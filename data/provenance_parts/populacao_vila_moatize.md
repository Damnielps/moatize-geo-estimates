<!-- SECAO_POPULACAO_VILA_MOATIZE_INICIO -->
## População da Vila de Moatize — estimativa dasimétrica de terceiros (§3, §5.3)

Script: `pipeline/02_metrics/populacao_vila_moatize.py`.
Gerado em 2026-09-09.
Correção de enquadramento em `docs/ADR/0017`: a banda deixou de ser composta só por
variantes atenuadas por máscara de construído — a única variante que valida em Cidade
de Tete (partição de Voronoi sem peso de construído) passou de "diagnóstico não
publicável" a TETO da banda.

### Por que este número não vem do HDX/INE

O HDX COD-PS só publica população por ADM2 (Distrito de Moatize). A Vila de Moatize é
ADM3 e não tem contagem oficial isolada em nenhuma fonte localizada (nível A ou B).

### O que a validação cruzada em Cidade de Tete mostrou (leia isto antes da tabela)

Nenhuma forma de aplicar a máscara de construído recupera o observado
(307338, HDX COD-PS 2017) — nem o multiplicador de fração
(classificação própria: -40.4%; GHSL: -74.5%), nem
a pertença binária (fração > 0: -25.2%; fração ≥ mediana das células
presentes: -50.4%). O GRID3 v1.1 já é um produto dasimétrico calibrado ao
Censo 2017: pesá-lo de novo por uma máscara de construído própria restringe a população
**duas vezes**, descartando gente que o produtor já havia colocado onde ela está. A única
variante que reproduz o observado é a partição espacial (Voronoi por sede mais próxima)
**sem nenhum peso de construído**: +1.6%. O que funciona é particionar,
não pesar.

### Banda — piso e teto (nenhum valor central)

| variante | tipo | estimativa (hab.) | desvio em Tete |
|---|---|---|---|
| classificação própria (fração) | restrita | 29009 | -40.4% |
| GHSL BUILT-S 2020 (fração) | restrita | 15192 | -74.5% |
| pertença binária (fração > 0) | restrita | 40444 | -25.2% |
| pertença por mediana (quantil, ADR 0014) | restrita | 24630 | -50.4% |
| **sem peso de construído (cluster inteiro)** | **TETO** | **69301** | **+1.6%** |
| **piso publicado** | menor das restritas | **15192** | — |

Leitura: **piso** (15192) restringe ao construído e, pela validação em
Tete, perde entre 25% e 74% das pessoas que o GRID3 lá coloca — limite
INFERIOR.
**teto** (69301) soma o GRID3 no cluster de Voronoi inteiro, sem peso de
construído — inclui a área rural do cluster atribuída à sede mais próxima, logo é
limite SUPERIOR para a vila, não a vila propriamente. Nenhuma das cinco variantes é
publicada como "a estimativa"; cada uma é nomeada em
`populacao_vila_moatize_sensibilidade.csv`.

Ano de referência: 2017 (calibração do GRID3). Um único ponto — não há série, não há
CAGR. Selo `modelado`, nível de fonte `A` (GRID3 é CC BY 4.0, produtor institucional
WorldPop/Southampton — ver `data/provenance_parts/worldpop_grid3.md`), mas **não é
contagem**: é estimativa dasimétrica de terceiros sobre uma grade já modelada.

### Validação cruzada em Cidade de Tete — tabela completa

O mesmo procedimento aplicado a Cidade de Tete, comparado contra os
307338 habitantes observados (HDX COD-PS 2017, nível A):

| variante | estimativa (hab.) | desvio frente ao observado |
|---|---|---|
| classificação própria (fração) | 183036 | -40.4% |
| GHSL BUILT-S 2020 (fração) | 78512 | -74.5% |
| pertença binária (fração > 0) | 229867 | -25.2% |
| pertença por mediana (quantil) | 152462 | -50.4% |
| sem peso de construído (teto) | 312300 | +1.6% |

Este desvio — não um limiar de aprovação — é a medida de quanto confiar na estimativa da
Vila de Moatize, que usa exatamente o mesmo método sem ter uma âncora observada própria
contra a qual se comparar. Publicado mesmo se grande: **toda variante restrita por
construído SUBESTIMA** a população observada de Cidade de Tete; só a partição sem peso
não subestima. **A estimativa da Vila herda esse mesmo viés** — toda variante restrita
publicada na banda é, à luz desta validação, mais provável de subestimar do que de
superestimar a população real da vila; o teto é a única variante que a validação não
desqualifica, ao custo de incluir população rural do cluster.

### Correção da nota de comissão (dois referentes, não um)

O peso 'classificação própria' carrega a comissão medida na classe construído
(acurácia do usuário de `construido` = 0,286–0,625 (docs/ADR/0009; reexecutado em docs/ADR/0014): entre 37,5 % e 71,4 % do que o mapa chama de construído não é.). Essa comissão tem DUAS relações
distintas, cada uma com seu referente: frente ao peso GHSL (o outro multiplicador de
fração), tende a puxar a estimativa para CIMA. Frente à população OBSERVADA em Cidade
de Tete, a mesma variante SUBESTIMA em 40.4% — a comissão de
área não é grande o suficiente para compensar a dupla restrição imposta pela máscara
sobre um GRID3 que já é dasimétrico.

### Saídas

`data/processed/populacao_vila_moatize_sensibilidade.csv` (as cinco variantes, piso/teto
para Vila e Tete, mais a linha `validacao_cruzada`). Linha em
`data/processed/demografia_serie_1997_2025.csv` (unidade "Vila de Moatize", ano 2017,
`selo=modelado`, `nivel_fonte=A`, valor publicado = TETO — a variante validada —, com
piso/desvios explícitos em `nota`, `comparabilidade` explicando a natureza do número).
`config/unidades.yaml`: `moatize_vila` continua `comparavel_entre_familias: false` —
existe estimativa modelada agora, mas continua não sendo contagem, e nenhuma razão
população/área com essa vila deixa de ser inválida por causa disso.

<!-- SECAO_POPULACAO_VILA_MOATIZE_FIM -->
