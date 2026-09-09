# Desenho pré-registrado da Fase 3 — §5.4 (causal), §5.5 (cenários), §5.6.4 (logit) e §5.6.7

- **Data de fixação:** 2026-09-08
- **Autor:** subagente `desenho-causal` (§5.4, §5.5, §5.6.4, §5.6.7)
- **Estado:** pré-registro. Fixado **antes** de qualquer série de luzes noturnas existir em disco
  (`data/raw/` não contém nenhum produto DMSP, VIIRS ou harmonizado na data acima; o fetch
  corre em paralelo). Este é o ponto do documento: um desenho escrito depois de ver a série é
  um desenho ajustado ao resultado.
- **Contexto vinculante:** `docs/ADR/0003`, `0008` (+ emenda de 2026-09-08), `0009`, `0011`,
  `0012`, `0013`, `0014`. As restrições do item "O que a Fase 3 pode e não pode estimar" de
  `docs/ADR/0013` são tratadas aqui como **vinculantes**, não como recomendação.
- **Determinismo:** todo processo estocástico usa `config/seeds.yaml`
  (`controle_sintetico.seed: 13579`, `n_placebos_espaciais: 5`, `n_placebos_temporais: 4`;
  `bootstrap.seed: 97531`, `n_reamostragens: 1000`; `logit_espacial.seed: 24680`).
- **Regra de valor:** este documento não contém nenhuma estimativa. Onde um número ainda não
  existe, há `⟨PLACEHOLDER⟩` e o **critério** que o preencherá. Nenhum valor plausível é escrito
  no lugar de um valor medido.

---

## 0. Fronteira herdada — o que já está proibido antes de começar

| Proibição | Origem | Motivo em uma linha |
|---|---|---|
| Quebra de nível ou inclinação sobre a série própria pós-R2 (2005, 2011, 2016, 2022) | ADR 0013 §"não pode" | fração herdada 0→18 % atravessa as quebras; quebra é indistinguível de aceleração da catraca |
| Testar H4 com área vinda de R2 | ADR 0013 §"não pode" | ΔR2 ≥ 0 por construção; o desenho produz "área cresce, atividade estagna" mesmo se H4 for falsa |
| Usar o par 2015–2020 como base de efeito | ADR 0013 §"não pode", ADR 0014 §"o que isto não corrige" | 2015 inflado (~15 km²) pelo colapso do pool de `solo_exposto`; a quebra de 2016 cai entre os dois anos contaminados |
| Ler WSF Evolution ou GHSL-BUILT como **estoque** de área urbana | ADR 0008 emenda, ADR 0013 ressalva | ambos são ano-de-primeira-detecção / não-decrescentes; nenhuma quebra estimada aí detecta contração |
| Usar GHSL 2025/2030 em qualquer afirmação de tendência | §0 e §4.2 do mandato | épocas **extrapoladas**, não observadas |
| Usar acurácia global como critério | ADR 0009 | classe rara: mapa vazio obtém 98–99 % |
| Inferir conversão pixel a pixel sem declarar churn | ADR 0013 §3 | churn de `construido` 31–54 % entre anos-âncora consecutivos |

O que **sobra** para §5.4 é: (a) a taxa anual de primeira detecção do WSF Evolution até 2015;
(b) as luzes noturnas, que **podem cair**; (c) `estoque_sustentado_pelo_ano_km2` como
sensibilidade declaradamente experimental. Todo o desenho abaixo cabe dentro disso.

---

## 1. Estimando **o quê** — série, unidade e janela para cada uma das quatro quebras

### 1.1 Séries candidatas, definidas antes de vistas

| id | Série | Unidade | Cobertura | Pode cair? | Nível | Estado em disco (2026-09-08) |
|---|---|---|---|---|---|---|
| `S_WSF_taxa` | WSF Evolution: **pixels de primeira detecção no ano** convertidos a km²/ano | km²/ano | 1985–2015, anual | **não** (taxa ≥ 0; o acumulado é monotônico por construção) | A | tiles da AOI presentes (`wsf_evolution_S18E032/E034`); **tiles dos controles ausentes** |
| `S_VIIRS_soma` ⟨EMENDADO 2026-09-08 · E3: série não existe em nível A; substituída por `S_HARM_soma`⟩ | VIIRS DNB anual (VNP46A4 ou EOG annual v2): **soma de radiância** sobre polígono de geometria fixa | nW·cm⁻²·sr⁻¹ | 2012–2025, anual | **sim** | A | **ausente** |
| `S_DMSP_soma` ⟨EMENDADO 2026-09-08 · E3: excluída, nível C⟩ | DMSP-OLS calibrado v4: soma de DN sobre o mesmo polígono | DN·pixel | 1992–2013, anual | sim | A | **ausente** |
| `S_HARM` ⟨EMENDADO 2026-09-08 · E2: é Chen/Yu 2021, nível **A**, e passa a ser a série primária de luz⟩ | DMSP–VIIRS harmonizado (Li et al. 2020) | — | 1992–2018+ | sim | **B** | ausente — só validação, nunca sustenta número publicado |
| `S_SUST` | `estoque_sustentado_pelo_ano_km2` (ADR 0013 §1) | km² | 6 anos-âncora | sim (cai em 2020) | A, **experimental** | `data/processed/causal/decomposicao_permanencia_urbano.csv` |
| `S_GHSL` | GHSL BUILT-S R2023A, épocas **observadas** | km² | 2000–2020, passo 5 anos | não (não-decrescente) | A | presente até E2020; **E2025 proibido (extrapolado)** |

⟨EMENDADO 2026-09-08 · E6: os recortes em disco são retângulos; ADM2 vira sensibilidade⟩
**Regra de geometria, fixada agora para impedir contaminação cruzada:** a soma de luz é
calculada sobre **polígono administrativo fixo** (COD-AB ADM2 `MZ0501` Cidade de Tete;
`MZ0510` Distrito de Moatize; homólogos dos cinco controles), **nunca** sobre a máscara de
construído do ano. Somar luz dentro de uma máscara que cresce por catraca importaria a catraca
para dentro da série de luz e produziria crescimento de luz por construção. Reportar também a
soma sobre a AOI-retângulo de `config/study.yaml` como sensibilidade de recorte.

**Cruzamento de geometria e população:** por `config/unidades.yaml`, o cruzamento COD-AB × COD-PS
é por **nome + província**, nunca por P-code (MZ1006 é Matutuine no COD-AB). Vale para os
controles também.

### 1.2 Atribuição série → quebra

⟨EMENDADO 2026-09-08 · E4/E8: janela das luzes começa em 2013; pré-janela de 2016 cai a 3 pontos; quadro consolidado em E8⟩

| Quebra | Série primária | Unidade | Janela de estimação | Pré / pós | Justificativa e limite |
|---|---|---|---|---|---|
| **2005** (concessão Vale 2004, licença 2006) | `S_WSF_taxa` | km²/ano | 1993–2015 | 12 / 11 | Único trecho com ΔR2/Δbruta ≈ 0,96–0,93 (ADR 0013 §1): o sinal bruto corrobora quase 1:1. Lida como **taxa de incorporação de solo**, não estoque. |
| **2011** (operação da mina, mai/2011) | `S_WSF_taxa` | km²/ano | 1996–2015 | 15 / 5 | **Potência baixa e declarada:** 5 observações pós. Quebra de **nível** reportada com IC; quebra de **inclinação** reportada como não conclusiva por construção da janela, não como nula. |
| **2016** (bust do carvão) | `S_VIIRS_soma` | nW·cm⁻²·sr⁻¹ | 2012–2025 | 4 / 10 | As luzes **podem cair** — é a única série disponível capaz de detectar bust. Pré-janela de 4 pontos: **inclinação pré não é estimável em VIIRS**; ver 1.3. |
| **2022** (saída da Vale / Vulcan) | `S_VIIRS_soma` | nW·cm⁻²·sr⁻¹ | 2012–2025 | 10 / 4 | Quebra de **nível** estimável com IC largo. **Quebra de inclinação em 2022: não estimável** com 4 pontos pós — declarado, não substituído. |

### 1.3 Quebras que **não são estimáveis** com o que existe — dito, não improvisado

⟨EMENDADO 2026-09-08 · E3/E4: item 3 agravado (2005 e 2011 perdem qualquer corroboração de luz); item 4 sem objeto (premissa da conciliação própria tornou-se impossível); critério de saturação DN=63 retirado por falta de objeto⟩

1. **2016 e 2022 sobre área construída: não estimáveis.** O WSF Evolution termina em **2015**;
   o GHSL observado termina em **2020** com passo quinquenal (dois pontos pós-2015, ambos
   não-decrescentes) e o E2025 é extrapolado. A série própria está proibida (ADR 0013). Não há
   substituto. **Não será construído um proxy de área pós-2015 para preencher esta lacuna.**
