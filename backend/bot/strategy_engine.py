"""
Strategy Engine — multi-strategy framework with regime-based selection.

Architecture:
  BaseStrategy      ← all strategies inherit from this
  StrategyEngine    ← manages strategies, routes by regime, picks best signal

Market Regimes (detected via ADX + ATR + volatility):
  - trending  → TrendFollowing, Breakout strategies
  - ranging   → MeanReversion, GridDCA strategies
  - volatile  → Breakout, ML strategies
"""

from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any

import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)


# ═══════════════════════════════════════════════════════════════════════
# Market Regime Detection
# ═══════════════════════════════════════════════════════════════════════

@dataclass
class MarketRegime:
    """Detected market regime for a given symbol."""
    regime: str           # trending, ranging, volatile
    adx: float            # ADX(14)
    atr_pct: float        # ATR as % of price
    volatility_percentile: float  # 0-100 where current vol sits vs 30-period history
    bb_width_pct: float   # Bollinger Band width as % of middle
    direction: str        # up, down, neutral (only meaningful for trending)


def detect_regime(df: pd.DataFrame) -> MarketRegime:
    """Detect market regime from OHLCV DataFrame with indicators.

    Uses:
      - ADX: trending vs ranging (threshold 25)
      - ATR/price %: volatility context
      - BB width percentile: squeeze vs expansion
      - EMA slope: direction in trending regimes

    Returns MarketRegime dataclass.
    """
    try:
        if len(df) < 30:
            return MarketRegime("ranging", 20.0, 1.0, 50.0, 3.0, "neutral")

        latest = df.iloc[-1]
        adx = float(latest.get("adx", 20.0)) if not pd.isna(latest.get("adx", np.nan)) else 20.0
        atr = float(latest.get("atr", 0.0)) if not pd.isna(latest.get("atr", np.nan)) else 0.0
        close = float(latest["close"])
        atr_pct = (atr / close) * 100 if close > 0 else 1.0

        # Bollinger Band width
        bb_upper = latest.get("bb_upper")
        bb_lower = latest.get("bb_lower")
        bb_middle = latest.get("bb_middle", close)
        if (
            bb_upper is not None and bb_lower is not None
            and not pd.isna(bb_upper) and not pd.isna(bb_lower)
            and bb_middle > 0
        ):
            bb_width_pct = ((float(bb_upper) - float(bb_lower)) / float(bb_middle)) * 100
        else:
            bb_width_pct = 3.0

        # Volatility percentile (where current ATR sits in 30-period history)
        atr_series = df.get("atr")
        if atr_series is not None and len(atr_series.dropna()) >= 20:
            atr_values = atr_series.dropna().tail(30).values
            volatility_percentile = (np.sum(atr_values <= atr) / len(atr_values)) * 100
        else:
            volatility_percentile = 50.0

        # Direction
        ema_12 = latest.get("ema_fast")
        ema_26 = latest.get("ema_slow")
        if ema_12 is not None and ema_26 is not None and not pd.isna(ema_12) and not pd.isna(ema_26):
            if float(ema_12) > float(ema_26) * 1.005:
                direction = "up"
            elif float(ema_12) < float(ema_26) * 0.995:
                direction = "down"
            else:
                direction = "neutral"
        else:
            direction = "neutral"

        # Classify regime
        if adx >= 30 and atr_pct >= 2.0:
            regime = "volatile"  # Strong trend + high volatility → volatile breakout
        elif adx >= 25:
            regime = "trending"
        elif atr_pct >= 3.0 or bb_width_pct > 6.0:
            regime = "volatile"
        else:
            regime = "ranging"

        return MarketRegime(
            regime=regime,
            adx=round(adx, 1),
            atr_pct=round(atr_pct, 2),
            volatility_percentile=round(volatility_percentile, 1),
            bb_width_pct=round(bb_width_pct, 2),
            direction=direction,
        )
    except Exception as e:
        logger.warning("Error detecting regime: %s", e)
        return MarketRegime("ranging", 20.0, 1.0, 50.0, 3.0, "neutral")


# ═══════════════════════════════════════════════════════════════════════
# Base Strategy
# ═══════════════════════════════════════════════════════════════════════

@dataclass
class StrategySignal:
    """Unified signal output from any strategy."""
    strategy_name: str
    symbol: str
    signal: str          # BUY, SELL, HOLD
    score: float         # 0-100 normalized score
    confidence: float    # 0-1 confidence level
    entry_price: float
    stop_loss: float | None = None
    take_profit: float | None = None
    regime: MarketRegime | None = None
    metadata: dict[str, Any] = field(default_factory=dict)


