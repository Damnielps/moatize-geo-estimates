"""pipeline/tests/test_publicacao.py — contratos de identidade da publicação.

Dois identificadores persistem a publicação para além da URL do GitHub Pages: o **ORCID**
do autor, que já existe, e o **DOI** do Zenodo, que só existe depois da primeira release
arquivada. Os contratos aqui garantem (a) que o ORCID é o mesmo em todos os lugares que o
declaram — inclusive na tela, não só nos metadados legíveis por máquina — e (b) que o DOI
só aparece por inteiro ou não aparece: nunca em três dos quatro arquivos.

Contratos:
1. O ORCID é idêntico em CITATION.cff, .zenodo.json, README.md, o JSON-LD de index.html
   e publicacao.js — e tem a forma de um ORCID válido, com dígito verificador.
2. O bloco "Como citar" renderiza o ORCID (não basta estar no JSON-LD).
3. Enquanto não há DOI, a ausência é declarada de forma coerente nos quatro arquivos, e
   nenhum deles carrega um DOI de exemplo.
4. `scripts/definir_doi.py` escreve o DOI nos quatro arquivos, é idempotente, substitui
   (não acumula) quando reexecutado com outro DOI, e recusa um DOI malformado.
5. O script é transacional: se uma âncora sumir, nada é escrito.
"""

import importlib.util
import json
import re
import shutil
import sys
from pathlib import Path

import pytest

RAIZ = Path(__file__).parent.parent.parent
QUATRO_ARQUIVOS = (
    "app/src/lib/publicacao.js",
    "CITATION.cff",
    "README.md",
    "app/index.html",
)
ORCID_RE = re.compile(r"\b(\d{4}-\d{4}-\d{4}-\d{3}[\dX])\b")


def _carregar_script(raiz: Path):
    """Importa `definir_doi.py` apontado para `raiz` (uma cópia do repositório)."""
    nome = f"definir_doi_{abs(hash(str(raiz)))}"
    spec = importlib.util.spec_from_file_location(nome, raiz / "scripts" / "definir_doi.py")
    modulo = importlib.util.module_from_spec(spec)
    # O módulo precisa estar em sys.modules ANTES do exec: @dataclass resolve as
    # anotações adiadas (`from __future__ import annotations`) por sys.modules[__module__].
    sys.modules[nome] = modulo
    spec.loader.exec_module(modulo)
    modulo.RAIZ = raiz
    modulo.PUBLICACAO_JS = raiz / "app/src/lib/publicacao.js"
    modulo.CITATION = raiz / "CITATION.cff"
    modulo.README = raiz / "README.md"
    modulo.INDEX_HTML = raiz / "app/index.html"
    return modulo


@pytest.fixture
def copia(tmp_path):
    """Cópia dos arquivos que o script toca, para testar a escrita sem sujar o repo."""
    for rel in (
        "scripts/definir_doi.py",
        "app/src/lib/publicacao.js",
        "CITATION.cff",
        "README.md",
        "app/index.html",
    ):
        destino = tmp_path / rel
        destino.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(RAIZ / rel, destino)
    return tmp_path


def _orcid_de(rel: str) -> str:
    achados = ORCID_RE.findall((RAIZ / rel).read_text(encoding="utf-8"))
    assert achados, f"nenhum ORCID em {rel}"
    return achados[0]


def _digito_verificador_ok(orcid: str) -> bool:
    """ISO 7064 mod 11-2, como manda a especificação do ORCID."""
    digitos = orcid.replace("-", "")
    total = 0
    for ch in digitos[:-1]:
        total = (total + int(ch)) * 2
    resto = total % 11
    esperado = (12 - resto) % 11
    return ("X" if esperado == 10 else str(esperado)) == digitos[-1]


# --- Contrato 1: um só ORCID, em todo lugar -------------------------------------------


def test_orcid_identico_em_todos_os_arquivos():
    arquivos = [
        "CITATION.cff",
        ".zenodo.json",
        "README.md",
        "app/index.html",
        "app/src/lib/publicacao.js",
    ]
    valores = {rel: _orcid_de(rel) for rel in arquivos}
    assert len(set(valores.values())) == 1, f"ORCIDs divergentes: {valores}"


def test_orcid_tem_digito_verificador_valido():
    orcid = _orcid_de("CITATION.cff")
    assert _digito_verificador_ok(orcid), f"{orcid} falha no mod 11-2 do ORCID"