2. **Inclinação pré-2016 em VIIRS: não estimável.** 2012–2015 são 4 pontos, e o primeiro ano de
   VIIRS anual tem calibração distinta. A quebra de 2016 será estimada **apenas como nível**,
   com a inclinação pré fixada pelo trecho DMSP quando as duas séries forem conciliáveis (ver 4).
3. **2005 e 2011 sobre luzes: secundárias, com ressalva de sensor.** `S_DMSP_soma` cobre 1992–2013
   e as suporta em princípio, mas atravessa trocas de satélite (F14/F15/F16) e sofre saturação em
   núcleos brilhantes. Serão reportadas como **corroboração**, com efeito fixo de satélite-ano e
   com verificação prévia de saturação (fração de pixels em DN = 63 dentro do polígono; se
   > ⟨PLACEHOLDER: limiar a fixar em 5 %⟩ em qualquer ano, a série é descartada para aquele
   polígono e isso é publicado).
4. **Emenda ao par DMSP↔VIIRS:** não haverá empilhamento das duas em uma única regressão sem
   um trecho de sobreposição estimado (2012–2013). Se a sobreposição de 2 anos não sustentar a
   conciliação — critério em 4.4 — as duas séries são analisadas **separadamente** e nenhuma
   quebra é atribuída ao par.
5. **Placebo de capacidade de observação sobre a série própria (ADR 0008 §5):** existe apenas
   nos 6 anos-âncora. Com 6 pontos não se ajusta um modelo segmentado de 4 parâmetros. Ele será
   reportado como **série descritiva pareada**, não como teste de quebra. Declarado, não maquiado.

---

## 2. Séries interrompidas — forma funcional, autocorrelação, nível e inclinação

### 2.1 Especificação primária

Para uma série `y_t` e uma quebra em `t0`:

```
log(y_t + c) = β0 + β1·(t − t0) + β2·D_t + β3·D_t·(t − t0) + ε_t
D_t = 1 se t ≥ t0, 0 caso contrário
```

- **`β2` é o NÍVEL:** salto imediato no ano da quebra, em log-pontos. Interpretação:
  descontinuidade de patamar.
- **`β3` é a INCLINAÇÃO:** mudança na taxa **anual** de crescimento após a quebra, em
  log-pontos/ano. Interpretação: mudança de ritmo.
- Reportar sempre os dois separadamente e **nunca** somar um ao outro em uma única "magnitude
  do efeito". Um salto de nível sem mudança de inclinação e uma mudança de inclinação sem salto
  são fenômenos distintos e o mandato pergunta pelos dois.
- `c` = constante de deslocamento para admitir zeros na taxa do WSF. Fixada **agora** como
  `c = 1 pixel convertido a km²` (0,0009 km² a 30 m). Não será recalibrada depois de ver a série.
- Especificação alternativa pré-registrada para `S_WSF_taxa`, que é **contagem**: regressão
  quasi-Poisson com log-link sobre `n_pixels(t)`, offset = área do polígono, mesmos regressores.
  Se o sinal de `β2` ou `β3` diferir entre log-OLS e quasi-Poisson, **as duas são publicadas** e
  a conclusão é registrada como sensível à forma funcional.

### 2.2 Autocorrelação — tratada, e o que fica por tratar

1. **Erros-padrão Newey–West (HAC)** com defasagem máxima pela regra de Andrews/Newey–West
   `L = floor(4·(T/100)^(2/9))`, calculada de `T` e **não escolhida olhando o resultado**.
2. **Prais–Winsten AR(1)** como especificação de sensibilidade. Se `β2`/`β3` trocarem de sinal
   entre HAC e AR(1), a conclusão é declarada não robusta.
3. **Diagnósticos publicados sempre:** Durbin–Watson, Breusch–Godfrey (ordens 1 e 2), ADF sobre
   o resíduo. Não são portões — são contexto obrigatório junto do coeficiente.
4. **O que fica por tratar, declarado:** com `T ≤ 23` (WSF) e `T = 14` (VIIRS), HAC é conhecido
   por sub-cobrir. Não há correção que resolva isso; a consequência é que os IC são **piso** de
   incerteza, não teto. Nenhum resultado de §5.4 será apresentado como "significativo" sem esta
   frase ao lado.
5. **Donut de ±1 ano em torno da quebra** como sensibilidade pré-registrada, porque o WSF é
   ano-de-**primeira detecção** e portanto atrasa a construção física por um intervalo não
   medido. Reestimar excluindo `t0−1, t0, t0+1` e publicar as duas versões.

### 2.3 O que conta como nível e o que conta como inclinação — regra de leitura

| Série | Um `β2 > 0` significa | Um `β3 < 0` significa | O que **não** pode significar |
|---|---|---|---|
| `S_WSF_taxa` | a cidade passou a incorporar solo mais rápido no ano da quebra | a incorporação desacelerou | nunca "a área construída caiu": a série é taxa não-negativa |
| `S_VIIRS_soma` | salto de radiância agregada | desaceleração da radiância | não significa PIB, não significa emprego, e não distingue luz industrial de luz residencial sem a máscara de pegada de ADR 0011 |
| `S_SUST` | — | — | experimental; não sustenta conclusão sozinha |

⟨EMENDADO 2026-09-08 · E11: executada em `decomposicao_luz.py`; **não é partição** — luz a ~500 m contra camadas a 30 m obriga a publicar duas envoltórias, e só o sinal comum às duas é afirmável⟩
**Decomposição de luz obrigatória:** `S_VIIRS_soma` é publicada em três recortes mutuamente
exclusivos — dentro da pegada `industrial` (ADR 0011/0014, já sem R2), dentro de `urbano`
fora da pegada, e o restante do polígono. Sem isso, uma queda de luz por fechamento de planta
seria lida como queda de atividade urbana.

---

## 3. DiD e controle sintético contra as cinco capitais de `config/study.yaml:81`

### 3.1 Justificativa por escrito de cada inclusão e de cada exclusão

Exigida por §3 e §5.4 do mandato e submetida a segunda opinião obrigatória do
`revisor-adversarial`. O critério único é: **a cidade sofreu, no período 1997–2025, um choque
de investimento extrativo ou logístico correlacionado com o ciclo carbonífero de Moatize?**
Se sim, ela é tratada, não controle.

**Incluídas (5):**

| Cidade | Por que serve de controle | Risco residual declarado |
|---|---|---|
| **Chimoio** (Manica) | Capital provincial, interior, economia agro-comercial; no corredor da Beira mas **a montante do carvão**, sem terminal nem mina. Vizinha de Tete em porte e clima. | O corredor da Beira transportou carvão de Moatize (linha do Sena reabilitada). Chimoio não é terminal nem origem, mas fica sobre o eixo. **É o doador com maior risco de contaminação por difusão do tratamento** — a ser testado por leave-one-out (3.5). |
| **Quelimane** (Zambézia) | Capital provincial costeira, base agrícola (coco, arroz), porto de pequeno calado sem função no escoamento do carvão. | Nenhum ciclo extrativo no período. Dinâmica de população própria (cheias, ciclones) que não é o tratamento mas é choque idiossincrático. |
| **Lichinga** (Niassa) | Capital provincial de interior, a mais isolada; sem mineração de escala nem corredor operante no período. | O ramal Nacala–Lichinga é histórico e não foi reabilitado pelo Corredor de Nacala do carvão. Risco baixo. |
| **Xai-Xai** (Gaza) | Capital provincial do sul, agrícola e de remessas da África do Sul; nenhuma exposição ao carvão. | Choque de remessas sul-africanas é ortogonal ao carvão — bom para o contrafactual, mas introduz variância própria. |
| **Inhambane** (Inhambane) | Capital provincial de base turística e de serviços; sem exposição ao ciclo carbonífero. | **Gás de Pande/Temane** está na província, a ~450 km, com terminal em Vilanculos/Temane e não em Inhambane cidade. Risco declarado como baixo, **mas é o segundo candidato a leave-one-out**. |

**Excluídas (3), com o motivo:**

| Cidade | Motivo da exclusão | Consequência de a incluir |
|---|---|---|
| **Pemba** | Boom de gás/LNG da Bacia do Rovuma a partir de ~2010, com investimento de escala comparável ao de Moatize, e conflito armado em Cabo Delgado desde 2017 com deslocamento massivo. **Tratamento contaminado nas duas pontas.** | O sintético incorporaria um segundo boom no contrafactual e **subestimaria** o efeito de Moatize; o deslocamento pós-2017 introduziria um choque de população não relacionado. |
| **Nampula** | Efeito Corredor de Nacala — exposição parcial ao **mesmo** choque carbonífero (a linha de Moatize a Nacala atravessa a província). | Difusão do tratamento no grupo de controle: viés para zero. |
| **Nacala** | Terminal de exportação do carvão de Moatize; exposição **direta** ao choque tratado. | Seria o caso mais grave: um doador tratado. Além disso, Nacala é **cidade-porto e não capital provincial** — não é comparável no eixo administrativo pelo qual os dados do INE/COD são organizados. |

