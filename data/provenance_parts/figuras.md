# Proveniência — Figuras (`pipeline/04_figures/`)

Fragmento gerado/atualizado manualmente ao lado dos scripts de `pipeline/04_figures/`.
Consolidado em `PROVENANCE.md` por `scripts/consolidar_registros.py`. Cada figura grava
também o seu próprio `.meta.json` ao lado do artefato em `paper/figuras/`, com hash
sha256 de cada insumo — este fragmento resume o que já está lá, não o substitui.

## `mapa_localizacao.py` — mapa de localização de Tete e Moatize

- **Script:** `pipeline/04_figures/mapa_localizacao.py`.
- **Saídas:** `paper/figuras/mapa_localizacao.pdf` (vetorial), `mapa_localizacao.png`
  (300 dpi), `mapa_localizacao.meta.json` (proveniência por artefato, com hash sha256
  de cada insumo, hash de `config/study.yaml`, commit git e selo).
- **Composição:** mapa principal (AOI, ano-âncora 2025) com as três camadas
  classificadas mutuamente exclusivas (`urbano`, `industrial`, `reassentamento`),
  hidrografia (HydroRIVERS v10 África), povoados de reassentamento georreferenciados
  e limites distritais de contexto; encarte 1 (província de Tete, AOI destacada);
  encarte 2 (Moçambique, província de Tete destacada). Barra de escala, seta de norte
  e grade de coordenadas no mapa principal.
- **Insumos (todos nível A, já espelhados):**
  - `data/raw/hdx_cod-ab-moz_admin_boundaries.geojson.zip` — admin0/1/2, selecionados
    por `adm2_pcode`/`adm1_pcode` do esquema **COD-AB** (não COD-PS — ver
    `config/unidades.yaml`, seção `esquemas_pcode`; Cidade de Tete = MZ0501,
    Moatize = MZ0510, província de Tete = MZ05).
  - `data/processed/imagery/{urbano,industrial,reassentamento}_2025.geojson` — saída
    de `pipeline/01_imagery/classificacao.py`, já em EPSG:32736.
  - `data/raw/reassentamentos.geojson` — Cateme e Mwaladzi com ponto georreferenciado;
    "25 de Setembro" com `geometry: null` (não localizado em fonte aberta, não
    inventado — ver `data/provenance_parts/reassentamento.md`).
  - `data/raw/hydrorivers_af_v10.gdb.zip`, camada `HydroRIVERS_v10_af`, recortada à AOI
    por bbox na leitura (`gpd.read_file(..., bbox=...)`).
- **CRS:** mapa principal em EPSG:32736 (UTM 36S, métrica de área, convenção do
  repositório); encartes em EPSG:4326 (só localização/orientação, distorção
  provincial/nacional aceitável porque não há medição nessa escala).
- **Identidade visual:** Sistema Ardósia, aplicado via `pipeline/04_figures/
  _paleta_ardosia.py` — cópia vendorizada e **sem alteração** de
  `ardosia-brand-guidelines/scripts/palette.py` (skill pessoal do autor, fora do
  repositório), para que o pipeline não dependa de um caminho fora do controle de
  versão. Qualquer atualização da paleta normativa precisa ser replicada manualmente
  aqui e registrada em `docs/ADR/`.
- **Honestidade cartográfica (obrigatória, embutida na figura, não só no texto):**
  1. Legenda com advertência textual: a camada `urbano` tem acurácia do usuário
     medida entre 0,286 e 0,625 por ano-âncora (`docs/ADR/0009`) — entre 37,5% e 71,4% do
     que o mapa chama de construído não é. A camada é insumo classificado, não
     cadastro.
  2. Rodapé: a série temporal de área construída (não plotada nesta figura, que é um
     corte único de 2025) é a do WSF Evolution, não a classificação própria
     (`docs/ADR/0008`) — para quem reusar o corte fora de contexto.
  3. Legenda: nota sobre "25 de Setembro" sem geometria localizável, não representada
     no mapa, não inventada.
  Todas as três ressalvas também estão em `mapa_localizacao.meta.json` (`ressalvas`),
  verificadas por `pipeline/tests/test_figuras.py::test_meta_declara_ressalvas_de_honestidade_cartografica`.
- **Determinismo:** layout orçado em polegadas fixas (figura 11×12 in); `savefig.bbox`
  do tema Ardósia (`tight`, recorta por bbox de conteúdo) é explicitamente desligado
  (`plt.rcParams["savefig.bbox"] = None`) para que o tamanho da tela em pixels não
  dependa da métrica de fonte disponível na máquina que renderiza. Sem RNG, sem
  downloads. `pipeline/tests/test_figuras.py::test_script_e_determinístico` roda o
  script duas vezes e compara as dimensões do PNG.
- **Selo:** `observado` — todas as camadas de entrada são classificação/dado
  observado; nenhuma extrapolação.
