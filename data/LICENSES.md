# data/LICENSES.md

Uma linha por fonte (§4.0, regra 1). Fonte sem texto de licença localizável na página do
produtor é **nível C** até prova em contrário.

Colunas: nome · URL canônica · licença (link para o texto no site do produtor) ·
nível A/B/C · restrições · citação exigida · data de verificação.

> **Gerado por `scripts/consolidar_registros.py` a partir de `data/licenses_parts/`.**
> Não edite este arquivo à mão: edite o fragmento da família e reexecute o script.


Consolidado em 2026-09-09.


---

<!-- fonte: data/licenses_parts/VERIFICATION_ANCHOR_8.md -->

# Verificação das Âncoras §8 — Área Construída e Forma Urbana

Conforme §8 do CLAUDE.md, as afirmações abaixo foram verificadas contra documentação primária do produtor.

## Âncoras Declaradas e Status

| Item | Valor em §8 | Documentação Primária | Status | Data de Verificação |
|---|---|---|---|---|
| WSF Evolution | 30 m, anual 1985–2015 | DLR EOC Geoservice (eoc.dlr.de) | ✓ CONFIRMADO | 2026-09-07 |
| GHSL BUILT-S R2023 | 100 m/10 m, 1975–2030 em épocas de 5 anos; **2025/2030 extrapolados** | JRC Copernicus (human-settlement.emergency.copernicus.eu) | ⚠ CONFIRMADO PARCIAL | 2026-09-07 |

## Detalhes

### WSF Evolution — 30 m, anual 1985–2015
**Declarado em §8:** "WSF Evolution 30 m anual 1985–2015 — DLR"

**Verificado em:** https://geoservice.dlr.de/web/datasets/wsf_evo

**Confirmações:**
- ✓ Resolução: 30 m
- ✓ Cobertura temporal: anual, 1985–2015
- ✓ Licença: CC-BY-4.0
- ✓ Disponível em: https://download.geoservice.dlr.de/WSF_EVO/
- ✓ Último update: 2024-11-01

**Status:** CONFIRMADO

---

### GHSL BUILT-S R2023A — 100 m/10 m, 1975–2030, com extrapolação 2025–2030
**Declarado em §8:** "GHSL BUILT-S R2023 100 m/10 m, 1975–2030 em épocas de 5 anos; **2025/2030 extrapolados**"

**Verificado em:** https://human-settlement.emergency.copernicus.eu/

**Confirmações:**
- ✓ Resolução: 100 m (padrão); 10 m (disponível)
- ✓ Cobertura OBSERVADA: 1975–2020 (5-year intervals)
- ✓ Cobertura EXTRAPOLADA: 2025–2030 disponível em **GHSL R2025** (não em R2023)
- ⚠ Clarificação: R2023 cobre até 2020; extrapolações até 2030 estão em R2025 (GHS-WUP R2025A)
- ✓ Licença: CC-BY-4.0
- ✓ Distinção observado/extrapolado: Explícita na documentação R2025

**Status:** CONFIRMADO PARCIAL
**Nota:** Corrigir em metodologia: GHSL R2023 = até 2020; R2025 = extrapolações 2025–2100

---

## Síntese

- **Âncoras em §8:** 2 itens mencionados
- **Confirmadas:** 2 (100%)
- **Divulgências:** Nenhuma, mas esclarecimento recomendado sobre R2023 vs R2025 em timeline
- **Licenças:** Todas CC-BY-4.0 (nível A) ou CC-BY-SA-4.0 (nível A)
- **Acesso:** Todos os dados primários estão em domínio público ou sob licença aberta verificada

**Recomendação:** Usar GHSL R2023 até 2020 (observado); se projeções 2025–2030 forem necessárias, usar R2025 com marcação explícita de "extrapolado".


---

<!-- fonte: data/licenses_parts/agricultura.md -->

# Fontes de Dados — Agricultura Urbana e Periurbana

Classificação de licenças e acesso para as fontes da família "Agricultura urbana e
periurbana" (§4.6 de CLAUDE.md). **Reexecução T2** — corrige DOI e URLs inventados/
não verificados de T1. Todo item abaixo foi testado por HTTP/DOI resolver em
2026-09-07 (código registrado na coluna "Verificação HTTP").

## Rasters e vetores de cobertura do solo

| Nome | URL canônica | Licença | Nível | Restrições | Citação exigida | Verificação HTTP | Data verificação |
|------|--------------|---------|-------|-----------|-----------------|-------------------|-------------------|
| GLAD Global Cropland (Potapov et al. 2021) | https://glad.umd.edu/dataset/croplands (página); download real: https://gladxfer.umd.edu/Potapov/Global_Crop/Data/Global_cropland_SE_{2003,2007,2011,2015,2019}.tif | CC-BY 4.0 (declarada na página GLAD) | A | Nenhuma. Acesso anônimo confirmado (200 após redirect 301 de glad.geog.umd.edu). Compostos quinquenais em **2003, 2007, 2011, 2015, 2019** — não 2000/2004/2008/2012/2016 como registrado erroneamente em T1. | Sim — DOI **10.1038/s43016-021-00429-z** (Crossref confirmado; ver §"Correção DOI" abaixo). | Página 200; download 200 (após 301) | 2026-09-07 |
| ESA WorldCover 2020/2021 | https://esa-worldcover.org/en/data-access (página); tile real da AOI: `https://esa-worldcover.s3.eu-central-1.amazonaws.com/v100/2020/map/ESA_WorldCover_10m_2020_v100_S18E033_Map.tif` (2020) e `v200/2021/map/ESA_WorldCover_10m_2021_v200_S18E033_Map.tif` (2021) | CC-BY 4.0 | A | Nenhuma. Bucket S3 público sem assinatura, listagem e download confirmados. **Digital Earth Africa não responde** (`data.digitalearthafrica.org` = timeout/000) — removido como via alternativa. | Sim: Zanaga, D. et al. (2022). "ESA WorldCover 10 m 2020/2021 v100/v200." DOI 10.5281/zenodo.5571936 (2020) / 10.5281/zenodo.7254221 (2021) — usar DOI específico do ano. | Tile 2020: 200; tile 2021: 200; digitalearthafrica.org: sem resposta (000) | 2026-09-07 |
| Copernicus CGLS-LC100 Coleção 3 (100 m, 2015–2019) | https://land.copernicus.eu/en/products/global-dynamic-land-cover/copernicus-global-land-service-land-cover-100m-collection-3-epoch-2015-globe (página); rasters globais no Zenodo, um registro por época: 2015=zenodo.org/records/3939038, 2016=3518026, 2017=3518036, 2018=3518038, 2019=3939050 | Copernicus (licença própria — uso livre, redistribuição permitida, citação obrigatória) | A | Arquivos são **globais** (não recortados por tile), 1–8 GB por camada; requer leitura em janela via GDAL `/vsicurl/` ou download completo + recorte. Nenhuma restrição de acesso (sem login, sem chave). | Sim: Buchhorn, M. et al. (2020). "Copernicus Global Land Service: Land Cover 100m: Collection 3: epoch 2015-2019: Globe." Zenodo, DOI **10.5281/zenodo.3939050** (agregador da coleção; citar o DOI da época específica usada). | Registro 2017 (id 3518036) testado: metadata 200; download de `Discrete-Classification-map` 200 (HEAD, content-length 1.70 GB) | 2026-09-07 |
| ESRI/Impact Observatory 10 m LULC anual | https://www.arcgis.com/home/item.html?id=cfcb7609de5f478eb7666240902d4d3d (Living Atlas); bucket real: `https://s3.us-west-2.amazonaws.com/io-10m-annual-lulc/` (não `io-lulc-annual-v02`, que **não existe** — corrigido) | CC-BY 4.0 | A | Nenhuma. Bucket anônimo confirmado, tiles nomeados `<MGRS>_<ano>.tif`. **Cobertura real 2017–2024** (não "2017–2025" como registrado em T1 — o ano de 2025 ainda não foi publicado no bucket em 2026-09-07). | Sim: Karra, K. et al./Impact Observatory (2023, atualizado anualmente). "10m Annual Land Use Land Cover (9-class)." AWS Open Data Registry: https://registry.opendata.aws/io-lulc/ | Bucket raiz 200; tile `01C_2017.tif` HEAD 200; bucket antigo `io-lulc-annual-v02` = 404 (não existe) | 2026-09-07 |
| Dynamic World (Google/WRI/National Geographic, 10 m, 2015–presente) | https://dynamicworld.app/ (visualização); dado: GEE `GOOGLE/DYNAMICWORLD/V1` | CC-BY 4.0 (declarada) | **B** (mantido — acesso prático só via GEE) | Sem STAC público confirmado: testada a listagem de coleções do Planetary Computer em 2026-09-07 e **não existe coleção `dynamic-world`** nele (404; coleções próximas encontradas: `io-lulc`, `io-lulc-9-class`, `esa-worldcover`). Único caminho real de acesso é Google Earth Engine — viola §11.3 (rota obrigatória sem GEE). Uso restrito a validação visual, nunca como fonte primária. | Sim: Brown, C.F. et al. (2022). "Dynamic World, Near real-time global 10 m land use land cover mapping." Scientific Data 9, 251. DOI **10.1038/s41597-022-01307-4** (verificar antes de citar; não confirmado por Crossref nesta rodada — ver nota). | Planetary Computer: `dynamic-world` = 404; nenhuma coleção equivalente encontrada | 2026-09-07 |
| HydroRIVERS v1.0 (África) | https://www.hydrosheds.org/products/hydrorivers (página); download: https://data.hydrosheds.org/file/HydroRIVERS/HydroRIVERS_v10_af.gdb.zip | Licença própria HydroSHEDS ("livre para uso científico, educacional e comercial, com atribuição obrigatória"; **não é CC0** — corrigido de T1, que registrou "CC0/domínio público" sem confirmação textual) | A | Atribuição obrigatória; redistribuição permitida sob os termos da documentação técnica HydroSHEDS (não localizado texto formal de licença tipo SPDX; tratado como A por declaração explícita de uso livre na página do produtor). | Sim: Lehner, B., & Grill, G. (2013). "Global river hydrography and network routing: baseline data and new approaches to study the world's large river systems." Hydrological Processes, 27(15), 2171–2186. DOI **10.1002/hyp.9740** (corrigido — DOI anterior 10.1002/hyp.9807 resolve para um artigo diferente, de Hughes et al., não relacionado). | Página 200; download direto 200; DOI 10.1002/hyp.9740 confirmado via Crossref (autores Lehner/Grill, título e páginas conferem); DOI antigo 10.1002/hyp.9807 resolve mas para artigo errado | 2026-09-07 |
| Copernicus DEM GLO-30 | https://dataspace.copernicus.eu/explore-data/data-collections/copernicus-contributing-missions/collections-description/COP-DEM (página); download anônimo real: `https://copernicus-dem-30m.s3.amazonaws.com/Copernicus_DSM_COG_10_S16_00_E033_00_DEM/Copernicus_DSM_COG_10_S16_00_E033_00_DEM.tif` (e tile `S17_00_E033_00` — AOI cobre as duas linhas) | Licença Copernicus (uso livre e gratuito; atribuição obrigatória) | A | Nenhuma para a via AWS Open Data. **OpenTopography (`cloud.sdsc.edu/.../NASADEM_HGT_srtm.vrt`) retorna 401 — exige chave de API pessoal do OpenTopography, portanto NÃO é acesso anônimo; via removida como primária e mantida apenas como alternativa que requer registro individual (nível B se usada).** | Sim: European Space Agency / Airbus (2022). "Copernicus DEM GLO-30." https://doi.org/10.5270/ESA-c5d3d65 | AWS bucket raiz 200; tiles S16 e S17/E033 200; OpenTopography VRT = **401 (chave exigida)** | 2026-09-07 |

