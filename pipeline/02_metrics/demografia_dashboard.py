#!/usr/bin/env python3
"""pipeline/02_metrics/demografia_dashboard.py — dashboard de população (§5.3 CLAUDE.md).

Produz `data/processed/demografia_serie_1997_2025.csv`: uma linha por
unidade × ano de população total, mais linhas de CAGR por intervalo e de
índice (base=100), para comparar o ritmo de crescimento de Cidade de Tete e
Distrito de Moatize com o da Província de Tete e o de Moçambique, 1997-2025.

Vila de Moatize entra com um único ponto (2017, `selo=modelado`): estimativa
dasimétrica de terceiros sobre a grade GRID3 (ver
`pipeline/02_metrics/populacao_vila_moatize.py`) — não é contagem, não tem
CAGR (um ponto não faz taxa), e a linha declara isso em `comparabilidade`.

## O que este script FAZ e o que reaproveita (não retranscreve)

- Cidade de Tete e Distrito de Moatize, 2017/2025 (nível A): reaproveita
  `reconstrucao_demografica.montar_nucleo()`.
- Cidade de Tete e Distrito de Moatize, 1997/2007 (nível B/C/ausente):
  reaproveita `reconstrucao_demografica.montar_contexto_b_c()`.
- Vila de Moatize, 2017 (nível A, `selo=modelado`): reaproveita
  `populacao_vila_moatize.estimar()` (nunca recalculado nem retranscrito
  aqui) — estimativa dasimétrica de terceiros (grade GRID3 × máscara
  construída própria, dentro do cluster de Voronoi `moatize_vila`).
- Província de Tete e Moçambique, 2017/2025 (nível A): soma dos ADM2 do
  HDX COD-PS **por nome de província**, nunca por P-code (ver
  `config/unidades.yaml`, esquemas de P-code incompatíveis entre COD-AB e
  COD-PS — MZ10 é Tete no COD-PS e Matutuine/Maputo no COD-AB).
- Província de Tete e Moçambique, 2007 (nível C): parse programático de
  `data/raw/censo2007-tete-quadro3-populacao-por-idade-distrito-2007.html`
  (linha "T O T A L" da província; rodapé "POP_Total(2007)" para o total
  nacional) — nenhum valor transcrito à mão.

## Este CSV NÃO entra em `stats_by_year_by_unit.csv`

Grava diretamente em `data/processed/`, fora do circuito
`data/interim/stats_*.csv` → `stats_by_year_by_unit.py`. O consolidador
reprova nível B/C no núcleo, e continua reprovando — este produto é próprio
do dashboard, com o nível explícito em cada linha (`nivel_fonte`), incluindo
B e C.

## Regras de selo/nível por linha (vinculante)

- População: 2017 = `observado`; 2025 = `modelado` (projeção institucional do
  INE); 1997/2007 = `observado` com o nível B/C/`ausente` que a fonte permite.
- Toda taxa (`cagr_<a>_<b>`) e todo índice (`indice_base_<ano>`) recebe
  `nivel_fonte` = pior nível das duas pontas (A<B<C<ausente) e
  `selo` = o pior selo das duas pontas (observado < interpolado < modelado), o que
  inclui — mas não se resume a — a projeção de 2025,
  senão `observado`. Isso impede que uma taxa 1997→2007 (B→C) apareça como se
  fosse nível A, e que uma taxa que toca 2025 pareça tão observada quanto uma
  que não toca.

Uso: `uv run python pipeline/02_metrics/demografia_dashboard.py`
"""

from __future__ import annotations

import itertools
import re
import sys
import unicodedata
from datetime import UTC, datetime
from pathlib import Path

import pandas as pd

REPO_ROOT = Path(__file__).resolve().parents[2]
DATA_RAW = REPO_ROOT / "data" / "raw"
DATA_PROCESSED = REPO_ROOT / "data" / "processed"
CENSO2007_HTML = DATA_RAW / "censo2007-tete-quadro3-populacao-por-idade-distrito-2007.html"
SAIDA_CSV = DATA_PROCESSED / "demografia_serie_1997_2025.csv"
PROVENANCE_FRAGMENT = REPO_ROOT / "data" / "provenance_parts" / "demografia_dashboard.md"

