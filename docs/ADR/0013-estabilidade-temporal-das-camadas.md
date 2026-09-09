# ADR 0013 — A instabilidade não é de `urbano`, mas a monotonicidade dele também não é evidência; e a causa das duas coisas é a mesma

- **Data:** 2026-09-08
- **Fase:** 2b — **diagnóstico**, não reclassificação
- **Autor:** subagente de desenho causal (§5.4)
- **Estado:** aceito
- **Contexto obrigatório:** `docs/ADR/0008` (viés de sensor), `0009` (critério de
  acurácia), `0011` (pegada como classe própria), `0012` (cultivo)
- **Artefatos:** `data/processed/causal/decomposicao_permanencia_urbano.csv`,
  `data/processed/causal/estabilidade_temporal_camadas.csv`,
  `data/processed/causal/estabilidade_temporal.meta.json`,
  `pipeline/03_causal/estabilidade_temporal.py`,
  `pipeline/tests/test_estabilidade.py`,
  rasters experimentais em `data/interim/estabilidade/` (git-ignored)

## Pergunta

`docs/ADR/0012` reprovou `cultivo_sequeiro` porque as classes de cobertura oscilam de
forma impossível entre anos-âncora (vegetação: 10,6 % → 75,5 % → 89,0 % → 6,1 % da AOI).
A camada `urbano` mostra uma série suave — mas essa suavidade é **imposta** pela regra R2
de permanência (`construido(t) = ∪_{t'≤t} construido_R1(t')`), não emergente. Catraca
sobre sinal ruidoso e estabilidade real são indistinguíveis à vista. Antes de abrir a
Fase 3, é preciso saber, com número, se a instabilidade contamina `urbano`.

## Método

`pipeline/03_causal/estabilidade_temporal.py` **regenera** (não reclassifica) os
intermediários que `classificacao.py` calcula em memória e não persiste: o rótulo bruto
de 4 classes do Random Forest e a máscara bruta de construído, antes de R1 e R2. Mesmas
seeds, mesmas features, mesmo pool de treino.

**Verificação de que a regeneração é fiel:** o R2 recalculado a partir das máscaras
regeneradas bate **pixel a pixel** com os `construido_<ano>_30m_32736.tif` publicados —
0 pixels divergentes em cada um dos seis anos. A áreas brutas reproduzem os
`area_construida_sem_restricao_km2` do CSV publicado até a terceira casa. Nada em
`data/processed/imagery/` foi tocado.

---

## 1. Quanto do estoque publicado é detecção do ano e quanto é catraca

`data/processed/causal/decomposicao_permanencia_urbano.csv`, km²:

| ano | bruta (RF) | após R1 | após R2 (publicado) | sustentado pelo ano | herdado da união | **fração herdada** | ΔR2 | Δbruta |
|---|---|---|---|---|---|---|---|---|
| 2000 | 16,93 | 14,04 | 14,04 | 14,04 | 0,00 | **0,0 %** | — | — |
| 2005 | 23,88 | 20,73 | 20,73 | 20,73 | 0,00 | **0,0 %** | +6,69 | +6,95 |
| 2010 | 33,32 | 28,55 | 29,56 | 28,55 | 1,01 | **3,4 %** | +8,83 | +9,45 |
| 2015 | 51,71 | 36,39 | 38,76 | 36,39 | 2,36 | **6,1 %** | +9,20 | +18,39 |
| 2020 | 38,87 | 36,11 | 41,38 | 36,11 | 5,27 | **12,7 %** | +2,62 | **−12,85** |
| 2025 | 39,60 | 39,60 | 48,29 | 39,60 | 8,69 | **18,0 %** | +6,91 | +0,74 |

Três leituras, todas com número:

1. **A fração herdada cresce monotonicamente: 0 → 0 → 3,4 → 6,1 → 12,7 → 18,0 %.** Em
   2025, **8,69 km² dos 48,29 km² publicados (18,0 %) não são detectados pela
   classificação daquele ano** — estão na série apenas pela união com anos anteriores.
   É exatamente o padrão que a pergunta antecipava: um artefato da regra com a mesma
   forma da tendência que o desenho quer medir.
