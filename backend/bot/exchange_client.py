"""
Multi-exchange abstraction layer using ccxt.

Supports Binance, Kraken, and any ccxt-compatible exchange.
Paper trading works identically across all exchanges.
"""

import logging
import os
import time
from collections.abc import Callable
from typing import Any

import ccxt

from bot.market_cache import get_price_cache

logger = logging.getLogger(__name__)

# ── Exchange name mapping (config → ccxt) ──────────────────────────
EXCHANGE_CCXT_ID = {
    "binance": "binance",
    "kraken": "kraken",
    "coinbase": "coinbase",
    "kucoin": "kucoin",
}


class ExchangeError(Exception):
    """Base class for exchange errors."""

    def __init__(self, action: str, original: Any):
        self.action = action
        self.original = original
        message = f"{action}: {original}"
        super().__init__(message)


class ExchangeTransientError(ExchangeError):
    """Temporary error that should be retried."""


class ExchangeCriticalError(ExchangeError):
    """Critical error requiring operator attention."""


# ── Paper trade helpers ─────────────────────────────────────────────

def _is_paper_trade(manager: "ExchangeManager") -> bool:
    return getattr(manager, "_paper_trade", False)


def _simulate_fill_order(
    symbol: str, side: str, quantity: float, source: str = "PAPER_TRADE"
) -> dict:
    """Simulate a filled order using current cached price."""
    try:
        cache = get_price_cache()
        cached = cache.get(symbol)
        current_price = float(cached.get("price", 0)) if cached else 0.0
    except Exception:
        current_price = 0.0

    order_id = int(time.time() * 1000) % 10_000_000_000
    transact_time = int(time.time() * 1000)

    logger.info(
        "📝 PAPER TRADE: %s %s %s qty=%.6f @ %.4f (SIMULATED)",
        symbol, side, source, quantity, current_price,
    )
    return {
        "symbol": symbol,
        "orderId": order_id,
        "clientOrderId": f"paper_{order_id}",
        "transactTime": transact_time,
        "price": str(current_price),
        "origQty": str(quantity),
        "executedQty": str(quantity),
        "cummulativeQuoteQty": str(quantity * current_price),
        "status": "FILLED",
        "type": "MARKET",
        "side": side.upper(),
        "fills": [{"price": str(current_price), "qty": str(quantity)}],
        "_paper_trade": True,
    }


# ── ExchangeManager ──────────────────────────────────────────────────

