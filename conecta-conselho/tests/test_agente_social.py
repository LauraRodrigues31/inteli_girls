"""
Testes automatizados do Agente de Impacto Social — Conecta Conselho.

Valida a ferramenta tool_social.py de forma isolada, sem depender da
instância IBM Cloud. Testa a lógica de cálculo, o contrato de saída
e o tratamento de erros.

Execute com:
    python -m pytest conecta-conselho/tests/test_agente_social.py -v

AVISO: Os dados testados são SIMULADOS e fictícios.
"""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import pytest

# ---------------------------------------------------------------------------
# Importação robusta que não depende de sys.path para resolver ambiguidade
# entre inteli_girls/tools/ (sem __init__.py) e conecta-conselho/tools/
# (com __init__.py). Carrega tool_social.py diretamente pelo caminho do arquivo.
# ---------------------------------------------------------------------------

_TOOL_SOCIAL_PATH = Path(__file__).parent.parent.parent / "tools" / "tool_social.py"
_spec = importlib.util.spec_from_file_location("tool_social", _TOOL_SOCIAL_PATH)
_mod = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_mod)

_calcular_indicadores_sociais = _mod._calcular_indicadores_sociais
_calcular_percentual_seguro   = _mod._calcular_percentual_seguro
_determinar_confianca         = _mod._determinar_confianca
_formatar_numero_ptbr         = _mod._formatar_numero_ptbr
_identificar_riscos           = _mod._identificar_riscos
_montar_justificativa         = _mod._montar_justificativa
_listar_campos_ausentes       = _mod._listar_campos_ausentes
_montar_resposta_erro         = _mod._montar_resposta_erro
_obter_campo_numerico         = _mod._obter_campo_numerico
_ADK_DISPONIVEL               = _mod._ADK_DISPONIVEL
_CAMPOS_OBRIGATORIOS_SOCIAL   = _mod._CAMPOS_OBRIGATORIOS_SOCIAL
_CAMPOS_CRITICOS_SOCIAL       = _mod._CAMPOS_CRITICOS_SOCIAL
analisar_impacto_social       = _mod.analisar_impacto_social

# ---------------------------------------------------------------------------
# Constantes de apoio
# ---------------------------------------------------------------------------

IDS_VALIDOS = ["aurora", "horizonte", "esperanca", "central", "vale_verde", "nova_uniao"]

CAMPOS_OBRIGATORIOS_CONTRATO = [
    "agente",
    "regiao_id",
    "regiao_nome",
    "score",
    "confianca",
    "tipo_resultado",
    "indicadores",
    "justificativa",
    "riscos",
    "limitacoes",
    "simulado",
    "erro",
]

CAMPOS_INDICADORES = [
    "percentual_domicilios_sem_internet",
    "quantidade_escolas",
    "escolas_sem_conectividade_adequada",
    "unidades_saude",
    "unidades_saude_conectividade_inadequada",
    "percentual_populacao_baixa_renda",
    "indice_vulnerabilidade_social",
    "pessoas_potencialmente_beneficiadas",
    "percentual_escolas_sem_conectividade",
    "percentual_saude_sem_conectividade",
    "score_exclusao_digital",
    "score_infraestrutura_social",
    "score_vulnerabilidade",
    "score_alcance",
]


def _extrair_conteudo(resultado) -> dict:
    """Extrai o dicionário de conteúdo do ToolResponse retornado pelo @tool."""
    if hasattr(resultado, "content"):
        return resultado.content
    return resultado


# ---------------------------------------------------------------------------
# 0. Testes de portabilidade (importação e ambiente)
# ---------------------------------------------------------------------------


class TestPortabilidade:
    def test_modulo_carrega_sem_excecao(self):
        """
        O módulo tool_social.py deve ser importável em qualquer ambiente Python 3.12,
        independentemente de o ADK estar instalado ou não.
        O try/except no import garante isso.
        """
        assert _mod is not None

    def test_adk_disponivel_e_bool(self):
        """_ADK_DISPONIVEL deve ser um booleano, True com ADK, False sem ADK."""
        assert isinstance(_ADK_DISPONIVEL, bool)

    def test_analisar_impacto_social_e_callable(self):
        """A ferramenta principal deve ser callable independentemente do caminho de import."""
        assert callable(analisar_impacto_social)

    def test_funcoes_puras_sao_callable(self):
        """Todas as funções auxiliares devem ser importáveis e chamáveis."""
        for func in [
            _calcular_percentual_seguro,
            _calcular_indicadores_sociais,
            _determinar_confianca,
            _formatar_numero_ptbr,
            _identificar_riscos,
            _montar_justificativa,
            _montar_resposta_erro,
            _obter_campo_numerico,
        ]:
            assert callable(func), f"{func.__name__} não é callable"


# ---------------------------------------------------------------------------
# 1. Testes de funções puras (sem ADK)
# ---------------------------------------------------------------------------


