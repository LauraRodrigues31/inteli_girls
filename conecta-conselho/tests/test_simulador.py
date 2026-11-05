"""
Testes do motor de cenários (simulador.py).

Cobre:
- Cenário base igual ao resultado atual do Guardião
- Tabela de valores esperados do plano de entrega
- Entradas inválidas (região inexistente, distância fora de 0-200, teto <= 0)
- Garantia de que regioes.json não foi alterado
"""

from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

import pytest

# ---------------------------------------------------------------------------
# Configuração de paths
# ---------------------------------------------------------------------------

_ROOT = Path(__file__).resolve().parent.parent.parent   # inteli_girls/
_CC_DIR = Path(__file__).resolve().parent.parent        # inteli_girls/conecta-conselho/

for _p in [str(_ROOT), str(_CC_DIR)]:
    if _p not in sys.path:
        sys.path.insert(0, _p)

from simulador import simular_cenario  # noqa: E402


# ---------------------------------------------------------------------------
# Hash inicial de regioes.json para verificação de imutabilidade
# ---------------------------------------------------------------------------

_REGIOES_JSON = _CC_DIR / "data" / "regioes.json"
_REGIOES_HASH_INICIAL = hashlib.md5(_REGIOES_JSON.read_bytes()).hexdigest()


# ---------------------------------------------------------------------------
# Auxiliares
# ---------------------------------------------------------------------------

def _base(r: dict) -> dict:
    return r["base"]


def _sim(r: dict) -> dict:
    return r["simulado"]


# ---------------------------------------------------------------------------
# Testes: regioes.json não foi alterado
# ---------------------------------------------------------------------------

class TestRegioesSemAlteracao:
    def test_regioes_json_nao_alterado(self):
        """regioes.json deve permanecer intacto após qualquer simulação."""
        # Roda algumas simulações que alteram dados em memória
        simular_cenario("esperanca", usar_parcerias=True)
        simular_cenario("nova_uniao", distancia_backbone_km=20)
        simular_cenario("horizonte", teto_investimento_reais=9000000)

        hash_atual = hashlib.md5(_REGIOES_JSON.read_bytes()).hexdigest()
        assert hash_atual == _REGIOES_HASH_INICIAL, (
            "regioes.json foi modificado — as simulações devem trabalhar em cópias!"
        )


# ---------------------------------------------------------------------------
# Testes: cenário base (sem ajustes) == resultado atual do Guardião
# ---------------------------------------------------------------------------

class TestCenarioBase:
    """O cenário base de simular_cenario deve ser idêntico ao do chamar_guardiao local."""

    def _guardiao_local(self, regiao_id: str) -> dict:
        """Chama o guardião local via integracao.py."""
        import importlib.util
        integ_path = _CC_DIR / "integracao.py"
        spec = importlib.util.spec_from_file_location("integracao", integ_path)
        mod = importlib.util.module_from_spec(spec)  # type: ignore[arg-type]
        spec.loader.exec_module(mod)  # type: ignore[union-attr]
        return mod.chamar_guardiao(regiao_id, fonte="local")

    @pytest.mark.parametrize("regiao_id,score_esperado,rec_esperada", [
        ("aurora",      62, "realizar_piloto"),
        ("horizonte",   57, "realizar_piloto"),
        ("esperanca",   44, "aguardar"),
        ("central",     60, "realizar_piloto"),
        ("vale_verde",  60, "realizar_piloto"),
        ("nova_uniao",  30, "aguardar"),
    ])
    def test_base_igual_guardiao(self, regiao_id, score_esperado, rec_esperada):
        r = simular_cenario(regiao_id)
        base = _base(r)
        assert base["score_consolidado"] == score_esperado, (
            f"{regiao_id}: score base esperado {score_esperado}, obtido {base['score_consolidado']}"
        )
        assert base["recomendacao"] == rec_esperada, (
            f"{regiao_id}: rec base esperada {rec_esperada}, obtida {base['recomendacao']}"
        )

    def test_nova_uniao_alerta_prioritario(self):
        r = simular_cenario("nova_uniao")
        assert _base(r)["atencao_prioritaria"] is True


