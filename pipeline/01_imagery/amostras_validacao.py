#!/usr/bin/env python3
"""pipeline/01_imagery/amostras_validacao.py — sorteia os pontos de validação e
renderiza os recortes RGB para interpretação visual (§5.1, §10).

## O que este script produz e o que NÃO produz

Produz: (a) `data/processed/validacao/pontos_validacao.csv` com os pontos
sorteados e a classe **mapeada** de cada um, e (b) folhas de contato PNG em
`data/processed/validacao/chips/` — uma grade de recortes RGB numerados, um por
ponto, para interpretação visual.

**Não** produz o rótulo de referência. O rótulo é atribuído olhando os recortes
e gravado à parte em `data/processed/validacao/rotulos_interpretados.csv`, com
o intérprete identificado. Separar as duas coisas é proposital: quem sorteia não
rotula, e o rótulo é rastreável a uma imagem concreta.

## Desenho amostral

- **Estratos:** dois, definidos pelo **mapa** (não pela referência):
  `construido` (artefato próprio; desde docs/ADR/0011 NÃO é a união das três
  camadas — `industrial` e `reassentamento` deixaram de ser subconjuntos de
  construído) e
  `nao_construido`. Estratificar pelo mapa é o que permite usar o estimador de
  Olofsson et al. (2014) para recuperar acurácia global **ponderada pela área
  real de cada estrato**, apesar de o construído ser raro (~1–2% da AOI). Uma
  amostra proporcional colocaria ~1 ponto construído por ano — inútil.
- **n por estrato por ano:** `N_POR_ESTRATO`. É pouco, e a razão é declarada:
  cada ponto exige interpretação visual de um recorte, e não há intérprete
  humano nem verdade de campo neste ambiente. O intervalo de confiança
  resultante é largo e reportado como tal por `acuracia.py` — número honesto com
  incerteza declarada, em vez de n grande obtido por regra automática (que foi
  exatamente o que reprovou a versão anterior).
- **Sorteio:** aleatório simples dentro de cada estrato, seed
  `config/seeds.yaml -> pontos_validacao.seed`, independente da seed de treino.

## Recortes

Janela de `LADO_CHIP_PX` × `LADO_CHIP_PX` pixels de 30 m (~0,9 km de lado)
centrada no ponto, do composto de estação seca **do próprio ano** (mesma imagem
que alimentou a classificação — a interpretação vê o mesmo dado, e não uma
imagem melhor de outra data, o que superestimaria a dificuldade real ou a
facilitaria indevidamente). Composição R=SWIR16, G=NIR, B=vermelho: nessa
combinação, construído e solo exposto ficam em tons distintos (construído
magenta/cinza, vegetação verde/laranja, solo rosado claro), o que a composição
cor-verdadeira a 30 m não separa. Contraste por percentis 2–98 **do próprio
recorte** (ver `esticar_recorte` para as três alternativas globais testadas e
descartadas, e para a limitação que a escolha impõe).

Limitação intrínseca, que nenhuma escolha de renderização remove: a 30 m, um
único pixel de construído esparso é frequentemente indistinguível de solo
exposto **para qualquer intérprete**. O ponto central é marcado por quatro
ticks nos cantos, nunca sobre o pixel.

Uso: `uv run python pipeline/01_imagery/amostras_validacao.py [ano ...]`
"""

from __future__ import annotations

import csv
import json
import sys
from datetime import UTC, datetime
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import rasterio
import yaml

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "00_fetch"))
from _config import carregar_estudo

REPO_ROOT = Path(__file__).resolve().parents[2]
STUDY_YAML = REPO_ROOT / "config" / "study.yaml"
SEEDS_YAML = REPO_ROOT / "config" / "seeds.yaml"
DATA_PROCESSED = REPO_ROOT / "data" / "processed" / "imagery"
DIR_VALIDACAO = REPO_ROOT / "data" / "processed" / "validacao"
DIR_CHIPS = DIR_VALIDACAO / "chips"
PONTOS_CSV = DIR_VALIDACAO / "pontos_validacao.csv"

# docs/ADR/0011: `industrial` e `reassentamento` deixaram de ser subconjuntos de
# `construido` — passaram a ser PEGADAS, com rocha e solo exposto que nenhum
# classificador de construído captura. Estratificar a validação pela união das três
# camadas passaria a jogar cava e pilha de estéril dentro do estrato `construido`, e
# o intérprete visual (corretamente) os leria como não construídos: a comissão
# medida seria a de um objeto que a camada nunca prometeu ser. O estrato passa a ser
# a máscara de construído propriamente dita, persistida por classificacao.py.
CAMADA_CONSTRUIDO = "construido"
LADO_CHIP_PX = 31
LADO_CONTEXTO_PX = 101
CHIPS_POR_FOLHA = 12
COLUNAS_FOLHA = 3
BANDAS_RGB = ("swir16", "nir", "red")


