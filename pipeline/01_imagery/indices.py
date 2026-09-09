#!/usr/bin/env python3
"""pipeline/01_imagery/indices.py — índices espectrais a partir dos compostos (§5.1).

Lê os compostos multibanda gravados por `compostos.py`
(`data/processed/imagery/composto_<ano>_<res>m_<epsg>.tif`) e calcula, para
cada ano-âncora, os índices declarados em `config/study.yaml -> indices`
(NDBI, NDVI, MNDWI, EVI, NDWI), na mesma grade e CRS do composto (nenhuma
reamostragem: a divisão de banda por banda já está pixel a pixel alinhada).

Fórmulas (todas em reflectância de superfície, adimensional):
  NDVI  = (nir - red) / (nir + red)                              [Rouse et al. 1974]
  NDBI  = (swir16 - nir) / (swir16 + nir)                        [Zha et al. 2003]
  MNDWI = (green - swir16) / (green + swir16)                    [Xu 2006]
  NDWI  = (green - nir) / (green + nir)                          [McFeeters 1996]
  EVI   = 2.5 * (nir - red) / (nir + 6*red - 7.5*blue + 1)       [Huete et al. 2002]

Cada índice é gravado como COG de banda única:
`<indice_minusculo>_<ano>_<res>m_<epsg>.tif`, seguindo a convenção de nomes
do CLAUDE.md. Pixels com alguma banda de reflectância **não positiva** são
mascarados (NaN), não divididos: reflectância de superfície <= 0 é
fisicamente inválida (artefato de correção atmosférica) e é a única origem de
explosão numérica nestas razões. O critério anterior (|denominador| < 0,1)
apagava o Zambeze — ver docs/ADR/0014.

Uso: `uv run python pipeline/01_imagery/indices.py [ano ...]`
Sem argumentos, processa todos os compostos já gravados em `data/processed/imagery/`.
"""

from __future__ import annotations

import hashlib
import json
import re
import subprocess
import sys
from datetime import UTC, datetime
from pathlib import Path

import numpy as np
import rioxarray
import xarray as xr
import yaml

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "00_fetch"))
from _config import carregar_estudo

REPO_ROOT = Path(__file__).resolve().parents[2]
STUDY_YAML = REPO_ROOT / "config" / "study.yaml"
TOLERANCES_YAML = REPO_ROOT / "config" / "tolerances.yaml"
DATA_PROCESSED = REPO_ROOT / "data" / "processed" / "imagery"


def _carregar_criterio_mascara() -> str:
    """Critério declarado em `config/tolerances.yaml ->
    processamento_indices.banda_nao_positiva.criterio` (§10: o critério vive em
    config, não como constante solta no script, para que fique auditável e
    versionado junto com as demais tolerâncias do estudo).

    Serve de contrato: se alguém trocar o critério no YAML sem trocar o código,
    a leitura falha alto em vez de divergir em silêncio.
    """
    with TOLERANCES_YAML.open(encoding="utf-8") as fh:
        tolerances = yaml.safe_load(fh)
    criterio = str(tolerances["processamento_indices"]["banda_nao_positiva"]["criterio"])
    if criterio != CRITERIO_MASCARA_ESPERADO:
        raise ValueError(
            "config/tolerances.yaml -> processamento_indices.banda_nao_positiva."
            f"criterio = {criterio!r}, mas indices.py implementa "
            f"{CRITERIO_MASCARA_ESPERADO!r}"
        )
    return criterio


# Critério de mascaramento (docs/ADR/0014). O critério anterior — |denominador|
# < 0,1 — foi retirado: ele é um limiar ABSOLUTO sobre uma soma de
# reflectâncias e, em água limpa (green baixo E swir16 baixo), o denominador do
# MNDWI cai naturalmente abaixo de 0,1 sem que haja instabilidade numérica
# nenhuma. Medido: o denominador do MNDWI sobre o Zambeze é 0,0821 (2000) e
# 0,0505 (2015), e a regra apagava 32.909 (2000) e 44.364 (2015) pixels — o rio
# inteiro — dos índices, e com ele a agricultura de vazante das margens e ilhas
# (§3, camada iii).
#
# O critério novo é físico, não numérico: mascara-se o pixel em que **alguma
# banda de reflectância usada na fórmula é não positiva**. Reflectância de
# superfície ≤ 0 é fisicamente inválida (artefato de correção atmosférica), e é
# só ali que a razão pode explodir. Medido nesta AOI: os pixels realmente
# patológicos (|índice| > 1) são exatamente 1 por raster, e todos têm banda não
# positiva — o critério novo remove o mesmo pixel e preserva 36.041 dos 36.042
# pixels de água.
CRITERIO_MASCARA_ESPERADO = "banda_de_reflectancia_nao_positiva"
CRITERIO_MASCARA = _carregar_criterio_mascara()

