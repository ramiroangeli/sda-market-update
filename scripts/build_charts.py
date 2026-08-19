"""
build_charts.py

Generates the 2 charts for the Q4 2025-26 quarterly update, styled with the
same matplotlib theme as the SDA Market Report 2026 (tokens.apply_matplotlib_theme
+ chart_premium gradient bars).

Run from this directory's parent:
    python3 scripts/build_charts.py

Reads:
    data/2025-26-Q4/processed/q4_trend_national.csv
    data/2025-26-Q4/processed/q4_trend_by_state.csv

Writes:
    outputs/2025-26-Q4/chart_1_dwelling_growth.png   — Q4-over-Q4 stock composition, 4 years
    outputs/2025-26-Q4/chart_2_state_distribution.png — dwellings by state, current quarter
"""

import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(HERE))

import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import pandas as pd

from tokens import (
    apply_matplotlib_theme,
    COLOR_CHART_PRIMARY,
    COLOR_CHART_SECONDARY,
    COLOR_CHART_TERTIARY,
    COLOR_CHART_NEUTRAL,
    COLOR_CHART_POSITIVE,
    COLOR_TEXT_FG,
    COLOR_TEXT_FG_MUTED,
    FONT_SANS,
)
import chart_premium as cp

apply_matplotlib_theme()

QUARTER   = "2025-26-Q4"
DATA_DIR  = HERE / "data" / QUARTER / "processed"
OUT_DIR   = HERE / "outputs" / QUARTER
OUT_DIR.mkdir(parents=True, exist_ok=True)

PERIOD_LABELS = {
    "Q4 2022-23": "Q4\n2022–23",
    "Q4 2023-24": "Q4\n2023–24",
    "Q4 2024-25": "Q4\n2024–25",
    "Q4 2025-26": "Q4\n2025–26",
}
STATE_ORDER = ["NSW", "VIC", "QLD", "WA", "SA", "TAS", "ACT", "NT"]
DESIGN_LABELS = {
    "design_high_physical_support": "High Physical\nSupport",
    "design_improved_liveability":  "Improved\nLiveability",
    "design_robust":                "Robust",
    "design_fully_accessible":      "Fully\nAccessible",
    "design_basic":                 "Basic",
    "design_multi_category":        "Multi-Design\nCategory",
}


def _parse_currency(series: pd.Series) -> pd.Series:
    return series.replace(r"[\$,]", "", regex=True).astype(float)


def build_chart_1() -> None:
    """Stacked bar: existing/legacy stock vs new-build stock, across the 4 Q4 snapshots."""
    df = pd.read_csv(DATA_DIR / "q4_trend_national.csv")
    df["period_label"] = df["period"].map(PERIOD_LABELS)
    df["existing_legacy"] = df["dwellings_existing"] + df["dwellings_legacy"]
    df["new_build_all"] = df["dwellings_new_build"] + df["dwellings_new_build_refurb"]

    fig, ax = plt.subplots(figsize=(10, 5.6), dpi=300)
    x = range(len(df))
    width = 0.56

    ax.bar(x, df["existing_legacy"], width, color=COLOR_CHART_NEUTRAL,
           label="Existing / legacy stock", zorder=3)
    ax.bar(x, df["new_build_all"], width, bottom=df["existing_legacy"],
           color=COLOR_CHART_PRIMARY, label="New build (incl. refurbished)", zorder=3)

    for i, row in df.iterrows():
        ax.text(i, row["dwellings_total"] + 220, f"{int(row['dwellings_total']):,}",
                 ha="center", va="bottom", fontsize=10.5, fontweight="bold",
                 color=COLOR_TEXT_FG, family=FONT_SANS)

    ax.set_xticks(list(x))
    ax.set_xticklabels(df["period_label"], fontsize=9, color=COLOR_TEXT_FG_MUTED)
    ax.yaxis.set_major_formatter(mticker.FuncFormatter(lambda v, _: f"{int(v):,}"))
    ax.set_ylim(0, df["dwellings_total"].max() * 1.15)
    ax.set_ylabel("Enrolled SDA dwellings", fontsize=9, color=COLOR_TEXT_FG_MUTED)

    ax.spines[["top", "right"]].set_visible(False)
    ax.spines[["left", "bottom"]].set_color(COLOR_CHART_NEUTRAL)
    ax.tick_params(axis="y", labelsize=8.5, colors=COLOR_TEXT_FG_MUTED)
    ax.grid(axis="y", color="#EEF2F7", linewidth=0.7, zorder=0)
    ax.set_axisbelow(True)

    ax.legend(loc="upper left", frameon=False, fontsize=8.5, handlelength=1.2, handleheight=1.2)

    fig.tight_layout()
    out_path = OUT_DIR / "chart_1_dwelling_growth.png"
    fig.savefig(out_path, dpi=300, bbox_inches="tight")
    plt.close(fig)
    print(f"Wrote {out_path}")


