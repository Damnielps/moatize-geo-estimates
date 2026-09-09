"""Contratos do pré-registro da Fase 3 e da regra do ramo vazio (docs/ADR/0015).

Dois defeitos reais, ambos da Fase 3:

1. **Ramo de teste relativo com referência nula** (ORCHESTRATION_LOG.md 3-10). O placebo
   espacial P1 classificou os cinco controles como "replica" da quebra de 2022 pelo ramo
   b3, comparando-os com um coeficiente de Tete de **+0,0083 cujo IC95 incluía zero**. O
   teste "≥50% da magnitude de Tete" virava "≥0,0042", que qualquer número satisfaz. O
   veredito dizia ao leitor que os controles replicaram uma queda de Tete — o oposto do
   dado, já que os controles subiam e Tete caía.

   É a sétima ocorrência do padrão de `docs/ADR/0014` (limiar ou razão absoluta sobre
   grandeza não estacionária) e a primeira num critério estatístico. Este contrato existe
   para que a oitava seja pega por máquina e não por leitura.

2. **Integridade do pré-registro** (3-11, 3-12). `docs/DESENHO_FASE3.md` é pré-registro:
   ele só vale se as mudanças forem anexadas como emenda datada, com o texto original
   intacto. Uma emenda que reescreve o desenho para caber no resultado é indistinguível,
   depois, de um desenho que sempre disse aquilo.
"""
from __future__ import annotations

import csv
import re
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
DESENHO = ROOT / "docs" / "DESENHO_FASE3.md"
PLACEBOS = ROOT / "data" / "processed" / "causal" / "placebos.csv"


def _f(v):
    try:
        return float(v)
    except (TypeError, ValueError):
        return None


def _ic_inclui_zero(inf, sup) -> bool | None:
    """None quando o IC não existe — ausência de dado não é ausência de defeito."""
    if inf is None or sup is None:
        return None
    return inf * sup <= 0


def _ramo_sustenta(linha: dict, pref: str) -> tuple[bool, bool | None]:
    """(o ramo sustenta o veredito?, a referência de Tete é estatisticamente nula?)

    Sustenta quando o coeficiente do controle tem mesmo sinal e ao menos metade da
    magnitude do de Tete — a regra pré-registrada em §4.1 do desenho. O segundo valor é o
    que `docs/ADR/0015` acrescenta: se a referência tem IC95 que inclui zero, a razão de
    magnitude não significa nada, porque o denominador é indistinguível de zero.
    """
    campo = "b2_nivel" if pref == "b2" else "b3_inclinacao"
    obs = _f(linha.get(campo))
    ref = _f(linha.get(f"{pref}_real_tete"))
    if obs is None or ref is None or ref == 0:
        return False, None
    mesmo_sinal = (obs > 0) == (ref > 0)
    magnitude = abs(obs) >= 0.5 * abs(ref)
    nulo = _ic_inclui_zero(
        _f(linha.get(f"{pref}_real_ic95_inf")), _f(linha.get(f"{pref}_real_ic95_sup"))
    )
    return (mesmo_sinal and magnitude), nulo


def _linhas_placebo() -> list[dict]:
    if not PLACEBOS.exists():
        return []
    with PLACEBOS.open(encoding="utf-8", newline="") as fh:
        return [x for x in csv.DictReader(fh) if x.get("rotulo")]


def test_nenhum_veredito_de_replica_apoiado_em_referencia_nula():
    """docs/ADR/0015: ramo cujo coeficiente de REFERÊNCIA tem IC que inclui zero é vazio.

    Não é "passa" nem "falha": é não estimável, com motivo. Um veredito conclusivo
    ("replica", "FALHA") sustentado só por um ramo desses é o defeito de 2022 de volta.
    """
    linhas = _linhas_placebo()
    if not linhas:
        pytest.skip("placebos.csv ainda não produzido")

    conclusivos = {"replica", "FALHA"}
    infratores = []
    for x in linhas:
        if x.get("veredito") not in conclusivos:
            continue

        sustenta_b2, ref_b2_nula = _ramo_sustenta(x, "b2")
        sustenta_b3, ref_b3_nula = _ramo_sustenta(x, "b3")

        ramos_validos = [
            s for s, nula in ((sustenta_b2, ref_b2_nula), (sustenta_b3, ref_b3_nula))
            if s and nula is False
        ]
        ramos_nulos = [
            s for s, nula in ((sustenta_b2, ref_b2_nula), (sustenta_b3, ref_b3_nula))
            if s and nula is True
        ]
        if ramos_nulos and not ramos_validos:
            infratores.append(
                f"{x['rotulo']}: veredito {x['veredito']!r} sustentado apenas por ramo "
                "cuja referência de Tete tem IC95 que inclui zero (docs/ADR/0015)"
            )

    assert not infratores, "; ".join(infratores)


