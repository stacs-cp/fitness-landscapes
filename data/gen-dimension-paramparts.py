#!/usr/bin/env python3

from itertools import permutations
from pathlib import Path
import sys


def matrix_literal(rows: list[tuple[int, ...]], dimension: int) -> str:
    row_domain = f"int(1..{dimension})"
    rows_text = [f"[{', '.join(map(str, row))}; {row_domain}]" for row in rows]
    return "[\n    " + ",\n    ".join(rows_text) + f"\n; int(1..{len(rows)})]"


def write_parampart(dimension: int, output_dir: Path) -> None:
    rows = list(permutations(range(1, dimension + 1)))
    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / f"dimension-{dimension}.parampart").write_text(
        "\n".join(
            [
                f"letting nbPermutations be {len(rows)}",
                "letting permutations be",
                f"    {matrix_literal(rows, dimension)}",
                "",
            ]
        )
    )


def main() -> None:
    if len(sys.argv) > 1:
        dimensions = [int(arg) for arg in sys.argv[1:]]
    else:
        dimensions = [3, 4, 5]

    for dimension in dimensions:
        if dimension < 1:
            raise ValueError(f"dimension must be positive: {dimension}")
        write_parampart(dimension, Path("data"))


if __name__ == "__main__":
    main()
