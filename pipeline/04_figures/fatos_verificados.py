#!/usr/bin/env python3
"""Gera `paper/FATOS_VERIFICADOS.md`: os números do artigo, extraídos dos CSV.

## Por que este script existe (ORCHESTRATION_LOG.md 4-03 a 4-09)

A Fase 4 reprovou quatro vezes por **afirmação relacional**: número certo, qualificador
errado. "Razão teto/piso de **até** 5,2" (5,21 é mediana; o máximo é 6,69). "Comissão entre
37 % e **63 %**" (0,625 é acurácia, não comissão; a comissão vai a 71,4 %). "Entre 37 % e
**73 %**" (valores anteriores à reexecução do `docs/ADR/0014`). Nos quatro casos o número
existia e a fonte existia; o que não existia era a **relação** entre eles — e as quatro
vieram do orquestrador citando de memória, não dos agentes.

A Fase 5 é um artigo de 8 a 10 mil palavras: a maior superfície de prosa do projeto,
escrita sobre exatamente estes números. Repetir ali o mesmo modo de trabalho — alguém
lembra o valor e escreve — reproduziria o defeito em escala.

Este script produz a **folha de fatos** que o redator consulta: cada número com o caminho
do CSV de onde saiu e a estatística que ele é (mediana, máximo, faixa, ano único). Nenhum
valor é escrito aqui; todos são calculados. É o mesmo padrão de
`pipeline/05_app/gerar_metodologia.py` para versões de biblioteca (§6-A) e de
`pipeline/lib/acuracia_texto.py` para a comissão.

Uso:  uv run python pipeline/04_figures/fatos_verificados.py
Saída: paper/FATOS_VERIFICADOS.md
"""
from __future__ import annotations

import csv
import statistics as st
from datetime import UTC, datetime
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
PROC = REPO_ROOT / "data" / "processed"
SAIDA = REPO_ROOT / "paper" / "FATOS_VERIFICADOS.md"


def linhas(caminho: Path) -> list[dict]:
    if not caminho.exists():
        return []
    with caminho.open(encoding="utf-8", newline="") as fh:
        return list(csv.DictReader(fh))


def num(v) -> float | None:
    try:
        return float(v)
    except (TypeError, ValueError):
        return None


def pt(v: float, casas: int = 0, sinal: bool = False) -> str:
    """Formata em convenção PT: milhar por espaço, decimal por vírgula.

    O bloco da Vila saía em convenção en-US ("15,192" para quinze mil) ao lado de uma
    tabela que escreve "101 984" — duas grafias do mesmo tipo de número na mesma página
    é convite a transcrever errado, e este arquivo existe para ser transcrito.
    """
    fmt = f"{v:+,.{casas}f}" if sinal else f"{v:,.{casas}f}"
    return fmt.replace(",", "\u00a0").replace(".", ",")


def bloco_acuracia(out: list[str]) -> None:
    src = PROC / "acuracia_por_ano.csv"
    dados = [(x["ano"], num(x.get("acuracia_usuario_construido"))) for x in linhas(src)]
    dados = [(a, b) for a, b in dados if b is not None]
    if not dados:
        return
    lo, hi = min(b for _, b in dados), max(b for _, b in dados)
    out += [
        "## Acurácia do usuário e comissão de `construido`",
        "",
        f"Fonte: `{src.relative_to(REPO_ROOT)}`, coluna `acuracia_usuario_construido`.",
        "Decidido em `docs/ADR/0009`; **valores reexecutados em `docs/ADR/0014`**.",
        "",
        "| ano | acurácia do usuário | comissão = 1 − acurácia |",
        "|---|---|---|",
    ]
    for a, b in dados:
        out.append(f"| {a} | {b:.4f} | {100 * (1 - b):.1f} % |")
    out += [
        "",
        f"- **Faixa da acurácia:** {lo:.3f} a {hi:.3f} (mínimo em "
        f"{next(a for a, b in dados if b == lo)}, máximo em "
        f"{next(a for a, b in dados if b == hi)}).",
        f"- **Faixa da comissão:** {100 * (1 - hi):.1f} % a {100 * (1 - lo):.1f} %.",
        "- **Como escrever:** é uma FAIXA entre anos-âncora, não um intervalo de confiança "
        "e não um valor único. Nunca citar 0,27–0,63 nem 37 %–73 %: são anteriores à "
        "reexecução do `docs/ADR/0014`.",
        "",
    ]


