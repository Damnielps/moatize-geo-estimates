#!/usr/bin/env python3
"""pipeline/01_imagery/acuracia_cultivo.py — acurácia por classe de `cultivo_sequeiro`
e `cultivo_irrigado` (§5.6.1, §10, ADR 0009 estendido a uma classe nova).

Mesmo estimador de `acuracia.py` (Olofsson et al. 2014, estratificado pelo MAPA), com
três estratos em vez de dois: `cultivo_sequeiro`, `cultivo_irrigado`, `outro`. Rótulos
de referência: interpretação visual automatizada (o mesmo tipo de intérprete de
ADR 0007 — um modelo de linguagem multimodal, não verdade de campo), de
`data/processed/validacao/rotulos_interpretados_cultivo.csv`.

**n pequeno e de um único ano** (ver `amostras_validacao_cultivo.py`): 12 pontos por
estrato, só 2020. §10 pede acurácia "por ano"; aqui isso não é atingível dentro do
orçamento desta entrega, e o CSV de saída diz isso explicitamente em vez de estender o
número de 2020 aos outros cinco anos-âncora.

Uso: `uv run python pipeline/01_imagery/acuracia_cultivo.py`
"""

from __future__ import annotations

import csv
import json
import sys
from datetime import UTC, datetime
from pathlib import Path

import numpy as np
import rasterio

REPO_ROOT = Path(__file__).resolve().parents[2]
DATA_PROCESSED = REPO_ROOT / "data" / "processed" / "imagery"
DIR_VALIDACAO = REPO_ROOT / "data" / "processed" / "validacao"
PONTOS_CSV = DIR_VALIDACAO / "pontos_validacao_cultivo.csv"
ROTULOS_CSV = DIR_VALIDACAO / "rotulos_interpretados_cultivo.csv"
SAIDA_CSV = REPO_ROOT / "data" / "processed" / "acuracia_cultivo_por_ano.csv"
PROVENANCE_FRAGMENT = REPO_ROOT / "data" / "provenance_parts" / "agricultura_fase2b.md"
MARCADOR_INICIO = "<!-- SECAO_ACURACIA_CULTIVO_INICIO -->"
MARCADOR_FIM = "<!-- SECAO_ACURACIA_CULTIVO_FIM -->"

CLASSES = ["cultivo_sequeiro", "cultivo_irrigado", "outro"]
CLASSES_DE_INTERESSE = ["cultivo_sequeiro", "cultivo_irrigado"]
RES_M, EPSG = 30, 32736
Z_95 = 1.959964


def pesos_dos_estratos(ano: int) -> dict[str, float]:
    def ler(nome):
        with rasterio.open(DATA_PROCESSED / f"{nome}_{ano}_{RES_M}m_{EPSG}.tif") as src:
            return src.read(1).astype(bool)

    seq = ler("cultivo_sequeiro")
    irr = ler("cultivo_irrigado")
    total = float(seq.size)
    w_seq = float(seq.sum()) / total
    w_irr = float(irr.sum()) / total
    return {"cultivo_sequeiro": w_seq, "cultivo_irrigado": w_irr, "outro": 1.0 - w_seq - w_irr}


def ler_amostra() -> tuple[int, list[dict]]:
    pontos = {p["id_cego"]: p for p in csv.DictReader(PONTOS_CSV.open(encoding="utf-8"))}
    if not ROTULOS_CSV.exists():
        raise FileNotFoundError(f"{ROTULOS_CSV} ausente")
    linhas = []
    for r in csv.DictReader(ROTULOS_CSV.open(encoding="utf-8")):
        ponto = pontos.get(r["id_cego"])
        if ponto is None:
            raise KeyError(f"rótulo para ponto inexistente: {r['id_cego']}")
        if r["classe_referencia"] not in (*CLASSES, "indeterminado"):
            raise ValueError(f"classe inválida em {r['id_cego']}: {r['classe_referencia']}")
        linhas.append(
            {
                "id_ponto": ponto["id_ponto"],
                "estrato_mapeado": ponto["estrato_mapeado"],
                "classe_referencia": r["classe_referencia"],
                "interprete": r["interprete"],
            }
        )
    anos = {int(p["ano"]) for p in pontos.values()}
    if len(anos) != 1:
        raise RuntimeError(f"amostra de cultivo esperada num único ano; achou {anos}")
    return anos.pop(), linhas


