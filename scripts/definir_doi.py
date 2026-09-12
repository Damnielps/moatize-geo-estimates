#!/usr/bin/env python3
"""Propaga o DOI do Zenodo para todos os arquivos que o publicam.

O DOI só existe depois que o Zenodo arquiva a primeira release (procedimento em
`docs/CHECKLIST_PUBLICACAO.md`). Até lá o repositório declara a ausência de forma
explícita — `DOI = null` no app, um comentário no lugar do selo no README, um
comentário no JSON-LD — em vez de um valor de exemplo que possa ser publicado por
engano.

Quando o identificador existir, este script escreve o valor **uma vez** nos quatro
lugares que o publicam, em vez das quatro edições manuais que o checklist descrevia.
Edição manual em quatro arquivos é exatamente a classe de erro que §11.2 proíbe: basta
um deles ficar para trás para o painel citar um DOI e o `CITATION.cff` citar outro.

Uso:

    uv run python scripts/definir_doi.py 10.5281/zenodo.1234567
    uv run python scripts/definir_doi.py 10.5281/zenodo.1234567 --doi-versao 10.5281/zenodo.1234568
    uv run python scripts/definir_doi.py --verificar

O primeiro argumento é o **DOI conceitual** (resolve sempre para a versão mais recente);
`--doi-versao` é o DOI da versão arquivada, registrado apenas como identificador
adicional no `CITATION.cff`. `--verificar` não escreve nada: informa em que estado o
repositório está e sai com rc=0 (coerente) ou rc=1 (incoerente entre arquivos).

O script é idempotente e transacional: valida a forma do DOI, localiza todas as âncoras
e só então grava. Se qualquer âncora faltar, nada é escrito e o rc é 2 — um arquivo
mudou de forma e o script precisa ser revisto, o que é melhor do que gravar em três dos
quatro e deixar o quarto divergente.
"""

from __future__ import annotations

import argparse
import re
import sys
from dataclasses import dataclass
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent

# 10.<registrante>/<sufixo>. O registrante do Zenodo é 5281, mas a regra não o fixa:
# um depósito noutro registrante continua sendo um DOI válido para citar.
DOI_RE = re.compile(r"^10\.\d{4,9}/[-._;()/:A-Za-z0-9]+$")

PUBLICACAO_JS = RAIZ / "app/src/lib/publicacao.js"
CITATION = RAIZ / "CITATION.cff"
README = RAIZ / "README.md"
INDEX_HTML = RAIZ / "app/index.html"

MARCA_README = "<!-- selo DOI: inserir após a release no Zenodo -->"
MARCA_JSONLD = '      "isAccessibleForFree": true,'

# O comentário que explica a AUSÊNCIA do DOI no JSON-LD. Enquanto o script só inseria o
# campo, esse comentário ficava para trás dizendo "o Zenodo ainda não emitiu" ao lado de
# um DOI emitido — uma contradição publicada no HTML servido. Ele é substituído junto.
COMENTARIO_SEM_DOI = re.compile(
    r'    <!--\n      Sem "identifier" de DOI por enquanto:.*?-->\n', re.S
)
COMENTARIO_COM_DOI = (
    "    <!--\n"
    "      O \"identifier\" abaixo é o DOI CONCEITUAL do Zenodo: resolve sempre para a\n"
    "      versão mais recente. O DOI da versão arquivada fica em CITATION.cff, como\n"
    "      identificador adicional. Ambos são escritos por scripts/definir_doi.py.\n"
    "    -->\n"
)


class AncoraAusente(RuntimeError):
    """Um arquivo mudou de forma e a âncora esperada não foi encontrada."""


@dataclass
class Mudanca:
    caminho: Path
    antes: str
    depois: str

    @property
    def mudou(self) -> bool:
        return self.antes != self.depois


def _ler(caminho: Path) -> str:
    if not caminho.is_file():
        raise AncoraAusente(f"arquivo ausente: {caminho.relative_to(RAIZ)}")
    return caminho.read_text(encoding="utf-8")


def doi_atual() -> str | None:
    """DOI hoje declarado em `publicacao.js`, ou None se ainda não houver."""
    texto = _ler(PUBLICACAO_JS)
    achado = re.search(r"^export const DOI = (null|\"([^\"]+)\");", texto, re.M)
    if achado is None:
        raise AncoraAusente("publicacao.js: não achei `export const DOI = ...`")
    return achado.group(2)


def _publicacao_js(texto: str, doi: str) -> str:
    novo, n = re.subn(
        r"^export const DOI = (?:null|\"[^\"]+\");",
        f'export const DOI = "{doi}";',
        texto,
        count=1,
        flags=re.M,
    )
    if n != 1:
        raise AncoraAusente("publicacao.js: não achei `export const DOI = ...`")
    return novo


