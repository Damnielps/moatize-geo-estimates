# ADR 0014 — Limiar relativo propagado às três instâncias, e permanência com escopo por camada

- **Data:** 2026-09-08
- **Fase:** 1, reaberta pela segunda vez
- **Decidido por:** usuário, sobre o diagnóstico de `docs/ADR/0013` e um achado paralelo do orquestrador
- **Estado:** aceito, com séries antes e depois medidas

## Contexto

`docs/ADR/0011` estabeleceu e testou um padrão de correção — **limiar relativo à mediana da
paisagem do próprio ano** — e o aplicou **apenas à pegada minerária**. Nunca foi propagado.

O mesmo defeito — **limiar absoluto sobre série não estacionária** — estava em mais dois
lugares, achados de forma independente e no mesmo dia:

1. **Corte de treino de vegetação** (`rotulos_treino()`, NDVI de seca ≥ 0,30). Achado por
   `docs/ADR/0013`. A fração da AOI acima do corte **era** a série de vegetação publicada, ao
   décimo — e a mediana da paisagem percorre 0,204 a 0,409, de modo que o corte fixo ora fica
   abaixo dela, ora acima.
2. **Máscara de denominador dos índices** (`denominador_minimo: 0.1`). Achado pelo
   orquestrador, ao conferir uma imagem de satélite da Tete central a pedido do usuário.
   Água tem green baixo **e** SWIR baixo, então `green + swir16` cai abaixo de 0,10 e o pixel
   é descartado como "instabilidade numérica". **Isso apagava o Zambeze.**

O terceiro problema, independente, veio do item 5 de `docs/ADR/0013`: a **regra R2 de
permanência** (união cumulativa) é defensável em `urbano`, indefensável em `industrial` — cava
é reabilitada — e **danosa em `reassentamento`**, onde torna abandono indetectável, que é
literalmente a pergunta 3 de §1.

## Decisão

1. **O corte de treino de vegetação passa a ser relativo:** NDVI de seca ≥ 1,30 × mediana de
   NDVI de seca da paisagem do ano.
2. **A máscara de índices deixa de olhar o denominador e passa a olhar as bandas:** pixel com
   qualquer banda de reflectância da fórmula ≤ 0 é mascarado. Reflectância não positiva é
   artefato de correção atmosférica, fisicamente inválido — e é a condição que de fato produz
   `|índice| > 1`.
3. **A regra R2 sai de `industrial` e de `reassentamento`.** Permanece em `urbano`, onde
   construído é de fato quase permanente.

A correção 2 foi **testada antes de prescrita**: os pixels realmente patológicos são
**exatamente 1** por raster, e **todos** têm banda não positiva. O critério novo remove o
mesmo 1 pixel e preserva **36.041 dos 36.042** pixels de água, contra 32.909 a 44.364
removidos pelo critério antigo.

## Resultado medido

### O Zambeze volta a existir

Classe `agua` na janela da Tete central (bbox 33,555–33,645 E / −16,190 a −16,115 S), onde o
rio tem cerca de 1 km de largura e atravessa a janela inteira:

| ano | antes | depois |
|---|---|---|
| 2000 | 0,2 % | **9,3 %** |
| 2005 | 0,2 % | **9,4 %** |
| 2010 | 0,5 % | **10,8 %** |
| 2015 | **0,0 %** | **10,6 %** |
| 2020 | 0,9 % | **11,0 %** |
| 2025 | 11,1 % | 11,1 % |

Um rio permanente passa a ser detectado de forma estável. É a confirmação mais direta
possível de que a correção 2 funcionou.

### As classes de cobertura param de oscilar

| ano | vegetação antes | depois | solo exposto antes | depois |
|---|---|---|---|---|
| 2000 | 10,6 % | 9,4 % | 87,3 % | 88,6 % |
| 2005 | 10,9 % | 9,6 % | 86,5 % | 87,9 % |
| 2010 | 75,5 % | **10,1 %** | 21,1 % | **86,5 %** |
| 2015 | **89,0 %** | **5,6 %** | 6,1 % | **89,7 %** |
| 2020 | 27,1 % | 12,1 % | 67,4 % | 82,8 % |
| 2025 | 6,1 % | 11,9 % | 87,8 % | 82,2 % |

A vegetação passa de variar por **fator 15** para **fator 2,2**; o solo exposto, de fator 14
para **1,09**. O que resta é compatível com variabilidade interanual de chuva em ambiente
semiárido — não mais com artefato de limiar.

### `reassentamento` deixa de ser catraca

Série depois da remoção de R2: 1,20 (2010) · 1,65 (2015) · **0,70** (2020) · 1,09 (2025).
**Deixou de ser monotônica**, que era o ponto: abandono e adensamento voltam a ser
observáveis. O valor de 2020 fica dentro da faixa de `config/plausibilidade.yaml` — a exceção
declarada que `docs/ADR/0013` previu como possível **não foi necessária**.

### A acurácia de `urbano` não muda

Reexecutada sobre os estratos novos, **não presumida**: acurácia do usuário de **0,286 a
0,625**, contra 0,27 a 0,63 antes. **`docs/ADR/0009` continua válido sem emenda.**

### O cultivo NÃO melhora — e isso fortalece o ADR 0012

`cultivo_sequeiro` continua indefensável depois da correção: kappa **−0,065**, Jaccard de
**0,001 a 0,002** contra o GLAD Cropland. E o desacordo de área é de ordem de grandeza — a
classificação dá 359 a 761 km², o GLAD dá cerca de **20 km²** na mesma AOI.

Isso é informativo: a correção resolveu água e cobertura e **não** resolveu o cultivo, o que
localiza a falha do cultivo na **abordagem fenológica bianual**, não nos limiares. O
`docs/ADR/0012` sai reforçado, não enfraquecido.

`cultivo_irrigado` segue melhor que o sequeiro (Jaccard 0,043 a 0,098) e continua com a
ressalva de acurácia do usuário 0,556 ± 0,344.

## O que isto não corrige

- **A anomalia de 2015 permanece.** A série bruta ainda pica em 55,56 km² naquele ano, contra
  33,31 em 2010 e 42,00 em 2020. `docs/ADR/0013` já havia mostrado, com o GHSL como árbitro
  independente, que 2015 é o ano anômalo e não 2020.
- **A catraca de `urbano` permanece**, porque R2 continua nela — por decisão, e defensável.
  As ressalvas do item 6 de `docs/ADR/0013` para a Fase 3 seguem valendo integralmente.
- **O WSF continua monotônico por construção**, conforme a emenda de `docs/ADR/0008`.

## Lição registrada

O defeito da máscara de denominador foi **prescrito pelo orquestrador**. Quando os contratos
acusaram 1 pixel fora de faixa em dois rasters e 4 em um terceiro, a instrução foi "mascare o
denominador, não afrouxe o contrato". O agente calibrou o limiar contra os pixels ofensores e
chegou a 0,10 — correto pelo que foi pedido.

**Um limiar calibrado apenas contra os casos que se quer excluir não é calibrado; é
ajustado.** A pergunta que faltava era o que mais ele removia — e a resposta era um rio.
