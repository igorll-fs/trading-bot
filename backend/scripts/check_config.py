"""Script para verificar e atualizar config no MongoDB."""
import asyncio
import os
from datetime import datetime, timezone
from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv

load_dotenv()

async def update_and_check():
    client = AsyncIOMotorClient(os.getenv('MONGO_URL', 'mongodb://localhost:27017'))
    db = client[os.getenv('DB_NAME', 'trading_bot')]
    
    # Atualizar config
    result = await db.configs.update_one(
        {'type': 'bot_config'},
        {'$set': {
            'strategy_min_signal_strength': 40,
            'selector_min_change_percent': 0.2,
            'updated_at': datetime.now(timezone.utc).isoformat()
        }}
    )
    print(f"Update: matched={result.matched_count}, modified={result.modified_count}")
    
    # Verificar
    config = await db.configs.find_one({'type': 'bot_config'})
    if config:
        print('\\n=== CONFIG ATUALIZADA ===')
        print(f"strategy_min_signal_strength: {config.get('strategy_min_signal_strength')}")
        print(f"selector_min_change_percent: {config.get('selector_min_change_percent')}")
    
    # Atualizar ML
    ml_result = await db.learning_data.update_one(
        {'type': 'parameters'},
        {'$set': {
            'parameters.min_confidence_score': 0.30,
            'timestamp': datetime.now(timezone.utc)
        }},
        upsert=True
    )
    print(f"\\nML Update: matched={ml_result.matched_count}, modified={ml_result.modified_count}")
    
    ml = await db.learning_data.find_one({'type': 'parameters'})
    if ml:
        print(f"min_confidence_score: {ml.get('parameters', {}).get('min_confidence_score')}")
    
    client.close()

if __name__ == '__main__':
    asyncio.run(update_and_check())
