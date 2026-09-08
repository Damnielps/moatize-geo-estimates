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
do CLAUDE.md. Denominadores próximos de zero são mascarados (NaN), não
divididos — evita explosão numérica sem gerar um valor "plausível" falso.

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


def _carregar_denominador_min() -> float:
    """Limiar declarado em `config/tolerances.yaml ->
    processamento_indices.denominador_minimo.min` (§10: "mascare o
    denominador, não afrouxe o contrato" — o limiar vive em config, não como
    constante solta no script, para que fique auditável e versionado junto
    com as demais tolerâncias do estudo).
    """
    with TOLERANCES_YAML.open(encoding="utf-8") as fh:
        tolerances = yaml.safe_load(fh)
    return float(tolerances["processamento_indices"]["denominador_minimo"]["min"])


# Denominador abaixo deste limiar (em valor absoluto) é mascarado: uma soma de
# duas reflectâncias fisicamente plausíveis (each em [-0.2, ~1.6] após o
# offset do Landsat C2 L2) só se aproxima de zero em pixels degenerados
# (cancelamento entre bandas de sinal oposto ou quase nulo). Ver
# `config/tolerances.yaml -> processamento_indices.denominador_minimo` para a
# justificativa completa do valor.
DENOMINADOR_MIN = _carregar_denominador_min()

NOME_ARQUIVO_RE = re.compile(r"^composto_(\d{4})_(\d+)m_(\d+)\.tif$")


def _razao_normalizada(a: xr.DataArray, b: xr.DataArray) -> xr.DataArray:
    denom = a + b
    denom_valido = denom.where(np.abs(denom) > DENOMINADOR_MIN)
    return (a - b) / denom_valido


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
    denom_valido = denom.where(np.abs(denom) > DENOMINADOR_MIN)
    return 2.5 * (nir - red) / denom_valido


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
            "denominador_min_mascarado": DENOMINADOR_MIN,
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
