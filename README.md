# Urbanização induzida pela mineração em Tete e Moatize (Moçambique), 1997–2025

Pipeline reproduzível, aplicação web e artigo sobre como o ciclo carbonífero de Moatize
alterou a trajetória demográfica, a forma urbana, a base econômica e a agricultura urbana
e periurbana de Tete e Moatize — e que trajetória se desenha para depois de 2025.

**Duas restrições atravessam todo o projeto:**
1. **Apenas dados de nível A** (públicos, licença que permite uso, redistribuição e
   obras derivadas) sustentam qualquer número publicado. Política em `CLAUDE.md` §4.0.
2. **Pipeline integralmente reproduzível por terceiros** a partir deste repositório,
   em ambiente limpo, sem intervenção manual.

## Estado

🟢 **Fase 0' encerrada, aprovada no portão de qualidade.** Fase 1 (pipeline de imagem)
em curso. O histórico das decisões está em `ORCHESTRATION_LOG.md`, lido do fim para o
começo; o veredito sobre as fontes, em `data/DATA_AUDIT.md`.

**Ressalva que atravessa todo o estudo:** o conjunto de fontes de nível A é **insuficiente**
para a extremidade 1997–2007 da série demográfica e para as tabulações domiciliares do INE.
A linha de base foi reformulada por área construída ([ADR 0003](docs/ADR/0003-linha-de-base-por-area-construida.md)).

| Fase | Estado |
|---|---|
| 0 — Bootstrap da orquestração | ✅ concluída (B-02 e B-03 resolvidos) |
| 0' — Reconhecimento e auditoria de dados | ✅ encerrada e aprovada; 8 famílias de fonte, 10 arquivos espelhados, 19 contratos |
| 1 — Pipeline de imagem | 🟡 em curso |
| 2 — Métricas e reconstrução demográfica | ⬜ |
| 2b — Agricultura urbana | ⬜ |
| 3 — Análise comparativa e cenários | ⬜ |
| 4 — App | ⬜ |
| 5 — Artigo | ⬜ |
| 6 — Revisão adversarial | ⬜ |
| 7 — Fechamento de custo | ⬜ |

## Como reproduzir (5 comandos — alvos ainda não implementados)

```bash
git clone <url> && cd tete-moatize
make env      # uv sync --locked — provisiona o próprio Python 3.12 (ver docs/ADR/0002)
make fetch    # baixa as fontes de nível A, verifica sha256, preenche PROVENANCE.md
make all      # pipeline completo: imagem → métricas → causal → figuras  (não implementado)
make app      # build estático do front-end em app/dist
```

`make env`, `make test` e `make app` já funcionam (`make app` depende de `app-data`, que
regenera `app/src/content/` a partir de `PROVENANCE.md`/`data/DATA_AUDIT.md`/`uv.lock` e
copia `data/processed/` para `app/public/data/`, antes de `npm ci && npm run build`).
Os demais alvos existem no grafo do `Makefile` mas falham explicitamente enquanto a fase
correspondente não for executada — de propósito: um alvo que não faz nada e sai com
sucesso é pior que um que diz que não está pronto.

A rota de referência para reprodutibilidade é **STAC público + Python local**
(`pipeline/01_imagery/stac/`), sem conta em nenhuma plataforma. A rota Google Earth
Engine (`pipeline/01_imagery/gee/`) é mantida em paralelo e precisa reproduzir a
primeira dentro das tolerâncias de `config/tolerances.yaml`.

## Estrutura

```
config/     AOI, anos-âncora, thresholds, seeds, tolerâncias, cidades-controle
data/       raw/ (nível A + .sha256 + .meta.json) · interim/ (git-ignored) · processed/
pipeline/   00_fetch 01_imagery 02_metrics 03_causal 04_figures tests
app/        front-end estático; consome apenas data/processed
paper/      manuscrito
scripts/    utilitários de orquestração
docs/ADR/   decisões metodológicas
```

## Documentos-chave

| Arquivo | Conteúdo |
|---|---|
| `CLAUDE.md` | contexto do estudo carregado por todo subagente: problema, periodização, unidades, fontes, métodos, critérios de qualidade |
| `data/LICENSES.md` | licença e nível A/B/C de cada fonte |
| `data/DATA_AUDIT.md` | veredito do auditor sobre a suficiência do conjunto A |
| `PROVENANCE.md` | cadeia de proveniência por artefato; fontes excluídas; dados inexistentes |
| `data/DATA_DICTIONARY.md` | cada coluna: tipo, unidade, fonte, método, selo |
| `ORCHESTRATION_LOG.md` | escalonamentos, fallbacks, desvios e bloqueios |
| `BUDGET.md` / `cost_ledger.csv` | teto e consumo por fase e camada de modelo |

## Licença

- **Código:** MIT (`LICENSE`).
- **Dados derivados:** CC-BY-4.0, com as citações exigidas pelas fontes primárias
  listadas em `data/LICENSES.md`.
- **Dados de nível B** (IPUMS, Planet NICFI, microdados DHS) não estão neste repositório
  e nunca entram no depósito publicado.

## Publicação

O app é publicado como página estática no GitHub Pages pelo workflow
`.github/workflows/publicar.yml` (build + deploy a cada push em `main`, sem rerodar o
pipeline de dados — mesmo padrão do projeto irmão `atlas-migração`), com verificação de
segredos (`gitleaks`, `.gitleaks.toml`) e de ausência de dado bruto/intermediário no
histórico do git. `CITATION.cff` e `docs/CHECKLIST_PUBLICACAO.md` seguem o mesmo molde.

**Destino decidido:** repositório `github.com/Damnielps/moatize-geo-estimates`, página
de projeto em `https://Damnielps.github.io/moatize-geo-estimates`. Assim que o
repositório existir no GitHub, configurar em *Settings → Secrets and variables →
Actions → Variables*: `SITE_URL=https://Damnielps.github.io/moatize-geo-estimates` e
`BASE_PATH=/moatize-geo-estimates/`. Até lá, o build cai no placeholder inválido de
propósito `https://EXEMPLO.invalid` (ver `app/vite.config.js`).

**E-mail dos commits:** corrigido em 2026-09-09 — o histórico (então com 1 commit) foi
reescrito com `git filter-repo` para usar o e-mail no-reply do GitHub
(`129672935+Damnielps@users.noreply.github.com`) em vez do e-mail pessoal do titular;
`user.email` local já está configurado com o mesmo endereço para os próximos commits.

**Varredura de segurança feita antes do primeiro push** (2026-09-09, detalhada em
`docs/CHECKLIST_PUBLICACAO.md`): `gitleaks detect` no histórico do git — nenhum segredo
encontrado; sweep manual por padrões de chave/token, e-mail pessoal, CPF, caminho local
e dado de nível B — limpo, com uma correção aplicada (`pipeline/00_fetch/fetch_osm_reassentamentos.sh`
tinha o e-mail pessoal do titular hardcoded no `User-Agent` de contato para a API do
OSM; trocado por uma URL do repositório, mesmo padrão já usado em `fetch_osm_contexto.py`).

## Ética

O estudo trata de reassentamento involuntário de aproximadamente 1.300 famílias.
A análise segue o marco IRR (Cernea) e as Normas de Desempenho da IFC (PS5):
os polígonos representam pessoas deslocadas. Nenhum dado que permita identificar
domicílios individuais é publicado.