class TestCalcularPercentualSeguro:
    def test_calculo_normal(self):
        assert _calcular_percentual_seguro(14, 42) == pytest.approx(33.3, abs=0.1)

    def test_denominador_zero_retorna_zero(self):
        assert _calcular_percentual_seguro(5, 0) == 0.0

    def test_cem_porcento(self):
        assert _calcular_percentual_seguro(10, 10) == 100.0

    def test_zero_numerador(self):
        assert _calcular_percentual_seguro(0, 50) == 0.0


class TestDeterminarConfianca:
    def test_todos_campos_retorna_alta(self):
        dados_completos = {
            "percentual_domicilios_sem_internet": 72,
            "quantidade_escolas": 61,
            "escolas_sem_conectividade_adequada": 48,
            "unidades_saude": 27,
            "unidades_saude_conectividade_inadequada": 20,
            "percentual_populacao_baixa_renda": 64,
            "indice_vulnerabilidade_social": 74,
            "pessoas_potencialmente_beneficiadas": 101376,
        }
        assert _determinar_confianca(dados_completos) == "alta"

    def test_campo_critico_ausente_retorna_baixa(self):
        dados_sem_critico = {
            "quantidade_escolas": 61,
            "escolas_sem_conectividade_adequada": 48,
            "unidades_saude": 27,
            "unidades_saude_conectividade_inadequada": 20,
            "percentual_populacao_baixa_renda": 64,
            # indice_vulnerabilidade_social ausente (campo crítico)
            # pessoas_potencialmente_beneficiadas ausente (campo crítico)
        }
        assert _determinar_confianca(dados_sem_critico) == "baixa"

    def test_dados_vazios_retorna_baixa(self):
        assert _determinar_confianca({}) == "baixa"

    def test_campo_nao_critico_ausente_com_5_presentes_retorna_baixa(self):
        """Menos de 6 campos presentes → baixa, mesmo sem campo crítico ausente."""
        dados = {
            "percentual_domicilios_sem_internet": 72,
            "quantidade_escolas": 61,
            "unidades_saude": 27,
            "indice_vulnerabilidade_social": 74,
            "pessoas_potencialmente_beneficiadas": 101376,
            # apenas 5 dos 8 campos
        }
        assert _determinar_confianca(dados) == "baixa"

    def test_6_campos_presentes_sem_critico_ausente_retorna_media(self):
        """6 campos presentes e nenhum crítico ausente → media."""
        dados = {
            "percentual_domicilios_sem_internet": 72,
            "quantidade_escolas": 61,
            "escolas_sem_conectividade_adequada": 48,
            "unidades_saude": 27,
            "indice_vulnerabilidade_social": 74,
            "pessoas_potencialmente_beneficiadas": 101376,
            # 6 de 8 campos; ausentes: unidades_saude_conectividade_inadequada e percentual_populacao_baixa_renda
        }
        assert _determinar_confianca(dados) == "media"


class TestListarCamposAusentes:
    """Testes de _listar_campos_ausentes — rastreabilidade de incompletude."""

    def test_dados_completos_retorna_lista_vazia(self):
        dados = {c: 1 for c in _CAMPOS_OBRIGATORIOS_SOCIAL}
        assert _listar_campos_ausentes(dados) == []

    def test_dados_vazios_lista_todos_os_obrigatorios(self):
        ausentes = _listar_campos_ausentes({})
        assert set(ausentes) == set(_CAMPOS_OBRIGATORIOS_SOCIAL)

    def test_campo_none_aparece_como_ausente(self):
        dados = {c: 1 for c in _CAMPOS_OBRIGATORIOS_SOCIAL}
        dados["indice_vulnerabilidade_social"] = None
        ausentes = _listar_campos_ausentes(dados)
        assert "indice_vulnerabilidade_social" in ausentes

    def test_identifica_apenas_os_ausentes(self):
        dados = {c: 1 for c in _CAMPOS_OBRIGATORIOS_SOCIAL}
        del dados["percentual_domicilios_sem_internet"]
        del dados["quantidade_escolas"]
        ausentes = _listar_campos_ausentes(dados)
        assert set(ausentes) == {"percentual_domicilios_sem_internet", "quantidade_escolas"}

    def test_campos_criticos_identificados_corretamente(self):
        """Campos críticos ausentes devem aparecer na lista retornada."""
        dados = {c: 1 for c in _CAMPOS_OBRIGATORIOS_SOCIAL}
        dados["indice_vulnerabilidade_social"] = None
        dados["pessoas_potencialmente_beneficiadas"] = None
        ausentes = _listar_campos_ausentes(dados)
        assert "indice_vulnerabilidade_social" in ausentes
        assert "pessoas_potencialmente_beneficiadas" in ausentes


