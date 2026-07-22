"""Multi-strategy trading system for bottrading."""

from bot.strategies.trend_following import TrendFollowingStrategy
from bot.strategies.mean_reversion import MeanReversionStrategy
from bot.strategies.breakout import BreakoutStrategy
from bot.strategies.grid_dca import GridDCAStrategy
from bot.strategies.ml_primary import MLPrimaryStrategy

__all__ = [
    "TrendFollowingStrategy",
    "MeanReversionStrategy",
    "BreakoutStrategy",
    "GridDCAStrategy",
    "MLPrimaryStrategy",
]
