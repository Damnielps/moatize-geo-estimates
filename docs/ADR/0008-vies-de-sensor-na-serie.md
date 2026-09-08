# ADR 0008 — Viés de detecção que cresce com o tempo na série de área construída

- **Data:** 2026-09-07
- **Status:** aceito
- **Contexto:** Fase 1, T3. Encomendado como `docs/ADR/0006-vies-de-sensor-na-serie.md`;
  o número 0006 já estava ocupado por *amostragem de treino proporcional ao prior*, e
  renumerar um ADR aceito quebraria referências no código. Fica **0008**.
- **Autor:** agente `desenho-causal` (§5.4).
- **Artefatos:** `data/processed/causal/teste_vies_morfologia.csv`,
  `data/processed/causal/teste_vies_degradacao.csv`,
  `data/processed/causal/teste_vies_sensor.meta.json`,
  `pipeline/03_causal/teste_vies_sensor.py`.

## Problema

A classificação própria e o WSF Evolution discordam **na direção da tendência**
entre 2000 e 2015. Com a série corrigida desta entrega (após o defeito de
denominador em `compostos_chuva.ndvi`, ver §"Correção" abaixo):

| período | classificação (pós-R2) | WSF Evolution |
|---|---|---|
| 2000–2005 | 8,10 %/ano | 2,58 %/ano |
| 2005–2010 | 7,35 %/ano | 3,30 %/ano |
| 2010–2015 | 5,57 %/ano | 4,26 %/ano |

A classificação desacelera monotonicamente; o WSF acelera monotonicamente. A
razão classificação/WSF sobe 0,41 → 0,52 → 0,65 → 0,69. Depois do ADR 0003, H1
é uma hipótese **sobre aceleração da área construída**: as duas fontes respondem
o oposto à pergunta central do estudo. Um viés que cresce monotonicamente é
indistinguível de tendência e seria lido pelo desenho de §5.4 (séries
interrompidas em 2005/2011/2016/2022, DiD) como efeito do tratamento.

## O que foi medido

### 1. Sentinel-2 não é a explicação (verificado, não presumido)

O teste pedido — "2015 com Landsat isolado e com Landsat+S2" — **é vazio**. O
composto de estação seca de 2015 (mai–out) **não contém Sentinel-2**:
`composto_2015_30m_32736.tif.meta.json` traz `colecao_sentinel2: null`, e o
composto de chuva 2014/15 traz `n_cenas_sentinel2 = 0`. O S2 L2A só cobre a AOI
a partir de dez/2015. O S2 entra em **2020 e 2025 apenas** — depois do fim do
WSF (2015), portanto fora da janela onde a discordância é observável. Rodado
mesmo assim como cenário de controle: `sem_sentinel2` em 2015 devolve
**exatamente** a mesma área que o produto cheio (51,712 km²), como tinha de ser.

### 2. Capacidade de observação: viés medido de −17,0 % em 2015

Mediana de observações válidas por pixel, estação seca: **3 (2000), 4 (2005),
4 (2010), 10 (2015), 31 (2020), 42 (2025)** — variação de 14× ao longo da série,
com protocolo idêntico.

Teste de degradação (`teste_vies_degradacao.csv`): 2015 reconstruído com a
capacidade de 2000 (3 cenas Landsat na seca, 6 na chuva, sem S2, escolhidas por
espaçamento uniforme na janela), tudo o mais idêntico — mesmas features, mesmo
treino semeado pelo WSF, mesma seed, mesmo filtro de coerência:

| cenário | área construída, RF puro |
|---|---|
| cheio (produto publicado) | 51,712 km² |
| sem Sentinel-2 | 51,712 km² |
| capacidade de 2000 | **42,935 km²** |

**−17,0 % de área** só por reduzir o número de observações. Equivale a
**+1,25 %/ano** de crescimento espúrio ao longo de 2000–2015. Aplicando essa
correção de nível ao ano final, a CAGR 2000–2015 cai de **7,00 %/ano** para
**5,68 %/ano** — a mesma ordem de grandeza que a diferença entre H1
(4 %/ano → 7 %/ano) e sua negação.

Limite declarado: a degradação altera o **número de observações** e a presença
do S2, **não a radiometria** (ETM+/TM 8 bits × OLI 12 bits, SNR distinto). Por
esse lado o viés real é subestimado.

### 3. Uma parte grande do viés não é sensor — é a geometria do protocolo

`teste_vies_morfologia.csv` aplica ao **próprio WSF** as duas operações
morfológicas do protocolo (erosão 3×3 que gera os positivos de treino; filtro de
coerência 3×3 sobre a predição), sem tocar em imagem:

| ano | WSF (km²) | WSF após as duas operações | razão | n manchas | mediana px/mancha |
|---|---|---|---|---|---|
| 2000 | 34,20 | 20,57 | 0,601 | 613 | 2 |
| 2005 | 38,86 | 24,80 | 0,638 | 562 | 2 |
| 2010 | 45,70 | 29,88 | 0,654 | 545 | 3 |
| 2015 | 56,31 | 38,04 | 0,676 | 480 | 8 |

