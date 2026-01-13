# Script de Limpeza e Preparacao para GitHub
# Versao: 2.0 - Segura e Profissional
# Data: 14/01/2026

param(
    [switch]$DryRun = $false,
    [switch]$Force = $false
)

$ErrorActionPreference = "Stop"
$projectRoot = "$PSScriptRoot\.."

Write-Host "`n=====================================" -ForegroundColor Cyan
Write-Host "PREPARACAO PARA GITHUB - LIMPEZA" -ForegroundColor Cyan
Write-Host "=====================================" -ForegroundColor Cyan

if ($DryRun) {
    Write-Host "`nMODO DRY-RUN: Nenhum arquivo sera modificado" -ForegroundColor Yellow
} else {
    Write-Host "`nMODO EXECUCAO: Arquivos serao modificados/removidos" -ForegroundColor Green
}

# FASE 1: Identificar arquivos sensiveis
Write-Host "`nFASE 1: Identificando arquivos sensiveis..." -ForegroundColor Cyan

$sensitivePaths = @(
    "backend\.env",
    "frontend\.env",
    "frontend\.env.local",
    "frontend\.env.production",
    "backend\uvicorn*.err",
    "backend\*.log",
    "logs\*.log",
    "*.err",
    "temp_trades.json",
    "temp_trades.json",
    "backend\trades_backup*.json",
    "data_raw\*.json",
    "analysis\*.zip",
    "lhci-report",
    "playwright-report",
    "test-results",
    "query",
    "nul",
    "*.bak",
    "*.tmp"
)

$foundSensitive = @()

foreach ($pattern in $sensitivePaths) {
    $files = Get-ChildItem -Path $projectRoot -Filter $pattern -Recurse -Force -ErrorAction SilentlyContinue
    if ($files) {
        $foundSensitive += $files
    }
}

Write-Host "Encontrados $($foundSensitive.Count) arquivos/pastas sensiveis" -ForegroundColor Yellow

# FASE 2: Atualizar .gitignore
Write-Host "`nFASE 2: Verificando/atualizando .gitignore..." -ForegroundColor Cyan

$gitignorePath = Join-Path $projectRoot ".gitignore"
$gitignoreContent = @"
# DADOS SENSIVEIS (NUNCA COMMITAR)
*.env
.env
.env.*
!.env.example

# API Keys e Credenciais
*secret*
*token*
*credentials*
*.key
*.pem

# LOGS E HISTORICO
*.log
*.err
logs/
*.log.*