sys.path.insert(0, str(Path(__file__).resolve().parent))
import populacao_vila_moatize as pvm  # noqa: E402  (estimativa dasimétrica de terceiros)
import reconstrucao_demografica as rd  # noqa: E402  (reaproveita montar_nucleo/contexto)

MARCADOR_INICIO = "<!-- SECAO_DEMOGRAFIA_DASHBOARD_INICIO -->"
MARCADOR_FIM = "<!-- SECAO_DEMOGRAFIA_DASHBOARD_FIM -->"

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
    "comparabilidade",
]

# A é o melhor nível; "ausente" é pior que C. Usado para "pior nível das duas pontas".
NIVEL_RANK = {"A": 0, "B": 1, "C": 2, "ausente": 3}

# Referências institucionais do INE (não do COD-PS) para 2017, já verificadas e
# registradas em `data/provenance_parts/demograficas.md` a partir da brochura
# provincial do INE (quadro "População Residente a 1 de Agosto de 2017"). Usadas
# SÓ para calcular a divergência frente à soma do COD-PS — o valor citado como
# núcleo A é sempre o somado programaticamente abaixo, nunca este.
INE_RESIDENTE_2017_TETE = 2_551_826
INE_RESIDENTE_2017_NACIONAL = 26_899_105
TOLERANCIA_SOMA_PROVINCIAL = 5


# ---------------------------------------------------------------------------
# 1. Soma dos ADM2 do COD-PS por nome de província (nunca por P-code)
# ---------------------------------------------------------------------------


def _normalizar_nome(nome: str) -> str:
    """Normaliza para cruzamento por NOME (§ item 6): caixa, acentuação e espaços
    de borda/internos não podem separar 'Tete' de 'TETE' ou 'Tete ' — o cruzamento
    é por nome, nunca por P-code (esquemas incompatíveis entre COD-AB e COD-PS), e
    'por nome' promete robustez a essas variações triviais, não igualdade literal."""
    sem_acento = (
        unicodedata.normalize("NFKD", str(nome)).encode("ascii", "ignore").decode("ascii")
    )
    return re.sub(r"\s+", " ", sem_acento).strip().casefold()


def somar_adm1(df: pd.DataFrame, provincia: str) -> int:
    """Soma T_TL de todos os ADM2 cujo ADM1_PT normalizado == `provincia`
    normalizado (cruzamento por NOME, nunca por P-code — ver config/unidades.yaml,
    esquemas de P-code incompatíveis entre COD-AB e COD-PS)."""
    alvo = _normalizar_nome(provincia)
    mascara = df["ADM1_PT"].map(_normalizar_nome) == alvo
    return int(df.loc[mascara, "T_TL"].sum())


def somar_nacional(df: pd.DataFrame) -> int:
    return int(df["T_TL"].sum())


# ---------------------------------------------------------------------------
# 2. Parse do HTML do Censo 2007 (província de Tete e total nacional)
# ---------------------------------------------------------------------------


def _texto_censo2007_html() -> str:
    # O documento está em extended-ASCII (não UTF-8) — latin-1 decodifica sem erro.
    return CENSO2007_HTML.read_text(encoding="latin-1")


def parse_provincia_tete_2007() -> int:
    """Lê a célula numérica da linha 'T O T A L' do Quadro 3 (total provincial,
    todos os grupos etários e sexos, área de residência total)."""
    texto = _texto_censo2007_html()
    m = re.search(r"T O T A L</td>\s*<td>([^<]*)</td>", texto)
    if not m:
        raise ValueError(
            f"linha 'T O T A L' não encontrada em {CENSO2007_HTML.relative_to(REPO_ROOT)}"
        )
    return int(re.sub(r"[^0-9]", "", m.group(1)))


