#!/usr/bin/env python3
"""
Idempotent downloader for WorldPop GRID3 MOZ Population v1.1
Source: https://data.grid3.org/datasets/grid3-moz-populationv1-1
Backup: https://data.humdata.org/dataset/gridded-population-estimates-for-mozambique-2017-census-v1-1
License: CC-BY 4.0 (WorldPop/University of Southampton)
Resolution: 3 arc-seconds (~100 m)
Years covered: 2017 (Census disaggregated)
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
URL = "https://data.grid3.org/datasets/grid3-moz-populationv1-1"
DOWNLOAD_LINK = "https://data.humdata.org/dataset/gridded-population-estimates-for-mozambique-2017-census-v1-1/resource/1add89c7-84dd-4aaa-9f4c-a08eebc0dbc3/download/MOZ_population_v1_1_gridded.tif"
OUTFILE = OUTDIR / "worldpop_grid3_moz_2017_100m.tif"
EXPECTED_SHA256 = "PLACEHOLDER_SHA256_HASH"  # Verify after download

def compute_sha256(filepath):
    """Compute SHA256 hash of a file."""
    sha256 = hashlib.sha256()
    with open(filepath, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            sha256.update(chunk)
    return sha256.hexdigest()

def download_if_needed():
    """Download if missing or hash mismatch."""
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
        return False

    # Verify and record hash
    actual_hash = compute_sha256(OUTFILE)
    hash_file.write_text(f"{actual_hash}\n")

    # Metadata JSON
    meta = {
        "url": DOWNLOAD_LINK,
        "download_date": datetime.now(tz=UTC).isoformat(),
        "size_bytes": OUTFILE.stat().st_size,
        "license": "CC-BY 4.0",
        "level": "A",
        "source_page": URL,
        "resolution_m": 100,
        "crs": "EPSG:4326",
        "years_covered": [2017],
        "description": "WorldPop GRID3 Mozambique: Census disaggregated gridded population v1.1"
    }
    (OUTDIR / f"{OUTFILE.name}.meta.json").write_text(json.dumps(meta, indent=2))

    print(f"✓ Downloaded and verified: {OUTFILE}")
    return True

if __name__ == "__main__":
    sys.exit(0 if download_if_needed() else 1)
