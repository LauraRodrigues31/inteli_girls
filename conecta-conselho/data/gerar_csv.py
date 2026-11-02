"""
Script para gerar regioes.csv a partir de regioes.json.

O JSON é a fonte única da verdade. Este script deve ser executado
sempre que o JSON for atualizado.

Uso:
    python gerar_csv.py

Ou a partir da raiz do projeto:
    python conecta-conselho/data/gerar_csv.py
"""

import csv
import json
from pathlib import Path


DATA_DIR = Path(__file__).parent
JSON_PATH = DATA_DIR / "regioes.json"
CSV_PATH = DATA_DIR / "regioes.csv"


def gerar_csv() -> None:
    with open(JSON_PATH, encoding="utf-8") as f:
        dados = json.load(f)

    regioes = dados["regioes"]
    linhas = []

    for r in regioes:
        m = r["mercado"]
        s = r["social"]
        e = r["engenharia"]
        fin = r["financeiro"]
        p = r["parcerias"]

        linha = {
            # Identificação
            "id": r["id"],
            "nome": r["nome"],
            "descricao_perfil": r["descricao_perfil"],
            # Mercado
            "populacao_estimada": m["populacao_estimada"],
            "domicilios_total": m["domicilios_total"],
            "renda_media_mensal_reais": m["renda_media_mensal_reais"],
            "taxa_crescimento_populacional_pct": m["taxa_crescimento_populacional_pct"],
            "percentual_domicilios_conectados": m["percentual_domicilios_conectados"],
            "clientes_potenciais": m["clientes_potenciais"],
            "ticket_medio_mensal_reais": m["ticket_medio_mensal_reais"],
            "numero_concorrentes": m["numero_concorrentes"],
            # Social
            "percentual_domicilios_sem_internet": s["percentual_domicilios_sem_internet"],
            "quantidade_escolas": s["quantidade_escolas"],
            "escolas_sem_conectividade_adequada": s["escolas_sem_conectividade_adequada"],
            "unidades_saude": s["unidades_saude"],
            "unidades_saude_conectividade_inadequada": s["unidades_saude_conectividade_inadequada"],
            "percentual_populacao_baixa_renda": s["percentual_populacao_baixa_renda"],
            "indice_vulnerabilidade_social": s["indice_vulnerabilidade_social"],
            "pessoas_potencialmente_beneficiadas": s["pessoas_potencialmente_beneficiadas"],
            # Engenharia
            "tipo_infraestrutura_disponivel": e["tipo_infraestrutura_disponivel"],
            "distancia_backbone_km": e["distancia_backbone_km"],
            "percentual_cobertura_fibra": e["percentual_cobertura_fibra"],
            "capacidade_infraestrutura_existente": e["capacidade_infraestrutura_existente"],
            "dificuldades_tecnicas": " | ".join(e["dificuldades_tecnicas"]),
            "prazo_implantacao_meses": e["prazo_implantacao_meses"],
            "tecnologias_viaveis": " | ".join(e["tecnologias_viaveis"]),
            "indice_viabilidade_tecnica": e["indice_viabilidade_tecnica"],
            # Financeiro
            "capex_reais": fin["capex_reais"],
            "opex_mensal_reais": fin["opex_mensal_reais"],
            "orcamento_disponivel_reais": fin["orcamento_disponivel_reais"],
            "taxa_adesao_esperada_pct": fin["taxa_adesao_esperada_pct"],
            "receita_mensal_reais": fin["receita_mensal_reais"],
            "payback_meses": fin["payback_meses"] if fin["payback_meses"] is not None else "inviavel",
            "restricoes_orcamentarias": fin["restricoes_orcamentarias"],
            "riscos_financeiros": " | ".join(fin["riscos_financeiros"]),
            # Parcerias
            "quantidade_instituicoes_ancora": p["quantidade_instituicoes_ancora"],
            "parceiros_publicos_possiveis": " | ".join(p["parceiros_publicos_possiveis"]),
            "parceiros_privados_possiveis": " | ".join(p["parceiros_privados_possiveis"]),
            "infraestrutura_compartilhavel": p["infraestrutura_compartilhavel"],
            "oportunidades_reducao_custos": " | ".join(p["oportunidades_reducao_custos"]),
            "percentual_economia_potencial_pct": p["percentual_economia_potencial_pct"],
            "maturidade_parcerias": p["maturidade_parcerias"],
        }
        linhas.append(linha)

    if not linhas:
        print("Nenhuma região encontrada no JSON.")
        return

    with open(CSV_PATH, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(linhas[0].keys()))
        writer.writeheader()
        writer.writerows(linhas)

    print(f"CSV gerado com sucesso: {CSV_PATH}")
    print(f"  {len(linhas)} regiões exportadas, {len(linhas[0])} colunas.")


if __name__ == "__main__":
    gerar_csv()
