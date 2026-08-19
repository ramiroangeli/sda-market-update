"""
chart_premium.py

Premium visual helpers for SDA Report 2026 matplotlib charts.
Provides gradient bar fills, editorial title treatment, and accent effects.

Import AFTER tokens.py — shares the same brand token constants.
"""

import numpy as np
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors
from PIL import Image, ImageOps

from tokens import (
    COLOR_BRAND_PRIMARY,
    COLOR_BRAND_DARK_DEEP,
    COLOR_CHART_TERTIARY,
    COLOR_TEXT_FG,
    COLOR_TEXT_FG_MUTED,
    FONT_SERIF,
    FONT_SANS,
)


# ── Color utilities ───────────────────────────────────────────────────────────

def _lighten(color, amount: float = 0.20):
    """Mix `color` with white by `amount` (0 = unchanged, 1 = white)."""
    r, g, b = mcolors.to_rgb(color)
    return (
        min(1.0, r + (1.0 - r) * amount),
        min(1.0, g + (1.0 - g) * amount),
        min(1.0, b + (1.0 - b) * amount),
    )


# ── Gradient bar primitives ───────────────────────────────────────────────────

def gradient_hbar(ax, y_pos: float, value: float, height: float,
                  color, lighten: float = 0.20, left: float = 0.0) -> None:
    """
    Horizontal bar with a left → right gradient.
    Left edge: full `color`. Right edge: lightened by `lighten`.
    Uses a single imshow call — O(1) regardless of bar count.
    """
    if value <= 0:
        return
    cmap = mcolors.LinearSegmentedColormap.from_list(
        '_gh', [mcolors.to_rgb(color), _lighten(color, lighten)], N=256
    )
    img = np.linspace(0, 1, 256).reshape(1, 256)
    ax.imshow(
        img, aspect='auto', cmap=cmap,
        extent=[left, left + value,
                y_pos - height / 2, y_pos + height / 2],
        zorder=3, origin='lower', interpolation='bilinear',
    )


def gradient_vbar(ax, x_pos: float, value: float, width: float,
                  color, lighten: float = 0.20, bottom: float = 0.0) -> None:
    """
    Vertical bar with a bottom → top gradient.
    Bottom: lightened. Top: full `color`.
    """
    if value <= 0:
        return
    cmap = mcolors.LinearSegmentedColormap.from_list(
        '_gv', [_lighten(color, lighten), mcolors.to_rgb(color)], N=256
    )
    img = np.linspace(0, 1, 256).reshape(256, 1)
    ax.imshow(
        img, aspect='auto', cmap=cmap,
        extent=[x_pos - width / 2, x_pos + width / 2,
                bottom, bottom + value],
        zorder=3, origin='lower', interpolation='bilinear',
    )


def accent_stripe_hbar(ax, y_pos: float, height: float,
                       scale: float, color=None) -> None:
    """
    Thin bright left-edge accent stripe on the leading horizontal bar.
    `scale` is the chart's x-axis reference value (e.g. data maximum).
    """
    if color is None:
        color = COLOR_CHART_TERTIARY
    ax.barh(
        y_pos, scale * 0.007, left=0,
        height=height + 0.04,
        color=color, zorder=5, linewidth=0,
    )


# ── Title & editorial decoration ──────────────────────────────────────────────

def add_title_rule(ax, color=COLOR_BRAND_PRIMARY, linewidth: float = 1.5) -> None:
    """
    Editorial accent rule: a thin horizontal line at the top of the axes,
    sitting between the subtitle and the chart body.
    """
    line = plt.Line2D(
        [0, 1], [1.0, 1.0],
        transform=ax.transAxes,
        color=color, linewidth=linewidth,
        solid_capstyle='butt', clip_on=False, zorder=10,
    )
    ax.add_artist(line)


def add_chart_title_premium(fig, ax, title: str, subtitle: str = "", title_y: float = None,
                             title_fontsize: float = 11, subtitle_fontsize: float = 7.5) -> None:
    """
    Premium title block:
      • Serif, bold  — strong typographic anchor (default 11pt)
      • Sans, muted — quiet context line (omitted when subtitle is empty, default 7.5pt)
      • 1.5pt brand-blue rule at the top of the axes — editorial separator
    When no subtitle, the title sits higher for breathing room between title and plot.
    Pass title_y to override the default vertical position (axes fraction above 1.0).
    Pass title_fontsize/subtitle_fontsize to scale up for charts displayed at a
    smaller width than they were authored for (e.g. half-page figures).
    """
    if title_y is None:
        title_y = 1.06 if not subtitle else 1.07
    fig.text(
        0.0, title_y, title,
        transform=ax.transAxes,
        fontfamily=FONT_SERIF, fontsize=title_fontsize, fontweight="bold",
        color=COLOR_TEXT_FG, va="bottom", ha="left",
    )
    if subtitle:
        fig.text(
            0.0, 1.018, subtitle,
            transform=ax.transAxes,
            fontfamily=FONT_SANS, fontsize=subtitle_fontsize, fontweight="400",
            color=COLOR_TEXT_FG_MUTED, va="bottom", ha="left",
        )
    add_title_rule(ax)


# ── Column-pair height matching ───────────────────────────────────────────────
# Reusable whenever two charts are shown side by side (e.g. a 50/50 flex row) and
# need to line up top and bottom exactly. Matching figsize alone does NOT
# guarantee matching pixel dimensions when savefig uses bbox_inches="tight" (or
# similar auto-cropping) — the crop depends on drawn content (legend, tick
# labels, etc.), not the nominal figure size. This pads the shorter image with
# solid background colour below its content (never stretches/distorts either
# image) so both end up exactly the same pixel height.
def match_heights(path_a: str, path_b: str, bg_color: str = "white") -> None:
    """
    Equalise the pixel height of two PNGs meant to share a column in the report,
    by padding the shorter one with solid colour below it. Overwrites both files
    in place. Never upscales/stretches — only adds padding.
    """
    img_a = Image.open(path_a)
    img_b = Image.open(path_b)

    target_height = max(img_a.height, img_b.height)

    for path, img in [(path_a, img_a), (path_b, img_b)]:
        if img.height < target_height:
            padded = ImageOps.pad(
                img,
                (img.width, target_height),
                color=bg_color,
                centering=(0.5, 0.0),  # anchor to top — padding added below
            )
            padded.save(path)
