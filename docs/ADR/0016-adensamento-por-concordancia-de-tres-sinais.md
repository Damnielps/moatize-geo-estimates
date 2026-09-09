# ADR 0016 — Adensamento 2020–2025 por concordância de três sinais, em postos e em grade agregada

- **Data:** 2026-09-09
- **Fase:** 4 (reapresentação descritiva), camada nova
- **Decidido por:** usuário (redefinição de objetivo em 2026-09-09), sobre desenho do
  orquestrador; redação do método pelo subagente de desenho causal (§5.4/§5.6)
- **Estado:** aceito — **escrito antes do código**. Os valores realizados dos cortes e as
  razões de sensibilidade entram como emenda datada após a primeira execução.
- **Contexto obrigatório:** `docs/ADR/0009` (acurácia de classe rara), `0011` (limiar
  relativo à paisagem), `0013` (estabilidade temporal e catraca R2), `0014` (limiar
  relativo propagado; R2 removida de `industrial` e `reassentamento`)
- **Artefatos previstos:** `pipeline/02_metrics/adensamento.py`;
  `data/processed/imagery/adensamento_2020_2025_{240m,30m}_32736.tif` (+ `.meta.json`);
  `data/processed/imagery/adensamento_2020_2025.geojson`;
  `data/processed/adensamento_2020_2025_por_unidade.csv`;
  `data/processed/adensamento_sensibilidade.csv`; `pipeline/tests/test_adensamento.py`

---

## Contexto

O objetivo do estudo foi redefinido pelo usuário: **não** se busca mais estabelecer relação
causal entre mineração e urbanização; busca-se **mapear descritivamente** o processo de
urbanização de Tete e Moatize entre 1997 e 2025. A Fase 3 permanece íntegra e passa a
delimitar o que o mapeamento **não** pode afirmar. Esta camada é o primeiro produto sob o
novo objetivo, e responde a uma pergunta descritiva: **onde, entre 2020 e 2025, houve
processo de adensamento urbano e periurbano** — áreas ainda não plenamente ocupadas, mas
em intensificação.

Quatro fatos medidos governam o desenho. Nenhum deles é hipótese.

**1. A catraca R2 não infla o incremento 2020→2025 — ela o censura por baixo.**
`aplicar_regras_temporais()` (`pipeline/01_imagery/classificacao.py:703–730`) faz união
cumulativa, logo `construido_2025 ⊇ construido_2020` por construção. Verificado: **0 pixels
de 2020 ausentes em 2025**. O incremento é, portanto, exatamente o conjunto das primeiras
detecções de 2025 — **6.701 pixels = 6,03 km²** — e os 18,0 % de estoque herdado da união em
2025 (`docs/ADR/0013`, tabela 1) já estão dentro de 2020 e **cancelam na diferença**. O custo
real não é inflação: é que o sinal **só pode subir**. Daí a decisão, em §Decisão-7, de não
criar classe de esvaziamento.

**2. Os dois mapas que entram na diferença têm qualidade muito desigual.**
`data/processed/acuracia_por_ano.csv`: 2020 tem acurácia do usuário 0,476, do produtor
**0,055** e **kappa 0,073**; 2025 tem 0,625 / 1,000 e kappa 0,766. Uma diferença de níveis
entre um mapa quase sem informação e um mapa razoável mede sobretudo a mudança de
qualidade do mapa. É a razão de existir do princípio de postos (§Decisão-1).

**3. A identidade pixel a pixel não sobrevive entre anos.** Churn 2020–2025 = **0,310**,
Jaccard = **0,690** (`data/processed/causal/estabilidade_temporal_camadas.csv`). `docs/ADR/0013`
já concluiu que qualquer detecção de mudança tem de operar em **grade agregada**, nunca em
pixel. Além disso, **R1 não é aplicável em 2025** — não há ano-âncora seguinte, e todo ganho
de 2025 entra **sem confirmação**.

**4. O defeito do limiar absoluto reincidiu sete vezes nesta linha de trabalho**
(`docs/ADR/0011`, `0013`, `0014`). Esta seria a oitava oportunidade. O desenho abaixo o
impede **por construção**, não por disciplina (§Decisão-2 e contrato T5).

---

## Decisão

### 1. Comparar **postos**, não níveis

