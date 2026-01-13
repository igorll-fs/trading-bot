# 🧹 Script de Limpeza e Preparação para GitHub
# Versão: 2.0 - Profissional e Seguro
# Data: 14/01/2026

param(
    [switch]$DryRun = $false,  # Simula sem deletar
    [switch]$Force = $false     # Força limpeza sem confirmação
)

$ErrorActionPreference = "Stop"
$projectRoot = Split-Path -Parent $PSScriptRoot

Write-Host "`n🔍 ANÁLISE PROFISSIONAL DE LIMPEZA PARA GITHUB" -ForegroundColor Cyan
Write-Host "=" * 70 -ForegroundColor Cyan
Write-Host "Projeto: $projectRoot" -ForegroundColor Yellow
if ($DryRun) {
    Write-Host "⚠️  MODO DRY-RUN: Nada será deletado (simulação apenas)" -ForegroundColor Yellow
}
Write-Host ""

# ============================================================================
# FASE 1: VERIFICAÇÃO DE SEGURANÇA - ARQUIVOS .ENV
# ============================================================================
Write-Host "`n📋 FASE 1: Verificando arquivos .env existentes..." -ForegroundColor Green

$envFiles = @(
    "$projectRoot\backend\.env",
    "$projectRoot\frontend\.env",
    "$projectRoot\frontend\.env.development.local"
)

$envFilesFound = @()
foreach ($envFile in $envFiles) {
    if (Test-Path $envFile) {
        $envFilesFound += $envFile
        Write-Host "  ✅ Encontrado: $($envFile -replace [regex]::Escape($projectRoot), '.')" -ForegroundColor Green
    }
}

if ($envFilesFound.Count -eq 0) {
    Write-Host "  ⚠️  Nenhum arquivo .env encontrado (já foram ignorados)" -ForegroundColor Yellow
} else {
    Write-Host "`n  📝 Total: $($envFilesFound.Count) arquivos .env encontrados" -ForegroundColor Cyan
}

# ============================================================================
# FASE 2: BUSCAR DADOS SENSÍVEIS EM CÓDIGO
# ============================================================================
Write-Host "`n🔎 FASE 2: Buscando dados sensíveis hardcoded..." -ForegroundColor Green

$sensitivePaths = @(
    "$projectRoot\backend\*.py",
    "$projectRoot\frontend\src\**\*.js",
    "$projectRoot\frontend\src\**\*.jsx",
    "$projectRoot\frontend\src\**\*.ts",
    "$projectRoot\frontend\src\**\*.tsx"
)

$sensitivePatterns = @{
    "API Keys" = "(api[_-]?key|api[_-]?secret)\s*=\s*['\"][^'\"]{20,}['\"]"
    "Tokens" = "(token|bearer)\s*=\s*['\"][^'\"]{30,}['\"]"
    "Senhas" = "(password|passwd|pwd)\s*=\s*['\"][^'\"]+['\"]"
    "IPs Privados" = "\b192\.168\.\d{1,3}\.\d{1,3}\b"
    "MongoDB URLs" = "mongodb:\/\/[^\/]+@"
}

$sensitiveFound = @()
foreach ($pattern in $sensitivePatterns.GetEnumerator()) {
    Write-Host "  Buscando: $($pattern.Key)..." -NoNewline
    
    $matches = Get-ChildItem -Path $projectRoot -Include *.py,*.js,*.jsx,*.ts,*.tsx -Recurse -ErrorAction SilentlyContinue |
        Select-String -Pattern $pattern.Value -List |
        Where-Object { 
            $_.Path -notmatch "node_modules" -and 
            $_.Path -notmatch ".venv" -and
            $_.Path -notmatch "__pycache__" -and
            $_.Path -notmatch "\.example\."
        }
    
    if ($matches) {
        $sensitiveFound += @{
            Type = $pattern.Key
            Matches = $matches
        }
        Write-Host " ⚠️  $($matches.Count) encontrado(s)" -ForegroundColor Yellow
    } else {
        Write-Host " ✅" -ForegroundColor Green
    }
}