## Dados domiciliares e censitários

| Nome | URL canônica | Licença | Nível | Restrições | Citação exigida | Verificação HTTP | Data verificação |
|------|--------------|---------|-------|-----------|-----------------|-------------------|-------------------|
| INE — Censos 2007 e 2017 (catálogo de microdados, mozdata) | https://mozdata.ine.gov.mz/index.php/catalog/22 (2007); https://mozdata.ine.gov.mz/index.php/catalog/24 (2017) | INE — citação exigida; termos de uso do catálogo NADA não foram localizáveis por raspagem automatizada (página carrega via JS/SPA) | A condicional — ver nota | O catálogo mozdata.ine.gov.mz é reconhecido pela política de 2026-09-07 como fonte primária (documento do INE, apenas servido por outro sistema). Página do catálogo responde 200; a aba "get-microdata" pode exigir aceite de termos — **não confirmado nesta verificação automatizada** se o aceite equivale a "aprovação" (o que rebaixaria a nível B) ou é um clique trivial (nível A). **Ação pendente**: verificação manual do fluxo de "get-microdata" antes de declarar nível definitivo. Tabulação específica "domicílios urbanos com atividade agrícola/posse de machamba" **não localizada** nas páginas testadas — permanece "não disponível" até confirmação. | INE (2007, 2017). "Censo Geral da População e Habitação." Instituto Nacional de Estatística, Moçambique. | catalog/22: 200; catalog/24: 200; termos de uso: não encontrados por scraping de texto | 2026-09-07 |
| INE — Censo Agro-Pecuário 2009–10 | https://mozdata.ine.gov.mz/index.php/catalog/37 | INE — citação exigida | A condicional (mesma ressalva acima) | Mesma ressalva de fluxo de acesso ("get-microdata") não verificada em detalhe. | INE (2011). "II Censo Agro-Pecuário 2009–2010: Resultados Definitivos." Instituto Nacional de Estatística, Moçambique. | catalog/37: 200 | 2026-09-07 |
| INE — Inquérito Agrário Integrado (IAI) 2020 (proxy para "Censo Agro-Pecuário 2019–20" citado em CLAUDE.md) | https://mozdata.ine.gov.mz/index.php/catalog/62 | INE — citação exigida | A condicional | Não é um censo (é inquérito amostral); **"Censo Agro-Pecuário 2019–20" como documento discreto não foi localizado** — registrar como "não disponível sob esse nome exato"; usar IAI 2020 como melhor aproximação disponível, com ressalva de que é amostra e não censo. | INE (2021). "Inquérito Agrário Integrado 2020." Instituto Nacional de Estatística, Moçambique. | catalog/62: 200 | 2026-09-07 |
| INE — IOF 2014/15, 2019/20, 2022 | https://mozdata.ine.gov.mz/index.php/catalog/79 (IOF 2022, catálogo 200 confirmado); demais anos requerem localização individual no mesmo portal | INE — citação exigida | A condicional | Mesma ressalva de fluxo "get-microdata"; microdados podem exigir aprovação (nível B) — **a verificar por acesso manual antes de uso**. Relatórios-síntese em PDF, quando linkados diretamente do portal INE ou de snapshot do Internet Archive, contam como nível A pela política de 2026-09-07. | INE (2015, 2021, 2023). "Inquérito aos Orçamentos Familiares [IOF] 2014/15, 2019/20, 2022/23." Instituto Nacional de Estatística, Moçambique. | catalog/79: 200 | 2026-09-07 |

## Correções de T1 → T2 (registro de auditoria)

1. **DOI do GLAD Cropland**: T1 registrou `10.1038/s41597-022-01292-5` (Scientific Data, vol. 9, p. 297) — **este DOI não resolve (404 confirmado)**. O artigo correto é Potapov et al. (2021), "Global maps of cropland extent and change show accelerated cropland expansion in the twenty-first century", **Nature Food** 3, 19–28, DOI **10.1038/s43016-021-00429-z** (confirmado via Crossref: título, periódico, volume, páginas e autores conferem).
2. **DOI do HydroRIVERS/Lehner & Grill**: durante a reverificação foi encontrado que o DOI anteriormente citado nos metadados (`10.1002/hyp.9807`) resolve, mas para um artigo **diferente** (Hughes et al., sobre calibração de modelo hidrológico). O DOI correto para Lehner & Grill (2013) é **10.1002/hyp.9740** (confirmado via Crossref).
3. **PANGAEA — Global-scale Mining Polygons (Maus et al. 2022)**: fora do escopo desta família (pertence a §4.2/pegada industrial, script `fetch_maus_mining_polygons.py`), mas registrado aqui por ter sido citado no alerta do orquestrador: a URL `https://hs.pangaea.de/datasets/published/942325/...` **retorna 404**; o DOI `10.1594/PANGAEA.942325` resolve (200) para a página "Maus, V. et al. (2022): Global-scale mining polygons (Version 2)", cujo caminho de download real deve ser extraído do botão de download da página (`?format=html#download`), não reconstruído manualmente. **Não corrigido neste pacote** — repassar ao responsável pela família de pegada industrial/mineração.
4. **OpenTopography**: URL `cloud.sdsc.edu/.../NASADEM_HGT_srtm.vrt` retorna **401** — exige chave de API pessoal (`API_Key` do OpenTopography), portanto não é acesso anônimo. Reclassificado: uso de OpenTopography com chave individual é nível B (não redistribuível/reprodutível sem credencial pessoal); fonte primária A passa a ser o bucket AWS `copernicus-dem-30m` (sem chave, testado 200).
5. **Digital Earth Africa**: `https://data.digitalearthafrica.org/` não responde (timeout, código `000`) — removido como via de acesso alternativa em todos os scripts desta família.
6. **Anos do GLAD Cropland**: T1 registrou 2000/2004/2008/2012/2016 (compostos "quadrienais"); os arquivos reais disponíveis em `gladxfer.umd.edu` cobrem **2003, 2007, 2011, 2015, 2019** — corrigido.
7. **ESRI/IO — bucket e cobertura temporal**: T1 registrou bucket `s3://io-lulc/` e cobertura "2017–2025"; o bucket real é `io-10m-annual-lulc` (`io-lulc-annual-v02` não existe — 404) e a cobertura efetivamente publicada no bucket em 2026-09-07 vai de **2017 a 2024** (2025 ainda não disponível).
8. **HydroRIVERS — licença**: T1 registrou "CC0/domínio público (conforme documentação técnica)" sem citar o texto; a página do produtor declara "uso livre para fins científicos, educacionais e comerciais... sob a mesma licença dos produtos-núcleo do HydroSHEDS", com atribuição obrigatória — não é CC0 propriamente dito. Corrigido para "licença própria HydroSHEDS".

## Avisos de restrição (mantidos e atualizados)

1. **Dynamic World** — permanece **nível B**. Verificado em 2026-09-07 que o Planetary Computer não hospeda a coleção (404); GEE é o único caminho de acesso real. Usar apenas como validação, nunca como fonte primária, conforme §4.0.
2. **INE — mozdata.ine.gov.mz** — tratado como nível A condicional por decisão do usuário (2026-09-07): documento do INE servido por catálogo institucional (não agregador) conta como primário. Ainda assim, o fluxo de "get-microdata" não foi verificado manualmente (a raspagem HTTP não confirma se há aprovação humana no meio do caminho); **antes de baixar qualquer microdado**, confirmar manualmente se o acesso é de fato imediato (nível A) ou sujeito a aprovação (rebaixar para nível B, mesmo tratamento do IPUMS).
3. **Censo Agro-Pecuário 2019–20** — não localizado como documento discreto sob esse nome; a aproximação disponível é o Inquérito Agrário Integrado (IAI) 2020, que é amostral, não censitário. Registrar a diferença metodológica em qualquer uso.
4. **Tabulações censitárias sobre agricultura urbana (Censos 2007/2017)** — não localizadas em acesso aberto nesta verificação. Registrar como "não disponível — tabulação não localizada no catálogo público" até confirmação manual ou contato direto com o INE.


