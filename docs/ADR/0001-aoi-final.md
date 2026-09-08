# ADR 0001 — Correção do bbox provisório da AOI (extensão a leste para incluir Cateme e Mwaladzi)

- **Data:** 2026-09-07
- **Fase:** 0' (Reconhecimento)
- **Decidido por:** `coletor-dados` (proposta) — aplicação em `config/study.yaml` é decisão do orquestrador
- **Estado:** proposto (não aplicado)

## Contexto

`config/study.yaml` define a AOI provisória (§3 de CLAUDE.md) como:

```
xmin: 33.50, ymin: -16.35, xmax: 33.95, ymax: -16.00   (EPSG:4326)
```

O georreferenciamento dos povoados de reassentamento (Fase 0', aprovado em T2,
`data/raw/reassentamentos.geojson`) fixou coordenadas verificadas via OSM/Nominatim:

| Ponto | Longitude E | Latitude S | Dentro do bbox atual? |
|---|---|---|---|
| Cateme | 33.9731329 | -16.0899313 | **Não** — 33.9731 > xmax 33.95 |
| Mwaladzi | 34.0326177 | -16.1057131 | **Não** — 34.0326 > xmax 33.95 |
| 25 de Setembro | sem geometria (não localizada) | — | não aplicável |
| Cidade de Tete | 33.5871 | -16.1604 | Sim |
| Vila de Moatize | 33.7288 | -16.1178 | Sim |
| Mina de Moatize (âncora §8) | 33.7895 | -16.1678 | Sim |

Dois dos três povoados de reassentamento com geometria confirmada **ficam fora** do
limite leste (`xmax = 33.95`) do bbox provisório. Um estudo cuja pergunta central
(§1) trata explicitamente de reassentamentos não pode ter uma AOI que exclui os
próprios povoados de reassentamento. O limite norte (`ymax = -16.00`) e os limites
oeste/sul (`xmin = 33.50`, `ymin = -16.35`), em contraste, já comportam todos os
pontos verificados com folga (menor distância à borda: Cateme a ~0,090° do limite
norte, ≈ 10 km — acima da margem de 3 km exigida pelo anel periurbano de §3).

§3 exige ainda margem para (i) o anel periurbano recalculado ano a ano (0–3 km da
borda urbana de cada época) e (ii) o corredor logístico/ferroviário (linha do Sena,
que segue a leste de Moatize em direção a Mwaladzi/Beira). O CRS métrico do projeto,
EPSG:32736 (UTM zona 36S), é válido para 30°E–36°E — qualquer bbox candidato deve
permanecer dentro dessa faixa.

## Decisão

Estender o limite leste do bbox provisório de `xmax = 33.95` para **`xmax = 34.10`**,
mantendo os demais limites (`xmin = 33.50`, `ymin = -16.35`, `ymax = -16.00`)
inalterados nesta rodada, por já comportarem todos os pontos verificados com margem
suficiente.

**Bbox proposto (EPSG:4326):** `xmin=33.50, ymin=-16.35, xmax=34.10, ymax=-16.00`.

Justificativa ponto a ponto:

1. **Cateme (33.9731 E)** — passa a ficar a ≈ 0,127° (≈ 13,6 km) do novo limite leste,
   dentro do polígono com folga ampla para o anel periurbano de 3 km.
2. **Mwaladzi (34.0326 E)** — ponto mais oriental conhecido da AOI. A margem calculada
   para cobrir o anel periurbano de 3 km a partir de qualquer borda urbana futura em
   torno de Mwaladzi é de ≈ 0,028° de longitude nessa latitude (3 km / 106,9 km por
   grau de longitude a -16° de latitude, com cos(16°) ≈ 0,961). `34.0326 + 0,028 ≈
   34,061`. O valor adotado, `34.10`, acrescenta margem adicional (≈ 7,5 km além do
   ponto) para cobrir o traçado do corredor ferroviário/logístico que segue a leste de
   Moatize e para não exigir novo ajuste caso a geometria de 25 de Setembro venha a ser
   localizada mais a leste que Mwaladzi (não esperado, mas não descartado).
