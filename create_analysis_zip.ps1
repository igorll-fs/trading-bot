# Script para criar ZIP do projeto de trading bot para analise
# Cria COPIAS dos arquivos, nao move os originais

$ErrorActionPreference = "Stop"

# Configuracao
$projectRoot = "C:\Users\igor\Desktop\17-10-2025-main"
$tempDir = Join-Path $env:TEMP "trading-bot-analysis-temp"
$outputZip = Join-Path $projectRoot "trading-bot-analysis.zip"

Write-Host "======================================================================" -ForegroundColor Cyan
Write-Host "CRIANDO ZIP DO PROJETO PARA ANALISE" -ForegroundColor Yellow
Write-Host "======================================================================" -ForegroundColor Cyan

# Limpar diretorio temporario se existir
if (Test-Path $tempDir) {
    Write-Host "`nLimpando diretorio temporario anterior..." -ForegroundColor Gray
    Remove-Item -Path $tempDir -Recurse -Force
}

# Criar diretorio temporario
Write-Host "Criando estrutura temporaria..." -ForegroundColor Cyan
New-Item -ItemType Directory -Path $tempDir -Force | Out-Null

# Criar estrutura de pastas
$folders = @(
    "backend",
    "backend\bot",
    "backend\api",
    "backend\api\routes",
    "backend\scripts",
    "docs",
    "logs",
    "tests"
)

foreach ($folder in $folders) {
    $fullPath = Join-Path $tempDir $folder
    New-Item -ItemType Directory -Path $fullPath -Force | Out-Null
}

Write-Host "OK - Estrutura criada`n" -ForegroundColor Green

# Funcao para copiar arquivo com substituicao de segredos
function Copy-FileWithSecrets {
    param(
        [string]$Source,
        [string]$Destination
    )
    
    $content = Get-Content -Path $Source -Raw -ErrorAction Stop
    
    # Substituir chaves sensiveis
    $content = $content -replace "BINANCE_API_KEY=.*", "BINANCE_API_KEY=SUA_CHAVE_API_AQUI"
    $content = $content -replace "BINANCE_API_SECRET=.*", "BINANCE_API_SECRET=SEU_SECRET_AQUI"
    $content = $content -replace "TELEGRAM_TOKEN=.*", "TELEGRAM_TOKEN=SEU_TOKEN_TELEGRAM_AQUI"
    $content = $content -replace "MONGO_URL=mongodb://.*", "MONGO_URL=mongodb://localhost:27017"
    
    Set-Content -Path $Destination -Value $content -Force
}

# Copiar arquivos do backend
Write-Host "Copiando arquivos do backend..." -ForegroundColor Cyan

$backendFiles = @{
    # Backend principal
    "backend\server.py" = "backend\server.py"
    "backend\requirements.txt" = "backend\requirements.txt"
    
    # Bot core
    "backend\bot\trading_bot.py" = "backend\bot\trading_bot.py"
    "backend\bot\strategy.py" = "backend\bot\strategy.py"
    "backend\bot\risk_manager.py" = "backend\bot\risk_manager.py"
    "backend\bot\selector.py" = "backend\bot\selector.py"
    "backend\bot\binance_client.py" = "backend\bot\binance_client.py"
    "backend\bot\config.py" = "backend\bot\config.py"
    "backend\bot\learning_system.py" = "backend\bot\learning_system.py"
    "backend\bot\market_cache.py" = "backend\bot\market_cache.py"
    "backend\bot\telegram_client.py" = "backend\bot\telegram_client.py"
    "backend\bot\logging_config.py" = "backend\bot\logging_config.py"
    "backend\bot\__init__.py" = "backend\bot\__init__.py"
    
    # API
    "backend\api\__init__.py" = "backend\api\__init__.py"
    "backend\api\models.py" = "backend\api\models.py"
    
    # Scripts uteis
    "backend\test_binance_connection.py" = "backend\scripts\test_binance_connection.py"
    "backend\check_trades.py" = "backend\scripts\check_trades.py"
    "backend\verify_dashboard_sync.py" = "backend\scripts\verify_dashboard_sync.py"
}

$copiedCount = 0
foreach ($file in $backendFiles.Keys) {
    $source = Join-Path $projectRoot $file
    $dest = Join-Path $tempDir $backendFiles[$file]
    
    if (Test-Path $source) {
        Copy-Item -Path $source -Destination $dest -Force
        $copiedCount++
        Write-Host "  OK - $file" -ForegroundColor Gray
    } else {
        Write-Host "  AVISO - $file (nao encontrado)" -ForegroundColor DarkYellow
    }
}

Write-Host "OK - $copiedCount arquivos do backend copiados`n" -ForegroundColor Green

# Copiar .env com substituicao de segredos
Write-Host "Processando arquivo .env..." -ForegroundColor Cyan
$envSource = Join-Path $projectRoot "backend\.env"
$envDest = Join-Path $tempDir "backend\.env"

