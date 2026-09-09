"""Contratos sobre a reconstrução demográfica (§5.3, §10).

Propósito: garantir que (1) toda série do núcleo demográfico carrega selo, (2)
só nível A entra em `stats_by_year_by_unit.csv`, (3) os pontos de nível B/C
ficam de fora do núcleo, em arquivo à parte e claramente rotulados, e (4) o
teste de sensibilidade da dasimetria existe e é interpretável.

Entradas: `data/processed/stats_by_year_by_unit.csv`,
`data/processed/demografia_contexto_nao_nucleo.csv`,
`data/processed/populacao_dasimetrica_sensibilidade.csv`.
Saídas: nenhuma (só asserções). Testes pulam se os artefatos ainda não
existirem (`reconstrucao_demografica.py` não roda automaticamente em pytest).
"""

from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd
import pytest

ROOT = Path(__file__).resolve().parents[2]
PROCESSED = ROOT / "data" / "processed"
STATS_CSV = PROCESSED / "stats_by_year_by_unit.csv"
CONTEXTO_CSV = PROCESSED / "demografia_contexto_nao_nucleo.csv"
SENSIB_CSV = PROCESSED / "populacao_dasimetrica_sensibilidade.csv"

SELOS_VALIDOS = {"observado", "interpolado", "modelado"}

sys.path.insert(0, str(ROOT / "pipeline" / "02_metrics"))


def _valores_hdx_observados_e_modelados() -> dict[tuple[str, int], int]:
    """Lê `data/raw/hdx_cod-ps-moz_admpop_adm2_2017_v2.csv`/`_2025.csv` em tempo de
    execução — nunca transcrito à mão (armadilha já paga duas vezes nesta sessão,
    ver `pipeline/02_metrics/populacao_vila_moatize.py`). Reaproveita
    `reconstrucao_demografica.UNIDADES_HDX`/`ler_hdx_2017`/`ler_hdx_2025`, a mesma
    leitura que produz `stats_by_year_by_unit.csv`, para que o contrato meça o
    pipeline contra a fonte primária, não contra um valor congelado que envelhece
    com o dado e passa a defender o erro."""
    import reconstrucao_demografica as rd

    df2017 = rd.ler_hdx_2017()
    df2025 = rd.ler_hdx_2025()
    esperado: dict[tuple[str, int], int] = {}
    for unidade, chaves in rd.UNIDADES_HDX.items():
        linha_2017 = df2017[df2017["ADM2_PT"] == chaves["nome_2017"]]
        linha_2025 = df2025[df2025["ADM2_PT"] == chaves["nome_2025"]]
        if not linha_2017.empty:
            esperado[(unidade, 2017)] = int(linha_2017.iloc[0]["T_TL"])
        if not linha_2025.empty:
            esperado[(unidade, 2025)] = int(linha_2025.iloc[0]["T_TL"])
    return esperado


@pytest.fixture(scope="module")
def valores_hdx() -> dict[tuple[str, int], int]:
    caminho_2017 = ROOT / "data" / "raw" / "hdx_cod-ps-moz_admpop_adm2_2017_v2.csv"
    caminho_2025 = ROOT / "data" / "raw" / "hdx_cod-ps-moz_admpop_adm2_2025.csv"
    if not (caminho_2017.exists() and caminho_2025.exists()):
        pytest.skip(f"{caminho_2017} e/ou {caminho_2025} ainda não baixados")
    return _valores_hdx_observados_e_modelados()


def _skip_se_ausente(path: Path):
    if not path.exists():
        pytest.skip(
            f"{path} ainda não gerado — rode pipeline/02_metrics/reconstrucao_demografica.py"
        )


@pytest.fixture(scope="module")
def stats_demografia() -> pd.DataFrame:
    _skip_se_ausente(STATS_CSV)
    df = pd.read_csv(STATS_CSV)
    return df[df["familia"] == "demografia"].copy()


@pytest.fixture(scope="module")
def contexto() -> pd.DataFrame:
    _skip_se_ausente(CONTEXTO_CSV)
    return pd.read_csv(CONTEXTO_CSV)