if ($sensitiveFound.Count -gt 0) {
    Write-Host "`n  ⚠️  ATENÇÃO: Dados sensíveis encontrados em código!" -ForegroundColor Red
    foreach ($item in $sensitiveFound) {
        Write-Host "`n  📄 $($item.Type):" -ForegroundColor Yellow
        foreach ($match in $item.Matches) {
            $relativePath = $match.Path -replace [regex]::Escape($projectRoot), "."
            Write-Host "    - $relativePath : Linha $($match.LineNumber)" -ForegroundColor Gray
            Write-Host "      $($match.Line.Trim())" -ForegroundColor DarkGray
        }
    }
    Write-Host "`n  ⚠️  RECOMENDAÇÃO: Refatore para usar variáveis de ambiente" -ForegroundColor Yellow
} else {
    Write-Host "  ✅ Nenhum dado sensível hardcoded encontrado!" -ForegroundColor Green
}

# ============================================================================
# FASE 3: IDENTIFICAR ARQUIVOS PARA DELETAR
# ============================================================================
Write-Host "`n🗑️  FASE 3: Identificando arquivos para deletar..." -ForegroundColor Green

$filesToDelete = @()

# 3.1 Logs
Write-Host "  Buscando logs..." -NoNewline
$logs = Get-ChildItem -Path $projectRoot -Include *.log,*.err -Recurse -ErrorAction SilentlyContinue |
    Where-Object { $_.FullName -notmatch "node_modules" }
$filesToDelete += $logs
Write-Host " $($logs.Count) encontrado(s)" -ForegroundColor Cyan

# 3.2 Arquivos query, nul, -w
Write-Host "  Buscando arquivos inválidos (query, nul, -w)..." -NoNewline
$invalidFiles = Get-ChildItem -Path $projectRoot -Include query,nul,-w -Recurse -ErrorAction SilentlyContinue |
    Where-Object { $_.FullName -notmatch "node_modules" }
$filesToDelete += $invalidFiles
Write-Host " $($invalidFiles.Count) encontrado(s)" -ForegroundColor Cyan

# 3.3 Caches Python
Write-Host "  Buscando caches Python (__pycache__)..." -NoNewline
$pycache = Get-ChildItem -Path $projectRoot -Directory -Filter "__pycache__" -Recurse -ErrorAction SilentlyContinue
$filesToDelete += $pycache
Write-Host " $($pycache.Count) encontrado(s)" -ForegroundColor Cyan

# 3.4 Arquivos temporários
Write-Host "  Buscando temporários (temp_*, tmp, *.tmp)..." -NoNewline
$tempFiles = Get-ChildItem -Path $projectRoot -Include temp_*,*.tmp -Recurse -ErrorAction SilentlyContinue |
    Where-Object { $_.FullName -notmatch "node_modules" }
$filesToDelete += $tempFiles
Write-Host " $($tempFiles.Count) encontrado(s)" -ForegroundColor Cyan

# 3.5 Diretórios grandes (node_modules, build, dist)
Write-Host "  Analisando diretórios grandes..." -NoNewline
$largeDirs = @()
$dirsToCheck = @("node_modules", "build", "dist", ".venv", "venv")
foreach ($dir in $dirsToCheck) {
    $paths = Get-ChildItem -Path $projectRoot -Directory -Filter $dir -Recurse -ErrorAction SilentlyContinue |
        Where-Object { $_.Parent.Name -ne ".archive" }  # Preservar .archive se existir
    $largeDirs += $paths
}
Write-Host " $($largeDirs.Count) encontrado(s)" -ForegroundColor Cyan

# 3.6 Playwright/Lighthouse reports
Write-Host "  Buscando relatórios de testes..." -NoNewline
$testReports = Get-ChildItem -Path "$projectRoot\frontend" -Directory -Include playwright-report,lhci-report,test-results -ErrorAction SilentlyContineContinue
$filesToDelete += $testReports
Write-Host " $($testReports.Count) encontrado(s)" -ForegroundColor Cyan

