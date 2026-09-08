# ADR 0006 — Amostragem de treino proporcional ao prior (redesenho da Fase 1)

**Data:** 2026-09-07
**Estado:** aceito
**Contexto:** escalonamento T2→T3; a classificação em três camadas foi reprovada.

## Decisão

A amostragem de treino da classificação (`pipeline/01_imagery/classificacao.py`)
passa de **estratificada balanceada** (`n_por_classe: 500`) para **aleatória
simples sobre o conjunto rotulado** (`n_total: 200000`), que respeita o prior das
classes por construção, com piso de `n_minimo_por_classe: 500` apenas para que
classes raras (água) não desapareçam do treino.

## Motivo

Construído ocupa ~1% da AOI. Com 500 amostras por classe, a classe entrava no
treino com 25% do peso — um prior artificial 25 vezes maior que o real. O efeito
foi medido diretamente nesta AOI, com o mesmo classificador, mesmas features e
mesma seed, mudando **só** a estratégia de amostragem:

| Ano | balanceada (500/classe) | proporcional ao prior (n=200 000) | WSF Evolution | GHSL BUILT-S (≥25%) |
|---|---|---|---|---|
| 2000 | 365,1 km² | 15,7 km² | 34,2 km² | 20,4 km² |
| 2015 | 186,8 km² | 40,4 km² | 56,3 km² | 34,9 km² |
| 2025 | 792,8 km² | 35,9 km² | — (série termina em 2015) | — (época extrapolada) |

A sensibilidade é de mais de uma ordem de grandeza. Ela **não desaparece** com a
decisão tomada aqui: ela é uma fragilidade estrutural do produto e está
declarada como tal no resumo da tarefa e na proveniência. O que a decisão faz é
escolher a opção estatisticamente defensável (não distorcer o prior) em vez da
que produz o número mais parecido com a referência — a referência (WSF) é a
semente do treino e calibrar contra ela seria circular.

## Alternativas rejeitadas

1. **Manter o balanceamento e corrigir o posterior pelo prior.** Equivalente em
   teoria, mas introduz um parâmetro de correção a mais para calibrar, com o
   risco prático de ser calibrado até bater com a referência.
2. **Escolher a razão de amostragem que aproxima a área do WSF/GHSL.** Rejeitada
   por circularidade: WSF semeia o treino, e ajustar um hiperparâmetro até bater
   com a referência é fabricar a resposta — exatamente o defeito que reprovou a
   versão anterior (limiares por percentil).

## Estabilidade

A decisão foi verificada quanto a ruído de amostragem: `n_total` de 60 000 e de
200 000 dão áreas dentro de ~10% uma da outra (2000: 13,5 vs 15,7 km²; 2015:
41,7 vs 40,4; 2025: 34,2 vs 35,9). O valor 200 000 foi escolhido pelo menor ruído,
não por produzir um número específico.

## Consequência

Muda os artefatos de `data/processed/imagery/`. A seed (`20250907`) não muda.