Todo sinal com série é convertido, **dentro de cada ano**, à sua posição na ECDF empírica da
AOI daquele ano (`scipy.stats.rankdata(method="average")`, normalizado a [0,1]); só depois se
toma a diferença entre anos.

Justificativa: um viés que desloca **monotonicamente** o mapa inteiro de um ano — comissão
generalizada em 2020, recalibração de sensor, mudança de ganho na série de luz — desloca
todos os postos na mesma direção e **cancela na diferença de postos**, ao passo que
sobreviveria integralmente a uma diferença de níveis. É a mesma família de correção que
`docs/ADR/0011` e `0014` adotaram para limiares: **estatística relativa à paisagem do próprio
ano**, aqui aplicada não ao corte, mas ao próprio sinal.

O que o posto **não** conserta, e fica declarado como risco R1: erro **espacialmente
estruturado** (comissão concentrada em solo exposto de borda, por exemplo) reordena as
células e sobrevive à transformação.

### 2. Todo limiar é **quantil**, nenhum é valor físico

Nenhum corte deste método é um número absoluto de fração construída, de radiância, de área de
telhado ou de metros. Todos são **probabilidades** fixadas a priori, cujos **valores
realizados** são calculados na execução, gravados no `.meta.json` e só então transcritos aqui.

| símbolo | probabilidade | papel | valor realizado |
|---|---|---|---|
| `TAU` | **0,70** | corte de voto de cada sinal `S_i` | `<PLACEHOLDER: após primeira execução — três valores, um por sinal>` |
| `Q_ALTO` | **0,80** | piso de `consolidado` sobre `f_2020` | `<PLACEHOLDER: após primeira execução>` |
| `Q_BAIXO` | **0,20** | piso de ocupação para `expansao_nova`/`vazio_estavel` | `<PLACEHOLDER: após primeira execução>` |
| `Q_INDUSTRIAL` | **0,50** | corte de `fracao_industrial` nas células industriais | `<PLACEHOLDER: após primeira execução>` |

Por que o desenho impede o defeito **por construção**, e não por cuidado do autor:

- os quantis são calculados sobre a **distribuição do próprio ano e do próprio sinal**, de
  modo que um deslocamento de nível não move a fração selecionada;
- a partição de classes é **exaustiva por precedência** (§Decisão-5): não existe "resto"
  definido por um número solto;
- os únicos literais numéricos permitidos no código são estruturais, não de calibração:
  `0`/`1` de sinal, `8`/`64`/`16` de geometria de grade, `1000`/`3000` lidos de
  `config/study.yaml`, e os códigos inteiros de classe;
- o **contrato T5** varre a árvore sintática (AST) do script: toda variável cujo nome case
  `LIMIAR|CORTE|Q_|TAU` tem de ser atribuída por `np.quantile` ou por mediana, e todo
  `ast.Compare` com literal numérico à direita reprova salvo se o literal estiver na lista
  branca declarada acima. O defeito passa a ser **detectável por máquina**, que é a única
  forma de não ser a nona ocorrência.

Consequência aceita: os cortes são **relativos à paisagem**, portanto a área de cada classe
não é comparável a outra AOI nem a outro período sem recalcular os quantis. Isso está escrito
na legenda.

### 3. Grade de **240 m = 8 × 8 pixels de 30 m**

A grade canônica é `(1299, 2144)` a 30 m. `2144 / 8 = 268` exato; `1299 / 8 = 162,375`, logo
**162 linhas completas × 268 colunas = 43.416 células** de 0,0576 km², somando **2.500,76 km²**
de domínio. As **268 células parciais da borda sul** (3 linhas de pixels, **5,79 km²**, 0,23 %
dos 2.506,55 km² da AOI) saem do domínio pelo critério `n_pixels_30m == 64` e recebem a classe
`fora_de_dominio`. A variante de sensibilidade a 480 m é agregação **2 × 2 estrita** sobre a
mesma grade — mudança de escala, nunca regradeamento.

250 m foi rejeitado (ver Alternativas, (f)): `250 / 30 = 8,33`, o que exigiria reamostragem e
introduziria mistura de pixels na fronteira de cada célula — ruído artificial numa camada cuja
pergunta inteira é sobre fração de ocupação por célula.

### 4. Os três sinais

