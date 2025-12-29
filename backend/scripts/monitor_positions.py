"""Script para monitorar posições e trades."""
import asyncio
import os
from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv

load_dotenv()

async def monitor():
    client = AsyncIOMotorClient(os.getenv('MONGO_URL', 'mongodb://localhost:27017'))
    db = client[os.getenv('DB_NAME', 'trading_bot')]
    
    print("=" * 50)
    print("MONITORAMENTO DO BOT")
    print("=" * 50)
    
    # Posições abertas
    positions = await db.positions.find({'status': 'open'}).to_list(10)
    print(f"\n📊 POSIÇÕES ABERTAS: {len(positions)}")
    for p in positions:
        symbol = p.get('symbol', 'N/A')
        side = p.get('side', 'N/A')
        entry = p.get('entry_price', 0)
        sl = p.get('stop_loss', 0)
        tp = p.get('take_profit', 0)
        size = p.get('position_size', 0)
        ml_score = p.get('ml_score', 0)
        opened = p.get('opened_at', 'N/A')
        
        print(f"\n  🔹 {symbol} ({side})")
        print(f"     Entrada: ${entry:.4f}")
        print(f"     Stop Loss: ${sl:.4f}")
        print(f"     Take Profit: ${tp:.4f}")
        print(f"     Tamanho: ${size:.2f} USDT")
        print(f"     ML Score: {ml_score:.2f}")
        print(f"     Aberta em: {opened}")
    
    # Últimos trades fechados
    trades = await db.trades.find().sort('closed_at', -1).to_list(5)
    print(f"\n📈 ÚLTIMOS TRADES FECHADOS: {len(trades)}")
    total_pnl = 0
    for t in trades:
        symbol = t.get('symbol', 'N/A')
        side = t.get('side', 'N/A')
        pnl = t.get('pnl', 0)
        roe = t.get('roe', 0)
        reason = t.get('close_reason', 'N/A')
        closed = t.get('closed_at', 'N/A')
        total_pnl += pnl
        
        emoji = "✅" if pnl > 0 else "❌"
        print(f"\n  {emoji} {symbol} ({side})")
        print(f"     PnL: ${pnl:.2f} ({roe:.2f}%)")
        print(f"     Motivo: {reason}")
        print(f"     Fechado em: {closed}")
    
    if trades:
        print(f"\n💰 PnL TOTAL (últimos {len(trades)} trades): ${total_pnl:.2f}")
    
    client.close()

if __name__ == '__main__':
    asyncio.run(monitor())
