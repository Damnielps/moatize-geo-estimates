# ADR 0002 — Ambiente reprodutível com `uv` + `pyproject.toml`/`uv.lock`, não conda

- **Data:** 2026-09-07
- **Fase:** 0' (Reconhecimento)
- **Decidido por:** orquestrador
- **Estado:** aceito

## Contexto

§11.1 do prompt-mestre admite duas formas de fixar o ambiente:
`environment.yml + conda-lock.yml` **ou** `pyproject + uv.lock`. É preciso escolher uma,
porque §10 exige que o pipeline reexecute em ambiente limpo a partir de `make all`
sem intervenção manual.

Estado da máquina de desenvolvimento em 2026-09-07: `conda` **não instalado**,
`gdalinfo` **não instalado**, `geopandas`/`rasterio` ausentes do Python do sistema
(3.14.4). `uv` 0.12.1 presente.

## Decisão

`pyproject.toml` + `uv.lock`, com `requires-python = "==3.12.*"`.

O Python 3.12 é fixado (e não 3.13/3.14) porque a pilha geoespacial binária
— `rasterio`, `fiona`, `pyproj`, `pylandstats` — tem wheels estáveis para 3.12.
`uv python install 3.12` provisiona o próprio interpretador, de modo que a
reprodução não depende do Python do sistema do usuário.

GDAL e PROJ entram como bibliotecas embarcadas nas wheels do `rasterio`/`pyproj`
(GDAL 3.12.4, PROJ 9.8.1 na resolução corrente), não como dependência de sistema.
Nenhum `apt`/`brew install gdal` é exigido de quem reproduz.

`earthengine-api` fica em `optional-dependencies.gee`: a rota GEE é a (a) de §11.3,
opcional e dependente de conta; a rota STAC é a de referência e está nas dependências
obrigatórias (`pystac-client`, `odc-stac`, `stackstac`, `planetary-computer`).

## Alternativa rejeitada

**conda / mamba + `conda-lock.yml`.** É a escolha tradicional para pilha geoespacial e
resolve GDAL como pacote de sistema, o que evita divergência entre a GDAL do `rasterio`
e a de linha de comando. Rejeitada por três motivos:

1. exige instalar um gerenciador que não está na máquina, aumentando o número de passos
   de `make env` e afastando o repositório do teto de cinco comandos de §11.2.5;
2. `conda-lock` produz locks por plataforma; o projeto precisa rodar em macOS arm64
   (desenvolvimento) e linux amd64 (container e CI), o que dobra o arquivo de lock e o
   custo de mantê-lo coerente. `uv.lock` é multiplataforma por construção;
3. a resolução `uv` é determinística e rápida o bastante para ser reexecutada em CI a
   cada commit, como §11.2.4 exige.

## Consequência

- `make env` passa a ser `uv sync --locked`.
- Nenhum utilitário GDAL de linha de comando (`gdalinfo`, `ogr2ogr`, `gdal_translate`)
  pode ser usado nos scripts do pipeline: eles não existem no ambiente reproduzido.
  Toda operação raster/vetor é feita pela API Python (`rasterio`, `geopandas`).
  As entradas correspondentes em `permissions.allow` de `.claude/settings.json` ficam
  sem efeito prático — mantidas, mas não devem ser exercidas.
- O `Dockerfile` parte de `python:3.12-slim` + `uv sync --locked`, sem camada conda.
