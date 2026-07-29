from __future__ import annotations

import csv
import json
import re
import shlex
import sys
from dataclasses import dataclass
from functools import lru_cache
from itertools import permutations
from pathlib import Path
from typing import Iterable, Literal


PROPS = ("RSE", "SE")
MISSING_VALUES = {"", "na", "n/a", "none", "null", "initialised", "unknown"}
ROOT = Path(__file__).resolve().parent.parent

SAT_RESULT_RE = re.compile(r"dim-(\d+)-peak-(\d+)-(RSE|SE)-(\d+)\.txt$")
CP_STATS_RE = re.compile(r"model000001-peaks-to-(RSE|SE)-dimension-(\d+)-peaks-(\d+)-count-(\d+)\.stats\.json$")
YEWPAR_RESULT_RE = re.compile(r"dim-(\d+)-peak-(\d+)-(RSE|SE)-(\d+)\.txt$")


CellKind = Literal["decision", "exact", "known_at_least", "time"]
Backend = Literal["sat", "cp", "yewpar"]


@dataclass
class UpsertStats:
    inserted: int = 0
    updated: int = 0
    unchanged: int = 0
    conflicts: int = 0

    def __iadd__(self, other: "UpsertStats") -> "UpsertStats":
        self.inserted += other.inserted
        self.updated += other.updated
        self.unchanged += other.unchanged
        self.conflicts += other.conflicts
        return self


def face_count_max(dimension: int) -> int:
    if dimension < 2:
        return 0
    return dimension * (dimension - 1) // 2 * (2 ** (dimension - 2))


def face_counts(dimension: int) -> range:
    return range(0, face_count_max(dimension) + 1)


def peak_counts(dimension: int) -> range:
    return range(1, 2 ** (dimension - 1) + 1)


def peak_counts_with_zero(dimension: int) -> range:
    return range(0, 2 ** (dimension - 1) + 1)


def parse_int_list(raw: str | None, default: Iterable[int]) -> list[int]:
    if raw is None:
        return list(default)
    values: list[int] = []
    for part in raw.split(","):
        part = part.strip()
        if not part:
            continue
        if "-" in part:
            start, end = [int(piece) for piece in part.split("-", 1)]
            step = 1 if start <= end else -1
            values.extend(range(start, end + step, step))
        else:
            values.append(int(part))
    return values


def parse_props(raw: str | None) -> list[str]:
    if raw is None:
        return list(PROPS)
    props = [part.strip().upper() for part in raw.split(",") if part.strip()]
    invalid = sorted(set(props) - set(PROPS))
    if invalid:
        raise ValueError(f"unknown prop(s): {', '.join(invalid)}")
    return props


def is_missing(value: object) -> bool:
    if value is None:
        return True
    return str(value).strip().lower() in MISSING_VALUES


def is_integer_cell(value: object) -> bool:
    return re.fullmatch(r"\d+", str(value).strip()) is not None


def is_float_cell(value: object) -> bool:
    try:
        float(str(value).strip())
        return not is_missing(value)
    except ValueError:
        return False


def cell_quality(value: object, kind: CellKind) -> int:
    if is_missing(value):
        return 0
    value_text = str(value).strip()
    if kind == "decision":
        return 3 if value_text in {"0", "1"} else 0
    if kind == "exact":
        return 3 if is_integer_cell(value_text) else 0
    if kind == "known_at_least":
        return 2 if is_integer_cell(value_text) else 0
    if kind == "time":
        return 2 if is_float_cell(value_text) else 0
    raise ValueError(f"unknown cell kind: {kind}")


