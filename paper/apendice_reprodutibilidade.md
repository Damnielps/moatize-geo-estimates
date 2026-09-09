# Apêndice D — Reprodutibilidade, ambiente e implementação

Apêndice do manuscrito `paper/artigo.md` (Fase 5). Exigido por `CLAUDE.md` §6-A e varrido pelo
contrato `pipeline/tests/test_transparencia_metodologica.py`, que reprova qualquer versão de
biblioteca declarada aqui que não coincida com `uv.lock` e exige a menção aos ADR que mudaram a
resposta do estudo. **As versões da seção D.2 foram extraídas de `uv.lock` em 2026-09-08, não
redigidas.** Este apêndice não conta no limite de palavras do corpo (§6-A).

## D.1 Ambiente

- **Gerenciador:** `uv` (imagem `ghcr.io/astral-sh/uv:0.12.1` no `Dockerfile`; `uv` 0.12.1 na
  máquina de desenvolvimento, `docs/ADR/0002`). `make env` executa `uv sync --locked`.
- **Interpretador:** `requires-python = "==3.12.*"` (`pyproject.toml`; `uv.lock` linha 3).
  O `uv` provisiona o próprio Python 3.12; a reprodução não depende do Python do sistema.
- **Lockfile:** `uv.lock`, `version = 1`, `revision = 3`, multiplataforma (macOS arm64 para
  desenvolvimento; linux amd64 para contêiner e CI).
- **GDAL e PROJ:** embarcados nas *wheels* das bibliotecas raster e de CRS, não instalados como
  dependência de sistema. O ADR 0002 declara GDAL 3.12.4 e PROJ 9.8.1 na resolução corrente.
  Nenhum utilitário GDAL de linha de comando (`gdalinfo`, `ogr2ogr`, `gdal_translate`) é usado em
  nenhum script: toda operação raster e vetorial é feita pela API Python.
- **Contêiner:** `python:3.12-slim` + `apt-get install make git ca-certificates curl jq` +
  `uv sync --locked --no-install-project` + `COPY . .`; `CMD ["make", "all"]`.
- **Alternativa rejeitada:** conda/mamba + `conda-lock` (`docs/ADR/0002`): gerenciador ausente da
  máquina, lock por plataforma, resolução mais lenta para CI a cada commit.

## D.2 Bibliotecas críticas — versões travadas em `uv.lock`

Lidas do bloco `[[package]]` de `uv.lock` (`name` e `version`). O contrato de transparência
compara cada versão abaixo com o lockfile e reprova divergência.

| Biblioteca | Versão em `uv.lock` | Papel no pipeline |
|---|---|---|
| rasterio | 1.5.1 | leitura e escrita raster COG, máscara por geometria, reprojeção e agregação por média |
| odc-stac | 0.5.3 | carregamento das cenas STAC na grade canônica |
| odc-geo | 0.5.3 | geometria da grade canônica |
| pystac-client | 0.9.0 | consulta ao catálogo STAC |
| pystac | 1.15.2 | modelo de itens STAC |
| stackstac | 0.5.0 | rota alternativa de carregamento (§11.3) |
| scikit-learn | 1.9.0 | Random Forest de trezentas árvores |
| numpy | 2.5.3 | álgebra de índices e máscaras |
| pandas | 3.0.5 | tabelas e CSV |
| scipy | 1.18.1 | filtros morfológicos e transformada de distância (HAND aproximado) |
| pylandstats | 3.1.0 | métricas de fragmentação |
| geopandas | 1.1.4 | vetores, partição de Voronoi, buffers |
| shapely | 2.1.2 | geometria |
| pyproj | 3.8.0 | CRS (EPSG:32736 para área; EPSG:4326 para exibição) |
| xarray | 2026.7.0 | pilhas de cenas e mediana |
| rioxarray | 0.23.0 | ponte entre xarray e rasterio |
| statsmodels | 0.15.0 | séries interrompidas, HAC, Prais–Winsten, quasi-Poisson, DiD |
| matplotlib | 3.11.1 | figuras (paleta Ardósia vendorizada) |

`earthengine-api` fica em `optional-dependencies.gee` e não é usado na rota de referência.

## D.3 Plataformas como meio, não fonte

O catálogo STAC canônico é o Microsoft Planetary Computer (`docs/ADR/0004`). O Element84 Earth
Search foi rejeitado por dois motivos medidos: resolve os assets Landsat para um bucket
*Requester Pays* (exige conta com faturamento, o que viola a rota sem conta) e indexa cada
reprocessamento Sentinel-2 como item separado, o que dobraria a contagem de cenas e enviesaria a
mediana. O custo aceito é uma lacuna de três cenas Landsat 9 em 2025, registrada no `.meta.json`
do composto. A rota GEE é opcional (dependência extra `gee`), exige conta, e a tolerância de
concordância entre rotas está em `config/tolerances.yaml` (`concordancia_rotas`: erro relativo
de área por camada e ano ≤ 3 %; acordo pixel a pixel ≥ 95 %). Os dados subjacentes — Landsat
Collection 2 Level-2 (USGS) e Sentinel-2 L2A (Copernicus) — são nível A independentemente da
plataforma.

