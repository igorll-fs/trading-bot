"""Verificar dados do sistema ML"""
from pymongo import MongoClient
import os
from dotenv import load_dotenv

# Carregar variáveis de ambiente
load_dotenv()
MONGO_URL = os.getenv("MONGO_URL", "mongodb://localhost:27017")
DB_NAME = os.getenv("DB_NAME", "trading_bot")

client = MongoClient(MONGO_URL)
db = client[DB_NAME]

print("=" * 60)
print("VERIFICAÇÃO SISTEMA ML - DADOS REAIS")
print("=" * 60)

# 1. Verificar trades
total_trades = db.trades.count_documents({})
print(f"\n📊 TRADES NO MONGODB: {total_trades}")

if total_trades > 0:
    trades = list(db.trades.find({}).limit(10))
    winning = [t for t in trades if t.get('pnl', 0) > 0]
    losing = [t for t in trades if t.get('pnl', 0) <= 0]
    
    print(f"   - Winning (PnL > 0): {len(winning)}")
    print(f"   - Losing (PnL <= 0): {len(losing)}")
    
    print("\n📈 Últimos 10 trades:")
    for i, trade in enumerate(trades[:10], 1):
        symbol = trade.get('symbol', 'N/A')
        pnl = trade.get('pnl', 0)
        status = '✅ WIN' if pnl > 0 else '❌ LOSS'
        print(f"   {i}. {symbol}: PnL={pnl:.4f} {status}")

# 2. Verificar learning_data
total_learning = db.learning_data.count_documents({})
print(f"\n🧠 LEARNING_DATA NO MONGODB: {total_learning}")

if total_learning > 0:
    params = db.learning_data.find_one({'type': 'parameters'})
    if params:
        print(f"\n   Parâmetros atuais:")
        print(f"   - min_confidence_score: {params.get('min_confidence_score', 'N/A')}")
        print(f"   - stop_loss_multiplier: {params.get('stop_loss_multiplier', 'N/A')}")
        print(f"   - total_adjustments: {params.get('total_adjustments', 0)}")
    
    # Análises de trades
    analyses = list(db.learning_data.find({'type': 'trade_analysis'}).limit(5))
    print(f"\n   Análises de trade: {len(analyses)}")
    for i, analysis in enumerate(analyses, 1):
        won = analysis.get('won', False)
        confidence = analysis.get('confidence_score', 0)
        print(f"   {i}. Won={won}, Confidence={confidence:.2f}")

# 3. Verificar endpoint learning stats
print("\n" + "=" * 60)
print("VERIFICANDO CÁLCULOS DO BACKEND")
print("=" * 60)

from bot.learning_system import BotLearningSystem

try:
    ml_system = BotLearningSystem()
    
    print(f"\n📊 Performance Metrics:")
    print(f"   - Total Trades: {ml_system.performance_metrics.get('total_trades', 0)}")
    print(f"   - Win Rate: {ml_system.performance_metrics.get('win_rate', 0):.2f}%")
    print(f"   - Avg Confidence: {ml_system.performance_metrics.get('average_confidence', 0):.2f}")
    
    print(f"\n🎯 Adjustable Parameters:")
    for param, value in ml_system.adjustable_params.items():
        print(f"   - {param}: {value}")
    
except Exception as e:
    print(f"❌ Erro ao carregar BotLearningSystem: {e}")

print("\n" + "=" * 60)
print("DIAGNÓSTICO COMPLETO")
print("=" * 60)

# Diagnóstico final
if total_trades == 0:
    print("\n⚠️ PROBLEMA: Nenhum trade registrado no MongoDB")
    print("   Solução: Bot precisa executar trades para coletar dados")
elif total_trades > 0 and total_learning == 0:
    print("\n⚠️ PROBLEMA: Trades existem mas learning_data vazio")
    print("   Solução: Sistema ML não está analisando trades")
else:
    print("\n✅ Sistema ML configurado e operacional")
    print(f"   - {total_trades} trades registrados")
    print(f"   - {total_learning} documentos de aprendizado")
