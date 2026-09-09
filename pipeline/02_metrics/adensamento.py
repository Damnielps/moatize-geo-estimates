#!/usr/bin/env python3
"""pipeline/02_metrics/adensamento.py — camada de adensamento 2020–2025.

Implementa **exatamente** `docs/ADR/0016-adensamento-por-concordancia-de-tres-sinais.md`.
Este script não redesenha o método — o ADR é o mandato; qualquer divergência entre os
dois é bug deste arquivo, não liberdade de implementação.

## Resumo do método (ver o ADR para a justificativa de cada escolha)

Grade de 240 m (8×8 pixels de 30 m) sobre a grade canônica (1299, 2144). Domínio =
células completas (`n_pixels_30m == 64`; a AOI tem 268 células parciais na borda sul,
excluídas). Três sinais, cada um convertido a **posto** (ECDF empírica,
`scipy.stats.rankdata`) antes da diferença entre anos — nunca em nível:

- **S1** — ganho de posto de fração construída (`urbano ∪ reassentamento`, industrial
  fora), ECDF calculada sobre células ocupadas em pelo menos um dos dois anos.
- **S2** — inclinação de Theil–Sen (mediana das 15 inclinações par a par) do posto
  anual de luz noturna (Chen/Yu, 2020–2025), postos calculados dentro de cada ano.
- **S3** — resíduo `ECDF_OB(fp) − ECDF_2020(f)` entre a pegada de edificações (Open
  Buildings v3, epoch único ~2023) e a posição de 2020 na MESMA ECDF de S1 (`f_2020`) —
  os dois sinais **partilham o minuendo negativo** (risco R2 do ADR).

Concordância: `V_i = (S_i > 0) & (S_i >= quantile(S_i, TAU))`, `adensando ⇔ ΣV_i ≥ 2`.
Sete classes por precedência (fora_de_dominio > pegada_industrial > consolidado >
expansao_nova > adensando > esparso_estavel > vazio_estavel). Anel periurbano e
distância à borda de 2025 são **atributos**, não critério de classe. Selo: `modelado`.

Todo limiar é `np.quantile` — ver `QUANTIS` abaixo e o contrato T5
(`pipeline/tests/test_adensamento.py`), que varre a AST deste arquivo.

Uso: `uv run python pipeline/02_metrics/adensamento.py`
"""

from __future__ import annotations

import hashlib
import json
import subprocess
import sys
from datetime import UTC, datetime
from pathlib import Path

import geopandas as gpd
import numpy as np
import pandas as pd
import rasterio
import rasterio.features
import rasterio.warp
import shapely.geometry
from scipy.ndimage import distance_transform_edt

sys.path.insert(0, str(Path(__file__).resolve().parent))
import _common as c

REPO_ROOT = Path(__file__).resolve().parents[2]
IMAGERY_DIR = REPO_ROOT / "data" / "processed" / "imagery"
DATA_PROCESSED = REPO_ROOT / "data" / "processed"
DATA_RAW = REPO_ROOT / "data" / "raw"
DATA_INTERIM_ESTAB = REPO_ROOT / "data" / "interim" / "estabilidade"
PROVENANCE_FRAGMENT = REPO_ROOT / "data" / "provenance_parts" / "adensamento.md"

MARCADOR_INICIO_PROV = "<!-- SECAO_ADENSAMENTO_INICIO -->"
MARCADOR_FIM_PROV = "<!-- SECAO_ADENSAMENTO_FIM -->"

ANO_INICIO = 2020
ANO_FIM = 2025
ANOS_LUZ = list(range(ANO_INICIO, ANO_FIM + 1))  # 2020..2025, seis anos
FATOR_GRADE = 8          # 240 m / 30 m — geometria de grade, não calibração
FATOR_GRADE_480M = 16    # 480 m / 30 m — variante de sensibilidade (2x2 estrito)
N_PIXELS_CELULA = FATOR_GRADE * FATOR_GRADE  # 64, geometria de grade
RES_M = 30.0
CELL_M = FATOR_GRADE * RES_M  # 240.0

# §Decisão-2 do ADR: todo limiar é PROBABILIDADE (quantil), nunca valor físico.
# Os valores realizados (calculados na execução) são ecoados literalmente no
# .meta.json e transcritos na emenda datada do ADR — nunca editados aqui.
QUANTIS = {
    "TAU": 0.70,
    "Q_ALTO": 0.80,
    "Q_BAIXO": 0.20,
    "Q_INDUSTRIAL": 0.50,
}

# §Decisão-9 do ADR — critério de publicação por sensibilidade, FIXADO antes de ver o
# resultado. Não é calibrado contra os dados: é o próprio critério editorial. Nomeado
# para que nenhuma comparação no código carregue um literal solto (contrato T5).
FAIXA_RAZAO_PUBLICAVEL_COMO_AREA = (0.5, 2.0)
FAIXA_RAZAO_PUBLICAVEL_COMO_PADRAO = (0.2, 5.0)

# Códigos de classe — §Decisão-6 do ADR, partição exaustiva por precedência.
CLASSES = {
    0: "fora_de_dominio",
    1: "vazio_estavel",
    2: "esparso_estavel",
    3: "adensando",
    4: "expansao_nova",
    5: "consolidado",
    6: "pegada_industrial",
}

UNIDADES = ["tete", "moatize_vila", "cateme", "mwaladzi"]

VIIRS_GLOB = "viirs_like_*_{ano}_tete_aoi.tif"
OPEN_BUILDINGS_CSV = DATA_RAW / "open_buildings_v3_aoi.csv"

RASTER_240M = IMAGERY_DIR / "adensamento_2020_2025_240m_32736.tif"
RASTER_30M = IMAGERY_DIR / "adensamento_2020_2025_30m_32736.tif"
GEOJSON_OUT = IMAGERY_DIR / "adensamento_2020_2025.geojson"
POR_UNIDADE_CSV = DATA_PROCESSED / "adensamento_2020_2025_por_unidade.csv"
SENSIBILIDADE_CSV = DATA_PROCESSED / "adensamento_sensibilidade.csv"


# ---------------------------------------------------------------------------
# Proveniência (mesmo padrão de pipeline/01_imagery/classificacao.py)
# ---------------------------------------------------------------------------


