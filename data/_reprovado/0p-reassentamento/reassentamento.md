# Proveniência — Dados de Reassentamento e Conflito

## Arquivo: `reassentamentos.geojson`

| Propriedade | Valor |
|---|---|
| **URL** | Compilado de múltiplas fontes (não URL único) |
| **Data de acesso / compilação** | 2026-09-07 |
| **Licença** | CC-BY-NC-ND (HRW 2013) + CC-BY (Lillywhite et al. 2015, ODbL Nominatim) |
| **Citação padrão** | Vide seção "Citações" abaixo |
| **Resolução geográfica** | Ponto (features); EPSG:4326 (WGS84) |
| **Anos cobertos** | Reassentamentos 2009–2010 (Vale); 2012 (Riversdale/Rio Tinto) |
| **Acurácia espacial** | Confiance média (±500 m em Cateme e 25 de Setembro, ±2–5 km em Mwaladzi); vide campo `confianca` em cada feature |

### Features incluídas

#### 1. Cateme (rural, Vale)
- **Coordenadas (EPSG:4326)**: 33.9068°E, -16.1952°S (aproximadas)
- **Número de famílias**: 717 (nov/2009 – abr/2010)
- **Fonte primária**: HRW (2013), p. XX–YY [verificar página exata na versão final]
- **Tipo**: Rural; ~40 km de Moatize; solo pobre; sem acesso a água adequada
- **Confiança**: Média (coordenada via Nominatim OSM; proximidade de Moatize verificada em literatura)

#### 2. 25 de Setembro (urbano, Vale)
- **Coordenadas (EPSG:4326)**: 33.8932°E, -16.2060°S (aproximadas)
- **Número de famílias**: 288 (nov/2009 – abr/2010)
- **Fonte primária**: HRW (2013), p. XX–YY [verificar página exata]
- **Tipo**: Urbano; bairro de Moatize; planejamento semi-formal
- **Confiança**: Média (coordenada via Nominatim OSM + localização urbana em literatura)

#### 3. Mwaladzi (rural, Riversdale/Rio Tinto — Benga)
- **Coordenadas (EPSG:4326)**: 33.7950°E, -16.3000°S (estimadas)
- **Número de famílias**: 84 (inicial); Rio Tinto planejava +388
- **Fonte primária**: Lillywhite, S., Kemp, D. & Sturman, K. (2015), p. XX–YY [verificar página exata]
- **Tipo**: Rural; ~50 km de Capanga; zona árida; sem acesso a água
- **Confiança**: Baixa (coordenada estimada; literatura menciona "~50 km de Capanga" mas não dá coordenada exata)

---

## Citações padrão (por fonte)

### HRW 2013
```bibtex
@report{hrw2013_moatize,
  author = {Human Rights Watch},
  year = {2013},
  title = {What is a House without Food? Mozambique's Coal Mining Boom and Resettlements},
  month = {May},
  day = {23},
  url = {https://www.hrw.org/news/2013/05/23/mozambique-mining-resettlements-disrupt-food-water},
  institution = {Human Rights Watch},
  address = {New York}
}
```

### Lillywhite et al. 2015
```bibtex
@book{lillywhite2015,
  author = {Lillywhite, S. and Kemp, D. and Sturman, K.},
  year = {2015},
  title = {Mining, resettlement and lost livelihoods: Listening to the voices of resettled communities in Mualadzi, Mozambique},
  publisher = {Oxfam},
  address = {Melbourne},
  url = {https://www.csrm.uq.edu.au/publications/mining-resettlement-and-lost-livelihoods}
}
```

### Kirshner & Power 2015
```bibtex
@article{kirshner2015,
  author = {Kirshner, J. and Power, M.},
  year = {2015},
  title = {Mining and extractive urbanism: Postdevelopment in a Mozambican boomtown},
  journal = {Geoforum},
  url = {https://dro.dur.ac.uk/15121}
}
```

---

## Notas de metodologia

1. **Coordenadas**: As coordenadas de Cateme e 25 de Setembro foram obtidas via Nominatim (OSM API). Confianças média e baixa refletem incerteza inerente a geocodificação automática; para análise fina de forma urbana, recomenda-se validação contra imagem e OSM visual.

2. **Mwaladzi**: A coordenada é **estimativa** baseada em descrição literária ("~50 km de Capanga", "zona árida a leste de Capanga"). Sem ponto de referência geográfico exato na literatura, a coordenada deve ser **revalidada** via imagem Sentinel-2 / Landsat ou relatórios de EIA da Riversdale/Rio Tinto (se acessíveis).

3. **Número de famílias**: Valores extraídos de HRW (2013) e Lillywhite et al. (2015). HRW cita 1.365 para Vale (717 Cateme + 288 → 25 de Setembro, total 1.005; diferença de 360 famílias não explicada em leitura rápida — **verificar página exata em HRW 2013 no texto final**).

4. **Anos de reassentamento**: 2009–2010 para Vale (documentado). Riversdale/Rio Tinto — Mwaladzi associado a 2012 (Benga mine opening), mas data exata não verificada em literatura acessível.

---

## Próximas etapas (Fase 1)

- Validar coordenadas de Mwaladzi contra imagem Sentinel-2 (buscar padrão de assentamento disperso novo, ~2012–2013)
- Localizar relatórios de EIA/RAP de Riversdale/Rio Tinto (Benga) para coordenada e número de famílias exato
- Buscar relatório de EIA/RAP da Vale (2007, 2011) em repositórios governamentais mozambicanos ou via UNEP/EISA
- Compilar campo `n_familias` e `ano_reassentamento` para Mwaladzi quando dados estiverem disponíveis
