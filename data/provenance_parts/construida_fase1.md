# Proveniência — Fase 1: WSF Evolution (fragmento novo, complementa construida.md)

`construida.md` está fechado (Fase 0'). Este fragmento cobre exclusivamente o
WSF Evolution (DLR), que passou a caminho crítico pelo ADR 0003.

## Fonte

- **Produto:** World Settlement Footprint (WSF) Evolution — Landsat-5/-7 — Global.
- **Página do produtor:** https://geoservice.dlr.de/web/datasets/wsf_evo (verificada
  2026-09-07, HTTP 200).
- **Portal de download:** https://download.geoservice.dlr.de/WSF_EVO/ — acesso anônimo
  confirmado (sem login/cadastro, HTTP 200).
- **Índice de tiles** (não documentado publicamente; localizado por engenharia reversa
  do `mainScript.js` do portal): https://download.geoservice.dlr.de/WSF_EVO/grid.geojson
  — GeoJSON com 5138 features globais, grade de 2°x2°, cada feature trazendo
  `properties.Download` (URL do `.tif`), `.filename`, `.md5sum`, `.filesize`, `.id`
  (`"<lon0>_<lat0>"`, canto SW).
- **Tiles que cobrem a AOI** (`config/study.yaml`, bbox 33.50–34.10 E / -16.35–-16.00 S):
  id do produtor `"32_-18"` e `"34_-18"` — derivados via `tile_sw_corners(aoi, 2.0)`,
  nunca fixados no código. Gravados como `data/raw/wsf_evolution_S18E032.tif` e
  `wsf_evolution_S18E034.tif` (convenção hemisférica, para compatibilizar com o
  contrato de cobertura de AOI que agrupa tiles pelo prefixo antes de `_S`/`_N`).
- **Resolução:** 30 m (confirmado por rasterio: `res = 0.0002695°` ≈ 30 m).
- **Anos cobertos:** 1985–2015, anual. Valor de pixel = **ano estimado de primeira
  detecção do assentamento**; 0 = sem dado — confirmado na aba "Abstract" da página do
  produtor, não presumido; confirmado também empiricamente por rasterio: valores únicos
  no intervalo [0, 2015] em ambos os tiles.
- **Selo:** `observado` (máscara classificada a partir de Landsat-5/7, não modelo).
- **Licença:** CC BY 4.0 — texto em https://creativecommons.org/licenses/by/4.0/,
  declarado na aba "License" da página de download (bloco
  `dcat-ap.de/def/licenses/cc-by/4.0`). Aviso adicional do produtor: "DLR not liable for
  damage resulting from use" (isenção de responsabilidade, não restringe uso/redistribuição).
- **Citação exigida:** Marconcini, M., Metz-Marconcini, A., Esch, T., Gorelick, N. (2021).
  "Understanding Current Trends in Global Urbanisation - The World Settlement Footprint
  Suite." GI_Forum 2021, Issue 1, p. 33-38. DOI: 10.1553/giscience2021_01_s33.
- **Nível:** A (licença localizável no site do produtor, acesso anônimo, uso e
  redistribuição permitidos sob CC BY 4.0). Confirma o pressuposto do ADR 0003.

## Arquivos baixados

| Arquivo | id do produtor | Data de acesso | Tamanho (bytes) | MD5 confere |
|---|---|---|---|---|
| data/raw/wsf_evolution_S18E032.tif | 32_-18 | 2026-09-07T23:34:23Z | 1.554.597 | sim (84daed72425b41fd4250ac6449aeabfe) |
| data/raw/wsf_evolution_S18E034.tif | 34_-18 | 2026-09-07T23:34:25Z | 1.953.451 | sim (c35bf468b65b86de3074e6888c6f7e41) |

## Verificação com rasterio

- CRS: EPSG:4326 (ambos os tiles).
- Bounds (união): 31,9898°E–36,0101°E / -18,0101°S–-15,9899°S — cobre a AOI inteira
  (33,50–34,10 E / -16,35–-16,00 S) com folga.
- Resolução: 0,00026949458523585647° por pixel ≈ 30 m no equador (compatível com o
  30 m declarado).
- Shape: 7496×7497 pixels por tile.
- Valores de pixel: inteiros em [0, 2015]. Tile S18E032 tem 32 valores distintos, tile
  S18E034 tem 30 — consistente com "ano de detecção, 0 = sem dado" (não um valor
  contínuo nem uma máscara binária).
- Cobertura da AOI: **confirmada** — os dois tiles juntos cobrem o bbox inteiro da AOI;
  nenhum canto da AOI fica fora de ambos.

## Notas

- `data/interim/wsf_evo_grid.geojson` é apenas um índice de URLs (cache do grid do
  produtor), não um espelho de dado nível A: não recebe `.sha256`/`.meta.json` porque
  não é ele próprio um artefato citável — é reconstituível a qualquer momento a partir de
  `GRID_URL` em `pipeline/00_fetch/fetch_wsf_evolution.py`.
- O portal DLR retorna URLs de download com barra dupla (`.../files//WSFevolution_...tif`);
  isso é do próprio produtor, mantido como está (funciona, resolvido pelo servidor).
- Ambiente de execução: o host `download.geoservice.dlr.de` encadeia até a
  HARICA TLS RSA Root CA 2021, ausente do cafile default do OpenSSL usado pelo
  interpretador Python deste ambiente (embora presente no bundle do `certifi`). O
  script usa `certifi.where()` como cafile quando disponível — sem isso o handshake
  TLS falhava com "self-signed certificate in certificate chain" mesmo a fonte sendo
  legítima. Registrado aqui para não ser confundido com problema da fonte.
