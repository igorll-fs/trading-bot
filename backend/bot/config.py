from __future__ import annotations

"""Centralized configuration helpers for the trading bot."""

import os
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Mapping, Optional

CONFIG_COLLECTION = "configs"
CONFIG_DOCUMENT_FILTER = {"type": "bot_config"}
DEFAULT_SELECTOR_BASE_SYMBOLS = [
    "BTCUSDT",
    "ETHUSDT",
    "BNBUSDT",
    "SOLUSDT",
    "XRPUSDT",
    "ADAUSDT",
    "DOGEUSDT",
    "AVAXUSDT",
    "DOTUSDT",
    "POLUSDT",
    "LINKUSDT",
    "ATOMUSDT",
    "LTCUSDT",
    "UNIUSDT",
    "NEARUSDT",
]

# Limiares de liquidez (spread/volume)
DEFAULT_SELECTOR_MIN_QUOTE_VOLUME = 50_000.0  # volume mínimo no timeframe configurado (USDT)
DEFAULT_SELECTOR_MAX_SPREAD_PERCENT = 0.25     # spread máximo aceitável (percentual)


def _default_selector_symbols() -> List[str]:
    return DEFAULT_SELECTOR_BASE_SYMBOLS.copy()


@dataclass
class BotConfig:
    """Represents the persisted settings required by the trading bot."""

    binance_api_key: str = ""
    binance_api_secret: str = ""
    binance_testnet: bool = True
    telegram_bot_token: str = ""
    telegram_chat_id: str = ""
    telegram_verify_ssl: bool = True
    max_positions: int = 2  # CORREÇÃO: Reduzido de 3 para 2 (mais conservador)
    risk_percentage: float = 1.5  # CORREÇÃO: Reduzido de 2.0 para 1.5 (arriscar menos por trade)
    leverage: int = 1
    balance_cache_ttl: float = 30.0
    observation_alert_interval: float = 300.0
    strategy_timeframe: str = "15m"
    strategy_confirmation_timeframe: str = "1h"
    strategy_klines_limit: int = 200
    strategy_min_signal_strength: int = 80  # CORREÇÃO: Aumentado de 60 para 80
    selector_base_symbols: List[str] = field(default_factory=_default_selector_symbols)
    selector_trending_refresh_interval: int = 120
    selector_min_change_percent: float = 1.0  # CORREÇÃO: Aumentado de 0.5 para 1.0 (mais momentum)
    selector_trending_pool_size: int = 10
    selector_min_quote_volume: float = 100_000.0  # CORREÇÃO: Aumentado de 50k para 100k (liquidez)
    selector_max_spread_percent: float = DEFAULT_SELECTOR_MAX_SPREAD_PERCENT
    risk_stop_loss_percentage: float = 1.2  # CORREÇÃO: Reduzido de 1.5 para 1.2 (stops mais apertados)
    risk_reward_ratio: float = 2.5  # CORREÇÃO: Aumentado de 2.0 para 2.5 (melhor R/R)
    risk_trailing_activation: float = 0.75
    risk_trailing_step: float = 0.5
    loop_interval_seconds: float = 15.0
    risk_use_position_cap: bool = True
    daily_drawdown_limit_pct: float = 0.0
    weekly_drawdown_limit_pct: float = 0.0
    extra: Dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_mapping(cls, data: Optional[Mapping[str, Any]]) -> "BotConfig":
        if not data:
            return cls()

        known_fields = {
            "binance_api_key",
            "binance_api_secret",
            "binance_testnet",
            "telegram_bot_token",
            "telegram_chat_id",
            "max_positions",
            "risk_percentage",
            "leverage",
            "balance_cache_ttl",
            "observation_alert_interval",
            "telegram_verify_ssl",
            "strategy_timeframe",
            "strategy_confirmation_timeframe",
            "strategy_klines_limit",
            "strategy_min_signal_strength",
            "selector_base_symbols",
            "selector_trending_refresh_interval",
            "selector_min_change_percent",
            "selector_trending_pool_size",
            "selector_min_quote_volume",
            "selector_max_spread_percent",
            "risk_stop_loss_percentage",
            "risk_reward_ratio",
            "risk_trailing_activation",
            "risk_trailing_step",
            "loop_interval_seconds",
            "risk_use_position_cap",
            "daily_drawdown_limit_pct",
            "weekly_drawdown_limit_pct",
        }

        kwargs = {field: data[field] for field in known_fields if field in data}
        extras = {key: value for key, value in data.items() if key not in known_fields}
        return cls(**kwargs, extra=extras)

    @classmethod
    def from_env(cls) -> "BotConfig":
        """Create a config instance using environment defaults."""
        return cls(
            binance_api_key=os.getenv("BINANCE_API_KEY", ""),
            binance_api_secret=os.getenv("BINANCE_API_SECRET", ""),
            binance_testnet=_str_to_bool(os.getenv("BINANCE_TESTNET", "true")),
            telegram_bot_token=os.getenv("TELEGRAM_BOT_TOKEN", ""),
            telegram_chat_id=os.getenv("TELEGRAM_CHAT_ID", ""),
            telegram_verify_ssl=_str_to_bool(os.getenv("TELEGRAM_VERIFY_SSL", "true")),
            max_positions=_to_int(os.getenv("MAX_POSITIONS", 3), default=3, minimum=1),
            risk_percentage=_to_float(os.getenv("RISK_PERCENTAGE", 2.0), default=2.0, minimum=0.1),
            leverage=_to_int(os.getenv("LEVERAGE", 1), default=1, minimum=1),
            balance_cache_ttl=_to_float(os.getenv("BALANCE_CACHE_TTL", 30.0), default=30.0, minimum=1.0),
            observation_alert_interval=_to_float(
                os.getenv("OBSERVATION_ALERT_INTERVAL", 300.0),
                default=300.0,
                minimum=30.0,
            ),
            strategy_timeframe=os.getenv("STRATEGY_TIMEFRAME", "15m"),
            strategy_confirmation_timeframe=os.getenv("STRATEGY_CONFIRMATION_TIMEFRAME", "1h"),
            strategy_klines_limit=_to_int(os.getenv("STRATEGY_KLINES_LIMIT", 200), default=200, minimum=10),
            strategy_min_signal_strength=_to_int(
                os.getenv("STRATEGY_MIN_SIGNAL_STRENGTH", 60),
                default=60,
                minimum=0,
            ),
            selector_base_symbols=_parse_symbol_list(os.getenv("SELECTOR_BASE_SYMBOLS")),
            selector_trending_refresh_interval=_to_int(
                os.getenv("SELECTOR_TRENDING_REFRESH_INTERVAL", 120),
                default=120,
                minimum=30,
            ),
            selector_min_change_percent=_to_float(
                os.getenv("SELECTOR_MIN_CHANGE_PERCENT", 0.5),
                default=0.5,
                minimum=0.0,
            ),
            selector_trending_pool_size=_to_int(
                os.getenv("SELECTOR_TRENDING_POOL_SIZE", 10),
                default=10,
                minimum=1,
            ),
            selector_min_quote_volume=_to_float(
                os.getenv("SELECTOR_MIN_QUOTE_VOLUME", DEFAULT_SELECTOR_MIN_QUOTE_VOLUME),
                default=DEFAULT_SELECTOR_MIN_QUOTE_VOLUME,
                minimum=0.0,
            ),
            selector_max_spread_percent=_to_float(
                os.getenv("SELECTOR_MAX_SPREAD_PERCENT", DEFAULT_SELECTOR_MAX_SPREAD_PERCENT),
                default=DEFAULT_SELECTOR_MAX_SPREAD_PERCENT,
                minimum=0.0,
            ),
            risk_stop_loss_percentage=_to_float(
                os.getenv("RISK_STOP_LOSS_PERCENTAGE", 1.5),
                default=1.5,
                minimum=0.1,
            ),
            risk_reward_ratio=_to_float(
                os.getenv("RISK_REWARD_RATIO", 2.0),
                default=2.0,
                minimum=0.5,
            ),
            risk_trailing_activation=_to_float(
                os.getenv("RISK_TRAILING_ACTIVATION", 0.75),
                default=0.75,
                minimum=0.0,
            ),
            risk_trailing_step=_to_float(
                os.getenv("RISK_TRAILING_STEP", 0.5),
                default=0.5,
                minimum=0.0,
            ),
            loop_interval_seconds=_to_float(
                os.getenv("LOOP_INTERVAL_SECONDS", 15.0),
                default=15.0,
                minimum=5.0,
            ),
            risk_use_position_cap=_str_to_bool(os.getenv("RISK_USE_POSITION_CAP", "true")),
            daily_drawdown_limit_pct=_to_float(os.getenv("DAILY_DRAWDOWN_LIMIT_PCT", 0.0), default=0.0, minimum=0.0),
            weekly_drawdown_limit_pct=_to_float(os.getenv("WEEKLY_DRAWDOWN_LIMIT_PCT", 0.0), default=0.0, minimum=0.0),
        )

    def sanitized(self) -> "BotConfig":
        """Return a defensive copy with normalized numeric ranges."""
        return BotConfig(
            binance_api_key=self.binance_api_key.strip(),
            binance_api_secret=self.binance_api_secret.strip(),
            binance_testnet=bool(self.binance_testnet),
            telegram_bot_token=self.telegram_bot_token.strip(),
            telegram_chat_id=str(self.telegram_chat_id).strip(),
            telegram_verify_ssl=bool(self.telegram_verify_ssl),
            max_positions=max(1, int(self.max_positions or 1)),
            risk_percentage=max(0.1, float(self.risk_percentage or 0.1)),
            leverage=max(1, int(self.leverage or 1)),
            balance_cache_ttl=max(1.0, float(self.balance_cache_ttl or 30.0)),
            observation_alert_interval=max(30.0, float(self.observation_alert_interval or 300.0)),
            strategy_timeframe=str(self.strategy_timeframe or "15m"),
            strategy_confirmation_timeframe=str(self.strategy_confirmation_timeframe or "1h"),
            strategy_klines_limit=max(10, int(self.strategy_klines_limit or 200)),
            strategy_min_signal_strength=max(0, min(100, int(self.strategy_min_signal_strength or 60))),
            selector_base_symbols=_sanitize_symbol_list(self.selector_base_symbols),
            selector_trending_refresh_interval=max(30, int(self.selector_trending_refresh_interval or 120)),
            selector_min_change_percent=max(0.0, float(self.selector_min_change_percent or 0.0)),
            selector_trending_pool_size=max(1, int(self.selector_trending_pool_size or 10)),
            selector_min_quote_volume=max(0.0, float(self.selector_min_quote_volume or DEFAULT_SELECTOR_MIN_QUOTE_VOLUME)),
            selector_max_spread_percent=max(0.0, float(self.selector_max_spread_percent or DEFAULT_SELECTOR_MAX_SPREAD_PERCENT)),
            risk_stop_loss_percentage=max(0.1, float(self.risk_stop_loss_percentage or 1.5)),
            risk_reward_ratio=max(0.5, float(self.risk_reward_ratio or 2.0)),
            risk_trailing_activation=max(0.0, float(self.risk_trailing_activation or 0.0)),
            risk_trailing_step=max(0.0, float(self.risk_trailing_step or 0.0)),
            loop_interval_seconds=max(5.0, float(self.loop_interval_seconds or 15.0)),
            risk_use_position_cap=bool(self.risk_use_position_cap),
            daily_drawdown_limit_pct=max(0.0, float(self.daily_drawdown_limit_pct or 0.0)),
            weekly_drawdown_limit_pct=max(0.0, float(self.weekly_drawdown_limit_pct or 0.0)),
            extra=self.extra.copy(),
        )

    def to_document(self) -> Dict[str, Any]:
        sanitized = self.sanitized()
        payload = asdict(sanitized)
        payload.update(self.extra)
        payload.update(CONFIG_DOCUMENT_FILTER)
        payload["updated_at"] = datetime.now(timezone.utc).isoformat()
        payload.pop("extra", None)
        return payload

    def to_public_dict(self) -> Dict[str, Any]:
        data = asdict(self)
        data.pop("extra", None)
        data.update(self.extra)
        return data


