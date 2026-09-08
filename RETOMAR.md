# RETOMAR.md — ponto de retomada da Fase 0'

> Escrito em 2026-09-07 pelo orquestrador, imediatamente antes de uma reinicialização
> deliberada do Claude Code. Todo o estado está em disco. Leia este arquivo,
> `ORCHESTRATION_LOG.md` (do fim para o começo) e `routing_state.json`, nesta ordem.

## Por que a sessão foi reiniciada

`.claude/agents/coletor-dados.md` teve `maxTurns` elevado de **40 para 100**, mas o
frontmatter é lido na inicialização: dentro da sessão anterior o limite continuou em 40.
Cinco execuções de subagente morreram nesse limite **antes de gravar** — a família
demográfica sozinha consumiu **331K tokens em quatro tentativas** e deixou apenas um
esqueleto com todas as linhas `PENDENTE`. Reiniciar é o que faz a correção valer.

Confirme, na primeira delegação depois do arranque, que o agente ultrapassa 40 turnos.
Se não ultrapassar, `maxTurns` não é honrado nesta versão e a estratégia tem de mudar
(decompor por fonte, ou o orquestrador levantar os fatos e delegar só a redação).

## O que fazer, em ordem

### 1. Corrigir a AOI fixada nos scripts de fetch  ← bloqueia a Fase 1
`pipeline/tests/test_config.py::test_scripts_de_fetch_nao_fixam_a_aoi_no_codigo` está
**falhando**. Sete scripts copiaram o bbox provisório `xmax = 33.95` para dentro do
código em vez de lerem `config/study.yaml`:
`fetch_esa_worldcover.py`, `fetch_glad_cropland.py`, `fetch_hydro_datasets.py`,
`fetch_lulc_products.py`, `fetch_nighttime_lights.py`, `fetch_wsf_evolution.py`.

A AOI foi corrigida para `xmax = 34.10` pelo ADR 0001 (Cateme e Mwaladzi estavam fora).
Os scripts não acompanharam, e **falham em silêncio**: baixam a área errada.

### 2. Baixar o tile do Copernicus DEM em E034  ← bloqueia §5.6
`pipeline/tests/test_config.py::test_rasters_de_data_raw_cobrem_a_aoi` está **falhando**.
`fetch_hydro_datasets.py` derivou os tiles da AOI antiga e baixou só a coluna E033.
A faixa 34.0–34.1 E ficou sem elevação — é onde está **Mwaladzi (34.0326 E)**, e sem ela
não há HAND de várzea num povoado de reassentamento.
Falta `Copernicus_DSM_COG_10_S17_00_E034_00_DEM`. Verifique também se
`S16_00_E033_00` é mesmo necessário: a AOI vai só até -16.00, então ele pode ser supérfluo.

### 3. Fechar a família demográfica
Estado: `data/{licenses,provenance}_parts/demograficas.md` são **esqueletos**, tudo
`PENDENTE`. Nada verificado. É a única das seis famílias ainda aberta.

