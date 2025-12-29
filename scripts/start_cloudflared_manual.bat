@echo off
echo ========================================
echo Parando Servico Cloudflared e Reiniciando Manualmente
echo ========================================
echo.

echo [1/3] Parando servico Windows...
net stop cloudflared
timeout /t 3 /nobreak >nul

echo.
echo [2/3] Aguarde enquanto o tunnel inicia...
echo.

cd C:\Users\igor
start "Cloudflared Tunnel" cmd /k "cloudflared.exe tunnel run trading-bot"

timeout /t 5 /nobreak >nul

echo.
echo [3/3] Tunnel iniciado em uma nova janela!
echo.
echo ========================================
echo Verifique a janela "Cloudflared Tunnel"
echo Deve mostrar: "Registered tunnel connection"
echo ========================================
echo.
echo Teste em: https://botrading.uk
echo.
pause
