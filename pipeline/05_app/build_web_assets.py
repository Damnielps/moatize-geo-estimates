#!/usr/bin/env python3
"""pipeline/05_app/build_web_assets.py — artefatos web em data/processed/app/ (Fase 4, §6).

Resolve os dois bloqueios registrados pelo orquestrador antes de qualquer front-end:

**Bloqueio 1 — volume.** `data/processed/imagery/*.geojson` (367 MB / 49 arquivos, até
37 MB por arquivo) não é a complexidade geométrica: são polígonos de pixel (30 m)
poligonizados 1:1, gravados com ~15 dígitos significativos de coordenada (nanômetros de
precisão sobre uma grade de 30 m). Fixar a precisão e simplificar dentro da tolerância
declarada resolve o volume sem tocar a geometria substantiva.

**Bloqueio 2 — projeção.** Os GeoJSON de origem estão em EPSG:32736 (UTM 36S) com um
membro `crs` que a maioria das bibliotecas (inclusive o MapLibre) ignora — o resultado é
um mapa vazio ou "no oceano". Este script reprojeta para EPSG:4326 e grava GeoJSON
RFC 7946 puro (sem membro `crs`; WGS84 é o default do formato).

## Decisões (com justificativa) — ver também data/processed/app/imagery/DECISOES.md

1. **Formato: GeoJSON simplificado, não PMTiles/tippecanoe.** A causa do inchaço não era
   complexidade vetorial (a maioria dos polígonos já vem dissolvida pela classificação
   upstream; ver nota de `union_all` testado manualmente) e sim precisão de coordenada e,
   secundariamente, vértices de "escada" de 30 m. Corrigir isso com as bibliotecas já
   travadas em `uv.lock` (`shapely`, `geopandas`, `pyproj`) resolve o problema sem
   introduzir um binário fora do gerenciador de dependências do projeto (`docs/ADR/0002`
   já baniu utilitários de linha de comando do GDAL pelo mesmo motivo de determinismo).
   Texto plano também mantém os artefatos auditáveis por `git diff`. Se uma camada futura
   voltar a crescer além do que GeoJSON simplificado aguenta, PMTiles é o próximo degrau
   documentado — não foi necessário aqui.
2. **Tolerância de simplificação: adaptativa por camada×ano, nunca > 1 % de erro de
   área.** Para cada arquivo, testa-se uma lista decrescente de tolerâncias (metros, em
   EPSG:32736) e escolhe-se a MAIOR tolerância cujo erro de área medido (|área
   simplificada − área original| / área original) fique ≤ ao teto declarado em
   `config/tolerances.yaml → app_geometria_simplificacao`. Nunca escolhe tolerância cujo
   erro exceda o teto; na pior hipótese cai para tolerância 0 (sem simplificação
   geométrica, só correção de precisão de coordenada) e o erro fica registrado como 0.
   O erro medido por arquivo entra em `manifest.json` — nenhum número é omitido.
3. **Precisão de coordenada de saída: 6 casas decimais (~0,11 m no equador).** Muito
   abaixo da resolução do pixel (30 m) e da tolerância de simplificação: não introduz erro
   adicional mensurável, apenas remove os dígitos que não carregam informação.
4. **`cultivo_sequeiro` não sai em pé de igualdade visual com as outras camadas**
   (`docs/ADR/0012`: acurácia do usuário 0,000 em 2020, único ano validado). O manifesto
   marca `confiabilidade: "candidata_nao_confirmada"` e carrega a acurácia/IC95 medidas
   para que o app renderize com estilo distinto (contorno, opacidade reduzida,
   OFF por padrão) e nunca como "cultivo confirmado".
5. **`urbano` carrega a comissão (ADR 0009) e a fração herdada da catraca R2 (ADR 0013)
   por ano**, lidas de `data/processed/acuracia_por_ano.csv` e
   `data/processed/causal/decomposicao_permanencia_urbano.csv` — nunca digitadas à mão.
   `industrial` e `reassentamento` carregam a fração herdada equivalente, lida de
   `data/processed/pegada_por_ano.csv` (ADR 0013 item 5: para `reassentamento` a fração
   chega a 68,6 % em 2020 — R2 pode esconder abandono, que é exatamente a pergunta 3 de
   §1).
6. **Cintilação do slider temporal (churn de pixel 31-54 %, ADR 0013 item 2): o app NÃO
   deve interpolar/morfar geometria entre anos-âncora.** Essa decisão de dado (não é
   código de UI, que fica para a Fase 4 seguinte) está registrada aqui porque condiciona
   o que este script publica: o manifesto carrega o churn por par de anos consecutivos
   (`data/processed/causal/estabilidade_temporal_camadas.csv`, rótulo bruto do RF,
   EXPERIMENTAL conforme o próprio CSV) para que a UI mostre o número ao lado de qualquer
   troca de ano, em vez de animar uma "mudança" que é ruído de classificação.

## O que este script NÃO faz
- Não regenera nem corrige `data/processed/imagery/*` (fonte, intocada).
- Não produz tiles raster (COG reamostrado) para os `*_30m_32736.tif` — fora do escopo
  dos dois bloqueios registrados (GeoJSON). Registrado como trabalho futuro em
  DECISOES.md.
- Não constrói o app (`app/`) — só os dados que ele vai consumir.
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

import geopandas as gpd
import numpy as np
import pandas as pd
import yaml
from shapely.geometry import box, mapping

REPO = Path(__file__).resolve().parents[2]
IMAGERY_DIR = REPO / "data" / "processed" / "imagery"
OUT_DIR = REPO / "data" / "processed" / "app" / "imagery"
RAW_DIR = REPO / "data" / "raw"
CONFIG_STUDY = REPO / "config" / "study.yaml"
CONFIG_TOL = REPO / "config" / "tolerances.yaml"

# Camadas de contexto (§6, tarefa "topônimos, rodovias e ferrovia em TODOS os mapas").
# Já coletadas em EPSG:4326, sem membro `crs` a remover, nível A (ODbL, data/LICENSES.md
# linha "OpenStreetMap (Geofabrik Moçambique)"). Este script só arredonda coordenada e
# minifica — mesmo tratamento das demais camadas — e NÃO reprojeta (a tarefa pede
# explicitamente para não reprojetar dado que já está em WGS84).
CAMADAS_CONTEXTO = {
    "osm_lugares": {
        "arquivo_raw": "osm_lugares_aoi.geojson",
        "descricao": "Topônimos (cidades, vilas, povoados) — OpenStreetMap",
    },
    "osm_vias": {
        "arquivo_raw": "osm_vias_aoi.geojson",
        "descricao": "Rede rodoviária (trunk/primary/secondary/tertiary) — OpenStreetMap",
    },
    "osm_ferrovia": {
        "arquivo_raw": "osm_ferrovia_aoi.geojson",
        "descricao": "Ferrovia (linha do Sena) — OpenStreetMap",
    },
    "osm_aerodromo": {
        "arquivo_raw": "osm_aerodromo_aoi.geojson",
        "descricao": (
            "Aeródromo de Tete / Chingodzi (IATA TET, ICAO FQTT) e pista — "
            "OpenStreetMap"
        ),
    },
}
CAMADAS_CONTEXTO_FONTE = "OpenStreetMap (Geofabrik Moçambique), data/LICENSES.md"
CAMADAS_CONTEXTO_LICENCA = "ODbL 1.0 — © OpenStreetMap contributors"

COORD_DECIMALS = 6  # ~0.11 m no equador; §ver docstring, decisão 3

# Decisão 7 (o que fica fora): `vegetacao` e `solo_exposto` são classes de cobertura
# intermediárias da classificação (§5.1) — nenhuma das funcionalidades pedidas em §6
# (cor-verdadeira, classificação em 3 camadas [urbano/reassentamento/industrial],
# produtos de referência WSF/GHSL, camada de agricultura urbana, Zambeze) as usa como
# camada de mapa. Juntas somam ~104 MB (28 % do total) e têm a MESMA instabilidade
# diagnosticada pelo item 3 do docs/ADR/0013 (razão de área entre anos-âncora de fator
# 32 e 41 — limiar de rótulo absoluto sobre paisagem não estacionária) sem nenhuma tela
# do app que dependa delas. Publicá-las seria pagar o custo de banda de uma camada
# instável e fora de escopo. Permanecem intocadas em data/processed/imagery/ para o
# artigo e para qualquer reprocessamento futuro (opção C do ADR 0013); só não entram no
# app. Registradas no manifesto como "excluida_do_app", não omitidas silenciosamente.
CAMADAS_EXCLUIDAS_DO_APP = {
    "vegetacao": (
        "classe intermediária de cobertura, fora das camadas de mapa pedidas em §6; "
        "instabilidade ADR 0013 item 3 (fator 32x entre anos)"
    ),
    "solo_exposto": (
        "classe intermediária de cobertura, fora das camadas de mapa pedidas em §6; "
        "instabilidade ADR 0013 item 3 (fator 41x entre anos)"
    ),
}

# Decisão 8: `cultivo_sequeiro` é dispersa (67 % dos polígonos são 1 pixel isolado;
# docs/ADR/0012, acurácia do usuário 0,000) e NÃO se beneficia de simplificação de
# vértice nem de dissolução de vizinhos (testado: união de todos os polígonos de
# cultivo_sequeiro_2025 preserva as 42 307 partes — não há adjacência a fundir). Grade
# de 1 km é o mesmo princípio de um "raster reamostrado" (opção citada na tarefa),
# aplicada só a esta camada: reduz ~42 mil feições para ~2 400 células, coerente com o
# status de "candidata" (generalização deliberada, não falsa precisão). `área_km2`
# publicada na célula é a SOMA exata da área original dos pixels dentro dela — não é
# aproximada pela área da célula.
GRADE_CULTIVO_SEQUEIRO_M = 1000.0


def carregar_config():
    study = yaml.safe_load(CONFIG_STUDY.read_text())
    tol = yaml.safe_load(CONFIG_TOL.read_text())
    crs_metrico = study["crs"]["metrico"]
    crs_exibicao = study["crs"]["exibicao"]
    app_tol = tol["app_geometria_simplificacao"]
    return crs_metrico, crs_exibicao, app_tol


def listar_arquivos():
    arquivos = sorted(IMAGERY_DIR.glob("*.geojson"))
    if not arquivos:
        raise SystemExit(f"nenhum GeoJSON em {IMAGERY_DIR}")
    return arquivos


_RE_CAMADA_DOIS_ANOS = re.compile(r"^(?P<camada>.+)_(?P<ano0>\d{4})_(?P<ano1>\d{4})$")


def nome_camada_ano(path: Path):
    """(camada, ano) a partir do nome do arquivo. `ano` é `None` (sem ano — ex.:
    `varzea`), `int` (um ano — ex.: `agua_2000`) ou `(ano0, ano1)` (camada de
    JANELA entre dois anos — ex.: `adensamento_2020_2025`, docs/ADR/0016).

    Defeito corrigido aqui (verificado, docs/ADR/0016 §Decisão-10):
    `nome_camada_ano("adensamento_2020_2025")` devolvia `('adensamento_2020', '2025')`
    porque o `rsplit` de um trailing `_<ano>` sozinho não distingue "um ano" de
    "dois anos concatenados" — o regex de dois anos é tentado primeiro."""
    stem = path.stem  # ex.: agua_2000, varzea, adensamento_2020_2025
    m = _RE_CAMADA_DOIS_ANOS.match(stem)
    if m:
        return m.group("camada"), (int(m.group("ano0")), int(m.group("ano1")))
    partes = stem.rsplit("_", 1)
    if len(partes) == 2 and partes[1].isdigit():
        return partes[0], int(partes[1])
    return stem, None


def sufixo_ano(ano) -> str:
    """`''`, `'_2000'` ou `'_2020_2025'`, conforme o tipo de `ano` devolvido por
    `nome_camada_ano` — um único ponto de formatação para não repetir o `isinstance`
    em cada lugar do script que monta nome de arquivo/chave de manifesto."""
    if ano is None:
        return ""
    if isinstance(ano, tuple):
        return f"_{ano[0]}_{ano[1]}"
    return f"_{ano}"


def arredondar_coords(geojson_geom: dict, casas: int) -> dict:
    """Arredonda recursivamente coordenadas de um __geo_interface__ (mapping) de shapely."""

    def rec(coords):
        if isinstance(coords[0], (float, int)):
            return [round(c, casas) for c in coords]
        return [rec(c) for c in coords]

    geojson_geom = dict(geojson_geom)
    geojson_geom["coordinates"] = rec(geojson_geom["coordinates"])
    return geojson_geom


def simplificar_com_tolerancia_adaptativa(
    gdf_metrico: gpd.GeoDataFrame, candidatos_m: list[float], erro_max_pct: float
):
    """Testa tolerâncias decrescentes (m, no CRS métrico) e escolhe a maior que respeita
    o teto de erro de área. Retorna (geometria_simplificada, tolerancia_escolhida_m,
    erro_area_pct_medido, area_original_km2, area_final_km2)."""
    area_original_km2 = gdf_metrico.geometry.area.sum() / 1e6
    if area_original_km2 == 0:
        # camada vazia neste ano: nada a simplificar, nada a errar
        return gdf_metrico.geometry, 0.0, 0.0, 0.0, 0.0

    for tol in sorted(candidatos_m, reverse=True):
        if tol == 0:
            geom_simpl = gdf_metrico.geometry
        else:
            geom_simpl = gdf_metrico.geometry.simplify(tol, preserve_topology=True)
        area_final_km2 = geom_simpl.area.sum() / 1e6
        erro_pct = abs(area_final_km2 - area_original_km2) / area_original_km2 * 100
        if erro_pct <= erro_max_pct:
            return geom_simpl, tol, erro_pct, area_original_km2, area_final_km2

    # nenhuma tolerância candidata respeitou o teto (não deveria acontecer com 0 na lista,
    # que tem erro 0 por definição) — guarda de segurança.
    return gdf_metrico.geometry, 0.0, 0.0, area_original_km2, area_original_km2


def agregar_em_grade(gdf_metrico: gpd.GeoDataFrame, cell_m: float, ano: int | None, camada: str):
    """Agrega feições dispersas numa grade regular alinhada à origem dos dados, somando
    area_km2 por célula. Preserva a área total exatamente (soma), sacrificando só a
    localização exata dentro da célula — decisão 8 acima."""
    area_total_antes_km2 = gdf_metrico["area_km2"].sum()
    if len(gdf_metrico) == 0:
        cols = ["ano", "camada", "area_km2", "fracao_cobertura_celula", "geometry"]
        vazio = gpd.GeoDataFrame(columns=cols, geometry="geometry", crs=gdf_metrico.crs)
        return vazio, area_total_antes_km2, area_total_antes_km2

    cent = gdf_metrico.geometry.centroid
    xmin, ymin = cent.x.min(), cent.y.min()
    bx = np.floor((cent.x - xmin) / cell_m).astype(int)
    by = np.floor((cent.y - ymin) / cell_m).astype(int)
    df = pd.DataFrame(
        {"bx": bx.values, "by": by.values, "area_km2": gdf_metrico["area_km2"].values}
    )
    agg = df.groupby(["bx", "by"], as_index=False)["area_km2"].sum()

    cell_area_km2 = (cell_m * cell_m) / 1e6
    geoms = [
        box(
            xmin + r.bx * cell_m,
            ymin + r.by * cell_m,
            xmin + (r.bx + 1) * cell_m,
            ymin + (r.by + 1) * cell_m,
        )
        for r in agg.itertuples()
    ]
    out = gpd.GeoDataFrame(
        {
            "ano": ano,
            "camada": camada,
            "area_km2": agg["area_km2"].round(6),
            "fracao_cobertura_celula": (agg["area_km2"] / cell_area_km2).round(4),
        },
        geometry=geoms,
        crs=gdf_metrico.crs,
    )
    area_total_depois_km2 = out["area_km2"].sum()
    return out, area_total_antes_km2, area_total_depois_km2


def escrever_geojson_minificado(gdf_4326: gpd.GeoDataFrame, path: Path):
    features = []
    for _, row in gdf_4326.iterrows():
        geom = arredondar_coords(mapping(row.geometry), COORD_DECIMALS)
        props = {k: row[k] for k in gdf_4326.columns if k != "geometry"}
        features.append({"type": "Feature", "properties": props, "geometry": geom})
    fc = {"type": "FeatureCollection", "features": features}
    path.write_text(json.dumps(fc, separators=(",", ":"), ensure_ascii=False))


def carregar_caveats(camada: str, ano, tabelas: dict):
    """Monta o bloco de proveniência de UMA camada×ano a partir de artefatos JÁ
    publicados em data/processed/ — nenhum número digitado à mão (§6, §10).

    `ano` pode ser `None`, `int` ou `(ano0, ano1)` (camada de janela — docs/ADR/0016)."""
    caveat = {}

    if camada == "adensamento":
        meta = tabelas.get("adensamento_meta")
        sens = tabelas.get("adensamento_sensibilidade")
        if meta is not None:
            # 1. Selo — a camada é síntese de três produtos sob cortes escolhidos,
            # nunca observação (§Decisão-8 do ADR).
            caveat["adr_0016_selo_modelado"] = {
                "selo": meta["selo"],
                "periodo": meta["periodo"],
                "quantis_declarados": meta["quantis_declarados"],
                "quantis_realizados": meta["quantis_realizados"],
                "nota": (
                    "Síntese de classificação própria + luz noturna de terceiros + "
                    "edificações de terceiros, sob cortes por quantil escolhidos a "
                    "priori — não é observação. NÃO somar `adensando` com "
                    "`expansao_nova` numa única figura (são respostas distintas)."
                ),
                "fonte": (
                    "data/processed/imagery/adensamento_2020_2025_240m_32736.tif.meta.json "
                    "(docs/ADR/0016)"
                ),
            }
            # 2. Áreas por classe, publicadas — nunca digitadas.
            caveat["adr_0016_areas_por_classe"] = {
                "areas_km2": meta["areas_por_classe_km2"],
                "area_dominio_km2": meta["area_dominio_km2"],
                "nota": (
                    "Domínio = aritmética de grade (n_pixels_30m == 64), não estimativa "
                    "— ver config/plausibilidade.yaml, camada adensamento."
                ),
                "fonte": "idem",
            }
            # 3. Sensibilidade — critério de publicação fixado ANTES de ver o resultado.
            caveat["adr_0016_sensibilidade"] = {
                "razao_maxima_1_decil": meta["razao_sensibilidade_maxima_1_decil"],
                "regime_publicacao": meta["regime_publicacao_sensibilidade"],
                "publicavel_como": meta.get("publicavel_como"),
                "nota": (
                    "Razão de área da classe `adensando` entre as variantes de ±1 decil "
                    "de TAU/Q_ALTO/Q_BAIXO e a base. Fora de [0,5; 2,0]: publica-se só "
                    "padrão espacial e ordem de grandeza, nunca a área pontual."
                ),
                "fonte": (
                    "data/processed/adensamento_sensibilidade.csv (docs/ADR/0016 §Decisão-9)"
                ),
            }
            # 4. R2 — S1 e S3 partilham o mesmo minuendo negativo (f_2020): os votos
            # não são independentes. Risco declarado, não uma medida numérica nova.
            caveat["adr_0016_risco_r2_correlacao_sinais"] = {
                "risco": meta["riscos"]["R2"],
                "nota": (
                    "S1 = ECDF_2025(f) - ECDF_2020(f) e S3 = ECDF_OB(fp) - ECDF_2020(f) "
                    "partilham ECDF_2020(f). Uma célula com f_2020 subestimado tende a "
                    "votar duas vezes. Medido pela variante `sem_S3` do CSV de "
                    "sensibilidade."
                ),
            }
            # 5. R3 — a camada não detecta esvaziamento (censura por baixo).
            caveat["adr_0016_risco_r3_sem_esvaziamento"] = {
                "risco": meta["riscos"]["R3"],
                "nota": (
                    "Não existe classe `desadensando`: o método é incapaz de povoá-la "
                    "(S1 só pode subir, catraca R2 de `urbano`). A ausência dela não "
                    "significa ausência do fenômeno no terreno."
                ),
            }
            # 6. R6 — janela real de S3 é 2020 -> ~2023, epoch único do Open Buildings.
            caveat["adr_0016_risco_r6_janela_s3"] = {
                "risco": meta["riscos"]["R6"],
                "nota": (
                    "Open Buildings v3 é epoch único (~2021-2023), sem série. A parcela "
                    "do voto de concordância que vem de S3 não cobre 2023-2025."
                ),
            }
        if sens is not None:
            caveat.setdefault("adr_0016_sensibilidade", {})["variantes"] = sens.to_dict(
                orient="records"
            )

    if camada == "urbano" and ano is not None:
        au = tabelas["acuracia_por_ano"]
        row = au[au["ano"] == ano]
        if not row.empty:
            r = row.iloc[0]
            caveat["adr_0009_comissao"] = {
                "acuracia_usuario_construido": float(r["acuracia_usuario_construido"]),
                "ic95": float(r["ic95_acuracia_usuario_construido"]),
                "comissao_estimada": round(1 - float(r["acuracia_usuario_construido"]), 4),
                "fonte": "data/processed/acuracia_por_ano.csv (docs/ADR/0009)",
            }
        dp = tabelas["decomposicao_permanencia"]
        rowd = dp[dp["ano"] == ano]
        if not rowd.empty:
            rd = rowd.iloc[0]
            caveat["adr_0013_catraca"] = {
                "fracao_estoque_herdada": float(rd["fracao_estoque_herdada"]),
                "area_publicada_km2": float(rd["area_urbano_publicado_km2"]),
                "estoque_sustentado_pelo_ano_km2": float(rd["estoque_sustentado_pelo_ano_km2"]),
                "nota": (
                    "Série não-decrescente por construção (regra R2 de permanência); "
                    "incapaz de mostrar contração. fracao_estoque_herdada é a parcela "
                    "do estoque publicado NÃO detectada pela classificação do próprio "
                    "ano — só herdada da união com anos anteriores."
                ),
                "fonte": (
                    "data/processed/causal/decomposicao_permanencia_urbano.csv "
                    "(docs/ADR/0013)"
                ),
            }

    if camada in ("industrial", "reassentamento") and ano is not None:
        pg = tabelas["pegada_por_ano"]
        rowp = pg[(pg["ano"] == ano) & (pg["camada"] == camada)]
        if not rowp.empty:
            rp = rowp.iloc[0]
            pub = float(rp["area_publicada_km2"])
            sem = float(rp["area_sem_permanencia_km2"])
            fracao = round((pub - sem) / pub, 4) if pub else 0.0
            caveat["adr_0013_catraca"] = {
                "area_sem_permanencia_km2": sem,
                "area_publicada_km2": pub,
                "fracao_herdada": fracao,
                "nota": (
                    "docs/ADR/0013 item 5 recomenda remover a permanência (R2) de "
                    "`industrial` e `reassentamento` (mina fecha e reabilita; povoado "
                    "pode ser abandonado, e R2 torna abandono indetectável por "
                    "construção). Decisão de reprocessar a série é do orquestrador "
                    "da Fase 3, não deste script — o número acima é só a exposição do "
                    "que já está publicado."
                ),
                "fonte": "data/processed/pegada_por_ano.csv (docs/ADR/0013)",
            }

    if camada.startswith("cultivo_"):
        ac = tabelas["acuracia_cultivo_por_ano"]
        row = ac[ac["ano"] == 2020]  # único ano validado (docs/ADR/0012)
        if not row.empty:
            r = row.iloc[0]
            if camada == "cultivo_sequeiro":
                caveat["adr_0012_confiabilidade"] = {
                    "confiabilidade": "candidata_nao_confirmada",
                    "acuracia_usuario_2020": float(r["acuracia_usuario_cultivo_sequeiro"]),
                    "ic95_2020": float(r["ic95_usuario_cultivo_sequeiro"]),
                    "nota": (
                        "Acurácia do usuário 0,000 (IC95 ±0,000; n=8/12, 2020, único "
                        "ano validado). NENHUM ponto confirmado como cultivo pelo "
                        "intérprete visual; Jaccard ~0 contra GLAD/WorldCover em TODOS "
                        "os anos. Rotular como 'vegetação de fenologia sazonal "
                        "acentuada, candidata a cultivo OU savana natural', nunca como "
                        "cultivo confirmado. Camada OFF por padrão no app."
                    ),
                    "fonte": "data/processed/acuracia_cultivo_por_ano.csv (docs/ADR/0012)",
                }
            else:
                caveat["adr_0012_confiabilidade"] = {
                    "confiabilidade": "defensavel_com_ressalva",
                    "acuracia_usuario_2020": float(r["acuracia_usuario_cultivo_irrigado"]),
                    "ic95_2020": float(r["ic95_usuario_cultivo_irrigado"]),
                    "nota": (
                        "Acurácia do usuário 0,556 (IC95 ±0,344; n=9/12, 2020, único "
                        "ano validado). Positivo e acima do acaso, mas IC95 amplo — "
                        "sustenta leitura qualitativa e ordem de grandeza, não número "
                        "pontual preciso."
                    ),
                    "fonte": "data/processed/acuracia_cultivo_por_ano.csv (docs/ADR/0012)",
                }

    return caveat


def carregar_churn_pares(tabelas: dict):
    """Churn/Jaccard por par de anos-âncora consecutivos, por classe — para o app avisar
    a cada troca de ano que a mudança de traçado inclui ruído de classificação
    (docs/ADR/0013 item 2), não deslocamento literal no terreno."""
    est = tabelas["estabilidade_temporal_camadas"]
    saida = {}
    for _, r in est.iterrows():
        chave = f"{r['par_anos']}__{r['classe']}"
        saida[chave] = {
            "par_anos": r["par_anos"],
            "classe": r["classe"],
            "jaccard": float(r["jaccard"]),
            "churn": float(r["churn"]),
            "razao_area_t1_sobre_t": float(r["razao_area_t1_sobre_t"]),
            "nota": (
                "Rótulo bruto do RF, antes de R1/R2 e das pegadas (ADR 0011). "
                "EXPERIMENTAL — não substitui nenhum artefato publicado. "
                "Ver docs/ADR/0013."
            ),
        }
    return saida


def processar_camadas_contexto(manifest: dict) -> None:
    """Copia topônimos/vias/ferrovia de data/raw/ para o app, só arredondando
    coordenada e minificando — sem reprojeção (já estão em EPSG:4326) e sem simplificação
    geométrica (poucas feições: 23/219/57, nenhum problema de volume)."""
    manifest.setdefault("camadas_contexto", {})
    for camada, cfg in CAMADAS_CONTEXTO.items():
        raw_path = RAW_DIR / cfg["arquivo_raw"]
        if not raw_path.exists():
            print(
                f"[app-data] AVISO: {raw_path} nao encontrado — camada de contexto pulada",
                file=sys.stderr,
            )
            continue
        dados = json.loads(raw_path.read_text(encoding="utf-8"))
        dados.pop("crs", None)
        features_out = []
        for feat in dados.get("features", []):
            geom = arredondar_coords(feat["geometry"], COORD_DECIMALS)
            features_out.append(
                {"type": "Feature", "properties": feat.get("properties", {}), "geometry": geom}
            )
        fc = {"type": "FeatureCollection", "features": features_out}
        out_name = f"{camada}.geojson"
        out_path = OUT_DIR / out_name
        out_path.write_text(json.dumps(fc, separators=(",", ":"), ensure_ascii=False))
        manifest["camadas_contexto"][camada] = {
            "camada": camada,
            "arquivo": f"imagery/{out_name}",
            "n_features": len(features_out),
            "descricao": cfg["descricao"],
            "fonte": CAMADAS_CONTEXTO_FONTE,
            "licenca": CAMADAS_CONTEXTO_LICENCA,
            "atribuicao_exigida": "© OpenStreetMap contributors",
            "fonte_bruta": f"data/raw/{cfg['arquivo_raw']}",
            "reprojetado": False,
            "simplificado": False,
        }
        print(
            f"[app-data] {out_name}: {len(features_out)} feicoes "
            "(camada de contexto, sem simplificacao)",
            file=sys.stderr,
        )


def main():
    crs_metrico, crs_exibicao, app_tol = carregar_config()
    candidatos_m = app_tol["candidatos_m"]
    erro_max_pct = app_tol["erro_area_max_pct"] * 100  # tolerances.yaml guarda fração

    OUT_DIR.mkdir(parents=True, exist_ok=True)

    processed = REPO / "data" / "processed"
    tabelas = {
        "acuracia_por_ano": pd.read_csv(processed / "acuracia_por_ano.csv"),
        "acuracia_cultivo_por_ano": pd.read_csv(processed / "acuracia_cultivo_por_ano.csv"),
        "decomposicao_permanencia": pd.read_csv(
            processed / "causal" / "decomposicao_permanencia_urbano.csv"
        ),
        "pegada_por_ano": pd.read_csv(processed / "pegada_por_ano.csv"),
        "estabilidade_temporal_camadas": pd.read_csv(
            processed / "causal" / "estabilidade_temporal_camadas.csv"
        ),
    }
    caminho_sens_adensamento = processed / "adensamento_sensibilidade.csv"
    if caminho_sens_adensamento.exists():
        tabelas["adensamento_sensibilidade"] = pd.read_csv(caminho_sens_adensamento)
    caminho_meta_adensamento = (
        processed / "imagery" / "adensamento_2020_2025_240m_32736.tif.meta.json"
    )
    if caminho_meta_adensamento.exists():
        tabelas["adensamento_meta"] = json.loads(
            caminho_meta_adensamento.read_text(encoding="utf-8")
        )

    manifest = {
        "gerado_por": "pipeline/05_app/build_web_assets.py",
        "crs_saida": "EPSG:4326 (RFC 7946, sem membro crs)",
        "crs_origem": crs_metrico,
        "precisao_coordenada_decimais": COORD_DECIMALS,
        "tolerancia_candidatos_m": candidatos_m,
        "erro_area_maximo_pct": erro_max_pct,
        "camadas": {},
    }

    for path in listar_arquivos():
        camada, ano = nome_camada_ano(path)

        if camada in CAMADAS_EXCLUIDAS_DO_APP:
            chave_manifest = f"{camada}{sufixo_ano(ano)}"
            manifest["camadas"][chave_manifest] = {
                "camada": camada,
                "ano": ano,
                "status": "excluida_do_app",
                "motivo": CAMADAS_EXCLUIDAS_DO_APP[camada],
                "fonte_intocada": f"data/processed/imagery/{path.name}",
            }
            print(
                f"[app-data] {path.name}: EXCLUÍDA do app "
                f"({CAMADAS_EXCLUIDAS_DO_APP[camada]})",
                file=sys.stderr,
            )
            continue

        gdf = gpd.read_file(path)
        if gdf.crs is None:
            gdf = gdf.set_crs(crs_metrico)
        else:
            gdf = gdf.to_crs(crs_metrico) if str(gdf.crs).upper() != crs_metrico.upper() else gdf

        n_antes = len(gdf)
        bytes_antes = path.stat().st_size

        if camada == "cultivo_sequeiro":
            gdf_out, area_orig_km2, area_final_km2 = agregar_em_grade(
                gdf, GRADE_CULTIVO_SEQUEIRO_M, ano, camada
            )
            tol_escolhida = None
            erro_pct = (
                abs(area_final_km2 - area_orig_km2) / area_orig_km2 * 100 if area_orig_km2 else 0.0
            )
            representacao = f"grade_regular_{int(GRADE_CULTIVO_SEQUEIRO_M)}m"
        else:
            geom_simpl, tol_escolhida, erro_pct, area_orig_km2, area_final_km2 = (
                simplificar_com_tolerancia_adaptativa(gdf, candidatos_m, erro_max_pct)
            )
            gdf_out = gdf.copy()
            gdf_out["geometry"] = geom_simpl
            gdf_out = gdf_out.set_geometry("geometry")
            gdf_out = gdf_out[~gdf_out.geometry.is_empty & gdf_out.geometry.notna()]
            representacao = "poligono_simplificado"

        if len(gdf_out):
            gdf_4326 = gdf_out.to_crs(crs_exibicao)
        else:
            gdf_4326 = gdf_out.set_crs(crs_exibicao, allow_override=True)

        if camada != "cultivo_sequeiro" and len(gdf_out):
            # recalcula area_km2 pós-simplificação (em métrico) para não publicar o valor
            # herdado do arquivo de origem, que pode ter sido calculado antes do corte
            area_series_km2 = gdf_out.to_crs(crs_metrico).geometry.area / 1e6
            gdf_4326 = gdf_4326.assign(area_km2=area_series_km2.round(6).values)

        out_name = f"{camada}{sufixo_ano(ano)}.geojson"
        out_path = OUT_DIR / out_name
        escrever_geojson_minificado(gdf_4326, out_path)
        bytes_depois = out_path.stat().st_size

        caveats = carregar_caveats(camada, ano, tabelas)

        chave_manifest = f"{camada}{sufixo_ano(ano)}"
        manifest["camadas"][chave_manifest] = {
            "camada": camada,
            "ano": ano,
            "arquivo": f"imagery/{out_name}",
            "representacao": representacao,
            "n_features_antes": n_antes,
            "n_features_depois": len(gdf_4326),
            "bytes_antes": bytes_antes,
            "bytes_depois": bytes_depois,
            "tolerancia_simplificacao_m": tol_escolhida,
            "area_km2_original": round(area_orig_km2, 6),
            "area_km2_final": round(area_final_km2, 6),
            "erro_area_pct": round(erro_pct, 6),
            "caveats": caveats,
        }
        print(
            f"[app-data] {out_name}: {bytes_antes/1e6:.2f} MB -> {bytes_depois/1e6:.2f} MB "
            f"(repr={representacao}, tol={tol_escolhida}, erro_area={erro_pct:.4f} %, "
            f"n={n_antes}->{len(gdf_4326)})",
            file=sys.stderr,
        )

    manifest["churn_pares_temporais"] = carregar_churn_pares(tabelas)
    processar_camadas_contexto(manifest)

    manifest_path = OUT_DIR / "manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2, ensure_ascii=False, sort_keys=True))

    publicadas = [v for v in manifest["camadas"].values() if v.get("status") != "excluida_do_app"]
    total_antes = sum(v["bytes_antes"] for v in publicadas)
    total_depois = sum(v["bytes_depois"] for v in publicadas)
    n_excluidas = len(manifest["camadas"]) - len(publicadas)
    print(
        f"[app-data] TOTAL (camadas publicadas): {total_antes/1e6:.1f} MB -> "
        f"{total_depois/1e6:.1f} MB ({len(publicadas)} arquivos publicados; "
        f"{n_excluidas} excluídas)",
        file=sys.stderr,
    )


if __name__ == "__main__":
    main()