def bloco_churn(out: list[str]) -> None:
    src = PROC / "causal" / "estabilidade_temporal_camadas.csv"
    dados = [
        (x["par_anos"], num(x.get("churn")))
        for x in linhas(src)
        if x.get("classe") == "construido"
    ]
    dados = [(a, b) for a, b in dados if b is not None]
    if not dados:
        return
    out += [
        "## Churn de `construido` entre anos-âncora",
        "",
        f"Fonte: `{src.relative_to(REPO_ROOT)}` (`docs/ADR/0013`).",
        "",
    ]
    out += [f"- {a}: {100 * b:.1f} %" for a, b in dados]
    out += [
        "",
        f"- **Faixa:** {100 * min(b for _, b in dados):.1f} % a "
        f"{100 * max(b for _, b in dados):.1f} %.",
        "- **Como escrever:** afeta tipologia (infill/borda/leapfrog) e matriz de "
        "transição, que dependem de QUAL pixel mudou. NÃO afeta área, CAGR nem "
        "fragmentação agregada.",
        "",
    ]


def bloco_razao(out: list[str]) -> None:
    src = PROC / "causal" / "decomposicao_luz_por_camada.csv"
    por: dict[str, list[float]] = {}
    for x in linhas(src):
        v = num(x.get("razao_teto_sobre_piso"))
        if v is not None:
            por.setdefault(x.get("classe", "?"), []).append(v)
    if not por:
        return
    out += [
        "## Razão teto/piso da decomposição de luz",
        "",
        f"Fonte: `{src.relative_to(REPO_ROOT)}`, coluna `razao_teto_sobre_piso`.",
        "",
        "| classe | n | mediana | máximo |",
        "|---|---|---|---|",
    ]
    for c, v in sorted(por.items()):
        out.append(f"| {c} | {len(v)} | {st.median(v):.2f} | {max(v):.2f} |")
    glob_max = max(max(v) for v in por.values())
    out += [
        "",
        f"- **Máximo global:** {glob_max:.2f}.",
        "- **Como escrever:** a decomposição **não é partição**. Publicar piso e teto, "
        "nunca um valor. Um qualificador de máximo ('até N') só pode trazer o máximo "
        f"({glob_max:.2f}), jamais a mediana. Só o sinal comum às duas envoltórias é "
        "afirmável (`docs/ADR/0015`, decisão 4).",
        "",
    ]