def carregar_yaml(path: Path) -> dict:
    with path.open(encoding="utf-8") as fh:
        return yaml.safe_load(fh)


def mask_construido(ano: int, res_m: int, epsg: int) -> tuple[np.ndarray, dict]:
    caminho = DATA_PROCESSED / f"{CAMADA_CONSTRUIDO}_{ano}_{res_m}m_{epsg}.tif"
    with rasterio.open(caminho) as src:
        mask = src.read(1).astype(bool)
        perfil = {"transform": src.transform, "crs": src.crs, "shape": src.shape}
    return mask, perfil


def carregar_rgb(ano: int, res_m: int, epsg: int) -> np.ndarray:
    caminho = DATA_PROCESSED / f"composto_{ano}_{res_m}m_{epsg}.tif"
    with rasterio.open(caminho) as src:
        descricoes = list(src.descriptions)
        canais = []
        for nome in BANDAS_RGB:
            idx = descricoes.index(nome) + 1
            canais.append(src.read(idx, masked=True).filled(np.nan))
    return np.stack(canais, axis=-1)


def escala_aoi(rgb: np.ndarray) -> np.ndarray:
    """Percentis 2–98 da AOI por banda — base de cor comum a todos os recortes."""
    return np.array([np.nanpercentile(rgb[..., i], [2, 98]) for i in range(3)])


def esticar_recorte(
    recorte: np.ndarray,
    escala: np.ndarray,
    piso_amp: float = 0.30,
    ganho: tuple[float, float] | None = None,
) -> np.ndarray | tuple[np.ndarray, tuple[float, float]]:
    """Normalização de cor **global** seguida de ganho local **comum às bandas**.

    Histórico das tentativas, porque a escolha determina o que se consegue ver:

    - percentis 2–98 globais à AOI, sem ganho local: quase todo recorte cai numa
      faixa estreita no meio da rampa e sai lavado, sem textura;
    - percentis 10–90 globais: as bandas são muito correlacionadas na savana
      seca, o pixel claro satura nas três ao mesmo tempo e o recorte vira branco;
    - equalização de histograma por banda sobre a AOI: o construído **é** o
      extremo brilhante da AOI (medido: percentis 88–99), logo satura no topo da
      rampa qualquer que seja o esticamento global;
    - percentis 2–98 **do próprio recorte, banda a banda** (versão anterior):
      falhou por um motivo diferente e pior. Esticar cada banda contra o próprio
      intervalo local **decorrelaciona as bandas**: o ruído independente de cada
      banda é amplificado por um ganho diferente e vira cor. Medido nos recortes
      de 2000, o resultado é um mosaico de pontos vermelhos, azuis e verdes sem
      relação com a superfície, sobre o qual não se rotula nada.

    Adotado: normalizar primeiro pelos percentis 2–98 **da AOI** (mantém a
    relação entre bandas e, portanto, a cor do alvo: construído magenta/cinza
    claro, vegetação verde, água escura, solo rosado), e só então aplicar **um
    único** ganho linear local, calculado sobre a média das três bandas
    normalizadas. Como o mesmo ganho vale para as três, ruído correlacionado
    continua cinza e não vira cor; o que ganha contraste é a estrutura.

    O ganho pode ser **imposto de fora** (`ganho`): as duas janelas de um mesmo
    ponto — contexto e detalhe — usam o ganho calculado sobre o **contexto**, de
    modo que o detalhe mostre o contraste do pixel em relação à sua vizinhança
    real, e não em relação a si mesmo. Sem isso, um recorte de detalhe uniforme
    ganharia contraste artificial e pareceria estruturado.

    `piso_amp` é a amplitude mínima, em fração da amplitude da AOI, que o ganho
    local pode assumir. Sem esse piso, um recorte espectralmente homogêneo — que
    é justamente a informação "aqui não há nada" — teria seu ruído esticado até
    ocupar a rampa inteira e pareceria estruturado. Com o piso, recorte
    homogêneo sai homogêneo.

    Deliberadamente **não** se anota no recorte nenhum valor de índice espectral
    (NDVI, NDBI, amplitude): seriam as mesmas variáveis que alimentam o
    classificador, e olhá-las ao rotular reintroduziria a circularidade que
    reprovou a versão anterior desta validação.
    """
    base = np.zeros_like(recorte)
    for i in range(3):
        lo, hi = escala[i]
        base[..., i] = (recorte[..., i] - lo) / max(hi - lo, 1e-6)

    if ganho is None:
        cinza = np.nanmean(base, axis=-1)
        if np.isfinite(cinza).any():
            g_lo, g_hi = np.nanpercentile(cinza, [2, 98])
        else:
            g_lo, g_hi = 0.0, 1.0
        amp = max(float(g_hi - g_lo), piso_amp)
        lo = float(g_lo + g_hi) / 2.0 - amp / 2.0
        ganho = (lo, amp)
    lo, amp = ganho

    saida = np.nan_to_num(np.clip((base - lo) / amp, 0, 1), nan=0.0)
    return saida, ganho


