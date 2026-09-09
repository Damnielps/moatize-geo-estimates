#!/bin/bash
#
# fetch_osm_reassentamentos.sh
#
# Georreferencia os povoados de reassentamento do complexo carbonífero de Moatize
# consultando ao vivo a API Nominatim do OSM (busca por nome) e, quando o Nominatim
# não retorna resultado, a Overpass API (busca por elemento nomeado dentro da AOI).
#
# Regra inviolável: NENHUMA coordenada é gravada sem vir diretamente da resposta
# JSON de uma dessas APIs nesta execução. Se nenhuma API retornar elemento, a feição
# é gravada com geometry: null e confianca: "baixa" (ou omitida, ver NOTA_25_SETEMBRO).
#
# Uso: bash fetch_osm_reassentamentos.sh [--force]
#
# Idempotência: se data/raw/reassentamentos.geojson já existe com o hash esperado
# (gravado em reassentamentos.geojson.sha256 na execução anterior deste mesmo script),
# a execução é pulada. Use --force para reconsultar as APIs e regravar.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJ_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
OUTPUT_DIR="$PROJ_ROOT/data/raw"
OUTPUT_FILE="$OUTPUT_DIR/reassentamentos.geojson"
SHA_FILE="$OUTPUT_FILE.sha256"
META_FILE="$OUTPUT_FILE.meta.json"
FORCE="${1:-}"

UA="tete-moatize-research/1.0 (+https://github.com/Damnielps/moatize-geo-estimates; uso academico nao comercial)"
NOMINATIM="https://nominatim.openstreetmap.org/search"
OVERPASS="https://overpass.kumi.systems/api/interpreter"

log() { echo "[$(date '+%Y-%m-%d %H:%M:%S')] $*" >&2; }
die() { log "ERRO: $*"; exit 1; }

mkdir -p "$OUTPUT_DIR"

if [[ -f "$OUTPUT_FILE" && -f "$SHA_FILE" && "$FORCE" != "--force" ]]; then
    ACTUAL_SHA=$(shasum -a 256 "$OUTPUT_FILE" | awk '{print $1}')
    EXPECTED_SHA=$(awk '{print $1}' "$SHA_FILE")
    if [[ "$ACTUAL_SHA" == "$EXPECTED_SHA" ]]; then
        log "OK: arquivo já existe com hash íntegro ($EXPECTED_SHA). Pulando. Use --force para reconsultar."
        exit 0
    else
        die "Arquivo existe mas hash divergiu do registrado em $SHA_FILE. Esperado: $EXPECTED_SHA. Atual: $ACTUAL_SHA."
    fi
fi

command -v jq >/dev/null || die "jq é necessário e não foi encontrado no PATH."
command -v curl >/dev/null || die "curl é necessário e não foi encontrado no PATH."

nominatim_query() {
    local q="$1"
    curl -sG --max-time 20 -A "$UA" \
        --data-urlencode "q=$q" \
        --data-urlencode "format=jsonv2" \
        --data-urlencode "addressdetails=1" \
        "$NOMINATIM"
    sleep 1.1   # respeita o limite de 1 req/s do Nominatim público
}

log "Consultando Nominatim: Cateme, Mozambique"
CATEME_JSON=$(nominatim_query "Cateme, Mozambique")
CATEME_COUNT=$(echo "$CATEME_JSON" | jq 'length')
[[ "$CATEME_COUNT" -ge 1 ]] || die "Nominatim não retornou resultado para Cateme. Não é seguro prosseguir sem coordenada verificada."
CATEME_LAT=$(echo "$CATEME_JSON" | jq -r '.[0].lat')
CATEME_LON=$(echo "$CATEME_JSON" | jq -r '.[0].lon')
CATEME_OSMTYPE=$(echo "$CATEME_JSON" | jq -r '.[0].osm_type')
CATEME_OSMID=$(echo "$CATEME_JSON" | jq -r '.[0].osm_id')
CATEME_DISPLAY=$(echo "$CATEME_JSON" | jq -r '.[0].display_name')
log "Cateme -> lat=$CATEME_LAT lon=$CATEME_LON osm_type=$CATEME_OSMTYPE osm_id=$CATEME_OSMID"

