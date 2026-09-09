#!/usr/bin/env python3
"""pipeline/01_imagery/cultivo_varzea.py — cruzamento cultivo × várzea (§3, H5).

§3 chama de "cultivo de vazante" o cultivo de estação seca em planície aluvial. Este
script cruza, por ano-âncora, as camadas `cultivo_irrigado`/`cultivo_sequeiro`
(`cultivo.py`, dinâmicas) com `varzea` (`varzea.py`, estática) e publica a fração de
cada classe de cultivo que cai dentro da várzea — o número que sustenta ou refuta H5
("a agricultura persiste em várzeas do Zambeze e do Revúbuè").

Não classifica nada novo: só soma pixels de camadas já gravadas em
`data/processed/imagery/`.

Uso: `uv run python pipeline/01_imagery/cultivo_varzea.py [ano ...]`
"""

from __future__ import annotations

import csv
import sys
from pathlib import Path

import numpy as np
import rasterio

REPO_ROOT = Path(__file__).resolve().parents[2]
DATA_PROCESSED = REPO_ROOT / "data" / "processed" / "imagery"
SAIDA_CSV = REPO_ROOT / "data" / "processed" / "cultivo_varzea_por_ano.csv"
ANOS_ANCORA = [2000, 2005, 2010, 2015, 2020, 2025]
RES_M, EPSG = 30, 32736


def ler_mask(nome: str, ano: int | None) -> np.ndarray:
    sufixo = f"_{ano}" if ano is not None else ""
    caminho = DATA_PROCESSED / f"{nome}{sufixo}_{RES_M}m_{EPSG}.tif"
    if not caminho.exists():
        raise FileNotFoundError(f"{caminho} ausente — rode cultivo.py e varzea.py antes")
    with rasterio.open(caminho) as src:
        mask = src.read(1).astype(bool)
        transform = src.transform
    return mask, transform


def area_km2(mask: np.ndarray, transform) -> float:
    return float(mask.sum()) * abs(transform.a * transform.e) / 1e6


def main(argv: list[str]) -> int:
    anos = [int(a) for a in argv] if argv else ANOS_ANCORA
    varzea, transform = ler_mask("varzea", None)
    area_varzea = area_km2(varzea, transform)

    linhas = []
    for ano in anos:
        seq, _ = ler_mask("cultivo_sequeiro", ano)
        irr, _ = ler_mask("cultivo_irrigado", ano)
        seq_varzea = seq & varzea
        irr_varzea = irr & varzea
        linhas.append(
            {
                "ano": ano,
                "area_varzea_km2": round(area_varzea, 3),
                "cultivo_sequeiro_km2": round(area_km2(seq, transform), 3),
                "cultivo_sequeiro_em_varzea_km2": round(area_km2(seq_varzea, transform), 3),
                "fracao_sequeiro_em_varzea": (
                    round(float(seq_varzea.sum()) / seq.sum(), 4) if seq.sum() else 0.0
                ),
                "cultivo_irrigado_km2": round(area_km2(irr, transform), 3),
                "cultivo_irrigado_em_varzea_km2": round(area_km2(irr_varzea, transform), 3),
                "fracao_irrigado_em_varzea": (
                    round(float(irr_varzea.sum()) / irr.sum(), 4) if irr.sum() else 0.0
                ),
                "fracao_varzea_cultivada": (
                    round(float((seq_varzea | irr_varzea).sum()) / varzea.sum(), 4)
                    if varzea.sum()
                    else 0.0
                ),
                "selo": "observado",
                "nota": (
                    "varzea é camada ESTÁTICA (HAND aproximado, ver varzea.py); "
                    "fracao_*_em_varzea = fração da área da classe de cultivo do ano que "
                    "cai dentro da várzea — sustenta H5 se alta e estável; "
                    "fracao_varzea_cultivada = fração da várzea coberta por cultivo "
                    "(irrigado OU sequeiro) no ano."
                ),
            }
        )
        print(f"[ok] {ano}: sequeiro em várzea={linhas[-1]['fracao_sequeiro_em_varzea']:.2%} "
              f"irrigado em várzea={linhas[-1]['fracao_irrigado_em_varzea']:.2%}",
              file=sys.stderr)

    SAIDA_CSV.parent.mkdir(parents=True, exist_ok=True)
    with SAIDA_CSV.open("w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=list(linhas[0].keys()))
        w.writeheader()
        w.writerows(linhas)
    print(f"[ok] {SAIDA_CSV.relative_to(REPO_ROOT)}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
