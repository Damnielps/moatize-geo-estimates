"""§5.5 e §5.6.7 — tres cenarios a 2035 e 2040, com sensibilidade a migracao liquida.

CENARIO E CENARIO, NAO PREVISAO. Todo numero abaixo tem selo `modelado` e premissa
declarada ao lado. Nenhum usa GHSL 2025/2030 (epocas extrapoladas).
Saidas: cenarios_2035_2040.csv, cenarios_pressao_varzea.csv
"""

from __future__ import annotations

import json
from pathlib import Path

import geopandas as gpd
import numpy as np
import pandas as pd
import rasterio
from rasterio.mask import mask
from scipy import ndimage

RAIZ = Path(__file__).resolve().parents[2]
SAIDA = RAIZ / "data" / "processed" / "causal"
IMG = RAIZ / "data" / "processed" / "imagery"
CODAB = f"zip://{RAIZ}/data/raw/hdx_cod-ab-moz_admin_boundaries.geojson.zip!moz_admin2.geojson"

# --- PREMISSAS DECLARADAS (nenhuma e estimada; todas sao escolhas, e estao aqui) ---
DELTA_PP = 1.5          # p.p./ano em torno da taxa do INE (regra explicita do desenho 6.2)
MIGRACAO_PP = [-1.0, 0.0, +1.0]   # sensibilidade a migracao liquida, 3 niveis
TAM_DOMICILIO = {"baixo": 4.5, "central": 5.0, "alto": 5.5}  # PREMISSA, nao observado
POP_2017 = {"Cidade de Tete": 307338, "Distrito de Moatize": 260843}
POP_2025 = {"Cidade de Tete": 460248, "Distrito de Moatize": 349103}
CAGR_INE = {"Cidade de Tete": 5.177, "Distrito de Moatize": 3.710}
SUBENUM = 3.7
CENARIOS = {"continuidade": 0.0, "declinio": -DELTA_PP, "diversificacao": +DELTA_PP}


def area_urbana_tete_2025() -> float:
    g = gpd.read_file(CODAB)
    geo = g[g.adm2_pcode == "MZ0501"].to_crs(32736).geometry.iloc[0]
    with rasterio.open(IMG / "urbano_2025_30m_32736.tif") as s:
        out, _ = mask(s, [geo], crop=True, filled=True, nodata=0)
    return float((out[0] > 0).sum() * 900 / 1e6)


