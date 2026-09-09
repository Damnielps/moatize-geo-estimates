"""§4 do desenho — os QUATRO placebos obrigatorios (P1..P4).

Cada um recebe veredito explicito: passa / falha / nao estimavel - motivo.
"nao rodado" nao e resultado admissivel (§4.5).
Saida: data/processed/causal/placebos.csv

ADR 0015 (2026-09-08) / EMENDA 2 do desenho (§12): um ramo de teste RELATIVO
("magnitude >= 50% da de Tete") e INAPLICAVEL quando o coeficiente de referencia
tem IC95 que inclui zero ou foi declarado nao estimavel pelo desenho. Nesse caso o
ramo e VAZIO: nao passa nem falha. Se todos os ramos de uma quebra forem vazios, o
veredito e "nao estimavel - motivo". A regra vale para P1 e P2 (a assimetria de
origem, em que so P2 exigia "IC exclui zero", fica eliminada: P1 passa a exigir o
mesmo do coeficiente do proprio placebo).
O veredito anterior a ADR 0015 e PRESERVADO em coluna propria
(`veredito_pre_adr0015`) e nunca sobrescrito.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import rasterio

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _its_core import ajusta_its

RAIZ = Path(__file__).resolve().parents[2]
SAIDA = RAIZ / "data" / "processed" / "causal"
C_WSF = 0.0009
CONTROLES = ["chimoio", "quelimane", "lichinga", "xaixai", "inhambane"]
# Anos falsos FIXADOS no pre-registro (§4.2). Sem discricionariedade posterior.
ANOS_FALSOS = {2005: 1999, 2011: 2008, 2016: 2014, 2022: 2019}
# ADR 0013 §3 — radiometria de paisagem nos 6 anos-ancora (fracao da AOI com NDVI seca >= 0,30)
NDVI_PAISAGEM = {2000: 10.8, 2005: 11.1, 2010: 76.7, 2015: 90.9, 2020: 27.6, 2025: 6.1}

# ADR 0015. Ramos declarados VAZIOS pelo desenho, independentemente do IC estimado.
# Chave: (quebra, coeficiente) -> motivo. Nao ha discricionariedade aqui: as duas
# entradas vem de clausulas escritas ANTES do resultado (E8) ou da decisao 2 do ADR.
RAMOS_VAZIOS_POR_DESENHO = {
    (2022, "b3"): ("EMENDA E8 (escrita antes de estimar os placebos): a inclinacao "
                   "pos-2022 e NAO ESTIMAVEL com 4 pontos pos. Aplicar E8 aqui e "
                   "execucao de clausula anterior, nao emenda nova."),
    (2022, "b2"): ("ADR 0015 decisoes 2 e 4: o ramo b2 compara a soma de luz sobre um "
                   "retangulo que CONTEM a mina de Moatize contra retangulos de controle "
                   "sem mina. A queda de 2022 esta fora da Cidade de Tete (ADM2 +0,7%; "
                   "resto do retangulo -12,7%). Geometrias nao comparaveis enquanto a "
                   "decomposicao industrial/urbano/resto de §2.3 nao sustentar a leitura."),
}


def _ref(alvo) -> dict:
    """Coeficientes de REFERENCIA (Tete real) com IC95 — ADR 0015 exige o IC, nao so o ponto."""
    return {
        "b2_real_tete": float(alvo.b2_nivel),
        "b3_real_tete": float(alvo.b3_inclinacao),
        "b2_real_ic95_inf": float(alvo.b2_ic95_inf),
        "b2_real_ic95_sup": float(alvo.b2_ic95_sup),
        "b3_real_ic95_inf": float(alvo.b3_ic95_inf),
        "b3_real_ic95_sup": float(alvo.b3_ic95_sup),
        "real_estimavel": bool(alvo.estimavel),
    }


def estado_do_ramo(quebra, coef: str, inf: float, sup: float) -> tuple[bool, str]:
    """ADR 0015 regra 1. Devolve (aplicavel, motivo).

    O ramo relativo "|b| >= 50% de |b_ref|" so e aplicavel se b_ref for distinguivel
    de zero. Com IC95 que inclui zero o denominador colapsa e QUALQUER valor satisfaz
    o teste: e ramo vazio, nao ramo que passa nem ramo que falha.
    """
    try:
        q = int(quebra)
    except (TypeError, ValueError):
        q = quebra
    if (q, coef) in RAMOS_VAZIOS_POR_DESENHO:
        return False, f"vazio (desenho): {RAMOS_VAZIOS_POR_DESENHO[(q, coef)]}"
    if not np.isfinite(inf) or not np.isfinite(sup):
        return False, f"vazio: {coef} de referencia nao estimado (IC ausente)"
    if inf * sup <= 0:
        return False, (f"vazio: IC95 do {coef} de referencia de Tete "
                       f"[{inf:.4f}; {sup:.4f}] inclui zero — o teste relativo "
                       f"'>= 50% da magnitude' tem denominador que colapsa")
    return True, "aplicavel"


def _wsf(wsf: pd.DataFrame, uni: str, ini: int) -> pd.DataFrame:
    return wsf[(wsf.unidade == uni) & (wsf.ano >= ini) & (wsf.ano <= 2015)].sort_values("ano")


def p1_espacial(luz, wsf, real):
    """Trata cada controle como se fosse a tratada e reestima a MESMA quebra."""
    out = []
    for t0, ini in ((2005, 1993), (2011, 1996)):
        alvo = real[(real.rotulo == f"S_WSF_taxa|tete_aoi|{t0}")
                    & (real.variante == "principal_log_HAC")].iloc[0]
        for uni in CONTROLES:
            s = _wsf(wsf, uni, ini)
            r = ajusta_its(s.ano, s.area_primeira_deteccao_km2, t0, c=C_WSF,
                           rotulo=f"P1|S_WSF_taxa|{uni}|{t0}")
            r.update(placebo="P1_espacial", serie="S_WSF_taxa", unidade=uni,
                     quebra=t0, **_ref(alvo))
            out.append(r)
    for t0 in (2016, 2022):
        alvo = real[(real.rotulo == f"S_HARM_soma|tete_aoi|{t0}")
                    & (real.variante == "principal_log_HAC")].iloc[0]
        for uni in CONTROLES:
            s = luz[(luz.unidade == uni) & (luz.ano >= 2013)].sort_values("ano")
            r = ajusta_its(s.ano, s.soma_radiancia, t0, rotulo=f"P1|S_HARM_soma|{uni}|{t0}")
            r.update(placebo="P1_espacial", serie="S_HARM_soma", unidade=uni,
                     quebra=t0, **_ref(alvo))
            out.append(r)
    return out


def p2_temporal(luz, wsf, real):
    """Quebra falsa dentro do pre-periodo: 1999, 2008, 2014, 2019."""
    out = []
    for t0, ini in ((2005, 1993), (2011, 1996)):
        tf = ANOS_FALSOS[t0]
        alvo = real[(real.rotulo == f"S_WSF_taxa|tete_aoi|{t0}")
                    & (real.variante == "principal_log_HAC")].iloc[0]
        s = _wsf(wsf, "tete_aoi", ini)
        # janela do placebo: mesma janela, quebra deslocada para o pre
        r = ajusta_its(s.ano, s.area_primeira_deteccao_km2, tf, c=C_WSF,
                       rotulo=f"P2|S_WSF_taxa|tete_aoi|falsa{tf}(real{t0})")
        r.update(placebo="P2_temporal", serie="S_WSF_taxa", unidade="tete_aoi",
                 quebra=t0, ano_falso=tf, **_ref(alvo))
        out.append(r)
    for t0 in (2016, 2022):
        tf = ANOS_FALSOS[t0]
        alvo = real[(real.rotulo == f"S_HARM_soma|tete_aoi|{t0}")
                    & (real.variante == "principal_log_HAC")].iloc[0]
        s = luz[(luz.unidade == "tete_aoi") & (luz.ano >= 2013)].sort_values("ano")
        r = ajusta_its(s.ano, s.soma_radiancia, tf,
                       rotulo=f"P2|S_HARM_soma|tete_aoi|falsa{tf}(real{t0})")
        r.update(placebo="P2_temporal", serie="S_HARM_soma", unidade="tete_aoi",
                 quebra=t0, ano_falso=tf, **_ref(alvo))
        if tf == 2014:
            r["ressalva"] = ("EMENDA E4: com janela iniciando em 2013, a quebra falsa de "
                             "2014 tem 1 ponto pre. Nao estimavel como quebra.")
        out.append(r)
    return out


def p3_capacidade():
    """ADR 0008 §5. Capacidade de observacao vs desfecho."""
    out = []
    # (a) serie propria: 6 anos-ancora, mediana de observacoes validas por pixel
    med = {}
    for ano in (2000, 2005, 2010, 2015, 2020, 2025):
        f = RAIZ / "data" / "interim" / f"composto_{ano}_30m_32736_nobs.tif"
        with rasterio.open(f) as s:
            a = s.read(1).astype("float64")
            a = a[np.isfinite(a) & (a > 0)]
            med[ano] = float(np.median(a)) if a.size else np.nan
    dec = pd.read_csv(SAIDA / "decomposicao_permanencia_urbano.csv")
    dec = dec[dec.ano.isin(med)].sort_values("ano")
    cap = np.array([med[a] for a in dec.ano])
    y = dec.estoque_sustentado_pelo_ano_km2.to_numpy(dtype=float)
    rho = float(np.corrcoef(cap, y)[0, 1])
    out.append({
        "placebo": "P3_capacidade", "serie": "serie propria (S_SUST)", "unidade": "tete_aoi",
        "quebra": "todas", "estimavel": False,
        "motivo_nao_estimavel": ("6 anos-ancora: nao se ajusta modelo segmentado de 4 "
                                 "parametros. Reportado como serie pareada (§1.3 item 5)."),
        "correlacao_capacidade_desfecho": round(rho, 4),
        "mediana_nobs_por_ano": json.dumps({k: round(v, 1) for k, v in med.items()}),
        "limiar_pre_registrado": "|rho| > 0,8",
        "veredito": "FALHA (descritivo)" if abs(rho) > 0.8 else "passa (descritivo)",
        "o_que_a_falha_invalida": ("o DESFECHO da serie propria — que ja esta proibido como "
                                   "desfecho causal (ADR 0013). Nao transfere veredito as "
                                   "series usadas de fato (S_WSF_taxa, S_HARM_soma)."),
    })
    # (b) desfechos efetivamente usados
    for serie, motivo in (
        ("S_HARM_soma", "O produto Chen/Yu e um composto anual harmonizado; os recortes "
                        "espelhados nao trazem a contagem de noites validas por pixel, e "
                        "ela nao e derivavel do raster de radiancia. NAO ESTIMAVEL."),
        ("S_WSF_taxa", "O WSF Evolution nao publica, nos tiles espelhados, a contagem de "
                       "cenas Landsat por ano usada na deteccao. A capacidade de observacao "
                       "do Landsat cresce no periodo e e uma explicacao alternativa viva "
                       "para a taxa de primeira deteccao. NAO ESTIMAVEL — e e um limite real, "
                       "nao formalidade."),
    ):
        out.append({"placebo": "P3_capacidade", "serie": serie, "unidade": "tete_aoi",
                    "quebra": "todas", "estimavel": False,
                    "motivo_nao_estimavel": motivo, "veredito": "nao estimavel"})
    return out


def p4_radiometria():
    """Radiometria de paisagem (ADR 0013 §3). Serie anual nao construida -> descritivo."""
    anos = sorted(NDVI_PAISAGEM)
    v = np.array([NDVI_PAISAGEM[a] for a in anos])
    sinal_ndvi = np.sign(np.diff(v)).tolist()
    dec = pd.read_csv(SAIDA / "decomposicao_permanencia_urbano.csv").sort_values("ano")
    sinal_y = np.sign(np.diff(dec.estoque_sustentado_pelo_ano_km2.to_numpy(float))).tolist()
    coincide = sum(int(a == b) for a, b in zip(sinal_ndvi, sinal_y, strict=False))
    return [{
        "placebo": "P4_radiometria_paisagem", "serie": "fracao AOI NDVI(seca)>=0,30",
        "unidade": "tete_aoi", "quebra": "todas", "estimavel": False,
        "motivo_nao_estimavel": ("serie ANUAL de NDVI de paisagem 1997-2025 NAO foi "
                                 "construida (pre-requisito (iii) do §9, ainda nao "
                                 "satisfeito — EMENDA E1). Com 6 pontos o teste e descritivo, "
                                 "conforme a alternativa ja pre-registrada em §4.4."),
        "valores_por_ano_pct": json.dumps(NDVI_PAISAGEM),
        "sinais_ndvi": json.dumps(sinal_ndvi), "sinais_desfecho_S_SUST": json.dumps(sinal_y),
        "n_sinais_coincidentes_de_5": coincide,
        "veredito": ("FALHA (descritivo)" if coincide >= 4 else
                     "inconclusivo (descritivo)" if coincide == 3 else "passa (descritivo)"),
        "o_que_a_falha_invalida": ("a MEDICAO da serie propria e, por tabela, a suficiencia "
                                   "de ADR 0014. Nao se aplica a S_WSF_taxa nem a "
                                   "S_HARM_soma, que nao derivam da classificacao propria."),
    }]


def main() -> None:
    luz = pd.read_csv(SAIDA / "serie_luzes_anual.csv")
    wsf = pd.read_csv(SAIDA / "serie_wsf_taxa_anual.csv")
    real = pd.read_csv(SAIDA / "its_quebras.csv")
    linhas = p1_espacial(luz, wsf, real) + p2_temporal(luz, wsf, real)
    df = pd.DataFrame(linhas)

    # Vereditos de P1 e P2. DUAS colunas, lado a lado e nunca sobrescritas:
    #   `veredito_pre_adr0015` = regra pre-registrada literal (§4.1/§4.2), como rodou em 3-10
    #   `veredito`             = regra emendada por ADR 0015 / EMENDA 2 (ramo vazio)
    def _flags(r):
        s2 = np.sign(r["b2_nivel"]) == np.sign(r["b2_real_tete"])
        m2 = abs(r["b2_nivel"]) >= 0.5 * abs(r["b2_real_tete"])
        z2 = r["b2_ic95_inf"] * r["b2_ic95_sup"] > 0
        s3 = np.sign(r["b3_inclinacao"]) == np.sign(r["b3_real_tete"])
        m3 = abs(r["b3_inclinacao"]) >= 0.5 * abs(r["b3_real_tete"])
        z3 = r["b3_ic95_inf"] * r["b3_ic95_sup"] > 0
        return (s2 and m2), z2, (s3 and m3), z3

    def veredito_pre(r):
        """Regra literal anterior a ADR 0015. Preservada para auditoria, nao para decidir."""
        if not r.get("estimavel", False):
            return "nao estimavel"
        rep2, z2, rep3, z3 = _flags(r)
        if r["placebo"] == "P2_temporal":
            return "FALHA" if ((rep2 and z2) or (rep3 and z3)) else "passa"
        return "replica" if (rep2 or rep3) else "nao replica"

    def veredito_adr0015(r):
        """ADR 0015: ramo vazio nao decide; P1 passa a exigir o mesmo IC que P2 exigia."""
        ap2, mot2 = estado_do_ramo(r["quebra"], "b2",
                                   r.get("b2_real_ic95_inf", np.nan),
                                   r.get("b2_real_ic95_sup", np.nan))
        ap3, mot3 = estado_do_ramo(r["quebra"], "b3",
                                   r.get("b3_real_ic95_inf", np.nan),
                                   r.get("b3_real_ic95_sup", np.nan))
        if not r.get("estimavel", False):
            return "nao estimavel", mot2, mot3, r.get("motivo_nao_estimavel", "")
        if not ap2 and not ap3:
            motivo = f"ambos os ramos vazios (ADR 0015). b2: {mot2} | b3: {mot3}"
            return "nao estimavel", mot2, mot3, motivo
        rep2, z2, rep3, z3 = _flags(r)
        disp = (ap2 and rep2 and z2) or (ap3 and rep3 and z3)
        if r["placebo"] == "P2_temporal":
            return ("FALHA" if disp else "passa"), mot2, mot3, ""
        return ("replica" if disp else "nao replica"), mot2, mot3, ""

    df["veredito_pre_adr0015"] = df.apply(veredito_pre, axis=1)
    novo = df.apply(veredito_adr0015, axis=1, result_type="expand")
    df["veredito"] = novo[0]
    df["ramo_b2_estado"] = novo[1]
    df["ramo_b3_estado"] = novo[2]
    df["motivo_nao_estimavel"] = df.get(
        "motivo_nao_estimavel", pd.Series([""] * len(df))).fillna("").astype(str)
    df.loc[novo[3].astype(bool), "motivo_nao_estimavel"] = novo[3][novo[3].astype(bool)]

    # P1 falha se >=2 controles replicam a quebra (mesmo sinal, >=50% da magnitude)
    p1v = []
    for (t0, serie), g in df[df.placebo == "P1_espacial"].groupby(["quebra", "serie"]):
        n_pre = int((g.veredito_pre_adr0015 == "replica").sum())
        n = int((g.veredito == "replica").sum())
        vazios = (g.veredito == "nao estimavel").all()
        p1v.append({"placebo": "P1_espacial", "serie": serie, "unidade": "AGREGADO",
                    "quebra": t0, "n_controles_que_replicam": n, "n_controles": len(g),
                    "n_controles_que_replicam_pre_adr0015": n_pre,
                    "veredito_pre_adr0015": "FALHA" if n_pre >= 2 else "passa",
                    "veredito": ("nao estimavel" if vazios else
                                 "FALHA" if n >= 2 else "passa"),
                    "ramo_b2_estado": g.ramo_b2_estado.iloc[0],
                    "ramo_b3_estado": g.ramo_b3_estado.iloc[0],
                    "motivo_nao_estimavel": (g.motivo_nao_estimavel.iloc[0]
                                             if vazios else ""),
                    "regra": ("ADR 0015: falha se >=2 controles com quebra de mesmo sinal, "
                              ">=50% da magnitude de Tete e IC95 proprio que exclui zero, "
                              "contados APENAS em ramos aplicaveis (coeficiente de "
                              "referencia com IC95 que exclui zero). Todos os ramos "
                              "vazios => nao estimavel.")})
    p2v = []
    for (t0, serie), g in df[df.placebo == "P2_temporal"].groupby(["quebra", "serie"]):
        p2v.append({"placebo": "P2_temporal", "serie": serie, "unidade": "AGREGADO",
                    "quebra": t0, "ano_falso": ANOS_FALSOS[t0],
                    "veredito_pre_adr0015": g.veredito_pre_adr0015.iloc[0],
                    "veredito": g.veredito.iloc[0],
                    "ramo_b2_estado": g.ramo_b2_estado.iloc[0],
                    "ramo_b3_estado": g.ramo_b3_estado.iloc[0],
                    "motivo_nao_estimavel": g.motivo_nao_estimavel.iloc[0],
                    "regra": ("ADR 0015: falha se o placebo produz b2 ou b3 de mesmo sinal, "
                              ">=50% da magnitude real, com IC95 que exclui zero, em ramo "
                              "aplicavel. Todos os ramos vazios => nao estimavel.")})
    # Rastro explicito da mudanca. Um afrouxamento (FALHA -> passa) NUNCA e lido como
    # reabilitacao: e consequencia de o proprio coeficiente de referencia de Tete ser
    # indistinguivel de zero. Marcado na linha para que ninguem o leia como resultado.
    def _mudanca(r):
        a, b = r.get("veredito_pre_adr0015"), r.get("veredito")
        if not isinstance(a, str) or not isinstance(b, str) or a == b:
            return "inalterado"
        if b == "nao estimavel":
            return f"{a} -> nao estimavel (ramo vazio, ADR 0015)"
        if a in ("FALHA", "replica") and b in ("passa", "nao replica"):
            return (f"{a} -> {b} AFROUXAMENTO. NAO reabilita nada: o ramo que disparava "
                    "usava um coeficiente de referencia de Tete cujo IC95 inclui zero. "
                    "O veredito pre-ADR 0015 fica na coluna ao lado e continua publicavel.")
        return f"{a} -> {b}"

    for _d in (df,):
        _d["mudanca_apos_adr0015"] = _d.apply(_mudanca, axis=1)
    for _l in (p1v, p2v):
        for _r in _l:
            _r["mudanca_apos_adr0015"] = _mudanca(_r)

    tudo = pd.concat([df, pd.DataFrame(p1v), pd.DataFrame(p2v),
                      pd.DataFrame(p3_capacidade()), pd.DataFrame(p4_radiometria())],
                     ignore_index=True)
    tudo.to_csv(SAIDA / "placebos.csv", index=False)
    print(tudo[tudo.unidade.isin(["AGREGADO", "tete_aoi"])]
          .reindex(columns=["placebo", "serie", "quebra", "ano_falso",
                            "veredito_pre_adr0015", "veredito",
                            "mudanca_apos_adr0015",
                            "n_controles_que_replicam", "correlacao_capacidade_desfecho",
                            "n_sinais_coincidentes_de_5"]).to_string(index=False))


if __name__ == "__main__":
    main()
