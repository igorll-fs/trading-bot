"""
MeanReversionStrategy — Bollinger squeeze + RSI oversold/overbought entries.

Triggers when:
  1. Bollinger Band squeeze (width < 2%) signals impending expansion
  2. RSI is oversold (< 30) for BUY or overbought (> 70) for SELL
  3. Price touches lower band (BUY) or upper band (SELL)
  4. Optional: bullish/bearish RSI divergence for confirmation

Compatible regimes: ranging, volatile (squeeze before breakout)
"""

from __future__ import annotations

import logging

import numpy as np
import pandas as pd

from bot.strategy_engine import BaseStrategy, MarketRegime, StrategySignal

logger = logging.getLogger(__name__)


class MeanReversionStrategy(BaseStrategy):
    """Mean reversion: buy oversold RSI near BB lower, sell overbought near BB upper."""

    name = "mean_reversion"
    compatible_regimes = ["ranging", "volatile"]

    def __init__(
        self,
        client=None,
        *,
        rsi_oversold: int = 30,
        rsi_overbought: int = 70,
        bb_squeeze_threshold: float = 3.0,  # BB width % threshold for squeeze
        bb_touch_threshold: float = 0.005,  # 0.5% proximity to band
        require_squeeze: bool = True,
        min_score: int = 60,
        **kwargs,
    ):
        super().__init__(client, **kwargs)
        self.rsi_oversold = rsi_oversold
        self.rsi_overbought = rsi_overbought
        self.bb_squeeze_threshold = bb_squeeze_threshold
        self.bb_touch_threshold = bb_touch_threshold
        self.require_squeeze = require_squeeze
        self.min_score = min_score

    def analyze(self, symbol: str, df: pd.DataFrame, regime: MarketRegime) -> StrategySignal | None:
        try:
            if len(df) < 30:
                return None

            df = self._ensure_indicators(df)
            latest = df.iloc[-1]

            price = float(latest["close"])
            rsi = float(latest.get("rsi", 50)) if not pd.isna(latest.get("rsi", np.nan)) else 50.0

            # Bollinger data
            bb_upper = latest.get("bb_upper")
            bb_lower = latest.get("bb_lower")
            bb_middle = latest.get("bb_middle", price)

            if bb_upper is None or bb_lower is None or pd.isna(bb_upper) or pd.isna(bb_lower):
                return None

            bb_upper, bb_lower, bb_middle = float(bb_upper), float(bb_lower), float(bb_middle)
            bb_width_pct = ((bb_upper - bb_lower) / bb_middle) * 100 if bb_middle > 0 else 100.0

            # Bollinger %B (0=lower, 1=upper)
            bb_range = bb_upper - bb_lower
            bb_pct_b = (price - bb_lower) / bb_range if bb_range > 0 else 0.5

            # ---- Filter: Squeeze detection ----
            if self.require_squeeze and bb_width_pct > self.bb_squeeze_threshold:
                return None  # No squeeze = no trade

            # ---- BUY signal (oversold near lower band) ----
            buy_signal = False
            buy_score = 0

            if rsi <= self.rsi_oversold:
                buy_score += 30
            elif rsi <= 35:
                buy_score += 20
            elif rsi <= 40:
                buy_score += 10

            if bb_pct_b <= 0.15:  # Price very near lower band
                buy_score += 30
            elif bb_pct_b <= 0.25:
                buy_score += 20
            elif bb_pct_b <= 0.35:
                buy_score += 10

            # RSI divergence bonus
            divergence = self._detect_rsi_divergence(df)
            if divergence == "bullish":
                buy_score += 20
            elif divergence == "bearish":
                buy_score -= 15

            # Squeeze bonus (tighter = stronger signal when it breaks)
            if bb_width_pct < 1.5:
                buy_score += 15
            elif bb_width_pct < 2.0:
                buy_score += 10

            # Bollinger squeeze play: price at lower band in squeeze → expansion imminent
            if bb_width_pct < self.bb_squeeze_threshold and bb_pct_b <= 0.2:
                buy_score += 15

            # Volume confirmation
            volume_ratio = self._volume_ratio(df)
            if volume_ratio > 1.3:  # High volume on reversal
                buy_score += 15
            elif volume_ratio > 1.0:
                buy_score += 8

            if buy_score >= self.min_score:
                buy_signal = True

            # ---- SELL signal (overbought near upper band) ----
            sell_signal = False
            sell_score = 0

            if rsi >= self.rsi_overbought:
                sell_score += 30
            elif rsi >= 65:
                sell_score += 20
            elif rsi >= 60:
                sell_score += 10

            if bb_pct_b >= 0.85:
                sell_score += 30
            elif bb_pct_b >= 0.75:
                sell_score += 20
            elif bb_pct_b >= 0.65:
                sell_score += 10

            if divergence == "bearish":
                sell_score += 20
            elif divergence == "bullish":
                sell_score -= 15

            if bb_width_pct < 1.5:
                sell_score += 15
            elif bb_width_pct < 2.0:
                sell_score += 10

            if volume_ratio > 1.3:
                sell_score += 15
            elif volume_ratio > 1.0:
                sell_score += 8

            if sell_score >= self.min_score:
                sell_signal = True

            # Pick best direction
            if not buy_signal and not sell_signal:
                return None

            if buy_signal and sell_signal:
                signal = "BUY" if buy_score > sell_score else "SELL"
                score = max(buy_score, sell_score)
            elif buy_signal:
                signal = "BUY"
                score = buy_score
            else:
                signal = "SELL"
                score = sell_score

            # Stop loss / take profit
            atr = float(latest.get("atr", 0))
            if atr <= 0:
                atr = price * 0.01

            if signal == "BUY":
                sl = bb_lower - atr * 0.5  # Tight stop below BB lower
                tp = bb_middle             # Target: mean reversion to middle
            else:
                sl = bb_upper + atr * 0.5
                tp = bb_middle

            return StrategySignal(
                strategy_name=self.name,
                symbol=symbol,
                signal=signal,
                score=min(score, 100),
                confidence=score / 100.0,
                entry_price=price,
                stop_loss=sl,
                take_profit=tp,
                regime=regime,
                metadata={
                    "rsi": rsi,
                    "bb_pct_b": round(bb_pct_b, 3),
                    "bb_width_pct": round(bb_width_pct, 2),
                    "divergence": divergence,
                    "volume_ratio": round(volume_ratio, 2),
                },
            )

        except Exception as e:
            logger.error("MeanReversionStrategy error on %s: %s", symbol, e)
            return None

    def _detect_rsi_divergence(self, df: pd.DataFrame, lookback: int = 14) -> str:
        """Detect bullish or bearish RSI divergence."""
        try:
            if len(df) < lookback:
                return "none"
            close = df["close"].values[-lookback:]
            rsi = df["rsi"].values[-lookback:]
            if np.isnan(rsi).any():
                return "none"

            # Price making lower low, RSI making higher low → bullish divergence
            price_last3 = close[-3:]
            rsi_last3 = rsi[-3:]
            if close[-1] <= min(close[:-1]) and rsi[-1] > min(rsi[:-1]):
                return "bullish"

            # Price making higher high, RSI making lower high → bearish divergence
            if close[-1] >= max(close[:-1]) and rsi[-1] < max(rsi[:-1]):
                return "bearish"

            return "none"
        except Exception:
            return "none"

    def _volume_ratio(self, df: pd.DataFrame) -> float:
        try:
            vol = df["volume"]
            current = float(vol.iloc[-1])
            avg = float(vol.rolling(20).mean().iloc[-1])
            return current / avg if avg > 0 else 1.0
        except Exception:
            return 1.0