def build_chart_2() -> None:
    """Horizontal gradient bars: dwellings by state, current quarter (Q4 2025-26)."""
    df = pd.read_csv(DATA_DIR / "q4_trend_by_state.csv")
    current = df[df["period"] == "Q4 2025-26"].set_index("state")
    current = current.reindex(STATE_ORDER).dropna(subset=["dwellings_total"])
    current = current.sort_values("dwellings_total", ascending=True)

    fig, ax = plt.subplots(figsize=(10, 5.6), dpi=300)
    y_positions = range(len(current))
    max_val = current["dwellings_total"].max()

    for i, (state, row) in enumerate(current.iterrows()):
        color = COLOR_CHART_PRIMARY if i == len(current) - 1 else COLOR_CHART_SECONDARY
        cp.gradient_hbar(ax, i, row["dwellings_total"], height=0.62, color=color, lighten=0.35)
        ax.text(row["dwellings_total"] + max_val * 0.015, i, f"{int(row['dwellings_total']):,}",
                 va="center", ha="left", fontsize=9.5, fontweight="bold",
                 color=COLOR_TEXT_FG, family=FONT_SANS)

    ax.set_yticks(list(y_positions))
    ax.set_yticklabels(current.index, fontsize=10, color=COLOR_TEXT_FG)
    ax.set_xlim(0, max_val * 1.18)
    ax.xaxis.set_major_formatter(mticker.FuncFormatter(lambda v, _: f"{int(v):,}"))
    ax.set_xlabel("Enrolled SDA dwellings — Q4 2025–26", fontsize=9, color=COLOR_TEXT_FG_MUTED)

    ax.spines[["top", "right", "left"]].set_visible(False)
    ax.spines["bottom"].set_color(COLOR_CHART_NEUTRAL)
    ax.tick_params(axis="both", length=0)
    ax.tick_params(axis="x", labelsize=8.5, colors=COLOR_TEXT_FG_MUTED)
    ax.grid(axis="x", color="#EEF2F7", linewidth=0.7, zorder=0)
    ax.set_axisbelow(True)

    fig.tight_layout()
    out_path = OUT_DIR / "chart_2_state_distribution.png"
    fig.savefig(out_path, dpi=300, bbox_inches="tight")
    plt.close(fig)
    print(f"Wrote {out_path}")


def build_chart_3() -> None:
    """Horizontal gradient bars: dwellings by design category, current quarter (Q4 2025-26)."""
    df = pd.read_csv(DATA_DIR / "q4_design_mix_trend_national.csv")
    current = df[df["period"] == "Q4 2025-26"].iloc[0]
    current = current[list(DESIGN_LABELS)].sort_values(ascending=True)

    fig, ax = plt.subplots(figsize=(10, 5.6), dpi=300)
    max_val = current.max()

    for i, (col, value) in enumerate(current.items()):
        color = COLOR_CHART_PRIMARY if i == len(current) - 1 else COLOR_CHART_SECONDARY
        cp.gradient_hbar(ax, i, value, height=0.62, color=color, lighten=0.35)
        ax.text(value + max_val * 0.015, i, f"{int(value):,}",
                 va="center", ha="left", fontsize=9.5, fontweight="bold",
                 color=COLOR_TEXT_FG, family=FONT_SANS)

    ax.set_yticks(range(len(current)))
    ax.set_yticklabels([DESIGN_LABELS[c] for c in current.index], fontsize=9.5, color=COLOR_TEXT_FG)
    ax.set_xlim(0, max_val * 1.18)
    ax.xaxis.set_major_formatter(mticker.FuncFormatter(lambda v, _: f"{int(v):,}"))
    ax.set_xlabel("Enrolled SDA dwellings — Q4 2025–26", fontsize=9, color=COLOR_TEXT_FG_MUTED)

    ax.spines[["top", "right", "left"]].set_visible(False)
    ax.spines["bottom"].set_color(COLOR_CHART_NEUTRAL)
    ax.tick_params(axis="both", length=0)
    ax.tick_params(axis="x", labelsize=8.5, colors=COLOR_TEXT_FG_MUTED)
    ax.grid(axis="x", color="#EEF2F7", linewidth=0.7, zorder=0)
    ax.set_axisbelow(True)

    fig.tight_layout()
    out_path = OUT_DIR / "chart_3_design_mix.png"
    fig.savefig(out_path, dpi=300, bbox_inches="tight")
    plt.close(fig)
    print(f"Wrote {out_path}")


