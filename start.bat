@echo off
REM ═══════════════════════════════════════════════════════════════
REM   TRADING BOT - INICIALIZADOR UNICO
REM   Inicia: MongoDB + Backend + Frontend + Cloudflare + Dashboard
REM ═══════════════════════════════════════════════════════════════

setlocal enabledelayedexpansion
cd /d "%~dp0"

REM Cores (via PowerShell inline)
set "PS_GREEN=Write-Host '%s' -ForegroundColor Green"
set "PS_YELLOW=Write-Host '%s' -ForegroundColor Yellow"
set "PS_RED=Write-Host '%s' -ForegroundColor Red"
set "PS_CYAN=Write-Host '%s' -ForegroundColor Cyan"

cls
echo.
echo ╔════════════════════════════════════════════════════════════╗
echo ║            TRADING BOT - INICIALIZACAO COMPLETA            ║
echo ╚════════════════════════════════════════════════════════════╝
echo.

REM ═══════════════════════════════════════════════════════════════
REM [1/6] VERIFICAR PRIVILEGIOS DE ADMINISTRADOR
REM ═══════════════════════════════════════════════════════════════
echo [1/6] Verificando privilegios...
REM ✅ Funciona COM ou SEM Admin
net session >nul 2>&1
if %errorlevel% neq 0 (
    powershell -Command "Write-Host '  ⚠️  Executando sem privilegios de Admin' -ForegroundColor Yellow"
    powershell -Command "Write-Host '  ℹ️  MongoDB e Cloudflare poderao nao iniciar' -ForegroundColor Gray"
    powershell -Command "Write-Host '  ✓ Backend e Frontend funcionarao normalmente!' -ForegroundColor Green"
    set "ADMIN=0"
) else (
    powershell -Command "Write-Host '  ✅ Privilegios de Administrador OK - Funcionalidade completa!' -ForegroundColor Green"
    set "ADMIN=1"
)

REM ═══════════════════════════════════════════════════════════════
REM [2/6] INICIAR MONGODB
REM ═══════════════════════════════════════════════════════════════
echo.
echo [2/6] Iniciando MongoDB...
if "%ADMIN%"=="1" (
    sc query MongoDB | find "RUNNING" >nul 2>&1
    if !errorlevel! neq 0 (
        net start MongoDB >nul 2>&1
        if !errorlevel! equ 0 (
            powershell -Command "Write-Host '  ✓ MongoDB iniciado com sucesso' -ForegroundColor Green"
            timeout /t 3 /nobreak >nul
        ) else (
            powershell -Command "Write-Host '  [ERRO] Falha ao iniciar MongoDB' -ForegroundColor Red"
            powershell -Command "Write-Host '  Verifique se o servico esta instalado' -ForegroundColor Yellow"
        )
    ) else (
        powershell -Command "Write-Host '  ✓ MongoDB ja esta rodando' -ForegroundColor Green"
    )
) else (
    powershell -Command "Write-Host '  ⚠ MongoDB requer privilegios Admin - pulando' -ForegroundColor Yellow"
)

REM ═══════════════════════════════════════════════════════════════
REM [3/6] INICIAR BACKEND (FastAPI na porta 8000)
REM ═══════════════════════════════════════════════════════════════
echo.
echo [3/6] Iniciando Backend (FastAPI)...

REM ✅ Detecta portas em uso e limpa automaticamente
netstat -an | find ":8000" | find "LISTENING" >nul 2>&1
if %errorlevel% equ 0 (
    powershell -Command "Write-Host '  ⚠️  Porta 8000 ja esta em uso - limpando...' -ForegroundColor Yellow"
    for /f "tokens=5" %%a in ('netstat -ano ^| find ":8000" ^| find "LISTENING"') do (
        taskkill /F /PID %%a >nul 2>&1
        powershell -Command "Write-Host '  ✓ Processo PID %%a encerrado' -ForegroundColor Gray"
    )
    timeout /t 2 /nobreak >nul
    powershell -Command "Write-Host '  ✓ Porta 8000 liberada!' -ForegroundColor Green"
)

