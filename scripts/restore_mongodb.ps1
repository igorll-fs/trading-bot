# =============================================================================
# Script de Restore do MongoDB - Trading Bot
# =============================================================================
# 
# USO:
#   .\restore_mongodb.ps1 -BackupFile "2024-01-15_14-30-00.zip"
#   .\restore_mongodb.ps1 -BackupFile "2024-01-15_14-30-00.zip" -Drop
#
# CUIDADO: Use -Drop apenas se quiser substituir dados existentes!
#
# =============================================================================

param(
    [Parameter(Mandatory=$true)]
    [string]$BackupFile,
    
    [string]$BackupDir = "$PSScriptRoot\..\backups\mongodb",
    [string]$MongoHost = "localhost",
    [int]$MongoPort = 27017,
    [string]$Database = "trading_bot",
    [switch]$Drop = $false
)

$ErrorActionPreference = "Stop"

# Cores para output
function Write-Info { Write-Host "[INFO] $args" -ForegroundColor Cyan }
function Write-Success { Write-Host "[OK] $args" -ForegroundColor Green }
function Write-Warn { Write-Host "[WARN] $args" -ForegroundColor Yellow }
function Write-Err { Write-Host "[ERROR] $args" -ForegroundColor Red }

# Header
Write-Host ""
Write-Host "========================================" -ForegroundColor Blue
Write-Host "  MongoDB Restore - Trading Bot" -ForegroundColor Blue
Write-Host "========================================" -ForegroundColor Blue
Write-Host ""

# Verificar se mongorestore existe
$mongorestore = Get-Command mongorestore -ErrorAction SilentlyContinue
if (-not $mongorestore) {
    Write-Err "mongorestore nao encontrado. Instale MongoDB Tools:"
    Write-Host "  https://www.mongodb.com/try/download/database-tools" -ForegroundColor Gray
    exit 1
}

# Localizar arquivo de backup
$fullPath = $BackupFile
if (-not (Test-Path $fullPath)) {
    $fullPath = Join-Path $BackupDir $BackupFile
}

if (-not (Test-Path $fullPath)) {
    Write-Err "Arquivo de backup nao encontrado: $BackupFile"
    Write-Info "Backups disponiveis em $BackupDir :"
    Get-ChildItem $BackupDir -File | ForEach-Object { Write-Host "  $($_.Name)" -ForegroundColor Gray }
    exit 1
}

Write-Info "Arquivo de backup: $fullPath"

# Aviso de seguranca
if ($Drop) {
    Write-Warn "ATENCAO: A opcao -Drop ira SUBSTITUIR todos os dados existentes!"
    $confirm = Read-Host "Deseja continuar? (sim/nao)"
    if ($confirm -ne "sim") {
        Write-Info "Operacao cancelada."
        exit 0
    }
}

# Descomprimir se necessario
$restorePath = $fullPath
$tempDir = $null

if ($fullPath.EndsWith(".zip")) {
    Write-Info "Descomprimindo backup..."
    $tempDir = Join-Path $env:TEMP "mongodb_restore_$(Get-Date -Format 'yyyyMMddHHmmss')"
    
    Expand-Archive -Path $fullPath -DestinationPath $tempDir -Force
    
    # Encontrar diretorio do dump
    $restorePath = Get-ChildItem $tempDir -Directory | Select-Object -First 1 | ForEach-Object { $_.FullName }
    
    if (-not $restorePath) {
        $restorePath = $tempDir
    }
    
    Write-Info "Backup descomprimido em: $restorePath"
}

# Construir comando mongorestore
$restoreArgs = @(
    "--host=$MongoHost",
    "--port=$MongoPort",
    "--db=$Database",
    "--dir=$restorePath\$Database"
)

if ($Drop) {
    $restoreArgs += "--drop"
}

# Executar restore
Write-Info "Iniciando restore..."
Write-Host ""

try {
    & mongorestore @restoreArgs
    
    if ($LASTEXITCODE -ne 0) {
        throw "mongorestore retornou codigo de erro: $LASTEXITCODE"
    }
    
    Write-Success "Restore concluido com sucesso!"
    
} catch {
    Write-Err "Falha no restore: $_"
    exit 1
} finally {
    # Limpar diretorio temporario
    if ($tempDir -and (Test-Path $tempDir)) {
        Remove-Item $tempDir -Recurse -Force
        Write-Info "Diretorio temporario removido"
    }
}

Write-Host ""
Write-Success "Banco de dados restaurado!"
Write-Host ""