def estimar(linhas: list[dict], pesos: dict[str, float]) -> tuple[dict, list[dict]]:
    n_indeterminado = sum(1 for r in linhas if r["classe_referencia"] == "indeterminado")
    uteis = [r for r in linhas if r["classe_referencia"] != "indeterminado"]

    contagem = {(h, i): 0 for h in CLASSES for i in CLASSES}
    n_h = dict.fromkeys(CLASSES, 0)
    for r in uteis:
        h = r["estrato_mapeado"]
        contagem[(h, r["classe_referencia"])] += 1
        n_h[h] += 1

    p = {(h, i): (pesos[h] * contagem[(h, i)] / n_h[h] if n_h[h] else 0.0)
         for h in CLASSES for i in CLASSES}
    acuracia_global = sum(p[(h, h)] for h in CLASSES)

    var = 0.0
    for h in CLASSES:
        if n_h[h] < 2:
            continue
        acerto_h = contagem[(h, h)] / n_h[h]
        var += pesos[h] ** 2 * acerto_h * (1 - acerto_h) / (n_h[h] - 1)
    ic_global = Z_95 * float(np.sqrt(var))

    linha_marg = {h: sum(p[(h, i)] for i in CLASSES) for h in CLASSES}
    col_marg = {i: sum(p[(h, i)] for h in CLASSES) for i in CLASSES}
    p_e = sum(linha_marg[c] * col_marg[c] for c in CLASSES)
    kappa = (acuracia_global - p_e) / (1 - p_e) if p_e < 1 else float("nan")

    por_classe = {}
    for c in CLASSES_DE_INTERESSE:
        n_mapeado = n_h[c]
        usuario = contagem[(c, c)] / n_mapeado if n_mapeado else float("nan")
        ic_usuario = (
            Z_95 * float(np.sqrt(usuario * (1 - usuario) / (n_mapeado - 1)))
            if n_mapeado > 1 else float("nan")
        )
        denom_prod = sum(p[(h, c)] for h in CLASSES)
        produtor = p[(c, c)] / denom_prod if denom_prod else float("nan")

        # n por estrato é pequeno (12) em TODOS os estratos aqui — não só no majoritário
        # como em acuracia.py. O produtor não é reportado como estimativa utilizável;
        # ver `alavanca` e a nota.
        alavancas = {
            h: (pesos[h] / n_h[h] if n_h[h] else float("nan"))
            for h in CLASSES if h != c
        }
        maior_alavanca = max(alavancas.values()) if alavancas else float("nan")
        produtor_estimavel = n_mapeado > 1 and all(n_h[h] >= 8 for h in CLASSES)

        por_classe[c] = {
            f"prevalencia_mapa_{c}": round(pesos[c], 6),
            f"n_mapeado_{c}": n_mapeado,
            f"acuracia_usuario_{c}": round(usuario, 4) if np.isfinite(usuario) else None,
            f"ic95_usuario_{c}": round(ic_usuario, 4) if np.isfinite(ic_usuario) else None,
            f"acuracia_produtor_{c}": round(produtor, 4) if np.isfinite(produtor) else None,
            f"produtor_estimavel_{c}": produtor_estimavel,
            f"alavanca_maxima_1_ponto_{c}": round(maior_alavanca, 4)
            if np.isfinite(maior_alavanca) else None,
        }

    resumo = {
        "n_total": len(linhas),
        "n_indeterminado": n_indeterminado,
        **{f"n_{c}": n_h[c] for c in CLASSES},
        "acuracia_global": round(acuracia_global, 4),
        "ic95_acuracia_global": round(ic_global, 4),
        "kappa": round(kappa, 4),
    }
    for c in CLASSES_DE_INTERESSE:
        resumo.update(por_classe[c])

    celulas = [
        {"estrato_mapeado": h, "classe_referencia": i, "n": contagem[(h, i)],
         "proporcao_de_area": round(p[(h, i)], 6)}
        for h in CLASSES for i in CLASSES
    ]
    return resumo, celulas


