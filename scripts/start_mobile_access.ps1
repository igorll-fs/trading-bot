<# 
.SYNOPSIS
    Configura acesso mobile ao Trading Bot Dashboard
.DESCRIPTION
    Oferece 3 opcoes para acessar o dashboard pelo celular:
    1. Cloudflare Tunnel (qualquer rede - recomendado)
    2. Rede Local (mesma WiFi)
    3. Ngrok (alternativa)
.EXAMPLE
    .\start_mobile_access.ps1 -Option cloudflare
    .\start_mobile_access.ps1 -Option local
#>

param(
    [ValidateSet("cloudflare", "local", "ngrok", "status")]
    [string]$Option = "status"
)

$ErrorActionPreference = "SilentlyContinue"
$BackendPort = 8000
$FrontendPort = 3000

# Obter IP local
$localIP = (ipconfig | Select-String -Pattern "IPv4" | Select-Object -First 1).ToString().Split(":")[-1].Trim()

Write-Host ""
Write-Host "================================================================" -ForegroundColor Magenta
Write-Host "       TRADING BOT - ACESSO MOBILE AO DASHBOARD" -ForegroundColor Magenta
Write-Host "================================================================" -ForegroundColor Magenta
Write-Host ""
Write-Host "[INFO] Seu IP Local: $localIP" -ForegroundColor Cyan

# Verificar servicos
$backendOnline = Test-NetConnection -ComputerName localhost -Port $BackendPort -InformationLevel Quiet -WarningAction SilentlyContinue
$frontendOnline = Test-NetConnection -ComputerName localhost -Port $FrontendPort -InformationLevel Quiet -WarningAction SilentlyContinue

Write-Host ""
Write-Host "Status dos Servicos:" -ForegroundColor Yellow
Write-Host "   Backend (porta $BackendPort):  $(if($backendOnline){'[OK] ONLINE'}else{'[X] OFFLINE'})" -ForegroundColor $(if($backendOnline){'Green'}else{'Red'})
Write-Host "   Frontend (porta $FrontendPort): $(if($frontendOnline){'[OK] ONLINE'}else{'[X] OFFLINE'})" -ForegroundColor $(if($frontendOnline){'Green'}else{'Red'})

if (-not $backendOnline -or -not $frontendOnline) {
    Write-Host ""
    Write-Host "[ERRO] Servicos nao estao rodando! Inicie primeiro." -ForegroundColor Red
    if ($Option -ne "status") { exit 1 }
}

