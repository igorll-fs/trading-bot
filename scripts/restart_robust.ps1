# Script Robusto de Restart do Sistema Trading Bot
# Para e reinicia MongoDB, Backend e Frontend com validações

param(
    [int]$BackendPort = 8000,
    [int]$FrontendPort = 3000,
    [int]$MaxRetries = 3
)

$ErrorActionPreference = "Continue"
Write-Host "`n========================================" -ForegroundColor Cyan
Write-Host " Trading Bot - Restart Robusto" -ForegroundColor Cyan
Write-Host "========================================`n" -ForegroundColor Cyan

$ProjectRoot = Split-Path -Parent $PSScriptRoot

# Função para parar processo em porta específica
function Stop-ProcessOnPort {
    param([int]$Port)
    
    Write-Host "Verificando porta $Port..." -ForegroundColor Yellow
    
    try {
        $processes = Get-NetTCPConnection -LocalPort $Port -ErrorAction SilentlyContinue | 
            Select-Object -ExpandProperty OwningProcess -Unique
        
        if ($processes) {
            foreach ($pid in $processes) {
                Write-Host "  Parando processo PID $pid na porta $Port..." -ForegroundColor Yellow
                Stop-Process -Id $pid -Force -ErrorAction SilentlyContinue
            }
            Start-Sleep -Seconds 2
            Write-Host "  ✓ Porta $Port liberada" -ForegroundColor Green
        } else {
            Write-Host "  ✓ Porta $Port já livre" -ForegroundColor Green
        }
    } catch {
        Write-Host "  ! Erro ao verificar porta $Port`: $_" -ForegroundColor Yellow
    }
}

# Função para verificar se porta está disponível
function Test-PortAvailable {
    param([int]$Port)
    
    try {
        $connection = Get-NetTCPConnection -LocalPort $Port -ErrorAction SilentlyContinue
        return $null -eq $connection
    } catch {
        return $true
    }
}

# Função para aguardar serviço estar pronto
function Wait-ServiceReady {
    param(
        [string]$Url,
        [int]$TimeoutSeconds = 30,
        [string]$Name = "Serviço"
    )
    
    Write-Host "Aguardando $Name iniciar..." -ForegroundColor Yellow
    
    $elapsed = 0
    while ($elapsed -lt $TimeoutSeconds) {
        try {
            $response = Invoke-WebRequest -Uri $Url -Method Get -TimeoutSec 2 -UseBasicParsing -ErrorAction Stop
            if ($response.StatusCode -eq 200) {
                Write-Host "  ✓ $Name pronto!" -ForegroundColor Green
                return $true
            }
        } catch {
            # Ainda não está pronto
        }
        
        Start-Sleep -Seconds 1
        $elapsed++
        
        if ($elapsed % 5 -eq 0) {
            $msg = "  Aguardando... (" + $elapsed + " de " + $TimeoutSeconds + " segundos)"
            Write-Host $msg -ForegroundColor Gray
        }
    }
    
    $errMsg = "  X Timeout: " + $Name + " nao respondeu em " + $TimeoutSeconds + " segundos"
    Write-Host $errMsg -ForegroundColor Red
    return $false
}

# ETAPA 1: Parar todos os serviços
Write-Host "`n[1/5] Parando serviços existentes..." -ForegroundColor Cyan

# Parar processos Python (backend)
Write-Host "Parando processos Python..." -ForegroundColor Yellow
Get-Process -Name "python" -ErrorAction SilentlyContinue | Stop-Process -Force -ErrorAction SilentlyContinue
Start-Sleep -Seconds 1

# Parar processos Node (frontend)
Write-Host "Parando processos Node..." -ForegroundColor Yellow
Get-Process -Name "node" -ErrorAction SilentlyContinue | Stop-Process -Force -ErrorAction SilentlyContinue
Start-Sleep -Seconds 1

# Liberar portas específicas
Stop-ProcessOnPort -Port $BackendPort
Stop-ProcessOnPort -Port $FrontendPort

