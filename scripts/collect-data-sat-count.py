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
    sat_exact_table,
    upsert_csv_grid,
    write_combined_stats,
    write_missing_stats,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Collect SAT exact-count results into stored CSV tables.")
    parser.add_argument(
        "input_dirs",
        nargs="*",
        default=["output/raw/count-sat-cadical"],
        help="Directories containing dim-...txt result files.",
    )
    parser.add_argument("--dimensions", default="3,4,5", help="Comma-separated dimensions or ranges to collect.")
    parser.add_argument("--props", default="RSE,SE", help="Comma-separated props to collect: RSE,SE.")
    parser.add_argument("--recursive", action="store_true", help="Search input directories recursively.")
    parser.add_argument("--output-dir", help="Override table output directory.")
    parser.add_argument(
        "--runsolver-dirs",
        nargs="*",
        default=[],
        help="Directories containing Slurm .out or per-result .runsolver files.",
    )
    parser.add_argument(
        "--stats-output",
        help="Combined per-instance CSV containing counts, solver time, and runsolver resource usage.",
    )
    parser.add_argument(
        "--missing-output",
        help="CSV listing records with missing result or runsolver fields.",
    )
    parser.add_argument(
        "--no-grid",
        action="store_true",
        help="Do not update the existing face/peak count grids.",
    )
    return parser.parse_args()


def iter_result_files(input_dirs: list[str], recursive: bool) -> list[Path]:
    files: list[Path] = []
    for raw_dir in input_dirs:
        root = Path(raw_dir)
        pattern = "**/dim-*-peak-*-*-*.txt" if recursive else "dim-*-peak-*-*-*.txt"
        files.extend(path for path in root.glob(pattern) if SAT_RESULT_RE.match(path.name))
    return files


def main() -> None:
    args = parse_args()
    dimensions = set(parse_int_list(args.dimensions, default=[3, 4, 5]))
    props = set(parse_props(args.props))
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
        exact = parsed.get("exact")
        if exact is None:
            record.setdefault("exact_count", "")
        else:
            record["exact_count"] = exact
            updates[(prop, dimension_i)][(face_count_i, nb_peaks_i)] = exact
        record["solver_time_seconds"] = parsed.get("time", "")

    add_runsolver_records(records, args.runsolver_dirs, dimensions, props)

    total = UpsertStats()
    if not args.no_grid:
        for prop in sorted(props):
            for dimension in sorted(dimensions):
                table_updates = updates.get((prop, dimension), {})
                if not table_updates:
                    continue
                path = Path(args.output_dir) / f"dim-{dimension}-{prop}.csv" if args.output_dir else sat_exact_table(prop, dimension)
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

    if args.runsolver_dirs or args.stats_output:
        if args.stats_output:
            stats_path = Path(args.stats_output)
        else:
            run_name = Path(args.input_dirs[0]).name
            stats_path = Path("output/summary/combined/counting") / f"{run_name}-stats.csv"
        write_combined_stats(stats_path, records, ["exact_count", "solver_time_seconds"])
        print(f"{stats_path}: wrote {len(records)} combined per-instance records")

    if args.missing_output:
        missing_path = Path(args.missing_output)
        missing_count = write_missing_stats(
            missing_path,
            records,
            ["exact_count", "solver_time_seconds", *RUNSOLVER_REQUIRED_FIELDS],
        )
        print(f"{missing_path}: wrote {missing_count} records with missing fields")

    print(
        f"Total: inserted {total.inserted}, updated {total.updated}, "
        f"unchanged {total.unchanged}, conflicts {total.conflicts}"
    )


if __name__ == "__main__":
    main()
