"""Contratos do diagnóstico de estabilidade temporal (docs/ADR/0013).

Motivo: a série publicada de área construída é monotônica **por construção** (regra R2
de permanência). Nenhum contrato existente perguntava quanto do estoque publicado em
cada ano é sustentado pela detecção daquele ano e quanto é herdado da união cumulativa.
Sem essa decomposição ao lado, uma quebra estimada em §5.4 sobre a série pós-R2 pode ser
artefato da regra. Estes contratos garantem que a decomposição existe, é coerente e
continua sendo publicada.
"""

from __future__ import annotations

import csv
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
CSV_DECOMPOSICAO = ROOT / "data" / "processed" / "causal" / "decomposicao_permanencia_urbano.csv"
CSV_ESTABILIDADE = ROOT / "data" / "processed" / "causal" / "estabilidade_temporal_camadas.csv"
ADR = ROOT / "docs" / "ADR" / "0013-estabilidade-temporal-das-camadas.md"


def ler(caminho: Path) -> list[dict]:
    if not caminho.exists():
        pytest.skip(f"{caminho.name} ausente — rode pipeline/03_causal/estabilidade_temporal.py")
    with caminho.open(encoding="utf-8") as fh:
        return list(csv.DictReader(fh))


@pytest.fixture(scope="module")
def decomposicao() -> list[dict]:
    return ler(CSV_DECOMPOSICAO)


def test_decomposicao_fecha_com_a_serie_publicada(decomposicao):
    """sustentado + herdado = estoque pós-R2. Se não fecha, a decomposição não é uma
    partição e nenhuma leitura dela vale."""
    for linha in decomposicao:
        soma = float(linha["estoque_sustentado_pelo_ano_km2"]) + float(
            linha["estoque_herdado_da_uniao_km2"]
        )
        r2 = float(linha["area_apos_r2_km2"])
        assert abs(soma - r2) < 1e-2, f"{linha['ano']}: {soma} != {r2}"


def test_fracao_herdada_publicada_por_ano(decomposicao):
    """A fração herdada é o número que qualifica toda quebra estimada sobre a série.
    Ela tem de existir, estar em [0, 1] e ser zero no primeiro ano (não há o que herdar).
    """
    assert decomposicao, "decomposição vazia"
    for linha in decomposicao:
        f = float(linha["fracao_estoque_herdada"])
        assert 0.0 <= f <= 1.0, f"{linha['ano']}: fração fora de [0,1]"
    assert float(decomposicao[0]["fracao_estoque_herdada"]) == 0.0


def test_estabilidade_compara_construido_com_as_classes_de_cobertura():
    """O diagnóstico só responde à pergunta se medir `construido` no MESMO estimador e
    no mesmo denominador que `vegetacao` e `solo_exposto` (docs/ADR/0012)."""
    linhas = ler(CSV_ESTABILIDADE)
    classes = {linha["classe"] for linha in linhas}
    assert {"construido", "vegetacao", "solo_exposto"} <= classes
    pares = {linha["par_anos"] for linha in linhas}
    assert len(pares) >= 5, "faltam pares de anos consecutivos"


def test_adr_0013_existe_e_e_citado_pelos_csv():
    """Número sem ADR ao lado vira folclore. Os dois CSV têm de apontar para ele."""
    assert ADR.exists(), "docs/ADR/0013 ausente"
    for caminho in (CSV_DECOMPOSICAO, CSV_ESTABILIDADE):
        linhas = ler(caminho)
        assert any("0013" in (linha.get("nota") or "") for linha in linhas), (
            f"{caminho.name} não cita docs/ADR/0013"
        )