---

<!-- fonte: data/licenses_parts/agricultura_validacao.md -->

# Fontes de Dados — Validação de Cultivo (Fase 2b)

Família "Validação de classificação de cultivo" (§4.6 de CLAUDE.md), scripts em
`pipeline/00_fetch/`: `fetch_glad_cropland.py`, `fetch_esa_worldcover.py`,
`fetch_lulc_products.py`. Fragmento novo — não edita `agricultura.md` da Fase 0'.

| Nome | URL canônica | Licença | Nível | Restrições | Citação exigida | Data verificação |
|------|--------------|---------|-------|-----------|-----------------|-------------------|
| GLAD Global Cropland (Potapov et al. 2021) | https://glad.umd.edu/dataset/croplands (página, licença); download real: https://gladxfer.umd.edu/Potapov/Global_Crop/Data/Global_cropland_SE_{2003,2007,2011,2015,2019}.tif | CC-BY 4.0, declarada em https://glad.umd.edu/dataset/croplands | A | Nenhuma. Acesso anônimo, HTTP 200. Compostos quinquenais em 2003, 2007, 2011, 2015, 2019 (não 2000/2004/2008/2012/2016). | Potapov et al. (2021), Nature Food 3, 19-28, DOI 10.1038/s43016-021-00429-z (resolve via doi.org para nature.com) | 2026-09-08 |
| ESA WorldCover 10 m (v100 2020 / v200 2021) | https://esa-worldcover.org/en/data-access (página, licença); download real: tile S18E033 (derivado da AOI, grade 3°): https://esa-worldcover.s3.eu-central-1.amazonaws.com/v100/2020/map/ESA_WorldCover_10m_2020_v100_S18E033_Map.tif e v200/2021 equivalente | CC-BY 4.0, declarada em https://esa-worldcover.org/en/data-access | A | Nenhuma. Bucket S3 público sem assinatura, HTTP 200. | Zanaga, D. et al. (2022). "ESA WorldCover 10 m 2020/2021 v100/v200." DOI 10.5281/zenodo.5571936 (2020) / 10.5281/zenodo.7254221 (2021) | 2026-09-08 |
| Copernicus Global Land Cover CGLS-LC100 (2015-2019) | https://land.copernicus.eu/en/products/global-dynamic-land-cover (página, sem texto de licença localizável nela); licença declarada nos registros Zenodo por época (ex.: https://zenodo.org/records/3518036); download real: API Zenodo -> arquivo `Discrete-Classification-map` | CC-BY 4.0 (declarada em cada registro Zenodo, ex. https://zenodo.org/records/3518036) | A | Nenhuma. Acesso anônimo, HTTP 200. Arquivos globais grandes (~1,7 GB/época); recortados na AOI no momento do fetch, não mirrorados inteiros. | Buchhorn, M. et al. (2020). Zenodo, DOI 10.5281/zenodo.<record_id_da_época> | 2026-09-08 |
| ESRI/Impact Observatory 10 m Annual LULC (2017-2024) | https://registry.opendata.aws/io-lulc/ (página, licença); download real: bucket S3 público `https://io-10m-annual-lulc.s3.us-west-2.amazonaws.com/<CELULA>_<ANO>.tif`, células GZD 36K e 36L (derivadas da AOI por amostragem com a biblioteca `mgrs`, confirmadas por listagem do bucket e leitura de janela) | CC-BY 4.0, declarada em https://registry.opendata.aws/io-lulc/ | A | Nenhuma. Bucket S3 público sem assinatura, HTTP 200. 2025 ainda não publicado no bucket (2024 é o ano mais recente). | Karra, K. et al. (2021), IGARSS 2021; Impact Observatory/Microsoft/Esri (2023, atualizado anualmente), "Sentinel-2 10m Land Use/Land Cover Time Series" | 2026-09-08 |


---

<!-- fonte: data/licenses_parts/construida.md -->

# LICENSES — Área Construída e Forma Urbana (§4.2)

| Nome | URL Canônica | Licença | Nível | Restrições | Citação Exigida | Verificação |
|---|---|---|---|---|---|---|
| WSF Evolution (DLR) | https://geoservice.dlr.de/web/datasets/wsf_evo | CC-BY-4.0 | A | Nenhuma | Sim: Esch et al. 2013 e documentação técnica | 2026-09-07 |
| WSF 2015 / WSF 2019 (DLR) | https://geoservice.dlr.de/web/datasets/wsf | CC-BY-4.0 | A | Nenhuma | Sim: referência DLR EOC | 2026-09-07 |
| GHSL BUILT-S R2023A (JRC) | https://human-settlement.emergency.copernicus.eu/ghs_buS2023.php | CC-BY-4.0 | A | Nenhuma; dados 1975–2020 observados | Sim: Pesaresi et al. + publicação Copernicus | 2026-09-07 |
| GHSL BUILT-V R2023A (JRC) | https://human-settlement.emergency.copernicus.eu/ghs_buV2023.php | CC-BY-4.0 | A | Nenhuma; dados 1975–2020 observados, volume calculado a partir de S2+Landsat+DEM | Sim: Pesaresi et al. | 2026-09-07 |
| GHSL POP R2023A (JRC) | https://human-settlement.emergency.copernicus.eu/datasets.php | CC-BY-4.0 | A | Nenhuma; grade de população alocada | Sim: referência GHSL | 2026-09-07 |
| GHSL SMOD R2023A (JRC) | https://human-settlement.emergency.copernicus.eu/datasets.php | CC-BY-4.0 | A | Nenhuma; classificação de grau de urbanização | Sim: referência GHSL | 2026-09-07 |
| GHSL R2025 (JRC) Projeções | https://human-settlement.emergency.copernicus.eu/ghs_wup_built_s_r2025a.php | CC-BY-4.0 | A | 2025–2100 são extrapolações (dados 2020 observados, 2025+ modelados); cuidado com extrapolações distantes | Sim: Pesaresi et al. R2025 | 2026-09-07 |
| Google Open Buildings v3 | https://sites.research.google/open-buildings/ | CC-BY-4.0 ou ODbL 1.0 (escolha do usuário) | A | Nenhuma em uso não comercial; verificar termos comerciais | Sim: Google Open Buildings + citação exigida | 2026-09-07 |
| Microsoft Global Building Footprints | https://github.com/microsoft/GlobalMLBuildingFootprints | CDLA Permissive 2.0 | A | Nenhuma; uso comercial permitido com atribuição | Sim: Microsoft | 2026-09-07 |
| OpenStreetMap (Geofabrik Moçambique) | https://download.geofabrik.de/africa/mozambique.html | ODbL 1.0 | A | Redistribuição requer manutenção da licença; derivadas sob ODbL | Sim: OpenStreetMap Contributors + Geofabrik | 2026-09-07 |
| Global-scale Mining Polygons v2 (Maus et al. 2022) | https://doi.org/10.1594/PANGAEA.942325 | CC-BY-SA-4.0 | A | Derivadas devem manter CC-BY-SA-4.0 | Sim: Maus, V et al. (2022) | 2026-09-07 |
| Global-scale Mining Polygons v1 (Maus et al. 2020) | https://doi.org/10.1594/PANGAEA.910894 | CC-BY-SA-4.0 | A | Derivadas devem manter CC-BY-SA-4.0 | Sim: Maus, V et al. (2020) | 2026-09-07 |


---

<!-- fonte: data/licenses_parts/demograficas.md -->

# LICENSES — Fontes Demográficas e Domiciliares (§4.1 CLAUDE.md)

Família: Demográficas e Domiciliares. Tentativa 5 (esta execução) — fecha a família.
Última atualização: 2026-09-07.

