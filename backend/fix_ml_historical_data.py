"""Script para corrigir dados históricos do sistema ML no MongoDB"""
from pymongo import MongoClient
import os
from dotenv import load_dotenv
from datetime import datetime, timezone

load_dotenv()
MONGO_URL = os.getenv("MONGO_URL", "mongodb://localhost:27017")
DB_NAME = os.getenv("DB_NAME", "trading_bot")

client = MongoClient(MONGO_URL)
db = client[DB_NAME]

print("=" * 70)
print("CORRIGINDO DADOS HISTÓRICOS DO SISTEMA ML")
print("=" * 70)

# 1. Atualizar análises de trade antigas (adicionar campo 'won' e 'ml_score')
print("\n📊 Atualizando análises de trade...")
analyses = list(db.learning_data.find({'type': 'trade_analysis'}))
print(f"   - Encontradas {len(analyses)} análises")

updated_count = 0
for analysis in analyses:
    pnl = analysis.get('pnl', 0)
    
    # Adicionar campos faltantes
    update_fields = {}
    
    # Campo 'won' baseado no PnL
    if 'won' not in analysis:
        update_fields['won'] = pnl > 0
    
    # Campo 'ml_score' (usar confidence_score se existir, senão 0)
    if 'ml_score' not in analysis:
        update_fields['ml_score'] = analysis.get('confidence_score', 0.0)
    
    # Campo 'timestamp' se não existe
    if 'timestamp' not in analysis:
        update_fields['timestamp'] = analysis.get('analyzed_at', datetime.now(timezone.utc).isoformat())
    
    if update_fields:
        db.learning_data.update_one(
            {'_id': analysis['_id']},
            {'$set': update_fields}
        )
        updated_count += 1

print(f"   - ✅ {updated_count} análises atualizadas")

# 2. Verificar parâmetros salvos
print("\n🎯 Verificando parâmetros salvos...")
params_docs = list(db.learning_data.find({'type': 'parameters'}).sort('timestamp', -1))
print(f"   - Encontrados {len(params_docs)} registros de parâmetros")

if params_docs:
    latest = params_docs[0]
    print(f"\n   Último registro:")
    print(f"   - Timestamp: {latest.get('timestamp', 'N/A')}")
    print(f"   - Total adjustments: {latest.get('total_adjustments', 0)}")
    
    params = latest.get('parameters', {})
    if params:
        print(f"   - min_confidence_score: {params.get('min_confidence_score', 'N/A')}")
        print(f"   - stop_loss_multiplier: {params.get('stop_loss_multiplier', 'N/A')}")
        print(f"   - take_profit_multiplier: {params.get('take_profit_multiplier', 'N/A')}")
        print(f"   - position_size_multiplier: {params.get('position_size_multiplier', 'N/A')}")
    else:
        print("   ⚠️ Parâmetros vazios no registro")

# 3. Verificar consistência dos dados
print("\n🔍 Verificando consistência dos dados...")

# Contar wins vs losses
total_analyses = db.learning_data.count_documents({'type': 'trade_analysis'})
wins = db.learning_data.count_documents({'type': 'trade_analysis', 'won': True})
losses = db.learning_data.count_documents({'type': 'trade_analysis', 'won': False})
win_rate = (wins / total_analyses * 100) if total_analyses > 0 else 0

print(f"   - Total análises: {total_analyses}")
print(f"   - Wins: {wins} ({win_rate:.1f}%)")
print(f"   - Losses: {losses} ({100-win_rate:.1f}%)")

# Verificar scores ML
analyses_with_scores = db.learning_data.count_documents({
    'type': 'trade_analysis',
    'ml_score': {'$gt': 0}
})
print(f"   - Análises com ML score > 0: {analyses_with_scores}/{total_analyses}")

# 4. Resumo final
print("\n" + "=" * 70)
print("RESUMO FINAL")
print("=" * 70)

if updated_count > 0:
    print(f"\n✅ Correção aplicada com sucesso!")
    print(f"   - {updated_count} análises atualizadas")
    print(f"   - Win Rate calculado: {win_rate:.1f}%")
else:
    print("\n✅ Dados já estão corretos!")

print(f"\n📊 Próximos passos:")
print("   1. Reinicie o backend para carregar dados corrigidos")
print("   2. Verifique o dashboard - seção Machine Learning")
print("   3. Execute um novo trade para testar o sistema")
print("\n" + "=" * 70)
