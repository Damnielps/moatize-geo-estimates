#!/usr/bin/env python3
"""pipeline/01_imagery/compostos_chuva.py — composto de estação CHUVOSA e
métricas fenológicas (§5.6.1), usados aqui para separar construído de solo
exposto (§5.1).

## Por que

O construído é espectralmente **estável** entre a estação chuvosa e a seca; o
solo exposto da savana semiárida **esverdeia** na chuva. A amplitude
`NDVI(chuva) - NDVI(seca)` é, portanto, o discriminante físico entre as duas
classes que a classificação só de estação seca confunde. Este script produz
essa amplitude onde os dados permitem — e **falha explicitamente**, ano a ano,
onde não permitem, em vez de preencher com o ano vizinho.

## Critério de viabilidade (declarado ANTES de medir)

Um ano tem composto de chuva utilizável se, na janela nov(A-1)–abr(A):
  1. há >= `MIN_CENAS` cenas da missão do ano, e
  2. >= `MIN_FRACAO_PIXELS_COBERTOS` da AOI tem >= `MIN_OBS_POR_PIXEL`
     observações válidas após máscara de nuvem/sombra.
Estes números não foram escolhidos depois de ver o resultado; estão fixados
aqui e o relatório de cobertura registra o valor medido de cada ano, aprovado
ou reprovado.

Se a missão do ano-âncora reprovar, tenta-se a outra missão Landsat da mesma
geração (TM<->ETM+) na mesma janela — substituto declarado, registrado por ano no
CSV de cobertura, aceitável para NDVI porque TM e ETM+ têm bandpasses quase
idênticos no vermelho e no NIR.

Janela: nov(A-1)–abr(A) — a estação chuvosa que **precede** a estação seca
maio–out(A) do composto principal, isto é, o mesmo ano agrícola.

Saída: `data/processed/imagery/ndvi_chuva_<ano>_30m_32736.tif`,
`ndvi_amplitude_<ano>_30m_32736.tif` e
`data/processed/cobertura_estacao_chuvosa.csv` (todos os anos, inclusive os
reprovados).

Uso: uv run python pipeline/01_imagery/compostos_chuva.py [ano ...]
"""

from __future__ import annotations

import csv
import json
import sys
from datetime import UTC, datetime
from pathlib import Path

import numpy as np
import rasterio
import rioxarray  # noqa: F401
import xarray as xr

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "00_fetch"))
from _config import carregar_estudo

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _stac_common import (
    PLATAFORMA_STAC_POR_MISSAO,
    STAC_ENDPOINT_CANONICO,
    abrir_cliente_stac,
    compor_mediana,
    contar_observacoes_validas,
)
from compostos import (
    DATA_PROCESSED,
    REPO_ROOT,
    STUDY_YAML,
    carregar_colecao_mascarada,
    combinar_fontes,
    commit_git_atual,
    construir_geobox,
    hash_arquivo,
)
from indices import _razao_normalizada

COBERTURA_CSV = REPO_ROOT / "data" / "processed" / "cobertura_estacao_chuvosa.csv"

# Critério de viabilidade — fixado antes da medição (ver docstring).
MIN_CENAS = 3
MIN_OBS_POR_PIXEL = 2
MIN_FRACAO_PIXELS_COBERTOS = 0.90

# Filtro de nuvem de cena para a estação chuvosa. Mais permissivo que os 40%
# da estação seca (`config/study.yaml -> composto.nuvem_max_pct`) porque a
# estação chuvosa é, por definição, mais nublada: manter 40% descartaria cenas
# parcialmente úteis cuja nuvem cai fora da AOI. A máscara fina por pixel
# (qa_pixel/SCL) é a mesma e continua sendo a que decide.
NUVEM_MAX_PCT_CHUVA = 80

# Substituto declarado quando a missão do ano-âncora reprova no critério acima.
# Regra (fixada aqui, aplicada igual em todos os anos): tenta primeiro a missão
# que `config/study.yaml -> sensores.<ano>.missao` define para a estação seca; se
# reprovar, tenta a outra missão Landsat operante na mesma janela. Isto é aceitável
# **para NDVI** entre TM (L5) e ETM+ (L7), cujas bandas vermelha e NIR têm
# bandpasses quase idênticos; NÃO seria aceitável misturar reflectância bruta nem
# incluir OLI (L8/L9), cujo NIR é mais estreito. Por isso a lista de substitutos
# só contém o par TM<->ETM+, e o ano usado é registrado no CSV de cobertura.
MISSAO_SUBSTITUTA = {"LANDSAT_5": "LANDSAT_7", "LANDSAT_7": "LANDSAT_5"}


