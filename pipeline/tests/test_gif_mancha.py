"""Contratos sobre pipeline/04_figures/gif_mancha.py (§6.3, §10, ADR 0013, ADR 0018).

Propósito: garantir que o GIF animado da progressão da mancha urbana existe, tem os
6 quadros dos anos-âncora, que o `.meta.json` que o acompanha lista os 6 anos e os
hashes sha256 dos insumos batendo com os arquivos atualmente em
`data/processed/app/imagery/`, e — §10, reexecução em ambiente limpo — que o GIF
REGENERADO a partir desses insumos confere com o publicado: byte a byte, ou dentro da
tolerância declarada em `.meta.json['reprodutibilidade']['tolerancia']`.

Pula (`pytest.skip`) se o GIF ainda não foi gerado ou se os insumos estão ausentes num
checkout parcial (num clone completo eles estão versionados).
"""
from __future__ import annotations

import hashlib
import importlib.util
import json
from hashlib import sha256
from pathlib import Path

import pytest
import yaml

ROOT = Path(__file__).resolve().parents[2]
FIGURAS = ROOT / "paper" / "figuras"
DATA_APP_IMAGERY = ROOT / "data" / "processed" / "app" / "imagery"
SCRIPT = ROOT / "pipeline" / "04_figures" / "gif_mancha.py"
PALETA_YAML = ROOT / "config" / "paleta_uso_solo.yaml"

GIF = FIGURAS / "mancha_urbana_2000_2025.gif"
META = FIGURAS / "mancha_urbana_2000_2025.meta.json"

ANOS_ESPERADOS = [2000, 2005, 2010, 2015, 2020, 2025]


