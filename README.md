# SDA Market Update

Quarterly 5-page complement to the [SDA Market Report 2026](../ndis-python-v2) —
analysis of each new NDIS quarterly release (Supplement P), in the same
editorial visual system as the full report (Playfair Display / Source Sans 3,
brand blue/navy palette, WeasyPrint + Jinja2 pipeline).

This is one persistent repo, reused every quarter — not a new repo per release.

## Quarterly workflow

1. Drop the new NDIS Excel release into `data/<quarter>/raw/`
   (e.g. `data/2026-Q2/raw/Supplement_P_2026_Q2.xlsx`)
2. `python3 scripts/extract_quarterly.py --quarter 2026-Q2`
   → writes clean CSVs to `data/2026-Q2/processed/`
3. `python3 scripts/build_charts.py --quarter 2026-Q2`
   → writes `outputs/2026-Q2/chart_1.png`, `chart_2.png`
4. Fill in the real copy/KPIs in `build_pdf.py::load_context()`
5. `python3 build_pdf.py --quarter 2026-Q2`
   → writes `outputs/2026-Q2/update_debug.html` for review in the browser
6. Once approved, `python3 build_pdf.py --quarter 2026-Q2 --pdf`
   → writes `outputs/2026-Q2/SDA_Market_Update_2026-Q2.pdf`

**Rule**: never render the PDF until the HTML preview has been reviewed and
explicitly approved — same convention as the main report.

## What's shared with the main report vs. specific to this one

Copied once from `ndis-python-v2` (design system, not duplicated data/content):
- `tokens.py`, `tokens.css` — brand colors, typography, spacing
- `fonts/` — Playfair Display, Source Sans 3, Barlow Condensed, Bebas Neue
- `chart_premium.py` — matplotlib chart styling helpers
- `templates/editorial-archetypes.css` — the reusable page-archetype system
  (cover, market-snapshot, chart-hero, closing, etc.)

If the master tokens in `ndis-python-v2` change, re-copy the four items above —
there's no automatic sync between the two repos.

Specific to this repo: `templates/update.html` (5-page layout), `build_pdf.py`,
`scripts/extract_quarterly.py`, `scripts/build_charts.py`, and everything in `data/`
and `outputs/`.

## Structure

```
sda-market-update/
├── data/<quarter>/raw/          # NDIS Excel as downloaded
├── data/<quarter>/processed/    # clean CSVs
├── tokens.py, tokens.css, fonts/, chart_premium.py   # shared design system
├── templates/
│   ├── update.html              # 5-page Jinja2 layout
│   └── editorial-archetypes.css # shared page-archetype system
├── scripts/
│   ├── extract_quarterly.py
│   └── build_charts.py
├── build_pdf.py
└── outputs/<quarter>/           # debug HTML + final PDF + chart PNGs
```