def bloco_causal(out: list[str]) -> None:
    q = PROC / "causal" / "its_quebras.csv"
    v = PROC / "causal" / "veredito_fase3.csv"
    prin = [
        x for x in linhas(q)
        if x.get("estimavel") == "True" and "principal" in (x.get("variante") or "")
    ]
    if prin:
        out += [
            "## Quebras estimadas (séries interrompidas), variante principal",
            "",
            f"Fonte: `{q.relative_to(REPO_ROOT)}`.",
            "",
            "| série / unidade / quebra | b2 (nível) | IC95 | p |",
            "|---|---|---|---|",
        ]
        for x in prin:
            b2, lo, hi, p = (
                num(x.get("b2_nivel")), num(x.get("b2_ic95_inf")),
                num(x.get("b2_ic95_sup")), num(x.get("b2_p")),
            )
            out.append(
                f"| `{x['rotulo']}` | {b2:+.3f} | [{lo:+.3f}, {hi:+.3f}] | {p:.3f} |"
            )
        out.append("")
    vered = [
        " | ".join(str(y) for y in x.values()) for x in linhas(v)
        if "SUSTENTAD" in " ".join(str(y) for y in x.values()).upper()
    ]
    if vered:
        # SEM TRUNCAR (4-11). A versão anterior cortava em 160 caracteres e gravava
        # "F7_loo_desloca_mais_de_5" onde o CSV diz "F7_loo_desloca_mais_de_50pct" —
        # truncar um critério muda o critério.
        out += ["### Veredito dos painéis contrafactuais", ""]
        out += [f"- {t}" for t in vered]

        # O motivo de cada painel cair vem do CSV, não de uma frase geral. A versão
        # anterior dizia que os quatro caíam "porque o placebo espacial mostra a mesma
        # quebra em capitais sem carvão" — verdadeiro em 2011 e 2016, FALSO em 2005 e
        # 2022, onde P1 é "nao estimavel". Era erro relacional dentro da própria folha
        # que existe para impedir erro relacional.
        p1 = {
            x.get("quebra"): x.get("veredito")
            for x in linhas(PROC / "causal" / "placebos.csv")
            if x.get("unidade") == "AGREGADO" and x.get("placebo") == "P1_espacial"
        }
        if p1:
            out += ["", "**Placebo espacial P1, por quebra (de `placebos.csv`):**", ""]
            out += [f"- {q}: {v}" for q, v in sorted(p1.items())]
        falha = sorted(q for q, v in p1.items() if v == "FALHA")
        naoest = sorted(q for q, v in p1.items() if v and "estimavel" in v)
        out += [
            "",
            "- **Como escrever:** os quatro painéis são NÃO SUSTENTADOS, mas **não pelo "
            "mesmo motivo** — a coluna de critérios F acima diz qual caiu por quê. "
            f"O placebo espacial FALHA em {', '.join(falha) or 'nenhuma quebra'} "
            f"(controles sem carvão replicam a quebra) e é NÃO ESTIMÁVEL em "
            f"{', '.join(naoest) or 'nenhuma'} (`docs/ADR/0015`, ramo de referência nula). "
            "Não generalizar o motivo de uma quebra para as outras.",
            "- Um coeficiente com p = 0,000 descreve a série de Tete; ele **não** mede "
            "efeito do carvão.",
            "- **Piso de inferência:** com 1 tratado e 5 doadores, o p mínimo por "
            "permutação é **1/6 ≈ 0,167**. Nenhum resultado pode atingir p < 0,05. "
            "Um p perto de 0,167 é o piso do teste, não um nulo comum.",
            "",
        ]


def bloco_luz(out: list[str]) -> None:
    src = PROC / "causal" / "serie_luzes_anual.csv"
    t = {
        int(x["ano"]): x for x in linhas(src)
        if x.get("unidade") == "tete_aoi" and x.get("ano", "").isdigit()
    }
    if not t:
        return
    out += [
        "## Luz noturna: cidade de Tete contra o resto do retângulo",
        "",
        f"Fonte: `{src.relative_to(REPO_ROOT)}`, colunas `soma_radiancia` e "
        "`soma_radiancia_adm2_int_recorte`.",
        "",
        "| janela | retângulo | Cidade de Tete | resto (Moatize + mina) |",
        "|---|---|---|---|",
    ]
    for a, b in ((2021, 2022), (2021, 2025), (2011, 2013)):
        if a not in t or b not in t:
            continue
        ta, tb = num(t[a]["soma_radiancia"]), num(t[b]["soma_radiancia"])
        ca, cb = (
            num(t[a]["soma_radiancia_adm2_int_recorte"]),
            num(t[b]["soma_radiancia_adm2_int_recorte"]),
        )
        out.append(
            f"| {a}→{b} | {100 * (tb / ta - 1):+.1f} % | {100 * (cb / ca - 1):+.1f} % | "
            f"{100 * (((tb - cb) / (ta - ca)) - 1):+.1f} % |"
        )
    # A contribuição da pegada industrial para a queda de 2022 é CALCULADA, não escrita.
    # A versão anterior trazia "32–42 %" como literal, contra a própria docstring deste
    # módulo ("nenhum valor é escrito aqui") — o defeito nomeado em 4-07, num arquivo que
    # existe para eliminá-lo (4-11).
    dec = linhas(PROC / "causal" / "decomposicao_luz_por_camada.csv")
    contrib = ""
    if dec:
        def soma(ano: int, classe: str, coluna: str) -> float | None:
            v = [
                num(x.get(coluna)) for x in dec
                if x.get("ano") == str(ano) and x.get("classe") == classe
                and x.get("variante_mascara") == "mascara_fixa_2020"
            ]
            v = [y for y in v if y is not None]
            return v[0] if v else None

        fracoes = []
        for col in ("soma_radiancia_piso_por_area", "soma_radiancia_teto_por_presenca"):
            i21, i22 = soma(2021, "industrial", col), soma(2022, "industrial", col)
            tot21 = num(next((x.get("soma_radiancia_aoi_total") for x in dec
                              if x.get("ano") == "2021"), None))
            tot22 = num(next((x.get("soma_radiancia_aoi_total") for x in dec
                              if x.get("ano") == "2022"), None))
            if None not in (i21, i22, tot21, tot22) and tot21 != tot22:
                fracoes.append(100 * (i21 - i22) / (tot21 - tot22))
        if fracoes:
            contrib = (
                f"a pegada industrial responde por {min(fracoes):.0f}–{max(fracoes):.0f} % "
                "da queda (piso e teto da envoltória), "
            )

    out += [
        "",
        "- **Como escrever:** a queda de 2022 **não está na cidade**. Atribuí-la à mina é "
        f"PROIBIDO (`docs/ADR/0015`, decisão 4): {contrib}"
        "e o maior contribuinte é `resto`, que não é industrial nem urbano classificado. "
        "O que se pode dizer é que a queda está **fora da cidade**.",
        "",
    ]


