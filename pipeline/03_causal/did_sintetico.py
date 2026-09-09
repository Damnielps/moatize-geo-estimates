"""§3 do desenho — DiD, controle sintetico, tendencia paralela (T1/T2/T3) e F1-F7.

Pool honesto: 1 tratado (Tete) + 5 doadores. Piso de p por permutacao = 1/6 ~ 0,167 (§3.6).
Nenhum resultado aqui pode atingir significancia convencional; e aritmetica do pool.
Saidas: did_sintetico_pesos.csv, tendencia_paralela_pre2005.csv, did_efeitos.csv
"""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd
import statsmodels.api as sm
import yaml
from scipy.optimize import minimize

RAIZ = Path(__file__).resolve().parents[2]
SAIDA = RAIZ / "data" / "processed" / "causal"
SEEDS = yaml.safe_load((RAIZ / "config" / "seeds.yaml").read_text(encoding="utf-8"))
SEED_SCM = SEEDS["controle_sintetico"]["seed"]
SEED_BOOT = SEEDS["bootstrap"]["seed"]
N_BOOT = SEEDS["bootstrap"]["n_reamostragens"]
TRAT = "tete_aoi"
CONTROLES = ["chimoio", "quelimane", "lichinga", "xaixai", "inhambane"]

# painel -> (serie, ano_inicial, quebras)
PAINEIS = {
    "A_area_WSF": {"ini": 1993, "fim": 2015, "quebras": [2005, 2011]},
    "B_luz_HARM": {"ini": 2013, "fim": 2025, "quebras": [2016, 2022]},
}


def carrega() -> dict:
    luz = pd.read_csv(SAIDA / "serie_luzes_anual.csv")
    wsf = pd.read_csv(SAIDA / "serie_wsf_taxa_anual.csv")
    a = wsf.pivot(index="ano", columns="unidade", values="area_primeira_deteccao_km2")
    b = luz.pivot(index="ano", columns="unidade", values="soma_radiancia")
    return {"A_area_WSF": a.loc[1993:2015], "B_luz_HARM": b.loc[2013:2025]}


def normaliza(m: pd.DataFrame, pre: np.ndarray) -> pd.DataFrame:
    """Divide cada serie pela sua media pre-tratamento (§3.2.3)."""
    return m / m.loc[pre].mean()


def scm(y_trat, y_doa, mask_pre) -> np.ndarray:
    """Pesos ADH: nao-negativos, soma 1, sem extrapolacao. Multistart determinista."""
    x = y_doa[mask_pre]
    yt = y_trat[mask_pre]
    n = x.shape[1]
    rng = np.random.default_rng(SEED_SCM)
    cons = ({"type": "eq", "fun": lambda w: w.sum() - 1.0},)
    lim = [(0.0, 1.0)] * n

    def perda(w):
        return float(np.mean((yt - x @ w) ** 2))

    melhor, melhor_v = None, np.inf
    partidas = [np.full(n, 1 / n)] + [rng.dirichlet(np.ones(n)) for _ in range(19)]
    for w0 in partidas:
        r = minimize(perda, w0, method="SLSQP", bounds=lim, constraints=cons,
                     options={"maxiter": 500, "ftol": 1e-12})
        if r.success and r.fun < melhor_v:
            melhor, melhor_v = r.x, r.fun
    w = np.clip(melhor, 0, None)
    return w / w.sum()


def rmspe(a, b, m):
    return float(np.sqrt(np.mean((a[m] - b[m]) ** 2)))


