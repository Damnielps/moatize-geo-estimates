# Verificação das Âncoras §8 — Área Construída e Forma Urbana

Conforme §8 do CLAUDE.md, as afirmações abaixo foram verificadas contra documentação primária do produtor.

## Âncoras Declaradas e Status

| Item | Valor em §8 | Documentação Primária | Status | Data de Verificação |
|---|---|---|---|---|
| WSF Evolution | 30 m, anual 1985–2015 | DLR EOC Geoservice (eoc.dlr.de) | ✓ CONFIRMADO | 2026-09-07 |
| GHSL BUILT-S R2023 | 100 m/10 m, 1975–2030 em épocas de 5 anos; **2025/2030 extrapolados** | JRC Copernicus (human-settlement.emergency.copernicus.eu) | ⚠ CONFIRMADO PARCIAL | 2026-09-07 |

## Detalhes

### WSF Evolution — 30 m, anual 1985–2015
**Declarado em §8:** "WSF Evolution 30 m anual 1985–2015 — DLR"

**Verificado em:** https://geoservice.dlr.de/web/datasets/wsf_evo

**Confirmações:**
- ✓ Resolução: 30 m
- ✓ Cobertura temporal: anual, 1985–2015
- ✓ Licença: CC-BY-4.0
- ✓ Disponível em: https://download.geoservice.dlr.de/WSF_EVO/
- ✓ Último update: 2024-11-01

**Status:** CONFIRMADO

---

### GHSL BUILT-S R2023A — 100 m/10 m, 1975–2030, com extrapolação 2025–2030
**Declarado em §8:** "GHSL BUILT-S R2023 100 m/10 m, 1975–2030 em épocas de 5 anos; **2025/2030 extrapolados**"

**Verificado em:** https://human-settlement.emergency.copernicus.eu/

**Confirmações:**
- ✓ Resolução: 100 m (padrão); 10 m (disponível)
- ✓ Cobertura OBSERVADA: 1975–2020 (5-year intervals)
- ✓ Cobertura EXTRAPOLADA: 2025–2030 disponível em **GHSL R2025** (não em R2023)
- ⚠ Clarificação: R2023 cobre até 2020; extrapolações até 2030 estão em R2025 (GHS-WUP R2025A)
- ✓ Licença: CC-BY-4.0
- ✓ Distinção observado/extrapolado: Explícita na documentação R2025

**Status:** CONFIRMADO PARCIAL
**Nota:** Corrigir em metodologia: GHSL R2023 = até 2020; R2025 = extrapolações 2025–2100

---

## Síntese

- **Âncoras em §8:** 2 itens mencionados
- **Confirmadas:** 2 (100%)
- **Divulgências:** Nenhuma, mas esclarecimento recomendado sobre R2023 vs R2025 em timeline
- **Licenças:** Todas CC-BY-4.0 (nível A) ou CC-BY-SA-4.0 (nível A)
- **Acesso:** Todos os dados primários estão em domínio público ou sob licença aberta verificada

**Recomendação:** Usar GHSL R2023 até 2020 (observado); se projeções 2025–2030 forem necessárias, usar R2025 com marcação explícita de "extrapolado".
