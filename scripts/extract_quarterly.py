"""
extract_quarterly.py

Extracts Q4-over-Q4 comparison data from the 4 Supplement P releases
(2022-23 -> 2025-26) into clean CSVs for the quarterly update's charts.

Excel-parsing logic (open_xl / parse_table / classify_row / SDA_COL_MAP)
mirrors ndis-python-v2/scripts/extract_sda_master.py — same source files,
same strict-OOXML workaround, same P.1/P.4 table layout.

Run from this directory's parent:
    python3 scripts/extract_quarterly.py

Reads:
    data/context/historical-q4/Supplement P ... 2022-23 Q4.xlsx
    data/context/historical-q4/Supplement P ... 2023-24 Q4.xlsx
    data/context/historical-q4/Supplement P ... 2024-25 Q4.xlsx
    data/2025-26-Q4/raw/Supplement P ... 2025-26 Q4.xlsx

Writes:
    data/2025-26-Q4/processed/q4_trend_national.csv
    data/2025-26-Q4/processed/q4_trend_by_state.csv
    data/2025-26-Q4/processed/q4_design_mix_current.csv
"""

import io
import logging
import zipfile
from pathlib import Path

import pandas as pd

logging.basicConfig(level=logging.INFO, format="%(levelname)s  %(message)s")
log = logging.getLogger(__name__)

HERE = Path(__file__).resolve().parent.parent
DATA = HERE / "data"

# Ordered oldest -> newest
SUPPLEMENT_P_FILES = [
    ("Q4 2022-23", DATA / "context/historical-q4/Supplement P Specialist Disability Accommodation 2022-23 Q4.xlsx"),
    ("Q4 2023-24", DATA / "context/historical-q4/Supplement P Specialist Disability Accommodation 2023-24 Q4.xlsx"),
    ("Q4 2024-25", DATA / "context/historical-q4/Supplement P Specialist Disability Accommodation 2024-25 Q4.xlsx"),
    ("Q4 2025-26", DATA / "2025-26-Q4/raw/Supplement P Specialist Disability Accommodation 2025-26 Q4.xlsx"),
]
CURRENT_PERIOD = "Q4 2025-26"
OUT_DIR = DATA / "2025-26-Q4" / "processed"

# Strict OOXML (purl.oclc.org) -> Transitional namespace replacements.
STRICT_NS = {
    "http://purl.oclc.org/ooxml/spreadsheetml/main":
        "http://schemas.openxmlformats.org/spreadsheetml/2006/main",
    "http://purl.oclc.org/ooxml/officeDocument/relationships":
        "http://schemas.openxmlformats.org/officeDocument/2006/relationships",
    "http://purl.oclc.org/ooxml/drawingml/2006/main":
        "http://schemas.openxmlformats.org/drawingml/2006/main",
    "http://purl.oclc.org/ooxml/drawingml/2006/spreadsheetDrawing":
        "http://schemas.openxmlformats.org/drawingml/2006/spreadsheetDrawing",
}

STATE_ABBREVS   = {"ACT", "NSW", "VIC", "QLD", "WA", "SA", "TAS", "NT", "OT"}
NATIONAL_LABELS = {"Total", "National", "Missing", "Other Territories"}

# P.1 SDA participant column names changed between Q4 2023-24 and Q4 2024-25
SDA_COL_MAP = {
    "Active participants with SDA supports": "participants_sda",  # pre-2024-25
    "Participants with SDA in use":          "participants_sda",  # 2024-25 onward
    "Participants SDA eligible, not yet using SDA": "participants_sda_eligible_not_using",
    "Active participants with SIL supports": "participants_sil",
    "Number of active participants":         "active_participants_total",
}


# ── Helpers (mirrors extract_sda_master.py) ──────────────────────────────────

def open_xl(path: Path) -> pd.ExcelFile:
    """Open an XLSX, transparently rewriting Strict OOXML -> Transitional in memory."""
    buf = io.BytesIO()
    with zipfile.ZipFile(path, "r") as zin, \
         zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zout:
        for item in zin.infolist():
            data = zin.read(item.filename)
            if item.filename.endswith((".xml", ".rels")):
                try:
                    text = data.decode("utf-8")
                    for old, new in STRICT_NS.items():
                        text = text.replace(old, new)
                    text = text.replace(' conformance="strict"', "")
                    data = text.encode("utf-8")
                except UnicodeDecodeError:
                    pass
            zout.writestr(item, data)
    buf.seek(0)
    return pd.ExcelFile(buf, engine="openpyxl")


def classify_row(val: str) -> str:
    val = str(val).strip()
    if val in STATE_ABBREVS:
        return "State"
    if val in NATIONAL_LABELS:
        return "National"
    if " - " in val:
        return "SA4"
    return "Other"


