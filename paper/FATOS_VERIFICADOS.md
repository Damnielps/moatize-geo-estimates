# Fatos verificados — números do artigo, extraídos dos CSV

> **Não edite este arquivo.** Ele é gerado por `pipeline/04_figures/fatos_verificados.py` a partir de `data/processed/`. Todo número do artigo deve sair daqui, com a estatística que ele é (faixa, mediana, máximo, ano único) — nunca de memória.

- Gerado em: 2026-09-09T17:05:25+00:00

---

## Acurácia do usuário e comissão de `construido`

Fonte: `data/processed/acuracia_por_ano.csv`, coluna `acuracia_usuario_construido`.
Decidido em `docs/ADR/0009`; **valores reexecutados em `docs/ADR/0014`**.

| ano | acurácia do usuário | comissão = 1 − acurácia |
|---|---|---|
| 2000 | 0.5238 | 47.6 % |
| 2005 | 0.6087 | 39.1 % |
| 2010 | 0.2857 | 71.4 % |
| 2015 | 0.5909 | 40.9 % |
| 2020 | 0.4762 | 52.4 % |
| 2025 | 0.6250 | 37.5 % |

- **Faixa da acurácia:** 0.286 a 0.625 (mínimo em 2010, máximo em 2025).
- **Faixa da comissão:** 37.5 % a 71.4 %.
- **Como escrever:** é uma FAIXA entre anos-âncora, não um intervalo de confiança e não um valor único. Nunca citar 0,27–0,63 nem 37 %–73 %: são anteriores à reexecução do `docs/ADR/0014`.

## Churn de `construido` entre anos-âncora

Fonte: `data/processed/causal/estabilidade_temporal_camadas.csv` (`docs/ADR/0013`).

- 2000-2005: 47.5 %
- 2005-2010: 47.3 %
- 2010-2015: 54.4 %
- 2015-2020: 41.5 %
- 2020-2025: 31.0 %

- **Faixa:** 31.0 % a 54.4 %.
- **Como escrever:** afeta tipologia (infill/borda/leapfrog) e matriz de transição, que dependem de QUAL pixel mudou. NÃO afeta área, CAGR nem fragmentação agregada.

## Razão teto/piso da decomposição de luz

Fonte: `data/processed/causal/decomposicao_luz_por_camada.csv`, coluna `razao_teto_sobre_piso`.

| classe | n | mediana | máximo |
|---|---|---|---|
| industrial | 35 | 2.12 | 4.61 |
| reassentamento | 30 | 5.21 | 6.69 |
| resto | 38 | 0.28 | 0.47 |
| urbano | 38 | 1.83 | 2.24 |

- **Máximo global:** 6.69.
- **Como escrever:** a decomposição **não é partição**. Publicar piso e teto, nunca um valor. Um qualificador de máximo ('até N') só pode trazer o máximo (6.69), jamais a mediana. Só o sinal comum às duas envoltórias é afirmável (`docs/ADR/0015`, decisão 4).

## Quebras estimadas (séries interrompidas), variante principal

Fonte: `data/processed/causal/its_quebras.csv`.

| série / unidade / quebra | b2 (nível) | IC95 | p |
|---|---|---|---|
| `S_WSF_taxa|tete_aoi|2005` | -0.402 | [-1.237, +0.433] | 0.345 |
| `S_WSF_taxa|tete_aoi|2011` | +0.613 | [-0.008, +1.234] | 0.053 |
| `S_HARM_soma|tete_aoi|2016` | -0.152 | [-0.215, -0.088] | 0.000 |
| `S_HARM_soma|tete_aoi|2022` | -0.181 | [-0.259, -0.104] | 0.000 |

### Veredito dos painéis contrafactuais

- criterio_F | A_area_WSF|2005 | A_area_WSF | 2005 | CONTRAFACTUAL NAO SUSTENTADO |  |  | F3_rmspe_pre_maior_que_meio_dp;F5_rank_nao_top2;F7_loo_desloca_mais_de_50pct
- criterio_F | A_area_WSF|2011 | A_area_WSF | 2011 | CONTRAFACTUAL NAO SUSTENTADO |  |  | F3_rmspe_pre_maior_que_meio_dp;F5_rank_nao_top2;F7_loo_desloca_mais_de_50pct
- criterio_F | B_luz_HARM|2016 | B_luz_HARM | 2016 | CONTRAFACTUAL NAO SUSTENTADO |  |  | F4_peso_concentrado_>0.80;F5_rank_nao_top2;F7_loo_desloca_mais_de_50pct
- criterio_F | B_luz_HARM|2022 | B_luz_HARM | 2022 | CONTRAFACTUAL NAO SUSTENTADO |  |  | F3_rmspe_pre_maior_que_meio_dp;F4_peso_concentrado_>0.80

**Placebo espacial P1, por quebra (de `placebos.csv`):**

- 2005: nao estimavel
- 2011: FALHA
- 2016: FALHA
- 2022: nao estimavel

