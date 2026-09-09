#!/usr/bin/env python3
"""pipeline/01_imagery/validacao_externa_cultivo.py — concordância de `cultivo_*` com
GLAD Global Cropland e ESA WorldCover (§5.6.1, item "validação externa").

## Papel deste script — NÃO substitui `acuracia_cultivo.py`

A Fase 0' registrou URLs quebradas para as referências externas de cultivo; um fetch
paralelo às vezes as recupera. Quando `data/raw/glad_cropland_*.tif` e/ou
`data/raw/esa_worldcover_*.tif` existem, este script mede **concordância** — não
acurácia, pelo mesmo motivo que `classificacao.concordancia_ghsl` não é acurácia contra
GHSL: os dois produtos têm erro próprio, resolução nativa diferente (GLAD 30 m, ESA
WorldCover 10 m, `cultivo_*` 30 m) e definição diferente de "cultivo" (GLAD e ESA WC
mapeiam PARCELA cultivada reconhecível; `cultivo_sequeiro`/`cultivo_irrigado` medem
fenologia, e docs/ADR/0012 já mostrou que `cultivo_sequeiro` não corresponde de forma
confiável a cultivo). Concordância baixa aqui **não piora** o veredito de ADR 0012;
concordância alta seria evidência a favor, mas não a validação por si (ver limitação 3).

## Referências disponíveis e correspondência de ano

- **GLAD Global Cropland** (Potapov et al. 2021): composto quinquenal centrado no ano do
  arquivo (`data/raw/glad_cropland_<ano>_aoi.tif`, valores 0/1). Comparado ao
  `cultivo.py` do ano-âncora mais próximo disponível.
- **ESA WorldCover** (`data/raw/esa_worldcover_<ano>_*.tif`, classe 40 = cropland),
  10 m, só 2020/2021 — comparado a 2020.

## Limitações declaradas

1. Reprojeção de 10-30 m para a grade de 30 m/EPSG:32736 usa a fração de área
   (`Resampling.average` sobre a máscara binária) com corte em 50%: uma célula de 30 m
   conta como cropland externo se mais de metade da área, na referência, for cropland.
2. GLAD e ESA WorldCover definem "cropland" por reconhecimento de parcela (padrão
   geométrico + fenologia), não só fenologia — por isso concordância parcial é esperada
   mesmo se `cultivo.py` estivesse correto.
3. Nenhuma métrica aqui altera o veredito de docs/ADR/0012 (acurácia por interpretação
   visual, que usa um rótulo de referência independente de padrão geométrico). Este
   script é complementar, não substituto.

Uso: `uv run python pipeline/01_imagery/validacao_externa_cultivo.py`
"""

from __future__ import annotations

import csv
import sys
from pathlib import Path

import numpy as np
import rasterio
import rasterio.warp

REPO_ROOT = Path(__file__).resolve().parents[2]
DATA_RAW = REPO_ROOT / "data" / "raw"
DATA_PROCESSED = REPO_ROOT / "data" / "processed" / "imagery"
SAIDA_CSV = REPO_ROOT / "data" / "processed" / "concordancia_externa_cultivo.csv"
PROVENANCE_FRAGMENT = REPO_ROOT / "data" / "provenance_parts" / "agricultura_fase2b.md"
MARCADOR_INICIO = "<!-- SECAO_VALIDACAO_EXTERNA_CULTIVO_INICIO -->"
MARCADOR_FIM = "<!-- SECAO_VALIDACAO_EXTERNA_CULTIVO_FIM -->"
RES_M, EPSG = 30, 32736
CORTE_FRACAO = 0.50

GLAD_ANOS = {int(p.stem.split("_")[2]): p for p in DATA_RAW.glob("glad_cropland_*_aoi.tif")}
ESA_TILES = sorted(DATA_RAW.glob("esa_worldcover_*_aoi.tif"))
ESA_CLASSE_CROPLAND = 40


