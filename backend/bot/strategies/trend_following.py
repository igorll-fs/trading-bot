"""
TrendFollowingStrategy — multi-timeframe trend following with unified scoring.

Refactored from the original TradingStrategy.calculate_unified_score().
Compatible regimes: trending, volatile.
"""

from __future__ import annotations

import logging
from typing import Any

import numpy as np
import pandas as pd

from bot.strategy_engine import BaseStrategy, MarketRegime, StrategySignal

logger = logging.getLogger(__name__)


class TrendFollowingStrategy(BaseStrategy):
    """Trend-following strategy using EMA cross, MACD, RSI, VWAP, Bollinger Bands."""

    name = "trend_following"
    compatible_regimes = ["trending", "volatile"]

    def __init__(
        self,
        client=None,
        *,
        min_signal_strength: int = 70,
        confirmation_timeframe: str = "1h",
        klines_limit: int = 200,
        **kwargs,
    ):
        super().__init__(client, **kwargs)
        self.min_signal_strength = min_signal_strength
        self.confirmation_timeframe = confirmation_timeframe
        self.klines_limit = klines_limit

    def analyze(self, symbol: str, df: pd.DataFrame, regime: MarketRegime) -> StrategySignal | None:
        try:
            if len(df) < 26:
                return None

            df = self._ensure_indicators(df)
            latest = df.iloc[-1]
            prev = df.iloc[-2]

            higher_df = self._get_higher_tf(symbol)

            volume_ma = df["volume"].rolling(window=20).mean().iloc[-1]
            current_volume = float(df["volume"].iloc[-1])
            volume_ratio = current_volume / float(volume_ma) if volume_ma > 0 else 1.0

            signal = "HOLD"
            if self._has(latest, "ema_fast", "ema_slow") and self._has(prev, "ema_fast", "ema_slow"):
                if latest["ema_fast"] > latest["ema_slow"] and prev["ema_fast"] <= prev["ema_slow"]:
                    signal = "BUY"
                elif latest["ema_fast"] < latest["ema_slow"] and prev["ema_fast"] >= prev["ema_slow"]:
                    signal = "SELL"

            if signal == "HOLD":
                return None

            score = self._calc_score(df, higher_df, volume_ratio, signal, symbol)
            if score < self.min_signal_strength:
                return None

            atr = float(latest.get("atr", 0))
            price = float(latest["close"])
            if atr <= 0:
                atr = price * 0.01

            if signal == "BUY":
                sl = price - atr * 1.5
                tp = price + atr * 3.0
            else:
                sl = price + atr * 1.5
                tp = price - atr * 3.0

            return StrategySignal(
                strategy_name=self.name,
                symbol=symbol,
                signal=signal,
                score=float(score),
                confidence=float(score) / 100.0,
                entry_price=price,
                stop_loss=sl,
                take_profit=tp,
                regime=regime,
                metadata={"volume_ratio": volume_ratio, "atr": atr, "adx": regime.adx},
            )

        except Exception as e:
            logger.error("TrendFollowingStrategy error on %s: %s", symbol, e)
            return None

    def _get_higher_tf(self, symbol: str) -> pd.DataFrame | None:
        if self.client is None:
            return None
        try:
            klines = self.client.get_klines(
                symbol=symbol, interval=self.confirmation_timeframe, limit=100
            )
            df = pd.DataFrame(klines, columns=[
                "timestamp", "open", "high", "low", "close", "volume",
                "close_time", "quote_volume", "trades", "taker_buy_base",
                "taker_buy_quote", "ignore",
            ])
            for col in ["open", "high", "low", "close", "volume"]:
                df[col] = pd.to_numeric(df[col])
            return self._ensure_indicators(df)
        except Exception:
            return None

    def _has(self, row, *cols) -> bool:
        for c in cols:
            if c not in row or pd.isna(row[c]):
                return False
        return True

    def _calc_score(self, df, higher_df, vol_ratio, signal, symbol) -> int:
        try:
            latest, prev = df.iloc[-1], df.iloc[-2]
            score = 0

            # 1. EMA Cross/Trend (20 pts)
            if self._has(latest, "ema_fast", "ema_slow") and self._has(prev, "ema_fast"):
                if signal == "BUY" and latest["ema_fast"] > latest["ema_slow"]:
                    score += 12 if prev["ema_fast"] <= prev["ema_slow"] else 8
                elif signal == "SELL" and latest["ema_fast"] < latest["ema_slow"]:
                    score += 12 if prev["ema_fast"] >= prev["ema_slow"] else 8
            if self._has(latest, "ema_50", "ema_200"):
                if (signal == "BUY" and latest["ema_50"] > latest["ema_200"]) or \
                   (signal == "SELL" and latest["ema_50"] < latest["ema_200"]):
                    score += 8

            # 2. Higher TF (15 pts)
            if higher_df is not None and len(higher_df) >= 2:
                hl = higher_df.iloc[-1]
                if self._has(hl, "ema_50", "ema_200"):
                    if (signal == "BUY" and hl["ema_50"] > hl["ema_200"]) or \
                       (signal == "SELL" and hl["ema_50"] < hl["ema_200"]):
                        score += 15
                    elif signal == "BUY" and hl["ema_50"] < hl["ema_200"]:
                        score = max(0, score - 5)

            # 3. MACD (10 pts)
            if self._has(latest, "macd_hist") and self._has(prev, "macd_hist"):
                hist, prev_hist = latest["macd_hist"], prev["macd_hist"]
                if signal == "BUY":
                    score += 10 if hist > 0 and hist > prev_hist else (6 if hist > 0 else (4 if hist < 0 and hist > prev_hist else 0))
                elif signal == "SELL":
                    score += 10 if hist < 0 and hist < prev_hist else (6 if hist < 0 else (4 if hist > 0 and hist < prev_hist else 0))

            # 4. RSI (15 pts)
            rsi = latest.get("rsi", 50)
            if not pd.isna(rsi):
                if signal == "BUY":
                    score += 10 if 30 <= rsi <= 45 else (6 if 45 < rsi <= 55 else (8 if rsi < 30 else 0))
                elif signal == "SELL":
                    score += 10 if 55 <= rsi <= 70 else (6 if 45 <= rsi < 55 else (8 if rsi > 70 else 0))

            # 5. Volume (20 pts)
            vol_score = 0
            if vol_ratio >= 1.5: vol_score += 10
            elif vol_ratio >= 1.2: vol_score += 7
            elif vol_ratio >= 1.0: vol_score += 4
            buy_pct = latest.get("buy_volume_pct", 0.5)
            if not pd.isna(buy_pct):
                if signal == "BUY" and buy_pct > 0.55: vol_score += 10
                elif signal == "BUY" and buy_pct > 0.50: vol_score += 5
                elif signal == "SELL" and buy_pct < 0.45: vol_score += 10
                elif signal == "SELL" and buy_pct < 0.50: vol_score += 5
            score += min(vol_score, 20)

            # 6. VWAP (10 pts)
            if self._has(latest, "vwap"):
                vwap, price = latest["vwap"], latest["close"]
                if signal == "BUY" and price > vwap: score += 10
                elif signal == "BUY" and price > vwap * 0.995: score += 5
                elif signal == "SELL" and price < vwap: score += 10

            # 7. Bollinger (10 pts)
            if self._has(latest, "bb_lower", "bb_upper"):
                price = latest["close"]
                bb_low, bb_up = latest["bb_lower"], latest["bb_upper"]
                bb_mid = latest.get("bb_middle", (bb_low + bb_up) / 2)
                if signal == "BUY" and price <= bb_low * 1.005: score += 10
                elif signal == "BUY" and price < bb_mid: score += 6
                elif signal == "SELL" and price >= bb_up * 0.995: score += 10
                elif signal == "SELL" and price > bb_mid: score += 6

            # 8. BTC penalty
            if "BTC" not in symbol and signal == "BUY" and self._is_btc_bearish():
                score = max(0, score - 15)

            return min(max(score, 0), 100)
        except Exception as e:
            logger.warning("Score calc error: %s", e)
            return 0

    def _is_btc_bearish(self) -> bool:
        if self.client is None:
            return False
        try:
            klines = self.client.get_klines(symbol="BTCUSDT", interval="15m", limit=20)
            closes = [float(k[4]) for k in klines]
            return closes[-1] < closes[-5]
        except Exception:
            return False
