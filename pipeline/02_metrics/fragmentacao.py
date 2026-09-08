#!/usr/bin/env python3
"""pipeline/02_metrics/fragmentacao.py — §5.2 item 3: fragmentação com `pylandstats`.

Métricas por ano e por camada (`urbano`, `industrial`, `reassentamento`),
usando a classificação própria — é a única fonte que separa as três camadas
mutuamente exclusivas (ADR 0008). Todas as métricas de fragmentação carregam
a mesma ressalva do item 5 da tarefa: **sensíveis à comissão medida (0,27-0,63,
ADR 0009)**. Comissão tende a acrescentar manchas pequenas e espúrias
("sal e pimenta" residual, mesmo depois do filtro de coerência 3×3 aplicado na
classificação) — isso INFLA `n_manchas` e a `densidade_de_borda`, e DEPRIME o
`tamanho médio de mancha` e o `largest_patch_index`. A direção do viés é
declarada; a magnitude, não.

Também roda por unidade (usando a mesma atribuição por vizinho mais próximo de
`_common.atribuir_unidade_mais_proxima`) para `urbano`, restrito a
`tete`/`moatize` — `industrial` e `reassentamento` já são unidades ou já têm
split próprio, então a fragmentação por camada inteira (linha "aoi") já cobre
o caso delas sem introduzir um segundo split arbitrário.

Métricas reportadas, por classe presente/ausente (`pylandstats`, landscape
binário: classe 1 = camada, classe 0 = resto):
- `n_manchas` (number_of_patches)
- `area_media_manchas_km2` (area_mn, convertida de ha)
- `largest_patch_index_pct` (largest_patch_index, já em %)
- `densidade_borda_m_ha` (edge_density, m/ha nativo do pacote)
- `indice_forma_medio` (shape_index_mn, adimensional, 1 = mais compacto)

Uso: `uv run python pipeline/02_metrics/fragmentacao.py`
"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pylandstats as pls

sys.path.insert(0, str(Path(__file__).resolve().parent))
import _common as c

CAMADAS = ["urbano", "industrial", "reassentamento"]
METRICAS_PLS = {
    "n_manchas": ("number_of_patches", "n", None),
    "area_media_manchas_km2": ("area_mn", "km2", 1e-2),  # area_mn vem em ha -> km2
    "largest_patch_index_pct": ("largest_patch_index", "%", None),
    "densidade_borda_m_ha": ("edge_density", "m/ha", None),
    "indice_forma_medio": ("shape_index_mn", "adimensional", None),
}


def metricas_landscape(mask: np.ndarray, res_m: float = 30.0) -> dict[str, float | None]:
    if mask.sum() == 0:
        return dict.fromkeys(METRICAS_PLS, None)
    arr = mask.astype("int16")
    ls = pls.Landscape(arr, res=(res_m, res_m), nodata=-1)
    saida = {}
    for nome, (metodo, _unid, fator) in METRICAS_PLS.items():
        try:
            valor = getattr(ls, metodo)(class_val=1)
        except Exception:
            valor = None
        if valor is not None and fator is not None:
            valor = valor * fator
        saida[nome] = round(float(valor), 4) if valor is not None else None
    return saida


def linhas(estudo: dict, epsg: int) -> list[dict]:
    linhas_out = []
    anos = estudo["anos_ancora"]["imagem"]
    pontos_urbano = {
        k: v for k, v in c.pontos_sede_utm(epsg).items() if k in ("tete", "moatize_vila")
    }

    for ano in anos:
        for camada in CAMADAS:
            mask, perfil = c.carregar_camada(camada, ano, epsg=epsg)
            m = metricas_landscape(mask)
            for nome_metrica, valor in m.items():
                _, unid_med, _ = METRICAS_PLS[nome_metrica]
                linhas_out.append(
                    _linha(ano, "aoi", camada, nome_metrica, valor, unid_med, int(mask.sum()))
                )

            if camada == "urbano":
                partes = c.atribuir_unidade_mais_proxima(mask, perfil["transform"], pontos_urbano)
                for u, mu in partes.items():
                    m_u = metricas_landscape(mu)
                    for nome_metrica, valor in m_u.items():
                        _, unid_med, _ = METRICAS_PLS[nome_metrica]
                        linhas_out.append(
                            _linha(ano, u, camada, nome_metrica, valor, unid_med, int(mu.sum()))
                        )
    return linhas_out


def _linha(
    ano: int, unidade: str, camada: str, metrica: str, valor, unid_med: str, n_pixels: int
) -> dict:
    return {
        "ano": ano,
        "unidade": unidade,
        "camada": camada,
        "fonte_dado": "classificacao_propria",
        "metrica": metrica,
        "periodo_inicio": None,
        "valor": valor,
        "unidade_medida": unid_med,
        "selo": "observado",
        "confiavel_para_tendencia": False,
        "fonte": (
            f"pylandstats 3.1.0 sobre data/processed/imagery/{camada}_{ano}_30m_32736.tif"
        ),
        "metodo": (
            "Landscape binário (classe=camada, res=30m), pylandstats.Landscape, "
            "neighborhood_rule='8' (padrão)."
        ),
        "nota": (
            f"n_pixels_camada={n_pixels}. "
            "Sensível à comissão medida (acurácia do usuário 0,27-0,63, ADR 0009): "
            "comissão tende a inflar n_manchas/densidade_borda e a deprimir "
            "tamanho médio de mancha/largest_patch_index — direção declarada, "
            "magnitude não corrigida."
        ),
    }


def main() -> list[dict]:
    estudo = c.carregar_estudo()
    epsg = c.epsg_metrico(estudo)
    return linhas(estudo, epsg)


if __name__ == "__main__":
    import json

    out = main()
    print(json.dumps(out[:5], indent=2, ensure_ascii=False))
    print(f"{len(out)} linhas geradas.", file=sys.stderr)
