# =============================================================================
# Inicia Dashboard com Acesso Remoto Total
# =============================================================================

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  Trading Bot - Remote Dashboard" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

$cloudflared = "$env:USERPROFILE\cloudflared.exe"

if (-not (Test-Path $cloudflared)) {
    Write-Host "[ERRO] cloudflared.exe nao encontrado!" -ForegroundColor Red
    Write-Host "Execute: .\setup_remote_access.ps1" -ForegroundColor Yellow
    exit 1
}

# Verificar se backend está rodando
$backendRunning = netstat -ano | Select-String "8002" | Select-String "LISTENING"
if (-not $backendRunning) {
    Write-Host "[AVISO] Backend nao esta rodando na porta 8002" -ForegroundColor Yellow
    Write-Host "Inicie o backend primeiro!" -ForegroundColor Yellow
    exit 1
}

# Verificar se frontend está rodando
$frontendRunning = netstat -ano | Select-String "3000" | Select-String "LISTENING"
if (-not $frontendRunning) {
    Write-Host "[AVISO] Frontend nao esta rodando na porta 3000" -ForegroundColor Yellow
    Write-Host "Inicie o frontend primeiro!" -ForegroundColor Yellow
    exit 1
}

Write-Host "[OK] Backend rodando (porta 8002)" -ForegroundColor Green
Write-Host "[OK] Frontend rodando (porta 3000)" -ForegroundColor Green
Write-Host ""

# Iniciar tunel do backend em processo separado
Write-Host "Iniciando tunel do Backend..." -ForegroundColor Yellow
$backendJob = Start-Job -ScriptBlock {
    param($exe)
    & $exe tunnel --url http://localhost:8002 2>&1
} -ArgumentList $cloudflared

Start-Sleep -Seconds 5

# Capturar URL do backend
$backendOutput = Receive-Job -Job $backendJob
$backendUrl = ($backendOutput | Select-String "https://.*\.trycloudflare\.com" | Select-Object -First 1).Matches.Value

if ($backendUrl) {
    Write-Host "[OK] Backend Tunel: $backendUrl" -ForegroundColor Green
} else {
    Write-Host "[ERRO] Nao foi possivel criar tunel do backend" -ForegroundColor Red
    Stop-Job -Job $backendJob
    Remove-Job -Job $backendJob
    exit 1
}

# Salvar URL do backend em arquivo temporario para o frontend usar
$backendUrl | Out-File -FilePath "$env:TEMP\trading-bot-backend-url.txt" -Encoding UTF8

# Iniciar tunel do frontend
Write-Host ""
Write-Host "Iniciando tunel do Frontend..." -ForegroundColor Yellow
Write-Host ""

# Configurar variavel de ambiente para o frontend
$env:REACT_APP_BACKEND_URL = $backendUrl

Write-Host ""
Write-Host "========================================" -ForegroundColor Green
Write-Host "  DASHBOARD REMOTO ATIVO!" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green
Write-Host ""
Write-Host "Backend API:  $backendUrl" -ForegroundColor Cyan
Write-Host ""
Write-Host "Aguarde a URL do Dashboard..." -ForegroundColor Yellow
Write-Host ""

# Iniciar tunel do frontend (este ficará em foreground)
& $cloudflared tunnel --url http://localhost:3000

# Cleanup quando encerrar
Write-Host ""
Write-Host "Encerrando tuneis..." -ForegroundColor Yellow
Stop-Job -Job $backendJob -ErrorAction SilentlyContinue
Remove-Job -Job $backendJob -ErrorAction SilentlyContinue
Remove-Item "$env:TEMP\trading-bot-backend-url.txt" -ErrorAction SilentlyContinue
Write-Host "Tuneis encerrados." -ForegroundColor Green
