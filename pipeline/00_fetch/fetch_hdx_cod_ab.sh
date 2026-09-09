#!/bin/bash
# Idempotent downloader for HDX COD-AB Mozambique (administrative boundaries, P-codes)
# Source: https://data.humdata.org/dataset/cod-ab-moz
# Producer declarado (via CKAN API dataset_source): INE - Instituto Nacional de Estatistica
# Licença: Creative Commons Attribution for Intergovernmental Organisations (CC BY-IGO 3.0)
#   http://creativecommons.org/licenses/by/3.0/igo/legalcode (lida via CKAN API license_url)
# Verificado (fetch real, nao apenas HEAD) em 2026-09-08 pela Fase 3 (T2).
#
# Resource ID e URL obtidos via CKAN API, NUNCA hardcoded sem verificacao:
#   curl -s "https://data.humdata.org/api/3/action/package_show?id=cod-ab-moz"
# O resource escolhido é o GeoJSON (moz_admin_boundaries.geojson.zip), que traz
# ADM0-ADM4 + pontos de capitais administrativas num unico pacote.

set -euo pipefail

OUTDIR="data/raw"
mkdir -p "$OUTDIR"

RESOURCE_URL="https://data.humdata.org/dataset/5e8d83a5-1210-49be-b7d9-cf286dbc15df/resource/f1d97232-4cb5-4083-b3cc-d192aa9bdcfe/download/moz_admin_boundaries.geojson.zip"
OUTFILE="${OUTDIR}/moz_admin_boundaries.geojson.zip"

if [[ -f "${OUTFILE}.sha256" ]]; then
    ACTUAL_SHA256=$(shasum -a 256 "${OUTFILE}" | awk '{print $1}')
    REGISTRADO=$(awk '{print $1}' "${OUTFILE}.sha256")
    if [[ "$ACTUAL_SHA256" == "$REGISTRADO" ]]; then
        echo "OK: ${OUTFILE} ja presente e integro (sha256 confere)."
        exit 0
    else
        echo "ERRO: hash de ${OUTFILE} nao confere com ${OUTFILE}.sha256 -- fonte pode ter mudado." >&2
        exit 1
    fi
fi

echo "Baixando ${RESOURCE_URL}..."
HTTP_CODE=$(curl -sL -o "${OUTFILE}" -w "%{http_code}" "${RESOURCE_URL}")
if [[ "$HTTP_CODE" != "200" ]]; then
    echo "ERRO: HTTP ${HTTP_CODE} para ${RESOURCE_URL}" >&2
    rm -f "${OUTFILE}"
    exit 1
fi

shasum -a 256 "${OUTFILE}" | awk '{print $1"  "FILENAME}' FILENAME="$(basename "$OUTFILE")" > "${OUTFILE}.sha256"

SIZE=$(stat -f%z "${OUTFILE}" 2>/dev/null || stat -c%s "${OUTFILE}")
DL_DATE=$(date -u +%Y-%m-%dT%H:%M:%SZ)
cat > "${OUTFILE}.meta.json" << METADATA
{
  "url": "${RESOURCE_URL}",
  "download_date": "${DL_DATE}",
  "size_bytes": ${SIZE},
  "license": "Creative Commons Attribution for Intergovernmental Organisations (CC BY-IGO)",
  "license_url": "http://creativecommons.org/licenses/by/3.0/igo/legalcode",
  "level": "nao classificado - cabe ao auditor-dados",
  "source_page": "https://data.humdata.org/dataset/cod-ab-moz",
  "dataset_source_declarado": "INE - Instituto Nacional de Estatistica (declarado pelo HDX/CKAN API, nao verificado no site do INE)",
  "citation": "OCHA/HDX COD-AB Mozambique (moz_admin_boundaries), fonte declarada INE",
  "resolucao": "poligonos administrativos ADM0-ADM4 + pontos de capitais",
  "selo": "observado"
}
METADATA

echo "OK: baixado e verificado: ${OUTFILE} (${SIZE} bytes)"
