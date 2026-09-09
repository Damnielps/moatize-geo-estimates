## OpenStreetMap — topônimos, malha rodoviária e ferroviária (AOI Tete–Moatize, Fase 4)

Fonte: OpenStreetMap, via Overpass API (`https://overpass-api.de/api/interpreter`).
Dado subjacente é OSM; a Overpass API é meio de acesso, não a fonte.

Licença observada: **Open Database License (ODbL) 1.0** — https://www.openstreetmap.org/copyright
Atribuição exigida: **"© OpenStreetMap contributors"** (ODbL 1.0, Anexo de Atribuição). O app
tem de exibir esta atribuição em qualquer mapa que use estas camadas.
Restrição relevante: compartilhamento de derivadas sob ODbL/licença compatível
(Share-Alike sobre o banco de dados).

| Camada | Arquivo | Feições | Status |
|---|---|---|---|
| Topônimos (place=city/town/village/suburb/hamlet/neighbourhood) | data/raw/osm_lugares_aoi.geojson | 23 | verificado |
| Malha rodoviária (highway=motorway/trunk/primary/secondary/tertiary) | data/raw/osm_vias_aoi.geojson | 219 (0 motorway, 76 trunk, 17 primary, 23 secondary, 103 tertiary) | verificado |
| Malha ferroviária (railway=rail/light_rail/narrow_gauge) | data/raw/osm_ferrovia_aoi.geojson | 57 (todas railway=rail; 0 light_rail, 0 narrow_gauge) | verificado |

Data de verificação: 2026-09-08.
Nível A/B/C: não classificado aqui — atribuição de nível é papel do `auditor-dados`.
