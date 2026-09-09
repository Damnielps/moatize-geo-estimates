"""Contrato das afirmações relacionais: número certo, qualificador errado.

Duas ocorrências reais, ambas na Fase 4, ambas **originadas no orquestrador**, ambas
invisíveis aos 101 contratos anteriores (ORCHESTRATION_LOG.md 4-03 e 4-04):

1. O app dizia razão teto/piso "de **até** 5,2×". O 5,21 existe — é a **mediana** de
   `reassentamento`. O máximo é **6,69**. A palavra "até" transformou mediana em máximo e
   subestimou a incerteza em 28 %, na frase que existe para declarar incerteza.
2. O app dizia comissão de `urbano` "entre 37 % e **63 %**". O 0,625 existe — é a
   **acurácia do usuário máxima**. A comissão é o seu **complemento**, e vai a **71,4 %**.
   Confundiu uma grandeza com o seu complemento, num aviso exibido sempre que a camada
   está ativa.

Nos dois casos o número existia, a fonte existia, e o que não existia era a **relação**
entre eles. Nenhum contrato comparava o que o texto afirma sobre um número com o que aquele
número é — e a Fase 5 é quase inteiramente prosa.

O método aqui é o mesmo de `test_transparencia_metodologica.py` para versões de biblioteca:
**o valor canônico é calculado da fonte, nunca escrito neste arquivo.** Se a fonte mudar,
o contrato acompanha; se o texto ficar para trás, o contrato acusa.
"""
from __future__ import annotations

import csv
import re
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
PROCESSED = ROOT / "data" / "processed"

# Superfícies de texto onde uma afirmação relacional pode aparecer.
#
# ESCOPO CORRIGIDO (ORCHESTRATION_LOG.md 4-06). A primeira versão listava só `app/src` e
# `paper/` — **onde o defeito tinha aparecido**, não onde ele podia aparecer. O portão
# mostrou que a terceira instância vivia em `pipeline/`: a nota "entre 37 % e 73 %",
# codificada em 14 arquivos de `pipeline/`, é gravada em 152 linhas de
# `decomposicao_luz_por_camada.csv` e repassada verbatim a `metodologia.json`, que o app
# serve ao usuário. Uma exclusão de conveniência protegia exatamente a cópia sobrevivente.
#
# É a terceira vez nesta sessão que escopar o contrato à instância deixa o defeito
# reincidir uma camada abaixo (2-10, 3-04, e agora esta) — e a segunda em que o autor do
# contrato mal escopado é o orquestrador.
SUPERFICIES = [
    ROOT / "app" / "src",
    ROOT / "paper",
    ROOT / "pipeline",
    ROOT / "data" / "processed",
    ROOT / "docs",
]
EXTENSOES = {".jsx", ".js", ".ts", ".tsx", ".md", ".qmd", ".tex", ".py", ".csv", ".json"}
# Arquivos de teste falam de defeitos passados citando os números errados de propósito.
EXCLUIR_DIRS = {"tests", "node_modules", "dist", ".venv"}

# Tolerância em pontos percentuais. 1,0 acomoda arredondamento honesto ("37 %" para 37,5 %)
# e reprova confusão de grandeza (63 % contra 71,4 % erra por 8 pontos).
TOL_PP = 1.0


def _num(v):
    try:
        return float(v)
    except (TypeError, ValueError):
        return None


def comissao_urbano_pct() -> tuple[float, float] | None:
    """Comissão = 1 − acurácia do usuário. Calculada, nunca transcrita."""
    caminho = PROCESSED / "acuracia_por_ano.csv"
    if not caminho.exists():
        return None
    with caminho.open(encoding="utf-8", newline="") as fh:
        vals = [
            _num(x.get("acuracia_usuario_construido"))
            for x in csv.DictReader(fh)
        ]
    vals = [v for v in vals if v is not None]
    if not vals:
        return None
    return (100 * (1 - max(vals)), 100 * (1 - min(vals)))


def churn_construido_pct() -> tuple[float, float] | None:
    caminho = PROCESSED / "causal" / "estabilidade_temporal_camadas.csv"
    if not caminho.exists():
        return None
    with caminho.open(encoding="utf-8", newline="") as fh:
        vals = [
            _num(x.get("churn")) for x in csv.DictReader(fh)
            if x.get("classe") == "construido"
        ]
    vals = [v for v in vals if v is not None]
    if not vals:
        return None
    return (100 * min(vals), 100 * max(vals))