def trajetorias() -> pd.DataFrame:
    area_tete = area_urbana_tete_2025()
    wsf = pd.read_csv(SAIDA / "serie_wsf_taxa_anual.csv")
    taxa_wsf = float(wsf[(wsf.unidade == "tete_aoi") & wsf.ano.between(2011, 2015)]
                     .area_primeira_deteccao_km2.mean())
    linhas = []
    for unidade in POP_2025:
        p0 = POP_2025[unidade]
        p0_aj = p0 * (1 + SUBENUM / 100)
        intens = (area_tete * 1e6 / p0) if unidade == "Cidade de Tete" else np.nan
        for cen, dc in CENARIOS.items():
            for mig in MIGRACAO_PP:
                r = (CAGR_INE[unidade] + dc + mig) / 100
                for h in (2035, 2040):
                    n = h - 2025
                    pop = p0 * (1 + r) ** n
                    pop_aj = p0_aj * (1 + r) ** n
                    area_int = intens * pop / 1e6 if unidade == "Cidade de Tete" else np.nan
                    area_wsf = (area_tete + taxa_wsf * n) if unidade == "Cidade de Tete" else np.nan
                    linhas.append({
                        "unidade": unidade, "cenario": cen, "migracao_liquida_pp": mig,
                        "horizonte": h, "taxa_anual_pct": round(r * 100, 3),
                        "populacao": round(pop),
                        "populacao_ajustada_3_7pct": round(pop_aj),
                        "domicilios_central_5_0": round(pop / TAM_DOMICILIO["central"]),
                        "domicilios_faixa_4_5_a_5_5": (
                            f"{round(pop / TAM_DOMICILIO['alto'])}-"
                            f"{round(pop / TAM_DOMICILIO['baixo'])}"),
                        "area_construida_km2_via_intensidade": (
                            round(area_int, 2) if area_int == area_int else np.nan),
                        "area_construida_km2_via_taxa_wsf": (
                            round(area_wsf, 2) if area_wsf == area_wsf else np.nan),
                        "selo": "modelado",
                        "premissa_taxa": (
                            f"CAGR INE 2017-2025 = {CAGR_INE[unidade]}%/ano "
                            f"(MODELADO na ponta de 2025) {dc:+.1f} p.p. do cenario "
                            f"{mig:+.1f} p.p. de migracao liquida"),
                        "premissa_domicilio": (
                            "tamanho medio do domicilio 4,5-5,5 pessoas: PREMISSA "
                            "declarada. Nao ha contagem de domicilios em nivel A "
                            "(ADR 0010); as taxas de acesso a agua/saneamento do Censo "
                            "2017 sao nivel C. A demanda e reportada como TOTAL A SERVIR, "
                            "nunca como deficit."),
                        "premissa_contaminada": (
                            "SIM - area via intensidade de uso: a intensidade "
                            f"({intens:.1f} m2/hab em 2025) vem da serie propria com "
                            "catraca R2 (ADR 0013). A variante via taxa WSF "
                            f"({taxa_wsf:.2f} km2/ano, media 2011-2015) tem OUTRO vies "
                            "(ano de primeira deteccao, e o WSF termina em 2015), nao o mesmo."
                            if unidade == "Cidade de Tete" else
                            "area nao projetada: a forma urbana e medida sobre a vila de "
                            "Moatize e a populacao sobre o DISTRITO (config/unidades.yaml). "
                            "Razao area/populacao invalida."),
                        "circularidade": (
                            "a base de 2025 e a projecao do INE; projetar sobre ela "
                            "reencena a premissa do INE. Declarado, nao corrigido."),
                    })
    return pd.DataFrame(linhas)


