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
    """
    Build the Jinja2 context for one quarter.

    TODO once the new NDIS Supplement P file is in data/<quarter>/raw/:
      - run scripts/extract_quarterly.py to populate data/<quarter>/processed/
      - run scripts/build_charts.py to populate outputs/<quarter>/chart_*.png
      - replace the placeholder values below with real figures
    """
    processed = DATA / quarter / "processed"
    charts    = OUTPUTS / quarter

    logo_path = ASSETS_DIR / "sdahc-logo.png"

    ctx = {
        "report_title":    f"SDA Market Update — {quarter}",
        "tokens_css":      TOKENS_CSS.read_text(),
        "editorial_css":   EDITORIAL_CSS.read_text(),
        "logo_uri":        _b64_uri(logo_path, "image/png") if logo_path.exists() else None,

        # ── Page 1: Cover ──────────────────────────────────────────
        "cover_title":     "MARKET<br>UPDATE",
        "quarter_label":   quarter,
        "cover_tagline":   "A quarterly complement to the SDA Market Report 2026, "
                            "tracking the latest NDIS release against the report's baseline.",

        # ── Page 2: Snapshot ───────────────────────────────────────
        "snapshot_title":       "PLACEHOLDER — RUN EXTRACTOR",
        "snapshot_description": "Replace with 2–3 sentences of context once the new "
                                 "Supplement P release has been processed.",
        "headline_kpis": [
            {"value": "—", "label": "Participants with SDA in use", "sublabel": "national, QoQ"},
            {"value": "—", "label": "Enrolled dwellings",            "sublabel": "national, QoQ"},
            {"value": "—", "label": "New builds this quarter"},
            {"value": "—", "label": "Funding committed"},
        ],

        # ── Page 3: Chart hero 1 ───────────────────────────────────
        "chart1_kicker":       "NATIONAL TREND",
        "chart1_title":        "PLACEHOLDER TITLE",
        "chart1_interpretive": "Interpretive paragraph — what changed this quarter and why it matters.",
        "chart1_uri":          _b64_uri(charts / "chart_1.png", "image/png") if (charts / "chart_1.png").exists() else "",
        "chart1_source":       f"Source: NDIA, Quarterly SDA Data (Supplement P), {quarter}.",

        # ── Page 4: Chart hero 2 ───────────────────────────────────
        "chart2_kicker":       "REGIONAL / SEGMENT CUT",
        "chart2_title":        "PLACEHOLDER TITLE",
        "chart2_interpretive": "Interpretive paragraph — secondary cut of the data (state, design category, etc.).",
        "chart2_uri":          _b64_uri(charts / "chart_2.png", "image/png") if (charts / "chart_2.png").exists() else "",
        "chart2_source":       f"Source: NDIA, Quarterly SDA Data (Supplement P), {quarter}.",

        # ── Page 5: Closing ────────────────────────────────────────
        "closing_title":        "WHAT THIS MEANS",
        "closing_body":         "Closing commentary tying this quarter's release back to the "
                                 "SDA Market Report 2026 baseline and forward outlook.",
        "closing_quote":        "“Optional pull quote or key takeaway.”",
        "closing_source_note":  "Figures are drawn from the NDIA's published quarterly SDA data. "
                                 "See the SDA Market Report 2026 for full methodology.",
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
