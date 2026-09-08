# Makefile — grafo de dependências explícito (§11.1, §11.2).
# Reprodução em cinco comandos: clone · make env · make fetch · make all · make app
# Ambiente: uv + uv.lock (docs/ADR/0002). Nenhum utilitário GDAL de linha de comando.

SHELL := /bin/bash
.SHELLFLAGS := -eu -o pipefail -c
PY := uv run python

CONFIG := config/study.yaml config/seeds.yaml config/tolerances.yaml
ANOS := 2000 2005 2010 2015 2020 2025

.PHONY: all env fetch imagery metrics agri causal figures app test lint audit clean help
.DEFAULT_GOAL := help

help:  ## lista os alvos
	@grep -hE '^[a-z-]+:.*?## ' $(MAKEFILE_LIST) | sort | awk -F':.*?## ' '{printf "  %-12s %s\n", $$1, $$2}'

env:  ## cria o ambiente exatamente como travado em uv.lock
	uv sync --locked

fetch:  ## baixa fontes de nível A, verifica sha256, preenche PROVENANCE.md  (Fase 0')
	@echo "[fetch] executando pipeline/00_fetch/ de forma idempotente"
	@for s in pipeline/00_fetch/*.sh;  do [ -e "$$s" ] && bash "$$s"    || true; done
	@for s in pipeline/00_fetch/*.py;  do [ -e "$$s" ] && $(PY) "$$s"   || true; done

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
	$(PY) pipeline/02_metrics/stats_by_year_by_unit.py

# Ordem obrigatória: os quatro primeiros produzem métricas; `write_stats_forma_urbana`
# converte a saída deles para o esquema canônico e grava o fragmento da família;
# `reconstrucao_demografica` grava o fragmento da sua; e só então
# `stats_by_year_by_unit` monta data/processed/stats_by_year_by_unit.csv e REPROVA se
# faltar família, se um selo for inválido ou se entrar linha de nível B/C no núcleo.
# Cada família grava fragmento em data/interim/ porque as duas gravavam o arquivo final
# em modo "w" e a última apagava a outra (ORCHESTRATION_LOG.md 2-01).

agri: imagery  ## agricultura urbana e periurbana  (Fase 2b, §5.6)
	@echo "[agri] alvo ainda não implementado — Fase 2b"
	@exit 1

causal: metrics agri  ## séries interrompidas, DiD, controle sintético, cenários  (Fase 3, §5.4-5.5)
	$(PY) pipeline/03_causal/teste_vies_sensor.py

# A Fase 3 ainda não começou; o único script aqui é o teste de viés de sensor que
# sustenta docs/ADR/0008 e precisa ser reproduzível como qualquer outro artefato.

figures: causal  ## figuras do artigo, paleta Ardósia  (§6.3)
	$(PY) pipeline/04_figures/mapa_localizacao.py

all: imagery metrics agri causal figures  ## pipeline completo até data/processed/

app:  ## build estático do front-end em app/dist  (Fase 4, §6)
	cd app && npm ci && npm run build

test:  ## contratos de dados e regressão numérica (§11.2.4)
	uv run pytest -q

lint:
	uv run ruff check .

clean:  ## remove apenas intermediários regeneráveis
	rm -rf data/interim/*