2. **O estoque sustentado pelo próprio ano estagna depois de 2015:** 36,39 (2015) →
   36,11 (2020) → 39,60 (2025). CAGR 2015–2025 de **0,85 %/ano**, contra **2,23 %/ano**
   da série publicada. A série publicada diz que a área construída cresceu **24,6 %**
   entre 2015 e 2025; a parte dela sustentada por observação do próprio ano cresceu
   **8,8 %**. Quase dois terços do crescimento da última década são catraca.
3. **A razão ΔR2/Δbruta desmonta a série em duas metades:** 0,96 (2000–05), 0,93
   (2005–10), 0,50 (2010–15), **−0,20** (2015–20), **+9,38** (2020–25). Até 2010 o
   incremento publicado é acompanhado quase um-para-um pelo sinal bruto. De 2010 em
   diante descola; em 2015–2020 **inverte de sinal** (a série publicada sobe enquanto o
   sinal bruto cai 12,85 km²); em 2020–2025 a série publicada sobe 9,4 vezes mais que o
   sinal bruto.

**Consequência aritmética que precisa estar escrita ao lado de qualquer uso da série:**
o incremento de R2 é, por construção, formado só por primeiras detecções confirmadas.
Ele **não pode ser negativo**. Perguntar a essa série se houve desaceleração depois de
2016 é perguntar a um contador cumulativo se ele já andou para trás.

---

## 2. `urbano` é mais estável que as classes de cobertura — por uma ordem de grandeza em
área, mas não em pixel

`data/processed/causal/estabilidade_temporal_camadas.csv`, sobre o rótulo **bruto** do
RF (antes de R1, R2 e das pegadas de ADR 0011), no domínio válido comum a cada par:

| par | classe | área t (km²) | área t+1 (km²) | razão t+1/t | Jaccard | churn |
|---|---|---|---|---|---|---|
| 2000–05 | construido | 16,92 | 23,87 | 1,41 | 0,525 | 0,475 |
| 2005–10 | construido | 23,86 | 33,31 | 1,40 | 0,527 | 0,473 |
| 2010–15 | construido | 33,13 | 51,71 | 1,56 | 0,456 | 0,544 |
| 2015–20 | construido | 50,18 | 38,84 | **0,77** | 0,585 | 0,415 |
| 2020–25 | construido | 38,87 | 38,44 | 0,99 | 0,690 | 0,310 |
| 2005–10 | vegetacao | 270,9 | 1889,1 | **6,97** | 0,138 | 0,863 |
| 2015–20 | vegetacao | 2230,4 | 678,2 | **0,30** | 0,302 | 0,698 |
| 2020–25 | vegetacao | 680,0 | 151,9 | **0,22** | 0,193 | 0,808 |
| 2005–10 | solo_exposto | 2164,0 | 535,6 | **0,25** | 0,239 | 0,761 |
| 2015–20 | solo_exposto | 167,7 | 1730,4 | **10,32** | 0,091 | 0,909 |

**Resposta ao item 2: não, a instabilidade de `urbano` não é da mesma ordem.**

- **Em área:** a razão t+1/t de `construido` fica no intervalo **[0,77 · 1,56]** — amplitude
  de fator 2,0 ao longo da série. `vegetacao` fica em [0,22 · 6,97] (fator **32**) e
  `solo_exposto` em [0,25 · 10,32] (fator **41**). `urbano` é **de 16 a 20 vezes** mais
  estável em área que as duas classes de cobertura. `construido` é o alvo espectralmente
  mais distinto, como se suspeitava — e agora está medido.
- **Em pixel, a folga é muito menor.** O churn de `construido` é **31 % a 54 %** em todos
  os pares: entre um terço e metade dos pixels chamados de construído trocam de identidade
  entre anos-âncora consecutivos. O Jaccard médio de `construido` (0,556) é maior que o de
  `vegetacao` (0,338) e o de `solo_exposto` (0,423), mas na mesma ordem de grandeza.
  A estabilidade de `urbano` vem de **ganhos e perdas que se compensam** (perda 17–35 %,
  ganho 15–49 %), não de os pixels ficarem no lugar.

Isto é uma resposta de duas pontas, e as duas importam: **a área agregada de `urbano` é
utilizável; a localização pixel a pixel não é.** Qualquer método de §5.4/§5.6 que dependa
de o mesmo pixel ser construído em dois anos consecutivos — matriz de transição, logit de
conversão de §5.6.4, tipologia infill/borda/leapfrog — opera sobre um sinal com 31–54 % de
churn e precisa dizê-lo.

