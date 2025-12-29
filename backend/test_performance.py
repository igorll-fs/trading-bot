"""Script para comparar performance com e sem cache de mercado."""

import asyncio
import statistics
import time
import logging

from bot.strategy import TradingStrategy
from bot.binance_client import binance_manager
from bot.market_cache import get_cache


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def test_performance() -> None:
    symbols = ['BTCUSDT', 'ETHUSDT', 'BNBUSDT', 'SOLUSDT', 'XRPUSDT']

    logger.info('=' * 60)
    logger.info('TESTE DE PERFORMANCE - CACHE DE MERCADO')
    logger.info('=' * 60)

    logger.info('Inicializando Binance...')
    if not binance_manager.initialize():
        logger.error('Não foi possível inicializar o cliente Binance.')
        return

    strategy = TradingStrategy(binance_manager.client)
    cache = get_cache()

    def measure(symbol_list):
        durations = []
        for symbol in symbol_list:
            start = time.perf_counter()
            _ = strategy.get_historical_data(symbol)
            elapsed = time.perf_counter() - start
            durations.append(elapsed)
            logger.info('  %s: %.3fs', symbol, elapsed)
        return durations

    # Teste 1: sem cache (primeira consulta)
    logger.info('\nTeste 1 - Primeira execução (sem cache)')
    cache.clear()
    times_no_cache = measure(symbols)
    avg_no_cache = statistics.mean(times_no_cache)
    logger.info('  Média sem cache: %.3fs', avg_no_cache)

    # Teste 2: com cache (segunda consulta)
    logger.info('\nTeste 2 - Segunda execução (com cache)')
    times_with_cache = measure(symbols)
    avg_with_cache = statistics.mean(times_with_cache)
    logger.info('  Média com cache: %.3fs', avg_with_cache)

    improvement = ((avg_no_cache - avg_with_cache) / avg_no_cache) * 100 if avg_no_cache else 0
    speedup = (avg_no_cache / avg_with_cache) if avg_with_cache else 0

    logger.info('\nResultados:')
    logger.info('  Tempo médio sem cache: %.3fs', avg_no_cache)
    logger.info('  Tempo médio com cache : %.3fs', avg_with_cache)
    logger.info('  Melhoria aproximada   : %.1f%%', improvement)
    logger.info('  Speedup estimado      : %.2fx', speedup)

    stats = cache.stats()
    logger.info('\nEstatísticas do cache: %s', stats)

    # Teste 3: análise completa
    logger.info('\nTeste 3 - Análise completa de símbolos (com cache)')
    start_full = time.perf_counter()
    for symbol in symbols:
        analysis = strategy.analyze_symbol(symbol)
        if analysis:
            logger.info('  %s -> %s (força %s)', symbol, analysis['signal'], analysis['strength'])
    total = time.perf_counter() - start_full
    logger.info('  Tempo total: %.2fs', total)
    logger.info('  Tempo por símbolo: %.2fs', total / len(symbols))

    estimated_15 = (total / len(symbols)) * 15
    logger.info('  Estimativa para 15 símbolos: %.2fs', estimated_15)


if __name__ == '__main__':
    asyncio.run(test_performance())

