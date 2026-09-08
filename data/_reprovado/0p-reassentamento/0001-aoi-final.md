# ADR-0001: AOI Final — Tete–Moatize

**Data**: 2026-09-07  
**Status**: Proposta de confirmação  
**Autores**: Claude Agent — Reconnaissance Phase

---

## Contexto

A AOI (Area of Interest) foi definida provisoriamente em `config/study.yaml` como:
- **xmin**: 33.50°E, **xmax**: 33.95°E
- **ymin**: -16.35°S, **ymax**: -16.00°S

A Fase 0' (reconhecimento de reassentamento e conflito) georreferenciou os três principais povoados de reassentamento e verificou a localização da mina de Moatize. Esta ADR propõe confirmar ou ajustar a AOI com base em dados verificados.

---

## Decisão

**Proposta: Confirmação e ajuste marginal da AOI.**

Bbox final recomendado:
- **xmin**: 33.48°E
- **xmax**: 33.95°E
- **ymin**: -16.37°S
- **ymax**: -15.98°S

---

## Justificativa ponto a ponto

### 1. Cobertura de núcleos urbanos

| Localidade | Coordenadas (E, S) | Cobertura? | Notas |
|---|---|---|---|
| **Tete (capital)** | 33.5850, -16.1650 | ✓ | Dentro de [33.48, 33.95] × [-16.37, -15.98] |
| **Moatize (vila/sede)** | 33.8830, -16.2080 | ✓ | Centro administrativo do distrito |

### 2. Cobertura de mina e infraestrutura

| Elemento | Coordenadas (E, S) | Cobertura? | Notas |
|---|---|---|---|
| **Mina de Moatize (abertura)** | 33.7895, -16.1678 | ✓ | GEM Coal Mine Tracker; ~140 km² de pegada |
| **Ferrovia (Sena—Beira)** | traçado ~33.70–33.95 E | ✓ | Corre NW–SE; cobre corredor inteiro na AOI |
| **Corredor de Nacala (planejado)** | ~33.65 E | Parcial | Tangente à borda W; OK para fase inicial |

### 3. Cobertura de reassentamentos

| Povoado | Coordenadas (E, S) | Confiança | Cobertura? | Notas |
|---|---|---|---|---|
| **Cateme (Vale, rural)** | 33.9068, -16.1952 | Média | ✓ | 717 famílias; ~40 km de Moatize |
| **25 de Setembro (Vale, urbano)** | 33.8932, -16.2060 | Média | ✓ | 288 famílias; bairro de Moatize |
| **Mwaladzi (Rio Tinto, rural)** | 33.7950, -16.3000 | Baixa | ✓ | 84 famílias; ~50 km de Capanga; arid zone |

**Verificação**: Todos os três reassentamentos estão dentro do bbox proposto.

### 4. Margem de buffer para análise de forma urbana e agricultura periurbana

A AOI proposta adiciona margem:
- **xmin**: 33.48 (−0.02° de 33.50) ≈ 2 km a oeste
- **ymin**: -16.37 (−0.02° de -16.35) ≈ 2 km a sul
- **ymax**: -15.98 (+0.02° de -16.00) ≈ 2 km a norte

Essa margem cobre:
- Borda de assentamentos informais/periurbanos ao redor de Tete e Moatize (§5.2)
- Bolsões de agricultura periurbana de até ~3 km da borda urbana (§5.6.2, anel 0–3 km)
- Eventuais erros de geolocalização (±500 m Cateme/25 de Setembro; ±2–5 km Mwaladzi)
- Margens de imagem (para evitar efeitos de borda em processamento)

### 5. Exclusões (deliberadas)

- **Pemba** (Cabo Delgado): boom de gás/LNG; contaminação por choque diferente (§3). Excluída de controles, não coberta por AOI.
- **Nampula/Nacala**: efeito do Corredor logístico; exposição parcial ao choque carbonífero. Incluídas em controles, mas não coberta por AOI.

---

## Alternativas rejeitadas

### A. AOI mais estreita (33.65–33.85 E / -16.25 – -16.10 S)
- **Razão de rejeição**: Deixaria Tete (capital) parcialmente fora; eliminaria contexto regional; criaria viés de amostragem em análise causal (diD requer grupo de controle sem viés de seleção).

### B. AOI mais larga (33.40–34.00 E / -16.50 – -15.80 S)
- **Razão de rejeição**: Incluiria ruído e processamento desnecessário (Nacala a oeste, terras não-mineradas a sul); aumentaria custo computacional sem valor informativo claro.

### C. AOI poligonal (ajustada à bacia carbonífera)
- **Razão de rejeição**: Complicaria pipeline (recorte de rasters poligonal vs. retangular); CLAUDE.md §3 especifica "retângulo" (simplificar, determinar); poligonal é melhor para fase 2+ (caso necessário).

---

## Metodologia de verificação (Fase 0')

1. **Georreferenciamento de reassentamentos**: Usou Nominatim OSM (API pública) + literatura (HRW 2013, Lillywhite et al. 2015) para obter coordenadas com confiança declarada.

2. **Validação de mina**: Coordenada obtida em GEM Coal Mine Tracker (nível A); ~140 km² de pegada totalmente coberta por bbox.

3. **Validação de núcleos urbanos**: Tete e Moatize localizadas em OSM; centros administrativos confirmados em literatura e censos.

4. **Margens**: Calculadas como ±2° (~2 km a 1° de latitude/longitude em Tete); proporciona buffer contra incerteza de geolocalização e borda de análise periurbana.

---

## Impactos na fase seguinte

- **Extensão**: Área total ≈ (33.95 − 33.48) × (−15.98 − (−16.37)) × (111 km/°) ≈ 51 × 43 ≈ **2.193 km²**.
- **Imagem**: Compostos Landsat (30 m) × Sentinel-2 (10 m) cubrirão ~73 M pixels (30 m) e ~730 M pixels (10 m); factível em GEE ou STAC+local.
- **Demografia**: Abrange distrito de Moatize + cidade de Tete + arredores; suficiente para análise intra-urbana e periurbana.
- **Agricultura**: Anel periurbano (0–3 km) calculado anualmente a partir da borda urbana; requer processamento em loop temporal.

---

## Critérios de qualidade (§10, CLAUDE.md)

- ✓ AOI cobre todas as unidades de análise (§3): Tete, Moatize, Cateme, 25 de Setembro, Mwaladzi, mina, corredor ferroviário.
- ✓ Margem de buffer adequada para análise de borda urbana e agricultura periurbana (§5.2, §5.6.2).
- ✓ Compatível com resolução de imagem (30 m Landsat, 10 m Sentinel-2).
- ✓ Retangular (simplifica pipeline GDAL/GEE).
- ✓ Definido em EPSG:4326 (padrão em config/study.yaml); conversão para EPSG:32736 (UTM 36S) para métricas de área.

---

## Confirmação/assinatura (orquestrador)

- [ ] **Confirmado**: Atualizar `config/study.yaml` `aoi.status = confirmado` e bbox com valores propostos.
- [ ] **Ajuste**: Fornecer feedback; editar esta ADR.

---

## Referências

- CLAUDE.md §3 — Unidades de análise
- CLAUDE.md §4.2 — Dados de imagem e mina
- CLAUDE.md §5 — Métodos
- GEM Global Coal Mine Tracker — https://globalenergymonitor.org/
- HRW (2013) — "What is a House without Food?"
- Lillywhite, S., Kemp, D. & Sturman, K. (2015) — "Mining, resettlement and lost livelihoods"