# Guarda numérica residual, **só para o EVI**. O denominador dele
# (nir + 6*red - 7.5*blue + 1) não é uma soma de reflectâncias: é combinação
# linear com coeficiente negativo grande no azul e um "+1" de fundo de dossel.
# Ele pode cancelar mesmo com as três bandas positivas (azul alto por aerossol
# residual), e aí o EVI explode: medido em 2025, 6 pixels saem de [-1, 1.5],
# chegando a -21,3.
#
# Diferença essencial em relação ao critério retirado em docs/ADR/0014: este
# denominador é centrado em ~1, não em zero, e **não tem nada a ver com água**
# (sobre o Zambeze ele fica em 0,6-1,0). Um corte em 0,1 é 10 % do valor
# nominal, não atravessa nenhuma população de interesse e mascara, medido,
# 4 pixels em 2025 e 0 em 2000/2015 — não os 33-44 mil pixels de rio que o
# critério antigo apagava.
EVI_DENOM_MIN = 0.1

NOME_ARQUIVO_RE = re.compile(r"^composto_(\d{4})_(\d+)m_(\d+)\.tif$")


def _bandas_positivas(*bandas: xr.DataArray) -> xr.DataArray:
    """Máscara booleana: todas as bandas de entrada estritamente positivas."""
    valido = bandas[0] > 0
    for banda in bandas[1:]:
        valido = valido & (banda > 0)
    return valido


def _razao_normalizada(a: xr.DataArray, b: xr.DataArray) -> xr.DataArray:
    """(a-b)/(a+b) onde as duas reflectâncias são positivas; NaN onde não são.

    Com a > 0 e b > 0 o denominador é positivo por construção e o resultado
    está em (-1, 1) por álgebra — nenhum corte adicional é necessário.
    """
    return ((a - b) / (a + b)).where(_bandas_positivas(a, b))


def calcular_ndvi(c: xr.Dataset) -> xr.DataArray:
    return _razao_normalizada(c["nir"], c["red"])


def calcular_ndbi(c: xr.Dataset) -> xr.DataArray:
    return _razao_normalizada(c["swir16"], c["nir"])


def calcular_mndwi(c: xr.Dataset) -> xr.DataArray:
    return _razao_normalizada(c["green"], c["swir16"])


def calcular_ndwi(c: xr.Dataset) -> xr.DataArray:
    return _razao_normalizada(c["green"], c["nir"])


def calcular_evi(c: xr.Dataset) -> xr.DataArray:
    nir, red, blue = c["nir"], c["red"], c["blue"]
    denom = nir + 6 * red - 7.5 * blue + 1
    valido = _bandas_positivas(nir, red, blue) & (np.abs(denom) > EVI_DENOM_MIN)
    return (2.5 * (nir - red) / denom).where(valido)


CALCULADORAS = {
    "NDVI": calcular_ndvi,
    "NDBI": calcular_ndbi,
    "MNDWI": calcular_mndwi,
    "NDWI": calcular_ndwi,
    "EVI": calcular_evi,
}


