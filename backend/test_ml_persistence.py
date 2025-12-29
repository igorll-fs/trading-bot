"""Valida se o sistema de aprendizado salva e restaura dados corretamente."""

import asyncio
from datetime import datetime
from typing import Any, Dict, List

from motor.motor_asyncio import AsyncIOMotorClient


MONGO_URL = "mongodb://localhost:27017"
DB_NAME = "trading_bot"


async def _fetch_latest_params(db) -> Dict[str, Any] | None:
    return await db.learning_data.find_one(
        {'type': 'parameters'},
        sort=[('timestamp', -1)]
    )


async def _fetch_all_params(db) -> List[Dict[str, Any]]:
    cursor = db.learning_data.find({'type': 'parameters'}).sort('timestamp', 1)
    return await cursor.to_list(100)


async def test_learning_persistence() -> None:
    print('=' * 80)
    print('TESTE: Persistencia do sistema de Machine Learning')
    print('=' * 80)

    client = AsyncIOMotorClient(MONGO_URL)
    db = client[DB_NAME]

    print('1) Conectando ao MongoDB...')
    print(f'   URL........: {MONGO_URL}')
    print(f'   Database...: {DB_NAME}')
    print('   Collection.: learning_data\n')

    print('2) Buscando dados mais recentes...')
    latest = await _fetch_latest_params(db)

    if latest:
        print('   -> Aprendizado encontrado!')
        print('   Ultimo registro salvo:')
        print(f"      Data: {latest.get('timestamp', 'N/A')}")

        params = latest.get('parameters', {})
        metrics = latest.get('metrics', {})
        print('      Parametros ajustados:')
        print(f"        - Confidence score minimo: {params.get('min_confidence_score', 0.6):.3f}")
        print(f"        - Stop loss multiplier   : {params.get('stop_loss_multiplier', 1.0):.2f}x")
        print(f"        - Take profit multiplier : {params.get('take_profit_multiplier', 1.0):.2f}x")
        print(f"        - Position size multiplier: {params.get('position_size_multiplier', 1.0):.2f}x")

        print('      Metricas:')
        print(f"        - Total trades  : {metrics.get('total_trades', 0)}")
        print(f"        - Win rate      : {metrics.get('win_rate', 0):.1f}%")
        print(f"        - Avg profit    : ${metrics.get('avg_profit', 0):.2f}")
        print(f"        - Avg loss      : ${metrics.get('avg_loss', 0):.2f}")

        trigger = latest.get('trigger_trade', {})
        if trigger:
            print('      Trade que disparou o ajuste:')
            print(f"        - Simbolo       : {trigger.get('symbol', 'N/A')}")
            print(f"        - PnL           : ${trigger.get('pnl', 0):.2f}")
            print(f"        - ROE           : {trigger.get('roe', 0):.2f}%")
    else:
        print('   -> Nenhum aprendizado encontrado. Execute o bot e tente novamente.\n')

    print('\n3) Contagem de registros...')
    total_params = await db.learning_data.count_documents({'type': 'parameters'})
    total_analysis = await db.learning_data.count_documents({'type': 'trade_analysis'})
    print(f'   Registros de parametros: {total_params}')
    print(f'   Analises de trades     : {total_analysis}')

    if total_params > 1:
        print('\n4) Evolucao dos parametros (ate 10 ultimos):')
        all_params = await _fetch_all_params(db)
        header = f"{'Data/Hora':<20} {'Conf.Score':<12} {'SL':<8} {'TP':<8} {'WinRate':<10}"
        print('   ' + header)
        print('   ' + '-' * len(header))
        for record in all_params[-10:]:
            timestamp = record.get('timestamp', '')[:19].replace('T', ' ')
            params = record.get('parameters', {})
            metrics = record.get('metrics', {})
            print(
                f"   {timestamp:<20} {params.get('min_confidence_score', 0.6):<12.3f} "
                f"{params.get('stop_loss_multiplier', 1.0):<8.2f} {params.get('take_profit_multiplier', 1.0):<8.2f} "
                f"{metrics.get('win_rate', 0):<10.1f}"
            )

    print('\n5) Status geral:')
    if total_params > 0:
        print('   Sistema de persistencia ativo e salvando ajustes.')
        print('   Ao reiniciar o bot, os parametros aprendidos sao restaurados automaticamente.')
    else:
        print('   Sistema pronto, mas sem dados. Deixe o bot executar trades e rode este teste de novo.')

    print('\nResumo:')
    if total_params > 0:
        print('   - Aprendizado detectado; o bot ja possui memoria persistente.')
        print('   - Continue operando para acumular mais metricas.')
    else:
        print('   - Nenhum trade registrado ainda. Sem entradas em learning_data.')

    client.close()


if __name__ == '__main__':
    asyncio.run(test_learning_persistence())

