# Proveniência — GIF animado da mancha urbana (`pipeline/04_figures/gif_mancha.py`)

Fragmento gerado/atualizado manualmente ao lado do script. Consolidado em
`PROVENANCE.md` por `scripts/consolidar_registros.py`. O próprio artefato grava
`.meta.json` ao lado, com hash sha256 de cada insumo — este fragmento resume o que já
está lá, não o substitui.

## Mudança de método (Fase 4b, tarefa A3)

O GIF `paper/figuras/mancha_urbana_2000_2025.gif` deixou de ser gerado por captura de
tela automatizada do app (Chrome headless via Puppeteer, fora do pipeline
reprodutível) e passou a ser gerado deterministicamente por
`pipeline/04_figures/gif_mancha.py`, a partir dos mesmos GeoJSON simplificados que o
app consome (`data/processed/app/imagery/`, ver `manifest.json`). O app deixa de
publicar/usar o GIF em `app/public/media/`; a remoção desse diretório é tarefa do
orquestrador, não deste script.

## Composição

Um quadro por ano-âncora (2000, 2005, 2010, 2015, 2020, 2025): camadas classificadas
`agua`, `cultivo_irrigado`, `urbano`, `industrial`, `reassentamento` (nesta ordem de
empilhamento) + camadas estáticas `varzea`, `osm_vias`, `osm_ferrovia`,
`osm_aerodromo`, `osm_lugares` (topônimos). Excluídas, como no artefato anterior:
`cultivo_sequeiro` (vegetação sazonal não confirmada como cultivo) e
`adensamento_2020_2025` (modelado, ADR 0016 — pergunta distinta desta figura).

Mesmo enquadramento em todos os quadros: bbox da AOI de `config/study.yaml`
(`aoi.bbox`), em EPSG:4326 (CRS de exibição, §11.2.1) — os insumos já nascem nesse CRS.
Correção de aspecto por `1/cos(latitude_média)` (equirretangular), equivalente ao
efeito visual do MapLibre do app nesta escala; nenhuma reprojeção métrica.

Cores por camada replicadas de `app/src/components/MapaTemporal.jsx`
(`CORES_CAMADA`), para que o GIF e o app apresentem a mesma paleta. Estilo de texto,
fundo e paleta de apoio: Sistema Ardósia (`_paleta_ardosia.py`, vendorizado sem
alteração).

Ano em destaque (serifa) em cada quadro; a partir do 2º quadro, texto miúdo com o
churn de `construido` do par de anos consecutivo, lido de
`data/processed/app/imagery/manifest.json` → `churn_pares_temporais` (ADR 0013) — é o
rótulo bruto do classificador, antes de R1/R2, **EXPERIMENTAL**, não substitui nenhum
artefato publicado de área construída; a nota acompanha o número no próprio quadro.
Crédito de fontes no rodapé.

## Fonte tipográfica (corrigido após reprovação no portão, 2026-09-11)

**Defeito encontrado.** A 1ª versão escolhia a fonte pela lista `SERIF`/`SANS` de
`_paleta_ardosia.py`, resolvida por nome contra as fontes do sistema. No macOS de
geração o ano saiu em "Iowan Old Style", que não existe no Docker (`python:3.12-slim`)
nem no runner `ubuntu-latest` do CI: em Linux o GIF sairia com outra fonte e outros
bytes, e o `.meta.json` só declarava determinismo dentro da mesma máquina.

**Correção.** O GIF usa SOMENTE os TTF embutidos no wheel do matplotlib
(`matplotlib/mpl-data/fonts/ttf/DejaVuSerif-Bold.ttf` para o ano,
`DejaVuSans.ttf` para o resto), carregados por caminho (`FontProperties(fname=...)`).
`verificar_fontes()` aborta a geração se qualquer texto visível tiver outra origem.
O `.meta.json` registra caminho relativo e sha256 de cada TTF. `_paleta_ardosia.py`
não foi alterado (é compartilhado).

**Achado registrado, não corrigido (fora do escopo desta tarefa).** O mesmo defeito está
latente em `pipeline/04_figures/mapa_localizacao.py`: usa `fontfamily=SANS`, `SERIF` e
`MONO` de `_paleta_ardosia.py`, resolvidos por nome contra o sistema, e grava PDF (que
embute a fonte resolvida). O `mapa_localizacao.pdf` gerado em macOS e em Linux terá
fontes e bytes diferentes. Correção sugerida: a mesma deste script.

## Determinismo e garantia de reprodução

Fontes de variação eliminadas:
- fonte do sistema: só TTF DejaVu embutidos, por caminho (acima);
- FreeType do sistema: o wheel do matplotlib 3.11.1 embute o próprio
  (`ft2font.__freetype_build_type__ == "local"`, FreeType 2.14.3), versão fixada por
  `uv.lock`;
