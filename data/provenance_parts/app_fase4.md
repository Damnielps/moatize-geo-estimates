## Fase 4 — artefatos do app (`data/processed/app/` e `app/src/content/`)

### `data/processed/app/imagery/` — camadas para a web

- **Gerado por:** `pipeline/05_app/build_web_assets.py`, alvo `app-data` do Makefile.
- **Selo:** derivado de `data/processed/imagery/`; nenhum dado novo é medido.
- **Nível da fonte:** A (deriva apenas de `data/processed/`).
- **Transformações, todas declaradas em `DECISOES.md` e `manifest.json` locais:**
  reprojeção EPSG:32736 → EPSG:4326 (RFC 7946, sem membro `crs`); precisão de coordenada
  truncada a 6 decimais (~0,1 m); simplificação Douglas-Peucker adaptativa em EPSG:32736,
  com tolerância escolhida por busca gulosa e **teto de 1 % de erro de área** declarado em
  `config/tolerances.yaml → app_geometria_simplificacao`.
- **Erro de área medido, arquivo a arquivo: 0,0000 %.** Conferido de forma independente
  pelo orquestrador comparando a área original em EPSG:32736 com a versão web reprojetada
  de volta: diferença de **+0,0004 % a −0,0007 %**, contagem de feições idêntica.
- **Volume:** 367 MB → 25 MB. O inchaço era **precisão de coordenada**, não complexidade
  geométrica — 15 dígitos por número em UTM.
- **`cultivo_sequeiro` é entregue como grade de 1 km**, não como 42 mil polígonos. Não é
  economia de bytes: com acurácia do usuário 0,000 (`docs/ADR/0012`), polígono comunica
  "objeto detectado" e grade comunica "candidato agregado". A forma da representação passa
  a coincidir com a confiança do dado.
- **`vegetacao` e `solo_exposto` excluídos:** não são camadas de mapa de §6 e carregam a
  instabilidade de 32× a 41× de `docs/ADR/0013`.

### `app/src/content/metodologia.json` — página de metodologia

- **Gerado por:** `pipeline/05_app/gerar_metodologia.py`, com carimbo `gerado_por`.
- **Fontes:** `PROVENANCE.md`, `data/DATA_AUDIT.md`, `docs/ADR/*` e **`uv.lock`**.
- **Nunca redigido à mão** (§6-A). As versões de biblioteca são extraídas do lockfile;
  `pipeline/tests/test_transparencia_metodologica.py` reprova versão divergente.

### Decisão de animação temporal

O slider faz **troca dura de ano ou crossfade de opacidade, nunca interpolação de
geometria**. A identidade pixel a pixel de `urbano` troca 31 % a 54 % entre anos-âncora
(`docs/ADR/0013`): animar isso exibiria instabilidade de classificação como movimento no
terreno, e movimento persuade mais que número.

### Ressalvas que o app exibe onde o número aparece, não em página separada

Comissão de `urbano` (37,5 %–71,4 %, com **IC95 de ±0,20 e prevalência de 0,5–1,9 %**, e a
nota de que **nenhum dos 15 pares de anos-âncora tem IC95 sem sobreposição** — a variação
entre anos não é distinguível de ruído); catraca R2 e incapacidade de detectar contração;
churn de 31 %–54 % junto à tipologia e à matriz de transição; piso de inferência
p = 1/6 ≈ 0,167 ao lado de qualquer p; veredito CONTRAFACTUAL NÃO SUSTENTADO nas quatro
quebras; proibição de atribuir a queda de luz de 2022 à mina (`docs/ADR/0015`).

### O que §6 pede e o app NÃO entrega, declarado em vez de simulado

- **Anéis periurbanos por ano e modo "transições":** o dado não existe
  (`logit_conversao_status.csv` = NÃO DETERMINÁVEL). O app declara a ausência no painel de
  camadas em vez de desenhar geometria plausível.
- **Swipe com WSF/GHSL:** essas camadas não foram preparadas para consumo web.
