#!/usr/bin/env python3
"""pipeline/01_imagery/amostras_validacao_cultivo.py — pontos e recortes para a
validação por interpretação visual de `cultivo_sequeiro`/`cultivo_irrigado` (§5.6.1,
§10, ADR 0007/0009 reaproveitados para uma classe nova).

## Por que o desenho é menor que o de `amostras_validacao.py` (construído)

A validação de `construido` cobre os 6 anos-âncora com 24 pontos/estrato/ano (288
pontos, ADR 0007) porque a série de área construída é o produto central da Fase 1. A
classificação de cultivo é uma entrega derivada, com o mesmo custo por ponto
(interpretação visual manual, um a um, sem verdade de campo) e sem orçamento para
replicar 288 pontos por classe nova. A escolha, declarada:

- **um único ano-âncora**, 2020 — meio da série, com as duas classes presentes em
  proporção que não deixa nenhuma delas residual (`cultivo_sequeiro` 361,0 km²,
  `cultivo_irrigado` 51,5 km² em `data/processed/cultivo_por_ano.csv`), e sensor L8+S2
  (mesma geração usada em 2015/2025, o que dá alguma generalização, embora não
  comprovada, aos anos vizinhos de mesmo sensor);
- **N_POR_ESTRATO menor** que o de construído — 12, não 24.

**Consequência aritmética, aceita e declarada:** o resultado NÃO é uma acurácia por ano
por classe ao longo da série, como §10 pede para a classificação de construído. É uma
acurácia pontual, medida em um ano, com um intervalo de confiança maior do que o de
`construido`. `acuracia_cultivo.py` reporta isso explicitamente e não estende o número
aos outros cinco anos-âncora.

## Estratos e recortes

Três estratos, definidos pelo MAPA: `cultivo_sequeiro`, `cultivo_irrigado`, `outro`
(todo o resto — urbano, industrial, reassentamento, água, e o que sobra de vegetacao/
solo_exposto fora do recorte fenológico). Recortes: mesma composição RGB (SWIR1/NIR/
vermelho), mesmas duas janelas (contexto 3,0 km e detalhe 0,9 km) e mesmo cegamento por
`id_cego` de `amostras_validacao.py` — reaproveitados por import, não reescritos.

Uso: `uv run python pipeline/01_imagery/amostras_validacao_cultivo.py [ano]`
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
from amostras_validacao import carregar_rgb, escala_aoi, esticar_recorte

REPO_ROOT = Path(__file__).resolve().parents[2]
SEEDS_YAML = REPO_ROOT / "config" / "seeds.yaml"
DATA_PROCESSED = REPO_ROOT / "data" / "processed" / "imagery"
DIR_VALIDACAO = REPO_ROOT / "data" / "processed" / "validacao"
DIR_CHIPS = DIR_VALIDACAO / "chips_cultivo"
PONTOS_CSV = DIR_VALIDACAO / "pontos_validacao_cultivo.csv"

ANO_PADRAO = 2020
N_POR_ESTRATO = 12
LADO_CHIP_PX = 31
LADO_CONTEXTO_PX = 101
CHIPS_POR_FOLHA = 12
COLUNAS_FOLHA = 3
RES_M, EPSG = 30, 32736
ESTRATOS = ["cultivo_sequeiro", "cultivo_irrigado", "outro"]


def carregar_yaml(path: Path) -> dict:
    with path.open(encoding="utf-8") as fh:
        return yaml.safe_load(fh)


def mask_estratos(ano: int) -> tuple[dict[str, np.ndarray], dict]:
    def ler(nome):
        with rasterio.open(DATA_PROCESSED / f"{nome}_{ano}_{RES_M}m_{EPSG}.tif") as src:
            return src.read(1).astype(bool), {
                "transform": src.transform, "crs": src.crs, "shape": src.shape
            }

    seq, perfil = ler("cultivo_sequeiro")
    irr, _ = ler("cultivo_irrigado")
    outro = ~(seq | irr)
    return {"cultivo_sequeiro": seq, "cultivo_irrigado": irr, "outro": outro}, perfil


def sortear_pontos(ano: int, masks: dict[str, np.ndarray], perfil: dict, seed: int) -> list[dict]:
    rng = np.random.default_rng(seed + ano)
    margem = LADO_CONTEXTO_PX // 2
    pontos = []
    for estrato in ESTRATOS:
        linhas, colunas = np.where(masks[estrato])
        dentro = (
            (linhas >= margem)
            & (linhas < perfil["shape"][0] - margem)
            & (colunas >= margem)
            & (colunas < perfil["shape"][1] - margem)
        )
        linhas, colunas = linhas[dentro], colunas[dentro]
        n = min(N_POR_ESTRATO, linhas.size)
        escolhidos = rng.choice(linhas.size, size=n, replace=False)
        for k in escolhidos:
            lin, col = int(linhas[k]), int(colunas[k])
            x, y = perfil["transform"] * (col + 0.5, lin + 0.5)
            pontos.append(
                {
                    "ano": ano, "estrato_mapeado": estrato, "linha": lin, "coluna": col,
                    "x_utm36s": round(x, 1), "y_utm36s": round(y, 1),
                }
            )
    pontos.sort(key=lambda p: (p["estrato_mapeado"], p["linha"], p["coluna"]))
    for i, p in enumerate(pontos, start=1):
        p["id_ponto"] = f"cult{ano}-{i:03d}"
    ordem = rng.permutation(len(pontos))
    for k, idx in enumerate(ordem, start=1):
        pontos[int(idx)]["id_cego"] = f"cult{ano}-C{k:03d}"
    return pontos


def _recorte(rgb: np.ndarray, lin: int, col: int, lado: int) -> np.ndarray:
    m = lado // 2
    return rgb[lin - m : lin + m + 1, col - m : col + m + 1]


def renderizar_folhas(ano: int, pontos: list[dict], rgb: np.ndarray) -> list[Path]:
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    DIR_CHIPS.mkdir(parents=True, exist_ok=True)
    escala = escala_aoi(rgb)
    caminhos = []
    pontos = sorted(pontos, key=lambda p: p["id_cego"])
    m_ctx, m_det = LADO_CONTEXTO_PX // 2, LADO_CHIP_PX // 2
    for inicio in range(0, len(pontos), CHIPS_POR_FOLHA):
        lote = pontos[inicio : inicio + CHIPS_POR_FOLHA]
        linhas_grade = int(np.ceil(len(lote) / COLUNAS_FOLHA))
        fig, eixos = plt.subplots(
            linhas_grade, COLUNAS_FOLHA * 2,
            figsize=(COLUNAS_FOLHA * 2 * 2.7, linhas_grade * 3.1),
        )
        eixos = np.atleast_2d(eixos)
        for ax in eixos.ravel():
            ax.axis("off")
        for j, ponto in enumerate(lote):
            lin, col = ponto["linha"], ponto["coluna"]
            r, c = j // COLUNAS_FOLHA, (j % COLUNAS_FOLHA) * 2
            ax = eixos[r, c]
            ctx = _recorte(rgb, lin, col, LADO_CONTEXTO_PX)
            img_ctx, ganho = esticar_recorte(ctx, escala)
            ax.imshow(img_ctx, interpolation="nearest")
            ax.add_patch(
                plt.Rectangle(
                    (m_ctx - m_det - 0.5, m_ctx - m_det - 0.5), LADO_CHIP_PX, LADO_CHIP_PX,
                    fill=False, edgecolor="yellow", linewidth=0.9,
                )
            )
            ax.set_title(f"{ponto['id_cego']} · contexto 3,0 km", fontsize=7)
            ax.axis("off")
            ax = eixos[r, c + 1]
            det = _recorte(rgb, lin, col, LADO_CHIP_PX)
            ax.imshow(esticar_recorte(det, escala, ganho=ganho)[0], interpolation="nearest")
            for dx, dy in ((-3, 0), (3, 0), (0, -3), (0, 3)):
                ax.plot([m_det + dx * 0.9], [m_det + dy * 0.9], marker="+", color="yellow", ms=6)
            ax.set_title(f"{ponto['id_cego']} · detalhe 0,9 km", fontsize=7)
            ax.axis("off")
        fig.suptitle(
            f"{ano} — cultivo — R=SWIR1 G=NIR B=vermelho, 30 m — cruz marca o pixel avaliado",
            fontsize=9,
        )
        fig.tight_layout()
        caminho = DIR_CHIPS / f"folha_cultivo_{ano}_{inicio // CHIPS_POR_FOLHA + 1:02d}.png"
        fig.savefig(caminho, dpi=150)
        plt.close(fig)
        caminhos.append(caminho)
    return caminhos


def main(argv: list[str]) -> int:
    seeds_cfg = carregar_yaml(SEEDS_YAML)
    # +1: independente do sorteio de construído (amostras_validacao.py)
    seed = int(seeds_cfg["pontos_validacao"]["seed"]) + 1
    ano = int(argv[0]) if argv else ANO_PADRAO

    masks, perfil = mask_estratos(ano)
    pontos = sortear_pontos(ano, masks, perfil, seed)
    rgb = carregar_rgb(ano, RES_M, EPSG)
    folhas = renderizar_folhas(ano, pontos, rgb)

    DIR_VALIDACAO.mkdir(parents=True, exist_ok=True)
    campos = ["id_ponto", "id_cego", "ano", "estrato_mapeado", "linha", "coluna",
              "x_utm36s", "y_utm36s"]
    with PONTOS_CSV.open("w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=campos)
        w.writeheader()
        for p in pontos:
            w.writerow({c: p[c] for c in campos})

    (DIR_VALIDACAO / "pontos_validacao_cultivo.meta.json").write_text(
        json.dumps(
            {
                "ano_unico": ano,
                "motivo_ano_unico": (
                    "custo de interpretação visual manual, sem verdade de campo; ver "
                    "docstring de amostras_validacao_cultivo.py"
                ),
                "estratos": ESTRATOS,
                "n_por_estrato": N_POR_ESTRATO,
                "seed": seed,
                "folhas_de_contato": [str(p.relative_to(REPO_ROOT)) for p in folhas],
                "data_geracao": datetime.now(UTC).isoformat(),
                "script": "pipeline/01_imagery/amostras_validacao_cultivo.py",
            },
            indent=2, ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    print(f"[ok] {PONTOS_CSV.relative_to(REPO_ROOT)} — {len(pontos)} pontos, "
          f"{len(folhas)} folhas", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
