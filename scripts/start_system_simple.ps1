# Script simplificado para iniciar Backend + Frontend
param(
    [int]$BackendPort = 8000,
    [int]$FrontendPort = 3000
)

$ErrorActionPreference = "Stop"
$ProjectRoot = "$PSScriptRoot\.."

Write-Host "`n=== INICIANDO SISTEMA DE TRADING ===" -ForegroundColor Cyan

# 1. Encerrar processos antigos
Write-Host "`n[1/4] Encerrando processos antigos..." -ForegroundColor Yellow
Get-Process python -ErrorAction SilentlyContinue | Stop-Process -Force -ErrorAction SilentlyContinue
Get-Process node -ErrorAction SilentlyContinue | Where-Object { $_.MainWindowTitle -like "*react*" } | Stop-Process -Force -ErrorAction SilentlyContinue
Start-Sleep -Seconds 3

# 2. Iniciar MongoDB (se não estiver rodando)
Write-Host "[2/4] Verificando MongoDB..." -ForegroundColor Yellow
$mongoService = Get-Service -Name "MongoDB" -ErrorAction SilentlyContinue
if ($mongoService -and $mongoService.Status -ne 'Running') {
    Start-Service -Name "MongoDB"
    Write-Host "  MongoDB iniciado" -ForegroundColor Green
} else {
    Write-Host "  MongoDB OK" -ForegroundColor Green
}

# 3. Iniciar Backend
Write-Host "[3/4] Iniciando Backend..." -ForegroundColor Yellow
$backendJob = Start-Job -Name "TradingBackend" -ScriptBlock {
    param($root, $port)
    Set-Location "$root\backend"
    & "$root\.venv\Scripts\python.exe" -m uvicorn server:app --host 0.0.0.0 --port $port --log-level info
} -ArgumentList $ProjectRoot, $BackendPort

Start-Sleep -Seconds 8

# Verificar se backend iniciou
$backendOK = Test-NetConnection -ComputerName localhost -Port $BackendPort -InformationLevel Quiet
if ($backendOK) {
    Write-Host "  Backend ONLINE na porta $BackendPort" -ForegroundColor Green
} else {
    Write-Host "  ERRO: Backend falhou ao iniciar!" -ForegroundColor Red
    Receive-Job -Job $backendJob
    exit 1
}

# 4. Iniciar Frontend  
Write-Host "[4/4] Iniciando Frontend..." -ForegroundColor Yellow
$frontendJob = Start-Job -Name "TradingFrontend" -ScriptBlock {
    param($root, $port)
    Set-Location "$root\frontend"
    $env:PORT = $port
    yarn start
} -ArgumentList $ProjectRoot, $FrontendPort

Start-Sleep -Seconds 10

# Verificar se frontend iniciou
$frontendOK = Test-NetConnection -ComputerName localhost -Port $FrontendPort -InformationLevel Quiet
if ($frontendOK) {
    Write-Host "  Frontend ONLINE na porta $FrontendPort" -ForegroundColor Green
} else {
    Write-Host "  AVISO: Frontend pode estar iniciando ainda..." -ForegroundColor Yellow
}

# Status final
Write-Host "`n=== STATUS FINAL ===" -ForegroundColor Cyan
Write-Host "Backend Job:  $(Get-Job -Name TradingBackend | Select-Object -ExpandProperty State)" -ForegroundColor $(if((Get-Job -Name TradingBackend).State -eq 'Running'){'Green'}else{'Red'})
Write-Host "Frontend Job: $(Get-Job -Name TradingFrontend | Select-Object -ExpandProperty State)" -ForegroundColor $(if((Get-Job -Name TradingFrontend).State -eq 'Running'){'Green'}else{'Red'})
Write-Host "Cloudflared:  $($(Get-Service cloudflared -ErrorAction SilentlyContinue).Status)" -ForegroundColor Green

Write-Host "`n=== ACESSO ===" -ForegroundColor Cyan
Write-Host "Local:  http://localhost:$FrontendPort"
Write-Host "Remoto: https://botrading.uk"

Write-Host "`nPara monitorar logs:" -ForegroundColor Yellow
Write-Host "  Receive-Job -Name TradingBackend -Keep"
Write-Host "  Receive-Job -Name TradingFrontend -Keep"
Write-Host "`nPara parar tudo:" -ForegroundColor Yellow
Write-Host "  Get-Job | Stop-Job; Get-Job | Remove-Job"
