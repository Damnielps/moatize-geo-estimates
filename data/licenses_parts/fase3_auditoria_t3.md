# Fase 3 — Auditoria de classificação (auditor-dados, T3)

Classifica as fontes coletadas em `data/licenses_parts/fase3_coleta_t2_licenca.md`
(que registrou "não classificado — cabe ao auditor-dados" em toda linha) e as duas
fontes não obtidas, com evidência HTTP. Verificado via `.meta.json` em `data/raw/`
e página do produtor (Harvard Dataverse), nunca via agregador.

## Correção de autoria — obrigatória, atinge CLAUDE.md §4.4

O item "Harmonized DMSP-VIIRS Nighttime Lights (1992–2018) (Li et al. 2020)" da tabela
§4.4 de `CLAUDE.md` e a linha correspondente em `data/licenses_parts/economicos.md`
descrevem um produto **diferente** do coletado nesta rodada. Confirmado por busca na
página do produtor/paper original (não por agregador):

- **Produto coletado (54 tiles, `viirs_like_li2020_v2_*.tif`)**: autoria **Chen, Z.,
  Yu, B., Yang, C., Zhou, Y., Yao, S., Qian, X., Wang, C., Wu, B., Wu, J.** Paper de
  método: Chen et al. (2021), "An extended time series (2000–2018) of global
  NPP-VIIRS-like nighttime light data from a cross-sensor calibration", *Earth System
  Science Data*, 13, 889–906, DOI **10.5194/essd-13-889-2021**. Dataset hospedado no
  Harvard Dataverse como "The global NPP-VIIRS-like nighttime light data (Version 2)
  for 1992–2025", V10, DOI **10.7910/DVN/YGIVCD**, licença **CC0 1.0** (lida no JSON
  da API do Dataverse — `metadataBlocks.citation.license`, confirmado no `.meta.json`
  de cada tile).
- **Produto descrito em CLAUDE.md §4.4 ("Li et al. 2020")**: Li, X., Zhou, Y., Zhao,
  M., Zhao, X. (2020), "A harmonized global nighttime light dataset 1992–2018",
  *Scientific Data*, 7, 168 — hospedado em figshare, **não** em Harvard Dataverse. É
  um harmonizado DMSP↔VIIRS **distinto**, de outro grupo de autores, com outra
  metodologia de calibração cruzada.
- **Nome de arquivo do coletor é ambíguo por desenho** (`viirs_like_li2020_v2_*`),
  mas o `.meta.json` de cada arquivo já registra a citação correta (Chen/Yu). O nome
  do arquivo não deve ser lido como atribuição de autoria.
- **Ação exigida**: `CLAUDE.md` §4.4 deve ser corrigido para separar as duas linhas —
  "Harmonized DMSP-VIIRS (Li et al. 2020, figshare, DOI 10.1038/s41597-020-0510-y)"
  permanece como item **não coletado nesta rodada**; "NPP-VIIRS-like (Chen/Yu et al.,
  Harvard Dataverse V10, DOI 10.7910/DVN/YGIVCD)" é o item efetivamente em
  `data/raw/`. `data/licenses_parts/economicos.md` cita o DOI/figshare de Li et al.
  para um produto que **não foi baixado**; não corrigido aqui (fora do escopo desta
  família), sinalizado para o responsável por `economicos.md`.

## Classificação

| # | Fonte | Nível | Licença confirmada | Citação exigida | Nota |
|---|---|---|---|---|---|
| 1 | NPP-VIIRS-like (Chen/Yu et al.), 54 recortes, Harvard Dataverse V10 | **A** | CC0 1.0, http://creativecommons.org/publicdomain/zero/1.0, confirmada no JSON da API do Dataverse (não agregador) | Recomendada, não obrigatória sob CC0: Chen, Z. et al. (2021) *ESSD* 13, 889–906, DOI 10.5194/essd-13-889-2021 + Chen, Z., Yu, B. et al. "Global NPP-VIIRS-like nighttime light data (V2) 1992–2025", Harvard Dataverse V10, DOI 10.7910/DVN/YGIVCD | Único raster global nunca mirrorado; só recortes de AOI (2–6 KB) em `data/raw/`, conforme §4.0 regra 2 |
| 2 | WSF Evolution — 5 tiles novos (Chimoio S20E032, Quelimane S18E036, Lichinga S14E034, Xai-Xai S26E032, Inhambane S24E034) | **A** | CC BY 4.0, https://creativecommons.org/licenses/by/4.0/, mesma licença já registrada em `construida.md` para os tiles da AOI de estudo | Marconcini, M., Metz-Marconcini, A., Esch, T., Gorelick, N. (2021), GI_Forum 2021, Issue 1, p. 33–38, DOI 10.1553/giscience2021_01_s33 | Consistente com classificação prévia da família; nenhuma divergência de licença entre tiles |
| 3 | HDX COD-AB Moçambique (`moz_admin_boundaries.geojson.zip`) | **A** | CC BY-IGO 3.0, http://creativecommons.org/licenses/by/3.0/igo/legalcode, lida via API CKAN `package_show` (mesmo padrão já aceito para HDX COD-PS em `demograficas.md`) | OCHA/HDX COD-AB Mozambique (moz_admin_boundaries), fonte declarada INE — não verificada diretamente no site do INE (mesma ressalva já registrada para COD-PS) | ADM0–3, P-codes; nível A pela mesma lógica já aplicada ao COD-PS: variante nomeada de CC-BY, reprocessador com licença própria distingue do documento-INE bruto (nível C) |