def arquivos_de_texto() -> list[Path]:
    saida: list[Path] = []
    for base in SUPERFICIES:
        if not base.exists():
            continue
        saida += [
            p for p in base.rglob("*")
            if p.is_file()
            and p.suffix in EXTENSOES
            and not (EXCLUIR_DIRS & set(p.parts))
        ]
    return saida


# (nome legível, calculadora, palavras que identificam o conceito no texto)
# As palavras identificam o CONCEITO, não uma redação. A primeira versão listava só
# "comiss"/"commission" e perdia a formulação que o repositório de fato usa — "acurácia do
# usuário ... entre 37 % e 73 % do que o mapa chama de construído não é" —, que não contém
# a palavra "comissão" em lugar nenhum (ORCHESTRATION_LOG.md 4-09). Um detector de conceito
# calibrado sobre um único jeito de dizer a coisa é a mesma falha de escopo de sempre,
# agora em vocabulário.
FAIXAS = [
    (
        "comissão de `urbano`",
        comissao_urbano_pct,
        ("comiss", "commission", "acurácia do usuário", "acuracia do usuario",
         "user accuracy", "chama de construído", "chama de construido",
         "calls built-up", "calls “urban”", 'calls "urban"'),
    ),
    ("churn de `construido`", churn_construido_pct, ("churn",)),
]

# Faixa escrita em DECIMAL, sem "%": "0,27–0,63" é a forma dos ADR e foi a que
# sobreviveu no docs/ADR/0011 até a sexta passagem do portão (4-11).
PADRAO_DECIMAL = re.compile(
    r"(?:entre\s+)?(0[.,]\d{2,3})\s*(?:[–—-]|a|e|to|and)\s*(0[.,]\d{2,3})", re.I
)

# Formas de escrever faixa que o repositório de fato usa.
#
# QUARTA VACUIDADE (ORCHESTRATION_LOG.md 4-10). A versão anterior só casava
# "entre X % e Y %" e "de X % a Y %" — e **não** casava "X %–Y %", que é o formato
# canônico produzido por `pipeline/lib/acuracia_texto.py` e o majoritário no repositório.
# Medido: "37,5 %–71,4 %" dava 0 casamentos. Uma classe inteira de citações ficava fora da
# verificação, no formato que o próprio gerador emite.
#
# É a quarta vez que este contrato falha por cobrir só a forma em que o defeito apareceu:
# linha a linha, parágrafo, vocabulário, e agora pontuação.
PADRAO_FAIXA = re.compile(
    r"(?:"
    r"(?:entre|between|de|from)\s+(?P<a1>\d{1,3}(?:[.,]\d+)?)\s*%\s*(?:e|and|a|to)\s+"
    r"(?P<b1>\d{1,3}(?:[.,]\d+)?)\s*%"
    r"|"
    # "X %–Y %", "X%-Y%", "X % a Y %" com travessão, meia-risca ou hífen
    r"(?P<a2>\d{1,3}(?:[.,]\d+)?)\s*%\s*[–—-]\s*(?P<b2>\d{1,3}(?:[.,]\d+)?)\s*%"
    r")",
    re.I,
)


def _faixa_do_match(m: re.Match) -> tuple[float, float]:
    a = m.group("a1") or m.group("a2")
    b = m.group("b1") or m.group("b2")
    return float(a.replace(",", ".")), float(b.replace(",", "."))



def _distancia_ao_conceito(plano: str, ini: int, chaves) -> int:
    """Distância, em caracteres, da afirmação à menção mais próxima de um conceito.

    Serve à regra "grandeza mais próxima vence" (ORCHESTRATION_LOG.md 4-13): um parágrafo
    pode falar de comissão E de churn, e sem esta desambiguação cada teste acusa a faixa do
    outro — o mesmo erro relacional que eles existem para pegar, cometido entre dois testes
    irmãos.
    """
    baixa = plano.lower()
    melhor = 10**9
    for k in chaves:
        pos = baixa.rfind(k.lower(), max(0, ini - 400), ini)
        if pos >= 0:
            melhor = min(melhor, ini - pos)
    return melhor


