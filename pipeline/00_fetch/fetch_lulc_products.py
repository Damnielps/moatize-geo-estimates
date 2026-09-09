#!/usr/bin/env python3
"""
fetch_lulc_products.py — Download idempotente de Copernicus CGLS-LC100 e ESRI/IO Land Cover,
recortados na AOI.

Fontes (nível A):

1. Copernicus Global Land Service Land Cover 100m (CGLS-LC100), Collection 3,
   épocas 2015-2019, 100 m, anual. Um registro Zenodo por época:
     2015 -> https://zenodo.org/records/3939038
     2016 -> https://zenodo.org/records/3518026
     2017 -> https://zenodo.org/records/3518036
     2018 -> https://zenodo.org/records/3518038
     2019 -> https://zenodo.org/records/3939050
   Camada usada: "Discrete-Classification-map" (inclui classe cropland, valor 40).
   Página do produtor: https://land.copernicus.eu/en/products/global-dynamic-land-cover
   (sem texto de licença localizável nela — a licença é declarada no próprio
   registro Zenodo de cada época: CC-BY 4.0, confirmado em 2026-09-08).
   Arquivos GLOBAIS (~1,7 GB o "Discrete-Classification-map" de cada época,
   confirmado via API Zenodo). Este script NÃO baixa o global: lê a janela da
   AOI via GDAL /vsicurl/ e grava só o recorte.

2. ESRI/Impact Observatory 10 m Annual LULC, 2017-2024.
   Bucket real (confirmado por listagem S3 pública em 2026-09-08):
     https://io-10m-annual-lulc.s3.us-west-2.amazonaws.com/<CELULA>_<ANO>.tif
   <CELULA> é o Grid Zone Designator MGRS de 3 caracteres (zona UTM + banda de
   latitude, ex.: "36K"), NÃO o quadrado de 100 km de 5 caracteres — confirmado
   por listagem do bucket (chaves "36K_2020.tif", "01C_2017.tif" etc., não
   "36KWH_...").
   A CÉLULA da AOI foi DERIVADA (não presumida) amostrando uma grade de pontos
   sobre a AOI de config/study.yaml com a biblioteca `mgrs` (conversão lat/lon ->
   MGRS): a AOI cruza a fronteira das bandas K/L em -16.00°, cobrindo as células
   36K e 36L (ambas confirmadas com dados sobre a AOI via leitura de janela).
   Licença: CC-BY 4.0 — AWS Open Data Registry https://registry.opendata.aws/io-lulc/
   (texto de licença "CC BY 4.0" declarado na página do registro).
   Citação: Karra, K., Kontgis, C., Statman-Weil, Z., Mazzariello, J.C., Mathis, M.,
   Brumby, S.P. (2021). "Global land use/land cover with Sentinel-2 and deep
   learning." IGARSS 2021. / Impact Observatory, Microsoft, Esri (2023, atualizado
   anualmente). "Sentinel-2 10m Land Use/Land Cover Time Series."

Comportamento idempotente e falho-explícito (§11.2.2): ver docstring de
fetch_glad_cropland.py. Nenhum sucesso é registrado sem leitura/gravação efetiva
com HTTP 200 confirmado (rasterio levanta em qualquer falha HTTP via /vsicurl/).
"""

import hashlib
import json
import sys
from datetime import UTC, datetime
from pathlib import Path

import rasterio
from _config import carregar_aoi
from pyproj import Transformer
from rasterio.windows import from_bounds

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
DATA_RAW = PROJECT_ROOT / "data" / "raw"

MARGEM_GRAUS = 0.02
MARGEM_METROS = 2000

# --- CGLS-LC100 --------------------------------------------------------------

