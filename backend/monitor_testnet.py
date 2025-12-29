"""
Script de monitoramento contínuo para validação das correções no testnet.
Monitora métricas-chave: Profit Factor, Win Rate, Trades/dia, Perda máxima.
"""
import os
from datetime import datetime, timedelta
from pymongo import MongoClient
from dotenv import load_dotenv

load_dotenv()

MONGO_URL = os.getenv("MONGO_URL", "mongodb://localhost:27017")
DB_NAME = os.getenv("DB_NAME", "trading_bot")

def get_testnet_stats(days=7):
    """Obtém estatísticas do período de testnet."""
    client = MongoClient(MONGO_URL)
    db = client[DB_NAME]
    
    # Data de início do período
    cutoff = datetime.now() - timedelta(days=days)
    
    # Buscar trades fechados no período
    trades = list(db.trades.find({
        "status": "closed",
        "closed_at": {"$gte": cutoff}
    }).sort("closed_at", -1))
    
    if not trades:
        return {
            "total_trades": 0,
            "message": "Nenhum trade fechado no período de testnet ainda"
        }
    
    # Calcular métricas
    total_trades = len(trades)
    wins = [t for t in trades if t.get("pnl", 0) > 0]
    losses = [t for t in trades if t.get("pnl", 0) < 0]
    
    win_count = len(wins)
    loss_count = len(losses)
    win_rate = (win_count / total_trades * 100) if total_trades > 0 else 0
    
    gross_profit = sum(t.get("pnl", 0) for t in wins)
    gross_loss = abs(sum(t.get("pnl", 0) for t in losses))
    
    profit_factor = gross_profit / gross_loss if gross_loss > 0 else float('inf')
    
    total_pnl = sum(t.get("pnl", 0) for t in trades)
    
    # Trades por dia
    dias_com_trades = len(set(t["closed_at"].date() for t in trades))
    trades_per_day = total_trades / dias_com_trades if dias_com_trades > 0 else 0
    
    # Maior perda individual
    worst_loss = min((t.get("pnl", 0) for t in trades), default=0)
    worst_trade = next((t for t in trades if t.get("pnl", 0) == worst_loss), None)
    
    # Status das metas
    metas = {
        "profit_factor": {
            "atual": round(profit_factor, 2),
            "meta": 1.5,
            "status": "✅" if profit_factor >= 1.5 else "❌"
        },
        "win_rate": {
            "atual": round(win_rate, 1),
            "meta": 50.0,
            "status": "✅" if win_rate >= 50.0 else "❌"
        },
        "trades_dia": {
            "atual": round(trades_per_day, 1),
            "meta": "≤ 5",
            "status": "✅" if trades_per_day <= 5 else "❌"
        },
        "perda_max": {
            "atual": round(worst_loss, 2),
            "meta": "> -50",
            "status": "✅" if worst_loss > -50 else "❌"
        }
    }
    
    return {
        "periodo_dias": days,
        "total_trades": total_trades,
        "dias_com_trades": dias_com_trades,
        "trades_per_day": round(trades_per_day, 1),
        "win_rate": round(win_rate, 1),
        "wins": win_count,
        "losses": loss_count,
        "profit_factor": round(profit_factor, 2),
        "gross_profit": round(gross_profit, 2),
        "gross_loss": round(gross_loss, 2),
        "total_pnl": round(total_pnl, 2),
        "worst_loss": round(worst_loss, 2),
        "worst_symbol": worst_trade.get("symbol", "N/A") if worst_trade else "N/A",
        "metas": metas,
        "ultimos_5": [
            {
                "symbol": t.get("symbol"),
                "side": t.get("side"),
                "pnl": round(t.get("pnl", 0), 2),
                "close_reason": t.get("close_reason"),
                "closed_at": t.get("closed_at").strftime("%Y-%m-%d %H:%M")
            }
            for t in trades[:5]
        ]
    }

def print_stats():
    """Imprime estatísticas formatadas."""
    print("\n" + "="*70)
    print("🧪 MONITORAMENTO TESTNET - VALIDAÇÃO DAS CORREÇÕES")
    print("="*70)
    
    stats = get_testnet_stats(days=7)
    
    if "message" in stats:
        print(f"\n⏳ {stats['message']}")
        print("\n💡 O bot está rodando. Aguarde os primeiros trades fecharem...")
        return
    
    print(f"\n📊 PERÍODO: Últimos {stats['periodo_dias']} dias")
    print(f"📈 TOTAL DE TRADES: {stats['total_trades']} ({stats['dias_com_trades']} dias)")
    print(f"📉 TRADES/DIA: {stats['trades_per_day']}")
    
    print("\n🎯 MÉTRICAS vs METAS:")
    print("-" * 70)
    
    for nome, dados in stats['metas'].items():
        nome_display = nome.replace("_", " ").upper()
        print(f"{dados['status']} {nome_display:15} | Atual: {dados['atual']:>8} | Meta: {dados['meta']:>8}")
    
    print("\n💰 PERFORMANCE:")
    print("-" * 70)
    print(f"Win Rate:       {stats['win_rate']}% ({stats['wins']}W / {stats['losses']}L)")
    print(f"Profit Factor:  {stats['profit_factor']}")
    print(f"Gross Profit:   {stats['gross_profit']} USDT")
    print(f"Gross Loss:     {stats['gross_loss']} USDT")
    print(f"PnL Total:      {stats['total_pnl']} USDT")
    print(f"Pior Trade:     {stats['worst_loss']} USDT ({stats['worst_symbol']})")
    
    print("\n📋 ÚLTIMOS 5 TRADES:")
    print("-" * 70)
    for t in stats['ultimos_5']:
        pnl_color = "+" if t['pnl'] > 0 else ""
        print(f"{t['closed_at']} | {t['symbol']:10} {t['side']:4} | PnL: {pnl_color}{t['pnl']:>8} | {t['close_reason']}")
    
    # Análise de progresso
    print("\n📈 ANÁLISE DE PROGRESSO:")
    print("-" * 70)
    
    metas_ok = sum(1 for m in stats['metas'].values() if m['status'] == "✅")
    total_metas = len(stats['metas'])
    
    if metas_ok == total_metas:
        print("🎉 TODAS AS METAS ATINGIDAS! Bot pronto para produção.")
        print("\n✅ PRÓXIMO PASSO: Desativar testnet no .env:")
        print("   BINANCE_TESTNET=false")
    elif metas_ok >= total_metas / 2:
        print(f"⚠️  {metas_ok}/{total_metas} metas atingidas. Progresso bom, mas continue monitorando.")
        print(f"   Ainda faltam {total_metas - metas_ok} meta(s) para validação completa.")
    else:
        print(f"❌ Apenas {metas_ok}/{total_metas} metas atingidas.")
        print("   Correções podem precisar de ajustes adicionais.")
        print("   Aguarde mais trades ou revise parâmetros.")
    
    print("\n" + "="*70)
    print(f"⏰ Última atualização: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*70 + "\n")

if __name__ == "__main__":
    print_stats()