- `matplotlibrc` do usuário: `rcdefaults()` antes do estilo Ardósia, dentro de
  `rc_context` (não vaza para outros testes);
- backend: `FigureCanvasAgg` explícito, sem pyplot e sem PNG intermediário — o raster
  RGBA sai do buffer do Agg;
- paleta adaptativa: a quantização por median cut por quadro foi trocada por uma
  **paleta fixa de 256 entradas derivada só de constantes** (cores das camadas, Ardósia
  e misturas lineares frente/fundo que o antialiasing produz; sha256 no meta), sem
  dithering. Com paleta adaptativa, 1 pixel diferente pode reordenar a paleta inteira e
  mudar todos os índices; com a fixa, a diferença fica local. Custo medido no quadro
  2015: MAE RGB de quantização 0,65 (median cut: 0,11), máximo 23 de 255 em pixels de
  borda — sem efeito visível.

Garantias declaradas em `.meta.json['reprodutibilidade']`:
- **Mesma plataforma + mesmo `uv.lock`: byte a byte.** Verificado nesta sessão (Darwin
  arm64): duas execuções com o mesmo sha256, e uma terceira idêntica com `MPLCONFIGDIR`
  vazio (cache de fontes reconstruído) e um `matplotlibrc` hostil (monospace, sem
  hinting, antialiasing desligado).
- **Entre plataformas (macOS arm64 × Linux x86_64): tolerância, não byte a byte.** Não
  houve execução em Linux nesta sessão (sem Docker na máquina). Resíduo esperado:
  arredondamento de ponto flutuante nas transformações (FMA/contração, arm64 × x86_64)
  mudando o arredondamento subpixel do Agg em pixels de borda. Tolerância, por quadro,
  sobre os quadros decodificados, só quando o sha256 difere: mesmo nº de quadros,
  tamanho e duração; todos os pixels na paleta fixa; fração de pixels com índice
  diferente ≤ 0,002; MAE RGB ≤ 0,05 (escala 0–255).
- **Calibração da tolerância** (mesma máquina, AOI × (1 + eps), pior quadro):
  eps 1e-15 → idêntico; 1e-12 → fração 5,8e-7; 1e-9 → fração 2,5e-4, MAE 0,0011
  (aprovado); 1e-6 (≈ 0,08 px, ≈ 3,7 m de deslocamento real) → fração 0,081, MAE 0,61
  (**reprovado**). A tolerância aceita ruído numérico várias ordens de grandeza acima de
  1 ulp e reprova deslocamento geométrico real.

sha256 do GIF publicado (Darwin arm64, matplotlib 3.11.1, Pillow 12.3.0):
`71eca7f3dbc4ba6a4e67d9b42dc49ef213d8e0061f6dea21a22d012a0b0280e6`.

A verificação entre plataformas não fica só declarada: o teste
`test_gif_regenerado_confere_com_o_publicado` regenera o GIF num diretório temporário e
aplica `comparar_gifs()`; no CI (`ubuntu-latest`) ele é a verificação efetiva Linux ×
macOS. Na plataforma de geração exige byte a byte.

## Insumos (todos os hashes sha256 no `.meta.json` do artefato)

`data/processed/app/imagery/{urbano,industrial,reassentamento,cultivo_irrigado,agua}_<ano>.geojson`
para cada ano-âncora; `varzea.geojson`, `osm_vias.geojson`, `osm_ferrovia.geojson`,
`osm_lugares.geojson`, `osm_aerodromo.geojson`; `manifest.json` (para o churn do par
temporal).

## Selo e ressalvas

Selo composto (ver `.meta.json['selo']`): `observado` para as camadas classificadas e
para as camadas OSM; `estático` para várzea; o indicador de churn exibido em texto
miúdo é **EXPERIMENTAL** (ADR 0013), não um selo de série publicada.

Ressalvas (embutidas no `.meta.json` e no rodapé do próprio GIF):
1. Corte discreto de fonte de dado por ano-âncora, sem interpolação de geometria entre
   anos (ADR 0013) — a "transição" é troca de camada, não movimento real.
2. Acurácia da camada `urbano` varia por ano (docs/ADR/0009, docs/ADR/0014).
3. Material de apresentação/comunicação — não é figura de resultado do artigo e não
   substitui as figuras de `pipeline/04_figures` com proveniência hash-rastreada.
4. O churn de `construido` por par de anos vem do rótulo bruto do classificador,
   antes de R1/R2 — EXPERIMENTAL.

## Integração