REM ✅ Janelas minimizadas (não poluem o desktop)
start "Trading Bot Backend" /MIN cmd /k "cd /d %~dp0backend && ..\\.venv\\Scripts\\activate && python server.py"

powershell -Command "Write-Host '  ✓ Backend iniciando em janela minimizada...' -ForegroundColor Green"
powershell -Command "Write-Host '  ⏳ Aguardando estabilizacao (8 segundos)' -ForegroundColor Gray"
timeout /t 8 /nobreak >nul

REM ✅ Health checks antes de abrir o navegador
powershell -Command "$retries=0; $maxRetries=3; while($retries -lt $maxRetries) { try { $r = Invoke-WebRequest -Uri 'http://localhost:8000/health' -TimeoutSec 3 -UseBasicParsing -ErrorAction Stop; Write-Host '  ✅ Backend ONLINE - Health Check PASSOU!' -ForegroundColor Green; break } catch { $retries++; if($retries -lt $maxRetries) { Write-Host ('  ⏳ Tentativa {0}/{1} - aguardando...' -f $retries, $maxRetries) -ForegroundColor Gray; Start-Sleep -Seconds 2 } else { Write-Host '  ⚠️  Backend pode estar iniciando ainda' -ForegroundColor Yellow } } }"

REM ═══════════════════════════════════════════════════════════════
REM [4/6] INICIAR FRONTEND (React na porta 3000)
REM ═══════════════════════════════════════════════════════════════
echo.
echo [4/6] Iniciando Frontend (React)...

REM ✅ Detecta portas em uso e limpa automaticamente
netstat -an | find ":3000" | find "LISTENING" >nul 2>&1
if %errorlevel% equ 0 (
    powershell -Command "Write-Host '  ⚠️  Porta 3000 ja esta em uso - limpando...' -ForegroundColor Yellow"
    for /f "tokens=5" %%a in ('netstat -ano ^| find ":3000" ^| find "LISTENING"') do (
        taskkill /F /PID %%a >nul 2>&1
        powershell -Command "Write-Host '  ✓ Processo PID %%a encerrado' -ForegroundColor Gray"
    )
    timeout /t 2 /nobreak >nul
    powershell -Command "Write-Host '  ✓ Porta 3000 liberada!' -ForegroundColor Green"
)

REM ✅ Janelas minimizadas (não poluem o desktop)
cd frontend
start "Trading Bot Frontend" /MIN cmd /k "npm start"
cd ..

powershell -Command "Write-Host '  ✓ Frontend iniciando em janela minimizada...' -ForegroundColor Green"
powershell -Command "Write-Host '  ⏳ Aguardando estabilizacao (12 segundos)' -ForegroundColor Gray"
timeout /t 12 /nobreak >nul

REM ═══════════════════════════════════════════════════════════════
REM [5/6] CLOUDFLARE TUNNEL (OPCIONAL)
REM ═══════════════════════════════════════════════════════════════
echo.
echo [5/6] Verificando Cloudflare Tunnel...

REM Verificar se serviço existe
sc query cloudflared >nul 2>&1
if %errorlevel% equ 0 (
    REM Servico instalado
    sc query cloudflared | find "RUNNING" >nul 2>&1
    if !errorlevel! equ 0 (
        powershell -Command "Write-Host '  ✓ Cloudflare Tunnel ja esta rodando' -ForegroundColor Green"
    ) else (
        if "%ADMIN%"=="1" (
            net start cloudflared >nul 2>&1
            if !errorlevel! equ 0 (
                powershell -Command "Write-Host '  ✓ Cloudflare Tunnel iniciado' -ForegroundColor Green"
            ) else (
                powershell -Command "Write-Host '  [ERRO] Falha ao iniciar Cloudflare Tunnel' -ForegroundColor Red"
            )
        ) else (
            powershell -Command "Write-Host '  ⚠ Cloudflare Tunnel requer Admin - pulando' -ForegroundColor Yellow"
        )
    )
) else (
    REM Servico nao instalado - tentar manual
    if exist "C:\Users\%USERNAME%\cloudflared.exe" (
        powershell -Command "Write-Host '  ℹ Cloudflare nao instalado como servico' -ForegroundColor Yellow"
        powershell -Command "Write-Host '  Execute: scripts\install_cloudflare_service.bat (como Admin)' -ForegroundColor Gray"
    ) else (
        powershell -Command "Write-Host '  ℹ Cloudflare Tunnel nao configurado' -ForegroundColor Gray"
    )
)

