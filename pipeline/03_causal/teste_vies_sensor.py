#!/usr/bin/env python3
"""pipeline/03_causal/teste_vies_sensor.py — o viés de detecção cresce com o tempo?

## Por que este script existe (§5.4, e não §5.1)

A série própria de área construída e o WSF Evolution **discordam na direção da
tendência** entre 2000 e 2015:

| período   | classificação | WSF     |
|-----------|---------------|---------|
| 2000–2005 | 7,7 %/ano     | 2,6 %/ano |
| 2005–2010 | 7,3 %/ano     | 3,4 %/ano |
| 2010–2015 | 5,9 %/ano     | 4,2 %/ano |

A classificação **desacelera**; o WSF **acelera**. A razão entre as duas sobe
monotonicamente (0,4 → 0,5 → 0,6 → 0,7). Depois de `docs/ADR/0003`, H1 é uma
hipótese sobre **aceleração da área construída** — as duas fontes respondem o
oposto à pergunta central. Um viés que cresce monotonicamente é indistinguível
de tendência, e é exatamente o que o desenho causal de §5.4 (séries
interrompidas, DiD) leria como efeito do tratamento. Por isso o teste é do
agente de desenho causal, não do de imagem.

## Hipóteses concorrentes, e como cada uma é testada aqui

- **H-obs — capacidade de observação.** O número mediano de observações válidas
  por pixel na estação seca cresce 3 → 4 → 4 → 10 → 31 → 42 de 2000 a 2025. Uma
  mediana de 3 observações é muito mais ruidosa que uma de 42; se a detecção de
  construído esparso melhora com o número de observações, o crescimento medido
  é confundido com a capacidade de medir. Testado por **degradação** (parte B):
  reconstrói-se um ano recente com o número de cenas e o sensor de um ano
  antigo, e reclassifica-se com protocolo idêntico.
- **H-S2 — entrada do Sentinel-2.** Testada e **descartada por inspeção dos
  metadados** (parte A): o composto de estação seca de 2015 **não tem
  Sentinel-2** (`colecao_sentinel2: null` em
  `composto_2015_30m_32736.tif.meta.json`) — a janela é mai–out/2015 e o S2 L2A
  só cobre a AOI a partir de dez/2015. O S2 entra apenas em 2020 e 2025.
  Portanto o S2 **não pode** explicar a divergência 2000–2015, que é justamente
  onde o WSF existe e a discordância aparece. O teste pedido ("2015 com e sem
  S2") é vazio; o teste com conteúdo é 2020 com e sem S2, feito na parte B.
- **H-morf — geometria do próprio protocolo.** O classificador (i) semeia o
  treino com o WSF **erodido 3×3** e (ii) filtra a predição por coerência
  espacial 3×3 (maioria 5/9). Ambas as operações removem borda, e removem uma
  fração **maior** de manchas pequenas e fragmentadas que de manchas grandes e
  compactas. Se a mancha de 2000 for mais fragmentada que a de 2015 — o que é
  esperado numa cidade que adensa —, a razão classificação/WSF sobe com o tempo
  **sem nenhum viés de sensor**. Testado na parte A aplicando as mesmas
  operações morfológicas ao próprio WSF, sem tocar em imagem.
- **H-def — definições diferentes.** WSF Evolution mapeia *settlement extent*
  (mancha de assentamento, inclusive solo e quintal entre construções); a
  camada `urbano` daqui é predição espectral de construído. Não são a mesma
  grandeza. Parte A mede quanto do construído classificado cai **dentro** do
  WSF, o que separa "detecto menos dentro da mesma mancha" de "detecto outra
  coisa em outro lugar".

## O que o script NÃO faz

Não decide se H1 é testável — isso é uma conclusão escrita, e vai para
`docs/ADR/0008-vies-de-sensor-na-serie.md` com os números daqui. Não altera a
série publicada. Não reescreve `area_construida_por_ano.csv`.

Saídas:
  data/processed/causal/teste_vies_morfologia.csv   (parte A)
  data/processed/causal/teste_vies_degradacao.csv   (parte B)
  data/processed/causal/teste_vies_sensor.meta.json

Uso:
  uv run python pipeline/03_causal/teste_vies_sensor.py morfologia
  uv run python pipeline/03_causal/teste_vies_sensor.py degradacao 2020
"""

from __future__ import annotations

import csv
import json
import sys
from datetime import UTC, datetime
from pathlib import Path

import numpy as np
import rasterio
import xarray as xr
from scipy import ndimage

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT / "pipeline" / "01_imagery"))