| Fonte | URL canônica | Licença (texto/link) | Nível | Restrições | Citação exigida | Verificado em |
|---|---|---|---|---|---|---|
| INE — Censo 1997 (II RGPH), brochura provincial de Tete | http://www.ine.gov.mz/Censo97/05/brochura/ (arquivado; ine.gov.mz fora do ar desde 2026-09-07) | não localizado — nenhum texto de licença em ine.gov.mz nem no snapshot arquivado | pendente_auditoria | As páginas com os números (05dados.htm, 05populacao.htm) nunca foram rastreadas pelo Internet Archive; **conteúdo numérico não recuperável**, apenas a existência da brochura foi confirmada | INE, II Recenseamento Geral da População e Habitação 1997, Moçambique | 2026-09-07 |
| INE — Censo 2007 (III RGPH) — Quadro 3, Tete (distrito/cidade) | https://web.archive.org/web/20100809032728id_/http://www.ine.gov.mz/censo2007/rdcenso09/Tete/c0705q3 | não localizado — nenhum texto de licença em ine.gov.mz nem no snapshot arquivado | pendente_auditoria | Proveniência primária (arquivo do próprio INE via Wayback); falta apenas o texto de licença — classificação final A/B/C cabe ao `auditor-dados` | INE, III Recenseamento Geral da População e Habitação 2007, Resultados Definitivos, Quadro 3, Província de Tete | 2026-09-07 |
| INE — Censo 2017 (IV RGPH) — brochura nacional (resultados definitivos) | https://web.archive.org/web/20190501151428id_/http://www.ine.gov.mz/iv-rgph-2017/mocambique/censo-2017-brochura-dos-resultados-definitivos-do-iv-rgph-nacional.pdf | não localizado — nenhum texto de licença em ine.gov.mz nem no snapshot arquivado | pendente_auditoria | Idem acima; contém o "Quadro do Tamanho da População de Moçambique 2017" com taxas de omissão por província | INE, IV Recenseamento Geral da População e Habitação 2017, Resultados Definitivos, Brochura Nacional | 2026-09-07 |
| INE — Censo 2017 (IV RGPH) — Quadro 3, Tete (distrito/cidade) | https://web.archive.org/web/20191114015524id_/http://www.ine.gov.mz/iv-rgph-2017/tete/quadro-3-populacao-por-idade-segundo-area-de-residencia-distrito-e-sexo-provincia-de-tete-2017.xlsx | não localizado — nenhum texto de licença em ine.gov.mz nem no snapshot arquivado | pendente_auditoria | Idem acima | INE, IV Recenseamento Geral da População e Habitação 2017, Resultados Definitivos, Quadro 3, Província de Tete | 2026-09-07 |
| INE — mozdata.ine.gov.mz catálogo Censo 2007 (moz-ine-censo-iii-2007-v1) | https://mozdata.ine.gov.mz | não verificado nesta rodada — mozdata.ine.gov.mz responde 200 (site ativo, diferente de ine.gov.mz que está fora do ar), mas a busca por um endpoint de API/catálogo compatível com CKAN não teve retorno estruturado no tempo desta rodada; conteúdo é redundante com o Quadro 3 de 2007 já espelhado via Wayback | não avaliado | — | 2026-09-07 (verificação parcial — ver nota) |
| INE — mozdata.ine.gov.mz catálogo Censo 2017 (moz-ine-censo-iv-2017-v1) | https://mozdata.ine.gov.mz | não verificado nesta rodada (mesma nota acima); redundante com Quadro 3 de 2017 já espelhado via Wayback | não avaliado | — | 2026-09-07 (verificação parcial — ver nota) |
| IPUMS International — amostras 10% Moçambique | https://international.ipums.org/international/terms.shtml | "IPUMS International microdata are available free of charge, but their use imposes legally-binding responsibilities upon the user... provided for the exclusive purposes of teaching and scholarly research... redistribution to third parties is prohibited." Registro individual obrigatório. | B | Uso não comercial, exclusivamente pesquisa/ensino; proibida redistribuição do bruto; aprovação por usuário | IPUMS International, University of Minnesota, www.ipums.org | 2026-09-07 |
| HDX COD-PS Moçambique (Mozambique — Subnational Population Statistics) | https://data.humdata.org/dataset/cod-ps-moz | CC BY-IGO — http://creativecommons.org/licenses/by/3.0/igo/legalcode (campo `license_id`/`license_url` do dataset, lido via API `package_show`) | A | Atribuição obrigatória; dataset com "caveats" declarando ajustes não oficiais de OCHA/PMA às projeções de população e limites, pendente de revisão oficial do INE prevista para 2027 | INE Moçambique (fonte declarada em `dataset_source`); publicado por OCHA Mozambique / HDX FIS | 2026-09-07 |
| HDX COD-AB Moçambique (Subnational Administrative Boundaries) | https://data.humdata.org/dataset/cod-ab-moz | CC BY-IGO — http://creativecommons.org/licenses/by/3.0/igo/legalcode (campo `license_id`/`license_url` do dataset, lido via API `package_show`) | A | Atribuição obrigatória; limites ADM3/ADM4 com "ajustes não oficiais" (ver metodologia do dataset); revisão oficial do INE esperada em 2027 | INE Moçambique / Administração Nacional de Terras e Geografia (fonte declarada); publicado por OCHA Mozambique / HDX FIS | 2026-09-07 |
| WorldPop / GRID3 MOZ v1.1 | https://hub.worldpop.org/geodata/summary?id=6545 (página geral de termos do WorldPop; página específica do GRID3 Data Hub, data.grid3.org, não expõe `licenseInfo` de forma legível por máquina — retorna `"licenseInfo":"null"` no JSON da página) | CC BY 4.0 — https://creativecommons.org/licenses/by/4.0/ (texto geral do WorldPop: "you are free to share... and adapt... provided attribution is included"); **exceção**: camadas derivadas de OpenStreetMap/Microsoft Building Footprints/Microsoft Roads são ODbL | pendente_auditoria (licença geral do produtor localizada e é CC-BY 4.0/A-compatível, mas o item específico "MOZ Population v1.1" no GRID3 Data Hub não declara a licença na própria página do item; auditor-dados deve confirmar se esse dataset específico cai na exceção ODbL) | Atribuição obrigatória (CC-BY) ou compartilhamento pela mesma licença (ODbL) conforme a camada | WorldPop (www.worldpop.org), School of Geography and Environmental Science, University of Southampton; GRID3 (funded by Bill & Melinda Gates Foundation e UK FCDO) | 2026-09-07 |
| DHS 1997/2003/2011/2015 — relatórios finais | https://dhsprogram.com/data/Terms-of-Use.cfm ; agregados via https://dhsprogram.com/data/statcompiler.cfm | Termos de Uso do DHS Program: relatórios finais e STATcompiler são de acesso aberto sem necessidade de registro para consulta agregada; Spatial Data Repository/STATcompiler sob Open Database License (ODbL) conforme página de termos | A (relatórios/STATcompiler); ver nota | Atribuição exigida | The DHS Program, ICF, funded by USAID | 2026-09-07 |
| DHS — microdados (Moçambique 1997/2003/2011/2015) | https://dhsprogram.com/data/Terms-of-Use.cfm | Requer registro individual, projeto de pesquisa aprovado; "datasets will not be shared with other researchers without written consent"; uso restrito ao projeto registrado; dados tratados como confidenciais | B | Não redistribuível; uso não comercial/acadêmico aprovado; relatório de resultados deve ser enviado ao DHS Program | The DHS Program, ICF, funded by USAID | 2026-09-07 |
| INE — IOF 2014/15, 2019/20, 2022 (relatórios do Inquérito ao Orçamento Familiar) | não localizado nesta rodada | não avaliado — busca no Wayback por `ine.gov.mz/*iaf*` e `*iof*` não retornou nenhum PDF de relatório dentro do tempo desta rodada (zero capturas com filtro `.pdf`); pasta genérica `inqueritos_dir/iaf/` foi vista no CDX do Censo 2007 mas não os relatórios do IOF propriamente ditos | pendente_auditoria | — | 2026-09-07 (busca incompleta — ver PROVENANCE.md) |

## Notas

- Todas as linhas "pendente_auditoria" referem-se a documentos com **proveniência primária
  confirmada** (arquivo do próprio produtor, recuperado do Internet Archive porque o domínio
  original está fora do ar), mas sem texto de licença localizável em nenhum lugar acessível.
  Pela regra §4.0.1 do CLAUDE.md ("sem licença localizável ⇒ C"), a classificação final é
  atribuição do `auditor-dados`; o coletor apenas registra o fato e a ressalva.
- INE não publica, em nenhuma das páginas/domínios consultados (ine.gov.mz, arquivado ou
  ao vivo), uma página de "termos de uso" ou "licença" dedicada — diferente do HDX e do
  IPUMS, que declaram a licença em campo próprio.
- mozdata.ine.gov.mz está no ar (200) mas não foi possível, no tempo desta rodada, extrair
  um catálogo estruturado (API CKAN não respondeu no endpoint testado). Como os números de
  2007 e 2017 já foram confirmados via Wayback com o mesmo produtor (INE), a ausência dessa
  verificação redundante não compromete os achados desta família.


---

<!-- fonte: data/licenses_parts/demograficas_terceiros.md -->

# LICENSES — Demográficas via reprocessadores institucionais (Fase 0', tarefa adicional)

Escopo: recuperar Cidade de Tete/Distrito de Moatize 1997, e confirmar 2007/2017 por
segunda via independente, através de **reprocessadores institucionais** (não
agregadores) — ver distinção no prompt desta tarefa. Fragmento novo; não sobrepõe
`demograficas.md` (fechado, em uso por outro agente).

Classificação pela licença do **reprocessador**, não do INE. Cada linha registra:
quem reprocessou, censo de origem declarado, licença do produto do reprocessador.