def wild_cluster_boot(y, x, grupos, idx_teste) -> float:
    """Wild cluster bootstrap (Rademacher) da F conjunta. 6 clusters: assintotico invalido."""
    rng = np.random.default_rng(SEED_BOOT)
    livre = [i for i in range(x.shape[1]) if i not in idx_teste]
    m_full = sm.OLS(y, x).fit()
    r_full = np.array([[1.0 if j == i else 0.0 for j in range(x.shape[1])] for i in idx_teste])
    f_obs = float(m_full.f_test(r_full).fvalue)
    m_res = sm.OLS(y, x[:, livre]).fit()
    yhat, resid = m_res.fittedvalues, m_res.resid
    gs = np.unique(grupos)
    conta = 0
    for _ in range(N_BOOT):
        sinais = {g: rng.choice([-1.0, 1.0]) for g in gs}
        yb = yhat + resid * np.array([sinais[g] for g in grupos])
        try:
            fb = float(sm.OLS(yb, x).fit().f_test(r_full).fvalue)
        except Exception:
            continue
        conta += int(fb >= f_obs)
    return (conta + 1) / (N_BOOT + 1), f_obs


def tendencia_paralela(m: pd.DataFrame, pre_fim: int, base: int, painel: str) -> list:
    """T1 (interacoes unidade x t) e T2 (event study com leads)."""
    pre = m.loc[m.index <= pre_fim]
    unidades = [TRAT, *CONTROLES]
    linhas = []
    if len(pre) < 4:
        return [{"painel": painel, "teste": "T1", "estimavel": False,
                 "motivo_nao_estimavel": f"pre-janela de {len(pre)} pontos; "
                 "interacoes unidade x t nao identificaveis"},
                {"painel": painel, "teste": "T2", "estimavel": False,
                 "motivo_nao_estimavel": f"pre-janela de {len(pre)} pontos"}]
    dados = []
    for u in unidades:
        for ano, v in pre[u].items():
            dados.append({"unidade": u, "ano": int(ano),
                          "y": np.log(max(v, 1e-6) + (0.0009 if painel.startswith("A") else 0.0))})
    d = pd.DataFrame(dados)
    du = pd.get_dummies(d.unidade, prefix="u", drop_first=True).astype(float)
    da = pd.get_dummies(d.ano, prefix="a", drop_first=True).astype(float)
    tt = (d.ano - d.ano.min()).to_numpy(float)
    inter = du.mul(tt, axis=0).add_prefix("t_")
    x = pd.concat([pd.Series(1.0, index=d.index, name="const"), du, da, inter], axis=1)
    idx = [x.columns.get_loc(c) for c in inter.columns]
    p, f_obs = wild_cluster_boot(d.y.to_numpy(float), x.to_numpy(float),
                                 d.unidade.to_numpy(), idx)
    linhas.append({"painel": painel, "teste": "T1", "estimavel": True, "F": f_obs,
                   "p_wild_cluster_bootstrap": p, "n_clusters": 6,
                   "veredito_F1": "DISPARA" if p < 0.10 else "nao dispara",
                   "nota": "6 clusters: assintotico invalido; wild cluster bootstrap "
                           "(Rademacher), seed 97531, 1000 reamostragens. Um F que nao "
                           "rejeita nao e evidencia de paralelismo."})
    # T2 event study: y ~ unidade + ano + tratado x ano (leads), base = `base`
    d["trat"] = (d.unidade == TRAT).astype(float)
    anos = sorted(a for a in d.ano.unique() if a != base)
    leads = pd.DataFrame({f"lead_{a}": d.trat * (d.ano == a) for a in anos}).astype(float)
    x2 = pd.concat([pd.Series(1.0, index=d.index, name="const"), du, da, leads], axis=1)
    m2 = sm.OLS(d.y.to_numpy(float), x2.to_numpy(float)).fit(
        cov_type="cluster", cov_kwds={"groups": pd.factorize(d.unidade)[0]})
    ci = m2.conf_int()
    exclui = []
    for c in leads.columns:
        i = x2.columns.get_loc(c)
        exclui.append((int(c.split("_")[1]), float(m2.params[i]),
                       float(ci[i][0]), float(ci[i][1]), ci[i][0] * ci[i][1] > 0))
    seq = 0
    maxseq = 0
    for _, _, _, _, e in sorted(exclui):
        seq = seq + 1 if e else 0
        maxseq = max(maxseq, seq)
    idx2 = [x2.columns.get_loc(c) for c in leads.columns]
    p2, f2 = wild_cluster_boot(d.y.to_numpy(float), x2.to_numpy(float),
                               d.unidade.to_numpy(), idx2)
    linhas.append({"painel": painel, "teste": "T2", "estimavel": True, "ano_base": base,
                   "F_conjunta_leads": f2, "p_wild_cluster_bootstrap": p2,
                   "max_leads_consecutivos_com_IC_excluindo_zero": maxseq,
                   "leads": json.dumps([[a, round(b, 4), round(lo, 4), round(hi, 4)]
                                        for a, b, lo, hi, _ in sorted(exclui)]),
                   "veredito_F2": "DISPARA" if (maxseq >= 2 or p2 < 0.10) else "nao dispara"})
    return linhas


