# Proveniência — Fase 2b: agricultura e várzea (§5.6)

Fragmento consolidado por `scripts/consolidar_registros.py` em `PROVENANCE.md`. Não editar à mão as seções entre marcadores: são geradas pelo script correspondente.


<!-- SECAO_CULTIVO_INICIO -->

## Cultivo — separação fenológica sequeiro × irrigado (§5.6.1, Fase 2b)

Gerado por `pipeline/01_imagery/cultivo.py`. `cultivo_sequeiro` e `cultivo_irrigado` são recortes fenológicos DENTRO de `solo_exposto` e `vegetacao` (§5.1), não camadas novas na partição mutuamente exclusiva da AOI: sobrepõem essas duas camadas por construção e são mutuamente exclusivas apenas em relação a `urbano`/`industrial`/`reassentamento`/`agua`.

**Limiar relativo à paisagem do próprio ano** (ratio_irrigado_amp=0.5, ratio_sequeiro_amp=1.3, ratio_sequeiro_chuva=1.0), pelo mesmo motivo de docs/ADR/0011: NDVI absoluto não é comparável entre os anos-âncora desta série.

**Limitação declarada:** fenologia bianual não separa cultivo de vegetação natural com o mesmo padrão sazonal. `cultivo_sequeiro` mede vegetação de fenologia estacional acentuada (inclui savana herbácea/arbustiva sazonal); `cultivo_irrigado` mede verde persistente de baixa amplitude (inclui mata ripária). A acurácia do usuário medida por interpretação visual está em `acuracia_cultivo.py` / `data/processed/acuracia_cultivo_por_ano.csv`.

**Instabilidade herdada da Fase 1:** a proporção vegetacao/solo_exposto muda de forma não monotônica entre anos-âncora por diferença de sensor/pluviosidade (mesmo efeito de docs/ADR/0008 e ADR/0009). A série de área de cultivo herda essa instabilidade e não deve ser lida como mudança real de uso do solo sem controlar por ela.

| ano | sequeiro km² | irrigado km² | domínio veg km² | domínio solo km² | mediana amplitude | mediana NDVI seca | mediana NDVI chuva |
|---|---|---|---|---|---|---|---|
| 2000 | 576.6 | 47.1 | 235.3 | 2219.7 | 0.235 | 0.233 | 0.475 |

<!-- SECAO_CULTIVO_FIM -->




<!-- SECAO_VARZEA_INICIO -->

## Várzea — HAND aproximado (§5.6.2, Fase 2b)

Gerado por `pipeline/01_imagery/varzea.py`. Camada ESTÁTICA (não varia por ano-âncora): geomorfologia, não cobertura do solo.

**Aproximação declarada:** HAND por vizinho mais próximo NO PLANO (`scipy.ndimage.distance_transform_edt`), não por caminho de fluxo D8 — nenhuma biblioteca de roteamento hidrológico (`pysheds`/`richdem`/`whitebox`) está disponível neste ambiente. A aproximação tende a superestimar a várzea em relevo dissecado; é aceitável no vale de baixa declividade do Zambeze/Revúbuè dentro da AOI, mas não foi corrigida onde falha. Ver docstring completa do script.

- **Parâmetros (config/study.yaml):** hand_max_m=10.0, dist_max_rio_m=1000.0
- **Fonte de drenagem:** HydroRIVERS v10 África, 130 trechos na AOI, sem filtro de ordem de fluxo (riachos pequenos incluídos)
- **Área de várzea:** 650.2 km²
- **Selo:** modelado (HAND derivado de DEM observado + rede de drenagem observada)

<!-- SECAO_VARZEA_FIM -->



<!-- SECAO_ACURACIA_CULTIVO_INICIO -->

## Acurácia por classe — cultivo (§5.6.1, §10)

Gerado por `pipeline/01_imagery/acuracia_cultivo.py`. **Não editar à mão.**

**Ano validado:** 2020 (único — ver `amostras_validacao_cultivo.py`). **Intérprete(s):** Claude (Sonnet 5), interpretação visual automatizada de recorte RGB — não humana, não verdade de campo.

