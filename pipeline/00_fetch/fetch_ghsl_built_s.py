#!/usr/bin/env python3
"""pipeline/00_fetch/fetch_ghsl_built_s.py — espelha GHSL BUILT-S R2023A (JRC).

Nível A (CC-BY-4.0, ver data/LICENSES.md). Grade 3 arcsec (~100 m) em EPSG:4326,
épocas quinquenais. **Só as épocas OBSERVADAS (1975–2020) são baixadas aqui.**
As épocas 2025/2030 do R2023A/R2025A são EXTRAPOLADAS por modelo, não observadas
(§0 e §8 do prompt-mestre): usá-las como referência independente de validação de
uma classificação de 2025 seria validar observação contra extrapolação. Por isso
2025 fica deliberadamente de fora e a validação cruzada de 2025 é declarada
ausente, não substituída.

Papel no pipeline (declarado, §5.1): GHSL é **referência independente de
concordância** — não entra em treino, não entra em nenhum limiar. O WSF Evolution
tem o papel oposto (semeia treino) e por isso não pode ser reusado como
referência. Ver docstring de pipeline/01_imagery/classificacao.py.

Uso: uv run python pipeline/00_fetch/fetch_ghsl_built_s.py
"""

from __future__ import annotations

import hashlib
import io
import json
import sys
import urllib.request
import zipfile
from datetime import UTC, datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _config import carregar_aoi

REPO_ROOT = Path(__file__).resolve().parents[2]
DATA_RAW = REPO_ROOT / "data" / "raw"

EPOCAS_OBSERVADAS = [2000, 2005, 2010, 2015, 2020]
BASE = (
    "https://jeodpp.jrc.ec.europa.eu/ftp/jrc-opendata/GHSL/GHS_BUILT_S_GLOBE_R2023A/"
    "GHS_BUILT_S_E{e}_GLOBE_R2023A_4326_3ss/V1-0/tiles/"
    "GHS_BUILT_S_E{e}_GLOBE_R2023A_4326_3ss_V1_0_{tile}.zip"
)
LICENCA = "CC-BY-4.0 (JRC/Copernicus) — Pesaresi & Politis, GHSL R2023A"


def tile_de_aoi(aoi: dict) -> str:
    """Tile 10°x10° da grade GHSL 4326 que contém o canto NW da AOI.

    Convenção GHSL: R1 cobre 90N..80N, C1 cobre 180W..170W. A AOI do estudo
    (33.5–34.1 E, 16.35–16.0 S) cabe inteira em um único tile; se um dia a AOI
    cruzar uma borda de tile, esta função precisa devolver lista (falha alta e
    explícita abaixo, em vez de baixar o tile errado em silêncio).
    """
    linha = int((90.0 - aoi["ymax"]) // 10) + 1
    coluna = int((aoi["xmin"] + 180.0) // 10) + 1
    linha_sul = int((90.0 - aoi["ymin"]) // 10) + 1
    coluna_leste = int((aoi["xmax"] + 180.0) // 10) + 1
    if (linha, coluna) != (linha_sul, coluna_leste):
        raise RuntimeError(
            "AOI cruza mais de um tile GHSL — esta função só trata o caso de tile "
            f"único (NW=R{linha}_C{coluna}, SE=R{linha_sul}_C{coluna_leste})."
        )
    return f"R{linha}_C{coluna}"


def baixar(epoca: int, tile: str) -> Path:
    url = BASE.format(e=epoca, tile=tile)
    destino = DATA_RAW / f"ghsl_built_s_E{epoca}_R2023A_4326_3ss_{tile}.tif"
    if destino.exists():
        print(f"[skip] {destino.name} já existe", file=sys.stderr)
        return destino
    print(f"[get ] {url}", file=sys.stderr)
    with urllib.request.urlopen(url, timeout=300) as resp:
        bruto = resp.read()
    with zipfile.ZipFile(io.BytesIO(bruto)) as zf:
        nomes = [n for n in zf.namelist() if n.lower().endswith(".tif")]
        if len(nomes) != 1:
            raise RuntimeError(f"esperava 1 .tif no zip de {epoca}, achei {nomes}")
        destino.write_bytes(zf.read(nomes[0]))
    sha = hashlib.sha256(destino.read_bytes()).hexdigest()
    destino.with_suffix(".tif.sha256").write_text(f"{sha}  {destino.name}\n", encoding="utf-8")
    destino.with_suffix(".tif.meta.json").write_text(
        json.dumps(
            {
                "fonte": "GHSL BUILT-S R2023A (JRC/Copernicus)",
                "url": url,
                "epoca": epoca,
                "selo": "observado",
                "nivel_dados": "A",
                "licenca": LICENCA,
                "resolucao": "3 arcsec (~100 m), EPSG:4326",
                "papel_no_pipeline": (
                    "referência independente de concordância na validação da "
                    "classificação (§5.1). NÃO usado em treino nem em limiares."
                ),
                "sha256": sha,
                "data_download": datetime.now(UTC).isoformat(),
                "script": "pipeline/00_fetch/fetch_ghsl_built_s.py",
            },
            indent=2,
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    return destino


def main() -> int:
    aoi = carregar_aoi()
    tile = tile_de_aoi(aoi)
    for epoca in EPOCAS_OBSERVADAS:
        baixar(epoca, tile)
    print(
        "[nota] 2025 NÃO baixado: épocas 2025/2030 do GHSL são extrapoladas, não "
        "observadas — não servem de referência independente para 2025.",
        file=sys.stderr,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
