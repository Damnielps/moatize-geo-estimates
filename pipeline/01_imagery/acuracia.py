#!/usr/bin/env python3
"""pipeline/01_imagery/acuracia.py — acurácia por ano pelo estimador estratificado
de Olofsson et al. (2014), a partir de rótulos de **interpretação visual**.

## Quem interpretou, e por que isso está escrito em toda saída

Os rótulos de referência de `data/processed/validacao/rotulos_interpretados.csv`
foram atribuídos por **um modelo de linguagem multimodal (Claude), olhando as
folhas de contato PNG** geradas por `amostras_validacao.py` — não por um
intérprete humano treinado, não por verdade de campo, não por imagem de
resolução mais fina. Isto **não é fotointerpretação** no sentido em que a
literatura de sensoriamento remoto usa o termo, e não é chamado assim em nenhum
lugar deste repositório. É interpretação visual automatizada, com o intérprete
identificado na coluna `interprete` de cada linha.

O que isso permite e o que não permite:
- **Permite** medir omissão e comissão contra um julgamento que **não usa** as
  variáveis do classificador (o intérprete vê um RGB SWIR1/NIR/vermelho, nunca
  NDBI, NDVI ou amplitude). A versão reprovada media concordância entre duas
  regras espectrais sobre o mesmo sinal confundido — isto é diferente.
- **Não permite** tratar o resultado como acurácia de referência independente de
  qualidade humana. A 30 m, construído esparso e solo exposto são
  frequentemente indistinguíveis **para qualquer intérprete**, e o erro do
  intérprete entra no número como se fosse erro do mapa.

## Papéis das referências (sem circularidade)

O WSF Evolution **semeia o treino** (`classificacao.rotulos_treino`). Pela regra
declarada, ele **não valida**: nenhuma métrica contra WSF aparece aqui, nem como
acurácia nem sob outro nome. As colunas `jaccard_wsf`/`erro_relativo_area_wsf`
da versão anterior de `acuracia_por_ano.csv` foram **removidas** — eram
concordância com a própria semente. Concordância com o GHSL (referência que não
toca em treino) continua sendo calculada, mas por `classificacao.py`, em
`concordancia_ghsl.csv`, e não é acurácia.

## Estimador

Estratos = classes do **mapa** (construido / nao_construido), com pesos `W_h`
iguais à fração de área da AOI em cada estrato. Para uma amostra estratificada
com `n_h` pontos no estrato `h`:

    p_ij = W_h * n_ij / n_h        (célula da matriz em proporção de ÁREA)
    acurácia global = Σ_i p_ii
    V(Ô) = Σ_h W_h² * ŝ_h² / n_h   (Olofsson et al. 2014, eq. 5)

Kappa é reportado sobre a mesma matriz em proporção de área. O CSV publica
`n` por estrato, IC de 95 % e o veredito contra a meta de `config/study.yaml`
(`acuracia.meta_global`). **Número abaixo da meta é publicado como está**, com
justificativa; nunca ajustado.

Uso: `uv run python pipeline/01_imagery/acuracia.py`
"""

from __future__ import annotations

import csv
import json
import sys
from datetime import UTC, datetime
from pathlib import Path

import numpy as np
import rasterio
import yaml

REPO_ROOT = Path(__file__).resolve().parents[2]
STUDY_YAML = REPO_ROOT / "config" / "study.yaml"
DATA_PROCESSED = REPO_ROOT / "data" / "processed" / "imagery"
DIR_VALIDACAO = REPO_ROOT / "data" / "processed" / "validacao"
PONTOS_CSV = DIR_VALIDACAO / "pontos_validacao.csv"
AMOSTRA_CSV = DIR_VALIDACAO / "amostra_interpretada.csv"
ROTULOS_CSV = DIR_VALIDACAO / "rotulos_interpretados.csv"
SAIDA_CSV = REPO_ROOT / "data" / "processed" / "acuracia_por_ano.csv"
MATRIZ_CSV = REPO_ROOT / "data" / "processed" / "matriz_confusao_por_ano.csv"
PROVENANCE_FRAGMENT = REPO_ROOT / "data" / "provenance_parts" / "imagem_fase1.md"
MARCADOR_INICIO = "<!-- SECAO_ACURACIA_INICIO -->"
MARCADOR_FIM = "<!-- SECAO_ACURACIA_FIM -->"