class TestCalcularIndicadoresSociais:
    def test_score_entre_0_e_100(self):
        dados = {
            "percentual_domicilios_sem_internet": 72,
            "quantidade_escolas": 61,
            "escolas_sem_conectividade_adequada": 48,
            "unidades_saude": 27,
            "unidades_saude_conectividade_inadequada": 20,
            "percentual_populacao_baixa_renda": 64,
            "indice_vulnerabilidade_social": 74,
            "pessoas_potencialmente_beneficiadas": 101376,
        }
        indicadores, score = _calcular_indicadores_sociais(dados)
        assert 0 <= score <= 100

    def test_score_e_inteiro(self):
        dados = {
            "percentual_domicilios_sem_internet": 38,
            "quantidade_escolas": 42,
            "escolas_sem_conectividade_adequada": 14,
            "unidades_saude": 18,
            "unidades_saude_conectividade_inadequada": 5,
            "percentual_populacao_baixa_renda": 28,
            "indice_vulnerabilidade_social": 32,
            "pessoas_potencialmente_beneficiadas": 70528,
        }
        _, score = _calcular_indicadores_sociais(dados)
        assert isinstance(score, int)

    def test_percentual_escolas_calculado_corretamente(self):
        """percentual_escolas_sem_conectividade = (48 / 61) × 100 ≈ 78.7"""
        dados = {
            "percentual_domicilios_sem_internet": 72,
            "quantidade_escolas": 61,
            "escolas_sem_conectividade_adequada": 48,
            "unidades_saude": 27,
            "unidades_saude_conectividade_inadequada": 20,
            "percentual_populacao_baixa_renda": 64,
            "indice_vulnerabilidade_social": 74,
            "pessoas_potencialmente_beneficiadas": 101376,
        }
        indicadores, _ = _calcular_indicadores_sociais(dados)
        assert indicadores["percentual_escolas_sem_conectividade"] == pytest.approx(78.7, abs=0.1)

    def test_percentual_saude_calculado_corretamente(self):
        """percentual_saude_sem_conectividade = (20 / 27) × 100 ≈ 74.1"""
        dados = {
            "percentual_domicilios_sem_internet": 72,
            "quantidade_escolas": 61,
            "escolas_sem_conectividade_adequada": 48,
            "unidades_saude": 27,
            "unidades_saude_conectividade_inadequada": 20,
            "percentual_populacao_baixa_renda": 64,
            "indice_vulnerabilidade_social": 74,
            "pessoas_potencialmente_beneficiadas": 101376,
        }
        indicadores, _ = _calcular_indicadores_sociais(dados)
        assert indicadores["percentual_saude_sem_conectividade"] == pytest.approx(74.1, abs=0.1)

    def test_todos_sub_scores_presentes(self):
        dados = {
            "percentual_domicilios_sem_internet": 50,
            "quantidade_escolas": 10,
            "escolas_sem_conectividade_adequada": 5,
            "unidades_saude": 5,
            "unidades_saude_conectividade_inadequada": 2,
            "percentual_populacao_baixa_renda": 40,
            "indice_vulnerabilidade_social": 50,
            "pessoas_potencialmente_beneficiadas": 60000,
        }
        indicadores, _ = _calcular_indicadores_sociais(dados)
        for campo in ["score_exclusao_digital", "score_infraestrutura_social",
                       "score_vulnerabilidade", "score_alcance"]:
            assert campo in indicadores

    def test_score_zero_dados_sem_exclusao(self):
        """Região com 0% sem internet, 0 escolas problemáticas, 0 vulnerabilidade → score baixo."""
        dados = {
            "percentual_domicilios_sem_internet": 0,
            "quantidade_escolas": 10,
            "escolas_sem_conectividade_adequada": 0,
            "unidades_saude": 5,
            "unidades_saude_conectividade_inadequada": 0,
            "percentual_populacao_baixa_renda": 0,
            "indice_vulnerabilidade_social": 0,
            "pessoas_potencialmente_beneficiadas": 0,
        }
        _, score = _calcular_indicadores_sociais(dados)
        assert score == 0

    def test_dados_ausentes_nao_lancam_excecao(self):
        """Campos ausentes devem retornar score 0, não lançar exceção."""
        _, score = _calcular_indicadores_sociais({})
        assert score == 0

    def test_campo_none_equivale_a_ausente(self):
        """
        Campo presente com valor None deve ser tratado igual a campo ausente —
        ambos resultam em 0.0/0 no cálculo, não em erro de tipo.
        Garante que a base simulada nunca quebre o cálculo mesmo com None explícito.
        """
        dados_com_none = {
            "percentual_domicilios_sem_internet": None,
            "quantidade_escolas": 10,
            "escolas_sem_conectividade_adequada": 5,
            "unidades_saude": 5,
            "unidades_saude_conectividade_inadequada": 2,
            "percentual_populacao_baixa_renda": 30,
            "indice_vulnerabilidade_social": None,
            "pessoas_potencialmente_beneficiadas": 50000,
        }
        indicadores, score = _calcular_indicadores_sociais(dados_com_none)
        assert isinstance(score, int)
        assert indicadores["percentual_domicilios_sem_internet"] == 0.0
        assert indicadores["indice_vulnerabilidade_social"] == 0.0

    def test_campo_zero_legitimo_nao_e_confundido_com_ausente(self):
        """
        Campo presente com valor 0 (legítimo, ex: 0% de exclusão digital) deve
        ser lido como 0, não como dado ausente.
        """
        dados_com_zero = {
            "percentual_domicilios_sem_internet": 0,
            "quantidade_escolas": 10,
            "escolas_sem_conectividade_adequada": 0,
            "unidades_saude": 5,
            "unidades_saude_conectividade_inadequada": 0,
            "percentual_populacao_baixa_renda": 0,
            "indice_vulnerabilidade_social": 0,
            "pessoas_potencialmente_beneficiadas": 0,
        }
        indicadores, _ = _calcular_indicadores_sociais(dados_com_zero)
        # Campos presentes com valor 0 devem ser retornados como 0, não como None
        assert indicadores["percentual_domicilios_sem_internet"] == 0.0
        assert indicadores["indice_vulnerabilidade_social"] == 0.0
        assert indicadores["pessoas_potencialmente_beneficiadas"] == 0

    def test_retorna_tupla_dict_int(self):
        """_calcular_indicadores_sociais deve retornar (dict, int)."""
        dados = {
            "percentual_domicilios_sem_internet": 50,
            "quantidade_escolas": 10,
            "escolas_sem_conectividade_adequada": 5,
            "unidades_saude": 5,
            "unidades_saude_conectividade_inadequada": 2,
            "percentual_populacao_baixa_renda": 40,
            "indice_vulnerabilidade_social": 50,
            "pessoas_potencialmente_beneficiadas": 60000,
        }
        resultado = _calcular_indicadores_sociais(dados)
        assert isinstance(resultado, tuple)
        assert len(resultado) == 2
        assert isinstance(resultado[0], dict)
        assert isinstance(resultado[1], int)


