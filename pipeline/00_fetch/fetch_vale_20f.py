#!/usr/bin/env python3
"""fetch_vale_20f.py — Download idempotente dos Form 20-F da Vale S.A. (SEC EDGAR)
e, quando localizados via EDGAR full text search, dos Forms 6-K "Operations
Review" da Rio Tinto plc com dados de produção da mina de Benga (Moatize
Basin, Mozambique), até a venda da operação (2014).

Fonte primária: SEC EDGAR.
  - Vale S.A., CIK 0000917851 — Form 20-F.
  - Rio Tinto plc, CIK 0000863064 — Form 6-K, exhibits "Operations Review".
Licença: "Website Dissemination" — https://www.sec.gov/about/privacy-information
  ("Information presented on sec.gov is considered public information and may
  be copied or further distributed by users of the web site without the SEC's
  permission. Please consider appropriate citation to the SEC as the source.")
  → nível A. Base legal é a política do REGULADOR (a SEC), não a página do
  emissor — ver data/DATA_AUDIT.md, seção "Fase 4b — Marcos, relatórios de
  emissor e licenças de publicação".

POLÍTICA DE ACESSO JUSTO DA SEC (obrigatória, não opcional):
  A SEC exige que todo request de dado automatizado identifique quem está
  baixando, com um contato real, no formato "Nome Sobrenome email@dominio"
  (ver https://www.sec.gov/os/webmaster-faq#developers). Não existe um
  User-Agent "correto" universal: o que a SEC rejeita é a AUSÊNCIA de contato
  real verificável — não um literal específico. Por isso este script NUNCA
  embute um contato no código. Ele lê a variável de ambiente obrigatória
  `SEC_USER_AGENT` e falha explicitamente, com esta explicação, se ela não
  estiver definida. Quem executa o script preenche o próprio contato:

    export SEC_USER_AGENT="Nome Sobrenome email@dominio"
    uv run python pipeline/00_fetch/fetch_vale_20f.py

  O valor de SEC_USER_AGENT NUNCA é gravado em `.meta.json`, log ou qualquer
  artefato versionado — só é usado no cabeçalho HTTP do próprio processo.

NOTA HISTÓRICA (2026-09-11, reexecução da tarefa A2b/T2): uma execução
anterior deste script embutia um literal fixo de User-Agent contendo um
endereço em `users.noreply.github.com` e concluiu, a partir de um 403 da SEC
para esse literal específico, que o WAF da SEC bloqueava "a string exigida
pela tarefa". O diagnóstico correto é mais simples: o domínio
`users.noreply.github.com` não corresponde à política de contato real da SEC
(ver link acima), e um User-Agent no formato "Nome Sobrenome email@dominio"
de um domínio de e-mail comum recebe 200 na mesma URL, no mesmo instante —
verificado nesta reexecução em `data.sec.gov/submissions/...`. A causa era a
instrução (um literal de contato inválido embutido no orquestrador anterior),
não uma falha deste script nem um bloqueio geral da SEC a coleta
automatizada identificada corretamente. Esta versão corrige isso: não embute
nenhum User-Agent; exige que quem executa declare o próprio contato via
variável de ambiente.

Máx. 10 req/s (aqui, 1 req a cada 0,15 s de margem).

Uso:
  export SEC_USER_AGENT="Nome Sobrenome email@dominio"
  uv run python pipeline/00_fetch/fetch_vale_20f.py

Saída esperada em execução bem-sucedida:
  - Um .htm por Form 20-F da Vale (exercícios 2007–2022, filings 2008–2023)
    em `data/raw/`, cada um com `.sha256` e `.meta.json`.
  - Um .htm por exhibit "Operations Review" da Rio Tinto localizado nesta
    coleta (ver `RIO_TINTO_OPERATIONS_REVIEWS` abaixo), com o mesmo contrato.
  - `data/processed/economia/producao_moatize_anual.csv` regenerado a partir
    exclusivamente dos arquivos em `data/raw/` — nunca por valor digitado à
    mão. Sem os brutos localmente, o CSV mantém as linhas "não disponível"
    com o motivo "aguarda SEC_USER_AGENT".
"""

from __future__ import annotations

import hashlib
import json
import logging
import os
import re
import sys
import time
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

import pandas as pd

REPO_ROOT = Path(__file__).resolve().parents[2]
DATA_RAW = REPO_ROOT / "data" / "raw"
DATA_INTERIM = REPO_ROOT / "data" / "interim"
DATA_PROCESSED = REPO_ROOT / "data" / "processed" / "economia"
DATA_INTERIM.mkdir(parents=True, exist_ok=True)
DATA_RAW.mkdir(parents=True, exist_ok=True)
DATA_PROCESSED.mkdir(parents=True, exist_ok=True)

CIK_VALE = "0000917851"
CIK_RIO_TINTO = "0000863064"
ANOS_ALVO_VALE = set(range(2008, 2023))  # 20-F referentes a exercícios 2007–2022

