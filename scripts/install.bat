Configurações → Hora e idioma → Data e hora → Sincronizar agora@echo off
echo ========================================
echo  Trading Bot - Instalacao
echo ========================================
echo.

echo [1/3] Instalando dependencias Python...
cd backend
pip install -r requirements.txt
if errorlevel 1 (
    echo Erro ao instalar dependencias Python!
    pause
    exit /b 1
)
cd ..

echo.
echo [2/3] Instalando dependencias Node.js...
cd frontend
where yarn >nul 2>&1
if %ERRORLEVEL%==0 (
    echo Yarn detectado. Instalando com yarn...
    call yarn install
) else (
    echo Yarn nao encontrado. Instalando com npm...
    call npm install
)
if errorlevel 1 (
    echo Erro ao instalar dependencias Node.js!
    pause
    exit /b 1
)
cd ..

echo.
echo [3/3] Verificando MongoDB...
sc query MongoDB >nul 2>&1
if errorlevel 1 (
    echo AVISO: MongoDB nao detectado!
    echo Por favor, instale o MongoDB: https://www.mongodb.com/try/download/community
    echo.
) else (
    echo MongoDB detectado!
)

echo.
echo ========================================
echo  Instalacao concluida!
echo ========================================
echo.
echo Execute start.bat para iniciar o bot
echo.
pause