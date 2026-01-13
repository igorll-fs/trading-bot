@echo off
echo ================================================================
echo    INSTALANDO CLOUDFLARE TUNNEL COMO SERVICO WINDOWS
echo ================================================================
echo.

echo [1/3] Instalando servico...
%USERPROFILE%\cloudflared.exe service install
if %errorlevel% neq 0 (
    echo ERRO: Falha ao instalar. Execute como Administrador!
    pause
    exit /b 1
)

echo.
echo [2/3] Iniciando servico...
net start cloudflared

echo.
echo [3/3] Verificando status...
sc query cloudflared

echo.
echo ================================================================
echo    INSTALACAO CONCLUIDA!
echo ================================================================
echo.
echo Seu dashboard estara disponivel em:
echo    https://botrading.uk
echo.
echo A API estara disponivel em:
echo    https://api.botrading.uk
echo.
echo O servico inicia automaticamente com o Windows!
echo ================================================================
pause