# ---------------------------------------------------------------------------
# Testes: tabela do plano de entrega
# ---------------------------------------------------------------------------

class TestTabelaEsperada:

    # esperanca | base | 44 aguardar
    def test_esperanca_base(self):
        r = simular_cenario("esperanca")
        assert _base(r)["score_consolidado"] == 44
        assert _base(r)["recomendacao"] == "aguardar"

    # esperanca | usar_parcerias=True | 50 realizar_piloto (orçamento 20 → 47)
    def test_esperanca_parcerias(self):
        r = simular_cenario("esperanca", usar_parcerias=True)
        assert _sim(r)["score_consolidado"] == 50
        assert _sim(r)["recomendacao"] == "realizar_piloto"
        # Orçamento deve ter subido de 20 para 47
        score_orc_sim = _sim(r)["pareceres"]["orcamento"]["score"]
        assert score_orc_sim == 47, f"Orçamento simulado esperado 47, obtido {score_orc_sim}"

    # esperanca | distancia_backbone_km=20 | 46 aguardar (engenharia 34 → 44)
    def test_esperanca_backbone_20(self):
        r = simular_cenario("esperanca", distancia_backbone_km=20)
        assert _sim(r)["score_consolidado"] == 46
        assert _sim(r)["recomendacao"] == "aguardar"
        score_eng_sim = _sim(r)["pareceres"]["engenharia"]["score"]
        assert score_eng_sim == 44, f"Engenharia simulada esperada 44, obtida {score_eng_sim}"

    # esperanca | backbone 20 + parcerias | 53 realizar_piloto
    def test_esperanca_backbone_20_parcerias(self):
        r = simular_cenario("esperanca", distancia_backbone_km=20, usar_parcerias=True)
        assert _sim(r)["score_consolidado"] == 53
        assert _sim(r)["recomendacao"] == "realizar_piloto"

    # esperanca | teto = CAPEX (8_700_000) | 51 realizar_piloto (orçamento → 50)
    def test_esperanca_teto_capex(self):
        r = simular_cenario("esperanca", teto_investimento_reais=8_700_000)
        assert _sim(r)["score_consolidado"] == 51
        assert _sim(r)["recomendacao"] == "realizar_piloto"
        score_orc_sim = _sim(r)["pareceres"]["orcamento"]["score"]
        assert score_orc_sim == 50, f"Orçamento simulado esperado 50, obtido {score_orc_sim}"

    # nova_uniao | usar_parcerias=True | 30 aguardar, alerta continua
    def test_nova_uniao_parcerias_alerta_continua(self):
        r = simular_cenario("nova_uniao", usar_parcerias=True)
        assert _sim(r)["score_consolidado"] == 30
        assert _sim(r)["recomendacao"] == "aguardar"
        assert _sim(r)["atencao_prioritaria"] is True, (
            "Nova União com parcerias deve continuar com alerta de atenção prioritária"
        )

    # nova_uniao | distancia_backbone_km=20 | 35 aguardar (engenharia 11 → 31), alerta continua
    def test_nova_uniao_backbone_20(self):
        r = simular_cenario("nova_uniao", distancia_backbone_km=20)
        assert _sim(r)["score_consolidado"] == 35
        assert _sim(r)["recomendacao"] == "aguardar"
        assert _sim(r)["atencao_prioritaria"] is True
        score_eng_sim = _sim(r)["pareceres"]["engenharia"]["score"]
        assert score_eng_sim == 31, f"Engenharia simulada esperada 31, obtida {score_eng_sim}"

    # horizonte | usar_parcerias=True | 60 realizar_piloto (orçamento 60 → 75)
    def test_horizonte_parcerias(self):
        r = simular_cenario("horizonte", usar_parcerias=True)
        assert _sim(r)["score_consolidado"] == 60
        assert _sim(r)["recomendacao"] == "realizar_piloto"
        score_orc_sim = _sim(r)["pareceres"]["orcamento"]["score"]
        assert score_orc_sim == 75, f"Orçamento simulado esperado 75, obtido {score_orc_sim}"