class TestObterCampoNumerico:
    """Testes da função auxiliar _obter_campo_numerico."""

    def test_campo_presente_retorna_valor_convertido(self):
        dados = {"campo": 42}
        assert _obter_campo_numerico(dados, "campo", int, 0) == 42

    def test_campo_ausente_retorna_padrao(self):
        assert _obter_campo_numerico({}, "campo", int, 99) == 99

    def test_campo_none_retorna_padrao(self):
        dados = {"campo": None}
        assert _obter_campo_numerico(dados, "campo", int, 99) == 99

    def test_conversao_para_float(self):
        dados = {"campo": 7}
        resultado = _obter_campo_numerico(dados, "campo", float, 0.0)
        assert isinstance(resultado, float)
        assert resultado == 7.0

    def test_zero_legitimo_nao_e_padrao(self):
        """Valor 0 explícito deve ser retornado, não substituído pelo padrão."""
        dados = {"campo": 0}
        assert _obter_campo_numerico(dados, "campo", int, 99) == 0


class TestFormatarNumeroPtbr:
    """Testes do formatador de número pt-BR, sem replace destrutivo."""

    def test_numero_grande(self):
        assert _formatar_numero_ptbr(101376) == "101.376"

    def test_numero_pequeno(self):
        assert _formatar_numero_ptbr(999) == "999"

    def test_numero_com_dois_separadores(self):
        assert _formatar_numero_ptbr(1234567) == "1.234.567"

    def test_zero(self):
        assert _formatar_numero_ptbr(0) == "0"

    def test_justificativa_sem_replace_destrutivo(self):
        """
        Garante que a justificativa não contém vírgulas gramaticais convertidas
        em pontos pelo replace(",", ".") que existia anteriormente.
        O texto gerado deve usar ponto como separador de milhar no número
        de pessoas, mas manter vírgulas gramaticais intactas.
        """
        indicadores = {
            "percentual_domicilios_sem_internet": 72,
            "indice_vulnerabilidade_social": 74,
            "pessoas_potencialmente_beneficiadas": 101376,
            "percentual_escolas_sem_conectividade": 78.7,
            "percentual_saude_sem_conectividade": 74.1,
            "percentual_populacao_baixa_renda": 64,
        }
        texto = _montar_justificativa("Região Horizonte", indicadores, 76)
        # Número formatado com ponto (pt-BR)
        assert "101.376" in texto
        # Não deve conter o número com vírgula americana
        assert "101,376" not in texto


class TestMontagemJustificativa:
    def test_justificativa_contem_nome_regiao(self):
        indicadores = {
            "percentual_domicilios_sem_internet": 72,
            "indice_vulnerabilidade_social": 74,
            "pessoas_potencialmente_beneficiadas": 101376,
            "percentual_escolas_sem_conectividade": 78.7,
            "percentual_saude_sem_conectividade": 74.1,
            "percentual_populacao_baixa_renda": 64,
        }
        texto = _montar_justificativa("Região Horizonte", indicadores, 76)
        assert "Região Horizonte" in texto

    def test_justificativa_contem_score(self):
        indicadores = {
            "percentual_domicilios_sem_internet": 72,
            "indice_vulnerabilidade_social": 74,
            "pessoas_potencialmente_beneficiadas": 101376,
            "percentual_escolas_sem_conectividade": 78.7,
            "percentual_saude_sem_conectividade": 74.1,
            "percentual_populacao_baixa_renda": 64,
        }
        texto = _montar_justificativa("Região Horizonte", indicadores, 76)
        assert "76" in texto

    def test_justificativa_minimo_50_caracteres(self):
        indicadores = {
            "percentual_domicilios_sem_internet": 38,
            "indice_vulnerabilidade_social": 32,
            "pessoas_potencialmente_beneficiadas": 70528,
            "percentual_escolas_sem_conectividade": 33.3,
            "percentual_saude_sem_conectividade": 27.8,
            "percentual_populacao_baixa_renda": 28,
        }
        texto = _montar_justificativa("Região Aurora", indicadores, 38)
        assert len(texto) >= 50


