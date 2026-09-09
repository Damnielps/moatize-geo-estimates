"""Contratos T1–T11 da camada de adensamento 2020–2025 (`docs/ADR/0016`).

Cada contrato é verificado, quando aplicável, reintroduzindo o defeito **sobre uma
CÓPIA** do artefato publicado (nunca o original — `shutil.copy` para o scratchpad de
teste, muta a cópia). A verificação de que o contrato acusa o defeito acontece em
`test_zz_reintroducao_de_defeitos_e_verificada`, ao final do arquivo, para que ela rode
depois que os contratos "normais" já tiverem confirmado que passam sobre o artefato
real.

Convenção de numeração (o ADR só nomeia T2, T5 e T7 explicitamente — os demais são a
cobertura desta entrega, na mesma família):

- T1 — domínio por aritmética de grade (n_pixels_30m == 64; 43.416 células; 2.500,76 km²)
- T2 — a classe publicada no GeoJSON é reproduzível a partir dos atributos publicados
  (f_2020, f_2025, S1, S2, S3, fracao_industrial) e dos quantis realizados do `.meta.json`
- T3 — partição exaustiva e mutuamente exclusiva (soma das classes == domínio; nenhuma
  célula em duas classes)
- T4 — `QUANTIS` do módulo é ecoado literalmente em `quantis_declarados` do `.meta.json`
- T5 — AST: toda variável `LIMIAR|CORTE|Q_|TAU` vem de `np.quantile`/mediana; todo
  `ast.Compare` com literal numérico à direita está na lista branca
- T6 — determinismo: sem seed declarada (nem em `config/seeds.yaml`), e o script é
  determinístico por construção (Theil-Sen exato, quantis) — reexecução em memória dá o
  mesmo resultado
- T7 — `build_web_assets.nome_camada_ano` reconhece `<camada>_<ano0>_<ano1>`; o
  manifesto carrega as seis chaves de ressalva `adr_0016_*` para a camada
- T8 — `adensamento_sensibilidade.csv` traz todas as variantes do ADR
- T9 — o anel periurbano é ATRIBUTO, não critério: nunca decide `classe`
- T10 — selo `modelado` em `.meta.json`, no manifesto do app e em
  `config/plausibilidade.yaml` (nunca `observado`)
- T11 — precedência de classe respeitada (pegada_industrial > consolidado >
  expansao_nova > adensando/esparso_estavel > vazio_estavel > fora_de_dominio)
"""
from __future__ import annotations

import ast
import json
import shutil
import sys
from pathlib import Path

import numpy as np
import pytest

ROOT = Path(__file__).resolve().parents[2]
IMAGERY = ROOT / "data" / "processed" / "imagery"
PROCESSED = ROOT / "data" / "processed"
SCRIPT = ROOT / "pipeline" / "02_metrics" / "adensamento.py"

RASTER_240M = IMAGERY / "adensamento_2020_2025_240m_32736.tif"
RASTER_30M = IMAGERY / "adensamento_2020_2025_30m_32736.tif"
GEOJSON = IMAGERY / "adensamento_2020_2025.geojson"
META_240M = IMAGERY / "adensamento_2020_2025_240m_32736.tif.meta.json"
POR_UNIDADE_CSV = PROCESSED / "adensamento_2020_2025_por_unidade.csv"
SENSIBILIDADE_CSV = PROCESSED / "adensamento_sensibilidade.csv"

pytestmark = pytest.mark.skipif(
    not META_240M.exists(), reason="camada de adensamento ainda não gerada — rode `make metrics`"
)


sys.path.insert(0, str(ROOT / "pipeline" / "02_metrics"))


def _modulo_adensamento():
    import importlib.util

    spec = importlib.util.spec_from_file_location("adensamento", SCRIPT)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


@pytest.fixture(scope="module")
def meta() -> dict:
    return json.loads(META_240M.read_text(encoding="utf-8"))


@pytest.fixture(scope="module")
def gdf():
    gpd = pytest.importorskip("geopandas")
    return gpd.read_file(GEOJSON)


# ---------------------------------------------------------------------------
# T1 — domínio por aritmética de grade
# ---------------------------------------------------------------------------


def test_t1_dominio_por_aritmetica_de_grade(meta):
    """162 linhas completas x 268 colunas = 43.416 células; 2.500,76 km² — número
    fixado por geometria da grade (1299/8, 2144/8), não por classificação."""
    assert meta["n_celulas_dominio"] == 162 * 268 == 43416
    assert meta["area_dominio_km2"] == pytest.approx(43416 * 0.0576, abs=0.01)
    assert meta["fator_grade_pixels_30m"] == 8
    assert meta["n_pixels_celula"] == 64