**Nota de honestidade sobre a exclusão:** as três exclusões são teoricamente corretas e
**reduzem o pool de doadores de 8 para 5**, o que tem custo estatístico direto e é a razão do
piso de p em 3.6. O custo é aceito porque um doador tratado enviesa o ponto; um pool pequeno
apenas alarga o intervalo.

### 3.2 Como o pool de doadores é montado

1. Geometria: COD-AB ADM2 de cada uma das cinco capitais, cruzada por **nome + província**.
2. Desfecho, dois painéis independentes:
   - ⟨EMENDADO 2026-09-08 · E1: os 5 tiles chegaram; o DiD de área é executável⟩
   - **Painel A (área):** `S_WSF_taxa` por cidade, anual 1993–2015. **Pré-requisito de dados não
     satisfeito:** os tiles do WSF Evolution dos cinco controles **não estão em `data/raw/`**.
     Os tiles necessários (convenção de canto inferior-esquerdo, passo 2°, conforme os dois já
     espelhados) são ⟨PLACEHOLDER: lista a confirmar no catálogo do DLR antes do download⟩.
     **Sem esses tiles não há DiD de área. Nenhum substituto será improvisado.**
   - **Painel B (luz):** `S_VIIRS_soma` (2012–2025) e `S_DMSP_soma` (1992–2013) pelos mesmos
     polígonos.
3. Normalização: cada série é dividida pela sua média no período pré-tratamento da respectiva
   quebra, para que o sintético não persiga escala em vez de trajetória. Publicar também a
   versão em log-nível.
4. Preditores do sintético: apenas os **valores defasados do próprio desfecho** em anos
   pré-tratamento, mais área do polígono. **Nenhum preditor pós-tratamento**, e nenhum preditor
   derivado da classificação própria (que carrega catraca e viés de observação).
5. Pesos: SCM padrão (Abadie–Diamond–Hainmueller), otimização com `controle_sintetico.seed: 13579`.
   Pesos não-negativos, somando 1, sem extrapolação.

### 3.3 Tendência paralela pré-2005 — **testada**, não assumida

Três testes, todos sobre a janela **1993–2004** (Painel A) e **1993–2003** (Painel B/DMSP):

- **T1 — interação unidade × tendência linear.** Regressão do desfecho em log sobre efeitos fixos
  de unidade, efeitos fixos de ano e `unidade × t` restrita ao pré-período. **Teste F conjunto**
  de que todos os coeficientes `unidade × t` são nulos, com erros agrupados por cidade
  (5 controles + 1 tratado = 6 clusters ⇒ correção de Bell–McCaffrey e **wild cluster bootstrap**
  com `bootstrap.seed: 97531`, 1000 reamostragens; com 6 clusters, o assintótico é inválido e
  isso é declarado, não contornado).
- **T2 — event study com leads.** Coeficientes ano a ano relativos a 2004 (ano-base), para
  1996–2003. Publicados como gráfico e como tabela com IC95.
- **T3 — RMSPE pré-tratamento do sintético**, comparado à distribuição dos RMSPE pré dos
  placebos in-space.

**A tendência paralela é uma hipótese sobre o pré-período que nenhum teste pode confirmar; os
três acima só podem falhá-la.** Um F que não rejeita não é evidência de paralelismo — é ausência
de evidência contra, com a potência de 6 unidades e ≤12 anos. Esta frase entra no artigo.

### 3.4 Critério declarado de fracasso — escrito antes de ver o dado

O contrafactual **é declarado não sustentado**, e nenhuma estimativa de DiD ou SCM é publicada
como causal (só como descrição), se **qualquer** um destes ocorrer:

- **F1** — T1 rejeita a nulidade conjunta das interações `unidade × t` a **p < 0,10** (wild cluster
  bootstrap). Limiar frouxo de propósito: aqui o erro caro é *aceitar* paralelismo falso.
- **F2** — em T2, **dois ou mais** leads consecutivos têm IC95 que exclui zero, ou o teste conjunto
  dos leads rejeita a p < 0,10.
- **F3** — RMSPE pré-tratamento do sintético > **0,5 ×** o desvio-padrão pré-tratamento da série
  tratada. O sintético que não reproduz o pré não pode reproduzir o contrafactual.
- **F4** — os pesos do sintético concentram **> 0,80 em um único doador**. Nesse caso o "sintético"
  é uma cidade só, e o resultado é reportado como comparação bilateral, não como sintético.
- **F5** — a razão RMSPE pós/pré de Tete **não** fica em 1º ou 2º lugar na distribuição das 6
  unidades no placebo in-space (isto é, `p ≥ 2/6 = 0,33`).
- **F6** — o efeito estimado inverte de sinal entre Painel A e Painel B para a mesma quebra sem
  explicação mecanicamente declarada.
- **F7** — no leave-one-out (3.5), a remoção de **um** doador altera o efeito estimado em mais de
  ⟨PLACEHOLDER: 50 % da magnitude do efeito principal — critério fixado agora em termos relativos,
  o valor absoluto só existe depois da estimativa⟩.

**Compromisso:** se F1–F7 dispararem, o resultado publicado é "o contrafactual não se sustenta
com este pool de doadores", e não uma reespecificação buscada até passar. Qualquer
reespecificação posterior a ver o dado é registrada como **exploratória** em ADR próprio, com
esta seção citada.

### 3.5 Robustez pré-registrada

- **Leave-one-out** por doador (5 execuções), com atenção especial a Chimoio (corredor da Beira)
  e Inhambane (gás de Pande/Temane) — os dois riscos residuais declarados em 3.1.
- **In-time**: SCM reestimado com quebra falsa em 1999 (ver §4, P2).
- **Sensibilidade de recorte**: polígono ADM2 versus AOI-retângulo.
- **Sensibilidade de ajuste censitário**: 3,7 % de subenumeração de 2017 aplicada **também aos
  controles**, conforme `config/study.yaml:censo_2017`, com as duas versões publicadas.

### 3.6 O piso de p — limite aritmético declarado agora

Com 1 tratado e 5 doadores, a inferência por permutação tem **p mínimo = 1/6 ≈ 0,167**.
**Nenhum resultado desta Fase 3 pode atingir p < 0,05 por permutação.** Isso não é uma falha do
desenho: é o que o pool honesto permite. Qualquer p < 0,05 que apareça no relatório virá de
inferência assintótica sobre 6 clusters e será marcado como **não confiável**.

---

## 4. Os quatro placebos obrigatórios

Nenhum contrafactual é publicado sem os quatro. Um contrafactual sem placebos é reprovado
(§5.4 do mandato). Cada um responde a uma explicação alternativa **diferente**; passar em três
não substitui o quarto.

### 4.1 P1 — Placebo espacial (5 execuções, `n_placebos_espaciais: 5`)

- **O que faz:** trata cada uma das cinco capitais de controle como se fosse a tratada, com as
  outras quatro + Tete como doadoras, e estima a mesma quebra.
- **O que testa:** se a quebra é específica da exposição ao boom carbonífero ou é um choque
  nacional (política, moeda, ciclo de crédito, censo) que atinge todas as capitais.
- ⟨EMENDADO 2026-09-08 · E10: ramo cujo coeficiente de referência de Tete tem IC95 que inclui zero é **vazio**; P1 passa a exigir IC próprio que exclua zero, como P2 sempre exigiu⟩
- **Falha se:** duas ou mais cidades de controle exibirem quebra do mesmo sinal e de magnitude
  ≥ 50 % da de Tete; ou se a razão RMSPE pós/pré de Tete não ficar no topo (F5).
- **O que a falha invalida:** a **atribuição** do efeito ao carvão. O efeito pode existir e ser
  nacional. A conclusão passa a ser "houve quebra, não é atribuível ao tratamento".

### 4.2 P2 — Placebo temporal (4 execuções, `n_placebos_temporais: 4`)

- **O que faz:** para cada uma das quatro quebras reais, reestima o mesmo modelo com a quebra
  deslocada para dentro do período **pré-tratamento** correspondente. Anos falsos fixados agora,
  sem discricionariedade posterior: **1999** (para a quebra de 2005), **2008** (para 2011),
  **2014** (para 2016) e **2019** (para 2022).
  Nota declarada: 2014 e 2019 caem em anos de VIIRS já disponível; 2008 cai no WSF; 1999 cai
  no WSF e no DMSP.
- **O que testa:** se o modelo segmentado detecta quebras em qualquer ano — isto é, se a
  tendência está mal especificada e a "quebra" é curvatura não modelada.
- ⟨EMENDADO 2026-09-08 · E10: o ramo só é avaliado se o coeficiente **real** de referência tiver IC95 que exclua zero; ramo vazio ⇒ "não estimável"⟩
- **Falha se:** o placebo produzir `β2` ou `β3` de mesmo sinal e magnitude ≥ 50 % do real, com IC
  que exclua zero.
- **O que a falha invalida:** a **datação** do efeito, e portanto a especificação. Não sobra
  "efeito em outro ano": sobra "o modelo não identifica ano".