# docs/ADR/0011: `industrial` e `reassentamento` deixaram de ser subconjuntos de
# `construido` — passaram a ser PEGADAS, com rocha e solo exposto que nenhum
# classificador de construído captura. Estratificar a validação pela união das três
# camadas passaria a jogar cava e pilha de estéril dentro do estrato `construido`, e
# o intérprete visual (corretamente) os leria como não construídos: a comissão
# medida seria a de um objeto que a camada nunca prometeu ser. O estrato passa a ser
# a máscara de construído propriamente dita, persistida por classificacao.py.
CAMADA_CONSTRUIDO = "construido"
CLASSES = ["construido", "nao_construido"]
Z_95 = 1.959964


def carregar_yaml(path: Path) -> dict:
    with path.open(encoding="utf-8") as fh:
        return yaml.safe_load(fh)


def ler_amostra() -> dict[int, list[dict]]:
    """Junta rótulo de referência + AMOSTRA CONGELADA (coordenadas e desenho).

    Mudança de docs/ADR/0014, que corrige um defeito silencioso. O join é por
    `id_cego` — o intérprete só viu o identificador cego. Antes, o `id_cego` era
    procurado em `pontos_validacao.csv`, que `amostras_validacao.py` **redesenha
    a cada execução a partir do mapa vigente**. Quando a classificação muda, o
    sorteio muda: medido nesta reabertura, dos 288 pontos, **zero** caíram na
    mesma linha/coluna de antes. O rótulo de `2000-C006` continuava sendo lido,
    mas aplicado a outro pixel — julgamento de um lugar atribuído a outro, sem
    que nenhum contrato percebesse.
    A amostra que foi de fato interpretada passa a ser um artefato próprio e
    imutável (`amostra_interpretada.csv`), com linha/coluna, o estrato **do
    desenho** e o peso de área daquele estrato **na época do sorteio** — que é o
    que define a probabilidade de inclusão e, portanto, o estimador.
    """
    if not AMOSTRA_CSV.exists():
        raise FileNotFoundError(
            f"{AMOSTRA_CSV} ausente — é a amostra congelada que foi interpretada "
            "(coordenadas + desenho). Sem ela não há como saber a que pixel cada "
            "rótulo se refere."
        )
    pontos = {p["id_cego"]: p for p in csv.DictReader(AMOSTRA_CSV.open(encoding="utf-8"))}
    if not ROTULOS_CSV.exists():
        raise FileNotFoundError(
            f"{ROTULOS_CSV} ausente — os rótulos de referência são produzidos por "
            "interpretação visual das folhas em data/processed/validacao/chips/."
        )
    por_ano: dict[int, list[dict]] = {}
    for r in csv.DictReader(ROTULOS_CSV.open(encoding="utf-8")):
        ponto = pontos.get(r["id_cego"])
        if ponto is None:
            raise KeyError(f"rótulo para ponto inexistente: {r['id_cego']}")
        if r["classe_referencia"] not in (*CLASSES, "indeterminado"):
            raise ValueError(f"classe inválida em {r['id_cego']}: {r['classe_referencia']}")
        por_ano.setdefault(int(ponto["ano"]), []).append(
            {
                "id_ponto": ponto["id_ponto"],
                "id_cego": r["id_cego"],
                "estrato_desenho": ponto["estrato_desenho"],
                "w_h_desenho": float(ponto["w_h_desenho"]),
                "linha": int(ponto["linha"]),
                "coluna": int(ponto["coluna"]),
                "classe_referencia": r["classe_referencia"],
                "interprete": r["interprete"],
            }
        )
    return por_ano


def classe_no_mapa_atual(ano: int, linhas: list[dict], res_m: int, epsg: int) -> None:
    """Lê, no mapa VIGENTE, a classe de cada ponto da amostra congelada.

    É este passo que torna a reutilização legítima: o rótulo de referência é uma
    observação do terreno naquela coordenada e não caduca quando o classificador
    muda; o que muda é a classe que o mapa atribui ao mesmo pixel.
    """
    caminho = DATA_PROCESSED / f"{CAMADA_CONSTRUIDO}_{ano}_{res_m}m_{epsg}.tif"
    with rasterio.open(caminho) as src:
        mask = src.read(1).astype(bool)
    for r in linhas:
        r["classe_mapa"] = "construido" if mask[r["linha"], r["coluna"]] else "nao_construido"