import classificacao as clf  # noqa: E402
import compostos as cmp  # noqa: E402
import indices as idx  # noqa: E402
from _stac_common import (  # noqa: E402
    PLATAFORMA_STAC_POR_MISSAO,
    abrir_cliente_stac,
    compor_mediana,
    contar_observacoes_validas,
)
from compostos import (  # noqa: E402
    carregar_colecao_mascarada,
    combinar_fontes,
    construir_geobox,
    janela_datas,
)
from compostos_chuva import (  # noqa: E402
    MIN_OBS_POR_PIXEL,
    NUVEM_MAX_PCT_CHUVA,
    janela_chuva,
)

SAIDA = REPO_ROOT / "data" / "processed" / "causal"
MORFOLOGIA_CSV = SAIDA / "teste_vies_morfologia.csv"
DEGRADACAO_CSV = SAIDA / "teste_vies_degradacao.csv"
META_JSON = SAIDA / "teste_vies_sensor.meta.json"

ANOS_WSF = [2000, 2005, 2010, 2015]


def area_km2(mask: np.ndarray, transform) -> float:
    return float(mask.sum()) * abs(transform.a * transform.e) / 1e6


def perfil_de_referencia() -> dict:
    caminho = clf.DATA_PROCESSED / "composto_2000_30m_32736.tif"
    with rasterio.open(caminho) as src:
        return {"crs": src.crs, "transform": src.transform, "shape": src.shape}


def construido_classificado(ano: int) -> np.ndarray | None:
    """União urbano+industrial+reassentamento do produto publicado (pós-R2)."""
    partes = []
    for camada in ("urbano", "industrial", "reassentamento"):
        caminho = clf.DATA_PROCESSED / f"{camada}_{ano}_30m_32736.tif"
        if not caminho.exists():
            continue
        with rasterio.open(caminho) as src:
            partes.append(src.read(1) > 0)
    if not partes:
        return None
    return np.logical_or.reduce(partes)


def morfologia() -> list[dict]:
    """Parte A — H-morf e H-def, sem tocar em imagem.

    Para cada ano com WSF, mede:
      - área WSF bruta;
      - área WSF após erosão 3×3 (a operação que gera os POSITIVOS de treino);
      - área WSF após o filtro de coerência 3×3 (a operação aplicada à PREDIÇÃO);
      - área WSF após as duas em sequência (piso geométrico do protocolo);
      - fração do construído classificado que cai dentro do WSF (H-def);
      - fragmentação do WSF (n de manchas, mediana de pixels por mancha).
    """
    perfil = perfil_de_referencia()
    wsf = clf.carregar_wsf_reprojetado(perfil)
    transform = perfil["transform"]
    estrutura = np.ones((3, 3), dtype=bool)

    linhas = []
    for ano in ANOS_WSF:
        m = (wsf > 0) & (wsf <= ano)
        erodido = ndimage.binary_erosion(m, structure=estrutura)
        coerente = clf.filtrar_coerencia_espacial(m)
        ambos = clf.filtrar_coerencia_espacial(erodido)

        rotulado, n_manchas = ndimage.label(m, structure=estrutura)
        tamanhos = np.bincount(rotulado.ravel())[1:] if n_manchas else np.array([0])

        cls = construido_classificado(ano)
        if cls is not None:
            dentro = float((cls & m).sum()) / max(float(cls.sum()), 1.0)
            area_cls = area_km2(cls, transform)
        else:
            dentro, area_cls = float("nan"), float("nan")

        a_wsf = area_km2(m, transform)
        linhas.append(
            {
                "ano": ano,
                "area_wsf_km2": round(a_wsf, 3),
                "area_wsf_erodido_km2": round(area_km2(erodido, transform), 3),
                "area_wsf_coerencia_km2": round(area_km2(coerente, transform), 3),
                "area_wsf_erodido_e_coerencia_km2": round(area_km2(ambos, transform), 3),
                "razao_piso_geometrico": round(area_km2(ambos, transform) / a_wsf, 4),
                "n_manchas_wsf": int(n_manchas),
                "mediana_px_por_mancha": float(np.median(tamanhos)),
                "p90_px_por_mancha": float(np.percentile(tamanhos, 90)),
                "area_classificada_km2": round(area_cls, 3),
                "razao_classificado_wsf": round(area_cls / a_wsf, 4),
                "fracao_classificado_dentro_do_wsf": round(dentro, 4),
            }
        )
    return linhas


# ---------------------------------------------------------------------------
# Parte B — degradação à capacidade de observação de um ano antigo
# ---------------------------------------------------------------------------

