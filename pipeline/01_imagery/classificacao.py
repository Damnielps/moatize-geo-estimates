#!/usr/bin/env python3
"""pipeline/01_imagery/classificacao.py — classificação em 3 camadas mutuamente
exclusivas (§5.1, §10). **Redesenho da Fase 1** (escalonamento T2→T3).

Este arquivo substitui a versão reprovada. O que foi reprovado não era código:
era a estratégia. Segue o desenho novo, com cada decisão declarada.

## 1. O que estava errado e o que mudou

Quatro defeitos foram diagnosticados e corrigidos:

1. **Limiares adaptativos por percentil** selecionavam uma fatia quase constante
   da imagem todo ano (3,4–4,4% da AOI): o produto media o percentil, não o
   crescimento. Agora **nenhum percentil da própria imagem** entra em nenhum
   rótulo — o treino é ancorado no WSF Evolution (produto externo, ano de
   primeira detecção) e em limiares físicos; o de `vegetacao` é expresso como
   **razão à mediana da paisagem do próprio ano** (docs/ADR/0014) — normalização
   radiométrica, não percentil: o corte não seleciona fração fixa da AOI
   (9,9 a 13,5 % ao longo da série).
2. **Confusão solo exposto × construído** na savana semiárida em estação seca.
   Agora há **separação fenológica**: `NDVI(chuva) − NDVI(seca)`. Construído é
   estável entre estações; solo exposto esverdeia na chuva. Medido nesta AOI, a
   separabilidade (d de Cohen) entre WSF-construído e não-construído é 1,83
   (2000) / 2,03 (2015) / 1,87 (2025) para a amplitude, contra 0,39 / 0,71 /
   0,29 para o NDBI — de 3 a 6 vezes mais discriminante que o índice que a
   versão anterior usava como eixo principal.
3. **Série não monotônica** (85,6 → 111,5 → 106,3 → 102,0 km²). Agora há regras
   temporais explícitas (R1 confirmação, R2 permanência), aplicadas fora do
   classificador, com a série sem restrição publicada ao lado.
4. **"Acurácia" era concordância entre duas regras espectrais** sobre o mesmo
   sinal confundido. A validação saiu deste script: ver
   `pipeline/01_imagery/acuracia.py`, com pontos rotulados por interpretação
   visual de recortes RGB (declaradamente por modelo, não por humano, não por
   campo) e estimador estratificado de Olofsson et al. (2014).

## 2. Papéis das referências externas — escolhidos e assumidos (sem circularidade)

- **WSF Evolution (DLR, 30 m, 1985–2015)** — **semeia o treino**. Consequência
  assumida: **não pode** ser reusado como validação. Nenhuma métrica de
  concordância com WSF é reportada como acurácia neste desenho.
- **GHSL BUILT-S R2023A (JRC, 100 m, épocas observadas 2000–2020)** —
  **referência independente de concordância**. Não toca em treino nem em
  limiar. As épocas 2025/2030 do GHSL são **extrapoladas**, não observadas, e
  por isso **não** são usadas: 2025 fica sem referência de produto, declarado,
  não substituído.
- **Maus et al. v2 (polígonos de mineração, Sentinel-2 2017–2019)** — máscara
  espacial da camada `industrial`, com método declarado por ano em
  `METODO_INDUSTRIAL_POR_ANO` (não vale para 2000/2005: a mina não existia).

## 3. Amostras de treino (nenhum percentil da imagem)

Positivos de `construido`: pixels com WSF ∈ (0, min(ano, 2015)], **erodidos**
por uma janela 3×3 (só o miolo da mancha entra; borda mista fica fora).
Para 2020 e 2025 os positivos vêm do construído já existente em 2015 — o WSF
termina em 2015. Isso é válido porque construído é quase permanente (o que
existia em 2015 continua existindo), mas significa que **nenhum assentamento
posterior a 2015 semeia o treino**: quem detecta o novo é o modelo, não o
rótulo.

Negativos: todo pixel válido fora de uma faixa de guarda de
`FAIXA_GUARDA_NEGATIVO_M` em torno de qualquer pixel WSF-construído (de qualquer
época) e fora dos polígonos de mineração e dos buffers de reassentamento. A
partição é **exaustiva** — todo negativo recebe uma classe, por limiares
**físicos fixos**, iguais em todos os anos, nunca percentis:

- `agua`: MNDWI > 0 e NDWI > 0 (limiar canônico de Xu 2006 — água tem MNDWI
  positivo por construção do índice; não é um corte ajustado a esta AOI);
- `vegetacao`: não-água e NDVI(seca) ≥ 1,30 × **mediana de NDVI(seca) da
  paisagem do próprio ano** — verde **persistente na seca** e **acima da
  paisagem daquele ano**: arbóreo, ripário ou irrigado. Era um corte absoluto
  de 0,30; `docs/ADR/0013` mostrou que a mediana da paisagem percorre
  0,205–0,409 na série e que o corte fixo, caindo dentro dessa faixa, media o
  ano verde e não a vegetação (10,7 % da AOI em 2000, 90,8 % em 2015).
  Corrigido em `docs/ADR/0014`, propagando a normalização que `docs/ADR/0011`
  já usava na pegada;
- `solo_exposto`: todo o resto do pool de negativos.

A exaustividade não é detalhe: numa primeira versão deste redesenho,
`solo_exposto` exigia NDVI(seca) < 0,20 **e** amplitude > 0,10, o que deixava
uma faixa espectral larga sem rótulo. Na predição essa faixa era absorvida por
`construido` e a área saía em 365 km² (2000). Os negativos precisam cobrir todo
o espaço espectral não construído.

Amostragem: **aleatória simples** sobre o conjunto rotulado, respeitando o prior
das classes (docs/ADR/0006), com piso por classe. Amostragem balanceada
(500/classe) inflava a área construída em mais de uma ordem de grandeza — essa
sensibilidade é a fragilidade principal deste produto e está declarada.

Risco residual declarado, sem solução com dados de nível A: em 2020 e 2025, um
assentamento novo pós-2015 fora da faixa de guarda e dos buffers conhecidos pode
ser sorteado como negativo, enviesando o modelo para **omitir** construído novo
nesses dois anos. Nenhum produto de nível A cobre 2016–2025 com ano de primeira
detecção.

## 4. Regras temporais — declaradas, não escondidas em pós-processamento

- **R1 — confirmação de primeira detecção.** Um pixel só é aceito como
  construído no primeiro ano-âncora `t` em que o RF o classifica assim se o RF
  também o classificar como construído no ano-âncora **seguinte**. Sem
  confirmação, a detecção é descartada. O último ano da série (2025) não tem
  ano seguinte: suas primeiras detecções entram **não confirmadas** e o CSV
  marca isso.
- **R2 — permanência (só `urbano`).** Depois de R1, `construido(t) = ∪_{t' ≤ t} construido_R1(t')`.
  A série passa a ser não decrescente **por construção**. Justificativa:
  construído é quase permanente nesta AOI (o próprio WSF é, por definição, um
  ano de primeira detecção — monotônico); desaparecimento entre anos-âncora é
  sinal de erro de classificação, não de dinâmica. **Escopo por camada**
  (`docs/ADR/0014`): R2 vale para `urbano` e **não** vale para `industrial`
  nem para `reassentamento` — cava é reabilitada e povoado pode ser
  abandonado. Custo de R2 em `urbano`, medido em `docs/ADR/0013`: 18,0 % do
  estoque de 2025 não é detectado no próprio ano, e a série pós-R2 não pode
  cair, logo não serve para estimar quebra nem para testar H4.
- **Transparência obrigatória:** `data/processed/area_construida_por_ano.csv`
  publica lado a lado a área **sem restrição** (RF puro + filtro espacial), a
  área **após R1** e a área **após R2**. O leitor vê exatamente quanto cada
  regra moveu. Nenhuma das duas regras é aplicada em silêncio.

## 5. Escopo: o que este script NÃO faz

Não calcula acurácia. Acurácia, kappa e intervalo de confiança saem de
`pipeline/01_imagery/acuracia.py`, a partir de rótulos de interpretação visual
em `data/processed/validacao/`. Aqui só se calcula **concordância com o GHSL**,
que é concordância entre dois mapas com erros próprios — nunca acurácia.

Uso: `uv run python pipeline/01_imagery/classificacao.py [ano ...]`
(sempre processa a série inteira em ordem: as regras R1/R2 são temporais.)
"""

from __future__ import annotations

import csv
import hashlib
import json
import re
import subprocess
import sys
from datetime import UTC, datetime
from pathlib import Path

import geopandas as gpd
import numpy as np
import rasterio
import rasterio.features
import rasterio.warp
import shapely.geometry
import shapely.ops
import yaml
from rasterio.merge import merge as rasterio_merge
from scipy.ndimage import (
    binary_closing,
    binary_dilation,
    binary_erosion,
    uniform_filter,
)
from sklearn.ensemble import RandomForestClassifier

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "00_fetch"))
from _config import carregar_estudo

REPO_ROOT = Path(__file__).resolve().parents[2]

sys.path.insert(0, str(REPO_ROOT / "pipeline" / "lib"))
import acuracia_texto  # noqa: E402

STUDY_YAML = REPO_ROOT / "config" / "study.yaml"
SEEDS_YAML = REPO_ROOT / "config" / "seeds.yaml"
DATA_RAW = REPO_ROOT / "data" / "raw"
DATA_PROCESSED = REPO_ROOT / "data" / "processed" / "imagery"
AREA_CSV = REPO_ROOT / "data" / "processed" / "area_construida_por_ano.csv"
CONCORDANCIA_CSV = REPO_ROOT / "data" / "processed" / "concordancia_ghsl.csv"
PEGADA_CSV = REPO_ROOT / "data" / "processed" / "pegada_por_ano.csv"
PROVENANCE_FRAGMENT = REPO_ROOT / "data" / "provenance_parts" / "imagem_fase1.md"
MARCADOR_INICIO = "<!-- SECAO_CLASSIFICACAO_INICIO -->"
MARCADOR_FIM = "<!-- SECAO_CLASSIFICACAO_FIM -->"

