#!/usr/bin/env python3
"""pipeline/01_imagery/_stac_common.py — utilitários compartilhados da rota STAC.

§11.3 rota (b) — rota de referência, reprodutível sem conta. Usado por
`compostos.py` e `indices.py`. Nada aqui lê `config/study.yaml` diretamente
com valores fixados: os chamadores passam os parâmetros já carregados de lá
(§11.2.1 — config é a única fonte da AOI/janelas/thresholds).

## Catálogo canônico: Planetary Computer (ver docs/ADR/0004)

Testado empiricamente nesta tarefa (2026-09-07): o Element84 Earth Search
resolve os assets de `landsat-c2-l2` para `s3://usgs-landsat`, um bucket
"Requester Pays" da AWS — leitura anônima falha com
`AccessDenied: Anonymous users cannot invoke requests against Requester Pays
buckets`. Isso exige uma conta AWS com faturamento ativo, o que viola a
exigência de §11.3(b) de que a rota de referência "não exige conta". O
Planetary Computer (`pc.sign_inplace`) resolve os mesmos dados via URLs
assinadas (SAS) em Azure Blob Storage, de leitura anônima e gratuita,
confirmado por leitura real de pixel nesta tarefa. Por isso o PC é o
catálogo canônico aqui, mesmo tendo uma lacuna de cobertura conhecida em
2025 (ver ADR 0004) — a alternativa (Element84) não é utilizável sem conta.
"""

from __future__ import annotations

import numpy as np
import planetary_computer as pc
import pystac
import pystac_client
import xarray as xr

STAC_ENDPOINT_CANONICO = "https://planetarycomputer.microsoft.com/api/stac/v1"

# Nomes de asset por coleção STAC, para as bandas que os índices de §5.1/§5.6
# precisam (azul, verde, vermelho, NIR, dois SWIR, e a banda de qualidade).
# Landsat C2 L2 (USGS) usa nomes "comuns" (common names) já no PC e no E84.
# Sentinel-2 L2A no PC usa os códigos de banda nativos (B02 etc.); no E84 usa
# nomes comuns — só importa a variante do PC porque é o catálogo canônico.
BANDAS_POR_COLECAO: dict[str, dict[str, str]] = {
    "landsat-c2-l2": {
        "blue": "blue",
        "green": "green",
        "red": "red",
        "nir": "nir08",
        "swir16": "swir16",
        "swir22": "swir22",
        "qa": "qa_pixel",
    },
    "sentinel-2-l2a": {
        "blue": "B02",
        "green": "B03",
        "red": "B04",
        "nir": "B08",
        "swir16": "B11",
        "swir22": "B12",
        "qa": "SCL",
    },
}

# Plataforma STAC (propriedade `platform`) por missão do YAML (`sensores.<ano>.missao`).
# Filtra o `landsat-c2-l2`, que mistura L5/L7/L8/L9, para a missão que o protocolo
# do estudo determina por ano-âncora (§5.1: "evitar L7 por causa das falhas de linha"
# em 2005/2010, por exemplo).
PLATAFORMA_STAC_POR_MISSAO = {
    "LANDSAT_5": "landsat-5",
    "LANDSAT_7": "landsat-7",
    "LANDSAT_8": "landsat-8",
    "LANDSAT_9": "landsat-9",
}

# qa_pixel (Landsat C2 L2): bits de qualidade (USGS LSDS-1328).
QA_PIXEL_BIT_FILL = 0
QA_PIXEL_BIT_DILATED_CLOUD = 1
QA_PIXEL_BIT_CIRRUS = 2
QA_PIXEL_BIT_CLOUD = 3
QA_PIXEL_BIT_CLOUD_SHADOW = 4