| classe | prevalência no mapa | n | AU | IC95 AU | AP | AP estimável? |
|---|---|---|---|---|---|---|
| cultivo_sequeiro | 0.1682 | 8 | 0.0 | 0.0 | 0.0 | True |
| cultivo_irrigado | 0.0138 | 9 | 0.5556 | 0.3443 | 0.154 | True |

**Acurácia global:** 0.621 ± 0.262 · **kappa:** -0.065 · **n indeterminado:** 11 de 36.

AU = acurácia do usuário (1 − comissão) · AP = acurácia do produtor (1 − omissão).

n=12/estrato, ANO ÚNICO (2020) — ver amostras_validacao_cultivo.py para o motivo do desenho reduzido em relação a acuracia.py (construído: 24/estrato, 6 anos). NÃO generalizar este número aos outros 5 anos-âncora. Rótulos por interpretação visual automatizada (mesmo tipo de intérprete de ADR 0007), não verdade de campo. Produtor não é confiável quando produtor_estimavel_* é False — ver alavanca_maxima_1_ponto_*: fração da área da AOI que UM ponto do estrato de maior peso entre os outros dois carrega no estimador.

**Referência externa:** GLAD Cropland / ESA WorldCover / Dynamic World não estavam espelhados em `data/raw/` no momento desta execução (Fase 0' registrou URLs quebradas). Esta validação é só interna (interpretação visual); nenhuma métrica contra produto externo de cobertura de cultivo é reportada. Se os arquivos aparecerem depois, a validação externa é trabalho futuro — não duplicado aqui.

<!-- SECAO_ACURACIA_CULTIVO_FIM -->




<!-- SECAO_VALIDACAO_EXTERNA_CULTIVO_INICIO -->

## Validação externa de cultivo — GLAD Cropland / ESA WorldCover

Gerado por `pipeline/01_imagery/validacao_externa_cultivo.py`. **Concordância, não acurácia** (mesma ressalva de `concordancia_ghsl` em `classificacao.py`): produtos com erro próprio, resolução e definição de cultivo diferentes.

| referência | ano ref. | ano cultivo | camada | área mapa km² | área ref. km² | Jaccard | recall/ref. |
|---|---|---|---|---|---|---|---|
| GLAD_Global_Cropland | 2003 | 2005 | cultivo_sequeiro | 358.671 | 19.895 | 0.001 | 0.0196 |
| GLAD_Global_Cropland | 2003 | 2005 | cultivo_irrigado | 16.389 | 19.895 | 0.0686 | 0.1171 |
| GLAD_Global_Cropland | 2007 | 2005 | cultivo_sequeiro | 358.671 | 17.956 | 0.0007 | 0.0138 |
| GLAD_Global_Cropland | 2007 | 2005 | cultivo_irrigado | 16.389 | 17.956 | 0.0976 | 0.1701 |
| GLAD_Global_Cropland | 2011 | 2010 | cultivo_sequeiro | 760.501 | 20.989 | 0.0011 | 0.0398 |
| GLAD_Global_Cropland | 2011 | 2010 | cultivo_irrigado | 152.651 | 20.989 | 0.0433 | 0.3436 |
| GLAD_Global_Cropland | 2015 | 2015 | cultivo_sequeiro | 398.902 | 24.991 | 0.0018 | 0.0309 |
| GLAD_Global_Cropland | 2015 | 2015 | cultivo_irrigado | 42.66 | 24.991 | 0.1287 | 0.3087 |
| GLAD_Global_Cropland | 2019 | 2020 | cultivo_sequeiro | 421.7 | 40.063 | 0.0006 | 0.0066 |
| GLAD_Global_Cropland | 2019 | 2020 | cultivo_irrigado | 34.552 | 40.063 | 0.1445 | 0.2352 |
| ESA_WorldCover | 2020 | 2020 | cultivo_sequeiro | 421.7 | 42.467 | 0.0043 | 0.0463 |
| ESA_WorldCover | 2020 | 2020 | cultivo_irrigado | 34.552 | 42.467 | 0.0327 | 0.0574 |

Concordância baixa não piora o veredito de docs/ADR/0012 (`cultivo_sequeiro` já reprovado por interpretação visual própria); concordância alta seria evidência de apoio, não validação por si — ver limitações na docstring do script.

<!-- SECAO_VALIDACAO_EXTERNA_CULTIVO_FIM -->



