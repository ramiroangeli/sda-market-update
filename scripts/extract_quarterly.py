"""
extract_quarterly.py

Turns the raw NDIS Supplement P release for one quarter into clean CSVs,
mirroring the approach in ndis-python-v2/scripts/extract_sda_master.py
but scoped to just the tables this update needs (no need to reprocess
the full historical series each time).

Run from this directory's parent:
    python3 scripts/extract_quarterly.py --quarter 2026-Q2

Expects:
    data/<quarter>/raw/Supplement_P_<quarter>.xlsx

Writes:
    data/<quarter>/processed/*.csv
"""

import argparse
from pathlib import Path

import pandas as pd

HERE = Path(__file__).resolve().parent.parent


def extract(quarter: str) -> None:
    raw_dir = HERE / "data" / quarter / "raw"
    out_dir = HERE / "data" / quarter / "processed"
    out_dir.mkdir(parents=True, exist_ok=True)

    xlsx_files = list(raw_dir.glob("*.xlsx"))
    if not xlsx_files:
        raise FileNotFoundError(
            f"No .xlsx found in {raw_dir} — drop the new Supplement P release there first."
        )

    # TODO: adapt sheet/column parsing to match the new release's layout.
    # See ndis-python-v2/scripts/extract_sda_master.py for the reference
    # parsing logic (state rows, dwelling counts by SA4, design category mix).
    print(f"Found {len(xlsx_files)} raw file(s) in {raw_dir}:")
    for f in xlsx_files:
        print(f"  - {f.name}")
    print("Implement the sheet-specific parsing here, then write CSVs to", out_dir)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--quarter", required=True, help="e.g. 2026-Q2")
    args = parser.parse_args()
    extract(args.quarter)
