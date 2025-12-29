@echo off
REM Stop only the backend (bot control happens via dashboard)
title Trading Bot - Parando Backend
echo ========================================
echo  Parando Backend Apenas
echo ========================================
echo.

echo Fechando janela do Backend...
taskkill /FI "WINDOWTITLE eq Trading Bot - Backend*" /F >nul 2>&1

rem Fallback: matar processo na porta 8001
for /f "tokens=5" %%p in ('netstat -ano ^| findstr /R /C:":8001[ ].*LISTENING"') do (
    echo Finalizando processo na porta 8001 (PID %%p)...
    taskkill /PID %%p /F >nul 2>&1
)

echo.
echo Backend parado!
echo Frontend continua rodando em http://localhost:3000
echo.
timeout /t 2 >nul
