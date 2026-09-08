#!/usr/bin/env python3
"""
fetch_esa_worldcover.py — Download idempotente de ESA WorldCover 2020 e 2021.

ESA WorldCover 10 m 2020 (v100) e 2021 (v200):
- Página do produtor: https://esa-worldcover.org/en/data-access
- Download real, tile(s) da grade de 3°x3° (nomeados pelo canto SW) que cobrem a
  AOI Tete-Moatize, bucket S3 público sem assinatura (confirmado por HTTP 200 em
  2026-09-07):
    2020: https://esa-worldcover.s3.eu-central-1.amazonaws.com/v100/2020/map/ESA_WorldCover_10m_2020_v100_<TILE>_Map.tif
    2021: https://esa-worldcover.s3.eu-central-1.amazonaws.com/v200/2021/map/ESA_WorldCover_10m_2021_v200_<TILE>_Map.tif
  onde <TILE> é derivado da AOI em config/study.yaml (ver _config.tile_sw_corners).
  Para a AOI confirmada (docs/ADR/0001-aoi-final.md), o único tile necessário é
  S18E033 (a grade de 3° cobre 33..36E, então xmax=34.10 ainda cai no mesmo tile).
- Digital Earth Africa (`data.digitalearthafrica.org`) foi testado em 2026-09-07 e
  NÃO RESPONDE (timeout) — removido como via alternativa (T3).
- Resolução: 10 m
- Licença: CC-BY 4.0
- Citação: Zanaga, D. et al. (2022), DOI 10.5281/zenodo.5571936 (2020) /
  10.5281/zenodo.7254221 (2021) — confirmados via Zenodo/Crossref.

AOI: lida de config/study.yaml em tempo de execução (§11.2.1). Nunca fixar aqui.

Saída:
  data/raw/esa_worldcover_<ano>_<tile_lower>.tif (+ .sha256 + .meta.json)

Comportamento idempotente e falho-explícito: ver docstring de fetch_glad_cropland.py.
Nenhum sucesso é registrado (.sha256/.meta.json) sem download efetivo verificado.
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

WORLDCOVER_TILE_SIZE_DEG = 3.0

LICENSE = "CC-BY 4.0"

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
    2020: (
        'Zanaga, D. et al. (2022). "ESA WorldCover 10 m 2020 v100." '
        "DOI 10.5281/zenodo.5571936"
    ),
    2021: (
        'Zanaga, D. et al. (2022). "ESA WorldCover 10 m 2021 v200." '
        "DOI 10.5281/zenodo.7254221"
    ),
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
        "level": "A",
        "source_page": SOURCE_PAGE,
        "ano": ano,
        "aoi_bbox": aoi,
        "tile": tile,
        "citation": citation,
        "nota": f"Tile {tile} (nao recortado para a AOI); recorte em 02_metrics.",
    }
    meta_path = filepath.with_name(filepath.name + ".meta.json")
    meta_path.write_text(json.dumps(meta, indent=2, ensure_ascii=False), encoding="utf-8")


def download(url: str, dest: Path) -> None:
    req = urllib.request.Request(url, headers={"User-Agent": "tete-moatize-fetch/1.0"})
    tmp = dest.with_suffix(dest.suffix + ".part")
    try:
        with urllib.request.urlopen(req, timeout=120) as resp:
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


def fetch_one(ano: int, url: str, citation: str, aoi: dict, tile: str) -> bool:
    filename = f"esa_worldcover_{ano}_{tile.lower()}.tif"
    filepath = DATA_RAW / filename
    sidecar = filepath.with_name(filepath.name + ".sha256")

    if filepath.exists() and sidecar.exists():
        registrado = sidecar.read_text(encoding="utf-8").split()
        digest = compute_sha256(filepath)
        if len(registrado) < 2 or registrado[0] != digest:
            print(
                f"ERRO [{ano}]: hash de {filename} não confere com {sidecar.name}",
                file=sys.stderr,
            )
            return False
        print(f"OK [{ano}]: {filename} já presente e íntegro.")
        return True

    print(f"Baixando [{ano}]: {url}")
    try:
        download(url, filepath)
    except (urllib.error.URLError, RuntimeError, TimeoutError, OSError) as exc:
        print(f"ERRO [{ano}]: falha ao baixar {url}: {exc}", file=sys.stderr)
        if filepath.exists():
            filepath.unlink()
        return False

    digest = compute_sha256(filepath)
    write_sha256(filepath, digest)
    write_meta(filepath, url, ano, citation, aoi, tile)
    print(f"OK [{ano}]: {filename} baixado, {filepath.stat().st_size} bytes, sha256={digest}")
    return True


def main() -> int:
    DATA_RAW.mkdir(parents=True, exist_ok=True)

    aoi = carregar_aoi()
    tiles = [tile_name(lat0, lon0) for lat0, lon0 in tile_sw_corners(aoi, WORLDCOVER_TILE_SIZE_DEG)]
    if not tiles:
        print("ERRO: nenhum tile ESA WorldCover derivado da AOI.", file=sys.stderr)
        return 1
    if len(tiles) > 1:
        print(
            f"AVISO: AOI cruza {len(tiles)} tiles ESA WorldCover ({tiles}); "
            "baixando todos.",
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
