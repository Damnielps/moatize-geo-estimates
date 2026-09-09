#!/usr/bin/env python3
"""pipeline/01_imagery/cultivo.py — separação fenológica de cultivo (§5.6.1, Fase 2b).

Duas classes novas, `cultivo_sequeiro` e `cultivo_irrigado`, recortadas de dentro das
camadas já existentes `solo_exposto` e `vegetacao` (`classificacao.py`, §5.1). **Não são
uma sétima e oitava camada da partição da AOI**: são um refinamento fenológico das duas
camadas de cobertura não construída, e por isso podem — e devem — sobrepor
`solo_exposto`/`vegetacao`. O que elas NÃO podem sobrepor é `urbano`, `industrial` e
`reassentamento` (§10 continua valendo: nenhuma cava e nenhum povoado de reassentamento
vira cultivo), o que decorre por construção porque o domínio de busca é
`solo_exposto ∪ vegetacao`, que já exclui as três camadas de construído/pegada e `agua`.

## Regra de separação — por que fenológica e por que relativa à paisagem

§5.6.1 pede a separação por amplitude de NDVI chuva-seca: sequeiro verdeja na chuva e
seca na seca (amplitude alta); irrigado/vazante mantém verde na seca (NDVI de seca alto,
amplitude baixa). A Fase 1 mediu que um limiar ABSOLUTO de NDVI não é comparável entre
os anos-âncora desta série — a mediana de NDVI(chuva) da paisagem vai de 0,669 (2015) a
0,330 (2025), por diferença de sensor e de pluviosidade (docs/ADR/0011). O mesmo problema
se aplica aqui e é resolvido do mesmo jeito: os limiares são uma RAZÃO à mediana de uma
população de referência fixa por ano — não um percentil da imagem (a população não é
definida por uma fração arbitrária, e a fração selecionada varia livremente ano a ano).

**População de referência do ano:** todo pixel válido em `solo_exposto ∪ vegetacao`
(isto é, fora de `urbano`, `industrial`, `reassentamento` e `agua`) — a mesma construção
de `classificacao.mediana_paisagem`, reaproveitada aqui.

## As duas regras

- **`cultivo_irrigado`** — dentro de `vegetacao` (que já exige NDVI(seca) ≥ 0,30: verde
  persistente na seca, por definição de `classificacao.py`), os pixels de MENOR amplitude
  relativa: `amplitude ≤ RATIO_IRRIGADO_AMP × mediana(amplitude, referência)`. Amplitude
  baixa dentro de um conjunto que já é persistentemente verde isola o subconjunto que
  varia MENOS entre estações — o padrão esperado de irrigação ou vazante, que mantém
  verde na seca por decisão de manejo, e não por dossel perene natural (mata ripária,
  miombo). O corte não separa perfeitamente os dois: **limitação declarada** abaixo.
- **`cultivo_sequeiro`** — dentro de `solo_exposto` (NDVI(seca) < 0,30 por definição),
  os pixels de MAIOR amplitude relativa E com reverdecimento genuíno na chuva:
  `amplitude ≥ RATIO_SEQUEIRO_AMP × mediana(amplitude, referência)` E
  `NDVI(chuva) ≥ RATIO_SEQUEIRO_CHUVA × mediana(NDVI-chuva, referência)`. A segunda
  condição existe para não capturar solo quase nu com ruído de amplitude alta e chuva
  fraca — exige um "flush" de verde de fato na estação chuvosa.

## Limitação declarada, com o número que a sustenta (não escondida)

**Fenologia bianual (uma estação seca, uma chuvosa, por ano) não separa cultivo de
sequeiro de vegetação herbácea/arbustiva natural com o mesmo padrão sazonal** (savana
que verdeja na chuva e seca no inverno), nem cultivo irrigado de mata ripária perene com
o mesmo padrão de verde persistente. Nenhum dado de nível A nesta AOI resolve essa
ambiguidade em 30 m sem série intra-anual mais densa (§5.6.1 pede "número de picos", que
exigiria compostos mensais — fora do escopo desta entrega, que dispõe só de dois
compostos por ano). `cultivo_sequeiro` mede, com mais precisão, "vegetação de fenologia
estacional acentuada" — cultivo de sequeiro é o componente antrópico dominante dentro da
mancha periurbana e nos vales, mas a classe INCLUI savana herbácea/arbustiva sazonal fora
desses contextos. `cultivo_irrigado` mede "verde persistente de baixa amplitude" — inclui
mata ripária além de hortas e campos de vazante. A validação por interpretação visual
(`acuracia_cultivo.py`) mede exatamente essa confusão pela acurácia do usuário.

**A instabilidade herdada da Fase 1 é maior do que a fenológica.** As proporções de
`vegetacao` e `solo_exposto` na AOI oscilam de forma não monotônica entre anos-âncora —
de 6,5 % de vegetação em 2000 (solo_exposto domina, seca/sensor L7) a 87,8 % em 2015
(veja `cultivo_por_ano.csv`, coluna `area_dominio_veg_km2`/`area_dominio_solo_km2`) — o
mesmo tipo de instabilidade de sensor/pluviosidade já documentado para `urbano`
(docs/ADR/0008, ADR/0009). Como as classes de cultivo são recortadas DENTRO dessas duas
camadas, elas herdam essa instabilidade: **a série de área de `cultivo_sequeiro` e
`cultivo_irrigado` não deve ser lida como série de mudança real de uso agrícola** sem
controlar por esse efeito. Isso é medido e publicado, não presumido — ver a coluna
`nota_instabilidade` do CSV de saída.

Uso: `uv run python pipeline/01_imagery/cultivo.py [ano ...]`
"""