def perfil_ano(ano: int) -> dict:
    with rasterio.open(DATA_PROCESSED / f"cultivo_sequeiro_{ano}_{RES_M}m_{EPSG}.tif") as src:
        return {"crs": src.crs, "transform": src.transform, "shape": src.shape}


def ler_camada(nome: str, ano: int) -> np.ndarray:
    with rasterio.open(DATA_PROCESSED / f"{nome}_{ano}_{RES_M}m_{EPSG}.tif") as src:
        return src.read(1).astype(bool)


def reprojetar_fracao(caminho_bin_0_1: Path, perfil: dict) -> np.ndarray:
    """Reprojeta uma máscara binária (0/1, qualquer resolução/CRS) para a grade de
    estudo como FRAÇÃO de área positiva por célula (Resampling.average)."""
    with rasterio.open(caminho_bin_0_1) as src:
        origem = src.read(1).astype("float32")
        destino = np.zeros(perfil["shape"], dtype="float32")
        rasterio.warp.reproject(
            source=origem,
            destination=destino,
            src_transform=src.transform,
            src_crs=src.crs,
            dst_transform=perfil["transform"],
            dst_crs=perfil["crs"],
            resampling=rasterio.warp.Resampling.average,
        )
    return destino


def concordancia(mapa: np.ndarray, referencia: np.ndarray) -> dict:
    inter = int((mapa & referencia).sum())
    uniao = int((mapa | referencia).sum())
    return {
        "area_mapa_km2": round(float(mapa.sum()) * RES_M * RES_M / 1e6, 3),
        "area_referencia_km2": round(float(referencia.sum()) * RES_M * RES_M / 1e6, 3),
        "jaccard": round(inter / uniao, 4) if uniao else float("nan"),
        "recall_sobre_referencia": (
            round(inter / referencia.sum(), 4) if referencia.sum() else float("nan")
        ),
    }


