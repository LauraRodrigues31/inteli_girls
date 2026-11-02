# Conecta Conselho — Contexto do Projeto

**Trilha 3 · Telecomunicações inteligentes com Fundação Telefônica · 23/10/2026**  
**AI Experiential Learning Lab · IBM SkillsBuild**

> Documento unificado para o repositório. Reúne o texto do *Conecta Conselho – One-pager* (23/10/2026) e a visão atualizada do produto fornecida pela equipe. O conteúdo original foi preservado nas seções de concepção; as especificações mais recentes aparecem na seção **Visão do produto e escopo atualizado do MVP**. Em caso de divergência operacional, prevalecem as especificações atualizadas, sem apagar o histórico da ideia.

## 1. Como os agentes trabalham juntos

Cada região passa por cinco agentes que analisam os mesmos dados públicos, debatem e entregam ao Guardião, que decide e explica o porquê.

### Fluxo conceitual do one-pager

```text
Dados públicos (IBGE, Anatel, INEP, CNES; só fontes abertas)
    │
    ├── Agente de Mercado — defende o retorno financeiro
    ├── Agente de Impacto Social — defende escolas, saúde, inclusão
    ├── Agente de Engenharia — avalia a viabilidade técnica
    ├── Agente de Orçamento — controla custo e prazo
    └── Agente de Pontes — busca clientes âncora
                    │
                    ▼
          Debate: discordam e apresentam evidências
                    │
                    ▼
           Guardião: pesa os argumentos,
           mostra a confiança e explica o motivo
                    │
                    ▼
  Investir agora | Começar com piloto | Esperar | Escalar a um humano
```

**A decisão pode ser:** Investir agora · Começar com piloto · Esperar · Escalar a um humano.

O Agente de Pontes (em destaque) amplia as opções do debate procurando escolas, postos de saúde e prefeituras que sirvam de clientes âncora. O Guardião escolhe entre quatro resultados e, quando a confiança é baixa, escala para uma pessoa.

## 2. O papel de cada agente

Cada agente defende um ponto de vista diferente de propósito, para que nenhuma decisão seja tomada só pelo lucro.

| Agente | Pergunta que responde | O que leva ao debate |
|---|---|---|
| Mercado | Vale a pena financeiramente? | Retorno esperado e risco comercial da região |
| Impacto Social | Quem ganha com a conexão? | Escolas, postos de saúde e comunidades sem acesso |
| Engenharia | Dá para construir? | Relevo, distância e tipo de rede mais adequado |
| Orçamento | Cabe no limite de custo e prazo? | Custo estimado e possibilidade de fazer em fases |
| Pontes | Dá para tornar a região viável? | Clientes âncora (escolas, saúde, prefeituras) que garantem demanda |
| Guardião | O que fazemos? | Decisão, nível de confiança e explicação |

## 3. Exemplo de debate (região fictícia)

Uma região "não lucrativa" pode virar um piloto viável quando o Agente de Pontes entra no debate.

1. Mercado: renda baixa e poucos domicílios; o retorno individual é fraco.
2. Impacto Social: há escolas e um posto de saúde sem conexão; o impacto é alto.
3. Engenharia: o relevo encarece a fibra; rádio ou satélite seriam mais indicados.
4. Orçamento: não cabe tudo de uma vez, mas cabe em duas fases.
5. Pontes: se a operadora atender escolas, posto e prefeitura juntos, a demanda fica garantida e a rede pode ser compartilhada.
6. Guardião: recomenda começar com um piloto, informa a confiança e explica que a decisão depende dos clientes âncora.

## 4. Quando a IA decide e quando chama uma pessoa

O Guardião nunca entrega só uma resposta: entrega decisão, confiança e motivo, e passa para um humano quando não tem segurança.

- **Explicação:** cada decisão mostra os argumentos de cada agente e o que pesou mais.
- **Confiança:** cada decisão vem com um nível de confiança.
- **Escalonamento:** confiança baixa ou agentes em forte desacordo levam a decisão para uma pessoa.
- **Sem dados pessoais:** só fontes públicas e abertas, sem dados de clientes.

---

## 5. Visão do produto e escopo atualizado do MVP

### 5.1 Problema

Operadoras precisam priorizar onde expandir conectividade, conciliando viabilidade comercial, restrições de infraestrutura, orçamento e benefício social. Uma análise isolada pode favorecer áreas rentáveis e ignorar localidades desassistidas. O Conecta Conselho reúne perspectivas especializadas e testa se instituições âncora (escolas, unidades de saúde e outros equipamentos públicos) poderiam melhorar o cenário de atendimento.