- **Como escrever:** os quatro painéis são NÃO SUSTENTADOS, mas **não pelo mesmo motivo** — a coluna de critérios F acima diz qual caiu por quê. O placebo espacial FALHA em 2011, 2016 (controles sem carvão replicam a quebra) e é NÃO ESTIMÁVEL em 2005, 2022 (`docs/ADR/0015`, ramo de referência nula). Não generalizar o motivo de uma quebra para as outras.
- Um coeficiente com p = 0,000 descreve a série de Tete; ele **não** mede efeito do carvão.
- **Piso de inferência:** com 1 tratado e 5 doadores, o p mínimo por permutação é **1/6 ≈ 0,167**. Nenhum resultado pode atingir p < 0,05. Um p perto de 0,167 é o piso do teste, não um nulo comum.

## Luz noturna: cidade de Tete contra o resto do retângulo

Fonte: `data/processed/causal/serie_luzes_anual.csv`, colunas `soma_radiancia` e `soma_radiancia_adm2_int_recorte`.

| janela | retângulo | Cidade de Tete | resto (Moatize + mina) |
|---|---|---|---|
| 2021→2022 | -6.0 % | +0.7 % | -12.7 % |
| 2021→2025 | +21.2 % | +45.0 % | -2.5 % |
| 2011→2013 | +15.4 % | +21.8 % | +7.6 % |

- **Como escrever:** a queda de 2022 **não está na cidade**. Atribuí-la à mina é PROIBIDO (`docs/ADR/0015`, decisão 4): a pegada industrial responde por 32–42 % da queda (piso e teto da envoltória), e o maior contribuinte é `resto`, que não é industrial nem urbano classificado. O que se pode dizer é que a queda está **fora da cidade**.

## Adensamento 2020→2025 (`docs/ADR/0016`)

- Fonte: `data/processed/imagery/adensamento_2020_2025_240m_32736.tif.meta.json`, `data/processed/adensamento_sensibilidade.csv`, `data/processed/adensamento_2020_2025_por_unidade.csv`
- Selo: **modelado** · publicável como: **padrao_espacial** · estocasticidade: nenhuma — Theil-Sen exato e quantis são determinísticos

- Área da classe `adensando` na variante **base**: **15.32 km²** (domínio de 2500.76 km²).
- Entre as 6 variantes de ±1 decil, essa área vai de **6.682 km²** (tau_080) a **23.9 km²** (qbaixo_010).
- Razão **frente à variante base** (é este o critério de publicação do ADR 0016, e é este o número do meta): **2.2931**. Razão **entre os dois extremos**, que é outra coisa: **3.578**.
- Área por classe (km², variante base): `vazio_estavel` 2366; `pegada_industrial` 45.45; `esparso_estavel` 44.18; `consolidado` 19.64; `adensando` 15.32; `expansao_nova` 10.31
- `adensando` por unidade (km², soma dos anéis): tete 11.4; moatize_vila 2.822; cateme 0.6336; mwaladzi 0.4608

- **Como escrever:** a área **não é um resultado publicável**. O regime declarado no meta é: *publicada só como padrão espacial e ordem de grandeza, NÃO como área (razão em (2.0, 5.0])*. Escrever "15.32 km² adensaram" é converter um padrão espacial numa medida de área que a própria sensibilidade recusa — a mesma área muda por um fator de 2.2931 só por deslocar um corte em um decil. Escreva **onde** adensa (as unidades e anéis acima), não **quanto**.
- **Como escrever:** a camada é **modelada**, nunca observada. Ela é síntese de três sinais por concordância de 2 em 3, não uma classificação de imagem: não há pixel algum que tenha sido *visto* adensando.
- **Como escrever:** a camada **não detecta esvaziamento**. Não existe classe `desadensando`, por construção (a catraca R2 torna a série de construído não-decrescente). Ausência de `adensando` não é evidência de estagnação.
- **Como escrever:** a janela real do sinal S3 (Open Buildings) é **2020→~2023**, não 2020→2025. Toda frase que der o intervalo completo a S3 está errada.

- Riscos declarados no meta (todos têm de sobreviver à redação):
  - `R1` — erro espacialmente estruturado sobrevive ao posto
  - `R2` — S1 e S3 partilham f_2020 — votos não são independentes
  - `R3` — camada não detecta esvaziamento (S1 censurado por baixo pela catraca R2 de urbano)
  - `R4` — luz sobreamostrada de ~500 m para 240 m
  - `R5` — S3 pode ser desacordo de sensor, não construção
  - `R6` — janela real de S3 é 2020 -> ~2023, não 2020->2025
  - `R7` — churn de pixel de 31% sobrevive parcialmente à agregação
  - `R8` — dependência dos cortes — ver sensibilidade acima
  - `R9` — moatize_vila possivelmente inflada (25 de Setembro sem geometria)
  - `R10` — camada modelada, risco de ser lida como observada — selo em 4 lugares

---

## População comparada, 1997–2025

