#!/usr/bin/env python3
"""Scan completo do bot - verifica status e histórico."""
import asyncio
import os
import sys
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import httpx
from dotenv import load_dotenv
from motor.motor_asyncio import AsyncIOMotorClient

load_dotenv(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), '.env'))


async def get_price(symbol):
    try:
        async with httpx.AsyncClient() as client:
            resp = await client.get(f"https://testnet.binance.vision/api/v3/ticker/price?symbol={symbol}")
            return float(resp.json()['price'])
    except Exception:
        return None


async def scan():
    client = AsyncIOMotorClient(os.getenv('MONGO_URL', 'mongodb://localhost:27017'))
    db = client[os.getenv('DB_NAME', 'trading_bot')]
    
    print("=" * 70)
    print("                    🔍 SCAN COMPLETO DO BOT")
    print("=" * 70)
    print(f"  Horário: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # 1. Posições abertas
    open_positions = await db.positions.find({'status': 'open'}).to_list(100)
    print(f"\n📊 POSIÇÕES ABERTAS: {len(open_positions)}")
    print("-" * 70)
    
    if open_positions:
        for pos in open_positions:
            current = await get_price(pos['symbol'])
            if current:
                pnl_pct = ((current - pos['entry_price']) / pos['entry_price']) * 100
                pnl_usd = pos['position_size'] * (pnl_pct / 100)
                status = "🟢" if pnl_pct > 0 else "🔴" if pnl_pct < -0.5 else "🟡"
                print(f"  {status} {pos['symbol']}")
                print(f"     Entry: ${pos['entry_price']:.4f} | Atual: ${current:.4f}")
                print(f"     P&L: ${pnl_usd:+.2f} ({pnl_pct:+.2f}%)")
                print(f"     SL: ${pos['stop_loss']:.4f} | TP: ${pos['take_profit']:.4f}")
    else:
        print("  Nenhuma posição aberta no momento")
    
    # 2. Trades fechados (histórico)
    trades = await db.trades.find().sort('closed_at', -1).limit(10).to_list(10)
    print(f"\n📜 ÚLTIMOS TRADES FECHADOS: {len(trades)}")
    print("-" * 70)
    
    if trades:
        total_pnl = 0
        wins = 0
        for t in trades:
            pnl = t.get('pnl', 0)
            total_pnl += pnl
            if pnl > 0:
                wins += 1
            status = "🟢" if pnl > 0 else "🔴"
            reason = t.get('close_reason', 'N/A')
            symbol = t.get('symbol', '?')
            t.get('closed_at', 'N/A')
            print(f"  {status} {symbol} | PnL: ${pnl:+.2f} | Motivo: {reason}")
        
        print()
        print(f"  📈 Resumo: {wins}/{len(trades)} wins | PnL Total: ${total_pnl:+.2f}")
    else:
        print("  Nenhum trade fechado ainda")
    
    # 3. Posições fechadas (não em trades)
    closed_positions = await db.positions.find({
        'status': {'$nin': ['open']}
    }).sort('opened_at', -1).limit(5).to_list(5)
    
    print(f"\n📁 POSIÇÕES RECENTES (fechadas/canceladas): {len(closed_positions)}")
    print("-" * 70)
    
    if closed_positions:
        for p in closed_positions:
            status = p.get('status', 'unknown')
            symbol = p.get('symbol', '?')
            entry = p.get('entry_price', 0)
            print(f"  • {symbol} | Status: {status} | Entry: ${entry:.4f}")
    else:
        print("  Nenhuma")
    
    # 4. Verificar se bot está rodando
    print("\n🤖 STATUS DO BOT")
    print("-" * 70)
    
    try:
        async with httpx.AsyncClient(timeout=5) as http:
            resp = await http.get("http://localhost:8002/api/bot/status")
            if resp.status_code == 200:
                data = resp.json()
                running = data.get('running', False)
                status = "🟢 RODANDO" if running else "🔴 PARADO"
                print(f"  Status: {status}")
                if running:
                    print(f"  Modo: {data.get('mode', 'N/A')}")
                    print(f"  Posições: {data.get('positions_count', 0)}")
            else:
                print(f"  ⚠️ API retornou erro: {resp.status_code}")
    except Exception as e:
        print(f"  ❌ Não foi possível conectar à API: {e}")
    
    # 5. Saldo
    print("\n💰 SALDO (Testnet)")
    print("-" * 70)
    try:
        async with httpx.AsyncClient(timeout=5) as http:
            resp = await http.get("http://localhost:8002/api/balance")
            if resp.status_code == 200:
                data = resp.json()
                print(f"  USDT: ${data.get('balance', 0):,.2f}")
            else:
                print("  ⚠️ Erro ao buscar saldo")
    except Exception:
        print("  ❌ API indisponível")
    
    print()
    print("=" * 70)
    
    client.close()


if __name__ == '__main__':
    asyncio.run(scan())