### 4.3 P3 — Placebo de capacidade de observação (exigido por `docs/ADR/0008` §5)

- **O que faz:** estima a mesma quebra sobre a **mediana de observações válidas por pixel por
  ano** (3 / 4 / 4 / 10 / 31 / 42 nos anos-âncora) e, para as luzes, sobre o **número de noites
  válidas por composto anual**.
- **O que testa:** se a quebra é aumento da capacidade de medir, e não do fenômeno. O viés medido
  em ADR 0008 é de **+1,25 %/ano**, da mesma ordem do efeito procurado.
- **Limitação declarada:** para a série própria só existem **6 pontos** — não se ajusta modelo
  segmentado de 4 parâmetros. Será reportado como série pareada e correlação com o desfecho, não
  como teste de quebra. Para VIIRS, a contagem de noites válidas é anual e o teste completo é
  possível.
- **Falha se:** a série de capacidade exibir quebra no mesmo ano e mesmo sinal (VIIRS), ou se a
  correlação entre capacidade e desfecho nos 6 anos-âncora exceder ⟨PLACEHOLDER: |ρ| > 0,8,
  limiar fixado agora⟩.
- **O que a falha invalida:** o **desfecho** — a série mede o instrumento. Nada é salvável por
  reespecificação; só por outra fonte.

### 4.4 P4 — Placebo de radiometria da paisagem (exigido por `docs/ADR/0013`)

- **O que faz:** estima a mesma quebra sobre a **fração da AOI com NDVI de estação seca ≥ 0,30**.
  Valores conhecidos nos anos-âncora (ADR 0013 §3): 10,8 / 11,1 / 76,7 / 90,9 / 27,6 / 6,1 %.
- **Por que é o placebo certo:** essa fração é **radiometria de paisagem** — sensor, calibração e
  pluviosidade do ano. **Não tem relação nenhuma com carvão.** Se a quebra aparecer também aí, é
  o ano, e não o tratamento.
- ⟨EMENDADO 2026-09-08 · E1(iii): a série anual de NDVI **não** foi construída; P4 fica descritivo, como esta linha já previa⟩
- **Pré-requisito de dados, declarado:** com 6 pontos o teste é descritivo. Para ser um teste de
  quebra de verdade, é preciso construir a série **anual** de NDVI de seca da paisagem,
  1997–2025, a partir do mesmo arquivo Landsat/Sentinel — artefato novo:
  `data/processed/causal/ndvi_paisagem_anual.csv`. **Se essa série anual não for construída, P4
  é reportado como descritivo e essa insuficiência é publicada**, não silenciada.
- **Falha se:** a série de radiometria exibir quebra de mesmo sinal no mesmo ano com IC que
  exclua zero; ou, na versão descritiva, se o padrão de sinal por fase coincidir com o do desfecho.
- **O que a falha invalida:** a **medição** e, por tabela, ADR 0014 — significaria que a correção
  do limiar relativo não bastou e que a série de desfecho ainda é o ano verde, não a cidade.

### 4.5 Regra de agregação dos quatro

A publicação de qualquer efeito causal exige **P1, P2, P3 e P4 reportados**, cada um com seu
veredito explícito (`passa` / `falha` / `não estimável — motivo`). "Não estimável" é resultado
admissível e vai para a tabela; "não rodado" não é.

---

## 5. Elasticidades população–luz e área–luz por fase

### 5.1 O que é estimável sem circularidade

| Elasticidade | Fase | Estimável? | Fonte de cada lado | Ressalva vinculante |
|---|---|---|---|---|
| **área–luz** | linha de base (1997–2005) | **sim, parcialmente** | `S_WSF_taxa` × `S_DMSP_soma` | ambos anuais; DMSP sujeito a troca de satélite e saturação; é elasticidade **taxa de incorporação × luz**, não estoque × luz |
| **área–luz** | implantação (2005–2011) | **sim, parcialmente** | idem | idem |
| **área–luz** | boom (2011–2015) | **sim, parcialmente**, 5 pontos | idem | potência mínima; reportar como descritivo |
| **área–luz** | bust (2015–2019) | **NÃO** | não existe série de área utilizável pós-2015 | WSF termina 2015; GHSL observado é não-decrescente e quinquenal; série própria proibida (ADR 0013); par 2015–2020 proibido |
| **área–luz** | transição (2019–2025) | **NÃO** | idem | idem, agravado: GHSL E2025 é extrapolado |
| **população–luz** | qualquer fase | **NÃO** | população em nível A só existe em **2017** (COD-PS, observado) e **2025** (COD-PS, projeção do INE, *modelado*) | dois pontos, um deles modelado; 1997 é nível B (UNSD DYB), 2007 é nível C (INE via Wayback, sem licença localizável) |

### 5.2 Consequência direta para H4 — e por que ela **não é reabilitada aqui**

H4 afirma o **descolamento entre luz e população/área após ~2016**. As duas células que
testariam H4 — área–luz no bust e na transição — são exatamente as **não estimáveis**. E a
elasticidade população–luz não é estimável em fase nenhuma.

O que **é** estimável é a **trajetória isolada das luzes** pós-2016 (§1.2), que é condição
**necessária e não suficiente** para H4. Se as luzes caírem, H4 continua não testada — apenas
não refutada por esse lado. Isso será escrito assim no artigo. `S_SUST` (6 pontos,
experimental, com o viés de ADR 0008 e a anomalia de 2015 sem correção) pode ser pareado às
luzes **apenas como ilustração declaradamente experimental**, jamais como teste de H4.

### 5.3 Causalidade reversa luz ↔ população — declarada, não resolvida

Luz é usada como proxy de atividade, e atividade atrai população, que produz luz. Não há
instrumento disponível nesta AOI que rompa o ciclo. O desenho **não** tenta resolvê-lo por
defasagem (uma defasagem de 1 ano não identifica nada com T = 14) e **não** usa VAR/Granger,
que com esta amostra produziria resultado sem conteúdo. A elasticidade área–luz é reportada
como **associação por fase**, com a palavra "elasticidade" acompanhada sempre de "de associação".

### 5.4 Especificação, quando estimável

Regressão em log-log por fase, com erros HAC, `log(luz_t) = α_f + η_f·log(taxa_área_t) + ε_t`,
`η_f` reportado por fase com IC95 por bootstrap em blocos (`bootstrap.seed: 97531`, 1000
reamostragens, tamanho de bloco ⟨PLACEHOLDER: regra `T^{1/3}` arredondada, calculada de T⟩).
Um `η_f` estimado sobre ≤ 5 pontos é publicado com a contagem de pontos na mesma célula da tabela.

---

## 6. §5.5 e §5.6.7 — Cenários a 2035 e 2040

**Regra de rótulo, sem exceção:** todo número de cenário é `modelado`. Cenário é cenário, não
previsão. Nenhuma trajetória de cenário entra em tabela sem o selo e sem a premissa ao lado.

### 6.1 Os três cenários e o que os distingue

| Cenário | Mecanismo narrativo | Alavanca quantitativa |
|---|---|---|
| **Continuidade** | mineração segue sob novos operadores (Vulcan, ICVL, Jindal); volumes e emprego próximos aos de 2019–2025 | migração líquida ≈ tendência recente |
| **Declínio** | esgotamento gradual, retração de emprego direto e indireto, saída de serviços | migração líquida negativa |
| **Diversificação** | energia (Cahora Bassa, Mphanda Nkuwa), logística do corredor, agroindústria | migração líquida positiva, com composição setorial distinta |

### 6.2 Proveniência de cada parâmetro — estimado, premissa, ou premissa contaminada

| Parâmetro | Origem | Classificação | Marca obrigatória |
|---|---|---|---|
| População-base 2017 | COD-PS ADM2, IV RGPH | **observado**, nível A | ajustada e não ajustada por 3,7 % |
| População 2025 | COD-PS vintage 2025 (projeção do INE) | **modelado** | risco de circularidade já registrado em `stats_by_year_by_unit.csv`: usar a projeção do INE como base e depois projetar sobre ela reencena a premissa do INE |
| Taxa de crescimento 2025–2040 por cenário | **premissa declarada** | premissa | ⟨PLACEHOLDER: três taxas, fixadas por regra explícita a partir da taxa do INE ± um delta declarado, nunca por ajuste ao resultado desejado⟩ |
| Migração líquida | **premissa declarada**, variável de sensibilidade | premissa | análise de sensibilidade obrigatória em três níveis por cenário (9 trajetórias) |
| Intensidade de uso (m²/hab) | série própria de área construída | **premissa contaminada** | ⚠️ **MARCADO**: a área vem de série com catraca (ADR 0013). Todo resultado de área construída projetada carrega esta marca |
| Área construída projetada | população × intensidade de uso | **derivado de premissa contaminada** | ⚠️ **MARCADO**; reportar em paralelo a variante ancorada na taxa de incorporação do WSF até 2015, que tem outro viés (declarado) e não o mesmo |
| Demanda de água, saneamento, habitação | taxas de acesso do Censo 2017 × domicílios projetados | premissa + observado nível **C** para as taxas do INE | domicílios sem fonte A (ADR 0010): a conversão pessoas→domicílios é modelada e herda a incerteza |
| Perda de área agrícola por cenário | classificação de cultivo | **parcialmente não determinável** | `cultivo_sequeiro` reprovado (ADR 0012, reforçado por ADR 0014: kappa −0,065, Jaccard 0,001–0,002 contra GLAD). Só `cultivo_irrigado`/várzea entram, com acurácia do usuário **0,556 ± 0,344** |
| Domicílios afetados | perda de área × densidade domiciliar | derivado | regra pré-registrada em 6.4 |
| Áreas de proteção compatível | várzea (HAND ≤ 10 m, dist. rio ≤ 1000 m) menos envelope de expansão projetado | derivado, geométrico | churn de 31–54 % declarado; entregue como zona, não como parcela |