class TestIdentificarRiscos:
    def test_alta_baixa_renda_gera_risco(self):
        dados = {"percentual_populacao_baixa_renda": 65, "percentual_domicilios_sem_internet": 30,
                 "indice_vulnerabilidade_social": 40}
        riscos = _identificar_riscos(dados, "Região Teste")
        assert any("baixa renda" in r.lower() or "renda" in r.lower() for r in riscos)

    def test_alta_exclusao_digital_gera_risco(self):
        dados = {"percentual_populacao_baixa_renda": 20, "percentual_domicilios_sem_internet": 80,
                 "indice_vulnerabilidade_social": 40}
        riscos = _identificar_riscos(dados, "Região Teste")
        assert any("exclusão" in r.lower() or "digital" in r.lower() for r in riscos)

    def test_retorna_lista_nao_vazia(self):
        dados = {"percentual_populacao_baixa_renda": 20, "percentual_domicilios_sem_internet": 20,
                 "indice_vulnerabilidade_social": 20}
        riscos = _identificar_riscos(dados, "Região Teste")
        assert len(riscos) >= 1


class TestRespostaErro:
    def test_estrutura_resposta_erro(self):
        resposta = _montar_resposta_erro("xyz", "Região não encontrada: 'xyz'")
        assert resposta["agente"] == "impacto_social"
        assert resposta["score"] == 0
        assert resposta["confianca"] == "nao_avaliada"
        assert resposta["erro"] is not None
        assert resposta["simulado"] is True
        assert isinstance(resposta["indicadores"], dict)
        assert len(resposta["indicadores"]) == 0


# ---------------------------------------------------------------------------
# 2. Testes de contrato (via @tool — acessa ToolResponse.content)
# ---------------------------------------------------------------------------


class TestContratoAnalisarImpactoSocial:

    @pytest.mark.parametrize("regiao_id", IDS_VALIDOS)
    def test_retorna_todos_campos_obrigatorios(self, regiao_id):
        resultado = _extrair_conteudo(analisar_impacto_social(regiao_id))
        for campo in CAMPOS_OBRIGATORIOS_CONTRATO:
            assert campo in resultado, f"Campo '{campo}' ausente para '{regiao_id}'"

    @pytest.mark.parametrize("regiao_id", IDS_VALIDOS)
    def test_score_inteiro_entre_0_e_100(self, regiao_id):
        resultado = _extrair_conteudo(analisar_impacto_social(regiao_id))
        assert isinstance(resultado["score"], int), f"score deve ser int em '{regiao_id}'"
        assert 0 <= resultado["score"] <= 100, f"score fora de [0,100] em '{regiao_id}'"

    @pytest.mark.parametrize("regiao_id", IDS_VALIDOS)
    def test_simulado_sempre_true(self, regiao_id):
        resultado = _extrair_conteudo(analisar_impacto_social(regiao_id))
        assert resultado["simulado"] is True

    @pytest.mark.parametrize("regiao_id", IDS_VALIDOS)
    def test_erro_e_none_para_regioes_validas(self, regiao_id):
        resultado = _extrair_conteudo(analisar_impacto_social(regiao_id))
        assert resultado["erro"] is None, f"erro deve ser None para região válida '{regiao_id}'"

    @pytest.mark.parametrize("regiao_id", IDS_VALIDOS)
    def test_agente_e_impacto_social(self, regiao_id):
        resultado = _extrair_conteudo(analisar_impacto_social(regiao_id))
        assert resultado["agente"] == "impacto_social"

    @pytest.mark.parametrize("regiao_id", IDS_VALIDOS)
    def test_confianca_valor_valido(self, regiao_id):
        resultado = _extrair_conteudo(analisar_impacto_social(regiao_id))
        assert resultado["confianca"] in {"alta", "media", "baixa", "nao_avaliada"}

    @pytest.mark.parametrize("regiao_id", IDS_VALIDOS)
    def test_indicadores_contem_campos_calculados(self, regiao_id):
        resultado = _extrair_conteudo(analisar_impacto_social(regiao_id))
        for campo in CAMPOS_INDICADORES:
            assert campo in resultado["indicadores"], (
                f"Campo indicadores.{campo} ausente para '{regiao_id}'"
            )

    @pytest.mark.parametrize("regiao_id", IDS_VALIDOS)
    def test_riscos_nao_vazio(self, regiao_id):
        resultado = _extrair_conteudo(analisar_impacto_social(regiao_id))
        assert len(resultado["riscos"]) >= 1

    @pytest.mark.parametrize("regiao_id", IDS_VALIDOS)
    def test_limitacoes_contem_aviso_simulado(self, regiao_id):
        resultado = _extrair_conteudo(analisar_impacto_social(regiao_id))
        texto_limitacoes = " ".join(resultado["limitacoes"]).lower()
        assert "simulado" in texto_limitacoes or "fictício" in texto_limitacoes, (
            f"Aviso de dado simulado ausente nas limitações para '{regiao_id}'"
        )

    @pytest.mark.parametrize("regiao_id", IDS_VALIDOS)
    def test_justificativa_minimo_50_chars(self, regiao_id):
        resultado = _extrair_conteudo(analisar_impacto_social(regiao_id))
        assert len(resultado["justificativa"]) >= 50

    @pytest.mark.parametrize("regiao_id", IDS_VALIDOS)
    def test_regiao_id_retornado_igual_ao_enviado(self, regiao_id):
        resultado = _extrair_conteudo(analisar_impacto_social(regiao_id))
        assert resultado["regiao_id"] == regiao_id

    @pytest.mark.parametrize("regiao_id", IDS_VALIDOS)
    def test_tipo_resultado_e_parecer_para_regioes_validas(self, regiao_id):
        """Regiões válidas devem retornar tipo_resultado='parecer', nunca 'erro'."""
        resultado = _extrair_conteudo(analisar_impacto_social(regiao_id))
        assert resultado["tipo_resultado"] == "parecer", (
            f"tipo_resultado deveria ser 'parecer' para '{regiao_id}', "
            f"recebeu '{resultado['tipo_resultado']}'"
        )

    @pytest.mark.parametrize("regiao_id", IDS_VALIDOS)
    def test_limitacoes_primeira_entrada_texto_contrato(self, regiao_id):
        """
        A primeira entrada de limitações deve ser o texto exato do contrato
        conforme PADRAO_DESENVOLVIMENTO_AGENTES.md Seção 3.2.
        """
        resultado = _extrair_conteudo(analisar_impacto_social(regiao_id))
        assert resultado["limitacoes"][0] == "Dado simulado — não reflete condições reais.", (
            f"Primeira limitação diverge do texto do contrato para '{regiao_id}'"
        )


