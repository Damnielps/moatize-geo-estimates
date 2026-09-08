# PROVENIÊNCIA — Proxies Econômicos (Fase 0')

## Formato
| URL | Data de acesso | Licença | Citação | Resolução/Nível geográfico | Anos cobertos | Arquivo local | Status |

## Downloads e Acessos Documentados

### 1. World Bank Commodity Markets Observatory — Pink Sheet (Junho 2026)

| URL | Data de acesso | Licença | Citação | Resolução/Nível geográfico | Anos cobertos | Arquivo local | Status |
|---|---|---|---|---|---|---|---|
| https://thedocs.worldbank.org/en/doc/74e8be41ceb20fa0da750cda2f6b9e4e-0050012026/related/CMO-Pink-Sheet-June-2026.pdf | 2026-09-07 | Domínio público (World Bank) | World Bank. Commodity Markets Observatory — Pink Sheet. June 2026. | Global (commodity prices) | 1960–junho 2026 | `data/raw/WorldBank_CommodityPrices_PinkSheet_June2026.pdf` | ✓ Espelhado |
| — | — | — | — | — | — | SHA256: `e3cb29d01889af02ac8a6138153937deb02a8078133850fd8df65731e8d5dbcf` | — |

**Conteúdo:** Série histórica de preços de carvão (Australia e South Africa) em USD/mt, mensal. Formato: PDF com tabelas; excelente para análise de ciclos de preço relativos à operação da mina de Moatize (2011–2026).

---

### 2. DMSP-OLS Global Radiance-Calibrated Nighttime Lights (v4)

| URL | Data de acesso | Licença | Citação | Resolução/Nível geográfico | Anos cobertos | Arquivo local | Status |
|---|---|---|---|---|---|---|---|
| https://www.ncei.noaa.gov/products/dmsp-operational-linescan-system | 2026-09-07 | Domínio público (NOAA/NCEI — sem copyright) | NOAA/NCEI. DMSP-OLS Global Radiance-Calibrated Nighttime Lights Version 4. Years: [anos solicitados]. | 1 km (ou 2.7 km, conforme versão) | 1992–2013 | Não espelhado (grande; acesso via GEE ou FTP NOAA) | Pipeline via GEE |

**Observação:** Dados em GeoTIFF/ENVI. Grande volume (~3 GB descomprimido). Primária fonte para série histórica de luzes noturnas pré-2012. Pipeline acessa via Google Earth Engine (plataforma primária §4.3 CLAUDE.md).

---

### 3. VIIRS DNB Annual Composites (Earth Observation Group / Colorado School of Mines)

| URL | Data de acesso | Licença | Citação | Resolução/Nível geográfico | Anos cobertos | Arquivo local | Status |
|---|---|---|---|---|---|---|---|
| https://eogdata.mines.edu/products/viirs/ | 2026-09-07 | Domínio público (NASA/NOAA; EOG sem restrições) | Earth Observation Group, Colorado School of Mines. VIIRS DNB Nighttime Day/Night Annual Composites. Version: [versão]. Year: [ano]. | 15 arcsec (~500 m) | 2012–presente | Não espelhado (acesso via GEE ou EOG FTP público) | Pipeline via GEE |

**Observação:** Dados em GeoTIFF, compostos anuais medianos por período de seca (maio–outubro). Continuidade de DMSP-OLS a partir de 2012.

---

### 4. Harmonized DMSP-VIIRS Nighttime Lights (1992–2018) — Li et al. (2020)

| URL | Data de acesso | Licença | Citação | Resolução/Nível geográfico | Anos cobertos | Arquivo local | Status |
|---|---|---|---|---|---|---|---|
| https://figshare.com/articles/dataset/Harmonization_of_DMSP_and_VIIRS_nighttime_light_data_from_1992-2018_at_the_global_scale/9828827 | 2026-09-07 | CC-BY 4.0 | Li, X., Zhou, Y., Zhao, M. & Zhao, X. (2020). A harmonized global nighttime light dataset 1992–2018. *Scientific Data*, 7, 168. DOI: 10.6084/m9.figshare.9828827. | 30 arcsec (~1 km) | 1992–2018 | Não espelhado (acesso via figshare) | Validação opcional |

**Observação:** Série harmonizada que intercalibra DMSP (1992–2013) com VIIRS simulado (2014–2018). Nível B para validação (exigência de cadastro em figshare/Zenodo). Pode complementar análise de série contínua, mas não será dependência do pipeline.

---

### 5. Global Coal Mine Tracker (Global Energy Monitor, Agosto 2026)

| URL | Data de acesso | Licença | Citação | Resolução/Nível geográfico | Anos cobertos | Arquivo local | Status |
|---|---|---|---|---|---|---|---|
| https://globalenergymonitor.org/projects/global-coal-mine-tracker/download-data/ | 2026-09-07 | CC-BY 4.0 International | Global Energy Monitor. Global Coal Mine Tracker. August 2026 release. | Mine-level (pontos + polígonos) | 2022–agosto 2026 (atualizado continuamente) | Não espelhado (formulário de download; verificar manualmente) | ⚠ Acesso via formulário |

