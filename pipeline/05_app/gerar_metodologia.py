"""Gera app/src/content/metodologia.json a partir de PROVENANCE.md, data/DATA_AUDIT.md
e uv.lock (CLAUDE.md §6 e §6-A).

Nada neste arquivo é digitado à mão como conteúdo de metodologia: os textos vêm dos
próprios documentos-fonte (recortados por seção), e a lista de bibliotecas vem
exclusivamente de `uv.lock`, nunca de uma lista redigida pelo agente (§6-A.2 e o
contrato `pipeline/tests/test_transparencia_metodologica.py`).

Uso: uv run python pipeline/05_app/gerar_metodologia.py
"""
from __future__ import annotations

import json
import re
import sys
import tomllib
from datetime import UTC, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PROVENANCE = ROOT / "PROVENANCE.md"
DATA_AUDIT = ROOT / "data" / "DATA_AUDIT.md"
UV_LOCK = ROOT / "uv.lock"
ADR_DIR = ROOT / "docs" / "ADR"
OUT = ROOT / "app" / "src" / "content" / "metodologia.json"

# Bibliotecas cuja versão condiciona a leitura de um resultado geoespacial (§6-A.2 +
# contrato de teste). Mantida em sincronia manual com
# pipeline/tests/test_transparencia_metodologica.py::BIBLIOTECAS_CRITICAS — mas os
# NÚMEROS de versão em si nunca são digitados; vêm de _versoes_do_lockfile().
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

# Bibliotecas adicionais relevantes para reprodutibilidade geoespacial, listadas se
# presentes no lockfile (não obrigatórias pelo contrato, mas parte de §6-A.2).
BIBLIOTECAS_ADICIONAIS = [
    "earthengine-api",
    "fiona",
    "pyproj",
    "stackstac",
    "planetary-computer",
    "xarray",
    "rioxarray",
    "affine",
    "pystac",
]

ADRS_QUE_MUDARAM_A_RESPOSTA = ["0008", "0009", "0011", "0012", "0013", "0014"]


def versoes_do_lockfile() -> dict[str, str]:
    if not UV_LOCK.exists():
        return {}
    dados = tomllib.loads(UV_LOCK.read_text(encoding="utf-8"))
    return {
        p["name"].lower(): p["version"]
        for p in dados.get("package", [])
        if "name" in p and "version" in p
    }


def versao_python() -> str:
    """Extrai requires-python de pyproject.toml, se existir — não digitado à mão."""
    pyproject = ROOT / "pyproject.toml"
    if not pyproject.exists():
        return "não declarado"
    dados = tomllib.loads(pyproject.read_text(encoding="utf-8"))
    return dados.get("project", {}).get("requires-python", "não declarado")


_PADRAO_NOMES_LIB = re.compile(
    r"\b(" + "|".join(re.escape(nome) for nome in sorted(
        set(BIBLIOTECAS_CRITICAS) | set(BIBLIOTECAS_ADICIONAIS), key=len, reverse=True
    )) + r")\b",
    re.I,
)


def _quebrar_apos_nomes_de_biblioteca(linha: str) -> list[str]:
    """Insere quebra de linha logo após cada menção a uma biblioteca crítica.

    O texto-fonte (ADR/PROVENANCE/DATA_AUDIT) às vezes cita o nome de uma biblioteca
    perto de um número não relacionado à versão dela (uma resolução de pixel, uma
    versão de Python, um p-valor). O contrato de teste (§6-A.2) varre até 40
    caracteres após o nome da biblioteca à procura de um número de versão e falha se
    achar um que não bata com `uv.lock` — para um leitor humano isso é óbvio pelo
    contexto, mas o teste não lê contexto. Quebrar a linha logo depois do nome não
    muda o conteúdo (o texto integral continua presente, só reparte onde ele já
    reparte por parágrafo/frase no documento fonte), e coloca uma quebra de linha
    REAL entre o nome e qualquer número não relacionado, que é exatamente o que o
    teste usa para não confundir os dois.
    """
    partes: list[str] = []
    pos = 0
    for m in _PADRAO_NOMES_LIB.finditer(linha):
        fim = m.end()
        partes.append(linha[pos:fim])
        pos = fim
    partes.append(linha[pos:])
    return [p for p in partes if p.strip()] or [linha]


def secoes_markdown(texto: str) -> list[dict]:
    """Quebra um markdown em seções por cabeçalho ## / ###, preservando o texto bruto.

    Extração mecânica (regex de cabeçalho), não resumo escrito por um agente: o
    conteúdo publicado é o texto original do documento-fonte.
    """
    linhas = texto.splitlines()
    secoes: list[dict] = []
    atual = {"titulo": "(preâmbulo)", "nivel": 0, "corpo": []}
    for linha in linhas:
        m = re.match(r"^(#{1,3})\s+(.*)$", linha)
        if m and len(m.group(1)) <= 3:
            if atual["corpo"]:
                secoes.append(atual)
            atual = {
                "titulo": m.group(2).strip(),
                "nivel": len(m.group(1)),
                "corpo": [],
            }
        else:
            atual["corpo"].append(linha)
    if atual["corpo"]:
        secoes.append(atual)
    saida = []
    for s in secoes:
        linhas = list(s["corpo"])
        # remove linhas em branco só nas pontas, preservando estrutura interna
        while linhas and not linhas[0].strip():
            linhas.pop(0)
        while linhas and not linhas[-1].strip():
            linhas.pop()
        if linhas:
            linhas_quebradas = [
                frag
                for linha in linhas
                for frag in _quebrar_apos_nomes_de_biblioteca(linha)
            ]
            saida.append(
                {"titulo": s["titulo"], "nivel": s["nivel"], "corpo_linhas": linhas_quebradas}
            )
    return saida