def parse_nacional_2007() -> int:
    """Lê o total nacional do rodapé do documento ('POP_Total(2007): 21.802.866 Hab')."""
    texto = _texto_censo2007_html()
    m = re.search(r"POP_Total\(2007\):\s*([0-9.]+)", texto)
    if not m:
        raise ValueError(
            f"'POP_Total(2007)' não encontrado em {CENSO2007_HTML.relative_to(REPO_ROOT)}"
        )
    return int(m.group(1).replace(".", ""))


# ---------------------------------------------------------------------------
# 3. Linhas de população (uma por unidade × ano)
# ---------------------------------------------------------------------------


def _linha(
    unidade: str,
    ano: int,
    valor,
    selo: str,
    nivel: str,
    fonte: str,
    metodo: str,
    nota: str,
    comparabilidade: str,
) -> dict:
    return {
        "familia": "demografia",
        "unidade_geografica": unidade,
        "ano": ano,
        "variavel": "populacao_total_residente",
        "valor": valor,
        "unidade_medida": "pessoas",
        "selo": selo,
        "nivel_fonte": nivel,
        "fonte": fonte,
        "metodo": metodo,
        "nota": nota,
        "comparabilidade": comparabilidade,
    }


def _comparabilidade_ano_unidade(unidade: str, ano: int) -> str:
    if ano == 2025:
        return "projeção INE"
    if unidade == "Distrito de Moatize":
        return "limites do distrito mudaram entre censos — não garantida"
    return "ok"


def montar_ponto_vila_moatize() -> dict:
    """Vila de Moatize, 2017, único ponto — estimativa dasimétrica de terceiros.

    Reaproveita `populacao_vila_moatize.estimar()` (nunca recalcula nem retranscreve o
    número aqui). Correção de `docs/ADR/0017`: NENHUMA variante restrita por máscara de
    construído recupera o observado em Cidade de Tete (desvios de −25% a −74%) — só a
    partição de Voronoi SEM peso de construído valida (+1,61%). O esquema deste CSV
    (`COLUNAS`) não comporta um intervalo por linha, então `valor` carrega o TETO (a
    variante validada, não um "valor central" — não existe valor central publicado
    aqui); `piso`, as quatro variantes restritas e os desvios de validação de cada uma
    vão inteiros para `nota`/`comparabilidade`.
    """
    resultado, _ = pvm.estimar()
    r = resultado["moatize_vila"]
    r_tete = resultado["tete"]
    valor_teto = r["teto"]
    nota = (
        "Estimativa dasimétrica de TERCEIROS, não contagem: soma da grade GRID3 v1.1 "
        "(WorldPop/Southampton, calibrada ao Censo 2017, CC BY 4.0) dentro do cluster de "
        "Voronoi 'moatize_vila' (nenhum limite administrativo aberto para a vila — ver "
        "pipeline/02_metrics/_common.py). `valor` publicado aqui = TETO "
        f"({r['teto']:.0f}) = soma do GRID3 no cluster inteiro, SEM peso de construído — "
        "a ÚNICA variante que validou em Cidade de Tete (ver abaixo); inclui a área "
        "rural do cluster atribuída à sede mais próxima, logo é limite SUPERIOR para a "
        "vila, não um valor central. `piso` = "
        f"{r['piso']:.0f} = menor das quatro variantes restritas por construído "
        "(classificação própria, GHSL, pertença binária, pertença por mediana — corte "
        "por np.quantile, ADR 0014). Variantes individuais: classificação própria "
        f"{r['estimativa_classificacao_propria']:.0f}, GHSL BUILT-S "
        f"{r['estimativa_ghsl_built_s']:.0f}, pertença binária "
        f"{r['estimativa_pertenca_binaria']:.0f}, pertença por mediana "
        f"{r['estimativa_pertenca_mediana']:.0f}. Validação cruzada do MESMO método em "
        f"Cidade de Tete contra os {r_tete['populacao_observada_2017']} habitantes "
        "observados (HDX COD-PS 2017): desvio "
        f"{r_tete['desvio_pct_estimativa_classificacao_propria']:+.1f}% (classificação "
        f"própria), {r_tete['desvio_pct_estimativa_ghsl_built_s']:+.1f}% (GHSL), "
        f"{r_tete['desvio_pct_estimativa_pertenca_binaria']:+.1f}% (pertença binária), "
        f"{r_tete['desvio_pct_estimativa_pertenca_mediana']:+.1f}% (pertença por "
        f"mediana), {r_tete['desvio_pct_diagnostico_sem_peso_construido']:+.1f}% (sem "
        "peso de construído = TETO). TODA variante restrita por construído SUBESTIMA o "
        "observado — o GRID3 já é dasimétrico (calibrado ao Censo 2017) e pesá-lo de "
        "novo pela máscara de construído restringe a população duas vezes. A "
        "estimativa da Vila herda esse viés: o piso publicado é mais provável de "
        "subestimar do que de superestimar a população real. Um único ano — não há "
        "série, não há CAGR."
    )
    return _linha(
        "Vila de Moatize",
        2017,
        round(valor_teto, 1),
        "modelado",
        "A",
        (
            "GRID3 v1.1 MOZ (Bondarenko et al. 2020, WorldPop/Southampton, CC BY 4.0, "
            "calibrado ao Censo 2017) — data/raw/grid3_moz_pop_v1_1_2020_100m_aoi.tif; "
            "`valor` = soma do cluster de Voronoi 'moatize_vila' SEM peso de construído "
            "(teto validado) — ver pipeline/02_metrics/populacao_vila_moatize.py"
        ),
        (
            "soma célula a célula do GRID3 (grade nativa, nunca reprojetada/reamostrada) "
            "no cluster de Voronoi 'moatize_vila' (vizinho mais próximo entre os quatro "
            "pontos-sede, _common.atribuir_unidade_mais_proxima_grade_completa); nenhum "
            "peso de máscara construída aplicado a este valor — variantes restritas por "
            "construído (fração e pertença) publicadas em piso/nota, não em `valor`"
        ),
        nota,
        (
            "estimativa dasimétrica de terceiros, não contagem — `valor` é o TETO da "
            "banda (variante validada em Cidade de Tete, +1,61%), não um valor central; "
            "não comparável a populacao_total_residente de unidades com fonte censitária "
            "direta sem essa ressalva; ver nota para piso e desvio de validação de cada "
            "variante"
        ),
    )


