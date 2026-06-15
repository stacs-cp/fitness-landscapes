#!/usr/bin/env python3
from __future__ import annotations

import argparse
from collections import defaultdict
from pathlib import Path

from result_tables import (
    SAT_RESULT_RE,
    UpsertStats,
    face_counts,
    parse_int_list,
    parse_props,
    parse_sat_result_file,
    peak_counts_with_zero,
    sat_decision_table,
    sat_known_at_least_table,
    upsert_csv_grid,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Collect SAT decision results into stored CSV tables.")
    parser.add_argument(
        "input_dirs",
        nargs="*",
        default=["output/raw/decision-sat-cadical"],
        help="Directories containing dim-...txt result files.",
    )
    parser.add_argument("--dimensions", default="3,4,5", help="Comma-separated dimensions or ranges to collect.")
    parser.add_argument("--props", default="RSE,SE", help="Comma-separated props to collect: RSE,SE.")
    parser.add_argument(
        "--mode",
        choices=["decision", "known-at-least"],
        default="decision",
        help="Collect SAT/UNSAT decisions or partial enumeration lower bounds.",
    )
    parser.add_argument("--recursive", action="store_true", help="Search input directories recursively.")
    parser.add_argument("--output-dir", help="Override table output directory.")
    return parser.parse_args()


def iter_result_files(input_dirs: list[str], recursive: bool) -> list[Path]:
    files: list[Path] = []
    for raw_dir in input_dirs:
        root = Path(raw_dir)
        pattern = "**/dim-*-peak-*-*-*.txt" if recursive else "dim-*-peak-*-*-*.txt"
        files.extend(path for path in root.glob(pattern) if SAT_RESULT_RE.match(path.name))
    return files


def default_table(prop: str, dimension: int, mode: str) -> Path:
    if mode == "decision":
        return sat_decision_table(prop, dimension)
    return sat_known_at_least_table(prop, dimension)


def main() -> None:
    args = parse_args()
    dimensions = set(parse_int_list(args.dimensions, default=[3, 4, 5]))
    props = set(parse_props(args.props))
    value_key = "decision" if args.mode == "decision" else "known_at_least"
    kind = "decision" if args.mode == "decision" else "known_at_least"
    updates: dict[tuple[str, int], dict[tuple[int, int], str]] = defaultdict(dict)

    for path in iter_result_files(args.input_dirs, args.recursive):
        match = SAT_RESULT_RE.match(path.name)
        if match is None:
            continue
        dimension, nb_peaks, prop, face_count = match.groups()
        dimension_i = int(dimension)
        nb_peaks_i = int(nb_peaks)
        face_count_i = int(face_count)
        if dimension_i not in dimensions or prop not in props:
            continue
        value = parse_sat_result_file(path).get(value_key)
        if value is None:
            continue
        updates[(prop, dimension_i)][(face_count_i, nb_peaks_i)] = value

    total = UpsertStats()
    for prop in sorted(props):
        for dimension in sorted(dimensions):
            table_updates = updates.get((prop, dimension), {})
            if not table_updates:
                continue
            path = Path(args.output_dir) / f"dim-{dimension}-{prop}.csv" if args.output_dir else default_table(prop, dimension, args.mode)
            stats = upsert_csv_grid(
                path,
                table_updates,
                kind=kind,
                columns=peak_counts_with_zero(dimension),
                rows=face_counts(dimension),
            )
            total += stats
            print(
                f"{path}: inserted {stats.inserted}, updated {stats.updated}, "
                f"unchanged {stats.unchanged}, conflicts {stats.conflicts}"
            )

    print(
        f"Total: inserted {total.inserted}, updated {total.updated}, "
        f"unchanged {total.unchanged}, conflicts {total.conflicts}"
    )


if __name__ == "__main__":
    main()
