# ADR 0011 — A pegada minerária e a de reassentamento passam a ser classe própria, não interseção com "construído"

- **Data:** 2026-09-08
- **Fase:** 1 (Pipeline de imagem), reaberta
- **Decidido por:** usuário; execução pelo subagente de métodos causais
- **Estado:** aceito
- **Substitui:** o método declarado em `METODO_INDUSTRIAL_POR_ANO` e `NOTA_BUFFER_REASSENTAMENTO` da versão anterior de `pipeline/01_imagery/classificacao.py`

## Contexto

As camadas `industrial` e `reassentamento` eram definidas como:

```python
industrial     = construido & rasterizar(poligono_mineracao)
reassentamento = restante   & buffer_ativo
```

Isto é, a **interseção da classificação de construído com uma máscara espacial**. Elas
mediam "construído dentro do polígono", não a pegada.

O defeito é físico, não de programação: **cava, pilha de estéril e rejeito são rocha e
solo exposto — espectralmente não são construído**, e um classificador de construído os
perde por definição. O mesmo vale para habitação de reassentamento, que é baixa, esparsa
e de telhado metálico ou fibrocimento, e a 30 m não produz a assinatura de construído
denso.

Medição que motivou a reabertura (AOI, EPSG:32736, 2025):

| | km² |
|---|---|
| polígonos de Maus et al. v2 na AOI | 59,2 |
| classificados como `industrial` | 4,2 (**7,1 %** dos polígonos) |
| pegada minerária em nenhuma camada | 55,0 |
| `reassentamento` | 0,07 (piso plausível: ~0,5) |

O contrato de exclusividade mútua passava, e passava com razão: as camadas eram
disjuntas. Nenhum contrato perguntava se a camada **media o que o nome dela promete**.
Essa lacuna foi fechada por `config/plausibilidade.yaml` e
`pipeline/tests/test_plausibilidade.py`.

A intenção original era legítima: os polígonos de Maus são de Sentinel-2 2017–2019, um
retrato único, e interseccioná-los com a classificação anual era a forma de obter série
temporal. O erro estava na execução, não no objetivo.

## Decisão

**1. A pegada passa a ser classificada por assinatura espectral própria.** A classe é
*solo/rocha exposto persistente*: NDVI baixo **nas duas estações**. Numa savana
semiárida, solo exposto natural esverdeia na estação chuvosa; cava, pilha de estéril,
rejeito e terreno decapado não. É a mesma separação fenológica que resolveu a confusão
solo × construído na classificação urbana, usada aqui para o fim oposto — **isolar** o
solo exposto persistente em vez de descartá-lo.

**2. O limiar é relativo à paisagem do próprio ano, não absoluto.** NDVI absoluto não é
comparável entre os anos-âncora desta série: a mediana de NDVI(chuva) da paisagem vai de
0,669 (2015) a 0,330 (2025), por diferença de sensor e de pluviosidade. Medido, um corte
absoluto de NDVI(chuva) < 0,25 marcaria 83 km² fora dos polígonos em 2000 e **472 km²**
em 2025 — mediria o ano, não a mina. O critério adotado é

```
razao_verde = NDVI(pixel) / mediana(NDVI da paisagem de referência do ano) < 0,60
```

exigido na seca **e** na chuva, com água excluída.

Isto **não é um percentil da imagem** — o defeito que reprovou a primeira versão da
classificação. Um percentil seleciona uma fração fixa da AOI por construção; aqui o
denominador é uma estatística de tendência central de uma população definida a priori
(pixels válidos, fora d'água, fora do envelope minerário e fora dos buffers de
reassentamento), e a fração selecionada é livre para variar — e varia de 0 % a mais de
50 % do envelope ao longo da série.

**3. Os polígonos de Maus entram como referência e restrição, não como máscara que
exige construído.** Eles definem um **envelope de busca** — os polígonos dilatados em
500 m, correspondendo a ~80 m/ano de avanço de frente de lavra entre 2019 e 2025. O
envelope restringe **onde** a classe pode aparecer; a **extensão é medida por ano**.

