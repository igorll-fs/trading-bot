<#
.SYNOPSIS
    Inicia o Trading Bot com acesso mobile via Cloudflare Tunnel
.DESCRIPTION
    Este script:
    1. Verifica se backend e frontend estao rodando
    2. Cria tuneis Cloudflare para ambos
    3. Gera URLs e instrucoes para acesso mobile
.EXAMPLE
    .\start_remote_access.ps1
#>

$ErrorActionPreference = "SilentlyContinue"
$BackendPort = 8000
$FrontendPort = 3000
$CloudflaredPath = "C:\Users\igor\cloudflared.exe"

Write-Host ""
Write-Host "================================================================" -ForegroundColor Magenta
Write-Host "   TRADING BOT - ACESSO REMOTO (PC + CELULAR)" -ForegroundColor Magenta
Write-Host "================================================================" -ForegroundColor Magenta
Write-Host ""

# Verificar cloudflared
if (-not (Test-Path $CloudflaredPath)) {
    Write-Host "[ERRO] cloudflared nao encontrado em $CloudflaredPath" -ForegroundColor Red
    exit 1
}

# Verificar servicos
$backendOnline = Test-NetConnection -ComputerName localhost -Port $BackendPort -InformationLevel Quiet -WarningAction SilentlyContinue
$frontendOnline = Test-NetConnection -ComputerName localhost -Port $FrontendPort -InformationLevel Quiet -WarningAction SilentlyContinue

Write-Host "Status dos Servicos:" -ForegroundColor Yellow
Write-Host "   Backend (porta $BackendPort):  $(if($backendOnline){'[OK] ONLINE'}else{'[X] OFFLINE'})" -ForegroundColor $(if($backendOnline){'Green'}else{'Red'})
Write-Host "   Frontend (porta $FrontendPort): $(if($frontendOnline){'[OK] ONLINE'}else{'[X] OFFLINE'})" -ForegroundColor $(if($frontendOnline){'Green'}else{'Red'})

if (-not $backendOnline -or -not $frontendOnline) {
    Write-Host ""
    Write-Host "[ERRO] Backend e Frontend precisam estar rodando!" -ForegroundColor Red
    Write-Host "   Execute: .\scripts\start.bat" -ForegroundColor Cyan
    exit 1
}

Write-Host ""
Write-Host "Iniciando tuneis Cloudflare..." -ForegroundColor Cyan
Write-Host "(Isso pode demorar alguns segundos)" -ForegroundColor Gray
Write-Host ""

# Arquivo temporario para capturar URLs
$backendUrlFile = "$env:TEMP\cf_backend_url.txt"
$frontendUrlFile = "$env:TEMP\cf_frontend_url.txt"

# Limpar arquivos anteriores
Remove-Item $backendUrlFile -Force -ErrorAction SilentlyContinue
Remove-Item $frontendUrlFile -Force -ErrorAction SilentlyContinue

# Iniciar tunel do backend em background
$backendJob = Start-Job -ScriptBlock {
    param($CloudflaredPath, $BackendPort, $OutputFile)
    
    $process = Start-Process -FilePath $CloudflaredPath -ArgumentList "tunnel", "--url", "http://localhost:$BackendPort" -RedirectStandardError "$env:TEMP\cf_backend_stderr.txt" -NoNewWindow -PassThru
    
    # Aguardar e capturar URL
    Start-Sleep -Seconds 8
    $stderr = Get-Content "$env:TEMP\cf_backend_stderr.txt" -Raw
    if ($stderr -match "https://[a-z0-9-]+\.trycloudflare\.com") {
        $Matches[0] | Out-File $OutputFile -Force
    }
    
    # Manter processo rodando
    Wait-Process -Id $process.Id
} -ArgumentList $CloudflaredPath, $BackendPort, $backendUrlFile

# Iniciar tunel do frontend em background
$frontendJob = Start-Job -ScriptBlock {
    param($CloudflaredPath, $FrontendPort, $OutputFile)
    
    $process = Start-Process -FilePath $CloudflaredPath -ArgumentList "tunnel", "--url", "http://localhost:$FrontendPort" -RedirectStandardError "$env:TEMP\cf_frontend_stderr.txt" -NoNewWindow -PassThru
    
    # Aguardar e capturar URL
    Start-Sleep -Seconds 8
    $stderr = Get-Content "$env:TEMP\cf_frontend_stderr.txt" -Raw
    if ($stderr -match "https://[a-z0-9-]+\.trycloudflare\.com") {
        $Matches[0] | Out-File $OutputFile -Force
    }
    
    # Manter processo rodando
    Wait-Process -Id $process.Id
} -ArgumentList $CloudflaredPath, $FrontendPort, $frontendUrlFile

Write-Host "Aguardando tuneis serem criados..." -ForegroundColor Yellow

