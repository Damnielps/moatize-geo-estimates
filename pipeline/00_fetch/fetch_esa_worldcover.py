#!/usr/bin/env python3
"""
fetch_esa_worldcover.py — Download idempotente de ESA WorldCover 2020 e 2021, recortado na AOI.

ESA WorldCover 10 m 2020 (v100) e 2021 (v200):
- Página do produtor: https://esa-worldcover.org/en/data-access (HTTP 200)
- Licença: CC-BY 4.0, declarada na página do produtor
  (https://esa-worldcover.org/en/data-access, seção "Data access").
- Download real, tile(s) da grade de 3°x3° (nomeados pelo canto SW) que cobrem a
  AOI Tete-Moatize, bucket S3 público sem assinatura (confirmado por HTTP 200 em
  2026-09-08):
    2020: https://esa-worldcover.s3.eu-central-1.amazonaws.com/v100/2020/map/ESA_WorldCover_10m_2020_v100_<TILE>_Map.tif
    2021: https://esa-worldcover.s3.eu-central-1.amazonaws.com/v200/2021/map/ESA_WorldCover_10m_2021_v200_<TILE>_Map.tif
  <TILE> é DERIVADO da AOI de config/study.yaml via `_config.tile_sw_corners`
  (grade de 3°) — nunca hardcoded. Para a AOI confirmada em 2026-09-08, o único
  tile resultante é S18E033 (canto SW: lat0=-18.0, lon0=33.0).
- Resolução: 10 m
- Citação: Zanaga, D. et al. (2022), DOI 10.5281/zenodo.5571936 (2020) /
  10.5281/zenodo.7254221 (2021).

Cada tile tem ~180 MB (confirmado por Content-Length). Em vez de mirrorar o tile
inteiro, este script lê a janela da AOI (+ margem de 0.02 grau) via GDAL
`/vsicurl/` (rasterio) — mesma lógica de fetch_glad_cropland.py.

Saída: data/raw/esa_worldcover_<ano>_<tile_lower>_aoi.tif (+ .sha256 + .meta.json)
"""

import hashlib
import json
import sys
from datetime import UTC, datetime
from pathlib import Path

import rasterio
from _config import carregar_aoi, tile_sw_corners
from rasterio.windows import from_bounds

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
DATA_RAW = PROJECT_ROOT / "data" / "raw"

WORLDCOVER_TILE_SIZE_DEG = 3.0
MARGEM_GRAUS = 0.02

LICENSE = "CC-BY 4.0"
LICENSE_URL = "https://esa-worldcover.org/en/data-access"

BASE_URLS = {
    2020: (
        "https://esa-worldcover.s3.eu-central-1.amazonaws.com/v100/2020/map/"
        "ESA_WorldCover_10m_2020_v100_{tile}_Map.tif"
    ),
    2021: (
        "https://esa-worldcover.s3.eu-central-1.amazonaws.com/v200/2021/map/"
        "ESA_WorldCover_10m_2021_v200_{tile}_Map.tif"
    ),
}

CITATIONS = {
    2020: ('Zanaga, D. et al. (2022). "ESA WorldCover 10 m 2020 v100." DOI 10.5281/zenodo.5571936'),
    2021: ('Zanaga, D. et al. (2022). "ESA WorldCover 10 m 2021 v200." DOI 10.5281/zenodo.7254221'),
}

SOURCE_PAGE = "https://esa-worldcover.org/en/data-access"


def tile_name(lat0: float, lon0: float) -> str:
    """Nome de tile ESA WorldCover (grade 3°x3°, canto SW), ex.: S18E033."""
    lat_hemi = "S" if lat0 < 0 else "N"
    lon_hemi = "W" if lon0 < 0 else "E"
    return f"{lat_hemi}{abs(int(lat0)):02d}{lon_hemi}{abs(int(lon0)):03d}"


def compute_sha256(filepath: Path) -> str:
    sha256_hash = hashlib.sha256()
    with filepath.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            sha256_hash.update(chunk)
    return sha256_hash.hexdigest()


def write_sha256(filepath: Path, digest: str) -> None:
    sidecar = filepath.with_name(filepath.name + ".sha256")
    sidecar.write_text(f"{digest}  {filepath.name}\n", encoding="utf-8")


