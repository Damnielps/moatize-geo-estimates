# ORCHESTRATION_LOG.md

Registro de escalonamentos, rebaixamentos, fallbacks e decisões de arbitragem
(§0-A.2, §0-A.3, §0-A.4 e §9 do prompt-mestre).

Formato de cada entrada:
`data · fase · tarefa · camada inicial → camada final · motivo · quem decidiu`

---

## 2026-09-07 — Fase 0 (Bootstrap)

### B-01 · Arquivos de orquestração criados
Criados `.claude/agents/` (8 agentes), `scripts/log_cost.sh`, `CLAUDE.md`, `BUDGET.md`,
`config/{study,seeds,tolerances}.yaml`, `routing_state.json`, esqueleto do repositório (§11.1).
Hook `log_cost.sh` testado com payload sintético: grava linha válida em `cost_ledger.csv`.

### B-02 · BLOQUEIO — `.claude/settings.json` não pôde ser gravado
**Motivo:** o classificador de auto-mode do Claude Code recusou a escrita em
`.claude/settings.json` (arquivo de configuração do harness, contendo definição de `hooks`),
tanto por `Write` quanto por heredoc em `Bash`. Não é falha do prompt-mestre nem do
ambiente Python/geo.
**Consequência:** sem esse arquivo, não valem `model: opus` na sessão principal,
`CLAUDE_CODE_SUBAGENT_MODEL=sonnet`, `CLAUDE_CODE_MAX_CONCURRENT_SUBAGENTS=6`,
a cadeia de fallback nem o hook `SubagentStop` → `cost_ledger.csv` fica vazio.
**Ação pendente do usuário:** gravar manualmente o conteúdo proposto em
`docs/settings.json.proposto` para `.claude/settings.json`.