---

## 3. A causa comum das duas instabilidades: limiar absoluto sobre série radiometricamente
não comparável

Este é o achado que não estava na encomenda e que explica os dois fenômenos de uma vez.

`rotulos_treino()` rotula os negativos por **limiares físicos absolutos e fixos**, entre
eles `vegetacao` ⇔ `NDVI(seca) ≥ 0,30`. Medido na AOI:

| ano | mediana NDVI(seca) da paisagem | fração da AOI com NDVI(seca) ≥ 0,30 | vegetação publicada (§ do prompt) |
|---|---|---|---|
| 2000 | 0,233 | 10,8 % | 10,6 % |
| 2005 | 0,231 | 11,1 % | — |
| 2010 | 0,358 | 76,7 % | 75,5 % |
| 2015 | 0,409 | 90,9 % | 89,0 % |
| 2020 | 0,259 | 27,6 % | — |
| 2025 | 0,204 | 6,1 % | 6,1 % |

(`data/processed/causal/estabilidade_temporal.meta.json` →
`radiometria_da_paisagem_por_ano`; domínio = pixels válidos em todas as features do ano.)

**A oscilação "impossível" de `vegetacao` não é falha do classificador: é o limiar de
rótulo, transmitido quase inalterado à saída.** A mediana de NDVI(seca) da paisagem
percorre 0,204–0,409 entre os anos-âncora — por diferença de sensor (ETM+ / TM / OLI /
OLI-2) e de pluviosidade — e o corte fixo de 0,30 cai **dentro** dessa faixa. Um corte
que atravessa a mediana da própria distribuição não separa vegetação de solo: separa ano
verde de ano seco.

