# Licenças — Imagens Orbitais (Fase 0')

Registros de licença para fontes de imagens orbitais conforme §4.0 e §4.3 de CLAUDE.md.
Colunas: nome, URL canônica, licença, nível, restrições, citação exigida, data de verificação.

---

## Fontes de Imagem (Nível A — Aberto)

### Landsat Collection 2 Level 2

| Campo | Valor |
|---|---|
| **Nome** | Landsat Collection 2 Level-2 Science Products (USGS) |
| **URL canônica** | https://www.usgs.gov/landsat-missions/landsat-collection-2-level-2-science-products |
| **Licença** | Domínio Público — sem restrições de uso (Public Domain) |
| **Nível** | **A** (Aberto) |
| **Restrições** | Nenhuma; uso livre, redistribuição e derivadas permitidas |
| **Citação exigida** | Sim. Formato sugerido: "Landsat Collection 2 Level-2 Science Products courtesy of the U.S. Geological Survey" |
| **Data de verificação** | 2026-09-07 |
| **Nota** | USGS garante acesso anônimo e livre desde 2008; reformulação em Collection 2 (C2) mantém o status de domínio público. Acesso via EarthExplorer (https://earthexplorer.usgs.gov), AWS (Landsat on AWS), e plataformas STAC (Planetary Computer, Element84 Earth Search). Missões: Landsat 4–9 em L2 (L1 a partir de Landsat 1). |

---

### Sentinel-2 Level 2A

| Campo | Valor |
|---|---|
| **Nome** | Copernicus Sentinel-2 Level-2A (ESA / Copernicus) |
| **URL canônica** | https://dataspace.copernicus.eu/data-collections/copernicus-sentinel-missions/sentinel-2 |
| **Licença** | Copernicus Sentinel Data Licence (Regulamento UE) — Acesso livre, completo e aberto |
| **Nível** | **A** (Aberto) |
| **Restrições** | Nenhuma para fins não comerciais e comerciais (uso reprodução, distribuição, transformação, combinação permitidos sob EU Law). Proibido adicionar restrições técnicas/legais que limitem outros usos. |
| **Citação exigida** | Sim. Formato sugerido: "Copernicus Sentinel-2 data [ano], processed by [nome da instituição]" ou conforme guia ESA. Referência: https://open.esa.int/copernicus-sentinel-satellite-imagery-under-open-licence/ |
| **Data de verificação** | 2026-09-07 |
| **Nota** | Acesso via Copernicus Data Space Ecosystem (https://dataspace.copernicus.eu), plataformas STAC (Planetary Computer, Element84), Google Earth Engine. Dados nível 2A (SR — Surface Reflectance) desde dezembro de 2015 (missões S2A e S2B). Migração da legacy Copernicus Open Access Hub (encerrado outubro 2023) completada. |

---

## Plataformas STAC (Meios, não fontes — §4.0.3)

As plataformas abaixo **não são produtoras de dados**, mas meio de acesso STAC-compatível:

### Planetary Computer (Microsoft)

| Campo | Valor |
|---|---|
| **Nome** | Planetary Computer STAC API (Microsoft) |
| **URL canônica** | https://planetarycomputer.microsoft.com/api/stac/v1 |
| **Endpoint STAC** | POST `https://planetarycomputer.microsoft.com/api/stac/v1/search` |
| **Colecções testadas** | `landsat-c2-l2`, `sentinel-2-l2a`, Copernicus DEM, NAIP, etc. |
| **Termos de uso** | Acesso livre sem autenticação para uso educacional e de pesquisa; vide https://planetarycomputer.microsoft.com/terms |
| **Nota** | Plataforma STAC 1.0.0 compatível. Dados subjacentes (Landsat, Sentinel) mantêm licenças originais (A). **Corrigido em T2 (2026-09-07):** este endpoint **não fornece** `numberMatched`/`context.matched` na resposta de busca — o probe de T1 confundia o `limit` da página com a contagem real. O probe reescrito pagina via `links[].rel=="next"` e soma `numberReturned` por página até esgotar. Contagens medidas: ver `data/provenance_parts/imagem.md` (diverge do Element84 em 2 de 8 células testadas; discrepância registrada, não resolvida). |

### Element84 Earth Search

| Campo | Valor |
|---|---|
| **Nome** | Element84 Earth Search STAC API |
| **URL canônica** | https://www.element84.com/earth-search |
| **Endpoint STAC** | POST `https://earth-search.aws.element84.com/v1/search` |
| **Colecções** | `landsat-c2-l2`, `sentinel-2-l2a`, `sentinel-1`, Copernicus DEM |
| **Termos de uso** | Acesso livre; dados em AWS S3 (open data); vide https://element84.com/earth-search |
| **Nota** | Plataforma STAC compatível (open-source FilmDrop). Dados subjacentes mantêm licenças A. **Corrigido em T2 (2026-09-07):** o probe de T1 nunca consultou este endpoint (bug de implementação, gravava `não_testado` sem requisição). Reexecutado em T2 com `pipeline/00_fetch/probe_stac.py`: o endpoint **responde normalmente** via POST e devolve `numberMatched`/`context.matched` diretamente (não exige paginação manual, ao contrário do Planetary Computer). Contagens medidas batem exatamente com a verificação independente do orquestrador em todos os anos/coleções testados — ver `data/provenance_parts/imagem.md`. |

---

## Planet NICFI (Nível B — Livre com restrição)

| Campo | Valor |
|---|---|
| **Nome** | Planet NICFI Basemaps (Norway's International Climate and Forest Initiative) |
| **URL canônica** | https://www.planet.com/nicfi/ |
| **Colecções** | Mosaicos mensal Level 0 e 1 (4,77 m resolução); níveis de processamento superiores (Level 2) descontinuados |
| **Licença** | Acesso não comercial sob os termos do programa (quando ativo); vide https://www.planet.com/nicfi/ e FAQ em https://community.planet.com/nicfi-satellite-data-program-38/frequently-asked-questions-about-the-nicfi-data-program-99 |
| **Nível** | **B** (Livre com restrição) — **e, em 2026, na prática inacessível: programa descontinuado sem sucessor ativo** |
| **Restrições** | (i) Uso exclusivamente não comercial; (ii) redistribuição do dado bruto proibida; (iii) acesso previsto apenas via plataformas colaborativas (GEE, QGIS plugin, ArcGIS) — nunca armazenar em repositório público |
| **Citação exigida** | Sim, quando acessível. Conforme guia: "Planet-NICFI [ano], accessed [data]" |
| **Data de verificação** | 2026-09-07 |
| **Nota (atualizada em T2)** | **Situação confirmada por busca em 2026-09-07: o programa está descontinuado.** O contrato do NICFI Satellite Data Program com a Planet expirou em 23/01/2025 (https://www.nicfi.no/2025/01/28/nicfi-satellite-data-program-enters-new-phase/); acesso de nível 0/1 foi temporariamente estendido pela Planet/KSAT até 01/04/2025, quando o acesso a mosaicos de alta resolução foi encerrado em plataformas terceiras (Global Forest Watch, Collect Earth, etc.); em setembro de 2025 o governo da Noruega **cancelou** o processo de licitação para a fase seguinte, sem substituto lançado até a data de verificação. Não há endpoint ativo a consultar; nenhum script de obtenção foi escrito em `pipeline/00_fetch/` por essa razão. Cobertura original incluía Moçambique (Tete–Moatize dentro da zona tropical de cobertura), mas isso é agora irrelevante na prática — o dado não está disponível para uso no pipeline em 2026. |

---

## Google Earth Engine (Plataforma, não fonte)

| Campo | Valor |
|---|---|
| **Nome** | Google Earth Engine (GEE) |
| **URL canônica** | https://earthengine.google.com |
| **Colecções relevantes** | LANDSAT/LE07/C02, LANDSAT/LT05/C02, LANDSAT/LC08/C02, COPERNICUS/S2_SR_HARMONIZED |
| **Termos de uso** | Acesso requer cadastro Google; uso livre para pesquisa, educação, não comercial; repositório não pode depender exclusivamente de GEE (§11.3 CLAUDE.md) |
| **Nota** | Plataforma de processamento, não fonte primária. Dados subjacentes mantêm licenças A. Rota alternativa obrigatória: STAC (Planetary Computer, Element84). |

---

## Resumo de Disponibilidade (Reexecução T2 — 2026-09-07)

Ver medição completa e discussão da discrepância em
`data/provenance_parts/imagem.md`. Contagens de referência
(Element84, `numberMatched`) confirmadas de forma independente pelo
orquestrador em todas as células:

| Missão | Ano | Landsat PC | Landsat E84 | Sentinel-2 PC | Sentinel-2 E84 | Nota |
|---|---|---|---|---|---|---|
| Landsat 7 ETM+ | 2000 | 7 | 7 | n/a | n/a | pré-SLC-off |
| Landsat 5 TM | 2005 | 6 | 6 | n/a | n/a | — |
| Landsat 5 TM | 2010 | 4 | 4 | n/a | n/a | limite crítico p/ mediana — ver diagnóstico |
| Landsat 8 OLI | 2015 | 19 | 19 | 0 | 0 | S2 ainda não cobre a AOI em 2015 |
| Landsat 8 OLI | 2020 | 16 | 16 | 103 | 194 | discrepância PC×E84 registrada, não resolvida |
| Landsat 9 OLI-2 | 2025 | 16 | 18 | 162 | 162 | discrepância pequena em landsat |

---

**Arquivo gerado:** 2026-09-07 (Fase 0' — Reconhecimento)  
**Reexecutado (T2):** 2026-09-07 — bug de contagem e de Element84 não testado corrigidos.
**Próximo passo:** Fase 1 — `fetch_stac.py` para download real das cenas via Element84 (referência) com PC como espelho.
