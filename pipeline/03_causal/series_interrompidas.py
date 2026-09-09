"""§5.4 — Séries interrompidas nas quatro quebras, conforme o desenho EMENDADO.

Quadro vigente (docs/DESENHO_FASE3.md §11, E8):
  2005, 2011 -> S_WSF_taxa (1993-2015)
  2016, 2022 -> S_HARM_soma (janela homogenea 2013-2025)
  2016/2022 sobre area  : NAO estimaveis
  2005/2011 sobre luz   : NAO estimaveis (E4 item 4)

Saida: data/processed/causal/its_quebras.csv
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _its_core import ajusta_donut, ajusta_its, para_df, quasi_poisson

RAIZ = Path(__file__).resolve().parents[2]
SAIDA = RAIZ / "data" / "processed" / "causal"
C_WSF = 0.0009  # 1 pixel de 30 m em km2 — fixado no desenho, nao recalibrado
AREA_RECORTE_KM2 = {"tete_aoi": 2493.8}


def main() -> None:
    luz = pd.read_csv(SAIDA / "serie_luzes_anual.csv")
    wsf = pd.read_csv(SAIDA / "serie_wsf_taxa_anual.csv")
    linhas = []

    # --- Painel A: WSF taxa, Tete, quebras 2005 e 2011 ---
    w = wsf[(wsf.unidade == "tete_aoi")].sort_values("ano")
    for t0, ini in ((2005, 1993), (2011, 1996)):
        sub = w[(w.ano >= ini) & (w.ano <= 2015)]
        base = ajusta_its(
            sub.ano, sub.area_primeira_deteccao_km2, t0, c=C_WSF, log=True,
            rotulo=f"S_WSF_taxa|tete_aoi|{t0}",
        )
        base["serie"] = "S_WSF_taxa"
        base["unidade"] = "tete_aoi"
        base["variante"] = "principal_log_HAC"
        linhas.append(base)
        d = ajusta_donut(
            sub.ano, sub.area_primeira_deteccao_km2, t0, c=C_WSF, log=True,
            rotulo=f"S_WSF_taxa|tete_aoi|{t0}",
        )
        d.update(serie="S_WSF_taxa", unidade="tete_aoi")
        linhas.append(d)
        q = quasi_poisson(
            sub.ano, sub.n_pixels, AREA_RECORTE_KM2["tete_aoi"], t0,
            rotulo=f"S_WSF_taxa|tete_aoi|{t0}",
        )
        q.update(serie="S_WSF_taxa", unidade="tete_aoi")
        linhas.append(q)

    # --- Painel B: luzes Chen/Yu, Tete, quebras 2016 e 2022, janela homogenea ---
    lz = luz[(luz.unidade == "tete_aoi") & (luz.ano >= 2013)].sort_values("ano")
    for t0 in (2016, 2022):
        base = ajusta_its(
            lz.ano, lz.soma_radiancia, t0, c=0.0, log=True,
            rotulo=f"S_HARM_soma|tete_aoi|{t0}",
        )
        base.update(serie="S_HARM_soma", unidade="tete_aoi",
                    variante="principal_log_HAC")
        if t0 == 2016:
            base["ressalva"] = (
                "EMENDA E4: pre-janela de 3 pontos (2013-2015). b1 e aritmetica de "
                "tres observacoes, nao tendencia. Quebra lida so como NIVEL."
            )
        else:
            base["ressalva"] = (
                "EMENDA E5: quebra de produto nao descartada, com evidencia "
                "direcional contra ela (soma sobe 2023-2025 enquanto o maximo cai). "
                "Inclinacao pos com 4 pontos: nao estimavel como tendencia."
            )
        linhas.append(base)
        d = ajusta_donut(lz.ano, lz.soma_radiancia, t0, c=0.0, log=True,
                         rotulo=f"S_HARM_soma|tete_aoi|{t0}")
        d.update(serie="S_HARM_soma", unidade="tete_aoi")
        linhas.append(d)

    # --- Celulas declaradas NAO ESTIMAVEIS (entram na tabela, nao no silencio) ---
    for t0 in (2016, 2022):
        linhas.append({
            "rotulo": f"AREA|tete_aoi|{t0}", "serie": "area construida", "t0": t0,
            "unidade": "tete_aoi", "variante": "principal", "estimavel": False,
            "motivo_nao_estimavel": (
                "WSF Evolution termina em 2015; GHSL observado termina em 2020, "
                "quinquenal e nao-decrescente; E2025 extrapolado; serie propria "
                "proibida (ADR 0013); par 2015-2020 proibido. Sem substituto."
            )})
    for t0 in (2005, 2011):
        linhas.append({
            "rotulo": f"S_HARM_soma|tete_aoi|{t0}", "serie": "S_HARM_soma", "t0": t0,
            "unidade": "tete_aoi", "variante": "principal", "estimavel": False,
            "motivo_nao_estimavel": (
                "EMENDA E4 item 4: sem DMSP em nivel A, o trecho pre-2013 do produto "
                "Chen/Yu tem 6 pontos irregulares (2000,2005,2008,2010,2011,2012) do "
                "lado heterogeneo da costura. Sem corroboracao de luz para 2005/2011."
            )})

    df = para_df(linhas)
    df.insert(0, "selo", "observado (desfecho) / estimado (coeficiente)")
    df.to_csv(SAIDA / "its_quebras.csv", index=False)
    (SAIDA / "its_quebras.meta.json").write_text(json.dumps({
        "script": "pipeline/03_causal/series_interrompidas.py",
        "desenho": "docs/DESENHO_FASE3.md §2 + EMENDA 1 (§11, E4/E5/E8)",
        "aviso_obrigatorio": (
            "T<=23: HAC sub-cobre. Os IC sao PISO de incerteza, nao teto. "
            "Nenhum resultado aqui e apresentado como significativo sem esta frase."
        ),
        "fonte_luz": "Chen/Yu 2021 (10.5194/essd-13-889-2021), CC0 — NAO Li et al. 2020",
    }, indent=2, ensure_ascii=False), encoding="utf-8")
    cols = ["rotulo", "variante", "estimavel", "b2_nivel", "b2_ic95_inf", "b2_ic95_sup",
            "b3_inclinacao", "b3_ic95_inf", "b3_ic95_sup", "troca_sinal_hac_ar1"]
    print(df.reindex(columns=cols).to_string(index=False))


if __name__ == "__main__":
    main()
