#!/usr/bin/env python3
"""pipeline/02_metrics/populacao_vila_moatize.py — estimativa dasimétrica de terceiros
da população da Vila de Moatize (§3, §4.0, §5.3, §10 CLAUDE.md).

## O problema

A Vila de Moatize (ADM3, posto administrativo) não aparece em nenhuma fonte de
população: o HDX COD-PS só publica ADM2 (Distrito de Moatize, muito maior — ver
docstring de `reconstrucao_demografica.py`, item 2). Não há como "reconstruir" um
total que nenhuma fonte primária jamais tabulou.

O que este script faz em vez disso é diferente de dasimetria: `reconstrucao_demografica
.dasimetria_tete_2017` REDISTRIBUI um total já observado (307.338, HDX/INE) pela mancha
construída. Aqui não há total observado para redistribuir — o que existe é uma grade de
POPULAÇÃO já contada por outra instituição (GRID3 v1.1, calibrado ao Censo 2017 de
Moçambique, CC BY 4.0, nível A — `data/provenance_parts/worldpop_grid3.md`), e o produto
é a SOMA das células dessa grade que caem dentro da mancha construída da Vila. É "colher
de terceiros", não "redistribuir o próprio total" — por isso o selo é `modelado` e a
fonte é do GRID3, não do HDX.

## Método de sobreposição grade populacional × máscara construída (a escolha, e por quê)

Uma grade de CONTAGEM populacional (pessoas por célula, não densidade) não pode ser
reamostrada por interpolação para outra grade: interpolar os VALORES de população
espalharia pessoas entre células vizinhas e mudaria a soma total do raster — o oposto do
que uma contagem exige. A rota adotada aqui evita esse problema por construção:

1. A grade de população (GRID3) **nunca é reprojetada nem reamostrada**; permanece na
   sua grade nativa (EPSG:4326, ~100 m) do início ao fim.
2. É a MÁSCARA de área construída (urbano ∪ reassentamento, EPSG:32736, 30 m) que é
   reprojetada para a grade do GRID3 — com `Resampling.average`, que dá a FRAÇÃO de cada
   célula do GRID3 coberta por pixels construídos (0-1), não um valor de população.
   `Resampling.average` sobre uma máscara categórica (0/1) é reamostragem de COBERTURA
   (área), legítima e padrão em análise de uso do solo; não é interpolação de uma
   variável de contagem.
3. A população atribuída à Vila = soma, célula a célula do GRID3, de
   `populacao_da_celula × fração_construída_da_célula × pertence_ao_cluster_moatize_vila`.
   Isso nunca cria nem move população entre células do GRID3: cada célula continua
   contribuindo, no máximo, com o valor que o GRID3 já lhe atribuiu.

## Partição espacial (Voronoi) — reaproveitada, não reimplementada

Não há polígono para "Vila de Moatize"; a mesma partição de Voronoi por vizinho mais
próximo de `pipeline/02_metrics/_common.py`/`tipologia_expansao.py` é reaproveitada aqui
via `_common.atribuir_unidade_mais_proxima_grade_completa` (variante que classifica a
grade INTEIRA do GRID3, não só os pixels já sabidamente construídos — necessário porque
aqui a grade de referência é a de população, não a de classificação) e
`_common.pontos_sede_wgs84()` (mesmos quatro pontos-sede de `pontos_sede_utm`, em
EPSG:4326 — o CRS nativo do GRID3/GHSL, evitando reprojetar o raster de coordenadas).

## Piso e teto — reenquadrado em `docs/ADR/0017` (nunca um valor único — item 1 da tarefa)

Quatro variantes RESTRITAS por máscara de construído (todas atenuam a soma do GRID3):

- **classificação própria, multiplicador de fração** (urbano ∪ reassentamento 2020;
  carrega a comissão medida em `docs/ADR/0009`/`0014`, `pipeline/lib/acuracia_texto.py`
  — frente ao peso GHSL tende a puxar a estimativa para CIMA; frente ao OBSERVADO em
  Cidade de Tete, subestima ~40%: são dois referentes distintos, nunca uma frase só).
- **GHSL BUILT-S 2020, multiplicador de fração** (fração construída 0-1, já nativa em
  EPSG:4326 ~100 m — mesmo produto de `classificacao.ghsl_fracao_construida`,
  reprojetado à grade do GRID3).
- **pertença binária** (fração_construída > 0, sem multiplicador — a célula conta
  inteira se tiver qualquer construído).
- **pertença por mediana** (fração_construída ≥ mediana das células do cluster com
  fração > 0 — corte por `np.quantile`, nunca limiar absoluto, ADR 0014).

Validado contra Cidade de Tete (307.338 observados, HDX COD-PS 2017), NENHUMA das quatro
recupera o observado: desvios de −25,2% a −74,5%. `piso` = mínimo das quatro.

A quinta variante — soma do GRID3 no cluster de Voronoi inteiro, **sem nenhum peso de
construído** — é a ÚNICA que valida em Cidade de Tete (+1,61%). Isso não é ruído do
multiplicador: o GRID3 v1.1 já é um produto dasimétrico calibrado ao Censo 2017, e
pesá-lo de novo pela nossa máscara de construído restringe a população duas vezes,
descartando gente que o produtor já havia colocado onde ela está. É a PARTIÇÃO espacial,
não o peso, que reproduz o observado. Por isso essa variante deixa de ser "diagnóstico
não publicável" e passa a ser o `teto` — limite SUPERIOR, porque inclui a área rural do
cluster atribuída à sede mais próxima, não porque seja "a" vila.

Nenhuma das cinco variantes é publicada como valor central. Todas vão, nomeadas, para
`data/processed/populacao_vila_moatize_sensibilidade.csv`.

## Validação cruzada em Cidade de Tete (o resultado que importa)

O MESMO procedimento (as cinco variantes, mesma soma célula a célula, mesmo cluster de
Voronoi, agora para `tete`) é aplicado a Cidade de Tete e comparado contra os 307.338
habitantes observados (HDX COD-PS 2017, nível A — `reconstrucao_demografica.montar_nucleo`,
nunca transcrito à mão). O desvio percentual medido ali é publicado e é ele — não um
limiar de aprovação — que diz ao leitor quanto confiar no número da Vila: as duas cidades
compartilham grade (GRID3), classificação própria e método de partição, então qualquer
viés sistemático do método (comissão da classificação, resolução do GRID3, erro da
Voronoi ao aproximar um limite administrativo por um ponto-sede) aparece nos dois lugares
na mesma direção e ordem de grandeza.

## O que este script NÃO faz

- Não produz série: um único ano (2017, ano de calibração do GRID3) — nenhum CAGR.
- Não substitui o Distrito de Moatize nem o modifica.
- Não trata "25 de Setembro" (sem geometria, ver `_common.py`) — os pixels desse
  povoado, se construídos, caem no cluster `moatize_vila` por proximidade (mesma
  advertência de `_common.py`, herdada aqui).

Uso: `uv run python pipeline/02_metrics/populacao_vila_moatize.py`
"""

