# Decisões — preparação de dados web (Fase 4, primeira tarefa)

Gerado por `pipeline/05_app/build_web_assets.py`. Este arquivo é escrito à mão (é
documentação de decisão, não número derivado); os números que ele cita vêm de
`manifest.json`, gerado sem intervenção manual. Alvo do Makefile: `make app-data`.

## Os dois bloqueios e a causa raiz

`data/processed/imagery/*.geojson` (367 MB / 49 arquivos) não estava inchado por
complexidade vetorial: a maioria das camadas já chega dissolvida da classificação
upstream (`urbano_2025` tem 622 feições para 43,1 km², não um polígono por pixel de
30 m). O inchaço vinha de (a) coordenadas UTM gravadas com ~15 dígitos significativos —
precisão de nanômetro sobre um pixel de 30 m — e (b) vértices de "escada" herdados da
poligonização do raster. **Bloqueio 2** (projeção) era ortogonal: coordenadas UTM cruas
com um membro `crs` que a maior parte das bibliotecas web ignora.

## Decisões

1. **Formato de saída: GeoJSON RFC 7946 (WGS84, sem membro `crs`), minificado**, não
   PMTiles/tippecanoe. Nenhuma dessas ferramentas está no `uv.lock`; introduzi-las
   quebraria a garantia de `docs/ADR/0002` (nenhum utilitário de linha de comando fora
   do gerenciador de dependências) e adicionaria um binário à cadeia de reprodução só
   para resolver um problema que já tinha causa identificada e corrigível com
   `shapely`/`geopandas`, já travados. Texto plano também mantém os artefatos
   auditáveis por `git diff`, o que PMTiles (binário) não permite. Se uma camada futura
   crescer além do que GeoJSON simplificado aguenta, PMTiles é o próximo degrau — não
   foi necessário aqui.
2. **Precisão de coordenada: 6 casas decimais (~0,11 m no equador).** Muito abaixo da
   resolução do pixel (30 m); não introduz erro mensurável, só remove dígitos sem
   informação.
3. **Tolerância de simplificação geométrica: adaptativa por camada×ano, teto de erro de
   área declarado em `config/tolerances.yaml → app_geometria_simplificacao`
   (1 %, conforme pedido pelo orquestrador).** Candidatos testados em ordem decrescente:
   15, 10, 5, 2, 1, 0,5, 0,1, 0 m (em EPSG:32736); escolhida a maior tolerância cujo erro
   de área medido fica dentro do teto. **Erro medido em todos os 31 arquivos poligonais
   publicados: 0,0000 %** — a tolerância de 15 m (metade de um pixel) nunca alterou a
   área de nenhuma camada em nenhum ano além da precisão reportada (6 casas). O número
   por arquivo está em `manifest.json → camadas.<nome>.erro_area_pct`; nenhum ficou acima
   de 0 %.
4. **`vegetacao` e `solo_exposto` ficam fora do app** (12 arquivos, ~104 MB na origem).
   Nenhuma funcionalidade de §6 as usa como camada de mapa (cor-verdadeira, classificação
   em 3 camadas [`urbano`/`reassentamento`/`industrial`], produtos de referência
   WSF/GHSL, camada de agricultura urbana, Zambeze — nenhuma é `vegetacao` nem
   `solo_exposto`). Além de fora de escopo, são as duas camadas com a instabilidade
   diagnosticada por `docs/ADR/0013` item 3 (razão de área entre anos-âncora de fator 32
   e 41 — limiar de rótulo absoluto sobre paisagem não estacionária, não sinal real).
   Publicá-las pagaria banda por uma camada instável e não pedida. Permanecem intocadas
   em `data/processed/imagery/` para o artigo. Registradas no manifesto como
   `"status": "excluida_do_app"` com o motivo — nunca omitidas silenciosamente.
