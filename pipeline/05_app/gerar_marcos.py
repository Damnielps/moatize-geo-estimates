#!/usr/bin/env python3
"""pipeline/05_app/gerar_marcos.py — linha do tempo de marcos (eventos) em JSON.

Fase 4b: Lê config/marcos.yaml, valida schema e semântica, calcula anos decimais para
posicionar na trilha do slider, e grava data/processed/app/marcos.json com hash do
YAML para detectar desatualização.

Validação:
- ids únicos (fases e marcos)
- tipos em conjunto fixo {concessao, licenca, obras, operacao, reassentamento,
  preco, logistica, saida, censo}
- níveis em {A, B, C, secundario}
- datas parseáveis (AAAA, AAAA-MM, AAAA-MM-DD ou null)
- fim >= inicio quando ambas presentes
- fonte e url não vazios para marcos
- fases contíguas (fim de uma = inicio da próxima) e sem sobreposição
- anos decimais em [1997, 2041]

Saída (determinística, sem data de geração):
  data/processed/app/marcos.json — JSON com ensure_ascii=False, indent=2, chaves
  ordenadas, \\n final; ordenado por ano_inicio (depois id).

Depende de:
- config/marcos.yaml (consumido; seu sha256 entra no JSON)
- nenhuma fonte externa
"""

import json
import sys
from hashlib import sha256
from pathlib import Path

import yaml


def load_yaml(path):
    """Carrega YAML com suporte a None literal."""
    with open(path, encoding="utf-8") as f:
        return yaml.safe_load(f)


def parse_data(date_str):
    """
    Parse data em AAAA, AAAA-MM ou AAAA-MM-DD; retorna (ano, mês, dia) ou None.
    Valida que ano está em [1997, 2041].
    """
    if date_str is None:
        return None
    date_str = str(date_str).strip()
    if not date_str:
        return None

    parts = date_str.split("-")
    if len(parts) == 1:
        try:
            ano = int(parts[0])
            if not 1997 <= ano <= 2041:
                raise ValueError(f"Ano {ano} fora do intervalo [1997, 2041]")
            return (ano, None, None)
        except ValueError as e:
            raise ValueError(f"Data '{date_str}': {e}") from e
    elif len(parts) == 2:
        try:
            ano, mes = int(parts[0]), int(parts[1])
            if not 1997 <= ano <= 2041:
                raise ValueError(f"Ano {ano} fora do intervalo [1997, 2041]")
            if not 1 <= mes <= 12:
                raise ValueError(f"Mês {mes} inválido (deve estar em [1, 12])")
            return (ano, mes, None)
        except ValueError as e:
            raise ValueError(f"Data '{date_str}': {e}") from e
    elif len(parts) == 3:
        try:
            ano, mes, dia = int(parts[0]), int(parts[1]), int(parts[2])
            if not 1997 <= ano <= 2041:
                raise ValueError(f"Ano {ano} fora do intervalo [1997, 2041]")
            # Valida que mês e dia formam uma data válida
            if not 1 <= mes <= 12:
                raise ValueError(f"Mês {mes} inválido")
            # Simples checagem de dia (sem validação de bissexto aqui)
            if not 1 <= dia <= 31:
                raise ValueError(f"Dia {dia} inválido")
            return (ano, mes, dia)
        except ValueError as e:
            raise ValueError(f"Data '{date_str}': {e}") from e
    else:
        raise ValueError(f"Data '{date_str}': formato inválido (esperado AAAA[-MM[-DD]])")


def data_para_decimal(data_tuple):
    """Converte (ano, mês, dia) para ano decimal. None retorna None."""
    if data_tuple is None:
        return None
    ano, mes, dia = data_tuple
    if mes is None:
        return float(ano) + 0.5
    if dia is None:
        return float(ano) + (mes - 0.5) / 12.0
    # Com dia: posiciona no meio do mês
    return float(ano) + (mes - 0.5) / 12.0


def validate_marcos(marcos):
    """Valida lista de marcos."""
    ids = set()
    tipos_validos = {
        "concessao", "licenca", "obras", "operacao", "reassentamento",
        "preco", "logistica", "saida", "censo"
    }
    niveis_validos = {"A", "B", "C", "secundario"}

    for i, marco in enumerate(marcos):
        # ID único
        if "id" not in marco or not marco["id"]:
            raise ValueError(f"Marco índice {i}: 'id' ausente ou vazio")
        id_val = marco["id"]
        if id_val in ids:
            raise ValueError(f"Marco '{id_val}': id duplicado")
        ids.add(id_val)

        # Tipo válido
        if "tipo" not in marco:
            raise ValueError(f"Marco '{id_val}': 'tipo' ausente")
        tipo = marco["tipo"]
        if tipo not in tipos_validos:
            msg = f"Marco '{id_val}': tipo '{tipo}' inválido (esperado um dos tipos)"
            raise ValueError(msg)

        # Nível válido
        if "nivel" not in marco:
            raise ValueError(f"Marco '{id_val}': 'nivel' ausente")
        nivel = marco["nivel"]
        if nivel not in niveis_validos:
            msg = f"Marco '{id_val}': nivel '{nivel}' inválido (esperado um dos níveis)"
            raise ValueError(msg)

        # Datas
        inicio = marco.get("inicio")
        fim = marco.get("fim")

        inicio_data = parse_data(inicio)
        fim_data = parse_data(fim)

        # fim >= inicio
        if inicio_data is not None and fim_data is not None:
            if fim_data < inicio_data:
                raise ValueError(f"Marco '{id_val}': fim ({fim}) < inicio ({inicio})")

        # Fonte e URL não vazios para marcos
        if "fonte" not in marco or not marco["fonte"]:
            raise ValueError(f"Marco '{id_val}': 'fonte' ausente ou vazio")
        if "url" not in marco or not marco["url"]:
            raise ValueError(f"Marco '{id_val}': 'url' ausente ou vazio")

    return ids


