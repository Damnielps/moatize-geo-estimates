# data/DATA_DICTIONARY.md

Dicionário de dados dos artefatos de `data/processed/`. Cada família (§5.2, §5.3, §5.6…)
adiciona sua seção; **não sobrescreva outra seção ao editar** — acrescente a sua.
Convenção: colunas comuns em tabela "long" (uma linha = um número), documentadas uma vez;
o catálogo de `variavel` é documentado por família.

Toda série carrega **selo** `observado` / `interpolado` / `modelado` — nenhuma exceção
(§10). Série sem selo é reprovada.

---

<!-- SECAO_DEMOGRAFIA_FASE2_INICIO -->
## §5.3 — Reconstrução demográfica (Fase 2)

Gerado por `pipeline/02_metrics/reconstrucao_demografica.py`.

### `data/processed/stats_by_year_by_unit.csv` — núcleo A, formato longo

Uma linha = um número. Filtrar por `familia == "demografia"` para esta seção; outras
famílias (§5.2, §5.6) acrescentam linhas com `familia` diferente, mesmo esquema de coluna.

| coluna | tipo | descrição |
|---|---|---|
| `familia` | string | módulo que produziu a linha (`demografia` para esta seção) |
| `unidade_geografica` | string | `"Cidade de Tete"` ou `"Distrito de Moatize"` (unidades ADM2 do INE/COD-PS; ver CLAUDE.md §3 sobre a ausência de subdivisão oficial em postos para a Cidade de Tete) |
| `ano` | int | ano-âncora do valor |
| `variavel` | string | ver catálogo abaixo |
| `valor` | float/int | valor numérico; unidade em `unidade_medida` |
| `unidade_medida` | string | `pessoas`, `%/ano` |
| `selo` | string | `observado` \| `interpolado` \| `modelado` — **obrigatório, sem exceção** |
| `nivel_fonte` | string | `A` (política de dados abertos, §4.0) — só nível A entra neste arquivo |
| `fonte` | string | citação + caminho do arquivo em `data/raw/` |
| `metodo` | string | como o número foi obtido/calculado |
| `nota` | string | ressalvas necessárias para interpretar o número (subenumeração, risco de circularidade, etc.) |

**Catálogo de `variavel` (família demografia):**

| variavel | significado | anos disponíveis |
|---|---|---|
| `populacao_total_residente` | população residente total, contagem/projeção INE, **não ajustada** pela subenumeração do Censo 2017. São duas taxas de unidades diferentes, não uma faixa: 3,7% no total nacional e 3,8% na Província de Tete. `censo_2017.subenumeracao_pct` em `config/study.yaml` guarda a **nacional (3,7%)**, aplicada de forma consistente também aos controles, que estão noutras províncias; nenhum valor publicado é ajustado por qualquer das duas | 2017 (observado), 2025 (modelado) |
| `populacao_homens` / `populacao_mulheres` | mesma fonte, por sexo | 2017, 2025 |
| `cagr_2017_2025` | taxa de crescimento anual composta entre os dois únicos pontos de nível A: `(pop2025/pop2017)^(1/8) - 1`, em %/ano | 2025 (rótulo do ponto final) |

**Por que não há linhas para 1997/2007 nem para 2018-2024:** ver
`data/processed/demografia_contexto_nao_nucleo.csv` (1997/2007, nível B/C, fora do
núcleo) e a docstring de `pipeline/02_metrics/reconstrucao_demografica.py` (nenhuma
interpolação entre 2017 e 2025 — dois pontos não são série).

### `data/processed/demografia_contexto_nao_nucleo.csv` — fora do núcleo, nunca citável em número publicado

Mesmo tipo de conteúdo que o núcleo, mas nível B ou C (ou fonte não recuperada). Colunas:
`unidade_geografica`, `ano`, `variavel`, `valor` (pode ser vazio/`None` quando não
recuperado), `unidade_medida`, `selo`, `nivel_fonte` (`B`, `C` ou `ausente`), `fonte`,
`metodo`, `motivo_nao_nucleo`. Uso permitido: validação cruzada rotulada e discussão
metodológica no artigo/app, sempre com o selo de nível visível. **Nunca** entra em
tabela de resultados nem sustenta afirmação quantitativa isolada (§4.0 regra "B").

