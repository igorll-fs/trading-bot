@echo off
REM ================================================================
REM Script Completo: Iniciar Sistema com Cloudflare Tunnel
REM ================================================================

echo.
echo ╔════════════════════════════════════════════════════════════╗
echo ║  INICIANDO TRADING BOT COM CLOUDFLARE TUNNEL               ║
echo ╚════════════════════════════════════════════════════════════╝
echo.

REM Verificar se está rodando como Administrador
net session >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERRO] Este script precisa ser executado como ADMINISTRADOR
    echo        Clique com botao direito -^> Executar como administrador
    pause
    exit /b 1
)

echo [1/6] Verificando MongoDB...
sc query MongoDB | find "RUNNING" >nul
if %errorlevel% neq 0 (
    echo   • Iniciando MongoDB...
    net start MongoDB
    if %errorlevel% neq 0 (
        echo   [ERRO] Falha ao iniciar MongoDB
        pause
        exit /b 1
    )
    timeout /t 3 /nobreak >nul
)
echo   ✓ MongoDB rodando

echo.
echo [2/6] Iniciando Backend (Python)...
cd /d "%~dp0"
start "Trading Bot Backend" cmd /k "cd /d %~dp0 && .venv\Scripts\activate && python backend\server.py"
echo   ✓ Backend iniciando em http://localhost:8000

echo.
echo [3/6] Aguardando backend estabilizar (10s)...
timeout /t 10 /nobreak >nul

echo.
echo [4/6] Iniciando Frontend (React)...
cd frontend
start "Trading Bot Frontend" cmd /k "npm start"
cd ..
echo   ✓ Frontend iniciando em http://localhost:3000

echo.
echo [5/6] Aguardando frontend estabilizar (15s)...
timeout /t 15 /nobreak >nul

echo.
echo [6/6] Verificando Cloudflare Tunnel...
sc query cloudflared >nul 2>&1
if %errorlevel% equ 0 (
    REM Servico existe
    sc query cloudflared | find "RUNNING" >nul
    if %errorlevel% neq 0 (
        echo   • Iniciando Cloudflare Tunnel...
        net start cloudflared
    )
    echo   ✓ Cloudflare Tunnel ATIVO
    echo.
    echo ╔════════════════════════════════════════════════════════════╗
    echo ║  SISTEMA ONLINE - ACESSO REMOTO DISPONIVEL                 ║
    echo ╚════════════════════════════════════════════════════════════╝
    echo.
    echo Acesso Local:
    echo   • Dashboard: http://localhost:3000
    echo   • API:       http://localhost:8000
    echo.
    echo Acesso Remoto (qualquer lugar):
    echo   • Dashboard: https://botrading.uk
    echo   • API:       https://api.botrading.uk
    echo.
) else (
    echo   ⚠ Servico Cloudflare NAO instalado
    echo.
    echo ╔════════════════════════════════════════════════════════════╗
    echo ║  SISTEMA ONLINE - ACESSO LOCAL APENAS                      ║
    echo ╚════════════════════════════════════════════════════════════╝
    echo.
    echo Acesso Local:
    echo   • Dashboard: http://localhost:3000
    echo   • API:       http://localhost:8000
    echo.
    echo Para habilitar acesso remoto:
    echo   1. Execute: scripts\install_cloudflare_service.bat
    echo   2. Reinicie este script
    echo.
)

echo ════════════════════════════════════════════════════════════
echo.
echo Janelas abertas:
echo   1. Trading Bot Backend  (Python)
echo   2. Trading Bot Frontend (React)
echo.
echo NAO FECHE ESTA JANELA - PRESSIONE QUALQUER TECLA PARA PARAR TUDO
pause >nul

echo.
echo Parando servicos...
taskkill /F /FI "WINDOWTITLE eq Trading Bot*" >nul 2>&1
echo Servicos parados.
echo.
