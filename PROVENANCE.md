# PROVENANCE.md

Cadeia de proveniência por artefato (§11.2.3): insumos com hash, script com commit,
parâmetros com hash do YAML, data, versão do ambiente e selo
`observado` / `interpolado` / `modelado`.

> **Gerado por `scripts/consolidar_registros.py` a partir de `data/provenance_parts/`.**
> Não edite este arquivo à mão: edite o fragmento da família e reexecute o script.


Consolidado em 2026-09-09.


---

<!-- fonte: data/provenance_parts/adensamento.md -->

<!-- SECAO_ADENSAMENTO_INICIO -->
## Adensamento 2020-2025 — concordância de três sinais (docs/ADR/0016, §5.2/§5.6)

Script: `pipeline/02_metrics/adensamento.py`.
Gerado em 2026-09-09.

Camada `modelado`, grade de 240 m (8×
8 pixels de 30 m), domínio = células completas
(`n_pixels_30m == 64`; 43416 células,
2500.76 km²). Três sinais (S1 fração construída própria, S2
inclinação Theil-Sen de luz noturna, S3 resíduo de pegada de edificações Open
Buildings) convertidos a posto (ECDF) e votados contra um corte de quantil
(`TAU = 0.7` declarado; realizado
`TAU_s1=0.007436`, `TAU_s2=0.001117`,
`TAU_s3=0.352931`) — voto exige também `dominio_ocupado`
(Emenda 2 do ADR 0016). `adensando ⇔ Σ votos ≥ 2`. Sete classes por precedência,
partição exaustiva.

### Área por classe (km², contagem real de pixels de 30 m — ver `docs/ADR/0016`,
### achado 2 do portão da Frente B: `fora_de_dominio` NÃO usa `n_células × área
### nominal`, que superestimava por ~2,67×)

| classe | área (km²) |
|---|---|
| `fora_de_dominio` | 5.7888 |
| `vazio_estavel` | 2365.8624 |
| `esparso_estavel` | 44.1792 |
| `adensando` | 15.3216 |
| `expansao_nova` | 10.3104 |
| `consolidado` | 19.6416 |
| `pegada_industrial` | 45.4464 |

### Sensibilidade

Razão máxima entre a variante mais extrema e a base, no primeiro decil de células
adensando: **2.2931** — regime de publicação:
**publicada só como padrão espacial e ordem de grandeza, NÃO como área (razão em (2.0, 5.0])** (`publicavel_como=padrao_espacial`).
Ver `data/processed/adensamento_sensibilidade.csv` (todas as variantes `tau_0*`/`qalto_0*`/
`qbaixo_0*`, pré-registradas antes de ver o resultado, §Decisão-9 do ADR).

### Riscos declarados (R1-R10, ver ADR para detalhe)

- **R1**: erro espacialmente estruturado sobrevive ao posto
- **R2**: S1 e S3 partilham f_2020 — votos não são independentes
- **R3**: camada não detecta esvaziamento (S1 censurado por baixo pela catraca R2 de urbano)
- **R4**: luz sobreamostrada de ~500 m para 240 m
- **R5**: S3 pode ser desacordo de sensor, não construção
- **R6**: janela real de S3 é 2020 -> ~2023, não 2020->2025
- **R7**: churn de pixel de 31% sobrevive parcialmente à agregação
- **R8**: dependência dos cortes — ver sensibilidade acima
- **R9**: moatize_vila possivelmente inflada (25 de Setembro sem geometria)
- **R10**: camada modelada, risco de ser lida como observada — selo em 4 lugares

### Saídas

Raster 240 m: `data/processed/imagery/adensamento_2020_2025_240m_32736.tif`. Raster 30 m (desagregado, mesma classe
em todos os pixels da célula): `data/processed/imagery/adensamento_2020_2025_30m_32736.tif`. Vetor:
`data/processed/imagery/adensamento_2020_2025.geojson` (443 polígonos, atributos
`f_2020`/`f_2025`/`s1`/`s2`/`s3`/`concordancia`/`fracao_industrial` — reconstroem
`classe` e `concordancia` sem reexecutar o pipeline, contratos T2/T13 de
`pipeline/tests/test_adensamento.py`). Por unidade:
`data/processed/adensamento_2020_2025_por_unidade.csv`.

Não alimenta `stats_by_year_by_unit.csv` (§ Makefile, alvo `metrics`): camada
independente, lida por unidade/ano avulsos. Selo `modelado` em quatro lugares
(raster 240 m, raster 30 m, GeoJSON, CSV por unidade) — risco R10.

<!-- SECAO_ADENSAMENTO_FIM -->


---

<!-- fonte: data/provenance_parts/agricultura.md -->

# Proveniência — Agricultura Urbana e Periurbana

Detalhes de acesso, download, resolução geográfica, anos cobertos e suficiência para
responder às perguntas de §1 de CLAUDE.md. **Reexecução T3** — alinha este arquivo às
correções já aplicadas em `data/licenses_parts/agricultura.md` (T2), que T2 havia
deixado de propagar aqui. Todas as datas de verificação: 2026-09-07.

> Nota de consolidação: existe também `data/PROVENANCE.md`, criado por uma execução
> anterior. Pela convenção do repositório (§11.1) o `PROVENANCE.md` **canônico** é o da
> raiz do projeto, que hoje só documenta artefatos de `data/processed/` (ainda vazio).
> `data/PROVENANCE.md` é uma duplicata desalinhada (mesmos DOI/URLs incorretos
> corrigidos aqui) — **não editada por esta tarefa**; fica registrada para o
> orquestrador decidir sua fusão ou remoção.

## Rasters de cobertura do solo

### 1. GLAD Global Cropland (Potapov et al. 2021)

| Atributo | Valor |
|----------|-------|
| **URL de acesso** | https://glad.umd.edu/dataset/croplands |
| **URL de download por tile** | https://gladxfer.umd.edu/Potapov/Global_Crop/Data/Global_cropland_SE_{2003,2007,2011,2015,2019}.tif |
| **Data de verificação** | 2026-09-07 |
| **Licença** | CC-BY 4.0 |
| **Citação recomendada** | Potapov, P., Turubanova, S., Hansen, M.C., Tyukavina, A., Zalles, V., Khan, A., Song, X.-P., Pickens, A., Shen, Q., Cortez, J. (2021). "Global maps of cropland extent and change show accelerated cropland expansion in the twenty-first century." Nature Food 3, 19–28. DOI 10.1038/s43016-021-00429-z |
| **Resolução espacial** | 30 m |
| **Anos cobertos** | 2003, 2007, 2011, 2015, 2019 (compostos quinquenais; **não** 2000/2004/2008/2012/2016, erro de T1) |
| **Âmbito geográfico** | Global; recorte obrigatório para AOI Tete–Moatize (33.50°E–34.10°E / 16.35°S–16.00°S) (AOI confirmada pelo ADR 0001; o bbox provisório terminava em 33.95°E) |
| **Tamanho estimado (AOI)** | Arquivo é regional (SE = Sudeste da África); recorte necessário após download |
| **Tipo de dado** | Máscara binária (cultivo vs. não-cultivo) |
| **Status de download** | Confirmado por HTTP: página 200 (após redirect 301); tile 2019 200. Não baixado nesta tarefa (fora do escopo de execução de fetch em massa); script corrigido em `pipeline/00_fetch/fetch_glad_cropland.py` |
| **Nota metodológica** | Não discrimina sequeiro × irrigado; usar fenologia de NDVI (01_imagery) para desagregação |

### 2. ESA WorldCover 2020 e 2021

| Atributo | Valor |
|----------|-------|
| **URL de acesso** | https://esa-worldcover.org/en/data-access |
| **URL de download por tile (AOI)** | `https://esa-worldcover.s3.eu-central-1.amazonaws.com/v100/2020/map/ESA_WorldCover_10m_2020_v100_S18E033_Map.tif` (2020); `https://esa-worldcover.s3.eu-central-1.amazonaws.com/v200/2021/map/ESA_WorldCover_10m_2021_v200_S18E033_Map.tif` (2021) |
| **Data de verificação** | 2026-09-07 |
| **Licença** | CC-BY 4.0 |
| **Citação recomendada** | Zanaga, D. et al. (2022). "ESA WorldCover 10 m 2020 v100" DOI 10.5281/zenodo.5571936; e "ESA WorldCover 10 m 2021 v200" DOI 10.5281/zenodo.7254221 — citar o DOI do ano usado (ambos confirmados via Crossref/Zenodo) |
| **Resolução espacial** | 10 m |
| **Anos cobertos** | 2020, 2021 |
| **Âmbito geográfico** | Global, distribuído em tiles de 3°×3°; tile `S18E033` cobre a AOI |
| **Tamanho estimado (AOI)** | Tile completo, recorte necessário |
| **Tipo de dado** | Classificação multiclasse (11 classes incluindo cropland = classe 40) |
| **Status de download** | Confirmado por HTTP: tiles 2020 e 2021 ambos 200 no bucket S3 sem assinatura. **Digital Earth Africa removido como via alternativa** — `data.digitalearthafrica.org` não responde (timeout, código 000) |
| **Nota metodológica** | Cropland = classe 40; não discrimina sequeiro × irrigado |

### 3. Copernicus CGLS-LC100 (100 m, 2015–2019)

| Atributo | Valor |
|----------|-------|
| **URL de acesso** | https://land.copernicus.eu/en/products/global-dynamic-land-cover/copernicus-global-land-service-land-cover-100m-collection-3-epoch-2015-globe |
| **URL de download por época** | Zenodo, um registro por época: 2015=zenodo.org/records/3939038; 2016=3518026; 2017=3518036; 2018=3518038; 2019=3939050 |
| **Data de verificação** | 2026-09-07 |
| **Licença** | Copernicus (uso livre, redistribuição permitida, citação obrigatória) |
| **Citação recomendada** | Buchhorn, M. et al. (2020). "Copernicus Global Land Service: Land Cover 100m: Collection 3: epoch 2015-2019: Globe." Zenodo. DOI da época específica (ex.: 10.5281/zenodo.3518036 para 2017; confirmado via Crossref) |
| **Resolução espacial** | 100 m |
| **Anos cobertos** | 2015, 2016, 2017, 2018, 2019 (anual) |
| **Âmbito geográfico** | Global; arquivos não recortados por tile (1–8 GB por camada) |
| **Tamanho estimado** | 1,70 GB por camada `Discrete-Classification-map` (época 2017, confirmado por HEAD) |
| **Tipo de dado** | Classificação multiclasse; inclui fração de cultivo (0–100%) |
| **Status de download** | Confirmado por HTTP: registro 2017 (id 3518036) — metadata 200, download HEAD 200. Requer leitura em janela via GDAL `/vsicurl/` ou download completo + recorte |
| **Nota metodológica** | Fornece fração de cultivo e cobertura do solo; válido para validação de GLAD |

### 4. Dynamic World (Google/WRI, 10 m, 2015–presente) — **nível B**

| Atributo | Valor |
|----------|-------|
| **URL de acesso** | https://dynamicworld.app/ (visualização); dado real: GEE `GOOGLE/DYNAMICWORLD/V1` |
| **URL de download alternativa** | Testada listagem de coleções do Microsoft Planetary Computer em 2026-09-07: **não existe coleção `dynamic-world`** (404). Coleções próximas encontradas: `io-lulc`, `io-lulc-9-class`, `esa-worldcover` |
| **Data de verificação** | 2026-09-07 |
| **Licença** | CC-BY 4.0 (declarada) |
| **Nível** | **B** — único caminho de acesso real é GEE, o que viola a rota alternativa obrigatória sem GEE (§11.3). Uso restrito a validação visual |
| **Citação recomendada** | Brown, C.F. et al. (2022). "Dynamic World, Near real-time global 10 m land use land cover mapping." Scientific Data 9, 251. DOI 10.1038/s41597-022-01307-4 (citação não reconfirmada via Crossref nesta rodada — verificar antes de uso efetivo) |
| **Resolução espacial** | 10 m |
| **Anos cobertos** | 2015–presente (contínuo) |
| **Status** | Não baixado (nível B); nenhum script de fetch em `pipeline/00_fetch/` grava o bruto — apenas ESRI/IO e CGLS-LC100 cobrem esse papel como fontes A |

### 5. ESRI/Impact Observatory 10 m LULC anual (2017–2024)

| Atributo | Valor |
|----------|-------|
| **URL de acesso** | https://www.arcgis.com/home/item.html?id=cfcb7609de5f478eb7666240902d4d3d (Living Atlas) |
| **URL de download (bucket real)** | `https://s3.us-west-2.amazonaws.com/io-10m-annual-lulc/` — **não** `io-lulc-annual-v02` (404 confirmado, bucket não existe; erro de T1) |
| **Data de verificação** | 2026-09-07 |
| **Licença** | CC-BY 4.0 |
| **Citação recomendada** | Karra, K. et al. / Impact Observatory (2023, atualizado anualmente). "10m Annual Land Use Land Cover (9-class)." AWS Open Data Registry: https://registry.opendata.aws/io-lulc/ |
| **Resolução espacial** | 10 m |
| **Anos cobertos** | **2017–2024** (não 2017–2025: 2025 ainda não publicado no bucket em 2026-09-07 — corrigido) |
| **Âmbito geográfico** | Global, tiles nomeados `<MGRS>_<ano>.tif` |
| **Status de download** | Confirmado por HTTP: bucket raiz 200; tile `01C_2017.tif` HEAD 200; bucket antigo `io-lulc-annual-v02` = 404 |
| **Nota metodológica** | Cropland = classe 5 ("crops"); não discrimina sequeiro/irrigado sem fenologia complementar |

### 6. Copernicus DEM GLO-30

| Atributo | Valor |
|----------|-------|
| **URL de acesso** | https://dataspace.copernicus.eu/explore-data/data-collections/copernicus-contributing-missions/collections-description/COP-DEM |
| **URL de download anônimo (AWS Open Data)** | `https://copernicus-dem-30m.s3.amazonaws.com/Copernicus_DSM_COG_10_S16_00_E033_00_DEM/Copernicus_DSM_COG_10_S16_00_E033_00_DEM.tif` e tile `S17_00_E033_00` (AOI cobre as duas linhas de latitude) |
| **Data de verificação** | 2026-09-07 |
| **Licença** | Licença Copernicus (uso livre e gratuito; atribuição obrigatória) |
| **Citação recomendada** | European Space Agency / Airbus (2022). "Copernicus DEM GLO-30." DOI 10.5270/ESA-c5d3d65 |
| **Resolução espacial** | 30 m |
| **Anos cobertos** | Datum fixo (sem série temporal; captura radar 2011–2015) |
| **Âmbito geográfico** | Global |
| **Status de download** | Confirmado por HTTP: bucket raiz 200; ambos os tiles (S16 e S17) 200 |
| **Via removida** | OpenTopography (`cloud.sdsc.edu/.../NASADEM_HGT_srtm.vrt`) retorna **401** — exige `API_Key` pessoal do OpenTopography, portanto **não é acesso anônimo**. Reclassificada como nível B se usada; a via primária A passa a ser o bucket AWS `copernicus-dem-30m` |
| **Nota metodológica** | Essencial para HAND (Height Above Nearest Drainage) = discriminador de várzea, combinado com HydroRIVERS |

### 7. HydroRIVERS v1.0 (África)

| Atributo | Valor |
|----------|-------|
| **URL de acesso** | https://www.hydrosheds.org/products/hydrorivers |
| **URL de download direto** | https://data.hydrosheds.org/file/HydroRIVERS/HydroRIVERS_v10_af.gdb.zip |
| **Data de verificação** | 2026-09-07 |
| **Licença** | Licença própria HydroSHEDS — uso livre científico/educacional/comercial com atribuição obrigatória. **Não é CC0/domínio público** (correção de T2: T1 registrou "CC0/Domínio Público" sem texto de licença localizado) |
| **Citação recomendada** | Lehner, B., & Grill, G. (2013). "Global river hydrography and network routing: baseline data and new approaches to study the world's large river systems." Hydrological Processes, 27(15), 2171–2186. DOI **10.1002/hyp.9740** (corrigido — DOI anterior `10.1002/hyp.9807` resolve, mas para um artigo diferente, de Hughes et al., não relacionado; confirmado via Crossref) |
| **Resolução espacial** | Vetorial; LineString com atributos de fluxo |
| **Anos cobertos** | Datum fixo (sem série temporal) |
| **Âmbito geográfico** | África; arquivo cobre todo o continente (recorte necessário para AOI) |
| **Tamanho** | 116.303.789 bytes (110,9 MiB) — medido no arquivo efetivamente baixado |
| **Status de download** | **Baixado e espelhado** em `data/raw/hydrorivers_af_v10.gdb.zip`, com `.sha256` (formato `<hash>  <nome>`, conferido) e `.meta.json` (corrigido nesta tarefa: licença e DOI de citação atualizados) |
| **Nota metodológica** | Entrada obrigatória para HAND em combinação com Copernicus DEM |
| **Recomendação de versionamento** | Ver seção "Recomendação — HydroRIVERS 116 MB" abaixo |

## Dados domiciliares e censitários

Política aplicada (decisão do usuário, 2026-09-07): documento do INE servido pelo
catálogo `mozdata.ine.gov.mz` ou por snapshot do Internet Archive conta como fonte
primária, porque `ine.gov.mz` está fora do ar (código `000` em todas as variantes
testadas). Snapshot de agregador (citypopulation.de, Wikipedia) continua não citável.

### 8. INE — Censos 2007 e 2017 (tabulações sobre agricultura urbana)

| Atributo | Valor |
|----------|-------|
| **URL de acesso** | Censo 2007: https://mozdata.ine.gov.mz/index.php/catalog/22 ; Censo 2017: https://mozdata.ine.gov.mz/index.php/catalog/24 |
| **Data de verificação** | 2026-09-07 (catalog/22 e catalog/24: HTTP 200) |
| **Licença** | INE — citação exigida; termos de uso do catálogo NADA (Nesstar/CKAN) não confirmados por raspagem automatizada (página é SPA) |
| **Citação recomendada** | INE (2007, 2017). "Censo Geral da População e Habitação." Instituto Nacional de Estatística, Moçambique |
| **Resolução geográfica** | Província/distrito/cidade (não uniforme por variável) |
| **Anos** | 2007 (III RGPH), 2017 (IV RGPH) |
| **Âmbito** | Moçambique; recorte para Cidade de Tete e Distrito de Moatize |
| **Disponibilidade de tabulação "domicílios com atividade agrícola/posse de machamba"** | **Não disponível — tabulação não localizada** nas páginas do catálogo testadas nesta verificação (200 na página do catálogo não implica tabulação específica publicada; não confirmada por raspagem de texto). Motivo exato: página é SPA carregada via JavaScript, não indexável por `curl`; navegação manual do fluxo "get-microdata" fica pendente |
| **Status** | Nível "A condicional": documento é do INE (via mozdata), mas o fluxo de acesso a microdados ("get-microdata") pode exigir aprovação humana, o que rebaixaria a B (mesmo tratamento do IPUMS) — **não verificado manualmente nesta tarefa** |
| **Nota metodológica** | Censitária (observada); melhor fonte possível para dimensão domiciliar de H6 se a tabulação existir e for de acesso imediato |

### 9. INE — Censo Agro-Pecuário 2009–10 (CAP)

| Atributo | Valor |
|----------|-------|
| **URL de acesso** | https://mozdata.ine.gov.mz/index.php/catalog/37 |
| **Data de verificação** | 2026-09-07 (catalog/37: HTTP 200) |
| **Licença** | INE — citação exigida |
| **Citação recomendada** | INE (2011). "II Censo Agro-Pecuário 2009–2010: Resultados Definitivos." Instituto Nacional de Estatística, Moçambique |
| **Resolução geográfica** | Distrito e abaixo |
| **Anos** | Coleta 2009–2010; publicação 2011 |
| **Âmbito** | Moçambique, incluindo Tete e Moatize |
| **Conteúdo** | Explorações agropecuárias, área cultivada, tipo de cultivo |
| **Status** | Catálogo confirmado (200); microdados/tabulações por distrito não baixados nesta tarefa — fluxo "get-microdata" não verificado manualmente (mesma ressalva do item 8) |
| **Nota metodológica** | Linha de base pré-boom (anterior à operação da Vale em 2011); essencial para H5 |

### 10. INE — "Censo Agro-Pecuário 2019–20" (nome citado em CLAUDE.md §4.6)

| Atributo | Valor |
|----------|-------|
| **Situação** | **Não disponível sob esse nome exato.** Nenhum documento discreto chamado "Censo Agro-Pecuário 2019–20" foi localizado no catálogo mozdata nesta verificação |
| **Melhor aproximação encontrada** | Inquérito Agrário Integrado (IAI) 2020 — **é um inquérito amostral, não um censo** — catálogo: https://mozdata.ine.gov.mz/index.php/catalog/62 (HTTP 200, 2026-09-07) |
| **Citação recomendada (da aproximação)** | INE (2021). "Inquérito Agrário Integrado 2020." Instituto Nacional de Estatística, Moçambique |
| **Licença** | INE — citação exigida |
| **Ressalva metodológica obrigatória** | Ao usar o IAI 2020 no lugar do CAP 2019-20, registrar explicitamente a diferença de desenho amostral vs. censitário; não tratar os dois como equivalentes em precisão ou cobertura |
| **Status** | Motivo exato do "não disponível": busca no catálogo público não retornou documento com esse nome; não confirmado se existe sob outro nome ou se está represado internamente no INE |

### 11. INE — IOF 2014/15, 2019/20, 2022

| Atributo | Valor |
|----------|-------|
| **URL de acesso** | IOF 2022: https://mozdata.ine.gov.mz/index.php/catalog/79 (HTTP 200, 2026-09-07) |
| **URL de acesso — 2014/15 e 2019/20** | Não localizados como catálogos individuais numerados nesta verificação; requer busca adicional dentro do mesmo portal mozdata (não executada nesta tarefa por escopo de tempo) |
| **Licença** | INE — citação exigida |
| **Citação recomendada** | INE (2015, 2021, 2023). "Inquérito aos Orçamentos Familiares [IOF] 2014/15, 2019/20, 2022/23." Instituto Nacional de Estatística, Moçambique |
| **Resolução geográfica** | Província (raramente urbano/rural específico) |
| **Anos** | Coletas 2014–15, 2019–20, 2022–23 |
| **Âmbito** | Moçambique, incluindo Tete por agregação provincial (sem desagregação para Tete/Moatize cidade) |
| **Conteúdo** | Consumo, ativos, segurança alimentar, atividade agrícola domiciliar (consumo próprio) |
| **Status** | Catálogo do IOF 2022 confirmado (200); 2014/15 e 2019/20 pendentes de localização exata — registrar como "pendente de localização", não "não disponível", pois o portal está de pé |
| **Nota metodológica** | Relevante para H6 (segurança alimentar no bust); desagregação apenas provincial, não urbana/Tete-específica |

---

## Correções propagadas de T2 → T3 (este arquivo estava desatualizado)

`data/licenses_parts/agricultura.md` já continha as correções abaixo desde T2, mas
`data/provenance_parts/agricultura.md` (este arquivo) ainda trazia as versões antigas
incorretas. T3 corrige:

1. DOI do GLAD Cropland: `10.1038/s41597-022-01292-5` (não resolve) → `10.1038/s43016-021-00429-z` (Nature Food, confirmado via Crossref).
2. Anos do GLAD Cropland: `2000, 2004, 2008, 2012, 2016, 2019` → `2003, 2007, 2011, 2015, 2019` (arquivos reais em `gladxfer.umd.edu`).
3. ESA WorldCover: removida referência a `data.digitalearthafrica.org` (sem resposta); URLs de tile S3 reais (`S18E033`) adicionadas; DOIs específicos por ano (2020: zenodo.5571936; 2021: zenodo.7254221).
4. Copernicus DEM: removida via primária via OpenTopography (`cloud.sdsc.edu/.../NASADEM_HGT_srtm.vrt`, HTTP 401, exige chave — não é acesso anônimo); via primária A passa a ser o bucket AWS `copernicus-dem-30m`.
5. HydroRIVERS: licença "CC0/Domínio Público" → "licença própria HydroSHEDS" (texto real da página do produtor); DOI de citação `10.1002/hyp.9807` (resolve, mas artigo errado) → `10.1002/hyp.9740` (confirmado, Lehner & Grill 2013). Também corrigido no `data/raw/hydrorivers_af_v10.gdb.zip.meta.json`.
6. ESRI/Impact Observatory: bucket `io-lulc-annual-v02` (404, não existe) → `io-10m-annual-lulc` (confirmado); cobertura "2017–2025" → "2017–2024" (2025 ainda não publicado).

## Recomendação — HydroRIVERS 116 MB (§11.1)

O arquivo `data/raw/hydrorivers_af_v10.gdb.zip` pesa 116.303.789 bytes (~111 MiB),
medido diretamente (`ls -la` e recomputação do SHA256, ambos conferem com o
`.meta.json`). §11.1 admite DVC/git-lfs para binários grandes. Recomendação: **não
versionar no git "puro"** — um arquivo de 111 MiB é o maior do repositório com folga e
infla o histórico para sempre, mesmo que seja pequeno perto de outros níveis B. Se o
projeto adotar DVC ou git-lfs, versionar por lá; caso contrário, manter apenas
`pipeline/00_fetch/fetch_hydro_datasets.py` (idempotente, com hash esperado) como
fonte de verdade e não commitar o binário — reexecução local reconstrói o arquivo.
Decisão final cabe ao orquestrador; `.gitignore` não foi alterado por esta tarefa.

---

## Suficiência para responder às perguntas de §1 e testar H5 e H6

(Seção preservada da execução anterior — conteúdo bom, atualizado às fontes
reclassificadas nesta rodada.)

### Pergunta 8: "Agricultura urbana e periurbana"

**Pergunta completa** (CLAUDE.md §1):
> Onde estão os bolsões (machambas de sequeiro, hortas irrigadas de baixa, campos de vazante) dentro e no entorno de Tete e Moatize; quanto ocupam; como evoluíram (conversão em construído, deslocamento para anéis externos, persistência em várzeas e interstícios); papel na segurança alimentar e na renda dos domicílios urbanos, incluindo reassentados; e que espaço lhes resta nos cenários pós-2025.

**Avaliação de suficiência**:

#### Parte 1: "Onde estão e quanto ocupam" (mapeamento geográfico e área)

- **Sequeiro urbano/periurbano (2003–2024)**: GLAD (2003, 2007, 2011, 2015, 2019) + ESRI/IO (2017–2024) = cobertura contígua a partir de 2003, densa a partir de 2017. CGLS-LC100 (2015–19) e ESA WorldCover (2020–21) para validação cruzada.
- **Irrigado vs. sequeiro (fenologia)**: Landsat/Sentinel-2 NDVI mensal — **pertence a `pipeline/01_imagery`, não a esta família**; sem essa camada, não há discriminação sequeiro/irrigado.
- **Várzea (cultivo de vazante)**: HAND (Copernicus DEM via AWS + HydroRIVERS) define geometricamente a zona de risco de inundação; NDWI intra-anual (01_imagery) confirma. **OK para a parte geométrica**.
- **Reassentamento**: Cateme, 25 de Setembro etc. já geolocalizados em `data/raw/reassentamentos.geojson` (família reassentamento); machambas atribuídas nos EIA/RAP ainda não integradas a esta camada.

**Insuficiência identificada** (inalterada desde a rodada anterior):
- Componente fenológica (NDVI/NDWI intra-anual) não está nesta família; será em `01_imagery`.
- Dados domiciliares específicos sobre "posse de machamba" em Tete/Moatize continuam **não confirmados como públicos** (item 8 acima).

#### Parte 2: "Como evoluíram" (séries temporais, matrizes de transição)

- **Conversão cropland→construído**: GLAD/ESRI-IO vs. urbano classificado (02_metrics/03_causal). Anos-âncora comuns: 2003/2007/2011/2015/2019 (GLAD) cruzam parcialmente com 2000/2005/2010/2015/2020/2025 (CLAUDE.md §2) — **defasagem de anos exige interpolação ou reamostragem, documentar explicitamente ao usar**.
- **Deslocamento (anel periurbano recalculado por ano)**: definido por GHSL SMOD (família construída, não aqui); metodologia em §5.6.
- **Persistência em várzea**: HAND + fenologia NDVI (01_imagery).

**Insuficiência clara**: dados de abandono/consolidação pixel-a-pixel de bolsões específicos não existem em fonte A; tratamento qualitativo via literatura (HRW, CIP, Mosca & Selemane), fora desta família (§4.5).

#### Parte 3: "Papel na segurança alimentar e renda domiciliar" (reassentados)

- **Domicílios urbanos com atividade agrícola**: Censos 2007/17 — tabulação **não disponível** nesta verificação (item 8). **Lacuna crítica confirmada** (não resolvida desde a rodada anterior).
- **Consumo próprio e segurança alimentar**: IOF 2019-20 e 2022 — catálogo do 2022 confirmado (200); 2019/20 pendente de localização exata. Desagregação apenas provincial, não Tete-específica.
- **Reassentamento**: literatura (HRW, CIP, Mosca) qualifica solo pobre em Cateme e perda de acesso — alimenta cenários qualitativamente.

