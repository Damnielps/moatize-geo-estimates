#!/usr/bin/env python3
"""pipeline/02_metrics/edificacoes.py — §5.2 item 5: densidade de edificações e
regularidade da malha como proxy de urbanização formal × informal.

## O que este módulo entrega, e o que NÃO entrega

A tarefa pede "densidade de edificações e regularidade da malha (Open Buildings +
OSM)". Este módulo usa **só o Google Open Buildings v3**
(`data/raw/open_buildings_v3_aoi.csv`, nível A — ver
`pipeline/00_fetch/fetch_open_buildings.py`). **Não há, neste repositório, um
extrator de malha viária OSM** (`pipeline/00_fetch/fetch_osm_reassentamentos.sh`
só resolve os pontos-sede dos povoados de reassentamento, não a rede de vias).
Construir e validar um fetch de rede viária OSM está fora do escopo desta
entrega — fica registrado como pendência, não simulado. A regularidade da malha
publicada aqui é, portanto, um **proxy parcial**, calculado só a partir da
geometria das edificações:

- regularidade do **espaçamento** entre edificações (distância ao vizinho mais
  próximo, coeficiente de variação);
- regularidade do **tamanho** das edificações (área, coeficiente de variação).

Malha regular (baixo CV nas duas dimensões) é lida como proxy de assentamento
planejado/formal; malha irregular (CV alto), como proxy de crescimento
espontâneo/informal — na linha de Ludeña (2002) e da literatura de textura
urbana usada em WSF/GHSL para inferir informalidade sem parcela cadastral. É
uma leitura indireta, não uma classificação formal/informal validada em campo.

## Epoch único, não série temporal

Open Buildings v3 é um retrato de imagem de alta resolução ~2021–2023 (Google
não publica data de aquisição por edifício nesta AOI) — **não existe série por
ano-âncora**. Todas as linhas aqui usam `ano=2023` como aproximação do epoch de
aquisição, com a imprecisão declarada em `nota`. Para comparar com área
construída por ano, a linha usa a camada de classificação própria mais próxima
no tempo (`urbano`+`industrial`+`reassentamento`, ano-âncora 2020 — o mais
próximo <= epoch disponível) só como **denominador de densidade**, com a
mesma ressalva de comissão do ADR 0009 herdada dessa camada.

## Unidade de atribuição

Cada edificação (centróide lat/lon) é atribuída ao ponto-sede mais próximo
(mesma partição de Voronoi de `_common.atribuir_unidade_mais_proxima`, agora
sobre pontos em vez de pixels) entre `tete`, `moatize`, `cateme`, `mwaladzi`.
Mesma ressalva de "25 de Setembro" das demais métricas: sem geometria própria,
qualquer edificação desse povoado cai em `moatize` por proximidade.

## Filtro de confiança

Google recomenda confidence >= 0,65 como piso de qualidade para o v3 nesta
região (é o próprio piso do bloco: mínimo observado na AOI = 0,65). Não se
aplica filtro adicional — reportar a distribuição de confiança já é a
validação disponível nesta entrega; nenhum ponto é descartado por confiança
abaixo de um limiar mais alto que não foi calibrado para esta AOI.

Uso: `uv run python pipeline/02_metrics/edificacoes.py`
"""

from __future__ import annotations

import csv
import sys
from pathlib import Path

import numpy as np
from pyproj import Transformer
from scipy.spatial import cKDTree

sys.path.insert(0, str(Path(__file__).resolve().parent))
import _common as c

UNIDADES = ["tete", "moatize_vila", "cateme", "mwaladzi"]
ANO_EPOCH_APROX = 2023
ANO_DENOMINADOR_AREA = 2020
FONTE_OB = (
    "Google Open Buildings v3, recorte AOI — data/raw/open_buildings_v3_aoi.csv "
    "(ver data/raw/open_buildings_v3_aoi.csv.meta.json)"
)