CSV_SAIDA = DATA_PROCESSED / "producao_moatize_anual.csv"
CSV_COLUNAS = [
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

# Exhibits "Operations Review" da Rio Tinto plc (CIK 863064) localizados via
# EDGAR full text search (https://www.sec.gov/cgi-bin/srqsb ... efts.sec.gov,
# verificado 2026-09-11) contendo a string "Benga" no período em que a mina
# esteve sob controle da Rio Tinto (2011-2013). Cada item é um 6-K distinto;
# o texto contém tabelas trimestrais de produção "Rio Tinto Coal Mozambique
# — Benga", não uma tabela anual única. Ver nota em extrair_producao_benga().
RIO_TINTO_OPERATIONS_REVIEWS = [
    {
        "accessionNumber": "0001193125-12-170807",
        "primaryDocument": "d337623dex991.htm",
        "periodo": "1Q2012",
        "filingDate": "2012-04-19",
    },
    {
        "accessionNumber": "0001003297-12-000457",
        "primaryDocument": "rt99-1.htm",
        "periodo": "3Q2012",
        "filingDate": "2012-11-02",
    },
    {
        "accessionNumber": "0001003297-13-000034",
        "primaryDocument": "exhibit99-1.htm",
        "periodo": "4Q2012/FY2012",
        "filingDate": "2013-02-05",
    },
]

LOG_FILE = DATA_INTERIM / "vale_20f_fetch.log"
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[logging.FileHandler(LOG_FILE), logging.StreamHandler()],
)
logger = logging.getLogger(__name__)


class SecUserAgentAusente(SystemExit):
    """Levantada (como SystemExit) quando SEC_USER_AGENT não está definida."""


MENSAGEM_SEC_USER_AGENT = """\
ERRO: variável de ambiente SEC_USER_AGENT não definida.

A SEC exige que todo acesso automatizado a sec.gov/data.sec.gov identifique
um contato real no cabeçalho HTTP User-Agent, no formato:

    Nome Sobrenome email@dominio

(política de acesso justo da SEC — https://www.sec.gov/os/webmaster-faq#developers).
Este script nunca embute um contato de terceiros nem inventa um — quem
executa a coleta declara o próprio. Defina a variável e rode de novo:

    export SEC_USER_AGENT="Nome Sobrenome email@dominio"
    uv run python pipeline/00_fetch/fetch_vale_20f.py

O valor de SEC_USER_AGENT nunca é gravado em .meta.json, log ou qualquer
artefato versionado deste repositório.
"""


def obter_user_agent() -> str:
    valor = os.environ.get("SEC_USER_AGENT", "").strip()
    if not valor:
        logger.error(MENSAGEM_SEC_USER_AGENT)
        raise SecUserAgentAusente(2)
    return valor


def sha256_file(filepath: Path, chunk_size: int = 8192) -> str:
    sha256 = hashlib.sha256()
    with open(filepath, "rb") as f:
        for chunk in iter(lambda: f.read(chunk_size), b""):
            sha256.update(chunk)
    return sha256.hexdigest()


def _get(url: str, user_agent: str) -> bytes:
    """GET com o User-Agent do operador; levanta a exceção HTTP explicitamente."""
    req = Request(url, headers={"User-Agent": user_agent})
    with urlopen(req, timeout=60) as resp:
        return resp.read()


def listar_filings_20f(cik: str, user_agent: str) -> list[dict]:
    """Lista os Forms 20-F de um CIK via API de submissions da SEC.

    Percorre `filings.recent` e, quando presentes, os arquivos adicionais em
    `filings.files` (submissões paginadas para emissores com muitos filings,
    caso da Vale). Retorna lista de dicts {accessionNumber, filingDate,
    primaryDocument, reportDate}. Levanta RuntimeError explícito se o
    request falhar (403, 404, formato inesperado) — nunca inventa uma lista
    de filings.
    """
    url = f"https://data.sec.gov/submissions/CIK{cik}.json"
    raw = _get(url, user_agent)
    data = json.loads(raw)

    def extrair(bloco: dict) -> list[dict]:
        forms = bloco["form"]
        out = []
        for i, form in enumerate(forms):
            if form == "20-F":
                out.append(
                    {
                        "accessionNumber": bloco["accessionNumber"][i],
                        "filingDate": bloco["filingDate"][i],
                        "primaryDocument": bloco["primaryDocument"][i],
                        "reportDate": bloco.get("reportDate", [""] * len(forms))[i],
                    }
                )
        return out

    filings = extrair(data["filings"]["recent"])
    for extra in data["filings"].get("files", []):
        extra_url = f"https://data.sec.gov/submissions/{extra['name']}"
        time.sleep(0.15)
        extra_raw = _get(extra_url, user_agent)
        extra_data = json.loads(extra_raw)
        filings.extend(extrair(extra_data))
    return filings


@dataclass
class ArquivoBaixado:
    caminho: Path
    ano_ref: str
    accession: str
    url: str


