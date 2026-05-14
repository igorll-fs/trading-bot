import logging
import os
import time
from collections.abc import Callable
from typing import Any

from binance.client import Client
from binance.exceptions import BinanceAPIException, BinanceOrderException, BinanceRequestException

from bot.market_cache import get_price_cache

logger = logging.getLogger(__name__)


class BinanceServiceError(Exception):
    """Base class for errors raised by BinanceClientManager operations."""

    def __init__(self, action: str, original: Any):
        self.action = action
        self.original = original
        message = f"{action}: {original}"
        super().__init__(message)


class BinanceTransientError(BinanceServiceError):
    """Temporary error that should be retried by the caller later."""


class BinanceCriticalError(BinanceServiceError):
    """Critical error that requires operator attention."""


class BinanceClientManager:
    def __init__(self):
        self.testnet_api_key = os.getenv("BINANCE_API_KEY", "")
        self.testnet_api_secret = os.getenv("BINANCE_API_SECRET", "")
        # Suporte a TESTNET_MODE (novo) ou BINANCE_TESTNET (legado) - padrao True
        testnet_env = os.getenv("TESTNET_MODE", os.getenv("BINANCE_TESTNET", "true"))
        self.use_testnet = str(testnet_env).strip().lower() in {"1", "true", "yes", "y", "on"}
        self.client = None
        self._price_cache = get_price_cache()
        # Configurações de retry mais robustas
        self.max_retries = int(os.getenv("BINANCE_MAX_RETRIES", "5"))  # Aumentado de 3 para 5
        self.retry_backoff = float(
            os.getenv("BINANCE_RETRY_BACKOFF", "0.5")
        )  # Reduzido para retry mais rápido
        # Erros que podem ser retentados
        self._retryable_api_errors = {-1003, -1015, -1021, -1001}  # Adicionado -1001 (DISCONNECTED)
        self._timestamp_error_code = -1021
        self._last_time_sync = 0.0
        self._time_sync_min_interval = 30.0  # Sync a cada 30s ao invés de 60s
        self._recv_window = 60000  # 60 segundos de tolerância para timestamp
        self._paper_trade = str(os.getenv("PAPER_TRADE", "")).strip().lower() in {"1", "true", "yes", "y", "on"}

    def initialize(self, api_key=None, api_secret=None, testnet=None):
        """Initialize Binance client with provided or env credentials"""
        try:
            key = api_key or self.testnet_api_key
            secret = api_secret or self.testnet_api_secret
            use_test = testnet if testnet is not None else self.use_testnet

            # Atualizar use_testnet para refletir o modo atual
            self.use_testnet = use_test

            if not key or not secret:
                logger.warning("Binance API credentials not provided")
                return False

            if use_test:
                # Testnet Spot URLs
                self.client = Client(key, secret, testnet=True)
                self.client.API_URL = "https://testnet.binance.vision/api"
                logger.info("Using Binance SPOT TESTNET (virtual funds)")
            else:
                # Production Binance Spot
                self.client = Client(key, secret)
                logger.info("Using Binance SPOT MAINNET (real funds)")

            # Test connection
            self.client.ping()

            # Sincronizar timestamp com servidor Binance para evitar erros -1021
            self._sync_server_time(force=True)

            logger.info("Binance client connected successfully")
            return True

        except BinanceAPIException as e:
            logger.error(f"Binance API error: {e}")
            return False
        except Exception as e:
            logger.error(f"Error initializing Binance client: {e}")
            return False

    def _sync_server_time(self, force: bool = False) -> None:
        """Synchronize timestamp offset with Binance to avoid -1021 errors."""
        if not self.client:
            return
        now = time.time()
        if not force and (now - self._last_time_sync) < self._time_sync_min_interval:
            return
        try:
            # Múltiplas tentativas de sync para maior robustez
            for attempt in range(3):
                try:
                    server_time = self.client.get_server_time()
                    local_time = int(time.time() * 1000)
                    time_diff = server_time["serverTime"] - local_time
                    self.client.timestamp_offset = time_diff
                    self._last_time_sync = time.time()

                    # Log apenas se offset significativo (>1s)
                    if abs(time_diff) > 1000:
                        logger.warning(
                            f"Timestamp offset significativo: {time_diff}ms - relogio local pode estar dessincronizado"
                        )
                    else:
                        logger.debug(f"Timestamp offset atualizado: {time_diff}ms")
                    return
                except Exception:
                    if attempt < 2:
                        time.sleep(0.5)
                        continue
                    raise
        except Exception as exc:
            logger.error(f"Erro ao sincronizar timestamp com Binance (apos 3 tentativas): {exc}")

    def _is_retryable_api_error(self, exc: BinanceAPIException) -> bool:
        return exc.code in self._retryable_api_errors

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
            except BinanceAPIException as exc:
                last_exc = exc
                if exc.code == self._timestamp_error_code:
                    logger.warning("Erro de timestamp (%s) em %s. Realinhando...", exc.code, action)
                    self._sync_server_time(force=True)
                if self._is_retryable_api_error(exc):
                    delay = self.retry_backoff * attempt
                    logger.warning(
                        "Binance API %s falhou (code=%s). Tentativa %s/%s - retry em %.1fs",
                        action,
                        exc.code,
                        attempt,
                        attempts,
                        delay,
                    )
                    time.sleep(delay)
                    continue
                logger.error("Binance API erro nao recuperavel em %s: %s", action, exc)
                raise BinanceCriticalError(action, exc) from exc
            except BinanceRequestException as exc:
                last_exc = exc
                delay = self.retry_backoff * attempt
                logger.warning(
                    "Erro de requisicao em %s: %s (tentativa %s/%s) - retry em %.1fs",
                    action,
                    exc,
                    attempt,
                    attempts,
                    delay,
                )
                time.sleep(delay)
                continue
            except BinanceOrderException as exc:
                logger.error("Ordem rejeitada em %s: %s", action, exc)
                raise BinanceCriticalError(action, exc) from exc
            except Exception as exc:
                last_exc = exc
                delay = self.retry_backoff * attempt
                if attempt < attempts:
                    logger.warning(
                        "Erro inesperado em %s: %s (tentativa %s/%s) - retry em %.1fs",
                        action,
                        exc,
                        attempt,
                        attempts,
                        delay,
                    )
                    time.sleep(delay)
                    continue
                if critical:
                    raise BinanceCriticalError(action, exc) from exc
                raise BinanceTransientError(action, exc) from exc

        failure_message = f"{action} falhou apos {attempts} tentativas"
        if critical:
            raise BinanceCriticalError(failure_message, last_exc or RuntimeError(action))
        raise BinanceTransientError(failure_message, last_exc or RuntimeError(action))

    def get_account_balance(self):
        """Get account balance for Spot trading"""
        try:
            if not self.client:
                logger.warning("Binance client not initialized, cannot get balance")
                return None

            # Sincronizar timestamp antes de chamadas autenticadas
            self._sync_server_time()

            # Usar recvWindow maior (60s) para tolerar diferenca de timestamp
            account = self._execute_with_retry(
                "get_account_balance",
                lambda: self.client.get_account(recvWindow=self._recv_window),
                critical=False,
            )
            # Buscar saldo USDT
            usdt_balance = next(
                (float(asset["free"]) for asset in account["balances"] if asset["asset"] == "USDT"),
                0.0,
            )
            logger.info(f"Spot account balance retrieved: ${usdt_balance} USDT")
            return usdt_balance
        except BinanceTransientError:
            raise
        except BinanceCriticalError:
            raise
        except Exception as e:
            logger.error(f"Error getting balance: {e}")
            raise BinanceTransientError("get_account_balance", e) from e

    def get_symbol_price(self, symbol):
        """Get current symbol price for Spot"""
        try:
            if not self.client:
                return None
            ticker = self._execute_with_retry(
                f"get_symbol_price:{symbol}",
                lambda: self.client.get_symbol_ticker(symbol=symbol),
                critical=False,
            )
            return float(ticker["price"])
        except BinanceTransientError:
            raise
        except BinanceCriticalError:
            raise
        except Exception as e:
            logger.error(f"Error getting price for {symbol}: {e}")
            raise BinanceTransientError(f"get_symbol_price:{symbol}", e) from e

    def get_price_map(self, symbols):
        """Get current prices for a collection of symbols with minimal API calls"""
        try:
            if not self.client or not symbols:
                return {}

            symbol_set = set(symbols)
            prices: dict[str, float] = {}

            # Primeiro tenta preencher via snapshot em cache
            snapshot = self._price_cache.get("symbol_price_snapshot")
            if snapshot:
                for ticker in snapshot:
                    sym = ticker.get("symbol")
                    if sym in symbol_set:
                        try:
                            prices[sym] = float(ticker["price"])
                        except (TypeError, ValueError):
                            continue

            missing = symbol_set.difference(prices)

            # Se ainda falta e não há snapshot válido, baixa uma vez e guarda
            if missing:

                def fetch_all():
                    return self._execute_with_retry(
                        "get_symbol_ticker_snapshot",
                        lambda: self.client.get_symbol_ticker(),
                        critical=False,
                    )

                snapshot = self._price_cache.get_or_set("symbol_price_snapshot", fetch_all)
                if snapshot:
                    for ticker in snapshot:
                        sym = ticker.get("symbol")
                        if sym in missing:
                            try:
                                prices[sym] = float(ticker["price"])
                            except (TypeError, ValueError):
                                continue
                    missing = symbol_set.difference(prices)

            # Fallback pontual para símbolos que continuarem faltando
            for symbol in list(missing):
                ticker = self._execute_with_retry(
                    f"get_symbol_ticker:{symbol}",
                    lambda sym=symbol: self.client.get_symbol_ticker(symbol=sym),
                    critical=False,
                )
                if ticker and "price" in ticker:
                    prices[symbol] = float(ticker["price"])

            return prices
        except (BinanceTransientError, BinanceCriticalError):
            raise
        except Exception as e:
            logger.error(f"Error getting bulk prices: {e}")
            raise BinanceTransientError("get_price_map", e) from e

    def get_symbol_precision(self, symbol: str) -> tuple:
        """Get quantity and price precision for a symbol.

        Returns:
            tuple: (quantity_precision, price_precision, min_qty, step_size)
        """
        if not self.client:
            return (2, 2, 0.01, 0.01)  # defaults

        try:
            info = self.client.get_symbol_info(symbol)
            if not info:
                logger.warning(f"No info found for {symbol}, using defaults")
                return (2, 2, 0.01, 0.01)

            qty_precision = 2
            price_precision = 2
            min_qty = 0.01
            step_size = 0.01

            for f in info.get("filters", []):
                if f["filterType"] == "LOT_SIZE":
                    step_size = float(f["stepSize"])
                    min_qty = float(f["minQty"])
                    # Calculate precision from step size
                    if step_size >= 1:
                        qty_precision = 0
                    else:
                        qty_precision = len(str(step_size).rstrip("0").split(".")[-1])
                elif f["filterType"] == "PRICE_FILTER":
                    tick_size = float(f["tickSize"])
                    if tick_size >= 1:
                        price_precision = 0
                    else:
                        price_precision = len(str(tick_size).rstrip("0").split(".")[-1])

            return (qty_precision, price_precision, min_qty, step_size)
        except Exception as e:
            logger.warning(f"Error getting symbol precision for {symbol}: {e}")
            return (2, 2, 0.01, 0.01)

    def adjust_quantity(self, symbol: str, quantity: float) -> float:
        """Adjust quantity to match symbol's precision requirements."""
        qty_precision, _, min_qty, step_size = self.get_symbol_precision(symbol)

        # Round down to step size
        adjusted = (quantity // step_size) * step_size

        # Apply precision
        adjusted = round(adjusted, qty_precision)

        # Ensure minimum
        if adjusted < min_qty:
            logger.warning(f"Quantity {adjusted} below min {min_qty} for {symbol}")
            return 0

        return adjusted

    def place_order(self, symbol, side, quantity, price=None, order_type="MARKET"):
        """Place a Spot order (simulated when PAPER_TRADE=true)"""

        # ── PAPER TRADING SAFETY LOCK ──────────────────────────────────
        if _is_paper_trade(self):
            return _simulate_fill_order(symbol, side, quantity, "PAPER_TRADE")

        if not self.client:
            raise RuntimeError("Binance client not initialized")

        # Adjust quantity to match symbol's precision
        adjusted_qty = self.adjust_quantity(symbol, quantity)
        if adjusted_qty <= 0:
            raise BinanceCriticalError(
                f"place_order:{symbol}:{side}",
                ValueError(f"Quantity {quantity} too small for {symbol}"),
            )

        logger.info(f"Quantity adjusted for {symbol}: {quantity} -> {adjusted_qty}")

        params = {
            "symbol": symbol,
            "side": side,
            "type": order_type,
            "quantity": adjusted_qty,
            "recvWindow": self._recv_window,  # Tolerância de timestamp
        }

        if order_type == "LIMIT" and price:
            params["price"] = price
            params["timeInForce"] = "GTC"

        def submit_order():
            # Sincronizar timestamp antes de enviar ordem
            self._sync_server_time()
            order = self.client.create_order(**params)
            logger.info("Placed order %s %s qty=%s", symbol, side, adjusted_qty)
            return order

        return self._execute_with_retry(
            f"place_order:{symbol}:{side}",
            submit_order,
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
        """Coloca uma ordem OCO (SELL) após compra: TP (LIMIT) + SL (STOP_LIMIT) no Binance.

        Para Spot BUY: OCO de venda com TP em cima e SL abaixo.
        - take_profit_price: preço alvo para fechar com lucro
        - stop_price:        gatilho que ativa a ordem STOP_LIMIT
        - stop_limit_price:  preço de execução após o gatilho (ligeiramente abaixo do stop)

        Retorna o resultado da API ou None se OCO não suportado/falhou.
        """
        # ── PAPER TRADING SAFETY LOCK ──────────────────────────────────
        if _is_paper_trade(self):
            logger.info("[OCO] %s: PAPER TRADE — OCO não necessário (monitoramento em memória)", symbol)
            return None

        if not self.client:
            return None

        adjusted_qty = self.adjust_quantity(symbol, quantity)
        if adjusted_qty <= 0:
            logger.warning("OCO: quantidade inválida para %s (%.8f)", symbol, quantity)
            return None

        self._sync_server_time()

        def submit_oco():
            return self.client.create_oco_order(
                symbol=symbol,
                side="SELL",
                quantity=adjusted_qty,
                price=str(take_profit_price),  # Alvo de lucro (LIMIT)
                stopPrice=str(stop_price),  # Gatilho de stop
                stopLimitPrice=str(stop_limit_price),  # Preço da STOP_LIMIT
                stopLimitTimeInForce="GTC",
                recvWindow=self._recv_window,
            )

        try:
            result = self._execute_with_retry(
                f"place_oco:{symbol}",
                submit_oco,
                critical=False,
            )
            logger.info(
                "[OCO] %s: TP=%.4f SL_trigger=%.4f SL_limit=%.4f qty=%.6f",
                symbol,
                take_profit_price,
                stop_price,
                stop_limit_price,
                adjusted_qty,
            )
            return result
        except Exception as exc:
            # OCO pode falhar se símbolo não suporta (ex: preço já atingido, filtros)
            logger.warning(
                "[OCO] Falha ao criar OCO para %s: %s — usando monitoramento em memória",
                symbol,
                exc,
            )
            return None

    def get_open_orders(self, symbol=None):
        """Get open Spot orders"""
        if not self.client:
            return []

        # Sincronizar timestamp antes de chamada autenticada
        self._sync_server_time()

        action = f"get_open_orders:{symbol}" if symbol else "get_open_orders"
        fetch = (
            (lambda: self.client.get_open_orders(symbol=symbol, recvWindow=self._recv_window))
            if symbol
            else (lambda: self.client.get_open_orders(recvWindow=self._recv_window))
        )

        return self._execute_with_retry(
            action,
            fetch,
            critical=False,
        )

    def cancel_order(self, symbol, order_id):
        """Cancel a Spot order"""
        if not self.client:
            return False

        # Sincronizar timestamp antes de cancelar
        self._sync_server_time()

        self._execute_with_retry(
            f"cancel_order:{symbol}:{order_id}",
            lambda: self.client.cancel_order(
                symbol=symbol, orderId=order_id, recvWindow=self._recv_window
            ),
            critical=False,
        )
        return True


# ── Paper Trading Helpers ──────────────────────────────────────────────

def _is_paper_trade(manager: "BinanceClientManager") -> bool:
    """Check if paper trading mode is active (safety: never hits real API for orders)."""
    return getattr(manager, "_paper_trade", False)


def _simulate_fill_order(symbol: str, side: str, quantity: float, source: str = "PAPER") -> dict:
    """Create a simulated FILLED order dict with current market price.
    
    The returned dict mimics Binance's create_order response so the rest of the
    bot (position tracking, P&L, learning) works identically — just with simulated
    fills at real market prices.
    """
    import time as _time
    
    # Get current price from the manager's price cache
    current_price = 0.0
    try:
        cached = binance_manager._price_cache.get(symbol)
        if cached and _time.time() - cached.get("ts", 0) < 30:
            current_price = float(cached.get("price", 0))
    except Exception:
        pass
    
    order_id = int(_time.time() * 1000) % 10_000_000_000  # Pseudo-unique ID
    transact_time = int(_time.time() * 1000)
    
    logger.info(
        "📝 PAPER TRADE: %s %s %s qty=%.6f @ %.4f (SIMULATED — no real order)",
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
        "fills": [
            {
                "price": str(current_price),
                "qty": str(quantity),
                "commission": "0",
                "commissionAsset": "USDT",
            }
        ],
        "_paper_trade": True,
    }


binance_manager = BinanceClientManager()
