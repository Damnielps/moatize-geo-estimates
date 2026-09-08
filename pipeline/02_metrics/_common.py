#!/usr/bin/env python3
"""pipeline/02_metrics/_common.py — utilidades compartilhadas de §5.2.

Concentra o que os quatro scripts de métrica de forma urbana (`area_cagr.py`,
`tipologia_expansao.py`, `fragmentacao.py`, `edificacoes.py`) precisam em
comum: leitura de config, leitura das camadas classificadas e do WSF
Evolution na mesma grade, pontos-sede das unidades de análise e a atribuição
de cada pixel construído à unidade mais próxima.

## Unidades de análise (§3 do CLAUDE.md) e como cada uma é delimitada aqui

Não existe polígono administrativo aberto para "núcleo urbano de Tete" ou
"vila de Moatize" no acervo desta pesquisa — `data/raw/hdx_cod-ab-moz_admin_boundaries.xlsx`
é uma tabela de população por unidade administrativa, sem geometria. Em vez de
inventar um limite, cada pixel construído é atribuído à unidade cujo
**ponto-sede** (§8 do CLAUDE.md / `docs/ADR/0001-aoi-final.md`) está mais
próximo — uma partição de Voronoi sobre os cinco pontos-sede. É uma
aproximação declarada, não um limite administrativo:

- `tete` — Cidade de Tete, 33.5871E/16.1604S (ADR 0001)
- `moatize` — vila de Moatize, 33.7288E/16.1178S (ADR 0001)
- `cateme` — povoado de reassentamento, coordenada em `data/raw/reassentamentos.geojson`
- `mwaladzi` — povoado de reassentamento, idem
- `industrial` — **não** entra na partição de Voronoi. É definida pela camada
  `industrial` da classificação (que já usa o polígono de Maus et al. como
  semente — ver `classificacao.py::carregar_poligono_mineracao`) e, para a
  série do WSF Evolution (que não distingue uso do solo, só presença de
  assentamento), pela exclusão de qualquer pixel WSF dentro do polígono de
  Maus et al. + 150 m de guarda da série de `tete`/`moatize`/`cateme`/`mwaladzi`
  — ver `excluir_poligono_mineracao_wsf()`.

**"25 de Setembro" não entra**: `geometry: null` em `reassentamentos.geojson`
(ver restrição 3 da tarefa). Qualquer pixel construído que pertença a esse
povoado é atribuído, por proximidade, a `moatize` — ele é geometricamente o
mais próximo dos quatro pontos-sede. Isso **infla `moatize`** com crescimento
por reassentamento que §10 do CLAUDE.md manda contar à parte; a magnitude não
é estimável sem a geometria (mesma conclusão da Fase 1). Toda saída que usa
esta atribuição carrega essa nota.
"""

from __future__ import annotations

import sys
from pathlib import Path

import geopandas as gpd
import numpy as np
import rasterio
import rasterio.features
import yaml
from pyproj import Transformer
from scipy.spatial import cKDTree

REPO_ROOT = Path(__file__).resolve().parents[2]
STUDY_YAML = REPO_ROOT / "config" / "study.yaml"
IMAGERY_DIR = REPO_ROOT / "data" / "processed" / "imagery"
DATA_RAW = REPO_ROOT / "data" / "raw"
DATA_PROCESSED = REPO_ROOT / "data" / "processed"
REASSENTAMENTOS_GEOJSON = DATA_RAW / "reassentamentos.geojson"
MAUS_AOI_GEOJSON = DATA_RAW / "global_mining_polygons_v2_maus_2022_aoi.geojson"
OPEN_BUILDINGS_CSV = DATA_RAW / "open_buildings_v3_aoi.csv"

CAMADAS_CONSTRUIDO = ["urbano", "industrial", "reassentamento"]