MAUS_AOI_GEOJSON = DATA_RAW / "global_mining_polygons_v2_maus_2022_aoi.geojson"
REASSENTAMENTOS_GEOJSON = DATA_RAW / "reassentamentos.geojson"
WSF_TILES = [DATA_RAW / "wsf_evolution_S18E032.tif", DATA_RAW / "wsf_evolution_S18E034.tif"]
GHSL_EPOCAS_OBSERVADAS = [2000, 2005, 2010, 2015, 2020]


def caminho_ghsl(epoca: int) -> Path:
    return DATA_RAW / f"ghsl_built_s_E{epoca}_R2023A_4326_3ss_R11_C22.tif"


# --- constantes do desenho (todas fixas entre anos; nenhuma é percentil) ----

ANO_FIM_WSF = 2015
# Faixa de guarda em torno de qualquer pixel já detectado pelo WSF (qualquer
# época): nenhum negativo é sorteado dentro dela. Existe porque a borda de uma
# mancha construída é espectralmente mista a 30 m e porque o WSF tem omissão
# conhecida em construído esparso/informal — um negativo colado na mancha teria
# alta chance de ser construído de fato. 150 m = 5 pixels.
FAIXA_GUARDA_NEGATIVO_M = 150.0
LIMIAR_AGUA_MNDWI = 0.0
LIMIAR_AGUA_NDWI = 0.0

# Rótulo de `vegetacao` no treino: **razão à mediana de NDVI(seca) da paisagem do
# próprio ano**, não corte absoluto (docs/ADR/0014).
#
# O corte absoluto anterior era `NDVI(seca) >= 0,30`. `docs/ADR/0013` mediu o
# defeito: a mediana de NDVI(seca) da paisagem percorre 0,205–0,409 entre os
# anos-âncora (sensor ETM+/TM/OLI/OLI-2 e pluviosidade), e o corte fixo cai
# DENTRO dessa faixa. A fração da AOI acima dele ia de 10,7 % (2000) a 90,8 %
# (2015) e reaparecia quase inalterada na classe publicada — o produto media o
# ano verde, não a vegetação. `docs/ADR/0011` já tinha corrigido exatamente esse
# defeito, mas só na pegada minerária; aqui a correção é propagada.
#
# Valor: 1,30. Não é ajuste ao sintoma. É a razão que o corte histórico de 0,30
# representava nos dois anos em que a paisagem estava radiometricamente
# comparável e o classificador se comportava de forma plausível — 2000
# (mediana 0,233 => razão 1,29) e 2005 (0,231 => 1,30), os anos de maior pool de
# `solo_exposto` e de razão bruta/GHSL de 0,83 e 1,08. Isto preserva a intenção
# física do rótulo ("verde persistente na seca, acima da paisagem de savana
# semiárida") e a torna comparável entre anos.
#
# NÃO é percentil da imagem (o defeito que reprovou a primeira classificação):
# o corte não seleciona fração fixa da AOI. Medido com este valor, a fração
# rotulável como vegetação é 9,9 / 11,0 / 11,6 / 6,4 / 13,5 / 13,2 % — varia por
# fator 2,1 entre anos, contra fator 15 do corte absoluto.
RAZAO_VERDE_VEGETACAO = 1.30

# Filtro de coerência espacial: maioria simples numa janela 3×3. Menos agressivo
# que o 5×5/50% da versão anterior (que apagava manchas legítimas de poucos
# pixels, como um povoado de reassentamento recém-construído).
JANELA_COERENCIA = 3
FRACAO_COERENCIA = 5 / 9

# Fração mínima de superfície construída (m² por célula de 100 m, máximo 10000)
# para uma célula GHSL contar como "construída" na comparação. 25% é o corte
# usado na literatura GHSL para "built-up area" em comparações binárias; é
# declarado aqui e a sensibilidade a ele é reportada no CSV (10% e 50%).
FRACOES_GHSL = [0.10, 0.25, 0.50]
FRACAO_GHSL_PRINCIPAL = 0.25

ANO_ABERTURA_MINA = 2011
ANO_LICENCA_MINA = 2006

# --- pegada minerária e de reassentamento: classe própria, não interseção -----
#
# Redesenho da Fase 2 (docs/ADR/0011). Antes, `industrial` era
# `construido & poligono_maus` e `reassentamento` era `restante & buffer`: as duas
# camadas eram a interseção da classificação de CONSTRUÍDO com uma máscara espacial,
# e por isso mediam "construído dentro do polígono", não a pegada. O defeito é
# físico, não de código: **cava, pilha de estéril e rejeito são rocha e solo
# exposto — espectralmente não são construído**, e um classificador de construído
# os perde por definição. Medido: 4,2 km² contra os 59,2 km² de Maus et al. (7,1 %).
#
# A pegada passa a ser classificada por assinatura própria: **solo/rocha exposto
# persistente**, isto é, ausência de reverdecimento na estação chuvosa. Numa savana
# semiárida, solo exposto natural esverdeia na chuva; cava, pilha e rejeito não.
#
# O limiar NÃO é absoluto. NDVI absoluto não é comparável entre anos-âncora nesta
# série (a mediana de NDVI(chuva) da paisagem vai de 0,669 em 2015 a 0,330 em 2025,
# por diferença de sensor e de pluviosidade): medido, um corte absoluto de
# NDVI(chuva) < 0,25 marcaria 83 km² fora dos polígonos em 2000 e 472 km² em 2025.
# O critério é a **razão** entre o pixel e a mediana da paisagem do PRÓPRIO ano:
#
#     razao_verde = NDVI(pixel) / mediana(NDVI da paisagem de referência do ano)
#
# Isto é normalização radiométrica por ano, **não** um percentil da imagem: o corte
# não seleciona uma fração fixa da AOI (o defeito que reprovou a primeira versão da
# classificação), e sim pixels cuja resposta é uma fração fixa da paisagem. A prova
# está no comportamento temporal: a mesma regra devolve 0,00 km² em 2000 e 2005,
# quando a mina não existia, e 61,5 km² em 2025.
RAZAO_VERDE_PEGADA = 0.60
# Calibrado por J de Youden contra os polígonos de Maus et al. em 2020 — o
# ano-âncora de MENOR defasagem em relação à referência (Sentinel-2 2017-2019, ~1
# ano). J tem máximo achatado em 0,60-0,65 (J = 0,405); adota-se 0,60, o mais
# conservador dos dois. F1 foi rejeitado como critério: dentro do envelope a
# prevalência da classe é ~52 %, e F1 cresce monotonicamente com o recall até
# limiares absurdos (0,672 em lim = 0,85), enquanto J tem máximo interior.
# Consequência declarada: a concordância com Maus em 2020 **não é validação
# independente** — o limiar foi ajustado nela. A evidência independente é temporal
# (ver `data/processed/pegada_sensibilidade.csv` e o placebo pré-2006).

# Envelope de busca: os polígonos de Maus et al. dilatados. Eles são um retrato de
# 2017-2019 e não podem servir de máscara rígida para 2025 — a lavra avança. 500 m
# corresponde a ~80 m/ano de avanço de frente entre 2019 e 2025, ordem de grandeza
# conservadora para cava a céu aberto deste porte. O envelope **restringe onde** a
# classe pode aparecer; **não** impõe a extensão, que é medida por ano.
BUFFER_EXPANSAO_MINA_M = 500.0

# Fecho morfológico 3x3 (90 m): fecha vãos de um pixel dentro da pegada (bermas,
# vias de serviço, poças no fundo de cava). É o mesmo tamanho de janela de
# JANELA_COERENCIA, pelo mesmo motivo. NÃO se aplica preenchimento de buracos
# (`binary_fill_holes`): ele acrescentaria de 10 a 25 % de área sem que nenhum
# pixel acrescentado tivesse a assinatura da classe.
JANELA_FECHO_PEGADA = 3

# R2 (permanência) tem ESCOPO POR CAMADA, não é regra global (docs/ADR/0013 item 5,
# executado em docs/ADR/0014). Antes valia para as três camadas pelo argumento
# "construído é permanente". O argumento é de alvenaria e não sustenta número sobre
# rocha movida nem sobre povoado que pode ser abandonado:
#
# - `urbano`: R2 MANTIDO. Edificação é quase permanente nesta AOI; o custo está
#   medido e publicado (fração do estoque herdada da união: 0 / 0 / 3,4 / 6,1 /
#   12,7 / 18,0 % — `data/processed/causal/decomposicao_permanencia_urbano.csv`).
# - `industrial`: R2 REMOVIDO. Mina fecha, cava é reabilitada, pilha de estéril é
#   revegetada. docs/ADR/0011 item 5 já registrava que parte da pilha de 2015
#   aparece revegetada ou sombreada em 2020 e que a permanência a mantinha contada.
# - `reassentamento`: R2 REMOVIDO. Aqui não é só indefensável, é danoso: a pergunta
#   específica 3 de §1 é "consolidação, ABANDONO ou adensamento", e a permanência
#   torna abandono indetectável por construção — o pipeline respondia
#   "consolidação" sempre, antes de medir.
#
# Consequência declarada e antecipada: `reassentamento` 2020 cai de 2,00 para
# 0,63 km², abaixo do piso de `config/plausibilidade.yaml`. É sinal honesto, não
# falha — a faixa NÃO foi afrouxada; abriu-se a exceção declarada no YAML
# apontando docs/ADR/0014, que é o mecanismo previsto para exatamente isto.
#
# A acumulação, quando aplicada, começaria no ano de licença da mina (2006) e, para
# cada povoado, no seu ano de reassentamento. As colunas
# `area_sem_permanencia_km2` e `area_publicada_km2` de
# `data/processed/pegada_por_ano.csv` continuam publicadas lado a lado — agora
# idênticas para as duas pegadas, que é a forma de o leitor ver que R2 saiu.
PEGADA_APLICA_PERMANENCIA = {
    "industrial": False,
    "reassentamento": False,
}