# 3.7 Arquivos de análise (*.zip, *.tar.gz)
Write-Host "  Buscando arquivos de backup/análise..." -NoNewline
$archives = Get-ChildItem -Path $projectRoot -Include *.zip,*.tar.gz,*.tar,*.tgz -Recurse -ErrorAction SilentlyContinue |
    Where-Object { $_.FullName -notmatch "node_modules" }
$filesToDelete += $archives
Write-Host " $($archives.Count) encontrado(s)" -ForegroundColor Cyan

# ============================================================================
# FASE 4: RESUMO E CONFIRMAÇÃO
# ============================================================================
Write-Host "`n📊 FASE 4: Resumo da limpeza" -ForegroundColor Green
Write-Host "=" * 70 -ForegroundColor Cyan

$totalSize = 0
$itemsByCategory = @{
    "Logs" = $logs
    "Arquivos Inválidos" = $invalidFiles
    "Caches Python" = $pycache
    "Temporários" = $tempFiles
    "Diretórios Grandes" = $largeDirs
    "Relatórios de Teste" = $testReports
    "Arquivos de Backup" = $archives
}

foreach ($category in $itemsByCategory.GetEnumerator()) {
    if ($category.Value.Count -gt 0) {
        $categorySize = ($category.Value | Measure-Object -Property Length -Sum -ErrorAction SilentlyContinue).Sum
        if ($null -eq $categorySize) { $categorySize = 0 }
        $totalSize += $categorySize
        
        Write-Host "`n  📁 $($category.Key):" -ForegroundColor Yellow
        Write-Host "    Quantidade: $($category.Value.Count) item(s)" -ForegroundColor Cyan
        Write-Host "    Tamanho: $([math]::Round($categorySize / 1MB, 2)) MB" -ForegroundColor Cyan
        
        # Mostrar até 5 exemplos
        $examples = $category.Value | Select-Object -First 5
        foreach ($item in $examples) {
            $relativePath = $item.FullName -replace [regex]::Escape($projectRoot), "."
            Write-Host "      - $relativePath" -ForegroundColor Gray
        }
        if ($category.Value.Count -gt 5) {
            Write-Host "      ... e mais $($category.Value.Count - 5) item(s)" -ForegroundColor DarkGray
        }
    }
}

Write-Host "`n  💾 TOTAL A DELETAR:" -ForegroundColor Magenta
Write-Host "    Arquivos/Pastas: $($filesToDelete.Count + $largeDirs.Count) item(s)" -ForegroundColor White
Write-Host "    Espaço liberado: ~$([math]::Round($totalSize / 1MB, 2)) MB" -ForegroundColor White

# ============================================================================
# FASE 5: VERIFICAR .gitignore
# ============================================================================
Write-Host "`n🛡️  FASE 5: Verificando .gitignore..." -ForegroundColor Green

$gitignorePath = "$projectRoot\.gitignore"
$gitignoreContent = @"
# 🔐 CREDENCIAIS E SEGURANÇA (NUNCA ENVIAR!)
.env
.env.local
.env.*.local
*.key
*.pem
*.p8
credentials.json
*credentials*
*token.json*

# 🐍 PYTHON
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
.pytest_cache/
.coverage
htmlcov/

# 📦 VIRTUAL ENVIRONMENTS
.venv/
venv/
env/
ENV/
env.bak/
venv.bak/

# 📝 LOGS E TEMPORÁRIOS
*.log
*.err
query
nul
logs/
temp/
tmp/
*.tmp
uvicorn*.err
uvicorn*.log
backend.log

# 🎨 NODEJS / FRONTEND
node_modules/
npm-debug.log*
yarn-debug.log*
yarn-error.log*
/.pnp
.pnp.js
frontend/build/
frontend/dist/
frontend/lhci-report/
frontend/playwright-report/
frontend/test-results/
.cache/
-w

# 🔧 IDE E EDITORES
.vscode/
.idea/
*.swp
*.swo
*~
.DS_Store

# 🗂️ ARQUIVOS GERADOS
*.zip
*.tar.gz
*.tar
*.tgz
analysis/
data_raw/
*.csv
temp_*