@pytest.fixture(scope="module")
def sensibilidade() -> pd.DataFrame:
    _skip_se_ausente(SENSIB_CSV)
    return pd.read_csv(SENSIB_CSV)


# ---------------------------------------------------------------------------
# Núcleo: stats_by_year_by_unit.csv
# ---------------------------------------------------------------------------


def test_toda_linha_do_nucleo_tem_selo_valido(stats_demografia):
    assert not stats_demografia.empty
    assert stats_demografia["selo"].notna().all()
    assert set(stats_demografia["selo"].unique()) <= SELOS_VALIDOS


def test_nucleo_so_contem_nivel_a(stats_demografia):
    """§4.0 regra 1: só nível A sustenta número publicado no núcleo."""
    assert set(stats_demografia["nivel_fonte"].unique()) == {"A"}


def test_nucleo_tem_apenas_2017_e_2025_sem_interpolacao(stats_demografia):
    """Dois pontos não fazem série: nenhum ano entre 2018 e 2024 pode aparecer
    como população interpolada/modelada no núcleo demográfico."""
    anos = set(stats_demografia["ano"].unique())
    assert anos <= {2017, 2025}
    assert not any(2018 <= a <= 2024 for a in anos)


def test_ano_2017_e_observado_ano_2025_e_modelado(stats_demografia):
    pop_2017 = stats_demografia[
        (stats_demografia["ano"] == 2017)
        & (stats_demografia["variavel"] == "populacao_total_residente")
    ]
    pop_2025 = stats_demografia[
        (stats_demografia["ano"] == 2025)
        & (stats_demografia["variavel"] == "populacao_total_residente")
    ]
    assert (pop_2017["selo"] == "observado").all()
    assert (pop_2025["selo"] == "modelado").all()


def test_valores_batem_com_ancoras_hdx(stats_demografia, valores_hdx):
    pop = stats_demografia[stats_demografia["variavel"] == "populacao_total_residente"]
    for (unidade, ano), valor in valores_hdx.items():
        linha = pop[(pop["unidade_geografica"] == unidade) & (pop["ano"] == ano)]
        assert len(linha) == 1, f"esperava 1 linha para {unidade}/{ano}, achou {len(linha)}"
        assert int(linha.iloc[0]["valor"]) == valor


def test_cagr_e_marcado_modelado_com_ressalva_de_circularidade(stats_demografia):
    cagr = stats_demografia[stats_demografia["variavel"] == "cagr_2017_2025"]
    assert not cagr.empty
    assert (cagr["selo"] == "modelado").all()
    assert cagr["nota"].str.contains("circularidade", case=False).all()


# ---------------------------------------------------------------------------
# Contexto B/C: nunca no núcleo
# ---------------------------------------------------------------------------


def test_contexto_so_tem_nivel_b_c_ou_ausente(contexto):
    assert set(contexto["nivel_fonte"].unique()) <= {"B", "C", "ausente"}
    assert "A" not in set(contexto["nivel_fonte"].unique())


def test_pontos_de_contexto_nao_aparecem_no_nucleo(stats_demografia, contexto):
    """Nenhum (unidade, ano) do contexto B/C pode reaparecer no núcleo A com o
    mesmo par — 1997 e 2007 devem estar ausentes de stats_by_year_by_unit.csv."""
    pares_contexto = set(zip(contexto["unidade_geografica"], contexto["ano"], strict=True))
    pares_nucleo = set(
        zip(stats_demografia["unidade_geografica"], stats_demografia["ano"], strict=True)
    )
    assert pares_contexto.isdisjoint(pares_nucleo)


def test_contexto_declara_motivo_de_exclusao(contexto):
    assert contexto["motivo_nao_nucleo"].notna().all()
    assert (contexto["motivo_nao_nucleo"].str.len() > 10).all()


# ---------------------------------------------------------------------------
# Dasimetria: teste de sensibilidade
# ---------------------------------------------------------------------------


