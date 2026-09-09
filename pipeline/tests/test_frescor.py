"""Contrato de frescor: nenhum produto pode ser mais antigo que os seus insumos.

Defeito real (ORCHESTRATION_LOG.md 2-08): a reabertura da Fase 1 regerou as camadas
classificadas às 09:48; `data/processed/stats_by_year_by_unit.csv` era de 09:09 e
continuou declarando 1,06 km² de área industrial em 2015, quando a camada nova tem
30,15 km². Os contratos de esquema, faixa e exclusividade **todos passavam** — nenhum
comparava data.

O grafo do Makefile declara a dependência (`metrics: imagery`), mas `make` só compara
data de arquivos quando os pré-requisitos são arquivos, e os alvos aqui são fase a fase.
Este contrato cobre a lacuna sem exigir reescrever o Makefile em nível de arquivo.
"""
from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]

# produto → padrões de insumo dos quais ele deriva
DERIVACOES: dict[str, list[str]] = {
    "data/processed/stats_by_year_by_unit.csv": [
        "data/interim/stats_*.csv",
    ],
    "data/interim/stats_forma_urbana.csv": [
        "data/processed/imagery/urbano_*_30m_32736.tif",
        "data/processed/imagery/industrial_*_30m_32736.tif",
        "data/processed/imagery/reassentamento_*_30m_32736.tif",
    ],
    "data/interim/stats_demografia.csv": [
        "data/raw/hdx_cod-ps-moz_admpop_adm2_2017_v2.csv",
        "data/raw/hdx_cod-ps-moz_admpop_adm2_2025.csv",
    ],
    "data/processed/acuracia_por_ano.csv": [
        "data/processed/validacao/rotulos_interpretados.csv",
    ],
    "data/processed/cultivo_por_ano.csv": [
        "data/processed/imagery/vegetacao_*_30m_32736.tif",
        "data/processed/imagery/solo_exposto_*_30m_32736.tif",
        "data/processed/imagery/ndvi_amplitude_*_30m_32736.tif",
    ],
    "data/processed/imagery/varzea_30m_32736.tif": [
        "data/raw/copernicus_dem_glo30_S17_00_E033_00.tif",
        "data/raw/copernicus_dem_glo30_S17_00_E034_00.tif",
        "data/raw/hydrorivers_af_v10.gdb.zip",
    ],
    "data/processed/cultivo_varzea_por_ano.csv": [
        "data/processed/imagery/varzea_30m_32736.tif",
        "data/processed/imagery/cultivo_sequeiro_*_30m_32736.tif",
        "data/processed/imagery/cultivo_irrigado_*_30m_32736.tif",
    ],
    "data/processed/acuracia_cultivo_por_ano.csv": [
        "data/processed/validacao/rotulos_interpretados_cultivo.csv",
    ],
    "data/processed/imagery/adensamento_2020_2025_240m_32736.tif": [
        "data/processed/imagery/urbano_*_30m_32736.tif",
        "data/processed/imagery/reassentamento_*_30m_32736.tif",
        "data/processed/imagery/industrial_*_30m_32736.tif",
        "data/raw/viirs_like_*_tete_aoi.tif",
        "data/raw/open_buildings_v3_aoi.csv",
    ],
    "data/processed/adensamento_2020_2025_por_unidade.csv": [
        "data/processed/imagery/urbano_*_30m_32736.tif",
        "data/processed/imagery/reassentamento_*_30m_32736.tif",
        "data/processed/imagery/industrial_*_30m_32736.tif",
        "data/raw/viirs_like_*_tete_aoi.tif",
        "data/raw/open_buildings_v3_aoi.csv",
    ],
    "data/processed/adensamento_sensibilidade.csv": [
        "data/processed/imagery/urbano_*_30m_32736.tif",
        "data/processed/imagery/reassentamento_*_30m_32736.tif",
        "data/processed/imagery/industrial_*_30m_32736.tif",
        "data/raw/viirs_like_*_tete_aoi.tif",
        "data/raw/open_buildings_v3_aoi.csv",
    ],
}

# Folga para diferenças de sistema de arquivos e execuções encadeadas no mesmo segundo.
TOLERANCIA_S = 2.0


def test_produtos_nao_sao_mais_antigos_que_os_insumos():
    problemas = []
    for produto, padroes in DERIVACOES.items():
        alvo = ROOT / produto
        if not alvo.exists():
            continue
        t_produto = alvo.stat().st_mtime

        for padrao in padroes:
            for insumo in sorted(ROOT.glob(padrao)):
                atraso = insumo.stat().st_mtime - t_produto
                if atraso > TOLERANCIA_S:
                    problemas.append(
                        f"{produto} é {atraso / 60:.0f} min mais antigo que "
                        f"{insumo.relative_to(ROOT)} — reexecute a etapa"
                    )
    # Uma linha por produto basta; não inundar com um insumo de cada vez.
    vistos, unicos = set(), []
    for p in problemas:
        chave = p.split(" é ")[0]
        if chave not in vistos:
            vistos.add(chave)
            unicos.append(p)
    assert not unicos, "; ".join(unicos)


def test_toda_derivacao_declarada_aponta_para_caminhos_existentes():
    """Uma derivação que aponta para caminho inexistente não protege nada.

    Se um produto for renomeado, este contrato avisa em vez de silenciar.
    """
    problemas = []
    for produto, padroes in DERIVACOES.items():
        if not (ROOT / produto).exists():
            continue  # produto ainda não gerado: legítimo
        for padrao in padroes:
            if not list(ROOT.glob(padrao)):
                problemas.append(f"{produto}: padrão de insumo '{padrao}' não casa com nada")
    assert not problemas, "; ".join(problemas)
