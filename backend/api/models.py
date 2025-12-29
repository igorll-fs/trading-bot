"""
Modelos Pydantic para a API do Trading Bot.
"""

from pydantic import BaseModel, Field, ConfigDict
from typing import Optional

from bot.config import (
    DEFAULT_SELECTOR_MIN_QUOTE_VOLUME,
    DEFAULT_SELECTOR_MAX_SPREAD_PERCENT,
)


class ConfigModel(BaseModel):
    """Modelo para receber configuração do bot."""
    binance_api_key: str
    binance_api_secret: str
    binance_testnet: bool = True
    telegram_bot_token: str
    telegram_chat_id: str
    max_positions: int = 3
    risk_percentage: float = 2.0
    leverage: int = 1
    balance_cache_ttl: float = 30.0
    observation_alert_interval: float = 300.0
    risk_use_position_cap: bool = True
    daily_drawdown_limit_pct: float = 0.0
    weekly_drawdown_limit_pct: float = 0.0

    # Parâmetros configuráveis via dashboard (filtros de entrada e proteção)
    selector_min_quote_volume: float = DEFAULT_SELECTOR_MIN_QUOTE_VOLUME
    selector_max_spread_percent: float = DEFAULT_SELECTOR_MAX_SPREAD_PERCENT
    strategy_min_signal_strength: int = 60


class ConfigResponse(BaseModel):
    """Modelo de resposta para configuração."""
    model_config = ConfigDict(extra="ignore")
    
    binance_api_key: str = ""
    binance_api_secret: str = ""
    binance_testnet: bool = True
    telegram_bot_token: str = ""
    telegram_chat_id: str = ""
    max_positions: int = 3
    risk_percentage: float = 2.0
    leverage: int = 1
    balance_cache_ttl: float = 30.0
    observation_alert_interval: float = 300.0
    risk_use_position_cap: bool = True
    daily_drawdown_limit_pct: float = 0.0
    weekly_drawdown_limit_pct: float = 0.0

    selector_min_quote_volume: float = DEFAULT_SELECTOR_MIN_QUOTE_VOLUME
    selector_max_spread_percent: float = DEFAULT_SELECTOR_MAX_SPREAD_PERCENT
    strategy_min_signal_strength: int = 60


class BotControlRequest(BaseModel):
    """Modelo para controle do bot (start/stop)."""
    action: str  # "start" or "stop"


class SyncResponse(BaseModel):
    """Modelo de resposta para sincronização de conta."""
    status: str
    found_orders: int = Field(ge=0)
    canceled_orders: int = Field(ge=0)
    message: Optional[str] = None


class TradeResponse(BaseModel):
    """Modelo de resposta para trades."""
    model_config = ConfigDict(extra="ignore")
    
    symbol: str
    side: str
    entry_price: float
    exit_price: Optional[float] = None
    quantity: float
    position_size: float
    leverage: int
    pnl: Optional[float] = None
    roe: Optional[float] = None
    opened_at: str
    closed_at: Optional[str] = None
    status: str