@pytest.mark.parametrize("nome,calc,palavras", FAIXAS, ids=[f[0] for f in FAIXAS])
def test_faixa_declarada_bate_com_a_fonte(nome, calc, palavras):
    """Toda faixa percentual declarada no texto tem de ser a faixa medida no CSV."""
    esperado = calc()
    if esperado is None:
        pytest.skip(f"fonte de {nome} ainda não produzida")
    lo_ok, hi_ok = esperado

    infratores = []
    for caminho in arquivos_de_texto():
        texto = caminho.read_text(encoding="utf-8", errors="ignore")
        # Varredura por PARÁGRAFO com espaços normalizados, não por linha.
        #
        # A primeira versão varria linha a linha e perdia qualquer faixa quebrada entre
        # duas linhas — e quebrar linha é a norma em Markdown e em docstring, que é
        # exatamente o formato do artigo da Fase 5. Medido em
        # `pipeline/lib/acuracia_texto.py`: 0 ocorrências linha a linha, 1 no texto
        # contínuo. O contrato passaria por vacuidade justamente na maior superfície de
        # prosa do projeto.
        # JANELA LOCAL em torno de cada ocorrência, não "parágrafo" (4-09).
        #
        # A versão anterior partia o texto por linha em branco. Num JSON pretty-printed
        # sem linhas em branco — `metodologia.json`, 411 KB e 5.673 linhas — o arquivo
        # inteiro virava **um único parágrafo**, e a dispensa de citação histórica, que
        # só exige a marca "0014" **em algum ponto do bloco**, passava a valer para o
        # arquivo todo. O contrato ficava incapaz de disparar ali, qualquer que fosse o
        # número — e era justamente onde sobrevivia a quarta instância do valor obsoleto,
        # em conteúdo servido ao usuário.
        #
        # A dispensa agora é avaliada numa janela de ±400 caracteres em torno da própria
        # afirmação: "aqui perto está dito que isto é histórico", não "em algum lugar
        # deste arquivo existe a palavra 0014".
        # Remove ênfase Markdown ANTES de casar: a forma real do repositório é
        # "entre **37 % e 63 %**", e os asteriscos impediam o casamento — sexta
        # vacuidade (4-11). Normalizar a marcação é mais robusto que enumerá-la.
        plano = re.sub(r"[*_`]+", "", re.sub(r"\s+", " ", texto))
        if not any(p in plano.lower() for p in palavras):
            continue
        for m in PADRAO_FAIXA.finditer(plano):
            ini, fim = m.span()
            janela = plano[max(0, ini - 400):fim + 400]
            if not any(p in janela.lower() for p in palavras):
                continue  # a faixa não é da grandeza que este teste cobre

            # GRANDEZA CONCORRENTE no contexto imediato (4-11). Um parágrafo pode falar
            # de acurácia do usuário E citar a acurácia GLOBAL que um classificador nulo
            # obteria (98,1 %–99,4 %, docs/ADR/0009). Sem esta exclusão o contrato acusa
            # a grandeza errada — o mesmo erro relacional que ele existe para pegar,
            # cometido por ele.
            antes = plano[max(0, ini - 120):ini].lower()
            if re.search(r"acur[áa]cia global|global accuracy|preval[êe]ncia|kappa"
                         r"|acur[áa]cia do produtor|producer accuracy"
                         # Fração herdada da catraca R2 (docs/ADR/0013): outra grandeza,
                         # que também vive perto de menções à comissão. 4-15.
                         r"|herdad|uni[ãa]o cumulativa|catraca|estoque|jaccard"
                         r"|fra[çc][ãa]o do estoque|inherited", antes):
                continue

            # GRANDEZA MAIS PRÓXIMA VENCE (4-13). Um parágrafo pode falar de comissão E de
            # churn; sem isto, cada teste acusa a faixa do outro — o mesmo erro relacional
            # que ele existe para pegar, cometido entre dois testes irmãos. Só dispara o
            # teste cuja grandeza está MAIS PERTO da afirmação.
            minha = _distancia_ao_conceito(plano, ini, palavras)
            outras = [
                _distancia_ao_conceito(plano, ini, outras_palavras)
                for _, _, outras_palavras in FAIXAS
                if outras_palavras != palavras
            ]
            if outras and min(outras) < minha:
                continue
            historico = bool(
                re.search(r"\b0014\b", janela)
                # Marcadores por RADICAL, não por palavra inteira: a versão anterior
                # tinha "antes" e falhava em "anteriores" — quinta vez que este
                # contrato erra por cobrir uma só forma de dizer a coisa (4-10).
                and re.search(
                    r"\b0009\b|ante[sr]|substitu|superad|supersess|obsolet"
                    r"|corrigi|reexecu|nunca citar|n[ãa]o citar|hist[óo]ric",
                    janela, re.I,
                )
            )
            if historico:
                continue
            lo, hi = _faixa_do_match(m)
            if abs(lo - lo_ok) > TOL_PP or abs(hi - hi_ok) > TOL_PP:
                # Linha aproximada: conta quebras no texto original até o trecho casado.
                trecho = m.group(0)
                pos = texto.find(trecho.split()[0])
                linha_n = texto[:pos].count("\n") + 1 if pos >= 0 else 0
                infratores.append(
                    f"{caminho.relative_to(ROOT)}:~{linha_n}: {nome} declarada como "
                    f"{lo:g}%–{hi:g}%, medida é {lo_ok:.1f}%–{hi_ok:.1f}%"
                )

    assert not infratores, (
        "faixa declarada no texto não é a faixa medida na fonte:\n  "
        + "\n  ".join(infratores)
    )


