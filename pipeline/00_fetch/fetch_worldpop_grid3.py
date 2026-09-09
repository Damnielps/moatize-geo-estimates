#!/usr/bin/env python3
"""
Idempotent downloader for WorldPop / GRID3 population grids, recortados à AOI
do estudo Tete-Moatize (config/study.yaml), usados para estimar a população
da Vila de Moatize (não publicada por nenhuma fonte primária: o COD-PS só
cobre o distrito de Moatize).

Fontes:
  1. GRID3 MOZ Population v1.1 (WorldPop/GRID3, calibrado ao censo 2017 --
     é a ÚNICA versão v1.1 publicada; não existe v1.1 "2020"). Servida pelo
     backend wopr.worldpop.org (não suporta HTTP Range) e catalogada no HDX:
     https://data.humdata.org/dataset/gridded-population-estimates-for-mozambique-2017-census-v1-1
     Como o servidor não aceita Range, o arquivo nacional é baixado para um
     diretório temporário, recortado à AOI com rasterio, e o arquivo nacional
     é descartado (nunca espelhado inteiro em data/raw/, conforme instrução).
  2. WorldPop "Population Counts", grades anuais MOZ 2000/2005/2010 (produto
     unconstrained -- é o único disponível para esses anos; o "constrained"
     do WorldPop só existe a partir de 2015, calculado sobre building
     footprints) e 2015/2020 (produto constrained, release R2024B, preferido
     por ser calibrado com pegada de edificações, mais preciso em área
     urbana). Ambos servidos por data.worldpop.org, que suporta HTTP Range;
     o recorte à AOI é feito por leitura em janela via /vsicurl/ (rasterio),
     sem baixar o Moçambique inteiro.

Licenças observadas nas páginas do produtor: registradas em
data/licenses_parts/worldpop_grid3.md (WorldPop/GRID3 declara CC-BY 4.0 para
os produtos de população; ver ressalva sobre camadas derivadas de OSM/MS
Building Footprints, que não se aplica aos rasters de população usados aqui).

Este script NÃO classifica nível A/B/C (papel do auditor-dados).
"""

import hashlib
import json
import subprocess
import sys
import tempfile
from datetime import UTC, datetime
from pathlib import Path

import numpy as np
import rasterio
from rasterio.windows import from_bounds

REPO_ROOT = Path(__file__).resolve().parents[2]
OUTDIR = REPO_ROOT / "data" / "raw"
OUTDIR.mkdir(parents=True, exist_ok=True)

# AOI de config/study.yaml (§3), com a folga de 0.05 grau já embutida no bbox
# confirmado na Fase 0' (docs/ADR/0001-aoi-final.md): 33.50-34.10E, -16.35 a -16.00S.
AOI_BOUNDS = (33.50, -16.35, 34.10, -16.00)  # (xmin, ymin, xmax, ymax) EPSG:4326

# Margem de seguranca para a janela de recorte (nao para o AOI declarado): o
# alinhamento de grade dos rasters WorldPop/GRID3 nao cai exatamente nos limites
# do AOI, e round_offsets/round_lengths por si so nao bastaram (testado: a
# primeira tentativa de recorte do GRID3 ficou ~44 m curta no canto SW e falhou
# o teste de cobertura). Um raster maior que o AOI e sempre aceitavel.
WINDOW_BUFFER_DEG = 0.01

GRID3_SOURCE_PAGE = (
    "https://data.humdata.org/dataset/gridded-population-estimates-for-mozambique-2017-census-v1-1"
)
GRID3_DOWNLOAD_URL = "https://wopr.worldpop.org/download/237"  # MOZ_population_v1_1_gridded.tif
GRID3_LICENSE = (
    "CC BY 4.0 (Creative Commons Attribution) -- https://data.humdata.org package "
    "license_id=cc-by, license_url=http://www.opendefinition.org/licenses/cc-by "
    "(confirmado via HDX package_show API em 2026-09-09)"
)
GRID3_CITATION = (
    "Bondarenko M, Jones P, Leasure D, Lazar AN, Tatem AJ. 2020. Census disaggregated "
    "gridded population estimates for Mozambique (2017), version 1.1. WorldPop, "
    "University of Southampton. doi:10.5258/SOTON/WP00672"
)

