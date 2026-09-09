<!-- SECAO_METRICAS_FASE2_INICIO -->
## Forma urbana (§5.2, Fase 2)

Scripts: `pipeline/02_metrics/area_cagr.py`, `fragmentacao.py`,
`tipologia_expansao.py`, `edificacoes.py`, consolidados em
`write_stats_forma_urbana.py` -> `data/interim/stats_forma_urbana.csv` ->
`stats_by_year_by_unit.py` -> `data/processed/stats_by_year_by_unit.csv`
(familia `forma_urbana`). Gerado em 2026-09-08.

### Duas séries, dois papéis (ADR 0008) — não misturar

- **Série de tendência (área, CAGR)**: WSF Evolution (DLR), nível A, ano de
  primeira detecção por pixel, 1985-2015. Único produto usado para "quanto
  cresceu e a que taxa". Cobre `tete`, `moatize`, `cateme`, `mwaladzi`; não
  cobre `industrial` (WSF é assentamento, não uso do solo) nem 2015->2020 ou
  2020->2025 (fim da série do WSF nesta entrega — linhas ausentes, não
  aproximadas).
- **Série de decomposição por camada**: classificação própria (Random Forest,
  protocolo único, 6 anos-âncora), nível A (Landsat/Sentinel via STAC). Única
  fonte que separa `urbano`/`industrial`/`reassentamento`. Toda área e
  fragmentação desta série é marcada `confiavel_para_tendencia=False` e
  carrega a acurácia do usuário medida em `data/processed/acuracia_por_ano.csv`
  (0,286-0,625, ADR 0009): 37,5%-71,4% do que o mapa chama de construído não é.
  Direção de expansão e tipologia (infill/borda/leapfrog) são declaradas
  robustas a essa comissão (um falso positivo disperso tende a virar
  "leapfrog" de baixa densidade, não inventa infill onde não há nada) — teto,
  não medida limpa, para a proporção de leapfrog.

### Intensidade de uso (área/população) — NÃO calculada

Não há série de população por unidade e por ano compatível com o polígono de
núcleo urbano usado aqui (ver `demografia_fase2.md`: só dois pontos por
unidade, 2017 observado e 2025 modelado, geografia de distrito/cidade
administrativa, não do núcleo mapeado). Cruzar área com essa população
misturaria duas geografias incomparáveis — não publicado. Pendência aberta.

### Rosa de expansão

Setores: 16 x 22,5°, 0°=Norte, sentido horário, a partir do **centróide do
construído em t0 da própria unidade** (não do ponto-sede fixo) — a origem
muda a cada período porque a mancha muda. Estatística de Rayleigh
(`direcao_expansao_graus`, `concentracao_direcional_r`) mais o histograma
completo por setor (`frac_novo_setor_00`...`frac_novo_setor_15`), fração dos
pixels novos do período em cada setor — é o dado que o app precisa para
desenhar a rosa, não só o resumo escalar. Fonte por período: WSF até 2015,
classificação própria em 2015->2020 e 2020->2025 (mesma regra de ADR 0008).
Direção é declarada robusta à comissão (mesmo raciocínio da tipologia).

### Fragmentação (`pylandstats` 3.1.0)

`n_manchas`, `area_media_manchas_km2`, `largest_patch_index_pct`,
`densidade_borda_m_ha`, `indice_forma_medio`, por camada (`urbano`,
`industrial`, `reassentamento`) e ano-âncora, landscape binário res=30 m,
vizinhança 8-conexa (padrão do pacote). Roda sobre a classificação própria —
único produto com as três camadas separadas — logo **sensível à comissão**:
comissão tende a inflar `n_manchas`/`densidade_borda` e a deprimir
`area_media_manchas_km2`/`largest_patch_index_pct` (sal-e-pimenta residual
mesmo após o filtro de coerência 3x3 da classificação); direção do viés
declarada, magnitude não.

### Densidade de edificações e regularidade da malha (§5.2 item 5)

**Fonte obtida**: Google Open Buildings v3, nível A, acesso anônimo
confirmado nesta rodada — `pipeline/00_fetch/fetch_open_buildings.py`
(idempotente, streaming do bloco S2-nível-4 `193` que cobre a AOI, ~1 GB
original, filtrado linha a linha pelo bbox de `config/study.yaml`, nunca
gravado inteiro em disco). Resultado: 268.942 edificações dentro da AOI em
`data/raw/open_buildings_v3_aoi.csv` (66.894.584 bytes), hash em
`open_buildings_v3_aoi.csv.sha256` (`d4085d...` — ver `.meta.json` para o
valor completo e `size_bytes` medido), confiança mínima observada no recorte
0,65 (mesmo piso recomendado pelo produtor para esta versão).

**O que foi calculado**: `pipeline/02_metrics/edificacoes.py` atribui cada
edificação ao ponto-sede mais próximo (mesma partição de Voronoi das outras
métricas) e reporta, por unidade: `n_edificacoes`,
`densidade_edificacoes_km2` (denominador = área construída da classificação
própria, ano 2020, com a mesma ressalva de comissão da série de decomposição),
`area_media_edificacao_m2`, `regularidade_tamanho_cv` (coeficiente de
variação da área das edificações) e `regularidade_espacamento_cv`
(coeficiente de variação da distância ao vizinho mais próximo). CV baixo em
tamanho e espaçamento é lido como proxy de malha planejada/formal; CV alto,
como proxy de crescimento espontâneo/informal — leitura indireta, não uma
classificação formal/informal validada em campo. Todas as linhas usam
`ano=2023` como aproximação do epoch de aquisição da imagem (Google não
publica data de captura por edifício nesta AOI) e não constituem série
temporal.

