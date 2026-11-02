"""
Testes automatizados para a base de dados do Conecta Conselho.

Execute com:
    python -m pytest conecta-conselho/tests/ -v

Ou, a partir da pasta conecta-conselho:
    python -m pytest tests/ -v

AVISO: Os dados testados são SIMULADOS e fictícios.
"""

from __future__ import annotations

import csv
import json
import math
import sys
from pathlib import Path
from typing import Any, Dict, List

import pytest

# Adiciona o diretório pai ao path para importar os módulos do projeto
sys.path.insert(0, str(Path(__file__).parent.parent))

from tools.consultar_regiao import (
    comparar_indicador,
    consultar_engenharia,
    consultar_financeiro,
    consultar_mercado,
    consultar_parcerias,
    consultar_regiao,
    consultar_social,
    listar_ids_regioes,
    listar_regioes,
)

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

DATA_DIR = Path(__file__).parent.parent / "data"
JSON_PATH = DATA_DIR / "regioes.json"
CSV_PATH = DATA_DIR / "regioes.csv"

IDS_ESPERADOS = {"aurora", "horizonte", "esperanca", "central", "vale_verde", "nova_uniao"}
TOTAL_REGIOES = 6


@pytest.fixture(scope="session")
def dados_json() -> Dict[str, Any]:
    with open(JSON_PATH, encoding="utf-8") as f:
        return json.load(f)


@pytest.fixture(scope="session")
def regioes(dados_json: Dict[str, Any]) -> List[Dict[str, Any]]:
    return dados_json["regioes"]