def choose_better(existing: str, candidate: str, kind: CellKind) -> tuple[str, str]:
    existing_quality = cell_quality(existing, kind)
    candidate_quality = cell_quality(candidate, kind)
    if candidate_quality == 0:
        return existing, "unchanged"
    if existing_quality == 0:
        return candidate, "inserted"

    if kind == "known_at_least" and existing.isdigit() and candidate.isdigit():
        if int(candidate) > int(existing):
            return candidate, "updated"
        return existing, "unchanged"

    if kind == "time" and is_float_cell(existing) and is_float_cell(candidate):
        if float(candidate) < float(existing):
            return candidate, "updated"
        return existing, "unchanged"

    if candidate_quality > existing_quality:
        return candidate, "updated"

    if candidate_quality == existing_quality and existing.strip() != candidate.strip():
        return existing, "conflict"

    return existing, "unchanged"


def _to_int_if_possible(value: str) -> int | str:
    try:
        return int(value)
    except ValueError:
        return value


def _sorted_labels(labels: Iterable[str]) -> list[str]:
    return sorted({str(label).strip() for label in labels}, key=_to_int_if_possible)


def _unique_paths(paths: Iterable[Path]) -> list[Path]:
    seen: set[Path] = set()
    unique: list[Path] = []
    for path in paths:
        if path in seen:
            continue
        seen.add(path)
        unique.append(path)
    return unique


@lru_cache(maxsize=None)
def load_csv_grid(path_text: str) -> tuple[str, tuple[str, ...], tuple[tuple[str, tuple[str, ...]], ...]]:
    path = Path(path_text)
    if not path.exists():
        return "Faces/Peaks", tuple(), tuple()

    with path.open("r", encoding="utf8", newline="") as handle:
        rows = list(csv.reader(handle))

    if not rows:
        return "Faces/Peaks", tuple(), tuple()

    header = rows[0]
    corner = header[0].strip() if header else "Faces/Peaks"
    columns = tuple(cell.strip() for cell in header[1:])
    body: list[tuple[str, tuple[str, ...]]] = []
    for row in rows[1:]:
        if not row:
            continue
        padded = row + [""] * max(0, len(columns) + 1 - len(row))
        body.append((padded[0].strip(), tuple(cell.strip() for cell in padded[1 : len(columns) + 1])))
    return corner, columns, tuple(body)


def csv_cell(path: Path, face_count: int, nb_peaks: int) -> str | None:
    _corner, columns, rows = load_csv_grid(str(path))
    column = str(nb_peaks)
    row_key = str(face_count)
    if column not in columns:
        return None
    col_index = columns.index(column)
    for label, cells in rows:
        if label == row_key:
            return cells[col_index] if col_index < len(cells) else ""
    return None