Write-Host "✓ Serviços parados`n" -ForegroundColor Green

# ETAPA 2: Verificar MongoDB
Write-Host "[2/5] Verificando MongoDB..." -ForegroundColor Cyan

$mongoService = Get-Service -Name "MongoDB" -ErrorAction SilentlyContinue

if ($null -eq $mongoService) {
    Write-Host "✗ MongoDB não encontrado como serviço!" -ForegroundColor Red
    Write-Host "Instale MongoDB Community Server ou configure manualmente." -ForegroundColor Yellow
    exit 1
}

if ($mongoService.Status -ne "Running") {
    Write-Host "MongoDB parado. Tentando iniciar..." -ForegroundColor Yellow
    try {
        Start-Service -Name "MongoDB" -ErrorAction Stop
        Start-Sleep -Seconds 3
        Write-Host "✓ MongoDB iniciado" -ForegroundColor Green
    } catch {
        Write-Host "✗ Erro ao iniciar MongoDB: $_" -ForegroundColor Red
        Write-Host "Execute este script como Administrador." -ForegroundColor Yellow
        exit 1
    }
} else {
    Write-Host "✓ MongoDB rodando`n" -ForegroundColor Green
}

# ETAPA 3: Iniciar Backend
Write-Host "[3/5] Iniciando Backend (porta $BackendPort)..." -ForegroundColor Cyan

# Garantir que porta está livre
if (-not (Test-PortAvailable -Port $BackendPort)) {
    Write-Host "✗ Porta $BackendPort ainda ocupada!" -ForegroundColor Red
    Stop-ProcessOnPort -Port $BackendPort
    Start-Sleep -Seconds 2
}

# Ativar venv e iniciar backend
$backendPath = Join-Path $ProjectRoot "backend"
$venvActivate = Join-Path $ProjectRoot ".venv\Scripts\Activate.ps1"

if (-not (Test-Path $venvActivate)) {
    Write-Host "✗ Virtual environment não encontrado!" -ForegroundColor Red
    Write-Host "Crie o venv primeiro: python -m venv .venv" -ForegroundColor Yellow
    exit 1
}

# Iniciar backend em background
$backendJob = Start-Job -ScriptBlock {
    param($venvPath, $backendPath, $port)
    Set-Location $backendPath
    & $venvPath
    python -m uvicorn server:app --host 0.0.0.0 --port $port --reload
} -ArgumentList $venvActivate, $backendPath, $BackendPort

Start-Sleep -Seconds 3

# Validar se backend iniciou
$backendReady = Wait-ServiceReady -Url "http://localhost:$BackendPort/api/health" -TimeoutSeconds 30 -Name "Backend"

if (-not $backendReady) {
    Write-Host "✗ Backend falhou ao iniciar!" -ForegroundColor Red
    Write-Host "Verifique logs em backend/uvicorn*.err" -ForegroundColor Yellow
    $backendJob | Stop-Job -ErrorAction SilentlyContinue
    exit 1
}

# ETAPA 4: Iniciar Frontend
Write-Host "`n[4/5] Iniciando Frontend (porta $FrontendPort)..." -ForegroundColor Cyan

# Garantir que porta está livre
if (-not (Test-PortAvailable -Port $FrontendPort)) {
    Write-Host "Porta $FrontendPort ocupada. Liberando..." -ForegroundColor Yellow
    Stop-ProcessOnPort -Port $FrontendPort
    Start-Sleep -Seconds 2
}

$frontendPath = Join-Path $ProjectRoot "frontend"

# Verificar se node_modules existe
if (-not (Test-Path (Join-Path $frontendPath "node_modules"))) {
    Write-Host "node_modules não encontrado. Execute 'yarn install' primeiro." -ForegroundColor Yellow
    Write-Host "Tentando instalar..." -ForegroundColor Yellow
    Push-Location $frontendPath
    yarn install
    Pop-Location
}

