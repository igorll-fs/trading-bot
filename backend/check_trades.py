from motor.motor_asyncio import AsyncIOMotorClient
import asyncio

async def check():
    client = AsyncIOMotorClient('mongodb://localhost:27017')
    db = client['trading_bot']
    
    trades_count = await db.trades.count_documents({})
    positions_count = await db.positions.count_documents({})
    
    print(f"📊 Trades no banco: {trades_count}")
    print(f"📊 Posições abertas: {positions_count}")
    
    if trades_count > 0:
        print("\nÚltimos 3 trades:")
        async for trade in db.trades.find().sort('opened_at', -1).limit(3):
            print(f"  - {trade.get('symbol')} | {trade.get('side')} | {trade.get('status')}")
    
    client.close()

asyncio.run(check())