**Lacuna mantida**: sem microdados/tabulações desagregadas para Tete/Moatize, o papel da agricultura urbana na renda domiciliar é inferido via IOF provincial + literatura, não medido diretamente.

#### Parte 4: "Cenários pós-2025"

- Projeção de pressão sobre bolsões: possível com séries GLAD/ESRI-IO em DiD/extrapolação, sujeita à defasagem de anos-âncora citada na Parte 2.
- Cenários de permanência vs. perda: exploratório, sensível a hipóteses de preço do carvão/emprego (proxy: luzes noturnas, §4.4).

**Suficiência: PARCIAL, com lacunas explicitamente documentadas** (igual à rodada anterior; nenhuma lacuna nova introduzida pelas correções de URL/DOI desta tarefa — eram problemas de citação e acesso, não de cobertura de dados).

### Hipótese H5 — expansão consome terras agrícolas acessíveis; agricultura persiste em várzeas

**Dados necessários e status:**
1. Topografia/declividade — Copernicus DEM GLO-30 (via AWS, corrigida): confirmado acesso A. ✓
2. HAND (várzea) — Copernicus DEM + HydroRIVERS: ambos confirmados A. ✓
3. Sequeiro/irrigado por local — NDVI intra-anual: pendente, pertence a `01_imagery`.

**Avaliação**: **TESTÁVEL** com GLAD/ESRI-IO + Copernicus DEM + HydroRIVERS já confirmados nesta rodada. Fenologia será adicionada em 01_imagery.

### Hipótese H6 — agricultura urbana como amortecedor após 2016 (bust)

**Dados necessários e status:**
1. Série de área cultivada 2010–2024 — GLAD (até 2019) + ESRI/IO (2017–2024): combinação necessária, cobertura contígua confirmada. ✓
2. Dimensão domiciliar (posse de machamba, consumo próprio) — IOF (catálogo 2022 confirmado; 2014/15 e 2019/20 pendentes de localização): desagregação só provincial. ⚠️
3. Especificidade de reassentados — literatura + EIA/RAP (família §4.5, fora do escopo aqui).

**Avaliação**: **TESTÁVEL PARCIALMENTE**. Série de área OK; dimensão domiciliar limitada à escala provincial, sem granularidade Tete/Moatize.

---

## Resumo: Suficiência GERAL

| Elemento | Status | Observação |
|----------|--------|-----------|
| Mapeamento de cultivo 2003–2024 | ✓ OK | GLAD 2003–19 + ESRI/IO 2017–24; URLs e anos corrigidos nesta rodada |
| Discriminação sequeiro/irrigado | ⚠️ Parcial | Requer fenologia (01_imagery) |
| Delimitação de várzea (HAND) | ✓ OK | Copernicus DEM (via AWS, não OpenTopography) + HydroRIVERS confirmados A |
| Série de área urbana (GHSL) | ✓ OK | Em §4.2 (02_metrics), fora desta família |
| Matrizes de transição (conversão) | ✓ Possível | Sujeito à defasagem de anos-âncora GLAD vs. CLAUDE.md §2 |
| Dimensão domiciliar (H6) | ⚠️ Limitado | IOF provincial parcialmente localizado; Censos com tabulação não confirmada |
| Reassentados especificamente | ⚠️ Qualitativo | Literatura + EIA/RAP (§4.5) |
| Cenários 2025–2040 | ⚠️ Exploratório | Séries OK; parâmetros comportamentais são hipótese |

**Conclusão**: as correções de DOI/URL desta rodada (T3) resolvem defeitos de citação e
de acesso identificados pelo orquestrador, sem alterar a avaliação de suficiência
substantiva feita na rodada anterior: o conjunto A responde majoritariamente a §1.8 e
permite testar H5; H6 permanece parcialmente testável, limitado pela ausência de
tabulações domiciliares desagregadas para Tete/Moatize (Censos 2007/2017) e pela
localização ainda pendente dos catálogos de IOF 2014/15 e 2019/20.

---

## RECONCILIAÇÃO OBRIGATÓRIA — 2026-09-08

> **As avaliações de suficiência acima são da Fase 0' e foram FALSIFICADAS POR MEDIÇÃO.**
> Elas julgavam **disponibilidade de dado**; o que veio depois mediu **desempenho da
> classificação**, e o resultado é pior que a expectativa. Onde este fragmento diz que uma
> hipótese é testável, vale o que segue.

**`cultivo_sequeiro` NÃO é defensável** (`docs/ADR/0012`, confirmado após a correção de raiz
em `docs/ADR/0014`):

| métrica | valor |
|---|---|
| acurácia do usuário | **0,000** |
| kappa | **−0,065** (pior que aleatório) |
| Jaccard contra GLAD Cropland e ESA WorldCover | **0,001 a 0,002** |
| área classificada × área do GLAD na mesma AOI | 359–761 km² × **~20 km²** |

A correção de `docs/ADR/0014` resolveu a classe de água e as classes de cobertura e **não**
melhorou o cultivo — o que localiza a falha na **abordagem fenológica bianual**, não nos
limiares, e **reforça** o ADR 0012.

**`cultivo_irrigado`** é utilizável com ressalva: acurácia do usuário 0,556 ± 0,344,
Jaccard 0,043–0,098.

### Consequência para as hipóteses

- **H5 — sustentada FRACAMENTE, não "respondível".** O único apoio é o enriquecimento
  relativo em várzea: `cultivo_irrigado` aparece 2 a 3 vezes mais concentrado na zona de
  várzea que `cultivo_sequeiro`, em 4 dos 6 anos-âncora. É sinal de razão entre classes, não
  medida de área agrícola — e a classe de sequeiro, que é o termo de comparação, tem
  acurácia nula.
- **H6 — SEM RESPOSTA.** Não é lacuna de dado domiciliar, como este fragmento supunha na
  Fase 0': é que **a série de área de cultivo que sustentaria a hipótese tem kappa negativo
  e não mede cropland**. Nenhuma leitura de "a agricultura urbana cresceu no bust" se
  sustenta com o que existe.
- **Pergunta 8 de §1** fica respondível apenas na parte de **localização de várzea** e de
  cultivo irrigado com ressalva. "Quanto ocupam" e "como evoluíram" não são respondíveis.


---

<!-- fonte: data/provenance_parts/agricultura_fase2b.md -->

# Proveniência — Fase 2b: agricultura e várzea (§5.6)

Fragmento consolidado por `scripts/consolidar_registros.py` em `PROVENANCE.md`. Não editar à mão as seções entre marcadores: são geradas pelo script correspondente.


<!-- SECAO_CULTIVO_INICIO -->

## Cultivo — separação fenológica sequeiro × irrigado (§5.6.1, Fase 2b)

Gerado por `pipeline/01_imagery/cultivo.py`. `cultivo_sequeiro` e `cultivo_irrigado` são recortes fenológicos DENTRO de `solo_exposto` e `vegetacao` (§5.1), não camadas novas na partição mutuamente exclusiva da AOI: sobrepõem essas duas camadas por construção e são mutuamente exclusivas apenas em relação a `urbano`/`industrial`/`reassentamento`/`agua`.

**Limiar relativo à paisagem do próprio ano** (ratio_irrigado_amp=0.5, ratio_sequeiro_amp=1.3, ratio_sequeiro_chuva=1.0), pelo mesmo motivo de docs/ADR/0011: NDVI absoluto não é comparável entre os anos-âncora desta série.

**Limitação declarada:** fenologia bianual não separa cultivo de vegetação natural com o mesmo padrão sazonal. `cultivo_sequeiro` mede vegetação de fenologia estacional acentuada (inclui savana herbácea/arbustiva sazonal); `cultivo_irrigado` mede verde persistente de baixa amplitude (inclui mata ripária). A acurácia do usuário medida por interpretação visual está em `acuracia_cultivo.py` / `data/processed/acuracia_cultivo_por_ano.csv`.

**Instabilidade herdada da Fase 1:** a proporção vegetacao/solo_exposto muda de forma não monotônica entre anos-âncora por diferença de sensor/pluviosidade (mesmo efeito de docs/ADR/0008 e ADR/0009). A série de área de cultivo herda essa instabilidade e não deve ser lida como mudança real de uso do solo sem controlar por ela.

| ano | sequeiro km² | irrigado km² | domínio veg km² | domínio solo km² | mediana amplitude | mediana NDVI seca | mediana NDVI chuva |
|---|---|---|---|---|---|---|---|
| 2000 | 576.6 | 47.1 | 235.3 | 2219.7 | 0.235 | 0.233 | 0.475 |

<!-- SECAO_CULTIVO_FIM -->




<!-- SECAO_VARZEA_INICIO -->

## Várzea — HAND aproximado (§5.6.2, Fase 2b)

Gerado por `pipeline/01_imagery/varzea.py`. Camada ESTÁTICA (não varia por ano-âncora): geomorfologia, não cobertura do solo.

**Aproximação declarada:** HAND por vizinho mais próximo NO PLANO (`scipy.ndimage.distance_transform_edt`), não por caminho de fluxo D8 — nenhuma biblioteca de roteamento hidrológico (`pysheds`/`richdem`/`whitebox`) está disponível neste ambiente. A aproximação tende a superestimar a várzea em relevo dissecado; é aceitável no vale de baixa declividade do Zambeze/Revúbuè dentro da AOI, mas não foi corrigida onde falha. Ver docstring completa do script.

- **Parâmetros (config/study.yaml):** hand_max_m=10.0, dist_max_rio_m=1000.0
- **Fonte de drenagem:** HydroRIVERS v10 África, 130 trechos na AOI, sem filtro de ordem de fluxo (riachos pequenos incluídos)
- **Área de várzea:** 650.2 km²
- **Selo:** modelado (HAND derivado de DEM observado + rede de drenagem observada)

<!-- SECAO_VARZEA_FIM -->



<!-- SECAO_ACURACIA_CULTIVO_INICIO -->

## Acurácia por classe — cultivo (§5.6.1, §10)

Gerado por `pipeline/01_imagery/acuracia_cultivo.py`. **Não editar à mão.**

**Ano validado:** 2020 (único — ver `amostras_validacao_cultivo.py`). **Intérprete(s):** Claude (Sonnet 5), interpretação visual automatizada de recorte RGB — não humana, não verdade de campo.

| classe | prevalência no mapa | n | AU | IC95 AU | AP | AP estimável? |
|---|---|---|---|---|---|---|
| cultivo_sequeiro | 0.1682 | 8 | 0.0 | 0.0 | 0.0 | True |
| cultivo_irrigado | 0.0138 | 9 | 0.5556 | 0.3443 | 0.154 | True |

**Acurácia global:** 0.621 ± 0.262 · **kappa:** -0.065 · **n indeterminado:** 11 de 36.

AU = acurácia do usuário (1 − comissão) · AP = acurácia do produtor (1 − omissão).

n=12/estrato, ANO ÚNICO (2020) — ver amostras_validacao_cultivo.py para o motivo do desenho reduzido em relação a acuracia.py (construído: 24/estrato, 6 anos). NÃO generalizar este número aos outros 5 anos-âncora. Rótulos por interpretação visual automatizada (mesmo tipo de intérprete de ADR 0007), não verdade de campo. Produtor não é confiável quando produtor_estimavel_* é False — ver alavanca_maxima_1_ponto_*: fração da área da AOI que UM ponto do estrato de maior peso entre os outros dois carrega no estimador.