# Ponto-sede de cada unidade urbana/vila, em WGS84 (EPSG:4326) — fonte:
# docs/ADR/0001-aoi-final.md (Cidade de Tete, Vila de Moatize) e
# data/raw/reassentamentos.geojson (Cateme, Mwaladzi). "25 de Setembro" fica
# fora por não ter geometria localizável (ver docstring do módulo).
PONTOS_SEDE_WGS84 = {
    "tete": (33.5871, -16.1604),
    "moatize_vila": (33.7288, -16.1178),
}

# Guarda de 150 m em torno do polígono de mineração (mesmo valor de
# FAIXA_GUARDA_NEGATIVO_M em classificacao.py) para excluir pixels do WSF que
# estão dentro/junto da pegada industrial da série "assentamento" de tete/
# moatize/cateme/mwaladzi.
GUARDA_INDUSTRIAL_WSF_M = 150.0

SELOS_VALIDOS = {"observado", "interpolado", "modelado"}


def carregar_estudo(path: Path = STUDY_YAML) -> dict:
    with open(path, encoding="utf-8") as f:
        return yaml.safe_load(f)


def epsg_metrico(estudo: dict | None = None) -> int:
    estudo = estudo or carregar_estudo()
    return int(estudo["crs"]["metrico"].split(":")[-1])


def carregar_pontos_reassentamento_wgs84() -> dict[str, tuple[float, float] | None]:
    """{'cateme': (lon, lat), 'mwaladzi': (lon, lat), '25_de_setembro': None}."""
    gdf = gpd.read_file(REASSENTAMENTOS_GEOJSON)
    pontos: dict[str, tuple[float, float] | None] = {}
    for _, row in gdf.iterrows():
        chave = "25_de_setembro" if row["nome"] == "25 de Setembro" else row["nome"].lower()
        if row.geometry is None:
            pontos[chave] = None
        else:
            pontos[chave] = (row.geometry.x, row.geometry.y)
    return pontos


def pontos_sede_utm(epsg: int) -> dict[str, tuple[float, float]]:
    """Todos os pontos-sede localizáveis (tete, moatize, cateme, mwaladzi),
    projetados para o CRS métrico do estudo. NÃO inclui '25 de Setembro'
    (sem geometria) nem 'industrial' (não é um ponto — ver docstring)."""
    transformer = Transformer.from_crs("EPSG:4326", f"EPSG:{epsg}", always_xy=True)
    pontos = {}
    for nome, (lon, lat) in PONTOS_SEDE_WGS84.items():
        pontos[nome] = transformer.transform(lon, lat)
    for nome, coord in carregar_pontos_reassentamento_wgs84().items():
        if coord is not None:
            pontos[nome] = transformer.transform(*coord)
    return pontos


def carregar_camada(
    camada: str, ano: int, res_m: int = 30, epsg: int | None = None
) -> tuple[np.ndarray, dict]:
    epsg = epsg or epsg_metrico()
    caminho = IMAGERY_DIR / f"{camada}_{ano}_{res_m}m_{epsg}.tif"
    with rasterio.open(caminho) as src:
        arr = src.read(1).astype(bool)
        perfil = {
            "transform": src.transform,
            "crs": src.crs,
            "shape": src.shape,
            "width": src.width,
            "height": src.height,
        }
    return arr, perfil


def carregar_construido_total(
    ano: int, res_m: int = 30, epsg: int | None = None
) -> tuple[np.ndarray, dict]:
    """União das três camadas mutuamente exclusivas — só para uso interno
    (ex.: máscara de referência de grade). Nunca é publicada como 'unidade'."""
    mask = None
    perfil = {}
    for camada in CAMADAS_CONSTRUIDO:
        m, perfil = carregar_camada(camada, ano, res_m, epsg)
        mask = m if mask is None else (mask | m)
    return mask, perfil


