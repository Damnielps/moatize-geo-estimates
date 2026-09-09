# ADR 0017 — Vila de Moatize: o teto publicável é a partição sem peso de construído

- **Data:** 2026-09-09
- **Fase:** 2 (métricas), correção
- **Decidido por:** orquestrador, sobre validação cruzada medida em Cidade de Tete
- **Estado:** aceito, com séries antes e depois medidas

## Contexto

`pipeline/02_metrics/populacao_vila_moatize.py` estima a população da Vila de Moatize
(sem contagem oficial isolada — só o Distrito de Moatize, ADM2, tem HDX COD-PS) somando
a grade GRID3 v1.1 (calibrada ao Censo 2017) dentro do cluster de Voronoi `moatize_vila`,
ponderada por uma máscara de área construída (classificação própria ou GHSL BUILT-S).

A validação cruzada do mesmo procedimento em Cidade de Tete, contra os 307.338
habitantes observados (HDX COD-PS 2017), media:

| variante sobre o cluster de Voronoi de Tete | estimativa | desvio |
|---|---|---|
| multiplicador de fração — classificação própria | 183.036 | −40,44% |
| multiplicador de fração — GHSL BUILT-S | 78.512 | −74,45% |
| pertença binária, fração > 0 | 229.867 | −25,21% |
| pertença, fração ≥ mediana das células com fração > 0 | 152.462 | −50,39% |
| sem peso de construído, cluster inteiro | 312.300 | **+1,61%** |

A banda publicada até então (piso/teto) era composta só das quatro primeiras variantes —
todas atenuadas por uma máscara de construído. A quinta linha, a única que valida, estava
rotulada "diagnóstico, não publicável".

## Decisão

1. **Nenhuma forma de aplicar a máscara de construído recupera o observado** — nem o
   multiplicador (−40%), nem a pertença binária (−25%). O desvio não nasce de "qual
   peso", nasce de pesar. O GRID3 v1.1 **já é um produto dasimétrico**, calibrado ao
   Censo 2017; ponderá-lo de novo por uma máscara de construído própria **restringe a
   população duas vezes**, descartando gente que o produtor já havia colocado onde ela
   está (periferia difusa, informalidade, resolução).
2. **A partição espacial sozinha (Voronoi por sede mais próxima, sem peso) reproduz Tete
   dentro de 1,61%.** O que funciona é particionar, não pesar.
3. **A banda é reenquadrada:**
   - **teto** = soma do GRID3 no cluster de Voronoi **sem peso de construído** — a
     variante validada. Limite SUPERIOR: inclui a área rural do cluster atribuída à sede
     mais próxima.
   - **piso** = a menor das variantes RESTRITAS por construído (classificação própria,
     GHSL, pertença binária, pertença por mediana). Limite INFERIOR: a validação em Tete
     mostra que essa família de variantes perde entre 25% e 74% do observado.
   - **Nenhum valor central é publicado.** O que antes era publicado como "estimativa
     central" (peso 'classificação própria') passa a ser uma variante nomeada dentro da
     banda, nunca "a estimativa".
4. **Duas variantes adicionais entram na tabela de sensibilidade**, para Vila e Tete:
   pertença binária (fração > 0) e pertença por mediana (corte por `np.quantile` sobre
   as células do próprio cluster com fração > 0 — nunca um limiar absoluto, ADR 0014).
5. **A nota de comissão é corrigida** (afirmação relacional com dois referentes, não um):
   o peso 'classificação própria' tende a inflar a estimativa **frente ao peso GHSL**
   (o outro multiplicador de fração); tende a **subestimar em ~40%** frente à população
   **observada** em Cidade de Tete. As duas relações têm referentes distintos.

## Consequências

- `data/processed/populacao_vila_moatize_sensibilidade.csv` passa de 4 métodos de peso
  para 5 (mais `piso_teto` e `validacao_cruzada`), com o desvio de validação de cada
  variante publicado, inclusive da que valida bem.
- `data/processed/demografia_serie_1997_2025.csv`, linha "Vila de Moatize" (2017): o
  esquema de colunas não comporta um intervalo por linha, então `valor` passa a carregar
  o TETO (69.301, a variante validada), não mais o peso 'classificação própria'
  (29.009). `nota`/`comparabilidade` deixam explícito que é o teto, não um valor
  central, e citam piso e o desvio de cada variante.
- Nenhum número da Vila de Moatize deixa de ser `modelado`; nenhuma série ganha CAGR
  (ano único, 2017).
- `pipeline/tests/test_demografia.py` ganha contratos que amarram teto à variante sem
  peso, piso ao mínimo das variantes restritas, a publicação do desvio de cada variante,
  e a ausência de qualquer afirmação de valor central para a Vila.
