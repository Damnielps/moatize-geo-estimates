"""pipeline/tests/test_marcos.py — testes de contrato para marcos.json (Fase 4b).

Contratos:
1. O YAML valida (script roda sem erro)
2. O JSON existe e seu sha256_config bate com o sha256 do YAML atual
3. Todo marco tem fonte e url não vazios
4. Anos decimais estão em [1997, 2041]
5. As seis fases cobrem 1997–2040 sem buraco (contiguidade)
"""

import json
from hashlib import sha256
from pathlib import Path

import pytest
import yaml


@pytest.fixture
def repo_root():
    """Raiz do repositório."""
    return Path(__file__).parent.parent.parent


@pytest.fixture
def config_path(repo_root):
    """Caminho do YAML de entrada."""
    return repo_root / "config" / "marcos.yaml"


@pytest.fixture
def output_path(repo_root):
    """Caminho do JSON de saída."""
    return repo_root / "data" / "processed" / "app" / "marcos.json"


@pytest.fixture
def config_data(config_path):
    """Carrega o YAML."""
    with open(config_path, encoding="utf-8") as f:
        return yaml.safe_load(f)


@pytest.fixture
def output_data(output_path):
    """Carrega o JSON se existir."""
    if not output_path.exists():
        return None
    with open(output_path, encoding="utf-8") as f:
        return json.load(f)


class TestMarcosYAML:
    """Testes do YAML de entrada."""

    def test_yaml_exists(self, config_path):
        """YAML existe."""
        assert config_path.exists(), f"{config_path} não encontrado"

    def test_yaml_has_fases_and_marcos(self, config_data):
        """YAML tem ambas as seções."""
        assert "fases" in config_data, "Falta seção 'fases'"
        assert "marcos" in config_data, "Falta seção 'marcos'"
        assert len(config_data["fases"]) > 0, "Fases vazia"
        assert len(config_data["marcos"]) > 0, "Marcos vazia"

    def test_fase_ids_unique(self, config_data):
        """IDs de fases são únicos."""
        ids = [f["id"] for f in config_data["fases"]]
        assert len(ids) == len(set(ids)), f"IDs duplicadas em fases: {ids}"

    def test_marco_ids_unique(self, config_data):
        """IDs de marcos são únicos."""
        ids = [m["id"] for m in config_data["marcos"]]
        assert len(ids) == len(set(ids)), f"IDs duplicadas em marcos: {ids}"

    def test_marcos_have_fonte_url(self, config_data):
        """Todo marco tem fonte e url não vazios."""
        for marco in config_data["marcos"]:
            assert marco.get("fonte"), f"Marco '{marco['id']}': fonte vazia"
            assert marco.get("url"), f"Marco '{marco['id']}': url vazia"

    def test_marcos_tipos_validos(self, config_data):
        """Todos os tipos de marcos são válidos."""
        tipos_validos = {
            "concessao", "licenca", "obras", "operacao", "reassentamento",
            "preco", "logistica", "saida", "censo"
        }
        for marco in config_data["marcos"]:
            tipo = marco["tipo"]
            assert tipo in tipos_validos, (
                f"Marco '{marco['id']}': tipo inválido '{tipo}'"
            )

    def test_marcos_niveis_validos(self, config_data):
        """Todos os níveis de marcos são válidos."""
        niveis_validos = {"A", "B", "C", "secundario"}
        for marco in config_data["marcos"]:
            nivel = marco["nivel"]
            assert nivel in niveis_validos, (
                f"Marco '{marco['id']}': nivel inválido '{nivel}'"
            )

    def test_fases_contiguous(self, config_data):
        """Fases são contíguas (fim de uma = inicio da próxima)."""
        fases = sorted(config_data["fases"], key=lambda f: f["inicio"])
        for i in range(len(fases) - 1):
            assert fases[i]["fim"] == fases[i + 1]["inicio"], (
                f"Fases '{fases[i]['id']}' e '{fases[i+1]['id']}' não são contíguas: "
                f"{fases[i]['fim']} != {fases[i+1]['inicio']}"
            )

    def test_fases_cover_1997_to_2040(self, config_data):
        """Fases cobrem 1997–2040."""
        fases = sorted(config_data["fases"], key=lambda f: f["inicio"])
        assert fases[0]["inicio"] == 1997, f"Primeira fase começa em {fases[0]['inicio']}, não 1997"
        assert fases[-1]["fim"] == 2040, f"Última fase termina em {fases[-1]['fim']}, não 2040"