def carregar_wsf_reprojetado(perfil: dict) -> np.ndarray:
    """Reusa a rotina de reprojeção do WSF Evolution de `01_imagery/classificacao.py`
    (mesmo mosaico, mesmo resampling nearest) para não duplicar a lógica de
    fusão de tiles. Valor de retorno: ano da primeira detecção por pixel (0 = nunca)."""
    sys.path.insert(0, str(REPO_ROOT / "pipeline" / "01_imagery"))
    from classificacao import carregar_wsf_reprojetado as _carregar

    return _carregar(perfil)


def carregar_poligono_mineracao_utm(epsg: int):
    sys.path.insert(0, str(REPO_ROOT / "pipeline" / "01_imagery"))
    from classificacao import carregar_poligono_mineracao

    return carregar_poligono_mineracao(f"EPSG:{epsg}")


def rasterizar_geometria(geometria, perfil: dict) -> np.ndarray:
    if geometria is None or geometria.is_empty:
        return np.zeros(perfil["shape"], dtype=bool)
    return rasterio.features.rasterize(
        [(geometria, 1)],
        out_shape=perfil["shape"],
        transform=perfil["transform"],
        fill=0,
        dtype="uint8",
        all_touched=False,
    ).astype(bool)


def mascara_exclusao_industrial(perfil: dict, epsg: int) -> np.ndarray:
    """Máscara True dentro do polígono de mineração (Maus et al.) + 150 m de
    guarda — usada para tirar pixels da série do WSF Evolution antes de
    atribuí-los a tete/moatize/cateme/mwaladzi (ver docstring do módulo)."""
    poligono = carregar_poligono_mineracao_utm(epsg)
    if poligono is None:
        return np.zeros(perfil["shape"], dtype=bool)
    guarda = poligono.buffer(GUARDA_INDUSTRIAL_WSF_M)
    return rasterizar_geometria(guarda, perfil)


def coordenadas_pixels(mask: np.ndarray, transform) -> tuple[np.ndarray, np.ndarray]:
    """Coordenadas (x, y) do CENTRO de cada pixel True de `mask`, no CRS de `transform`."""
    linhas, colunas = np.where(mask)
    xs, ys = rasterio.transform.xy(transform, linhas, colunas, offset="center")
    return np.asarray(xs), np.asarray(ys)


def atribuir_unidade_mais_proxima(
    mask: np.ndarray, transform, pontos: dict[str, tuple[float, float]]
) -> dict[str, np.ndarray]:
    """Particiona os pixels True de `mask` entre as unidades de `pontos` por
    vizinho mais próximo (Voronoi). Retorna {unidade: mask_bool_mesma_forma}."""
    nomes = list(pontos.keys())
    arvore = cKDTree(np.array([pontos[n] for n in nomes]))
    linhas, colunas = np.where(mask)
    if linhas.size == 0:
        return {n: np.zeros(mask.shape, dtype=bool) for n in nomes}
    xs, ys = rasterio.transform.xy(transform, linhas, colunas, offset="center")
    _, idx = arvore.query(np.column_stack([xs, ys]))
    saida = {n: np.zeros(mask.shape, dtype=bool) for n in nomes}
    for i, nome in enumerate(nomes):
        sel = idx == i
        saida[nome][linhas[sel], colunas[sel]] = True
    return saida


def area_km2(mask: np.ndarray, res_m: float = 30.0) -> float:
    return float(mask.sum()) * (res_m * res_m) / 1e6


def cagr(area_inicial: float, area_final: float, anos: float) -> float | None:
    """Taxa de crescimento anual composta. None se a base for <=0 ou o
    intervalo <=0 (log indefinido / divisão por zero) — nunca inventa um
    valor para esses casos."""
    if area_inicial <= 0 or anos <= 0:
        return None
    return (area_final / area_inicial) ** (1.0 / anos) - 1.0


def checar_selo(selo: str) -> str:
    if selo not in SELOS_VALIDOS:
        raise ValueError(f"selo inválido: {selo!r} — precisa ser um de {SELOS_VALIDOS}")
    return selo