def montar_pontos_populacao() -> list[dict]:
    """Reaproveita `montar_nucleo()` (2017/2025, A) e `montar_contexto_b_c()`
    (1997/2007, B/C/ausente) de `reconstrucao_demografica.py`, e acrescenta
    Província de Tete e Moçambique (soma COD-PS 2017/2025; parse do HTML do
    INE para 2007), e Vila de Moatize (2017, estimativa dasimétrica de terceiros,
    `montar_ponto_vila_moatize()`)."""
    linhas: list[dict] = []

    for linha in rd.montar_nucleo():
        if linha["variavel"] != "populacao_total_residente":
            continue
        unidade = linha["unidade_geografica"]
        ano = linha["ano"]
        linhas.append(
            _linha(
                unidade,
                ano,
                linha["valor"],
                linha["selo"],
                linha["nivel_fonte"],
                linha["fonte"],
                linha["metodo"],
                linha["nota"],
                _comparabilidade_ano_unidade(unidade, ano),
            )
        )

    for linha in rd.montar_contexto_b_c():
        if linha["variavel"] != "populacao_total_residente":
            continue
        unidade = linha["unidade_geografica"]
        ano = linha["ano"]
        valor = linha["valor"]
        linhas.append(
            _linha(
                unidade,
                ano,
                valor,
                linha["selo"],
                linha["nivel_fonte"],
                linha["fonte"],
                linha["metodo"],
                linha["motivo_nao_nucleo"],
                _comparabilidade_ano_unidade(unidade, ano),
            )
        )

    linhas.append(montar_ponto_vila_moatize())

    df2017 = rd.ler_hdx_2017()
    df2025 = rd.ler_hdx_2025()

    soma_prov_2017 = somar_adm1(df2017, "Tete")
    soma_nac_2017 = somar_nacional(df2017)
    soma_prov_2025 = somar_adm1(df2025, "Tete")
    soma_nac_2025 = somar_nacional(df2025)

    diferenca_provincial = soma_prov_2017 - INE_RESIDENTE_2017_TETE
    if abs(diferenca_provincial) > TOLERANCIA_SOMA_PROVINCIAL:
        raise ValueError(
            f"soma provincial 2017 do COD-PS ({soma_prov_2017}) fora da tolerância de "
            f"±{TOLERANCIA_SOMA_PROVINCIAL} frente à 'população residente' do INE "
            f"({INE_RESIDENTE_2017_TETE}) — diferença {diferenca_provincial:+d}. PARE e "
            "reporte; não ajuste esta asserção para fazê-la passar."
        )

    prov_2007 = parse_provincia_tete_2007()
    nac_2007 = parse_nacional_2007()

    fonte_hdx_2017 = (
        "HDX COD-PS (UNFPA/OCHA), vintage 2017, soma dos ADM2 por nome de província — "
        "data/raw/hdx_cod-ps-moz_admpop_adm2_2017_v2.csv"
    )
    fonte_hdx_2025 = (
        "HDX COD-PS (UNFPA/OCHA), vintage 2025, projeção do INE, soma dos ADM2 por nome — "
        "data/raw/hdx_cod-ps-moz_admpop_adm2_2025.csv"
    )
    fonte_html_2007 = (
        "data/raw/censo2007-tete-quadro3-populacao-por-idade-distrito-2007.html "
        "(INE, via Wayback) — parse programático da linha 'T O T A L' (província) e do "
        "rodapé 'POP_Total(2007)' (nacional)"
    )

    diferenca_nacional_2017 = INE_RESIDENTE_2017_NACIONAL - soma_nac_2017
    nota_nacional_2017 = (
        "Decisão do usuário (2026-09-09): total nacional = soma do COD-PS, mesma base "
        "residente dos distritos, não o total 'ajustado' pela sub-enumeração do INE. "
        "Divergência frente à 'população residente a 1 de agosto de 2017' publicada pelo "
        f"INE ({INE_RESIDENTE_2017_NACIONAL}): {diferenca_nacional_2017:+d} pessoas "
        f"(soma COD-PS = {soma_nac_2017})."
    )
    nota_provincial_2017 = (
        f"Confere com a 'população residente' publicada pelo INE ({INE_RESIDENTE_2017_TETE}) "
        f"dentro da tolerância declarada (diferença observada: {diferenca_provincial:+d})."
    )

    linhas.append(
        _linha(
            "Província de Tete",
            2007,
            prov_2007,
            "observado",
            "C",
            fonte_html_2007,
            "contagem censitária (III RGPH 2007), linha 'T O T A L' lida por parse "
            "automático do documento primário (não transcrita à mão)",
            "Sem texto de licença localizável no documento (nível C, §4.0 regra 1); sem "
            "reprocessador A/B alternativo para 2007 no nível provincial.",
            "ok",
        )
    )
    linhas.append(
        _linha(
            "Moçambique",
            2007,
            nac_2007,
            "observado",
            "C",
            fonte_html_2007,
            "contagem censitária (III RGPH 2007), rodapé 'POP_Total(2007)' lido por parse "
            "automático do documento primário (não transcrito à mão)",
            "Sem texto de licença localizável no documento (nível C); sem reprocessador "
            "A/B alternativo para 2007 no nível nacional.",
            "ok",
        )
    )
    linhas.append(
        _linha(
            "Província de Tete",
            2017,
            soma_prov_2017,
            "observado",
            "A",
            fonte_hdx_2017,
            "soma dos T_TL de todos os ADM2 com ADM1_PT == 'Tete' (por nome, nunca por "
            "P-code — MZ10 do COD-PS é Matutuine/Maputo no COD-AB)",
            nota_provincial_2017,
            "ok",
        )
    )
    linhas.append(
        _linha(
            "Moçambique",
            2017,
            soma_nac_2017,
            "observado",
            "A",
            fonte_hdx_2017,
            "soma dos T_TL de todos os ADM2 do COD-PS 2017",
            nota_nacional_2017,
            "ok",
        )
    )
    linhas.append(
        _linha(
            "Província de Tete",
            2025,
            soma_prov_2025,
            "modelado",
            "A",
            fonte_hdx_2025,
            "soma dos T_TL de todos os ADM2 com ADM1_PT == 'Tete', vintage 2025 (projeção "
            "institucional do INE, método interno não publicado)",
            "Projeção, não recontagem — mesma ressalva de circularidade do núcleo 2025 "
            "(ver reconstrucao_demografica.py).",
            "projeção INE",
        )
    )
    linhas.append(
        _linha(
            "Moçambique",
            2025,
            soma_nac_2025,
            "modelado",
            "A",
            fonte_hdx_2025,
            "soma dos T_TL de todos os ADM2 do COD-PS 2025 (projeção institucional do INE)",
            "Projeção, não recontagem — mesma ressalva de circularidade do núcleo 2025.",
            "projeção INE",
        )
    )

    return linhas