def sortear_pontos(ano: int, res_m: int, epsg: int, seed: int, n_por_estrato: int) -> list[dict]:
    construido, perfil = mask_construido(ano, res_m, epsg)
    rng = np.random.default_rng(seed + ano)  # ano entra na seed: estratos diferem por ano

    pontos = []
    for estrato, mask in (("construido", construido), ("nao_construido", ~construido)):
        linhas, colunas = np.where(mask)
        # margem: a janela de CONTEXTO (a maior das duas) precisa caber inteira na
        # grade, senão o recorte sai truncado e o ponto fica sem evidência
        margem = LADO_CONTEXTO_PX // 2
        dentro = (
            (linhas >= margem)
            & (linhas < perfil["shape"][0] - margem)
            & (colunas >= margem)
            & (colunas < perfil["shape"][1] - margem)
        )
        linhas, colunas = linhas[dentro], colunas[dentro]
        n = min(n_por_estrato, linhas.size)
        escolhidos = rng.choice(linhas.size, size=n, replace=False)
        for k in escolhidos:
            lin, col = int(linhas[k]), int(colunas[k])
            x, y = perfil["transform"] * (col + 0.5, lin + 0.5)
            pontos.append(
                {
                    "ano": ano,
                    "estrato_mapeado": estrato,
                    "linha": lin,
                    "coluna": col,
                    "x_utm36s": round(x, 1),
                    "y_utm36s": round(y, 1),
                }
            )
    # ordem determinística e id estável
    pontos.sort(key=lambda p: (p["estrato_mapeado"], p["linha"], p["coluna"]))
    for i, p in enumerate(pontos, start=1):
        p["id_ponto"] = f"{ano}-{i:03d}"

    # --- cegamento do intérprete ---
    # `id_ponto` é atribuído após ordenar por estrato: 001..024 são sempre do
    # estrato `construido` e 025..048 do `nao_construido`. Se a folha de contato
    # exibisse esse id, ou se os recortes fossem renderizados nessa ordem, o
    # intérprete saberia a classe do mapa antes de olhar o recorte — e a
    # concordância medida ficaria inflada por essa pista, não pelo sinal da
    # imagem. Por isso os pontos recebem um segundo identificador, `id_cego`,
    # atribuído sobre uma permutação determinística que mistura os dois
    # estratos; as folhas mostram só `id_cego`, e o vínculo id_cego -> estrato
    # existe apenas no CSV, que não é olhado durante a interpretação.
    ordem = rng.permutation(len(pontos))
    for k, idx in enumerate(ordem, start=1):
        pontos[int(idx)]["id_cego"] = f"{ano}-C{k:03d}"
    return pontos


def _recorte(rgb: np.ndarray, lin: int, col: int, lado: int) -> np.ndarray:
    m = lado // 2
    return rgb[lin - m : lin + m + 1, col - m : col + m + 1]