from __future__ import annotations

import csv
import json
import sys
from datetime import UTC, datetime
from pathlib import Path

import numpy as np
import rasterio

sys.path.insert(0, str(Path(__file__).resolve().parent))
from classificacao import (
    area_km2,
    commit_git_atual,
    hash_arquivo,
    salvar_raster,
    salvar_vetor,
)

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "00_fetch"))
from _config import carregar_estudo

REPO_ROOT = Path(__file__).resolve().parents[2]
STUDY_YAML = REPO_ROOT / "config" / "study.yaml"
DATA_PROCESSED = REPO_ROOT / "data" / "processed" / "imagery"
CULTIVO_CSV = REPO_ROOT / "data" / "processed" / "cultivo_por_ano.csv"
PROVENANCE_FRAGMENT = REPO_ROOT / "data" / "provenance_parts" / "agricultura_fase2b.md"
MARCADOR_INICIO = "<!-- SECAO_CULTIVO_INICIO -->"
MARCADOR_FIM = "<!-- SECAO_CULTIVO_FIM -->"

ANOS_ANCORA = [2000, 2005, 2010, 2015, 2020, 2025]
RES_M, EPSG = 30, 32736

# Razões à mediana da paisagem de referência do ano (solo_exposto ∪ vegetacao, fora de
# construído/pegada/água) — ver docstring do módulo. Nenhum valor é percentil da imagem.
RATIO_IRRIGADO_AMP = 0.50
RATIO_SEQUEIRO_AMP = 1.30
RATIO_SEQUEIRO_CHUVA = 1.00

NOMES_CAMADAS_CULTIVO = ["cultivo_sequeiro", "cultivo_irrigado"]


def caminho_camada(nome: str, ano: int) -> Path:
    return DATA_PROCESSED / f"{nome}_{ano}_{RES_M}m_{EPSG}.tif"


def ler_raster(path: Path, masked: bool = False) -> tuple[np.ndarray, dict]:
    with rasterio.open(path) as src:
        dados = src.read(1, masked=masked)
        perfil = {"crs": src.crs, "transform": src.transform, "shape": src.shape}
    return dados, perfil


def carregar_ano(ano: int) -> dict:
    faltando = [
        n
        for n in ("ndvi", "ndvi_chuva", "ndvi_amplitude", "vegetacao", "solo_exposto",
                  "agua", "urbano", "industrial", "reassentamento")
        if not caminho_camada(n, ano).exists()
    ]
    if faltando:
        raise FileNotFoundError(
            f"{ano}: insumos ausentes em data/processed/imagery/: {faltando}. Rode "
            "compostos_chuva.py e classificacao.py antes de cultivo.py."
        )
    ndvi_seca, perfil = ler_raster(caminho_camada("ndvi", ano), masked=True)
    ndvi_seca = np.ma.filled(ndvi_seca, np.nan)
    ndvi_chuva = np.ma.filled(ler_raster(caminho_camada("ndvi_chuva", ano), masked=True)[0], np.nan)
    amplitude = np.ma.filled(
        ler_raster(caminho_camada("ndvi_amplitude", ano), masked=True)[0], np.nan
    )
    veg = ler_raster(caminho_camada("vegetacao", ano))[0].astype(bool)
    solo = ler_raster(caminho_camada("solo_exposto", ano))[0].astype(bool)
    agua = ler_raster(caminho_camada("agua", ano))[0].astype(bool)
    urbano = ler_raster(caminho_camada("urbano", ano))[0].astype(bool)
    industrial = ler_raster(caminho_camada("industrial", ano))[0].astype(bool)
    reassentamento = ler_raster(caminho_camada("reassentamento", ano))[0].astype(bool)
    return {
        "perfil": perfil,
        "ndvi_seca": ndvi_seca,
        "ndvi_chuva": ndvi_chuva,
        "amplitude": amplitude,
        "veg": veg,
        "solo": solo,
        "agua": agua,
        "urbano": urbano,
        "industrial": industrial,
        "reassentamento": reassentamento,
    }