# Perfil de capacidade do ano de referência antigo (medido, não presumido):
# `composto_2000_30m_32736.tif.meta.json` -> 3 cenas Landsat-7 na estação seca;
# `data/processed/cobertura_estacao_chuvosa.csv` -> 6 cenas na estação chuvosa.
PERFIL_ANO_ANTIGO = {"ano": 2000, "n_cenas_seca": 3, "n_cenas_chuva": 6}


def _subconjunto_uniforme(itens: list, n: int) -> list:
    """Escolhe `n` itens espaçados uniformemente na ordem temporal.

    Determinístico e sem RNG (não há seed a declarar). Espaçar em vez de pegar
    os `n` primeiros preserva a cobertura sazonal da janela — as 3 cenas de 2000
    se distribuem de julho a outubro, não se amontoam num mês. Pegar as
    primeiras trocaria o efeito de "menos observações" pelo efeito de "outra
    parte da estação seca", que é uma confusão diferente.
    """
    if n >= len(itens):
        return list(itens)
    ordenados = sorted(itens, key=lambda it: it.datetime)
    passo = (len(ordenados) - 1) / (n - 1) if n > 1 else 0
    escolhidos = [ordenados[round(i * passo)] for i in range(n)]
    return sorted(escolhidos, key=lambda it: it.id)


class _LimitarCenas:
    """Faz `carregar_colecao_mascarada` enxergar só um subconjunto das cenas.

    A alternativa seria duplicar o carregador com um parâmetro a mais. Este
    caminho garante que a degradação passa **exatamente** pelo mesmo código de
    máscara, escala, reamostragem e composição do produto publicado — a única
    diferença entre o composto degradado e o cheio é o conjunto de cenas, que é
    o que se quer medir.
    """

    def __init__(self, limites: dict[str, int | None]):
        self.limites = limites
        # `compostos.carregar_colecao_mascarada` chama `buscar_itens` pelo nome
        # JÁ IMPORTADO no namespace de `compostos` (`from _stac_common import
        # buscar_itens`). Substituir `_stac_common.buscar_itens` não teria
        # efeito nenhum — e não teve, na primeira execução deste teste: os três
        # cenários devolveram exatamente a mesma área porque as três rodadas
        # usaram as mesmas 10 cenas. O ponto de troca correto é o namespace de
        # `compostos`.
        self.original = cmp.buscar_itens
        self.usados: dict[str, list] = {}

    def __enter__(self):
        def wrapper(client, colecao, *args, **kwargs):
            itens = self.original(client, colecao, *args, **kwargs)
            limite = self.limites.get(colecao, None)
            if limite == 0:
                itens = []
            elif limite is not None:
                itens = _subconjunto_uniforme(itens, limite)
            self.usados[colecao] = itens
            return itens

        cmp.buscar_itens = wrapper
        return self

    def __exit__(self, *exc):
        cmp.buscar_itens = self.original
        return False


def _bbox_lista(estudo: dict) -> list[float]:
    b = estudo["aoi"]["bbox"]
    return [b["xmin"], b["ymin"], b["xmax"], b["ymax"]]


def _composto_seca(ano, estudo, client, geobox, limites) -> tuple[xr.Dataset, np.ndarray, dict]:
    cfg = estudo["composto"]
    sensor = estudo["sensores"][ano]
    faixa, _, _ = janela_datas(
        ano, cfg["estacao_seca"]["mes_inicio"], cfg["estacao_seca"]["mes_fim"], cfg["janela_anos"]
    )
    with _LimitarCenas(limites):
        bandas_l, itens_l = carregar_colecao_mascarada(
            client, "landsat-c2-l2", _bbox_lista(estudo), faixa, cfg["nuvem_max_pct"],
            geobox, PLATAFORMA_STAC_POR_MISSAO[sensor["missao"]],
        )
        bandas_s2, itens_s2 = (None, [])
        if "S2" in sensor.get("complemento", "") and limites.get("sentinel-2-l2a") != 0:
            bandas_s2, itens_s2 = carregar_colecao_mascarada(
                client, "sentinel-2-l2a", _bbox_lista(estudo), faixa,
                cfg["nuvem_max_pct"], geobox,
            )
    combinadas = combinar_fontes(bandas_l, bandas_s2)
    nobs = contar_observacoes_validas(combinadas).compute()
    composto = compor_mediana(combinadas).compute()
    info = {
        "janela_seca": faixa,
        "n_cenas_landsat_seca": len(itens_l),
        "n_cenas_s2_seca": len(itens_s2),
        "mediana_obs_por_pixel_seca": float(nobs.median()),
    }
    return composto, nobs.values, info


