#!/usr/bin/env python3
"""pipeline/02_metrics/write_stats_forma_urbana.py — grava o fragmento §5.2.

Roda os quatro módulos de métrica de forma urbana (`area_cagr.py`,
`fragmentacao.py`, `tipologia_expansao.py`, `edificacoes.py`), converte a saída
de cada um (schema interno de linha, específico de cada módulo) para o schema
canônico do consolidador (`familia, unidade_geografica, ano, variavel, valor,
unidade_medida, selo, nivel_fonte, fonte, metodo, nota`) e grava
`data/interim/stats_forma_urbana.csv`.

Não grava `data/processed/stats_by_year_by_unit.csv` diretamente — isso é
`stats_by_year_by_unit.py` (o consolidador), que junta este fragmento com o de
demografia e reprova se faltar algum. Ver ORCHESTRATION_LOG.md 2-01.

## Como o `variavel` é montado (para não colidir entre módulos)

`variavel = metrica` + `_desde_<periodo_inicio>` (se houver período) +
`_<camada>` (se a camada não for o "sujeito" implícito da própria unidade —
`construido_total` de tipologia/rosa e `edificacoes_open_buildings` de
`edificacoes.py` não entram no nome porque já são o único assunto daquele
módulo; `assentamento_wsf`/`urbano`/`industrial`/`reassentamento` entram,
porque um mesmo par unidade+ano tem mais de uma camada). O script verifica
que não há duas linhas com a mesma chave (familia, unidade, ano, variavel) e
valores diferentes antes de gravar — a mesma checagem que o consolidador faz,
adiantada aqui para falhar cedo com um traceback localizável.

Uso: `uv run python pipeline/02_metrics/write_stats_forma_urbana.py`
"""

from __future__ import annotations

import csv
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import area_cagr
import edificacoes
import fragmentacao
import tipologia_expansao
from _common import carregar_estudo, epsg_metrico

REPO_ROOT = Path(__file__).resolve().parents[2]
SAIDA = REPO_ROOT / "data" / "interim" / "stats_forma_urbana.csv"

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
]

# Camadas que já são o único assunto do módulo (não entram no nome da variável).
CAMADAS_IMPLICITAS = {"construido_total", "edificacoes_open_buildings"}

NOTA_SLC_OFF_2010 = (
    "2010 usa Landsat 7 SLC-off (docs/ADR/0005): 26,64% dos pixels da AOI têm "
    "menos de 4 observações válidas no composto de estação seca "
    "(data/interim/slc_off_2010_cobertura.csv). Métricas derivadas da "
    "classificação própria de 2010 (ou de período que usa 2010 como t0/t1) "
    "herdam essa cobertura desigual — não é um viés de comissão adicional, é "
    "ruído de amostragem de composto que pode inflar heterogeneidade espacial "
    "espúria (manchas, densidade de borda, tipologia)."
)


def _variavel_de(linha: dict) -> str:
    partes = [linha["metrica"]]
    periodo = linha.get("periodo_inicio")
    if periodo is not None:
        partes.append(f"desde_{periodo}")
    camada = linha.get("camada")
    if camada and camada not in CAMADAS_IMPLICITAS:
        partes.append(camada)
    return "_".join(partes)


def _nota_confiabilidade(linha: dict) -> str:
    """Garante que toda linha declare robustez/sensibilidade à comissão, mesmo
    quando o módulo de origem deixou `nota` vazia para o caso 'sem ressalva
    extra' (ex.: linhas de área do WSF sem o caso '25 de Setembro')."""
    nota = (linha.get("nota") or "").strip()
    if "comissão" in nota or "confiáve" in nota.lower() or "confiave" in nota.lower():
        return nota
    if linha.get("confiavel_para_tendencia"):
        tag = (
            "Robusta à comissão do mapa (ADR 0009): fonte é o WSF Evolution ou "
            "uma métrica declarada robusta a falsos positivos dispersos "
            "(direção/tipologia de expansão)."
        )
    else:
        tag = (
            "Sensível à comissão do mapa (ADR 0009, acurácia do usuário do "
            "construído = 0,27-0,63): não interpretar como medição absoluta "
            "livre de erro."
        )
    return f"{nota} {tag}".strip()


def _com_nota_2010(linha: dict, nota: str) -> str:
    anos_envolvidos = {linha.get("ano"), linha.get("periodo_inicio")}
    if linha.get("fonte_dado") == "classificacao_propria" and 2010 in anos_envolvidos:
        if "SLC-off" not in nota:
            nota = f"{nota} {NOTA_SLC_OFF_2010}".strip()
    return nota


def converter(linhas_modulo: list[dict], familia: str = "forma_urbana") -> list[dict]:
    saida = []
    for linha in linhas_modulo:
        nota = _nota_confiabilidade(linha)
        nota = _com_nota_2010(linha, nota)
        saida.append(
            {
                "familia": familia,
                "unidade_geografica": linha["unidade"],
                "ano": linha["ano"],
                "variavel": _variavel_de(linha),
                "valor": "" if linha["valor"] is None else linha["valor"],
                "unidade_medida": linha["unidade_medida"],
                "selo": linha["selo"],
                "nivel_fonte": "A",
                "fonte": linha["fonte"],
                "metodo": linha["metodo"],
                "nota": nota,
            }
        )
    return saida


def checar_duplicatas(linhas: list[dict]) -> None:
    vistos: dict[tuple, str] = {}
    for x in linhas:
        chave = (x["familia"], x["unidade_geografica"], x["ano"], x["variavel"])
        valor = str(x["valor"])
        if chave in vistos and vistos[chave] != valor:
            raise ValueError(
                f"chave duplicada e divergente: {chave} ({vistos[chave]!r} x {valor!r})"
            )
        vistos[chave] = valor


def main() -> int:
    estudo = carregar_estudo()
    epsg = epsg_metrico(estudo)

    brutas = []
    brutas += area_cagr.linhas_wsf(estudo, epsg)
    brutas += area_cagr.linhas_classificacao(estudo, epsg)
    brutas += fragmentacao.linhas(estudo, epsg)
    brutas += tipologia_expansao.linhas(estudo, epsg)
    brutas += edificacoes.linhas(estudo, epsg)

    linhas_saida = converter(brutas)
    checar_duplicatas(linhas_saida)

    SAIDA.parent.mkdir(parents=True, exist_ok=True)
    with SAIDA.open("w", newline="", encoding="utf-8") as fh:
        escritor = csv.DictWriter(fh, fieldnames=COLUNAS)
        escritor.writeheader()
        escritor.writerows(linhas_saida)

    print(f"[ok] {SAIDA.relative_to(REPO_ROOT)}: {len(linhas_saida)} linhas.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
