"""Constrói as duas séries-base da Fase 3 (§5.4, emendado em docs/DESENHO_FASE3.md §11).

Saídas:
  data/processed/causal/serie_luzes_anual.csv   S_HARM_soma (Chen/Yu 2021, CC0, nível A)
  data/processed/causal/serie_wsf_taxa_anual.csv S_WSF_taxa (DLR WSF Evolution, nível A)

Geometria: recorte fixo por unidade (EMENDA E6). Sensibilidade: ADM2 ∩ recorte.
Sem seed: nenhuma etapa aqui é estocástica.
"""

from __future__ import annotations

import json
from pathlib import Path

import geopandas as gpd
import numpy as np
import pandas as pd
import rasterio
from rasterio.mask import mask
from shapely.geometry import box

RAIZ = Path(__file__).resolve().parents[2]
SAIDA = RAIZ / "data" / "processed" / "causal"
CODAB = f"zip://{RAIZ}/data/raw/hdx_cod-ab-moz_admin_boundaries.geojson.zip!moz_admin2.geojson"

UNIDADES = {
    "tete_aoi": ("MZ0501", "Cidade de Tete", "tratada"),
    "chimoio": ("MZ0601", "Cidade de Chimoio", "controle"),
    "quelimane": ("MZ0401", "Quelimane", "controle"),
    "lichinga": ("MZ0101", "Cidade de Lichinga", "controle"),
    "xaixai": ("MZ0901", "Xai-Xai", "controle"),
    "inhambane": ("MZ0801", "Cidade de Inhambane", "controle"),
}
# tile WSF por unidade; Tete precisa dos dois (a AOI cruza 34°E)
WSF = {
    "tete_aoi": ["wsf_evolution_S18E032.tif", "wsf_evolution_S18E034.tif"],
    "chimoio": ["wsf_evolution_S20E032.tif"],
    "quelimane": ["wsf_evolution_S18E036.tif"],
    "lichinga": ["wsf_evolution_S14E034.tif"],
    "xaixai": ["wsf_evolution_S26E032.tif"],
    "inhambane": ["wsf_evolution_S24E034.tif"],
}


def _adm2() -> gpd.GeoDataFrame:
    return gpd.read_file(CODAB)


def _recorte_bounds(uni: str, ano: int = 2013) -> tuple:
    f = RAIZ / "data" / "raw" / f"viirs_like_li2020_v2_{ano}_{uni}.tif"
    with rasterio.open(f) as s:
        return tuple(s.bounds)


def serie_luzes() -> pd.DataFrame:
    adm2 = _adm2()
    anos = sorted(
        int(p.name.split("_v2_")[1].split("_")[0])
        for p in (RAIZ / "data" / "raw").glob("viirs_like_li2020_v2_*_tete_aoi.tif")
    )
    linhas = []
    for uni, (pcode, nome, papel) in UNIDADES.items():
        geo_adm2 = adm2[adm2.adm2_pcode == pcode].geometry.iloc[0]
        b = _recorte_bounds(uni)
        cob = geo_adm2.intersection(box(*b))
        # fração de cobertura em área métrica
        g = gpd.GeoSeries([geo_adm2, cob], crs=4326).to_crs(32736)
        frac = float(g.iloc[1].area / g.iloc[0].area)
        for ano in anos:
            f = RAIZ / "data" / "raw" / f"viirs_like_li2020_v2_{ano}_{uni}.tif"
            with rasterio.open(f) as src:
                a = src.read(1).astype("float64")
                a = np.where(np.isfinite(a), a, 0.0)
                try:
                    m, _ = mask(src, [cob], crop=False, filled=True, nodata=0.0)
                    a_adm2 = np.where(np.isfinite(m[0]), m[0], 0.0)
                except Exception:
                    a_adm2 = np.full_like(a, np.nan)
            linhas.append(
                {
                    "unidade": uni,
                    "adm2_nome": nome,
                    "adm2_pcode": pcode,
                    "papel": papel,
                    "ano": ano,
                    "soma_radiancia": float(a.sum()),
                    "media_radiancia": float(a.mean()),
                    "max_radiancia": float(a.max()),
                    "n_pixels": int(a.size),
                    "n_acesos": int((a > 0).sum()),
                    "frac_acesos": float((a > 0).mean()),
                    "soma_radiancia_adm2_int_recorte": float(np.nansum(a_adm2)),
                    "cobertura_adm2_no_recorte": round(frac, 4),
                    "janela_homogenea": ano >= 2013,
                    "geometria": "recorte fixo (EMENDA E6); ADM2 apenas como sensibilidade",
                    "selo": "observado",
                    "nivel_fonte": "A",
                    "fonte": (
                        "Chen, Z., Yu, B. et al. (2021) ESSD 13:889-906, "
                        "DOI 10.5194/essd-13-889-2021; dataset Harvard Dataverse "
                        "10.7910/DVN/YGIVCD (CC0). ATENCAO: prefixo de arquivo "
                        "'viirs_like_li2020_' e heranca de erro; NAO e Li et al. 2020."
                    ),
                }
            )
    return pd.DataFrame(linhas)


