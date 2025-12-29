# Script para manter Frontend rodando de forma robusta
# Reinicia automaticamente se cair
param(
    [int]$MaxRetries = 999,
    [int]$RetryDelay = 5
)

$ProjectRoot = Split-Path -Parent $PSScriptRoot
$FrontendPath = Join-Path $ProjectRoot "frontend"
$RetryCount = 0

Write-Host "========================================" -ForegroundColor Cyan
Write-Host " Frontend Auto-Recovery System" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Modo: Reinício automático ativado" -ForegroundColor Green
Write-Host "Tentativas máximas: $MaxRetries" -ForegroundColor Yellow
Write-Host "Delay entre tentativas: $RetryDelay segundos" -ForegroundColor Yellow
Write-Host ""
Write-Host "Pressione Ctrl+C para parar" -ForegroundColor Red
Write-Host ""

while ($RetryCount -lt $MaxRetries) {
    $RetryCount++
    
    Write-Host "[$RetryCount/$MaxRetries] Iniciando frontend..." -ForegroundColor Cyan
    
    try {
        # Limpar porta 3000 se estiver ocupada
        $ProcessOnPort = Get-NetTCPConnection -LocalPort 3000 -ErrorAction SilentlyContinue | 
            Select-Object -ExpandProperty OwningProcess -Unique
        
        if ($ProcessOnPort) {
            Write-Host "Limpando processo antigo na porta 3000 (PID: $ProcessOnPort)..." -ForegroundColor Yellow
            Stop-Process -Id $ProcessOnPort -Force -ErrorAction SilentlyContinue
            Start-Sleep -Seconds 2
        }
        
        # Iniciar yarn start
        Push-Location $FrontendPath
        
        $Process = Start-Process -FilePath "yarn" -ArgumentList "start" -PassThru -NoNewWindow
        
        Write-Host "Frontend iniciado! (PID: $($Process.Id))" -ForegroundColor Green
        Write-Host "Aguardando até que o processo termine..." -ForegroundColor Gray
        Write-Host ""
        
        # Aguardar o processo terminar
        $Process.WaitForExit()
        
        Pop-Location
        
        Write-Host ""
        Write-Host "Frontend parou! (Exit Code: $($Process.ExitCode))" -ForegroundColor Yellow
        
        if ($RetryCount -lt $MaxRetries) {
            Write-Host "Reiniciando em $RetryDelay segundos..." -ForegroundColor Cyan
            Start-Sleep -Seconds $RetryDelay
        }
        
    } catch {
        Write-Host "Erro ao iniciar frontend: $_" -ForegroundColor Red
        
        if ($RetryCount -lt $MaxRetries) {
            Write-Host "Tentando novamente em $RetryDelay segundos..." -ForegroundColor Yellow
            Start-Sleep -Seconds $RetryDelay
        }
    }
}

Write-Host ""
Write-Host "Limite de tentativas atingido. Finalizando..." -ForegroundColor Red
Pop-Location -ErrorAction SilentlyContinue
