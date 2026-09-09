#!/usr/bin/env python3
"""pipeline/01_imagery/varzea.py — zona de várzea por HAND (§5.6.2, Fase 2b).

Máscara estática (não varia por ano-âncora — é geomorfologia, não cobertura do solo)
que aproxima "cultivo de vazante" (§3): planície aluvial do Zambeze, do Revúbuè e de
riachos menores, onde o cultivo de estação seca é fisicamente viável por proximidade ao
lençol/inundação sazonal. Parâmetros: `config/study.yaml ->
zoneamento_agricola.varzea` (`hand_max_m`, `dist_max_rio_m`).

## O que é calculado — e o que NÃO é

HAND (height above nearest drainage) canônico (Rennó et al. 2008) exige rede de
drenagem por acumulação de fluxo D8 sobre o DEM e, a partir dela, o caminho de fluxo até
a célula de drenagem mais próxima HIDROLOGICAMENTE conectada. Este ambiente não tem
biblioteca de roteamento hidrológico (`pysheds`/`richdem`/`whitebox` — nenhuma
disponível; ver `pyproject.toml`), e implementar D8 + acumulação de fluxo do zero está
fora do escopo desta entrega.

**Aproximação adotada, declarada explicitamente:** HAND por VIZINHO MAIS PRÓXIMO NO
PLANO, não por caminho de fluxo:

    HAND_aprox(pixel) = DEM(pixel) - DEM(pixel do rio mais próximo por distância euclidiana)

calculado com `scipy.ndimage.distance_transform_edt(..., return_indices=True)`, que
devolve ao mesmo tempo a distância e o índice do pixel-rio mais próximo — exatamente os
dois insumos de que a regra precisa (`hand_max_m` e `dist_max_rio_m`).

**Por que a aproximação é aceitável aqui e onde ela falha:** no vale do Zambeze/Revúbuè
dentro da AOI o relevo é de baixa declividade e a rede de drenagem é relativamente densa
(ver `data/raw/hydrorivers_af_v10.gdb.zip` recortado à AOI); nessas condições o pixel-rio
mais próximo no plano tende a coincidir com o pixel-rio hidrologicamente conectado mais
próximo. A aproximação **superestima** a várzea em relevo mais dissecado, onde um vizinho
planar próximo pode estar do outro lado de uma crista (hidrologicamente distante apesar
de fisicamente perto) — não há correção para esse efeito neste desenho; é uma limitação
declarada, não uma falha silenciosa.

## Fonte de drenagem

HydroRIVERS v10 Africa (Lehner & Grill 2013, nível A), recortado à AOI. **Nenhum filtro
de ordem de fluxo é aplicado**: todos os trechos dentro da AOI entram na rede rasterizada,
incluindo os menores, porque riachos pequenos também sustentam cultivo de vazante local
(§3). Isso torna a várzea mais abrangente do que se só o Zambeze/Revúbuè principais
fossem considerados — declarado, não escondido.

Uso: `uv run python pipeline/01_imagery/varzea.py`
"""

from __future__ import annotations

import glob
import json
import sys
import tempfile
import zipfile
from datetime import UTC, datetime
from pathlib import Path

import geopandas as gpd
import numpy as np
import rasterio
import rasterio.features
import rasterio.warp
from rasterio.merge import merge as rasterio_merge
from scipy.ndimage import distance_transform_edt

sys.path.insert(0, str(Path(__file__).resolve().parent))
from classificacao import (
    area_km2,
    commit_git_atual,
    hash_arquivo,
    salvar_raster,
    salvar_vetor,
)

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "00_fetch"))
from _config import carregar_estudo

REPO_ROOT = Path(__file__).resolve().parents[2]
STUDY_YAML = REPO_ROOT / "config" / "study.yaml"
DATA_RAW = REPO_ROOT / "data" / "raw"
DATA_PROCESSED = REPO_ROOT / "data" / "processed" / "imagery"
VARZEA_TIF = DATA_PROCESSED / "varzea_30m_32736.tif"
VARZEA_GEOJSON = DATA_PROCESSED / "varzea.geojson"
PROVENANCE_FRAGMENT = REPO_ROOT / "data" / "provenance_parts" / "agricultura_fase2b.md"
MARCADOR_INICIO = "<!-- SECAO_VARZEA_INICIO -->"
MARCADOR_FIM = "<!-- SECAO_VARZEA_FIM -->"

DEM_TILES = sorted(DATA_RAW.glob("copernicus_dem_glo30_*.tif"))
HYDRORIVERS_ZIP = DATA_RAW / "hydrorivers_af_v10.gdb.zip"


