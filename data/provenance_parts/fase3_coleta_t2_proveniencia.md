# Fase 3 (T2) — fragmento de proveniência

Cada linha: arquivo, URL, data de acesso, licença, citação, resolução/nível geográfico, anos cobertos.
Status inicial PENDENTE; atualizado incrementalmente conforme cada download é tentado.

| arquivo | URL | data acesso | licença | resolução/nível | anos | status |
|---|---|---|---|---|---|---|
| viirs_like_li2020_v2_{ano}_tete_aoi.tif — 9 anos (2000,2005,2010,2011,2015,2016,2020,2022,2025) | https://dataverse.harvard.edu/api/access/datafile/{id} (ids: 13295261,13295251,13295266,13295270,13295271,13295278,13295279,14085057,14085060) | 2026-09-08 | CC0 1.0 | ~500 m (0,004492°); recorte AOI Tete/Moatize (config/study.yaml bbox) | ano-âncora único por arquivo, cobertura da série-fonte 1992-2025 | OK — 9 arquivos, 100% sucesso |
| viirs_like_li2020_v2_{ano}_{cidade}.tif — 5 cidades de controle (chimoio, quelimane, lichinga, xaixai, inhambane) × 9 anos = 45 arquivos | mesma fonte acima | 2026-09-08 | CC0 1.0 | ~500 m; recorte de buffer 0,15° (~15 km) em torno do centro geográfico de cada capital (coordenadas Nominatim fornecidas pelo orquestrador) | idem | OK — 45 arquivos, 100% sucesso |

Método: cada ano é um GeoTIFF global (~10 GB descomprimido) dentro de um .zip comprimido
(82–186 MB) hospedado no Harvard Dataverse. O .zip foi baixado para scratch temporário,
lido com GDAL /vsizip/ (janela de leitura, sem descompactar o global inteiro), recortado
para a AOI de Tete e para um buffer de 0,15° em torno de cada uma das 5 capitais de
controle, e o .zip global foi descartado após o recorte — **o raster global nunca foi
mirrorado em data/raw/**, só os recortes (2–6 KB cada). 54/54 recortes obtidos, 0 falhas.
Citação: Chen, Z., Yu, B., et al. "The global NPP-VIIRS-like nighttime light data
(Version 2) for 1992-2025." Harvard Dataverse V10. DOI: 10.7910/DVN/YGIVCD.

| VIIRS annual VNL V2 (EOG, eogdata.mines.edu) | https://eogdata.mines.edu/products/vnl/ | 2026-09-08 | não obtido | não obtido — todos os diretórios de download (/nighttime_light/annual/v10,v20,v21,v22/) e os links diretos .tif.gz retornam HTTP 302 para eogauth.mines.edu (login OAuth obrigatório via conta EOG; não é acesso anônimo) | 2012-presente (não coberto) | NÃO DISPONÍVEL — requer cadastro/login (EOG account), HTTP 302→OAuth em todas as rotas testadas |
| DMSP-OLS estável (NOAA/NCEI) | https://ngdc.noaa.gov/eog/dmsp/downloadV4composites.html | 2026-09-08 | não obtido | página do CLAUDE.md (ngdc.noaa.gov/eog/dmsp/downloadV4composites.html) responde HTTP 404 (removida; www.ngdc.noaa.gov não tem mais seção /eog/); página sucessora eogdata.mines.edu/products/dmsp/ existe (HTTP 200) mas os links de download (wwwdata/dmsp/rad_cal/*.tgz) redirecionam HTTP 302 para eogauth.mines.edu (mesmo login obrigatório do VNL) | 1992-2013 (não coberto) | NÃO DISPONÍVEL — página original 404; sucessora exige login EOG |
| wsf_evolution_S20E032.tif (Chimoio) | https://download.geoservice.dlr.de/WSF_EVO/files//WSFevolution_v1_32_-20.tif | 2026-09-08 | CC BY 4.0 | 30 m; tile 2x2 graus, canto SW confirmado no grid.geojson do produtor (id 32_-20) | 1985-2015 (pixel=ano de 1a deteccao; 0=sem dado) | OK — 1.657.913 bytes, MD5 verificado contra grid.geojson do produtor |
| wsf_evolution_S18E036.tif (Quelimane) | https://download.geoservice.dlr.de/WSF_EVO/files//WSFevolution_v1_36_-18.tif | 2026-09-08 | CC BY 4.0 | 30 m; tile id 36_-18 | 1985-2015 | OK — 1.635.622 bytes, MD5 verificado |
| wsf_evolution_S14E034.tif (Lichinga) | https://download.geoservice.dlr.de/WSF_EVO/files//WSFevolution_v1_34_-14.tif | 2026-09-08 | CC BY 4.0 | 30 m; tile id 34_-14 | 1985-2015 | OK — 1.936.190 bytes, MD5 verificado |
| wsf_evolution_S26E032.tif (Xai-Xai) | https://download.geoservice.dlr.de/WSF_EVO/files//WSFevolution_v1_32_-26.tif | 2026-09-08 | CC BY 4.0 | 30 m; tile id 32_-26 | 1985-2015 | OK — 2.629.500 bytes, MD5 verificado (1a tentativa: broken pipe, retentada com sucesso) |
| wsf_evolution_S24E034.tif (Inhambane) | https://download.geoservice.dlr.de/WSF_EVO/files//WSFevolution_v1_34_-24.tif | 2026-09-08 | CC BY 4.0 | 30 m; tile id 34_-24 | 1985-2015 | OK — 1.626.342 bytes, MD5 verificado |
| moz_admin_boundaries.geojson.zip (HDX COD-AB, ADM0-4 + capitais) | https://data.humdata.org/dataset/5e8d83a5-1210-49be-b7d9-cf286dbc15df/resource/f1d97232-4cb5-4083-b3cc-d192aa9bdcfe/download/moz_admin_boundaries.geojson.zip | 2026-09-08 | CC BY-IGO 3.0 (declarada via CKAN API) | polígono admin, ADM0/1/2/3/4 + pontos de capital; fonte declarada INE via OCHA | vigente (valid_on 2025-01-01, version v02) | OK — 61.310.853 bytes |

P-codes ADM2 lidos diretamente do arquivo moz_admin2.geojson extraído (não do agregador, não asseridos):
- Cidade de Tete: MZ0501 (adm1 MZ05, Tete)
- Moatize: MZ0510 (adm1 MZ05, Tete)
- Cidade de Chimoio: MZ0601 (adm1 MZ06, Manica)
- Quelimane: MZ0401 (adm1 MZ04, Zambézia)
- Cidade de Lichinga: MZ0101 (adm1 MZ01, Niassa)
- Xai-Xai: MZ0901 (adm1 MZ09, Gaza)
- Cidade de Inhambane: MZ0801 (adm1 MZ08, Inhambane)

Nota: estes são P-codes do esquema COD-AB (geometria). Conforme config/unidades.yaml,
o esquema COD-PS (população/HDX) usa códigos INCOMPATÍVEIS com os mesmos dígitos apontando
para entidades diferentes — cruzamento correto é por NOME normalizado + província, nunca
por P-code entre os dois esquemas.
