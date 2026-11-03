<#
.SYNOPSIS
    Gera e publica (importa) ferramenta + agente no IBM watsonx Orchestrate.

.DESCRIPTION
    Etapa 7 do piloto Conecta Conselho.

    Fluxo para um nome:
      1. Lê WXO_API_KEY do .env e ativa o ambiente conecta-conselho (se necessário).
      2. Executa scripts/gerar_ferramenta_nuvem.py -Nome → gera _build/tool_<nome>_nuvem.py.
      3. Importa _build/tool_<nome>_nuvem.py como ferramenta Python no ADK.
      4. Importa agents/agente_<nome>.yaml como agente.
      5. Lista os artefatos publicados para confirmação.

.PARAMETER Nome
    Nome do agente a publicar.
    Valores válidos: engenharia, mercado, social, orcamento, pontes

.NOTES
    Regras do workspace compartilhado:
      - Só mexa em recursos com o seu próprio nome.
      - Avise no grupo ANTES de publicar.
      - Uma pessoa por vez — publicações simultâneas causam conflito.
      - NUNCA rode orchestrate chat ask — trava no Windows (EOF infinito).
      - Para testar use: python scripts\testar_agente_nuvem.py <nome>
        ou Agent Builder → Preview na tela.

.EXAMPLE
    # Publica o agente de engenharia (Laura)
    scripts\publicar_agente.ps1 -Nome engenharia

    # Publica o agente de mercado
    scripts\publicar_agente.ps1 -Nome mercado
#>

[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)]
    [ValidateSet("engenharia", "mercado", "social", "orcamento", "pontes")]
    [string]$Nome
)

$ErrorActionPreference = "Stop"
$env:PYTHONIOENCODING  = "utf-8"
$env:PYTHONDONTWRITEBYTECODE = "1"

# ---------------------------------------------------------------------------
# Caminhos
# ---------------------------------------------------------------------------
$ROOT        = Split-Path $PSScriptRoot -Parent
$ORCHESTRATE = Join-Path $ROOT ".venv\Scripts\orchestrate.exe"
$PYTHON      = Join-Path $ROOT ".venv\Scripts\python.exe"
$GERADOR     = Join-Path $ROOT "scripts\gerar_ferramenta_nuvem.py"
$TOOL_FILE   = Join-Path $ROOT "_build\tool_${Nome}_nuvem.py"
$AGENT_FILE  = Join-Path $ROOT "agents\agente_${Nome}.yaml"
$ENV_FILE    = Join-Path $ROOT ".env"
$ENV_NAME    = "conecta-conselho"

# Resolve executáveis
if (!(Test-Path $ORCHESTRATE)) { throw "orchestrate.exe não encontrado em $ORCHESTRATE" }
if (!(Test-Path $PYTHON))       { throw "python.exe não encontrado em $PYTHON" }
if (!(Test-Path $GERADOR))      { throw "Gerador não encontrado em $GERADOR" }
if (!(Test-Path $AGENT_FILE))   { throw "YAML do agente não encontrado em $AGENT_FILE" }

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
function Write-Step([string]$msg) { Write-Host "`n==> $msg" -ForegroundColor Cyan }
function Write-OK([string]$msg)   { Write-Host "    [OK] $msg" -ForegroundColor Green }
function Write-Warn([string]$msg) { Write-Host "    [AVISO] $msg" -ForegroundColor Yellow }
function Write-Fail([string]$msg) { Write-Host "    [ERRO] $msg" -ForegroundColor Red }

# ---------------------------------------------------------------------------
# 1. Ler API key do .env sem expô-la
# ---------------------------------------------------------------------------
Write-Step "Lendo credenciais do .env ..."

if (!(Test-Path $ENV_FILE)) {
    Write-Fail ".env não encontrado em $ENV_FILE"
    exit 1
}

$apiKey = $null
foreach ($linha in Get-Content $ENV_FILE) {
    if ($linha -match '^WXO_API_KEY\s*=\s*(.+)$') {
        $apiKey = $Matches[1].Trim()
        break
    }
}

if ([string]::IsNullOrWhiteSpace($apiKey)) {
    Write-Fail "WXO_API_KEY não encontrada no .env"
    exit 1
}

Write-OK "Credenciais lidas (não exibidas)."

# ---------------------------------------------------------------------------
# 2. Ativar ambiente
# ---------------------------------------------------------------------------
Write-Step "Ativando ambiente '$ENV_NAME' ..."

