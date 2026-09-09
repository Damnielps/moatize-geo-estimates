#!/usr/bin/env python3
"""Gera `data/processed/MANIFESTO.sha256`: o hash de cada artefato publicado.

Motivo (ORCHESTRATION_LOG.md 3-14, achado pelo portão da Fase 3). `data/raw/` tem um
`.sha256` por arquivo desde a Fase 0'; `data/processed/` **não tinha nada**. O critério de
§10 exige que o pipeline reproduza os artefatos publicados "byte a byte ou dentro de
tolerância declarada" — mas nada no repositório registrava quais bytes eram esperados.

O portão notou o sintoma: o `mtime` de `placebos.csv` mudou sem o conteúdo mudar, e
nenhum contrato saberia dizer se o conteúdo tivesse mudado. A causa foi benigna (a
verificação por reintrodução do orquestrador, que altera e restaura o arquivo), mas a
lacuna não é: entre um fechamento de fase e o seguinte, qualquer reescrita silenciosa de
artefato publicado passava sem deixar rastro.

Uso:
    uv run python scripts/manifesto_processed.py          # confere
    uv run python scripts/manifesto_processed.py --gravar # regrava (ato deliberado)

Regravar é ato de fechamento de fase, não rotina: o manifesto só muda quando alguém
decide que o novo conteúdo é o publicado.
"""
from __future__ import annotations

import hashlib
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
PROCESSED = REPO_ROOT / "data" / "processed"
MANIFESTO = PROCESSED / "MANIFESTO.sha256"

# Extensões versionadas. Rasters (.tif) ficam de fora por tamanho — eles já são cobertos
# pelo contrato de frescor e pelas métricas derivadas, e entrariam com centenas de MB.
EXTENSOES = {".csv", ".geojson", ".json", ".md", ".parquet"}


def sha256_de(caminho: Path) -> str:
    h = hashlib.sha256()
    with caminho.open("rb") as fh:
        for bloco in iter(lambda: fh.read(1 << 20), b""):
            h.update(bloco)
    return h.hexdigest()


def artefatos() -> list[Path]:
    if not PROCESSED.exists():
        return []
    return sorted(
        p for p in PROCESSED.rglob("*")
        if p.is_file() and p.suffix in EXTENSOES and p != MANIFESTO
    )


def calcular() -> dict[str, str]:
    return {str(p.relative_to(PROCESSED)): sha256_de(p) for p in artefatos()}


def ler_manifesto() -> dict[str, str]:
    if not MANIFESTO.exists():
        return {}
    saida = {}
    for linha in MANIFESTO.read_text(encoding="utf-8").splitlines():
        linha = linha.strip()
        if not linha or linha.startswith("#"):
            continue
        h, _, nome = linha.partition("  ")
        if h and nome:
            saida[nome] = h
    return saida


def gravar(atual: dict[str, str]) -> None:
    linhas = [
        "# Hash dos artefatos publicados em data/processed/.",
        "# Gerado por scripts/manifesto_processed.py --gravar, no fechamento de fase.",
        "# Contrato: pipeline/tests/test_manifesto.py",
        "",
    ]
    linhas += [f"{h}  {nome}" for nome, h in sorted(atual.items())]
    MANIFESTO.write_text("\n".join(linhas) + "\n", encoding="utf-8")


def comparar(atual: dict[str, str], gravado: dict[str, str]) -> list[str]:
    problemas = []
    for nome, h in sorted(gravado.items()):
        if nome not in atual:
            problemas.append(f"{nome}: no manifesto, ausente do disco")
        elif atual[nome] != h:
            problemas.append(
                f"{nome}: conteúdo mudou sem o manifesto ser regravado "
                f"({h[:12]}… -> {atual[nome][:12]}…)"
            )
    for nome in sorted(atual):
        if nome not in gravado:
            problemas.append(f"{nome}: no disco, ausente do manifesto")
    return problemas


def main() -> int:
    atual = calcular()
    if not atual:
        print("nenhum artefato em data/processed/", file=sys.stderr)
        return 1

    if "--gravar" in sys.argv:
        gravar(atual)
        print(f"[ok] {MANIFESTO.relative_to(REPO_ROOT)}: {len(atual)} artefatos")
        return 0

    problemas = comparar(atual, ler_manifesto())
    if not ler_manifesto():
        print("manifesto ausente — rode com --gravar", file=sys.stderr)
        return 1
    for p in problemas:
        print(f"DIVERGE: {p}", file=sys.stderr)
    print(f"{len(atual)} artefatos, {len(problemas)} divergências")
    return 1 if problemas else 0


if __name__ == "__main__":
    raise SystemExit(main())