WORLDPOP_UNCONSTRAINED_TEMPLATE = (
    "https://data.worldpop.org/GIS/Population/Global_2000_2020/{year}/MOZ/moz_ppp_{year}.tif"
)
WORLDPOP_CONSTRAINED_TEMPLATE = (
    "https://data.worldpop.org/GIS/Population/Global_2015_2030/R2024B/"
    "{year}/MOZ/v1/100m/constrained/"
    "moz_pop_{year}_CN_100m_R2024B_v1.tif"
)
WORLDPOP_UNCONSTRAINED_LICENSE = (
    "CC BY 4.0 -- declarada em https://www.worldpop.org/data/licence "
    "(WorldPop, University of Southampton)"
)
WORLDPOP_CONSTRAINED_LICENSE = WORLDPOP_UNCONSTRAINED_LICENSE
WORLDPOP_UNCONSTRAINED_CITATION = (
    "WorldPop (www.worldpop.org - School of Geography and Environmental Science, University of "
    "Southampton). {year}. Mozambique 100m Population (unconstrained, Global_2000_2020). "
    "doi:10.5258/SOTON/WP00645"
)
WORLDPOP_CONSTRAINED_CITATION = (
    "WorldPop (www.worldpop.org - School of Geography and Environmental Science, University of "
    "Southampton). 2024. Mozambique 100m Population (constrained, individual countries 2015-2030, "
    "UN adjusted, R2024B), {year}."
)

# Anos-âncora do estudo cobertos por cada produto (§2 do CLAUDE.md).
UNCONSTRAINED_YEARS = [2000, 2005, 2010]
CONSTRAINED_YEARS = [2015, 2020]


