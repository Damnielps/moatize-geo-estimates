# PROVENANCE — Área Construída e Forma Urbana (§4.2)

## Rasters de Assentamento (Sentinel-based e Landsat-based)

### WSF Evolution — 30 m, anual, 1985–2015
- **URL**: https://download.geoservice.dlr.de/WSF_EVO/
- **Data de Acesso Esperada**: (será baixado via pipeline/00_fetch/fetch_wsf_evolution.py)
- **Licença**: CC-BY-4.0
- **Citação**: Esch, T., Heldens, W., Hirner, A., et al. (2022). World Settlement Footprint (WSF) Evolution—Mapping human presence on Earth with Landsat, Sentinel-1 and Sentinel-2 time series data. *Remote Sensing of Environment*, 287, 113453. https://doi.org/10.1016/j.rse.2022.113453
- **Resolução**: 30 m
- **Nível Geográfico**: Global; recorte pela AOI (33.50°E–34.10°E / 16.35°S–16.00°S) (AOI confirmada pelo ADR 0001; o bbox provisório terminava em 33.95°E)
- **Anos Cobertos**: 1985–2015 (anual)
- **Observações**: Máscara binária de assentamento; dados para Moçambique disponíveis em tiles 2×2°. Redownload anual para verificação de updates.

### WSF 2015 / WSF 2019 — 10 m
- **URL**: https://download.geoservice.dlr.de/WSF/
- **Data de Acesso Esperada**: (será baixado via pipeline)
- **Licença**: CC-BY-4.0
- **Citação**: DLR Earth Observation Center, WSF 2015 / WSF 2019
- **Resolução**: 10 m
- **Nível Geográfico**: Global; recorte pela AOI
- **Anos Cobertos**: 2015 (WSF 2015), 2019 (WSF 2019)
- **Observações**: Refinamento de resolução sobre WSF Evolution; disponível apenas para esses dois anos-âncora.

### GHSL BUILT-S R2023A — 100 m e 10 m, 1975–2020
- **URL**: https://human-settlement.emergency.copernicus.eu/ghs_buS2023.php
- **Data de Acesso Esperada**: (será acessado via GEE ou STAC alternativo)
- **Licença**: CC-BY-4.0
- **Citação**: Pesaresi, M., Politis, P., Fonte, C. C., et al. (2024). GHS-BUILT-S R2023A – Global Built-up Surface derived from Sentinel-2 composite and Landsat, multitemporal (1975–2020). European Commission, Joint Research Centre (JRC). https://doi.org/10.2905/jrc-ghsl-10007
- **Resolução**: 100 m (padrão); 10 m (subproduto)
- **Nível Geográfico**: Global; recorte pela AOI
- **Anos Cobertos**: 1975–2020 (intervals de 5 anos), observados
- **Observações**: Superfície construída em m²/pixel; base para múltiplos produtos; validado contra WSF.

### GHSL BUILT-V R2023A — 100 m, 1975–2020
- **URL**: https://human-settlement.emergency.copernicus.eu/ghs_buV2023.php
- **Data de Acesso Esperada**: (será acessado via GEE ou STAC)
- **Licença**: CC-BY-4.0
- **Citação**: Pesaresi et al. (2024), GHS-BUILT-V R2023A
- **Resolução**: 100 m
- **Nível Geográfico**: Global; recorte pela AOI
- **Anos Cobertos**: 1975–2020 (5-year intervals), observados
- **Observações**: Volume construído em m³/pixel; derivado de BUILT-S + Landsat-8 DEM; proxy de altura e densidade.

### GHSL POP R2023A — 100 m, 1975–2020
- **URL**: https://human-settlement.emergency.copernicus.eu/datasets.php
- **Data de Acesso Esperada**: (será acessado via GEE ou STAC)
- **Licença**: CC-BY-4.0
- **Citação**: Pesaresi et al. (2024), GHS-POP R2023A
- **Resolução**: 100 m
- **Nível Geográfico**: Global; recorte pela AOI
- **Anos Cobertos**: 1975–2020 (5-year intervals)
- **Observações**: População alocada em grade via dasymetric mapping; utilizado para validação de densidades.

### GHSL SMOD R2023A — 100 m, 2015 + projeção 2020
- **URL**: https://human-settlement.emergency.copernicus.eu/datasets.php
- **Data de Acesso Esperada**: (será acessado via GEE ou STAC)
- **Licença**: CC-BY-4.0
- **Citação**: Pesaresi et al., GHS-SMOD R2023A
- **Resolução**: 100 m
- **Nível Geográfico**: Global; recorte pela AOI
- **Anos Cobertos**: 2015, 2020 (projetado)
- **Observações**: Grau de urbanização: rural, intermédio, urbano; utilizado para classificação de perímetro urbano.

### GHSL R2025 — Projeções 2025–2100 (CC-BY-4.0)
- **URL**: https://human-settlement.emergency.copernicus.eu/ghs_wup_built_s_r2025a.php
- **Data de Acesso Esperada**: (será acessado quando disponível em plataforma pública)
- **Licença**: CC-BY-4.0
- **Citação**: Pesaresi et al. (2025), GHS-WUP R2025 — Global Human Settlement R2025
- **Resolução**: Conforme BUILT-S (100 m)
- **Nível Geográfico**: Global; recorte pela AOI
- **Anos Cobertos**: 2025–2030 (projetados, continuidade estável de não-residencial + crescimento residencial modelado)
- **Observações**: **EXTRAPOLADOS**, não observados; usar apenas com marcação explícita de nível de confiança reduzido; base 2020 observada.

