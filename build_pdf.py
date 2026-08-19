"""
build_pdf.py

Assembles a quarterly SDA Market Update (5pp) from the latest NDIS release.

  1. Loads processed CSVs from data/<quarter>/processed/
  2. Renders templates/update.html via Jinja2 (tokens.css + editorial-archetypes.css inlined)
  3. Writes outputs/<quarter>/update_debug.html
  4. Writes outputs/<quarter>/SDA_Market_Update_<quarter>.pdf via WeasyPrint

Run from this directory:
    python3 build_pdf.py --quarter 2026-Q2
    python3 build_pdf.py --quarter 2026-Q2 --pdf   # also render the PDF

WORKFLOW RULE (same convention as the 76pp report)
  During development, always stop at update_debug.html for browser review.
  Only render the PDF when explicitly requested (pass --pdf).
"""

import argparse
import base64
import os
import sys
from pathlib import Path

_brew_lib = Path("/opt/homebrew/lib")
if _brew_lib.exists():
    os.environ.setdefault("DYLD_LIBRARY_PATH", str(_brew_lib))

HERE       = Path(__file__).resolve().parent
DATA       = HERE / "data"
OUTPUTS    = HERE / "outputs"
TEMPLATES  = HERE / "templates"
ASSETS_DIR = HERE / "assets"
TOKENS_CSS = HERE / "tokens.css"
EDITORIAL_CSS = TEMPLATES / "editorial-archetypes.css"

sys.path.insert(0, str(HERE))

from jinja2 import Environment, FileSystemLoader


def _b64_uri(path: Path, mime: str) -> str:
    data = base64.b64encode(path.read_bytes()).decode("ascii")
    return f"data:{mime};base64,{data}"


