# Proveniência — Compostos de Imagem e Índices (Fase 1)

Fragmento gerado por `pipeline/01_imagery/compostos.py`. **Não editar à mão**
— reexecute o script para regenerar. Consolidado em `PROVENANCE.md` por
`scripts/consolidar_registros.py`. Este fragmento é novo e não substitui
`data/provenance_parts/imagem.md` (Fase 0', fechado).

Catálogo STAC canônico: `https://planetarycomputer.microsoft.com/api/stac/v1` (ver `docs/ADR/0004-divergencia-catalogos-stac.md`).

Nenhum processo estocástico: `config/seeds.yaml` não se aplica a este
estágio (mediana não amostra nem sorteia). Determinismo garantido pela
ordenação por `id` dos itens STAC antes da composição.

## Defeito corrigido nesta entrega (Fase 1) e descarte dos produtos anteriores

Os cinco compostos gravados por uma execução anterior desta mesma tarefa
(2000, 2005, 2015, 2020, 2025) foram **descartados e regravados do zero**,
não ajustados. `odc.stac.load` honrava o `nodata: 1` declarado no
`raster:bands` do asset `qa_pixel` (Landsat C2 L2) — e 1 é exatamente o
valor do bit de FILL, não um nodata de fato. Isso trocava todo pixel de
falha real (fill/gap) por `0` na banda carregada, e `0` não tem nenhum bit
de qualidade ruim aceso: a máscara de nuvem/sombra/preenchimento
classificava esses pixels de falha como válidos. O sintoma mais visível
era o composto de 2010 (Landsat 7 SLC-off, medição experimental de
`docs/ADR/0005-...md`): declarava 95,68% dos pixels com as 4 observações
completas e 0% sem nenhuma, quando a contagem correta é 73,36% com as 4
e 0,005% sem nenhuma — bom demais para ser real em cenas SLC-off.

Corrigido via `_stac_common.STAC_CFG_QA_PIXEL_SEM_NODATA` (passado a
`odc.stac.load(..., stac_cfg=...)`, desliga o nodata declarado só para
`qa_pixel`) e uma defesa em profundidade em `mascara_valida_landsat`
(`qa == 0` também é tratado como inválido — 0 nunca é um valor legítimo de
`QA_PIXEL`). Ver `pipeline/tests/test_imagery.py::test_nobs_bate_com_calculo_direto_do_qa_pixel` para o contrato de
regressão (usa as cenas Landsat 7/2010, o único conjunto do repositório
com pixels de fill reais dentro da AOI) e `config/tolerances.yaml ->
regressao_numerica.contrato_qa_pixel` para a tolerância declarada.

Os cinco compostos e todos os índices abaixo foram gerados **depois**
dessa correção — nenhum artefato do defeito permanece em
`data/processed/imagery/`.

## Ano-âncora 2010

- **Arquivo**: `data/processed/imagery/composto_2010_30m_32736.tif`
- **Janela temporal**: `2010-05-01T00:00:00Z/2010-10-31T23:59:59Z` (janela_anos=1)
- **Landsat**: landsat-7, 4 cenas
- **Sentinel-2**: não incluído (fora do complemento do ano ou sem cobertura)
- **Observações válidas por pixel**: mínimo 0, mediana 4.0
- **Pixels sem nenhuma observação válida**: 130 de 2785056 (0.00%)
- **Commit**: `desconhecido (git indisponível)`
- **Hash de `config/study.yaml`**: `7b09119f1c8660a361e9711c5145ca5e2c134f6701204e6dc400f1469e9cfdfd`
- **Data de processamento**: 2026-09-08T00:39:40.003841+00:00
- **Selo**: observado

IDs das cenas Landsat: LE07_L2SP_168071_20100507_02_T1, LE07_L2SP_168071_20100608_02_T1, LE07_L2SP_168071_20100827_02_T1, LE07_L2SP_168071_20101014_02_T1

<!-- SECAO_CLASSIFICACAO_INICIO -->

## Classificação — redesenho da Fase 1 (§5.1, §10)

Gerado por `pipeline/01_imagery/classificacao.py`. Substitui a versão reprovada, cujo defeito central era usar **limiares adaptativos por percentil**: eles selecionavam uma fatia quase constante da AOI todo ano (3,4–4,4%), de modo que o produto media o percentil, não o crescimento.

**Papéis das referências (escolhidos e assumidos, sem circularidade):** WSF Evolution **semeia o treino** e por isso **não** é usado como validação; GHSL BUILT-S R2023A (épocas observadas 2000–2020) é **referência independente de concordância** e não toca em treino nem em limiar; as épocas 2025/2030 do GHSL são extrapoladas e por isso 2025 fica **sem** referência de produto, declarado.

**Separação fenológica.** Features incluem `NDVI(chuva)` e a amplitude `NDVI(chuva) − NDVI(seca)` (nov(A−1)–abr(A) contra mai–out(A)). Separabilidade medida nesta AOI entre WSF-construído e não-construído (d de Cohen): amplitude 1,83 (2000) / 2,03 (2015) / 1,87 (2025); NDBI 0,39 / 0,71 / 0,29. Cobertura da estação chuvosa por ano em `data/processed/cobertura_estacao_chuvosa.csv`.

**Regras temporais declaradas.** R1: primeira detecção só vale se confirmada no ano-âncora seguinte (2025 não é confirmável — não há ano seguinte). R2: permanência, `construído(t) = ∪_{t'≤t}`. As três séries (sem restrição, após R1, após R2) estão lado a lado em `data/processed/area_construida_por_ano.csv`.

**Acurácia não é calculada aqui.** Ver `pipeline/01_imagery/acuracia.py` e `data/processed/acuracia_por_ano.csv`.

**Pegada minerária e de reassentamento — classe própria desde docs/ADR/0011.** Antes, `industrial` era `construido & poligono_maus` e `reassentamento` era `restante & buffer`: as duas camadas eram a INTERSEÇÃO da classificação de construído com uma máscara espacial, e mediam 'construído dentro do polígono', não a pegada. O defeito é físico: cava, pilha de estéril e rejeito são rocha e solo exposto — espectralmente NÃO são construído — e um classificador de construído os perde por definição (media 4,2 km² contra os 59,2 km² de Maus et al., 7,1%). A pegada passou a ser classificada por assinatura própria: solo/rocha exposto persistente (NDVI de seca E de chuva abaixo de 0.6 da mediana da paisagem do próprio ano — normalização radiométrica anual, NÃO percentil da imagem), unida ao construído do ano, dentro do envelope de Maus dilatado em 500 m. Cobertura dos polígonos de Maus em 2025: de 7,1% para 76,3%.

**Limiar calibrado, e onde isso cria circularidade.** O limiar foi calibrado por J de Youden contra Maus et al. em 2020, o ano-âncora de menor defasagem em relação à referência. Logo **a concordância com Maus em 2020 não é validação independente**. A evidência independente é temporal: a mesma regra devolve **0,000 km² em 2000 e 2005**, antes da licença da Vale (2006) — placebo temporal que se mantém nas 30 configurações de `data/processed/pegada_sensibilidade.csv`.

**`industrial` e `reassentamento` NÃO são subconjuntos de `construido`.** Elas incluem rocha e solo exposto. Consequência aritmética: `urbano + industrial + reassentamento > area_construida`, e **só `urbano` é área construída** — a soma das três não tem significado. A máscara de construído é publicada à parte, em `construido_<ano>_30m_32736.tif`, e é ela que define o estrato da validação de acurácia.

**O que não mudou, verificado e não presumido:** a classificação de construído é idêntica à anterior (o raio de exclusão de negativos do treino foi mantido em 1500 m, separado do raio de detecção de 1000 m); os 288 pontos de validação não se moveram (0 de 288); `data/processed/acuracia_por_ano.csv` é idêntico por diff e a acurácia do usuário de `construido` continua 0,27-0,63 (docs/ADR/0009); `urbano` dentro dos polígonos de mineração continua 0,0000 km² de 2010 em diante. O único efeito sobre `urbano` é a migração de construído do envelope minerário (planta, pátio ferroviário) para `industrial`: 44,02 -> 42,84 km² em 2025.

**Camada de reassentamento — incompleta por falta de dado:** Buffer de 1000 m em torno do ponto único de cada povoado (não há polígono de traçado real de nível A) delimitando ONDE PROCURAR. Dentro dele a camada é a pegada: solo exposto persistente (mesma regra e mesmo limiar razao_verde < 0.6 da pegada minerária) em união com o construído do ano. **A detecção não exige assinatura de construído** — foi esse o defeito corrigido: habitação de reassentamento é baixa, esparsa e de telhado metálico ou fibrocimento, e a 30 m um classificador de construído a perde (a camada anterior media 0,07 km², cerca de um décimo do piso plausível). **O que a camada mede é a pegada do povoado — lotes, vias e terreno alterado — não a área de telhado.** **A camada continua incompleta e isso é estrutural, não um bug**: o povoado urbano '25 de Setembro' (289 famílias, HRW 2013) tem `geometry: null` em data/raw/reassentamentos.geojson — Nominatim e Overpass não o localizaram e a coordenada não foi inventada. Consequência aritmética: o construído do 25 de Setembro está contado dentro de `urbano`, isto é, `urbano` inclui crescimento por reassentamento que §10 manda separar. A magnitude desse vazamento não é estimável sem a geometria.

### Ano-âncora 2000

- **Método `industrial`:** classe própria de solo/rocha exposto persistente (razao_verde < 0.6) dentro do envelope de Maus et al. dilatado em 500 m, união com o construído do ano no mesmo envelope. Resultado 0,00 km²: PLACEBO TEMPORAL — a concessão da Vale é de 2004 e a licença de 2006, então a regra tinha de devolver ~zero aqui, e devolve. Sem acumulação (anterior a 2006).
- **Área construída (km²):** sem restrição 16.9 · após R1 14.0 · após R2 (publicada) 14.0
- **Camadas (km²):** urbano=14.04, industrial=0.00, reassentamento=0.00, vegetacao=266.51, solo_exposto=2187.35, agua=0.60 (industrial e reassentamento são PEGADAS, não subconjuntos de construído)
- **Pegada sem permanência (km²):** industrial=0.00, reassentamento=0.00 · cobertura dos polígonos de Maus: 0.0% · mediana NDVI(chuva) da paisagem: 0.474
- **Importância das features (5 maiores):** ndvi=0.484, evi=0.202, ndwi=0.104, ndbi=0.048, red=0.029

### Ano-âncora 2005

- **Método `industrial`:** mesma regra de 2000. Resultado 0,00 km²: segundo ponto do placebo temporal, um ano antes da licença. Sem acumulação (anterior a 2006).
- **Área construída (km²):** sem restrição 23.9 · após R1 20.7 · após R2 (publicada) 20.7
- **Camadas (km²):** urbano=20.73, industrial=0.00, reassentamento=0.00, vegetacao=273.59, solo_exposto=2167.75, agua=0.62 (industrial e reassentamento são PEGADAS, não subconjuntos de construído)
- **Pegada sem permanência (km²):** industrial=0.00, reassentamento=0.00 · cobertura dos polígonos de Maus: 0.0% · mediana NDVI(chuva) da paisagem: 0.543
- **Importância das features (5 maiores):** ndvi=0.469, evi=0.200, ndwi=0.098, red=0.043, ndbi=0.042

### Ano-âncora 2010

- **Método `industrial`:** solo/rocha exposto persistente + construído, dentro do envelope, acumulado desde 2006. Obras desde ~2007; a mina só opera em mai/2011, então a pegada aqui é de decapagem e canteiro, não de lavra plena.
- **Área construída (km²):** sem restrição 33.3 · após R1 28.5 · após R2 (publicada) 29.6
- **Camadas (km²):** urbano=28.26, industrial=7.45, reassentamento=1.20, vegetacao=1891.85, solo_exposto=529.60, agua=1.63 (industrial e reassentamento são PEGADAS, não subconjuntos de construído)
- **Pegada sem permanência (km²):** industrial=7.45, reassentamento=1.20 · cobertura dos polígonos de Maus: 7.0% · mediana NDVI(chuva) da paisagem: 0.477
- **Importância das features (5 maiores):** ndvi=0.433, evi=0.161, ndwi=0.148, red=0.068, ndbi=0.041

### Ano-âncora 2015

- **Método `industrial`:** solo/rocha exposto persistente + construído, dentro do envelope, acumulado desde 2006. Operação da Vale desde 2011 e Benga desde 2012. O envelope vem de imagem 2017-2019, POSTERIOR a este ano: parte dele ainda não era lavra em 2015, e é por isso que a extensão é medida pela assinatura do ano e não pelo polígono.
- **Área construída (km²):** sem restrição 51.7 · após R1 36.4 · após R2 (publicada) 38.8
- **Camadas (km²):** urbano=36.76, industrial=30.15, reassentamento=1.93, vegetacao=2230.93, solo_exposto=152.37, agua=0.16 (industrial e reassentamento são PEGADAS, não subconjuntos de construído)
- **Pegada sem permanência (km²):** industrial=27.66, reassentamento=1.64 · cobertura dos polígonos de Maus: 41.2% · mediana NDVI(chuva) da paisagem: 0.670
- **Importância das features (5 maiores):** ndvi=0.398, ndwi=0.183, evi=0.116, mndwi=0.050, green=0.049

### Ano-âncora 2020

- **Método `industrial`:** solo/rocha exposto persistente + construído, dentro do envelope, acumulado desde 2006. Defasagem de ~1 ano em relação à referência — é neste ano que o limiar foi calibrado, e por isso a concordância com Maus em 2020 não é validação independente.
- **Área construída (km²):** sem restrição 38.9 · após R1 36.1 · após R2 (publicada) 41.4
- **Camadas (km²):** urbano=39.21, industrial=46.43, reassentamento=2.00, vegetacao=679.02, solo_exposto=1689.60, agua=2.95 (industrial e reassentamento são PEGADAS, não subconjuntos de construído)
- **Pegada sem permanência (km²):** industrial=36.70, reassentamento=0.63 · cobertura dos polígonos de Maus: 62.7% · mediana NDVI(chuva) da paisagem: 0.579
- **Importância das features (5 maiores):** ndvi=0.466, evi=0.207, ndwi=0.119, ndbi=0.041, red=0.040

### Ano-âncora 2025

- **Método `industrial`:** solo/rocha exposto persistente + construído, dentro do envelope, acumulado desde 2006. Defasagem de ~6 anos: o envelope dilatado em 500 m admite avanço de lavra posterior a 2019, mas expansão além dessa faixa fica fora e é subestimação declarada.
- **Área construída (km²):** sem restrição 39.6 · após R1 39.6 · após R2 (publicada) 48.3
- **Camadas (km²):** urbano=42.84, industrial=62.50, reassentamento=2.32, vegetacao=151.95, solo_exposto=2201.44, agua=40.31 (industrial e reassentamento são PEGADAS, não subconjuntos de construído)
- **Pegada sem permanência (km²):** industrial=56.67, reassentamento=1.01 · cobertura dos polígonos de Maus: 76.3% · mediana NDVI(chuva) da paisagem: 0.331
- **Importância das features (5 maiores):** ndvi=0.303, evi=0.212, ndwi=0.125, ndbi=0.074, mndwi=0.063

<!-- SECAO_CLASSIFICACAO_FIM -->












<!-- SECAO_ACURACIA_INICIO -->

## Validação de acurácia (Fase 1, §5.1 e §10)

Gerado por `pipeline/01_imagery/acuracia.py`. **Não editar à mão.**

**Natureza do rótulo de referência.** Os 288 pontos (24 por estrato por ano, 6 anos) foram rotulados por **interpretação visual automatizada** de recortes RGB (R=SWIR1, G=NIR, B=vermelho) do composto de estação seca do próprio ano, em duas janelas por ponto — contexto de 3,0 km e detalhe de 0,9 km, a 30 m. O intérprete é um **modelo de linguagem multimodal**, não um intérprete humano treinado e não verdade de campo. **Isto não é fotointerpretação** e não é chamado assim em nenhum artefato. O erro do intérprete entra no número como se fosse erro do mapa; a 30 m, construído esparso e solo exposto são frequentemente indistinguíveis para qualquer intérprete.

**Cegamento.** As folhas de contato exibem `id_cego`, atribuído sobre uma permutação determinística que mistura os dois estratos. O intérprete não sabia, ao olhar o recorte, se o mapa classificava aquele pixel como construído. Sem isso a concordância mediria a pista, não a imagem.

**Estimador.** Olofsson et al. (2014), estratificado pelas classes do mapa, com pesos `W_h` iguais à fração de área da AOI em cada estrato e IC de 95 %.

**Intérprete(s):** Claude (modelo multimodal, Anthropic) — interpretação visual de recortes RGB; NÃO é fotointerpretação humana nem verdade de campo

| ano | n | AG | IC95 AG | kappa | AU construído | IC95 AU | AP construído | IC95 AP | indet. | W construído | alavanca de 1 ponto |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 2000 | 48 | 0.997 | ±0.001 | 0.684 | 0.522 | ±0.209 | 1.000 | ±0.000 | 1 | 0.0056 | 0.0414 |
| 2005 | 48 | 0.997 | ±0.002 | 0.735 | 0.583 | ±0.202 | 1.000 | ±0.000 | 0 | 0.0083 | 0.0413 |
| 2010 | 48 | 0.991 | ±0.002 | 0.426 | 0.273 | ±0.191 | 1.000 | ±0.000 | 4 | 0.0118 | 0.0449 |
| 2015 | 48 | 0.950 | ±0.084 | 0.233 | 0.542 | ±0.204 | 0.164 | ±0.273 | 1 | 0.0155 | 0.0428 |
| 2020 | 48 | 0.869 | ±0.133 | 0.090 | 0.522 | ±0.209 | 0.066 | ±0.070 | 1 | 0.0165 | 0.0410 |
| 2025 | 48 | 0.993 | ±0.004 | 0.766 | 0.625 | ±0.198 | 1.000 | ±0.000 | 0 | 0.0193 | 0.0409 |

AG = acurácia global · AU = acurácia do usuário (1 − comissão) · AP = acurácia do produtor (1 − omissão).

**Como ler estes números, e como não ler.**

1. A **acurácia global** cumpre a meta de §10 (≥ 0,85) em todos os anos, mas essa comparação é fraca aqui: o estrato `nao_construido` ocupa 98–99,5 % da AOI, e um mapa que errasse *toda* a classe construída ainda teria acurácia global ≈ 0,98. A meta de §10 não discrimina neste desenho.
2. O que informa sobre a classe de interesse é a **acurácia do usuário**: 0,27–0,63. Cerca de metade dos pixels que o mapa chama de construído não parecem construídos ao intérprete — **comissão alta e consistente**, pior em 2010. É coerente com o viés já documentado no ADR 0008 e com a confusão solo exposto × construído na savana semiárida em estação seca.
3. A **acurácia do produtor não é utilizável neste n**. A coluna `alavanca de 1 ponto` é a fração da área da AOI que **um único** ponto de referência do estrato `nao_construido` carrega no estimador (≈ 0,041). Em 2020, 3 pontos desse estrato foram lidos como construídos, o que projeta ~12 % da AOI como construído não mapeado — implausível. O valor de 0,07 mede a fragilidade do desenho, não o mapa.
4. O **kappa** cai a 0,09–0,23 em 2015 e 2020 e não atinge a meta de 0,70 em 2010, 2015 e 2020. Kappa é instável para classe rara; é reportado por exigência de §5.1, não como critério.

**O que seria preciso para estreitar o intervalo.** O IC da acurácia global chega a ±0,133 (2020). A largura é dominada pelo estrato `nao_construido`, cuja variância escala com `W²/n`. Levar o IC de 2020 de ±0,13 para ±0,03 exigiria ~n=24 → ~n=470 pontos nesse estrato **por ano** (o IC escala com 1/√n), isto é, cerca de 2 800 recortes interpretados um a um em vez de 288. Isso não é atingível por interpretação neste ambiente; seria atingível com verdade de campo, com imagem de resolução submétrica (fora do nível A), ou aceitando um rotulador automático — que é exatamente o que reprovou a versão anterior.

**Papel do WSF Evolution.** Semeia o treino; por construção **não valida**. Nenhuma métrica contra WSF aparece em `acuracia_por_ano.csv`. A concordância está em `data/processed/concordancia_wsf.csv`, rotulada como concordância entre produtos com dependência por construção.

<!-- SECAO_ACURACIA_FIM -->