def test_razao_teto_piso_nao_e_declarada_como_maximo():
    """A mediana de uma razão não pode ser apresentada com qualificador de máximo.

    O defeito de 4-03: "razão teto/piso de ATÉ 5,2" — 5,21 é mediana, o máximo é 6,69.
    """
    caminho = PROCESSED / "causal" / "decomposicao_luz_por_camada.csv"
    if not caminho.exists():
        pytest.skip("decomposição ainda não produzida")

    with caminho.open(encoding="utf-8", newline="") as fh:
        vals = [_num(x.get("razao_teto_sobre_piso")) for x in csv.DictReader(fh)]
    vals = [v for v in vals if v is not None]
    if not vals:
        pytest.skip("coluna razao_teto_sobre_piso vazia")
    maximo = max(vals)

    # Qualificadores de máximo seguidos de um número, na mesma frase que fala da razão.
    padrao = re.compile(
        r"(?:at[ée]|no m[áa]ximo,?|up to|at most,?)\s+(\d{1,2}(?:[.,]\d+)?)\s*[×x]?",
        re.I,
    )
    infratores = []
    for caminho_txt in arquivos_de_texto():
        # Mesma varredura por JANELA do teste acima (4-11). A versão anterior varria
        # linha a linha e exigia "teto/piso" na MESMA linha do "até N": bastava a frase
        # quebrar entre linhas para escapar. Era a primeira vacuidade sobrevivendo no
        # segundo contrato, cinco correções depois de ter sido diagnosticada no primeiro.
        texto = caminho_txt.read_text(encoding="utf-8", errors="ignore")
        plano = re.sub(r"[*_`]+", "", re.sub(r"\s+", " ", texto))
        baixa = plano.lower()
        if "teto/piso" not in baixa and "teto sobre piso" not in baixa:
            continue
        for m in padrao.finditer(plano):
            ini = m.start()
            janela = plano[max(0, ini - 300):m.end() + 100].lower()
            if "teto/piso" not in janela and "teto sobre piso" not in janela:
                continue
            # O número tem de ser uma RAZÃO, não qualquer coisa contável perto de uma
            # menção a teto/piso. "até 3 anos de distância" apareceu como falso positivo
            # (4-11) — é distância temporal, não razão. Exige-se marca de razão colada.
            perto = plano[max(0, ini - 80):m.end() + 40].lower()
            if not re.search(r"[×x]|vezes|raz[ãa]o|teto/piso|ratio", perto):
                continue
            # Citação histórica: a docstring que explica o defeito "até 5,2" precisa
            # poder citá-lo. Mesma dispensa do teste acima.
            if re.search(r"\b0015\b|hist[óo]ric|defeito|era mediana|4-0[0-9]", janela):
                continue
            declarado = float(m.group(1).replace(",", "."))
            if abs(declarado - maximo) > 0.15:
                pos = texto.find(m.group(0).split()[0])
                linha_n = texto[:pos].count("\n") + 1 if pos >= 0 else 0
                infratores.append(
                    f"{caminho_txt.relative_to(ROOT)}:~{linha_n}: declara máximo "
                    f"{declarado:g}, máximo medido é {maximo:.2f}"
                )

    assert not infratores, (
        "qualificador de máximo com valor que não é o máximo da fonte:\n  "
        + "\n  ".join(infratores)
    )

def acuracia_usuario_faixa() -> tuple[float, float] | None:
    """Faixa da acurácia do usuário de `construido`, em decimal (não em %)."""
    caminho = PROCESSED / "acuracia_por_ano.csv"
    if not caminho.exists():
        return None
    with caminho.open(encoding="utf-8", newline="") as fh:
        vals = [_num(x.get("acuracia_usuario_construido")) for x in csv.DictReader(fh)]
    vals = [v for v in vals if v is not None]
    return (min(vals), max(vals)) if vals else None


