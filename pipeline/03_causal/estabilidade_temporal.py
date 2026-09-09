#!/usr/bin/env python3
"""pipeline/03_causal/estabilidade_temporal.py — a série de `urbano` é cidade ou catraca?

## Por que este script existe (Fase 2b, diagnóstico — §5.4)

`docs/ADR/0012` reprovou `cultivo_sequeiro` porque as classes de cobertura oscilam
de forma fisicamente impossível entre anos-âncora (vegetação 10,6 % → 89,0 % → 6,1 %
da AOI). A pergunta que resta antes de abrir a Fase 3 é se a mesma instabilidade
contamina a camada `urbano`, da qual todo o desenho causal de §5.4 depende.

A série publicada de `urbano` é **monotônica por construção**, não por evidência: a
regra R2 de `pipeline/01_imagery/classificacao.py` faz
`construido(t) = ∪_{t'≤t} construido_R1(t')`. Suavidade imposta por união cumulativa
sobre sinal ruidoso é indistinguível, à vista, de suavidade emergente. A única forma
de separar as duas é abrir a série **antes** das regras temporais — isto é, comparar
o estoque publicado (pós-R2) com a detecção bruta do Random Forest ano a ano.

**Este script NÃO reclassifica nada.** Ele regenera, de forma determinística e com as
mesmas seeds de `config/seeds.yaml`, os produtos intermediários que
`classificacao.py` calcula em memória e **não persiste** (o rótulo de 4 classes do RF
e a máscara bruta de construído). Nenhum artefato de `data/processed/` é reescrito.
Os intermediários saem em `data/interim/estabilidade/`, marcados como experimentais.

## O que é medido

1. **Decomposição do estoque publicado (item 1).** Para cada ano t:
   - `sustentada` = pixels de R2(t) que o RF **também** detecta em t;
   - `herdada`    = pixels de R2(t) que o RF **não** detecta em t e que só estão lá
     pela união com anos anteriores.
   Se a fração herdada crescer ao longo da série, a curva de crescimento é artefato
   da regra, não da cidade. Reporta-se também o incremento ΔR2 ao lado de Δbruta: o
   incremento de R2 é, **por construção**, formado só por primeiras detecções
   confirmadas (R1) — logo a pergunta "quanto do crescimento é detecção nova" só tem
   conteúdo quando comparada à variação do sinal bruto no mesmo intervalo.

2. **Instabilidade comparada entre camadas (item 2).** Sobre o rótulo **bruto** do RF
   (antes de R1, R2 e das pegadas de `docs/ADR/0011`), para cada par de anos
   consecutivos e cada classe espectral: Jaccard, churn (diferença simétrica / união),
   taxa de perda e taxa de ganho. `construido` é comparado a `vegetacao` e
   `solo_exposto` no mesmo denominador e com o mesmo estimador.

3. **A queda de 2015→2020 (item 4).** Distribuição de classes, em 2020, dos pixels
   que o RF chamava de construído em 2015 e deixou de chamar em 2020 — para dizer se
   o construído "perdido" virou vegetação, solo ou água. Cruzado com a mediana de
   NDVI(seca) e de NDVI(chuva) da paisagem de cada ano. O corte de rótulo de
   `vegetacao` em `rotulos_treino()` ERA ABSOLUTO (NDVI(seca) >= 0,30) e a mediana da
   paisagem percorre 0,204-0,409 entre os anos-âncora: o corte atravessava a própria
   distribuição, e era isso que movia o prior de treino de `solo_exposto` — a classe
   concorrente de `construido` — em uma ordem de grandeza entre anos. **Corrigido em
   docs/ADR/0014**: o corte passou a ser razão à mediana da paisagem do próprio ano.
   Este script continua reportando a fração acima do corte absoluto histórico, que é
   o quarto placebo exigido por docs/ADR/0013, ao lado da fração vigente.

Uso: `uv run python pipeline/03_causal/estabilidade_temporal.py`
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
sys.path.insert(0, str(REPO_ROOT / "pipeline" / "01_imagery"))

import classificacao as clf  # noqa: E402

DATA_INTERIM = REPO_ROOT / "data" / "interim" / "estabilidade"
DATA_CAUSAL = REPO_ROOT / "data" / "processed" / "causal"
CSV_DECOMPOSICAO = DATA_CAUSAL / "decomposicao_permanencia_urbano.csv"
CSV_ESTABILIDADE = DATA_CAUSAL / "estabilidade_temporal_camadas.csv"
META_JSON = DATA_CAUSAL / "estabilidade_temporal.meta.json"

# Corte absoluto que vigorava até docs/ADR/0013 e foi substituído em
# docs/ADR/0014. Fica aqui, e não em classificacao.py, porque não é mais um
# parâmetro do pipeline: é a série de diagnóstico do quarto placebo (fração da
# AOI acima de um corte fixo de NDVI de seca — radiometria de paisagem, sem
# relação com o carvão).
LIMIAR_VEGETACAO_ABSOLUTO_HISTORICO = 0.30

NOTA_EXPERIMENTAL = (
    "EXPERIMENTAL — regeneração determinística dos intermediários do RF que "
    "classificacao.py não persiste. Não substitui nenhum artefato publicado."
)


def area_km2(mask: np.ndarray, transform) -> float:
    return float(mask.sum()) * abs(transform.a * transform.e) / 1e6


def salvar_interim(mask: np.ndarray, nome: str, crs, transform) -> None:
    DATA_INTERIM.mkdir(parents=True, exist_ok=True)
    clf.salvar_raster(mask, DATA_INTERIM / nome, crs, transform)


def regenerar_brutas(anos: list[int]) -> dict:
    """Reexecuta o passo 1 de classificacao.main (RF por ano), sem R1/R2.

    Determinístico: mesmas seeds, mesmas features, mesmo pool de treino. As
    máscaras devolvidas aqui são bit-idênticas às que classificacao.py usa em
    memória antes de `aplicar_regras_temporais`.
    """
    estudo = clf.carregar_estudo(clf.STUDY_YAML)
    seeds_cfg = clf.carregar_yaml(clf.SEEDS_YAML)
    disponiveis = clf.compostos_disponiveis()
    m0 = clf.NOME_ARQUIVO_RE.match(disponiveis[anos[0]].name)
    res_m, epsg = int(m0.group(2)), int(m0.group(3))

    rotulos: dict[int, np.ndarray] = {}
    brutas: dict[int, np.ndarray] = {}
    ndvi_chuva_mediana: dict[int, float] = {}
    radiometria: dict[int, dict] = {}
    prior_treino: dict[int, dict] = {}
    perfil_ref = None
    wsf = None
    mask_excluir_negativos = None

    for ano in anos:
        f = clf.carregar_features_ano(ano, res_m, epsg)
        if perfil_ref is None:
            perfil_ref = f["perfil"]
            crs = str(perfil_ref["crs"])
            poligono = clf.carregar_poligono_mineracao(crs)
            buffers, _ = clf.carregar_buffers_reassentamento(crs)
            clf.conferir_grade_contra_config(perfil_ref, estudo)
            wsf = clf.carregar_wsf_reprojetado(perfil_ref)
            mask_excluir_negativos = clf.rasterizar(poligono, perfil_ref)
            for item in buffers:
                mask_excluir_negativos |= clf.rasterizar(
                    item["ponto"].buffer(clf.RAIO_EXCLUSAO_NEGATIVO_REASSENTAMENTO_M),
                    perfil_ref,
                )
        rotulo, bruta, info = clf.classificar_ano(
            ano, f, wsf, mask_excluir_negativos, res_m, seeds_cfg
        )
        rotulos[ano] = rotulo
        brutas[ano] = bruta
        ndvi_chuva = f["indices"]["ndvi_chuva"]
        finito = np.isfinite(ndvi_chuva) & f["mask_valida"]
        ndvi_chuva_mediana[ano] = float(np.median(ndvi_chuva[finito]))
        # Radiometria da paisagem. Até docs/ADR/0013 era ela que movia o rótulo de
        # treino, porque o corte de `vegetacao` em rotulos_treino() era ABSOLUTO
        # (0,30). docs/ADR/0014 trocou o corte pela razão à mediana do ano. As duas
        # frações continuam publicadas lado a lado: a do corte absoluto histórico
        # (que é o QUARTO PLACEBO exigido por docs/ADR/0013 — radiometria de paisagem,
        # sem relação com o carvão) e a do corte relativo vigente.
        ndvi_seca = f["indices"]["ndvi"]
        fin_seca = np.isfinite(ndvi_seca) & f["mask_valida"]
        med_seca = float(np.median(ndvi_seca[fin_seca]))
        radiometria[ano] = {
            "mediana_ndvi_seca_paisagem": round(med_seca, 4),
            "mediana_ndvi_chuva_paisagem": round(ndvi_chuva_mediana[ano], 4),
            "fracao_aoi_acima_do_limiar_absoluto_historico": round(
                float((ndvi_seca[fin_seca] >= LIMIAR_VEGETACAO_ABSOLUTO_HISTORICO).mean()), 4
            ),
            "limiar_vegetacao_ndvi_seca_absoluto_historico": (
                LIMIAR_VEGETACAO_ABSOLUTO_HISTORICO
            ),
            "fracao_aoi_acima_do_limiar_relativo_vigente": round(
                float(
                    (ndvi_seca[fin_seca] >= clf.RAZAO_VERDE_VEGETACAO * med_seca).mean()
                ),
                4,
            ),
            "razao_verde_vegetacao_vigente": clf.RAZAO_VERDE_VEGETACAO,
            "limiar_vegetacao_ndvi_seca_do_ano": round(
                clf.RAZAO_VERDE_VEGETACAO * med_seca, 4
            ),
        }
        prior_treino[ano] = {
            "n_disponivel_por_classe": info["n_disponivel_por_classe"],
            "n_amostrado_por_classe": info["n_amostrado_por_classe"],
            "importancia_ndvi_seca": round(info["importancia_features"]["ndvi"], 4),
            "importancia_ndvi_amplitude": round(
                info["importancia_features"]["ndvi_amplitude"], 4
            ),
        }
        salvar_interim(
            bruta,
            f"bruta_construido_{ano}_{res_m}m_{epsg}.tif",
            crs,
            perfil_ref["transform"],
        )
        print(
            f"[rf ] {ano}: bruto = {area_km2(bruta, perfil_ref['transform']):.3f} km²",
            file=sys.stderr,
        )
    return {
        "rotulos": rotulos,
        "brutas": brutas,
        "perfil": perfil_ref,
        "res_m": res_m,
        "epsg": epsg,
        "ndvi_chuva_mediana": ndvi_chuva_mediana,
        "radiometria": radiometria,
        "prior_treino": prior_treino,
    }


def carregar_publicado(anos: list[int], res_m: int, epsg: int) -> dict[int, np.ndarray]:
    """`construido_<ano>` publicado = série pós-R2 (o estoque que a Fase 3 usaria)."""
    out = {}
    for ano in anos:
        caminho = clf.DATA_PROCESSED / f"construido_{ano}_{res_m}m_{epsg}.tif"
        with rasterio.open(caminho) as src:
            out[ano] = src.read(1).astype(bool)
    return out


def carregar_urbano(anos: list[int], res_m: int, epsg: int) -> dict[int, np.ndarray]:
    out = {}
    for ano in anos:
        caminho = clf.DATA_PROCESSED / f"urbano_{ano}_{res_m}m_{epsg}.tif"
        with rasterio.open(caminho) as src:
            out[ano] = src.read(1).astype(bool)
    return out


def decompor(anos, brutas, apos_r1, r2, urbano, transform) -> list[dict]:
    linhas = []
    for i, ano in enumerate(anos):
        a = area_km2
        sustentada = r2[ano] & brutas[ano]
        herdada = r2[ano] & ~brutas[ano]
        rejeitada_r1 = brutas[ano] & ~r2[ano]
        area_r2 = a(r2[ano], transform)
        linha = {
            "ano": ano,
            "area_bruta_rf_km2": round(a(brutas[ano], transform), 3),
            "area_apos_r1_km2": round(a(apos_r1[ano], transform), 3),
            "area_apos_r2_km2": round(area_r2, 3),
            "area_urbano_publicado_km2": round(a(urbano[ano], transform), 3),
            "estoque_sustentado_pelo_ano_km2": round(a(sustentada, transform), 3),
            "estoque_herdado_da_uniao_km2": round(a(herdada, transform), 3),
            "fracao_estoque_herdada": round(a(herdada, transform) / area_r2, 4)
            if area_r2 > 0
            else 0.0,
            "deteccao_do_ano_rejeitada_por_r1_km2": round(a(rejeitada_r1, transform), 3),
        }
        if i == 0:
            linha |= {
                "delta_r2_km2": "",
                "delta_bruta_km2": "",
                "delta_estoque_herdado_km2": "",
                "razao_delta_r2_sobre_delta_bruta": "",
            }
        else:
            ant = anos[i - 1]
            d_r2 = area_r2 - a(r2[ant], transform)
            d_bruta = a(brutas[ano], transform) - a(brutas[ant], transform)
            d_herdado = a(herdada, transform) - a(r2[ant] & ~brutas[ant], transform)
            linha |= {
                "delta_r2_km2": round(d_r2, 3),
                "delta_bruta_km2": round(d_bruta, 3),
                "delta_estoque_herdado_km2": round(d_herdado, 3),
                "razao_delta_r2_sobre_delta_bruta": round(d_r2 / d_bruta, 3)
                if abs(d_bruta) > 1e-9
                else "indefinida (delta bruto ~ 0)",
            }
        linhas.append(linha)
    return linhas


def estabilidade(anos, rotulos, brutas, mask_valida_por_ano, transform) -> list[dict]:
    """Instabilidade ano a ano das classes espectrais BRUTAS (antes de R1/R2)."""
    linhas = []
    for i in range(len(anos) - 1):
        t, u = anos[i], anos[i + 1]
        comum = mask_valida_por_ano[t] & mask_valida_por_ano[u]
        for nome, cod in clf.CODIGO_CLASSE.items():
            if nome == "construido":
                a_t = brutas[t] & comum
                a_u = brutas[u] & comum
                fonte = "RF bruto + filtro de coerencia 3x3 (antes de R1/R2)"
            else:
                a_t = (rotulos[t] == cod) & comum
                a_u = (rotulos[u] == cod) & comum
                fonte = "rotulo bruto do RF (antes das pegadas de ADR 0011)"
            inter = int((a_t & a_u).sum())
            uni = int((a_t | a_u).sum())
            n_t, n_u = int(a_t.sum()), int(a_u.sum())
            px_km2 = abs(transform.a * transform.e) / 1e6
            linhas.append(
                {
                    "par_anos": f"{t}-{u}",
                    "classe": nome,
                    "fonte": fonte,
                    "area_t_km2": round(n_t * px_km2, 3),
                    "area_t1_km2": round(n_u * px_km2, 3),
                    "jaccard": round(inter / uni, 4) if uni else "",
                    "churn": round((uni - inter) / uni, 4) if uni else "",
                    "taxa_perda": round((n_t - inter) / n_t, 4) if n_t else "",
                    "taxa_ganho": round((n_u - inter) / n_u, 4) if n_u else "",
                    "razao_area_t1_sobre_t": round(n_u / n_t, 4) if n_t else "",
                }
            )
    return linhas


def destino_do_construido_perdido(rotulos, brutas, transform, t=2015, u=2020) -> dict:
    perdido = brutas[t] & ~brutas[u]
    px_km2 = abs(transform.a * transform.e) / 1e6
    dist = {}
    for nome, cod in clf.CODIGO_CLASSE.items():
        dist[nome] = round(float((perdido & (rotulos[u] == cod)).sum()) * px_km2, 3)
    dist["sem_rotulo_valido"] = round(float((perdido & (rotulos[u] < 0)).sum()) * px_km2, 3)
    dist["_total_perdido_km2"] = round(float(perdido.sum()) * px_km2, 3)
    return dist


def escrever_csv(caminho: Path, linhas: list[dict], nota: str) -> None:
    caminho.parent.mkdir(parents=True, exist_ok=True)
    campos = [*linhas[0].keys(), "nota"]
    with caminho.open("w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=campos)
        w.writeheader()
        for linha in linhas:
            w.writerow({**linha, "nota": nota})


def main() -> int:
    anos = sorted(clf.compostos_disponiveis())
    saida = regenerar_brutas(anos)
    rotulos, brutas = saida["rotulos"], saida["brutas"]
    transform = saida["perfil"]["transform"]
    res_m, epsg = saida["res_m"], saida["epsg"]

    apos_r1, r2_recalculado = clf.aplicar_regras_temporais(brutas)
    r2_publicado = carregar_publicado(anos, res_m, epsg)
    urbano = carregar_urbano(anos, res_m, epsg)

    # Conferência de reprodutibilidade: o R2 recalculado tem de bater com o publicado.
    divergencia = {
        ano: int((r2_recalculado[ano] ^ r2_publicado[ano]).sum()) for ano in anos
    }
    reproduz = all(v == 0 for v in divergencia.values())
    print(f"[chk] divergência pixel a pixel R2 recalculado × publicado: {divergencia}",
          file=sys.stderr)

    r2 = r2_publicado if reproduz else r2_recalculado
    mask_valida_por_ano = {ano: rotulos[ano] >= 0 for ano in anos}

    linhas_dec = decompor(anos, brutas, apos_r1, r2, urbano, transform)
    escrever_csv(
        CSV_DECOMPOSICAO,
        linhas_dec,
        "Decomposição do estoque publicado (pós-R2) em (a) sustentado pela detecção "
        "do próprio ano e (b) herdado da união cumulativa. Ver docs/ADR/0013. "
        + NOTA_EXPERIMENTAL,
    )

    linhas_est = estabilidade(anos, rotulos, brutas, mask_valida_por_ano, transform)
    escrever_csv(
        CSV_ESTABILIDADE,
        linhas_est,
        "Instabilidade ano a ano das classes ANTES de R1/R2, no domínio válido comum "
        "ao par. Ver docs/ADR/0013. " + NOTA_EXPERIMENTAL,
    )

    meta = {
        "gerado_em": datetime.now(UTC).isoformat(),
        "commit": clf.commit_git_atual(),
        "selo": "modelado (diagnóstico experimental)",
        "reproducao_r2_publicado": {
            "bate_pixel_a_pixel": reproduz,
            "pixels_divergentes_por_ano": divergencia,
        },
        "destino_2015_2020": destino_do_construido_perdido(rotulos, brutas, transform),
        "radiometria_da_paisagem_por_ano": {
            str(k): v for k, v in saida["radiometria"].items()
        },
        "prior_de_treino_por_ano": {str(k): v for k, v in saida["prior_treino"].items()},
        "nota": NOTA_EXPERIMENTAL,
        "rasters_experimentais": str(DATA_INTERIM.relative_to(REPO_ROOT)),
    }
    META_JSON.parent.mkdir(parents=True, exist_ok=True)
    META_JSON.write_text(json.dumps(meta, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"[ok ] {CSV_DECOMPOSICAO}\n[ok ] {CSV_ESTABILIDADE}\n[ok ] {META_JSON}",
          file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
