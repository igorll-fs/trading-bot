# =============================================================================
# Script de Backup do MongoDB - Trading Bot
# =============================================================================
# 
# USO:
#   .\backup_mongodb.ps1                    # Backup completo
#   .\backup_mongodb.ps1 -Collections trades,configs  # Apenas colecoes especificas
#   .\backup_mongodb.ps1 -KeepDays 30       # Manter backups dos ultimos 30 dias
#
# REQUISITOS:
#   - MongoDB Tools instalado (mongodump)
#   - MongoDB rodando localmente
#
# =============================================================================

param(
    [string]$BackupDir = "$PSScriptRoot\..\backups\mongodb",
    [string]$MongoHost = "localhost",
    [int]$MongoPort = 27017,
    [string]$Database = "trading_bot",
    [string[]]$Collections = @(),
    [int]$KeepDays = 7,
    [switch]$Compress = $true
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
Write-Host "  MongoDB Backup - Trading Bot" -ForegroundColor Blue
Write-Host "========================================" -ForegroundColor Blue
Write-Host ""

# Verificar se mongodump existe
$mongodump = Get-Command mongodump -ErrorAction SilentlyContinue
if (-not $mongodump) {
    Write-Err "mongodump nao encontrado. Instale MongoDB Tools:"
    Write-Host "  https://www.mongodb.com/try/download/database-tools" -ForegroundColor Gray
    exit 1
}

Write-Info "Usando mongodump: $($mongodump.Source)"

# Criar diretorio de backup
$timestamp = Get-Date -Format "yyyy-MM-dd_HH-mm-ss"
$backupPath = Join-Path $BackupDir $timestamp

if (-not (Test-Path $BackupDir)) {
    New-Item -ItemType Directory -Path $BackupDir -Force | Out-Null
    Write-Info "Diretorio de backups criado: $BackupDir"
}

# Construir comando mongodump
$dumpArgs = @(
    "--host=$MongoHost",
    "--port=$MongoPort",
    "--db=$Database",
    "--out=$backupPath"
)

# Adicionar colecoes especificas se fornecidas
if ($Collections.Count -gt 0) {
    foreach ($col in $Collections) {
        $dumpArgs += "--collection=$col"
    }
    Write-Info "Backup de colecoes: $($Collections -join ', ')"
} else {
    Write-Info "Backup completo do banco: $Database"
}

# Executar backup
Write-Info "Iniciando backup..."
Write-Host ""

try {
    & mongodump @dumpArgs
    
    if ($LASTEXITCODE -ne 0) {
        throw "mongodump retornou codigo de erro: $LASTEXITCODE"
    }
    
    Write-Success "Backup concluido: $backupPath"
    
    # Comprimir se solicitado
    if ($Compress) {
        Write-Info "Comprimindo backup..."
        $zipPath = "$backupPath.zip"
        
        Compress-Archive -Path $backupPath -DestinationPath $zipPath -Force
        
        # Remover diretorio nao comprimido
        Remove-Item -Path $backupPath -Recurse -Force
        
        $zipSize = (Get-Item $zipPath).Length / 1MB
        Write-Success "Backup comprimido: $zipPath ($([math]::Round($zipSize, 2)) MB)"
    }
    
    # Limpar backups antigos
    Write-Info "Limpando backups com mais de $KeepDays dias..."
    
    $cutoffDate = (Get-Date).AddDays(-$KeepDays)
    $oldBackups = Get-ChildItem $BackupDir -File | Where-Object { $_.LastWriteTime -lt $cutoffDate }
    
    if ($oldBackups.Count -gt 0) {
        foreach ($old in $oldBackups) {
            Remove-Item $old.FullName -Force
            Write-Warn "Removido backup antigo: $($old.Name)"
        }
    } else {
        Write-Info "Nenhum backup antigo para remover"
    }
    
    # Listar backups existentes
    Write-Host ""
    Write-Info "Backups disponiveis:"
    Get-ChildItem $BackupDir -File | Sort-Object LastWriteTime -Descending | ForEach-Object {
        $size = $_.Length / 1MB
        Write-Host "  $($_.Name) - $([math]::Round($size, 2)) MB" -ForegroundColor Gray
    }
    
} catch {
    Write-Err "Falha no backup: $_"
    exit 1
}

Write-Host ""
Write-Success "Backup completo!"
Write-Host ""