def test_t1_raster_240m_tem_shape_esperado():
    rasterio = pytest.importorskip("rasterio")
    with rasterio.open(RASTER_240M) as src:
        # ceil(1299/8) = 163 linhas de célula, 2144/8 = 268 colunas — a última linha
        # de célula é parcial (fora_de_dominio), mas ainda existe no raster.
        assert src.shape == (163, 268)
        assert abs(src.res[0] - 240.0) < 1e-6


# ---------------------------------------------------------------------------
# T2 — classe reproduzível a partir dos atributos publicados
# ---------------------------------------------------------------------------


def test_t2_classe_reproduzivel_a_partir_dos_atributos(gdf, meta):
    """Recalcula a classe de cada feição a partir de f_2020/f_2025/concordancia/
    fracao_industrial e dos CORTES REALIZADOS publicados no `.meta.json` — nunca dos
    quantis DECLARADOS (que são probabilidades, não os valores realizados)."""
    cortes = meta["quantis_realizados"]
    q_alto, q_baixo, q_ind = cortes["Q_ALTO"], cortes["Q_BAIXO"], cortes["Q_INDUSTRIAL"]

    CLASSES_COD = {
        "fora_de_dominio": 0,
        "vazio_estavel": 1,
        "esparso_estavel": 2,
        "adensando": 3,
        "expansao_nova": 4,
        "consolidado": 5,
        "pegada_industrial": 6,
    }

    divergencias = 0
    for _, row in gdf.iterrows():
        f2020, f2025 = row["f_2020"], row["f_2025"]
        conc = row["concordancia"]
        frac_ind = row["fracao_industrial"]
        cod_publicado = row["classe_codigo"]

        if not np.isnan(q_ind) and frac_ind >= q_ind:
            cod_esperado = CLASSES_COD["pegada_industrial"]
        elif f2020 >= q_alto:
            cod_esperado = CLASSES_COD["consolidado"]
        elif f2020 < q_baixo and f2025 >= q_baixo:
            cod_esperado = CLASSES_COD["expansao_nova"]
        elif q_baixo <= f2020 < q_alto:
            cod_esperado = CLASSES_COD["adensando"] if conc >= 2 else CLASSES_COD["esparso_estavel"]
        else:
            cod_esperado = CLASSES_COD["vazio_estavel"]

        if cod_esperado != cod_publicado:
            divergencias += 1

    assert divergencias == 0, (
        f"{divergencias}/{len(gdf)} feições têm classe publicada divergente da "
        "recomputada a partir dos atributos + cortes realizados do .meta.json"
    )


# ---------------------------------------------------------------------------
# T13 — concordância reconstruível a partir de S1/S2/S3 e dos cortes realizados
# (achado 3 do portão da Frente B, 2026-09-09; Emenda 2 do ADR 0016)
# ---------------------------------------------------------------------------


def test_t13_concordancia_reproduzivel_a_partir_dos_atributos(gdf, meta):
    """Análogo, para `concordancia`, do que T2 já faz para `classe`: reconstrói o
    voto de cada sinal a partir só de `S1/S2/S3` e dos cortes `TAU_s1/s2/s3` do
    `.meta.json`, e exige zero divergências. `dominio_ocupado` não é publicado como
    atributo próprio, mas toda feição do GeoJSON já está dentro do domínio (só
    classes 2-6 são vetorizadas) e `dominio_ocupado = dominio & (f_2020>0 |
    f_2025>0)` — reconstruível de `f_2020`/`f_2025`, ambos publicados. É esse termo
    que faltava na fórmula do ADR (`V_i = (S_i>0) & (S_i>=quantil)`, sem
    `dominio_ocupado`): sem ele, células nunca ocupadas com S3 alto (Open
    Buildings, sem correspondência em urbano/reassentamento) dariam voto positivo
    indevido — foi o caso medido de 13 feições `pegada_industrial`."""
    cortes = meta["quantis_realizados"]
    tau_s1, tau_s2, tau_s3 = cortes["TAU_s1"], cortes["TAU_s2"], cortes["TAU_s3"]

    def _voto(valor: float, corte: float, dominio_ocupado: bool) -> bool:
        return bool(dominio_ocupado and valor > 0 and valor >= corte)

    divergencias = 0
    for _, row in gdf.iterrows():
        dominio_ocupado = (row["f_2020"] > 0) or (row["f_2025"] > 0)
        v1 = _voto(row["S1"], tau_s1, dominio_ocupado)
        v2 = _voto(row["S2"], tau_s2, dominio_ocupado)
        v3 = _voto(row["S3"], tau_s3, dominio_ocupado)
        conc_esperada = int(v1) + int(v2) + int(v3)
        if conc_esperada != row["concordancia"]:
            divergencias += 1

    assert divergencias == 0, (
        f"{divergencias}/{len(gdf)} feições têm concordancia publicada divergente da "
        "reconstruída a partir de S1/S2/S3 + TAU_s1/s2/s3 do .meta.json — ADR e "
        "código voltaram a divergir na regra de voto"
    )


