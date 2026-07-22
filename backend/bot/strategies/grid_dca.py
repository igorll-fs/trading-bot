"""
GridDCAStrategy — scaling position entries with grid/DCA approach.

Instead of one entry, this strategy identifies accumulation zones and produces
signals with multiple target levels. The trading bot handles the scaling.

Logic:
  1. Identify a value zone (between BB lower and middle for BUY, upper and middle for SELL)
  2. Divide into N grid levels with equal spacing
  3. Signal includes grid_levels metadata for position scaling
  4. Entry triggers when price enters the value zone + RSI confirms

Compatible regimes: ranging (best), volatile (ok with wider grid)
"""

from __future__ import annotations

import logging

import numpy as np
import pandas as pd

from bot.strategy_engine import BaseStrategy, MarketRegime, StrategySignal

logger = logging.getLogger(__name__)


class GridDCAStrategy(BaseStrategy):
    """Grid / Dollar-Cost-Averaging entries in value zones."""

    name = "grid_dca"
    compatible_regimes = ["ranging", "volatile"]

    def __init__(
        self,
        client=None,
        *,
        grid_levels: int = 3,         # Number of DCA levels
        level_spacing_pct: float = 2.0,  # % spacing between levels
        rsi_trigger: int = 35,         # RSI below this = start accumulating (BUY)
        rsi_sell_trigger: int = 65,    # RSI above this = start distributing (SELL)
        bb_zone: str = "lower_half",    # Where to place grid: lower_half, upper_half
        min_score: int = 45,
        **kwargs,
    ):
        super().__init__(client, **kwargs)
        self.grid_levels = grid_levels
        self.level_spacing_pct = level_spacing_pct
        self.rsi_trigger = rsi_trigger
        self.rsi_sell_trigger = rsi_sell_trigger
        self.bb_zone = bb_zone
        self.min_score = min_score

    def analyze(self, symbol: str, df: pd.DataFrame, regime: MarketRegime) -> StrategySignal | None:
        try:
            if len(df) < 30:
                return None

            df = self._ensure_indicators(df)
            latest = df.iloc[-1]
            price = float(latest["close"])
            rsi = float(latest.get("rsi", 50)) if not pd.isna(latest.get("rsi", np.nan)) else 50.0

            bb_upper = latest.get("bb_upper")
            bb_lower = latest.get("bb_lower")
            bb_middle = latest.get("bb_middle", price)
            if bb_upper is None or bb_lower is None or pd.isna(bb_upper) or pd.isna(bb_lower):
                return None
            bb_upper, bb_lower, bb_middle = float(bb_upper), float(bb_lower), float(bb_middle)

            bb_range = bb_upper - bb_lower
            if bb_range <= 0:
                return None

            atr = float(latest.get("atr", 0))
            if atr <= 0:
                atr = price * 0.01

            # ---- BUY grid (accumulate in lower half) ----
            buy_signal = False
            buy_score = 0
            buy_grid: list[dict] = []

            # Entry zone: lower half of BB
            zone_bottom = bb_lower
            zone_top = bb_middle

            if price <= zone_top and rsi <= self.rsi_trigger:
                buy_signal = True
                buy_score += 25

                # Score based on how deep in the zone
                zone_position = (price - zone_bottom) / (zone_top - zone_bottom) if zone_top > zone_bottom else 0.5
                if zone_position <= 0.2:
                    buy_score += 30  # Deep in value zone
                elif zone_position <= 0.4:
                    buy_score += 20
                elif zone_position <= 0.6:
                    buy_score += 10

                # RSI extreme bonus
                if rsi <= 25: buy_score += 20
                elif rsi <= 30: buy_score += 15
                elif rsi <= 35: buy_score += 10

                # ADX confirmation (low ADX = ranging = good for grid)
                if regime.adx < 25: buy_score += 15
                elif regime.adx < 30: buy_score += 8

                # Volume spike on dip = capitulation = good entry
                vol_ratio = self._volume_ratio(df)
                if vol_ratio > 1.5: buy_score += 15
                elif vol_ratio > 1.2: buy_score += 8

                # Generate grid levels
                for i in range(self.grid_levels):
                    level_price = zone_bottom + (zone_top - zone_bottom) * (i / (self.grid_levels - 1))
                    position_pct = 1.0 / self.grid_levels  # Equal distribution
                    buy_grid.append({
                        "level": i + 1,
                        "price": round(level_price, 2),
                        "size_pct": position_pct,
                        "triggered": level_price >= price,
                    })

            # ---- SELL grid (distribute in upper half) ----
            sell_signal = False
            sell_score = 0
            sell_grid: list[dict] = []

            sell_zone_bottom = bb_middle
            sell_zone_top = bb_upper

            if price >= sell_zone_bottom and rsi >= self.rsi_sell_trigger:
                sell_signal = True
                sell_score += 25

                zone_position = (price - sell_zone_bottom) / (sell_zone_top - sell_zone_bottom) if sell_zone_top > sell_zone_bottom else 0.5
                if zone_position >= 0.8: sell_score += 30
                elif zone_position >= 0.6: sell_score += 20
                elif zone_position >= 0.4: sell_score += 10

                if rsi >= 75: sell_score += 20
                elif rsi >= 70: sell_score += 15
                elif rsi >= 65: sell_score += 10

                if regime.adx < 25: sell_score += 15
                elif regime.adx < 30: sell_score += 8

                for i in range(self.grid_levels):
                    level_price = sell_zone_bottom + (sell_zone_top - sell_zone_bottom) * (i / (self.grid_levels - 1))
                    position_pct = 1.0 / self.grid_levels
                    sell_grid.append({
                        "level": i + 1,
                        "price": round(level_price, 2),
                        "size_pct": position_pct,
                        "triggered": level_price <= price,
                    })

            # Pick best direction
            if not buy_signal and not sell_signal:
                return None

            if buy_signal and sell_signal:
                signal = "BUY" if buy_score > sell_score else "SELL"
                score = max(buy_score, sell_score)
                grid = buy_grid if signal == "BUY" else sell_grid
            elif buy_signal:
                signal = "BUY"
                score = buy_score
                grid = buy_grid
            else:
                signal = "SELL"
                score = sell_score
                grid = sell_grid

            if score < self.min_score:
                return None

            sl = bb_lower - atr if signal == "BUY" else bb_upper + atr
            tp = bb_middle if signal == "BUY" else bb_middle

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
                    "grid_levels": self.grid_levels,
                    "grid_entries": grid,
                    "rsi": round(rsi, 1),
                    "zone": "lower_half" if signal == "BUY" else "upper_half",
                },
            )

        except Exception as e:
            logger.error("GridDCAStrategy error on %s: %s", symbol, e)
            return None

    def _volume_ratio(self, df: pd.DataFrame) -> float:
        try:
            vol = df["volume"]
            return float(vol.iloc[-1]) / float(vol.rolling(20).mean().iloc[-1])
        except Exception:
            return 1.0
