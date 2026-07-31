#!/usr/bin/env python3
from __future__ import annotations

import argparse
import datetime
import sys
from pathlib import Path

from result_tables import cp_command, face_counts, parse_int_list, parse_props, peak_counts, skip_exact_reason, write_cp_param


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate CP/Conjure exact-count commands for missing instances.")
    parser.add_argument("--dimensions", default="3,4,5", help="Comma-separated dimensions or ranges, e.g. 3,4,5 or 3-7.")
    parser.add_argument("--props", default="RSE,SE", help="Comma-separated props to generate: RSE,SE.")
    parser.add_argument("--commands-file", default="cpcommands", help="Output command file.")
    parser.add_argument(
        "--output-dir",
        default=f"output/raw/count-essence-edge-branching",
        help="Directory passed to conjure solve -o.",
    )
    parser.add_argument("--no-skip", action="store_true", help="Generate every command, ignoring stored data.")
    parser.add_argument("--source-sym", action="store_true", help="Use the 0 being source symmetry handling only.")
    parser.add_argument("--decision", action="store_true", help="Solve decision problem.")
    parser.add_argument("--solver", default="minion", help="Choose the solver.")

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
                        if not args.no_skip and skip_exact_reason("cp", prop, dimension, nb_peaks, face_count):
                            skipped += 1
                            continue
                        param = write_cp_param(prop, dimension, nb_peaks, face_count, not args.source_sym)
                        
                        out_dir = args.output_dir
                        if args.output_dir == f"output/raw/count-essence-edge-branching":
                            if args.decision:
                                out_dir = f"output/raw/decision-essence-edge-branching"

                            out_dir = out_dir + "-" + args.solver
                            if args.source_sym:              
                                out_dir = out_dir + "-0-source-sym-" + timestamp
                            else:
                                out_dir = out_dir + "-full-sym-" + timestamp
                        Path(out_dir).mkdir(parents=True, exist_ok=True)
                        print(cp_command(param, dec=args.decision, output_dir=out_dir, solver=args.solver), file=handle)
                        emitted += 1

    print(f"Wrote {emitted} CP/Conjure exact commands to {args.commands_file}; skipped {skipped}.", file=sys.stderr)


if __name__ == "__main__":
    main()