**4. O limiar 0,60 foi calibrado por J de Youden contra Maus em 2020**, o ano-âncora de
menor defasagem em relação à referência (~1 ano). J tem máximo achatado em 0,60–0,65
(J = 0,405); adota-se o mais conservador. **F1 foi rejeitado como critério**: dentro do
envelope a prevalência da classe é ~52 %, e F1 cresce monotonicamente com o recall até
limiares absurdos, sem máximo interior útil.

**Consequência declarada: a concordância com Maus em 2020 não é validação independente**
— o limiar foi ajustado nela.

**5. Reassentamento segue a mesma lógica**, com o mesmo limiar. Os buffers dos povoados
delimitam **onde procurar**; a detecção não exige assinatura de construído. O raio de
detecção cai de 1500 m para **1000 m**: a 1500 m a camada devolvia 2,34 km² já em 2010,
acima do teto de plausibilidade da fase, porque varria as machambas do entorno para
dentro da camada.

**6. O raio de exclusão de negativos do treino permanece em 1500 m**, separado do raio de
detecção. Os dois têm propósitos opostos — a exclusão quer ser generosa, a detecção quer
ser restrita — e não devem ser o mesmo parâmetro.

**7. `industrial` e `reassentamento` deixam de ser subconjuntos de `construido`.**
Consequência aritmética que precisa estar escrita em toda saída: `urbano + industrial +
reassentamento > area_construida`, e **só `urbano` é área construída**. A soma das três
colunas não tem significado.

**8. A máscara de construído passa a ser persistida** como `construido_<ano>_30m_32736.tif`
e é ela, não a união das três camadas, que define o estrato da validação de acurácia.

## O que a decisão produziu

Série publicada (`data/processed/pegada_por_ano.csv`), km², após permanência:

| ano | industrial | cobertura de Maus | reassentamento |
|---|---|---|---|
| 2000 | 0,00 | 0 % | 0,00 |
| 2005 | 0,00 | 0 % | 0,00 |
| 2010 | 7,45 | 7 % | 1,20 |
| 2015 | 30,15 | 41 % | 1,93 |
| 2020 | 46,43 | 63 % | 2,00 |
| 2025 | 62,50 | **76 %** | 2,32 |

A cobertura dos polígonos de Maus em 2025 passa de **7,1 % para 76,3 %**.

## Evidência independente: o placebo temporal

A concordância com Maus em 2020 é circular (item 4). A evidência **não circular** é
temporal e sai de graça do desenho: a mesma regra, com os mesmos parâmetros, aplicada aos
compostos de 2000 e 2005 — quando a concessão da Vale ainda não existia (licitação 2004,
licença 2006) — devolve **0,000 km²**. Uma regra que estivesse apenas marcando "terreno
seco dentro de um polígono" marcaria o polígono em 2000 também.

Esse resultado é **invariante à parametrização**: nas 30 combinações de
`data/processed/pegada_sensibilidade.csv` (razão 0,50–0,70 × envelope 250–750 m × fecho
3–5 px), a área pré-2006 é 0,000 km² em **todas**, e a cobertura de Maus em 2025 fica
entre 71 % e 84 % (área 47,9–85,3 km²). **As 30 configurações satisfazem o contrato**, o
que responde à objeção de que os parâmetros teriam sido ajustados até passar.

## O que NÃO mudou (verificado, não presumido)

- **A classificação de construído é bit-idêntica à anterior.** A série
  `area_construida_por_ano.csv` (14,04 → 48,29 km²) não se move. Isso foi garantido de
  propósito, mantendo o raio de exclusão de negativos em 1500 m (item 6).
- **Os 288 pontos de validação são os mesmos** — verificado ponto a ponto: 0 de 288
  mudaram de posição ou de estrato. Os rótulos interpretados continuam válidos.