REM ═══════════════════════════════════════════════════════════════
REM [6/6] ABRIR DASHBOARD NO NAVEGADOR
REM ═══════════════════════════════════════════════════════════════
echo.
echo [6/6] Abrindo Dashboard...

REM ✅ Health checks antes de abrir o navegador
powershell -Command "$retries=0; $maxRetries=5; $ready=$false; while($retries -lt $maxRetries) { try { $r = Invoke-WebRequest -Uri 'http://localhost:3000' -TimeoutSec 3 -UseBasicParsing -ErrorAction Stop; Write-Host '  ✅ Frontend ONLINE - Health Check PASSOU!' -ForegroundColor Green; $ready=$true; break } catch { $retries++; if($retries -lt $maxRetries) { Write-Host ('  ⏳ Tentativa {0}/{1} - aguardando frontend...'-f $retries, $maxRetries) -ForegroundColor Gray; Start-Sleep -Seconds 3 } else { Write-Host '  ⚠️  Frontend ainda nao respondeu, mas abrindo navegador...' -ForegroundColor Yellow } } }"

REM Abrir navegador padrão
timeout /t 1 /nobreak >nul
start http://localhost:3000

powershell -Command "Write-Host '  ✅ Dashboard aberto no navegador!' -ForegroundColor Green"

REM ═══════════════════════════════════════════════════════════════
REM STATUS FINAL
REM ═══════════════════════════════════════════════════════════════
echo.
echo ════════════════════════════════════════════════════════════
powershell -Command "Write-Host '✅ SISTEMA INICIADO COM SUCESSO!' -ForegroundColor Green -BackgroundColor DarkGreen"
echo ════════════════════════════════════════════════════════════
echo.
REM ✅ Mensagens coloridas e claras
powershell -Command "Write-Host '📊 ACESSO LOCAL:' -ForegroundColor Cyan"
echo   • Dashboard:  http://localhost:3000
echo   • API:        http://localhost:8000
echo   • API Docs:   http://localhost:8000/docs
echo.

REM ✅ Mostra URLs remotas se Cloudflare estiver ativo
sc query cloudflared | find "RUNNING" >nul 2>&1
if %errorlevel% equ 0 (
    powershell -Command "Write-Host '🌐 ACESSO REMOTO (Cloudflare Tunnel Ativo):' -ForegroundColor Green"
    echo   • Dashboard:  https://botrading.uk
    echo   • API:        https://api.botrading.uk
    powershell -Command "Write-Host '   ✓ Acessivel de qualquer lugar!' -ForegroundColor Gray"
    echo.
) else (
    powershell -Command "Write-Host '📡 ACESSO REMOTO: Cloudflare Tunnel NAO ativo' -ForegroundColor DarkGray"
    powershell -Command "Write-Host '   Para ativar: scripts\install_cloudflare_service.bat' -ForegroundColor DarkGray"
    echo.
)

powershell -Command "Write-Host 'ℹ️  CONTROLES:' -ForegroundColor Yellow"
echo   • Parar tudo:  Execute scripts\stop_all.ps1
echo   • Monitorar:   Execute scripts\monitor_bot.ps1
echo.
echo ════════════════════════════════════════════════════════════
echo.
powershell -Command "Write-Host 'Pressione CTRL+C para sair (processos continuarao rodando)' -ForegroundColor Gray"
echo.

REM Manter janela aberta
pause >nul
