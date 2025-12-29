"""
Script para acelerar o aprendizado do bot através de:
1. Backtest com dados históricos
2. Simulação de trades para treinar o ML

Execute: python accelerate_learning.py
"""

import asyncio
import os
import sys
from datetime import datetime, timezone, timedelta
import random

# Adicionar path do bot
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from motor.motor_asyncio import AsyncIOMotorClient
from bot.advanced_learning import AdvancedLearningSystem

# Configurações
MONGO_URL = os.getenv("MONGO_URL", "mongodb://localhost:27017")
DB_NAME = os.getenv("DB_NAME", "trading_bot")

# Símbolos para simular
SYMBOLS = ["BTCUSDT", "ETHUSDT", "SOLUSDT", "BNBUSDT", "XRPUSDT", "ADAUSDT", "DOGEUSDT"]


async def generate_realistic_trades(num_trades: int = 50):
    """
    Gera trades realistas baseados em estatísticas típicas de mercado
    Win rate ~40-50%, Profit Factor ~1.2-1.5
    """
    trades = []
    base_time = datetime.now(timezone.utc) - timedelta(days=30)
    
    # Parâmetros realistas
    win_rate = 0.45  # 45% win rate (realista para trading)
    avg_win_percent = 2.5  # Ganho médio de 2.5%
    avg_loss_percent = 1.8  # Perda média de 1.8%
    base_position = 50  # $50 por trade
    
    for i in range(num_trades):
        symbol = random.choice(SYMBOLS)
        side = random.choice(["BUY", "SELL"])
        is_win = random.random() < win_rate
        
        # Variação realista
        if is_win:
            roe = random.uniform(1.0, avg_win_percent * 2) 
            pnl = base_position * (roe / 100)
        else:
            roe = -random.uniform(0.5, avg_loss_percent * 2)
            pnl = base_position * (roe / 100)
        
        # Timestamps
        open_time = base_time + timedelta(hours=i * 2, minutes=random.randint(0, 59))
        duration = timedelta(minutes=random.randint(15, 480))  # 15min a 8h
        close_time = open_time + duration
        
        # Hora do dia (para padrões)
        hour = open_time.hour
        if 0 <= hour < 6:
            period = "night"
        elif 6 <= hour < 12:
            period = "morning"
        elif 12 <= hour < 18:
            period = "afternoon"
        else:
            period = "evening"
        
        entry_price = random.uniform(0.1, 100000)  # Preço fictício
        exit_price = entry_price * (1 + roe/100) if side == "BUY" else entry_price * (1 - roe/100)
        
        # Calcular SL e TP realistas
        stop_loss_pct = random.uniform(1.5, 3.0)
        take_profit_pct = random.uniform(2.0, 5.0)
        
        if side == "BUY":
            stop_loss = entry_price * (1 - stop_loss_pct/100)
            take_profit = entry_price * (1 + take_profit_pct/100)
        else:
            stop_loss = entry_price * (1 + stop_loss_pct/100)
            take_profit = entry_price * (1 - take_profit_pct/100)
        
        trade = {
            "symbol": symbol,
            "side": side,
            "entry_price": round(entry_price, 8),
            "exit_price": round(exit_price, 8),
            "stop_loss": round(stop_loss, 8),
            "take_profit": round(take_profit, 8),
            "quantity": round(base_position / entry_price, 8),
            "position_size": base_position,
            "pnl": round(pnl, 2),
            "roe": round(roe, 2),
            "opened_at": open_time,
            "closed_at": close_time,
            "close_reason": "take_profit" if is_win else random.choice(["stop_loss", "trailing_stop"]),
            "period": period,
            "duration_minutes": int(duration.total_seconds() / 60),
            "simulated": True,  # Marcar como simulado
        }
        
        trades.append(trade)
    
    return trades