def renderizar_folhas(ano: int, pontos: list[dict], rgb: np.ndarray) -> list[Path]:
    """Duas janelas por ponto: contexto (~3 km) e detalhe (~0,9 km).

    A janela de detalhe é a evidência principal; a de contexto existe porque a
    decisão "este pixel é construído" a 30 m depende de padrão de ocupação —
    estar dentro de uma malha, na borda de um povoado, junto a uma via ou
    isolado no mato muda o julgamento, e a janela de 0,9 km não mostra isso.
    Nenhuma das duas expõe variável do classificador.
    """
    DIR_CHIPS.mkdir(parents=True, exist_ok=True)
    escala = escala_aoi(rgb)
    caminhos = []
    # ordem de exibição = ordem cega (estratos misturados); ver sortear_pontos
    pontos = sorted(pontos, key=lambda p: p["id_cego"])
    m_ctx, m_det = LADO_CONTEXTO_PX // 2, LADO_CHIP_PX // 2
    for inicio in range(0, len(pontos), CHIPS_POR_FOLHA):
        lote = pontos[inicio : inicio + CHIPS_POR_FOLHA]
        pares_por_linha = COLUNAS_FOLHA
        linhas_grade = int(np.ceil(len(lote) / pares_por_linha))
        fig, eixos = plt.subplots(
            linhas_grade,
            pares_por_linha * 2,
            figsize=(pares_por_linha * 2 * 2.7, linhas_grade * 3.1),
        )
        eixos = np.atleast_2d(eixos)
        for ax in eixos.ravel():
            ax.axis("off")
        for j, ponto in enumerate(lote):
            lin, col = ponto["linha"], ponto["coluna"]
            r, c = j // pares_por_linha, (j % pares_por_linha) * 2

            ax = eixos[r, c]
            ctx = _recorte(rgb, lin, col, LADO_CONTEXTO_PX)
            img_ctx, ganho = esticar_recorte(ctx, escala)
            ax.imshow(img_ctx, interpolation="nearest")
            ax.add_patch(
                plt.Rectangle(
                    (m_ctx - m_det - 0.5, m_ctx - m_det - 0.5),
                    LADO_CHIP_PX,
                    LADO_CHIP_PX,
                    fill=False,
                    edgecolor="yellow",
                    linewidth=0.9,
                )
            )
            ax.set_title(f"{ponto['id_cego']} · contexto 3,0 km", fontsize=7)
            ax.axis("off")

            ax = eixos[r, c + 1]
            det = _recorte(rgb, lin, col, LADO_CHIP_PX)
            ax.imshow(esticar_recorte(det, escala, ganho=ganho)[0], interpolation="nearest")
            for dx, dy in ((-3, 0), (3, 0), (0, -3), (0, 3)):
                ax.plot(
                    [m_det + dx * 0.9], [m_det + dy * 0.9], marker="+", color="yellow", ms=6
                )
            ax.set_title(f"{ponto['id_cego']} · detalhe 0,9 km", fontsize=7)
            ax.axis("off")
        fig.suptitle(
            f"{ano} — R=SWIR1 G=NIR B=vermelho, 30 m — cruz marca o pixel avaliado; "
            "retângulo no contexto = janela de detalhe",
            fontsize=9,
        )
        fig.tight_layout()
        caminho = DIR_CHIPS / f"folha_{ano}_{inicio // CHIPS_POR_FOLHA + 1:02d}.png"
        fig.savefig(caminho, dpi=150)
        plt.close(fig)
        caminhos.append(caminho)
    return caminhos


def main(argv: list[str]) -> int:
    estudo = carregar_estudo(STUDY_YAML)
    seeds_cfg = carregar_yaml(SEEDS_YAML)
    cfg_acuracia = estudo["acuracia"]
    n_por_estrato = int(cfg_acuracia["n_pontos_interpretados_por_estrato_ano"])
    seed = int(seeds_cfg["pontos_validacao"]["seed"])

    anos = [int(a) for a in argv] if argv else estudo["anos_ancora"]["imagem"]
    res_m = 30
    epsg = int(estudo["crs"]["metrico"].split(":")[-1])

    todos: list[dict] = []
    folhas: list[str] = []
    for ano in anos:
        pontos = sortear_pontos(ano, res_m, epsg, seed, n_por_estrato)
        rgb = carregar_rgb(ano, res_m, epsg)
        folhas += [str(p.relative_to(REPO_ROOT)) for p in renderizar_folhas(ano, pontos, rgb)]
        todos += pontos
        print(f"[ok] {ano}: {len(pontos)} pontos", file=sys.stderr)

    DIR_VALIDACAO.mkdir(parents=True, exist_ok=True)
    campos = [
        "id_ponto",
        "id_cego",
        "ano",
        "estrato_mapeado",
        "linha",
        "coluna",
        "x_utm36s",
        "y_utm36s",
    ]
    with PONTOS_CSV.open("w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=campos)
        w.writeheader()
        for p in todos:
            w.writerow({c: p[c] for c in campos})

    (DIR_VALIDACAO / "pontos_validacao.meta.json").write_text(
        json.dumps(
            {
                "desenho": "estratificado pelo MAPA em construido/nao_construido",
                "n_por_estrato_por_ano": n_por_estrato,
                "seed": seed,
                "seed_efetiva_por_ano": "pontos_validacao.seed + ano",
                "cegamento": (
                    "as folhas exibem id_cego, atribuído sobre permutação determinística "
                    "que mistura os dois estratos; o intérprete não sabe a classe do mapa "
                    "ao olhar o recorte"
                ),
                "lado_chip_px": LADO_CHIP_PX,
                "lado_contexto_px": LADO_CONTEXTO_PX,
                "resolucao_m": res_m,
                "composicao_rgb": list(BANDAS_RGB),
                "imagem_interpretada": (
                    "composto de estação seca do próprio ano, 30 m, EPSG:32736 — a mesma "
                    "imagem que alimentou a classificação"
                ),
                "folhas_de_contato": folhas,
                "estimador_previsto": "Olofsson et al. (2014), estratificado pelo mapa",
                "aviso": (
                    "este arquivo não contém rótulo de referência; ver "
                    "rotulos_interpretados.csv"
                ),
                "data_geracao": datetime.now(UTC).isoformat(),
                "script": "pipeline/01_imagery/amostras_validacao.py",
            },
            indent=2,
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    print(f"[ok] {PONTOS_CSV.relative_to(REPO_ROOT)} e {len(folhas)} folhas", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