from __future__ import annotations

import csv
import sys
from datetime import UTC, datetime
from pathlib import Path

import numpy as np
import rasterio
import rasterio.warp

REPO_ROOT = Path(__file__).resolve().parents[2]
DATA_RAW = REPO_ROOT / "data" / "raw"
DATA_PROCESSED = REPO_ROOT / "data" / "processed"
IMAGERY = DATA_PROCESSED / "imagery"
GRID3_TIF = DATA_RAW / "grid3_moz_pop_v1_1_2020_100m_aoi.tif"
SAIDA_CSV = DATA_PROCESSED / "populacao_vila_moatize_sensibilidade.csv"
PROVENANCE_FRAGMENT = REPO_ROOT / "data" / "provenance_parts" / "populacao_vila_moatize.md"

sys.path.insert(0, str(Path(__file__).resolve().parent))
import _common as c  # noqa: E402
import reconstrucao_demografica as rd  # noqa: E402

sys.path.insert(0, str(REPO_ROOT / "pipeline" / "01_imagery"))
import classificacao as cls  # noqa: E402

sys.path.insert(0, str(REPO_ROOT / "pipeline" / "lib"))
import acuracia_texto  # noqa: E402

MARCADOR_INICIO = "<!-- SECAO_POPULACAO_VILA_MOATIZE_INICIO -->"
MARCADOR_FIM = "<!-- SECAO_POPULACAO_VILA_MOATIZE_FIM -->"

ANO_MASCARA = 2020  # único ano-âncora disponível mais próximo de "circa 2017" com
# classificação própria e GHSL simultaneamente cobrindo a AOI inteira (GHSL 2015/2020).


def _perfil_grid3() -> tuple[dict, np.ndarray]:
    with rasterio.open(GRID3_TIF) as src:
        pop = src.read(1).astype("float64")
        nodata = src.nodata
        if nodata is not None:
            pop = np.where(pop == nodata, 0.0, pop)
        pop = np.clip(pop, 0.0, None)  # nenhuma célula negativa entra na soma
        perfil = {
            "transform": src.transform,
            "crs": src.crs,
            "shape": src.shape,
            "width": src.width,
            "height": src.height,
        }
    return perfil, pop


