"""pipeline/05_app/gerar_artigo.py — app/src/content/artigo.json a partir de
`paper/artigo.md` (CLAUDE.md §6, tarefa "aba Artigo").

Mesmo padrão de `pipeline/05_app/gerar_metodologia.py`: o conteúdo publicado é o texto
bruto do documento-fonte, recortado de forma mecânica (regex de cabeçalho), nunca
resumido ou reescrito por um agente. Se `paper/artigo.md` mudar, esta rotina tem de
rodar de novo — é isso que o `sync-data`/Makefile garante — ou o app diverge em
silêncio do manuscrito, que é exatamente a classe de defeito que a tarefa pede para
evitar.

O JSON de saída carrega:
- o texto Markdown completo (`markdown`), para o app renderizar com
  `react-markdown` + `remark-gfm` (o manuscrito tem tabelas GFM, blocos de citação e
  notas que Markdown puro do CommonMark não cobre);
- um sumário mecânico (`sumario`), uma entrada por cabeçalho `#`/`##`/`###`, com o
  mesmo algoritmo de slug que o app usa para gerar `id` de cabeçalho — os dois lados
  (JSON e componente React) calculam o slug de forma independente a partir do MESMO
  texto de título, então não há lista de âncoras mantida à mão para divergir.

Uso: uv run python pipeline/05_app/gerar_artigo.py
"""
from __future__ import annotations

import json
import re
from datetime import UTC, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
ARTIGO_MD = ROOT / "paper" / "artigo.md"
OUT = ROOT / "app" / "src" / "content" / "artigo.json"

_PADRAO_CABECALHO = re.compile(r"^(#{1,3})\s+(.*)$")


def slugificar(titulo: str) -> str:
    """Mesmo algoritmo usado por `ArtigoPage.jsx` para gerar `id` de cabeçalho a
    partir do texto do título — não uma lista de âncoras mantida em paralelo."""
    texto = titulo.strip().lower()
    texto = re.sub(r"[`*_]", "", texto)
    texto = re.sub(r"[^\w\s-]", "", texto, flags=re.UNICODE)
    texto = re.sub(r"[\s]+", "-", texto).strip("-")
    return texto


def remover_frontmatter(texto: str) -> tuple[str, str | None]:
    """Separa o bloco YAML de frontmatter (entre `---`) do corpo Markdown, se
    existir — o frontmatter (título, autor, abstract) tem de ser tratado à parte,
    não misturado ao corpo GFM."""
    if not texto.startswith("---"):
        return texto, None
    partes = texto.split("---", 2)
    if len(partes) < 3:
        return texto, None
    return partes[2].lstrip("\n"), partes[1].strip()


def montar_sumario(corpo_md: str) -> list[dict]:
    sumario = []
    vistos: dict[str, int] = {}
    for linha in corpo_md.splitlines():
        m = _PADRAO_CABECALHO.match(linha)
        if not m:
            continue
        nivel = len(m.group(1))
        titulo = m.group(2).strip()
        slug_base = slugificar(titulo)
        n = vistos.get(slug_base, 0)
        vistos[slug_base] = n + 1
        slug = slug_base if n == 0 else f"{slug_base}-{n}"
        sumario.append({"nivel": nivel, "titulo": titulo, "slug": slug})
    return sumario


def main() -> None:
    if not ARTIGO_MD.exists():
        raise SystemExit(f"não encontrado: {ARTIGO_MD}")

    texto = ARTIGO_MD.read_text(encoding="utf-8")
    corpo_md, frontmatter_raw = remover_frontmatter(texto)
    sumario = montar_sumario(corpo_md)

    doc = {
        "gerado_por": "pipeline/05_app/gerar_artigo.py",
        "gerado_em_utc": datetime.now(UTC).isoformat(),
        "fonte": str(ARTIGO_MD.relative_to(ROOT)),
        "aviso": (
            "Este conteúdo é GERADO de paper/artigo.md. Nenhum trecho foi copiado ou "
            "reescrito à mão: o Markdown abaixo é o corpo do manuscrito na íntegra, "
            "menos o frontmatter YAML. Reexecute "
            "pipeline/05_app/gerar_artigo.py após qualquer edição do manuscrito — "
            "nunca edite este JSON manualmente."
        ),
        "frontmatter_raw": frontmatter_raw,
        "markdown": corpo_md,
        "sumario": sumario,
    }

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(doc, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"escrito: {OUT.relative_to(ROOT)} ({OUT.stat().st_size} bytes, {len(sumario)} seções)")


if __name__ == "__main__":
    main()
