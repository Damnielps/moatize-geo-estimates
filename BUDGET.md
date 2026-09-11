# BUDGET.md — teto de tokens por fase e camada

Unidade: milhares de tokens (K), somando entrada + saída de todos os subagentes da fase.
Fonte de verdade da execução: `cost_ledger.csv` (hook `SubagentStop`), consolidado na Fase 7.

| Fase | T1 `haiku` | T2 `sonnet` | T3 `opus` | T4 `fable` | Teto da fase |
|---|---|---|---|---|---|
| 0 — Bootstrap | 40 | 20 | 20 | 0 | 80 |
| 0' — Reconhecimento | 450 | 1100 | 120 | 0 | 1670 |
| 1 — Pipeline de imagem | 60 | 900 | 200 | 40 | 1200 |
| 2 — Métricas e reconstrução | 40 | 600 | 150 | 0 | 790 |
| 2b — Agricultura urbana | 40 | 700 | 250 | 40 | 1030 |
| 3 — Comparativo e cenários | 20 | 150 | 600 | 150 | 920 |
| 4 — App | 120 | 800 | 80 | 0 | 1000 |
| 5 — Artigo | 150 | 120 | 700 | 150 | 1120 |
| 6 — Revisão adversarial | 0 | 40 | 60 | 250 | 350 |
| 7 — Fechamento | 60 | 20 | 20 | 0 | 100 |
| 4b — Painel, contexto provincial e publicação (aberta 2026-09-11) | 150 | 700 | 250 | 100 | 1200 |
| **Total** | **980** | **4450** | **2200** | **630** | **8260** |

## Regras de orçamento (§0-A.5 do prompt-mestre)

1. Ao atingir **80 %** do teto de uma fase, o orquestrador **para de escalar para T4**
   e reporta ao usuário antes de continuar.
2. Ao atingir **100 %** do teto de uma fase, a execução **para** e aguarda decisão
   explícita do usuário (aumentar o teto, reduzir escopo, ou aceitar entrega parcial).
3. Estouro de teto em T4 nunca é absorvido silenciosamente: cada invocação de
   `revisor-adversarial` é registrada em `ORCHESTRATION_LOG.md` com justificativa.
4. Tetos são revisáveis ao fim de cada fase, com o número real da fase anterior como base.

## Status

### Fase 0' — fechamento de custo (2026-09-07)

**Teto estourado.** Registrado aqui em vez de absorvido em silêncio, como manda a regra 3.

| Camada | Consumido | Teto | Uso |
|---|---|---|---|
| T1 haiku | 361.884 | 450.000 | 80% |
| T2 sonnet | **1.324.763** | 1.100.000 | **120%** |
| T3 opus | 0 | 120.000 | 0% |
| **Fase 0'** | **1.686.647** | 1.670.000 | **101%** |

T2, por invocação:

| Antes do reinício da sessão | | Depois do reinício | |
|---|---|---|---|
| imagem (reexecução) | 68.886 | AOI + tile do DEM | 108.125 |
| reassentamento (reexecução) | 72.381 | demográficas (final) | 137.367 |
| demográficas 2ª | 78.946 | auditor-dados | 95.051 |
| reassentamento (fecho) | 63.115 | portão qa 1ª passagem | 102.062 |
| demográficas 3ª | 100.734 | reprocessadores institucionais | 99.502 |
| agricultura (reexecução) | 92.934 | auditor-dados (revisão) | 105.013 |
| agricultura 3ª | 105.224 | | |
| demográficas 4ª | 95.423 | | |
| **subtotal** | **677.643** | **subtotal** | **647.120** |

### O que o estouro diz

**Metade do T2 foi desperdício de configuração, não trabalho.** Das oito invocações antes
do reinício, **cinco terminaram no limite de 40 turnos sem gravar nada** — a família
demográfica sozinha consumiu 331K em quatro tentativas e entregou um esqueleto. Com
`maxTurns: 100` valendo, nenhuma das seis invocações seguintes foi truncada.