def _fracao_construida_propria_na_grade_grid3(perfil_grid3: dict) -> np.ndarray:
    """urbano ∪ reassentamento (30 m, 32736) -> fração de cobertura por célula do
    GRID3 (Resampling.average — cobertura de área, não interpolação de contagem)."""
    urbano, perfil_30m = c.carregar_camada("urbano", ANO_MASCARA)
    reassent, _ = c.carregar_camada("reassentamento", ANO_MASCARA)
    mask = urbano | reassent
    destino = np.zeros(perfil_grid3["shape"], dtype="float32")
    rasterio.warp.reproject(
        source=mask.astype("float32"),
        destination=destino,
        src_transform=perfil_30m["transform"],
        src_crs=perfil_30m["crs"],
        dst_transform=perfil_grid3["transform"],
        dst_crs=perfil_grid3["crs"],
        resampling=rasterio.warp.Resampling.average,
    )
    return np.clip(destino, 0.0, 1.0)


def _clusters_grid3(perfil_grid3: dict) -> dict[str, np.ndarray]:
    pontos = c.pontos_sede_wgs84()
    return c.atribuir_unidade_mais_proxima_grade_completa(perfil_grid3, pontos)


def _populacao_observada_2017(unidade: str) -> int:
    """Nunca transcrito à mão: lido de `reconstrucao_demografica.montar_nucleo()`."""
    for linha in rd.montar_nucleo():
        if (
            linha["unidade_geografica"] == unidade
            and linha["ano"] == 2017
            and linha["variavel"] == "populacao_total_residente"
        ):
            return int(linha["valor"])
    raise ValueError(f"população 2017 observada não encontrada para {unidade!r}")


def estimar() -> dict:
    """Seis variantes por cluster (a, a', b, c, d + validação), medidas — não
    presumidas — em `docs/ADR/0017` (a correção deste script): a máscara de
    construído pesa DUAS VEZES um GRID3 que já é dasimétrico (calibrado ao Censo
    2017), e nenhuma forma de aplicá-la recupera o observado em Cidade de Tete.
    O que valida (+1,61 %) é a partição de Voronoi SEM peso de construído — por
    isso ela deixa de ser 'diagnóstico não publicável' e passa a ser o TETO.

    - (a) multiplicador de fração, classificação própria — variante, não teto.
    - (a') multiplicador de fração, GHSL BUILT-S — variante, tipicamente o piso.
    - (b) pertença binária: fração_construída > 0 (limiar de existência, não corte
      arbitrário — ADR 0014).
    - (c) pertença binária: fração_construída >= mediana das células do cluster
      com fração > 0 (`np.quantile`, nunca limiar absoluto — ADR 0014).
    - (d) TETO: soma do GRID3 no cluster de Voronoi inteiro, sem nenhum peso de
      construído — inclui a área rural do cluster atribuída à sede mais próxima;
      é limite SUPERIOR para a vila, não a estimativa da vila.
    """
    perfil_grid3, pop = _perfil_grid3()
    clusters = _clusters_grid3(perfil_grid3)

    peso_own = _fracao_construida_propria_na_grade_grid3(perfil_grid3)
    peso_ghsl = cls.ghsl_fracao_construida(ANO_MASCARA, perfil_grid3)
    if peso_ghsl is None:
        raise FileNotFoundError(f"GHSL BUILT-S {ANO_MASCARA} ausente em data/raw/")
    peso_ghsl = np.clip(peso_ghsl, 0.0, 1.0)

    resultado = {}
    for unidade_cluster in ("moatize_vila", "tete"):
        cluster = clusters[unidade_cluster]
        peso_cluster = peso_own[cluster]
        presentes = peso_cluster[peso_cluster > 0]
        mediana_presentes = (
            float(np.quantile(presentes, 0.5)) if presentes.size else float("nan")
        )

        est_own = float((pop * peso_own * cluster).sum())
        est_ghsl = float((pop * peso_ghsl * cluster).sum())
        # (b) pertença binária: toda célula com QUALQUER fração construída conta
        # a população inteira da célula (nenhuma fração é aplicada).
        bin_presente = (peso_own > 0) & cluster
        est_bin_presente = float(pop[bin_presente].sum())
        # (c) pertença binária mais restrita: só células cuja fração construída
        # atinge a MEDIANA das células do próprio cluster com fração > 0 — corte
        # é um quantil da amostra, nunca um valor absoluto fixado a priori.
        if presentes.size:
            bin_mediana = (peso_own >= mediana_presentes) & (peso_own > 0) & cluster
        else:
            bin_mediana = np.zeros_like(cluster)
        est_bin_mediana = float(pop[bin_mediana].sum())
        # (d) TETO: cluster de Voronoi inteiro, sem nenhum peso de construído —
        # única variante que valida em Cidade de Tete (+1,61 %); limite SUPERIOR
        # para a vila (inclui a área rural do cluster atribuída à sede mais
        # próxima), não um valor central.
        est_sem_peso = float(pop[cluster].sum())

        variantes = {
            "estimativa_classificacao_propria": est_own,
            "estimativa_ghsl_built_s": est_ghsl,
            "estimativa_pertenca_binaria": est_bin_presente,
            "estimativa_pertenca_mediana": est_bin_mediana,
            "diagnostico_sem_peso_construido": est_sem_peso,
        }
        # piso = menor das variantes RESTRITAS por construído (nunca inclui (d),
        # que por definição é o teto e não restringe nada).
        variantes_restritas = {
            k: v for k, v in variantes.items() if k != "diagnostico_sem_peso_construido"
        }
        resultado[unidade_cluster] = {
            **variantes,
            "piso": min(variantes_restritas.values()),
            "teto": est_sem_peso,
            "mediana_fracao_presentes": mediana_presentes,
            "n_celulas_cluster": int(cluster.sum()),
            "n_celulas_com_fracao_positiva": int(presentes.size),
        }

    pop_observada_tete = _populacao_observada_2017("Cidade de Tete")
    for peso_nome in (
        "estimativa_classificacao_propria",
        "estimativa_ghsl_built_s",
        "estimativa_pertenca_binaria",
        "estimativa_pertenca_mediana",
        "diagnostico_sem_peso_construido",
    ):
        est = resultado["tete"][peso_nome]
        resultado["tete"][f"desvio_pct_{peso_nome}"] = (
            (est - pop_observada_tete) / pop_observada_tete * 100.0
        )
    resultado["tete"]["populacao_observada_2017"] = pop_observada_tete

    return resultado, perfil_grid3