def test_faixa_decimal_de_acuracia_bate_com_a_fonte():
    """Faixa escrita em DECIMAL, sem "%": "0,27–0,63", a forma dos ADR.

    Defeito real (ORCHESTRATION_LOG.md 4-12): `PADRAO_DECIMAL` foi escrito na sexta
    passagem e **nunca ligado ao laço de varredura** — definido, compilado, nunca usado.
    O contrato passava dando aparência de cobrir a forma decimal, e a instância viva de
    `docs/ADR/0007:92` ("entre **0,27 e 0,63**", sem marca de supersessão) atravessava
    até o `metodologia.json` servido ao usuário.

    Código morto num contrato é pior que contrato ausente: promete verificação que não
    acontece.
    """
    esperado = acuracia_usuario_faixa()
    if esperado is None:
        pytest.skip("acuracia_por_ano.csv ainda não produzido")
    lo_ok, hi_ok = esperado
    tol = 0.01  # acomoda "0,29" para 0,286; reprova 0,27 (erra por 0,016)

    palavras = ("acurácia do usuário", "acuracia do usuario", "user accuracy",
                "comiss", "commission")
    infratores = []
    for caminho in arquivos_de_texto():
        texto = caminho.read_text(encoding="utf-8", errors="ignore")
        plano = re.sub(r"[*_`]+", "", re.sub(r"\s+", " ", texto))
        if not any(p in plano.lower() for p in palavras):
            continue
        for m in PADRAO_DECIMAL.finditer(plano):
            ini, fim = m.span()
            janela = plano[max(0, ini - 400):fim + 400]
            if not any(p in janela.lower() for p in palavras):
                continue
            antes = plano[max(0, ini - 120):ini].lower()
            if re.search(r"acur[áa]cia global|global accuracy|preval[êe]ncia|kappa"
                         r"|acur[áa]cia do produtor|producer accuracy|jaccard", antes):
                continue
            # Dispensa histórica. Marcador FORTE dispensa sozinho — exigir "0014" na
            # janela reprovava o próprio `docs/ADR/0014`, que escreve "0,286 a 0,625,
            # contra 0,27 a 0,63 antes" e não se autocita pelo número (4-12).
            forte = re.search(
                r"ante[sr]|superad|supersess|obsolet|reexecu|nunca citar"
                r"|n[ãa]o citar|hist[óo]ric|passa a ser|em vez de|contra ", janela, re.I
            )
            fraco = re.search(r"\b0014\b", janela) and re.search(
                r"\b0009\b|substitu|corrigi", janela, re.I
            )
            if forte or fraco:
                continue
            lo = float(m.group(1).replace(",", "."))
            hi = float(m.group(2).replace(",", "."))
            if abs(lo - lo_ok) > tol or abs(hi - hi_ok) > tol:
                pos = texto.find(m.group(1).replace(".", ","))
                linha_n = texto[:pos].count("\n") + 1 if pos >= 0 else 0
                infratores.append(
                    f"{caminho.relative_to(ROOT)}:~{linha_n}: acurácia do usuário "
                    f"declarada como {lo:g}–{hi:g}, medida é {lo_ok:.3f}–{hi_ok:.3f}"
                )
    assert not infratores, (
        "faixa decimal declarada no texto não é a medida na fonte:\n  "
        + "\n  ".join(infratores)
    )


# ---------------------------------------------------------------------------
# TAXA DE CRESCIMENTO DEMOGRÁFICO (CAGR)
#
# Escrito ANTES da página de dashboard existir (plano da Frente A, item 9), e por um
# motivo específico: a Fase 4 reprovou oito vezes por afirmação relacional, e **todas as
# instâncias vieram do orquestrador** citando de memória. O dashboard de população vai
# comparar quatro unidades ao longo de quatro pontos, o que dá doze taxas — e taxa é
# exatamente o tipo de número que se escreve de cabeça ("Tete cresce ~7 %/ano") porque
# soa memorável.
#
# Diferença de forma em relação aos testes acima: CAGR é um valor PONTUAL, não uma faixa.
# Por isso não entra em FAIXAS; tem padrão e teste próprios.
#
# Passa por vacuidade enquanto `demografia_serie_1997_2025.csv` não existir, e morde no
# instante em que ele aparecer — mesmo padrão de `test_transparencia_metodologica.py`.
# ---------------------------------------------------------------------------

CSV_DEMOGRAFIA = PROCESSED / "demografia_serie_1997_2025.csv"

# Como o texto nomeia cada unidade. A chave é o `unidade_geografica` do CSV; os valores
# são as formas que a prosa de fato usa. Vocabulário largo de propósito: a quarta
# vacuidade da Fase 4 foi um detector calibrado sobre um único jeito de dizer a coisa.
UNIDADES_NO_TEXTO = {
    "Cidade de Tete": ("cidade de tete", "tete-cidade", "tete (cidade)", "city of tete"),
    "Distrito de Moatize": ("distrito de moatize", "moatize (distrito)", "moatize district"),
    "Vila de Moatize": ("vila de moatize", "sede de moatize", "moatize town"),
    "Província de Tete": ("província de tete", "provincia de tete", "tete province"),
    "Moçambique": ("moçambique", "mocambique", "mozambique", "nacional", "país", "pais"),
}