def janela_chuva(ano: int, mes_inicio: int, mes_fim: int) -> str:
    """nov(ano-1) 01 .. abr(ano) 30 — a janela atravessa o ano-novo."""
    return (
        f"{ano - 1}-{mes_inicio:02d}-01T00:00:00Z/"
        f"{ano}-{mes_fim:02d}-30T23:59:59Z"
    )


def ndvi(bandas: xr.Dataset) -> xr.DataArray:
    """NDVI da estação chuvosa, pela **mesma** função de razão normalizada de
    `indices.py` — inclusive a máscara de denominador quase-zero de
    `config/tolerances.yaml -> processamento_indices.denominador_minimo`.

    Correção de defeito (Fase 1, T3): esta função dividia `(nir-red)/(nir+red)`
    sem mascarar o denominador, ao contrário do NDVI da estação seca. O
    resultado saía da faixa algébrica [-1, 1] onde `nir+red` cancelava
    (`ndvi_chuva_2015` chegava a 2,85), e o erro se propagava para
    `ndvi_amplitude`, que é a feature mais discriminante do classificador.
    Reusar `indices._razao_normalizada` garante que as duas estações passam
    pelo mesmo tratamento numérico — exigência de protocolo idêntico (§5.1).
    """
    return _razao_normalizada(bandas["nir"], bandas["red"])


def ndvi_seca_do_disco(ano: int, res_m: int, epsg: int) -> np.ndarray:
    caminho = DATA_PROCESSED / f"ndvi_{ano}_{res_m}m_{epsg}.tif"
    with rasterio.open(caminho) as src:
        return src.read(1, masked=True).filled(np.nan)


def escrever_cog_float(arr: np.ndarray, path: Path, perfil_ref: dict) -> None:
    perfil = {
        "driver": "COG",
        "height": arr.shape[0],
        "width": arr.shape[1],
        "count": 1,
        "dtype": "float32",
        "crs": perfil_ref["crs"],
        "transform": perfil_ref["transform"],
        "nodata": np.nan,
        "compress": "deflate",
        "predictor": 3,
    }
    path.parent.mkdir(parents=True, exist_ok=True)
    with rasterio.open(path, "w", **perfil) as dst:
        dst.write(arr.astype("float32"), 1)


