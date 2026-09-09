#!/usr/bin/env python3
"""Espelha do OpenStreetMap as camadas de CONTEXTO do mapa: topônimos, rodovias,
ferrovia e aeródromo, restritas à AOI de `config/study.yaml`.

## Por que este script existe (ORCHESTRATION_LOG.md 4-17)

A primeira coleta destas camadas foi feita **ad hoc**, por consultas Overpass avulsas: os
GeoJSON ficaram em `data/raw/` com sidecar correto, mas **nenhum script foi gravado**. O
critério de §10 exige que `make all` reproduza os artefatos em ambiente limpo sem
intervenção manual — e uma coleta que só existe no histórico de uma sessão não reproduz.
Este script fecha essa lacuna e, na mesma passada, acrescenta o aeródromo de Tete.

Contexto ≠ medição: nada daqui entra em número publicado. São camadas de **leitura** do
mapa — o leitor precisa saber onde fica Moatize, por onde passa a N7 e onde está a
ferrovia para interpretar a mancha construída. Por isso `selo: contexto`.

Licença: **ODbL 1.0**. A atribuição `© OpenStreetMap contributors` é obrigatória e está
registrada no `.meta.json` de cada arquivo e exibida pelo app no controle de atribuição.

Uso:
    uv run python pipeline/00_fetch/fetch_osm_contexto.py [camada ...]

Sem argumentos, busca todas. Idempotente: pula a camada cujo `.geojson`, `.sha256` e
`.meta.json` já existem — para rebaixar, apague o arquivo.
"""
from __future__ import annotations

import hashlib
import json
import subprocess
import sys
import time
from datetime import UTC, datetime
from pathlib import Path

import yaml

REPO_ROOT = Path(__file__).resolve().parents[2]
RAW = REPO_ROOT / "data" / "raw"
CONFIG = REPO_ROOT / "config" / "study.yaml"

ENDPOINT = "https://overpass-api.de/api/interpreter"
UA = "tete-moatize-estudo/1.0 (pesquisa academica; contato via repositorio)"

# Folga em graus para não cortar rótulo nem geometria na borda da AOI.
FOLGA = 0.05

# Cada camada declara o corpo Overpass (sem o bbox, que é injetado) e o tipo de saída.
CAMADAS: dict[str, dict] = {
    "osm_lugares_aoi": {
        "descricao": "Topônimos: cidade, vila, povoado, bairro",
        "corpo": """
          node["place"~"^(city|town|village|suburb|hamlet|neighbourhood)$"]({bbox});
          way["place"~"^(city|town|village|suburb|hamlet|neighbourhood)$"]({bbox});
        """,
    },
    "osm_vias_aoi": {
        "descricao": "Malha rodoviária estruturante (inclui a N7, eixo Tete-Moatize)",
        "corpo": """
          way["highway"~"^(motorway|trunk|primary|secondary|tertiary)$"]({bbox});
        """,
    },
    "osm_ferrovia_aoi": {
        "descricao": "Malha ferroviária (linha do Sena)",
        "corpo": """
          way["railway"~"^(rail|light_rail|narrow_gauge)$"]({bbox});
        """,
    },
    "osm_aerodromo_aoi": {
        "descricao": (
            "Aeródromo de Tete (Chingodzi) e pistas. Infraestrutura de conexão do "
            "enclave minerário — relevante à leitura de §1, pergunta 5"
        ),
        "corpo": """
          node["aeroway"="aerodrome"]({bbox});
          way["aeroway"="aerodrome"]({bbox});
          relation["aeroway"="aerodrome"]({bbox});
          way["aeroway"="runway"]({bbox});
        """,
    },
}


def bbox_aoi() -> str:
    """Overpass usa (sul, oeste, norte, leste) — ordem diferente da do GeoJSON."""
    cfg = yaml.safe_load(CONFIG.read_text(encoding="utf-8"))
    b = cfg["aoi"]["bbox"]
    return (
        f"{b['ymin'] - FOLGA},{b['xmin'] - FOLGA},"
        f"{b['ymax'] + FOLGA},{b['xmax'] + FOLGA}"
    )


def consulta(camada: str, bbox: str) -> str:
    corpo = CAMADAS[camada]["corpo"].format(bbox=bbox).strip()
    return f"[out:json][timeout:180];\n(\n{corpo}\n);\nout geom;"