def validate_fases(fases, marco_ids):
    """Valida lista de fases. marco_ids é recebido mas não usado (contrato)."""
    ids = set()

    fases_sorted = sorted(fases, key=lambda f: f["inicio"])

    for i, fase in enumerate(fases_sorted):
        # ID único
        if "id" not in fase or not fase["id"]:
            raise ValueError(f"Fase índice {i}: 'id' ausente ou vazio")
        id_val = fase["id"]
        if id_val in ids:
            raise ValueError(f"Fase '{id_val}': id duplicado")
        ids.add(id_val)

        # Datas (para fases, devem estar sempre presentes)
        inicio = parse_data(fase.get("inicio"))
        fim = parse_data(fase.get("fim"))

        if inicio is None:
            raise ValueError(f"Fase '{id_val}': 'inicio' não pode ser null")
        if fim is None:
            raise ValueError(f"Fase '{id_val}': 'fim' não pode ser null")
        if fim < inicio:
            msg = f"Fase '{id_val}': fim ({fase['fim']}) < inicio ({fase['inicio']})"
            raise ValueError(msg)

        # Contiguidade e sem sobreposição
        if i < len(fases_sorted) - 1:
            prox_fase = fases_sorted[i + 1]
            prox_inicio = parse_data(prox_fase.get("inicio"))
            if fim != prox_inicio:
                msg = (
                    f"Fase '{id_val}' (fim {fase['fim']}) não é contígua com "
                    f"'{prox_fase['id']}' (inicio {prox_fase['inicio']})"
                )
                raise ValueError(msg)

    return ids


def compute_json(config_path):
    """Carrega YAML, valida, calcula anos decimais, monta JSON."""
    config = load_yaml(config_path)

    if "fases" not in config or "marcos" not in config:
        raise ValueError("YAML deve conter 'fases' e 'marcos'")

    fases = config["fases"]
    marcos = config["marcos"]

    # Validar
    marco_ids = validate_marcos(marcos)
    validate_fases(fases, marco_ids)

    # Processar fases
    fases_out = []
    for fase in fases:
        inicio = parse_data(fase.get("inicio"))
        fim = parse_data(fase.get("fim"))
        fases_out.append({
            "id": fase["id"],
            "inicio": fase.get("inicio"),
            "fim": fase.get("fim"),
            "ano_inicio": data_para_decimal(inicio),
            "ano_fim": data_para_decimal(fim),
            "rotulo_pt": fase.get("rotulo_pt", ""),
            "rotulo_en": fase.get("rotulo_en", ""),
        })

    # Processar marcos (e sort por ano_inicio depois id)
    marcos_out = []
    for marco in marcos:
        inicio = parse_data(marco.get("inicio"))
        fim = parse_data(marco.get("fim"))
        marcos_out.append({
            "id": marco["id"],
            "inicio": marco.get("inicio"),
            "fim": marco.get("fim"),
            "ano_inicio": data_para_decimal(inicio),
            "ano_fim": data_para_decimal(fim),
            "tipo": marco["tipo"],
            "rotulo_pt": marco.get("rotulo_pt", ""),
            "rotulo_en": marco.get("rotulo_en", ""),
            "fonte": marco["fonte"],
            "url": marco["url"],
            "nivel": marco["nivel"],
            "verificado_em": marco.get("verificado_em", ""),
            "nota": marco.get("nota", ""),
        })

    marcos_out.sort(
        key=lambda m: (m["ano_inicio"] if m["ano_inicio"] is not None else 9999, m["id"])
    )

    # Calcular SHA256 do YAML
    with open(config_path, "rb") as f:
        yaml_sha256 = sha256(f.read()).hexdigest()

    # Montar output
    output = {
        "gerado_por": "pipeline/05_app/gerar_marcos.py",
        "sha256_config": yaml_sha256,
        "fases": fases_out,
        "marcos": marcos_out,
    }

    return output


def main():
    """Entrada principal."""
    repo_root = Path(__file__).parent.parent.parent
    config_path = repo_root / "config" / "marcos.yaml"
    output_dir = repo_root / "data" / "processed" / "app"
    output_path = output_dir / "marcos.json"

    if not config_path.exists():
        print(f"ERRO: {config_path} não encontrado", file=sys.stderr)
        sys.exit(1)

    try:
        data = compute_json(config_path)
    except Exception as e:
        print(f"ERRO ao processar {config_path}: {e}", file=sys.stderr)
        sys.exit(1)

    # Garantir diretório
    output_dir.mkdir(parents=True, exist_ok=True)

    # Gravar JSON determinístico
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2, sort_keys=True)
        f.write("\n")  # Final newline

    print(f"✓ {output_path}")
    print(f"  fases: {len(data['fases'])}, marcos: {len(data['marcos'])}")
    print(f"  sha256(config): {data['sha256_config'][:16]}...")


if __name__ == "__main__":
    main()