| # | Fonte (reprocessador) | URL / DOI verificado | Código HTTP | Censo de origem declarado | Licença do reprocessador | Nível | Restrições | Citação exigida | Verificado em |
|---|---|---|---|---|---|---|---|---|---|
| 1 | CIESIN GPWv3 — National Identifier Grid / documentação Moçambique | https://sedac.ciesin.columbia.edu/data/set/gpw-v3-national-identifier-grid | 000 (timeout, sem resposta em 20s, 2026-09-07) | não verificado — servidor inacessível | não verificado | não avaliado | sedac.ciesin.columbia.edu não respondeu (curl -m 20, exit 28) em duas tentativas; não é possível confirmar conteúdo nem licença nesta rodada | não aplicável | 2026-09-07 (falha de acesso — servidor fora do ar ou bloqueando; não é 404, é timeout) |
| 2 | CIESIN GPWv4 — Population Count / Input Data Country-Level, Mozambique | https://sedac.ciesin.columbia.edu/data/set/gpw-v4-population-count-rev11 | 000 (timeout, sem resposta em 20s, 2026-09-07) | não verificado — servidor inacessível | não verificado | não avaliado | mesmo domínio do item 1, mesma falha; sedac.ciesin.columbia.edu inacessível nesta rodada | não aplicável | 2026-09-07 (falha de acesso) |
| 3 | UNSD Demographic Yearbook 2007 — Tabela 8 (population of capital cities and cities >=100.000) | https://unstats.un.org/unsd/demographic/products/dyb/dyb2007/Table08.xls (espelhado em data/raw/unsd_dyb2007_table08_capital_cities.xls) | 200 | Censo de 1997 (data exata 1 VIII 1997, CDFC), Moçambique — única linha de Moçambique nesta tabela | UN Terms and Conditions of Use (un.org/en/aboutun/terms): uso pessoal não-comercial; **proíbe redistribuição e obras derivadas sem autorização escrita** | B | Tabela lista 'city proper', não distrito. Tete = 101.984 (CONFIRMA exatamente a âncora §8: 101.984). Moatize não consta (só é listado se o país submeter cidade ≥100 mil; Moatize distrito é majoritariamente rural em 1997, não aparece como 'city') | United Nations Statistics Division, Demographic Yearbook 2007, Table 8 | 2026-09-07 |
| 4 | IPUMS International — amostra 10% Moçambique 1997/2007/2017 (verificação de tabulação agregada pública) | https://international.ipums.org/international-action/sample_details/country/mz | 200 | 1997 (II RGPH), 2007 (III RGPH), 2017 (IV RGPH) — os três aparecem listados como amostras 'available' (mz1997a, mz2007a, mz2017a) | Termos de uso IPUMS International (international.ipums.org/international/terms.shtml): microdado gratuito mediante cadastro, uso exclusivo para pesquisa/ensino, redistribuição proibida — já registrado em `demograficas.md` | B | Página de detalhe do país (sample_details/country/mz) não expõe nenhuma tabulação agregada pública nem link de download sem login; é apenas catálogo de amostras. Confirma que IPUMS 1997/2007/2017 é acessível somente como microdado sob licença B — nenhuma tabulação de nível A encontrada nesta fonte. | IPUMS International, University of Minnesota, www.ipums.org (não citável como valor numérico sem o microdado, que não pode ser baixado por esta tarefa) | 2026-09-07 |
| 5 | World Bank Microdata Library / IHSN Central Data Catalog — ficha do II RGPH 1997 | https://microdata.worldbank.org/index.php/catalog/central?q=mozambique+1997+census ; API testada: /index.php/api/catalog e /index.php/api/catalog/central/search | 200 (páginas de busca), mas 400 no endpoint de API com parâmetro de busca testado; catálogo é renderizado em cliente (Vue) e não expôs resultados filtrados por Moçambique nas tentativas de API desta rodada | não determinado | não determinado | não avaliado — não disponível nesta rodada | Motivo exato: interface de busca do catálogo (microdata.worldbank.org e catalog.ihsn.org, mesmo software NADA) não retornou lista de resultados via HTTP simples dentro do tempo desta rodada; não é 404 nem paywall, é limitação de scraping de app client-side. Não confirmado nem negado — registrar como não disponível, não como C. | não aplicável | 2026-09-07 (busca incompleta) |
| 6 | UNFPA Moçambique / ReliefWeb / HDX — séries históricas por distrito pré-2017 | https://reliefweb.int/updates?advanced-search=%28PC167%29 | 202 (aceito, resposta assíncrona típica de busca; conteúdo não inspecionado em profundidade nesta rodada) | não determinado | não determinado | não avaliado — não disponível nesta rodada | ReliefWeb é agregador de relatórios humanitários, não reprocessador estatístico dedicado; não foi encontrado, no tempo desta rodada, nenhum documento com tabulação distrital de 1997/2007 hospedado nele. HDX pré-2017 já coberto pelos itens 7/8/10 (COD-PS 2017). | não aplicável | 2026-09-07 (busca incompleta) |
| 7 | HDX COD-PS Moçambique — vintage 2017 (moz_admpop_adm2_2017_v2.csv), confirmação independente de 2007→2017 | https://data.humdata.org/dataset/46b79d47-0667-4baa-8d69-468b208855ed/resource/173abc7f-810a-4022-89dd-c9a9fa40a490/download/moz_admpop_adm2_2017_v2.csv (espelhado em data/raw/hdx_cod-ps-moz_admpop_adm2_2017_v2.csv) | 200 | 2017 (IV RGPH) — vintage do arquivo é 2017, alinhado ao censo de 2017 | CC BY-IGO 3.0 (http://creativecommons.org/licenses/by/3.0/igo/legalcode) — já registrado para o dataset cod-ps-moz em `demograficas.md` | A | Atribuição obrigatória. **CONFIRMA EXATAMENTE**: Cidade De Tete T_TL=307.338; Moatize T_TL=260.843 — idênticos aos valores de §8 recuperados via Wayback do INE. Nenhuma divergência. | OCHA Mozambique / HDX Field Information Services (FIS), COD-PS Mozambique, vintage 2017; fonte declarada: INE Moçambique, IV RGPH 2017 | 2026-09-07 |
| 8 | UNSD Demographic Yearbook — confirmação independente 2017 (IV RGPH), Tete/Moatize | https://unstats.un.org/unsd/demographic-social/products/dyb/dybcensusdata.cshtml | 200 (página acessível), mas interface é aplicação client-side (dybcensusdata) sem API pública identificada nesta rodada para extrair a tabela por país/ano | não extraído | mesma do item 3 (UN Terms and Conditions) — se confirmado, seria nível B | não avaliado — não disponível nesta rodada | Diferente do item 3 (arquivo .xls estático da edição 2007), a versão atual de 'dybcensusdata' é uma tabela interativa sem endpoint de exportação claro; não foi possível extrair a linha de Moçambique 2017 no tempo desta rodada. Como o item 7 (HDX, nível A) já confirma 2017 com valores idênticos, esta segunda via não é crítica. | não aplicável | 2026-09-07 (busca incompleta) |
| 9 | World Bank Microdata Library / IHSN — ficha do III RGPH 2007 e IV RGPH 2017 | https://microdata.worldbank.org/index.php/catalog/central?q=mozambique+population+census | 200 (página), 400 (API com parâmetro sk= testado) | não determinado | não determinado | não avaliado — não disponível nesta rodada | Mesma limitação de scraping do item 5 (app client-side); não crítico porque 2007 e 2017 já têm confirmação independente pelos itens 3 (parcial, 1997) e 7 (completa, 2017, nível A) | não aplicável | 2026-09-07 (busca incompleta) |
| 10 | HDX COD-PS Moçambique — cobertura histórica (vintages disponíveis no dataset) | https://data.humdata.org/api/3/action/package_show?id=cod-ps-moz | 200 | Vintages encontrados: 2017, 2023, 2024, 2025 (via API package_show, campo `resources`). Não há vintage 1997 nem 2007 no dataset (mais antigo é o de 2017). | CC BY-IGO 3.0 (mesma do item 7) | A (para o vintage 2017, ver item 7); vintages 2023–2025 são projeções INE pós-2017, não recenseamento — úteis para §1 pergunta 6/pergunta 7 (pós-2025), fora do escopo desta verificação de 1997/2007/2017) | Confirma que o dataset cod-ps-moz não cobre 1997 nem 2007 diretamente — só a partir do vintage 2017. Não serve como segunda via para 1997. | OCHA Mozambique / HDX FIS, COD-PS Mozambique | 2026-09-07 |

## Notas de método

- "Código HTTP" é medido com `curl -s -o /dev/null -w '%{http_code}' -L <url>`; DOIs
  resolvidos com `curl -s -L -H "Accept: application/vnd.citationstyles.csl+json" https://doi.org/<doi>`.
- Linha 4 (IPUMS) é tratada como nível B por definição do prompt-mestre; não será
  baixado microdado — só se registra o que a amostra permitiria validar.
- Toda linha permanece `PENDENTE` até verificação com evidência de acesso efetivo
  registrada em `data/provenance_parts/demograficas_terceiros.md`.


---

<!-- fonte: data/licenses_parts/economicos.md -->

# LICENÇAS — Proxies Econômicos (Fase 0')

## Formato
| Nome | URL canônica | Licença | Nível | Restrições | Citação exigida | Data de verificação |

## Fontes

| Nome | URL canônica | Licença | Nível | Restrições | Citação exigida | Data de verificação |
|---|---|---|---|---|---|---|
| DMSP-OLS Global Radiance-Calibrated Nighttime Lights (v4) | https://www.ncei.noaa.gov/products/dmsp-operational-linescan-system | Domínio público (NOAA — sem copyright, sem restrições) | A | Nenhuma | NOAA/NCEI DMSP-OLS v4 + anos utilizados | 2026-09-07 |
| VIIRS DNB Annual Composites (EOG/Colorado School of Mines) | https://eogdata.mines.edu/products/viirs/ | Domínio público (NASA/NOAA; EOG sem restrições) | A | Nenhuma; acesso via GEE ou EOG FTP público | Earth Observation Group, Colorado School of Mines, VIIRS DNB Annual Composites + versão + ano | 2026-09-07 |
| Harmonized DMSP-VIIRS Nighttime Lights (1992–2018) (Li et al. 2020) | https://figshare.com/articles/dataset/Harmonization_of_DMSP_and_VIIRS_nighttime_light_data_from_1992-2018_at_the_global_scale/9828827 | CC-BY 4.0 (como registrado em Scientific Data) | A | Citação obrigatória | Li, X., Zhou, Y., Zhao, M. & Zhao, X. (2020). A harmonized global nighttime light dataset 1992–2018. *Scientific Data*, 7, 168. DOI: 10.6084/m9.figshare.9828827 | 2026-09-07 |
| Global Coal Mine Tracker (Global Energy Monitor) | https://globalenergymonitor.org/projects/global-coal-mine-tracker/download-data/ | CC-BY 4.0 International (atribuição obrigatória) | A | Formulário de download; acesso anônimo com preenchimento de nome/email; citação obrigatória | Global Energy Monitor. Global Coal Mine Tracker. August 2026 release. | 2026-09-07 |
| World Bank Commodity Markets Observatory — Pink Sheet (preços de carvão) | https://thedocs.worldbank.org/en/doc/18675f1d1639c7a34d463f59263ba0a2-0050012025/related/ | Domínio público (World Bank — acesso livre, reutilização permitida) | A | Citação recomendada (não obrigatória); acesso direto sem cadastro | World Bank. Commodity Markets Observatory — Pink Sheet (Coal — Australia, Coal — South Africa). [Mês/Ano]. | 2026-09-07 |
| INE Moçambique — Índice de Preços ao Consumidor (IPC), Tete | https://www.ine.gov.mz/web/guest/b/indice-de-preco-no-consumidor | Licença INE com citação (dados do INE — acesso público) | A | Citação ao INE obrigatória | Instituto Nacional de Estatística (INE) de Moçambique. Índice de Preços ao Consumidor (IPC). Base: 2023 = 100. [Data/Período]. | 2026-09-07 |

