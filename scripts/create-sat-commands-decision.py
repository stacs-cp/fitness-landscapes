#!/usr/bin/env python3
from __future__ import annotations

import argparse
import datetime
import sys
from pathlib import Path

from result_tables import face_counts, parse_int_list, parse_props, peak_counts, sat_command, skip_decision_reason


def parse_args() -> argparse.Namespace:
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d-%H-%M")
    parser = argparse.ArgumentParser(description="Generate SAT decision commands for missing instances.")
    parser.add_argument("--dimensions", default="3,4,5", help="Comma-separated dimensions or ranges, e.g. 3,4,5 or 3-7.")
    parser.add_argument("--props", default="RSE,SE", help="Comma-separated props to generate: RSE,SE.")
    parser.add_argument("--commands-file", default="satcommandsDEC", help="Output command file.")
    parser.add_argument(
        "--output-dir",
        default=f"output/raw/decision-sat-cadical",
        help="Directory passed to models/sat/bio.py --output.",
    )
    parser.add_argument("--no-skip", action="store_true", help="Generate every command, ignoring stored data.")
    parser.add_argument("--source-sym", action="store_true", help="Use the 0 being source symmetry handling only.")
    return parser.parse_args()


def main() -> None:
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d-%H-%M")
    args = parse_args()
    dimensions = parse_int_list(args.dimensions, default=[3, 4, 5])
    props = parse_props(args.props)
    emitted = 0
    skipped = 0

    with Path(args.commands_file).open("w", encoding="utf8") as handle:
        for dimension in dimensions:
            for nb_peaks in peak_counts(dimension):
                for prop in props:
                    for face_count in face_counts(dimension):
                        if not args.no_skip and skip_decision_reason(prop, dimension, nb_peaks, face_count):
                            skipped += 1
                            continue
                        out_dir = args.output_dir
                        if args.output_dir == f"output/raw/decision-sat-cadical":
                            if args.source_sym:              
                                out_dir = out_dir + "-0-source-sym-" + timestamp
                            else:
                                out_dir = out_dir + "-full-sym-" + timestamp
                        Path(out_dir).mkdir(parents=True, exist_ok=True)
                        print(
                            sat_command(
                                dimension,
                                nb_peaks,
                                prop,
                                face_count,
                                args.source_sym,
                                output_dir=out_dir,
                                enumerate_all=False,
                            ),
                            file=handle,
                        )
                        emitted += 1

    print(f"Wrote {emitted} SAT decision commands to {args.commands_file}; skipped {skipped}.", file=sys.stderr)


if __name__ == "__main__":
    main()
