# WorldPop / GRID3 — fragmento de proveniência (Vila de Moatize, população)

Objetivo: estimar população da Vila de Moatize (não publicada em nenhuma fonte; COD-PS só cobre distrito).
Recorte por janela (rasterio/vsicurl) na AOI de `config/study.yaml`, sem espelhar o país inteiro.

| Arquivo | URL | Data de acesso | Licença | Citação | Resolução/nível geográfico | Ano | Soma pop. na AOI |
|---|---|---|---|---|---|---|---|
| data/raw/grid3_moz_pop_v1_1_2020_100m_aoi.tif | https://wopr.worldpop.org/download/237 (catalogado em https://data.humdata.org/dataset/gridded-population-estimates-for-mozambique-2017-census-v1-1) | 2026-09-09 | CC BY 4.0 | Bondarenko M, Jones P, Leasure D, Lazar AN, Tatem AJ. 2020. Census disaggregated gridded population estimates for Mozambique (2017), version 1.1. WorldPop, University of Southampton. doi:10.5258/SOTON/WP00672 | ~100m grade (3 arc-sec), recorte AOI (33.50-34.10E, -16.35 a -16.00S), EPSG:4326 | calibrado ao Censo 2017 (nome de arquivo mantém rótulo "2020" pedido na tarefa, mas o dado v1.1 não tem versão 2020; ver nota de método no .meta.json) | 400.619 |
| worldpop_moz_pop_2000_100m_aoi.tif -- **NÃO GERADO** | https://data.worldpop.org/GIS/Population/Global_2000_2020/2000/MOZ/moz_ppp_2000.tif | tentativa 2026-09-09, não concluída | CC BY 4.0 | WorldPop (www.worldpop.org). Mozambique 100m Population, 2000 (unconstrained). doi:10.5258/SOTON/WP00645 | ~100m grade, AOI (não recortado) | 2000 | N/A -- ver motivo de falha abaixo |
| worldpop_moz_pop_2005_100m_aoi.tif -- **NÃO GERADO** | https://data.worldpop.org/GIS/Population/Global_2000_2020/2005/MOZ/moz_ppp_2005.tif | tentativa 2026-09-09, não concluída | CC BY 4.0 | WorldPop (www.worldpop.org). Mozambique 100m Population, 2005 (unconstrained). doi:10.5258/SOTON/WP00645 | ~100m grade, AOI (não recortado) | 2005 | N/A -- ver motivo de falha abaixo |
| worldpop_moz_pop_2010_100m_aoi.tif -- **NÃO GERADO** | https://data.worldpop.org/GIS/Population/Global_2000_2020/2010/MOZ/moz_ppp_2010.tif | tentativa 2026-09-09, não concluída | CC BY 4.0 | WorldPop (www.worldpop.org). Mozambique 100m Population, 2010 (unconstrained). doi:10.5258/SOTON/WP00645 | ~100m grade, AOI (não recortado) | 2010 | N/A -- ver motivo de falha abaixo |
| worldpop_moz_pop_2015_100m_aoi.tif -- **NÃO GERADO** | https://data.worldpop.org/GIS/Population/Global_2015_2030/R2024B/2015/MOZ/v1/100m/constrained/moz_pop_2015_CN_100m_R2024B_v1.tif | tentativa 2026-09-09, não concluída | CC BY 4.0 | WorldPop (www.worldpop.org). Mozambique 100m Population (constrained, R2024B), 2015. | ~100m grade, AOI (não recortado) | 2015 | N/A -- ver motivo de falha abaixo |
| worldpop_moz_pop_2020_100m_aoi.tif -- **NÃO GERADO** | https://data.worldpop.org/GIS/Population/Global_2015_2030/R2024B/2020/MOZ/v1/100m/constrained/moz_pop_2020_CN_100m_R2024B_v1.tif | tentativa 2026-09-09, não concluída | CC BY 4.0 | WorldPop (www.worldpop.org). Mozambique 100m Population (constrained, R2024B), 2020. | ~100m grade, AOI (não recortado) | 2020 | N/A -- ver motivo de falha abaixo |