# "5,18 %/ano", "5,18 % ao ano", "5.18 %/year", "5,18 por cento ao ano"
PADRAO_TAXA = re.compile(
    r"(\d{1,2}(?:[.,]\d{1,3})?)\s*(?:%|por\s+cento|per\s*cent)\s*"
    r"(?:/|\s+ao\s+|\s+a\s+|\s+per\s+|\s+)?(?:ano|year|a\.a\.|aa)\b",
    re.I,
)


def cagr_publicado() -> dict[tuple[str, str], float]:
    """{(unidade, nome_da_variavel_cagr): valor em %/ano}, lido do CSV publicado.

    Nunca transcrito: se a série mudar, o contrato acompanha.
    """
    if not CSV_DEMOGRAFIA.exists():
        return {}
    with CSV_DEMOGRAFIA.open(encoding="utf-8", newline="") as fh:
        linhas = list(csv.DictReader(fh))
    saida: dict[tuple[str, str], float] = {}
    for x in linhas:
        var = (x.get("variavel") or "").strip()
        if not var.startswith("cagr"):
            continue
        v = _num(x.get("valor"))
        if v is not None:
            saida[((x.get("unidade_geografica") or "").strip(), var)] = v
    return saida


def test_taxa_de_crescimento_declarada_bate_com_a_fonte():
    """Toda taxa em %/ano escrita perto de uma unidade tem de existir no CSV.

    A regra é deliberadamente frouxa quanto a QUAL intervalo o texto cita — o texto pode
    dizer "cresce 5,2 %/ano" sem nomear o intervalo — e estrita quanto ao VALOR: o número
    tem de bater com **alguma** taxa publicada daquela unidade. Uma taxa que não existe em
    intervalo nenhum é invenção; e é esse o defeito que o teste persegue.

    Tolerância de 0,05 ponto percentual: acomoda arredondar 5,177 para "5,18" ou "5,2",
    e reprova 5,177 escrito como "7" (o valor da hipótese H1 original, que a reformulação
    do docs/ADR/0003 abandonou e que é o erro mais provável de se cometer de memória).
    """
    publicado = cagr_publicado()
    if not publicado:
        pytest.skip("demografia_serie_1997_2025.csv ainda não produzido")

    tol_pp = 0.05
    por_unidade: dict[str, list[float]] = {}
    for (unidade, _var), valor in publicado.items():
        por_unidade.setdefault(unidade, []).append(valor)

    infratores = []
    for caminho in arquivos_de_texto():
        texto = caminho.read_text(encoding="utf-8", errors="ignore")
        plano = re.sub(r"[*_`]+", "", re.sub(r"\s+", " ", texto))
        baixa = plano.lower()
        for m in PADRAO_TAXA.finditer(plano):
            ini = m.start()
            janela = baixa[max(0, ini - 300):m.end() + 120]

            # Qual unidade está mais perto desta taxa? Mesma regra de desambiguação dos
            # testes acima: a grandeza mais próxima vence. Sem unidade por perto, a taxa
            # não é objeto deste contrato (pode ser CAGR de área, de luz, de qualquer
            # coisa) e é ignorada — falso positivo aqui seria pior que falso negativo,
            # porque desacreditaria o contrato inteiro.
            # A taxa tem de ser de POPULAÇÃO. Exigência POSITIVA, não só exclusão: o
            # repositório está cheio de taxas anuais de outra natureza — CAGR de área
            # construída, viés de sensor de +1,25 %/ano (ADR 0008), taxas de cenário
            # 2035/2040, crescimento de radiância. Sem esta guarda o contrato acusa a
            # grandeza errada, que é exatamente o defeito que ele existe para pegar.
            if not re.search(r"popula|habitante|residente|demogr|censo|hab\b", janela):
                continue

            # Grandeza concorrente colada à taxa: cenário e área têm CAGR próprio.
            antes_curto = baixa[max(0, ini - 160):ini]
            if re.search(
                r"cen[áa]rio|migra[çc][ãa]o|proje[çc][ãa]o de cen|[áa]rea|constru[íi]d|"
                r"radi[âa]ncia|luz|vi[ée]s|sensor|primeira detec",
                antes_curto,
            ):
                continue

            # Unidade mais próxima ANTES da taxa. A versão anterior usava `rfind` sobre a
            # janela inteira, que inclui o texto POSTERIOR — e "Cidade de Tete ... CAGR de
            # 5,18 %/ano; Distrito de Moatize 260.843" atribuía a taxa de Tete a Moatize,
            # porque `rfind` devolve a ÚLTIMA ocorrência. Erro de atribuição dentro do
            # contrato antirrelacional.
            prefixo = baixa[max(0, ini - 300):ini]
            candidatas = []
            for unidade, formas in UNIDADES_NO_TEXTO.items():
                if unidade not in por_unidade:
                    continue
                for f in formas:
                    pos = prefixo.rfind(f)
                    if pos >= 0:
                        candidatas.append((len(prefixo) - pos, unidade))
            if not candidatas:
                continue
            unidade = min(candidatas)[1]

            # Citação histórica ou hipótese explicitamente rotulada como abandonada
            # (a H1 original falava em "~4 %/ano" e "~7 %/ano"): dispensada.
            if re.search(
                r"\bh1\b|hip[óo]tese|abandonad|reformulad|0003|original|"
                r"ante[sr]|superad|obsolet",
                janela,
            ):
                continue

            declarado = float(m.group(1).replace(",", "."))
            if not any(abs(declarado - v) <= tol_pp for v in por_unidade[unidade]):
                linha_n = texto[: texto.find(m.group(0).split()[0])].count("\n") + 1
                infratores.append(
                    f"{caminho.relative_to(ROOT)}:~{linha_n}: taxa {declarado:g} %/ano "
                    f"atribuída a {unidade!r} não existe no CSV; publicadas: "
                    + ", ".join(f"{v:g}" for v in sorted(por_unidade[unidade]))
                )

    assert not infratores, (
        "taxa de crescimento declarada no texto não é a medida na fonte:\n  "
        + "\n  ".join(infratores)
    )