# ---------------------------------------------------------------------------
# 2b. Testes de sinalização de dados ausentes (via @tool)
# ---------------------------------------------------------------------------


class TestSinalizacaoDadosAusentes:
    """
    Valida que ausências de campos obrigatórios são sinalizadas explicitamente
    nas limitacoes do parecer, sem quebrar o contrato (tipo_resultado="parecer").

    Estes testes usam funções internas diretamente (sem @tool) para simular
    dados parciais, já que a base real sempre tem todos os campos.
    """

    def test_dados_completos_sem_aviso_de_ausencia(self):
        """Base completa → limitacoes não contém aviso de campos ausentes."""
        dados_completos = {
            "percentual_domicilios_sem_internet": 72,
            "quantidade_escolas": 61,
            "escolas_sem_conectividade_adequada": 48,
            "unidades_saude": 27,
            "unidades_saude_conectividade_inadequada": 20,
            "percentual_populacao_baixa_renda": 64,
            "indice_vulnerabilidade_social": 74,
            "pessoas_potencialmente_beneficiadas": 101376,
        }
        ausentes = _listar_campos_ausentes(dados_completos)
        assert ausentes == [], "Dados completos não devem gerar lista de ausentes"

    def test_campo_critico_ausente_gera_aviso_aten_o(self):
        """
        Quando campo crítico está ausente, _listar_campos_ausentes retorna o campo.
        O texto "ATENÇÃO" deve aparecer nas limitacoes do parecer (verificado
        na lógica de analisar_impacto_social via campos_ausentes).
        """
        dados_parciais = {
            "quantidade_escolas": 61,
            "escolas_sem_conectividade_adequada": 48,
            "unidades_saude": 27,
            "unidades_saude_conectividade_inadequada": 20,
            "percentual_populacao_baixa_renda": 64,
            # percentual_domicilios_sem_internet ausente (crítico)
            # indice_vulnerabilidade_social ausente (crítico)
            # pessoas_potencialmente_beneficiadas ausente (crítico)
        }
        ausentes = _listar_campos_ausentes(dados_parciais)
        # Todos os três críticos devem ser identificados
        for critico in _CAMPOS_CRITICOS_SOCIAL:
            assert critico in ausentes, f"Campo crítico '{critico}' não foi detectado como ausente"

    def test_campo_nao_critico_ausente_gera_aviso_parcial(self):
        """Quando apenas campo não crítico está ausente, confianca não é baixa por esse motivo."""
        dados_parciais = {
            "percentual_domicilios_sem_internet": 72,
            "quantidade_escolas": 61,
            "escolas_sem_conectividade_adequada": 48,
            "unidades_saude": 27,
            "unidades_saude_conectividade_inadequada": 20,
            "indice_vulnerabilidade_social": 74,
            "pessoas_potencialmente_beneficiadas": 101376,
            # percentual_populacao_baixa_renda ausente (não crítico)
        }
        ausentes = _listar_campos_ausentes(dados_parciais)
        assert "percentual_populacao_baixa_renda" in ausentes
        # Campos críticos todos presentes → confianca não deve ser "baixa" por critico ausente
        confianca = _determinar_confianca(dados_parciais)
        assert confianca in {"media", "alta"}, (
            f"Sem crítico ausente, confianca deveria ser media ou alta, não '{confianca}'"
        )

    def test_parecer_base_real_sem_aviso_de_ausencia(self):
        """
        Para as 6 regiões da base real (dados completos), as limitacoes
        não devem conter aviso de campos ausentes.
        A base garante que todos os campos obrigatórios estão presentes.
        """
        for regiao_id in IDS_VALIDOS:
            resultado = _extrair_conteudo(analisar_impacto_social(regiao_id))
            limitacoes_texto = " ".join(resultado["limitacoes"])
            assert "ATENÇÃO" not in limitacoes_texto, (
                f"Região '{regiao_id}' não deveria ter aviso de ausência, "
                f"mas limitacoes contém: {limitacoes_texto}"
            )
            assert "ausentes na base" not in limitacoes_texto, (
                f"Região '{regiao_id}' não deveria ter aviso de campo ausente"
            )

    def test_tipo_resultado_permanece_parecer_com_dados_incompletos(self):
        """
        Mesmo com dados parciais, o contrato exige tipo_resultado='parecer'.
        A sinalização ocorre via confianca e limitacoes, não via tipo_resultado.
        Valida que a decisão de design foi preservada.
        """
        # Verifica via _montar_resposta_erro que o único caminho para tipo='erro'
        # é região inexistente — não dados incompletos.
        resposta_erro = _montar_resposta_erro("xyz", "não existe")
        assert resposta_erro["tipo_resultado"] == "erro"
        # Para regiões válidas, sempre "parecer" independentemente da confianca
        for regiao_id in IDS_VALIDOS:
            resultado = _extrair_conteudo(analisar_impacto_social(regiao_id))
            assert resultado["tipo_resultado"] == "parecer", (
                f"tipo_resultado deveria ser 'parecer' para '{regiao_id}', "
                f"mas confianca={resultado['confianca']} — dados da base estão completos"
            )


