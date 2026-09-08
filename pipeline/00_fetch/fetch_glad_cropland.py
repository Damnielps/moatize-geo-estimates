#!/usr/bin/env python3
"""
fetch_glad_cropland.py — Download e verificação idempotente de GLAD Global Cropland.

GLAD Global Cropland (Potapov et al. 2021, Nature Food 3, 19-28, DOI
10.1038/s43016-021-00429-z — corrigido em T3; o DOI 10.1038/s41597-022-01292-5
usado em versões anteriores deste script NÃO resolve):

- Página do produtor: https://glad.umd.edu/dataset/croplands
- Download real (confirmado por HTTP 200 em 2026-09-07, após redirect 301):
  https://gladxfer.umd.edu/Potapov/Global_Crop/Data/Global_cropland_SE_<ANO>.tif
  (mosaico regional "SE" = Sudeste da África, cobre a AOI Tete-Moatize)
- Resolução: 30 m
- Anos disponíveis: 2003, 2007, 2011, 2015, 2019 (compostos quinquenais reais —
  NÃO 2000/2004/2008/2012/2016, erro corrigido em T3)
- Formato: GeoTIFF
- Licença: CC-BY 4.0

AOI: lida de config/study.yaml em tempo de execução (§11.2.1). Nunca fixar aqui.

Saída:
  data/raw/glad_cropland_<ano>_se.tif
  data/raw/glad_cropland_<ano>_se.tif.sha256
  data/raw/glad_cropland_<ano>_se.tif.meta.json

Comportamento (idempotente e falho-explícito, §11.2.2 e regra de fetch do orquestrador):
  1. Se o arquivo local existe: recalcula o hash e compara contra o hash gravado no
     .sha256 já existente. Diverge -> falha (sys.exit(1)), NÃO sobrescreve.
  2. Se não existe: baixa via streaming HTTP. Qualquer status HTTP != 200, timeout,
     ou erro de rede -> falha (sys.exit(1)) e NÃO grava .sha256/.meta.json (o script
     nunca registra sucesso sem ter baixado o arquivo).
  3. Ao baixar com sucesso: grava o arquivo, calcula sha256, grava <arquivo>.sha256
     no formato "<hash>  <nome>" (compatível com `shasum -c`) e <arquivo>.meta.json.
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

ANOS = [2003, 2007, 2011, 2015, 2019]

SOURCE_PAGE = "https://glad.umd.edu/dataset/croplands"
DOWNLOAD_BASE = "https://gladxfer.umd.edu/Potapov/Global_Crop/Data"
LICENSE = "CC-BY 4.0"
CITATION = (
    "Potapov, P., Turubanova, S., Hansen, M.C., Tyukavina, A., Zalles, V., Khan, A., "
    "Song, X.-P., Pickens, A., Shen, Q., Cortez, J. (2021). \"Global maps of cropland "
    "extent and change show accelerated cropland expansion in the twenty-first "
    "century.\" Nature Food 3, 19-28. DOI 10.1038/s43016-021-00429-z"
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
        "level": "A",
        "source_page": SOURCE_PAGE,
        "ano": ano,
        "aoi_bbox": aoi,
        "citation": CITATION,
        "nota": "Mosaico regional 'SE' (nao recortado para a AOI); recorte em 02_metrics.",
    }
    meta_path = filepath.with_name(filepath.name + ".meta.json")
    meta_path.write_text(json.dumps(meta, indent=2, ensure_ascii=False), encoding="utf-8")


def download(url: str, dest: Path) -> None:
    """Baixa `url` para `dest` via streaming. Levanta exceção em qualquer falha."""
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


def fetch_one(ano: int, aoi: dict) -> bool:
    """Retorna True em sucesso (arquivo presente e validado), False em falha."""
    filename = f"glad_cropland_{ano}_se.tif"
    filepath = DATA_RAW / filename
    url = f"{DOWNLOAD_BASE}/Global_cropland_SE_{ano}.tif"
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
        print(f"OK [{ano}]: {filename} já presente e íntegro (hash confere).")
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
    write_meta(filepath, url, ano, aoi)
    print(f"OK [{ano}]: {filename} baixado, {filepath.stat().st_size} bytes, sha256={digest}")
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