### 6.3 Estrutura do modelo de projeção

- Componente demográfico: geométrico por fase **e** coorte-componente simplificado (§5.3), com
  migração líquida como alavanca de cenário. Publicar os dois; divergência entre eles é
  resultado, não erro a esconder.
- Horizontes: 2035 e 2040 (`config/study.yaml:cenarios.horizontes`).
- Sensibilidade à migração líquida: 3 níveis × 3 cenários = 9 trajetórias, todas publicadas.
  Nenhuma trajetória "central" é destacada visualmente sobre as outras no app.
- **Nada de GHSL 2025/2030 como âncora.** Épocas extrapoladas não podem ancorar extrapolação:
  seria extrapolar uma extrapolação e apresentá-la como observação.

### 6.4 Regra pré-registrada contra o número plausível

Se o intervalo de 95 % de **área agrícola perdida** ou de **domicílios afetados** incluir zero,
ou se a acurácia do usuário da classe envolvida for < ⟨PLACEHOLDER: 0,60, limiar fixado agora,
sem retroceder para acomodar resultado⟩, o valor é publicado como **"não determinável com esta
série"** — não como estimativa pontual com ressalva textual. A ressalva textual não impede que
o número circule; a recusa impede (mesmo argumento de ADR 0008, alternativas rejeitadas).

---

## 7. §5.6.4 — Logit espacial de conversão cropland→construído: **condicionado, não agendado**

O desenho existe, mas o pré-requisito não está satisfeito e isso é declarado antes de qualquer
execução.

- **Especificação pretendida:** logit de `conversão(pixel) ∈ {0,1}` entre dois anos-âncora, com
  covariáveis de acessibilidade (distância a via OSM, ao centro de cada núcleo, à pegada
  minerária de Maus et al.), declividade (Copernicus DEM GLO-30), várzea (HAND ≤ 10 m e
  distância ao rio ≤ 1000 m, `config/study.yaml:zoneamento_agricola`) e efeito de fase.
  Amostragem: `logit_espacial.seed: 24680`, `n_amostras_negativas: 10000`.
- **Autocorrelação espacial, tratada explicitamente:** (a) erros-padrão agrupados em blocos
  espaciais (grade regular de ⟨PLACEHOLDER: lado do bloco, fixado como ≥ 2× o alcance do
  variograma do resíduo, medido antes de estimar⟩); (b) diagnóstico de **I de Moran** sobre os
  resíduos, publicado; (c) especificação alternativa com termo autologístico (proporção de
  vizinhos convertidos em janela 3×3) — que **canibaliza** parte do efeito das covariáveis e por
  isso é publicada ao lado, nunca no lugar.
- **O que NÃO será feito, e dito:** nenhum modelo SAR/CAR de máxima verossimilhança completo
  sobre a grade inteira (custo e, mais importante, não corrige a fonte de erro dominante aqui);
  nenhuma correção de autocorrelação que ainda assim salve um sinal com o churn abaixo.
- **Bloqueio declarado — dois, independentes:**
  1. **Churn de 31–54 %** na identidade pixel a pixel de `construido` entre anos-âncora
     consecutivos (ADR 0013 §2/§3). O desfecho do logit é literalmente "este pixel mudou", e
     entre um terço e metade dos pixels trocam de identidade sem que a cidade mude.
  2. **`cultivo_sequeiro` não é defensável como cropland** (ADR 0012, confirmado por ADR 0014
     após a correção de limiar). Sem a classe de origem, "cropland→construído" não é definível.
- **Condição para rodar:** a opção **C** de `docs/ADR/0013` (limiar relativo propagado *mais* uma
  abordagem de cultivo que não seja a fenologia bianual reprovada) executada e aprovada. É
  decisão do orquestrador, não deste desenho.
- **Se a condição não for satisfeita:** §5.6.4 é entregue como **"não determinável com esta
  série"**, com este parágrafo como justificativa, e H5 idem — pelo mesmo argumento com que
  ADR 0012 reprovou `cultivo_sequeiro`. Um logit rodado sobre um desfecho com 31–54 % de churn
  produziria coeficientes significativos e sem conteúdo.

---

## 8. O que este desenho **não consegue responder**

Escrito antes de estimar, para que nenhuma dessas perguntas apareça respondida depois.

1. **Se o estoque de área construída acelerou.** Nem a série própria (catraca R2), nem o WSF
   (ano de primeira detecção), nem o GHSL (não-decrescente) fornecem estoque sem monotonicidade
   imposta. **H1 só existe como hipótese sobre taxa de incorporação de solo**, até 2015.
2. **Se a área construída contraiu em algum momento.** Nenhuma série disponível é capaz de
   detectar contração. A ausência de contração nos resultados é uma propriedade do dado.
3. **H4 (descolamento luz × área/população após 2016).** As duas elasticidades que a testariam
   não são estimáveis (§5.1). H4 chega à Fase 3 **rebaixada** e sai rebaixada: será reportada
   como não testada, com a trajetória isolada das luzes ao lado e a advertência de que
   necessária ≠ suficiente. **Este desenho não a reabilita.**
4. **H6 (agricultura urbana como amortecedor no bust).** `cultivo_sequeiro` está reprovado; a
   dimensão domiciliar depende de censos de nível C e de domicílios sem fonte A (ADR 0010).
   Rebaixada, e mantida rebaixada.
5. **H5 (conversão preferencial das terras agrícolas acessíveis).** Bloqueada pelos mesmos dois
   pré-requisitos do §7.
6. **Qualquer quebra de área em 2016 ou 2022.** Sem série de área utilizável pós-2015 (§1.3).
7. **Significância convencional.** p mínimo por permutação = 1/6 ≈ 0,167 (§3.6).
8. **A direção causal entre luz e população.** Declarada, não resolvida (§5.3).
9. **A separação entre crescimento de "25 de Setembro" e crescimento orgânico.** O povoado não
   tem geometria localizada (`config/unidades.yaml`), a camada `urbano` o inclui sem poder
   separá-lo, e a magnitude do vazamento não é estimável.
10. **Reabilitação de área minerária.** Indetectável neste desenho (ADR 0011 §6), mesmo depois
    da remoção de R2 de `industrial`.
11. **Qualquer efeito baseado no par 2015–2020.** Proibido; a quebra de 2016 cai entre dois
    anos-âncora contaminados e o desenho a estima **apenas** sobre luzes.
12. **Trajetórias de cenário como previsão.** São `modelado`, com premissa declarada, e três
    delas dependem de uma intensidade de uso vinda de série contaminada (⚠️ marcada em 6.2).

---

## 9. Artefatos que este desenho produzirá (caminhos reservados)

| Caminho | Conteúdo |
|---|---|
| `pipeline/03_causal/series_interrompidas.py` | ITS §2, quatro quebras, HAC + AR(1) + quasi-Poisson |
| `pipeline/03_causal/did_sintetico.py` | DiD e SCM §3, seed 13579 |
| `pipeline/03_causal/placebos.py` | P1–P4, §4 |
| `pipeline/03_causal/elasticidades.py` | §5, com as células "não estimável" explícitas |
| `pipeline/03_causal/cenarios.py` | §6, 9 trajetórias |
| `data/processed/causal/its_quebras.csv` | β0–β3, IC95, diagnósticos, por série × quebra |
| `data/processed/causal/did_sintetico_pesos.csv` | pesos por doador, RMSPE pré/pós |
| `data/processed/causal/tendencia_paralela_pre2005.csv` | T1, T2, T3 e veredito F1–F7 |
| `data/processed/causal/placebos.csv` | quatro placebos, veredito `passa`/`falha`/`não estimável` |
| `data/processed/causal/elasticidades_por_fase.csv` | com coluna `n_pontos` e coluna `estimavel` |
| `data/processed/causal/cenarios_2035_2040.csv` | selo `modelado`, coluna `premissa`, coluna `premissa_contaminada` |
| `data/processed/causal/ndvi_paisagem_anual.csv` | pré-requisito de P4 (§4.4) |