def main() -> None:
    paineis = carrega()
    pesos_l, efeitos_l, tp_l = [], [], []
    for painel, cfg in PAINEIS.items():
        m = paineis[painel]
        for t0 in cfg["quebras"]:
            pre = m.index[m.index < t0].to_numpy()
            pos = m.index[m.index >= t0].to_numpy()
            if len(pre) < 3:
                efeitos_l.append({"painel": painel, "quebra": t0, "estimavel": False,
                                  "motivo_nao_estimavel": f"pre-janela de {len(pre)} pontos "
                                  "(EMENDA E4): controle sintetico nao ajustavel"})
                continue
            mn = normaliza(m, pre)
            mask_pre = np.isin(mn.index.to_numpy(), pre)
            mask_pos = ~mask_pre
            # SCM para cada unidade como tratada (P1 in-space e F5 de uma so vez)
            razoes = {}
            for alvo in [TRAT, *CONTROLES]:
                doadores = [u for u in [TRAT, *CONTROLES] if u != alvo]
                w = scm(mn[alvo].to_numpy(float), mn[doadores].to_numpy(float), mask_pre)
                sint = mn[doadores].to_numpy(float) @ w
                rp = rmspe(mn[alvo].to_numpy(float), sint, mask_pre)
                rq = rmspe(mn[alvo].to_numpy(float), sint, mask_pos)
                razoes[alvo] = rq / rp if rp > 0 else np.inf
                if alvo == TRAT:
                    w_trat, sint_trat, rp_t, rq_t = w, sint, rp, rq
                    for u, wi in zip(doadores, w, strict=False):
                        pesos_l.append({"painel": painel, "quebra": t0, "doador": u,
                                        "peso": round(float(wi), 4),
                                        "rmspe_pre": round(rp, 4), "rmspe_pos": round(rq, 4),
                                        "n_pre": len(pre), "n_pos": len(pos),
                                        "seed": SEED_SCM})
                else:
                    pesos_l.append({"painel": painel, "quebra": t0, "doador": "-",
                                    "peso": np.nan, "placebo_in_space_alvo": alvo,
                                    "rmspe_pre": round(rp, 4), "rmspe_pos": round(rq, 4)})
            ordem = sorted(razoes, key=lambda k: -razoes[k])
            posicao = ordem.index(TRAT) + 1
            p_perm = posicao / len(ordem)
            sd_pre = (float(np.std(mn[TRAT].to_numpy(float)[mask_pre], ddof=1))
                      if len(pre) > 1 else np.nan)
            # efeito medio pos (gap normalizado) e DiD 2x2 em log
            gap = float(np.mean(mn[TRAT].to_numpy(float)[mask_pos] - sint_trat[mask_pos]))
            # LOO (F7)
            loo = {}
            for fora in CONTROLES:
                doad = [u for u in CONTROLES if u != fora]
                w2 = scm(mn[TRAT].to_numpy(float), mn[doad].to_numpy(float), mask_pre)
                s2 = mn[doad].to_numpy(float) @ w2
                loo[fora] = float(np.mean(mn[TRAT].to_numpy(float)[mask_pos] - s2[mask_pos]))
            desvio_max = max(abs(v - gap) for v in loo.values()) / abs(gap) if gap else np.inf
            # DiD twoway FE em log, cluster por cidade
            d = m.stack().rename("y").reset_index()
            d.columns = ["ano", "unidade", "y"]
            c = 0.0009 if painel.startswith("A") else 0.0
            d["ly"] = np.log(d.y.clip(lower=1e-6) + c)
            d["trat"] = (d.unidade == TRAT).astype(float)
            d["pos"] = (d.ano >= t0).astype(float)
            X = pd.concat(
                [pd.get_dummies(d.unidade, drop_first=True).astype(float),
                 pd.get_dummies(d.ano, drop_first=True).astype(float),
                 (d.trat * d.pos).rename("did")], axis=1)
            X = sm.add_constant(X)
            X.columns = [str(c) for c in X.columns]
            md = sm.OLS(d.ly.to_numpy(float), X.to_numpy(float)).fit(
                cov_type="cluster", cov_kwds={"groups": pd.factorize(d.unidade)[0]})
            i_did = list(X.columns).index("did")
            f_flags = {
                "F3_rmspe_pre_maior_que_meio_dp": bool(rp_t > 0.5 * sd_pre),
                "F4_peso_concentrado_>0.80": bool(np.max(w_trat) > 0.80),
                "F5_rank_nao_top2": bool(posicao > 2),
                "F6_inversao_entre_paineis": ("nao aplicavel - nenhuma quebra e "
                                              "estimada nos dois paineis"),
                "F7_loo_desloca_mais_de_50pct": bool(desvio_max > 0.5),
            }
            efeitos_l.append({
                "painel": painel, "quebra": t0, "estimavel": True,
                "n_pre": len(pre), "n_pos": len(pos),
                "gap_medio_pos_normalizado": round(gap, 4),
                "rmspe_pre": round(rp_t, 4), "rmspe_pos": round(rq_t, 4),
                "razao_pos_pre": round(rq_t / rp_t, 3),
                "rank_razao_entre_6": posicao, "p_permutacao": round(p_perm, 3),
                "piso_de_p_por_permutacao": round(1 / 6, 3),
                "peso_max_doador": round(float(np.max(w_trat)), 3),
                "doador_dominante": CONTROLES[int(np.argmax(w_trat))],
                "dp_pre_tratado": round(sd_pre, 4),
                "did_coef_log": round(float(md.params[i_did]), 4),
                "did_ic95_inf": round(float(md.conf_int()[i_did][0]), 4),
                "did_ic95_sup": round(float(md.conf_int()[i_did][1]), 4),
                "loo_desvio_relativo_max": round(float(desvio_max), 3),
                "loo_por_doador": json.dumps({k: round(v, 4) for k, v in loo.items()}),
                **f_flags,
                "criterios_F_disparados": ";".join(
                    k for k, v in f_flags.items() if v is True),
                "selo": "estimado",
            })
        base = {"A_area_WSF": 2004, "B_luz_HARM": 2015}[painel]
        pre_fim = {"A_area_WSF": 2004, "B_luz_HARM": 2015}[painel]
        tp_l += tendencia_paralela(m, pre_fim, base, painel)

    pd.DataFrame(pesos_l).to_csv(SAIDA / "did_sintetico_pesos.csv", index=False)
    ef = pd.DataFrame(efeitos_l)
    ef.to_csv(SAIDA / "did_efeitos.csv", index=False)
    pd.DataFrame(tp_l).to_csv(SAIDA / "tendencia_paralela_pre2005.csv", index=False)
    print(ef.reindex(columns=["painel", "quebra", "estimavel", "gap_medio_pos_normalizado",
                              "rmspe_pre", "razao_pos_pre", "rank_razao_entre_6",
                              "p_permutacao", "peso_max_doador", "did_coef_log",
                              "criterios_F_disparados"]).to_string(index=False))
    print(pd.DataFrame(tp_l).reindex(
        columns=["painel", "teste", "estimavel", "p_wild_cluster_bootstrap",
                 "max_leads_consecutivos_com_IC_excluindo_zero", "veredito_F1",
                 "veredito_F2", "motivo_nao_estimavel"]).to_string(index=False))


if __name__ == "__main__":
    main()
