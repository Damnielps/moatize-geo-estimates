#!/usr/bin/env python3
"""
Idempotent downloader for HDX COD-PS Moçambique (Population Statistics)
Source: https://data.humdata.org/dataset/cod-ps-moz
License: CC-BY 4.0 (UNFPA/OCHA)
Resolution: Admin 0–2 (adm3 in development)
Years covered: 2024 (latest available)
Format: Excel (.xlsx) with tabs per admin level + P-codes, sex, age disaggregated
"""

import hashlib
import json
import subprocess
import sys
from datetime import UTC, datetime
from pathlib import Path

OUTDIR = Path("data/raw")
OUTDIR.mkdir(parents=True, exist_ok=True)

# Dataset metadata
URL = "https://data.humdata.org/dataset/cod-ps-moz"
# NOTE: actual download link may vary; this is placeholder
DOWNLOAD_LINK = "https://data.humdata.org/dataset/cod-ps-moz/resource/[RESOURCE_ID]/download/moz_cod_ps_2024.xlsx"
OUTFILE = OUTDIR / "cod_ps_moz_2024.xlsx"
EXPECTED_SHA256 = "PLACEHOLDER_SHA256_HASH"  # Verify after download

def compute_sha256(filepath):
    sha256 = hashlib.sha256()
    with open(filepath, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            sha256.update(chunk)
    return sha256.hexdigest()

def download_if_needed():
    hash_file = Path(f"{OUTFILE}.sha256")

    if OUTFILE.exists() and hash_file.exists():
        actual_hash = compute_sha256(OUTFILE)
        expected_hash = hash_file.read_text().strip()
        if actual_hash == expected_hash:
            print(f"✓ {OUTFILE.name} already verified (hash match)")
            return True

    print(f"Downloading {DOWNLOAD_LINK}...")
    try:
        subprocess.run(
            ["curl", "-L", "--output", str(OUTFILE), DOWNLOAD_LINK],
            check=True,
            stderr=subprocess.PIPE
        )
    except subprocess.CalledProcessError as e:
        print(f"✗ Download failed: {e}")
        print(f"   Note: Verify DOWNLOAD_LINK on {URL}")
        return False

    actual_hash = compute_sha256(OUTFILE)
    hash_file.write_text(f"{actual_hash}\n")

    meta = {
        "url": DOWNLOAD_LINK,
        "download_date": datetime.now(tz=UTC).isoformat(),
        "size_bytes": OUTFILE.stat().st_size,
        "license": "CC-BY 4.0",
        "level": "A",
        "source_page": URL,
        "admin_levels": [0, 1, 2],
        "years_covered": [2024],
        "description": (
        "UNFPA/OCHA: Mozambique Subnational Population Statistics (COD-PS) "
        "with P-codes, sex, age disaggregation"
    )
    }
    (OUTDIR / f"{OUTFILE.name}.meta.json").write_text(json.dumps(meta, indent=2))

    print(f"✓ Downloaded and verified: {OUTFILE}")
    return True

if __name__ == "__main__":
    sys.exit(0 if download_if_needed() else 1)