def is_footnote(row: pd.Series) -> bool:
    return len(str(row.iloc[0])) > 80 and row.iloc[1:].isna().all()


def parse_table(xl: pd.ExcelFile, sheet: str, add_row_type: bool = False) -> pd.DataFrame | None:
    if sheet not in xl.sheet_names:
        log.warning("  Sheet '%s' not found — skipping", sheet)
        return None

    raw = xl.parse(sheet, header=None)
    df = raw.copy()
    df.columns = df.iloc[1]
    df = df.iloc[2:].reset_index(drop=True)
    df.columns.name = None

    region_col = df.columns[0]
    df = df[df[region_col] != "Back to Table of Contents"]
    df = df[~df.apply(is_footnote, axis=1)]
    df = df[df[region_col].notna()].reset_index(drop=True)

    if add_row_type:
        df.insert(1, "row_type", df[region_col].apply(classify_row))

    return df


# ── Extraction ────────────────────────────────────────────────────────────────

def extract_dwelling_rows(xl: pd.ExcelFile, period: str) -> list[dict]:
    df = parse_table(xl, "Table P.4", add_row_type=True)
    if df is None:
        return []
    rows = []
    for _, row in df.iterrows():
        if row.get("row_type") not in ("State", "National"):
            continue
        rows.append({
            "period":              period,
            "state":               str(row.iloc[0]).strip(),
            "row_type":            row["row_type"],
            "dwellings_existing":  row.get("Existing"),
            "dwellings_legacy":    row.get("Legacy"),
            "dwellings_new_build": row.get("New Build"),
            "dwellings_new_build_refurb": row.get("New Build (refurbished)"),
            "dwellings_total":     row.get("Total"),
        })
    return rows


def extract_participant_rows(xl: pd.ExcelFile, period: str) -> list[dict]:
    df = parse_table(xl, "Table P.1", add_row_type=True)
    if df is None:
        return []
    df = df.rename(columns={c: SDA_COL_MAP[c] for c in df.columns if c in SDA_COL_MAP})
    rows = []
    for _, row in df.iterrows():
        if row.get("row_type") not in ("State", "National"):
            continue
        rows.append({
            "period":                              period,
            "state":                               str(row.iloc[0]).strip(),
            "participants_sda":                    row.get("participants_sda"),
            "participants_sda_eligible_not_using":  row.get("participants_sda_eligible_not_using"),
            "participants_sil":                     row.get("participants_sil"),
        })
    return rows


def _national_state_label(row: pd.Series) -> str | None:
    """National-classified rows can be labelled 'Total', 'National', 'Missing' or
    'Other Territories' depending on the table. Only 'Total'/'National' is the true
    country-wide aggregate — normalize it to 'Total' so it joins against the other
    tables' national row. Returns None for the 'Missing'/'Other Territories' rows,
    which callers should skip."""
    label = str(row.iloc[0]).strip()
    if row.get("row_type") == "State":
        return label
    if label in ("Total", "National"):
        return "Total"
    return None


def extract_funding_rows(xl: pd.ExcelFile, period: str) -> list[dict]:
    df = parse_table(xl, "Table P.2", add_row_type=True)
    if df is None:
        return []
    rows = []
    for _, row in df.iterrows():
        state = _national_state_label(row)
        if state is None:
            continue
        rows.append({
            "period":                   period,
            "state":                    state,
            "funding_sda_committed":    row.get("Annualised supports committed to SDA in current plans"),
            "funding_total_committed":  row.get("Total committed in supports in current plans"),
        })
    return rows


def extract_provider_rows(xl: pd.ExcelFile, period: str) -> list[dict]:
    """Table P.3 — the provider-count column name embeds the quarter/year, so
    it's addressed positionally (region, row_type, providers) rather than by name."""
    df = parse_table(xl, "Table P.3", add_row_type=True)
    if df is None:
        return []
    providers_col = df.columns[2]
    rows = []
    for _, row in df.iterrows():
        state = _national_state_label(row)
        if state is None:
            continue
        rows.append({
            "period":           period,
            "state":            state,
            "providers_active": row.get(providers_col),
        })
    return rows


def extract_design_mix(xl: pd.ExcelFile) -> pd.DataFrame | None:
    """Table P.5 — dwellings by design category, full SA4 breakdown, current quarter only."""
    return parse_table(xl, "Table P.5", add_row_type=True)


