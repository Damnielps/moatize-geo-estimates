#!/usr/bin/env python3
"""fetch_gem_coal_tracker.py — Verificação (não download) do Global Coal Mine
Tracker da Global Energy Monitor (GEM), para status/capacidade das minas da
bacia de Moatize.

Classificação de nível (verificada em 2026-09-11):

1. O dataset da Global Coal Mine Tracker é distribuído via formulário
   (widget `<gem-download-form>` em
   https://globalenergymonitor.org/projects/global-coal-mine-tracker/#download,
   slug "coal-mine-tracker"), que exige preencher nome/e-mail para liberar o
   link de download. Por instrução da tarefa, esse formulário NÃO foi
   preenchido (não fornecer dados pessoais para obter acesso).
2. O conteúdo textual do GEM Wiki (onde estão as páginas descritivas de cada
   mina, ex. https://www.gem.wiki/Moatize_mine) está sob
   **Creative Commons Attribution-NonCommercial-ShareAlike 4.0**
   (verificado no rodapé de https://www.gem.wiki/Moatize_mine, elemento
   `<link rel="license" href="https://creativecommons.org/licenses/by-nc-sa/4.0/">`).
   A cláusula NC (uso não comercial) classifica a fonte como nível B por
   §4.0 do CLAUDE.md ("restringe a uso não comercial").

Conclusão: Global Coal Mine Tracker = **nível B** (gated form + licença NC).
Por §4.0, nível B não é gravado em `data/raw/`, nem sustenta número
publicado; serve apenas como validação/localização de status/capacidade das
minas, nunca substitui produção do 20-F. Nenhum arquivo de dado é gravado
por este script — apenas este registro de verificação, com hash esperado
indisponível porque o dado nunca é baixado aqui.

Uso: `uv run python pipeline/00_fetch/fetch_gem_coal_tracker.py`
(roda a verificação de licença acima; não grava nenhum dado em data/raw/).
"""

from __future__ import annotations

import json
import logging
import sys
from datetime import UTC, datetime
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

REPO_ROOT = Path(__file__).resolve().parents[2]
DATA_INTERIM = REPO_ROOT / "data" / "interim"
DATA_INTERIM.mkdir(parents=True, exist_ok=True)

USER_AGENT = "moatize-geo-estimates 129672935+Damnielps@users.noreply.github.com"
TRACKER_PAGE = "https://globalenergymonitor.org/projects/global-coal-mine-tracker/"
WIKI_MOATIZE = "https://www.gem.wiki/Moatize_mine"

LOG_FILE = DATA_INTERIM / "gem_coal_tracker_check.log"
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[logging.FileHandler(LOG_FILE), logging.StreamHandler()],
)
logger = logging.getLogger(__name__)


def _get(url: str) -> str:
    req = Request(url, headers={"User-Agent": USER_AGENT})
    with urlopen(req, timeout=60) as resp:
        return resp.read().decode("utf-8", errors="replace")


def verificar_gated_form() -> bool:
    """Confirma que o download exige formulário (widget gem-download-form)."""
    html = _get(TRACKER_PAGE)
    return "gem-download-form" in html


def verificar_licenca_wiki() -> str | None:
    """Extrai a licença declarada no rodapé de uma página do GEM Wiki."""
    html = _get(WIKI_MOATIZE)
    marker = 'rel="license" href="'
    idx = html.find(marker)
    if idx == -1:
        return None
    start = idx + len(marker)
    end = html.find('"', start)
    return html[start:end]


def main() -> int:
    resultado = {
        "checked_date": datetime.now(tz=UTC).date().isoformat(),
        "tracker_page": TRACKER_PAGE,
        "wiki_page_amostra": WIKI_MOATIZE,
        "level": "B",
        "motivo": [],
        "uso_permitido": (
            "apenas validação/localização de status e capacidade das minas; "
            "nunca substitui produção declarada no 20-F da Vale (nível A)"
        ),
    }
    try:
        gated = verificar_gated_form()
        resultado["download_exige_formulario"] = gated
        if gated:
            resultado["motivo"].append(
                "download do Coal Mine Tracker exige formulário com nome/e-mail "
                "(widget gem-download-form, slug coal-mine-tracker) — não "
                "preenchido, por instrução da tarefa."
            )
    except (HTTPError, URLError) as exc:
        logger.error("Falha ao verificar página do tracker: %s", exc)
        resultado["download_exige_formulario"] = f"não verificável ({exc})"

    try:
        licenca = verificar_licenca_wiki()
        resultado["licenca_gem_wiki"] = licenca
        if licenca and "nc" in licenca.lower():
            resultado["motivo"].append(
                f"conteúdo do GEM Wiki sob licença com cláusula NonCommercial "
                f"({licenca}) — restringe uso comercial, nível B por §4.0."
            )
    except (HTTPError, URLError) as exc:
        logger.error("Falha ao verificar licença do GEM Wiki: %s", exc)
        resultado["licenca_gem_wiki"] = f"não verificável ({exc})"

    out_file = DATA_INTERIM / "gem_coal_tracker_verificacao.json"
    out_file.write_text(json.dumps(resultado, indent=2, ensure_ascii=False))
    logger.info("Verificação gravada em %s (nível B — não versionado como dado).", out_file)
    logger.info("Nenhum arquivo de dado bruto gravado em data/raw/ (regra nível B).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
