# Fase 3 — Proveniência da auditoria de classificação (T3)

Complementa `data/provenance_parts/fase3_coleta_t2_proveniencia.md` com o selo de
nível A/B/C que faltava (a coleta registrou apenas `.meta.json` com
`"level": "nao classificado - cabe ao auditor-dados"`).

| arquivo/família | nível final | selo | verificado contra |
|---|---|---|---|
| `viirs_like_li2020_v2_*.tif` (54 recortes, AOI Tete + 5 controles) | A | observado | JSON da API do Harvard Dataverse (`metadataBlocks.citation.license`), não agregador |
| `wsf_evolution_S20E032.tif` (Chimoio) | A | observado (pixel = ano de 1ª detecção) | `grid.geojson` do produtor DLR + página de licença geoservice.dlr.de |
| `wsf_evolution_S18E036.tif` (Quelimane) | A | observado | idem |
| `wsf_evolution_S14E034.tif` (Lichinga) | A | observado | idem |
| `wsf_evolution_S26E032.tif` (Xai-Xai) | A | observado | idem |
| `wsf_evolution_S24E034.tif` (Inhambane) | A | observado | idem |
| `moz_admin_boundaries.geojson.zip` | A | observado | API CKAN `package_show` de data.humdata.org |
| VIIRS VNL V2 (EOG, `eogdata.mines.edu`) | B (rebaixada de A registrada em `economicos.md`) | não obtido | evidência HTTP 302→OAuth em todas as rotas testadas, 2026-09-08 |
| DMSP-OLS estável (NOAA/NCEI) | C — excluída | não obtido | HTTP 404 na URL de `CLAUDE.md`; via sucessora bloqueada por OAuth |

## Consequência para `docs/DESENHO_FASE3.md` — premissa 4 (§1.3 item 4)

O desenho pré-registrado (`docs/DESENHO_FASE3.md`, fixado 2026-09-08, §1.1 tabela e
§1.3 item 4) previa **duas séries de luz independentes que se sobrepõem em 2012–2013**
(`S_VIIRS_soma`, EOG, 2012–2025, nível A antes desta auditoria; `S_DMSP_soma`,
1992–2013, nível A) para conciliar DMSP↔VIIRS por um trecho de sobreposição estimado
**por nós**, com critério pré-registrado em §1.3.4 e §4.4 (P4) do mesmo documento; o
harmonizado (`S_HARM`, Li et al. 2020, ali já registrado como nível **B**) estava
reservado a "só validação, nunca sustenta número publicado" — precisamente porque a
conciliação interna ao produtor não é verificável por nós.

Esta auditoria muda o insumo, não o julgamento already escrito no desenho: `S_VIIRS_soma`
passa de A para B (item 4 acima) e `S_DMSP_soma` passa de A para C (item 5 acima, a
única via de acesso identificada está bloqueada e a página original é 404). **As duas
séries que dariam a conciliação independente deixam de existir em nível A.** A única
série de luz que permanece A é `viirs_like_li2020_v2` (Chen/Yu, Harvard Dataverse) —
que é, ela própria, **um harmonizado produzido pelo método do produtor** (calibração
cruzada por super-resolução/aprendizado profundo, conforme Chen et al. 2021 e extensões
posteriores), não uma soma bruta de radiância por sensor.

## Resposta direta à pergunta do orquestrador

**Sim, a perda de VIIRS VNL (rebaixada a B) e de DMSP-OLS (excluída, C) torna o
harmonizado Chen/Yu a única série de luzes de nível A disponível**, e isso **não é
aceitável como equivalente à premissa original do desenho**, pelos seguintes motivos,
sem eufemismo:

1. A premissa 4 do desenho supunha conciliação **estimada por nós**, com erro-padrão,
   critério de falha e placebo publicáveis (§1.3.4, §4.4 P4 do `DESENHO_FASE3.md`).
   Usar só o harmonizado do produtor substitui isso por uma conciliação **feita dentro
   de um modelo de terceiros** (rede neural de super-resolução, no caso de Chen et al.),
   cujos parâmetros, dados de treino e possíveis mudanças de versão **não são auditáveis
   por este pipeline** — é uma caixa preta de calibração, não uma calibração
   transparente.
2. Isso é agravado, não apenas mencionado en passant, pela descontinuidade medida pelo
   orquestrador (70,4→49,9 entre 2020 e 2022, estável em 49,9 até 2025) **coincidindo
   com uma janela em que terceiros documentam reprocessamento do produto para
   exatamente os anos 2021–2022** (ver `fase3_auditoria_t3.md`, seção de licenças). Sem
   DMSP ou VNL bruto para comparar, **não há como distinguir estatisticamente, com os
   dados hoje em `data/raw/`, uma quebra de produto de uma quebra de economia** na
   quebra de 2022 do desenho causal (`docs/DESENHO_FASE3.md` §1.2, linha "2022").
3. Nenhuma fonte B pode "resolver" isso: por §4.0, B é só validação, nunca sustenta
   conclusão. Não há, hoje, nenhuma fonte A alternativa para cross-checar o harmonizado
   na janela 2020–2022.

**Consequência declarada para o desenho causal**: a quebra de 2022 em `S_VIIRS_soma`
(agora `S_HARM`, o único disponível) deve ser tratada, além dos quatro placebos já
exigidos (P1–P4 de `DESENHO_FASE3.md` §4), com um **quinto aviso obrigatório e
explícito** em qualquer figura/tabela que a publique: "não distinguível de mudança de
versão do produtor entre 2020 e 2022 — nenhuma fonte de nível A permite verificação
independente". Isto não é um placebo executável (não há dado para rodá-lo); é uma
lacuna a declarar, não a maquiar, seguindo o mesmo padrão de honestidade já adotado em
`docs/DESENHO_FASE3.md` §1.3 e §8. Recomenda-se ao orquestrador que `docs/DESENHO_FASE3.md`
receba uma emenda datada (§10 do próprio documento) registrando esta mudança de
disponibilidade de dado, com a declaração explícita de que o autor da emenda **já viu**
o valor da radiância (70,4/49,9) antes de escrevê-la — exigência do próprio protocolo de
pré-registro.