def load_context(quarter: str) -> dict:
    """Build the Jinja2 context for one quarter from data/<quarter>/processed/ + outputs/<quarter>/."""
    charts = OUTPUTS / quarter
    logo_path = ASSETS_DIR / "sdahc-logo.png"

    ctx = {
        "report_title":    f"SDA Market Update — {quarter}",
        "tokens_css":      TOKENS_CSS.read_text(),
        "editorial_css":   EDITORIAL_CSS.read_text(),
        "logo_uri":        _b64_uri(logo_path, "image/png") if logo_path.exists() else None,

        # ── Page 1: Cover ──────────────────────────────────────────
        "cover_title":     "MARKET<br>UPDATE",
        "quarter_label":   "Q4 2025–26",
        "cover_tagline":   "A quarterly complement to the SDA Market Report 2026, "
                            "tracking the latest NDIS release against the report's baseline.",

        # ── Page 2: Snapshot ───────────────────────────────────────
        "snapshot_title":       "Supply keeps expanding, led by new-build delivery",
        "snapshot_description": "Enrolled SDA dwellings reached 14,235 nationally in Q4 2025–26, "
                                 "up 22% on Q4 2024–25 and up 80% on Q4 2022–23. New-build stock "
                                 "now accounts for 73% of the total, against 48% four years ago — "
                                 "legacy and existing-stock enrolments have stayed essentially flat "
                                 "across the period. 9,014 participants remain SDA-eligible but not "
                                 "yet housed, pointing to continued undersupply despite the delivery pace.",
        "headline_kpis": [
            {"value": "14,235", "label": "Enrolled SDA dwellings", "sublabel": "+22% vs Q4 2024–25 (11,642)"},
            {"value": "73%",    "label": "New-build share of stock", "sublabel": "up from 48% in Q4 2022–23"},
            {"value": "16,644", "label": "Participants with SDA in use", "sublabel": "+9.7% vs Q4 2024–25"},
            {"value": "9,014",  "label": "Eligible, not yet using SDA", "sublabel": "unmet demand, national"},
            {"value": "$683.8m","label": "Committed SDA funding", "sublabel": "+22% vs Q4 2024–25 ($559.8m)"},
            {"value": "585",    "label": "Active SDA providers", "sublabel": "+14% vs Q4 2024–25 (514)"},
        ],

        # ── Page 3: Chart hero 1 ───────────────────────────────────
        "chart1_kicker":       "FOUR-YEAR TREND",
        "chart1_title":        "New-build supply has nearly tripled since Q4 2022–23, "
                                "while legacy stock stays flat",
        "chart1_interpretive": "National SDA enrolments grew from 7,925 dwellings in Q4 2022–23 to "
                                "14,235 in Q4 2025–26. Almost all of that growth came from new-build "
                                "(including refurbished) stock, which rose from 3,818 to 10,414 dwellings "
                                "over the same four Q4 snapshots. Existing and legacy stock, by contrast, "
                                "has drifted slightly lower — from 4,107 to 3,821 — as older dwellings exit "
                                "the register faster than they're replenished. The result is a steady shift "
                                "in the composition of the register: new-build now represents 73% of all "
                                "enrolled SDA dwellings, up from 48% at the start of the series.",
        "chart1_uri":          _b64_uri(charts / "chart_1_dwelling_growth.png", "image/png")
                                if (charts / "chart_1_dwelling_growth.png").exists() else "",
        "chart1_source":       "Source: NDIA, Supplement P — Specialist Disability Accommodation, Table P.4, Q4 releases 2022–23 to 2025–26.",

        # ── Page 4: Chart hero 2 ───────────────────────────────────
        "chart2_kicker":       "STATE DISTRIBUTION",
        "chart2_title":        "Victoria and NSW together hold over half the national stock",
        "chart2_interpretive": "Victoria leads all jurisdictions with 4,190 enrolled dwellings (29% of "
                                "the national total), followed by NSW at 3,395 (24%) and Queensland at "
                                "2,978 (21%). Together the three largest states account for nearly three "
                                "quarters of national supply. At the other end, the ACT, Tasmania and the "
                                "Northern Territory remain small markets — 213, 183 and 149 dwellings "
                                "respectively — though all three have grown faster in percentage terms than "
                                "the larger states over the past year, off a much smaller base.",
        "chart2_uri":          _b64_uri(charts / "chart_2_state_distribution.png", "image/png")
                                if (charts / "chart_2_state_distribution.png").exists() else "",
        "chart2_source":       "Source: NDIA, Supplement P — Specialist Disability Accommodation, Table P.4, Q4 2025–26.",

        # ── Page 5: Chart hero 3 ───────────────────────────────────
        "chart3_kicker":       "DESIGN CATEGORY MIX",
        "chart3_title":        "High Physical Support now dominates the register, while Basic stock keeps shrinking",
        "chart3_interpretive": "High Physical Support is by far the largest design category nationally, with "
                                "7,173 enrolled dwellings — more than half of all new-build delivery since "
                                "Q4 2022–23 has landed in this category, growing from 2,664 to 7,173 dwellings "
                                "over four years. Improved Liveability (2,066) and Fully Accessible (1,231) "
                                "follow at a distance. Basic is the only category moving in the opposite "
                                "direction: it has declined every year on record, from 2,072 dwellings in "
                                "Q4 2022–23 to 1,862 in Q4 2025–26, even as total stock grew 80% over the same "
                                "period. Multi-Design Category remains a rounding error nationally at 65 dwellings.",
        "chart3_uri":          _b64_uri(charts / "chart_3_design_mix.png", "image/png")
                                if (charts / "chart_3_design_mix.png").exists() else "",
        "chart3_source":       "Source: NDIA, Supplement P — Specialist Disability Accommodation, Table P.5, Q4 2025–26.",

        # ── Page 6: Chart hero 4 ───────────────────────────────────
        "chart4_kicker":       "FUNDING & PROVIDER BASE",
        "chart4_title":        "Committed funding and the active provider base are both growing, but funding is outpacing provider entry",
        "chart4_interpretive": "Annualised SDA funding committed in current plans has grown from $364.9m in "
                                "Q4 2022–23 to $683.8m in Q4 2025–26 — an 87% increase in four years, and up "
                                "22% on Q4 2024–25 alone ($559.8m). The number of active SDA providers has "
                                "grown more slowly, from 472 to 585 over the same period (+24%), though it did "
                                "dip slightly between Q4 2023–24 (594) and Q4 2024–25 (514) before recovering. "
                                "The gap between funding growth and provider growth is consistent with the "
                                "flight-to-quality pattern visible in the design-mix data: capital is "
                                "concentrating in higher-value, higher-support dwellings delivered by a "
                                "provider base that isn't expanding at the same pace.",
        "chart4_uri":          _b64_uri(charts / "chart_4_funding_providers.png", "image/png")
                                if (charts / "chart_4_funding_providers.png").exists() else "",
        "chart4_source":       "Source: NDIA, Supplement P — Specialist Disability Accommodation, Tables P.2 and P.3, Q4 releases 2022–23 to 2025–26.",

        # ── Page 7: Closing ────────────────────────────────────────
        "closing_title":        "WHAT THIS MEANS",
        "closing_body":         "This release confirms the trajectory set out in the SDA Market Report "
                                 "2026: new-build delivery is now the primary driver of register growth, "
                                 "not stock turnover. But the 9,014 participants who are SDA-eligible and "
                                 "not yet housed — a cohort the NDIA only began reporting separately from "
                                 "Q4 2024–25 — show that delivery has not caught up with demand. Note that "
                                 "participant figures from Q4 2022–23 and Q4 2023–24 use a single combined "
                                 "metric ('active participants with SDA supports') and are not directly "
                                 "comparable to the split in-use / eligible-not-using figures reported from "
                                 "Q4 2024–25 onward.",
        "closing_quote":        "“New-build stock has gone from under half to nearly three quarters "
                                 "of the national SDA register in four years.”",
        "closing_source_note":  "Figures are drawn from the NDIA's published quarterly SDA data "
                                 "(Supplement P, Tables P.1 and P.4). See the SDA Market Report 2026 "
                                 "for full methodology.",
        "contact_name":         "SDA Home Choices",
        "contact_email":        "hello@sdahomechoices.com.au",
        "contact_note":         "For the full 76-page SDA Market Report 2026, see sdahomechoices.com.au",
    }
    return ctx


def render_html(quarter: str) -> Path:
    env = Environment(loader=FileSystemLoader(str(TEMPLATES)))
    template = env.get_template("update.html")
    html = template.render(**load_context(quarter))

    out_dir = OUTPUTS / quarter
    out_dir.mkdir(parents=True, exist_ok=True)
    debug_path = out_dir / "update_debug.html"
    debug_path.write_text(html, encoding="utf-8")
    print(f"Wrote {debug_path}")
    return debug_path


def render_pdf(quarter: str, debug_path: Path) -> None:
    from weasyprint import HTML
    out_dir = OUTPUTS / quarter
    pdf_path = out_dir / f"SDA_Market_Update_{quarter}.pdf"
    HTML(string=debug_path.read_text(encoding="utf-8"), base_url=str(TEMPLATES)).write_pdf(str(pdf_path))
    print(f"Wrote {pdf_path}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--quarter", required=True, help="e.g. 2026-Q2")
    parser.add_argument("--pdf", action="store_true", help="also render the PDF (default: HTML only)")
    args = parser.parse_args()

    debug_path = render_html(args.quarter)
    if args.pdf:
        render_pdf(args.quarter, debug_path)
    else:
        print("Stopped at HTML preview. Pass --pdf to also render the PDF.")