def classificar_ano(dados: dict) -> tuple[np.ndarray, np.ndarray, dict]:
    finito = (
        np.isfinite(dados["ndvi_seca"])
        & np.isfinite(dados["ndvi_chuva"])
        & np.isfinite(dados["amplitude"])
    )
    dominio_referencia = (dados["veg"] | dados["solo"]) & finito
    if dominio_referencia.sum() == 0:
        raise RuntimeError("domínio de referência vazio — vegetacao/solo_exposto ausentes?")

    med_amp = float(np.median(dados["amplitude"][dominio_referencia]))
    med_seca = float(np.median(dados["ndvi_seca"][dominio_referencia]))
    med_chuva = float(np.median(dados["ndvi_chuva"][dominio_referencia]))

    cultivo_irrigado = (
        dados["veg"] & finito & (dados["amplitude"] <= RATIO_IRRIGADO_AMP * med_amp)
    )
    cultivo_sequeiro = (
        dados["solo"]
        & finito
        & (dados["amplitude"] >= RATIO_SEQUEIRO_AMP * med_amp)
        & (dados["ndvi_chuva"] >= RATIO_SEQUEIRO_CHUVA * med_chuva)
    )

    # Garantia por construção, verificada explicitamente (nunca presumida): nenhuma
    # sobreposição com construído/pegada/água, porque o domínio de busca já as exclui.
    construido_ou_pegada_ou_agua = (
        dados["urbano"] | dados["industrial"] | dados["reassentamento"] | dados["agua"]
    )
    assert not (cultivo_irrigado & construido_ou_pegada_ou_agua).any()
    assert not (cultivo_sequeiro & construido_ou_pegada_ou_agua).any()
    assert not (cultivo_irrigado & cultivo_sequeiro).any()

    diagnostico = {
        "mediana_amplitude_paisagem": med_amp,
        "mediana_ndvi_seca_paisagem": med_seca,
        "mediana_ndvi_chuva_paisagem": med_chuva,
        "n_pixels_dominio_referencia": int(dominio_referencia.sum()),
        "n_pixels_vegetacao": int(dados["veg"].sum()),
        "n_pixels_solo_exposto": int(dados["solo"].sum()),
    }
    return cultivo_sequeiro, cultivo_irrigado, diagnostico


