# Urbanização induzida pela mineração em Tete e Moatize (Moçambique), 1997–2025

[https://Damnielps.github.io/moatize-geo-estimates](https://Damnielps.github.io/moatize-geo-estimates)

<!-- selo DOI: inserir após a release no Zenodo -->

**Licenças:** código sob MIT; dados e textos sob CC BY 4.0 (exceções em `LICENSE-DADOS.md`).

Pipeline reproduzível, aplicação web e artigo sobre como o ciclo carbonífero de Moatize
alterou a trajetória demográfica, a forma urbana, a base econômica e a agricultura urbana
e periurbana de Tete e Moatize — e que trajetória se desenha para depois de 2025.

**Duas restrições atravessam todo o projeto:**
1. **Apenas dados de nível A** (públicos, licença que permite uso, redistribuição e
   obras derivadas) sustentam qualquer número publicado. Política em `CLAUDE.md` §4.0.
2. **Pipeline integralmente reproduzível por terceiros** a partir deste repositório,
   em ambiente limpo, sem intervenção manual.

## Como citar

Para citar os dados, o painel ou o artigo, use:

```yaml
authors:
  - family-names: "Pessini Sobreira"
    given-names: "Daniel"
    orcid: "https://orcid.org/0000-0002-6632-3991"
title: "Urbanização induzida pela mineração em Tete e Moatize (Moçambique), 1997–2025"
year: 2026
url: "https://Damnielps.github.io/moatize-geo-estimates"
repository-code: "https://github.com/Damnielps/moatize-geo-estimates"
license: "CC-BY-4.0"
```

Ver `CITATION.cff` para detalhes completos e `LICENSE-DADOS.md` para as fontes primárias
e como citá-las.

## Estado

🟢 **Fases 0, 0', 1, 2, 3, 4 e 5 concluídas. Fase 6 (Revisão adversarial) em curso.**
O histórico das decisões está em `ORCHESTRATION_LOG.md`, lido do fim para o começo;
o veredito sobre as fontes, em `data/DATA_AUDIT.md`.

**Ressalva que atravessa todo o estudo:** o conjunto de fontes de nível A é **insuficiente**
para a extremidade 1997–2007 da série demográfica e para as tabulações domiciliares do INE.
A linha de base foi reformulada por área construída ([ADR 0003](docs/ADR/0003-linha-de-base-por-area-construida.md)).

| Fase | Estado |
|---|---|
| 0 — Bootstrap da orquestração | ✅ concluída (B-02 e B-03 resolvidos) |
| 0' — Reconhecimento e auditoria de dados | ✅ encerrada e aprovada; 8 famílias de fonte, 10 arquivos espelhados, 19 contratos |
| 1 — Pipeline de imagem | ✅ concluída |
| 2 — Métricas e reconstrução demográfica | ✅ concluída |
| 2b — Agricultura urbana | ✅ concluída |
| 3 — Análise comparativa e cenários | ✅ concluída |
| 4 — App | ✅ concluída (layouting e storytelling segundo Fase 4b) |
| 5 — Artigo | ✅ concluída |
| 6 — Revisão adversarial | 🟡 em curso |
| 7 — Fechamento de custo | ⬜ |

## Como reproduzir (5 comandos)

```bash
git clone https://github.com/Damnielps/moatize-geo-estimates && cd moatize-geo-estimates
make env      # uv sync --locked — provisiona o próprio Python 3.12 (ver docs/ADR/0002)
make fetch    # baixa as fontes de nível A, verifica sha256, preenche PROVENANCE.md
make all      # pipeline completo: imagem → métricas → causal → figuras
make app      # build estático do front-end em app/dist
```

`make env`, `make test` e `make app` já funcionam. `make fetch` e `make all` reexecutam
o pipeline de dados de forma idempotente. Ver `Makefile` para alvos intermediários
por fase.

A rota de referência para reprodutibilidade é **STAC público + Python local**
(`pipeline/01_imagery/stac/`), sem conta em nenhuma plataforma. A rota Google Earth
Engine (`pipeline/01_imagery/gee/`) é mantida em paralelo e precisa reproduzir a
primeira dentro das tolerâncias de `config/tolerances.yaml`.

A coleta de produção no SEC EDGAR exige `export SEC_USER_AGENT="Nome Sobrenome email@exemplo"` (política de acesso da SEC).

## Estrutura

```
config/              AOI, anos-âncora, thresholds, seeds, tolerâncias, cidades-controle
data/                raw/ (nível A + .sha256 + .meta.json) · interim/ (git-ignored) · processed/
pipeline/            00_fetch 01_imagery 02_metrics 02b_agri 03_causal 04_figures 05_app tests
app/                 front-end estático; consome apenas data/processed
paper/               manuscrito (Quarto), figuras
scripts/             utilitários de orquestração
docs/ADR/            decisões metodológicas (ADRs 0001–0014)
.github/workflows/   CI/CD: testes, gitleaks, publicação em GitHub Pages
```

## Documentos-chave

| Arquivo | Conteúdo |
|---|---|
| `CLAUDE.md` | contexto do estudo carregado por todo subagente: problema, periodização, unidades, fontes, métodos, critérios de qualidade |
| `LICENSE` | MIT para código-fonte |
| `LICENSE-DADOS.md` | CC BY 4.0 para dados, com tabela de exceções por camada |
| `CITATION.cff` | metadados de citação (CFF 1.2.0) |
| `data/LICENSES.md` | licença e nível A/B/C de cada fonte, data de verificação |
| `data/DATA_AUDIT.md` | veredito do auditor sobre a suficiência do conjunto A |
| `PROVENANCE.md` | cadeia de proveniência por artefato; fontes excluídas; dados inexistentes |
| `data/DATA_DICTIONARY.md` | cada coluna: tipo, unidade, fonte, método, selo (observado/interpolado/modelado) |
| `ORCHESTRATION_LOG.md` | escalonamentos, fallbacks, desvios e bloqueios |
| `BUDGET.md` / `cost_ledger.csv` | teto e consumo por fase e camada de modelo |
| `docs/CHECKLIST_PUBLICACAO.md` | checklist de pré-publicação e procedimento de DOI |

## Publicação

O app é publicado como página estática no GitHub Pages pelo workflow
`.github/workflows/publicar.yml` (build + deploy a cada push em `main`, sem rerodar o
pipeline de dados). Inclui verificação de segredos (`gitleaks`, `.gitleaks.toml`) e de
ausência de dado bruto/intermediário no histórico do git.

**Destino:** repositório `github.com/Damnielps/moatize-geo-estimates`, página de projeto
em `https://Damnielps.github.io/moatize-geo-estimates`.

**E-mail dos commits:** corrigido em 2026-09-09 — o histórico (então com 1 commit) foi
reescrito com `git filter-repo` para usar o e-mail no-reply do GitHub
(`129672935+Damnielps@users.noreply.github.com`) em vez do e-mail pessoal; `user.email`
local está configurado com o mesmo endereço para próximos commits.

**Varredura de segurança** (2026-09-09, detalhada em `docs/CHECKLIST_PUBLICACAO.md`):
`gitleaks detect` no histórico do git — nenhum segredo encontrado; sweep manual por
padrões de chave, token, e-mail pessoal, CPF, caminho local e dado de nível B — limpo.

## Ética

O estudo trata de reassentamento involuntário de aproximadamente 1.300 famílias.
A análise segue o marco IRR (Cernea) e as Normas de Desempenho da IFC (PS5):
os polígonos representam pessoas deslocadas. Nenhum dado que permita identificar
domicílios individuais é publicado.
