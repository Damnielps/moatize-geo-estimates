#!/usr/bin/env python3
"""Consolida `data/processed/stats_by_year_by_unit.csv` a partir dos fragmentos por família.

Propósito (§9 nomeia este CSV como artefato da Fase 2): as famílias de métrica — forma
urbana (§5.2) e demografia (§5.3) — são produzidas por módulos distintos, e na primeira
execução ambos gravavam o arquivo final em modo `"w"`. O último a rodar apagava o outro:
o arquivo ficou com 14 linhas só de `familia=demografia`, sem nenhuma métrica de forma
urbana. Ver ORCHESTRATION_LOG.md 2-01.

Cada módulo passa a gravar `data/interim/stats_<familia>.csv`; este script monta o
canônico. É o mesmo padrão de `scripts/consolidar_registros.py`, que resolve a mesma
colisão para `LICENSES.md` e `PROVENANCE.md`.

Entradas: data/interim/stats_*.csv
Saída:    data/processed/stats_by_year_by_unit.csv
Determinístico: ordena por família, unidade, variável e ano; nenhuma dependência de
ordem de execução dos módulos.
"""
from __future__ import annotations

import csv
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
INTERIM = REPO_ROOT / "data" / "interim"
SAIDA = REPO_ROOT / "data" / "processed" / "stats_by_year_by_unit.csv"

COLUNAS = [
    "familia",
    "unidade_geografica",
    "ano",
    "variavel",
    "valor",
    "unidade_medida",
    "selo",
    "nivel_fonte",
    "fonte",
    "metodo",
    "nota",
]

# Famílias que a Fase 2 tem de entregar. A ausência de qualquer uma é erro, não omissão
# tolerável: significa que um módulo não rodou ou que o fragmento foi perdido.
FAMILIAS_ESPERADAS = {"forma_urbana", "demografia"}

SELOS_VALIDOS = {"observado", "interpolado", "modelado"}


def ler_fragmentos() -> list[dict]:
    linhas: list[dict] = []
    fragmentos = sorted(INTERIM.glob("stats_*.csv"))
    if not fragmentos:
        print(f"nenhum fragmento em {INTERIM.relative_to(REPO_ROOT)}", file=sys.stderr)
        return linhas

    for fragmento in fragmentos:
        with fragmento.open(encoding="utf-8", newline="") as fh:
            for linha in csv.DictReader(fh):
                faltando = [c for c in COLUNAS if c not in linha]
                if faltando:
                    raise ValueError(f"{fragmento.name}: colunas ausentes {faltando}")
                linhas.append({c: (linha.get(c) or "") for c in COLUNAS})
        print(f"  lido {fragmento.name}")
    return linhas


def ordenar(linhas: list[dict]) -> list[dict]:
    def chave(x: dict) -> tuple:
        try:
            ano = int(x["ano"])
        except (ValueError, TypeError):
            ano = -1
        return (x["familia"], x["unidade_geografica"], x["variavel"], ano)

    return sorted(linhas, key=chave)


def validar(linhas: list[dict]) -> list[str]:
    """Erros que impedem publicar o CSV. Não conserta nada — só relata."""
    problemas: list[str] = []

    familias = {x["familia"] for x in linhas}
    ausentes = FAMILIAS_ESPERADAS - familias
    if ausentes:
        problemas.append(
            f"famílias ausentes: {sorted(ausentes)} — algum módulo não gravou seu fragmento"
        )

    for x in linhas:
        if x["selo"] not in SELOS_VALIDOS:
            problemas.append(
                f"{x['familia']}/{x['unidade_geografica']}/{x['variavel']}/{x['ano']}: "
                f"selo {x['selo']!r} fora de {sorted(SELOS_VALIDOS)}"
            )
        if x["nivel_fonte"] not in {"A", "B", "C"}:
            problemas.append(
                f"{x['familia']}/{x['variavel']}/{x['ano']}: "
                f"nivel_fonte {x['nivel_fonte']!r} inválido"
            )
        # §4.0: só nível A sustenta número publicado. B e C vivem em arquivo de contexto,
        # nunca no CSV de núcleo que alimenta app e artigo.
        if x["nivel_fonte"] in {"B", "C"}:
            problemas.append(
                f"{x['familia']}/{x['variavel']}/{x['ano']}: nível {x['nivel_fonte']} "
                "no CSV de núcleo — mova para o arquivo de contexto"
            )

    # Uma mesma célula não pode vir de dois fragmentos com valores diferentes.
    vistos: dict[tuple, str] = {}
    for x in linhas:
        k = (x["familia"], x["unidade_geografica"], x["ano"], x["variavel"])
        if k in vistos and vistos[k] != x["valor"]:
            problemas.append(f"{k}: valor duplicado e divergente ({vistos[k]} × {x['valor']})")
        vistos[k] = x["valor"]

    return problemas


def main() -> int:
    linhas = ler_fragmentos()
    if not linhas:
        return 1

    problemas = validar(linhas)
    if problemas:
        for p in problemas:
            print(f"ERRO: {p}", file=sys.stderr)
        return 1

    linhas = ordenar(linhas)
    SAIDA.parent.mkdir(parents=True, exist_ok=True)
    with SAIDA.open("w", newline="", encoding="utf-8") as fh:
        escritor = csv.DictWriter(fh, fieldnames=COLUNAS)
        escritor.writeheader()
        escritor.writerows(linhas)

    familias = sorted({x["familia"] for x in linhas})
    print(f"[ok] {SAIDA.relative_to(REPO_ROOT)}: {len(linhas)} linhas, famílias {familias}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