$activateOut = & $ORCHESTRATE env activate $ENV_NAME --api-key $apiKey 2>&1
$activateOut | ForEach-Object { Write-Host "    $_" }

if ($LASTEXITCODE -ne 0) {
    Write-Fail "Falha ao ativar ambiente '$ENV_NAME'."
    exit 1
}
Write-OK "Ambiente ativado."

# ---------------------------------------------------------------------------
# 3. Gerar ferramenta self-contained
# ---------------------------------------------------------------------------
Write-Step "Gerando ferramenta self-contained: tool_${Nome}_nuvem.py ..."

$genOut = & $PYTHON $GERADOR $Nome 2>&1
$genOut | ForEach-Object { Write-Host "    $_" }

if ($LASTEXITCODE -ne 0) {
    Write-Fail "Falha ao gerar ferramenta."
    exit 1
}

if (!(Test-Path $TOOL_FILE)) {
    Write-Fail "Arquivo gerado não encontrado: $TOOL_FILE"
    exit 1
}
Write-OK "Ferramenta gerada: $TOOL_FILE"

# ---------------------------------------------------------------------------
# 4. Importar ferramenta
# ---------------------------------------------------------------------------
Write-Step "Importando ferramenta no ADK ..."
Write-Host "    $TOOL_FILE"

$toolOut = & $ORCHESTRATE tools import -k python -f $TOOL_FILE 2>&1
$toolOut | ForEach-Object { Write-Host "    $_" }

if ($LASTEXITCODE -ne 0) {
    Write-Fail "Falha ao importar ferramenta."
    exit 1
}

if ($toolOut -match "updated successfully|imported successfully") {
    Write-OK "Ferramenta importada/atualizada com sucesso."
} else {
    Write-Warn "Verificar saída acima — import pode ter retornado aviso."
}

# ---------------------------------------------------------------------------
# 5. Importar agente
# ---------------------------------------------------------------------------
Write-Step "Importando agente: agente_${Nome}.yaml ..."
Write-Host "    $AGENT_FILE"

$agentOut = & $ORCHESTRATE agents import -f $AGENT_FILE 2>&1
$agentOut | ForEach-Object { Write-Host "    $_" }

if ($LASTEXITCODE -ne 0) {
    Write-Fail "Falha ao importar agente."
    exit 1
}

if ($agentOut -match "updated successfully|imported successfully") {
    Write-OK "Agente importado/atualizado com sucesso."
} else {
    Write-Warn "Verificar saída acima — import pode ter retornado aviso."
}

# ---------------------------------------------------------------------------
# 6. Confirmação final
# ---------------------------------------------------------------------------
Write-Step "Artefatos publicados em '$ENV_NAME':"

Write-Host "`n  Ferramentas:" -ForegroundColor White
& $ORCHESTRATE tools list 2>&1 | ForEach-Object { Write-Host "    $_" }

Write-Host "`n  Agentes:" -ForegroundColor White
& $ORCHESTRATE agents list 2>&1 | ForEach-Object { Write-Host "    $_" }

# ---------------------------------------------------------------------------
# 7. Instruções de teste
# ---------------------------------------------------------------------------
# Mapa nome → nome real do agente no Orchestrate
$agentNomeReal = @{
    "engenharia" = "cc_engenharia"
    "mercado"    = "cc_mercado"
    "social"     = "cc_impacto_social"
    "orcamento"  = "cc_orcamento"
    "pontes"     = "cc_pontes"
}[$Nome]

Write-Host @"

============================================================
  PUBLICACAO CONCLUIDA: $agentNomeReal em '$ENV_NAME'
============================================================

  REGRAS DO WORKSPACE COMPARTILHADO:
    - Avise no grupo que terminou de publicar.
    - Nao teste recursos de outras integrantes.

  Para testar o agente, escolha UMA opcao:

  A) Pela tela (sem instalar nada):
     1. https://jp-tok.watson-orchestrate.cloud.ibm.com
     2. Agent Builder -> $agentNomeReal -> Preview

  B) Pela API REST (Python — nao trava no Windows):
     `$env:PYTHONIOENCODING = "utf-8"
     python scripts\testar_agente_nuvem.py $Nome

  NAO use 'orchestrate chat ask' — trava no Windows (EOF infinito).

"@ -ForegroundColor Green
