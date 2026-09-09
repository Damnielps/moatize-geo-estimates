# Proveniência — Validação de Cultivo (Fase 2b)

Um bloco por arquivo efetivamente baixado (§ regra de PROVENANCE.md). Fragmento novo —
não edita `agricultura.md` da Fase 0'.

## GLAD Global Cropland

- Arquivos: `data/raw/glad_cropland_{2003,2007,2011,2015,2019}_aoi.tif`
- URL: https://gladxfer.umd.edu/Potapov/Global_Crop/Data/Global_cropland_SE_<ANO>.tif
- Acesso: 2026-09-08
- Licença: CC-BY 4.0 (https://glad.umd.edu/dataset/croplands)
- Citação: Potapov, P. et al. (2021). "Global maps of cropland extent and change show
  accelerated cropland expansion in the twenty-first century." Nature Food 3, 19-28.
  DOI 10.1038/s43016-021-00429-z
- Resolução: 30 m; recorte da AOI (config/study.yaml) + margem de 0.02 grau, via leitura
  em janela GDAL /vsicurl/ (o mosaico regional "SE" global NÃO foi mirrorado inteiro)
- Nível geográfico: recorte da AOI Tete-Moatize
- Anos cobertos: compostos quinquenais 2003, 2007, 2011, 2015, 2019 (observado)

## ESA WorldCover

- Arquivos: `data/raw/esa_worldcover_2020_s18e033_aoi.tif`, `data/raw/esa_worldcover_2021_s18e033_aoi.tif`
- URL: https://esa-worldcover.s3.eu-central-1.amazonaws.com/v100/2020/map/ESA_WorldCover_10m_2020_v100_S18E033_Map.tif
  e https://esa-worldcover.s3.eu-central-1.amazonaws.com/v200/2021/map/ESA_WorldCover_10m_2021_v200_S18E033_Map.tif
- Acesso: 2026-09-08
- Licença: CC-BY 4.0 (https://esa-worldcover.org/en/data-access)
- Citação: Zanaga, D. et al. (2022). "ESA WorldCover 10 m 2020 v100." DOI
  10.5281/zenodo.5571936; "ESA WorldCover 10 m 2021 v200." DOI 10.5281/zenodo.7254221
- Resolução: 10 m; tile S18E033 derivado da AOI (config/study.yaml) via grade de 3°;
  recorte da AOI + margem de 0.02 grau, via leitura em janela GDAL /vsicurl/ (o tile
  3x3 grau inteiro, ~180 MB, NÃO foi mirrorado)
- Nível geográfico: recorte da AOI Tete-Moatize
- Anos cobertos: 2020, 2021 (observado)

## Copernicus Global Land Cover CGLS-LC100

- Arquivos: `data/raw/cgls_lc100_{2015,2016,2017,2018,2019}_aoi.tif`
- URL: resolvida via API Zenodo por época (registros 3939038, 3518026, 3518036,
  3518038, 3939050), arquivo `*_Discrete-Classification-map_EPSG-4326.tif`
- Acesso: 2026-09-08
- Licença: CC-BY 4.0 (declarada em cada registro Zenodo, ex. https://zenodo.org/records/3518036)
- Citação: Buchhorn, M. et al. (2020). "Copernicus Global Land Service: Land Cover
  100m: Collection 3: epoch <ANO>: Globe." Zenodo. DOI 10.5281/zenodo.<record_id>
- Resolução: 100 m; recorte da AOI (config/study.yaml) + margem de 0.02 grau, via
  leitura em janela GDAL /vsicurl/ (o arquivo global "Discrete-Classification-map",
  ~1,7 GB por época, NÃO foi mirrorado inteiro)
- Nível geográfico: recorte da AOI Tete-Moatize
- Anos cobertos: 2015, 2016, 2017, 2018, 2019 (observado)

## ESRI/Impact Observatory 10 m Annual LULC

- Arquivos: `data/raw/esri_io_lulc_<ANO>_{36k,36l}_aoi.tif`, ANO em 2017-2024
- URL: https://io-10m-annual-lulc.s3.us-west-2.amazonaws.com/<CELULA>_<ANO>.tif
- Acesso: 2026-09-08
- Licença: CC-BY 4.0 (https://registry.opendata.aws/io-lulc/)
- Citação: Karra, K., Kontgis, C., Statman-Weil, Z., Mazzariello, J.C., Mathis, M.,
  Brumby, S.P. (2021). "Global land use/land cover with Sentinel-2 and deep
  learning." IGARSS 2021. Impact Observatory/Microsoft/Esri (2023, atualizado
  anualmente). "Sentinel-2 10m Land Use/Land Cover Time Series."
- Resolução: 10 m; células MGRS GZD (3 caracteres) 36K e 36L, DERIVADAS da AOI por
  amostragem de grade com a biblioteca `mgrs` (a AOI cruza a fronteira de banda de
  latitude K/L em -16.00°) e confirmadas por listagem do bucket S3 e leitura de
  janela; recorte da AOI + margem de 2000 m em EPSG:32736 (CRS nativo dos tiles),
  via leitura em janela GDAL /vsicurl/ (o tile inteiro da célula, ~200-250 MB, NÃO
  foi mirrorado)
- Nível geográfico: recorte da AOI Tete-Moatize
- Anos cobertos: 2017-2024 (observado). 2025 não publicado no bucket em 2026-09-08.
