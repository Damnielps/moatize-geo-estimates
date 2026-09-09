"""Contratos sobre pipeline/04_figures/ (§6.3, §10, §11.2.4).

Propósito: garantir que a figura de localização (mapa principal + encartes de
província e país) existe, tem tamanho plausível, declara as ressalvas de honestidade
cartográfica obrigatórias (docs/ADR/0008, docs/ADR/0009) e é determinística — mesma
entrada, mesmo tamanho de tela. O teste não compara hash de pixel: fontes do sistema
variam a rasterização de texto entre máquinas (documentado no próprio script), então
o contrato checa geometria da tela (dimensões em pixels a 300 dpi), não bytes.

Pula (`pytest.skip`) se a figura ainda não foi gerada — `mapa_localizacao.py` lê
`data/raw/` e `data/processed/imagery/`, que podem não existir num checkout parcial.
"""
from __future__ import annotations

import json
import re
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
FIGURAS = ROOT / "paper" / "figuras"
SCRIPT = ROOT / "pipeline" / "04_figures" / "mapa_localizacao.py"

PDF = FIGURAS / "mapa_localizacao.pdf"
PNG = FIGURAS / "mapa_localizacao.png"
META = FIGURAS / "mapa_localizacao.meta.json"

# Tamanho de tela declarado no orçamento de layout do script (figsize 11x12.0in a
# 300 dpi). Tolerância pequena para variação de arredondamento entre backends.
TAMANHO_ESPERADO_PNG = (3300, 3600)
TOLERANCIA_PX = 4


def _artefatos_disponiveis() -> bool:
    return PDF.exists() and PNG.exists() and META.exists()


@pytest.fixture(scope="module")
def meta():
    if not META.exists():
        pytest.skip("mapa_localizacao.meta.json ainda não gerado")
    with META.open(encoding="utf-8") as fh:
        return json.load(fh)


def test_arquivos_de_saida_existem_com_tamanho_plausivel():
    if not _artefatos_disponiveis():
        pytest.skip("figura ainda não gerada (rode pipeline/04_figures/mapa_localizacao.py)")
    # PDF vetorial de um mapa com hidrografia + polígonos classificados: dezenas de KB
    # no mínimo; PNG a 300 dpi de página quase carta: também na casa das centenas de KB.
    assert PDF.stat().st_size > 50_000, "PDF suspeito de vazio/corrompido"
    assert PNG.stat().st_size > 200_000, "PNG suspeito de vazio/corrompido"
    assert PDF.read_bytes()[:5] == b"%PDF-", "arquivo não é um PDF válido"
    assert PNG.read_bytes()[:8] == b"\x89PNG\r\n\x1a\n", "arquivo não é um PNG válido"


def test_png_tem_dimensoes_do_orcamento_de_layout():
    if not PNG.exists():
        pytest.skip("PNG ainda não gerado")
    from PIL import Image

    with Image.open(PNG) as im:
        largura, altura = im.size
    assert abs(largura - TAMANHO_ESPERADO_PNG[0]) <= TOLERANCIA_PX, (
        f"largura {largura}px fora do orçamento de layout fixo "
        f"({TAMANHO_ESPERADO_PNG[0]}px) — bbox_inches deixou de ser fixo?"
    )
    assert abs(altura - TAMANHO_ESPERADO_PNG[1]) <= TOLERANCIA_PX, (
        f"altura {altura}px fora do orçamento de layout fixo "
        f"({TAMANHO_ESPERADO_PNG[1]}px)"
    )


def test_meta_declara_selo_e_crs(meta):
    assert meta["selo"] == "observado"
    assert meta["crs_mapa_principal"] == "EPSG:32736"
    assert meta["crs_encartes"] == "EPSG:4326"
    assert meta["ano_camadas_classificadas"] == 2025


def test_meta_declara_ressalvas_de_honestidade_cartografica(meta):
    """§10: 'urbano' não é cadastro; a série de área é do WSF, não da classificação
    própria; geometria ausente não é inventada. As três ressalvas têm de estar
    registradas na proveniência, não só implícitas na legenda."""
    ressalvas = " ".join(meta.get("ressalvas", [])).lower()

    # A faixa é LIDA da fonte, não escrita aqui (ORCHESTRATION_LOG.md 4-07).
    #
    # A versão anterior exigia os literais "0,27" e "0,63". Quando `docs/ADR/0014`
    # reexecutou a validação e obteve 0,286–0,625, este contrato passou a **exigir o
    # número obsoleto**: corrigir a figura o fazia falhar. Um contrato que codifica um
    # valor medido envelhece com ele e passa a defender o erro — é o mesmo defeito que
    # `pipeline/lib/acuracia_texto.py` existe para eliminar no pipeline.
    import csv as _csv

    csv_acuracia = ROOT / "data" / "processed" / "acuracia_por_ano.csv"
    if csv_acuracia.exists():
        with csv_acuracia.open(encoding="utf-8", newline="") as fh:
            vals = []
            for linha in _csv.DictReader(fh):
                try:
                    vals.append(float(linha["acuracia_usuario_construido"]))
                except (KeyError, TypeError, ValueError):
                    pass
        if vals:
            # Aceita 2 ou 3 decimais: "0,286" e "0,29" descrevem o mesmo valor medido.
            alvos = []
            for v in (min(vals), max(vals)):
                alvos.append({f"{v:.3f}".replace(".", ","), f"{v:.2f}".replace(".", ",")})
            faltando = [a for a in alvos if not (a & set(re.findall(r"0,\d{2,3}", ressalvas)))]
            assert not faltando, (
                "faixa de acurácia do usuário ausente ou desatualizada nas ressalvas: "
                f"esperado {min(vals):.3f}–{max(vals):.3f} "
                f"(de acuracia_por_ano.csv, reexecutado em docs/ADR/0014); "
                f"encontrado {sorted(set(re.findall(r'0,\\d{2,3}', ressalvas)))}"
            )
    assert "wsf" in ressalvas, "menção ao WSF Evolution como série primária (docs/ADR/0008) ausente"
    assert "25 de setembro" in ressalvas, "nota sobre geometria não localizada ausente"


def test_meta_lista_insumos_com_hash(meta):
    insumos = meta.get("insumos", {})
    assert set(insumos) >= {
        "admin_zip", "urbano", "industrial", "reassentamento_poligonos",
        "reassentamentos_pontos", "hydro",
    }
    for caminho, hash_sha256 in insumos.values():
        assert len(hash_sha256) == 64, f"hash não parece sha256: {caminho}"


def test_script_e_determinístico(tmp_path):
    """Roda o script duas vezes e compara o tamanho de tela do PNG (não o hash de
    pixel — texto pode rasterizar de forma levemente diferente entre execuções da
    mesma máquina por causa de cache de fonte, mas as dimensões da tela não devem
    mudar, porque o layout é orçado em polegadas fixas, não em bbox de conteúdo)."""
    if not (ROOT / "data" / "raw" / "reassentamentos.geojson").exists():
        pytest.skip("insumos de data/raw/ e data/processed/ não disponíveis neste checkout")

    from PIL import Image

    tamanhos = []
    for _ in range(2):
        resultado = subprocess.run(
            [sys.executable, str(SCRIPT)], cwd=ROOT, capture_output=True,
            text=True, timeout=300, check=False,
        )
        assert resultado.returncode == 0, resultado.stderr
        with Image.open(PNG) as im:
            tamanhos.append(im.size)
    assert tamanhos[0] == tamanhos[1], f"tamanho de tela variou entre execuções: {tamanhos}"
