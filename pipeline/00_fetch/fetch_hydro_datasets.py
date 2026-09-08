#!/usr/bin/env python3
"""
fetch_hydro_datasets.py — Download idempotente de HydroRIVERS e Copernicus DEM GLO-30.

Fontes (ambas nível A, corrigidas em T3):

1. HydroRIVERS v1.0 (África), ~111 MiB — pequeno o suficiente para espelhamento em
   data/raw/. Licença própria HydroSHEDS (uso livre científico/educacional/comercial
   com atribuição obrigatória; NÃO é CC0 — corrigido, T1 registrava "CC0/Domínio
   Público" sem texto localizado).
   URL: https://data.hydrosheds.org/file/HydroRIVERS/HydroRIVERS_v10_af.gdb.zip
   Citação: Lehner, B., & Grill, G. (2013). Hydrological Processes, 27(15),
   2171-2186. DOI 10.1002/hyp.9740 (corrigido — 10.1002/hyp.9807 resolve para um
   artigo diferente, de Hughes et al.)

2. Copernicus DEM GLO-30, via AWS Open Data (sem chave, acesso anônimo confirmado
   por HTTP 200 em 2026-09-07):
   https://copernicus-dem-30m.s3.amazonaws.com/Copernicus_DSM_COG_10_<TILE>_DEM/Copernicus_DSM_COG_10_<TILE>_DEM.tif
   Os tiles são de 1°x1°, nomeados pelo canto SW ("S<lat>_00_E<lon>_00"), e são
   derivados da AOI em config/study.yaml em tempo de execução (ver
   _config.tile_sw_corners) — nunca listados à mão aqui.
   A via OpenTopography (`cloud.sdsc.edu/.../NASADEM_HGT_srtm.vrt`) retorna HTTP 401
   — exige API_Key pessoal, portanto NÃO é acesso anônimo. Removida como via
   primária nesta correção; se usada, tratar como nível B (não redistribuível sem
   credencial individual).

AOI: lida de config/study.yaml em tempo de execução (§11.2.1). Nunca fixar aqui.

Saída:
  data/raw/hydrorivers_af_v10.gdb.zip (+ .sha256 + .meta.json)
  data/raw/copernicus_dem_glo30_<TILE>.tif (+ .sha256 + .meta.json), um por tile
  necessário para cobrir a AOI.

Comportamento idempotente e falho-explícito: ver docstring de fetch_glad_cropland.py.
"""

import hashlib
import json
import sys
import urllib.error
import urllib.request
from datetime import UTC, datetime
from pathlib import Path

from _config import carregar_aoi, tile_sw_corners

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
DATA_RAW = PROJECT_ROOT / "data" / "raw"

COPERNICUS_DEM_TILE_SIZE_DEG = 1.0

HYDRORIVERS_URL = "https://data.hydrosheds.org/file/HydroRIVERS/HydroRIVERS_v10_af.gdb.zip"
HYDRORIVERS_FILENAME = "hydrorivers_af_v10.gdb.zip"
HYDRORIVERS_LICENSE = (
    "Licença própria HydroSHEDS (uso livre científico/educacional/comercial com "
    "atribuição obrigatória; não é CC0)"
)
HYDRORIVERS_SOURCE_PAGE = "https://www.hydrosheds.org/products/hydrorivers"
HYDRORIVERS_CITATION = (
    "Lehner, B., & Grill, G. (2013). \"Global river hydrography and network routing: "
    "baseline data and new approaches to study the world's large river systems.\" "
    "Hydrological Processes, 27(15), 2171-2186. DOI 10.1002/hyp.9740"
)

COPERNICUS_DEM_LICENSE = "Licença Copernicus (uso livre e gratuito; atribuição obrigatória)"
COPERNICUS_DEM_SOURCE_PAGE = (
    "https://dataspace.copernicus.eu/explore-data/data-collections/"
    "copernicus-contributing-missions/collections-description/COP-DEM"
)
COPERNICUS_DEM_CITATION = (
    "European Space Agency / Airbus (2022). \"Copernicus DEM GLO-30.\" "
    "DOI 10.5270/ESA-c5d3d65"
)
COPERNICUS_DEM_BASE = "https://copernicus-dem-30m.s3.amazonaws.com"


def tile_name(lat0: float, lon0: float) -> str:
    """Nome de tile Copernicus DEM (grade 1°x1°, canto SW), ex.: S17_00_E033_00."""
    lat_hemi = "S" if lat0 < 0 else "N"
    lon_hemi = "W" if lon0 < 0 else "E"
    return f"{lat_hemi}{abs(int(lat0)):02d}_00_{lon_hemi}{abs(int(lon0)):03d}_00"