async def run_accelerated_learning_auto(choice: str):
    """Executa aprendizado acelerado automaticamente com escolha predefinida"""
    
    print("=" * 60)
    print("🚀 ACELERADOR DE APRENDIZADO DO BOT")
    print("=" * 60)
    
    # Conectar ao MongoDB
    client = AsyncIOMotorClient(MONGO_URL)
    db = client[DB_NAME]
    
    # Verificar trades existentes
    existing_count = await db.trades.count_documents({})
    print(f"\n📊 Trades existentes no banco: {existing_count}")
    
    # Inicializar sistema de aprendizado
    learning = AdvancedLearningSystem(db)
    await learning.initialize()
    
    print(f"📈 Métricas atuais:")
    print(f"   - Total trades analisados: {learning.metrics['total_trades']}")
    print(f"   - Win Rate: {learning.metrics['win_rate']:.1f}%")
    print(f"   - Profit Factor: {learning.metrics['profit_factor']:.2f}")
    print(f"   - Expectancy: ${learning.metrics['expectancy']:.2f}")
    
    if choice == "5":
        # Limpar simulados
        result = await db.trades.delete_many({"simulated": True})
        print(f"✅ Removidos {result.deleted_count} trades simulados")
        return
    
    if choice == "4":
        # Apenas re-analisar
        trades = await db.trades.find({}).sort("closed_at", -1).limit(200).to_list(200)
        print(f"\n🔄 Re-analisando {len(trades)} trades...")
        
        for i, trade in enumerate(trades):
            await learning.learn_from_trade(trade)
            if (i + 1) % 10 == 0:
                print(f"   Processados: {i+1}/{len(trades)}")
        
    else:
        # Gerar novos trades
        num_trades = {
            "1": 30,
            "2": 50,
            "3": 100,
        }.get(choice, 50)
        
        print(f"\n🎲 Gerando {num_trades} trades simulados realistas...")
        trades = await generate_realistic_trades(num_trades)
        
        # Salvar no banco
        print("💾 Salvando trades no MongoDB...")
        await db.trades.insert_many(trades)
        
        # Processar cada trade no sistema de aprendizado
        print("🧠 Processando trades no sistema de ML...")
        for i, trade in enumerate(trades):
            await learning.learn_from_trade(trade)
            if (i + 1) % 10 == 0:
                print(f"   Processados: {i+1}/{num_trades}")
    
    # Mostrar resultados finais
    print("\n" + "=" * 60)
    print("📊 RESULTADOS APÓS APRENDIZADO:")
    print("=" * 60)
    print(f"   Total trades: {learning.metrics['total_trades']}")
    print(f"   Win Rate: {learning.metrics['win_rate']:.1f}%")
    print(f"   Profit Factor: {learning.metrics['profit_factor']:.2f}")
    print(f"   Expectancy: ${learning.metrics['expectancy']:.2f}")
    print(f"   Sharpe Ratio: {learning.metrics['sharpe_ratio']:.2f}")
    print(f"   Max Drawdown: ${learning.metrics['max_drawdown']:.2f}")
    
    print("\n📋 PARÂMETROS OTIMIZADOS:")
    for param, value in learning.params.items():
        print(f"   {param}: {value}")
    
    # Melhores padrões
    best = learning.pattern_analyzer.get_best_patterns(min_trades=3)
    if best:
        print("\n🏆 MELHORES PADRÕES:")
        for pattern, wr, count, avg_pnl in best[:5]:
            print(f"   {pattern}: WR={wr:.0f}%, Trades={count}, Avg PnL=${avg_pnl:.2f}")
    
    worst = learning.pattern_analyzer.get_worst_patterns(min_trades=3)
    if worst:
        print("\n⚠️ PIORES PADRÕES (evitar):")
        for pattern, wr, count, avg_pnl in worst[:5]:
            print(f"   {pattern}: WR={wr:.0f}%, Trades={count}, Avg PnL=${avg_pnl:.2f}")
    
    print("\n✅ Aprendizado acelerado concluído!")
    print("   Reinicie o backend para aplicar os novos parâmetros.")