# ---------------------------------------------------------------------------
# 4. Taxas (CAGR por intervalo) e índice (base=100), por unidade
# ---------------------------------------------------------------------------


def _pior_selo(*selos: str) -> str:
    """Selo de uma linha derivada: `modelado` se QUALQUER ponta for modelada.

    A primeira versão derivava o selo do ANO (`ano == 2025`), não das pontas. Funcionou
    enquanto a única fonte de valor modelado era a projeção do INE para 2025 — e falhou
    no primeiro caso em que não era: a Vila de Moatize tem um único ponto, 2017, com
    `selo=modelado` (estimativa dasimétrica sobre GRID3), e o seu índice saiu
    `observado`. Um índice de um valor modelado é modelado; o ano não sabe disso, a
    ponta sabe. `interpolado` fica entre os dois: pior que observado, melhor que
    modelado (§10, selo obrigatório em toda série).
    """
    ordem = {"observado": 0, "interpolado": 1, "modelado": 2}
    return max(selos, key=lambda x: ordem.get(str(x), 3))


def _valor_numerico(v) -> float | None:
    if v is None:
        return None
    if isinstance(v, str) and v == "":
        return None
    try:
        if pd.isna(v):
            return None
    except (TypeError, ValueError):
        pass
    return float(v)


def _pior_nivel(a: str, b: str) -> str:
    return max([a, b], key=lambda x: NIVEL_RANK.get(x, 99))


