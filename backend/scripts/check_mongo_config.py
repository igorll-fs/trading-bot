#!/usr/bin/env python3
"""Verificar configuração do MongoDB."""
import asyncio
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), '.env'))


async def check():
    client = AsyncIOMotorClient(os.getenv('MONGO_URL', 'mongodb://localhost:27017'))
    db = client[os.getenv('DB_NAME', 'trading_bot')]
    config = await db.configs.find_one({'_id': 'main'})
    
    if config:
        has_key = bool(config.get('binance_api_key'))
        has_secret = bool(config.get('binance_api_secret'))
        testnet = config.get('testnet_mode', True)
        print('Config encontrada no MongoDB')
        print(f'  API Key: {"SIM" if has_key else "NAO"}')
        print(f'  API Secret: {"SIM" if has_secret else "NAO"}')
        print(f'  Testnet: {testnet}')
    else:
        print('Nenhuma config no MongoDB')
    
    client.close()


if __name__ == '__main__':
    asyncio.run(check())
