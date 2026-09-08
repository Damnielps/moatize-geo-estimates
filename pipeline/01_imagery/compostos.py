#!/usr/bin/env python3
"""pipeline/01_imagery/compostos.py — compostos de estação seca por mediana (§5.1).

Rota (b) do §11.3 — STAC público + Python local, **rota de referência** para
reprodutibilidade (não exige conta; ver `docs/ADR/0004-divergencia-catalogos-stac.md`
sobre a escolha do Planetary Computer como catálogo canônico).

Para cada ano-âncora de `config/study.yaml -> anos_ancora.imagem`:
  1. busca cenas na AOI, na janela de estação seca (maio-outubro), com nuvem de
     cena inteira <= `composto.nuvem_max_pct`;
  2. aplica máscara de nuvem/sombra a partir de `qa_pixel` (Landsat) ou `SCL`
     (Sentinel-2) — nunca confia só no `eo:cloud_cover` da cena inteira;
  3. aplica os fatores de escala oficiais (Landsat C2 L2: DN*0.0000275-0.2;
     Sentinel-2 L2A: DN/10000);
  4. reduz por mediana ao longo do tempo, por pixel;
  5. grava um COG multibanda em EPSG:32736 e um `.meta.json` de proveniência.

Nenhum processo estocástico roda aqui: não há uso de `config/seeds.yaml`
(mediana não amostra, não sorteia). A única exigência de determinismo (§11.2.1)
é a ordem de composição dos itens STAC, fixada por `id` em `_stac_common.buscar_itens`.

Uso: `uv run python pipeline/01_imagery/compostos.py [ano ...]`
Sem argumentos, processa todos os anos-âncora de `config/study.yaml`.
"""

from __future__ import annotations

import calendar
import hashlib
import json
import subprocess
import sys
from datetime import UTC, datetime
from pathlib import Path

