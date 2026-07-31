#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path

from result_tables import cp_stats_filename, parse_runsolver_output_file, sat_result_filename


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Reconstruct compact runsolver -v files from verbose Slurm runsolver output."
    )
    parser.add_argument("slurm_dir", help="Directory containing Slurm .out files.")
    parser.add_argument("result_dir", help="Directory for the corresponding result files.")
    parser.add_argument("--overwrite", action="store_true", help="Replace existing .runsolver files.")
    parser.add_argument(
        "--allow-missing-results",
        action="store_true",
        help="Create sidecars even when the original result files are absent.",
    )
    return parser.parse_args()


def render_runsolver_vars(values: dict[str, str]) -> str:
    fields = [
        ("WCTIME", "real_time_seconds"),
        ("CPUTIME", "cpu_time_seconds"),
        ("USERTIME", "user_time_seconds"),
        ("SYSTEMTIME", "system_time_seconds"),
        ("CPUUSAGE", "cpu_usage_percent"),
        ("MAXVM", "max_virtual_memory_kib"),
    ]
    lines: list[str] = []
    for variable, key in fields:
        value = values.get(key)
        if value is None:
            raise ValueError(f"missing runsolver field {key}")
        lines.append(f"{variable}={value}")

    status = values.get("status")
    if status not in {"completed", "timeout", "memory-out"}:
        raise ValueError(f"cannot reconstruct unknown run status: {values.get('status')}")
    lines.append(f"TIMEOUT={'true' if status == 'timeout' else 'false'}")
    lines.append(f"MEMOUT={'true' if status == 'memory-out' else 'false'}")

    return "\n".join(lines) + "\n"


def main() -> None:
    args = parse_args()
    slurm_dir = Path(args.slurm_dir)
    result_dir = Path(args.result_dir)
    created = 0
    unchanged = 0
    failures: list[str] = []
    seen_results: set[Path] = set()
    missing_results = 0

    if args.allow_missing_results:
        result_dir.mkdir(parents=True, exist_ok=True)

    for slurm_path in sorted(slurm_dir.glob("*.out")):
        values = parse_runsolver_output_file(slurm_path)
        identity_fields = ("dimension", "nb_peaks", "prop", "face_count")
        if not all(field in values for field in identity_fields):
            failures.append(f"{slurm_path}: could not identify experiment instance")
            continue

        filename_factory = cp_stats_filename if values.get("backend") == "cp" else sat_result_filename
        result_path = result_dir / filename_factory(
            int(values["dimension"]),
            int(values["nb_peaks"]),
            values["prop"],
            int(values["face_count"]),
        )
        if result_path in seen_results:
            failures.append(f"{slurm_path}: duplicate result mapping for {result_path}")
            continue
        seen_results.add(result_path)
        if not result_path.exists():
            missing_results += 1
            if not args.allow_missing_results:
                failures.append(f"{slurm_path}: result file does not exist: {result_path}")
                continue

        try:
            content = render_runsolver_vars(values)
        except ValueError as error:
            failures.append(f"{slurm_path}: {error}")
            continue

        output_path = result_path.with_suffix(result_path.suffix + ".runsolver")
        if output_path.exists():
            existing = output_path.read_text(encoding="utf8")
            if existing == content:
                unchanged += 1
                continue
            if not args.overwrite:
                failures.append(f"{output_path}: already exists with different content")
                continue

        output_path.write_text(content, encoding="utf8")
        created += 1

    if failures:
        for failure in failures:
            print(failure)
        raise SystemExit(f"Failed to reconstruct {len(failures)} runsolver file(s)")

    print(
        f"Reconstructed {created} runsolver file(s); "
        f"{unchanged} already matched; {len(seen_results)} instances mapped; "
        f"{missing_results} original result file(s) absent."
    )


if __name__ == "__main__":
    main()
