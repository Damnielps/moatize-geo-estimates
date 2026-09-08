#!/usr/bin/env python3
"""Idempotent fetcher for Global-scale Mining Polygons v2 (Maus et al. 2022).

Source: PANGAEA https://doi.org/10.1594/PANGAEA.942325
License: CC-BY-SA-4.0 (nível A — já registrado em data/LICENSES.md)
Citation: Maus, V., da Silva, D. M., Gutschlhofer, J., da Rosa, R., Giljum, S.,
Gass, S. L. B., Luckeneder, S., Lieber, M., McCallum, I. (2022): Global-scale
mining polygons (Version 2) [dataset]. PANGAEA, https://doi.org/10.1594/PANGAEA.942325

Correção desta entrega (Fase 1, classificação em 3 camadas): a versão anterior
deste script tinha uma URL de download placeholder
(`https://hs.pangaea.de/datasets/published/942325/...`, retorna 404 —
registrado em `data/licenses_parts/agricultura.md`). A URL correta foi
descoberta inspecionando o texto de descrição do dataset
(`?format=textfile`), que lista o padrão real de download por arquivo:
`https://download.pangaea.de/dataset/942325/files/<nome_do_arquivo>`.

Este script baixa o GeoPackage completo (~23,5 MB, ~44.929 polígonos
globais), recorta para a AOI de `config/study.yaml` (fonte única — nunca
hardcode o bbox aqui) e grava dois artefatos em `data/raw/`:
  - `global_mining_polygons_v2_maus_2022.gpkg` — arquivo global bruto (para
    permitir reprocessar com outra AOI sem rebaixar 23,5 MB);
  - `global_mining_polygons_v2_maus_2022_aoi.geojson` — recorte já na AOI do
    estudo, o que `classificacao.py` de fato consome.

Uso: `uv run python pipeline/00_fetch/fetch_maus_mining_polygons.py`
"""

from __future__ import annotations

import hashlib
import json
import logging
import subprocess
import sys
from datetime import UTC, datetime
from pathlib import Path

import geopandas as gpd

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _config import carregar_aoi

DATA_DIR = Path(__file__).parent.parent.parent / "data" / "raw"
DATA_INTERIM = Path(__file__).parent.parent.parent / "data" / "interim"
DATASET_NAME = "global_mining_polygons_v2_maus_2022"
DOI = "10.1594/PANGAEA.942325"
DOI_URL = "https://doi.org/10.1594/PANGAEA.942325"

# Descoberto em `?format=textfile` (ver docstring do módulo) — não reconstruído
# manualmente. Padrão: https://download.pangaea.de/dataset/<id>/files/<nome>.
DOWNLOAD_URL = (
    "https://download.pangaea.de/dataset/942325/files/global_mining_polygons_v2.gpkg"
)

# `data/raw/` exige `.sha256`+`.meta.json` por arquivo (contrato
# `test_checksums_de_data_raw_conferem`) — um log de execução não é um dado
# de nível A, vai em `data/interim/` (regenerável, git-ignored).
DATA_INTERIM.mkdir(parents=True, exist_ok=True)
LOG_FILE = DATA_INTERIM / "maus_mining_fetch.log"

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[logging.FileHandler(LOG_FILE), logging.StreamHandler()],
)
logger = logging.getLogger(__name__)


def sha256_file(filepath: Path, chunk_size: int = 8192) -> str:
    sha256 = hashlib.sha256()
    with open(filepath, "rb") as f:
        for chunk in iter(lambda: f.read(chunk_size), b""):
            sha256.update(chunk)
    return sha256.hexdigest()


def fetch_dataset(output_file: Path, url: str) -> bool:
    logger.info(f"Attempting download from {url}")
    cmd = ["curl", "-L", "-f", "--max-time", "600", "-o", str(output_file), url]
    result = subprocess.run(cmd, capture_output=True, text=True, check=False)
    if result.returncode != 0:
        logger.warning(f"curl failed with code {result.returncode}: {result.stderr}")
        return False
    if not output_file.exists() or output_file.stat().st_size == 0:
        logger.error(f"File not created or empty: {output_file}")
        return False
    logger.info(f"Downloaded {output_file.stat().st_size} bytes to {output_file}")
    return True


def commit_git_atual() -> str:
    try:
        return subprocess.check_output(
            ["git", "rev-parse", "HEAD"],
            cwd=Path(__file__).resolve().parents[2],
            text=True,
            stderr=subprocess.DEVNULL,
        ).strip()
    except (subprocess.CalledProcessError, FileNotFoundError):
        return "desconhecido (git indisponível)"


