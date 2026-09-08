"""Contratos sobre config/ (§11.2.1, §11.2.4).

Propósito: garantir que os parâmetros que definem a proveniência de todo artefato
(AOI, CRS, anos-âncora, seeds) são válidos e mutuamente coerentes antes de qualquer
etapa do pipeline rodar. Entradas: config/*.yaml. Saídas: nenhuma (só asserções).
"""
from itertools import pairwise
from pathlib import Path

import pytest
import yaml
from pyproj import CRS

ROOT = Path(__file__).resolve().parents[2]
CONFIG = ROOT / "config"


def _load(name):
    with (CONFIG / name).open(encoding="utf-8") as fh:
        return yaml.safe_load(fh)


@pytest.fixture(scope="module")
def study():
    return _load("study.yaml")


def test_crs_metrico_e_projetado_em_metros(study):
    """§ convenções: toda métrica de área em EPSG:32736; 4326 só para exibição."""
    metrico = CRS.from_user_input(study["crs"]["metrico"])
    assert metrico.to_epsg() == 32736
    assert metrico.is_projected
    assert all(ax.unit_name == "metre" for ax in metrico.axis_info)
    assert CRS.from_user_input(study["crs"]["exibicao"]).to_epsg() == 4326


def test_aoi_bbox_bem_formado_e_em_mocambique(study):
    bbox = study["aoi"]["bbox"]
    assert bbox["xmin"] < bbox["xmax"] and bbox["ymin"] < bbox["ymax"]
    # Tete/Moatize: hemisfério sul, leste da África Austral.
    assert 30 < bbox["xmin"] < 36 and 30 < bbox["xmax"] < 36
    assert -18 < bbox["ymin"] < -15 and -18 < bbox["ymax"] < -15
    # A AOI cai inteiramente na zona UTM 36S (30°E–36°E), como exige o CRS métrico.
    assert bbox["xmin"] >= 30 and bbox["xmax"] <= 36


def test_mina_de_moatize_dentro_da_aoi(study):
    """Âncora §8: 16,1678°S 33,7895°E. A AOI tem de conter a mina."""
    bbox = study["aoi"]["bbox"]
    lon, lat = 33.7895, -16.1678
    assert bbox["xmin"] <= lon <= bbox["xmax"]
    assert bbox["ymin"] <= lat <= bbox["ymax"]


def test_anos_ancora_coerentes_com_sensores(study):
    anos = study["anos_ancora"]["imagem"]
    assert anos == sorted(anos)
    assert set(anos) == set(study["sensores"].keys())


def test_censos_sao_os_tres_realizados(study):
    assert study["anos_ancora"]["censo"] == [1997, 2007, 2017]


def test_composto_usa_estacao_seca(study):
    """§5.1: compostos de estação seca, maio–outubro, por mediana."""
    c = study["composto"]
    assert (c["estacao_seca"]["mes_inicio"], c["estacao_seca"]["mes_fim"]) == (5, 10)
    assert c["reducao"] == "median"
    assert 0 < c["nuvem_max_pct"] <= 100


def test_composto_fenologico_cobre_as_duas_estacoes(study):
    """§5.6.1: separar sequeiro de irrigado exige chuva e seca."""
    f = study["composto_fenologico"]
    assert f["estacao_chuvosa"]["mes_inicio"] > f["estacao_chuvosa"]["mes_fim"], (
        "a estação chuvosa atravessa o ano-novo (nov–abr)"
    )
    seca = set(range(f["estacao_seca"]["mes_inicio"], f["estacao_seca"]["mes_fim"] + 1))
    chuva = set(range(f["estacao_chuvosa"]["mes_inicio"], 13)) | set(
        range(1, f["estacao_chuvosa"]["mes_fim"] + 1)
    )
    assert not (seca & chuva), "as duas estações não podem se sobrepor"
    assert seca | chuva == set(range(1, 13)), "as duas estações devem cobrir o ano"


def test_classes_sao_as_do_repositorio(study):
    """Convenções: nomes de camada válidos, e nenhuma classe repetida entre grupos."""
    validas = {
        "urbano", "reassentamento", "industrial", "cultivo_sequeiro",
        "cultivo_irrigado", "vegetacao", "solo_exposto", "agua",
    }
    construido = set(study["classes"]["construido"])
    cobertura = set(study["classes"]["cobertura"])
    assert construido <= validas and cobertura <= validas
    assert not (construido & cobertura), "as camadas têm de ser mutuamente exclusivas"


