"""
Script para verificar o sistema de aprendizado do bot
"""
import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
import os
from dotenv import load_dotenv

load_dotenv()

async def check_learning():
    client = AsyncIOMotorClient(os.getenv('MONGO_URL', 'mongodb://localhost:27017'))
    db = client[os.getenv('DB_NAME', 'trading_bot')]
    
    print("=" * 60)
    print("ANALISE DO SISTEMA DE APRENDIZADO DO BOT")
    print("=" * 60)
    
    # Verificar parametros aprendidos
    params = await db.learning_data.find_one({'type': 'parameters'}, sort=[('timestamp', -1)])
    
    if params:
        print("\n📚 PARAMETROS APRENDIDOS (mais recentes):")
        print("-" * 40)
        print(f"  Timestamp: {params.get('timestamp', 'N/A')}")
        
        metrics = params.get('metrics', {})
        print(f"  Total de Trades: {metrics.get('total_trades', 0)}")
        print(f"  Win Rate: {metrics.get('win_rate', 0):.1f}%")
        print(f"  Trades Vencedores: {metrics.get('winning_trades', 0)}")
        print(f"  Trades Perdedores: {metrics.get('losing_trades', 0)}")
        print(f"  Lucro Medio: ${metrics.get('avg_profit', 0):.2f}")
        print(f"  Perda Media: ${metrics.get('avg_loss', 0):.2f}")
        
        print("\n🎯 Parametros Ajustados pelo ML:")
        print("-" * 40)
        for k, v in params.get('parameters', {}).items():
            # Valor padrao para comparacao
            defaults = {
                'min_confidence_score': 0.5,
                'stop_loss_multiplier': 1.0,
                'take_profit_multiplier': 1.0,
                'position_size_multiplier': 1.0,
            }
            default = defaults.get(k, 'N/A')
            diff = ""
            if isinstance(v, (int, float)) and isinstance(default, (int, float)):
                change = ((v - default) / default) * 100
                if change > 0:
                    diff = f" (+{change:.1f}%)"
                elif change < 0:
                    diff = f" ({change:.1f}%)"
            print(f"  {k}: {v:.3f} (padrao: {default}){diff}")
        
        trigger = params.get('trigger_trade', {})
        if trigger:
            print(f"\n  Ultimo trade que triggou ajuste:")
            print(f"    Symbol: {trigger.get('symbol', 'N/A')}")
            print(f"    PnL: ${trigger.get('pnl', 0):.2f}")
            print(f"    ROE: {trigger.get('roe', 0):.2f}%")
    else:
        print("\n⚠️ Nenhum parametro aprendido encontrado!")
        print("   O bot ainda nao teve trades suficientes para aprender.")
    
    # Contar registros
    total_params = await db.learning_data.count_documents({'type': 'parameters'})
    total_analyses = await db.learning_data.count_documents({'type': 'trade_analysis'})
    total_trades = await db.trades.count_documents({})
    
    print("\n📊 ESTATISTICAS GERAIS:")
    print("-" * 40)
    print(f"  Total de trades no historico: {total_trades}")
    print(f"  Total de ajustes de parametros: {total_params}")
    print(f"  Total de analises de trade: {total_analyses}")
    
    # Verificar se o learning system esta ativo
    min_trades = int(os.getenv("LEARNING_MIN_TRADES", "20"))
    mode = os.getenv("BOT_LEARNING_MODE", "active")
    
    print(f"\n⚙️ CONFIGURACAO:")
    print("-" * 40)
    print(f"  Modo: {mode}")
    print(f"  Trades minimos para ajuste: {min_trades}")
    print(f"  Fator de suavizacao: {os.getenv('LEARNING_SMOOTHING_FACTOR', '0.15')}")
    
    if total_trades < min_trades:
        print(f"\n⏳ O bot precisa de {min_trades - total_trades} trades a mais para comecar a ajustar parametros.")
    else:
        print(f"\n✅ O bot ja tem trades suficientes e esta ajustando parametros automaticamente!")
    
    # Mostrar ultimas analises
    analyses = await db.learning_data.find({'type': 'trade_analysis'}).sort('analyzed_at', -1).limit(5).to_list(5)
    if analyses:
        print("\n📝 ULTIMAS 5 ANALISES DE TRADES:")
        print("-" * 40)
        for a in analyses:
            lessons = a.get('lessons_learned', {})
            symbol = a.get('symbol', 'N/A')
            pnl = a.get('pnl', 0)
            result = lessons.get('result', 'N/A')
            quality = lessons.get('quality', 'N/A')
            timing = lessons.get('timing', 'N/A')
            print(f"  {symbol}: ${pnl:+.2f} | {result} | {quality}")
    
    # Mostrar evolucao dos parametros ao longo do tempo
    param_history = await db.learning_data.find({'type': 'parameters'}).sort('timestamp', -1).limit(10).to_list(10)
    if len(param_history) > 1:
        print("\n📈 EVOLUCAO DOS PARAMETROS (ultimos 10 ajustes):")
        print("-" * 40)
        print(f"  {'Timestamp':<25} | {'Conf':<6} | {'SL':<6} | {'TP':<6} | {'Size':<6} | {'WinRate':<8}")
        print("-" * 75)
        for p in reversed(param_history):
            ts = p.get('timestamp', 'N/A')[:19] if p.get('timestamp') else 'N/A'
            params = p.get('parameters', {})
            metrics = p.get('metrics', {})
            print(f"  {ts:<25} | {params.get('min_confidence_score', 0):.3f} | {params.get('stop_loss_multiplier', 0):.3f} | {params.get('take_profit_multiplier', 0):.3f} | {params.get('position_size_multiplier', 0):.3f} | {metrics.get('win_rate', 0):.1f}%")
    
    print("\n" + "=" * 60)
    
    client.close()

if __name__ == "__main__":
    asyncio.run(check_learning())