`docs/ADR/0011` diagnosticou exatamente esse defeito para o NDVI ("um corte absoluto de
NDVI(chuva) < 0,25 marcaria 83 km² em 2000 e 472 km² em 2025 — mediria o ano, não a
mina") e o corrigiu **apenas na camada de pegada**, adotando a razão à mediana da
paisagem do ano. **A correção nunca foi propagada para `rotulos_treino`.** As classes de
cobertura ficaram com o defeito que a pegada teve corrigido.

O efeito sobre `construido` é indireto e é o que fecha o item 4. O pool de treino de
`solo_exposto` — a classe que absorve os pixels secos e brilhantes, os mais confundíveis
com construído — colapsa junto:

| ano | negativos `solo_exposto` disponíveis | amostrados (proporcional ao prior) | área bruta de construído |
|---|---|---|---|
| 2000 | 2 262 852 | 176 487 | 16,93 km² |
| 2005 | 2 235 169 | 174 722 | 23,88 km² |
| 2010 | 501 653 | 38 868 | 33,32 km² |
| 2015 | **124 838** | **9 707** | **51,71 km²** |
| 2020 | 1 792 219 | 139 329 | 38,87 km² |
| 2025 | 2 363 722 | 180 757 | 39,60 km² |

Em 2015 a classe concorrente de `construido` entra no treino com **18 vezes menos**
amostras que em 2000 e 2025, e é exatamente o ano em que a área bruta de construído
atinge o máximo da série — **maior que a de 2025**, o que é fisicamente impossível numa
cidade que cresceu. A amostragem proporcional ao prior (`docs/ADR/0006`) é correta em
princípio e aqui repassa fielmente um prior que está errado.

Registre-se, de passagem, que a `ndvi_amplitude` — a métrica fenológica em torno da qual
o redesenho da Fase 1 foi construído e que o docstring de `classificacao.py` descreve
como a mais discriminante — tem importância de **0,004 a 0,018** no Random Forest em
todos os seis anos, contra 0,30–0,48 do NDVI de seca (`prior_de_treino_por_ano` no mesmo meta.json). O classificador publicado não usa
a fenologia; ele usa o nível de verde do ano. É a mesma constatação por outro caminho.

---

## 4. A queda de 2015→2020 é artefato — e o ano anômalo é **2015**, não 2020

O enunciado do diagnóstico observa que a capacidade de observação **aumenta** (mediana de
observações por pixel 10 → 31; 10 cenas Landsat sem S2 em 2015, 9 Landsat + 103 S2 em
2020) e a área sem restrição **cai 25 %** — o inverso do viés de `docs/ADR/0008`.

Três medições resolvem:

1. **O canal de observação não explica a queda; ele a agrava.** `docs/ADR/0008` mediu, por
   degradação controlada, que 2015 reconstruído com a capacidade de 2000 devolve 42,9 km²
   contra 51,7 km² — **mais observações ⇒ mais área**. Indo de 2015 para 2020 as
   observações triplicam, então esse canal prevê 2020 **acima** de 51,7. O observado é
   38,9. O resíduo a explicar não é −12,8 km²: é **maior** que isso. H-obs está
   descartada como explicação da queda, por sinal.
2. **Referência externa independente aponta 2015 como o outlier.** GHSL BUILT-S R2023A
   (épocas observadas, corte 0,25 — `data/processed/concordancia_ghsl.csv`) cresce
   suavemente: 20,4 / 22,0 / 26,2 / 34,9 / 36,4 km². A razão bruta/GHSL é 0,83 / 1,08 /
   1,27 / **1,48** / 1,07. O pico de 1,48 está em 2015 e em nenhum outro ano. O GHSL não
   registra queda alguma entre 2015 e 2020 (+4,3 %). **O que precisa de explicação é o
   excesso de 2015, não o déficit de 2020.**
3. **Para onde foi o construído "perdido".** Dos 18,86 km² que o RF chama de construído em
   2015 e não chama em 2020 (`estabilidade_temporal.meta.json`): **15,03 km² (79,7 %)
   viram `solo_exposto`** em 2020, 1,80 km² continuam rotulados construído mas caem no
   filtro de coerência 3×3, 1,53 km² ficam sem rótulo válido e apenas **0,48 km² (2,5 %)
   viram vegetação**. O "construído" perdido é, quase inteiramente, terreno seco e
   brilhante que em 2015 não tinha classe concorrente com quem competir no treino — o
   mecanismo do item 3, confirmado no destino dos pixels.

**Conclusão do item 4: a queda 2015→2020 é artefato de rotulagem, e é a inflação de 2015
que a produz.** Nota a crédito da regra R1: ela rejeitou **15,32 km² em 2015** — de longe a
maior rejeição da série (2,9 / 3,1 / 4,8 / **15,3** / 2,8 / 0,0) — justamente porque esses
pixels não se confirmaram em 2020. A confirmação de primeira detecção funcionou como
anticorpo contra a anomalia; a permanência (R2), não.

---

## 5. R2 deveria ter escopo por camada

Sim, e a evidência para separar já está publicada em `data/processed/pegada_por_ano.csv`:

| camada / ano | sem permanência | publicada (com R2) | **fração herdada** |
|---|---|---|---|
| `industrial` 2020 | 36,70 | 46,43 | 21,0 % |
| `industrial` 2025 | 56,67 | 62,50 | 9,3 % |
| `reassentamento` 2020 | **0,63** | 2,00 | **68,6 %** |
| `reassentamento` 2025 | 1,01 | 2,32 | **56,4 %** |

- **`urbano`: R2 é defensável, com custo agora quantificado.** Edificação é quase
  permanente nesta AOI; a união é a hipótese física correta. O custo é o item 1: 18 % do
  estoque de 2025 sem sustentação no ano. Defensável **não** é o mesmo que gratuito, e o
  número tem de viajar junto com a série.
- **`industrial`: R2 não é defensável pelo mesmo argumento.** Mina fecha, cava é
  reabilitada, pilha de estéril é revegetada. `docs/ADR/0011` item 5 **já registra** que
  parte da pilha de 2015 aparece revegetada ou sombreada em 2020 e que a permanência a
  mantém contada, e o item 6 declara que reabilitação é indetectável neste desenho.
  Aplicar a `industrial` uma regra justificada por "construído é permanente" é usar um
  argumento sobre alvenaria para sustentar um número sobre rocha movida.
- **`reassentamento`: R2 é indefensável e ativamente danoso.** Não pelo tamanho do efeito
  (embora seja o maior: 69 % do valor de 2020 é herdado), mas porque a **pergunta
  específica 3 de §1** é literalmente "como os povoados de reassentamento evoluíram —
  consolidação, **abandono**, adensamento". A permanência torna abandono **indetectável
  por construção**. O pipeline responde à pergunta antes de medi-la, e responde
  "consolidação" sempre.

---

## Decisão

1. **A camada `urbano` não sofre da instabilidade que reprovou `cultivo_sequeiro`.**
   Amplitude de razão inter-anual de fator 2,0 contra 32 e 41 das classes de cobertura;
   Jaccard médio 0,556 contra 0,338 e 0,423. **A área agregada de `urbano` é utilizável.**
   Isto é registrado como resultado positivo, com os números acima.
2. **A monotonicidade da série publicada não é evidência, e a fração herdada é o número
   que a qualifica.** `fracao_estoque_herdada` (0 / 0 / 3,4 / 6,1 / 12,7 / 18,0 %) passa a
   ser publicada ao lado da série em toda tabela, figura e tooltip que use área construída
   própria, com os contratos de `pipeline/tests/test_estabilidade.py` a garantir.
3. **A localização pixel a pixel de `urbano` não é utilizável sem ressalva.** Churn de
   31–54 % entre anos-âncora consecutivos. Toda análise por pixel (§5.6.4, matrizes de
   transição, tipologia de expansão) declara esse número.
4. **A causa raiz das instabilidades de cobertura está identificada e localizada:** limiar
   absoluto `NDVI(seca) ≥ 0,30` em `rotulos_treino()`, sobre uma série cuja mediana de
   paisagem percorre 0,204–0,409. `docs/ADR/0011` corrigiu esse defeito só na pegada. **Este
   ADR não corrige nada** — o escopo da Fase 2b é diagnóstico. A opção de correção e seu
   custo estão abaixo, e a decisão é do orquestrador.
5. **R2 passa a ser questão de escopo por camada, não regra global.** Recomendação:
   manter em `urbano`, remover de `industrial` e `reassentamento`. Decisão do orquestrador.

## O que a Fase 3 pode e não pode estimar (item 5)

**Não pode:**

- **Estimar quebra de nível na série própria pós-R2 (2005, 2011, 2016, 2022).** A fração
  herdada cresce 0 → 18 % ao longo da série, com monotonicidade e concavidade próprias,
  atravessando as duas quebras de interesse. Uma quebra estimada aí é indistinguível de
  aceleração da catraca. Isto **reforça e estende** `docs/ADR/0008`, que já tinha tirado a
  série própria do papel de série primária de tendência.
- **Testar H4 (descolamento luz × área após 2016) com a área vinda de R2.** ΔR2 ≥ 0 por
  construção. Numa elasticidade área–luz, o lado da área não pode cair enquanto a luz cai:
  o desenho produz "área cresce, atividade estagna" **mesmo se H4 for falsa**. É
  circularidade, não resultado. A elasticidade por fase só é estimável com a área vinda de
  série externa, ou com a coluna `estoque_sustentado_pelo_ano_km2` desta decomposição
  (que **pode** cair, e de fato cai em 2020).
- **Usar o par 2015–2020 como base de qualquer efeito.** 2015 está inflado em ~15 km² pelo
  mecanismo do item 3, e a quebra de 2016 cai exatamente entre os dois anos-âncora
  contaminados. Um efeito de "bust" estimado aí mede o colapso do pool de treino de
  `solo_exposto`, não o do preço do carvão.

**Ressalva que precisa ser dita mesmo sobre a alternativa de `docs/ADR/0008`:** o WSF
Evolution é um produto de **ano de primeira detecção** e portanto **também é monotônico por
construção**. Trocar a série própria pelo WSF resolve o viés de protocolo, **não** resolve
a catraca. Toda quebra estimada sobre WSF ou GHSL-BUILT é quebra na **taxa de primeira
detecção**, nunca em "área urbana", e é incapaz de detectar contração. Isso precisa estar
escrito no artigo, não só no ADR.

**Pode:**

- **Estimar quebras em 2005 e 2011 sobre o WSF Evolution anual**, lido explicitamente como
  taxa de primeira detecção, com a ressalva acima. É o trecho da série em que ΔR2/Δbruta é
  0,96 e 0,93 — o sinal bruto corrobora o publicado quase um-para-um.
- **Estimar as quebras de 2016 e 2022 sobre luzes noturnas (DMSP-VIIRS harmonizado,
  VIIRS DNB).** As luzes **não são ratcheted**: podem cair, e é por isso que carregam o
  teste de bust e de H4 que a área construída não pode carregar. Recomenda-se que a série
  de luzes seja a série primária de §5.4 depois de 2015. Cuidado declarado do próprio
  mandato: causalidade reversa entre luz e população.
- **Estimar sobre `estoque_sustentado_pelo_ano_km2`**, como série de sensibilidade
  declaradamente experimental, para mostrar quanto do efeito estimado sobrevive fora da
  catraca. Não como série primária: ela carrega o viés de observação de `docs/ADR/0008` e a
  anomalia de 2015 sem nenhuma correção.
- **Rodar os placebos, agora em número de quatro.** Aos dois já exigidos (placebo espacial
  nas capitais de comparação; placebo temporal), `docs/ADR/0008` acrescentou a quebra sobre
  a mediana de observações por pixel. **Este ADR acrescenta um quarto placebo obrigatório:
  a mesma quebra estimada sobre a fração da AOI com NDVI(seca) ≥ 0,30** (10,8 / 11,1 /
  76,7 / 90,9 / 27,6 / 6,1 %), que é radiometria de paisagem e não tem relação nenhuma com
  o carvão. Se a quebra aparecer também aí, é o ano, não o tratamento.

## Se algo precisa mudar: opções e custo (decisão do orquestrador)

| # | Mudança | Custo medido | Risco |
|---|---|---|---|
| **A** | Nada muda. Publica-se a decomposição ao lado da série e a Fase 3 opera sob as ressalvas acima. | **zero** — os artefatos já existem | Nenhum resultado novo; §5.6.4 e H5 continuam apoiados em cobertura instável |
| **B** | Remover R2 de `industrial` e `reassentamento`, manter em `urbano`. | ~15 min de máquina (a etapa de RF regenerou os seis anos em **~3 min** nesta execução) + `make imagery metrics agri` + revisão de `config/plausibilidade.yaml`. **1 sessão de agente.** | `reassentamento` 2020 cai para 0,63 km², abaixo do piso de plausibilidade vigente. Isso é sinal honesto, não falha — mas o contrato precisa ser rediscutido, não afrouxado |
| **C** | Corrigir a raiz: trocar os limiares absolutos de `rotulos_treino()` pela razão à mediana da paisagem do ano, como `docs/ADR/0011` já fez para a pegada. | Reabre a Fase 1 pela terceira vez. Muda todos os anos, os estratos de validação (os 288 pontos interpretados continuam válidos — a posição não muda —, mas os **pesos** do estimador de Olofsson mudam), os números de `docs/ADR/0009` e as conclusões de `docs/ADR/0012`. **2–3 sessões.** | Alto em escopo, mas é o **único** caminho que torna as classes de cobertura utilizáveis — e delas dependem H5 (conversão cropland→construído), o logit de §5.6.4 e a pergunta 8 de §1 |

Recomendação do autor, para decisão do orquestrador: **B agora** (barato, corrige um
defeito de escopo já documentado em `docs/ADR/0011` e destrava a pergunta 3 de §1), e **C
como pré-requisito declarado de §5.6.4 e de H5** — não de §5.4, que pode avançar com A
sob as ressalvas do item 5. Sem C, a resposta honesta a H5 é "não determinável com esta
série", pelo mesmo argumento que `docs/ADR/0012` usou para `cultivo_sequeiro`.

## Alternativas rejeitadas

- **Concluir "urbano é estável" a partir da série publicada.** Rejeitada: a série é
  monotônica por construção. Era a conclusão que o diagnóstico existia para evitar.
- **Reclassificar para testar as hipóteses.** Fora do escopo declarado da Fase 2b. Os
  intermediários foram **regenerados**, com prova de identidade pixel a pixel contra o
  publicado, e escritos em `data/interim/` marcados como experimentais.
- **Atribuir a queda de 2015→2020 à entrada do Sentinel-2.** Rejeitada por medição: o
  composto de seca de 2015 não tem S2 (`colecao_sentinel2: null`), e o canal de observação
  prevê a queda no sentido oposto ao observado (item 4.1).
- **Recalibrar `LIMIAR_VEGETACAO_NDVI_SECA` até a série de vegetação ficar suave.**
  Rejeitada pelo mesmo motivo que `docs/ADR/0012` rejeitou recalibrar `cultivo_sequeiro`:
  seria ajustar o parâmetro contra o sintoma. A correção correta é estrutural (opção C):
  o limiar não deve ser absoluto.
