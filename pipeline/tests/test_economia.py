"""Contratos sobre data/processed/economia/.

Organização: um bloco por artefato, cada teste com o prefixo do artefato
(`test_contas_ine_*` para contas_regionais_tete.csv). Outros agentes acrescentam
blocos novos com prefixo próprio; não reutilize os helpers de outro bloco.

Bloco `test_contas_ine_*` — contas_regionais_tete.csv, gerado por
pipeline/00_fetch/extrair_ine_folheto_tete.py a partir do Folheto Provincial de
Tete 2021 (INE), nível C (§4.0: contexto, não núcleo). §11.2: o CSV tem de ser
regenerável por script; o teste de regeneração compara byte a byte e pula
(`pytest.skip`) quando o PDF bruto não está no cache local — `data/raw/*.pdf` não é
versionado, só os sidecars `.sha256` e `.meta.json`.
"""
from __future__ import annotations

import csv
import importlib.util
import sys
from pathlib import Path

import pandas as pd
import pytest

ROOT = Path(__file__).resolve().parents[2]
ECONOMIA = ROOT / "data" / "processed" / "economia"

# ---------------------------------------------------------------------------
# contas_regionais_tete.csv (INE, Folheto Provincial Tete 2021) — nível C
# ---------------------------------------------------------------------------

CONTAS_CSV = ECONOMIA / "contas_regionais_tete.csv"
CONTAS_SCRIPT = ROOT / "pipeline" / "00_fetch" / "extrair_ine_folheto_tete.py"
CONTAS_PDF = ROOT / "data" / "raw" / "ine_contas_folheto_provincial_tete_2021.pdf"
CONTAS_COLUNAS = [
    "unidade_geografica",
    "ano",
    "variavel",
    "valor",
    "unidade_medida",
    "selo",
    "nivel_fonte",
    "fonte",
    "metodo",
    "nota",
]


