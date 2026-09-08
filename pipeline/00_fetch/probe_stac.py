#!/usr/bin/env python3
"""probe_stac.py — Teste de disponibilidade de imagens via STAC.

Fase 0' (reexecução em T2): mede a disponibilidade real de cenas Landsat
Collection 2 L2 e Sentinel-2 L2A na AOI e na janela de estação seca do
estudo, consultando os DOIS endpoints STAC candidatos a rota alternativa
sem GEE (§11.3 do CLAUDE.md): Planetary Computer e Element84 Earth Search.

Requisitos atendidos (correção dos defeitos de T1):
  1. Contagem via `numberMatched`/`context.matched` quando o servidor
     fornece; quando não fornece (caso do Planetary Computer), pagina via
     `links[] | rel == "next"` até esgotar, somando `numberReturned`.
  2. Os dois endpoints são de fato consultados via HTTP — nenhum resultado
     é gravado sem medição.
  3. Janela temporal do mês final calculada com o último dia real do mês
     (via `calendar.monthrange`), não hardcoded em "-30".
  4. Idempotente: reescreve o CSV inteiro a cada execução, mesmo esquema.
  5. Falha explícita: se um endpoint não responde (timeout, HTTP != 200,
     JSON inválido), grava uma linha de status "erro" com a mensagem real
     — nunca inventa uma contagem.

Parâmetros lidos de config/study.yaml: aoi.bbox, anos_ancora.imagem,
composto.estacao_seca, composto.nuvem_max_pct. Nada é hardcoded aqui além
dos endpoints e das coleções STAC (que são identificadores fixos das
plataformas, não parâmetros do estudo).
"""

from __future__ import annotations

import calendar
import csv
import sys
from datetime import UTC, datetime
from pathlib import Path

import requests
import yaml

REPO_ROOT = Path(__file__).resolve().parents[2]
STUDY_YAML = REPO_ROOT / "config" / "study.yaml"
DEFAULT_OUTPUT = REPO_ROOT / "data" / "interim" / "stac_disponibilidade.csv"

TIMEOUT_S = 30
MAX_PAGES = 50  # salvaguarda contra paginação infinita por bug de servidor
PAGE_LIMIT = 250  # itens por página ao paginar manualmente

ENDPOINTS = {
    "Planetary Computer": "https://planetarycomputer.microsoft.com/api/stac/v1/search",
    "Element84 Earth Search": "https://earth-search.aws.element84.com/v1/search",
}

COLECOES = {
    "landsat-c2-l2": {"ano_min": None},  # todos os anos-âncora testados
    "sentinel-2-l2a": {"ano_min": 2015},  # dado só existe a partir de dez/2015
}

CSV_FIELDS = [
    "ano",
    "plataforma",
    "endpoint",
    "colecao",
    "n_cenas",
    "metodo_contagem",
    "nuvem_max_pct",
    "janela_inicio",
    "janela_fim",
    "status",
    "data_consulta",
    "nota",
]


def carregar_config(path: Path) -> dict:
    with open(path, encoding="utf-8") as f:
        return yaml.safe_load(f)


def janela_estacao_seca(ano: int, mes_inicio: int, mes_fim: int) -> tuple[str, str]:
    """Retorna (inicio, fim) ISO-8601 UTC cobrindo o mês final por inteiro."""
    ultimo_dia = calendar.monthrange(ano, mes_fim)[1]
    inicio = f"{ano}-{mes_inicio:02d}-01T00:00:00Z"
    fim = f"{ano}-{mes_fim:02d}-{ultimo_dia:02d}T23:59:59Z"
    return inicio, fim


def consultar_pagina(endpoint: str, body: dict) -> dict:
    resp = requests.post(endpoint, json=body, timeout=TIMEOUT_S)
    resp.raise_for_status()
    return resp.json()