def test_sensibilidade_tem_ao_menos_dois_pesos_aplicaveis(sensibilidade):
    aplicaveis = sensibilidade[sensibilidade["aplicavel"] == True]  # noqa: E712
    metodos = set(aplicaveis["metodo_peso"]) & {
        "classificacao_propria",
        "ghsl_built_s",
        "wsf_evolution",
    }
    assert len(metodos) >= 2


def test_sensibilidade_preserva_populacao_total_por_construcao(sensibilidade, valores_hdx):
    linhas = sensibilidade[
        sensibilidade["metodo_peso"].isin(
            ["classificacao_propria", "ghsl_built_s", "wsf_evolution"]
        )
    ]
    linhas = linhas[linhas["aplicavel"] == True]  # noqa: E712
    assert linhas["populacao_total_distribuida"].nunique() == 1
    assert int(linhas["populacao_total_distribuida"].iloc[0]) == valores_hdx[
        ("Cidade de Tete", 2017)
    ]


def test_sensibilidade_selo_modelado_nivel_a(sensibilidade):
    linhas = sensibilidade[sensibilidade["aplicavel"] == True]  # noqa: E712
    linhas_com_selo = linhas[linhas["selo"].notna() & (linhas["selo"] != "")]
    assert not linhas_com_selo.empty
    assert set(linhas_com_selo["selo"].unique()) <= SELOS_VALIDOS
    assert set(linhas_com_selo["nivel_fonte"].unique()) <= {"A"}


def test_densidade_implicada_varia_entre_pesos(sensibilidade):
    """A razão de ser deste teste é justamente mostrar que o peso importa —
    se todos os pesos dessem a mesma densidade, o teste de sensibilidade não
    estaria testando nada."""
    linhas = sensibilidade[
        sensibilidade["metodo_peso"].isin(
            ["classificacao_propria", "ghsl_built_s", "wsf_evolution"]
        )
    ]
    linhas = linhas[linhas["aplicavel"] == True]  # noqa: E712
    densidades = linhas["densidade_implicada_hab_km2"].dropna()
    if len(densidades) >= 2:
        assert densidades.max() / densidades.min() > 1.1


# ---------------------------------------------------------------------------
# Dashboard demográfico 1997-2025 (Frente A1 do plano; demografia_dashboard.py)
# ---------------------------------------------------------------------------

DASHBOARD_CSV = PROCESSED / "demografia_serie_1997_2025.csv"
NIVEL_RANK = {"A": 0, "B": 1, "C": 2, "ausente": 3}


def _pior_nivel(a: str, b: str) -> str:
    return max([a, b], key=lambda x: NIVEL_RANK.get(x, 99))


@pytest.fixture(scope="module")
def dashboard() -> pd.DataFrame:
    _skip_se_ausente(DASHBOARD_CSV)
    return pd.read_csv(DASHBOARD_CSV)


def test_dashboard_soma_provincial_2017_confere_com_ine(dashboard):
    linha = dashboard[
        (dashboard["unidade_geografica"] == "Província de Tete")
        & (dashboard["ano"] == 2017)
        & (dashboard["variavel"] == "populacao_total_residente")
    ]
    assert len(linha) == 1
    assert abs(float(linha.iloc[0]["valor"]) - 2_551_826) <= 5


def test_dashboard_nenhuma_linha_a_cita_ine_diretamente_na_fonte(dashboard):
    """§4.0 regra 1 / data/DATA_AUDIT.md §0: o INE é mencionável em prosa (é a 'fonte
    declarada' dentro dos metadados do HDX), mas a citação de uma linha nível A tem de
    apontar para o HDX COD-PS ou para o GRID3 (Vila de Moatize — outro produtor
    institucional de nível A, ver `data/provenance_parts/worldpop_grid3.md`), nunca
    para o documento/URL do INE diretamente — o documento primário do INE (ex.: o HTML
    do Censo 2007) é nível C, não A."""
    nivel_a = dashboard[dashboard["nivel_fonte"] == "A"]
    nivel_a = nivel_a[nivel_a["unidade_geografica"] != "Vila de Moatize"]
    assert not nivel_a.empty
    fonte = nivel_a["fonte"].fillna("")
    assert (fonte.str.contains("HDX COD-PS", case=False)).all()
    assert not fonte.str.contains("censo2007", case=False).any()
    assert not fonte.str.contains(r"ine\.gov\.mz", case=False, regex=True).any()