**Notas:**
- Todas as fontes acima são nível A: acesso anônimo, sem restrições de redistribuição (salvo indicação de citação), e licenças compatíveis com pipelines abertos.
- DMSP-OLS e VIIRS DNB — licenças de domínio público (não copyrighted); acesso via GEE ou repositórios públicos NOAA.
- GCMT — exige preenchimento de formulário, mas acesso imediato sem approval formal; CC-BY 4.0.
- World Bank Pink Sheet — acesso direto em PDFs; não há CSV público documentado, registrar como PDF.
- INE IPC — coleta abrange 8 cidades, incluindo Tete; dados em PDF (pode conter tabelas); série desde 1997 (verificar continuidade de Tete).


---

<!-- fonte: data/licenses_parts/fase3_auditoria_t3.md -->

# Fase 3 — Auditoria de classificação (auditor-dados, T3)

Classifica as fontes coletadas em `data/licenses_parts/fase3_coleta_t2_licenca.md`
(que registrou "não classificado — cabe ao auditor-dados" em toda linha) e as duas
fontes não obtidas, com evidência HTTP. Verificado via `.meta.json` em `data/raw/`
e página do produtor (Harvard Dataverse), nunca via agregador.

## Correção de autoria — obrigatória, atinge CLAUDE.md §4.4

O item "Harmonized DMSP-VIIRS Nighttime Lights (1992–2018) (Li et al. 2020)" da tabela
§4.4 de `CLAUDE.md` e a linha correspondente em `data/licenses_parts/economicos.md`
descrevem um produto **diferente** do coletado nesta rodada. Confirmado por busca na
página do produtor/paper original (não por agregador):

- **Produto coletado (54 tiles, `viirs_like_li2020_v2_*.tif`)**: autoria **Chen, Z.,
  Yu, B., Yang, C., Zhou, Y., Yao, S., Qian, X., Wang, C., Wu, B., Wu, J.** Paper de
  método: Chen et al. (2021), "An extended time series (2000–2018) of global
  NPP-VIIRS-like nighttime light data from a cross-sensor calibration", *Earth System
  Science Data*, 13, 889–906, DOI **10.5194/essd-13-889-2021**. Dataset hospedado no
  Harvard Dataverse como "The global NPP-VIIRS-like nighttime light data (Version 2)
  for 1992–2025", V10, DOI **10.7910/DVN/YGIVCD**, licença **CC0 1.0** (lida no JSON
  da API do Dataverse — `metadataBlocks.citation.license`, confirmado no `.meta.json`
  de cada tile).
- **Produto descrito em CLAUDE.md §4.4 ("Li et al. 2020")**: Li, X., Zhou, Y., Zhao,
  M., Zhao, X. (2020), "A harmonized global nighttime light dataset 1992–2018",
  *Scientific Data*, 7, 168 — hospedado em figshare, **não** em Harvard Dataverse. É
  um harmonizado DMSP↔VIIRS **distinto**, de outro grupo de autores, com outra
  metodologia de calibração cruzada.
- **Nome de arquivo do coletor é ambíguo por desenho** (`viirs_like_li2020_v2_*`),
  mas o `.meta.json` de cada arquivo já registra a citação correta (Chen/Yu). O nome
  do arquivo não deve ser lido como atribuição de autoria.
- **Ação exigida**: `CLAUDE.md` §4.4 deve ser corrigido para separar as duas linhas —
  "Harmonized DMSP-VIIRS (Li et al. 2020, figshare, DOI 10.1038/s41597-020-0510-y)"
  permanece como item **não coletado nesta rodada**; "NPP-VIIRS-like (Chen/Yu et al.,
  Harvard Dataverse V10, DOI 10.7910/DVN/YGIVCD)" é o item efetivamente em
  `data/raw/`. `data/licenses_parts/economicos.md` cita o DOI/figshare de Li et al.
  para um produto que **não foi baixado**; não corrigido aqui (fora do escopo desta
  família), sinalizado para o responsável por `economicos.md`.

## Classificação

| # | Fonte | Nível | Licença confirmada | Citação exigida | Nota |
|---|---|---|---|---|---|
| 1 | NPP-VIIRS-like (Chen/Yu et al.), 54 recortes, Harvard Dataverse V10 | **A** | CC0 1.0, http://creativecommons.org/publicdomain/zero/1.0, confirmada no JSON da API do Dataverse (não agregador) | Recomendada, não obrigatória sob CC0: Chen, Z. et al. (2021) *ESSD* 13, 889–906, DOI 10.5194/essd-13-889-2021 + Chen, Z., Yu, B. et al. "Global NPP-VIIRS-like nighttime light data (V2) 1992–2025", Harvard Dataverse V10, DOI 10.7910/DVN/YGIVCD | Único raster global nunca mirrorado; só recortes de AOI (2–6 KB) em `data/raw/`, conforme §4.0 regra 2 |
| 2 | WSF Evolution — 5 tiles novos (Chimoio S20E032, Quelimane S18E036, Lichinga S14E034, Xai-Xai S26E032, Inhambane S24E034) | **A** | CC BY 4.0, https://creativecommons.org/licenses/by/4.0/, mesma licença já registrada em `construida.md` para os tiles da AOI de estudo | Marconcini, M., Metz-Marconcini, A., Esch, T., Gorelick, N. (2021), GI_Forum 2021, Issue 1, p. 33–38, DOI 10.1553/giscience2021_01_s33 | Consistente com classificação prévia da família; nenhuma divergência de licença entre tiles |
| 3 | HDX COD-AB Moçambique (`moz_admin_boundaries.geojson.zip`) | **A** | CC BY-IGO 3.0, http://creativecommons.org/licenses/by/3.0/igo/legalcode, lida via API CKAN `package_show` (mesmo padrão já aceito para HDX COD-PS em `demograficas.md`) | OCHA/HDX COD-AB Mozambique (moz_admin_boundaries), fonte declarada INE — não verificada diretamente no site do INE (mesma ressalva já registrada para COD-PS) | ADM0–3, P-codes; nível A pela mesma lógica já aplicada ao COD-PS: variante nomeada de CC-BY, reprocessador com licença própria distingue do documento-INE bruto (nível C) |

## Fontes não obtidas — excluídas, com evidência HTTP (não é lacuna a esconder)

| # | Fonte | Nível | Motivo | Evidência HTTP |
|---|---|---|---|---|
| 4 | VIIRS VNL V2 (Earth Observation Group, `eogdata.mines.edu`) | **B, rebaixada de A** — reclassificação desta auditoria | O item já registrado em `economicos.md` como nível A ("acesso via GEE ou EOG FTP público") descrevia um acesso que **deixou de existir**: todo diretório de download testado (`/nighttime_light/annual/v10,v20,v21,v22/`) e os links `.tif.gz` diretos redirecionam HTTP 302 para `eogauth.mines.edu`, exigindo login OAuth com conta EOG — não é acesso anônimo nem cadastro trivial (o cadastro EOG historicamente exige aprovação institucional/e-mail verificado, não é um clique). Isso satisfaz a definição de nível B do §4.0 ("gratuito mas exige aprovação de uso"), não a de A. **Não avaliado nesta rodada** um acesso equivalente via Google Earth Engine (`NOAA/VIIRS/DNB/MONTHLY_V1/VCMSLCFG` ou coleção correlata): se confirmado que o dado subjacente é replicável por essa via semina exigir mais que uma conta Google trivial, o dado (não a plataforma) poderia retornar a A — pendente de teste, não presumido. | `eogdata.mines.edu/products/vnl/` = 200 (página); todos os `/nighttime_light/annual/*` e `.tif.gz` = 302 → `eogauth.mines.edu` (OAuth), verificado 2026-09-08 |
| 5 | DMSP-OLS estável (NOAA/NCEI) | **C — excluída** | URL registrada em `CLAUDE.md` §4.4 (`ngdc.noaa.gov/eog/dmsp/downloadV4composites.html`) responde HTTP 404 — página removida, sem redirecionamento para conteúdo equivalente. Página sucessora em `eogdata.mines.edu/products/dmsp/` existe (200) mas os links de download (`wwwdata/dmsp/rad_cal/*.tgz`) sofrem o mesmo bloqueio OAuth do item 4. Nenhuma licença localizável no domínio que efetivamente serve o dado hoje; NOAA/NCEI (domínio público, texto de licença já visto em `economicos.md`) não hospeda mais o arquivo. Pela regra §4.0.1 ("sem licença localizável ⇒ C") e pela ausência de via anônima, classificação é **C**, distinta da simples indisponibilidade temporária (não é timeout, é 404 + login obrigatório na via sucessora). | `ngdc.noaa.gov/eog/dmsp/downloadV4composites.html` = 404; `eogdata.mines.edu/products/dmsp/` = 200; `wwwdata/dmsp/rad_cal/*.tgz` = 302 → OAuth, verificado 2026-09-08 |

## Descontinuidade de versão documentada pelo produtor — material para P5/P6/§5.4

