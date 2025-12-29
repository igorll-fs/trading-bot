"""
CLI simples para rodar backtests com a TradingStrategy usando dados historicos da Binance.

Exemplo de uso (a partir do diretorio `backend`):

    $env:PYTHONPATH=.
    python scripts/backtest_strategy.py --symbol BTCUSDT --interval 15m --days 14 --initial-balance 1500
"""

from __future__ import annotations

import argparse
import os
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Optional, Tuple

import pandas as pd
from binance.client import Client

from bot.strategy import TradingStrategy
from bot.risk_manager import RiskManager


@dataclass
class BacktestResult:
    symbol: str
    interval: str
    confirmation_interval: Optional[str]
    start: datetime
    end: datetime
    initial_balance: float
    final_balance: float
    total_trades: int
    winning_trades: int
    losing_trades: int
    win_rate: float
    net_profit: float
    roi: float
    max_drawdown_pct: float
    profit_factor: Optional[float]
    trades: List[Dict]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Backtest da estrategia principal usando dados historicos da Binance.")
    parser.add_argument("--symbol", default="BTCUSDT", help="Par a ser avaliado (ex: BTCUSDT).")
    parser.add_argument("--interval", default="15m", help="Timeframe principal (ex: 15m, 1h).")
    parser.add_argument(
        "--confirmation-interval",
        default="1h",
        help="Timeframe de confirmacao (defina para 'none' para desabilitar)."
    )
    parser.add_argument("--start", help="Data inicial ISO8601 (ex: 2025-01-01T00:00:00).")
    parser.add_argument("--end", help="Data final ISO8601 (padrao = agora UTC).")
    parser.add_argument(
        "--days",
        type=int,
        default=7,
        help="Usado quando --start nao e informado. Busca os ultimos N dias."
    )
    parser.add_argument("--initial-balance", type=float, default=1000.0, help="Capital inicial em USDT.")
    parser.add_argument(
        "--risk-percent",
        type=float,
        default=2.0,
        help="Percentual de risco por trade utilizado pelo RiskManager."
    )
    parser.add_argument("--max-positions", type=int, default=1, help="Maximo de posicoes simultaneas permitidas.")
    parser.add_argument("--min-strength", type=int, default=50, help="Forca minima exigida do sinal (0-100).")
    parser.add_argument(
        "--allow-shorts",
        action="store_true",
        help="Permite abrir posicoes vendidas quando a estrategia gerar sinal SELL."
    )
    parser.add_argument(
        "--disable-confirmation",
        action="store_true",
        help="Ignora timeframe de confirmacao (forca sinais apenas com o timeframe principal)."
    )
    return parser.parse_args()


def _parse_datetime(value: Optional[str], fallback: datetime) -> datetime:
    if not value:
        return fallback
    cleaned = value.strip()
    if cleaned.endswith("Z"):
        cleaned = cleaned[:-1]
    dt = datetime.fromisoformat(cleaned)
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