## D.4 Seeds e determinismo

Todo processo estocástico lê `config/seeds.yaml`; alterar uma seed muda os artefatos e exige ADR.

| Processo | Seed | Parâmetros |
|---|---|---|
| Random Forest | 20250907 | 300 árvores; `min_samples_leaf` 1; `max_samples` 0,5; `max_features` sqrt; bootstrap |
| Amostragem de treino | 20250907 | aleatória simples, proporcional ao prior, n = 200.000, piso 500 por classe (`docs/ADR/0006`) |
| Pontos de validação | 424242 | independente do treino; 24 por estrato e ano |
| Controle sintético | 13579 | 20 partidas SLSQP; 5 placebos espaciais; 4 temporais |
| Wild cluster bootstrap | 97531 | 1.000 reamostragens, Rademacher |
| Logit espacial | 24680 | reservada; não usada (recusa registrada em `logit_conversao_status.csv`) |

Os compostos de mediana não usam seed: os itens STAC são ordenados por `id` antes da composição,
o que torna a mediana determinística.

## D.5 Grafo de execução (`Makefile`)

```
env ──► fetch ──► imagery ──┬──► metrics ──┐
                            │               ├──► causal ──► figures ──► (artigo)
                            └──► agri ──────┘        │
                                                     └──► app-data ──► app
all = imagery metrics agri causal figures
```

Ordem interna de cada alvo, como escrita no `Makefile`:

- `imagery`: `compostos.py` → `indices.py` → `compostos_chuva.py` → `classificacao.py` →
  `pegada_sensibilidade.py` → `amostras_validacao.py` → `acuracia.py` → `concordancia_wsf.py` →
  `slc_off_2010.py`.
- `metrics`: `area_cagr.py` → `fragmentacao.py` → `tipologia_expansao.py` → `edificacoes.py` →
  `write_stats_forma_urbana.py` → `reconstrucao_demografica.py` → `stats_by_year_by_unit.py`
  (reprova se faltar família, se um selo for inválido ou se entrar linha de nível B/C no núcleo).
- `agri`: `cultivo.py` → `varzea.py` → `cultivo_varzea.py` → `amostras_validacao_cultivo.py` →
  `acuracia_cultivo.py` → `validacao_externa_cultivo.py`.
- `causal`: `teste_vies_sensor.py` → `estabilidade_temporal.py` → `series_base.py` →
  `series_interrompidas.py` → `decomposicao_luz.py` → `placebos.py` → `did_sintetico.py` →
  `elasticidades.py` → `logit_conversao.py` (registra a recusa; não estima) → `cenarios.py` →
  `veredito_fase3.py`.
- `figures`: `mapa_localizacao.py` → `fatos_verificados.py` (gera `paper/FATOS_VERIFICADOS.md`).
- `test`: `uv run pytest -q` sobre `pipeline/tests/`, incluindo os contratos de dados, de
  estabilidade e de transparência metodológica.

Nenhuma etapa depende de estado de sessão: toda entrada vem de `config/*.yaml` e de `data/raw/`
(espelho de nível A com `.sha256` e `.meta.json`); saídas intermediárias vão para `data/interim/`
(regenerável, git-ignored) e finais para `data/processed/` (versionado).

## D.6 O que reproduz byte a byte e o que reproduz dentro de tolerância

**Byte a byte**, dado o mesmo catálogo STAC e o mesmo lockfile: os compostos de mediana (itens
ordenados por `id`; sem seed), os índices espectrais, a classificação e as regras R1/R2 (seed
fixa), as pegadas por razão de NDVI, os rasters de cultivo e várzea, e todas as tabelas derivadas
deles. A única fonte conhecida de divergência entre execuções é a reingestão de cenas no catálogo,
detectável pela lista de `id` gravada no `.meta.json` de cada composto.

**Dentro de tolerância declarada** (`config/tolerances.yaml`, bloco `regressao_numerica`):

| Grandeza | Métrica | Tolerância |
|---|---|---|
| área por camada e ano | erro relativo absoluto | 0,5 % |
| acurácia global | diferença absoluta | 0,01 |
| população dasimétrica | erro relativo absoluto | 2 % |
| índices espectrais por pixel | diferença absoluta | 1e-5 |
| contrato do `qa_pixel` (soma de observações válidas por dois caminhos de reprojeção) | erro relativo absoluto | 1 % |