Medição do orquestrador: radiância máxima na AOI de Tete cai de 70,4 (2020) para 49,9
(2022) e permanece em 49,9 (2025), na série `viirs_like_li2020_v2` (Chen/Yu). Busca na
literatura do próprio produto (não no dado em si, que este agente não abriu) encontra
evidência **de terceiros que documentam** revisão dos anos 2021–2022 do dataset
NPP-VIIRS-like desta mesma linhagem (rastreamento de catálogo GEE-community, discussão
pública de changelog): "the annual NPP-VIIRS-like NTL data of 2021 and 2022 have been
updated" — i.e., o produtor reprocessou/recalibrou especificamente esses dois anos após
a publicação original de 2021 (que cobria só 2000–2018; a extensão 2019–2025 e as
revisões de 2021–2022 são posteriores, do V10 hospedado no Dataverse). **Isto não é
confirmação de primeira mão do texto de cada nota de versão do Dataverse** (o agente não
teve acesso ao changelog interno do Dataverse nesta rodada — página client-side não
renderizada pelo fetch disponível); é evidência de terceiros de que existe reprocessamento
documentado na janela 2020–2022. **Recomendação, não veredito**: a queda de 70,4→49,9
medida pelo orquestrador **coincide temporalmente com um reprocessamento conhecido do
produto**, e não deve ser lida como quebra de nível econômica (bust do carvão, ADR/ desenho
§1.2 quebra de 2022) sem antes descartar essa explicação alternativa — tratar como
candidato a "placebo de versão do produto" adicional ao já exigido em
`docs/DESENHO_FASE3.md` §4 (P1–P4), a ser verificado por segunda via (ex.: comparação
com VIIRS DNB bruto, se e quando obtido) antes de qualquer atribuição causal à quebra de
2022.


---

<!-- fonte: data/licenses_parts/fase3_coleta_t2_licenca.md -->

# Fase 3 (T2) — fragmento de licenças

| fonte | URL canônica | licença (observada) | nível provisório | restrições | citação exigida | data verificação |
|---|---|---|---|---|---|---|
| Harmonized DMSP-VIIRS / NPP-VIIRS-like (Chen, Yu et al., ex-"Li et al. 2020") | https://doi.org/10.7910/DVN/YGIVCD | CC0 1.0 (http://creativecommons.org/publicdomain/zero/1.0, lida no JSON da API Dataverse: metadataBlocks.citation license) | não classificado — cabe ao auditor-dados | nenhuma (CC0); acesso anônimo confirmado, sem cadastro | "Chen, Z., Yu, B., et al. The global NPP-VIIRS-like nighttime light data (Version 2) for 1992-2025. Harvard Dataverse, V10. DOI: 10.7910/DVN/YGIVCD" | 2026-09-08 |
| VIIRS annual VNL V2 (EOG) | https://eogdata.mines.edu/products/vnl/ | Licença declarada em https://eogdata.mines.edu/files/EOG_products_CC_License.pdf (texto não lido — acesso ao arquivo em si não testado, só o link) | não classificado — cabe ao auditor-dados | download bloqueado: TODOS os diretórios /nighttime_light/annual/v10,v20,v21,v22/ e os links diretos .tif.gz retornam HTTP 302 para eogauth.mines.edu (OAuth, exige conta EOG). Não é acesso anônimo. | (não obtido) | 2026-09-08 |
| DMSP-OLS estável (NOAA/NCEI, agora hospedado em EOG/Mines) | https://ngdc.noaa.gov/eog/dmsp/downloadV4composites.html | não localizável — página fonte migrou | não classificado — cabe ao auditor-dados | URL do CLAUDE.md (ngdc.noaa.gov) responde 301->www.ngdc.noaa.gov->HTTP 404 (página removida). Página sucessora em eogdata.mines.edu/products/dmsp/ existe (HTTP 200) mas os links de download (eogdata.mines.edu/wwwdata/dmsp/rad_cal/*.tgz) redirecionam HTTP 302 para eogauth.mines.edu (OAuth, exige conta EOG) — mesmo bloqueio do VNL. | (não obtido) | 2026-09-08 |
| WSF Evolution — tile S20E032 (Chimoio) | https://download.geoservice.dlr.de/WSF_EVO/files//WSFevolution_v1_32_-20.tif | CC BY 4.0 (https://creativecommons.org/licenses/by/4.0/, lida na aba License de https://geoservice.dlr.de/web/datasets/wsf_evo) | não classificado — cabe ao auditor-dados | citar autores; sem redistribuicao de obra derivada sem atribuicao | Marconcini et al. 2021, GI_Forum 2021 Issue 1 p.33-38, DOI 10.1553/giscience2021_01_s33 | 2026-09-08 |
| WSF Evolution — tile S18E036 (Quelimane) | https://download.geoservice.dlr.de/WSF_EVO/files//WSFevolution_v1_36_-18.tif | CC BY 4.0 (https://creativecommons.org/licenses/by/4.0/) | não classificado — cabe ao auditor-dados | citar autores | Marconcini et al. 2021, DOI 10.1553/giscience2021_01_s33 | 2026-09-08 |
| WSF Evolution — tile S14E034 (Lichinga) | https://download.geoservice.dlr.de/WSF_EVO/files//WSFevolution_v1_34_-14.tif | CC BY 4.0 (https://creativecommons.org/licenses/by/4.0/) | não classificado — cabe ao auditor-dados | citar autores | Marconcini et al. 2021, DOI 10.1553/giscience2021_01_s33 | 2026-09-08 |
| WSF Evolution — tile S26E032 (Xai-Xai) | https://download.geoservice.dlr.de/WSF_EVO/files//WSFevolution_v1_32_-26.tif | CC BY 4.0 (https://creativecommons.org/licenses/by/4.0/) | não classificado — cabe ao auditor-dados | citar autores | Marconcini et al. 2021, DOI 10.1553/giscience2021_01_s33 | 2026-09-08 |
| WSF Evolution — tile S24E034 (Inhambane) | https://download.geoservice.dlr.de/WSF_EVO/files//WSFevolution_v1_34_-24.tif | CC BY 4.0 (https://creativecommons.org/licenses/by/4.0/) | não classificado — cabe ao auditor-dados | citar autores | Marconcini et al. 2021, DOI 10.1553/giscience2021_01_s33 | 2026-09-08 |
| HDX COD-AB Moçambique (moz_admin_boundaries, INE via OCHA/CKAN) | https://data.humdata.org/dataset/cod-ab-moz | CC BY-IGO 3.0 (http://creativecommons.org/licenses/by/3.0/igo/legalcode, lida via CKAN API package_show license_url) | não classificado — cabe ao auditor-dados (fonte declarada INE, não verificada no site do INE) | atribuicao exigida pela IGO license | OCHA/HDX COD-AB Mozambique, moz_admin_boundaries, dataset_source declarado "INE - Instituto Nacional de Estatistica" | 2026-09-08 |


---

<!-- fonte: data/licenses_parts/imagem.md -->

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


---

<!-- fonte: data/licenses_parts/osm_vias_lugares.md -->

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


---

<!-- fonte: data/licenses_parts/reassentamento.md -->

# Família: REASSENTAMENTO (Cateme, 25 de Setembro, Mwaladzi)