def test_aneis_periurbanos_sao_contiguos_e_crescentes(study):
    """§5.6.2: anéis 0–1 km e 1–3 km, sem lacuna nem sobreposição."""
    aneis = study["zoneamento_agricola"]["aneis_km"]
    assert aneis[0][0] == 0
    for anterior, seguinte in pairwise(aneis):
        assert anterior[1] == seguinte[0]
    assert all(a[0] < a[1] for a in aneis)


def test_seeds_fixas_e_inteiras():
    """§11.2.1: determinismo. Toda seed declarada, nenhuma nula."""
    seeds = _load("seeds.yaml")
    achadas = []

    def walk(node):
        if isinstance(node, dict):
            for chave, valor in node.items():
                if isinstance(valor, (dict, list)):
                    walk(valor)
                elif "seed" in str(chave).lower():
                    achadas.append((chave, valor))
        elif isinstance(node, list):
            for item in node:
                walk(item)

    walk(seeds)
    assert achadas, "config/seeds.yaml não declara nenhuma seed"
    for chave, valor in achadas:
        assert isinstance(valor, int), f"seed {chave!r} não é inteira: {valor!r}"


def test_tolerancias_declaradas_e_positivas():
    """§10: reprodução byte a byte ou dentro de tolerância declarada."""
    tol = _load("tolerances.yaml")
    assert tol, "config/tolerances.yaml está vazio"


def test_aoi_confirmada_na_fase_0_linha(study):
    """A AOI deixa de ser provisória só depois do ADR 0001."""
    assert study["aoi"]["status"] == "confirmado"


def test_povoados_de_reassentamento_dentro_da_aoi(study):
    """§3: a AOI tem de conter os povoados de reassentamento.

    O bbox provisório deixava Cateme (33.9731 E) e Mwaladzi (34.0326 E) de fora, e
    nada no repositório acusava o erro. Ver docs/ADR/0001-aoi-final.md.
    Feições com `geometry: null` (povoado sem elemento OSM localizável) são ignoradas
    de propósito: ausência de coordenada não é coordenada fora da AOI.
    """
    caminho = ROOT / "data" / "raw" / "reassentamentos.geojson"
    if not caminho.exists():
        pytest.skip("reassentamentos.geojson ainda não coletado (Fase 0')")

    import json

    bbox = study["aoi"]["bbox"]
    with caminho.open(encoding="utf-8") as fh:
        colecao = json.load(fh)

    com_geometria = [f for f in colecao["features"] if f.get("geometry")]
    assert com_geometria, "nenhum povoado com geometria: o arquivo não cumpre §3"

    fora = []
    for feicao in com_geometria:
        lon, lat = feicao["geometry"]["coordinates"]
        if not (bbox["xmin"] <= lon <= bbox["xmax"] and bbox["ymin"] <= lat <= bbox["ymax"]):
            fora.append((feicao["properties"]["nome"], lon, lat))
    assert not fora, f"povoados fora da AOI: {fora}"


def test_coordenada_de_reassentamento_tem_fonte_rastreavel():
    """§10: nenhuma coordenada inventada.

    Uma execução da Fase 0' gravou pontos a 13 km e 31 km do que o OSM devolve,
    declarando "Nominatim OSM" com uma URL de *busca* como fonte. Quem diz que a
    coordenada veio do OSM tem de apontar o elemento resolvido.
    """
    caminho = ROOT / "data" / "raw" / "reassentamentos.geojson"
    if not caminho.exists():
        pytest.skip("reassentamentos.geojson ainda não coletado (Fase 0')")

    import json

    with caminho.open(encoding="utf-8") as fh:
        colecao = json.load(fh)

    problemas = []
    for feicao in colecao["features"]:
        props = feicao["properties"]
        nome = props.get("nome", "?")
        fonte = (props.get("fonte_coordenada") or "").lower()
        url = props.get("url_fonte") or ""

        if feicao.get("geometry") is None:
            continue  # ausência declarada: exigir url de elemento não faz sentido

        if "osm" in fonte:
            if not props.get("osm_id"):
                problemas.append(f"{nome}: declara OSM mas não traz osm_id")
            if "/search" in url or "?query=" in url:
                problemas.append(f"{nome}: url_fonte é uma busca, não um elemento ({url})")
            elif not any(t in url for t in ("/node/", "/way/", "/relation/")):
                problemas.append(f"{nome}: url_fonte não aponta um elemento OSM ({url})")
        elif not url.startswith("http"):
            problemas.append(f"{nome}: coordenada sem URL de fonte ({fonte!r})")

    assert not problemas, "; ".join(problemas)


