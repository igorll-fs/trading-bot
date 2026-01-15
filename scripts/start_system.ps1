# start_system.ps1
# Script para iniciar o Trading Bot System completo

Write-Host "`n" -NoNewline
Write-Host "═══════════════════════════════════════════════════════" -ForegroundColor Cyan
Write-Host "    🤖 TRADING BOT SYSTEM - Inicialização" -ForegroundColor Cyan
Write-Host "═══════════════════════════════════════════════════════" -ForegroundColor Cyan
Write-Host "`n"

$ROOT_PATH = "$PSScriptRoot\.."

# 1. Verificar MongoDB
Write-Host "1️⃣  Verificando MongoDB..." -ForegroundColor Yellow
try {
    $mongoService = Get-Service -Name "MongoDB" -ErrorAction Stop
    if($mongoService.Status -eq "Running") {
        Write-Host "   ✅ MongoDB ativo" -ForegroundColor Green
    } else {
        Write-Host "   ⚠️  MongoDB parado. Tentando iniciar..." -ForegroundColor Yellow
        Start-Service -Name "MongoDB"
        Start-Sleep -Seconds 3
        Write-Host "   ✅ MongoDB iniciado" -ForegroundColor Green
    }
} catch {
    Write-Host "   ❌ MongoDB não encontrado!" -ForegroundColor Red
    Write-Host "   Instale o MongoDB Community Server" -ForegroundColor Yellow
    exit 1
}

# 2. Iniciar Backend
Write-Host "`n2️⃣  Iniciando Backend..." -ForegroundColor Yellow
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd $ROOT_PATH\backend; Write-Host '🔧 Iniciando Backend...' -ForegroundColor Cyan; python server.py"
Write-Host "   ⏳ Aguardando backend inicializar (5 segundos)..." -ForegroundColor Gray
Start-Sleep -Seconds 5

$backendActive = $false
for($i = 1; $i -le 3; $i++) {
    $backend = Test-NetConnection -ComputerName localhost -Port 8001 -InformationLevel Quiet -WarningAction SilentlyContinue
    if($backend) {
        Write-Host "   ✅ Backend ativo (porta 8001)" -ForegroundColor Green
        $backendActive = $true
        break
    }
    Write-Host "   ⏳ Tentativa $i/3..." -ForegroundColor Gray
    Start-Sleep -Seconds 3
}

if(-not $backendActive) {
    Write-Host "   ⚠️  Backend ainda não respondeu, mas pode estar inicializando..." -ForegroundColor Yellow
}

# 3. Iniciar Frontend
Write-Host "`n3️⃣  Iniciando Frontend..." -ForegroundColor Yellow
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd $ROOT_PATH\frontend; Write-Host '⚛️  Iniciando Frontend (React)...' -ForegroundColor Cyan; npm start"
Write-Host "   ⏳ Aguardando compilação do React (15 segundos)..." -ForegroundColor Gray
Start-Sleep -Seconds 15

$frontendActive = $false
for($i = 1; $i -le 3; $i++) {
    $frontend = Test-NetConnection -ComputerName localhost -Port 3000 -InformationLevel Quiet -WarningAction SilentlyContinue
    if($frontend) {
        Write-Host "   ✅ Frontend ativo (porta 3000)" -ForegroundColor Green
        $frontendActive = $true
        break
    }
    Write-Host "   ⏳ Tentativa $i/3 (compilação pode levar tempo)..." -ForegroundColor Gray
    Start-Sleep -Seconds 5
}

if(-not $frontendActive) {
    Write-Host "   ⚠️  Frontend ainda compilando. Aguarde mais um pouco..." -ForegroundColor Yellow
}

# 4. Resumo do Sistema
Write-Host "`n" -NoNewline
Write-Host "═══════════════════════════════════════════════════════" -ForegroundColor Cyan
Write-Host "    📊 STATUS DO SISTEMA" -ForegroundColor Cyan
Write-Host "═══════════════════════════════════════════════════════" -ForegroundColor Cyan
Write-Host "`n"

# MongoDB
$mongo = Get-Service -Name "MongoDB" -ErrorAction SilentlyContinue
$mongoStatus = if($mongo -and $mongo.Status -eq "Running") { "✅ ATIVO" } else { "❌ INATIVO" }
Write-Host "   MongoDB:  $mongoStatus" -ForegroundColor $(if($mongo -and $mongo.Status -eq "Running"){'Green'}else{'Red'})

# Backend
$backend = Test-NetConnection -ComputerName localhost -Port 8001 -InformationLevel Quiet -WarningAction SilentlyContinue
$backendStatus = if($backend) { "✅ ATIVO" } else { "❌ INATIVO" }
Write-Host "   Backend:  $backendStatus  (http://localhost:8001)" -ForegroundColor $(if($backend){'Green'}else{'Red'})

# Frontend
$frontend = Test-NetConnection -ComputerName localhost -Port 3000 -InformationLevel Quiet -WarningAction SilentlyContinue
$frontendStatus = if($frontend) { "✅ ATIVO" } else { "⏳ COMPILANDO" }
Write-Host "   Frontend: $frontendStatus  (http://localhost:3000)" -ForegroundColor $(if($frontend){'Green'}else{'Yellow'})

Write-Host "`n"

# 5. Abrir Dashboard
if($frontend) {
    Write-Host "4️⃣  Abrindo Dashboard no navegador..." -ForegroundColor Yellow
    Start-Sleep -Seconds 2
    Start-Process "http://localhost:3000"
    Write-Host "   ✅ Dashboard aberto!" -ForegroundColor Green
} else {
    Write-Host "4️⃣  Frontend ainda não está pronto" -ForegroundColor Yellow
    Write-Host "   ⏳ Acesse http://localhost:3000 manualmente em 1 minuto" -ForegroundColor Gray
}

# 6. Mensagem Final
Write-Host "`n" -NoNewline
Write-Host "═══════════════════════════════════════════════════════" -ForegroundColor Green
Write-Host "    ✅ SISTEMA INICIADO COM SUCESSO!" -ForegroundColor Green
Write-Host "═══════════════════════════════════════════════════════" -ForegroundColor Green
Write-Host "`n"
Write-Host "📝 Próximos passos:" -ForegroundColor Cyan
Write-Host "   1. Acesse: http://localhost:3000" -ForegroundColor White
Write-Host "   2. Vá em Settings para configurar credenciais" -ForegroundColor White
Write-Host "   3. Clique em 'Iniciar Bot' no Dashboard" -ForegroundColor White
Write-Host "`n"
Write-Host "💡 Dica: Mantenha as janelas do PowerShell abertas!" -ForegroundColor Yellow
Write-Host "   Backend e Frontend estão rodando nelas." -ForegroundColor Yellow
Write-Host "`n"

# Manter script aberto
Read-Host "Pressione Enter para fechar este script (os serviços continuarão rodando)"
