"""Núcleo de série interrompida (§2 do desenho, emendado).

log(y_t + c) = b0 + b1*(t-t0) + b2*D_t + b3*D_t*(t-t0)
b2 = NIVEL (salto), b3 = INCLINACAO (mudanca de ritmo). Nunca somados.
HAC Newey-West com L = floor(4*(T/100)^(2/9)); AR(1) Prais-Winsten como sensibilidade.
"""

from __future__ import annotations

import warnings

import numpy as np
import pandas as pd
import statsmodels.api as sm
from statsmodels.stats.diagnostic import acorr_breusch_godfrey
from statsmodels.stats.stattools import durbin_watson
from statsmodels.tsa.stattools import adfuller

warnings.filterwarnings("ignore")


def hac_lag(t_obs: int) -> int:
    return int(np.floor(4 * (t_obs / 100) ** (2 / 9)))


def _design(anos: np.ndarray, t0: int) -> np.ndarray:
    tc = anos - t0
    d = (anos >= t0).astype(float)
    return np.column_stack([np.ones_like(tc, dtype=float), tc, d, d * tc])


def ajusta_its(
    anos, y, t0: int, c: float = 0.0, log: bool = True, rotulo: str = ""
) -> dict:
    anos = np.asarray(anos, dtype=float)
    y = np.asarray(y, dtype=float)
    ordem = np.argsort(anos)
    anos, y = anos[ordem], y[ordem]
    yy = np.log(y + c) if log else y
    x = _design(anos, t0)
    t_obs = len(anos)
    n_pre = int((anos < t0).sum())
    n_pos = int((anos >= t0).sum())
    lag = hac_lag(t_obs)
    fora = {
        "rotulo": rotulo,
        "t0": t0,
        "T": t_obs,
        "n_pre": n_pre,
        "n_pos": n_pos,
        "hac_lag": lag,
        "escala": "log" if log else "nivel",
        "c_deslocamento": c,
    }
    if n_pre < 3 or n_pos < 3:
        fora["estimavel"] = False
        fora["motivo_nao_estimavel"] = (
            f"pre={n_pre}, pos={n_pos}: modelo segmentado de 4 parametros exige >=3 de cada lado"
        )
        return fora
    m = sm.OLS(yy, x).fit(cov_type="HAC", cov_kwds={"maxlags": lag})
    ci = m.conf_int()
    fora.update(
        {
            "estimavel": True,
            "b0": m.params[0],
            "b1_tendencia_pre": m.params[1],
            "b2_nivel": m.params[2],
            "b2_ic95_inf": ci[2][0],
            "b2_ic95_sup": ci[2][1],
            "b2_p": m.pvalues[2],
            "b3_inclinacao": m.params[3],
            "b3_ic95_inf": ci[3][0],
            "b3_ic95_sup": ci[3][1],
            "b3_p": m.pvalues[3],
            "r2": m.rsquared,
        }
    )
    ols = sm.OLS(yy, x).fit()
    resid = ols.resid
    fora["durbin_watson"] = float(durbin_watson(resid))
    for ordem_bg in (1, 2):
        try:
            fora[f"breusch_godfrey_p_ordem{ordem_bg}"] = float(
                acorr_breusch_godfrey(ols, nlags=ordem_bg)[1]
            )
        except Exception:
            fora[f"breusch_godfrey_p_ordem{ordem_bg}"] = np.nan
    try:
        fora["adf_resid_p"] = float(adfuller(resid, maxlag=1, autolag=None)[1])
    except Exception:
        fora["adf_resid_p"] = np.nan
    # AR(1) Prais-Winsten (sensibilidade)
    try:
        g = sm.GLSAR(yy, x, rho=1).iterative_fit(maxiter=10)
        fora["b2_nivel_ar1"] = float(g.params[2])
        fora["b3_inclinacao_ar1"] = float(g.params[3])
        fora["troca_sinal_hac_ar1"] = bool(
            np.sign(g.params[2]) != np.sign(m.params[2])
            or np.sign(g.params[3]) != np.sign(m.params[3])
        )
    except Exception:
        fora["b2_nivel_ar1"] = np.nan
        fora["b3_inclinacao_ar1"] = np.nan
        fora["troca_sinal_hac_ar1"] = None
    return fora


def ajusta_donut(anos, y, t0: int, **kw) -> dict:
    """Sensibilidade pré-registrada (§2.2.5): exclui t0-1, t0, t0+1."""
    anos = np.asarray(anos, dtype=float)
    y = np.asarray(y, dtype=float)
    keep = (anos < t0 - 1) | (anos > t0 + 1)
    r = ajusta_its(anos[keep], y[keep], t0, **kw)
    r["variante"] = "donut_+-1ano"
    return r


def quasi_poisson(anos, n_eventos, offset_area, t0: int, rotulo: str = "") -> dict:
    """Especificação alternativa pré-registrada para contagem (§2.1)."""
    anos = np.asarray(anos, dtype=float)
    n = np.asarray(n_eventos, dtype=float)
    x = _design(anos, t0)
    off = np.full(len(anos), np.log(offset_area))
    try:
        m = sm.GLM(n, x, family=sm.families.Poisson(), offset=off).fit(
            cov_type="HAC", cov_kwds={"maxlags": hac_lag(len(anos))}
        )
        disp = float(m.pearson_chi2 / m.df_resid)
        return {
            "rotulo": rotulo,
            "t0": t0,
            "variante": "quasi_poisson",
            "b2_nivel": float(m.params[2]),
            "b3_inclinacao": float(m.params[3]),
            "dispersao_pearson": disp,
            "estimavel": True,
        }
    except Exception as e:  # pragma: no cover
        return {"rotulo": rotulo, "t0": t0, "variante": "quasi_poisson",
                "estimavel": False, "motivo_nao_estimavel": str(e)}


def para_df(linhas) -> pd.DataFrame:
    return pd.DataFrame(linhas)
