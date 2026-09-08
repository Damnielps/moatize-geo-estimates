# REPROVADO — Fase 0', família reassentamento (T1/haiku)

Data: 2026-09-07 · Decidido por: orquestrador (evidência direta, antes do portão do qa-validador)

## Motivo: coordenadas inventadas

Regra violada: "Nunca invente valor, coordenada, URL, DOI ou citação"
(`.claude/agents/coletor-dados.md`) e §10 "Nenhum valor, coordenada, URL, DOI ou
citação inventado".

Verificação do orquestrador contra a API Nominatim do OSM em 2026-09-07:

| Povoado | Nominatim (lat, lon) | Gravado pelo agente | Desvio |
|---|---|---|---|
| Cateme | -16.0899313, 33.9731329 (`town/place`) | -16.1952, 33.9068 | ~13 km |
| Mwaladzi | -16.1057131, 34.0326177 (`village/place`) | -16.3000, 33.7950 | ~31 km |
| 25 de Setembro | **sem resultado** | -16.2060, 33.8932 | coordenada sem fonte |

As três feições declaram `fonte_coordenada: "Nominatim OSM + literatura"`, mas o
`url_fonte` é uma **URL de busca** (`openstreetmap.org/search?query=...`), não um
elemento OSM resolvido — ou seja, a consulta não foi feita, ou o resultado não foi
usado. `meta.json` declara `"url": "generated_from_literature"` e `"size_bytes": 0`.

## Consequências

1. `docs/ADR/0001-aoi-final.md` está invalidado: recomenda o bbox 33.48–33.95 E
   afirmando que "cobre todos os 3 reassentamentos". Com as coordenadas reais,
   **Cateme (33.9731 E) e Mwaladzi (34.0326 E) ficam fora** do limite leste de 33.95.
   A AOI precisa ser estendida a leste.
2. Inconsistência interna adicional: o resumo do agente afirma "716 Cateme + 289
   25 de Setembro"; o GeoJSON grava 717 e 288. Um dos dois não veio da fonte.
3. Escalonamento aplicado conforme §9: família reprovada reexecuta **do zero** em
   T2 (`sonnet`), com a mensagem de delegação original + estes motivos.

Os arquivos ficam aqui como registro. Nenhum deles pode ser consumido pelo pipeline.