def baixar_documento(
    cik: str,
    accession_number: str,
    primary_document: str,
    out_name: str,
    user_agent: str,
    extra_meta: dict,
) -> Path | None:
    """Baixa um documento primário (20-F ou exhibit de 6-K); grava .sha256/.meta.json.

    Idempotente: se o arquivo e o .sha256 já existem e conferem, não baixa de
    novo. Se o hash não confere (fonte mudou), falha explicitamente. O
    .meta.json nunca contém o valor de SEC_USER_AGENT.
    """
    accession_nodash = accession_number.replace("-", "")
    url = f"https://www.sec.gov/Archives/edgar/data/{int(cik)}/{accession_nodash}/{primary_document}"
    # `primaryDocument` pode trazer subdiretório do EDGAR (ex.: "FY2012/exhibit99-1.htm"):
    # o nome LOCAL é achatado para ficar em data/raw/; a URL continua com o caminho original.
    out_name = out_name.replace("/", "_")
    out_file = DATA_RAW / out_name
    checksum_file = DATA_RAW / f"{out_name}.sha256"
    meta_file = DATA_RAW / f"{out_name}.meta.json"

    if out_file.exists() and checksum_file.exists():
        expected = checksum_file.read_text().split()[0].strip()
        actual = sha256_file(out_file)
        if actual == expected:
            logger.info(f"{out_name}: já presente, hash confere, pulando.")
            return out_file
        raise RuntimeError(
            f"{out_name}: hash local não confere com {checksum_file} — "
            "arquivo pré-existente foi alterado; abortando em vez de "
            "sobrescrever silenciosamente."
        )

    try:
        content = _get(url, user_agent)
    except (HTTPError, URLError) as exc:
        logger.error(f"Falha ao baixar {url}: {exc}")
        return None

    out_file.write_bytes(content)
    sha = sha256_file(out_file)
    checksum_file.write_text(f"{sha}  {out_file.name}\n")
    meta = {
        "url": url,
        "download_date": datetime.now(tz=UTC).date().isoformat(),
        "size_bytes": out_file.stat().st_size,
        "license": (
            "Website Dissemination — SEC.gov: informação pública, pode ser "
            "copiada/redistribuída com citação à SEC como fonte "
            "(https://www.sec.gov/about/privacy-information)."
        ),
        "level": "A",
        "source_page": f"https://www.sec.gov/cgi-bin/browse-edgar?action=getcompany&CIK={cik}",
        "accessionNumber": accession_number,
        **extra_meta,
    }
    meta_file.write_text(json.dumps(meta, indent=2, ensure_ascii=False))
    logger.info(f"Baixado {out_name} ({out_file.stat().st_size} bytes).")
    time.sleep(0.15)  # margem sob o limite de 10 req/s da SEC
    return out_file


def baixar_20f_vale(user_agent: str) -> list[ArquivoBaixado]:
    filings = listar_filings_20f(CIK_VALE, user_agent)
    if not filings:
        raise RuntimeError(f"Nenhum 20-F encontrado para CIK {CIK_VALE} — abortando.")
    baixados = []
    for filing in filings:
        ano = int(filing["reportDate"][:4]) if filing["reportDate"] else None
        if ano is not None and ano not in ANOS_ALVO_VALE and (ano + 1) not in ANOS_ALVO_VALE:
            continue
        ano_ref = filing["reportDate"][:4] or filing["filingDate"][:4]
        out_name = f"vale_20f_{ano_ref}_{filing['primaryDocument']}"
        path = baixar_documento(
            CIK_VALE,
            filing["accessionNumber"],
            filing["primaryDocument"],
            out_name,
            user_agent,
            extra_meta={
                "filingDate": filing["filingDate"],
                "reportDate": filing["reportDate"],
                "issuer": "Vale S.A. (CIK 0000917851)",
                "form": "20-F",
            },
        )
        if path is not None:
            baixados.append(
                ArquivoBaixado(path, ano_ref, filing["accessionNumber"], path.name)
            )
    return baixados


def baixar_6k_rio_tinto(user_agent: str) -> list[ArquivoBaixado]:
    baixados = []
    for item in RIO_TINTO_OPERATIONS_REVIEWS:
        out_name = f"riotinto_6k_{item['periodo']}_{item['primaryDocument']}"
        path = baixar_documento(
            CIK_RIO_TINTO,
            item["accessionNumber"],
            item["primaryDocument"],
            out_name,
            user_agent,
            extra_meta={
                "filingDate": item["filingDate"],
                "issuer": "Rio Tinto plc (CIK 0000863064)",
                "form": "6-K",
                "exhibit": "Global Operations Review",
                "periodo": item["periodo"],
            },
        )
        if path is not None:
            baixados.append(
                ArquivoBaixado(path, item["periodo"], item["accessionNumber"], path.name)
            )
    return baixados


# ---------------------------------------------------------------------------
# Extração — produção de carvão em Moatize (Vale, 20-F)
# ---------------------------------------------------------------------------


class ExtracaoFalhou(Exception):
    """Levantada quando a estrutura esperada da tabela não é encontrada."""


# Registro determinístico de qual flavor de parser HTML leu cada arquivo
# (para o provenance/metodo — nunca decidido implicitamente pelo fallback
# interno e não documentado do próprio pandas.read_html).
FLAVOR_USADO: dict[str, str] = {}


_MSG_NENHUMA_TABELA = "No tables found matching"


def _ler_tabelas_html(html_path: Path, match: str) -> list[pd.DataFrame]:
    """Lê as tabelas de `html_path` que casam com `match`, com ordem de
    flavor FIXA e determinística: tenta `lxml` primeiro; só cai para
    `bs4`/`html5lib` se `lxml` levantar uma falha de PARSE (qualquer exceção
    cuja mensagem não seja a de "nenhuma tabela casou com o padrão" —
    ausência real de tabela não é falha de parser, e tentar outro flavor no
    mesmo documento não vai fazer a tabela aparecer). Registra em
    FLAVOR_USADO[html_path.name] qual foi efetivamente usado, para o CSV de
    proveniência poder citar o parser por arquivo em vez de depender do
    fallback silencioso e não determinístico de versão para versão do
    pandas (ver nota de reexecução A2b/T2).
    """
    try:
        tabelas = pd.read_html(html_path, match=match, flavor="lxml")
        FLAVOR_USADO[html_path.name] = "lxml"
        return tabelas
    except ValueError as exc_lxml:
        if _MSG_NENHUMA_TABELA in str(exc_lxml):
            # lxml analisou o documento com sucesso mas não achou tabela que
            # casasse com `match` — ausência real, não falha de parser.
            FLAVOR_USADO[html_path.name] = "lxml"
            raise
        tabelas = pd.read_html(html_path, match=match, flavor="bs4")
        FLAVOR_USADO[html_path.name] = (
            f"bs4/html5lib (lxml falhou: ValueError: {exc_lxml}"[:120] + ")"
        )
        return tabelas
    except Exception as exc_lxml:
        tabelas = pd.read_html(html_path, match=match, flavor="bs4")
        FLAVOR_USADO[html_path.name] = (
            f"bs4/html5lib (lxml falhou: {type(exc_lxml).__name__}: {exc_lxml}"[:120] + ")"
        )
        return tabelas