def test_zenodo_json_declara_o_orcid_no_criador():
    dados = json.loads((RAIZ / ".zenodo.json").read_text(encoding="utf-8"))
    criadores = dados["creators"]
    assert criadores, ".zenodo.json sem creators"
    assert all("orcid" in c for c in criadores), "criador sem ORCID no .zenodo.json"


# --- Contrato 2: o ORCID chega à tela -------------------------------------------------


def test_bloco_como_citar_renderiza_o_orcid():
    fonte = (RAIZ / "app/src/components/ComoCitar.jsx").read_text(encoding="utf-8")
    assert "AUTOR.orcid" in fonte, "ComoCitar.jsx não usa AUTOR.orcid"
    assert "orcid.org/" in fonte, "ComoCitar.jsx não liga o ORCID ao orcid.org"


def test_i18n_tem_rotulo_de_autor_nos_dois_idiomas():
    fonte = (RAIZ / "app/src/lib/i18n.jsx").read_text(encoding="utf-8")
    assert fonte.count("como_citar_autor:") == 2, "rótulo de autor não está em PT e EN"
    assert fonte.count("como_citar_sem_doi:") == 2, "nota de DOI ausente não está em PT e EN"


# --- Contrato 3: sem DOI, a ausência é coerente ---------------------------------------


def test_estado_do_doi_e_coerente_no_repositorio():
    modulo = _carregar_script(RAIZ)
    assert modulo.verificar() == 0


def test_nenhum_doi_de_exemplo_publicado():
    """Um `zenodo.XXXXXX` servido como identificador viraria um link morto no painel.

    Comentários são varridos antes da checagem: `index.html` documenta no comentário do
    JSON-LD o formato que o campo terá quando o DOI existir, e essa instrução não é
    servida como dado — o que não pode existir é o valor de exemplo fora do comentário.
    """
    sem_comentario = {
        "app/index.html": lambda t: re.sub(r"<!--.*?-->", "", t, flags=re.S),
        "app/src/lib/publicacao.js": lambda t: re.sub(r"/\*.*?\*/|//[^\n]*", "", t, flags=re.S),
        "CITATION.cff": lambda t: re.sub(r"(?m)^\s*#[^\n]*$", "", t),
    }
    for rel, limpar in sem_comentario.items():
        texto = limpar((RAIZ / rel).read_text(encoding="utf-8"))
        assert not re.search(r"10\.5281/zenodo\.[X]+", texto), f"DOI de exemplo em {rel}"


# --- Contrato 4: o script escreve o DOI nos quatro lugares ----------------------------


def test_definir_doi_escreve_nos_quatro_arquivos(copia):
    modulo = _carregar_script(copia)
    doi = "10.5281/zenodo.1234567"
    assert modulo.main([doi]) == 0

    publicacao = (copia / "app/src/lib/publicacao.js").read_text(encoding="utf-8")
    assert f'export const DOI = "{doi}";' in publicacao
    citation = (copia / "CITATION.cff").read_text(encoding="utf-8")
    assert f'doi: "{doi}"' in citation
    assert citation.count(doi) >= 2, "o DOI tem de estar na raiz e em preferred-citation"
    assert f"https://doi.org/{doi}" in (copia / "README.md").read_text(encoding="utf-8")
    index_html = (copia / "app/index.html").read_text(encoding="utf-8")
    assert f'"identifier": "https://doi.org/{doi}"' in index_html
    assert modulo.verificar() == 0


def test_definir_doi_e_idempotente(copia):
    modulo = _carregar_script(copia)
    doi = "10.5281/zenodo.1234567"
    modulo.main([doi])
    depois_da_primeira = {
        rel: (copia / rel).read_text(encoding="utf-8")
        for rel in QUATRO_ARQUIVOS
    }
    modulo.main([doi])
    for rel, antes in depois_da_primeira.items():
        assert (copia / rel).read_text(encoding="utf-8") == antes, f"{rel} mudou na 2ª execução"


def test_doi_novo_substitui_o_anterior_em_vez_de_acumular(copia):
    modulo = _carregar_script(copia)
    modulo.main(["10.5281/zenodo.1111111"])
    modulo.main(["10.5281/zenodo.2222222"])
    for rel in QUATRO_ARQUIVOS:
        texto = (copia / rel).read_text(encoding="utf-8")
        assert "zenodo.1111111" not in texto, f"DOI antigo sobreviveu em {rel}"
        assert "zenodo.2222222" in texto


