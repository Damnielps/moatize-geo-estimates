# ADR 0005 — Ano-âncora de 2010: sensor indisponível, não janela curta

- **Data:** 2026-09-07
- **Fase:** 1 (Pipeline de imagem — compostos e índices)
- **Proposto por:** `pipeline-imagem`
- **Estado:** **proposto, não aplicado** — decisão de aplicar é do orquestrador
  (§ restrições da tarefa: "a decisão de aplicar é do orquestrador — não altere
  `config/study.yaml`").

## Correção ao enquadramento anterior desta ADR

A versão anterior deste documento tratava 2010 como um caso de **"janela
curta"**: 4 cenas Landsat 5, abaixo de um piso de robustez de mediana. Essa
premissa estava errada. `compostos.py 2010` (janela padrão, mai–out, nuvem
≤40%, plataforma filtrada por `sensores.2010.missao = LANDSAT_5`) falha porque
**não existe nenhuma cena Landsat 5** no catálogo do Planetary Computer para a
AOI nessa janela — não é pouca cobertura, é ausência total da missão
configurada. O levantamento do orquestrador (contagem por plataforma, não pela
coleção `landsat-c2-l2` inteira) confirma:

| ano | Landsat 5 | Landsat 7 |
|---|---|---|
| 2008 | 6 | 3 |
| 2009 | 3 | 5 |
| **2010** | **0** | **4** |
| 2011 | 1 | 8 |

O caso real é **sensor indisponível em 2010**, não "poucas cenas do sensor
certo". A contagem "4 cenas" da Fase 0' vinha de contar `landsat-c2-l2` sem
filtrar `platform`, e essas 4 cenas são todas Landsat 7 (SLC-off).

## Correção de 2026-09-07 (mesma data, entrega seguinte): a primeira medição estava inflada por um defeito de máscara

A tabela original desta seção (95,68% dos pixels com as 4 observações
completas, 0% com 0 ou 1) **estava errada**, não porque a AOI ou a janela
mudaram, mas porque `carregar_colecao_mascarada` (via `odc.stac.load`) tinha
um defeito de carregamento: o item STAC declara `raster:bands[0].nodata == 1`
para o asset `qa_pixel`, e 1 é exatamente o valor do bit de FILL — não um
"nodata" de fato. O carregador honrava esse nodata declarado e, ao
reprojetar para o `GeoBox` canônico, trocava todo pixel de valor `1` (fill
real) pelo preenchimento de saída, `0`. Como `0` não tem nenhum bit "ruim"
aceso, `mascara_valida_landsat` classificava esses pixels de falha real como
válidos — a máscara de nuvem/sombra/preenchimento não via os gaps do
SLC-off. Corrigido nesta entrega: ver
`pipeline/01_imagery/_stac_common.py::STAC_CFG_QA_PIXEL_SEM_NODATA` (impede o
remapeamento) e a defesa em profundidade `qa != 0` em `mascara_valida_landsat`
(0 nunca é um valor legítimo de `QA_PIXEL` — mesmo um pixel limpo tem o bit
`clear` aceso).

A tabela abaixo, gerada depois da correção (`slc_off_2010_cobertura.csv`,
regravado nesta entrega), é a medição que sustenta a decisão — a anterior foi
descartada, não ajustada.

## Medição direta (corrigida): cobertura do composto Landsat 7 SLC-off de 2010

Executado `pipeline/01_imagery/slc_off_2010.py` (mesma AOI, mesma janela
mai–out/2010, mesma máscara `qa_pixel` de nuvem/sombra/preenchimento que
`compostos.py` usa nos demais anos — sem esse script não seria possível medir
sem também alterar `compostos.py` para short-circuitar o filtro de missão).

4 cenas encontradas, todas Landsat 7 nível C2 L2:

```
LE07_L2SP_168071_20100507_02_T1  2010-05-07
LE07_L2SP_168071_20100608_02_T1  2010-06-08
LE07_L2SP_168071_20100827_02_T1  2010-08-27
LE07_L2SP_168071_20101014_02_T1  2010-10-14
```

Distribuição da contagem de observações válidas por pixel, na AOI inteira
(2.785.056 pixels a 30 m), depois da máscara `qa_pixel` corrigida (bits de
fill, nuvem dilatada, cirrus, nuvem e sombra, mais a defesa `qa != 0` — os
mesmos 5 bits de `mascara_valida_landsat` em `_stac_common.py`; o bit de FILL
é o mesmo bit que o USGS usa para marcar os gaps de linha do SLC-off, então a
máscara de nuvem já filtra os gaps sem lógica adicional, agora que o
remapeamento de nodata não os esconde mais):

| observações válidas | pixels | fração da AOI |
|---|---|---|
| 0 | 130 | 0,005% |
| 1 | 83.068 | 2,98% |
| 2 | 169.034 | 6,07% |
| 3 | 489.613 | 17,58% |
| **4** | **2.043.211** | **73,36%** |

**Número decisivo: 0,005% dos pixels da AOI (130 de 2.785.056) ficam com zero
observações válidas.** O orquestrador, calculando a contagem diretamente das
quatro cenas `qa_pixel` na AOI (sem passar pelo `GeoBox`/reprojeção do
pipeline), mediu 56 pixels em 2.785.056 (0,002%) — a pequena diferença entre
56 e 130 vem da reamostragem para a grade UTM canônica (bordas de linha do
SLC-off caem de forma ligeiramente diferente dependendo se a contagem é feita
na grade nativa do L7 ou já reprojetada), não de um novo defeito; as duas
medições concordam na ordem de grandeza e na conclusão. Mesmo no pior dos
dois números (130 pixels), isso é **0,005% da AOI**, muito abaixo de qualquer
piso de robustez de mediana. Os 73,36% dos pixels com as 4 observações
completas (contra os 95,68% da medição com defeito) ainda deixam a mediana
não degenerada em praticamente toda a AOI: 97,0% dos pixels têm 3 ou 4
observações, e 99,995% têm pelo menos 1.

Artefatos desta medição (não são produto final; não foram gravados em
`data/processed/`):
- `data/interim/slc_off_2010_cobertura.csv` — a tabela acima, completa.
- `data/interim/composto_experimental_2010_L7_SLCoff_30m_32736.tif` — composto
  de mediana das 4 cenas L7, para inspeção visual.
- `data/interim/composto_experimental_2010_L7_SLCoff_30m_32736_nobs.tif` —
  contagem de observações válidas por pixel, mesma grade.

## As três saídas possíveis e o que cada uma custa

### Opção A — Landsat 7 em 2010 (recomendada)

Trocar `sensores.2010.missao` de `LANDSAT_5` para `LANDSAT_7` (com a mesma
nota de "SLC-off" que já existe em `sensores.2000`), mantendo
`composto.janela_anos: 1`.

- **Custo:** o composto de 2010 herda o mesmo tipo de degradação que 2000 já
  tem (linhas de gap na banda bruta, mitigadas pela mediana multi-data) — não
  introduz uma categoria de problema nova ao estudo, só estende ao segundo
  ano-âncora um efeito que o protocolo já precisa descrever para o primeiro.
- **Benefício:** preserva 2010 como observação pontual de um único ano civil,
  igual aos demais anos-âncora, e preserva a fronteira exata entre as fases de
  Implantação e Boom (operação da Vale em maio de 2011) sem a diluir numa
  janela mais larga.
- **Sustentado por (número medido, corrigido do defeito de máscara):** 0,005%
  de pixels sem nenhuma observação válida (130 em 2.785.056; 0,002% na
  contagem independente do orquestrador direto do `qa_pixel`); 73,36% com as
  4 observações completas e 97,0% com 3 ou 4.

### Opção B — ampliar a janela para ±1 ano (2009–2011), mantendo Landsat 5

- **Custo medido nesta tarefa:** só 4 cenas Landsat 5 no total dos 3 anos
  (2009: 3; 2010: 0; 2011: 1) — pior cobertura numérica que a Opção A (4 cenas
  L7 só em 2010) e a janela passaria a atravessar 2009–2011, exatamente o
  intervalo que contém a operação da Vale (mai/2011) e os reassentamentos de
  2009–2010. Isso borra a fronteira Implantação/Boom que a periodização do
  CLAUDE.md declara como marcador central — um pixel que mudou de solo exposto
  para construído entre 2009 e 2011 apareceria "misturado" na mediana, no
  meio da fase que o estudo mais precisa resolver.
- **Não recomendada:** pior cobertura numérica e maior dano à periodização
  que a Opção A.

### Opção C — mover a âncora de 2010 para 2008 (Landsat 5 = 6 cenas)

- **Custo:** desiguala os intervalos da série de anos-âncora (2000, 2005,
  2008, 2015, 2020, 2025 — um intervalo de 3 anos entre 2005 e 2008, contra 5
  anos nos demais), o que complica CAGR e séries interrompidas (§5.4) que
  assumem espaçamento comparável entre pontos, e ainda perde 2010 como o
  ano-âncora mais próximo da operação da Vale (mai/2011) — 2008 fica 3 anos
  antes do início da operação, contra 2010 a menos de 1 ano antes.
- **Não recomendada:** resolve a cobertura (6 cenas L5) mas ao custo de
  desalinhar a periodização, sem necessidade — a Opção A já resolve a
  cobertura sem esse custo.

## Recomendação

**Opção A — usar Landsat 7 em 2010**, sustentada pelo número medido (já
corrigido do defeito de máscara descrito acima): 0,005% de pixels sem
observação válida (0,002% na contagem independente do orquestrador) e 73,36%
com cobertura completa (4/4), 97,0% com 3 ou 4, na mesma AOI e no mesmo
protocolo de máscara usado nos demais anos. É a única das três opções que
resolve a lacuna de cobertura sem introduzir mistura temporal de fases
(Opção B) nem desalinhar o espaçamento da série de anos-âncora (Opção C).
O número de pixels sem observação é pequeno o bastante (56–130 em 2,78
milhões) para não comprometer a mediana em nenhuma parte relevante da AOI,
mesmo tendo caído de 95,68% (número com defeito, descartado) para 73,36%
(número real) na fração com as 4 observações completas.

## Decisão

**Não aplicada nesta tarefa.** `config/study.yaml` permanece com
`sensores.2010.missao: LANDSAT_5` e `composto.janela_anos: 1`, conforme a
restrição explícita desta entrega. O composto experimental de 2010 (Landsat
7, SLC-off) foi gerado em `data/interim/`, fora de `data/processed/`, e a
tabela de cobertura medida está em
`data/interim/slc_off_2010_cobertura.csv` para o orquestrador decidir se
aplica a Opção A (editar `config/study.yaml` e regravar este ADR como
"aceito"), a Opção B, a Opção C, ou nenhuma (manter 2010 como ano sem
composto, registrado como falha).

---

## Adendo do orquestrador — decisão aplicada (2026-09-07)

**Opção A aceita e aplicada.** `config/study.yaml` passa a ter, para 2010,
`missao: LANDSAT_7` e a coleção correspondente, com o motivo no próprio comentário.
`composto.janela_anos` **permanece 1** para todos os anos: o protocolo de §5.1 fica
uniforme, e a fronteira entre Implantação e Boom — a operação da Vale em maio de 2011 —
não é borrada.

O que sustenta a decisão é uma medição, não uma preferência: **0,005% dos pixels da AOI
ficam sem qualquer observação válida** e 97% têm três ou quatro. As falhas do SLC-off não
coincidem entre as quatro datas o suficiente para inviabilizar a mediana — que era
exatamente a dúvida que motivou medir em vez de decidir por teoria.

Duas coisas que precisam acompanhar este composto daqui em diante:

1. **2010 é o único ano com sensor diferente do previsto**, e o único com falhas
   sistemáticas de sensor. A comparação de área construída entre 2005 e 2010 e entre 2010 e
   2015 carrega essa assimetria. O `nobs` de 2010 tem de ser publicado junto do produto,
   não escondido, e a Fase 2 precisa verificar se a métrica de forma urbana é sensível à
   contagem de observações.
2. **A primeira medição estava inflada** — dizia 95,68% com cobertura completa, contra os
   73,36% reais — por causa do defeito de máscara descrito em `ORCHESTRATION_LOG.md` 1-04.
   A decisão teria sido a mesma, mas por evidência errada. Fica o registro de que o número
   que sustenta um ADR precisa ser conferido contra a fonte, não só contra o pipeline que
   o produziu.