_RE_VENDA_ATIVO = re.compile(
    r"sale of (our )?coal (operations|assets)", re.IGNORECASE
)
_RE_PRE_OPERACAO = re.compile(
    r"nominal production capacity of\s+[\d.]+\s*(million metric tons|Mtpy)",
    re.IGNORECASE,
)
_RE_NAO_EM_PRODUCAO = re.compile(
    r"mine is not yet in production", re.IGNORECASE
)


def _diagnosticar_ausencia_tabela(html_path: Path) -> str:
    """Quando nenhuma tabela de produção é localizada, procura no texto bruto
    do próprio 20-F um motivo textual verificável — nunca infere o motivo por
    suposição externa ao documento. Devolve uma frase para `nota`/mensagem de
    erro; se nenhum padrão textual conhecido é encontrado, diz isso
    explicitamente em vez de inventar uma causa.
    """
    try:
        texto = html_path.read_text(encoding="utf-8", errors="ignore")
    except OSError:
        return "não foi possível ler o arquivo para diagnosticar a ausência da tabela."
    if _RE_VENDA_ATIVO.search(texto) and "Moatize" in texto:
        return (
            "o texto do próprio 20-F relata a venda das operações de carvão "
            "(incluindo a mina de Moatize) — ver trecho 'sale of coal "
            "operations/assets'; o exercício fiscal deste filing não tem "
            "mais Moatize como segmento reportado da Vale."
        )
    if _RE_NAO_EM_PRODUCAO.search(texto) or (
        _RE_PRE_OPERACAO.search(texto) and "thousand metric tons" not in texto.lower()
    ):
        return (
            "o texto do próprio 20-F descreve Moatize em fase de licenciamento/"
            "construção ('nominal production capacity' futura ou 'mine is not "
            "yet in production'), sem tabela de produção real neste exercício."
        )
    return (
        "nenhum padrão textual conhecido (venda de ativo, mina ainda não "
        "em produção) foi localizado no documento para explicar a ausência "
        "da tabela — motivo não determinado a partir deste arquivo."
    )



_RE_ANO = re.compile(r"^(19|20)\d{2}$")
_RE_MOATIZE = re.compile(r"^Moatize(\(\d+\))?\s*$", re.IGNORECASE)
_RE_SECAO_METALURGICO = re.compile(r"^Metallurgical coal:?\s*$", re.IGNORECASE)
_RE_SECAO_TERMICO = re.compile(r"^Thermal coal:?\s*$", re.IGNORECASE)


def _celula_para_valor(cel) -> float | None:
    """Converte uma célula de tabela de produção em número (ou None).

    Trata NaN, travessão/hífen (sem produção reportada) e separador de
    milhar; nunca converte texto não numérico em zero silenciosamente.
    """
    if cel is None or (isinstance(cel, float) and pd.isna(cel)):
        return None
    texto = str(cel).strip()
    if texto in ("", "–", "-", "—", "nan", "NaN"):
        return None
    texto = texto.replace(",", "")
    try:
        return float(texto)
    except ValueError:
        return None


_RE_NUMERO_OU_DASH = re.compile(r"^[\d,]+$|^[-–—]$")


def _anos_por_coluna(df: pd.DataFrame) -> dict[int, int] | None:
    """Localiza a linha de cabeçalho com os anos e devolve um mapa
    {índice_de_coluna: ano}, preservando a posição exata de cada ano no
    cabeçalho — nunca assume que os anos aparecem em ordem crescente nem que
    cada ano ocupa uma única coluna (os 20-F da Vale usam pares de colunas
    por ano, com uma delas em branco/zero-width-space por diagramação)."""
    for _, row in df.iterrows():
        mapa: dict[int, int] = {}
        for col_idx, cel in enumerate(row.tolist()):
            texto = str(cel).strip()
            if _RE_ANO.match(texto):
                mapa[col_idx] = int(texto)
        if len(set(mapa.values())) >= 2:
            return mapa
    return None