CGLS_ZENODO_RECORDS = {
    2015: "3939038",
    2016: "3518026",
    2017: "3518036",
    2018: "3518038",
    2019: "3939050",
}
CGLS_LICENSE = "CC-BY 4.0"
# Licença declarada no registro Zenodo (repetida em cada época).
CGLS_LICENSE_URL = "https://zenodo.org/records/3518036"
CGLS_SOURCE_PAGE = "https://land.copernicus.eu/en/products/global-dynamic-land-cover"
CGLS_LAYER_KEY = "Discrete-Classification-map"


def cgls_citation(ano: int, record_id: str) -> str:
    return (
        f'Buchhorn, M. et al. (2020). "Copernicus Global Land Service: Land Cover '
        f'100m: Collection 3: epoch {ano}: Globe." Zenodo. DOI 10.5281/zenodo.{record_id}'
    )


# --- ESRI / Impact Observatory ------------------------------------------------

ESRI_IO_ANOS = [2017, 2018, 2019, 2020, 2021, 2022, 2023, 2024]
ESRI_IO_BUCKET = "https://io-10m-annual-lulc.s3.us-west-2.amazonaws.com"
ESRI_IO_LICENSE = "CC-BY 4.0"
ESRI_IO_LICENSE_URL = "https://registry.opendata.aws/io-lulc/"
ESRI_IO_SOURCE_PAGE = "https://registry.opendata.aws/io-lulc/"
ESRI_IO_CITATION = (
    "Karra, K., Kontgis, C., Statman-Weil, Z., Mazzariello, J.C., Mathis, M., "
    'Brumby, S.P. (2021). "Global land use/land cover with Sentinel-2 and deep '
    'learning." IGARSS 2021. Impact Observatory, Microsoft, Esri (2023, atualizado '
    'anualmente). "Sentinel-2 10m Land Use/Land Cover Time Series."'
)
# Grid Zone Designators MGRS (3 caracteres) que cobrem a AOI — derivados por
# amostragem de grade sobre config/study.yaml com a biblioteca `mgrs`, não
# presumidos (ver docstring do módulo). A AOI cruza a fronteira K/L em -16.00°.
ESRI_IO_CELULAS = ["36K", "36L"]


def compute_sha256(filepath: Path) -> str:
    sha256_hash = hashlib.sha256()
    with filepath.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            sha256_hash.update(chunk)
    return sha256_hash.hexdigest()


def write_sha256(filepath: Path, digest: str) -> None:
    sidecar = filepath.with_name(filepath.name + ".sha256")
    sidecar.write_text(f"{digest}  {filepath.name}\n", encoding="utf-8")


def write_meta(
    filepath: Path,
    url: str,
    source_page: str,
    license_text: str,
    license_url: str,
    citation: str,
    dataset: str,
    ano: int,
    aoi: dict,
    extra: dict | None = None,
) -> None:
    meta = {
        "url": url,
        "download_date": datetime.now(UTC).isoformat(),
        "size_bytes": filepath.stat().st_size,
        "license": license_text,
        "license_url": license_url,
        "level": "A",
        "selo": "observado",
        "source_page": source_page,
        "dataset": dataset,
        "ano": ano,
        "anos_cobertos": str(ano),
        "aoi_bbox": aoi,
        "citation": citation,
    }
    if extra:
        meta.update(extra)
    meta_path = filepath.with_name(filepath.name + ".meta.json")
    meta_path.write_text(json.dumps(meta, indent=2, ensure_ascii=False), encoding="utf-8")


def cgls_download_url(record_id: str) -> str:
    """Resolve a URL de download real da camada Discrete-Classification-map dentro
    de um registro Zenodo, consultando a API de registros do Zenodo."""
    import urllib.request

    api_url = f"https://zenodo.org/api/records/{record_id}"
    req = urllib.request.Request(api_url, headers={"User-Agent": "tete-moatize-fetch/1.0"})
    with urllib.request.urlopen(req, timeout=60) as resp:
        if resp.status != 200:
            raise RuntimeError(f"HTTP {resp.status} ao consultar {api_url}")
        record = json.loads(resp.read().decode("utf-8"))
    for f in record.get("files", []):
        nome = f.get("key", "")
        if CGLS_LAYER_KEY in nome:
            return f["links"]["self"]
    raise RuntimeError(f"Nenhum arquivo '{CGLS_LAYER_KEY}' no registro {record_id}")


