#!/usr/bin/env python3
"""pipeline/lib/acuracia_texto.py — faixa de acurácia/comissão de `construido`, de uma
única fonte.

## Por que este módulo existe (ORCHESTRATION_LOG.md 4-06)

`docs/ADR/0009` mediu acurácia do usuário de `construido` = 0,27–0,63 (comissão "entre
37 % e 73 %"). `docs/ADR/0014` reexecutou a validação sobre os estratos corrigidos e obteve
0,286–0,625 — valor que **substitui**, não complementa, o do ADR 0009. O ADR 0014 escreveu
o número novo uma vez; catorze arquivos de `pipeline/` continuaram citando o número antigo
de memória, porque nada os obrigava a recalculá-lo.

O padrão aqui é o mesmo de `pipeline/05_app/gerar_metodologia.py` para versões de
biblioteca (§6-A): **o número e o texto que o descreve saem sempre da mesma fonte**,
`data/processed/acuracia_por_ano.csv`, coluna `acuracia_usuario_construido`. Nenhum arquivo
de `pipeline/` deve escrever "0,27", "0,63", "0,286", "0,625", "37 %" ou "71 %" literalmente
no corpo — chama uma função daqui.

Onde a nota vive numa docstring de módulo, avaliada antes de `data/processed/` existir (por
exemplo, no primeiro `uv run` de um repositório limpo), não é possível calcular o número em
tempo de execução: a docstring fica **sem valor numérico**, remetendo a `docs/ADR/0009`,
`docs/ADR/0014` e a este módulo.

Se `acuracia_por_ano.csv` ainda não existe, as funções levantam `FileNotFoundError` — não
adivinham um valor. Quem chama em contexto onde o arquivo pode faltar (docstring avaliada
em import time, por exemplo) precisa tratar isso, não presumir um número.
"""
from __future__ import annotations

import csv
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
ACURACIA_CSV = REPO_ROOT / "data" / "processed" / "acuracia_por_ano.csv"

COLUNA = "acuracia_usuario_construido"


def _valores_por_ano() -> dict[int, float]:
    """Lê `acuracia_por_ano.csv` e devolve {ano: acurácia do usuário de `construido`}.

    Nunca cacheia entre execuções de processo diferentes: o arquivo é a fonte viva, e
    recalcular a cada chamada é o que torna o número impossível de ficar desatualizado.
    """
    if not ACURACIA_CSV.exists():
        raise FileNotFoundError(
            f"{ACURACIA_CSV} não existe — rode a validação de acurácia "
            "(pipeline/01_imagery/acuracia.py) antes de gerar texto que a cite."
        )
    valores: dict[int, float] = {}
    with ACURACIA_CSV.open(encoding="utf-8", newline="") as fh:
        for linha in csv.DictReader(fh):
            ano = int(linha["ano"])
            valores[ano] = float(linha[COLUNA])
    return valores


def acuracia_usuario_construido_por_ano() -> dict[int, float]:
    """{ano: acurácia do usuário de `construido`} — para uso em dicionários por ano
    (ex.: `ACURACIA_USUARIO_CONSTRUIDO` de `decomposicao_luz.py`), nunca copiado à mão."""
    return _valores_por_ano()


def faixa_acuracia_usuario_construido() -> tuple[float, float]:
    """(mínimo, máximo) da acurácia do usuário de `construido`, entre anos-âncora."""
    vals = list(_valores_por_ano().values())
    return (min(vals), max(vals))


def faixa_comissao_construido_pct() -> tuple[float, float]:
    """(mínimo, máximo) da comissão em pontos percentuais = 100 × (1 − acurácia do usuário).

    O mínimo de comissão corresponde ao MÁXIMO de acurácia, e vice-versa — é o complemento,
    não a mesma ordenação (defeito registrado em ORCHESTRATION_LOG.md 4-04: "63 %" era a
    acurácia máxima reaproveitada como teto de comissão, quando o teto real é 71,4 %).
    """
    lo, hi = faixa_acuracia_usuario_construido()
    return (100 * (1 - hi), 100 * (1 - lo))


def nota_comissao_construido() -> str:
    """Frase pronta, em PT, para docstring/mensagem que cite a comissão de `construido`.

    Formato fixo — arredondamento a 1 casa na acurácia, a 1 casa percentual na comissão —
    para que `pipeline/tests/test_afirmacoes_relacionais.py` (tolerância de 1 p.p.) sempre
    passe quando esta função é a origem do texto.
    """
    lo_ac, hi_ac = faixa_acuracia_usuario_construido()
    lo_com, hi_com = faixa_comissao_construido_pct()

    def _br(v: float, casas: int) -> str:
        return f"{v:.{casas}f}".replace(".", ",")

    return (
        f"acurácia do usuário de `construido` = {_br(lo_ac, 3)}–{_br(hi_ac, 3)} "
        f"(docs/ADR/0009; reexecutado em docs/ADR/0014): entre {_br(lo_com, 1)} % e "
        f"{_br(hi_com, 1)} % do que o mapa chama de construído não é."
    )
