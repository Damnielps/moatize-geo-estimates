#!/usr/bin/env python3
"""
Fetch World Bank CMO Historical Data Annual (coal prices 2000–2025).

Idempotent: verifies SHA256 before downloading. Fails explicitly if source changes.
Generates:
  - data/raw/CMO-Historical-Data-Annual.xlsx + .sha256 + .meta.json
  - data/processed/economia/preco_carvao_anual.csv
"""

import hashlib
import json
import logging
import sys
from datetime import UTC, datetime
from pathlib import Path

import pandas as pd
import requests

logger = logging.getLogger(__name__)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
)

# Paths
DATA_RAW = Path(__file__).parent.parent.parent / "data" / "raw"
DATA_PROCESSED = Path(__file__).parent.parent.parent / "data" / "processed" / "economia"
PIPELINE_DIR = Path(__file__).parent.parent.parent / "pipeline" / "00_fetch"

# Configuration
URL = "https://thedocs.worldbank.org/en/doc/74e8be41ceb20fa0da750cda2f6b9e4e-0050012026/related/CMO-Historical-Data-Annual.xlsx"
FILENAME = "CMO-Historical-Data-Annual.xlsx"
SOURCE_PAGE = "https://www.worldbank.org/en/research/commodity-markets"
LICENSE_URL = "https://www.worldbank.org/ext/en/legal/terms-conditions/datasets"
LICENSE_TEXT = (
    "Creative Commons Attribution 4.0 International (CC BY 4.0). "
    "See https://www.worldbank.org/ext/en/legal/terms-conditions/datasets"
)

# Sheet and column configuration
SHEET_NAME = "Annual Prices (Nominal)"
# Column indices in Excel (0-indexed): Year is 0, Coal Australian is 5, Coal South African is 6
COAL_COLUMNS = {
    5: "preco_carvao_australia",
    6: "preco_carvao_africa_do_sul",
}