def test_dashboard_taxa_carrega_pior_nivel_das_pontas(dashboard):
    taxas = dashboard[dashboard["variavel"].str.startswith("cagr_", na=False)]
    assert not taxas.empty
    pop = dashboard[dashboard["variavel"] == "populacao_total_residente"]
    for _, linha in taxas.iterrows():
        _, ano_a, ano_b = linha["variavel"].split("_")
        ano_a, ano_b = int(ano_a), int(ano_b)
        unidade = linha["unidade_geografica"]
        p_a = pop[(pop["unidade_geografica"] == unidade) & (pop["ano"] == ano_a)]
        p_b = pop[(pop["unidade_geografica"] == unidade) & (pop["ano"] == ano_b)]
        assert len(p_a) == 1 and len(p_b) == 1, f"{unidade}/{ano_a}-{ano_b}: pontos ausentes"
        esperado = _pior_nivel(p_a.iloc[0]["nivel_fonte"], p_b.iloc[0]["nivel_fonte"])
        assert linha["nivel_fonte"] == esperado, (
            f"{unidade}/{linha['variavel']}: nivel_fonte {linha['nivel_fonte']!r} != "
            f"pior nível esperado {esperado!r} "
            f"({ano_a}={p_a.iloc[0]['nivel_fonte']}, {ano_b}={p_b.iloc[0]['nivel_fonte']})"
        )


def test_dashboard_toda_linha_de_2025_e_modelado(dashboard):
    linhas_2025 = dashboard[dashboard["ano"] == 2025]
    assert not linhas_2025.empty
    assert (linhas_2025["selo"] == "modelado").all()


def test_dashboard_linhas_bc_nao_aparecem_no_nucleo(dashboard, stats_demografia):
    bc = dashboard[dashboard["nivel_fonte"].isin(["B", "C", "ausente"])]
    assert not bc.empty
    pares_bc = set(zip(bc["unidade_geografica"], bc["ano"], bc["variavel"], strict=True))
    pares_nucleo = set(
        zip(
            stats_demografia["unidade_geografica"],
            stats_demografia["ano"],
            stats_demografia["variavel"],
            strict=True,
        )
    )
    assert pares_bc.isdisjoint(pares_nucleo)


def test_dashboard_cagr_recalculado_bate_com_publicado(dashboard):
    taxas = dashboard[dashboard["variavel"].str.startswith("cagr_", na=False)]
    pop = dashboard[dashboard["variavel"] == "populacao_total_residente"]
    assert not taxas.empty
    for _, linha in taxas.iterrows():
        _, ano_a, ano_b = linha["variavel"].split("_")
        ano_a, ano_b = int(ano_a), int(ano_b)
        unidade = linha["unidade_geografica"]
        p_a = pop[(pop["unidade_geografica"] == unidade) & (pop["ano"] == ano_a)].iloc[0]
        p_b = pop[(pop["unidade_geografica"] == unidade) & (pop["ano"] == ano_b)].iloc[0]
        v_a, v_b = float(p_a["valor"]), float(p_b["valor"])
        anos = ano_b - ano_a
        recalculado = round(((v_b / v_a) ** (1.0 / anos) - 1.0) * 100, 3)
        assert abs(recalculado - float(linha["valor"])) < 0.001, (
            f"{unidade}/{linha['variavel']}: publicado {linha['valor']}, "
            f"recalculado {recalculado}"
        )


# ---------------------------------------------------------------------------
# Vila de Moatize (populacao_vila_moatize.py) — estimativa dasimétrica de terceiros
# ---------------------------------------------------------------------------

VILA_SENSIB_CSV = PROCESSED / "populacao_vila_moatize_sensibilidade.csv"