def test_veredito_anterior_a_adr0015_foi_preservado():
    """A mudança de critério é pós-dado: o leitor tem de ver os dois vereditos.

    Sobrescrever o veredito original tornaria impossível, depois, distinguir uma regra
    que sempre foi essa de uma regra ajustada ao resultado.
    """
    linhas = _linhas_placebo()
    if not linhas:
        pytest.skip("placebos.csv ainda não produzido")

    assert "veredito_pre_adr0015" in linhas[0], (
        "placebos.csv não preserva o veredito anterior ao docs/ADR/0015 — "
        "a coluna veredito_pre_adr0015 é obrigatória (decisão 2 do ADR)"
    )
    preenchidas = sum(1 for x in linhas if (x.get("veredito_pre_adr0015") or "").strip())
    assert preenchidas > 0, "coluna veredito_pre_adr0015 existe mas está inteiramente vazia"


def test_emendas_do_desenho_sao_anexadas_e_datadas():
    """O pré-registro só vale se a emenda for anexo datado, não reescrita."""
    if not DESENHO.exists():
        pytest.skip("docs/DESENHO_FASE3.md ainda não escrito")

    texto = DESENHO.read_text(encoding="utf-8")
    emendas = re.findall(r"^##\s*\d+\.\s*EMENDA\s*(\d+)\s*[—-]\s*(\d{4}-\d{2}-\d{2})",
                         texto, re.M)
    if not emendas:
        pytest.skip("nenhuma emenda ainda")

    # Toda emenda tem data explícita (o regex acima já a exige) e vem DEPOIS do corpo:
    # a primeira emenda não pode aparecer antes da última seção numerada do desenho.
    pos_primeira_emenda = texto.index("EMENDA")
    secoes = [m.start() for m in re.finditer(r"^##\s*\d+\.", texto, re.M)]
    corpo = [p for p in secoes if p < pos_primeira_emenda]
    assert corpo, "as emendas aparecem antes de qualquer seção do desenho"

    # Afirmação original emendada tem de estar MARCADA, não removida.
    marcas = len(re.findall(r"⟨EMENDADO", texto))
    assert marcas >= len(emendas), (
        f"{len(emendas)} emenda(s) e apenas {marcas} marca(s) ⟨EMENDADO⟩ no corpo: "
        "uma emenda que não marca o que emendou reescreveu o desenho em vez de anexá-lo"
    )


def test_decomposicao_nao_e_publicada_como_particao():
    """docs/ADR/0015 decisão 4: a decomposição de luz NÃO é partição.

    Razão teto/piso medida: 2,1 (industrial), 1,8 (urbano), 5,2 (reassentamento). Com
    envoltórias dessa largura, nenhum nível e nenhum *share* é publicável — só o sinal
    comum às duas. Este contrato exige que o artefato carregue as duas envoltórias, para
    que ninguém leia uma delas como se fosse o valor.
    """
    caminho = ROOT / "data" / "processed" / "causal" / "decomposicao_luz_por_camada.csv"
    if not caminho.exists():
        pytest.skip("decomposição ainda não produzida")

    with caminho.open(encoding="utf-8", newline="") as fh:
        linhas = list(csv.DictReader(fh))
    assert linhas, "decomposicao_luz_por_camada.csv vazio"

    for col in ("soma_radiancia_piso_por_area", "soma_radiancia_teto_por_presenca"):
        assert col in linhas[0], (
            f"{caminho.name} não traz {col}: sem as duas envoltórias, um leitor toma "
            "uma estimativa pontual onde só existe intervalo (docs/ADR/0015)"
        )

    # E a razão entre elas tem de estar exposta, não deixada para o leitor calcular.
    assert "razao_teto_sobre_piso" in linhas[0], (
        f"{caminho.name} não expõe razao_teto_sobre_piso — é ela que diz ao leitor "
        "que a decomposição não é partição"
    )