## Método de recorte adotado (GRID3, bem-sucedido)

Leitura completa do mosaico nacional (servidor `wopr.worldpop.org` não honra `Range`),
recorte via `rasterio.windows.from_bounds` à AOI (33.50-34.10E, -16.35 a -16.00S,
EPSG:4326), arquivo nacional descartado. Nenhum arquivo de país inteiro foi espelhado
em `data/raw/`.

## Escolha de produto WorldPop (constrained vs. unconstrained)

- **2000, 2005, 2010**: só existe o produto *unconstrained* (Global_2000_2020) --
  o *constrained* do WorldPop (calibrado com pegada de edificações Maxar/Microsoft)
  só cobre 2015 em diante. Não é uma preferência, é a única opção verificada
  (HTTP 200 nas URLs; ausência de diretório `constrained` para esses anos em
  `data.worldpop.org/GIS/Population/Global_2015_2030/R2024B/{2000,2005,2010}/`).
- **2015, 2020**: usado o produto *constrained*, release R2024B, calibração ajustada
  por UN (`UNadj`), por ser mais preciso em área urbana (restringe a população a
  pixels com pegada de edificações). Confirmado disponível via listagem de diretório
  em `data.worldpop.org/GIS/Population/Global_2015_2030/R2024B/{2015,2020}/MOZ/v1/100m/constrained/`.
- Calibração censitária: WorldPop unconstrained e constrained (R2024B) são calibrados
  contra projeções da ONU/censo nacional (não contra o Censo 2017 de Moçambique
  especificamente para todos os anos -- ver `MOZ_population_v1_1_README.pdf` do GRID3
  para a calibração específica ao Censo 2017 de Moçambique, que é o único produto
  desta lista calibrado diretamente ao censo nacional).

## Falha de coleta -- WorldPop Population Counts (2000, 2005, 2010, 2015, 2020): NÃO OBTIDOS NESTA SESSÃO

Todas as 5 URLs foram verificadas como válidas (`curl -I` retorna HTTP 200, tipo
`image/tiff`, `Content-Length` correto: 446.768.688 bytes para 2000; 89.821.219 bytes
para 2020 constrained). O download por leitura em janela (`/vsicurl/` + `rasterio`)
falhou com o erro do GDAL `"Range downloading not supported by this server!"` --
confirmado de forma independente: `curl -r 0-1023` (pedido de 1 KB) contra
`data.worldpop.org` retornou o corpo completo (HTTP 200, não 206), isto é, o
servidor anuncia `Accept-Ranges: bytes` no cabeçalho mas não honra `Range` em `GET`.

Diante disso, a única rota possível é baixar o mosaico nacional inteiro (444-446 MB
para os produtos *unconstrained* 2000/2005/2010; ~90-93 MB para os *constrained*
2015/2020) e recortar localmente -- a mesma estratégia usada com sucesso para o GRID3.
Três tentativas de download completo (`curl`, sem paralelismo na tentativa final)
mediram taxas de transferência de 11,6 KB/s a ~70 KB/s (variável, possivelmente
throttling do lado do servidor). Nessas taxas, o tempo projetado de download é de
25 a 130 minutos por arquivo *constrained* e de 1,8 a 8 horas por arquivo
*unconstrained* -- inviável dentro do orçamento desta sessão de coleta.

**Nenhum dado foi inventado.** Os 5 arquivos `worldpop_moz_pop_{ano}_100m_aoi.tif`
permanecem ausentes de `data/raw/`; nenhum `.sha256` ou `.meta.json` foi gravado para
eles (regra: nunca gravar sidecar de arquivo que não existe). `pipeline/00_fetch/fetch_worldpop_grid3.py`
foi corrigido (URL do GRID3 estava morta -- 404; adicionado suporte aos 5 anos WorldPop)
e é idempotente: uma nova execução, com mais tempo ou banda melhor, retoma de onde
parou (verifica hash antes de baixar) e completa os 5 arquivos que faltam.