def main(argv: list[str]) -> int:
    estudo = carregar_estudo(STUDY_YAML)
    crs_esperado = estudo["crs"]["metrico"]

    anos = [int(a) for a in argv] if argv else ANOS_ANCORA
    registros = []

    for ano in anos:
        dados = carregar_ano(ano)
        perfil = dados["perfil"]
        if f"EPSG:{perfil['crs'].to_epsg()}" != crs_esperado:
            raise RuntimeError(f"{ano}: grade em {perfil['crs']}, esperado {crs_esperado}")

        sequeiro, irrigado, diag = classificar_ano(dados)
        transform, crs = perfil["transform"], perfil["crs"]

        areas = {}
        for nome, mask in (("cultivo_sequeiro", sequeiro), ("cultivo_irrigado", irrigado)):
            caminho_raster = caminho_camada(nome, ano)
            salvar_raster(mask, caminho_raster, crs, transform)
            caminho_vetor = DATA_PROCESSED / f"{nome}_{ano}.geojson"
            n_poligonos = salvar_vetor(mask, caminho_vetor, crs, transform, ano, nome)
            area = area_km2(mask, transform)
            areas[nome] = area

            meta = {
                "ano": ano,
                "camada": nome,
                "arquivo_raster": str(caminho_raster.relative_to(REPO_ROOT)),
                "arquivo_vetor": str(caminho_vetor.relative_to(REPO_ROOT)),
                "n_poligonos_vetor": n_poligonos,
                "area_km2": area,
                "n_pixels": int(mask.sum()),
                "resolucao_m": RES_M,
                "crs": f"EPSG:{EPSG}",
                "metodo": (
                    "recorte fenológico de vegetacao/solo_exposto por amplitude de NDVI "
                    "chuva-seca relativa à mediana da paisagem de referência do ano "
                    f"(ratio_irrigado_amp={RATIO_IRRIGADO_AMP}, "
                    f"ratio_sequeiro_amp={RATIO_SEQUEIRO_AMP}, "
                    f"ratio_sequeiro_chuva={RATIO_SEQUEIRO_CHUVA})"
                ),
                "natureza": (
                    "refinamento fenológico DENTRO de "
                    + ("vegetacao" if nome == "cultivo_irrigado" else "solo_exposto")
                    + " — NÃO é camada mutuamente exclusiva com ela; é mutuamente "
                    "exclusiva com urbano/industrial/reassentamento/agua"
                ),
                "limitacao": (
                    "fenologia bianual não separa cultivo de vegetação natural com o "
                    "mesmo padrão sazonal (savana herbácea/arbustiva para sequeiro; mata "
                    "ripária para irrigado); ver docstring de cultivo.py e "
                    "acuracia_cultivo.py para a acurácia do usuário medida"
                ),
                "diagnostico": diag,
                "selo": "observado",
                "data_processamento": datetime.now(UTC).isoformat(),
                "commit_git": commit_git_atual(),
                "hash_config_study_yaml": hash_arquivo(STUDY_YAML),
                "script": "pipeline/01_imagery/cultivo.py",
            }
            caminho_raster.with_suffix(".tif.meta.json").write_text(
                json.dumps(meta, indent=2, ensure_ascii=False), encoding="utf-8"
            )

        registros.append(
            {
                "ano": ano,
                "cultivo_sequeiro_km2": areas["cultivo_sequeiro"],
                "cultivo_irrigado_km2": areas["cultivo_irrigado"],
                "area_dominio_veg_km2": area_km2(dados["veg"], transform),
                "area_dominio_solo_km2": area_km2(dados["solo"], transform),
                "mediana_amplitude_paisagem": diag["mediana_amplitude_paisagem"],
                "mediana_ndvi_seca_paisagem": diag["mediana_ndvi_seca_paisagem"],
                "mediana_ndvi_chuva_paisagem": diag["mediana_ndvi_chuva_paisagem"],
            }
        )
        print(
            f"[ok] {ano}: sequeiro={areas['cultivo_sequeiro']:.1f} km² "
            f"irrigado={areas['cultivo_irrigado']:.1f} km²",
            file=sys.stderr,
        )

    escrever_csv(registros)
    escrever_proveniencia(registros)
    print(f"[ok] {CULTIVO_CSV.relative_to(REPO_ROOT)} gravado", file=sys.stderr)
    return 0


def escrever_csv(registros: list[dict]) -> None:
    CULTIVO_CSV.parent.mkdir(parents=True, exist_ok=True)
    nota = (
        "Recorte fenológico DENTRO de vegetacao (irrigado) e solo_exposto (sequeiro) — "
        "não são camadas adicionais na partição da AOI, sobrepõem essas duas por "
        "construção. Limiares são razão à mediana da paisagem de referência do PRÓPRIO "
        "ano (solo_exposto ∪ vegetacao, fora de construído/pegada/água), não percentil "
        "da imagem. ATENÇÃO: a proporção vegetacao/solo_exposto oscila fortemente entre "
        "anos-âncora por diferença de sensor/pluviosidade herdada da Fase 1 "
        "(docs/ADR/0008, ADR/0009) — ver colunas area_dominio_veg_km2/"
        "area_dominio_solo_km2. A série de área de cultivo NÃO deve ser lida como "
        "mudança real de uso agrícola sem controlar por esse efeito. Selo: observado."
    )
    with CULTIVO_CSV.open("w", newline="", encoding="utf-8") as fh:
        campos = [
            "ano",
            "cultivo_sequeiro_km2",
            "cultivo_irrigado_km2",
            "area_dominio_veg_km2",
            "area_dominio_solo_km2",
            "mediana_amplitude_paisagem",
            "mediana_ndvi_seca_paisagem",
            "mediana_ndvi_chuva_paisagem",
            "selo",
            "nota_instabilidade",
        ]
        w = csv.DictWriter(fh, fieldnames=campos)
        w.writeheader()
        for r in registros:
            linha = {k: (f"{v:.4f}" if isinstance(v, float) else v) for k, v in r.items()}
            linha["selo"] = "observado"
            linha["nota_instabilidade"] = nota
            w.writerow(linha)