@pytest.fixture(scope="module")
def vila_sensibilidade() -> pd.DataFrame:
    _skip_se_ausente(VILA_SENSIB_CSV)
    return pd.read_csv(VILA_SENSIB_CSV)


def test_vila_moatize_tem_exatamente_um_ano_no_dashboard(dashboard):
    vila = dashboard[dashboard["unidade_geografica"] == "Vila de Moatize"]
    assert not vila.empty
    anos = set(vila["ano"].unique())
    assert anos == {2017}, f"Vila de Moatize tem de ter só o ano 2017, achou {anos}"


def test_vila_moatize_nunca_tem_cagr(dashboard):
    """Um ponto não faz taxa — nenhuma linha `cagr_*` pode existir para a vila."""
    vila = dashboard[dashboard["unidade_geografica"] == "Vila de Moatize"]
    cagr_vila = vila[vila["variavel"].str.startswith("cagr_", na=False)]
    assert cagr_vila.empty, (
        f"Vila de Moatize não pode ter CAGR (um ponto não faz taxa); achou "
        f"{len(cagr_vila)} linha(s): {cagr_vila['variavel'].tolist()}"
    )


def test_vila_moatize_populacao_residente_e_modelada_nivel_a(dashboard):
    pop = dashboard[
        (dashboard["unidade_geografica"] == "Vila de Moatize")
        & (dashboard["variavel"] == "populacao_total_residente")
    ]
    assert len(pop) == 1
    assert pop.iloc[0]["selo"] == "modelado"
    assert pop.iloc[0]["nivel_fonte"] == "A"
    assert "estimativa dasimétrica" in str(pop.iloc[0]["comparabilidade"]).lower()


def test_vila_moatize_piso_menor_ou_igual_estimativa_menor_ou_igual_teto(vila_sensibilidade):
    """piso <= cada variante restrita <= teto, para a Vila. Não há valor central
    publicado (docs/ADR/0017): a banda é [piso, teto], e o valor gravado no
    dashboard (`demografia_serie_1997_2025.csv`) é o TETO, não uma média — este
    contrato só verifica que as variantes ficam dentro da banda, nunca fora dela."""
    vila = vila_sensibilidade[vila_sensibilidade["unidade_geografica"] == "Vila de Moatize"]
    piso_teto = vila[vila["metodo_peso"] == "piso_teto"]
    assert len(piso_teto) == 1
    piso = float(piso_teto.iloc[0]["piso"])
    teto = float(piso_teto.iloc[0]["teto"])
    assert piso <= teto

    estimativas = vila[
        vila["metodo_peso"].isin(["classificacao_propria", "ghsl_built_s"])
    ]["estimativa_populacao"].astype(float)
    assert not estimativas.empty
    assert (estimativas >= piso - 1e-6).all()
    assert (estimativas <= teto + 1e-6).all()


def test_validacao_cruzada_tete_esta_publicada(vila_sensibilidade, valores_hdx):
    """O desvio percentual medido em Cidade de Tete (mesmo método aplicado a uma
    unidade com população observada) tem de estar publicado — é ele que diz quanto
    confiar no número da Vila, não um limiar de aprovação."""
    validacao = vila_sensibilidade[
        (vila_sensibilidade["unidade_geografica"] == "Cidade de Tete")
        & (vila_sensibilidade["metodo_peso"] == "validacao_cruzada")
    ]
    assert len(validacao) == 1
    linha = validacao.iloc[0]
    assert pd.notna(linha["populacao_observada_2017"])
    assert int(linha["populacao_observada_2017"]) == valores_hdx[("Cidade de Tete", 2017)]
    assert pd.notna(linha["desvio_pct_classificacao_propria"])
    assert pd.notna(linha["desvio_pct_ghsl_built_s"])


