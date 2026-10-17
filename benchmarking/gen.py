#!/usr/bin/env python3
"""Gera entradas (aleatórias, mas reprodutíveis) para o life.

Uso:
    python3 gen.py L C G [seed] [densidade] > arquivo.in

    L         número de linhas da grade
    C         número de colunas da grade
    G         número de gerações
    seed      semente do gerador aleatório (padrão: 0); mesma semente => mesmo arquivo
    densidade fração de células vivas na grade inicial (padrão: 0.3)

Exemplo (casos grandes usados em parallel/):
    python3 gen.py  500  500 500 5 > ../parallel/in/life-5.in
    python3 gen.py 1000 1000 500 6 > ../parallel/in/life-6.in
    python3 gen.py 2000 2000 300 7 > ../parallel/in/life-7.in
    python3 gen.py 4000 4000 100 8 > ../parallel/in/life-8.in

A entrada vai para stdout; as mensagens informativas vão para stderr,
então não atrapalham o redirecionamento para o arquivo.
"""
import random
import sys

RULES = ["B3/S23", "B36/S23", "B3678/S34678", "B2/S"]


def human_size(n):
    for unit in ("B", "KB", "MB", "GB"):
        if n < 1024:
            return f"{n:.1f} {unit}"
        n /= 1024
    return f"{n:.1f} TB"


def main():
    if len(sys.argv) < 4:
        sys.stderr.write(__doc__)
        sys.exit(1)

    L, C, G = map(int, sys.argv[1:4])
    seed = int(sys.argv[4]) if len(sys.argv) > 4 else 0
    density = float(sys.argv[5]) if len(sys.argv) > 5 else 0.3
    random.seed(seed)

    out = [f"{L} {C} {G}", str(len(RULES)), *RULES]

    # Regiões de regras em faixas verticais, como nos exemplos do sequential.
    band = max(1, C // len(RULES))
    row_ids = " ".join(str(min(c // band, len(RULES) - 1)) for c in range(C))
    out.extend(row_ids for _ in range(L))

    alive = 0
    for _ in range(L):
        row = "".join("x" if random.random() < density else " " for _ in range(C))
        alive += row.count("x")
        out.append(row)

    text = "\n".join(out) + "\n"
    sys.stdout.write(text)

    cells = L * C
    log = sys.stderr.write
    log(f"Entrada gerada: grade {L}x{C} ({cells:,} células), {G} gerações\n")
    log(f"  regras        : {', '.join(f'{i}={r}' for i, r in enumerate(RULES))} (faixas verticais)\n")
    log(f"  células vivas : {alive:,} ({alive / cells:.1%}, densidade pedida {density:.0%})\n")
    log(f"  trabalho      : {cells * G:,} atualizações de célula (células x gerações)\n")
    log(f"  tamanho       : {human_size(len(text.encode()))}\n")
    log(f"  seed          : {seed}\n")


if __name__ == "__main__":
    main()