def montar_taxas_e_indices(linhas_populacao: list[dict]) -> list[dict]:
    """Para cada unidade, calcula o índice (base = primeiro ano com valor
    numérico disponível) em todo ano disponível, e o CAGR entre cada par de
    anos consecutivos com valor. Nunca opera sobre pontos sem valor (ex.:
    Distrito de Moatize 1997, nível 'ausente')."""
    saida: list[dict] = []
    df = pd.DataFrame(linhas_populacao)

    for unidade, grupo in df.groupby("unidade_geografica"):
        grupo = grupo.sort_values("ano")
        pontos = [r for _, r in grupo.iterrows() if _valor_numerico(r["valor"]) is not None]
        if not pontos:
            continue

        base = pontos[0]
        base_ano = int(base["ano"])
        base_valor = _valor_numerico(base["valor"])

        for p in pontos:
            ano = int(p["ano"])
            valor = _valor_numerico(p["valor"])
            nivel = _pior_nivel(base["nivel_fonte"], p["nivel_fonte"])
            selo = _pior_selo(base["selo"], p["selo"])
            indice = round(valor / base_valor * 100, 2)
            fonte = p["fonte"] if ano == base_ano else f"{base['fonte']} ; {p['fonte']}"
            saida.append(
                {
                    "familia": "demografia",
                    "unidade_geografica": unidade,
                    "ano": ano,
                    "variavel": f"indice_base_{base_ano}",
                    "valor": indice,
                    "unidade_medida": "índice (base=100)",
                    "selo": selo,
                    "nivel_fonte": nivel,
                    "fonte": fonte,
                    "metodo": f"valor_{ano} / valor_{base_ano} * 100",
                    "nota": (
                        f"base {base_ano} = 100. nível da linha = pior nível entre "
                        f"{base_ano} ({base['nivel_fonte']}) e {ano} ({p['nivel_fonte']})."
                    ),
                    "comparabilidade": p["comparabilidade"],
                }
            )

        for a, b in itertools.pairwise(pontos):
            ano_a, ano_b = int(a["ano"]), int(b["ano"])
            v_a, v_b = _valor_numerico(a["valor"]), _valor_numerico(b["valor"])
            anos = ano_b - ano_a
            taxa = (v_b / v_a) ** (1.0 / anos) - 1.0
            nivel = _pior_nivel(a["nivel_fonte"], b["nivel_fonte"])
            selo = _pior_selo(a["selo"], b["selo"])
            nota = (
                f"CAGR geométrico entre {ano_a} ({a['selo']}, nível {a['nivel_fonte']}) e "
                f"{ano_b} ({b['selo']}, nível {b['nivel_fonte']}): "
                f"(pop_{ano_b}/pop_{ano_a})^(1/{anos})-1. nivel_fonte desta linha é o pior "
                "das duas pontas (A<B<C<ausente)."
            )
            if 2025 in (ano_a, ano_b):
                nota += (
                    " Uma das pontas é projeção institucional (2025) — herda o risco de "
                    "circularidade já registrado em reconstrucao_demografica.py: não usar "
                    "como evidência independente de aceleração/desaceleração."
                )
            saida.append(
                {
                    "familia": "demografia",
                    "unidade_geografica": unidade,
                    "ano": ano_b,
                    "variavel": f"cagr_{ano_a}_{ano_b}",
                    "valor": round(taxa * 100, 3),
                    "unidade_medida": "%/ano",
                    "selo": selo,
                    "nivel_fonte": nivel,
                    "fonte": f"{a['fonte']} ; {b['fonte']}",
                    "metodo": f"CAGR geométrico: (pop_{ano_b}/pop_{ano_a})^(1/{anos})-1",
                    "nota": nota,
                    "comparabilidade": b["comparabilidade"],
                }
            )

    return saida