def upsert_csv_grid(
    path: Path,
    updates: dict[tuple[int, int], str],
    *,
    kind: CellKind,
    columns: Iterable[int],
    rows: Iterable[int],
    corner_label: str = "Faces/Peaks",
) -> UpsertStats:
    stats = UpsertStats()
    path.parent.mkdir(parents=True, exist_ok=True)

    existing_corner, existing_columns, existing_rows = load_csv_grid(str(path))
    if existing_corner:
        corner_label = existing_corner

    all_columns = _sorted_labels([*existing_columns, *(str(col) for col in columns)])
    row_map: dict[str, dict[str, str]] = {
        row_label: {column: cells[index] if index < len(cells) else "" for index, column in enumerate(existing_columns)}
        for row_label, cells in existing_rows
    }
    for row in rows:
        row_map.setdefault(str(row), {})

    for row_label in row_map:
        for column in all_columns:
            row_map[row_label].setdefault(column, "")

    for (face_count, nb_peaks), candidate in sorted(updates.items()):
        row_label = str(face_count)
        column = str(nb_peaks)
        if row_label not in row_map:
            row_map[row_label] = {col: "" for col in all_columns}
        if column not in all_columns:
            all_columns = _sorted_labels([*all_columns, column])
            for cells in row_map.values():
                cells.setdefault(column, "")

        existing = row_map[row_label].get(column, "")
        chosen, action = choose_better(existing, candidate, kind)
        row_map[row_label][column] = chosen
        if action == "inserted":
            stats.inserted += 1
        elif action == "updated":
            stats.updated += 1
        elif action == "conflict":
            stats.conflicts += 1
            print(
                f"Conflict for {path} row {row_label} column {column}: "
                f"kept {existing!r}, ignored {candidate!r}",
                file=sys.stderr,
            )
        else:
            stats.unchanged += 1

    ordered_rows = _sorted_labels(row_map)
    with path.open("w", encoding="utf8", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow([corner_label, *all_columns])
        for row_label in ordered_rows:
            writer.writerow([row_label, *(row_map[row_label].get(column, "") for column in all_columns)])

    load_csv_grid.cache_clear()
    return stats


@lru_cache(maxsize=None)
def load_dimension_row_table(path_text: str) -> tuple[str | None, str | None, tuple[tuple[str, str], ...]]:
    path = Path(path_text)
    if not path.exists():
        return None, None, tuple()

    with path.open("r", encoding="utf8", newline="") as handle:
        rows = [[cell.strip() for cell in row] for row in csv.reader(handle)]

    if len(rows) < 2:
        return None, None, tuple()

    header_label: str | None = None
    value_label: str | None = None
    header = rows[0]
    values = rows[1]
    if header and not header[0].isdigit():
        header_label = header[0]
        header = header[1:]
        if values:
            value_label = values[0]
            values = values[1:]

    pairs = tuple((dimension, values[index] if index < len(values) else "") for index, dimension in enumerate(header))
    return header_label, value_label, pairs


def dimension_table_cell(path: Path, dimension: int) -> str | None:
    _header_label, _value_label, pairs = load_dimension_row_table(str(path))
    for label, value in pairs:
        if label == str(dimension):
            return value
    return None


def upsert_dimension_row_table(
    path: Path,
    updates: dict[int, str],
    *,
    kind: CellKind,
    header_label: str | None = None,
    value_label: str | None = None,
) -> UpsertStats:
    stats = UpsertStats()
    path.parent.mkdir(parents=True, exist_ok=True)

    existing_header_label, existing_value_label, pairs = load_dimension_row_table(str(path))
    header_label = existing_header_label if existing_header_label is not None else header_label
    value_label = existing_value_label if existing_value_label is not None else value_label
    values = {dimension: value for dimension, value in pairs}

    for dimension, candidate in sorted(updates.items()):
        label = str(dimension)
        existing = values.get(label, "")
        chosen, action = choose_better(existing, candidate, kind)
        values[label] = chosen
        if action == "inserted":
            stats.inserted += 1
        elif action == "updated":
            stats.updated += 1
        elif action == "conflict":
            stats.conflicts += 1
            print(
                f"Conflict for {path} dimension {label}: kept {existing!r}, ignored {candidate!r}",
                file=sys.stderr,
            )
        else:
            stats.unchanged += 1

    dimensions = _sorted_labels(values)
    with path.open("w", encoding="utf8", newline="") as handle:
        writer = csv.writer(handle)
        if header_label is None:
            writer.writerow(dimensions)
            writer.writerow([values.get(dimension, "") for dimension in dimensions])
        else:
            writer.writerow([header_label, *dimensions])
            writer.writerow([value_label or "", *(values.get(dimension, "") for dimension in dimensions)])

    load_dimension_row_table.cache_clear()
    return stats


def sat_exact_table(prop: str, dimension: int) -> Path:
    return ROOT / "output" / "summary" / "combined" / "counting" / f"dim-{dimension}-{prop}-0-source-sym.csv"


def sat_exact_time_table(prop: str, dimension: int) -> Path:
    return (
        ROOT
        / "output"
        / "summary"
        / "runtimes"
        / "old-runtimes"
        / f"count-sat-cadical-0-source-sym-dim-{dimension}-{prop}-time.csv"
    )


def sat_decision_table(prop: str, dimension: int) -> Path:
    return ROOT / "output" / "summary" / "combined" / "decision" / f"dim-{dimension}-{prop}.csv"


def sat_decision_time_table(prop: str, dimension: int) -> Path:
    return (
        ROOT
        / "output"
        / "summary"
        / "runtimes"
        / "old-runtimes"
        / f"decision-sat-cadical-dim-{dimension}-{prop}-time.csv"
    )


def sat_known_at_least_table(prop: str, dimension: int) -> Path:
    return ROOT / "output" / "summary" / "combined" / "counting" / f"dim-{dimension}-{prop}-known-at-least.csv"


def cp_exact_table(prop: str, dimension: int) -> Path:
    return ROOT / "output" / "summary" / "combined" / "counting" / f"dim-{dimension}-{prop}-full-aut-sym.csv"


def bottom_left_exact_table() -> Path:
    return ROOT / "output" / "summary" / "combined" / "counting" / "SE-bottom-left-0-source-symmetry.csv"


def default_exact_table(backend: Backend, prop: str, dimension: int) -> Path:
    if backend == "sat":
        return sat_exact_table(prop, dimension)
    return cp_exact_table(prop, dimension)


def parse_sat_result_file(path: Path) -> dict[str, str]:
    result: dict[str, str] = {}
    try:
        for raw_line in path.read_text(encoding="utf8").splitlines():
            line = raw_line.strip()
            if line == "SAT":
                result["decision"] = "1"
            elif line == "UNSAT":
                result["decision"] = "0"
                result.setdefault("exact", "0")
            elif line.startswith("Number of models:"):
                result["exact"] = line.split(":", 1)[1].strip()
            elif line.startswith("Number of models so far:"):
                result["known_at_least"] = line.split(":", 1)[1].strip()
            elif line.startswith("Time taken:"):
                result["time"] = line.split(":", 1)[1].strip()
    except OSError:
        return {}
    return result


def parse_cp_stats_file(path: Path) -> dict[str, str]:
    try:
        with path.open("r", encoding="utf8") as handle:
            raw = json.load(handle)
    except (OSError, json.JSONDecodeError):
        return {}

    if raw.get("status") != "OK":
        return {}

    info = raw.get("savilerowInfo", {})
    result: dict[str, str] = {}
    if "SolverSolutionsFound" in info:
        result["exact"] = str(info["SolverSolutionsFound"])
    if "SolverSatisfiable" in info:
        result["decision"] = str(info["SolverSatisfiable"])
        if str(info["SolverSatisfiable"]) == "0":
            result.setdefault("exact", "0")
    if "SolverTotalTime" in info:
        result["solver_time"] = str(info["SolverTotalTime"])
    if "SavileRowTotalTime" in info:
        result["savilerow_time"] = str(info["SavileRowTotalTime"])
    return result


def sat_result_filename(dimension: int, nb_peaks: int, prop: str, face_count: int) -> str:
    return f"dim-{dimension}-peak-{nb_peaks}-{prop}-{face_count}.txt"


def cp_stats_filename(dimension: int, nb_peaks: int, prop: str, face_count: int) -> str:
    return f"model000001-peaks-to-{prop}-dimension-{dimension}-peaks-{nb_peaks}-count-{face_count}.stats.json"


def sat_raw_paths(prop: str, dimension: int, nb_peaks: int, face_count: int, *, decision: bool) -> list[Path]:
    filename = sat_result_filename(dimension, nb_peaks, prop, face_count)
    if decision:
        paths = [
            ROOT / "output" / "raw" / "decision-sat-cadical" / filename,
            *(ROOT / "output" / "raw").glob(f"decision-sat-*/{filename}"),
        ]
    else:
        paths = [
            ROOT / "output" / "raw" / "count-sat-cadical" / filename,
            *(ROOT / "output" / "raw").glob(f"count-sat-*/{filename}"),
        ]
    return _unique_paths(paths)


def cp_raw_paths(prop: str, dimension: int, nb_peaks: int, face_count: int) -> list[Path]:
    filename = cp_stats_filename(dimension, nb_peaks, prop, face_count)
    paths = [
        ROOT / "output" / "raw" / "count-essence-edge-branching-full-symmetry-minion" / filename,
        *(ROOT / "output" / "raw").glob(f"count-essence-*/{filename}"),
        ROOT / "conjure-output" / filename,
        *ROOT.glob(f"results-*/{filename}"),
    ]
    return _unique_paths(paths)


def sat_raw_value(prop: str, dimension: int, nb_peaks: int, face_count: int, kind: CellKind) -> str | None:
    for path in sat_raw_paths(prop, dimension, nb_peaks, face_count, decision=(kind == "decision")):
        if not path.exists():
            continue
        value = parse_sat_result_file(path).get(kind)
        if cell_quality(value, kind) > 0:
            return value
    return None


def cp_raw_exact_value(prop: str, dimension: int, nb_peaks: int, face_count: int) -> str | None:
    for path in cp_raw_paths(prop, dimension, nb_peaks, face_count):
        if not path.exists():
            continue
        value = parse_cp_stats_file(path).get("exact")
        if cell_quality(value, "exact") > 0:
            return value
    return None


def stored_decision_value(prop: str, dimension: int, nb_peaks: int, face_count: int) -> str | None:
    value = csv_cell(sat_decision_table(prop, dimension), face_count, nb_peaks)
    if cell_quality(value, "decision") > 0:
        return value
    value = sat_raw_value(prop, dimension, nb_peaks, face_count, "decision")
    if cell_quality(value, "decision") > 0:
        return value
    return None


def stored_exact_value(backend: Backend, prop: str, dimension: int, nb_peaks: int, face_count: int) -> str | None:
    value = csv_cell(default_exact_table(backend, prop, dimension), face_count, nb_peaks)
    if cell_quality(value, "exact") > 0:
        return value

    if backend == "sat":
        value = sat_raw_value(prop, dimension, nb_peaks, face_count, "exact")
    else:
        value = cp_raw_exact_value(prop, dimension, nb_peaks, face_count)

    if cell_quality(value, "exact") > 0:
        return value
    return None


def bottom_left_exact_value(dimension: int) -> str | None:
    value = dimension_table_cell(bottom_left_exact_table(), dimension)
    if cell_quality(value, "exact") > 0:
        return value
    face_count = face_count_max(dimension)
    return sat_raw_value("SE", dimension, 1, face_count, "exact")


def skip_decision_reason(prop: str, dimension: int, nb_peaks: int, face_count: int) -> str | None:
    if stored_decision_value(prop, dimension, nb_peaks, face_count) is not None:
        return "decision result already stored"
    if stored_exact_value("sat", prop, dimension, nb_peaks, face_count) is not None:
        return "SAT exact result already stored"
    return None


def skip_exact_reason(backend: Backend, prop: str, dimension: int, nb_peaks: int, face_count: int) -> str | None:
    if stored_exact_value(backend, prop, dimension, nb_peaks, face_count) is not None:
        return f"{backend.upper()} exact result already stored"

    decision = stored_decision_value(prop, dimension, nb_peaks, face_count)
    if decision == "0":
        return "decision result is UNSAT"

    return None


def quote_command(parts: Iterable[str | Path]) -> str:
    return " ".join(shlex.quote(str(part)) for part in parts)


def dimension_parampart(dimension: int) -> str:
    for path in (
        ROOT / "intermediate-data" / f"dimension-{dimension}.parampart",
        ROOT / "data" / f"dimension-{dimension}.parampart",
    ):
        if path.exists():
            return path.read_text(encoding="utf8").strip()

    rows = list(permutations(range(1, dimension + 1)))
    row_domain = f"int(1..{dimension})"
    rows_text = [f"[{', '.join(map(str, row))}; {row_domain}]" for row in rows]
    matrix = "[\n    " + ",\n    ".join(rows_text) + f"\n; int(1..{len(rows)})]"
    return "\n".join(
        [
            f"letting nbPermutations be {len(rows)}",
            "letting permutations be",
            f"    {matrix}",
        ]
    )


def cp_param_path(prop: str, dimension: int, nb_peaks: int, face_count: int) -> Path:
    return ROOT / "input" / f"peaks-to-{prop}-dimension-{dimension}-peaks-{nb_peaks}-count-{face_count}.param"


def write_cp_param(prop: str, dimension: int, nb_peaks: int, face_count: int, symmetry: bool) -> Path:
    path = cp_param_path(prop, dimension, nb_peaks, face_count)
    path.parent.mkdir(parents=True, exist_ok=True)
    if symmetry:
        sym = "true"
    else:
        sym = "false"
    path.write_text(
        "\n".join(
            [
                f"letting dimension be {dimension}",
                f"letting nb_peaks be {nb_peaks}",
                f"letting symmetryFlag be {sym}",
                "letting props be",
                "{",
                f"    (1, 1, {prop}, {face_count})",
                "}",
                "",
                dimension_parampart(dimension),
                "",
            ]
        ),
        encoding="utf8",
    )
    return path


def _relative_to_root(path: Path) -> Path:
    try:
        return path.relative_to(ROOT)
    except ValueError:
        return path


def runsolver_parts(result_path: Path) -> list[str | Path]:
    return [
        "/home/rh347/.local/bin/runsolver",
        "-W",
        "3600",
        "-R",
        "18000",
        "-v",
        result_path.with_suffix(result_path.suffix + ".runsolver"),
    ]


def cp_command(param: Path, *, output_dir: str | None = None, solver: str) -> str:
    result_dir = Path(output_dir) if output_dir else ROOT / "conjure-output"
    result_path = result_dir / f"model000001-{param.stem}.stats.json"
    parts: list[str | Path] = [
        *runsolver_parts(result_path),
        "conjure",
        "solve",
        "models/essence-edge-branching/edge.essence",
        _relative_to_root(param) if param.is_absolute() else param,
        f"--use-existing-models=output/raw/count-essence-edge-branching/model000001.eprime",
        "--savilerow-options=-O1",
        f"--solver={solver}",
        "--number-of-solutions=all",
        "--copy-solutions=no",
        "--solutions-in-one-file",
        "--output-format=json",
        
    ]
    if output_dir:
        parts.extend(["-o", output_dir])
    return quote_command(parts)



def sat_command(
    dimension: int,
    nb_peaks: int,
    prop: str,
    face_count: int,
    sym: bool,
    *,
    output_dir: str,
    enumerate_all: bool,
) -> str:
        result_path = Path(output_dir) / sat_result_filename(dimension, nb_peaks, prop, face_count)
        parts: list[str | Path] = [
            *runsolver_parts(result_path),
            "python",
            "models/sat/bio.py",
            "-n",
            str(dimension),
            "--peak-count",
            str(nb_peaks),
            f"--{prop}-count",
            str(face_count),
            "--output",
            output_dir,
        ]
        if enumerate_all:
            parts.append("-a")
        if sym:
            parts.extend(["--partial-sym-break", "0"])
        else:
            parts.append("--complete-sym-break")
        return quote_command(parts)

def yewpar_command(
    dimension: int,
    nb_peaks: int,
    prop: str,
    face_count: int,
    sym: bool,
    *,
    output_dir: str,
) -> str:
        result_path = Path(output_dir) / sat_result_filename(dimension, nb_peaks, prop, face_count)
        parts: list[str | Path] = [
            *runsolver_parts(result_path),
            "../YewPar/build/install/bin/fitness-landscape",
            "-n",
            str(dimension),
            "--peaks",
            str(nb_peaks),
            "--faces",
            str(face_count),
            "--face-type",
            prop,
        ]
        # if sym:
        #     parts.append("--sym-break")
        #     parts.append("")
        # else:
        #     parts.append("--complete-sym-break")
        parts.extend(["--skeleton", "budget", "-b", str(100000)])
        return quote_command(parts) + f" > {shlex.quote(str(result_path))}"
