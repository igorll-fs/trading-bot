# ============================================================
# SCRIPT: Iniciar Backend + Frontend (Bot fica parado)
# ============================================================
# O bot só será iniciado manualmente pelo Dashboard após configurar
# ============================================================

param(
    [switch]$NoBrowser  # Use -NoBrowser para não abrir o navegador automaticamente
)

$ErrorActionPreference = "Stop"
$ROOT = Split-Path -Parent $PSScriptRoot
$BACKEND_DIR = Join-Path $ROOT "backend"
$FRONTEND_DIR = Join-Path $ROOT "frontend"

Write-Host ""
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "   TRADING BOT - Iniciando Sistema" -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host ""

# ------------------------------------------------------------
# 1. Verificar MongoDB
# ------------------------------------------------------------
Write-Host "[1/4] Verificando MongoDB..." -ForegroundColor Yellow
$mongo = Get-Process mongod -ErrorAction SilentlyContinue
if (-not $mongo) {
    Write-Host "  -> MongoDB nao esta rodando. Tentando iniciar..." -ForegroundColor DarkYellow
    try {
        Start-Process "mongod" -WindowStyle Hidden
        Start-Sleep -Seconds 3
        Write-Host "  -> MongoDB iniciado!" -ForegroundColor Green
    } catch {
        Write-Host "  -> AVISO: Nao foi possivel iniciar MongoDB automaticamente." -ForegroundColor Red
        Write-Host "     Certifique-se de que o MongoDB esta instalado e rodando." -ForegroundColor Red
    }
} else {
    Write-Host "  -> MongoDB ja esta rodando." -ForegroundColor Green
}

# ------------------------------------------------------------
# 2. Parar processos anteriores (se existirem)
# ------------------------------------------------------------
Write-Host ""
Write-Host "[2/4] Limpando processos anteriores..." -ForegroundColor Yellow

# Parar backend na porta 8002
$proc8002 = netstat -ano 2>$null | Select-String ":8002.*LISTENING"
if ($proc8002) {
    $pid8002 = ($proc8002 -split '\s+')[-1]
    Stop-Process -Id $pid8002 -Force -ErrorAction SilentlyContinue
    Write-Host "  -> Backend anterior (PID $pid8002) parado." -ForegroundColor DarkYellow
    Start-Sleep -Seconds 2
}

# Parar frontend na porta 3000
$proc3000 = netstat -ano 2>$null | Select-String ":3000.*LISTENING"
if ($proc3000) {
    $pid3000 = ($proc3000 -split '\s+')[-1]
    Stop-Process -Id $pid3000 -Force -ErrorAction SilentlyContinue
    Write-Host "  -> Frontend anterior (PID $pid3000) parado." -ForegroundColor DarkYellow
    Start-Sleep -Seconds 2
}

Write-Host "  -> Pronto!" -ForegroundColor Green

# ------------------------------------------------------------
# 3. Iniciar Backend (porta 8002)
# ------------------------------------------------------------
Write-Host ""
Write-Host "[3/4] Iniciando Backend (porta 8002)..." -ForegroundColor Yellow

$backendJob = Start-Process powershell -ArgumentList @(
    "-NoProfile",
    "-Command",
    "cd '$BACKEND_DIR'; python -m uvicorn server:app --host 0.0.0.0 --port 8002"
) -PassThru -WindowStyle Minimized

Write-Host "  -> Backend iniciando (PID: $($backendJob.Id))..." -ForegroundColor DarkYellow

# Aguardar backend estar pronto
$maxWait = 30
$waited = 0
while ($waited -lt $maxWait) {
    Start-Sleep -Seconds 1
    $waited++
    try {
        $response = Invoke-RestMethod -Uri "http://localhost:8002/api/bot/status" -TimeoutSec 2 -ErrorAction Stop
        Write-Host "  -> Backend pronto!" -ForegroundColor Green
        break
    } catch {
        Write-Host "  -> Aguardando backend... ($waited s)" -ForegroundColor DarkGray -NoNewline
        Write-Host "`r" -NoNewline
    }
}

if ($waited -ge $maxWait) {
    Write-Host "  -> AVISO: Backend demorou mais que $maxWait s para iniciar." -ForegroundColor Red
}

# ------------------------------------------------------------
# 4. Iniciar Frontend (porta 3000)
# ------------------------------------------------------------
Write-Host ""
Write-Host "[4/4] Iniciando Frontend (porta 3000)..." -ForegroundColor Yellow

$frontendJob = Start-Process powershell -ArgumentList @(
    "-NoProfile",
    "-Command",
    "cd '$FRONTEND_DIR'; yarn start"
) -PassThru -WindowStyle Minimized

Write-Host "  -> Frontend iniciando (PID: $($frontendJob.Id))..." -ForegroundColor DarkYellow

# Aguardar frontend estar pronto
$maxWait = 60
$waited = 0
while ($waited -lt $maxWait) {
    Start-Sleep -Seconds 2
    $waited += 2
    try {
        $null = Invoke-WebRequest -Uri "http://localhost:3000" -TimeoutSec 2 -ErrorAction Stop
        Write-Host "  -> Frontend pronto!" -ForegroundColor Green
        break
    } catch {
        Write-Host "  -> Compilando frontend... ($waited s)" -ForegroundColor DarkGray -NoNewline
        Write-Host "`r" -NoNewline
    }
}

# ------------------------------------------------------------
# Finalização
# ------------------------------------------------------------
Write-Host ""
Write-Host "============================================================" -ForegroundColor Green
Write-Host "   SISTEMA INICIADO COM SUCESSO!" -ForegroundColor Green
Write-Host "============================================================" -ForegroundColor Green
Write-Host ""
Write-Host "  Backend:   http://localhost:8002" -ForegroundColor White
Write-Host "  Dashboard: http://localhost:3000" -ForegroundColor White
Write-Host ""
Write-Host "  IMPORTANTE:" -ForegroundColor Yellow
Write-Host "  1. Acesse o Dashboard" -ForegroundColor White
Write-Host "  2. Va em 'Configuracoes' e configure suas APIs" -ForegroundColor White
Write-Host "  3. Clique em 'Salvar Configuracoes'" -ForegroundColor White
Write-Host "  4. Volte ao Dashboard e clique em 'Iniciar Bot'" -ForegroundColor White
Write-Host ""
Write-Host "============================================================" -ForegroundColor Green

# Abrir navegador automaticamente (se não usar -NoBrowser)
if (-not $NoBrowser) {
    Start-Sleep -Seconds 2
    Start-Process "http://localhost:3000"
    Write-Host ""
    Write-Host "  -> Dashboard aberto no navegador!" -ForegroundColor Cyan
}

Write-Host ""
Write-Host "Pressione qualquer tecla para fechar esta janela..." -ForegroundColor DarkGray
Write-Host "(Backend e Frontend continuarao rodando em segundo plano)" -ForegroundColor DarkGray
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
