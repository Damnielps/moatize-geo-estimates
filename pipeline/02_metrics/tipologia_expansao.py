#!/usr/bin/env python3
"""pipeline/02_metrics/tipologia_expansao.py — §5.2 itens 2 e 4: tipologia de
expansão (infill / borda / leapfrog) e rosa de expansão.

## Regra de decisão da tipologia (Angel et al. 2010; Xu et al. 2019)

Para cada par de anos-âncora consecutivos (t0, t1), um pixel é "novo" se
está construído em t1 e não em t0. Cada pixel novo é classificado pela
**densidade de pixels já construídos em t0** dentro de um raio fixo ao seu
redor (disco de 90 m = 3 pixels de 30 m, excluindo o próprio pixel — 28
vizinhos no disco):

- **infill**: densidade >= 0,50 (metade ou mais da vizinhança já era construída em t0)
- **borda** (edge): 0 < densidade < 0,50 (toca construído em t0, mas a maioria da vizinhança não é)
- **leapfrog**: densidade == 0 (nenhum pixel construído em t0 no raio de 90 m)

O raio de 90 m é um limiar declarado, não calibrado: é o menor múltiplo do
pixel (30 m) que dá um disco com vizinhança não trivial (28 pixels) sem
ultrapassar a ordem de grandeza de "quarteirão" usada por Angel et al. Não há
verdade de campo para calibrar o raio nesta AOI; sensibilidade a essa escolha
não foi testada e fica registrada como limite.

## Por que isto é publicável apesar da comissão de 0,27-0,63 (ADR 0009)

O item 2 das restrições herdadas diz: "direção da expansão e tipologia tendem
a ser robustas [à comissão]; área absoluta e densidade, não." O raciocínio:
um falso positivo disperso ("sal e pimenta") tende a virar `leapfrog` (baixa
densidade ao redor) independentemente de ser um pixel real ou comissão — o
que view enviesaria a tipologia **na direção de superestimar leapfrog**, não
inventaria infill/borda onde não há nenhum construído. A proporção de
leapfrog aqui é, portanto, um teto, não uma medida limpa; documentado nos
metadados de cada linha.

## Fontes por período (ver ADR 0008)

- 2000→2005, 2005→2010, 2010→2015: WSF Evolution (série de tendência).
- 2015→2020, 2020→2025: classificação própria (construído = urbano ∪
  industrial ∪ reassentamento), porque o WSF termina em 2015. Marcado com
  fonte e selo distintos.

## Rosa de expansão

Para os mesmos pixels "novos", ângulo (0°=Norte, sentido horário) do vetor
entre o **centróide do construído em t0** da unidade e o pixel novo,
agregado em 16 setores de 22,5°. Estatística circular: direção resultante
(ângulo do vetor-soma) e razão de concentração R de Rayleigh (0 = disperso
em todas as direções, 1 = toda a expansão num único rumo).

Uso: `uv run python pipeline/02_metrics/tipologia_expansao.py`
"""

from __future__ import annotations

import itertools
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
import _common as c

RAIO_M = 90.0
LIMIAR_INFILL = 0.50
UNIDADES = ["tete", "moatize_vila", "cateme", "mwaladzi"]
ANO_FIM_WSF = 2015


def _disco(raio_px: int) -> np.ndarray:
    y, x = np.ogrid[-raio_px : raio_px + 1, -raio_px : raio_px + 1]
    return (x * x + y * y) <= raio_px * raio_px


def densidade_vizinhanca(mask_t0: np.ndarray, raio_m: float, res_m: float) -> np.ndarray:
    raio_px = max(1, round(raio_m / res_m))
    kernel = _disco(raio_px).astype("float32")
    kernel[raio_px, raio_px] = 0  # exclui o próprio pixel
    n_vizinhos = kernel.sum()
    from scipy.signal import fftconvolve

    soma = fftconvolve(mask_t0.astype("float32"), kernel, mode="same")
    return np.clip(soma / n_vizinhos, 0, 1)


