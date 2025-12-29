#!/usr/bin/env python3
"""
Análise profunda da estratégia para identificar problemas.
"""
import asyncio
import os
import sys
from datetime import datetime, timezone
from collections import defaultdict

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), '.env'))


async def analyze():
    client = AsyncIOMotorClient(os.getenv('MONGO_URL', 'mongodb://localhost:27017'))
    db = client[os.getenv('DB_NAME', 'trading_bot')]
    
    trades = await db.trades.find().sort('closed_at', -1).to_list(100)
    
    print("=" * 80)
    print("              🔍 ANÁLISE PROFUNDA DA ESTRATÉGIA")
    print("=" * 80)
    
    if not trades:
        print("\nNenhum trade para analisar.")
        return
    
    # Métricas gerais
    total_trades = len(trades)
    wins = [t for t in trades if t.get('pnl', 0) > 0]
    losses = [t for t in trades if t.get('pnl', 0) <= 0]
    
    total_pnl = sum(t.get('pnl', 0) for t in trades)
    total_win = sum(t.get('pnl', 0) for t in wins)
    total_loss = sum(t.get('pnl', 0) for t in losses)
    
    avg_win = total_win / len(wins) if wins else 0
    avg_loss = total_loss / len(losses) if losses else 0
    
    win_rate = (len(wins) / total_trades) * 100
    
    print(f"\n📊 RESUMO GERAL ({total_trades} trades)")
    print("-" * 80)
    print(f"  Total PnL:        ${total_pnl:,.2f}")
    print(f"  Wins:             {len(wins)} ({win_rate:.1f}%)")
    print(f"  Losses:           {len(losses)} ({100-win_rate:.1f}%)")
    print(f"  Média Win:        ${avg_win:,.2f}")
    print(f"  Média Loss:       ${avg_loss:,.2f}")
    print(f"  Profit Factor:    {abs(total_win/total_loss):.2f}" if total_loss else "  N/A")
    
    # 🚨 PROBLEMA 1: Stop Loss vs Take Profit
    print(f"\n🚨 PROBLEMA 1: CONFIGURAÇÃO DE SL/TP")
    print("-" * 80)
    
    for t in trades:
        entry = t['entry_price']
        sl = t['stop_loss']
        tp = t['take_profit']
        
        # Calcular distâncias
        sl_dist = abs((sl - entry) / entry) * 100
        tp_dist = abs((tp - entry) / entry) * 100
        
        # Verificar se SL está no lado errado (acima do entry para BUY)
        sl_wrong_side = (t['side'] == 'BUY' and sl > entry) or (t['side'] == 'SELL' and sl < entry)
        
        if sl_wrong_side:
            print(f"  ❌ {t['symbol']}: SL NO LADO ERRADO!")
            print(f"     Entry: ${entry} | SL: ${sl} | Side: {t['side']}")
            print(f"     SL deveria ser ABAIXO do entry para BUY")
    
    # Análise de R/R
    print(f"\n📈 ANÁLISE DE RISK/REWARD")
    print("-" * 80)
    
    for t in trades:
        entry = t['entry_price']
        sl = t['stop_loss']
        tp = t['take_profit']
        pnl = t.get('pnl', 0)
        
        risk = abs(entry - sl)
        reward = abs(tp - entry)
        rr = reward / risk if risk > 0 else 0
        
        sl_pct = abs((sl - entry) / entry) * 100
        tp_pct = abs((tp - entry) / entry) * 100
        
        status = "🟢" if pnl > 0 else "🔴"
        rr_status = "✅" if rr >= 2 else "⚠️" if rr >= 1 else "❌"
        
        # Verificar inconsistências
        issues = []
        if t['side'] == 'BUY' and sl > entry:
            issues.append("SL>Entry")
        if rr < 1:
            issues.append(f"RR:{rr:.1f}")
        if sl_pct > 10:
            issues.append(f"SL muito largo:{sl_pct:.1f}%")
        
        issue_str = " | ".join(issues) if issues else ""
        
        print(f"  {status} {t['symbol']:10} | PnL: ${pnl:>8.2f} | SL:{sl_pct:>5.1f}% | TP:{tp_pct:>5.1f}% | RR 1:{rr:.1f} {rr_status} {issue_str}")
    
    # 🚨 PROBLEMA 2: Trailing Stop mal configurado
    print(f"\n🚨 PROBLEMA 2: TRAILING STOP")
    print("-" * 80)
    
    trailing_active = 0
    for t in trades:
        trailing = t.get('trailing', {})
        if trailing.get('active'):
            trailing_active += 1
            # Se o trailing ativou mas ainda perdeu, pode ser problema
            if t.get('pnl', 0) < 0:
                print(f"  ⚠️ {t['symbol']}: Trailing ATIVOU mas trade perdeu ${t.get('pnl', 0):.2f}")
    
    print(f"  Trades com trailing ativo: {trailing_active}/{total_trades}")
    
    # 🚨 PROBLEMA 3: Grandes perdas
    print(f"\n🚨 PROBLEMA 3: MAIORES PERDAS")
    print("-" * 80)
    
    big_losses = sorted([t for t in trades if t.get('pnl', 0) < -20], key=lambda x: x.get('pnl', 0))
    for t in big_losses[:5]:
        entry = t['entry_price']
        exit_p = t.get('exit_price', 0)
        sl = t['stop_loss']
        
        # O preço de saída está muito longe do SL?
        if t['side'] == 'BUY':
            sl_should_trigger = sl
            actual_exit = exit_p
            slippage = ((sl - exit_p) / sl) * 100 if sl > 0 else 0
        
        print(f"  💀 {t['symbol']}: Perdeu ${t.get('pnl', 0):.2f}")
        print(f"     Entry: ${entry:.4f} → Exit: ${exit_p:.4f}")
        print(f"     SL era: ${sl:.4f} | ROE: {t.get('roe', 0):.1f}%")
        if abs(exit_p - sl) / sl > 0.01:
            print(f"     ⚠️ SLIPPAGE: Saiu ${exit_p:.4f} vs SL ${sl:.4f}")
    
    # 🚨 PROBLEMA 4: Por símbolo
    print(f"\n🚨 PROBLEMA 4: PERFORMANCE POR SÍMBOLO")
    print("-" * 80)
    
    by_symbol = defaultdict(list)
    for t in trades:
        by_symbol[t['symbol']].append(t)
    
    for symbol, symbol_trades in sorted(by_symbol.items()):
        pnl = sum(t.get('pnl', 0) for t in symbol_trades)
        w = sum(1 for t in symbol_trades if t.get('pnl', 0) > 0)
        status = "🟢" if pnl > 0 else "🔴"
        print(f"  {status} {symbol:10}: {len(symbol_trades)} trades | PnL: ${pnl:>8.2f} | Wins: {w}/{len(symbol_trades)}")
    
    # 🔧 DIAGNÓSTICO FINAL
    print(f"\n" + "=" * 80)
    print("              💡 DIAGNÓSTICO E RECOMENDAÇÕES")
    print("=" * 80)
    
    problems = []
    
    # Verificar SL no lado errado
    sl_wrong = sum(1 for t in trades if (t['side'] == 'BUY' and t['stop_loss'] > t['entry_price']))
    if sl_wrong > 0:
        problems.append(f"❌ CRÍTICO: {sl_wrong} trades com Stop Loss ACIMA do entry (deveria ser abaixo para BUY)")
    
    # Verificar R/R ruim
    bad_rr = sum(1 for t in trades if abs(t['take_profit'] - t['entry_price']) / abs(t['entry_price'] - t['stop_loss']) < 1.5)
    if bad_rr > total_trades * 0.5:
        problems.append(f"⚠️ {bad_rr}/{total_trades} trades com Risk/Reward < 1.5")
    
    # Win rate baixo
    if win_rate < 40:
        problems.append(f"⚠️ Win rate muito baixo: {win_rate:.1f}%")
    
    # Média de loss maior que win
    if abs(avg_loss) > abs(avg_win):
        problems.append(f"⚠️ Perdas médias (${abs(avg_loss):.2f}) maiores que ganhos médios (${avg_win:.2f})")
    
    if problems:
        for p in problems:
            print(f"\n  {p}")
    else:
        print("\n  ✅ Nenhum problema crítico identificado")
    
    print(f"\n📋 RECOMENDAÇÕES:")
    print("-" * 80)
    print("  1. VERIFICAR CÁLCULO DO STOP LOSS - parece estar invertido em alguns trades")
    print("  2. Aumentar distância do TP para melhorar R/R (mínimo 1:2)")
    print("  3. Revisar lógica do trailing stop - está ativando mas não protegendo")
    print("  4. Considerar filtrar símbolos com histórico ruim")
    print()
    print("=" * 80)
    
    client.close()


if __name__ == '__main__':
    asyncio.run(analyze())
