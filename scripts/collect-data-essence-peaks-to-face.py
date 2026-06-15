#!/usr/bin/env python3
from __future__ import annotations

import argparse
from collections import defaultdict
from pathlib import Path

from result_tables import (
    CP_STATS_RE,
    UpsertStats,
    cp_exact_table,
    face_counts,
    parse_cp_stats_file,
    parse_int_list,
    parse_props,
    peak_counts_with_zero,
    upsert_csv_grid,
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
        exact = parse_cp_stats_file(path).get("exact")
        if exact is None:
            continue
        updates[(prop, dimension_i)][(face_count_i, nb_peaks_i)] = exact

    total = UpsertStats()
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

    print(
        f"Total: inserted {total.inserted}, updated {total.updated}, "
        f"unchanged {total.unchanged}, conflicts {total.conflicts}"
    )


if __name__ == "__main__":
    main()
