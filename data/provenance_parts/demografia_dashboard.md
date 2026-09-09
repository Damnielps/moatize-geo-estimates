<!-- SECAO_DEMOGRAFIA_DASHBOARD_INICIO -->
## Dashboard de população 1997-2025 (§5.3, Frente A)

Script: `pipeline/02_metrics/demografia_dashboard.py`.
Gerado em 2026-09-09.

Produz `data/processed/demografia_serie_1997_2025.csv`: uma linha por unidade
× ano de população, mais linhas `cagr_<a>_<b>` e `indice_base_<ano>` por
unidade. **Não entra em `stats_by_year_by_unit.csv`** — grava direto em
`data/processed/`, fora do circuito de fragmentos/consolidador; carrega nível
A, B, C e `ausente` lado a lado, cada linha com o seu.

Unidades: Cidade de Tete, Distrito de Moatize (reaproveitados de
`reconstrucao_demografica.montar_nucleo()`/`montar_contexto_b_c()`, sem
retranscrição), Província de Tete e Moçambique (soma dos ADM2 do HDX
COD-PS por nome de província 2017/2025; parse programático do HTML do
Censo 2007 do INE para 2007), e Vila de Moatize — um único ponto (2017,
`selo=modelado`, `nivel_fonte=A` mas fonte GRID3, não HDX COD-PS: estimativa
dasimétrica de terceiros, reaproveitada de
`populacao_vila_moatize.estimar()`, nunca contagem; sem CAGR — um ponto não
faz taxa; piso/teto e o desvio da validação cruzada em Cidade de Tete vão na
`nota`. Ver `data/processed/populacao_vila_moatize_sensibilidade.csv` e
`data/provenance_parts/populacao_vila_moatize.md`.

### Somas verificadas nesta execução

| unidade | 2017 (soma COD-PS) | 2025 (soma COD-PS) |
|---|---|---|
| Província de Tete | 2551824 | 3432961 |
| Moçambique | 26899102 | 35163992 |

Soma provincial 2017 confere com a "população residente" publicada pelo INE
(2.551.826) dentro de ±5 (diferença observada:
-2). Soma nacional 2017 diverge da
"população residente" publicada pelo INE (26.899.105) em
+3 pessoas — divergência esperada e
documentada em cada linha nacional do CSV (decisão do usuário de 2026-09-09:
usar a soma do COD-PS, não o total do INE, como base nacional).

### Regras de selo/nível aplicadas

População: 2017 observado/A; 2025 modelado/A; 1997/2007 observado com
nível B, C ou `ausente` conforme a fonte disponível para a unidade. Toda
linha `cagr_*`/`indice_base_*` carrega `nivel_fonte` = pior nível das duas
pontas e `selo` = **pior selo das duas pontas** (`_pior_selo`: `modelado` se
qualquer ponta for `modelado`; `interpolado` se nenhuma for `modelado` mas
alguma for `interpolado`; `observado` só se as duas forem). Não é uma regra
em função do ANO: a primeira versão desta regra dizia `selo = modelado`
sempre que uma ponta fosse 2025, e coincidia com o executado enquanto a
única origem de valor modelado fosse a projeção do INE para 2025 — errou no
primeiro caso em que não era, a Vila de Moatize (2017, `selo=modelado` por
ser estimativa dasimétrica sobre GRID3, não por ser 2025), cujo índice teria
saído `observado` pela regra por ano.

<!-- SECAO_DEMOGRAFIA_DASHBOARD_FIM -->
