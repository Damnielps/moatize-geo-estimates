#!/usr/bin/env python3
"""pipeline/01_imagery/slc_off_2010.py — mede a cobertura real das 4 cenas
Landsat 7 (SLC-off) disponíveis para a estação seca de 2010 (§ Prioridade 2
da tarefa; ver docs/ADR/0005-janela-temporal-2010.md).

Não escreve nada em `data/processed/` nem altera `config/study.yaml`. Grava:
  - um composto EXPERIMENTAL de 2010 (Landsat 7, SLC-off) em `data/interim/`;
  - `data/interim/slc_off_2010_cobertura.csv` com a distribuição pixel a pixel
    do número de observações válidas (0..4) depois da máscara de nuvem/sombra
    E da máscara de gap do SLC-off (via o próprio `qa_pixel`: o bit FILL já
    sinaliza tanto nodata de borda quanto os gaps de linha do SLC-off, porque
    o USGS marca os gaps como pixel de preenchimento na banda QA — não é uma
    suposição: é o comportamento documentado do produto C2 L2 SLC-off, no qual
    o gap vira valor de preenchimento (fill) em todas as bandas, inclusive QA).

Uso: `uv run python pipeline/01_imagery/slc_off_2010.py`
"""

from __future__ import annotations

import csv
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "00_fetch"))
from _config import carregar_estudo

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _stac_common import (
    STAC_ENDPOINT_CANONICO,
    abrir_cliente_stac,
    buscar_itens,
)
from compostos import (
    carregar_colecao_mascarada,
    construir_geobox,
    escrever_composto_cog,
    escrever_nobs_cog,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
STUDY_YAML = REPO_ROOT / "config" / "study.yaml"
DATA_INTERIM = REPO_ROOT / "data" / "interim"

ANO = 2010
DATETIME_RANGE = "2010-05-01T00:00:00Z/2010-10-31T23:59:59Z"
PLATAFORMA = "landsat-7"


def main() -> int:
    estudo = carregar_estudo(STUDY_YAML)
    bbox_aoi = estudo["aoi"]["bbox"]
    bbox = [bbox_aoi["xmin"], bbox_aoi["ymin"], bbox_aoi["xmax"], bbox_aoi["ymax"]]
    crs_metrico = estudo["crs"]["metrico"]
    nuvem_max = estudo["composto"]["nuvem_max_pct"]
    res_m = estudo["sensores"][2005]["res_m"]  # mesma resolução Landsat (30 m)

    geobox = construir_geobox(bbox_aoi, crs_metrico, res_m)
    client = abrir_cliente_stac(STAC_ENDPOINT_CANONICO)

    # Confirma a contagem declarada pelo orquestrador (4 cenas L7, mai-out/2010).
    itens = buscar_itens(client, "landsat-c2-l2", bbox, DATETIME_RANGE, nuvem_max, PLATAFORMA)
    print(
        f"[info] {len(itens)} cenas Landsat 7 encontradas para 2010 "
        f"(mai-out, nuvem<={nuvem_max}%)",
        file=sys.stderr,
    )
    for it in itens:
        print(f"  - {it.id}  {it.datetime.isoformat() if it.datetime else '?'}", file=sys.stderr)

    bandas, itens_usados = carregar_colecao_mascarada(
        client, "landsat-c2-l2", bbox, DATETIME_RANGE, nuvem_max, geobox, PLATAFORMA
    )
    if bandas is None:
        print("[FALHA] nenhuma cena retornada — não é possível medir cobertura", file=sys.stderr)
        return 1

    # nº de observações válidas por pixel, banda de referência (máscara igual em todas).
    primeira = bandas[next(iter(bandas))]
    nobs = primeira.notnull().sum(dim="time").compute()

    n_datas = len(itens_usados)
    valores, contagens = np.unique(nobs.values, return_counts=True)
    total = int(nobs.size)

    distrib = {int(k): int(v) for k, v in zip(valores, contagens, strict=True)}
    linhas = []
    for k in range(0, n_datas + 1):
        n_pixels = distrib.get(k, 0)
        linhas.append(
            {
                "n_observacoes_validas": k,
                "n_pixels": n_pixels,
                "fracao_da_aoi": n_pixels / total,
            }
        )

    DATA_INTERIM.mkdir(parents=True, exist_ok=True)
    csv_path = DATA_INTERIM / "slc_off_2010_cobertura.csv"
    with csv_path.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(
            fh, fieldnames=["n_observacoes_validas", "n_pixels", "fracao_da_aoi"]
        )
        writer.writeheader()
        writer.writerows(linhas)

    fracao_zero = distrib.get(0, 0) / total
    print(f"[resultado] pixels totais na AOI: {total}", file=sys.stderr)
    print(f"[resultado] cenas usadas: {n_datas}", file=sys.stderr)
    for linha in linhas:
        print(
            f"[resultado] {linha['n_observacoes_validas']} obs válidas: "
            f"{linha['n_pixels']} pixels ({100 * linha['fracao_da_aoi']:.2f}%)",
            file=sys.stderr,
        )
    print(f"[DECISIVO] fração de pixels com ZERO observações válidas: {100 * fracao_zero:.2f}%",
          file=sys.stderr)

    # Grava o composto experimental (mediana das 4 cenas), só para inspeção —
    # não é um artefato final, não tem .meta.json de proveniência de Fase 1.
    import xarray as xr

    composto = xr.Dataset({nome: da.median(dim="time", skipna=True) for nome, da in bandas.items()})
    composto_computado = composto.compute()
    nome_base = "composto_experimental_2010_L7_SLCoff_30m_32736"
    escrever_composto_cog(composto_computado, DATA_INTERIM / f"{nome_base}.tif", crs_metrico)
    escrever_nobs_cog(nobs.astype("uint16"), DATA_INTERIM / f"{nome_base}_nobs.tif", crs_metrico)

    print(f"[ok] composto experimental gravado em data/interim/{nome_base}.tif", file=sys.stderr)
    print(f"[ok] cobertura gravada em {csv_path.relative_to(REPO_ROOT)}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
