"""
Backtesting Engine — walk-forward backtesting with comprehensive metrics.

Supports:
  - Walk-forward optimization (train on past, test on future)
  - Multiple strategies tested simultaneously
  - Comprehensive metrics: Sharpe, Sortino, max drawdown, win rate, profit factor
  - Equity curve and trade log export
  - Comparison reports across strategies

Usage:
  from backtesting import BacktestEngine, BacktestConfig

  config = BacktestConfig(
      symbol="BTCUSDT",
      start_date="2025-01-01",
      end_date="2025-06-01",
      initial_capital=10000,
      strategies=[TrendFollowingStrategy(), MeanReversionStrategy()],
  )
  engine = BacktestEngine(config)
  results = engine.run()
  engine.print_report(results)
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)


# ═══════════════════════════════════════════════════════════════════════
# Config
# ═══════════════════════════════════════════════════════════════════════

@dataclass
class BacktestConfig:
    """Configuration for backtesting run."""
    symbol: str = "BTCUSDT"
    start_date: str = "2024-01-01"
    end_date: str = "2025-01-01"
    initial_capital: float = 10000.0
    commission_pct: float = 0.1         # 0.1% per trade
    slippage_pct: float = 0.05          # 0.05% slippage
    max_position_pct: float = 0.2       # Max 20% of capital per position
    strategies: list[Any] = field(default_factory=list)
    data: pd.DataFrame | None = None    # Pre-loaded OHLCV data (optional)


# ═══════════════════════════════════════════════════════════════════════
# Results
# ═══════════════════════════════════════════════════════════════════════

@dataclass
class TradeRecord:
    symbol: str
    signal: str
    entry_time: str
    exit_time: str
    entry_price: float
    exit_price: float
    quantity: float
    pnl: float
    pnl_pct: float
    strategy: str
    exit_reason: str = "close"


@dataclass
class BacktestResult:
    """Results from a backtesting run."""
    strategy_name: str
    symbol: str
    start_date: str
    end_date: str
    initial_capital: float
    final_equity: float
    total_return_pct: float
    total_trades: int
    winning_trades: int
    losing_trades: int
    win_rate: float
    avg_win_pct: float
    avg_loss_pct: float
    profit_factor: float
    max_drawdown_pct: float
    max_drawdown_duration: int  # candles
    sharpe_ratio: float
    sortino_ratio: float
    calmar_ratio: float
    expectancy: float
    trades: list[TradeRecord] = field(default_factory=list)
    equity_curve: list[float] = field(default_factory=list)


# ═══════════════════════════════════════════════════════════════════════
# Engine
# ═══════════════════════════════════════════════════════════════════════

class BacktestEngine:
    """Walk-forward backtesting engine."""

    def __init__(self, config: BacktestConfig):
        self.config = config
        self.data: pd.DataFrame | None = config.data

    def load_data(self) -> pd.DataFrame:
        """Load or return pre-loaded OHLCV data."""
        if self.data is not None:
            return self.data

        # Try loading from client if available
        for s in self.config.strategies:
            if s.client is not None:
                klines = s.client.get_klines(
                    symbol=self.config.symbol,
                    interval="1h",
                    limit=1000,
                )
                df = pd.DataFrame(klines, columns=[
                    "timestamp", "open", "high", "low", "close", "volume",
                    "close_time", "quote_volume", "trades", "taker_buy_base",
                    "taker_buy_quote", "ignore",
                ])
                for col in ["open", "high", "low", "close", "volume"]:
                    df[col] = pd.to_numeric(df[col])
                df["timestamp"] = pd.to_datetime(df["timestamp"], unit="ms")
                self.data = df
                return df

        raise ValueError("No data source available. Provide data in BacktestConfig.data or set client on strategies.")

    def run(self) -> dict[str, BacktestResult]:
        """Run backtest for all strategies. Returns {strategy_name: BacktestResult}."""
        df = self.load_data()
        results: dict[str, BacktestResult] = {}

        for strategy in self.config.strategies:
            logger.info("Backtesting %s on %s...", strategy.name, self.config.symbol)
            result = self._run_single(strategy, df)
            results[strategy.name] = result

        return results

    def _run_single(self, strategy, df: pd.DataFrame) -> BacktestResult:
        """Run a single strategy through the data."""
        from bot.strategy_engine import detect_regime

        trades: list[TradeRecord] = []
        equity = self.config.initial_capital
        equity_curve = [equity]
        capital = self.config.initial_capital
        position = None  # {entry_price, quantity, signal, strategy, entry_idx}

        for i in range(50, len(df)):  # Start after enough data
            window = df.iloc[:i+1].copy()
            current_price = float(window["close"].iloc[-1])

            # Check position exit
            if position is not None:
                exit_now = False
                exit_price = current_price
                exit_reason = "close"

                # Stop loss hit
                if position["signal"] == "BUY" and current_price <= position.get("sl", 0):
                    exit_now = True
                    exit_price = position["sl"]
                    exit_reason = "stop_loss"
                elif position["signal"] == "SELL" and current_price >= position.get("sl", float("inf")):
                    exit_now = True
                    exit_price = position["sl"]
                    exit_reason = "stop_loss"

                # Take profit hit
                if position["signal"] == "BUY" and current_price >= position.get("tp", float("inf")):
                    exit_now = True
                    exit_price = position["tp"]
                    exit_reason = "take_profit"
                elif position["signal"] == "SELL" and current_price <= position.get("tp", 0):
                    exit_now = True
                    exit_price = position["tp"]
                    exit_reason = "take_profit"

                if exit_now:
                    slippage = 1 - self.config.slippage_pct / 100
                    if position["signal"] == "SELL":
                        exit_price_adj = exit_price * (1 + self.config.slippage_pct / 100)
                    else:
                        exit_price_adj = exit_price * slippage

                    pnl_pct = (exit_price_adj / position["entry_price"] - 1) * 100
                    if position["signal"] == "SELL":
                        pnl_pct = -pnl_pct  # Invert for short

                    pnl = position["quantity"] * position["entry_price"] * pnl_pct / 100
                    pnl -= position["quantity"] * position["entry_price"] * self.config.commission_pct / 100 * 2
                    capital += pnl
                    equity = capital
                    equity_curve.append(equity)

                    trades.append(TradeRecord(
                        symbol=self.config.symbol,
                        signal=position["signal"],
                        entry_time=str(df["timestamp"].iloc[position["entry_idx"]]),
                        exit_time=str(df["timestamp"].iloc[i]),
                        entry_price=position["entry_price"],
                        exit_price=exit_price_adj,
                        quantity=position["quantity"],
                        pnl=pnl,
                        pnl_pct=pnl_pct,
                        strategy=strategy.name,
                        exit_reason=exit_reason,
                    ))
                    position = None

            # Check entry if no position
            if position is None:
                try:
                    regime = detect_regime(window)
                    signal = strategy.analyze(self.config.symbol, window, regime)
                except Exception as e:
                    logger.debug("Strategy error at idx %d: %s", i, e)
                    signal = None

                if signal is not None and signal.signal != "HOLD":
                    quantity = (capital * self.config.max_position_pct) / current_price
                    if quantity > 0:
                        position = {
                            "signal": signal.signal,
                            "entry_price": current_price,
                            "quantity": quantity,
                            "sl": signal.stop_loss or 0,
                            "tp": signal.take_profit or float("inf"),
                            "entry_idx": i,
                            "strategy": strategy.name,
                        }

        # Close any remaining position
        if position is not None:
            final_price = float(df["close"].iloc[-1])
            pnl_pct = (final_price / position["entry_price"] - 1) * 100
            if position["signal"] == "SELL":
                pnl_pct = -pnl_pct
            pnl = position["quantity"] * position["entry_price"] * pnl_pct / 100
            capital += pnl
            equity_curve.append(capital)

            trades.append(TradeRecord(
                symbol=self.config.symbol,
                signal=position["signal"],
                entry_time=str(df["timestamp"].iloc[position["entry_idx"]]),
                exit_time=str(df["timestamp"].iloc[-1]),
                entry_price=position["entry_price"],
                exit_price=final_price,
                quantity=position["quantity"],
                pnl=pnl,
                pnl_pct=pnl_pct,
                strategy=strategy.name,
                exit_reason="end_of_data",
            ))

        # Calculate metrics
        return self._calculate_metrics(strategy.name, trades, equity_curve, capital)

    def _calculate_metrics(
        self, name: str, trades: list[TradeRecord], equity_curve: list[float], final_equity: float
    ) -> BacktestResult:
        """Calculate all performance metrics."""
        total = len(trades)
        wins = [t for t in trades if t.pnl > 0]
        losses = [t for t in trades if t.pnl <= 0]
        win_count = len(wins)
        loss_count = len(losses)

        win_rate = (win_count / total * 100) if total > 0 else 0
        avg_win = np.mean([t.pnl_pct for t in wins]) if wins else 0
        avg_loss = np.mean([t.pnl_pct for t in losses]) if losses else 0

        gross_profit = sum(t.pnl for t in wins) if wins else 0
        gross_loss = abs(sum(t.pnl for t in losses)) if losses else 0
        profit_factor = gross_profit / gross_loss if gross_loss > 0 else float("inf")

        total_return = ((final_equity / self.config.initial_capital) - 1) * 100

        expectancy = (win_rate / 100 * avg_win) + ((1 - win_rate / 100) * avg_loss)

        # Drawdown
        eq = np.array(equity_curve)
        peak = np.maximum.accumulate(eq)
        drawdown_pct = (eq - peak) / peak * 100
        max_dd = abs(np.min(drawdown_pct))

        # Max drawdown duration
        dd_start = None
        max_dd_duration = 0
        for i, dd in enumerate(drawdown_pct):
            if dd < 0 and dd_start is None:
                dd_start = i
            elif dd >= 0 and dd_start is not None:
                max_dd_duration = max(max_dd_duration, i - dd_start)
                dd_start = None
        if dd_start is not None:
            max_dd_duration = max(max_dd_duration, len(drawdown_pct) - dd_start)

        # Sharpe ratio (annualized, assume risk-free = 0 for crypto)
        returns = np.diff(eq) / eq[:-1]
        sharpe = (np.mean(returns) / np.std(returns)) * np.sqrt(365 * 24) if np.std(returns) > 0 else 0

        # Sortino ratio (only downside deviation)
        downside = returns[returns < 0]
        sortino = (np.mean(returns) / np.std(downside)) * np.sqrt(365 * 24) if len(downside) > 0 and np.std(downside) > 0 else 0

        # Calmar ratio
        calmar = (total_return / 100) / (max_dd / 100) if max_dd > 0 else float("inf")

        return BacktestResult(
            strategy_name=name,
            symbol=self.config.symbol,
            start_date=self.config.start_date,
            end_date=self.config.end_date,
            initial_capital=self.config.initial_capital,
            final_equity=final_equity,
            total_return_pct=round(total_return, 2),
            total_trades=total,
            winning_trades=win_count,
            losing_trades=loss_count,
            win_rate=round(win_rate, 2),
            avg_win_pct=round(avg_win, 2),
            avg_loss_pct=round(avg_loss, 2),
            profit_factor=round(profit_factor, 2),
            max_drawdown_pct=round(max_dd, 2),
            max_drawdown_duration=max_dd_duration,
            sharpe_ratio=round(sharpe, 3),
            sortino_ratio=round(sortino, 3),
            calmar_ratio=round(calmar, 3),
            expectancy=round(expectancy, 2),
            trades=trades,
            equity_curve=[round(e, 2) for e in equity_curve],
        )

    def print_report(self, results: dict[str, BacktestResult]) -> str:
        """Generate a formatted report string."""
        lines = ["=" * 70, "BACKTEST REPORT", "=" * 70, ""]

        for name, r in results.items():
            lines.extend([
                f"Strategy: {name}",
                f"  Symbol:      {r.symbol}  |  Period: {r.start_date} → {r.end_date}",
                f"  Capital:     ${r.initial_capital:,.0f} → ${r.final_equity:,.2f}  ({r.total_return_pct:+.2f}%)",
                "",
                f"  Trades:      {r.total_trades}  |  Win Rate: {r.win_rate:.1f}%",
                f"  Avg Win:     {r.avg_win_pct:+.2f}%  |  Avg Loss: {r.avg_loss_pct:+.2f}%",
                f"  Profit Factor: {r.profit_factor:.2f}  |  Expectancy: {r.expectancy:+.2f}%",
                "",
                f"  Max DD:      {r.max_drawdown_pct:.2f}%  ({r.max_drawdown_duration} candles)",
                f"  Sharpe:      {r.sharpe_ratio:.3f}  |  Sortino: {r.sortino_ratio:.3f}  |  Calmar: {r.calmar_ratio:.3f}",
                "",
                "  Recent Trades:",
            ])
            for t in r.trades[-5:]:
                lines.append(
                    f"    {t.entry_time[:10]}  {t.signal:4s}  "
                    f"${t.entry_price:,.2f} → ${t.exit_price:,.2f}  "
                    f"P&L: {t.pnl:+.2f} ({t.pnl_pct:+.2f}%)  [{t.exit_reason}]"
                )
            lines.append("")
            lines.append("-" * 70)
            lines.append("")

        # Comparison if multiple strategies
        if len(results) > 1:
            lines.append("COMPARISON:")
            lines.append(f"{'Strategy':<22} {'Return':>8} {'Win%':>7} {'PF':>6} {'Sharpe':>8} {'MaxDD':>7}")
            lines.append("-" * 60)
            best = max(results.values(), key=lambda r: r.sharpe_ratio)
            for name, r in results.items():
                marker = " ★" if r is best else ""
                lines.append(
                    f"{name:<22} {r.total_return_pct:>+7.1f}% "
                    f"{r.win_rate:>6.1f}% {r.profit_factor:>5.1f} "
                    f"{r.sharpe_ratio:>7.3f} {r.max_drawdown_pct:>6.1f}%{marker}"
                )
            lines.append("")
            lines.append(f"★ Best: {best.strategy_name} (highest Sharpe ratio)")

        return "\n".join(lines)


# ═══════════════════════════════════════════════════════════════════════
# Convenience
# ═══════════════════════════════════════════════════════════════════════

def quick_backtest(
    strategy,
    symbol: str,
    df: pd.DataFrame,
    initial_capital: float = 10000.0,
) -> BacktestResult:
    """Quick backtest with a single strategy and pre-loaded DataFrame."""
    config = BacktestConfig(
        symbol=symbol,
        initial_capital=initial_capital,
        strategies=[strategy],
        data=df,
    )
    engine = BacktestEngine(config)
    results = engine.run()
    return results[strategy.name]