5. **`cultivo_sequeiro` vira grade regular de 1000 m, não polígono.** É a camada maior
   (até 37 MB/ano) e a menos defensável (`docs/ADR/0012`: acurácia do usuário **0,000**,
   n=8/12, único ano validado; Jaccard ~0 contra GLAD/WorldCover em todos os anos). Ela
   também não se beneficia de simplificação de vértice nem de dissolução: testado, a
   união de todos os 42 307 polígonos de `cultivo_sequeiro_2025` preserva as 42 307
   partes — são pixels dispersos, sem adjacência a fundir (67 % das feições já são um
   único pixel isolado). A grade de 1 km (~9 × 9 células por km², alinhada à origem dos
   dados) reduz ~20-42 mil feições/ano para ~2000-2400 células, cada uma carregando a
   **soma exata** da área original dos pixels candidatos dentro dela
   (`area_km2`) e a fração de cobertura da célula (`fracao_cobertura_celula`). Isso é
   generalização deliberada — coerente com o status de "candidata, não confirmada" da
   camada — não falsa precisão. **Erro de área agregada por ano: 0,0000 %** (a soma é
   exata; só a localização dentro da célula de 1 km é perdida, e isso é o ponto).
   `cultivo_irrigado` (mais defensável: acurácia do usuário 0,556, IC95 ±0,344) mantém
   representação poligonal completa.
6. **A comissão de `urbano` (ADR 0009) e a fração herdada pela catraca R2 (ADR 0013)
   entram no `manifest.json`, por ano, lidas de `acuracia_por_ano.csv` e
   `causal/decomposicao_permanencia_urbano.csv`** — não em cada uma das 622+ feições
   (bloat) nem digitadas à mão. O mesmo vale para `industrial`/`reassentamento`
   (fração herdada de `pegada_por_ano.csv`; ADR 0013 item 5 chega a 68,6 % para
   `reassentamento` em 2020 — R2 pode esconder abandono). O tooltip de proveniência da
   Fase 4 seguinte consulta este manifesto por `camada`+`ano`, não números embutidos no
   código do app.
7. **Cintilação do slider temporal (churn de pixel 31–54 % entre anos-âncora
   consecutivos, ADR 0013 item 2): decisão de dado, para a Fase 4 seguinte implementar.**
   O app **não deve interpolar/morfar geometria entre anos** — animar um "deslocamento"
   que é ruído de classificação seria fazer o mapa mentir com movimento, exatamente o que
   a tarefa pediu para evitar. Troca de ano é corte discreto (ou, no máximo, crossfade de
   opacidade da camada inteira, nunca tween de vértice). `manifest.json →
   churn_pares_temporais` carrega o Jaccard/churn por par de anos consecutivos e por
   classe (rótulo bruto do RF, EXPERIMENTAL conforme o próprio CSV de origem) para a UI
   exibir esse número toda vez que o ano muda, em vez de escondê-lo atrás de uma
   transição suave. A série `urbano` publicada também é não-decrescente por construção
   (regra R2): nenhum elemento de UI pode implicar contração dela sem o aviso do item 6.

## O que fica fora desta entrega

- Rasters `*_30m_32736.tif` (compostos, `construido_*`) não foram tocados nem
  retilhados/reamostrados — os dois bloqueios registrados eram de GeoJSON. Servir os
  COGs como tiles raster (PNG/WebP pré-renderizados) é trabalho da Fase 4 seguinte
  quando o mapa de cor-verdadeira e o swipe contra WSF/GHSL forem implementados.
- Camadas fixas de §6 (limites COD-AB, fichas de povoados de reassentamento) ainda não
  estão em `data/processed/imagery/` — nada a preparar aqui; ficam para quando esses
  artefatos existirem.

## Atualização (Fase 4, segunda tarefa) — topônimos, vias e ferrovia

`osm_lugares_aoi.geojson` (23 feições), `osm_vias_aoi.geojson` (219) e
`osm_ferrovia_aoi.geojson` (57) já chegaram de `data/raw/` em EPSG:4326, sem membro `crs`,
nível A (ODbL, ver `data/LICENSES.md`, linha "OpenStreetMap (Geofabrik Moçambique)"). O
script só arredonda coordenada a 6 casas e minifica — **sem reprojeção** (já estão em
WGS84) e **sem simplificação geométrica**: nenhuma das três tem volume ou complexidade de
vértice (a maior, vias, tem 219 feições/150 KB) que justifique o mesmo tratamento adaptativo
aplicado às camadas classificadas. Publicadas como `imagery/osm_lugares.geojson`,
`imagery/osm_vias.geojson`, `imagery/osm_ferrovia.geojson`, registradas em
`manifest.json → camadas_contexto` com fonte, licença e atribuição exigida
(`© OpenStreetMap contributors`) — não misturadas com `manifest.json → camadas`, que é o
esquema das camadas classificadas com caveat de acurácia/permanência (não aplicável a
dado de referência OSM).
