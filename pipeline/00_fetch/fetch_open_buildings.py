#!/usr/bin/env python3
"""pipeline/00_fetch/fetch_open_buildings.py — Google Open Buildings v3, recorte da AOI.

§5.2 item 5: densidade de edificações e regularidade da malha como proxy de
urbanização formal vs. informal. Google Open Buildings v3 é nível A
(`data/LICENSES.md`) mas é distribuído em blocos S2-nível-4 continentais
(~1 GB por bloco, cobrindo dezenas de países) — não há endpoint que sirva só a
AOI. Este script:

1. Baixa o índice público de blocos (`tiles.geojson`).
2. Identifica o(s) bloco(s) que intersectam a AOI de `config/study.yaml`.
3. Faz *streaming* do CSV.gz do bloco (sem gravar o `.gz` de ~1 GB em disco:
   `requests` com `stream=True` -> `gzip.GzipFile` sobre o socket -> filtro
   linha a linha pelo bbox) e grava só as linhas dentro da AOI.

O artefato gravado (`data/raw/open_buildings_v3_aoi.csv`) é um **recorte
espacial** da fonte nível A, não o bloco inteiro — documentado assim em
`.meta.json` porque mirror do bloco de ~1 GB é impraticável e desnecessário
(o resto do bloco cobre outros países). O método é 100% reproduzível a partir
da URL pública registrada.

Idempotência: pula se o arquivo de saída já existe com hash íntegro. Use
--force para refazer.
"""

from __future__ import annotations

import argparse
import csv
import gzip
import hashlib
import io
import json
import sys
from datetime import UTC, datetime
from pathlib import Path

import requests
from shapely.geometry import box, shape

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _config import carregar_aoi

REPO_ROOT = Path(__file__).resolve().parents[2]
OUT_CSV = REPO_ROOT / "data" / "raw" / "open_buildings_v3_aoi.csv"
TILES_INDEX_URL = "https://openbuildings-public-dot-gweb-research.uw.r.appspot.com/public/tiles.geojson"
TIMEOUT = 60


def _sha256(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def _ja_integro(path: Path) -> bool:
    sha_file = path.with_suffix(path.suffix + ".sha256")
    if not (path.exists() and sha_file.exists()):
        return False
    esperado = sha_file.read_text().split()[0]
    return _sha256(path) == esperado


def _tiles_que_intersectam(aoi_box) -> list[dict]:
    r = requests.get(TILES_INDEX_URL, timeout=TIMEOUT)
    r.raise_for_status()
    idx = r.json()
    out = []
    for feat in idx["features"]:
        geom = shape(feat["geometry"])
        if geom.intersects(aoi_box):
            out.append(feat["properties"])
    return out


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--force", action="store_true")
    args = ap.parse_args()

    if OUT_CSV.exists() and _ja_integro(OUT_CSV) and not args.force:
        print(f"OK: {OUT_CSV} já existe com hash íntegro. Pulando (--force para refazer).")
        return

    aoi = carregar_aoi()
    aoi_box = box(aoi["xmin"], aoi["ymin"], aoi["xmax"], aoi["ymax"])

    print(f"Consultando índice de blocos: {TILES_INDEX_URL}", file=sys.stderr)
    try:
        tiles = _tiles_que_intersectam(aoi_box)
    except requests.RequestException as e:
        print(f"FALHA ao obter índice de blocos do Open Buildings v3: {e}", file=sys.stderr)
        print(
            "Sem o índice não é possível localizar o bloco correto. "
            "Nenhum arquivo será gravado; use o proxy de densidade de edificação "
            "derivado da camada 'urbano' classificada (pipeline/02_metrics).",
            file=sys.stderr,
        )
        sys.exit(1)

    if not tiles:
        print("FALHA: nenhum bloco do índice intersecta a AOI. Nada gravado.", file=sys.stderr)
        sys.exit(1)

    print(f"Blocos que intersectam a AOI: {[t['tile_id'] for t in tiles]}", file=sys.stderr)

    OUT_CSV.parent.mkdir(parents=True, exist_ok=True)
    n_linhas = 0
    cabecalho = [
        "latitude",
        "longitude",
        "area_in_meters",
        "confidence",
        "geometry",
        "full_plus_code",
    ]
    with open(OUT_CSV, "w", newline="", encoding="utf-8") as fout:
        writer = csv.writer(fout)
        writer.writerow(cabecalho)
        for tile in tiles:
            url = tile["tile_url"]
            tam_mb = tile.get("size_mb", "?")
            print(f"Streaming {url} ({tam_mb} MB, filtrando pela AOI)...", file=sys.stderr)
            try:
                resp = requests.get(url, stream=True, timeout=TIMEOUT)
                resp.raise_for_status()
            except requests.RequestException as e:
                print(f"FALHA ao baixar {url}: {e}", file=sys.stderr)
                sys.exit(1)
            raw = resp.raw
            raw.decode_content = True
            with gzip.GzipFile(fileobj=raw) as gz:
                text = io.TextIOWrapper(gz, encoding="utf-8")
                reader = csv.reader(text)
                header = next(reader)
                assert header[:4] == cabecalho[:4], header
                for i, row in enumerate(reader):
                    if i % 2_000_000 == 0 and i > 0:
                        print(
                            f"  ... {i:,} linhas lidas do bloco, {n_linhas:,} dentro da AOI",
                            file=sys.stderr,
                        )
                    lat = float(row[0])
                    lon = float(row[1])
                    if aoi["xmin"] <= lon <= aoi["xmax"] and aoi["ymin"] <= lat <= aoi["ymax"]:
                        writer.writerow(row)
                        n_linhas += 1
            print(
                f"Bloco {tile['tile_id']}: {n_linhas:,} edificações dentro da AOI até aqui.",
                file=sys.stderr,
            )

    sha = _sha256(OUT_CSV)
    (OUT_CSV.with_suffix(OUT_CSV.suffix + ".sha256")).write_text(f"{sha}  {OUT_CSV.name}\n")
    tamanho_bytes = OUT_CSV.stat().st_size
    meta = {
        "fonte": "Google Open Buildings v3",
        "url_indice": TILES_INDEX_URL,
        "blocos_origem": [{"tile_id": t["tile_id"], "url": t["tile_url"]} for t in tiles],
        "metodo": (
            "Streaming do(s) bloco(s) S2-nível-4 que intersectam a AOI "
            "(config/study.yaml -> aoi.bbox), filtro linha a linha por "
            "latitude/longitude dentro do bbox, sem gravar o bloco original "
            "(~1 GB, cobre múltiplos países) em disco."
        ),
        "aoi_bbox": aoi,
        "n_edificacoes_aoi": n_linhas,
        "size_bytes": tamanho_bytes,
        "licenca": "CC-BY-4.0 (ou ODbL 1.0, à escolha do usuário) — ver data/LICENSES.md",
        "nivel": "A",
        "data_processamento": datetime.now(UTC).isoformat(),
        "nota": (
            "Recorte espacial de uma fonte nível A, não o bloco completo. "
            "Reproduzível byte a byte a partir da URL do bloco e do bbox acima."
        ),
    }
    (OUT_CSV.with_suffix(OUT_CSV.suffix + ".meta.json")).write_text(
        json.dumps(meta, indent=2, ensure_ascii=False)
    )
    print(f"OK: {n_linhas:,} edificações gravadas em {OUT_CSV}", file=sys.stderr)


if __name__ == "__main__":
    main()