- **S1 — ganho de fração construída.** `f_t(c) = |urbano_t ∪ reassentamento_t em c| / 64`,
  com `industrial` **fora** (§10: nenhuma cava contada como área urbana).
  `S1 = ECDF_2025(f) − ECDF_2020(f)`, com a ECDF calculada sobre as células ocupadas em pelo
  menos um dos anos. `reassentamento` não tem R2 desde `docs/ADR/0014` e **pode cair** — e o
  desenho quer que possa, porque abandono e adensamento de povoado são a pergunta 3 de §1.
- **S2 — tendência de luz noturna.** Seis anos, 2020–2025, da série Chen/Yu (NPP-VIIRS-like,
  nível A, ~500 m), reprojetada bilinear a 30 m e mediada por célula; **posto dentro de cada
  ano**; inclinação por **Theil–Sen exato** (mediana das 15 inclinações par a par) —
  determinística, sem seed, robusta a um ano anômalo. Ressalva vinculante: **luz é proxy de
  atividade, não de população**, e o mandato de §5.4 já alerta para a causalidade reversa
  entre luz e população. Por isso a luz **nunca decide sozinha** (§Decisão-5).
- **S3 — resíduo de estado de edificações.** Open Buildings v3, epoch único ~2023, sem série:
  `fp(c) = Σ area_in_meters / 57.600`; `S3 = ECDF_OB(fp) − ECDF_2020(f)`. Lê-se: *a célula tem,
  em ~2023, mais edificação do que a sua posição de 2020 previa*. A janela real é
  **2020 → ~2023**, não 2020→2025, e isso vai escrito em toda saída. Sem filtro absoluto de
  confiança — `edificacoes.py` usa `confidence ≥ 0,65`, que é um limiar absoluto herdado do
  produtor; aqui a variante de sensibilidade usa `confidence ≥ quantil 0,50` do próprio
  recorte, coerente com §Decisão-2.

### 5. Concordância ≥ 2 de 3

`V_i = dominio_ocupado ∧ (S_i > 0) ∧ (S_i ≥ np.quantile(S_i[dominio_ocupado], TAU))`, com
`TAU = 0,70`; **`adensando ⇔ Σ V_i ≥ 2`**.

O corte é um quantil da ECDF calculada **sobre `dominio_ocupado`** (célula do domínio, ocupada
em pelo menos um dos dois anos — a mesma referência usada para os postos de S1 e S3, §4).
`V_i` herda essa restrição explicitamente, não só por transitividade do valor de `S_i`: uma
célula fora de `dominio_ocupado` não tem posição na distribuição de referência (§ver
`posto_ecdf` em `pipeline/02_metrics/_common.py`), então perguntar se ela ultrapassa um quantil
dessa distribuição não tem significado — um posto avaliado fora da população que o define não
é comparável ao corte. Célula **nunca ocupada** (`f_2020 = f_2025 = 0`, típica de
`pegada_industrial` com `dominio_ocupado = False`) fica com `S1 = S3 = 0` por construção de
`posto_ecdf` (retorna 0 fora da referência) e, portanto, `V1 = V3 = False` mesmo que o valor
numérico de `S_i` isolado pareça alto — o voto é sobre pertencer à população avaliada, não só
sobre o sinal cruzar o corte. Nesta camada essas células caem em `pegada_industrial` por
precedência de classe (regra 6, código 6 antes de código 3), então a classificação final não
muda; o que muda é que `concordancia = 0` publicado nelas é reproduzível a partir de `S1/S2/S3`
e de `quantis_realizados` sem reimplementar o pipeline — ver o contrato T13
(`pipeline/tests/test_adensamento.py`), que recalcula `concordancia` a partir só desses
atributos publicados e exige zero divergências.

Exigir dois votos entre três sinais de naturezas diferentes — classificação espectral própria,
radiância noturna de terceiros, pegada vetorial de edificações de terceiros — é o que permite
publicar uma camada cujo insumo mais direto (S1) herda **kappa 0,073** de 2020. Nenhum sinal
isolado sustentaria a afirmação; a concordância a torna defensável como **padrão**, não como
medida. O atributo `concordancia` (0 a 3) é publicado em **toda** célula, para que o leitor
possa reconstruir outra partição a partir dos atributos.