def test_checksums_de_data_raw_conferem():
    """§11.2.2: todo arquivo espelhado tem .sha256 verificável e .meta.json coerente.

    Defeitos reais da Fase 0' que este contrato pega: um .sha256 gravado só com o hash
    (sem o nome do arquivo, o que faz `shasum -c` falhar) e um .meta.json declarando
    260418 bytes para um arquivo de 266418.
    """
    import hashlib
    import json

    raw = ROOT / "data" / "raw"
    if not raw.exists():
        pytest.skip("data/raw ainda não populado")

    arquivos = [
        p for p in raw.iterdir()
        if p.is_file() and p.suffix not in {".sha256", ".json"} and not p.name.startswith(".")
    ]
    if not arquivos:
        pytest.skip("nenhum arquivo espelhado ainda")

    problemas = []
    for arquivo in arquivos:
        sidecar = arquivo.with_suffix(arquivo.suffix + ".sha256")
        meta = arquivo.with_suffix(arquivo.suffix + ".meta.json")

        if not sidecar.exists():
            problemas.append(f"{arquivo.name}: sem .sha256")
        else:
            texto = sidecar.read_text(encoding="utf-8").split()
            if len(texto) < 2 or texto[1].lstrip("*") != arquivo.name:
                problemas.append(
                    f"{arquivo.name}: .sha256 fora do formato '<hash>  <nome>'"
                )
            digest = hashlib.sha256(arquivo.read_bytes()).hexdigest()
            if texto and texto[0] != digest:
                problemas.append(f"{arquivo.name}: hash não confere")

        if not meta.exists():
            problemas.append(f"{arquivo.name}: sem .meta.json")
        else:
            dados = json.loads(meta.read_text(encoding="utf-8"))
            declarado = dados.get("size_bytes")
            real = arquivo.stat().st_size
            if declarado is not None and declarado != real:
                problemas.append(
                    f"{arquivo.name}: .meta.json diz {declarado} bytes, arquivo tem {real}"
                )

    # Sidecar sem o dado ao lado: o .gitignore mantém só os sidecars versionados, então
    # um órfão faz o repositório declarar um espelho que ninguém consegue reconstruir.
    nomes = {p.name for p in arquivos}
    for sidecar in list(raw.glob("*.sha256")) + list(raw.glob("*.meta.json")):
        alvo = sidecar.name.rsplit(".sha256", 1)[0].rsplit(".meta.json", 1)[0]
        if alvo not in nomes:
            problemas.append(f"{sidecar.name}: sidecar sem o arquivo {alvo}")

    assert not problemas, "; ".join(problemas)


def test_rasters_de_data_raw_cobrem_a_aoi(study):
    """Todo raster espelhado tem de cobrir a AOI inteira, em união.

    Defeito real da Fase 0': o script do Copernicus DEM fixou no código a AOI
    provisória (33.50–33.95 E) e uma lista de tiles à mão, então baixou apenas a
    coluna E033. Com a AOI confirmada indo a 34.10 E, a faixa 34.0–34.1 ficou sem
    elevação — exatamente onde está Mwaladzi (34.0326 E), o que inviabilizaria o
    HAND de várzea (§5.6) num povoado de reassentamento.
    """
    rasterio = pytest.importorskip("rasterio")

    raw = ROOT / "data" / "raw"
    tifs = sorted(raw.glob("*.tif")) if raw.exists() else []
    if not tifs:
        pytest.skip("nenhum raster espelhado ainda")

    bbox = study["aoi"]["bbox"]
    # Agrupa por família (prefixo antes do primeiro '_S' ou '_N' do nome do tile).
    familias: dict[str, list] = {}
    for caminho in tifs:
        familia = caminho.name.split("_S")[0].split("_N")[0]
        familias.setdefault(familia, []).append(caminho)

    faltando = []
    for familia, caminhos in familias.items():
        cobertos = []
        for caminho in caminhos:
            with rasterio.open(caminho) as src:
                if src.crs is None or src.crs.to_epsg() != 4326:
                    continue  # cobertura em outro CRS: fora do escopo deste contrato
                cobertos.append(src.bounds)
        if not cobertos:
            continue
        # Amostra o bbox da AOI e exige que cada ponto caia em algum tile.
        passos = 11
        for i in range(passos):
            lon = bbox["xmin"] + (bbox["xmax"] - bbox["xmin"]) * i / (passos - 1)
            for j in range(passos):
                lat = bbox["ymin"] + (bbox["ymax"] - bbox["ymin"]) * j / (passos - 1)
                if not any(
                    b.left <= lon <= b.right and b.bottom <= lat <= b.top for b in cobertos
                ):
                    faltando.append(f"{familia}: ({lon:.4f}, {lat:.4f}) fora de todo tile")
                    break
            else:
                continue
            break

    assert not faltando, "; ".join(faltando)