# 🤖 BOT ESPECÍFICO
backend/bot/logs/
data_collection/
strategy/backtest_results/
*.pkl
*.joblib
*.sqlite
*.db

# 📊 MONGODB E DATABASES
dump/
backup/
*.mongodump

# 📋 MISC
.ai_status.json
.ai_work_log.jsonl
AI_SESSION_LOG.jsonl
"@

if (Test-Path $gitignorePath) {
    $currentContent = Get-Content $gitignorePath -Raw
    if ($currentContent -notmatch "\.env" -or $currentContent -notmatch "__pycache__") {
        Write-Host "  ⚠️  .gitignore incompleto ou desatualizado" -ForegroundColor Yellow
        if (-not $DryRun) {
            Write-Host "  📝 Atualizando .gitignore..." -ForegroundColor Cyan
            $gitignoreContent | Set-Content $gitignorePath -Encoding UTF8
            Write-Host "  ✅ .gitignore atualizado!" -ForegroundColor Green
        } else {
            Write-Host "  📝 [DRY-RUN] .gitignore seria atualizado" -ForegroundColor Yellow
        }
    } else {
        Write-Host "  ✅ .gitignore está atualizado" -ForegroundColor Green
    }
} else {
    Write-Host "  ⚠️  .gitignore não encontrado!" -ForegroundColor Red
    if (-not $DryRun) {
        Write-Host "  📝 Criando .gitignore..." -ForegroundColor Cyan
        $gitignoreContent | Set-Content $gitignorePath -Encoding UTF8
        Write-Host "  ✅ .gitignore criado!" -ForegroundColor Green
    } else {
        Write-Host "  📝 [DRY-RUN] .gitignore seria criado" -ForegroundColor Yellow
    }
}

# ============================================================================
# FASE 6: VERIFICAR .gitattributes (Solução Roff)
# ============================================================================
Write-Host "`n🏷️  FASE 6: Verificando .gitattributes (correção Roff)..." -ForegroundColor Green

$gitattributesPath = "$projectRoot\.gitattributes"
$gitattributesContent = @"
# 🎯 Indicar linguagens principais ao GitHub Linguist
*.py linguist-language=Python
*.js linguist-language=JavaScript
*.jsx linguist-language=JavaScript
*.ts linguist-language=TypeScript
*.tsx linguist-language=TypeScript

# 📦 Marcar dependências como vendored (não conta nas estatísticas)
node_modules/ linguist-vendored
.venv/ linguist-vendored
venv/ linguist-vendored
frontend/build/ linguist-vendored
frontend/node_modules/ linguist-vendored

