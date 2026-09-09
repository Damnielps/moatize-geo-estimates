# Proveniência — Compostos de Imagem e Índices (Fase 1)

Fragmento gerado por `pipeline/01_imagery/compostos.py`. **Não editar à mão**
— reexecute o script para regenerar. Consolidado em `PROVENANCE.md` por
`scripts/consolidar_registros.py`. Este fragmento é novo e não substitui
`data/provenance_parts/imagem.md` (Fase 0', fechado).

Catálogo STAC canônico: `https://planetarycomputer.microsoft.com/api/stac/v1` (ver `docs/ADR/0004-divergencia-catalogos-stac.md`).

Nenhum processo estocástico: `config/seeds.yaml` não se aplica a este
estágio (mediana não amostra nem sorteia). Determinismo garantido pela
ordenação por `id` dos itens STAC antes da composição.

## Defeito corrigido nesta entrega (Fase 1) e descarte dos produtos anteriores

Os cinco compostos gravados por uma execução anterior desta mesma tarefa
(2000, 2005, 2015, 2020, 2025) foram **descartados e regravados do zero**,
não ajustados. `odc.stac.load` honrava o `nodata: 1` declarado no
`raster:bands` do asset `qa_pixel` (Landsat C2 L2) — e 1 é exatamente o
valor do bit de FILL, não um nodata de fato. Isso trocava todo pixel de
falha real (fill/gap) por `0` na banda carregada, e `0` não tem nenhum bit
de qualidade ruim aceso: a máscara de nuvem/sombra/preenchimento
classificava esses pixels de falha como válidos. O sintoma mais visível
era o composto de 2010 (Landsat 7 SLC-off, medição experimental de
`docs/ADR/0005-...md`): declarava 95,68% dos pixels com as 4 observações
completas e 0% sem nenhuma, quando a contagem correta é 73,36% com as 4
e 0,005% sem nenhuma — bom demais para ser real em cenas SLC-off.

Corrigido via `_stac_common.STAC_CFG_QA_PIXEL_SEM_NODATA` (passado a
`odc.stac.load(..., stac_cfg=...)`, desliga o nodata declarado só para
`qa_pixel`) e uma defesa em profundidade em `mascara_valida_landsat`
(`qa == 0` também é tratado como inválido — 0 nunca é um valor legítimo de
`QA_PIXEL`). Ver `pipeline/tests/test_imagery.py::test_nobs_bate_com_calculo_direto_do_qa_pixel` para o contrato de
regressão (usa as cenas Landsat 7/2010, o único conjunto do repositório
com pixels de fill reais dentro da AOI) e `config/tolerances.yaml ->
regressao_numerica.contrato_qa_pixel` para a tolerância declarada.

Os cinco compostos e todos os índices abaixo foram gerados **depois**
dessa correção — nenhum artefato do defeito permanece em
`data/processed/imagery/`.

## Ano-âncora 2000

- **Arquivo**: `data/processed/imagery/composto_2000_30m_32736.tif`
- **Janela temporal**: `2000-05-01T00:00:00Z/2000-10-31T23:59:59Z` (janela_anos=1)
- **Landsat**: landsat-7, 3 cenas
- **Sentinel-2**: não incluído (fora do complemento do ano ou sem cobertura)
- **Observações válidas por pixel**: mínimo 0, mediana 3.0
- **Pixels sem nenhuma observação válida**: 12 de 2785056 (0.00%)
- **Commit**: `a81ac6b5803ff36a1dfad3dc30efb0fe22da1442`
- **Hash de `config/study.yaml`**: `f6de82755961c660a96ab2e3563b500b784d1680907e53fde54629d684fd5f1a`
- **Data de processamento**: 2026-09-08T14:18:38.641595+00:00
- **Selo**: observado

IDs das cenas Landsat: LE07_L2SP_168071_20000714_02_T1, LE07_L2SP_168071_20000831_02_T1, LE07_L2SP_168071_20001002_02_T1

## Ano-âncora 2005

- **Arquivo**: `data/processed/imagery/composto_2005_30m_32736.tif`
- **Janela temporal**: `2005-05-01T00:00:00Z/2005-10-31T23:59:59Z` (janela_anos=1)
- **Landsat**: landsat-5, 4 cenas
- **Sentinel-2**: não incluído (fora do complemento do ano ou sem cobertura)
- **Observações válidas por pixel**: mínimo 2, mediana 4.0
- **Pixels sem nenhuma observação válida**: 0 de 2785056 (0.00%)
- **Commit**: `a81ac6b5803ff36a1dfad3dc30efb0fe22da1442`
- **Hash de `config/study.yaml`**: `f6de82755961c660a96ab2e3563b500b784d1680907e53fde54629d684fd5f1a`
- **Data de processamento**: 2026-09-08T14:18:56.643286+00:00
- **Selo**: observado

IDs das cenas Landsat: LT05_L2SP_168071_20050517_02_T1, LT05_L2SP_168071_20050720_02_T1, LT05_L2SP_168071_20050906_02_T1, LT05_L2SP_168071_20050922_02_T1

## Ano-âncora 2010

- **Arquivo**: `data/processed/imagery/composto_2010_30m_32736.tif`
- **Janela temporal**: `2010-05-01T00:00:00Z/2010-10-31T23:59:59Z` (janela_anos=1)
- **Landsat**: landsat-7, 4 cenas
- **Sentinel-2**: não incluído (fora do complemento do ano ou sem cobertura)
- **Observações válidas por pixel**: mínimo 0, mediana 4.0
- **Pixels sem nenhuma observação válida**: 130 de 2785056 (0.00%)
- **Commit**: `a81ac6b5803ff36a1dfad3dc30efb0fe22da1442`
- **Hash de `config/study.yaml`**: `f6de82755961c660a96ab2e3563b500b784d1680907e53fde54629d684fd5f1a`
- **Data de processamento**: 2026-09-08T14:19:14.658606+00:00
- **Selo**: observado

IDs das cenas Landsat: LE07_L2SP_168071_20100507_02_T1, LE07_L2SP_168071_20100608_02_T1, LE07_L2SP_168071_20100827_02_T1, LE07_L2SP_168071_20101014_02_T1

## Ano-âncora 2015

- **Arquivo**: `data/processed/imagery/composto_2015_30m_32736.tif`
- **Janela temporal**: `2015-05-01T00:00:00Z/2015-10-31T23:59:59Z` (janela_anos=1)
- **Landsat**: landsat-8, 10 cenas
- **Sentinel-2**: não incluído (fora do complemento do ano ou sem cobertura)
- **Observações válidas por pixel**: mínimo 6, mediana 10.0
- **Pixels sem nenhuma observação válida**: 0 de 2785056 (0.00%)
- **Commit**: `a81ac6b5803ff36a1dfad3dc30efb0fe22da1442`
- **Hash de `config/study.yaml`**: `f6de82755961c660a96ab2e3563b500b784d1680907e53fde54629d684fd5f1a`
- **Data de processamento**: 2026-09-08T14:19:53.314955+00:00
- **Selo**: observado

IDs das cenas Landsat: LC08_L2SP_168071_20150513_02_T1, LC08_L2SP_168071_20150529_02_T1, LC08_L2SP_168071_20150614_02_T1, LC08_L2SP_168071_20150630_02_T1, LC08_L2SP_168071_20150716_02_T1, LC08_L2SP_168071_20150817_02_T1, LC08_L2SP_168071_20150902_02_T1, LC08_L2SP_168071_20150918_02_T1, LC08_L2SP_168071_20151004_02_T1, LC08_L2SP_168071_20151020_02_T1

## Ano-âncora 2020

- **Arquivo**: `data/processed/imagery/composto_2020_30m_32736.tif`
- **Janela temporal**: `2020-05-01T00:00:00Z/2020-10-31T23:59:59Z` (janela_anos=1)
- **Landsat**: landsat-8, 9 cenas
- **Sentinel-2**: 103 cenas
- **Observações válidas por pixel**: mínimo 9, mediana 31.0
- **Pixels sem nenhuma observação válida**: 0 de 2785056 (0.00%)
- **Commit**: `a81ac6b5803ff36a1dfad3dc30efb0fe22da1442`
- **Hash de `config/study.yaml`**: `f6de82755961c660a96ab2e3563b500b784d1680907e53fde54629d684fd5f1a`
- **Data de processamento**: 2026-09-08T14:23:48.798380+00:00
- **Selo**: observado

IDs das cenas Landsat: LC08_L2SP_168071_20200526_02_T1, LC08_L2SP_168071_20200611_02_T1, LC08_L2SP_168071_20200627_02_T1, LC08_L2SP_168071_20200713_02_T1, LC08_L2SP_168071_20200814_02_T1, LC08_L2SP_168071_20200830_02_T1, LC08_L2SP_168071_20200915_02_T1, LC08_L2SP_168071_20201001_02_T1, LC08_L2SP_168071_20201017_02_T1

IDs das cenas Sentinel-2: S2A_MSIL2A_20200503T073621_R092_T36KWG_20200920T071754, S2A_MSIL2A_20200503T073621_R092_T36KXG_20200920T071802, S2A_MSIL2A_20200503T073621_R092_T36LWH_20200920T071815, S2A_MSIL2A_20200503T073621_R092_T36LXH_20200920T071818, S2A_MSIL2A_20200513T073621_R092_T36KWG_20200918T001320, S2A_MSIL2A_20200513T073621_R092_T36KWG_20200918T001335, S2A_MSIL2A_20200513T073621_R092_T36KXG_20200918T001328, S2A_MSIL2A_20200513T073621_R092_T36KXG_20200918T001339, S2A_MSIL2A_20200513T073621_R092_T36LWH_20200918T001337, S2A_MSIL2A_20200513T073621_R092_T36LWH_20200918T001341, S2A_MSIL2A_20200513T073621_R092_T36LXH_20200918T001335, S2A_MSIL2A_20200513T073621_R092_T36LXH_20200918T001350, S2A_MSIL2A_20200523T073621_R092_T36KWG_20200910T155537, S2A_MSIL2A_20200523T073621_R092_T36KXG_20200910T155551, S2A_MSIL2A_20200523T073621_R092_T36LWH_20200910T155602, S2A_MSIL2A_20200523T073621_R092_T36LXH_20200910T155605, S2A_MSIL2A_20200602T073621_R092_T36LWH_20200825T200719, S2A_MSIL2A_20200602T073621_R092_T36LXH_20200825T200721, S2A_MSIL2A_20200622T073621_R092_T36KWG_20200908T190853, S2A_MSIL2A_20200622T073621_R092_T36KXG_20200908T191021, S2A_MSIL2A_20200622T073621_R092_T36LWH_20200908T191748, S2A_MSIL2A_20200622T073621_R092_T36LXH_20200908T191924, S2A_MSIL2A_20200712T073621_R092_T36KWG_20200912T215411, S2A_MSIL2A_20200712T073621_R092_T36KWG_20200912T215421, S2A_MSIL2A_20200712T073621_R092_T36KXG_20200912T215419, S2A_MSIL2A_20200712T073621_R092_T36KXG_20200912T215428, S2A_MSIL2A_20200712T073621_R092_T36LWH_20200912T215438, S2A_MSIL2A_20200712T073621_R092_T36LWH_20200912T215443, S2A_MSIL2A_20200712T073621_R092_T36LXH_20200912T215441, S2A_MSIL2A_20200712T073621_R092_T36LXH_20200912T215450, S2A_MSIL2A_20200722T073621_R092_T36KWG_20200817T020801, S2A_MSIL2A_20200722T073621_R092_T36KXG_20200908T191022, S2A_MSIL2A_20200722T073621_R092_T36LXH_20200817T020828, S2A_MSIL2A_20200801T073621_R092_T36KWG_20201027T083643, S2A_MSIL2A_20200801T073621_R092_T36LWH_20200815T171202, S2A_MSIL2A_20200801T073621_R092_T36LXH_20200908T191927, S2A_MSIL2A_20200811T073621_R092_T36KWG_20200814T184913, S2A_MSIL2A_20200811T073621_R092_T36KXG_20200814T184850, S2A_MSIL2A_20200811T073621_R092_T36LWH_20200814T184841, S2A_MSIL2A_20200811T073621_R092_T36LXH_20200814T184909, S2A_MSIL2A_20200831T073621_R092_T36KWG_20200919T052429, S2A_MSIL2A_20200831T073621_R092_T36LWH_20200907T203302, S2A_MSIL2A_20200831T073621_R092_T36LXH_20200907T203139, S2A_MSIL2A_20200910T073621_R092_T36KWG_20200912T032248, S2A_MSIL2A_20200910T073621_R092_T36KXG_20200912T031437, S2A_MSIL2A_20200910T073621_R092_T36LWH_20200912T031541, S2A_MSIL2A_20200910T073621_R092_T36LXH_20200912T032250, S2A_MSIL2A_20200920T073621_R092_T36KWG_20201027T220553, S2A_MSIL2A_20200920T073621_R092_T36KXG_20201027T214743, S2A_MSIL2A_20200920T073621_R092_T36LWH_20201027T224117, S2A_MSIL2A_20200920T073621_R092_T36LXH_20201027T214710, S2A_MSIL2A_20200930T073721_R092_T36KWG_20201002T080946, S2A_MSIL2A_20200930T073721_R092_T36LXH_20201002T080902, S2A_MSIL2A_20201010T073831_R092_T36KWG_20201012T031508, S2A_MSIL2A_20201010T073831_R092_T36KXG_20201012T032006, S2A_MSIL2A_20201010T073831_R092_T36LWH_20201012T030002, S2A_MSIL2A_20201010T073831_R092_T36LXH_20201027T125105, S2A_MSIL2A_20201020T073941_R092_T36KWG_20201021T210400, S2A_MSIL2A_20201020T073941_R092_T36KXG_20201021T205233, S2A_MSIL2A_20201020T073941_R092_T36LWH_20201021T205550, S2A_MSIL2A_20201020T073941_R092_T36LXH_20201021T205220, S2A_MSIL2A_20201030T074041_R092_T36KWG_20201101T235804, S2A_MSIL2A_20201030T074041_R092_T36KXG_20201102T000300, S2A_MSIL2A_20201030T074041_R092_T36LWH_20201101T235823, S2A_MSIL2A_20201030T074041_R092_T36LXH_20201101T235804, S2B_MSIL2A_20200518T073609_R092_T36KWG_20201027T071120, S2B_MSIL2A_20200518T073609_R092_T36KXG_20200910T032436, S2B_MSIL2A_20200518T073609_R092_T36LWH_20200910T032436, S2B_MSIL2A_20200518T073609_R092_T36LXH_20201027T071121, S2B_MSIL2A_20200607T073619_R092_T36KWG_20200919T052433, S2B_MSIL2A_20200607T073619_R092_T36KXG_20200919T052438, S2B_MSIL2A_20200617T073619_R092_T36KWG_20200823T025222, S2B_MSIL2A_20200617T073619_R092_T36KXG_20201027T074459, S2B_MSIL2A_20200617T073619_R092_T36LWH_20201027T074455, S2B_MSIL2A_20200617T073619_R092_T36LXH_20200823T025229, S2B_MSIL2A_20200627T073619_R092_T36LXH_20200824T082726, S2B_MSIL2A_20200707T073619_R092_T36KXG_20200912T091123, S2B_MSIL2A_20200707T073619_R092_T36LWH_20200912T091124, S2B_MSIL2A_20200707T073619_R092_T36LXH_20201027T081734, S2B_MSIL2A_20200727T073619_R092_T36KWG_20200908T190907, S2B_MSIL2A_20200727T073619_R092_T36KXG_20200817T185010, S2B_MSIL2A_20200727T073619_R092_T36LWH_20200817T185021, S2B_MSIL2A_20200727T073619_R092_T36LXH_20200908T191927, S2B_MSIL2A_20200816T073619_R092_T36KWG_20200818T143332, S2B_MSIL2A_20200816T073619_R092_T36KXG_20200818T143242, S2B_MSIL2A_20200816T073619_R092_T36LWH_20200818T143319, S2B_MSIL2A_20200816T073619_R092_T36LXH_20200818T143328, S2B_MSIL2A_20200826T073619_R092_T36KWG_20200827T221401, S2B_MSIL2A_20200826T073619_R092_T36KXG_20200827T221205, S2B_MSIL2A_20200826T073619_R092_T36LWH_20201027T091234, S2B_MSIL2A_20200826T073619_R092_T36LXH_20200919T052629, S2B_MSIL2A_20200915T073619_R092_T36KWG_20200918T104345, S2B_MSIL2A_20200915T073619_R092_T36KXG_20200918T104323, S2B_MSIL2A_20200915T073619_R092_T36LWH_20200918T104325, S2B_MSIL2A_20200915T073619_R092_T36LXH_20200918T104315, S2B_MSIL2A_20200925T073649_R092_T36KWG_20201104T001607, S2B_MSIL2A_20200925T073649_R092_T36KXG_20201028T072056, S2B_MSIL2A_20200925T073649_R092_T36LWH_20201028T071744, S2B_MSIL2A_20200925T073649_R092_T36LXH_20201028T071754, S2B_MSIL2A_20201025T074009_R092_T36KWG_20201030T090351, S2B_MSIL2A_20201025T074009_R092_T36KXG_20201030T090339, S2B_MSIL2A_20201025T074009_R092_T36LWH_20201030T092504, S2B_MSIL2A_20201025T074009_R092_T36LXH_20201109T233238

## Ano-âncora 2025

- **Arquivo**: `data/processed/imagery/composto_2025_30m_32736.tif`
- **Janela temporal**: `2025-05-01T00:00:00Z/2025-10-31T23:59:59Z` (janela_anos=1)
- **Landsat**: landsat-9, 6 cenas
- **Sentinel-2**: 162 cenas
- **Observações válidas por pixel**: mínimo 32, mediana 42.0
- **Pixels sem nenhuma observação válida**: 0 de 2785056 (0.00%)
- **Commit**: `a81ac6b5803ff36a1dfad3dc30efb0fe22da1442`
- **Hash de `config/study.yaml`**: `f6de82755961c660a96ab2e3563b500b784d1680907e53fde54629d684fd5f1a`
- **Data de processamento**: 2026-09-08T14:29:29.234284+00:00
- **Selo**: observado

IDs das cenas Landsat: LC09_L2SP_168071_20250516_02_T1, LC09_L2SP_168071_20250601_02_T1, LC09_L2SP_168071_20250804_02_T1, LC09_L2SP_168071_20250820_02_T1, LC09_L2SP_168071_20250905_02_T1, LC09_L2SP_168071_20251007_02_T1

IDs das cenas Sentinel-2: S2A_MSIL2A_20250509T074021_R092_T36KWG_20250509T113013, S2A_MSIL2A_20250509T074021_R092_T36KXG_20250509T113013, S2A_MSIL2A_20250509T074021_R092_T36LWH_20250509T113013, S2A_MSIL2A_20250509T074021_R092_T36LXH_20250509T113013, S2A_MSIL2A_20250519T075451_R092_T36KWG_20250519T100916, S2A_MSIL2A_20250608T075451_R092_T36KWG_20250608T100815, S2A_MSIL2A_20250608T075451_R092_T36KXG_20250608T100815, S2A_MSIL2A_20250608T075451_R092_T36LWH_20250608T100815, S2A_MSIL2A_20250608T075451_R092_T36LXH_20250608T100815, S2A_MSIL2A_20250618T074021_R092_T36KWG_20250618T110116, S2A_MSIL2A_20250618T074021_R092_T36KXG_20250618T110116, S2A_MSIL2A_20250618T074021_R092_T36LWH_20250618T110116, S2A_MSIL2A_20250618T074021_R092_T36LXH_20250618T110116, S2A_MSIL2A_20250628T075451_R092_T36KWG_20250628T102909, S2A_MSIL2A_20250628T075451_R092_T36KXG_20250628T102909, S2A_MSIL2A_20250628T075451_R092_T36LWH_20250628T102909, S2A_MSIL2A_20250628T075451_R092_T36LXH_20250628T102909, S2A_MSIL2A_20250708T074031_R092_T36LWH_20250708T112915, S2A_MSIL2A_20250708T074031_R092_T36LXH_20250708T112915, S2A_MSIL2A_20250718T075451_R092_T36KWG_20250718T101120, S2A_MSIL2A_20250718T075451_R092_T36KXG_20250718T101120, S2A_MSIL2A_20250718T075451_R092_T36LWH_20250718T101120, S2A_MSIL2A_20250807T075451_R092_T36KWG_20250807T103914, S2A_MSIL2A_20250807T075451_R092_T36KXG_20250807T103914, S2A_MSIL2A_20250807T075451_R092_T36LWH_20250807T103914, S2A_MSIL2A_20250807T075451_R092_T36LXH_20250807T103914, S2A_MSIL2A_20250817T074021_R092_T36KWG_20250817T110213, S2A_MSIL2A_20250817T074021_R092_T36KXG_20250817T110213, S2A_MSIL2A_20250817T074021_R092_T36LWH_20250817T110213, S2A_MSIL2A_20250817T074021_R092_T36LXH_20250817T110213, S2A_MSIL2A_20250827T075451_R092_T36KWG_20250827T101719, S2A_MSIL2A_20250827T075451_R092_T36KXG_20250827T101719, S2A_MSIL2A_20250827T075451_R092_T36LWH_20250827T101719, S2A_MSIL2A_20250827T075451_R092_T36LXH_20250827T101719, S2A_MSIL2A_20250906T074021_R092_T36KXG_20250906T114026, S2A_MSIL2A_20250906T074021_R092_T36LWH_20250906T114026, S2A_MSIL2A_20250906T074021_R092_T36LXH_20250906T114026, S2A_MSIL2A_20250916T075451_R092_T36KWG_20250916T100824, S2A_MSIL2A_20250916T075451_R092_T36KXG_20250916T100824, S2A_MSIL2A_20250916T075451_R092_T36LWH_20250916T100824, S2A_MSIL2A_20250916T075451_R092_T36LXH_20250916T100824, S2A_MSIL2A_20251006T074031_R092_T36KWG_20251006T112017, S2A_MSIL2A_20251006T074031_R092_T36KXG_20251006T112017, S2A_MSIL2A_20251006T074031_R092_T36LWH_20251006T112017, S2A_MSIL2A_20251006T074031_R092_T36LXH_20251006T112017, S2A_MSIL2A_20251016T075451_R092_T36KWG_20251016T103126, S2A_MSIL2A_20251016T075451_R092_T36KXG_20251016T103126, S2A_MSIL2A_20251016T075451_R092_T36LWH_20251016T103126, S2A_MSIL2A_20251016T075451_R092_T36LXH_20251016T103126, S2A_MSIL2A_20251026T074031_R092_T36KWG_20251026T110418, S2A_MSIL2A_20251026T074031_R092_T36KXG_20251026T110418, S2A_MSIL2A_20251026T074031_R092_T36LXH_20251026T110418, S2B_MSIL2A_20250502T073619_R092_T36KWG_20250502T113003, S2B_MSIL2A_20250502T073619_R092_T36KXG_20250502T113003, S2B_MSIL2A_20250502T073619_R092_T36LWH_20250502T113003, S2B_MSIL2A_20250502T073619_R092_T36LXH_20250502T113003, S2B_MSIL2A_20250522T073619_R092_T36KWG_20250522T095453, S2B_MSIL2A_20250522T073619_R092_T36LWH_20250522T095453, S2B_MSIL2A_20250601T073619_R092_T36KWG_20250601T102230, S2B_MSIL2A_20250601T073619_R092_T36KXG_20250601T102230, S2B_MSIL2A_20250601T073619_R092_T36LWH_20250601T102230, S2B_MSIL2A_20250601T073619_R092_T36LXH_20250601T102230, S2B_MSIL2A_20250611T073609_R092_T36KXG_20250611T112907, S2B_MSIL2A_20250611T073609_R092_T36LWH_20250611T103259, S2B_MSIL2A_20250611T073609_R092_T36LWH_20250611T112907, S2B_MSIL2A_20250611T073609_R092_T36LXH_20250611T103259, S2B_MSIL2A_20250611T073609_R092_T36LXH_20250611T112907, S2B_MSIL2A_20250621T073619_R092_T36KWG_20250621T095930, S2B_MSIL2A_20250621T073619_R092_T36KXG_20250621T095930, S2B_MSIL2A_20250621T073619_R092_T36LWH_20250621T095930, S2B_MSIL2A_20250621T073619_R092_T36LXH_20250621T095930, S2B_MSIL2A_20250731T073609_R092_T36KWG_20250731T100050, S2B_MSIL2A_20250731T073609_R092_T36KXG_20250731T100050, S2B_MSIL2A_20250731T073609_R092_T36LWH_20250731T100050, S2B_MSIL2A_20250731T073609_R092_T36LXH_20250731T100050, S2B_MSIL2A_20250810T073619_R092_T36KWG_20250810T102333, S2B_MSIL2A_20250810T073619_R092_T36KXG_20250810T102333, S2B_MSIL2A_20250810T073619_R092_T36LWH_20250810T102333, S2B_MSIL2A_20250810T073619_R092_T36LXH_20250810T102333, S2B_MSIL2A_20250820T073619_R092_T36KWG_20250820T113111, S2B_MSIL2A_20250820T073619_R092_T36KXG_20250820T113111, S2B_MSIL2A_20250820T073619_R092_T36LWH_20250820T102406, S2B_MSIL2A_20250820T073619_R092_T36LWH_20250820T113111, S2B_MSIL2A_20250820T073619_R092_T36LXH_20250820T102406, S2B_MSIL2A_20250820T073619_R092_T36LXH_20250820T113111, S2B_MSIL2A_20250830T073619_R092_T36KWG_20250830T102143, S2B_MSIL2A_20250830T073619_R092_T36KXG_20250830T102143, S2B_MSIL2A_20250830T073619_R092_T36LWH_20250830T102143, S2B_MSIL2A_20250830T073619_R092_T36LXH_20250830T102143, S2B_MSIL2A_20250909T073609_R092_T36KWG_20250909T102706, S2B_MSIL2A_20250909T073609_R092_T36KXG_20250909T102706, S2B_MSIL2A_20250909T073609_R092_T36LWH_20250909T102706, S2B_MSIL2A_20250909T073609_R092_T36LXH_20250909T102706, S2B_MSIL2A_20250919T073609_R092_T36KWG_20250919T095927, S2B_MSIL2A_20250919T073609_R092_T36LXH_20250919T095927, S2B_MSIL2A_20250929T073619_R092_T36KWG_20250929T102250, S2B_MSIL2A_20250929T073619_R092_T36KXG_20250929T102250, S2B_MSIL2A_20250929T073619_R092_T36LWH_20250929T102250, S2B_MSIL2A_20250929T073619_R092_T36LXH_20250929T102250, S2B_MSIL2A_20251009T073729_R092_T36KWG_20251009T102743, S2B_MSIL2A_20251009T073729_R092_T36KXG_20251009T102743, S2B_MSIL2A_20251009T073729_R092_T36LWH_20251009T102743, S2B_MSIL2A_20251009T073729_R092_T36LXH_20251009T102743, S2B_MSIL2A_20251019T073839_R092_T36KWG_20251019T095556, S2B_MSIL2A_20251019T073839_R092_T36KXG_20251019T095556, S2B_MSIL2A_20251019T073839_R092_T36LWH_20251019T095556, S2B_MSIL2A_20251019T073839_R092_T36LXH_20251019T095556, S2B_MSIL2A_20251029T073939_R092_T36KWG_20251029T114333, S2B_MSIL2A_20251029T073939_R092_T36KXG_20251029T114333, S2B_MSIL2A_20251029T073939_R092_T36LWH_20251029T114333, S2B_MSIL2A_20251029T073939_R092_T36LXH_20251029T114333, S2C_MSIL2A_20250517T073631_R092_T36KWG_20250517T123613, S2C_MSIL2A_20250527T073631_R092_T36KWG_20250527T130031, S2C_MSIL2A_20250527T073631_R092_T36LWH_20250527T130031, S2C_MSIL2A_20250527T073631_R092_T36LXH_20250527T130031, S2C_MSIL2A_20250626T073631_R092_T36KWG_20250626T123815, S2C_MSIL2A_20250626T073631_R092_T36KXG_20250626T123815, S2C_MSIL2A_20250626T073631_R092_T36LWH_20250626T123815, S2C_MSIL2A_20250626T073631_R092_T36LXH_20250626T123815, S2C_MSIL2A_20250706T073641_R092_T36KWG_20250706T124023, S2C_MSIL2A_20250706T073641_R092_T36KXG_20250706T124023, S2C_MSIL2A_20250706T073641_R092_T36LWH_20250706T124023, S2C_MSIL2A_20250706T073641_R092_T36LXH_20250706T124023, S2C_MSIL2A_20250716T073641_R092_T36KWG_20250716T124416, S2C_MSIL2A_20250716T073641_R092_T36KXG_20250716T124416, S2C_MSIL2A_20250716T073641_R092_T36LWH_20250716T124416, S2C_MSIL2A_20250716T073641_R092_T36LXH_20250716T124416, S2C_MSIL2A_20250726T073641_R092_T36KWG_20250726T123415, S2C_MSIL2A_20250726T073641_R092_T36KXG_20250726T123415, S2C_MSIL2A_20250726T073641_R092_T36LWH_20250726T123415, S2C_MSIL2A_20250726T073641_R092_T36LXH_20250726T123415, S2C_MSIL2A_20250805T073631_R092_T36KWG_20250805T110921, S2C_MSIL2A_20250805T073631_R092_T36KXG_20250805T110921, S2C_MSIL2A_20250805T073631_R092_T36LWH_20250805T110921, S2C_MSIL2A_20250805T073631_R092_T36LXH_20250805T110921, S2C_MSIL2A_20250815T073631_R092_T36KWG_20250815T130315, S2C_MSIL2A_20250815T073631_R092_T36KXG_20250815T130315, S2C_MSIL2A_20250815T073631_R092_T36LWH_20250815T130315, S2C_MSIL2A_20250815T073631_R092_T36LXH_20250815T130315, S2C_MSIL2A_20250825T073631_R092_T36KWG_20250825T123913, S2C_MSIL2A_20250825T073631_R092_T36KXG_20250825T123913, S2C_MSIL2A_20250825T073631_R092_T36LWH_20250825T123913, S2C_MSIL2A_20250825T073631_R092_T36LXH_20250825T123913, S2C_MSIL2A_20250904T073631_R092_T36KWG_20250904T124917, S2C_MSIL2A_20250904T073631_R092_T36KXG_20250904T124917, S2C_MSIL2A_20250904T073631_R092_T36LWH_20250904T124917, S2C_MSIL2A_20250904T073631_R092_T36LXH_20250904T124917, S2C_MSIL2A_20250914T073631_R092_T36KWG_20250914T141320, S2C_MSIL2A_20250914T073631_R092_T36KXG_20250914T141320, S2C_MSIL2A_20250914T073631_R092_T36LWH_20250914T141320, S2C_MSIL2A_20250914T073631_R092_T36LXH_20250914T141320, S2C_MSIL2A_20250924T073651_R092_T36KWG_20250924T130114, S2C_MSIL2A_20250924T073651_R092_T36KXG_20250924T130114, S2C_MSIL2A_20250924T073651_R092_T36LWH_20250924T130114, S2C_MSIL2A_20250924T073651_R092_T36LXH_20250924T130114, S2C_MSIL2A_20251014T073911_R092_T36KWG_20251014T111716, S2C_MSIL2A_20251014T073911_R092_T36KXG_20251014T111716, S2C_MSIL2A_20251014T073911_R092_T36LWH_20251014T111716, S2C_MSIL2A_20251014T073911_R092_T36LXH_20251014T111716, S2C_MSIL2A_20251024T074011_R092_T36KWG_20251024T110917, S2C_MSIL2A_20251024T074011_R092_T36KXG_20251024T110917, S2C_MSIL2A_20251024T074011_R092_T36LXH_20251024T110917

<!-- SECAO_CLASSIFICACAO_INICIO -->

## Classificação — redesenho da Fase 1 (§5.1, §10)

Gerado por `pipeline/01_imagery/classificacao.py`. Substitui a versão reprovada, cujo defeito central era usar **limiares adaptativos por percentil**: eles selecionavam uma fatia quase constante da AOI todo ano (3,4–4,4%), de modo que o produto media o percentil, não o crescimento.

**Papéis das referências (escolhidos e assumidos, sem circularidade):** WSF Evolution **semeia o treino** e por isso **não** é usado como validação; GHSL BUILT-S R2023A (épocas observadas 2000–2020) é **referência independente de concordância** e não toca em treino nem em limiar; as épocas 2025/2030 do GHSL são extrapoladas e por isso 2025 fica **sem** referência de produto, declarado.

**Separação fenológica.** Features incluem `NDVI(chuva)` e a amplitude `NDVI(chuva) − NDVI(seca)` (nov(A−1)–abr(A) contra mai–out(A)). Separabilidade medida nesta AOI entre WSF-construído e não-construído (d de Cohen): amplitude 1,83 (2000) / 2,03 (2015) / 1,87 (2025); NDBI 0,39 / 0,71 / 0,29. Cobertura da estação chuvosa por ano em `data/processed/cobertura_estacao_chuvosa.csv`.

**Regras temporais declaradas.** R1: primeira detecção só vale se confirmada no ano-âncora seguinte (2025 não é confirmável — não há ano seguinte). R2: permanência, `construído(t) = ∪_{t'≤t}`. As três séries (sem restrição, após R1, após R2) estão lado a lado em `data/processed/area_construida_por_ano.csv`.

**Acurácia não é calculada aqui.** Ver `pipeline/01_imagery/acuracia.py` e `data/processed/acuracia_por_ano.csv`.

**Pegada minerária e de reassentamento — classe própria desde docs/ADR/0011.** Antes, `industrial` era `construido & poligono_maus` e `reassentamento` era `restante & buffer`: as duas camadas eram a INTERSEÇÃO da classificação de construído com uma máscara espacial, e mediam 'construído dentro do polígono', não a pegada. O defeito é físico: cava, pilha de estéril e rejeito são rocha e solo exposto — espectralmente NÃO são construído — e um classificador de construído os perde por definição (media 4,2 km² contra os 59,2 km² de Maus et al., 7,1%). A pegada passou a ser classificada por assinatura própria: solo/rocha exposto persistente (NDVI de seca E de chuva abaixo de 0.6 da mediana da paisagem do próprio ano — normalização radiométrica anual, NÃO percentil da imagem), unida ao construído do ano, dentro do envelope de Maus dilatado em 500 m. Cobertura dos polígonos de Maus em 2025: de 7,1% para 76,3%.

**Limiar calibrado, e onde isso cria circularidade.** O limiar foi calibrado por J de Youden contra Maus et al. em 2020, o ano-âncora de menor defasagem em relação à referência. Logo **a concordância com Maus em 2020 não é validação independente**. A evidência independente é temporal: a mesma regra devolve **0,000 km² em 2000 e 2005**, antes da licença da Vale (2006) — placebo temporal que se mantém nas 30 configurações de `data/processed/pegada_sensibilidade.csv`.

**`industrial` e `reassentamento` NÃO são subconjuntos de `construido`.** Elas incluem rocha e solo exposto. Consequência aritmética: `urbano + industrial + reassentamento > area_construida`, e **só `urbano` é área construída** — a soma das três não tem significado. A máscara de construído é publicada à parte, em `construido_<ano>_30m_32736.tif`, e é ela que define o estrato da validação de acurácia.

**O que não mudou, verificado e não presumido:** a classificação de construído é idêntica à anterior (o raio de exclusão de negativos do treino foi mantido em 1500 m, separado do raio de detecção de 1000 m); os 288 pontos de validação não se moveram (0 de 288); `data/processed/acuracia_por_ano.csv` é idêntico por diff e a acurácia do usuário de `construido` continua 0,286-0,625 (docs/ADR/0009); `urbano` dentro dos polígonos de mineração continua 0,0000 km² de 2010 em diante. O único efeito sobre `urbano` é a migração de construído do envelope minerário (planta, pátio ferroviário) para `industrial`: 44,02 -> 42,84 km² em 2025.

**Camada de reassentamento — incompleta por falta de dado:** Buffer de 1000 m em torno do ponto único de cada povoado (não há polígono de traçado real de nível A) delimitando ONDE PROCURAR. Dentro dele a camada é a pegada: solo exposto persistente (mesma regra e mesmo limiar razao_verde < 0.6 da pegada minerária) em união com o construído do ano. **A detecção não exige assinatura de construído** — foi esse o defeito corrigido: habitação de reassentamento é baixa, esparsa e de telhado metálico ou fibrocimento, e a 30 m um classificador de construído a perde (a camada anterior media 0,07 km², cerca de um décimo do piso plausível). **O que a camada mede é a pegada do povoado — lotes, vias e terreno alterado — não a área de telhado.** **A camada continua incompleta e isso é estrutural, não um bug**: o povoado urbano '25 de Setembro' (289 famílias, HRW 2013) tem `geometry: null` em data/raw/reassentamentos.geojson — Nominatim e Overpass não o localizaram e a coordenada não foi inventada. Consequência aritmética: o construído do 25 de Setembro está contado dentro de `urbano`, isto é, `urbano` inclui crescimento por reassentamento que §10 manda separar. A magnitude desse vazamento não é estimável sem a geometria.

### Ano-âncora 2000

- **Método `industrial`:** classe própria de solo/rocha exposto persistente (razao_verde < 0.6) dentro do envelope de Maus et al. dilatado em 500 m, união com o construído do ano no mesmo envelope. Resultado 0,00 km²: PLACEBO TEMPORAL — a concessão da Vale é de 2004 e a licença de 2006, então a regra tinha de devolver ~zero aqui, e devolve. Sem acumulação (anterior a 2006).
- **Área construída (km²):** sem restrição 16.9 · após R1 13.8 · após R2 (publicada) 13.8
- **Camadas (km²):** urbano=13.81, industrial=0.00, reassentamento=0.00, vegetacao=235.34, solo_exposto=2219.66, agua=30.34 (industrial e reassentamento são PEGADAS, não subconjuntos de construído)
- **Pegada sem permanência (km²):** industrial=0.00, reassentamento=0.00 · cobertura dos polígonos de Maus: 0.0% · mediana NDVI(chuva) da paisagem: 0.474
- **Importância das features (5 maiores):** ndvi=0.482, evi=0.171, ndwi=0.107, ndbi=0.050, nir=0.039

### Ano-âncora 2005

- **Método `industrial`:** mesma regra de 2000. Resultado 0,00 km²: segundo ponto do placebo temporal, um ano antes da licença. Sem acumulação (anterior a 2006).
- **Área construída (km²):** sem restrição 23.6 · após R1 20.5 · após R2 (publicada) 20.5
- **Camadas (km²):** urbano=20.48, industrial=0.00, reassentamento=0.00, vegetacao=239.83, solo_exposto=2202.24, agua=31.94 (industrial e reassentamento são PEGADAS, não subconjuntos de construído)
- **Pegada sem permanência (km²):** industrial=0.00, reassentamento=0.00 · cobertura dos polígonos de Maus: 0.0% · mediana NDVI(chuva) da paisagem: 0.543
- **Importância das features (5 maiores):** ndvi=0.441, evi=0.190, ndwi=0.106, ndbi=0.045, red=0.040

### Ano-âncora 2010

- **Método `industrial`:** solo/rocha exposto persistente + construído, dentro do envelope, acumulado desde 2006. Obras desde ~2007; a mina só opera em mai/2011, então a pegada aqui é de decapagem e canteiro, não de lavra plena.
- **Área construída (km²):** sem restrição 33.3 · após R1 28.9 · após R2 (publicada) 29.9
- **Camadas (km²):** urbano=28.16, industrial=7.43, reassentamento=1.20, vegetacao=254.31, solo_exposto=2168.11, agua=36.83 (industrial e reassentamento são PEGADAS, não subconjuntos de construído)
- **Pegada sem permanência (km²):** industrial=7.43, reassentamento=1.20 · cobertura dos polígonos de Maus: 7.0% · mediana NDVI(chuva) da paisagem: 0.477
- **Importância das features (5 maiores):** ndvi=0.369, ndwi=0.150, evi=0.141, red=0.072, ndbi=0.053

### Ano-âncora 2015

- **Método `industrial`:** solo/rocha exposto persistente + construído, dentro do envelope, acumulado desde 2006. Operação da Vale desde 2011 e Benga desde 2012. O envelope vem de imagem 2017-2019, POSTERIOR a este ano: parte dele ainda não era lavra em 2015, e é por isso que a extensão é medida pela assinatura do ano e não pelo polígono.
- **Área construída (km²):** sem restrição 55.6 · após R1 39.6 · após R2 (publicada) 41.7
- **Camadas (km²):** urbano=37.28, industrial=31.55, reassentamento=1.65, vegetacao=139.82, solo_exposto=2247.47, agua=37.27 (industrial e reassentamento são PEGADAS, não subconjuntos de construído)
- **Pegada sem permanência (km²):** industrial=31.55, reassentamento=1.65 · cobertura dos polígonos de Maus: 45.9% · mediana NDVI(chuva) da paisagem: 0.670
- **Importância das features (5 maiores):** ndvi=0.336, ndwi=0.153, evi=0.118, red=0.072, mndwi=0.068

### Ano-âncora 2020

- **Método `industrial`:** solo/rocha exposto persistente + construído, dentro do envelope, acumulado desde 2006. Defasagem de ~1 ano em relação à referência — é neste ano que o limiar foi calibrado, e por isso a concordância com Maus em 2020 não é validação independente.
- **Área construída (km²):** sem restrição 42.0 · após R1 38.6 · após R2 (publicada) 44.3
- **Camadas (km²):** urbano=39.46, industrial=41.49, reassentamento=0.70, vegetacao=302.44, solo_exposto=2074.27, agua=39.96 (industrial e reassentamento são PEGADAS, não subconjuntos de construído)
- **Pegada sem permanência (km²):** industrial=41.49, reassentamento=0.70 · cobertura dos polígonos de Maus: 59.2% · mediana NDVI(chuva) da paisagem: 0.579
- **Importância das features (5 maiores):** ndvi=0.413, evi=0.176, ndwi=0.118, ndbi=0.053, red=0.042

### Ano-âncora 2025

- **Método `industrial`:** solo/rocha exposto persistente + construído, dentro do envelope, acumulado desde 2006. Defasagem de ~6 anos: o envelope dilatado em 500 m admite avanço de lavra posterior a 2019, mas expansão além dessa faixa fica fora e é subestimação declarada.
- **Área construída (km²):** sem restrição 39.6 · após R1 39.6 · após R2 (publicada) 50.3
- **Camadas (km²):** urbano=43.10, industrial=56.68, reassentamento=1.09, vegetacao=298.46, solo_exposto=2060.72, agua=41.22 (industrial e reassentamento são PEGADAS, não subconjuntos de construído)
- **Pegada sem permanência (km²):** industrial=56.68, reassentamento=1.09 · cobertura dos polígonos de Maus: 70.5% · mediana NDVI(chuva) da paisagem: 0.331
- **Importância das features (5 maiores):** ndvi=0.347, evi=0.238, ndwi=0.134, ndbi=0.061, swir22=0.048

<!-- SECAO_CLASSIFICACAO_FIM -->

<!-- SECAO_ACURACIA_INICIO -->

## Validação de acurácia (Fase 1, §5.1 e §10)

Gerado por `pipeline/01_imagery/acuracia.py`. **Não editar à mão.**

**Natureza do rótulo de referência.** Os 288 pontos (24 por estrato por ano, 6 anos) foram rotulados por **interpretação visual automatizada** de recortes RGB (R=SWIR1, G=NIR, B=vermelho) do composto de estação seca do próprio ano, em duas janelas por ponto — contexto de 3,0 km e detalhe de 0,9 km, a 30 m. O intérprete é um **modelo de linguagem multimodal**, não um intérprete humano treinado e não verdade de campo. **Isto não é fotointerpretação** e não é chamado assim em nenhum artefato. O erro do intérprete entra no número como se fosse erro do mapa; a 30 m, construído esparso e solo exposto são frequentemente indistinguíveis para qualquer intérprete.

**Cegamento.** As folhas de contato exibem `id_cego`, atribuído sobre uma permutação determinística que mistura os dois estratos. O intérprete não sabia, ao olhar o recorte, se o mapa classificava aquele pixel como construído. Sem isso a concordância mediria a pista, não a imagem.

**Estimador.** Olofsson et al. (2014) generalizado para **reúso da amostra sob o desenho congelado** (docs/ADR/0014): os estratos e os pesos `W_h` são os do mapa vigente **na época do sorteio** (`amostra_interpretada.csv`), e a classe do mapa **atual** em cada ponto é lida do raster do ano. Quando os dois mapas coincidem, a expressão colapsa na eq. 4 de Olofsson. **Consequência declarada:** a amostra não foi otimizada para os estratos do mapa atual, e o número correto de fazer depois de uma reclassificação é uma NOVA rodada de interpretação sobre `pontos_validacao.csv` (que já foi redesenhado e está sem rótulo). Até lá, este é um estimador não viesado mas de variância subótima para o mapa vigente.

**Intérprete(s):** Claude (modelo multimodal, Anthropic) — interpretação visual de recortes RGB; NÃO é fotointerpretação humana nem verdade de campo

| ano | n | AG | IC95 AG | kappa | AU construído | IC95 AU | AP construído | IC95 AP | indet. | W construído | alavanca de 1 ponto |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 2000 | 48 | 0.997 | ±0.001 | 0.665 | 0.524 | ±0.218 | 0.917 | ±0.160 | 1 | 0.0056 | 0.0414 |
| 2005 | 48 | 0.997 | ±0.002 | 0.755 | 0.609 | ±0.204 | 1.000 | ±0.000 | 0 | 0.0083 | 0.0413 |
| 2010 | 48 | 0.992 | ±0.002 | 0.442 | 0.286 | ±0.198 | 1.000 | ±0.000 | 4 | 0.0118 | 0.0449 |
| 2015 | 48 | 0.951 | ±0.084 | 0.239 | 0.591 | ±0.210 | 0.164 | ±0.273 | 1 | 0.0155 | 0.0428 |
| 2020 | 48 | 0.868 | ±0.133 | 0.073 | 0.476 | ±0.218 | 0.055 | ±0.060 | 1 | 0.0165 | 0.0410 |
| 2025 | 48 | 0.993 | ±0.004 | 0.766 | 0.625 | ±0.198 | 1.000 | ±0.000 | 0 | 0.0193 | 0.0409 |

AG = acurácia global · AU = acurácia do usuário (1 − comissão) · AP = acurácia do produtor (1 − omissão).

**Como ler estes números, e como não ler.**

1. A **acurácia global** cumpre a meta de §10 (≥ 0,85) em todos os anos, mas essa comparação é fraca aqui: o estrato `nao_construido` ocupa 98–99,5 % da AOI, e um mapa que errasse *toda* a classe construída ainda teria acurácia global ≈ 0,98. A meta de §10 não discrimina neste desenho.
2. O que informa sobre a classe de interesse é a **acurácia do usuário**: 0,286–0,625. Cerca de metade dos pixels que o mapa chama de construído não parecem construídos ao intérprete — **comissão alta e consistente**, pior em 2010. É coerente com o viés já documentado no ADR 0008 e com a confusão solo exposto × construído na savana semiárida em estação seca.
3. A **acurácia do produtor não é utilizável neste n**. A coluna `alavanca de 1 ponto` é a fração da área da AOI que **um único** ponto de referência do estrato `nao_construido` carrega no estimador (≈ 0,041). Em 2020, 3 pontos desse estrato foram lidos como construídos, o que projeta ~12 % da AOI como construído não mapeado — implausível. O valor de 0,07 mede a fragilidade do desenho, não o mapa.
4. O **kappa** cai a 0,09–0,23 em 2015 e 2020 e não atinge a meta de 0,70 em 2010, 2015 e 2020. Kappa é instável para classe rara; é reportado por exigência de §5.1, não como critério.

**O que seria preciso para estreitar o intervalo.** O IC da acurácia global chega a ±0,133 (2020). A largura é dominada pelo estrato `nao_construido`, cuja variância escala com `W²/n`. Levar o IC de 2020 de ±0,13 para ±0,03 exigiria ~n=24 → ~n=470 pontos nesse estrato **por ano** (o IC escala com 1/√n), isto é, cerca de 2 800 recortes interpretados um a um em vez de 288. Isso não é atingível por interpretação neste ambiente; seria atingível com verdade de campo, com imagem de resolução submétrica (fora do nível A), ou aceitando um rotulador automático — que é exatamente o que reprovou a versão anterior.

**Papel do WSF Evolution.** Semeia o treino; por construção **não valida**. Nenhuma métrica contra WSF aparece em `acuracia_por_ano.csv`. A concordância está em `data/processed/concordancia_wsf.csv`, rotulada como concordância entre produtos com dependência por construção.

<!-- SECAO_ACURACIA_FIM -->