def _format_ts(ts: datetime) -> str:
    return ts.astimezone(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")


def _fetch_klines(client: Client, symbol: str, interval: str, start: datetime, end: datetime) -> pd.DataFrame:
    start_str = start.strftime("%Y-%m-%d %H:%M:%S")
    end_str = end.strftime("%Y-%m-%d %H:%M:%S")
    klines = client.get_historical_klines(symbol=symbol, interval=interval, start_str=start_str, end_str=end_str)
    if not klines:
        return pd.DataFrame()

    columns = [
        "timestamp",
        "open",
        "high",
        "low",
        "close",
        "volume",
        "close_time",
        "quote_volume",
        "trades",
        "taker_buy_base",
        "taker_buy_quote",
        "ignore",
    ]
    df = pd.DataFrame(klines, columns=columns)
    numeric_cols = ["open", "high", "low", "close", "volume", "quote_volume", "taker_buy_base", "taker_buy_quote"]
    for col in numeric_cols:
        df[col] = pd.to_numeric(df[col], errors="coerce")
    df["timestamp"] = pd.to_datetime(df["timestamp"], unit="ms", utc=True)
    df = df.dropna(subset=["close", "high", "low", "volume"]).reset_index(drop=True)
    return df


def _first_valid_signal_index(df: pd.DataFrame) -> int:
    required = ["ema_fast", "ema_slow", "ema_50", "ema_200", "macd_hist", "rsi", "vwap"]
    indices: List[int] = []
    for col in required:
        idx = df[col].first_valid_index()
        if idx is not None:
            indices.append(int(idx))
    if not indices:
        return 1
    return max(1, max(indices))


def _get_higher_slice(higher_df: Optional[pd.DataFrame], current_ts: pd.Timestamp) -> Optional[pd.DataFrame]:
    if higher_df is None or higher_df.empty:
        return None
    pos = higher_df["timestamp"].searchsorted(current_ts, side="right") - 1
    if pos < 1:
        return None
    return higher_df.iloc[: pos + 1]


def _evaluate_exit(position: Dict, high_price: float, low_price: float) -> Tuple[Optional[float], Optional[str]]:
    exit_price = None
    reason = None
    if position["side"] == "BUY":
        if low_price <= position["stop_loss"]:
            exit_price = position["stop_loss"]
            reason = "STOP_LOSS"
        elif high_price >= position["take_profit"]:
            exit_price = position["take_profit"]
            reason = "TAKE_PROFIT"
    else:
        if high_price >= position["stop_loss"]:
            exit_price = position["stop_loss"]
            reason = "STOP_LOSS"
        elif low_price <= position["take_profit"]:
            exit_price = position["take_profit"]
            reason = "TAKE_PROFIT"
    return exit_price, reason


def run_backtest(
    strategy: TradingStrategy,
    risk_manager: RiskManager,
    df: pd.DataFrame,
    higher_df: Optional[pd.DataFrame],
    initial_balance: float,
    symbol: str,
    interval: str,
    confirmation_interval: Optional[str],
    allow_shorts: bool,
) -> BacktestResult:
    if df.empty:
        raise ValueError("Nenhum candle foi retornado para o periodo solicitado.")

    df = df.copy().sort_values("timestamp").reset_index(drop=True)
    df = strategy.calculate_indicators(df)
    df["volume_ma20"] = df["volume"].rolling(window=20).mean()

    if higher_df is not None and not higher_df.empty:
        higher_df = higher_df.copy().sort_values("timestamp").reset_index(drop=True)
        higher_df = strategy.calculate_indicators(higher_df)

    start_index = _first_valid_signal_index(df)
    if start_index >= len(df):
        raise ValueError("Nao ha candles suficientes para iniciar o backtest (indicadores continuam vazios).")

    balance = initial_balance
    equity_peak = balance
    max_drawdown = 0.0
    trades: List[Dict] = []
    position: Optional[Dict] = None
    wins = 0
    losses = 0

    for idx in range(start_index, len(df)):
        window = df.iloc[: idx + 1]
        candle = df.iloc[idx]
        current_ts = candle["timestamp"]
        higher_slice = _get_higher_slice(higher_df, current_ts) if higher_df is not None else None

        volume_ma = candle.get("volume_ma20", 0.0)
        if pd.isna(volume_ma) or volume_ma == 0:
            volume_ratio = 1.0
        else:
            volume_ratio = float(candle["volume"] / volume_ma)

        signal = strategy.generate_signal(window, higher_slice, volume_ratio)
        price = float(candle["close"])
        high_price = float(candle["high"])
        low_price = float(candle["low"])

        if position is not None:
            exit_price, exit_reason = _evaluate_exit(position, high_price, low_price)
            if exit_price is None and signal["signal"] in ("BUY", "SELL") and signal["signal"] != position["side"]:
                exit_price = price
                exit_reason = "OPPOSITE_SIGNAL"

            if exit_price is not None:
                if position["side"] == "BUY":
                    pnl = (exit_price - position["entry_price"]) * position["quantity"]
                else:
                    pnl = (position["entry_price"] - exit_price) * position["quantity"]
                balance += pnl
                if pnl >= 0:
                    wins += 1
                else:
                    losses += 1
                trades.append(
                    {
                        "side": position["side"],
                        "entry_price": round(position["entry_price"], 6),
                        "exit_price": round(exit_price, 6),
                        "quantity": position["quantity"],
                        "opened_at": _format_ts(position["opened_at"]),
                        "closed_at": _format_ts(current_ts),
                        "reason": exit_reason,
                        "pnl": round(pnl, 2),
                    }
                )
                position = None

        if position is None and signal["signal"] in ("BUY", "SELL"):
            if signal["signal"] == "SELL" and not allow_shorts:
                continue
            sizing = risk_manager.calculate_position_size(balance, price)
            if sizing and sizing.get("quantity", 0) > 0:
                stop_loss = signal.get("stop_loss")
                take_profit = signal.get("take_profit")
                if signal["signal"] == "BUY":
                    stop_loss = stop_loss or sizing["stop_loss"]
                    take_profit = take_profit or sizing["take_profit"]
                else:
                    stop_loss = stop_loss or (price + abs(price - sizing["stop_loss"]))
                    take_profit = take_profit or (price - abs(sizing["take_profit"] - price))
                if stop_loss is not None and take_profit is not None and take_profit != stop_loss:
                    position = {
                        "side": signal["signal"],
                        "entry_price": price,
                        "quantity": sizing["quantity"],
                        "stop_loss": float(stop_loss),
                        "take_profit": float(take_profit),
                        "opened_at": current_ts,
                    }

        equity = balance
        if position:
            if position["side"] == "BUY":
                equity += (price - position["entry_price"]) * position["quantity"]
            else:
                equity += (position["entry_price"] - price) * position["quantity"]
        equity_peak = max(equity_peak, equity)
        if equity_peak > 0:
            drawdown = (equity_peak - equity) / equity_peak
            max_drawdown = max(max_drawdown, drawdown)

    if position is not None:
        final_price = float(df.iloc[-1]["close"])
        if position["side"] == "BUY":
            pnl = (final_price - position["entry_price"]) * position["quantity"]
        else:
            pnl = (position["entry_price"] - final_price) * position["quantity"]
        balance += pnl
        if pnl >= 0:
            wins += 1
        else:
            losses += 1
        trades.append(
            {
                "side": position["side"],
                "entry_price": round(position["entry_price"], 6),
                "exit_price": round(final_price, 6),
                "quantity": position["quantity"],
                "opened_at": _format_ts(position["opened_at"]),
                "closed_at": _format_ts(df.iloc[-1]["timestamp"]),
                "reason": "FORCED_EXIT",
                "pnl": round(pnl, 2),
            }
        )

    profits = [t["pnl"] for t in trades if t["pnl"] > 0]
    losses_values = [abs(t["pnl"]) for t in trades if t["pnl"] < 0]
    profit_factor = None
    if profits and losses_values:
        total_loss = sum(losses_values)
        if total_loss > 0:
            profit_factor = sum(profits) / total_loss

    total_trades = len(trades)
    win_rate = (wins / total_trades * 100) if total_trades else 0.0
    final_balance = balance
    net_profit = final_balance - initial_balance
    roi = (net_profit / initial_balance * 100) if initial_balance else 0.0

    return BacktestResult(
        symbol=symbol,
        interval=interval,
        confirmation_interval=confirmation_interval,
        start=df.iloc[start_index]["timestamp"].to_pydatetime(),
        end=df.iloc[-1]["timestamp"].to_pydatetime(),
        initial_balance=initial_balance,
        final_balance=final_balance,
        total_trades=total_trades,
        winning_trades=wins,
        losing_trades=losses,
        win_rate=win_rate,
        net_profit=net_profit,
        roi=roi,
        max_drawdown_pct=max_drawdown * 100,
        profit_factor=profit_factor,
        trades=trades,
    )


def main() -> None:
    args = parse_args()
    now_utc = datetime.now(timezone.utc)
    start_default = now_utc - timedelta(days=args.days)
    start_dt = _parse_datetime(args.start, start_default)
    end_dt = _parse_datetime(args.end, now_utc)
    if start_dt >= end_dt:
        raise SystemExit("A data inicial precisa ser anterior a data final.")

    api_key = os.getenv("BINANCE_API_KEY", "")
    api_secret = os.getenv("BINANCE_API_SECRET", "")
    client = Client(api_key, api_secret)

    strategy = TradingStrategy(client, min_signal_strength=args.min_strength)
    strategy.timeframe = args.interval
    if not args.disable_confirmation:
        strategy.confirmation_timeframe = args.confirmation_interval

    print(f"[INFO] Baixando candles {args.interval} de {args.symbol} entre {_format_ts(start_dt)} e {_format_ts(end_dt)}...")
    df = _fetch_klines(client, args.symbol, args.interval, start_dt, end_dt)
    higher_df = None
    confirmation_interval = None
    if not args.disable_confirmation:
        confirmation_interval = args.confirmation_interval
        print(f"[INFO] Baixando candles {confirmation_interval} para confirmacao...")
        higher_df = _fetch_klines(client, args.symbol, confirmation_interval, start_dt, end_dt)

    risk_manager = RiskManager(
        risk_percentage=args.risk_percent,
        max_positions=args.max_positions,
    )

    result = run_backtest(
        strategy=strategy,
        risk_manager=risk_manager,
        df=df,
        higher_df=higher_df,
        initial_balance=args.initial_balance,
        symbol=args.symbol,
        interval=args.interval,
        confirmation_interval=confirmation_interval,
        allow_shorts=args.allow_shorts,
    )

    print("\n=== Resumo do Backtest ===")
    print(f"Par: {result.symbol} | Timeframe: {result.interval} | Confirmacao: {result.confirmation_interval or 'desativada'}")
    print(f"Periodo: {_format_ts(result.start)}  {_format_ts(result.end)}")
    print(f"Trades: {result.total_trades} (Vitorias: {result.winning_trades} | Derrotas: {result.losing_trades})")
    print(f"Win Rate: {result.win_rate:.2f}%")
    print(f"Balanco inicial: ${result.initial_balance:.2f} | Final: ${result.final_balance:.2f}")
    print(f"Lucro liquido: ${result.net_profit:.2f} | ROI: {result.roi:.2f}%")
    print(f"Max. Drawdown: {result.max_drawdown_pct:.2f}%")
    if result.profit_factor is not None:
        print(f"Profit Factor: {result.profit_factor:.2f}")

    if result.trades:
        print("\n Ultimos trades:")
        for trade in result.trades[-5:]:
            print(
                f"{trade['opened_at']}  {trade['closed_at']} | {trade['side']} @ {trade['entry_price']} "
                f" {trade['exit_price']} | PnL ${trade['pnl']:.2f} ({trade['reason']})"
            )
    else:
        print("\nNenhum trade executado no periodo escolhido.")


if __name__ == "__main__":
    main()