- Fonte: `data/processed/demografia_serie_1997_2025.csv` (38 linhas: 15 de população, 9 de CAGR, 14 de índice)

| unidade | ano | população | selo | nível |
|---|---:|---:|---|---|
| Cidade de Tete | 1997 | 101 984 | observado | **B** |
| Cidade de Tete | 2007 | 155 870 | observado | **C** |
| Cidade de Tete | 2017 | 307 338 | observado | **A** |
| Cidade de Tete | 2025 | 460 248 | modelado | **A** |
| Distrito de Moatize | 1997 | — | observado | **ausente** |
| Distrito de Moatize | 2007 | 215 092 | observado | **C** |
| Distrito de Moatize | 2017 | 260 843 | observado | **A** |
| Distrito de Moatize | 2025 | 349 103 | modelado | **A** |
| Moçambique | 2007 | 21 802 866 | observado | **C** |
| Moçambique | 2017 | 26 899 102 | observado | **A** |
| Moçambique | 2025 | 35 163 992 | modelado | **A** |
| Província de Tete | 2007 | 1 783 967 | observado | **C** |
| Província de Tete | 2017 | 2 551 824 | observado | **A** |
| Província de Tete | 2025 | 3 432 961 | modelado | **A** |
| Vila de Moatize | 2017 | 69 301 | modelado | **A** |

| unidade | intervalo | CAGR (%/ano) | selo | nível |
|---|---|---:|---|---|
| Cidade de Tete | 1997→2007 | 4.333 | observado | **C** |
| Cidade de Tete | 2007→2017 | 7.025 | observado | **C** |
| Cidade de Tete | 2017→2025 | 5.177 | modelado | **A** |
| Distrito de Moatize | 2007→2017 | 1.947 | observado | **C** |
| Distrito de Moatize | 2017→2025 | 3.710 | modelado | **A** |
| Moçambique | 2007→2017 | 2.123 | observado | **C** |
| Moçambique | 2017→2025 | 3.406 | modelado | **A** |
| Província de Tete | 2007→2017 | 3.645 | observado | **C** |
| Província de Tete | 2017→2025 | 3.777 | modelado | **A** |

**Ritmo relativo (razão entre CAGR da unidade e o de Moçambique, mesmo intervalo):**

- `cagr_2007_2017` (Moçambique = 2.123 %/ano): Cidade de Tete 3.31×; Província de Tete 1.72×; Distrito de Moatize 0.92×
- `cagr_2017_2025` (Moçambique = 3.406 %/ano): Cidade de Tete 1.52×; Província de Tete 1.11×; Distrito de Moatize 1.09×

- **Como escrever:** o nível é **por ponto**, não por série. Os pontos desta tabela vão de ['A', 'B', 'C', 'ausente']. Uma taxa que atravessa 1997 ou 2007 tem ponta **B ou C** e, por §4.0, **não sustenta número publicado** — entra como contexto, com o nível na mesma frase. Não existe 'a taxa 1997–2025'.
- **Como escrever:** 2025 **não é observação**. É projeção geométrica do INE: o CAGR 2017–2025 é **premissa do produtor**, não medida deste estudo. Usá-lo como evidência de aceleração ou desaceleração é circular.
- **Como escrever:** os valores de 2017 são contagens **residentes não ajustadas** pela sub-enumeração estimada pelo próprio INE — **3,8 %** na Província de Tete (a grandeza pertinente às unidades deste estudo, todas nela); 3,7 % é a taxa **nacional**, uma grandeza distinta, não uma faixa de incerteza da mesma medida.
- **Como escrever:** o **Distrito de Moatize mudou de limites** entre censos; a comparabilidade 2007/2017 não está garantida, e a taxa desse intervalo mistura crescimento com mudança de perímetro.
- **Como escrever:** o total nacional é **soma do COD-PS**, não o número publicado pelo INE; a divergência está no CSV. Use o valor do CSV.

- Banda da Vila de Moatize (2017, único ano): **15 192** (piso) a **69 301** (teto). Variantes, do menor ao maior, com o desvio de cada uma na validação cruzada em Cidade de Tete contra 307 338 observados: `ghsl_built_s` 15 192 (-74,45 %); `pertenca_mediana` 24 630 (-50,39 %); `classificacao_propria` 29 009 (-40,44 %); `pertenca_binaria` 40 444 (-25,21 %); `diagnostico_sem_peso_construido` 69 301 (+1,61 %)

- **Como escrever — Vila de Moatize:** um **único ano** (2017), logo **nenhum CAGR e nenhuma série**. O valor publicado é o **teto de uma banda**, não uma estimativa central: é a soma do GRID3 no cluster de Voronoi **sem peso de construído**, a única que valida (+1,61 %). Inclui área rural atribuída à sede mais próxima, logo é **limite superior**. Toda variante restrita pela máscara de construído subestima o observado (de 25,2 % a 74,5 %) — o GRID3 já é dasimétrico, e pesá-lo outra vez restringe duas vezes. Ver `docs/ADR/0017`.

---