def contar_cenas(endpoint: str, colecao: str, bbox: list, inicio: str, fim: str, nuvem_max: int):
    """Retorna (n_cenas, metodo, nota) ou levanta exceção com a causa real."""
    body = {
        "collections": [colecao],
        "bbox": bbox,
        "datetime": f"{inicio}/{fim}",
        "query": {"eo:cloud_cover": {"lte": nuvem_max}},
        "limit": PAGE_LIMIT,
    }
    data = consultar_pagina(endpoint, body)

    n_matched = data.get("numberMatched")
    if n_matched is None:
        ctx = data.get("context") or {}
        n_matched = ctx.get("matched")

    if n_matched is not None:
        return int(n_matched), "numberMatched/context.matched", ""

    # Servidor não fornece contagem total: paginar e somar numberReturned.
    total = len(data.get("features", []))
    paginas = 1
    proximo = None
    for link in data.get("links", []):
        if link.get("rel") == "next":
            proximo = link
            break

    while proximo is not None and paginas < MAX_PAGES:
        method = proximo.get("method", "GET").upper()
        href = proximo["href"]
        if method == "POST":
            data = consultar_pagina(href, proximo.get("body", {}))
        else:
            resp = requests.get(href, timeout=TIMEOUT_S)
            resp.raise_for_status()
            data = resp.json()
        total += len(data.get("features", []))
        paginas += 1
        proximo = None
        for link in data.get("links", []):
            if link.get("rel") == "next":
                proximo = link
                break

    nota = f"paginado manualmente ({paginas} página(s) de até {PAGE_LIMIT})"
    if paginas >= MAX_PAGES and proximo is not None:
        nota += " — ATENÇÃO: MAX_PAGES atingido, contagem pode estar incompleta"
    return total, "paginação manual (numberReturned somado)", nota


def main() -> int:
    output_csv = Path(sys.argv[1]) if len(sys.argv) > 1 else DEFAULT_OUTPUT
    output_csv.parent.mkdir(parents=True, exist_ok=True)

    cfg = carregar_config(STUDY_YAML)
    bbox_cfg = cfg["aoi"]["bbox"]
    bbox = [bbox_cfg["xmin"], bbox_cfg["ymin"], bbox_cfg["xmax"], bbox_cfg["ymax"]]
    anos = cfg["anos_ancora"]["imagem"]
    mes_inicio = cfg["composto"]["estacao_seca"]["mes_inicio"]
    mes_fim = cfg["composto"]["estacao_seca"]["mes_fim"]
    nuvem_max = cfg["composto"]["nuvem_max_pct"]

    data_consulta = datetime.now(UTC).strftime("%Y-%m-%d")

    rows = []
    for ano in anos:
        inicio, fim = janela_estacao_seca(ano, mes_inicio, mes_fim)
        for colecao, regras in COLECOES.items():
            ano_min = regras["ano_min"]
            if ano_min is not None and ano < ano_min:
                for plataforma, endpoint in ENDPOINTS.items():
                    rows.append(
                        {
                            "ano": ano,
                            "plataforma": plataforma,
                            "endpoint": endpoint,
                            "colecao": colecao,
                            "n_cenas": "",
                            "metodo_contagem": "não_aplicável",
                            "nuvem_max_pct": nuvem_max,
                            "janela_inicio": inicio,
                            "janela_fim": fim,
                            "status": "não_aplicável",
                            "data_consulta": data_consulta,
                            "nota": f"coleção {colecao} não existe antes de {ano_min}",
                        }
                    )
                continue

            for plataforma, endpoint in ENDPOINTS.items():
                row = {
                    "ano": ano,
                    "plataforma": plataforma,
                    "endpoint": endpoint,
                    "colecao": colecao,
                    "nuvem_max_pct": nuvem_max,
                    "janela_inicio": inicio,
                    "janela_fim": fim,
                    "data_consulta": data_consulta,
                }
                try:
                    n_cenas, metodo, nota = contar_cenas(
                        endpoint, colecao, bbox, inicio, fim, nuvem_max
                    )
                    row.update(
                        {
                            "n_cenas": n_cenas,
                            "metodo_contagem": metodo,
                            "status": "ok",
                            "nota": nota,
                        }
                    )
                    print(
                        f"[ok] {ano} {plataforma} {colecao}: {n_cenas} cenas "
                        f"({metodo})",
                        file=sys.stderr,
                    )
                except requests.exceptions.RequestException as exc:
                    status_code = getattr(getattr(exc, "response", None), "status_code", None)
                    row.update(
                        {
                            "n_cenas": "",
                            "metodo_contagem": "não_medido",
                            "status": "erro",
                            "nota": f"HTTP {status_code}: {exc}" if status_code else str(exc),
                        }
                    )
                    print(f"[erro] {ano} {plataforma} {colecao}: {exc}", file=sys.stderr)
                except (ValueError, KeyError) as exc:
                    row.update(
                        {
                            "n_cenas": "",
                            "metodo_contagem": "não_medido",
                            "status": "erro",
                            "nota": f"resposta inesperada: {exc}",
                        }
                    )
                    print(f"[erro] {ano} {plataforma} {colecao}: {exc}", file=sys.stderr)
                rows.append(row)

    with open(output_csv, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=CSV_FIELDS)
        writer.writeheader()
        for row in rows:
            writer.writerow(row)

    print(f"CSV gravado: {output_csv}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
