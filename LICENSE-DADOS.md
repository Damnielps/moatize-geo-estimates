# Licença dos dados e do conteúdo

Este arquivo cobre os **dados agregados publicados** (`data/processed/**`), as **figuras e tabelas** (`paper/figuras/`, `paper/tabelas/`), o **artigo** (`paper/`), a **documentação** (`docs/`) e o **conteúdo textual do painel**. O código-fonte do projeto tem uma licença separada — ver `LICENSE` (MIT).

## Licença: CC BY 4.0

Salvo as exceções abaixo, esse conteúdo está sob a licença **[Creative Commons Atribuição 4.0 Internacional (CC BY 4.0)](https://creativecommons.org/licenses/by/4.0/deed.pt-br)**: qualquer pessoa pode copiar, redistribuir, adaptar e usar para qualquer finalidade, inclusive comercial, **desde que dê a atribuição apropriada**, indique se houve alterações e forneça um link para a licença.

### Como atribuir

> Daniel Pessini Sobreira. *Urbanização induzida pela mineração em Tete e Moatize (Moçambique), 1997–2025* — dados, painel e artigo. Fontes primárias: Instituto Nacional de Estatística (INE Moçambique) Censos 2007 e 2017; USGS Landsat; Copernicus Sentinel-2; JRC GHSL; DLR WSF Evolution; GLAD Global Cropland; ESA WorldCover; OpenStreetMap; Humanitarian Data Exchange (HDX) COD-AB e COD-PS; Chen, Z., Yu, B. et al. (2021) NPP-VIIRS-like nighttime lights; Maus, V. et al. (2020/2022) Global-scale Mining Polygons; HydroSHEDS; World Bank Commodity Markets Observatory.

Para citação formal, ver `CITATION.cff` e a seção "Como citar" do `README.md`.

## Exceções: conteúdo derivado de terceiros com licença própria

| Conteúdo | Fonte | Licença que prevalece | DOI/URL de verificação |
|---|---|---|---|
| OpenStreetMap em camadas `osm_*` do app (vias, pontos de interesse) | © Contribuidores do OpenStreetMap | **ODbL 1.0** (dados derivados de base de dados abertos; atribuição obrigatória e compartilhamento pela mesma licença) | https://www.openstreetmap.org/copyright |
| Camada `industrial` (mineração) — derivada de "Global-scale Mining Polygons v2" | Maus, V., et al. (2022). PANGAEA | **CC-BY-SA-4.0** (compartilhamento obrigatório pela mesma licença) | DOI 10.1594/PANGAEA.942325 |
| GHSL BUILT-S/BUILT-V/POP/SMOD R2023A; GHSL R2025 projeções | JRC Copernicus, Comissão Europeia | CC BY 4.0 | https://human-settlement.emergency.copernicus.eu/ |
| WSF Evolution (30 m, anual 1985–2015) e WSF 2015/2019 (10 m) | DLR German Aerospace Center | CC BY 4.0 | https://geoservice.dlr.de/web/datasets/wsf_evo |
| GLAD Global Cropland (Potapov et al. 2021) | Global Land Analysis & Discovery (GLAD), University of Maryland | CC BY 4.0 | DOI 10.1038/s43016-021-00429-z |
| ESA WorldCover 10 m (v100 2020 / v200 2021) | European Space Agency | CC BY 4.0 | DOI 10.5281/zenodo.5571936 (2020) / 10.5281/zenodo.7254221 (2021) |
| Copernicus Global Land Service CGLS-LC100 (100 m, 2015–2019) | Copernicus, JRC | CC BY 4.0 (por época Zenodo) | DOI 10.5281/zenodo.3939050 (agregador) |
| Google Open Buildings v3 (polígonos de edificações) | Google Research | CC BY 4.0 ou ODbL 1.0 (escolha do usuário) | https://sites.research.google/open-buildings/ |
| Microsoft Global Building Footprints (polígonos de edificações) | Microsoft | CDLA Permissive 2.0 | https://github.com/microsoft/GlobalMLBuildingFootprints |
| HydroRIVERS v1.0 (África) — rede hidrográfica | HydroSHEDS, McGill University | Licença própria HydroSHEDS (uso livre com atribuição obrigatória) | https://www.hydrosheds.org/products/hydrorivers |
| Copernicus DEM GLO-30 (modelo digital de elevação) | European Space Agency / Airbus | Licença Copernicus (uso livre e gratuito; atribuição obrigatória) | DOI 10.5270/ESA-c5d3d65 |
| Imagens Landsat (série completa) | USGS / NASA | Domínio público | https://www.usgs.gov/faqs/what-are-terms-use-landsat-imagery |
| Imagens Sentinel-2 (série completa) | Copernicus / ESA | Uso livre com atribuição "Contém dados modificados Copernicus Sentinel" | https://www.esa.int/Applications/Observing_the_Earth/Copernicus/Sentinel-2/Access |
| HDX COD-AB Moçambique (limites administrativos) | OCHA/HDX, fonte INE/ANTA | CC BY-IGO 3.0 | https://data.humdata.org/dataset/cod-ab-moz |
| HDX COD-PS Moçambique (população por unidade administrativa) | OCHA/HDX, fonte INE | CC BY-IGO 3.0 | https://data.humdata.org/dataset/cod-ps-moz |
| NPP-VIIRS-like nighttime lights anual (Chen, Z., Yu, B. et al. 2021) | Harvard Dataverse | CC0 1.0 (domínio público) | DOI 10.7910/DVN/YGIVCD |
| INE — Censos 2007 e 2017 (tabulações agregadas) | Instituto Nacional de Estatística, Moçambique | Dados públicos com citação obrigatória | https://mozdata.ine.gov.mz |
| World Bank Commodity Markets Observatory — preços do carvão (CMO Historical Data Annual) | World Bank | CC BY 4.0 — texto em https://www.worldbank.org/ext/en/legal/terms-conditions/datasets. Atribuição exigida: "The World Bank: Commodity Markets Observatory — CMO Historical Data Annual: Coal, Australian and Coal, South African (USD/mt, nominal). World Bank." | https://www.worldbank.org/ext/en/legal/terms-conditions/datasets |
| Marcos da linha do tempo do ciclo do carvão (datas de `config/marcos.yaml`) | Vale S.A., Rio Tinto plc, Human Rights Watch, SEC EDGAR, INE — documentos institucionais e regulatórios diversos (ver `data/licenses_parts/marcos.md`) | Não redistribuídos — o app exibe apenas a **data** e a **referência bibliográfica** de cada marco, nunca o documento-fonte; vários desses documentos são de nível C/secundário quanto à licença (sem texto de licença localizável), por isso não entram sob CC BY 4.0 desta licença | ver `data/licenses_parts/marcos.md` para a lista de URLs por marco |
| INE Moçambique — Folheto Provincial Tete 2021 (indicadores de PIB e inflação, contexto) | Instituto Nacional de Estatística, Moçambique | Nível C — licença não localizada no PDF nem no domínio `ine.gov.mz` (erro de certificado TLS impediu verificar a página de termos); documento usado apenas como **contexto** em `data/processed/economia/contas_regionais_tete.csv`, não redistribuído nesta licença | https://ine.gov.mz/documents/20119/176900/Folheto%20Provincial_Tete_2021.pdf (ver `data/licenses_parts/economia_ine_contas.md`) |

## Dados de nível B e C não redistribuídos

Esta licença cobre **exclusivamente dados agregados publicados**. Conforme a política de §4.0 de `CLAUDE.md`:

- **Dados de nível B** (IPUMS International microdados, Planet NICFI, DHS Demographic and Health Surveys microdados) — não estão neste repositório. O pipeline consome esses dados apenas quando disponíveis; os resultados agregados são mantidos aqui sob CC BY 4.0, mas o bruto nível B nunca é redistribuído ou versionado. Scripts de obtenção e hashes esperados constam em `pipeline/00_fetch/`; quem desejar reproduzir usando as mesmas fontes deve solicitar acesso direto aos provedores (IPUMS, Planet, DHS Program).

- **Dados de nível C** (sem licença localizável, sob NDA, paywall) — excluídos do pipeline. Uma amostra de tentativas de localizar documentação primária com sucesso parcial está em `data/LICENSES.md` e `PROVENANCE.md`; o repositório publica apenas afirmações sobre dados de nível A e marcações explícitas de "não disponível" para o resto.

A licença CC BY 4.0 acima não outorga direitos sobre dados de origem nível B ou C — apenas sobre os resultados agregados e estatisticamente controlados que este projeto publica a partir de fontes de nível A verificáveis.

## Auditorias de licença

Cada fonte de nível A foi verificada quanto a:
- ✓ Licença: texto localizado na página do produtor ou em documento institucional
- ✓ Acesso: URL canônica testa 200 (HTTP HEAD/GET), sem autenticação pessoal
- ✓ Redistribuição: licença permite uso, adaptação e obras derivadas (CC0, CC-BY, CC-BY-SA, ODbL, domínio público, ou licenças institucionais que declaram uso livre)
- ✓ Citação: formato e DOI/URL verificados via Crossref, resolver de DOI ou repositório do produtor

Ver `data/LICENSES.md` para o registro linha a linha de cada fonte, data de verificação e restrições.