@pytest.fixture(scope="session")
def dados_csv() -> List[Dict[str, str]]:
    with open(CSV_PATH, encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


# ---------------------------------------------------------------------------
# 1. Existência e singularidade das seis regiões
# ---------------------------------------------------------------------------


class TestExistenciaRegioes:

    def test_arquivo_json_existe(self):
        assert JSON_PATH.exists(), f"regioes.json não encontrado em {JSON_PATH}"

    def test_arquivo_csv_existe(self):
        assert CSV_PATH.exists(), f"regioes.csv não encontrado em {CSV_PATH}. Execute data/gerar_csv.py"

    def test_quantidade_regioes(self, regioes):
        assert len(regioes) == TOTAL_REGIOES, (
            f"Esperado {TOTAL_REGIOES} regiões, encontrado {len(regioes)}"
        )

    def test_ids_unicos(self, regioes):
        ids = [r["id"] for r in regioes]
        assert len(ids) == len(set(ids)), f"IDs duplicados encontrados: {ids}"

    def test_ids_esperados_presentes(self, regioes):
        ids_encontrados = {r["id"] for r in regioes}
        assert ids_encontrados == IDS_ESPERADOS, (
            f"IDs divergentes.\nEsperado: {IDS_ESPERADOS}\nEncontrado: {ids_encontrados}"
        )

    def test_nomes_unicos(self, regioes):
        nomes = [r["nome"] for r in regioes]
        assert len(nomes) == len(set(nomes)), f"Nomes duplicados: {nomes}"


# ---------------------------------------------------------------------------
# 2. Campos obrigatórios em todas as regiões
# ---------------------------------------------------------------------------


SECOES_OBRIGATORIAS = ["mercado", "social", "engenharia", "financeiro", "parcerias"]

CAMPOS_MERCADO = [
    "populacao_estimada", "domicilios_total", "renda_media_mensal_reais",
    "taxa_crescimento_populacional_pct", "percentual_domicilios_conectados",
    "clientes_potenciais", "ticket_medio_mensal_reais", "numero_concorrentes",
]
CAMPOS_SOCIAL = [
    "percentual_domicilios_sem_internet", "quantidade_escolas",
    "escolas_sem_conectividade_adequada", "unidades_saude",
    "unidades_saude_conectividade_inadequada", "percentual_populacao_baixa_renda",
    "indice_vulnerabilidade_social", "pessoas_potencialmente_beneficiadas",
]
CAMPOS_ENGENHARIA = [
    "tipo_infraestrutura_disponivel", "distancia_backbone_km",
    "percentual_cobertura_fibra", "capacidade_infraestrutura_existente",
    "dificuldades_tecnicas", "prazo_implantacao_meses",
    "tecnologias_viaveis", "indice_viabilidade_tecnica",
]
CAMPOS_FINANCEIRO = [
    "capex_reais", "opex_mensal_reais", "orcamento_disponivel_reais",
    "taxa_adesao_esperada_pct", "receita_mensal_reais",
    "restricoes_orcamentarias", "riscos_financeiros",
    # payback_meses pode ser null (intencionalmente), portanto não testamos presença, mas tipo
]
CAMPOS_PARCERIAS = [
    "quantidade_instituicoes_ancora", "parceiros_publicos_possiveis",
    "parceiros_privados_possiveis", "infraestrutura_compartilhavel",
    "oportunidades_reducao_custos", "percentual_economia_potencial_pct",
    "maturidade_parcerias",
]


class TestCamposObrigatorios:

    @pytest.mark.parametrize("id_regiao", list(IDS_ESPERADOS))
    def test_campos_raiz(self, id_regiao, regioes):
        regiao = next(r for r in regioes if r["id"] == id_regiao)
        for campo in ["id", "nome", "descricao_perfil"] + SECOES_OBRIGATORIAS:
            assert campo in regiao, f"Campo '{campo}' ausente na região '{id_regiao}'"

    @pytest.mark.parametrize("id_regiao", list(IDS_ESPERADOS))
    def test_campos_mercado(self, id_regiao, regioes):
        regiao = next(r for r in regioes if r["id"] == id_regiao)
        for campo in CAMPOS_MERCADO:
            assert campo in regiao["mercado"], f"Campo mercado.{campo} ausente em '{id_regiao}'"

    @pytest.mark.parametrize("id_regiao", list(IDS_ESPERADOS))
    def test_campos_social(self, id_regiao, regioes):
        regiao = next(r for r in regioes if r["id"] == id_regiao)
        for campo in CAMPOS_SOCIAL:
            assert campo in regiao["social"], f"Campo social.{campo} ausente em '{id_regiao}'"

    @pytest.mark.parametrize("id_regiao", list(IDS_ESPERADOS))
    def test_campos_engenharia(self, id_regiao, regioes):
        regiao = next(r for r in regioes if r["id"] == id_regiao)
        for campo in CAMPOS_ENGENHARIA:
            assert campo in regiao["engenharia"], f"Campo engenharia.{campo} ausente em '{id_regiao}'"

    @pytest.mark.parametrize("id_regiao", list(IDS_ESPERADOS))
    def test_campos_financeiro(self, id_regiao, regioes):
        regiao = next(r for r in regioes if r["id"] == id_regiao)
        for campo in CAMPOS_FINANCEIRO:
            assert campo in regiao["financeiro"], f"Campo financeiro.{campo} ausente em '{id_regiao}'"

    @pytest.mark.parametrize("id_regiao", list(IDS_ESPERADOS))
    def test_campos_parcerias(self, id_regiao, regioes):
        regiao = next(r for r in regioes if r["id"] == id_regiao)
        for campo in CAMPOS_PARCERIAS:
            assert campo in regiao["parcerias"], f"Campo parcerias.{campo} ausente em '{id_regiao}'"


# ---------------------------------------------------------------------------
# 3. Tipos de dados e intervalos
# ---------------------------------------------------------------------------


class TestTiposEIntervalos:

    @pytest.mark.parametrize("id_regiao", list(IDS_ESPERADOS))
    def test_percentuais_mercado_0_100(self, id_regiao, regioes):
        r = next(x for x in regioes if x["id"] == id_regiao)
        m = r["mercado"]
        for campo in ["percentual_domicilios_conectados", "taxa_crescimento_populacional_pct"]:
            val = m[campo]
            assert 0 <= val <= 100, f"mercado.{campo} = {val} fora do intervalo [0, 100] em '{id_regiao}'"

    @pytest.mark.parametrize("id_regiao", list(IDS_ESPERADOS))
    def test_percentuais_social_0_100(self, id_regiao, regioes):
        r = next(x for x in regioes if x["id"] == id_regiao)
        s = r["social"]
        for campo in [
            "percentual_domicilios_sem_internet",
            "percentual_populacao_baixa_renda",
            "indice_vulnerabilidade_social",
        ]:
            val = s[campo]
            assert 0 <= val <= 100, f"social.{campo} = {val} fora do intervalo [0, 100] em '{id_regiao}'"

    @pytest.mark.parametrize("id_regiao", list(IDS_ESPERADOS))
    def test_indice_viabilidade_tecnica_0_100(self, id_regiao, regioes):
        r = next(x for x in regioes if x["id"] == id_regiao)
        val = r["engenharia"]["indice_viabilidade_tecnica"]
        assert 0 <= val <= 100, f"indice_viabilidade_tecnica = {val} fora de [0, 100] em '{id_regiao}'"

    @pytest.mark.parametrize("id_regiao", list(IDS_ESPERADOS))
    def test_valores_monetarios_positivos(self, id_regiao, regioes):
        r = next(x for x in regioes if x["id"] == id_regiao)
        fin = r["financeiro"]
        for campo in ["capex_reais", "opex_mensal_reais", "orcamento_disponivel_reais"]:
            assert fin[campo] > 0, f"financeiro.{campo} deve ser > 0 em '{id_regiao}'"

    @pytest.mark.parametrize("id_regiao", list(IDS_ESPERADOS))
    def test_taxa_adesao_0_100(self, id_regiao, regioes):
        r = next(x for x in regioes if x["id"] == id_regiao)
        val = r["financeiro"]["taxa_adesao_esperada_pct"]
        assert 0 <= val <= 100, f"taxa_adesao_esperada_pct = {val} fora de [0, 100] em '{id_regiao}'"

    @pytest.mark.parametrize("id_regiao", list(IDS_ESPERADOS))
    def test_payback_none_ou_inteiro_positivo(self, id_regiao, regioes):
        r = next(x for x in regioes if x["id"] == id_regiao)
        pb = r["financeiro"]["payback_meses"]
        assert pb is None or (isinstance(pb, int) and pb > 0), (
            f"payback_meses deve ser null ou inteiro > 0 em '{id_regiao}', encontrado: {pb}"
        )

    @pytest.mark.parametrize("id_regiao", list(IDS_ESPERADOS))
    def test_maturidade_parcerias_valida(self, id_regiao, regioes):
        r = next(x for x in regioes if x["id"] == id_regiao)
        val = r["parcerias"]["maturidade_parcerias"]
        assert val in {"baixa", "média", "alta"}, (
            f"maturidade_parcerias = '{val}' inválido em '{id_regiao}'"
        )

    @pytest.mark.parametrize("id_regiao", list(IDS_ESPERADOS))
    def test_infraestrutura_compartilhavel_booleano(self, id_regiao, regioes):
        r = next(x for x in regioes if x["id"] == id_regiao)
        val = r["parcerias"]["infraestrutura_compartilhavel"]
        assert isinstance(val, bool), (
            f"infraestrutura_compartilhavel deve ser bool em '{id_regiao}', encontrado: {type(val)}"
        )

    @pytest.mark.parametrize("id_regiao", list(IDS_ESPERADOS))
    def test_listas_nao_vazias(self, id_regiao, regioes):
        r = next(x for x in regioes if x["id"] == id_regiao)
        assert len(r["engenharia"]["dificuldades_tecnicas"]) >= 1
        assert len(r["engenharia"]["tecnologias_viaveis"]) >= 1
        assert len(r["financeiro"]["riscos_financeiros"]) >= 1


# ---------------------------------------------------------------------------
# 4. Regras de consistência dos dados
# ---------------------------------------------------------------------------


class TestConsistencia:

    @pytest.mark.parametrize("id_regiao", list(IDS_ESPERADOS))
    def test_populacao_maior_que_3x_domicilios(self, id_regiao, regioes):
        r = next(x for x in regioes if x["id"] == id_regiao)
        m = r["mercado"]
        assert m["populacao_estimada"] >= m["domicilios_total"] * 3, (
            f"população ({m['populacao_estimada']}) < domicílios×3 ({m['domicilios_total']*3}) em '{id_regiao}'"
        )

    @pytest.mark.parametrize("id_regiao", list(IDS_ESPERADOS))
    def test_clientes_potenciais_menor_igual_domicilios(self, id_regiao, regioes):
        r = next(x for x in regioes if x["id"] == id_regiao)
        m = r["mercado"]
        assert m["clientes_potenciais"] <= m["domicilios_total"], (
            f"clientes_potenciais ({m['clientes_potenciais']}) > domicilios_total ({m['domicilios_total']}) em '{id_regiao}'"
        )

    @pytest.mark.parametrize("id_regiao", list(IDS_ESPERADOS))
    def test_percentuais_conectados_e_sem_internet_complementares(self, id_regiao, regioes):
        r = next(x for x in regioes if x["id"] == id_regiao)
        conectados = r["mercado"]["percentual_domicilios_conectados"]
        sem_internet = r["social"]["percentual_domicilios_sem_internet"]
        soma = conectados + sem_internet
        assert abs(soma - 100) <= 1, (
            f"conectados ({conectados}) + sem_internet ({sem_internet}) = {soma}, esperado ≈ 100 em '{id_regiao}'"
        )

    @pytest.mark.parametrize("id_regiao", list(IDS_ESPERADOS))
    def test_escolas_sem_conectividade_menor_igual_total(self, id_regiao, regioes):
        r = next(x for x in regioes if x["id"] == id_regiao)
        s = r["social"]
        assert s["escolas_sem_conectividade_adequada"] <= s["quantidade_escolas"]

    @pytest.mark.parametrize("id_regiao", list(IDS_ESPERADOS))
    def test_unidades_saude_inadequadas_menor_igual_total(self, id_regiao, regioes):
        r = next(x for x in regioes if x["id"] == id_regiao)
        s = r["social"]
        assert s["unidades_saude_conectividade_inadequada"] <= s["unidades_saude"]


# ---------------------------------------------------------------------------
# 5. Integridade dos cálculos financeiros
# ---------------------------------------------------------------------------


TOLERANCIA_REAIS = 1.0  # tolerância de R$ 1,00 para arredondamentos


class TestCalculosFinanceiros:

    @pytest.mark.parametrize("id_regiao", list(IDS_ESPERADOS))
    def test_receita_mensal_formula(self, id_regiao, regioes):
        """receita = clientes_potenciais × (taxa_adesao / 100) × ticket_medio"""
        r = next(x for x in regioes if x["id"] == id_regiao)
        m = r["mercado"]
        fin = r["financeiro"]
        receita_calculada = (
            m["clientes_potenciais"]
            * (fin["taxa_adesao_esperada_pct"] / 100)
            * m["ticket_medio_mensal_reais"]
        )
        receita_declarada = fin["receita_mensal_reais"]
        diferenca = abs(receita_calculada - receita_declarada)
        assert diferenca <= TOLERANCIA_REAIS, (
            f"Receita divergente em '{id_regiao}': "
            f"calculado R${receita_calculada:.2f} vs declarado R${receita_declarada:.2f} "
            f"(diferença: R${diferenca:.2f})"
        )

    @pytest.mark.parametrize("id_regiao", list(IDS_ESPERADOS))
    def test_payback_formula(self, id_regiao, regioes):
        """payback = capex / (receita - opex), quando receita > opex"""
        r = next(x for x in regioes if x["id"] == id_regiao)
        fin = r["financeiro"]
        receita = fin["receita_mensal_reais"]
        opex = fin["opex_mensal_reais"]
        capex = fin["capex_reais"]
        payback = fin["payback_meses"]

        margem = receita - opex
        if margem <= 0:
            # Projeto inviável: payback deve ser null
            assert payback is None, (
                f"payback deve ser null quando receita ({receita}) <= opex ({opex}) em '{id_regiao}', "
                f"mas encontrado: {payback}"
            )
        else:
            payback_calculado = capex / margem
            assert payback is not None, (
                f"payback não pode ser null quando receita > opex em '{id_regiao}'"
            )
            # Tolerância de ±2 meses para arredondamento
            assert abs(payback - payback_calculado) <= 2, (
                f"Payback divergente em '{id_regiao}': "
                f"calculado {payback_calculado:.1f} vs declarado {payback} meses"
            )


# ---------------------------------------------------------------------------
# 6. Consistência entre JSON e CSV
# ---------------------------------------------------------------------------


class TestConsistenciaJsonCsv:

    def test_quantidade_linhas_csv(self, regioes, dados_csv):
        assert len(dados_csv) == len(regioes), (
            f"CSV tem {len(dados_csv)} linhas, JSON tem {len(regioes)} regiões"
        )

    def test_ids_iguais_json_csv(self, regioes, dados_csv):
        ids_json = sorted([r["id"] for r in regioes])
        ids_csv = sorted([row["id"] for row in dados_csv])
        assert ids_json == ids_csv, f"IDs divergentes: JSON={ids_json} CSV={ids_csv}"

    @pytest.mark.parametrize("id_regiao", list(IDS_ESPERADOS))
    def test_nome_consistente_json_csv(self, id_regiao, regioes, dados_csv):
        nome_json = next(r["nome"] for r in regioes if r["id"] == id_regiao)
        nome_csv = next(row["nome"] for row in dados_csv if row["id"] == id_regiao)
        assert nome_json == nome_csv, (
            f"Nome divergente para '{id_regiao}': JSON='{nome_json}' CSV='{nome_csv}'"
        )

    @pytest.mark.parametrize("id_regiao", list(IDS_ESPERADOS))
    def test_receita_consistente_json_csv(self, id_regiao, regioes, dados_csv):
        receita_json = next(r["financeiro"]["receita_mensal_reais"] for r in regioes if r["id"] == id_regiao)
        receita_csv_str = next(row["receita_mensal_reais"] for row in dados_csv if row["id"] == id_regiao)
        assert abs(float(receita_csv_str) - receita_json) <= TOLERANCIA_REAIS


# ---------------------------------------------------------------------------
# 7. Funções de consulta
# ---------------------------------------------------------------------------


class TestFuncoesConsulta:

    def test_listar_regioes_retorna_lista(self):
        resultado = listar_regioes()
        assert isinstance(resultado, list)
        assert len(resultado) == TOTAL_REGIOES

    def test_listar_regioes_campos_minimos(self):
        for r in listar_regioes():
            assert "id" in r
            assert "nome" in r
            assert "descricao_perfil" in r

    def test_listar_ids_regioes(self):
        ids = listar_ids_regioes()
        assert set(ids) == IDS_ESPERADOS

    @pytest.mark.parametrize("id_regiao", list(IDS_ESPERADOS))
    def test_consultar_regiao_retorna_dados(self, id_regiao):
        resultado = consultar_regiao(id_regiao)
        assert "erro" not in resultado
        assert resultado["id"] == id_regiao

    def test_consultar_regiao_inexistente(self):
        resultado = consultar_regiao("regiao_inexistente_xyz")
        assert "erro" in resultado
        assert "regiao_inexistente_xyz" in resultado["mensagem"]

    @pytest.mark.parametrize("id_regiao", list(IDS_ESPERADOS))
    def test_consultar_mercado(self, id_regiao):
        resultado = consultar_mercado(id_regiao)
        assert "erro" not in resultado
        assert resultado["perspectiva"] == "mercado"
        assert "clientes_potenciais" in resultado["dados"]

    @pytest.mark.parametrize("id_regiao", list(IDS_ESPERADOS))
    def test_consultar_social(self, id_regiao):
        resultado = consultar_social(id_regiao)
        assert "erro" not in resultado
        assert resultado["perspectiva"] == "social"
        assert "indice_vulnerabilidade_social" in resultado["dados"]

    @pytest.mark.parametrize("id_regiao", list(IDS_ESPERADOS))
    def test_consultar_engenharia(self, id_regiao):
        resultado = consultar_engenharia(id_regiao)
        assert "erro" not in resultado
        assert resultado["perspectiva"] == "engenharia"
        assert "indice_viabilidade_tecnica" in resultado["dados"]

    @pytest.mark.parametrize("id_regiao", list(IDS_ESPERADOS))
    def test_consultar_financeiro(self, id_regiao):
        resultado = consultar_financeiro(id_regiao)
        assert "erro" not in resultado
        assert resultado["perspectiva"] == "financeiro"
        assert "capex_reais" in resultado["dados"]

    @pytest.mark.parametrize("id_regiao", list(IDS_ESPERADOS))
    def test_consultar_parcerias(self, id_regiao):
        resultado = consultar_parcerias(id_regiao)
        assert "erro" not in resultado
        assert resultado["perspectiva"] == "parcerias"
        assert "maturidade_parcerias" in resultado["dados"]

    def test_consultar_mercado_inexistente(self):
        resultado = consultar_mercado("nao_existe")
        assert "erro" in resultado

    def test_consultar_social_inexistente(self):
        resultado = consultar_social("nao_existe")
        assert "erro" in resultado

    def test_consultar_engenharia_inexistente(self):
        resultado = consultar_engenharia("nao_existe")
        assert "erro" in resultado

    def test_consultar_financeiro_inexistente(self):
        resultado = consultar_financeiro("nao_existe")
        assert "erro" in resultado

    def test_consultar_parcerias_inexistente(self):
        resultado = consultar_parcerias("nao_existe")
        assert "erro" in resultado

    def test_comparar_indicador_viabilidade(self):
        resultado = comparar_indicador("engenharia.indice_viabilidade_tecnica")
        assert len(resultado) == TOTAL_REGIOES
        # Deve estar ordenado decrescente por valor
        valores = [r["valor"] for r in resultado if r["valor"] is not None]
        assert valores == sorted(valores, reverse=True)

    def test_comparar_indicador_campo_invalido(self):
        resultado = comparar_indicador("campo_sem_ponto")
        assert "erro" in resultado[0]

    def test_consultar_regiao_id_case_insensitive(self):
        """IDs devem ser aceitos independentemente de maiúsculas/minúsculas."""
        resultado_lower = consultar_regiao("aurora")
        resultado_upper = consultar_regiao("AURORA")
        resultado_mixed = consultar_regiao("Aurora")
        assert "erro" not in resultado_lower
        assert "erro" not in resultado_upper
        assert "erro" not in resultado_mixed


# ---------------------------------------------------------------------------
# 8. Metadados do JSON
# ---------------------------------------------------------------------------


class TestMetadados:

    def test_metadados_presentes(self, dados_json):
        assert "metadados" in dados_json

    def test_status_simulado(self, dados_json):
        assert dados_json["metadados"]["status"] == "SIMULADO"

    def test_aviso_presente(self, dados_json):
        assert "aviso" in dados_json["metadados"]
        assert len(dados_json["metadados"]["aviso"]) > 10

    def test_formulas_documentadas(self, dados_json):
        assert "formulas_e_premissas" in dados_json["metadados"]
        formulas = dados_json["metadados"]["formulas_e_premissas"]
        assert "receita_mensal" in formulas
        assert "payback_meses" in formulas
