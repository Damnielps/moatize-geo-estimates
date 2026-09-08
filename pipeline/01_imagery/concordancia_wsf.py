#!/usr/bin/env python3
"""pipeline/01_imagery/concordancia_wsf.py — concordância entre a classificação
própria e o WSF Evolution (DLR), 2000–2015.

## Isto NÃO é acurácia, e o motivo é estrutural

O WSF Evolution **semeia os rótulos de treino** da classificação própria
(`classificacao.rotulos_treino`: positivos = WSF erodido 3×3). Comparar o
resultado com o WSF é, portanto, comparar um mapa com a sua própria semente:
qualquer concordância alta é em parte tautológica e qualquer discordância mede
o quanto o classificador se afastou da semente, não o quanto ele acerta o
terreno. Nenhum número deste arquivo pode ser lido como acurácia, nem entrar em
frase do tipo "o mapa tem X% de acerto".

O que o arquivo serve para dizer, e só isso: **quanto** a classificação própria
se afasta da semente, em que direção, e em que anos. É um diagnóstico de
comportamento do classificador.

## Papéis, para não haver dúvida

| produto | papel neste desenho |
|---|---|
| WSF Evolution | semente de treino; **excluído da validação por construção** |
| GHSL BUILT-S | referência externa, independente do treino; concordância em
  `concordancia_ghsl.csv` — também **não** é acurácia |
| interpretação visual de recortes | única base de acurácia
  (`acuracia_por_ano.csv`), com as limitações do ADR 0007 |

## Cobertura

O WSF Evolution termina em **2015**. Para 2020 e 2025 não existe linha: a
comparação seria contra um produto que não observa aqueles anos. Extrapolá-lo
seria inventar referência.

## Métricas

- `jaccard` = |A ∩ B| / |A ∪ B| sobre a máscara binária de construído
  (própria = urbano ∪ industrial ∪ reassentamento).
- `erro_relativo_area` = (área própria − área WSF) / área WSF. Sinal positivo =
  a classificação própria mapeia mais construído que a semente.

Uso: `uv run python pipeline/01_imagery/concordancia_wsf.py`
"""

from __future__ import annotations

import csv
import json
import sys
from datetime import UTC, datetime
from pathlib import Path

import numpy as np
import rasterio
import yaml

sys.path.insert(0, str(Path(__file__).resolve().parent))
from classificacao import ANO_FIM_WSF, carregar_wsf_reprojetado

REPO_ROOT = Path(__file__).resolve().parents[2]
STUDY_YAML = REPO_ROOT / "config" / "study.yaml"
DATA_PROCESSED = REPO_ROOT / "data" / "processed" / "imagery"
SAIDA_CSV = REPO_ROOT / "data" / "processed" / "concordancia_wsf.csv"

CAMADAS_CONSTRUIDO = ["urbano", "industrial", "reassentamento"]


def carregar_yaml(path: Path) -> dict:
    with path.open(encoding="utf-8") as fh:
        return yaml.safe_load(fh)


def mask_propria(ano: int, res_m: int, epsg: int) -> tuple[np.ndarray, dict]:
    mask = None
    perfil: dict = {}
    for camada in CAMADAS_CONSTRUIDO:
        caminho = DATA_PROCESSED / f"{camada}_{ano}_{res_m}m_{epsg}.tif"
        with rasterio.open(caminho) as src:
            arr = src.read(1).astype(bool)
            perfil = {
                "transform": src.transform,
                "crs": src.crs,
                "shape": src.shape,
                "width": src.width,
                "height": src.height,
            }
        mask = arr if mask is None else (mask | arr)
    assert mask is not None
    return mask, perfil


def main(argv: list[str]) -> int:
    estudo = carregar_yaml(STUDY_YAML)
    res_m = 30
    epsg = int(estudo["crs"]["metrico"].split(":")[-1])
    anos = [int(a) for a in argv] if argv else estudo["anos_ancora"]["imagem"]
    area_px_km2 = (res_m * res_m) / 1e6

    linhas = []
    for ano in sorted(anos):
        if ano > ANO_FIM_WSF:
            print(f"[skip] {ano}: WSF Evolution termina em {ANO_FIM_WSF}", file=sys.stderr)
            continue
        propria, perfil = mask_propria(ano, res_m, epsg)
        wsf = carregar_wsf_reprojetado(perfil)
        wsf_mask = (wsf > 0) & (wsf <= min(ano, ANO_FIM_WSF))

        inter = int((propria & wsf_mask).sum())
        uniao = int((propria | wsf_mask).sum())
        area_p = float(propria.sum()) * area_px_km2
        area_w = float(wsf_mask.sum()) * area_px_km2
        linhas.append(
            {
                "ano": ano,
                "area_propria_km2": round(area_p, 3),
                "area_wsf_km2": round(area_w, 3),
                "jaccard": round(inter / uniao, 4) if uniao else float("nan"),
                "erro_relativo_area": (
                    round((area_p - area_w) / area_w, 4) if area_w else float("nan")
                ),
                "e_acuracia": False,
                "papel_do_wsf": "semente de treino — dependência por construção",
                "nota": (
                    "concordância entre dois produtos, NÃO acurácia. O WSF Evolution "
                    "semeia os rótulos de treino desta classificação; a concordância é "
                    "em parte tautológica e a discordância mede afastamento da semente, "
                    "não erro contra o terreno. Acurácia está em acuracia_por_ano.csv."
                ),
            }
        )
        print(
            f"[ok] {ano}: jaccard {linhas[-1]['jaccard']:.3f} | "
            f"erro relativo de área {linhas[-1]['erro_relativo_area']:+.3f}",
            file=sys.stderr,
        )

    with SAIDA_CSV.open("w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=list(linhas[0].keys()))
        w.writeheader()
        w.writerows(linhas)

    SAIDA_CSV.with_suffix(".meta.json").write_text(
        json.dumps(
            {
                "e_acuracia": False,
                "papel_do_wsf": "semente de treino (classificacao.rotulos_treino)",
                "cobertura": f"1985-{ANO_FIM_WSF}; 2020 e 2025 ausentes por falta de referência",
                "saida": str(SAIDA_CSV.relative_to(REPO_ROOT)),
                "data_processamento": datetime.now(UTC).isoformat(),
                "script": "pipeline/01_imagery/concordancia_wsf.py",
            },
            indent=2,
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    print(f"[ok] {SAIDA_CSV.relative_to(REPO_ROOT)}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
