"""Contratos sobre `pipeline/01_imagery/cultivo.py`, `varzea.py` e `acuracia_cultivo.py`
(§5.6, Fase 2b).

Propósito: garantir que as camadas de cultivo não sobrepõem construído/pegada/água (§10
não pode regredir), que a várzea é uma máscara física plausível, e que a acurácia por
classe está publicada com prevalência — mesmo contrato de espírito de ADR 0009, agora
para cultivo. Todos os testes pulam se os artefatos ainda não foram gerados.
"""
from __future__ import annotations

import csv
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
IMAGERY = ROOT / "data" / "processed" / "imagery"
ANOS_ANCORA = [2000, 2005, 2010, 2015, 2020, 2025]
CAMADAS_CULTIVO = ["cultivo_sequeiro", "cultivo_irrigado"]
CAMADAS_EXCLUSIVAS = ["urbano", "industrial", "reassentamento", "agua"]


def _caminho(camada: str, ano: int | None) -> Path:
    sufixo = f"_{ano}" if ano is not None else ""
    return IMAGERY / f"{camada}{sufixo}_30m_32736.tif"


def _anos_com_cultivo() -> list[int]:
    return [a for a in ANOS_ANCORA if all(_caminho(c, a).exists() for c in CAMADAS_CULTIVO)]


def test_cultivo_ainda_nao_gerado_e_marcado():
    if not _anos_com_cultivo():
        pytest.skip("data/processed/imagery/ ainda não tem cultivo_* — rode cultivo.py")


def test_cultivo_nao_sobrepoe_construido_pegada_ou_agua():
    """§10: cultivo não pode sobrepor urbano/industrial/reassentamento/agua — a mesma
    regra de exclusividade que protege 'nenhuma cava contada como urbano' se estende a
    'nenhuma cava contada como cultivo'."""
    rasterio = pytest.importorskip("rasterio")
    anos = _anos_com_cultivo()
    if not anos:
        pytest.skip("cultivo ainda não gerado")

    problemas = []
    for ano in anos:
        with rasterio.open(_caminho("cultivo_sequeiro", ano)) as src:
            seq = src.read(1).astype(bool)
        with rasterio.open(_caminho("cultivo_irrigado", ano)) as src:
            irr = src.read(1).astype(bool)
        if (seq & irr).any():
            problemas.append(f"{ano}: cultivo_sequeiro e cultivo_irrigado se sobrepõem")
        for camada in CAMADAS_EXCLUSIVAS:
            caminho = _caminho(camada, ano)
            if not caminho.exists():
                continue
            with rasterio.open(caminho) as src:
                mask = src.read(1).astype(bool)
            if (seq & mask).any():
                problemas.append(f"{ano}: cultivo_sequeiro sobrepõe {camada}")
            if (irr & mask).any():
                problemas.append(f"{ano}: cultivo_irrigado sobrepõe {camada}")
    assert not problemas, "; ".join(problemas)


def test_cultivo_sequeiro_e_subconjunto_de_solo_exposto():
    """cultivo_sequeiro é um RECORTE de solo_exposto (não uma camada nova na partição
    da AOI) — verificado, não presumido."""
    rasterio = pytest.importorskip("rasterio")
    anos = _anos_com_cultivo()
    if not anos:
        pytest.skip("cultivo ainda não gerado")
    problemas = []
    for ano in anos:
        caminho_solo = _caminho("solo_exposto", ano)
        if not caminho_solo.exists():
            continue
        with rasterio.open(_caminho("cultivo_sequeiro", ano)) as src:
            seq = src.read(1).astype(bool)
        with rasterio.open(caminho_solo) as src:
            solo = src.read(1).astype(bool)
        if (seq & ~solo).any():
            problemas.append(f"{ano}: cultivo_sequeiro tem pixel fora de solo_exposto")
    assert not problemas, "; ".join(problemas)


def test_cultivo_irrigado_e_subconjunto_de_vegetacao():
    rasterio = pytest.importorskip("rasterio")
    anos = _anos_com_cultivo()
    if not anos:
        pytest.skip("cultivo ainda não gerado")
    problemas = []
    for ano in anos:
        caminho_veg = _caminho("vegetacao", ano)
        if not caminho_veg.exists():
            continue
        with rasterio.open(_caminho("cultivo_irrigado", ano)) as src:
            irr = src.read(1).astype(bool)
        with rasterio.open(caminho_veg) as src:
            veg = src.read(1).astype(bool)
        if (irr & ~veg).any():
            problemas.append(f"{ano}: cultivo_irrigado tem pixel fora de vegetacao")
    assert not problemas, "; ".join(problemas)


def test_varzea_ainda_nao_gerada_e_marcada():
    if not _caminho("varzea", None).exists():
        pytest.skip("data/processed/imagery/varzea_30m_32736.tif ausente — rode varzea.py")