**Referência externa:** GLAD Cropland / ESA WorldCover / Dynamic World não estavam espelhados em `data/raw/` no momento desta execução (Fase 0' registrou URLs quebradas). Esta validação é só interna (interpretação visual); nenhuma métrica contra produto externo de cobertura de cultivo é reportada. Se os arquivos aparecerem depois, a validação externa é trabalho futuro — não duplicado aqui.

<!-- SECAO_ACURACIA_CULTIVO_FIM -->




<!-- SECAO_VALIDACAO_EXTERNA_CULTIVO_INICIO -->

## Validação externa de cultivo — GLAD Cropland / ESA WorldCover

Gerado por `pipeline/01_imagery/validacao_externa_cultivo.py`. **Concordância, não acurácia** (mesma ressalva de `concordancia_ghsl` em `classificacao.py`): produtos com erro próprio, resolução e definição de cultivo diferentes.

| referência | ano ref. | ano cultivo | camada | área mapa km² | área ref. km² | Jaccard | recall/ref. |
|---|---|---|---|---|---|---|---|
| GLAD_Global_Cropland | 2003 | 2005 | cultivo_sequeiro | 358.671 | 19.895 | 0.001 | 0.0196 |
| GLAD_Global_Cropland | 2003 | 2005 | cultivo_irrigado | 16.389 | 19.895 | 0.0686 | 0.1171 |
| GLAD_Global_Cropland | 2007 | 2005 | cultivo_sequeiro | 358.671 | 17.956 | 0.0007 | 0.0138 |
| GLAD_Global_Cropland | 2007 | 2005 | cultivo_irrigado | 16.389 | 17.956 | 0.0976 | 0.1701 |
| GLAD_Global_Cropland | 2011 | 2010 | cultivo_sequeiro | 760.501 | 20.989 | 0.0011 | 0.0398 |
| GLAD_Global_Cropland | 2011 | 2010 | cultivo_irrigado | 152.651 | 20.989 | 0.0433 | 0.3436 |
| GLAD_Global_Cropland | 2015 | 2015 | cultivo_sequeiro | 398.902 | 24.991 | 0.0018 | 0.0309 |
| GLAD_Global_Cropland | 2015 | 2015 | cultivo_irrigado | 42.66 | 24.991 | 0.1287 | 0.3087 |
| GLAD_Global_Cropland | 2019 | 2020 | cultivo_sequeiro | 421.7 | 40.063 | 0.0006 | 0.0066 |
| GLAD_Global_Cropland | 2019 | 2020 | cultivo_irrigado | 34.552 | 40.063 | 0.1445 | 0.2352 |
| ESA_WorldCover | 2020 | 2020 | cultivo_sequeiro | 421.7 | 42.467 | 0.0043 | 0.0463 |
| ESA_WorldCover | 2020 | 2020 | cultivo_irrigado | 34.552 | 42.467 | 0.0327 | 0.0574 |

Concordância baixa não piora o veredito de docs/ADR/0012 (`cultivo_sequeiro` já reprovado por interpretação visual própria); concordância alta seria evidência de apoio, não validação por si — ver limitações na docstring do script.

<!-- SECAO_VALIDACAO_EXTERNA_CULTIVO_FIM -->


---

<!-- fonte: data/provenance_parts/agricultura_validacao.md -->

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


---

<!-- fonte: data/provenance_parts/app_fase4.md -->

## Fase 4 — artefatos do app (`data/processed/app/` e `app/src/content/`)

### `data/processed/app/imagery/` — camadas para a web

- **Gerado por:** `pipeline/05_app/build_web_assets.py`, alvo `app-data` do Makefile.
- **Selo:** derivado de `data/processed/imagery/`; nenhum dado novo é medido.
- **Nível da fonte:** A (deriva apenas de `data/processed/`).
- **Transformações, todas declaradas em `DECISOES.md` e `manifest.json` locais:**
  reprojeção EPSG:32736 → EPSG:4326 (RFC 7946, sem membro `crs`); precisão de coordenada
  truncada a 6 decimais (~0,1 m); simplificação Douglas-Peucker adaptativa em EPSG:32736,
  com tolerância escolhida por busca gulosa e **teto de 1 % de erro de área** declarado em
  `config/tolerances.yaml → app_geometria_simplificacao`.
- **Erro de área medido, arquivo a arquivo: 0,0000 %.** Conferido de forma independente
  pelo orquestrador comparando a área original em EPSG:32736 com a versão web reprojetada
  de volta: diferença de **+0,0004 % a −0,0007 %**, contagem de feições idêntica.
- **Volume:** 367 MB → 25 MB. O inchaço era **precisão de coordenada**, não complexidade
  geométrica — 15 dígitos por número em UTM.
- **`cultivo_sequeiro` é entregue como grade de 1 km**, não como 42 mil polígonos. Não é
  economia de bytes: com acurácia do usuário 0,000 (`docs/ADR/0012`), polígono comunica
  "objeto detectado" e grade comunica "candidato agregado". A forma da representação passa
  a coincidir com a confiança do dado.
- **`vegetacao` e `solo_exposto` excluídos:** não são camadas de mapa de §6 e carregam a
  instabilidade de 32× a 41× de `docs/ADR/0013`.

### `app/src/content/metodologia.json` — página de metodologia

- **Gerado por:** `pipeline/05_app/gerar_metodologia.py`, com carimbo `gerado_por`.
- **Fontes:** `PROVENANCE.md`, `data/DATA_AUDIT.md`, `docs/ADR/*` e **`uv.lock`**.
- **Nunca redigido à mão** (§6-A). As versões de biblioteca são extraídas do lockfile;
  `pipeline/tests/test_transparencia_metodologica.py` reprova versão divergente.

### Decisão de animação temporal

O slider faz **troca dura de ano ou crossfade de opacidade, nunca interpolação de
geometria**. A identidade pixel a pixel de `urbano` troca 31 % a 54 % entre anos-âncora
(`docs/ADR/0013`): animar isso exibiria instabilidade de classificação como movimento no
terreno, e movimento persuade mais que número.

### Ressalvas que o app exibe onde o número aparece, não em página separada

Comissão de `urbano` (37,5 %–71,4 %, com **IC95 de ±0,20 e prevalência de 0,5–1,9 %**, e a
nota de que **nenhum dos 15 pares de anos-âncora tem IC95 sem sobreposição** — a variação
entre anos não é distinguível de ruído); catraca R2 e incapacidade de detectar contração;
churn de 31 %–54 % junto à tipologia e à matriz de transição; piso de inferência
p = 1/6 ≈ 0,167 ao lado de qualquer p; veredito CONTRAFACTUAL NÃO SUSTENTADO nas quatro
quebras; proibição de atribuir a queda de luz de 2022 à mina (`docs/ADR/0015`).

### O que §6 pede e o app NÃO entrega, declarado em vez de simulado

- **Anéis periurbanos por ano e modo "transições":** o dado não existe
  (`logit_conversao_status.csv` = NÃO DETERMINÁVEL). O app declara a ausência no painel de
  camadas em vez de desenhar geometria plausível.
- **Swipe com WSF/GHSL:** essas camadas não foram preparadas para consumo web.


---

<!-- fonte: data/provenance_parts/arbitragem_p1_2022.md -->

# Arbitragem — placebo espacial P1, quebra de 2022 (S_HARM_soma)

- **Data:** 2026-09-08
- **Papel:** segunda opinião obrigatória da Fase 3 (`docs/DESENHO_FASE3.md` §3.1) e arbitragem pedida em `ORCHESTRATION_LOG.md` 3-10.
- **Lido:** `docs/DESENHO_FASE3.md` (§0–§11), `pipeline/03_causal/placebos.py`, `data/processed/causal/{placebos,its_quebras,veredito_fase3,did_efeitos,did_sintetico_pesos,serie_luzes_anual}.csv`, `docs/ADR/0013`, `docs/ADR/0014`, log 3-09 e 3-10.
- **Nada foi alterado** em `pipeline/`, `data/processed/`, `docs/`.

## 0. O fato que muda a pergunta

A pergunta foi posta como "Tete cai enquanto as cinco capitais sobem". A série já publicada em
`serie_luzes_anual.csv` (coluna `soma_radiancia_adm2_int_recorte`, sensibilidade exigida por E6)
mostra que **a queda de 2022 não está na cidade de Tete**:

| 2021→2022, log-% | valor |
|---|---|
| Retângulo AOI (série primária) | **−6,2 %** |
| ADM2 `MZ0501` Cidade de Tete ∩ recorte (cobertura 0,845) | **+0,7 %** |
| Resto do retângulo (= Moatize + mina + corredor; 2 207 km² dos 2 494) | **−13,6 %** |

Dentro da cidade a luz não cai em 2022; cai **fora** dela, no lado do retângulo onde ficam
a mina e a vila de Moatize. A `max_radiancia` cai 63,7→49,9 no mesmo ano (E5) — o pixel mais
brilhante da AOI é, com toda a probabilidade, a planta de beneficiamento, não um bairro. E o
recorte de Tete tem 2 494 km² contra ~1 000–1 090 km² dos cinco controles: é o único dos seis
que **contém uma pegada industrial de escala** dentro da geometria.

A decomposição obrigatória de §2.3 ("dentro da pegada `industrial` / `urbano` fora da pegada /
resto — sem isso, uma queda de luz por fechamento de planta seria lida como queda de atividade
urbana") **não foi produzida**: não existe artefato em `data/processed/causal/` e nenhum script
de `pipeline/03_causal/` referencia a pegada. O desenho previu exatamente esta confusão e a
proibiu; a execução pulou a etapa.

Segundo fato: "Tete cai" é um ponto. 2023 +14,4 %, 2024 +3,6 %, 2025 +7,4 %; a soma de 2025
(9 366) está 19 % acima da de 2021. O que é verdade é **mais fraco**: Tete cresce 19 % (AOI) ou
37 % (ADM2) entre 2021 e 2025 enquanto os controles crescem 40–61 %, partindo de tendências
pré quase planas (b1 = −0,016 a +0,036) contra 0,072 de Tete. O b2 positivo dos cinco controles
é uma **aceleração comum a partir de 2021** (+13 %, +13 %, +3 %, +5 %, +13 % já em 2021), que o
modelo com t0 = 2022 aloca em nível + inclinação. Cinco capitais não tratadas acelerando em
uníssono de ~0 para ~13 %/ano em 2021–2025 é choque nacional ou produto (V2 estendido a 2025,
Dataverse V10) — em qualquer dos casos, não é contrafactual de Tete.

## 1. Veredito de P1 em 2022: manter, rever ou indeterminado?

**A favor de manter "FALHA".** A regra foi escrita antes do dado; o código (`placebos.py:185`)
implementa a disjunção b2-OU-b3 de forma literal; o ramo b3 dispara. Qualquer revisão depois
de ver que a regra reprova o resultado desejado é especificação procurada — o próprio
orquestrador o disse em 3-10. Manter o veredito custa nada e preserva o pré-registro.

**A favor de rever para "passa".** O ramo b3 não testou nada: 0,5 × |0,0083| = 0,0042 é
satisfeito por qualquer inclinação positiva. Um teste que não pode reprovar não é teste. E o
próprio desenho, em E8 (escrito **antes** de estimar placebos), declara que a inclinação pós
de 2022 é **"não estimável com 4 pontos"**. Aplicar a P1 um coeficiente que o pré-registro já
declarou não estimável não é seguir a regra; é violar E8. Só pelo ramo b2, zero controles
replicam e P1 "passa".

**A favor de "indeterminado".** Mesmo restringindo a b2, o que P1 compararia é a soma sobre
um retângulo com mina contra somas sobre retângulos sem mina. A divergência de sinal em b2
some quando a geometria é a cidade (ADM2: +0,7 %). P1 não está medindo "Tete vs. controles";
está medindo "mina de Moatize vs. cinco cidades". O teste está mal-posto em geometria, e um
teste mal-posto não passa nem falha.

**Conclusão: "não estimável — motivo", que é veredito admissível por §4.5, e não "FALHA" nem
"passa".** Motivo em uma linha: *o ramo b3 é vazio por E8 e o ramo b2 compara geometrias não
comparáveis sem a decomposição de §2.3*. "FALHA" está errado (o teste não reprovou Tete;
reprovou a si mesmo). "Passa" está errado (P1 pelo ramo b2 passaria por um artefato de
recorte). Registrar "FALHA" no artigo levaria o leitor a crer que os controles replicaram a
queda de Tete, o que é o oposto do que os dados mostram.

## 2. O defeito é genuíno? É do critério ou da aplicação?

**Genuíno, e é do critério — mas já estava coberto por uma cláusula pré-registrada que a
aplicação ignorou.** Duas camadas:

- **Critério:** "≥ 50 % da magnitude de Tete" é um teste de razão cujo denominador pode ser
  zero. Quando o coeficiente de referência é indistinguível de zero, a razão é indefinida e
  qualquer valor a satisfaz. É a mesma família de defeito de `docs/ADR/0014` (limiar relativo
  a denominador que colapsa), agora num critério estatístico. O desenho tinha à mão a
  ferramenta que faltou: em P2 (§4.2) o mesmo teste exige "IC95 que exclua zero" — em P1
  (§4.1) não. A assimetria é inexplicada e é a raiz.
- **Aplicação:** §4.1 diz "quebra do mesmo sinal e de magnitude ≥ 50 % da de Tete" sem nomear
  coeficiente. A leitura "b2 OU b3" é uma escolha de implementação (`placebos.py:185`),
  coerente com §4.2, mas **incompatível com E8**, que exclui b3 de 2022 como estimável. A
  aplicação usou um coeficiente que o próprio pré-registro tinha retirado da mesa.

Portanto: defeito de critério (denominador nulo) + erro de aplicação (ignorar E8). Nenhum dos
dois é "leitura do orquestrador": a leitura está correta.

## 3. Um conserto agora é lícito?

**Regra geral: não.** Corrigir o critério depois de ver que reprova o resultado atraente é a
definição de especificação procurada, independentemente de a correção ser "óbvia".

**Condições que tornariam uma emenda defensável, e se estão presentes:**

| Condição | Presente? |
|---|---|
| (a) A correção deriva de uma cláusula **já pré-registrada** antes do resultado, não de uma ideia nova | **Sim** para o ramo b3: E8 (2022: inclinação pós não estimável) antecede a estimação dos placebos. Aplicá-lo é cumprir o pré-registro, não emendá-lo |
| (b) A correção é **neutra quanto ao resultado**: aplicada a todas as quebras, não só à que incomoda | Aplicando "ramo só sobre coeficiente estimável e com IC que exclua zero" a 2005, 2011, 2016 e 2022: 2005 (1 replica) continua "passa"; 2011 (Tete b2 IC inclui zero; b3 exclui) — cai a 3 replicas em b3 (Chimoio, Lichinga, Xai-Xai), continua FALHA; 2016 continua FALHA (5 em b2); 2022 vai a 0 em b2. **Neutra em três de quatro; muda só a que degenera** |
| (c) A emenda é **datada, declara que o autor viu o dado**, e mantém o veredito original legível ao lado | Exigido por §10; fácil de cumprir |
| (d) A emenda **não produz resultado causal publicável** que antes não existia | **Sim**: F3 e F4 já disparam para B_luz_HARM 2022 (RMSPE pré > ½ DP; sintético = Inhambane com peso 1,0); DiD −0,12 com IC [−0,276; +0,035]; p de permutação 0,333. O contrafactual de 2022 está "NÃO SUSTENTADO" por critérios que não dependem de P1. Um P1 "passa" não reabilita nada |

**Veredito sobre licitude:** aplicar E8 ao ramo b3 é lícito porque não é emenda — é execução
de cláusula anterior. **Acrescentar** "IC que exclua zero" a P1 (espelhando P2) é emenda
genuína: lícita só como **emenda datada, declarada pós-dado, aplicada às quatro quebras, com
os dois vereditos (original e emendado) publicados lado a lado** e com a demonstração (b)
de que só altera a quebra degenerada. Recomendo fazê-la assim, e nunca substituindo o
veredito original no CSV: coluna nova `veredito_emenda2`, não sobrescrita.

O que **não** é lícito: reformular P1 para "b2 apenas" porque em 2022 b2 dá o resultado
atraente. Isso escolhe o coeficiente pelo resultado.

## 4. A divergência de sinal em 2022 é substantiva ou artefato?

Argumento por explicação alternativa, em ordem de força:

1. **Geometria (E6) — explica a queda de Tete quase por inteiro.** A queda está fora do ADM2
   (−13,6 %) e ausente dentro (+0,7 %). Sem a decomposição de §2.3, o que se pode dizer é que
   a luz da parte não-urbana do retângulo (mina, Moatize, corredor) caiu em 2022. Isso é
   coerente com a transição Vale→Vulcan (venda concluída abr/2022) e pode ser resultado — mas
   é resultado **sobre a pegada minerária**, não sobre "Tete". Como afirmação sobre a cidade,
   é **artefato de recorte**.
2. **Aceleração comum dos controles a partir de 2021** — explica o b2 positivo deles. Cinco
   capitais a centenas de km acelerando em uníssono de ~0 para 10–25 %/ano é choque nacional
   (expansão da rede EDM, pós-Covid) ou comportamento do produto V2 nos anos de extensão
   (2023–2025 são anos recentes do V10). Tete também acelera em 2023 (+14,4 %). A "divergência
   de sinal" é em boa parte "Tete já crescia a 7 %/ano e não acelerou; os outros partiram do
   zero e aceleraram".
3. **Costura DMSP→VIIRS (E4)** — fora da janela; **não** explica 2022. Concordo com E5.
4. **Queda do máximo (E5)** — o argumento "soma sobe com máximo caindo = dispersão" é correto
   para 2023–2025, mas em **2022** a soma **e** o máximo caem juntos (−6,2 % e 63,7→49,9). Em
   2022 especificamente, E5 não separa produto de economia; separa só a partir de 2023. E o
   pixel máximo estar fora do ADM2 reforça que é a planta.
5. **P2 (2019)** passou por 2 pontos percentuais: b2 do placebo = −0,087, 48 % do real, com IC
   que exclui zero e b3 = −0,054 também significativo. O modelo segmentado encontra "quebra"
   negativa em 2019 quase tão grande quanto a de 2022. A datação é frágil.
6. **p mínimo 1/6.** Rank 2 de 6, p = 0,333. Nada aqui atinge significância por permutação, e
   HAC com T = 13 sub-cobre (§2.2.4).

**Conclusão:** como afirmação "Tete diverge dos controles em 2022", **não há resultado
defensável**. O que sobrevive é descritivo e mais estreito: (i) a luz na parte do retângulo
fora da cidade de Tete caiu ~14 % em 2022 e não recuperou o ritmo anterior (2025 ≈ 2023);
(ii) a luz da cidade (ADM2) não caiu em 2022 e cresceu 37 % em 2021–2025, abaixo dos controles
(40–61 %). (i) só vira afirmação sobre a mina depois da decomposição de §2.3. (ii) é comparação
bilateral sem contrafactual sustentado (F3, F4).

## 5. ADR?

**Sim — um ADR, decidindo quatro coisas:**

1. **Regra geral de critérios relativos:** nenhum teste "≥ x % da magnitude de referência" é
   aplicado a coeficiente cujo IC95 inclua zero ou que o desenho declare não estimável; nesse
   caso o ramo é "vazio" e o veredito, se todos os ramos forem vazios, é "não estimável".
   Aplicado retroativamente a P1 e P2 nas quatro quebras, com os dois vereditos publicados.
2. **P1-2022: veredito reclassificado de "FALHA" para "não estimável — ramo b3 vazio (E8);
   ramo b2 sem decomposição de §2.3"**, com o "FALHA" original mantido em coluna própria.
3. **A decomposição de luz de §2.3 é pré-requisito** de qualquer frase sobre 2022, e sua
   ausência é registrada como etapa não executada (não "não estimável": a pegada existe em
   ADR 0011/0014). Até ela existir, a quebra de 2022 é publicada só com a série ADM2 ao lado.
4. **Sétima ocorrência do padrão "denominador que colapsa"** (ADR 0014 lista seis), primeira
   num critério estatístico — registrada como lição, com a assimetria P1/P2 como causa.

O ADR **não** decide que 2022 é resultado. Decide que o teste estava mal-posto e que a
afirmação sobre a cidade não sobrevive à sensibilidade de geometria já publicada.

## Custo

Fase 3, camada `03_causal`: (a) coluna `veredito_emenda2` em `placebos.py` (< 1 h);
(b) decomposição de §2.3 — soma de radiância por máscara `industrial`/`urbano`/resto, 13 anos
× 3 recortes, com a pegada de ADR 0011/0014 reamostrada a ~500 m (1 sessão); (c) ADR (< 1 h).
Nada volta à Fase 1 ou 2.


---

<!-- fonte: data/provenance_parts/causal_fase3.md -->

# Fase 3 — Proveniência de §5.4 (causal), §5.5/§5.6.7 (cenários) e §5.6.4 (logit)

Autor: subagente `desenho-causal`. Data: 2026-09-08.
Documento vinculante: `docs/DESENHO_FASE3.md` (pré-registro de 2026-09-08) **mais a
EMENDA 1 (§11 do mesmo arquivo, datada 2026-09-08)**. A emenda foi escrita **depois** de
ver a série de luzes e antes de qualquer estimação; a declaração exigida pelo §10 do
pré-registro está no cabeçalho da emenda. Nenhuma afirmação de §0–§9 foi reescrita: as
afetadas estão marcadas em linha com `⟨EMENDADO 2026-09-08 · E#⟩`.

## 1. Fontes usadas nesta fase

| Série | Fonte | Nível | Selo | Papel |
|---|---|---|---|---|
| `S_HARM_soma` | **Chen, Z., Yu, B. et al. (2021)**, *ESSD* 13:889–906, DOI `10.5194/essd-13-889-2021`; dataset Harvard Dataverse `10.7910/DVN/YGIVCD` (CC0) | A | observado | quebras de 2016 e 2022 |
| `S_WSF_taxa` | DLR World Settlement Footprint Evolution, 30 m, 1985–2015 | A | observado | quebras de 2005 e 2011 |
| geometria | HDX COD-AB ADM2 (cruzamento por nome + província, nunca por P-code) | A | observado | unidades |
| população-base dos cenários | HDX COD-PS ADM2, vintage 2017 (observado) e 2025 (projeção do INE) | A | 2017 observado / 2025 **modelado** | §5.5 |
| várzea e `urbano_2025` | classificação própria (§5.1) + HAND | A | observado, **com catraca R2** | zona de proteção |

**Aviso de nomenclatura, deliberado.** Os arquivos em `data/raw/` têm prefixo
`viirs_like_li2020_v2_*`. É **herança de erro** de uma delegação anterior: o produto é o de
Chen/Yu, **não** o de Li et al. 2020 (`10.1038/s41597-020-0510-y`), que é um harmonizado
distinto. `data/raw/` não foi editado por este subagente; os `.meta.json` já trazem a
citação correta. Nenhuma saída desta fase cita Li et al. 2020.

## 2. O que a emenda mudou, em uma linha cada

- **E1** — os pré-requisitos (i) luzes e (ii) tiles WSF dos controles foram satisfeitos; **(iii) a série anual de NDVI de paisagem não foi construída**, e por isso P4 continua descritivo.
- **E2** — `S_HARM` sobe de nível B ("só validação") para **A** e vira a série primária de luz.
- **E3** — a premissa 4 (conciliar DMSP↔VIIRS por sobreposição própria) tornou-se **impossível**: VNL rebaixado a B, DMSP excluído em C. A conciliação existe, mas é interna ao produtor e **não auditável por este pipeline**.
- **E4** — **achado novo:** a costura DMSP→VIIRS é visível no dado (as seis áreas colapsam em `n>0` em 2012–2013 e todas se recuperam). Janela homogênea das luzes = **2013–2025**; pré-janela de 2016 cai de 4 para **3** pontos; 2011–2012 não servem de base pré-tratamento; **2005 e 2011 perdem qualquer corroboração de luz**.
- **E5** — a ressalva sobre 2022 **enfraquece e é reclassificada, não apagada**: a soma sobe em 2023–2025 enquanto o máximo cai, o que é dispersão da luz e não reescalonamento do produto. Continua obrigatória em toda figura da quebra de 2022, como "quebra de produto não descartada, com evidência direcional contra ela".
- **E6** — a regra de geometria por polígono ADM2 **não é executável**: os recortes espelhados são retângulos e cobrem 0,182 (Lichinga) a 1,000 (Chimoio) do ADM2 respectivo. A geometria primária passa a ser o **recorte fixo**, e ADM2 ∩ recorte vira sensibilidade, sempre com a fração de cobertura ao lado.
- **E7** — nada é afrouxado: F1–F7 como escritos, piso de p = 1/6, §8 inteiro, H4/H5/H6 rebaixadas.

## 3. Determinismo

`config/seeds.yaml`: controle sintético `13579` (20 partidas SLSQP determinísticas, a
primeira uniforme e 19 de uma Dirichlet semeada); wild cluster bootstrap `97531`, 1000
reamostragens; `logit_espacial.seed: 24680` **reservada e não usada** (§5.6.4 bloqueado).
Nenhuma etapa depende de estado de sessão; ordem no alvo `causal` do Makefile.

## 4. Aviso obrigatório sobre a inferência

Com `T ≤ 23` (WSF) e `T = 13` (luzes), o HAC **sub-cobre**: os IC publicados são **piso**
de incerteza, não teto. Com 1 tratado e 5 doadores o **p mínimo por permutação é 1/6 ≈
0,167** — nenhum resultado desta fase atinge significância convencional, e isso é aritmética
do pool, não fraqueza do efeito. Qualquer `p < 0,05` que apareça vem de inferência
assintótica sobre 6 clusters e está marcado como não confiável.

## 5. Causalidade reversa luz ↔ população

Declarada e **não resolvida**. Não há instrumento nesta AOI. O desenho proibiu resolver por
defasagem ou por VAR/Granger com esta amostra, e a proibição foi respeitada: as
elasticidades são reportadas como **associação por fase**, com a contagem de pontos na mesma
célula.

## 6. Extrapolação do GHSL

Nenhuma época GHSL 2025/2030 foi usada como âncora, série ou insumo de cenário. Os cenários
partem de COD-PS 2025 (projeção do INE, marcada `modelado`) e da classificação própria de
2025, não do GHSL.


---

<!-- fonte: data/provenance_parts/causal_fase3_adr0015.md -->

# Fase 3 — Proveniência da execução do ADR 0015 (Emenda 2 do desenho)

Autor: subagente `desenho-causal` (§5.4, §5.5, §5.6.4, §5.6.7). Data: **2026-09-08**.
Documento vinculante: `docs/ADR/0015` e `docs/DESENHO_FASE3.md` **§12 (EMENDA 2)**.
Antecedentes: `data/provenance_parts/arbitragem_p1_2022.md` (parecer do
`revisor-adversarial`), `ORCHESTRATION_LOG.md` 3-10 e 3-11.
Complementa — não substitui — `data/provenance_parts/causal_fase3.md`.

**Natureza da emenda, declarada de saída:** é **pós-dado**. Foi motivada por contestação
do orquestrador ao veredito de P1 em 2022, arbitrada pelo `revisor-adversarial`, e a
arbitragem deu **contra quem contestou**: a queda de 2022 não está na Cidade de Tete
(2021→2022: cidade **+0,7 %**, resto do retângulo **−12,7 %**; 2021→2025: cidade
**+45,0 %**, resto **−2,5 %**). A emenda é lícita porque **não reabilita nada** — ver §4.

---

## 1. O que mudou no código

| Arquivo | Mudança |
|---|---|
| `pipeline/03_causal/placebos.py` | regra do **ramo vazio** (ADR 0015 §1) aplicada a **P1 e P2**; P1 passa a exigir IC próprio que exclua zero, como P2 sempre exigiu; colunas novas `veredito_pre_adr0015`, `mudanca_apos_adr0015`, `ramo_b2_estado`, `ramo_b3_estado`, `b2_real_ic95_inf/sup`, `b3_real_ic95_inf/sup` |
| `pipeline/03_causal/veredito_fase3.py` | propaga `veredito_pre_adr0015` e `mudanca_apos_adr0015` para `veredito_fase3.csv` |
| `pipeline/03_causal/decomposicao_luz.py` | **novo** — decomposição de §2.3, registrada como etapa não executada em ADR 0015 decisão 4 |
| `Makefile` | `decomposicao_luz.py` entra no alvo `causal`, antes de `placebos.py` |
| `docs/DESENHO_FASE3.md` | **§12, EMENDA 2** (E10, E11, E12) + três marcas `⟨EMENDADO · E10/E11⟩` em §2.3, §4.1 e §4.2 |

**Nada foi sobrescrito.** O veredito pré-ADR 0015 fica em coluna própria de
`data/processed/causal/placebos.csv` e de `veredito_fase3.csv`, ao lado do novo.

**Determinismo:** nenhum passo novo é estocástico. `config/seeds.yaml` continua sendo a
única fonte de seeds da fase e não foi alterado; `decomposicao_luz.py` não consome seed
porque não sorteia — declarado no cabeçalho do script para que a ausência não seja lida
como omissão.

---

## 2. Placebos sob a regra do ramo vazio — as quatro quebras

Artefato: `data/processed/causal/placebos.csv` (colunas `veredito_pre_adr0015`,
`veredito`, `mudanca_apos_adr0015`, linhas `unidade == AGREGADO`).

| Quebra | Série | P1 pré | **P1 novo** | P2 pré | **P2 novo** |
|---|---|---|---|---|---|
| 2005 | `S_WSF_taxa` | passa (1 replica) | **não estimável** | passa | **não estimável** |
| 2011 | `S_WSF_taxa` | FALHA (4) | **FALHA** (3) | FALHA | **passa** (afrouxamento; ver §3) |
| 2016 | `S_HARM_soma` | FALHA (5) | **FALHA** (4) | não estimável | não estimável |
| 2022 | `S_HARM_soma` | FALHA (5) | **não estimável** | passa | **não estimável** |

Motivo de cada ramo vazio, com o coeficiente de referência de Tete
(`its_quebras.csv`, variante `principal_log_HAC`):

| Quebra | `b2` de Tete (IC95) | `b3` de Tete (IC95) | ramo `b2` | ramo `b3` |
|---|---|---|---|---|
| 2005 | −0,4024 [−1,2374; +0,4327] | +0,0636 [−0,0312; +0,1584] | vazio (IC inclui 0) | vazio (IC inclui 0) |
| 2011 | +0,6129 [−0,0084; +1,2342] | −0,1830 [−0,3126; −0,0534] | vazio (IC inclui 0) | aplicável |
| 2016 | −0,1516 [−0,2148; −0,0885] | −0,1233 [−0,1449; −0,1017] | aplicável | aplicável |
| 2022 | −0,1814 [−0,2586; −0,1042] | +0,0083 [−0,0159; +0,0324] | **vazio por desenho** (ADR 0015 dec. 2/4: geometrias não comparáveis) | **vazio por E8** (inclinação pós não estimável com 4 pontos) + IC inclui 0 |

### Duas divergências em relação ao parecer do revisor

Registradas porque são informação sobre o **parecer**, não só sobre o código.

1. **2005 não "continua passa".** O parecer previa que sim. Pela regra que ele próprio
   propôs, os dois coeficientes de referência de Tete em 2005 incluem zero: **os dois
   ramos ficam vazios** e P1 em 2005 é **não estimável**. Em consequência, a condição (b)
   do parecer — "neutra em três de quatro quebras; muda só a que degenera" — **não se
   verifica**: a regra muda **duas** das quatro quebras em P1 e **três** das quatro em P2.
   A direção continua sendo de enfraquecimento, que é o que mantém a emenda lícita, mas
   a demonstração de neutralidade que o parecer ofereceu não sobrevive à execução.
2. **2016 tem 4 réplicas, não 5.** Quelimane sai: `b2` = −0,0763 com IC
   [−0,1860; +0,0333], que inclui zero, e P1 passa a exigir IC próprio que o exclua.
   Veredito inalterado: **FALHA**.

---

## 3. O único afrouxamento, e por que não é reabilitação

**P2 em 2011 vai de FALHA para "passa".** O ramo que disparava era `b2`, e o `b2` real de
Tete em 2011 (+0,613) tem IC [−0,008; +1,234] que inclui zero: não há efeito de nível a
datar. Não reabilita a quebra de 2011 porque, independentemente de P2:

- **P1 em 2011 continua FALHA** (3 controles replicam em `b3`: Chimoio, Lichinga, Xai-Xai);
- o painel `A_area_WSF|2011` continua **"CONTRAFACTUAL NÃO SUSTENTADO"** em
  `veredito_fase3.csv`, por critérios F que não dependem de placebo;
- o `b2` de 2011 é ele próprio indistinguível de zero.

A linha `mudanca_apos_adr0015` marca o afrouxamento em texto, no CSV, para que ninguém o
leia como resultado.

---

## 4. A emenda não reabilita nada — verificado por execução

`data/processed/causal/veredito_fase3.csv`, bloco `criterio_F`, após reexecução:

| painel | quebra | veredito |
|---|---|---|
| `A_area_WSF` | 2005 | CONTRAFACTUAL NÃO SUSTENTADO |
| `A_area_WSF` | 2011 | CONTRAFACTUAL NÃO SUSTENTADO |
| `B_luz_HARM` | 2016 | CONTRAFACTUAL NÃO SUSTENTADO |
| `B_luz_HARM` | 2022 | CONTRAFACTUAL NÃO SUSTENTADO |

Para 2022 especificamente, F3 e F4 continuam disparando com os mesmos números de antes da
emenda: sintético = **Inhambane com peso 1,000**; DiD **−0,12**, IC95 **[−0,28; +0,03]**,
p de permutação **0,333** (piso do pool = 1/6 = 0,167). **H4 não é reabilitada e H6
continua rebaixada.**

---

## 5. Decomposição de luz de §2.3 — executada, e o que ela permite dizer

Artefatos: `data/processed/causal/decomposicao_luz_por_camada.csv` e
`decomposicao_luz_por_camada.meta.json`. Script: `pipeline/03_causal/decomposicao_luz.py`.

**Insumos.** Luz: Chen/Yu 2021 (`10.5194/essd-13-889-2021`; Dataverse
`10.7910/DVN/YGIVCD`, CC0), 19 anos, recorte fixo `tete_aoi`, ~500 m, EPSG:4326.
Camadas: `industrial_*`, `urbano_*`, `reassentamento_*` a 30 m, EPSG:32736, seis
anos-âncora. **Reconciliação verificada:** a soma total por ano reproduz
`serie_luzes_anual.csv:soma_radiancia` com diferença máxima de **0,0004**.

**Não é uma partição, e este é o ponto principal.** Um pixel de luz cobre ~278 pixels de
camada; a repartição sub-pixel é indeterminada sem premissa sobre como a luz se distribui
dentro do pixel. Publicam-se **duas envoltórias**, nunca uma:

- **piso** — radiância repartida proporcionalmente à **área** de cada classe no pixel
  (premissa: densidade de luz uniforme; subestima classe compacta e brilhante);
- **teto** — pixel inteiro para a classe de maior prioridade presente
  (`industrial > urbano > reassentamento`), com qualquer fração > 0 (superestima).

Razão teto/piso, mediana sobre os anos: **industrial 2,12 · urbano 1,83 ·
reassentamento 5,21**. **Nenhum nível e nenhum share desta tabela é publicável como
número.** Só é afirmável o que tem **o mesmo sinal nas duas envoltórias**.

**Agregação e bordas.** Máscara 0/1 reamostrada para a grade da luz por **média**
(= fração de área da célula), `rasterio.warp.reproject`, `Resampling.average` — a única
agregação que conserva área; vizinho mais próximo perderia a classe, que é sub-pixel.
Efeito de borda: toda fronteira de classe fica difusa em ~500 m, ordem de grandeza da
própria vila de Moatize e maior que vários bairros de Tete. Após a agregação as camadas
**deixam de ser mutuamente exclusivas** no pixel de luz: 22 a 32 pixels contêm duas ou
mais classes (0 em 2000 e 2005). A prioridade do teto resolve isso por convenção, não por
medição.

**Tempo e selo.** As camadas existem só nos seis anos-âncora; a luz é anual. Máscara
categórica não se interpola: usa-se a do **ano-âncora mais próximo** (empate → âncora
anterior), com `distancia_anos_ate_ancora` em coluna. **Selo `observado` apenas quando o
ano da luz é o próprio ano-âncora; `interpolado` em todos os demais.** Toda comparação
plurianual deve ser lida na variante **`mascara_fixa_2020`**, que é invariante à mudança
de máscara e isola variação de luz de variação de classificação.

**Vieses herdados, declarados e não corrigidos** (colunas próprias no CSV):
`urbano` carrega a catraca **R2** (ADR 0013; fração do estoque herdada da união cumulativa
0 / 0 / 3,4 / 6,1 / 12,7 / **18,0 %** em 2000…2025) e a **comissão** de ADR 0009 (acurácia
do usuário de `construido` **0,286–0,625**: entre 37,5 % e 71,4 % do que a máscara chama de
construído não é construído). As duas entram **inteiras** na parcela de luz atribuída a
`urbano`. `industrial` e `reassentamento` não têm R2 (ADR 0014), mas o limiar de
`industrial` foi calibrado contra Maus em 2020 — a concordância de 2020 não é validação
independente.

### 5.1 O que a decomposição sustenta (máscara fixa de 2020; sinal igual nas duas envoltórias)

| Afirmação | piso | teto |
|---|---|---|
| 2021→2022, luz na pegada `industrial` **cai** | −15,3 % | −9,8 % |
| 2021→2022, luz em `urbano` fica **plana** (sinal ambíguo) | +2,8 % | −1,7 % |
| 2021→2025, luz em `urbano` **cresce** | +34,7 % | +32,4 % |
| 2021→2025, luz na pegada `industrial` **não recupera** | −13,9 % | −4,3 % |

### 5.2 O que ela NÃO sustenta — a restrição que importa

Contribuição de cada classe para a queda total de **−6,04 %** entre 2021 e 2022, em pontos
percentuais do total de 2021:

| classe | piso | teto |
|---|---|---|
| `industrial` | −1,94 pp | −2,54 pp |
| `urbano` | +0,77 pp | −0,89 pp |
| `reassentamento` | +0,01 pp | +0,04 pp |
| **`resto`** (sem camada classificada) | **−4,87 pp** | **−2,64 pp** |

A pegada `industrial` responde por **32 % a 42 %** da queda. O maior contribuinte isolado,
sob as duas envoltórias, está **fora** de tudo o que o pipeline classificou. Portanto, pela
decisão 4 do ADR 0015, **não é autorizada** a frase "a luz da mina caiu em 2022 e explica a
queda". O que é autorizado: *"a luz na pegada industrial caiu entre 10 % e 15 % em 2022 e
não recuperou até 2025; ela responde por cerca de um terço a dois quintos da queda do
retângulo, e o restante está em área não classificada"*.

### 5.3 Alerta de série, novo e não previsto em nenhuma emenda anterior

Entre 2013 e 2025 o crescimento do total (**+123 %**) é dominado por `resto`
(**+171 %** piso / **+427 %** teto), isto é, por pixels fora das camadas classificadas.
Compatível com (a) dispersão espacial da luz — a leitura de E5 —, (b) assentamento novo não
captado pela máscara de 2020 e (c) comportamento do produto Chen/Yu nos anos de extensão.
**As três não se separam com o conjunto A disponível.** Qualquer leitura da série de luz
como "atividade econômica da cidade" carrega esta linha junto.

---

## 6. Premissas frágeis desta execução

1. **Repartição sub-pixel indeterminada.** Teto/piso ≈ 2 em `industrial` e `urbano`, ≈ 5 em
   `reassentamento`. Nenhum nível é publicável; só sinal comum às duas envoltórias.
2. **Máscara interpolada.** Fora dos seis âncoras, a classificação é de outro ano (até 3
   anos de distância). Nenhuma quebra anual pode ser lida na decomposição.
3. **`urbano` = catraca R2 + comissão 0,286–0,625.** A parcela de luz de `urbano` cresce em
   parte por construção da regra de permanência, não por acender luz.
4. **`resto` domina.** Mais de metade da radiância, e o maior contribuinte tanto da queda
   de 2022 quanto do crescimento de 2013–2025, está fora das camadas.
5. **Geometria do recorte.** O retângulo `tete_aoi` (2.494 km²) contém a mina; os recortes
   de controle (~1.000–1.090 km²) não. A decomposição atenua, mas não elimina, o problema
   que reprovou a leitura de 2022 — porque a atenuação depende de `industrial` capturar a
   pegada, e ela cobre 76 % dos polígonos de Maus em 2025 e menos antes disso.
6. **Prioridade do teto é convenção.** `industrial > urbano > reassentamento` foi escolhida
   pela ordem de §2.3, não medida. Afeta 22–32 pixels por ano-âncora.
7. **Radiância negativa zerada** como ruído do produto, sem correção de viés — decisão de
   uma linha, declarada aqui porque não está em nenhuma emenda anterior.
8. **O afrouxamento de P2-2011** é consequência mecânica da regra, não achado. Lido
   isoladamente, faria 2011 parecer mais sólido; lido com P1-2011 (FALHA) e com o critério
   F (não sustentado), não faz.


---

<!-- fonte: data/provenance_parts/construida.md -->

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


---

<!-- fonte: data/provenance_parts/construida_fase1.md -->

# Proveniência — Fase 1: WSF Evolution (fragmento novo, complementa construida.md)

`construida.md` está fechado (Fase 0'). Este fragmento cobre exclusivamente o
WSF Evolution (DLR), que passou a caminho crítico pelo ADR 0003.

## Fonte

- **Produto:** World Settlement Footprint (WSF) Evolution — Landsat-5/-7 — Global.
- **Página do produtor:** https://geoservice.dlr.de/web/datasets/wsf_evo (verificada
  2026-09-07, HTTP 200).
- **Portal de download:** https://download.geoservice.dlr.de/WSF_EVO/ — acesso anônimo
  confirmado (sem login/cadastro, HTTP 200).
- **Índice de tiles** (não documentado publicamente; localizado por engenharia reversa
  do `mainScript.js` do portal): https://download.geoservice.dlr.de/WSF_EVO/grid.geojson
  — GeoJSON com 5138 features globais, grade de 2°x2°, cada feature trazendo
  `properties.Download` (URL do `.tif`), `.filename`, `.md5sum`, `.filesize`, `.id`
  (`"<lon0>_<lat0>"`, canto SW).
- **Tiles que cobrem a AOI** (`config/study.yaml`, bbox 33.50–34.10 E / -16.35–-16.00 S):
  id do produtor `"32_-18"` e `"34_-18"` — derivados via `tile_sw_corners(aoi, 2.0)`,
  nunca fixados no código. Gravados como `data/raw/wsf_evolution_S18E032.tif` e
  `wsf_evolution_S18E034.tif` (convenção hemisférica, para compatibilizar com o
  contrato de cobertura de AOI que agrupa tiles pelo prefixo antes de `_S`/`_N`).
- **Resolução:** 30 m (confirmado por rasterio: `res = 0.0002695°` ≈ 30 m).
- **Anos cobertos:** 1985–2015, anual. Valor de pixel = **ano estimado de primeira
  detecção do assentamento**; 0 = sem dado — confirmado na aba "Abstract" da página do
  produtor, não presumido; confirmado também empiricamente por rasterio: valores únicos
  no intervalo [0, 2015] em ambos os tiles.
- **Selo:** `observado` (máscara classificada a partir de Landsat-5/7, não modelo).
- **Licença:** CC BY 4.0 — texto em https://creativecommons.org/licenses/by/4.0/,
  declarado na aba "License" da página de download (bloco
  `dcat-ap.de/def/licenses/cc-by/4.0`). Aviso adicional do produtor: "DLR not liable for
  damage resulting from use" (isenção de responsabilidade, não restringe uso/redistribuição).
- **Citação exigida:** Marconcini, M., Metz-Marconcini, A., Esch, T., Gorelick, N. (2021).
  "Understanding Current Trends in Global Urbanisation - The World Settlement Footprint
  Suite." GI_Forum 2021, Issue 1, p. 33-38. DOI: 10.1553/giscience2021_01_s33.
- **Nível:** A (licença localizável no site do produtor, acesso anônimo, uso e
  redistribuição permitidos sob CC BY 4.0). Confirma o pressuposto do ADR 0003.

## Arquivos baixados

| Arquivo | id do produtor | Data de acesso | Tamanho (bytes) | MD5 confere |
|---|---|---|---|---|
| data/raw/wsf_evolution_S18E032.tif | 32_-18 | 2026-09-07T23:34:23Z | 1.554.597 | sim (84daed72425b41fd4250ac6449aeabfe) |
| data/raw/wsf_evolution_S18E034.tif | 34_-18 | 2026-09-07T23:34:25Z | 1.953.451 | sim (c35bf468b65b86de3074e6888c6f7e41) |

## Verificação com rasterio

- CRS: EPSG:4326 (ambos os tiles).
- Bounds (união): 31,9898°E–36,0101°E / -18,0101°S–-15,9899°S — cobre a AOI inteira
  (33,50–34,10 E / -16,35–-16,00 S) com folga.
- Resolução: 0,00026949458523585647° por pixel ≈ 30 m no equador (compatível com o
  30 m declarado).
- Shape: 7496×7497 pixels por tile.
- Valores de pixel: inteiros em [0, 2015]. Tile S18E032 tem 32 valores distintos, tile
  S18E034 tem 30 — consistente com "ano de detecção, 0 = sem dado" (não um valor
  contínuo nem uma máscara binária).
- Cobertura da AOI: **confirmada** — os dois tiles juntos cobrem o bbox inteiro da AOI;
  nenhum canto da AOI fica fora de ambos.

## Notas

- `data/interim/wsf_evo_grid.geojson` é apenas um índice de URLs (cache do grid do
  produtor), não um espelho de dado nível A: não recebe `.sha256`/`.meta.json` porque
  não é ele próprio um artefato citável — é reconstituível a qualquer momento a partir de
  `GRID_URL` em `pipeline/00_fetch/fetch_wsf_evolution.py`.
- O portal DLR retorna URLs de download com barra dupla (`.../files//WSFevolution_...tif`);
  isso é do próprio produtor, mantido como está (funciona, resolvido pelo servidor).
- Ambiente de execução: o host `download.geoservice.dlr.de` encadeia até a
  HARICA TLS RSA Root CA 2021, ausente do cafile default do OpenSSL usado pelo
  interpretador Python deste ambiente (embora presente no bundle do `certifi`). O
  script usa `certifi.where()` como cafile quando disponível — sem isso o handshake
  TLS falhava com "self-signed certificate in certificate chain" mesmo a fonte sendo
  legítima. Registrado aqui para não ser confundido com problema da fonte.


---

<!-- fonte: data/provenance_parts/demografia_dashboard.md -->

<!-- SECAO_DEMOGRAFIA_DASHBOARD_INICIO -->
## Dashboard de população 1997-2025 (§5.3, Frente A)

Script: `pipeline/02_metrics/demografia_dashboard.py`.
Gerado em 2026-09-09.

Produz `data/processed/demografia_serie_1997_2025.csv`: uma linha por unidade
× ano de população, mais linhas `cagr_<a>_<b>` e `indice_base_<ano>` por
unidade. **Não entra em `stats_by_year_by_unit.csv`** — grava direto em
`data/processed/`, fora do circuito de fragmentos/consolidador; carrega nível
A, B, C e `ausente` lado a lado, cada linha com o seu.

Unidades: Cidade de Tete, Distrito de Moatize (reaproveitados de
`reconstrucao_demografica.montar_nucleo()`/`montar_contexto_b_c()`, sem
retranscrição), Província de Tete e Moçambique (soma dos ADM2 do HDX
COD-PS por nome de província 2017/2025; parse programático do HTML do
Censo 2007 do INE para 2007), e Vila de Moatize — um único ponto (2017,
`selo=modelado`, `nivel_fonte=A` mas fonte GRID3, não HDX COD-PS: estimativa
dasimétrica de terceiros, reaproveitada de
`populacao_vila_moatize.estimar()`, nunca contagem; sem CAGR — um ponto não
faz taxa; piso/teto e o desvio da validação cruzada em Cidade de Tete vão na
`nota`. Ver `data/processed/populacao_vila_moatize_sensibilidade.csv` e
`data/provenance_parts/populacao_vila_moatize.md`.

### Somas verificadas nesta execução

| unidade | 2017 (soma COD-PS) | 2025 (soma COD-PS) |
|---|---|---|
| Província de Tete | 2551824 | 3432961 |
| Moçambique | 26899102 | 35163992 |

Soma provincial 2017 confere com a "população residente" publicada pelo INE
(2.551.826) dentro de ±5 (diferença observada:
-2). Soma nacional 2017 diverge da
"população residente" publicada pelo INE (26.899.105) em
+3 pessoas — divergência esperada e
documentada em cada linha nacional do CSV (decisão do usuário de 2026-09-09:
usar a soma do COD-PS, não o total do INE, como base nacional).

### Regras de selo/nível aplicadas

População: 2017 observado/A; 2025 modelado/A; 1997/2007 observado com
nível B, C ou `ausente` conforme a fonte disponível para a unidade. Toda
linha `cagr_*`/`indice_base_*` carrega `nivel_fonte` = pior nível das duas
pontas e `selo` = **pior selo das duas pontas** (`_pior_selo`: `modelado` se
qualquer ponta for `modelado`; `interpolado` se nenhuma for `modelado` mas
alguma for `interpolado`; `observado` só se as duas forem). Não é uma regra
em função do ANO: a primeira versão desta regra dizia `selo = modelado`
sempre que uma ponta fosse 2025, e coincidia com o executado enquanto a
única origem de valor modelado fosse a projeção do INE para 2025 — errou no
primeiro caso em que não era, a Vila de Moatize (2017, `selo=modelado` por
ser estimativa dasimétrica sobre GRID3, não por ser 2025), cujo índice teria
saído `observado` pela regra por ano.

<!-- SECAO_DEMOGRAFIA_DASHBOARD_FIM -->


---

<!-- fonte: data/provenance_parts/demografia_fase2.md -->

<!-- SECAO_DEMOGRAFIA_FASE2_INICIO -->
## Reconstrução demográfica e domiciliar (§5.3, Fase 2)

Script: `pipeline/02_metrics/reconstrucao_demografica.py`.
Gerado em 2026-09-09.

### Núcleo A — o que existe

| unidade | ano | selo | nível | fonte |
|---|---|---|---|---|
| Cidade de Tete | 2017 | observado | A | HDX COD-PS 2017 (INE IV RGPH via reprocessador) |
| Cidade de Tete | 2025 | modelado | A | HDX COD-PS 2025 (projeção do INE) |
| Distrito de Moatize | 2017 | observado | A | HDX COD-PS 2017 |
| Distrito de Moatize | 2025 | modelado | A | HDX COD-PS 2025 |

Dois pontos por unidade (um observado, um modelado) **não constituem série de
tendência** — não há interpolação entre eles no núcleo. CAGR 2017-2025
calculado e publicado com selo `modelado` e nota de risco de circularidade
para H4.

### Fora do núcleo — contexto rotulado (nível B/C)

`data/processed/demografia_contexto_nao_nucleo.csv`: Cidade de Tete 1997
(101.984, nível B, UNSD Demographic Yearbook); Distrito de Moatize 1997 (não
recuperado em A nem B); Cidade de Tete e Distrito de Moatize 2007 (155.870 e
215.092, nível C, documento do INE via Wayback sem licença localizável).
Nenhum desses quatro pontos sustenta número publicado no núcleo (§4.0 regra 1;
§10).

### Dasimetria 2017 (Cidade de Tete apenas)

`307338` habitantes distribuídos pela mancha construída própria
(urbano ∪ reassentamento, média 2015/2020), com teste de sensibilidade contra
GHSL BUILT-S e WSF Evolution como pesos alternativos —
`data/processed/populacao_dasimetrica_sensibilidade.csv`. Selo `modelado`.
Raster: `data/processed/imagery/populacao_dasimetrica_tete_2017_30m_32736.tif`.

**Distrito de Moatize não foi dasimetrizado**: o total (260.843 em 2017) é do
distrito inteiro (8.427 km², COD-AB), muito além da mancha construída mapeada
na AOI; distribuí-lo sobre essa mancha implicaria que toda a população rural
do distrito mora dentro do núcleo urbano — falso por construção. Precisaria de
total ao nível de posto administrativo (ADM3), que o COD-PS não publica.

### Domicílios (§5.3)

Não construído nesta rodada. Ver `docs/ADR/0010-domicilios-sem-fonte-a.md`:
o tamanho médio do domicílio para Tete/Moatize não tem fonte de nível A nem B
confirmada (tabulação do INE não localizada como pública; catálogo mozdata
carrega via JS e não expõe a tabulação diretamente) — qualquer produto
"edificações × tamanho médio do domicílio" herdaria nível C do denominador,
o que a política de dados abertos proíbe de sustentar número publicado.
Google Open Buildings/Microsoft Footprints (nível A, listados em
`data/LICENSES.md`) não foram baixados: buscá-los agora seria custo sem
retorno enquanto o denominador continuar sem fonte A.

### Projeções 2027-2040 (§5.3)

Não construídas. Com dois pontos (2017 observado, 2025 já modelado pelo INE),
qualquer extrapolação própria projetaria sobre uma premissa de crescimento
geométrico já embutida no ponto de 2025 — "compor premissas invisíveis",
exatamente o risco que o enunciado da tarefa aponta. O que resolveria isso é
o Censo 2027 (ainda não publicado) ou uma projeção com metodologia própria
declarada (cohort-component, migração líquida como parâmetro de cenário) a
partir de 2017 apenas — não implementada nesta rodada por não ter sido
solicitada como tal e por depender de parâmetros de fecundidade/mortalidade/
migração que este script não tem em nível A.

### Suficiência para §1

- **Pergunta 1 (linha de base 1997-2005, H1 em população):** não respondível
  em nível A — 1997 não tem fonte A/B verificável para nenhuma das duas
  unidades com valor íntegro (Tete tem só B; Moatize nem isso). H1 já foi
  reformulada por área construída (`docs/ADR/0003`), que é a via respondível.
- **Pergunta 2 (implantação/boom 2005-2015):** não respondível diretamente em
  população de nível A — não há âncora demográfica A entre 2007 (nível C) e
  2017. Só a série de área construída (§5.1/§5.2) cobre esse intervalo em A.
- **Pergunta 6 (bust/transição 2015-2025):** parcialmente respondível. Há dois
  pontos A (2017 observado, 2025 modelado), mas o ponto de 2025 é projeção
  institucional, não recontagem — não pode sozinho provar desaceleração/
  estagnação/reconversão sem o risco de circularidade já registrado para H4.
  Cruzar com luzes noturnas e área construída (outras famílias) é necessário
  para qualquer conclusão de P6, não substituível por este produto isolado.

<!-- SECAO_DEMOGRAFIA_FASE2_FIM -->


---

<!-- fonte: data/provenance_parts/demograficas.md -->

# PROVENANCE — Fontes Demográficas e Domiciliares

Tentativa 4. Rastreabilidade de arquivos efetivamente baixados para `data/raw/`.
Última atualização: 2026-09-07 (esqueleto).

## Arquivos baixados

| # | Arquivo local | URL (snapshot/original) | Data de acesso | Licença | Nível | Resolução/nível geográfico | Anos cobertos | Status |
|---|---|---|---|---|---|---|---|---|
| 1 | data/raw/censo2007-tete-quadro3-populacao-por-idade-distrito-2007.html | https://web.archive.org/web/20100809032728id_/http://www.ine.gov.mz/censo2007/rdcenso09/Tete/c0705q3 | 2026-09-07 | pendente_auditoria (INE, primário via Wayback; sem texto de licença localizado) | pendente_auditoria | distrito/cidade, Província de Tete | 2007 | OK |
| 2 | data/raw/quadro-3-populacao-por-idade-segundo-area-de-residencia-distrito-e-sexo-provincia-de-tete-2017.xlsx | https://web.archive.org/web/20191114015524id_/http://www.ine.gov.mz/iv-rgph-2017/tete/quadro-3-populacao-por-idade-segundo-area-de-residencia-distrito-e-sexo-provincia-de-tete-2017.xlsx | 2026-09-07 | pendente_auditoria (INE, primário via Wayback; sem texto de licença localizado) | pendente_auditoria | distrito/cidade, Província de Tete | 2017 | OK |
| 3 | data/raw/censo-2017-brochura-dos-resultados-definitivos-do-iv-rgph-nacional.pdf | https://web.archive.org/web/20190501151428id_/http://www.ine.gov.mz/iv-rgph-2017/mocambique/censo-2017-brochura-dos-resultados-definitivos-do-iv-rgph-nacional.pdf | 2026-09-07 | pendente_auditoria (INE, primário via Wayback; sem texto de licença localizado) | pendente_auditoria | nacional/provincial | 2017 | OK |
| 4 | data/raw/hdx_cod-ab-moz_admin_boundaries.xlsx | https://data.humdata.org/dataset/5e8d83a5-1210-49be-b7d9-cf286dbc15df/resource/47ea3adb-8370-4aba-9f0f-bed6087199de/download/moz_admin_boundaries.xlsx | 2026-09-07 | CC BY-IGO (https://creativecommons.org/licenses/by/3.0/igo/legalcode) | A | admin0-4 (país/província/distrito/posto/localidade) | limites válidos a partir de 2017-01-01 (dataset v02, revisado 2026-03-10) | OK |

## Âncoras de §8 — verificação contra fonte primária

| Unidade | Ano | Valor em §8 | Valor lido em fonte primária | URL do snapshot | Quadro/página | Veredito |
|---|---|---|---|---|---|---|
| Cidade de Tete | 1997 | 101.984 | não disponível | — | — | NÃO LOCALIZADO EM FONTE PRIMÁRIA |
| Cidade de Tete | 2007 | 155.870 | 155.870 | https://web.archive.org/web/20100809032728id_/http://www.ine.gov.mz/censo2007/rdcenso09/Tete/c0705q3 | Quadro 3 (III RGPH 2007, Tete) | CONFIRMADO |
| Cidade de Tete | 2017 | 305.722 ou 307.338 | 307.338 (305.722 não consta deste quadro) | https://web.archive.org/web/20191114015524id_/http://www.ine.gov.mz/iv-rgph-2017/tete/quadro-3-... .xlsx | Quadro 3 (IV RGPH 2017, Tete) | DIVERGENTE PARCIAL — 307.338 confirmado; 305.722 não localizado em fonte primária |
| Distrito de Moatize | 1997 | 109.103 | não disponível | — | — | NÃO LOCALIZADO EM FONTE PRIMÁRIA |
| Distrito de Moatize | 2007 | 215.092 | 215.092 | https://web.archive.org/web/20100809032728id_/http://www.ine.gov.mz/censo2007/rdcenso09/Tete/c0705q3 | Quadro 3 (III RGPH 2007, Tete) | CONFIRMADO |
| Distrito de Moatize | 2017 | 260.843 | 260.843 (grafia da fonte: "MAOATIZE") | https://web.archive.org/web/20191114015524id_/http://www.ine.gov.mz/iv-rgph-2017/tete/quadro-3-... .xlsx | Quadro 3 (IV RGPH 2017, Tete) | CONFIRMADO |

## Questões a resolver (§ orquestrador)

- **(a) A que recorte correspondem 305.722 e 307.338.** 307.338 é o valor lido diretamente
  no Quadro 3 do IV RGPH 2017 (Tete), linha "CIDADE DE TETE", coluna TOTAL — **confirmado em
  fonte primária** (`data/raw/quadro-3-...-2017.xlsx`). **305.722 não aparece em nenhum lugar
  do Quadro 3 nem na brochura nacional** (`data/raw/censo-2017-brochura-...-nacional.pdf`,
  varrida por busca textual por "305 722"/"305722": zero ocorrências). Hipóteses não
  verificadas para a origem de 305.722: (i) população "presente" ou "residente" com outro
  ajuste censitário não publicado nos quadros consultados; (ii) erro de transcrição em
  agregador (citypopulation.de/Wikipedia); (iii) recorte de limite administrativo diferente
  (ex.: cidade sem um bairro periférico). Sem documento primário que o contenha, **305.722
  fica como "não disponível / não confirmado"** — não deve ser citado no núcleo do estudo.

- **(b) Sub-enumeração de 3,7% — documentada e incorporada?** Documentada: **sim**, na
  brochura nacional do IV RGPH 2017, página do "QUADRO DO TAMANHO DA POPULAÇÃO DE
  MOÇAMBIQUE, 2017" (`data/raw/censo-2017-brochura-...-nacional.pdf`). O quadro apresenta,
  por província, três colunas: "População Total (Ajustada à Taxa de Omissão)", "Taxa de
  Omissão" e "População Residente a 1 de Agosto de 2017". Para Moçambique: população
  ajustada = 27.909.798; taxa de omissão = **3,7%**; população residente (não ajustada) =
  26.899.105. Para a província de Tete especificamente a taxa foi 3,8% (mulheres 3,7%),
  população ajustada 2.648.941 vs. residente 2.551.826.
  **Incorporada nos números distritais/municipais publicados nos quadros provinciais?
  NÃO.** Verificação direta: o TOTAL da linha "T O T A L" do Quadro 3 da província de Tete
  (2017) é **2.551.826** — exatamente igual à "População Residente" (não ajustada) do
  quadro nacional, e não aos 2.648.941 ajustados. Logo, **307.338 (Cidade de Tete) e 260.843
  (Distrito de Moatize) são contagens residentes, sem o ajuste de omissão — 3,8% na Província de Tete
  (a taxa pertinente a estas unidades) e 3,7% no total nacional: duas taxas de
  unidades diferentes, NÃO uma faixa de incerteza de uma só grandeza
  aplicado.** Isso é relevante para H1 e para qualquer comparação com o total oficial do
  país: os números distritais publicados sistematicamente subestimam a população "real"
  estimada pelo INE em cerca de 3-6% a mais, dependendo da província.

- **(c) Mudança de limites do Distrito de Moatize entre censos.** Não foi possível
  confirmar ou refutar diretamente com documento cartográfico de 1997/2007/2017 dentro do
  tempo disponível nesta rodada. Indício indireto: o COD-AB (HDX, `data/raw/hdx_cod-ab-moz_admin_boundaries.xlsx`,
  metodologia declarada no próprio dataset) afirma explicitamente que os limites ADM3/ADM4
  atuais foram objeto de "ajustes não oficiais" pela OCHA/PMA para corrigir desalinhamentos
  com os censos de 2017, e que uma atualização oficial de limites administrativos só é
  esperada em 2027 — ou seja, o próprio INE reconhece que a malha administrativa vigente
  ainda deriva da base de 2017 sem revisão completa. Isso não prova mudança 1997→2007→2017,
  mas mostra que a malha não é estática e que qualquer comparação direta de área/população
  por "Distrito de Moatize" ao longo do tempo **precisa de nota metodológica explícita de
  não comparabilidade garantida**, até que se localizem os mapas/codificadores de cada
  censo (não localizados nesta rodada). Registrar como **não resolvido — requer fonte
  cartográfica dedicada (INE/DINAGECA/ANTG), fora do escopo desta verificação textual**.

## Censo 1997 (II RGPH) — busca dedicada
Status: CONCLUÍDA — não disponível em fonte primária acessível.

Buscas feitas (todas via CDX do Wayback Machine, `web.archive.org/cdx/search/cdx`, 2026-09-07):
1. `ine.gov.mz/censo97/*` (filtro statuscode:200, colapsado por urlkey, limite 500) — 123 capturas.
   Estrutura: pastas numéricas `00`–`11` = brochuras provinciais "II RECENSEAMENTO GERAL DA
   POPULAÇÃO E HABITAÇÃO 1997 — INDICADORES SÓCIO-DEMOGRÁFICOS" por província (confirmado por
   inspeção de `<n>introdu.htm` em cada pasta): 00=País, 01=Niassa, 02=Cabo Delgado,
   04=Zambézia, 05=**Tete**, 08=Inhambane, 09=Gaza, 10=Maputo (Cidade/Província). Não há pasta
   por distrito ou cidade.
2. Pasta `05` (Tete) tem só 8 arquivos arquivados: `05estado.htm`, `05forcade.htm`,
   `05fucundidade.htm`, `05habitaca.htm`, `05introdu.htm`, `05linguas.htm`, `brochura.htm`,
   `imagens/t_05indicadores.gif`. O índice `brochura.htm` (arquivado em
   `https://web.archive.org/web/20000124214016id_/http://www.ine.gov.mz:80/Censo97/05/brochura/brochura.htm`)
   lista 14 seções, incluindo `05dados.htm` (DADOS BÁSICOS) e `05populacao.htm` (TAMANHO,
   ESTRUTURA E CRESCIMENTO DA POPULAÇÃO) — exatamente as páginas que conteriam os números de
   população — mas **nenhuma das duas foi rastreada pelo crawler do Internet Archive em
   nenhuma data** (consulta CDX específica para essas duas URLs: zero capturas, qualquer
   status). `05mortalidade.htm` e `05agregado.htm` foram rastreados mas retornaram 404 já em
   2000-07-08 (arquivo removido do servidor antes de ser espelhado).
3. Mesmo se recuperadas, as brochuras do II RGPH 1997 são de nível **provincial**, não
   distrital/municipal — não há evidência de que contivessem tabela "Cidade de Tete" ou
   "Distrito de Moatize" (o `id_tete` de 2007 mostra que essas brochuras trazem apenas
   indicadores da província inteira, comparando 1997 vs 2007 a esse nível).
4. `ine.gov.mz/censos_dir/*` — existe, mas cobre exclusivamente Censo Agro-Pecuário e Censo
   às Empresas (CEMPRE); nenhum arquivo relativo ao II RGPH 1997 população.
5. `ine.gov.mz/ii-rgph*` e `ine.gov.mz/IIRGPH*` — zero capturas.
6. `ine.gov.mz/censo1997/*` — não testado isoladamente (redundante com `censo97/*`, que já
   cobre o padrão real de URL usado pelo INE).
7. mozdata.ine.gov.mz — confirmado por execução anterior que não lista o Censo 1997 (II RGPH)
   em seu catálogo.

**Conclusão:** os valores de §8 para 1997 (Cidade de Tete = 101.984; Distrito de Moatize =
109.103) **não puderam ser confirmados em fonte primária**. Não há documento do INE
acessível (nem ao vivo, nem arquivado) com desagregação distrital/municipal do II RGPH 1997
para a província de Tete. Motivo exato: páginas candidatas (`05dados.htm`, `05populacao.htm`)
nunca foram rastreadas pelo Internet Archive antes de saírem do ar; o site atual
(`ine.gov.mz`) está fora do ar (000) desde a verificação de 2026-09-07. Os valores de §8
permanecem como citação de agregador (citypopulation.de/Wikipedia) e **não devem ser usados
como número publicado** — apenas como hipótese de trabalho para a linha de base contrafactual
de H1, com selo "não verificado em fonte primária".

## Suficiência para §1

**Pergunta 1 (linha de base 1997–2005) e H1 (aceleração de ~4%/ano para ~7%/ano):**
**parcialmente respondível, com lacuna séria na ponta 1997.** Os anos-âncora 2007 e 2017
estão confirmados em fonte primária (Cidade de Tete: 155.870 em 2007, 307.338 em 2017;
Distrito de Moatize: 215.092 em 2007, 260.843 em 2017 — todos não ajustados pela taxa de
omissão de 3,8% da Província de Tete; a nacional, 3,7%, é outra grandeza). O ano-âncora 1997 **não foi confirmado em fonte primária** (busca
exaustiva no Wayback, ver seção acima) — os valores de §8 (101.984 e 109.103) continuam
como citação de agregador, não verificável. Isso significa que a CAGR pré-2005 (ponta do
H1) só pode ser calculada com um número não verificado, o que deve ser declarado
explicitamente no artigo/app como "não observado / fonte não localizada" caso não se
encontre alternativa (ex.: publicação impressa do INE digitalizada por terceiros, ou
consulta direta ao INE). A CAGR 2007→2017 (a segunda perna de H1) é computável e sólida.

**Pergunta 6 (bust e transição, 2015–2025):** os dados desta família **não cobrem** esse
período — o próximo censo é 2027 (ainda não realizado/publicado). Séries demográficas para
2015–2025 dependem de projeções do INE (não localizadas nesta busca) ou de proxies de outras
famílias (imagem, luzes noturnas), fora do escopo desta verificação. **Não respondível com
esta família isoladamente.**

**H1 especificamente:** testável apenas com ressalva. Recomenda-se: (i) manter 1997 como
"não verificado" e não usá-lo em nenhum número publicado no núcleo A; (ii) se o
`auditor-dados` aceitar 1997 como validação B (citação de agregador, rotulada como tal), a
hipótese pode ser explorada em caráter exploratório, nunca como conclusão do núcleo A;
(iii) qualquer comparação de área/população do "Distrito de Moatize" ao longo do tempo deve
vir acompanhada da ressalva de (c) sobre possível mudança de limites administrativos, ainda
não resolvida.

**O que falta, especificamente:**
1. Um documento primário do INE com Cidade de Tete/Distrito de Moatize para 1997 (não
   localizado no Wayback; pode existir em acervo físico do INE ou publicação impressa não
   digitalizada).
2. Confirmação cartográfica de mudança de limites do Distrito de Moatize 1997→2007→2017
   (fora do escopo desta busca textual).
3. Origem do número 305.722 (não localizado em nenhum documento primário consultado).

---

## RECONCILIAÇÃO — 2026-09-08

A avaliação acima trata **H1 na formulação original, em população** ("aceleração de ~4 %/ano
para ~7 %/ano"), e a classifica como "parcialmente respondível, com lacuna séria na ponta
1997". Duas decisões posteriores mudam isso:

- **`docs/ADR/0003`** reformulou H1 em termos de **área construída**, não de habitantes,
  precisamente porque o Censo de 1997 não existe em fonte acessível. A formulação em
  população **não é mais a hipótese do estudo**.
- **A emenda de 2026-09-08 ao `docs/ADR/0008`** restringe ainda mais a formulação em área:
  ela vale sobre **taxa de primeira detecção**, não sobre estoque, porque nem a classificação
  própria (regra R2) nem o WSF Evolution (formato do dado) fornecem estoque sem
  monotonicidade imposta.

O conteúdo factual deste fragmento — licenças, âncoras verificadas, o que existe e o que não
existe — **permanece válido**. O que caducou é a avaliação de testabilidade de H1, que foi
feita antes das reformulações.


---

<!-- fonte: data/provenance_parts/demograficas_terceiros.md -->

# PROVENANCE — Demográficas via reprocessadores institucionais (Fase 0', tarefa adicional)

Fragmento novo, paralelo a `demograficas.md` (fechado). Registra, para cada fonte
candidata a reprocessador institucional (§ distinção do prompt desta tarefa): URL
exata testada, código HTTP, data de acesso, o que foi efetivamente lido, e se os
valores de §8 (101.984 / 109.103 em 1997; 155.870 / 215.092 em 2007; 307.338 / 260.843
em 2017) foram confirmados, divergiram, ou não foram encontrados.

Todas as linhas seguem `PENDENTE` até verificação efetiva (regra "grave incrementalmente").

## 1. CIESIN GPWv3 — National Identifier Grid / documentação Moçambique
Status: NÃO DISPONÍVEL — servidor inacessível.
- URL testada: https://sedac.ciesin.columbia.edu/data/set/gpw-v3-national-identifier-grid
- `curl -m 20 -L -o /dev/null -w '%{http_code}'` retornou `000` (exit 28, timeout) em duas
  tentativas em 2026-09-07. `curl -sI -m 20 https://sedac.ciesin.columbia.edu` também
  falhou (mesmo domínio raiz inacessível).
- Motivo exato: timeout de conexão — não é 404, não é paywall; o servidor não respondeu
  dentro de 20s em nenhuma tentativa desta rodada.
- Não foi possível confirmar se GPWv3 traz dados de entrada por distrito para Moçambique
  1997/2000, nem a licença. Registrado como não disponível, não como C — reavaliar em
  execução futura com o domínio no ar.

## 2. CIESIN GPWv4 — Population Count / Input Data Country-Level, Mozambique
Status: NÃO DISPONÍVEL — mesma falha do item 1.
- URL testada: https://sedac.ciesin.columbia.edu/data/set/gpw-v4-population-count-rev11
- `curl -m 20 -L -o /dev/null -w '%{http_code}'` → `000` (timeout, exit 28), 2026-09-07.
- sedac.ciesin.columbia.edu inteiro inacessível nesta rodada; não confirmável.

## 3. UNSD Demographic Yearbook 2007 — Tabela 8, censo de 1997
Status: VERIFICADO — CONFIRMA a âncora de Tete 1997 (101.984), via reprocessador institucional.
- URL: https://unstats.un.org/unsd/demographic/products/dyb/dyb2007/Table08.xls → HTTP 200.
- Espelhado em `data/raw/unsd_dyb2007_table08_capital_cities.xls` (2.813.440 bytes),
  com `.sha256` e `.meta.json`.
- Tabela 8 "Population of capital cities and cities of 100.000 or more inhabitants:
  latest available year, 1988-2007". Bloco "Mozambique", subcabeçalho "1 VIII 1997
  (CDFC)" (censo de facto, 1 de agosto de 1997): linha "Tete" = 101.984 (city proper,
  ambos os sexos). Lido diretamente do arquivo com `xlrd` (planilha "Data", linha 214).
- Também testada a edição DYB2000 (Table08.xls, planilha "tables"): só lista Maputo
  para 1997 (1.015.300 na tabela de urban agglomeration da edição 2000, célula
  diferente da de 2007 — a UNSD atualiza retroativamente conforme países submetem
  dados); Tete não aparece na edição 2000, só na de 2007. Não gravado em disco por
  não conter dado relevante ao escopo desta tarefa (só Maputo).
- Moatize (distrito) não aparece em nenhuma edição: a tabela só lista "cidades"
  (city proper) submetidas pelo país como tal, e o distrito de Moatize em 1997 era
  majoritariamente rural — não teria sido reportado nessa categoria.
- **Divergência**: nenhuma. Valor idêntico ao registrado em §8 e ao que
  `demograficas.md` já havia recuperado do Wayback (rastreamento pendente lá).
- Licença: UN Terms and Conditions of Use (un.org/en/aboutun/terms) — acesso livre,
  mas uso restrito a "personal, non-commercial use", sem redistribuição nem obras
  derivadas sem autorização escrita. **Nível B**, não A: não atende ao requisito de
  licença que permita "uso, redistribuição e derivadas" do §4.0 do CLAUDE.md.
- **Efeito prático**: o valor de Tete 1997 deixa de depender só de um agregador
  (citypopulation.de/Wikipedia) e passa a ter uma fonte reprocessadora institucional
  citável (UNSD) — mas essa fonte é nível B, então não desbloqueia núcleo A sozinha.
  Serve como confirmação/validação forte do número, não como habilitação de publicação
  em núcleo A.

## 4. IPUMS International — amostras Moçambique 1997/2007/2017 (verificar tabulação agregada pública)
Status: VERIFICADO — permanece nível B, nenhuma tabulação agregada de nível A encontrada.
- URL testada: https://international.ipums.org/international-action/sample_details/country/mz
  → HTTP 200 (2026-09-07).
- Página lista as três amostras de Moçambique como "available": mz1997a (1997, II RGPH),
  mz2007a (2007, III RGPH), mz2017a (2017, IV RGPH). Confirma que IPUMS harmoniza os três
  censos com GEO2_MZ e GEO3_MZ1997/APOSTMZ conforme §4.1 do CLAUDE.md.
- Busca por `sample_details/mz1997a` direta retornou 404; a página funcional é
  `sample_details/country/mz`, que lista as amostras por país (não por amostra individual).
- Não há, nessa página nem nos termos de uso (international.ipums.org/international/terms.shtml,
  já registrado em `demograficas.md`), nenhuma tabulação agregada pública sem cadastro:
  o acesso é só ao microdado, sob termos que proíbem redistribuição.
- **Conclusão**: IPUMS 1997/2007/2017 confirma-se como nível B para os três censos —
  útil apenas para validação (dasimetria, checagem cruzada), nunca como fonte publicável
  de nível A. Não foi baixado nenhum microdado (regra de nível B do CLAUDE.md).

## 5. World Bank Microdata Library / IHSN — ficha do II RGPH 1997
Status: NÃO DISPONÍVEL nesta rodada (não é 404 nem paywall — limitação de scraping).
- URLs testadas: https://microdata.worldbank.org/index.php/catalog/central?q=mozambique+1997+census
  (HTTP 200, mas conteúdo renderizado em cliente via Vue/JS, sem lista de resultados no HTML bruto);
  https://microdata.worldbank.org/index.php/api/catalog?search=Mozambique%20Population%20Census
  (HTTP 200, mas retornou 15 registros genéricos, nenhum de Moçambique — parâmetro `search`
  parece ignorado por esse endpoint); https://microdata.worldbank.org/index.php/api/catalog/central/search?ps=20&sk=mozambique
  (HTTP 400 — parâmetros incorretos para esse endpoint); catalog.ihsn.org (mesmo software
  NADA, mesma limitação, HTTP 200 na página inicial).
- Motivo exato: não foi possível, no tempo desta rodada, identificar o endpoint de API
  correto que o catálogo usa internamente para popular a busca renderizada em
  JavaScript. Isso é uma limitação de método (falta de execução de JS), não uma
  indicação de que o dado não exista ou esteja fechado.
- Registrado como **não disponível nesta rodada** — não como C. Recomenda-se, em
  execução futura, usar um navegador headless ou localizar a documentação da API do
  NADA (geralmente `/index.php/api/catalog/…` com parâmetros diferentes dos testados).

## 6. UNFPA / ReliefWeb / HDX — séries históricas por distrito pré-2017
Status: NÃO DISPONÍVEL nesta rodada — busca incompleta.
- URL testada: https://reliefweb.int/updates?advanced-search=%28PC167%29 → HTTP 202
  (resposta assíncrona típica de app de busca; conteúdo da lista de resultados não foi
  inspecionado em profundidade dentro do tempo desta rodada).
- ReliefWeb é um repositório de relatórios humanitários, não um reprocessador
  estatístico dedicado como CIESIN/UNSD/HDX — mesmo que aceitável pela distinção desta
  tarefa, não seria fonte primária de tabulação censitária, apenas possível ponte para
  documentos de terceiros (que por sua vez precisariam ser rastreados até o INE).
- HDX (item 7/10) já cobre 2017 diretamente com nível A; pré-2017 (1997/2007) não foi
  localizado em ReliefWeb nem em HDX nesta rodada.

## 7. HDX COD-PS Moçambique — vintage 2017 (moz_admpop_adm2_2017_v2.csv)
Status: VERIFICADO — CONFIRMA exatamente Cidade de Tete e Distrito de Moatize 2017.
- URL: https://data.humdata.org/dataset/46b79d47-0667-4baa-8d69-468b208855ed/resource/173abc7f-810a-4022-89dd-c9a9fa40a490/download/moz_admpop_adm2_2017_v2.csv
  → HTTP 200.
- Espelhado em `data/raw/hdx_cod-ps-moz_admpop_adm2_2017_v2.csv` (54.556 bytes),
  com `.sha256` e `.meta.json`.
- Linha lida diretamente do CSV: `MZ10,Tete,...,MZ1006,Cidade De Tete,District,...,T_TL=307338`
  e `MZ10,Tete,...,MZ1012,Moatize,District,...,T_TL=260843`.
- **Confirma exatamente** os dois valores de 2017 já recuperados do documento primário
  do INE via Wayback em `demograficas.md` (307.338 e 260.843) — nenhuma divergência.
- Licença: CC BY-IGO 3.0 (creativecommons.org/licenses/by/3.0/igo/legalcode), já
  registrada para o dataset `cod-ps-moz` como nível A em `demograficas.md`. Fonte
  declarada pelo dataset: INE Moçambique, IV RGPH 2017; reprocessador: OCHA
  Mozambique / HDX FIS.
- **Efeito prático**: os valores de 2017 (307.338 e 260.843) agora têm confirmação por
  reprocessador institucional de **nível A**, independente do Wayback/INE. Isso é o
  resultado de maior valor desta rodada depois da prioridade 1 (1997), conforme
  esperado pelo enunciado desta tarefa.

## 8. UNSD Demographic Yearbook — dybcensusdata (tabela interativa) — 2017
Status: NÃO DISPONÍVEL nesta rodada (interface client-side sem endpoint de exportação identificado).
- URL: https://unstats.un.org/unsd/demographic-social/products/dyb/dybcensusdata.cshtml
  → HTTP 200, mas o HTML bruto não contém a tabela de dados (populada via JavaScript).
- Diferente da edição 2007 (item 3), que ainda distribui arquivos .xls estáticos por
  tabela e ano, a versão atual "dybcensusdata" é uma aplicação interativa sem link de
  export .xls/.csv identificável nesta rodada.
- Não crítico: o item 7 (HDX, nível A) já confirma 2017 com os dois valores exatos.

## 9. World Bank Microdata Library / IHSN — ficha do III RGPH 2007 e IV RGPH 2017
Status: NÃO DISPONÍVEL nesta rodada — mesma limitação de scraping do item 5.
- URLs testadas: https://microdata.worldbank.org/index.php/catalog/central?q=mozambique+population+census
  (HTTP 200, sem lista extraível); API com `sk=mozambique` → HTTP 400.
- Não crítico: 2007 tem confirmação parcial pelo item 3 (mesma família UN, mas tabela
  de 1997) e 2017 tem confirmação completa e de nível A pelo item 7.

## 10. HDX COD-PS Moçambique — inventário de vintages (package_show)
Status: VERIFICADO — dataset não cobre 1997 nem 2007.
- URL: https://data.humdata.org/api/3/action/package_show?id=cod-ps-moz → HTTP 200 (API CKAN).
- Campo `resources` lista vintages 2017, 2023, 2024, 2025 (mais antigo: 2017,
  `moz_admpop_2017.xlsx` e CSVs por nível admin). Não há recurso de 1997 nem 2007.
- Licença do dataset: `license_id: cc-by-igo`, `license_url:
  http://creativecommons.org/licenses/by/3.0/igo/legalcode` (mesma do item 7).
- **Conclusão**: HDX COD-PS não é caminho para confirmar 1997; é o caminho de nível A
  já usado no item 7 para confirmar 2017. Vintages 2023–2025 são projeções INE
  pós-censo (não recenseamento), relevantes para §1 pergunta 6/7, fora do escopo
  desta verificação pontual de 1997/2007/2017.

## Veredito

Para cada um dos seis valores-âncora de §8 do CLAUDE.md, o melhor nível de licença
alcançado nesta rodada, via reprocessador institucional (não agregador):

| Âncora | Valor em §8 | Melhor reprocessador encontrado | Nível | Publicável em núcleo A? |
|---|---|---|---|---|
| Cidade de Tete, 1997 | 101.984 | UNSD Demographic Yearbook 2007, Tabela 8 (`data/raw/unsd_dyb2007_table08_capital_cities.xls`) — valor **confirmado, sem divergência** | B | **Não.** UN Terms and Conditions proíbe redistribuição/obras derivadas sem autorização escrita. Só serve como validação/confirmação forte de que o número não é inventado. |
| Distrito de Moatize, 1997 | 109.103 | Nenhum reprocessador institucional localizado nesta rodada (CIESIN/SEDAC inacessível — timeout; World Bank/IHSN não raspável; UNSD Table 8 só lista "cidades", e Moatize não aparece como tal em 1997; IPUMS é B e não expõe tabulação agregada) | não avaliado (não disponível) | **Não.** Permanece sem qualquer reprocessador citável nesta rodada; continua dependendo só do agregador (citypopulation.de) mencionado em §8, o que **não é citável** pela regra §4.0.4. |
| Cidade de Tete, 2007 | 155.870 | Nenhuma segunda via de reprocessador institucional confirmada nesta rodada além do próprio INE (Wayback, já registrado em `demograficas.md`, nível "pendente_auditoria"); UNSD Table 8 2007 só carrega o censo de 1997 para Moçambique, não o de 2007 | não avaliado (não disponível) | **Não muda** — segue no mesmo status de `demograficas.md` (documento primário via Wayback, licença INE não localizável). |
| Distrito de Moatize, 2007 | 215.092 | Idem acima — nenhuma segunda via encontrada | não avaliado (não disponível) | **Não muda.** |
| Cidade de Tete, 2017 | 307.338 (não ajustado) | **HDX COD-PS Moçambique, vintage 2017** (`data/raw/hdx_cod-ps-moz_admpop_adm2_2017_v2.csv`) — valor **confirmado exatamente**, T_TL=307338 | **A** | **Sim.** CC BY-IGO 3.0, reprocessador institucional (OCHA/HDX), origem declarada INE IV RGPH 2017. Converte este valor para núcleo A. |
| Distrito de Moatize, 2017 | 260.843 | **HDX COD-PS Moçambique, vintage 2017** (mesmo arquivo) — valor **confirmado exatamente**, T_TL=260843 | **A** | **Sim**, mesma justificativa acima. |

### A linha de base de 1997 foi recuperada?

**Parcialmente, e só em nível B.** A Cidade de Tete 1997 (101.984) agora tem uma fonte
reprocessadora institucional citável — o UNSD Demographic Yearbook 2007, Tabela 8 —
que confirma o valor exatamente. Isso é estritamente melhor do que depender só de
citypopulation.de/Wikipedia (que nunca poderiam ser citados pela regra §4.0.4), mas a
licença do UNSD (uso pessoal não-comercial, sem redistribuição nem obras derivadas sem
autorização escrita) é **nível B**, não A. Portanto **o valor pode ser citado no texto
com a ressalva de nível B e fonte UNSD**, mas **não pode sustentar um número em tabela
de resultados do núcleo reprodutível** (regra §4.0, "apenas fontes de nível A
sustentam números publicados").

O Distrito de Moatize 1997 (109.103) **não foi recuperado** por nenhum reprocessador
institucional nesta rodada: CIESIN/SEDAC (a pista mais forte apontada no enunciado)
esteve inacessível (timeout, `curl -m 20` retornando `000`/exit 28 em múltiplas
tentativas) durante toda a janela desta execução — não é um "não existe", é uma falha
de acesso ao servidor que deveria ser reexecutada. A tabela do UNSD que confirmou Tete
só lista "cidades" (city proper) submetidas pelo país, e Moatize em 1997 era um
distrito majoritariamente rural, não elegível a essa categoria.

**Conclusão para `docs/ADR/0003`:** como nenhum dos dois valores de 1997 chegou a
nível A (Tete ficou em B; Moatize permanece sem reprocessador), **o ADR não precisa
ser revisto por esta rodada** — a linha de base por área construída continua sendo a
melhor alternativa disponível para 1997 no núcleo reprodutível A. Se uma execução
futura conseguir acessar CIESIN/SEDAC (hoje inacessível) e ele expuser tabulações de
Moçambique por distrito em nível CC-BY-4.0 (nível A) cobrindo Moatize 1997, **então
sim** o ADR 0003 precisaria ser reaberto — mas isso não aconteceu nesta rodada.

O maior ganho concreto desta rodada é a **elevação de 2017 (ambos os valores) para
núcleo A** via HDX COD-PS, que antes dependia só do documento do INE via Wayback sem
licença localizável ("pendente_auditoria" em `demograficas.md`). Isso desbloqueia
diretamente o pilar demográfico de §5.3 para o ano de 2017, o mais recente censo.

---

## Acréscimo do orquestrador — COD-PS vintages 2024/2025 (2026-09-07)

A rodada anterior consultou o COD-PS apenas no vintage 2017. Consultando a API do CKAN do
HDX (`package_show?id=cod-ps-moz`), o mesmo dataset publica também os vintages **2023, 2024
e 2025**, com notas técnicas próprias.

Espelhado: `data/raw/hdx_cod-ps-moz_admpop_adm2_2025.csv` (com `.sha256` e `.meta.json`).

| Unidade | P-code | Homens | Mulheres | Total 2025 |
|---|---|---|---|---|
| Cidade De Tete | MZ1006 | 229.296 | 230.952 | **460.248** |
| Moatize | MZ1012 | 171.221 | 177.882 | **349.103** |

**Licença CC BY-IGO 3.0 → nível A.** Origem declarada: projeções do INE.

**Selo obrigatório: `modelado`.** São projeções, não contagem censitária, e não podem ser
apresentadas como população recenseada. §5.3 exige o selo explícito.

### Por que isto importa

`data/DATA_AUDIT.md` concluiu que a **pergunta 6 de §1** (bust e transição, 2015–2025) era
irrespondível por não haver âncora demográfica depois de 2017. Com o COD-PS, passa a haver
uma ponta em 2025 de nível A — modelada, mas citável. A pergunta muda de "não respondível"
para "respondível com ressalva de selo".

Não resolve 1997 nem 2007, que continuam sem fonte de nível A.

### Via esgotada nesta rodada

**CIESIN/SEDAC está fora do ar** — `sedac.ciesin.columbia.edu` devolve **000** em todas as
tentativas, igual a `ine.gov.mz`. Era a via mais promissora para 1997 e 2007 por distrito,
porque o GPW publica os dados de entrada por unidade administrativa. Não foi falha de busca:
o servidor não responde. **Retomar quando voltar.**

---

## RECONCILIAÇÃO — 2026-09-08 (revisão de `data/DATA_AUDIT.md`)

Acima está escrito que a pergunta 6 passa de "não respondível" para **"respondível com
ressalva de selo"**, graças à ponta de 2025 do COD-PS. A revisão do `data/DATA_AUDIT.md` de
2026-09-08 acrescenta duas restrições que este fragmento não podia conhecer:

1. **O par 2015–2020 da série própria de área está contaminado** pelo colapso do pool de
   treino em 2015 (`docs/ADR/0013`), e **não pode ancorar magnitude de bust**. As séries de
   luzes noturnas (VIIRS e DMSP) passam a ser a via primária pós-2015.
2. **A circularidade de H4 é dos dois lados**, não de um: a população de 2025 é projeção
   modelada **e** a série de `urbano` é catraca por R2. Usar as duas juntas confirmaria o
   descolamento população–luz por construção.

O achado central deste fragmento — que o HDX COD-PS torna 2017 publicável em nível A por um
segundo caminho, com licença própria e verificável — **permanece válido e não é afetado**.


---

<!-- fonte: data/provenance_parts/economicos.md -->

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


---

<!-- fonte: data/provenance_parts/fase3_auditoria_t3.md -->

# Fase 3 — Proveniência da auditoria de classificação (T3)

Complementa `data/provenance_parts/fase3_coleta_t2_proveniencia.md` com o selo de
nível A/B/C que faltava (a coleta registrou apenas `.meta.json` com
`"level": "nao classificado - cabe ao auditor-dados"`).

| arquivo/família | nível final | selo | verificado contra |
|---|---|---|---|
| `viirs_like_li2020_v2_*.tif` (54 recortes, AOI Tete + 5 controles) | A | observado | JSON da API do Harvard Dataverse (`metadataBlocks.citation.license`), não agregador |
| `wsf_evolution_S20E032.tif` (Chimoio) | A | observado (pixel = ano de 1ª detecção) | `grid.geojson` do produtor DLR + página de licença geoservice.dlr.de |
| `wsf_evolution_S18E036.tif` (Quelimane) | A | observado | idem |
| `wsf_evolution_S14E034.tif` (Lichinga) | A | observado | idem |
| `wsf_evolution_S26E032.tif` (Xai-Xai) | A | observado | idem |
| `wsf_evolution_S24E034.tif` (Inhambane) | A | observado | idem |
| `moz_admin_boundaries.geojson.zip` | A | observado | API CKAN `package_show` de data.humdata.org |
| VIIRS VNL V2 (EOG, `eogdata.mines.edu`) | B (rebaixada de A registrada em `economicos.md`) | não obtido | evidência HTTP 302→OAuth em todas as rotas testadas, 2026-09-08 |
| DMSP-OLS estável (NOAA/NCEI) | C — excluída | não obtido | HTTP 404 na URL de `CLAUDE.md`; via sucessora bloqueada por OAuth |

## Consequência para `docs/DESENHO_FASE3.md` — premissa 4 (§1.3 item 4)

O desenho pré-registrado (`docs/DESENHO_FASE3.md`, fixado 2026-09-08, §1.1 tabela e
§1.3 item 4) previa **duas séries de luz independentes que se sobrepõem em 2012–2013**
(`S_VIIRS_soma`, EOG, 2012–2025, nível A antes desta auditoria; `S_DMSP_soma`,
1992–2013, nível A) para conciliar DMSP↔VIIRS por um trecho de sobreposição estimado
**por nós**, com critério pré-registrado em §1.3.4 e §4.4 (P4) do mesmo documento; o
harmonizado (`S_HARM`, Li et al. 2020, ali já registrado como nível **B**) estava
reservado a "só validação, nunca sustenta número publicado" — precisamente porque a
conciliação interna ao produtor não é verificável por nós.

Esta auditoria muda o insumo, não o julgamento already escrito no desenho: `S_VIIRS_soma`
passa de A para B (item 4 acima) e `S_DMSP_soma` passa de A para C (item 5 acima, a
única via de acesso identificada está bloqueada e a página original é 404). **As duas
séries que dariam a conciliação independente deixam de existir em nível A.** A única
série de luz que permanece A é `viirs_like_li2020_v2` (Chen/Yu, Harvard Dataverse) —
que é, ela própria, **um harmonizado produzido pelo método do produtor** (calibração
cruzada por super-resolução/aprendizado profundo, conforme Chen et al. 2021 e extensões
posteriores), não uma soma bruta de radiância por sensor.

## Resposta direta à pergunta do orquestrador

**Sim, a perda de VIIRS VNL (rebaixada a B) e de DMSP-OLS (excluída, C) torna o
harmonizado Chen/Yu a única série de luzes de nível A disponível**, e isso **não é
aceitável como equivalente à premissa original do desenho**, pelos seguintes motivos,
sem eufemismo:

1. A premissa 4 do desenho supunha conciliação **estimada por nós**, com erro-padrão,
   critério de falha e placebo publicáveis (§1.3.4, §4.4 P4 do `DESENHO_FASE3.md`).
   Usar só o harmonizado do produtor substitui isso por uma conciliação **feita dentro
   de um modelo de terceiros** (rede neural de super-resolução, no caso de Chen et al.),
   cujos parâmetros, dados de treino e possíveis mudanças de versão **não são auditáveis
   por este pipeline** — é uma caixa preta de calibração, não uma calibração
   transparente.
2. Isso é agravado, não apenas mencionado en passant, pela descontinuidade medida pelo
   orquestrador (70,4→49,9 entre 2020 e 2022, estável em 49,9 até 2025) **coincidindo
   com uma janela em que terceiros documentam reprocessamento do produto para
   exatamente os anos 2021–2022** (ver `fase3_auditoria_t3.md`, seção de licenças). Sem
   DMSP ou VNL bruto para comparar, **não há como distinguir estatisticamente, com os
   dados hoje em `data/raw/`, uma quebra de produto de uma quebra de economia** na
   quebra de 2022 do desenho causal (`docs/DESENHO_FASE3.md` §1.2, linha "2022").
3. Nenhuma fonte B pode "resolver" isso: por §4.0, B é só validação, nunca sustenta
   conclusão. Não há, hoje, nenhuma fonte A alternativa para cross-checar o harmonizado
   na janela 2020–2022.

**Consequência declarada para o desenho causal**: a quebra de 2022 em `S_VIIRS_soma`
(agora `S_HARM`, o único disponível) deve ser tratada, além dos quatro placebos já
exigidos (P1–P4 de `DESENHO_FASE3.md` §4), com um **quinto aviso obrigatório e
explícito** em qualquer figura/tabela que a publique: "não distinguível de mudança de
versão do produtor entre 2020 e 2022 — nenhuma fonte de nível A permite verificação
independente". Isto não é um placebo executável (não há dado para rodá-lo); é uma
lacuna a declarar, não a maquiar, seguindo o mesmo padrão de honestidade já adotado em
`docs/DESENHO_FASE3.md` §1.3 e §8. Recomenda-se ao orquestrador que `docs/DESENHO_FASE3.md`
receba uma emenda datada (§10 do próprio documento) registrando esta mudança de
disponibilidade de dado, com a declaração explícita de que o autor da emenda **já viu**
o valor da radiância (70,4/49,9) antes de escrevê-la — exigência do próprio protocolo de
pré-registro.


---

<!-- fonte: data/provenance_parts/fase3_coleta_t2_proveniencia.md -->

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


---

<!-- fonte: data/provenance_parts/fatos_verificados.md -->

## `paper/FATOS_VERIFICADOS.md` — folha de fatos do artigo

- **Gerado por:** `pipeline/04_figures/fatos_verificados.py`, alvo `figures` do Makefile.
- **Selo:** derivado — nenhum valor é observado aqui; todos são recalculados de
  `data/processed/` a cada execução.
- **Nível da fonte:** A (todos os insumos são `data/processed/`, que só contém nível A).
- **Não editar à mão.** O arquivo é sobrescrito por `make figures`.

**Insumos:** `acuracia_por_ano.csv` · `causal/estabilidade_temporal_camadas.csv` ·
`causal/decomposicao_luz_por_camada.csv` · `causal/its_quebras.csv` ·
`causal/veredito_fase3.csv` · `causal/placebos.csv` · `causal/serie_luzes_anual.csv`.

**Por que existe (ORCHESTRATION_LOG.md 4-03 a 4-11).** A Fase 4 reprovou seis vezes por
**afirmação relacional**: número certo, qualificador errado — mediana citada como máximo,
acurácia citada como comissão, valor anterior à reexecução do `docs/ADR/0014` citado como
corrente. Todas vieram do orquestrador citando de memória. O artigo da Fase 5 é a maior
superfície de prosa do projeto e escreveria sobre os mesmos números.

Cada número aqui vem com **a estatística que ele é** (faixa entre anos, mediana, máximo,
ano único) e uma linha **"Como escrever"** que declara o que pode e o que não pode ser
afirmado sobre ele — por exemplo, que "até N" só admite o máximo medido, jamais a mediana;
que um p = 0,000 descreve a série de Tete mas não mede efeito do carvão; e que a queda de
luz de 2022 está fora da cidade e **não** pode ser atribuída à mina (`docs/ADR/0015`).

**Erro relacional encontrado dentro da própria folha, na sexta passagem do portão:** a
versão inicial dizia que os quatro painéis caíam "porque o placebo espacial mostra a mesma
quebra em capitais sem carvão" — verdadeiro em 2011 e 2016, **falso** em 2005 e 2022, onde
P1 é *não estimável*. O motivo passou a ser lido do CSV por quebra, em vez de generalizado.


---

<!-- fonte: data/provenance_parts/figuras.md -->

# Proveniência — Figuras (`pipeline/04_figures/`)

Fragmento gerado/atualizado manualmente ao lado dos scripts de `pipeline/04_figures/`.
Consolidado em `PROVENANCE.md` por `scripts/consolidar_registros.py`. Cada figura grava
também o seu próprio `.meta.json` ao lado do artefato em `paper/figuras/`, com hash
sha256 de cada insumo — este fragmento resume o que já está lá, não o substitui.

## `mapa_localizacao.py` — mapa de localização de Tete e Moatize

- **Script:** `pipeline/04_figures/mapa_localizacao.py`.
- **Saídas:** `paper/figuras/mapa_localizacao.pdf` (vetorial), `mapa_localizacao.png`
  (300 dpi), `mapa_localizacao.meta.json` (proveniência por artefato, com hash sha256
  de cada insumo, hash de `config/study.yaml`, commit git e selo).
- **Composição:** mapa principal (AOI, ano-âncora 2025) com as três camadas
  classificadas mutuamente exclusivas (`urbano`, `industrial`, `reassentamento`),
  hidrografia (HydroRIVERS v10 África), povoados de reassentamento georreferenciados
  e limites distritais de contexto; encarte 1 (província de Tete, AOI destacada);
  encarte 2 (Moçambique, província de Tete destacada). Barra de escala, seta de norte
  e grade de coordenadas no mapa principal.
- **Insumos (todos nível A, já espelhados):**
  - `data/raw/hdx_cod-ab-moz_admin_boundaries.geojson.zip` — admin0/1/2, selecionados
    por `adm2_pcode`/`adm1_pcode` do esquema **COD-AB** (não COD-PS — ver
    `config/unidades.yaml`, seção `esquemas_pcode`; Cidade de Tete = MZ0501,
    Moatize = MZ0510, província de Tete = MZ05).
  - `data/processed/imagery/{urbano,industrial,reassentamento}_2025.geojson` — saída
    de `pipeline/01_imagery/classificacao.py`, já em EPSG:32736.
  - `data/raw/reassentamentos.geojson` — Cateme e Mwaladzi com ponto georreferenciado;
    "25 de Setembro" com `geometry: null` (não localizado em fonte aberta, não
    inventado — ver `data/provenance_parts/reassentamento.md`).
  - `data/raw/hydrorivers_af_v10.gdb.zip`, camada `HydroRIVERS_v10_af`, recortada à AOI
    por bbox na leitura (`gpd.read_file(..., bbox=...)`).
- **CRS:** mapa principal em EPSG:32736 (UTM 36S, métrica de área, convenção do
  repositório); encartes em EPSG:4326 (só localização/orientação, distorção
  provincial/nacional aceitável porque não há medição nessa escala).
- **Identidade visual:** Sistema Ardósia, aplicado via `pipeline/04_figures/
  _paleta_ardosia.py` — cópia vendorizada e **sem alteração** de
  `ardosia-brand-guidelines/scripts/palette.py` (skill pessoal do autor, fora do
  repositório), para que o pipeline não dependa de um caminho fora do controle de
  versão. Qualquer atualização da paleta normativa precisa ser replicada manualmente
  aqui e registrada em `docs/ADR/`.
- **Honestidade cartográfica (obrigatória, embutida na figura, não só no texto):**
  1. Legenda com advertência textual: a camada `urbano` tem acurácia do usuário
     medida entre 0,286 e 0,625 por ano-âncora (`docs/ADR/0009`) — entre 37,5% e 71,4% do
     que o mapa chama de construído não é. A camada é insumo classificado, não
     cadastro.
  2. Rodapé: a série temporal de área construída (não plotada nesta figura, que é um
     corte único de 2025) é a do WSF Evolution, não a classificação própria
     (`docs/ADR/0008`) — para quem reusar o corte fora de contexto.
  3. Legenda: nota sobre "25 de Setembro" sem geometria localizável, não representada
     no mapa, não inventada.
  Todas as três ressalvas também estão em `mapa_localizacao.meta.json` (`ressalvas`),
  verificadas por `pipeline/tests/test_figuras.py::test_meta_declara_ressalvas_de_honestidade_cartografica`.
- **Determinismo:** layout orçado em polegadas fixas (figura 11×12 in); `savefig.bbox`
  do tema Ardósia (`tight`, recorta por bbox de conteúdo) é explicitamente desligado
  (`plt.rcParams["savefig.bbox"] = None`) para que o tamanho da tela em pixels não
  dependa da métrica de fonte disponível na máquina que renderiza. Sem RNG, sem
  downloads. `pipeline/tests/test_figuras.py::test_script_e_determinístico` roda o
  script duas vezes e compara as dimensões do PNG.
- **Selo:** `observado` — todas as camadas de entrada são classificação/dado
  observado; nenhuma extrapolação.


---

<!-- fonte: data/provenance_parts/imagem.md -->

# Proveniência — Imagens Orbitais (Fase 0')

Registros de proveniência para dados de imagens orbitais. Nenhuma imagem foi
efetivamente baixada nesta fase; o que segue é o registro do **probe de
disponibilidade** (contagem de cenas), pré-requisito para dimensionar o
composto de estação seca do §5.1.

---

## Reexecução T2 (2026-09-07) — correção do probe de T1

A execução em T1 tinha três defeitos identificados pelo orquestrador:
(1) contava tamanho de página (`limit`) em vez de contagem real; (2) nunca
consultava o Element84 Earth Search, gravando `não_testado` sem emitir
requisição; (3) truncava o mês final em "-30", perdendo 31 de outubro.

Reescrita: `pipeline/00_fetch/probe_stac.py` (lógica) + `probe_stac.sh`
(wrapper fino via `uv run`). Lê `config/study.yaml` (AOI, anos-âncora,
estação seca, `nuvem_max_pct`) — nada hardcoded além dos dois endpoints STAC
e dos nomes de coleção. Consulta **os dois** endpoints para cada ano/coleção.
Contagem: usa `numberMatched`/`context.matched` quando o servidor fornece
(Element84); pagina via `links[].rel == "next"` somando `numberReturned`
quando não fornece (Planetary Computer, que não expõe contagem total).
Falha explícita (linha `status=erro` com a exceção HTTP real) se um endpoint
não responder — nenhuma linha é gravada sem medição.

Saída: `data/interim/stac_disponibilidade.csv`. Reexecutado duas vezes em
sequência para checar idempotência: mesmo conteúdo byte a byte (exceto
`data_consulta`, que muda só se o dia mudar).

### Contagens medidas (bbox 33.50,-16.35,34.10,-16.00; 01/mai–31/out; nuvem ≤40%)

> Medidas primeiro com o bbox provisório (`xmax` 33.95) e **reexecutadas** depois de o
> ADR 0001 confirmar `xmax` 34.10. As contagens ficaram **idênticas**: a extensão a leste
> não cruzou fronteira de tile. O CSV publicado corresponde à AOI confirmada.

| ano | landsat-c2-l2 PC | landsat-c2-l2 E84 | sentinel-2-l2a PC | sentinel-2-l2a E84 |
|---|---|---|---|---|
| 2000 | 7 | 7 | n/a (pré-2015) | n/a |
| 2005 | 6 | 6 | n/a | n/a |
| 2010 | 4 | 4 | n/a | n/a |
| 2015 | 19 | 19 | 0 | 0 |
| 2020 | 16 | 16 | 103 | 194 |
| 2025 | 16 | 18 | 162 | 162 |

**Element84 bate exatamente com a medição de referência do orquestrador em
todas as células** (landsat 2000–2025, sentinel 2020/2025). Isso confirma que
o probe está de fato medindo, não inventando.

**Discrepância PC vs. Element84** em landsat 2025 (16 vs. 18) e sentinel
2020 (103 vs. 194): investigado, não forçado. Ambos os endpoints reivindicam
indexar o mesmo dado de origem (USGS Landsat C2 L2 e Copernicus Sentinel-2
L2A em AWS Open Data), mas usam catálogos STAC mantidos separadamente
(Microsoft Planetary Computer vs. Element84/AWS Earth Search) com filtros de
interseção geometria-vs-bbox e políticas de deduplicação de cena
possivelmente distintas — não foi possível confirmar a causa exata sem
inspecionar item a item os `id`s retornados por cada catálogo (fora do
escopo do probe de disponibilidade). **Registro da discrepância, sem
resolução**: para fins de planejamento de composto, usar o **maior** valor
plausível como teto otimista e o **menor** como piso conservador; a
Fase 1 (download real) vai revelar a contagem definitiva ao materializar
os itens.

---

## Viabilidade por ano (composto de mediana de estação seca, §5.1)

Critério de referência: um composto de mediana robusto a nuvem residual e
ruído sensor-a-sensor tipicamente precisa de **≥ 5–8 cenas independentes**
por período; abaixo disso a mediana degenera para poucos valores válidos por
pixel e a robustez cai.

- **2000 (Landsat 7, pré-SLC-off) — 7 cenas.** Suficiente para mediana.
  Sensor único (ETM+), sem falha de linha antes de mai/2003. OK.
- **2005 (Landsat 5) — 6 cenas.** No limite inferior da faixa de referência.
  Aceitável para mediana, mas com menor robustez a outliers de nuvem
  residual do que 2000/2015/2020/2025.
- **2010 (Landsat 5) — 4 cenas.** **Abaixo do piso de referência.** Um
  composto de mediana com 4 observações por pixel tem alta sensibilidade a
  uma única cena ruidosa (path/row parcialmente nublado que passa no filtro
  de 40 % de nuvem de cena inteira mas cobre a AOI com nuvem local). Isso é
  esperado: Landsat 5 tinha revisita de 16 dias e, no fim de sua vida útil
  (2010, antes da falha do SLC em nov/2011), a AOI cai em poucas
  passagens equatoriais dentro de 6 meses de estação seca sem exceder o
  limiar de nuvem.
  **Implicação para `config/study.yaml`:** `composto.janela_anos` está em
  `1` (só o ano-âncora). Se a Fase 1 confirmar que as 4 cenas de 2010 não
  cobrem a AOI inteira sem falha (parte da cena pode estar fora da faixa de
  nuvem aceitável mas ainda assim nublada localmente), **ampliar a janela
  para ±1 ano (2009–2011) especificamente para 2010** é a correção mínima.
  Isso **quebra a uniformidade "mesmo protocolo em todos os anos" do §5.1**
  e exige um **ADR explícito** (`docs/ADR/`) justificando a exceção,
  documentando quantas cenas adicionais a ampliação traria e se alguma delas
  intersecta datas de composto de anos vizinhos (2005, 2015) — o que
  poderia contaminar a independência dos compostos entre anos-âncora. Não
  alterei `config/study.yaml`; a decisão cabe à Fase 1/ADR.
- **2015 (Landsat 8) — 19 cenas.** Landsat 8 tem revisita de 16 dias mas
  operação mais estável; robusto. Sentinel-2 = 0 cenas na AOI: **correto e
  esperado** — S2A foi lançado em jun/2015, primeiras cenas na órbita e
  processamento L2A relevantes só chegam à região depois; não é falha do
  probe, é ausência real de cobertura antes do fim de 2015 nesta AOI.
  Landsat sozinho já é suficiente para 2015.
- **2020 (Landsat 8 + Sentinel-2) — 16 Landsat + 103–194 Sentinel-2.**
  Amplamente suficiente; sobra de cenas Sentinel-2 permite filtro de nuvem
  mais rigoroso que 40 % se necessário na Fase 1.
  **A discrepância PC (103) vs. E84 (194) importa aqui**: mesmo no piso
  (103), a robustez do composto S2 não é comprometida.
- **2025 (Landsat 9 + Sentinel-2) — 16–18 Landsat + 162 Sentinel-2.**
  Suficiente nos dois sensores.

**Resumo:** todos os anos-âncora têm cobertura suficiente para um composto
robusto de mediana de estação seca, **exceto 2010**, que fica no limite
crítico (4 cenas Landsat 5, sem alternativa Sentinel). Recomendação para a
Fase 1: tentar processar 2010 com a janela padrão primeiro; se a validação
visual/quantitativa mostrar artefatos de nuvem residual ou lacunas de dado
válido na AOI, abrir ADR para ampliar `janela_anos` só para 2010 (2009–2011),
registrando explicitamente a quebra de uniformidade do protocolo.

---

## Rota alternativa sem GEE (§11.3) — veredicto

**Viável.** Os dois endpoints STAC candidatos (Planetary Computer e Element84
Earth Search) respondem, cobrem as mesmas coleções (`landsat-c2-l2`,
`sentinel-2-l2a`) e produzem contagens consistentes (idênticas em 6 de 8
comparações possíveis; divergentes, mas ambas com volume suficiente, nas
outras 2). O pipeline de imagem pode ser implementado sobre `pystac-client` +
`odc-stac`/`stackstac` sem depender de uma única plataforma proprietária,
cumprindo §11.3. Element84/AWS Earth Search é recomendado como fonte de
contagem/canônica quando os dois divergem, por bater exatamente com a
medição independente de referência do orquestrador em todas as células
testadas.

---

## Dados não baixados (nível B) — Planet NICFI

Planet NICFI **não foi baixado** (nível B, §4.0). Situação do programa em
2026: o contrato do NICFI Satellite Data Program com a Planet expirou em
janeiro de 2025; acesso a dados de nível 0/1 foi temporariamente estendido
até abril de 2025; em setembro de 2025 o governo norueguês cancelou o
processo de licitação para a próxima fase. **Não há fase nova em operação
em 2026** — o programa está efetivamente descontinuado, com continuidade
incerta. Classificação mantida como **nível B/inacessível na prática**;
registrado em `data/licenses_parts/imagem.md`. Não incorporado ao pipeline
reprodutível; não há script de obtenção em `pipeline/00_fetch/` porque não
há endpoint ativo a consultar.

---

## Arquivos gerados nesta reexecução

- `pipeline/00_fetch/probe_stac.py` — lógica de consulta/paginação/contagem.
- `pipeline/00_fetch/probe_stac.sh` — wrapper (`uv run`), idempotente.
- `data/interim/stac_disponibilidade.csv` — medição bruta (não versionar
  como resultado publicado; é artefato de diagnóstico de Fase 0').

**Próximo passo (Fase 1):** implementar `pipeline/00_fetch/fetch_stac.py`
para baixar cenas de fato via a rota Element84 (ou PC como espelho),
gerar compostos de mediana, e então preencher os registros de proveniência
por composto (URL, coleção, cenas componentes, licença, citação, resolução,
CRS) neste mesmo arquivo.


---

<!-- fonte: data/provenance_parts/imagem_fase1.md -->

# Proveniência — Compostos de Imagem e Índices (Fase 1)

Fragmento gerado por `pipeline/01_imagery/compostos.py`. **Não editar à mão**
— reexecute o script para regenerar. Consolidado em `PROVENANCE.md` por
`scripts/consolidar_registros.py`. Este fragmento é novo e não substitui
`data/provenance_parts/imagem.md` (Fase 0', fechado).

Catálogo STAC canônico: `https://planetarycomputer.microsoft.com/api/stac/v1` (ver `docs/ADR/0004-divergencia-catalogos-stac.md`).

Nenhum processo estocástico: `config/seeds.yaml` não se aplica a este
estágio (mediana não amostra nem sorteia). Determinismo garantido pela
ordenação por `id` dos itens STAC antes da composição.

## Defeito corrigido nesta entrega (Fase 1) e descarte dos produtos anteriores

Os cinco compostos gravados por uma execução anterior desta mesma tarefa
(2000, 2005, 2015, 2020, 2025) foram **descartados e regravados do zero**,
não ajustados. `odc.stac.load` honrava o `nodata: 1` declarado no
`raster:bands` do asset `qa_pixel` (Landsat C2 L2) — e 1 é exatamente o
valor do bit de FILL, não um nodata de fato. Isso trocava todo pixel de
falha real (fill/gap) por `0` na banda carregada, e `0` não tem nenhum bit
de qualidade ruim aceso: a máscara de nuvem/sombra/preenchimento
classificava esses pixels de falha como válidos. O sintoma mais visível
era o composto de 2010 (Landsat 7 SLC-off, medição experimental de
`docs/ADR/0005-...md`): declarava 95,68% dos pixels com as 4 observações
completas e 0% sem nenhuma, quando a contagem correta é 73,36% com as 4
e 0,005% sem nenhuma — bom demais para ser real em cenas SLC-off.

Corrigido via `_stac_common.STAC_CFG_QA_PIXEL_SEM_NODATA` (passado a
`odc.stac.load(..., stac_cfg=...)`, desliga o nodata declarado só para
`qa_pixel`) e uma defesa em profundidade em `mascara_valida_landsat`
(`qa == 0` também é tratado como inválido — 0 nunca é um valor legítimo de
`QA_PIXEL`). Ver `pipeline/tests/test_imagery.py::test_nobs_bate_com_calculo_direto_do_qa_pixel` para o contrato de
regressão (usa as cenas Landsat 7/2010, o único conjunto do repositório
com pixels de fill reais dentro da AOI) e `config/tolerances.yaml ->
regressao_numerica.contrato_qa_pixel` para a tolerância declarada.

Os cinco compostos e todos os índices abaixo foram gerados **depois**
dessa correção — nenhum artefato do defeito permanece em
`data/processed/imagery/`.

## Ano-âncora 2000

- **Arquivo**: `data/processed/imagery/composto_2000_30m_32736.tif`
- **Janela temporal**: `2000-05-01T00:00:00Z/2000-10-31T23:59:59Z` (janela_anos=1)
- **Landsat**: landsat-7, 3 cenas
- **Sentinel-2**: não incluído (fora do complemento do ano ou sem cobertura)
- **Observações válidas por pixel**: mínimo 0, mediana 3.0
- **Pixels sem nenhuma observação válida**: 12 de 2785056 (0.00%)
- **Commit**: `a81ac6b5803ff36a1dfad3dc30efb0fe22da1442`
- **Hash de `config/study.yaml`**: `f6de82755961c660a96ab2e3563b500b784d1680907e53fde54629d684fd5f1a`
- **Data de processamento**: 2026-09-08T14:18:38.641595+00:00
- **Selo**: observado

IDs das cenas Landsat: LE07_L2SP_168071_20000714_02_T1, LE07_L2SP_168071_20000831_02_T1, LE07_L2SP_168071_20001002_02_T1

## Ano-âncora 2005

- **Arquivo**: `data/processed/imagery/composto_2005_30m_32736.tif`
- **Janela temporal**: `2005-05-01T00:00:00Z/2005-10-31T23:59:59Z` (janela_anos=1)
- **Landsat**: landsat-5, 4 cenas
- **Sentinel-2**: não incluído (fora do complemento do ano ou sem cobertura)
- **Observações válidas por pixel**: mínimo 2, mediana 4.0
- **Pixels sem nenhuma observação válida**: 0 de 2785056 (0.00%)
- **Commit**: `a81ac6b5803ff36a1dfad3dc30efb0fe22da1442`
- **Hash de `config/study.yaml`**: `f6de82755961c660a96ab2e3563b500b784d1680907e53fde54629d684fd5f1a`
- **Data de processamento**: 2026-09-08T14:18:56.643286+00:00
- **Selo**: observado

IDs das cenas Landsat: LT05_L2SP_168071_20050517_02_T1, LT05_L2SP_168071_20050720_02_T1, LT05_L2SP_168071_20050906_02_T1, LT05_L2SP_168071_20050922_02_T1

## Ano-âncora 2010

- **Arquivo**: `data/processed/imagery/composto_2010_30m_32736.tif`
- **Janela temporal**: `2010-05-01T00:00:00Z/2010-10-31T23:59:59Z` (janela_anos=1)
- **Landsat**: landsat-7, 4 cenas
- **Sentinel-2**: não incluído (fora do complemento do ano ou sem cobertura)
- **Observações válidas por pixel**: mínimo 0, mediana 4.0
- **Pixels sem nenhuma observação válida**: 130 de 2785056 (0.00%)
- **Commit**: `a81ac6b5803ff36a1dfad3dc30efb0fe22da1442`
- **Hash de `config/study.yaml`**: `f6de82755961c660a96ab2e3563b500b784d1680907e53fde54629d684fd5f1a`
- **Data de processamento**: 2026-09-08T14:19:14.658606+00:00
- **Selo**: observado

IDs das cenas Landsat: LE07_L2SP_168071_20100507_02_T1, LE07_L2SP_168071_20100608_02_T1, LE07_L2SP_168071_20100827_02_T1, LE07_L2SP_168071_20101014_02_T1

## Ano-âncora 2015

- **Arquivo**: `data/processed/imagery/composto_2015_30m_32736.tif`
- **Janela temporal**: `2015-05-01T00:00:00Z/2015-10-31T23:59:59Z` (janela_anos=1)
- **Landsat**: landsat-8, 10 cenas
- **Sentinel-2**: não incluído (fora do complemento do ano ou sem cobertura)
- **Observações válidas por pixel**: mínimo 6, mediana 10.0
- **Pixels sem nenhuma observação válida**: 0 de 2785056 (0.00%)
- **Commit**: `a81ac6b5803ff36a1dfad3dc30efb0fe22da1442`
- **Hash de `config/study.yaml`**: `f6de82755961c660a96ab2e3563b500b784d1680907e53fde54629d684fd5f1a`
- **Data de processamento**: 2026-09-08T14:19:53.314955+00:00
- **Selo**: observado

IDs das cenas Landsat: LC08_L2SP_168071_20150513_02_T1, LC08_L2SP_168071_20150529_02_T1, LC08_L2SP_168071_20150614_02_T1, LC08_L2SP_168071_20150630_02_T1, LC08_L2SP_168071_20150716_02_T1, LC08_L2SP_168071_20150817_02_T1, LC08_L2SP_168071_20150902_02_T1, LC08_L2SP_168071_20150918_02_T1, LC08_L2SP_168071_20151004_02_T1, LC08_L2SP_168071_20151020_02_T1

## Ano-âncora 2020

- **Arquivo**: `data/processed/imagery/composto_2020_30m_32736.tif`
- **Janela temporal**: `2020-05-01T00:00:00Z/2020-10-31T23:59:59Z` (janela_anos=1)
- **Landsat**: landsat-8, 9 cenas
- **Sentinel-2**: 103 cenas
- **Observações válidas por pixel**: mínimo 9, mediana 31.0
- **Pixels sem nenhuma observação válida**: 0 de 2785056 (0.00%)
- **Commit**: `a81ac6b5803ff36a1dfad3dc30efb0fe22da1442`
- **Hash de `config/study.yaml`**: `f6de82755961c660a96ab2e3563b500b784d1680907e53fde54629d684fd5f1a`
- **Data de processamento**: 2026-09-08T14:23:48.798380+00:00
- **Selo**: observado

IDs das cenas Landsat: LC08_L2SP_168071_20200526_02_T1, LC08_L2SP_168071_20200611_02_T1, LC08_L2SP_168071_20200627_02_T1, LC08_L2SP_168071_20200713_02_T1, LC08_L2SP_168071_20200814_02_T1, LC08_L2SP_168071_20200830_02_T1, LC08_L2SP_168071_20200915_02_T1, LC08_L2SP_168071_20201001_02_T1, LC08_L2SP_168071_20201017_02_T1

IDs das cenas Sentinel-2: S2A_MSIL2A_20200503T073621_R092_T36KWG_20200920T071754, S2A_MSIL2A_20200503T073621_R092_T36KXG_20200920T071802, S2A_MSIL2A_20200503T073621_R092_T36LWH_20200920T071815, S2A_MSIL2A_20200503T073621_R092_T36LXH_20200920T071818, S2A_MSIL2A_20200513T073621_R092_T36KWG_20200918T001320, S2A_MSIL2A_20200513T073621_R092_T36KWG_20200918T001335, S2A_MSIL2A_20200513T073621_R092_T36KXG_20200918T001328, S2A_MSIL2A_20200513T073621_R092_T36KXG_20200918T001339, S2A_MSIL2A_20200513T073621_R092_T36LWH_20200918T001337, S2A_MSIL2A_20200513T073621_R092_T36LWH_20200918T001341, S2A_MSIL2A_20200513T073621_R092_T36LXH_20200918T001335, S2A_MSIL2A_20200513T073621_R092_T36LXH_20200918T001350, S2A_MSIL2A_20200523T073621_R092_T36KWG_20200910T155537, S2A_MSIL2A_20200523T073621_R092_T36KXG_20200910T155551, S2A_MSIL2A_20200523T073621_R092_T36LWH_20200910T155602, S2A_MSIL2A_20200523T073621_R092_T36LXH_20200910T155605, S2A_MSIL2A_20200602T073621_R092_T36LWH_20200825T200719, S2A_MSIL2A_20200602T073621_R092_T36LXH_20200825T200721, S2A_MSIL2A_20200622T073621_R092_T36KWG_20200908T190853, S2A_MSIL2A_20200622T073621_R092_T36KXG_20200908T191021, S2A_MSIL2A_20200622T073621_R092_T36LWH_20200908T191748, S2A_MSIL2A_20200622T073621_R092_T36LXH_20200908T191924, S2A_MSIL2A_20200712T073621_R092_T36KWG_20200912T215411, S2A_MSIL2A_20200712T073621_R092_T36KWG_20200912T215421, S2A_MSIL2A_20200712T073621_R092_T36KXG_20200912T215419, S2A_MSIL2A_20200712T073621_R092_T36KXG_20200912T215428, S2A_MSIL2A_20200712T073621_R092_T36LWH_20200912T215438, S2A_MSIL2A_20200712T073621_R092_T36LWH_20200912T215443, S2A_MSIL2A_20200712T073621_R092_T36LXH_20200912T215441, S2A_MSIL2A_20200712T073621_R092_T36LXH_20200912T215450, S2A_MSIL2A_20200722T073621_R092_T36KWG_20200817T020801, S2A_MSIL2A_20200722T073621_R092_T36KXG_20200908T191022, S2A_MSIL2A_20200722T073621_R092_T36LXH_20200817T020828, S2A_MSIL2A_20200801T073621_R092_T36KWG_20201027T083643, S2A_MSIL2A_20200801T073621_R092_T36LWH_20200815T171202, S2A_MSIL2A_20200801T073621_R092_T36LXH_20200908T191927, S2A_MSIL2A_20200811T073621_R092_T36KWG_20200814T184913, S2A_MSIL2A_20200811T073621_R092_T36KXG_20200814T184850, S2A_MSIL2A_20200811T073621_R092_T36LWH_20200814T184841, S2A_MSIL2A_20200811T073621_R092_T36LXH_20200814T184909, S2A_MSIL2A_20200831T073621_R092_T36KWG_20200919T052429, S2A_MSIL2A_20200831T073621_R092_T36LWH_20200907T203302, S2A_MSIL2A_20200831T073621_R092_T36LXH_20200907T203139, S2A_MSIL2A_20200910T073621_R092_T36KWG_20200912T032248, S2A_MSIL2A_20200910T073621_R092_T36KXG_20200912T031437, S2A_MSIL2A_20200910T073621_R092_T36LWH_20200912T031541, S2A_MSIL2A_20200910T073621_R092_T36LXH_20200912T032250, S2A_MSIL2A_20200920T073621_R092_T36KWG_20201027T220553, S2A_MSIL2A_20200920T073621_R092_T36KXG_20201027T214743, S2A_MSIL2A_20200920T073621_R092_T36LWH_20201027T224117, S2A_MSIL2A_20200920T073621_R092_T36LXH_20201027T214710, S2A_MSIL2A_20200930T073721_R092_T36KWG_20201002T080946, S2A_MSIL2A_20200930T073721_R092_T36LXH_20201002T080902, S2A_MSIL2A_20201010T073831_R092_T36KWG_20201012T031508, S2A_MSIL2A_20201010T073831_R092_T36KXG_20201012T032006, S2A_MSIL2A_20201010T073831_R092_T36LWH_20201012T030002, S2A_MSIL2A_20201010T073831_R092_T36LXH_20201027T125105, S2A_MSIL2A_20201020T073941_R092_T36KWG_20201021T210400, S2A_MSIL2A_20201020T073941_R092_T36KXG_20201021T205233, S2A_MSIL2A_20201020T073941_R092_T36LWH_20201021T205550, S2A_MSIL2A_20201020T073941_R092_T36LXH_20201021T205220, S2A_MSIL2A_20201030T074041_R092_T36KWG_20201101T235804, S2A_MSIL2A_20201030T074041_R092_T36KXG_20201102T000300, S2A_MSIL2A_20201030T074041_R092_T36LWH_20201101T235823, S2A_MSIL2A_20201030T074041_R092_T36LXH_20201101T235804, S2B_MSIL2A_20200518T073609_R092_T36KWG_20201027T071120, S2B_MSIL2A_20200518T073609_R092_T36KXG_20200910T032436, S2B_MSIL2A_20200518T073609_R092_T36LWH_20200910T032436, S2B_MSIL2A_20200518T073609_R092_T36LXH_20201027T071121, S2B_MSIL2A_20200607T073619_R092_T36KWG_20200919T052433, S2B_MSIL2A_20200607T073619_R092_T36KXG_20200919T052438, S2B_MSIL2A_20200617T073619_R092_T36KWG_20200823T025222, S2B_MSIL2A_20200617T073619_R092_T36KXG_20201027T074459, S2B_MSIL2A_20200617T073619_R092_T36LWH_20201027T074455, S2B_MSIL2A_20200617T073619_R092_T36LXH_20200823T025229, S2B_MSIL2A_20200627T073619_R092_T36LXH_20200824T082726, S2B_MSIL2A_20200707T073619_R092_T36KXG_20200912T091123, S2B_MSIL2A_20200707T073619_R092_T36LWH_20200912T091124, S2B_MSIL2A_20200707T073619_R092_T36LXH_20201027T081734, S2B_MSIL2A_20200727T073619_R092_T36KWG_20200908T190907, S2B_MSIL2A_20200727T073619_R092_T36KXG_20200817T185010, S2B_MSIL2A_20200727T073619_R092_T36LWH_20200817T185021, S2B_MSIL2A_20200727T073619_R092_T36LXH_20200908T191927, S2B_MSIL2A_20200816T073619_R092_T36KWG_20200818T143332, S2B_MSIL2A_20200816T073619_R092_T36KXG_20200818T143242, S2B_MSIL2A_20200816T073619_R092_T36LWH_20200818T143319, S2B_MSIL2A_20200816T073619_R092_T36LXH_20200818T143328, S2B_MSIL2A_20200826T073619_R092_T36KWG_20200827T221401, S2B_MSIL2A_20200826T073619_R092_T36KXG_20200827T221205, S2B_MSIL2A_20200826T073619_R092_T36LWH_20201027T091234, S2B_MSIL2A_20200826T073619_R092_T36LXH_20200919T052629, S2B_MSIL2A_20200915T073619_R092_T36KWG_20200918T104345, S2B_MSIL2A_20200915T073619_R092_T36KXG_20200918T104323, S2B_MSIL2A_20200915T073619_R092_T36LWH_20200918T104325, S2B_MSIL2A_20200915T073619_R092_T36LXH_20200918T104315, S2B_MSIL2A_20200925T073649_R092_T36KWG_20201104T001607, S2B_MSIL2A_20200925T073649_R092_T36KXG_20201028T072056, S2B_MSIL2A_20200925T073649_R092_T36LWH_20201028T071744, S2B_MSIL2A_20200925T073649_R092_T36LXH_20201028T071754, S2B_MSIL2A_20201025T074009_R092_T36KWG_20201030T090351, S2B_MSIL2A_20201025T074009_R092_T36KXG_20201030T090339, S2B_MSIL2A_20201025T074009_R092_T36LWH_20201030T092504, S2B_MSIL2A_20201025T074009_R092_T36LXH_20201109T233238

## Ano-âncora 2025

- **Arquivo**: `data/processed/imagery/composto_2025_30m_32736.tif`
- **Janela temporal**: `2025-05-01T00:00:00Z/2025-10-31T23:59:59Z` (janela_anos=1)
- **Landsat**: landsat-9, 6 cenas
- **Sentinel-2**: 162 cenas
- **Observações válidas por pixel**: mínimo 32, mediana 42.0
- **Pixels sem nenhuma observação válida**: 0 de 2785056 (0.00%)
- **Commit**: `a81ac6b5803ff36a1dfad3dc30efb0fe22da1442`
- **Hash de `config/study.yaml`**: `f6de82755961c660a96ab2e3563b500b784d1680907e53fde54629d684fd5f1a`
- **Data de processamento**: 2026-09-08T14:29:29.234284+00:00
- **Selo**: observado

IDs das cenas Landsat: LC09_L2SP_168071_20250516_02_T1, LC09_L2SP_168071_20250601_02_T1, LC09_L2SP_168071_20250804_02_T1, LC09_L2SP_168071_20250820_02_T1, LC09_L2SP_168071_20250905_02_T1, LC09_L2SP_168071_20251007_02_T1

IDs das cenas Sentinel-2: S2A_MSIL2A_20250509T074021_R092_T36KWG_20250509T113013, S2A_MSIL2A_20250509T074021_R092_T36KXG_20250509T113013, S2A_MSIL2A_20250509T074021_R092_T36LWH_20250509T113013, S2A_MSIL2A_20250509T074021_R092_T36LXH_20250509T113013, S2A_MSIL2A_20250519T075451_R092_T36KWG_20250519T100916, S2A_MSIL2A_20250608T075451_R092_T36KWG_20250608T100815, S2A_MSIL2A_20250608T075451_R092_T36KXG_20250608T100815, S2A_MSIL2A_20250608T075451_R092_T36LWH_20250608T100815, S2A_MSIL2A_20250608T075451_R092_T36LXH_20250608T100815, S2A_MSIL2A_20250618T074021_R092_T36KWG_20250618T110116, S2A_MSIL2A_20250618T074021_R092_T36KXG_20250618T110116, S2A_MSIL2A_20250618T074021_R092_T36LWH_20250618T110116, S2A_MSIL2A_20250618T074021_R092_T36LXH_20250618T110116, S2A_MSIL2A_20250628T075451_R092_T36KWG_20250628T102909, S2A_MSIL2A_20250628T075451_R092_T36KXG_20250628T102909, S2A_MSIL2A_20250628T075451_R092_T36LWH_20250628T102909, S2A_MSIL2A_20250628T075451_R092_T36LXH_20250628T102909, S2A_MSIL2A_20250708T074031_R092_T36LWH_20250708T112915, S2A_MSIL2A_20250708T074031_R092_T36LXH_20250708T112915, S2A_MSIL2A_20250718T075451_R092_T36KWG_20250718T101120, S2A_MSIL2A_20250718T075451_R092_T36KXG_20250718T101120, S2A_MSIL2A_20250718T075451_R092_T36LWH_20250718T101120, S2A_MSIL2A_20250807T075451_R092_T36KWG_20250807T103914, S2A_MSIL2A_20250807T075451_R092_T36KXG_20250807T103914, S2A_MSIL2A_20250807T075451_R092_T36LWH_20250807T103914, S2A_MSIL2A_20250807T075451_R092_T36LXH_20250807T103914, S2A_MSIL2A_20250817T074021_R092_T36KWG_20250817T110213, S2A_MSIL2A_20250817T074021_R092_T36KXG_20250817T110213, S2A_MSIL2A_20250817T074021_R092_T36LWH_20250817T110213, S2A_MSIL2A_20250817T074021_R092_T36LXH_20250817T110213, S2A_MSIL2A_20250827T075451_R092_T36KWG_20250827T101719, S2A_MSIL2A_20250827T075451_R092_T36KXG_20250827T101719, S2A_MSIL2A_20250827T075451_R092_T36LWH_20250827T101719, S2A_MSIL2A_20250827T075451_R092_T36LXH_20250827T101719, S2A_MSIL2A_20250906T074021_R092_T36KXG_20250906T114026, S2A_MSIL2A_20250906T074021_R092_T36LWH_20250906T114026, S2A_MSIL2A_20250906T074021_R092_T36LXH_20250906T114026, S2A_MSIL2A_20250916T075451_R092_T36KWG_20250916T100824, S2A_MSIL2A_20250916T075451_R092_T36KXG_20250916T100824, S2A_MSIL2A_20250916T075451_R092_T36LWH_20250916T100824, S2A_MSIL2A_20250916T075451_R092_T36LXH_20250916T100824, S2A_MSIL2A_20251006T074031_R092_T36KWG_20251006T112017, S2A_MSIL2A_20251006T074031_R092_T36KXG_20251006T112017, S2A_MSIL2A_20251006T074031_R092_T36LWH_20251006T112017, S2A_MSIL2A_20251006T074031_R092_T36LXH_20251006T112017, S2A_MSIL2A_20251016T075451_R092_T36KWG_20251016T103126, S2A_MSIL2A_20251016T075451_R092_T36KXG_20251016T103126, S2A_MSIL2A_20251016T075451_R092_T36LWH_20251016T103126, S2A_MSIL2A_20251016T075451_R092_T36LXH_20251016T103126, S2A_MSIL2A_20251026T074031_R092_T36KWG_20251026T110418, S2A_MSIL2A_20251026T074031_R092_T36KXG_20251026T110418, S2A_MSIL2A_20251026T074031_R092_T36LXH_20251026T110418, S2B_MSIL2A_20250502T073619_R092_T36KWG_20250502T113003, S2B_MSIL2A_20250502T073619_R092_T36KXG_20250502T113003, S2B_MSIL2A_20250502T073619_R092_T36LWH_20250502T113003, S2B_MSIL2A_20250502T073619_R092_T36LXH_20250502T113003, S2B_MSIL2A_20250522T073619_R092_T36KWG_20250522T095453, S2B_MSIL2A_20250522T073619_R092_T36LWH_20250522T095453, S2B_MSIL2A_20250601T073619_R092_T36KWG_20250601T102230, S2B_MSIL2A_20250601T073619_R092_T36KXG_20250601T102230, S2B_MSIL2A_20250601T073619_R092_T36LWH_20250601T102230, S2B_MSIL2A_20250601T073619_R092_T36LXH_20250601T102230, S2B_MSIL2A_20250611T073609_R092_T36KXG_20250611T112907, S2B_MSIL2A_20250611T073609_R092_T36LWH_20250611T103259, S2B_MSIL2A_20250611T073609_R092_T36LWH_20250611T112907, S2B_MSIL2A_20250611T073609_R092_T36LXH_20250611T103259, S2B_MSIL2A_20250611T073609_R092_T36LXH_20250611T112907, S2B_MSIL2A_20250621T073619_R092_T36KWG_20250621T095930, S2B_MSIL2A_20250621T073619_R092_T36KXG_20250621T095930, S2B_MSIL2A_20250621T073619_R092_T36LWH_20250621T095930, S2B_MSIL2A_20250621T073619_R092_T36LXH_20250621T095930, S2B_MSIL2A_20250731T073609_R092_T36KWG_20250731T100050, S2B_MSIL2A_20250731T073609_R092_T36KXG_20250731T100050, S2B_MSIL2A_20250731T073609_R092_T36LWH_20250731T100050, S2B_MSIL2A_20250731T073609_R092_T36LXH_20250731T100050, S2B_MSIL2A_20250810T073619_R092_T36KWG_20250810T102333, S2B_MSIL2A_20250810T073619_R092_T36KXG_20250810T102333, S2B_MSIL2A_20250810T073619_R092_T36LWH_20250810T102333, S2B_MSIL2A_20250810T073619_R092_T36LXH_20250810T102333, S2B_MSIL2A_20250820T073619_R092_T36KWG_20250820T113111, S2B_MSIL2A_20250820T073619_R092_T36KXG_20250820T113111, S2B_MSIL2A_20250820T073619_R092_T36LWH_20250820T102406, S2B_MSIL2A_20250820T073619_R092_T36LWH_20250820T113111, S2B_MSIL2A_20250820T073619_R092_T36LXH_20250820T102406, S2B_MSIL2A_20250820T073619_R092_T36LXH_20250820T113111, S2B_MSIL2A_20250830T073619_R092_T36KWG_20250830T102143, S2B_MSIL2A_20250830T073619_R092_T36KXG_20250830T102143, S2B_MSIL2A_20250830T073619_R092_T36LWH_20250830T102143, S2B_MSIL2A_20250830T073619_R092_T36LXH_20250830T102143, S2B_MSIL2A_20250909T073609_R092_T36KWG_20250909T102706, S2B_MSIL2A_20250909T073609_R092_T36KXG_20250909T102706, S2B_MSIL2A_20250909T073609_R092_T36LWH_20250909T102706, S2B_MSIL2A_20250909T073609_R092_T36LXH_20250909T102706, S2B_MSIL2A_20250919T073609_R092_T36KWG_20250919T095927, S2B_MSIL2A_20250919T073609_R092_T36LXH_20250919T095927, S2B_MSIL2A_20250929T073619_R092_T36KWG_20250929T102250, S2B_MSIL2A_20250929T073619_R092_T36KXG_20250929T102250, S2B_MSIL2A_20250929T073619_R092_T36LWH_20250929T102250, S2B_MSIL2A_20250929T073619_R092_T36LXH_20250929T102250, S2B_MSIL2A_20251009T073729_R092_T36KWG_20251009T102743, S2B_MSIL2A_20251009T073729_R092_T36KXG_20251009T102743, S2B_MSIL2A_20251009T073729_R092_T36LWH_20251009T102743, S2B_MSIL2A_20251009T073729_R092_T36LXH_20251009T102743, S2B_MSIL2A_20251019T073839_R092_T36KWG_20251019T095556, S2B_MSIL2A_20251019T073839_R092_T36KXG_20251019T095556, S2B_MSIL2A_20251019T073839_R092_T36LWH_20251019T095556, S2B_MSIL2A_20251019T073839_R092_T36LXH_20251019T095556, S2B_MSIL2A_20251029T073939_R092_T36KWG_20251029T114333, S2B_MSIL2A_20251029T073939_R092_T36KXG_20251029T114333, S2B_MSIL2A_20251029T073939_R092_T36LWH_20251029T114333, S2B_MSIL2A_20251029T073939_R092_T36LXH_20251029T114333, S2C_MSIL2A_20250517T073631_R092_T36KWG_20250517T123613, S2C_MSIL2A_20250527T073631_R092_T36KWG_20250527T130031, S2C_MSIL2A_20250527T073631_R092_T36LWH_20250527T130031, S2C_MSIL2A_20250527T073631_R092_T36LXH_20250527T130031, S2C_MSIL2A_20250626T073631_R092_T36KWG_20250626T123815, S2C_MSIL2A_20250626T073631_R092_T36KXG_20250626T123815, S2C_MSIL2A_20250626T073631_R092_T36LWH_20250626T123815, S2C_MSIL2A_20250626T073631_R092_T36LXH_20250626T123815, S2C_MSIL2A_20250706T073641_R092_T36KWG_20250706T124023, S2C_MSIL2A_20250706T073641_R092_T36KXG_20250706T124023, S2C_MSIL2A_20250706T073641_R092_T36LWH_20250706T124023, S2C_MSIL2A_20250706T073641_R092_T36LXH_20250706T124023, S2C_MSIL2A_20250716T073641_R092_T36KWG_20250716T124416, S2C_MSIL2A_20250716T073641_R092_T36KXG_20250716T124416, S2C_MSIL2A_20250716T073641_R092_T36LWH_20250716T124416, S2C_MSIL2A_20250716T073641_R092_T36LXH_20250716T124416, S2C_MSIL2A_20250726T073641_R092_T36KWG_20250726T123415, S2C_MSIL2A_20250726T073641_R092_T36KXG_20250726T123415, S2C_MSIL2A_20250726T073641_R092_T36LWH_20250726T123415, S2C_MSIL2A_20250726T073641_R092_T36LXH_20250726T123415, S2C_MSIL2A_20250805T073631_R092_T36KWG_20250805T110921, S2C_MSIL2A_20250805T073631_R092_T36KXG_20250805T110921, S2C_MSIL2A_20250805T073631_R092_T36LWH_20250805T110921, S2C_MSIL2A_20250805T073631_R092_T36LXH_20250805T110921, S2C_MSIL2A_20250815T073631_R092_T36KWG_20250815T130315, S2C_MSIL2A_20250815T073631_R092_T36KXG_20250815T130315, S2C_MSIL2A_20250815T073631_R092_T36LWH_20250815T130315, S2C_MSIL2A_20250815T073631_R092_T36LXH_20250815T130315, S2C_MSIL2A_20250825T073631_R092_T36KWG_20250825T123913, S2C_MSIL2A_20250825T073631_R092_T36KXG_20250825T123913, S2C_MSIL2A_20250825T073631_R092_T36LWH_20250825T123913, S2C_MSIL2A_20250825T073631_R092_T36LXH_20250825T123913, S2C_MSIL2A_20250904T073631_R092_T36KWG_20250904T124917, S2C_MSIL2A_20250904T073631_R092_T36KXG_20250904T124917, S2C_MSIL2A_20250904T073631_R092_T36LWH_20250904T124917, S2C_MSIL2A_20250904T073631_R092_T36LXH_20250904T124917, S2C_MSIL2A_20250914T073631_R092_T36KWG_20250914T141320, S2C_MSIL2A_20250914T073631_R092_T36KXG_20250914T141320, S2C_MSIL2A_20250914T073631_R092_T36LWH_20250914T141320, S2C_MSIL2A_20250914T073631_R092_T36LXH_20250914T141320, S2C_MSIL2A_20250924T073651_R092_T36KWG_20250924T130114, S2C_MSIL2A_20250924T073651_R092_T36KXG_20250924T130114, S2C_MSIL2A_20250924T073651_R092_T36LWH_20250924T130114, S2C_MSIL2A_20250924T073651_R092_T36LXH_20250924T130114, S2C_MSIL2A_20251014T073911_R092_T36KWG_20251014T111716, S2C_MSIL2A_20251014T073911_R092_T36KXG_20251014T111716, S2C_MSIL2A_20251014T073911_R092_T36LWH_20251014T111716, S2C_MSIL2A_20251014T073911_R092_T36LXH_20251014T111716, S2C_MSIL2A_20251024T074011_R092_T36KWG_20251024T110917, S2C_MSIL2A_20251024T074011_R092_T36KXG_20251024T110917, S2C_MSIL2A_20251024T074011_R092_T36LXH_20251024T110917

<!-- SECAO_CLASSIFICACAO_INICIO -->

## Classificação — redesenho da Fase 1 (§5.1, §10)

Gerado por `pipeline/01_imagery/classificacao.py`. Substitui a versão reprovada, cujo defeito central era usar **limiares adaptativos por percentil**: eles selecionavam uma fatia quase constante da AOI todo ano (3,4–4,4%), de modo que o produto media o percentil, não o crescimento.

**Papéis das referências (escolhidos e assumidos, sem circularidade):** WSF Evolution **semeia o treino** e por isso **não** é usado como validação; GHSL BUILT-S R2023A (épocas observadas 2000–2020) é **referência independente de concordância** e não toca em treino nem em limiar; as épocas 2025/2030 do GHSL são extrapoladas e por isso 2025 fica **sem** referência de produto, declarado.

**Separação fenológica.** Features incluem `NDVI(chuva)` e a amplitude `NDVI(chuva) − NDVI(seca)` (nov(A−1)–abr(A) contra mai–out(A)). Separabilidade medida nesta AOI entre WSF-construído e não-construído (d de Cohen): amplitude 1,83 (2000) / 2,03 (2015) / 1,87 (2025); NDBI 0,39 / 0,71 / 0,29. Cobertura da estação chuvosa por ano em `data/processed/cobertura_estacao_chuvosa.csv`.

**Regras temporais declaradas.** R1: primeira detecção só vale se confirmada no ano-âncora seguinte (2025 não é confirmável — não há ano seguinte). R2: permanência, `construído(t) = ∪_{t'≤t}`. As três séries (sem restrição, após R1, após R2) estão lado a lado em `data/processed/area_construida_por_ano.csv`.

**Acurácia não é calculada aqui.** Ver `pipeline/01_imagery/acuracia.py` e `data/processed/acuracia_por_ano.csv`.

**Pegada minerária e de reassentamento — classe própria desde docs/ADR/0011.** Antes, `industrial` era `construido & poligono_maus` e `reassentamento` era `restante & buffer`: as duas camadas eram a INTERSEÇÃO da classificação de construído com uma máscara espacial, e mediam 'construído dentro do polígono', não a pegada. O defeito é físico: cava, pilha de estéril e rejeito são rocha e solo exposto — espectralmente NÃO são construído — e um classificador de construído os perde por definição (media 4,2 km² contra os 59,2 km² de Maus et al., 7,1%). A pegada passou a ser classificada por assinatura própria: solo/rocha exposto persistente (NDVI de seca E de chuva abaixo de 0.6 da mediana da paisagem do próprio ano — normalização radiométrica anual, NÃO percentil da imagem), unida ao construído do ano, dentro do envelope de Maus dilatado em 500 m. Cobertura dos polígonos de Maus em 2025: de 7,1% para 76,3%.

**Limiar calibrado, e onde isso cria circularidade.** O limiar foi calibrado por J de Youden contra Maus et al. em 2020, o ano-âncora de menor defasagem em relação à referência. Logo **a concordância com Maus em 2020 não é validação independente**. A evidência independente é temporal: a mesma regra devolve **0,000 km² em 2000 e 2005**, antes da licença da Vale (2006) — placebo temporal que se mantém nas 30 configurações de `data/processed/pegada_sensibilidade.csv`.

**`industrial` e `reassentamento` NÃO são subconjuntos de `construido`.** Elas incluem rocha e solo exposto. Consequência aritmética: `urbano + industrial + reassentamento > area_construida`, e **só `urbano` é área construída** — a soma das três não tem significado. A máscara de construído é publicada à parte, em `construido_<ano>_30m_32736.tif`, e é ela que define o estrato da validação de acurácia.

**O que não mudou, verificado e não presumido:** a classificação de construído é idêntica à anterior (o raio de exclusão de negativos do treino foi mantido em 1500 m, separado do raio de detecção de 1000 m); os 288 pontos de validação não se moveram (0 de 288); `data/processed/acuracia_por_ano.csv` é idêntico por diff e a acurácia do usuário de `construido` continua 0,286-0,625 (docs/ADR/0009); `urbano` dentro dos polígonos de mineração continua 0,0000 km² de 2010 em diante. O único efeito sobre `urbano` é a migração de construído do envelope minerário (planta, pátio ferroviário) para `industrial`: 44,02 -> 42,84 km² em 2025.

**Camada de reassentamento — incompleta por falta de dado:** Buffer de 1000 m em torno do ponto único de cada povoado (não há polígono de traçado real de nível A) delimitando ONDE PROCURAR. Dentro dele a camada é a pegada: solo exposto persistente (mesma regra e mesmo limiar razao_verde < 0.6 da pegada minerária) em união com o construído do ano. **A detecção não exige assinatura de construído** — foi esse o defeito corrigido: habitação de reassentamento é baixa, esparsa e de telhado metálico ou fibrocimento, e a 30 m um classificador de construído a perde (a camada anterior media 0,07 km², cerca de um décimo do piso plausível). **O que a camada mede é a pegada do povoado — lotes, vias e terreno alterado — não a área de telhado.** **A camada continua incompleta e isso é estrutural, não um bug**: o povoado urbano '25 de Setembro' (289 famílias, HRW 2013) tem `geometry: null` em data/raw/reassentamentos.geojson — Nominatim e Overpass não o localizaram e a coordenada não foi inventada. Consequência aritmética: o construído do 25 de Setembro está contado dentro de `urbano`, isto é, `urbano` inclui crescimento por reassentamento que §10 manda separar. A magnitude desse vazamento não é estimável sem a geometria.

### Ano-âncora 2000

- **Método `industrial`:** classe própria de solo/rocha exposto persistente (razao_verde < 0.6) dentro do envelope de Maus et al. dilatado em 500 m, união com o construído do ano no mesmo envelope. Resultado 0,00 km²: PLACEBO TEMPORAL — a concessão da Vale é de 2004 e a licença de 2006, então a regra tinha de devolver ~zero aqui, e devolve. Sem acumulação (anterior a 2006).
- **Área construída (km²):** sem restrição 16.9 · após R1 13.8 · após R2 (publicada) 13.8
- **Camadas (km²):** urbano=13.81, industrial=0.00, reassentamento=0.00, vegetacao=235.34, solo_exposto=2219.66, agua=30.34 (industrial e reassentamento são PEGADAS, não subconjuntos de construído)
- **Pegada sem permanência (km²):** industrial=0.00, reassentamento=0.00 · cobertura dos polígonos de Maus: 0.0% · mediana NDVI(chuva) da paisagem: 0.474
- **Importância das features (5 maiores):** ndvi=0.482, evi=0.171, ndwi=0.107, ndbi=0.050, nir=0.039

### Ano-âncora 2005

- **Método `industrial`:** mesma regra de 2000. Resultado 0,00 km²: segundo ponto do placebo temporal, um ano antes da licença. Sem acumulação (anterior a 2006).
- **Área construída (km²):** sem restrição 23.6 · após R1 20.5 · após R2 (publicada) 20.5
- **Camadas (km²):** urbano=20.48, industrial=0.00, reassentamento=0.00, vegetacao=239.83, solo_exposto=2202.24, agua=31.94 (industrial e reassentamento são PEGADAS, não subconjuntos de construído)
- **Pegada sem permanência (km²):** industrial=0.00, reassentamento=0.00 · cobertura dos polígonos de Maus: 0.0% · mediana NDVI(chuva) da paisagem: 0.543
- **Importância das features (5 maiores):** ndvi=0.441, evi=0.190, ndwi=0.106, ndbi=0.045, red=0.040

### Ano-âncora 2010

- **Método `industrial`:** solo/rocha exposto persistente + construído, dentro do envelope, acumulado desde 2006. Obras desde ~2007; a mina só opera em mai/2011, então a pegada aqui é de decapagem e canteiro, não de lavra plena.
- **Área construída (km²):** sem restrição 33.3 · após R1 28.9 · após R2 (publicada) 29.9
- **Camadas (km²):** urbano=28.16, industrial=7.43, reassentamento=1.20, vegetacao=254.31, solo_exposto=2168.11, agua=36.83 (industrial e reassentamento são PEGADAS, não subconjuntos de construído)
- **Pegada sem permanência (km²):** industrial=7.43, reassentamento=1.20 · cobertura dos polígonos de Maus: 7.0% · mediana NDVI(chuva) da paisagem: 0.477
- **Importância das features (5 maiores):** ndvi=0.369, ndwi=0.150, evi=0.141, red=0.072, ndbi=0.053

### Ano-âncora 2015

- **Método `industrial`:** solo/rocha exposto persistente + construído, dentro do envelope, acumulado desde 2006. Operação da Vale desde 2011 e Benga desde 2012. O envelope vem de imagem 2017-2019, POSTERIOR a este ano: parte dele ainda não era lavra em 2015, e é por isso que a extensão é medida pela assinatura do ano e não pelo polígono.
- **Área construída (km²):** sem restrição 55.6 · após R1 39.6 · após R2 (publicada) 41.7
- **Camadas (km²):** urbano=37.28, industrial=31.55, reassentamento=1.65, vegetacao=139.82, solo_exposto=2247.47, agua=37.27 (industrial e reassentamento são PEGADAS, não subconjuntos de construído)
- **Pegada sem permanência (km²):** industrial=31.55, reassentamento=1.65 · cobertura dos polígonos de Maus: 45.9% · mediana NDVI(chuva) da paisagem: 0.670
- **Importância das features (5 maiores):** ndvi=0.336, ndwi=0.153, evi=0.118, red=0.072, mndwi=0.068

### Ano-âncora 2020

- **Método `industrial`:** solo/rocha exposto persistente + construído, dentro do envelope, acumulado desde 2006. Defasagem de ~1 ano em relação à referência — é neste ano que o limiar foi calibrado, e por isso a concordância com Maus em 2020 não é validação independente.
- **Área construída (km²):** sem restrição 42.0 · após R1 38.6 · após R2 (publicada) 44.3
- **Camadas (km²):** urbano=39.46, industrial=41.49, reassentamento=0.70, vegetacao=302.44, solo_exposto=2074.27, agua=39.96 (industrial e reassentamento são PEGADAS, não subconjuntos de construído)
- **Pegada sem permanência (km²):** industrial=41.49, reassentamento=0.70 · cobertura dos polígonos de Maus: 59.2% · mediana NDVI(chuva) da paisagem: 0.579
- **Importância das features (5 maiores):** ndvi=0.413, evi=0.176, ndwi=0.118, ndbi=0.053, red=0.042

### Ano-âncora 2025

- **Método `industrial`:** solo/rocha exposto persistente + construído, dentro do envelope, acumulado desde 2006. Defasagem de ~6 anos: o envelope dilatado em 500 m admite avanço de lavra posterior a 2019, mas expansão além dessa faixa fica fora e é subestimação declarada.
- **Área construída (km²):** sem restrição 39.6 · após R1 39.6 · após R2 (publicada) 50.3
- **Camadas (km²):** urbano=43.10, industrial=56.68, reassentamento=1.09, vegetacao=298.46, solo_exposto=2060.72, agua=41.22 (industrial e reassentamento são PEGADAS, não subconjuntos de construído)
- **Pegada sem permanência (km²):** industrial=56.68, reassentamento=1.09 · cobertura dos polígonos de Maus: 70.5% · mediana NDVI(chuva) da paisagem: 0.331
- **Importância das features (5 maiores):** ndvi=0.347, evi=0.238, ndwi=0.134, ndbi=0.061, swir22=0.048

<!-- SECAO_CLASSIFICACAO_FIM -->

<!-- SECAO_ACURACIA_INICIO -->

## Validação de acurácia (Fase 1, §5.1 e §10)

Gerado por `pipeline/01_imagery/acuracia.py`. **Não editar à mão.**

**Natureza do rótulo de referência.** Os 288 pontos (24 por estrato por ano, 6 anos) foram rotulados por **interpretação visual automatizada** de recortes RGB (R=SWIR1, G=NIR, B=vermelho) do composto de estação seca do próprio ano, em duas janelas por ponto — contexto de 3,0 km e detalhe de 0,9 km, a 30 m. O intérprete é um **modelo de linguagem multimodal**, não um intérprete humano treinado e não verdade de campo. **Isto não é fotointerpretação** e não é chamado assim em nenhum artefato. O erro do intérprete entra no número como se fosse erro do mapa; a 30 m, construído esparso e solo exposto são frequentemente indistinguíveis para qualquer intérprete.

**Cegamento.** As folhas de contato exibem `id_cego`, atribuído sobre uma permutação determinística que mistura os dois estratos. O intérprete não sabia, ao olhar o recorte, se o mapa classificava aquele pixel como construído. Sem isso a concordância mediria a pista, não a imagem.

**Estimador.** Olofsson et al. (2014) generalizado para **reúso da amostra sob o desenho congelado** (docs/ADR/0014): os estratos e os pesos `W_h` são os do mapa vigente **na época do sorteio** (`amostra_interpretada.csv`), e a classe do mapa **atual** em cada ponto é lida do raster do ano. Quando os dois mapas coincidem, a expressão colapsa na eq. 4 de Olofsson. **Consequência declarada:** a amostra não foi otimizada para os estratos do mapa atual, e o número correto de fazer depois de uma reclassificação é uma NOVA rodada de interpretação sobre `pontos_validacao.csv` (que já foi redesenhado e está sem rótulo). Até lá, este é um estimador não viesado mas de variância subótima para o mapa vigente.

**Intérprete(s):** Claude (modelo multimodal, Anthropic) — interpretação visual de recortes RGB; NÃO é fotointerpretação humana nem verdade de campo

| ano | n | AG | IC95 AG | kappa | AU construído | IC95 AU | AP construído | IC95 AP | indet. | W construído | alavanca de 1 ponto |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 2000 | 48 | 0.997 | ±0.001 | 0.665 | 0.524 | ±0.218 | 0.917 | ±0.160 | 1 | 0.0056 | 0.0414 |
| 2005 | 48 | 0.997 | ±0.002 | 0.755 | 0.609 | ±0.204 | 1.000 | ±0.000 | 0 | 0.0083 | 0.0413 |
| 2010 | 48 | 0.992 | ±0.002 | 0.442 | 0.286 | ±0.198 | 1.000 | ±0.000 | 4 | 0.0118 | 0.0449 |
| 2015 | 48 | 0.951 | ±0.084 | 0.239 | 0.591 | ±0.210 | 0.164 | ±0.273 | 1 | 0.0155 | 0.0428 |
| 2020 | 48 | 0.868 | ±0.133 | 0.073 | 0.476 | ±0.218 | 0.055 | ±0.060 | 1 | 0.0165 | 0.0410 |
| 2025 | 48 | 0.993 | ±0.004 | 0.766 | 0.625 | ±0.198 | 1.000 | ±0.000 | 0 | 0.0193 | 0.0409 |

AG = acurácia global · AU = acurácia do usuário (1 − comissão) · AP = acurácia do produtor (1 − omissão).

**Como ler estes números, e como não ler.**

1. A **acurácia global** cumpre a meta de §10 (≥ 0,85) em todos os anos, mas essa comparação é fraca aqui: o estrato `nao_construido` ocupa 98–99,5 % da AOI, e um mapa que errasse *toda* a classe construída ainda teria acurácia global ≈ 0,98. A meta de §10 não discrimina neste desenho.
2. O que informa sobre a classe de interesse é a **acurácia do usuário**: 0,286–0,625. Cerca de metade dos pixels que o mapa chama de construído não parecem construídos ao intérprete — **comissão alta e consistente**, pior em 2010. É coerente com o viés já documentado no ADR 0008 e com a confusão solo exposto × construído na savana semiárida em estação seca.
3. A **acurácia do produtor não é utilizável neste n**. A coluna `alavanca de 1 ponto` é a fração da área da AOI que **um único** ponto de referência do estrato `nao_construido` carrega no estimador (≈ 0,041). Em 2020, 3 pontos desse estrato foram lidos como construídos, o que projeta ~12 % da AOI como construído não mapeado — implausível. O valor de 0,07 mede a fragilidade do desenho, não o mapa.
4. O **kappa** cai a 0,09–0,23 em 2015 e 2020 e não atinge a meta de 0,70 em 2010, 2015 e 2020. Kappa é instável para classe rara; é reportado por exigência de §5.1, não como critério.

**O que seria preciso para estreitar o intervalo.** O IC da acurácia global chega a ±0,133 (2020). A largura é dominada pelo estrato `nao_construido`, cuja variância escala com `W²/n`. Levar o IC de 2020 de ±0,13 para ±0,03 exigiria ~n=24 → ~n=470 pontos nesse estrato **por ano** (o IC escala com 1/√n), isto é, cerca de 2 800 recortes interpretados um a um em vez de 288. Isso não é atingível por interpretação neste ambiente; seria atingível com verdade de campo, com imagem de resolução submétrica (fora do nível A), ou aceitando um rotulador automático — que é exatamente o que reprovou a versão anterior.

**Papel do WSF Evolution.** Semeia o treino; por construção **não valida**. Nenhuma métrica contra WSF aparece em `acuracia_por_ano.csv`. A concordância está em `data/processed/concordancia_wsf.csv`, rotulada como concordância entre produtos com dependência por construção.

<!-- SECAO_ACURACIA_FIM -->


---

<!-- fonte: data/provenance_parts/metricas_fase2.md -->

<!-- SECAO_METRICAS_FASE2_INICIO -->
## Forma urbana (§5.2, Fase 2)

Scripts: `pipeline/02_metrics/area_cagr.py`, `fragmentacao.py`,
`tipologia_expansao.py`, `edificacoes.py`, consolidados em
`write_stats_forma_urbana.py` -> `data/interim/stats_forma_urbana.csv` ->
`stats_by_year_by_unit.py` -> `data/processed/stats_by_year_by_unit.csv`
(familia `forma_urbana`). Gerado em 2026-09-08.

### Duas séries, dois papéis (ADR 0008) — não misturar

- **Série de tendência (área, CAGR)**: WSF Evolution (DLR), nível A, ano de
  primeira detecção por pixel, 1985-2015. Único produto usado para "quanto
  cresceu e a que taxa". Cobre `tete`, `moatize`, `cateme`, `mwaladzi`; não
  cobre `industrial` (WSF é assentamento, não uso do solo) nem 2015->2020 ou
  2020->2025 (fim da série do WSF nesta entrega — linhas ausentes, não
  aproximadas).
- **Série de decomposição por camada**: classificação própria (Random Forest,
  protocolo único, 6 anos-âncora), nível A (Landsat/Sentinel via STAC). Única
  fonte que separa `urbano`/`industrial`/`reassentamento`. Toda área e
  fragmentação desta série é marcada `confiavel_para_tendencia=False` e
  carrega a acurácia do usuário medida em `data/processed/acuracia_por_ano.csv`
  (0,286-0,625, ADR 0009): 37,5%-71,4% do que o mapa chama de construído não é.
  Direção de expansão e tipologia (infill/borda/leapfrog) são declaradas
  robustas a essa comissão (um falso positivo disperso tende a virar
  "leapfrog" de baixa densidade, não inventa infill onde não há nada) — teto,
  não medida limpa, para a proporção de leapfrog.

### Intensidade de uso (área/população) — NÃO calculada

Não há série de população por unidade e por ano compatível com o polígono de
núcleo urbano usado aqui (ver `demografia_fase2.md`: só dois pontos por
unidade, 2017 observado e 2025 modelado, geografia de distrito/cidade
administrativa, não do núcleo mapeado). Cruzar área com essa população
misturaria duas geografias incomparáveis — não publicado. Pendência aberta.

### Rosa de expansão

Setores: 16 x 22,5°, 0°=Norte, sentido horário, a partir do **centróide do
construído em t0 da própria unidade** (não do ponto-sede fixo) — a origem
muda a cada período porque a mancha muda. Estatística de Rayleigh
(`direcao_expansao_graus`, `concentracao_direcional_r`) mais o histograma
completo por setor (`frac_novo_setor_00`...`frac_novo_setor_15`), fração dos
pixels novos do período em cada setor — é o dado que o app precisa para
desenhar a rosa, não só o resumo escalar. Fonte por período: WSF até 2015,
classificação própria em 2015->2020 e 2020->2025 (mesma regra de ADR 0008).
Direção é declarada robusta à comissão (mesmo raciocínio da tipologia).

### Fragmentação (`pylandstats` 3.1.0)

`n_manchas`, `area_media_manchas_km2`, `largest_patch_index_pct`,
`densidade_borda_m_ha`, `indice_forma_medio`, por camada (`urbano`,
`industrial`, `reassentamento`) e ano-âncora, landscape binário res=30 m,
vizinhança 8-conexa (padrão do pacote). Roda sobre a classificação própria —
único produto com as três camadas separadas — logo **sensível à comissão**:
comissão tende a inflar `n_manchas`/`densidade_borda` e a deprimir
`area_media_manchas_km2`/`largest_patch_index_pct` (sal-e-pimenta residual
mesmo após o filtro de coerência 3x3 da classificação); direção do viés
declarada, magnitude não.

### Densidade de edificações e regularidade da malha (§5.2 item 5)

**Fonte obtida**: Google Open Buildings v3, nível A, acesso anônimo
confirmado nesta rodada — `pipeline/00_fetch/fetch_open_buildings.py`
(idempotente, streaming do bloco S2-nível-4 `193` que cobre a AOI, ~1 GB
original, filtrado linha a linha pelo bbox de `config/study.yaml`, nunca
gravado inteiro em disco). Resultado: 268.942 edificações dentro da AOI em
`data/raw/open_buildings_v3_aoi.csv` (66.894.584 bytes), hash em
`open_buildings_v3_aoi.csv.sha256` (`d4085d...` — ver `.meta.json` para o
valor completo e `size_bytes` medido), confiança mínima observada no recorte
0,65 (mesmo piso recomendado pelo produtor para esta versão).

**O que foi calculado**: `pipeline/02_metrics/edificacoes.py` atribui cada
edificação ao ponto-sede mais próximo (mesma partição de Voronoi das outras
métricas) e reporta, por unidade: `n_edificacoes`,
`densidade_edificacoes_km2` (denominador = área construída da classificação
própria, ano 2020, com a mesma ressalva de comissão da série de decomposição),
`area_media_edificacao_m2`, `regularidade_tamanho_cv` (coeficiente de
variação da área das edificações) e `regularidade_espacamento_cv`
(coeficiente de variação da distância ao vizinho mais próximo). CV baixo em
tamanho e espaçamento é lido como proxy de malha planejada/formal; CV alto,
como proxy de crescimento espontâneo/informal — leitura indireta, não uma
classificação formal/informal validada em campo. Todas as linhas usam
`ano=2023` como aproximação do epoch de aquisição da imagem (Google não
publica data de captura por edifício nesta AOI) e não constituem série
temporal.

**O que NÃO foi calculado, e por quê**: a tarefa pede "densidade de
edificações e regularidade da malha (Open Buildings **+ OSM**)". Este
repositório não tem um extrator de rede viária OSM — o único script OSM
existente (`fetch_osm_reassentamentos.sh`) resolve pontos-sede de povoados de
reassentamento, não vias. Construir e validar um fetch de malha viária (Overpass
ou extrato .pbf) está fora do escopo desta entrega; simular esse componente
sem dado real violaria a proibição de inventar disponibilidade. A regularidade
publicada é, portanto, um **proxy parcial**, só de geometria de edificação —
declarado em `nota` de cada linha, não escondido.

### Selos e nível de fonte

Toda linha de `forma_urbana` tem selo `observado` (WSF, classificação própria
e Open Buildings são todos produtos de detecção sobre imagem, não projeção) e
`nivel_fonte=A`. Nenhuma linha é `modelado` nesta família — se uma extensão
futura extrapolar tendência para anos sem imagem, o selo muda ali, não aqui.

### Sensibilidade à cobertura de observações de 2010 (SLC-off)

2010 usa Landsat 7 SLC-off (`docs/ADR/0005`): 26,64% dos pixels da AOI têm
menos de 4 observações válidas no composto de estação seca
(`data/interim/slc_off_2010_cobertura.csv`). Toda linha derivada da
classificação própria de 2010, ou de um período que usa 2010 como início ou
fim (fragmentação 2010; tipologia/rosa 2005->2010 e 2010->2015; decomposição
de área por camada em 2010), carrega essa nota no CSV — cobertura desigual
pode inflar heterogeneidade espacial espúria (mais manchas, mais densidade de
borda, tipologia mais "recortada") independentemente da comissão do
classificador. As linhas de **tendência (WSF)** não são afetadas porque não
dependem do composto próprio.

### Restrições herdadas propagadas

- **Nenhuma cava de mina conta como `urbano`**: a camada `industrial` é
  exclusiva e a série do WSF exclui explicitamente o polígono de mineração
  (Maus et al. 2022) + 150 m de guarda antes de atribuir pixels a
  tete/moatize/cateme/mwaladzi (`_common.mascara_exclusao_industrial`).
- **"25 de Setembro" (`geometry: null`)**: toda linha de `moatize` que soma
  pixels ou edificações de `urbano`/`assentamento_wsf`/`edificacoes` carrega a
  nota de que a magnitude do reassentamento embutido não é estimável —
  propagada em `area_cagr.py`, `write_stats_forma_urbana.py` e
  `edificacoes.py`.

### Suficiência para §1

- **Pergunta 4 (forma de urbanização — compacta/dispersa, infill/borda/
  leapfrog, eixos)**: respondível em nível A para 2000-2015 (WSF) e
  parcialmente para 2015-2025 (classificação própria, com a ressalva de
  comissão). Direção e tipologia são as métricas mais robustas desta
  entrega.
- **Pergunta 4 (formal vs. informal)**: só parcialmente respondível — o proxy
  de regularidade cobre um epoch único (~2023) e não tem o componente de
  malha viária OSM; não permite comparar formal/informal ao longo do tempo,
  só descrever o padrão atual.
<!-- SECAO_METRICAS_FASE2_FIM -->

---

## RESSALVA DE CHURN — acrescentada em 2026-09-08 (`docs/ADR/0013`)

O bloco "Duas séries, dois papéis" acima atribui a robustez da **direção de expansão** e da
**tipologia infill/borda/leapfrog** apenas ao viés de comissão de `docs/ADR/0009`. **Faltava
a ressalva mais séria.**

`docs/ADR/0013` mediu, para a camada `urbano`, um **churn de identidade pixel a pixel de 31 a
54 %** entre anos-âncora consecutivos. A leitura correta é: **a área é utilizável; a
localização não.**

Isso atinge, nominalmente, toda métrica que dependa de **qual** pixel mudou:

| métrica | efeito |
|---|---|
| tipologia infill / borda / leapfrog | a classificação de um pixel novo como infill ou leapfrog depende de onde estava a mancha no ano anterior — e até 54 % dos pixels da mancha anterior não são os mesmos |
| matriz de transição entre classes | idem: a transição é definida pelo par de rótulos do mesmo pixel em dois anos |
| rosa de expansão | menos afetada: agrega por setor angular, e o churn é aproximadamente isotrópico dentro do setor |
| área, CAGR, fragmentação agregada | não afetadas por churn de identidade, apenas pela comissão de `docs/ADR/0009` |

**Consequência prática:** nenhuma proporção de tipologia deste fragmento sustenta afirmação
sobre *onde* a cidade cresceu num par de anos específico. O que resta defensável é a
**tendência agregada** ao longo da série inteira, e ainda assim com a comissão declarada.

Contrato que impede a reincidência:
`pipeline/tests/test_coerencia_hipoteses.py::test_metricas_por_pixel_carregam_a_ressalva_de_churn`.


---

<!-- fonte: data/provenance_parts/osm_vias_lugares.md -->

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


---

<!-- fonte: data/provenance_parts/populacao_vila_moatize.md -->

<!-- SECAO_POPULACAO_VILA_MOATIZE_INICIO -->
## População da Vila de Moatize — estimativa dasimétrica de terceiros (§3, §5.3)

Script: `pipeline/02_metrics/populacao_vila_moatize.py`.
Gerado em 2026-09-09.
Correção de enquadramento em `docs/ADR/0017`: a banda deixou de ser composta só por
variantes atenuadas por máscara de construído — a única variante que valida em Cidade
de Tete (partição de Voronoi sem peso de construído) passou de "diagnóstico não
publicável" a TETO da banda.

### Por que este número não vem do HDX/INE

O HDX COD-PS só publica população por ADM2 (Distrito de Moatize). A Vila de Moatize é
ADM3 e não tem contagem oficial isolada em nenhuma fonte localizada (nível A ou B).

### O que a validação cruzada em Cidade de Tete mostrou (leia isto antes da tabela)

Nenhuma forma de aplicar a máscara de construído recupera o observado
(307338, HDX COD-PS 2017) — nem o multiplicador de fração
(classificação própria: -40.4%; GHSL: -74.5%), nem
a pertença binária (fração > 0: -25.2%; fração ≥ mediana das células
presentes: -50.4%). O GRID3 v1.1 já é um produto dasimétrico calibrado ao
Censo 2017: pesá-lo de novo por uma máscara de construído própria restringe a população
**duas vezes**, descartando gente que o produtor já havia colocado onde ela está. A única
variante que reproduz o observado é a partição espacial (Voronoi por sede mais próxima)
**sem nenhum peso de construído**: +1.6%. O que funciona é particionar,
não pesar.

### Banda — piso e teto (nenhum valor central)

| variante | tipo | estimativa (hab.) | desvio em Tete |
|---|---|---|---|
| classificação própria (fração) | restrita | 29009 | -40.4% |
| GHSL BUILT-S 2020 (fração) | restrita | 15192 | -74.5% |
| pertença binária (fração > 0) | restrita | 40444 | -25.2% |
| pertença por mediana (quantil, ADR 0014) | restrita | 24630 | -50.4% |
| **sem peso de construído (cluster inteiro)** | **TETO** | **69301** | **+1.6%** |
| **piso publicado** | menor das restritas | **15192** | — |

Leitura: **piso** (15192) restringe ao construído e, pela validação em
Tete, perde entre 25% e 74% das pessoas que o GRID3 lá coloca — limite
INFERIOR.
**teto** (69301) soma o GRID3 no cluster de Voronoi inteiro, sem peso de
construído — inclui a área rural do cluster atribuída à sede mais próxima, logo é
limite SUPERIOR para a vila, não a vila propriamente. Nenhuma das cinco variantes é
publicada como "a estimativa"; cada uma é nomeada em
`populacao_vila_moatize_sensibilidade.csv`.

Ano de referência: 2017 (calibração do GRID3). Um único ponto — não há série, não há
CAGR. Selo `modelado`, nível de fonte `A` (GRID3 é CC BY 4.0, produtor institucional
WorldPop/Southampton — ver `data/provenance_parts/worldpop_grid3.md`), mas **não é
contagem**: é estimativa dasimétrica de terceiros sobre uma grade já modelada.

### Validação cruzada em Cidade de Tete — tabela completa

O mesmo procedimento aplicado a Cidade de Tete, comparado contra os
307338 habitantes observados (HDX COD-PS 2017, nível A):

| variante | estimativa (hab.) | desvio frente ao observado |
|---|---|---|
| classificação própria (fração) | 183036 | -40.4% |
| GHSL BUILT-S 2020 (fração) | 78512 | -74.5% |
| pertença binária (fração > 0) | 229867 | -25.2% |
| pertença por mediana (quantil) | 152462 | -50.4% |
| sem peso de construído (teto) | 312300 | +1.6% |

Este desvio — não um limiar de aprovação — é a medida de quanto confiar na estimativa da
Vila de Moatize, que usa exatamente o mesmo método sem ter uma âncora observada própria
contra a qual se comparar. Publicado mesmo se grande: **toda variante restrita por
construído SUBESTIMA** a população observada de Cidade de Tete; só a partição sem peso
não subestima. **A estimativa da Vila herda esse mesmo viés** — toda variante restrita
publicada na banda é, à luz desta validação, mais provável de subestimar do que de
superestimar a população real da vila; o teto é a única variante que a validação não
desqualifica, ao custo de incluir população rural do cluster.

### Correção da nota de comissão (dois referentes, não um)

O peso 'classificação própria' carrega a comissão medida na classe construído
(acurácia do usuário de `construido` = 0,286–0,625 (docs/ADR/0009; reexecutado em docs/ADR/0014): entre 37,5 % e 71,4 % do que o mapa chama de construído não é.). Essa comissão tem DUAS relações
distintas, cada uma com seu referente: frente ao peso GHSL (o outro multiplicador de
fração), tende a puxar a estimativa para CIMA. Frente à população OBSERVADA em Cidade
de Tete, a mesma variante SUBESTIMA em 40.4% — a comissão de
área não é grande o suficiente para compensar a dupla restrição imposta pela máscara
sobre um GRID3 que já é dasimétrico.

### Saídas

`data/processed/populacao_vila_moatize_sensibilidade.csv` (as cinco variantes, piso/teto
para Vila e Tete, mais a linha `validacao_cruzada`). Linha em
`data/processed/demografia_serie_1997_2025.csv` (unidade "Vila de Moatize", ano 2017,
`selo=modelado`, `nivel_fonte=A`, valor publicado = TETO — a variante validada —, com
piso/desvios explícitos em `nota`, `comparabilidade` explicando a natureza do número).
`config/unidades.yaml`: `moatize_vila` continua `comparavel_entre_familias: false` —
existe estimativa modelada agora, mas continua não sendo contagem, e nenhuma razão
população/área com essa vila deixa de ser inválida por causa disso.

<!-- SECAO_POPULACAO_VILA_MOATIZE_FIM -->


---

<!-- fonte: data/provenance_parts/reassentamento.md -->

# Proveniência — Reassentamentos (Cateme, 25 de Setembro, Mwaladzi)

Artefato: `data/raw/reassentamentos.geojson` (+ `.sha256`, `.meta.json`).

## Origem dos dados

| Item | Detalhe |
|---|---|
| URL(s) consultada(s) | `https://nominatim.openstreetmap.org/search` (Cateme, Mwaladzi); `https://overpass.kumi.systems/api/interpreter` (25 de Setembro, sem resultado) |
| Data de acesso | 2026-09-07 |
| Licença | ODbL 1.0 © OpenStreetMap contributors — https://www.openstreetmap.org/copyright |
| Citação exigida | "© OpenStreetMap contributors" |
| CRS | EPSG:4326 (coordenadas decimais lon/lat, conforme retornado pelas APIs) |
| Resolução/nível geográfico | Ponto (node OSM individual por povoado); sem polígono de área ocupada |
| Anos cobertos | Geometria: estado atual do OSM (consultado em 2026-09-07). Atributos de contexto (`n_familias`, `ano_reassentamento`, `operador`): 2009 (Cateme, 25 de Setembro) e 2011 (Mwaladzi), conforme HRW 2013 |
| Nível (§4.0) | A — geometria OSM (ODbL, acesso anônimo, redistribuição e derivadas permitidas). Os atributos numéricos (`n_familias`) vêm de HRW 2013, fonte nível B — ver `data/licenses_parts/reassentamento.md` |
| Hash | `300fdfe29e661255972d9a7ea19cd9cfada0f3f20a4e8f45428f24d48a4681bf` (`reassentamentos.geojson.sha256`, formato `<hash>  <nome do arquivo>`, verificado com `shasum -a 256 -c`) |

## Registro por povoado

- **Cateme** — node OSM `3899065178`, 33.9731329 E / -16.0899313 S. `geometry` presente.
  `n_familias = 716` (corpo do relatório HRW 2013, ver citação abaixo). Ano: 2009.
  Operador: Vale Moçambique.
- **25 de Setembro** — `geometry: null` (intencional). Nominatim (busca "25 de Setembro,
  Moatize, Mozambique") e Overpass (busca `name~"25 de Setembro"` na bbox
  `-16.35,33.50,-16.00,34.10`) não retornaram nenhum elemento em 2026-09-07. Bairro
  urbano de Moatize; `n_familias = 289` (HRW 2013). Ano: 2009. Operador: Vale Moçambique.
  **Nenhuma coordenada foi inventada** — ausência de geometria registrada como tal.
- **Mwaladzi** — node OSM `3899065179`, 34.0326177 E / -16.1057131 S. `geometry`
  presente. `n_familias = 84` (HRW 2013). Ano: 2011. Operador: Riversdale/Rio Tinto
  (projeto Benga). HRW registra ainda um plano de mais 595 famílias até maio/2013,
  não confirmado como concluído nesta pesquisa (não incluído no total do GeoJSON).

## Âncora §8 — verificação

**Item de CLAUDE.md §8:** "Reassentamento Vale — ~1.300 famílias (Cateme, 25 de
Setembro) — fonte declarada: Sapa-AFP 2011; HRW 2013."

**Veredito: DIVERGENTE (não reconciliado).** O relatório primário localizado (HRW 2013,
nível B, CC BY-NC-ND 3.0 US — ver `data/licenses_parts/reassentamento.md`) contém **duas
leituras internamente inconsistentes** do mesmo total Vale (Cateme + 25 de Setembro):

1. **Corpo do relatório, soma das duas seções por povoado = 1.005 famílias**
   - Cateme (rural): *"Vale resettled 716 families into Cateme, a rural resettlement
     designed for farmers located approximately 40 km from Moatize."*
   - 25 de Setembro (urbano): *"Vale resettled 289 families into 25 de Setembro,
     designed as an urban neighborhood in the town of Moatize."*
   - 716 + 289 = **1.005**.

2. **Seção de contexto/introdução do mesmo relatório = 1.365 famílias**
   - *"Between 2009 and 2010, Vale resettled 1,365 households to a newly-constructed
     village, Cateme, and an urban neighborhood, 25 de Setembro."*
   - E, mais adiante: *"Vale's Moatize mine and expansion involved moving 1,365
     households living in and near the villages of Chipanga, Bagamoyo, Mithete, and
     Malabwe into two resettlements or providing them with other forms of
     compensation."*

**Fonte:** Human Rights Watch (2013), "What is a House without Food? Mozambique's
Coal Mining Boom and Resettlements", https://www.hrw.org/report/2013/05/23/what-house-without-food/mozambiques-coal-mining-boom-and-resettlements
(HTTP 200 em 2026-09-07; trechos extraídos diretamente do HTML da página em
2026-09-07).

**Leitura:** nem 1.005 nem 1.365 batem exatamente com a âncora "~1.300" de CLAUDE.md
(que por sua vez cita Sapa-AFP 2011 e HRW 2013 via agregador, não o texto primário
verificado aqui). O valor 1.365 parece incluir famílias compensadas por outras formas
que não resides em Cateme/25 de Setembro ("or providing them with other forms of
compensation"), o que explicaria por que excede a soma 716+289. Isso **não foi
confirmado** no texto disponível — é uma hipótese de leitura, registrada como tal, não
uma reconciliação. **As duas leituras são preservadas** nas notas do GeoJSON
(`data/raw/reassentamentos.geojson`, propriedade `notas` do feature Cateme) e aqui;
nenhum valor foi escolhido como "correto" para substituir o outro.

**Não localizado nesta verificação:** o relatório Sapa-AFP (2011) citado como
co-fonte da âncora §8 não foi localizado em URL de acesso primário (agência de notícias
sem arquivo público estável identificado); a âncora §8, portanto, permanece rastreável
apenas até HRW (2013) nesta Fase 0'.


---

<!-- fonte: data/provenance_parts/worldpop_grid3.md -->

# WorldPop / GRID3 — fragmento de proveniência (Vila de Moatize, população)

Objetivo: estimar população da Vila de Moatize (não publicada em nenhuma fonte; COD-PS só cobre distrito).
Recorte por janela (rasterio/vsicurl) na AOI de `config/study.yaml`, sem espelhar o país inteiro.

| Arquivo | URL | Data de acesso | Licença | Citação | Resolução/nível geográfico | Ano | Soma pop. na AOI |
|---|---|---|---|---|---|---|---|
| data/raw/grid3_moz_pop_v1_1_2020_100m_aoi.tif | https://wopr.worldpop.org/download/237 (catalogado em https://data.humdata.org/dataset/gridded-population-estimates-for-mozambique-2017-census-v1-1) | 2026-09-09 | CC BY 4.0 | Bondarenko M, Jones P, Leasure D, Lazar AN, Tatem AJ. 2020. Census disaggregated gridded population estimates for Mozambique (2017), version 1.1. WorldPop, University of Southampton. doi:10.5258/SOTON/WP00672 | ~100m grade (3 arc-sec), recorte AOI (33.50-34.10E, -16.35 a -16.00S), EPSG:4326 | calibrado ao Censo 2017 (nome de arquivo mantém rótulo "2020" pedido na tarefa, mas o dado v1.1 não tem versão 2020; ver nota de método no .meta.json) | 400.619 |
| worldpop_moz_pop_2000_100m_aoi.tif -- **NÃO GERADO** | https://data.worldpop.org/GIS/Population/Global_2000_2020/2000/MOZ/moz_ppp_2000.tif | tentativa 2026-09-09, não concluída | CC BY 4.0 | WorldPop (www.worldpop.org). Mozambique 100m Population, 2000 (unconstrained). doi:10.5258/SOTON/WP00645 | ~100m grade, AOI (não recortado) | 2000 | N/A -- ver motivo de falha abaixo |
| worldpop_moz_pop_2005_100m_aoi.tif -- **NÃO GERADO** | https://data.worldpop.org/GIS/Population/Global_2000_2020/2005/MOZ/moz_ppp_2005.tif | tentativa 2026-09-09, não concluída | CC BY 4.0 | WorldPop (www.worldpop.org). Mozambique 100m Population, 2005 (unconstrained). doi:10.5258/SOTON/WP00645 | ~100m grade, AOI (não recortado) | 2005 | N/A -- ver motivo de falha abaixo |
| worldpop_moz_pop_2010_100m_aoi.tif -- **NÃO GERADO** | https://data.worldpop.org/GIS/Population/Global_2000_2020/2010/MOZ/moz_ppp_2010.tif | tentativa 2026-09-09, não concluída | CC BY 4.0 | WorldPop (www.worldpop.org). Mozambique 100m Population, 2010 (unconstrained). doi:10.5258/SOTON/WP00645 | ~100m grade, AOI (não recortado) | 2010 | N/A -- ver motivo de falha abaixo |
| worldpop_moz_pop_2015_100m_aoi.tif -- **NÃO GERADO** | https://data.worldpop.org/GIS/Population/Global_2015_2030/R2024B/2015/MOZ/v1/100m/constrained/moz_pop_2015_CN_100m_R2024B_v1.tif | tentativa 2026-09-09, não concluída | CC BY 4.0 | WorldPop (www.worldpop.org). Mozambique 100m Population (constrained, R2024B), 2015. | ~100m grade, AOI (não recortado) | 2015 | N/A -- ver motivo de falha abaixo |
| worldpop_moz_pop_2020_100m_aoi.tif -- **NÃO GERADO** | https://data.worldpop.org/GIS/Population/Global_2015_2030/R2024B/2020/MOZ/v1/100m/constrained/moz_pop_2020_CN_100m_R2024B_v1.tif | tentativa 2026-09-09, não concluída | CC BY 4.0 | WorldPop (www.worldpop.org). Mozambique 100m Population (constrained, R2024B), 2020. | ~100m grade, AOI (não recortado) | 2020 | N/A -- ver motivo de falha abaixo |

## Método de recorte adotado (GRID3, bem-sucedido)

Leitura completa do mosaico nacional (servidor `wopr.worldpop.org` não honra `Range`),
recorte via `rasterio.windows.from_bounds` à AOI (33.50-34.10E, -16.35 a -16.00S,
EPSG:4326), arquivo nacional descartado. Nenhum arquivo de país inteiro foi espelhado
em `data/raw/`.

## Escolha de produto WorldPop (constrained vs. unconstrained)

- **2000, 2005, 2010**: só existe o produto *unconstrained* (Global_2000_2020) --
  o *constrained* do WorldPop (calibrado com pegada de edificações Maxar/Microsoft)
  só cobre 2015 em diante. Não é uma preferência, é a única opção verificada
  (HTTP 200 nas URLs; ausência de diretório `constrained` para esses anos em
  `data.worldpop.org/GIS/Population/Global_2015_2030/R2024B/{2000,2005,2010}/`).
- **2015, 2020**: usado o produto *constrained*, release R2024B, calibração ajustada
  por UN (`UNadj`), por ser mais preciso em área urbana (restringe a população a
  pixels com pegada de edificações). Confirmado disponível via listagem de diretório
  em `data.worldpop.org/GIS/Population/Global_2015_2030/R2024B/{2015,2020}/MOZ/v1/100m/constrained/`.
- Calibração censitária: WorldPop unconstrained e constrained (R2024B) são calibrados
  contra projeções da ONU/censo nacional (não contra o Censo 2017 de Moçambique
  especificamente para todos os anos -- ver `MOZ_population_v1_1_README.pdf` do GRID3
  para a calibração específica ao Censo 2017 de Moçambique, que é o único produto
  desta lista calibrado diretamente ao censo nacional).

## Falha de coleta -- WorldPop Population Counts (2000, 2005, 2010, 2015, 2020): NÃO OBTIDOS NESTA SESSÃO

Todas as 5 URLs foram verificadas como válidas (`curl -I` retorna HTTP 200, tipo
`image/tiff`, `Content-Length` correto: 446.768.688 bytes para 2000; 89.821.219 bytes
para 2020 constrained). O download por leitura em janela (`/vsicurl/` + `rasterio`)
falhou com o erro do GDAL `"Range downloading not supported by this server!"` --
confirmado de forma independente: `curl -r 0-1023` (pedido de 1 KB) contra
`data.worldpop.org` retornou o corpo completo (HTTP 200, não 206), isto é, o
servidor anuncia `Accept-Ranges: bytes` no cabeçalho mas não honra `Range` em `GET`.

Diante disso, a única rota possível é baixar o mosaico nacional inteiro (444-446 MB
para os produtos *unconstrained* 2000/2005/2010; ~90-93 MB para os *constrained*
2015/2020) e recortar localmente -- a mesma estratégia usada com sucesso para o GRID3.
Três tentativas de download completo (`curl`, sem paralelismo na tentativa final)
mediram taxas de transferência de 11,6 KB/s a ~70 KB/s (variável, possivelmente
throttling do lado do servidor). Nessas taxas, o tempo projetado de download é de
25 a 130 minutos por arquivo *constrained* e de 1,8 a 8 horas por arquivo
*unconstrained* -- inviável dentro do orçamento desta sessão de coleta.

**Nenhum dado foi inventado.** Os 5 arquivos `worldpop_moz_pop_{ano}_100m_aoi.tif`
permanecem ausentes de `data/raw/`; nenhum `.sha256` ou `.meta.json` foi gravado para
eles (regra: nunca gravar sidecar de arquivo que não existe). `pipeline/00_fetch/fetch_worldpop_grid3.py`
foi corrigido (URL do GRID3 estava morta -- 404; adicionado suporte aos 5 anos WorldPop)
e é idempotente: uma nova execução, com mais tempo ou banda melhor, retoma de onde
parou (verifica hash antes de baixar) e completa os 5 arquivos que faltam.
