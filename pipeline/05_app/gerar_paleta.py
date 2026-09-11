#!/usr/bin/env python3
"""pipeline/05_app/gerar_paleta.py — paleta das classes de uso do solo para o app (ADR 0018).

Lê `config/paleta_uso_solo.yaml` (fonte única das cores de classe: legenda ESA WorldCover /
FAO LCCS, com adaptações declaradas) e grava `app/src/content/paleta_uso_solo.json`, que o
front-end importa (`app/src/lib/camadasBase.js`). Nenhuma cor de classe é escrita à mão no app.

Validação (falha com código 1, sem gravar):
- toda classe tem `cor` em hex `#RRGGBB`, `origem` em {worldcover, adaptacao} e
  `classe_worldcover`; `contorno`, quando houver, também em hex;
- toda classe `origem: adaptacao` tem `nota` (a adaptação é declarada, nunca implícita);
- `opacidade`, quando houver, em (0, 1];
- `industrial` não tem cor nem contorno vermelhos (CLAUDE.md §10: cava de mina não é área
  urbana; o vermelho é o Built-up da WorldCover);
- toda chave de `contexto` é hex.

Saída (determinística, sem data de geração): JSON com `ensure_ascii=False`, `indent=2`,
chaves ordenadas, `\\n` final; `sha256_config` é o sha256 dos bytes do YAML, para o teste
detectar JSON desatualizado (`pipeline/tests/test_paleta.py`).
"""

import colorsys
import json
import re
import sys
from hashlib import sha256
from pathlib import Path

import yaml

RAIZ = Path(__file__).resolve().parents[2]
ENTRADA = RAIZ / "config" / "paleta_uso_solo.yaml"
SAIDA = RAIZ / "app" / "src" / "content" / "paleta_uso_solo.json"

HEX = re.compile(r"^#[0-9A-Fa-f]{6}$")
ORIGENS = {"worldcover", "adaptacao"}


def eh_vermelho(hex_cor: str) -> bool:
    """Matiz a até 30° do vermelho, com saturação e brilho perceptíveis.

    Critério do teste de §10 (`industrial` nunca vermelho), repetido aqui para o gerador
    recusar a paleta antes de o app a publicar.
    """
    r, g, b = (int(hex_cor[i : i + 2], 16) / 255 for i in (1, 3, 5))
    h, s, v = colorsys.rgb_to_hsv(r, g, b)
    graus = h * 360
    return s >= 0.25 and v >= 0.2 and (graus <= 30 or graus >= 330)


def validar(paleta: dict) -> list[str]:
    erros = []
    classes = paleta.get("classes") or {}
    if not classes:
        erros.append("sem seção `classes`")
    for nome, c in classes.items():
        cor = str(c.get("cor", ""))
        if not HEX.match(cor):
            erros.append(f"{nome}: cor inválida {cor!r}")
        if c.get("origem") not in ORIGENS:
            erros.append(f"{nome}: origem {c.get('origem')!r} fora de {sorted(ORIGENS)}")
        if not c.get("classe_worldcover"):
            erros.append(f"{nome}: sem classe_worldcover")
        if "contorno" in c and not HEX.match(str(c["contorno"])):
            erros.append(f"{nome}: contorno inválido {c['contorno']!r}")
        if c.get("origem") == "adaptacao" and not str(c.get("nota", "")).strip():
            erros.append(f"{nome}: adaptação sem `nota`")
        if "opacidade" in c and not (0 < float(c["opacidade"]) <= 1):
            erros.append(f"{nome}: opacidade fora de (0, 1]")
        for chave in ("rotulo_pt", "rotulo_en"):
            if not str(c.get(chave, "")).strip():
                erros.append(f"{nome}: sem {chave}")
    ind = classes.get("industrial", {})
    for chave in ("cor", "contorno"):
        valor = str(ind.get(chave, ""))
        if HEX.match(valor) and eh_vermelho(valor):
            erros.append(f"industrial.{chave} = {valor} é vermelho (CLAUDE.md §10)")
    for nome, valor in (paleta.get("contexto") or {}).items():
        if not HEX.match(str(valor)):
            erros.append(f"contexto.{nome}: cor inválida {valor!r}")
    return erros


def gerar() -> dict:
    bruto = ENTRADA.read_bytes()
    paleta = yaml.safe_load(bruto.decode("utf-8"))
    erros = validar(paleta)
    if erros:
        for e in erros:
            print(f"[gerar_paleta] ERRO: {e}", file=sys.stderr)
        sys.exit(1)
    return {
        "gerado_por": "pipeline/05_app/gerar_paleta.py",
        "fonte": "config/paleta_uso_solo.yaml",
        "adr": "docs/ADR/0018-paleta-uso-do-solo-worldcover.md",
        "sha256_config": sha256(bruto).hexdigest(),
        "padrao": paleta["padrao"],
        "classes": paleta["classes"],
        "contexto": paleta["contexto"],
    }


def main() -> None:
    saida = gerar()
    texto = json.dumps(saida, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    SAIDA.parent.mkdir(parents=True, exist_ok=True)
    SAIDA.write_text(texto, encoding="utf-8")
    print(f"[gerar_paleta] {len(saida['classes'])} classes -> {SAIDA.relative_to(RAIZ)}")


if __name__ == "__main__":
    main()
