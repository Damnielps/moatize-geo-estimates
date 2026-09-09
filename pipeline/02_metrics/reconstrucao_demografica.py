#!/usr/bin/env python3
"""pipeline/02_metrics/reconstrucao_demografica.py — §5.3 CLAUDE.md.

Reconstrução demográfica e domiciliar de Tete e Moatize, dentro dos limites
reais da base de nível A (ver `data/DATA_AUDIT.md` e
`data/provenance_parts/demograficas.md`/`demograficas_terceiros.md`).

## O que este script NÃO faz, e por quê (ler antes de estender)

1. **Não interpola 1997-2007-2017 numa série contínua.** Só 2017 (observado) e
   2025 (modelado, projeção do INE) têm valor de nível A para Cidade de Tete e
   Distrito de Moatize. 1997 (UNSD Demographic Yearbook, só Cidade de Tete) é
   nível B; 2007 (documento INE via Wayback) é nível C — ambos vão para
   `demografia_contexto_nao_nucleo.csv`, nunca para o núcleo. Interpolar entre
   dois pontos por si só (2017->2025) para preencher 2018-2024 fabricaria uma
   trajetória suave que a base não sustenta (a hipótese de trabalho H4 é
   justamente sobre um possível desvio da suavidade nesse intervalo); por isso
   não se faz.
2. **A dasimetria só é executada para Cidade de Tete.** O total de 260.843/
   349.103 é do *Distrito* de Moatize (8.427 km², COD-AB), que se estende muito
   além da mancha construída mapeada (a AOI cobre ~35x39 km em torno do núcleo
   urbano). Distribuir o total distrital sobre a mancha construída mapeada
   implicaria que toda a população rural do distrito mora dentro da mancha
   urbana — errado por construção. Seria necessário o total do posto-sede de
   Moatize (nível ADM3), que o COD-PS não publica (só ADM2). Registrado como
   lacuna, não contornado.
3. **Não se projeta 2027-2040.** Ver seção "Projeções" abaixo: com dois pontos
   (um observado, um modelado-institucional), qualquer extrapolação herdaria a
   premissa de crescimento geométrico já embutida no ponto de 2025 do INE —
   projetar sobre projeção. Não é uma limitação de tempo de execução: é uma
   limitação de disponibilidade de dado, que o Censo 2027 resolve e nada mais
   resolve nesta janela.
4. **Não se constrói o produto de domicílios.** Ver
   `docs/ADR/0010-domicilios-sem-fonte-a.md`.

## O que este script FAZ

- Lê `data/raw/hdx_cod-ps-moz_admpop_adm2_{2017_v2,2025}.csv` (nível A) e grava
  o núcleo demográfico em `data/processed/stats_by_year_by_unit.csv`
  (`familia=demografia`), com selo e nível de fonte em toda linha.
- Grava os pontos de nível B/C (1997, 2007) à parte, em
  `data/processed/demografia_contexto_nao_nucleo.csv`, explicitamente fora do
  núcleo.
- Dasimetria 2017 para Cidade de Tete: distribui os 307.338 habitantes pela
  mancha construída própria (urbano ∪ reassentamento, média 2015/2020 como
  proxy de "circa 2017"), com teste de sensibilidade usando GHSL BUILT-S e
  WSF Evolution como pesos alternativos.

Uso: `uv run python pipeline/02_metrics/reconstrucao_demografica.py`
"""

from __future__ import annotations

import csv
import json
import sys
from datetime import UTC, datetime
from pathlib import Path

import numpy as np
import pandas as pd
import rasterio
import rasterio.warp
import yaml

REPO_ROOT = Path(__file__).resolve().parents[2]
DATA_RAW = REPO_ROOT / "data" / "raw"
DATA_PROCESSED = REPO_ROOT / "data" / "processed"
IMAGERY = DATA_PROCESSED / "imagery"
STUDY_YAML = REPO_ROOT / "config" / "study.yaml"