async def run_accelerated_learning():
    """Executa aprendizado acelerado com trades simulados"""
    
    print("=" * 60)
    print("🚀 ACELERADOR DE APRENDIZADO DO BOT")
    print("=" * 60)
    
    # Conectar ao MongoDB
    client = AsyncIOMotorClient(MONGO_URL)
    db = client[DB_NAME]
    
    # Verificar trades existentes
    existing_count = await db.trades.count_documents({})
    print(f"\n📊 Trades existentes no banco: {existing_count}")
    
    # Inicializar sistema de aprendizado
    learning = AdvancedLearningSystem(db)
    await learning.initialize()
    
    print(f"📈 Métricas atuais:")
    print(f"   - Total trades analisados: {learning.metrics['total_trades']}")
    print(f"   - Win Rate: {learning.metrics['win_rate']:.1f}%")
    print(f"   - Profit Factor: {learning.metrics['profit_factor']:.2f}")
    print(f"   - Expectancy: ${learning.metrics['expectancy']:.2f}")
    
    # Perguntar quantos trades simular
    print("\n" + "=" * 60)
    print("OPÇÕES:")
    print("1. Gerar 30 trades simulados (rápido)")
    print("2. Gerar 50 trades simulados (recomendado)")
    print("3. Gerar 100 trades simulados (completo)")
    print("4. Apenas analisar trades existentes")
    print("5. Limpar trades simulados anteriores")
    print("0. Sair")
    print("=" * 60)
    
    choice = input("\nEscolha uma opção: ").strip()
    
    if choice == "0":
        print("Saindo...")
        return
    
    if choice == "5":
        # Limpar simulados
        result = await db.trades.delete_many({"simulated": True})
        print(f"✅ Removidos {result.deleted_count} trades simulados")
        return
    
    if choice == "4":
        # Apenas re-analisar
        trades = await db.trades.find({}).sort("closed_at", -1).limit(200).to_list(200)
        print(f"\n🔄 Re-analisando {len(trades)} trades...")
        
        for i, trade in enumerate(trades):
            await learning.learn_from_trade(trade)
            if (i + 1) % 10 == 0:
                print(f"   Processados: {i+1}/{len(trades)}")
        
    else:
        # Gerar novos trades
        num_trades = {
            "1": 30,
            "2": 50,
            "3": 100,
        }.get(choice, 50)
        
        print(f"\n🎲 Gerando {num_trades} trades simulados realistas...")
        trades = await generate_realistic_trades(num_trades)
        
        # Salvar no banco
        print("💾 Salvando trades no MongoDB...")
        await db.trades.insert_many(trades)
        
        # Processar cada trade no sistema de aprendizado
        print("🧠 Processando trades no sistema de ML...")
        for i, trade in enumerate(trades):
            await learning.learn_from_trade(trade)
            if (i + 1) % 10 == 0:
                print(f"   Processados: {i+1}/{num_trades}")
    
    # Mostrar resultados finais
    print("\n" + "=" * 60)
    print("📊 RESULTADOS APÓS APRENDIZADO:")
    print("=" * 60)
    print(f"   Total trades: {learning.metrics['total_trades']}")
    print(f"   Win Rate: {learning.metrics['win_rate']:.1f}%")
    print(f"   Profit Factor: {learning.metrics['profit_factor']:.2f}")
    print(f"   Expectancy: ${learning.metrics['expectancy']:.2f}")
    print(f"   Sharpe Ratio: {learning.metrics['sharpe_ratio']:.2f}")
    print(f"   Max Drawdown: ${learning.metrics['max_drawdown']:.2f}")
    
    print("\n📋 PARÂMETROS OTIMIZADOS:")
    for param, value in learning.params.items():
        print(f"   {param}: {value}")
    
    # Melhores padrões
    best = learning.pattern_analyzer.get_best_patterns(min_trades=3)
    if best:
        print("\n🏆 MELHORES PADRÕES:")
        for pattern, wr, count, avg_pnl in best[:5]:
            print(f"   {pattern}: WR={wr:.0f}%, Trades={count}, Avg PnL=${avg_pnl:.2f}")
    
    worst = learning.pattern_analyzer.get_worst_patterns(min_trades=3)
    if worst:
        print("\n⚠️ PIORES PADRÕES (evitar):")
        for pattern, wr, count, avg_pnl in worst[:5]:
            print(f"   {pattern}: WR={wr:.0f}%, Trades={count}, Avg PnL=${avg_pnl:.2f}")
    
    print("\n✅ Aprendizado acelerado concluído!")
    print("   Reinicie o backend para aplicar os novos parâmetros.")


if __name__ == "__main__":
    # Aceitar argumento via linha de comando
    if len(sys.argv) > 1:
        choice = sys.argv[1]
        asyncio.run(run_accelerated_learning_auto(choice))
    else:
        asyncio.run(run_accelerated_learning())