if (Test-Path $envSource) {
    Copy-FileWithSecrets -Source $envSource -Destination $envDest
    Write-Host "OK - .env copiado com chaves substituidas`n" -ForegroundColor Green
} else {
    Write-Host "AVISO - .env nao encontrado`n" -ForegroundColor Yellow
}

# Copiar documentacao
Write-Host "Copiando documentacao..." -ForegroundColor Cyan

$docFiles = @(
    "README.md",
    "QUICK_START.md",
    "STATUS_ATUAL.md",
    "docs\BOT_ARCHITECTURE.md",
    "docs\MACHINE_LEARNING.md",
    "docs\TESTNET_GUIDE.md",
    "docs\COMO_INICIAR.md",
    "AUDITORIA_PROFISSIONAL.md",
    "PLANO_IMPLEMENTACAO.md",
    "FAQ_CORRECOES.md"
)

$docsCopied = 0
foreach ($file in $docFiles) {
    $source = Join-Path $projectRoot $file
    $filename = Split-Path $file -Leaf
    
    if ($file -like "docs\*") {
        $dest = Join-Path $tempDir $file
    } else {
        $dest = Join-Path $tempDir "docs\$filename"
    }
    
    if (Test-Path $source) {
        Copy-Item -Path $source -Destination $dest -Force
        $docsCopied++
        Write-Host "  OK - $file" -ForegroundColor Gray
    }
}

Write-Host "OK - $docsCopied arquivos de documentacao copiados`n" -ForegroundColor Green

# Copiar codigo de correcoes criticas se existir
$codigoCorrecoes = Join-Path $projectRoot "CODIGO_CORRECOES_CRITICAS.py"
if (Test-Path $codigoCorrecoes) {
    Write-Host "Copiando codigo de correcoes..." -ForegroundColor Cyan
    Copy-Item -Path $codigoCorrecoes -Destination (Join-Path $tempDir "docs\CODIGO_CORRECOES_CRITICAS.py") -Force
    Write-Host "OK - Codigo de correcoes copiado`n" -ForegroundColor Green
}

# Copiar logs recentes (ultimas 1000 linhas)
Write-Host "Copiando logs relevantes..." -ForegroundColor Cyan

$logFiles = @(
    "backend\uvicorn.err",
    "backend\uvicorn_latest.err"
)

$logsCopied = 0
foreach ($logFile in $logFiles) {
    $source = Join-Path $projectRoot $logFile
    
    if (Test-Path $source) {
        $fileInfo = Get-Item $source
        $filename = Split-Path $logFile -Leaf
        $dest = Join-Path $tempDir "logs\$filename"
        
        if ($fileInfo.Length -gt 100KB) {
            # Copiar apenas ultimos 1000 linhas
            $content = Get-Content -Path $source -Tail 1000 -ErrorAction SilentlyContinue
            if ($content) {
                $content | Set-Content -Path $dest
                Write-Host "  OK - $filename (ultimas 1000 linhas)" -ForegroundColor Gray
                $logsCopied++
            }
        } else {
            Copy-Item -Path $source -Destination $dest -Force
            Write-Host "  OK - $filename" -ForegroundColor Gray
            $logsCopied++
        }
    }
}

if ($logsCopied -gt 0) {
    Write-Host "OK - $logsCopied arquivos de log copiados`n" -ForegroundColor Green
} else {
    Write-Host "AVISO - Nenhum arquivo de log encontrado`n" -ForegroundColor Yellow
}

# Copiar testes
Write-Host "Copiando testes..." -ForegroundColor Cyan

$testFiles = Get-ChildItem -Path (Join-Path $projectRoot "tests") -Filter "test_*.py" -ErrorAction SilentlyContinue

$testsCopied = 0
if ($testFiles) {
    foreach ($file in $testFiles) {
        $dest = Join-Path $tempDir "tests\$($file.Name)"
        Copy-Item -Path $file.FullName -Destination $dest -Force
        $testsCopied++
        Write-Host "  OK - $($file.Name)" -ForegroundColor Gray
    }
    Write-Host "OK - $testsCopied arquivos de teste copiados`n" -ForegroundColor Green
} else {
    Write-Host "AVISO - Nenhum arquivo de teste encontrado`n" -ForegroundColor Yellow
}

# Copiar pyproject.toml se existir
$pyproject = Join-Path $projectRoot "pyproject.toml"
if (Test-Path $pyproject) {
    Write-Host "Copiando pyproject.toml..." -ForegroundColor Cyan
    Copy-Item -Path $pyproject -Destination (Join-Path $tempDir "pyproject.toml") -Force
    Write-Host "OK - pyproject.toml copiado`n" -ForegroundColor Green
}

# Criar arquivo README de contexto
Write-Host "Criando README de contexto..." -ForegroundColor Cyan

$readmeContent = @"
# Trading Bot - Analise de Codigo

## Contexto
Este ZIP contem COPIAS dos arquivos essenciais do projeto de trading bot para analise e diagnostico.