# Fragmento, não o canônico: forma urbana e demografia gravavam ambos o arquivo final
# em modo "w" e o último apagava o outro (ORCHESTRATION_LOG.md 2-01).
# `pipeline/02_metrics/stats_by_year_by_unit.py` monta o canônico a partir dos fragmentos.
STATS_CSV = REPO_ROOT / "data" / "interim" / "stats_demografia.csv"
CONTEXTO_CSV = DATA_PROCESSED / "demografia_contexto_nao_nucleo.csv"
DASIMETRIA_SENSIB_CSV = DATA_PROCESSED / "populacao_dasimetrica_sensibilidade.csv"
DASIMETRIA_RASTER = IMAGERY / "populacao_dasimetrica_tete_2017_30m_32736.tif"
PROVENANCE_FRAGMENT = REPO_ROOT / "data" / "provenance_parts" / "demografia_fase2.md"

sys.path.insert(0, str(REPO_ROOT / "pipeline" / "01_imagery"))
import classificacao as cls  # noqa: E402  (import depende do sys.path acima)

sys.path.insert(0, str(REPO_ROOT / "pipeline" / "lib"))
import acuracia_texto  # noqa: E402

MARCADOR_INICIO = "<!-- SECAO_DEMOGRAFIA_FASE2_INICIO -->"
MARCADOR_FIM = "<!-- SECAO_DEMOGRAFIA_FASE2_FIM -->"

# ---------------------------------------------------------------------------
# Âncoras de referência para a partição espacial Tete x Moatize (dasimetria).
# Coordenadas já verificadas e usadas em docs/ADR/0001-aoi-final.md (não são
# valores novos/inventados aqui): Cidade de Tete 33.5871E/-16.1604S; Vila de
# Moatize 33.7288E/-16.1178S. EPSG:4326.
# ---------------------------------------------------------------------------
REF_TETE_4326 = (33.5871, -16.1604)
REF_MOATIZE_4326 = (33.7288, -16.1178)

# Âncoras HDX COD-PS: unidade -> (P-code, nome da coluna no CSV de origem)
UNIDADES_HDX = {
    "Cidade de Tete": {
        "pcode": "MZ1006",
        "nome_2017": "Cidade De Tete",
        "nome_2025": "Cidade De Tete",
    },
    "Distrito de Moatize": {"pcode": "MZ1012", "nome_2017": "Moatize", "nome_2025": "Moatize"},
}


def _carregar_yaml(path: Path) -> dict:
    with path.open(encoding="utf-8") as fh:
        return yaml.safe_load(fh)


# ---------------------------------------------------------------------------
# 1. Núcleo A: HDX COD-PS 2017 (observado) e 2025 (modelado)
# ---------------------------------------------------------------------------


def ler_hdx_2017() -> pd.DataFrame:
    caminho = DATA_RAW / "hdx_cod-ps-moz_admpop_adm2_2017_v2.csv"
    df = pd.read_csv(caminho, encoding="utf-8-sig")
    df.columns = [c.strip() for c in df.columns]
    return df


def ler_hdx_2025() -> pd.DataFrame:
    caminho = DATA_RAW / "hdx_cod-ps-moz_admpop_adm2_2025.csv"
    df = pd.read_csv(caminho, encoding="utf-8-sig")
    df.columns = [c.strip() for c in df.columns]
    return df


