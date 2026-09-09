# ADR 0012 — `cultivo_sequeiro` não é defensável como cropland com fenologia bianual; `cultivo_irrigado` é defensável com ressalva

- **Data:** 2026-09-08
- **Fase:** 2b (agricultura urbana e periurbana), §5.6.1
- **Decidido por:** subagente de imagem, sobre validação própria por interpretação visual
- **Estado:** aceito

## Contexto

`cultivo.py` recorta `cultivo_sequeiro` e `cultivo_irrigado` de dentro de `solo_exposto`
e `vegetacao` por razão de amplitude de NDVI chuva-seca relativa à mediana da paisagem do
ano (mesmo desenho de docs/ADR/0011). A separação foi desenhada para responder a §5.6.1,
mas dependia de validação para saber se estava, de fato, isolando cultivo — e não apenas
vegetação natural com o mesmo padrão sazonal.

## Validação executada

`amostras_validacao_cultivo.py` sorteou 12 pontos por estrato (`cultivo_sequeiro`,
`cultivo_irrigado`, `outro`) em 2020 (único ano validado — custo de interpretação manual;
ver docstring do script) e `acuracia_cultivo.py` estimou acurácia por classe pelo
estimador de Olofsson et al. (2014). Os rótulos de referência são interpretação visual
automatizada (mesmo tipo de intérprete que ADR 0007: modelo de linguagem multimodal, não
verdade de campo), registrados em
`data/processed/validacao/rotulos_interpretados_cultivo.csv`.

**Resultado (`data/processed/acuracia_cultivo_por_ano.csv`, 2020):**

| classe | prevalência no mapa | n mapeado | acurácia do usuário | IC95 |
|---|---|---|---|---|
| `cultivo_sequeiro` | 14,4 % | 8 (de 12; 4 indeterminados) | **0,000** | ±0,000 |
| `cultivo_irrigado` | 10,4 % | 9 (de 12; 3 indeterminados) | 0,556 | ±0,344 |

Matriz de confusão de `cultivo_sequeiro` (8 pontos decidíveis): **0** confirmados como
`cultivo_sequeiro`, 2 lidos como `cultivo_irrigado`, 6 lidos como `outro` (vegetação/solo
não cultivado). **Nenhum dos 8 pontos que o mapa chama de `cultivo_sequeiro` foi
confirmado como tal pelo intérprete.**

## Decisão

1. **`cultivo_sequeiro`, como especificado hoje, não é defensável como camada de
   cultivo.** A acurácia do usuário medida é 0,000 (n=8) — o pior resultado possível, não
   apenas baixo. A regra (amplitude alta + reverdecimento na chuva, dentro de
   `solo_exposto`) isola vegetação de fenologia estacional acentuada, mas o intérprete
   não confirmou nenhuma como campo cultivado reconhecível; o padrão detectado é
   indistinguível, a 30 m com dois compostos por ano, de savana herbácea/arbustiva
   natural — exatamente a ambiguidade antecipada na docstring de `cultivo.py` antes da
   validação, agora quantificada.
2. **`cultivo_irrigado` é defensável com ressalva forte.** Acurácia do usuário 0,556, mas
   com IC95 de ±0,344 (n=9) — o intervalo cobre de ~0,21 a ~0,90. Não é um resultado que
   sustente afirmação quantitativa precisa, mas é **positivo e acima do acaso**, e a
   confusão observada (2 dos pontos errados foram lidos como vegetação natural
   persistente, coerente com a limitação declarada de mata ripária) é a esperada, não uma
   falha estrutural como a de `cultivo_sequeiro`.
3. **A camada `cultivo_sequeiro` permanece no repositório, mas é publicada com o rótulo
   de "candidata", não de "cultivo confirmado".** Ela mede, com mais precisão, "vegetação
   de fenologia sazonal acentuada" (candidata a cultivo de sequeiro OU savana natural).
   Nenhum número de área de `cultivo_sequeiro` deve sustentar conclusão quantitativa no
   artigo ou no app sem essa ressalva ao lado.