# Defeito corrigido nesta entrega (Fase 1, correção pós-diagnóstico do
# orquestrador): o item STAC do `landsat-c2-l2` declara
# `raster:bands[0].nodata == 1` para o asset `qa_pixel` — e 1 é exatamente o
# valor do bit de FILL (QA_PIXEL_BIT_FILL), não um "nodata" no sentido de
# ausência de leitura. `odc.stac.load` honra esse nodata declarado por
# padrão: ao reprojetar/mosaicar para o `GeoBox` canônico, qualquer pixel
# cujo valor de origem seja 1 é tratado como buraco e substituído pelo
# preenchimento de saída do driver, que é 0 (não há atributo `nodata`
# explícito no GeoTIFF em si — só o valor `1` declarado no STAC). Depois
# disso, `mascara_valida_landsat(0)` dava `(0 & bits_ruins) == 0` verdadeiro
# — o pixel de falha real (fill) passava a máscara como válido. Verificado
# empiricamente nesta tarefa: os cinco itens STAC usados pelos compostos têm
# `raster:bands[0].nodata == 1` neste asset, e o GeoTIFF fonte não tem nodata
# próprio (confirmado por leitura direta do item).
#
# Correção: `stac_cfg` (ver `compostos.carregar_colecao_mascarada`) declara
# explicitamente `nodata: None` para `qa_pixel` na coleção `landsat-c2-l2`.
# Isso faz `odc.stac.load` pular inteiramente a metadata `raster:bands` do
# item para este asset (ver `odc.stac._mdtools._extract_bands`: uma entrada
# de `stac_cfg.assets` com o nome exato do asset é usada tal como está, sem
# nunca chamar `band_metadata()` sobre o item) — nenhum valor é tratado como
# nodata, e o valor real `1` (fill) chega intacto ao array carregado.
QA_PIXEL_VALOR_FILL = 1

# Configuração passada a `odc.stac.load(..., stac_cfg=...)`: desliga o
# nodata declarado (e incorreto para este uso) do asset `qa_pixel`. Ver o
# comentário acima para o porquê. `data_type`/`unit` repetem o que o STAC já
# declara — só `nodata` muda.
STAC_CFG_QA_PIXEL_SEM_NODATA: dict = {
    "landsat-c2-l2": {
        "assets": {
            "qa_pixel": {"data_type": "uint16", "nodata": None, "unit": "bit index"},
        }
    }
}

# SCL (Sentinel-2 L2A, ESA): classes mantidas como observação válida.
# Exclui: 0 no-data, 1 saturado/defeituoso, 3 sombra de nuvem, 8/9 nuvem
# média/alta probabilidade, 10 cirrus fino. Mantém 2 (área escura — ambígua,
# mas não é nuvem), 4 vegetação, 5 solo exposto, 6 água, 7 não classificado,
# 11 neve/gelo (não esperado na AOI, mantido por completude).
SCL_CLASSES_VALIDAS = frozenset({2, 4, 5, 6, 7, 11})


def abrir_cliente_stac(endpoint: str = STAC_ENDPOINT_CANONICO) -> pystac_client.Client:
    """Abre o cliente STAC canônico, assinando os assets automaticamente (PC)."""
    modifier = pc.sign_inplace if "planetarycomputer" in endpoint else None
    return pystac_client.Client.open(endpoint, modifier=modifier)


def buscar_itens(
    client: pystac_client.Client,
    colecao: str,
    bbox: list[float],
    datetime_range: str,
    nuvem_max_pct: int,
    plataforma: str | None = None,
) -> list[pystac.Item]:
    """Busca itens STAC, filtro de nuvem de cena inteira (§5.1: pré-filtro grosseiro,
    a máscara fina vem da qa_pixel/SCL recortada na AOI — a cena inteira pode ter
    nuvem em outra parte da cena e ainda assim estar limpa sobre a AOI, e vice-versa).
    """
    query: dict = {"eo:cloud_cover": {"lte": nuvem_max_pct}}
    if plataforma is not None:
        query["platform"] = {"eq": plataforma}
    search = client.search(
        collections=[colecao],
        bbox=bbox,
        datetime=datetime_range,
        query=query,
    )
    itens = list(search.items())
    # Ordem determinística (§11.2.1): a ordem de retorno do servidor não é uma
    # garantia de API estável; ordenar por id fixa a ordem de composição do
    # dask/xarray entre execuções.
    itens.sort(key=lambda it: it.id)
    return itens


