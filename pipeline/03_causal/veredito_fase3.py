"""Consolida o veredito da Fase 3: placebos, criterios F1-F7 e o que ficou nao estimavel.

Regra do desenho §3.4: se F1-F7 dispararem, o resultado publicado e "o contrafactual nao
se sustenta com este pool de doadores" — nao uma reespecificacao buscada ate passar.
Saida: data/processed/causal/veredito_fase3.csv
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd

SAIDA = Path(__file__).resolve().parents[2] / "data" / "processed" / "causal"


def main() -> None:
    pl = pd.read_csv(SAIDA / "placebos.csv")
    ef = pd.read_csv(SAIDA / "did_efeitos.csv")
    tp = pd.read_csv(SAIDA / "tendencia_paralela_pre2005.csv")
    linhas = []
    ag = pl[pl.unidade == "AGREGADO"]
    for _, r in ag.iterrows():
        linhas.append({"bloco": "placebo", "id": r.placebo, "serie": r.serie,
                       "quebra": r.quebra, "veredito": r.veredito,
                       "veredito_pre_adr0015": r.get("veredito_pre_adr0015"),
                       "mudanca_apos_adr0015": r.get("mudanca_apos_adr0015"),
                       "detalhe": r.get("regra")})
    for _, r in pl[pl.placebo.isin(["P3_capacidade", "P4_radiometria_paisagem"])].iterrows():
        linhas.append({"bloco": "placebo", "id": r.placebo, "serie": r.serie,
                       "quebra": r.quebra, "veredito": r.veredito,
                       "detalhe": r.get("motivo_nao_estimavel")})
    for _, r in ef.iterrows():
        disp = r.get("criterios_F_disparados")
        linhas.append({
            "bloco": "criterio_F", "id": f"{r.painel}|{r.quebra}", "serie": r.painel,
            "quebra": r.quebra,
            "veredito": ("CONTRAFACTUAL NAO SUSTENTADO" if isinstance(disp, str) and disp
                         else "nenhum criterio F disparou"),
            "detalhe": disp if isinstance(disp, str) else r.get("motivo_nao_estimavel")})
    for _, r in tp.iterrows():
        v = r.get("veredito_F1") if r.teste == "T1" else r.get("veredito_F2")
        linhas.append({"bloco": "tendencia_paralela", "id": f"{r.painel}|{r.teste}",
                       "serie": r.painel, "quebra": "pre-tratamento",
                       "veredito": v if isinstance(v, str) else "nao estimavel",
                       "detalhe": r.get("motivo_nao_estimavel") or r.get("nota")})
    for id_, det in [
        ("area 2016/2022", "sem serie de area utilizavel pos-2015"),
        ("luz 2005/2011", "EMENDA E4 item 4: sem DMSP em nivel A"),
        ("elasticidade populacao-luz", "populacao em nivel A so em 2017 e 2025 (2025 modelado)"),
        ("elasticidade area-luz bust/transicao", "sem serie de area pos-2015"),
        ("H4", "NAO TESTADA e nao reabilitada"),
        ("H5 e logit §5.6.4", "bloqueados (churn 31-54% e cultivo_sequeiro reprovado)"),
        ("H6", "rebaixada e mantida rebaixada"),
        ("area agricola perdida / domicilios afetados",
         "regra 6.4 DISPAROU: acuracia do usuario de cultivo_irrigado 0,556 < 0,60"),
        ("coorte-componente", "nao executado: sem estrutura etaria em nivel A para 2025"),
        ("P4 como teste de quebra", "serie anual de NDVI de paisagem nao construida"),
    ]:
        linhas.append({"bloco": "nao_estimavel", "id": id_, "serie": "-", "quebra": "-",
                       "veredito": "nao estimavel / nao determinavel", "detalhe": det})
    linhas.append({"bloco": "inferencia", "id": "piso de p por permutacao", "serie": "-",
                   "quebra": "-", "veredito": "1/6 = 0,167",
                   "detalhe": ("1 tratado + 5 doadores. Nenhum resultado desta fase atinge "
                               "significancia convencional. Aritmetica do pool, nao fraqueza "
                               "do efeito.")})
    df = pd.DataFrame(linhas)
    df.to_csv(SAIDA / "veredito_fase3.csv", index=False)
    print(df[df.bloco.isin(["placebo", "criterio_F", "tendencia_paralela"])]
          .reindex(columns=["bloco", "id", "serie", "quebra", "veredito"]).to_string(index=False))


if __name__ == "__main__":
    main()
