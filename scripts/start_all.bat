@echo off
:: ============================================================
:: TRADING BOT - Iniciar Sistema Completo
:: ============================================================
:: Inicia Backend + Frontend. O bot fica PARADO ate voce
:: configurar e iniciar manualmente pelo Dashboard.
:: ============================================================

cd /d "%~dp0"
powershell -ExecutionPolicy Bypass -File "start_all.ps1"