def serie_wsf() -> pd.DataFrame:
    """Área de PRIMEIRA DETECÇÃO por ano (km²/ano). Não é estoque (ADR 0008/0013)."""
    linhas = []
    for uni, (_pcode, nome, papel) in UNIDADES.items():
        b = _recorte_bounds(uni)
        recorte = box(*b)
        cont = []
        for tile in WSF[uni]:
            with rasterio.open(RAIZ / "data" / "raw" / tile) as src:
                inter = box(*src.bounds).intersection(recorte)
                if inter.is_empty:
                    continue
                out, tr = mask(src, [inter], crop=True, filled=True, nodata=0)
                arr = out[0]
                # área de pixel: grade geográfica -> usar latitude central
                lat = (inter.bounds[1] + inter.bounds[3]) / 2.0
                px_km2 = (
                    abs(tr.a) * 111.32 * np.cos(np.radians(lat)) * abs(tr.e) * 110.57
                )
                anos_v, n = np.unique(arr[arr > 0], return_counts=True)
                cont.append(pd.Series(n * px_km2, index=anos_v.astype(int)))
        s = pd.concat(cont).groupby(level=0).sum() if cont else pd.Series(dtype=float)
        for ano in range(1985, 2016):
            linhas.append(
                {
                    "unidade": uni,
                    "adm2_nome": nome,
                    "papel": papel,
                    "ano": ano,
                    "area_primeira_deteccao_km2": float(s.get(ano, 0.0)),
                    "n_pixels": int(round(float(s.get(ano, 0.0)) / 0.000899, 0)),
                    "selo": "observado",
                    "nivel_fonte": "A",
                    "fonte": "DLR World Settlement Footprint Evolution (30 m, 1985-2015)",
                    "nota": (
                        "TAXA de primeira deteccao, nao estoque. O acumulado e "
                        "monotonico por construcao (ADR 0008 emenda, ADR 0013): "
                        "nenhuma contracao e detectavel nesta serie."
                    ),
                }
            )
    return pd.DataFrame(linhas)


def main() -> None:
    SAIDA.mkdir(parents=True, exist_ok=True)
    dl = serie_luzes()
    dl.to_csv(SAIDA / "serie_luzes_anual.csv", index=False)
    dw = serie_wsf()
    dw.to_csv(SAIDA / "serie_wsf_taxa_anual.csv", index=False)
    meta = {
        "script": "pipeline/03_causal/series_base.py",
        "desenho": "docs/DESENHO_FASE3.md (pré-registro) + EMENDA 1 de 2026-09-08 (§11)",
        "geometria": "recorte fixo por unidade (E6); ADM2 ∩ recorte como sensibilidade",
        "janela_homogenea_luzes": "2013-2025 (E4)",
        "anos_luz": sorted(dl.ano.unique().tolist()),
        "unidades": list(UNIDADES),
        "estocastico": False,
    }
    (SAIDA / "series_base.meta.json").write_text(
        json.dumps(meta, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    print(dl.groupby("unidade").soma_radiancia.apply(lambda x: round(x.iloc[-1], 1)))
    print(dw.groupby("unidade").area_primeira_deteccao_km2.sum().round(2))


if __name__ == "__main__":
    main()