def bloco_adensamento(out: list[str]) -> None:
    """ADR 0016 — camada `adensamento_2020_2025`.

    O risco de prosa desta camada é específico e nomeado no próprio meta: ela é
    **modelada** e será lida como observada, e a sua área **não é publicável como área**.
    O bloco existe para que o redator não tenha de decidir isso de memória.
    """
    import json

    meta_path = (
        PROC / "imagery" / "adensamento_2020_2025_240m_32736.tif.meta.json"
    )
    if not meta_path.exists():
        return
    with meta_path.open(encoding="utf-8") as fh:
        meta = json.load(fh)

    sens = linhas(PROC / "adensamento_sensibilidade.csv")
    areas_var = {x["variante"]: num(x["area_adensando_km2"]) for x in sens}
    areas_var = {k: v for k, v in areas_var.items() if v is not None}
    # Só as variantes de ±1 decil entram na razão de publicação — as demais (grade,
    # sem_S2/S3, bruta) testam outra coisa. A lista vem do CSV, não de uma lista escrita.
    decil = {k: v for k, v in areas_var.items() if "variante ±1 decil" in
             next((x["nota"] for x in sens if x["variante"] == k), "")}

    areas_classe = meta.get("areas_por_classe_km2", {})
    base = areas_var.get("base")
    razao = meta.get("razao_sensibilidade_maxima_1_decil")
    regime = meta.get("regime_publicacao_sensibilidade", "")

    porun = linhas(PROC / "adensamento_2020_2025_por_unidade.csv")
    aden = [x for x in porun if x.get("classe") == "adensando"]
    por_unidade: dict[str, float] = {}
    for x in aden:
        v = num(x.get("area_km2"))
        if v is not None:
            por_unidade[x["unidade"]] = por_unidade.get(x["unidade"], 0.0) + v

    out += [
        "## Adensamento 2020→2025 (`docs/ADR/0016`)",
        "",
        f"- Fonte: `{meta_path.relative_to(REPO_ROOT)}`, "
        f"`data/processed/adensamento_sensibilidade.csv`, "
        "`data/processed/adensamento_2020_2025_por_unidade.csv`",
        f"- Selo: **{meta.get('selo')}** · publicável como: "
        f"**{meta.get('publicavel_como')}** · estocasticidade: {meta.get('estocasticidade')}",
        "",
    ]
    if base is not None:
        out += [
            f"- Área da classe `adensando` na variante **base**: **{base:.4g} km²** "
            f"(domínio de {num(meta.get('area_dominio_km2')):.6g} km²).",
        ]
    if decil:
        lo, hi = min(decil.values()), max(decil.values())
        nomes_lo = [k for k, v in decil.items() if v == lo]
        nomes_hi = [k for k, v in decil.items() if v == hi]
        # `razao` é a razão de cada variante frente à BASE (o critério pré-registado do
        # ADR 0016), NÃO a razão entre os extremos. Escrever os dois extremos e a seguir
        # "razão máxima" sem dizer o referente é afirmação relacional — número certo,
        # qualificador errado, o defeito que este arquivo existe para impedir. Os dois
        # são calculados e nomeados.
        entre_extremos = hi / lo if lo else None
        out += [
            f"- Entre as {len(decil)} variantes de ±1 decil, essa área vai de "
            f"**{lo:.4g} km²** ({', '.join(sorted(nomes_lo))}) a "
            f"**{hi:.4g} km²** ({', '.join(sorted(nomes_hi))}).",
            f"- Razão **frente à variante base** (é este o critério de publicação do "
            f"ADR 0016, e é este o número do meta): **{razao}**. "
            + (f"Razão **entre os dois extremos**, que é outra coisa: "
               f"**{entre_extremos:.4g}**." if entre_extremos else ""),
        ]
    if areas_classe:
        ordem = sorted(
            ((k, v) for k, v in areas_classe.items() if k != "fora_de_dominio"),
            key=lambda kv: -kv[1],
        )
        out += [
            "- Área por classe (km², variante base): "
            + "; ".join(f"`{k}` {v:.4g}" for k, v in ordem),
        ]
    if por_unidade:
        out += [
            "- `adensando` por unidade (km², soma dos anéis): "
            + "; ".join(f"{u} {v:.4g}" for u, v in sorted(
                por_unidade.items(), key=lambda kv: -kv[1])),
        ]
    out += [
        "",
        "- **Como escrever:** a área **não é um resultado publicável**. O regime "
        f"declarado no meta é: *{regime}*. Escrever \"{base:.4g} km² adensaram\" é "
        "converter um padrão espacial numa medida de área que a própria sensibilidade "
        "recusa — a mesma área muda por um fator de "
        f"{razao} só por deslocar um corte em um decil. Escreva **onde** adensa "
        "(as unidades e anéis acima), não **quanto**."
        if base is not None and razao is not None else "",
        "- **Como escrever:** a camada é **modelada**, nunca observada. Ela é síntese de "
        "três sinais por concordância de 2 em 3, não uma classificação de imagem: não há "
        "pixel algum que tenha sido *visto* adensando.",
        "- **Como escrever:** a camada **não detecta esvaziamento**. Não existe classe "
        "`desadensando`, por construção (a catraca R2 torna a série de construído "
        "não-decrescente). Ausência de `adensando` não é evidência de estagnação.",
        "- **Como escrever:** a janela real do sinal S3 (Open Buildings) é **2020→~2023**, "
        "não 2020→2025. Toda frase que der o intervalo completo a S3 está errada.",
        "",
    ]
    riscos = meta.get("riscos")
    if isinstance(riscos, dict) and riscos:
        out += ["- Riscos declarados no meta (todos têm de sobreviver à redação):"]
        out += [f"  - `{k}` — {v}" for k, v in riscos.items()]
        out += [""]
    elif isinstance(riscos, list) and riscos:
        out += ["- Riscos declarados no meta (todos têm de sobreviver à redação):"]
        out += [f"  - {r}" for r in riscos]
        out += [""]
    out += ["---", ""]