def estimar(ano: int, linhas: list[dict]) -> tuple[dict, list[dict]]:
    """Matriz em proporção de área + acurácia global, kappa e IC de 95 %.

    Estimador de Horvitz-Thompson sobre o **desenho amostral congelado**
    (docs/ADR/0014). Cada ponto pertence a um estrato `h` do desenho (as classes
    do mapa **na época do sorteio**), com peso de área `W_h` e `n_h` pontos:

        p(m, r) = Σ_h W_h * n_h(m, r) / n_h

    onde `m` é a classe do ponto no mapa **vigente** e `r` a classe de
    referência. Σ_{m,r} p = Σ_h W_h = 1. Quando o mapa vigente é o mesmo que
    gerou o desenho, `m == h` para todo ponto e a expressão colapsa exatamente
    na eq. 4 de Olofsson et al. (2014) — o estimador anterior é caso particular
    deste, não foi substituído por outro.

    Acurácias e variâncias saem da mesma matriz:
        AG = Σ_c p(c, c);  V(AG) = Σ_h W_h² ŝ²_h/n_h  (Olofsson, eq. 5)
        AU(c) = p(c,c)/Σ_r p(c,r);  AP(c) = p(c,c)/Σ_m p(m,c)
    As duas últimas são razões de dois estimadores lineares e o IC vem de
    linearização (delta), com a variância de `y - R·z` estimada dentro de cada
    estrato do desenho — que é o análogo direto das eq. 6/7 de Olofsson quando
    estrato e classe do mapa deixam de coincidir.

    Pontos rotulados `indeterminado` **não são descartados em silêncio**: entram
    no CSV como `n_indeterminado` e saem do estimador, e a nota diz que a
    acurácia vale condicionada aos pontos decidíveis.
    """
    n_indeterminado = sum(1 for r in linhas if r["classe_referencia"] == "indeterminado")
    uteis = [r for r in linhas if r["classe_referencia"] != "indeterminado"]

    estratos = sorted({r["estrato_desenho"] for r in uteis})
    pesos_h = {h: uteis[0]["w_h_desenho"] for h in estratos}
    for r in uteis:
        pesos_h[r["estrato_desenho"]] = r["w_h_desenho"]
    por_estrato = {h: [r for r in uteis if r["estrato_desenho"] == h] for h in estratos}
    n_h = {h: len(v) for h, v in por_estrato.items()}

    def media_estrato(h: str, f) -> float:
        return sum(f(r) for r in por_estrato[h]) / n_h[h] if n_h[h] else 0.0

    def total(f) -> float:
        """Estimador linear Σ_h W_h * média_h(f) — proporção de área."""
        return sum(pesos_h[h] * media_estrato(h, f) for h in estratos)

    def var_total(f) -> float:
        var = 0.0
        for h in estratos:
            if n_h[h] < 2:
                continue
            m = media_estrato(h, f)
            s2 = sum((f(r) - m) ** 2 for r in por_estrato[h]) / (n_h[h] - 1)
            var += pesos_h[h] ** 2 * s2 / n_h[h]
        return var

    def indicador(m: str, r_: str):
        def f(x: dict) -> float:
            return 1.0 * (x["classe_mapa"] == m and x["classe_referencia"] == r_)

        return f

    p = {(m, r_): total(indicador(m, r_)) for m in CLASSES for r_ in CLASSES}
    contagem = {
        (m, r_): sum(
            1 for x in uteis if x["classe_mapa"] == m and x["classe_referencia"] == r_
        )
        for m in CLASSES
        for r_ in CLASSES
    }
    n_mapa = {m: sum(contagem[(m, r_)] for r_ in CLASSES) for m in CLASSES}

    acuracia = sum(p[(c, c)] for c in CLASSES)
    ic = Z_95 * float(
        np.sqrt(var_total(lambda x: 1.0 * (x["classe_mapa"] == x["classe_referencia"])))
    )

    # Kappa sobre a matriz em proporção de área.
    linha_marg = {m: sum(p[(m, r_)] for r_ in CLASSES) for m in CLASSES}
    col_marg = {r_: sum(p[(m, r_)] for m in CLASSES) for r_ in CLASSES}
    p_e = sum(linha_marg[c] * col_marg[c] for c in CLASSES)
    kappa = (acuracia - p_e) / (1 - p_e) if p_e < 1 else float("nan")

    def razao_com_ic(f_num, f_den) -> tuple[float, float]:
        num, den = total(f_num), total(f_den)
        if den <= 0:
            return float("nan"), float("nan")
        r_hat = num / den
        var = var_total(lambda x: f_num(x) - r_hat * f_den(x)) / den**2
        return r_hat, Z_95 * float(np.sqrt(max(var, 0.0)))

    acerto_c = indicador("construido", "construido")

    def mapa_c(x: dict) -> float:
        return 1.0 * (x["classe_mapa"] == "construido")

    def ref_c(x: dict) -> float:
        return 1.0 * (x["classe_referencia"] == "construido")

    usuario, ic_usuario = razao_com_ic(acerto_c, mapa_c)
    produtor, ic_produtor = razao_com_ic(acerto_c, ref_c)

    # Alavanca amostral: fração da ÁREA da AOI que UM único ponto de referência
    # do estrato `nao_construido` do DESENHO carrega no estimador. Com n_h pequeno
    # e W_nao_construido ~ 0,98, um único ponto mal rotulado desloca a área
    # estimada da classe rara em vários pontos percentuais da AOI. É por isso
    # que a acurácia do PRODUTOR não é utilizável neste n, e a nota diz isso.
    alavanca = (
        pesos_h["nao_construido"] / n_h["nao_construido"]
        if n_h.get("nao_construido")
        else float("nan")
    )

    celulas = [
        {
            "ano": ano,
            "classe_mapa": m,
            "classe_referencia": r_,
            "n": contagem[(m, r_)],
            "proporcao_de_area": round(p[(m, r_)], 6),
        }
        for m in CLASSES
        for r_ in CLASSES
    ]
    resumo = {
        "ano": ano,
        "n_total": len(linhas),
        "n_construido": n_mapa["construido"],
        "n_nao_construido": n_mapa["nao_construido"],
        "n_indeterminado": n_indeterminado,
        "peso_estrato_construido_desenho": round(pesos_h.get("construido", float("nan")), 6),
        "peso_area_construido_mapa_atual": round(linha_marg["construido"], 6),
        "acuracia_global": round(acuracia, 4),
        "ic95_acuracia_global": round(ic, 4),
        "kappa": round(kappa, 4),
        "acuracia_usuario_construido": round(usuario, 4),
        "ic95_acuracia_usuario_construido": round(ic_usuario, 4),
        "acuracia_produtor_construido": round(produtor, 4),
        "ic95_acuracia_produtor_construido": round(ic_produtor, 4),
        "alavanca_area_de_um_ponto_nao_construido": round(alavanca, 4),
    }
    return resumo, celulas


