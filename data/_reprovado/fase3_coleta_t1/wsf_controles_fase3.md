# data/provenance_parts/wsf_controles_fase3.md

Proveniência de WSF Evolution para capitais de controle — série de forma urbana (§5.2, §5.4).

## WSF Evolution — Tiles para 5 Capitais de Controle

**Status:** PENDENTE — coleta em progresso

| Atributo | Valor |
|----------|-------|
| **URL de acesso** | https://geoservice.dlr.de/web/datasets/wsf_evo |
| **URL de download** | https://download.geoservice.dlr.de/WSF_EVO/ |
| **Produtora** | DLR (German Aerospace Center) |
| **Resolução espacial** | 30 m |
| **Resolução temporal** | Anual, 1985–2015 |
| **Anos de interesse** | 2000, 2005, 2010, 2015 (anos-âncora de §2) |
| **Âmbito geográfico** | 5 tiles: S16E34, S20E36, S22E32, S24E34, S28E32 (caps. de controle) |
| **Tipo de dado** | Raster, valor = ano de detecção (1985–2015) ou 0 (sem dados), banda única |
| **Método de acesso** | HTTP GET direto; servidor ativo (acesso confirmado via curl em 2026-09-07) |
| **Tamanho estimado** | ~20–30 MB por tile GeoTIFF |
| **Licença** | CC-BY-4.0 |
| **Citação** | Marconcini, M., Metz-Marconcini, A., Üreyen, S., Pophillat, M., Bachmann, M., Zeidler, J., Esch, T., Gorelick, N., Kakarla, A., Paganini, M., & Antropov, G. (2021). "Outlining where humans live — The World Settlement Footprint 2015." Scientific Data 7, 242. https://doi.org/10.1038/s41597-020-00580-5 |
| **Data de verificação de acesso** | 2026-09-07 |
| **Status de download** | ⚠ Pendente; servidor ativo, método de download a confirmar (direto HTTP vs. FTP). |
| **Script de coleta** | Planejado em `pipeline/00_fetch/fetch_wsf_evolution_tiles.py` |

### Tiles por Capital

1. **Chimoio (S22E32)**: -19.14°S, 33.48°E — Manica province, centro-oeste
2. **Quelimane (S20E36)**: -17.88°S, 36.89°E — Zambézia province, costa centro
3. **Lichinga (S16E34)**: -13.30°S, 35.25°E — Niassa province, norte (contraste clima árido)
4. **Xai-Xai (S28E32)**: -25.04°S, 33.64°E — Gaza province, sul (crescimento moderado)
5. **Inhambane (S24E34)**: -22.78°S, 34.57°E — Inhambane province, sul (estagnação esperada)

### Uso Metodológico

- **Série 2000–2015** (não ultrapassa 2015 em WSF Evolution): baseline pré-VIIRS
- **Validação de área construída**: complementa Landsat/Sentinel da Fase 1
- **Comparação entre treated (Tete) e controls**: diferenciais de expansão urbana
- **Teste de tendência paralela** (§5.4): trajetórias pré-2005 devem ser similares

