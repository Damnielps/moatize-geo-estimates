"""Contrato de transparência metodológica (CLAUDE.md §6-A, decisão do usuário 2026-09-08).

O app e o artigo têm de apresentar metodologia detalhada E processo de implementação,
incluindo bibliotecas com versão exata. A exigência tem um modo de falha específico e
previsível: **um agente escreve a lista de versões à mão**, ela fica plausível, e ninguém
confere. Esta sessão já produziu essa classe de erro várias vezes — DOI inexistente,
coordenadas fabricadas, contagem de cenas não medida, P-code afirmado sem abrir o arquivo.
Uma lista de dependências redigida em vez de gerada é o mesmo defeito com outra roupa.

Por que este contrato existe ANTES dos artefatos: o defeito recorrente desta sessão é
escopar a verificação aos artefatos onde o problema já apareceu, em vez da classe onde ele
pode aparecer (ORCHESTRATION_LOG.md 2-10, docs/ADR/0014). Enquanto as Fases 4 e 5 não
produzirem seus artefatos, os testes passam por vacuidade — e passam a morder no instante
em que o arquivo aparece, sem que ninguém precise lembrar de escrever o contrato depois.
"""
from __future__ import annotations

import re
import tomllib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]

# Artefatos de metodologia que as Fases 4 e 5 vão produzir. Ainda não existem.
PAGINA_METODO_APP = ROOT / "app" / "src" / "content" / "metodologia.json"
APENDICE_ARTIGO = ROOT / "paper" / "apendice_reprodutibilidade.md"

# Bibliotecas cuja versão condiciona a leitura de um resultado geoespacial. Se o texto
# nomeia uma delas, tem de dar a versão — "usamos rasterio" não é método reproduzível.
BIBLIOTECAS_CRITICAS = [
    "rasterio",
    "odc-stac",
    "pystac-client",
    "scikit-learn",
    "numpy",
    "pandas",
    "pylandstats",
    "geopandas",
    "shapely",
]

# Decisões que mudaram a resposta do estudo. §6-A.5 exige que apareçam, não que sejam
# apêndice. A ausência de qualquer uma num texto de método é omissão material.
ADRS_QUE_MUDARAM_A_RESPOSTA = ["0008", "0009", "0011", "0012", "0013", "0014"]


def _texto(caminho: Path) -> str:
    return caminho.read_text(encoding="utf-8") if caminho.exists() else ""


def _versoes_do_lockfile() -> dict[str, str]:
    """Fonte de verdade das versões: uv.lock. Nunca o texto de um agente."""
    lock = ROOT / "uv.lock"
    if not lock.exists():
        return {}
    dados = tomllib.loads(lock.read_text(encoding="utf-8"))
    return {
        p["name"].lower(): p["version"]
        for p in dados.get("package", [])
        if "name" in p and "version" in p
    }


def test_lockfile_existe_e_e_legivel():
    """Sem lockfile, nenhuma alegação de versão é verificável — nem para conferir."""
    versoes = _versoes_do_lockfile()
    assert versoes, "uv.lock ausente ou sem pacotes: §6-A.2 não é verificável"
    faltando = [b for b in BIBLIOTECAS_CRITICAS if b.replace("-", "_") not in
                {k.replace("-", "_") for k in versoes}]
    assert not faltando, (
        f"bibliotecas críticas fora do lockfile: {faltando}. "
        "Ou o ambiente mudou, ou a lista de §6-A.2 precisa ser revista — "
        "as duas coisas exigem decisão, não ajuste silencioso do contrato."
    )


def test_versoes_declaradas_batem_com_o_lockfile():
    """O modo de falha alvo: versão plausível, escrita à mão, divergente do ambiente real.

    Não exige que o texto cite todas as bibliotecas — exige que toda versão que ele
    afirmar seja a verdadeira. Uma alegação errada é pior que uma alegação ausente.
    """
    versoes = _versoes_do_lockfile()
    if not versoes:
        return

    for artefato in (PAGINA_METODO_APP, APENDICE_ARTIGO):
        texto = _texto(artefato)
        if not texto:
            continue  # a fase ainda não rodou; o contrato morde quando o arquivo existir

        divergentes: list[str] = []
        for lib in BIBLIOTECAS_CRITICAS:
            padrao = re.compile(
                rf"\b{re.escape(lib)}\b[^\n]{{0,40}}?(\d+\.\d+(?:\.\d+)?)", re.I
            )
            real = versoes.get(lib.lower()) or versoes.get(lib.lower().replace("-", "_"))
            for m in padrao.finditer(texto):
                afirmada = m.group(1)
                if real and not real.startswith(afirmada) and not afirmada.startswith(real):
                    divergentes.append(f"{lib}: texto diz {afirmada}, uv.lock diz {real}")

        assert not divergentes, (
            f"{artefato.relative_to(ROOT)} afirma versões que não são as do ambiente:\n  "
            + "\n  ".join(divergentes)
            + "\nA lista tem de ser GERADA de uv.lock (§6-A.2), não redigida."
        )


def test_metodo_cobre_as_decisoes_que_mudaram_a_resposta():
    """§6-A.5: os ADRs que mudaram a resposta do estudo não são apêndice opcional.

    0008 tirou a série própria do papel de série de tendência; 0011 tornou H3 testável;
    0012 recusou uma camada; 0013 restringiu o que a Fase 3 pode estimar. Um texto de
    método que os omite descreve um estudo que não foi o que aconteceu.
    """
    for artefato in (PAGINA_METODO_APP, APENDICE_ARTIGO):
        texto = _texto(artefato)
        if not texto:
            continue

        ausentes = [n for n in ADRS_QUE_MUDARAM_A_RESPOSTA if n not in texto]
        assert not ausentes, (
            f"{artefato.relative_to(ROOT)} não menciona os ADR {ausentes}, "
            "que mudaram a resposta do estudo (§6-A.5)."
        )


def test_pagina_de_metodologia_do_app_nao_e_escrita_a_mao():
    """§6 e §6-A: a página de metodologia é GERADA de PROVENANCE.md, DATA_AUDIT.md e uv.lock.

    Um JSON de conteúdo sem o carimbo de qual script o gerou é indistinguível de um JSON
    digitado — e a diferença é justamente o que §6-A quer garantir.
    """
    if not PAGINA_METODO_APP.exists():
        return

    texto = _texto(PAGINA_METODO_APP)
    assert re.search(r"gerado_por|generated_by|script_origem", texto, re.I), (
        f"{PAGINA_METODO_APP.relative_to(ROOT)} não declara o script que o gerou. "
        "§6 manda gerar de PROVENANCE.md e data/DATA_AUDIT.md; sem o carimbo de origem "
        "não há como distinguir gerado de digitado."
    )


def test_exigencia_esta_escrita_onde_os_agentes_das_fases_4_e_5_leem():
    """A exigência do usuário só vale se estiver em CLAUDE.md, que todo subagente carrega.

    Registrada apenas na conversa, ela se perde na próxima compactação de contexto — que
    é exatamente como o fechamento de custo da Fase 2b se perdeu (BUDGET.md).
    """
    claude_md = _texto(ROOT / "CLAUDE.md")
    assert "6-A" in claude_md and "TRANSPARÊNCIA METODOLÓGICA" in claude_md, (
        "CLAUDE.md não carrega §6-A: a exigência de metodologia detalhada não chegaria "
        "aos agentes das Fases 4 e 5."
    )
    for termo in ("uv.lock", "bibliotecas", "implementação"):
        assert termo in claude_md, f"§6-A não menciona {termo!r}"