class ExchangeManager:
    """Multi-exchange client manager using ccxt as the unified backend."""

    def __init__(self):
        self.exchange_id: str = ""
        self._ccxt_client: Any = None
        self._paper_trade: bool = False
        self._testnet: bool = False
        self._price_cache = get_price_cache()
        self.max_retries: int = 5
        self.retry_backoff: float = 0.5
        self._last_time_sync: float = 0.0
        self._time_sync_min_interval: float = 30.0

    # ── Initialization ───────────────────────────────────────────────

    def initialize(
        self,
        exchange: str = "binance",
        api_key: str = "",
        api_secret: str = "",
        testnet: bool = False,
        paper_trade: bool = True,
    ) -> bool:
        """Initialize the exchange client.

        Args:
            exchange: Exchange id ('binance', 'kraken', etc.)
            api_key: API key
            api_secret: API secret
            testnet: Use sandbox/testnet if available
            paper_trade: Simulate orders instead of sending real ones
        """
        try:
            if not api_key or not api_secret:
                logger.warning("%s API credentials not provided", exchange)
                return False

            self.exchange_id = exchange
            self._paper_trade = paper_trade
            self._testnet = testnet
            ccxt_id = EXCHANGE_CCXT_ID.get(exchange, exchange)

            # Build ccxt exchange instance
            exchange_class = getattr(ccxt, ccxt_id, None)
            if exchange_class is None:
                logger.error("Exchange '%s' not found in ccxt", exchange)
                return False

            config: dict = {
                "apiKey": api_key,
                "secret": api_secret,
                "enableRateLimit": True,
                "timeout": 30000,
            }

            if testnet and exchange == "binance":
                config["urls"] = {
                    "api": {
                        "public": "https://testnet.binance.vision/api",
                        "private": "https://testnet.binance.vision/api",
                    }
                }
                config["options"] = {"defaultType": "spot"}

            if exchange == "kraken":
                # Kraken sandbox/demo URL
                if testnet:
                    logger.info("Kraken demo mode — using sandbox URL")
                    # Kraken doesn't have a real sandbox, use Futures demo
                    # For spot, we rely on paper trading instead
                config["options"] = config.get("options", {})
                config["options"]["defaultType"] = "spot"

            self._ccxt_client = exchange_class(config)

            # Test connection (public endpoint, no auth needed)
            self._ccxt_client.load_markets()
            logger.info(
                "%s %s initialized — %d markets loaded (%s)",
                exchange.upper(),
                "TESTNET" if testnet else "MAINNET",
                len(self._ccxt_client.markets) if self._ccxt_client.markets else 0,
                "PAPER TRADING" if paper_trade else "LIVE",
            )
            return True

        except Exception as e:
            logger.error("Error initializing %s client: %s", exchange, e)
            return False

    @property
    def client(self) -> Any:
        """Return the underlying ccxt client (for backward compat)."""
        return self._ccxt_client

    @property
    def is_initialized(self) -> bool:
        return self._ccxt_client is not None

    @property
    def use_testnet(self) -> bool:
        return self._testnet

    # ── Standardized symbol (ccxt uses XXXX/YYYY format) ─────────────

    def _to_ccxt_symbol(self, symbol: str) -> str:
        """Convert 'BTCUSDT' to 'BTC/USDT' for ccxt."""
        # Already in ccxt format?
        if "/" in symbol:
            return symbol
        # Common quote assets
        for quote in ["USDT", "USD", "BTC", "ETH", "USDC", "EUR"]:
            if symbol.endswith(quote) and symbol != quote:
                base = symbol[: -len(quote)]
                return f"{base}/{quote}"
        return symbol  # fallback

    def _from_ccxt_symbol(self, ccxt_symbol: str) -> str:
        """Convert 'BTC/USDT' to 'BTCUSDT'."""
        return ccxt_symbol.replace("/", "")

    # ── Market data ──────────────────────────────────────────────────

    def get_symbol_price(self, symbol: str) -> float | None:
        """Get current price for a symbol."""
        if not self._ccxt_client:
            return None
        try:
            ticker = self._execute_with_retry(
                f"fetch_ticker:{symbol}",
                lambda: self._ccxt_client.fetch_ticker(self._to_ccxt_symbol(symbol)),
            )
            return float(ticker["last"]) if ticker.get("last") else None
        except (ExchangeTransientError, ExchangeCriticalError):
            raise
        except Exception as e:
            logger.error("Error getting price for %s: %s", symbol, e)
            raise ExchangeTransientError(f"get_symbol_price:{symbol}", e) from e

    def get_price_map(self, symbols: list[str]) -> dict[str, float]:
        """Get current prices for multiple symbols efficiently."""
        if not self._ccxt_client or not symbols:
            return {}

        symbol_set = set(symbols)
        prices: dict[str, float] = {}

        # Try cache first
        snapshot = self._price_cache.get("symbol_price_snapshot")
        if snapshot:
            for ticker in snapshot:
                sym = ticker.get("symbol", "")
                if sym in symbol_set:
                    try:
                        prices[sym] = float(ticker["last"])
                    except (TypeError, ValueError):
                        continue

        missing = symbol_set.difference(prices)

        if missing:
            try:
                all_tickers = self._execute_with_retry(
                    "fetch_tickers",
                    lambda: self._ccxt_client.fetch_tickers(),
                )
                self._price_cache.set("symbol_price_snapshot", list(all_tickers.values()), ttl=30)
                for sym, ticker in all_tickers.items():
                    ccxt_sym = self._from_ccxt_symbol(sym)
                    if ccxt_sym in missing and ticker.get("last"):
                        prices[ccxt_sym] = float(ticker["last"])
            except Exception as e:
                logger.warning("fetch_tickers failed: %s — falling back individually", e)
                for sym in list(missing):
                    try:
                        p = self.get_symbol_price(sym)
                        if p:
                            prices[sym] = p
                    except Exception:
                        pass

        return prices

    def get_symbol_precision(self, symbol: str) -> tuple[int, int, float, float]:
        """Get (qty_precision, price_precision, min_qty, step_size)."""
        if not self._ccxt_client:
            return (2, 2, 0.01, 0.01)

        try:
            ccxt_sym = self._to_ccxt_symbol(symbol)
            market = self._ccxt_client.market(ccxt_sym)
            if market:
                qty_precision = market.get("precision", {}).get("amount", 2) or 2
                price_precision = market.get("precision", {}).get("price", 2) or 2
                min_qty = market.get("limits", {}).get("amount", {}).get("min", 0.01) or 0.01
                step_size = market.get("limits", {}).get("amount", {}).get("step", 0.01) or 0.01
                return (
                    int(qty_precision) if qty_precision else 2,
                    int(price_precision) if price_precision else 2,
                    float(min_qty),
                    float(step_size),
                )
        except Exception as e:
            logger.warning("No market info for %s: %s", symbol, e)
        return (2, 2, 0.01, 0.01)

    def adjust_quantity(self, symbol: str, quantity: float) -> float:
        """Round quantity to exchange precision."""
        qty_precision, _, min_qty, step_size = self.get_symbol_precision(symbol)
        adjusted = (quantity // step_size) * step_size
        adjusted = round(adjusted, qty_precision)
        if adjusted < min_qty:
            logger.warning("Quantity %s below min %s for %s", adjusted, min_qty, symbol)
            return 0
        return adjusted

    # ── Account ──────────────────────────────────────────────────────

    def get_account_balance(self) -> float | None:
        """Get USDT balance."""
        if self._paper_trade:
            return float(os.getenv("PAPER_TRADE_BALANCE", 8000.0))

        if not self._ccxt_client:
            logger.warning("Exchange client not initialized")
            return None

        try:
            balance = self._execute_with_retry(
                "fetch_balance",
                lambda: self._ccxt_client.fetch_balance(),
            )
            usdt = float(balance.get("USDT", {}).get("free", 0) or 0)
            if usdt == 0:
                usdt = float(balance.get("USD", {}).get("free", 0) or 0)
            logger.info("Account balance: $%.2f USDT", usdt)
            return usdt
        except (ExchangeTransientError, ExchangeCriticalError):
            raise
        except Exception as e:
            logger.error("Error getting balance: %s", e)
            raise ExchangeTransientError("get_account_balance", e) from e

    # ── Orders ───────────────────────────────────────────────────────

    def place_order(
        self,
        symbol: str,
        side: str,
        quantity: float,
        price: float | None = None,
        order_type: str = "MARKET",
    ) -> dict:
        """Place a spot order (or simulate if paper trading)."""
        if _is_paper_trade(self):
            return _simulate_fill_order(symbol, side, quantity, "PAPER_TRADE")

        if not self._ccxt_client:
            raise RuntimeError("Exchange client not initialized")

        adjusted_qty = self.adjust_quantity(symbol, quantity)
        if adjusted_qty <= 0:
            raise ExchangeCriticalError(
                f"place_order:{symbol}:{side}",
                ValueError(f"Quantity {quantity} too small for {symbol}"),
            )

        ccxt_sym = self._to_ccxt_symbol(symbol)
        logger.info("Placing %s %s %s qty=%s", order_type, symbol, side, adjusted_qty)

        return self._execute_with_retry(
            f"place_order:{symbol}:{side}",
            lambda: self._ccxt_client.create_order(
                symbol=ccxt_sym,
                type=order_type.lower(),
                side=side.lower(),
                amount=adjusted_qty,
                price=price,
            ),
            critical=True,
        )

    def place_oco_order(
        self,
        symbol: str,
        quantity: float,
        take_profit_price: float,
        stop_price: float,
        stop_limit_price: float,
    ) -> dict | None:
        """Place OCO order (or skip if paper trading)."""
        if _is_paper_trade(self):
            logger.info("[OCO] %s: PAPER TRADE — monitoring in memory", symbol)
            return None

        if not self._ccxt_client:
            return None

        # ccxt doesn't have a unified OCO API — exchange-specific
        # For now, fall back to in-memory monitoring
        logger.warning("[OCO] %s: OCO not implemented for %s — using memory monitoring", symbol, self.exchange_id)
        return None

    def get_open_orders(self, symbol: str | None = None) -> list:
        """Get open orders."""
        if not self._ccxt_client:
            return []
        try:
            ccxt_sym = self._to_ccxt_symbol(symbol) if symbol else None
            return self._execute_with_retry(
                f"fetch_open_orders:{symbol}" if symbol else "fetch_open_orders",
                lambda: self._ccxt_client.fetch_open_orders(symbol=ccxt_sym),
            )
        except Exception as e:
            logger.warning("Error fetching open orders: %s", e)
            return []

    def cancel_order(self, symbol: str, order_id: str) -> bool:
        """Cancel an existing order."""
        if not self._ccxt_client:
            return False
        try:
            self._execute_with_retry(
                f"cancel_order:{symbol}:{order_id}",
                lambda: self._ccxt_client.cancel_order(order_id, self._to_ccxt_symbol(symbol)),
            )
            return True
        except Exception as e:
            logger.warning("Error canceling order %s: %s", order_id, e)
            return False

    # ── Binance-compat shims (used by strategy/selector) ─────────────────

    def get_orderbook_ticker(self, symbol: str) -> dict | None:
        """Binance-compat: returns {symbol, bidPrice, bidQty, askPrice, askQty} via order book."""
        if not self._ccxt_client:
            return None
        try:
            ccxt_sym = self._to_ccxt_symbol(symbol)
            ob = self._execute_with_retry(
                f"fetch_order_book:{symbol}",
                lambda: self._ccxt_client.fetch_order_book(ccxt_sym, limit=1),
            )
            bid = ob["bids"][0] if ob.get("bids") else [0, 0]
            ask = ob["asks"][0] if ob.get("asks") else [0, 0]
            return {
                "symbol": symbol,
                "bidPrice": str(bid[0]),
                "bidQty": str(bid[1]),
                "askPrice": str(ask[0]),
                "askQty": str(ask[1]),
            }
        except Exception as e:
            logger.warning("Error fetching order book ticker for %s: %s", symbol, e)
            return None

    def get_all_tickers(self) -> list[dict]:
        """Binance-compat: returns list of {symbol, priceChangePercent, quoteVolume, lastPrice, bidPrice, askPrice}."""
        if not self._ccxt_client:
            return []
        try:
            all_tickers = self._execute_with_retry(
                "fetch_tickers",
                lambda: self._ccxt_client.fetch_tickers(),
            )
            result = []
            for ccxt_sym, ticker in all_tickers.items():
                result.append({
                    "symbol": self._from_ccxt_symbol(ccxt_sym),
                    "priceChangePercent": str(ticker.get("percentage", 0) or 0),
                    "quoteVolume": str(ticker.get("quoteVolume", 0) or 0),
                    "lastPrice": str(ticker.get("last", 0) or 0),
                    "bidPrice": str(ticker.get("bid", 0) or 0),
                    "askPrice": str(ticker.get("ask", 0) or 0),
                })
            return result
        except Exception as e:
            logger.warning("Error fetching all tickers: %s", e)
            return []

    def get_klines(self, symbol: str, timeframe: str = "15m", limit: int = 200) -> list:
        """Get OHLCV candles."""
        if not self._ccxt_client:
            return []
        try:
            ccxt_sym = self._to_ccxt_symbol(symbol)
            ohlcv = self._execute_with_retry(
                f"fetch_ohlcv:{symbol}:{timeframe}",
                lambda: self._ccxt_client.fetch_ohlcv(ccxt_sym, timeframe=timeframe, limit=limit),
            )
            # ccxt returns [timestamp, open, high, low, close, volume]
            return ohlcv
        except Exception as e:
            logger.error("Error fetching klines for %s: %s", symbol, e)
            return []

    def get_ticker(self, symbol: str) -> dict:
        """Get full ticker data."""
        if not self._ccxt_client:
            return {}
        try:
            return self._execute_with_retry(
                f"fetch_ticker:{symbol}",
                lambda: self._ccxt_client.fetch_ticker(self._to_ccxt_symbol(symbol)),
            )
        except Exception as e:
            logger.error("Error fetching ticker for %s: %s", symbol, e)
            return {}

    # ── Retry logic ──────────────────────────────────────────────────

    def _execute_with_retry(
        self,
        action: str,
        func: Callable[[], Any],
        *,
        critical: bool = False,
        max_attempts: int | None = None,
    ) -> Any:
        attempts = max_attempts or self.max_retries
        last_exc: Exception | None = None

        for attempt in range(1, attempts + 1):
            try:
                return func()
            except ccxt.NetworkError as exc:
                last_exc = exc
                delay = self.retry_backoff * attempt
                logger.warning("%s network error (attempt %s/%s): %s — retry in %.1fs", action, attempt, attempts, exc, delay)
                time.sleep(delay)
                continue
            except ccxt.RateLimitExceeded as exc:
                last_exc = exc
                delay = self.retry_backoff * attempt * 2
                logger.warning("%s rate limited (attempt %s/%s) — retry in %.1fs", action, attempt, attempts, delay)
                time.sleep(delay)
                continue
            except ccxt.ExchangeError as exc:
                logger.error("%s exchange error: %s", action, exc)
                raise ExchangeCriticalError(action, exc) from exc
            except Exception as exc:
                last_exc = exc
                delay = self.retry_backoff * attempt
                if attempt < attempts:
                    logger.warning("%s unexpected error (attempt %s/%s): %s — retry in %.1fs", action, attempt, attempts, exc, delay)
                    time.sleep(delay)
                    continue
                if critical:
                    raise ExchangeCriticalError(action, exc) from exc
                raise ExchangeTransientError(action, exc) from exc

        failure_message = f"{action} failed after {attempts} attempts"
        if critical:
            raise ExchangeCriticalError(failure_message, last_exc or RuntimeError(action))
        raise ExchangeTransientError(failure_message, last_exc or RuntimeError(action))


# ── Singleton ────────────────────────────────────────────────────────

exchange_manager = ExchangeManager()