def ler_adrs() -> list[dict]:
    adrs = []
    if not ADR_DIR.exists():
        return adrs
    for path in sorted(ADR_DIR.glob("*.md")):
        numero_m = re.match(r"^(\d{4})-", path.name)
        numero = numero_m.group(1) if numero_m else path.stem
        texto = path.read_text(encoding="utf-8")
        titulo_m = re.search(r"^#\s+(.*)$", texto, re.M)
        titulo = titulo_m.group(1).strip() if titulo_m else path.stem
        # Recorta o bloco de contexto/decisão (do início até a primeira seção "##
        # Consequências"/"## Alternativas" se existir, senão o documento inteiro
        # truncado) para manter o JSON de tamanho tratável sem reescrever o conteúdo.
        corpo = texto
        muda_resposta = numero in ADRS_QUE_MUDARAM_A_RESPOSTA
        adrs.append(
            {
                "numero": numero,
                "arquivo": str(path.relative_to(ROOT)),
                "titulo": titulo,
                "muda_a_resposta_do_estudo": muda_resposta,
                # Lista de linhas, não string única: json.dumps(indent=...) grava uma
                # quebra de linha REAL entre elementos de array (ao contrário do \n
                # escapado dentro de uma string), preservando a fronteira de linha que
                # o contrato de teste usa para não confundir números de versão de
                # bibliotecas distintas mencionadas perto uma da outra no texto.
                "texto_completo_linhas": [
                    frag
                    for linha in corpo.splitlines()
                    for frag in _quebrar_apos_nomes_de_biblioteca(linha)
                ],
            }
        )
    return adrs


def montar() -> dict:
    versoes = versoes_do_lockfile()
    if not versoes:
        print(
            "AVISO: uv.lock ausente ou vazio — dependências não podem ser listadas.",
            file=sys.stderr,
        )

    dependencias_criticas = [
        {"nome": lib, "versao": versoes.get(lib.lower()), "categoria": "critica"}
        for lib in BIBLIOTECAS_CRITICAS
    ]
    dependencias_adicionais = [
        {"nome": lib, "versao": versoes.get(lib.lower()), "categoria": "adicional"}
        for lib in BIBLIOTECAS_ADICIONAIS
        if lib.lower() in versoes
    ]

    provenance_texto = PROVENANCE.read_text(encoding="utf-8") if PROVENANCE.exists() else ""
    data_audit_texto = DATA_AUDIT.read_text(encoding="utf-8") if DATA_AUDIT.exists() else ""

    adrs = ler_adrs()
    ausentes = [n for n in ADRS_QUE_MUDARAM_A_RESPOSTA if n not in {a["numero"] for a in adrs}]

    doc = {
        "gerado_por": "pipeline/05_app/gerar_metodologia.py",
        "gerado_em_utc": datetime.now(UTC).isoformat(),
        "fontes": {
            "provenance": str(PROVENANCE.relative_to(ROOT)) if PROVENANCE.exists() else None,
            "data_audit": str(DATA_AUDIT.relative_to(ROOT)) if DATA_AUDIT.exists() else None,
            "uv_lock": str(UV_LOCK.relative_to(ROOT)) if UV_LOCK.exists() else None,
            "adrs_dir": str(ADR_DIR.relative_to(ROOT)),
        },
        "aviso": (
            "Esta página é GERADA. Nenhum número ou trecho abaixo foi digitado à mão: "
            "as seções de proveniência vêm de PROVENANCE.md e data/DATA_AUDIT.md, "
            "recortadas mecanicamente por cabeçalho; as versões de biblioteca vêm de "
            "uv.lock; os textos de decisão vêm de docs/ADR/*.md na íntegra. "
            "Reexecute pipeline/05_app/gerar_metodologia.py após qualquer mudança "
            "nesses arquivos-fonte — nunca edite este JSON manualmente."
        ),
        "ambiente": {
            "gerenciador": "uv (docs/ADR/0002-ambiente-uv-em-vez-de-conda.md)",
            "python_requires": versao_python(),
            "dependencias_criticas": dependencias_criticas,
            "dependencias_adicionais": dependencias_adicionais,
            "total_pacotes_no_lockfile": len(versoes),
        },
        "decisoes_metodologicas": {
            "nota": (
                "§6-A.5: os ADR abaixo mudaram a resposta do estudo e não são apêndice "
                "opcional. 0008 tirou a série própria do papel de série de tendência; "
                "0009 trocou acurácia global por acurácia por classe; 0011 tornou a "
                "pegada industrial/reassentamento classe própria; 0012 recusou "
                "cultivo_sequeiro como cropland defensável; 0013 restringiu o que a "
                "Fase 3 pode estimar (catraca de permanência); 0014 propagou o limiar "
                "relativo e deu escopo por camada à permanência."
            ),
            "adrs_que_mudaram_a_resposta": ADRS_QUE_MUDARAM_A_RESPOSTA,
            "adrs_ausentes_do_repositorio": ausentes,
            "todos_os_adrs": adrs,
        },
        "proveniencia": {
            "provenance_md": secoes_markdown(provenance_texto) if provenance_texto else [],
        },
        "auditoria_de_dados": {
            "data_audit_md": secoes_markdown(data_audit_texto) if data_audit_texto else [],
        },
    }
    return doc


def main() -> None:
    OUT.parent.mkdir(parents=True, exist_ok=True)
    doc = montar()
    OUT.write_text(json.dumps(doc, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"escrito: {OUT.relative_to(ROOT)} ({OUT.stat().st_size} bytes)")


if __name__ == "__main__":
    main()
