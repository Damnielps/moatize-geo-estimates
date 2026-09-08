"""Contratos de plausibilidade por camada (config/plausibilidade.yaml).

Motivo: o contrato de exclusividade mútua passava, e mesmo assim `industrial` media
"construído dentro do polígono de mineração" em vez da pegada — 4,2 km² contra os 59,2
conhecidos, com 93% da mina fora de qualquer camada. Nenhum contrato perguntava se a
camada media o que o nome dela promete. Ver ORCHESTRATION_LOG.md 2-06.
"""
from __future__ import annotations

from pathlib import Path

import pytest
import yaml

ROOT = Path(__file__).resolve().parents[2]
IMAGERY = ROOT / "data" / "processed" / "imagery"


@pytest.fixture(scope="module")
def plaus() -> dict:
    with (ROOT / "config" / "plausibilidade.yaml").open(encoding="utf-8") as fh:
        return yaml.safe_load(fh)


def area_km2(caminho: Path) -> float:
    import rasterio

    with rasterio.open(caminho) as src:
        pixel_m2 = abs(src.transform.a * src.transform.e)
        return int((src.read(1) > 0).sum()) * pixel_m2 / 1e6


def faixa_do_ano(camada: dict, ano: int) -> dict | None:
    for f in camada["faixas"]:
        if f["ano_min"] <= ano <= f["ano_max"]:
            return f
    return None


def test_toda_camada_declara_justificativa_e_fonte(plaus):
    """Faixa sem justificativa é número arbitrário — e vira folclore em duas semanas."""
    problemas = []
    for nome, camada in plaus["camadas"].items():
        if not camada.get("justificativa", "").strip():
            problemas.append(f"{nome}: sem justificativa")
        if not camada.get("faixas"):
            problemas.append(f"{nome}: sem faixas")
        for f in camada.get("faixas", []):
            if not f.get("nota", "").strip():
                problemas.append(f"{nome} [{f['ano_min']}–{f['ano_max']}]: faixa sem nota")
            if f["min_km2"] > f["max_km2"]:
                problemas.append(f"{nome} [{f['ano_min']}–{f['ano_max']}]: min > max")
    assert not problemas, "; ".join(problemas)


def test_area_das_camadas_dentro_da_faixa_plausivel(plaus):
    """A camada tem de medir, em ordem de grandeza, o objeto que o nome dela promete.

    Sair da faixa não é proibido — é obrigatório explicar num ADR e declarar a exceção
    em `config/plausibilidade.yaml`.
    """
    pytest.importorskip("rasterio")
    if not IMAGERY.exists():
        pytest.skip("camadas ainda não classificadas")

    excecoes = plaus.get("excecoes") or {}
    problemas = []

    for nome, camada in plaus["camadas"].items():
        for caminho in sorted(IMAGERY.glob(f"{nome}_*_30m_32736.tif")):
            try:
                ano = int(caminho.stem.split("_")[1])
            except (IndexError, ValueError):
                continue
            f = faixa_do_ano(camada, ano)
            if f is None:
                problemas.append(f"{nome} {ano}: sem faixa declarada para o ano")
                continue

            area = area_km2(caminho)
            if not (f["min_km2"] <= area <= f["max_km2"]):
                chave = f"{nome}:{ano}"
                adr = excecoes.get(chave)
                if adr:
                    caminhos = list((ROOT / "docs" / "ADR").glob(f"{adr}*"))
                    if caminhos and nome in caminhos[0].read_text(encoding="utf-8"):
                        continue  # exceção declarada e explicada
                    problemas.append(
                        f"{chave}: exceção aponta ADR {adr}, que não existe "
                        "ou não menciona a camada"
                    )
                else:
                    problemas.append(
                        f"{nome} {ano}: {area:.2f} km² fora da faixa "
                        f"[{f['min_km2']}, {f['max_km2']}] — {f['nota'][:60]}"
                    )
    assert not problemas, "; ".join(problemas)


def test_industrial_cobre_fracao_razoavel_da_referencia_externa(plaus):
    """Onde há referência externa, a camada tem de encontrá-la.

    Os polígonos de Maus et al. são a única referência de nível A para a pegada minerária.
    Uma camada `industrial` que cobre 7% deles não está medindo a pegada.
    """
    gpd = pytest.importorskip("geopandas")
    rasterio = pytest.importorskip("rasterio")
    from rasterio.features import geometry_mask

    poligonos = ROOT / "data" / "raw" / "global_mining_polygons_v2_maus_2022_aoi.geojson"
    alvo = IMAGERY / "industrial_2025_30m_32736.tif"
    if not poligonos.exists() or not alvo.exists():
        pytest.skip("polígonos de mineração ou camada industrial ausentes")

    g = gpd.read_file(poligonos).to_crs(32736)
    with rasterio.open(alvo) as src:
        ind = src.read(1) > 0
        dentro = geometry_mask(g.geometry, out_shape=src.shape,
                               transform=src.transform, invert=True)

    cobertura = (ind & dentro).sum() / max(dentro.sum(), 1)
    assert cobertura >= 0.50, (
        f"a camada industrial cobre {cobertura:.1%} dos polígonos de Maus et al. "
        "(referência 2017–2019). Abaixo de 50% ela não está medindo a pegada minerária — "
        "ver ORCHESTRATION_LOG.md 2-06."
    )