def test_vila_moatize_todas_variantes_entre_piso_e_teto(vila_sensibilidade):
    """Estende o contrato anterior às quatro variantes restritas por construído
    (fração própria, fração GHSL, pertença binária, pertença por mediana): todas têm
    de estar entre piso e teto publicados — nenhuma pode escapar da banda."""
    vila = vila_sensibilidade[vila_sensibilidade["unidade_geografica"] == "Vila de Moatize"]
    piso_teto = vila[vila["metodo_peso"] == "piso_teto"]
    assert len(piso_teto) == 1
    piso = float(piso_teto.iloc[0]["piso"])
    teto = float(piso_teto.iloc[0]["teto"])
    assert piso <= teto

    variantes_restritas = vila[
        vila["metodo_peso"].isin(
            ["classificacao_propria", "ghsl_built_s", "pertenca_binaria", "pertenca_mediana"]
        )
    ]["estimativa_populacao"].astype(float)
    assert len(variantes_restritas) == 4
    assert (variantes_restritas >= piso - 1e-6).all()
    assert (variantes_restritas <= teto + 1e-6).all()


def test_vila_moatize_teto_e_a_variante_sem_peso_de_construido(vila_sensibilidade):
    """O teto tem de ser exatamente a variante 'sem peso de construído' (partição de
    Voronoi pura) — não a maior das variantes pesadas, não uma média, não nenhum outro
    valor. É essa igualdade que torna o teto a variante VALIDADA, não arbitrária."""
    vila = vila_sensibilidade[vila_sensibilidade["unidade_geografica"] == "Vila de Moatize"]
    piso_teto = vila[vila["metodo_peso"] == "piso_teto"].iloc[0]
    sem_peso = vila[vila["metodo_peso"] == "diagnostico_sem_peso_construido"].iloc[0]
    assert abs(float(piso_teto["teto"]) - float(sem_peso["estimativa_populacao"])) < 1e-6


def test_vila_moatize_piso_e_o_minimo_das_variantes_restritas(vila_sensibilidade):
    """O piso tem de ser o MENOR das quatro variantes restritas por construído — nunca
    incluir a variante sem peso (que é o teto por definição, não uma restrição)."""
    vila = vila_sensibilidade[vila_sensibilidade["unidade_geografica"] == "Vila de Moatize"]
    piso_teto = vila[vila["metodo_peso"] == "piso_teto"].iloc[0]
    variantes_restritas = vila[
        vila["metodo_peso"].isin(
            ["classificacao_propria", "ghsl_built_s", "pertenca_binaria", "pertenca_mediana"]
        )
    ]["estimativa_populacao"].astype(float)
    assert abs(float(piso_teto["piso"]) - variantes_restritas.min()) < 1e-6


def test_validacao_cruzada_publica_desvio_de_cada_variante(vila_sensibilidade):
    """Toda variante medida (as quatro restritas + a sem peso) tem o desvio de
    validação em Cidade de Tete publicado — nenhuma pode ficar de fora da linha
    `validacao_cruzada`, nem mesmo a que valida bem."""
    validacao = vila_sensibilidade[
        (vila_sensibilidade["unidade_geografica"] == "Cidade de Tete")
        & (vila_sensibilidade["metodo_peso"] == "validacao_cruzada")
    ]
    assert len(validacao) == 1
    linha = validacao.iloc[0]
    for coluna in (
        "desvio_pct_classificacao_propria",
        "desvio_pct_ghsl_built_s",
        "desvio_pct_pertenca_binaria",
        "desvio_pct_pertenca_mediana",
        "desvio_pct_diagnostico_sem_peso",
    ):
        assert coluna in linha.index, f"coluna {coluna} ausente da linha validacao_cruzada"
        assert pd.notna(linha[coluna]), f"{coluna} está vazio na linha validacao_cruzada"


