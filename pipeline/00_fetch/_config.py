#!/usr/bin/env python3
"""pipeline/00_fetch/_config.py — leitura centralizada de config/study.yaml.

§11.2.1: `config/` é a única fonte da AOI. Nenhum script de fetch pode copiar o
bbox para dentro de si — quem faz isso deixa de acompanhar o ADR que corrige a
AOI (docs/ADR/0001-aoi-final.md) e passa a baixar a área errada em silêncio.

Todo script de `pipeline/00_fetch/` que precisa da AOI importa `carregar_aoi()`
daqui. Scripts que também recortam a AOI em grades de tiles (WSF, ESA
WorldCover, Copernicus DEM) usam `tile_sw_corners()`.
"""

from __future__ import annotations

import math
from pathlib import Path

import yaml

REPO_ROOT = Path(__file__).resolve().parents[2]
STUDY_YAML = REPO_ROOT / "config" / "study.yaml"


def carregar_estudo(path: Path = STUDY_YAML) -> dict:
    """Carrega config/study.yaml inteiro."""
    with open(path, encoding="utf-8") as f:
        return yaml.safe_load(f)


def carregar_aoi(path: Path = STUDY_YAML) -> dict:
    """Retorna o bbox da AOI: {xmin, ymin, xmax, ymax, crs}.

    Fonte única: config/study.yaml -> aoi.bbox. Não hardcode o bbox em nenhum
    script de fetch (ver docstring do módulo).
    """
    estudo = carregar_estudo(path)
    aoi = estudo["aoi"]
    bbox = aoi["bbox"]
    return {
        "xmin": bbox["xmin"],
        "ymin": bbox["ymin"],
        "xmax": bbox["xmax"],
        "ymax": bbox["ymax"],
        "crs": aoi.get("crs_definicao", "EPSG:4326"),
    }


def tile_sw_corners(
    aoi: dict, size: float, eps: float = 1e-9
) -> list[tuple[float, float]]:
    """Cantos SW (lat, lon) dos tiles de `size` graus que cobrem a AOI.

    Convenção de grade: um tile de canto SW (lat0, lon0) cobre o intervalo
    [lat0, lat0+size) x [lon0, lon0+size), ancorado em múltiplos de `size` a
    partir do equador/meridiano de Greenwich (convenção dos tiles Copernicus
    DEM de 1° e ESA WorldCover de 3°).

    Subtrai-se `eps` do lado máximo do bbox antes de arredondar para baixo,
    para não puxar um tile extra quando o limite da AOI cai exatamente sobre
    uma linha de grade (ex.: ymax = -16.00 não precisa do tile ao norte,
    porque o tile ao sul já cobre esse ponto — os tiles reais têm alguma
    sobreposição/arredondamento de borda, mas a convenção lógica de grade é
    half-open). Isso é intencional e deve ser revisto caso a AOI mude de
    forma a colar exatamente sobre outra linha de grade.
    """

    def _piso_na_grade(v: float) -> float:
        return math.floor(v / size) * size

    lat0 = _piso_na_grade(aoi["ymin"])
    lat1 = _piso_na_grade(aoi["ymax"] - eps)
    lon0 = _piso_na_grade(aoi["xmin"])
    lon1 = _piso_na_grade(aoi["xmax"] - eps)

    lats = []
    v = lat0
    while v <= lat1 + eps:
        lats.append(round(v, 6))
        v += size

    lons = []
    v = lon0
    while v <= lon1 + eps:
        lons.append(round(v, 6))
        v += size

    return [(lat, lon) for lat in lats for lon in lons]
