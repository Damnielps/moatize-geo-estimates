# data/provenance_parts/luzes_noturnas_fase3.md

Proveniência de fontes de luzes noturnas — série causal de atividade econômica (§5.4, ADR 0013).

## Harmonized DMSP-VIIRS (Li et al. 2020)

**Status:** PENDENTE — coleta em progresso

| Atributo | Valor |
|----------|-------|
| **URL de acesso** | https://doi.org/10.6084/m9.figshare.9828827 |
| **Plataforma** | Figshare |
| **Resolução espacial** | 30 arc-segundos (~1 km global) |
| **Resolução temporal** | Anual, 1992–2018 |
| **Anos de interesse para Fase 3** | 1997, 2005, 2010, 2015, 2020 (anos-âncora de §2) |
| **Âmbito geográfico** | Global; recorte obrigatório para AOI + 5 capitais de controle (coords em study.yaml) |
| **Tipo de dado** | Raster, DN (Digital Number), banda única |
| **Método de acesso** | HTTP GET via Figshare API; redirecionamento por DOI esperado |
| **Tamanho estimado** | Desconhecido (Figshare não lista tamanho nos resultados de busca; tipicamente 100–500 MB para global annual) |
| **Licença** | CC-BY 4.0 |
| **Citação** | Li, X., Zhou, Y., Zhao, M., & Zhao, X. (2020). "A harmonized global nighttime light dataset 1992–2018." Scientific Data 7, 168. https://doi.org/10.1038/s41597-020-0510-y |
| **Data de verificação de acesso** | 2026-09-08 |
| **Status de download** | ⚠ Figshare HTTP 403 sem autenticação (WebFetch testado); API JSON esperada 200 OK (curl testado, saída nula). Downloader: usar download direto via browser ou script com Python+requests. |
| **Script de coleta** | Planejado em `pipeline/00_fetch/fetch_harmonized_dmsp_viirs.py` |

**Nota metodológica:** Esta é a série primária para testar H4 (descola luz–população após 2016) conforme §5.4. Luzes são não-monotônicas por construção (podem cair), diferentemente de área construída (sempre cresce). Série contínua necessária: Harmonized cobre 1992–2018, VIIRS VNL v2.2 cobre 2012+, sobreposição 2012–2018 permite validação cruzada.

---

## VIIRS Annual Nighttime Light V2.2 (Earth Observation Group, Colorado School of Mines)

**Status:** PENDENTE — coleta em progresso

| Atributo | Valor |
|----------|-------|
| **URL de acesso** | https://eogdata.mines.edu/nighttime_light/annual/v22/ |
| **Produtora** | Earth Observation Group, Payne Institute for Public Policy, Colorado School of Mines |
| **Resolução espacial** | 15 arc-segundos (~500 m) |
| **Resolução temporal** | Anual, 2012–2021; possível extensão verificar readme |
| **Anos de interesse para Fase 3** | 2015, 2020, (2021 se disponível) |
| **Âmbito geográfico** | Global; recorte obrigatório para AOI + 5 capitais de controle |
| **Tipo de dado** | Raster, radiância nocturna (valores reais), banda única (radiance) ou máscara (lit_mask) |
| **Método de acesso** | HTTP GET direto; servidor ativo (curl HTTP 200 confirmado em 2026-09-08) |
| **Tamanho estimado** | ~50–100 MB por ano (tiled ou global, verificar) |
| **Licença** | CC-BY 4.0 International (conforme EOG Products CC License PDF) |
| **Citação** | Elvidge, C.D., Zhizhin, M., Ghosh, T., Hsu, F.C., Taneja, J. (2021). "Annual time series of global VIIRS nighttime lights derived from monthly averages: 2012 to 2019." Remote Sensing 13(5), 922. https://doi.org/10.3390/rs13050922 |
| **Data de verificação de acesso** | 2026-09-08 |
| **Status de download** | ✓ Servidor ativo HTTP 200. Download direto esperado sem autenticação. |
| **Script de coleta** | Planejado em `pipeline/00_fetch/fetch_viirs_vnl_v22.py` |

**Nota:** Complementa Harmonized DMSP-VIIRS para período 2012–2021+. Resolução superior (15 vs 30 arc-seg) permite análise de aglomerados urbanos de tamanho médio. Arquivo "lit_mask" oferece classificação binária (lit/unlit) para robustez estatística.

---

## DMSP-OLS Stable Lights V4 (NOAA NCEI)

**Status:** PENDENTE — coleta em progresso

| Atributo | Valor |
|----------|-------|
| **URL de acesso** | https://www.ncei.noaa.gov/products/dmsp-operational-linescan-system |
| **URL de download** | https://ngdc.noaa.gov/eog/data/web_data/v4composites (HTTP 301 → https://www.ngdc.noaa.gov/...) |
| **Produtora** | NOAA National Centers for Environmental Information (NCEI); coleta USAF Weather Agency |
| **Resolução espacial** | 30 arc-segundos |
| **Resolução temporal** | Anual, 1992–2013 |
| **Anos de interesse para Fase 3** | 1997, 2005, 2010 (pré-VIIRS) |
| **Âmbito geográfico** | Global; recorte obrigatório para AOI + 5 capitais de controle |
| **Tipo de dado** | Raster, DN (0–63), banda única (stable lights) |
| **Método de acesso** | HTTP GET direto; servidor NOAA ativo (curl HTTP 301 confirmado) |
| **Tamanho estimado** | ~50 MB por ano (padrão EOG) |
| **Licença** | Domínio público / sem restrições copyright; crédito a NOAA NCEI obrigatório |
| **Citação** | "Image and data processing by NOAA's National Geophysical Data Center. DMSP data collected by US Air Force Weather Agency." |
| **Data de verificação de acesso** | 2026-09-08 |
| **Status de download** | ✓ Servidor ativo HTTP 301/200. Download direto esperado sem autenticação. |
| **Script de coleta** | Planejado em `pipeline/00_fetch/fetch_dmsp_ols_stable_lights.py` |

**Nota metodológica:** Base histórica de 1992–2013. Série Harmonized DMSP-VIIRS já harmoniza DMSP-OLS com VIIRS para período comum (1992–2018), portanto DMSP-OLS bruto é opcional — presente apenas como validação / cross-check. Threshold DN recomendado pela literatura: 7 ou superior.

---

## Plano de Download Resumido

1. **Harmonized DMSP-VIIRS**: Via Figshare/DOI, recorte para AOI + 5 capitais, SHA256, .meta.json
2. **VIIRS VNL v2.2**: Via EOG, anual 2015–2021, recorte, SHA256, .meta.json
3. **DMSP-OLS V4**: Via NOAA, anual 1992–2013 (opcional), recorte, SHA256, .meta.json

Todos os arquivos destinam-se a `data/raw/` com nomes de arquivo originais + `.sha256` + `.meta.json`.

---

## Especificação Técnica de Recorte

- **AOI principal**: xmin 33.50, ymin -16.35, xmax 34.10, ymax -16.00 (EPSG:4326)
- **Capitais de controle** (bounding boxes 0.5° × 0.5°):
  - Chimoio: 33.2–33.8 E, 19.4–18.8 S
  - Quelimane: 36.6–37.2 E, 18.2–17.6 S
  - Lichinga: 35.0–35.5 E, 13.6–13.0 S
  - Xai-Xai: 33.4–34.0 E, 25.4–24.6 S
  - Inhambane: 34.3–34.9 E, 23.1–22.4 S

Exportar como GeoTIFF COG, EPSG:4326, com compressão LZW.