### `data/processed/populacao_dasimetrica_sensibilidade.csv` — teste de sensibilidade da dasimetria 2017 (só Cidade de Tete)

Distribui os 307.338 habitantes de 2017 pela mancha construída, com três pesos
alternativos, para quantificar o efeito da escolha de peso sobre a densidade implicada
(exigência da Fase 2: "quantifique o efeito").

| coluna | tipo | descrição |
|---|---|---|
| `metodo_peso` | string | `classificacao_propria` (urbano ∪ reassentamento, própria do pipeline, média 2015/2020) \| `ghsl_built_s` (fração construída GHSL BUILT-S R2023A, média 2015/2020) \| `wsf_evolution` (máscara de detecção WSF Evolution ≤2015) \| `correlacao_own_x_ghsl_no_cluster` (linha de diagnóstico) |
| `aplicavel` | bool | `False` se o raster de peso não estava disponível |
| `populacao_total_distribuida` | int | sempre 307.338 pessoas — igual por construção em qualquer peso; o que muda é a área |
| `area_construida_ponderada_km2` | float | soma dos pesos (0-1 por pixel) × área do pixel, só nos pixels atribuídos ao cluster de Tete |
| `densidade_implicada_hab_km2` | float | `populacao_total_distribuida / area_construida_ponderada_km2` — varia **~2,7×** entre os três pesos nesta AOI (7.724-20.932 hab/km²), evidenciando que a comissão de 0,27-0,63 medida em `docs/ADR/0009` desloca materialmente a densidade implícita |
| `correlacao_pearson` | float | (só na linha de diagnóstico) correlação pixel a pixel entre peso próprio e peso GHSL dentro do cluster de Tete |
| `selo` | string | `modelado` em toda linha aplicável |
| `nivel_fonte` | string | `A` |

**Partição espacial Tete × Moatize:** não há polígono administrativo com geometria em
nível A disponível no repositório (HDX COD-AB entrega atributos tabulares — área,
nome — mas não a geometria em formato lido nesta rodada). A partição usa vizinho mais
próximo por pixel a dois pontos de referência já verificados em
`docs/ADR/0001-aoi-final.md`: Cidade de Tete (33,5871E/16,1604S) e Vila de Moatize
(33,7288E/16,1178S). Isto aproxima, não reproduz, o limite administrativo — declarado
como limitação, não corrigido silenciosamente.

**Discrepância de área administrativa registrada, não resolvida:** o atributo
`area_sqkm` do HDX COD-AB para "Cidade de Tete" é 287,27 km², quase o dobro da âncora de
§8 do CLAUDE.md (~149 km², fonte Wikipedia, não nível A). Não investigado nesta rodada;
relevante para quem calcular densidade populacional por área administrativa (§5.2) — usar
a fonte nível A (COD-AB) e citar a divergência, não silenciá-la.

### `data/processed/imagery/populacao_dasimetrica_tete_2017_30m_32736.tif`

Raster GeoTIFF, EPSG:32736, 30 m, float32. Cada célula = pessoas estimadas naquela célula
em 2017, população dasimétrica de Cidade de Tete usando peso `classificacao_propria`
(escolhido como produto principal por estar disponível em todos os anos-âncora do
pipeline, não só 2015/2020). Soma de todas as células = 307.338 (por construção). Selo
`modelado`. Ver `.tif.meta.json` companheiro para proveniência completa e a advertência de
incerteza (herda a acurácia do usuário de `docs/ADR/0009`).

### Domicílios — não produzido

Ver `docs/ADR/0010-domicilios-sem-fonte-a.md`: tamanho médio do domicílio para
Tete/Moatize não tem fonte de nível A (nem B confirmada); um produto "edificações ×
tamanho médio" herdaria esse nível C e não poderia sustentar número publicado. Não
construído; Open Buildings/Microsoft Footprints não baixados por esse motivo.

### Projeções 2027-2040 — não produzidas

