#!/usr/bin/env python3
"""
Completa a série ANUAL do harmonizado NPP-VIIRS-like (Chen, Z., Yu, B. et al. 2021,
ESSD 13:889-906, DOI 10.5194/essd-13-889-2021), dataset Harvard Dataverse
DOI 10.7910/DVN/YGIVCD (CC0 1.0), para a AOI de Tete/Moatize e as 5 capitais de
controle (Chimoio, Quelimane, Lichinga, Xai-Xai, Inhambane).

Procedimento idêntico ao usado na coleta anterior (verificado por reprodução: os
valores lidos por /vsizip/ para 2020 batem pixel a pixel, diff máxima 0.0, com o
arquivo já em data/raw/):
  1. baixa o zip "Version2" do ano (arquivo comprimido ~80 MB por ano; o GeoTIFF
     global descomprimido, ~10 GB, NUNCA é escrito em disco por inteiro);
  2. abre via GDAL /vsizip/ (caminho rasterio "zip://...!/...tif");
  3. calcula a janela de leitura com rasterio.windows.from_bounds() usando os MESMOS
     bounds dos recortes já existentes em data/raw/ (lidos dinamicamente do ano 2020,
     que serve de referência de grade);
  4. lê só a janela, escreve um GeoTIFF recortado com a MESMA resolução/grade/CRS;
  5. grava .sha256 (formato "<hash>  <nome-base>") e .meta.json;
  6. apaga o zip temporário.

Idempotente: se o .tif de saída já existe (e tem .sha256 e .meta.json), pula o ano/
cidade. Roda um ano por vez e grava os sidecars imediatamente após escrever o .tif —
nunca grava .sha256/.meta.json de arquivo que não existe.

Uso:
    uv run python pipeline/00_fetch/fetch_npp_viirs_like_chen_yu_annual.py [ano1 ano2 ...]

Sem argumentos, tenta todos os anos que faltam em RAW_DIR, na ordem de prioridade
definida em PRIORIDADE.
"""

import hashlib
import json
import subprocess
import sys
import tempfile
from datetime import UTC, datetime
from pathlib import Path

import rasterio
from rasterio.windows import from_bounds

REPO_ROOT = Path(__file__).resolve().parents[2]
RAW_DIR = REPO_ROOT / "data" / "raw"

DATASET_DOI = "10.7910/DVN/YGIVCD"
CITATION = (
    'Chen, Z., Yu, B., et al. (2020/2025). "The global NPP-VIIRS-like nighttime '
    'light data (Version 2) for 1992-2025." Harvard Dataverse, V10. '
    "DOI: 10.7910/DVN/YGIVCD. Método publicado em Chen, Z., Yu, B., Yang, C., et al. "
    '(2021). "An extended time series (2000-2018) of global NPP-VIIRS-like nighttime '
    'light data from a cross-sensor calibration." Earth System Science Data, 13, '
    "889-906. DOI: 10.5194/essd-13-889-2021"
)

# datafile id do arquivo "<ano>_Version2.zip" no Dataverse (API /api/datasets/:persistentId/),
# confirmado por listagem em 2026-09-08. Preferido sobre "_Version1" e "_HasMask_Version1".
DATAFILE_IDS = {
    1992: 13295247, 1993: 13295252, 1994: 13295256, 1995: 13295258,
    1996: 13295262, 1997: 13295260, 1998: 13295265, 1999: 13295253,
    2000: 13295261, 2001: 13295264, 2002: 13295249, 2003: 13295255,
    2004: 13295259, 2005: 13295251, 2006: 13295257, 2007: 13295263,
    2008: 13295250, 2009: 13295254, 2010: 13295266, 2011: 13295270,
    2012: 13295268, 2013: 13295267, 2014: 13295269, 2015: 13295271,
    2016: 13295278, 2017: 13295273, 2018: 13295272, 2019: 13295276,
    2020: 13295279, 2021: 13295274, 2022: 14085057, 2023: 14085058,
    2024: 14085059, 2025: 14085060,
}


# Tamanho de "<ano>_Version2.zip" em MB, lido da API do Dataverse
# (/api/datasets/:persistentId/versions/:latest/files?persistentId=doi:10.7910/DVN/YGIVCD).
# Usado so para dimensionar o teto de relogio do download — nao entra em nenhum numero
# publicado. Ano ausente aqui cai no padrao de 150 MB, que e maior que o maior conhecido.
TAMANHOS_MB = {
    2008: 140, 2013: 85, 2014: 89, 2017: 110, 2018: 74,
    2021: 86, 2023: 95, 2024: 99,
}

# anos já presentes em data/raw/ antes desta tarefa (2ª passagem da Fase 3)
ANOS_JA_PRESENTES = {2000, 2005, 2010, 2011, 2015, 2016, 2020, 2022, 2025}