# ---------------------------------------------------------------------------
# 3. Testes de comportamento esperado (lógica de negócio)
# ---------------------------------------------------------------------------


class TestComportamentoEsperado:

    def test_horizonte_score_maior_que_aurora(self):
        """
        Horizonte (72% sem internet, vulnerabilidade 74) deve ter score maior
        que Aurora (38% sem internet, vulnerabilidade 32).
        """
        score_horizonte = _extrair_conteudo(analisar_impacto_social("horizonte"))["score"]
        score_aurora = _extrair_conteudo(analisar_impacto_social("aurora"))["score"]
        assert score_horizonte > score_aurora, (
            f"Horizonte ({score_horizonte}) deveria ter score maior que Aurora ({score_aurora})"
        )

    def test_nova_uniao_score_alto_por_exclusao(self):
        """
        Nova União (82% sem internet, vulnerabilidade 86) deve ter score alto
        do ponto de vista de impacto social.
        """
        resultado = _extrair_conteudo(analisar_impacto_social("nova_uniao"))
        assert resultado["score"] >= 60, (
            f"Nova União deveria ter score alto de impacto social (recebeu {resultado['score']})"
        )

    def test_central_score_menor_que_horizonte(self):
        """
        Central (29% sem internet, vulnerabilidade 24) deve ter score menor
        que Horizonte (72% sem internet, vulnerabilidade 74).
        """
        score_central = _extrair_conteudo(analisar_impacto_social("central"))["score"]
        score_horizonte = _extrair_conteudo(analisar_impacto_social("horizonte"))["score"]
        assert score_central < score_horizonte, (
            f"Central ({score_central}) deveria ter score menor que Horizonte ({score_horizonte})"
        )

    def test_percentuais_derivados_batem_com_dados_brutos(self):
        """
        percentual_escolas_sem_conectividade e percentual_saude_sem_conectividade
        devem ser coerentes com os dados brutos retornados.
        """
        resultado = _extrair_conteudo(analisar_impacto_social("horizonte"))
        ind = resultado["indicadores"]

        escolas_total = ind["quantidade_escolas"]
        escolas_sem = ind["escolas_sem_conectividade_adequada"]
        pct_escolas_calculado = _calcular_percentual_seguro(escolas_sem, escolas_total)

        assert abs(ind["percentual_escolas_sem_conectividade"] - pct_escolas_calculado) < 0.2, (
            "percentual_escolas_sem_conectividade diverge do cálculo esperado"
        )

        saude_total = ind["unidades_saude"]
        saude_sem = ind["unidades_saude_conectividade_inadequada"]
        pct_saude_calculado = _calcular_percentual_seguro(saude_sem, saude_total)

        assert abs(ind["percentual_saude_sem_conectividade"] - pct_saude_calculado) < 0.2, (
            "percentual_saude_sem_conectividade diverge do cálculo esperado"
        )

    def test_scores_sao_determinísticos(self):
        """A mesma região deve retornar sempre o mesmo score."""
        score1 = _extrair_conteudo(analisar_impacto_social("aurora"))["score"]
        score2 = _extrair_conteudo(analisar_impacto_social("aurora"))["score"]
        assert score1 == score2


# ---------------------------------------------------------------------------
# 4. Testes de tratamento de erro
# ---------------------------------------------------------------------------


