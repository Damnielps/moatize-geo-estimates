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

from pathlib import Path

import pandas as pd
import pytest

ROOT = Path(__file__).resolve().parents[2]
PROCESSED = ROOT / "data" / "processed"
STATS_CSV = PROCESSED / "stats_by_year_by_unit.csv"
CONTEXTO_CSV = PROCESSED / "demografia_contexto_nao_nucleo.csv"
SENSIB_CSV = PROCESSED / "populacao_dasimetrica_sensibilidade.csv"

SELOS_VALIDOS = {"observado", "interpolado", "modelado"}


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


def test_valores_batem_com_ancoras_hdx(stats_demografia):
    esperado = {
        ("Cidade de Tete", 2017): 307338,
        ("Cidade de Tete", 2025): 460248,
        ("Distrito de Moatize", 2017): 260843,
        ("Distrito de Moatize", 2025): 349103,
    }
    pop = stats_demografia[stats_demografia["variavel"] == "populacao_total_residente"]
    for (unidade, ano), valor in esperado.items():
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


def test_sensibilidade_preserva_populacao_total_por_construcao(sensibilidade):
    linhas = sensibilidade[
        sensibilidade["metodo_peso"].isin(
            ["classificacao_propria", "ghsl_built_s", "wsf_evolution"]
        )
    ]
    linhas = linhas[linhas["aplicavel"] == True]  # noqa: E712
    assert linhas["populacao_total_distribuida"].nunique() == 1
    assert int(linhas["populacao_total_distribuida"].iloc[0]) == 307338


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
