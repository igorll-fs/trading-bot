# =============================================================================
# Script para Acesso Remoto ao Trading Bot Dashboard
# Permite acessar de qualquer rede/Wi-Fi
# =============================================================================

param(
    [ValidateSet("ngrok", "cloudflare", "info")]
    [string]$Method = "info"
)

$ErrorActionPreference = "Continue"

function Write-Title { param($msg) Write-Host "`n$msg" -ForegroundColor Cyan }
function Write-Success { param($msg) Write-Host "[OK] $msg" -ForegroundColor Green }
function Write-Info { param($msg) Write-Host "[i] $msg" -ForegroundColor Yellow }
function Write-Err { param($msg) Write-Host "[X] $msg" -ForegroundColor Red }

$BackendPort = 8002
$FrontendPort = 3000

Write-Host ""
Write-Host "========================================" -ForegroundColor Magenta
Write-Host "  Trading Bot - Remote Access Setup" -ForegroundColor Magenta  
Write-Host "========================================" -ForegroundColor Magenta

if ($Method -eq "info") {
    Write-Title "OPCOES PARA ACESSO REMOTO (qualquer rede)"
    
    Write-Host ""
    Write-Host "1. NGROK (Recomendado - Facil e Rapido)" -ForegroundColor Green
    Write-Host "   - Cria URL publica temporaria (ex: https://abc123.ngrok.io)"
    Write-Host "   - Gratuito com limite de 1 tunel"
    Write-Host "   - Download: https://ngrok.com/download"
    Write-Host "   - Comando: .\setup_remote_access.ps1 -Method ngrok"
    
    Write-Host ""
    Write-Host "2. CLOUDFLARE TUNNEL (Mais Seguro)" -ForegroundColor Blue
    Write-Host "   - URL permanente com seu dominio"
    Write-Host "   - Gratuito, requer conta Cloudflare"
    Write-Host "   - Download: https://developers.cloudflare.com/cloudflare-one/connections/connect-apps/install-and-setup/tunnel-guide/"
    
    Write-Host ""
    Write-Host "3. PORT FORWARDING (Avancado)" -ForegroundColor Yellow
    Write-Host "   - Configurar no roteador"
    Write-Host "   - Expoe diretamente na internet"
    Write-Host "   - Precisa IP fixo ou servico DDNS"
    Write-Host "   - Menos seguro"
    
    Write-Host ""
    Write-Host "4. TAILSCALE/ZEROTIER (VPN Pessoal)" -ForegroundColor Cyan
    Write-Host "   - Cria rede privada entre seus dispositivos"
    Write-Host "   - Muito seguro"
    Write-Host "   - Precisa instalar app no celular tambem"
    Write-Host "   - https://tailscale.com ou https://zerotier.com"
    
    Write-Host ""
    Write-Host "========================================" -ForegroundColor Magenta
    Write-Host ""
    exit 0
}

if ($Method -eq "ngrok") {
    Write-Title "Configurando NGROK..."
    
    # Verificar se ngrok existe
    $ngrokPath = $null
    $possiblePaths = @(
        "ngrok",
        "$env:USERPROFILE\ngrok.exe",
        "$env:USERPROFILE\Downloads\ngrok.exe",
        "C:\ngrok\ngrok.exe",
        "$env:LOCALAPPDATA\ngrok\ngrok.exe"
    )
    
    foreach ($path in $possiblePaths) {
        if (Get-Command $path -ErrorAction SilentlyContinue) {
            $ngrokPath = $path
            break
        }
        if (Test-Path $path) {
            $ngrokPath = $path
            break
        }
    }
    
    if (-not $ngrokPath) {
        Write-Err "Ngrok nao encontrado!"
        Write-Host ""
        Write-Info "Para instalar o Ngrok:"
        Write-Host "  1. Acesse: https://ngrok.com/download" -ForegroundColor White
        Write-Host "  2. Baixe a versao Windows (ZIP)" -ForegroundColor White
        Write-Host "  3. Extraia ngrok.exe para: $env:USERPROFILE" -ForegroundColor White
        Write-Host "  4. Crie conta gratuita em: https://dashboard.ngrok.com/signup" -ForegroundColor White
        Write-Host "  5. Copie seu authtoken de: https://dashboard.ngrok.com/get-started/your-authtoken" -ForegroundColor White
        Write-Host "  6. Execute: ngrok config add-authtoken SEU_TOKEN" -ForegroundColor White
        Write-Host "  7. Execute este script novamente" -ForegroundColor White
        Write-Host ""
        exit 1
    }
    
    Write-Success "Ngrok encontrado: $ngrokPath"
    
    # Criar arquivo de configuracao ngrok
    $ngrokConfig = @"
version: "2"
tunnels:
  frontend:
    addr: $FrontendPort
    proto: http
    inspect: false
  backend:
    addr: $BackendPort
    proto: http
    inspect: false
"@
    
    $configPath = "$env:USERPROFILE\.ngrok-trading-bot.yml"
    $ngrokConfig | Out-File -FilePath $configPath -Encoding UTF8
    Write-Success "Configuracao criada: $configPath"
    
    Write-Host ""
    Write-Info "Iniciando tuneis ngrok..."
    Write-Host ""
    Write-Host "  Para iniciar APENAS o frontend (1 tunel gratuito):" -ForegroundColor Yellow
    Write-Host "    $ngrokPath http $FrontendPort" -ForegroundColor White
    Write-Host ""
    Write-Host "  Para iniciar frontend + backend (requer ngrok pago):" -ForegroundColor Yellow
    Write-Host "    $ngrokPath start --all --config `"$configPath`"" -ForegroundColor White
    Write-Host ""
    
    # Iniciar apenas frontend
    Write-Info "Iniciando tunel para o Dashboard (porta $FrontendPort)..."
    Write-Host ""
    Write-Host "Pressione Ctrl+C para encerrar o tunel" -ForegroundColor Red
    Write-Host ""
    
    & $ngrokPath http $FrontendPort
}

if ($Method -eq "cloudflare") {
    Write-Title "Configurando CLOUDFLARE TUNNEL..."
    
    $cloudflaredPath = $null
    $possiblePaths = @(
        "cloudflared",
        "$env:USERPROFILE\cloudflared.exe",
        "$env:USERPROFILE\Downloads\cloudflared.exe",
        "C:\cloudflared\cloudflared.exe"
    )
    
    foreach ($path in $possiblePaths) {
        if (Get-Command $path -ErrorAction SilentlyContinue) {
            $cloudflaredPath = $path
            break
        }
        if (Test-Path $path) {
            $cloudflaredPath = $path
            break
        }
    }
    
    if (-not $cloudflaredPath) {
        Write-Err "Cloudflared nao encontrado!"
        Write-Host ""
        Write-Info "Para instalar:"
        Write-Host "  1. Acesse: https://developers.cloudflare.com/cloudflare-one/connections/connect-apps/install-and-setup/installation/" -ForegroundColor White
        Write-Host "  2. Baixe cloudflared para Windows" -ForegroundColor White
        Write-Host "  3. Extraia para: $env:USERPROFILE" -ForegroundColor White
        Write-Host ""
        exit 1
    }
    
    Write-Success "Cloudflared encontrado: $cloudflaredPath"
    Write-Host ""
    Write-Info "Iniciando tunel rapido (sem autenticacao)..."
    Write-Host ""
    
    & $cloudflaredPath tunnel --url http://localhost:$FrontendPort
}

Write-Host ""