def _ler_edificacoes(epsg: int) -> dict[str, np.ndarray]:
    """Lê o CSV recortado e devolve coordenadas UTM, área (m²) e confiança."""
    transformer = Transformer.from_crs("EPSG:4326", f"EPSG:{epsg}", always_xy=True)
    lons, lats, areas, confs = [], [], [], []
    with open(c.OPEN_BUILDINGS_CSV, encoding="utf-8") as f:
        for row in csv.DictReader(f):
            lons.append(float(row["longitude"]))
            lats.append(float(row["latitude"]))
            areas.append(float(row["area_in_meters"]))
            confs.append(float(row["confidence"]))
    lons_a, lats_a = np.asarray(lons), np.asarray(lats)
    xs, ys = transformer.transform(lons_a, lats_a)
    return {
        "x": np.asarray(xs),
        "y": np.asarray(ys),
        "area_m2": np.asarray(areas),
        "confianca": np.asarray(confs),
    }


def _atribuir_pontos(
    xs: np.ndarray, ys: np.ndarray, pontos: dict[str, tuple[float, float]]
) -> np.ndarray:
    nomes = list(pontos.keys())
    arvore = cKDTree(np.array([pontos[n] for n in nomes]))
    _, idx = arvore.query(np.column_stack([xs, ys]))
    return np.array([nomes[i] for i in idx])


def _cv(x: np.ndarray) -> float | None:
    if x.size < 2:
        return None
    m = float(np.mean(x))
    if m == 0:
        return None
    return float(np.std(x, ddof=1) / m)


def _dist_vizinho_mais_proximo(xs: np.ndarray, ys: np.ndarray) -> np.ndarray:
    """Distância de cada edificação à edificação mais próxima (excluindo si)."""
    pts = np.column_stack([xs, ys])
    arvore = cKDTree(pts)
    dist, _ = arvore.query(pts, k=2)
    return dist[:, 1]


def _area_construida_denominador_km2(epsg: int, pontos: dict) -> dict[str, float]:
    """Área construída (classificação própria, ano mais próximo do epoch OB) por
    unidade — só para densidade, com a ressalva de comissão da camada."""
    construido, perfil = c.carregar_construido_total(ANO_DENOMINADOR_AREA, epsg=epsg)
    pontos_urbano = {k: v for k, v in pontos.items() if k in UNIDADES}
    partes = c.atribuir_unidade_mais_proxima(construido, perfil["transform"], pontos_urbano)
    return {u: c.area_km2(partes[u]) for u in UNIDADES}