⟨EMENDADO 2026-09-08 · E1: (i) e (ii) satisfeitos; (iii) continua não satisfeito⟩

**Pré-requisitos de dados não satisfeitos na data de fixação:** (i) luzes noturnas — nenhuma
série em `data/raw/`; (ii) tiles do WSF Evolution para as cinco capitais de controle; (iii) série
anual de NDVI de paisagem para P4. Sem (i) não há quebras de 2016/2022; sem (ii) não há DiD;
sem (iii) P4 é descritivo. Nenhum substituto será improvisado para nenhum dos três.

---

## 10. Selo de pré-registro

Este documento foi fixado em **2026-09-08**, antes de qualquer série de luzes noturnas existir em
disco. Qualquer alteração posterior a §1–§5 é registrada como **emenda datada** no fim deste
arquivo, com o motivo e com a indicação de se o autor já tinha visto o dado. Uma emenda escrita
depois de ver a série e sem essa declaração invalida o pré-registro inteiro.

*(Emendas: uma, de 2026-09-08 — ver §11.)*

---

## 11. EMENDA 1 — 2026-09-08

**Declaração exigida por §10:** esta emenda foi escrita **depois** de o autor ver a série de
luzes noturnas em disco e depois de ler a verificação de integridade registrada em
`ORCHESTRATION_LOG.md` 3-04 a 3-09. Nada de §0–§9 foi reescrito. As afirmações originais
afetadas ficam onde estão e são marcadas abaixo como **emendadas**; o texto original
permanece legível para que a diferença entre o que foi pré-registrado e o que foi executado
seja auditável linha a linha.

### E1 — Os três pré-requisitos declarados em §9 foram satisfeitos

| Pré-requisito de §9 | O desenho dizia | O que mudou | Estado |
|---|---|---|---|
| (i) luzes noturnas | "nenhuma série em `data/raw/`; sem (i) não há quebras de 2016/2022" | chegaram **114 recortes = 19 anos × 6 áreas** (2000, 2005, 2008, 2010, 2011 e **anual 2012–2025**), AOI de Tete + as 5 capitais de controle | **satisfeito** |
| (ii) tiles WSF dos controles | "tiles dos controles **ausentes**; sem (ii) não há DiD" | 7 tiles em disco (`S18E032`, `S18E034` para Tete; `S20E032` Chimoio, `S18E036` Quelimane, `S14E034` Lichinga, `S26E032` Xai-Xai, `S24E034` Inhambane) | **satisfeito** |
| (iii) série anual de NDVI de paisagem para P4 | "sem (iii) P4 é descritivo" | **não** foi construída; só existem os 6 anos-âncora | **NÃO satisfeito** — P4 permanece descritivo, conforme a alternativa já pré-registrada em §4.4 |

O COD-AB também chegou, o que torna executável a regra de cruzamento por nome + província
de §1.1 — com a ressalva de geometria de **E6**.

### E2 — Atribuição do produto de luz: `S_HARM` era nível B e é nível A; o prefixo do arquivo é herança de erro

- **O desenho dizia** (§1.1, linha `S_HARM`): "DMSP–VIIRS harmonizado (**Li et al. 2020**) — nível
  **B** — só validação, nunca sustenta número publicado".
- **O que mudou:** o produto obtido não é o de Li et al. 2020. É o **NPP-VIIRS-like global
  de Chen, Z., Yu, B. et al.**, Harvard Dataverse `10.7910/DVN/YGIVCD` (CC0), método publicado
  em *ESSD* 13:889–906, **DOI 10.5194/essd-13-889-2021**. São dois harmonizados distintos, não
  dois nomes do mesmo. O `auditor-dados` classificou-o **A** (CC0 confirmada na API do Dataverse).
- **Consequência:** `S_HARM` deixa de ser "só validação" e passa a ser a **única série de luz de
  nível A** desta Fase 3 — portanto a série primária das quebras de 2016 e 2022.
- **Aviso de nomenclatura, deliberadamente não corrigido em `data/raw/`:** os arquivos têm prefixo
  `viirs_like_li2020_v2_*`. É **herança de erro** de uma delegação do orquestrador, não uma
  afirmação sobre o produto. `data/raw/` não é editado por este subagente (regra de tarefa);
  os `.meta.json` já trazem a citação correta de Chen/Yu. Toda saída desta fase cita Chen/Yu 2021
  e nenhuma cita Li et al. 2020. Quem ler o nome do arquivo tem de ler esta linha junto.

### E3 — A premissa 4 (conciliação DMSP↔VIIRS por sobreposição própria) tornou-se impossível

- **O desenho dizia** (§1.3, item 4, e §1.1 linhas `S_VIIRS_soma` e `S_DMSP_soma`): as duas séries
  seriam obtidas separadamente, em nível A, e conciliadas por um trecho de sobreposição próprio
  em 2012–2013, com critério de aceitação em §4.4.
- **O que mudou:** o `auditor-dados` **rebaixou o VIIRS VNL V2 de A para B** (`eogdata.mines.edu`
  passou a exigir login OAuth) e **excluiu o DMSP-OLS em C** (URL 404, sucessora sob o mesmo
  bloqueio). Nenhuma das duas séries existe em nível A.
- **Por quê isto importa mais do que a troca de fonte:** a conciliação DMSP↔VIIRS ainda existe —
  mas **dentro do modelo de Chen/Yu**, isto é, feita por terceiros com um método publicado e
  **não auditável por este pipeline**. O desenho havia pré-registrado a conciliação como algo que
  ele mesmo estimaria e poderia reprovar. Perdeu-se essa alavanca.
- **Consequência formal:** `S_VIIRS_soma` e `S_DMSP_soma`, como definidas em §1.1, **não existem**.
  São substituídas por uma única `S_HARM_soma` (soma de radiância anual Chen/Yu sobre geometria
  fixa). Onde §1.2, §1.3, §4 e §5 dizem `S_VIIRS_soma`, **leia-se `S_HARM_soma`**; onde dizem
  `S_DMSP_soma`, leia-se **não existe**. O critério de saturação em DN = 63 de §1.3 item 3 fica
  **sem objeto** (não há DMSP bruto para saturar) e é retirado, não flexibilizado.

### E4 — ACHADO NOVO E RESTRITIVO: a costura da harmonização é visível no dado

Isto **não estava previsto** em nenhum ponto de §0–§9. Fração de pixels acesos (`n>0`) nas seis
áreas (medida em 3-09, não estimada aqui):

| área | 2011 | 2012 | 2013 |
|---|---|---|---|
| Tete (AOI) | 13,9 % | 9,8 % | 6,5 % |
| Chimoio | 11,2 % | 7,4 % | 4,9 % |
| Quelimane | 5,3 % | 3,4 % | 2,9 % |
| Lichinga | 4,5 % | 3,2 % | 3,2 % |
| Xai-Xai | 19,1 % | 11,0 % | 7,8 % |
| Inhambane | 28,8 % | 14,4 % | 4,0 % |

As seis colapsam nos **mesmos dois anos** e todas se recuperam depois. Seis cidades a centenas de
quilômetros não têm choque comum em 2012–2013 seguido de recuperação comum: é a transição
DMSP→VIIRS embutida no produto (o DMSP floresce e satura; o VIIRS é nítido).

Na **soma de radiância** — a métrica primária de §1.1 — não há direção comum (2011→2013: Tete
+15 %, Chimoio +6 %, Quelimane +81 %, Lichinga −40 %, Xai-Xai −20 %, Inhambane −61 %), o que
**afasta um reescalonamento uniforme**. Mas uma dispersão de −61 % a +81 % em dois anos entre
**cinco capitais não tratadas** também não é economia.

**O que a emenda impõe, e é restritivo:**

1. A **janela homogênea das luzes começa em 2013**, não em 2012. `S_HARM_soma` só é usada como
   desfecho causal em 2013–2025 (**T = 13**).
2. **Emenda a §1.2, quebra de 2016:** a pré-janela cai de 4 pontos (2012–2015) para **3**
   (2013–2015). O desenho já dizia que a inclinação pré não era estimável com 4; com 3 isso
   **piora**, e a quebra de 2016 fica restrita a **nível**, com a inclinação pré ajustada sobre
   3 pontos e reportada como aritmética de três observações, não como tendência.
3. **2011 e 2012 não servem de base pré-tratamento nas luzes**, para nenhuma quebra, em nenhum
   painel, em nenhum placebo.
4. **Emenda a §1.3, item 3 — agravamento.** O desenho previa 2005 e 2011 nas luzes como
   *corroboração secundária* via DMSP. Sem DMSP em nível A, o que sobra do produto Chen/Yu antes
   de 2013 são **seis pontos irregulares** (2000, 2005, 2008, 2010, 2011, 2012) do lado
   heterogêneo da costura. **As quebras de 2005 e 2011 deixam de ter qualquer corroboração de
   luz** e ficam exclusivamente sobre `S_WSF_taxa`. Declarado, não substituído.
