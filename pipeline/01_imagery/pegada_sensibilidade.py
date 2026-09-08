#!/usr/bin/env python3
"""pipeline/01_imagery/pegada_sensibilidade.py — sensibilidade da pegada minerária
aos três parâmetros livres da regra (docs/ADR/0011).

## Por que este script existe

A regra da pegada tem três parâmetros: o limiar de razão de verde
(`RAZAO_VERDE_PEGADA`), o raio do envelope de busca (`BUFFER_EXPANSAO_MINA_M`) e a
janela do fecho morfológico (`JANELA_FECHO_PEGADA`). Um contrato de plausibilidade
que passa só na configuração adotada não distingue "a pegada é classificável" de
"os parâmetros foram ajustados até passar" — que é exatamente a acusação que este
redesenho precisa poder responder.

Este script varre a grade dos três parâmetros e publica, para cada combinação, a
série de área e a cobertura dos polígonos de Maus et al. O leitor confere por conta
própria se o resultado depende da escolha. **Nenhuma conclusão do estudo sai daqui**:
a série publicada é a de `pegada_por_ano.csv`, com os parâmetros de
`classificacao.py`. Isto é auditoria, não produto.

Uso: `uv run python pipeline/01_imagery/pegada_sensibilidade.py`
"""

from __future__ import annotations

import csv
import itertools
import sys
from pathlib import Path

import geopandas as gpd
import numpy as np
import rasterio
import rasterio.features
from scipy.ndimage import binary_closing, binary_dilation

sys.path.insert(0, str(Path(__file__).resolve().parent))
from classificacao import (
    ANO_LICENCA_MINA,
    BUFFER_EXPANSAO_MINA_M,
    JANELA_FECHO_PEGADA,
    LIMIAR_AGUA_MNDWI,
    MAUS_AOI_GEOJSON,
    RAZAO_VERDE_PEGADA,
    REPO_ROOT,
    area_km2,
)

DATA_PROCESSED = REPO_ROOT / "data" / "processed" / "imagery"
SAIDA = REPO_ROOT / "data" / "processed" / "pegada_sensibilidade.csv"

ANOS = [2000, 2005, 2010, 2015, 2020, 2025]
GRADE_RAZAO = [0.50, 0.55, 0.60, 0.65, 0.70]
GRADE_BUFFER_M = [250.0, 500.0, 750.0]
GRADE_FECHO = [3, 5]


def ler(nome: str, ano: int) -> np.ndarray:
    caminho = DATA_PROCESSED / f"{nome}_{ano}_30m_32736.tif"
    with rasterio.open(caminho) as src:
        return src.read(1, masked=True).filled(np.nan)


def ler_bool(nome: str, ano: int) -> np.ndarray:
    caminho = DATA_PROCESSED / f"{nome}_{ano}_30m_32736.tif"
    with rasterio.open(caminho) as src:
        return src.read(1) > 0


def main() -> int:
    with rasterio.open(DATA_PROCESSED / "ndvi_2020_30m_32736.tif") as src:
        transform, shape = src.transform, src.shape
        res_m = abs(src.transform.a)

    gdf = gpd.read_file(MAUS_AOI_GEOJSON).to_crs(32736)
    maus = rasterio.features.geometry_mask(
        gdf.geometry, out_shape=shape, transform=transform, invert=True
    )

    dados = {}
    for ano in ANOS:
        dados[ano] = (
            ler("ndvi", ano),
            ler("ndvi_chuva", ano),
            ler("mndwi", ano),
            ler_bool("construido", ano),
        )

    linhas = []
    for razao, buffer_m, fecho in itertools.product(GRADE_RAZAO, GRADE_BUFFER_M, GRADE_FECHO):
        raio_px = max(1, round(buffer_m / res_m))
        lado = 2 * raio_px + 1
        envelope = binary_dilation(maus, structure=np.ones((lado, lado), dtype=bool))
        acum = np.zeros(shape, dtype=bool)
        for ano in ANOS:
            ndvi, ndvi_chuva, mndwi, construido = dados[ano]
            finito = np.isfinite(ndvi) & np.isfinite(ndvi_chuva) & np.isfinite(mndwi)
            agua = finito & (mndwi > LIMIAR_AGUA_MNDWI)
            referencia = finito & ~agua & ~envelope
            med_s = float(np.median(ndvi[referencia]))
            med_c = float(np.median(ndvi_chuva[referencia]))
            nua = (
                finito
                & ~agua
                & (ndvi_chuva < razao * med_c)
                & (ndvi < razao * med_s)
            )
            # `fechar_pegada` usa a janela fixa do módulo; aqui a janela é o
            # parâmetro varrido, então o fecho é aplicado explicitamente. Quando
            # fecho == JANELA_FECHO_PEGADA as duas expressões coincidem, e é isso
            # que a linha `adotado=True` verifica contra pegada_por_ano.csv.
            estrutura = np.ones((fecho, fecho), dtype=bool)
            mask = binary_closing((nua | construido) & envelope, structure=estrutura)
            mask &= envelope
            if ano < ANO_LICENCA_MINA:
                mask = np.zeros(shape, dtype=bool)
                acum[:] = False
            else:
                acum |= mask
            linhas.append(
                {
                    "razao_verde": razao,
                    "buffer_envelope_m": buffer_m,
                    "janela_fecho_px": fecho,
                    "ano": ano,
                    "area_km2": round(area_km2(acum, transform), 3),
                    "cobertura_poligonos_maus": round(
                        float((acum & maus).sum() / maus.sum()), 4
                    ),
                    "adotado": (
                        razao == RAZAO_VERDE_PEGADA
                        and buffer_m == BUFFER_EXPANSAO_MINA_M
                        and fecho == JANELA_FECHO_PEGADA
                    ),
                }
            )

    SAIDA.parent.mkdir(parents=True, exist_ok=True)
    with SAIDA.open("w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=[*list(linhas[0]), "nota"])
        w.writeheader()
        nota = (
            "Varredura dos três parâmetros livres da regra de pegada minerária "
            "(docs/ADR/0011). A linha com adotado=True é a configuração publicada em "
            "pegada_por_ano.csv. Área após permanência, acumulada desde 2006. "
            "AUDITORIA, não produto: nenhum número do artigo ou do app sai daqui."
        )
        for linha in linhas:
            w.writerow({**linha, "nota": nota})

    n_ok = sum(
        1
        for r in linhas
        if r["ano"] == 2025 and r["cobertura_poligonos_maus"] >= 0.50
    )
    n_cfg = len(GRADE_RAZAO) * len(GRADE_BUFFER_M) * len(GRADE_FECHO)
    print(
        f"[ok] {SAIDA.relative_to(REPO_ROOT)}: {n_cfg} configurações; "
        f"{n_ok}/{n_cfg} cobrem >=50% de Maus em 2025",
        file=sys.stderr,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