O custo médio por invocação **subiu** de 84,7K para 107,9K depois do reinício. Não é
regressão: as invocações passaram a ir até o fim, em vez de morrer no meio. Pagar 108K por
uma entrega completa é melhor que pagar 95K por um arquivo vazio.

**Estimativa do custo evitável:** as cinco invocações truncadas somam ~473K, das quais só a
última rodada de cada família produziu algo aproveitável. Sem o bloqueio de `maxTurns`, a
Fase 0' teria fechado perto de **1.100–1.200K**, dentro do teto original revisto.

### Implicação para as fases seguintes
Os tetos de 1 a 7 foram dimensionados supondo pouca reexecução. A Fase 0' teve **quatro das
seis famílias reprovadas por integridade** e uma reprovação no portão. Se essa taxa se
mantiver, os tetos de 1, 2b e 5 são otimistas. Revisar ao fim da Fase 1, com número real
em mãos — que é o que a regra 4 manda.

### Fase 1 — parcial (2026-09-07)

**T3 estourado, T2 dentro, fase em 93% antes de fechar.** Registrado, não absorvido (regra 3).

| Camada | Consumido | Teto | Uso |
|---|---|---|---|
| T2 sonnet | 777.272 | 900.000 | 86% |
| T3 opus | **339.845** | 200.000 | **170%** |
| **Fase 1 até aqui** | **1.117.117** | 1.200.000 | **93%** |

T2, por invocação: código de compostos 150.135 · WSF Evolution 92.021 · gerar compostos
109.789 · corrigir máscara 199.636 · classificação 225.691.
T3: recalibrar amostragem 193.035 · viés de sensor 146.810.

**Por que o T3 estourou.** O teto de 200K supunha que a camada T3 seria acionada uma vez,
para recalibrar amostras depois de uma reprovação. Foram **duas invocações**, e a segunda
não estava prevista em lugar nenhum: nasceu de um problema que só apareceu depois da
recalibração — o viés de sensor de +1,25%/ano, da mesma ordem do efeito procurado.

Essa segunda invocação **mudou o desenho do estudo**: a série própria deixou de ser a série
primária de tendência e o WSF Evolution assumiu esse papel (`docs/ADR/0008`). Não foi
retrabalho; foi a descoberta que impede o estudo de interpretar um artefato de sensor como
efeito da mineração. O teto estava errado, não o gasto.

Ambas as invocações foram truncadas no limite de 50 turnos, o que somou desperdício por
cima — mesmo padrão do `coletor-dados` na Fase 0'. `maxTurns` de `desenho-causal` já está
em 110.

**Revisão sugerida para as fases seguintes** (regra 4, com número real em mãos): o teto de
T3 na Fase 3, hoje 600K, supõe uma análise causal sem reformulação de desenho. A Fase 1
mostrou que uma reformulação custa ~150–200K por rodada.

### Fase 1 — fechamento (2026-09-08)

| Camada | Consumido | Teto | Uso |
|---|---|---|---|
| T2 sonnet | 901.346 | 900.000 | 100% |
| T3 opus | **566.527** | 200.000 | **283%** |
| **Fase 1** | **1.467.873** | 1.200.000 | **122%** |

T3 teve **três** invocações, contra a de uma prevista: recalibrar a amostragem depois da
reprovação, medir o viés de sensor, e fechar a validação. As duas últimas não estavam no
plano e foram as que mais mudaram o estudo — o viés de +1,25%/ano tirou a série própria do
papel de série de tendência, e a validação estratificada revelou que o critério de acurácia
de §10 não discriminava classe rara. Nenhuma foi retrabalho.

### Fase 2 — fechamento (2026-09-08)

| Camada | Consumido | Teto | Uso |
|---|---|---|---|
| T2 sonnet | 799.650 | 600.000 | 133% |
| T3 opus | 151.249 | 150.000 | 101% |
| **Fase 2** | **950.899** | 790.000 | **120%** |