def montar_nucleo() -> list[dict]:
    """Monta as linhas de núcleo A para `stats_by_year_by_unit.csv`.

    Duas âncoras por unidade (2017 observado, 2025 modelado). Nenhuma
    interpolação entre elas: ver docstring do módulo, item 1.
    """
    df2017 = ler_hdx_2017()
    df2025 = ler_hdx_2025()

    linhas: list[dict] = []
    fonte_2017 = (
        "HDX COD-PS (UNFPA/OCHA), vintage 2017, alinhado ao IV RGPH — "
        "data/raw/hdx_cod-ps-moz_admpop_adm2_2017_v2.csv"
    )
    fonte_2025 = (
        "HDX COD-PS (UNFPA/OCHA), vintage 2025, projeção do INE — "
        "data/raw/hdx_cod-ps-moz_admpop_adm2_2025.csv"
    )
    nota_2017 = (
        "Contagem residente do IV RGPH 2017 reprocessada pelo COD-PS (CC BY-IGO, nível A "
        "independente do documento do INE, que é nível C — data/DATA_AUDIT.md §0.1). NÃO "
        "ajustada pela sub-enumeração: para a Província de Tete (unidade pertinente a este "
        "estudo, todas as suas unidades sendo em Tete) a taxa é 3,8%; a taxa nacional é uma "
        "grandeza distinta, 3,7% — não são duas medidas da mesma coisa, e não se fundem numa "
        "faixa (verificado: o total do quadro provincial bate com a 'População Residente' não "
        "ajustada, não com o total ajustado da brochura nacional — "
        "data/provenance_parts/demograficas.md)."
    )
    nota_2025 = (
        "Projeção institucional do INE, não recontagem. Método de projeção não publicado no "
        "dataset. Risco de circularidade para H4 (§1): se a projeção assume taxa geométrica "
        "fixa, não pode por construção revelar desaceleração real — usar só com esta ressalva "
        "visível (data/DATA_AUDIT.md §0, item 2)."
    )

    for unidade, chaves in UNIDADES_HDX.items():
        linha_2017 = df2017[df2017["ADM2_PT"] == chaves["nome_2017"]]
        if linha_2017.empty:
            raise ValueError(f"unidade {unidade!r} não encontrada no CSV 2017")
        r = linha_2017.iloc[0]
        for variavel, valor in [
            ("populacao_total_residente", int(r["T_TL"])),
            ("populacao_homens", int(r["M_TL"])),
            ("populacao_mulheres", int(r["F_TL"])),
        ]:
            linhas.append(
                {
                    "familia": "demografia",
                    "unidade_geografica": unidade,
                    "ano": 2017,
                    "variavel": variavel,
                    "valor": valor,
                    "unidade_medida": "pessoas",
                    "selo": "observado",
                    "nivel_fonte": "A",
                    "fonte": fonte_2017,
                    "metodo": "contagem censitária (IV RGPH 2017), reprocessada por COD-PS",
                    "nota": nota_2017,
                }
            )

        linha_2025 = df2025[df2025["ADM2_PT"] == chaves["nome_2025"]]
        if linha_2025.empty:
            raise ValueError(f"unidade {unidade!r} não encontrada no CSV 2025")
        r = linha_2025.iloc[0]
        for variavel, valor in [
            ("populacao_total_residente", int(r["T_TL"])),
            ("populacao_homens", int(r["M_TL"])),
            ("populacao_mulheres", int(r["F_TL"])),
        ]:
            linhas.append(
                {
                    "familia": "demografia",
                    "unidade_geografica": unidade,
                    "ano": 2025,
                    "variavel": variavel,
                    "valor": valor,
                    "unidade_medida": "pessoas",
                    "selo": "modelado",
                    "nivel_fonte": "A",
                    "fonte": fonte_2025,
                    "metodo": (
                        "projeção demográfica institucional do INE (método interno não publicado)"
                    ),
                    "nota": nota_2025,
                }
            )

        pop_2017 = int(linha_2017.iloc[0]["T_TL"])
        pop_2025 = int(df2025[df2025["ADM2_PT"] == chaves["nome_2025"]].iloc[0]["T_TL"])
        cagr = (pop_2025 / pop_2017) ** (1 / (2025 - 2017)) - 1
        linhas.append(
            {
                "familia": "demografia",
                "unidade_geografica": unidade,
                "ano": 2025,
                "variavel": "cagr_2017_2025",
                "valor": round(cagr * 100, 3),
                "unidade_medida": "%/ano",
                "selo": "modelado",
                "nivel_fonte": "A",
                "fonte": f"{fonte_2017}; {fonte_2025}",
                "metodo": (
                    "CAGR geométrico entre 2017 (observado) e 2025 (modelado): "
                    "(pop2025/pop2017)^(1/8)-1"
                ),
                "nota": (
                    "Dois pontos não fazem série de tendência; este número mistura uma ponta "
                    "observada com uma ponta modelada e HERDA o risco de circularidade da nota "
                    "de 2025 acima. Não usar como evidência independente de aceleração/"
                    "desaceleração para H1/H4 sem essa ressalva."
                ),
            }
        )

    return linhas


