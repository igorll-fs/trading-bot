#!/usr/bin/env python3
"""Atualizar Take Profit para melhorar R/R."""
import asyncio
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), '.env'))


async def update_tp():
    client = AsyncIOMotorClient(os.getenv('MONGO_URL', 'mongodb://localhost:27017'))
    db = client[os.getenv('DB_NAME', 'trading_bot')]
    
    NEW_TP_PCT = 4.5  # Novo Take Profit em %
    
    # 1. Atualizar config para novos trades
    result = await db.configs.update_one(
        {'_id': 'main'},
        {'$set': {'take_profit_percent': NEW_TP_PCT}},
        upsert=True
    )
    print(f"✅ Config atualizada: take_profit_percent = {NEW_TP_PCT}%")
    
    # 2. Atualizar posição aberta atual
    pos = await db.positions.find_one({'status': 'open'})
    if pos:
        entry = pos['entry_price']
        old_tp = pos['take_profit']
        new_tp = round(entry * (1 + NEW_TP_PCT/100), 4)
        
        old_rr = abs((old_tp - entry) / (entry - pos['stop_loss']))
        new_rr = abs((new_tp - entry) / (entry - pos['stop_loss']))
        
        await db.positions.update_one(
            {'_id': pos['_id']},
            {'$set': {'take_profit': new_tp}}
        )
        
        print(f"\n✅ Posição {pos['symbol']} atualizada:")
        print(f"   Entrada:    ${entry:.4f}")
        print(f"   Stop Loss:  ${pos['stop_loss']:.4f}")
        print(f"   TP antigo:  ${old_tp:.4f} (R/R 1:{old_rr:.1f})")
        print(f"   TP novo:    ${new_tp:.4f} (R/R 1:{new_rr:.1f})")
    else:
        print("\n⚠️ Nenhuma posição aberta para atualizar")
    
    client.close()


if __name__ == '__main__':
    asyncio.run(update_tp())
