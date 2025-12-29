@echo off
cd /d "%~dp0\.."
title Trading Bot - Sistema Robusto
echo ========================================
echo  Trading Bot - Inicializacao Robusta
echo ========================================
echo.

REM Verificar MongoDB
echo [1/3] Verificando MongoDB...
sc query MongoDB | find "RUNNING" >nul
if errorlevel 1 (
    echo MongoDB parado. Tentando iniciar...
    net start MongoDB >nul 2>&1
    if errorlevel 1 (
        echo ERRO: MongoDB nao iniciou. Execute como Administrador
        echo ou inicie o MongoDB manualmente.
        pause
        exit /b 1
    )
    timeout /t 2 >nul
)
echo MongoDB: OK

echo.
echo [2/3] Iniciando Backend (porta 8000)...
REM Matar processos na porta 8000
for /f "tokens=5" %%p in ('netstat -ano ^| findstr /R /C:":8000[ ].*LISTENING" 2^>nul') do (
    echo Limpando porta 8000 (PID %%p)...
    taskkill /PID %%p /F >nul 2>&1
)
timeout /t 1 >nul

start "Trading Bot - Backend" /MIN cmd /c "cd backend && python -m uvicorn server:app --host 0.0.0.0 --port 8000 --reload"
timeout /t 3 >nul
echo Backend: Iniciado

echo.
echo [3/3] Iniciando Frontend com Auto-Recovery...
REM Usar script PowerShell que reinicia automaticamente
start "Trading Bot - Frontend (Auto-Recovery)" powershell -NoExit -ExecutionPolicy Bypass -File "%~dp0keep_frontend_running.ps1"

timeout /t 5 >nul

echo.
echo ========================================
echo  Sistema Iniciado com Auto-Recovery!
echo ========================================
echo.
echo Backend:  http://localhost:8000
echo Frontend: http://localhost:3000
echo.
echo RECURSOS DE SEGURANCA:
echo - Frontend reinicia automaticamente se cair
echo - Backend em modo reload (atualiza ao salvar)
echo - MongoDB monitorado
echo.
echo Para parar tudo: execute stop_all.bat
echo.

REM Abrir navegador após 3 segundos
timeout /t 3 >nul
start http://localhost:3000

echo Pressione qualquer tecla para fechar esta janela...
echo (Os servicos continuarao rodando em background)
pause >nul