**O que NÃO foi calculado, e por quê**: a tarefa pede "densidade de
edificações e regularidade da malha (Open Buildings **+ OSM**)". Este
repositório não tem um extrator de rede viária OSM — o único script OSM
existente (`fetch_osm_reassentamentos.sh`) resolve pontos-sede de povoados de
reassentamento, não vias. Construir e validar um fetch de malha viária (Overpass
ou extrato .pbf) está fora do escopo desta entrega; simular esse componente
sem dado real violaria a proibição de inventar disponibilidade. A regularidade
publicada é, portanto, um **proxy parcial**, só de geometria de edificação —
declarado em `nota` de cada linha, não escondido.

### Selos e nível de fonte

Toda linha de `forma_urbana` tem selo `observado` (WSF, classificação própria
e Open Buildings são todos produtos de detecção sobre imagem, não projeção) e
`nivel_fonte=A`. Nenhuma linha é `modelado` nesta família — se uma extensão
futura extrapolar tendência para anos sem imagem, o selo muda ali, não aqui.

### Sensibilidade à cobertura de observações de 2010 (SLC-off)

2010 usa Landsat 7 SLC-off (`docs/ADR/0005`): 26,64% dos pixels da AOI têm
menos de 4 observações válidas no composto de estação seca
(`data/interim/slc_off_2010_cobertura.csv`). Toda linha derivada da
classificação própria de 2010, ou de um período que usa 2010 como início ou
fim (fragmentação 2010; tipologia/rosa 2005->2010 e 2010->2015; decomposição
de área por camada em 2010), carrega essa nota no CSV — cobertura desigual
pode inflar heterogeneidade espacial espúria (mais manchas, mais densidade de
borda, tipologia mais "recortada") independentemente da comissão do
classificador. As linhas de **tendência (WSF)** não são afetadas porque não
dependem do composto próprio.

### Restrições herdadas propagadas

- **Nenhuma cava de mina conta como `urbano`**: a camada `industrial` é
  exclusiva e a série do WSF exclui explicitamente o polígono de mineração
  (Maus et al. 2022) + 150 m de guarda antes de atribuir pixels a
  tete/moatize/cateme/mwaladzi (`_common.mascara_exclusao_industrial`).
- **"25 de Setembro" (`geometry: null`)**: toda linha de `moatize` que soma
  pixels ou edificações de `urbano`/`assentamento_wsf`/`edificacoes` carrega a
  nota de que a magnitude do reassentamento embutido não é estimável —
  propagada em `area_cagr.py`, `write_stats_forma_urbana.py` e
  `edificacoes.py`.

### Suficiência para §1

- **Pergunta 4 (forma de urbanização — compacta/dispersa, infill/borda/
  leapfrog, eixos)**: respondível em nível A para 2000-2015 (WSF) e
  parcialmente para 2015-2025 (classificação própria, com a ressalva de
  comissão). Direção e tipologia são as métricas mais robustas desta
  entrega.
- **Pergunta 4 (formal vs. informal)**: só parcialmente respondível — o proxy
  de regularidade cobre um epoch único (~2023) e não tem o componente de
  malha viária OSM; não permite comparar formal/informal ao longo do tempo,
  só descrever o padrão atual.
<!-- SECAO_METRICAS_FASE2_FIM -->

---

## RESSALVA DE CHURN — acrescentada em 2026-09-08 (`docs/ADR/0013`)

O bloco "Duas séries, dois papéis" acima atribui a robustez da **direção de expansão** e da
**tipologia infill/borda/leapfrog** apenas ao viés de comissão de `docs/ADR/0009`. **Faltava
a ressalva mais séria.**

`docs/ADR/0013` mediu, para a camada `urbano`, um **churn de identidade pixel a pixel de 31 a
54 %** entre anos-âncora consecutivos. A leitura correta é: **a área é utilizável; a
localização não.**

Isso atinge, nominalmente, toda métrica que dependa de **qual** pixel mudou:

| métrica | efeito |
|---|---|
| tipologia infill / borda / leapfrog | a classificação de um pixel novo como infill ou leapfrog depende de onde estava a mancha no ano anterior — e até 54 % dos pixels da mancha anterior não são os mesmos |
| matriz de transição entre classes | idem: a transição é definida pelo par de rótulos do mesmo pixel em dois anos |
| rosa de expansão | menos afetada: agrega por setor angular, e o churn é aproximadamente isotrópico dentro do setor |
| área, CAGR, fragmentação agregada | não afetadas por churn de identidade, apenas pela comissão de `docs/ADR/0009` |

**Consequência prática:** nenhuma proporção de tipologia deste fragmento sustenta afirmação
sobre *onde* a cidade cresceu num par de anos específico. O que resta defensável é a
**tendência agregada** ao longo da série inteira, e ainda assim com a comissão declarada.

Contrato que impede a reincidência:
`pipeline/tests/test_coerencia_hipoteses.py::test_metricas_por_pixel_carregam_a_ressalva_de_churn`.
