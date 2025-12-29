#!/usr/bin/env python3
"""
Monitor em tempo real da posição aberta.
Mostra P&L, distância do SL/TP e métricas de estratégia.
"""
import asyncio
import os
import sys
from datetime import datetime, timezone

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv
import httpx

load_dotenv(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), '.env'))


async def get_current_price(symbol: str) -> float:
    """Busca preço atual na testnet."""
    async with httpx.AsyncClient() as client:
        resp = await client.get(
            f"https://testnet.binance.vision/api/v3/ticker/price?symbol={symbol}"
        )
        data = resp.json()
        return float(data['price'])


async def monitor():
    mongo_url = os.getenv('MONGO_URL', 'mongodb://localhost:27017')
    db_name = os.getenv('DB_NAME', 'trading_bot')
    
    client = AsyncIOMotorClient(mongo_url)
    db = client[db_name]
    
    # Buscar posição aberta
    position = await db.positions.find_one({'status': 'open'})
    
    if not position:
        print("❌ Nenhuma posição aberta encontrada.")
        return
    
    symbol = position['symbol']
    entry = position['entry_price']
    sl = position['stop_loss']
    tp = position['take_profit']
    size = position['position_size']
    ml_score = position.get('ml_score', 0)
    opened_at = position['opened_at']
    
    # Buscar preço atual
    current = await get_current_price(symbol)
    
    # Calcular métricas
    pnl_pct = ((current - entry) / entry) * 100
    pnl_usd = size * (pnl_pct / 100)
    
    sl_distance = ((sl - current) / current) * 100  # Negativo se acima do SL
    tp_distance = ((tp - current) / current) * 100  # Positivo se abaixo do TP
    
    risk = abs(entry - sl)
    reward = abs(tp - entry)
    rr_ratio = reward / risk if risk > 0 else 0
    
    # Calcular tempo na posição
    try:
        opened_dt = datetime.fromisoformat(opened_at.replace('Z', '+00:00'))
        duration = datetime.now(timezone.utc) - opened_dt
        duration_str = str(duration).split('.')[0]  # Remover microsegundos
    except:
        duration_str = "N/A"
    
    # Status visual
    if pnl_pct > 0:
        status_emoji = "🟢"
        status_text = "EM LUCRO"
    elif pnl_pct < -1:
        status_emoji = "🔴"
        status_text = "EM PREJUÍZO"
    else:
        status_emoji = "🟡"
        status_text = "NEUTRO"
    
    print("=" * 60)
    print(f"        {status_emoji} MONITOR DE POSIÇÃO - {symbol} {status_emoji}")
    print("=" * 60)
    print()
    print(f"  Status:          {status_text}")
    print(f"  Tempo aberta:    {duration_str}")
    print()
    print("-" * 60)
    print("  PREÇOS")
    print("-" * 60)
    print(f"  Entrada:         ${entry:.4f}")
    print(f"  Atual:           ${current:.4f}")
    print(f"  Stop Loss:       ${sl:.4f} ({sl_distance:+.2f}% de distância)")
    print(f"  Take Profit:     ${tp:.4f} ({tp_distance:+.2f}% de distância)")
    print()
    print("-" * 60)
    print("  P&L")
    print("-" * 60)
    print(f"  Variação:        {pnl_pct:+.2f}%")
    print(f"  Lucro/Prejuízo:  ${pnl_usd:+.2f}")
    print(f"  Tamanho:         ${size:.2f}")
    print()
    print("-" * 60)
    print("  ESTRATÉGIA")
    print("-" * 60)
    print(f"  ML Score:        {ml_score:.2f} {'✅' if ml_score >= 0.4 else '⚠️'}")
    print(f"  Risk/Reward:     1:{rr_ratio:.1f} {'✅' if rr_ratio >= 2 else '⚠️'}")
    print(f"  Risco ($):       ${size * abs((entry - sl) / entry):.2f}")
    print(f"  Alvo ($):        ${size * abs((tp - entry) / entry):.2f}")
    print()
    print("=" * 60)
    
    # Avaliar qualidade do trade
    print("  AVALIAÇÃO DO SETUP")
    print("-" * 60)
    
    score = 0
    checks = []
    
    if rr_ratio >= 2:
        score += 1
        checks.append("✅ Risk/Reward >= 1:2")
    else:
        checks.append("⚠️ Risk/Reward < 1:2")
    
    if ml_score >= 0.4:
        score += 1
        checks.append("✅ ML Score >= 0.40")
    else:
        checks.append("⚠️ ML Score < 0.40")
    
    if pnl_pct > 0:
        score += 1
        checks.append("✅ Posição em lucro")
    elif pnl_pct < -1:
        checks.append("❌ Posição em prejuízo")
    else:
        checks.append("🟡 Posição neutra")
    
    for check in checks:
        print(f"  {check}")
    
    print()
    print(f"  Score Geral: {score}/3 - ", end="")
    if score >= 2:
        print("BOM SETUP 👍")
    else:
        print("SETUP MODERADO ⚠️")
    
    print("=" * 60)
    
    client.close()


if __name__ == '__main__':
    asyncio.run(monitor())