---

## Vetores de Edificações

### Google Open Buildings v3 — ~2022–2023
- **URL**: https://sites.research.google/open-buildings/
- **Acesso Alternativo**: HDX (dados por país)
- **Data de Acesso Esperada**: (será obtido via HDX ou GEE conforme disponibilidade)
- **Licença**: CC-BY-4.0 ou ODbL 1.0 (escolha do usuário)
- **Citação**: Google Open Buildings v3, 2023
- **Resolução**: Polígonos individuais de edificações; ~1.8 bilhões de detecções globais
- **Nível Geográfico**: 147 países (Africa, Asia, Américas); Moçambique coberto
- **Anos Cobertos**: ~2022–2023 (inferência para período único)
- **Observações**: Detecções por deep learning; score de confiança 0.65–1.0; disponível em CSV por tile S2 L4, GeoJSON via HDX (Moçambique), ou download via gsutil.

### Microsoft Global Building Footprints — ~2020–2022
- **URL**: https://github.com/microsoft/GlobalMLBuildingFootprints
- **Data de Acesso Esperada**: (será baixado via script idempotente)
- **Licença**: CDLA Permissive 2.0
- **Citação**: Microsoft, Global Building Footprints
- **Resolução**: Polígonos individuais de edificações; cobertura global
- **Nível Geográfico**: 225 regiões; ~30.340 tiles; Moçambique coberto
- **Anos Cobertos**: ~2020–2022 (mosaico sem data específica de inferência por pixel)
- **Observações**: Formato `.csv.gz` (conteúdo GeoJSONL); coordenadas EPSG:4326; baixar via Azure Blob Storage (https://bfppub.blob.core.windows.net/); scripts Python fornecidos no repositório.

---

## Polígonos Minerários

### Global-scale Mining Polygons v2 (Maus et al. 2022) — CC-BY-SA-4.0
- **URL**: https://doi.org/10.1594/PANGAEA.942325
- **Data de Acesso Esperada**: 2026-09-07 (verificação, download se < 50 MB)
- **Licença**: CC-BY-SA-4.0 (compartilhamento de derivadas obrigatório)
- **Citação**: Maus, V., Giljum, S., da Silva, D. M., et al. (2022). Global-scale mining polygons (Version 2) [Dataset]. PANGAEA. https://doi.org/10.1594/PANGAEA.942325
- **Resolução**: Polígonos digitalizados, 10 m (fonte: Sentinel-2 2019)
- **Nível Geográfico**: Global; 44.929 polígonos; verificar cobertura em AOI Tete/Moatize (33.50°E–34.10°E / 16.35°S–16.00°S) (AOI confirmada pelo ADR 0001; o bbox provisório terminava em 33.95°E)
- **Anos Cobertos**: 2019 (base de interpretação); atualizado em versão 2 (2022)
- **Observações**: Área total: 101.583 km²; inclui open-cuts, tailings, waste dumps, processamento, água relacionada a mineração. Acurácia de validação: 88,3%. **Requer download de PANGAEA com script idempotente**.

### Global-scale Mining Polygons v1 (Maus et al. 2020)
- **URL**: https://doi.org/10.1594/PANGAEA.910894
- **Data de Acesso Esperada**: (opcional, referência histórica)
- **Licença**: CC-BY-SA-4.0
- **Citação**: Maus, V., Giljum, S., da Silva, D. M., et al. (2020). Global-scale mining polygons (Version 1) [Dataset]. PANGAEA. https://doi.org/10.1594/PANGAEA.910894
- **Resolução**: Polígonos, ~10 m
- **Nível Geográfico**: Global; >21.000 polígonos
- **Anos Cobertos**: 2016–2019 (base de interpretação)
- **Observações**: Versão anterior; v2 é recomendada.

---

## Dados de Referência de Uso Agrícola e Cobertura

### OpenStreetMap — Moçambique (ODbL 1.0)
- **URL**: https://download.geofabrik.de/africa/mozambique.html
- **Formato**: OSM.PBF (242 MB, 2026-09-07), Shapefile ZIP (686 MB), GeoPackage ZIP
- **Data de Acesso Esperada**: (será baixado via script idempotente)
- **Licença**: ODbL 1.0 (OpenStreetMap Contributors, processado por Geofabrik GmbH)
- **Citação**: OpenStreetMap Contributors (2026), Moçambique. Disponível em https://download.geofabrik.de/africa/mozambique.html (acesso 2026-09-07).
- **Resolução**: Vetores (pontos, linhas, polígonos) com atributos de categorização
- **Nível Geográfico**: Moçambique (país inteiro); recorte pela AOI
- **Anos Cobertos**: Contínuo; data de captura conforme download (checkout 2026-05-10T20:20:31Z no download testado)
- **Observações**: Inclui edificações, vias, cultivos, mercados, água; útil para validação e contexto; requer manutenção de ODbL em redistribuição ou derivadas.

---

## Resumo de Política de Dados

- **Nível A (Aberto)**: Todas as fontes acima ✓
- **Versionamento em `data/raw/`**: WSF, GHSL, Google OB, Microsoft FB, OSM, Maus Polygons (se < 50 MB)
- **Formato**: GeoTIFF COG (rasters), GeoJSON/GeoPackage (vetores)
- **Checksums**: SHA-256 para cada arquivo
- **Metadados**: `.meta.json` com URL, data_download, size_bytes, license, level, source_page
- **Scripts de obtenção**: `pipeline/00_fetch/fetch_<fonte>.py` com idempotência e hash de verificação
