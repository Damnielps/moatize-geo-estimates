#!/usr/bin/env python3
"""pipeline/04_figures/gif_mancha.py — GIF animado da progressão da mancha urbana.

Substitui a captura de tela do app (Puppeteer, fora do pipeline) por um artefato
gerado deterministicamente a partir de `data/processed/app/imagery/` — os mesmos
GeoJSON simplificados que o app consome (§6, `data/processed/app/imagery/manifest.json`).

## Insumos

- Por ano-âncora (2000, 2005, 2010, 2015, 2020, 2025): `urbano`, `industrial`,
  `reassentamento`, `cultivo_irrigado`, `agua`.
- Estáticos: `varzea`, `osm_vias`, `osm_ferrovia`, `osm_lugares` (topônimos),
  `osm_aerodromo`.
- Excluídos (como no `.meta.json` anterior, gerado pela captura de tela):
  `cultivo_sequeiro` (vegetação sazonal não confirmada como cultivo) e
  `adensamento_2020_2025` (modelado, ADR 0016 — não é a mesma pergunta que este GIF
  responde).

## Estilo

Cores das classes de uso do solo lidas de `config/paleta_uso_solo.yaml` — a mesma fonte
que o app consome via `pipeline/05_app/gerar_paleta.py` / `app/src/lib/camadasBase.js`
(ADR 0018: legenda ESA WorldCover/FAO LCCS, com adaptações declaradas). Nenhum hex de
classe é escrito neste script: `reassentamento` e `industrial` levam o contorno
(`contorno`) do YAML, como no app; `varzea` usa a `opacidade` do YAML. Cores de contexto
(vias, ferrovia, aeródromo, topônimos, fundo do mapa) vêm da seção `contexto` do mesmo
YAML. Paleta de texto e fundo do Sistema Ardósia (`_paleta_ardosia.py`, vendorizado sem
alteração) continua reservada ao que não é classe de uso do solo (ano em destaque,
legenda, rodapé).

## Enquadramento

Mesmo bbox em todos os quadros — a AOI de `config/study.yaml` (`aoi.bbox`), em
EPSG:4326 (CRS de exibição, §11.2.1 e convenção do repositório). Os dados de
`data/processed/app/imagery/` já nascem em EPSG:4326 (ver `manifest.json`). "Projetado
para exibição" aqui significa: eixo com razão de aspecto corrigida pela latitude média
da AOI (`1/cos(lat_media)`), a mesma distorção equirretangular que o MapLibre do app
aplica por default a esta escala — não é a reprojeção métrica de EPSG:32736 (reservada
a cálculo de área, nunca usada para exibição, §11.2.1).

## Churn do par temporal (ADR 0013)

`manifest.json` chave `churn_pares_temporais` traz, por par de anos-âncora consecutivo
e por classe, o churn (1 − Jaccard) do **rótulo bruto do classificador**, antes de
R1 (área mínima) e R2 (permanência) e antes do corte em `urbano`/`industrial`/
`reassentamento` — EXPERIMENTAL, não substitui nenhum artefato publicado (nota do
próprio manifesto). Este GIF expõe, a partir do 2º quadro, o valor da classe
`construido` para o par (ano_anterior, ano_atual), em texto miúdo, com a ressalva.

## Determinismo

- Nenhum download, nenhum RNG.
- `matplotlib`: rcParams reiniciados para o default embutido na versão travada em
  `uv.lock` (`rcdefaults()` ignora `matplotlibrc` do usuário) antes do estilo Ardósia;
  backend Agg por `FigureCanvasAgg`, sem pyplot; figsize/dpi fixos; sem
  `bbox_inches="tight"`; o raster RGBA sai direto do buffer do Agg, sem PNG
  intermediário.
- Fonte: SOMENTE os TTF DejaVu embutidos no próprio pacote matplotlib
  (`matplotlib/mpl-data/fonts/ttf/`), carregados por caminho de arquivo
  (`FontProperties(fname=...)`), nunca por nome de família resolvido contra o sistema.
  `verificar_fontes()` falha se qualquer texto do quadro tiver outra origem. A lista
  `SERIF` de `_paleta_ardosia.py` NÃO é usada aqui: nela o 1º nome disponível no macOS
  era "Iowan Old Style", inexistente no Docker (`python:3.12-slim`) e no CI.
- Paleta do GIF FIXA, derivada só de constantes de cor (camadas do app + Ardósia +
  misturas lineares fundo/figura, `paleta_fixa()`), sem dithering: o mapeamento
  RGB→índice não depende do conteúdo do quadro. Uma paleta adaptativa (median cut) por
  quadro amplificaria qualquer diferença de 1 pixel numa troca global de índices.
- Garantia: byte a byte na mesma plataforma com o mesmo `uv.lock` (verificado por duas
  execuções); entre plataformas (macOS arm64 × Linux x86_64), TOLERÂNCIA declarada em
  `TOLERANCIA` e verificada por `comparar_gifs()` — ver `.meta.json['reprodutibilidade']`
  e `pipeline/tests/test_gif_mancha.py`.

## O que este GIF não é

Corte discreto de fonte de dado por ano-âncora, sem interpolação de geometria entre
anos (ADR 0013) — a "transição" é troca de camada, não movimento real. A acurácia da
camada `urbano` varia por ano (docs/ADR/0009, docs/ADR/0014). Material de
apresentação/comunicação — não é figura de resultado do artigo e não substitui as
figuras com proveniência hash-rastreada de `pipeline/04_figures/`.
"""
from __future__ import annotations

