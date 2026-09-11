#!/usr/bin/env python3
"""pipeline/00_fetch/extrair_ine_folheto_tete.py — quadro "PIB e Inflação" do
Folheto Provincial de Tete 2021 (INE) -> data/processed/economia/contas_regionais_tete.csv.

Nível C (licença não localizada; ver data/raw/<pdf>.meta.json): contexto, não núcleo
(§4.0). Nenhum número deste CSV sustenta resultado publicado.

Etapas (§11.2):
  (a) bruto: se `data/raw/ine_contas_folheto_provincial_tete_2021.pdf` não existe,
      baixa da URL Wayback `id_` registrada no `.meta.json` e confere o sha256 do
      `.sha256`; se existe, só confere o hash. Hash divergente => falha explícita
      (§11.2.2), nada é gravado.
  (b) extração: texto do PDF via pypdf (o quadro está na p.1); o quadro é localizado pelo cabeçalho
      "PIB e Inflação Provincia Nacional" e cada campo por regex ancorada no rótulo
      da linha. Cada regex tem de casar exatamente uma vez no documento; qualquer
      outro resultado => falha, sem gravação parcial.
  (c) saída: CSV UTF-8, QUOTE_MINIMAL, fim de linha "\\n", ordem de linhas fixa.
      Valores preservam a grafia do PDF, trocando apenas a vírgula decimal por ponto.

Uso:
  uv run python pipeline/00_fetch/extrair_ine_folheto_tete.py [--saida CAMINHO]
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
import re
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
PDF_NOME = "ine_contas_folheto_provincial_tete_2021.pdf"
PDF_PATH = REPO_ROOT / "data" / "raw" / PDF_NOME
SHA_PATH = PDF_PATH.with_name(PDF_NOME + ".sha256")
META_PATH = PDF_PATH.with_name(PDF_NOME + ".meta.json")
SAIDA_PADRAO = REPO_ROOT / "data" / "processed" / "economia" / "contas_regionais_tete.csv"

COLUNAS = [
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

METODO = (
    "extraído por pipeline/00_fetch/extrair_ine_folheto_tete.py do texto do PDF "
    "(pypdf), quadro 'PIB e Inflação'"
)

# Âncoras do quadro no texto extraído pelo pypdf.
CABECALHO_QUADRO = re.compile(r"PIB e Infla[çc][ãa]o\s+Provincia\s+Nacional")
FONTE_QUADRO = re.compile(
    r"Fonte:\s*INE,\s*Direc[çc][ãa]o de Contas Nacionais,\s*Indicadores Globais"
)

NUM = r"(-?\d+(?:,\d+)?)"
# campo -> regex ancorada no rótulo da linha do quadro; grupos: ano, Província, Nacional.
CAMPOS: dict[str, re.Pattern[str]] = {
    "taxa_crescimento_pib_real": re.compile(
        r"Taxa de Crescimento do PIB \(%\)\s*-\s*(\d{4})\s+" + NUM + r"\s+" + NUM + r"\s*$",
        re.MULTILINE,
    ),
    "pib_per_capita_usd": re.compile(
        r"PIB per capita em US\$ \((\d{4})\)\s+" + NUM + r"\s+" + NUM + r"\s*$",
        re.MULTILINE,
    ),
    "pib_percentual_pib_nacional": re.compile(
        r"PIB em % do PIB Nacional \((\d{4})\)\s+" + NUM + r"\s+" + NUM + r"\s*$",
        re.MULTILINE,
    ),
    "inflacao_media": re.compile(
        r"Infla[çc][ãa]o m[ée]dia \(%\)\s*-\s*(\d{4})\s+" + NUM + r"\s+" + NUM + r"\s*$",
        re.MULTILINE,
    ),
    "inflacao_acumulada": re.compile(
        r"Infla[çc][ãa]o acumulada \(%\)\s*-\s*(\d{4})\s+" + NUM + r"\s+" + NUM + r"\s*$",
        re.MULTILINE,
    ),
}

TETE = "Provincia de Tete"
MOZ = "Mocambique"
FONTE_PROV = "INE Folheto Provincial Tete 2021 p.1, quadro 'PIB e Inflação'"
FONTE_NAC = "INE Folheto Provincial Tete 2021 p.1, quadro 'PIB e Inflação', coluna Nacional"
PREFIXO_NOTA = "contexto, não núcleo (§4.0): "

# Ordem de linhas fixa: (unidade, campo, coluna do quadro, unidade_medida, fonte, nota).
LINHAS = [
    (
        TETE, "taxa_crescimento_pib_real", "provincia", "percentual",
        FONTE_PROV + "; fonte declarada no documento: INE Direcção de Contas Nacionais "
        "Indicadores Globais",
        "série provincial de PIB do INE (Contas Regionais); não disponível diretamente "
        "em ine.gov.mz (erro de certificado TLS); lido via snapshot Wayback Machine "
        "20251116031649 do PDF Folheto Provincial_Tete_2021.pdf",
    ),
    (
        MOZ, "taxa_crescimento_pib_real", "nacional", "percentual", FONTE_NAC,
        "valor nacional publicado no mesmo folheto provincial de Tete, para comparação; "
        "mesma proveniência do valor provincial nesta linha",
    ),
    (
        TETE, "pib_per_capita_usd", "provincia", "USD", FONTE_PROV,
        "PIB per capita provincial declarado; ver nota da primeira linha sobre acesso",
    ),
    (
        MOZ, "pib_per_capita_usd", "nacional", "USD", FONTE_NAC,
        "valor nacional para comparação; ver nota da primeira linha",
    ),
    (
        TETE, "pib_percentual_pib_nacional", "provincia", "percentual", FONTE_PROV,
        "participação da província no PIB nacional, único dado de magnitude/composição "
        "encontrado; não é série por ramo de atividade (Contas Regionais por ramo de "
        "atividade não localizadas)",
    ),
    (
        TETE, "inflacao_media", "provincia", "percentual", FONTE_PROV,
        "inflação média provincial declarada; ver nota da primeira linha sobre acesso",
    ),
    (
        MOZ, "inflacao_media", "nacional", "percentual", FONTE_NAC,
        "valor nacional para comparação; ver nota da primeira linha",
    ),
    (
        TETE, "inflacao_acumulada", "provincia", "percentual", FONTE_PROV,
        "inflação acumulada provincial declarada; ver nota da primeira linha sobre acesso",
    ),
    (
        MOZ, "inflacao_acumulada", "nacional", "percentual", FONTE_NAC,
        "valor nacional para comparação; ver nota da primeira linha",
    ),
]


class ExtracaoFalhou(RuntimeError):
    """Qualquer divergência do documento esperado. Nada é gravado."""


def sha256_arquivo(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for bloco in iter(lambda: f.read(1 << 16), b""):
            h.update(bloco)
    return h.hexdigest()


def hash_esperado() -> str:
    conteudo = SHA_PATH.read_text(encoding="utf-8").split()
    if not conteudo or not re.fullmatch(r"[0-9a-f]{64}", conteudo[0]):
        raise ExtracaoFalhou(f"{SHA_PATH} sem sha256 válido")
    return conteudo[0]


def garantir_pdf(pdf: Path = PDF_PATH) -> Path:
    """(a) Baixa se ausente; confere o sha256 em qualquer caso."""
    esperado = hash_esperado()
    if not pdf.exists():
        import requests  # só necessário quando há download

        url = json.loads(META_PATH.read_text(encoding="utf-8"))["url"]
        print(f"[folheto-tete] PDF ausente; baixando {url}", file=sys.stderr)
        resp = requests.get(url, timeout=120)
        resp.raise_for_status()
        obtido = hashlib.sha256(resp.content).hexdigest()
        if obtido != esperado:
            raise ExtracaoFalhou(
                f"sha256 do download diverge (esperado {esperado}, obtido {obtido}); "
                "a fonte mudou — nada gravado (§11.2.2)"
            )
        tmp = pdf.with_name(pdf.name + ".part")
        tmp.write_bytes(resp.content)
        tmp.replace(pdf)
    obtido = sha256_arquivo(pdf)
    if obtido != esperado:
        raise ExtracaoFalhou(
            f"sha256 de {pdf} diverge (esperado {esperado}, obtido {obtido}) (§11.2.2)"
        )
    return pdf


def texto_pdf(pdf: Path) -> str:
    import pypdf

    return "\n".join((p.extract_text() or "") for p in pypdf.PdfReader(str(pdf)).pages)


def _decimal_ponto(s: str) -> str:
    return s.replace(",", ".")


def extrair_quadro(texto: str) -> dict[str, dict[str, str]]:
    """(b) Retorna {campo: {"ano", "provincia", "nacional"}} ou falha."""
    for nome, rx in (("cabeçalho", CABECALHO_QUADRO), ("linha de fonte", FONTE_QUADRO)):
        n = len(rx.findall(texto))
        if n != 1:
            raise ExtracaoFalhou(f"{nome} do quadro 'PIB e Inflação' casou {n} vezes (esperado 1)")
    inicio = CABECALHO_QUADRO.search(texto).end()
    resultado: dict[str, dict[str, str]] = {}
    for campo, rx in CAMPOS.items():
        casos = rx.findall(texto)
        if len(casos) != 1:
            raise ExtracaoFalhou(f"campo {campo!r} casou {len(casos)} vezes (esperado 1)")
        m = rx.search(texto)
        if m.start() < inicio:
            raise ExtracaoFalhou(f"campo {campo!r} encontrado antes do cabeçalho do quadro")
        ano, prov, nac = casos[0]
        resultado[campo] = {
            "ano": ano,
            "provincia": _decimal_ponto(prov),
            "nacional": _decimal_ponto(nac),
        }
    # Verificação interna do quadro: a coluna Nacional da participação tem de ser 100.
    if float(resultado["pib_percentual_pib_nacional"]["nacional"]) != 100.0:
        raise ExtracaoFalhou("coluna Nacional de 'PIB em % do PIB Nacional' ≠ 100")
    return resultado


def montar_linhas(quadro: dict[str, dict[str, str]]) -> list[dict[str, str]]:
    linhas = []
    for unidade, campo, coluna, unidade_medida, fonte, nota in LINHAS:
        linhas.append(
            {
                "unidade_geografica": unidade,
                "ano": quadro[campo]["ano"],
                "variavel": campo,
                "valor": quadro[campo][coluna],
                "unidade_medida": unidade_medida,
                "selo": "observado",
                "nivel_fonte": "C",
                "fonte": fonte,
                "metodo": METODO,
                "nota": PREFIXO_NOTA + nota,
            }
        )
    if len(linhas) != 9:
        raise ExtracaoFalhou(f"{len(linhas)} linhas montadas (esperado 9)")
    return linhas


def serializar(linhas: list[dict[str, str]]) -> bytes:
    buf = io.StringIO()
    w = csv.DictWriter(buf, fieldnames=COLUNAS, quoting=csv.QUOTE_MINIMAL, lineterminator="\n")
    w.writeheader()
    w.writerows(linhas)
    return buf.getvalue().encode("utf-8")


def main(saida: Path = SAIDA_PADRAO, pdf: Path = PDF_PATH) -> Path:
    pdf = garantir_pdf(pdf)
    conteudo = serializar(montar_linhas(extrair_quadro(texto_pdf(pdf))))
    saida.parent.mkdir(parents=True, exist_ok=True)
    tmp = saida.with_name(saida.name + ".tmp")
    tmp.write_bytes(conteudo)
    tmp.replace(saida)
    print(f"[folheto-tete] {saida} sha256={hashlib.sha256(conteudo).hexdigest()}")
    return saida


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--saida", type=Path, default=SAIDA_PADRAO)
    args = ap.parse_args()
    try:
        main(args.saida)
    except ExtracaoFalhou as e:
        print(f"[folheto-tete] FALHA: {e}", file=sys.stderr)
        sys.exit(1)