def mascara_valida_landsat(qa_pixel: xr.DataArray) -> xr.DataArray:
    """True nos pixels utilizáveis (sem preenchimento, nuvem, cirrus ou sombra).

    Defesa em profundidade (diagnosticado pelo orquestrador, Fase 1): além dos
    cinco bits de qualidade, rejeita explicitamente `qa == 0`. Zero **não é um
    valor legítimo** de `QA_PIXEL` no Landsat Collection 2 — mesmo um pixel
    perfeitamente limpo tem o bit `clear` (bit 6) aceso, então o valor mínimo
    real para um pixel válido já é 64, nunca 0. Um `qa == 0` só aparece por
    remapeamento indevido de nodata a montante (o defeito corrigido acima, via
    `STAC_CFG_QA_PIXEL_SEM_NODATA`). A checagem é barata, não descarta nenhum
    pixel real e protege contra qualquer remapeação futura equivalente que
    reintroduza o mesmo defeito por outro caminho (nova versão do driver,
    outro catálogo STAC, etc.).
    """
    qa = qa_pixel.astype("uint16")
    bits_ruins = (
        (1 << QA_PIXEL_BIT_FILL)
        | (1 << QA_PIXEL_BIT_DILATED_CLOUD)
        | (1 << QA_PIXEL_BIT_CIRRUS)
        | (1 << QA_PIXEL_BIT_CLOUD)
        | (1 << QA_PIXEL_BIT_CLOUD_SHADOW)
    )
    return xr.apply_ufunc(
        lambda q: ((q & bits_ruins) == 0) & (q != 0),
        qa,
        dask="parallelized",
        output_dtypes=[bool],
    )


def mascara_valida_sentinel2(scl: xr.DataArray) -> xr.DataArray:
    """True nos pixels cuja classe SCL está em SCL_CLASSES_VALIDAS."""
    scl_int = scl.astype("uint8")

    def _valida(bloco: np.ndarray) -> np.ndarray:
        return np.isin(bloco, list(SCL_CLASSES_VALIDAS))

    return xr.apply_ufunc(_valida, scl_int, dask="parallelized", output_dtypes=[bool])


def escalar_landsat_c2_l2(da: xr.DataArray) -> xr.DataArray:
    """Fatores de escala oficiais do Landsat Collection 2 Level-2 (USGS LSDS-1619):
    reflectância = DN * 0.0000275 - 0.2. Sem isso os índices espectrais (razões
    de bandas) saem sistematicamente errados, porque DN é inteiro e não-linear
    em relação à reflectância de superfície pelo offset de -0.2.
    """
    return da.astype("float32") * 0.0000275 - 0.2


def escalar_sentinel2_l2a(da: xr.DataArray) -> xr.DataArray:
    """Sentinel-2 L2A: reflectância = DN / 10000 (BOA_QUANTIFICATION_VALUE)."""
    return da.astype("float32") / 10000.0


def compor_mediana(
    bandas_mascaradas: dict[str, xr.DataArray],
    dim: str = "time",
) -> xr.Dataset:
    """Reduz cada banda por mediana ao longo de `dim`, ignorando NaN (nuvem/sombra
    mascaradas). §5.1/composto.reducao = 'median' em config/study.yaml.
    """
    saida = {}
    for nome, da in bandas_mascaradas.items():
        saida[nome] = da.median(dim=dim, skipna=True)
    return xr.Dataset(saida)


def contar_observacoes_validas(
    bandas_mascaradas: dict[str, xr.DataArray], dim: str = "time"
) -> xr.DataArray:
    """Número de observações válidas (não-NaN) por pixel, para diagnóstico de
    robustez do composto — usa a primeira banda como referência (a máscara é
    aplicada igualmente a todas).
    """
    primeira = next(iter(bandas_mascaradas.values()))
    return primeira.notnull().sum(dim=dim)
