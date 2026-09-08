#!/usr/bin/env python3
"""
fetch_lulc_products.py — Download idempotente de Copernicus CGLS-LC100 e ESRI/IO Land Cover.

Fontes (nível A, corrigidas em T3):

1. Copernicus CGLS-LC100 (Collection 3, epoch 2015-2019), 100 m, anual.
   Um registro Zenodo por época (não um arquivo global único por "coleção"):
     2015 -> https://zenodo.org/records/3939038
     2016 -> https://zenodo.org/records/3518026
     2017 -> https://zenodo.org/records/3518036
     2018 -> https://zenodo.org/records/3518038
     2019 -> https://zenodo.org/records/3939050
   Camada usada: "Discrete-Classification-map" (classificação discreta, inclui
   fração de cultivo). Arquivos são GLOBAIS (1-8 GB), sem recorte por tile —
   confirmado por HEAD 200 em 2026-09-07 no registro de 2017 (~1,70 GB).
   Licença: Copernicus (uso livre, redistribuição permitida, citação obrigatória).
   Citação: Buchhorn, M. et al. (2020). Zenodo. DOI da época específica usada
   (ex.: 10.5281/zenodo.3518036 para 2017).

2. ESRI/Impact Observatory 10 m Annual LULC, 2017-2024 (NÃO 2017-2025: 2025 ainda
   não publicado no bucket em 2026-09-07 — corrigido).
   Bucket real (confirmado por HTTP 200): s3://io-10m-annual-lulc/
   (o bucket "io-lulc-annual-v02" citado em versões anteriores deste script NÃO
   EXISTE — 404 confirmado).
   Tile nomeado por célula MGRS + ano, ex.: "36KWC_2017.tif"; a AOI Tete-Moatize
   cai na célula MGRS 36KWC/36KWB (a confirmar por interseção exata em 01_imagery).
   Licença: CC-BY 4.0.
   Citação: Karra, K. et al. / Impact Observatory (2023, atualizado anualmente).
   AWS Open Data Registry: https://registry.opendata.aws/io-lulc/

Este script busca a camada global do CGLS-LC100 (grande; requer recorte posterior
por AOI em 02_metrics) e os tiles anuais do ESRI/IO cuja célula MGRS cobre a AOI.

Comportamento idempotente e falho-explícito: ver docstring de fetch_glad_cropland.py.
Nenhum sucesso é registrado sem download efetivo com HTTP 200 confirmado.
"""

import hashlib
import json
import sys
import urllib.error
import urllib.request
from datetime import UTC, datetime
from pathlib import Path

from _config import carregar_aoi

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
DATA_RAW = PROJECT_ROOT / "data" / "raw"

CGLS_ZENODO_RECORDS = {
    2015: "3939038",
    2016: "3518026",
    2017: "3518036",
    2018: "3518038",
    2019: "3939050",
}
CGLS_LICENSE = "Copernicus (uso livre, redistribuição permitida, citação obrigatória)"
CGLS_SOURCE_PAGE = (
    "https://land.copernicus.eu/en/products/global-dynamic-land-cover/"
    "copernicus-global-land-service-land-cover-100m-collection-3-epoch-2015-globe"
)


def cgls_citation(ano: int, record_id: str) -> str:
    return (
        f"Buchhorn, M. et al. (2020). \"Copernicus Global Land Service: Land Cover "
        f"100m: Collection 3: epoch {ano}: Globe.\" Zenodo. DOI 10.5281/zenodo.{record_id}"
    )


ESRI_IO_ANOS = [2017, 2018, 2019, 2020, 2021, 2022, 2023, 2024]
ESRI_IO_BUCKET = "https://s3.us-west-2.amazonaws.com/io-10m-annual-lulc"
ESRI_IO_LICENSE = "CC-BY 4.0"
ESRI_IO_SOURCE_PAGE = "https://registry.opendata.aws/io-lulc/"
ESRI_IO_CITATION = (
    "Karra, K. et al. / Impact Observatory (2023, atualizado anualmente). "
    "\"10m Annual Land Use Land Cover (9-class).\" AWS Open Data Registry."
)
# Célula MGRS que cobre a AOI Tete-Moatize; a confirmar por interseção exata do
# grid MGRS com a AOI em pipeline/01_imagery (aqui usamos a candidata verificada
# via tile de teste "01C" só para validar o padrão de nome do bucket — NÃO é a
# célula real da AOI. Marcar `mgrs_cell` como pendente até a confirmação.)
ESRI_IO_MGRS_CELL_PENDENTE = True


def compute_sha256(filepath: Path) -> str:
    sha256_hash = hashlib.sha256()
    with filepath.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            sha256_hash.update(chunk)
    return sha256_hash.hexdigest()


def write_sha256(filepath: Path, digest: str) -> None:
    sidecar = filepath.with_name(filepath.name + ".sha256")
    sidecar.write_text(f"{digest}  {filepath.name}\n", encoding="utf-8")


