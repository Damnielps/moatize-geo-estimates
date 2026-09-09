## Proveniência — OSM topônimos, vias e ferrovia (Fase 4, app)

Bbox AOI (config/study.yaml, com folga de 0,05°): minLon=33.45, minLat=-16.40, maxLon=34.15, maxLat=-16.05
Acesso: Overpass API, endpoint https://overpass-api.de/api/interpreter (HTTP 200 nas três consultas)
Data de acesso: 2026-09-08
Licença: ODbL 1.0 — © OpenStreetMap contributors — https://www.openstreetmap.org/copyright
CRS de saída: EPSG:4326, RFC 7946, sem membro `crs`.
Resolução/nível geográfico: estado atual da base OSM colaborativa (sem ano-âncora — não é série temporal histórica).

### data/raw/osm_lugares_aoi.geojson
- Query: `[out:json][timeout:120];(node["place"~"^(city|town|village|suburb|hamlet|neighbourhood)$"](-16.40,33.45,-16.05,34.15);way[...](mesmo filtro);relation[...](mesmo filtro););out center tags;`
- Feições retornadas: 23 (nós e centróides de polígonos com tag `place`)
- Campos: osm_type, osm_id, name, place

### data/raw/osm_vias_aoi.geojson
- Query: `[out:json][timeout:180];(way["highway"~"^(motorway|trunk|primary|secondary|tertiary)$"](-16.40,33.45,-16.05,34.15););out geom tags;`
- Feições retornadas: 219 — 0 motorway, 76 trunk, 17 primary, 23 secondary, 103 tertiary (inclui a N7, eixo Tete–Moatize, classificada como trunk/primary no OSM conforme o trecho)
- Campos: osm_id, highway, name, ref

### data/raw/osm_ferrovia_aoi.geojson
- Query: `[out:json][timeout:120];(way["railway"~"^(rail|light_rail|narrow_gauge)$"](-16.40,33.45,-16.05,34.15););out geom tags;`
- Feições retornadas: 57, todas `railway=rail` (0 light_rail, 0 narrow_gauge) — inclui a linha do Sena
- Campos: osm_id, railway, name, usage

Anos cobertos: nenhum — estado presente (2026-09-08) da base editável do OSM; não retroage a 1997–2025.