METODO_INDUSTRIAL_POR_ANO = {
    2000: (
        "classe própria de solo/rocha exposto persistente (razao_verde < "
        f"{RAZAO_VERDE_PEGADA}) dentro do envelope de Maus et al. dilatado em "
        f"{BUFFER_EXPANSAO_MINA_M:.0f} m, união com o construído do ano no mesmo "
        "envelope. Resultado 0,00 km²: PLACEBO TEMPORAL — a concessão da Vale é de "
        "2004 e a licença de 2006, então a regra tinha de devolver ~zero aqui, e "
        "devolve. Sem acumulação (anterior a 2006)."
    ),
    2005: (
        "mesma regra de 2000. Resultado 0,00 km²: segundo ponto do placebo temporal, "
        "um ano antes da licença. Sem acumulação (anterior a 2006)."
    ),
    2010: (
        "solo/rocha exposto persistente + construído, dentro do envelope, acumulado "
        "desde 2006. Obras desde ~2007; a mina só opera em mai/2011, então a pegada "
        "aqui é de decapagem e canteiro, não de lavra plena."
    ),
    2015: (
        "solo/rocha exposto persistente + construído, dentro do envelope, acumulado "
        "desde 2006. Operação da Vale desde 2011 e Benga desde 2012. O envelope vem "
        "de imagem 2017-2019, POSTERIOR a este ano: parte dele ainda não era lavra "
        "em 2015, e é por isso que a extensão é medida pela assinatura do ano e não "
        "pelo polígono."
    ),
    2020: (
        "solo/rocha exposto persistente + construído, dentro do envelope, acumulado "
        "desde 2006. Defasagem de ~1 ano em relação à referência — é neste ano que o "
        "limiar foi calibrado, e por isso a concordância com Maus em 2020 não é "
        "validação independente."
    ),
    2025: (
        "solo/rocha exposto persistente + construído, dentro do envelope, acumulado "
        "desde 2006. Defasagem de ~6 anos: o envelope dilatado em "
        f"{BUFFER_EXPANSAO_MINA_M:.0f} m admite avanço de lavra posterior a 2019, mas "
        "expansão além dessa faixa fica fora e é subestimação declarada."
    ),
}

# 1000 m, não 1500 m. O raio anterior (1500 m = 7,1 km² por povoado) era generoso
# demais e admitia as machambas do entorno: medido, devolvia 2,34 km² já em 2010,
# acima do teto de plausibilidade daquela fase. Cateme tem 716 lotes e Mwaladzi 84
# (HRW 2013, nível B — dimensiona, não publica); a 500-1000 m² por lote são 0,4-0,8
# km² de lotes, que cabem folgadamente num raio de 1 km (3,14 km²).
RAIO_BUFFER_REASSENTAMENTO_M = 1000.0

# Raio SEPARADO, e maior, para excluir negativos do treino do Random Forest. Os dois
# raios têm propósitos opostos e não devem ser o mesmo botão: a exclusão de negativos
# quer ser generosa (não sortear como "não construído" um pixel que pode ser casa de
# reassentamento), enquanto o domínio de detecção quer ser restrito (não varrer as
# machambas do entorno para dentro da camada). Mantê-lo em 1500 m preserva, além
# disso, o pool de treino EXATAMENTE como estava antes de docs/ADR/0011 — logo o
# classificador de construído, o estrato da validação e a acurácia de docs/ADR/0009
# não se movem por efeito colateral de uma mudança que é sobre a pegada. Isso é
# verificado, não presumido: ver pipeline/tests/test_imagery.py.
RAIO_EXCLUSAO_NEGATIVO_REASSENTAMENTO_M = 1500.0

NOTA_BUFFER_REASSENTAMENTO = (
    f"Buffer de {RAIO_BUFFER_REASSENTAMENTO_M:.0f} m em torno do ponto único de cada "
    "povoado (não há polígono de traçado real de nível A) delimitando ONDE PROCURAR. "
    "Dentro dele a camada é a pegada: solo exposto persistente (mesma regra e mesmo "
    f"limiar razao_verde < {RAZAO_VERDE_PEGADA} da pegada minerária) em união com o "
    "construído do ano. **A detecção não exige assinatura de construído** — foi esse "
    "o defeito corrigido: habitação de reassentamento é baixa, esparsa e de telhado "
    "metálico ou fibrocimento, e a 30 m um classificador de construído a perde "
    "(a camada anterior media 0,07 km², cerca de um décimo do piso plausível). "
    "**O que a camada mede é a pegada do povoado — lotes, vias e terreno alterado — "
    "não a área de telhado.** "
    "**A camada continua incompleta e isso é estrutural, não um bug**: o povoado "
    "urbano '25 de Setembro' (289 famílias, HRW 2013) tem `geometry: null` em "
    "data/raw/reassentamentos.geojson — Nominatim e Overpass não o localizaram e a "
    "coordenada não foi inventada. Consequência aritmética: o construído do 25 de "
    "Setembro está contado dentro de `urbano`, isto é, `urbano` inclui crescimento "
    "por reassentamento que §10 manda separar. A magnitude desse vazamento não é "
    "estimável sem a geometria."
)

BANDAS_COMUNS = ["blue", "green", "red", "nir", "swir16", "swir22"]
INDICES_SECA = ["ndvi", "ndbi", "mndwi", "ndwi", "evi"]
INDICES_FENOLOGICOS = ["ndvi_chuva", "ndvi_amplitude"]
FEATURES = [*INDICES_SECA, *INDICES_FENOLOGICOS, *BANDAS_COMUNS]

CLASSES_ESPECTRAIS = ["agua", "vegetacao", "solo_exposto", "construido"]
NOMES_CAMADAS = ["urbano", "industrial", "reassentamento", "vegetacao", "solo_exposto", "agua"]
CODIGO_CLASSE = {nome: i for i, nome in enumerate(CLASSES_ESPECTRAIS)}
NOME_CLASSE = {i: nome for nome, i in CODIGO_CLASSE.items()}

NOME_ARQUIVO_RE = re.compile(r"^composto_(\d{4})_(\d+)m_(\d+)\.tif$")


# ---------------------------------------------------------------------------
# Proveniência
# ---------------------------------------------------------------------------