Aprovada no portão, na segunda passagem. O estouro de T2 vem de três coisas fora do plano
da fase: a **reabertura da Fase 1** (camadas que mediam o objeto errado), as **duas
passagens do portão**, e a **figura de localização** pedida pelo usuário. A reabertura não
é retrabalho da Fase 2 — é correção de defeito herdado, e foi ela que tornou H3 testável.

**Padrão consolidado nas três fases medidas:** 0' fechou em 101%, 1 em 122%, 2 em 120%.
O teto nunca foi excedido por escopo mal dimensionado; foi excedido por **defeitos
descobertos durante a execução**, que exigiram reabrir o que já parecia pronto. Um
orçamento que suponha zero reabertura vai errar por 20% de forma sistemática.

### Fases 3 a 7
Nada consumido. **Os tetos de T3 estão subdimensionados**: as Fases 0' e 1 mostram que uma
reformulação de desenho custa 150–230K por rodada, e que ela costuma aparecer *depois* da
primeira entrega, não antes. O teto de T3 na Fase 3 (600K) comporta duas ou três rodadas —
provavelmente pouco para uma fase que é inteiramente desenho causal.

### Fase 2b — fechamento (2026-09-08)

Teto: T1 40K · T2 700K · T3 250K · T4 40K · **total 1.030K**.

**Consumo não fechado com o mesmo rigor das fases anteriores.** As Fases 0', 1 e 2 foram
tabuladas somando os `subagent_tokens` das notificações de tarefa, uma a uma, durante a
execução. Na Fase 2b esse acúmulo se perdeu na compactação de contexto, e `cost_ledger.csv`
continua **não instrumentado** — o payload de `SubagentStop` não traz modelo nem tokens
(ORCHESTRATION_LOG.md 0-14). Preencher a tabela agora seria estimar e apresentar como
medido, que é exatamente o que este estudo proíbe nos dados. Fica declarado como lacuna.

O que é observável: a fase teve **três passagens de portão** (duas reprovações), a
**reabertura da Fase 1 pela segunda vez** (`docs/ADR/0014`, três instâncias do mesmo
defeito de limiar absoluto) e a **reexecução completa da classificação** nos seis
anos-âncora. Pelo padrão das três fases medidas — 101%, 122%, 120% — e por esta ter tido
mais reaberturas que qualquer outra, o teto de 1.030K quase certamente foi excedido.

**Consequência para o planejamento, que é o uso real deste arquivo:** a instrumentação de
custo precisa sair de dependência de notificação lida em tempo real. Enquanto ela não
existir, os fechamentos de fase são auditáveis apenas enquanto a sessão durar — e uma
sessão longa é justamente onde o custo importa.

### Fase 3 — fechamento (2026-09-08)

Teto: T1 20K · T2 150K · T3 600K · T4 150K · **total 920K**.

**Consumo não instrumentado**, pelo mesmo motivo da Fase 2b: `cost_ledger.csv` continua sem
modelo e sem tokens no payload do `SubagentStop`. Pelas notificações lidas em sessão, a fase
teve pelo menos **oito invocações** (coleta T1 reprovada, coleta T2, complemento de tile,
auditoria, desenho pré-registrado, estimação, arbitragem adversarial, execução do ADR 0015)
mais o portão — bem acima do que o teto comporta.

**Onde o teto errou, e não foi no escopo.** O plano supunha uma fase de desenho causal. O
que aconteceu: uma coleta inteira que não estava prevista (as luzes noturnas nunca tinham
sido baixadas, embora o ADR 0013 as designasse série primária), duas reprovações de coleta,
um download morto pelo próprio orquestrador, um defeito de timeout que fez 5 de 7 anos
falharem em silêncio, e uma arbitragem adversarial.

**Padrão em quatro fases medidas ou estimadas:** 0' 101 %, 1 122 %, 2 120 %, 2b e 3
excedidas sem medição. A causa é sempre a mesma e já é previsível: **defeito descoberto
durante a execução, exigindo reabrir o que parecia pronto.** Um orçamento que suponha zero
reabertura erra por 20 % ou mais, de forma sistemática — e a Fase 3 mostra que erra mais
quando a fase depende de dado que ninguém verificou existir.