# Iniciar frontend em background
$frontendJob = Start-Job -ScriptBlock {
    param($frontendPath)
    Set-Location $frontendPath
    yarn start
} -ArgumentList $frontendPath

Start-Sleep -Seconds 8

# Validar se frontend iniciou
$frontendReady = Wait-ServiceReady -Url "http://localhost:$FrontendPort" -TimeoutSeconds 40 -Name "Frontend"

if (-not $frontendReady) {
    Write-Host "! Frontend pode estar compilando ainda..." -ForegroundColor Yellow
    Write-Host "  Aguarde mais alguns segundos e verifique http://localhost:$FrontendPort" -ForegroundColor Yellow
}

# ETAPA 5: Validação Final
Write-Host "`n[5/5] Validação Final..." -ForegroundColor Cyan

# Testar endpoint crítico
try {
    Write-Host "Testando endpoint de moedas monitoradas..." -ForegroundColor Yellow
    $testUrl = "http://localhost:$BackendPort/api/market/monitored-coins"
    $response = Invoke-RestMethod -Uri $testUrl -Method Get -TimeoutSec 5
    
    if ($response.coins) {
        Write-Host "  ✓ Endpoint respondeu com $($response.count) moedas" -ForegroundColor Green
    } else {
        Write-Host "  ! Endpoint respondeu mas sem dados de moedas" -ForegroundColor Yellow
    }
} catch {
    Write-Host "  ✗ Erro ao testar endpoint: $_" -ForegroundColor Red
}

# Testar status do bot
try {
    Write-Host "Testando status do bot..." -ForegroundColor Yellow
    $statusUrl = "http://localhost:$BackendPort/api/bot/status"
    $status = Invoke-RestMethod -Uri $statusUrl -Method Get -TimeoutSec 5
    
    if ($status) {
        Write-Host "  ✓ Bot status: $(if($status.is_running){'Rodando'}else{'Parado'})" -ForegroundColor Green
        Write-Host "  ✓ Testnet: $($status.testnet_mode)" -ForegroundColor Green
    }
} catch {
    Write-Host "  ! Status do bot não disponível ainda" -ForegroundColor Yellow
}

# RESUMO FINAL
Write-Host "`n========================================" -ForegroundColor Cyan
Write-Host " Sistema Iniciado!" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan

Write-Host "`n📊 Serviços:" -ForegroundColor White
Write-Host "  • MongoDB:  " -NoNewline; Write-Host "Rodando" -ForegroundColor Green
Write-Host "  • Backend:  " -NoNewline; Write-Host "http://localhost:$BackendPort" -ForegroundColor Cyan
Write-Host "  • Frontend: " -NoNewline; Write-Host "http://localhost:$FrontendPort" -ForegroundColor Cyan

Write-Host "`n📁 Logs:" -ForegroundColor White
Write-Host "  • Backend:  backend\uvicorn*.err"
Write-Host "  • Frontend: Terminal de jobs"

Write-Host "`n🎯 Próximos Passos:" -ForegroundColor White
Write-Host "  1. Acesse: " -NoNewline; Write-Host "http://localhost:$FrontendPort" -ForegroundColor Green
Write-Host "  2. Configure API Keys se necessário"
Write-Host "  3. Inicie o bot pelo dashboard"

Write-Host "`n💡 Comandos Úteis:" -ForegroundColor White
Write-Host "  • Ver jobs:   Get-Job"
Write-Host "  • Parar tudo: ./scripts/stop_all.bat"
Write-Host "  • Logs:       Get-Content backend\uvicorn_latest.err -Tail 50 -Wait"

Write-Host "`n✓ Sistema pronto para uso!`n" -ForegroundColor Green

# Abrir navegador automaticamente após 3 segundos
Write-Host "Abrindo dashboard em 3 segundos..." -ForegroundColor Gray
Start-Sleep -Seconds 3
Start-Process "http://localhost:$FrontendPort"