def main() -> int:
    logger.info("Maus et al. Mining Polygons v2 — Fetcher initialized")
    logger.info(f"DOI: {DOI_URL}")

    DATA_DIR.mkdir(parents=True, exist_ok=True)
    DATA_INTERIM.mkdir(parents=True, exist_ok=True)

    output_file = DATA_DIR / f"{DATASET_NAME}.gpkg"
    checksum_file = DATA_DIR / f"{DATASET_NAME}.gpkg.sha256"
    meta_file = DATA_DIR / f"{DATASET_NAME}.gpkg.meta.json"

    ja_valido = False
    if output_file.exists() and checksum_file.exists():
        expected = checksum_file.read_text().split()[0].strip()
        actual = sha256_file(output_file)
        if actual == expected:
            logger.info("Arquivo global já existe e o checksum confere; pulando download.")
            ja_valido = True
        else:
            logger.warning("Checksum não confere; baixando de novo.")
            output_file.unlink()
            checksum_file.unlink()

    if not ja_valido:
        if not fetch_dataset(output_file, DOWNLOAD_URL):
            logger.error(
                "Download falhou. Baixe manualmente de "
                "https://doi.org/10.1594/PANGAEA.942325 (botão de download, "
                "arquivo global_mining_polygons_v2.gpkg)."
            )
            meta = {
                "source": "Maus et al. Global-scale Mining Polygons v2",
                "doi": DOI,
                "url": DOI_URL,
                "download_url": DOWNLOAD_URL,
                "license": "CC-BY-SA-4.0",
                "level": "A",
                "status": "download_failed",
                "checked_date": datetime.now(tz=UTC).isoformat(),
            }
            meta_file.write_text(json.dumps(meta, indent=2, ensure_ascii=False))
            return 1

        actual_sha256 = sha256_file(output_file)
        checksum_file.write_text(f"{actual_sha256}  {output_file.name}\n")
        logger.info(f"Checksum (SHA-256): {actual_sha256}")

        size = output_file.stat().st_size
        meta = {
            "source": "Maus et al. Global-scale Mining Polygons v2",
            "doi": DOI,
            "url": DOI_URL,
            "download_url": DOWNLOAD_URL,
            "license": "CC-BY-SA-4.0",
            "level": "A",
            "resolution": "10 m (source: Sentinel-2 cloudless mosaic 2019, s2maps.eu)",
            "spatial_extent": "Global; 44,929 polygons, 101,583 km²",
            "temporal_extent": "2019 (source imagery year); v2 released 2022-03-14",
            "format": "GeoPackage (GPKG)",
            "crs": "EPSG:4326 (WGS84)",
            "size_bytes": size,
            "sha256": actual_sha256,
            "download_date": datetime.now(tz=UTC).isoformat(),
            "citation": (
                "Maus, V., da Silva, D. M., Gutschlhofer, J., da Rosa, R., Giljum, S., "
                "Gass, S. L. B., Luckeneder, S., Lieber, M., McCallum, I. (2022): "
                "Global-scale mining polygons (Version 2) [dataset]. PANGAEA, "
                "https://doi.org/10.1594/PANGAEA.942325"
            ),
            "accuracy_reported_by_producer": {
                "overall_accuracy": 0.883,
                "kappa": 0.77,
                "f1_score": 0.87,
                "producer_accuracy_mine": 0.789,
                "user_accuracy_mine": 0.972,
                "n_control_points": 1000,
                "nota": "Validação própria dos autores (Maus et al.), não recalculada aqui.",
            },
        }
        meta_file.write_text(json.dumps(meta, indent=2, ensure_ascii=False))
        logger.info(f"Metadata written to {meta_file}")

    # Recorte para a AOI do estudo — fonte única config/study.yaml (nunca hardcode).
    aoi = carregar_aoi()
    bbox = (aoi["xmin"], aoi["ymin"], aoi["xmax"], aoi["ymax"])
    gdf = gpd.read_file(output_file, bbox=bbox)
    logger.info(f"{len(gdf)} polígonos de mineração dentro da AOI {bbox}")

    aoi_file = DATA_DIR / f"{DATASET_NAME}_aoi.geojson"
    aoi_checksum = DATA_DIR / f"{DATASET_NAME}_aoi.geojson.sha256"
    aoi_meta = DATA_DIR / f"{DATASET_NAME}_aoi.geojson.meta.json"
    gdf.to_file(aoi_file, driver="GeoJSON")

    aoi_sha256 = sha256_file(aoi_file)
    aoi_checksum.write_text(f"{aoi_sha256}  {aoi_file.name}\n")

    aoi_meta_content = {
        "source": "Maus et al. Global-scale Mining Polygons v2 — recorte AOI",
        "doi": DOI,
        "url": DOI_URL,
        "arquivo_origem": output_file.name,
        "hash_arquivo_origem": sha256_file(output_file),
        "aoi_bbox": {"xmin": bbox[0], "ymin": bbox[1], "xmax": bbox[2], "ymax": bbox[3]},
        "aoi_crs": aoi["crs"],
        "n_poligonos": len(gdf),
        "area_total_km2": float(gdf.to_crs(32736).area.sum() / 1e6) if len(gdf) else 0.0,
        "license": "CC-BY-SA-4.0",
        "level": "A",
        "crs": "EPSG:4326 (WGS84)",
        "sha256": aoi_sha256,
        "processed_date": datetime.now(tz=UTC).isoformat(),
        "commit_git": commit_git_atual(),
        "script": "pipeline/00_fetch/fetch_maus_mining_polygons.py",
        "nota": (
            "Polígonos digitalizados sobre mosaico Sentinel-2 sem nuvens de 2019 — "
            "representam a pegada minerária em 2019, não em anos anteriores. Para "
            "2000/2005 (antes da abertura da mina de Moatize em 2011), este polígono "
            "NÃO é retroativo; ver metodologia por ano em "
            "pipeline/01_imagery/classificacao.py e data/provenance_parts/imagem_fase1.md."
        ),
    }
    aoi_meta.write_text(json.dumps(aoi_meta_content, indent=2, ensure_ascii=False))

    logger.info(f"Recorte AOI gravado em {aoi_file}")
    logger.info("Fetch complete.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
