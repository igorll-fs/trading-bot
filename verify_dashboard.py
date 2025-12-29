import requests

print("=" * 50)
print("VERIFICACAO DOS DADOS DO DASHBOARD")
print("=" * 50)

# Performance
perf = requests.get('http://127.0.0.1:8000/api/performance').json()
print(f"\n[PERFORMANCE]")
print(f"Total Trades: {perf['total_trades']}")
print(f"Winning Trades: {perf['winning_trades']}")
print(f"Losing Trades: {perf['losing_trades']}")
print(f"Win Rate: {perf['win_rate']:.1f}%")
print(f"PnL Total: ${perf['total_pnl']}")
print(f"Profit Factor: {perf['profit_factor']}")
print(f"Expectancy: ${perf['expectancy']}")
print(f"Max Drawdown: ${perf['max_drawdown']}")
print(f"Best Trade: ${perf['best_trade']}")
print(f"Worst Trade: ${perf['worst_trade']}")
print(f"Avg Win: ${perf['avg_win']}")
print(f"Avg Loss: ${perf['avg_loss']}")
print(f"Streak: {perf['current_streak']} ({perf['streak_type']})")

# Bot Status
status = requests.get('http://127.0.0.1:8000/api/bot/status').json()
print(f"\n[BOT STATUS]")
print(f"Running: {status['is_running']}")
print(f"Balance: ${status['balance']:.2f}")
print(f"Open Positions: {status['open_positions']}/{status['max_positions']}")
print(f"Testnet Mode: {status.get('testnet_mode', 'N/A')}")

# Trades
trades = requests.get('http://127.0.0.1:8000/api/trades?limit=5').json()
print(f"\n[ULTIMOS 5 TRADES]")
for t in trades[:5]:
    simulated = " (SIMULADO)" if t.get('simulated') else ""
    print(f"  {t['symbol']}: ${t.get('pnl', 0):.2f} - {t.get('close_reason', 'N/A')}{simulated}")

print("\n" + "=" * 50)
print("VERIFICACAO CONCLUIDA")
print("=" * 50)