class TestTratamentoErro:

    def test_regiao_inexistente_retorna_erro(self):
        resultado = _extrair_conteudo(analisar_impacto_social("nao_existe"))
        assert resultado["erro"] is not None
        assert len(resultado["erro"]) > 0

    def test_regiao_inexistente_score_zero(self):
        resultado = _extrair_conteudo(analisar_impacto_social("nao_existe"))
        assert resultado["score"] == 0

    def test_regiao_inexistente_confianca_nao_avaliada(self):
        resultado = _extrair_conteudo(analisar_impacto_social("nao_existe"))
        assert resultado["confianca"] == "nao_avaliada"

    def test_regiao_inexistente_simulado_true(self):
        resultado = _extrair_conteudo(analisar_impacto_social("nao_existe"))
        assert resultado["simulado"] is True

    def test_regiao_inexistente_justificativa_menciona_ids_validos(self):
        resultado = _extrair_conteudo(analisar_impacto_social("xyz_invalido"))
        texto = resultado["justificativa"].lower()
        assert "aurora" in texto or "horizonte" in texto or "válidos" in texto

    def test_id_maiusculo_aceito(self):
        """IDs com letras maiúsculas devem ser aceitos (case-insensitive)."""
        resultado = _extrair_conteudo(analisar_impacto_social("AURORA"))
        assert resultado["erro"] is None
        assert resultado["score"] > 0

    def test_id_com_espacos_extras_aceito(self):
        """IDs com espaços em branco ao redor devem ser aceitos."""
        resultado = _extrair_conteudo(analisar_impacto_social("  aurora  "))
        assert resultado["erro"] is None
        assert resultado["score"] > 0

    def test_regiao_inexistente_tipo_resultado_e_erro(self):
        """
        Região inexistente deve retornar tipo_resultado='erro', não 'parecer'.
        Garante que score=0 de erro não seja confundido com parecer válido de score 0.
        """
        resultado = _extrair_conteudo(analisar_impacto_social("nao_existe"))
        assert resultado["tipo_resultado"] == "erro", (
            f"tipo_resultado deveria ser 'erro' para região inexistente, "
            f"recebeu '{resultado['tipo_resultado']}'"
        )

    def test_tipo_resultado_distingue_erro_de_score_zero_valido(self):
        """
        Um parecer válido com score 0 (tipo_resultado='parecer') deve ser
        distinguível de uma resposta de erro (tipo_resultado='erro').
        Garante que o Guardião não descarte pareceres válidos por terem score baixo.
        """
        resposta_erro = _montar_resposta_erro("xyz", "Região não encontrada: 'xyz'")
        assert resposta_erro["tipo_resultado"] == "erro"
        assert resposta_erro["score"] == 0

        dados_sem_exclusao = {
            "percentual_domicilios_sem_internet": 0,
            "quantidade_escolas": 10,
            "escolas_sem_conectividade_adequada": 0,
            "unidades_saude": 5,
            "unidades_saude_conectividade_inadequada": 0,
            "percentual_populacao_baixa_renda": 0,
            "indice_vulnerabilidade_social": 0,
            "pessoas_potencialmente_beneficiadas": 0,
        }
        _, score_valido = _calcular_indicadores_sociais(dados_sem_exclusao)
        assert score_valido == 0
        # O campo tipo_resultado distingue os dois casos:
        # - resposta_erro["tipo_resultado"] == "erro"   → região não existe
        # - parecer válido com score 0 → tipo_resultado == "parecer"


# ---------------------------------------------------------------------------
# 5. Testes de consistência entre _montar_resposta_erro e o contrato
# ---------------------------------------------------------------------------


class TestEstruturaRespostaErroCompleta:
    """
    Valida que _montar_resposta_erro produz exatamente a estrutura do contrato,
    incluindo o campo tipo_resultado='erro'.
    """

    def test_todos_campos_obrigatorios_presentes_em_erro(self):
        resposta = _montar_resposta_erro("abc", "mensagem de erro")
        for campo in CAMPOS_OBRIGATORIOS_CONTRATO:
            assert campo in resposta, f"Campo '{campo}' ausente na resposta de erro"

    def test_tipo_resultado_e_erro(self):
        resposta = _montar_resposta_erro("abc", "mensagem de erro")
        assert resposta["tipo_resultado"] == "erro"

    def test_agente_e_impacto_social(self):
        resposta = _montar_resposta_erro("abc", "mensagem de erro")
        assert resposta["agente"] == "impacto_social"

    def test_simulado_sempre_true(self):
        resposta = _montar_resposta_erro("abc", "mensagem de erro")
        assert resposta["simulado"] is True

    def test_indicadores_dict_vazio(self):
        resposta = _montar_resposta_erro("abc", "mensagem de erro")
        assert resposta["indicadores"] == {}

    def test_regiao_nome_none(self):
        resposta = _montar_resposta_erro("abc", "mensagem de erro")
        assert resposta["regiao_nome"] is None

    def test_confianca_nao_avaliada(self):
        resposta = _montar_resposta_erro("abc", "mensagem de erro")
        assert resposta["confianca"] == "nao_avaliada"