import hashlib
import json
import platform
import subprocess
import sys
import warnings
from pathlib import Path

import geopandas as gpd
import matplotlib as mpl
import numpy as np
import yaml
from matplotlib import ft2font
from matplotlib.backends.backend_agg import FigureCanvasAgg
from matplotlib.figure import Figure
from matplotlib.font_manager import FontProperties
from matplotlib.lines import Line2D
from matplotlib.patches import Rectangle
from matplotlib.text import Text
from PIL import Image

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "00_fetch"))

from _config import carregar_aoi
from _paleta_ardosia import (
    FILETE,
    GRAFITE,
    PAPEL,
    PAPEL_CL,
    PEDRA,
    TINTA,
    apply_ardosia,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
DATA_APP_IMAGERY = REPO_ROOT / "data" / "processed" / "app" / "imagery"
OUT_FIG = REPO_ROOT / "paper" / "figuras"
NOME_GIF = "mancha_urbana_2000_2025.gif"
NOME_META = "mancha_urbana_2000_2025.meta.json"

ANOS = [2000, 2005, 2010, 2015, 2020, 2025]

# Camadas por ano-âncora (nome do arquivo -> chave estável de estilo)
CAMADAS_POR_ANO = ["agua", "urbano", "industrial", "reassentamento", "cultivo_irrigado"]
CAMADAS_ESTATICAS = ["varzea", "osm_vias", "osm_ferrovia", "osm_aerodromo"]
CAMADA_LUGARES = "osm_lugares"

CAMADAS_EXCLUIDAS = ["cultivo_sequeiro", "adensamento_2020_2025"]

# --- Paleta de uso do solo: fonte única config/paleta_uso_solo.yaml (ADR 0018) ---------
CAMINHO_PALETA_USO_SOLO = REPO_ROOT / "config" / "paleta_uso_solo.yaml"
_BRUTO_PALETA_USO_SOLO = CAMINHO_PALETA_USO_SOLO.read_bytes()
_PALETA_USO_SOLO = yaml.safe_load(_BRUTO_PALETA_USO_SOLO.decode("utf-8"))
CLASSES_USO_SOLO = _PALETA_USO_SOLO["classes"]
CONTEXTO_USO_SOLO = _PALETA_USO_SOLO["contexto"]
SHA256_PALETA_USO_SOLO = hashlib.sha256(_BRUTO_PALETA_USO_SOLO).hexdigest()
ADR_PALETA_USO_SOLO = "docs/ADR/0018-paleta-uso-do-solo-worldcover.md"

# Cores por camada — classes lidas de `classes`, contexto (vias/ferrovia/aeródromo/
# topônimos) de `contexto`. Nenhum hex de classe escrito aqui.
CORES_CAMADA = {
    "urbano": CLASSES_USO_SOLO["urbano"]["cor"],
    "industrial": CLASSES_USO_SOLO["industrial"]["cor"],
    "reassentamento": CLASSES_USO_SOLO["reassentamento"]["cor"],
    "cultivo_irrigado": CLASSES_USO_SOLO["cultivo_irrigado"]["cor"],
    "agua": CLASSES_USO_SOLO["agua"]["cor"],
    "varzea": CLASSES_USO_SOLO["varzea"]["cor"],
    "osm_vias": CONTEXTO_USO_SOLO["vias"],
    "osm_ferrovia": CONTEXTO_USO_SOLO["ferrovia"],
    "osm_aerodromo": CONTEXTO_USO_SOLO["aerodromo"],
    "osm_lugares": CONTEXTO_USO_SOLO["toponimo"],
}

# Contorno das classes adaptadas que o exigem (reassentamento e industrial, ADR 0018) —
# mesmo estilo do app (`app/src/lib/camadasBase.js`, `CONTORNO_CAMADA`).
CONTORNO_CAMADA = {
    "reassentamento": CLASSES_USO_SOLO["reassentamento"]["contorno"],
    "industrial": CLASSES_USO_SOLO["industrial"]["contorno"],
}
LARGURA_CONTORNO_PT = 0.7  # equivalente visual ao line-width 1.2 do MapLibre nesta escala

# Opacidade da várzea (zona estática, não cobertura observada) — do YAML, não fixa no código.
OPACIDADE_VARZEA = CLASSES_USO_SOLO["varzea"]["opacidade"]

# Cor de fundo do mapa: seção `contexto` do YAML (mesma do app, `COR_FUNDO_MAPA`).
COR_CONTORNO_FANTASMA = CONTEXTO_USO_SOLO["contorno_fantasma"]  # inventariada; não desenhada
# neste GIF (sem par "ano anterior" sobreposto) — carregada aqui só para que nenhuma cor de
# contexto do YAML fique fora do inventário de proveniência deste script (item 1 da tarefa).

LEGENDA_ROTULOS = {
    "urbano": "Urbano (classificação própria)",
    "industrial": "Industrial / minerário (classificação própria)",
    "reassentamento": "Reassentamento (classificação própria, recorte de urbano)",
    "cultivo_irrigado": "Cultivo irrigado / vazante (classificação própria)",
    "agua": "Água (classificação própria)",
    "varzea": "Várzea (estática, DEM + distância ao rio)",
    "osm_vias": "Vias (OpenStreetMap)",
    "osm_ferrovia": "Ferrovia — linha do Sena (OpenStreetMap)",
    "osm_aerodromo": "Aeródromo de Tete/Chingodzi — TET/FQTT (OpenStreetMap)",
}

FUNDO_MAPA = CONTEXTO_USO_SOLO["fundo_mapa"]  # mesmo tom do fundo do app (camadasBase.js)
ALPHA_LEGENDA = 0.92

FIGSIZE_IN = (10.0, 7.6)
DPI = 150
TAMANHO_PX_ESPERADO = (int(FIGSIZE_IN[0] * DPI), int(FIGSIZE_IN[1] * DPI))

DURACAO_MS = 900

# --- Fontes: só os TTF embutidos no pacote matplotlib, por caminho de arquivo ---------
DIR_FONTES_MPL = Path(mpl.get_data_path()) / "fonts" / "ttf"
ARQUIVOS_FONTE = {
    "serif_negrito": "DejaVuSerif-Bold.ttf",  # ano em destaque
    "sans": "DejaVuSans.ttf",  # topônimos, legenda, churn, rodapé
}

# --- Tolerância entre plataformas (declarada no .meta.json e testada) -----------------
# Aplicada quadro a quadro, sobre os quadros decodificados do GIF, só quando os bytes
# diferem. Número de quadros, tamanho, duração e paleta têm de ser idênticos.
TOLERANCIA = {
    "fracao_max_pixels_com_indice_diferente_por_quadro": 0.002,
    "diferenca_media_abs_rgb_max_por_quadro_0a255": 0.05,
}
# Calibração (2026-09-11, Darwin arm64): o GIF foi regenerado com a AOI multiplicada
# por (1 + eps) — perturbação de coordenadas que simula divergência de ponto flutuante
# — e comparado ao publicado por `comparar_gifs()`. Pior quadro de cada caso. A
# diferença de arredondamento entre arm64 e x86_64 é da ordem de 1 ulp (~1e-16
# relativo), abaixo do menor eps que já muda algum pixel.
CALIBRACAO_TOLERANCIA = {
    "metodo": "AOI × (1 + eps); pior quadro; mesma máquina",
    "eps_1e-15": {"byte_a_byte": True, "fracao": 0.0, "mae_rgb": 0.0},
    "eps_1e-12": {"byte_a_byte": False, "fracao": 5.8e-07, "mae_rgb": 1.6e-06},
    "eps_1e-09": {"byte_a_byte": False, "fracao": 2.5e-04, "mae_rgb": 1.1e-03},
    "eps_1e-06": {
        "byte_a_byte": False, "fracao": 8.1e-02, "mae_rgb": 0.61,
        "nota": "≈ 0,08 px (≈ 3,7 m) de deslocamento real — REPROVADO pela tolerância",
    },
}


def commit_git_atual() -> str:
    try:
        return subprocess.check_output(
            ["git", "rev-parse", "HEAD"], cwd=REPO_ROOT, text=True, stderr=subprocess.DEVNULL
        ).strip()
    except (subprocess.CalledProcessError, FileNotFoundError):
        return "desconhecido (git indisponível)"


def hash_arquivo(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def caminho_fonte(chave: str) -> Path:
    caminho = DIR_FONTES_MPL / ARQUIVOS_FONTE[chave]
    if not caminho.is_file():
        raise FileNotFoundError(f"fonte embutida do matplotlib ausente: {caminho}")
    return caminho


def fonte(chave: str, tamanho: float) -> FontProperties:
    """FontProperties presa a um arquivo TTF embutido — sem resolução por nome."""
    return FontProperties(fname=str(caminho_fonte(chave)), size=tamanho)


def verificar_fontes(fig: Figure) -> None:
    """Falha se algum texto visível do quadro não vier de um TTF embutido permitido."""
    permitidos = {caminho_fonte(k).resolve() for k in ARQUIVOS_FONTE}
    for t in fig.findobj(Text):
        if not t.get_text() or not t.get_visible():
            continue
        arquivo = t.get_fontproperties().get_file()
        if arquivo is None or Path(arquivo).resolve() not in permitidos:
            raise RuntimeError(f"texto {t.get_text()!r} com fonte não embutida: {arquivo!r}")


def _rgb(hex_cor: str) -> np.ndarray:
    h = hex_cor.lstrip("#")
    return np.array([int(h[i : i + 2], 16) for i in (0, 2, 4)], dtype=float)


def _mistura(frente: str | np.ndarray, fundo: str | np.ndarray, alpha: float) -> np.ndarray:
    f = _rgb(frente) if isinstance(frente, str) else frente
    b = _rgb(fundo) if isinstance(fundo, str) else fundo
    return alpha * f + (1.0 - alpha) * b


def paleta_fixa() -> bytes:
    """Paleta de 256 cores derivada SÓ de constantes (768 bytes RGB).

    Cores puras de frente (camadas, contornos, texto, filete) e de fundo (papel, fundo do
    mapa, várzea translúcida, caixa da legenda), mais misturas lineares frente/fundo em
    1/4, 1/2 e 3/4, camada/camada em 1/2, contorno/preenchimento e contorno/fundo em
    passos próprios, e texto/fundo em passos de 1/5 deslocados — as cores que o antialiasing do
    Agg produz nas bordas. Independe do conteúdo dos quadros; logo é idêntica em qualquer
    plataforma. Cores repetidas são removidas na ordem de inserção; o resto até 256 é
    preenchido com a 1ª cor. A paleta cresceu com a paleta de uso do solo (ADR 0018, mais
    classes e dois contornos que a antiga réplica de MapaTemporal.jsx); os contornos
    recebem um tratamento mais estreito (menos amostras de mistura) só para caber em 256
    entradas — eles são traços finos, com muito menos pixels de antialiasing do que um
    preenchimento.
    """
    fundos = [
        _rgb(PAPEL),
        _rgb(FUNDO_MAPA),
        _mistura(CORES_CAMADA["varzea"], FUNDO_MAPA, OPACIDADE_VARZEA),
        _mistura(PAPEL_CL, FUNDO_MAPA, ALPHA_LEGENDA),
    ]
    frentes_hex = [*dict.fromkeys(CORES_CAMADA.values()), TINTA, PEDRA, GRAFITE, FILETE]
    frentes = [_rgb(c) for c in frentes_hex]
    cores: list[tuple[int, int, int]] = []

    def add(c: np.ndarray) -> None:
        t = tuple(int(v) for v in np.clip(np.rint(c), 0, 255))
        if t not in cores:
            cores.append(t)

    for c in fundos + frentes:
        add(c)
    for f in frentes:
        for b in fundos:
            for a in (0.25, 0.5, 0.75):
                add(_mistura(f, b, a))
    # Bordas entre camadas opacas vizinhas (ex.: urbano × água): mistura 1/2.
    camadas = [_rgb(c) for c in dict.fromkeys(CORES_CAMADA.values())]
    for i, f in enumerate(camadas):
        for b in camadas[i + 1 :]:
            add(_mistura(f, b, 0.5))
    # Contornos (reassentamento, industrial, ADR 0018): cor pura, mais antialiasing
    # contra o próprio preenchimento e contra o fundo do mapa/papel (onde o traço mais
    # aparece) — amostragem mais estreita que a dos preenchimentos (motivo na docstring).
    for camada, cor_contorno in CONTORNO_CAMADA.items():
        contorno = _rgb(cor_contorno)
        add(contorno)
        for fundo_ref in (CORES_CAMADA[camada], FUNDO_MAPA, PAPEL):
            for a in (0.3, 0.6, 0.9):
                add(_mistura(contorno, fundo_ref, a))
    # Texto (maior parte dos pixels de antialiasing) sobre papel e fundo do mapa.
    for f in (TINTA, PEDRA, GRAFITE):
        for b in fundos[:2]:
            for a in (0.1, 0.3, 0.5, 0.7, 0.9):
                add(_mistura(f, b, a))
    if len(cores) > 256:
        raise RuntimeError(f"paleta fixa excede 256 cores: {len(cores)}")
    cores += [cores[0]] * (256 - len(cores))
    return bytes(v for c in cores for v in c)


def caminho_camada_ano(camada: str, ano: int) -> Path:
    return DATA_APP_IMAGERY / f"{camada}_{ano}.geojson"


def caminho_camada_estatica(camada: str) -> Path:
    return DATA_APP_IMAGERY / f"{camada}.geojson"


def listar_insumos() -> dict[str, Path]:
    insumos: dict[str, Path] = {}
    for ano in ANOS:
        for camada in CAMADAS_POR_ANO:
            insumos[f"{camada}_{ano}"] = caminho_camada_ano(camada, ano)
    for camada in [*CAMADAS_ESTATICAS, CAMADA_LUGARES]:
        insumos[camada] = caminho_camada_estatica(camada)
    insumos["manifest"] = DATA_APP_IMAGERY / "manifest.json"
    insumos["paleta_uso_solo_yaml"] = CAMINHO_PALETA_USO_SOLO
    return insumos


def carregar_churn_construido(manifest: dict) -> dict[str, dict]:
    churn = manifest.get("churn_pares_temporais", {})
    return {chave: valor for chave, valor in churn.items() if chave.endswith("__construido")}


def desenhar_quadro(
    ano: int,
    aoi: dict,
    churn_construido: dict[str, dict],
    ano_anterior: int | None,
) -> np.ndarray:
    """Renderiza um quadro com o Agg e devolve o raster RGB (uint8, H×W×3)."""
    fig = Figure(figsize=FIGSIZE_IN, dpi=DPI)
    canvas = FigureCanvasAgg(fig)
    ax = fig.add_subplot(1, 1, 1)
    fig.patch.set_facecolor(PAPEL)
    ax.set_facecolor(FUNDO_MAPA)
    ax.grid(False)

    xmin, ymin, xmax, ymax = aoi["xmin"], aoi["ymin"], aoi["xmax"], aoi["ymax"]
    lat_media = (ymin + ymax) / 2.0
    ax.set_xlim(xmin, xmax)
    ax.set_ylim(ymin, ymax)
    ax.set_aspect(1.0 / np.cos(np.radians(lat_media)))
    ax.set_xticks([])
    ax.set_yticks([])
    for spine in ax.spines.values():
        spine.set_visible(True)
        spine.set_edgecolor(FILETE)

    # --- camadas estáticas de contexto (desenhadas primeiro, ao fundo) ---
    varzea = gpd.read_file(caminho_camada_estatica("varzea"))
    varzea.plot(ax=ax, color=CORES_CAMADA["varzea"], alpha=OPACIDADE_VARZEA, linewidth=0, zorder=1)

    vias = gpd.read_file(caminho_camada_estatica("osm_vias"))
    vias.plot(ax=ax, color=CORES_CAMADA["osm_vias"], linewidth=0.6, zorder=2)

    ferrovia = gpd.read_file(caminho_camada_estatica("osm_ferrovia"))
    ferrovia.plot(
        ax=ax, color=CORES_CAMADA["osm_ferrovia"], linewidth=1.0,
        linestyle=(0, (4, 2)), zorder=2,
    )

    aerodromo = gpd.read_file(caminho_camada_estatica("osm_aerodromo"))
    aerodromo.plot(
        ax=ax, facecolor="none", edgecolor=CORES_CAMADA["osm_aerodromo"],
        linewidth=1.0, zorder=2,
    )

    # --- camadas classificadas do ano, na mesma ordem de empilhamento do app ---
    # `reassentamento` e `industrial` levam o contorno do YAML (ADR 0018), como no app
    # (`camadasBase.js`, `CONTORNO_CAMADA` / `layer-<camada>-contorno`); as demais, sem
    # contorno, como antes.
    for camada in ["agua", "cultivo_irrigado", "urbano", "industrial", "reassentamento"]:
        gdf = gpd.read_file(caminho_camada_ano(camada, ano))
        if len(gdf) == 0:
            continue
        contorno = CONTORNO_CAMADA.get(camada)
        if contorno:
            gdf.plot(
                ax=ax, facecolor=CORES_CAMADA[camada], edgecolor=contorno,
                linewidth=LARGURA_CONTORNO_PT, zorder=3,
            )
        else:
            gdf.plot(ax=ax, color=CORES_CAMADA[camada], linewidth=0, zorder=3)

    # --- topônimos ---
    lugares = gpd.read_file(caminho_camada_estatica(CAMADA_LUGARES))
    for _, row in lugares.iterrows():
        pt = row.geometry
        if pt is None:
            continue
        nome = row.get("name")
        if nome is None or (isinstance(nome, float) and np.isnan(nome)):
            continue
        nome = str(nome)
        if not nome.strip():
            continue
        ax.annotate(
            nome, (pt.x, pt.y), color=CORES_CAMADA["osm_lugares"],
            fontproperties=fonte("sans", 6), ha="left", va="bottom", zorder=4,
            xytext=(2, 2), textcoords="offset points",
        )

    # --- ano em destaque, serifa (DejaVu Serif Bold embutida) ---
    ax.text(
        0.02, 0.95, str(ano), transform=ax.transAxes, color=TINTA,
        fontproperties=fonte("serif_negrito", 34), ha="left", va="top", zorder=5,
    )

    # --- churn do par temporal (ADR 0013), a partir do 2º quadro ---
    if ano_anterior is not None:
        registro = churn_construido.get(f"{ano_anterior}-{ano}__construido")
        if registro is not None:
            texto_churn = (
                f"churn 'construído' {ano_anterior}→{ano}: "
                f"{registro['churn'] * 100:.1f}% (rótulo bruto do RF, pré-R1/R2 — "
                f"ADR 0013, EXPERIMENTAL, não substitui artefato publicado)"
            )
            ax.text(
                0.02, 0.02, texto_churn, transform=ax.transAxes, color=PEDRA,
                fontproperties=fonte("sans", 6.5), ha="left", va="bottom", zorder=5,
            )

    # --- legenda ---
    # Classes `origem: adaptacao` (YAML) levam um "*" discreto no rótulo — a nota da linha
    # de crédito de cores, no rodapé, explica o que ele marca (item 2 da tarefa).
    handles: list = []
    labels: list[str] = []
    for camada in ["urbano", "industrial", "reassentamento", "cultivo_irrigado", "agua", "varzea"]:
        contorno = CONTORNO_CAMADA.get(camada, "none")
        handles.append(Rectangle((0, 0), 1, 1, facecolor=CORES_CAMADA[camada], edgecolor=contorno))
        sufixo = " *" if CLASSES_USO_SOLO[camada]["origem"] == "adaptacao" else ""
        labels.append(LEGENDA_ROTULOS[camada] + sufixo)
    for camada, estilo in [("osm_vias", "-"), ("osm_ferrovia", "--"), ("osm_aerodromo", "-")]:
        handles.append(
            Line2D([0], [0], color=CORES_CAMADA[camada], linestyle=estilo, linewidth=1.4)
        )
        labels.append(LEGENDA_ROTULOS[camada])
    legenda = ax.legend(
        handles, labels, loc="upper right", frameon=True,
        facecolor=PAPEL_CL, edgecolor=FILETE, framealpha=ALPHA_LEGENDA,
        prop=fonte("sans", 6.2),
    )
    legenda.set_zorder(6)

    # --- crédito de cores, sobre a legenda (item 2 da tarefa) ---
    fig.text(
        0.99, 0.955,
        "Cores: ESA WorldCover (FAO LCCS); adaptações no ADR 0018 (classes com * na legenda)",
        color=GRAFITE, fontproperties=fonte("sans", 5.6), ha="right", va="top", zorder=6,
    )

    # --- crédito de fontes no rodapé ---
    rodape = (
        "Fontes: classificação própria (Landsat/Sentinel-2, compostos de estação "
        "seca, §5.1); OpenStreetMap (© OpenStreetMap contributors, ODbL 1.0) — "
        "vias, ferrovia, aeródromo, topônimos. Material de comunicação; "
        "não é figura de resultado do artigo. Corte discreto por ano-âncora, sem "
        "interpolação de geometria (ADR 0013)."
    )
    fig.text(
        0.01, 0.005, rodape, color=GRAFITE, fontproperties=fonte("sans", 5.6),
        ha="left", va="bottom", wrap=True,
    )

    fig.subplots_adjust(left=0.01, right=0.99, top=0.99, bottom=0.045)

    verificar_fontes(fig)
    canvas.draw()
    rgba = np.asarray(canvas.buffer_rgba())
    return np.ascontiguousarray(rgba[..., :3])


def quantizar(rgb: np.ndarray) -> Image.Image:
    """RGB → modo P na paleta fixa, sem dithering (vizinho mais próximo)."""
    ref = Image.new("P", (1, 1))
    ref.putpalette(paleta_fixa())
    return Image.fromarray(rgb, mode="RGB").quantize(palette=ref, dither=Image.Dither.NONE)


def montar_gif(quadros_rgb: list[np.ndarray], destino: Path) -> None:
    tamanhos = {q.shape for q in quadros_rgb}
    if len(tamanhos) != 1:
        raise RuntimeError(f"quadros com tamanhos diferentes: {tamanhos}")
    quantizadas = [quantizar(q) for q in quadros_rgb]
    quantizadas[0].save(
        destino,
        save_all=True,
        append_images=quantizadas[1:],
        duration=DURACAO_MS,
        loop=0,
        disposal=2,
        optimize=False,
    )


def ler_quadros(gif: Path) -> tuple[list[np.ndarray], list[np.ndarray], list[int]]:
    """Decodifica o GIF: (índices de paleta, RGB, duração) por quadro."""
    indices, rgbs, duracoes = [], [], []
    with Image.open(gif) as im:
        for i in range(getattr(im, "n_frames", 1)):
            im.seek(i)
            rgb = np.asarray(im.convert("RGB"), dtype=np.int16)
            rgbs.append(rgb)
            indices.append(_rgb_para_indice(rgb))
            duracoes.append(int(im.info.get("duration", 0)))
    return indices, rgbs, duracoes


def _rgb_para_indice(rgb: np.ndarray) -> np.ndarray:
    """Índice na paleta fixa de cada pixel decodificado (-1 se a cor não pertencer)."""
    pal = np.frombuffer(paleta_fixa(), dtype=np.uint8).reshape(-1, 3).astype(np.int32)
    chave_pal = (pal[:, 0] << 16) | (pal[:, 1] << 8) | pal[:, 2]
    chave_pal_unica, primeiro = np.unique(chave_pal, return_index=True)
    r = rgb.astype(np.int32)
    chave = (r[..., 0] << 16) | (r[..., 1] << 8) | r[..., 2]
    pos = np.clip(np.searchsorted(chave_pal_unica, chave), 0, len(chave_pal_unica) - 1)
    return np.where(chave_pal_unica[pos] == chave, primeiro[pos], -1)


def comparar_gifs(publicado: Path, regenerado: Path) -> dict:
    """Compara dois GIFs segundo `TOLERANCIA`. Devolve métricas e veredito."""
    if hash_arquivo(publicado) == hash_arquivo(regenerado):
        return {"identico_byte_a_byte": True, "dentro_da_tolerancia": True, "quadros": []}
    ia, ra, da = ler_quadros(publicado)
    ib, rb, db = ler_quadros(regenerado)
    res: dict = {"identico_byte_a_byte": False, "quadros": [], "violacoes": []}
    if len(ia) != len(ib) or da != db:
        res["violacoes"].append(f"n_quadros/duração: {len(ia)}/{da} vs {len(ib)}/{db}")
    for k, (a, b, x, y) in enumerate(zip(ia, ib, ra, rb, strict=False)):
        if a.shape != b.shape:
            res["violacoes"].append(f"quadro {k}: tamanho {a.shape} vs {b.shape}")
            continue
        fora = int((a < 0).sum() + (b < 0).sum())
        frac = float((a != b).mean())
        mae = float(np.abs(x - y).mean())
        res["quadros"].append({"quadro": k, "fracao_pixels_diferentes": frac, "mae_rgb": mae})
        if fora:
            res["violacoes"].append(f"quadro {k}: {fora} pixels fora da paleta fixa")
        if frac > TOLERANCIA["fracao_max_pixels_com_indice_diferente_por_quadro"]:
            res["violacoes"].append(f"quadro {k}: fração de pixels diferentes {frac:.5f}")
        if mae > TOLERANCIA["diferenca_media_abs_rgb_max_por_quadro_0a255"]:
            res["violacoes"].append(f"quadro {k}: MAE RGB {mae:.4f}")
    res["dentro_da_tolerancia"] = not res["violacoes"]
    return res


def ambiente_de_renderizacao() -> dict:
    """Versões e hashes que condicionam o raster — lidos em tempo de execução."""
    import PIL
    import pyogrio
    import shapely

    return {
        "python": platform.python_version(),
        "plataforma_de_geracao": f"{platform.system()} {platform.machine()}",
        "matplotlib": mpl.__version__,
        "freetype": ft2font.__freetype_version__,
        "freetype_build": ft2font.__freetype_build_type__,
        "pillow": PIL.__version__,
        "numpy": np.__version__,
        "geopandas": gpd.__version__,
        "pyogrio": pyogrio.__version__,
        "gdal_via_pyogrio": pyogrio.__gdal_version_string__,
        "shapely": shapely.__version__,
        "fontes_ttf": {
            chave: {
                "arquivo": f"matplotlib/mpl-data/fonts/ttf/{nome}",
                "sha256": hash_arquivo(caminho_fonte(chave)),
            }
            for chave, nome in ARQUIVOS_FONTE.items()
        },
        "sha256_paleta_fixa": hashlib.sha256(paleta_fixa()).hexdigest(),
    }


def gerar(destino: Path, aoi: dict | None = None) -> dict:
    """Gera o GIF em `destino` e devolve o dicionário do `.meta.json`.

    `aoi` só existe para a calibração da tolerância (perturbação de coordenadas); o
    artefato publicado usa sempre a AOI de `config/study.yaml`.
    """
    mpl.use("Agg")
    aoi = aoi if aoi is not None else carregar_aoi()
    manifest = json.loads((DATA_APP_IMAGERY / "manifest.json").read_text(encoding="utf-8"))
    churn_construido = carregar_churn_construido(manifest)

    with mpl.rc_context(), warnings.catch_warnings():
        # Parte do default embutido na versão travada — ignora matplotlibrc do usuário.
        mpl.rcdefaults()
        # apply_ardosia() re-registra os colormaps a cada chamada (aviso inofensivo).
        warnings.filterwarnings("ignore", message="Overwriting the cmap")
        apply_ardosia()
        quadros = []
        ano_anterior = None
        for ano in ANOS:
            quadros.append(desenhar_quadro(ano, aoi, churn_construido, ano_anterior))
            ano_anterior = ano

    destino.parent.mkdir(parents=True, exist_ok=True)
    montar_gif(quadros, destino)

    with Image.open(destino) as im:
        n_quadros = getattr(im, "n_frames", 1)
        tamanho_px = im.size

    insumos = listar_insumos()
    hashes_insumos = {
        nome: hash_arquivo(caminho) for nome, caminho in insumos.items() if caminho.exists()
    }
    faltantes = [nome for nome, caminho in insumos.items() if not caminho.exists()]

    meta = {
        "figura": (
            "GIF animado — progressão da mancha urbana e pegadas associadas, "
            "Tete–Moatize, 2000-2025"
        ),
        "arquivos_saida": [f"paper/figuras/{NOME_GIF}"],
        "anos_ancora": ANOS,
        "metodo": "pipeline/04_figures/gif_mancha.py",
        "camadas_ativas": [
            "urbano",
            "industrial",
            "reassentamento",
            "cultivo_irrigado (cultivo irrigado / vazante)",
            "agua",
            "varzea (estática)",
            "osm_vias (rodovias, N7 e demais)",
            "osm_ferrovia (linha do Sena)",
            "osm_lugares (topônimos)",
            "osm_aerodromo (Tete — TET/FQTT)",
        ],
        "camadas_excluidas": [
            "cultivo_sequeiro / vegetação sazonal (não confirmada como cultivo)",
            "adensamento_2020_2025 (modelado, concordância de 3 sinais, ADR 0016)",
        ],
        "insumos_por_ano_ancora": [
            f"data/processed/app/imagery/{c}_<ano>.geojson" for c in CAMADAS_POR_ANO
        ],
        "insumos_estaticos": [
            f"data/processed/app/imagery/{c}.geojson"
            for c in ["varzea", "osm_vias", "osm_ferrovia", CAMADA_LUGARES, "osm_aerodromo"]
        ],
        "hashes_sha256_insumos": hashes_insumos,
        "insumos_faltantes": faltantes,
        "paleta_cores": {
            "fonte": "config/paleta_uso_solo.yaml",
            "sha256": SHA256_PALETA_USO_SOLO,
            "adr": ADR_PALETA_USO_SOLO,
            "nota": (
                "Cores das classes de uso do solo e do contexto OSM lidas do YAML — mesma "
                "fonte do app (pipeline/05_app/gerar_paleta.py); legenda ESA WorldCover/FAO "
                "LCCS, adaptações declaradas na paleta e marcadas com * na legenda do GIF."
            ),
        },
        "churn_construido_por_par_ano": churn_construido,
        "commit_git": commit_git_atual(),
        "crs_original_dos_dados": (
            "EPSG:4326 (mesmo CRS de exibição do app, §11.2.1; sem reprojeção métrica)"
        ),
        "enquadramento": {
            "bbox_aoi_4326": aoi,
            "correcao_aspecto": (
                "1/cos(latitude_media) — equirretangular, mesmo efeito visual do MapLibre "
                "do app nesta escala"
            ),
        },
        "fonte_serif_usada": "DejaVu Serif Bold (TTF embutido no matplotlib, por caminho)",
        "fonte_sans_usada": "DejaVu Sans (TTF embutido no matplotlib, por caminho)",
        "duracao_ms_por_quadro": DURACAO_MS,
        "n_quadros": n_quadros,
        "tamanho_px": list(tamanho_px),
        "sha256_gif": hash_arquivo(destino),
        "reprodutibilidade": {
            "ambiente": ambiente_de_renderizacao(),
            "garantia_mesma_plataforma": (
                "byte a byte: mesma plataforma + mesmo uv.lock ⇒ mesmo sha256_gif "
                "(verificado por duas execuções na plataforma de geração, e por uma "
                "terceira com MPLCONFIGDIR vazio — cache de fontes reconstruído — e um "
                "matplotlibrc hostil: font.family monospace, text.hinting no_hinting, "
                "antialiasing desligado)"
            ),
            "garantia_entre_plataformas": (
                "tolerância, não byte a byte: não houve execução em Linux nesta sessão "
                "(sem Docker na máquina de geração). O teste "
                "pipeline/tests/test_gif_mancha.py regenera o GIF e compara: aceita "
                "sha256 idêntico; senão exige mesmo n_quadros, tamanho, duração, todos os "
                "pixels na paleta fixa e, por quadro, os limites de 'tolerancia'."
            ),
            "tolerancia": TOLERANCIA,
            "calibracao_da_tolerancia": CALIBRACAO_TOLERANCIA,
            "fontes_de_variacao_eliminadas": [
                "fonte do sistema: só TTF DejaVu embutidos no wheel do matplotlib, por "
                "caminho; verificar_fontes() aborta se algum texto tiver outra origem",
                "FreeType do sistema: o wheel do matplotlib embute o próprio "
                "(freetype_build = 'local'); versão fixada por uv.lock",
                "matplotlibrc do usuário: rcdefaults() antes do estilo",
                "backend: FigureCanvasAgg explícito, sem pyplot nem PNG intermediário",
                "paleta adaptativa: paleta fixa derivada de constantes, sem dithering",
            ],
            "fontes_de_variacao_residuais": [
                "aritmética de ponto flutuante das transformações (FMA/contração do "
                "compilador, arm64 × x86_64) pode mudar o arredondamento subpixel do Agg "
                "em pixels de borda",
                "parse numérico dos GeoJSON pelo GDAL embutido no pyogrio (mesma versão "
                "por uv.lock; strtod corretamente arredondado — variação não esperada)",
            ],
        },
        "selo": (
            "observado (classificação própria) para urbano/industrial/reassentamento/"
            "cultivo_irrigado/agua; observado (OSM) para vias/ferrovia/topônimos/"
            "aeródromo; estático para várzea; ver 'churn_construido_por_par_ano' para "
            "selo experimental do indicador de churn (ADR 0013)"
        ),
        "ressalvas": [
            "Corte discreto de fonte de dado por ano-âncora, sem interpolação de geometria "
            "entre anos (ADR 0013) — a 'transição' no GIF é troca de camada, não "
            "movimento real.",
            "Acurácia da camada 'urbano' varia por ano — ver docs/ADR/0009 e "
            "docs/ADR/0014 e o aviso equivalente exibido no próprio app.",
            "Este GIF é material de apresentação/comunicação; não é figura de resultado "
            "do artigo e não substitui as figuras geradas por pipeline/04_figures com "
            "proveniência hash-rastreada.",
            "O indicador de churn 'construído' por par de anos, exibido em texto miúdo, "
            "vem do rótulo bruto do classificador antes de R1/R2 (ADR 0013) — "
            "EXPERIMENTAL, não é o número publicado de área construída.",
        ],
    }
    return meta


def main() -> None:
    OUT_FIG.mkdir(parents=True, exist_ok=True)
    meta = gerar(OUT_FIG / NOME_GIF)
    meta_path = OUT_FIG / NOME_META
    with meta_path.open("w", encoding="utf-8") as f:
        json.dump(meta, f, ensure_ascii=False, indent=2, sort_keys=True)
        f.write("\n")
    print(f"[gif_mancha] gerado: {OUT_FIG / NOME_GIF}")
    print(f"[gif_mancha] sha256: {meta['sha256_gif']}")


if __name__ == "__main__":
    main()