def montar_contexto_b_c() -> list[dict]:
    """Pontos de nível B/C: nunca entram no núcleo, servem só de contexto rotulado."""
    return [
        {
            "unidade_geografica": "Cidade de Tete",
            "ano": 1997,
            "variavel": "populacao_total_residente",
            "valor": 101984,
            "unidade_medida": "pessoas",
            "selo": "observado",
            "nivel_fonte": "B",
            "fonte": (
                "UNSD Demographic Yearbook 2007, Tabela 8 (city proper) — via agregador "
                "citypopulation.de/Wikipedia originalmente"
            ),
            "metodo": "contagem censitária (II RGPH 1997), confirmada em reprocessador da ONU",
            "motivo_nao_nucleo": (
                "Termos de uso da ONU proíbem redistribuição/obra derivada — nível B "
                "(§4.0). Documento primário do INE não localizado (busca exaustiva no "
                "Wayback, ver data/provenance_parts/demograficas.md)."
            ),
        },
        {
            "unidade_geografica": "Distrito de Moatize",
            "ano": 1997,
            "variavel": "populacao_total_residente",
            "valor": None,
            "unidade_medida": "pessoas",
            "selo": "observado",
            "nivel_fonte": "ausente",
            "fonte": "nenhuma fonte A ou B localizada",
            "metodo": "não recuperado",
            "motivo_nao_nucleo": (
                "Valor de §8 (109.103) é citação de agregador, sem reprocessador A/B "
                "localizado. UNSD só lista city proper (Moatize era distrito majoritariamente "
                "rural em 1997). CIESIN/SEDAC, via mais promissora, ficou fora do ar durante "
                "toda a janela de busca — 'via não esgotada por indisponibilidade', não 'dado "
                "inexistente'. Reexecutar quando o domínio voltar."
            ),
        },
        {
            "unidade_geografica": "Cidade de Tete",
            "ano": 2007,
            "variavel": "populacao_total_residente",
            "valor": 155870,
            "unidade_medida": "pessoas",
            "selo": "observado",
            "nivel_fonte": "C",
            "fonte": (
                "data/raw/censo2007-tete-quadro3-populacao-por-idade-distrito-2007.html "
                "(INE, via Wayback)"
            ),
            "metodo": (
                "contagem censitária (III RGPH 2007), lida diretamente do documento primário"
            ),
            "motivo_nao_nucleo": (
                "Proveniência primária resolvida (documento do INE), mas sem texto de licença "
                "localizável em nenhum domínio, ao vivo ou arquivado — nível C por §4.0 regra 1. "
                "Sem reprocessador institucional alternativo (HDX COD-PS só cobre 2017+)."
            ),
        },
        {
            "unidade_geografica": "Distrito de Moatize",
            "ano": 2007,
            "variavel": "populacao_total_residente",
            "valor": 215092,
            "unidade_medida": "pessoas",
            "selo": "observado",
            "nivel_fonte": "C",
            "fonte": (
                "data/raw/censo2007-tete-quadro3-populacao-por-idade-distrito-2007.html "
                "(INE, via Wayback)"
            ),
            "metodo": (
                "contagem censitária (III RGPH 2007), lida diretamente do documento primário"
            ),
            "motivo_nao_nucleo": "mesma razão da linha acima (nível C, §4.0 regra 1).",
        },
    ]