def write_meta(filepath: Path, url: str, ano: int, citation: str, aoi: dict, tile: str) -> None:
    meta = {
        "url": url,
        "download_date": datetime.now(UTC).isoformat(),
        "size_bytes": filepath.stat().st_size,
        "license": LICENSE,
        "license_url": LICENSE_URL,
        "level": "A",
        "selo": "observado",
        "source_page": SOURCE_PAGE,
        "ano": ano,
        "anos_cobertos": str(ano),
        "aoi_bbox": aoi,
        "tile": tile,
        "citation": citation,
        "nota": (
            f"Recortado da AOI (+{MARGEM_GRAUS} grau de margem) via leitura em janela "
            "GDAL /vsicurl/ no momento do fetch; o tile 3x3 grau inteiro NÃO foi "
            "mirrorado."
        ),
    }
    meta_path = filepath.with_name(filepath.name + ".meta.json")
    meta_path.write_text(json.dumps(meta, indent=2, ensure_ascii=False), encoding="utf-8")


def fetch_one(ano: int, remote_url: str, citation: str, aoi: dict, tile: str) -> bool:
    filename = f"esa_worldcover_{ano}_{tile.lower()}_aoi.tif"
    filepath = DATA_RAW / filename
    sidecar = filepath.with_name(filepath.name + ".sha256")

    if filepath.exists() and sidecar.exists():
        registrado = sidecar.read_text(encoding="utf-8").split()
        digest = compute_sha256(filepath)
        if len(registrado) < 2 or registrado[0] != digest:
            print(
                f"ERRO [{ano}]: hash de {filename} não confere com {sidecar.name}", file=sys.stderr
            )
            return False
        print(f"OK [{ano}]: {filename} já presente e íntegro.")
        return True

    vsi_url = f"/vsicurl/{remote_url}"
    print(f"Lendo janela AOI [{ano}]: {remote_url}")
    try:
        with rasterio.open(vsi_url) as src:
            win = from_bounds(
                aoi["xmin"] - MARGEM_GRAUS,
                aoi["ymin"] - MARGEM_GRAUS,
                aoi["xmax"] + MARGEM_GRAUS,
                aoi["ymax"] + MARGEM_GRAUS,
                src.transform,
            )
            data = src.read(1, window=win)
            out_transform = src.window_transform(win)
            profile = src.profile.copy()
            profile.update(
                height=data.shape[0],
                width=data.shape[1],
                transform=out_transform,
                compress="deflate",
            )
            tmp = filepath.with_suffix(filepath.suffix + ".part")
            with rasterio.open(tmp, "w", **profile) as dst:
                dst.write(data, 1)
            tmp.replace(filepath)
    except Exception as exc:
        print(f"ERRO [{ano}]: falha ao ler/recortar {remote_url}: {exc}", file=sys.stderr)
        tmp = filepath.with_suffix(filepath.suffix + ".part")
        if tmp.exists():
            tmp.unlink()
        if filepath.exists():
            filepath.unlink()
        return False

    digest = compute_sha256(filepath)
    write_sha256(filepath, digest)
    write_meta(filepath, remote_url, ano, citation, aoi, tile)
    print(
        f"OK [{ano}]: {filename} gravado (recorte AOI), "
        f"{filepath.stat().st_size} bytes, sha256={digest}"
    )
    return True


def main() -> int:
    DATA_RAW.mkdir(parents=True, exist_ok=True)

    aoi = carregar_aoi()
    tiles = [tile_name(lat0, lon0) for lat0, lon0 in tile_sw_corners(aoi, WORLDCOVER_TILE_SIZE_DEG)]
    if not tiles:
        print("ERRO: nenhum tile ESA WorldCover derivado da AOI.", file=sys.stderr)
        return 1
    print(f"Tile(s) ESA WorldCover derivado(s) da AOI: {tiles}")
    if len(tiles) > 1:
        print(
            f"AVISO: AOI cruza {len(tiles)} tiles ESA WorldCover ({tiles}); baixando todos.",
            file=sys.stderr,
        )

    resultados = []
    for ano, base_url in BASE_URLS.items():
        for tile in tiles:
            url = base_url.format(tile=tile)
            resultados.append(fetch_one(ano, url, CITATIONS[ano], aoi, tile))

    if not all(resultados):
        print("FALHA: um ou mais anos/tiles de ESA WorldCover não foram obtidos.", file=sys.stderr)
        return 1
    print("Todos os anos/tiles de ESA WorldCover obtidos e validados.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