### Fase 4 — fechamento (2026-09-08)

Teto: **1.000K**. **Consumo não instrumentado**, como em 2b e 3.

**Nove passagens de portão, oito reprovações.** Nenhuma foi por rigor performático: todas
apontaram defeito com instância viva em disco, e as duas últimas acharam problemas
substantivos (acurácia publicada sem IC95, violando §10; e a não separabilidade dos 15 pares
de anos, que nenhum ADR registrava).

**O que o orçamento não previa, e é a lição:** o custo dominante da fase não foi construir o
app — foi **descobrir que os defeitos de conteúdo vinham do orquestrador**, e que os
contratos escritos para pegá-los tinham eles próprios o mesmo defeito. Nove formas distintas
de vacuidade num único arquivo de teste.

**Padrão em cinco fases:** 0' 101 %, 1 122 %, 2 120 %, 2b/3/4 excedidas sem medição. Um
orçamento que suponha zero reabertura erra por 20 % ou mais, sistematicamente — e erra
muito mais quando a fase depende de prosa, porque prosa não tem contrato até alguém escrever
um, e o primeiro que se escreve costuma ser frouxo.

### Fase 5 — fechamento (2026-09-08)

Teto: **1.120K**. Consumo não instrumentado. Quatro invocações de redação (uma perdida por
limite de sessão do modelo, sem edição) mais o portão.

**Aprovada na primeira passagem**, contra oito reprovações da Fase 4. A diferença não é
sorte: a Fase 4 pagou o custo de descobrir que o defeito dominante era afirmação relacional
vinda da memória do orquestrador, e produziu a folha de fatos gerada e o contrato que varre
`paper/`. O artigo foi escrito dentro dessas defesas.

**Lição de orçamento:** uma fase que constrói defesa contra uma classe de erro parece
estourar sozinha, mas está pagando pela fase seguinte. Medir fases isoladamente esconde
isso.

### Fase 4b — fechamento de custo (2026-09-11)

Teto aprovado no plano: T1 150K · T2 700K · T3 250K · T4 100K · **total 1.200K**.
Consumo somado dos `subagent_tokens` que cada invocação reportou ao terminar (o hook
`SubagentStop` continua sem modelo e sem tokens; a soma é do orquestrador, invocação a invocação,
e inclui a releitura de contexto a cada turno — mesma medida das fases anteriores):

| Camada | Invocações | Consumido | Teto | Uso |
|---|---|---|---|---|
| T1 haiku | 4 | ~262K | 150K | **175 %** |
| T2 sonnet (inclui 7 portões `qa-validador`) | 22 | ~2.212K | 700K | **316 %** |
| T3 opus | 10 | ~1.460K | 250K | **584 %** |
| T4 fable | 0 | 0 | 100K | 0 % |
| **Fase 4b** | 36 | **~3.934K** | 1.200K | **~328 %** |

**Teto estourado sem parada a 100 % — falha do orquestrador, registrada aqui em vez de absorvida
(regra 3).** A soma não foi feita em tempo real; só no fechamento. Pela regra 1, a revisão
adversarial em T4 (último passo do plano) **não foi disparada**: fica para decisão do usuário.

**Onde o teto errou.** (i) O plano estimou porte de UI; o custo real foi verificação visual e
reexecução: seis tarefas de app reprovaram na primeira passagem, e cinco correções foram em opus.
(ii) Cinco pedidos do usuário chegaram durante a fase (várzea, rodovias/ferrovia/aeroporto, cores
WorldCover, eixo repetido, botões). (iii) Três agentes pararam no limite de turnos e foram
retomados. (iv) A coleta no EDGAR custou ~308K sem publicar número, porque a SEC recusa o contato
no-reply do GitHub (pendência do titular). O que funcionou: portões baratos pegaram defeitos
reais (proveniência em tabela, título que atribuía à mina, fonte do macOS), e verificação direta do
orquestrador substituiu portões inteiros em tarefas simples (A1b, A2a, B1, A2b).
