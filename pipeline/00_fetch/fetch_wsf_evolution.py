#!/usr/bin/env python3
"""
fetch_wsf_evolution.py — Download idempotente do WSF Evolution (DLR).

World Settlement Footprint (WSF) Evolution — Landsat-5/-7 — Global: máscara
de assentamento anual, 30 m, 1985-2015. Nível A.

- Página do produtor / metadados: https://geoservice.dlr.de/web/datasets/wsf_evo
- Portal de download: https://download.geoservice.dlr.de/WSF_EVO/
- Confirmado por acesso anônimo (sem login, sem cadastro) em 2026-09-07.
- O portal é uma SPA; a grade de tiles (2°x2°, ~5138 tiles globais) e as URLs
  de download reais estão em um GeoJSON servido pelo próprio backend:
    https://download.geoservice.dlr.de/WSF_EVO/grid.geojson
  Cada feature tem properties.Download (URL do .tif), .filename, .md5sum,
  .filesize e .id no formato "<lon0>_<lat0>" (canto SW do tile, múltiplos de
  2° a partir de 0/0 — mesma convenção usada por _config.tile_sw_corners).
  Confirmado por inspeção: a AOI (config/study.yaml) cai nos tiles
  id="32_-18" e id="34_-18" (o tile "_-16" ao norte não é necessário: a
  convenção de grade half-open de tile_sw_corners já cobre ymax=-16.00 pelo
  tile "-18", que vai de -18.01 a -15.99).
- Resolução: 30 m. Valor de pixel = ano estimado de primeira detecção do
  assentamento (1985-2015); 0 = sem dado (confirmado na aba "Abstract" da
  página do produtor, não presumido).
- Licença: CC BY 4.0 — texto em
  https://creativecommons.org/licenses/by/4.0/ , conforme declarado na aba
  "License" da página do produtor (bloco JSON dcat-ap.de/def/licenses/cc-by/4.0).
- Citação: Marconcini, M., Metz-Marconcini, A., Esch, T., Gorelick, N. (2021).
  "Understanding Current Trends in Global Urbanisation - The World Settlement
  Footprint Suite." GI_Forum 2021, Issue 1, p. 33-38.
  DOI: 10.1553/giscience2021_01_s33

AOI: lida de config/study.yaml em tempo de execução (§11.2.1). Nunca fixar aqui.
O nome/local dos tiles é derivado do grid.geojson do produtor, não hardcoded:
o grid é baixado (ou reutilizado, se já em cache local) e filtrado pela AOI.

Saída:
  data/raw/wsf_evolution_<id>.tif (+ .sha256 + .meta.json)
  data/interim/wsf_evo_grid.geojson (cache do índice de tiles; não é espelho
  de dado nível A por si só, é só um índice de URLs — não precisa de sidecar)

Idempotência e falha explícita: mesmo padrão de fetch_esa_worldcover.py.
Nenhum sucesso é registrado (.sha256/.meta.json) sem download efetivo
verificado por hash (MD5, publicado pelo próprio grid.geojson do produtor).
"""

import hashlib
import json
import ssl
import sys
import urllib.error
import urllib.request
from datetime import UTC, datetime
from pathlib import Path

from _config import carregar_aoi, tile_sw_corners

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
DATA_RAW = PROJECT_ROOT / "data" / "raw"
DATA_INTERIM = PROJECT_ROOT / "data" / "interim"

GRID_URL = "https://download.geoservice.dlr.de/WSF_EVO/grid.geojson"
GRID_CACHE = DATA_INTERIM / "wsf_evo_grid.geojson"

TILE_SIZE_DEG = 2.0

def _ssl_context() -> ssl.SSLContext | None:
    """Contexto TLS com o bundle do certifi, se disponível.

    O host download.geoservice.dlr.de encadeia até a HARICA TLS RSA Root CA
    2021; essa raiz está no bundle do certifi mas nem sempre no cafile default
    do OpenSSL usado pelo interpretador (varia por como o Python foi
    construído). Sem isso o handshake falha com self-signed certificate in
    certificate chain mesmo a fonte sendo legítima. Cai para o contexto
    default se certifi não estiver instalado.
    """
    try:
        import certifi

        return ssl.create_default_context(cafile=certifi.where())
    except ImportError:
        return None


