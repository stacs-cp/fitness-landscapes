#!/usr/bin/env python3
from __future__ import annotations

import argparse
from collections import defaultdict
from pathlib import Path

from result_tables import (
    RUNSOLVER_REQUIRED_FIELDS,
    SAT_RESULT_RE,
    UpsertStats,
    add_runsolver_records,
    face_counts,
    parse_int_list,
    parse_props,
    parse_sat_result_file,
    peak_counts_with_zero,
    sat_decision_table,
    sat_known_at_least_table,
    upsert_csv_grid,
    write_combined_stats,
    write_missing_stats,
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
    parser.add_argument("--runsolver-dirs", nargs="*", default=[], help="Directories containing per-result .runsolver files.")
    parser.add_argument("--stats-output", help="Combined per-instance result and resource-usage CSV.")
    parser.add_argument("--missing-output", help="CSV listing records with missing result or runsolver fields.")
    parser.add_argument("--no-grid", action="store_true", help="Do not update the existing decision grids.")
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
    records: dict[tuple[str, int, int, int], dict[str, str]] = {}

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
        parsed = parse_sat_result_file(path)
        key = (prop, dimension_i, nb_peaks_i, face_count_i)
        record = records.setdefault(key, {})
        record["result_file"] = str(path)
        record["solver_time_seconds"] = parsed.get("time", "")
        value = parsed.get(value_key)
        if value is None:
            record.setdefault(value_key, "")
            continue
        record[value_key] = value
        updates[(prop, dimension_i)][(face_count_i, nb_peaks_i)] = value

    add_runsolver_records(records, args.runsolver_dirs, dimensions, props)

    total = UpsertStats()
    if not args.no_grid:
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

    result_fields = [value_key, "solver_time_seconds"]
    if args.runsolver_dirs or args.stats_output:
        stats_path = Path(args.stats_output) if args.stats_output else (
            Path("output/summary/combined/decision") / f"{Path(args.input_dirs[0]).name}-stats.csv"
        )
        write_combined_stats(stats_path, records, result_fields)
        print(f"{stats_path}: wrote {len(records)} combined per-instance records")

    if args.missing_output:
        missing_path = Path(args.missing_output)
        missing_count = write_missing_stats(
            missing_path,
            records,
            [*result_fields, *RUNSOLVER_REQUIRED_FIELDS],
        )
        print(f"{missing_path}: wrote {missing_count} records with missing fields")

    print(
        f"Total: inserted {total.inserted}, updated {total.updated}, "
        f"unchanged {total.unchanged}, conflicts {total.conflicts}"
    )


if __name__ == "__main__":
    main()