def extrair_producao_moatize_vale(
    html_path: Path, ano_arquivo: str, accession: str, url_fonte: str
) -> list[dict]:
    """Extrai produção de carvão de Moatize (Vale) de um 20-F.

    Localiza, entre as tabelas que mencionam "Moatize", a tabela de produção
    (contém uma seção "Metallurgical coal:" e/ou "Thermal coal:" e uma linha
    de cabeçalho com pelo menos dois anos de 4 dígitos). Para cada linha cujo
    rótulo é exatamente "Moatize" (com ou sem nota de rodapé numerada), lê os
    valores numéricos da linha, na ordem em que aparecem, e os associa
    posicionalmente aos anos da linha de cabeçalho (mesma ordem de leitura).
    Levanta ExtracaoFalhou se a tabela de produção não for localizada, ou se
    o número de valores numéricos de uma linha "Moatize" não corresponder ao
    número de anos do cabeçalho — nunca adivinha o alinhamento.

    Cada item retornado carrega o localizador: ano do filing (nome do
    arquivo), accession number, URL, e a legenda da tabela.
    """
    try:
        tabelas = _ler_tabelas_html(html_path, match="Moatize")
    except ValueError as exc:
        diagnostico = _diagnosticar_ausencia_tabela(html_path)
        raise ExtracaoFalhou(
            f"Nenhuma tabela com 'Moatize' em {html_path.name} "
            f"(parser: {FLAVOR_USADO.get(html_path.name, 'desconhecido')}): {exc} — {diagnostico}"
        ) from exc

    tabela_producao = None
    for tabela in tabelas:
        texto_tabela = tabela.astype(str).apply(lambda c: c.str.cat(sep=" ")).str.cat(sep=" ")
        # \s cobre espaço normal e non-breaking space (U+00A0), que a Vale
        # usa em alguns exercícios dentro da própria legenda da unidade.
        tem_secao = re.search(r"Metallurgical\s*coal\s*:", texto_tabela)
        tem_unidade = re.search(r"thousand\s*metric\s*tons", texto_tabela)
        if tem_secao and tem_unidade:
            tabela_producao = tabela
            break

    if tabela_producao is None:
        diagnostico = _diagnosticar_ausencia_tabela(html_path)
        raise ExtracaoFalhou(
            f"Tabela de produção de carvão ('Metallurgical coal:' + "
            f"'(thousand metric tons)') não localizada em {html_path.name} "
            f"(parser: {FLAVOR_USADO.get(html_path.name, 'desconhecido')}) — {diagnostico}"
        )

    anos_por_coluna = _anos_por_coluna(tabela_producao)
    if anos_por_coluna is None:
        raise ExtracaoFalhou(
            f"Linha de cabeçalho com anos não localizada na tabela de produção de {html_path.name}."
        )
    anos_unicos = sorted(set(anos_por_coluna.values()))
    colunas_por_ano: dict[int, list[int]] = {ano: [] for ano in anos_unicos}
    for col_idx, ano in anos_por_coluna.items():
        colunas_por_ano[ano].append(col_idx)

    resultados = []
    secao_atual = None
    for _, row in tabela_producao.iterrows():
        valores_linha = row.tolist()
        rotulo = None
        for cel in valores_linha[:3]:
            texto = str(cel).strip()
            if texto and texto.lower() != "nan":
                rotulo = texto
                break
        if rotulo is None:
            continue
        if _RE_SECAO_METALURGICO.match(rotulo):
            secao_atual = "producao_carvao_metalurgico"
            continue
        if _RE_SECAO_TERMICO.match(rotulo):
            secao_atual = "producao_carvao_termico"
            continue
        if not _RE_MOATIZE.match(rotulo):
            continue

        if secao_atual is None:
            raise ExtracaoFalhou(
                f"Linha 'Moatize' em {html_path.name} encontrada fora de uma "
                "seção 'Metallurgical coal:'/'Thermal coal:' reconhecida."
            )

        # Alinhamento por índice de coluna, não por posição sequencial dos
        # valores não vazios: cada ano tem uma ou mais colunas candidatas
        # (diagramação em pares), e exatamente uma delas deve conter um
        # número ou travessão nesta linha de dados. Quando o PRÓPRIO
        # CABEÇALHO do documento repete o rótulo do ano (defeito do filing
        # de origem, não do parser — ex.: FY2019 20-F rotula duas colunas
        # como "2018"), a ambiguidade não é resolvida por posição: a linha
        # fica marcada como ambígua para aquele ano específico, com os dois
        # valores brutos preservados em `nota`, e a extração dos DEMAIS anos
        # da mesma linha/tabela continua normalmente — um defeito pontual no
        # cabeçalho não pode apagar dados válidos e não ambíguos do resto do
        # arquivo.
        valores_por_ano: dict[int, float | None] = {}
        ambiguos: dict[int, list[str]] = {}
        for ano in anos_unicos:
            candidatos = []
            for col_idx in colunas_por_ano[ano]:
                if col_idx >= len(valores_linha):
                    continue
                texto = str(valores_linha[col_idx]).strip()
                if _RE_NUMERO_OU_DASH.match(texto):
                    candidatos.append(texto)
            if len(candidatos) > 1 and len(set(candidatos)) > 1:
                ambiguos[ano] = candidatos
                valores_por_ano[ano] = None
                continue
            valores_por_ano[ano] = _celula_para_valor(candidatos[0]) if candidatos else None

        for ano, valor_mil_t in sorted(valores_por_ano.items()):
            locator = (
                f"Vale S.A., Form 20-F (arquivo {html_path.name}, exercício "
                f"declarado {ano_arquivo}), accession {accession}, tabela "
                f"'coal production' / seção {secao_atual}, {url_fonte}"
            )
            if ano in ambiguos:
                resultados.append(
                    {
                        "ano": ano,
                        "variavel": secao_atual,
                        "valor_mt": None,
                        "flavor": FLAVOR_USADO.get(html_path.name, "lxml"),
                        "ambiguo": True,
                        "nota_ambiguidade": (
                            f"cabeçalho da tabela em {html_path.name} rotula mais de "
                            f"uma coluna como '{ano}' (defeito de diagramação do "
                            f"próprio filing, não do parser); valores brutos "
                            f"conflitantes encontrados nessas colunas: "
                            f"{ambiguos[ano]} mil t — não atribuído a nenhum ano "
                            "por não haver critério textual de desambiguação neste "
                            "documento."
                        ),
                        "locator": locator,
                    }
                )
                continue
            resultados.append(
                {
                    "ano": ano,
                    "variavel": secao_atual,
                    "valor_mt": None if valor_mil_t is None else round(valor_mil_t / 1000.0, 4),
                    "flavor": FLAVOR_USADO.get(html_path.name, "lxml"),
                    "locator": locator,
                }
            )
    if not resultados:
        raise ExtracaoFalhou(
            f"Tabela de produção localizada em {html_path.name}, mas nenhuma linha "
            "'Moatize' foi extraída dela."
        )
    return resultados


