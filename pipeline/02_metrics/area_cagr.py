#!/usr/bin/env python3
"""pipeline/02_metrics/area_cagr.py — §5.2 item 1: área, CAGR e decomposição por camada.

## Duas séries, duas perguntas, dois selos — não misturar (docs/ADR/0008)

1. **Série de TENDÊNCIA (área e CAGR)**: WSF Evolution, ano de primeira
   detecção por pixel, 1985–2015. É a série primária para responder "quanto
   cresceu e a que taxa" em `tete`, `moatize`, `cateme`, `mwaladzi` — a
   classificação própria NÃO serve para isso (viés de sensor de +1,25%/ano,
   mesma ordem de grandeza do efeito procurado). Cobre só até 2015: **não há
   série de tendência defensável para 2015→2020 ou 2020→2025** nesta entrega;
   as linhas desses períodos ficam ausentes, não aproximadas.
   `industrial` fica de fora da série do WSF por construção: o WSF é um
   produto de *assentamento*, não de uso do solo, e não separa mina de vila.
2. **Série de DECOMPOSIÇÃO por camada**: classificação própria
   (`urbano`/`industrial`/`reassentamento`), nos 6 anos-âncora. É a única
   fonte que separa as três camadas mutuamente exclusivas — é o que ADR 0008
   diz que ela ainda serve para fazer. Toda área desta série carrega a
   acurácia do usuário medida em `acuracia_por_ano.csv` (docs/ADR/0009;
   valor reexecutado em docs/ADR/0014 — ver `pipeline/lib/acuracia_texto.py`
   para o número corrente, não transcrito aqui). Marcada
   `confiavel_para_tendencia=False` sempre — a magnitude não deve entrar em
   CAGR nem em comparação entre anos como se fosse medição repetida do mesmo
   fenômeno com erro constante.

## Intensidade de uso (área/população) — NÃO calculada nesta entrega

§5.2 pede "intensidade de uso (área/pop)". Não há, no repositório, nenhuma
série de população por unidade e por ano — isso é o objeto de §5.3
(reconstrução demográfica e domiciliar), fase distinta desta entrega. As
únicas tabelas de população disponíveis (`hdx_cod-ps-moz_admpop_adm2_*.csv`)
são por DISTRITO (geografia administrativa que engloba área rural extensa,
incomparável ao polígono de núcleo urbano usado aqui) e só para 2017/2025.
Dividir área por essa população produziria uma "intensidade" que mistura duas
geografias diferentes — é exatamente o número frágil que a tarefa pede para
não publicar. Fica registrado como pendência explícita para §5.3.

Uso: `uv run python pipeline/02_metrics/area_cagr.py`
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import _common as c

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "lib"))
import acuracia_texto

ANOS_IMAGEM = None  # preenchido de config/study.yaml em main()
ANO_FIM_WSF = 2015
UNIDADES_WSF = ["tete", "moatize_vila", "cateme", "mwaladzi"]
FONTE_WSF = "WSF Evolution (DLR), 30 m, ano de primeira detecção — data/raw/wsf_evolution_*.tif"
FONTE_CLASSIFICACAO = (
    "Classificação própria (Random Forest, protocolo único todos os anos) — "
    "data/processed/imagery/{camada}_{ano}_30m_32736.tif"
)


def linhas_wsf(estudo: dict, epsg: int) -> list[dict]:
    """Área e CAGR por unidade a partir do WSF, atribuindo cada pixel
    construído (em cada ano) ao ponto-sede mais próximo, com exclusão prévia
    da pegada industrial (Maus et al. + 150 m — ver _common.mascara_exclusao_industrial)."""
    linhas = []
    anos_imagem = [a for a in estudo["anos_ancora"]["imagem"] if a <= ANO_FIM_WSF]
    # perfil de referência: qualquer camada de qualquer ano serve (grade única).
    _, perfil = c.carregar_camada("urbano", 2000, epsg=epsg)
    wsf = c.carregar_wsf_reprojetado(perfil)
    excl_industrial = c.mascara_exclusao_industrial(perfil, epsg)
    pontos = c.pontos_sede_utm(epsg)

    areas_por_ano: dict[int, dict[str, float]] = {}
    for ano in anos_imagem:
        construido_ano = (wsf > 0) & (wsf <= ano) & ~excl_industrial
        partes = c.atribuir_unidade_mais_proxima(construido_ano, perfil["transform"], pontos)
        areas_por_ano[ano] = {u: c.area_km2(partes[u]) for u in UNIDADES_WSF}
        for u in UNIDADES_WSF:
            linhas.append(
                {
                    "ano": ano,
                    "unidade": u,
                    "camada": "assentamento_wsf",
                    "fonte_dado": "wsf_evolution",
                    "metrica": "area_km2",
                    "periodo_inicio": None,
                    "valor": round(areas_por_ano[ano][u], 4),
                    "unidade_medida": "km2",
                    "selo": "observado",
                    "confiavel_para_tendencia": True,
                    "fonte": FONTE_WSF,
                    "metodo": (
                        "Área cumulativa (ano de detecção <= ano-âncora) do WSF Evolution, "
                        "menos pegada industrial (Maus et al. 2022 + 150 m), atribuída ao "
                        "ponto-sede mais próximo (partição de Voronoi entre tete/moatize/"
                        "cateme/mwaladzi). Ver docstring de pipeline/02_metrics/_common.py."
                    ),
                    "nota": (
                        "'moatize_vila' inclui qualquer pixel do povoado '25 de Setembro' "
                        "(geometry: null, não localizável) por ser o ponto-sede mais "
                        "próximo — infla moatize com reassentamento não separável, "
                        "magnitude não estimável (ver restrição 3 da tarefa)."
                        if u == "moatize_vila"
                        else ""
                    ),
                }
            )

    # CAGR entre pares consecutivos de anos-âncora <= 2015, e o intervalo cheio.
    for u in UNIDADES_WSF:
        for i in range(len(anos_imagem) - 1):
            a0, a1 = anos_imagem[i], anos_imagem[i + 1]
            v0, v1 = areas_por_ano[a0][u], areas_por_ano[a1][u]
            r = c.cagr(v0, v1, a1 - a0)
            linhas.append(
                {
                    "ano": a1,
                    "unidade": u,
                    "camada": "assentamento_wsf",
                    "fonte_dado": "wsf_evolution",
                    "metrica": "cagr_pct_ano",
                    "periodo_inicio": a0,
                    "valor": round(r * 100, 4) if r is not None else None,
                    "unidade_medida": "%/ano",
                    "selo": "observado",
                    "confiavel_para_tendencia": True,
                    "fonte": FONTE_WSF,
                    "metodo": (
                        f"CAGR = (area({a1})/area({a0}))^(1/{a1-a0}) - 1, "
                        "sobre a série WSF acima."
                    ),
                    "nota": (
                        "área inicial ou intervalo nulo — CAGR indefinida, não publicada como 0."
                        if r is None
                        else ""
                    ),
                }
            )
        a0, a1 = anos_imagem[0], anos_imagem[-1]
        v0, v1 = areas_por_ano[a0][u], areas_por_ano[a1][u]
        r = c.cagr(v0, v1, a1 - a0)
        linhas.append(
            {
                "ano": a1,
                "unidade": u,
                "camada": "assentamento_wsf",
                "fonte_dado": "wsf_evolution",
                "metrica": "cagr_pct_ano",
                "periodo_inicio": a0,
                "valor": round(r * 100, 4) if r is not None else None,
                "unidade_medida": "%/ano",
                "selo": "observado",
                "confiavel_para_tendencia": True,
                "fonte": FONTE_WSF,
                "metodo": f"CAGR do intervalo inteiro observado pelo WSF: {a0}-{a1}.",
                "nota": (
                    "Nota do ADR 0008: 2005-2010 e 2010-2015 têm a mesma mediana de "
                    "observações da classificação própria (4) e são o trecho menos "
                    "contaminado por viés de sensor — mas esta linha já é WSF, que não "
                    "tem esse viés por construção; a nota vale para quem comparar com a "
                    "série de classificação em paralelo."
                ),
            }
        )
    return linhas


def linhas_classificacao(estudo: dict, epsg: int) -> list[dict]:
    """Área por camada e por unidade, nos 6 anos-âncora, a partir da
    classificação própria. Decomposição, não tendência (ver docstring)."""
    linhas = []
    anos = estudo["anos_ancora"]["imagem"]
    pontos_urbano = {
        k: v for k, v in c.pontos_sede_utm(epsg).items() if k in ("tete", "moatize_vila")
    }
    pontos_reass = {
        k: v for k, v in c.pontos_sede_utm(epsg).items() if k in ("cateme", "mwaladzi")
    }

    for ano in anos:
        # industrial: unidade própria, sem split.
        m_ind, perfil = c.carregar_camada("industrial", ano, epsg=epsg)
        linhas.append(
            _linha_classificacao(ano, "industrial", "industrial", c.area_km2(m_ind))
        )

        # reassentamento: split entre cateme/mwaladzi por proximidade.
        m_reass, _ = c.carregar_camada("reassentamento", ano, epsg=epsg)
        if pontos_reass:
            partes = c.atribuir_unidade_mais_proxima(m_reass, perfil["transform"], pontos_reass)
            for u, m in partes.items():
                linhas.append(_linha_classificacao(ano, u, "reassentamento", c.area_km2(m)))

        # urbano: split entre tete/moatize por proximidade.
        m_urb, _ = c.carregar_camada("urbano", ano, epsg=epsg)
        partes = c.atribuir_unidade_mais_proxima(m_urb, perfil["transform"], pontos_urbano)
        for u, m in partes.items():
            nota = (
                "Inclui pixels do povoado '25 de Setembro' (geometry null, não "
                "localizável), atribuídos a moatize por proximidade — não separável "
                "de crescimento orgânico com os dados disponíveis (restrição 3)."
                if u == "moatize_vila"
                else ""
            )
            linhas.append(_linha_classificacao(ano, u, "urbano", c.area_km2(m), nota=nota))

    return linhas


def _linha_classificacao(
    ano: int, unidade: str, camada: str, valor_km2: float, nota: str = ""
) -> dict:
    return {
        "ano": ano,
        "unidade": unidade,
        "camada": camada,
        "fonte_dado": "classificacao_propria",
        "metrica": "area_km2",
        "periodo_inicio": None,
        "valor": round(valor_km2, 4),
        "unidade_medida": "km2",
        "selo": "observado",
        "confiavel_para_tendencia": False,
        "fonte": FONTE_CLASSIFICACAO.format(camada=camada, ano=ano),
        "metodo": (
            "Pixel classificado na camada, atribuído ao ponto-sede mais próximo "
            "(industrial não é atribuído — é a própria camada)."
            if camada != "industrial"
            else "Soma da camada 'industrial' inteira (já é uma unidade, sem split espacial)."
        ),
        "nota": (
            f"Área SENSÍVEL à comissão medida ({acuracia_texto.nota_comissao_construido()}) "
            "Não usar para CAGR nem para "
            "'quanto cresceu' — só para a PROPORÇÃO entre camadas no mesmo ano/unidade. "
            + nota
        ).strip(),
    }


def main() -> int:
    estudo = c.carregar_estudo()
    epsg = c.epsg_metrico(estudo)
    linhas = linhas_wsf(estudo, epsg) + linhas_classificacao(estudo, epsg)
    return linhas  # consumido por stats_by_year_by_unit.py


if __name__ == "__main__":
    import json

    out = main()
    print(json.dumps(out[:3], indent=2, ensure_ascii=False))
    print(f"{len(out)} linhas geradas.", file=sys.stderr)
