@echo off
:: ================================================================
:: HEALTH CHECK - Verifica e reinicia servicos se necessario
:: Pode ser agendado no Task Scheduler para rodar a cada 5 min
:: ================================================================

:: Log com timestamp
echo [%date% %time%] Health Check Iniciado >> C:\Users\igor\botrading_health.log

:: Verifica MongoDB
sc query MongoDB | findstr "RUNNING" >nul
if %errorlevel% neq 0 (
    echo [%date% %time%] MongoDB estava parado - reiniciando >> C:\Users\igor\botrading_health.log
    net start MongoDB >nul 2>&1
)

:: Verifica Cloudflared
sc query cloudflared | findstr "RUNNING" >nul
if %errorlevel% neq 0 (
    echo [%date% %time%] Cloudflared estava parado - reiniciando >> C:\Users\igor\botrading_health.log
    net start cloudflared >nul 2>&1
)

exit /b 0