4. **`cultivo_irrigado` pode sustentar leitura qualitativa e leitura cruzada com
   `varzea.py`** (`cultivo_varzea_por_ano.csv`), mas não um número pontual de área com
   precisão maior do que a ordem de grandeza, dado o IC95.
5. **O que seria preciso para tornar `cultivo_sequeiro` defensável e não foi feito aqui:**
   série intra-anual mais densa (compostos mensais ou bimestrais, não só seca/chuva) para
   calcular número de picos e forma da curva fenológica — é o que §5.6.1 pede sob o nome
   `n_picos`, presente em `config/study.yaml -> composto_fenologico.metricas` mas nunca
   implementado nesta série (só `ndvi_amplitude` foi produzido na Fase 1). Isso é
   trabalho futuro declarado, não uma correção de parâmetro dentro desta entrega —
   recalibrar os limiares atuais contra os mesmos 12 pontos usados para medir a falha
   seria overfitting ao próprio conjunto de validação (a mesma armadilha de
   circularidade que docs/ADR/0011 evitou explicitamente ao declarar que a concordância
   de 2020 com Maus et al. não é validação independente).

## Corroboração externa (obtida depois da decisão acima, mesma direção)

Um fetch paralelo recuperou GLAD Global Cropland e ESA WorldCover em `data/raw/`
(ausentes até então — Fase 0' havia registrado URLs quebradas). `validacao_externa_cultivo.py`
mede concordância (não acurácia — resolução e definição de cultivo diferentes) entre
`cultivo_*` e essas referências, em `data/processed/concordancia_externa_cultivo.csv`:

| referência | Jaccard `cultivo_sequeiro` | Jaccard `cultivo_irrigado` |
|---|---|---|
| GLAD 2003→2005 | 0,0010 | 0,0685 |
| GLAD 2007→2005 | 0,0007 | 0,0971 |
| GLAD 2011→2010 | 0,0021 | 0,0168 |
| GLAD 2015→2015 | 0,0016 | 0,0367 |
| GLAD 2019→2020 | 0,0006 | 0,1248 |
| ESA WorldCover 2020 | 0,0046 | 0,0352 |

`cultivo_sequeiro` tem Jaccard essencialmente nulo (0,0006–0,0046) com as duas
referências externas de cropland, em TODOS os pares ano — corrobora, de forma
independente do intérprete visual, a decisão do item 1: a camada não corresponde a
cropland reconhecível por nenhum dos dois métodos. `cultivo_irrigado` tem Jaccard maior
em todos os pares (0,017–0,125) — ainda baixo em termos absolutos (não sustenta
concordância forte), mas consistentemente acima de `cultivo_sequeiro`, na mesma direção
da acurácia do usuário medida (0,556 vs. 0,000). As duas validações independentes
(interpretação visual e concordância com produto externo) apontam para a mesma decisão.

## Alternativa rejeitada

**Recalibrar `RATIO_SEQUEIRO_AMP`/`RATIO_SEQUEIRO_CHUVA` até a acurácia medida melhorar,
sobre os mesmos 36 pontos.** Rejeitada porque o conjunto de validação é a única
referência independente disponível; ajustar o limiar contra ele o transformaria em
critério de treino, não de validação — exatamente o padrão que reprovou a primeira
versão da classificação de construído (ADR 0007) e que ADR 0011 evitou deliberadamente
para a pegada minerária.

## Consequência

- `pipeline/01_imagery/cultivo.py`, `config/plausibilidade.yaml` e
  `data/provenance_parts/agricultura_fase2b.md` citam este ADR e carregam a ressalva.
- App e artigo: `cultivo_sequeiro` deve aparecer com selo de confiabilidade reduzida
  (tooltip de proveniência apontando para este ADR), nunca em pé de igualdade visual com
  `cultivo_irrigado` ou com as camadas de construído.
- A pergunta de pesquisa 8 de §1 ("bolsões de sequeiro") permanece **parcialmente
  respondida**: a extensão candidata é mapeada e publicada, a composição real
  (agrícola vs. natural) não é determinável com os dados de nível A desta série.
