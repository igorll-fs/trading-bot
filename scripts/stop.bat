@echo off
cd /d "%~dp0"
title Trading Bot - Parando...
echo ========================================
echo  Trading Bot - Parando Sistema
echo ========================================
echo.

echo Parando processos...
taskkill /FI "WINDOWTITLE eq Trading Bot - Backend*" /F >nul 2>&1
taskkill /FI "WINDOWTITLE eq Trading Bot - Frontend*" /F >nul 2>&1

rem Fallback: matar processos presos nas portas 8001 (backend) e 3000 (frontend)
for /f "tokens=5" %%p in ('netstat -ano ^| findstr /R /C:":8001[ ].*LISTENING"') do taskkill /PID %%p /F >nul 2>&1
for /f "tokens=5" %%p in ('netstat -ano ^| findstr /R /C:":3000[ ].*LISTENING"') do taskkill /PID %%p /F >nul 2>&1

echo.
echo Sistema parado!
echo.
pause