3. **Limite norte (`ymax = -16.00`)** — mantido. Cateme (-16.0899) e Mwaladzi
   (-16.1057) ficam a ≥ 0,090° (≥ 9,7 km) do limite, e a Cidade de Tete (-16.1604) e a
   mina de Moatize (-16.1678) ficam ainda mais distantes. Não há indício, nos pontos
   verificados, de necessidade de estender a AOI mais ao norte.
4. **Limite oeste (`xmin = 33.50`)** — mantido. A Cidade de Tete (33.5871) fica a
   ≈ 0,087° (≈ 9,3 km) do limite, distância que já excede a margem de 3 km exigida
   pelo anel periurbano do lado oeste da cidade.
5. **Limite sul (`ymin = -16.35`)** — mantido. Nenhum ponto verificado nesta fase se
   aproxima do limite sul; folga de ≥ 0,18° (≥ 20 km) em relação ao ponto mais ao sul
   conhecido (mina de Moatize, -16.1678).
6. **EPSG:32736 (UTM 36S), válido 30°E–36°E** — o bbox proposto (33.50°E–34.10°E) está
   inteiramente contido nessa faixa; nenhuma reprojeção adicional é necessária.

## Alternativa rejeitada

**Manter `xmax = 33.95` e tratar Cateme/Mwaladzi como pontos "fora da AOI", analisados
à parte.** Rejeitada porque:

1. contraria §3 ("Povoados de reassentamento — georreferenciar... Cateme, 25 de
   Setembro, Mwaladzi") e §1 (pergunta 3, sobre onde estão e como evoluem os
   reassentamentos): excluir 2 dos 3 povoados verificados da AOI principal
   inviabilizaria a análise de forma urbana e de anel periurbano exatamente para os
   casos mais sensíveis do estudo (reassentamento rural, IRR/PS5, §0);
2. geraria uma AOI descontínua ou um recorte ad hoc por povoado, complicando o
   pipeline de imagem (§5.1, "mesmo protocolo em todos os anos" sobre uma única AOI)
   sem ganho de simplicidade real, já que a extensão para leste é pequena (0,15°,
   ≈ 16 km) e permanece dentro da faixa válida de EPSG:32736.

## Consequência

- `config/study.yaml` deve ser atualizado por decisão do orquestrador para
  `aoi.bbox.xmax = 34.10` (mantendo `xmin=33.50`, `ymin=-16.35`, `ymax=-16.00`) e
  `aoi.status` alterado de `provisorio` para `confirmado` somente após essa aplicação.
- Nenhum artefato de `data/raw/` ou `data/processed/` depende do bbox nesta fase
  (nenhuma imagem foi baixada ainda) — a mudança não invalida proveniência existente.
- Áreas de imagem/composto (§5.1) e zoneamento de agricultura urbana (§5.6.2) que
  vierem a ser calculados devem usar o bbox corrigido, não o provisório de
  `33.50–33.95`.

---

## Adendo do orquestrador — aplicação (2026-09-07)

Proposta **aceita e aplicada**: `config/study.yaml` agora tem `aoi.bbox.xmax = 34.10` e
`aoi.status = confirmado`.

Uma consequência que a proposta não registrou: **o probe STAC de `data/interim/
stac_disponibilidade.csv` foi medido com o bbox provisório** (`33.50–33.95`). Como
`probe_stac.py` lê a AOI de `config/study.yaml`, a contagem de cenas por ano muda com a
AOI ampliada — uma AOI maior tende a intersectar mais órbitas/tiles. O probe foi
**reexecutado** após a aplicação, e o CSV publicado corresponde ao bbox confirmado.

Acrescentado também um contrato em `pipeline/tests/test_config.py` que falha se algum
povoado de reassentamento com geometria em `data/raw/reassentamentos.geojson` cair fora
da AOI. O erro que este ADR corrige era silencioso: nada no repositório o teria acusado.