# 📋 Marcar arquivos gerados como generated
*.min.js linguist-generated
*.min.css linguist-generated
frontend/build/** linguist-generated
"@

if (Test-Path $gitattributesPath) {
    Write-Host "  ✅ .gitattributes já existe" -ForegroundColor Green
} else {
    Write-Host "  ⚠️  .gitattributes não encontrado (necessário para corrigir Roff 81.4%)" -ForegroundColor Yellow
    if (-not $DryRun) {
        Write-Host "  📝 Criando .gitattributes..." -ForegroundColor Cyan
        $gitattributesContent | Set-Content $gitattributesPath -Encoding UTF8
        Write-Host "  ✅ .gitattributes criado!" -ForegroundColor Green
    } else {
        Write-Host "  📝 [DRY-RUN] .gitattributes seria criado" -ForegroundColor Yellow
    }
}

# ============================================================================
# FASE 7: EXECUÇÃO DA LIMPEZA
# ============================================================================
if (-not $DryRun) {
    if (-not $Force) {
        Write-Host "`n⚠️  CONFIRMAÇÃO NECESSÁRIA" -ForegroundColor Yellow
        Write-Host "Isso irá deletar $($filesToDelete.Count + $largeDirs.Count) item(s) (~$([math]::Round($totalSize / 1MB, 2)) MB)" -ForegroundColor Yellow
        $confirmation = Read-Host "`nProsseguir com a limpeza? (S/N)"
        
        if ($confirmation -ne 'S' -and $confirmation -ne 's') {
            Write-Host "`n❌ Limpeza cancelada pelo usuário" -ForegroundColor Red
            exit 0
        }
    }
    
    Write-Host "`n🗑️  FASE 7: Executando limpeza..." -ForegroundColor Green
    
    $deletedCount = 0
    $errors = @()
    
    # Deletar arquivos individuais
    foreach ($file in $filesToDelete) {
        try {
            if (Test-Path $file.FullName) {
                Remove-Item $file.FullName -Force -Recurse -ErrorAction Stop
                $deletedCount++
                Write-Progress -Activity "Limpando arquivos" -Status "Deletado: $($file.Name)" -PercentComplete (($deletedCount / ($filesToDelete.Count + $largeDirs.Count)) * 100)
            }
        } catch {
            $errors += "Erro ao deletar $($file.FullName): $($_.Exception.Message)"
        }
    }
    
    # Deletar diretórios grandes
    foreach ($dir in $largeDirs) {
        try {
            if (Test-Path $dir.FullName) {
                Remove-Item $dir.FullName -Force -Recurse -ErrorAction Stop
                $deletedCount++
                Write-Progress -Activity "Limpando diretórios" -Status "Deletado: $($dir.Name)" -PercentComplete (($deletedCount / ($filesToDelete.Count + $largeDirs.Count)) * 100)
            }
        } catch {
            $errors += "Erro ao deletar $($dir.FullName): $($_.Exception.Message)"
        }
    }
    
    Write-Progress -Completed -Activity "Limpeza concluída"
    
    Write-Host "`n  ✅ Limpeza concluída!" -ForegroundColor Green
    Write-Host "  📊 Deletados: $deletedCount item(s)" -ForegroundColor Cyan
    
    if ($errors.Count -gt 0) {
        Write-Host "`n  ⚠️  Erros encontrados ($($errors.Count)):" -ForegroundColor Yellow
        foreach ($error in $errors) {
            Write-Host "    - $error" -ForegroundColor Red
        }
    }
} else {
    Write-Host "`n  ℹ️  [DRY-RUN] Nenhum arquivo foi deletado (simulação)" -ForegroundColor Yellow
}

# ============================================================================
# FASE 8: INSTRUÇÕES FINAIS
# ============================================================================
Write-Host "`n📋 FASE 8: Próximos passos para GitHub" -ForegroundColor Green
Write-Host "=" * 70 -ForegroundColor Cyan

Write-Host @"

✅ LIMPEZA CONCLUÍDA! Próximos passos:

1️⃣  VERIFICAR STATUS GIT
   git status
   (deve mostrar apenas arquivos tracked, sem .env, logs, etc)

2️⃣  ADICIONAR MUDANÇAS
   git add .gitignore .gitattributes
   git commit -m "chore: Atualizar .gitignore e .gitattributes para GitHub"

3️⃣  REMOVER ARQUIVOS DO HISTÓRICO (se já commitados)
   git rm --cached backend/.env frontend/.env -f
   git rm --cached backend/*.log frontend/*.log -f
   git commit -m "chore: Remover arquivos sensíveis do histórico"

4️⃣  PUSH PARA GITHUB
   git push origin main

5️⃣  VERIFICAR CORREÇÃO DO ROFF
   • GitHub reprocessará em 24-48h
   • Linguagem principal: Python (~80%)
   • Linguagem secundária: JavaScript (~20%)
   • Roff 81.4% deve desaparecer

6️⃣  SE ROFF NÃO SUMIR EM 48H
   git commit --allow-empty -m "chore: Force GitHub Linguist recalculation"
   git push origin main

⚠️  IMPORTANTE:
   • .env files estão em .gitignore (não serão enviados)
   • Recrie .env no servidor de produção manualmente
   • Nunca commite credenciais (API keys, tokens, senhas)

📚 DOCUMENTAÇÃO:
   • .env.example contém template de variáveis
   • README.md contém instruções de setup
   • QUICK_START.md para iniciar rapidamente

"@

Write-Host "`n✨ Projeto limpo e pronto para GitHub!" -ForegroundColor Green
Write-Host "=" * 70 -ForegroundColor Cyan
Write-Host ""
