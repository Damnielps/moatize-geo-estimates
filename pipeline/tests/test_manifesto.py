"""Contrato do manifesto de `data/processed/` (ORCHESTRATION_LOG.md 3-14).

Lacuna achada pelo portão da Fase 3, e não coberta por nenhum contrato anterior:
`data/raw/` tem um `.sha256` por arquivo desde a Fase 0'; `data/processed/` não tinha
nada. O critério de §10 exige reprodução "byte a byte ou dentro de tolerância declarada",
mas o repositório não registrava quais bytes eram os publicados.

O sintoma que denunciou a lacuna foi benigno — o `mtime` de `placebos.csv` mudou sem o
conteúdo mudar, por causa da verificação por reintrodução do próprio orquestrador. A
lacuna não é benigna: entre um fechamento de fase e o seguinte, qualquer reescrita
silenciosa de artefato publicado passava sem rastro, e é justamente `data/processed/` que
alimenta o app e o artigo.

Este contrato **não** exige que o pipeline seja determinístico a ponto de reproduzir hashes
— isso é o critério de §10 e tem tolerância declarada. Exige que o conjunto publicado seja
o conjunto registrado: nada some, nada aparece, nada muda sem que alguém decida.
"""
from __future__ import annotations

import importlib.util
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "scripts" / "manifesto_processed.py"
MANIFESTO = ROOT / "data" / "processed" / "MANIFESTO.sha256"


def _modulo():
    spec = importlib.util.spec_from_file_location("manifesto_processed", SCRIPT)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def test_script_do_manifesto_existe():
    assert SCRIPT.exists(), (
        "scripts/manifesto_processed.py ausente: sem ele não há registro de quais bytes "
        "são os publicados em data/processed/"
    )


def test_manifesto_cobre_o_que_esta_publicado():
    """Nada some, nada aparece e nada muda em data/processed/ sem ato deliberado."""
    if not MANIFESTO.exists():
        pytest.skip("manifesto ainda não gerado (rode com --gravar no fechamento de fase)")

    mod = _modulo()
    problemas = mod.comparar(mod.calcular(), mod.ler_manifesto())
    assert not problemas, (
        "data/processed/ diverge do manifesto:\n  "
        + "\n  ".join(problemas)
        + "\n\nSe a mudança é legítima (a fase regenerou o artefato), regrave o manifesto "
        "com `uv run python scripts/manifesto_processed.py --gravar`. Se não é, alguém "
        "reescreveu artefato publicado sem registrar."
    )


def test_manifesto_nao_lista_a_si_mesmo():
    """Auto-referência tornaria o manifesto impossível de regravar de forma estável."""
    if not MANIFESTO.exists():
        pytest.skip("manifesto ainda não gerado")
    gravado = _modulo().ler_manifesto()
    assert "MANIFESTO.sha256" not in gravado, "o manifesto lista a si mesmo"
