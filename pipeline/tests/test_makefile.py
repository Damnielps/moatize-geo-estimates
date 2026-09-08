"""Contratos sobre o grafo de reprodução (§10, §11.2).

§10 exige que `make all` reexecute o pipeline em ambiente limpo sem intervenção manual.
Defeito real, pego pelo portão da Fase 2: o alvo `metrics` continuou sendo um stub com
`exit 1` depois de a fase inteira ser entregue, e nenhum dos sete scripts de
`pipeline/02_metrics/` estava no Makefile. Os artefatos existiam apenas porque foram
rodados à mão, fora do grafo declarado. Ver ORCHESTRATION_LOG.md 2-05.
"""
from __future__ import annotations

import re
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
MAKEFILE = ROOT / "Makefile"

# Diretório de scripts → alvo do Makefile que deve executá-los.
ETAPAS = {
    "pipeline/00_fetch": "fetch",
    "pipeline/01_imagery": "imagery",
    "pipeline/02_metrics": "metrics",
    "pipeline/03_causal": "causal",
    "pipeline/04_figures": "figures",
}

def e_auxiliar(nome: str) -> bool:
    """Módulo importado por outros, não executável isoladamente.

    Convenção do repositório: prefixo `_`. Melhor que uma lista à mão, que fica
    desatualizada — foi o que aconteceu com `_paleta_ardosia.py`.
    """
    return nome.startswith("_") or nome.startswith("test_")


@pytest.fixture(scope="module")
def makefile() -> str:
    return MAKEFILE.read_text(encoding="utf-8")


def bloco_do_alvo(texto: str, alvo: str) -> str:
    """Devolve as linhas de receita do alvo (linhas iniciadas por TAB)."""
    m = re.search(rf"^{re.escape(alvo)}:.*?$", texto, re.M)
    if not m:
        return ""
    resto = texto[m.end():]
    linhas = []
    for linha in resto.splitlines()[1:]:
        if linha.startswith("\t"):
            linhas.append(linha)
        elif linha.strip() and not linha.startswith("#"):
            break
    return "\n".join(linhas)


def test_alvo_nao_e_stub_se_a_etapa_tem_scripts(makefile):
    """Um alvo que sai com erro enquanto seus scripts existem mente sobre o estado.

    Enquanto a etapa não foi implementada, o stub é honesto — diz que não está pronta.
    Depois que os scripts existem, ele passa a esconder que o grafo não os executa.
    """
    problemas = []
    for diretorio, alvo in ETAPAS.items():
        caminho = ROOT / diretorio
        if not caminho.exists():
            continue
        scripts = [
            p.name for p in caminho.glob("*.py")
            if not e_auxiliar(p.name)
        ]
        if not scripts:
            continue  # etapa sem scripts: stub é legítimo

        receita = bloco_do_alvo(makefile, alvo)
        if "exit 1" in receita and "não implementado" in receita:
            problemas.append(
                f"alvo '{alvo}' ainda é stub, mas {diretorio} já tem "
                f"{len(scripts)} script(s): {sorted(scripts)[:4]}"
            )
    assert not problemas, "; ".join(problemas)


def test_todo_script_de_etapa_implementada_esta_no_grafo(makefile):
    """Script que existe mas não é chamado por nenhum alvo não é reproduzível.

    O artefato que ele produz só existe porque alguém o rodou à mão — e §10 exige o
    contrário.
    """
    problemas = []
    for diretorio, alvo in ETAPAS.items():
        caminho = ROOT / diretorio
        if not caminho.exists():
            continue
        receita = bloco_do_alvo(makefile, alvo)
        if "exit 1" in receita and "não implementado" in receita:
            continue  # etapa declaradamente não implementada; o outro contrato cobre

        for script in sorted(caminho.glob("*.py")):
            if e_auxiliar(script.name):
                continue
            # `fetch` roda o diretório inteiro em laço, não script a script.
            if alvo == "fetch" and ("00_fetch/*" in receita or "for s in" in receita):
                continue
            if script.name not in receita:
                problemas.append(f"{diretorio}/{script.name} não é chamado pelo alvo '{alvo}'")
    assert not problemas, "; ".join(problemas)


def test_all_depende_de_todas_as_etapas(makefile):
    """`make all` tem de percorrer o pipeline inteiro, não um subconjunto."""
    m = re.search(r"^all:([^\n#]*)", makefile, re.M)
    assert m, "Makefile não declara o alvo 'all'"
    deps = set(m.group(1).split())
    faltando = {"imagery", "metrics", "causal", "figures"} - deps
    assert not faltando, f"'all' não depende de: {sorted(faltando)}"