def compute_sha256(filepath):
    """Compute SHA256 hash of a file."""
    sha256 = hashlib.sha256()
    with open(filepath, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            sha256.update(chunk)
    return sha256.hexdigest()


def download_file(url, output_path):
    """Download file with retries and size verification."""
    logger.info(f"Downloading {url}")
    try:
        response = requests.get(url, timeout=30)
        response.raise_for_status()
    except requests.RequestException as e:
        logger.error(f"Download failed: {e}")
        raise

    with open(output_path, "wb") as f:
        f.write(response.content)

    size = output_path.stat().st_size
    logger.info(f"Downloaded {size:,} bytes to {output_path}")
    return size


def fetch_cmo_annual():
    """Main: download and process World Bank CMO Annual."""
    DATA_RAW.mkdir(parents=True, exist_ok=True)
    DATA_PROCESSED.mkdir(parents=True, exist_ok=True)

    filepath = DATA_RAW / FILENAME
    sha_filepath = DATA_RAW / f"{FILENAME}.sha256"
    meta_filepath = DATA_RAW / f"{FILENAME}.meta.json"

    # Check if file exists and hash matches
    if filepath.exists() and sha_filepath.exists():
        try:
            with open(sha_filepath) as f:
                stored_hash = f.read().strip().split()[0]
            current_hash = compute_sha256(filepath)
            if current_hash == stored_hash:
                logger.info(f"File {FILENAME} already cached; hash matches.")
                return filepath, meta_filepath
            else:
                logger.error(
                    f"Hash mismatch for {FILENAME}: stored={stored_hash}, current={current_hash}. "
                    "Source may have changed. Failing explicitly."
                )
                raise RuntimeError("Source hash changed; refusing to proceed.")
        except Exception as e:
            logger.error(f"Error verifying cached file: {e}")
            raise

    # Download
    size_bytes = download_file(URL, filepath)
    file_hash = compute_sha256(filepath)

    # Write SHA256
    with open(sha_filepath, "w") as f:
        f.write(f"{file_hash}  {FILENAME}\n")
    logger.info(f"SHA256 written to {sha_filepath}")

    # Write metadata
    meta = {
        "url": URL,
        "download_date": datetime.now(UTC).strftime("%Y-%m-%d"),
        "size_bytes": size_bytes,
        "license": LICENSE_TEXT,
        "license_url": LICENSE_URL,
        "level": "A",
        "source_page": SOURCE_PAGE,
        "content_description": (
            "World Bank Commodity Markets Observatory — CMO Historical Data Annual. "
            "Coal prices (Australia and South Africa) in USD/mt, annual data."
        ),
        "years_covered": "2000–2025",
        "geographic_level": "global (commodity prices)",
        "format": "XLSX",
        "sheet_used": SHEET_NAME,
        "notes": "Direct download from World Bank public repository; no authentication required.",
    }

    with open(meta_filepath, "w") as f:
        json.dump(meta, f, indent=2, ensure_ascii=False)
    logger.info(f"Metadata written to {meta_filepath}")

    return filepath, meta_filepath


def extract_coal_prices(filepath):
    """Read Excel and extract coal price series from correct sheet."""
    logger.info(f"Reading {filepath} (sheet: {SHEET_NAME})")
    try:
        # Skip the first 8 rows (title, description, etc.); headers are at row 6 (0-indexed)
        df = pd.read_excel(
            filepath, sheet_name=SHEET_NAME, header=None, skiprows=8
        )
    except Exception as e:
        logger.error(f"Error reading Excel: {e}")
        raise

    logger.info(f"Data shape: {df.shape} rows x {df.shape[1]} columns")

    # Extract Year (col 0) and coal columns (5, 6)
    try:
        coal_data = df[[0, 5, 6]].copy()
        coal_data.columns = ["ano", "coal_au_raw", "coal_sa_raw"]
    except (KeyError, IndexError) as e:
        logger.error(f"Error extracting coal columns: {e}")
        raise

    # Clean and convert
    coal_data["ano"] = pd.to_numeric(coal_data["ano"], errors="coerce")
    coal_data["coal_au_raw"] = pd.to_numeric(coal_data["coal_au_raw"], errors="coerce")
    coal_data["coal_sa_raw"] = pd.to_numeric(coal_data["coal_sa_raw"], errors="coerce")

    coal_data = coal_data.dropna()
    coal_data["ano"] = coal_data["ano"].astype(int)

    # Filter to 2000–2025
    coal_data = coal_data[(coal_data["ano"] >= 2000) & (coal_data["ano"] <= 2025)].copy()
    coal_data = coal_data.sort_values("ano").reset_index(drop=True)

    logger.info(f"Extracted {len(coal_data)} annual price records (2000–2025)")

    # Reshape to long format
    rows = []
    for _, row in coal_data.iterrows():
        rows.append({
            "ano": int(row["ano"]),
            "variavel": "preco_carvao_australia",
            "valor": row["coal_au_raw"],
        })
        rows.append({
            "ano": int(row["ano"]),
            "variavel": "preco_carvao_africa_do_sul",
            "valor": row["coal_sa_raw"],
        })

    result = pd.DataFrame(rows)
    return result


def generate_output_csv(coal_data, meta_filepath):
    """Generate final CSV in required format."""
    output_csv = DATA_PROCESSED / "preco_carvao_anual.csv"

    # Read metadata for citation
    with open(meta_filepath) as f:
        meta = json.load(f)

    # Build output rows
    rows = []
    for _, row in coal_data.iterrows():
        rows.append(
            {
                "unidade_geografica": "Mercado mundial",
                "ano": row["ano"],
                "variavel": row["variavel"],
                "valor": row["valor"],
                "unidade_medida": "USD/t (nominal)",
                "selo": "observado",
                "nivel_fonte": "A",
                "fonte": (
                    "World Bank. Commodity Markets Observatory — "
                    f"CMO Historical Data Annual. {meta['download_date']}. File: {FILENAME}"
                ),
                "metodo": "média anual publicada pelo World Bank (CMO), sem transformação",
                "nota": "",
            }
        )

    output_df = pd.DataFrame(rows)
    output_df = output_df.sort_values(["variavel", "ano"]).reset_index(drop=True)

    output_csv.parent.mkdir(parents=True, exist_ok=True)
    output_df.to_csv(output_csv, index=False, encoding="utf-8")
    logger.info(f"CSV written to {output_csv}")

    return output_csv


def main():
    """Entry point."""
    try:
        logger.info("=" * 60)
        logger.info("World Bank CMO Annual — Fetch and Process")
        logger.info("=" * 60)

        # Fetch
        filepath, meta_filepath = fetch_cmo_annual()

        # Extract
        coal_data = extract_coal_prices(filepath)

        # Generate CSV
        output_csv = generate_output_csv(coal_data, meta_filepath)

        logger.info("=" * 60)
        logger.info("Success.")
        logger.info(f"Output CSV: {output_csv}")
        logger.info(f"Records: {len(coal_data)}")
        logger.info("=" * 60)

        return 0

    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)
        return 1


if __name__ == "__main__":
    sys.exit(main())