def montar_linhas_sensibilidade(resultado: dict) -> list[dict]:
    r_tete = resultado["tete"]
    desvio_propria_tete = r_tete["desvio_pct_estimativa_classificacao_propria"]
    desvio_diag_tete = r_tete["desvio_pct_diagnostico_sem_peso_construido"]
    faixa_restrita_tete = _faixa_desvio_restrito(r_tete)

    nota_metodo = (
        "Grade de população (GRID3 v1.1, EPSG:4326, ~100 m, calibrada ao Censo 2017) "
        "NUNCA reprojetada/reamostrada — permanece na grade nativa. A máscara de "
        "área construída (30 m, 32736) é que é reprojetada para a grade do GRID3, com "
        "Resampling.average (fração de cobertura por célula, 0-1) — cobertura de área, "
        "não interpolação de uma variável de contagem. Estimativa = soma célula a célula "
        "de população_da_célula x fração_construída x pertence_ao_cluster (Voronoi por "
        "vizinho mais próximo entre tete/moatize_vila/cateme/mwaladzi, "
        "_common.atribuir_unidade_mais_proxima_grade_completa)."
    )
    # Corrigido (docs/ADR/0017): a versão anterior desta nota dizia só que o peso
    # 'classificacao_propria' "tende a inflar a estimativa" — verdade só frente ao
    # OUTRO peso (GHSL), não frente ao observado. Frente ao observado em Cidade de
    # Tete, a mesma variante SUBESTIMA (percentual calculado abaixo, de `resultado`,
    # nunca digitado). As duas relações têm referentes diferentes e não podem
    # compartilhar uma frase.
    nota_comissao = (
        f"peso 'classificacao_propria' carrega a comissão medida na classe construído: "
        f"{acuracia_texto.nota_comissao_construido()} — DUAS relações, dois referentes: "
        "frente ao peso GHSL BUILT-S (o outro multiplicador de fração), tende a puxar a "
        "estimativa para CIMA (mais comissão = mais área contada = mais população pesada); "
        "frente à população OBSERVADA em Cidade de Tete (307.338, HDX COD-PS 2017), a "
        f"mesma variante SUBESTIMA em {abs(desvio_propria_tete):.1f}% — nenhum multiplicador "
        "de fração recupera o observado, porque o GRID3 já é um produto dasimétrico "
        "calibrado ao Censo 2017, e pesá-lo de novo pela máscara de construído restringe "
        "a população duas vezes."
    )
    linhas = []
    clusters_rotulos = (("moatize_vila", "Vila de Moatize"), ("tete", "Cidade de Tete"))
    for unidade_cluster, rotulo in clusters_rotulos:
        r = resultado[unidade_cluster]
        for peso_nome, campo, fonte_peso in (
            (
                "classificacao_propria",
                "estimativa_classificacao_propria",
                "classificação própria (urbano ∪ reassentamento, 2020) — multiplicador de "
                "fração, RESTRITO por construído",
            ),
            (
                "ghsl_built_s",
                "estimativa_ghsl_built_s",
                "GHSL BUILT-S R2023A, época 2020 (fração construída por célula) — "
                "multiplicador de fração, RESTRITO por construído",
            ),
            (
                "pertenca_binaria",
                "estimativa_pertenca_binaria",
                "classificação própria, pertença binária (fração_construída > 0, sem "
                "multiplicador) — RESTRITO por construído",
            ),
            (
                "pertenca_mediana",
                "estimativa_pertenca_mediana",
                "classificação própria, pertença binária acima da mediana das células com "
                "fração > 0 (corte por np.quantile, ADR 0014, nunca limiar absoluto) — "
                "RESTRITO por construído",
            ),
        ):
            linha = {
                "unidade_geografica": rotulo,
                "ano_referencia": 2017,
                "metodo_peso": peso_nome,
                "estimativa_populacao": round(r[campo], 1),
                "selo": "modelado",
                "nivel_fonte": "A",
                "fonte_populacao": (
                    "GRID3 v1.1 MOZ (Bondarenko et al. 2020, WorldPop/Southampton, CC BY 4.0, "
                    "calibrado ao Censo 2017) — data/raw/grid3_moz_pop_v1_1_2020_100m_aoi.tif"
                ),
                "fonte_peso": fonte_peso,
                "nota_metodo": nota_metodo,
                "nota_comissao": nota_comissao if peso_nome == "classificacao_propria" else "",
                "desvio_pct_validacao_tete": (
                    round(r.get(f"desvio_pct_{campo}", float("nan")), 2)
                    if unidade_cluster == "tete"
                    else ""
                ),
            }
            linhas.append(linha)
        linhas.append(
            {
                "unidade_geografica": rotulo,
                "ano_referencia": 2017,
                "metodo_peso": "piso_teto",
                "piso": round(r["piso"], 1),
                "teto": round(r["teto"], 1),
                "selo": "modelado",
                "nivel_fonte": "A",
                "nota_metodo": (
                    "piso = MENOR das variantes RESTRITAS por máscara de construído "
                    "(classificação própria, GHSL, pertença binária, pertença por mediana) "
                    f"— na validação em Cidade de Tete perde {faixa_restrita_tete} do "
                    "observado, logo é limite INFERIOR. teto = soma do GRID3 no cluster de "
                    "Voronoi INTEIRO, sem nenhum peso de construído (variante 'd' abaixo) — "
                    f"valida em Cidade de Tete a {desvio_diag_tete:+.1f}% do observado, mas "
                    "inclui a área rural do cluster atribuída à sede mais próxima, logo é "
                    "limite SUPERIOR, não a vila propriamente. NENHUM valor central é "
                    "publicado: nem a média, nem qualquer variante isolada — ver linhas "
                    "'metodo_peso' individuais para cada variante nomeada, e a linha "
                    "'validacao_cruzada' para o desvio de cada uma frente ao observado."
                ),
            }
        )
        linhas.append(
            {
                "unidade_geografica": rotulo,
                "ano_referencia": 2017,
                "metodo_peso": "diagnostico_sem_peso_construido",
                "estimativa_populacao": round(r["diagnostico_sem_peso_construido"], 1),
                "selo": "modelado",
                "nivel_fonte": "A",
                "desvio_pct_validacao_tete": (
                    round(r.get("desvio_pct_diagnostico_sem_peso_construido", float("nan")), 2)
                    if unidade_cluster == "tete"
                    else ""
                ),
                "nota_metodo": (
                    "É o TETO publicado (mesmo valor da linha 'piso_teto'), mantido também "
                    "aqui, nomeado, por ser a variante que valida em Cidade de Tete "
                    f"({desvio_diag_tete:+.1f}% do observado): soma do GRID3 em todo o "
                    "cluster de Voronoi, sem nenhum peso de construído (equivale a atribuir "
                    "a célula inteira, mesmo se rural, ao ponto-sede mais próximo). A "
                    "validação mostra que é a PARTIÇÃO espacial, não o peso de construído, "
                    "que reproduz o observado — todo peso de construído (fração ou pertença) "
                    "SUBESTIMA."
                ),
            }
        )

    linhas.append(
        {
            "unidade_geografica": "Cidade de Tete",
            "ano_referencia": 2017,
            "metodo_peso": "validacao_cruzada",
            "populacao_observada_2017": resultado["tete"]["populacao_observada_2017"],
            "desvio_pct_classificacao_propria": round(
                resultado["tete"]["desvio_pct_estimativa_classificacao_propria"], 2
            ),
            "desvio_pct_ghsl_built_s": round(
                resultado["tete"]["desvio_pct_estimativa_ghsl_built_s"], 2
            ),
            "desvio_pct_pertenca_binaria": round(
                resultado["tete"]["desvio_pct_estimativa_pertenca_binaria"], 2
            ),
            "desvio_pct_pertenca_mediana": round(
                resultado["tete"]["desvio_pct_estimativa_pertenca_mediana"], 2
            ),
            "desvio_pct_diagnostico_sem_peso": round(
                resultado["tete"]["desvio_pct_diagnostico_sem_peso_construido"], 2
            ),
            # Selo da LINHA de comparação, não do valor observado em si: segue a mesma
            # regra do dashboard (demografia_dashboard.py) de que uma linha que toca
            # qualquer ponta modelada leva selo `modelado` — o `populacao_observada_2017`
            # citado dentro dela é `observado`, mas a linha como um todo mede um desvio
            # entre um observado e um modelado, e "desvio" em si é sempre modelado.
            "selo": "modelado",
            "nivel_fonte": "A",
            "nota_metodo": (
                "Mesmo procedimento (mesma grade GRID3, mesmas quatro variantes restritas "
                "por construído + a variante sem peso, mesma partição de Voronoi) aplicado "
                "a Cidade de Tete e comparado contra os "
                f"{resultado['tete']['populacao_observada_2017']} habitantes observados "
                "(HDX COD-PS 2017, nível A). O desvio percentual É o resultado — mede "
                "quanto confiar no número da Vila de Moatize, que usa o mesmo método sem "
                "âncora observada própria para se comparar. NENHUMA variante restrita por "
                "construído recupera o observado (desvios de −25% a −74%); só a partição "
                "sem peso (+1,61%) o faz — a conclusão é que o GRID3 já é dasimétrico e "
                "pesá-lo de novo pela máscara de construído restringe a população duas "
                "vezes. Não é um limiar de aprovação: publicado mesmo se grande, porque um "
                "desvio grande não invalida a entrega, invalida a pretensão de precisão do "
                "método, e isso tem de estar escrito."
            ),
        }
    )
    return linhas