import numpy as np
import odc.stac
import rioxarray  # noqa: F401  (registra o acessor .rio em xr.DataArray)
import xarray as xr
from odc.geo.geobox import GeoBox
from odc.geo.geom import BoundingBox

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "00_fetch"))
from _config import carregar_estudo

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _stac_common import (
    BANDAS_POR_COLECAO,
    PLATAFORMA_STAC_POR_MISSAO,
    STAC_CFG_QA_PIXEL_SEM_NODATA,
    STAC_ENDPOINT_CANONICO,
    abrir_cliente_stac,
    buscar_itens,
    compor_mediana,
    contar_observacoes_validas,
    escalar_landsat_c2_l2,
    escalar_sentinel2_l2a,
    mascara_valida_landsat,
    mascara_valida_sentinel2,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
STUDY_YAML = REPO_ROOT / "config" / "study.yaml"
DATA_INTERIM = REPO_ROOT / "data" / "interim"
DATA_PROCESSED = REPO_ROOT / "data" / "processed" / "imagery"
PROVENANCE_FRAGMENT = REPO_ROOT / "data" / "provenance_parts" / "imagem_fase1.md"

BANDAS_COMUNS = ["blue", "green", "red", "nir", "swir16", "swir22"]

# Resampling por tipo de banda: contínua (reflectância) -> bilinear;
# categórica (qa_pixel/SCL) -> nearest (interpolar códigos de classe não faz sentido).
RESAMPLING_CONTINUO = "bilinear"
RESAMPLING_CATEGORICO = "nearest"


class CoberturaInsuficiente(RuntimeError):
    """Levantada quando um ano-âncora não tem cobertura STAC suficiente.

    §restrições: "Se um ano não fechar, falhe explicitamente e registre — não
    preencha com o ano vizinho nem invente cobertura."
    """


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


def janela_datas(ano: int, mes_inicio: int, mes_fim: int, janela_anos: int) -> tuple[str, int, int]:
    """Retorna (intervalo ISO 'inicio/fim', ano_inicio, ano_fim) da janela de
    estação seca. `janela_anos=1` -> só o ano-âncora; `janela_anos=3` -> o ano
    anterior, o ano-âncora e o seguinte (ver docs/ADR/0005 para 2010).
    """
    if janela_anos < 1 or janela_anos % 2 == 0:
        raise ValueError(f"janela_anos deve ser ímpar e >=1, recebido {janela_anos}")
    metade = (janela_anos - 1) // 2
    ano_ini, ano_fim = ano - metade, ano + metade
    ultimo_dia = calendar.monthrange(ano_fim, mes_fim)[1]
    inicio = f"{ano_ini}-{mes_inicio:02d}-01T00:00:00Z"
    fim = f"{ano_fim}-{mes_fim:02d}-{ultimo_dia:02d}T23:59:59Z"
    return f"{inicio}/{fim}", ano_ini, ano_fim


def construir_geobox(bbox_aoi: dict, crs_metrico: str, resolucao_m: float) -> GeoBox:
    """Grade canônica única, fixa entre anos (§ contrato: 'grade coerente entre
    anos'). Construída uma vez a partir da AOI de `config/study.yaml`; todo
    `odc.stac.load` desta tarefa usa exatamente este `GeoBox`, nunca um bbox
    recalculado por ano, para garantir alinhamento pixel a pixel entre anos.
    """
    bbox_4326 = BoundingBox(
        bbox_aoi["xmin"], bbox_aoi["ymin"], bbox_aoi["xmax"], bbox_aoi["ymax"], crs="EPSG:4326"
    )
    bbox_nativo = bbox_4326.to_crs(crs_metrico)
    return GeoBox.from_bbox(bbox_nativo, crs=crs_metrico, resolution=resolucao_m, tight=True)


def carregar_colecao_mascarada(
    client,
    colecao: str,
    bbox: list[float],
    datetime_range: str,
    nuvem_max_pct: int,
    geobox: GeoBox,
    plataforma: str | None = None,
) -> tuple[dict[str, xr.DataArray] | None, list]:
    """Busca, carrega, mascara e escala uma coleção STAC para a grade canônica.

    Retorna (bandas_mascaradas, itens) com `bandas_mascaradas=None` se não
    houve nenhum item (o chamador decide se isso é falha ou ausência esperada,
    ex.: Sentinel-2 em 2015 antes do fim do ano).
    """
    itens = buscar_itens(client, colecao, bbox, datetime_range, nuvem_max_pct, plataforma)
    if not itens:
        return None, []

    alias = BANDAS_POR_COLECAO[colecao]
    nome_para_asset = {b: alias[b] for b in BANDAS_COMUNS}
    asset_qa = alias["qa"]
    assets_pedidos = [*list(nome_para_asset.values()), asset_qa]

    resampling = dict.fromkeys(nome_para_asset.values(), RESAMPLING_CONTINUO)
    resampling[asset_qa] = RESAMPLING_CATEGORICO

    # `stac_cfg` desliga o nodata declarado (e incorreto para este uso) de
    # `qa_pixel` no Landsat C2 L2 — ver `_stac_common.STAC_CFG_QA_PIXEL_SEM_NODATA`
    # para o porquê. Sem coleção declarada em `stac_cfg`, o parâmetro não tem
    # efeito (Sentinel-2/SCL não tem esse problema: não declara `nodata` no
    # `raster:bands`, verificado nesta tarefa).
    ds = odc.stac.load(
        itens,
        bands=assets_pedidos,
        geobox=geobox,
        chunks={"time": 1},
        resampling=resampling,
        groupby="id",
        stac_cfg=STAC_CFG_QA_PIXEL_SEM_NODATA,
    )

    asset_para_nome = {v: k for k, v in nome_para_asset.items()}
    ds = ds.rename({asset: asset_para_nome[asset] for asset in nome_para_asset.values()})

    if colecao == "landsat-c2-l2":
        escalar = escalar_landsat_c2_l2
        mascara = mascara_valida_landsat(ds[asset_qa])
    elif colecao == "sentinel-2-l2a":
        escalar = escalar_sentinel2_l2a
        mascara = mascara_valida_sentinel2(ds[asset_qa])
    else:
        raise ValueError(f"coleção sem regra de escala/máscara: {colecao}")

    bandas_mascaradas = {nome: escalar(ds[nome]).where(mascara) for nome in BANDAS_COMUNS}
    return bandas_mascaradas, itens


def combinar_fontes(*fontes: dict[str, xr.DataArray] | None) -> dict[str, xr.DataArray]:
    validas = [f for f in fontes if f is not None]
    if not validas:
        raise CoberturaInsuficiente("nenhuma fonte com observações válidas")
    return {
        nome: xr.concat([f[nome] for f in validas], dim="time", coords="minimal", compat="override")
        for nome in BANDAS_COMUNS
    }


def escrever_composto_cog(composto: xr.Dataset, path: Path, crs: str) -> None:
    """Grava um COG multibanda, um band por variável de `composto`.

    O nome de cada banda vai na *descrição* GDAL do band (não na coordenada
    `band`, que o GDAL força a ser inteira 1..N): `attrs["long_name"]` como
    tupla é o único jeito confirmado (por teste direto nesta tarefa) de o
    `rio.to_raster` escrever uma descrição por banda em vez de repetir a
    primeira em todas — sem isso `indices.py` não consegue recuperar qual
    banda é `nir`, `swir16` etc. a partir só do arquivo.
    """
    path.parent.mkdir(parents=True, exist_ok=True)
    bandas = list(composto.data_vars)
    arr = xr.concat([composto[b] for b in bandas], dim="band").astype("float32")
    arr = arr.assign_coords(band=("band", list(range(1, len(bandas) + 1))))
    arr.attrs["long_name"] = tuple(bandas)
    arr = arr.rio.write_crs(crs)
    arr = arr.rio.write_nodata(np.nan)
    arr.rio.to_raster(path, driver="COG", compress="deflate", predictor=3, dtype="float32")


def escrever_nobs_cog(nobs: xr.DataArray, path: Path, crs: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    arr = nobs.astype("uint16").rio.write_crs(crs).rio.write_nodata(0)
    arr.rio.to_raster(path, driver="COG", compress="deflate", predictor=2, dtype="uint16")


def processar_ano(
    ano: int,
    estudo: dict,
    client,
    geobox: GeoBox,
) -> dict:
    """Gera o composto de um ano-âncora. Levanta `CoberturaInsuficiente` se não
    houver cobertura Landsat mínima. Retorna o registro de proveniência do ano.
    """
    bbox_aoi = estudo["aoi"]["bbox"]
    bbox = [bbox_aoi["xmin"], bbox_aoi["ymin"], bbox_aoi["xmax"], bbox_aoi["ymax"]]
    crs_metrico = estudo["crs"]["metrico"]
    composto_cfg = estudo["composto"]
    mes_inicio = composto_cfg["estacao_seca"]["mes_inicio"]
    mes_fim = composto_cfg["estacao_seca"]["mes_fim"]
    nuvem_max = composto_cfg["nuvem_max_pct"]
    janela_anos = composto_cfg["janela_anos"]

    sensor_cfg = estudo["sensores"][ano]
    missao = sensor_cfg["missao"]
    plataforma = PLATAFORMA_STAC_POR_MISSAO[missao]
    res_m = sensor_cfg["res_m"]

    datetime_range, ano_ini, ano_fim = janela_datas(ano, mes_inicio, mes_fim, janela_anos)

    bandas_landsat, itens_landsat = carregar_colecao_mascarada(
        client, "landsat-c2-l2", bbox, datetime_range, nuvem_max, geobox, plataforma
    )
    if bandas_landsat is None:
        raise CoberturaInsuficiente(
            f"{ano}: nenhuma cena {missao} ({plataforma}) na janela {datetime_range} "
            f"com nuvem <= {nuvem_max}%. Nenhum ano vizinho foi usado como substituto."
        )

    itens_s2: list = []
    bandas_s2 = None
    complemento = sensor_cfg.get("complemento", "")
    if "S2" in complemento:
        bandas_s2, itens_s2 = carregar_colecao_mascarada(
            client, "sentinel-2-l2a", bbox, datetime_range, nuvem_max, geobox
        )
        # Ausência de S2 é esperada e documentada em 2015 (lançamento recente do
        # S2A/S2B): não é falha, só significa que o composto usa só Landsat.

    combinadas = combinar_fontes(bandas_landsat, bandas_s2)
    nobs = contar_observacoes_validas(combinadas)
    composto = compor_mediana(combinadas)

    nobs_computado = nobs.compute()
    pixels_sem_obs = int((nobs_computado == 0).sum())
    total_pixels = int(nobs_computado.size)
    if pixels_sem_obs == total_pixels:
        raise CoberturaInsuficiente(
            f"{ano}: composto resultou em 100% dos pixels sem nenhuma observação "
            "válida (todas as cenas mascaradas por nuvem/sombra/fill na AOI)."
        )

    composto_computado = composto.compute()

    nome_base = f"composto_{ano}_{res_m}m_{crs_metrico.split(':')[-1]}"
    caminho_composto = DATA_PROCESSED / f"{nome_base}.tif"
    caminho_nobs = DATA_INTERIM / f"{nome_base}_nobs.tif"

    escrever_composto_cog(composto_computado, caminho_composto, crs_metrico)
    escrever_nobs_cog(nobs_computado, caminho_nobs, crs_metrico)

    registro = {
        "ano": ano,
        "arquivo": str(caminho_composto.relative_to(REPO_ROOT)),
        "bandas": BANDAS_COMUNS,
        "resolucao_m": res_m,
        "crs": crs_metrico,
        "janela_temporal": {
            "inicio_fim_iso": datetime_range,
            "ano_ancora": ano,
            "ano_inicio_janela": ano_ini,
            "ano_fim_janela": ano_fim,
            "janela_anos": janela_anos,
        },
        "nuvem_max_pct_cena": nuvem_max,
        "reducao": composto_cfg["reducao"],
        "pixels_sem_observacao": pixels_sem_obs,
        "pixels_total": total_pixels,
        "min_observacoes_por_pixel": int(nobs_computado.min()),
        "mediana_observacoes_por_pixel": float(nobs_computado.median()),
        "catalogo_stac": STAC_ENDPOINT_CANONICO,
        "colecao_landsat": {
            "id_colecao": "landsat-c2-l2",
            "plataforma": plataforma,
            "n_itens": len(itens_landsat),
            "itens": [
                {"id": it.id, "datetime": it.datetime.isoformat() if it.datetime else None}
                for it in itens_landsat
            ],
        },
        "colecao_sentinel2": {
            "id_colecao": "sentinel-2-l2a",
            "n_itens": len(itens_s2),
            "itens": [
                {"id": it.id, "datetime": it.datetime.isoformat() if it.datetime else None}
                for it in itens_s2
            ],
        }
        if itens_s2
        else None,
        "selo": "observado",
        "data_processamento": datetime.now(UTC).isoformat(),
        "commit_git": commit_git_atual(),
        "hash_config_study_yaml": hash_arquivo(STUDY_YAML),
        "script": "pipeline/01_imagery/compostos.py",
    }

    meta_path = caminho_composto.with_suffix(".tif.meta.json")
    meta_path.write_text(json.dumps(registro, indent=2, ensure_ascii=False), encoding="utf-8")

    print(
        f"[ok] {ano}: {caminho_composto.relative_to(REPO_ROOT)} "
        f"({len(itens_landsat)} Landsat + {len(itens_s2)} Sentinel-2; "
        f"min {registro['min_observacoes_por_pixel']} obs/pixel)",
        file=sys.stderr,
    )
    return registro


def escrever_fragmento_provenencia(registros: list[dict]) -> None:
    """Reescreve `data/provenance_parts/imagem_fase1.md` por inteiro, de forma
    idempotente, a partir dos registros desta execução (mesmo padrão de
    `probe_stac.py`: reescrita completa, não anexação).
    """
    linhas = [
        "# Proveniência — Compostos de Imagem e Índices (Fase 1)",
        "",
        "Fragmento gerado por `pipeline/01_imagery/compostos.py`. **Não editar à mão**",
        "— reexecute o script para regenerar. Consolidado em `PROVENANCE.md` por",
        "`scripts/consolidar_registros.py`. Este fragmento é novo e não substitui",
        "`data/provenance_parts/imagem.md` (Fase 0', fechado).",
        "",
        f"Catálogo STAC canônico: `{STAC_ENDPOINT_CANONICO}` "
        "(ver `docs/ADR/0004-divergencia-catalogos-stac.md`).",
        "",
        "Nenhum processo estocástico: `config/seeds.yaml` não se aplica a este",
        "estágio (mediana não amostra nem sorteia). Determinismo garantido pela",
        "ordenação por `id` dos itens STAC antes da composição.",
        "",
        "## Defeito corrigido nesta entrega (Fase 1) e descarte dos produtos anteriores",
        "",
        "Os cinco compostos gravados por uma execução anterior desta mesma tarefa",
        "(2000, 2005, 2015, 2020, 2025) foram **descartados e regravados do zero**,",
        "não ajustados. `odc.stac.load` honrava o `nodata: 1` declarado no",
        "`raster:bands` do asset `qa_pixel` (Landsat C2 L2) — e 1 é exatamente o",
        "valor do bit de FILL, não um nodata de fato. Isso trocava todo pixel de",
        "falha real (fill/gap) por `0` na banda carregada, e `0` não tem nenhum bit",
        "de qualidade ruim aceso: a máscara de nuvem/sombra/preenchimento",
        "classificava esses pixels de falha como válidos. O sintoma mais visível",
        "era o composto de 2010 (Landsat 7 SLC-off, medição experimental de",
        "`docs/ADR/0005-...md`): declarava 95,68% dos pixels com as 4 observações",
        "completas e 0% sem nenhuma, quando a contagem correta é 73,36% com as 4",
        "e 0,005% sem nenhuma — bom demais para ser real em cenas SLC-off.",
        "",
        "Corrigido via `_stac_common.STAC_CFG_QA_PIXEL_SEM_NODATA` (passado a",
        "`odc.stac.load(..., stac_cfg=...)`, desliga o nodata declarado só para",
        "`qa_pixel`) e uma defesa em profundidade em `mascara_valida_landsat`",
        "(`qa == 0` também é tratado como inválido — 0 nunca é um valor legítimo de",
        "`QA_PIXEL`). Ver `pipeline/tests/test_imagery.py::"
        "test_nobs_bate_com_calculo_direto_do_qa_pixel` para o contrato de",
        "regressão (usa as cenas Landsat 7/2010, o único conjunto do repositório",
        "com pixels de fill reais dentro da AOI) e `config/tolerances.yaml ->",
        "regressao_numerica.contrato_qa_pixel` para a tolerância declarada.",
        "",
        "Os cinco compostos e todos os índices abaixo foram gerados **depois**",
        "dessa correção — nenhum artefato do defeito permanece em",
        "`data/processed/imagery/`.",
        "",
    ]
    for r in registros:
        linhas += [
            f"## Ano-âncora {r['ano']}",
            "",
            f"- **Arquivo**: `{r['arquivo']}`",
            f"- **Janela temporal**: `{r['janela_temporal']['inicio_fim_iso']}` "
            f"(janela_anos={r['janela_temporal']['janela_anos']})",
            f"- **Landsat**: {r['colecao_landsat']['plataforma']}, "
            f"{r['colecao_landsat']['n_itens']} cenas",
            (
                f"- **Sentinel-2**: {r['colecao_sentinel2']['n_itens']} cenas"
                if r["colecao_sentinel2"]
                else "- **Sentinel-2**: não incluído (fora do complemento do ano ou sem cobertura)"
            ),
            f"- **Observações válidas por pixel**: mínimo {r['min_observacoes_por_pixel']}, "
            f"mediana {r['mediana_observacoes_por_pixel']:.1f}",
            f"- **Pixels sem nenhuma observação válida**: {r['pixels_sem_observacao']} "
            f"de {r['pixels_total']} "
            f"({100 * r['pixels_sem_observacao'] / r['pixels_total']:.2f}%)",
            f"- **Commit**: `{r['commit_git']}`",
            f"- **Hash de `config/study.yaml`**: `{r['hash_config_study_yaml']}`",
            f"- **Data de processamento**: {r['data_processamento']}",
            f"- **Selo**: {r['selo']}",
            "",
            "IDs das cenas Landsat: "
            + ", ".join(i["id"] for i in r["colecao_landsat"]["itens"]),
            "",
        ]
        if r["colecao_sentinel2"]:
            linhas += [
                "IDs das cenas Sentinel-2: "
                + ", ".join(i["id"] for i in r["colecao_sentinel2"]["itens"]),
                "",
            ]
    PROVENANCE_FRAGMENT.parent.mkdir(parents=True, exist_ok=True)
    PROVENANCE_FRAGMENT.write_text("\n".join(linhas), encoding="utf-8")


def main(argv: list[str]) -> int:
    estudo = carregar_estudo(STUDY_YAML)
    anos = [int(a) for a in argv] if argv else list(estudo["anos_ancora"]["imagem"])

    bbox_aoi = estudo["aoi"]["bbox"]
    crs_metrico = estudo["crs"]["metrico"]
    # Resolução da grade canônica: a mais fina declarada em `sensores.*.res_m`
    # (hoje 30 m para todos os anos — grade única, coerente entre anos).
    resolucoes = {estudo["sensores"][a]["res_m"] for a in anos}
    if len(resolucoes) != 1:
        raise CoberturaInsuficiente(
            f"anos processados juntos com resoluções diferentes: {resolucoes}. "
            "Rode compostos.py separadamente por resolução para não quebrar a "
            "grade coerente entre anos."
        )
    resolucao_m = next(iter(resolucoes))
    geobox = construir_geobox(bbox_aoi, crs_metrico, resolucao_m)

    client = abrir_cliente_stac(STAC_ENDPOINT_CANONICO)

    registros = []
    falhas = []
    for ano in anos:
        try:
            registros.append(processar_ano(ano, estudo, client, geobox))
        except CoberturaInsuficiente as exc:
            print(f"[FALHA] {ano}: {exc}", file=sys.stderr)
            falhas.append((ano, str(exc)))

    if registros:
        escrever_fragmento_provenencia(registros)

    if falhas:
        print(
            f"\n{len(falhas)} ano(s) falharam e NÃO têm composto: "
            + ", ".join(str(a) for a, _ in falhas),
            file=sys.stderr,
        )
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
