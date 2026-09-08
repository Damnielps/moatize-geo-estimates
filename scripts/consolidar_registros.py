#!/usr/bin/env python3
"""Consolida data/{licenses,provenance}_parts/ em data/LICENSES.md e PROVENANCE.md.

Propósito (§4.0 regra 1, §11.2.3): as famílias de fonte são coletadas em paralelo por
subagentes distintos, que gravariam em conflito no mesmo arquivo. Cada uma escreve seu
fragmento; este script monta os documentos canônicos a partir deles.

Entradas: data/licenses_parts/*.md, data/provenance_parts/*.md
Saídas:   data/LICENSES.md, PROVENANCE.md (raiz)
Determinístico: ordem alfabética dos fragmentos; nenhuma dependência de estado.
"""
from __future__ import annotations

import datetime as dt
import pathlib
import sys

RAIZ = pathlib.Path(__file__).resolve().parents[1]

CABECALHO_LICENSES = """# data/LICENSES.md

Uma linha por fonte (§4.0, regra 1). Fonte sem texto de licença localizável na página do
produtor é **nível C** até prova em contrário.

Colunas: nome · URL canônica · licença (link para o texto no site do produtor) ·
nível A/B/C · restrições · citação exigida · data de verificação.

> **Gerado por `scripts/consolidar_registros.py` a partir de `data/licenses_parts/`.**
> Não edite este arquivo à mão: edite o fragmento da família e reexecute o script.
"""

CABECALHO_PROVENANCE = """# PROVENANCE.md

Cadeia de proveniência por artefato (§11.2.3): insumos com hash, script com commit,
parâmetros com hash do YAML, data, versão do ambiente e selo
`observado` / `interpolado` / `modelado`.

> **Gerado por `scripts/consolidar_registros.py` a partir de `data/provenance_parts/`.**
> Não edite este arquivo à mão: edite o fragmento da família e reexecute o script.
"""


def montar(diretorio: pathlib.Path, cabecalho: str, destino: pathlib.Path) -> int:
    fragmentos = sorted(p for p in diretorio.glob("*.md"))
    if not fragmentos:
        print(f"nenhum fragmento em {diretorio}", file=sys.stderr)
        return 1

    partes = [cabecalho, f"\nConsolidado em {dt.datetime.now(tz=dt.UTC).date().isoformat()}.\n"]

    def contar_pendentes(caminho: pathlib.Path) -> int:
        """Conta só células de tabela ainda por verificar.

        A palavra também aparece em texto de método ("toda linha permanece PENDENTE
        até verificação"), e contar essas ocorrências marcava como incompleta uma
        família que estava fechada — aviso falso no documento consolidado.
        """
        total = 0
        for linha in caminho.read_text(encoding="utf-8").splitlines():
            despido = linha.strip()
            if despido.startswith("|") and "PENDENTE" in despido:
                total += despido.count("PENDENTE")
        return total

    pendentes = {p.stem: contar_pendentes(p) for p in fragmentos}
    incompletas = {k: v for k, v in pendentes.items() if v}
    if incompletas:
        partes.append(
            "\n> ⚠️ **Famílias incompletas** (linhas ainda marcadas `PENDENTE`): "
            + ", ".join(f"`{k}` ({v})" for k, v in sorted(incompletas.items()))
            + ". Nenhum número dessas famílias pode sustentar resultado publicado.\n"
        )

    for fragmento in fragmentos:
        texto = fragmento.read_text(encoding="utf-8").strip()
        partes.append(f"\n---\n\n<!-- fonte: {fragmento.relative_to(RAIZ)} -->\n\n{texto}\n")

    destino.write_text("\n".join(partes), encoding="utf-8")
    print(f"{destino.relative_to(RAIZ)}: {len(fragmentos)} fragmentos, "
          f"{sum(pendentes.values())} linhas PENDENTE")
    return 0


def main() -> int:
    codigo = montar(RAIZ / "data" / "licenses_parts", CABECALHO_LICENSES,
                    RAIZ / "data" / "LICENSES.md")
    codigo |= montar(RAIZ / "data" / "provenance_parts", CABECALHO_PROVENANCE,
                     RAIZ / "PROVENANCE.md")
    return codigo


if __name__ == "__main__":
    raise SystemExit(main())