def _hash_arquivo(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _caminho_insumo(nome: str) -> Path:
    if nome == "manifest":
        return DATA_APP_IMAGERY / "manifest.json"
    if nome == "paleta_uso_solo_yaml":
        return PALETA_YAML
    return DATA_APP_IMAGERY / f"{nome}.geojson"


@pytest.fixture(scope="module")
def meta():
    if not META.exists():
        pytest.skip("mancha_urbana_2000_2025.meta.json ainda não gerado")
    with META.open(encoding="utf-8") as fh:
        return json.load(fh)


@pytest.fixture(scope="module")
def gif_mancha():
    spec = importlib.util.spec_from_file_location("gif_mancha", SCRIPT)
    modulo = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(modulo)
    return modulo


def test_gif_existe_e_tem_tamanho_plausivel():
    if not GIF.exists():
        pytest.skip("GIF ainda não gerado (rode pipeline/04_figures/gif_mancha.py)")
    assert GIF.stat().st_size > 100_000, "GIF suspeito de vazio/corrompido"
    assert GIF.read_bytes()[:6] in (b"GIF87a", b"GIF89a"), "arquivo não é um GIF válido"


def test_gif_tem_6_quadros():
    if not GIF.exists():
        pytest.skip("GIF ainda não gerado")
    from PIL import Image

    with Image.open(GIF) as im:
        n_frames = getattr(im, "n_frames", 1)
    assert n_frames == 6, f"esperado 1 quadro por ano-âncora (6), obtido {n_frames}"


def test_meta_lista_os_6_anos_ancora(meta):
    assert meta["anos_ancora"] == ANOS_ESPERADOS


def test_meta_declara_metodo_pipeline(meta):
    assert meta["metodo"] == "pipeline/04_figures/gif_mancha.py"


def test_meta_declara_selo_para_todas_as_series(meta):
    assert meta.get("selo")


def test_meta_declara_ressalvas_obrigatorias(meta):
    texto = " ".join(meta["ressalvas"])
    assert "ADR 0013" in texto
    assert "acurácia" in texto.lower() or "acuracia" in texto.lower()
    assert "não é figura de resultado" in texto or "nao e figura de resultado" in texto.lower()


def test_meta_nao_referencia_app_public_media(meta):
    texto = json.dumps(meta, ensure_ascii=False)
    assert "app/public/media" not in texto, (
        "o app deixou de usar o GIF — a referência a app/public/media/ é herança "
        "da geração por captura de tela e não deve mais constar do meta"
    )


def test_hashes_dos_insumos_batem_com_os_arquivos_atuais(meta):
    hashes = meta.get("hashes_sha256_insumos", {})
    if not hashes:
        pytest.skip("meta sem hashes de insumos (deveria haver, mas não bloqueia checkout parcial)")
    ausentes = []
    divergentes = []
    for nome, hash_esperado in hashes.items():
        caminho = _caminho_insumo(nome)
        if not caminho.exists():
            ausentes.append(nome)
            continue
        if _hash_arquivo(caminho) != hash_esperado:
            divergentes.append(nome)
    if ausentes:
        pytest.skip(f"insumos ausentes no checkout parcial: {ausentes}")
    assert not divergentes, (
        f"insumos mudaram desde a geração do GIF, sem regeneração: {divergentes}"
    )


def test_cores_do_gif_vem_do_yaml_da_paleta_de_uso_do_solo(gif_mancha):
    """ADR 0018: nenhuma cor de classe é escrita no script — todas vêm do YAML.

    Substitui o antigo contrato "cores replicadas de MapaTemporal.jsx" (o app já não
    guarda cores ali; a fonte única é `config/paleta_uso_solo.yaml`). Cada cor usada por
    `gif_mancha.CORES_CAMADA`/`CONTORNO_CAMADA` tem de ser um subconjunto exato das cores
    declaradas no YAML (classes + contexto), e o script tem de reportar o hash do YAML
    lido, para o `.meta.json` rastrear a proveniência da paleta.
    """
    paleta = yaml.safe_load(PALETA_YAML.read_text(encoding="utf-8"))
    classes = paleta["classes"]
    contexto = paleta["contexto"]

    cores_esperadas = {
        "urbano": classes["urbano"]["cor"],
        "industrial": classes["industrial"]["cor"],
        "reassentamento": classes["reassentamento"]["cor"],
        "cultivo_irrigado": classes["cultivo_irrigado"]["cor"],
        "agua": classes["agua"]["cor"],
        "varzea": classes["varzea"]["cor"],
        "osm_vias": contexto["vias"],
        "osm_ferrovia": contexto["ferrovia"],
        "osm_aerodromo": contexto["aerodromo"],
        "osm_lugares": contexto["toponimo"],
    }
    assert gif_mancha.CORES_CAMADA == cores_esperadas

    contornos_esperados = {
        "reassentamento": classes["reassentamento"]["contorno"],
        "industrial": classes["industrial"]["contorno"],
    }
    assert gif_mancha.CONTORNO_CAMADA == contornos_esperados

    assert gif_mancha.FUNDO_MAPA == contexto["fundo_mapa"]
    assert gif_mancha.OPACIDADE_VARZEA == classes["varzea"]["opacidade"]
    assert gif_mancha.COR_CONTORNO_FANTASMA == contexto["contorno_fantasma"]
    assert gif_mancha.SHA256_PALETA_USO_SOLO == sha256(PALETA_YAML.read_bytes()).hexdigest()
    assert gif_mancha.ADR_PALETA_USO_SOLO == "docs/ADR/0018-paleta-uso-do-solo-worldcover.md"


def test_meta_registra_hash_e_adr_da_paleta_de_uso_do_solo(meta):
    paleta_cores = meta.get("paleta_cores", {})
    assert paleta_cores.get("fonte") == "config/paleta_uso_solo.yaml"
    assert paleta_cores.get("adr") == "docs/ADR/0018-paleta-uso-do-solo-worldcover.md"
    assert paleta_cores.get("sha256") == sha256(PALETA_YAML.read_bytes()).hexdigest()
    assert "hashes_sha256_insumos" in meta
    assert "paleta_uso_solo_yaml" in meta["hashes_sha256_insumos"], (
        "config/paleta_uso_solo.yaml tem de constar entre os insumos com hash rastreado"
    )


def test_meta_declara_fontes_embutidas_dejavu(meta):
    """Nenhuma fonte resolvida contra o sistema (Iowan Old Style não existe no CI)."""
    assert "DejaVu" in meta["fonte_serif_usada"]
    assert "DejaVu" in meta["fonte_sans_usada"]
    fontes = meta["reprodutibilidade"]["ambiente"]["fontes_ttf"]
    for registro in fontes.values():
        assert registro["arquivo"].startswith("matplotlib/mpl-data/fonts/ttf/DejaVu")


def test_meta_declara_a_mesma_tolerancia_que_o_script_aplica(meta, gif_mancha):
    assert meta["reprodutibilidade"]["tolerancia"] == gif_mancha.TOLERANCIA


def test_gif_regenerado_confere_com_o_publicado(meta, gif_mancha, tmp_path):
    """§10: regenera num diretório temporário e compara com o GIF publicado.

    Aceita sha256 idêntico; senão exige o que `comparar_gifs()` declara — mesmo número
    de quadros, tamanho e duração, todos os pixels na paleta fixa e, por quadro, fração
    de pixels diferentes e MAE RGB dentro de `TOLERANCIA`.
    """
    if not GIF.exists():
        pytest.skip("GIF ainda não gerado")
    ausentes = [n for n in meta["hashes_sha256_insumos"] if not _caminho_insumo(n).exists()]
    if ausentes:
        pytest.skip(f"insumos ausentes no checkout parcial: {ausentes}")

    regenerado = tmp_path / GIF.name
    gif_mancha.gerar(regenerado)
    resultado = gif_mancha.comparar_gifs(GIF, regenerado)
    assert resultado["dentro_da_tolerancia"], (
        "GIF regenerado fora da tolerância declarada: "
        f"{resultado['violacoes']} (métricas por quadro: {resultado['quadros']})"
    )
    # Na plataforma de geração (mesmo sistema e arquitetura), a garantia é byte a byte.
    plataforma = meta["reprodutibilidade"]["ambiente"]["plataforma_de_geracao"]
    import platform

    if plataforma == f"{platform.system()} {platform.machine()}":
        assert resultado["identico_byte_a_byte"], (
            f"mesma plataforma ({plataforma}) mas bytes diferentes: {resultado['quadros']}"
        )
