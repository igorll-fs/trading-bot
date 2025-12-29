#!/usr/bin/env python3
"""
Análise completa da estratégia de trading.
"""
import asyncio
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv
import httpx

load_dotenv(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), '.env'))


async def get_price(symbol):
    async with httpx.AsyncClient() as client:
        resp = await client.get(f"https://testnet.binance.vision/api/v3/ticker/price?symbol={symbol}")
        return float(resp.json()['price'])


async def analyze():
    client = AsyncIOMotorClient(os.getenv('MONGO_URL', 'mongodb://localhost:27017'))
    db = client[os.getenv('DB_NAME', 'trading_bot')]
    
    print("=" * 70)
    print("            📊 ANÁLISE COMPLETA DA ESTRATÉGIA")
    print("=" * 70)
    
    # === CONFIG ===
    config = await db.configs.find_one({'_id': 'main'})
    print("\n🔧 CONFIGURAÇÕES ATUAIS")
    print("-" * 70)
    if config:
        print(f"  Signal Strength Mínimo:    {config.get('strategy_min_signal_strength', 'N/A')}")
        print(f"  Variação Mínima (%):       {config.get('selector_min_change_percent', 'N/A')}")
        print(f"  Confiança ML Mínima:       {config.get('min_confidence_score', 'N/A')}")
        print(f"  Stop Loss (%):             {config.get('stop_loss_percent', 'N/A')}")
        print(f"  Take Profit (%):           {config.get('take_profit_percent', 'N/A')}")
        print(f"  Máx Posição (%):           {config.get('max_position_percent', 'N/A')}")
    
    # === POSIÇÃO ABERTA ===
    pos = await db.positions.find_one({'status': 'open'})
    print("\n📈 POSIÇÃO ATUAL")
    print("-" * 70)
    if pos:
        current_price = await get_price(pos['symbol'])
        entry = pos['entry_price']
        sl = pos['stop_loss']
        tp = pos['take_profit']
        size = pos['position_size']
        ml_score = pos.get('ml_score', 0)
        
        pnl_pct = ((current_price - entry) / entry) * 100
        pnl_usd = size * (pnl_pct / 100)
        
        risk_pct = abs((sl - entry) / entry) * 100
        reward_pct = abs((tp - entry) / entry) * 100
        rr = reward_pct / risk_pct if risk_pct > 0 else 0
        
        print(f"  Par:                       {pos['symbol']}")
        print(f"  Direção:                   {pos['side']}")
        print(f"  Entrada:                   ${entry:.4f}")
        print(f"  Preço Atual:               ${current_price:.4f}")
        print(f"  Stop Loss:                 ${sl:.4f} (-{risk_pct:.2f}%)")
        print(f"  Take Profit:               ${tp:.4f} (+{reward_pct:.2f}%)")
        print(f"  Tamanho:                   ${size:.2f}")
        print(f"  ML Score:                  {ml_score:.2f}")
        print(f"  Risk/Reward:               1:{rr:.1f}")
        print(f"  P&L Atual:                 ${pnl_usd:+.2f} ({pnl_pct:+.2f}%)")
    else:
        print("  Nenhuma posição aberta")
    
    # === HISTÓRICO ===
    trades = await db.trades.find().sort('closed_at', -1).limit(20).to_list(20)
    print("\n📜 HISTÓRICO DE TRADES")
    print("-" * 70)
    if trades:
        wins = sum(1 for t in trades if t.get('pnl', 0) > 0)
        losses = len(trades) - wins
        total_pnl = sum(t.get('pnl', 0) for t in trades)
        avg_win = sum(t.get('pnl', 0) for t in trades if t.get('pnl', 0) > 0) / wins if wins > 0 else 0
        avg_loss = sum(t.get('pnl', 0) for t in trades if t.get('pnl', 0) <= 0) / losses if losses > 0 else 0
        
        print(f"  Total de Trades:           {len(trades)}")
        print(f"  Wins:                      {wins}")
        print(f"  Losses:                    {losses}")
        print(f"  Win Rate:                  {(wins/len(trades))*100:.1f}%")
        print(f"  Lucro Médio:               ${avg_win:.2f}")
        print(f"  Prejuízo Médio:            ${avg_loss:.2f}")
        print(f"  PnL Total:                 ${total_pnl:.2f}")
    else:
        print("  Nenhum trade fechado ainda (bot novo)")
    
    # === ML STATE ===
    ml = await db.ml_state.find_one({'_id': 'learning_system'})
    print("\n🤖 SISTEMA DE MACHINE LEARNING")
    print("-" * 70)
    if ml:
        params = ml.get('parameters', {})
        stats = ml.get('stats', {})
        print(f"  Confiança Mínima:          {params.get('min_confidence_score', 'N/A')}")
        print(f"  Multiplicador Posição:     {params.get('position_size_multiplier', 'N/A')}")
        print(f"  Multiplicador SL:          {params.get('stop_loss_multiplier', 'N/A')}")
        print(f"  Multiplicador TP:          {params.get('take_profit_multiplier', 'N/A')}")
        print(f"  Trades Aprendidos:         {stats.get('total_trades', 0)}")
        print(f"  Trades Vencedores:         {stats.get('winning_trades', 0)}")
    else:
        print("  ML ainda não salvou estado (bot novo)")
    
    # === AVALIAÇÃO ===
    print("\n" + "=" * 70)
    print("            💡 FEEDBACK DA ESTRATÉGIA")
    print("=" * 70)
    
    feedback = []
    score = 0
    max_score = 8
    
    # 1. Configurações de threshold
    if config:
        signal = config.get('strategy_min_signal_strength', 60)
        if signal <= 50:
            feedback.append("✅ Signal strength baixo (40-50) permite mais trades")
            score += 1
        elif signal > 70:
            feedback.append("⚠️ Signal strength alto (>70) pode filtrar demais")
        else:
            feedback.append("✅ Signal strength moderado (50-70)")
            score += 1
        
        conf = config.get('min_confidence_score', 0.5)
        if conf <= 0.35:
            feedback.append("✅ ML confidence baixa permite mais trades")
            score += 1
        elif conf > 0.6:
            feedback.append("⚠️ ML confidence alta pode perder oportunidades")
        else:
            feedback.append("✅ ML confidence balanceada")
            score += 1
    
    # 2. Risk/Reward da posição atual
    if pos:
        if rr >= 2.5:
            feedback.append("✅ Excelente R/R (>= 1:2.5)")
            score += 2
        elif rr >= 2.0:
            feedback.append("✅ Bom R/R (1:2.0)")
            score += 1
        else:
            feedback.append("⚠️ R/R poderia ser melhor (<1:2)")
        
        if ml_score >= 0.5:
            feedback.append("✅ ML score alto (>= 0.5) indica confiança")
            score += 1
        elif ml_score >= 0.35:
            feedback.append("🟡 ML score moderado (0.35-0.5)")
            score += 0.5
        else:
            feedback.append("⚠️ ML score baixo (<0.35)")
    
    # 3. Tamanho da posição
    if pos and config:
        balance_approx = 6667  # testnet balance
        pos_pct = (pos['position_size'] / balance_approx) * 100
        if pos_pct <= 30:
            feedback.append(f"✅ Tamanho conservador ({pos_pct:.0f}% do saldo)")
            score += 1
        elif pos_pct <= 40:
            feedback.append(f"🟡 Tamanho moderado ({pos_pct:.0f}% do saldo)")
            score += 0.5
        else:
            feedback.append(f"⚠️ Tamanho agressivo ({pos_pct:.0f}% do saldo)")
    
    # 4. Stop Loss
    if pos:
        if risk_pct <= 2:
            feedback.append(f"✅ Stop loss apertado ({risk_pct:.1f}%)")
            score += 1
        elif risk_pct <= 3:
            feedback.append(f"🟡 Stop loss moderado ({risk_pct:.1f}%)")
            score += 0.5
        else:
            feedback.append(f"⚠️ Stop loss largo ({risk_pct:.1f}%)")
    
    print()
    for f in feedback:
        print(f"  {f}")
    
    print()
    print("-" * 70)
    rating = (score / max_score) * 100
    if rating >= 75:
        emoji = "🌟"
        text = "ESTRATÉGIA EXCELENTE"
    elif rating >= 50:
        emoji = "👍"
        text = "ESTRATÉGIA BOA"
    elif rating >= 25:
        emoji = "🟡"
        text = "ESTRATÉGIA MODERADA"
    else:
        emoji = "⚠️"
        text = "ESTRATÉGIA PRECISA AJUSTES"
    
    print(f"  {emoji} RATING: {rating:.0f}% - {text}")
    print()
    
    # Recomendações
    print("📋 RECOMENDAÇÕES")
    print("-" * 70)
    
    if not trades:
        print("  1. Aguarde alguns trades fecharem para avaliar eficácia real")
        print("  2. Monitore se os trades estão atingindo TP ou SL")
        print("  3. Após 10+ trades, ajuste parâmetros ML baseado em resultados")
    else:
        wr = (wins/len(trades))*100
        if wr < 40:
            print("  1. Win rate baixo - considere aumentar signal_strength")
            print("  2. Revise condições de entrada (RSI, MACD, etc)")
        elif wr > 60:
            print("  1. Win rate bom - mantenha configurações")
            print("  2. Pode experimentar aumentar tamanho de posição")
        
        if total_pnl < 0:
            print("  3. PnL negativo - revise stops e gestão de risco")
    
    print()
    print("=" * 70)
    
    client.close()


if __name__ == '__main__':
    asyncio.run(analyze())