switch ($Option) {
    "status" {
        Write-Host ""
        Write-Host "================================================================" -ForegroundColor DarkGray
        Write-Host "  OPCOES DE ACESSO MOBILE" -ForegroundColor DarkGray
        Write-Host "================================================================" -ForegroundColor DarkGray
        
        Write-Host ""
        Write-Host "[1] CLOUDFLARE TUNNEL (Qualquer Rede - RECOMENDADO)" -ForegroundColor Green
        Write-Host "    + Acesso de qualquer lugar (4G, WiFi diferente, etc.)"
        Write-Host "    + HTTPS automatico (conexao segura)"
        Write-Host "    + Nao precisa configurar roteador/firewall"
        Write-Host "    + 100% GRATIS"
        Write-Host "    Comando: .\scripts\start_mobile_access.ps1 -Option cloudflare" -ForegroundColor Cyan
        
        Write-Host ""
        Write-Host "[2] REDE LOCAL (Mesma WiFi)" -ForegroundColor Cyan
        Write-Host "    + Configuracao simples e rapida"
        Write-Host "    + Baixa latencia"
        Write-Host "    - Funciona APENAS na mesma rede WiFi"
        Write-Host "    Comando: .\scripts\start_mobile_access.ps1 -Option local" -ForegroundColor Cyan
        
        Write-Host ""
        Write-Host "[3] NGROK (Alternativa ao Cloudflare)" -ForegroundColor Yellow
        Write-Host "    + Similar ao Cloudflare Tunnel"
        Write-Host "    - Requer criar conta gratuita em ngrok.com"
        Write-Host "    Comando: .\scripts\start_mobile_access.ps1 -Option ngrok" -ForegroundColor Cyan
        
        Write-Host ""
        Write-Host "================================================================" -ForegroundColor DarkGray
        Write-Host ""
    }
    
    "cloudflare" {
        Write-Host ""
        Write-Host "[CLOUDFLARE TUNNEL] Acesso de Qualquer Rede" -ForegroundColor Magenta
        Write-Host ""
        
        $cfInstalled = Get-Command cloudflared -ErrorAction SilentlyContinue
        
        if (-not $cfInstalled) {
            Write-Host "[AVISO] cloudflared nao esta instalado!" -ForegroundColor Yellow
            Write-Host ""
            Write-Host "Instale de uma das formas:" -ForegroundColor Yellow
            Write-Host ""
            Write-Host "   OPCAO A - Download direto:" -ForegroundColor White
            Write-Host "   https://github.com/cloudflare/cloudflared/releases/latest" -ForegroundColor Cyan
            Write-Host "   Baixe: cloudflared-windows-amd64.exe" -ForegroundColor Gray
            Write-Host "   Renomeie para: cloudflared.exe" -ForegroundColor Gray
            Write-Host "   Mova para: C:\Windows\System32\" -ForegroundColor Gray
            Write-Host ""
            Write-Host "   OPCAO B - Via Winget:" -ForegroundColor White
            Write-Host "   winget install Cloudflare.cloudflared" -ForegroundColor Cyan
            Write-Host ""
            
            $download = Read-Host "Deseja abrir a pagina de download? (S/N)"
            if ($download -eq "S" -or $download -eq "s") {
                Start-Process "https://github.com/cloudflare/cloudflared/releases/latest"
            }
            exit 1
        }
        
        Write-Host "[OK] cloudflared encontrado!" -ForegroundColor Green
        Write-Host ""
        Write-Host "INSTRUCOES:" -ForegroundColor Yellow
        Write-Host ""
        Write-Host "   1. Abra DOIS terminais PowerShell" -ForegroundColor White
        Write-Host ""
        Write-Host "   2. No PRIMEIRO terminal (Backend):" -ForegroundColor White
        Write-Host "       cloudflared tunnel --url http://localhost:$BackendPort" -ForegroundColor Cyan
        Write-Host "       -> Copie a URL (ex: https://abc-123.trycloudflare.com)" -ForegroundColor Gray
        Write-Host ""
        Write-Host "   3. No SEGUNDO terminal (Frontend):" -ForegroundColor White
        Write-Host "       cloudflared tunnel --url http://localhost:$FrontendPort" -ForegroundColor Cyan
        Write-Host "       -> Copie a URL (ex: https://xyz-456.trycloudflare.com)" -ForegroundColor Gray
        Write-Host ""
        Write-Host "   4. NO CELULAR:" -ForegroundColor White
        Write-Host "       -> Acesse a URL do FRONTEND no navegador" -ForegroundColor Gray
        Write-Host "       -> Quando pedir, cole a URL do BACKEND" -ForegroundColor Gray
        Write-Host ""
        
        $startNow = Read-Host "Iniciar tunel do Backend agora? (S/N)"
        if ($startNow -eq "S" -or $startNow -eq "s") {
            Write-Host "[INFO] Iniciando tunel do Backend..." -ForegroundColor Cyan
            Write-Host "   (Abra outro terminal e execute o mesmo para o Frontend)" -ForegroundColor Gray
            Write-Host ""
            cloudflared tunnel --url http://localhost:$BackendPort
        }
    }
    
    "local" {
        Write-Host ""
        Write-Host "[REDE LOCAL] Acesso pela mesma WiFi" -ForegroundColor Magenta
        Write-Host ""
        
        Write-Host "URLs para acessar no celular:" -ForegroundColor Yellow
        Write-Host ""
        Write-Host "   Dashboard: http://${localIP}:${FrontendPort}" -ForegroundColor Green
        Write-Host "   API:       http://${localIP}:${BackendPort}/api" -ForegroundColor Cyan
        Write-Host ""
        
        Write-Host "[INFO] Verificando firewall..." -ForegroundColor Cyan
        
        $isAdmin = ([Security.Principal.WindowsPrincipal] [Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
        
        if (-not $isAdmin) {
            Write-Host "[AVISO] Para liberar o firewall, execute como Administrador!" -ForegroundColor Yellow
            Write-Host ""
            Write-Host "   Comandos para liberar (execute como Admin):" -ForegroundColor Yellow
            Write-Host "   netsh advfirewall firewall add rule name=`"TradingBot-Backend`" dir=in action=allow protocol=tcp localport=$BackendPort" -ForegroundColor Cyan
            Write-Host "   netsh advfirewall firewall add rule name=`"TradingBot-Frontend`" dir=in action=allow protocol=tcp localport=$FrontendPort" -ForegroundColor Cyan
            Write-Host ""
        } else {
            Write-Host "   Liberando porta $BackendPort..." -NoNewline
            netsh advfirewall firewall delete rule name="TradingBot-Backend" 2>&1 | Out-Null
            netsh advfirewall firewall add rule name="TradingBot-Backend" dir=in action=allow protocol=tcp localport=$BackendPort | Out-Null
            Write-Host " [OK]" -ForegroundColor Green
            
            Write-Host "   Liberando porta $FrontendPort..." -NoNewline
            netsh advfirewall firewall delete rule name="TradingBot-Frontend" 2>&1 | Out-Null
            netsh advfirewall firewall add rule name="TradingBot-Frontend" dir=in action=allow protocol=tcp localport=$FrontendPort | Out-Null
            Write-Host " [OK]" -ForegroundColor Green
            
            Write-Host ""
            Write-Host "[OK] Firewall configurado!" -ForegroundColor Green
        }
        
        Write-Host ""
        Write-Host "================================================================" -ForegroundColor DarkGray
        Write-Host ""
        Write-Host "   Abra no navegador do celular:" -ForegroundColor Yellow
        Write-Host ""
        Write-Host "      http://${localIP}:${FrontendPort}" -ForegroundColor Green
        Write-Host ""
        Write-Host "   IMPORTANTE: O celular deve estar na MESMA WiFi!" -ForegroundColor Yellow
        Write-Host ""
    }
    
    "ngrok" {
        Write-Host ""
        Write-Host "[NGROK] Acesso de Qualquer Rede" -ForegroundColor Magenta
        Write-Host ""
        
        $ngrokInstalled = Get-Command ngrok -ErrorAction SilentlyContinue
        
        if (-not $ngrokInstalled) {
            Write-Host "[AVISO] ngrok nao esta instalado!" -ForegroundColor Yellow
            Write-Host ""
            Write-Host "Instalacao:" -ForegroundColor Yellow
            Write-Host "   1. Acesse: https://ngrok.com/download" -ForegroundColor Cyan
            Write-Host "   2. Crie uma conta gratuita" -ForegroundColor Gray
            Write-Host "   3. Baixe e instale o ngrok" -ForegroundColor Gray
            Write-Host "   4. Configure seu authtoken:" -ForegroundColor Gray
            Write-Host "      ngrok config add-authtoken SEU_TOKEN" -ForegroundColor Cyan
            Write-Host ""
            
            $download = Read-Host "Deseja abrir a pagina de download? (S/N)"
            if ($download -eq "S" -or $download -eq "s") {
                Start-Process "https://ngrok.com/download"
            }
            exit 1
        }
        
        Write-Host "[OK] ngrok encontrado!" -ForegroundColor Green
        Write-Host ""
        Write-Host "INSTRUCOES:" -ForegroundColor Yellow
        Write-Host ""
        Write-Host "   1. Abra DOIS terminais" -ForegroundColor White
        Write-Host ""
        Write-Host "   2. Terminal 1 (Backend):" -ForegroundColor White
        Write-Host "       ngrok http $BackendPort" -ForegroundColor Cyan
        Write-Host ""
        Write-Host "   3. Terminal 2 (Frontend):" -ForegroundColor White
        Write-Host "       ngrok http $FrontendPort" -ForegroundColor Cyan
        Write-Host ""
        Write-Host "   4. Use as URLs Forwarding no celular" -ForegroundColor White
        Write-Host ""
    }
}

Write-Host ""