### B-03 · BLOQUEIO — agentes não registrados nesta sessão
**Motivo:** o registro de `subagent_type` do Claude Code é fixado no início da sessão.
Teste de fumaça em `coletor-dados` retornou:
`Agent type 'coletor-dados' not found. Available agents: claude, claude-code-guide,
Explore, general-purpose, Plan, statusline-setup`.
**Consequência:** a verificação do bootstrap exigida por §0-B ("disparar tarefa trivial em
cada subagente e confirmar via `/tasks` que cada um roda no modelo declarado")
**não pôde ser concluída**. O roteamento por camada T1–T4 não está operante.
**Ação pendente do usuário:** reiniciar o Claude Code neste diretório. Os 8 agentes em
`.claude/agents/` passam a ser carregados na inicialização.
**Alternativa (degradada, não recomendada):** delegar a `general-purpose` com `model`
por invocação e o system prompt do agente colado na mensagem de delegação. Preserva o
roteamento de modelo, mas perde `tools`, `maxTurns` e a `description` que dirige o
roteamento automático — e o prompt-mestre trata roteamento silenciosamente errado como
o principal risco de estouro de custo (§0-B).

### B-04 · Desvios deliberados em relação ao texto do prompt-mestre

| Item pedido | O que foi feito | Motivo |
|---|---|---|
| `effort:` no frontmatter dos agentes | **omitido** | Campo não documentado no frontmatter de subagentes na versão vigente. Incluí-lo daria falsa garantia de que o esforço está sendo controlado. O `effort` desejado por camada está tabelado em `BUDGET.md` para aplicação por invocação. |
| Cadeia de fallback por camada (`fable→opus→sonnet`, `opus→sonnet`, …) | **cadeia única de sessão** `["opus","sonnet","haiku"]` | A chave documentada é `fallbackModel`, um array **global de sessão** (verificado em code.claude.com/docs/en/model-config, 2026-09-07). Não há cadeia por agente. A regra "a cadeia desce de camada, nunca sobe" é preservada; o caso ascendente `haiku→sonnet` não é expressável e fica como regra manual do orquestrador. |
| `skills: [ardosia-brand-guidelines]` em `pipeline-imagem` | movido para `app-frontend` e `redator-artigo` | `pipeline-imagem` não produz figuras; quem aplica identidade visual é o app (§6.3) e as figuras do artigo (`pipeline/04_figures/`). |
| `.claude/agents/auditor-dados.md` | criado (o prompt o define em §11.4, fora do bloco §0-B) | Necessário para o portão da Fase 0'. |

---

## Estado do roteamento

Ver `routing_state.json`. Nenhuma classe de tarefa executou ainda: todas as camadas
correntes são as iniciais da tabela de §9. Nenhum escalonamento, rebaixamento ou
fallback ocorreu.

## Custo acumulado

`cost_ledger.csv` contém apenas o registro do teste de fumaça do hook (marcado
`smoke_test`). Consumo real da Fase 0: **não instrumentado**, por causa de B-02 —
o hook só passa a gravar depois que `settings.json` existir.

---

## 2026-09-07 — Fase 0 (encerramento) e início da Fase 0'

### B-05 · BLOQUEIOS B-02 e B-03 RESOLVIDOS
`.claude/settings.json` foi gravado pelo usuário a partir de `docs/settings.json.proposto`
(conteúdo equivalente; diferenças apenas de formatação JSON e remoção da chave
`_COMENTARIO`). Na sessão corrente os 8 agentes de `.claude/agents/` estão registrados e
disponíveis como `subagent_type`. O roteamento por camada T1–T4 passa a ser operante.

**Verificação do bootstrap (§0-B), forma adotada:** em vez de gastar orçamento com seis
tarefas triviais, a conferência de modelo por agente é feita sobre o `cost_ledger.csv`
gravado pelo hook `SubagentStop` nas invocações reais da Fase 0'. O critério é o mesmo
(cada agente responde no modelo declarado no seu frontmatter); o custo é zero adicional.
Registrado aqui como desvio deliberado em relação à letra de §0-B.

### 0'-01 · Fase 0' iniciada — seis linhas de coleta em paralelo
`coletor-dados` (T1, haiku), seis invocações concorrentes, uma por família de fonte:
demográficas (§4.1), área construída (§4.2), imagem orbital (§4.3), proxies econômicos
(§4.4), reassentamento e AOI (§4.5), agricultura urbana (§4.6).
Respeita `CLAUDE_CODE_MAX_CONCURRENT_SUBAGENTS=6`.

**Desvio deliberado:** para evitar escrita concorrente no mesmo arquivo, cada linha grava
em `data/licenses_parts/<familia>.md` e `data/provenance_parts/<familia>.md`. A
consolidação em `data/LICENSES.md` e `PROVENANCE.md` é feita pelo orquestrador antes do
portão. §11.4 atribui o preenchimento ao `coletor-dados`; a atribuição é preservada — o
que muda é apenas o arquivo de destino intermediário.

Cada linha recebeu também a tarefa de re-verificar as âncoras de §8 que lhe cabem contra
fonte primária, com veredito CONFIRMADO / DIVERGENTE / NÃO LOCALIZADO.

### 0'-02 · Três escalonamentos T1→T2 na Fase 0'

O orquestrador verificou os artefatos em disco em vez de aceitar os resumos dos
subagentes. Três das seis famílias foram reprovadas e reexecutadas **do zero** em T2
(`sonnet`), conforme §9 ("um subagente reprovado é reexecutado do zero na camada superior
com a mensagem de delegação original + motivos da reprovação").

| Família | Motivo | Evidência do orquestrador |
|---|---|---|
| reassentamento | **coordenadas inventadas** | Nominatim consultado em 2026-09-07: Cateme -16.0899/33.9731, Mwaladzi -16.1057/34.0326, "25 de Setembro" sem resultado. O agente gravou pontos a 13 km e 31 km, e inventou o terceiro. Detalhe em `data/_reprovado/0p-reassentamento/MOTIVO.md`. |
| imagem | **contagem não medida** | `probe_stac.sh` conta `.features \| length` com `limit:100` (os "100" de S2 em 2020/2025 são truncamento) e **grava** a linha `não_testado` do Element84 sem emitir requisição. O orquestrador consultou o Element84: responde e devolve `numberMatched` (2020: 194 cenas S2; 2025: 162). Janela termina em `-30`, perdendo 31/out. |
| demográficas | **âncora "confirmada" contra agregador** e **licença por presunção** | Seis âncoras de §8 marcadas "✓ CONFIRMADO (citypopulation.de)", contra §4.0 regra 4. Licenças registradas como "presumido domínio público" e "CC-BY 4.0 (inferido de política HDX)", contra §4.0 regra 1. |

Famílias aprovadas em T1 nesta rodada: **área construída** e **proxies econômicos**
(pendentes ainda do portão formal do `qa-validador`). **Agricultura urbana** em execução.

### 0'-03 · Achado que precisa de decisão do usuário (§4.0, regra 5)
A execução T1 da família demográfica classificou os **Censos INE 1997, 2007 e 2017 como
nível C** (licença não localizável, servidor intermitente). Se isso se confirmar em T2,
a espinha dorsal demográfica do estudo (§5.3, H1, perguntas 1, 2 e 6 de §1) não tem
fonte de nível A, e §4.0 regra 5 obriga o orquestrador a reportar ao usuário antes de
prosseguir. A reexecução em T2 recebeu instrução de esgotar as vias de acesso
(curl direto, catálogo `mozdata.ine.gov.mz` com as condições de uso por estudo,
Wayback Machine) antes de manter a classificação.

### 0'-04 · Infraestrutura de reprodutibilidade (§11.1), pelo orquestrador
A máquina não tinha `conda`, `gdal` nem a pilha geoespacial em Python. Criados:
`pyproject.toml` + `uv.lock` (Python 3.12 fixado), `Dockerfile`, `Makefile` com o grafo
de alvos, `LICENSE` (MIT para código, CC-BY-4.0 para dados derivados),
`.github/workflows/ci.yml` e `pipeline/tests/test_config.py` (11 contratos sobre
`config/`, todos passando). Escolha de `uv` em vez de conda registrada em
`docs/ADR/0002-ambiente-uv-em-vez-de-conda.md`.
Consequência registrada no ADR: nenhum utilitário GDAL de linha de comando existe no
ambiente reproduzido — toda operação raster/vetor passa pela API Python.
O conjunto de regras do `ruff` foi fixado no `pyproject.toml`: sem `select` explícito
ele era herdado de fora do repositório, o que faria CI e máquina do autor divergirem.

`CITATION.cff` (§11.1) **não foi criado**: exige nome do titular, e não há identidade
configurada no git deste repositório. `LICENSE` traz `<TITULAR DOS DIREITOS>` como
marcador. Pendência do usuário.

### 0'-05 · Quarto defeito: DOI inventado na família de agricultura urbana
O orquestrador testou por HTTP todas as URLs contidas nos scripts de
`pipeline/00_fetch/` das famílias aprovadas em T1. Resultado para a citação do GLAD
Global Cropland, gravada em `pipeline/00_fetch/fetch_glad_cropland.py:59`,
`data/provenance_parts/agricultura.md:15` e `data/PROVENANCE.md:51`:

> "Potapov, P., et al. (2022). Global cropland extent, 2000–2019: Annual raster data
> (v1.1). **Scientific Data, 9, 297**. https://doi.org/**10.1038/s41597-022-01292-5**"

O DOI **não resolve**. A referência correta, obtida do Crossref:
Potapov et al., "Global maps of cropland extent and change show accelerated cropland
expansion in the twenty-first century", **Nature Food** 3, 19–28 (2021),
DOI **10.1038/s43016-021-00429-z**. Periódico, volume, página e DOI estavam todos errados.

Isso reprova a família de agricultura urbana por §10 ("nenhum DOI inventado"), apesar
de a análise de suficiência para §1 e H5/H6 daquela entrega ser boa e honesta sobre as
lacunas. A reexecução em T2 **não foi disparada** — ver 0'-07, teto de orçamento.

Outras URLs quebradas encontradas no mesmo teste, a corrigir na reexecução:
`hs.pangaea.de/datasets/published/942325/…` (404), `cloud.sdsc.edu/…NASADEM_HGT_srtm.vrt`
(401 — exige chave OpenTopography, o que afeta a classificação de nível),
`data.digitalearthafrica.org` (sem resposta).
A URL do PANGAEA por DOI (`10.1594/PANGAEA.942325`) resolve e confere:
"Global-scale mining polygons (Version 2)".

### 0'-06 · O hook de custo não instrumenta custo
`cost_ledger.csv` recebeu seis linhas reais na Fase 0', todas com `model=unknown` e
tokens vazios: o payload do `SubagentStop` nesta versão do Claude Code não traz nem o
modelo nem a contagem de tokens nos caminhos que `log_cost.sh` consulta. Consequência:
a conferência de modelo por agente exigida por §0-B **também não pode ser feita pelo
ledger** (era o plano registrado em B-05), e o custo da Fase 0' é conhecido apenas pelas
notificações de tarefa, não pelo instrumento do repositório.

Mitigação aplicada: `scripts/log_cost.sh` passa a gravar o payload bruto em
`data/interim/subagent_stop_payloads.jsonl`. Na próxima fase o esquema real fica visível
e os seletores `jq` podem ser corrigidos. Registrado como pendência, não como resolvido.

### 0'-07 · Teto de orçamento da Fase 0' atingido em T1 — parada para decisão do usuário
Custo T1 da Fase 0' pelas notificações de tarefa (entrada + saída por subagente):
econômicos 62,7K · construída 48,4K · reassentamento 55,3K · imagem 58,7K ·
demográficas 56,1K · agricultura 80,6K = **361,9K de um teto de 400K (90%)**.

`BUDGET.md`, regra 1, dispara em 80%. Quatro das seis famílias precisam de reexecução em
T2 e três já estão em curso; a quarta (agricultura) empurraria o gasto T2 acima do teto
de 250K da fase. Conforme a regra 2, a execução **para aqui** e aguarda decisão explícita
do usuário. Nenhum novo subagente será disparado até então.

### 0'-08 · Duas decisões do usuário (2026-09-07)

**Decisão 1 — teto da Fase 0' elevado.** T1 400K→450K e T2 250K→450K, aplicando a regra 4
de `BUDGET.md`. Justificativa aceita: quatro das seis famílias falharam por integridade, e
a Fase 0' é a que determina se o estudo tem base de nível A — economizar aqui contamina
todas as fases seguintes. A reexecução de agricultura em T2 fica autorizada.

**Decisão 2 — política sobre o INE.** Um documento do INE servido pelo **Internet Archive
(Wayback Machine)**, ou registrado no catálogo **`mozdata.ine.gov.mz`** com as suas
condições de uso, **conta como fonte primária de nível A**: é o documento do INE, apenas
servido de outro lugar. Isso preserva a espinha dorsal demográfica (§5.3, H1, perguntas
1, 2 e 6 de §1) sem violar §4.0.4, porque o que se cita continua sendo o documento do
produtor — e não um agregador que apenas transcreve o número.

Limite da decisão, a respeitar no portão: um **snapshot arquivado do citypopulation.de
continua sendo agregador** e continua não citável. O que muda de estatuto é o PDF/quadro
do INE, não o intermediário.

### 0'-09 · Entrega T2 da família imagem — aprovada pelo orquestrador
`probe_stac.py` + `probe_stac.sh` reescritos: consulta efetiva aos dois endpoints,
contagem por `numberMatched` no Element84 e por paginação somada no Planetary Computer,
janela final por `calendar.monthrange`, erro de rede gravado com a mensagem real,
idempotência verificada. As oito células do Element84 batem com a medição independente
do orquestrador.

Dois achados que a Fase 1 herda:
1. **Discrepância entre catálogos, não resolvida e não forçada:** Planetary Computer ×
   Element84 divergem em `landsat-c2-l2` 2025 (16 × 18) e `sentinel-2-l2a` 2020 (103 × 194).
   §11.3 exige que as duas rotas concordem dentro da tolerância declarada; isso precisa de
   investigação e provavelmente de um ADR antes da Fase 1 fechar.
2. **2010 tem apenas 4 cenas Landsat 5** na estação seca com nuvem ≤ 40%, nos dois
   catálogos. Abaixo do razoável para um composto de mediana. Ampliar `composto.janela_anos`
   só para 2010 quebra o "mesmo protocolo em todos os anos" de §5.1 e exige ADR próprio.

**Planet NICFI: programa descontinuado.** Contrato expirado em jan/2025, extensão até
abr/2025, licitação da fase seguinte cancelada em set/2025, sem sucessor. Sai da lista de
fontes (era nível B, validação opcional); §4.3 do prompt-mestre fica desatualizado nesse
ponto.

### 0'-10 · Limite de 40 turnos truncou duas entregas T2
`maxTurns: 40` no frontmatter de `coletor-dados` interrompeu as reexecuções de
**reassentamento** e **demográficas** antes de escreverem os arquivos de registro.
Não há, nesta versão do Claude Code, forma de retomar um subagente interrompido a partir
da sessão principal (a ferramenta de mensagem disponível só alcança sessões pares, não
subagentes). As duas foram **relançadas com escopo estreito**, com o que já estava
verificado passado na mensagem de delegação para não gastar turnos redescobrindo.

Consequência para as fases seguintes: tarefas de coleta precisam ser decompostas em
unidades que caibam em 40 turnos, ou o `maxTurns` de `coletor-dados` precisa subir.
Registrado como pendência de configuração.

**O que a execução truncada de reassentamento já entregou e o orquestrador aprovou:**
`data/raw/reassentamentos.geojson` com Cateme (node OSM 3899065178) e Mwaladzi
(node OSM 3899065179) resolvidos de verdade, e **25 de Setembro com `geometry: null`** —
Nominatim e Overpass não retornam elemento, e o agente registrou a ausência em vez de
inventar ponto. É exatamente o comportamento que a execução T1 falhou em ter.

Achado substantivo preservado: o HRW 2013 é **internamente inconsistente**. O corpo do
relatório dá 716 famílias em Cateme e 289 em 25 de Setembro (soma 1.005); o sumário
executivo do mesmo relatório dá 1.365 para o total reassentado pela Vale. A âncora de §8
("~1.300 famílias") aproxima-se do segundo número, não da soma do primeiro. A divergência
fica documentada e **não reconciliada** — reconciliar exigiria fonte que ainda não existe.

Defeito menor detectado pelo orquestrador na mesma entrega, a corrigir:
`reassentamentos.geojson.sha256` contém só o hash, sem o nome do arquivo, e por isso
`shasum -a 256 -c` falha. O hash em si confere.

### 0'-11 · AOI corrigida e aplicada
`docs/ADR/0001-aoi-final.md` aceito. `config/study.yaml`: `aoi.bbox.xmax` de **33.95 → 34.10**,
`aoi.status` de `provisorio` → `confirmado`. Demais limites mantidos (folga ≥ 9 km em todos).
O bbox continua dentro de 30°E–36°E, faixa válida de EPSG:32736.

Consequência que a proposta não previa e o orquestrador tratou: o probe STAC havia sido
medido com o bbox antigo. Como `probe_stac.py` lê a AOI do YAML, foi **reexecutado**;
as contagens ficaram idênticas (a extensão não cruzou fronteira de tile), e o CSV
publicado passa a corresponder à AOI confirmada.

Quatro contratos novos em `pipeline/tests/test_config.py` (15 testes, todos passando),
cada um derivado de um defeito real desta fase:
- `test_aoi_confirmada_na_fase_0_linha` — a AOI não pode seguir `provisorio` além da 0'.
- `test_povoados_de_reassentamento_dentro_da_aoi` — teria pegado a AOI que excluía Cateme
  e Mwaladzi. Ignora feições com `geometry: null` de propósito: ausência declarada de
  coordenada não é coordenada fora da AOI.
- `test_coordenada_de_reassentamento_tem_fonte_rastreavel` — reprova quem declara "OSM"
  sem `osm_id` ou com URL de busca em vez de elemento (`/node/`, `/way/`, `/relation/`).
  É o defeito exato da execução T1.
- `test_checksums_de_data_raw_conferem` — `.sha256` no formato `<hash>  <nome>`, hash
  conferido, e `size_bytes` do `.meta.json` igual ao tamanho real. Pegou de imediato o
  Pink Sheet (260418 declarado × 266418 real); campo corrigido pela medição.

### 0'-12 · Achado que restringe a pergunta 3 de §1 — literatura de reassentamento não é nível A
A verificação de licenças da família reassentamento, com acesso efetivo a cada página:

| Fonte | Nível | Motivo |
|---|---|---|
| OpenStreetMap (nós de Cateme e Mwaladzi) | **A** | ODbL 1.0 |
| Human Rights Watch 2013 | **B** | CC BY-NC-ND 3.0 US — proíbe uso comercial e obras derivadas |
| Lillywhite, Kemp & Sturman 2015 | **C** | sem licença localizável; oxfam.org.au devolve 403 |
| Mosca & Selemane 2011 (CIP) | **C** | "todos os direitos reservados" |
| Kirshner & Power 2015 | **C** | paywall Elsevier; via aberta do Unpaywall devolve 403 |
| CIP e Justiça Ambiental (relatórios) | **C** | "todos os direitos reservados" / licença não localizada |
| EIA/RAP — Vale, Riversdale/Rio Tinto, Jindal | **não disponível** | 404 / 406 / não localizado |

Correção de citação obtida no Crossref: o DOI de Kirshner & Power 2015 é
**10.1016/j.geoforum.2015.02.019** — o inicialmente suposto apontava outro artigo.

**Consequência metodológica, por §4.0:** só nível A sustenta número publicado; B entra
apenas como validação marcada e "não sustenta conclusão"; C é proibido. Logo:
- **onde estão** e **quanto ocupam** os reassentamentos — respondível em nível A
  (nós OSM + classificação própria de imagem);
- **quantas famílias** foram reassentadas — **não citável em tabela de resultados**.
  716 / 289 / 84 vêm do HRW 2013, que é B. A âncora de §8 ("~1.300 famílias") herda a
  mesma restrição, e ainda por cima é internamente inconsistente na própria fonte.

Isso não inviabiliza a pergunta 3 de §1, mas muda o que ela pode afirmar: a análise passa
a ser de **área e forma**, com a contagem de famílias como contexto qualitativo marcado
"validação B", nunca como resultado. Precisa de decisão do usuário na Fase 5.

### 0'-13 · Falha estrutural: `maxTurns: 40` consome a tarefa antes da gravação
Três reexecuções T2 terminaram **no limite de turnos, sem gravar nada em disco**:

| Família | Tokens | Escreveu? |
|---|---|---|
| demográficas (2ª tentativa) | 78,9K | não |
| demográficas (3ª tentativa, escopo estreito) | 100,7K | não |
| agricultura (reexecução) | 92,9K | não |

Os arquivos `data/{licenses,provenance}_parts/demograficas.md` continuam sendo os da
rodada T1, com as âncoras marcadas "✓ CONFIRMADO (citypopulation.de)" — exatamente o
defeito que a reexecução deveria corrigir. A família demográfica já consumiu
**235,7K tokens em três execuções** e o artefato em disco continua reprovado.

Diagnóstico: tarefas de verificação são dominadas por I/O (curl, WebFetch, resolução de
DOI). Cada verificação é um turno, e a gravação vem no fim — então o corte em 40 turnos
descarta justamente o produto. Estreitar o escopo não resolveu: a 3ª tentativa foi a mais
estreita e a mais cara.

Correção necessária antes de qualquer nova delegação de coleta (nenhuma foi aplicada
ainda, por causa do teto — ver 0'-14): elevar `maxTurns` de `coletor-dados` **e** exigir
na mensagem de delegação que o agente **grave primeiro um esqueleto do arquivo e o
atualize a cada fonte verificada**, em vez de acumular tudo para o fim.

### 0'-14 · Teto T2 da Fase 0' ultrapassado — segunda parada para decisão
T2 consumido: imagem 68,9K · reassentamento 72,4K · demográficas 78,9K ·
reassentamento (fecho) 63,1K · demográficas 100,7K · agricultura 92,9K =
**476,9K contra o teto revisado de 450K**. Regra 2 de `BUDGET.md`: a execução para e
aguarda decisão explícita do usuário. Nenhum subagente novo foi disparado.

### 0'-15 · INE: verificação feita pelo orquestrador (sem custo de subagente)
Como três delegações falharam em produzir o registro, o orquestrador executou ele mesmo
a parte decisiva, por `curl`, em 2026-09-07:

| Alvo | Resultado |
|---|---|
| `https://www.ine.gov.mz/`, `https://ine.gov.mz/`, `http://ine.gov.mz/` | **000** — sem resposta em todas as variantes; o sítio do INE está fora do ar, não "intermitente" |
| `https://mozdata.ine.gov.mz/index.php/catalog` | **200** — catálogo NADA de pé |
| Censo 2007, III | presente: `catalog/22`, IDNO `moz-ine-censo-iii-2007-v1` |
| Censo 2017, IV | presente: `catalog/24`, IDNO `moz-ine-censo-iv-2017-v1` |
| **Censo 1997, II** | **ausente do catálogo** |
| `catalog/24/get-microdata` | 200 mas **corpo vazio** — nenhum arquivo de dados, nenhuma política de acesso publicada |
| `api/catalog/<id>` (JSON) | 400 — a API do NADA não está exposta neste servidor |

As páginas de estudo trazem metadados ricos (tópicos, conceitos, definições), mas
**nenhum texto de licença ou condições de uso foi localizado**, e não há arquivo de
dados para baixar. Pela §4.0 regra 1, isso mantém o INE em **C** — a decisão do usuário
em 0'-08 resolve a questão da *proveniência* (um documento do INE servido de outro lugar
continua sendo do INE), mas não cria a licença que a regra exige.

Consequência ainda em aberto, e que a Fase 1 não pode herdar sem decisão: o **Censo 1997**
é a linha de base contrafactual da periodização de §2 e da hipótese H1. Ele não está no
catálogo do INE, e o sítio que hospedaria o PDF está fora do ar. A via restante é o
Internet Archive, que ainda não foi esgotada.

### 0'-16 · Correções aplicadas após a segunda parada (decisões do usuário)

**Decisão 1 — destravar a coleta.** `.claude/agents/coletor-dados.md`: `maxTurns` de
**40 → 100**, e acrescentada a seção "Grave incrementalmente (regra dura)": o agente grava
o arquivo de destino com todas as linhas marcadas `PENDENTE` **antes** de verificar
qualquer coisa, e atualiza cada linha imediatamente após verificá-la. Assim uma
interrupção deixa um arquivo parcial e honesto em vez de nada.

Ressalva de implementação: `maxTurns` vem do frontmatter, que é lido na inicialização da
sessão — pode só valer a partir do próximo arranque (mesmo mecanismo do bloqueio B-03).
A regra de gravação incremental, essa, vale de imediato, porque também vai na mensagem de
delegação. **Confirmado em execução:** o esqueleto de `data/licenses_parts/demograficas.md`
apareceu em disco antes de qualquer verificação, na 4ª tentativa.

**Teto T2 da Fase 0': 450 → 700K**, implicado pela decisão de continuar a coleta.

**Decisão 2 — esgotar o Internet Archive antes de mexer na linha de base.** Em curso.

### 0'-17 · Wayback: via confirmada pelo orquestrador
A CDX API do Internet Archive responde para `ine.gov.mz` e o acervo é extenso (o corte em
4.000 registros só de PDFs já satura; consultas amplas demais devolvem 504, é preciso
fatiar por subdiretório).

Documento recuperado, baixado e **lido com sucesso** pelo orquestrador:
`https://web.archive.org/web/20190501151428id_/http://www.ine.gov.mz/iv-rgph-2017/mocambique/censo-2017-brochura-dos-resultados-definitivos-do-iv-rgph-nacional.pdf`
— 8,6 MB, 947 mil caracteres de texto extraível. É a **Brochura dos Resultados Definitivos
do IV RGPH**, documento primário do INE.

**Mas é a edição nacional:** menciona a província de Tete e **não** traz cidade nem
distrito. Nenhum dos três valores de 2017 das âncoras de §8 (305.722, 307.338, 260.843)
aparece nela. Falta localizar a brochura **provincial de Tete** ou os quadros por
distrito, que existem no acervo no padrão
`ine.gov.mz/iv-rgph-2017/mocambique/quadro-<n>-<descrição>.xls`.
Para o Censo 2007 há `http://www.ine.gov.mz/censo2007/rdcenso09/Tete/` arquivado.

O que isto estabelece: **a via do Wayback funciona e devolve documento primário do INE
legível**. Deixa de ser hipótese. O que resta é localizar a edição com desagregação
distrital — tarefa delimitada, delegada com as URLs e o método já apurados.

O prefixo `id_` no caminho do Wayback (`/web/<timestamp>id_/<url>`) devolve o objeto
original sem o cabeçalho de navegação do arquivo, e é o que permite conferir hash do PDF.

### 0'-18 · Entrega T2 da família agricultura — aprovada, com um defeito sistêmico revelado
`data/{licenses,provenance}_parts/agricultura.md` reescritos com verificação por acesso.
DOI do GLAD corrigido para `10.1038/s43016-021-00429-z` (o script guarda nota explícita de
que o anterior não resolvia — comportamento correto). OpenTopography reclassificado:
devolve 401 e exige chave individual, logo **não é acesso anônimo**; substituído pelo
Copernicus DEM GLO-30 via AWS. `data.digitalearthafrica.org` removido (sem resposta).
Dois tiles do Copernicus DEM baixados de fato, com checksum conferido pelo orquestrador.
O agente **recusou-se a fabricar metadados** para um arquivo órfão em `data/raw/`
(`quadro3_tete_2017.xlsx`, deixado por outra família ainda em execução) e reportou a falha
de teste em vez de contorná-la — comportamento exemplar.

**Defeito sistêmico que o novo contrato expôs.** `test_scripts_de_fetch_nao_fixam_a_aoi_no_codigo`
reprova **sete** scripts que copiaram o bbox provisório (`xmax = 33.95`) para dentro do
próprio código, em vez de lerem `config/study.yaml`:
`fetch_esa_worldcover.py`, `fetch_glad_cropland.py`, `fetch_hydro_datasets.py`,
`fetch_lulc_products.py`, `fetch_nighttime_lights.py`, `fetch_wsf_evolution.py`
(e a nota de cabeçalho de `fetch_hydro_datasets.py`).

Consequência já materializada, pega por `test_rasters_de_data_raw_cobrem_a_aoi`: o script
do DEM derivou a lista de tiles da AOI antiga e baixou só a coluna **E033**. Com a AOI
confirmada indo a **34.10 E**, a faixa 34.0–34.1 ficou **sem elevação** — exatamente onde
está **Mwaladzi (34.0326 E)**. Isso inviabilizaria o HAND de várzea (§5.6) num povoado de
reassentamento, e teria falhado em silêncio: nada no repositório acusaria.

Contraria §11.2.1 ("nenhuma etapa depende de estado de sessão"; `config/` é a única fonte
da AOI) e mostra que o ADR 0001 não se propaga sozinho. Correção pendente: todos os
scripts de `00_fetch/` passam a ler a AOI de `config/study.yaml`, e o tile do DEM em E034
precisa ser baixado.

### 0'-19 · Âncoras de 2017 resolvidas contra fonte primária do INE
A 4ª execução da família demográfica bateu no limite de turnos, mas deixou em `data/raw/`
um arquivo órfão, `quadro3_tete_2017.xlsx`, sem `.sha256`, sem `.meta.json` e sem linha de
proveniência. O orquestrador leu a planilha diretamente. Ela é:

> **QUADRO 3. POPULAÇÃO POR IDADE, SEGUNDO ÁREA DE RESIDÊNCIA, DISTRITO E SEXO.
> PROVÍNCIA DE TETE, 2017** — documento primário do INE.

| Unidade | Total | Homens | Mulheres | Soma confere? |
|---|---|---|---|---|
| CIDADE DE TETE | **307.338** | 151.816 | 155.522 | sim |
| DISTRITO DE MAOATIZE (grafia da fonte) | **260.843** | 127.210 | 133.633 | sim |

Isto resolve a ambiguidade da âncora de §8 para 2017: **o número do INE é 307.338**, e
**305.722 não consta deste quadro**. Confirma também 260.843 para o Distrito de Moatize.

**Mas os números ainda não são publicáveis.** Falta a URL de origem, e §11.2.2 exige
proveniência completa para tudo que fica em `data/raw/`. O arquivo foi movido para
`data/interim/proveniencia_a_confirmar/`, com `LEIA-ME.md` registrando hash, tamanho,
o conteúdo lido e o critério de fechamento: quando o Internet Archive voltar, localizar o
snapshot, conferir o sha256 e, só então, promover o arquivo a `data/raw/`. Se o hash não
bater, o arquivo é descartado.

### 0'-20 · Internet Archive fora do ar
Durante a busca pelo Censo 1997 o Internet Archive passou a responder
"Internet Archive services are temporarily offline" (e 504 no endpoint CDX). A via do
Wayback está **validada** (0'-17) mas **indisponível no momento**. O Censo 1997 —
linha de base contrafactual de §2 e de H1 — segue sem localização, agora por
indisponibilidade externa, não por falta de método.

### 0'-21 · Consolidação e limpeza feitas pelo orquestrador
- `scripts/consolidar_registros.py` criado: monta `data/LICENSES.md` e o `PROVENANCE.md`
  da raiz a partir dos fragmentos por família, em ordem determinística, e marca no topo
  quais famílias ainda têm linhas `PENDENTE`. Resolve o conflito de escrita concorrente
  registrado em 0'-01 sem que nenhuma família precise saber das outras.
- `data/PROVENANCE.md` (duplicata criada pela família agricultura em T1, fora do lugar
  previsto por §11.1 e ainda com o DOI inexistente) movido para
  `data/_reprovado/0p-agricultura/`, com motivo registrado.
- Lint: 66 erros nos scripts dos agentes, todos corrigidos. Além do estilo, dois de
  substância: `datetime.utcnow()`/`datetime.now()` sem fuso em quatro scripts de fetch
  (as datas de acesso vão para o `PROVENANCE.md` e precisam ser UTC), e
  `subprocess.run` sem `check` — este último falso positivo, porque o `returncode` já era
  conferido na linha seguinte; tornado explícito com `check=False`.
  Todos os dez scripts continuam com sintaxe válida. `ruff check .` limpo.

### 0'-22 · Estado dos contratos ao fim da rodada
15 de 17 testes passam. Os dois que falham são os defeitos reais ainda abertos:
- `test_rasters_de_data_raw_cobrem_a_aoi` — falta o tile do Copernicus DEM em E034;
  a faixa 34.0–34.1 E, onde está Mwaladzi, segue sem elevação.
- `test_scripts_de_fetch_nao_fixam_a_aoi_no_codigo` — sete scripts ainda fixam o bbox
  provisório `xmax = 33.95` no código, em vez de lerem `config/study.yaml`.

---

## 2026-09-07 (após reinício da sessão) — Fase 0' continua

### 0'-23 · `maxTurns: 100` confirmado em vigor
A primeira delegação depois do reinício usou **57 turnos** e concluiu. O limite de 40 que
truncou cinco execuções era de fato lido na inicialização, como suspeitado em 0'-16.
A verificação pedida em `RETOMAR.md` está feita: a correção vale.

### 0'-24 · Proveniência do Quadro 3 fechada
O Internet Archive voltou. O orquestrador localizou o snapshot e confirmou a origem do
arquivo que estava órfão:

- URL original: `http://www.ine.gov.mz/iv-rgph-2017/tete/quadro-3-populacao-por-idade-segundo-area-de-residencia-distrito-e-sexo-provincia-de-tete-2017.xlsx`
- snapshot `20191114015524`, recuperado com o prefixo `id_`
- **sha256 idêntico** ao do arquivo órfão: `167350d9…e57e5ab`

A origem está **confirmada, não presumida**. O arquivo foi promovido de
`data/interim/proveniencia_a_confirmar/` para `data/raw/`, com `.sha256` e `.meta.json`
completos. O `.meta.json` registra `level: pendente_auditoria` — a proveniência é primária,
mas o texto de licença continua não localizado, e a classificação A/B/C cabe ao
`auditor-dados`.

Descoberta colateral de peso: **os 59 quadros do IV RGPH para a província de Tete estão
arquivados**, no padrão `ine.gov.mz/iv-rgph-2017/<provincia>/quadro-<n>-…xlsx`. O censo de
2017 para Tete está inteiro ao alcance, apesar de `ine.gov.mz` estar fora do ar.

### 0'-25 · Correção da AOI nos scripts — aprovada
Criado `pipeline/00_fetch/_config.py` com `carregar_estudo()`, `carregar_aoi()` e
`tile_sw_corners()`. Os seis scripts que fixavam o bbox passam a lê-lo de
`config/study.yaml`, e os tiles são **derivados** da AOI em vez de listados à mão.

Verificado pelo orquestrador: **17 de 17 testes passam**, `ruff check .` limpo, nenhuma
menção a `33.95` sobrou, e os bounds reais dos rasters cobrem a AOI.

Baixado o tile que faltava, `copernicus_dem_glo30_S17_00_E034_00.tif` — Mwaladzi deixa de
estar sem elevação e o HAND de várzea de §5.6 volta a ser possível.

Dois pontos que o agente tratou bem e merecem registro:
- `tile_sw_corners()` corrige a borda com epsilon, para não puxar um tile a mais quando o
  limite da AOI cai exatamente sobre uma linha de grade;
- `fetch_wsf_evolution.py` gravava um `.log` dentro de `data/raw/`, o que quebrava
  `test_checksums_de_data_raw_conferem` assim que o script rodasse. O log foi para
  `data/interim/`. O contrato pegou um defeito que ainda não tinha se manifestado.

**`copernicus_dem_glo30_S16_00_E033_00.tif` é supérfluo** — confirmado pelo orquestrador
via `rasterio`: seu limite inferior é -15.99986, inteiramente ao norte da AOI, cujo limite
norte é -16.00. **Não foi apagado.** Entra na decisão pendente sobre versionar `data/raw/`,
que hoje tem 195 MB+ e inclui um binário de 111 MB já sinalizado para exclusão do git.

### 0'-26 · Família demográfica fechada — a sexta e última
Entrega verificada pelo orquestrador por leitura direta das fontes, não pelo resumo.
Nenhuma linha `PENDENTE` restante; todos os dez arquivos de `data/raw/` com checksum
conferido; 17 de 17 contratos passando.

**Âncoras de §8 — veredito final:**

| Unidade | 1997 | 2007 | 2017 |
|---|---|---|---|
| Cidade de Tete | **NÃO LOCALIZADO** | **155.870 — CONFIRMADO** | **307.338 — CONFIRMADO** |
| Distrito de Moatize | **NÃO LOCALIZADO** | **215.092 — CONFIRMADO** | **260.843 — CONFIRMADO** |

Fonte de 2007: `web.archive.org/…/ine.gov.mz/censo2007/rdcenso09/Tete/c0705q3`, snapshot
de 2010, "QUADRO 3. POPULAÇÃO POR IDADE, SEGUNDO DISTRITO, ÁREA DE RESIDÊNCIA E SEXO".
O orquestrador extraiu o texto e leu `CIDADE DE TETE 155,870` e
`DISTRITO DE MOATIZE 215,092` — confere com §8 exatamente.
Fonte de 2017: o Quadro 3 do IV RGPH já espelhado (0'-24).

**Três perguntas em aberto, respondidas:**
1. **305.722 não consta de nenhum documento primário consultado.** O número circula em
   agregadores. O valor do INE é 307.338. A âncora de §8 estava com um valor não rastreável.
2. **A sub-enumeração de 3,7–3,8% está documentada** na brochura nacional de 2017, mas
   **não foi incorporada** aos quadros distritais publicados — confirmado numericamente.
   Toda comparação intercensitária tem de dizer isso.
3. **A mudança de limites do Distrito de Moatize entre censos não foi resolvida.** Fica como
   pendência cartográfica. Enquanto não se resolver, a série 1997→2017 do distrito não pode
   ser tratada como comparável sem ressalva.

**Âncora de §8 sobre o codificador do INE — CONFIRMADA** pelo COD-AB do HDX: o Distrito de
Moatize tem três postos (Moatize, Kambulatsitsi, Zóbue) e a Cidade de Tete não tem
subdivisão.

### 0'-27 · O Censo 1997 não existe em fonte primária acessível
Busca exaustiva no Wayback, sete padrões de URL. Confirmou-se apenas a **existência** de
uma brochura provincial de Tete do II RGPH (pasta `05`); as páginas com os números nunca
foram arquivadas. O `mozdata` não lista o Censo 1997, e `ine.gov.mz` está fora do ar.

A decisão do usuário em 0'-08 foi **esgotar o Internet Archive antes** de reformular a
linha de base. O acervo foi esgotado. Consequência, que agora precisa de decisão:

- §2 define 1997–2005 como a fase de **linha de base contrafactual**;
- **H1** afirma aceleração de ~4%/ano (1997–2007) para ~7%/ano (2007–2017);
- sem 1997, a ponta inicial de H1 não tem fonte de nível A e a hipótese **não é testável
  como formulada**.

A família também registra que a **pergunta 6 de §1 (bust e transição, 2015–2025) não é
respondível** com esta família: não há dado demográfico censitário depois de 2017.

### 0'-28 · Auditoria de dados emitida — conjunto A **insuficiente**
`data/DATA_AUDIT.md`. Arbitragens:

- **(a) INE → nível C.** O auditor separa corretamente os dois critérios independentes de
  §4.0: proveniência (regra 4) e licença (regra 1). A decisão do usuário em 0'-08 resolveu
  a proveniência; a licença continua não localizável, e a regra 1 não é condicional.
  Recusar-se a presumir licença a partir da natureza da instituição é a conduta certa.
- **(b) Reassentamento:** confirma HRW = B e o resto = C. Resta em A apenas a localização
  aproximada (dois dos três povoados, pontos e não polígonos) e a evolução do construído
  em buffer via WSF/GHSL.
- **(c) WorldPop/GRID3 → A**, pela licença geral CC-BY 4.0 do produtor.

**Veredito: conjunto A insuficiente.** A Fase 1 pode abrir apenas para os módulos não
demográficos — imagem, forma urbana, luzes noturnas, cultivo e várzea. O pilar demográfico
de §5.3 fica bloqueado.

**Verificação do orquestrador sobre a arbitragem (a).** Notei que a tabela de nível A do
§4.0, tanto no `CLAUDE.md` quanto no prompt-mestre, **nomeia explicitamente** "licença INE
de reprodução com citação" como licença de nível A, o que à primeira vista contradiz o
veredito. Fui atrás da evidência antes de arbitrar:

| Busca | Resultado |
|---|---|
| Páginas de termos/copyright/direitos/condições em `ine.gov.mz`, no Wayback | nenhuma |
| Nota de reprodução no corpo da brochura do IV RGPH | nenhuma |
| Ocorrência de "copyright" no PDF | apenas metadado de fonte tipográfica embutida, não licença do documento |

Não há contradição real: a tabela de §4.0 antecipa que **se** a licença de reprodução do
INE for encontrada, a fonte é A; a regra 1 governa o caso em que não se encontra. O
veredito do auditor está correto e **não foi sobreposto**.

### 0'-29 · Duas decisões do usuário aplicadas

**Linha de base por área construída.** Registrada em
`docs/ADR/0003-linha-de-base-por-area-construida.md`. H1 passa a ser hipótese sobre área,
não sobre habitantes, e precisa ser reescrita em §1 antes da Fase 3. Ganho colateral: o
WSF Evolution é anual, então o pré-tratamento passa de três pontos censitários para
dezenove observações — o teste de tendência paralela de §5.4 fica mais forte, não mais
fraco. Consequência operacional: `fetch_wsf_evolution.py` deixa de ser deferimento e vira
caminho crítico da Fase 1.

**`data/raw/` fora do git, só sidecars versionados.** `.gitignore` passa a excluir os
binários e a manter `.sha256` e `.meta.json` — são eles que garantem que o download futuro
é byte a byte o mesmo arquivo. Vinte sidecars versionados, nenhum binário. Removido o tile
`copernicus_dem_glo30_S16_00_E033_00`, supérfluo por ficar ao norte da AOI (regenerável
pelo script).

Dois defeitos que a mudança expôs, ambos corrigidos:
- o contrato de checksums reprovava o `.gitkeep`; passa a ignorar arquivos ocultos;
- **`wsf_evolution.meta.json` era um sidecar órfão** — descrevia uma fonte deferida ao
  GEE/STAC, sem arquivo espelhado ao lado. Com o `.gitignore` novo isso é pior que estético:
  o repositório passaria a declarar um espelho que ninguém consegue reconstruir. O registro
  foi para `data/interim/`, o script foi corrigido na origem, e o contrato ganhou uma
  verificação de **sidecar órfão** que antes não existia.

17 de 17 contratos passando, `ruff check .` limpo.

### 0'-30 · Portão da Fase 0' — **REPROVADO** na primeira passagem
O `qa-validador` reprovou com quatro motivos. Todos verificados pelo orquestrador e
**todos legítimos**. É o portão funcionando: quatro defeitos que passaram por seis
famílias, uma auditoria e a minha própria conferência.

**1. Arquivo órfão recomendando publicar número de agregador.**
`data/FASE0_DEMOGRAFICAS_SUMMARY.md`, deixado pela execução T1 reprovada, verificava as
seis âncoras contra `citypopulation.de` e recomendava textualmente **"Usar para
publicação"**. Estava solto em `data/`, sem referência de ninguém e sem marca de superado,
convivendo com `DATA_AUDIT.md` como se valesse. Movido para
`data/_reprovado/0p-demograficas/` com motivo.
Detalhe que merece registro: o valor que ele recomendava, 307.338, **é** o do Quadro 3 do
IV RGPH. Chegar ao número certo pelo caminho errado não valida o caminho — e o mesmo
arquivo oferecia 305.722 como alternativa plausível, valor que não consta de documento
primário nenhum.

**2, 3 e 4. A correção da AOI não se propagou para a documentação.**
O ADR 0001 mudou `xmax` de 33.95 para 34.10 e `config/study.yaml` foi atualizado, mas
seguiram declarando o bbox provisório:
- `data/provenance_parts/imagem.md:31` (cabeçalho das contagens STAC)
- `data/provenance_parts/construida.md:11` e `:110`
- `data/provenance_parts/agricultura.md:28`
- `data/raw/copernicus_dem_glo30_S17_00_E033_00.tif.meta.json` e
  `data/raw/hydrorivers_af_v10.gdb.zip.meta.json`, no campo `aoi_bbox`

Isto é a **segunda manifestação** do mesmo problema de 0'-18: o ADR não se propaga sozinho.
Da primeira vez foram os scripts; agora, a documentação de proveniência — e, por
`scripts/consolidar_registros.py`, o erro chegava aos consolidados da raiz.

Tudo resincronizado. O cabeçalho de `imagem.md` passa a declarar 34.10 e a registrar que
as contagens foram **reexecutadas** e ficaram idênticas, porque a extensão a leste não
cruzou fronteira de tile — que era a ambiguidade apontada pelo validador.

**Dois contratos novos**, levando a suíte a 19:
- `test_sidecars_nao_declaram_aoi_divergente` — compara todo `aoi`/`bbox` de `.meta.json`
  contra `config/study.yaml`;
- `test_proveniencia_nao_afirma_aoi_obsoleta` — reprova o bbox antigo em fragmento de
  proveniência, salvo em linha marcada como histórica.

Ambos foram **testados contra o defeito**: reintroduzi `xmax: 33.95` num sidecar e
confirmei que o contrato reprova. Contrato que não foi visto falhar não vale nada.

**Defeito de forma no próprio validador**, registrado para não induzir erro depois: a
resposta começou com `APROVADO`, seguido de `Não.` e só então `REPROVADO`. O formato de
§10 é rígido — primeira linha é o veredito — e um consumidor que lesse só a primeira linha
concluiria o oposto do que o validador decidiu. O veredito real é **REPROVADO**.

### 0'-31 · Reprocessadores institucionais — 2017 desbloqueado em nível A
Tarefa decidida pelo usuário: recuperar o censo do INE por terceiros, já que o INE está
fora do ar. A distinção aplicada, que mantém isto dentro de §4.0 em vez de abrir exceção:
**reprocessador institucional com licença própria e verificável** (UNSD, CIESIN, OCHA,
WorldPop, IPUMS) não é **agregador que apenas transcreve** (citypopulation.de, Wikipedia).
Classifica-se pelo nível da licença do reprocessador; o INE é a origem declarada.

**Achado principal — HDX COD-PS, vintage 2017, CC BY-IGO 3.0, nível A.** Verificado pelo
orquestrador lendo o CSV:

| Unidade | P-code | Homens | Mulheres | Total |
|---|---|---|---|---|
| Cidade De Tete | MZ1006 | 151.816 | 155.522 | **307.338** |
| Moatize | MZ1012 | 127.210 | 133.633 | **260.843** |

Batem com o Quadro 3 do IV RGPH **exatamente, inclusive na desagregação por sexo**. As duas
âncoras de 2017 deixam de ser nível C e passam a ser **publicáveis em núcleo A** — não por
mudança de critério, mas porque existe um segundo caminho, com licença que se pode ler.

**Achado do orquestrador — COD-PS vintages 2024 e 2025.** A rodada do agente consultou só o
vintage 2017. Pela API do CKAN o mesmo dataset publica 2023, 2024 e 2025. Espelhado o de
2025: Cidade de Tete **460.248**, Moatize **349.103**. Nível A, **selo `modelado`** (são
projeções do INE, não contagem). Isso dá à **pergunta 6 de §1** a ponta que o `DATA_AUDIT.md`
declarava inexistente: de "não respondível" para "respondível com ressalva de selo".

**1997 e 2007 continuam sem nível A.** A Cidade de Tete em 1997 (101.984) foi confirmada
pelo UNSD Demographic Yearbook 2007, tabela 8 — mas a licença da ONU proíbe redistribuição
e derivadas, o que a torna **nível B**: serve de validação marcada, não sustenta conclusão.
O Distrito de Moatize em 1997 e ambos os valores de 2007 não foram recuperados.

**CIESIN/SEDAC está fora do ar** (000 em todas as tentativas, confirmado pelo orquestrador),
e era a via mais promissora para 1997 e 2007 por distrito, porque o GPW publica os dados de
entrada por unidade administrativa. Não é falha de busca; é indisponibilidade externa, como
a do próprio INE. Fica registrado para retomada.

**`docs/ADR/0003` permanece válido:** a linha de base de 1997 não foi recuperada em nível A,
então a reformulação por área construída continua sendo a decisão em vigor.

### 0'-32 · `DATA_AUDIT.md` revisto — bloqueio reduzido, não removido
Veredito global continua **conjunto A insuficiente**, mas o alcance do bloqueio caiu de
"pilar demográfico inteiro" para "extremidade 1997–2007 e tabulações domiciliares do INE".

O que passou a ser respondível em nível A:
- **Âncoras de 2017**, citando o HDX/OCHA e não o INE. O auditor formula a distinção com
  precisão: o valor via documento do INE (nível C) e o mesmo valor via reprocessador com
  licença própria (nível A) **são coisas distintas**, mesmo sendo o mesmo número.
- **P1 e H1 reformuladas** pelo ADR 0003, via WSF Evolution — e com resolução temporal
  superior à formulação censitária original.
- **P6 e P7**, com a ponta de 2025 do COD-PS, sob selo `modelado`.

**Ressalva que o auditor levantou e que o orquestrador considera o achado mais fino da
revisão: risco de circularidade em H4.** Se a projeção do INE para 2025 assume crescimento
geométrico fixo, usá-la para testar "população cresce enquanto a atividade estagna"
confirmaria a hipótese **por construção, não por evidência**. H4 fica rebaixada a parcial e
**não pode ser sustentada apenas pela projeção**. Precisa de dado independente da projeção
— área construída classificada, contagem de edificações, ou o Censo 2027 quando sair.

Seguem bloqueados: extremidade 1997/2007, P3 (reassentamento, por §4.5 ser B/C) e
P8/H6 (dimensão domiciliar).

### 0'-33 · Teto da Fase 0' estourado — 101% do total, 120% em T2
Registrado em `BUDGET.md`, não absorvido em silêncio (regra 3). T1 fechou em 80% do teto;
T2 em **120%**; a fase inteira em **101%**.

A leitura do estouro importa mais que o número. **Cinco das oito invocações T2 anteriores ao
reinício terminaram no limite de 40 turnos sem gravar nada**, somando ~473K de trabalho
perdido — a família demográfica sozinha gastou 331K em quatro tentativas para entregar um
esqueleto. Depois do reinício, com `maxTurns: 100`, **nenhuma das seis invocações foi
truncada**.

O custo médio por invocação subiu de 84,7K para 107,9K. Isso não é regressão: as invocações
passaram a chegar ao fim. Pagar 108K por entrega completa é melhor que pagar 95K por
arquivo vazio.

Sem o bloqueio de configuração, a estimativa é que a fase teria fechado em **1.100–1.200K**,
dentro do teto. O estouro é atribuível à configuração, não ao dimensionamento do orçamento
nem ao escopo da fase.

**Implicação registrada para a regra 4:** os tetos das fases 1 a 7 pressupõem pouca
reexecução. Esta fase teve quatro das seis famílias reprovadas por integridade mais uma
reprovação no portão. Se a taxa se mantiver, os tetos de 1, 2b e 5 são otimistas — revisar
ao fim da Fase 1, com número real.

### 0'-34 · Portão da Fase 0' — **APROVADO** na segunda passagem
Dez itens verificados com evidência. O validador não aceitou a minha palavra sobre os
contratos novos: **reintroduziu o defeito manualmente** e confirmou que
`test_sidecars_nao_declaram_aoi_divergente` e `test_proveniencia_nao_afirma_aoi_obsoleta`
reprovam quando o `aoi_bbox` diverge ou quando `33.95` aparece sem marcador histórico, e
voltam a passar depois da reversão. É a conduta certa.

Julgou também procedente, e não exceção disfarçada, a distinção entre **reprocessador com
licença própria** (HDX COD-PS, CC BY-IGO) e **agregador sem licença própria**
(citypopulation.de) — a questão que decidiu o desbloqueio de 2017.

19 de 19 contratos, `ruff` limpo, os dez arquivos de `data/raw/` com checksum conferido,
`LICENSES.md` e `PROVENANCE.md` sem nenhuma linha pendente.

**FASE 0' ENCERRADA.**

---

## 2026-09-07 — Fase 1 (Pipeline de imagem) — início

Aberta conforme o veredito de `data/DATA_AUDIT.md`: sem restrição para imagem, forma
urbana, luzes e cultivo, e para P1/H1 via área construída.

### 1-01 · WSF Evolution obtido — o pressuposto do ADR 0003 se confirma
`fetch_wsf_evolution.py` deixou de ser script de deferimento e baixa de verdade. Dois tiles
de 2°×2° cobrem a AOI: `wsf_evolution_S18E032.tif` e `S18E034.tif`.

**Licença CC BY 4.0 confirmada pelo orquestrador** na página do produtor
(`download.geoservice.dlr.de/WSF_EVO/`), com link para o texto da Creative Commons.
Nível **A**, acesso anônimo, sem cadastro. O ADR 0003, que apoiou toda a linha de base
nesta fonte, tinha base — agora verificada e não presumida.

**Verificação de conteúdo pelo orquestrador**, com `rasterio`: EPSG:4326, ~30 m, `int32`,
valores em [0, 2015] representando o **ano de primeira detecção do assentamento** (0 = sem
dado). A união dos dois tiles cobre a AOI inteira.

Contagem bruta no recorte da AOI, tile principal — **teste de fumaça, não achado**:

| até | pixels | ≈ km² |
|---|---|---|
| 1997 | 38.000 | 34,2 |
| 2005 | 45.261 | 40,7 |
| 2011 | 56.669 | 51,0 |
| 2015 | 64.960 | 58,5 |

A curva tem inflexão por volta de 2005, o que é coerente com H1 reformulada em área. **Mas
isto não pode ser lido como resultado**: a contagem bruta inclui a pegada minerária, e §5.1
exige exatamente a separação em três camadas mutuamente exclusivas antes de qualquer leitura.
Registrado apenas como prova de que o dado é utilizável.

O tile oriental tem 0,12% de assentamento — é a área de Cateme e Mwaladzi, rural esparsa.
Coerente.

Dois pontos que o agente tratou bem: a grade real de tiles do DLR **não é documentada** e
foi obtida do `grid.geojson` do portal; e o host do DLR encadeia até uma raiz TLS ausente do
`cafile` padrão do OpenSSL deste ambiente, o que o script contorna com `certifi.where()` —
registrado na proveniência para não ser confundido com problema da fonte.

**Correção do orquestrador:** `certifi` era usado mas **não declarado** em `pyproject.toml`,
chegando só por transitividade de `requests`. Numa reresolução poderia sumir e o download
falharia de forma obscura. Declarado explicitamente, com o motivo no comentário. §11.2.1
exige que nenhuma etapa dependa de estado não fixado — dependência transitiva é isso.

### 1-02 · ADR 0004 — Planetary Computer é o catálogo canônico
A divergência entre catálogos tem causa, e ela derruba um pressuposto meu. O **Element84
responde à busca anonimamente, mas os assets do Landsat ficam num bucket Requester Pays do
USGS, que exige conta AWS com faturamento.** Ou seja: o E84 não é rota "sem conta" para
Landsat, ao contrário do que a Fase 0' registrou ao ver o `/search` funcionar. Contar cenas
não é o mesmo que conseguir lê-las.

Decisão do ADR: **Planetary Computer canônico** para Landsat e Sentinel-2, com
`planetary_computer.sign_inplace`. Custo aceito e declarado: 3 cenas Landsat 9 de 2025
ausentes do PC (16 contra 19 do E84), acima do piso para mediana.

### 1-03 · 2010 não tem Landsat 5 — o problema é pior que "poucas cenas"
`compostos.py 2010` falhou de forma explícita e correta: **nenhuma cena LANDSAT_5**.
`config/study.yaml` atribui L5 a 2010 e manda evitar L7 por causa das falhas SLC-off.

Levantamento do orquestrador no Planetary Computer (estação seca, nuvem ≤ 40%):

| ano | Landsat 5 | Landsat 7 |
|---|---|---|
| 2008 | 6 | 3 |
| 2009 | 3 | 5 |
| **2010** | **0** | 4 |
| 2011 | 1 | 8 |
| 2012 | 0 | 6 |

A ressalva anterior — "2010 tem 4 cenas" — estava **errada por omissão**: o probe da Fase 0'
contou a coleção `landsat-c2-l2` inteira, sem filtrar plataforma. As quatro cenas de 2010
são todas Landsat 7. O sensor declarado não existe no acervo para esse ano e essa AOI.

Isso muda o ADR 0005 de "janela curta" para "sensor indisponível", e invalida as duas
saídas óbvias:
- **ampliar a janela para ±1 ano** dá apenas 4 cenas L5 (3 de 2009, 1 de 2011) e atravessa
  2009–2011, borrando a fronteira entre Implantação e Boom — a operação da Vale começa em
  maio de 2011 — que é justamente o que a periodização de §2 quer medir;
- **mover a âncora para 2008** (L5 = 6) mantém a fase, mas desiguala os intervalos da série.

Resta usar **Landsat 7 em 2010** e tratar as falhas SLC-off. Não decidido por teoria: a
questão empírica é quantos pixels da AOI ficam **sem nenhuma observação válida** na mediana
das 4 cenas. As falhas do SLC-off, no mesmo par path/row, são parcialmente coincidentes
entre datas, então a compensação por múltiplas datas **não pode ser presumida** — tem de
ser medida. Delegado com essa instrução.

`maxTurns` de `pipeline-imagem` elevado de 60 para 120 (só vale após reinício da sessão).

### 1-04 · DEFEITO GRAVE — falhas do SLC-off contadas como observação válida
O composto experimental de 2010 declarou **95,7% dos pixels com as 4 observações** e
**nenhum pixel sem observação**. Bom demais para Landsat 7 SLC-off. O orquestrador foi
conferir na fonte.

**Passo 1 — as falhas são reais.** Lendo o `qa_pixel` das 4 cenas direto do Planetary
Computer, dentro da AOI: **8,40% a 8,83% de pixels de *fill* por cena**. Não é ruído.

**Passo 2 — a distribuição verdadeira difere muito da declarada.** Calculando a contagem de
observações válidas a partir das quatro bandas de qualidade:

| Observações válidas | Real (qa_pixel) | Declarado pelo composto |
|---|---|---|
| 0 | 56 px (0,002%) | 0 |
| 1 | 82.687 (2,97%) | 0 |
| 2 | 163.593 (5,88%) | 149 |
| 3 | 464.694 (16,69%) | 120.284 |
| 4 | 2.072.727 (74,46%) | 2.664.623 (95,68%) |

**Passo 3 — a causa.** A lógica de bits em `_stac_common.py` está **correta** (fill=0,
dilated=1, cirrus=2, cloud=3, shadow=4). O erro está antes dela:

> O item STAC declara **`nodata: 1`** para o asset `qa_pixel` — e **1 é justamente o valor
> de *fill***. O carregador honra esse `nodata` e substitui os pixels de falha pelo seu
> próprio valor de preenchimento, **0**. Aí `qa & bits_ruins == 0` dá **verdadeiro**, porque
> zero não tem nenhum bit ruim aceso. **A falha vira "válida".**

Confirmado na fonte: `raster:bands[0].nodata == 1` no STAC, o GeoTIFF sem nodata próprio, e
o valor 1 presente e abundante nos dados.

**Alcance: todos os compostos Landsat, não só 2010.** Os cinco anos já gravados em
`data/processed/imagery/` têm a mesma contaminação — em 2010 pelas falhas do SLC-off, nos
demais pelo *fill* de borda de cena. A mediana foi calculada sobre pixels de preenchimento
tratados como reflectância válida.

**Correção a aplicar:** impedir a remapeação de nodata ao carregar o `qa_pixel` **e**, por
defesa em profundidade, tratar `qa == 0` como inválido — 0 não é valor legítimo de
`QA_PIXEL` no Collection 2, então a regra é segura e barata. Os cinco compostos e todos os
índices precisam ser **regerados**.

Registro do que isto diz sobre método: a lógica estava certa, os bits estavam certos, o
teste de faixa passou, e mesmo assim o produto estava errado. **O que denunciou foi um
resultado bom demais**, conferido contra a fonte. Nenhum contrato existente pegaria isso —
precisa de um que compare a contagem de observações válidas do composto com a calculada
direto das bandas de qualidade.

### 1-05 · Compostos e índices gerados, com dois defeitos de faixa
Cinco anos (2000, 2005, 2015, 2020, 2025) em `data/processed/imagery/`, com índices.
Os contratos escritos pelo próprio agente reprovaram dois casos, e estão certos:
`ndbi_2000` e `mndwi_2000` com **1 pixel** fora de [-1, 1], `evi_2025` com **4 pixels**.

**Não é erro de escala** — o orquestrador conferiu a distribuição completa: p1 e p99 de
todos os índices estão em faixa plausível para savana semiárida (NDVI p99 entre 0,39 e
0,63). É instabilidade numérica com o denominador perto de zero. A correção é mascarar o
denominador, não afrouxar o contrato.

### 1-06 · Defeito de máscara corrigido e verificado
Causa confirmada e corrigida em `_stac_common.py` e `compostos.py`:
- `stac_cfg` faz o `odc-stac` ignorar os metadados `raster:bands` do `qa_pixel`, de modo
  que o valor real de *fill* (1) chega intacto à máscara;
- defesa em profundidade: `qa == 0` passa a ser inválido, porque 0 nunca é valor legítimo
  de `QA_PIXEL` no Collection 2 — mesmo um pixel limpo tem o bit *clear* aceso.

**Verificação do orquestrador contra a medição independente:**

| | 4 obs | 0 obs |
|---|---|---|
| medição do orquestrador (3 bits) | 74,46% | 0,002% |
| pipeline corrigido (5 bits, mais estrito) | 73,36% | 0,005% |

A diferença é exatamente o cirrus e a nuvem dilatada que o pipeline mascara a mais.
**Correção confirmada.** O agente também verificou que o contrato novo,
`test_nobs_bate_com_calculo_direto_do_qa_pixel`, reprova com 9,5% de erro quando o defeito
é reintroduzido — ele recalcula a contagem por `rasterio` puro, sem passar pelo
`odc.stac.load`, que é o que dá independência ao contrato.

O limiar de denominador dos índices saiu de constante fixa no código para
`config/tolerances.yaml → processamento_indices.denominador_minimo`, calibrado contra os
pixels que de fato falhavam. Mascara no máximo 1,7% por índice e ano.

### 1-07 · Decisão de 2010 aplicada — Landsat 7
`config/study.yaml`: 2010 passa a `missao: LANDSAT_7`, com o motivo no comentário.
`composto.janela_anos` permanece **1** em todos os anos — o protocolo de §5.1 fica uniforme
e a fronteira Implantação/Boom não é borrada. Adendo registrado no ADR 0005.

Duas ressalvas que acompanham este produto daqui em diante: **2010 é o único ano com sensor
diferente do previsto e com falhas sistemáticas de sensor**, então o `nobs` tem de ser
publicado junto e a Fase 2 precisa checar se a métrica de forma urbana é sensível à
contagem de observações; e a primeira medição estava **inflada** (95,68% contra 73,36%
reais), de modo que a decisão teria sido a mesma por evidência errada.

### 1-08 · Compostos e índices completos nos seis anos-âncora
`data/processed/imagery/`: 36 rasters — composto + NDBI, NDVI, MNDWI, EVI e NDWI para
2000, 2005, 2010, 2015, 2020 e 2025, todos em EPSG:32736, 30 m, com `.meta.json` e selo
`observado`. 30 contratos passando, `ruff` limpo, `pytest` com código de saída 0.

Falta da Fase 1: a **classificação em três camadas mutuamente exclusivas** (urbano fora dos
polígonos de mineração, reassentamento em buffers dos povoados, industrial-minerário em
Maus et al. mais digitalização) e a **matriz de acurácia por ano**, com mínimo de 85% e
kappa.

### 1-09 · Classificação REPROVADA pelo orquestrador — falha metodológica, não defeito de código
O agente relatou honestamente acurácia 0,73–0,82 contra a meta de 0,85, e kappa 0,50–0,63
contra 0,70, sem recalibrar para passar. A conduta foi correta. **O produto, não.**

Verificação do orquestrador contra o WSF Evolution, que é nível A e independente:

| ano | classificado (km²) | WSF acumulado (km²) | razão |
|---|---|---|---|
| 2000 | 85,6 | 35,8 | 2,4× |
| 2005 | 111,5 | 40,7 | 2,7× |
| 2010 | 106,3 | 48,0 | 2,2× |
| 2015 | 102,0 | 59,0 | 1,7× |

Três sintomas, uma causa:

1. **Jaccard de 0,002 a 0,044** com o WSF. Não é só excesso de área — a classificação **não
   encontra os mesmos lugares**. Duas máscaras de construído sobre a mesma cidade não podem
   ter sobreposição quase nula.
2. **A série não é monotônica**: 85,6 → 111,5 → 106,3 → 102,0 → 99,5 → 107,8. Área
   construída não encolhe. O WSF, monotônico por construção, faz 35,8 → 40,7 → 48,0 → 59,0.
3. **A fração construída é quase constante**: 3,4%, 4,4%, 4,2%, 4,1%, 4,0%, 4,3% da AOI.

O terceiro sintoma explica os outros dois. Os **limiares adaptativos por percentil**
selecionam, por construção, uma fatia parecida da imagem em todo ano. O produto não mede
crescimento urbano: mede o percentil escolhido. Foi uma resposta compreensível ao problema
real que o agente diagnosticou — confusão espectral entre solo exposto e construído na
savana semiárida em estação seca, que com limiares de literatura classificava ~96% da AOI
como construído — mas troca um erro grosseiro por um artefato silencioso, que é pior.

**A acurácia relatada também não sustenta nada.** Os pontos de validação vieram de uma
**segunda regra espectral**, não de fotointerpretação. Isso mede concordância entre duas
regras sobre o mesmo sinal confundido — é circular. §5.1 exige pontos fotointerpretados, e
o próprio agente declarou a limitação.

**Escalonamento por §9:** falha de Fase 1 vai de T2 para **T3 (`desenho-causal` recalibra
amostras)**. É a decisão certa aqui, porque o que falhou não é código: é a estratégia de
amostragem e calibração.

**O que a reexecução tem de atacar:**
- **Separação fenológica.** Construído é espectralmente estável entre estação chuvosa e
  seca; solo exposto esverdeia na chuva. `config/study.yaml` já traz
  `composto_fenologico` com a estação chuvosa de novembro a abril, previsto em §5.6.1 para
  cultivo — é o mesmo instrumento que resolve a confusão aqui.
- **Consistência temporal.** Construído é quase permanente; desaparecimento é sinal de erro,
  não de dinâmica. A série tem de ser quase monotônica por construção ou penalizar reversão.
- **Amostras de treino ancoradas.** O WSF Evolution (nível A, 30 m, valor = ano de primeira
  detecção) pode semear treino, desde que declarado — mas então **não pode ser reutilizado
  como validação**, sob pena de circularidade. A validação precisa de fotointerpretação.

Entregas anteriores da Fase 1 (compostos e índices dos seis anos) **continuam válidas** —
o que foi reprovado é só a camada de classificação.

### 1-10 · Recalibração em T3 — o artefato do percentil sumiu, mas apareceu outro
A execução T3 parou no limite de 50 turnos, mas entregou o essencial da recalibração:
`compostos_chuva.py` (composto de estação chuvosa), `ndvi_amplitude_*` para os seis anos,
`amostras_validacao.py` em construção, e as camadas regeradas.

Verificação do orquestrador contra o WSF:

| ano | construído (km²) | WSF (km²) | razão | % da AOI |
|---|---|---|---|---|
| 2000 | 14,1 | 35,8 | 0,4 | 0,6% |
| 2005 | 20,4 | 40,7 | 0,5 | 0,8% |
| 2010 | 29,0 | 48,0 | 0,6 | 1,2% |
| 2015 | 38,7 | 59,0 | 0,7 | 1,5% |
| 2020 | 41,1 | — | — | 1,6% |
| 2025 | 48,1 | — | — | 1,9% |

**A série passou a ser monotônica** e a razão com o WSF saiu de 2,4× acima para 0,4–0,7×.
O artefato do percentil acabou — a separação fenológica funcionou.

**Mas há um problema de primeira ordem para H1**, que o orquestrador identificou:

| período | classificação | WSF |
|---|---|---|
| 2000–2005 | 7,7%/ano | 2,6%/ano |
| 2005–2010 | 7,3%/ano | 3,4%/ano |
| 2010–2015 | 5,9%/ano | 4,2%/ano |

**As duas fontes discordam na direção da tendência.** A classificação desacelera; o WSF
acelera. Depois do ADR 0003, H1 é precisamente uma hipótese sobre **aceleração da área
construída** — então as duas dão respostas opostas à pergunta central do estudo.

A razão classificação/WSF sobe de 0,4 para 0,7 ao longo da série. Isso é compatível com
**sensibilidade de detecção que melhora com o tempo**: os sensores mudam entre os anos-âncora
(L7 em 2000, L5 em 2005, L7 em 2010, L8 em 2015 e 2020, L9 em 2025, mais Sentinel-2 de 2015
em diante). Se a capacidade de detectar construído esparso cresce, **o crescimento medido
fica confundido com a capacidade de medir**. §5.1 exige "mesmo protocolo em todos os anos"
justamente para evitar isso, mas o protocolo idêntico sobre sensores diferentes não garante
sensibilidade idêntica.

Isto precisa ser resolvido antes da Fase 3, e provavelmente antes de fechar a Fase 1: um
viés que cresce monotonicamente com o tempo é indistinguível de tendência, e é exatamente o
que o desenho causal de §5.4 tentaria interpretar.

`maxTurns` de `desenho-causal` elevado de 50 para 110 (vale após reinício).

### 1-11 · Viés de sensor medido — e a série própria perde o papel de série de tendência
`docs/ADR/0008-vies-de-sensor-na-serie.md`. Duas coisas merecem registro.

**O agente corrigiu o orquestrador.** O teste que eu pedi — "classificar 2015 com Landsat
isolado e com Landsat+Sentinel-2" — **era vazio**: o composto de estação seca de 2015 não
contém Sentinel-2. O S2 L2A só cobre a AOI a partir de dez/2015, então entra apenas em 2020
e 2025. Verificado pelo orquestrador: `composto_2015_…meta.json` traz
`colecao_sentinel2: None` e dez cenas Landsat 8. O agente conferiu em vez de executar a
instrução no escuro. É a conduta certa, e eu devia ter checado antes de mandar.

**O teste que valia foi feito.** Mediana de observações válidas por pixel na estação seca —
verificada de forma independente pelo orquestrador:

| ano | 2000 | 2005 | 2010 | 2015 | 2020 | 2025 |
|---|---|---|---|---|---|---|
| mediana de observações | 3 | 4 | 4 | 10 | 31 | 42 |

**Variação de 14× ao longo da série.** Degradando 2015 à capacidade de observação de 2000,
a área classificada cai de 51,7 km² para 42,9 km²: **−17,0% só por reduzir o número de
observações**, sem mudar nada mais. O viés estimado é de **+1,25%/ano** — mesma ordem de
grandeza do efeito que o estudo procura.

**Decisão do ADR, aceita pelo orquestrador:**
1. A série própria **deixa de ser a série primária de tendência** para 1997–2015. O
   **WSF Evolution** assume esse papel, com protocolo único em todos os anos.
2. A classificação própria fica com o que só ela faz: **separar as três camadas** —
   urbano, reassentamento e industrial-minerário.
3. Testar H1 com a série própria **seria inválido**, porque o viés tem a mesma ordem de
   grandeza do efeito.
4. **Direção do viés:** ele infla o crescimento **tardio**, porque há mais observações
   depois. Corrigi-lo torna a desaceleração da série própria ainda mais acentuada — ou seja,
   a discordância com o WSF não se resolve, se agrava.
5. 2005 e 2010 têm a **mesma** mediana de observações (4): é o trecho menos contaminado
   da série, e o único diretamente comparável sem correção.
6. Toda quebra de §5.4 sobre a série própria passa a exigir **placebo adicional**.

Isto fecha a questão que o orquestrador levantou em 1-10, com número em vez de argumento.

### 1-12 · Teto T3 da Fase 1 estourado — 170%
T2 em 86% do teto (777K de 900K), **T3 em 170%** (340K de 200K), fase em 93% antes de
fechar. Registrado em `BUDGET.md`, não absorvido (regra 3).

A causa não é retrabalho. O teto de T3 supunha **uma** invocação, para recalibrar amostras
após reprovação. Houve duas, e a segunda não estava prevista: nasceu de um problema que só
apareceu depois da recalibração — o viés de sensor de +1,25%/ano, da mesma ordem de
grandeza do efeito procurado. Essa segunda invocação **mudou o desenho do estudo** (ADR
0008). O teto estava errado, não o gasto.

Somou-se a isso o desperdício por truncagem: as duas invocações bateram no limite de 50
turnos, mesmo padrão do `coletor-dados` na Fase 0'. `maxTurns` já corrigido para 110.

### 1-13 · Validação fechada — e ela revela que o critério de §10 não discrimina
`data/processed/acuracia_por_ano.csv`, `matriz_confusao_por_ano.csv`,
`concordancia_wsf.csv` e 288 pontos interpretados em `data/processed/validacao/`.
38 de 38 contratos, `ruff` limpo, reexecução byte a byte idêntica em 28 artefatos.

**Duas correções de desenho que o agente fez antes de interpretar, e sem as quais o número
seria vazio:**
1. **Cegamento.** O `id_ponto` era atribuído depois de ordenar por estrato — 001 a 024 eram
   sempre construído — e cada folha continha um único estrato. O intérprete saberia a classe
   do mapa **antes de olhar**. Corrigido com `id_cego`, permutação determinística que mistura
   os estratos; as folhas só mostram ele. Era um vício que invalidaria toda a validação.
2. **Renderização.** O realce por percentil **banda a banda** decorrelaciona as bandas: o
   ruído de cada uma recebe ganho distinto e vira cor. Os recortes de 2000 saíam como
   mosaico de arco-íris, ilegíveis. Trocado por normalização pelos percentis da AOI com um
   **único** ganho comum às três bandas.

**O achado que importa: o critério de §10 não discrimina neste problema.**

| ano | acurácia global | IC95 | kappa | **acurácia do usuário, `construido`** | peso do estrato construído |
|---|---|---|---|---|---|
| 2000 | 0,997 | ±0,001 | 0,68 | **0,52** | 0,56% |
| 2005 | 0,997 | ±0,002 | 0,74 | **0,58** | 0,83% |
| 2010 | 0,991 | ±0,002 | 0,43 | **0,27** | 1,18% |
| 2015 | 0,950 | ±0,084 | 0,23 | **0,54** | 1,55% |
| 2020 | 0,869 | ±0,133 | 0,09 | **0,52** | 1,65% |
| 2025 | 0,993 | ±0,004 | 0,77 | **0,63** | 1,93% |

§10 exige acurácia global ≥ 85% por ano. **Todos os anos passam.** Mas o construído é
0,56% a 1,93% da AOI: **um mapa que errasse toda a classe rara ainda daria ≈0,98.** O
critério de §10, aplicado a uma classe rara, é satisfeito por construção e não informa nada.

O número que informa é a **acurácia do usuário do construído: 0,27 a 0,63.** Entre 37% e 73%
do que o mapa chama de construído não é construído. O kappa acompanha e desaba: 0,09 em
2020, 0,23 em 2015, 0,43 em 2010.

**A acurácia do produtor não é utilizável neste n:** um ponto do estrato não-construído
carrega ~4,1% da área da AOI. Está documentado em coluna própria, em vez de reportado como
se fosse estimativa estável.

**O IC95 da acurácia global chega a ±0,133** (2020). Estreitar para ±0,03 exigiria ~470
pontos por estrato e ano, ~2.800 recortes — inatingível por interpretação nesta escala.

**WSF: não valida, porque semeia o treino.** Emitido à parte como concordância entre
produtos, com a dependência declarada: Jaccard 0,37→0,58 e área própria 31–59% abaixo do
WSF, coerente com o ADR 0008.

**Premissas frágeis, todas declaradas pelo agente:** o erro do intérprete entra como se
fosse erro do mapa; a 30 m, construído esparso e solo exposto são indistinguíveis para
qualquer intérprete; o estrato construído inclui a pegada minerária, então "construído" ≠
"urbano"; 7 pontos ficaram indeterminados e a acurácia é condicionada aos decidíveis; e a
validação usa **a mesma imagem** que alimentou o classificador.

O alvo `imagery` do `Makefile` foi implementado — estava em `exit 1` apesar de a fase estar
completa.

### 1-14 · Duas decisões do usuário — o critério de §10 foi corrigido na origem

**Decisão 1 — trocar o critério de acurácia.** `docs/ADR/0009-criterio-de-acuracia-para-classe-rara.md`.
§10 foi reescrito **no `CLAUDE.md` e no prompt-mestre**: a acurácia global sai de critério e
vira contexto; entram acurácia do usuário e do produtor por classe, com IC95, mais kappa com
peso de critério, e a **prevalência publicada junto** — sem ela nenhum desses números é
interpretável.

Deliberadamente **não se fixou limiar numérico** para a acurácia do usuário. Um limiar
arbitrário sobre classe rara reproduziria o mesmo vício na direção oposta, e a literatura
não sustenta um valor único para construído esparso a 30 m em ambiente semiárido. O que se
exige é medir, publicar com IC, e declarar a incerteza em toda conclusão derivada.

Registro do que tornou o problema visível: a comissão só apareceu porque a validação usou
**amostragem estratificada pelo mapa** com o estimador de Olofsson, que obriga a reportar
por classe. Uma amostragem simples teria dado acurácia global alta, satisfeito §10 e
escondido a comissão — com muito menos trabalho.

A Fase 1 **não é reprovada retroativamente**: ela mede e publica exatamente o que o critério
novo exige. O que muda é qual número decide — 0,27–0,63, não 0,87–0,997.

**Decisão 2 — papel restrito da classificação.** Ela serve para **separar as três camadas**,
que é o que só ela faz. A **série de área construída é a do WSF Evolution** (ADR 0008).
Toda métrica de forma urbana de §5.2 — fragmentação, rosa de expansão, tipologia
infill/borda/leapfrog — carrega a comissão medida como **incerteza declarada**, não como
ruído ignorado.

### 1-15 · Portão da Fase 1 — **APROVADO**
Sete pontos de julgamento verificados com evidência, além das verificações mecânicas que o
orquestrador fez antes (exclusividade mútua das camadas: **0 pixels em duas ou mais** nos
seis anos; AOI e seeds vindos de `config/`; "fotointerpretação" só como negação).

O validador confirmou, com caminho de arquivo, que a incerteza é propagada em vez de
maquiada: a acurácia do usuário de 0,27–0,63 aparece com IC95 por ano, e nenhum número
derivado — área, CAGR — é apresentado sem a ressalva anexa. A série própria não reaparece
como série de tendência em artefato nenhum. Os selos estão presentes, inclusive o
`modelado` obrigatório na projeção de 2025 do COD-PS.

Achado que merece registro pela qualidade: o validador viu que a proveniência **propaga a
consequência aritmética** de "25 de Setembro" não ter geometria — "urbano inclui crescimento
por reassentamento que §10 manda separar, e a magnitude desse vazamento não é estimável sem
a geometria". Não é só declarar a ausência; é declarar o que ela contamina.

**Achado residual, corrigido pelo orquestrador:** a tabela do plano de execução em §9 do
prompt-mestre ainda definia o portão da Fase 1 como "acurácia ≥ 85 %", critério que o ADR
0009 invalidou. Eu havia atualizado §10 nos dois arquivos, mas não §9. Corrigido. O
validador acertou em não reprovar por isso — nenhum artefato de dados usava o critério
antigo para aprovar nada — e acertou mais ainda em não deixar passar.

**FASE 1 ENCERRADA.**

---

## 2026-09-08 — Fase 2 (Métricas e reconstrução)

### 2-01 · ERRO DE DELEGAÇÃO DO ORQUESTRADOR — dois agentes, um só artefato de saída
Abri a Fase 2 em duas frentes paralelas, §5.2 (forma urbana) e §5.3 (demografia), e **dei a
ambas o mesmo artefato de saída**: `data/processed/stats_by_year_by_unit.csv`, que §9 nomeia
para a fase. `pipeline/02_metrics/area_cagr.py` e `reconstrucao_demografica.py` escrevem os
dois nele.

Resultado: o arquivo tem hoje **14 linhas, todas de `familia: demografia`**. As linhas de
forma urbana foram sobrescritas.

É exatamente o mesmo problema que eu já havia resolvido na Fase 0' com
`scripts/consolidar_registros.py` — famílias coletadas em paralelo gravando em fragmentos e
um consolidador montando o documento canônico — e que não apliquei aqui. O esquema que os
agentes escolheram é bom (formato longo com coluna `familia` discriminadora); o que falta é
que ninguém pode reescrever o arquivo inteiro.

**Correção a aplicar:** cada módulo grava `data/interim/stats_<familia>.csv` e um
consolidador monta `data/processed/stats_by_year_by_unit.csv`, com contrato que reprova se
alguma família esperada estiver ausente. Aplicar **depois** que a frente demográfica
terminar, para não competir com ela pelo mesmo arquivo — o mesmo cuidado que falhou na
delegação.

### 2-02 · Unidades geográficas incompatíveis entre as famílias — pego pelo orquestrador
Com o consolidador funcionando, as duas famílias revelaram um problema que nenhum contrato
existente pegaria: **nenhuma unidade em comum**.

| família | unidades |
|---|---|
| demografia | `Cidade de Tete`, `Distrito de Moatize` |
| forma_urbana | `tete`, `moatize`, `cateme`, `mwaladzi`, `industrial`, `aoi` |

Interseção: **vazia**. E o problema é pior que rótulo divergente:

- **Tete:** `tete` e `Cidade de Tete` são a **mesma** geografia (§3 diz que o núcleo urbano
  de Tete é o distrito "Cidade de Tete"), com rótulos diferentes.
- **Moatize:** `moatize` é a **vila-sede** (§3), e `Distrito de Moatize` é o **distrito
  inteiro**, que contém a vila mais os postos de Kambulatsitsi e Zóbue. **Geografias
  diferentes sob nomes que se confundem.**

Qualquer razão população/área que juntasse as duas calcularia a população do distrito sobre
a área construída da vila — inflada, e **em silêncio**. A Fase 3 junta exatamente isso.

**Correções aplicadas pelo orquestrador:**
1. `config/unidades.yaml` — vocabulário controlado com oito unidades, cada uma declarando
   geografia, tipo, fonte da geometria e **se é comparável entre famílias**. Só `tete` é.
   `moatize_vila` e `moatize_distrito` declaram, em campo próprio, por que não são.
2. `pipeline/tests/test_unidades.py` — três contratos: toda unidade declara geografia e
   comparabilidade; o CSV de núcleo só usa unidades do vocabulário; e **nenhum par de
   unidades tem rótulos que se confundam com geografias diferentes**.
3. Renomeada a unidade ambígua `moatize` → `moatize_vila` **na origem**, nos cinco módulos
   de `pipeline/02_metrics/`, não no arquivo final.

O contrato foi visto reprovando antes da correção — acusou `moatize` como fora do
vocabulário. 54 contratos passando, `ruff` limpo, consolidado com 670 linhas e as duas
famílias.

### 2-03 · Custo da Fase 1 fechado — T3 em 283%
T2 em 100% do teto (901K de 900K), **T3 em 283%** (567K de 200K), fase em **122%**.

T3 teve **três** invocações contra a de uma prevista: recalibrar a amostragem após a
reprovação, medir o viés de sensor, e fechar a validação. As duas últimas não estavam no
plano — e foram as que mais mudaram o estudo. Nenhuma foi retrabalho.

Padrão que se repete e que a regra 4 deve absorver: **a reformulação de desenho aparece
depois da primeira entrega, não antes**, e custa 150–230K por rodada. Os tetos de T3 das
fases seguintes estão subdimensionados sob essa lógica — em especial o da Fase 3, que é
inteiramente desenho causal e tem 600K.

### 2-04 · ACHADO CRÍTICO — esquemas de P-code incompatíveis entre COD-AB e COD-PS
Ao buscar a geometria dos limites administrativos para os mapas de localização do artigo,
o orquestrador descobriu que as duas fontes do HDX usam **esquemas de P-code diferentes**:

| | província de Tete | Cidade de Tete | Moatize |
|---|---|---|---|
| **COD-AB** (geometria) | `MZ05` | `MZ0501` | `MZ0510` |
| **COD-PS** (população) | `MZ10` | `MZ1006` | `MZ1012` |

No COD-AB, **`MZ10` é Maputo** e **`MZ1006` é Matutuine**, distrito da província de Maputo,
a cerca de 1.500 km de Tete.

**Por que isto é o pior achado até agora:** um merge por P-code entre população e geometria
**tem sucesso**. A chave existe nos dois lados. Nenhum erro, nenhuma chave faltante, nenhum
aviso — e os 307.338 habitantes da Cidade de Tete vão parar em Matutuine. Todo mapa
coroplético, toda densidade e toda dasimetria derivada estariam errados, com aparência de
corretos.

**O `config/unidades.yaml` que eu mesmo escrevi horas antes carregava o código errado**
("HDX COD-AB, ADM2 MZ1006"), copiado do COD-PS sem conferir contra a geometria. Corrigido.

**Correções aplicadas:**
1. `config/unidades.yaml` declara agora `pcode_cod_ab` **e** `pcode_cod_ps` por unidade, com
   a advertência no próprio arquivo, mais uma seção `esquemas_pcode` documentando a colisão.
   **Regra: o cruzamento é por nome normalizado mais província, nunca por código.**
2. `pipeline/tests/test_unidades.py::test_pcodes_das_duas_fontes_nao_sao_intercambiaveis` —
   contrato que lê as duas fontes e afirma que o código do COD-PS **não** resolve para
   'Cidade de Tete' no COD-AB. Se um dia os esquemas convergirem, o contrato falha e obriga
   a revisar a regra antes de liberar merge por código.
3. Geometria espelhada: `data/raw/hdx_cod-ab-moz_admin_boundaries.geojson.zip` (58 MB,
   admin0 a admin4), CC BY-IGO 3.0, nível A, com `.sha256` e `.meta.json`. O XLSX que já
   estava espelhado traz **só a tabela de atributos**, sem geometria — por isso não servia
   para os mapas.

55 contratos passando, `ruff` limpo.

### 2-05 · Portão da Fase 2 — **REPROVADO** e corrigido
Dois motivos, ambos legítimos, e o primeiro é do orquestrador.

**1. `make all` não reproduzia a Fase 2.** O alvo `metrics` continuou sendo um stub com
`exit 1` depois de a fase inteira ser entregue, e **nenhum dos sete scripts** de
`pipeline/02_metrics/` estava no Makefile. Os 670 registros de
`stats_by_year_by_unit.csv` existiam só porque os scripts foram rodados à mão, fora do
grafo declarado. §10 exige o contrário, explicitamente.

Corrigido: o alvo executa os sete na ordem obrigatória — as quatro métricas, a conversão
para o esquema canônico, o fragmento demográfico, e por fim o consolidador que reprova se
faltar família. **Verificado rodando a cadeia inteira**: os sete saem `ok` e o consolidado
reproduz as mesmas 670 linhas.

**2. O ADR 0010 afirmava algo falso.** Dizia "não baixar Open Buildings ainda" e que
`00_fetch/` não ganharia esse script — mas a frente de §5.2, em paralelo, **baixou**
268.942 edificações no mesmo dia, e `edificacoes.py` as consome. As duas frentes decidiram
sobre o mesmo dado sem se ver: **erro de delegação do orquestrador**, o mesmo de 2-01.

Emendado, com a distinção que importa: a decisão de fundo **não é reaberta**, porque o
motivo nunca foi o custo do numerador — foi a **ausência de denominador** (tamanho médio do
domicílio não tem fonte A nem B). Sai o argumento acessório sobre custo de download, que
além de irrelevante estava errado: o recorte pela AOI tem 66 MB, não múltiplos GB. O ADR
passa de `proposto` a `aceito, com emenda`.

**O contrato que faltava**, e o que ele encontrou. `pipeline/tests/test_makefile.py`, três
regras: alvo não pode ser stub se a etapa já tem scripts; todo script de etapa implementada
tem de ser chamado por algum alvo; e `all` tem de depender de todas as etapas.

Rodado pela primeira vez, ele achou **mais três casos do mesmo defeito**, nenhum deles
suspeitado: `causal` era stub com `pipeline/03_causal/teste_vies_sensor.py` já existente,
`figures` era stub com `mapa_localizacao.py` já existente, e
`pipeline/01_imagery/slc_off_2010.py` não era chamado por nenhum alvo. Todos ligados.

Um ajuste na regra do próprio contrato: módulo auxiliar passou a ser identificado pelo
prefixo `_`, e não por lista à mão — a lista já tinha ficado desatualizada com
`_paleta_ardosia.py`.

58 contratos passando.

### 2-06 · DEFEITO DE FASE 1 QUE PASSOU PELO PORTÃO — as camadas medem o que não prometem
Ao conferir a figura de localização, o orquestrador notou que a camada `reassentamento`
era invisível no mapa. Não era problema de cor: ela tem **77 pixels, 0,07 km²** em 2025.

Cateme recebeu 716 famílias e Mwaladzi 84 (HRW 2013). A ordem de grandeza de um lote em
povoado de reassentamento é 500–1.000 m²; 800 famílias dariam ~0,6 km² só de lotes, sem vias
nem equipamentos. A camada detecta **cerca de um décimo** do piso plausível.

Investigando, o problema é de construção, não de calibração. `classificacao.py:613` e `:622`:

```
industrial     = construido & rasterizar(poligono_mineracao)
reassentamento = restante   & buffer_ativo
```

**As duas camadas são a interseção da classificação de construído com uma máscara
espacial.** Elas medem "construído dentro do polígono", não a pegada.

Medição do orquestrador para 2025:

| | km² |
|---|---|
| polígonos de mineração de Maus et al. na AOI | **59,2** |
| classificados como `industrial` | **4,2** |
| urbano dentro de polígono de mina | **0,00** |
| pegada minerária em **nenhuma** camada | **55,0** |

O que se sustenta: a exclusividade mútua funciona, e **nenhuma cava é contada como urbano** —
a proibição central de §10 está de pé.

O que não se sustenta: cava, pilha de estéril e rejeito são rocha e solo exposto.
**Espectralmente não são construído**, então um classificador de construído os perde por
definição. 93% da pegada minerária conhecida fica fora de qualquer camada.

**Consequências para §1:**
- **Pergunta 5** (evolução da área industrial) — medida errada: mede construído na mina.
- **H3** ("a pegada industrial cresce mais rápido que a urbana entre 2010 e 2015") — não
  testável com esta construção. Os números atuais (industrial 0,7 → 1,1 km²; urbano
  28,8 → 37,6) dizem o oposto, mas isso é artefato do desenho, não evidência.
- **Pergunta 3** ("reassentamentos: onde estão, quanto ocupam") — "onde estão" continua de pé,
  pelos nós OSM; **"quanto ocupam" está uma ordem de grandeza abaixo do plausível**.

A intenção era legítima: os polígonos de Maus são de Sentinel-2 2017–2019, um retrato único,
e interseccioná-los com a classificação anual era a forma de obter série temporal. O erro
está na execução, não no objetivo.

**Como o defeito passou pelo portão:** eu verifiquei a **exclusividade mútua** — que passa — e
não verifiquei se **cada camada mede o que o nome dela promete**. O contrato existente também
só testa exclusividade. Nenhum dos dois pergunta se a área é plausível para o objeto nomeado.

### 2-07 · Fase 1 reaberta e corrigida — a pegada é classificável
`docs/ADR/0011-pegada-como-classe-propria.md`. A pegada minerária deixou de ser
"construído dentro do polígono" e virou **classe própria**: solo e rocha exposta
**persistente**, isto é, sem reverdecimento na estação chuvosa.

Verificação independente do orquestrador:

| ano | industrial | cobertura de Maus | reassentamento | urbano dentro da mina |
|---|---|---|---|---|
| 2000 | 0,00 | 0% | 0,00 | 0,079 |
| 2005 | 0,00 | 0% | 0,00 | 0,113 |
| 2010 | 7,45 | 7,0% | 1,20 | 0,0000 |
| 2015 | 30,15 | 41,2% | 1,93 | 0,0000 |
| 2020 | 46,43 | 62,7% | 2,00 | 0,0000 |
| 2025 | **62,50** | **76,3%** | 2,32 | 0,0000 |

Cobertura dos polígonos de Maus em 2025: de **7,1% para 76,3%**. Exclusividade mútua
intacta: 0 pixels em duas camadas, todos os anos. 70 contratos, `ruff` limpo.

**A decisão técnica que fez a diferença: limiar relativo, não absoluto.** A mediana de
NDVI da estação chuvosa na paisagem vai de 0,669 (2015) a 0,330 (2025) — um corte absoluto
marcaria 472 km² fora dos polígonos em 2025. O limiar passou a ser relativo à mediana da
paisagem **do próprio ano**, e os polígonos de Maus entram como **envelope de busca**
(dilatado 500 m), não como máscara que exige construído.

**Circularidade declarada pelo próprio agente:** o limiar foi calibrado por J de Youden
contra Maus em 2020, então **a concordância de 2020 não é validação independente**. A
evidência não circular é o **placebo temporal**: a mesma regra devolve 0,000 km² em 2000 e
2005 — antes da licença da Vale —, e isso se mantém nas **30 configurações** da varredura
de parâmetros (área de 2025 entre 47,9 e 85,3 km²; todas passam o contrato). É a resposta
correta à objeção de que os parâmetros teriam sido ajustados até passar.

**H3 passa a ser testável, e a resposta é forte** (cálculo do orquestrador):

| | 2010 | 2015 | %/ano |
|---|---|---|---|
| industrial | 7,45 | 30,15 | **32,3%** |
| urbano | 28,26 | 36,76 | 5,4% |
| reassentamento | 1,20 | 1,93 | 9,9% |

De 2015 a 2025 a razão persiste (7,6% contra 1,5%). Com a construção anterior, os números
diziam o **oposto** — e teriam sido interpretados como refutação de H3.

**Dois achados finos do agente, ambos corretos:**
1. **`industrial` e `reassentamento` deixaram de ser subconjuntos de `construido`.** Somar
   as três colunas perdeu significado. Ele persistiu `construido_<ano>.tif` como artefato
   próprio e **repontou a validação para ele** — estratificar pela união jogaria cava
   dentro do estrato "construído".
2. O contrato de §10 acusou 0,079 km² (2000) e 0,113 km² (2005) de `urbano` dentro do
   polígono **futuro** da mina. **Não é violação**: é o povoado que existia antes da mina.
   Ele escopou o contrato a partir de 2006 e documentou, em vez de zerar o dado.

**O que não mudou, verificado e não presumido:** o raio de exclusão de negativos do treino
foi mantido separado do novo raio de detecção, deixando o RF bit-idêntico. **0 de 288
pontos de validação se moveram** e `acuracia_por_ano.csv` é idêntico por `diff` — a
acurácia do usuário segue 0,27–0,63 e o ADR 0009 está intacto. `urbano` cai só de 44,02
para 42,84 km² em 2025, com planta e pátio migrando para `industrial`.

**Premissas frágeis declaradas:** a regra de permanência aplicada à pegada torna a
reabilitação minerária indetectável (em 2020 a diferença é 36,7 sem permanência contra
46,4 publicada); expansão de lavra além de 500 m do polígono de 2019 não é capturada, o
que subestima 2025; a camada não distingue cava de infraestrutura; e o limiar único foi
reutilizado para reassentamento sem calibração própria, por não haver referência externa
ali.

### 2-08 · Produto mais antigo que o insumo — e nenhum contrato via
A reabertura da Fase 1 regerou as camadas classificadas às 09:48.
`data/processed/stats_by_year_by_unit.csv` era das **09:09** e continuou declarando
**1,06 km²** de área industrial em 2015, quando a camada nova tem **30,15 km²**.

Os contratos de esquema, faixa plausível, exclusividade mútua, selo e nível de fonte
**todos passavam**. Nenhum comparava data. O grafo do Makefile declara a dependência
(`metrics: imagery`), mas `make` só compara timestamp quando os pré-requisitos são
arquivos — aqui os alvos são fase a fase, então a dependência é de ordem, não de frescor.

Métricas reprocessadas sobre as camadas corrigidas; conferido que o CSV agora reproduz o
raster (2015: 30,15; 2025: 62,50).

**Contrato novo:** `pipeline/tests/test_frescor.py` declara, por produto, os padrões de
insumo dos quais ele deriva, e reprova quando o produto é mais antigo. Testado contra o
defeito — envelheci o CSV em uma hora e o contrato reprovou.

Segunda regra no mesmo arquivo: toda derivação declarada tem de apontar para caminho que
existe, senão um produto renomeado silencia a proteção sem ninguém notar.

72 contratos, `ruff` limpo.

**Padrão que se repete e vale nomear:** esta é a terceira vez que um defeito passa por
todos os contratos porque nenhum deles fazia a pergunta certa. Exclusividade mútua passava
enquanto a camada media o objeto errado (2-06); o alvo do Makefile era stub enquanto os
scripts existiam (2-05); e agora o produto estava velho enquanto o esquema estava perfeito.
Em todos, o que faltava não era rigor — era **uma pergunta que ninguém tinha feito**.

### 2-09 · Portão da Fase 2 — **APROVADO** na segunda passagem
Dez itens verificados com evidência. Os dois motivos da reprovação fecham: o `Makefile`
encadeia os sete scripts e `test_makefile.py` impõe isso daqui em diante; o ADR 0010 está
factualmente consistente. O reprocessamento propagou: o validador conferiu que a linha de
`industrial` 2015 tem 33.503 pixels × 900 m² = 30,15 km², batendo com o ADR 0011, e que as
datas respeitam o contrato de frescor.

Dois achados dele que valem registro.

**Item 7 — docstring desatualizada.** `amostras_validacao.py:20` ainda descrevia o estrato
como "união de urbano ∪ industrial ∪ reassentamento", contradizendo o próprio código do
mesmo arquivo e o ADR 0011. Cosmético, mas é exatamente o tipo de texto que alguém lê e
acredita. Corrigido.

**Item 5 — e este é maior que o portão: a alegação "0 de 288 pontos se moveram" NÃO é
verificável de forma independente.** Não há commit no repositório (`git log` → "does not
have any commits yet"). O validador foi preciso: a evidência indireta é *consistente* com a
alegação — `pontos_validacao.csv` é anterior à regravação dos rasters, logo não foi regerado
— mas **isso é ausência de contradição, não confirmação**.

O repositório acumulou 11 ADRs, 72 contratos e três reaberturas de fase **sem um único
commit**. Toda afirmação da forma "isto não mudou" é, hoje, indemonstrável. É uma lacuna de
infraestrutura de verificação, não de método, e ela cresce a cada fase.

### 2-10 · Custo da Fase 2 — 120% do teto
| Camada | Consumido | Teto | Uso |
|---|---|---|---|
| T2 sonnet | 799.650 | 600.000 | 133% |
| T3 opus | 151.249 | 150.000 | 101% |
| **Fase 2** | **950.899** | 790.000 | **120%** |

O T2 estourou por causa de duas coisas que não estavam no plano da fase: a reabertura da
Fase 1 (que consumiu T3) e as duas passagens do portão, mais a figura de localização pedida
pelo usuário. A reabertura não é retrabalho da Fase 2 — é correção de defeito herdado.