# ---------------------------------------------------------------------------
# 5. Gravação e proveniência
# ---------------------------------------------------------------------------


def gravar_csv(linhas: list[dict], caminho: Path) -> None:
    caminho.parent.mkdir(parents=True, exist_ok=True)
    df = pd.DataFrame(linhas)
    for coluna in COLUNAS:
        if coluna not in df.columns:
            df[coluna] = ""
    df = df[COLUNAS].sort_values(["unidade_geografica", "variavel", "ano"])
    df.to_csv(caminho, index=False)


def gravar_provenance_fragment(resumo: dict) -> None:
    texto = f"""{MARCADOR_INICIO}
## Dashboard de população 1997-2025 (§5.3, Frente A)

Script: `pipeline/02_metrics/demografia_dashboard.py`.
Gerado em {datetime.now(UTC).date().isoformat()}.

Produz `data/processed/demografia_serie_1997_2025.csv`: uma linha por unidade
× ano de população, mais linhas `cagr_<a>_<b>` e `indice_base_<ano>` por
unidade. **Não entra em `stats_by_year_by_unit.csv`** — grava direto em
`data/processed/`, fora do circuito de fragmentos/consolidador; carrega nível
A, B, C e `ausente` lado a lado, cada linha com o seu.

Unidades: Cidade de Tete, Distrito de Moatize (reaproveitados de
`reconstrucao_demografica.montar_nucleo()`/`montar_contexto_b_c()`, sem
retranscrição), Província de Tete e Moçambique (soma dos ADM2 do HDX
COD-PS por nome de província 2017/2025; parse programático do HTML do
Censo 2007 do INE para 2007), e Vila de Moatize — um único ponto (2017,
`selo=modelado`, `nivel_fonte=A` mas fonte GRID3, não HDX COD-PS: estimativa
dasimétrica de terceiros, reaproveitada de
`populacao_vila_moatize.estimar()`, nunca contagem; sem CAGR — um ponto não
faz taxa; piso/teto e o desvio da validação cruzada em Cidade de Tete vão na
`nota`. Ver `data/processed/populacao_vila_moatize_sensibilidade.csv` e
`data/provenance_parts/populacao_vila_moatize.md`.

### Somas verificadas nesta execução

| unidade | 2017 (soma COD-PS) | 2025 (soma COD-PS) |
|---|---|---|
| Província de Tete | {resumo["soma_prov_2017"]} | {resumo["soma_prov_2025"]} |
| Moçambique | {resumo["soma_nac_2017"]} | {resumo["soma_nac_2025"]} |

Soma provincial 2017 confere com a "população residente" publicada pelo INE
(2.551.826) dentro de ±{TOLERANCIA_SOMA_PROVINCIAL} (diferença observada:
{resumo["diferenca_provincial"]:+d}). Soma nacional 2017 diverge da
"população residente" publicada pelo INE (26.899.105) em
{resumo["diferenca_nacional"]:+d} pessoas — divergência esperada e
documentada em cada linha nacional do CSV (decisão do usuário de 2026-09-09:
usar a soma do COD-PS, não o total do INE, como base nacional).

### Regras de selo/nível aplicadas

População: 2017 observado/A; 2025 modelado/A; 1997/2007 observado com
nível B, C ou `ausente` conforme a fonte disponível para a unidade. Toda
linha `cagr_*`/`indice_base_*` carrega `nivel_fonte` = pior nível das duas
pontas e `selo` = **pior selo das duas pontas** (`_pior_selo`: `modelado` se
qualquer ponta for `modelado`; `interpolado` se nenhuma for `modelado` mas
alguma for `interpolado`; `observado` só se as duas forem). Não é uma regra
em função do ANO: a primeira versão desta regra dizia `selo = modelado`
sempre que uma ponta fosse 2025, e coincidia com o executado enquanto a
única origem de valor modelado fosse a projeção do INE para 2025 — errou no
primeiro caso em que não era, a Vila de Moatize (2017, `selo=modelado` por
ser estimativa dasimétrica sobre GRID3, não por ser 2025), cujo índice teria
saído `observado` pela regra por ano.

{MARCADOR_FIM}
"""
    PROVENANCE_FRAGMENT.write_text(texto, encoding="utf-8")


