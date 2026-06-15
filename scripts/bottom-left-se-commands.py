#!/usr/bin/env python3
from __future__ import annotations

import argparse
import datetime
import sys
from pathlib import Path

from result_tables import (
    bottom_left_exact_value,
    cp_command,
    face_count_max,
    parse_int_list,
    sat_command,
    skip_exact_reason,
    write_cp_param,
)


def parse_args() -> argparse.Namespace:
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d-%H-%M")
    parser = argparse.ArgumentParser(description="Generate only the bottom-left SE exact-count commands.")
    parser.add_argument("--dimensions", default="3-7", help="Comma-separated dimensions or ranges, e.g. 3-7.")
    parser.add_argument("--backend", choices=["sat", "cp", "both"], default="both", help="Which command file(s) to write.")
    parser.add_argument("--sat-commands-file", default="satcommands-bottom-left-SE", help="SAT command output file.")
    parser.add_argument("--cp-commands-file", default="cpcommands-bottom-left-SE", help="CP/Conjure command output file.")
    parser.add_argument(
        "--sat-output-dir",
        default=f"output/raw/count-sat-cadical-SE-bottom-left-{timestamp}",
        help="Directory passed to models/sat/bio.py --output.",
    )
    parser.add_argument(
        "--cp-output-dir",
        default=f"output/raw/count-essence-edge-branching-full-symmetry-minion-SE-bottom-left-{timestamp}",
        help="Directory passed to conjure solve -o.",
    )
    parser.add_argument("--no-skip", action="store_true", help="Generate commands even when stored data exists.")
    return parser.parse_args()


def should_skip_sat(dimension: int, face_count: int, no_skip: bool) -> str | None:
    if no_skip:
        return None
    if bottom_left_exact_value(dimension) is not None:
        return "SAT bottom-left result already stored"
    return skip_exact_reason("sat", "SE", dimension, 1, face_count)


def should_skip_cp(dimension: int, face_count: int, no_skip: bool) -> str | None:
    if no_skip:
        return None
    return skip_exact_reason("cp", "SE", dimension, 1, face_count)


def write_sat_commands(dimensions: list[int], args: argparse.Namespace) -> tuple[int, int]:
    emitted = 0
    skipped = 0
    with Path(args.sat_commands_file).open("w", encoding="utf8") as handle:
        for dimension in dimensions:
            face_count = face_count_max(dimension)
            if should_skip_sat(dimension, face_count, args.no_skip) is not None:
                skipped += 1
                continue
            print(
                sat_command(
                    dimension,
                    1,
                    "SE",
                    face_count,
                    output_dir=args.sat_output_dir,
                    enumerate_all=True,
                ),
                file=handle,
            )
            emitted += 1
    return emitted, skipped


def write_cp_commands(dimensions: list[int], args: argparse.Namespace) -> tuple[int, int]:
    emitted = 0
    skipped = 0
    with Path(args.cp_commands_file).open("w", encoding="utf8") as handle:
        for dimension in dimensions:
            face_count = face_count_max(dimension)
            if should_skip_cp(dimension, face_count, args.no_skip) is not None:
                skipped += 1
                continue
            param = write_cp_param("SE", dimension, 1, face_count)
            print(cp_command(param, output_dir=args.cp_output_dir), file=handle)
            emitted += 1
    return emitted, skipped


def main() -> None:
    args = parse_args()
    dimensions = parse_int_list(args.dimensions, default=[3, 4, 5, 6, 7])

    if args.backend in {"sat", "both"}:
        emitted, skipped = write_sat_commands(dimensions, args)
        print(f"Wrote {emitted} SAT bottom-left SE commands to {args.sat_commands_file}; skipped {skipped}.", file=sys.stderr)

    if args.backend in {"cp", "both"}:
        emitted, skipped = write_cp_commands(dimensions, args)
        print(f"Wrote {emitted} CP/Conjure bottom-left SE commands to {args.cp_commands_file}; skipped {skipped}.", file=sys.stderr)


if __name__ == "__main__":
    main()