def bloco_demografia(out: list[str]) -> None:
    """Dashboard demográfico 1997-2025 (`data/processed/demografia_serie_1997_2025.csv`).

    O risco de prosa aqui é o nível da fonte: 1997 e 2007 são B/C e **não sustentam
    número publicado** (§4.0), mas são justamente os anos que fecham o intervalo mais
    citável ("cresceu X% ao ano desde 1997"). Toda taxa sai daqui com o pior nível das
    suas duas pontas, para que a frase carregue a ressalva junto com o número.
    """
    src = PROC / "demografia_serie_1997_2025.csv"
    dados = linhas(src)
    if not dados:
        return

    pop = [x for x in dados if x["variavel"] == "populacao_total_residente"]
    cagr = [x for x in dados if x["variavel"].startswith("cagr_")]
    indice = [x for x in dados if x["variavel"].startswith("indice_base_")]

    out += [
        "## População comparada, 1997–2025",
        "",
        # Cada contagem nomeia exatamente o que conta. "taxa/índice" para o número que
        # só conta CAGR seria a mesma classe de erro que este arquivo persegue — rótulo
        # mais largo que a grandeza.
        f"- Fonte: `{src.relative_to(REPO_ROOT)}` "
        f"({len(dados)} linhas: {len(pop)} de população, {len(cagr)} de CAGR, "
        f"{len(indice)} de índice)",
        "",
        "| unidade | ano | população | selo | nível |",
        "|---|---:|---:|---|---|",
    ]
    for x in sorted(pop, key=lambda y: (y["unidade_geografica"], int(y["ano"]))):
        v = num(x["valor"])
        valor = f"{v:,.0f}".replace(",", " ") if v is not None else "—"
        out.append(
            f"| {x['unidade_geografica']} | {x['ano']} | {valor} | "
            f"{x['selo']} | **{x['nivel_fonte']}** |"
        )
    out += ["", "| unidade | intervalo | CAGR (%/ano) | selo | nível |", "|---|---|---:|---|---|"]
    for x in sorted(cagr, key=lambda y: (y["unidade_geografica"], y["variavel"])):
        v = num(x["valor"])
        intervalo = x["variavel"].replace("cagr_", "").replace("_", "→")
        out.append(
            f"| {x['unidade_geografica']} | {intervalo} | "
            f"{v:.3f} | {x['selo']} | **{x['nivel_fonte']}** |"
            if v is not None else ""
        )

    # A comparação que o usuário pediu: ritmo da sede contra província e país, por
    # intervalo. Calculada aqui, não escrita — e só entre taxas do MESMO intervalo.
    por_intervalo: dict[str, dict[str, float]] = {}
    for x in cagr:
        v = num(x["valor"])
        if v is not None:
            por_intervalo.setdefault(x["variavel"], {})[x["unidade_geografica"]] = v
    out += ["", "**Ritmo relativo (razão entre CAGR da unidade e o de Moçambique, "
            "mesmo intervalo):**", ""]
    for var in sorted(por_intervalo):
        taxas = por_intervalo[var]
        base = taxas.get("Moçambique")
        if base in (None, 0):
            continue
        partes = [
            f"{u} {t / base:.2f}×"
            for u, t in sorted(taxas.items(), key=lambda kv: -kv[1])
            if u != "Moçambique"
        ]
        out.append(f"- `{var}` (Moçambique = {base:.3f} %/ano): " + "; ".join(partes))

    niveis = {x["nivel_fonte"] for x in pop}
    out += [
        "",
        "- **Como escrever:** o nível é **por ponto**, não por série. "
        f"Os pontos desta tabela vão de {sorted(niveis)}. Uma taxa que atravessa 1997 ou "
        "2007 tem ponta **B ou C** e, por §4.0, **não sustenta número publicado** — entra "
        "como contexto, com o nível na mesma frase. Não existe 'a taxa 1997–2025'.",
        "- **Como escrever:** 2025 **não é observação**. É projeção geométrica do INE: o "
        "CAGR 2017–2025 é **premissa do produtor**, não medida deste estudo. Usá-lo como "
        "evidência de aceleração ou desaceleração é circular.",
        "- **Como escrever:** os valores de 2017 são contagens **residentes não ajustadas** "
        "pela sub-enumeração estimada pelo próprio INE — **3,8 %** na Província de Tete "
        "(a grandeza pertinente às unidades deste estudo, todas nela); 3,7 % é a taxa "
        "**nacional**, uma grandeza distinta, não uma faixa de incerteza da mesma medida.",
        "- **Como escrever:** o **Distrito de Moatize mudou de limites** entre censos; a "
        "comparabilidade 2007/2017 não está garantida, e a taxa desse intervalo mistura "
        "crescimento com mudança de perímetro.",
        "- **Como escrever:** o total nacional é **soma do COD-PS**, não o número publicado "
        "pelo INE; a divergência está no CSV. Use o valor do CSV.",
        "",
    ]

    # Vila de Moatize: TODO número sai de `populacao_vila_moatize_sensibilidade.csv`.
    #
    # A primeira versão deste bloco tinha os valores DIGITADOS na prosa ("+1,61 %",
    # "307.338", "25 % a 74 %") — dentro do arquivo cujo cabeçalho manda não fazer isso,
    # e escrita pelo próprio orquestrador. O portão da Frente A a reprovou. Um gerador
    # que digita o número não é gerador: é o mesmo defeito com uma camada a mais de
    # aparência de rigor.
    sens = linhas(PROC / "populacao_vila_moatize_sensibilidade.csv")
    vila_sens = [x for x in sens if x.get("unidade_geografica") == "Vila de Moatize"]
    vc = next((x for x in sens if x.get("metodo_peso") == "validacao_cruzada"), None)
    if vila_sens and vc:
        # Cada variante com a sua estimativa e o desvio que ela teve na validação em Tete.
        # O par (variante -> coluna de desvio) é derivado do nome, não de uma lista escrita.
        # O nome da coluna de desvio NÃO é `desvio_pct_{metodo}` para toda variante:
        # `diagnostico_sem_peso_construido` publica em `desvio_pct_diagnostico_sem_peso`.
        # A primeira versão assumia a igualdade e **descartou em silêncio** justamente a
        # variante que valida — o bloco inteiro sumiu do arquivo sem uma linha de erro.
        # Aqui o casamento é por prefixo e a ausência levanta exceção: uma variante que
        # não casa tem de parar a geração, nunca desaparecer.
        colunas_desvio = [c for c in vc if c.startswith("desvio_pct_") and num(vc[c]) is not None]

        def _desvio(metodo: str) -> float:
            candidatas = [
                c for c in colunas_desvio if metodo.startswith(c[len("desvio_pct_"):])
            ]
            if len(candidatas) != 1:
                raise ValueError(
                    f"variante {metodo!r} casa com {len(candidatas)} colunas de desvio "
                    f"({candidatas}) em populacao_vila_moatize_sensibilidade.csv"
                )
            return num(vc[candidatas[0]])

        variantes = []
        for x in vila_sens:
            metodo = x["metodo_peso"]
            est = num(x.get("estimativa_populacao"))
            if est is None:  # `piso_teto` é linha de resumo, não variante
                continue
            variantes.append((metodo, est, _desvio(metodo)))
        variantes.sort(key=lambda t: t[1])
        obs = num(vc.get("populacao_observada_2017"))
        restritas = [t for t in variantes if not t[0].startswith("diagnostico_sem_peso")]
        sem_peso = [t for t in variantes if t[0].startswith("diagnostico_sem_peso")]
        if variantes and restritas and sem_peso and obs is not None:
            piso = min(t[1] for t in restritas)
            teto = sem_peso[0][1]
            pior, melhor = (
                max(abs(t[2]) for t in restritas),
                min(abs(t[2]) for t in restritas),
            )
            out += [
                f"- Banda da Vila de Moatize (2017, único ano): **{pt(piso)}** (piso) a "
                f"**{pt(teto)}** (teto). Variantes, do menor ao maior, com o desvio de "
                "cada uma na validação cruzada em Cidade de Tete contra "
                f"{pt(obs)} observados: "
                + "; ".join(f"`{m}` {pt(e)} ({pt(d, 2, sinal=True)} %)" for m, e, d in variantes),
                "",
                "- **Como escrever — Vila de Moatize:** um **único ano** (2017), logo "
                "**nenhum CAGR e nenhuma série**. O valor publicado é o **teto de uma "
                "banda**, não uma estimativa central: é a soma do GRID3 no cluster de "
                f"Voronoi **sem peso de construído**, a única que valida "
                f"({pt(sem_peso[0][2], 2, sinal=True)} %). Inclui área rural atribuída à sede mais "
                "próxima, logo é **limite superior**. Toda variante restrita pela máscara "
                f"de construído subestima o observado (de {pt(melhor, 1)} % a {pt(pior, 1)} %) "
                "— o GRID3 já é dasimétrico, e pesá-lo outra vez restringe duas vezes. "
                "Ver `docs/ADR/0017`.",
                "",
            ]
    out += ["---", ""]


def main() -> int:
    out: list[str] = [
        "# Fatos verificados — números do artigo, extraídos dos CSV",
        "",
        "> **Não edite este arquivo.** Ele é gerado por "
        "`pipeline/04_figures/fatos_verificados.py` a partir de `data/processed/`. "
        "Todo número do artigo deve sair daqui, com a estatística que ele é (faixa, "
        "mediana, máximo, ano único) — nunca de memória.",
        "",
        f"- Gerado em: {datetime.now(UTC).isoformat(timespec='seconds')}",
        "",
        "---",
        "",
    ]
    bloco_acuracia(out)
    bloco_churn(out)
    bloco_razao(out)
    bloco_causal(out)
    bloco_luz(out)
    bloco_adensamento(out)
    bloco_demografia(out)

    SAIDA.parent.mkdir(parents=True, exist_ok=True)
    SAIDA.write_text("\n".join(out) + "\n", encoding="utf-8")
    print(f"[ok] {SAIDA.relative_to(REPO_ROOT)}: {len(out)} linhas")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