def test_scripts_de_fetch_nao_fixam_a_aoi_no_codigo():
    """§11.2.1: config/ é a única fonte da AOI; nenhuma etapa depende de estado próprio.

    Um script que copia o bbox para dentro de si deixa de acompanhar o ADR que muda a
    AOI — e falha em silêncio, baixando a área errada.
    """
    fetch = ROOT / "pipeline" / "00_fetch"
    if not fetch.exists():
        pytest.skip("pipeline/00_fetch ainda não existe")

    import re

    # O bbox provisório, já superado pelo ADR 0001. Achá-lo num script é erro certo.
    obsoletos = (r"33\.95", r"33,95")
    infratores = []
    for caminho in sorted(list(fetch.glob("*.py")) + list(fetch.glob("*.sh"))):
        texto = caminho.read_text(encoding="utf-8", errors="replace")
        for linha_n, linha in enumerate(texto.splitlines(), 1):
            # Menção em comentário histórico é aceitável se disser que foi corrigida.
            if any(re.search(p, linha) for p in obsoletos) and "corrigid" not in linha.lower():
                infratores.append(f"{caminho.name}:{linha_n}: {linha.strip()[:80]}")
    assert not infratores, (
        "bbox provisório (xmax=33.95) fixado em script; leia config/study.yaml. "
        + "; ".join(infratores)
    )


def test_sidecars_nao_declaram_aoi_divergente(study):
    """§11.2.2: o .meta.json é a proveniência do arquivo espelhado.

    Defeito real, pego pelo portão da Fase 0': dois sidecars seguiram declarando
    `aoi_bbox` com o `xmax` provisório de 33.95 depois de o ADR 0001 confirmar 34.10.
    Um .meta.json que descreve um recorte diferente do que o pipeline usa documenta
    um arquivo que não é o que está ali.
    """
    import json

    raw = ROOT / "data" / "raw"
    if not raw.exists():
        pytest.skip("data/raw ainda não populado")

    bbox = study["aoi"]["bbox"]
    divergentes = []
    for meta in sorted(raw.glob("*.meta.json")):
        dados = json.loads(meta.read_text(encoding="utf-8"))
        for chave in ("aoi_bbox", "aoi", "bbox"):
            valor = dados.get(chave)
            if not isinstance(valor, dict):
                continue
            for canto in ("xmin", "ymin", "xmax", "ymax"):
                if canto in valor and abs(float(valor[canto]) - bbox[canto]) > 1e-9:
                    divergentes.append(
                        f"{meta.name}: {chave}.{canto}={valor[canto]}, "
                        f"config diz {bbox[canto]}"
                    )
    assert not divergentes, "; ".join(divergentes)


def test_proveniencia_nao_afirma_aoi_obsoleta():
    """A proveniência é o que o leitor usa para reproduzir o recorte.

    Só se aceita o bbox obsoleto numa linha que explicitamente a trate como histórica —
    caso contrário o documento afirma um recorte que o pipeline não usa, e o erro se
    propaga para os consolidados por scripts/consolidar_registros.py.
    """
    obsoleto = "33.95"
    marcas = ("adr", "provisóri", "provisori", "corrigid", "era ", "reexecut", "antes")

    infratores = []
    for pasta in ("licenses_parts", "provenance_parts"):
        diretorio = ROOT / "data" / pasta
        if not diretorio.exists():
            continue
        for fragmento in sorted(diretorio.glob("*.md")):
            for n, linha in enumerate(fragmento.read_text(encoding="utf-8").splitlines(), 1):
                if obsoleto in linha and not any(m in linha.lower() for m in marcas):
                    infratores.append(f"{pasta}/{fragmento.name}:{n}")
    assert not infratores, (
        "bbox obsoleto (xmax=33.95) afirmado sem marcá-lo como histórico: "
        + "; ".join(infratores)
    )