# ordem de prioridade pedida pela delegação: 2012-2025 obrigatório; 2008/2014/2019
# obrigatórios (placebo P2); resto de 2000-2011 desejável.
PRIORIDADE = [
    2012, 2013, 2014, 2017, 2018, 2019, 2021, 2023, 2024,  # obrigatório: janela DiD
    2008,  # obrigatório: placebo P2 (2014, 2019 já cobertos acima)
    2001, 2002, 2003, 2004, 2006, 2007, 2009,  # desejável: pré-tratamento denso
    1992, 1993, 1994, 1995, 1996, 1997, 1998, 1999,  # desejável: início da série
]

CIDADES = ["tete_aoi", "chimoio", "quelimane", "lichinga", "xaixai", "inhambane"]


def bounds_referencia():
    """Le os bounds exatos dos recortes ja existentes (ano 2020) para usar como grade."""
    bounds = {}
    for cidade in CIDADES:
        ref = RAW_DIR / f"viirs_like_li2020_v2_2020_{cidade}.tif"
        with rasterio.open(ref) as ds:
            bounds[cidade] = ds.bounds
    return bounds


def sha256_de(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def baixar_zip(ano: int, destino: Path) -> bool:
    datafile_id = DATAFILE_IDS[ano]
    url = f"https://dataverse.harvard.edu/api/access/datafile/{datafile_id}"
    # curl com timeout de conexao e retries: urllib ficou preso indefinidamente numa
    # conexao TCP parada (visto no ano 2014, 1a tentativa).
    #
    # DEFEITO CORRIGIDO (ORCHESTRATION_LOG.md 3-07): a versao anterior usava
    # `--speed-limit 51200 --speed-time 30` (aborta abaixo de 50 KB/s por 30 s) e
    # `timeout=300` (5 min de relogio para um zip de 90-140 MB). A banda medida nesta
    # rede oscila entre 35 e 500+ KB/s, ou seja, cruza os 50 KB/s o tempo todo: o curl
    # matava as proprias transferencias legitimas, e o teto de 5 min so deixava passar
    # os anos que calhavam de pegar a rede rapida. Dos 7 anos pedidos, 5 falharam.
    #
    # E o mesmo padrao de docs/ADR/0014 — limiar ABSOLUTO sobre grandeza NAO
    # ESTACIONARIA, calibrado contra os casos que se quer excluir (conexao travada) sem
    # perguntar o que mais ele remove (conexao apenas lenta). Aqui a correcao segue a
    # mesma forma: o criterio passa a distinguir PARADO de LENTO, e o teto de relogio
    # passa a ser proporcional ao tamanho do arquivo em vez de constante.
    #
    # `-C -` retoma de onde parou: uma falha deixa de custar todo o progresso anterior.
    tamanho_mb = TAMANHOS_MB.get(ano, 150)
    # piso de 30 min; alem disso, 1 s por 12 KB (~12 KB/s de piso efetivo de banda).
    teto_s = max(1800, int(tamanho_mb * 1_000_000 / 12_000))
    cmd = [
        "curl", "-sL", "--fail", "-C", "-",
        "--connect-timeout", "20",
        # PARADO, nao lento: 5 KB/s por 120 s. Uma conexao viva a 35 KB/s sobrevive.
        "--speed-limit", "5120", "--speed-time", "120",
        "--retry", "5", "--retry-delay", "10",
        "-o", str(destino), url,
    ]
    try:
        result = subprocess.run(cmd, timeout=teto_s, check=False)
    except subprocess.TimeoutExpired:
        print(f"  FALHA no download do ano {ano}: timeout de {teto_s}s "
              f"({tamanho_mb} MB a menos de 12 KB/s)")
        return False
    if result.returncode != 0:
        print(f"  FALHA no download do ano {ano}: curl saiu com codigo {result.returncode}")
        return False
    if not destino.exists() or destino.stat().st_size < 10_000:
        tam = destino.stat().st_size if destino.exists() else 0
        print(f"  FALHA: zip do ano {ano} vazio ou minusculo ({tam} bytes)")
        return False
    return True


def nome_interno_tif(zip_path: Path) -> str | None:
    import zipfile
    try:
        with zipfile.ZipFile(zip_path) as z:
            for n in z.namelist():
                if n.endswith(".tif"):
                    return n
    except Exception as e:
        print(f"  FALHA ao ler zip: {e}")
        return None
    return None


def processar_ano(ano: int, bounds_ref: dict, tmp_dir: Path) -> None:
    saidas_faltando = []
    for cidade in CIDADES:
        out = RAW_DIR / f"viirs_like_li2020_v2_{ano}_{cidade}.tif"
        if not (out.exists() and out.with_suffix(out.suffix + ".sha256").exists()
                and out.with_suffix(out.suffix + ".meta.json").exists()):
            saidas_faltando.append(cidade)
    if not saidas_faltando:
        print(f"ano {ano}: ja completo, pulando")
        return

    if ano not in DATAFILE_IDS:
        print(f"ano {ano}: NAO EXISTE no dataset Chen/Yu "
              "(fora do intervalo do produto) — nao disponivel")
        return

    zip_path = tmp_dir / f"{ano}_Version2.zip"
    print(f"ano {ano}: baixando datafile {DATAFILE_IDS[ano]} ...")
    ok = baixar_zip(ano, zip_path)
    if not ok:
        print(f"ano {ano}: NAO DISPONIVEL — download falhou (ver mensagem acima)")
        return

    interno = nome_interno_tif(zip_path)
    if interno is None:
        print(f"ano {ano}: NAO DISPONIVEL — zip sem .tif interno ou corrompido")
        zip_path.unlink(missing_ok=True)
        return

    vsizip_path = f"zip://{zip_path}!/{interno}"
    try:
        with rasterio.open(vsizip_path) as ds:
            for cidade in saidas_faltando:
                b = bounds_ref[cidade]
                win = from_bounds(b.left, b.bottom, b.right, b.top, transform=ds.transform)
                data = ds.read(1, window=win)
                out_transform = ds.window_transform(win)
                out = RAW_DIR / f"viirs_like_li2020_v2_{ano}_{cidade}.tif"
                profile = {
                    "driver": "GTiff",
                    "height": data.shape[0],
                    "width": data.shape[1],
                    "count": 1,
                    "dtype": data.dtype,
                    "crs": ds.crs,
                    "transform": out_transform,
                    "nodata": ds.nodata,
                    "compress": "deflate",
                }
                with rasterio.open(out, "w", **profile) as dst:
                    dst.write(data, 1)

                sha = sha256_de(out)
                sha_path = Path(str(out) + ".sha256")
                sha_path.write_text(f"{sha}  {out.name}\n")

                meta = {
                    "url": f"https://dataverse.harvard.edu/api/access/datafile/{DATAFILE_IDS[ano]}",
                    "download_date": datetime.now(UTC).isoformat(),
                    "size_bytes": out.stat().st_size,
                    "license": "CC0 1.0",
                    "license_url": "http://creativecommons.org/publicdomain/zero/1.0",
                    "level": "nao classificado - cabe ao auditor-dados",
                    "source_page": f"https://doi.org/{DATASET_DOI}",
                    "citation": CITATION,
                    "selo": "observado",
                    "ano": ano,
                    "anos_cobertos": str(ano),
                    "resolucao_deg": out_transform.a,
                    "unidade_aproximada_m": 500,
                    "aoi_bbox": {
                        "xmin": b.left, "ymin": b.bottom, "xmax": b.right, "ymax": b.top,
                    },
                    "regiao": (
                        "AOI Tete/Moatize (config/study.yaml)" if cidade == "tete_aoi"
                        else f"Capital de controle: {cidade} (config/study.yaml controles)"
                    ),
                    "nota": (
                        f"Recortado da grade global via GDAL /vsizip/ (leitura em janela, "
                        f"rasterio.windows.from_bounds) a partir do zip {ano}_Version2.zip "
                        f"(datafile id {DATAFILE_IDS[ano]}); arquivo global (~10 GB tif "
                        f"descomprimido) NAO foi mirrorado inteiro, so o zip comprimido "
                        f"temporario ({zip_path.stat().st_size} bytes) foi baixado e "
                        f"descartado apos o recorte. Grade identica aos recortes ja "
                        f"existentes em data/raw/ (bounds lidos do ano 2020 como referencia; "
                        f"verificado por reproducao: leitura de 2020 via este metodo "
                        f"reproduz o arquivo ja em disco pixel a pixel, diff maxima 0.0)."
                    ),
                }
                Path(str(out) + ".meta.json").write_text(
                    json.dumps(meta, indent=2, ensure_ascii=False)
                )
                print(f"  {cidade}: OK ({out.name}, {out.stat().st_size} bytes)")
    finally:
        zip_path.unlink(missing_ok=True)
    print(f"ano {ano}: concluido")


def main():
    args = sys.argv[1:]
    anos = [int(a) for a in args] if args else PRIORIDADE
    bounds_ref = bounds_referencia()
    with tempfile.TemporaryDirectory(prefix="npp_viirs_chen_yu_") as tmp:
        tmp_dir = Path(tmp)
        for ano in anos:
            processar_ano(ano, bounds_ref, tmp_dir)


if __name__ == "__main__":
    main()