def _faixa_desvio_restrito(r_tete: dict) -> str:
    """Faixa (menor–maior, em módulo) do desvio das quatro variantes RESTRITAS por
    construído, formatada em tempo de execução a partir de `resultado["tete"]` —
    nunca digitada (armadilha registrada: casar por igualdade de nome de coluna
    descarta em silêncio a variante 'diagnostico_sem_peso_construido', cujo desvio
    NÃO entra aqui por não ser restrita; ver `_common_desvios_restritos`)."""
    valores = [abs(v) for v in _desvios_restritos(r_tete).values()]
    return f"entre {min(valores):.0f}% e {max(valores):.0f}%"


def _desvios_restritos(r_tete: dict) -> dict[str, float]:
    """Desvios (%) das variantes RESTRITAS por construído, casados por PREFIXO
    (`desvio_pct_estimativa_*`) — nunca por igualdade de nome, e nunca a lista
    escrita à mão: se uma variante nova não casar, é erro, não omissão silenciosa."""
    prefixo = "desvio_pct_estimativa_"
    desvios = {k: v for k, v in r_tete.items() if k.startswith(prefixo)}
    esperadas = {
        "classificacao_propria",
        "ghsl_built_s",
        "pertenca_binaria",
        "pertenca_mediana",
    }
    achadas = {k[len(prefixo) :] for k in desvios}
    faltando = esperadas - achadas
    if faltando:
        raise KeyError(
            f"variante(s) restrita(s) sem desvio casado por prefixo: {sorted(faltando)}"
        )
    return desvios


