#!/usr/bin/env python3
"""Verifica que nenhum commit descartado por reescrita continua recuperável no servidor.

Reescrever o histórico e forçar o push **não apaga os objetos antigos do GitHub**. Eles
continuam alcançáveis enquanto alguma referência do lado do servidor os segurar —
tipicamente `refs/pull/<n>/head`, que sobrevive ao fechamento do PR e à remoção da branch,
e que nenhum push do dono remove. Foi o que aconteceu aqui (ORCHESTRATION_LOG 4b-29 e
4b-30): `main` ficou limpa, e o e-mail pessoal seguiu publicamente recuperável por quem
tivesse o SHA.

Este script transforma essa checagem em contrato. Ele responde a uma pergunta que
`git log` na árvore local não responde, porque a resposta está no servidor:

1. Nenhuma referência remota (`git ls-remote`) aponta para um commit da lista de
   descartados de `config/commits_obsoletos.yaml`.
2. Nenhum commit descartado resolve pela API do GitHub — nem os do histórico antigo, nem
   os heads de PR que os ancoravam.
3. Toda `refs/pull/*` que ainda exista tem o pai dentro do histórico de `main` — ou seja,
   nasceu do histórico atual e não ressuscita nenhum outro.

Uso:

    uv run python scripts/verificar_exposicao.py
    uv run python scripts/verificar_exposicao.py --repo Damnielps/moatize-geo-estimates

rc=0 quando nada está exposto; rc=1 quando algo está (com a lista do que está); rc=2 em
erro de configuração ou de rede — um erro de rede **não** é tratado como ausência de
exposição, que é a falha que deixaria um "verde" falso passar.
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
import urllib.error
import urllib.request
from dataclasses import dataclass, field
from pathlib import Path

import yaml

RAIZ = Path(__file__).resolve().parent.parent
CONFIG = RAIZ / "config" / "commits_obsoletos.yaml"
API = "https://api.github.com/repos/{repo}/commits/{sha}"


class ErroDeVerificacao(RuntimeError):
    """Não foi possível concluir a verificação (rede, configuração, git)."""


@dataclass
class Resultado:
    expostos: list[str] = field(default_factory=list)
    conferidos: int = 0
    refs_remotas: int = 0
    notas: list[str] = field(default_factory=list)

    @property
    def limpo(self) -> bool:
        return not self.expostos


def shas_descartados(config: Path = CONFIG) -> list[str]:
    """Todos os SHAs que não podem mais resolver: histórico antigo + heads de PR."""
    dados = yaml.safe_load(config.read_text(encoding="utf-8"))
    shas = [c["sha"] for r in dados.get("reescritas", []) for c in r.get("commits", [])]
    shas += [p["sha"] for p in dados.get("refs_pull_ancoradas", [])]
    if not shas:
        raise ErroDeVerificacao(f"{config} não lista nenhum commit descartado")
    return shas


def ls_remote(remoto: str) -> dict[str, str]:
    """Mapa ref -> sha do servidor. Falha alto: sem isso não há verificação."""
    try:
        saida = subprocess.run(
            ["git", "ls-remote", remoto],
            cwd=RAIZ,
            capture_output=True,
            text=True,
            check=True,
            timeout=60,
        ).stdout
    except (subprocess.CalledProcessError, subprocess.TimeoutExpired) as erro:
        raise ErroDeVerificacao(f"git ls-remote {remoto} falhou: {erro}") from erro
    pares = (linha.split("\t") for linha in saida.splitlines() if "\t" in linha)
    return {ref: sha for sha, ref in pares}


def commit_na_api(repo: str, sha: str) -> dict | None:
    """O commit como a API devolve, ou None se ela não o entrega (404/422)."""
    req = urllib.request.Request(
        API.format(repo=repo, sha=sha),
        headers={"Accept": "application/vnd.github+json", "User-Agent": "verificar-exposicao"},
    )
    try:
        with urllib.request.urlopen(req, timeout=30) as resposta:
            return json.load(resposta)
    except urllib.error.HTTPError as erro:
        if erro.code in (404, 422):
            return None
        if erro.code == 403:
            raise ErroDeVerificacao(
                "API do GitHub recusou (403) — provável limite de taxa por IP. "
                "Repita mais tarde: um 403 não prova que o commit sumiu."
            ) from erro
        raise ErroDeVerificacao(f"API do GitHub devolveu {erro.code} para {sha[:7]}") from erro
    except urllib.error.URLError as erro:
        raise ErroDeVerificacao(f"rede indisponível ao consultar {sha[:7]}: {erro}") from erro


def commits_de_main() -> set[str]:
    try:
        saida = subprocess.run(
            ["git", "log", "--format=%H", "main"],
            cwd=RAIZ,
            capture_output=True,
            text=True,
            check=True,
        ).stdout
    except subprocess.CalledProcessError as erro:
        raise ErroDeVerificacao(f"git log main falhou: {erro}") from erro
    return set(saida.split())


def verificar(repo: str, remoto: str) -> Resultado:
    res = Resultado()
    descartados = set(shas_descartados())

    refs = ls_remote(remoto)
    res.refs_remotas = len(refs)
    for ref, sha in refs.items():
        if sha in descartados:
            res.expostos.append(f"{ref} aponta para o commit descartado {sha[:7]}")

    for sha in sorted(descartados):
        res.conferidos += 1
        if commit_na_api(repo, sha) is not None:
            res.expostos.append(f"a API do GitHub ainda entrega o commit descartado {sha}")

    vivos = commits_de_main()
    for ref, sha in refs.items():
        if not ref.startswith("refs/pull/"):
            continue
        dados = commit_na_api(repo, sha)
        if dados is None:
            res.notas.append(f"{ref}: head {sha[:7]} não resolve na API (ref órfã)")
            continue
        for pai in (p["sha"] for p in dados.get("parents", [])):
            if pai not in vivos:
                res.expostos.append(
                    f"{ref} nasce de {pai[:7]}, que não está no histórico de main — "
                    "essa ref ancora um histórico descartado"
                )
    return res


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    ap.add_argument("--repo", default="Damnielps/moatize-geo-estimates", help="owner/repo")
    ap.add_argument("--remoto", default="origin", help="remoto git a consultar")
    args = ap.parse_args(argv)

    try:
        res = verificar(args.repo, args.remoto)
    except ErroDeVerificacao as erro:
        print(f"VERIFICAÇÃO INCONCLUSIVA: {erro}", file=sys.stderr)
        return 2

    for nota in res.notas:
        print(f"nota: {nota}")
    print(
        f"referências remotas: {res.refs_remotas}"
        f" · commits descartados conferidos: {res.conferidos}"
    )

    if res.limpo:
        print("LIMPO: nenhum commit descartado é alcançável no servidor.")
        return 0
    print("\nEXPOSTO:", file=sys.stderr)
    for item in res.expostos:
        print(f"  - {item}", file=sys.stderr)
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