def main(argv: list[str]) -> int:
    ano, linhas = ler_amostra()
    pesos = pesos_dos_estratos(ano)
    resumo, celulas = estimar(linhas, pesos)
    resumo = {"ano": ano, **resumo}
    interpretes = sorted({r["interprete"] for r in linhas})

    nota = (
        "n=12/estrato, ANO ÚNICO (2020) — ver amostras_validacao_cultivo.py para o "
        "motivo do desenho reduzido em relação a acuracia.py (construído: 24/estrato, "
        "6 anos). NÃO generalizar este número aos outros 5 anos-âncora. Rótulos por "
        "interpretação visual automatizada (mesmo tipo de intérprete de ADR 0007), não "
        "verdade de campo. Produtor não é confiável quando produtor_estimavel_* é "
        "False — ver alavanca_maxima_1_ponto_*: fração da área da AOI que UM ponto do "
        "estrato de maior peso entre os outros dois carrega no estimador."
    )
    resumo["nota"] = nota

    SAIDA_CSV.parent.mkdir(parents=True, exist_ok=True)
    with SAIDA_CSV.open("w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=list(resumo.keys()))
        w.writeheader()
        w.writerow(resumo)

    matriz_csv = REPO_ROOT / "data" / "processed" / "matriz_confusao_cultivo.csv"
    with matriz_csv.open("w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=list(celulas[0].keys()))
        w.writeheader()
        w.writerows(celulas)

    (DIR_VALIDACAO / "acuracia_cultivo.meta.json").write_text(
        json.dumps(
            {
                "ano_unico": ano,
                "estimador": "Olofsson et al. (2014), estratificado pelo mapa, 3 estratos",
                "interpretes": interpretes,
                "n_por_estrato": 12,
                "saidas": [
                    str(SAIDA_CSV.relative_to(REPO_ROOT)),
                    str(matriz_csv.relative_to(REPO_ROOT)),
                ],
                "data_processamento": datetime.now(UTC).isoformat(),
                "script": "pipeline/01_imagery/acuracia_cultivo.py",
            },
            indent=2, ensure_ascii=False,
        ),
        encoding="utf-8",
    )

    escrever_proveniencia(resumo, interpretes)
    print(
        f"[ok] {ano}: acurácia global {resumo['acuracia_global']:.3f} · kappa "
        f"{resumo['kappa']:.3f} · AU sequeiro "
        f"{resumo.get('acuracia_usuario_cultivo_sequeiro')} · AU irrigado "
        f"{resumo.get('acuracia_usuario_cultivo_irrigado')}",
        file=sys.stderr,
    )
    return 0


def escrever_proveniencia(resumo: dict, interpretes: list[str]) -> None:
    linhas = [
        MARCADOR_INICIO,
        "",
        "## Acurácia por classe — cultivo (§5.6.1, §10)",
        "",
        "Gerado por `pipeline/01_imagery/acuracia_cultivo.py`. **Não editar à mão.**",
        "",
        f"**Ano validado:** {resumo['ano']} (único — ver `amostras_validacao_cultivo.py`). "
        f"**Intérprete(s):** {'; '.join(interpretes)}.",
        "",
        "| classe | prevalência no mapa | n | AU | IC95 AU | AP | AP estimável? |",
        "|---|---|---|---|---|---|---|",
        f"| cultivo_sequeiro | {resumo['prevalencia_mapa_cultivo_sequeiro']:.4f} | "
        f"{resumo['n_mapeado_cultivo_sequeiro']} | "
        f"{resumo['acuracia_usuario_cultivo_sequeiro']} | "
        f"{resumo['ic95_usuario_cultivo_sequeiro']} | "
        f"{resumo['acuracia_produtor_cultivo_sequeiro']} | "
        f"{resumo['produtor_estimavel_cultivo_sequeiro']} |",
        f"| cultivo_irrigado | {resumo['prevalencia_mapa_cultivo_irrigado']:.4f} | "
        f"{resumo['n_mapeado_cultivo_irrigado']} | "
        f"{resumo['acuracia_usuario_cultivo_irrigado']} | "
        f"{resumo['ic95_usuario_cultivo_irrigado']} | "
        f"{resumo['acuracia_produtor_cultivo_irrigado']} | "
        f"{resumo['produtor_estimavel_cultivo_irrigado']} |",
        "",
        f"**Acurácia global:** {resumo['acuracia_global']:.3f} "
        f"± {resumo['ic95_acuracia_global']:.3f} "
        f"· **kappa:** {resumo['kappa']:.3f} "
        f"· **n indeterminado:** {resumo['n_indeterminado']} de {resumo['n_total']}.",
        "",
        "AU = acurácia do usuário (1 − comissão) · AP = acurácia do produtor (1 − omissão).",
        "",
        resumo["nota"],
        "",
        "**Referência externa:** GLAD Cropland / ESA WorldCover / Dynamic World não "
        "estavam espelhados em `data/raw/` no momento desta execução (Fase 0' registrou "
        "URLs quebradas). Esta validação é só interna (interpretação visual); nenhuma "
        "métrica contra produto externo de cobertura de cultivo é reportada. Se os "
        "arquivos aparecerem depois, a validação externa é trabalho futuro — não "
        "duplicado aqui.",
        "",
        MARCADOR_FIM,
        "",
    ]
    atual = PROVENANCE_FRAGMENT.read_text(encoding="utf-8") if PROVENANCE_FRAGMENT.exists() else (
        "# Proveniência — Fase 2b: agricultura e várzea (§5.6)\n\n"
    )
    if MARCADOR_INICIO in atual and MARCADOR_FIM in atual:
        novo = atual.split(MARCADOR_INICIO)[0] + "\n".join(linhas) + atual.split(MARCADOR_FIM)[1]
    else:
        novo = atual + "\n" + "\n".join(linhas)
    PROVENANCE_FRAGMENT.parent.mkdir(parents=True, exist_ok=True)
    PROVENANCE_FRAGMENT.write_text(novo, encoding="utf-8")


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