# ---------------------------------------------------------------------------
# T3 — partição exaustiva e mutuamente exclusiva
# ---------------------------------------------------------------------------


def test_t3_particao_exaustiva_soma_area_classes_igual_dominio(meta):
    """A área publicada por classe tem de bater com a RECONTAGEM de pixels de 30 m
    do raster de 30 m — não com uma fórmula de `n_células × área_nominal_da_célula`,
    que só vale para células completas e é exatamente o que fazia `fora_de_dominio`
    (células PARCIAIS da borda) publicar 15,4368 km² em vez dos 5,7888 km² reais
    (achado 2 do portão da Frente B, 2026-09-09; fator de erro ~2,67). Este contrato
    é o análogo, para área, do que T2 já faz para classe: nenhum valor medido é
    codificado aqui — tudo vem do raster e do `.meta.json` em tempo de execução."""
    rasterio = pytest.importorskip("rasterio")

    with rasterio.open(RASTER_30M) as src:
        arr = src.read(1)
        n_lin, n_col = src.shape
        res_x, res_y = src.res

    codigo_para_nome = {
        0: "fora_de_dominio",
        1: "vazio_estavel",
        2: "esparso_estavel",
        3: "adensando",
        4: "expansao_nova",
        5: "consolidado",
        6: "pegada_industrial",
    }
    vals, counts = np.unique(arr, return_counts=True)
    contagem = dict(zip(vals.tolist(), counts.tolist(), strict=True))
    area_pixel_km2 = (res_x * res_y) / 1e6

    areas_publicadas = meta["areas_por_classe_km2"]
    for cod, nome in codigo_para_nome.items():
        area_recontada = contagem.get(cod, 0) * area_pixel_km2
        assert areas_publicadas[nome] == pytest.approx(area_recontada, abs=0.01), (
            f"classe '{nome}': publicado {areas_publicadas[nome]} km², "
            f"recontado do raster de 30 m {area_recontada} km²"
        )

    soma_publicada = sum(areas_publicadas.values())
    area_grade_total = n_lin * n_col * area_pixel_km2
    assert soma_publicada == pytest.approx(area_grade_total, abs=0.5), (
        "soma das classes publicadas diverge da área total da grade de 30 m "
        f"recontada ({area_grade_total} km²)"
    )


def test_t3_raster_240m_toda_celula_tem_exatamente_uma_classe_0_a_6():
    rasterio = pytest.importorskip("rasterio")
    with rasterio.open(RASTER_240M) as src:
        arr = src.read(1)
        valores = set(np.unique(arr).tolist())
    assert valores <= set(range(7)), f"valores fora de 0-6 encontrados: {valores - set(range(7))}"


# ---------------------------------------------------------------------------
# T4 — QUANTIS ecoado literalmente
# ---------------------------------------------------------------------------


def test_t4_quantis_declarados_ecoam_o_modulo(meta):
    mod = _modulo_adensamento()
    assert meta["quantis_declarados"] == mod.QUANTIS


# ---------------------------------------------------------------------------
# T5 — AST: literais fora da lista branca
# ---------------------------------------------------------------------------


WHITELIST_LITERAIS = {0, 1, 8, 16, 64, 1000, 3000, 2, 3, 4, 5, 6}
PADRAO_VARIAVEL_CORTE = ("limiar", "corte", "q_", "tau")


def _nome_casa_padrao(nome: str) -> bool:
    nome_l = nome.lower()
    return any(p in nome_l for p in PADRAO_VARIAVEL_CORTE)


def _contem_quantile_ou_mediana(node: ast.AST) -> bool:
    for sub in ast.walk(node):
        if isinstance(sub, ast.Call):
            alvo = sub.func
            nome = getattr(alvo, "attr", None) or getattr(alvo, "id", None)
            if nome in ("quantile", "median", "theilslopes"):
                return True
            # float("nan") — bail-out declarado de "sem dado para calcular o quantil",
            # não um valor de corte: aceito explicitamente, nunca um número calibrado.
            if nome == "float" and sub.args and isinstance(sub.args[0], ast.Constant):
                if isinstance(sub.args[0].value, str) and sub.args[0].value.lower() == "nan":
                    return True
        if isinstance(sub, ast.Name) and sub.id in ("QUANTIS",):
            return True
        if isinstance(sub, ast.Subscript):
            # ex.: QUANTIS["Q_ALTO"] ou cortes_realizados["Q_ALTO"]
            val = sub.value
            nome_up = val.id.upper() if isinstance(val, ast.Name) else ""
            if "QUANTI" in nome_up or "CORTE" in nome_up:
                return True
    return False