5. **Emenda a §4.2 (P2, placebo temporal):** o ano falso **2014** e o ano falso **2019** caem
   dentro da janela homogênea e são executáveis; **1999** e **2008** caem no WSF e são
   executáveis. Os quatro anos falsos permanecem como fixados, sem discricionariedade.

### E5 — A preocupação com 2022 enfraquece — reclassificada, não apagada

- **O que estava registrado** (3-04 e 3-05): a radiância máxima cai de 70,4 (2020) para 49,9
  (2022) e fica em 49,9 (2025); o `auditor-dados` concluiu que "não é possível, com o conjunto A
  de hoje, distinguir quebra de produto de quebra de economia em 2022", e isso viraria aviso
  obrigatório em toda figura que publicasse a quebra.
- **Evidência nova:** a **soma sobe** em 2023–2025 enquanto o **máximo cai**. Um reescalonamento
  do produto move soma e máximo na mesma direção; soma subindo com máximo caindo é **dispersão
  espacial da luz** (mais pixels acesos, menos concentração), que é fenômeno de paisagem, não de
  calibração. Além disso, 2022 está **dentro** da janela homogênea fixada em E4 — a costura
  identificada é de 2012–2013, não de 2020–2022.
- **Reclassificação, e é o que a emenda decide:** a ressalva do auditor **continua valendo e
  continua obrigatória em toda figura e tabela da quebra de 2022** — mas rebaixada de
  "indistinguível de quebra de produto" para "**quebra de produto não descartada, com evidência
  direcional contra ela**". Não é apagada. Quem publicar a quebra de 2022 publica esta linha junto.

### E6 — Geometria: a regra do polígono ADM2 de §1.1 **não é executável** com os recortes existentes

- **O desenho dizia** (§1.1): a soma de luz é calculada sobre **polígono administrativo fixo**
  (COD-AB ADM2), com a AOI-retângulo apenas como sensibilidade de recorte.
- **O que mudou:** os recortes espelhados em `data/raw/` são **retângulos**, não polígonos — um
  quadrado de 0,30° (~1.000–1.090 km²) por capital de controle e o retângulo da AOI para Tete.
  Medido nesta sessão, a fração do ADM2 contida no recorte é:

  | unidade | ADM2 | área ADM2 (km²) | área do recorte (km²) | **cobertura do ADM2** |
  |---|---|---|---|---|
  | Tete | MZ0501 | 287,1 | 2.493,8 | 0,845 (corta a oeste: ADM2 começa em 33,426° e o recorte em 33,500°) |
  | Chimoio | MZ0601 | 204,4 | 1.054,0 | 1,000 |
  | Quelimane | MZ0401 | 802,7 | 1.065,9 | 0,534 |
  | Lichinga | MZ0101 | 3.314,7 | 1.086,3 | **0,182** |
  | Xai-Xai | MZ0901 | 312,9 | 1.011,7 | 0,990 |
  | Inhambane | MZ0801 | 202,4 | 1.022,3 | 0,948 |

  Recortar de novo a grade global exigiria rebaixar ~10 GB por ano × 19 anos, o que não é feito
  aqui.
- **Emenda:** a geometria primária passa a ser o **recorte fixo** de cada unidade, e a soma sobre
  **ADM2 ∩ recorte** passa a ser a sensibilidade, publicada **sempre com a fração de cobertura ao
  lado**. A inversão de papéis é declarada, não silenciosa.
- **Por que isto é aceitável e onde não é:** a geometria é **idêntica em todos os anos**, e é essa
  fixidez — não a coincidência com a fronteira administrativa — que a série interrompida e o DiD
  normalizado exigem. Um truncamento constante desloca o **nível** da série, e o nível é absorvido
  pelo efeito fixo de unidade e pela normalização pela média pré-tratamento de §3.2.3. **Onde não
  é aceitável:** qualquer leitura da soma de luz como grandeza *da cidade* (per capita, por km² de
  ADM2, comparação de magnitude entre cidades). Lichinga com 18 % do ADM2 é a única cuja série
  poderia ainda assim mudar de forma se a expansão urbana atravessar a borda do recorte; fica
  marcada como o doador de maior risco geométrico, ao lado dos dois riscos temáticos já declarados
  em §3.1 (Chimoio, Inhambane).
- **Não emendado:** a proibição de somar luz dentro da máscara de construído do ano continua
  integral. A catraca não entra na série de luz.

### E7 — O que **não** é emendado, e é reafirmado explicitamente

Nenhuma das seguintes é afrouxada por esta emenda, e nenhuma pode ser afrouxada depois dela:

1. **Todas as proibições de §0** (série própria pós-R2, par 2015–2020, WSF/GHSL como estoque,
   GHSL 2025/2030, acurácia global, churn).
2. **Os critérios de fracasso F1–F7 de §3.4**, com os limiares como escritos. Se dispararem,
   dispararam.
3. **O piso de p de §3.6:** 1 tratado + 5 doadores ⇒ p mínimo por permutação = **1/6 ≈ 0,167**.
   Nenhum resultado desta fase atinge significância convencional; é aritmética do pool.
4. **§8 inteiro** — em particular: **H4 não é reabilitada** (as duas elasticidades que a testariam
   continuam não estimáveis: não há série de área utilizável pós-2015, e população em nível A
   existe em 2017 e 2025 apenas); **H6 não é reabilitada**; **H5 e o logit de §7 continuam
   bloqueados** enquanto a opção C de ADR 0013 não for executada e aprovada.
5. **P4 continua descritivo** (E1, item iii), com a insuficiência publicada, não silenciada.
6. **A regra de agregação de §4.5:** "não estimável — motivo" é resultado admissível; "não rodado"
   não é.

### E8 — Consequência líquida sobre o quadro de §1.2, depois da emenda

| Quebra | Série que sobrevive | Janela | Pré/pós | O que é estimável |
|---|---|---|---|---|
| **2005** | `S_WSF_taxa` | 1993–2015 | 12 / 11 | nível **e** inclinação |
| **2011** | `S_WSF_taxa` | 1996–2015 | 15 / 5 | nível; inclinação não conclusiva por construção da janela |
| **2016** | `S_HARM_soma` | **2013**–2025 | **3 / 10** | **nível apenas**; inclinação pré é aritmética de 3 pontos |
| **2022** | `S_HARM_soma` | 2013–2025 | 9 / 4 | nível, IC largo; inclinação pós **não estimável** com 4 pontos |
| 2016 e 2022 sobre **área** | — | — | — | **não estimáveis** (§1.3 item 1, inalterado) |
| 2005 e 2011 sobre **luz** | — | — | — | **não estimáveis** (E4 item 4 — agravamento em relação a §1.3 item 3) |

### E9 — Execução realizada sob esta emenda (ponteiro, não resultado)

Os artefatos produzidos sob o desenho emendado estão em `data/processed/causal/`
(`its_quebras.csv`, `placebos.csv`, `did_efeitos.csv`, `did_sintetico_pesos.csv`,
`tendencia_paralela_pre2005.csv`, `elasticidades_por_fase.csv`, `cenarios_2035_2040.csv`,
`cenarios_pressao_varzea.csv`, `logit_conversao_status.csv`, `veredito_fase3.csv`), gerados
pelo alvo `causal` do Makefile. A proveniência está em
`data/provenance_parts/causal_fase3.md`. **Nenhuma especificação foi alterada depois de ver
o resultado**: os critérios F1–F7, os limiares dos placebos e os quatro anos falsos são os
que estavam escritos em §3.4 e §4.2 antes de qualquer dado existir. Onde eles dispararam,
está publicado que dispararam.

---

## 12. EMENDA 2 — 2026-09-08

**Declaração exigida por §10, e nos mesmos termos da Emenda 1.** Esta emenda é
**pós-dado**: foi escrita depois de os placebos rodarem, depois de o orquestrador ver
que P1 reprovava em 2022 e **contestar** o veredito (`ORCHESTRATION_LOG.md` 3-10), e
depois de o `revisor-adversarial` arbitrar a contestação
(`data/provenance_parts/arbitragem_p1_2022.md`, log 3-11). A decisão está em
`docs/ADR/0015`. Nada de §0–§11 foi reescrito; as afirmações originais afetadas ficam
onde estão e são marcadas em linha como `⟨EMENDADO · E10/E11⟩`.

**A arbitragem deu contra quem contestou.** O orquestrador argumentava que Tete divergia
em sinal de todos os controles em 2022. O revisor mostrou que a queda de 2022 **não está
na cidade**: 2021→2022 a Cidade de Tete (ADM2 ∩ recorte) faz **+0,7 %** e o resto do
retângulo — onde estão a mina e a vila de Moatize — faz **−12,7 %**; 2021→2025 a cidade
faz **+45,0 %** e o resto **−2,5 %**. O que existia era artefato de recorte, e a
decomposição que o mostrava estava no CSV desde a Emenda E6, sem que ninguém a lesse.