def extract_design_mix_national(xl: pd.ExcelFile, period: str) -> dict | None:
    """Table P.5 — National row only, collected across all periods for a Basic/Legacy trend."""
    df = parse_table(xl, "Table P.5", add_row_type=True)
    if df is None:
        return None
    national_rows = df[df["row_type"] == "National"]
    if national_rows.empty:
        return None
    row = national_rows.iloc[0]
    return {
        "period":                period,
        "design_basic":          row.get("Basic"),
        "design_improved_liveability": row.get("Improved Liveability"),
        "design_high_physical_support": row.get("High Physical Support"),
        "design_robust":         row.get("Robust"),
        "design_fully_accessible": row.get("Fully Accessible"),
        "design_multi_category": row.get("Multi-Design Category"),
        "design_total":          row.get("Total"),
    }


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    all_dwellings, all_participants, all_funding, all_providers = [], [], [], []
    design_mix_current = None
    design_mix_trend = []

    for period, path in SUPPLEMENT_P_FILES:
        if not path.exists():
            log.warning("  NOT FOUND — skipping %s: %s", period, path)
            continue
        log.info("  %s  <- %s", period, path.name)
        xl = open_xl(path)
        all_dwellings.extend(extract_dwelling_rows(xl, period))
        all_participants.extend(extract_participant_rows(xl, period))
        all_funding.extend(extract_funding_rows(xl, period))
        all_providers.extend(extract_provider_rows(xl, period))
        design_mix_row = extract_design_mix_national(xl, period)
        if design_mix_row is not None:
            design_mix_trend.append(design_mix_row)
        if period == CURRENT_PERIOD:
            design_mix_current = extract_design_mix(xl)

    df_dwell = pd.DataFrame(all_dwellings)
    df_part  = pd.DataFrame(all_participants).drop(columns=["row_type"], errors="ignore")
    df_fund  = pd.DataFrame(all_funding).drop(columns=["row_type"], errors="ignore")
    df_prov  = pd.DataFrame(all_providers).drop(columns=["row_type"], errors="ignore")

    # NDIA source occasionally publishes a near-duplicate row for the same state
    # (e.g. ACT in Q4 2025-26 P.1, values differ only in the 5th decimal) — keep
    # the first and drop the rest rather than double-counting via the join.
    for label, df in (("dwellings", df_dwell), ("participants", df_part),
                       ("funding", df_fund), ("providers", df_prov)):
        dupes = df.duplicated(subset=["period", "state"], keep="first").sum()
        if dupes:
            log.warning("  %d duplicate (period, state) row(s) in %s — keeping first", dupes, label)
    df_dwell = df_dwell.drop_duplicates(subset=["period", "state"], keep="first")
    df_part  = df_part.drop_duplicates(subset=["period", "state"], keep="first")
    df_fund  = df_fund.drop_duplicates(subset=["period", "state"], keep="first")
    df_prov  = df_prov.drop_duplicates(subset=["period", "state"], keep="first")

    merged = pd.merge(df_dwell, df_part, on=["period", "state"], how="left")
    merged = pd.merge(merged, df_fund, on=["period", "state"], how="left")
    merged = pd.merge(merged, df_prov, on=["period", "state"], how="left")

    period_order = {p: i for i, (p, _) in enumerate(SUPPLEMENT_P_FILES)}
    rtype_order  = {"National": 0, "State": 1}
    merged["_p"] = merged["period"].map(period_order)
    merged["_r"] = merged["row_type"].map(rtype_order)
    merged = merged.sort_values(["_p", "_r", "state"]).drop(columns=["_p", "_r"])

    national = merged[merged["row_type"] == "National"].drop(columns=["row_type"])
    by_state = merged[merged["row_type"] == "State"].drop(columns=["row_type"])

    national_path = OUT_DIR / "q4_trend_national.csv"
    state_path    = OUT_DIR / "q4_trend_by_state.csv"
    national.to_csv(national_path, index=False)
    by_state.to_csv(state_path, index=False)
    log.info("Wrote %s (%d rows)", national_path, len(national))
    log.info("Wrote %s (%d rows)", state_path, len(by_state))

    if design_mix_current is not None:
        design_path = OUT_DIR / "q4_design_mix_current.csv"
        design_mix_current.to_csv(design_path, index=False)
        log.info("Wrote %s (%d rows)", design_path, len(design_mix_current))
    else:
        log.warning("Table P.5 not found in %s — no design-mix CSV written", CURRENT_PERIOD)

    if design_mix_trend:
        trend_df = pd.DataFrame(design_mix_trend)
        trend_df["_p"] = trend_df["period"].map(period_order)
        trend_df = trend_df.sort_values("_p").drop(columns=["_p"])
        trend_path = OUT_DIR / "q4_design_mix_trend_national.csv"
        trend_df.to_csv(trend_path, index=False)
        log.info("Wrote %s (%d rows)", trend_path, len(trend_df))


if __name__ == "__main__":
    main()