def compute_sha256(filepath: Path) -> str:
    sha256 = hashlib.sha256()
    with open(filepath, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            sha256.update(chunk)
    return sha256.hexdigest()


def write_sidecars(
    outfile: Path,
    url: str,
    license_text: str,
    citation: str,
    year,
    method_note: str,
    res_m: float,
    extra: dict | None = None,
):
    """Grava .sha256 e .meta.json SOMENTE se outfile existir de fato."""
    if not outfile.exists():
        raise FileNotFoundError(f"tentativa de gravar sidecar para arquivo inexistente: {outfile}")
    digest = compute_sha256(outfile)
    (outfile.parent / f"{outfile.name}.sha256").write_text(f"{digest}  {outfile.name}\n")
    with rasterio.open(outfile) as src:
        crs = str(src.crs)
        shape = [src.height, src.width]
    meta = {
        "url": url,
        "download_date": datetime.now(tz=UTC).isoformat(),
        "size_bytes": outfile.stat().st_size,
        "license": license_text,
        "citation": citation,
        "year": year,
        "resolution_m": res_m,
        "crs": crs,
        "shape_rows_cols": shape,
        "clip_method": method_note,
        "aoi_bounds_epsg4326": list(AOI_BOUNDS),
        "sha256": digest,
    }
    if extra:
        meta.update(extra)
    (outfile.parent / f"{outfile.name}.meta.json").write_text(json.dumps(meta, indent=2))
    return digest


def sum_population(outfile: Path) -> float:
    with rasterio.open(outfile) as src:
        arr = src.read(1, masked=True)
        nodata = src.nodata
    arr = np.where(np.ma.getmaskarray(arr), 0.0, np.ma.getdata(arr))
    if nodata is not None:
        arr = np.where(arr == nodata, 0.0, arr)
    arr = np.where(arr < 0, 0.0, arr)  # WorldPop usa negativos/NaN como nodata em alguns produtos
    return float(np.nansum(arr))


def fetch_grid3():
    """GRID3 v1.1 (2017): sem suporte a Range no servidor -> baixa completo
    para um arquivo temporário fora de data/raw/, recorta à AOI, descarta o
    arquivo nacional."""
    outfile = OUTDIR / "grid3_moz_pop_v1_1_2020_100m_aoi.tif"
    # nome do arquivo mantém o rótulo "2020" pedido na tarefa, mas o dado é
    # calibrado ao Censo 2017 -- ver nota de método no .meta.json.
    if outfile.exists() and (outfile.parent / f"{outfile.name}.sha256").exists():
        digest = compute_sha256(outfile)
        expected = (outfile.parent / f"{outfile.name}.sha256").read_text().split()[0]
        if digest == expected:
            print(f"OK ja verificado: {outfile.name}")
            return outfile, sum_population(outfile)

    with tempfile.TemporaryDirectory() as td:
        tmp_national = Path(td) / "MOZ_population_v1_1_gridded_NATIONAL_TEMP.tif"
        print(f"Baixando GRID3 nacional (sem suporte a Range) de {GRID3_DOWNLOAD_URL} ...")
        result = subprocess.run(
            [
                "curl",
                "-sL",
                "-w",
                "%{http_code}",
                "--max-time",
                "300",
                "--output",
                str(tmp_national),
                GRID3_DOWNLOAD_URL,
            ],
            capture_output=True,
            text=True,
            check=False,
        )
        http_code = result.stdout.strip()
        if http_code != "200" or not tmp_national.exists() or tmp_national.stat().st_size < 1000:
            print(f"FALHA no download do GRID3: HTTP {http_code}, URL {GRID3_DOWNLOAD_URL}")
            return None, None

        with rasterio.open(tmp_national) as src:
            buffered_bounds = (
                AOI_BOUNDS[0] - WINDOW_BUFFER_DEG,
                AOI_BOUNDS[1] - WINDOW_BUFFER_DEG,
                AOI_BOUNDS[2] + WINDOW_BUFFER_DEG,
                AOI_BOUNDS[3] + WINDOW_BUFFER_DEG,
            )
            window = from_bounds(*buffered_bounds, transform=src.transform)
            # expande para fora, garante cobertura total da AOI
            window = window.round_offsets(op="floor").round_lengths(op="ceil")
            transform = src.window_transform(window)
            data = src.read(1, window=window)
            profile = src.profile.copy()
            profile.update(
                {
                    "height": data.shape[0],
                    "width": data.shape[1],
                    "transform": transform,
                }
            )
            with rasterio.open(outfile, "w", **profile) as dst:
                dst.write(data, 1)

    write_sidecars(
        outfile,
        GRID3_DOWNLOAD_URL,
        GRID3_LICENSE,
        GRID3_CITATION,
        year=2017,
        method_note=(
            "Arquivo nacional baixado integralmente (servidor wopr.worldpop.org nao suporta "
            "HTTP Range), recortado a AOI via rasterio.windows.from_bounds, arquivo nacional "
            "descartado apos o recorte. Dado calibrado ao Censo 2017 (v1.1), apesar do rotulo "
            "'2020' no nome do arquivo pedido pela tarefa."
        ),
        res_m=100,
        extra={"calibration_census_year": 2017, "source_page": GRID3_SOURCE_PAGE},
    )
    total = sum_population(outfile)
    print(f"OK GRID3 recortado: {outfile.name} soma_pop_AOI={total:.0f}")
    return outfile, total


def fetch_worldpop_year(year: int, constrained: bool):
    template = WORLDPOP_CONSTRAINED_TEMPLATE if constrained else WORLDPOP_UNCONSTRAINED_TEMPLATE
    url = template.format(year=year)
    tag = "constrained" if constrained else "unconstrained"
    outfile = OUTDIR / f"worldpop_moz_pop_{year}_100m_aoi.tif"

    if outfile.exists() and (outfile.parent / f"{outfile.name}.sha256").exists():
        digest = compute_sha256(outfile)
        expected = (outfile.parent / f"{outfile.name}.sha256").read_text().split()[0]
        if digest == expected:
            print(f"OK ja verificado: {outfile.name}")
            return outfile, sum_population(outfile)

    # /vsicurl/ com leitura em janela falhou: o servidor anuncia Accept-Ranges
    # mas nao honra Range GET (GDAL recusa com "Range downloading not
    # supported by this server!"). Baixa o mosaico nacional inteiro para um
    # diretorio temporario fora de data/raw/, recorta a AOI, descarta o
    # nacional -- mesma estrategia usada para o GRID3.
    with tempfile.TemporaryDirectory() as td:
        tmp_national = Path(td) / f"moz_{tag}_{year}_NATIONAL_TEMP.tif"
        print(f"Baixando WorldPop {tag} {year} (Range nao confiavel) de {url} ...")
        result = subprocess.run(
            [
                "curl",
                "-sL",
                "-w",
                "%{http_code}",
                "--max-time",
                "600",
                "--output",
                str(tmp_national),
                url,
            ],
            capture_output=True,
            text=True,
            check=False,
        )
        http_code = result.stdout.strip()
        if http_code != "200" or not tmp_national.exists() or tmp_national.stat().st_size < 1000:
            print(f"FALHA no download de {tag} {year}: HTTP {http_code}, URL {url}")
            return None, None

        try:
            with rasterio.open(tmp_national) as src:
                buffered_bounds = (
                    AOI_BOUNDS[0] - WINDOW_BUFFER_DEG,
                    AOI_BOUNDS[1] - WINDOW_BUFFER_DEG,
                    AOI_BOUNDS[2] + WINDOW_BUFFER_DEG,
                    AOI_BOUNDS[3] + WINDOW_BUFFER_DEG,
                )
                window = from_bounds(*buffered_bounds, transform=src.transform)
                # expande para fora, garante cobertura total da AOI
                window = window.round_offsets(op="floor").round_lengths(op="ceil")
                transform = src.window_transform(window)
                data = src.read(1, window=window)
                profile = src.profile.copy()
                profile.update(
                    {
                        "height": data.shape[0],
                        "width": data.shape[1],
                        "transform": transform,
                    }
                )
                with rasterio.open(outfile, "w", **profile) as dst:
                    dst.write(data, 1)
        except Exception as e:
            print(f"FALHA ao recortar {tag} {year}: {e}. URL: {url}")
            return None, None

    license_text = WORLDPOP_CONSTRAINED_LICENSE if constrained else WORLDPOP_UNCONSTRAINED_LICENSE
    citation = (
        WORLDPOP_CONSTRAINED_CITATION if constrained else WORLDPOP_UNCONSTRAINED_CITATION
    ).format(year=year)
    write_sidecars(
        outfile,
        url,
        license_text,
        citation,
        year=year,
        method_note=(
            f"Mosaico nacional {tag} do WorldPop baixado integralmente para diretorio "
            f"temporario (Range GET nao honrado pelo servidor apesar de anunciar "
            f"Accept-Ranges), recortado a AOI via rasterio.windows.from_bounds, "
            f"arquivo nacional descartado apos o recorte."
        ),
        res_m=100,
        extra={
            "product": f"WorldPop Population Counts ({tag})",
            "constrained": constrained,
            "calibration_census_year": 2017 if constrained else None,
        },
    )
    total = sum_population(outfile)
    print(f"OK WorldPop {tag} {year}: {outfile.name} soma_pop_AOI={total:.0f}")
    return outfile, total


def main():
    results = {}
    grid3_file, grid3_sum = fetch_grid3()
    if grid3_file:
        results["grid3_2020_label_censo2017"] = grid3_sum

    for year in UNCONSTRAINED_YEARS:
        f, s = fetch_worldpop_year(year, constrained=False)
        if f:
            results[f"worldpop_unconstrained_{year}"] = s

    for year in CONSTRAINED_YEARS:
        f, s = fetch_worldpop_year(year, constrained=True)
        if f:
            results[f"worldpop_constrained_{year}"] = s

    print("\n=== Resumo somas de populacao na AOI ===")
    for k, v in results.items():
        print(f"{k}: {v:.0f}")

    return 0 if results else 1


if __name__ == "__main__":
    sys.exit(main())
