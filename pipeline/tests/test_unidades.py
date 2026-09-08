"""Contratos sobre o vocabulário de unidades geográficas (config/unidades.yaml).

Motivo: as famílias `forma_urbana` e `demografia` chegaram à Fase 2 sem nenhuma unidade
em comum, e uma delas descrevia geografias diferentes sob nomes parecidos — 'moatize'
é a vila-sede, 'Distrito de Moatize' é o distrito inteiro. Uma razão população/área que
misturasse as duas seria inválida, e nada no repositório teria acusado.
Ver ORCHESTRATION_LOG.md 2-02.
"""
from __future__ import annotations

import csv
from pathlib import Path

import pytest
import yaml

ROOT = Path(__file__).resolve().parents[2]
STATS = ROOT / "data" / "processed" / "stats_by_year_by_unit.csv"


@pytest.fixture(scope="module")
def unidades() -> dict:
    with (ROOT / "config" / "unidades.yaml").open(encoding="utf-8") as fh:
        return yaml.safe_load(fh)["unidades"]


def test_toda_unidade_declara_geografia_e_comparabilidade(unidades):
    faltando = []
    for chave, u in unidades.items():
        for campo in ("rotulo", "geografia", "tipo", "fonte_geometria",
                      "comparavel_entre_familias"):
            if campo not in u:
                faltando.append(f"{chave}: sem '{campo}'")
        # Quem não é comparável tem de dizer por quê — senão a restrição vira folclore.
        if u.get("comparavel_entre_familias") is False and not u.get("motivo_nao_comparavel"):
            if u.get("tipo") not in {"reassentamento", "industrial", "agregado"}:
                faltando.append(f"{chave}: não comparável sem motivo declarado")
    assert not faltando, "; ".join(faltando)


def test_stats_usa_apenas_unidades_do_vocabulario(unidades):
    """Nenhuma linha do CSV de núcleo pode usar unidade fora do vocabulário.

    Sem isto, 'tete' e 'Cidade de Tete' convivem como se fossem coisas diferentes — e
    'moatize' e 'Distrito de Moatize' convivem como se fossem a mesma.
    """
    if not STATS.exists():
        pytest.skip("stats_by_year_by_unit.csv ainda não consolidado")

    validos = set(unidades) | {u["rotulo"] for u in unidades.values()}
    with STATS.open(encoding="utf-8", newline="") as fh:
        usadas = {linha["unidade_geografica"] for linha in csv.DictReader(fh)}

    fora = sorted(usadas - validos)
    assert not fora, (
        f"unidades fora de config/unidades.yaml: {fora}. "
        "Acrescente ao vocabulário ou renomeie para um id existente."
    )


def test_nao_ha_par_de_unidades_com_geografia_ambigua(unidades):
    """Dois ids não podem ter rótulos que se confundam se a geografia for diferente.

    'Vila de Moatize' e 'Distrito de Moatize' são geografias distintas e precisam de
    rótulos que não permitam confundi-las ao ler uma tabela.
    """
    problemas = []
    itens = list(unidades.items())
    for i, (ka, a) in enumerate(itens):
        for kb, b in itens[i + 1:]:
            ra, rb = a["rotulo"].lower(), b["rotulo"].lower()
            mesma_raiz = ra.split()[-1] == rb.split()[-1]
            if mesma_raiz and a["geografia"] != b["geografia"]:
                # Aceitável só se ambos declararem o tipo, que é o que desambigua.
                if a["tipo"] == b["tipo"]:
                    problemas.append(
                        f"{ka} e {kb} compartilham a raiz do rótulo, têm geografias "
                        f"diferentes e o mesmo tipo ({a['tipo']})"
                    )
    assert not problemas, "; ".join(problemas)


def test_pcodes_das_duas_fontes_nao_sao_intercambiaveis(unidades):
    """Geometria (COD-AB) e população (COD-PS) usam esquemas de P-code diferentes.

    Verificado em 2026-09-08: no COD-AB a província de Tete é MZ05 e a Cidade de Tete é
    MZ0501; no COD-PS a província é MZ10 e a cidade é MZ1006. E MZ1006 **existe** no
    COD-AB — é Matutuine, distrito da província de Maputo, a cerca de 1.500 km.

    Um merge por P-code entre as duas fontes **tem sucesso** e atribui a população de
    Tete a Matutuine: nenhuma chave faltante, nenhum aviso. Este contrato existe para que
    o repositório registre a incompatibilidade e para que qualquer alteração que a
    "resolva" igualando os códigos falhe aqui primeiro.
    """
    gpd = pytest.importorskip("geopandas")

    zip_ab = ROOT / "data" / "raw" / "hdx_cod-ab-moz_admin_boundaries.geojson.zip"
    csv_ps = ROOT / "data" / "raw" / "hdx_cod-ps-moz_admpop_adm2_2017_v2.csv"
    if not zip_ab.exists() or not csv_ps.exists():
        pytest.skip("fontes de limites ou população ainda não espelhadas")

    ab = gpd.read_file(f"zip://{zip_ab}!moz_admin2.geojson")
    with csv_ps.open(encoding="utf-8-sig", newline="") as fh:
        ps = list(csv.DictReader(fh))

    ab_por_code = dict(zip(ab["adm2_pcode"], ab["adm2_name"], strict=False))
    ps_tete = next((x for x in ps if x.get("ADM2_PT") == "Cidade De Tete"), None)
    assert ps_tete, "COD-PS não traz 'Cidade De Tete'"

    code_ps = ps_tete["ADM2_PCODE"]
    nome_no_ab = ab_por_code.get(code_ps)

    # O ponto do contrato: o código do COD-PS resolve, no COD-AB, para OUTRA entidade.
    # Se um dia os esquemas convergirem, esta asserção falha e o alerta é revisado.
    assert nome_no_ab != "Cidade de Tete", (
        f"O P-code {code_ps} do COD-PS agora resolve para 'Cidade de Tete' no COD-AB. "
        "Os esquemas podem ter convergido — reveja config/unidades.yaml e a regra de "
        "cruzamento por nome antes de permitir merge por código."
    )

    # E o vocabulário tem de registrar os dois códigos, para ninguém adivinhar.
    tete = unidades["tete"]
    assert tete.get("pcode_cod_ab") and tete.get("pcode_cod_ps"), (
        "config/unidades.yaml não declara os dois P-codes de 'tete'"
    )
    assert tete["pcode_cod_ab"] != tete["pcode_cod_ps"], (
        "os dois P-codes declarados são iguais — um deles está errado"
    )
