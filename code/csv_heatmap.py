#!/usr/bin/env python3
"""Render a numeric CSV as a heatmap image."""

from __future__ import annotations

import argparse
import csv
import math
import sys
from copy import copy
from pathlib import Path

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
import numpy as np
from matplotlib import colors, ticker

MISSING_MARKERS = {"", "na", "nan", "none", "null", "initialised"}
SUPPORTED_FORMATS = {"svg", "png", "pdf"}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Turn a numeric CSV table into a colour-coded heatmap. "
            "The first column is treated as row labels."
        )
    )
    parser.add_argument("input_csv", type=Path, help="Path to the input CSV file.")
    parser.add_argument(
        "-o",
        "--output",
        type=Path,
        help="Output image path. Defaults to <input-stem>-heatmap.svg.",
    )
    parser.add_argument(
        "--format",
        choices=sorted(SUPPORTED_FORMATS),
        default="svg",
        help="Image format to write when the output path has no extension.",
    )
    parser.add_argument(
        "--title",
        help="Optional figure title. Defaults to a title based on the input filename.",
    )
    parser.add_argument(
        "--cmap",
        default="viridis",
        help="Matplotlib colormap to use. Default: viridis.",
    )
    parser.add_argument(
        "--linear-scale",
        action="store_true",
        help="Use a linear colour scale instead of a log scale.",
    )
    parser.add_argument(
        "--value-format",
        default=".3g",
        help="Python format specifier for cell annotations. Default: .3g.",
    )
    return parser.parse_args()


def load_csv(path: Path) -> tuple[str, list[str], list[str], np.ndarray]:
    with path.open("r", encoding="utf8", newline="") as handle:
        rows = list(csv.reader(handle))

    if not rows:
        raise ValueError(f"{path} is empty.")

    header = rows[0]
    if len(header) < 2:
        raise ValueError(f"{path} must have at least one row-label column and one data column.")

    row_axis_label = header[0].strip() or "Row"
    column_labels = [cell.strip() for cell in header[1:]]
    row_labels: list[str] = []
    values: list[list[float]] = []

    for line_number, row in enumerate(rows[1:], start=2):
        if not row or not any(cell.strip() for cell in row):
            continue

        if len(row) != len(header):
            raise ValueError(
                f"{path}:{line_number} has {len(row)} columns, expected {len(header)}."
            )

        row_labels.append(row[0].strip())
        parsed_row: list[float] = []
        for raw_value in row[1:]:
            text = raw_value.strip()
            if text.lower() in MISSING_MARKERS:
                parsed_row.append(np.nan)
                continue

            try:
                parsed_row.append(float(text))
            except ValueError as exc:
                raise ValueError(
                    f"{path}:{line_number} contains a non-numeric value {raw_value!r}."
                ) from exc
        values.append(parsed_row)

    if not values:
        raise ValueError(f"{path} has no data rows.")

    return row_axis_label, column_labels, row_labels, np.array(values, dtype=float)


def infer_axis_labels(row_axis_label: str) -> tuple[str, str]:
    if "/" in row_axis_label:
        y_label, x_label = [part.strip() for part in row_axis_label.split("/", 1)]
        if y_label and x_label:
            return x_label, y_label
    return "Column", row_axis_label.strip() or "Row"


def infer_title(path: Path) -> str:
    return path.stem.replace("-", " ")


def resolve_output_path(input_csv: Path, output: Path | None, default_format: str) -> tuple[Path, str]:
    if output is None:
        return input_csv.with_name(f"{input_csv.stem}-heatmap.{default_format}"), default_format

    if output.suffix:
        detected_format = output.suffix[1:].lower()
        if detected_format not in SUPPORTED_FORMATS:
            raise ValueError(
                f"Unsupported output format {output.suffix!r}. "
                f"Use one of: {', '.join(sorted(SUPPORTED_FORMATS))}."
            )
        return output, detected_format

    return output.with_suffix(f".{default_format}"), default_format


def make_norm(
    data: np.ndarray, use_log_scale: bool
) -> tuple[np.ndarray, colors.Normalize, str, bool]:
    finite_values = data[np.isfinite(data)]
    if finite_values.size == 0:
        return data.copy(), colors.Normalize(vmin=0.0, vmax=1.0), "Missing data", False

    plot_data = data.copy()
    label = "Value"

    if use_log_scale:
        positive_values = finite_values[finite_values > 0]
        if positive_values.size == 0:
            raise ValueError("Log scaling requires at least one positive value.")

        min_positive = float(np.min(positive_values))
        max_positive = float(np.max(positive_values))
        non_positive_mask = np.isfinite(plot_data) & (plot_data <= 0)
        if np.any(non_positive_mask):
            print(
                "Warning: non-positive values were mapped to the smallest positive value "
                "to keep log scaling valid.",
                file=sys.stderr,
            )
            plot_data[non_positive_mask] = min_positive

        if math.isclose(min_positive, max_positive):
            min_positive *= 0.9
            max_positive *= 1.1

        return (
            plot_data,
            colors.LogNorm(vmin=min_positive, vmax=max_positive),
            f"{label} (log scale)",
            True,
        )

    min_value = float(np.min(finite_values))
    max_value = float(np.max(finite_values))
    if math.isclose(min_value, max_value):
        if min_value == 0:
            max_value = 1.0
        else:
            min_value *= 0.9
            max_value *= 1.1

    return plot_data, colors.Normalize(vmin=min_value, vmax=max_value), label, True