def build_chart_4() -> None:
    """Committed SDA funding (bars) vs active providers (line), across the 4 Q4 snapshots."""
    df = pd.read_csv(DATA_DIR / "q4_trend_national.csv")
    df["period_label"] = df["period"].map(PERIOD_LABELS)
    df["funding_m"] = _parse_currency(df["funding_sda_committed"]) / 1_000_000

    fig, ax = plt.subplots(figsize=(10, 5.6), dpi=300)
    ax2 = ax.twinx()
    x = range(len(df))
    width = 0.5

    ax.bar(x, df["funding_m"], width, color=COLOR_CHART_PRIMARY, zorder=3,
           label="Committed SDA funding ($m)")
    for i, v in enumerate(df["funding_m"]):
        ax.text(i, v / 2, f"${v:,.0f}m",
                 ha="center", va="center", fontsize=10, fontweight="bold",
                 color="white", family=FONT_SANS)

    ax2.plot(x, df["providers_active"], color=COLOR_CHART_POSITIVE, marker="o",
              markersize=6, linewidth=2, zorder=4, label="Active SDA providers")
    n = len(df)
    for i, v in enumerate(df["providers_active"]):
        if i not in (0, n - 1):
            continue
        ax2.annotate(f"{int(v):,} providers", (i, v), textcoords="offset points", xytext=(0, 11),
                      ha="center", fontsize=9.5, fontweight="bold",
                      color=COLOR_CHART_POSITIVE, family=FONT_SANS)

    ax.set_xticks(list(x))
    ax.set_xticklabels(df["period_label"], fontsize=9, color=COLOR_TEXT_FG_MUTED)
    ax.set_ylim(0, df["funding_m"].max() * 1.2)
    ax2.set_ylim(0, df["providers_active"].max() * 1.35)
    ax.yaxis.set_major_formatter(mticker.FuncFormatter(lambda v, _: f"${int(v):,}m"))
    ax.set_ylabel("Committed SDA funding ($m)", fontsize=9, color=COLOR_TEXT_FG_MUTED)
    ax2.set_ylabel("Active SDA providers", fontsize=9, color=COLOR_TEXT_FG_MUTED)

    ax.spines[["top"]].set_visible(False)
    ax2.spines[["top"]].set_visible(False)
    ax.spines[["left", "bottom"]].set_color(COLOR_CHART_NEUTRAL)
    ax2.spines[["right"]].set_color(COLOR_CHART_NEUTRAL)
    ax.tick_params(axis="y", labelsize=8.5, colors=COLOR_TEXT_FG_MUTED)
    ax2.tick_params(axis="y", labelsize=8.5, colors=COLOR_TEXT_FG_MUTED)
    ax.grid(axis="y", color="#EEF2F7", linewidth=0.7, zorder=0)
    ax2.grid(False)
    ax.set_axisbelow(True)
    ax2.set_axisbelow(True)

    lines1, labels1 = ax.get_legend_handles_labels()
    lines2, labels2 = ax2.get_legend_handles_labels()
    ax.legend(lines1 + lines2, labels1 + labels2, loc="upper left", frameon=False,
              fontsize=8.5, handlelength=1.2, handleheight=1.2)

    fig.tight_layout()
    out_path = OUT_DIR / "chart_4_funding_providers.png"
    fig.savefig(out_path, dpi=300, bbox_inches="tight")
    plt.close(fig)
    print(f"Wrote {out_path}")


if __name__ == "__main__":
    build_chart_1()
    build_chart_2()
    build_chart_3()
    build_chart_4()
