"""§2.3 do desenho — decomposicao OBRIGATORIA da soma de luz em industrial / urbano / resto.

Etapa registrada como NAO EXECUTADA em `docs/ADR/0015` decisao 4. Este script a executa e,
sobretudo, mede o quanto ela e (ou nao e) defensavel.

O que o desenho pede (§2.3): "S_HARM_soma e publicada em tres recortes mutuamente exclusivos
— dentro da pegada `industrial`, dentro de `urbano` fora da pegada, e o restante do poligono.
Sem isso, uma queda de luz por fechamento de planta seria lida como queda de atividade urbana."

Tres incompatibilidades entre o que se pede e o que existe, TODAS declaradas em coluna:

1. RESOLUCAO. A luz e Chen/Yu a ~500 m (0,004492 graus); as camadas sao 30 m em EPSG:32736.
   Um pixel de luz cobre ~278 pixels de camada. Nao existe forma de repartir a radiancia de
   um pixel de luz entre classes sub-pixel sem uma premissa sobre COMO a luz se distribui
   dentro dele. O script nao escolhe uma: calcula as DUAS envoltorias.
     - `_area` (piso): radiancia repartida proporcionalmente a AREA de cada classe no pixel.
       Premissa: densidade de luz uniforme dentro do pixel. Subestima classes brilhantes e
       compactas (planta de beneficiamento, centro urbano) e joga quase tudo em `resto`.
     - `_presenca` (teto): o pixel inteiro vai para a classe de maior prioridade presente
       (industrial > urbano > reassentamento > resto), com qualquer fracao > 0.
       Premissa: toda a luz do pixel vem da classe presente. Superestima.
   O valor verdadeiro esta entre as duas. A RAZAO teto/piso e publicada por ano e por classe:
   ela e a medida direta da indeterminacao, e e o numero que decide se a decomposicao serve.

2. TEMPO. As camadas existem em SEIS anos-ancora (2000, 2005, 2010, 2015, 2020, 2025); a luz
   e anual. Mascara categorica nao se interpola: usa-se a mascara do ANO-ANCORA MAIS PROXIMO
   (empate -> ancora anterior). Nos anos-ancora o selo e "observado (luz) / classificado
   (mascara)"; em todos os demais e "interpolado" — a decomposicao daquele ano NAO e
   observacao, e nenhuma quebra anual pode ser lida nela. A distancia em anos ate a ancora
   usada vai em coluna (`distancia_anos_ate_ancora`, 0 a 3).

3. VIESES HERDADOS, declarados e nao estimados por cima:
     - `urbano` carrega a catraca R2 (ADR 0013): fracao do estoque herdada da uniao cumulativa
       0 / 0 / 3,4 / 6,1 / 12,7 / 18,0 % em 2000..2025. A parcela de luz atribuida a `urbano`
       herda esse crescimento por construcao, e cresce mesmo que nada acenda.
     - `urbano` carrega a comissao medida na acuracia do usuario de `construido`
       (ADR 0009, valor reexecutado em ADR 0014; ver `data/processed/acuracia_por_ano.csv`
       e `pipeline/lib/acuracia_texto.py` para o numero corrente — nao transcrito aqui
       porque esta docstring e avaliada antes do CSV existir num repositorio limpo).
     - `industrial` e `reassentamento` NAO tem R2 (removido por ADR 0014), mas `industrial` tem
       o limiar calibrado contra Maus em 2020 — a concordancia de 2020 nao e independente.
   Nenhum desses vieses e corrigido aqui. Corrigi-los exigiria estimativa que este pipeline
   nao tem; o que se faz e escreve-los na tabela para que nao sejam lidos como ausentes.

Determinismo: nenhum processo estocastico. Nada em `config/seeds.yaml` e consumido porque
nada aqui sorteia — declarado para que a ausencia de seed nao seja lida como omissao.

Saida: data/processed/causal/decomposicao_luz_por_camada.csv
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import rasterio
from rasterio.warp import Resampling, reproject

RAIZ = Path(__file__).resolve().parents[2]
IMG = RAIZ / "data" / "processed" / "imagery"
BRUTO = RAIZ / "data" / "raw"
SAIDA = RAIZ / "data" / "processed" / "causal"

sys.path.insert(0, str(RAIZ / "pipeline" / "lib"))
import acuracia_texto as _acuracia_texto  # noqa: E402

ANCORAS = (2000, 2005, 2010, 2015, 2020, 2025)
CAMADAS = ("industrial", "urbano", "reassentamento")
# prioridade da envoltoria superior: §2.3 pede "industrial / urbano fora da pegada / resto"
PRIORIDADE = ("industrial", "urbano", "reassentamento")
FRACAO_HERDADA_R2 = {2000: 0.000, 2005: 0.000, 2010: 0.034,
                     2015: 0.061, 2020: 0.127, 2025: 0.180}
# Lida de acuracia_por_ano.csv via pipeline/lib/acuracia_texto.py (ORCHESTRATION_LOG.md
# 4-06) — nunca digitada aqui. Se o CSV ainda nao existe, o import acima ja teria
# funcionado (a leitura e preguicosa); a chamada abaixo e o ponto que falha, alto e claro,
# em vez de propagar um numero desatualizado.
ACURACIA_USUARIO_CONSTRUIDO = _acuracia_texto.acuracia_usuario_construido_por_ano()


def anos_de_luz() -> list[int]:
    anos = []
    for f in sorted(BRUTO.glob("viirs_like_li2020_v2_*_tete_aoi.tif")):
        anos.append(int(f.stem.split("_")[4]))
    return sorted(anos)


def ancora_mais_proxima(ano: int) -> int:
    return min(ANCORAS, key=lambda a: (abs(a - ano), a))


def fracoes_na_grade_da_luz(ano_ancora: int, perfil_luz) -> dict[str, np.ndarray]:
    """Reamostra cada mascara de 30 m para a grade de ~500 m da luz, por MEDIA.

    A media de uma mascara 0/1 na celula de destino e exatamente a fracao de area da
    celula coberta pela classe. E a unica agregacao que conserva area; qualquer
    reamostragem por vizinho mais proximo perderia a classe (ela e sub-pixel).
    Efeito de borda declarado: a fronteira de uma classe cai dentro de um pixel de luz
    de ~500 m, entao TODA fronteira e difusa a 1 pixel — ~500 m de indeterminacao
    espacial em torno de cada poligono, que e a ordem de grandeza da propria vila de
    Moatize e maior que varios bairros de Tete.
    """
    out = {}
    for camada in CAMADAS:
        f = IMG / f"{camada}_{ano_ancora}_30m_32736.tif"
        with rasterio.open(f) as src:
            a = src.read(1)
            m = ((a == 1) & (a != src.nodata)).astype("float32")
            dst = np.zeros((perfil_luz["height"], perfil_luz["width"]), dtype="float32")
            reproject(source=m, destination=dst,
                      src_transform=src.transform, src_crs=src.crs,
                      dst_transform=perfil_luz["transform"], dst_crs=perfil_luz["crs"],
                      src_nodata=None, dst_nodata=None,
                      resampling=Resampling.average)
        out[camada] = np.clip(dst, 0.0, 1.0)
    return out


def le_luz(ano: int) -> tuple[np.ndarray, dict]:
    with rasterio.open(BRUTO / f"viirs_like_li2020_v2_{ano}_tete_aoi.tif") as src:
        perfil = {"height": src.height, "width": src.width,
                  "transform": src.transform, "crs": src.crs}
        r = src.read(1).astype("float64")
        nod = src.nodata
    valido = np.isfinite(r) if nod is None else (np.isfinite(r) & (r != nod))
    r = np.where(valido & (r > 0), r, 0.0)   # radiancia negativa e ruido do produto
    return r, perfil


def linha(ano: int, variante: str, anc: int, r: np.ndarray,
          fr: dict[str, np.ndarray]) -> list[dict]:
    f_resto = np.clip(1.0 - fr["industrial"] - fr["urbano"] - fr["reassentamento"], 0.0, 1.0)
    total = float(r.sum())

    # envoltoria inferior: reparticao proporcional a AREA de cada classe no pixel
    soma_area = {c: float((r * fr[c]).sum()) for c in CAMADAS}
    soma_area["resto"] = float((r * f_resto).sum())

    # envoltoria superior: pixel inteiro para a classe de maior prioridade presente
    atribuido = np.zeros(r.shape, dtype=bool)
    soma_pres, npix_pres = {}, {}
    for c in PRIORIDADE:
        sel = (fr[c] > 0) & ~atribuido
        soma_pres[c] = float(r[sel].sum())
        npix_pres[c] = int(sel.sum())
        atribuido |= sel
    soma_pres["resto"] = float(r[~atribuido].sum())
    npix_pres["resto"] = int((~atribuido).sum())

    out = []
    for classe in ("industrial", "urbano", "reassentamento", "resto"):
        piso, teto = soma_area[classe], soma_pres[classe]
        out.append({
            "ano": ano,
            "unidade": "tete_aoi",
            "variante_mascara": variante,
            "classe": classe,
            "soma_radiancia_aoi_total": round(total, 3),
            "soma_radiancia_piso_por_area": round(piso, 3),
            "soma_radiancia_teto_por_presenca": round(teto, 3),
            "share_piso": round(piso / total, 5) if total else np.nan,
            "share_teto": round(teto / total, 5) if total else np.nan,
            "razao_teto_sobre_piso": round(teto / piso, 2) if piso > 0 else np.nan,
            "fracao_area_aoi_da_classe": round(
                float(fr[classe].mean()) if classe in fr else float(f_resto.mean()), 5),
            "n_pixels_luz_com_a_classe": npix_pres[classe],
            "n_pixels_luz_total": int(r.size),
            "ano_mascara_usada": anc,
            "distancia_anos_ate_ancora": abs(ano - anc),
            "selo": ("observado (luz) / classificado (mascara do proprio ano)"
                     if anc == ano else
                     "interpolado (mascara de outro ano-ancora, nao do ano)"),
            "janela_homogenea_E4": ano >= 2013,
            "catraca_R2_na_classe": (classe == "urbano"),
            "fracao_estoque_urbano_herdada_da_uniao": (
                FRACAO_HERDADA_R2[anc] if classe == "urbano" else np.nan),
            "acuracia_usuario_construido_do_ano_ancora": (
                ACURACIA_USUARIO_CONSTRUIDO[anc] if classe == "urbano" else np.nan),
        })
    return out


def main() -> None:
    linhas: list[dict] = []
    cache: dict[int, dict[str, np.ndarray]] = {}
    diag_exclusividade: dict[int, dict] = {}

    for ano in anos_de_luz():
        r, perfil = le_luz(ano)
        # Duas variantes de mascara, e a segunda existe por um motivo especifico:
        # com a mascara FIXA de 2020 qualquer comparacao entre dois anos e invariante a
        # mudanca de mascara, e portanto isola a variacao de LUZ da variacao de
        # CLASSIFICACAO (inclusive da catraca R2, que cresce a mascara `urbano` por
        # construcao). Nenhuma comparacao plurianual deve ser lida na outra variante.
        for variante, anc in (("mascara_ancora_mais_proxima", ancora_mais_proxima(ano)),
                              ("mascara_fixa_2020", 2020)):
            if anc not in cache:
                cache[anc] = fracoes_na_grade_da_luz(anc, perfil)
                # Contrato de exclusividade mutua (§5.1): a 30 m as camadas sao disjuntas.
                # A ~500 m elas deixam de ser — o mesmo pixel de luz pode conter duas.
                f = cache[anc]
                diag_exclusividade[anc] = {
                    "max_soma_fracoes": float(
                        (f["industrial"] + f["urbano"] + f["reassentamento"]).max()),
                    "n_pixels_luz_com_2_ou_mais_classes": int(
                        ((f["industrial"] > 0).astype(int) + (f["urbano"] > 0).astype(int)
                         + (f["reassentamento"] > 0).astype(int) >= 2).sum()),
                }
            linhas.extend(linha(ano, variante, anc, r, cache[anc]))

    df = pd.DataFrame(linhas)
    df["nota"] = (
        "Decomposicao de §2.3, executada sob docs/ADR/0015 decisao 4. NAO e particao unica: "
        "piso e teto sao as duas envoltorias de uma reparticao sub-pixel indeterminada "
        "(luz ~500 m x camadas 30 m, ~278 pixels de camada por pixel de luz). Publicar "
        "SEMPRE os dois. `urbano` herda a catraca R2 (ADR 0013; fracao herdada ate 18,0 % "
        "em 2025) e a comissao medida em `construido`: "
        f"{_acuracia_texto.nota_comissao_construido()} "
        "Essa comissao entra inteira na parcela de luz atribuida a urbano. `industrial` e "
        "`reassentamento` nao tem R2 (ADR 0014), mas o limiar de `industrial` foi calibrado "
        "contra Maus em 2020. Fora dos seis anos-ancora a mascara e de outro ano: selo "
        "`interpolado`. Nenhuma quebra anual pode ser lida nesta tabela."
    )
    SAIDA.mkdir(parents=True, exist_ok=True)
    df.to_csv(SAIDA / "decomposicao_luz_por_camada.csv", index=False)

    meta = {
        "artefato": "decomposicao_luz_por_camada.csv",
        "origem": "pipeline/03_causal/decomposicao_luz.py",
        "mandato": "docs/DESENHO_FASE3.md §2.3; docs/ADR/0015 decisao 4",
        "luz": ("Chen, Z., Yu, B. et al. (2021) ESSD 13:889-906, "
                "DOI 10.5194/essd-13-889-2021; Harvard Dataverse 10.7910/DVN/YGIVCD (CC0). "
                "Prefixo 'viirs_like_li2020_' e heranca de erro (EMENDA E2), "
                "NAO e Li et al. 2020."),
        "camadas": ("data/processed/imagery/"
                    "{industrial,urbano,reassentamento}_<ancora>_30m_32736.tif"),
        "resolucoes": {"luz_graus": 0.00449157642059761, "luz_m_aprox": 500,
                       "camada_m": 30, "pixels_de_camada_por_pixel_de_luz": 278},
        "agregacao": ("mascara 0/1 reamostrada para a grade da luz por MEDIA (= fracao de "
                      "area da celula), rasterio.warp.reproject Resampling.average"),
        "exclusividade_mutua_apos_agregacao": diag_exclusividade,
        "determinismo": "nenhum processo estocastico; config/seeds.yaml nao e consumido",
        "selos": "observado so onde ano == ano-ancora da mascara; interpolado nos demais",
    }
    (SAIDA / "decomposicao_luz_por_camada.meta.json").write_text(
        json.dumps(meta, indent=2, ensure_ascii=False), encoding="utf-8")

    v = df[df.variante_mascara == "mascara_ancora_mais_proxima"]
    print(v.pivot_table(index="ano", columns="classe",
                        values=["share_piso", "share_teto"]).round(4).to_string())
    print("\nrazao teto/piso, mediana sobre os anos:")
    print(df.groupby("classe").razao_teto_sobre_piso.median().round(2).to_string())
    print("\nexclusividade apos agregacao:", json.dumps(diag_exclusividade))


if __name__ == "__main__":
    main()