Ver docstring de `pipeline/02_metrics/reconstrucao_demografica.py`, seção "Projeções":
dois pontos (2017 observado, 2025 já modelado pelo INE) não sustentam uma projeção
própria sem herdar/compor a premissa de crescimento geométrico já embutida no ponto de
2025. Requer Censo 2027 ou parâmetros de fecundidade/mortalidade/migração em nível A,
não disponíveis.
<!-- SECAO_DEMOGRAFIA_FASE2_FIM -->

---

<!-- SECAO_FORMA_URBANA_FASE2_INICIO -->
## §5.2 — Forma urbana (Fase 2)

Gerado por `pipeline/02_metrics/area_cagr.py`, `fragmentacao.py`,
`tipologia_expansao.py`, `edificacoes.py`, consolidados por
`write_stats_forma_urbana.py` em `data/interim/stats_forma_urbana.csv` e daí em
`data/processed/stats_by_year_by_unit.csv` (`familia == "forma_urbana"`, mesmo
esquema de coluna descrito na seção de demografia acima).

`unidade_geografica` nesta família usa os rótulos internos do pipeline, não os
nomes administrativos completos: `tete`, `moatize`, `cateme`, `mwaladzi`
(pontos-sede, partição de Voronoi — ver docstring de `pipeline/02_metrics/_common.py`)
e `aoi` (só nas métricas de fragmentação por camada inteira, sem split espacial).
`unidade_geografica == "industrial"` aparece nas linhas de área por camada da
classificação própria (a pegada industrial não é dividida entre núcleos).

**Duas séries no mesmo arquivo, não intercambiáveis (ADR 0008):**
- linhas com `fonte` citando "WSF Evolution" → série de TENDÊNCIA, área e CAGR,
  1985-2015, `confiavel_para_tendencia` implícito na nota "Robusta à comissão...".
- linhas com `fonte` citando "Classificação própria" ou "pylandstats" → série de
  DECOMPOSIÇÃO por camada, 6 anos-âncora, sempre com nota "Sensível à comissão
  do mapa (ADR 0009, acurácia do usuário do construído = 0,27-0,63)".

### Catálogo de `variavel`

| padrão de `variavel` | significado | unidade_medida | fonte típica |
|---|---|---|---|
| `area_km2_assentamento_wsf` | área cumulativa do WSF Evolution (pixels com ano de detecção <= ano-âncora), menos pegada industrial | km2 | WSF Evolution |
| `area_km2_urbano` / `_industrial` / `_reassentamento` | área da camada classificada, no ano-âncora | km2 | classificação própria |
| `cagr_pct_ano_desde_<ano0>_assentamento_wsf` | CAGR entre `<ano0>` e o ano da linha, série WSF | %/ano | WSF Evolution |
| `prop_infill_desde_<ano0>` / `prop_borda_desde_<ano0>` / `prop_leapfrog_desde_<ano0>` | proporção de pixels novos no período `<ano0>`→ano da linha classificados por densidade de vizinhança (raio 90 m; infill >=0,50, leapfrog =0) | fração dos pixels novos | WSF até 2015; classificação própria em 2015→2020 e 2020→2025 |
| `direcao_expansao_graus_desde_<ano0>` | direção resultante (Rayleigh) do vetor centróide-do-construído-em-t0 → pixel novo, 0°=Norte, sentido horário | graus | idem |
| `concentracao_direcional_r_desde_<ano0>` | razão de concentração de Rayleigh (0=disperso, 1=um só rumo) | adimensional 0-1 | idem |
| `frac_novo_setor_NN_desde_<ano0>` (NN=00..15) | fração dos pixels novos do período no setor `NN` (`[NN*22,5°, (NN+1)*22,5°)` a partir do Norte, horário) — série completa para desenhar a rosa | fração dos pixels novos | idem |
| `n_manchas_<camada>` | número de manchas (`pylandstats.number_of_patches`), landscape binário da camada | contagem | classificação própria + pylandstats |
| `area_media_manchas_km2_<camada>` | área média de mancha (`area_mn`, convertida de ha) | km2 | idem |
| `largest_patch_index_pct_<camada>` | maior mancha como % da paisagem | % | idem |
| `densidade_borda_m_ha_<camada>` | densidade de borda (`edge_density`) | m/ha | idem |
| `indice_forma_medio_<camada>` | índice de forma médio (`shape_index_mn`, 1=mais compacto) | adimensional | idem |
| `n_edificacoes` | contagem de edificações Open Buildings v3 atribuídas à unidade | contagem | Open Buildings v3 |
| `densidade_edificacoes_km2` | `n_edificacoes` / área construída (classificação própria, ano 2020) | edificações/km2 | Open Buildings v3 + classificação própria |
| `area_media_edificacao_m2` | média de `area_in_meters` das edificações da unidade | m2 | Open Buildings v3 |
| `regularidade_tamanho_cv` | coeficiente de variação da área das edificações — proxy de malha planejada (baixo) vs. espontânea (alto) | adimensional (CV) | Open Buildings v3 |
| `dist_media_vizinho_mais_proximo_m` | distância média ao vizinho mais próximo entre edificações | m | Open Buildings v3 |
| `regularidade_espacamento_cv` | CV da distância ao vizinho mais próximo — proxy parcial de regularidade da malha (só geometria de edificação, sem componente OSM — ver nota abaixo) | adimensional (CV) | Open Buildings v3 |