def classificar_tipologia(
    mask_t0: np.ndarray, mask_t1: np.ndarray, res_m: float
) -> dict[str, np.ndarray]:
    novo = mask_t1 & ~mask_t0
    dens = densidade_vizinhanca(mask_t0, RAIO_M, res_m)
    infill = novo & (dens >= LIMIAR_INFILL)
    leapfrog = novo & (dens == 0)
    borda = novo & ~infill & ~leapfrog
    return {"infill": infill, "borda": borda, "leapfrog": leapfrog, "novo": novo}


def rosa_expansao(mask_t0: np.ndarray, novo: np.ndarray, transform) -> dict:
    if mask_t0.sum() == 0 or novo.sum() == 0:
        return {
            "n_setores": 16,
            "direcao_resultante_graus": None,
            "concentracao_r": None,
            "n_pixels_novos": int(novo.sum()),
            "histograma_setores": [0] * 16,
        }
    xs0, ys0 = c.coordenadas_pixels(mask_t0, transform)
    cx, cy = xs0.mean(), ys0.mean()
    xs1, ys1 = c.coordenadas_pixels(novo, transform)
    dx, dy = xs1 - cx, ys1 - cy
    # ângulo com 0°=Norte, sentido horário: atan2(dx, dy) em coordenadas projetadas (y para norte)
    ang = np.degrees(np.arctan2(dx, dy)) % 360
    rad = np.radians(ang)
    r_x, r_y = np.cos(rad).sum(), np.sin(rad).sum()
    direcao = np.degrees(np.arctan2(r_y, r_x)) % 360
    concentracao = float(np.hypot(r_x, r_y) / len(ang))
    setores = np.floor(ang / 22.5).astype(int) % 16
    hist = np.bincount(setores, minlength=16)
    return {
        "n_setores": 16,
        "direcao_resultante_graus": round(float(direcao), 2),
        "concentracao_r": round(concentracao, 4),
        "n_pixels_novos": int(novo.sum()),
        "histograma_setores": hist.tolist(),
    }