> **Correção, 2026-09-09 (Emenda 2).** Esta seção descrevia `V_i` sem o termo
> `dominio_ocupado`, embora `pipeline/02_metrics/adensamento.py:359` sempre o tivesse aplicado.
> Medido pelo portão da Frente B: 13 feições, todas `pegada_industrial` com `f_2020 = f_2025 =
> 0` e `S3` até 0,98, publicavam `concordancia = 0` — coerente com o código, mas não
> reconstruível pela fórmula então escrita aqui, que daria `Σ V_i ≥ 1` para elas. **O código
> estava certo; o ADR estava incompleto** — é este documento que muda, não a saída publicada.

### 6. Sete classes, partição exaustiva por precedência

Primeira regra que casa vence. Todo corte é quantil.

| cód | classe | definição |
|---|---|---|
| 0 | `fora_de_dominio` | célula parcial (`n_pixels_30m < 64`) |
| 6 | `pegada_industrial` | `fracao_industrial ≥ quantil Q_INDUSTRIAL` das células industriais |
| 5 | `consolidado` | `f_2020 ≥ quantil Q_ALTO` — já pleno no início, fora da pergunta |
| 4 | `expansao_nova` | `f_2020 < quantil Q_BAIXO` **e** `f_2025 ≥ quantil Q_BAIXO` — cruza o piso |
| 3 | `adensando` | piso ≤ `f_2020` < teto **e** concordância ≥ 2 — sobe de posto |
| 2 | `esparso_estavel` | piso ≤ `f_2020` < teto, concordância ≤ 1 |
| 1 | `vazio_estavel` | abaixo do piso nos dois anos |

`expansao_nova` é **extensão** da mancha; `adensando` é **intensificação dentro** dela. As duas
são respostas distintas à pergunta do usuário e não devem ser somadas numa figura só.

### 7. O anel periurbano é **atributo**, não restrição

`distance_transform_edt(~urbano_2020, sampling=30)` em EPSG:32736, avaliada no centróide da
célula, com os limites lidos de `config/study.yaml → zoneamento_agricola.aneis_km`
(`[[0,1],[1,3]]`, **materializado pela primeira vez**): `intraurbano`, `periurbano_0_1km`,
`periurbano_1_3km`, `externo`. Publica-se também `dist_borda_urbano_2025_m`. O anel
**estratifica** o CSV; não decide classe nenhuma.

### 8. Selo **modelado**, em quatro lugares

`.meta.json`, manifesto do app, legenda da camada e tabela do artigo. Esta camada é uma
síntese de três produtos, dois deles de terceiros, sob cortes escolhidos: não é observação.
`estocasticidade: nenhuma` — nenhum passo usa seed; Theil–Sen exato e quantis são
determinísticos, o que satisfaz §Determinismo sem entrada em `config/seeds.yaml`.

### 9. Critério de publicação por sensibilidade (fixado **antes** de ver o resultado)

`data/processed/adensamento_sensibilidade.csv` traz as variantes `base`, `tau_060/080`,
`qalto_070/090`, `qbaixo_010/030`, `grade_480m`, `ob_conf_mediana`, `concordancia_3de3`,
`sem_S2`, `sem_S3` e `bruta_experimental` (S1 sobre `data/interim/estabilidade/bruta_construido_*`,
diagnóstico, não publicável). Então:

- razão de área de `adensando` entre as variantes de **±1 decil** dentro de **[0,5; 2,0]** →
  a camada é publicada **como área**;
- fora de [0,5; 2,0] mas dentro de **[0,2; 5,0]** → publica-se **apenas o padrão espacial e a
  ordem de grandeza**, nunca a área;
- fora de **[0,2; 5,0]** → a camada vira **figura de diagnóstico**, não resultado.

Razão realizada: `<PLACEHOLDER: após primeira execução — razão máxima entre variantes ±1 decil>`.
Regime resultante: `<PLACEHOLDER: após primeira execução>`.

### 10. Dois defeitos latentes que esta camada acorda

`pipeline/05_app/build_web_assets.py`: `nome_camada_ano("adensamento_2020_2025")` devolve
`('adensamento_2020', '2025')` — **verificado**; e `carregar_caveats()` não tem ramo para a
camada, de modo que ela sairia no manifesto **sem nenhuma ressalva**. Ambos são corrigidos
junto com a camada, e o segundo é coberto pelo contrato T7.

