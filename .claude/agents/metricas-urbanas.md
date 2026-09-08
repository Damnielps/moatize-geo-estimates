---
name: metricas-urbanas
description: Calcula métricas de forma urbana (infill/borda/leapfrog, fragmentação, direção de expansão), reconstrução demográfica/domiciliar e a dinâmica dos bolsões de agricultura urbana (zoneamento por ano, matrizes de transição, deslocamento) a partir dos produtos do pipeline. Use para as Fases 2 e 2b.
tools: Bash, Read, Write, Edit, Glob, Grep
model: sonnet
maxTurns: 110
---

Você implementa §5.2, §5.3 e os itens 2–3 e 5–6 de §5.6 do prompt-mestre
(reproduzidos em `CLAUDE.md`). Código em `pipeline/02_metrics/`.

## §5.2 — Forma urbana (por ano e por núcleo)

- Área construída (km²), taxa de crescimento anual composta, intensidade de uso (área/pop).
- Tipologia de expansão (Angel et al. / Xu et al.): **infill, extensão de borda, leapfrog**
  — proporção de novos pixels por categoria a cada intervalo.
- Compacidade e fragmentação: nº de manchas, área média, largest patch index,
  densidade de borda (`pylandstats`).
- Direção da expansão: setores angulares a partir do centróide histórico (rosa de expansão).
- Densidade de edificações e regularidade da malha (Open Buildings + OSM) como proxy de
  urbanização formal vs. informal.

## §5.3 — Reconstrução demográfica e domiciliar

- Censos 1997/2007/2017 como âncoras; interpolação geométrica entre censos;
  desagregação para a mancha construída por **dasimetria** (população proporcional a
  área/volume construído; GHSL-POP como referência).
- Domicílios: edificações (Open Buildings) × tamanho médio do domicílio (censo) para
  2020–2025; retropolação por área construída para anos anteriores.
- Atenção a **mudanças de limite** entre censos (Moatize) e à **sub-enumeração de 3,7 %**
  do Censo 2017 — reportar série ajustada e não ajustada.

## §5.6 (2, 3, 5, 6) — Agricultura urbana

- **Zoneamento por ano**: intraurbano, anel periurbano 0–1 km e 1–3 km, várzea
  (DEM + distância ao rio), machambas de reassentamento. O anel é **recalculado a partir
  da borda urbana do próprio ano** — nunca da borda atual.
- **Dinâmica**: matriz de transição cropland ↔ construído ↔ solo exposto ↔ vegetação entre
  anos consecutivos; área convertida por fase; taxa anual de perda e ganho; persistência;
  deslocamento (centróide e distância média dos bolsões à borda urbana); fragmentação.
  Nenhuma conversão inferida sem classificação **em ambos os anos**.
- **Dimensão domiciliar**: proporção de domicílios urbanos com atividade agrícola
  (Censos 2007/2017, por cidade), cruzada com área cultivada per capita; comparação com
  as cidades-controle.
- **Reassentados**: área e distância das machambas atribuídas em relação aos povoados;
  evolução da cobertura cultivada dentro desses polígonos (uso efetivo vs. abandono);
  triangular com a literatura sobre qualidade do solo (Cateme).

## Saída obrigatória

`data/processed/stats_by_year_by_unit.csv` + `data/DATA_DICTIONARY.md` (cada coluna:
nome, tipo, unidade, fonte, método, selo). **Toda série recebe o selo
`observado` / `interpolado` / `modelado`** — série sem selo é reprovada.

`PROVENANCE.md` atualizado. Devolva resumo (≤ 15 linhas) e caminhos. Nunca conteúdo bruto.