def crop_and_write(
    vsi_url: str, dest: Path, xmin: float, ymin: float, xmax: float, ymax: float
) -> None:
    """Lê a janela [xmin,ymin,xmax,ymax] (no CRS nativo da fonte) via /vsicurl/ e
    grava um GeoTIFF recortado em `dest`. Levanta exceção em qualquer falha."""
    with rasterio.open(vsi_url) as src:
        win = from_bounds(xmin, ymin, xmax, ymax, src.transform)
        data = src.read(1, window=win)
        if data.size == 0:
            raise RuntimeError(f"janela vazia para {vsi_url} (AOI fora da cobertura do tile)")
        out_transform = src.window_transform(win)
        profile = src.profile.copy()
        profile.update(
            height=data.shape[0],
            width=data.shape[1],
            transform=out_transform,
            compress="deflate",
        )
        tmp = dest.with_suffix(dest.suffix + ".part")
        with rasterio.open(tmp, "w", **profile) as dst:
            dst.write(data, 1)
        tmp.replace(dest)


def fetch_cgls(aoi: dict) -> bool:
    ok = True
    xmin, ymin = aoi["xmin"] - MARGEM_GRAUS, aoi["ymin"] - MARGEM_GRAUS
    xmax, ymax = aoi["xmax"] + MARGEM_GRAUS, aoi["ymax"] + MARGEM_GRAUS

    for ano, record_id in CGLS_ZENODO_RECORDS.items():
        filename = f"cgls_lc100_{ano}_aoi.tif"
        filepath = DATA_RAW / filename
        sidecar = filepath.with_name(filepath.name + ".sha256")

        if filepath.exists() and sidecar.exists():
            registrado = sidecar.read_text(encoding="utf-8").split()
            digest = compute_sha256(filepath)
            if len(registrado) < 2 or registrado[0] != digest:
                print(f"ERRO [CGLS {ano}]: hash de {filename} não confere", file=sys.stderr)
                ok = False
                continue
            print(f"OK [CGLS {ano}]: {filename} já presente e íntegro.")
            continue

        try:
            url = cgls_download_url(record_id)
        except Exception as exc:
            print(
                f"ERRO [CGLS {ano}]: não foi possível resolver URL de download: {exc}",
                file=sys.stderr,
            )
            ok = False
            continue

        vsi_url = f"/vsicurl/{url}"
        print(f"Lendo janela AOI [CGLS {ano}]: {url}")
        try:
            crop_and_write(vsi_url, filepath, xmin, ymin, xmax, ymax)
        except Exception as exc:
            print(f"ERRO [CGLS {ano}]: falha ao ler/recortar {url}: {exc}", file=sys.stderr)
            tmp = filepath.with_suffix(filepath.suffix + ".part")
            if tmp.exists():
                tmp.unlink()
            if filepath.exists():
                filepath.unlink()
            ok = False
            continue

        digest = compute_sha256(filepath)
        write_sha256(filepath, digest)
        write_meta(
            filepath,
            url,
            CGLS_SOURCE_PAGE,
            CGLS_LICENSE,
            CGLS_LICENSE_URL,
            cgls_citation(ano, record_id),
            "CGLS-LC100",
            ano,
            aoi,
            extra={
                "zenodo_record": record_id,
                "resolution_m": 100,
                "nota": (
                    f"Recortado da AOI (+{MARGEM_GRAUS} grau de margem) via leitura em "
                    "janela GDAL /vsicurl/ no momento do fetch; o arquivo global "
                    "'Discrete-Classification-map' (~1,7 GB) NÃO foi mirrorado inteiro."
                ),
            },
        )
        print(
            f"OK [CGLS {ano}]: {filename} gravado (recorte AOI), "
            f"{filepath.stat().st_size} bytes, sha256={digest}"
        )
    return ok


