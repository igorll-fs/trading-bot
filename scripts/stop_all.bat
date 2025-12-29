@echo off
:: ============================================================
:: TRADING BOT - Parar Sistema Completo
:: ============================================================

cd /d "%~dp0"
powershell -ExecutionPolicy Bypass -File "stop_all.ps1"
