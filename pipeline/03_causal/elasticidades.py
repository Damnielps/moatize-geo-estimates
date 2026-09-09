"""§5 do desenho — elasticidades DE ASSOCIACAO area-luz e populacao-luz, por fase.

Regra do desenho (§5.1/§5.2): a maioria das celulas NAO e estimavel, e a tabela publica
o motivo em vez de um numero. H4 NAO e reabilitada aqui.
Saida: data/processed/causal/elasticidades_por_fase.csv
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd
import statsmodels.api as sm
import yaml

RAIZ = Path(__file__).resolve().parents[2]
SAIDA = RAIZ / "data" / "processed" / "causal"
SEEDS = yaml.safe_load((RAIZ / "config" / "seeds.yaml").read_text(encoding="utf-8"))

FASES = {
    "linha_de_base_1997_2005": (1997, 2005),
    "implantacao_2005_2011": (2005, 2011),
    "boom_2011_2015": (2011, 2015),
    "bust_2015_2019": (2015, 2019),
    "transicao_2019_2025": (2019, 2025),
}


def main() -> None:
    luz = pd.read_csv(SAIDA / "serie_luzes_anual.csv")
    wsf = pd.read_csv(SAIDA / "serie_wsf_taxa_anual.csv")
    lz = luz[luz.unidade == "tete_aoi"].set_index("ano").soma_radiancia
    wf = wsf[wsf.unidade == "tete_aoi"].set_index("ano").area_primeira_deteccao_km2
    linhas = []
    for fase, (a0, a1) in FASES.items():
        anos = [a for a in lz.index if a0 <= a <= a1 and a in wf.index]
        homog = [a for a in anos if a >= 2013]
        base = {"elasticidade": "area-luz", "fase": fase, "janela": f"{a0}-{a1}",
                "n_pontos": len(anos), "n_pontos_janela_homogenea": len(homog),
                "selo": "estimado", "nivel_fonte": "A"}
        if a0 >= 2015:
            base.update(estimavel=False, motivo_nao_estimavel=(
                "nao existe serie de area utilizavel pos-2015: WSF termina em 2015; "
                "GHSL observado e quinquenal e nao-decrescente; E2025 extrapolado; "
                "serie propria proibida (ADR 0013); par 2015-2020 proibido."))
        elif len(homog) < 3:
            base.update(estimavel=False, motivo_nao_estimavel=(
                f"{len(anos)} pontos na fase, dos quais {len(homog)} na janela homogenea "
                "das luzes (>=2013, EMENDA E4). Fora da janela a serie de luz atravessa a "
                "costura DMSP->VIIRS: a associacao mediria o produto, nao a cidade."))
        else:
            x = np.log(wf.loc[homog].to_numpy(float) + 0.0009)
            y = np.log(lz.loc[homog].to_numpy(float))
            m = sm.OLS(y, sm.add_constant(x)).fit()
            base.update(estimavel=True, eta=round(float(m.params[1]), 3),
                        ic95_inf=round(float(m.conf_int()[1][0]), 3),
                        ic95_sup=round(float(m.conf_int()[1][1]), 3),
                        ressalva=("associacao, nao elasticidade causal; "
                                  f"{len(homog)} pontos; causalidade reversa luz-populacao "
                                  "declarada e NAO resolvida (§5.3)."))
        linhas.append(base)
        linhas.append({
            "elasticidade": "populacao-luz", "fase": fase, "janela": f"{a0}-{a1}",
            "n_pontos": 0, "estimavel": False, "selo": "-", "nivel_fonte": "A",
            "motivo_nao_estimavel": (
                "populacao em nivel A existe so em 2017 (COD-PS, observado) e 2025 "
                "(COD-PS, projecao do INE, MODELADO). Dois pontos, um deles modelado. "
                "1997 e nivel B; 2007 e nivel C. Nao estimavel em fase nenhuma.")})
    df = pd.DataFrame(linhas)
    df["h4_reabilitada"] = False
    df["nota_h4"] = ("H4 exige as celulas area-luz do bust e da transicao, que sao "
                     "exatamente as nao estimaveis. A trajetoria isolada das luzes e "
                     "condicao NECESSARIA E NAO SUFICIENTE. H4 permanece NAO TESTADA.")
    df.to_csv(SAIDA / "elasticidades_por_fase.csv", index=False)
    print(df.reindex(columns=["elasticidade", "fase", "n_pontos", "n_pontos_janela_homogenea",
                              "estimavel", "eta", "ic95_inf", "ic95_sup"]).to_string(index=False))


if __name__ == "__main__":
    main()
