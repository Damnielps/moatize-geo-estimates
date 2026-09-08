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
