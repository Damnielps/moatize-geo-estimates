<!-- SECAO_ECONOMIA_PRECOS_INICIO -->
## Preços de Carvão — World Bank CMO Annual (Fase 4b, T A2a)

Script(s): `pipeline/00_fetch/fetch_wb_cmo_anual.py`.

| Arquivo | URL | Data de acesso | Licença | Citação | Nível geográfico | Anos cobertos |
|---|---|---|---|---|---|---|
| CMO-Historical-Data-Annual.xlsx | https://thedocs.worldbank.org/en/doc/74e8be41ceb20fa0da750cda2f6b9e4e-0050012026/related/CMO-Historical-Data-Annual.xlsx | 2026-09-11 | Domínio público / CC BY 4.0 (World Bank) | World Bank. Commodity Markets Observatory — CMO Historical Data Annual. 2026. | Global (commodity markets) | 2000–2025 |

**Derivado (data/processed/economia/preco_carvao_anual.csv):**

| Arquivo | Origem | Formato | Nível | Anos | Métodos | Notas |
|---|---|---|---|---|---|---|
| preco_carvao_anual.csv | CMO-Historical-Data-Annual.xlsx (sheet: "Annual Prices (Nominal)") | CSV, UTF-8; colunas: unidade_geografica, ano, variavel (preco_carvao_australia, preco_carvao_africa_do_sul), valor, unidade_medida, selo, nivel_fonte, fonte, metodo, nota | A | 2000–2025 (26 anos × 2 variáveis = 52 registros) | Extração direta de "Annual Prices (Nominal)"; colunas 0, 5, 6 (Year, Coal Australian, Coal South African); sem transformação, valores nominais (USD/mt) | Verificação: 3 amostras (2008 AUS 127.1, 2015 SA 56.7, 2022 AUS 344.9) conferem contra XLSX original. Idempotência: script rodado 2 vezes, CSV byte-idêntico (SHA256: 5b8fe9b60c5e35df44dcb8dcc4ff459d945edc801e2347f0fec4fb09a3001c3e). |

**Rastreamento de integridade:**

- Arquivo baixado: 3.175.855 bytes
- SHA256: `ed4564bca630c9b3198fc093571d58d594b82a7f79c293901e142d1d176c75d6`
- Script verifica hash antes de reutilizar; falha explicitamente se fonte mudou.
- Reprodutibilidade: `uv run python pipeline/00_fetch/fetch_wb_cmo_anual.py` é determinístico (idempotente).

<!-- SECAO_ECONOMIA_PRECOS_FIM -->
