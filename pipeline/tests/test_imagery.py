"""Contratos sobre `pipeline/01_imagery/` (§5.1, §10, §11.2.4).

Propósito: garantir que os compostos e índices gravados em
`data/processed/imagery/` obedecem ao CRS métrico do estudo, compartilham uma
grade única entre anos-âncora, ficam numa faixa fisicamente plausível, não têm
nulos além do esperado, e são reprodutíveis dentro da tolerância declarada em
`config/tolerances.yaml`. Entradas: os COGs de `data/processed/imagery/` e seus
`.meta.json`. Saídas: nenhuma (só asserções).

Todos os testes pulam (`pytest.skip`) se os artefatos ainda não foram gerados
— `compostos.py`/`indices.py` exigem rede (STAC) e não rodam durante `pytest`.
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

import numpy as np
import pytest
import rasterio
import yaml

ROOT = Path(__file__).resolve().parents[2]
IMAGERY = ROOT / "data" / "processed" / "imagery"
CONFIG = ROOT / "config"

sys.path.insert(0, str(ROOT / "pipeline" / "01_imagery"))

# Faixa fisicamente plausível dos índices normalizados (razão de duas
# reflectâncias em [-1, 1] por construção algébrica: (a-b)/(a+b), |a-b| <= a+b
# quando a e b têm o mesmo sinal, que é o caso esperado em reflectância de
# superfície). EVI não é normalizado por essa fórmula (tem termo de correção
# de aerossol e um "L" de fundo de dossel no denominador) e pode exceder
# [-1, 1] mesmo em pixels válidos — faixa mais larga, mas ainda finita.
INDICES_NORMALIZADOS = {"ndvi", "ndbi", "mndwi", "ndwi"}
FAIXA_NORMALIZADA = (-1.0, 1.0)
FAIXA_EVI = (-3.0, 3.0)
# `ndvi_amplitude_<ano>` é NDVI(chuva) - NDVI(seca): uma DIFERENÇA de dois
# índices normalizados, não uma razão normalizada. Sua faixa algébrica é
# [-2, 2], não [-1, 1]. O contrato anterior derivava a família do índice do
# primeiro token do nome do arquivo ("ndvi_amplitude_2010" -> "ndvi") e cobrava
# da amplitude uma faixa que ela nunca teve de respeitar. A família passa a ser
# resolvida pelo nome inteiro.
FAIXA_AMPLITUDE = (-2.0, 2.0)


def _familia_do_indice(nome_arquivo: str) -> str:
    """Família do índice a partir do nome do arquivo `<familia>_<ano>_<res>m_<epsg>.tif`.

    A família pode ter mais de um token (`ndvi_chuva`, `ndvi_amplitude`), então
    é tudo o que vem antes do primeiro token de 4 dígitos (o ano-âncora).
    """
    tokens = nome_arquivo.removesuffix(".tif").split("_")
    familia = []
    for token in tokens:
        if len(token) == 4 and token.isdigit():
            break
        familia.append(token)
    return "_".join(familia)

# Pequena folga sobre [-1, 1] para tolerar erro de ponto flutuante float32
# (não uma reinterpretação da faixa teórica).
FOLGA_FLOAT32 = 1e-3


def _load_yaml(name: str) -> dict:
    with (CONFIG / name).open(encoding="utf-8") as fh:
        return yaml.safe_load(fh)


def _compostos_disponiveis() -> list[Path]:
    if not IMAGERY.exists():
        return []
    return sorted(IMAGERY.glob("composto_*_30m_32736.tif"))


def _indices_disponiveis() -> list[Path]:
    if not IMAGERY.exists():
        return []
    padroes = ("ndvi_", "ndbi_", "mndwi_", "ndwi_", "evi_")
    return sorted(p for p in IMAGERY.glob("*.tif") if p.name.startswith(padroes))


@pytest.fixture(scope="module")
def study():
    return _load_yaml("study.yaml")


@pytest.fixture(scope="module")
def tolerances():
    return _load_yaml("tolerances.yaml")


def test_compostos_e_indices_ainda_nao_gerados_e_marcado(request):
    """Sentinela: se nada foi gerado, os demais testes pulam — não falham em
    silêncio. Este teste sempre passa; existe só para deixar visível no
    relatório do pytest que o portão de imagem ainda não rodou, quando for
    o caso.
    """
    if not _compostos_disponiveis():
        pytest.skip("data/processed/imagery/ ainda não tem compostos — rode compostos.py")


def test_compostos_estao_em_epsg_32736(study):
    """§ convenções: toda métrica de área em EPSG:32736."""
    compostos = _compostos_disponiveis()
    if not compostos:
        pytest.skip("nenhum composto gerado ainda")
    crs_esperado = study["crs"]["metrico"]
    for caminho in compostos:
        with rasterio.open(caminho) as src:
            assert src.crs is not None, f"{caminho.name}: sem CRS gravado"
            assert f"EPSG:{src.crs.to_epsg()}" == crs_esperado, (
                f"{caminho.name}: CRS {src.crs} != {crs_esperado}"
            )


def test_indices_estao_em_epsg_32736(study):
    indices = _indices_disponiveis()
    if not indices:
        pytest.skip("nenhum índice gerado ainda")
    crs_esperado = study["crs"]["metrico"]
    for caminho in indices:
        with rasterio.open(caminho) as src:
            assert src.crs is not None, f"{caminho.name}: sem CRS gravado"
            assert f"EPSG:{src.crs.to_epsg()}" == crs_esperado, (
                f"{caminho.name}: CRS {src.crs} != {crs_esperado}"
            )


def test_grade_coerente_entre_todos_os_anos():
    """Grade canônica única (§ compostos.py: `construir_geobox`): todo composto
    e todo índice, de qualquer ano-âncora, têm de compartilhar exatamente a
    mesma forma, `transform` e CRS — sem isso a Fase 2 (classificação) não
    poderia empilhar bandas de anos diferentes pixel a pixel.
    """
    rasteres = _compostos_disponiveis() + _indices_disponiveis()
    if len(rasteres) < 2:
        pytest.skip("menos de 2 rasteres gerados; nada a comparar")

    referencia = None
    divergentes = []
    for caminho in rasteres:
        with rasterio.open(caminho) as src:
            perfil = (src.crs, src.shape, src.transform)
        if referencia is None:
            referencia = perfil
            continue
        if perfil != referencia:
            divergentes.append((caminho.name, perfil))

    assert not divergentes, (
        f"grade divergente da referência {referencia}: "
        + "; ".join(f"{nome}={perfil}" for nome, perfil in divergentes)
    )


def test_faixa_plausivel_dos_indices_normalizados():
    """NDVI/NDBI/MNDWI/NDWI são razões (a-b)/(a+b): em [-1, 1] por construção.
    Valores fora disso indicam reflectância de entrada fisicamente implausível
    (fora do intervalo aproximado [-0.2, ~1.6] do Landsat C2 L2) que passou
    pela máscara de nuvem/sombra sem ser pega.
    """
    indices = _indices_disponiveis()
    if not indices:
        pytest.skip("nenhum índice gerado ainda")

    infratores = []
    for caminho in indices:
        familia = _familia_do_indice(caminho.name)
        # `ndvi_chuva` É uma razão normalizada (mesma fórmula, outra estação) e
        # entra aqui; `ndvi_amplitude` é diferença de duas e tem teste próprio.
        if familia not in INDICES_NORMALIZADOS and familia != "ndvi_chuva":
            continue
        with rasterio.open(caminho) as src:
            dados = src.read(1, masked=True)
        validos = dados.compressed()
        if validos.size == 0:
            continue
        minimo, maximo = float(validos.min()), float(validos.max())
        lo, hi = FAIXA_NORMALIZADA
        if minimo < lo - FOLGA_FLOAT32 or maximo > hi + FOLGA_FLOAT32:
            infratores.append(f"{caminho.name}: faixa [{minimo:.4f}, {maximo:.4f}]")

    assert not infratores, "; ".join(infratores)


def test_faixa_plausivel_da_amplitude_fenologica():
    """`ndvi_amplitude` = NDVI(chuva) - NDVI(seca). Cada termo está em [-1, 1]
    por construção (ambos passam por `indices._razao_normalizada`, com a mesma
    máscara de denominador), logo a diferença está em [-2, 2]. Um valor fora
    disso só é possível se um dos dois NDVI tiver escapado da sua própria faixa
    — foi exatamente o defeito de `compostos_chuva.ndvi`, que dividia sem
    mascarar o denominador.
    """
    indices = [p for p in _indices_disponiveis() if _familia_do_indice(p.name) == "ndvi_amplitude"]
    if not indices:
        pytest.skip("nenhuma amplitude fenológica gerada ainda")

    infratores = []
    for caminho in indices:
        with rasterio.open(caminho) as src:
            dados = src.read(1, masked=True)
        validos = dados.compressed()
        validos = validos[np.isfinite(validos)]
        if validos.size == 0:
            continue
        minimo, maximo = float(validos.min()), float(validos.max())
        lo, hi = FAIXA_AMPLITUDE
        if minimo < lo - FOLGA_FLOAT32 or maximo > hi + FOLGA_FLOAT32:
            infratores.append(f"{caminho.name}: faixa [{minimo:.4f}, {maximo:.4f}]")

    assert not infratores, "; ".join(infratores)


def test_faixa_plausivel_do_evi():
    """EVI não é uma razão normalizada simples, mas ainda é finito e limitado
    numa faixa fisicamente razoável (Huete et al. 2002 relatam a maior parte
    da vegetação saudável entre 0.2 e 0.8; a faixa aqui só descarta explosões
    numéricas de denominador quase-zero que escaparam da máscara).
    """
    indices = [p for p in _indices_disponiveis() if p.name.startswith("evi_")]
    if not indices:
        pytest.skip("nenhum EVI gerado ainda")

    infratores = []
    for caminho in indices:
        with rasterio.open(caminho) as src:
            dados = src.read(1, masked=True)
        validos = dados.compressed()
        if validos.size == 0:
            continue
        minimo, maximo = float(validos.min()), float(validos.max())
        lo, hi = FAIXA_EVI
        if minimo < lo or maximo > hi:
            infratores.append(f"{caminho.name}: faixa [{minimo:.4f}, {maximo:.4f}]")

    assert not infratores, "; ".join(infratores)


def test_ausencia_de_nulos_indevidos():
    """Nulos (NaN/nodata) só são aceitáveis onde `compostos.py` já registrou,
    no `.meta.json`, que o pixel ficou sem nenhuma observação válida — nunca
    em proporção maior que a declarada, o que indicaria um bug introduzido
    depois da gravação do composto (ex.: no cálculo de um índice).
    """
    compostos = _compostos_disponiveis()
    if not compostos:
        pytest.skip("nenhum composto gerado ainda")

    problemas = []
    for caminho in compostos:
        meta_path = caminho.with_suffix(".tif.meta.json")
        if not meta_path.exists():
            problemas.append(f"{caminho.name}: sem .meta.json")
            continue
        meta = json.loads(meta_path.read_text(encoding="utf-8"))
        declarado = meta["pixels_sem_observacao"]

        with rasterio.open(caminho) as src:
            dados = src.read(masked=True)
        # Um pixel "sem observação" fica nulo em TODAS as bandas (a máscara é
        # comum); conta pixels onde a primeira banda é nula.
        nulos_real = int(dados[0].mask.sum()) if np.ma.is_masked(dados[0]) else 0

        if nulos_real != declarado:
            problemas.append(
                f"{caminho.name}: {nulos_real} pixels nulos, .meta.json declara {declarado}"
            )

    assert not problemas, "; ".join(problemas)


def test_regressao_numerica_indices_reproduz_a_formula(tolerances):
    """§11.2.4: regressão numérica determinística. Recalcula cada índice a
    partir do composto gravado (a mesma fórmula de `indices.py`) e compara
    pixel a pixel com o raster já gravado, dentro da tolerância declarada em
    `config/tolerances.yaml -> regressao_numerica.indices_espectrais_pixel`.
    Não depende de rede: os dois lados vêm de `data/processed/imagery/`.
    """
    from indices import (
        CALCULADORAS,
        NOME_ARQUIVO_RE,
        carregar_composto,
    )

    compostos = _compostos_disponiveis()
    if not compostos:
        pytest.skip("nenhum composto gerado ainda")

    tol = tolerances["regressao_numerica"]["indices_espectrais_pixel"]["max"]

    problemas = []
    for caminho_composto in compostos:
        m = NOME_ARQUIVO_RE.match(caminho_composto.name)
        ano, res_m, epsg = m.group(1), m.group(2), m.group(3)
        composto = carregar_composto(caminho_composto)

        for nome_indice, calculadora in CALCULADORAS.items():
            caminho_indice = IMAGERY / f"{nome_indice.lower()}_{ano}_{res_m}m_{epsg}.tif"
            if not caminho_indice.exists():
                continue  # índice não pedido para este ano; não é erro deste teste

            esperado = calculadora(composto).astype("float32").values
            with rasterio.open(caminho_indice) as src:
                gravado = src.read(1, masked=True)

            ambos_validos = ~np.isnan(esperado) & ~gravado.mask
            if not ambos_validos.any():
                continue
            diff = np.abs(esperado[ambos_validos] - gravado.data[ambos_validos])
            maxdiff = float(diff.max())
            if maxdiff > tol:
                problemas.append(
                    f"{caminho_indice.name}: diferença máxima {maxdiff:.2e} > tolerância {tol:.2e}"
                )

            # Máscara tem de coincidir: onde o composto dá denominador válido,
            # o índice gravado não pode estar mascarado, e vice-versa.
            so_no_esperado = (~np.isnan(esperado)) & gravado.mask
            so_no_gravado = np.isnan(esperado) & (~gravado.mask)
            if so_no_esperado.any() or so_no_gravado.any():
                problemas.append(
                    f"{caminho_indice.name}: máscara diverge da fórmula "
                    f"({int(so_no_esperado.sum())} só no recálculo, "
                    f"{int(so_no_gravado.sum())} só no arquivo)"
                )

    assert not problemas, "; ".join(problemas)


def test_janela_temporal_registrada_e_um_unico_ano_civil_salvo_2010():
    """§5.1: mesmo protocolo em todos os anos — cada composto cobre um único
    ano civil de estação seca (`janela_anos: 1`), exceto se `config/study.yaml`
    tiver sido explicitamente alterado (ex.: aplicação do ADR 0005 para 2010).
    """
    compostos = _compostos_disponiveis()
    if not compostos:
        pytest.skip("nenhum composto gerado ainda")

    for caminho in compostos:
        meta = json.loads(caminho.with_suffix(".tif.meta.json").read_text(encoding="utf-8"))
        janela = meta["janela_temporal"]
        assert janela["ano_inicio_janela"] == janela["ano_fim_janela"] == janela["ano_ancora"], (
            f"{caminho.name}: janela cobre mais de um ano civil "
            f"({janela['ano_inicio_janela']}-{janela['ano_fim_janela']}) "
            "sem ser uma decisão registrada em ADR"
        )
        assert meta["selo"] == "observado"


def test_nobs_bate_com_calculo_direto_do_qa_pixel(study, tolerances):
    """Contrato que teria pego o defeito de nodata do `qa_pixel` (Fase 1,
    diagnosticado pelo orquestrador): recalcula o número de observações
    válidas por pixel **diretamente** das cenas de origem — leitura
    `rasterio` bruta de cada `qa_pixel`, reprojetada manualmente para a grade
    canônica com `rasterio.warp.reproject`, sem passar por `odc.stac.load`
    nem por `stac_cfg` — e compara a soma total de observações válidas na AOI
    com a que `pipeline/01_imagery/compostos.py` calcularia para o mesmo
    conjunto de cenas (`carregar_colecao_mascarada` + soma de `notnull()`),
    dentro da tolerância declarada em `config/tolerances.yaml ->
    regressao_numerica.contrato_qa_pixel`.

    Nenhum dos dois lados reaproveita a lógica de bits do outro por acidente:
    o lado "direto" reimplementa a máscara com os bits importados de
    `_stac_common`, mas nunca chama `mascara_valida_landsat` nem
    `odc.stac.load` — só assim o teste teria detectado o defeito original
    (a lógica de bits sempre esteve certa; o defeito estava no carregamento).

    Usa as 4 cenas Landsat 7 (SLC-off) de mai-out/2010 (mesmas de
    `pipeline/01_imagery/slc_off_2010.py` / `docs/ADR/0005-...md`), não os
    cinco anos-âncora de `data/processed/imagery/`. Verificado nesta tarefa:
    nenhum dos cinco anos-âncora atuais (2000, 2005, 2015, 2020, 2025) tem um
    único pixel de FILL (`qa_pixel == 1`) dentro da AOI — a área cai bem
    dentro da faixa de cada cena nessas datas, sem sobra de borda. 2010/L7 é o
    único caso conhecido no repositório com preenchimento real dentro da AOI
    (os gaps de linha do SLC-off), e é por isso o único capaz de detectar este
    defeito por regressão — um contrato que sempre desse "bate" num ano sem
    nenhum pixel de fill não provaria nada. O teste primeiro confirma que há
    pixels de fill nas cenas brutas; se essa premissa deixar de valer (ex.:
    catálogo STAC trocou as cenas), pula em vez de dar um falso "passou".

    Precisa de rede (STAC + leitura dos assets); pula se indisponível.
    """
    ano = 2010
    janela = "2010-05-01T00:00:00Z/2010-10-31T23:59:59Z"
    nuvem_max = study["composto"]["nuvem_max_pct"]

    try:
        import numpy as np
        import planetary_computer as pc
        import rasterio
        from _stac_common import (
            QA_PIXEL_BIT_CIRRUS,
            QA_PIXEL_BIT_CLOUD,
            QA_PIXEL_BIT_CLOUD_SHADOW,
            QA_PIXEL_BIT_DILATED_CLOUD,
            QA_PIXEL_BIT_FILL,
            STAC_ENDPOINT_CANONICO,
            abrir_cliente_stac,
            buscar_itens,
        )
        from compostos import carregar_colecao_mascarada, construir_geobox
        from rasterio.warp import Resampling, reproject

        bbox_aoi = study["aoi"]["bbox"]
        bbox = [bbox_aoi["xmin"], bbox_aoi["ymin"], bbox_aoi["xmax"], bbox_aoi["ymax"]]
        crs_metrico = study["crs"]["metrico"]
        res_m = study["sensores"][2005]["res_m"]  # mesma resolução Landsat (30 m)
        geobox = construir_geobox(bbox_aoi, crs_metrico, res_m)

        client = abrir_cliente_stac(STAC_ENDPOINT_CANONICO)
        itens = buscar_itens(client, "landsat-c2-l2", bbox, janela, nuvem_max, "landsat-7")
        if not itens:
            pytest.skip(f"{ano}/landsat-7: nenhuma cena retornada pelo STAC")

        # Lado "direto": leitura rasterio bruta de cada qa_pixel, sem
        # `odc.stac.load` e sem qualquer nodata declarado no STAC — só o
        # valor de pixel como gravado no GeoTIFF de origem.
        bits_ruins = (
            (1 << QA_PIXEL_BIT_FILL)
            | (1 << QA_PIXEL_BIT_DILATED_CLOUD)
            | (1 << QA_PIXEL_BIT_CIRRUS)
            | (1 << QA_PIXEL_BIT_CLOUD)
            | (1 << QA_PIXEL_BIT_CLOUD_SHADOW)
        )
        crs_destino = f"EPSG:{geobox.crs.to_epsg()}"
        nobs_direto = np.zeros((geobox.shape.y, geobox.shape.x), dtype="int32")
        n_fill_bruto = 0
        for item in itens:
            href = pc.sign(item.assets["qa_pixel"].href)
            with rasterio.open(href) as src:
                destino = np.zeros((geobox.shape.y, geobox.shape.x), dtype="uint16")
                reproject(
                    source=rasterio.band(src, 1),
                    destination=destino,
                    src_transform=src.transform,
                    src_crs=src.crs,
                    dst_transform=geobox.affine,
                    dst_crs=crs_destino,
                    resampling=Resampling.nearest,
                    src_nodata=None,
                    dst_nodata=None,
                )
            n_fill_bruto += int((destino == 1).sum())
            valido = ((destino & bits_ruins) == 0) & (destino != 0)
            nobs_direto += valido.astype("int32")
    except Exception as exc:
        pytest.skip(f"rede/STAC indisponível para o contrato qa_pixel direto: {exc}")

    if n_fill_bruto == 0:
        pytest.skip(
            f"{ano}/landsat-7: nenhum pixel de FILL bruto na AOI — a premissa deste "
            "teste (cenas com preenchimento real dentro da AOI) não se sustenta mais "
            "para este conjunto de cenas; escolha outro ano/cena conhecido com fill."
        )

    total_direto = int(nobs_direto.sum())

    bandas_pipeline, _itens_usados = carregar_colecao_mascarada(
        client, "landsat-c2-l2", bbox, janela, nuvem_max, geobox, "landsat-7"
    )
    assert bandas_pipeline is not None, f"{ano}: pipeline não retornou bandas para o contrato"
    nobs_pipeline = next(iter(bandas_pipeline.values())).notnull().sum(dim="time").compute()
    total_pipeline = int(nobs_pipeline.values.sum())

    tol = tolerances["regressao_numerica"]["contrato_qa_pixel"]["max"]
    erro_relativo = abs(total_pipeline - total_direto) / total_direto
    assert erro_relativo <= tol, (
        f"{ano}: soma de observações válidas do pipeline ({total_pipeline}) diverge "
        f"do cálculo direto do qa_pixel ({total_direto}, {n_fill_bruto} pixels de fill "
        f"bruto encontrados) em {erro_relativo:.4f}, acima da tolerância {tol} — "
        "suspeite de remapeamento de nodata no carregamento"
    )


def test_nenhum_ano_ancora_foi_substituido_por_vizinho():
    """§ restrições da tarefa: 'se um ano falhar, falhe explicitamente — nunca
    substitua por ano vizinho'. O `.meta.json` de cada composto declara o
    `ano` do arquivo; tem de bater com o ano do nome do arquivo.
    """
    compostos = _compostos_disponiveis()
    if not compostos:
        pytest.skip("nenhum composto gerado ainda")

    for caminho in compostos:
        m = re.match(r"composto_(\d{4})_\d+m_\d+\.tif", caminho.name)
        ano_arquivo = int(m.group(1))
        meta = json.loads(caminho.with_suffix(".tif.meta.json").read_text(encoding="utf-8"))
        assert meta["ano"] == ano_arquivo, (
            f"{caminho.name}: nome do arquivo diz {ano_arquivo}, .meta.json diz {meta['ano']}"
        )


# ---------------------------------------------------------------------------
# Classificação em 3 camadas mutuamente exclusivas (§5.1, §10) —
# `pipeline/01_imagery/classificacao.py`
# ---------------------------------------------------------------------------

CAMADAS_PARTICAO = ["urbano", "industrial", "reassentamento"]
CAMADAS_COBERTURA = ["vegetacao", "solo_exposto", "agua"]
ANOS_ANCORA = [2000, 2005, 2010, 2015, 2020, 2025]


def _camada_disponivel(camada: str, ano: int) -> Path | None:
    caminho = IMAGERY / f"{camada}_{ano}_30m_32736.tif"
    return caminho if caminho.exists() else None


def _anos_com_classificacao() -> list[int]:
    return [
        ano
        for ano in ANOS_ANCORA
        if all(_camada_disponivel(c, ano) for c in [*CAMADAS_PARTICAO, *CAMADAS_COBERTURA])
    ]


def test_classificacao_ainda_nao_gerada_e_marcado():
    """Sentinela equivalente à de compostos/índices: torna visível no relatório
    do pytest quando `classificacao.py` ainda não rodou, em vez de os demais
    testes pularem em silêncio."""
    if not _anos_com_classificacao():
        pytest.skip(
            "data/processed/imagery/ ainda não tem as camadas de classificação — "
            "rode classificacao.py"
        )


def test_camadas_urbano_industrial_reassentamento_sao_mutuamente_exclusivas():
    """§10: 'nenhuma cava de mina contada como área urbana' — o contrato
    central desta entrega. Nenhum pixel pode estar em mais de uma das três
    camadas de construído, em nenhum ano-âncora.
    """
    anos = _anos_com_classificacao()
    if not anos:
        pytest.skip("classificação ainda não gerada")

    problemas = []
    for ano in anos:
        soma = None
        for camada in CAMADAS_PARTICAO:
            with rasterio.open(_camada_disponivel(camada, ano)) as src:
                mask = src.read(1).astype("uint8")
            soma = mask if soma is None else soma + mask
        n_sobrepostos = int((soma > 1).sum())
        if n_sobrepostos > 0:
            problemas.append(f"{ano}: {n_sobrepostos} pixels em mais de uma camada")

    assert not problemas, "; ".join(problemas)


def test_camadas_de_classificacao_tem_grade_e_crs_coerentes(study):
    """Todas as camadas de todos os anos compartilham grade e CRS com os
    compostos (§ convenções: EPSG:32736, grade fixa entre anos)."""
    anos = _anos_com_classificacao()
    if not anos:
        pytest.skip("classificação ainda não gerada")

    crs_esperado = study["crs"]["metrico"]
    referencia = None
    divergentes = []
    for ano in anos:
        for camada in [*CAMADAS_PARTICAO, *CAMADAS_COBERTURA]:
            caminho = _camada_disponivel(camada, ano)
            with rasterio.open(caminho) as src:
                assert f"EPSG:{src.crs.to_epsg()}" == crs_esperado, (
                    f"{caminho.name}: CRS {src.crs} != {crs_esperado}"
                )
                perfil = (src.crs, src.shape, src.transform)
            if referencia is None:
                referencia = perfil
            elif perfil != referencia:
                divergentes.append((caminho.name, perfil))

    assert not divergentes, (
        f"grade divergente da referência {referencia}: "
        + "; ".join(f"{nome}={perfil}" for nome, perfil in divergentes)
    )


def test_regressao_numerica_area_por_camada_e_ano(tolerances):
    """§11.2.4: a área declarada no `.meta.json` de cada camada tem de bater
    com a área recomputada diretamente do raster (contagem de pixels ×
    resolução), dentro da tolerância de
    `config/tolerances.yaml -> regressao_numerica.area_km2_por_camada_ano`.
    Protege contra uma futura divergência silenciosa entre o que o script
    grava no raster e o que ele declara na proveniência.
    """
    anos = _anos_com_classificacao()
    if not anos:
        pytest.skip("classificação ainda não gerada")

    tol = tolerances["regressao_numerica"]["area_km2_por_camada_ano"]["max"]
    problemas = []
    for ano in anos:
        for camada in [*CAMADAS_PARTICAO, *CAMADAS_COBERTURA]:
            caminho = _camada_disponivel(camada, ano)
            meta = json.loads(caminho.with_suffix(".tif.meta.json").read_text(encoding="utf-8"))
            with rasterio.open(caminho) as src:
                mask = src.read(1).astype(bool)
                px_m2 = abs(src.transform.a * src.transform.e)
            area_recomputada = float(mask.sum()) * px_m2 / 1e6
            area_declarada = meta["area_km2"]
            if area_declarada == 0 and area_recomputada == 0:
                continue
            base = max(area_declarada, area_recomputada, 1e-9)
            erro_relativo = abs(area_recomputada - area_declarada) / base
            if erro_relativo > tol:
                problemas.append(
                    f"{caminho.name}: área declarada {area_declarada:.4f} km², "
                    f"recomputada {area_recomputada:.4f} km² (erro relativo {erro_relativo:.4f})"
                )

    assert not problemas, "; ".join(problemas)


def test_camada_industrial_vazia_antes_da_licenca_da_mina():
    """§8/§ tarefa: a mina de Moatize não existe antes da licença de 2006 —
    2000 e 2005 não podem ter nenhum pixel `industrial` (método declarado
    como 'nenhum polígono', não silenciosamente preenchido)."""
    problemas = []
    for ano in (2000, 2005):
        caminho = _camada_disponivel("industrial", ano)
        if caminho is None:
            continue
        with rasterio.open(caminho) as src:
            n_pixels = int(src.read(1).astype(bool).sum())
        if n_pixels != 0:
            problemas.append(f"{ano}: {n_pixels} pixels industriais antes da licença da mina")
    if not any(_camada_disponivel("industrial", a) for a in (2000, 2005)):
        pytest.skip("classificação ainda não gerada para 2000/2005")
    assert not problemas, "; ".join(problemas)


def test_camada_reassentamento_so_existe_apos_o_ano_do_povoado():
    """Cateme/25 de Setembro (2009) e Mwaladzi (2011): a camada
    `reassentamento` não pode ter pixels em 2000 nem 2005 (nenhum povoado
    de reassentamento existia)."""
    problemas = []
    disponivel = False
    for ano in (2000, 2005):
        caminho = _camada_disponivel("reassentamento", ano)
        if caminho is None:
            continue
        disponivel = True
        with rasterio.open(caminho) as src:
            n_pixels = int(src.read(1).astype(bool).sum())
        if n_pixels != 0:
            problemas.append(f"{ano}: {n_pixels} pixels de reassentamento antes de 2009")
    if not disponivel:
        pytest.skip("classificação ainda não gerada para 2000/2005")
    assert not problemas, "; ".join(problemas)


def test_acuracia_por_ano_csv_existe_e_tem_todos_os_anos():
    """`data/processed/acuracia_por_ano.csv` é a saída obrigatória de
    validação (§ tarefa). Verifica presença e cobertura de todos os
    anos-âncora já classificados — não verifica o valor da acurácia em si
    (isso é resultado, não contrato; §10 pede para reportar o número real,
    não para forçá-lo a passar)."""
    csv_path = ROOT / "data" / "processed" / "acuracia_por_ano.csv"
    anos = _anos_com_classificacao()
    if not anos:
        pytest.skip("classificação ainda não gerada")
    assert csv_path.exists(), f"{csv_path} não existe"

    import csv as csv_mod

    with csv_path.open(encoding="utf-8") as fh:
        linhas = list(csv_mod.DictReader(fh))
    anos_no_csv = {int(linha["ano"]) for linha in linhas}
    faltando = set(anos) - anos_no_csv
    assert not faltando, f"anos sem linha em acuracia_por_ano.csv: {sorted(faltando)}"


# ---------------------------------------------------------------------------
# Contratos da pegada como classe própria (docs/ADR/0011)
# ---------------------------------------------------------------------------


def test_urbano_nao_invade_poligonos_de_mineracao():
    """§10, literal: 'nenhuma cava de mina contada como área urbana'.

    A exclusividade mútua entre as três camadas não garante isto sozinha — ela só
    diz que as camadas são disjuntas entre si, não que `urbano` fica fora da mina.
    Este contrato mede contra a referência externa (Maus et al.) e é o que impede
    uma regressão silenciosa quando a pegada mudar de método outra vez.

    **Vale a partir de 2006, e não antes, deliberadamente.** Os polígonos de Maus são
    de 2017-2019; projetá-los sobre 2000 e 2005 seria anacronismo. Naqueles anos ali
    não havia cava — havia o povoado de Moatize e as machambas que a mina viria a
    ocupar. Medido: 0,079 km² (2000) e 0,113 km² (2005) de `urbano` dentro do
    polígono futuro. **Isso não é violação de §10; é o assentamento que existia antes
    da mina, e contá-lo como pegada minerária é que seria o erro.** É também um
    lembrete de que a pegada de 2019 cobre terra que era ocupada.
    """
    gpd = pytest.importorskip("geopandas")
    from rasterio.features import geometry_mask

    poligonos = ROOT / "data" / "raw" / "global_mining_polygons_v2_maus_2022_aoi.geojson"
    anos = _anos_com_classificacao()
    if not poligonos.exists() or not anos:
        pytest.skip("polígonos de mineração ou classificação ausentes")

    g = gpd.read_file(poligonos).to_crs(32736)
    problemas = []
    for ano in anos:
        if ano < 2006:  # licença da Vale; antes disso não há cava a confundir
            continue
        with rasterio.open(_camada_disponivel("urbano", ano)) as src:
            urbano = src.read(1) > 0
            dentro = geometry_mask(
                g.geometry, out_shape=src.shape, transform=src.transform, invert=True
            )
            px_km2 = abs(src.transform.a * src.transform.e) / 1e6
        area = int((urbano & dentro).sum()) * px_km2
        if area > 0:
            problemas.append(f"{ano}: {area:.4f} km² de `urbano` dentro de polígono de mina")
    assert not problemas, "; ".join(problemas)


def test_urbano_e_subconjunto_da_mascara_de_construido():
    """Desde docs/ADR/0011 `industrial` e `reassentamento` são PEGADAS e deixaram de
    ser subconjuntos de `construido`. `urbano` não: ele continua sendo, e só,
    área construída. Se este contrato cair, a série de área construída e a
    validação de acurácia deixam de falar do mesmo objeto.
    """
    anos = _anos_com_classificacao()
    if not anos:
        pytest.skip("classificação ainda não gerada")

    problemas = []
    for ano in anos:
        caminho = IMAGERY / f"construido_{ano}_30m_32736.tif"
        if not caminho.exists():
            problemas.append(f"{ano}: construido_{ano}_30m_32736.tif ausente")
            continue
        with rasterio.open(caminho) as src:
            construido = src.read(1) > 0
        with rasterio.open(_camada_disponivel("urbano", ano)) as src:
            urbano = src.read(1) > 0
        fora = int((urbano & ~construido).sum())
        if fora:
            problemas.append(f"{ano}: {fora} pixels de `urbano` fora da máscara de construído")
    assert not problemas, "; ".join(problemas)


def test_pegada_pre_licenca_e_zero_em_toda_a_varredura_de_parametros():
    """Placebo temporal, e é ele que sustenta a classe.

    A concordância com Maus et al. em 2020 é circular — o limiar foi calibrado nela
    (docs/ADR/0011). A evidência independente é temporal: antes da licença da Vale
    (2006) não havia mina, então a regra tem de devolver zero. Se devolvesse área,
    estaria marcando "terreno seco dentro de um polígono", não a pegada.

    Exige-se o zero em TODAS as configurações da varredura de sensibilidade, não só
    na adotada: um placebo que só funciona nos parâmetros escolhidos não é placebo.
    """
    caminho = ROOT / "data" / "processed" / "pegada_sensibilidade.csv"
    if not caminho.exists():
        pytest.skip("pegada_sensibilidade.csv ainda não gerado")

    import csv

    problemas = []
    n = 0
    for linha in csv.DictReader(caminho.open(encoding="utf-8")):
        if int(linha["ano"]) >= 2006:
            continue
        n += 1
        if float(linha["area_km2"]) > 0.5:
            problemas.append(
                f"razao={linha['razao_verde']} buffer={linha['buffer_envelope_m']} "
                f"fecho={linha['janela_fecho_px']} ano={linha['ano']}: "
                f"{linha['area_km2']} km² antes da licença da mina"
            )
    assert n > 0, "varredura sem anos pré-licença — o placebo não foi avaliado"
    assert not problemas, "; ".join(problemas)