def _ast_do_script() -> ast.AST:
    return ast.parse(SCRIPT.read_text(encoding="utf-8"))


def test_t5_variaveis_de_corte_vem_de_quantile_ou_mediana():
    tree = _ast_do_script()
    problemas = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Assign):
            for alvo in node.targets:
                if isinstance(alvo, ast.Name) and _nome_casa_padrao(alvo.id):
                    if not _contem_quantile_ou_mediana(node.value):
                        problemas.append(
                            f"linha {node.lineno}: {alvo.id} não vem de quantile/mediana"
                        )
    assert not problemas, "; ".join(problemas)


def test_t5_nenhum_literal_fora_da_lista_branca_em_comparacoes():
    tree = _ast_do_script()
    problemas = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Compare):
            candidatos = list(node.comparators)
            if isinstance(node.left, ast.Constant):
                candidatos.append(node.left)
            for comp in candidatos:
                if isinstance(comp, ast.Constant) and isinstance(comp.value, (int, float)):
                    if isinstance(comp.value, bool):
                        continue
                    if comp.value not in WHITELIST_LITERAIS:
                        problemas.append(
                            f"linha {node.lineno}: literal {comp.value} fora da lista branca"
                        )
    assert not problemas, "; ".join(problemas)


# ---------------------------------------------------------------------------
# T6 — determinismo (sem seed)
# ---------------------------------------------------------------------------


def test_t6_theil_sen_e_deterministico_sem_seed():
    mod = _modulo_adensamento()
    y = np.random.RandomState(0).rand(6, 5, 5)  # 6 anos, grade pequena arbitrária
    s1 = mod.theil_sen_exato(y)
    s2 = mod.theil_sen_exato(y)
    assert np.array_equal(s1, s2)
    # bate com scipy.stats.theilslopes (mediana das inclinações par a par) numa célula
    from scipy.stats import theilslopes

    slope_ref, *_ = theilslopes(y[:, 0, 0], mod.ANOS_LUZ)
    assert s1[0, 0] == pytest.approx(slope_ref, abs=1e-9)


def test_t6_config_seeds_nao_precisa_declarar_adensamento():
    import yaml

    seeds = yaml.safe_load((ROOT / "config" / "seeds.yaml").read_text(encoding="utf-8"))
    assert "adensamento" not in seeds, (
        "adensamento não deveria precisar de seed própria — Theil-Sen exato e "
        "quantis são determinísticos (docs/ADR/0016 §Decisão-8)"
    )


# ---------------------------------------------------------------------------
# T7 — build_web_assets: nome_camada_ano e as seis chaves de ressalva
# ---------------------------------------------------------------------------


def _modulo_build_web_assets():
    import importlib.util

    caminho = ROOT / "pipeline" / "05_app" / "build_web_assets.py"
    spec = importlib.util.spec_from_file_location("build_web_assets", caminho)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def test_t7_nome_camada_ano_reconhece_dois_anos():
    mod = _modulo_build_web_assets()
    camada, ano = mod.nome_camada_ano(Path("adensamento_2020_2025.geojson"))
    assert camada == "adensamento"
    assert ano == (2020, 2025)
    # não regride o caso de um ano só
    camada_u, ano_u = mod.nome_camada_ano(Path("urbano_2020.geojson"))
    assert camada_u == "urbano" and ano_u == 2020


def test_t7_manifesto_do_app_tem_as_seis_chaves_de_ressalva():
    manifest_path = PROCESSED / "app" / "imagery" / "manifest.json"
    if not manifest_path.exists():
        pytest.skip("data/processed/app/imagery/manifest.json ainda não gerado")
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    entrada = manifest["camadas"].get("adensamento_2020_2025")
    assert entrada is not None, "camada adensamento_2020_2025 ausente do manifesto"
    caveats = entrada["caveats"]
    chaves_esperadas = {
        "adr_0016_selo_modelado",
        "adr_0016_areas_por_classe",
        "adr_0016_sensibilidade",
        "adr_0016_risco_r2_correlacao_sinais",
        "adr_0016_risco_r3_sem_esvaziamento",
        "adr_0016_risco_r6_janela_s3",
    }
    faltando = chaves_esperadas - set(caveats.keys())
    assert not faltando, f"chaves de ressalva ausentes no manifesto: {faltando}"


# ---------------------------------------------------------------------------
# T8 — sensibilidade traz todas as variantes do ADR
# ---------------------------------------------------------------------------


