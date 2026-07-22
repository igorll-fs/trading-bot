@echo off
echo ========================================
echo   LIBERAR PORTAS NO FIREWALL
echo ========================================
echo.
echo Este script vai adicionar regras de firewall para:
echo - Frontend (porta 3000)
echo - Backend (porta 8002)
echo.
echo IMPORTANTE: Execute como Administrador!
echo (Clique com botao direito -^> Executar como administrador)
echo.
pause

echo.
echo Liberando porta 3000 (Frontend)...
netsh advfirewall firewall add rule name="Trading Bot - Frontend" dir=in action=allow protocol=TCP localport=3000
if %ERRORLEVEL% EQU 0 (
    echo [OK] Porta 3000 liberada!
) else (
    echo [ERRO] Nao foi possivel liberar porta 3000. Execute como Administrador!
)

echo.
echo Liberando porta 8002 (Backend)...
netsh advfirewall firewall add rule name="Trading Bot - Backend" dir=in action=allow protocol=TCP localport=8002
if %ERRORLEVEL% EQU 0 (
    echo [OK] Porta 8002 liberada!
) else (
    echo [ERRO] Nao foi possivel liberar porta 8002. Execute como Administrador!
)

echo.
echo ========================================
echo   CONCLUIDO!
echo ========================================
echo.
echo Agora voce pode acessar o dashboard de outros dispositivos:
echo - No celular/tablet (mesma WiFi): http://192.168.2.105:3000
echo - Cloudflare Tunnel: Siga instrucoes em frontend/ACESSO_REMOTO.md
echo.
pause