# Aguardar URLs serem geradas
$maxWait = 20
$waited = 0
while ($waited -lt $maxWait) {
    Start-Sleep -Seconds 2
    $waited += 2
    
    $backendUrl = if (Test-Path $backendUrlFile) { (Get-Content $backendUrlFile -Raw).Trim() } else { $null }
    $frontendUrl = if (Test-Path $frontendUrlFile) { (Get-Content $frontendUrlFile -Raw).Trim() } else { $null }
    
    if ($backendUrl -and $frontendUrl) {
        break
    }
    
    Write-Host "   Aguardando... ($waited/$maxWait segundos)" -ForegroundColor Gray
}

# Verificar se obteve as URLs
$backendUrl = if (Test-Path $backendUrlFile) { (Get-Content $backendUrlFile -Raw).Trim() } else { $null }
$frontendUrl = if (Test-Path $frontendUrlFile) { (Get-Content $frontendUrlFile -Raw).Trim() } else { $null }

if (-not $backendUrl -or -not $frontendUrl) {
    Write-Host ""
    Write-Host "[ERRO] Nao foi possivel obter as URLs dos tuneis" -ForegroundColor Red
    Write-Host "   Verifique se cloudflared esta funcionando corretamente" -ForegroundColor Yellow
    exit 1
}

# Exibir resultado
Write-Host ""
Write-Host "================================================================" -ForegroundColor Green
Write-Host "   TUNEIS CRIADOS COM SUCESSO!" -ForegroundColor Green
Write-Host "================================================================" -ForegroundColor Green
Write-Host ""
Write-Host "URLs de Acesso:" -ForegroundColor Yellow
Write-Host ""
Write-Host "   DASHBOARD (Frontend):" -ForegroundColor Cyan
Write-Host "   $frontendUrl" -ForegroundColor White
Write-Host ""
Write-Host "   API (Backend):" -ForegroundColor Cyan
Write-Host "   $backendUrl" -ForegroundColor White
Write-Host ""
Write-Host "================================================================" -ForegroundColor DarkGray
Write-Host ""
Write-Host "COMO ACESSAR NO CELULAR:" -ForegroundColor Yellow
Write-Host ""
Write-Host "   1. Abra o navegador no celular" -ForegroundColor White
Write-Host ""
Write-Host "   2. Acesse: $frontendUrl" -ForegroundColor Green
Write-Host ""
Write-Host "   3. Quando pedir URL do Backend, cole:" -ForegroundColor White
Write-Host "      $backendUrl" -ForegroundColor Cyan
Write-Host ""
Write-Host "   4. Clique em 'Conectar' - Pronto!" -ForegroundColor White
Write-Host ""
Write-Host "================================================================" -ForegroundColor DarkGray
Write-Host ""
Write-Host "IMPORTANTE:" -ForegroundColor Yellow
Write-Host "   - E o MESMO bot rodando no PC" -ForegroundColor White
Write-Host "   - PC e celular veem os MESMOS dados" -ForegroundColor White
Write-Host "   - Mantenha esta janela ABERTA para manter os tuneis ativos" -ForegroundColor White
Write-Host ""
Write-Host "Pressione Ctrl+C para encerrar os tuneis..." -ForegroundColor Gray

# Salvar URLs em arquivo para referencia
$urlsFile = ".\mobile_access_urls.txt"
@"
=== TRADING BOT - URLs de Acesso Remoto ===
Gerado em: $(Get-Date -Format "yyyy-MM-dd HH:mm:ss")

DASHBOARD (abra no celular):
$frontendUrl

BACKEND (cole quando pedir):
$backendUrl

IMPORTANTE: URLs mudam cada vez que reiniciar os tuneis!
"@ | Out-File $urlsFile -Force

Write-Host ""
Write-Host "URLs salvas em: $urlsFile" -ForegroundColor Gray

# Manter script rodando
try {
    while ($true) {
        Start-Sleep -Seconds 60
        
        # Verificar se jobs ainda estao rodando
        $backendRunning = (Get-Job -Id $backendJob.Id).State -eq "Running"
        $frontendRunning = (Get-Job -Id $frontendJob.Id).State -eq "Running"
        
        if (-not $backendRunning -or -not $frontendRunning) {
            Write-Host ""
            Write-Host "[AVISO] Um dos tuneis foi encerrado" -ForegroundColor Yellow
            break
        }
    }
} finally {
    # Cleanup
    Write-Host ""
    Write-Host "Encerrando tuneis..." -ForegroundColor Yellow
    Stop-Job -Job $backendJob -ErrorAction SilentlyContinue
    Stop-Job -Job $frontendJob -ErrorAction SilentlyContinue
    Remove-Job -Job $backendJob -Force -ErrorAction SilentlyContinue
    Remove-Job -Job $frontendJob -Force -ErrorAction SilentlyContinue
    
    # Matar processos cloudflared
    Get-Process -Name "cloudflared" -ErrorAction SilentlyContinue | Stop-Process -Force
    
    Write-Host "[OK] Tuneis encerrados" -ForegroundColor Green
}