SSL_CONTEXT = _ssl_context()

LICENSE = "CC BY 4.0"
LICENSE_URL = "https://creativecommons.org/licenses/by/4.0/"
SOURCE_PAGE = "https://geoservice.dlr.de/web/datasets/wsf_evo"
CITATION = (
    "Marconcini, M., Metz-Marconcini, A., Esch, T., Gorelick, N. (2021). "
    '"Understanding Current Trends in Global Urbanisation - The World '
    'Settlement Footprint Suite." GI_Forum 2021, Issue 1, p. 33-38. '
    "DOI: 10.1553/giscience2021_01_s33"
)
ANOS_COBERTOS = "1985-2015 (valor de pixel = ano de primeira deteccao; 0 = sem dado)"
RESOLUCAO_M = 30


def compute_hash(filepath: Path, algo: str = "md5") -> str:
    h = hashlib.new(algo)
    with filepath.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def compute_sha256(filepath: Path) -> str:
    return compute_hash(filepath, "sha256")


def write_sha256(filepath: Path, digest: str) -> None:
    sidecar = filepath.with_name(filepath.name + ".sha256")
    sidecar.write_text(f"{digest}  {filepath.name}\n", encoding="utf-8")


def write_meta(filepath: Path, url: str, aoi: dict, tile_id: str, md5_esperado: str) -> None:
    meta = {
        "url": url,
        "download_date": datetime.now(UTC).isoformat(),
        "size_bytes": filepath.stat().st_size,
        "license": LICENSE,
        "license_url": LICENSE_URL,
        "level": "A",
        "source_page": SOURCE_PAGE,
        "citation": CITATION,
        "anos_cobertos": ANOS_COBERTOS,
        "resolucao_m": RESOLUCAO_M,
        "selo": "observado",
        "pixel_value": (
            "ano de primeira deteccao de assentamento (1985-2015); 0 = sem dado "
            "(confirmado na aba Abstract de " + SOURCE_PAGE + ")"
        ),
        "aoi_bbox": aoi,
        "tile_id": tile_id,
        "md5_produtor": md5_esperado,
        "nota": f"Tile {tile_id} (grade 2x2 graus do produtor; nao recortado para a AOI).",
    }
    meta_path = filepath.with_name(filepath.name + ".meta.json")
    meta_path.write_text(json.dumps(meta, indent=2, ensure_ascii=False), encoding="utf-8")


def download(url: str, dest: Path) -> None:
    req = urllib.request.Request(url, headers={"User-Agent": "tete-moatize-fetch/1.0"})
    tmp = dest.with_suffix(dest.suffix + ".part")
    try:
        with urllib.request.urlopen(req, timeout=180, context=SSL_CONTEXT) as resp:
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


