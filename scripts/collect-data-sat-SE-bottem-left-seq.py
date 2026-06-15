#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path

from result_tables import (
    SAT_RESULT_RE,
    bottom_left_exact_table,
    face_count_max,
    parse_int_list,
    parse_sat_result_file,
    sat_result_filename,
    upsert_dimension_row_table,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Collect bottom-left SE exact counts into the summary CSV.")
    parser.add_argument(
        "input_dirs",
        nargs="*",
        default=["output/raw/count-sat-cadical"],
        help="Directories containing dim-...txt result files.",
    )
    parser.add_argument("--dimensions", default="3-8", help="Comma-separated dimensions or ranges to collect.")
    parser.add_argument("--recursive", action="store_true", help="Search input directories recursively.")
    parser.add_argument("--output", default=str(bottom_left_exact_table()), help="Output summary CSV.")
    return parser.parse_args()


def iter_result_files(input_dirs: list[str], recursive: bool) -> list[Path]:
    files: list[Path] = []
    for raw_dir in input_dirs:
        root = Path(raw_dir)
        pattern = "**/dim-*-peak-*-SE-*.txt" if recursive else "dim-*-peak-*-SE-*.txt"
        files.extend(path for path in root.glob(pattern) if SAT_RESULT_RE.match(path.name))
    return files


def main() -> None:
    args = parse_args()
    dimensions = set(parse_int_list(args.dimensions, default=[3, 4, 5, 6, 7, 8]))
    expected_names = {sat_result_filename(dimension, 1, "SE", face_count_max(dimension)): dimension for dimension in dimensions}
    updates: dict[int, str] = {}

    for path in iter_result_files(args.input_dirs, args.recursive):
        dimension = expected_names.get(path.name)
        if dimension is None:
            continue
        exact = parse_sat_result_file(path).get("exact")
        if exact is not None:
            updates[dimension] = exact

    if not updates and not Path(args.output).exists():
        print(f"{args.output}: inserted 0, updated 0, unchanged 0, conflicts 0")
        return

    stats = upsert_dimension_row_table(Path(args.output), updates, kind="exact")
    print(
        f"{args.output}: inserted {stats.inserted}, updated {stats.updated}, "
        f"unchanged {stats.unchanged}, conflicts {stats.conflicts}"
    )


if __name__ == "__main__":
    main()