def gravar_csv(linhas: list[dict], caminho: Path) -> None:
    caminho.parent.mkdir(parents=True, exist_ok=True)
    campos: list[str] = []
    for linha in linhas:
        for chave in linha:
            if chave not in campos:
                campos.append(chave)
    with caminho.open("w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=campos, restval="")
        w.writeheader()
        w.writerows(linhas)


def gravar_provenance_fragment(resultado: dict) -> None:
    r_vila = resultado["moatize_vila"]
    r_tete = resultado["tete"]
    tete_propria = r_tete["estimativa_classificacao_propria"]
    tete_propria_desvio = r_tete["desvio_pct_estimativa_classificacao_propria"]
    tete_ghsl = r_tete["estimativa_ghsl_built_s"]
    tete_ghsl_desvio = r_tete["desvio_pct_estimativa_ghsl_built_s"]
    tete_bin = r_tete["estimativa_pertenca_binaria"]
    tete_bin_desvio = r_tete["desvio_pct_estimativa_pertenca_binaria"]
    tete_med = r_tete["estimativa_pertenca_mediana"]
    tete_med_desvio = r_tete["desvio_pct_estimativa_pertenca_mediana"]
    tete_diag = r_tete["diagnostico_sem_peso_construido"]
    tete_diag_desvio = r_tete["desvio_pct_diagnostico_sem_peso_construido"]
    _est_propria = r_vila["estimativa_classificacao_propria"]
    linha_propria = (
        f"| classificação própria (fração) | restrita | {_est_propria:.0f} "
        f"| {tete_propria_desvio:+.1f}% |"
    )
    linha_ghsl = (
        f'| GHSL BUILT-S 2020 (fração) | restrita | {r_vila["estimativa_ghsl_built_s"]:.0f} '
        f"| {tete_ghsl_desvio:+.1f}% |"
    )
    linha_bin = (
        f'| pertença binária (fração > 0) | restrita | {r_vila["estimativa_pertenca_binaria"]:.0f} '
        f"| {tete_bin_desvio:+.1f}% |"
    )
    linha_med = (
        "| pertença por mediana (quantil, ADR 0014) | restrita | "
        f'{r_vila["estimativa_pertenca_mediana"]:.0f} | {tete_med_desvio:+.1f}% |'
    )
    linha_teto = (
        "| **sem peso de construído (cluster inteiro)** | **TETO** | "
        f'**{r_vila["teto"]:.0f}** | **{tete_diag_desvio:+.1f}%** |'
    )
    linha_piso = f'| **piso publicado** | menor das restritas | **{r_vila["piso"]:.0f}** | — |'
    texto = f"""{MARCADOR_INICIO}
## População da Vila de Moatize — estimativa dasimétrica de terceiros (§3, §5.3)

Script: `pipeline/02_metrics/populacao_vila_moatize.py`.
Gerado em {datetime.now(UTC).date().isoformat()}.
Correção de enquadramento em `docs/ADR/0017`: a banda deixou de ser composta só por
variantes atenuadas por máscara de construído — a única variante que valida em Cidade
de Tete (partição de Voronoi sem peso de construído) passou de "diagnóstico não
publicável" a TETO da banda.

### Por que este número não vem do HDX/INE

O HDX COD-PS só publica população por ADM2 (Distrito de Moatize). A Vila de Moatize é
ADM3 e não tem contagem oficial isolada em nenhuma fonte localizada (nível A ou B).

### O que a validação cruzada em Cidade de Tete mostrou (leia isto antes da tabela)

Nenhuma forma de aplicar a máscara de construído recupera o observado
({r_tete["populacao_observada_2017"]}, HDX COD-PS 2017) — nem o multiplicador de fração
(classificação própria: {tete_propria_desvio:+.1f}%; GHSL: {tete_ghsl_desvio:+.1f}%), nem
a pertença binária (fração > 0: {tete_bin_desvio:+.1f}%; fração ≥ mediana das células
presentes: {tete_med_desvio:+.1f}%). O GRID3 v1.1 já é um produto dasimétrico calibrado ao
Censo 2017: pesá-lo de novo por uma máscara de construído própria restringe a população
**duas vezes**, descartando gente que o produtor já havia colocado onde ela está. A única
variante que reproduz o observado é a partição espacial (Voronoi por sede mais próxima)
**sem nenhum peso de construído**: {tete_diag_desvio:+.1f}%. O que funciona é particionar,
não pesar.

### Banda — piso e teto (nenhum valor central)

| variante | tipo | estimativa (hab.) | desvio em Tete |
|---|---|---|---|
{linha_propria}
{linha_ghsl}
{linha_bin}
{linha_med}
{linha_teto}
{linha_piso}

Leitura: **piso** ({r_vila["piso"]:.0f}) restringe ao construído e, pela validação em
Tete, perde {_faixa_desvio_restrito(r_tete)} das pessoas que o GRID3 lá coloca — limite
INFERIOR.
**teto** ({r_vila["teto"]:.0f}) soma o GRID3 no cluster de Voronoi inteiro, sem peso de
construído — inclui a área rural do cluster atribuída à sede mais próxima, logo é
limite SUPERIOR para a vila, não a vila propriamente. Nenhuma das cinco variantes é
publicada como "a estimativa"; cada uma é nomeada em
`populacao_vila_moatize_sensibilidade.csv`.

Ano de referência: 2017 (calibração do GRID3). Um único ponto — não há série, não há
CAGR. Selo `modelado`, nível de fonte `A` (GRID3 é CC BY 4.0, produtor institucional
WorldPop/Southampton — ver `data/provenance_parts/worldpop_grid3.md`), mas **não é
contagem**: é estimativa dasimétrica de terceiros sobre uma grade já modelada.

### Validação cruzada em Cidade de Tete — tabela completa

O mesmo procedimento aplicado a Cidade de Tete, comparado contra os
{r_tete["populacao_observada_2017"]} habitantes observados (HDX COD-PS 2017, nível A):

| variante | estimativa (hab.) | desvio frente ao observado |
|---|---|---|
| classificação própria (fração) | {tete_propria:.0f} | {tete_propria_desvio:+.1f}% |
| GHSL BUILT-S 2020 (fração) | {tete_ghsl:.0f} | {tete_ghsl_desvio:+.1f}% |
| pertença binária (fração > 0) | {tete_bin:.0f} | {tete_bin_desvio:+.1f}% |
| pertença por mediana (quantil) | {tete_med:.0f} | {tete_med_desvio:+.1f}% |
| sem peso de construído (teto) | {tete_diag:.0f} | {tete_diag_desvio:+.1f}% |

Este desvio — não um limiar de aprovação — é a medida de quanto confiar na estimativa da
Vila de Moatize, que usa exatamente o mesmo método sem ter uma âncora observada própria
contra a qual se comparar. Publicado mesmo se grande: **toda variante restrita por
construído SUBESTIMA** a população observada de Cidade de Tete; só a partição sem peso
não subestima. **A estimativa da Vila herda esse mesmo viés** — toda variante restrita
publicada na banda é, à luz desta validação, mais provável de subestimar do que de
superestimar a população real da vila; o teto é a única variante que a validação não
desqualifica, ao custo de incluir população rural do cluster.

### Correção da nota de comissão (dois referentes, não um)

O peso 'classificação própria' carrega a comissão medida na classe construído
({acuracia_texto.nota_comissao_construido()}). Essa comissão tem DUAS relações
distintas, cada uma com seu referente: frente ao peso GHSL (o outro multiplicador de
fração), tende a puxar a estimativa para CIMA. Frente à população OBSERVADA em Cidade
de Tete, a mesma variante SUBESTIMA em {abs(tete_propria_desvio):.1f}% — a comissão de
área não é grande o suficiente para compensar a dupla restrição imposta pela máscara
sobre um GRID3 que já é dasimétrico.

### Saídas

`data/processed/populacao_vila_moatize_sensibilidade.csv` (as cinco variantes, piso/teto
para Vila e Tete, mais a linha `validacao_cruzada`). Linha em
`data/processed/demografia_serie_1997_2025.csv` (unidade "Vila de Moatize", ano 2017,
`selo=modelado`, `nivel_fonte=A`, valor publicado = TETO — a variante validada —, com
piso/desvios explícitos em `nota`, `comparabilidade` explicando a natureza do número).
`config/unidades.yaml`: `moatize_vila` continua `comparavel_entre_familias: false` —
existe estimativa modelada agora, mas continua não sendo contagem, e nenhuma razão
população/área com essa vila deixa de ser inválida por causa disso.

{MARCADOR_FIM}
"""
    PROVENANCE_FRAGMENT.write_text(texto, encoding="utf-8")


def main() -> int:
    resultado, _ = estimar()
    linhas = montar_linhas_sensibilidade(resultado)
    gravar_csv(linhas, SAIDA_CSV)
    print(f"[ok] {SAIDA_CSV.relative_to(REPO_ROOT)} ({len(linhas)} linhas)", file=sys.stderr)

    gravar_provenance_fragment(resultado)
    print(f"[ok] {PROVENANCE_FRAGMENT.relative_to(REPO_ROOT)}", file=sys.stderr)

    r_vila = resultado["moatize_vila"]
    r_tete = resultado["tete"]
    desvio_propria = r_tete["desvio_pct_estimativa_classificacao_propria"]
    desvio_ghsl = r_tete["desvio_pct_estimativa_ghsl_built_s"]
    desvio_bin = r_tete["desvio_pct_estimativa_pertenca_binaria"]
    desvio_med = r_tete["desvio_pct_estimativa_pertenca_mediana"]
    desvio_teto = r_tete["desvio_pct_diagnostico_sem_peso_construido"]
    print(
        f"[resumo] Vila de Moatize: piso={r_vila['piso']:.0f} teto={r_vila['teto']:.0f} "
        "(teto = partição sem peso de construído, única variante validada em Tete); "
        f"validação Tete: propria={desvio_propria:+.1f}% ghsl={desvio_ghsl:+.1f}% "
        f"pertenca_bin={desvio_bin:+.1f}% pertenca_mediana={desvio_med:+.1f}% "
        f"sem_peso(teto)={desvio_teto:+.1f}%",
        file=sys.stderr,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