Fatos já estabelecidos, **não gaste turnos redescobrindo** (detalhe em 0'-15, 0'-17, 0'-19):
- `ine.gov.mz` está **fora do ar** — 000 em todas as variantes, não "intermitente".
- `mozdata.ine.gov.mz/index.php/catalog` responde 200. Censo 2007 = `catalog/22`,
  Censo 2017 = `catalog/24`. **O Censo 1997 não está no catálogo.**
  `get-microdata` devolve corpo vazio; `api/catalog/<id>` devolve 400.
  Nenhum texto de licença localizado nessas páginas.
- **A via do Wayback funciona.** CDX:
  `https://web.archive.org/cdx/search/cdx?url=ine.gov.mz/*&filter=statuscode:200&collapse=urlkey&fl=timestamp,original,length&limit=N&output=text`
  (use `--data-urlencode`; consultas amplas devolvem 504, fatie por subdiretório).
  Baixe com o prefixo `id_`: `https://web.archive.org/web/<timestamp>id_/<url original>`
  — devolve o objeto original, o que permite conferir hash.
- Brochura nacional do IV RGPH recuperada e lida: 8,6 MB, texto extraível. **É nacional**:
  não traz cidade nem distrito.
- **O Internet Archive estava FORA DO AR** ao fim da sessão anterior. Confirme que voltou
  antes de planejar em cima dele.

**Âncoras de 2017 já resolvidas** (0'-19), a partir do Quadro 3 do IV RGPH:
Cidade de Tete = **307.338**; Distrito de Moatize = **260.843**. O valor 305.722 de §8
**não consta** do quadro. Falta só amarrar a proveniência — ver item 4.

Continuam abertas as âncoras de **1997** e **2007**, e três perguntas:
(a) a que recorte corresponde 305.722; (b) se o INE documenta a sub-enumeração de 3,7% e
se os números publicados já a incorporam; (c) se os limites do Distrito de Moatize mudaram
entre censos — se mudaram, a série 1997→2017 não é comparável e H1 é afetada.

### 4. Fechar a proveniência do `quadro3_tete_2017.xlsx`
Está em `data/interim/proveniencia_a_confirmar/` com `LEIA-ME.md`. É documento primário do
INE, com os números de 2017 já lidos e conferidos, mas **sem URL de origem** — chegou órfão
de uma execução interrompida. Localize o snapshot (padrão provável
`ine.gov.mz/iv-rgph-2017/tete/quadro-3-*`), confira o sha256 contra o registrado no
LEIA-ME e só então promova para `data/raw/` com `.sha256` e `.meta.json` completos.
**Se o hash não bater, descarte o arquivo.**

### 5. Censo 1997 — decisão do usuário pendente
É a linha de base contrafactual de §2 e de H1, e não foi localizado. O usuário decidiu
**esgotar o Internet Archive antes** de reformular a linha de base. Se o Wayback voltar e
ainda assim não houver o II RGPH, volte ao usuário com as alternativas já postas:
recuar a linha de base para 2007 (perde a fase pré-projetos, H1 deixa de ser testável como
formulada) ou reconstruir a base 1997–2005 por área construída (WSF Evolution, 1985–2015,
nível A) reformulando H1 em termos de área.

### 6. `auditor-dados` (T3) → `DATA_AUDIT.md`
Só depois que as seis famílias estiverem fechadas. Rode
`uv run python scripts/consolidar_registros.py` antes, para atualizar `data/LICENSES.md`
e o `PROVENANCE.md` da raiz a partir dos fragmentos.

Alerte-o para o achado de 0'-12: **toda a literatura de reassentamento de §4.5 é nível B
ou C**; só o OSM é A. Consequência a arbitrar: "quantas famílias" (716/289/84, do HRW,
nível B) **não é citável em tabela de resultados**; "onde estão" e "quanto ocupam"
continuam respondíveis em nível A.

### 7. Portão do `qa-validador` → encerrar a Fase 0'
Reportar ao usuário em ≤ 15 linhas, como manda §9, antes de abrir a Fase 1.

## O que já está fechado (não refaça)

- **Ambiente reprodutível**: `uv sync --locked` → GDAL 3.12 / PROJ 9.8. `Dockerfile`,
  `Makefile`, CI, `LICENSE`. ADR 0002 registra a escolha de `uv` em vez de conda.
- **AOI confirmada**: `xmax` 33.95 → 34.10, `status: confirmado`. ADR 0001.
- **Rota STAC (§11.3)**: `probe_stac.py` consulta Planetary Computer e Element84 de fato,
  conta por `numberMatched` ou paginação somada, e é idempotente.
- **17 contratos** em `pipeline/tests/test_config.py`, 15 passando. Os 2 que falham são
  os itens 1 e 2 acima — foram escritos justamente para não deixá-los passar em silêncio.
- **Famílias aprovadas**: área construída, proxies econômicos, imagem, reassentamento,
  agricultura urbana.
- **Georreferenciamento**: `data/raw/reassentamentos.geojson` com Cateme e Mwaladzi em nós
  OSM reais e 25 de Setembro com `geometry: null` (não localizável, **não inventado**).

## Três achados que a Fase 1 herda

1. **Planetary Computer × Element84 discordam** — `sentinel-2-l2a` 2020: 103 × 194;
   `landsat-c2-l2` 2025: 16 × 18. §11.3 exige concordância dentro de tolerância declarada.
   Precisa de investigação e provavelmente de ADR.
2. **2010 tem só 4 cenas Landsat 5** na estação seca com nuvem ≤ 40%, nos dois catálogos.
   Pouco para mediana robusta. Ampliar `composto.janela_anos` só para 2010 quebra o
   "mesmo protocolo em todos os anos" de §5.1 e exige ADR próprio.
3. **Planet NICFI foi descontinuado** (licitação da fase seguinte cancelada em set/2025).
   §4.3 do prompt-mestre está desatualizado nesse ponto.

## Pendências do usuário

- `LICENSE` tem `<TITULAR DOS DIREITOS>` como marcador, e o `CITATION.cff` exigido por
  §11.1 não foi criado: não há identidade configurada no git deste repositório e o
  orquestrador não inventa nome de autor.
- `cost_ledger.csv` **não instrumenta custo**: o payload do `SubagentStop` não traz modelo
  nem tokens. O hook passou a salvar o payload bruto em
  `data/interim/subagent_stop_payloads.jsonl`; inspecione-o para corrigir os seletores
  `jq`. Enquanto isso, o custo real vem das notificações de tarefa (tabela em `BUDGET.md`).
