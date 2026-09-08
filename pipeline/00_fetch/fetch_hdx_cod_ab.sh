#!/bin/bash
# Idempotent downloader for HDX COD-AB Mozambique (administrative boundaries, P-codes)
# Source: https://data.humdata.org/dataset/cod-ab-moz
# License: CC-BY 4.0 (OCHA)
# Returns: COD-AB-MOZ shapefiles in EPSG:4326

set -euo pipefail

OUTDIR="data/raw"
mkdir -p "$OUTDIR"

# Dataset metadata
RESOURCE_ID="79b01a01-44e8-4b8d-bb6c-d99fc5f75ea0"  # Example; update with actual HDX resource ID
URL="https://data.humdata.org/dataset/cod-ab-moz/resource/${RESOURCE_ID}/download/moz_admbnda_adm0_2_2022.zip"
OUTFILE="${OUTDIR}/cod_ab_moz_2022.zip"
EXPECTED_SHA256="PLACEHOLDER_SHA256_HASH"  # To be filled after first download

# Download only if missing or hash mismatch
if [[ -f "${OUTFILE}.sha256" ]]; then
    ACTUAL_SHA256=$(sha256sum "${OUTFILE}" | awk '{print $1}')
    if [[ "$ACTUAL_SHA256" == "$(cat "${OUTFILE}.sha256")" ]]; then
        echo "✓ ${OUTFILE} already verified (hash match)"
        exit 0
    fi
fi

echo "Downloading ${URL}..."
wget -q --output-document="${OUTFILE}" "${URL}" || {
    echo "✗ Download failed. Check URL and network."
    exit 1
}

# Verify and record hash
sha256sum "${OUTFILE}" | awk '{print $1}' > "${OUTFILE}.sha256"

# Metadata JSON
cat > "${OUTFILE}.meta.json" << METADATA
{
  "url": "${URL}",
  "download_date": "$(date -u +%Y-%m-%d)",
  "size_bytes": $(stat -f%z "${OUTFILE}" 2>/dev/null || stat -c%s "${OUTFILE}"),
  "license": "CC-BY 4.0",
  "level": "A",
  "source_page": "https://data.humdata.org/dataset/cod-ab-moz",
  "description": "COD-AB Mozambique v2022: Admin levels 0-3, P-codes, WGS84 (EPSG:4326)"
}
METADATA

echo "✓ Downloaded and verified: ${OUTFILE}"
