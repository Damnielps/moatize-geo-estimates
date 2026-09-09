<!-- SECAO_ADENSAMENTO_INICIO -->
## Adensamento 2020-2025 — concordância de três sinais (docs/ADR/0016, §5.2/§5.6)

Script: `pipeline/02_metrics/adensamento.py`.
Gerado em 2026-09-09.

Camada `modelado`, grade de 240 m (8×
8 pixels de 30 m), domínio = células completas
(`n_pixels_30m == 64`; 43416 células,
2500.76 km²). Três sinais (S1 fração construída própria, S2
inclinação Theil-Sen de luz noturna, S3 resíduo de pegada de edificações Open
Buildings) convertidos a posto (ECDF) e votados contra um corte de quantil
(`TAU = 0.7` declarado; realizado
`TAU_s1=0.007436`, `TAU_s2=0.001117`,
`TAU_s3=0.352931`) — voto exige também `dominio_ocupado`
(Emenda 2 do ADR 0016). `adensando ⇔ Σ votos ≥ 2`. Sete classes por precedência,
partição exaustiva.

### Área por classe (km², contagem real de pixels de 30 m — ver `docs/ADR/0016`,
### achado 2 do portão da Frente B: `fora_de_dominio` NÃO usa `n_células × área
### nominal`, que superestimava por ~2,67×)

| classe | área (km²) |
|---|---|
| `fora_de_dominio` | 5.7888 |
| `vazio_estavel` | 2365.8624 |
| `esparso_estavel` | 44.1792 |
| `adensando` | 15.3216 |
| `expansao_nova` | 10.3104 |
| `consolidado` | 19.6416 |
| `pegada_industrial` | 45.4464 |

### Sensibilidade

Razão máxima entre a variante mais extrema e a base, no primeiro decil de células
adensando: **2.2931** — regime de publicação:
**publicada só como padrão espacial e ordem de grandeza, NÃO como área (razão em (2.0, 5.0])** (`publicavel_como=padrao_espacial`).
Ver `data/processed/adensamento_sensibilidade.csv` (todas as variantes `tau_0*`/`qalto_0*`/
`qbaixo_0*`, pré-registradas antes de ver o resultado, §Decisão-9 do ADR).

### Riscos declarados (R1-R10, ver ADR para detalhe)

- **R1**: erro espacialmente estruturado sobrevive ao posto
- **R2**: S1 e S3 partilham f_2020 — votos não são independentes
- **R3**: camada não detecta esvaziamento (S1 censurado por baixo pela catraca R2 de urbano)
- **R4**: luz sobreamostrada de ~500 m para 240 m
- **R5**: S3 pode ser desacordo de sensor, não construção
- **R6**: janela real de S3 é 2020 -> ~2023, não 2020->2025
- **R7**: churn de pixel de 31% sobrevive parcialmente à agregação
- **R8**: dependência dos cortes — ver sensibilidade acima
- **R9**: moatize_vila possivelmente inflada (25 de Setembro sem geometria)
- **R10**: camada modelada, risco de ser lida como observada — selo em 4 lugares

### Saídas

Raster 240 m: `data/processed/imagery/adensamento_2020_2025_240m_32736.tif`. Raster 30 m (desagregado, mesma classe
em todos os pixels da célula): `data/processed/imagery/adensamento_2020_2025_30m_32736.tif`. Vetor:
`data/processed/imagery/adensamento_2020_2025.geojson` (443 polígonos, atributos
`f_2020`/`f_2025`/`s1`/`s2`/`s3`/`concordancia`/`fracao_industrial` — reconstroem
`classe` e `concordancia` sem reexecutar o pipeline, contratos T2/T13 de
`pipeline/tests/test_adensamento.py`). Por unidade:
`data/processed/adensamento_2020_2025_por_unidade.csv`.

Não alimenta `stats_by_year_by_unit.csv` (§ Makefile, alvo `metrics`): camada
independente, lida por unidade/ano avulsos. Selo `modelado` em quatro lugares
(raster 240 m, raster 30 m, GeoJSON, CSV por unidade) — risco R10.

<!-- SECAO_ADENSAMENTO_FIM -->