---

## Alternativas rejeitadas

**(a) Limiar absoluto de fração construída** (ex.: "adensando se `f` subir mais de 0,10").
Rejeitada pelo argumento já medido em `docs/ADR/0011` e `0014`: a distribuição de fração
construída não é comparável entre 2020 e 2025, porque os dois mapas têm kappa 0,073 e 0,766.
Um corte absoluto mediria a diferença de qualidade dos mapas, não a mudança no terreno — e é
literalmente o defeito que reincidiu sete vezes nesta linha de trabalho.

**(b) Diferença bruta de fração, sem posto** (`f_2025 − f_2020`, mesmo com corte por quantil).
Rejeitada porque o corte relativo protege contra o **deslocamento do corte**, não contra o
**deslocamento do sinal**. Se 2025 tem comissão sistematicamente menor que 2020, a diferença
bruta é enviesada em toda a AOI; o posto absorve qualquer transformação monótona do sinal
dentro de um ano, que é exatamente a forma esperada desse viés.

**(c) Restringir a camada ao anel periurbano de 3 km.** Rejeitada por consequência espacial
verificável: Cateme (33,9731 E) e Mwaladzi (34,0326 E) — os povoados de reassentamento que
motivaram a extensão do bbox em `docs/ADR/0001` — ficam muito além de 3 km da borda urbana de
2020 e **desapareceriam da camada**. Reassentamento é a pergunta 3 de §1; uma camada de
adensamento que o exclui por definição responde à pergunta errada. O anel vira atributo.

**(d) Usar as máscaras brutas pré-R1/R2 como base.** Rejeitada por dois motivos independentes.
Primeiro, os rasters de `data/interim/estabilidade/` são declaradamente **experimentais**
(`docs/ADR/0013`) e carregam sem correção o viés de sensor de `docs/ADR/0008` e a anomalia de
2015. Segundo, e decisivo, **o motivo para preferi-los não existe**: verificou-se que
`construido_2025 ⊇ construido_2020` com 0 pixels ausentes, portanto o incremento publicado
(6.701 px = 6,03 km²) **não é inflado pela catraca** — a catraca o censura por baixo, o que é
uma limitação de sentido único, declarada em R3, e não uma contaminação. As máscaras brutas
entram apenas como variante `bruta_experimental` de diagnóstico.

**(e) Usar só a classificação própria, sem luz e sem edificações.** Rejeitada duas vezes: por
`docs/ADR/0013`, que desaconselha explicitamente leitura pixel a pixel desta série (churn de
31–54 % entre anos-âncora); e por aritmética de acurácia — S1 sozinho **herda o kappa 0,073 de
2020** e a acurácia do produtor de 0,055, isto é, herda um mapa que erra a maior parte do que
deveria encontrar. Um único sinal fraco não vira resultado por agregação espacial; três sinais
de origens independentes exigindo concordância viram, com o rótulo `modelado`.

**(f) Grade de 250 m em vez de 240 m.** Rejeitada por geometria: `250 / 30 = 8,33`. Uma grade
que não encaixa na grade canônica exige reamostragem e faz cada célula misturar frações de
pixels de fronteira — ruído introduzido justamente na quantidade que a camada mede. 240 m está
dentro do "~250 m" aceito pelo usuário e encaixa exato (8 × 8). O custo é 0,23 % da AOI na
borda sul, declarado e excluído do domínio.

---

## O que isto não corrige

Os dez riscos ficam na legenda da camada, no `.meta.json` e no manifesto do app — não só aqui.