def load_grid() -> dict:
    """Baixa (ou reutiliza) o índice de tiles do produtor. Nunca hardcode tiles."""
    DATA_INTERIM.mkdir(parents=True, exist_ok=True)
    if GRID_CACHE.exists():
        try:
            return json.loads(GRID_CACHE.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            pass
    req = urllib.request.Request(GRID_URL, headers={"User-Agent": "tete-moatize-fetch/1.0"})
    with urllib.request.urlopen(req, timeout=120, context=SSL_CONTEXT) as resp:
        if resp.status != 200:
            raise RuntimeError(f"HTTP {resp.status} para {GRID_URL}")
        raw = resp.read()
    GRID_CACHE.write_bytes(raw)
    return json.loads(raw.decode("utf-8"))


def tile_code(lon0: float, lat0: float) -> str:
    """Nome de tile em convenção hemisférica (S/N + E/W), ex.: S18E032.

    Usado só no nome do arquivo em data/raw/ (para compatibilidade com o
    contrato de cobertura de AOI de pipeline/tests/test_config.py, que agrupa
    tiles pela parte do nome anterior a "_S"/"_N"); a chave real de busca no
    grid do produtor continua sendo o id original "<lon0>_<lat0>".
    """
    lat_hemi = "S" if lat0 < 0 else "N"
    lon_hemi = "W" if lon0 < 0 else "E"
    return f"{lat_hemi}{abs(int(lat0)):02d}{lon_hemi}{abs(int(lon0)):03d}"


def tiles_for_aoi(grid: dict, aoi: dict) -> list[dict]:
    """Filtra as features do grid do produtor pelos cantos SW esperados na AOI."""
    esperados = {
        (float(lon0), float(lat0)) for lat0, lon0 in tile_sw_corners(aoi, TILE_SIZE_DEG)
    }
    achados = []
    for feature in grid["features"]:
        props = feature["properties"]
        tile_id = props["id"]
        lon_str, lat_str = tile_id.split("_")
        chave = (float(lon_str), float(lat_str))
        if chave in esperados:
            achados.append(props)
    return achados


def fetch_one(props: dict, aoi: dict) -> bool:
    tile_id = props["id"]
    lon_str, lat_str = tile_id.split("_")
    codigo = tile_code(float(lon_str), float(lat_str))
    filename = f"wsf_evolution_{codigo}.tif"
    filepath = DATA_RAW / filename
    sidecar = filepath.with_name(filepath.name + ".sha256")
    url = props["Download"]
    md5_esperado = props.get("md5sum", "")

    if filepath.exists() and sidecar.exists():
        registrado = sidecar.read_text(encoding="utf-8").split()
        digest = compute_sha256(filepath)
        if len(registrado) < 2 or registrado[0] != digest:
            print(
                f"ERRO [{tile_id}]: hash de {filename} não confere com {sidecar.name}",
                file=sys.stderr,
            )
            return False
        print(f"OK [{tile_id}]: {filename} já presente e íntegro.")
        return True

    print(f"Baixando [{tile_id}]: {url}")
    try:
        download(url, filepath)
    except (urllib.error.URLError, RuntimeError, TimeoutError, OSError) as exc:
        print(f"ERRO [{tile_id}]: falha ao baixar {url}: {exc}", file=sys.stderr)
        if filepath.exists():
            filepath.unlink()
        return False

    if md5_esperado:
        md5_real = compute_hash(filepath, "md5")
        if md5_real != md5_esperado:
            print(
                f"ERRO [{tile_id}]: MD5 divergente. produtor={md5_esperado} baixado={md5_real} "
                "— fonte pode ter mudado; abortando sem registrar sucesso.",
                file=sys.stderr,
            )
            filepath.unlink()
            return False

    digest = compute_sha256(filepath)
    write_sha256(filepath, digest)
    write_meta(filepath, url, aoi, tile_id, md5_esperado)
    print(
        f"OK [{tile_id}]: {filename} baixado, {filepath.stat().st_size} bytes, "
        f"sha256={digest}"
    )
    return True


def main() -> int:
    DATA_RAW.mkdir(parents=True, exist_ok=True)

    aoi = carregar_aoi()

    try:
        grid = load_grid()
    except (urllib.error.URLError, RuntimeError, TimeoutError, OSError) as exc:
        print(f"ERRO: falha ao obter o índice de tiles do produtor: {exc}", file=sys.stderr)
        return 1

    tiles = tiles_for_aoi(grid, aoi)
    if not tiles:
        print("ERRO: nenhum tile WSF Evolution derivado da AOI.", file=sys.stderr)
        return 1

    print(f"AOI cobre {len(tiles)} tile(s) WSF Evolution: {[t['id'] for t in tiles]}")

    resultados = [fetch_one(props, aoi) for props in tiles]

    if not all(resultados):
        print("FALHA: um ou mais tiles de WSF Evolution não foram obtidos.", file=sys.stderr)
        return 1
    print("Todos os tiles de WSF Evolution obtidos e validados.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