# ---------------------------------------------------------------------------
# Adensamento 2020->2025: a área existe no CSV e NÃO é publicável como área.
# ---------------------------------------------------------------------------
CSV_ADENSAMENTO_SENS = PROCESSED / "adensamento_sensibilidade.csv"
META_ADENSAMENTO = (
    PROCESSED / "imagery" / "adensamento_2020_2025_240m_32736.tif.meta.json"
)

# Ressalva mínima que precisa acompanhar a área: ou o selo, ou o regime de publicação,
# ou a sensibilidade. Vocabulário de CONCEITO, não de palavra — três formas de dizer a
# mesma coisa, porque exigir uma frase literal é contrato vazio disfarçado.
RESSALVAS_ADENSAMENTO = (
    "modelad",           # selo
    "padrão espacial",   # regime de publicação
    "padrao espacial",
    "ordem de grandeza",
    "sensibilidad",      # a variação por decil
    "não é publicável",
    "nao e publicavel",
    "não publicável como área",
)


def _area_base_adensando() -> float | None:
    """Lida da fonte em tempo de execução. NUNCA codificada aqui: um contrato que
    codifica um valor medido envelhece com ele e passa a defender o erro — foi o que
    aconteceu com `test_figuras.py` e os literais "0,27"/"0,63" (ORCHESTRATION_LOG 4-07).
    """
    import csv as _csv

    if not CSV_ADENSAMENTO_SENS.exists():
        return None
    with CSV_ADENSAMENTO_SENS.open(encoding="utf-8", newline="") as fh:
        for linha in _csv.DictReader(fh):
            if linha.get("variante") == "base":
                return _num(linha.get("area_adensando_km2"))
    return None


