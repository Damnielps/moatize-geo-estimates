# Makefile — grafo de dependências explícito (§11.1, §11.2).
# Reprodução em cinco comandos: clone · make env · make fetch · make all · make app
# Ambiente: uv + uv.lock (docs/ADR/0002). Nenhum utilitário GDAL de linha de comando.

SHELL := /bin/bash
.SHELLFLAGS := -eu -o pipefail -c
PY := uv run python

CONFIG := config/study.yaml config/seeds.yaml config/tolerances.yaml
ANOS := 2000 2005 2010 2015 2020 2025

.PHONY: all env fetch imagery metrics agri causal figures provenance app-data app test lint audit clean help
.DEFAULT_GOAL := help

help:  ## lista os alvos
	@grep -hE '^[a-z-]+:.*?## ' $(MAKEFILE_LIST) | sort | awk -F':.*?## ' '{printf "  %-12s %s\n", $$1, $$2}'

env:  ## cria o ambiente exatamente como travado em uv.lock
	uv sync --locked

fetch:  ## baixa fontes de nível A, verifica sha256, preenche PROVENANCE.md  (Fase 0')
	@echo "[fetch] executando pipeline/00_fetch/ de forma idempotente"
	@for s in pipeline/00_fetch/*.sh;  do [ -e "$$s" ] && bash "$$s"    || true; done
	@for s in pipeline/00_fetch/*.py;  do [ -e "$$s" ] && $(PY) "$$s"   || true; done
	@# o laço acima engole falhas (|| true); o extrator do folheto INE tem de falhar
	@# explicitamente se o sha256 ou o quadro divergirem (§11.2.2), por isso roda de novo aqui.
	$(PY) pipeline/00_fetch/extrair_ine_folheto_tete.py

audit:  ## reemite data/DATA_AUDIT.md a partir de data/LICENSES.md  (Fase 0')
	@echo "[audit] alvo ainda não implementado — Fase 0'"
	@exit 1

imagery:  ## compostos, índices, classificação e validação por ano  (Fase 1, §5.1)
	$(PY) pipeline/01_imagery/compostos.py $(ANOS)
	$(PY) pipeline/01_imagery/indices.py $(ANOS)
	$(PY) pipeline/01_imagery/compostos_chuva.py $(ANOS)
	$(PY) pipeline/01_imagery/classificacao.py $(ANOS)
	$(PY) pipeline/01_imagery/pegada_sensibilidade.py
	$(PY) pipeline/01_imagery/amostras_validacao.py $(ANOS)
	$(PY) pipeline/01_imagery/acuracia.py
	$(PY) pipeline/01_imagery/concordancia_wsf.py $(ANOS)
	$(PY) pipeline/01_imagery/slc_off_2010.py

# `amostras_validacao.py` regera os recortes e o sorteio (determinístico, seed em
# config/seeds.yaml). NÃO regera data/processed/validacao/rotulos_interpretados.csv:
# o rótulo de referência é um julgamento registrado, versionado no repositório, e
# não é produto de código. `acuracia.py` falha alto se ele faltar — que é o
# comportamento correto: sem rótulo não há validação.

metrics: imagery  ## forma urbana e reconstrução demográfica  (Fase 2, §5.2-5.3)
	$(PY) pipeline/02_metrics/area_cagr.py
	$(PY) pipeline/02_metrics/fragmentacao.py
	$(PY) pipeline/02_metrics/tipologia_expansao.py
	$(PY) pipeline/02_metrics/edificacoes.py
	$(PY) pipeline/02_metrics/write_stats_forma_urbana.py
	$(PY) pipeline/02_metrics/reconstrucao_demografica.py
	$(PY) pipeline/02_metrics/populacao_vila_moatize.py
	$(PY) pipeline/02_metrics/demografia_dashboard.py
	$(PY) pipeline/02_metrics/stats_by_year_by_unit.py
	$(PY) pipeline/02_metrics/adensamento.py

# `adensamento.py` (docs/ADR/0016) lê urbano/reassentamento/industrial já publicados
# por `imagery` e a série de luz/edificações de data/raw/; não alimenta nem depende de
# stats_by_year_by_unit.csv — roda por último no alvo por ser independente das demais,
# não por ordem de dependência real.

# Ordem obrigatória: os quatro primeiros produzem métricas; `write_stats_forma_urbana`
# converte a saída deles para o esquema canônico e grava o fragmento da família;
# `reconstrucao_demografica` grava o fragmento da sua; `populacao_vila_moatize` roda
# depois (precisa de urbano/reassentamento 2020 já publicados) e ANTES de
# `demografia_dashboard`, que importa `populacao_vila_moatize.estimar()` para acrescentar
# a Vila de Moatize à série (§5.3; não entra no núcleo A de `stats_by_year_by_unit.csv`,
# só no dashboard); e só então `stats_by_year_by_unit` monta
# data/processed/stats_by_year_by_unit.csv e REPROVA se faltar família, se um selo for
# inválido ou se entrar linha de nível B/C no núcleo.
# Cada família grava fragmento em data/interim/ porque as duas gravavam o arquivo final
# em modo "w" e a última apagava a outra (ORCHESTRATION_LOG.md 2-01).

agri: imagery  ## agricultura urbana e periurbana  (Fase 2b, §5.6)
	$(PY) pipeline/01_imagery/cultivo.py $(ANOS)
	$(PY) pipeline/01_imagery/varzea.py
	$(PY) pipeline/01_imagery/cultivo_varzea.py $(ANOS)
	$(PY) pipeline/01_imagery/amostras_validacao_cultivo.py
	$(PY) pipeline/01_imagery/acuracia_cultivo.py
	$(PY) pipeline/01_imagery/validacao_externa_cultivo.py

# `amostras_validacao_cultivo.py` regera os recortes e o sorteio (determinístico, seed em
# config/seeds.yaml). NÃO regera data/processed/validacao/rotulos_interpretados_cultivo.csv:
# o rótulo de referência é um julgamento registrado, versionado no repositório, e não é
# produto de código — mesma regra do alvo `imagery`. `acuracia_cultivo.py` falha alto se
# ele faltar. Ver docs/ADR/0012 para o resultado dessa validação (cultivo_sequeiro não
# defensável como cropland com a fenologia bianual disponível).

causal: metrics agri  ## séries interrompidas, DiD, controle sintético, cenários  (Fase 3, §5.4-5.5)
	$(PY) pipeline/03_causal/teste_vies_sensor.py
	$(PY) pipeline/03_causal/estabilidade_temporal.py
	$(PY) pipeline/03_causal/series_base.py
	$(PY) pipeline/03_causal/series_interrompidas.py
	$(PY) pipeline/03_causal/decomposicao_luz.py
	$(PY) pipeline/03_causal/placebos.py
	$(PY) pipeline/03_causal/did_sintetico.py
	$(PY) pipeline/03_causal/elasticidades.py
	$(PY) pipeline/03_causal/logit_conversao.py
	$(PY) pipeline/03_causal/cenarios.py
	$(PY) pipeline/03_causal/veredito_fase3.py

# A ordem importa: `series_base.py` constrói as duas séries-base (S_HARM_soma de luz e
# S_WSF_taxa de área) que todos os demais leem; `veredito_fase3.py` consolida placebos e
# critérios F1–F7 e é o último. `decomposicao_luz.py` executa a decomposição de §2.3
# (industrial / urbano / resto), registrada como etapa NÃO EXECUTADA em docs/ADR/0015
# decisão 4, e roda antes de `placebos.py` porque é ela que qualifica qualquer leitura da
# quebra de 2022. `logit_conversao.py` NÃO estima nada: registra, de forma
# reproduzível, a recusa pré-registrada do §5.6.4. Os dois primeiros scripts são
# diagnósticos que condicionam o que a fase pode estimar, e precisam ser reproduzíveis como qualquer outro artefato:
# `teste_vies_sensor.py` sustenta docs/ADR/0008 (viés de detecção que cresce com o
# tempo) e `estabilidade_temporal.py` sustenta docs/ADR/0013 (quanto da série de
# `urbano` é detecção do ano e quanto é catraca da regra R2 de permanência).

figures: causal  ## figuras e folha de fatos do artigo, paleta Ardósia  (§6.3)
	$(PY) pipeline/04_figures/mapa_localizacao.py
	$(PY) pipeline/04_figures/fatos_verificados.py
	$(PY) pipeline/04_figures/gif_mancha.py

provenance: metrics agri causal  ## monta data/LICENSES.md e PROVENANCE.md dos fragmentos  (§4.0, §11.2.3)
	$(PY) scripts/consolidar_registros.py

# Cada família (imagery/metrics/agri/causal) grava seu próprio fragmento em
# data/licenses_parts/ ou data/provenance_parts/ ao rodar (ver docstring de cada
# script). Este alvo só MONTA os dois documentos canônicos a partir dos fragmentos já
# gravados — por isso depende das etapas que os escrevem, não de `imagery`/`figures`
# diretamente (nenhuma delas grava fragmento próprio hoje). Sem este alvo no grafo,
# `make all` nunca regenerava PROVENANCE.md/data/LICENSES.md, e a página de
# Metodologia do app (gerada deles, §6) ficava presa ao estado do último `git commit`
# em vez do da última execução — violação de §10.

all: imagery metrics agri causal figures provenance  ## pipeline completo até data/processed/

app-data: causal agri provenance  ## data/processed/app/ a partir de data/processed/  (Fase 4, pré-requisito de `app`)
	# Camadas de CONTEXTO do mapa (topônimos, rodovias, ferrovia, aeródromo). Idempotente:
	# só consulta a Overpass para o que ainda não está espelhado em data/raw/.
	$(PY) pipeline/00_fetch/fetch_osm_contexto.py
	$(PY) pipeline/05_app/gerar_marcos.py
	# Paleta das classes de uso do solo (ADR 0018): config/paleta_uso_solo.yaml ->
	# app/src/content/paleta_uso_solo.json, lida pelo mapa e pelas legendas do app.
	$(PY) pipeline/05_app/gerar_paleta.py
	$(PY) pipeline/05_app/build_web_assets.py
	$(PY) pipeline/05_app/gerar_metodologia.py
	$(PY) pipeline/05_app/gerar_artigo.py

# `gerar_metodologia.py` e `gerar_artigo.py` escrevem em app/src/content/ (dentro do
# front-end, não em data/processed/) porque a página de Metodologia e a aba Artigo são
# GERADAS de PROVENANCE.md/data/DATA_AUDIT.md/uv.lock e de paper/artigo.md,
# respectivamente (§6, §6-A) — nunca escritas à mão. Rodar as duas aqui, antes de
# `npm run build`, garante que o app nunca publique uma versão desatualizada desses
# dois documentos.

app: app-data  ## build estático do front-end em app/dist  (Fase 4, §6)
	cd app && npm ci && npm run build

test:  ## contratos de dados e regressão numérica (§11.2.4)
	uv run pytest -q

lint:
	uv run ruff check .

clean:  ## remove apenas intermediários regeneráveis
	rm -rf data/interim/*