def extrair_producao_benga_riotinto(
    html_path: Path, periodo: str, accession: str, url_fonte: str
) -> list[dict]:
    """Extrai (parcialmente) produção de Benga dos exhibits 6-K da Rio Tinto.

    LIMITAÇÃO DOCUMENTADA (não contornada por adivinhação): o exhibit
    "Global Operations Review" 4Q2012/FY2012 (accession 0001003297-13-000034)
    traz Benga (65% de participação da Rio Tinto) em DUAS tabelas distintas
    para o mesmo ano-calendário 2012, com valores diferentes para a MESMA
    categoria de carvão:
      - tabela "Rio Tinto share of production", seção "COAL - hard coking":
        linha "Benga (d)", interesse 65%, coluna "Year 2012" = 188 mil t;
        mesma tabela, seção "COAL - thermal": linha "Benga (d)" = 272 mil t.
      - tabela "Rio Tinto operational data", bloco "Rio Tinto Coal
        Mozambique" / "Benga mine (a)", interesse 65.0%: "Hard coking coal
        production ('000 tonnes)" Year 2012 = 289 mil t; "Thermal coal
        production ('000 tonnes)" Year 2012 = 419 mil t.
    Uma nota de rodapé no documento ("Rio Tinto percentage interest shown
    above is at 31 December 2012. The data represent production and sales
    on a 100% basis unless otherwise stated.") aparece entre as duas
    tabelas, mas seu escopo (a que tabela exatamente ela se aplica) não é
    determinável pela diagramação HTML após a quebra de página — não há
    frase no documento que diga explicitamente qual das duas tabelas é a
    produção total da mina (100%) e qual é a fração atribuível à Rio Tinto.
    Sem esse critério textual, este extrator não escolhe uma das duas como
    "o" valor anual — devolve o achado de tabela (para registro em `nota`
    no chamador) e NÃO gera uma linha de valor único no CSV de produção.
    Isso é a aplicação de "nunca inventar" a um caso em que a ambiguidade
    está no próprio documento primário, não na leitura dele.
    """
    try:
        tabelas = _ler_tabelas_html(html_path, match="Benga")
    except ValueError as exc:
        raise ExtracaoFalhou(f"Nenhuma tabela com 'Benga' em {html_path.name}: {exc}") from exc

    achados = []
    for tabela in tabelas:
        texto_tabela = tabela.astype(str).apply(lambda c: c.str.cat(sep=" ")).str.cat(sep=" ")
        if "Benga" not in texto_tabela:
            continue
        achados.append(
            {
                "periodo": periodo,
                "accession": accession,
                "url": url_fonte,
                "tabela_bruta_presente": True,
            }
        )
    if not achados:
        raise ExtracaoFalhou(f"Nenhuma tabela utilizável com 'Benga' em {html_path.name}.")
    return achados


# ---------------------------------------------------------------------------
# Geração do CSV
# ---------------------------------------------------------------------------


