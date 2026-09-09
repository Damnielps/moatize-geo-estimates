#!/usr/bin/env python3
"""pipeline/04_figures/mapa_localizacao.py — figura de localização de Tete e Moatize.

Mapa principal (AOI, ano-âncora 2025) + dois encartes de localização (província de
Tete; Moçambique), no modelo clássico de "study area" com encartes aninhados.
Identidade visual: Sistema Ardósia (`_paleta_ardosia.py`, vendorizado sem alteração
de `ardosia-brand-guidelines/scripts/palette.py`).

## Fontes (todas de nível A, já espelhadas em data/raw/ e data/processed/)

- Limites administrativos: HDX COD-AB Moçambique (ITOS/OCHA), admin0/1/2.
  **P-codes do COD-AB, não do COD-PS** (config/unidades.yaml) — Cidade de Tete =
  MZ0501, Moatize = MZ0510, província de Tete = MZ05.
- Camadas classificadas (urbano/industrial/reassentamento, 2025): saída própria de
  `pipeline/01_imagery/classificacao.py`, EPSG:32736.
- Reassentamentos: `data/raw/reassentamentos.geojson` (Cateme, Mwaladzi georreferenciados;
  "25 de Setembro" com `geometry: null`, propositalmente não inventada — ver nota na
  legenda).
- Hidrografia: HydroRIVERS v10 Africa (Lehner & Grill 2013), recortada à AOI.

## Honestidade cartográfica (obrigatória, ver docs/ADR/0009 e docs/ADR/0008)

- A camada `urbano` tem acurácia do usuário medida por ano (docs/ADR/0009; valor
  reexecutado em docs/ADR/0014 — ver `pipeline/lib/acuracia_texto.py` para o número
  corrente, não transcrito aqui). Isto vai na legenda, não só no texto. Fonte não é
  usada como cadastro.
- A série de área construída ao longo do tempo é a do WSF Evolution (ADR 0008), não a
  classificação própria; esta figura mostra só o corte de 2025 (fim da série própria,
  sem contraparte WSF depois de 2015) e não plota nenhuma série temporal — a ressalva
  fica na nota de rodapé, para quem reusar o corte fora de contexto.

## CRS

- Mapa principal: **EPSG:32736** (UTM 36S) — métrica de área, permite barra de escala
  exata e norte verdadeiro aproximado (§ convenção do repositório).
  Camadas classificadas já nascem nesse CRS; limites administrativos e hidrografia são
  reprojetados.
- Encartes: **EPSG:4326** — só localização/orientação, nunca métrica (mesma regra do
  CRS de exibição do repositório), distorção aceitável na escala provincial/nacional.

## Determinismo

Sem RNG, sem downloads. Mesma entrada -> mesmo PDF/PNG byte a byte (fontes do sistema
podem variar a rasterização de texto entre máquinas; o contrato de teste checa
existência e tamanho plausível, não hash, por essa razão — ver
`pipeline/tests/test_figuras.py`).
"""
from __future__ import annotations

import datetime as dt
import hashlib
import json
import subprocess
import sys
from pathlib import Path

import geopandas as gpd
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.patches import FancyArrow, Rectangle
from pyproj import Transformer
from shapely.geometry import box

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "00_fetch"))
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "lib"))