| # | risco | por que sobrevive ao desenho |
|---|---|---|
| **R1** | erro **espacialmente estruturado** sobrevive ao posto | o posto cancela viés de nível, não viés de padrão: comissão concentrada em solo exposto de borda reordena as células |
| **R2** | **S1 e S3 partilham `f_2020`** | os votos **não são independentes**: `S1 = ECDF_2025(f) − ECDF_2020(f)` e `S3 = ECDF_OB(fp) − ECDF_2020(f)` têm o mesmo minuendo negativo. Uma célula com `f_2020` subestimado tende a votar duas vezes. Nomeado no meta e **medido** pela variante `sem_S3`; a concordância ≥2/3 é, nesse caso, mais fraca do que o nome sugere |
| **R3** | a camada **não detecta esvaziamento** | S1 é censurado por baixo pela catraca R2 (`construido` só cresce). A classe `desadensando` **deliberadamente não existe**: criá-la seria oferecer ao leitor uma categoria que o método é incapaz de povoar, e a ausência dela num mapa seria lida como ausência do fenômeno no terreno |
| **R4** | luz **sobreamostrada** de ~500 m para 240 m | uma célula de luz cobre ~4 células da grade; S2 tem resolução efetiva menor que a grade. Mitigado só por S2 nunca decidir sozinho |
| **R5** | S3 pode ser **desacordo de sensor**, não construção | Open Buildings é vetor derivado de imagem de alta resolução; discordar da máscara de 30 m de 2020 pode significar que a máscara errou, não que se construiu |
| **R6** | janela de S3 é **2020 → ~2023**, não 2020→2025 | epoch único; não há série de Open Buildings. Escrito em toda saída |
| **R7** | churn de **31 %** sobrevive à agregação | agregar a 240 m reduz, não elimina, a troca de identidade documentada em `docs/ADR/0013` |
| **R8** | dependência dos cortes | por isso a sensibilidade vai **no corpo** do artigo, não em apêndice, e o critério de §Decisão-9 foi fixado antes de ver o resultado |
| **R9** | `moatize_vila` possivelmente inflada | "25 de Setembro" não tem geometria; a partição por Voronoi atribui à vila área que pode pertencer ao povoado ausente |
| **R10** | **a camada é modelada e será lida como observada** | é o risco mais provável de todos, e o único cuja mitigação é editorial: selo em quatro lugares, e a proibição de somar `adensando` com `expansao_nova` numa única figura |

Além disso, e fora da tabela: esta camada **não estabelece causa**. Ela descreve onde houve
concordância de sinais de intensificação entre 2020 e 2025. Nada nela liga esse padrão a
mineração, a reassentamento ou a qualquer outro fator — e o novo objetivo do estudo não pede
essa ligação.

---

## Lição registrada

**Este ADR foi escrito antes do código, e é a primeira vez nesta série que isso acontece.**

`docs/ADR/0013` e `0014` foram escritos **depois** da implementação, como diagnóstico do que
já estava em disco. Custaram, entre os dois, **duas reaberturas da Fase 1**, a reexecução da
validação de acurácia sobre estratos novos, a revisão de `config/plausibilidade.yaml` e a
invalidação parcial dos números de `docs/ADR/0009`. O defeito de fundo — limiar absoluto sobre
série não estacionária — foi **prescrito** por quem orquestrava e **executado corretamente**
por quem implementava: nenhum dos dois errou dentro do seu escopo, e o resultado foi apagar o
Zambeze de cinco dos seis anos-âncora.

Escrever o método primeiro converte a decisão em objeto verificável: o script que vier a
seguir **implementa** este documento, e o contrato T2 exige que a classe publicada seja
reproduzível a partir dos atributos do GeoJSON, de modo que **divergência entre ADR e código
reprova o build**. O documento deixa de ser narrativa do que se fez e passa a ser
especificação do que se vai fazer — que é a única versão de ADR que impede alguma coisa.

Corolário operacional: um limiar calibrado contra os casos que se quer excluir não é
calibrado, é ajustado (`docs/ADR/0014`); e um método que só narra o caminho que deu certo não
é reproduzível, é publicidade (§6-A). Os `<PLACEHOLDER>` acima existem para que a segunda
falha não se repita por conveniência de redação: **nenhum valor entra neste documento antes
de ser medido.**

---

## Emenda 1 — 2026-09-09

Primeira execução completa após a correção de um defeito na tabela de sensibilidade (ver
abaixo). Preenche os seis `<PLACEHOLDER>` de valor deste documento com o medido; **o texto
acima não foi alterado**.

### Defeito corrigido antes desta medição

`pipeline/02_metrics/adensamento.py` chamava `calcular_sinais(..., incluir_s2=False,
incluir_s3=False)` nas variantes `grade_480m` e `bruta_experimental`, e depois classificava
com a `concordancia_minima` padrão (2 de 3). Com um só sinal ativo (S1), nenhuma célula pode
alcançar 2 votos: a área de `adensando` dessas duas linhas dava **0,00 km² por aritmética**,
qualquer que fosse o dado de entrada — não era medição. Corrigido para que:

