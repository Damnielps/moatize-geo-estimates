#!/bin/bash
# probe_stac.sh — Teste de disponibilidade de imagens via STAC (Fase 0', T2).
#
# Wrapper fino em torno de probe_stac.py. A lógica de consulta, paginação e
# contagem vive em Python (parsing YAML/JSON robusto); este script apenas
# garante o ambiente (uv) e repassa o caminho de saída.
#
# Uso: bash probe_stac.sh [output_csv]
# Idempotente: reescreve o CSV inteiro a cada execução, mesmo esquema.
# Falha explicitamente (exit != 0) se a consulta a algum endpoint não puder
# ser completada de forma alguma (ver mensagens de erro em stderr e a
# coluna `status` do CSV para falhas por ano/plataforma/coleção).

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

OUTPUT_CSV="${1:-$REPO_ROOT/data/interim/stac_disponibilidade.csv}"

cd "$REPO_ROOT"
uv run python3 "$SCRIPT_DIR/probe_stac.py" "$OUTPUT_CSV"