class BaseStrategy(ABC):
    """Abstract base for all trading strategies."""

    name: str = "base"
    compatible_regimes: list[str] = ["trending", "ranging", "volatile"]

    def __init__(self, client=None, **kwargs):
        self.client = client
        self.config = kwargs

    @abstractmethod
    def analyze(self, symbol: str, df: pd.DataFrame, regime: MarketRegime) -> StrategySignal | None:
        """Analyze a symbol and return a signal or None."""
        ...

    def calculate_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        """Subclasses can override to add custom indicators. Default: pass-through."""
        return df

    def _ensure_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        """Ensure standard indicators exist on the DataFrame."""
        if len(df) < 26:
            return df
        try:
            import talib
            close = df["close"].values
            high = df["high"].values
            low = df["low"].values

            if "adx" not in df.columns:
                df["adx"] = talib.ADX(high, low, close, timeperiod=14)
            if "atr" not in df.columns:
                df["atr"] = talib.ATR(high, low, close, timeperiod=14)
            if "rsi" not in df.columns:
                df["rsi"] = talib.RSI(close, timeperiod=14)
            if "bb_upper" not in df.columns:
                df["bb_upper"], df["bb_middle"], df["bb_lower"] = talib.BBANDS(close, timeperiod=20)
            if "ema_fast" not in df.columns:
                df["ema_fast"] = talib.EMA(close, timeperiod=12)
            if "ema_slow" not in df.columns:
                df["ema_slow"] = talib.EMA(close, timeperiod=26)
        except Exception as e:
            logger.warning("Error ensuring indicators: %s", e)
        return df


# ═══════════════════════════════════════════════════════════════════════
# Strategy Engine
# ═══════════════════════════════════════════════════════════════════════

# Default regime → strategy mapping
DEFAULT_REGIME_STRATEGIES: dict[str, list[str]] = {
    "trending": ["trend_following", "breakout", "ml_primary"],
    "ranging":  ["mean_reversion", "grid_dca"],
    "volatile": ["breakout", "ml_primary"],
}


class StrategyEngine:
    """Orchestrates multiple strategies with regime-based routing.

    Flow:
      1. Detect market regime
      2. Select compatible strategies
      3. Run each, collect signals
      4. Return best signal (highest score)
    """

    def __init__(
        self,
        strategies: list[BaseStrategy] | None = None,
        regime_map: dict[str, list[str]] | None = None,
        enable_all_regimes: bool = False,
    ):
        self._strategies: dict[str, BaseStrategy] = {}
        self._regime_map = regime_map or DEFAULT_REGIME_STRATEGIES
        self._enable_all_regimes = enable_all_regimes

        for s in (strategies or []):
            self.register(s)

    def register(self, strategy: BaseStrategy) -> None:
        """Register a strategy in the engine."""
        self._strategies[strategy.name] = strategy
        logger.info("Registered strategy: %s (regimes: %s)", strategy.name, strategy.compatible_regimes)

    def get_active_strategies(self, regime: str) -> list[BaseStrategy]:
        """Get strategies compatible with the given market regime."""
        names = self._regime_map.get(regime, [])
        strategies = []
        for name in names:
            s = self._strategies.get(name)
            if s and (regime in s.compatible_regimes or self._enable_all_regimes):
                strategies.append(s)
        return strategies

    def analyze_symbol(self, symbol: str, df: pd.DataFrame) -> list[StrategySignal]:
        """Run all eligible strategies on a symbol. Returns list of signals sorted by score desc."""
        regime = detect_regime(df)
        logger.debug(
            "[%s] Regime: %s (ADX=%.1f, ATR=%.2f%%, BB=%.1f%%, dir=%s)",
            symbol, regime.regime, regime.adx, regime.atr_pct,
            regime.bb_width_pct, regime.direction,
        )

        active = self.get_active_strategies(regime.regime)
        if not active:
            logger.debug("[%s] No strategies active for regime '%s'", symbol, regime.regime)
            return []

        signals: list[StrategySignal] = []
        for strategy in active:
            try:
                signal = strategy.analyze(symbol, df, regime)
                if signal is not None and signal.signal != "HOLD":
                    signals.append(signal)
            except Exception as e:
                logger.error("Strategy %s failed on %s: %s", strategy.name, symbol, e)

        signals.sort(key=lambda x: x.score, reverse=True)
        return signals

    def get_best_signal(self, symbol: str, df: pd.DataFrame) -> StrategySignal | None:
        """Get the single best signal for a symbol."""
        signals = self.analyze_symbol(symbol, df)
        return signals[0] if signals else None

    @property
    def strategy_names(self) -> list[str]:
        return list(self._strategies.keys())

    def get_regime(self, df: pd.DataFrame) -> MarketRegime:
        return detect_regime(df)
