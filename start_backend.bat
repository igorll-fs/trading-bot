@echo off
echo.
echo === INICIANDO TRADING BOT COM IA ===
echo.

REM Adicionar Ollama ao PATH
set PATH=%PATH%;C:\Users\%USERNAME%\AppData\Local\Programs\Ollama

REM Verificar Ollama
echo [1/3] Verificando Ollama...
ollama --version
if errorlevel 1 (
    echo ERRO: Ollama nao encontrado!
    pause
    exit /b 1
)

REM Ativar ambiente virtual
echo.
echo [2/3] Ativando ambiente virtual...
call .venv\Scripts\activate.bat

REM Iniciar backend
echo.
echo [3/3] Iniciando backend...
echo.
echo Backend disponivel em: http://localhost:8000
echo API Docs: http://localhost:8000/docs
echo LLM Status: http://localhost:8000/api/llm/status
echo.
echo Pressione Ctrl+C para parar o servidor
echo.

python backend\server.py