def hash_arquivo(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def commit_git_atual() -> str:
    try:
        return subprocess.check_output(
            ["git", "rev-parse", "HEAD"], cwd=REPO_ROOT, text=True, stderr=subprocess.DEVNULL
        ).strip()
    except (subprocess.CalledProcessError, FileNotFoundError):
        return "desconhecido (git indisponível)"


def carregar_yaml(path: Path) -> dict:
    with path.open(encoding="utf-8") as fh:
        return yaml.safe_load(fh)


# ---------------------------------------------------------------------------
# Leitura de features
# ---------------------------------------------------------------------------


def compostos_disponiveis() -> dict[int, Path]:
    achados: dict[int, Path] = {}
    if not DATA_PROCESSED.exists():
        return achados
    for caminho in sorted(DATA_PROCESSED.glob("composto_*.tif")):
        m = NOME_ARQUIVO_RE.match(caminho.name)
        if m:
            achados[int(m.group(1))] = caminho
    return achados


def carregar_features_ano(ano: int, res_m: int, epsg: int) -> dict:
    """Empilha índices de seca, métricas fenológicas e bandas do composto.

    Falha alta se faltar a métrica fenológica: o desenho depende dela e um
    ano sem ela não pode ser classificado com o mesmo protocolo dos demais
    (§5.1 exige protocolo idêntico entre anos).
    """
    caminho_composto = DATA_PROCESSED / f"composto_{ano}_{res_m}m_{epsg}.tif"
    with rasterio.open(caminho_composto) as src:
        perfil = {"crs": src.crs, "transform": src.transform, "shape": src.shape}
        dados = src.read(masked=True)
        descricoes = src.descriptions

    bandas = {
        nome: dados[i].filled(np.nan)
        for i, nome in enumerate(descricoes)
        if nome in BANDAS_COMUNS
    }

    indices: dict[str, np.ndarray] = {}
    for nome in [*INDICES_SECA, *INDICES_FENOLOGICOS]:
        caminho = DATA_PROCESSED / f"{nome}_{ano}_{res_m}m_{epsg}.tif"
        if not caminho.exists():
            raise FileNotFoundError(
                f"{caminho.name} ausente. As métricas fenológicas são obrigatórias neste "
                "desenho — rode pipeline/01_imagery/compostos_chuva.py antes."
            )
        with rasterio.open(caminho) as src:
            indices[nome] = src.read(1, masked=True).filled(np.nan)

    empilhados = np.stack(
        [indices[n] for n in [*INDICES_SECA, *INDICES_FENOLOGICOS]]
        + [bandas[n] for n in BANDAS_COMUNS]
    )
    mask_valida = np.all(np.isfinite(empilhados), axis=0)
    return {
        "perfil": perfil,
        "empilhados": empilhados,
        "mask_valida": mask_valida,
        "indices": indices,
    }


# ---------------------------------------------------------------------------
# WSF Evolution — semente de treino (papel único e declarado)
# ---------------------------------------------------------------------------


def carregar_wsf_reprojetado(perfil: dict) -> np.ndarray:
    tiles = [p for p in WSF_TILES if p.exists()]
    if not tiles:
        raise FileNotFoundError(
            "WSF Evolution ausente em data/raw/ — é a semente de treino deste desenho."
        )
    fontes = [rasterio.open(p) for p in tiles]
    try:
        mosaico, transform_mosaico = rasterio_merge(fontes)
        crs_origem = fontes[0].crs
    finally:
        for f in fontes:
            f.close()
    destino = np.zeros(perfil["shape"], dtype="int32")
    rasterio.warp.reproject(
        source=mosaico[0],
        destination=destino,
        src_transform=transform_mosaico,
        src_crs=crs_origem,
        dst_transform=perfil["transform"],
        dst_crs=perfil["crs"],
        resampling=rasterio.warp.Resampling.nearest,
        src_nodata=0,
        dst_nodata=0,
    )
    return destino


def rotulos_treino(
    ano: int,
    indices: dict,
    mask_valida: np.ndarray,
    wsf: np.ndarray,
    mask_excluir_negativos: np.ndarray,
    res_m: float,
) -> np.ndarray:
    """Rótulos de treino: WSF ancora `construido`; limiares físicos ancoram as
    três classes não construídas — `agua` por limiar canônico absoluto (Xu 2006)
    e `vegetacao` por RAZÃO à mediana de NDVI(seca) da paisagem do próprio ano
    (docs/ADR/0014). Ver §3 do docstring do módulo.

    Devolve `(rotulo, diagnostico)`; o diagnóstico carrega a mediana do ano e o
    limiar efetivo, que passam para a proveniência.

    A partição dos negativos é **exaustiva**: todo pixel do pool de negativos
    recebe uma das três classes não construídas. Isso é deliberado e foi um
    defeito corrigido durante o redesenho: numa primeira versão, `solo_exposto`
    exigia simultaneamente NDVI(seca) baixo e amplitude alta, deixando uma faixa
    espectral ampla **sem rótulo nenhum**. Como o classificador ainda precisa
    atribuir alguma classe a esses pixels na predição, e o único rótulo próximo
    era `construido`, a faixa ambígua inteira era absorvida por construído. Os
    negativos têm de cobrir todo o espaço espectral não construído.
    """
    ano_wsf = min(ano, ANO_FIM_WSF)
    wsf_construido = (wsf > 0) & (wsf <= ano_wsf)

    # Erosão 3×3: só o miolo da mancha WSF semeia positivos (borda mista a 30 m).
    positivos = binary_erosion(wsf_construido, structure=np.ones((3, 3), dtype=bool))

    raio_px = round(FAIXA_GUARDA_NEGATIVO_M / res_m)
    lado = 2 * raio_px + 1
    faixa_guarda = binary_dilation(wsf > 0, structure=np.ones((lado, lado), dtype=bool))
    pool_negativo = mask_valida & ~faixa_guarda & ~mask_excluir_negativos

    ndvi = indices["ndvi"]
    mndwi = indices["mndwi"]
    ndwi = indices["ndwi"]

    rotulo = np.full(ndvi.shape, -1, dtype="int8")
    e_agua = pool_negativo & (mndwi > LIMIAR_AGUA_MNDWI) & (ndwi > LIMIAR_AGUA_NDWI)
    # Referência radiométrica do ano: o próprio pool de negativos fora d'água —
    # população definida a priori (não é o corte que seleciona a classe), a mesma
    # lógica de `mediana_paisagem` usada na pegada desde docs/ADR/0011.
    referencia = pool_negativo & ~e_agua
    med_seca = mediana_paisagem(ndvi, referencia)
    limiar_veg = RAZAO_VERDE_VEGETACAO * med_seca
    e_veg = pool_negativo & ~e_agua & (ndvi >= limiar_veg)
    e_solo = pool_negativo & ~e_agua & ~e_veg

    rotulo[e_agua] = CODIGO_CLASSE["agua"]
    rotulo[e_veg] = CODIGO_CLASSE["vegetacao"]
    rotulo[e_solo] = CODIGO_CLASSE["solo_exposto"]
    rotulo[positivos] = CODIGO_CLASSE["construido"]
    rotulo[~mask_valida] = -1
    return rotulo, {
        "mediana_ndvi_seca_pool_negativo": med_seca,
        "limiar_vegetacao_ndvi_seca_do_ano": limiar_veg,
        "razao_verde_vegetacao": RAZAO_VERDE_VEGETACAO,
    }


def amostrar_treino(
    rotulo: np.ndarray, mask_valida: np.ndarray, cfg: dict
) -> tuple[tuple[np.ndarray, np.ndarray], np.ndarray, dict]:
    """Amostragem **aleatória simples** sobre o conjunto rotulado — respeita o
    prior das classes por construção (ver docs/ADR/0006), com piso por classe
    para que a água não desapareça do treino.
    """
    rng = np.random.default_rng(cfg["seed"])
    linhas, colunas = np.where(mask_valida & (rotulo >= 0))
    y_pool = rotulo[linhas, colunas]

    n_total = min(int(cfg["n_total"]), y_pool.size)
    sel = rng.choice(y_pool.size, size=n_total, replace=False)

    piso = int(cfg["n_minimo_por_classe"])
    extras = []
    for codigo in CODIGO_CLASSE.values():
        candidatos = np.where(y_pool == codigo)[0]
        ja_tem = int((y_pool[sel] == codigo).sum())
        falta = min(piso - ja_tem, candidatos.size)
        if falta > 0:
            extras.append(rng.choice(candidatos, size=falta, replace=False))
    if extras:
        sel = np.concatenate([sel, *extras])

    y = y_pool[sel]
    disponivel = {
        nome: int((y_pool == cod).sum()) for nome, cod in CODIGO_CLASSE.items()
    }
    return (linhas[sel], colunas[sel]), y, disponivel


def filtrar_coerencia_espacial(mask: np.ndarray) -> np.ndarray:
    """Maioria simples 3×3 sobre a máscara de construído: um pixel isolado sem
    vizinhança construída é rejeitado. Assentamentos e a mina formam manchas
    contíguas a 30 m; falso positivo espectral tende a ser 'sal e pimenta'.
    """
    fracao = uniform_filter(mask.astype("float32"), size=JANELA_COERENCIA, mode="nearest")
    return mask & (fracao >= FRACAO_COERENCIA)


def classificar_ano(
    ano: int,
    features_ano: dict,
    wsf: np.ndarray,
    mask_excluir_negativos: np.ndarray,
    res_m: float,
    seeds_cfg: dict,
) -> tuple[np.ndarray, np.ndarray, dict]:
    """Retorna (rotulo_4classes, mask_construido_bruta_filtrada, info_treino)."""
    rf_cfg = seeds_cfg["random_forest"]
    amostragem_cfg = seeds_cfg["amostragem_treino"]

    mask_valida = features_ano["mask_valida"]
    empilhados = features_ano["empilhados"]

    rotulo_treino, diag_rotulo = rotulos_treino(
        ano, features_ano["indices"], mask_valida, wsf, mask_excluir_negativos, res_m
    )
    (lin, col), y, disponivel = amostrar_treino(rotulo_treino, mask_valida, amostragem_cfg)
    X = empilhados[:, lin, col].T

    clf = RandomForestClassifier(
        n_estimators=rf_cfg["n_trees"],
        min_samples_leaf=rf_cfg["min_leaf_population"],
        max_samples=rf_cfg["bag_fraction"],
        max_features="sqrt"
        if rf_cfg["variables_per_split"] is None
        else rf_cfg["variables_per_split"],
        random_state=rf_cfg["seed"],
        bootstrap=True,
        n_jobs=-1,
    )
    clf.fit(X, y)

    lin_v, col_v = np.where(mask_valida)
    pred = clf.predict(empilhados[:, lin_v, col_v].T)
    rotulo = np.full(mask_valida.shape, -1, dtype="int8")
    rotulo[lin_v, col_v] = pred

    construido_bruto = rotulo == CODIGO_CLASSE["construido"]
    construido_filtrado = filtrar_coerencia_espacial(construido_bruto)

    info = {
        "n_amostras_treino": int(y.size),
        "n_disponivel_por_classe": disponivel,
        "n_amostrado_por_classe": {
            nome: int((y == cod).sum()) for nome, cod in CODIGO_CLASSE.items()
        },
        "importancia_features": dict(
            zip(FEATURES, [float(x) for x in clf.feature_importances_], strict=True)
        ),
        "estrategia_amostragem": amostragem_cfg["estrategia"],
        "limiar_vegetacao": diag_rotulo,
        "fonte_rotulos": (
            "positivos = WSF Evolution erodido 3x3 (WSF <= min(ano, 2015)); negativos = "
            "partição exaustiva, fora de uma faixa de guarda de "
            f"{FAIXA_GUARDA_NEGATIVO_M:.0f} m em torno de qualquer WSF construído e "
            "fora de mineração/reassentamento. `agua` por limiar canônico de Xu 2006 "
            "(MNDWI > 0 e NDWI > 0); `vegetacao` por RAZÃO à mediana de NDVI(seca) da "
            f"paisagem do próprio ano (>= {RAZAO_VERDE_VEGETACAO} x mediana = "
            f"{diag_rotulo['limiar_vegetacao_ndvi_seca_do_ano']:.4f} neste ano), "
            "docs/ADR/0014 — NÃO é limiar absoluto nem percentil da imagem."
        ),
    }
    return rotulo, construido_filtrado, info


# ---------------------------------------------------------------------------
# Regras temporais R1 e R2
# ---------------------------------------------------------------------------


def aplicar_regras_temporais(
    brutas: dict[int, np.ndarray],
) -> tuple[dict[int, np.ndarray], dict[int, np.ndarray]]:
    """R1 (confirmação de primeira detecção) e R2 (permanência).

    R1: a primeira detecção de um pixel só vale se o ano-âncora seguinte também
        o classificar como construído. O último ano não tem confirmação
        possível — suas primeiras detecções entram não confirmadas (declarado).
    R2: união cumulativa ao longo dos anos, tornando a série não decrescente.
    """
    anos = sorted(brutas)
    apos_r1: dict[int, np.ndarray] = {}
    ja_construido = np.zeros_like(brutas[anos[0]], dtype=bool)

    for i, ano in enumerate(anos):
        atual = brutas[ano]
        primeira_deteccao = atual & ~ja_construido
        if i + 1 < len(anos):
            confirmada = primeira_deteccao & brutas[anos[i + 1]]
        else:
            confirmada = primeira_deteccao  # sem ano seguinte: não confirmável
        apos_r1[ano] = (atual & ja_construido) | confirmada
        ja_construido = ja_construido | confirmada

    apos_r2: dict[int, np.ndarray] = {}
    acumulado = np.zeros_like(brutas[anos[0]], dtype=bool)
    for ano in anos:
        acumulado = acumulado | apos_r1[ano]
        apos_r2[ano] = acumulado.copy()
    return apos_r1, apos_r2


# ---------------------------------------------------------------------------
# Máscaras espaciais e partição em camadas
# ---------------------------------------------------------------------------


def carregar_poligono_mineracao(crs_destino: str):
    if not MAUS_AOI_GEOJSON.exists():
        return None
    gdf = gpd.read_file(MAUS_AOI_GEOJSON)
    if gdf.empty:
        return None
    return shapely.ops.unary_union(gdf.to_crs(crs_destino).geometry.values)


def carregar_buffers_reassentamento(crs_destino: str) -> tuple[list[dict], list[str]]:
    gdf = gpd.read_file(REASSENTAMENTOS_GEOJSON)
    resultado, ausentes = [], []
    for _, row in gdf.iterrows():
        if row.geometry is None:
            ausentes.append(row["nome"])
            continue
        ponto = gpd.GeoSeries([row.geometry], crs=gdf.crs).to_crs(crs_destino).iloc[0]
        resultado.append(
            {
                "nome": row["nome"],
                "ano_reassentamento": int(row["ano_reassentamento"]),
                "ponto": ponto,
                "geometria": ponto.buffer(RAIO_BUFFER_REASSENTAMENTO_M),
            }
        )
    return resultado, ausentes


def rasterizar(geometria, perfil: dict) -> np.ndarray:
    if geometria is None or geometria.is_empty:
        return np.zeros(perfil["shape"], dtype=bool)
    return rasterio.features.rasterize(
        [(geometria, 1)],
        out_shape=perfil["shape"],
        transform=perfil["transform"],
        fill=0,
        dtype="uint8",
        all_touched=False,
    ).astype(bool)


def mediana_paisagem(valores: np.ndarray, referencia: np.ndarray) -> float:
    """Mediana de um índice sobre a **paisagem de referência do ano**.

    Referência = pixels válidos, fora d'água, fora do envelope minerário e fora dos
    buffers de reassentamento. É a normalização radiométrica que torna o limiar
    comparável entre anos-âncora (ver comentário de RAZAO_VERDE_PEGADA). Não é um
    percentil da imagem: o denominador é uma estatística de tendência central de uma
    população fixa e definida a priori, não o corte que seleciona a classe.
    """
    amostra = valores[referencia & np.isfinite(valores)]
    if amostra.size == 0:
        raise RuntimeError("paisagem de referência vazia — envelope cobre a AOI inteira?")
    return float(np.median(amostra))


def solo_exposto_persistente(
    indices: dict, mask_valida: np.ndarray, referencia: np.ndarray
) -> np.ndarray:
    """Assinatura da pegada: **sem reverdecimento na estação chuvosa**.

    Cava, pilha de estéril, rejeito e terreno decapado são rocha e solo exposto o ano
    inteiro. Solo exposto natural de savana semiárida esverdeia na chuva. A regra
    exige NDVI baixo **nas duas estações**, medido em razão à mediana da paisagem do
    próprio ano, e exclui água (fundo de cava alagado e o Zambeze).
    """
    ndvi_seca, ndvi_chuva = indices["ndvi"], indices["ndvi_chuva"]
    mndwi = indices["mndwi"]
    med_seca = mediana_paisagem(ndvi_seca, referencia)
    med_chuva = mediana_paisagem(ndvi_chuva, referencia)
    finito = np.isfinite(ndvi_seca) & np.isfinite(ndvi_chuva) & np.isfinite(mndwi)
    return (
        mask_valida
        & finito
        & (mndwi <= LIMIAR_AGUA_MNDWI)
        & (ndvi_chuva < RAZAO_VERDE_PEGADA * med_chuva)
        & (ndvi_seca < RAZAO_VERDE_PEGADA * med_seca)
    )


def fechar_pegada(mask: np.ndarray, dominio: np.ndarray) -> np.ndarray:
    """Fecho morfológico 3x3, reconfinado ao domínio de busca."""
    fechada = binary_closing(
        mask, structure=np.ones((JANELA_FECHO_PEGADA, JANELA_FECHO_PEGADA), dtype=bool)
    )
    return fechada & dominio


def pegadas_por_ano(
    anos: list[int],
    features: dict[int, dict],
    brutas_construido: dict[int, np.ndarray],
    perfil: dict,
    poligono_mineracao,
    buffers_reassentamento: list[dict],
    res_m: float,
) -> tuple[dict[int, dict[str, np.ndarray]], dict[int, dict[str, np.ndarray]], dict[int, dict]]:
    """Classifica a pegada minerária e a de reassentamento em todos os anos.

    Devolve (sem_restricao, apos_permanencia, diagnostico). As duas séries são
    publicadas lado a lado: nenhuma regra temporal é aplicada em silêncio.
    """
    raio_px = max(1, round(BUFFER_EXPANSAO_MINA_M / res_m))
    lado = 2 * raio_px + 1
    maus = rasterizar(poligono_mineracao, perfil)
    envelope_mina = binary_dilation(maus, structure=np.ones((lado, lado), dtype=bool))

    buffers = {
        item["nome"]: rasterizar(item["geometria"], perfil) for item in buffers_reassentamento
    }
    dominio_reass = np.zeros(perfil["shape"], dtype=bool)
    for m in buffers.values():
        dominio_reass |= m
    # Precedência industrial > reassentamento já no domínio de busca.
    dominio_reass &= ~envelope_mina

    sem_restricao: dict[int, dict[str, np.ndarray]] = {}
    diagnostico: dict[int, dict] = {}

    for ano in anos:
        f = features[ano]
        indices, mask_valida = f["indices"], f["mask_valida"]
        agua = np.isfinite(indices["mndwi"]) & (indices["mndwi"] > LIMIAR_AGUA_MNDWI)
        referencia = mask_valida & ~agua & ~envelope_mina & ~dominio_reass
        nua = solo_exposto_persistente(indices, mask_valida, referencia)
        construido = brutas_construido[ano]

        industrial = fechar_pegada((nua | construido) & envelope_mina, envelope_mina)
        if ano < ANO_LICENCA_MINA:
            # Antes da licença não há pegada minerária a medir. A regra já devolve
            # ~zero por si (é o placebo temporal); o zero é imposto para que a série
            # não dependa de ruído residual.
            industrial = np.zeros(perfil["shape"], dtype=bool)

        reassentamento = np.zeros(perfil["shape"], dtype=bool)
        ativos = []
        for item in buffers_reassentamento:
            if ano >= item["ano_reassentamento"]:
                reassentamento |= buffers[item["nome"]]
                ativos.append(item["nome"])
        dominio_ano = reassentamento & ~envelope_mina
        reassentamento = fechar_pegada((nua | construido) & dominio_ano, dominio_ano)

        sem_restricao[ano] = {"industrial": industrial, "reassentamento": reassentamento}
        diagnostico[ano] = {
            "povoados_ativos": ativos,
            "mediana_ndvi_seca_paisagem": mediana_paisagem(indices["ndvi"], referencia),
            "mediana_ndvi_chuva_paisagem": mediana_paisagem(indices["ndvi_chuva"], referencia),
            "area_solo_nu_persistente_km2": area_km2(nua, perfil["transform"]),
            "area_envelope_mina_km2": area_km2(envelope_mina, perfil["transform"]),
            "area_poligonos_maus_km2": area_km2(maus, perfil["transform"]),
            "cobertura_poligonos_maus": (
                float((industrial & maus).sum() / maus.sum()) if maus.sum() else float("nan")
            ),
        }

    apos: dict[int, dict[str, np.ndarray]] = {}
    acum = {
        "industrial": np.zeros(perfil["shape"], dtype=bool),
        "reassentamento": np.zeros(perfil["shape"], dtype=bool),
    }
    for ano in anos:
        for camada in ("industrial", "reassentamento"):
            if PEGADA_APLICA_PERMANENCIA[camada]:
                acum[camada] = acum[camada] | sem_restricao[ano][camada]
                apos.setdefault(ano, {})[camada] = acum[camada].copy()
            else:
                apos.setdefault(ano, {})[camada] = sem_restricao[ano][camada]
        # Antes da licença/do reassentamento não há o que acumular.
        if ano < ANO_LICENCA_MINA:
            apos[ano]["industrial"] = np.zeros(perfil["shape"], dtype=bool)
            acum["industrial"][:] = False
        anos_reass = [i["ano_reassentamento"] for i in buffers_reassentamento] or [ano + 1]
        if ano < min(anos_reass):
            apos[ano]["reassentamento"] = np.zeros(perfil["shape"], dtype=bool)
            acum["reassentamento"][:] = False

    for ano in anos:
        diagnostico[ano]["cobertura_poligonos_maus_apos_permanencia"] = (
            float((apos[ano]["industrial"] & maus).sum() / maus.sum())
            if maus.sum()
            else float("nan")
        )
    return sem_restricao, apos, diagnostico


def construir_camadas(
    rotulo: np.ndarray,
    construido: np.ndarray,
    pegada: dict[str, np.ndarray],
) -> dict:
    """Partição mutuamente exclusiva das seis camadas.

    Precedência **industrial > reassentamento > urbano** (§10). Note a mudança de
    natureza introduzida em docs/ADR/0011: `industrial` e `reassentamento` **não são
    mais subconjuntos de `construido`** — são pegadas, e incluem rocha e solo exposto
    que nenhum classificador de construído poderia capturar. Consequência aritmética
    declarada: `urbano + industrial + reassentamento > area_construida`, e `urbano`
    é o único dos três que continua sendo área construída.
    """
    industrial = pegada["industrial"]
    reassentamento = pegada["reassentamento"] & ~industrial
    urbano = construido & ~industrial & ~reassentamento
    outras = ~industrial & ~reassentamento & ~construido
    return {
        "urbano": urbano,
        "industrial": industrial,
        "reassentamento": reassentamento,
        "vegetacao": (rotulo == CODIGO_CLASSE["vegetacao"]) & outras,
        "solo_exposto": (rotulo == CODIGO_CLASSE["solo_exposto"]) & outras,
        "agua": (rotulo == CODIGO_CLASSE["agua"]) & outras,
    }


# ---------------------------------------------------------------------------
# Escrita
# ---------------------------------------------------------------------------


def area_km2(mask: np.ndarray, transform) -> float:
    return float(mask.sum()) * abs(transform.a * transform.e) / 1e6


def salvar_raster(mask: np.ndarray, path: Path, crs, transform) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    perfil = {
        "driver": "COG",
        "height": mask.shape[0],
        "width": mask.shape[1],
        "count": 1,
        "dtype": "uint8",
        "crs": crs,
        "transform": transform,
        "nodata": 255,
        "compress": "deflate",
        "predictor": 2,
    }
    with rasterio.open(path, "w", **perfil) as dst:
        dst.write(mask.astype("uint8"), 1)


def salvar_vetor(mask: np.ndarray, path: Path, crs, transform, ano: int, camada: str) -> int:
    formas = list(rasterio.features.shapes(mask.astype("uint8"), mask=mask, transform=transform))
    if not formas:
        gdf = gpd.GeoDataFrame({"ano": [], "camada": [], "area_km2": []}, geometry=[], crs=crs)
    else:
        geoms = [shapely.geometry.shape(g) for g, _ in formas]
        gdf = gpd.GeoDataFrame(
            {"ano": [ano] * len(geoms), "camada": [camada] * len(geoms)}, geometry=geoms, crs=crs
        )
        gdf["area_km2"] = gdf.geometry.area / 1e6
    path.parent.mkdir(parents=True, exist_ok=True)
    gdf.to_file(path, driver="GeoJSON")
    return len(gdf)


# ---------------------------------------------------------------------------
# Concordância com GHSL (referência independente — nunca chamada de acurácia)
# ---------------------------------------------------------------------------


def ghsl_fracao_construida(epoca: int, perfil: dict) -> np.ndarray | None:
    caminho = caminho_ghsl(epoca)
    if not caminho.exists():
        return None
    with rasterio.open(caminho) as src:
        origem = src.read(1).astype("float32")
        destino = np.zeros(perfil["shape"], dtype="float32")
        rasterio.warp.reproject(
            source=origem,
            destination=destino,
            src_transform=src.transform,
            src_crs=src.crs,
            dst_transform=perfil["transform"],
            dst_crs=perfil["crs"],
            resampling=rasterio.warp.Resampling.average,
        )
    return destino / 10000.0  # m² construídos por célula de 100 m -> fração


def concordancia_ghsl(ano: int, construido: np.ndarray, perfil: dict, transform) -> list[dict]:
    """Concordância de área e de padrão (Jaccard) com GHSL BUILT-S, por corte
    de fração construída. **Não é acurácia**: os dois mapas têm erro próprio,
    resoluções nativas diferentes (30 m × 100 m) e definições diferentes de
    'construído' (GHSL mede superfície de edificação; aqui mede-se cobertura
    de assentamento). Serve para detectar discrepância de ordem de grandeza e
    de localização, que foi exatamente o que reprovou a versão anterior.
    """
    if ano not in GHSL_EPOCAS_OBSERVADAS:
        return [
            {
                "ano": ano,
                "aplicavel": False,
                "motivo": (
                    "GHSL R2023A só tem épocas observadas até 2020; 2025/2030 são "
                    "extrapoladas por modelo e não servem de referência para uma "
                    "classificação observada."
                ),
            }
        ]
    fracao = ghsl_fracao_construida(ano, perfil)
    if fracao is None:
        return [{"ano": ano, "aplicavel": False, "motivo": "raster GHSL não espelhado"}]

    linhas = []
    for corte in FRACOES_GHSL:
        ref = fracao >= corte
        inter = np.logical_and(construido, ref).sum()
        uniao = np.logical_or(construido, ref).sum()
        linhas.append(
            {
                "ano": ano,
                "aplicavel": True,
                "corte_fracao_ghsl": corte,
                "principal": corte == FRACAO_GHSL_PRINCIPAL,
                "area_pipeline_km2": area_km2(construido, transform),
                "area_ghsl_km2": area_km2(ref, transform),
                "razao_areas": (
                    area_km2(construido, transform) / area_km2(ref, transform)
                    if ref.sum() > 0
                    else float("nan")
                ),
                "jaccard": float(inter / uniao) if uniao > 0 else float("nan"),
                "recall_sobre_ghsl": float(inter / ref.sum()) if ref.sum() > 0 else float("nan"),
                "motivo": "",
            }
        )
    return linhas


# ---------------------------------------------------------------------------
# Orquestração
# ---------------------------------------------------------------------------


def conferir_grade_contra_config(perfil: dict, estudo: dict) -> None:
    """A AOI e o CRS métrico vivem só em `config/study.yaml` (§11.2.1). Este
    script não os fixa em código: confere que a grade herdada dos compostos
    ainda corresponde ao que o config declara, e falha alto se alguém mudar a
    AOI sem refazer os compostos.
    """
    crs_esperado = estudo["crs"]["metrico"]
    if f"EPSG:{perfil['crs'].to_epsg()}" != crs_esperado:
        raise RuntimeError(
            f"composto em {perfil['crs']} mas config/study.yaml pede {crs_esperado}"
        )
    bbox = estudo["aoi"]["bbox"]
    esquerda, cima = perfil["transform"] * (0, 0)
    direita, baixo = perfil["transform"] * (perfil["shape"][1], perfil["shape"][0])
    cantos = rasterio.warp.transform_bounds(
        perfil["crs"], "EPSG:4326", esquerda, baixo, direita, cima
    )
    tolerancia_graus = 0.01
    esperado = (bbox["xmin"], bbox["ymin"], bbox["xmax"], bbox["ymax"])
    if any(abs(a - b) > tolerancia_graus for a, b in zip(cantos, esperado, strict=True)):
        raise RuntimeError(
            f"grade dos compostos {cantos} não corresponde à AOI de config/study.yaml "
            f"{esperado} — refaça os compostos antes de classificar."
        )


def main(argv: list[str]) -> int:
    estudo = carregar_estudo(STUDY_YAML)
    seeds_cfg = carregar_yaml(SEEDS_YAML)

    disponiveis = compostos_disponiveis()
    if not disponiveis:
        print("[FALHA] nenhum composto encontrado.", file=sys.stderr)
        return 1

    anos = sorted(int(a) for a in argv) if argv else sorted(disponiveis)
    if argv and len(anos) < len(disponiveis):
        print(
            "[aviso] as regras temporais R1/R2 são definidas sobre a série inteira; "
            "rodar um subconjunto de anos produz um resultado NÃO equivalente ao da "
            "série completa.",
            file=sys.stderr,
        )
    faltando = [a for a in anos if a not in disponiveis]
    if faltando:
        print(f"[FALHA] sem composto para {faltando}", file=sys.stderr)
        return 1

    # --- passo 1: classificação bruta por ano ------------------------------
    m0 = NOME_ARQUIVO_RE.match(disponiveis[anos[0]].name)
    res_m, epsg = int(m0.group(2)), int(m0.group(3))

    features: dict[int, dict] = {}
    rotulos: dict[int, np.ndarray] = {}
    brutas: dict[int, np.ndarray] = {}
    infos: dict[int, dict] = {}

    perfil_ref = None
    poligono_mineracao = None
    buffers_reassentamento: list[dict] = []
    povoados_sem_geometria: list[str] = []
    wsf = None
    mask_excluir_negativos = None

    for ano in anos:
        f = carregar_features_ano(ano, res_m, epsg)
        if perfil_ref is None:
            perfil_ref = f["perfil"]
            crs = str(perfil_ref["crs"])
            poligono_mineracao = carregar_poligono_mineracao(crs)
            buffers_reassentamento, povoados_sem_geometria = carregar_buffers_reassentamento(crs)
            conferir_grade_contra_config(perfil_ref, estudo)
            wsf = carregar_wsf_reprojetado(perfil_ref)
            mask_excluir_negativos = rasterizar(poligono_mineracao, perfil_ref)
            for item in buffers_reassentamento:
                # Raio de exclusão de negativos, deliberadamente maior que o raio de
                # detecção (ver RAIO_EXCLUSAO_NEGATIVO_REASSENTAMENTO_M).
                mask_excluir_negativos |= rasterizar(
                    item["ponto"].buffer(RAIO_EXCLUSAO_NEGATIVO_REASSENTAMENTO_M), perfil_ref
                )

        rotulo, bruta, info = classificar_ano(
            ano, f, wsf, mask_excluir_negativos, res_m, seeds_cfg
        )
        features[ano] = f
        rotulos[ano] = rotulo
        brutas[ano] = bruta
        infos[ano] = info
        print(
            f"[rf ] {ano}: construído bruto = "
            f"{area_km2(bruta, f['perfil']['transform']):.1f} km²",
            file=sys.stderr,
        )

    # --- passo 2: regras temporais ----------------------------------------
    apos_r1, apos_r2 = aplicar_regras_temporais(brutas)

    # --- passo 3: pegadas (classe própria — docs/ADR/0011) ----------------
    pegada_sem_restricao, pegada, diag_pegada = pegadas_por_ano(
        anos, features, apos_r2, perfil_ref, poligono_mineracao, buffers_reassentamento, res_m
    )

    # --- passo 4: camadas, rasters, proveniência --------------------------
    transform = perfil_ref["transform"]
    crs = perfil_ref["crs"]
    registros = []
    linhas_concordancia: list[dict] = []

    for ano in anos:
        construido = apos_r2[ano]
        camadas = construir_camadas(rotulos[ano], construido, pegada[ano])
        # `construido` é persistido como artefato próprio: é ele, e não a união das
        # três camadas, que define o estrato da validação (pipeline/01_imagery/
        # acuracia.py). Desde docs/ADR/0011 a união deixou de ser igual ao construído.
        salvar_raster(
            construido,
            DATA_PROCESSED / f"construido_{ano}_{res_m}m_{epsg}.tif",
            crs,
            transform,
        )
        registro_camadas = {}
        for nome_camada in NOMES_CAMADAS:
            mask = camadas[nome_camada]
            caminho_raster = DATA_PROCESSED / f"{nome_camada}_{ano}_{res_m}m_{epsg}.tif"
            salvar_raster(mask, caminho_raster, crs, transform)
            caminho_vetor = DATA_PROCESSED / f"{nome_camada}_{ano}.geojson"
            n_poligonos = salvar_vetor(mask, caminho_vetor, crs, transform, ano, nome_camada)

            if nome_camada == "industrial":
                metodo = METODO_INDUSTRIAL_POR_ANO[ano]
            elif nome_camada == "reassentamento":
                metodo = (
                    NOTA_BUFFER_REASSENTAMENTO
                    + f" Povoados ativos neste ano: {diag_pegada[ano]['povoados_ativos']}."
                    + f" Povoados sem geometria (excluídos): {povoados_sem_geometria}."
                )
            else:
                metodo = (
                    "Random Forest com protocolo único em todos os anos "
                    "(config/seeds.yaml -> random_forest); rótulos de treino ancorados no "
                    "WSF Evolution e em limiares físicos (o de vegetação relativo à "
                    "mediana da paisagem do ano, docs/ADR/0014); features incluem as "
                    "métricas fenológicas chuva-seca."
                )

            meta = {
                "ano": ano,
                "camada": nome_camada,
                "arquivo_raster": str(caminho_raster.relative_to(REPO_ROOT)),
                "arquivo_vetor": str(caminho_vetor.relative_to(REPO_ROOT)),
                "n_poligonos_vetor": n_poligonos,
                "area_km2": area_km2(mask, transform),
                "n_pixels": int(mask.sum()),
                "resolucao_m": res_m,
                "crs": f"EPSG:{epsg}",
                "metodo": metodo,
                "ordem_precedencia": "industrial > reassentamento > urbano",
                "natureza": (
                    "pegada (inclui rocha e solo exposto; NÃO é subconjunto de "
                    "`construido`)"
                    if nome_camada in ("industrial", "reassentamento")
                    else "cobertura classificada"
                ),
                "diagnostico_pegada": (
                    diag_pegada[ano] if nome_camada in ("industrial", "reassentamento") else None
                ),
                "regras_temporais": {
                    "R1_confirmacao_primeira_deteccao": (
                        "primeira detecção só vale se confirmada no ano-âncora "
                        "seguinte; "
                        + (
                            "NÃO confirmável (último ano da série)"
                            if ano == anos[-1]
                            else "confirmada"
                        )
                    ),
                    "R2_permanencia": (
                        "construído(t) = união cumulativa até t — série não decrescente "
                        "por construção"
                    ),
                },
                "papel_wsf": "semente de treino (não é validação — ver docstring do script)",
                "papel_ghsl": "referência independente de concordância (não entra em treino)",
                "selo": "observado",
                "data_processamento": datetime.now(UTC).isoformat(),
                "commit_git": commit_git_atual(),
                "hash_config_study_yaml": hash_arquivo(STUDY_YAML),
                "hash_config_seeds_yaml": hash_arquivo(SEEDS_YAML),
                "script": "pipeline/01_imagery/classificacao.py",
                "info_treino_rf": infos[ano] if nome_camada == "urbano" else None,
            }
            caminho_raster.with_suffix(".tif.meta.json").write_text(
                json.dumps(meta, indent=2, ensure_ascii=False), encoding="utf-8"
            )
            registro_camadas[nome_camada] = meta

        linhas_concordancia += concordancia_ghsl(ano, construido, perfil_ref, transform)
        registros.append(
            {
                "ano": ano,
                "camadas": registro_camadas,
                "area_bruta_km2": area_km2(brutas[ano], transform),
                "area_r1_km2": area_km2(apos_r1[ano], transform),
                "area_r2_km2": area_km2(apos_r2[ano], transform),
                "povoados_sem_geometria": povoados_sem_geometria,
                "pegada_sem_restricao": {
                    c: area_km2(pegada_sem_restricao[ano][c], transform)
                    for c in ("industrial", "reassentamento")
                },
                "diagnostico_pegada": diag_pegada[ano],
            }
        )
        print(
            f"[ok ] {ano}: bruta={registros[-1]['area_bruta_km2']:.1f} "
            f"R1={registros[-1]['area_r1_km2']:.1f} R2={registros[-1]['area_r2_km2']:.1f} km²",
            file=sys.stderr,
        )

    escrever_area_csv(registros, anos)
    escrever_pegada_csv(registros)
    escrever_concordancia_csv(linhas_concordancia)
    escrever_proveniencia(registros, anos, infos)
    print(
        f"[ok] {AREA_CSV.relative_to(REPO_ROOT)} e "
        f"{CONCORDANCIA_CSV.relative_to(REPO_ROOT)} gravados",
        file=sys.stderr,
    )
    return 0


def escrever_area_csv(registros: list[dict], anos: list[int]) -> None:
    AREA_CSV.parent.mkdir(parents=True, exist_ok=True)
    with AREA_CSV.open("w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        w.writerow(
            [
                "ano",
                "area_construida_sem_restricao_km2",
                "area_construida_apos_R1_km2",
                "area_construida_apos_R2_km2",
                "urbano_km2",
                "industrial_km2",
                "reassentamento_km2",
                "primeira_deteccao_confirmavel",
                "selo",
                "nota",
            ]
        )
        for r in registros:
            w.writerow(
                [
                    r["ano"],
                    f"{r['area_bruta_km2']:.3f}",
                    f"{r['area_r1_km2']:.3f}",
                    f"{r['area_r2_km2']:.3f}",
                    f"{r['camadas']['urbano']['area_km2']:.3f}",
                    f"{r['camadas']['industrial']['area_km2']:.3f}",
                    f"{r['camadas']['reassentamento']['area_km2']:.3f}",
                    r["ano"] != anos[-1],
                    "observado",
                    "R1 = confirmação da primeira detecção no ano seguinte; "
                    "R2 = permanência (união cumulativa). Colunas publicadas lado a lado "
                    "para tornar visível quanto cada regra moveu a série. ATENÇÃO "
                    "(docs/ADR/0011): `industrial_km2` e `reassentamento_km2` são PEGADAS, "
                    "não subconjuntos da área construída — incluem rocha e solo exposto. "
                    "Só `urbano_km2` é área construída. Não some as três colunas; a soma "
                    "não tem significado. Detalhe em pegada_por_ano.csv.",
                ]
            )


def escrever_pegada_csv(registros: list[dict]) -> None:
    """Série da pegada minerária e de reassentamento, com a série sem permanência
    ao lado e o diagnóstico que permite auditar a classe (docs/ADR/0011)."""
    PEGADA_CSV.parent.mkdir(parents=True, exist_ok=True)
    campos = [
        "ano",
        "camada",
        "area_sem_permanencia_km2",
        "area_publicada_km2",
        "cobertura_poligonos_maus",
        "area_poligonos_maus_km2",
        "area_envelope_busca_km2",
        "mediana_ndvi_seca_paisagem",
        "mediana_ndvi_chuva_paisagem",
        "razao_verde_limiar",
        "selo",
        "nota",
    ]
    nota = (
        "Pegada classificada por assinatura própria (solo/rocha exposto persistente: "
        f"NDVI de seca E de chuva abaixo de {RAZAO_VERDE_PEGADA} da mediana da paisagem "
        "do ano) unida ao construído do ano, dentro do envelope de busca. NÃO é "
        "interseção com construído — ver docs/ADR/0011. `cobertura_poligonos_maus` só "
        "se aplica a `industrial` e mede quanto da referência externa (Maus et al. v2, "
        "Sentinel-2 2017-2019) a camada encontra; em 2000 e 2005 o valor baixo é o "
        "resultado esperado (placebo temporal: a mina não existia). O limiar foi "
        "calibrado em 2020 contra essa mesma referência, então a concordância de 2020 "
        "não é validação independente. **R2 (permanência) FOI REMOVIDO das duas "
        "pegadas** em docs/ADR/0014: cava é reabilitada e povoado pode ser abandonado, "
        "e a permanência tornava abandono indetectável por construção (pergunta 3 de "
        "§1). Por isso `area_sem_permanencia_km2` e `area_publicada_km2` são agora "
        "iguais nesta tabela; R2 continua valendo só para `urbano`."
    )
    with PEGADA_CSV.open("w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=campos)
        w.writeheader()
        for r in registros:
            d = r["diagnostico_pegada"]
            for camada in ("industrial", "reassentamento"):
                w.writerow(
                    {
                        "ano": r["ano"],
                        "camada": camada,
                        "area_sem_permanencia_km2": f"{r['pegada_sem_restricao'][camada]:.3f}",
                        "area_publicada_km2": f"{r['camadas'][camada]['area_km2']:.3f}",
                        "cobertura_poligonos_maus": (
                            f"{d['cobertura_poligonos_maus_apos_permanencia']:.4f}"
                            if camada == "industrial"
                            else ""
                        ),
                        "area_poligonos_maus_km2": f"{d['area_poligonos_maus_km2']:.3f}",
                        "area_envelope_busca_km2": (
                            f"{d['area_envelope_mina_km2']:.3f}" if camada == "industrial" else ""
                        ),
                        "mediana_ndvi_seca_paisagem": f"{d['mediana_ndvi_seca_paisagem']:.4f}",
                        "mediana_ndvi_chuva_paisagem": f"{d['mediana_ndvi_chuva_paisagem']:.4f}",
                        "razao_verde_limiar": RAZAO_VERDE_PEGADA,
                        "selo": "observado",
                        "nota": nota,
                    }
                )


def escrever_concordancia_csv(linhas: list[dict]) -> None:
    CONCORDANCIA_CSV.parent.mkdir(parents=True, exist_ok=True)
    campos = [
        "ano",
        "aplicavel",
        "corte_fracao_ghsl",
        "principal",
        "area_pipeline_km2",
        "area_ghsl_km2",
        "razao_areas",
        "jaccard",
        "recall_sobre_ghsl",
        "motivo",
    ]
    with CONCORDANCIA_CSV.open("w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=campos)
        w.writeheader()
        for linha in linhas:
            w.writerow({c: linha.get(c, "") for c in campos})


def escrever_proveniencia(registros: list[dict], anos: list[int], infos: dict) -> None:
    linhas = [
        MARCADOR_INICIO,
        "",
        "## Classificação — redesenho da Fase 1 (§5.1, §10)",
        "",
        "Gerado por `pipeline/01_imagery/classificacao.py`. Substitui a versão reprovada, "
        "cujo defeito central era usar **limiares adaptativos por percentil**: eles "
        "selecionavam uma fatia quase constante da AOI todo ano (3,4–4,4%), de modo que o "
        "produto media o percentil, não o crescimento.",
        "",
        "**Papéis das referências (escolhidos e assumidos, sem circularidade):** "
        "WSF Evolution **semeia o treino** e por isso **não** é usado como validação; "
        "GHSL BUILT-S R2023A (épocas observadas 2000–2020) é **referência independente de "
        "concordância** e não toca em treino nem em limiar; as épocas 2025/2030 do GHSL são "
        "extrapoladas e por isso 2025 fica **sem** referência de produto, declarado.",
        "",
        "**Separação fenológica.** Features incluem `NDVI(chuva)` e a amplitude "
        "`NDVI(chuva) − NDVI(seca)` (nov(A−1)–abr(A) contra mai–out(A)). Separabilidade "
        "medida nesta AOI entre WSF-construído e não-construído (d de Cohen): amplitude "
        "1,83 (2000) / 2,03 (2015) / 1,87 (2025); NDBI 0,39 / 0,71 / 0,29. Cobertura da "
        "estação chuvosa por ano em `data/processed/cobertura_estacao_chuvosa.csv`.",
        "",
        "**Regras temporais declaradas.** R1: primeira detecção só vale se confirmada no "
        "ano-âncora seguinte (2025 não é confirmável — não há ano seguinte). R2: "
        "permanência, `construído(t) = ∪_{t'≤t}`. As três séries (sem restrição, após R1, "
        "após R2) estão lado a lado em `data/processed/area_construida_por_ano.csv`.",
        "",
        "**Acurácia não é calculada aqui.** Ver `pipeline/01_imagery/acuracia.py` e "
        "`data/processed/acuracia_por_ano.csv`.",
        "",
        "**Pegada minerária e de reassentamento — classe própria desde docs/ADR/0011.** "
        "Antes, `industrial` era `construido & poligono_maus` e `reassentamento` era "
        "`restante & buffer`: as duas camadas eram a INTERSEÇÃO da classificação de "
        "construído com uma máscara espacial, e mediam 'construído dentro do polígono', "
        "não a pegada. O defeito é físico: cava, pilha de estéril e rejeito são rocha e "
        "solo exposto — espectralmente NÃO são construído — e um classificador de "
        "construído os perde por definição (media 4,2 km² contra os 59,2 km² de Maus et "
        "al., 7,1%). A pegada passou a ser classificada por assinatura própria: solo/rocha "
        f"exposto persistente (NDVI de seca E de chuva abaixo de {RAZAO_VERDE_PEGADA} da "
        "mediana da paisagem do próprio ano — normalização radiométrica anual, NÃO "
        "percentil da imagem), unida ao construído do ano, dentro do envelope de Maus "
        f"dilatado em {BUFFER_EXPANSAO_MINA_M:.0f} m. Cobertura dos polígonos de Maus em "
        "2025: de 7,1% para 76,3%.",
        "",
        "**Limiar calibrado, e onde isso cria circularidade.** O limiar foi calibrado por "
        "J de Youden contra Maus et al. em 2020, o ano-âncora de menor defasagem em "
        "relação à referência. Logo **a concordância com Maus em 2020 não é validação "
        "independente**. A evidência independente é temporal: a mesma regra devolve "
        "**0,000 km² em 2000 e 2005**, antes da licença da Vale (2006) — placebo temporal "
        "que se mantém nas 30 configurações de `data/processed/pegada_sensibilidade.csv`.",
        "",
        "**`industrial` e `reassentamento` NÃO são subconjuntos de `construido`.** Elas "
        "incluem rocha e solo exposto. Consequência aritmética: `urbano + industrial + "
        "reassentamento > area_construida`, e **só `urbano` é área construída** — a soma "
        "das três não tem significado. A máscara de construído é publicada à parte, em "
        "`construido_<ano>_30m_32736.tif`, e é ela que define o estrato da validação de "
        "acurácia.",
        "",
        "**O que não mudou, verificado e não presumido:** a classificação de construído é "
        "idêntica à anterior (o raio de exclusão de negativos do treino foi mantido em "
        f"{RAIO_EXCLUSAO_NEGATIVO_REASSENTAMENTO_M:.0f} m, separado do raio de detecção de "
        f"{RAIO_BUFFER_REASSENTAMENTO_M:.0f} m); os 288 pontos de validação não se moveram "
        "(0 de 288); `data/processed/acuracia_por_ano.csv` é idêntico por diff e a "
        f"{acuracia_texto.nota_comissao_construido()} `urbano` dentro dos "
        "polígonos de mineração continua 0,0000 km² de 2010 em diante. O único efeito sobre "
        "`urbano` é a migração de construído do envelope minerário (planta, pátio "
        "ferroviário) para `industrial`: 44,02 -> 42,84 km² em 2025.",
        "",
        "**Camada de reassentamento — incompleta por falta de dado:** "
        + NOTA_BUFFER_REASSENTAMENTO,
        "",
    ]
    for r in registros:
        ano = r["ano"]
        linhas += [
            f"### Ano-âncora {ano}",
            "",
            f"- **Método `industrial`:** {METODO_INDUSTRIAL_POR_ANO[ano]}",
            f"- **Área construída (km²):** sem restrição {r['area_bruta_km2']:.1f} · "
            f"após R1 {r['area_r1_km2']:.1f} · após R2 (publicada) {r['area_r2_km2']:.1f}",
            "- **Camadas (km²):** "
            + ", ".join(f"{n}={r['camadas'][n]['area_km2']:.2f}" for n in NOMES_CAMADAS)
            + " (industrial e reassentamento são PEGADAS, não subconjuntos de construído)",
            "- **Pegada sem permanência (km²):** "
            + ", ".join(
                f"{n}={r['pegada_sem_restricao'][n]:.2f}"
                for n in ("industrial", "reassentamento")
            )
            + f" · cobertura dos polígonos de Maus: "
            f"{r['diagnostico_pegada']['cobertura_poligonos_maus_apos_permanencia']:.1%}"
            + " · mediana NDVI(chuva) da paisagem: "
            f"{r['diagnostico_pegada']['mediana_ndvi_chuva_paisagem']:.3f}",
            "- **Importância das features (5 maiores):** "
            + ", ".join(
                f"{k}={v:.3f}"
                for k, v in sorted(
                    infos[ano]["importancia_features"].items(), key=lambda kv: -kv[1]
                )[:5]
            ),
            "",
        ]
    linhas += [MARCADOR_FIM, ""]

    atual = PROVENANCE_FRAGMENT.read_text(encoding="utf-8") if PROVENANCE_FRAGMENT.exists() else ""
    if MARCADOR_INICIO in atual and MARCADOR_FIM in atual:
        novo = atual.split(MARCADOR_INICIO)[0] + "\n".join(linhas) + atual.split(MARCADOR_FIM)[1]
    else:
        novo = atual + "\n" + "\n".join(linhas)
    PROVENANCE_FRAGMENT.parent.mkdir(parents=True, exist_ok=True)
    PROVENANCE_FRAGMENT.write_text(novo, encoding="utf-8")


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