# ---------------------------------------------------------------------------
# Testes: entradas inválidas
# ---------------------------------------------------------------------------

class TestEntradasInvalidas:

    def test_regiao_inexistente(self):
        r = simular_cenario("atlantida")
        assert "erro" in r
        assert "não encontrada" in r["erro"].lower() or "nao encontrada" in r["erro"].lower()

    def test_distancia_negativa(self):
        r = simular_cenario("esperanca", distancia_backbone_km=-1)
        assert "erro" in r

    def test_distancia_acima_do_limite(self):
        r = simular_cenario("esperanca", distancia_backbone_km=201)
        assert "erro" in r

    def test_distancia_zero_valida(self):
        """Distância 0 é válida (backbone na região)."""
        r = simular_cenario("esperanca", distancia_backbone_km=0)
        assert "erro" not in r

    def test_distancia_200_valida(self):
        """Distância 200 é o limite máximo válido."""
        r = simular_cenario("esperanca", distancia_backbone_km=200)
        assert "erro" not in r

    def test_teto_zero_invalido(self):
        r = simular_cenario("esperanca", teto_investimento_reais=0)
        assert "erro" in r

    def test_teto_negativo_invalido(self):
        r = simular_cenario("esperanca", teto_investimento_reais=-100000)
        assert "erro" in r

    def test_teto_positivo_valido(self):
        r = simular_cenario("esperanca", teto_investimento_reais=1000000)
        assert "erro" not in r

    def test_regiao_vazia(self):
        r = simular_cenario("")
        assert "erro" in r

    def test_sem_ajustes_retorna_base_e_simulado_iguais(self):
        r = simular_cenario("central")
        assert "erro" not in r
        base = _base(r)
        sim = _sim(r)
        assert base["score_consolidado"] == sim["score_consolidado"]
        assert base["recomendacao"] == sim["recomendacao"]


# ---------------------------------------------------------------------------
# Testes: estrutura do retorno
# ---------------------------------------------------------------------------

class TestEstruturaRetorno:

    def test_campos_obrigatorios(self):
        r = simular_cenario("esperanca", usar_parcerias=True)
        assert "erro" not in r
        for campo in ["regiao_id", "regiao_nome", "base", "simulado",
                      "parametros", "mudancas", "premissas", "simulado_localmente"]:
            assert campo in r, f"Campo '{campo}' ausente no retorno"

    def test_simulado_localmente_true(self):
        r = simular_cenario("esperanca")
        assert r["simulado_localmente"] is True

    def test_mudancas_lista(self):
        r = simular_cenario("esperanca", usar_parcerias=True)
        assert isinstance(r["mudancas"], list)

    def test_premissas_lista(self):
        r = simular_cenario("esperanca", usar_parcerias=True)
        assert isinstance(r["premissas"], list)
        assert len(r["premissas"]) > 0, "Deve haver pelo menos uma premissa quando parcerias são ativadas"

    def test_mercado_social_pontes_nao_mudam(self):
        """Mercado, Impacto Social e Pontes não devem mudar no cenário simulado."""
        r_base = simular_cenario("esperanca")
        r_sim = simular_cenario("esperanca", distancia_backbone_km=20, usar_parcerias=True)

        for agente in ["mercado", "impacto_social", "pontes"]:
            score_base = r_base["base"]["pareceres"][agente]["score"]
            score_sim = r_sim["simulado"]["pareceres"][agente]["score"]
            assert score_base == score_sim, (
                f"Agente '{agente}' não deveria mudar no simulado: "
                f"{score_base} != {score_sim}"
            )