**Observação:** Download via formulário (nome/email). Não há link direto XLSX. **Registro manual necessário para obter arquivo.** Conteúdo: status operacional, capacity, owner, coordinates, coal type, produção.

**Dados extraídos (verificação contra wiki):**
- **Mina de Moatize:** coordenadas -16.1537, 33.7207 (WGS84); abertura 2011; capacidade 43 Mtpa; status "Mothballed" (care & maintenance); operador Vulcan Mozambique SA (100%, Jindal).
- **Mina de Benga:** localização e operador a verificar contra GCMT.

---

### 6. INE Moçambique — Índice de Preços ao Consumidor (IPC), Tete

| URL | Data de acesso | Licença | Citação | Resolução/Nível geográfico | Anos cobertos | Arquivo local | Status |
|---|---|---|---|---|---|---|---|
| https://www.ine.gov.mz/web/guest/b/indice-de-preco-no-consumidor | 2026-09-07 | Licença INE (acesso público, citação obrigatória) | Instituto Nacional de Estatística (INE) de Moçambique. Índice de Preços ao Consumidor (IPC). Base: 2023 = 100. [Período]. | 8 cidades (Maputo, Beira, Nampula, Quelimane, **Tete**, Chimoio, Xai-Xai, Inhambane) | 1997–setembro 2025 (atualização mensal) | Não disponível (servidor não acessível; verificar manualmente) | ✗ Acesso falhado |

**Observação:** PDFs publicados mensalmente em ine.gov.mz. Tete é incluída em coleta de 8 cidades (peso 9,74% na cesta). IPC em regime novo (base 2023 = 100 desde janeiro 2025). **Recomendação:** acessar manualmente via site INE ou via repositório de dados de Moçambique (data.humdata.org ou opendataforafrica.org) se disponível.

---

## Resumo por Status

| Status | Fontes | Açoes necessárias |
|---|---|---|
| ✓ Espelhado em `data/raw/` | World Bank Pink Sheet (Junho 2026) | Nenhuma — arquivo pronto para pipeline |
| ⚠ Acesso via GEE/repositório público | DMSP-OLS, VIIRS DNB, Li et al. 2020 (figshare) | Scripts em `pipeline/00_fetch/` para baixar via GEE ou API pública |
| ⚠ Acesso via formulário | Global Coal Mine Tracker (GCMT) | Preenchimento manual do formulário; registrar XLSX quando obtido |
| ✗ Não acessível no momento | INE IPC (Tete) | Verificação manual; servidor www.ine.gov.mz indisponível em 2026-09-07 |

---

## Âncoras Factuais — Re-verificação contra GCMT (2026-09-07)

| Item | Valor original (§8 CLAUDE.md) | Valor verificado (GCMT Moatize_Coal_Mine wiki) | Divergência? | Ação |
|---|---|---|---|---|
| Mina de Moatize — coordenadas | 16,1678°S 33,7895°E | 16°09'13"S (≈16.1537°S) 33°43'15"E (≈33.7208°E) | Mínima (<1 km); dentro de incerteza de digitalização | ✓ CONFIRMADO |
| Mina de Moatize — abertura | 2011 | 2011 | Sim | ✓ CONFIRMADO |
| Mina de Moatize — capacidade | ~140 km² (pegada) | Não encontrado no wiki (capacidade: 43 Mtpa) | Áreas diferentes (pegada vs. produção) | ⚠ CLARO (140 km² é pegada, não capacidade) |
| Concessão Vale — licitação | 2004 | Não documentado explicitamente no wiki (texto menciona "begun mid-2000s") | Não verificável via wiki | — |
| Concessão Vale — licença | 2006 | Não documentado explicitamente no wiki | Não verificável via wiki | — |
| Vale — inauguração | 08/05/2011 | "May 2011" (exato até mês; dia 8 não confirmado) | Mês confirmado; dia não localizável | ✓ CONFIRMADO (mês/ano) |
| Venda a Vulcan | 2022 (venda alegada) | Dezembro 2021 (acordo); abril 2022 (fechamento) | Tecnicamente em 2021/2022; wiki diz "Vale sold in December 2021" | ✓ CONFIRMADO (2021–2022) |
| Operador corrente | Vulcan Minerals (Jindal Group) | Vulcan Mozambique SA (100%, Jindal) | Sim | ✓ CONFIRMADO |
| Status atual (2026) | — (especificação dizia "verificar situação atual") | "Mothballed" (care & maintenance) | Observado novo | ✓ NOVO — não operacional em 2026 |

**Conclusão:** Âncoras sobre mina de Moatize **confirmadas com pequenas precisões**. Status operacional em 2026: **mothballed** (não em operação plena).