def fetch_esri_io(aoi: dict) -> bool:
    transformer = Transformer.from_crs("EPSG:4326", "EPSG:32736", always_xy=True)
    xs, ys = transformer.transform(
        [aoi["xmin"], aoi["xmax"], aoi["xmin"], aoi["xmax"]],
        [aoi["ymin"], aoi["ymin"], aoi["ymax"], aoi["ymax"]],
    )
    xmin_m, xmax_m = min(xs) - MARGEM_METROS, max(xs) + MARGEM_METROS
    ymin_m, ymax_m = min(ys) - MARGEM_METROS, max(ys) + MARGEM_METROS

    ok = True
    for ano in ESRI_IO_ANOS:
        for celula in ESRI_IO_CELULAS:
            filename = f"esri_io_lulc_{ano}_{celula.lower()}_aoi.tif"
            filepath = DATA_RAW / filename
            sidecar = filepath.with_name(filepath.name + ".sha256")
            url = f"{ESRI_IO_BUCKET}/{celula}_{ano}.tif"

            if filepath.exists() and sidecar.exists():
                registrado = sidecar.read_text(encoding="utf-8").split()
                digest = compute_sha256(filepath)
                if len(registrado) < 2 or registrado[0] != digest:
                    print(
                        f"ERRO [ESRI/IO {ano} {celula}]: hash de {filename} não confere",
                        file=sys.stderr,
                    )
                    ok = False
                    continue
                print(f"OK [ESRI/IO {ano} {celula}]: {filename} já presente e íntegro.")
                continue

            vsi_url = f"/vsicurl/{url}"
            print(f"Lendo janela AOI [ESRI/IO {ano} {celula}]: {url}")
            try:
                crop_and_write(vsi_url, filepath, xmin_m, ymin_m, xmax_m, ymax_m)
            except Exception as exc:
                print(
                    f"ERRO [ESRI/IO {ano} {celula}]: falha ao ler/recortar {url}: {exc}",
                    file=sys.stderr,
                )
                tmp = filepath.with_suffix(filepath.suffix + ".part")
                if tmp.exists():
                    tmp.unlink()
                if filepath.exists():
                    filepath.unlink()
                ok = False
                continue

            digest = compute_sha256(filepath)
            write_sha256(filepath, digest)
            write_meta(
                filepath,
                url,
                ESRI_IO_SOURCE_PAGE,
                ESRI_IO_LICENSE,
                ESRI_IO_LICENSE_URL,
                ESRI_IO_CITATION,
                "ESRI/Impact Observatory 10m Annual LULC",
                ano,
                aoi,
                extra={
                    "celula_mgrs_gzd": celula,
                    "resolution_m": 10,
                    "crs_nativo": "EPSG:32736",
                    "nota": (
                        f"Recortado da AOI (+{MARGEM_METROS} m de margem, em EPSG:32736) "
                        "via leitura em janela GDAL /vsicurl/ no momento do fetch; o "
                        f"tile inteiro da célula GZD {celula} (~200-250 MB) NÃO foi "
                        "mirrorado."
                    ),
                },
            )
            print(
                f"OK [ESRI/IO {ano} {celula}]: {filename} gravado (recorte AOI), "
                f"{filepath.stat().st_size} bytes, sha256={digest}"
            )
    return ok


def main() -> int:
    DATA_RAW.mkdir(parents=True, exist_ok=True)
    aoi = carregar_aoi()
    ok_cgls = fetch_cgls(aoi)
    ok_esri = fetch_esri_io(aoi)
    if not (ok_cgls and ok_esri):
        print("FALHA: um ou mais produtos LULC não foram obtidos.", file=sys.stderr)
        return 1
    print("CGLS-LC100 e ESRI/IO obtidos e validados.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
