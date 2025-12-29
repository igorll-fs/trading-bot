from motor.motor_asyncio import AsyncIOMotorClient
import asyncio

async def check():
    client = AsyncIOMotorClient('mongodb://localhost:27017')
    db = client['trading_bot']
    config = await db.configs.find_one({'type': 'bot_config'})
    
    if config:
        print(f"Telegram Bot Token: {config.get('telegram_bot_token', 'VAZIO')[:20]}...")
        print(f"Telegram Chat ID: {config.get('telegram_chat_id', 'VAZIO')}")
    else:
        print("Config não encontrada")
    
    client.close()

asyncio.run(check())