def _citation(texto: str, doi: str, doi_versao: str | None) -> str:
    # Remove um bloco escrito por uma execução anterior, para que reexecutar com outro DOI
    # substitua em vez de acumular. O bloco sai por inteiro, com as quebras que o
    # delimitam: substituí-lo por "\n" acumularia uma linha em branco por execução.
    texto = re.sub(
        r"\n# --- DOI do Zenodo .*?# --- fim do bloco de DOI ---\n",
        "",
        texto,
        flags=re.S,
    )
    linhas = [
        "",
        "# --- DOI do Zenodo (escrito por scripts/definir_doi.py; não editar à mão) ---",
        f'doi: "{doi}"',
        "identifiers:",
        "  - type: doi",
        f'    value: "{doi}"',
        '    description: "DOI conceitual no Zenodo (resolve para a versão mais recente)"',
    ]
    if doi_versao:
        linhas += [
            "  - type: doi",
            f'    value: "{doi_versao}"',
            '    description: "DOI desta versão arquivada no Zenodo"',
        ]
    linhas += ["# --- fim do bloco de DOI ---", ""]
    bloco = "\n".join(linhas)

    # O bloco entra antes de `preferred-citation:`, que tem de continuar sendo o último
    # mapeamento do arquivo para não capturar as chaves de nível raiz que vêm depois.
    alvo = "\npreferred-citation:\n"
    if alvo not in texto:
        raise AncoraAusente("CITATION.cff: não achei `preferred-citation:`")
    texto = texto.replace(alvo, bloco + alvo, 1)

    # E o mesmo DOI dentro de preferred-citation, onde a chave é indentada.
    cabeca, _, cauda = texto.partition(alvo)
    cauda = re.sub(r"^  doi: \"[^\"]+\"\n", "", cauda, count=1, flags=re.M)
    cauda = cauda.replace("  type: data\n", f'  type: data\n  doi: "{doi}"\n', 1)
    return cabeca + alvo + cauda


def _readme(texto: str, doi: str) -> str:
    selo = (
        f"[![DOI](https://zenodo.org/badge/DOI/{doi}.svg)]"
        f"(https://doi.org/{doi})"
    )
    if MARCA_README in texto:
        return texto.replace(MARCA_README, selo, 1)
    novo, n = re.subn(
        r"\[!\[DOI\]\(https://zenodo\.org/badge/DOI/[^)]+\.svg\)\]\([^)]+\)",
        selo,
        texto,
        count=1,
    )
    if n != 1:
        raise AncoraAusente(
            "README.md: não achei nem o comentário de selo nem um selo de DOI anterior"
        )
    return novo


def _index_html(texto: str, doi: str) -> str:
    identificador = f'      "identifier": "https://doi.org/{doi}",'
    texto = COMENTARIO_SEM_DOI.sub(COMENTARIO_COM_DOI, texto, count=1)
    # Remove um identificador escrito antes, para que um DOI novo substitua o anterior.
    texto = re.sub(
        r'^      "identifier": "https://doi\.org/[^"]+",\n',
        "",
        texto,
        count=1,
        flags=re.M,
    )
    if MARCA_JSONLD not in texto:
        raise AncoraAusente(
            'app/index.html: não achei a linha "isAccessibleForFree" do JSON-LD'
        )
    return texto.replace(MARCA_JSONLD, identificador + "\n" + MARCA_JSONLD, 1)


def planejar(doi: str, doi_versao: str | None) -> list[Mudanca]:
    """Calcula todas as edições sem tocar no disco (transacional: tudo ou nada)."""
    pares = [
        (PUBLICACAO_JS, _publicacao_js),
        (CITATION, lambda t, d: _citation(t, d, doi_versao)),
        (README, _readme),
        (INDEX_HTML, _index_html),
    ]
    return [Mudanca(c, (a := _ler(c)), f(a, doi)) for c, f in pares]


def verificar() -> int:
    doi = doi_atual()
    if doi is None:
        print("DOI ainda não emitido: `publicacao.js` declara `null`.")
        for caminho, marca, nome in (
            (README, MARCA_README, "selo pendente"),
            (CITATION, "\ndoi:", "campo doi"),
        ):
            texto = _ler(caminho)
            presente = marca in texto
            esperado = caminho is README
            estado = "ok" if presente == esperado else "INCOERENTE"
            situacao = "presente" if presente else "ausente"
            print(f"  {caminho.relative_to(RAIZ)}: {nome} {situacao} — {estado}")
            if presente != esperado:
                return 1
        print("Coerente: o repositório declara a ausência de DOI em todos os lugares.")
        return 0

    print(f"DOI declarado: {doi}")
    faltando = [
        str(c.relative_to(RAIZ))
        for c in (CITATION, README, INDEX_HTML)
        if doi not in _ler(c)
    ]
    if faltando:
        print("INCOERENTE — o DOI não aparece em: " + ", ".join(faltando))
        return 1
    print(
        "Coerente: o mesmo DOI aparece no app, no CITATION.cff, no README e no JSON-LD."
    )
    return 0


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    ap.add_argument("doi", nargs="?", help="DOI conceitual (ex.: 10.5281/zenodo.1234567)")
    ap.add_argument("--doi-versao", help="DOI da versão arquivada, para registrar também")
    ap.add_argument("--verificar", action="store_true", help="só informa o estado; não escreve")
    args = ap.parse_args(argv)

    if args.verificar:
        return verificar()
    if not args.doi:
        ap.error("informe o DOI conceitual, ou use --verificar")

    for rotulo, valor in (("DOI", args.doi), ("--doi-versao", args.doi_versao)):
        if valor and not DOI_RE.match(valor):
            print(
                f"{rotulo} inválido: {valor!r} — esperado 10.<registrante>/<sufixo>",
                file=sys.stderr,
            )
            return 2

    try:
        mudancas = planejar(args.doi, args.doi_versao)
    except AncoraAusente as erro:
        print(f"Nada foi escrito. {erro}", file=sys.stderr)
        return 2

    escritas = [m for m in mudancas if m.mudou]
    for m in escritas:
        m.caminho.write_text(m.depois, encoding="utf-8")
        print(f"atualizado: {m.caminho.relative_to(RAIZ)}")
    if not escritas:
        print(f"nada a fazer: {args.doi} já está nos quatro arquivos")
    else:
        print("\nFalta reconstruir o app para o DOI chegar ao site: `npm --prefix app run build`.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