def test_area_de_adensamento_nunca_aparece_sem_a_ressalva_que_a_desqualifica():
    """A camada `adensamento_2020_2025` declara no seu próprio meta
    `publicavel_como: padrao_espacial` — a área da classe `adensando` **não é um
    resultado**: ela muda por um fator de ~2,3 só por deslocar um corte em um decil
    (`razao_sensibilidade_maxima_1_decil`, critério pré-registado no ADR 0016).

    Escrever "15,3 km² adensaram" é converter um padrão espacial numa medida de área que
    a própria sensibilidade recusa. É a mesma classe de defeito que esta suíte persegue
    desde a Fase 4 — número certo, estatística errada — e a camada nova é a maior
    superfície nova de prosa desde então.

    O contrato não proíbe citar a área: proíbe citá-la **nua**. Se o número aparece a
    menos de 400 caracteres de "adensa*", uma das ressalvas de `RESSALVAS_ADENSAMENTO`
    tem de estar na mesma vizinhança.
    """
    area = _area_base_adensando()
    if area is None:
        pytest.skip("adensamento_sensibilidade.csv ainda não gerado")

    # Formas plausíveis do mesmo número em texto PT (vírgula) e em código (ponto),
    # com 1 a 4 decimais. Todas derivadas do valor lido, nenhuma digitada.
    #
    # A grafia SEM decimal fica de fora de propósito: 15,3216 arredondado a "15" casa com
    # todo "15" do repositório, e a primeira execução deste contrato reprovou dois ADRs
    # por causa disso. Um contrato que dispara em qualquer inteiro não mede o defeito —
    # mede a frequência do número 15, e seria desligado na primeira semana.
    grafias = set()
    for casas in (1, 2, 3, 4):
        bruto = f"{area:.{casas}f}"
        grafias.add(bruto)
        grafias.add(bruto.replace(".", ","))
    padrao = re.compile(
        r"(?<![\d,.])(" + "|".join(re.escape(g) for g in sorted(grafias, key=len, reverse=True))
        + r")(?![\d,.])"
    )

    faltando = []
    for raiz in SUPERFICIES:
        if not raiz.exists():
            continue
        for caminho in raiz.rglob("*"):
            if not caminho.is_file() or caminho.suffix not in EXTENSOES:
                continue
            if any(p in EXCLUIR_DIRS for p in caminho.parts):
                continue
            try:
                texto = caminho.read_text(encoding="utf-8")
            except (UnicodeDecodeError, OSError):
                continue
            baixa = texto.lower()
            if "adensa" not in baixa:
                continue
            for m in padrao.finditer(texto):
                ini = m.start()
                janela = baixa[max(0, ini - 400): ini + 400]
                if "adensa" not in janela:
                    continue
                # Uma AFIRMAÇÃO DE ÁREA carrega a unidade — mas nem sempre colada ao
                # número. Numa tabela Markdown a unidade vive no CABEÇALHO da coluna
                # ("| variante | área de `adensando` (km²) | ..."), e as células só
                # trazem o valor. A primeira versão exigia `km²` a 40 caracteres do
                # número e por isso era CEGA à Tabela 6 do artigo — o único lugar onde a
                # área aparece como número (achado 3 do portão da Frente C, 2026-09-09).
                # Um contrato que não cobre a superfície real do risco não é um contrato,
                # é uma cerimônia.
                #
                # Duas formas de a unidade estar presente, e basta uma:
                #   (a) colada ao número, em prosa;
                #   (b) no cabeçalho da tabela Markdown a que a linha pertence.
                linha_ini = texto.rfind("\n", 0, ini) + 1
                linha = texto[linha_ini: texto.find("\n", ini)]
                unidade_colada = re.search(r"km\s*[²2^]", baixa[ini: ini + 40])
                unidade_no_cabecalho = False
                if linha.lstrip().startswith("|"):
                    # Sobe até o cabeçalho da tabela (primeira linha do bloco de `|`).
                    bloco_ini = linha_ini
                    while bloco_ini > 0:
                        anterior_ini = texto.rfind("\n", 0, bloco_ini - 1) + 1
                        anterior = texto[anterior_ini: bloco_ini - 1]
                        if not anterior.lstrip().startswith("|"):
                            break
                        bloco_ini = anterior_ini
                    cabecalho = texto[bloco_ini: texto.find("\n", bloco_ini)].lower()
                    unidade_no_cabecalho = bool(re.search(r"km\s*[²2^]", cabecalho))
                if not (unidade_colada or unidade_no_cabecalho):
                    continue
                # A sensibilidade e o meta SÃO a fonte do número: eles o declaram por
                # dever de ofício, e o meta carrega o regime na mesma estrutura.
                if caminho in (CSV_ADENSAMENTO_SENS, META_ADENSAMENTO):
                    continue
                if any(r in janela for r in RESSALVAS_ADENSAMENTO):
                    continue
                faltando.append(
                    f"{caminho.relative_to(ROOT)}:{texto[:ini].count(chr(10)) + 1} "
                    f"— '{m.group(0)}' junto de 'adensa' sem nenhuma ressalva "
                    f"({', '.join(RESSALVAS_ADENSAMENTO[:3])}...) em 400 caracteres"
                )

    assert not faltando, (
        "área de `adensando` publicada como se fosse um resultado de área:\n  "
        + "\n  ".join(faltando)
        + "\n\nO meta declara `publicavel_como: padrao_espacial`. Escreva ONDE adensa "
        "(unidades e anéis de adensamento_2020_2025_por_unidade.csv), não QUANTO."
    )
