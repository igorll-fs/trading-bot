@echo off
:: ================================================================
:: SCRIPT DE INICIALIZACAO DOS SERVICOS - BOTRADING
:: Executar como Administrador
:: ================================================================

echo ================================================================
echo    VERIFICANDO E INICIANDO SERVICOS BOTRADING
echo ================================================================
echo.

:: Verifica se esta rodando como admin
net session >nul 2>&1
if %errorlevel% neq 0 (
    echo ERRO: Execute este script como Administrador!
    echo Clique com botao direito -^> Executar como administrador
    pause
    exit /b 1
)

:: ----------------------------------------------------------------
:: 1. MONGODB
:: ----------------------------------------------------------------
echo [1/3] Verificando MongoDB...
sc query MongoDB | findstr "RUNNING" >nul
if %errorlevel% equ 0 (
    echo       MongoDB: OK - Ja esta rodando
) else (
    echo       MongoDB: Iniciando...
    net start MongoDB >nul 2>&1
    if %errorlevel% equ 0 (
        echo       MongoDB: OK - Iniciado com sucesso
    ) else (
        echo       MongoDB: ERRO - Falha ao iniciar
    )
)

:: Configura MongoDB para reiniciar automaticamente em caso de falha
sc failure MongoDB reset= 86400 actions= restart/5000/restart/10000/restart/30000 >nul 2>&1

echo.

:: ----------------------------------------------------------------
:: 2. CLOUDFLARED
:: ----------------------------------------------------------------
echo [2/3] Verificando Cloudflared...
sc query cloudflared | findstr "RUNNING" >nul
if %errorlevel% equ 0 (
    echo       Cloudflared: OK - Ja esta rodando
) else (
    :: Verifica se o servico existe
    sc query cloudflared >nul 2>&1
    if %errorlevel% neq 0 (
        echo       Cloudflared: Instalando servico...
        %USERPROFILE%\cloudflared.exe --config %USERPROFILE%\.cloudflared\config.yml service install >nul 2>&1
    )

    echo       Cloudflared: Iniciando...
    net start cloudflared >nul 2>&1
    if %errorlevel% equ 0 (
        echo       Cloudflared: OK - Iniciado com sucesso
    ) else (
        echo       Cloudflared: ERRO - Falha ao iniciar
    )
)

:: Configura Cloudflared para reiniciar automaticamente em caso de falha
sc failure cloudflared reset= 86400 actions= restart/5000/restart/10000/restart/30000 >nul 2>&1

echo.

:: ----------------------------------------------------------------
:: 3. VERIFICACAO FINAL
:: ----------------------------------------------------------------
echo [3/3] Verificacao Final...
echo.

:: Aguarda 3 segundos para os servicos estabilizarem
timeout /t 3 /nobreak >nul

:: Verifica portas
echo       Portas ativas:
netstat -an | findstr "LISTENING" | findstr ":27017 :3000 :8000"

echo.
echo ================================================================
echo    VERIFICACAO CONCLUIDA
echo ================================================================
echo.
echo    MongoDB:     porta 27017
echo    Frontend:    porta 3000  -^> https://botrading.uk
echo    Backend:     porta 8000  -^> https://api.botrading.uk
echo.
echo ================================================================
pause