def test_doi_de_versao_entra_como_identificador_adicional(copia):
    modulo = _carregar_script(copia)
    modulo.main(["10.5281/zenodo.1111111", "--doi-versao", "10.5281/zenodo.1111112"])
    citation = (copia / "CITATION.cff").read_text(encoding="utf-8")
    assert "zenodo.1111112" in citation
    # O DOI da versão é identificador adicional: quem cita o conjunto cita o conceitual.
    assert 'export const DOI = "10.5281/zenodo.1111111";' in (
        copia / "app/src/lib/publicacao.js"
    ).read_text(encoding="utf-8")


@pytest.mark.parametrize(
    "invalido",
    ["zenodo.1234567", "10.5281", "https://doi.org/10.5281/zenodo.1", "10.5281/", ""],
)
def test_doi_malformado_e_recusado_sem_escrever(copia, invalido):
    modulo = _carregar_script(copia)
    antes = (copia / "app/src/lib/publicacao.js").read_text(encoding="utf-8")
    rc = modulo.main([invalido]) if invalido else modulo.main(["--verificar"])
    if invalido:
        assert rc == 2
    assert (copia / "app/src/lib/publicacao.js").read_text(encoding="utf-8") == antes


# --- Contrato 5: transacional ---------------------------------------------------------


def test_ancora_ausente_impede_qualquer_escrita(copia):
    """Se o README perder a âncora, os outros três arquivos não podem ser escritos."""
    readme = copia / "README.md"
    readme.write_text("# sem âncora de DOI\n", encoding="utf-8")
    modulo = _carregar_script(copia)
    antes = (copia / "app/src/lib/publicacao.js").read_text(encoding="utf-8")

    citation_antes = (copia / "CITATION.cff").read_text(encoding="utf-8")

    assert modulo.main(["10.5281/zenodo.1234567"]) == 2
    assert (copia / "app/src/lib/publicacao.js").read_text(encoding="utf-8") == antes
    # Comparação contra o estado anterior, não contra a ausência da palavra "zenodo": o
    # repositório já pode ter um DOI escrito, e o contrato é "nada foi escrito", não
    # "nunca houve DOI".
    assert (copia / "CITATION.cff").read_text(encoding="utf-8") == citation_antes


# --- Contrato 6: a exposição residual é verificável, não declarada ---------------------
#
# Reescrever o histórico não apaga os objetos do servidor: `refs/pull/*` os segura e
# nenhum push do dono as remove. O contrato aqui não é "o repositório está limpo" — isso
# depende do servidor e muda fora do repositório —, é que a *verificação* funciona: que
# ela acusa quando há exposição e que não confunde falha de rede com ausência de exposição.


def _carregar_verificador():
    nome = "verificar_exposicao_teste"
    spec = importlib.util.spec_from_file_location(
        nome, RAIZ / "scripts" / "verificar_exposicao.py"
    )
    modulo = importlib.util.module_from_spec(spec)
    sys.modules[nome] = modulo
    spec.loader.exec_module(modulo)
    return modulo


def test_config_de_commits_obsoletos_lista_o_historico_descartado():
    v = _carregar_verificador()
    shas = v.shas_descartados()
    assert len(shas) == 10, "4 commits de histórico + 6 heads de PR"
    assert all(re.fullmatch(r"[0-9a-f]{40}", s) for s in shas), "SHA fora do formato"
    assert len(set(shas)) == len(shas), "SHA repetido na lista"


def test_mapeamento_declara_a_confianca_de_cada_correspondencia():
    """A correspondência de a81ac6b é inferida, não verificada — e tem de dizer isso."""
    import yaml

    dados = yaml.safe_load((RAIZ / "config/commits_obsoletos.yaml").read_text(encoding="utf-8"))
    commits = [c for r in dados["reescritas"] for c in r["commits"]]
    assert all(c["confianca"] in {"verificada", "inferida"} for c in commits)
    inferidas = [c["sha"][:7] for c in commits if c["confianca"] == "inferida"]
    assert inferidas == ["a81ac6b"], f"mudou o que é inferido: {inferidas}"