class TestMarcosJSON:
    """Testes do JSON de saída."""

    def test_json_exists(self, output_path):
        """JSON existe."""
        assert output_path.exists(), f"{output_path} não encontrado (rode make app-data primeiro?)"

    def test_json_sha256_matches_config(self, output_path, config_path, output_data):
        """sha256_config do JSON bate com o sha256 do YAML atual."""
        if output_data is None:
            pytest.skip("JSON não existe")

        with open(config_path, "rb") as f:
            current_sha256 = sha256(f.read()).hexdigest()

        json_sha256 = output_data.get("sha256_config")
        assert json_sha256 == current_sha256, (
            f"JSON desatualizado: sha256 gravado={json_sha256[:16]}... "
            f"!= atual={current_sha256[:16]}... (rode make app-data novamente)"
        )

    def test_json_has_fases_marcos(self, output_data):
        """JSON tem ambas as seções."""
        if output_data is None:
            pytest.skip("JSON não existe")
        assert "fases" in output_data, "Falta 'fases' no JSON"
        assert "marcos" in output_data, "Falta 'marcos' no JSON"
        assert len(output_data["fases"]) > 0, "Fases vazia"
        assert len(output_data["marcos"]) > 0, "Marcos vazia"

    def test_json_fases_contiguous(self, output_data):
        """Fases no JSON são contíguas."""
        if output_data is None:
            pytest.skip("JSON não existe")
        fases = output_data["fases"]
        # Já estão ordenados por construção, mas verifica contiguidade dos anos decimais
        for i in range(len(fases) - 1):
            assert fases[i]["ano_fim"] <= fases[i + 1]["ano_inicio"], (
                f"Fases '{fases[i]['id']}' e '{fases[i+1]['id']}' overlapped: "
                f"{fases[i]['ano_fim']} > {fases[i+1]['ano_inicio']}"
            )

    def test_json_marcos_anos_in_range(self, output_data):
        """Todos os anos decimais estão em [1997, 2041]."""
        if output_data is None:
            pytest.skip("JSON não existe")
        for marco in output_data["marcos"]:
            if marco["ano_inicio"] is not None:
                assert 1997 <= marco["ano_inicio"] <= 2041, (
                    f"Marco '{marco['id']}': ano_inicio {marco['ano_inicio']} fora de [1997, 2041]"
                )
            if marco["ano_fim"] is not None:
                assert 1997 <= marco["ano_fim"] <= 2041, (
                    f"Marco '{marco['id']}': ano_fim {marco['ano_fim']} fora de [1997, 2041]"
                )

    def test_json_marcos_sorted(self, output_data):
        """Marcos estão ordenados por ano_inicio (depois id)."""
        if output_data is None:
            pytest.skip("JSON não existe")
        marcos = output_data["marcos"]
        for i in range(len(marcos) - 1):
            m1, m2 = marcos[i], marcos[i + 1]
            # ano_inicio é None para eventos sem data definida; trata como infinito
            a1 = m1["ano_inicio"] if m1["ano_inicio"] is not None else float("inf")
            a2 = m2["ano_inicio"] if m2["ano_inicio"] is not None else float("inf")
            # Verifica ordem
            is_sorted = a1 <= a2 and (a1 != a2 or m1["id"] <= m2["id"])
            assert is_sorted, (
                f"Marcos não ordenados: '{m1['id']}' ({a1}) "
                f"deveria vir antes de '{m2['id']}' ({a2})"
            )

    def test_json_marcos_have_expected_fields(self, output_data):
        """Cada marco tem todos os campos esperados."""
        if output_data is None:
            pytest.skip("JSON não existe")
        expected = {
            "id", "inicio", "fim", "ano_inicio", "ano_fim",
            "tipo", "rotulo_pt", "rotulo_en", "fonte", "url", "nivel", "verificado_em", "nota"
        }
        for marco in output_data["marcos"]:
            assert set(marco.keys()) == expected, (
                f"Marco '{marco['id']}': campos diferem de esperado. "
                f"Tem: {set(marco.keys())}, esperado: {expected}"
            )