log "Consultando Nominatim: Mwaladzi, Mozambique"
MWALADZI_JSON=$(nominatim_query "Mwaladzi, Mozambique")
MWALADZI_COUNT=$(echo "$MWALADZI_JSON" | jq 'length')
[[ "$MWALADZI_COUNT" -ge 1 ]] || die "Nominatim não retornou resultado para Mwaladzi."
MWALADZI_LAT=$(echo "$MWALADZI_JSON" | jq -r '.[0].lat')
MWALADZI_LON=$(echo "$MWALADZI_JSON" | jq -r '.[0].lon')
MWALADZI_OSMTYPE=$(echo "$MWALADZI_JSON" | jq -r '.[0].osm_type')
MWALADZI_OSMID=$(echo "$MWALADZI_JSON" | jq -r '.[0].osm_id')
MWALADZI_DISPLAY=$(echo "$MWALADZI_JSON" | jq -r '.[0].display_name')
log "Mwaladzi -> lat=$MWALADZI_LAT lon=$MWALADZI_LON osm_type=$MWALADZI_OSMTYPE osm_id=$MWALADZI_OSMID"

log "Consultando Nominatim: 25 de Setembro, Moatize, Mozambique"
SET25_JSON=$(nominatim_query "25 de Setembro, Moatize, Mozambique")
SET25_COUNT=$(echo "$SET25_JSON" | jq 'length')
SET25_LAT=""; SET25_LON=""; SET25_OSMTYPE=""; SET25_OSMID=""
if [[ "$SET25_COUNT" -ge 1 ]]; then
    SET25_LAT=$(echo "$SET25_JSON" | jq -r '.[0].lat')
    SET25_LON=$(echo "$SET25_JSON" | jq -r '.[0].lon')
    SET25_OSMTYPE=$(echo "$SET25_JSON" | jq -r '.[0].osm_type')
    SET25_OSMID=$(echo "$SET25_JSON" | jq -r '.[0].osm_id')
    log "25 de Setembro (Nominatim) -> lat=$SET25_LAT lon=$SET25_LON"
else
    log "Nominatim sem resultado para 25 de Setembro. Tentando Overpass (bbox da AOI provisória)."
    OVERPASS_QUERY='[out:json][timeout:40];(node["name"~"25 de Setembro",i](-16.35,33.50,-16.00,34.10);way["name"~"25 de Setembro",i](-16.35,33.50,-16.00,34.10);relation["name"~"25 de Setembro",i](-16.35,33.50,-16.00,34.10););out center tags;'
    OVERPASS_JSON=$(curl -s --max-time 45 -A "$UA" --data-urlencode "data=$OVERPASS_QUERY" "$OVERPASS" || echo '{"elements":[]}')
    OVERPASS_N=$(echo "$OVERPASS_JSON" | jq '.elements | length' 2>/dev/null || echo 0)
    if [[ "$OVERPASS_N" -ge 1 ]]; then
        SET25_LAT=$(echo "$OVERPASS_JSON" | jq -r '.elements[0].center.lat // .elements[0].lat')
        SET25_LON=$(echo "$OVERPASS_JSON" | jq -r '.elements[0].center.lon // .elements[0].lon')
        SET25_OSMTYPE=$(echo "$OVERPASS_JSON" | jq -r '.elements[0].type')
        SET25_OSMID=$(echo "$OVERPASS_JSON" | jq -r '.elements[0].id')
        log "25 de Setembro (Overpass) -> lat=$SET25_LAT lon=$SET25_LON"
    else
        log "Overpass também não retornou elemento para 25 de Setembro (bairro de Moatize)."
        log "NOTA_25_SETEMBRO: nenhuma API geocodificou 25 de Setembro. Gravando feição com geometry: null."
    fi
fi

DOWNLOAD_DATE=$(date -u '+%Y-%m-%d')

# Monta a feição de 25 de Setembro condicionalmente (com ou sem geometria)
if [[ -n "$SET25_LAT" ]]; then
    SET25_GEOM="{\"type\":\"Point\",\"coordinates\":[$SET25_LON,$SET25_LAT]}"
    SET25_FONTE="OSM (Overpass, elemento nomeado dentro da AOI)"
    SET25_URL="https://www.openstreetmap.org/$SET25_OSMTYPE/$SET25_OSMID"
    SET25_OSMID_FIELD="\"$SET25_OSMTYPE/$SET25_OSMID\""
    SET25_CONF="media"
    SET25_NOTAS="Coordenada resolvida via Overpass API em $DOWNLOAD_DATE, elemento OSM $SET25_OSMTYPE/$SET25_OSMID. Bairro urbano de reassentamento da Vale em Moatize (HRW 2013)."
else
    SET25_GEOM="null"
    SET25_FONTE="nao_localizado"
    SET25_URL="nao_disponivel"
    SET25_OSMID_FIELD="null"
    SET25_CONF="baixa"
    SET25_NOTAS="Nominatim ('25 de Setembro, Moatize, Mozambique') e Overpass (busca por name~'25 de Setembro' na bbox -16.35,33.50,-16.00,34.10) não retornaram nenhum elemento em $DOWNLOAD_DATE. Bairro urbano de Moatize onde a Vale reassentou 289 famílias segundo HRW 2013 (ver data/provenance_parts/reassentamento.md), mas sem geometria OSM localizável. Coordenada NÃO inventada — geometry null intencional."