### 5.2 Usuário-alvo e decisão apoiada

Usuário principal: analista ou gerente de planejamento de expansão de uma operadora de telecomunicações. Usuários secundários: área de impacto social, equipe técnica e gestores de investimento. O sistema **apoia** a triagem de oportunidades, mas **não autoriza** obras, não calcula orçamento executivo e não substitui análise de campo, regulação ou negociação comercial.

### 5.3 Jornada obrigatória da demonstração

1. Usuário abre o dashboard e visualiza três municípios ou localidades pré-carregados.
2. Seleciona uma localidade e inspeciona indicadores com fontes e ano.
3. Define um teto de investimento hipotético e, opcionalmente, parâmetros de simulação identificados como estimativas.
4. Executa o Conselho.
5. Visualiza pareceres independentes dos agentes de Mercado, Impacto Social, Engenharia e Orçamento.
6. O Agente de Pontes identifica possíveis instituições âncora e sugere um cenário de articulação, sem presumir contratos firmados.
7. Motor determinístico compara cenário base e cenário com pontes.
8. O Guardião sintetiza convergências, divergências, incertezas e recomenda **Investir agora**, **Começar com piloto**, **Esperar** ou **Escalar a um humano**.
9. Usuário consulta evidências, limitações e trilha de auditoria; pode exportar relatório JSON.

### 5.4 Fora do escopo do MVP

Previsão precisa de ROI, CAPEX real, geoprocessamento de engenharia, negociação automática com escolas, integração em tempo real com sistemas de operadoras, contratação de serviços, classificação de pessoas, scraping irrestrito, RAG genérico, banco vetorial e deployment público obrigatório.

### 5.5 Critérios de sucesso observáveis

- Um comando inicia a API e outro inicia o frontend, com README reproduzível.
- Três localidades de demonstração com dados identificados como sintéticos ou oficiais.
- Pelo menos um fluxo ponta a ponta sem serviços pagos e sem credenciais externas.
- Pareceres de agentes exibem justificativa, dados usados, limitações e incertezas.
- Cenários base e pontes são calculados por funções Python testáveis, não por aritmética inventada pelo LLM.
- Recomendações possuem regras de segurança, rastreabilidade e revisão humana.
- Testes automatizados cobrem cálculos, contratos e orquestração em modo mock.

## 6. Diretrizes complementares para o MVP

As diretrizes abaixo acrescentam detalhes de implementação à concepção do one-pager, mantendo os nomes originais dos seis agentes: **Agente de Mercado, Agente de Impacto Social, Agente de Engenharia, Agente de Orçamento, Agente de Pontes e Guardião**.

**Instituições âncora:** o one-pager original usa a expressão “garantem demanda” no quadro e no exemplo fictício. Para o MVP, o Agente de Pontes identifica **possíveis** instituições âncora e modela cenários hipotéticos de articulação, **sem presumir contratos firmados ou demanda garantida**.

**Dados:** o fluxo original cita IBGE, Anatel, INEP e CNES e prevê fontes abertas. A demonstração pode usar localidades com dados **sintéticos ou oficiais**, desde que a natureza dos indicadores esteja explicitamente identificada. Quando um indicador for sintético, sua origem deve ser informada como simulação, sem atribuí-lo indevidamente a fontes oficiais.

**Decisão e cálculos:** o debate entre especialistas permanece central, mas a comparação entre o cenário base e o cenário com pontes deve utilizar **funções Python determinísticas e testáveis**. O Guardião sintetiza pareceres, divergências e incertezas e apresenta uma das quatro decisões definidas no one-pager. A recomendação é apoio à triagem, não autorização de investimento.

**Confiança e revisão humana:** o one-pager pede um nível de confiança para cada decisão. A metodologia desse nível precisa ser explicitada e validada; não deve ser apresentada como probabilidade estatística sem fundamento. Em casos de dados insuficientes, forte divergência ou restrições relevantes, o Guardião deve explicar a incerteza e indicar a necessidade de avaliação humana.

**Rastreabilidade:** os pareceres devem informar indicadores utilizados, fontes e ano quando aplicáveis, justificativas, riscos e limitações. A demonstração deve permitir consultar uma trilha de auditoria e exportar relatório em JSON.

---

*Base documental: “Conecta Conselho – One-pager”, Trilha 3, 23/10/2026, página 1; e texto atualizado “Visão do produto”, seções 1.1 a 1.5, fornecido pela equipe.*
