"""
BreakoutStrategy — Donchian channel + ATR breakout with volume confirmation.

Signals:
  - BUY:  price breaks above Donchian upper (20-period high) with ATR expansion
  - SELL: price breaks below Donchian lower (20-period low) with ATR expansion

Bonus filters:
  - Volume > 1.5x average confirms breakout
  - ATR expansion > 20% vs 10-period average = genuine breakout (not fakeout)
  - RSI alignment (50+ for BUY, < 50 for SELL)

Compatible regimes: trending, volatile
"""

from __future__ import annotations

import logging

import numpy as np
import pandas as pd

from bot.strategy_engine import BaseStrategy, MarketRegime, StrategySignal

logger = logging.getLogger(__name__)


class BreakoutStrategy(BaseStrategy):
    """Breakout trading using Donchian channels + ATR expansion + volume confirmation."""

    name = "breakout"
    compatible_regimes = ["trending", "volatile"]

    def __init__(
        self,
        client=None,
        *,
        donchian_period: int = 20,
        atr_expansion_threshold: float = 1.2,  # ATR must be 1.2x its own 10-period avg
        volume_expansion_threshold: float = 1.5,
        rsi_zone: tuple[int, int] = (40, 60),  # RSI outside this zone = stronger
        min_score: int = 55,
        **kwargs,
    ):
        super().__init__(client, **kwargs)
        self.donchian_period = donchian_period
        self.atr_expansion_threshold = atr_expansion_threshold
        self.volume_expansion_threshold = volume_expansion_threshold
        self.rsi_zone = rsi_zone
        self.min_score = min_score

    def analyze(self, symbol: str, df: pd.DataFrame, regime: MarketRegime) -> StrategySignal | None:
        try:
            if len(df) < self.donchian_period + 5:
                return None

            df = self._ensure_indicators(df)

            # Add Donchian channels
            df = self._add_donchian(df)

            latest = df.iloc[-1]
            prev = df.iloc[-2]
            price = float(latest["close"])

            donchian_upper = float(latest.get("donchian_upper", price))
            donchian_lower = float(latest.get("donchian_lower", price))
            donchian_mid = (donchian_upper + donchian_lower) / 2

            atr_now = float(latest.get("atr", 0))
            if atr_now <= 0:
                atr_now = price * 0.01

            # ATR expansion (is volatility expanding vs recent average?)
            atr_10ma = float(df["atr"].tail(10).mean()) if len(df) >= 10 else atr_now
            atr_expansion = atr_now / atr_10ma if atr_10ma > 0 else 1.0

            # Volume confirmation
            vol_ratio = self._volume_ratio(df)
            vol_ma10 = float(df["volume"].tail(10).mean())
            vol_now = float(df["volume"].iloc[-1])

            rsi = float(latest.get("rsi", 50)) if not pd.isna(latest.get("rsi", np.nan)) else 50.0

            # ---- Detect breakout ----
            prev_price = float(prev["close"])
            prev_upper = float(prev.get("donchian_upper", prev_price * 2))
            prev_lower = float(prev.get("donchian_lower", 0))

            # BUY breakout: price crosses above Donchian upper
            buy_breakout = price > donchian_upper and prev_price <= prev_upper

            # SELL breakout: price crosses below Donchian lower
            sell_breakout = price < donchian_lower and prev_price >= prev_lower

            if not buy_breakout and not sell_breakout:
                return None

            # ---- Score the breakout ----
            score = 0

            if buy_breakout:
                signal = "BUY"
                # Core breakout
                score += 30

                # ATR expansion bonus
                if atr_expansion >= 1.3: score += 20
                elif atr_expansion >= 1.2: score += 15
                elif atr_expansion >= 1.1: score += 8

                # Volume confirmation
                if vol_ratio >= 2.0: score += 20
                elif vol_ratio >= 1.5: score += 15
                elif vol_ratio >= 1.2: score += 8

                # RSI alignment (50+ supports uptrend)
                if rsi > 60: score += 15
                elif rsi > 50: score += 10

                # Price extension from mid (breakout strength)
                extension_pct = (price - donchian_mid) / donchian_mid * 100
                if extension_pct > 3: score += 15
                elif extension_pct > 2: score += 10

                # Trend alignment bonus
                if regime.direction == "up": score += 10

                # Stop loss / take profit
                sl = donchian_mid
                tp = price + (price - donchian_lower) * 2.0  # Measured move

            elif sell_breakout:
                signal = "SELL"
                score += 30

                if atr_expansion >= 1.3: score += 20
                elif atr_expansion >= 1.2: score += 15
                elif atr_expansion >= 1.1: score += 8

                if vol_ratio >= 2.0: score += 20
                elif vol_ratio >= 1.5: score += 15
                elif vol_ratio >= 1.2: score += 8

                if rsi < 40: score += 15
                elif rsi < 50: score += 10

                extension_pct = (donchian_mid - price) / donchian_mid * 100
                if extension_pct > 3: score += 15
                elif extension_pct > 2: score += 10

                if regime.direction == "down": score += 10

                sl = donchian_mid
                tp = price - (donchian_upper - price) * 2.0
            else:
                return None

            # Fakeout penalty: low volume breakout = likely fake
            if vol_ratio < 1.0:
                score -= 20

            # ATR must be expanding
            if atr_expansion < self.atr_expansion_threshold:
                score -= 15

            if score < self.min_score:
                return None

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
                    "atr_expansion": round(atr_expansion, 2),
                    "volume_ratio": round(vol_ratio, 2),
                    "donchian_upper": round(donchian_upper, 2),
                    "donchian_lower": round(donchian_lower, 2),
                    "rsi": round(rsi, 1),
                },
            )

        except Exception as e:
            logger.error("BreakoutStrategy error on %s: %s", symbol, e)
            return None

    def _add_donchian(self, df: pd.DataFrame) -> pd.DataFrame:
        """Add Donchian channel columns."""
        if "donchian_upper" not in df.columns:
            df["donchian_upper"] = df["high"].rolling(self.donchian_period).max()
            df["donchian_lower"] = df["low"].rolling(self.donchian_period).min()
        return df

    def _volume_ratio(self, df: pd.DataFrame) -> float:
        try:
            vol = df["volume"]
            current = float(vol.iloc[-1])
            avg = float(vol.rolling(20).mean().iloc[-1])
            return current / avg if avg > 0 else 1.0
        except Exception:
            return 1.0