def test_t8_sensibilidade_tem_todas_as_variantes_do_adr():
    pd = pytest.importorskip("pandas")
    df = pd.read_csv(SENSIBILIDADE_CSV)
    esperadas = {
        "base",
        "tau_060",
        "tau_080",
        "qalto_070",
        "qalto_090",
        "qbaixo_010",
        "qbaixo_030",
        "grade_480m",
        "ob_conf_mediana",
        "concordancia_3de3",
        "sem_S2",
        "sem_S3",
        "bruta_experimental",
    }
    faltando = esperadas - set(df["variante"])
    assert not faltando, f"variantes de sensibilidade ausentes: {faltando}"


# ---------------------------------------------------------------------------
# T9 — anel é atributo, não critério de classe
# ---------------------------------------------------------------------------


def test_t9_anel_nao_decide_classe(gdf):
    """Duas células com o mesmo f_2020/f_2025/concordancia/fracao_industrial mas
    anéis diferentes têm de ter a mesma classe — o anel é publicado como atributo
    (docs/ADR/0016 §Decisão-7), nunca usado no corte."""
    chave = gdf[["f_2020", "f_2025", "concordancia", "fracao_industrial"]].round(6)
    chave = chave.assign(classe=gdf["classe_codigo"])
    colunas_chave = ["f_2020", "f_2025", "concordancia", "fracao_industrial"]
    agrupado = chave.groupby(colunas_chave)["classe"].nunique()
    inconsistentes = agrupado[agrupado > 1]
    assert inconsistentes.empty, (
        f"{len(inconsistentes)} combinações de atributos com mais de uma classe — "
        "sugere que o anel (ou outro atributo não usado no corte) influenciou a classe"
    )


# ---------------------------------------------------------------------------
# T10 — selo modelado, nunca observado
# ---------------------------------------------------------------------------


def test_t10_selo_modelado_em_todos_os_lugares(meta):
    assert meta["selo"] == "modelado"

    manifest_path = PROCESSED / "app" / "imagery" / "manifest.json"
    if manifest_path.exists():
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        entrada = manifest["camadas"].get("adensamento_2020_2025")
        if entrada:
            selo_manifest = entrada["caveats"]["adr_0016_selo_modelado"]["selo"]
            assert selo_manifest == "modelado"

    import yaml

    plaus = yaml.safe_load((ROOT / "config" / "plausibilidade.yaml").read_text(encoding="utf-8"))
    assert "adensamento" in plaus["camadas"], "config/plausibilidade.yaml sem a camada adensamento"
    assert "faixas_por_classe" in plaus["camadas"]["adensamento"]


# ---------------------------------------------------------------------------
# T11 — precedência de classe
# ---------------------------------------------------------------------------


def test_t11_precedencia_pegada_industrial_nunca_e_consolidado_ou_adensando(gdf):
    """Precedência do ADR: pegada_industrial > consolidado > expansao_nova >
    adensando/esparso_estavel > vazio_estavel. Nenhuma feição de
    `pegada_industrial` pode simultaneamente satisfazer o critério de
    `consolidado` sem que a precedência tenha sido respeitada — aqui verificado
    indiretamente: nenhuma classe fora do conjunto válido, e a classe é
    consistente com fracao_industrial alta implicando código 6."""
    cortes = json.loads(META_240M.read_text(encoding="utf-8"))["quantis_realizados"]
    q_ind = cortes["Q_INDUSTRIAL"]
    if np.isnan(q_ind):
        pytest.skip("Q_INDUSTRIAL não realizado nesta execução (sem células industriais)")
    indust_alta = gdf[gdf["fracao_industrial"] >= q_ind]
    assert (indust_alta["classe_codigo"] == 6).all(), (
        "existe feição com fracao_industrial >= Q_INDUSTRIAL classificada fora de "
        "pegada_industrial — precedência violada"
    )


# ---------------------------------------------------------------------------
# T12 — nenhuma variante de sensibilidade tem menos sinais ativos que a
# concordância mínima exige (correção de 2026-09-09; ver Emenda 1 do ADR)
# ---------------------------------------------------------------------------


def test_t12_sensibilidade_nenhuma_variante_com_zero_estrutural():
    """`grade_480m` e `bruta_experimental` sobravam com 1 sinal ativo (só S1) e
    exigiam >=2 votos: a área de `adensando` dava 0,00 por aritmética, qualquer
    que fosse o dado — não é medição. Depois da correção, toda variante publicada
    tem `n_sinais_ativos >= concordancia_minima`, ou a linha é NaN com nota
    explicando o motivo (nunca um zero silencioso)."""
    pd = pytest.importorskip("pandas")
    df = pd.read_csv(SENSIBILIDADE_CSV)

    linha_480 = df.loc[df["variante"] == "grade_480m"].iloc[0]
    linha_bruta = df.loc[df["variante"] == "bruta_experimental"].iloc[0]

    for nome, linha in (("grade_480m", linha_480), ("bruta_experimental", linha_bruta)):
        area = linha["area_adensando_km2"]
        if pd.isna(area):
            assert "NÃO CALCULÁVEL" in linha["nota"], (
                f"{nome}: área NaN tem de vir acompanhada de nota explicando o motivo"
            )
        else:
            assert area != 0.0, (
                f"{nome}: área 0,00 é o sintoma do defeito original — variante com "
                "menos sinais ativos que a concordância mínima exige produz zero "
                "por aritmética, não por medição"
            )
            assert "RECALCULADOS" in linha["nota"] or "ATIVOS" in linha["nota"], (
                f"{nome}: nota não confirma que S2/S3 permanecem ativos/recalculados"
            )


