#!/usr/bin/env python3
"""
Verificar se a lógica de decisão de venda está funcionando corretamente.
Simula diferentes cenários de preço e verifica as decisões.
"""
import asyncio
import os
import sys

import httpx

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv
from motor.motor_asyncio import AsyncIOMotorClient

from bot.risk_manager import RiskManager

load_dotenv(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), '.env'))


async def get_current_price(symbol: str) -> float:
    async with httpx.AsyncClient() as client:
        resp = await client.get(f"https://testnet.binance.vision/api/v3/ticker/price?symbol={symbol}")
        return float(resp.json()['price'])


async def test_sell_decision():
    client = AsyncIOMotorClient(os.getenv('MONGO_URL', 'mongodb://localhost:27017'))
    db = client[os.getenv('DB_NAME', 'trading_bot')]
    
    print("=" * 70)
    print("     🧪 TESTE DE DECISÃO DE VENDA (FECHAMENTO)")
    print("=" * 70)
    
    # Buscar posição aberta
    pos = await db.positions.find_one({'status': 'open'})
    
    if not pos:
        print("\n❌ Nenhuma posição aberta para testar")
        return
    
    symbol = pos['symbol']
    entry = pos['entry_price']
    sl = pos['stop_loss']
    tp = pos['take_profit']
    side = pos['side']
    
    # Preço atual
    current = await get_current_price(symbol)
    
    print(f"\n📊 POSIÇÃO ATUAL: {symbol}")
    print("-" * 70)
    print(f"  Side:         {side}")
    print(f"  Entrada:      ${entry:.4f}")
    print(f"  Stop Loss:    ${sl:.4f}")
    print(f"  Take Profit:  ${tp:.4f}")
    print(f"  Preço Atual:  ${current:.4f}")
    
    # Criar RiskManager para testar
    rm = RiskManager()
    
    # Testar decisão atual
    print(f"\n🔍 TESTE COM PREÇO ATUAL (${current:.4f})")
    print("-" * 70)
    should_close, reason = rm.should_close_position(current, entry, sl, tp, side)
    
    if should_close:
        print(f"  ✅ Decisão: FECHAR - Motivo: {reason}")
    else:
        print("  ⏳ Decisão: MANTER ABERTA")
        print(f"     Distância SL: {((current - sl) / current) * 100:.2f}%")
        print(f"     Distância TP: {((tp - current) / current) * 100:.2f}%")
    
    # Simular cenários
    print("\n🎭 SIMULAÇÃO DE CENÁRIOS")
    print("-" * 70)
    
    scenarios = [
        ("Preço = Stop Loss", sl),
        ("Preço 0.1% abaixo do SL", sl * 0.999),
        ("Preço = Take Profit", tp),
        ("Preço 0.1% acima do TP", tp * 1.001),
        ("Preço no meio", (entry + tp) / 2),
    ]
    
    for desc, test_price in scenarios:
        should_close, reason = rm.should_close_position(test_price, entry, sl, tp, side)
        status = f"🔴 FECHAR ({reason})" if should_close else "🟢 MANTER"
        print(f"  {desc:30} | ${test_price:.4f} | {status}")
    
    # Verificar lógica inversa (lado SELL - não usado em Spot, mas para completude)
    print("\n📋 VERIFICAÇÃO DA LÓGICA")
    print("-" * 70)
    
    checks = []
    
    # Teste 1: Preço abaixo do SL deve fechar
    test1 = rm.should_close_position(sl - 0.001, entry, sl, tp, 'BUY')
    checks.append(("Preço < SL (BUY) deve fechar", test1[0] and test1[1] == 'STOP_LOSS'))
    
    # Teste 2: Preço = SL deve fechar
    test2 = rm.should_close_position(sl, entry, sl, tp, 'BUY')
    checks.append(("Preço = SL (BUY) deve fechar", test2[0] and test2[1] == 'STOP_LOSS'))
    
    # Teste 3: Preço > TP deve fechar
    test3 = rm.should_close_position(tp + 0.001, entry, sl, tp, 'BUY')
    checks.append(("Preço > TP (BUY) deve fechar", test3[0] and test3[1] == 'TAKE_PROFIT'))
    
    # Teste 4: Preço = TP deve fechar
    test4 = rm.should_close_position(tp, entry, sl, tp, 'BUY')
    checks.append(("Preço = TP (BUY) deve fechar", test4[0] and test4[1] == 'TAKE_PROFIT'))
    
    # Teste 5: Preço no meio não deve fechar
    test5 = rm.should_close_position(entry, entry, sl, tp, 'BUY')
    checks.append(("Preço = Entrada (BUY) não fecha", not test5[0]))
    
    all_passed = True
    for desc, passed in checks:
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"  {status} | {desc}")
        if not passed:
            all_passed = False
    
    print()
    print("=" * 70)
    if all_passed:
        print("  ✅ TODAS AS VERIFICAÇÕES PASSARAM - Lógica de venda OK!")
    else:
        print("  ❌ ALGUMAS VERIFICAÇÕES FALHARAM - Revisar lógica!")
    print("=" * 70)
    
    # Status do monitoramento
    print("\n📡 STATUS DO MONITORAMENTO")
    print("-" * 70)
    
    if side == 'BUY':
        if current <= sl:
            print(f"  🔴 ALERTA: Preço ({current:.4f}) <= Stop Loss ({sl:.4f})")
            print("     → Bot DEVERIA estar fechando a posição!")
        elif current >= tp:
            print(f"  🟢 ALERTA: Preço ({current:.4f}) >= Take Profit ({tp:.4f})")
            print("     → Bot DEVERIA estar fechando a posição!")
        else:
            pct_to_sl = ((current - sl) / current) * 100
            pct_to_tp = ((tp - current) / current) * 100
            print("  ⏳ Posição ATIVA - aguardando trigger")
            print(f"     Para SL: -{pct_to_sl:.2f}% (${current - sl:.4f})")
            print(f"     Para TP: +{pct_to_tp:.2f}% (${tp - current:.4f})")
    
    client.close()


if __name__ == '__main__':
    asyncio.run(test_sell_decision())