Alvo `figures` do `Makefile` executa `pipeline/04_figures/gif_mancha.py` após
`mapa_localizacao.py` e `fatos_verificados.py`. Teste de contrato:
`pipeline/tests/test_gif_mancha.py` (11 testes: existência, 6 quadros, anos no meta,
selo, ressalvas, hashes de insumo batendo com `data/processed/app/imagery/`, fontes
DejaVu embutidas, tolerância do meta igual à do script, e regeneração comparada ao
publicado). Os insumos estão versionados; o teste roda num clone limpo.

## Paleta de cores passa a vir de `config/paleta_uso_solo.yaml` (Fase 4b, tarefa A3b)

**Mudança.** `CORES_CAMADA` deixou de replicar hex à mão de
`app/src/components/MapaTemporal.jsx` (herança de uma versão do app que já não guarda
cores ali) e passou a ler `config/paleta_uso_solo.yaml` — a mesma fonte única que
`pipeline/05_app/gerar_paleta.py` grava em `app/src/content/paleta_uso_solo.json` para
o app (ADR 0018: legenda ESA WorldCover/FAO LCCS, com adaptações declaradas). Nenhum
hex de classe é escrito no script; cores de contexto (vias, ferrovia, aeródromo,
topônimos, fundo do mapa) vêm da seção `contexto` do mesmo YAML.

**O que mudou no desenho, para bater com o app** (`app/src/lib/camadasBase.js`):
- `reassentamento` e `industrial` (classes `origem: adaptacao`) passaram a levar
  contorno na cor `contorno` do YAML — antes eram preenchimento sólido sem borda.
- `varzea` passou a usar a `opacidade` declarada no YAML (0,25) em vez de uma constante
  fixa no script (0,35).
- A legenda ganhou a linha "Cores: ESA WorldCover (FAO LCCS); adaptações no ADR 0018" e
  um `*` discreto nos rótulos das classes `origem: adaptacao` (industrial,
  reassentamento, várzea).
- `cultivo_sequeiro` e `adensamento_2020_2025` continuam excluídos deste GIF, sem
  mudança.

**Paleta fixa de 256 cores (`paleta_fixa()`).** A troca de paleta trocou também as
cores de mistura usadas para simular o antialiasing do Agg. Com os 2 contornos novos
tratados como qualquer outra "frente" no laço cheio (frente × fundo × 4 alfas +
combinações par a par entre todas as camadas), o total passava de 256 (307–340
conforme a tentativa). Correção: (1) os passos de mistura frente/fundo do laço
principal foram reduzidos de 4 (0,2/0,4/0,6/0,8) para 3 (0,25/0,5/0,75); (2) os
contornos saíram do laço cheio e ganharam um tratamento próprio, mais estreito — cor
pura mais mistura contra o preenchimento da própria classe e contra fundo do
mapa/papel, em 3 alfas (0,3/0,6/0,9) — por serem traços finos, com muito menos pixels
de antialiasing do que um preenchimento. Resultado: exatamente 256 entradas, sem
sobra para preenchimento com a 1ª cor. Verificado com o quadro de 2000 e o de 2025
(inspeção visual): vermelho da mancha orgânica, cinza com contorno da pegada
industrial, azul da água, ciano claro da várzea e rosa do cultivo irrigado batendo com
a legenda ESA WorldCover.

**Insumo novo.** `config/paleta_uso_solo.yaml` entrou em `listar_insumos()` (chave
`paleta_uso_solo_yaml`) com hash sha256 em `.meta.json['hashes_sha256_insumos']`;
`.meta.json['paleta_cores']` registra a fonte, o sha256 do YAML e o ADR 0018.

**Determinismo verificado nesta tarefa.** Duas execuções consecutivas produziram o
mesmo `sha256_gif`
(`ea59ca3cb85177e154faa34f87a53b7c42e6770d45702dbe01a178bdcddee5f0`, Darwin arm64) — a
garantia byte a byte na mesma plataforma se mantém com a nova paleta; a tolerância
entre plataformas e a calibração declaradas acima não foram alteradas por esta tarefa.

**Teste.** `pipeline/tests/test_gif_mancha.py` trocou o contrato "cores replicadas do
app" (nunca chegou a existir como teste automatizado; só como comentário no script) por
`test_cores_do_gif_vem_do_yaml_da_paleta_de_uso_do_solo` — compara `CORES_CAMADA`,
`CONTORNO_CAMADA`, `FUNDO_MAPA`, `OPACIDADE_VARZEA` e `COR_CONTORNO_FANTASMA` do
script byte a byte contra o YAML — e `test_meta_registra_hash_e_adr_da_paleta_de_uso_do_solo`,
que confere `paleta_cores` e o hash do YAML entre os insumos do `.meta.json`. O teste de
regeneração (`test_gif_regenerado_confere_com_o_publicado`) não mudou de contrato, só
passou a exercer o caminho novo.
