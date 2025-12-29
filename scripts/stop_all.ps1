# ============================================================
# SCRIPT: Parar Backend + Frontend + Bot
# ============================================================

$ErrorActionPreference = "SilentlyContinue"

Write-Host ""
Write-Host "============================================================" -ForegroundColor Red
Write-Host "   TRADING BOT - Parando Sistema" -ForegroundColor Red
Write-Host "============================================================" -ForegroundColor Red
Write-Host ""

# ------------------------------------------------------------
# 1. Parar o Bot via API (se estiver rodando)
# ------------------------------------------------------------
Write-Host "[1/3] Parando Bot..." -ForegroundColor Yellow
try {
    $response = Invoke-RestMethod -Uri "http://localhost:8002/api/bot/control" -Method Post -ContentType "application/json" -Body '{"action":"stop"}' -TimeoutSec 5
    Write-Host "  -> Bot parado com sucesso!" -ForegroundColor Green
} catch {
    Write-Host "  -> Bot ja estava parado ou backend nao respondeu." -ForegroundColor DarkYellow
}

Start-Sleep -Seconds 2

# ------------------------------------------------------------
# 2. Parar Backend (porta 8002)
# ------------------------------------------------------------
Write-Host ""
Write-Host "[2/3] Parando Backend..." -ForegroundColor Yellow
$proc8002 = netstat -ano 2>$null | Select-String ":8002.*LISTENING"
if ($proc8002) {
    $pid8002 = ($proc8002 -split '\s+')[-1]
    Stop-Process -Id $pid8002 -Force -ErrorAction SilentlyContinue
    Write-Host "  -> Backend (PID $pid8002) parado!" -ForegroundColor Green
} else {
    Write-Host "  -> Backend ja estava parado." -ForegroundColor DarkYellow
}

# ------------------------------------------------------------
# 3. Parar Frontend (porta 3000)
# ------------------------------------------------------------
Write-Host ""
Write-Host "[3/3] Parando Frontend..." -ForegroundColor Yellow
$proc3000 = netstat -ano 2>$null | Select-String ":3000.*LISTENING"
if ($proc3000) {
    $pid3000 = ($proc3000 -split '\s+')[-1]
    Stop-Process -Id $pid3000 -Force -ErrorAction SilentlyContinue
    Write-Host "  -> Frontend (PID $pid3000) parado!" -ForegroundColor Green
} else {
    Write-Host "  -> Frontend ja estava parado." -ForegroundColor DarkYellow
}

# Parar processos node restantes (podem ser do frontend)
Get-Process node -ErrorAction SilentlyContinue | Stop-Process -Force -ErrorAction SilentlyContinue

Write-Host ""
Write-Host "============================================================" -ForegroundColor Green
Write-Host "   SISTEMA PARADO COM SUCESSO!" -ForegroundColor Green
Write-Host "============================================================" -ForegroundColor Green
Write-Host ""
Write-Host "Pressione qualquer tecla para fechar..." -ForegroundColor DarkGray
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
