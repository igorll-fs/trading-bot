"""Script para atualizar thresholds do ML e config."""
import asyncio
import os
import sys
from datetime import datetime, timezone

# Adicionar backend ao path
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv

load_dotenv()

async def update_thresholds():
    client = AsyncIOMotorClient(os.getenv('MONGO_URL', 'mongodb://localhost:27017'))
    db = client[os.getenv('DB_NAME', 'trading_bot')]
    
    print("=== ATUALIZANDO THRESHOLDS ===\n")
    
    # 1. Atualizar config do bot
    config_result = await db.configs.update_one(
        {'type': 'bot_config'},
        {'$set': {
            'strategy_min_signal_strength': 45,
            'updated_at': datetime.now(timezone.utc).isoformat()
        }}
    )
    print(f"✓ strategy_min_signal_strength: 60 → 45")
    print(f"  (Matched: {config_result.matched_count}, Modified: {config_result.modified_count})")
    
    # 2. Atualizar parâmetros de ML
    ml_result = await db.learning_data.update_one(
        {'type': 'parameters'},
        {'$set': {
            'parameters.min_confidence_score': 0.35,
            'timestamp': datetime.now(timezone.utc)
        }},
        upsert=True
    )
    print(f"\n✓ min_confidence_score: 0.50 → 0.35")
    print(f"  (Matched: {ml_result.matched_count}, Modified: {ml_result.modified_count}, Upserted: {ml_result.upserted_id is not None})")
    
    # 3. Verificar valores
    config = await db.configs.find_one({'type': 'bot_config'})
    ml_params = await db.learning_data.find_one({'type': 'parameters'})
    
    print("\n=== VALORES ATUAIS ===")
    print(f"strategy_min_signal_strength: {config.get('strategy_min_signal_strength')}")
    if ml_params and 'parameters' in ml_params:
        print(f"min_confidence_score: {ml_params['parameters'].get('min_confidence_score')}")
    
    print("\n✅ Reinicie o bot para aplicar as mudanças!")
    
    client.close()

if __name__ == '__main__':
    asyncio.run(update_thresholds())
