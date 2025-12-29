@echo off
cd /d "%~dp0"
title Trading Bot - Iniciando...
echo ========================================
echo  Trading Bot - Iniciando Sistema
echo ========================================
echo.

REM Check if MongoDB is running
echo [1/4] Verificando MongoDB...
sc query MongoDB | find "RUNNING" >nul
if errorlevel 1 (
    echo MongoDB nao esta rodando. Tentando iniciar...
    net start MongoDB >nul 2>&1
    if errorlevel 1 (
        echo ERRO: Nao foi possivel iniciar o MongoDB!
        echo Por favor, inicie o MongoDB manualmente.
        goto END
    )
)
echo MongoDB rodando!

echo.
echo [2/4] Preparando Backend (FastAPI)...
REM Check if backend CMD window already exists
tasklist /FI "WINDOWTITLE eq Trading Bot - Backend*" 2>NUL | find /I /N "cmd.exe">NUL
if "%ERRORLEVEL%"=="0" (
    echo Backend ja esta rodando! Pulando...
) else (
    REM Kill any process on port 8000
    set BACK_PID=
    for /f "tokens=5" %%p in ('netstat -ano ^| findstr /R /C:":8000[ ].*LISTENING"') do set BACK_PID=%%p
    if defined BACK_PID (
        echo Limpando processo antigo na porta 8000 (PID %BACK_PID%)...
        taskkill /PID %BACK_PID% /F >nul 2>&1
        timeout /t 2 >nul
    )
    echo Iniciando Backend (FastAPI)...
    start "Trading Bot - Backend" cmd /k "cd backend && python -m uvicorn server:app --host 0.0.0.0 --port 8000 --reload"
    timeout /t 3 >nul
)

echo.
echo [3/4] Preparando Frontend (React)...
REM Check if frontend CMD window already exists
tasklist /FI "WINDOWTITLE eq Trading Bot - Frontend*" 2>NUL | find /I /N "cmd.exe">NUL
if "%ERRORLEVEL%"=="0" (
    echo Frontend ja esta rodando! Pulando...
) else (
    REM Kill any process on port 3000
    set FE_PID=
    for /f "tokens=5" %%p in ('netstat -ano ^| findstr /R /C:":3000[ ].*LISTENING"') do set FE_PID=%%p
    if defined FE_PID (
        echo Limpando processo antigo na porta 3000 (PID %FE_PID%)...
        taskkill /PID %FE_PID% /F >nul 2>&1
        timeout /t 2 >nul
    )
    echo Iniciando Frontend (React)...
    set YARN_CMD=
    where yarn >nul 2>&1
    if %ERRORLEVEL%==0 set YARN_CMD=1
    if defined YARN_CMD (
        start "Trading Bot - Frontend" cmd /k "cd frontend && yarn start"
    ) else (
        start "Trading Bot - Frontend" cmd /k "cd frontend && npm start"
    )
    set "FE_STARTED=1"
    timeout /t 5 >nul
)

echo.
echo [4/4] Abrindo navegador...
timeout /t 3 >nul
start http://localhost:3000

echo.
echo ========================================
echo  Sistema Iniciado!
echo ========================================
echo.
echo Backend: http://localhost:8000
echo Frontend: http://localhost:3000
echo.
echo IMPORTANTE:
echo - Pare o BOT pelo Dashboard antes de fechar
echo - Backend fecha automaticamente ao parar o bot
echo - Frontend mantem rodando (feche manualmente se quiser)
echo.
goto END

:END
echo.
pause