Todas as linhas de `n_edificacoes` até `regularidade_espacamento_cv` usam
`ano = 2023` como aproximação do epoch de aquisição do Open Buildings v3 nesta
AOI (não há data de captura por edifício publicada) e **não são série
temporal** — comparáveis só nesse ano.

### Densidade de edificações e regularidade da malha — proxy parcial, declarado

A tarefa original pede "Open Buildings **+ OSM**". Este repositório não tem
um extrator de rede viária OSM (`pipeline/00_fetch/fetch_osm_reassentamentos.sh`
resolve só os pontos-sede dos povoados de reassentamento). A regularidade
publicada aqui usa exclusivamente geometria de edificação (tamanho e
espaçamento) — é um proxy parcial, não simulado, com a lacuna declarada em
cada linha (`nota` menciona explicitamente a ausência do componente OSM).

### Robustez à comissão (ADR 0009) e à cobertura de 2010 (ADR 0005)

Toda linha do CSV tem, na coluna `nota`, uma sentença explícita de
robustez/sensibilidade à comissão de 0,27-0,63 medida na Fase 1. Direção de
expansão, tipologia (infill/borda/leapfrog) e toda a série WSF são declaradas
robustas; área/densidade/fragmentação da classificação própria e a
densidade de edificações (cujo denominador vem da classificação própria) são
declaradas sensíveis. Toda linha derivada de 2010, ou de um período que usa
2010 como ponta, carrega adicionalmente a nota de cobertura SLC-off (26,64%
dos pixels da AOI com menos de 4 observações válidas,
`data/interim/slc_off_2010_cobertura.csv`).

### Restrições propagadas

- Nenhuma cava de mina entra como `urbano`: a série WSF exclui o polígono de
  mineração (Maus et al. 2022) + 150 m de guarda antes de atribuir pixels às
  unidades; `industrial` é camada própria, nunca somada a `tete`/`moatize`.
- "25 de Setembro" (`geometry: null`): toda linha de `moatize` derivada de
  `urbano`, `assentamento_wsf` ou edificações carrega a nota de que a
  magnitude do reassentamento embutido não é separável do crescimento
  orgânico com os dados disponíveis.

### Intensidade de uso (área/população) — não calculada

Sem série de população compatível com o polígono de núcleo urbano usado em
§5.2 (ver seção de demografia acima). Pendência registrada, não simulada.
<!-- SECAO_FORMA_URBANA_FASE2_FIM -->

---

<!-- SECAO_DEMOGRAFIA_DASHBOARD_INICIO -->
## §5.3 — Dashboard de população 1997-2025 (Frente A)

Gerado por `pipeline/02_metrics/demografia_dashboard.py`.

### `data/processed/demografia_serie_1997_2025.csv` — uma linha por unidade × ano/intervalo

