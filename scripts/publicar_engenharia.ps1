<#
.SYNOPSIS
    Publica o agente cc_engenharia no IBM watsonx Orchestrate.

.DESCRIPTION
    Wrapper específico para a integrante responsável pelo agente de engenharia.
    Equivale a: scripts\publicar_agente.ps1 -Nome engenharia

    Fluxo:
      1. Lê WXO_API_KEY do .env e ativa o ambiente conecta-conselho.
      2. Gera _build/tool_engenharia_nuvem.py (versão self-contained sem imports externos).
      3. Importa a ferramenta analisar_engenharia no ADK.
      4. Importa o agente cc_engenharia (agents/agente_engenharia.yaml).
      5. Imprime instruções de teste.

.NOTES
    Regras do workspace compartilhado:
      - Avise no grupo ANTES de publicar.
      - NUNCA rode orchestrate chat ask — trava no Windows (EOF infinito).
      - Para testar use a API REST ou Agent Builder → Preview:
          $env:PYTHONIOENCODING = "utf-8"
          .venv\Scripts\python.exe _build\test_cc_engenharia.py
        ou
          https://jp-tok.watson-orchestrate.cloud.ibm.com → Agent Builder → cc_engenharia → Preview

.EXAMPLE
    scripts\publicar_engenharia.ps1
#>

$ErrorActionPreference = "Stop"

# Delega para o script genérico com -Nome engenharia
$script = Join-Path $PSScriptRoot "publicar_agente.ps1"

if (!(Test-Path $script)) {
    Write-Host "[ERRO] Script base nao encontrado: $script" -ForegroundColor Red
    exit 1
}

Write-Host "==> Publicando cc_engenharia via publicar_agente.ps1 -Nome engenharia ..." -ForegroundColor Cyan
& $script -Nome engenharia

# Instruções de teste específicas para engenharia
if ($LASTEXITCODE -eq 0) {
    Write-Host @"

============================================================
  COMO TESTAR cc_engenharia (nao use orchestrate chat ask)
============================================================

  OPCAO A — API REST (Python, nao trava no Windows):
    `$env:PYTHONIOENCODING = "utf-8"
    .venv\Scripts\python.exe _build\test_cc_engenharia.py

    Testes executados (resultados esperados):
      T1  Analise a engenharia da regiao central     → score 86
      T2  Analise a regiao nova_uniao               → score 11
      T3  Analise a regiao atlantida                → score 0, confianca nao_avaliada
      T4  (multi-turn de T1) risco tecnico dela     → resposta baseada nos riscos do parecer

  OPCAO B — Pela tela (sem instalar nada):
    1. https://jp-tok.watson-orchestrate.cloud.ibm.com
    2. Agent Builder → cc_engenharia → Preview

  NAO use 'orchestrate chat ask' — trava no Windows (EOF infinito).

"@ -ForegroundColor Green
}