def processar_ano(ano: int, estudo: dict, client, geobox) -> dict:
    bbox_aoi = estudo["aoi"]["bbox"]
    bbox = [bbox_aoi["xmin"], bbox_aoi["ymin"], bbox_aoi["xmax"], bbox_aoi["ymax"]]
    crs_metrico = estudo["crs"]["metrico"]
    epsg = int(crs_metrico.split(":")[-1])
    fen = estudo["composto_fenologico"]["estacao_chuvosa"]
    sensor_cfg = estudo["sensores"][ano]
    res_m = sensor_cfg["res_m"]

    intervalo = janela_chuva(ano, fen["mes_inicio"], fen["mes_fim"])

    tentativas = [sensor_cfg["missao"]]
    substituta = MISSAO_SUBSTITUTA.get(sensor_cfg["missao"])
    if substituta is not None:
        tentativas.append(substituta)

    registro = {
        "ano": ano,
        "janela": intervalo,
        "nuvem_max_pct_cena": NUVEM_MAX_PCT_CHUVA,
    }
    escolhida = None
    for missao in tentativas:
        plataforma = PLATAFORMA_STAC_POR_MISSAO[missao]
        bandas_l, itens_l = carregar_colecao_mascarada(
            client, "landsat-c2-l2", bbox, intervalo, NUVEM_MAX_PCT_CHUVA, geobox, plataforma
        )
        itens_s2: list = []
        bandas_s2 = None
        if "S2" in sensor_cfg.get("complemento", ""):
            bandas_s2, itens_s2 = carregar_colecao_mascarada(
                client, "sentinel-2-l2a", bbox, intervalo, NUVEM_MAX_PCT_CHUVA, geobox
            )
        n_cenas = len(itens_l) + len(itens_s2)
        if bandas_l is None and bandas_s2 is None:
            fracao, mediana_obs, combinadas, nobs = 0.0, 0.0, None, None
        else:
            combinadas = combinar_fontes(bandas_l, bandas_s2)
            nobs = contar_observacoes_validas(combinadas).compute()
            fracao = float((nobs >= MIN_OBS_POR_PIXEL).mean())
            mediana_obs = float(nobs.median())
        viavel = (n_cenas >= MIN_CENAS) and (fracao >= MIN_FRACAO_PIXELS_COBERTOS)
        registro.update(
            {
                "missao_usada": missao,
                "missao_do_ano_ancora": sensor_cfg["missao"],
                "usou_missao_substituta": missao != sensor_cfg["missao"],
                "n_cenas_landsat": len(itens_l),
                "n_cenas_sentinel2": len(itens_s2),
                "n_cenas_total": n_cenas,
                "fracao_pixels_cobertos": fracao,
                "mediana_obs_por_pixel": mediana_obs,
                "viavel": bool(viavel),
                "motivo": ""
                if viavel
                else (
                    f"missao={missao}: n_cenas={n_cenas} (min {MIN_CENAS}), "
                    f"fração de pixels com >={MIN_OBS_POR_PIXEL} obs = {fracao:.3f} "
                    f"(min {MIN_FRACAO_PIXELS_COBERTOS})"
                ),
            }
        )
        if viavel:
            escolhida = (combinadas, nobs)
            break

    if escolhida is None:
        return registro

    combinadas, nobs = escolhida
    composto = compor_mediana(combinadas).compute()
    ndvi_chuva = ndvi(composto).values
    ndvi_chuva = np.where(nobs.values >= MIN_OBS_POR_PIXEL, ndvi_chuva, np.nan)

    perfil_ref_path = DATA_PROCESSED / f"composto_{ano}_{res_m}m_{epsg}.tif"
    with rasterio.open(perfil_ref_path) as src:
        perfil_ref = {"crs": src.crs, "transform": src.transform}

    amplitude = ndvi_chuva - ndvi_seca_do_disco(ano, res_m, epsg)

    p_chuva = DATA_PROCESSED / f"ndvi_chuva_{ano}_{res_m}m_{epsg}.tif"
    p_amp = DATA_PROCESSED / f"ndvi_amplitude_{ano}_{res_m}m_{epsg}.tif"
    escrever_cog_float(ndvi_chuva, p_chuva, perfil_ref)
    escrever_cog_float(amplitude, p_amp, perfil_ref)

    meta = {
        "ano": ano,
        "selo": "observado",
        "janela_estacao_chuvosa": intervalo,
        "missao_usada": registro["missao_usada"],
        "usou_missao_substituta": registro["usou_missao_substituta"],
        "n_cenas_landsat": registro["n_cenas_landsat"],
        "n_cenas_sentinel2": registro["n_cenas_sentinel2"],
        "itens_landsat": [it.id for it in itens_l],
        "itens_sentinel2": [it.id for it in itens_s2],
        "fracao_pixels_cobertos": fracao,
        "criterio_viabilidade": {
            "min_cenas": MIN_CENAS,
            "min_obs_por_pixel": MIN_OBS_POR_PIXEL,
            "min_fracao_pixels": MIN_FRACAO_PIXELS_COBERTOS,
        },
        "definicao_amplitude": "NDVI(chuva nov(A-1)-abr(A)) - NDVI(seca mai-out(A))",
        "catalogo_stac": STAC_ENDPOINT_CANONICO,
        "data_processamento": datetime.now(UTC).isoformat(),
        "commit_git": commit_git_atual(),
        "hash_config_study_yaml": hash_arquivo(STUDY_YAML),
        "script": "pipeline/01_imagery/compostos_chuva.py",
    }
    for p in (p_chuva, p_amp):
        p.with_suffix(".tif.meta.json").write_text(
            json.dumps(meta, indent=2, ensure_ascii=False), encoding="utf-8"
        )
    return registro


def escrever_csv(registros: list[dict]) -> None:
    COBERTURA_CSV.parent.mkdir(parents=True, exist_ok=True)
    campos = [
        "ano",
        "janela",
        "missao_do_ano_ancora",
        "missao_usada",
        "usou_missao_substituta",
        "n_cenas_landsat",
        "n_cenas_sentinel2",
        "n_cenas_total",
        "nuvem_max_pct_cena",
        "fracao_pixels_cobertos",
        "mediana_obs_por_pixel",
        "viavel",
        "motivo",
    ]
    with COBERTURA_CSV.open("w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=campos)
        w.writeheader()
        for r in registros:
            w.writerow({c: r.get(c, "") for c in campos})


def main(argv: list[str]) -> int:
    estudo = carregar_estudo(STUDY_YAML)
    anos = [int(a) for a in argv] if argv else estudo["anos_ancora"]["imagem"]
    client = abrir_cliente_stac()
    geobox = construir_geobox(estudo["aoi"]["bbox"], estudo["crs"]["metrico"], 30)

    registros = []
    for ano in anos:
        r = processar_ano(ano, estudo, client, geobox)
        registros.append(r)
        print(
            f"[{'ok' if r['viavel'] else 'REPROVADO'}] {ano}: cenas={r['n_cenas_total']} "
            f"cobertura={r.get('fracao_pixels_cobertos', 0):.3f} {r.get('motivo', '')}",
            file=sys.stderr,
        )
    escrever_csv(registros)
    print(f"[ok] {COBERTURA_CSV.relative_to(REPO_ROOT)} gravado", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
