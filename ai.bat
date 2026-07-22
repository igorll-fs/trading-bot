@echo off
REM ============================================
REM Quick AI Sync Commands for Windows CMD
REM ============================================

set ROOT=%~dp0..
set SCRIPT=%ROOT%\scripts\ai_sync.ps1

if "%1"=="" goto status
if "%1"=="status" goto status
if "%1"=="s" goto status
if "%1"=="notify" goto notify
if "%1"=="n" goto notify
if "%1"=="check" goto check
if "%1"=="c" goto check
if "%1"=="work" goto work
if "%1"=="w" goto work
if "%1"=="help" goto help
if "%1"=="h" goto help

:status
powershell -ExecutionPolicy Bypass -File "%SCRIPT%" -Action status
goto end

:notify
if "%2"=="" (
    echo Uso: ai A "mensagem" - Envia mensagem da Sessao A para B
    echo Uso: ai B "mensagem" - Envia mensagem da Sessao B para A
    goto end
)
powershell -ExecutionPolicy Bypass -File "%SCRIPT%" -Action notify -Session %2 -Message "%~3"
goto end

:check
if "%2"=="" (
    echo Uso: ai check A - Verifica mensagens para Sessao A
    echo Uso: ai check B - Verifica mensagens para Sessao B
    goto end
)
powershell -ExecutionPolicy Bypass -File "%SCRIPT%" -Action check -Session %2
goto end

:work
if "%2"=="" (
    echo Uso: ai work A "tarefa" - Marca Sessao A trabalhando
    echo Uso: ai work B "tarefa" - Marca Sessao B trabalhando
    goto end
)
powershell -ExecutionPolicy Bypass -File "%SCRIPT%" -Action work -Session %2 -Task "%~3"
goto end

:help
echo.
echo === AI SYNC - Comandos Rapidos ===
echo.
echo   ai              - Ver status das sessoes
echo   ai s            - Ver status (alias)
echo   ai n A "msg"    - Sessao A notifica B
echo   ai n B "msg"    - Sessao B notifica A
echo   ai c A          - Verifica mensagens para A
echo   ai c B          - Verifica mensagens para B
echo   ai w A "task"   - Marca A trabalhando
echo   ai w B "task"   - Marca B trabalhando
echo   ai h            - Esta ajuda
echo.
goto end

:end