**Não entra em `stats_by_year_by_unit.csv`**: grava direto em `data/processed/`, fora do
circuito `data/interim/stats_*.csv` → `stats_by_year_by_unit.py`. O consolidador do
núcleo continua reprovando nível B/C — este produto existe justamente para carregar B, C
e `ausente` lado a lado com A, cada linha com o seu nível explícito, para o dashboard do
app comparar Cidade de Tete e Distrito de Moatize com Província de Tete e Moçambique.

| coluna | tipo | descrição |
|---|---|---|
| `familia` | string | sempre `demografia` |
| `unidade_geografica` | string | `Cidade de Tete`, `Distrito de Moatize`, `Província de Tete`, `Moçambique` (Vila de Moatize fica fora desta invocação — ver WorldPop, coleta paralela) |
| `ano` | int | 1997, 2007, 2017 ou 2025 |
| `variavel` | string | `populacao_total_residente`; `cagr_<a>_<b>` (CAGR do intervalo `a`→`b`, publicado no ano `b`); `indice_base_<ano>` (índice, base=100 no primeiro ano disponível da unidade) |
| `valor` | float | vazio quando a unidade não tem valor para o ano (ex.: Distrito de Moatize, 1997) |
| `unidade_medida` | string | `pessoas`, `%/ano`, `índice (base=100)` |
| `selo` | string | `observado` \| `modelado` — **obrigatório**; `modelado` sempre que o ano ou uma das pontas do intervalo/índice for 2025 (projeção institucional do INE) |
| `nivel_fonte` | string | `A`, `B`, `C` ou `ausente`. Para `cagr_*`/`indice_base_*`: pior nível das duas pontas (A<B<C<ausente) |
| `fonte` | string | citação + caminho em `data/raw/`; nenhuma linha de nível A cita o INE diretamente — só HDX COD-PS (contrato `test_dashboard_nenhuma_linha_a_cita_ine_diretamente_na_fonte`) |
| `metodo` | string | como o número foi obtido/calculado |
| `nota` | string | ressalvas (subenumeração, circularidade da projeção 2025, mudança de limite administrativo, motivo de ausência) |
| `comparabilidade` | string | `"ok"` \| `"limites do distrito mudaram entre censos — não garantida"` (todo ano de Distrito de Moatize) \| `"projeção INE"` (todo ano 2025) |

**Origem de cada ponto:**

- Cidade de Tete e Distrito de Moatize, 2017/2025 (A): reaproveitados de
  `reconstrucao_demografica.montar_nucleo()`, sem retranscrição.
- Cidade de Tete e Distrito de Moatize, 1997/2007 (B/C/`ausente`): reaproveitados de
  `reconstrucao_demografica.montar_contexto_b_c()`.
- Província de Tete e Moçambique, 2017/2025 (A): soma dos `T_TL` de todos os ADM2 do HDX
  COD-PS **por nome de província** (`ADM1_PT`), nunca por P-code — o P-code `MZ10` do
  COD-PS resolve para outra entidade no COD-AB (ver `config/unidades.yaml`).
- Província de Tete e Moçambique, 2007 (C): parse programático de
  `data/raw/censo2007-tete-quadro3-populacao-por-idade-distrito-2007.html` (linha
  `T O T A L` da província; rodapé `POP_Total(2007)` para o total nacional) — nenhum
  valor transcrito à mão.

**Total nacional = soma do COD-PS, não o total "ajustado" do INE** (decisão do usuário,
2026-09-09): a soma dos ADM2 de 2017 (26.899.102) diverge da "população residente a 1 de
agosto de 2017" publicada pelo INE (26.899.105) em poucas unidades — a divergência é
calculada em tempo de execução e gravada na `nota` da linha, nunca digitada. A soma
provincial de 2017 (2.551.824) confere com o total do INE (2.551.826) dentro de ±5.

**Unidades novas em `config/unidades.yaml`:** `provincia_tete` e `mocambique`,
`comparavel_entre_familias: false` — servem só a este dashboard de população, não a
forma urbana nem agricultura.
<!-- SECAO_DEMOGRAFIA_DASHBOARD_FIM -->