def overpass(ql: str) -> dict:
    cmd = [
        "curl", "-sS", "--fail",
        "-H", f"User-Agent: {UA}",
        "--connect-timeout", "30",
        # PARADO, não lento (mesma lição de docs/ADR/0014 e do log 3-07): 5 KB/s por
        # 120 s é conexão morta; uma conexão viva e lenta sobrevive.
        "--speed-limit", "5120", "--speed-time", "120",
        "--retry", "3", "--retry-delay", "20",
        "--data-urlencode", f"data={ql}",
        ENDPOINT,
    ]
    r = subprocess.run(cmd, capture_output=True, text=True, timeout=600, check=False)
    if r.returncode != 0:
        raise RuntimeError(f"Overpass falhou (curl {r.returncode}): {r.stderr[:300]}")
    return json.loads(r.stdout)


def para_geojson(dados: dict) -> dict:
    """Converte a resposta Overpass em GeoJSON RFC 7946.

    **Sem membro `crs`**: o padrão exige WGS84 e um `crs` declarado faz várias
    bibliotecas — o MapLibre entre elas — lerem as coordenadas como cruas, o que
    renderiza o mapa vazio sem levantar erro.
    """
    feats = []
    for el in dados.get("elements", []):
        props = {k: v for k, v in (el.get("tags") or {}).items()}
        props["osm_id"] = el.get("id")
        props["osm_type"] = el.get("type")

        if el["type"] == "node":
            geom = {"type": "Point", "coordinates": [el["lon"], el["lat"]]}
        elif el.get("geometry"):
            coords = [[p["lon"], p["lat"]] for p in el["geometry"]]
            if len(coords) >= 4 and coords[0] == coords[-1]:
                geom = {"type": "Polygon", "coordinates": [coords]}
            else:
                geom = {"type": "LineString", "coordinates": coords}
        else:
            continue
        feats.append({"type": "Feature", "properties": props, "geometry": geom})
    return {"type": "FeatureCollection", "features": feats}


def sha256_de(p: Path) -> str:
    h = hashlib.sha256()
    with p.open("rb") as fh:
        for bloco in iter(lambda: fh.read(1 << 20), b""):
            h.update(bloco)
    return h.hexdigest()


def gravar(camada: str, gj: dict, ql: str) -> int:
    RAW.mkdir(parents=True, exist_ok=True)
    out = RAW / f"{camada}.geojson"
    out.write_text(json.dumps(gj, ensure_ascii=False), encoding="utf-8")

    (RAW / f"{camada}.geojson.sha256").write_text(
        f"{sha256_de(out)}  {out.name}\n", encoding="utf-8"
    )
    meta = {
        "fonte": "OpenStreetMap via Overpass API",
        "url": ENDPOINT,
        "descricao": CAMADAS[camada]["descricao"],
        "licenca_observada": "ODbL 1.0",
        "atribuicao_exigida": "© OpenStreetMap contributors",
        "consulta_overpass": ql,
        "download_date": datetime.now(UTC).isoformat(timespec="seconds"),
        "n_features": len(gj["features"]),
        "crs": "EPSG:4326 (RFC 7946, sem membro crs declarado)",
        "selo": "contexto",
        "nota": (
            "Camada de contexto para leitura do mapa. NAO sustenta numero publicado; "
            "classificacao de nivel A/B/C cabe ao auditor-dados."
        ),
    }
    (RAW / f"{camada}.geojson.meta.json").write_text(
        json.dumps(meta, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    return len(gj["features"])


def main() -> int:
    alvos = sys.argv[1:] or list(CAMADAS)
    desconhecidas = [a for a in alvos if a not in CAMADAS]
    if desconhecidas:
        print(f"camada desconhecida: {desconhecidas}", file=sys.stderr)
        return 1

    bbox = bbox_aoi()
    for i, camada in enumerate(alvos):
        completo = all(
            (RAW / f"{camada}.geojson{suf}").exists()
            for suf in ("", ".sha256", ".meta.json")
        )
        if completo:
            print(f"[osm] {camada}: já espelhado, pulando")
            continue
        if i:
            time.sleep(5)  # etiqueta da Overpass: uma consulta por vez, com pausa
        ql = consulta(camada, bbox)
        print(f"[osm] {camada}: consultando ...")
        try:
            gj = para_geojson(overpass(ql))
        except Exception as e:
            print(f"[osm] FALHA em {camada}: {e}", file=sys.stderr)
            return 1
        n = gravar(camada, gj, ql)
        print(f"[osm] {camada}: {n} feições")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