O "piso geométrico" sobe 0,601 → 0,676 **sem nenhum sensor envolvido**: a mancha
de 2000 é muito mais fragmentada (mediana de 2 pixels por mancha) que a de 2015
(8 pixels), e operações 3×3 punem mancha pequena proporcionalmente mais. A razão
observada classificação/WSF (0,41 → 0,69) dividida por esse piso dá 0,69 → 1,02:
**a maior parte da subida da razão é geometria do protocolo, e o resíduo é o
viés de detecção**.

### 4. Definição: não é "outro lugar", é "menos dentro da mesma mancha"

90 ± 2 % do construído classificado cai **dentro** do WSF do mesmo ano em todos
os quatro anos (0,930 / 0,893 / 0,894 / 0,904). A divergência não é de
localização nem de definição de assentamento: é de **quanto** da mesma mancha
cada produto preenche. Isso afasta H-def como explicação principal.

## Decisão

1. **A série própria de área construída não é a série primária de tendência
   para 1997–2015.** Até 2015 a série primária passa a ser o **WSF Evolution**,
   que tem sensor, protocolo e limiar constantes por construção e é o único
   produto de nível A com ano de primeira detecção anual na janela. A
   classificação própria mantém o papel que **só ela** cumpre: separar as três
   camadas mutuamente exclusivas (`urbano` / `reassentamento` / `industrial`),
   que nenhum produto externo faz — e é essa separação que o §5.1 e o §10 pedem
   ("nenhuma cava contada como área urbana").
2. **Consequência para a validação:** o WSF passa a ser série primária **e**
   semente de treino. Ele continua **proibido** como referência de acurácia
   (`pipeline/01_imagery/acuracia.py` não reporta nenhuma métrica contra WSF).
3. **H1 continua testável, com a hipótese reformulada em cima do WSF** e com a
   série própria usada só para decomposição por camada. Testar aceleração
   **com a série própria seria inválido**: o viés medido (+1,25 %/ano) tem a
   mesma ordem de grandeza do efeito procurado.
4. **Direção do viés, e o que ela salva:** o viés infla o crescimento **tardio**
   (mais observações depois). Corrigi-lo torna a desaceleração da série própria
   **mais** forte, não menos. Portanto a leitura "a classificação desacelera" é
   robusta ao viés; o que o viés impede é usar a **magnitude** da aceleração,
   que é exatamente o que H1 exige. Note-se ainda que 2005 e 2010 têm a **mesma**
   mediana de observações (4): o crescimento medido entre esses dois anos é o
   trecho menos contaminado da série.
5. **Toda quebra de §5.4 sobre a série própria (2005, 2011, 2016, 2022) passa a
   exigir um teste de placebo adicional:** a mesma quebra estimada sobre a
   mediana de observações por pixel. Se a "quebra" aparecer também aí, é
   capacidade de medir, não tratamento. Fica registrado como requisito da Fase 2.

## Alternativas rejeitadas

- **Harmonizar os sensores por regressão entre pares de cenas coincidentes.**
  Rejeitada: não há sobreposição temporal entre L5 e L8 nesta AOI nos anos-âncora,
  e harmonizar reflectância não corrige o efeito de **número de observações** na
  mediana, que é o viés medido.
- **Reamostrar todos os anos para 3 observações.** Corrigiria o viés nivelando por
  baixo, mas jogaria fora 90 % das observações de 2020/2025 e degradaria também a
  classificação de agricultura urbana de §5.6, que depende de fenologia intra-anual.
  Rejeitada como padrão; permanece disponível como **análise de sensibilidade**
  (o script já faz isso por ano).
- **Publicar a série própria como tendência com ressalva textual.** Rejeitada:
  a ressalva não impede que a série entre num DiD e produza um efeito.

## Correção de defeito registrada junto

`compostos_chuva.ndvi` dividia `(nir-red)/(nir+red)` **sem** a máscara de
denominador quase-zero de `config/tolerances.yaml`, ao contrário do NDVI de
estação seca. `ndvi_chuva_2015` chegava a 2,85 (faixa algébrica: [-1, 1]) e o
erro se propagava para `ndvi_amplitude`, a feature mais discriminante do
classificador. Corrigido na origem, reusando `indices._razao_normalizada`; os
seis anos de métrica fenológica e a classificação inteira foram regerados. O
contrato `test_faixa_plausivel_dos_indices_normalizados` cobrava de
`ndvi_amplitude` (diferença de dois NDVI, faixa [-2, 2]) uma faixa que ela nunca
teve de respeitar, porque derivava a família do índice do primeiro token do nome
do arquivo; agora a família é resolvida pelo nome inteiro e a amplitude tem
contrato próprio (`test_faixa_plausivel_da_amplitude_fenologica`).
