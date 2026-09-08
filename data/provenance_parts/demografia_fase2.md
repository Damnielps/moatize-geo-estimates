<!-- SECAO_DEMOGRAFIA_FASE2_INICIO -->
## Reconstrução demográfica e domiciliar (§5.3, Fase 2)

Script: `pipeline/02_metrics/reconstrucao_demografica.py`.
Gerado em 2026-09-08.

### Núcleo A — o que existe

| unidade | ano | selo | nível | fonte |
|---|---|---|---|---|
| Cidade de Tete | 2017 | observado | A | HDX COD-PS 2017 (INE IV RGPH via reprocessador) |
| Cidade de Tete | 2025 | modelado | A | HDX COD-PS 2025 (projeção do INE) |
| Distrito de Moatize | 2017 | observado | A | HDX COD-PS 2017 |
| Distrito de Moatize | 2025 | modelado | A | HDX COD-PS 2025 |

Dois pontos por unidade (um observado, um modelado) **não constituem série de
tendência** — não há interpolação entre eles no núcleo. CAGR 2017-2025
calculado e publicado com selo `modelado` e nota de risco de circularidade
para H4.

### Fora do núcleo — contexto rotulado (nível B/C)

`data/processed/demografia_contexto_nao_nucleo.csv`: Cidade de Tete 1997
(101.984, nível B, UNSD Demographic Yearbook); Distrito de Moatize 1997 (não
recuperado em A nem B); Cidade de Tete e Distrito de Moatize 2007 (155.870 e
215.092, nível C, documento do INE via Wayback sem licença localizável).
Nenhum desses quatro pontos sustenta número publicado no núcleo (§4.0 regra 1;
§10).

### Dasimetria 2017 (Cidade de Tete apenas)

`307338` habitantes distribuídos pela mancha construída própria
(urbano ∪ reassentamento, média 2015/2020), com teste de sensibilidade contra
GHSL BUILT-S e WSF Evolution como pesos alternativos —
`data/processed/populacao_dasimetrica_sensibilidade.csv`. Selo `modelado`.
Raster: `data/processed/imagery/populacao_dasimetrica_tete_2017_30m_32736.tif`.

**Distrito de Moatize não foi dasimetrizado**: o total (260.843 em 2017) é do
distrito inteiro (8.427 km², COD-AB), muito além da mancha construída mapeada
na AOI; distribuí-lo sobre essa mancha implicaria que toda a população rural
do distrito mora dentro do núcleo urbano — falso por construção. Precisaria de
total ao nível de posto administrativo (ADM3), que o COD-PS não publica.

### Domicílios (§5.3)

Não construído nesta rodada. Ver `docs/ADR/0010-domicilios-sem-fonte-a.md`:
o tamanho médio do domicílio para Tete/Moatize não tem fonte de nível A nem B
confirmada (tabulação do INE não localizada como pública; catálogo mozdata
carrega via JS e não expõe a tabulação diretamente) — qualquer produto
"edificações × tamanho médio do domicílio" herdaria nível C do denominador,
o que a política de dados abertos proíbe de sustentar número publicado.
Google Open Buildings/Microsoft Footprints (nível A, listados em
`data/LICENSES.md`) não foram baixados: buscá-los agora seria custo sem
retorno enquanto o denominador continuar sem fonte A.

### Projeções 2027-2040 (§5.3)

Não construídas. Com dois pontos (2017 observado, 2025 já modelado pelo INE),
qualquer extrapolação própria projetaria sobre uma premissa de crescimento
geométrico já embutida no ponto de 2025 — "compor premissas invisíveis",
exatamente o risco que o enunciado da tarefa aponta. O que resolveria isso é
o Censo 2027 (ainda não publicado) ou uma projeção com metodologia própria
declarada (cohort-component, migração líquida como parâmetro de cenário) a
partir de 2017 apenas — não implementada nesta rodada por não ter sido
solicitada como tal e por depender de parâmetros de fecundidade/mortalidade/
migração que este script não tem em nível A.

### Suficiência para §1

- **Pergunta 1 (linha de base 1997-2005, H1 em população):** não respondível
  em nível A — 1997 não tem fonte A/B verificável para nenhuma das duas
  unidades com valor íntegro (Tete tem só B; Moatize nem isso). H1 já foi
  reformulada por área construída (`docs/ADR/0003`), que é a via respondível.
- **Pergunta 2 (implantação/boom 2005-2015):** não respondível diretamente em
  população de nível A — não há âncora demográfica A entre 2007 (nível C) e
  2017. Só a série de área construída (§5.1/§5.2) cobre esse intervalo em A.
- **Pergunta 6 (bust/transição 2015-2025):** parcialmente respondível. Há dois
  pontos A (2017 observado, 2025 modelado), mas o ponto de 2025 é projeção
  institucional, não recontagem — não pode sozinho provar desaceleração/
  estagnação/reconversão sem o risco de circularidade já registrado para H4.
  Cruzar com luzes noturnas e área construída (outras famílias) é necessário
  para qualquer conclusão de P6, não substituível por este produto isolado.

<!-- SECAO_DEMOGRAFIA_FASE2_FIM -->