**Data de exportacao**: $(Get-Date -Format "dd/MM/yyyy HH:mm:ss")

## Problema Atual
- **Profit Factor**: 0.271 (critico - precisa ser > 1.5)
- **Win Rate**: 33.3%
- **Stop Loss Rate**: 72.2% (muito alto)
- **Take Profit Rate**: 11.1% (muito baixo)

## Estrutura do Projeto

### Backend (/backend)
- **server.py**: API FastAPI principal
- **bot/trading_bot.py**: Orquestrador do bot
- **bot/strategy.py**: Logica de sinais de trading
- **bot/risk_manager.py**: Gestao de risco e posicoes
- **bot/selector.py**: Selecao de criptomoedas
- **bot/binance_client.py**: Integracao com Binance
- **bot/config.py**: Configuracoes centralizadas

### Documentacao (/docs)
- **AUDITORIA_PROFISSIONAL.md**: Analise detalhada dos problemas
- **PLANO_IMPLEMENTACAO.md**: Plano de correcao em 30 dias
- **CODIGO_CORRECOES_CRITICAS.py**: Codigo com correcoes propostas
- **FAQ_CORRECOES.md**: Perguntas e respostas sobre correcoes

### Logs (/logs)
- Ultimas 1000 linhas dos logs principais
- Util para entender comportamento em tempo real

### Testes (/tests)
- Testes unitarios do sistema

## Seguranca
IMPORTANTE: As chaves de API foram substituidas por valores fake:
- BINANCE_API_KEY=SUA_CHAVE_API_AQUI
- BINANCE_API_SECRET=SEU_SECRET_AQUI
- TELEGRAM_TOKEN=SEU_TOKEN_TELEGRAM_AQUI

## Proximos Passos
1. Ler **AUDITORIA_PROFISSIONAL.md** para entender os problemas
2. Revisar **CODIGO_CORRECOES_CRITICAS.py** para ver as correcoes
3. Seguir **PLANO_IMPLEMENTACAO.md** para implementar

## Stack Tecnologico
- **Backend**: Python 3.11 + FastAPI
- **Frontend**: React 18
- **Database**: MongoDB
- **Exchange**: Binance Spot (Testnet disponivel)
- **Notificacoes**: Telegram

## Contato
Para duvidas sobre este codigo, consulte a documentacao incluida.

---
**Nota**: Este e um snapshot do codigo. Os arquivos originais permanecem intactos no projeto.
"@

$readmePath = Join-Path $tempDir "README_ANALISE.md"
Set-Content -Path $readmePath -Value $readmeContent -Force
Write-Host "OK - README de contexto criado`n" -ForegroundColor Green

# Criar arquivo ZIP
Write-Host "Criando arquivo ZIP..." -ForegroundColor Cyan

# Remover ZIP antigo se existir
if (Test-Path $outputZip) {
    Remove-Item -Path $outputZip -Force
    Write-Host "  INFO - ZIP anterior removido" -ForegroundColor Gray
}

# Comprimir
try {
    Compress-Archive -Path "$tempDir\*" -DestinationPath $outputZip -CompressionLevel Optimal -Force
    Write-Host "OK - ZIP criado com sucesso`n" -ForegroundColor Green
} catch {
    Write-Host "ERRO ao criar ZIP: $_" -ForegroundColor Red
    exit 1
}

# Limpar diretorio temporario
Write-Host "Limpando arquivos temporarios..." -ForegroundColor Cyan
Remove-Item -Path $tempDir -Recurse -Force
Write-Host "OK - Limpeza concluida`n" -ForegroundColor Green

# Estatisticas finais
$zipSize = (Get-Item $outputZip).Length / 1MB

Write-Host "======================================================================" -ForegroundColor Cyan
Write-Host "ZIP CRIADO COM SUCESSO!" -ForegroundColor Green
Write-Host "======================================================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Local do arquivo:" -ForegroundColor Yellow
Write-Host "   $outputZip" -ForegroundColor White
Write-Host ""
Write-Host "Tamanho: $([math]::Round($zipSize, 2)) MB" -ForegroundColor Cyan
Write-Host ""
Write-Host "Conteudo incluido:" -ForegroundColor Yellow
Write-Host "   OK - Codigo completo do backend" -ForegroundColor Gray
Write-Host "   OK - Documentacao e analises" -ForegroundColor Gray
Write-Host "   OK - Logs recentes" -ForegroundColor Gray
Write-Host "   OK - Testes" -ForegroundColor Gray
Write-Host "   OK - Configuracoes (chaves substituidas)" -ForegroundColor Gray
Write-Host ""
Write-Host "Seguranca:" -ForegroundColor Yellow
Write-Host "   OK - Chaves de API substituidas por valores fake" -ForegroundColor Green
Write-Host "   OK - Dados sensiveis removidos" -ForegroundColor Green
Write-Host ""
Write-Host "======================================================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Proximo passo: Compartilhar o arquivo para analise" -ForegroundColor Cyan
Write-Host ""
