#!/usr/bin/env python3
"""
fetch_glad_cropland.py — Download idempotente de GLAD Global Cropland, recortado na AOI.

GLAD Global Cropland (Potapov et al. 2021, Nature Food 3, 19-28, DOI
10.1038/s43016-021-00429-z — confirmado via doi.org, redireciona para
nature.com/articles/s43016-021-00429-z):

- Página do produtor: https://glad.umd.edu/dataset/croplands (HTTP 200)
- Licença: CC-BY 4.0, declarada na página do produtor.
- Download real (HEAD 200 confirmado em 2026-09-08), mosaico regional "SE"
  (Sudeste da África, cobre a AOI Tete-Moatize):
  https://gladxfer.umd.edu/Potapov/Global_Crop/Data/Global_cropland_SE_<ANO>.tif
- Resolução: 30 m
- Anos disponíveis (compostos quinquenais reais): 2003, 2007, 2011, 2015, 2019
- Formato: GeoTIFF

Cada mosaico regional "SE" tem ~684 MB (confirmado por Content-Length). Em vez de
baixar o arquivo inteiro para depois recortar em 02_metrics, este script usa leitura
em janela via GDAL `/vsicurl/` (rasterio) para trazer só a AOI de config/study.yaml
(§ regra de fetch: "não traga tile global inteiro se der para recortar"), com uma
margem de 0.02 grau (~2 km) para não cortar em cima da borda.

AOI: lida de config/study.yaml em tempo de execução (§11.2.1). Nunca fixar aqui.

Saída:
  data/raw/glad_cropland_<ano>_aoi.tif
  data/raw/glad_cropland_<ano>_aoi.tif.sha256
  data/raw/glad_cropland_<ano>_aoi.tif.meta.json

Comportamento (idempotente e falho-explícito, §11.2.2):
  1. Se o arquivo local existe com .sha256 íntegro: pula.
  2. Se não existe: abre a fonte remota via /vsicurl/, lê a janela da AOI (+ margem) e
     grava localmente. Qualquer falha de rede/HTTP -> sys.exit(1), sem gravar sidecars.
"""

import hashlib
import json
import sys
from datetime import UTC, datetime
from pathlib import Path

import rasterio
from _config import carregar_aoi
from rasterio.windows import from_bounds

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
DATA_RAW = PROJECT_ROOT / "data" / "raw"

ANOS = [2003, 2007, 2011, 2015, 2019]
MARGEM_GRAUS = 0.02

SOURCE_PAGE = "https://glad.umd.edu/dataset/croplands"
DOWNLOAD_BASE = "https://gladxfer.umd.edu/Potapov/Global_Crop/Data"
LICENSE = "CC-BY 4.0"
LICENSE_URL = "https://glad.umd.edu/dataset/croplands"
CITATION = (
    "Potapov, P., Turubanova, S., Hansen, M.C., Tyukavina, A., Zalles, V., Khan, A., "
    'Song, X.-P., Pickens, A., Shen, Q., Cortez, J. (2021). "Global maps of cropland '
    "extent and change show accelerated cropland expansion in the twenty-first "
    'century." Nature Food 3, 19-28. DOI 10.1038/s43016-021-00429-z'
)


def compute_sha256(filepath: Path) -> str:
    sha256_hash = hashlib.sha256()
    with filepath.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            sha256_hash.update(chunk)
    return sha256_hash.hexdigest()


def write_sha256(filepath: Path, digest: str) -> None:
    sidecar = filepath.with_name(filepath.name + ".sha256")
    sidecar.write_text(f"{digest}  {filepath.name}\n", encoding="utf-8")


def write_meta(filepath: Path, url: str, ano: int, aoi: dict) -> None:
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
        "anos_cobertos": f"composto quinquenal centrado em {ano}",
        "aoi_bbox": aoi,
        "citation": CITATION,
        "nota": (
            f"Recortado da AOI (+{MARGEM_GRAUS} grau de margem) via leitura em janela "
            "GDAL /vsicurl/ no momento do fetch; o arquivo global 'SE' NÃO foi "
            "mirrorado inteiro."
        ),
    }
    meta_path = filepath.with_name(filepath.name + ".meta.json")
    meta_path.write_text(json.dumps(meta, indent=2, ensure_ascii=False), encoding="utf-8")


def fetch_one(ano: int, aoi: dict) -> bool:
    filename = f"glad_cropland_{ano}_aoi.tif"
    filepath = DATA_RAW / filename
    remote_url = f"{DOWNLOAD_BASE}/Global_cropland_SE_{ano}.tif"
    sidecar = filepath.with_name(filepath.name + ".sha256")

    if filepath.exists() and sidecar.exists():
        registrado = sidecar.read_text(encoding="utf-8").split()
        digest = compute_sha256(filepath)
        if len(registrado) < 2 or registrado[0] != digest:
            print(
                f"ERRO [{ano}]: hash de {filename} não confere com {sidecar.name}", file=sys.stderr
            )
            return False
        print(f"OK [{ano}]: {filename} já presente e íntegro (hash confere).")
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
    write_meta(filepath, remote_url, ano, aoi)
    print(
        f"OK [{ano}]: {filename} gravado (recorte AOI), "
        f"{filepath.stat().st_size} bytes, sha256={digest}"
    )
    return True


def main() -> int:
    DATA_RAW.mkdir(parents=True, exist_ok=True)
    aoi = carregar_aoi()
    resultados = [fetch_one(ano, aoi) for ano in ANOS]
    if not all(resultados):
        print("FALHA: um ou mais anos de GLAD Global Cropland não foram obtidos.", file=sys.stderr)
        return 1
    print("Todos os anos de GLAD Global Cropland obtidos e validados.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