# ---------------------------------------------------------------------------


def main() -> int:
    pontos = montar_pontos_populacao()

    df2017 = rd.ler_hdx_2017()
    df2025 = rd.ler_hdx_2025()
    soma_prov_2017 = somar_adm1(df2017, "Tete")
    soma_nac_2017 = somar_nacional(df2017)
    soma_prov_2025 = somar_adm1(df2025, "Tete")
    soma_nac_2025 = somar_nacional(df2025)

    taxas_indices = montar_taxas_e_indices(pontos)

    linhas = pontos + taxas_indices
    gravar_csv(linhas, SAIDA_CSV)
    print(
        f"[ok] {SAIDA_CSV.relative_to(REPO_ROOT)} ({len(linhas)} linhas, "
        f"{len(pontos)} de população, {len(taxas_indices)} de taxa/índice)",
        file=sys.stderr,
    )

    resumo = {
        "soma_prov_2017": soma_prov_2017,
        "soma_prov_2025": soma_prov_2025,
        "soma_nac_2017": soma_nac_2017,
        "soma_nac_2025": soma_nac_2025,
        "diferenca_provincial": soma_prov_2017 - INE_RESIDENTE_2017_TETE,
        "diferenca_nacional": INE_RESIDENTE_2017_NACIONAL - soma_nac_2017,
    }
    gravar_provenance_fragment(resumo)
    print(f"[ok] {PROVENANCE_FRAGMENT.relative_to(REPO_ROOT)}", file=sys.stderr)

    print(
        f"[resumo] soma provincial 2017={soma_prov_2017} 2025={soma_prov_2025}; "
        f"soma nacional 2017={soma_nac_2017} 2025={soma_nac_2025}",
        file=sys.stderr,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
