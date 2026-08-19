"""
build_charts.py

Generates the 2 charts used in the quarterly update, styled with the same
matplotlib theme as the SDA Market Report 2026 (tokens.apply_matplotlib_theme
+ chart_premium helpers).

Run from this directory's parent:
    python3 scripts/build_charts.py --quarter 2026-Q2

Reads:
    data/<quarter>/processed/*.csv

Writes:
    outputs/<quarter>/chart_1.png
    outputs/<quarter>/chart_2.png
"""

import argparse
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(HERE))

import matplotlib.pyplot as plt
import pandas as pd

from tokens import apply_matplotlib_theme, COLOR_CHART_PRIMARY, COLOR_CHART_SECONDARY
import chart_premium as cp

apply_matplotlib_theme()


def build_chart_1(quarter: str) -> None:
    """National trend — mirror the historical_trends.csv line chart from the main report."""
    processed = HERE / "data" / quarter / "processed"
    out_path = HERE / "outputs" / quarter / "chart_1.png"
    out_path.parent.mkdir(parents=True, exist_ok=True)

    # TODO: load the relevant processed CSV and plot.
    # Placeholder so the pipeline runs end-to-end before real data arrives.
    fig, ax = plt.subplots(figsize=(10, 5.5), dpi=300)
    ax.text(0.5, 0.5, "chart_1 placeholder — wire up data/%s/processed" % quarter,
            ha="center", va="center", fontsize=10, color=COLOR_CHART_SECONDARY)
    ax.axis("off")
    fig.savefig(out_path, dpi=300, bbox_inches="tight")
    plt.close(fig)
    print(f"Wrote {out_path}")


def build_chart_2(quarter: str) -> None:
    """Regional or design-category cut."""
    out_path = HERE / "outputs" / quarter / "chart_2.png"
    out_path.parent.mkdir(parents=True, exist_ok=True)

    fig, ax = plt.subplots(figsize=(10, 5.5), dpi=300)
    ax.text(0.5, 0.5, "chart_2 placeholder — wire up data/%s/processed" % quarter,
            ha="center", va="center", fontsize=10, color=COLOR_CHART_PRIMARY)
    ax.axis("off")
    fig.savefig(out_path, dpi=300, bbox_inches="tight")
    plt.close(fig)
    print(f"Wrote {out_path}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--quarter", required=True, help="e.g. 2026-Q2")
    args = parser.parse_args()
    build_chart_1(args.quarter)
    build_chart_2(args.quarter)