def _ndvi_chuva(ano, estudo, client, geobox, limites) -> tuple[np.ndarray, dict]:
    cfg = estudo["composto_fenologico"]["estacao_chuvosa"]
    sensor = estudo["sensores"][ano]
    faixa = janela_chuva(ano, cfg["mes_inicio"], cfg["mes_fim"])
    with _LimitarCenas(limites):
        bandas_l, itens_l = carregar_colecao_mascarada(
            client, "landsat-c2-l2", _bbox_lista(estudo), faixa, NUVEM_MAX_PCT_CHUVA,
            geobox, PLATAFORMA_STAC_POR_MISSAO[sensor["missao"]],
        )
        bandas_s2, itens_s2 = (None, [])
        if "S2" in sensor.get("complemento", "") and limites.get("sentinel-2-l2a") != 0:
            bandas_s2, itens_s2 = carregar_colecao_mascarada(
                client, "sentinel-2-l2a", _bbox_lista(estudo), faixa,
                NUVEM_MAX_PCT_CHUVA, geobox,
            )
    combinadas = combinar_fontes(bandas_l, bandas_s2)
    nobs = contar_observacoes_validas(combinadas).compute()
    composto = compor_mediana(combinadas).compute()
    arr = idx.calcular_ndvi(composto).values
    arr = np.where(nobs.values >= MIN_OBS_POR_PIXEL, arr, np.nan)
    info = {
        "janela_chuva": faixa,
        "n_cenas_landsat_chuva": len(itens_l),
        "n_cenas_s2_chuva": len(itens_s2),
        "mediana_obs_por_pixel_chuva": float(nobs.median()),
    }
    return arr, info


def _features_de_composto(composto: xr.Dataset, ndvi_chuva: np.ndarray) -> dict:
    """Mesma pilha de features de `clf.carregar_features_ano`, mesma ordem,
    mesmas funções de índice — só que a partir de arrays em memória.
    """
    indices = {
        nome: idx.CALCULADORAS[nome.upper()](composto).values for nome in clf.INDICES_SECA
    }
    indices["ndvi_chuva"] = ndvi_chuva
    indices["ndvi_amplitude"] = ndvi_chuva - indices["ndvi"]
    bandas = {nome: composto[nome].values.astype("float32") for nome in clf.BANDAS_COMUNS}
    empilhados = np.stack(
        [indices[n] for n in [*clf.INDICES_SECA, *clf.INDICES_FENOLOGICOS]]
        + [bandas[n] for n in clf.BANDAS_COMUNS]
    )
    return {
        "empilhados": empilhados,
        "mask_valida": np.all(np.isfinite(empilhados), axis=0),
        "indices": indices,
    }


def degradacao(ano_alvo: int, cenarios: list[dict]) -> list[dict]:
    """Parte B — reconstrói `ano_alvo` sob capacidades de observação reduzidas
    e reclassifica com protocolo idêntico. A comparação é sempre RF puro contra
    RF puro (as regras temporais R1/R2 são da série, não de um ano isolado).
    """
    estudo = clf.carregar_yaml(clf.STUDY_YAML)
    seeds_cfg = clf.carregar_yaml(clf.SEEDS_YAML)
    client = abrir_cliente_stac()
    geobox = construir_geobox(estudo["aoi"]["bbox"], estudo["crs"]["metrico"], 30)

    perfil = perfil_de_referencia()
    wsf = clf.carregar_wsf_reprojetado(perfil)
    poligono_mineracao = clf.carregar_poligono_mineracao(perfil["crs"])
    buffers, _ = clf.carregar_buffers_reassentamento(perfil["crs"])
    excluir = clf.rasterizar(poligono_mineracao, perfil)
    for item in buffers:
        excluir |= clf.rasterizar(item["geometria"], perfil)

    linhas = []
    for cenario in cenarios:
        limites = cenario["limites"]
        composto, _, info_seca = _composto_seca(ano_alvo, estudo, client, geobox, limites)
        ndvi_chuva, info_chuva = _ndvi_chuva(ano_alvo, estudo, client, geobox, limites)
        feats = _features_de_composto(composto, ndvi_chuva)
        _, bruta, _ = clf.classificar_ano(
            ano_alvo, feats, wsf, excluir, 30.0, seeds_cfg
        )
        linhas.append(
            {
                "ano_alvo": ano_alvo,
                "cenario": cenario["nome"],
                **info_seca,
                **info_chuva,
                "area_construida_rf_puro_km2": round(area_km2(bruta, perfil["transform"]), 3),
                "fracao_pixels_validos": round(float(feats["mask_valida"].mean()), 4),
            }
        )
        print(f"[deg] {cenario['nome']}: {linhas[-1]['area_construida_rf_puro_km2']} km²",
              file=sys.stderr)
    return linhas