def gravar_csv(linhas: list[dict], caminho: Path) -> None:
    """Grava CSV com a união de todas as chaves usadas em `linhas` (algumas
    linhas de diagnóstico, p.ex. a correlação espacial da dasimetria, têm
    colunas próprias que as demais não têm — preenchidas em branco)."""
    caminho.parent.mkdir(parents=True, exist_ok=True)
    campos: list[str] = []
    for linha in linhas:
        for chave in linha:
            if chave not in campos:
                campos.append(chave)
    with caminho.open("w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=campos, restval="")
        w.writeheader()
        w.writerows(linhas)


# ---------------------------------------------------------------------------
# 2. Dasimetria 2017 — só Cidade de Tete (ver docstring, item 2)
# ---------------------------------------------------------------------------


def _perfil_referencia() -> dict:
    caminho = IMAGERY / "urbano_2015_30m_32736.tif"
    with rasterio.open(caminho) as src:
        return {
            "transform": src.transform,
            "crs": src.crs,
            "shape": src.shape,
            "width": src.width,
            "height": src.height,
        }


def _mascara_construida_propria(ano: int) -> np.ndarray:
    """urbano ∪ reassentamento (exclui industrial: não é uso residencial)."""
    caminhos = [
        IMAGERY / f"urbano_{ano}_30m_32736.tif",
        IMAGERY / f"reassentamento_{ano}_30m_32736.tif",
    ]
    mask = None
    for caminho in caminhos:
        with rasterio.open(caminho) as src:
            arr = src.read(1).astype(bool)
        mask = arr if mask is None else (mask | arr)
    return mask


def _pixel_centros_utm(perfil: dict) -> tuple[np.ndarray, np.ndarray]:
    """Coordenadas (x, y) do centro de cada pixel, na grade do perfil de referência."""
    transform = perfil["transform"]
    h, w = perfil["shape"]
    cols, rows = np.meshgrid(np.arange(w) + 0.5, np.arange(h) + 0.5)
    xs, ys = rasterio.transform.xy(transform, rows.ravel(), cols.ravel(), offset="center")
    return np.asarray(xs).reshape(h, w), np.asarray(ys).reshape(h, w)


def _ponto_utm(lon: float, lat: float, crs) -> tuple[float, float]:
    xs, ys = rasterio.warp.transform("EPSG:4326", crs, [lon], [lat])
    return xs[0], ys[0]


def _mascara_cluster_tete(perfil: dict) -> np.ndarray:
    """True onde o pixel está mais perto do ponto de referência de Tete do que
    do de Moatize (partição por vizinho mais próximo — não há polígono
    administrativo com geometria em nível A disponível, ver docstring)."""
    xs, ys = _pixel_centros_utm(perfil)
    tete_x, tete_y = _ponto_utm(*REF_TETE_4326, perfil["crs"])
    moat_x, moat_y = _ponto_utm(*REF_MOATIZE_4326, perfil["crs"])
    d_tete = (xs - tete_x) ** 2 + (ys - tete_y) ** 2
    d_moat = (xs - moat_x) ** 2 + (ys - moat_y) ** 2
    return d_tete <= d_moat


def _area_px_km2(perfil: dict) -> float:
    t = perfil["transform"]
    return abs(t.a * t.e) / 1e6


def dasimetria_tete_2017() -> tuple[list[dict], np.ndarray | None, dict | None]:
    perfil = _perfil_referencia()
    cluster_tete = _mascara_cluster_tete(perfil)
    area_px_km2 = _area_px_km2(perfil)

    # Peso 1: classificação própria (urbano ∪ reassentamento), média 2015/2020
    # como proxy de "circa 2017" (ano-âncora do censo fica entre os dois).
    m2015 = _mascara_construida_propria(2015).astype("float32")
    m2020 = _mascara_construida_propria(2020).astype("float32")
    peso_own = (m2015 + m2020) / 2.0

    # Peso 2: GHSL BUILT-S (fração construída por célula), média 2015/2020,
    # reprojetado para a mesma grade (reusa pipeline/01_imagery/classificacao.py).
    ghsl_2015 = cls.ghsl_fracao_construida(2015, perfil)
    ghsl_2020 = cls.ghsl_fracao_construida(2020, perfil)
    peso_ghsl = None
    if ghsl_2015 is not None and ghsl_2020 is not None:
        peso_ghsl = (ghsl_2015 + ghsl_2020) / 2.0

    # Peso 3: WSF Evolution (semente de treino, mas aqui só serve de peso
    # alternativo — não de acurácia). WSF termina em 2015; usa-se a máscara de
    # detecção até 2015 como o único ponto disponível (constante, não média).
    wsf = cls.carregar_wsf_reprojetado(perfil)
    peso_wsf = ((wsf > 0) & (wsf <= 2015)).astype("float32")

    pop_tete_2017 = 307338

    linhas = []
    pesos = {
        "classificacao_propria": peso_own,
        "ghsl_built_s": peso_ghsl,
        "wsf_evolution": peso_wsf,
    }
    for nome, peso in pesos.items():
        if peso is None:
            linhas.append(
                {
                    "metodo_peso": nome,
                    "aplicavel": False,
                    "motivo": "raster de peso indisponível",
                }
            )
            continue
        peso_cluster = np.where(cluster_tete, peso, 0.0)
        soma_peso = float(peso_cluster.sum())
        area_construida_km2 = soma_peso * area_px_km2
        densidade = pop_tete_2017 / area_construida_km2 if area_construida_km2 > 0 else float("nan")
        linhas.append(
            {
                "metodo_peso": nome,
                "aplicavel": True,
                "ano_referencia": 2017,
                "unidade": "Cidade de Tete",
                "populacao_total_distribuida": pop_tete_2017,
                "area_construida_ponderada_km2": round(area_construida_km2, 3),
                "densidade_implicada_hab_km2": round(densidade, 1)
                if not np.isnan(densidade)
                else None,
                "selo": "modelado",
                "nivel_fonte": "A",
                "nota": (
                    "área construída ponderada = soma dos pesos (0-1 por pixel) x área do "
                    "pixel; população total é a mesma por construção (soma=307.338 em "
                    "qualquer peso) — o que varia entre métodos é a área sobre a qual ela é "
                    "espalhada, logo a densidade implicada. Ver "
                    "populacao_dasimetrica_sensibilidade.csv para o efeito quantificado."
                ),
            }
        )

    # Correlação espacial entre pesos, dentro do cluster de Tete — mede o
    # quanto os métodos concordam sobre ONDE a população deveria ir, não só
    # sobre QUANTO território eles somam.
    if peso_ghsl is not None:
        a = peso_own[cluster_tete].ravel()
        b = peso_ghsl[cluster_tete].ravel()
        corr_own_ghsl = (
            float(np.corrcoef(a, b)[0, 1]) if a.std() > 0 and b.std() > 0 else float("nan")
        )
        linhas.append(
            {
                "metodo_peso": "correlacao_own_x_ghsl_no_cluster",
                "aplicavel": True,
                "correlacao_pearson": round(corr_own_ghsl, 4),
                "nota": (
                    "correlação pixel a pixel entre o peso da classificação própria e o peso "
                    "GHSL dentro do cluster de Tete. Baixa correlação indicaria que os métodos "
                    "não só discordam da área total, mas também de ONDE a população deveria "
                    "ser alocada — a comissão medida "
                    f"({acuracia_texto.nota_comissao_construido()}) é a explicação mais "
                    "provável para qualquer divergência observada aqui."
                ),
            }
        )

    # Raster de produto: usa o peso da classificação própria (é o único
    # disponível em todos os anos-âncora, inclusive fora de 2015/2020, o que
    # mantém o produto extensível a outras datas no futuro).
    peso_cluster_own = np.where(cluster_tete, peso_own, 0.0)
    soma_own = peso_cluster_own.sum()
    raster_pop = np.zeros(perfil["shape"], dtype="float32")
    if soma_own > 0:
        raster_pop = (peso_cluster_own / soma_own * pop_tete_2017).astype("float32")

    return linhas, raster_pop, perfil


def salvar_raster_dasimetrico(raster: np.ndarray, perfil: dict) -> None:
    DASIMETRIA_RASTER.parent.mkdir(parents=True, exist_ok=True)
    perfil_saida = {
        "driver": "GTiff",
        "height": raster.shape[0],
        "width": raster.shape[1],
        "count": 1,
        "dtype": "float32",
        "crs": perfil["crs"],
        "transform": perfil["transform"],
        "nodata": 0.0,
        "compress": "deflate",
    }
    with rasterio.open(DASIMETRIA_RASTER, "w", **perfil_saida) as dst:
        dst.write(raster, 1)
    meta = {
        "descricao": (
            "População dasimétrica 2017 (Cidade de Tete), pessoas por célula de 30 m, "
            "peso = classificação própria (urbano ∪ reassentamento), média 2015/2020."
        ),
        "populacao_total_distribuida": 307338,
        "selo": "modelado",
        "nivel_fonte": "A",
        "fonte_populacao": "HDX COD-PS 2017 (data/raw/hdx_cod-ps-moz_admpop_adm2_2017_v2.csv)",
        "fonte_peso": (
            "classificação própria (pipeline/01_imagery), média das máscaras "
            "urbano∪reassentamento de 2015 e 2020"
        ),
        "advertencia_incerteza": (
            f"o peso carrega a comissão medida na classe construído: "
            f"{acuracia_texto.nota_comissao_construido()} Parte do peso pode estar em "
            "pixels que não são de fato construídos, deslocando a densidade implícita. Ver "
            "populacao_dasimetrica_sensibilidade.csv para o teste de sensibilidade GHSL/WSF."
        ),
        "restricao_geografica": (
            "só Cidade de Tete; Distrito de Moatize não distribuído (ver docstring do "
            "script, item 2)"
        ),
        "data_processamento": datetime.now(UTC).isoformat(),
        "script": "pipeline/02_metrics/reconstrucao_demografica.py",
    }
    DASIMETRIA_RASTER.with_suffix(".tif.meta.json").write_text(
        json.dumps(meta, indent=2, ensure_ascii=False), encoding="utf-8"
    )


# ---------------------------------------------------------------------------
# 3. Proveniência
# ---------------------------------------------------------------------------


def gravar_provenance_fragment(pop_2017_tete: int, pop_2025_tete: int) -> None:
    texto = f"""{MARCADOR_INICIO}
## Reconstrução demográfica e domiciliar (§5.3, Fase 2)

Script: `pipeline/02_metrics/reconstrucao_demografica.py`.
Gerado em {datetime.now(UTC).date().isoformat()}.

### Núcleo A — o que existe

| unidade | ano | selo | nível | fonte |
|---|---|---|---|---|
| Cidade de Tete | 2017 | observado | A | HDX COD-PS 2017 (INE IV RGPH via reprocessador) |
| Cidade de Tete | 2025 | modelado | A | HDX COD-PS 2025 (projeção do INE) |
| Distrito de Moatize | 2017 | observado | A | HDX COD-PS 2017 |
| Distrito de Moatize | 2025 | modelado | A | HDX COD-PS 2025 |

Dois pontos por unidade (um observado, um modelado) **não constituem série de
tendência** — não há interpolação entre eles no núcleo. CAGR 2017-2025
calculado e publicado com selo `modelado` e nota de risco de circularidade
para H4.

### Fora do núcleo — contexto rotulado (nível B/C)

`data/processed/demografia_contexto_nao_nucleo.csv`: Cidade de Tete 1997
(101.984, nível B, UNSD Demographic Yearbook); Distrito de Moatize 1997 (não
recuperado em A nem B); Cidade de Tete e Distrito de Moatize 2007 (155.870 e
215.092, nível C, documento do INE via Wayback sem licença localizável).
Nenhum desses quatro pontos sustenta número publicado no núcleo (§4.0 regra 1;
§10).

### Dasimetria 2017 (Cidade de Tete apenas)

`{pop_2017_tete}` habitantes distribuídos pela mancha construída própria
(urbano ∪ reassentamento, média 2015/2020), com teste de sensibilidade contra
GHSL BUILT-S e WSF Evolution como pesos alternativos —
`data/processed/populacao_dasimetrica_sensibilidade.csv`. Selo `modelado`.
Raster: `data/processed/imagery/populacao_dasimetrica_tete_2017_30m_32736.tif`.

**Distrito de Moatize não foi dasimetrizado**: o total (260.843 em 2017) é do
distrito inteiro (8.427 km², COD-AB), muito além da mancha construída mapeada
na AOI; distribuí-lo sobre essa mancha implicaria que toda a população rural
do distrito mora dentro do núcleo urbano — falso por construção. Precisaria de
total ao nível de posto administrativo (ADM3), que o COD-PS não publica.

### Domicílios (§5.3)

Não construído nesta rodada. Ver `docs/ADR/0010-domicilios-sem-fonte-a.md`:
o tamanho médio do domicílio para Tete/Moatize não tem fonte de nível A nem B
confirmada (tabulação do INE não localizada como pública; catálogo mozdata
carrega via JS e não expõe a tabulação diretamente) — qualquer produto
"edificações × tamanho médio do domicílio" herdaria nível C do denominador,
o que a política de dados abertos proíbe de sustentar número publicado.
Google Open Buildings/Microsoft Footprints (nível A, listados em
`data/LICENSES.md`) não foram baixados: buscá-los agora seria custo sem
retorno enquanto o denominador continuar sem fonte A.

### Projeções 2027-2040 (§5.3)

Não construídas. Com dois pontos (2017 observado, 2025 já modelado pelo INE),
qualquer extrapolação própria projetaria sobre uma premissa de crescimento
geométrico já embutida no ponto de 2025 — "compor premissas invisíveis",
exatamente o risco que o enunciado da tarefa aponta. O que resolveria isso é
o Censo 2027 (ainda não publicado) ou uma projeção com metodologia própria
declarada (cohort-component, migração líquida como parâmetro de cenário) a
partir de 2017 apenas — não implementada nesta rodada por não ter sido
solicitada como tal e por depender de parâmetros de fecundidade/mortalidade/
migração que este script não tem em nível A.

### Suficiência para §1

- **Pergunta 1 (linha de base 1997-2005, H1 em população):** não respondível
  em nível A — 1997 não tem fonte A/B verificável para nenhuma das duas
  unidades com valor íntegro (Tete tem só B; Moatize nem isso). H1 já foi
  reformulada por área construída (`docs/ADR/0003`), que é a via respondível.
- **Pergunta 2 (implantação/boom 2005-2015):** não respondível diretamente em
  população de nível A — não há âncora demográfica A entre 2007 (nível C) e
  2017. Só a série de área construída (§5.1/§5.2) cobre esse intervalo em A.
- **Pergunta 6 (bust/transição 2015-2025):** parcialmente respondível. Há dois
  pontos A (2017 observado, 2025 modelado), mas o ponto de 2025 é projeção
  institucional, não recontagem — não pode sozinho provar desaceleração/
  estagnação/reconversão sem o risco de circularidade já registrado para H4.
  Cruzar com luzes noturnas e área construída (outras famílias) é necessário
  para qualquer conclusão de P6, não substituível por este produto isolado.

{MARCADOR_FIM}
"""
    PROVENANCE_FRAGMENT.write_text(texto, encoding="utf-8")


# ---------------------------------------------------------------------------


def main() -> int:
    nucleo = montar_nucleo()
    gravar_csv(nucleo, STATS_CSV)
    print(
        f"[ok] {STATS_CSV.relative_to(REPO_ROOT)} ({len(nucleo)} linhas, familia=demografia)",
        file=sys.stderr,
    )

    contexto = montar_contexto_b_c()
    gravar_csv(contexto, CONTEXTO_CSV)
    print(
        f"[ok] {CONTEXTO_CSV.relative_to(REPO_ROOT)} ({len(contexto)} linhas, fora do núcleo)",
        file=sys.stderr,
    )

    linhas_dasim, raster, perfil = dasimetria_tete_2017()
    gravar_csv(linhas_dasim, DASIMETRIA_SENSIB_CSV)
    print(f"[ok] {DASIMETRIA_SENSIB_CSV.relative_to(REPO_ROOT)}", file=sys.stderr)

    if raster is not None and perfil is not None:
        salvar_raster_dasimetrico(raster, perfil)
        print(f"[ok] {DASIMETRIA_RASTER.relative_to(REPO_ROOT)}", file=sys.stderr)

    pop_2017_tete = int(
        next(
            linha["valor"]
            for linha in nucleo
            if linha["unidade_geografica"] == "Cidade de Tete"
            and linha["ano"] == 2017
            and linha["variavel"] == "populacao_total_residente"
        )
    )
    pop_2025_tete = int(
        next(
            linha["valor"]
            for linha in nucleo
            if linha["unidade_geografica"] == "Cidade de Tete"
            and linha["ano"] == 2025
            and linha["variavel"] == "populacao_total_residente"
        )
    )
    gravar_provenance_fragment(pop_2017_tete, pop_2025_tete)
    print(f"[ok] {PROVENANCE_FRAGMENT.relative_to(REPO_ROOT)}", file=sys.stderr)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