def linhas(estudo: dict, epsg: int) -> list[dict]:
    del estudo  # não há anos-âncora aplicáveis a este epoch único
    dados = _ler_edificacoes(epsg)
    pontos = c.pontos_sede_utm(epsg)
    atribuicao = _atribuir_pontos(dados["x"], dados["y"], pontos)
    areas_km2 = _area_construida_denominador_km2(epsg, pontos)

    linhas_out: list[dict] = []
    for u in UNIDADES:
        sel = atribuicao == u
        n = int(sel.sum())
        xs_u, ys_u = dados["x"][sel], dados["y"][sel]
        areas_u = dados["area_m2"][sel]
        confs_u = dados["confianca"][sel]
        area_km2_u = areas_km2.get(u, 0.0)

        nota_25_setembro = (
            "Inclui edificações do povoado '25 de Setembro' (geometry: null, não "
            "localizável), atribuídas a moatize por proximidade — não separável de "
            "crescimento orgânico com os dados disponíveis (restrição 3)."
            if u == "moatize_vila"
            else ""
        )
        nota_epoch = (
            f"Epoch de Open Buildings v3 aproximado como {ANO_EPOCH_APROX} "
            "(Google não publica data de aquisição por edifício nesta AOI). "
            "Não é série temporal — comparável só ao ano informado."
        )

        densidade_km2 = (n / area_km2_u) if area_km2_u > 0 else None
        linhas_out.append(
            _linha(
                u,
                "n_edificacoes",
                n,
                "contagem",
                (
                    f"{nota_epoch} {nota_25_setembro}".strip()
                    + f" confiança mín/méd/máx na unidade: "
                    f"{confs_u.min():.2f}/{confs_u.mean():.2f}/{confs_u.max():.2f}."
                    if n > 0
                    else nota_epoch
                ),
            )
        )
        linhas_out.append(
            _linha(
                u,
                "densidade_edificacoes_km2",
                round(densidade_km2, 2) if densidade_km2 is not None else None,
                "edificacoes_por_km2",
                (
                    f"Denominador: área construída (classificação própria, ano "
                    f"{ANO_DENOMINADOR_AREA}, urbano+industrial+reassentamento) = "
                    f"{area_km2_u:.4f} km2 — SENSÍVEL à comissão medida (acurácia do "
                    "usuário 0,27-0,63, ADR 0009) porque o denominador vem da "
                    "classificação própria, não do WSF. "
                    + (
                        "sem área construída na unidade nesse ano — densidade indefinida"
                        if area_km2_u == 0
                        else ""
                    )
                ),
            )
        )

        area_media = float(np.mean(areas_u)) if n > 0 else None
        cv_area = _cv(areas_u) if n > 1 else None
        linhas_out.append(
            _linha(
                u,
                "area_media_edificacao_m2",
                round(area_media, 2) if area_media is not None else None,
                "m2",
                nota_epoch,
            )
        )
        linhas_out.append(
            _linha(
                u,
                "regularidade_tamanho_cv",
                round(cv_area, 4) if cv_area is not None else None,
                "adimensional_cv",
                (
                    "Coeficiente de variação (desvio-padrão/média) da área das "
                    "edificações. Menor = tamanhos mais homogêneos = proxy de malha "
                    "mais regular/planejada; maior = mistura de portes = proxy de "
                    "informalidade. Proxy indireto, não validado em campo. "
                    + nota_epoch
                ),
            )
        )

        if n > 1:
            dnn = _dist_vizinho_mais_proximo(xs_u, ys_u)
            dist_media = float(np.mean(dnn))
            cv_dist = _cv(dnn)
        else:
            dist_media = None
            cv_dist = None
        linhas_out.append(
            _linha(
                u,
                "dist_media_vizinho_mais_proximo_m",
                round(dist_media, 2) if dist_media is not None else None,
                "m",
                nota_epoch,
            )
        )
        linhas_out.append(
            _linha(
                u,
                "regularidade_espacamento_cv",
                round(cv_dist, 4) if cv_dist is not None else None,
                "adimensional_cv",
                (
                    "Coeficiente de variação da distância ao vizinho mais próximo "
                    "entre edificações. Menor = espaçamento mais uniforme (malha "
                    "regular, proxy de formal); maior = espaçamento errático (proxy "
                    "de informal). Componente de rede viária OSM NÃO incluída — "
                    "não há extrator de malha viária OSM neste repositório (ver "
                    "docstring do módulo). Proxy parcial, só geometria de edificação. "
                    + nota_epoch
                ),
            )
        )
    return linhas_out


def _linha(unidade: str, metrica: str, valor, unid_med: str, nota: str) -> dict:
    return {
        "ano": ANO_EPOCH_APROX,
        "unidade": unidade,
        "camada": "edificacoes_open_buildings",
        "fonte_dado": "open_buildings_v3",
        "metrica": metrica,
        "periodo_inicio": None,
        "valor": valor,
        "unidade_medida": unid_med,
        "selo": "observado",
        "confiavel_para_tendencia": False,
        "fonte": FONTE_OB,
        "metodo": (
            "Google Open Buildings v3, edificações atribuídas ao ponto-sede mais "
            "próximo (mesma partição de Voronoi das demais métricas de forma "
            "urbana), confidence >= 0,65 (piso do próprio recorte, ver docstring)."
        ),
        "nota": nota.strip(),
    }


def main() -> list[dict]:
    estudo = c.carregar_estudo()
    epsg = c.epsg_metrico(estudo)
    return linhas(estudo, epsg)


if __name__ == "__main__":
    import json

    out = main()
    print(json.dumps(out[:6], indent=2, ensure_ascii=False))
    print(f"{len(out)} linhas geradas.", file=sys.stderr)