- **`data/processed/acuracia_por_ano.csv` é idêntico**, verificado por diff. A acurácia do
  usuário de `construido` continua **0,27–0,63** e `docs/ADR/0009` continua valendo sem
  alteração.
  > **Valor superado (registro histórico).** Esta faixa é a medição vigente na data
  > deste ADR. `docs/ADR/0014` reexecutou a validação sobre os estratos corrigidos e
  > obteve **0,286–0,625** (comissão 37,5 %–71,4 %). O que este item afirma — que a
  > acurácia **não mudou** com a correção da pegada — continua verdadeiro; o número
  > que o ilustra é anterior à reexecução e não deve ser citado como corrente.
- **§10 não regride: `urbano` dentro dos polígonos de mineração = 0,0000 km² em todos os
  anos.** As seis camadas continuam mutuamente exclusivas e `urbano ⊆ construido`.
- **`docs/ADR/0008` não é afetado:** a série de tendência de área construída continua
  sendo a do WSF Evolution, não a classificação própria.

O efeito sobre `urbano` é pequeno e numa única direção — pixels construídos dentro do
envelope minerário (planta de beneficiamento, pátio ferroviário) migram de `urbano` para
`industrial`: **44,02 → 42,84 km² em 2025 (−1,18 km²)**.

## Alternativa rejeitada

**Usar os polígonos de Maus como retrato de 2017–2019, sem série.** Era a saída honesta se
a pegada não fosse classificável com dados de nível A, e estava sobre a mesa. Foi
rejeitada porque a pegada **é** classificável: a separabilidade medida entre envelope e
paisagem em 2025 é d de Cohen −1,58 em NDVI(chuva), −1,98 em NIR e −1,47 em SWIR1, e o
placebo temporal confirma que a regra responde ao objeto e não ao polígono. Manter só o
retrato descartaria a resposta à pergunta específica 2 de §1 (que parcela do salto é
pegada industrial) e à H3 (pegada industrial cresce mais rápido que a urbana entre 2010 e
2015 e estabiliza após 2016) — hipóteses que exigem série.

**Segunda alternativa rejeitada:** preenchimento de buracos (`binary_fill_holes`) dentro do
envelope, que elevaria a cobertura de Maus em 2025 de 76 % para ~88 %. Rejeitada porque
acrescentaria de 10 a 25 % de área **sem que nenhum pixel acrescentado tivesse a
assinatura da classe** — seria ajustar o número, não medir o objeto.

## Consequências e limitações declaradas

1. **A camada `industrial` não distingue lavra de infraestrutura.** Cava, pilha de
   estéril, rejeito, planta e pátio entram todos como "pegada". A pergunta "quanto é
   buraco e quanto é edificação" não é respondível com este produto.
2. **`reassentamento` mede a pegada do povoado** — lotes, vias e terreno alterado — **não
   a área de telhado**. A faixa de plausibilidade de `config/plausibilidade.yaml` foi
   derivada de área de lote (800 famílias × 500–1000 m²), e a `descricao` daquela camada
   foi corrigida para dizer "pegada" em vez de "área construída". **Nenhum número de
   faixa foi alterado.**
3. **O povoado "25 de Setembro" continua sem geometria** e fora da conta. É subestimação
   declarada, não erro, e o construído dele segue contado dentro de `urbano`.
4. **Expansão da lavra além de 500 m do polígono de 2019 não é capturada** — `industrial`
   é subestimado em 2025 por essa margem.
5. **A pegada herda a permanência (R2)** pelo mesmo argumento usado em construído. A série
   sem permanência é publicada ao lado, em `pegada_por_ano.csv`, coluna
   `area_sem_permanencia_km2`. Em 2020 a diferença é grande (36,7 sem permanência contra
   46,4 publicada) e o leitor precisa vê-la: parte da pilha de estéril de 2015 aparece
   revegetada ou sombreada em 2020, e a permanência a mantém na série.
6. **Reabilitação minerária não é detectável neste desenho.** Se uma pilha for revegetada,
   a permanência a mantém contada. Não há evidência de reabilitação concluída em Moatize
   no período, mas a limitação é do método, não do caso.
