"""Contrato: a avaliação de hipótese nos artefatos não pode ser mais antiga que a medição.

Defeito real, pego pelo portão da Fase 2b (ORCHESTRATION_LOG.md 2b-09): `data/DATA_AUDIT.md`
e `PROVENANCE.md` afirmavam que H5 era "RESPONDÍVEL" e H6 "PARCIAL", com data anterior a
`docs/ADR/0012` e `0014`, que mediram kappa −0,065 e Jaccard 0,001 para a classe que
sustentaria as duas. A avaliação honesta existia — mas só no log de orquestração, que o app
e o artigo não consomem.

Emendar um ADR não propaga sozinho: é a mesma lição de `docs/ADR/0011`, que corrigiu o
limiar absoluto só na pegada e deixou o defeito vivo em outras duas classes.
"""
from __future__ import annotations

import re
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]

def artefatos_consumidos() -> list[Path]:
    """Todo artefato que o app ou o artigo consomem.

    A primeira versão deste contrato listava só `DATA_AUDIT.md` e `PROVENANCE.md` — os dois
    onde o defeito tinha aparecido. O portão da Fase 2b mostrou que ele reincidiu uma camada
    abaixo, em `stats_by_year_by_unit.csv` e em `data/provenance_parts/metricas_fase2.md`,
    **sem que este contrato acusasse**. Escopar a regra às instâncias observadas, e não ao
    fenômeno, é o mesmo erro do limiar de denominador de `docs/ADR/0014`.
    """
    alvos = [ROOT / "PROVENANCE.md", ROOT / "data" / "DATA_AUDIT.md"]
    alvos += sorted((ROOT / "data" / "processed").glob("*.csv"))
    alvos += sorted((ROOT / "data" / "provenance_parts").glob("*.md"))
    return [a for a in alvos if a.exists()]


def afirma_sobre_hipotese(caminho: Path) -> bool:
    """O artefato faz afirmação que uma medição posterior pode falsificar?

    A regra de data só cabe aqui. Um CSV de contagem bruta não fica errado porque um ADR
    foi escrito depois — mas um documento que diz "H5 é respondível" fica, se a medição
    disser o contrário. Aplicar a regra de data a tudo foi a minha sobrecorreção ao
    reprovar da primeira vez.
    """
    if caminho.suffix != ".md":
        return False
    texto = caminho.read_text(encoding="utf-8")
    return bool(re.search(r"\bH[1-6]\b|respond[íi]vel|test[áa]vel|sufici[êe]ncia", texto, re.I))

# ADRs que mediram desempenho e podem invalidar uma avaliação anterior de testabilidade.
ADRS_DE_MEDICAO = ["0012", "0013", "0014"]


def test_artefatos_consumidos_nao_sao_mais_antigos_que_os_adrs_de_medicao():
    """Se um ADR mediu desempenho depois, o artefato precisa ter sido reconciliado."""
    adrs = []
    for numero in ADRS_DE_MEDICAO:
        achados = list((ROOT / "docs" / "ADR").glob(f"{numero}-*.md"))
        adrs.extend(achados)
    if not adrs:
        pytest.skip("nenhum ADR de medição ainda")

    mais_novo = max(a.stat().st_mtime for a in adrs)
    problemas = []
    for alvo in artefatos_consumidos():
        if not afirma_sobre_hipotese(alvo):
            continue  # não faz afirmação falsificável: a data não o compromete
        if alvo.stat().st_mtime < mais_novo - 2.0:
            problemas.append(
                f"{alvo.relative_to(ROOT)} é anterior ao ADR de medição mais recente — "
                "reconcilie ou regenere antes de publicar"
            )
    assert not problemas, "; ".join(problemas)


def test_nenhum_artefato_afirma_testabilidade_falsificada():
    """Frases que a medição desmentiu não podem sobreviver nos artefatos consumidos.

    Não basta a data: um documento regenerado pode reproduzir a frase antiga vinda de um
    fragmento. A verificação é textual e mira as afirmações concretas que os ADRs 0012 e
    0014 falsificaram.
    """
    # (padrão proibido, marca de reconciliação que o torna aceitável na mesma vizinhança)
    proibidos = [
        (r"permite testar\s+H5", "H5"),
        (r"H6\s+permanece parcialmente test", "H6"),
        (r"H5[^\n]{0,40}RESPONDÍVEL", "H5"),
    ]
    problemas = []
    for alvo in artefatos_consumidos():
        rel = alvo.relative_to(ROOT)
        texto = alvo.read_text(encoding="utf-8")
        reconciliado = "RECONCILIAÇÃO OBRIGATÓRIA" in texto
        for padrao, hip in proibidos:
            for m in re.finditer(padrao, texto, re.I):
                if reconciliado:
                    continue  # o documento carrega a reconciliação que corrige a frase
                linha = texto[: m.start()].count("\n") + 1
                problemas.append(
                    f"{rel}:{linha}: afirma testabilidade de {hip} "
                    "que a medição desmentiu"
                )
    assert not problemas, "; ".join(problemas)


def test_metricas_por_pixel_carregam_a_ressalva_de_churn():
    """Tipologia e transição por pixel exigem a ressalva de churn de `docs/ADR/0013`.

    O churn de identidade de pixel medido em `urbano` é de 31 a 54 % entre anos-âncora:
    a área é utilizável, a localização não. Qualquer métrica que dependa de **qual** pixel
    mudou — infill, borda, leapfrog, matriz de transição — herda essa incerteza, e o
    artefato que a publica precisa dizê-lo.
    """
    import csv

    alvos = {
        "prop_infill": "tipologia de expansão",
        "prop_borda": "tipologia de expansão",
        "prop_leapfrog": "tipologia de expansão",
        "transicao": "matriz de transição",
    }
    stats = ROOT / "data" / "processed" / "stats_by_year_by_unit.csv"
    problemas = []

    if stats.exists():
        with stats.open(encoding="utf-8", newline="") as fh:
            for linha in csv.DictReader(fh):
                var = linha.get("variavel", "")
                if any(var.startswith(k) for k in alvos):
                    nota = (linha.get("nota") or "").lower()
                    if "churn" not in nota:
                        problemas.append(
                            f"stats_by_year_by_unit.csv: '{var}' "
                            f"({linha.get('unidade_geografica')}, {linha.get('ano')}) "
                            "sem ressalva de churn"
                        )
                        break  # uma linha por variável basta

    frag = ROOT / "data" / "provenance_parts" / "metricas_fase2.md"
    if frag.exists() and "churn" not in frag.read_text(encoding="utf-8").lower():
        problemas.append("provenance_parts/metricas_fase2.md: sem ressalva de churn")

    assert not problemas, "; ".join(problemas)