def perfil_referencia() -> dict:
    """Grade de referência: qualquer composto já gerado (mesma grade em todos os anos)."""
    candidatos = sorted(DATA_PROCESSED.glob("composto_*_30m_32736.tif"))
    if not candidatos:
        raise FileNotFoundError("nenhum composto_*_30m_32736.tif — rode compostos.py antes")
    with rasterio.open(candidatos[0]) as src:
        return {"crs": src.crs, "transform": src.transform, "shape": src.shape}


def carregar_dem_reprojetado(perfil: dict) -> np.ndarray:
    if not DEM_TILES:
        raise FileNotFoundError("nenhum tile Copernicus DEM em data/raw/")
    fontes = [rasterio.open(p) for p in DEM_TILES]
    try:
        mosaico, transform_mosaico = rasterio_merge(fontes)
        crs_origem = fontes[0].crs
    finally:
        for f in fontes:
            f.close()
    destino = np.full(perfil["shape"], np.nan, dtype="float32")
    rasterio.warp.reproject(
        source=mosaico[0].astype("float32"),
        destination=destino,
        src_transform=transform_mosaico,
        src_crs=crs_origem,
        dst_transform=perfil["transform"],
        dst_crs=perfil["crs"],
        resampling=rasterio.warp.Resampling.bilinear,
        src_nodata=mosaico.fill_value if hasattr(mosaico, "fill_value") else None,
        dst_nodata=np.nan,
    )
    return destino


def carregar_rede_drenagem(
    perfil: dict, aoi_bbox4326: tuple[float, float, float, float]
) -> np.ndarray:
    if not HYDRORIVERS_ZIP.exists():
        raise FileNotFoundError(f"{HYDRORIVERS_ZIP} ausente")
    with tempfile.TemporaryDirectory() as tmp:
        with zipfile.ZipFile(HYDRORIVERS_ZIP) as z:
            z.extractall(tmp)
        gdb = glob.glob(f"{tmp}/*.gdb")[0]
        gdf = gpd.read_file(gdb, bbox=aoi_bbox4326)
    if gdf.empty:
        raise RuntimeError("HydroRIVERS não tem trechos dentro da AOI — verifique o recorte")
    gdf = gdf.to_crs(perfil["crs"])
    mask = rasterio.features.rasterize(
        [(geom, 1) for geom in gdf.geometry if geom is not None and not geom.is_empty],
        out_shape=perfil["shape"],
        transform=perfil["transform"],
        fill=0,
        dtype="uint8",
        all_touched=True,  # linha fina de rio não pode "cair entre" pixels de 30 m
    ).astype(bool)
    return mask, len(gdf)


def calcular_hand_aproximado(
    dem: np.ndarray, rio: np.ndarray, res_m: float
) -> tuple[np.ndarray, np.ndarray]:
    """HAND por vizinho mais próximo no plano (ver docstring do módulo).

    Devolve (hand_aprox, dist_m). Pixels sem DEM válido ficam NaN nos dois.
    """
    if not rio.any():
        raise RuntimeError("máscara de rede de drenagem vazia após rasterização")
    dist_px, indices = distance_transform_edt(~rio, return_indices=True)
    dist_m = dist_px * res_m
    dem_no_rio_mais_proximo = dem[indices[0], indices[1]]
    hand = dem - dem_no_rio_mais_proximo
    hand[~np.isfinite(dem)] = np.nan
    dist_m = dist_m.astype("float32")
    dist_m[~np.isfinite(dem)] = np.nan
    return hand, dist_m