### E10 — Ramo de teste relativo com referência nula é ramo vazio (P1 **e** P2)

- **O desenho dizia** (§4.1, P1): "falha se duas ou mais cidades de controle exibirem
  quebra do mesmo sinal e de magnitude **≥ 50 % da de Tete**" — sem exigir que a
  referência fosse distinguível de zero. E dizia (§4.2, P2) o mesmo teste **com** a
  exigência de "IC que exclua zero". A assimetria entre os dois nunca foi justificada.
- **O que muda:** um ramo (`b2` ou `b3`) é **inaplicável** quando o coeficiente de
  **referência** de Tete tem IC95 que inclui zero ou foi declarado não estimável pelo
  desenho. Ramo inaplicável é **vazio**: não passa nem falha. Se todos os ramos de uma
  quebra forem vazios, o veredito é **"não estimável — motivo"**, que §4.5 já admitia.
  A regra vale para **P1 e P2**, e a assimetria de origem sai: P1 passa a exigir, do
  coeficiente do **próprio placebo**, o mesmo IC que P2 exigia.
- **Dois ramos são declarados vazios por cláusula anterior, não por escolha nova:**
  `b3` de 2022 pela **Emenda E8**, escrita antes de os placebos rodarem; `b2` de 2022
  pela decisão 2/4 do ADR 0015 (retângulo com mina contra retângulos sem mina).
- **O veredito original é preservado**, nunca sobrescrito, em
  `placebos.csv:veredito_pre_adr0015`, ao lado de `veredito` e de
  `mudanca_apos_adr0015`. Os dois são publicáveis lado a lado.

**Resultado da aplicação às quatro quebras (executado, não previsto):**

| Quebra | P1 pré-ADR 0015 | P1 sob E10 | P2 pré | P2 sob E10 |
|---|---|---|---|---|
| 2005 | passa (1 replica) | **não estimável** (ambos os ramos de Tete com IC que inclui zero) | passa | **não estimável** |
| 2011 | FALHA (4 replicam) | **FALHA** (3 replicam, só no ramo `b3`) | FALHA | **passa** (ver ressalva) |
| 2016 | FALHA (5 replicam) | **FALHA** (4 replicam; Quelimane sai por IC próprio) | não estimável | não estimável |
| 2022 | FALHA (5 replicam) | **não estimável** (ramos `b2` e `b3` vazios) | passa | **não estimável** |

**Duas divergências em relação ao que o parecer do revisor previu**, registradas porque
são informação sobre o parecer e não só sobre o código:

1. O parecer previa que **2005 continuaria "passa"**. Não continua: pela regra que o
   próprio parecer propôs, os dois coeficientes de referência de Tete em 2005
   (`b2` = −0,402, IC [−1,237; +0,433]; `b3` = +0,064, IC [−0,031; +0,158]) incluem zero,
   e **os dois ramos ficam vazios**. P1 em 2005 é **não estimável**, não "passa". A
   condição (b) do parecer — "neutra em três de quatro" — não se sustenta: a regra muda
   **duas** das quatro quebras de P1 e três das quatro de P2. A direção da mudança
   continua sendo de enfraquecimento, que é o que torna a emenda lícita.
2. O parecer previa **5 réplicas em 2016**; são **4**. Quelimane tem `b2` = −0,076, com
   IC [−0,186; +0,033] que inclui zero, e sai pela exigência de IC própria que P1 herda
   de P2. O veredito não muda: FALHA.

**Ressalva obrigatória sobre P2 em 2011, que é o único afrouxamento da emenda.** O
veredito passa de FALHA para "passa" porque o ramo que disparava era `b2`, e o `b2` real
de Tete em 2011 (+0,613) tem IC [−0,008; +1,234] que inclui zero. **Isto não reabilita a
quebra de 2011:** P1 em 2011 continua **FALHA** (3 controles replicam em `b3`), o
critério F de §3.4 continua marcando o painel `A_area_WSF|2011` como **contrafactual não
sustentado**, e o próprio `b2` de 2011 é indistinguível de zero — não há efeito de nível
a datar. O "FALHA" pré-emenda fica publicado ao lado, e a linha
`mudanca_apos_adr0015` marca o afrouxamento em texto.

### E11 — A decomposição de §2.3 foi executada, e o que ela permite dizer é menos do que se queria

- **O desenho dizia** (§2.3): `S_VIIRS_soma` seria publicada em três recortes mutuamente
  exclusivos — dentro da pegada `industrial`, dentro de `urbano` fora da pegada, e o
  restante. **A etapa nunca foi executada** (ADR 0015, decisão 4). Agora foi:
  `pipeline/03_causal/decomposicao_luz.py` → `data/processed/causal/decomposicao_luz_por_camada.csv`.
- **Ela não é uma partição.** A luz é ~500 m e as camadas são 30 m: um pixel de luz cobre
  ~278 pixels de camada, e não existe repartição sub-pixel sem premissa sobre como a luz
  se distribui dentro do pixel. Publicam-se **as duas envoltórias** — piso (repartição por
  área) e teto (pixel inteiro para a classe presente, prioridade industrial > urbano >
  reassentamento). A razão teto/piso é **2,1 em `industrial`, 1,8 em `urbano` e 5,2 em
  `reassentamento`**: nenhum **nível** ou **share** desta tabela é publicável como número.
  Só afirmações **cujo sinal é o mesmo nas duas envoltórias** são publicáveis.
- **Selo.** As camadas existem em seis anos-âncora; a luz é anual. Fora dos âncoras a
  máscara é de outro ano e o selo é **`interpolado`**, nunca `observado`. Toda comparação
  plurianual deve ser lida na variante `mascara_fixa_2020`, que é invariante à mudança de
  máscara e isola a variação de luz da variação de classificação.
- **Vieses herdados, declarados e não corrigidos:** `urbano` carrega a catraca R2
  (ADR 0013; fração herdada da união cumulativa até **18,0 %** em 2025) e a comissão de
  ADR 0009 (acurácia do usuário de `construido` entre **0,286 e 0,625** — reexecutado
  em ADR 0014). A parcela de luz
  atribuída a `urbano` herda as duas **inteiras**.
- **O que a decomposição sustenta, com máscara fixa de 2020 e sinal igual nas duas
  envoltórias:** (i) 2021→2022 a luz na pegada `industrial` **cai** (−15,3 % piso /
  −9,8 % teto) e a luz em `urbano` fica **plana** (+2,8 % / −1,7 %, sinal ambíguo);
  (ii) 2021→2025 a luz em `urbano` **cresce** (+34,7 % / +32,4 %) enquanto a da pegada
  `industrial` **não recupera** (−13,9 % / −4,3 %, negativa nas duas envoltórias).
- **O que ela NÃO sustenta, e é a restrição que importa:** a queda de 2022 **não é
  atribuível majoritariamente à mina**. Dos −6,04 pontos percentuais de queda do total,
  a pegada `industrial` responde por **−1,9 a −2,5 pp (32 % a 42 %)** e a classe `resto`
  — área sem nenhuma camada classificada — responde por **−2,6 a −4,9 pp**. Sob as duas
  envoltórias, o maior contribuinte isolado da queda está **fora** de tudo o que o
  pipeline classificou. Pela decisão 4 do ADR 0015, isto **não autoriza** a frase "a luz
  da mina caiu em 2022 e explica a queda"; autoriza apenas "a luz na pegada industrial
  caiu, e responde por cerca de um terço a dois quintos da queda, com o restante em área
  não classificada".
- **Alerta de série, novo e não previsto:** entre 2013 e 2025 o crescimento do total
  (+123 %) é dominado por `resto` (+171 % piso / +427 % teto), isto é, por pixels fora
  das camadas classificadas. Isso é compatível com dispersão espacial da luz (E5), com
  assentamento novo não captado pela máscara e com comportamento do produto — e as três
  não se separam com o que existe em nível A. Qualquer leitura da série de luz como
  "atividade econômica da cidade" carrega esta linha.

### E12 — O que esta emenda **não** faz

1. **Não reabilita nenhuma conclusão.** O contrafactual de 2022 continua derrubado por
   **F3** e **F4**, que não dependem de P1: o sintético é **Inhambane com peso 1,000** e
   o DiD dá **−0,12, IC95 [−0,28; +0,03], p = 0,333**. Os quatro painéis continuam
   marcados "CONTRAFACTUAL NÃO SUSTENTADO" em `veredito_fase3.csv`. Esta cláusula é a
   condição de licitude da emenda: se ela reabilitasse algo, a emenda seria especificação
   procurada e não poderia ser feita.
2. **Não afrouxa nada de E7.** As proibições de §0, os critérios F1–F7 e o piso de
   p = 1/6 continuam como escritos.
3. **Não reabilita H4 nem H6**, que continuam não testada e rebaixada, respectivamente.
4. **Não transforma a decomposição em resultado causal.** Ela é descritiva, interna à
   AOI, sem contrafactual, e com selo `interpolado` fora dos seis anos-âncora.