def _contas_modulo():
    spec = importlib.util.spec_from_file_location("extrair_ine_folheto_tete", CONTAS_SCRIPT)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _contas_linhas() -> list[dict[str, str]]:
    if not CONTAS_CSV.exists():
        pytest.skip(f"{CONTAS_CSV} ausente")
    with open(CONTAS_CSV, encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


def test_contas_ine_colunas_exatas():
    if not CONTAS_CSV.exists():
        pytest.skip(f"{CONTAS_CSV} ausente")
    with open(CONTAS_CSV, encoding="utf-8", newline="") as f:
        cabecalho = next(csv.reader(f))
    assert cabecalho == CONTAS_COLUNAS


def test_contas_ine_nove_linhas():
    assert len(_contas_linhas()) == 9


def test_contas_ine_nivel_c_em_todas_as_linhas():
    linhas = _contas_linhas()
    assert all(r["nivel_fonte"] == "C" for r in linhas), "§4.0: folheto sem licença localizada ⇒ C"


def test_contas_ine_nota_declara_contexto():
    for r in _contas_linhas():
        assert r["nota"].startswith("contexto, não núcleo (§4.0): "), r["variavel"]


def test_contas_ine_metodo_aponta_para_o_script():
    for r in _contas_linhas():
        assert "pipeline/00_fetch/extrair_ine_folheto_tete.py" in r["metodo"], r["variavel"]


def test_contas_ine_extracao_falha_em_texto_incompleto():
    """Sem o quadro completo o extrator falha; nunca devolve valor parcial."""
    mod = _contas_modulo()
    texto = (
        "Fonte: INE, Direcção de Contas Nacionais, Indicadores Globais \n"
        "PIB e Inflação Provincia Nacional\n"
        "Taxa de Crescimento do PIB (%) - 2020 -2,1 -1,2\n"
        "PIB per capita em US$ (2020) 411 518\n"
    )
    with pytest.raises(mod.ExtracaoFalhou):
        mod.extrair_quadro(texto)


def test_contas_ine_extracao_falha_em_campo_duplicado():
    mod = _contas_modulo()
    texto = (
        "Fonte: INE, Direcção de Contas Nacionais, Indicadores Globais \n"
        "PIB e Inflação Provincia Nacional\n"
        "Taxa de Crescimento do PIB (%) - 2020 -2,1 -1,2\n"
        "Taxa de Crescimento do PIB (%) - 2020 -3,0 -1,2\n"
        "PIB per capita em US$ (2020) 411 518\n"
        "PIB em % do PIB Nacional (2020) 7,6 100,0\n"
        "Inflação média (%)- 2021 7,47 5,69\n"
        "Inflação acumulada (%) - 2021 6,85 6,74\n"
    )
    with pytest.raises(mod.ExtracaoFalhou):
        mod.extrair_quadro(texto)


def test_contas_ine_regeneracao_byte_a_byte(tmp_path):
    """§11.2: regenerar do PDF bruto reproduz o CSV publicado byte a byte."""
    if not CONTAS_PDF.exists():
        pytest.skip(f"{CONTAS_PDF.name} não está no cache local (data/raw/*.pdf não é versionado)")
    if not CONTAS_CSV.exists():
        pytest.skip(f"{CONTAS_CSV} ausente")
    mod = _contas_modulo()
    saida = mod.main(saida=tmp_path / "contas_regionais_tete.csv", pdf=CONTAS_PDF)
    assert saida.read_bytes() == CONTAS_CSV.read_bytes()


# ---------------------------------------------------------------------------
# preco_carvao_anual.csv (World Bank CMO) e producao_moatize_anual.csv
# (SEC EDGAR: Vale 20-F, Rio Tinto 6-K) — prefixos test_preco_ / test_producao_
# ---------------------------------------------------------------------------

PRECO_CSV = ECONOMIA / "preco_carvao_anual.csv"
PRODUCAO_CSV = ECONOMIA / "producao_moatize_anual.csv"
FETCH_VALE_SCRIPT = ROOT / "pipeline" / "00_fetch" / "fetch_vale_20f.py"

ECONOMIA_COLUNAS = [
    "unidade_geografica",
    "ano",
    "variavel",
    "valor",
    "unidade_medida",
    "selo",
    "nivel_fonte",
    "fonte",
    "metodo",
    "nota",
]


def _fetch_vale_modulo():
    spec = importlib.util.spec_from_file_location("fetch_vale_20f", FETCH_VALE_SCRIPT)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = mod  # dataclasses precisa do módulo em sys.modules
    spec.loader.exec_module(mod)
    return mod


def _csv_linhas(caminho: Path) -> list[dict[str, str]]:
    if not caminho.exists():
        pytest.skip(f"{caminho} ausente")
    with open(caminho, encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


def test_preco_colunas_exatas():
    if not PRECO_CSV.exists():
        pytest.skip(f"{PRECO_CSV} ausente")
    with open(PRECO_CSV, encoding="utf-8", newline="") as f:
        cabecalho = next(csv.reader(f))
    assert cabecalho == ECONOMIA_COLUNAS


def test_preco_valores_em_faixa_plausivel():
    """Preço de carvão (USD/t nominal) plausível: nem negativo, nem absurdo."""
    linhas = _csv_linhas(PRECO_CSV)
    for r in linhas:
        try:
            valor = float(r["valor"])
        except ValueError:
            continue  # "não disponível" — fora do escopo deste teste
        assert 0 < valor < 1000, (r["ano"], r["variavel"], valor)


def test_preco_nivel_a():
    linhas = _csv_linhas(PRECO_CSV)
    assert all(r["nivel_fonte"] == "A" for r in linhas)


def test_producao_colunas_exatas():
    if not PRODUCAO_CSV.exists():
        pytest.skip(f"{PRODUCAO_CSV} ausente")
    with open(PRODUCAO_CSV, encoding="utf-8", newline="") as f:
        cabecalho = next(csv.reader(f))
    assert cabecalho == ECONOMIA_COLUNAS


def test_producao_valores_em_faixa_plausivel_quando_presentes():
    """Produção anual de Moatize declarada (Mt/ano) plausível: a capacidade
    nominal histórica de Moatize é da ordem de 11-22 Mtpy (20-F da Vale);
    nenhum valor extraído deveria exceder uma margem generosa disso."""
    linhas = _csv_linhas(PRODUCAO_CSV)
    for r in linhas:
        try:
            valor = float(r["valor"])
        except ValueError:
            continue  # "não disponível"
        assert 0 <= valor < 30, (r["unidade_geografica"], r["ano"], r["variavel"], valor)


def test_producao_sem_valor_inventado_quando_raw_ausente():
    """Sem 20-F/6-K em data/raw/, todas as linhas de produção têm de ser
    'não disponível' — nunca um número, mesmo que plausível."""
    linhas = _csv_linhas(PRODUCAO_CSV)
    tem_vale = any(ROOT.glob("data/raw/vale_20f_*.htm"))
    tem_rt = any(ROOT.glob("data/raw/riotinto_6k_*.htm"))
    if tem_vale or tem_rt:
        pytest.skip("brutos presentes nesta máquina — teste de ausência não se aplica")
    assert all(r["valor"] == "não disponível" for r in linhas)


def test_producao_metodo_aponta_para_o_script():
    for r in _csv_linhas(PRODUCAO_CSV):
        assert "fetch_vale_20f.py" in r["metodo"], r["variavel"]


def test_producao_extrator_vale_falha_sem_tabela_de_producao(tmp_path):
    """Sem a tabela 'Metallurgical coal:'/'(thousand metric tons)', a
    extração tem de falhar explicitamente, nunca inventar um alinhamento."""
    mod = _fetch_vale_modulo()
    html = tmp_path / "sem_tabela.htm"
    html.write_text(
        "<html><body><table><tr><td>Moatize</td><td>Some other content, "
        "no production figures here.</td></tr></table></body></html>",
        encoding="utf-8",
    )
    with pytest.raises(mod.ExtracaoFalhou):
        mod.extrair_producao_moatize_vale(html, "2099", "TESTACC", "https://example.invalid")


def test_producao_extrator_vale_le_tabela_sintetica_pares_de_coluna(tmp_path):
    """Fixture sintética mínima reproduzindo a diagramação em PARES de coluna
    por ano observada nos 20-F mais antigos da Vale (ex.: FY2012), com
    valores e anos FICTÍCIOS (não copiados de nenhum filing real)."""
    mod = _fetch_vale_modulo()
    html = tmp_path / "sintetico_pares.htm"
    html.write_text(
        """
        <html><body>
        <table>
          <tr><td></td><td></td><td>Production for the year ended December 31,</td>
              <td>Production for the year ended December 31,</td>
              <td>Production for the year ended December 31,</td></tr>
          <tr><td>Operation</td><td>Mine type</td>
              <td>2030</td><td>2030</td>
              <td>2031</td><td>2031</td>
              <td>2032</td><td>2032</td></tr>
          <tr><td></td><td></td>
              <td>(thousand metric tons)</td><td>(thousand metric tons)</td>
              <td>(thousand metric tons)</td><td>(thousand metric tons)</td>
              <td>(thousand metric tons)</td><td>(thousand metric tons)</td></tr>
          <tr><td>Metallurgical coal:</td><td></td>
              <td></td><td></td><td></td><td></td><td></td><td></td></tr>
          <tr><td>Outra Mina</td><td>Open-cut</td>
              <td></td><td>500</td><td></td><td>600</td><td></td><td>700</td></tr>
          <tr><td>Moatize(9)</td><td>Open-cut</td>
              <td></td><td>&#8211;</td><td></td><td>111</td><td></td><td>222</td></tr>
          <tr><td>Thermal coal:</td><td></td>
              <td></td><td></td><td></td><td></td><td></td><td></td></tr>
          <tr><td>Moatize(9)</td><td>Open-cut</td>
              <td></td><td>&#8211;</td><td></td><td>33</td><td></td><td>44</td></tr>
        </table>
        </body></html>
        """,
        encoding="utf-8",
    )
    resultados = mod.extrair_producao_moatize_vale(html, "2032", "TESTACC", "https://example.invalid")
    por_ano_var = {(r["ano"], r["variavel"]): r["valor_mt"] for r in resultados}
    assert por_ano_var[(2030, "producao_carvao_metalurgico")] is None
    assert por_ano_var[(2031, "producao_carvao_metalurgico")] == 0.111
    assert por_ano_var[(2032, "producao_carvao_metalurgico")] == 0.222
    assert por_ano_var[(2031, "producao_carvao_termico")] == 0.033
    assert por_ano_var[(2032, "producao_carvao_termico")] == 0.044


def test_producao_extrator_vale_le_tabela_sintetica_nbsp_na_unidade(tmp_path):
    """Fixture sintética com non-breaking space (U+00A0) dentro de
    '(thousand metric tons)', variação observada em pelo menos um exercício
    da Vale (a extração não pode depender de espaço ASCII literal). O
    documento declara charset utf-8 explicitamente, como os 20-F reais."""
    mod = _fetch_vale_modulo()
    html = tmp_path / "sintetico_nbsp.htm"
    nbsp = "\u00a0"
    conteudo = (
        '<html><head><meta charset="utf-8"></head><body><table>'
        "<tr><td>Operation</td><td>Mine type</td>"
        "<td>2040</td><td>2041</td></tr>"
        "<tr><td></td><td></td>"
        f"<td>(thousand{nbsp}metric{nbsp}tons)</td>"
        f"<td>(thousand{nbsp}metric{nbsp}tons)</td></tr>"
        "<tr><td>Metallurgical coal:</td><td></td><td></td><td></td></tr>"
        "<tr><td>Moatize(2)</td><td>Open-cut</td><td>999</td><td>888</td></tr>"
        "</table></body></html>"
    )
    html.write_text(conteudo, encoding="utf-8")
    resultados = mod.extrair_producao_moatize_vale(html, "2041", "TESTACC", "https://example.invalid")
    por_ano_var = {(r["ano"], r["variavel"]): r["valor_mt"] for r in resultados}
    assert por_ano_var[(2040, "producao_carvao_metalurgico")] == 0.999
    assert por_ano_var[(2041, "producao_carvao_metalurgico")] == 0.888


def test_producao_extrator_vale_marca_ambiguidade_sem_abortar_arquivo(tmp_path):
    """Reproduz (com rótulos e valores FICTÍCIOS) o layout real encontrado no
    20-F referente ao exercício de 2018 (arquivo vale_20f_2019_*): o próprio
    CABEÇALHO do documento rotula duas colunas distintas com o MESMO ano
    ('2050' duas vezes), cada uma com um valor numérico diferente para a
    linha 'Moatize'. Extração não pode adivinhar qual coluna é a certa — mas
    também não pode, por causa de UM ano ambíguo, descartar os demais anos
    (não ambíguos) da mesma linha/tabela. Contrato: o ano ambíguo volta como
    item com `valor_mt=None` e `ambiguo=True`, preservando os candidatos
    brutos; o ano não ambíguo é extraído normalmente."""
    mod = _fetch_vale_modulo()
    html = tmp_path / "sintetico_ambiguo.htm"
    html.write_text(
        """
        <html><body><table>
          <tr><td>Operation</td><td>Mine type</td>
              <td>2049</td><td>2050</td><td>2050</td></tr>
          <tr><td></td><td></td>
              <td>(thousand metric tons)</td><td>(thousand metric tons)</td>
              <td>(thousand metric tons)</td></tr>
          <tr><td>Metallurgical coal:</td><td></td><td></td><td></td><td></td></tr>
          <tr><td>Moatize(3)</td><td>Open-cut</td><td>77</td><td>123</td><td>456</td></tr>
        </table></body></html>
        """,
        encoding="utf-8",
    )
    resultados = mod.extrair_producao_moatize_vale(
        html, "2050", "TESTACC", "https://example.invalid"
    )
    por_ano = {r["ano"]: r for r in resultados}
    assert por_ano[2049]["valor_mt"] == 0.077
    assert por_ano[2049].get("ambiguo") is not True
    entrada_ambigua = por_ano[2050]
    assert entrada_ambigua.get("ambiguo") is True
    assert entrada_ambigua["valor_mt"] is None
    assert "123" in entrada_ambigua["nota_ambiguidade"]
    assert "456" in entrada_ambigua["nota_ambiguidade"]


def test_producao_merge_preserva_valor_bom_e_anota_ambiguidade_de_filing_posterior(
    tmp_path, monkeypatch
):
    """Reproduz o caso real: um filing MAIS ANTIGO já resolveu um ano sem
    ambiguidade; um filing MAIS RECENTE, para o MESMO ano, tem o defeito de
    cabeçalho (duas colunas com o mesmo rótulo de ano). O valor bom do
    filing antigo não pode ser substituído por 'não disponível' só porque um
    filing posterior tropeçou no próprio cabeçalho — mas a ambiguidade
    encontrada tem de ficar registrada na nota, e sobreviver mesmo que um
    TERCEIRO filing, ainda mais recente e não ambíguo, também repita o
    mesmo ano com o mesmo valor (dedup normal não pode apagar a nota)."""
    mod = _fetch_vale_modulo()

    def tabela_limpa(ano_a, ano_b, valor_a, valor_b):
        return f"""
        <html><body><table>
          <tr><td>Operation</td><td>Mine type</td><td>{ano_a}</td><td>{ano_b}</td></tr>
          <tr><td></td><td></td>
              <td>(thousand metric tons)</td><td>(thousand metric tons)</td></tr>
          <tr><td>Metallurgical coal:</td><td></td><td></td><td></td></tr>
          <tr><td>Moatize(1)</td><td>Open-cut</td><td>{valor_a}</td><td>{valor_b}</td></tr>
        </table></body></html>
        """

    raw = tmp_path / "raw"
    processed = tmp_path / "processed" / "economia"
    raw.mkdir(parents=True)
    processed.mkdir(parents=True)

    # Filing antigo (2060): resolve 2059 sem ambiguidade.
    (raw / "vale_20f_2060_fixtureA.htm").write_text(
        tabela_limpa(2058, 2059, 10, 20), encoding="utf-8"
    )
    # Filing seguinte (2061): repete 2059 com cabeçalho ambíguo (duas
    # colunas '2059' com valores conflitantes).
    (raw / "vale_20f_2061_fixtureB.htm").write_text(
        """
        <html><body><table>
          <tr><td>Operation</td><td>Mine type</td><td>2058</td><td>2059</td><td>2059</td></tr>
          <tr><td></td><td></td>
              <td>(thousand metric tons)</td><td>(thousand metric tons)</td>
              <td>(thousand metric tons)</td></tr>
          <tr><td>Metallurgical coal:</td><td></td><td></td><td></td><td></td></tr>
          <tr><td>Moatize(1)</td><td>Open-cut</td><td>10</td><td>20</td><td>999</td></tr>
        </table></body></html>
        """,
        encoding="utf-8",
    )
    # Filing mais recente ainda (2062): repete 2059/2060, sem ambiguidade,
    # mesmo valor de 2059 já visto (20) — não pode apagar a nota anterior.
    (raw / "vale_20f_2062_fixtureC.htm").write_text(
        tabela_limpa(2059, 2060, 20, 30), encoding="utf-8"
    )

    monkeypatch.setattr(mod, "DATA_RAW", raw)
    monkeypatch.setattr(mod, "DATA_PROCESSED", processed)
    monkeypatch.setattr(mod, "CSV_SAIDA", processed / "producao_moatize_anual.csv")

    df = mod.gerar_csv_a_partir_de_raw()
    linha_2059 = df[
        (df["ano"] == 2059) & (df["variavel"] == "producao_carvao_metalurgico")
    ].iloc[0]
    assert linha_2059["valor"] == 0.02
    assert "vale_20f_2061_fixtureB.htm" in linha_2059["nota"]
    assert "999" in linha_2059["nota"]


def test_producao_flavor_html_e_deterministico_e_registrado(tmp_path, monkeypatch):
    """§(3) da tarefa: o flavor de pandas.read_html usado por arquivo é fixo
    (tenta lxml primeiro; só cai para bs4/html5lib se lxml levantar exceção
    de PARSE — não apenas 'nenhuma tabela casou') e fica registrado por
    arquivo em FLAVOR_USADO, para o provenance poder citar qual parser leu
    cada 20-F em vez de depender do fallback interno e não documentado do
    pandas."""
    mod = _fetch_vale_modulo()
    mod.FLAVOR_USADO.clear()
    chamadas = []

    def read_html_falso(path, match=None, flavor=None):
        chamadas.append(flavor)
        if flavor == "lxml":
            raise ValueError("lxml simulado: falha de parse")
        return [pd.DataFrame({"a": ["Moatize"], "b": ["ok"]})]

    monkeypatch.setattr(mod.pd, "read_html", read_html_falso)
    html = tmp_path / "arquivo_flavor.htm"
    html.write_text("<html><body>irrelevante</body></html>", encoding="utf-8")

    tabelas = mod._ler_tabelas_html(html, match="Moatize")
    assert len(tabelas) == 1
    assert chamadas == ["lxml", "bs4"]
    assert mod.FLAVOR_USADO[html.name].startswith("bs4/html5lib")


def test_producao_diagnostico_mina_ainda_nao_em_producao(tmp_path):
    """Reproduz (texto sintético, não copiado de nenhum filing) o padrão dos
    20-F de exercícios anteriores ao início da produção de Moatize: menção a
    capacidade nominal futura, sem tabela de produção real. O diagnóstico
    tem de vir do PRÓPRIO documento, não de suposição externa."""
    mod = _fetch_vale_modulo()
    html = tmp_path / "pre_producao.htm"
    html.write_text(
        "<html><body><table><tr><td>Moatize</td><td>placeholder</td></tr></table>"
        "<p>We have obtained all of the required licenses from the government "
        "of Mozambique for the construction of the Moatize mine, which will "
        "have nominal production capacity of 11 million metric tons per "
        "year.</p></body></html>",
        encoding="utf-8",
    )
    with pytest.raises(mod.ExtracaoFalhou, match="fase de licenciamento/construção"):
        mod.extrair_producao_moatize_vale(html, "2099", "TESTACC", "https://example.invalid")


def test_producao_diagnostico_ativo_vendido():
    """Reproduz (texto sintético) o padrão do 20-F FY2022: a Vale relata a
    venda das operações de carvão antes de qualquer tabela de produção de
    Moatize existir naquele exercício."""
    mod = _fetch_vale_modulo()
    texto = (
        "In April 2022, we concluded the sale of our coal operations, "
        "consisting of Moatize mine and the Nacala Logistics Corridor, to "
        "Vulcan Resources for US$270 million."
    )
    import tempfile

    with tempfile.NamedTemporaryFile("w", suffix=".htm", delete=False, encoding="utf-8") as f:
        f.write(f"<html><body><p>{texto}</p><p>Moatize</p></body></html>")
        caminho = Path(f.name)
    try:
        motivo = mod._diagnosticar_ausencia_tabela(caminho)
    finally:
        caminho.unlink()
    assert "venda das operações de carvão" in motivo


def test_producao_regeneracao_e_deterministica_com_brutos_reais():
    """Quando os brutos reais (20-F/6-K) estão em data/raw/, duas chamadas
    sucessivas de gerar_csv_a_partir_de_raw() produzem exatamente o mesmo
    DataFrame (byte a byte no CSV) — nenhuma etapa depende de ordem de
    iteração de conjunto/dicionário nem de estado de processo. Pula
    (`pytest.skip`) se os 20-F/6-K reais não estiverem no cache local desta
    máquina — eles não são versionados em data/raw/ além do que já estiver
    presente na execução (política §11.2)."""
    mod = _fetch_vale_modulo()
    if not any(ROOT.glob("data/raw/vale_20f_*.htm")):
        pytest.skip("20-F reais da Vale ausentes em data/raw/ nesta máquina")
    df1 = mod.gerar_csv_a_partir_de_raw()
    df2 = mod.gerar_csv_a_partir_de_raw()
    assert df1.to_csv(index=False) == df2.to_csv(index=False)


def test_producao_regeneracao_a_partir_de_raw_ausente_marca_aguarda_sec(tmp_path):
    """Sem nenhum vale_20f_*/riotinto_6k_* em data/raw/, o gerador tem de
    manter todas as linhas 'não disponível', com o motivo 'aguarda
    SEC_USER_AGENT' — nunca apagar o CSV nem inventar valor."""
    mod = _fetch_vale_modulo()
    raw_original = mod.DATA_RAW
    try:
        mod.DATA_RAW = tmp_path  # diretório vazio, sem nenhum filing
        df = mod.gerar_csv_a_partir_de_raw()
    finally:
        mod.DATA_RAW = raw_original
    assert (df["valor"] == "não disponível").all()
    assert df["nota"].str.contains("aguarda SEC_USER_AGENT").any()
    assert list(df.columns) == ECONOMIA_COLUNAS