def escrever_csv(linhas: list[dict], caminho: Path, nota: str) -> None:
    caminho.parent.mkdir(parents=True, exist_ok=True)
    campos = [*linhas[0].keys(), "nota"]
    with caminho.open("w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=campos)
        w.writeheader()
        for linha in linhas:
            w.writerow({**linha, "nota": nota})


def escrever_meta(bloco: str, conteudo: dict) -> None:
    META_JSON.parent.mkdir(parents=True, exist_ok=True)
    meta = {}
    if META_JSON.exists():
        meta = json.loads(META_JSON.read_text(encoding="utf-8"))
    meta[bloco] = {
        **conteudo,
        "data_processamento": datetime.now(UTC).isoformat(),
        "script": "pipeline/03_causal/teste_vies_sensor.py",
        "selo": "diagnostico",
    }
    META_JSON.write_text(json.dumps(meta, indent=2, ensure_ascii=False), encoding="utf-8")


def main(argv: list[str]) -> int:
    modo = argv[0] if argv else "morfologia"
    if modo == "morfologia":
        linhas = morfologia()
        nota = (
            "Parte A do teste de viés de sensor (§5.4). Operações morfológicas do "
            "protocolo (erosão 3x3 do treino, coerência 3x3 da predição) aplicadas ao "
            "PRÓPRIO WSF, sem imagem: mede quanto da razão classificação/WSF é "
            "geometria do protocolo e não capacidade de detecção."
        )
        escrever_csv(linhas, MORFOLOGIA_CSV, nota)
        escrever_meta(
            "morfologia",
            {
                "fonte_mascara": "WSF Evolution (DLR) reprojetado para a grade do estudo",
                "erosao": "3x3 (clf.rotulos_treino)",
                "coerencia": "maioria 5/9 em janela 3x3 (clf.filtrar_coerencia_espacial)",
                "saida": str(MORFOLOGIA_CSV.relative_to(REPO_ROOT)),
            },
        )
        print(f"[ok] {MORFOLOGIA_CSV.relative_to(REPO_ROOT)}", file=sys.stderr)
        return 0
    if modo == "degradacao":
        ano_alvo = int(argv[1]) if len(argv) > 1 else 2015
        cenarios = [
            {"nome": "cheio (produto publicado)", "limites": {}},
            {
                "nome": "sem_sentinel2",
                "limites": {"sentinel-2-l2a": 0},
            },
            {
                "nome": f"capacidade_de_{PERFIL_ANO_ANTIGO['ano']}",
                "limites": {
                    "landsat-c2-l2": PERFIL_ANO_ANTIGO["n_cenas_seca"],
                    "sentinel-2-l2a": 0,
                },
            },
        ]
        linhas = degradacao(ano_alvo, cenarios)
        nota = (
            "Parte B do teste de viés de sensor (§5.4). Mesmo ano, mesmo protocolo, "
            "mesma seed, mesmo treino; muda só o conjunto de cenas. A diferença de "
            "área entre 'cheio' e 'capacidade_de_2000' é a estimativa direta do viés "
            "de capacidade de observação embutido na tendência. Comparação sempre "
            "RF puro x RF puro (sem R1/R2, que são regras da série). Limite declarado: "
            "degrada o NÚMERO de observações e a presença do Sentinel-2, NÃO a "
            "radiometria do sensor (ETM+ 8 bits x OLI 12 bits) — o viés real é, por "
            "esse lado, subestimado."
        )
        escrever_csv(linhas, DEGRADACAO_CSV, nota)
        escrever_meta(
            "degradacao",
            {
                "ano_alvo": ano_alvo,
                "perfil_ano_antigo": PERFIL_ANO_ANTIGO,
                "regra_de_selecao_de_cenas": "espaçamento uniforme na ordem temporal",
                "saida": str(DEGRADACAO_CSV.relative_to(REPO_ROOT)),
            },
        )
        print(f"[ok] {DEGRADACAO_CSV.relative_to(REPO_ROOT)}", file=sys.stderr)
        return 0
    print(f"modo desconhecido: {modo}", file=sys.stderr)
    return 2


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