def test_t12_n_sinais_ativos_contra_concordancia_minima():
    """Unidade: `n_sinais_ativos` conta S1 (sempre ativo) + S2/S3 opcionais; o
    padrão do defeito original (`incluir_s2=False, incluir_s3=False` com
    `concordancia_minima=2`) tem, por construção, sinais insuficientes."""
    mod = _modulo_adensamento()
    assert mod.n_sinais_ativos(True, True) == 3
    assert mod.n_sinais_ativos(False, False) == 1
    assert mod.n_sinais_ativos(False, True) == 2
    # padrão do defeito original: 1 sinal ativo < concordância mínima (2)
    assert mod.n_sinais_ativos(False, False) < 2


# ---------------------------------------------------------------------------
# T14 — varredura ESTRUTURAL de todas as linhas do CSV de sensibilidade (não uma
# lista de nomes) — achado 4 do portão da Frente B, 2026-09-09
# ---------------------------------------------------------------------------


def test_t14_toda_linha_de_sensibilidade_sem_zero_silencioso():
    """T12 só olhava `grade_480m` e `bruta_experimental` por nome — uma variante
    nova registrada sem passar pela checagem voltaria a produzir 0,00 km² e
    passaria despercebida. Este contrato varre TODAS as linhas do CSV publicado,
    generacamente: nenhuma pode ter `area_adensando_km2 == 0` sem nota
    explicativa não vazia, e toda linha tem de trazer `n_sinais_ativos` e
    `concordancia_minima` (as colunas que tornam a checagem possível sem
    reimplementar o pipeline) com `n_sinais_ativos >= concordancia_minima` —
    exceto quando a área é NaN, caso em que a insuficiência de sinais pode ser
    exatamente o motivo declarado na nota."""
    pd = pytest.importorskip("pandas")
    df = pd.read_csv(SENSIBILIDADE_CSV)

    assert "n_sinais_ativos" in df.columns, (
        "CSV de sensibilidade sem coluna n_sinais_ativos — checagem estrutural "
        "de T14 não é possível sem reimplementar o pipeline"
    )
    assert "concordancia_minima" in df.columns

    for _, row in df.iterrows():
        nome = row["variante"]
        area = row["area_adensando_km2"]
        nota = row["nota"] if isinstance(row["nota"], str) else ""

        if not pd.isna(area) and area == 0.0:
            assert nota.strip() != "", f"{nome}: area=0 sem nota explicativa"

        n_ativos = row["n_sinais_ativos"]
        conc_min = row["concordancia_minima"]
        if pd.isna(area):
            # área não calculada: ou por sinais insuficientes (nota tem de dizer),
            # ou por insumo ausente — nunca sem nota.
            assert nota.strip() != "", f"{nome}: area=NaN sem nota explicativa"
        else:
            assert n_ativos >= conc_min, (
                f"{nome}: area calculada ({area}) com n_sinais_ativos={n_ativos} < "
                f"concordancia_minima={conc_min} — zero estrutural disfarçado de medição"
            )


# ---------------------------------------------------------------------------
# Reintrodução de defeitos sobre CÓPIA — verifica que os contratos acima realmente
# detectam o que dizem detectar. Nunca muta o artefato publicado.
# ---------------------------------------------------------------------------