def choose_figure_size(rows: int, cols: int) -> tuple[float, float]:
    width = max(7.0, cols * 0.45 + 2.8)
    height = max(4.5, rows * 0.18 + 2.0)
    return width, height


def annotate_cells(
    ax: plt.Axes,
    data: np.ndarray,
    norm: colors.Normalize,
    value_format: str,
) -> None:
    finite_values = data[np.isfinite(data)]
    if finite_values.size == 0:
        return

    for row_index in range(data.shape[0]):
        for col_index in range(data.shape[1]):
            value = data[row_index, col_index]
            if not np.isfinite(value):
                continue

            text_color = "white" if norm(value) < 0.45 else "black"
            ax.text(
                col_index,
                row_index,
                format(value, value_format),
                ha="center",
                va="center",
                fontsize=7,
                color=text_color,
            )


def render_heatmap(
    data: np.ndarray,
    row_labels: list[str],
    column_labels: list[str],
    x_label: str,
    y_label: str,
    title: str,
    cmap_name: str,
    value_format: str,
    output_path: Path,
    output_format: str,
    use_log_scale: bool,
) -> None:
    plot_data, norm, colorbar_label, has_finite_values = make_norm(
        data, use_log_scale=use_log_scale
    )
    masked_data = np.ma.masked_invalid(plot_data)

    cmap = copy(plt.get_cmap(cmap_name))
    cmap.set_bad("#f2f2f2")

    fig_width, fig_height = choose_figure_size(*data.shape)
    fig, ax = plt.subplots(figsize=(fig_width, fig_height), constrained_layout=True)

    image = ax.imshow(masked_data, cmap=cmap, norm=norm, aspect="auto")

    ax.set_xticks(np.arange(len(column_labels)), labels=column_labels)
    ax.set_yticks(np.arange(len(row_labels)), labels=row_labels)
    plt.setp(ax.get_xticklabels(), rotation=45, ha="right", rotation_mode="anchor")
    ax.tick_params(axis="x", labelsize=8)
    ax.tick_params(axis="y", labelsize=6 if len(row_labels) > 40 else 8)

    ax.set_xlabel(x_label)
    ax.set_ylabel(y_label)
    ax.set_title(title)

    ax.set_xticks(np.arange(-0.5, len(column_labels), 1), minor=True)
    ax.set_yticks(np.arange(-0.5, len(row_labels), 1), minor=True)
    ax.grid(which="minor", color="white", linestyle="-", linewidth=0.7)
    ax.tick_params(which="minor", bottom=False, left=False)

    if has_finite_values:
        colorbar = fig.colorbar(image, ax=ax)
        colorbar.set_label(colorbar_label)
        if use_log_scale:
            colorbar.formatter = ticker.LogFormatterMathtext()
            colorbar.update_ticks()
    else:
        ax.text(
            0.5,
            0.5,
            "No finite numeric values",
            transform=ax.transAxes,
            ha="center",
            va="center",
            fontsize=12,
            color="#555555",
            bbox={"facecolor": "white", "edgecolor": "#cccccc", "boxstyle": "round,pad=0.4"},
        )

    annotate_cells(ax, data, norm, value_format=value_format)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    save_kwargs = {"format": output_format, "bbox_inches": "tight"}
    if output_format in {"png"}:
        save_kwargs["dpi"] = 200
    fig.savefig(output_path, **save_kwargs)
    plt.close(fig)


def main() -> int:
    args = parse_args()

    row_axis_label, column_labels, row_labels, data = load_csv(args.input_csv)
    output_path, output_format = resolve_output_path(args.input_csv, args.output, args.format)
    x_label, y_label = infer_axis_labels(row_axis_label)

    render_heatmap(
        data=data,
        row_labels=row_labels,
        column_labels=column_labels,
        x_label=x_label,
        y_label=y_label,
        title=args.title or infer_title(args.input_csv),
        cmap_name=args.cmap,
        value_format=args.value_format,
        output_path=output_path,
        output_format=output_format,
        use_log_scale=not args.linear_scale,
    )

    print(output_path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