def main(argv: list[str]) -> int:
    estudo = carregar_estudo(STUDY_YAML)
    cfg = estudo["zoneamento_agricola"]["varzea"]
    hand_max_m = float(cfg["hand_max_m"])
    dist_max_rio_m = float(cfg["dist_max_rio_m"])
    if cfg["metodo"] != "hand":
        raise NotImplementedError(f"método '{cfg['metodo']}' não implementado — só 'hand'")

    perfil = perfil_referencia()
    res_m = abs(perfil["transform"].a)
    bbox = estudo["aoi"]["bbox"]
    aoi_bbox4326 = (bbox["xmin"], bbox["ymin"], bbox["xmax"], bbox["ymax"])

    dem = carregar_dem_reprojetado(perfil)
    rio, n_trechos = carregar_rede_drenagem(perfil, aoi_bbox4326)
    hand, dist_m = calcular_hand_aproximado(dem, rio, res_m)

    valido = np.isfinite(hand) & np.isfinite(dist_m)
    # Piso de -2 m: ruído de DEM/borda de canal pode gerar HAND levemente negativo junto
    # ao próprio pixel-rio; não se trata o pixel de rio como "fora de várzea" por isso.
    varzea = valido & (hand >= -2.0) & (hand <= hand_max_m) & (dist_m <= dist_max_rio_m)

    transform, crs = perfil["transform"], perfil["crs"]
    salvar_raster(varzea, VARZEA_TIF, crs, transform)
    n_poligonos = salvar_vetor(varzea, VARZEA_GEOJSON, crs, transform, 0, "varzea")
    area = area_km2(varzea, transform)

    meta = {
        "camada": "varzea",
        "arquivo_raster": str(VARZEA_TIF.relative_to(REPO_ROOT)),
        "arquivo_vetor": str(VARZEA_GEOJSON.relative_to(REPO_ROOT)),
        "n_poligonos_vetor": n_poligonos,
        "area_km2": area,
        "resolucao_m": res_m,
        "crs": f"EPSG:{crs.to_epsg()}",
        "metodo": (
            "HAND aproximado por vizinho mais próximo no plano (scipy.ndimage."
            "distance_transform_edt), NÃO por caminho de fluxo D8 — ver docstring de "
            "varzea.py para a limitação declarada"
        ),
        "parametros": {"hand_max_m": hand_max_m, "dist_max_rio_m": dist_max_rio_m},
        "fonte_dem": [str(p.relative_to(REPO_ROOT)) for p in DEM_TILES],
        "fonte_drenagem": str(HYDRORIVERS_ZIP.relative_to(REPO_ROOT)),
        "n_trechos_hydrorivers_na_aoi": n_trechos,
        "natureza": (
            "camada ESTÁTICA (geomorfologia; não varia por ano-âncora) — cruzar com "
            "cultivo_irrigado/cultivo_sequeiro de cada ano em cultivo_varzea_por_ano.csv "
            "para a leitura de 'cultivo de vazante' de §3"
        ),
        "selo": "modelado (HAND derivado de DEM observado + rede de drenagem observada)",
        "data_processamento": datetime.now(UTC).isoformat(),
        "commit_git": commit_git_atual(),
        "hash_config_study_yaml": hash_arquivo(STUDY_YAML),
        "script": "pipeline/01_imagery/varzea.py",
    }
    VARZEA_TIF.with_suffix(".tif.meta.json").write_text(
        json.dumps(meta, indent=2, ensure_ascii=False), encoding="utf-8"
    )

    escrever_proveniencia(meta)
    print(f"[ok] várzea: {area:.1f} km² — {VARZEA_TIF.relative_to(REPO_ROOT)}", file=sys.stderr)
    return 0


def escrever_proveniencia(meta: dict) -> None:
    linhas = [
        MARCADOR_INICIO,
        "",
        "## Várzea — HAND aproximado (§5.6.2, Fase 2b)",
        "",
        "Gerado por `pipeline/01_imagery/varzea.py`. Camada ESTÁTICA (não varia por "
        "ano-âncora): geomorfologia, não cobertura do solo.",
        "",
        "**Aproximação declarada:** HAND por vizinho mais próximo NO PLANO "
        "(`scipy.ndimage.distance_transform_edt`), não por caminho de fluxo D8 — nenhuma "
        "biblioteca de roteamento hidrológico (`pysheds`/`richdem`/`whitebox`) está "
        "disponível neste ambiente. A aproximação tende a superestimar a várzea em "
        "relevo dissecado; é aceitável no vale de baixa declividade do Zambeze/Revúbuè "
        "dentro da AOI, mas não foi corrigida onde falha. Ver docstring completa do "
        "script.",
        "",
        f"- **Parâmetros (config/study.yaml):** hand_max_m={meta['parametros']['hand_max_m']}, "
        f"dist_max_rio_m={meta['parametros']['dist_max_rio_m']}",
        f"- **Fonte de drenagem:** HydroRIVERS v10 África, "
        f"{meta['n_trechos_hydrorivers_na_aoi']} trechos na AOI, sem filtro de ordem "
        "de fluxo (riachos pequenos incluídos)",
        f"- **Área de várzea:** {meta['area_km2']:.1f} km²",
        f"- **Selo:** {meta['selo']}",
        "",
        MARCADOR_FIM,
        "",
    ]
    atual = PROVENANCE_FRAGMENT.read_text(encoding="utf-8") if PROVENANCE_FRAGMENT.exists() else (
        "# Proveniência — Fase 2b: agricultura e várzea (§5.6)\n\n"
        "Fragmento consolidado por `scripts/consolidar_registros.py` em `PROVENANCE.md`. "
        "Não editar à mão as seções entre marcadores: são geradas pelo script "
        "correspondente.\n\n"
    )
    if MARCADOR_INICIO in atual and MARCADOR_FIM in atual:
        novo = atual.split(MARCADOR_INICIO)[0] + "\n".join(linhas) + atual.split(MARCADOR_FIM)[1]
    else:
        novo = atual + "\n" + "\n".join(linhas)
    PROVENANCE_FRAGMENT.parent.mkdir(parents=True, exist_ok=True)
    PROVENANCE_FRAGMENT.write_text(novo, encoding="utf-8")


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