import acuracia_texto
from _config import carregar_aoi, carregar_estudo
from _paleta_ardosia import (
    ARDOSIA,
    ARDOSIA_CL,
    FILETE,
    GRAFITE,
    PAPEL,
    PAPEL_CL,
    PEDRA,
    SANS,
    SERIF,
    TERRACOTA,
    TERRACOTA_NEV,
    TINTA,
    apply_ardosia,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
DATA_RAW = REPO_ROOT / "data" / "raw"
DATA_PROC = REPO_ROOT / "data" / "processed"
OUT_FIG = REPO_ROOT / "paper" / "figuras"
OUT_PIPE = REPO_ROOT / "pipeline" / "04_figures"

ANO = 2025
CRS_METRICO = "EPSG:32736"
CRS_EXIBICAO = "EPSG:4326"

MONO = ["IBM Plex Mono", "DejaVu Sans Mono", "monospace"]

CAMINHOS = {
    "admin_zip": DATA_RAW / "hdx_cod-ab-moz_admin_boundaries.geojson.zip",
    "urbano": DATA_PROC / "imagery" / f"urbano_{ANO}.geojson",
    "industrial": DATA_PROC / "imagery" / f"industrial_{ANO}.geojson",
    "reassentamento_poligonos": DATA_PROC / "imagery" / f"reassentamento_{ANO}.geojson",
    "reassentamentos_pontos": DATA_RAW / "reassentamentos.geojson",
    "hydro": DATA_RAW / "hydrorivers_af_v10.gdb.zip",
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


# ---------------------------------------------------------------------------
# Carga de dados
# ---------------------------------------------------------------------------

def carregar_admin() -> dict[str, gpd.GeoDataFrame]:
    zpath = CAMINHOS["admin_zip"]
    admin0 = gpd.read_file(f"zip://{zpath}!moz_admin0.geojson")
    admin1 = gpd.read_file(f"zip://{zpath}!moz_admin1.geojson")
    admin2 = gpd.read_file(f"zip://{zpath}!moz_admin2.geojson")
    return {"admin0": admin0, "admin1": admin1, "admin2": admin2}


def carregar_hydro(aoi_4326: tuple[float, float, float, float]) -> gpd.GeoDataFrame:
    return gpd.read_file(
        CAMINHOS["hydro"], layer="HydroRIVERS_v10_af", bbox=aoi_4326
    )


def carregar_classificadas() -> dict[str, gpd.GeoDataFrame]:
    camadas = {}
    for nome in ("urbano", "industrial", "reassentamento_poligonos"):
        camadas[nome] = gpd.read_file(CAMINHOS[nome])
    return camadas


def carregar_reassentamentos_pontos() -> gpd.GeoDataFrame:
    g = gpd.read_file(CAMINHOS["reassentamentos_pontos"])
    if g.crs is None:
        g = g.set_crs(CRS_EXIBICAO)
    return g


# ---------------------------------------------------------------------------
# Elementos cartográficos genéricos
# ---------------------------------------------------------------------------

def desenhar_barra_escala(ax):
    """Barra de escala em km, no canto inferior esquerdo do eixo (unidades do CRS = m)."""
    xlim = ax.get_xlim()
    largura_eixo_m = xlim[1] - xlim[0]
    alvo_m = largura_eixo_m * 0.22
    passos_km = [1, 2, 5, 10, 20, 25, 50, 100]
    escolhido_km = min(passos_km, key=lambda k: abs(k * 1000 - alvo_m))

    x0 = xlim[0] + largura_eixo_m * 0.04
    y0 = ax.get_ylim()[0] + (ax.get_ylim()[1] - ax.get_ylim()[0]) * 0.045
    altura = (ax.get_ylim()[1] - ax.get_ylim()[0]) * 0.008

    segmento = escolhido_km * 1000 / 2
    for i, cor in enumerate([TINTA, PAPEL_CL]):
        ax.add_patch(
            Rectangle(
                (x0 + i * segmento, y0), segmento, altura,
                facecolor=cor, edgecolor=TINTA, linewidth=0.6, zorder=10,
            )
        )
    ax.text(
        x0, y0 + altura * 2.6, "0", fontsize=7, color=GRAFITE,
        ha="center", va="bottom", fontfamily=MONO, zorder=10,
    )
    ax.text(
        x0 + escolhido_km * 1000, y0 + altura * 2.6, f"{escolhido_km} km",
        fontsize=7, color=GRAFITE, ha="center", va="bottom", fontfamily=MONO, zorder=10,
    )


def desenhar_seta_norte(ax, x_frac=0.94, y_frac=0.90, tamanho_frac=0.045):
    xlim, ylim = ax.get_xlim(), ax.get_ylim()
    dx, dy = xlim[1] - xlim[0], ylim[1] - ylim[0]
    x = xlim[0] + x_frac * dx
    y0 = ylim[0] + (y_frac - tamanho_frac / 2) * dy
    comprimento = tamanho_frac * dy
    ax.add_patch(
        FancyArrow(
            x, y0, 0, comprimento, width=comprimento * 0.10,
            head_width=comprimento * 0.42, head_length=comprimento * 0.34,
            facecolor=TINTA, edgecolor="none", zorder=11, length_includes_head=True,
        )
    )
    ax.text(
        x, y0 + comprimento * 1.18, "N", fontsize=9, color=TINTA,
        ha="center", va="bottom", fontfamily=MONO, fontweight="bold", zorder=11,
    )


def desenhar_grade_coordenadas(ax, aoi_4326, crs_destino, passo_graus=0.1):
    """Grade discreta de coordenadas (filete, não linha grossa) e rótulos em mono."""
    xmin, ymin, xmax, ymax = aoi_4326
    transformer = Transformer.from_crs(CRS_EXIBICAO, crs_destino, always_xy=True)

    def arred(v, passo):
        return np.round(v / passo) * passo

    lons = np.arange(arred(xmin, passo_graus), xmax + passo_graus, passo_graus)
    lons = lons[(lons >= xmin) & (lons <= xmax)]
    lats = np.arange(arred(ymin, passo_graus), ymax + passo_graus, passo_graus)
    lats = lats[(lats >= ymin) & (lats <= ymax)]

    xlim, ylim = ax.get_xlim(), ax.get_ylim()
    for lon in lons:
        xs, ys = transformer.transform([lon, lon], [ymin, ymax])
        ax.plot(xs, ys, color=FILETE, linewidth=0.5, zorder=1, alpha=0.9)
        xr, yr = transformer.transform(lon, ymin)
        ax.text(
            xr, ylim[0] - (ylim[1] - ylim[0]) * 0.012, f"{lon:.1f}°E",
            fontsize=6.5, color=PEDRA, ha="center", va="top", fontfamily=MONO, clip_on=False,
        )
    for lat in lats:
        xs, ys = transformer.transform([xmin, xmax], [lat, lat])
        ax.plot(xs, ys, color=FILETE, linewidth=0.5, zorder=1, alpha=0.9)
        xr, yr = transformer.transform(xmin, lat)
        ax.text(
            xlim[0] - (xlim[1] - xlim[0]) * 0.012, yr, f"{abs(lat):.1f}°S",
            fontsize=6.5, color=PEDRA, ha="right", va="center", fontfamily=MONO, clip_on=False,
        )
    ax.set_xlim(xlim)
    ax.set_ylim(ylim)


# ---------------------------------------------------------------------------
# Montagem da figura
# ---------------------------------------------------------------------------

def montar_figura() -> plt.Figure:
    apply_ardosia()
    # Esta figura tem orçamento de layout fixo em polegadas (ver comentário acima de
    # `fig = plt.figure(...)`); 'tight' recortaria a tela conforme métrica de fonte da
    # máquina, tornando o tamanho não determinístico entre ambientes.
    plt.rcParams["savefig.bbox"] = None

    estudo = carregar_estudo()
    aoi = carregar_aoi()
    aoi_4326 = (aoi["xmin"], aoi["ymin"], aoi["xmax"], aoi["ymax"])
    aoi_poly_4326 = gpd.GeoDataFrame(
        geometry=[box(*aoi_4326)], crs=CRS_EXIBICAO
    )
    aoi_poly_metrico = aoi_poly_4326.to_crs(CRS_METRICO)

    admin = carregar_admin()
    hydro_4326 = carregar_hydro(aoi_4326)
    classificadas = carregar_classificadas()
    pontos = carregar_reassentamentos_pontos()

    hydro_metrico = hydro_4326.to_crs(CRS_METRICO)
    admin2_metrico = admin["admin2"].to_crs(CRS_METRICO)
    pontos_metrico = pontos.to_crs(CRS_METRICO)

    fig = plt.figure(figsize=(11, 12.0), facecolor=PAPEL)

    # eixo principal — orçamento vertical fixo em polegadas (ver comentário de layout
    # no topo do módulo); savefig usa bbox_inches='standard' (não 'tight') para que o
    # tamanho da tela seja determinístico e não dependa de métricas de fonte da máquina.
    ax_main = fig.add_axes([0.075, 0.3983, 0.855, 0.4667])
    ax_main.set_facecolor(PAPEL)

    bounds = aoi_poly_metrico.total_bounds
    margem = (bounds[2] - bounds[0]) * 0.015
    ax_main.set_xlim(bounds[0] - margem, bounds[2] + margem)
    ax_main.set_ylim(bounds[1] - margem, bounds[3] + margem)

    # hidrografia — espessura por ordem de fluxo (ORD_FLOW menor = rio maior)
    for ordem, largura in [(3, 2.4), (4, 1.6), (5, 1.1), (6, 0.7)]:
        sub = hydro_metrico[hydro_metrico["ORD_FLOW"] == ordem]
        if not sub.empty:
            sub.plot(ax=ax_main, color=ARDOSIA_CL, linewidth=largura, zorder=2)
    sub_menor = hydro_metrico[hydro_metrico["ORD_FLOW"] >= 7]
    if not sub_menor.empty:
        sub_menor.plot(ax=ax_main, color=ARDOSIA_CL, linewidth=0.5, zorder=2, alpha=0.7)

    # limites distritais de contexto (Cidade de Tete / Moatize) dentro da AOI
    admin2_clip = gpd.clip(admin2_metrico, aoi_poly_metrico)
    admin2_clip.boundary.plot(
        ax=ax_main, color=GRAFITE, linewidth=0.7, linestyle=(0, (4, 3)), zorder=3,
    )

    # camadas classificadas — urbano (ardósia), industrial (terracota),
    # reassentamento (terracota hachurado)
    urb = classificadas["urbano"]
    if not urb.empty:
        urb.plot(ax=ax_main, facecolor=ARDOSIA, edgecolor="none", zorder=4)

    ind = classificadas["industrial"]
    if not ind.empty:
        ind.plot(ax=ax_main, facecolor=TERRACOTA, edgecolor="none", zorder=5)

    reas_poly = classificadas["reassentamento_poligonos"]
    if not reas_poly.empty:
        reas_poly.plot(
            ax=ax_main, facecolor=TERRACOTA_NEV, edgecolor=TERRACOTA,
            linewidth=0.8, hatch="////", zorder=6,
        )

    # povoados de reassentamento (pontos georreferenciados)
    pontos_com_geom = pontos_metrico[pontos_metrico.geometry.notna()]
    pontos_sem_geom = pontos[pontos.geometry.isna()]
    if not pontos_com_geom.empty:
        pontos_com_geom.plot(
            ax=ax_main, marker="D", color=TERRACOTA, markersize=46,
            edgecolor=PAPEL, linewidth=1.0, zorder=8,
        )
        for _, row in pontos_com_geom.iterrows():
            ax_main.annotate(
                row["nome"], (row.geometry.x, row.geometry.y),
                xytext=(6, 6), textcoords="offset points",
                fontsize=8.5, color=TINTA, fontfamily=SANS,
                zorder=9,
            )

    # rótulos dos núcleos urbanos — halo claro para legibilidade sobre qualquer camada
    import matplotlib.patheffects as pe

    admin2_labels = admin2_clip.dropna(subset=["adm2_pcode"])
    for pcode, rotulo in [("MZ0501", "TETE"), ("MZ0510", "MOATIZE")]:
        alvo = admin2_labels[admin2_labels["adm2_pcode"] == pcode]
        if alvo.empty:
            continue
        c = alvo.geometry.centroid.iloc[0]
        ax_main.text(
            c.x, c.y, rotulo, fontsize=10.5, color=TINTA, fontstyle="italic",
            fontweight="semibold", ha="center", va="center", zorder=14,
            path_effects=[pe.withStroke(linewidth=3.0, foreground=PAPEL)],
        )

    # moldura da AOI
    aoi_poly_metrico.boundary.plot(ax=ax_main, color=TINTA, linewidth=1.2, zorder=12)

    desenhar_grade_coordenadas(ax_main, aoi_4326, CRS_METRICO, passo_graus=0.1)
    desenhar_barra_escala(ax_main)
    desenhar_seta_norte(ax_main)

    ax_main.set_xticks([])
    ax_main.set_yticks([])
    for spine in ax_main.spines.values():
        spine.set_visible(True)
        spine.set_color(TINTA)
        spine.set_linewidth(1.0)
    ax_main.grid(False)

    # A nota sobre geometria ausente ("25 de Setembro") vai na legenda — ver
    # montar_legenda() — não no corpo do mapa, para não colidir com a barra de escala.
    nomes_sem_geom = (
        ", ".join(pontos_sem_geom["nome"].tolist()) if not pontos_sem_geom.empty else None
    )

    titulo_kicker(fig)

    # -----------------------------------------------------------------
    # Encarte 1 — província de Tete
    # -----------------------------------------------------------------
    ax_prov = fig.add_axes([0.075, 0.0775, 0.30, 0.3083])
    admin2_4326 = admin["admin2"]
    tete_prov_2 = admin2_4326[admin2_4326["adm1_pcode"] == "MZ05"]
    tete_prov_2.plot(ax=ax_prov, facecolor=PAPEL_CL, edgecolor=FILETE, linewidth=0.6, zorder=1)
    tete_prov_2.boundary.plot(ax=ax_prov, color=GRAFITE, linewidth=0.5, zorder=2)
    aoi_poly_4326.boundary.plot(ax=ax_prov, color=TINTA, linewidth=1.1, zorder=4)
    aoi_poly_4326.plot(ax=ax_prov, facecolor=TERRACOTA, alpha=0.25, edgecolor="none", zorder=3)

    b = tete_prov_2.total_bounds
    margb = (b[2] - b[0]) * 0.06
    ax_prov.set_xlim(b[0] - margb, b[2] + margb)
    ax_prov.set_ylim(b[1] - margb, b[3] + margb)
    ax_prov.set_xticks([])
    ax_prov.set_yticks([])
    for spine in ax_prov.spines.values():
        spine.set_color(GRAFITE)
        spine.set_linewidth(0.8)
    ax_prov.text(
        0.02, 0.96, "PROVÍNCIA DE TETE", transform=ax_prov.transAxes, fontsize=7.5,
        color=TERRACOTA, fontweight="semibold", ha="left", va="top",
        fontfamily=SANS,
    )

    # -----------------------------------------------------------------
    # Encarte 2 — Moçambique
    # -----------------------------------------------------------------
    ax_pais = fig.add_axes([0.385, 0.0775, 0.22, 0.3083])
    admin0 = admin["admin0"]
    admin1 = admin["admin1"]
    admin0.plot(ax=ax_pais, facecolor=PAPEL_CL, edgecolor=GRAFITE, linewidth=0.6, zorder=1)
    admin1.boundary.plot(ax=ax_pais, color=FILETE, linewidth=0.4, zorder=2)
    tete_prov_1 = admin1[admin1["adm1_pcode"] == "MZ05"]
    tete_prov_1.plot(ax=ax_pais, facecolor=ARDOSIA, edgecolor=TINTA, linewidth=0.6, zorder=3)

    bp = admin0.total_bounds
    margp = (bp[2] - bp[0]) * 0.06
    ax_pais.set_xlim(bp[0] - margp, bp[2] + margp)
    ax_pais.set_ylim(bp[1] - margp, bp[3] + margp)
    ax_pais.set_xticks([])
    ax_pais.set_yticks([])
    for spine in ax_pais.spines.values():
        spine.set_color(GRAFITE)
        spine.set_linewidth(0.8)
    ax_pais.text(
        0.06, 0.97, "MOÇAMBIQUE", transform=ax_pais.transAxes, fontsize=7.5,
        color=ARDOSIA, fontweight="semibold", ha="left", va="top",
        fontfamily=SANS,
    )

    montar_legenda(fig, nomes_sem_geom)
    montar_rodape(fig, estudo)

    return fig


def titulo_kicker(fig):
    fig.text(
        0.075, 0.975, "ÁREA DE ESTUDO", fontsize=10.5, color=TERRACOTA,
        fontweight="semibold", fontfamily=SANS, ha="left",
        # versalete aproximado: caixa alta já aplicada ao texto
    )
    fig.text(
        0.075, 0.955,
        f"Tete e Moatize, Moçambique — mancha classificada, {ANO}",
        fontsize=19, color=TINTA, fontfamily=SERIF, ha="left", va="top",
    )
    import textwrap

    subtitulo = (
        "Camadas classificadas em três conjuntos mutuamente exclusivos (urbano, "
        "industrial-minerário, reassentamento), hidrografia e povoados de reassentamento "
        "georreferenciados."
    )
    fig.text(
        0.075, 0.917, "\n".join(textwrap.wrap(subtitulo, width=100)),
        fontsize=10, color=GRAFITE, fontfamily=SANS, ha="left", va="top", linespacing=1.4,
    )


def montar_legenda(fig, nomes_sem_geom=None):
    ax_leg = fig.add_axes([0.635, 0.0775, 0.30, 0.3083])
    ax_leg.axis("off")
    ax_leg.set_facecolor(PAPEL)

    y = 0.98
    ax_leg.text(0, y, "LEGENDA", fontsize=8, color=TERRACOTA, fontweight="semibold",
                fontfamily=SANS, transform=ax_leg.transAxes, va="top")
    y -= 0.09

    itens_area = [
        (ARDOSIA, "urbano (fora da mineração)"),
        (TERRACOTA, "industrial / pegada minerária"),
        (TERRACOTA_NEV, "reassentamento (buffer classificado)"),
    ]
    for cor, rotulo in itens_area:
        borda = TINTA if cor == TERRACOTA_NEV else "none"
        ax_leg.add_patch(Rectangle(
            (0, y - 0.045), 0.055, 0.055, transform=ax_leg.transAxes,
            facecolor=cor, edgecolor=borda, linewidth=0.6, clip_on=False,
        ))
        ax_leg.text(0.075, y - 0.018, rotulo, fontsize=8, color=TINTA, fontfamily=SANS,
                    transform=ax_leg.transAxes, va="center")
        y -= 0.085

    ax_leg.plot([0.01, 0.045], [y - 0.005, y - 0.005], color=ARDOSIA_CL, linewidth=2.2,
                transform=ax_leg.transAxes)
    ax_leg.text(0.075, y - 0.005, "hidrografia (HydroRIVERS v10)", fontsize=8, color=TINTA,
                fontfamily=SANS, transform=ax_leg.transAxes, va="center")
    y -= 0.085

    ax_leg.plot([0.028], [y - 0.005], marker="D", color=TERRACOTA, markersize=7,
                markeredgecolor=PAPEL, markeredgewidth=0.8, transform=ax_leg.transAxes)
    ax_leg.text(0.075, y - 0.005, "povoado de reassentamento (georreferenciado)", fontsize=8,
                color=TINTA, fontfamily=SANS, transform=ax_leg.transAxes, va="center")
    y -= 0.085

    ax_leg.plot([0.01, 0.045], [y - 0.005, y - 0.005], color=GRAFITE, linewidth=0.9,
                linestyle=(0, (4, 3)), transform=ax_leg.transAxes)
    ax_leg.text(0.075, y - 0.005, "limite distrital (Cidade de Tete / Moatize)", fontsize=8,
                color=TINTA, fontfamily=SANS, transform=ax_leg.transAxes, va="center")
    y -= 0.10

    aviso = (
        "Advertência de acurácia (docs/ADR/0009, reexecutado em docs/ADR/0014): a camada "
        f"'urbano' tem {acuracia_texto.nota_comissao_construido()} Esta camada NÃO é "
        "cadastro; é insumo classificado, sujeito a comissão alta."
    )
    import textwrap

    ax_leg.text(
        0, y, "\n".join(textwrap.wrap(aviso, width=62)), fontsize=6.6, color=GRAFITE,
        fontfamily=SANS, transform=ax_leg.transAxes, va="top", linespacing=1.5,
        bbox=dict(boxstyle="square,pad=0.35", facecolor=TERRACOTA_NEV, edgecolor="none"),
    )
    y -= 0.235

    if nomes_sem_geom:
        nota_geom = (
            f"Sem coordenada localizável em fonte aberta: {nomes_sem_geom} — não "
            "representado(a) no mapa (não inventado; ver data/provenance_parts/"
            "reassentamento.md)."
        )
        ax_leg.text(
            0, y, "\n".join(textwrap.wrap(nota_geom, width=62)), fontsize=6.6,
            color=GRAFITE, fontstyle="italic", fontfamily=SANS,
            transform=ax_leg.transAxes, va="top", linespacing=1.5,
        )


def montar_rodape(fig, estudo):
    import textwrap

    linha1 = (
        "Fontes — limites administrativos: HDX COD-AB Moçambique (ITOS/OCHA), P-codes do "
        "esquema COD-AB (§ config/unidades.yaml). Hidrografia: HydroRIVERS v10 África "
        "(Lehner & Grill 2013). Camadas classificadas (urbano/industrial/reassentamento, "
        f"{ANO}): classificação própria, pipeline/01_imagery/classificacao.py. "
        "Reassentamentos: georreferenciamento próprio via OSM/Nominatim, "
        "data/raw/reassentamentos.geojson."
    )
    linha2 = (
        "Projeção — mapa principal: EPSG:32736 (UTM 36S), métrica de área; encartes: "
        "EPSG:4326, só localização. A série temporal de área construída (não mostrada "
        "aqui) é a do WSF Evolution (DLR), não a classificação própria — docs/ADR/0008. "
        "Nenhuma cava de mina contada como urbano (§10 do prompt-mestre)."
    )
    # Quebra manual e determinística — evita que uma linha única exceda a largura da
    # figura e infle o bbox 'tight' do savefig (não confiar no wrap=True do matplotlib
    # para texto ancorado em coordenadas de figura, que não conhece a largura útil aqui).
    texto = "\n".join(textwrap.wrap(linha1, width=150)) + "\n" + "\n".join(
        textwrap.wrap(linha2, width=150)
    )
    fig.text(0.075, 0.012, texto, fontsize=6.3, color=PEDRA, fontfamily=SANS,
              ha="left", va="bottom", linespacing=1.5)


# ---------------------------------------------------------------------------
# Provenância
# ---------------------------------------------------------------------------

def gravar_meta(caminhos_saida: list[Path]) -> Path:
    meta = {
        "figura": "mapa de localização — Tete e Moatize",
        "ano_camadas_classificadas": ANO,
        "arquivos_saida": [str(p.relative_to(REPO_ROOT)) for p in caminhos_saida],
        "insumos": {
            nome: (
                str(p.relative_to(REPO_ROOT)),
                hash_arquivo(p) if p.is_file() else "diretório/zip — hash do zip abaixo",
            )
            for nome, p in CAMINHOS.items()
            if p.exists()
        },
        "script": "pipeline/04_figures/mapa_localizacao.py",
        "commit_git": commit_git_atual(),
        "hash_config_study_yaml": hash_arquivo(REPO_ROOT / "config" / "study.yaml"),
        "crs_mapa_principal": CRS_METRICO,
        "crs_encartes": CRS_EXIBICAO,
        "selo": "observado",
        "ressalvas": [
            f"Camada 'urbano' com {acuracia_texto.nota_comissao_construido()} "
            "Não é cadastro.",
            "Série temporal de área construída é do WSF Evolution, não da classificação "
            "própria (docs/ADR/0008).",
            "'25 de Setembro' sem geometria localizável em fonte aberta — não representado "
            "no mapa, não inventado.",
        ],
        "data_geracao": dt.datetime.now(tz=dt.UTC).isoformat(),
    }
    caminho_meta = OUT_FIG / "mapa_localizacao.meta.json"
    caminho_meta.write_text(json.dumps(meta, indent=2, ensure_ascii=False), encoding="utf-8")
    return caminho_meta


def main():
    OUT_FIG.mkdir(parents=True, exist_ok=True)
    fig = montar_figura()

    caminho_pdf = OUT_FIG / "mapa_localizacao.pdf"
    caminho_png = OUT_FIG / "mapa_localizacao.png"
    # bbox_inches=None sobrepõe o 'savefig.bbox: tight' global do Sistema Ardósia: o
    # orçamento de layout desta figura já é fixo em polegadas (montar_figura()), e um
    # recorte automático por bbox de conteúdo tornaria o tamanho da tela dependente da
    # métrica de fonte da máquina que renderiza — não determinístico entre ambientes.
    fig.savefig(caminho_pdf, format="pdf", bbox_inches=None)
    fig.savefig(caminho_png, format="png", dpi=300, bbox_inches=None)
    plt.close(fig)

    caminho_meta = gravar_meta([caminho_pdf, caminho_png])
    print(f"[mapa_localizacao] gravado: {caminho_pdf}")
    print(f"[mapa_localizacao] gravado: {caminho_png}")
    print(f"[mapa_localizacao] gravado: {caminho_meta}")


if __name__ == "__main__":
    main()