def copernicus_dem_url(tile: str) -> str:
    nome = f"Copernicus_DSM_COG_10_{tile}_DEM"
    return f"{COPERNICUS_DEM_BASE}/{nome}/{nome}.tif"


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
               citation: str, dataset: str, aoi: dict, extra: dict | None = None) -> None:
    meta = {
        "url": url,
        "download_date": datetime.now(UTC).isoformat(),
        "size_bytes": filepath.stat().st_size,
        "license": license_text,
        "level": "A",
        "source_page": source_page,
        "dataset": dataset,
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


def fetch_hydrorivers(aoi: dict) -> bool:
    filepath = DATA_RAW / HYDRORIVERS_FILENAME
    sidecar = filepath.with_name(filepath.name + ".sha256")

    if filepath.exists() and sidecar.exists():
        registrado = sidecar.read_text(encoding="utf-8").split()
        digest = compute_sha256(filepath)
        if len(registrado) < 2 or registrado[0] != digest:
            print(f"ERRO: hash de {filepath.name} não confere com {sidecar.name}", file=sys.stderr)
            return False
        print(f"OK: {filepath.name} já presente e íntegro.")
        return True

    print(f"Baixando HydroRIVERS: {HYDRORIVERS_URL}")
    try:
        download(HYDRORIVERS_URL, filepath)
    except (urllib.error.URLError, RuntimeError, TimeoutError, OSError) as exc:
        print(f"ERRO: falha ao baixar HydroRIVERS: {exc}", file=sys.stderr)
        if filepath.exists():
            filepath.unlink()
        return False

    digest = compute_sha256(filepath)
    write_sha256(filepath, digest)
    write_meta(
        filepath, HYDRORIVERS_URL, HYDRORIVERS_SOURCE_PAGE, HYDRORIVERS_LICENSE,
        HYDRORIVERS_CITATION, "HydroRIVERS v10 (África)", aoi,
        extra={
            "resolution_m": "vetorial (~500m acurácia de posicionamento)",
            "years_covered": "datum fixo (sem série temporal)",
        },
    )
    print(f"OK: {filepath.name} baixado, {filepath.stat().st_size} bytes, sha256={digest}")
    return True


def fetch_copernicus_dem(aoi: dict) -> bool:
    tiles = [
        tile_name(lat0, lon0)
        for lat0, lon0 in tile_sw_corners(aoi, COPERNICUS_DEM_TILE_SIZE_DEG)
    ]
    if not tiles:
        print("ERRO: nenhum tile Copernicus DEM derivado da AOI.", file=sys.stderr)
        return False

    ok = True
    for tile in tiles:
        url = copernicus_dem_url(tile)
        filename = f"copernicus_dem_glo30_{tile}.tif"
        filepath = DATA_RAW / filename
        sidecar = filepath.with_name(filepath.name + ".sha256")

        if filepath.exists() and sidecar.exists():
            registrado = sidecar.read_text(encoding="utf-8").split()
            digest = compute_sha256(filepath)
            if len(registrado) < 2 or registrado[0] != digest:
                print(f"ERRO [{tile}]: hash de {filename} não confere", file=sys.stderr)
                ok = False
                continue
            print(f"OK [{tile}]: {filename} já presente e íntegro.")
            continue

        print(f"Baixando [{tile}]: {url}")
        try:
            download(url, filepath)
        except (urllib.error.URLError, RuntimeError, TimeoutError, OSError) as exc:
            print(f"ERRO [{tile}]: falha ao baixar {url}: {exc}", file=sys.stderr)
            if filepath.exists():
                filepath.unlink()
            ok = False
            continue

        digest = compute_sha256(filepath)
        write_sha256(filepath, digest)
        write_meta(
            filepath, url, COPERNICUS_DEM_SOURCE_PAGE, COPERNICUS_DEM_LICENSE,
            COPERNICUS_DEM_CITATION, "Copernicus DEM GLO-30", aoi,
            extra={"tile": tile, "resolution_m": 30},
        )
        print(f"OK [{tile}]: {filename} baixado, {filepath.stat().st_size} bytes, sha256={digest}")
    return ok


def main() -> int:
    DATA_RAW.mkdir(parents=True, exist_ok=True)
    aoi = carregar_aoi()
    ok_hydro = fetch_hydrorivers(aoi)
    ok_dem = fetch_copernicus_dem(aoi)
    if not (ok_hydro and ok_dem):
        print("FALHA: um ou mais datasets hidrográficos não foram obtidos.", file=sys.stderr)
        return 1
    print("HydroRIVERS e Copernicus DEM GLO-30 obtidos e validados.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
