#!/usr/bin/env python3
"""
Script para remover posições duplicadas.
Mantém apenas a primeira posição por símbolo.
"""
import asyncio
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), '.env'))


async def fix_duplicates():
    mongo_url = os.getenv('MONGO_URL', 'mongodb://localhost:27017')
    db_name = os.getenv('DB_NAME', 'trading_bot')
    
    client = AsyncIOMotorClient(mongo_url)
    db = client[db_name]
    
    # Buscar posições abertas
    cursor = db.positions.find({'status': 'open'}).sort('opened_at', 1)
    positions = await cursor.to_list(100)
    
    print(f"Total de posições abertas: {len(positions)}")
    
    # Agrupar por símbolo
    by_symbol = {}
    for pos in positions:
        symbol = pos['symbol']
        if symbol not in by_symbol:
            by_symbol[symbol] = []
        by_symbol[symbol].append(pos)
    
    # Encontrar duplicatas
    duplicates_to_remove = []
    for symbol, pos_list in by_symbol.items():
        if len(pos_list) > 1:
            print(f"\n⚠️  Duplicatas encontradas para {symbol}: {len(pos_list)} posições")
            # Manter a primeira (mais antiga), remover as outras
            for i, pos in enumerate(pos_list):
                status = "✅ MANTER" if i == 0 else "❌ REMOVER"
                print(f"  {status}: ID={pos['_id']}, Aberta em: {pos['opened_at']}")
                if i > 0:
                    duplicates_to_remove.append(pos['_id'])
    
    if not duplicates_to_remove:
        print("\n✅ Nenhuma duplicata encontrada!")
        return
    
    # Confirmar remoção
    print(f"\n{len(duplicates_to_remove)} posições duplicadas serão marcadas como 'closed' (não deletadas)")
    confirm = input("Confirmar? (s/n): ").strip().lower()
    
    if confirm != 's':
        print("Operação cancelada.")
        return
    
    # Marcar duplicatas como fechadas
    for pos_id in duplicates_to_remove:
        result = await db.positions.update_one(
            {'_id': pos_id},
            {'$set': {'status': 'closed_duplicate', 'close_reason': 'duplicate_fix'}}
        )
        print(f"  Posição {pos_id} marcada como fechada: {result.modified_count}")
    
    print("\n✅ Duplicatas corrigidas!")
    
    client.close()


if __name__ == '__main__':
    asyncio.run(fix_duplicates())
