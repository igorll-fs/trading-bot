@echo off
echo ========================================
echo Reiniciando Servico Cloudflared
echo ========================================
echo.

echo Parando servico...
net stop cloudflared
timeout /t 3 /nobreak >nul

echo.
echo Iniciando servico...
net start cloudflared
timeout /t 3 /nobreak >nul

echo.
echo Status:
sc query cloudflared | findstr "ESTADO"

echo.
echo ========================================
echo Servico reiniciado com sucesso!
echo ========================================
echo.
echo Aguarde 10 segundos e teste: https://botrading.uk
pause