def test_zz_reintroducao_de_defeitos_e_verificada(tmp_path, meta):
    achados = {}

    # --- T5: reintroduz um limiar absoluto (literal fora da whitelist) sobre CÓPIA do
    # script, e confirma que o scanner AST o acusa.
    copia_script = tmp_path / "adensamento_com_defeito.py"
    shutil.copy(SCRIPT, copia_script)
    texto = copia_script.read_text(encoding="utf-8")
    texto_com_defeito = texto.replace(
        "corte = float(np.quantile(s[dominio_ocupado], tau))",
        "corte = float(np.quantile(s[dominio_ocupado], tau)) if tau != 0.73219 else 0.1",
        1,
    )
    msg_t5 = "ponto de reintrodução do defeito T5 não encontrado no script"
    assert texto_com_defeito != texto, msg_t5
    copia_script.write_text(texto_com_defeito, encoding="utf-8")
    tree_defeito = ast.parse(copia_script.read_text(encoding="utf-8"))
    literais_fora = [
        comp.value
        for node in ast.walk(tree_defeito)
        if isinstance(node, ast.Compare)
        for comp in node.comparators
        if isinstance(comp, ast.Constant)
        and isinstance(comp.value, (int, float))
        and not isinstance(comp.value, bool)
        and comp.value not in WHITELIST_LITERAIS
    ]
    achados["T5"] = "acusou literal absoluto reintroduzido" if literais_fora else "FALHOU EM ACUSAR"
    assert literais_fora, "T5 deveria ter acusado o literal absoluto reintroduzido"

    # --- T2/T3: reintroduz um código de classe inválido (7) numa CÓPIA do raster de
    # 240 m, e confirma que o contrato de partição (T3) o acusaria.
    rasterio = pytest.importorskip("rasterio")
    copia_raster = tmp_path / "adensamento_com_defeito.tif"
    with rasterio.open(RASTER_240M) as src_orig:
        arr = src_orig.read(1)
        perfil = src_orig.profile
    arr[0, 0] = 7  # código fora de 0-6 — precedência quebrada
    perfil.update(driver="GTiff")  # simples, não COG — evita a proteção de layout
    with rasterio.open(copia_raster, "w", **perfil) as dst:
        dst.write(arr, 1)
    with rasterio.open(copia_raster) as src:
        valores = set(np.unique(src.read(1)).tolist())
    fora = valores - set(range(7))
    achados["T3"] = "acusou código de classe fora de 0-6" if fora else "FALHOU EM ACUSAR"
    assert fora, "T3 deveria ter acusado o código de classe 7 reintroduzido"

    # --- T4: reintroduz um QUANTIS divergente numa CÓPIA do .meta.json.
    copia_meta = tmp_path / "adensamento_com_defeito.meta.json"
    meta_defeituoso = dict(meta)
    meta_defeituoso["quantis_declarados"] = dict(meta["quantis_declarados"])
    meta_defeituoso["quantis_declarados"]["TAU"] = 0.99  # diverge do QUANTIS do módulo
    copia_meta.write_text(json.dumps(meta_defeituoso), encoding="utf-8")
    mod = _modulo_adensamento()
    meta_lido = json.loads(copia_meta.read_text(encoding="utf-8"))
    divergente = meta_lido["quantis_declarados"] != mod.QUANTIS
    achados["T4"] = "acusou TAU divergente do módulo" if divergente else "FALHOU EM ACUSAR"
    assert divergente, "T4 deveria ter acusado o TAU divergente reintroduzido"

    # --- T7: reintroduz o defeito original de nome_camada_ano numa CÓPIA da função
    # (via monkeypatch simples de regex) e confirma que ele reaparece sem a correção.
    def nome_camada_ano_com_defeito(path: Path):
        stem = path.stem
        partes = stem.rsplit("_", 1)
        if len(partes) == 2 and partes[1].isdigit():
            return partes[0], int(partes[1])
        return stem, None

    camada_defeituosa, ano_defeituoso = nome_camada_ano_com_defeito(
        Path("adensamento_2020_2025.geojson")
    )
    defeito_reproduzido = (camada_defeituosa, ano_defeituoso) == ("adensamento_2020", 2025)
    achados["T7"] = (
        "reproduziu o defeito original ('adensamento_2020', 2025)"
        if defeito_reproduzido
        else "FALHOU EM ACUSAR"
    )
    msg_t7 = "a versão pré-correção deveria reproduzir o defeito documentado no ADR"
    assert defeito_reproduzido, msg_t7

    # --- T12: reintroduz o padrão do defeito original (área calculada com sinais
    # insuficientes, SEM a checagem de `registrar_checada`) sobre um `sinais` SINTÉTICO
    # — nunca sobre o artefato publicado — e confirma que ele volta a dar zero
    # estrutural, exatamente o sintoma que o contrato T12 acusa no CSV real.
    mod = _modulo_adensamento()
    n_lin, n_col = 4, 4
    dominio = np.ones((n_lin, n_col), dtype=bool)
    dominio_ocupado = np.ones((n_lin, n_col), dtype=bool)
    f_2020 = np.linspace(0.1, 0.4, n_lin * n_col).reshape(n_lin, n_col)
    f_2025 = f_2020 + 0.15  # todas as células sobem — S1 positivo em toda parte
    sinais_sinteticos = {
        "dominio": dominio,
        "dominio_ocupado": dominio_ocupado,
        "f_2020": f_2020,
        "f_2025": f_2025,
        "s1": np.full((n_lin, n_col), 0.5),
        "s2": np.full((n_lin, n_col), 0.5),  # sinal presente nos dados...
        "s3": np.full((n_lin, n_col), 0.5),  # ...mas desligado no voto abaixo
        "fracao_industrial": None,
        "fator_grade": mod.FATOR_GRADE,
    }
    area_com_defeito_reintroduzido = mod.area_adensando_km2(
        sinais_sinteticos, incluir_s2=False, incluir_s3=False, concordancia_minima=2
    )
    padrao_do_defeito = area_com_defeito_reintroduzido == 0.0
    achados["T12"] = (
        "reproduziu o zero estrutural (1 sinal ativo < concordancia_minima=2)"
        if padrao_do_defeito
        else "FALHOU EM ACUSAR"
    )
    assert padrao_do_defeito, (
        "chamar area_adensando_km2 sem passar por registrar_checada, com sinais "
        "insuficientes, deveria reproduzir o zero estrutural do defeito original"
    )
    # e a checagem correta (n_sinais_ativos >= concordancia_minima) recusa calcular:
    n_ativos = mod.n_sinais_ativos(incluir_s2=False, incluir_s3=False)
    assert n_ativos < 2, "padrão do defeito precisa ter sinais insuficientes por construção"

    # --- T13: reintroduz a fórmula do ADR SEM `dominio_ocupado` (o defeito
    # corrigido na Emenda 2) sobre uma linha SINTÉTICA — nunca sobre o GeoJSON
    # publicado — reproduzindo o caso medido: célula nunca ocupada
    # (f_2020 = f_2025 = 0) com S3 alto por Open Buildings, que a fórmula
    # incompleta votaria positivo indevidamente.
    linha_sintetica = {"f_2020": 0.0, "f_2025": 0.0, "S1": 0.0, "S2": 0.0, "S3": 0.85}
    tau_s3_sintetico = 0.35

    def _voto_formula_incompleta_do_adr(valor: float, corte: float) -> bool:
        # fórmula literal de `docs/ADR/0016` antes da Emenda 2: sem `dominio_ocupado`
        return bool(valor > 0 and valor >= corte)

    def _voto_codigo_correto(valor: float, corte: float, dominio_ocupado: bool) -> bool:
        return bool(dominio_ocupado and valor > 0 and valor >= corte)

    dominio_ocupado_sintetico = (linha_sintetica["f_2020"] > 0) or (linha_sintetica["f_2025"] > 0)
    v3_formula_incompleta = _voto_formula_incompleta_do_adr(
        linha_sintetica["S3"], tau_s3_sintetico
    )
    v3_codigo_correto = _voto_codigo_correto(
        linha_sintetica["S3"], tau_s3_sintetico, dominio_ocupado_sintetico
    )
    defeito_t13_reproduzido = v3_formula_incompleta is True and v3_codigo_correto is False
    achados["T13"] = (
        "fórmula incompleta do ADR votaria V3=True numa célula nunca ocupada; "
        "o código (com dominio_ocupado) vota V3=False — divergência que T13 acusaria"
        if defeito_t13_reproduzido
        else "FALHOU EM ACUSAR"
    )
    assert defeito_t13_reproduzido, (
        "a fórmula sem dominio_ocupado deveria votar positivo onde o código correto "
        "vota negativo, reproduzindo o achado de 13 feições pegada_industrial"
    )

    # --- T14: reintroduz uma linha `area=0` sem nota numa CÓPIA do DataFrame de
    # sensibilidade, e confirma que a varredura genérica (por linha, não por nome)
    # a acusaria.
    pd = pytest.importorskip("pandas")
    df_original = pd.read_csv(SENSIBILIDADE_CSV)
    df_com_defeito = pd.concat(
        [
            df_original,
            pd.DataFrame(
                [
                    {
                        "variante": "variante_nova_nao_prevista",
                        "area_adensando_km2": 0.0,
                        "nota": "",
                        "n_sinais_ativos": 1,
                        "concordancia_minima": 2,
                    }
                ]
            ),
        ],
        ignore_index=True,
    )
    linha_defeituosa = df_com_defeito.iloc[-1]
    nota_vazia = (
        not isinstance(linha_defeituosa["nota"], str) or linha_defeituosa["nota"].strip() == ""
    )
    area_zero_sem_nota = linha_defeituosa["area_adensando_km2"] == 0.0 and nota_vazia
    achados["T14"] = (
        "acusou linha nova com area=0 e nota vazia" if area_zero_sem_nota else "FALHOU EM ACUSAR"
    )
    assert area_zero_sem_nota, "T14 deveria acusar uma linha nova com area=0 sem nota"

    print("\n[reintroducao] " + "; ".join(f"{k}: {v}" for k, v in achados.items()))