A tolerância dos índices cobre apenas arredondamento de ponto flutuante; a do `qa_pixel` cobre a
diferença de reamostragem entre dois caminhos de reprojeção e teria capturado o defeito de
`nodata = 1` da primeira execução, que produzia dezenas de pontos percentuais de diferença.

**Não regenerado por código, e declarado:** os rótulos de referência
`data/processed/validacao/rotulos_interpretados.csv` e `rotulos_interpretados_cultivo.csv` são
julgamentos registrados e versionados (interpretação visual de recortes RGB por modelo
multimodal, cego ao mapa por `id_cego`, `docs/ADR/0007`). `amostras_validacao.py` regera os
recortes e o sorteio; `acuracia.py` falha alto se os rótulos faltarem, que é o comportamento
correto: sem rótulo não há validação.

**Não reproduzível por este pipeline, e declarado:** a conciliação DMSP↔VIIRS do produto de luz
(Chen, Yu et al., 2021) é interna ao produtor; a taxa de omissão do censo de 2017 e as
tabulações domiciliares do INE são nível C e não entram no núcleo.

## D.7 Decisões que mudaram a resposta do estudo

Os quinze ADR de `docs/ADR/` não são apêndice. Os seis abaixo alteraram o que o estudo pode
afirmar; cada um registra a alternativa rejeitada e a evidência medida.

| ADR | Decisão | Consequência |
|---|---|---|
| 0008 | a série própria deixa de ser série de tendência; o WSF Evolution assume, lido como taxa de primeira detecção (viés de detecção de −17,0 % em 2015 com a capacidade de 2000; +1,25 %/ano espúrio) | H1 só testável como taxa de incorporação de solo; nenhuma série de estoque sem catraca |
| 0009 | a acurácia do usuário substitui a acurácia global como critério para a classe rara (prevalência 0,5–1,9 %) | o número decisivo passa a ser 0,286–0,625, com IC95 sobrepostos entre anos |
| 0011 | pegada minerária e de reassentamento como classe própria de solo/rocha exposto persistente (a interseção com construído cobria 7,1 % dos polígonos de Maus) | H3 torna-se testável; a calibração em 2020 não é validação; o placebo temporal 2000/2005 é |
| 0012 | `cultivo_sequeiro` reprovado como cropland (acurácia do usuário 0,000; kappa −0,065; Jaccard 0,0006–0,0043) | H5 sem magnitude; H6 sem resposta; pergunta 8 parcial; regra 6.4 dos cenários dispara |
| 0013 | diagnóstico: `urbano` é estável em área, não em pixel (churn 31,0 %–54,4 %); R2 é catraca (18,0 % herdado em 2025); causa raiz é limiar absoluto sobre série não estacionária | a Fase 3 não pode estimar quebra na série própria nem testar H4 com área de R2; o par 2015–2020 não sustenta efeito |
| 0014 | limiar relativo à mediana da paisagem propagado ao treino; máscara por banda não positiva (o Zambeze volta); R2 removida de `industrial` e `reassentamento` | vegetação varia por fator 2,2 em vez de 15; abandono de povoado torna-se observável; acurácia reexecutada e inalterada em substância |

Os demais ADR (0001 AOI; 0002 ambiente; 0003 linha de base por área; 0004 catálogo STAC; 0005
janela de 2010; 0006 amostragem proporcional; 0007 validação cega por interpretação visual; 0010
domicílios sem fonte A; 0015 ramo de teste relativo vazio e decomposição de 2022) condicionam a
execução e a leitura, e estão resumidos na seção 4.7 e na Tabela E1 (Apêndice E) do artigo.

## D.8 Defeitos encontrados e corrigidos que condicionam a leitura

Registrados porque a versão que os continha teria produzido números plausíveis e errados:
`qa_pixel` com `nodata = 1` (falha de sensor contada como observação válida; compostos
regravados); NDVI de chuva sem máscara de denominador (amplitude fenológica contaminada; seis
anos regerados); máscara de denominador mínimo que apagava o Zambeze (substituída por máscara por
banda); limiar absoluto de vegetação sobre série não estacionária (inflação de ~15 km² do
construído bruto de 2015); pegada como interseção com construído (7,1 % dos polígonos);
placebo espacial com denominador nulo (ramo reclassificado como vazio, veredito original
preservado). Detalhe na seção 4.7 e no Apêndice E.15 do artigo e nos ADR 0013, 0014 e 0015.

## D.9 Reprodução em cinco comandos

```
git clone <repositório> && cd tete-moatize
make env        # uv sync --locked
make fetch      # espelho de nível A, sha256, PROVENANCE.md
make all        # imagery metrics agri causal figures → data/processed/
make test       # contratos de dados, regressão numérica e transparência
```

O contêiner equivalente é `docker build . && docker run <imagem>` (executa `make all`).