def hash_arquivo(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def commit_git_atual() -> str:
    try:
        return subprocess.check_output(
            ["git", "rev-parse", "HEAD"], cwd=REPO_ROOT, text=True, stderr=subprocess.DEVNULL
        ).strip()
    except (subprocess.CalledProcessError, FileNotFoundError):
        return "desconhecido (git indisponível)"


# ---------------------------------------------------------------------------
# Insumos
# ---------------------------------------------------------------------------


def perfil_referencia(epsg: int) -> dict:
    _, perfil = c.carregar_camada("urbano", ANO_INICIO, epsg=epsg)
    return perfil


def fracao_construido_urbano_reassentamento(ano: int, epsg: int) -> np.ndarray:
    """f_t(c): fração de `urbano ∪ reassentamento` por célula de 240 m — industrial
    fica FORA por construção (§10 do CLAUDE.md: nenhuma cava contada como urbano)."""
    urbano, _ = c.carregar_camada("urbano", ano, epsg=epsg)
    reass, _ = c.carregar_camada("reassentamento", ano, epsg=epsg)
    mask = urbano | reass
    fracao, n_validos = c.agregar_fracao(mask, FATOR_GRADE)
    return fracao, n_validos


def fracao_industrial(ano: int, epsg: int, fator_grade: int = FATOR_GRADE) -> np.ndarray:
    industrial, _ = c.carregar_camada("industrial", ano, epsg=epsg)
    fracao, _ = c.agregar_fracao(industrial, fator_grade)
    return fracao


def _reprojetar_bilinear(caminho: Path, perfil: dict) -> np.ndarray:
    with rasterio.open(caminho) as src:
        origem = src.read(1).astype("float32")
        nodata_origem = src.nodata
        destino = np.full(perfil["shape"], np.nan, dtype="float32")
        rasterio.warp.reproject(
            source=origem,
            destination=destino,
            src_transform=src.transform,
            src_crs=src.crs,
            src_nodata=nodata_origem,
            dst_transform=perfil["transform"],
            dst_crs=perfil["crs"],
            dst_nodata=np.nan,
            resampling=rasterio.warp.Resampling.bilinear,
        )
    return destino


def caminho_viirs(ano: int) -> Path:
    candidatos = sorted(DATA_RAW.glob(f"viirs_like_*_{ano}_tete_aoi.tif"))
    if not candidatos:
        raise FileNotFoundError(
            f"nenhum raster viirs_like_*_{ano}_tete_aoi.tif em {DATA_RAW} "
            "(série Chen/Yu — CLAUDE.md §4.4)"
        )
    return candidatos[0]


def serie_luz_postos_por_celula(
    perfil: dict, epsg: int, fator_grade: int = FATOR_GRADE
) -> np.ndarray:
    """Luz noturna (Chen/Yu, NPP-VIIRS-like) reprojetada bilinear a 30 m, mediada
    por célula de `fator_grade`×30 m (240 m na base; 480 m na variante de
    escala), e convertida a POSTO dentro de cada ano (§Decisão-4 do ADR).
    Retorna array (n_anos, n_lin_celulas, n_col_celulas)."""
    postos_anuais = []
    for ano in ANOS_LUZ:
        luz_30m = _reprojetar_bilinear(caminho_viirs(ano), perfil)
        soma, n_validos = c.grade_agregada(luz_30m, fator_grade)
        # média por célula (ignora pixels NaN, já fora de "validos" se todos os
        # 64 forem NaN — não deveria ocorrer dentro da AOI, mas não se assume).
        with np.errstate(invalid="ignore", divide="ignore"):
            media = soma / np.maximum(n_validos, 1)
        postos = c.posto_ecdf(media, n_validos > 0)
        postos_anuais.append(postos)
    return np.stack(postos_anuais, axis=0)


def theil_sen_exato(y_por_ano: np.ndarray) -> np.ndarray:
    """Inclinação de Theil–Sen EXATA (mediana das inclinações par a par), célula a
    célula, vetorizada sobre os `n_anos` postos anuais. `y_por_ano` tem shape
    `(n_anos, n_celulas...)`. Determinístico, sem seed (§Decisão-8 do ADR)."""
    n_anos = y_por_ano.shape[0]
    x = np.array(ANOS_LUZ, dtype="float64")
    forma_celulas = y_por_ano.shape[1:]
    y_flat = y_por_ano.reshape(n_anos, -1)

    inclinacoes = []
    for i in range(n_anos):
        for j in range(i + 1, n_anos):
            dx = x[j] - x[i]
            inclinacoes.append((y_flat[j] - y_flat[i]) / dx)
    inclinacoes = np.stack(inclinacoes, axis=0)  # (15, n_celulas)
    slope = np.median(inclinacoes, axis=0)
    return slope.reshape(forma_celulas)


def fracao_edificacoes_open_buildings(
    perfil: dict, epsg: int, filtro_confianca: float = 0.0, fator_grade: int = FATOR_GRADE
) -> np.ndarray:
    """fp(c) = Σ area_in_meters / área da célula (57.600 m² a 240 m; escala com
    `fator_grade` na variante `grade_480m`). Sem filtro absoluto de confiança na
    variante `base` (§Decisão-4 do ADR); a variante de sensibilidade
    `ob_conf_mediana` passa `filtro_confianca` como o quantil 0,50 do próprio
    recorte."""
    df = pd.read_csv(
        OPEN_BUILDINGS_CSV, usecols=["latitude", "longitude", "area_in_meters", "confidence"]
    )
    if filtro_confianca > 0.0:
        df = df[df["confidence"] >= filtro_confianca]

    from pyproj import Transformer

    transformer = Transformer.from_crs("EPSG:4326", f"EPSG:{epsg}", always_xy=True)
    xs, ys = transformer.transform(df["longitude"].to_numpy(), df["latitude"].to_numpy())

    linhas, colunas = rasterio.transform.rowcol(perfil["transform"], xs, ys)
    linhas = np.asarray(linhas)
    colunas = np.asarray(colunas)
    n_lin, n_col = perfil["shape"]
    dentro = (linhas >= 0) & (linhas < n_lin) & (colunas >= 0) & (colunas < n_col)
    area_por_pixel = np.zeros(perfil["shape"], dtype="float64")
    areas_validas = df["area_in_meters"].to_numpy()[dentro]
    np.add.at(area_por_pixel, (linhas[dentro], colunas[dentro]), areas_validas)

    soma_celula, _ = c.grade_agregada(area_por_pixel, fator_grade)
    cell_m = fator_grade * RES_M
    return soma_celula / (cell_m * cell_m)


# ---------------------------------------------------------------------------
# Núcleo do método (base + variantes de sensibilidade compartilham isto)
# ---------------------------------------------------------------------------


def calcular_sinais(
    epsg: int,
    fator_grade: int = FATOR_GRADE,
    incluir_s2: bool = True,
    incluir_s3: bool = True,
    filtro_confianca_ob: float = 0.0,
    fontes_urbano_reass: tuple[Path, Path] | None = None,
) -> dict:
    """Calcula S1/S2/S3, os postos de referência e os atributos de fração por
    célula, na grade `fator_grade`×30 m. `fontes_urbano_reass` permite a variante
    `bruta_experimental` substituir as camadas publicadas pelas máscaras brutas
    pré-R1/R2 de `data/interim/estabilidade/` (diagnóstico, §Alternativa (d))."""
    perfil = perfil_referencia(epsg)

    if fontes_urbano_reass is None:
        m_urb_2020, _ = c.carregar_camada("urbano", ANO_INICIO, epsg=epsg)
        m_reass_2020, _ = c.carregar_camada("reassentamento", ANO_INICIO, epsg=epsg)
        m_urb_2025, _ = c.carregar_camada("urbano", ANO_FIM, epsg=epsg)
        m_reass_2025, _ = c.carregar_camada("reassentamento", ANO_FIM, epsg=epsg)
        mask_2020 = m_urb_2020 | m_reass_2020
        mask_2025 = m_urb_2025 | m_reass_2025
    else:
        caminho_2020, caminho_2025 = fontes_urbano_reass
        with rasterio.open(caminho_2020) as src:
            mask_2020 = src.read(1).astype(bool)
        with rasterio.open(caminho_2025) as src:
            mask_2025 = src.read(1).astype(bool)

    f_2020, n_validos = c.agregar_fracao(mask_2020, fator_grade)
    f_2025, n_validos_2025 = c.agregar_fracao(mask_2025, fator_grade)
    assert n_validos.shape == n_validos_2025.shape
    n_pixels_celula = fator_grade * fator_grade
    dominio = n_validos == n_pixels_celula

    dominio_ocupado = dominio & ((f_2020 > 0) | (f_2025 > 0))

    posto_2020 = c.posto_ecdf(f_2020, dominio_ocupado)
    posto_2025 = c.posto_ecdf(f_2025, dominio_ocupado)
    s1 = posto_2025 - posto_2020

    if incluir_s2:
        postos_luz = serie_luz_postos_por_celula(perfil, epsg, fator_grade=fator_grade)
        s2 = theil_sen_exato(postos_luz)
    else:
        s2 = np.zeros_like(f_2020)

    if incluir_s3:
        fp = fracao_edificacoes_open_buildings(
            perfil, epsg, filtro_confianca_ob, fator_grade=fator_grade
        )
        dominio_ob = dominio & (fp > 0)
        posto_ob = c.posto_ecdf(fp, dominio_ob)
        s3 = posto_ob - posto_2020  # partilha o minuendo negativo de S1 (risco R2)
    else:
        s3 = np.zeros_like(f_2020)
        fp = np.zeros_like(f_2020)

    industrial_2025 = fracao_industrial(ANO_FIM, epsg, fator_grade=fator_grade)

    return {
        "perfil": perfil,
        "dominio": dominio,
        "dominio_ocupado": dominio_ocupado,
        "f_2020": f_2020,
        "f_2025": f_2025,
        "s1": s1,
        "s2": s2,
        "s3": s3,
        "fp": fp,
        "fracao_industrial": industrial_2025,
        "n_validos": n_validos,
        "n_pixels_celula": n_pixels_celula,
        "fator_grade": fator_grade,
    }


def classificar(
    sinais: dict,
    tau: float = QUANTIS["TAU"],
    q_alto: float = QUANTIS["Q_ALTO"],
    q_baixo: float = QUANTIS["Q_BAIXO"],
    q_industrial: float = QUANTIS["Q_INDUSTRIAL"],
    concordancia_minima: int = 2,
    incluir_s2: bool = True,
    incluir_s3: bool = True,
) -> dict:
    """Aplica os cortes por quantil (§Decisão-2), a concordância (§Decisão-5) e a
    partição exaustiva por precedência (§Decisão-6). Retorna `classe` (código
    inteiro), `concordancia` (0–3), os três votos e os valores realizados dos
    quantis (para o `.meta.json` e a emenda do ADR)."""
    dominio = sinais["dominio"]
    dominio_ocupado = sinais["dominio_ocupado"]
    f_2020 = sinais["f_2020"]
    f_2025 = sinais["f_2025"]
    s1, s2, s3 = sinais["s1"], sinais["s2"], sinais["s3"]

    def _voto(s: np.ndarray, ativo: bool) -> tuple[np.ndarray, float]:
        if not ativo or not dominio_ocupado.any():
            return np.zeros_like(s, dtype=bool), float("nan")
        corte = float(np.quantile(s[dominio_ocupado], tau))
        voto = dominio_ocupado & (s > 0) & (s >= corte)
        return voto, corte

    v1, corte_s1 = _voto(s1, True)
    v2, corte_s2 = _voto(s2, incluir_s2)
    v3, corte_s3 = _voto(s3, incluir_s3)
    concordancia = v1.astype(int) + v2.astype(int) + v3.astype(int)

    if dominio_ocupado.any():
        valor_q_alto = float(np.quantile(f_2020[dominio_ocupado], q_alto))
        valor_q_baixo = float(np.quantile(f_2020[dominio_ocupado], q_baixo))
    else:
        valor_q_alto = float("nan")
        valor_q_baixo = float("nan")

    fracao_ind = sinais.get("fracao_industrial")
    mascara_industrial = dominio & (fracao_ind > 0) if fracao_ind is not None else None
    if fracao_ind is not None and mascara_industrial.any():
        valor_q_ind = float(np.quantile(fracao_ind[mascara_industrial], q_industrial))
    else:
        fracao_ind = np.zeros_like(f_2020)
        valor_q_ind = float("nan")

    classe = np.zeros_like(f_2020, dtype="uint8")  # 0 = fora_de_dominio, default
    classe[dominio] = 1  # default dentro do domínio: vazio_estavel

    dentro = dominio
    if np.isnan(valor_q_ind):
        industrial_alta = np.zeros_like(dentro)
    else:
        industrial_alta = dentro & (fracao_ind >= valor_q_ind)
    consolidado = dentro & ~industrial_alta & (f_2020 >= valor_q_alto)
    cruza_piso = (f_2020 < valor_q_baixo) & (f_2025 >= valor_q_baixo)
    expansao_nova = dentro & ~industrial_alta & ~consolidado & cruza_piso
    na_faixa_media = (f_2020 >= valor_q_baixo) & (f_2020 < valor_q_alto)
    faixa_media = dentro & ~industrial_alta & ~consolidado & ~expansao_nova & na_faixa_media
    adensando = faixa_media & (concordancia >= concordancia_minima)
    esparso_estavel = faixa_media & ~adensando
    vazio_estavel = dentro & ~industrial_alta & ~consolidado & ~expansao_nova & ~faixa_media

    classe[industrial_alta] = 6
    classe[consolidado] = 5
    classe[expansao_nova] = 4
    classe[adensando] = 3
    classe[esparso_estavel] = 2
    classe[vazio_estavel] = 1
    classe[~dentro] = 0

    return {
        "classe": classe,
        "concordancia": concordancia,
        "v1": v1,
        "v2": v2,
        "v3": v3,
        "cortes_realizados": {
            "TAU_s1": corte_s1,
            "TAU_s2": corte_s2,
            "TAU_s3": corte_s3,
            "Q_ALTO": valor_q_alto,
            "Q_BAIXO": valor_q_baixo,
            "Q_INDUSTRIAL": valor_q_ind,
        },
        "fracao_industrial": fracao_ind,
    }


# ---------------------------------------------------------------------------
# Anel periurbano e distância à borda (atributo, não critério — §Decisão-7)
# ---------------------------------------------------------------------------


def aneis_por_celula(perfil: dict, sinais: dict, estudo: dict, epsg: int) -> dict:
    urbano_2020, _ = c.carregar_camada("urbano", ANO_INICIO, epsg=epsg)
    urbano_2025, _ = c.carregar_camada("urbano", ANO_FIM, epsg=epsg)

    dist_2020_px = distance_transform_edt(~urbano_2020, sampling=RES_M)
    dist_2025_px = distance_transform_edt(~urbano_2025, sampling=RES_M)

    fator = sinais["fator_grade"]
    n_lin_cel, n_col_cel = sinais["dominio"].shape
    meio = fator // 2  # centro do bloco 8x8 -> índice 4 (0-based)
    linhas_centro = np.arange(n_lin_cel) * fator + meio
    colunas_centro = np.arange(n_col_cel) * fator + meio
    linhas_centro = np.clip(linhas_centro, 0, dist_2020_px.shape[0] - 1)
    colunas_centro = np.clip(colunas_centro, 0, dist_2020_px.shape[1] - 1)

    dist_2020_celula = dist_2020_px[np.ix_(linhas_centro, colunas_centro)]
    dist_2025_celula = dist_2025_px[np.ix_(linhas_centro, colunas_centro)]

    aneis_km = estudo["zoneamento_agricola"]["aneis_km"]  # [[0,1],[1,3]] — study.yaml
    limite_1_m = aneis_km[0][1] * 1000  # 1000 — de config/study.yaml, não constante física
    limite_2_m = aneis_km[1][1] * 1000  # 3000 — idem

    anel = np.full(dist_2020_celula.shape, "externo", dtype=object)
    anel[dist_2020_celula == 0] = "intraurbano"
    anel[(dist_2020_celula > 0) & (dist_2020_celula <= limite_1_m)] = "periurbano_0_1km"
    anel[(dist_2020_celula > limite_1_m) & (dist_2020_celula <= limite_2_m)] = "periurbano_1_3km"

    return {
        "anel": anel,
        "dist_borda_urbano_2025_m": dist_2025_celula,
        "limite_1_m": limite_1_m,
        "limite_2_m": limite_2_m,
    }


# ---------------------------------------------------------------------------
# Escrita — raster 240 m, replicação 30 m, vetor, CSV por unidade
# ---------------------------------------------------------------------------


def transform_celula(perfil: dict, fator: int) -> rasterio.Affine:
    t = perfil["transform"]
    return rasterio.Affine(t.a * fator, t.b, t.c, t.d, t.e * fator, t.f)


def escrever_raster_240m(classe: np.ndarray, perfil: dict, epsg: int) -> None:
    transform = transform_celula(perfil, FATOR_GRADE)
    IMAGERY_DIR.mkdir(parents=True, exist_ok=True)
    with rasterio.open(
        RASTER_240M,
        "w",
        driver="COG",
        height=classe.shape[0],
        width=classe.shape[1],
        count=1,
        dtype="uint8",
        crs=f"EPSG:{epsg}",
        transform=transform,
        nodata=255,
        compress="deflate",
        predictor=2,
    ) as dst:
        dst.write(classe.astype("uint8"), 1)


def escrever_raster_30m(classe_240m: np.ndarray, perfil: dict, epsg: int) -> None:
    """Replicação EXATA (nearest, fator 8) da grade de 240 m sobre a grade de
    30 m publicada — mesma resolução das demais camadas, para sobrepor no app,
    sem reamostragem (repete cada valor 8x8 vezes)."""
    linhas_30m, colunas_30m = perfil["shape"]
    classe_30m = np.zeros((linhas_30m, colunas_30m), dtype="uint8")
    n_lin_cel, n_col_cel = classe_240m.shape
    linhas_rep = np.repeat(np.arange(n_lin_cel), FATOR_GRADE)[:linhas_30m]
    colunas_rep = np.repeat(np.arange(n_col_cel), FATOR_GRADE)[:colunas_30m]
    classe_30m[: len(linhas_rep), : len(colunas_rep)] = classe_240m[np.ix_(linhas_rep, colunas_rep)]
    # linhas/colunas além do que a grade de 240 m cobre (borda parcial) ficam 0
    # (fora_de_dominio) por default — coerente com o próprio raster de 240 m.
    with rasterio.open(
        RASTER_30M,
        "w",
        driver="COG",
        height=linhas_30m,
        width=colunas_30m,
        count=1,
        dtype="uint8",
        crs=perfil["crs"],
        transform=perfil["transform"],
        nodata=255,
        compress="deflate",
        predictor=2,
    ) as dst:
        dst.write(classe_30m, 1)


def escrever_geojson(
    classe: np.ndarray,
    atributos: dict,
    perfil: dict,
    epsg: int,
    unidade_por_celula: np.ndarray,
    anel_dict: dict,
) -> int:
    transform = transform_celula(perfil, FATOR_GRADE)
    mask_publicavel = (classe >= 2) & (classe <= 6)  # classes 2–6, por instrução da tarefa
    formas = list(
        rasterio.features.shapes(classe.astype("uint8"), mask=mask_publicavel, transform=transform)
    )
    if not formas:
        gdf = gpd.GeoDataFrame(geometry=[], crs=f"EPSG:{epsg}")
        gdf.to_file(GEOJSON_OUT, driver="GeoJSON")
        return 0

    linhas_out = []
    for geom, valor in formas:
        shp = shapely.geometry.shape(geom)
        # `representative_point()`, NÃO `centroid` — o centróide de um polígono côncavo
        # (comum quando `rasterio.features.shapes` funde vizinhos de mesma classe) pode
        # cair FORA da própria forma, lendo o atributo da célula vizinha errada (T2
        # reprovava 9/443 feições antes desta correção — ver docs/ADR/0016 §Decisão-6:
        # "a classe publicada tem de ser reproduzível a partir dos atributos").
        ponto = shp.representative_point()
        cx, cy = ponto.x, ponto.y
        row, col = rasterio.transform.rowcol(transform, cx, cy)
        row = min(max(row, 0), classe.shape[0] - 1)
        col = min(max(col, 0), classe.shape[1] - 1)
        linhas_out.append(
            {
                "geometry": shp,
                "classe_codigo": int(valor),
                "classe": CLASSES[int(valor)],
                "f_2020": round(float(atributos["f_2020"][row, col]), 6),
                "f_2025": round(float(atributos["f_2025"][row, col]), 6),
                "S1": round(float(atributos["s1"][row, col]), 6),
                "S2": round(float(atributos["s2"][row, col]), 6),
                "S3": round(float(atributos["s3"][row, col]), 6),
                "concordancia": int(atributos["concordancia"][row, col]),
                "fracao_industrial": round(float(atributos["fracao_industrial"][row, col]), 6),
                "anel": str(anel_dict["anel"][row, col]),
                "dist_borda_urbano_2025_m": round(
                    float(anel_dict["dist_borda_urbano_2025_m"][row, col]), 2
                ),
                "unidade": str(unidade_por_celula[row, col]),
                "area_km2": shp.area / 1e6,
            }
        )
    gdf = gpd.GeoDataFrame(linhas_out, geometry="geometry", crs=f"EPSG:{epsg}")
    IMAGERY_DIR.mkdir(parents=True, exist_ok=True)
    gdf.to_file(GEOJSON_OUT, driver="GeoJSON")
    return len(gdf)


def escrever_por_unidade_csv(
    classe: np.ndarray, unidade_por_celula: np.ndarray, anel: np.ndarray
) -> None:
    linhas_out = []
    for cod, nome_classe in CLASSES.items():
        for unidade in [*UNIDADES, "fora_da_particao"]:
            for anel_nome in ["intraurbano", "periurbano_0_1km", "periurbano_1_3km", "externo"]:
                sel = (classe == cod) & (unidade_por_celula == unidade) & (anel == anel_nome)
                n = int(sel.sum())
                if n == 0:
                    continue
                linhas_out.append(
                    {
                        "classe_codigo": cod,
                        "classe": nome_classe,
                        "unidade": unidade,
                        "anel": anel_nome,
                        "n_celulas": n,
                        "area_km2": round(n * (CELL_M * CELL_M) / 1e6, 4),
                    }
                )
    df = pd.DataFrame(linhas_out)
    DATA_PROCESSED.mkdir(parents=True, exist_ok=True)
    df.to_csv(POR_UNIDADE_CSV, index=False)


# ---------------------------------------------------------------------------
# Sensibilidade — §Decisão-9 do ADR
# ---------------------------------------------------------------------------


def area_adensando_km2(sinais: dict, **kwargs_classificar) -> float:
    resultado = classificar(sinais, **kwargs_classificar)
    n = int((resultado["classe"] == 3).sum())
    return n * (sinais["fator_grade"] * RES_M) ** 2 / 1e6


def n_sinais_ativos(incluir_s2: bool = True, incluir_s3: bool = True) -> int:
    """S1 é sempre ativo (nunca desligável); S2/S3 são opcionais por variante."""
    return 1 + int(incluir_s2) + int(incluir_s3)


def rodar_sensibilidade(epsg: int) -> pd.DataFrame:
    """Monta a tabela de sensibilidade. `_registrar` é o **único** ponto de
    escrita de uma linha e é privado: nenhum caminho de código pode gravar uma
    área sem passar por `registrar_checada`, que sempre verifica
    `n_sinais_ativos >= concordancia_minima` antes de calcular. Isto é
    estrutural, não uma lista de nomes protegidos — corrige o defeito em que
    `registrar()` era pública e chamada direto para `base`/`tau_*`/`qalto_*`/
    `qbaixo_*`/`ob_conf_mediana`, deixando uma variante futura livre para
    repetir, sem aviso de nenhum teste, o zero estrutural silencioso já
    corrigido uma vez na Emenda 1 do ADR 0016 (2026-09-09, portão da Frente B,
    achado 4)."""
    linhas_out = []

    def _registrar(
        nome: str,
        area_km2: float,
        nota: str,
        n_sinais_ativos_var: int,
        concordancia_minima: int,
    ) -> None:
        if area_km2 == 0.0 and not nota:
            raise ValueError(f"linha '{nome}': area=0 exige nota explicativa")
        linhas_out.append(
            {
                "variante": nome,
                "area_adensando_km2": area_km2 if np.isnan(area_km2) else round(area_km2, 4),
                "nota": nota,
                "n_sinais_ativos": n_sinais_ativos_var,
                "concordancia_minima": concordancia_minima,
            }
        )

    def registrar_checada(
        nome: str,
        sinais: dict | None,
        *,
        incluir_s2: bool = True,
        incluir_s3: bool = True,
        concordancia_minima: int = 2,
        nota_ok: str = "",
        nota_indisponivel: str | None = None,
        **kwargs_extra,
    ) -> None:
        """Calcula a área só se `n_sinais_ativos >= concordancia_minima` — uma
        variante com menos sinais ativos do que a concordância exige tem zero
        garantido por aritmética, não por medição (defeito corrigido em
        2026-09-09, ver Emenda 1 do ADR 0016). Nesse caso a linha é NaN com a
        razão registrada em `nota`, nunca um zero silencioso. `sinais=None`
        cobre o caso de insumo ausente nesta execução (ex.: raster interino
        git-ignored não regenerado) — também NaN, também com nota, nunca
        computado a partir de dado que não existe."""
        n_ativos = n_sinais_ativos(incluir_s2, incluir_s3)
        if sinais is None:
            _registrar(
                nome,
                float("nan"),
                nota_indisponivel or "insumo ausente nesta execução — variante não calculada",
                n_ativos,
                concordancia_minima,
            )
            return
        if n_ativos < concordancia_minima:
            _registrar(
                nome,
                float("nan"),
                f"NÃO CALCULÁVEL — {n_ativos} sinal(is) ativo(s) < concordância mínima "
                f"({concordancia_minima}); zero seria artefato da aritmética, não medição "
                "(ver Emenda 1, docs/ADR/0016).",
                n_ativos,
                concordancia_minima,
            )
            return
        area_v = area_adensando_km2(
            sinais,
            incluir_s2=incluir_s2,
            incluir_s3=incluir_s3,
            concordancia_minima=concordancia_minima,
            **kwargs_extra,
        )
        _registrar(nome, area_v, nota_ok, n_ativos, concordancia_minima)

    sinais_base = calcular_sinais(epsg)
    registrar_checada(
        "base",
        sinais_base,
        nota_ok="TAU=0.70, Q_ALTO=0.80, Q_BAIXO=0.20, grade 240 m",
    )

    for tau, nome in ((0.60, "tau_060"), (0.80, "tau_080")):
        registrar_checada(nome, sinais_base, nota_ok=f"TAU={tau} — variante ±1 decil", tau=tau)

    for q, nome in ((0.70, "qalto_070"), (0.90, "qalto_090")):
        registrar_checada(
            nome, sinais_base, nota_ok=f"Q_ALTO={q} — variante ±1 decil", q_alto=q
        )

    for q, nome in ((0.10, "qbaixo_010"), (0.30, "qbaixo_030")):
        registrar_checada(
            nome, sinais_base, nota_ok=f"Q_BAIXO={q} — variante ±1 decil", q_baixo=q
        )

    sinais_480 = calcular_sinais(epsg, fator_grade=FATOR_GRADE_480M)
    registrar_checada(
        "grade_480m",
        sinais_480,
        nota_ok=(
            "Grade 480 m (16x16 pixels de 30 m = agregação 2x2 ESTRITA sobre a grade "
            "de 240 m); S2 e S3 RECALCULADOS nesta resolução (ECDF sobre o novo domínio "
            "de células) — teste de escala, não de amputação de sinal "
            "(corrigido em 2026-09-09, ver Emenda 1 do ADR)."
        ),
    )

    df_ob = pd.read_csv(OPEN_BUILDINGS_CSV, usecols=["confidence"])
    mediana_conf = float(np.quantile(df_ob["confidence"].to_numpy(), 0.50))
    sinais_ob_mediana = calcular_sinais(epsg, filtro_confianca_ob=mediana_conf)
    registrar_checada(
        "ob_conf_mediana",
        sinais_ob_mediana,
        nota_ok=f"Open Buildings filtrado a confidence >= mediana do recorte ({mediana_conf:.4f})",
    )

    registrar_checada(
        "concordancia_3de3",
        sinais_base,
        concordancia_minima=3,
        nota_ok="Exige concordância 3 de 3 sinais, em vez de 2 de 3",
    )
    registrar_checada(
        "sem_S2",
        sinais_base,
        incluir_s2=False,
        nota_ok=(
            "S2 (luz) zerado — concordância decidida só por S1 e S3 "
            "(que partilham f_2020, risco R2)"
        ),
    )
    registrar_checada(
        "sem_S3",
        sinais_base,
        incluir_s3=False,
        nota_ok="S3 (Open Buildings) zerado — mede o efeito do risco R2 (S1/S3 partilham minuendo)",
    )

    caminho_2020 = DATA_INTERIM_ESTAB / "bruta_construido_2020_30m_32736.tif"
    caminho_2025 = DATA_INTERIM_ESTAB / "bruta_construido_2025_30m_32736.tif"
    sinais_bruta = None
    if caminho_2020.exists() and caminho_2025.exists():
        sinais_bruta = calcular_sinais(
            epsg,
            fontes_urbano_reass=(caminho_2020, caminho_2025),
        )
    registrar_checada(
        "bruta_experimental",
        sinais_bruta,
        nota_ok=(
            "S1 sobre data/interim/estabilidade/bruta_construido_* (rótulo bruto do "
            "RF, pré-R1/R2, EXPERIMENTAL); S2 e S3 permanecem ATIVOS e inalterados — "
            "a comparação com a base isola o efeito de R1/R2 em S1, não o número de "
            "sinais (corrigido em 2026-09-09, ver Emenda 1 do ADR) — diagnóstico, não "
            "publicável como resultado (§Alternativa d do ADR)"
        ),
        nota_indisponivel=(
            "data/interim/estabilidade/bruta_construido_*.tif ausente nesta execução "
            "(diretório regenerável, git-ignored) — variante não calculada"
        ),
    )

    return pd.DataFrame(linhas_out)


def razao_sensibilidade(df_sens: pd.DataFrame) -> tuple[float, str, str]:
    """Maior razão de área de `adensando` entre as variantes de ±1 decil e a base
    (§Decisão-9 do ADR: as três famílias `tau_0*`, `qalto_0*`, `qbaixo_0*`).
    Retorna `(razao_max, regime_texto, publicavel_como)`; o terceiro elemento é
    o código curto para `.meta.json` (chave `publicavel_como`): `"area"`,
    `"padrao_espacial"` ou `"diagnostico"`. O critério é o mesmo pré-registrado
    no ADR antes de ver o resultado — não se procura variante para reentrar
    na faixa."""
    base = float(df_sens.loc[df_sens["variante"] == "base", "area_adensando_km2"].iloc[0])
    variantes_1_decil = [
        "tau_060",
        "tau_080",
        "qalto_070",
        "qalto_090",
        "qbaixo_010",
        "qbaixo_030",
    ]
    razoes = []
    for v in variantes_1_decil:
        area_v = float(df_sens.loc[df_sens["variante"] == v, "area_adensando_km2"].iloc[0])
        if base > 0 and area_v > 0:
            r = max(area_v / base, base / area_v)
            razoes.append(r)
    if not razoes:
        return float("nan"), "não calculável — base ou variantes com área 0", "diagnostico"
    razao_max = max(razoes)
    _, teto_area = FAIXA_RAZAO_PUBLICAVEL_COMO_AREA
    _, teto_padrao = FAIXA_RAZAO_PUBLICAVEL_COMO_PADRAO
    if razao_max <= teto_area:
        regime = (
            f"publicada como área (razão <= {teto_area}, "
            f"dentro de {FAIXA_RAZAO_PUBLICAVEL_COMO_AREA})"
        )
        publicavel_como = "area"
    elif razao_max <= teto_padrao:
        regime = (
            f"publicada só como padrão espacial e ordem de grandeza, NÃO como área "
            f"(razão em ({teto_area}, {teto_padrao}])"
        )
        publicavel_como = "padrao_espacial"
    else:
        regime = f"figura de diagnóstico, não resultado (razão > {teto_padrao})"
        publicavel_como = "diagnostico"
    return razao_max, regime, publicavel_como


def gravar_provenance_fragment(meta: dict) -> None:
    """Grava `data/provenance_parts/adensamento.md` a partir de `meta` (o mesmo
    dict serializado nos `.tif.meta.json`) — números lidos de `meta`, nunca
    digitados (mesma regra das demais famílias em `data/provenance_parts/`)."""
    areas = meta["areas_por_classe_km2"]
    valores_realizados = meta["quantis_realizados"]
    tabela_classes = "\n".join(
        f"| `{classe}` | {areas.get(classe, 0.0):.4f} |" for classe in CLASSES.values()
    )
    texto = f"""{MARCADOR_INICIO_PROV}
## Adensamento 2020-2025 — concordância de três sinais (docs/ADR/0016, §5.2/§5.6)

Script: `pipeline/02_metrics/adensamento.py`.
Gerado em {datetime.now(UTC).date().isoformat()}.

Camada `modelado`, grade de {meta["grade_m"]:.0f} m ({meta["fator_grade_pixels_30m"]}×
{meta["fator_grade_pixels_30m"]} pixels de 30 m), domínio = células completas
(`n_pixels_30m == {meta["n_pixels_celula"]}`; {meta["n_celulas_dominio"]} células,
{meta["area_dominio_km2"]:.2f} km²). Três sinais (S1 fração construída própria, S2
inclinação Theil-Sen de luz noturna, S3 resíduo de pegada de edificações Open
Buildings) convertidos a posto (ECDF) e votados contra um corte de quantil
(`TAU = {meta["quantis_declarados"]["TAU"]}` declarado; realizado
`TAU_s1={valores_realizados["TAU_s1"]:.6f}`, `TAU_s2={valores_realizados["TAU_s2"]:.6f}`,
`TAU_s3={valores_realizados["TAU_s3"]:.6f}`) — voto exige também `dominio_ocupado`
(Emenda 2 do ADR 0016). `adensando ⇔ Σ votos ≥ 2`. Sete classes por precedência,
partição exaustiva.

### Área por classe (km², contagem real de pixels de 30 m — ver `docs/ADR/0016`,
### achado 2 do portão da Frente B: `fora_de_dominio` NÃO usa `n_células × área
### nominal`, que superestimava por ~2,67×)

| classe | área (km²) |
|---|---|
{tabela_classes}

### Sensibilidade

Razão máxima entre a variante mais extrema e a base, no primeiro decil de células
adensando: **{meta["razao_sensibilidade_maxima_1_decil"]}** — regime de publicação:
**{meta["regime_publicacao_sensibilidade"]}** (`publicavel_como={meta["publicavel_como"]}`).
Ver `{meta["arquivo_sensibilidade"]}` (todas as variantes `tau_0*`/`qalto_0*`/
`qbaixo_0*`, pré-registradas antes de ver o resultado, §Decisão-9 do ADR).

### Riscos declarados (R1-R10, ver ADR para detalhe)

{chr(10).join(f"- **{k}**: {v}" for k, v in meta["riscos"].items())}

### Saídas

Raster 240 m: `{meta["arquivo_raster_240m"]}`. Raster 30 m (desagregado, mesma classe
em todos os pixels da célula): `{meta["arquivo_raster_30m"]}`. Vetor:
`{meta["arquivo_vetor"]}` ({meta["n_poligonos_vetor"]} polígonos, atributos
`f_2020`/`f_2025`/`s1`/`s2`/`s3`/`concordancia`/`fracao_industrial` — reconstroem
`classe` e `concordancia` sem reexecutar o pipeline, contratos T2/T13 de
`pipeline/tests/test_adensamento.py`). Por unidade:
`{meta["arquivo_por_unidade"]}`.

Não alimenta `stats_by_year_by_unit.csv` (§ Makefile, alvo `metrics`): camada
independente, lida por unidade/ano avulsos. Selo `modelado` em quatro lugares
(raster 240 m, raster 30 m, GeoJSON, CSV por unidade) — risco R10.

{MARCADOR_FIM_PROV}
"""
    PROVENANCE_FRAGMENT.parent.mkdir(parents=True, exist_ok=True)
    PROVENANCE_FRAGMENT.write_text(texto, encoding="utf-8")


# ---------------------------------------------------------------------------
# main
# ---------------------------------------------------------------------------


def main() -> None:
    estudo = c.carregar_estudo()
    epsg = c.epsg_metrico(estudo)

    sinais = calcular_sinais(epsg)
    resultado = classificar(sinais)
    sinais["fracao_industrial"] = resultado["fracao_industrial"]

    perfil = sinais["perfil"]
    anel_dict = aneis_por_celula(perfil, sinais, estudo, epsg)

    pontos = c.pontos_sede_utm(epsg)
    n_lin_cel, n_col_cel = sinais["dominio"].shape
    transform_cel = transform_celula(perfil, FATOR_GRADE)
    linhas_idx, colunas_idx = np.meshgrid(np.arange(n_lin_cel), np.arange(n_col_cel), indexing="ij")
    xs, ys = rasterio.transform.xy(
        transform_cel, linhas_idx.ravel(), colunas_idx.ravel(), offset="center"
    )
    unidade_flat = c.atribuir_unidade_por_centroide(np.asarray(xs), np.asarray(ys), pontos)
    unidade_por_celula = unidade_flat.reshape(n_lin_cel, n_col_cel)
    unidade_por_celula = np.where(sinais["dominio"], unidade_por_celula, "fora_da_particao")

    escrever_raster_240m(resultado["classe"], perfil, epsg)
    escrever_raster_30m(resultado["classe"], perfil, epsg)

    atributos = {
        "f_2020": sinais["f_2020"],
        "f_2025": sinais["f_2025"],
        "s1": sinais["s1"],
        "s2": sinais["s2"],
        "s3": sinais["s3"],
        "concordancia": resultado["concordancia"],
        "fracao_industrial": resultado["fracao_industrial"],
    }
    n_poligonos = escrever_geojson(
        resultado["classe"], atributos, perfil, epsg, unidade_por_celula, anel_dict
    )
    escrever_por_unidade_csv(resultado["classe"], unidade_por_celula, anel_dict["anel"])

    df_sens = rodar_sensibilidade(epsg)
    DATA_PROCESSED.mkdir(parents=True, exist_ok=True)
    df_sens.to_csv(SENSIBILIDADE_CSV, index=False)
    razao_max, regime, publicavel_como = razao_sensibilidade(df_sens)

    # A área de cada classe vem da contagem REAL de pixels de 30 m (`n_validos`),
    # não da contagem de células × área nominal de célula. As classes 1-6 só
    # contêm células completas (n_validos == 64 por construção do domínio), então
    # a fórmula coincide com n_células × CELL_M² para elas — mas `fora_de_dominio`
    # (classe 0) é exatamente o conjunto das células PARCIAIS da borda, onde
    # n_validos < 64. Aplicar CELL_M² a essa classe superestimava sua área por um
    # fator ~2,67 (achado 2 do portão da Frente B, 2026-09-09).
    areas_por_classe = {
        CLASSES[cod]: round(
            int(sinais["n_validos"][resultado["classe"] == cod].sum()) * (RES_M * RES_M) / 1e6,
            4,
        )
        for cod in CLASSES
    }
    n_dominio = int(sinais["dominio"].sum())
    area_dominio_km2 = round(n_dominio * (CELL_M * CELL_M) / 1e6, 2)

    meta = {
        "camada": "adensamento",
        "periodo": [ANO_INICIO, ANO_FIM],
        "selo": "modelado",
        "grade_m": CELL_M,
        "fator_grade_pixels_30m": FATOR_GRADE,
        "n_pixels_celula": N_PIXELS_CELULA,
        "domain_criterio": "n_pixels_30m == 64 (célula completa; ver docs/ADR/0016 §Decisão-3)",
        "n_celulas_dominio": n_dominio,
        "area_dominio_km2": area_dominio_km2,
        "quantis_declarados": QUANTIS,
        "quantis_realizados": resultado["cortes_realizados"],
        "areas_por_classe_km2": areas_por_classe,
        "razao_sensibilidade_maxima_1_decil": None if np.isnan(razao_max) else round(razao_max, 4),
        "regime_publicacao_sensibilidade": regime,
        "publicavel_como": publicavel_como,
        "riscos": {
            "R1": "erro espacialmente estruturado sobrevive ao posto",
            "R2": "S1 e S3 partilham f_2020 — votos não são independentes",
            "R3": (
                "camada não detecta esvaziamento (S1 censurado por baixo pela "
                "catraca R2 de urbano)"
            ),
            "R4": "luz sobreamostrada de ~500 m para 240 m",
            "R5": "S3 pode ser desacordo de sensor, não construção",
            "R6": "janela real de S3 é 2020 -> ~2023, não 2020->2025",
            "R7": "churn de pixel de 31% sobrevive parcialmente à agregação",
            "R8": "dependência dos cortes — ver sensibilidade acima",
            "R9": "moatize_vila possivelmente inflada (25 de Setembro sem geometria)",
            "R10": "camada modelada, risco de ser lida como observada — selo em 4 lugares",
        },
        "arquivo_raster_240m": str(RASTER_240M.relative_to(REPO_ROOT)),
        "arquivo_raster_30m": str(RASTER_30M.relative_to(REPO_ROOT)),
        "arquivo_vetor": str(GEOJSON_OUT.relative_to(REPO_ROOT)),
        "n_poligonos_vetor": n_poligonos,
        "arquivo_por_unidade": str(POR_UNIDADE_CSV.relative_to(REPO_ROOT)),
        "arquivo_sensibilidade": str(SENSIBILIDADE_CSV.relative_to(REPO_ROOT)),
        "estocasticidade": "nenhuma — Theil-Sen exato e quantis são determinísticos",
        "adr": "docs/ADR/0016-adensamento-por-concordancia-de-tres-sinais.md",
        "data_processamento": datetime.now(UTC).isoformat(),
        "commit_git": commit_git_atual(),
        "hash_config_study_yaml": hash_arquivo(REPO_ROOT / "config" / "study.yaml"),
        "script": "pipeline/02_metrics/adensamento.py",
    }
    for caminho in (RASTER_240M, RASTER_30M):
        caminho.with_suffix(".tif.meta.json").write_text(
            json.dumps(meta, indent=2, ensure_ascii=False), encoding="utf-8"
        )

    gravar_provenance_fragment(meta)
    print(f"[ok] {PROVENANCE_FRAGMENT.relative_to(REPO_ROOT)}", file=sys.stderr)

    print(
        f"[ok] adensamento 2020-2025: dominio={area_dominio_km2:.1f} km2, "
        f"adensando={areas_por_classe['adensando']:.2f} km2, "
        f"razao_sensibilidade_max={razao_max:.3f}, regime={regime}",
        file=sys.stderr,
    )


if __name__ == "__main__":
    main()
