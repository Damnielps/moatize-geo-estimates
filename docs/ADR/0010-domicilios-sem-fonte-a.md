# ADR 0010 — Produto de domicílios (edificações × tamanho médio) não construído por falta de denominador em nível A

- **Data:** 2026-09-08
- **Fase:** 2 (§5.3, reconstrução demográfica e domiciliar)
- **Decidido por:** `metricas-urbanas` (subagente), a confirmar pelo orquestrador
- **Estado:** aceito, com emenda de 2026-09-08 (ver adendo ao final)

## Contexto

§5.3 pede domicílios por contagem de edificações (Google Open Buildings / Microsoft
Global Building Footprints, ambos nível A, listados em `data/LICENSES.md`) multiplicada
pelo tamanho médio do domicílio do censo, para 2020–2025, com retropolação por área
construída para anos anteriores.

O numerador (contagem de edificações) é buscável: Open Buildings e Microsoft Footprints
estão classificados nível A e não foram espelhados ainda. O denominador — tamanho médio
do domicílio por Tete/Moatize — **não tem fonte de nível A confirmada**:

- A tabulação específica ("pessoas por domicílio", "domicílios urbanos com atividade
  agrícola") do Censo 2007/2017 não foi localizada como página pública indexável — o
  catálogo `mozdata.ine.gov.mz` carrega via SPA/JavaScript e não expõe a tabulação por
  raspagem automatizada (`data/LICENSES.md`, linha "INE — Censos 2007 e 2017").
- Mesmo se localizada, qualquer tabulação lida diretamente de um documento do INE herda
  nível **C** (`data/DATA_AUDIT.md`, arbitragem (a)): sem licença localizável, documento
  do INE em si não sustenta número publicado — e não há reprocessador HDX/OCHA para
  tamanho médio de domicílio (o COD-PS só cobre totais populacionais por ADM2, não
  domicílios nem tabulações de composição domiciliar).
- IOF (Inquérito ao Orçamento Familiar) tem desagregação só provincial, não
  distrital/municipal, e cobre consumo/insegurança alimentar, não tamanho médio do
  domicílio diretamente.

## Decisão

**Não construir o produto "domicílios por edificação × tamanho médio" nesta rodada**, e
**não baixar Open Buildings/Microsoft Footprints ainda**. A regra de proveniência é
categórica: uma razão herda o nível do pior dos dois termos. Um numerador em nível A
dividido por um denominador em nível C (ou ausente) produz um número que **não pode
sustentar publicação no núcleo** (§4.0 regra 1; §10) — o produto inteiro sairia
carimbado C antes de qualquer processamento, e o custo de download (ambos os datasets
de edificações são multi-GB na escala da AOI) não se justifica para um produto que já
nasce fora do núcleo reprodutível.

## Alternativa rejeitada

**Usar um tamanho médio de domicílio nacional/genérico (ex.: de relatório internacional
sobre Moçambique) como aproximação.** Rejeitada: seria um número não específico a
Tete/Moatize, aplicado sobre uma contagem de edificações espacialmente precisa — a falsa
precisão resultante (edificação por edificação, multiplicada por uma constante nacional)
seria pior do que declarar a lacuna. Contraria a postura de "nunca inventar valor" do
papel do subagente.

## O que resolveria isto

1. Acesso confirmado e legível por máquina aos termos de licença do
   `mozdata.ine.gov.mz` (regra 1 de §4.0) — reclassificaria o catálogo mozdata de "A
   condicional" para A definitivo, o que abriria a tabulação de tamanho médio do
   domicílio (se de fato publicada nele; não confirmado que exista).
2. Um reprocessador institucional (tipo HDX/OCHA) que publique tamanho médio do
   domicílio por distrito/cidade, análogo ao que o COD-PS já faz para população total.
   Não localizado nesta busca.
3. Alternativa parcial: IPUMS International (nível B) tem tamanho médio do domicílio
   nos microdados de 1997/2007 por `GEO2_MZ`/posto — serviria só como **validação B**,
   nunca para número publicado, e exigiria aprovação de acesso (não obtida nesta rodada).

## Consequência

- `pipeline/00_fetch/` não ganha script de Open Buildings/Microsoft Footprints nesta
  rodada. Se a condição 1 ou 2 acima se resolver, reabrir este ADR antes de construir o
  fetch.
- `data/provenance_parts/demografia_fase2.md` registra esta decisão.
- Nenhuma linha "domicílios" aparece em `data/processed/stats_by_year_by_unit.csv` até
  este ADR ser superado.


---

## Adendo do orquestrador — emenda de 2026-09-08

Reprovação do portão da Fase 2, motivo 2: **duas passagens deste ADR ficaram factualmente
falsas no mesmo dia em que foi escrito.**

O texto dizia "**não baixar Open Buildings/Microsoft Footprints ainda**" e "`pipeline/00_fetch/`
não ganha script de Open Buildings/Microsoft Footprints nesta rodada". Mas a frente de §5.2,
rodando em paralelo, **baixou o Open Buildings**: `pipeline/00_fetch/fetch_open_buildings.py`
produziu `data/raw/open_buildings_v3_aoi.csv` com 268.942 edificações, consumido por
`pipeline/02_metrics/edificacoes.py` para a densidade de edificações e a regularidade da
malha, que §5.2 pede.

As duas frentes decidiram sobre o mesmo dado sem se ver — **erro de delegação do
orquestrador**, o mesmo que produziu a colisão de escrita registrada em
`ORCHESTRATION_LOG.md` 2-01.

**O que muda e o que não muda:**

- **A decisão de fundo permanece válida e não é reaberta.** O motivo para não construir o
  produto "domicílios" nunca foi o custo de download do numerador — foi a **ausência de
  denominador**: o tamanho médio do domicílio não tem fonte de nível A nem B para Tete e
  Moatize. Uma razão herda o nível do pior dos seus termos, e o produto sairia carimbado C
  antes de qualquer processamento.
- **O argumento acessório sai.** A frase sobre custo de download não sustenta nada e estava
  errada de fato: o recorte pela AOI tem 66 MB, não múltiplos GB, e já está espelhado com
  `.sha256` e `.meta.json`.
- **O Open Buildings tem uso legítimo e já em produção**, para densidade de edificações e
  regularidade da malha (§5.2). Isso é diferente de usá-lo como numerador de um produto de
  domicílios, que continua barrado.

**Condição de reabertura, inalterada:** localizar tamanho médio do domicílio em nível A ou B
para as unidades do estudo. O numerador deixou de ser obstáculo — o denominador continua sendo.
