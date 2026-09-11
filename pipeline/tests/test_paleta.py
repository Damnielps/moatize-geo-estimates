"""pipeline/tests/test_paleta.py — contrato da paleta de uso do solo (ADR 0018).

Contratos:
1. `app/src/content/paleta_uso_solo.json` foi gerado do YAML atual (`sha256_config`) e é
   idêntico ao que o gerador produz agora (determinismo, sem edição à mão).
2. Toda classe tem `cor` hex `#RRGGBB` e `origem` em {worldcover, adaptacao}.
3. Toda classe `origem: worldcover` tem exatamente a cor oficial da classe WorldCover que
   declara em `classe_worldcover`; toda `adaptacao` declara uma classe WorldCover existente.
4. `industrial` nunca tem o vermelho do Built-up nem vermelho algum, em `cor` ou `contorno`
   (CLAUDE.md §10: nenhuma cava de mina lida como área urbana).
"""

import colorsys
import importlib.util
import json
import re
from hashlib import sha256
from pathlib import Path

import pytest
import yaml

RAIZ = Path(__file__).resolve().parents[2]
YAML = RAIZ / "config" / "paleta_uso_solo.yaml"
JSON = RAIZ / "app" / "src" / "content" / "paleta_uso_solo.json"
GERADOR = RAIZ / "pipeline" / "05_app" / "gerar_paleta.py"

# Tabela oficial de cores da ESA WorldCover v100/v200 (legenda FAO LCCS). É a tabela de cores
# embutida no raster original da ESA cuja URL o cabeçalho de config/paleta_uso_solo.yaml
# registra (tile S18E033, v100/2020), conferida em 2026-09-11 (ADR 0018). Os recortes da AOI em
# data/raw/esa_worldcover_*_aoi.tif não trazem a tabela (NULL color table), por isso ela é
# fixada aqui e não lida em tempo de teste — o teste não depende de rede.
WORLDCOVER_OFICIAL = {
    10: "#006400",  # Tree cover
    20: "#FFBB22",  # Shrubland
    30: "#FFFF4C",  # Grassland
    40: "#F096FF",  # Cropland
    50: "#FA0000",  # Built-up
    60: "#B4B4B4",  # Bare / sparse vegetation
    70: "#F0F0F0",  # Snow and ice
    80: "#0064C8",  # Permanent water bodies
    90: "#0096A0",  # Herbaceous wetland
    95: "#00CF75",  # Mangroves
    100: "#FAE6A0",  # Moss and lichen
}
HEX = re.compile(r"^#[0-9A-Fa-f]{6}$")


def _eh_vermelho(hex_cor):
    r, g, b = (int(hex_cor[i : i + 2], 16) / 255 for i in (1, 3, 5))
    h, s, v = colorsys.rgb_to_hsv(r, g, b)
    graus = h * 360
    return s >= 0.25 and v >= 0.2 and (graus <= 30 or graus >= 330)


def _codigo(classe_worldcover):
    m = re.match(r"^\s*(\d+)\b", str(classe_worldcover))
    return int(m.group(1)) if m else None


@pytest.fixture(scope="module")
def paleta_yaml():
    return yaml.safe_load(YAML.read_text(encoding="utf-8"))


@pytest.fixture(scope="module")
def paleta_json():
    assert JSON.exists(), "rode `uv run python pipeline/05_app/gerar_paleta.py`"
    return json.loads(JSON.read_text(encoding="utf-8"))


def test_json_bate_com_yaml(paleta_json, paleta_yaml):
    assert paleta_json["sha256_config"] == sha256(YAML.read_bytes()).hexdigest(), (
        "paleta_uso_solo.json desatualizado: rode pipeline/05_app/gerar_paleta.py"
    )
    assert paleta_json["classes"] == paleta_yaml["classes"]
    assert paleta_json["contexto"] == paleta_yaml["contexto"]


def test_json_e_saida_deterministica_do_gerador():
    spec = importlib.util.spec_from_file_location("gerar_paleta", GERADOR)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    esperado = json.dumps(mod.gerar(), ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    assert JSON.read_text(encoding="utf-8") == esperado


def test_toda_classe_tem_cor_hex_e_origem_valida(paleta_json):
    assert paleta_json["classes"], "paleta sem classes"
    for nome, c in paleta_json["classes"].items():
        assert HEX.match(c["cor"]), f"{nome}: cor {c['cor']!r}"
        assert c["origem"] in {"worldcover", "adaptacao"}, f"{nome}: origem {c['origem']!r}"
        if "contorno" in c:
            assert HEX.match(c["contorno"]), f"{nome}: contorno {c['contorno']!r}"
        if c["origem"] == "adaptacao":
            assert str(c.get("nota", "")).strip(), f"{nome}: adaptação sem nota"
    for nome, valor in paleta_json["contexto"].items():
        assert HEX.match(valor), f"contexto.{nome}: {valor!r}"


def test_classes_worldcover_batem_com_tabela_oficial(paleta_json):
    for nome, c in paleta_json["classes"].items():
        codigo = _codigo(c["classe_worldcover"])
        assert codigo in WORLDCOVER_OFICIAL, (
            f"{nome}: classe WorldCover {c['classe_worldcover']!r} inexistente"
        )
        if c["origem"] == "worldcover":
            assert c["cor"].upper() == WORLDCOVER_OFICIAL[codigo], (
                f"{nome}: {c['cor']} ≠ oficial {WORLDCOVER_OFICIAL[codigo]} da classe {codigo}"
            )


def test_industrial_nunca_vermelho(paleta_json):
    ind = paleta_json["classes"]["industrial"]
    built_up = WORLDCOVER_OFICIAL[50]
    for chave in ("cor", "contorno"):
        if chave not in ind:
            continue
        assert ind[chave].upper() != built_up, f"industrial.{chave} usa o vermelho do Built-up"
        assert not _eh_vermelho(ind[chave]), f"industrial.{chave} = {ind[chave]} é vermelho (§10)"
    assert _codigo(ind["classe_worldcover"]) != 50, "industrial declarado como Built-up"


def test_criterio_de_vermelho_discrimina():
    # O critério tem de reconhecer os vermelhos da própria paleta e recusar os cinzas.
    assert _eh_vermelho("#FA0000") and _eh_vermelho("#9E0000") and _eh_vermelho("#5C0000")
    assert not _eh_vermelho("#B4B4B4") and not _eh_vermelho("#6E6E6E")
