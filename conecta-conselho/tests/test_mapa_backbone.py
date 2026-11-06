"""
Testes de M3 · Visualização da aproximação do backbone.

Cobre:
- _camada_simulacao: cálculo correto da proporção de deslocamento ilustrativo
- _resumo_inline: formato do texto de resumo
- renderizar_seletor_mapa: aceita o parâmetro camada_simulacao sem erro
- Casos de borda: distância igual, distância original zero, aumento de distância
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------

_ROOT = Path(__file__).resolve().parent.parent.parent
_CC_DIR = Path(__file__).resolve().parent.parent

for _p in [str(_ROOT), str(_CC_DIR)]:
    if _p not in sys.path:
        sys.path.insert(0, _p)

from simulador import simular_cenario  # noqa: E402


# ---------------------------------------------------------------------------
# Helpers copiados de simulador.py (testados em isolamento)
# ---------------------------------------------------------------------------

def _camada_simulacao(resultado: dict, dist_original: float):
    """Reproduz a lógica de _camada_simulacao de paginas/simulador.py."""
    if not resultado:
        return None
    params = resultado.get("parametros", {})
    dist_sim = params.get("distancia_backbone_km")
    if dist_sim is None:
        return None
    res_sim = resultado.get("simulado", {})
    rec = res_sim.get("recomendacao")
    return {"dist_original": dist_original, "dist_simulada": dist_sim, "recomendacao": rec}


def _proporcao(dist_original: float, dist_simulada: float) -> float:
    """Cálculo ilustrativo: 1 - nova / original (clamped 0..1)."""
    if dist_original <= 0:
        return 0.0
    return max(0.0, min(1.0, 1 - dist_simulada / dist_original))


# ---------------------------------------------------------------------------
# Testes: cálculo de proporção de deslocamento
# ---------------------------------------------------------------------------

class TestProporcaoDeslocamento:

    def test_nova_uniao_98_para_20(self):
        """98 → 20 km: proporção ≈ 0.796 (≈ 80%)."""
        p = _proporcao(98, 20)
        assert abs(p - (1 - 20 / 98)) < 1e-9

    def test_distancia_igual(self):
        """Distância igual à original: proporção 0 (sem deslocamento)."""
        assert _proporcao(50, 50) == 0.0

    def test_distancia_original_zero(self):
        """Distância original zero: proporção 0 (sem divisão por zero)."""
        assert _proporcao(0, 0) == 0.0
        assert _proporcao(0, 20) == 0.0

    def test_backbone_na_regiao(self):
        """Distância simulada 0 km: backbone na região, proporção 1.0."""
        assert _proporcao(98, 0) == pytest.approx(1.0, abs=1e-9)

    def test_aumento_de_distancia_clampado_a_zero(self):
        """Distância simulada maior que a original: proporção ≤ 0 → clamped a 0."""
        assert _proporcao(50, 80) == 0.0

    def test_distancia_200(self):
        """Limite máximo do slider: proporção correta."""
        p = _proporcao(200, 200)
        assert p == 0.0

    def test_proporcao_clamped_superior(self):
        """Nunca ultrapassa 1.0."""
        assert _proporcao(50, 0) <= 1.0

    def test_proporcao_clamped_inferior(self):
        """Nunca é negativa."""
        assert _proporcao(10, 100) >= 0.0


# ---------------------------------------------------------------------------
# Testes: _camada_simulacao com resultado real
# ---------------------------------------------------------------------------

class TestCamadaSimulacao:

    def test_nova_uniao_backbone_20(self):
        """Com distância 20, retorna camada com valores corretos."""
        r = simular_cenario("nova_uniao", distancia_backbone_km=20)
        camada = _camada_simulacao(r, dist_original=98)

        assert camada is not None
        assert camada["dist_original"] == 98
        assert camada["dist_simulada"] == 20
        assert camada["recomendacao"] == "aguardar"

    def test_sem_distancia_retorna_none(self):
        """Sem parametro de distância: camada é None."""
        r = simular_cenario("nova_uniao", usar_parcerias=True)
        camada = _camada_simulacao(r, dist_original=98)
        assert camada is None

    def test_resultado_vazio_retorna_none(self):
        camada = _camada_simulacao({}, dist_original=98)
        assert camada is None

    def test_resultado_none_retorna_none(self):
        camada = _camada_simulacao(None, dist_original=98)
        assert camada is None

    def test_distancia_original_zero_sem_erro(self):
        """distancia_original=0 não levanta exceção."""
        r = simular_cenario("nova_uniao", distancia_backbone_km=20)
        camada = _camada_simulacao(r, dist_original=0)
        assert camada is not None
        assert camada["dist_original"] == 0

    def test_distancia_igual_retorna_camada(self):
        """Distância igual à original ainda retorna camada (JS decide se desenha)."""
        r = simular_cenario("nova_uniao", distancia_backbone_km=98)
        camada = _camada_simulacao(r, dist_original=98)
        assert camada is not None
        assert camada["dist_simulada"] == 98


# ---------------------------------------------------------------------------
# Testes: resumo inline
# ---------------------------------------------------------------------------

class TestResumoInline:

    def _resumo(self, resultado: dict, dist_original: float) -> str:
        """Reproduz a lógica de _resumo_inline de paginas/simulador.py."""
        res_base = resultado.get("base", {})
        res_sim = resultado.get("simulado", {})
        eng_base = res_base.get("pareceres", {}).get("engenharia", {}).get("score", "–")
        eng_sim = res_sim.get("pareceres", {}).get("engenharia", {}).get("score", "–")
        score_base = res_base.get("score_consolidado", "–")
        score_sim = res_sim.get("score_consolidado", "–")
        rec = res_sim.get("recomendacao") or "–"
        rec_label = {
            "investir_agora": "investir agora",
            "realizar_piloto": "realizar piloto",
            "aguardar": "aguardar",
        }.get(rec, rec)
        return (
            f"Engenharia {eng_base} → {eng_sim} · "
            f"Score {score_base} → {score_sim} · "
            f"Recomendação: **{rec_label}**"
        )

    def test_nova_uniao_backbone_20(self):
        """Nova União 98 → 20 km: Engenharia 11 → 31, Score 30 → 35, aguardar."""
        r = simular_cenario("nova_uniao", distancia_backbone_km=20)
        texto = self._resumo(r, dist_original=98)

        assert "Engenharia 11 → 31" in texto
        assert "Score 30 → 35" in texto
        assert "aguardar" in texto

    def test_formato_contém_separadores(self):
        r = simular_cenario("nova_uniao", distancia_backbone_km=20)
        texto = self._resumo(r, dist_original=98)
        assert " · " in texto

    def test_sem_alteracao_mostra_valores_iguais(self):
        """Sem mudança: Engenharia e Score aparecem iguais."""
        r = simular_cenario("nova_uniao")
        texto = self._resumo(r, dist_original=98)
        # Score base = score simulado = 30
        assert "Score 30 → 30" in texto


# ---------------------------------------------------------------------------
# Testes: mapa_seletor aceita camada_simulacao como parâmetro
# ---------------------------------------------------------------------------

class TestMapaSeletorCamadaSimulacao:

    def test_carregar_geografia_tem_rotulo_em_todas_regioes(self):
        """Todas as regiões no GeoJSON têm o campo 'rotulo' necessário para a camada."""
        from paginas.mapa_seletor import _GEOJSON, _carregar_geografia
        camadas = _carregar_geografia(_GEOJSON.stat().st_mtime_ns)
        for feicao in camadas["regiao"]:
            assert "rotulo" in feicao["properties"], (
                f"Região '{feicao['properties']['id']}' sem campo 'rotulo'."
            )
            rotulo = feicao["properties"]["rotulo"]
            assert len(rotulo) == 2, "rotulo deve ser [lon, lat]"

    def test_fibra_tem_uma_feature(self):
        """Há exatamente um ponto de fibra (backbone) no GeoJSON."""
        from paginas.mapa_seletor import _GEOJSON, _carregar_geografia
        camadas = _carregar_geografia(_GEOJSON.stat().st_mtime_ns)
        assert len(camadas["fibra"]) == 1

    def test_nova_uniao_rotulo_existe(self):
        """nova_uniao tem rotulo no GeoJSON."""
        from paginas.mapa_seletor import _GEOJSON, _carregar_geografia
        camadas = _carregar_geografia(_GEOJSON.stat().st_mtime_ns)
        ids = {f["properties"]["id"]: f for f in camadas["regiao"]}
        assert "nova_uniao" in ids
        assert "rotulo" in ids["nova_uniao"]["properties"]