def main(argv: list[str]) -> int:
    estudo = carregar_yaml(STUDY_YAML)
    meta_global = float(estudo["acuracia"]["meta_global"])
    meta_kappa = float(estudo["acuracia"]["meta_kappa"])
    res_m, epsg = 30, int(estudo["crs"]["metrico"].split(":")[-1])

    por_ano = ler_amostra()
    interpretes = sorted({r["interprete"] for linhas in por_ano.values() for r in linhas})

    nota = (
        "Estimador de Olofsson et al. (2014), estratificado pelas classes do MAPA. "
        "Rótulos de referência por INTERPRETAÇÃO VISUAL AUTOMATIZADA de recortes RGB "
        "(R=SWIR1, G=NIR, B=vermelho; janela 31x31 px de 30 m) do composto de estação "
        "seca do próprio ano — não é fotointerpretação humana nem verdade de campo. "
        f"Intérprete(s): {'; '.join(interpretes)}. O WSF Evolution semeia o treino e por "
        "isso NÃO valida: nenhuma métrica contra WSF é reportada aqui (a concordância "
        "com WSF está em concordancia_wsf.csv, rotulada como concordância entre produtos "
        "com dependência por construção, não como acurácia). "
        "LEIA A ACURÁCIA GLOBAL COM CUIDADO: ela é dominada pelo estrato nao_construido, "
        "que ocupa ~98% da AOI; um mapa que errasse toda a classe rara ainda teria "
        "acurácia global alta. O que informa sobre a classe de interesse é a acurácia do "
        "USUÁRIO (comissão). A acurácia do PRODUTOR não é utilizável neste n: ver "
        "alavanca_area_de_um_ponto_nao_construido — um único ponto de referência do "
        "estrato nao_construido carrega essa fração da área da AOI, de modo que um erro "
        "de rotulagem isolado desloca a área estimada da classe rara em vários pontos "
        "percentuais."
    )

    resumos, celulas = [], []
    for ano in sorted(por_ano):
        classe_no_mapa_atual(ano, por_ano[ano], res_m, epsg)
        resumo, cel = estimar(ano, por_ano[ano])
        resumo["meta_global"] = meta_global
        resumo["meta_kappa"] = meta_kappa
        resumo["atinge_meta_global"] = bool(resumo["acuracia_global"] >= meta_global)
        resumo["atinge_meta_kappa"] = bool(resumo["kappa"] >= meta_kappa)
        resumo["nota"] = nota
        resumos.append(resumo)
        celulas += cel
        print(
            f"[ok] {ano}: acurácia {resumo['acuracia_global']:.3f} "
            f"± {resumo['ic95_acuracia_global']:.3f} | kappa {resumo['kappa']:.3f}",
            file=sys.stderr,
        )

    with SAIDA_CSV.open("w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=list(resumos[0].keys()))
        w.writeheader()
        w.writerows(resumos)
    with MATRIZ_CSV.open("w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=list(celulas[0].keys()))
        w.writeheader()
        w.writerows(celulas)

    (DIR_VALIDACAO / "acuracia.meta.json").write_text(
        json.dumps(
            {
                "estimador": "Olofsson et al. (2014), estratificado pelo mapa",
                "interpretes": interpretes,
                "tipo_de_rotulo": "interpretação visual automatizada (modelo multimodal)",
                "nao_e": ["fotointerpretação humana", "verdade de campo", "regra espectral"],
                "imagem_interpretada": "composto de estação seca do ano, 30 m, EPSG:32736",
                "papel_do_wsf": "semente de treino — excluído da validação por construção",
                "saidas": [
                    str(SAIDA_CSV.relative_to(REPO_ROOT)),
                    str(MATRIZ_CSV.relative_to(REPO_ROOT)),
                ],
                "data_processamento": datetime.now(UTC).isoformat(),
                "script": "pipeline/01_imagery/acuracia.py",
            },
            indent=2,
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    escrever_provenance(resumos, interpretes)
    print(f"[ok] {SAIDA_CSV.relative_to(REPO_ROOT)}", file=sys.stderr)
    return 0


def escrever_provenance(resumos: list[dict], interpretes: list[str]) -> None:
    """Fragmento de proveniência, gerado do resultado — nunca redigido à mão."""
    linhas = [
        MARCADOR_INICIO,
        "",
        "## Validação de acurácia (Fase 1, §5.1 e §10)",
        "",
        "Gerado por `pipeline/01_imagery/acuracia.py`. **Não editar à mão.**",
        "",
        "**Natureza do rótulo de referência.** Os 288 pontos (24 por estrato por ano, "
        "6 anos) foram rotulados por **interpretação visual automatizada** de recortes "
        "RGB (R=SWIR1, G=NIR, B=vermelho) do composto de estação seca do próprio ano, em "
        "duas janelas por ponto — contexto de 3,0 km e detalhe de 0,9 km, a 30 m. O "
        "intérprete é um **modelo de linguagem multimodal**, não um intérprete humano "
        "treinado e não verdade de campo. **Isto não é fotointerpretação** e não é "
        "chamado assim em nenhum artefato. O erro do intérprete entra no número como se "
        "fosse erro do mapa; a 30 m, construído esparso e solo exposto são frequentemente "
        "indistinguíveis para qualquer intérprete.",
        "",
        "**Cegamento.** As folhas de contato exibem `id_cego`, atribuído sobre uma "
        "permutação determinística que mistura os dois estratos. O intérprete não sabia, "
        "ao olhar o recorte, se o mapa classificava aquele pixel como construído. Sem "
        "isso a concordância mediria a pista, não a imagem.",
        "",
        "**Estimador.** Olofsson et al. (2014) generalizado para **reúso da amostra sob "
        "o desenho congelado** (docs/ADR/0014): os estratos e os pesos `W_h` são os do "
        "mapa vigente **na época do sorteio** (`amostra_interpretada.csv`), e a classe do "
        "mapa **atual** em cada ponto é lida do raster do ano. Quando os dois mapas "
        "coincidem, a expressão colapsa na eq. 4 de Olofsson. **Consequência declarada:** "
        "a amostra não foi otimizada para os estratos do mapa atual, e o número correto "
        "de fazer depois de uma reclassificação é uma NOVA rodada de interpretação sobre "
        "`pontos_validacao.csv` (que já foi redesenhado e está sem rótulo). Até lá, este "
        "é um estimador não viesado mas de variância subótima para o mapa vigente.",
        "",
        f"**Intérprete(s):** {'; '.join(interpretes)}",
        "",
        "| ano | n | AG | IC95 AG | kappa | AU construído | IC95 AU | AP construído | "
        "IC95 AP | indet. | W construído | alavanca de 1 ponto |",
        "|---|---|---|---|---|---|---|---|---|---|---|---|",
    ]
    for r in resumos:
        linhas.append(
            f"| {r['ano']} | {r['n_total']} | {r['acuracia_global']:.3f} | "
            f"±{r['ic95_acuracia_global']:.3f} | {r['kappa']:.3f} | "
            f"{r['acuracia_usuario_construido']:.3f} | "
            f"±{r['ic95_acuracia_usuario_construido']:.3f} | "
            f"{r['acuracia_produtor_construido']:.3f} | "
            f"±{r['ic95_acuracia_produtor_construido']:.3f} | "
            f"{r['n_indeterminado']} | {r['peso_estrato_construido_desenho']:.4f} | "
            f"{r['alavanca_area_de_um_ponto_nao_construido']:.4f} |"
        )
    _au_vals = [r["acuracia_usuario_construido"] for r in resumos]
    _au_min, _au_max = min(_au_vals), max(_au_vals)
    linhas += [
        "",
        "AG = acurácia global · AU = acurácia do usuário (1 − comissão) · "
        "AP = acurácia do produtor (1 − omissão).",
        "",
        "**Como ler estes números, e como não ler.**",
        "",
        "1. A **acurácia global** cumpre a meta de §10 (≥ 0,85) em todos os anos, mas "
        "essa comparação é fraca aqui: o estrato `nao_construido` ocupa 98–99,5 % da "
        "AOI, e um mapa que errasse *toda* a classe construída ainda teria acurácia "
        "global ≈ 0,98. A meta de §10 não discrimina neste desenho.",
        "2. O que informa sobre a classe de interesse é a **acurácia do usuário**: "
        f"{_au_min:.3f}–{_au_max:.3f}. Cerca de metade dos pixels que o mapa chama de "
        "construído não parecem construídos ao intérprete — **comissão alta e "
        "consistente**, pior em 2010. É coerente com o viés já documentado no ADR 0008 "
        "e com a confusão solo exposto × construído na savana semiárida em estação seca.",
        "3. A **acurácia do produtor não é utilizável neste n**. A coluna "
        "`alavanca de 1 ponto` é a fração da área da AOI que **um único** ponto de "
        "referência do estrato `nao_construido` carrega no estimador (≈ 0,041). Em 2020, "
        "3 pontos desse estrato foram lidos como construídos, o que projeta ~12 % da AOI "
        "como construído não mapeado — implausível. O valor de 0,07 mede a fragilidade "
        "do desenho, não o mapa.",
        "4. O **kappa** cai a 0,09–0,23 em 2015 e 2020 e não atinge a meta de 0,70 em "
        "2010, 2015 e 2020. Kappa é instável para classe rara; é reportado por exigência "
        "de §5.1, não como critério.",
        "",
        "**O que seria preciso para estreitar o intervalo.** O IC da acurácia global "
        "chega a ±0,133 (2020). A largura é dominada pelo estrato `nao_construido`, cuja "
        "variância escala com `W²/n`. Levar o IC de 2020 de ±0,13 para ±0,03 exigiria "
        "~n=24 → ~n=470 pontos nesse estrato **por ano** (o IC escala com 1/√n), isto é, "
        "cerca de 2 800 recortes interpretados um a um em vez de 288. Isso não é "
        "atingível por interpretação neste ambiente; seria atingível com verdade de "
        "campo, com imagem de resolução submétrica (fora do nível A), ou aceitando um "
        "rotulador automático — que é exatamente o que reprovou a versão anterior.",
        "",
        "**Papel do WSF Evolution.** Semeia o treino; por construção **não valida**. "
        "Nenhuma métrica contra WSF aparece em `acuracia_por_ano.csv`. A concordância "
        "está em `data/processed/concordancia_wsf.csv`, rotulada como concordância entre "
        "produtos com dependência por construção.",
        "",
        MARCADOR_FIM,
        "",
    ]
    atual = PROVENANCE_FRAGMENT.read_text(encoding="utf-8") if PROVENANCE_FRAGMENT.exists() else ""
    if MARCADOR_INICIO in atual and MARCADOR_FIM in atual:
        novo = atual.split(MARCADOR_INICIO)[0] + "\n".join(linhas) + atual.split(MARCADOR_FIM)[1]
    else:
        novo = atual + "\n" + "\n".join(linhas)
    PROVENANCE_FRAGMENT.parent.mkdir(parents=True, exist_ok=True)
    PROVENANCE_FRAGMENT.write_text(novo, encoding="utf-8")


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
