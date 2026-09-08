# Proveniência — Reassentamentos (Cateme, 25 de Setembro, Mwaladzi)

Artefato: `data/raw/reassentamentos.geojson` (+ `.sha256`, `.meta.json`).

## Origem dos dados

| Item | Detalhe |
|---|---|
| URL(s) consultada(s) | `https://nominatim.openstreetmap.org/search` (Cateme, Mwaladzi); `https://overpass.kumi.systems/api/interpreter` (25 de Setembro, sem resultado) |
| Data de acesso | 2026-09-07 |
| Licença | ODbL 1.0 © OpenStreetMap contributors — https://www.openstreetmap.org/copyright |
| Citação exigida | "© OpenStreetMap contributors" |
| CRS | EPSG:4326 (coordenadas decimais lon/lat, conforme retornado pelas APIs) |
| Resolução/nível geográfico | Ponto (node OSM individual por povoado); sem polígono de área ocupada |
| Anos cobertos | Geometria: estado atual do OSM (consultado em 2026-09-07). Atributos de contexto (`n_familias`, `ano_reassentamento`, `operador`): 2009 (Cateme, 25 de Setembro) e 2011 (Mwaladzi), conforme HRW 2013 |
| Nível (§4.0) | A — geometria OSM (ODbL, acesso anônimo, redistribuição e derivadas permitidas). Os atributos numéricos (`n_familias`) vêm de HRW 2013, fonte nível B — ver `data/licenses_parts/reassentamento.md` |
| Hash | `300fdfe29e661255972d9a7ea19cd9cfada0f3f20a4e8f45428f24d48a4681bf` (`reassentamentos.geojson.sha256`, formato `<hash>  <nome do arquivo>`, verificado com `shasum -a 256 -c`) |

## Registro por povoado

- **Cateme** — node OSM `3899065178`, 33.9731329 E / -16.0899313 S. `geometry` presente.
  `n_familias = 716` (corpo do relatório HRW 2013, ver citação abaixo). Ano: 2009.
  Operador: Vale Moçambique.
- **25 de Setembro** — `geometry: null` (intencional). Nominatim (busca "25 de Setembro,
  Moatize, Mozambique") e Overpass (busca `name~"25 de Setembro"` na bbox
  `-16.35,33.50,-16.00,34.10`) não retornaram nenhum elemento em 2026-09-07. Bairro
  urbano de Moatize; `n_familias = 289` (HRW 2013). Ano: 2009. Operador: Vale Moçambique.
  **Nenhuma coordenada foi inventada** — ausência de geometria registrada como tal.
- **Mwaladzi** — node OSM `3899065179`, 34.0326177 E / -16.1057131 S. `geometry`
  presente. `n_familias = 84` (HRW 2013). Ano: 2011. Operador: Riversdale/Rio Tinto
  (projeto Benga). HRW registra ainda um plano de mais 595 famílias até maio/2013,
  não confirmado como concluído nesta pesquisa (não incluído no total do GeoJSON).

## Âncora §8 — verificação

**Item de CLAUDE.md §8:** "Reassentamento Vale — ~1.300 famílias (Cateme, 25 de
Setembro) — fonte declarada: Sapa-AFP 2011; HRW 2013."

**Veredito: DIVERGENTE (não reconciliado).** O relatório primário localizado (HRW 2013,
nível B, CC BY-NC-ND 3.0 US — ver `data/licenses_parts/reassentamento.md`) contém **duas
leituras internamente inconsistentes** do mesmo total Vale (Cateme + 25 de Setembro):

1. **Corpo do relatório, soma das duas seções por povoado = 1.005 famílias**
   - Cateme (rural): *"Vale resettled 716 families into Cateme, a rural resettlement
     designed for farmers located approximately 40 km from Moatize."*
   - 25 de Setembro (urbano): *"Vale resettled 289 families into 25 de Setembro,
     designed as an urban neighborhood in the town of Moatize."*
   - 716 + 289 = **1.005**.

2. **Seção de contexto/introdução do mesmo relatório = 1.365 famílias**
   - *"Between 2009 and 2010, Vale resettled 1,365 households to a newly-constructed
     village, Cateme, and an urban neighborhood, 25 de Setembro."*
   - E, mais adiante: *"Vale's Moatize mine and expansion involved moving 1,365
     households living in and near the villages of Chipanga, Bagamoyo, Mithete, and
     Malabwe into two resettlements or providing them with other forms of
     compensation."*

**Fonte:** Human Rights Watch (2013), "What is a House without Food? Mozambique's
Coal Mining Boom and Resettlements", https://www.hrw.org/report/2013/05/23/what-house-without-food/mozambiques-coal-mining-boom-and-resettlements
(HTTP 200 em 2026-09-07; trechos extraídos diretamente do HTML da página em
2026-09-07).

**Leitura:** nem 1.005 nem 1.365 batem exatamente com a âncora "~1.300" de CLAUDE.md
(que por sua vez cita Sapa-AFP 2011 e HRW 2013 via agregador, não o texto primário
verificado aqui). O valor 1.365 parece incluir famílias compensadas por outras formas
que não resides em Cateme/25 de Setembro ("or providing them with other forms of
compensation"), o que explicaria por que excede a soma 716+289. Isso **não foi
confirmado** no texto disponível — é uma hipótese de leitura, registrada como tal, não
uma reconciliação. **As duas leituras são preservadas** nas notas do GeoJSON
(`data/raw/reassentamentos.geojson`, propriedade `notas` do feature Cateme) e aqui;
nenhum valor foi escolhido como "correto" para substituir o outro.

**Não localizado nesta verificação:** o relatório Sapa-AFP (2011) citado como
co-fonte da âncora §8 não foi localizado em URL de acesso primário (agência de notícias
sem arquivo público estável identificado); a âncora §8, portanto, permanece rastreável
apenas até HRW (2013) nesta Fase 0'.