def test_vila_moatize_corte_pertenca_mediana_vem_de_quantile():
    """ADR 0014 (sétima ocorrência): o corte da variante (c) tem de ser um QUANTIL
    (`np.quantile` sobre as células do próprio cluster com fração > 0), nunca um
    limiar absoluto fixado a priori. Verificado no código-fonte, não no resultado
    numérico (um valor fixo por acaso igual à mediana passaria num teste numérico)."""
    fonte = (ROOT / "pipeline" / "02_metrics" / "populacao_vila_moatize.py").read_text(
        encoding="utf-8"
    )
    assert "np.quantile(presentes, 0.5)" in fonte, (
        "o corte da pertença por mediana precisa vir de np.quantile sobre as células "
        "com fração > 0 do próprio cluster, não de um limiar absoluto"
    )
    # nenhuma comparação de fração contra um número decimal fixo fora do quantil
    # (ex.: `peso_own >= 0.5`) — a única comparação permitida é contra a variável
    # calculada por quantile.
    assert "peso_own >= 0.5" not in fonte
    assert "peso_cluster >= 0.5" not in fonte


def test_vila_moatize_nenhuma_linha_afirma_valor_central(dashboard):
    """O dashboard tem de deixar explícito que `valor` é o TETO da banda, não um
    valor central, e a linha de sensibilidade `piso_teto` tem de negar
    explicitamente a existência de um valor central."""
    vila = dashboard[
        (dashboard["unidade_geografica"] == "Vila de Moatize")
        & (dashboard["variavel"] == "populacao_total_residente")
    ]
    assert len(vila) == 1
    comparabilidade = str(vila.iloc[0]["comparabilidade"]).lower()
    assert "não é um valor central" in comparabilidade or "não um valor central" in comparabilidade

    sensib = pd.read_csv(VILA_SENSIB_CSV)
    piso_teto = sensib[
        (sensib["unidade_geografica"] == "Vila de Moatize") & (sensib["metodo_peso"] == "piso_teto")
    ]
    assert len(piso_teto) == 1
    nota = str(piso_teto.iloc[0]["nota_metodo"]).lower()
    assert "nenhum valor central" in nota


def test_selo_de_linha_derivada_e_o_pior_selo_das_pontas():
    """Índice e CAGR são linhas DERIVADAS: o seu selo tem de vir das pontas.

    A primeira versão derivava o selo do ANO (`ano == 2025 -> modelado`). A regra
    coincidia com a correta enquanto a única origem de valor modelado era a projeção do
    INE para 2025 — e errou no primeiro caso em que não era: a Vila de Moatize tem um
    único ponto, 2017, `selo=modelado` (dasimetria sobre GRID3), e o seu
    `indice_base_2017` saiu **observado**. Um índice de um valor modelado é modelado.

    O contrato compara cada linha derivada com os selos das linhas de população que a
    originaram, lidas do MESMO CSV em tempo de execução — nenhum selo esperado é
    escrito aqui.
    """
    import csv as _csv

    caminho = PROCESSED / "demografia_serie_1997_2025.csv"
    if not caminho.exists():
        pytest.skip("demografia_serie_1997_2025.csv ainda não gerado")
    with caminho.open(encoding="utf-8", newline="") as fh:
        linhas = list(_csv.DictReader(fh))

    ordem = {"observado": 0, "interpolado": 1, "modelado": 2}
    selo_pop = {
        (x["unidade_geografica"], int(x["ano"])): x["selo"]
        for x in linhas
        if x["variavel"] == "populacao_total_residente"
    }

    erros = []
    for x in linhas:
        var = x["variavel"]
        unidade, ano = x["unidade_geografica"], int(x["ano"])
        if var.startswith("indice_base_"):
            pontas = (int(var.rsplit("_", 1)[1]), ano)
        elif var.startswith("cagr_"):
            a, b = var.split("_")[1:3]
            pontas = (int(a), int(b))
        else:
            continue
        selos = [selo_pop.get((unidade, p)) for p in pontas]
        if any(s is None for s in selos):
            erros.append(f"{unidade} {ano} {var}: ponta sem linha de população")
            continue
        esperado = max(selos, key=lambda s: ordem.get(s, 3))
        if x["selo"] != esperado:
            erros.append(
                f"{unidade} {ano} {var}: selo '{x['selo']}' mas as pontas "
                f"{pontas} têm {selos} — o pior é '{esperado}'"
            )
    assert not erros, "selo de linha derivada não bate com as pontas:\n  " + "\n  ".join(erros)