fi

cat > "$OUTPUT_FILE" <<EOF
{
  "type": "FeatureCollection",
  "features": [
    {
      "type": "Feature",
      "properties": {
        "nome": "Cateme",
        "tipo": "rural",
        "fonte_coordenada": "OSM (Nominatim)",
        "url_fonte": "https://www.openstreetmap.org/$CATEME_OSMTYPE/$CATEME_OSMID",
        "osm_id": "$CATEME_OSMTYPE/$CATEME_OSMID",
        "n_familias": 716,
        "ano_reassentamento": 2009,
        "operador": "Vale Moçambique",
        "confianca": "alta",
        "notas": "Coordenada resolvida via Nominatim em $DOWNLOAD_DATE: $CATEME_DISPLAY. n_familias=716 conforme texto do corpo do relatório HRW 2013 'What is a House without Food?' ('Vale resettled 716 families into Cateme'); o sumário executivo do mesmo relatório dá o total combinado Cateme+25 de Setembro como 1.365, que diverge da soma 716+289=1.005 -- divergência registrada, não reconciliada (ver data/provenance_parts/reassentamento.md)."
      },
      "geometry": {
        "type": "Point",
        "coordinates": [$CATEME_LON, $CATEME_LAT]
      }
    },
    {
      "type": "Feature",
      "properties": {
        "nome": "25 de Setembro",
        "tipo": "urbano",
        "fonte_coordenada": "$SET25_FONTE",
        "url_fonte": "$SET25_URL",
        "osm_id": $SET25_OSMID_FIELD,
        "n_familias": 289,
        "ano_reassentamento": 2009,
        "operador": "Vale Moçambique",
        "confianca": "$SET25_CONF",
        "notas": "$SET25_NOTAS"
      },
      "geometry": $SET25_GEOM
    },
    {
      "type": "Feature",
      "properties": {
        "nome": "Mwaladzi",
        "tipo": "rural",
        "fonte_coordenada": "OSM (Nominatim)",
        "url_fonte": "https://www.openstreetmap.org/$MWALADZI_OSMTYPE/$MWALADZI_OSMID",
        "osm_id": "$MWALADZI_OSMTYPE/$MWALADZI_OSMID",
        "n_familias": 84,
        "ano_reassentamento": 2011,
        "operador": "Riversdale/Rio Tinto (projeto Benga)",
        "confianca": "alta",
        "notas": "Coordenada resolvida via Nominatim em $DOWNLOAD_DATE: $MWALADZI_DISPLAY. n_familias=84 conforme HRW 2013 ('Rio Tinto and Riversdale resettled 84 households to a newly-constructed village, Mwaladzi, in 2011'); HRW registra plano de reassentar mais 595 famílias até mai/2013, não confirmado como concluído nesta pesquisa."
      },
      "geometry": {
        "type": "Point",
        "coordinates": [$MWALADZI_LON, $MWALADZI_LAT]
      }
    }
  ]
}
EOF

python3 -c "import json,sys; json.load(open('$OUTPUT_FILE'))" || die "GeoJSON gerado é inválido."

shasum -a 256 "$OUTPUT_FILE" | awk '{print $1}' > "$SHA_FILE"
SHA=$(awk '{print $1}' "$SHA_FILE")
SIZE=$(wc -c < "$OUTPUT_FILE" | tr -d ' ')

cat > "$META_FILE" <<EOF
{
  "url": "https://nominatim.openstreetmap.org/search (Cateme, Mwaladzi); https://overpass.kumi.systems/api/interpreter (25 de Setembro, sem resultado)",
  "download_date": "$DOWNLOAD_DATE",
  "size_bytes": $SIZE,
  "license": "ODbL 1.0 (c) OpenStreetMap contributors -- https://www.openstreetmap.org/copyright",
  "level": "A",
  "source_page": "https://nominatim.openstreetmap.org ; https://overpass-api.de",
  "sha256": "$SHA",
  "description": "Pontos OSM para os povoados de reassentamento de Cateme e Mwaladzi (Nominatim, elemento node resolvido); 25 de Setembro sem elemento OSM localizável em ambas as APIs consultadas. n_familias e ano_reassentamento vêm de HRW 2013, não do OSM."
}
EOF

log "✓ GeoJSON gravado em $OUTPUT_FILE (sha256=$SHA, size=$SIZE bytes)"
exit 0