def test_verificador_acusa_ref_remota_apontando_para_commit_descartado(monkeypatch):
    v = _carregar_verificador()
    descartado = v.shas_descartados()[0]
    monkeypatch.setattr(v, "ls_remote", lambda _r: {"refs/pull/1/head": descartado})
    monkeypatch.setattr(v, "commit_na_api", lambda _repo, _sha: None)
    monkeypatch.setattr(v, "commits_de_main", lambda: set())

    res = v.verificar("dono/repo", "origin")
    assert not res.limpo
    assert any("refs/pull/1/head" in m for m in res.expostos)


def test_verificador_acusa_commit_que_a_api_ainda_entrega(monkeypatch):
    v = _carregar_verificador()
    descartado = v.shas_descartados()[0]
    monkeypatch.setattr(v, "ls_remote", lambda _r: {})
    monkeypatch.setattr(
        v, "commit_na_api", lambda _repo, sha: {"parents": []} if sha == descartado else None
    )
    monkeypatch.setattr(v, "commits_de_main", lambda: set())

    res = v.verificar("dono/repo", "origin")
    assert not res.limpo
    assert any(descartado in m for m in res.expostos)


def test_verificador_acusa_ref_pull_que_nasce_de_historico_morto(monkeypatch):
    """Uma ref de PR nova com SHA desconhecido ainda pode ancorar histórico descartado."""
    v = _carregar_verificador()
    monkeypatch.setattr(v, "ls_remote", lambda _r: {"refs/pull/9/head": "f" * 40})
    def api(_repo, sha):
        return {"parents": [{"sha": "e" * 40}]} if sha == "f" * 40 else None

    monkeypatch.setattr(v, "commit_na_api", api)
    monkeypatch.setattr(v, "commits_de_main", lambda: {"a" * 40})

    res = v.verificar("dono/repo", "origin")
    assert not res.limpo
    assert any("ancora um histórico descartado" in m for m in res.expostos)


def test_verificador_aprova_ref_pull_nascida_do_historico_vivo(monkeypatch):
    v = _carregar_verificador()
    monkeypatch.setattr(v, "ls_remote", lambda _r: {"refs/pull/9/head": "f" * 40})
    def api(_repo, sha):
        return {"parents": [{"sha": "a" * 40}]} if sha == "f" * 40 else None

    monkeypatch.setattr(v, "commit_na_api", api)
    monkeypatch.setattr(v, "commits_de_main", lambda: {"a" * 40})

    res = v.verificar("dono/repo", "origin")
    assert res.limpo, res.expostos


def test_falha_de_rede_nao_vira_veredito_de_limpo(monkeypatch):
    """Um 403 de limite de taxa não pode ser lido como 'o commit sumiu'."""
    v = _carregar_verificador()
    monkeypatch.setattr(v, "ls_remote", lambda _r: {})

    def recusa(_repo, _sha):
        raise v.ErroDeVerificacao("limite de taxa")

    monkeypatch.setattr(v, "commit_na_api", recusa)
    monkeypatch.setattr(v, "commits_de_main", lambda: set())

    assert v.main(["--repo", "dono/repo"]) == 2, "rc tem de ser 2 (inconclusivo), não 0"


def test_comentario_de_doi_ausente_nao_sobrevive_a_emissao(copia):
    """O JSON-LD não pode publicar "ainda não emitiu" ao lado de um DOI emitido."""
    modulo = _carregar_script(copia)
    modulo.main(["10.5281/zenodo.1234567"])
    html = (copia / "app/index.html").read_text(encoding="utf-8")
    assert "ainda não emitiu" not in html
    assert "zenodo.XXXXXXX" not in html
    assert "DOI CONCEITUAL do Zenodo" in html


def test_referencia_nao_repete_o_identificador():
    """A citação mostrava o identificador duas vezes: o texto ABNT já terminava nele e a
    tela acrescentava o link em seguida. O corpo e a cláusula de acesso são separados."""
    fonte = (RAIZ / "app/src/lib/publicacao.js").read_text(encoding="utf-8")
    assert "export function referenciaPartes" in fonte
    corpo = fonte.split("export function referenciaPartes")[1].split("export function")[0]
    assert "DOI: ${DOI}" in corpo, "a cláusula de acesso tem de sair de referenciaPartes"

    jsx = (RAIZ / "app/src/components/ComoCitar.jsx").read_text(encoding="utf-8")
    assert "referenciaPartes" in jsx
    assert "{corpo}" in jsx and "acesso.href" in jsx
    # O texto completo continua existindo — é o que o botão "Copiar" entrega.
    assert "referenciaAbnt(lang)" in jsx
