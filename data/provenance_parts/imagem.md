# Proveniência — Imagens Orbitais (Fase 0')

Registros de proveniência para dados de imagens orbitais. Nenhuma imagem foi
efetivamente baixada nesta fase; o que segue é o registro do **probe de
disponibilidade** (contagem de cenas), pré-requisito para dimensionar o
composto de estação seca do §5.1.

---

## Reexecução T2 (2026-09-07) — correção do probe de T1

A execução em T1 tinha três defeitos identificados pelo orquestrador:
(1) contava tamanho de página (`limit`) em vez de contagem real; (2) nunca
consultava o Element84 Earth Search, gravando `não_testado` sem emitir
requisição; (3) truncava o mês final em "-30", perdendo 31 de outubro.

Reescrita: `pipeline/00_fetch/probe_stac.py` (lógica) + `probe_stac.sh`
(wrapper fino via `uv run`). Lê `config/study.yaml` (AOI, anos-âncora,
estação seca, `nuvem_max_pct`) — nada hardcoded além dos dois endpoints STAC
e dos nomes de coleção. Consulta **os dois** endpoints para cada ano/coleção.
Contagem: usa `numberMatched`/`context.matched` quando o servidor fornece
(Element84); pagina via `links[].rel == "next"` somando `numberReturned`
quando não fornece (Planetary Computer, que não expõe contagem total).
Falha explícita (linha `status=erro` com a exceção HTTP real) se um endpoint
não responder — nenhuma linha é gravada sem medição.

Saída: `data/interim/stac_disponibilidade.csv`. Reexecutado duas vezes em
sequência para checar idempotência: mesmo conteúdo byte a byte (exceto
`data_consulta`, que muda só se o dia mudar).

### Contagens medidas (bbox 33.50,-16.35,34.10,-16.00; 01/mai–31/out; nuvem ≤40%)

> Medidas primeiro com o bbox provisório (`xmax` 33.95) e **reexecutadas** depois de o
> ADR 0001 confirmar `xmax` 34.10. As contagens ficaram **idênticas**: a extensão a leste
> não cruzou fronteira de tile. O CSV publicado corresponde à AOI confirmada.

| ano | landsat-c2-l2 PC | landsat-c2-l2 E84 | sentinel-2-l2a PC | sentinel-2-l2a E84 |
|---|---|---|---|---|
| 2000 | 7 | 7 | n/a (pré-2015) | n/a |
| 2005 | 6 | 6 | n/a | n/a |
| 2010 | 4 | 4 | n/a | n/a |
| 2015 | 19 | 19 | 0 | 0 |
| 2020 | 16 | 16 | 103 | 194 |
| 2025 | 16 | 18 | 162 | 162 |

**Element84 bate exatamente com a medição de referência do orquestrador em
todas as células** (landsat 2000–2025, sentinel 2020/2025). Isso confirma que
o probe está de fato medindo, não inventando.

**Discrepância PC vs. Element84** em landsat 2025 (16 vs. 18) e sentinel
2020 (103 vs. 194): investigado, não forçado. Ambos os endpoints reivindicam
indexar o mesmo dado de origem (USGS Landsat C2 L2 e Copernicus Sentinel-2
L2A em AWS Open Data), mas usam catálogos STAC mantidos separadamente
(Microsoft Planetary Computer vs. Element84/AWS Earth Search) com filtros de
interseção geometria-vs-bbox e políticas de deduplicação de cena
possivelmente distintas — não foi possível confirmar a causa exata sem
inspecionar item a item os `id`s retornados por cada catálogo (fora do
escopo do probe de disponibilidade). **Registro da discrepância, sem
resolução**: para fins de planejamento de composto, usar o **maior** valor
plausível como teto otimista e o **menor** como piso conservador; a
Fase 1 (download real) vai revelar a contagem definitiva ao materializar
os itens.

---

## Viabilidade por ano (composto de mediana de estação seca, §5.1)

Critério de referência: um composto de mediana robusto a nuvem residual e
ruído sensor-a-sensor tipicamente precisa de **≥ 5–8 cenas independentes**
por período; abaixo disso a mediana degenera para poucos valores válidos por
pixel e a robustez cai.

- **2000 (Landsat 7, pré-SLC-off) — 7 cenas.** Suficiente para mediana.
  Sensor único (ETM+), sem falha de linha antes de mai/2003. OK.
- **2005 (Landsat 5) — 6 cenas.** No limite inferior da faixa de referência.
  Aceitável para mediana, mas com menor robustez a outliers de nuvem
  residual do que 2000/2015/2020/2025.