def pressao_varzea(traj: pd.DataFrame) -> pd.DataFrame:
    """Envelope de expansao vs varzea. Entregue como ZONA, nunca como parcela."""
    g = gpd.read_file(CODAB)
    geo = g[g.adm2_pcode == "MZ0501"].to_crs(32736).geometry.iloc[0]
    with rasterio.open(IMG / "urbano_2025_30m_32736.tif") as s:
        urb = s.read(1) > 0
        _m_adm2, _ = mask(s, [geo], crop=False, filled=True, nodata=0)
        dentro_adm2 = np.zeros(urb.shape, bool)
        dentro_adm2[:] = False
        from rasterio.features import geometry_mask
        dentro_adm2 = ~geometry_mask([geo], out_shape=urb.shape, transform=s.transform,
                                     invert=False)
    urb = urb & dentro_adm2      # MESMA geometria da projecao (Cidade de Tete, MZ0501)
    with rasterio.open(IMG / "varzea_30m_32736.tif") as s:
        vz = (s.read(1) > 0) & dentro_adm2
    px = 900 / 1e6
    dist = ndimage.distance_transform_edt(~urb, sampling=(30, 30))
    dist = np.where(dentro_adm2, dist, np.inf)
    vz_total = float(vz.sum() * px)
    t = traj[(traj.unidade == "Cidade de Tete")]
    linhas = []
    for _, r in t.iterrows():
        alvo = r.area_construida_km2_via_intensidade - float(urb.sum() * px)
        if not np.isfinite(alvo) or alvo <= 0:
            continue
        # menor distancia d tal que a area nao-urbana a <=d cubra a area nova projetada
        ds = np.arange(30, 6001, 30)
        acum = np.array([float(((dist > 0) & (dist <= d)).sum() * px) for d in ds])
        i = int(np.searchsorted(acum, alvo))
        d = float(ds[min(i, len(ds) - 1)])
        env = (dist > 0) & (dist <= d)
        vz_sob = float((env & vz).sum() * px)
        linhas.append({
            "unidade": "Cidade de Tete (ADM2 MZ0501 recortado pela AOI)", "cenario": r.cenario,
            "migracao_liquida_pp": r.migracao_liquida_pp, "horizonte": r.horizonte,
            "area_nova_projetada_km2": round(alvo, 2),
            "raio_do_envelope_m": d,
            "varzea_total_km2": round(vz_total, 2),
            "varzea_dentro_do_envelope_km2": round(vz_sob, 2),
            "varzea_fora_do_envelope_km2": round(vz_total - vz_sob, 2),
            "fracao_varzea_sob_pressao": round(vz_sob / vz_total, 3),
            "selo": "modelado",
            "area_agricola_perdida_km2": "NAO DETERMINAVEL",
            "domicilios_afetados": "NAO DETERMINAVEL",
            "motivo_nao_determinavel": (
                "REGRA 6.4 DO DESENHO DISPAROU: a acuracia do usuario de "
                "cultivo_irrigado e 0,556 +- 0,344, abaixo do limiar de 0,60 fixado "
                "antes de ver o dado; cultivo_sequeiro esta reprovado (ADR 0012/0014). "
                "Publicar 'nao determinavel' em vez de estimativa pontual com ressalva "
                "textual e a regra pre-registrada — a ressalva nao impede o numero de "
                "circular, a recusa impede."),
            "leitura_permitida": (
                "ZONA, nao parcela. A varzea FORA do envelope e a area cuja protecao "
                "seria compativel com o crescimento projetado deste cenario. Churn de "
                "31-54% na identidade pixel a pixel (ADR 0013) proibe leitura parcelar. "
                "O envelope e um anel isotropico de distancia, nao um modelo de "
                "localizacao: o logit de §5.6.4 esta bloqueado."),
        })
    return pd.DataFrame(linhas)


def main() -> None:
    traj = trajetorias()
    traj.to_csv(SAIDA / "cenarios_2035_2040.csv", index=False)
    pv = pressao_varzea(traj)
    pv.to_csv(SAIDA / "cenarios_pressao_varzea.csv", index=False)
    (SAIDA / "cenarios.meta.json").write_text(json.dumps({
        "script": "pipeline/03_causal/cenarios.py",
        "regra_de_rotulo": "todo numero e `modelado`; cenario nao e previsao",
        "n_trajetorias": int(len(traj) / 2 / 2),
        "premissas": {
            "delta_por_cenario_pp": DELTA_PP,
            "migracao_liquida_pp": MIGRACAO_PP,
            "tamanho_domicilio": TAM_DOMICILIO,
            "modelo": "geometrico por fase; o coorte-componente NAO foi executado - "
                      "nao ha estrutura etaria por idade simples em nivel A para 2025",
        },
        "proibicoes_respeitadas": [
            "nenhuma epoca GHSL 2025/2030 usada como ancora",
            "nenhuma trajetoria destacada como central",
        ],
    }, indent=2, ensure_ascii=False), encoding="utf-8")
    print(traj[(traj.unidade == "Cidade de Tete") & (traj.migracao_liquida_pp == 0)]
          .reindex(columns=["cenario", "horizonte", "taxa_anual_pct", "populacao",
                            "area_construida_km2_via_intensidade",
                            "area_construida_km2_via_taxa_wsf"]).to_string(index=False))
    print(pv[pv.migracao_liquida_pp == 0].reindex(
        columns=["cenario", "horizonte", "area_nova_projetada_km2", "raio_do_envelope_m",
                 "varzea_dentro_do_envelope_km2", "varzea_fora_do_envelope_km2",
                 "fracao_varzea_sob_pressao"]).to_string(index=False))


if __name__ == "__main__":
    main()