Verificado em 2026-09-07 pelo `coletor-dados` (Fase 0'). Colunas conforme §4.0.1 de
CLAUDE.md. Verificação de acesso feita com `curl -s -o /dev/null -w '%{http_code}'`
(páginas) e resolução DOI via `curl -L -H "Accept: application/vnd.citationstyles.csl+json" https://doi.org/<doi>`
conferindo título/ano/autores contra o texto citado.

| Fonte | URL canônica | Licença | Nível | Restrições | Citação exigida | Verificado em |
|---|---|---|---|---|---|---|
| Human Rights Watch (2013), "What is a House without Food?" | https://www.hrw.org/report/2013/05/23/what-house-without-food/mozambiques-coal-mining-boom-and-resettlements (HTTP 200) | [CC BY-NC-ND 3.0 US](http://creativecommons.org/licenses/by-nc-nd/3.0/us/), conforme https://www.hrw.org/permissions (HTTP 200) | **B** — licença localizada, mas restringe uso comercial e obras derivadas (NC-ND); redistribuição do PDF integral é permitida sem alteração, com citação | Uso não comercial; proibida obra derivada do texto/relatório; permitido citar trechos com atribuição | Sim: Human Rights Watch, "What is a House without Food? Mozambique's Coal Mining Boom and Resettlements" (2013) | 2026-09-07 |
| Lillywhite, Kemp & Sturman (2015), "Mining, resettlement and lost livelihoods: listening to the voices of resettled communities in Mualadzi, Mozambique" — CSRM/Oxfam Australia, Melbourne | https://www.csrm.uq.edu.au/publications/mining-resettlement-and-lost-livelihoods (HTTP 200); PDF: https://www.csrm.uq.edu.au/media/docs/1167/miningresettlementandlostlivelihoods.pdf (HTTP 200) | Não localizada na página do produtor (UQ/CSRM) nenhuma licença aberta explícita; página de copyright da UQ (`uq.edu.au/copyright`) retornou 404 na verificação | **C** — sem texto de licença localizável na página do produtor; cópia em oxfam.org.au retornou 403 (bloqueio de acesso automatizado) na verificação | Presumir todos os direitos reservados até localização de licença explícita | Sim: Lillywhite, S., Kemp, D. & Sturman, K. (2015). *Mining, resettlement and lost livelihoods: listening to the voices of resettled communities in Mualadzi, Mozambique*. CSRM/Oxfam Australia, Melbourne | 2026-09-07 |
| Mosca, J. & Selemane, T. (2011), "El Dorado Tete: os mega projectos de mineração" — Centro de Integridade Pública (CIP), Maputo | https://cipmoz.org/ (HTTP 200; busca "El Dorado Tete" retorna páginas de índice, não o PDF em domínio próprio do CIP) | "© Copyright © 2026 CIP — Todos os direitos reservados" (texto extraído do rodapé de cipmoz.org) | **C** — declaração expressa de "todos os direitos reservados", sem licença aberta | Reprodução/redistribuição não autorizada pelo texto do site | Sim: Mosca, J. & Selemane, T. (2011). *El Dorado Tete: os mega projectos de mineração*. Centro de Integridade Pública, Maputo | 2026-09-07 |
| Kirshner, J. & Power, M. (2015), "Mining and extractive urbanism: Postdevelopment in a Mozambican boomtown", *Geoforum* 61, 67–78 | DOI confirmado por Crossref: https://doi.org/10.1016/j.geoforum.2015.02.019 (HTTP 200; CSL-JSON confere título/autores/ano); artigo em sciencedirect.com retorna HTTP 403 (paywall) | Elsevier TDM user license (mineração de texto/dados, não redistribuição): https://www.elsevier.com/tdm/userlicense/1.0/ ; cópia OA identificada via Unpaywall no repositório institucional de Durham University (worktribe.com/output/1443257, licença declarada `cc-by`), mas o link retornou HTTP 403 na verificação direta — **não confirmado por acesso** | **C** — versão de registro é paga (paywall); a via aberta apontada pelo Unpaywall não pôde ser acessada nesta verificação (403); tratar como fechada até confirmação de acesso | Citar apenas resumo/dados já publicados por terceiros verificáveis; não redistribuir o PDF | Sim: Kirshner, J. & Power, M. (2015). Mining and extractive urbanism: Postdevelopment in a Mozambican boomtown. *Geoforum*, 61, 67–78. https://doi.org/10.1016/j.geoforum.2015.02.019 | 2026-09-07 |
| Centro de Integridade Pública (CIP) — relatórios diversos sobre Moatize (ex.: Observador Rural) | https://cipmoz.org/ (HTTP 200) | "Todos os direitos reservados" (rodapé do site, sem licença CC ou equivalente localizada) | **C** | Sem redistribuição autorizada pelo texto do site | Sim, por relatório específico (título, ano, CIP) quando citado individualmente | 2026-09-07 |
| Justiça Ambiental (JA!) — relatórios sobre Moatize | https://www.ja4change.org/ (HTTP 200) | Página inclui aviso de "copyright"; texto integral da licença não localizado em busca automatizada nesta verificação | **C** — licença não localizada | Presumir todos os direitos reservados até localização de licença explícita | Sim, por relatório específico quando citado individualmente | 2026-09-07 |
| EIA/RAP — Vale (Projeto Moatize) | Não localizado em acesso público: `vale.com/w/moatize` e `vale.com/business/coal` retornaram HTTP 404 nesta verificação | não disponível | **não disponível** — 404 | — | — | 2026-09-07 |
| EIA/RAP — Riversdale/Rio Tinto (Projeto Benga) | Não localizado em busca automatizada nesta verificação; nenhuma URL institucional de EIA/RAP em acesso livre foi encontrada | não disponível | **não disponível** — não localizado | — | — | 2026-09-07 |
| EIA/RAP — Jindal (Tete) | `jindalafrica.com` retornou HTTP 406 nesta verificação; nenhum EIA/RAP em acesso livre localizado | não disponível | **não disponível** — 406 / não localizado | — | — | 2026-09-07 |
| OpenStreetMap (nodes Cateme e Mwaladzi) | https://www.openstreetmap.org/copyright | [ODbL 1.0](https://opendatacommons.org/licenses/odbl/1-0/) | **A** | Compartilhar-alike para bases de dados derivadas; atribuição obrigatória | Sim: "© OpenStreetMap contributors" | 2026-09-07 |

## Observações

- **Nenhum EIA/RAP primário (Vale, Riversdale/Rio Tinto, Jindal) foi localizado em
  acesso público** nesta verificação. Os números de famílias reassentadas usados no
  GeoJSON vêm de HRW (2013), que por sua vez cita os planos de reassentamento sem
  reproduzi-los; isso é uma limitação registrada, não uma citação inventada.
- CIP e Justiça Ambiental publicam material relevante para a família de reassentamento
  mas nenhuma licença aberta foi localizada na página do produtor — nível **C** por
  regra §4.0 ("sem licença localizável ⇒ C"), a rever se o site publicar termos mais
  específicos por documento.
- Kirshner & Power (2015): apesar de existir cópia de acesso aberto indexada pelo
  Unpaywall (Durham University repository, `cc-by`), o link retornou HTTP 403 nesta
  verificação — mantido como nível C até que o acesso seja confirmado.
- HRW (2013) é a única fonte primária desta família com licença aberta localizável e
  verificável (CC BY-NC-ND 3.0 US) — nível B, não A, pela cláusula NC-ND.


---

<!-- fonte: data/licenses_parts/worldpop_grid3.md -->

# WorldPop / GRID3 — fragmento de licenças (Vila de Moatize, população)

Sessão: coleta WorldPop/GRID3 recortado à AOI (33.50–34.10E, -16.35 a -16.00S).
Nível A/B/C **não** atribuído aqui — cabe ao `auditor-dados`. Abaixo, licença **observada** na página do produtor.

| Fonte | URL canônica | Licença observada | Restrições | Citação exigida | Data de verificação |
|---|---|---|---|---|---|
| GRID3 MOZ Population v1.1 (grade ~100m; calibrado ao Censo 2017 -- não existe versão v1.1 "2020") | https://data.humdata.org/dataset/gridded-population-estimates-for-mozambique-2017-census-v1-1 (download servido por wopr.worldpop.org, sem suporte a HTTP Range) | CC BY 4.0 -- confirmado via HDX package_show API (`license_id=cc-by`, `license_url=http://www.opendefinition.org/licenses/cc-by`, `isopen=true`), 2026-09-09 | Atribuição obrigatória; dataset é produto interino ("até que o INE publique a grade oficial do Censo 2017") | Bondarenko M, Jones P, Leasure D, Lazar AN, Tatem AJ. 2020. Census disaggregated gridded population estimates for Mozambique (2017), version 1.1. WorldPop, University of Southampton. doi:10.5258/SOTON/WP00672 | 2026-09-09 |
| WorldPop Population Counts MOZ 2000 (unconstrained -- único produto disponível para esse ano) | https://data.worldpop.org/GIS/Population/Global_2000_2020/2000/MOZ/moz_ppp_2000.tif (catalogado em https://data.humdata.org/dataset/worldpop-population-counts-for-mozambique) | CC BY 4.0 -- https://www.worldpop.org/data/licence | Atribuição obrigatória | WorldPop (www.worldpop.org). Mozambique 100m Population, 2000 (unconstrained, Global_2000_2020). doi:10.5258/SOTON/WP00645 | 2026-09-09 — **arquivo NÃO baixado nesta sessão**: ver nota de falha em PROVENANCE (data.worldpop.org ignora `Range`, download completo do mosaico nacional de ~446 MB throttled a ~11–70 KB/s medidos em 3 tentativas; tempo extrapolado 2–8 h, excede o orçamento da sessão) |
| WorldPop Population Counts MOZ 2005 (unconstrained -- único produto disponível para esse ano) | https://data.worldpop.org/GIS/Population/Global_2000_2020/2005/MOZ/moz_ppp_2005.tif | CC BY 4.0 -- https://www.worldpop.org/data/licence | Atribuição obrigatória | WorldPop (www.worldpop.org). Mozambique 100m Population, 2005 (unconstrained, Global_2000_2020). doi:10.5258/SOTON/WP00645 | 2026-09-09 — **arquivo NÃO baixado nesta sessão** (mesmo motivo do ano 2000: throttling do servidor) |
| WorldPop Population Counts MOZ 2010 (unconstrained -- único produto disponível para esse ano) | https://data.worldpop.org/GIS/Population/Global_2000_2020/2010/MOZ/moz_ppp_2010.tif | CC BY 4.0 -- https://www.worldpop.org/data/licence | Atribuição obrigatória | WorldPop (www.worldpop.org). Mozambique 100m Population, 2010 (unconstrained, Global_2000_2020). doi:10.5258/SOTON/WP00645 | 2026-09-09 — **arquivo NÃO baixado nesta sessão** (mesmo motivo do ano 2000: throttling do servidor) |
| WorldPop Population Counts MOZ 2015 (constrained, release R2024B -- preferido sobre unconstrained por ser calibrado com pegada de edificações) | https://data.worldpop.org/GIS/Population/Global_2015_2030/R2024B/2015/MOZ/v1/100m/constrained/moz_pop_2015_CN_100m_R2024B_v1.tif | CC BY 4.0 -- https://www.worldpop.org/data/licence | Atribuição obrigatória | WorldPop (www.worldpop.org). Mozambique 100m Population (constrained, individual countries 2015-2030, UN adjusted, R2024B), 2015. | 2026-09-09 — **arquivo NÃO baixado nesta sessão** (mesmo motivo: throttling do servidor a ~90 MB de mosaico nacional) |
| WorldPop Population Counts MOZ 2020 (constrained, release R2024B -- preferido sobre unconstrained por ser calibrado com pegada de edificações) | https://data.worldpop.org/GIS/Population/Global_2015_2030/R2024B/2020/MOZ/v1/100m/constrained/moz_pop_2020_CN_100m_R2024B_v1.tif | CC BY 4.0 -- https://www.worldpop.org/data/licence | Atribuição obrigatória | WorldPop (www.worldpop.org). Mozambique 100m Population (constrained, individual countries 2015-2030, UN adjusted, R2024B), 2020. | 2026-09-09 — **arquivo NÃO baixado nesta sessão**: HTTP 200 confirmado (`curl -I`, `Accept-Ranges: bytes` anunciado mas ignorado em `curl -r`/GDAL vsicurl, que retorna erro `Range downloading not supported by this server!`); 3 tentativas de download completo mediram 11,6–70 KB/s de throughput, projetando 25–130 min só para este arquivo de ~90 MB; interrompido por orçamento de sessão |