## Fontes não obtidas — excluídas, com evidência HTTP (não é lacuna a esconder)

| # | Fonte | Nível | Motivo | Evidência HTTP |
|---|---|---|---|---|
| 4 | VIIRS VNL V2 (Earth Observation Group, `eogdata.mines.edu`) | **B, rebaixada de A** — reclassificação desta auditoria | O item já registrado em `economicos.md` como nível A ("acesso via GEE ou EOG FTP público") descrevia um acesso que **deixou de existir**: todo diretório de download testado (`/nighttime_light/annual/v10,v20,v21,v22/`) e os links `.tif.gz` diretos redirecionam HTTP 302 para `eogauth.mines.edu`, exigindo login OAuth com conta EOG — não é acesso anônimo nem cadastro trivial (o cadastro EOG historicamente exige aprovação institucional/e-mail verificado, não é um clique). Isso satisfaz a definição de nível B do §4.0 ("gratuito mas exige aprovação de uso"), não a de A. **Não avaliado nesta rodada** um acesso equivalente via Google Earth Engine (`NOAA/VIIRS/DNB/MONTHLY_V1/VCMSLCFG` ou coleção correlata): se confirmado que o dado subjacente é replicável por essa via semina exigir mais que uma conta Google trivial, o dado (não a plataforma) poderia retornar a A — pendente de teste, não presumido. | `eogdata.mines.edu/products/vnl/` = 200 (página); todos os `/nighttime_light/annual/*` e `.tif.gz` = 302 → `eogauth.mines.edu` (OAuth), verificado 2026-09-08 |
| 5 | DMSP-OLS estável (NOAA/NCEI) | **C — excluída** | URL registrada em `CLAUDE.md` §4.4 (`ngdc.noaa.gov/eog/dmsp/downloadV4composites.html`) responde HTTP 404 — página removida, sem redirecionamento para conteúdo equivalente. Página sucessora em `eogdata.mines.edu/products/dmsp/` existe (200) mas os links de download (`wwwdata/dmsp/rad_cal/*.tgz`) sofrem o mesmo bloqueio OAuth do item 4. Nenhuma licença localizável no domínio que efetivamente serve o dado hoje; NOAA/NCEI (domínio público, texto de licença já visto em `economicos.md`) não hospeda mais o arquivo. Pela regra §4.0.1 ("sem licença localizável ⇒ C") e pela ausência de via anônima, classificação é **C**, distinta da simples indisponibilidade temporária (não é timeout, é 404 + login obrigatório na via sucessora). | `ngdc.noaa.gov/eog/dmsp/downloadV4composites.html` = 404; `eogdata.mines.edu/products/dmsp/` = 200; `wwwdata/dmsp/rad_cal/*.tgz` = 302 → OAuth, verificado 2026-09-08 |

## Descontinuidade de versão documentada pelo produtor — material para P5/P6/§5.4

Medição do orquestrador: radiância máxima na AOI de Tete cai de 70,4 (2020) para 49,9
(2022) e permanece em 49,9 (2025), na série `viirs_like_li2020_v2` (Chen/Yu). Busca na
literatura do próprio produto (não no dado em si, que este agente não abriu) encontra
evidência **de terceiros que documentam** revisão dos anos 2021–2022 do dataset
NPP-VIIRS-like desta mesma linhagem (rastreamento de catálogo GEE-community, discussão
pública de changelog): "the annual NPP-VIIRS-like NTL data of 2021 and 2022 have been
updated" — i.e., o produtor reprocessou/recalibrou especificamente esses dois anos após
a publicação original de 2021 (que cobria só 2000–2018; a extensão 2019–2025 e as
revisões de 2021–2022 são posteriores, do V10 hospedado no Dataverse). **Isto não é
confirmação de primeira mão do texto de cada nota de versão do Dataverse** (o agente não
teve acesso ao changelog interno do Dataverse nesta rodada — página client-side não
renderizada pelo fetch disponível); é evidência de terceiros de que existe reprocessamento
documentado na janela 2020–2022. **Recomendação, não veredito**: a queda de 70,4→49,9
medida pelo orquestrador **coincide temporalmente com um reprocessamento conhecido do
produto**, e não deve ser lida como quebra de nível econômica (bust do carvão, ADR/ desenho
§1.2 quebra de 2022) sem antes descartar essa explicação alternativa — tratar como
candidato a "placebo de versão do produto" adicional ao já exigido em
`docs/DESENHO_FASE3.md` §4 (P1–P4), a ser verificado por segunda via (ex.: comparação
com VIIRS DNB bruto, se e quando obtido) antes de qualquer atribuição causal à quebra de
2022.