def gerar_csv_a_partir_de_raw() -> pd.DataFrame:
    """Gera o DataFrame de saída a partir apenas do que está em data/raw/.

    Nunca inventa valor: se um 20-F esperado não está em data/raw/, a
    variável correspondente permanece "não disponível" com o motivo
    apropriado.
    """
    linhas = []

    arquivos_vale = sorted(DATA_RAW.glob("vale_20f_*.htm")) + sorted(
        DATA_RAW.glob("vale_20f_*.html")
    )
    if not arquivos_vale:
        motivo = "aguarda SEC_USER_AGENT (ver docstring deste script para a política da SEC)"
        for variavel, unidade in [
            ("producao_carvao_total", "Mt/ano"),
            ("producao_carvao_metalurgico", "Mt/ano"),
            ("producao_carvao_termico", "Mt/ano"),
            ("capacidade_nominal", "Mt/ano"),
            ("empregados_mocambique", "pessoas"),
        ]:
            linhas.append(
                {
                    "unidade_geografica": "Mina de Moatize (Vale)",
                    "ano": "",
                    "variavel": variavel,
                    "valor": "não disponível",
                    "unidade_medida": unidade,
                    "selo": "observado",
                    "nivel_fonte": "A",
                    "fonte": (
                        "Vale S.A., Form 20-F (SEC EDGAR, CIK 0000917851), "
                        "2008-2022 — não acessado"
                    ),
                    "metodo": (
                        "pipeline/00_fetch/fetch_vale_20f.py — "
                        "extrair_producao_moatize_vale()"
                    ),
                    "nota": motivo,
                }
            )
    else:
        extraidos: dict[tuple[int, str], dict] = {}
        # Notas (ambiguidade de cabeçalho OU revisão de valor entre filings)
        # encontradas para uma dada (ano, variável), guardadas FORA de
        # `extraidos` para sobreviver a substituições posteriores. Sem isso,
        # um terceiro filing que apenas reconfirma o valor já revisado (sem
        # diferir do imediatamente anterior) sobrescreveria `extraidos[chave]`
        # com um dict novo e apagaria silenciosamente a nota de revisão
        # registrada por um filing intermediário.
        notas_extra: dict[tuple[int, str], list[str]] = {}
        falhas_arquivo: dict[str, str] = {}
        for arquivo in arquivos_vale:
            meta_path = arquivo.with_suffix(arquivo.suffix + ".meta.json")
            meta = json.loads(meta_path.read_text()) if meta_path.exists() else {}
            ano_arquivo = arquivo.name.split("_")[2] if len(arquivo.name.split("_")) > 2 else ""
            try:
                registros = extrair_producao_moatize_vale(
                    arquivo, ano_arquivo, meta.get("accessionNumber", ""), meta.get("url", "")
                )
            except ExtracaoFalhou as exc:
                logger.warning(f"Extração falhou para {arquivo.name}: {exc}")
                falhas_arquivo[ano_arquivo] = str(exc)
                continue
            for r in registros:
                chave = (r["ano"], r["variavel"])
                anterior = extraidos.get(chave)
                if r.get("ambiguo"):
                    # Cabeçalho ambíguo NESTE arquivo para este ano. Nunca
                    # sobrescreve um valor já resolvido por outro filing —
                    # apenas anota a ambiguidade encontrada, num registro
                    # separado que sobrevive a atualizações futuras de
                    # `extraidos[chave]`. Se não há valor melhor ainda,
                    # também guarda a própria ambiguidade como "não
                    # disponível" com o motivo, mas sem "vencer" um filing
                    # mais antigo que já tenha resolvido o mesmo ano sem
                    # ambiguidade.
                    notas_extra.setdefault(chave, []).append(
                        f"[{arquivo.name}] {r['nota_ambiguidade']}"
                    )
                    if anterior is None:
                        r["ano_arquivo_num"] = ano_arquivo
                        extraidos[chave] = r
                    continue
                if anterior is None or int(ano_arquivo) >= int(anterior["ano_arquivo_num"] or 0):
                    if anterior is not None and anterior["valor_mt"] != r["valor_mt"]:
                        notas_extra.setdefault(chave, []).append(
                            f"valor revisado em {arquivo.name}; leitura anterior de "
                            f"{anterior['locator']}: {anterior['valor_mt']} Mt"
                        )
                    r["ano_arquivo_num"] = ano_arquivo
                    extraidos[chave] = r

        for (ano, variavel), r in sorted(extraidos.items()):
            linhas.append(
                {
                    "unidade_geografica": "Mina de Moatize (Vale)",
                    "ano": ano,
                    "variavel": variavel,
                    "valor": r["valor_mt"] if r["valor_mt"] is not None else "não disponível",
                    "unidade_medida": "Mt/ano",
                    "selo": "observado",
                    "nivel_fonte": "A",
                    "fonte": r["locator"],
                    "metodo": (
                        "pipeline/00_fetch/fetch_vale_20f.py — "
                        f"extrair_producao_moatize_vale(): pandas.read_html "
                        f"(parser: {r.get('flavor', 'lxml')}), tabela 'coal "
                        "production' do Form 20-F, alinhamento por índice de "
                        "coluna (não posicional) da linha 'Moatize' × cabeçalho "
                        "de anos; valor publicado pela Vale em milhares de "
                        "toneladas métricas, convertido aqui para Mt/ano "
                        "dividindo por 1.000 (conversão declarada nesta linha); "
                        "base: 100 % da produção da mina, não ajustada à "
                        "participação da Vale (nota de rodapé da tabela no 20-F)"
                    ),
                    "nota": " ".join(
                        n
                        for n in [
                            (
                                "sem produção reportada no filing (célula travessão "
                                "'–') — operação ainda não iniciada ou sem produção "
                                "declarada neste ano"
                                if r["valor_mt"] is None and not notas_extra.get((ano, variavel))
                                else ""
                            ),
                            *notas_extra.get((ano, variavel), []),
                        ]
                        if n
                    ),
                }
            )
        for variavel, unidade in [
            ("producao_carvao_total", "Mt/ano"),
            ("capacidade_nominal", "Mt/ano"),
            ("empregados_mocambique", "pessoas"),
        ]:
            if not any(row["variavel"] == variavel for row in linhas):
                linhas.append(
                    {
                        "unidade_geografica": "Mina de Moatize (Vale)",
                        "ano": "",
                        "variavel": variavel,
                        "valor": "não disponível",
                        "unidade_medida": unidade,
                        "selo": "observado",
                        "nivel_fonte": "A",
                        "fonte": "Vale S.A., Form 20-F (SEC EDGAR, CIK 0000917851)",
                        "metodo": (
                            "pipeline/00_fetch/fetch_vale_20f.py — "
                            "não extraído nesta execução: não há tabela "
                            "equivalente localizada para esta variável"
                        ),
                        "nota": (
                            "extrator cobre produção metalúrgica/térmica; "
                            "capacidade nominal e empregados não têm extração "
                            "implementada nesta versão"
                        ),
                    }
                )

        # Anos cujo 20-F próprio não tem tabela de produção (mina fora de
        # operação, ou ativo já vendido) e que NENHUM outro filing supre por
        # tabela retrospectiva (ex.: FY2011 relista 2009/2010): ficam
        # "não disponível" com o motivo diagnosticado no próprio documento —
        # nunca silenciosamente omitidos do CSV.
        anos_cobertos = {int(ano) for (ano, _v) in extraidos}
        for ano_arquivo, motivo in sorted(falhas_arquivo.items()):
            if not ano_arquivo.isdigit():
                continue
            ano_int = int(ano_arquivo)
            if ano_int in anos_cobertos:
                continue
            for variavel in ("producao_carvao_metalurgico", "producao_carvao_termico"):
                linhas.append(
                    {
                        "unidade_geografica": "Mina de Moatize (Vale)",
                        "ano": ano_int,
                        "variavel": variavel,
                        "valor": "não disponível",
                        "unidade_medida": "Mt/ano",
                        "selo": "observado",
                        "nivel_fonte": "A",
                        "fonte": (
                            f"Vale S.A., Form 20-F referente ao exercício "
                            f"{ano_arquivo} (SEC EDGAR, CIK 0000917851)"
                        ),
                        "metodo": (
                            "pipeline/00_fetch/fetch_vale_20f.py — "
                            "extrair_producao_moatize_vale(): nenhuma tabela de "
                            "produção localizada neste 20-F nem em outro filing "
                            "que reporte retrospectivamente este ano"
                        ),
                        "nota": motivo,
                    }
                )

    arquivos_rt = sorted(DATA_RAW.glob("riotinto_6k_*.htm"))
    if not arquivos_rt:
        linhas.append(
            {
                "unidade_geografica": "Mina de Benga",
                "ano": "",
                "variavel": "producao_carvao_total",
                "valor": "não disponível",
                "unidade_medida": "Mt/ano",
                "selo": "observado",
                "nivel_fonte": "A",
                "fonte": (
                    "Rio Tinto plc, Form 6-K 'Operations Review' (SEC EDGAR, "
                    "CIK 0000863064) — não acessado"
                ),
                "metodo": (
                    "pipeline/00_fetch/fetch_vale_20f.py — "
                    "extrair_producao_benga_riotinto()"
                ),
                "nota": (
                    "aguarda SEC_USER_AGENT (ver docstring deste script "
                    "para a política da SEC)"
                ),
            }
        )
    else:
        linhas.append(
            {
                "unidade_geografica": "Mina de Benga",
                "ano": "",
                "variavel": "producao_carvao_total",
                "valor": "não disponível",
                "unidade_medida": "Mt/ano",
                "selo": "observado",
                "nivel_fonte": "A",
                "fonte": (
                    "Rio Tinto plc, Form 6-K 'Operations Review' (SEC EDGAR, "
                    "CIK 0000863064), accessions "
                    + ", ".join(item["accessionNumber"] for item in RIO_TINTO_OPERATIONS_REVIEWS)
                ),
                "metodo": "pipeline/00_fetch/fetch_vale_20f.py — extrair_producao_benga_riotinto()",
                "nota": (
                    "documentos localizados e baixados; no exhibit 4Q2012/FY2012 "
                    "(accession 0001003297-13-000034) a tabela 'Rio Tinto share of "
                    "production' reporta Benga (65% de participação), ano 2012: "
                    "hard coking coal 188 mil t, thermal coal 272 mil t; a tabela "
                    "'Rio Tinto operational data', mesmo interesse 65,0%, mesmo "
                    "ano, reporta: hard coking coal 289 mil t, thermal coal 419 "
                    "mil t — nenhuma frase do documento identifica qual das duas "
                    "é a produção total da mina (100%) e qual é a fração "
                    "atribuível à Rio Tinto; sem esse critério textual, nenhum "
                    "valor único é publicado. Ver docstring de "
                    "extrair_producao_benga_riotinto()."
                ),
            }
        )

    return pd.DataFrame(linhas, columns=CSV_COLUNAS)