- **2010 (Landsat 5) — 4 cenas.** **Abaixo do piso de referência.** Um
  composto de mediana com 4 observações por pixel tem alta sensibilidade a
  uma única cena ruidosa (path/row parcialmente nublado que passa no filtro
  de 40 % de nuvem de cena inteira mas cobre a AOI com nuvem local). Isso é
  esperado: Landsat 5 tinha revisita de 16 dias e, no fim de sua vida útil
  (2010, antes da falha do SLC em nov/2011), a AOI cai em poucas
  passagens equatoriais dentro de 6 meses de estação seca sem exceder o
  limiar de nuvem.
  **Implicação para `config/study.yaml`:** `composto.janela_anos` está em
  `1` (só o ano-âncora). Se a Fase 1 confirmar que as 4 cenas de 2010 não
  cobrem a AOI inteira sem falha (parte da cena pode estar fora da faixa de
  nuvem aceitável mas ainda assim nublada localmente), **ampliar a janela
  para ±1 ano (2009–2011) especificamente para 2010** é a correção mínima.
  Isso **quebra a uniformidade "mesmo protocolo em todos os anos" do §5.1**
  e exige um **ADR explícito** (`docs/ADR/`) justificando a exceção,
  documentando quantas cenas adicionais a ampliação traria e se alguma delas
  intersecta datas de composto de anos vizinhos (2005, 2015) — o que
  poderia contaminar a independência dos compostos entre anos-âncora. Não
  alterei `config/study.yaml`; a decisão cabe à Fase 1/ADR.
- **2015 (Landsat 8) — 19 cenas.** Landsat 8 tem revisita de 16 dias mas
  operação mais estável; robusto. Sentinel-2 = 0 cenas na AOI: **correto e
  esperado** — S2A foi lançado em jun/2015, primeiras cenas na órbita e
  processamento L2A relevantes só chegam à região depois; não é falha do
  probe, é ausência real de cobertura antes do fim de 2015 nesta AOI.
  Landsat sozinho já é suficiente para 2015.
- **2020 (Landsat 8 + Sentinel-2) — 16 Landsat + 103–194 Sentinel-2.**
  Amplamente suficiente; sobra de cenas Sentinel-2 permite filtro de nuvem
  mais rigoroso que 40 % se necessário na Fase 1.
  **A discrepância PC (103) vs. E84 (194) importa aqui**: mesmo no piso
  (103), a robustez do composto S2 não é comprometida.
- **2025 (Landsat 9 + Sentinel-2) — 16–18 Landsat + 162 Sentinel-2.**
  Suficiente nos dois sensores.

**Resumo:** todos os anos-âncora têm cobertura suficiente para um composto
robusto de mediana de estação seca, **exceto 2010**, que fica no limite
crítico (4 cenas Landsat 5, sem alternativa Sentinel). Recomendação para a
Fase 1: tentar processar 2010 com a janela padrão primeiro; se a validação
visual/quantitativa mostrar artefatos de nuvem residual ou lacunas de dado
válido na AOI, abrir ADR para ampliar `janela_anos` só para 2010 (2009–2011),
registrando explicitamente a quebra de uniformidade do protocolo.

---

## Rota alternativa sem GEE (§11.3) — veredicto

**Viável.** Os dois endpoints STAC candidatos (Planetary Computer e Element84
Earth Search) respondem, cobrem as mesmas coleções (`landsat-c2-l2`,
`sentinel-2-l2a`) e produzem contagens consistentes (idênticas em 6 de 8
comparações possíveis; divergentes, mas ambas com volume suficiente, nas
outras 2). O pipeline de imagem pode ser implementado sobre `pystac-client` +
`odc-stac`/`stackstac` sem depender de uma única plataforma proprietária,
cumprindo §11.3. Element84/AWS Earth Search é recomendado como fonte de
contagem/canônica quando os dois divergem, por bater exatamente com a
medição independente de referência do orquestrador em todas as células
testadas.

---

## Dados não baixados (nível B) — Planet NICFI

Planet NICFI **não foi baixado** (nível B, §4.0). Situação do programa em
2026: o contrato do NICFI Satellite Data Program com a Planet expirou em
janeiro de 2025; acesso a dados de nível 0/1 foi temporariamente estendido
até abril de 2025; em setembro de 2025 o governo norueguês cancelou o
processo de licitação para a próxima fase. **Não há fase nova em operação
em 2026** — o programa está efetivamente descontinuado, com continuidade
incerta. Classificação mantida como **nível B/inacessível na prática**;
registrado em `data/licenses_parts/imagem.md`. Não incorporado ao pipeline
reprodutível; não há script de obtenção em `pipeline/00_fetch/` porque não
há endpoint ativo a consultar.

---

## Arquivos gerados nesta reexecução

- `pipeline/00_fetch/probe_stac.py` — lógica de consulta/paginação/contagem.
- `pipeline/00_fetch/probe_stac.sh` — wrapper (`uv run`), idempotente.
- `data/interim/stac_disponibilidade.csv` — medição bruta (não versionar
  como resultado publicado; é artefato de diagnóstico de Fase 0').

**Próximo passo (Fase 1):** implementar `pipeline/00_fetch/fetch_stac.py`
para baixar cenas de fato via a rota Element84 (ou PC como espelho),
gerar compostos de mediana, e então preencher os registros de proveniência
por composto (URL, coleção, cenas componentes, licença, citação, resolução,
CRS) neste mesmo arquivo.