def write_meta(filepath: Path, url: str, source_page: str, license_text: str,
               citation: str, dataset: str, ano: int, aoi: dict,
               extra: dict | None = None) -> None:
    meta = {
        "url": url,
        "download_date": datetime.now(UTC).isoformat(),
        "size_bytes": filepath.stat().st_size,
        "license": license_text,
        "level": "A",
        "source_page": source_page,
        "dataset": dataset,
        "ano": ano,
        "aoi_bbox": aoi,
        "citation": citation,
    }
    if extra:
        meta.update(extra)
    meta_path = filepath.with_name(filepath.name + ".meta.json")
    meta_path.write_text(json.dumps(meta, indent=2, ensure_ascii=False), encoding="utf-8")


def download(url: str, dest: Path) -> None:
    req = urllib.request.Request(url, headers={"User-Agent": "tete-moatize-fetch/1.0"})
    tmp = dest.with_suffix(dest.suffix + ".part")
    try:
        with urllib.request.urlopen(req, timeout=300) as resp:
            if resp.status != 200:
                raise RuntimeError(f"HTTP {resp.status} para {url}")
            with tmp.open("wb") as out:
                while True:
                    chunk = resp.read(1 << 20)
                    if not chunk:
                        break
                    out.write(chunk)
        tmp.replace(dest)
    finally:
        if tmp.exists():
            tmp.unlink()


def cgls_download_url(record_id: str) -> str:
    """Resolve a URL de download real do arquivo 'Discrete-Classification-map'
    dentro de um registro Zenodo, consultando a API de registros do Zenodo."""
    api_url = f"https://zenodo.org/api/records/{record_id}"
    req = urllib.request.Request(api_url, headers={"User-Agent": "tete-moatize-fetch/1.0"})
    with urllib.request.urlopen(req, timeout=60) as resp:
        if resp.status != 200:
            raise RuntimeError(f"HTTP {resp.status} ao consultar {api_url}")
        record = json.loads(resp.read().decode("utf-8"))
    for f in record.get("files", []):
        nome = f.get("key", "")
        if "Discrete-Classification-map" in nome:
            return f["links"]["self"]
    raise RuntimeError(f"Nenhum arquivo 'Discrete-Classification-map' no registro {record_id}")


def fetch_cgls(aoi: dict) -> bool:
    ok = True
    for ano, record_id in CGLS_ZENODO_RECORDS.items():
        filename = f"cgls_lc100_{ano}.tif"
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
        except (urllib.error.URLError, RuntimeError, TimeoutError, OSError) as exc:
            print(
                f"ERRO [CGLS {ano}]: não foi possível resolver URL de download: {exc}",
                file=sys.stderr,
            )
            ok = False
            continue

        print(f"Baixando [CGLS {ano}]: {url}")
        try:
            download(url, filepath)
        except (urllib.error.URLError, RuntimeError, TimeoutError, OSError) as exc:
            print(f"ERRO [CGLS {ano}]: falha ao baixar {url}: {exc}", file=sys.stderr)
            if filepath.exists():
                filepath.unlink()
            ok = False
            continue

        digest = compute_sha256(filepath)
        write_sha256(filepath, digest)
        write_meta(
            filepath, url, CGLS_SOURCE_PAGE, CGLS_LICENSE,
            cgls_citation(ano, record_id), "CGLS-LC100", ano, aoi,
            extra={"zenodo_record": record_id, "resolution_m": 100},
        )
        print(
            f"OK [CGLS {ano}]: {filename} baixado, {filepath.stat().st_size} bytes, sha256={digest}"
        )
    return ok


def fetch_esri_io() -> bool:
    if ESRI_IO_MGRS_CELL_PENDENTE:
        print(
            "AVISO: célula MGRS da AOI Tete-Moatize ainda não confirmada por "
            "interseção geométrica com o grid MGRS (pertence a pipeline/01_imagery). "
            "Nenhum tile ESRI/IO será baixado até essa confirmação — falhando "
            "explicitamente em vez de baixar um tile potencialmente errado.",
            file=sys.stderr,
        )
        return False

    ok = True
    for ano in ESRI_IO_ANOS:
        # placeholder de padrão de nome; substituir <CELULA_MGRS> após confirmação
        url = f"{ESRI_IO_BUCKET}/<CELULA_MGRS>_{ano}.tif"
        print(
            f"ERRO [ESRI/IO {ano}]: URL não resolvida (célula MGRS pendente): {url}",
            file=sys.stderr,
        )
        ok = False
    return ok


def main() -> int:
    DATA_RAW.mkdir(parents=True, exist_ok=True)
    aoi = carregar_aoi()
    ok_cgls = fetch_cgls(aoi)
    ok_esri = fetch_esri_io()
    if not (ok_cgls and ok_esri):
        print("FALHA: um ou mais produtos LULC não foram obtidos.", file=sys.stderr)
        return 1
    print("CGLS-LC100 e ESRI/IO obtidos e validados.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