def escrever_proveniencia(registros: list[dict]) -> None:
    linhas = [
        MARCADOR_INICIO,
        "",
        "## Cultivo — separação fenológica sequeiro × irrigado (§5.6.1, Fase 2b)",
        "",
        "Gerado por `pipeline/01_imagery/cultivo.py`. `cultivo_sequeiro` e "
        "`cultivo_irrigado` são recortes fenológicos DENTRO de `solo_exposto` e "
        "`vegetacao` (§5.1), não camadas novas na partição mutuamente exclusiva da AOI: "
        "sobrepõem essas duas camadas por construção e são mutuamente exclusivas apenas "
        "em relação a `urbano`/`industrial`/`reassentamento`/`agua`.",
        "",
        "**Limiar relativo à paisagem do próprio ano** "
        f"(ratio_irrigado_amp={RATIO_IRRIGADO_AMP}, ratio_sequeiro_amp={RATIO_SEQUEIRO_AMP}, "
        f"ratio_sequeiro_chuva={RATIO_SEQUEIRO_CHUVA}), pelo mesmo motivo de "
        "docs/ADR/0011: NDVI absoluto não é comparável entre os anos-âncora desta série.",
        "",
        "**Limitação declarada:** fenologia bianual não separa cultivo de vegetação "
        "natural com o mesmo padrão sazonal. `cultivo_sequeiro` mede vegetação de "
        "fenologia estacional acentuada (inclui savana herbácea/arbustiva sazonal); "
        "`cultivo_irrigado` mede verde persistente de baixa amplitude (inclui mata "
        "ripária). A acurácia do usuário medida por interpretação visual está em "
        "`acuracia_cultivo.py` / `data/processed/acuracia_cultivo_por_ano.csv`.",
        "",
        "**Instabilidade herdada da Fase 1:** a proporção vegetacao/solo_exposto muda "
        "de forma não monotônica entre anos-âncora por diferença de sensor/pluviosidade "
        "(mesmo efeito de docs/ADR/0008 e ADR/0009). A série de área de cultivo herda "
        "essa instabilidade e não deve ser lida como mudança real de uso do solo sem "
        "controlar por ela.",
        "",
        "| ano | sequeiro km² | irrigado km² | domínio veg km² | domínio solo km² | "
        "mediana amplitude | mediana NDVI seca | mediana NDVI chuva |",
        "|---|---|---|---|---|---|---|---|",
    ]
    for r in registros:
        linhas.append(
            f"| {r['ano']} | {r['cultivo_sequeiro_km2']:.1f} | "
            f"{r['cultivo_irrigado_km2']:.1f} | {r['area_dominio_veg_km2']:.1f} | "
            f"{r['area_dominio_solo_km2']:.1f} | {r['mediana_amplitude_paisagem']:.3f} | "
            f"{r['mediana_ndvi_seca_paisagem']:.3f} | {r['mediana_ndvi_chuva_paisagem']:.3f} |"
        )
    linhas += ["", MARCADOR_FIM, ""]

    atual = PROVENANCE_FRAGMENT.read_text(encoding="utf-8") if PROVENANCE_FRAGMENT.exists() else (
        "# Proveniência — Fase 2b: agricultura e várzea (§5.6)\n\n"
        "Fragmento consolidado por `scripts/consolidar_registros.py` em `PROVENANCE.md`. "
        "Não editar à mão as seções entre marcadores: são geradas pelo script "
        "correspondente.\n\n"
    )
    if MARCADOR_INICIO in atual and MARCADOR_FIM in atual:
        novo = atual.split(MARCADOR_INICIO)[0] + "\n".join(linhas) + atual.split(MARCADOR_FIM)[1]
    else:
        novo = atual + "\n" + "\n".join(linhas)
    PROVENANCE_FRAGMENT.parent.mkdir(parents=True, exist_ok=True)
    PROVENANCE_FRAGMENT.write_text(novo, encoding="utf-8")


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
