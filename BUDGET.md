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
