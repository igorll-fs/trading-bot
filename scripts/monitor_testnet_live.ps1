# Monitor Testnet em Tempo Real
# Monitora o período de validação das correções (5-7 dias)

param(
    [int]$IntervalSeconds = 300,  # Verificar a cada 5 minutos
    [int]$Days = 7
)

$ErrorActionPreference = "SilentlyContinue"

Write-Host "`n========================================" -ForegroundColor Cyan
Write-Host "  MONITOR TESTNET - VALIDAÇÃO CORREÇÕES" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Intervalo: $IntervalSeconds segundos" -ForegroundColor Yellow
Write-Host "Período: Últimos $Days dias" -ForegroundColor Yellow
Write-Host "Pressione CTRL+C para sair`n" -ForegroundColor Gray

$iteration = 0

while ($true) {
    $iteration++
    
    # Verificar se backend está online
    $backendOnline = Test-NetConnection -ComputerName localhost -Port 8000 -InformationLevel Quiet -WarningAction SilentlyContinue
    
    if (-not $backendOnline) {
        Write-Host "`n[$(Get-Date -Format 'HH:mm:ss')] ❌ Backend OFFLINE - Verificar serviços!" -ForegroundColor Red
        Start-Sleep -Seconds $IntervalSeconds
        continue
    }
    
    # Executar script Python de monitoramento
    Push-Location "$PSScriptRoot\..\backend"
    
    Write-Host "`n" -NoNewline
    Write-Host "━" * 80 -ForegroundColor DarkGray
    Write-Host "[$(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')] Atualização #$iteration" -ForegroundColor Cyan
    Write-Host "━" * 80 -ForegroundColor DarkGray
    
    python monitor_testnet.py
    
    Pop-Location
    
    # Aguardar próxima verificação
    Write-Host "`n⏳ Próxima verificação em $IntervalSeconds segundos..." -ForegroundColor Gray
    Start-Sleep -Seconds $IntervalSeconds
}