def gravar_csv(df: pd.DataFrame) -> Path:
    df.to_csv(CSV_SAIDA, index=False, encoding="utf-8")
    logger.info(f"CSV escrito em {CSV_SAIDA} ({len(df)} linha(s)).")
    return CSV_SAIDA


def main(argv: list[str] | None = None) -> int:
    import argparse

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--so-extrair",
        action="store_true",
        help=(
            "Pula o download (não requer SEC_USER_AGENT) e apenas regenera "
            "data/processed/economia/producao_moatize_anual.csv a partir do "
            "que já está em data/raw/. Uso: reexecução da extração (A2b/T2) "
            "contra os brutos já espelhados, sem rede."
        ),
    )
    args = parser.parse_args(argv)

    logger.info("Vale S.A. 20-F / Rio Tinto Benga 6-K fetcher — SEC EDGAR")

    if args.so_extrair:
        logger.info("--so-extrair: pulando download; regenerando CSV a partir de data/raw/.")
        df = gerar_csv_a_partir_de_raw()
        gravar_csv(df)
        return 0

    try:
        user_agent = obter_user_agent()
    except SecUserAgentAusente:
        # Ainda regenera o CSV com as linhas "não disponível" a partir do
        # que já estiver em data/raw/ (idempotente mesmo sem rede).
        df = gerar_csv_a_partir_de_raw()
        gravar_csv(df)
        return 2

    try:
        baixados_vale = baixar_20f_vale(user_agent)
        logger.info(f"Vale: {len(baixados_vale)} filing(s) 20-F baixado(s)/verificado(s).")
    except (HTTPError, URLError, RuntimeError) as exc:
        logger.error(f"Falha ao coletar 20-F da Vale: {exc}")
        baixados_vale = []

    try:
        baixados_rt = baixar_6k_rio_tinto(user_agent)
        logger.info(f"Rio Tinto: {len(baixados_rt)} exhibit(s) 6-K baixado(s)/verificado(s).")
    except (HTTPError, URLError, RuntimeError) as exc:
        logger.error(f"Falha ao coletar 6-K da Rio Tinto: {exc}")
        baixados_rt = []

    df = gerar_csv_a_partir_de_raw()
    gravar_csv(df)

    return 0 if (baixados_vale or baixados_rt) else 1


if __name__ == "__main__":
    sys.exit(main())
