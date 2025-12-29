from pymongo import MongoClient
from datetime import datetime, timedelta
import os
import sys

# Adicionar path do backend
sys.path.insert(0, 'backend')

# Conectar MongoDB
mongo_url = os.getenv('MONGO_URL', 'mongodb://localhost:27017')
db_name = os.getenv('DB_NAME', 'trading_bot')

try:
    client = MongoClient(mongo_url, serverSelectionTimeoutMS=5000)
    db = client[db_name]
    
    # 1. TRADES POR DIA
    print('='*70)
    print('1. TRADES POR DIA (ultimos 30 dias)')
    print('='*70)
    
    pipeline_por_dia = [
        {'$match': {'status': 'closed'}},
        {'$project': {
            'date': {'$dateToString': {'format': '%Y-%m-%d', 'date': '$close_time'}}
        }},
        {'$group': {
            '_id': '$date',
            'count': {'$sum': 1}
        }},
        {'$sort': {'_id': -1}},
        {'$limit': 30}
    ]
    
    trades_por_dia = list(db.trades.aggregate(pipeline_por_dia))
    
    if trades_por_dia:
        total_trades = sum(t['count'] for t in trades_por_dia)
        dias_com_trades = len(trades_por_dia)
        media_por_dia = total_trades / dias_com_trades
        
        print(f'\nTotal de trades (30 dias): {total_trades}')
        print(f'Dias com trades: {dias_com_trades}')
        print(f'Media por dia: {media_por_dia:.1f} trades/dia')
        print(f'\nUltimos 10 dias:')
        for t in trades_por_dia[:10]:
            print(f"  {t['_id']}: {t['count']} trades")
    else:
        print('Nenhum trade fechado encontrado')
    
    # 2. WIN RATE
    print('\n' + '='*70)
    print('2. WIN RATE (% de trades lucrativos)')
    print('='*70)
    
    all_trades = list(db.trades.find({'status': 'closed'}).sort('close_time', -1))
    
    if all_trades:
        total = len(all_trades)
        lucrativos = sum(1 for t in all_trades if t.get('pnl', 0) > 0)
        prejuizo = sum(1 for t in all_trades if t.get('pnl', 0) < 0)
        neutros = sum(1 for t in all_trades if t.get('pnl', 0) == 0)
        
        win_rate = (lucrativos / total * 100) if total > 0 else 0
        
        print(f'\nTotal de trades fechados: {total}')
        print(f'Trades lucrativos: {lucrativos} ({lucrativos/total*100:.1f}%)')
        print(f'Trades com prejuizo: {prejuizo} ({prejuizo/total*100:.1f}%)')
        print(f'Trades neutros: {neutros}')
        print(f'\n>>> WIN RATE: {win_rate:.1f}%')
        
        # PnL total
        pnl_total = sum(t.get('pnl', 0) for t in all_trades)
        lucro_total = sum(t.get('pnl', 0) for t in all_trades if t.get('pnl', 0) > 0)
        prejuizo_total = sum(t.get('pnl', 0) for t in all_trades if t.get('pnl', 0) < 0)
        
        print(f'\nPnL Total: {pnl_total:.2f} USDT')
        print(f'Lucro acumulado: {lucro_total:.2f} USDT')
        print(f'Prejuizo acumulado: {prejuizo_total:.2f} USDT')
        
        if lucro_total > 0 and abs(prejuizo_total) > 0:
            profit_factor = lucro_total / abs(prejuizo_total)
            print(f'Profit Factor: {profit_factor:.3f}')
    
    # 3. ÚLTIMOS TRADES (LOG)
    print('\n' + '='*70)
    print('3. ULTIMOS 10 TRADES (LOG DETALHADO)')
    print('='*70)
    
    ultimos_trades = list(db.trades.find({'status': 'closed'}).sort('close_time', -1).limit(10))
    
    for i, trade in enumerate(ultimos_trades, 1):
        symbol = trade.get('symbol', 'N/A')
        side = trade.get('side', 'N/A')
        entry_price = trade.get('entry_price', 0)
        exit_price = trade.get('exit_price', 0)
        quantity = trade.get('quantity', 0)
        pnl = trade.get('pnl', 0)
        close_reason = trade.get('close_reason', 'N/A')
        open_time = trade.get('open_time', 'N/A')
        close_time = trade.get('close_time', 'N/A')
        
        status_emoji = 'OK' if pnl > 0 else 'LOSS' if pnl < 0 else 'NEUTRO'
        
        print(f'\n{i}. [{status_emoji}] {symbol} | {side.upper()}')
        print(f'   Entrada: {entry_price:.8f} | Saida: {exit_price:.8f}')
        print(f'   Quantidade: {quantity:.4f}')
        print(f'   PnL: {pnl:+.2f} USDT')
        print(f'   Fechamento: {close_reason}')
        print(f'   Aberto: {open_time}')
        print(f'   Fechado: {close_time}')
    
    print('\n' + '='*70)
    
except Exception as e:
    print(f'ERRO: {e}')
    import traceback
    traceback.print_exc()
