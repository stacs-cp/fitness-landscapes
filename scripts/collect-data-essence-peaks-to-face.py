#!/usr/bin/env python3
from __future__ import annotations

import argparse
from collections import defaultdict
from pathlib import Path

from result_tables import (
    CP_STATS_RE,
    RUNSOLVER_REQUIRED_FIELDS,
    UpsertStats,
    add_runsolver_records,
    cp_exact_table,
    face_counts,
    parse_cp_stats_file,
    parse_int_list,
    parse_props,
    peak_counts_with_zero,
    upsert_csv_grid,
    write_combined_stats,
    write_missing_stats,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Collect CP/Conjure exact-count stats into stored CSV tables.")
    parser.add_argument(
        "input_dirs",
        nargs="*",
        default=["output/raw/count-essence-edge-branching-full-symmetry-minion"],
        help="Directories containing model000001-peaks-to-...stats.json files.",
    )
    parser.add_argument("--dimensions", default="3,4,5", help="Comma-separated dimensions or ranges to collect.")
    parser.add_argument("--props", default="RSE,SE", help="Comma-separated props to collect: RSE,SE.")
    parser.add_argument("--recursive", action="store_true", help="Search input directories recursively.")
    parser.add_argument("--output-dir", help="Override table output directory.")
    parser.add_argument("--runsolver-dirs", nargs="*", default=[], help="Directories containing per-result .runsolver files.")
    parser.add_argument("--stats-output", help="Combined per-instance result and resource-usage CSV.")
    parser.add_argument("--missing-output", help="CSV listing records with missing result or runsolver fields.")
    parser.add_argument("--no-grid", action="store_true", help="Do not update the existing exact-count grids.")
    return parser.parse_args()


def iter_stats_files(input_dirs: list[str], recursive: bool) -> list[Path]:
    files: list[Path] = []
    for raw_dir in input_dirs:
        root = Path(raw_dir)
        pattern = "**/model000001-peaks-to-*.stats.json" if recursive else "model000001-peaks-to-*.stats.json"
        files.extend(path for path in root.glob(pattern) if CP_STATS_RE.match(path.name))
    return files


def main() -> None:
    args = parse_args()
    dimensions = set(parse_int_list(args.dimensions, default=[3, 4, 5]))
    props = set(parse_props(args.props))
    updates: dict[tuple[str, int], dict[tuple[int, int], str]] = defaultdict(dict)
    records: dict[tuple[str, int, int, int], dict[str, str]] = {}

    for path in iter_stats_files(args.input_dirs, args.recursive):
        match = CP_STATS_RE.match(path.name)
        if match is None:
            continue
        prop, dimension, nb_peaks, face_count = match.groups()
        dimension_i = int(dimension)
        nb_peaks_i = int(nb_peaks)
        face_count_i = int(face_count)
        if dimension_i not in dimensions or prop not in props:
            continue
        parsed = parse_cp_stats_file(path)
        key = (prop, dimension_i, nb_peaks_i, face_count_i)
        record = records.setdefault(key, {})
        record["result_file"] = str(path)
        record["exact_count"] = parsed.get("exact", "")
        record["solver_time_seconds"] = parsed.get("solver_time", "")
        record["savilerow_time_seconds"] = parsed.get("savilerow_time", "")
        exact = parsed.get("exact")
        if exact is None:
            continue
        updates[(prop, dimension_i)][(face_count_i, nb_peaks_i)] = exact

    add_runsolver_records(records, args.runsolver_dirs, dimensions, props)

    total = UpsertStats()
    if not args.no_grid:
        for prop in sorted(props):
            for dimension in sorted(dimensions):
                table_updates = updates.get((prop, dimension), {})
                if not table_updates:
                    continue
                path = Path(args.output_dir) / f"dim-{dimension}-{prop}.csv" if args.output_dir else cp_exact_table(prop, dimension)
                stats = upsert_csv_grid(
                    path,
                    table_updates,
                    kind="exact",
                    columns=peak_counts_with_zero(dimension),
                    rows=face_counts(dimension),
                )
                total += stats
                print(
                    f"{path}: inserted {stats.inserted}, updated {stats.updated}, "
                    f"unchanged {stats.unchanged}, conflicts {stats.conflicts}"
                )

    result_fields = ["exact_count", "solver_time_seconds", "savilerow_time_seconds"]
    if args.runsolver_dirs or args.stats_output:
        stats_path = Path(args.stats_output) if args.stats_output else (
            Path("output/summary/combined/counting") / f"{Path(args.input_dirs[0]).name}-stats.csv"
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