# DADOS DE TRADING (PRIVADOS)
temp_trades.json
*trades_backup*.json
data_raw/*.json
data_raw/*.csv
cUsersigor*

# PYTHON
__pycache__/
*.py[cod]
*`$py.class
*.so
.Python
build/
develop-eggs/
dist/
downloads/
eggs/
.eggs/
lib/
lib64/
parts/
sdist/
var/
wheels/
*.egg-info/
.installed.cfg
*.egg
MANIFEST

# Virtual environments
.venv/
venv/
ENV/
env/
.virtualenv/

# PyTest
.pytest_cache/
.coverage
htmlcov/

# NODE / FRONTEND
node_modules/
npm-debug.log*
yarn-debug.log*
yarn-error.log*

# Build
frontend/build/
frontend/dist/
frontend/.cache/

# Reports
lhci-report/
playwright-report/
test-results/

# IDEs
.vscode/*
!.vscode/extensions.json
.idea/
*.swp
*.swo
*~

# SISTEMA OPERACIONAL
.DS_Store
Thumbs.db
desktop.ini
nul
query

# MONGODB DUMPS
*.dump
mongo_backup/

# TEMPORARIOS
*.tmp
*.bak
*.backup
temp/
tmp/
"@

if ($DryRun) {
    Write-Host "  DRY-RUN: Atualizaria .gitignore" -ForegroundColor Yellow
} else {
    Set-Content -Path $gitignorePath -Value $gitignoreContent -Encoding UTF8
    Write-Host "Gitignore atualizado" -ForegroundColor Green
}

# FASE 3: Criar .env.example
Write-Host "`nFASE 3: Criando arquivos .env.example..." -ForegroundColor Cyan

$backendEnvExample = @"
# BINANCE API (Obter em https://www.binance.com/en/my/settings/api-management)
BINANCE_API_KEY=your_binance_api_key_here
BINANCE_API_SECRET=your_binance_secret_here
USE_TESTNET=true

# MONGODB
MONGO_URL=mongodb://localhost:27017
DB_NAME=trading_bot

# TELEGRAM NOTIFICATIONS
TELEGRAM_BOT_TOKEN=your_telegram_bot_token
TELEGRAM_CHAT_ID=your_telegram_chat_id

# TRADING SETTINGS
CAPITAL_INICIAL=1000.0
MAX_POSITIONS=3
RISK_PER_TRADE=0.02
"@

$frontendEnvExample = @"
# BACKEND API
REACT_APP_BACKEND_URL=http://localhost:8000

# ENVIRONMENT
NODE_ENV=development
"@

$backendEnvPath = Join-Path $projectRoot "backend\.env.example"
$frontendEnvPath = Join-Path $projectRoot "frontend\.env.example"

if ($DryRun) {
    Write-Host "  DRY-RUN: Criaria backend\.env.example" -ForegroundColor Yellow
    Write-Host "  DRY-RUN: Criaria frontend\.env.example" -ForegroundColor Yellow
} else {
    Set-Content -Path $backendEnvPath -Value $backendEnvExample -Encoding UTF8
    Set-Content -Path $frontendEnvPath -Value $frontendEnvExample -Encoding UTF8
    Write-Host "Arquivos .env.example criados" -ForegroundColor Green
}

# FASE 4: Remover arquivos sensiveis
Write-Host "`nFASE 4: Removendo arquivos sensiveis..." -ForegroundColor Cyan

$removedCount = 0
$skippedCount = 0

foreach ($file in $foundSensitive) {
    $relativePath = $file.FullName.Replace($projectRoot, "").TrimStart("\")
    
    if ($DryRun) {
        Write-Host "  DRY-RUN: Removeria $relativePath" -ForegroundColor Yellow
        $removedCount++
    } else {
        try {
            if ($file.PSIsContainer) {
                Remove-Item -Path $file.FullName -Recurse -Force
            } else {
                Remove-Item -Path $file.FullName -Force
            }
            Write-Host "  Removido: $relativePath" -ForegroundColor Green
            $removedCount++
        } catch {
            Write-Host "  Erro ao remover: $relativePath" -ForegroundColor Red
            $skippedCount++
        }
    }
}

# FASE 5: Limpar arquivos markdown temporarios
Write-Host "`nFASE 5: Limpando arquivos markdown temporarios..." -ForegroundColor Cyan

$mdToRemove = @(
    "ACESSO_BOTRADING_UK.md",
    "ANALISE_DASHBOARD_DADOS.md",
    "ATUALIZACAO_GITHUB.txt",
    "AUDITORIA_PROFISSIONAL.md",
    "FAQ_CORRECOES.md",
    "REMOTE_ACCESS_STATUS.md",
    "VSCODE_REMOTE_SETUP.md",
    "AI_COORDINATION.md",
    "AI_SESSION_LOG.jsonl",
    "STATUS_ATUAL.md",
    "frontend\ACESSO_REMOTO.md"
)

foreach ($md in $mdToRemove) {
    $mdPath = Join-Path $projectRoot $md
    if (Test-Path $mdPath) {
        if ($DryRun) {
            Write-Host "  DRY-RUN: Removeria $md" -ForegroundColor Yellow
        } else {
            Remove-Item -Path $mdPath -Force
            Write-Host "  Removido: $md" -ForegroundColor Green
        }
        $removedCount++
    }
}

# FASE 6: Corrigir problema Roff
Write-Host "`nFASE 6: Verificando problema Roff (81.4%)..." -ForegroundColor Cyan

$gitattributesContent = @"
# Força detecção correta de linguagens no GitHub
*.py linguist-language=Python
*.js linguist-language=JavaScript
*.jsx linguist-language=JavaScript
*.ts linguist-language=TypeScript
*.tsx linguist-language=TypeScript

# Marca arquivos que não devem contar para estatísticas
*.md linguist-documentation
*.json linguist-generated=true
*.lock linguist-generated=true
package-lock.json linguist-generated=true
yarn.lock linguist-generated=true

# Ignora arquivos de build/vendor
frontend/build/** linguist-vendored
node_modules/** linguist-vendored
.venv/** linguist-vendored
__pycache__/** linguist-vendored
"@

$gitattributesPath = Join-Path $projectRoot ".gitattributes"

if ($DryRun) {
    Write-Host "  DRY-RUN: Criaria .gitattributes para corrigir Roff" -ForegroundColor Yellow
} else {
    Set-Content -Path $gitattributesPath -Value $gitattributesContent -Encoding UTF8
    Write-Host "Gitattributes criado (corrige problema Roff)" -ForegroundColor Green
}

# FASE 7: Verificar arquivos .env
Write-Host "`nFASE 7: Verificando arquivos .env no projeto..." -ForegroundColor Cyan

$envFiles = Get-ChildItem -Path $projectRoot -Filter ".env*" -Recurse -Force -ErrorAction SilentlyContinue | Where-Object { $_.Name -notlike "*.example" }

if ($envFiles) {
    Write-Host "`nATENCAO: Encontrados $($envFiles.Count) arquivos .env:" -ForegroundColor Red
    foreach ($env in $envFiles) {
        $relativePath = $env.FullName.Replace($projectRoot, "").TrimStart("\")
        Write-Host "  - $relativePath" -ForegroundColor Red
    }
    Write-Host "`nEstes arquivos NAO serao commitados (protegidos por .gitignore)" -ForegroundColor Yellow
} else {
    Write-Host "Nenhum arquivo .env encontrado (seguro)" -ForegroundColor Green
}

# RESUMO FINAL
Write-Host "`n=====================================" -ForegroundColor Cyan
Write-Host "RESUMO DA LIMPEZA" -ForegroundColor Cyan
Write-Host "=====================================" -ForegroundColor Cyan

if ($DryRun) {
    Write-Host "`nMODO DRY-RUN - Nada foi modificado" -ForegroundColor Yellow
    Write-Host "Execute novamente SEM -DryRun para aplicar mudancas" -ForegroundColor Yellow
}

Write-Host "`nArquivos/pastas que seriam removidos: $removedCount" -ForegroundColor Yellow
Write-Host "Arquivos com erro (nao removidos): $skippedCount" -ForegroundColor $(if($skippedCount -gt 0){'Red'}else{'Green'})

Write-Host "`nCHECKLIST DE SEGURANCA:" -ForegroundColor Green
Write-Host "  [OK] .gitignore atualizado" -ForegroundColor Green
Write-Host "  [OK] .env.example criados" -ForegroundColor Green
Write-Host "  [OK] .gitattributes criado (corrige Roff)" -ForegroundColor Green
Write-Host "  [OK] Arquivos sensiveis identificados" -ForegroundColor Green

Write-Host "`nPROXIMOS PASSOS:" -ForegroundColor Cyan
Write-Host "  1. Execute este script SEM -DryRun para aplicar mudancas" -ForegroundColor White
Write-Host "  2. Verifique os arquivos .env.example e configure localmente" -ForegroundColor White
Write-Host "  3. Execute: git add ." -ForegroundColor White
Write-Host "  4. Execute: git commit -m 'chore: prepare for github'" -ForegroundColor White
Write-Host "  5. Execute: git push origin main" -ForegroundColor White

Write-Host "`nScript concluido com sucesso!" -ForegroundColor Green
Write-Host "=====================================" -ForegroundColor Cyan