async def load_bot_config(db) -> BotConfig:
    """Fetch configuration from MongoDB, falling back to environment defaults."""
    document = await db[CONFIG_COLLECTION].find_one(CONFIG_DOCUMENT_FILTER, {"_id": 0})
    if document:
        return BotConfig.from_mapping(document).sanitized()
    return BotConfig.from_env()


async def save_bot_config(db, config: BotConfig) -> None:
    """Persist configuration to MongoDB."""
    await db[CONFIG_COLLECTION].update_one(
        CONFIG_DOCUMENT_FILTER,
        {"$set": config.to_document()},
        upsert=True,
    )


def _str_to_bool(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    return str(value).strip().lower() in {"1", "true", "yes", "y", "on"}


def _to_int(value: Any, *, default: int, minimum: int) -> int:
    try:
        return max(minimum, int(value))
    except (TypeError, ValueError):
        return default


def _to_float(value: Any, *, default: float, minimum: float) -> float:
    try:
        return max(minimum, float(value))
    except (TypeError, ValueError):
        return default


def _parse_symbol_list(value: Any) -> List[str]:
    if value is None or value == "":
        return _default_selector_symbols()
    if isinstance(value, list):
        candidates = value
    else:
        candidates = str(value).split(",")
    cleaned = [
        token.strip().upper()
        for token in candidates
        if isinstance(token, str) and token.strip()
    ]
    return cleaned or _default_selector_symbols()


def _sanitize_symbol_list(symbols: Any) -> List[str]:
    if isinstance(symbols, list):
        cleaned = [
            str(sym).strip().upper()
            for sym in symbols
            if str(sym).strip()
        ]
        return cleaned or _default_selector_symbols()
    return _default_selector_symbols()
