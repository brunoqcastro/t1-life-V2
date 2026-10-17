#!/usr/bin/env python3
"""Compara o tempo total (wall clock) da versão sequencial x paralela do life.

Uso:
    python3 bench.py [binario_seq] [binario_par] [repeticoes] [pasta_casos]

Padrões (relativos à raiz do projeto):
    binario_seq     sequential/life
    binario_par     parallel/life
    repeticoes      5
    pasta_casos     parallel/  (com as subpastas in/ e out/)

Para cada in/life-N.in da pasta, roda cada binário <repeticoes> vezes, usa a
mediana dos tempos e confere a saída com out/life-N.out (quando existir).

O número de threads da versão paralela segue OMP_NUM_THREADS; se não estiver
definido, o OpenMP usa o padrão do sistema (normalmente um por núcleo lógico).
"""
import os
import statistics
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def human_size(n):
    for unit in ("B", "KB", "MB", "GB"):
        if n < 1024:
            return f"{n:.1f} {unit}"
        n /= 1024
    return f"{n:.1f} TB"


def read_header(inp):
    """Lê 'L C G' da primeira linha da entrada."""
    with open(inp) as f:
        L, C, G = map(int, f.readline().split())
    return L, C, G


def run(binary, inp, reps):
    """Retorna (mediana dos tempos, menor, maior, stdout da última execução)."""
    times = []
    out = b""
    for _ in range(reps):
        with open(inp, "rb") as f:
            t0 = time.perf_counter()
            out = subprocess.run([binary], stdin=f, stdout=subprocess.PIPE, check=True).stdout
            times.append(time.perf_counter() - t0)
    return statistics.median(times), min(times), max(times), out


def check(out, inp):
    expected = inp.parent.parent / "out" / f"{inp.stem}.out"
    if not expected.exists():
        return "sem .out"
    return "ok" if out == expected.read_bytes() else "DIFERENTE"


def main():
    args = sys.argv[1:]
    if args and args[0] in ("-h", "--help"):
        print(__doc__)
        return

    seq = Path(args[0]) if len(args) > 0 else ROOT / "sequential" / "life"
    par = Path(args[1]) if len(args) > 1 else ROOT / "parallel" / "life"
    reps = int(args[2]) if len(args) > 2 else 5
    cases_dir = Path(args[3]) if len(args) > 3 else ROOT / "parallel"
    inputs_dir = cases_dir / "in"

    for b in (seq, par):
        if not b.exists():
            sys.exit(f"Binário não encontrado: {b}\nCompile antes com 'make' (no Mac: 'make CC=gcc-15').")

    inputs = sorted(inputs_dir.glob("life-*.in"), key=lambda p: int(p.stem.split("-")[1]))
    if not inputs:
        sys.exit(f"Nenhum life-*.in encontrado em {inputs_dir}")

    threads = os.environ.get("OMP_NUM_THREADS", f"padrão do sistema ({os.cpu_count()} núcleos lógicos)")

    print("=" * 78)
    print("Benchmark do Jogo da Vida: sequencial x paralelo (OpenMP)")
    print("=" * 78)
    print(f"  sequencial : {seq}")
    print(f"  paralelo   : {par}")
    print(f"  threads    : {threads}")
    print(f"  repetições : {reps} por caso (usa a mediana)")
    print(f"  entradas   : {inputs_dir} ({len(inputs)} casos)")
    print()

    print("Entradas")
    print("-" * 78)
    print(f"{'caso':<8}{'grade':>13}{'células':>13}{'gerações':>10}{'trabalho (cél x ger)':>22}{'arquivo':>12}")
    for inp in inputs:
        L, C, G = read_header(inp)
        print(f"{inp.stem:<8}{f'{L}x{C}':>13}{L * C:>13,}{G:>10}{L * C * G:>22,}{human_size(inp.stat().st_size):>12}")
    print()

    print("Tempos (wall clock, inclui leitura da entrada e escrita da saída)")
    print("-" * 78)
    print(f"{'caso':<8}{'seq (s)':>10}{'par (s)':>10}{'diferença (s)':>15}{'speedup':>10}{'mais rápido':>14}{'saídas':>11}")

    results = []
    for inp in inputs:
        print(f"{inp.stem:<8}", end="", flush=True)
        ts, _, _, out_s = run(seq, inp, reps)
        tp, _, _, out_p = run(par, inp, reps)
        speedup = ts / tp
        winner = "paralelo" if tp < ts else "sequencial"
        same = "iguais" if out_s == out_p else "DIFEREM"
        verdict = check(out_p, inp)
        status = same if verdict in ("ok", "sem .out") else f"{same}/{verdict}"
        print(f"{ts:>10.4f}{tp:>10.4f}{ts - tp:>15.4f}{speedup:>9.2f}x{winner:>14}{status:>11}")
        results.append((inp.stem, read_header(inp), ts, tp, speedup))

    print()
    print("Resumo")
    print("-" * 78)
    best = max(results, key=lambda r: r[4])
    worst = min(results, key=lambda r: r[4])
    print(f"  maior speedup : {best[0]} ({best[1][0]}x{best[1][1]}, {best[1][2]} gerações) -> {best[4]:.2f}x")
    print(f"  menor speedup : {worst[0]} ({worst[1][0]}x{worst[1][1]}, {worst[1][2]} gerações) -> {worst[4]:.2f}x")
    print(f"  tempo total   : seq {sum(r[2] for r in results):.2f}s | par {sum(r[3] for r in results):.2f}s (medianas somadas)")
    print()
    print("Como ler:")
    print("  - speedup = seq / par. Acima de 1x o paralelo ganhou; abaixo, perdeu.")
    print("  - Em grades pequenas o custo de criar/sincronizar threads supera o cálculo,")
    print("    então o paralelo tende a perder. O ganho aparece com grades grandes.")
    print("  - O tempo inclui a leitura com scanf, que é sequencial nas duas versões;")
    print("    por isso o speedup total fica abaixo do speedup do laço de gerações.")
    print("  - 'saídas' compara o resultado do paralelo com o do sequencial (e com o .out).")


if __name__ == "__main__":
    main()
