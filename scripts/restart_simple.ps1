# Script Robusto de Restart - Trading Bot
# Versao simplificada e funcional

Write-Host "`n========================================" -ForegroundColor Cyan
Write-Host " Trading Bot - Restart Sistema" -ForegroundColor Cyan
Write-Host "========================================`n" -ForegroundColor Cyan

$ProjectRoot = "$PSScriptRoot\.."
$BackendPort = 8000
$FrontendPort = 3000

# Funcao: Parar processo em porta
function Kill-PortProcess {
    param([int]$Port)
    
    Write-Host "Liberando porta $Port..." -ForegroundColor Yellow
    $procs = Get-NetTCPConnection -LocalPort $Port -ErrorAction SilentlyContinue | Select-Object -ExpandProperty OwningProcess -Unique
    
    foreach ($pid in $procs) {
        Stop-Process -Id $pid -Force -ErrorAction SilentlyContinue
    }
    Start-Sleep -Seconds 1
    Write-Host "  OK - Porta $Port livre" -ForegroundColor Green
}

# PASSO 1: Parar tudo
Write-Host "[1/4] Parando servicos..." -ForegroundColor Cyan
Get-Process python,node -ErrorAction SilentlyContinue | Stop-Process -Force -ErrorAction SilentlyContinue
Start-Sleep -Seconds 2

Kill-PortProcess -Port $BackendPort
Kill-PortProcess -Port $FrontendPort

Write-Host "  OK - Servicos parados`n" -ForegroundColor Green

# PASSO 2: Verificar MongoDB
Write-Host "[2/4] Verificando MongoDB..." -ForegroundColor Cyan
$mongo = Get-Service MongoDB -ErrorAction SilentlyContinue

if ($null -eq $mongo) {
    Write-Host "  ERRO: MongoDB nao instalado!" -ForegroundColor Red
    exit 1
}

if ($mongo.Status -ne "Running") {
    Write-Host "  Iniciando MongoDB..." -ForegroundColor Yellow
    Start-Service MongoDB -ErrorAction Stop
    Start-Sleep -Seconds 3
}

Write-Host "  OK - MongoDB rodando`n" -ForegroundColor Green

# PASSO 3: Iniciar Backend
Write-Host "[3/4] Iniciando Backend (porta $BackendPort)..." -ForegroundColor Cyan

$backendCmd = @"
cd '$ProjectRoot\backend'
& '$ProjectRoot\.venv\Scripts\Activate.ps1'
python -m uvicorn server:app --host 0.0.0.0 --port $BackendPort --reload
"@

Start-Job -Name "TradingBot-Backend" -ScriptBlock {
    param($cmd)
    Invoke-Expression $cmd
} -ArgumentList $backendCmd | Out-Null

Write-Host "  Aguardando backend iniciar..." -ForegroundColor Yellow
Start-Sleep -Seconds 8

# Testar backend
try {
    $null = Invoke-RestMethod "http://localhost:$BackendPort/api/health" -TimeoutSec 5 -ErrorAction Stop
    Write-Host "  OK - Backend respondendo`n" -ForegroundColor Green
} catch {
    Write-Host "  AVISO: Backend pode estar inicializando..." -ForegroundColor Yellow
    Write-Host "  Verifique logs em backend\uvicorn*.err`n" -ForegroundColor Gray
}

# PASSO 4: Iniciar Frontend
Write-Host "[4/4] Iniciando Frontend (porta $FrontendPort)..." -ForegroundColor Cyan

$frontendCmd = @"
cd '$ProjectRoot\frontend'
yarn start
"@

Start-Job -Name "TradingBot-Frontend" -ScriptBlock {
    param($cmd)
    Invoke-Expression $cmd
} -ArgumentList $frontendCmd | Out-Null

Write-Host "  Aguardando frontend compilar..." -ForegroundColor Yellow
Start-Sleep -Seconds 12

# Testar frontend
try {
    $null = Invoke-WebRequest "http://localhost:$FrontendPort" -TimeoutSec 5 -UseBasicParsing -ErrorAction Stop
    Write-Host "  OK - Frontend respondendo`n" -ForegroundColor Green
} catch {
    Write-Host "  AVISO: Frontend ainda compilando..." -ForegroundColor Yellow
    Write-Host "  Aguarde mais 10-20 segundos`n" -ForegroundColor Gray
}

# RESUMO
Write-Host "========================================" -ForegroundColor Cyan
Write-Host " Sistema Iniciado!" -ForegroundColor Cyan
Write-Host "========================================`n" -ForegroundColor Cyan

Write-Host "Servicos:" -ForegroundColor White
Write-Host "  MongoDB:  Rodando" -ForegroundColor Green
Write-Host "  Backend:  http://localhost:$BackendPort" -ForegroundColor Cyan
Write-Host "  Frontend: http://localhost:$FrontendPort" -ForegroundColor Cyan

Write-Host "`nJobs ativos:" -ForegroundColor White
Get-Job | Format-Table -AutoSize

Write-Host "`nComandos uteis:" -ForegroundColor White
Write-Host "  Ver jobs:      Get-Job"
Write-Host "  Parar backend: Stop-Job -Name TradingBot-Backend"
Write-Host "  Parar tudo:    Get-Job | Stop-Job"
Write-Host "  Logs backend:  Get-Content backend\uvicorn_latest.err -Tail 50 -Wait"

Write-Host "`nAbrindo dashboard em 3 segundos..." -ForegroundColor Gray
Start-Sleep -Seconds 3
Start-Process "http://localhost:$FrontendPort"

Write-Host "`nSistema pronto! Pressione Ctrl+C para sair (servicos continuam rodando)" -ForegroundColor Green
