# =============================================================================
# Script para configurar acesso mobile ao Trading Bot Dashboard
# Execute como Administrador!
# =============================================================================

param(
    [switch]$Remove,
    [switch]$Status
)

$ErrorActionPreference = "Stop"

# Configurações
$BackendPort = 8002
$FrontendPort = 3000
$MongoPort = 27017

# Cores
function Write-Success { param($msg) Write-Host "✅ $msg" -ForegroundColor Green }
function Write-Info { param($msg) Write-Host "ℹ️  $msg" -ForegroundColor Cyan }
function Write-Warn { param($msg) Write-Host "⚠️  $msg" -ForegroundColor Yellow }
function Write-Err { param($msg) Write-Host "❌ $msg" -ForegroundColor Red }

# Verificar se é admin
$isAdmin = ([Security.Principal.WindowsPrincipal] [Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)

if (-not $isAdmin) {
    Write-Err "Este script precisa ser executado como Administrador!"
    Write-Info "Clique com botão direito no PowerShell e selecione 'Executar como administrador'"
    exit 1
}

# Obter IP local
$localIP = (Get-NetIPAddress -AddressFamily IPv4 | Where-Object { 
    $_.InterfaceAlias -notlike "*Loopback*" -and 
    $_.IPAddress -notlike "169.*" -and
    $_.IPAddress -notlike "127.*"
} | Select-Object -First 1).IPAddress

Write-Host ""
Write-Host "========================================" -ForegroundColor Magenta
Write-Host "  Trading Bot - Mobile Access Setup" -ForegroundColor Magenta
Write-Host "========================================" -ForegroundColor Magenta
Write-Host ""
Write-Info "IP Local: $localIP"
Write-Host ""

if ($Status) {
    Write-Host "📋 Status das regras de firewall:" -ForegroundColor Yellow
    Write-Host ""
    
    $rules = @(
        "Trading Bot Backend (TCP $BackendPort)",
        "Trading Bot Frontend (TCP $FrontendPort)",
        "MongoDB (TCP $MongoPort)"
    )
    
    foreach ($rule in $rules) {
        $exists = netsh advfirewall firewall show rule name="$rule" 2>&1
        if ($exists -like "*Nenhuma regra*" -or $exists -like "*No rules*") {
            Write-Warn "$rule - NÃO CONFIGURADA"
        } else {
            Write-Success "$rule - ATIVA"
        }
    }
    
    Write-Host ""
    Write-Host "📱 URLs de acesso:" -ForegroundColor Yellow
    Write-Host "   Dashboard: http://${localIP}:${FrontendPort}" -ForegroundColor White
    Write-Host "   API:       http://${localIP}:${BackendPort}/api" -ForegroundColor White
    Write-Host ""
    exit 0
}

if ($Remove) {
    Write-Warn "Removendo regras de firewall..."
    
    netsh advfirewall firewall delete rule name="Trading Bot Backend (TCP $BackendPort)" 2>&1 | Out-Null
    netsh advfirewall firewall delete rule name="Trading Bot Frontend (TCP $FrontendPort)" 2>&1 | Out-Null
    netsh advfirewall firewall delete rule name="MongoDB (TCP $MongoPort)" 2>&1 | Out-Null
    
    Write-Success "Regras removidas!"
    exit 0
}

# Adicionar regras de firewall
Write-Info "Configurando regras de firewall..."

# Backend
Write-Host "  → Backend (porta $BackendPort)..." -NoNewline
netsh advfirewall firewall add rule name="Trading Bot Backend (TCP $BackendPort)" dir=in action=allow protocol=tcp localport=$BackendPort | Out-Null
Write-Host " OK" -ForegroundColor Green

# Frontend
Write-Host "  → Frontend (porta $FrontendPort)..." -NoNewline
netsh advfirewall firewall add rule name="Trading Bot Frontend (TCP $FrontendPort)" dir=in action=allow protocol=tcp localport=$FrontendPort | Out-Null
Write-Host " OK" -ForegroundColor Green

# MongoDB (opcional, apenas para acesso remoto ao DB)
Write-Host "  → MongoDB (porta $MongoPort)..." -NoNewline
netsh advfirewall firewall add rule name="MongoDB (TCP $MongoPort)" dir=in action=allow protocol=tcp localport=$MongoPort | Out-Null
Write-Host " OK" -ForegroundColor Green

Write-Host ""
Write-Success "Configuração concluída!"
Write-Host ""

Write-Host "========================================" -ForegroundColor Green
Write-Host "  📱 ACESSE PELO CELULAR:" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green
Write-Host ""
Write-Host "  Dashboard: " -NoNewline
Write-Host "http://${localIP}:${FrontendPort}" -ForegroundColor Cyan
Write-Host ""
Write-Host "  API:       " -NoNewline
Write-Host "http://${localIP}:${BackendPort}/api" -ForegroundColor Cyan
Write-Host ""
Write-Host "========================================" -ForegroundColor Green
Write-Host ""

Write-Info "Certifique-se de que:"
Write-Host "  1. Seu celular está na mesma rede Wi-Fi" -ForegroundColor White
Write-Host "  2. O backend está rodando (porta $BackendPort)" -ForegroundColor White
Write-Host "  3. O frontend está rodando (porta $FrontendPort)" -ForegroundColor White
Write-Host ""

# Gerar QR Code (se tiver módulo instalado)
try {
    $url = "http://${localIP}:${FrontendPort}"
    Write-Info "Escaneie o QR Code ou digite a URL no navegador do celular"
    Write-Host ""
    
    # Tentar gerar QR Code ASCII simples
    $qrUrl = "https://api.qrserver.com/v1/create-qr-code/?size=150x150&data=$url"
    Write-Host "  QR Code online: $qrUrl" -ForegroundColor Gray
} catch {
    # Ignorar se não conseguir
}

Write-Host ""
