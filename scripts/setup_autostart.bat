@echo off
:: ================================================================
:: CONFIGURA INICIALIZACAO AUTOMATICA DOS SERVICOS
:: Executar como Administrador (apenas uma vez)
:: ================================================================

echo ================================================================
echo    CONFIGURANDO INICIALIZACAO AUTOMATICA
echo ================================================================
echo.

:: Verifica se esta rodando como admin
net session >nul 2>&1
if %errorlevel% neq 0 (
    echo ERRO: Execute este script como Administrador!
    pause
    exit /b 1
)

:: ----------------------------------------------------------------
:: 1. CONFIGURA MONGODB PARA AUTO-START
:: ----------------------------------------------------------------
echo [1/4] Configurando MongoDB para iniciar automaticamente...
sc config MongoDB start= auto >nul 2>&1
sc failure MongoDB reset= 86400 actions= restart/5000/restart/10000/restart/30000 >nul 2>&1
echo       OK

:: ----------------------------------------------------------------
:: 2. CONFIGURA CLOUDFLARED PARA AUTO-START
:: ----------------------------------------------------------------
echo [2/4] Configurando Cloudflared para iniciar automaticamente...

:: Remove servico antigo se existir com config errada
sc query cloudflared >nul 2>&1
if %errorlevel% equ 0 (
    echo       Removendo instalacao antiga...
    net stop cloudflared >nul 2>&1
    C:\Users\igor\cloudflared.exe service uninstall >nul 2>&1
    timeout /t 2 /nobreak >nul
)

:: Instala com configuracao correta
echo       Instalando com configuracao correta...
C:\Users\igor\cloudflared.exe --config C:\Users\igor\.cloudflared\config.yml service install >nul 2>&1

sc config cloudflared start= auto >nul 2>&1
sc failure cloudflared reset= 86400 actions= restart/5000/restart/10000/restart/30000 >nul 2>&1
echo       OK

:: ----------------------------------------------------------------
:: 3. INICIA OS SERVICOS AGORA
:: ----------------------------------------------------------------
echo [3/4] Iniciando servicos...
net start MongoDB >nul 2>&1
net start cloudflared >nul 2>&1
echo       OK

:: ----------------------------------------------------------------
:: 4. VERIFICACAO
:: ----------------------------------------------------------------
echo [4/4] Verificando status...
echo.

sc query MongoDB | findstr "ESTADO"
sc query cloudflared | findstr "ESTADO"

echo.
echo ================================================================
echo    CONFIGURACAO CONCLUIDA!
echo ================================================================
echo.
echo    Os servicos agora:
echo    - Iniciam automaticamente com o Windows
echo    - Reiniciam automaticamente se falharem
echo    - Usam a configuracao IPv4 correta (127.0.0.1)
echo.
echo ================================================================
pause
