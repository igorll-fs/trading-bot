param(
    [int]$DurationMinutes = 120,  # 2 horas padrão
    [int]$IntervalSeconds = 30     # Verificar a cada 30s
)

$startTime = Get-Date
$endTime = $startTime.AddMinutes($DurationMinutes)
$logFile = "logs\performance_monitor_$(Get-Date -Format 'yyyyMMdd_HHmmss').log"

Write-Host "=== MONITOR DE PERFORMANCE ===" -ForegroundColor Cyan
Write-Host "Duracao: $DurationMinutes minutos" -ForegroundColor Yellow
Write-Host "Intervalo: $IntervalSeconds segundos" -ForegroundColor Yellow
Write-Host "Log: $logFile" -ForegroundColor Yellow
Write-Host "Inicio: $(Get-Date -Format 'HH:mm:ss')" -ForegroundColor Green
Write-Host "Fim previsto: $($endTime.ToString('HH:mm:ss'))" -ForegroundColor Green
Write-Host "`n[CTRL+C para parar]`n" -ForegroundColor Gray

# Headers do log
"Timestamp,CPU%,RAM_MB,Latency_ms,Trades,Status" | Out-File $logFile

$iteration = 0
while ((Get-Date) -lt $endTime) {
    $iteration++
    $now = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    
    try {
        # Buscar stats em tempo real
        $stats = Invoke-RestMethod "http://localhost:8000/api/realtime" -TimeoutSec 5 -ErrorAction Stop
        
        $cpu = [math]::Round($stats.cpu, 1)
        $ram = [math]::Round($stats.ram_mb, 0)
        $latency = [math]::Round($stats.latency_ms, 1)
        $trades = $stats.trades_per_min
        $status = "OK"
        
        # Alertas
        $alert = ""
        if ($cpu -gt 60) { $alert += " [!CPU:$cpu%]" }
        if ($ram -gt 12288) { $alert += " [!RAM:$($ram)MB]" }
        if ($latency -gt 500) { $alert += " [!LAT:$($latency)ms]" }
        
        # Display
        $line = "[$now] CPU:$cpu% RAM:$($ram)MB LAT:$($latency)ms TPM:$trades$alert"
        
        if ($alert) {
            Write-Host $line -ForegroundColor Red
        } else {
            Write-Host $line -ForegroundColor Green
        }
        
        # Log
        "$now,$cpu,$ram,$latency,$trades,$status" | Out-File $logFile -Append
        
    } catch {
        Write-Host "[$now] ERRO: Servidor nao respondeu" -ForegroundColor Red
        "$now,N/A,N/A,N/A,N/A,ERROR" | Out-File $logFile -Append
    }
    
    # Estatísticas a cada 10 iterações (5 minutos se intervalo=30s)
    if ($iteration % 10 -eq 0) {
        Write-Host "`n--- Estatisticas (ultimos 10 checks) ---" -ForegroundColor Cyan
        $recent = Import-Csv $logFile | Select-Object -Last 10
        $avgCpu = ($recent | Where-Object {$_.CPU -ne 'N/A'} | ForEach-Object {[double]$_.'CPU%'} | Measure-Object -Average).Average
        $avgRam = ($recent | Where-Object {$_.RAM_MB -ne 'N/A'} | ForEach-Object {[double]$_.RAM_MB} | Measure-Object -Average).Average
        $avgLat = ($recent | Where-Object {$_.Latency_ms -ne 'N/A'} | ForEach-Object {[double]$_.Latency_ms} | Measure-Object -Average).Average
        
        Write-Host "Media CPU: $([math]::Round($avgCpu, 1))%" -ForegroundColor Gray
        Write-Host "Media RAM: $([math]::Round($avgRam, 0))MB" -ForegroundColor Gray
        Write-Host "Media Latency: $([math]::Round($avgLat, 1))ms" -ForegroundColor Gray
        Write-Host "----------------------------------------`n" -ForegroundColor Cyan
    }
    
    Start-Sleep -Seconds $IntervalSeconds
}

Write-Host "`n=== MONITORAMENTO CONCLUIDO ===" -ForegroundColor Green
Write-Host "Log salvo em: $logFile" -ForegroundColor Yellow

# Resumo final
Write-Host "`n=== RESUMO FINAL ===" -ForegroundColor Cyan
$allData = Import-Csv $logFile | Where-Object {$_.Status -eq 'OK'}
$totalChecks = $allData.Count
$errors = (Import-Csv $logFile | Where-Object {$_.Status -eq 'ERROR'}).Count

Write-Host "Total de verificacoes: $totalChecks" -ForegroundColor White
Write-Host "Erros: $errors" -ForegroundColor $(if ($errors -eq 0) {'Green'} else {'Red'})

if ($totalChecks -gt 0) {
    $maxCpu = ($allData | ForEach-Object {[double]$_.'CPU%'} | Measure-Object -Maximum).Maximum
    $avgCpu = ($allData | ForEach-Object {[double]$_.'CPU%'} | Measure-Object -Average).Average
    $maxRam = ($allData | ForEach-Object {[double]$_.RAM_MB} | Measure-Object -Maximum).Maximum
    $avgRam = ($allData | ForEach-Object {[double]$_.RAM_MB} | Measure-Object -Average).Average
    $maxLat = ($allData | ForEach-Object {[double]$_.Latency_ms} | Measure-Object -Maximum).Maximum
    $avgLat = ($allData | ForEach-Object {[double]$_.Latency_ms} | Measure-Object -Average).Average
    
    Write-Host "`nCPU: Media=$([math]::Round($avgCpu,1))% Max=$([math]::Round($maxCpu,1))%" -ForegroundColor White
    Write-Host "RAM: Media=$([math]::Round($avgRam,0))MB Max=$([math]::Round($maxRam,0))MB" -ForegroundColor White
    Write-Host "Latency: Media=$([math]::Round($avgLat,1))ms Max=$([math]::Round($maxLat,1))ms" -ForegroundColor White
    
    # Alertas finais
    if ($maxCpu -gt 60) {
        Write-Host "`n[!] CPU ultrapassou 60% (max: $([math]::Round($maxCpu,1))%)" -ForegroundColor Red
    }
    if ($maxRam -gt 12288) {
        Write-Host "[!] RAM ultrapassou 12GB (max: $([math]::Round($maxRam,0))MB)" -ForegroundColor Red
    }
    if ($avgLat -gt 300) {
        Write-Host "[!] Latencia media alta: $([math]::Round($avgLat,1))ms" -ForegroundColor Yellow
    }
    
    if ($maxCpu -le 60 -and $maxRam -le 12288 -and $avgLat -le 300) {
        Write-Host "`n[V] Todas as metricas dentro dos limites!" -ForegroundColor Green
    }
}
