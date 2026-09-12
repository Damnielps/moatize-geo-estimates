# Release v1.0.0 — texto para o corpo da release no GitHub

Cole o conteúdo abaixo da linha no campo *Describe this release*. Tag `v1.0.0`,
título `v1.0.0 — Primeira publicação`. O Zenodo arquiva o zipball desta tag e emite
o DOI a partir de `.zenodo.json` (título, autor, ORCID, licença, palavras-chave e
identificadores relacionados já estão lá).

---

Primeira publicação arquivada do estudo sobre urbanização induzida pela mineração em
Tete e Moatize (província de Tete, Moçambique), 1997–2025: pipeline reproduzível,
painel interativo e artigo.

**Painel:** https://Damnielps.github.io/moatize-geo-estimates

## O que está incluído

- **Pipeline reproduzível** (`pipeline/`), de `data/raw` ao número publicado: compostos
  de estação seca Landsat/Sentinel-2, índices, classificação, pós-processamento,
  métricas de forma urbana, reconstrução demográfica, desenho causal e figuras.
  Ambiente fixado por `uv.lock`; execução por `make`.
- **Agregados publicados** (`data/processed/`): camadas anuais de mancha urbana,
  pegada da mineração, pegada de reassentamento, cultivo irrigado/de vazante e água
  para os anos-âncora 2000, 2005, 2010, 2015, 2020 e 2025; séries demográficas,
  econômicas (preço e produção de carvão, luz noturna) e o veredito da análise causal.
- **Painel** (`app/`): mapa temporal com as três camadas mantidas separadas, narrativa,
  contexto provincial, gráficos, artigo e uma página de metodologia **gerada** de
  `PROVENANCE.md`, `data/DATA_AUDIT.md` e do lockfile — não redigida à mão.
- **Artigo** (`paper/`) e apêndice de reprodutibilidade.
- **18 decisões metodológicas registradas** (`docs/ADR/`), várias das quais mudaram a
  resposta do estudo, não só a implementação.

## Política de dados

Todo número publicado deriva exclusivamente de fontes de **nível A** — acesso aberto e
licença que permite uso, redistribuição e obras derivadas. Nenhum dado de nível B
(IPUMS, Planet NICFI, microdados DHS) é versionado ou redistribuído. Fonte a fonte, com
licença e data de verificação, em `data/LICENSES.md` e `data/DATA_AUDIT.md`.

Código sob MIT; dados derivados sob CC BY 4.0, com as citações exigidas pelas fontes
primárias (`LICENSE-DADOS.md`).

## Limitações conhecidas — leia antes de reusar os dados

Estas não são ressalvas de rodapé: delimitam o que os artefatos sustentam.

- **Nenhuma leitura causal é sustentada.** Das quatro inflexões testadas do ciclo do
  carvão, nenhuma pode ser atribuída à mina com o grupo de comparação disponível
  (`data/processed/causal/veredito_fase3.csv`).
- **`cultivo_sequeiro` não é cropland confirmado** (ADR 0012): a fenologia disponível não
  o separa de vegetação sazonal não cultivada. A camada vem desligada por padrão no
  painel e as hipóteses que dependiam dela foram rebaixadas.
- **Comissão alta na classe `urbano`** (ADR 0009 e 0014): entre 37% e 71% do que o mapa
  chama de urbano não é construído, conforme o ano. A acurácia é reportada **por classe**,
  com prevalência — acurácia global não é critério aqui, porque numa AOI onde o construído
  é ~1% um mapa vazio acertaria 98%.
- **A série de área construída tem viés de sensor que cresce no tempo** (ADR 0008): a
  série própria não faz papel de série de tendência; essa função é do WSF Evolution.
- **Camadas modeladas são marcadas como tais**: adensamento 2020–2025 (ADR 0016) e as
  épocas extrapoladas do GHSL. Toda série leva selo observado / interpolado / modelado.
- **Proveniência com ponteiro pendente:** 99 artefatos de `data/processed/imagery` e duas
  figuras registram em `commit_git` um commit descartado por reescrita de histórico, que
  já não resolve. O mapeamento antigo→novo está em `config/commits_obsoletos.yaml`; a
  correção dos arquivos não entrou nesta versão.
- **Sem DOI no próprio snapshot:** o DOI só existe depois que esta release é arquivada,
  então o zipball de v1.0.0 não contém o próprio identificador. Ele é escrito no
  repositório logo depois (`scripts/definir_doi.py`), e o DOI conceitual resolve sempre
  para a versão mais recente.

## Reprodução

```bash
uv sync --locked
make all
```

Ou pelo `Dockerfile` da raiz. `pipeline/tests/` guarda os contratos que impedem que um
artefato publicado mude sem registro.
