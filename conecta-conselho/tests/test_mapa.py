"""
Testes unitários para as funções puras de mapa.py:
  - calcular_coordenadas: conversão de (distância, ângulo) → (x, y)
  - carregar_angulos: leitura do JSON de ângulos ilustrativos
"""

from __future__ import annotations

import json
import math
import tempfile
from pathlib import Path

import pytest

# Importa diretamente as funções puras (sem Streamlit)
from paginas.mapa import calcular_coordenadas, carregar_angulos  # type: ignore[import]


# ---------------------------------------------------------------------------
# calcular_coordenadas
# ---------------------------------------------------------------------------

class TestCalcularCoordenadas:
    """Testa a conversão polar → cartesiana."""

    def test_angulo_zero_aponta_para_leste(self):
        x, y = calcular_coordenadas(10.0, 0.0)
        assert math.isclose(x, 10.0, abs_tol=1e-9)
        assert math.isclose(y,  0.0, abs_tol=1e-9)

    def test_angulo_90_aponta_para_norte(self):
        x, y = calcular_coordenadas(10.0, 90.0)
        assert math.isclose(x,  0.0, abs_tol=1e-9)
        assert math.isclose(y, 10.0, abs_tol=1e-9)

    def test_angulo_180_aponta_para_oeste(self):
        x, y = calcular_coordenadas(10.0, 180.0)
        assert math.isclose(x, -10.0, abs_tol=1e-9)
        assert math.isclose(y,   0.0, abs_tol=1e-9)

    def test_angulo_270_aponta_para_sul(self):
        x, y = calcular_coordenadas(10.0, 270.0)
        assert math.isclose(x,  0.0, abs_tol=1e-9)
        assert math.isclose(y, -10.0, abs_tol=1e-9)

    def test_distancia_zero_retorna_origem(self):
        x, y = calcular_coordenadas(0.0, 45.0)
        assert math.isclose(x, 0.0, abs_tol=1e-9)
        assert math.isclose(y, 0.0, abs_tol=1e-9)

    def test_distancia_preservada(self):
        """A distância euclidiana deve ser igual ao raio de entrada."""
        for dist in (1, 10, 50, 98):
            for ang in (0, 30, 60, 90, 120, 200, 320):
                x, y = calcular_coordenadas(float(dist), float(ang))
                distancia_calculada = math.hypot(x, y)
                assert math.isclose(distancia_calculada, dist, abs_tol=1e-9), (
                    f"dist={dist}, ang={ang} → hypot={distancia_calculada}"
                )

    def test_angulo_45_diagonal(self):
        """A 45° x e y devem ser iguais (e positivos)."""
        x, y = calcular_coordenadas(10.0, 45.0)
        assert math.isclose(x, y, abs_tol=1e-9)
        assert x > 0 and y > 0

    def test_retorna_tupla_de_dois_floats(self):
        resultado = calcular_coordenadas(18.0, 20.0)
        assert isinstance(resultado, tuple)
        assert len(resultado) == 2
        assert all(isinstance(v, float) for v in resultado)

    @pytest.mark.parametrize("distancia,angulo,exp_x,exp_y", [
        (18.0,  20.0, 18.0 * math.cos(math.radians(20.0)),  18.0 * math.sin(math.radians(20.0))),
        (35.0,  80.0, 35.0 * math.cos(math.radians(80.0)),  35.0 * math.sin(math.radians(80.0))),
        (62.0, 140.0, 62.0 * math.cos(math.radians(140.0)), 62.0 * math.sin(math.radians(140.0))),
        ( 8.0, 200.0,  8.0 * math.cos(math.radians(200.0)),  8.0 * math.sin(math.radians(200.0))),
        (28.0, 260.0, 28.0 * math.cos(math.radians(260.0)), 28.0 * math.sin(math.radians(260.0))),
        (98.0, 320.0, 98.0 * math.cos(math.radians(320.0)), 98.0 * math.sin(math.radians(320.0))),
    ])
    def test_coordenadas_das_regioes_reais(self, distancia, angulo, exp_x, exp_y):
        """Verifica coordenadas para os dados reais das 6 regiões simuladas."""
        x, y = calcular_coordenadas(distancia, angulo)
        assert math.isclose(x, exp_x, abs_tol=1e-9)
        assert math.isclose(y, exp_y, abs_tol=1e-9)


# ---------------------------------------------------------------------------
# carregar_angulos
# ---------------------------------------------------------------------------

class TestCarregarAngulos:
    """Testa a leitura do JSON de ângulos ilustrativos."""

    def _json_temporario(self, conteudo: dict) -> Path:
        """Cria um arquivo JSON temporário e devolve o caminho."""
        tmp = tempfile.NamedTemporaryFile(
            mode="w", suffix=".json", delete=False, encoding="utf-8"
        )
        json.dump(conteudo, tmp, ensure_ascii=False)
        tmp.close()
        return Path(tmp.name)

    def test_carrega_angulos_corretos(self):
        dados = {
            "aviso": "teste",
            "angulos": {"aurora": 20, "horizonte": 80, "central": 200},
        }
        caminho = self._json_temporario(dados)
        angulos = carregar_angulos(caminho)
        assert angulos == {"aurora": 20.0, "horizonte": 80.0, "central": 200.0}
        caminho.unlink()

    def test_retorna_floats(self):
        dados = {"aviso": "x", "angulos": {"r1": 90, "r2": 180}}
        caminho = self._json_temporario(dados)
        angulos = carregar_angulos(caminho)
        for v in angulos.values():
            assert isinstance(v, float)
        caminho.unlink()

    def test_arquivo_real_tem_seis_regioes(self):
        """O mapa_ilustrativo.json real deve conter exatamente 6 regiões."""
        angulos = carregar_angulos()   # usa o caminho padrão
        assert len(angulos) == 6

    def test_arquivo_real_contem_ids_esperados(self):
        """Verifica que os IDs das regiões simuladas estão todos presentes."""
        ids_esperados = {"aurora", "horizonte", "esperanca", "central", "vale_verde", "nova_uniao"}
        angulos = carregar_angulos()
        assert set(angulos.keys()) == ids_esperados

    def test_arquivo_real_angulos_entre_0_e_360(self):
        angulos = carregar_angulos()
        for rid, ang in angulos.items():
            assert 0 <= ang < 360, f"Ângulo fora do intervalo para {rid}: {ang}"

    def test_arquivo_ausente_levanta_file_not_found(self):
        with pytest.raises(FileNotFoundError):
            carregar_angulos(Path("/caminho/inexistente/mapa.json"))

    def test_json_sem_chave_angulos_levanta_key_error(self):
        dados = {"aviso": "sem angulos"}
        caminho = self._json_temporario(dados)
        with pytest.raises(KeyError):
            carregar_angulos(caminho)
        caminho.unlink()