- `grade_480m` recalcule **S1, S2 e S3 na própria grade de 480 m** (16×16 pixels de 30 m —
  aritmeticamente a mesma coisa que agregar 2×2 sobre a grade de 240 m, já que 16 = 2 × 8), com
  a ECDF de cada sinal recalculada sobre o domínio de 480 m. É agora um teste de **escala**,
  como o ADR sempre pretendeu, não de amputação de sinal.
- `bruta_experimental` mantenha S2 e S3 **ativos e inalterados**, trocando só a fonte de S1
  pelas máscaras brutas pré-R1/R2 — isolando o efeito de R1/R2, e não o número de sinais.
- Foi acrescentado o contrato T12 (`pipeline/tests/test_adensamento.py`): nenhuma variante
  publicada pode ter `n_sinais_ativos < concordancia_minima`; quando isso não for evitável, a
  linha registra `area = NaN` com nota explicando o motivo, nunca um zero silencioso. Verificado
  por reintrodução do padrão do defeito sobre um `sinais` sintético (nunca sobre o artefato
  publicado).

Isto **não muda** `base` nem as variantes `tau_0*/qalto_0*/qbaixo_0*` (já usavam os três
sinais) — portanto não muda a razão de sensibilidade de ±1 decil nem o veredito do critério de
publicação abaixo.

### Valores realizados (§Decisão-2 — quantis)

| corte | valor declarado (probabilidade) | valor realizado |
|---|---|---|
| `TAU` (S1) | 0,70 | **0,007436** |
| `TAU` (S2) | 0,70 | **0,001117** |
| `TAU` (S3) | 0,70 | **0,352931** |
| `Q_ALTO` | 0,80 | **0,890625** |
| `Q_BAIXO` | 0,20 | **0,03125** |
| `Q_INDUSTRIAL` | 0,50 | **0,75** |

### Domínio (aritmética de grade, §Decisão-3)

43.416 células completas de 240 m = **2.500,76 km²** (2.506,55 km² da AOI menos 5,79 km² de
`fora_de_dominio`, célula incompleta na borda sul — ver `config/plausibilidade.yaml:122`, que
já declarava este total; a Emenda 1 original divergia dele em 9,65 km² por aplicar a fórmula da
célula cheia à classe de células parciais, corrigido na Emenda 2 abaixo).

### Áreas por classe (km², grade 240 m, período 2020–2025)

Classes 1–6 só contêm células **completas** por construção do domínio (`n_pixels_30m == 64`),
então `n_células × 0,0576 km²` e `n_pixels_30m_reais × 0,0009 km²` coincidem para elas.
`fora_de_dominio` é exatamente o conjunto das células **parciais**: sua área vem da contagem
real de pixels de 30 m válidos (`n_validos` de `pipeline/02_metrics/_common.agregar_fracao`),
não da contagem de células.

| classe | área (km²) |
|---|---|
| `vazio_estavel` | 2.365,8624 |
| `pegada_industrial` | 45,4464 |
| `esparso_estavel` | 44,1792 |
| `consolidado` | 19,6416 |
| `adensando` | 15,3216 |
| `expansao_nova` | 10,3104 |
| `fora_de_dominio` | 5,7888 |

### Sensibilidade — razão recalculada depois da correção do defeito acima

As seis variantes de ±1 decil (todas já usavam os três sinais, portanto **não mudam** com a
correção):

| variante | área (km²) | razão vs. base (15,3216 km²) |
|---|---|---|
| `tau_060` | 21,5424 | 1,406 |
| `tau_080` | 6,6816 | 0,436 |
| `qalto_070` | 13,9968 | 0,914 |
| `qalto_090` | 15,9552 | 1,041 |
| `qbaixo_010` | 23,9040 | 1,560 |
| `qbaixo_030` | 11,6352 | 0,759 |

Razão realizada: **2,2931** (máximo de `max(área/base, base/área)`, atingido por `tau_080`,
razão bruta 0,436).

Regime resultante: **fora de [0,5; 2,0] e dentro de [0,2; 5,0] → publicada só como padrão
espacial e ordem de grandeza, NÃO como área.**

