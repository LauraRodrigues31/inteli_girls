# Guia de Integração IBM Cloud — Agente de Impacto Social

**Agente:** `cc_impacto_social`
**Arquivo de ferramenta:** `tools/tool_social.py`
**Responsável pela integração:** pessoa designada para publicação no workspace IBM Trial

> ⚠️ Esta documentação é de responsabilidade do Integrante 2 (Agente de Impacto Social).
> Não descreve o processo de outros agentes.

---

## 1. Dependências locais que precisam ser disponibilizadas

O `tool_social.py` depende de três componentes locais que **não são enviados automaticamente**
pelo comando `orchestrate tool import`. A pessoa responsável pela integração precisa garantir
que os três estejam acessíveis no ambiente de execução da IBM Cloud.

### 1.1 `consultar_regiao.py` (obrigatório)

| Atributo | Valor |
|---|---|
| Caminho local | `conecta-conselho/tools/consultar_regiao.py` |
| Como é referenciado | `from tools.consultar_regiao import consultar_social, listar_ids_regioes` |
| Mecanismo de resolução | `sys.path.insert(0, Path(__file__).parent.parent / "conecta-conselho")` |

**Problema:** no ambiente IBM Cloud, `Path(__file__)` aponta para onde o arquivo foi carregado,
e o diretório `conecta-conselho/` **não existe** ao lado do `tool_social.py`.

**O que fazer:** enviar `consultar_regiao.py` junto com `tool_social.py` no mesmo diretório,
**ou** usar o mecanismo de toolkit/package do ADK para agrupar os dois arquivos.
Verificar com a equipe qual mecanismo está disponível no workspace Trial.

### 1.2 `regioes.json` (obrigatório)

| Atributo | Valor |
|---|---|
| Caminho local | `conecta-conselho/data/regioes.json` |
| Como é referenciado | Dentro de `consultar_regiao.py`, via `Path(__file__).parent.parent / "data" / "regioes.json"` |

**Problema:** `consultar_regiao.py` usa caminho relativo ao seu próprio `__file__`.
No ambiente remoto, o JSON não estará no caminho esperado.

**O que fazer:** enviar `regioes.json` na estrutura de diretórios esperada por `consultar_regiao.py`,
ou adaptar `consultar_regiao.py` para aceitar um caminho configurável via variável de ambiente.
**Não alterar `consultar_regiao.py` sem aprovação da equipe** (arquivo compartilhado).

### 1.3 `ibm_watsonx_orchestrate` (resolvido automaticamente)

O import do ADK usa `try/except` com fallback:

```python
try:
    from ibm_watsonx_orchestrate.agent_builder.tools import tool as tool
    _ADK_DISPONIVEL = True
except ImportError:
    def tool(func): return func
    _ADK_DISPONIVEL = False
```

No ambiente IBM Cloud, o pacote `ibm_watsonx_orchestrate` está disponível por padrão.
Nenhuma ação adicional é necessária para essa dependência.

---

## 2. Como o ADK calcula o `function_binding`

Ao executar `orchestrate tool import tools/tool_social.py`, o ADK registra:

```
tools.tool_social:analisar_impacto_social
```

Esse binding é calculado como caminho relativo ao `cwd` no momento do import,
convertido para notação de módulo Python. Isso significa que o arquivo deve ser
importável como `tools.tool_social` a partir do diretório raiz do projeto.

---

## 3. Checklist antes do `orchestrate tool import`

- [ ] Confirmar que `consultar_regiao.py` e `regioes.json` estarão acessíveis no ambiente de execução
- [ ] Confirmar que o modelo `watsonx/meta-llama/llama-3-2-90b-vision-instruct` está disponível no workspace Trial
      (alternativa comum: `watsonx/meta-llama/llama-3-1-70b-instruct`)
- [ ] Executar `python -m pytest conecta-conselho/tests/test_agente_social.py -q` localmente antes do import
- [ ] Verificar que `_ADK_DISPONIVEL` é `True` no ambiente de execução (pode ser logado no `print` de info)
- [ ] Não publicar sem alinhamento com o responsável pelo Guardião — o Guardião consome o output deste agente

---

## 4. Comportamento com dados incompletos

Caso a base de dados tenha campos ausentes ou `None` (não esperado com a base atual,
mas possível em versões futuras), o agente:

1. Calcula os sub-scores com `0` para campos ausentes (determinístico, sem exceção)
2. Registra `confianca="baixa"` no parecer
3. Adiciona aviso explícito nas `limitacoes` com os nomes dos campos ausentes

**Como o Guardião interpreta:**
- **Erro fatal** (região não encontrada): `erro != null` **e** `confianca == "nao_avaliada"`.
- **Parecer parcial** (dados incompletos): `confianca == "baixa"`. O texto de `limitacoes` é apenas informativo.
- **Parecer válido** (dados completos): `erro == null` e `confianca` em `{"alta", "media"}`.

---

## 5. Arquivos de propriedade deste integrante

| Arquivo | Pode modificar? |
|---|---|
| `tools/tool_social.py` | ✅ Sim |
| `agents/agente_social.yaml` | ✅ Sim |
| `conecta-conselho/tests/test_agente_social.py` | ✅ Sim |
| `agents/INTEGRACAO_IBM_agente_social.md` | ✅ Sim |
| `conecta-conselho/tools/consultar_regiao.py` | ❌ Não — arquivo compartilhado |
| `conecta-conselho/data/regioes.json` | ❌ Não — arquivo compartilhado |
| `conecta-conselho/models/regiao.py` | ❌ Não — arquivo compartilhado |
| `conecta-conselho/docs/PADRAO_DESENVOLVIMENTO_AGENTES.md` | ❌ Não sem aprovação do grupo |