def linhas(estudo: dict, epsg: int) -> list[dict]:
    linhas_out = []
    anos_img = estudo["anos_ancora"]["imagem"]
    pares = list(itertools.pairwise(anos_img))
    pontos = c.pontos_sede_utm(epsg)

    for a0, a1 in pares:
        if a1 <= ANO_FIM_WSF:
            fonte_dado, fonte_txt, selo = (
                "wsf_evolution",
                "WSF Evolution (DLR) — ano de primeira detecção",
                "observado",
            )
            _, perfil = c.carregar_camada("urbano", 2000, epsg=epsg)
            wsf = c.carregar_wsf_reprojetado(perfil)
            excl = c.mascara_exclusao_industrial(perfil, epsg)
            construido_t0_full = (wsf > 0) & (wsf <= a0) & ~excl
            construido_t1_full = (wsf > 0) & (wsf <= a1) & ~excl
        else:
            fonte_dado, fonte_txt, selo = (
                "classificacao_propria",
                "Classificação própria (urbano ∪ industrial ∪ reassentamento)",
                "observado",
            )
            construido_t0_full, perfil = c.carregar_construido_total(a0, epsg=epsg)
            construido_t1_full, _ = c.carregar_construido_total(a1, epsg=epsg)

        partes_t0 = c.atribuir_unidade_mais_proxima(construido_t0_full, perfil["transform"], pontos)
        partes_t1 = c.atribuir_unidade_mais_proxima(construido_t1_full, perfil["transform"], pontos)

        for u in UNIDADES:
            tip = classificar_tipologia(partes_t0[u], partes_t1[u], res_m=30.0)
            n_novo = int(tip["novo"].sum())
            for cat in ("infill", "borda", "leapfrog"):
                n_cat = int(tip[cat].sum())
                prop = (n_cat / n_novo) if n_novo > 0 else None
                linhas_out.append(
                    {
                        "ano": a1,
                        "unidade": u,
                        "camada": "construido_total",
                        "fonte_dado": fonte_dado,
                        "metrica": f"prop_{cat}",
                        "periodo_inicio": a0,
                        "valor": round(prop, 4) if prop is not None else None,
                        "unidade_medida": "fracao_pixels_novos",
                        "selo": selo,
                        "confiavel_para_tendencia": True,
                        "fonte": fonte_txt,
                        "metodo": (
                            f"Pixel novo em t1 classificado por densidade de construído em t0 "
                            f"num disco de raio {RAIO_M:.0f} m (limiar infill >= {LIMIAR_INFILL}); "
                            f"leapfrog = densidade 0. n_pixels_novos={n_novo}."
                        ),
                        "nota": (
                            "sem pixels novos no período para esta unidade — "
                            "proporção indefinida"
                            if n_novo == 0
                            else (
                                "proporção sensível a comissão do mapa; tende a "
                                "inflar leapfrog (ver docstring do módulo)."
                            )
                        ),
                    }
                )

            rosa = rosa_expansao(partes_t0[u], tip["novo"], perfil["transform"])
            metodo_rosa = (
                "Estatística circular (Rayleigh) do ângulo entre o centróide do "
                "construído em t0 (na unidade) e cada pixel novo em t1; 0°=Norte, "
                f"sentido horário, 16 setores de 22,5°. n_pixels_novos={rosa['n_pixels_novos']}."
            )
            nota_rosa = (
                "sem pixels novos ou sem base em t0 — direção indefinida"
                if rosa["direcao_resultante_graus"] is None
                else ""
            )
            for chave, valor, unid_med in (
                (
                    "direcao_expansao_graus",
                    rosa["direcao_resultante_graus"],
                    "graus_a_partir_do_norte",
                ),
                (
                    "concentracao_direcional_r",
                    rosa["concentracao_r"],
                    "adimensional_0_1",
                ),
            ):
                linhas_out.append(
                    {
                        "ano": a1,
                        "unidade": u,
                        "camada": "construido_total",
                        "fonte_dado": fonte_dado,
                        "metrica": chave,
                        "periodo_inicio": a0,
                        "valor": valor,
                        "unidade_medida": unid_med,
                        "selo": selo,
                        "confiavel_para_tendencia": True,
                        "fonte": fonte_txt,
                        "metodo": metodo_rosa,
                        "nota": nota_rosa,
                    }
                )

            # Histograma por setor (16 x 22,5°, 0=Norte, sentido horário) — fração
            # dos pixels novos em cada setor, base para desenhar a rosa no app.
            hist = rosa.get("histograma_setores") or [0] * 16
            n_novo_rosa = rosa.get("n_pixels_novos", 0) or 0
            for setor_idx, contagem in enumerate(hist):
                frac = (contagem / n_novo_rosa) if n_novo_rosa > 0 else None
                ini_deg = round(setor_idx * 22.5, 2)
                fim_deg = round((setor_idx + 1) * 22.5, 2)
                linhas_out.append(
                    {
                        "ano": a1,
                        "unidade": u,
                        "camada": "construido_total",
                        "fonte_dado": fonte_dado,
                        "metrica": f"frac_novo_setor_{setor_idx:02d}",
                        "periodo_inicio": a0,
                        "valor": round(frac, 4) if frac is not None else None,
                        "unidade_medida": "fracao_pixels_novos",
                        "selo": selo,
                        "confiavel_para_tendencia": True,
                        "fonte": fonte_txt,
                        "metodo": (
                            f"Setor {setor_idx} = [{ini_deg}°, {fim_deg}°) a partir do "
                            "Norte, sentido horário, sobre o mesmo vetor centróide-t0 -> "
                            "pixel-novo-t1 da rosa de expansão (ver métrica "
                            "direcao_expansao_graus)."
                        ),
                        "nota": (
                            "sem pixels novos no período para esta unidade — "
                            "fração indefinida"
                            if n_novo_rosa == 0
                            else ""
                        ),
                    }
                )
    return linhas_out


def main() -> list[dict]:
    estudo = c.carregar_estudo()
    epsg = c.epsg_metrico(estudo)
    return linhas(estudo, epsg)


if __name__ == "__main__":
    import json

    out = main()
    print(json.dumps(out[:6], indent=2, ensure_ascii=False))
    print(f"{len(out)} linhas geradas.", file=sys.stderr)