`grade_480m` (23,2704 km², agora com os três sinais recalculados na própria resolução) e
`bruta_experimental` (13,5360 km², S2/S3 mantidos) deixam de ser zero estrutural, mas
permanecem fora da família de ±1 decil usada no critério de §Decisão-9 — não entram nesse
cálculo, só passam a ser números interpretáveis na tabela em vez de artefatos de construção.

### Consequência de publicação (critério §Decisão-9, honrado, não contornado)

O piso da faixa de ±1 decil é **0,436**, abaixo de 0,5: o critério pré-registrado dispara. A
camada `adensamento_2020_2025` é publicada como **padrão espacial e ordem de grandeza**, e a
área de `adensando` (15,32 km²) **não é publicável como número de área** — só como indicação
de onde e aproximadamente quanto, não de quanto exatamente. Isto está gravado em
`publicavel_como: "padrao_espacial"` no `.meta.json` de ambos os rasters e deve ser repetido
nas ressalvas do manifesto do app e em qualquer figura/tabela que use esta camada. Nenhuma
variante adicional foi testada em busca de um número dentro de [0,5; 2,0]: o critério foi
fixado antes de ver o resultado, precisamente para impedir essa busca.

---

## Emenda 2 — 2026-09-09 (portão da Frente B)

Três correções, nenhuma delas muda a classificação publicada nem a razão de sensibilidade de
`adensando` (que não depende de `fora_de_dominio`).

1. **Área de `fora_de_dominio` estava errada por um fator ~2,67.**
   `pipeline/02_metrics/adensamento.py` aplicava `n_células × (240 m)²` a toda classe,
   inclusive `fora_de_dominio` — que por definição é o conjunto das células **parciais** da
   borda sul, não células cheias de 240 m. Medido no raster de 30 m: o código 0 ocupa 6.432
   pixels = 5,7888 km², não os 15,4368 km² publicados antes desta emenda (fator 2,67, oitava
   ocorrência do mesmo defeito neste estudo: uma constante calibrada para uma população
   aplicada a outra onde não vale). O script agora soma `n_validos` (contagem real de pixels de
   30 m válidos por célula, já calculada em `calcular_sinais`) por classe, em vez de
   `n_células × área_nominal_da_célula` — fórmula que só é válida para células completas. O
   total da AOI volta a bater com `config/plausibilidade.yaml:122` (2.506,55 km²), que já
   estava certo e nunca foi atualizado com o erro.
2. **A regra de voto do ADR (§5) estava incompleta** frente ao código
   (`adensamento.py:359`), que sempre filtrou por `dominio_ocupado`. Corrigido na própria §5
   acima, com a justificativa de que o corte é um quantil da ECDF de `dominio_ocupado` e uma
   célula fora dessa população não tem posição na distribuição de referência. A classificação
   publicada não mudou (as 13 feições afetadas já caíam em `pegada_industrial` por
   precedência); o que mudou é que `concordancia` agora é reconstruível a partir de
   `S1/S2/S3` e `quantis_realizados` sem reabrir o código — contrato T13.
3. **A guarda contra zero estrutural (Emenda 1) era opt-in.** `registrar()` continuava pública
   e chamada direto em várias linhas de `rodar_sensibilidade`, sem passar por
   `registrar_checada()`. Uma variante futura registrada assim, com um só sinal ativo sob a
   regra padrão de ≥ 2 votos, voltaria a produzir `area = 0,00 km²` silencioso sem que nenhum
   teste pegasse — T12 só varria `grade_480m` e `bruta_experimental` por nome. Corrigido:
   `registrar()` tornou-se privada (renomeada `_registrar_bruta`) e todo caminho de escrita da
   tabela de sensibilidade passa por `registrar_checada()`. Contrato novo T14 varre **todas**
   as linhas do CSV publicado (não uma lista de nomes) e falha se alguma tiver `area == 0` sem
   nota, ou `n_sinais_ativos < concordancia_minima` sem `area` marcada `NaN`.

Artefatos regravados por esta emenda: `data/processed/imagery/adensamento_2020_2025_{240m,30m}_32736.tif.meta.json`,
`app/public/data/imagery/manifest.json` (`caveats.adr_0016_areas_por_classe`),
`data/provenance_parts/metricas_fase2.md` (fragmento novo de proveniência da camada, achado 1
do mesmo portão).
