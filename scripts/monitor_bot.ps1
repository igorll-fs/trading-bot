# monitor_bot.ps1
# Script para monitoramento contínuo do Trading Bot

param(
    [int]$Interval = 30,  # Intervalo em segundos entre verificações
    [int]$Duration = 300  # Duração total em segundos (5 minutos padrão)
)

Write-Host "`n╔════════════════════════════════════════════════════════════╗" -ForegroundColor Cyan
Write-Host "║     🤖 MONITORAMENTO CONTÍNUO DO TRADING BOT 🤖          ║" -ForegroundColor Cyan
Write-Host "╚════════════════════════════════════════════════════════════╝`n" -ForegroundColor Cyan

Write-Host "⏱️  Intervalo: $Interval segundos" -ForegroundColor Gray
Write-Host "⏰ Duração: $Duration segundos ($([math]::Round($Duration/60, 1)) minutos)`n" -ForegroundColor Gray

$startTime = Get-Date
$endTime = $startTime.AddSeconds($Duration)
$iteration = 0

while ((Get-Date) -lt $endTime) {
    $iteration++
    $now = Get-Date -Format "HH:mm:ss"
    
    Write-Host "`n═══════════════════════════════════════════════════════════" -ForegroundColor Gray
    Write-Host "[$now] 🔍 Verificação #$iteration" -ForegroundColor Cyan
    Write-Host "═══════════════════════════════════════════════════════════" -ForegroundColor Gray
    
    # 1. Status dos serviços
    $backend = Test-NetConnection -ComputerName localhost -Port 8001 -InformationLevel Quiet -WarningAction SilentlyContinue
    $frontend = Test-NetConnection -ComputerName localhost -Port 3000 -InformationLevel Quiet -WarningAction SilentlyContinue
    
    Write-Host "`n📡 Serviços:" -ForegroundColor Yellow
    Write-Host "   Backend:  $(if($backend){'✅'}else{'❌'})" -ForegroundColor $(if($backend){'Green'}else{'Red'})
    Write-Host "   Frontend: $(if($frontend){'✅'}else{'❌'})" -ForegroundColor $(if($frontend){'Green'}else{'Red'})
    
    # 2. Status do bot
    if ($backend) {
        try {
            $status = Invoke-RestMethod -Uri "http://localhost:8001/api/bot/status" -Method GET -TimeoutSec 3
            
            Write-Host "`n🤖 Bot:" -ForegroundColor Yellow
            Write-Host "   Status:    $(if($status.is_running){'✅ Ativo'}else{'❌ Parado'})" -ForegroundColor $(if($status.is_running){'Green'}else{'Red'})
            Write-Host "   Saldo:     $([math]::Round($status.balance, 2)) USDT" -ForegroundColor White
            Write-Host "   Posições:  $($status.open_positions)/$($status.max_positions)" -ForegroundColor White
            
            # Alertar se houver posições abertas
            if ($status.open_positions -gt 0) {
                Write-Host "`n   🚨 ATENÇÃO: $($status.open_positions) posição(ões) aberta(s)!" -ForegroundColor Red
            }
            
        } catch {
            Write-Host "`n⚠️  Erro ao consultar bot: $_" -ForegroundColor Yellow
        }
        
        # 3. Verificar trades recentes
        try {
            $trades = Invoke-RestMethod -Uri "http://localhost:8001/api/trades?limit=3" -Method GET -TimeoutSec 3
            
            if ($trades -and $trades.Count -gt 0) {
                Write-Host "`n📊 Últimos Trades:" -ForegroundColor Yellow
                foreach ($trade in $trades) {
                    $emoji = if ($trade.pnl -gt 0) { "✅" } else { "❌" }
                    $pnlColor = if ($trade.pnl -gt 0) { "Green" } else { "Red" }
                    Write-Host "   $emoji $($trade.symbol) | $($trade.side) | PnL: $([math]::Round($trade.pnl, 2)) USDT" -ForegroundColor $pnlColor
                }
            }
        } catch {
            # Silencioso se não houver trades
        }
        
        # 4. Performance
        try {
            $perf = Invoke-RestMethod -Uri "http://localhost:8001/api/performance" -Method GET -TimeoutSec 3
            
            if ($perf.total_trades -gt 0) {
                $winRate = [math]::Round(($perf.winning_trades / $perf.total_trades) * 100, 1)
                Write-Host "`n📈 Performance:" -ForegroundColor Yellow
                Write-Host "   Total:     $($perf.total_trades) trades" -ForegroundColor White
                Write-Host "   Win Rate:  $winRate% ($($perf.winning_trades)W / $($perf.losing_trades)L)" -ForegroundColor $(if($winRate -ge 50){'Green'}else{'Red'})
                Write-Host "   PnL Total: $([math]::Round($perf.total_pnl, 2)) USDT" -ForegroundColor $(if($perf.total_pnl -gt 0){'Green'}else{'Red'})
            }
        } catch {
            # Silencioso
        }
    } else {
        Write-Host "`n❌ Backend offline - não é possível monitorar o bot!" -ForegroundColor Red
    }
    
    # 5. Uso de recursos
    $pythonProc = Get-Process | Where-Object {$_.ProcessName -like '*python*'} | Select-Object -First 1
    if ($pythonProc) {
        $ramUsage = [math]::Round($pythonProc.WorkingSet / 1MB, 2)
        Write-Host "`n💻 Recursos:" -ForegroundColor Yellow
        Write-Host "   Python RAM: $ramUsage MB" -ForegroundColor White
    }
    
    # Aguardar próximo ciclo
    if ((Get-Date) -lt $endTime) {
        Write-Host "`n⏳ Próxima verificação em $Interval segundos..." -ForegroundColor Gray
        Start-Sleep -Seconds $Interval
    }
}

Write-Host "`n╔════════════════════════════════════════════════════════════╗" -ForegroundColor Green
Write-Host "║            ✅ MONITORAMENTO CONCLUÍDO ✅                  ║" -ForegroundColor Green
Write-Host "╚════════════════════════════════════════════════════════════╝`n" -ForegroundColor Green

$totalTime = ((Get-Date) - $startTime).TotalMinutes
Write-Host "⏱️  Tempo total: $([math]::Round($totalTime, 1)) minutos" -ForegroundColor White
Write-Host "🔍 Verificações realizadas: $iteration`n" -ForegroundColor White