def main(argv: list[str]) -> int:
    if not GLAD_ANOS and not ESA_TILES:
        print(
            "[info] nenhuma referência externa em data/raw/ (glad_cropland_*/"
            "esa_worldcover_*) — validação externa AUSENTE, declarado. Ver "
            "acuracia_cultivo.py para a validação própria.",
            file=sys.stderr,
        )
        (REPO_ROOT / "data" / "processed" / "concordancia_externa_cultivo.AUSENTE.txt").write_text(
            "Nenhum arquivo GLAD Cropland / ESA WorldCover em data/raw/ no momento da "
            "execução — validação externa de cultivo não realizada. Ver "
            "acuracia_cultivo.py e docs/ADR/0012 para a validação própria (interna).\n",
            encoding="utf-8",
        )
        return 0

    linhas = []
    anos_cultivo = sorted(
        {int(p.stem.split("_")[2]) for p in DATA_PROCESSED.glob("cultivo_sequeiro_*_30m_32736.tif")}
    )

    if GLAD_ANOS and anos_cultivo:
        for ano_glad, caminho_glad in sorted(GLAD_ANOS.items()):
            ano_cultivo = min(anos_cultivo, key=lambda a: abs(a - ano_glad))
            perfil = perfil_ano(ano_cultivo)
            frac = reprojetar_fracao(caminho_glad, perfil)
            ref = frac >= CORTE_FRACAO
            for camada in ("cultivo_sequeiro", "cultivo_irrigado"):
                mapa = ler_camada(camada, ano_cultivo)
                linha = {
                    "referencia": "GLAD_Global_Cropland",
                    "ano_referencia": ano_glad,
                    "ano_cultivo": ano_cultivo,
                    "camada": camada,
                    **concordancia(mapa, ref),
                }
                linhas.append(linha)
                print(
                    f"[ok] GLAD {ano_glad} vs {camada} {ano_cultivo}: "
                    f"jaccard={linha['jaccard']}",
                    file=sys.stderr,
                )

    if ESA_TILES and 2020 in anos_cultivo:
        perfil = perfil_ano(2020)
        frac_total = np.zeros(perfil["shape"], dtype="float32")
        for caminho in ESA_TILES:
            with rasterio.open(caminho) as src:
                bin_crop = (src.read(1) == ESA_CLASSE_CROPLAND).astype("float32")
                destino = np.zeros(perfil["shape"], dtype="float32")
                rasterio.warp.reproject(
                    source=bin_crop,
                    destination=destino,
                    src_transform=src.transform,
                    src_crs=src.crs,
                    dst_transform=perfil["transform"],
                    dst_crs=perfil["crs"],
                    resampling=rasterio.warp.Resampling.average,
                )
            frac_total = np.maximum(frac_total, destino)
        ref = frac_total >= CORTE_FRACAO
        for camada in ("cultivo_sequeiro", "cultivo_irrigado"):
            mapa = ler_camada(camada, 2020)
            linha = {
                "referencia": "ESA_WorldCover",
                "ano_referencia": 2020,
                "ano_cultivo": 2020,
                "camada": camada,
                **concordancia(mapa, ref),
            }
            linhas.append(linha)
            print(
                f"[ok] ESA WorldCover 2020 vs {camada}: jaccard={linha['jaccard']}",
                file=sys.stderr,
            )

    if not linhas:
        print(
            "[info] referências presentes mas sem ano-âncora de cultivo compatível",
            file=sys.stderr,
        )
        return 0

    SAIDA_CSV.parent.mkdir(parents=True, exist_ok=True)
    with SAIDA_CSV.open("w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=list(linhas[0].keys()))
        w.writeheader()
        w.writerows(linhas)

    escrever_proveniencia(linhas)
    print(f"[ok] {SAIDA_CSV.relative_to(REPO_ROOT)}", file=sys.stderr)
    return 0


def escrever_proveniencia(linhas: list[dict]) -> None:
    conteudo = [
        MARCADOR_INICIO,
        "",
        "## Validação externa de cultivo — GLAD Cropland / ESA WorldCover",
        "",
        "Gerado por `pipeline/01_imagery/validacao_externa_cultivo.py`. **Concordância, "
        "não acurácia** (mesma ressalva de `concordancia_ghsl` em `classificacao.py`): "
        "produtos com erro próprio, resolução e definição de cultivo diferentes.",
        "",
        "| referência | ano ref. | ano cultivo | camada | área mapa km² | área ref. km² | "
        "Jaccard | recall/ref. |",
        "|---|---|---|---|---|---|---|---|",
    ]
    for r in linhas:
        conteudo.append(
            f"| {r['referencia']} | {r['ano_referencia']} | {r['ano_cultivo']} | "
            f"{r['camada']} | {r['area_mapa_km2']} | {r['area_referencia_km2']} | "
            f"{r['jaccard']} | {r['recall_sobre_referencia']} |"
        )
    conteudo += [
        "",
        "Concordância baixa não piora o veredito de docs/ADR/0012 (`cultivo_sequeiro` já "
        "reprovado por interpretação visual própria); concordância alta seria evidência "
        "de apoio, não validação por si — ver limitações na docstring do script.",
        "",
        MARCADOR_FIM,
        "",
    ]
    atual = PROVENANCE_FRAGMENT.read_text(encoding="utf-8") if PROVENANCE_FRAGMENT.exists() else ""
    if MARCADOR_INICIO in atual and MARCADOR_FIM in atual:
        novo = atual.split(MARCADOR_INICIO)[0] + "\n".join(conteudo) + atual.split(MARCADOR_FIM)[1]
    else:
        novo = atual + "\n" + "\n".join(conteudo)
    PROVENANCE_FRAGMENT.parent.mkdir(parents=True, exist_ok=True)
    PROVENANCE_FRAGMENT.write_text(novo, encoding="utf-8")


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