def hash_arquivo(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def commit_git_atual() -> str:
    try:
        return subprocess.check_output(
            ["git", "rev-parse", "HEAD"],
            cwd=REPO_ROOT,
            text=True,
            stderr=subprocess.DEVNULL,
        ).strip()
    except (subprocess.CalledProcessError, FileNotFoundError):
        return "desconhecido (git indisponível)"


def carregar_composto(path: Path) -> xr.Dataset:
    """Lê o COG multibanda e devolve um Dataset com uma variável por banda comum.

    `compostos.py` grava o nome de cada banda na descrição GDAL do band
    (`attrs["long_name"]`, como tupla) — a coordenada `band` em si é sempre
    1..N (o GDAL não aceita rótulo não-inteiro nela). Sem essa descrição não
    há como saber qual banda física é `nir`, `swir16` etc.
    """
    da = rioxarray.open_rasterio(path, masked=True)
    descricoes = da.attrs.get("long_name")
    if not isinstance(descricoes, (tuple, list)) or len(descricoes) != da.sizes["band"]:
        raise ValueError(
            f"{path}: descrições de banda ausentes ou incompletas "
            f"(long_name={descricoes!r}); não é possível mapear as bandas comuns"
        )
    return xr.Dataset(
        {
            nome: da.sel(band=i + 1).drop_vars("band")
            for i, nome in enumerate(descricoes)
        }
    )


def compostos_disponiveis() -> list[tuple[int, Path]]:
    achados = []
    if not DATA_PROCESSED.exists():
        return achados
    for caminho in sorted(DATA_PROCESSED.glob("composto_*.tif")):
        m = NOME_ARQUIVO_RE.match(caminho.name)
        if m:
            achados.append((int(m.group(1)), caminho))
    return achados


def processar_ano(ano: int, caminho_composto: Path, indices_pedidos: list[str]) -> dict:
    composto = carregar_composto(caminho_composto)
    crs = composto[next(iter(composto.data_vars))].rio.crs

    m = NOME_ARQUIVO_RE.match(caminho_composto.name)
    res_m, epsg = m.group(2), m.group(3)

    arquivos_gerados = {}
    for nome_indice in indices_pedidos:
        calculadora = CALCULADORAS.get(nome_indice)
        if calculadora is None:
            print(
                f"[aviso] índice {nome_indice!r} sem fórmula implementada; pulando",
                file=sys.stderr,
            )
            continue
        resultado = calculadora(composto).astype("float32")
        # A aritmética entre bandas herda `attrs` das variáveis de entrada
        # (inclusive `long_name`, que `compostos.py` grava como uma tupla com
        # os 6 nomes de banda do composto multibanda — ver
        # `escrever_composto_cog`). Um índice é sempre 1 banda: manter esse
        # `long_name` de 6 nomes faria o `rio.to_raster` rejeitar a escrita
        # ("Number of names ... does not equal the number of bands").
        resultado.attrs.pop("long_name", None)
        resultado = resultado.rio.write_crs(crs).rio.write_nodata(np.nan)

        nome_arquivo = f"{nome_indice.lower()}_{ano}_{res_m}m_{epsg}.tif"
        caminho_saida = DATA_PROCESSED / nome_arquivo
        resultado.rio.to_raster(
            caminho_saida, driver="COG", compress="deflate", predictor=3, dtype="float32"
        )
        arquivos_gerados[nome_indice] = str(caminho_saida.relative_to(REPO_ROOT))

        registro = {
            "ano": ano,
            "indice": nome_indice,
            "arquivo": str(caminho_saida.relative_to(REPO_ROOT)),
            "arquivo_origem": str(caminho_composto.relative_to(REPO_ROOT)),
            "hash_arquivo_origem": hash_arquivo(caminho_composto),
            "formula": {
                "NDVI": "(nir-red)/(nir+red)",
                "NDBI": "(swir16-nir)/(swir16+nir)",
                "MNDWI": "(green-swir16)/(green+swir16)",
                "NDWI": "(green-nir)/(green+nir)",
                "EVI": "2.5*(nir-red)/(nir+6*red-7.5*blue+1)",
            }[nome_indice],
            "criterio_mascara": CRITERIO_MASCARA,
            "evi_denominador_min": EVI_DENOM_MIN,
            "selo": "observado",
            "data_processamento": datetime.now(UTC).isoformat(),
            "commit_git": commit_git_atual(),
            "hash_config_study_yaml": hash_arquivo(STUDY_YAML),
            "script": "pipeline/01_imagery/indices.py",
        }
        caminho_saida.with_suffix(".tif.meta.json").write_text(
            json.dumps(registro, indent=2, ensure_ascii=False), encoding="utf-8"
        )

    print(
        f"[ok] {ano}: {len(arquivos_gerados)} índices gravados em {DATA_PROCESSED}",
        file=sys.stderr,
    )
    return {"ano": ano, "indices": arquivos_gerados}


def main(argv: list[str]) -> int:
    estudo = carregar_estudo(STUDY_YAML)
    indices_pedidos = estudo["indices"]

    disponiveis = dict(compostos_disponiveis())
    if not disponiveis:
        print(
            "[FALHA] nenhum composto encontrado em "
            f"{DATA_PROCESSED} — rode compostos.py primeiro.",
            file=sys.stderr,
        )
        return 1

    anos = [int(a) for a in argv] if argv else sorted(disponiveis)

    faltando = [a for a in anos if a not in disponiveis]
    if faltando:
        print(
            f"[FALHA] sem composto para os anos {faltando}; "
            "rode compostos.py para esses anos antes de indices.py.",
            file=sys.stderr,
        )
        return 1

    for ano in anos:
        processar_ano(ano, disponiveis[ano], indices_pedidos)
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
