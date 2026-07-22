"""
Multi-exchange client compatibility layer.

Re-exports the ExchangeManager singleton as binance_manager for backward
compatibility. All exchange logic lives in exchange_client.py.
"""

from bot.exchange_client import (
    ExchangeCriticalError as BinanceCriticalError,
    ExchangeError as BinanceServiceError,
    ExchangeManager,
    ExchangeTransientError as BinanceTransientError,
    exchange_manager,
)

# Backward-compatible aliases
binance_manager = exchange_manager
BinanceClientManager = ExchangeManager