def test_varzea_tem_area_plausivel_e_fica_dentro_da_aoi():
    """A várzea é geomorfologia estática; não deve cobrir a AOI inteira nem ser vazia."""
    rasterio = pytest.importorskip("rasterio")
    caminho = _caminho("varzea", None)
    if not caminho.exists():
        pytest.skip("varzea ainda não gerada")
    with rasterio.open(caminho) as src:
        mask = src.read(1).astype(bool)
        pixel_km2 = abs(src.transform.a * src.transform.e) / 1e6
    area = float(mask.sum()) * pixel_km2
    aoi_km2 = mask.size * pixel_km2
    assert 0 < area < 0.9 * aoi_km2, (
        f"várzea = {area:.1f} km² de {aoi_km2:.1f} km² da AOI — fora do plausível "
        "(vazia ou cobrindo quase toda a AOI, sinal de erro no HAND aproximado)"
    )


def test_acuracia_cultivo_publica_prevalencia_e_ic(tmp_path=None):
    """§10 (ADR 0009 estendido): acurácia por classe, com prevalência e IC — nunca só
    acurácia global."""
    caminho = ROOT / "data" / "processed" / "acuracia_cultivo_por_ano.csv"
    if not caminho.exists():
        pytest.skip("acuracia_cultivo_por_ano.csv ainda não gerado")
    with caminho.open(encoding="utf-8") as fh:
        linhas = list(csv.DictReader(fh))
    assert linhas, "acuracia_cultivo_por_ano.csv vazio"
    campos_obrigatorios = [
        "prevalencia_mapa_cultivo_sequeiro",
        "prevalencia_mapa_cultivo_irrigado",
        "acuracia_usuario_cultivo_sequeiro",
        "acuracia_usuario_cultivo_irrigado",
        "ic95_usuario_cultivo_sequeiro",
        "ic95_usuario_cultivo_irrigado",
        "kappa",
    ]
    faltando = [c for c in campos_obrigatorios if c not in linhas[0]]
    assert not faltando, f"colunas obrigatórias ausentes: {faltando}"


def test_acuracia_cultivo_sequeiro_ruim_esta_declarada_em_adr():
    """docs/ADR/0012 documenta acurácia do usuário = 0,000 para cultivo_sequeiro (2020).
    Este contrato garante que a limitação continua escrita, não silenciada numa futura
    reexecução que produza outro número sem atualizar o ADR."""
    adr = ROOT / "docs" / "ADR" / "0012-cultivo-sequeiro-nao-defensavel-sem-serie-intra-anual.md"
    assert adr.exists(), "ADR 0012 (limitação de cultivo_sequeiro) ausente"
    texto = adr.read_text(encoding="utf-8")
    assert "cultivo_sequeiro" in texto

    # O VALOR vem da fonte, não deste arquivo (ORCHESTRATION_LOG.md 4-08).
    #
    # A versão anterior exigia o literal "0,000". Uma reexecução que desse 0,05 obrigaria
    # a atualizar o ADR — e este contrato reprovaria **a atualização correta**, defendendo
    # um número obsoleto. Foi exatamente o que aconteceu com `test_figuras.py` e a faixa
    # 0,27–0,63 (4-07). A regra que saiu de lá: contrato verifica RELAÇÃO, não valor;
    # todo valor vem da fonte em tempo de execução.
    #
    # A relação que este contrato guarda é: **o ADR declara a acurácia que o CSV mediu.**
    import csv as _csv

    csv_ac = ROOT / "data" / "processed" / "acuracia_cultivo_por_ano.csv"
    if not csv_ac.exists():
        return
    with csv_ac.open(encoding="utf-8", newline="") as fh:
        vals = []
        for linha in _csv.DictReader(fh):
            try:
                vals.append(float(linha["acuracia_usuario_cultivo_sequeiro"]))
            except (KeyError, TypeError, ValueError):
                pass
    if not vals:
        return
    medido = min(vals)
    # Casamento com fronteira: "0,0" é substring de "0,047", e sem a fronteira o teste
    # aceitaria qualquer valor que comece igual — passaria por vacuidade.
    import re as _re

    formas = [
        f"{medido:.3f}".replace(".", ","),
        f"{medido:.2f}".replace(".", ","),
        f"{medido:.1f}".replace(".", ","),
    ]
    achou = any(
        _re.search(rf"(?<![\d,]){_re.escape(f)}(?![\d])", texto) for f in formas
    )
    assert achou, (
        f"docs/ADR/0012 não declara a acurácia do usuário medida para cultivo_sequeiro "
        f"({medido:.3f}, de acuracia_cultivo_por_ano.csv). Se a reexecução mudou o valor, "
        "atualize o ADR — este contrato exige que ele diga o número que o CSV mediu, "
        "não um número em particular."
    )
