import asyncio
import json
import logging
import os
import time
from collections import deque
from datetime import UTC, datetime, timedelta
from typing import Any

import pandas as pd

# Circuit breaker defaults - mais tolerante para evitar pausas desnecessárias
DEFAULT_MAX_CONSECUTIVE_FAILURES = 10  # Aumentado de 5 para 10
DEFAULT_CIRCUIT_BREAKER_COOLDOWN = 120  # Reduzido de 5 min para 2 min

logger = logging.getLogger(__name__)

from bot.advanced_learning import AdvancedLearningSystem
from bot.binance_client import (
    BinanceCriticalError,
    BinanceTransientError,
    binance_manager,
)
from bot.config import BotConfig, load_bot_config
from bot.risk_manager import RiskManager
from bot.selector import CryptoSelector
from bot.strategy import TradingStrategy
from bot.telegram_client import telegram_notifier

# ML Signal Filter - modelo treinado com dados historicos
try:
    from ml.ml_signal_filter import get_ml_filter

    ML_FILTER_AVAILABLE = True
except ImportError:
    ML_FILTER_AVAILABLE = False

# LLM Analyzer - Ollama integration for AI-powered decisions
try:
    from bot.llm_analyzer import get_llm_analyzer

    LLM_ANALYZER_AVAILABLE = True
except ImportError:
    LLM_ANALYZER_AVAILABLE = False
    logger.warning("LLM Analyzer module not found - AI analysis disabled")

# LLM Market Analyzer - Advanced market regime analysis with AI
try:
    from bot.llm_market_analyzer import get_market_analyzer

    LLM_MARKET_ANALYZER_AVAILABLE = True
except ImportError:
    LLM_MARKET_ANALYZER_AVAILABLE = False
    logger.warning("LLM Market Analyzer not available - using basic analysis")

# LLM Risk Advisor - Advanced risk management with 5 AI features
try:
    from bot.llm_risk_advisor import get_risk_advisor

    LLM_RISK_ADVISOR_AVAILABLE = True
except ImportError:
    LLM_RISK_ADVISOR_AVAILABLE = False
    logger.warning("LLM Risk Advisor not available - using base risk management")

# Multi-Strategy Engine
try:
    from bot.strategy_engine import StrategyEngine
    from bot.strategies import (
        TrendFollowingStrategy,
        MeanReversionStrategy,
        BreakoutStrategy,
        GridDCAStrategy,
        MLPrimaryStrategy,
    )
    STRATEGY_ENGINE_AVAILABLE = True
except ImportError:
    STRATEGY_ENGINE_AVAILABLE = False
    logger.warning("Strategy Engine not available - using legacy single-strategy mode")


class TradingBot:
    def __init__(self, db):
        self.db = db
        self.is_running = False
        self.positions: list[dict] = []
        self.config = BotConfig.from_env()
        self.risk_manager = RiskManager(
            risk_percentage=self.config.risk_percentage,
            max_positions=self.config.max_positions,
            leverage=1,  # Spot trading = no leverage
            stop_loss_percentage=self.config.risk_stop_loss_percentage,
            reward_ratio=self.config.risk_reward_ratio,
            trailing_activation=self.config.risk_trailing_activation,
            trailing_step=self.config.risk_trailing_step,
            use_position_cap=getattr(self.config, "risk_use_position_cap", True),
        )
        self.learning_system = AdvancedLearningSystem(db)

        # ML Signal Filter - modelo treinado com dados historicos
        self.ml_filter = None
        if ML_FILTER_AVAILABLE:
            try:
                self.ml_filter = get_ml_filter()
                if self.ml_filter.loaded:
                    logger.info("[ML] Filtro de sinais ML carregado com sucesso!")
                    logger.info(
                        "[ML] Accuracy: %.2f%% | Min confidence: %.2f",
                        self.ml_filter.metrics.get("accuracy", 0) * 100,
                        self.ml_filter.min_confidence,
                    )
                else:
                    logger.warning("[ML] Modelo nao encontrado - filtro ML desabilitado")
            except Exception as e:
                logger.warning("[ML] Erro ao carregar filtro ML: %s", e)
        else:
            logger.info("[ML] Modulo ML nao disponivel - usando apenas regras base")

        # LLM Analyzer - AI decision support (inicializado imediatamente)
        self.llm_analyzer = None
        if LLM_ANALYZER_AVAILABLE:
            try:
                self.llm_analyzer = get_llm_analyzer()
                logger.info(
                    "[LLM] Analyzer instanciado - verificacao de disponibilidade em initialize()"
                )
            except Exception as e:
                logger.warning("[LLM] Erro ao instanciar Analyzer: %s", e)

        # LLM Market Analyzer - Advanced market analysis
        self.market_analyzer = None
        if LLM_MARKET_ANALYZER_AVAILABLE:
            try:
                self.market_analyzer = get_market_analyzer()
                logger.info("[LLM Market] Advanced market analyzer inicializado!")
            except Exception as e:
                logger.warning("[LLM Market] Erro ao instanciar: %s", e)

        # LLM Risk Advisor - 5 AI features for risk management
        self.risk_advisor = None
        if LLM_RISK_ADVISOR_AVAILABLE:
            try:
                self.risk_advisor = get_risk_advisor()
                logger.info("[LLM Risk Advisor] Sistema inteligente de risco inicializado!")
            except Exception as e:
                logger.warning("[LLM Risk Advisor] Erro ao instanciar: %s", e)

        # Multi-Strategy Engine
        self.strategy_engine = None
        self._ml_primary_strategy = None
        if STRATEGY_ENGINE_AVAILABLE and self.config.multi_strategy_enabled:
            try:
                binance_client = None  # Will be set in initialize()
                self._ml_primary_strategy = MLPrimaryStrategy(
                    client=None,
                    min_score=self.config.strategy_min_signal_strength,
                    model_confidence_threshold=self.config.ml_confidence_threshold,
                    retrain_interval_hours=self.config.ml_retrain_interval_hours,
                )
                self.strategy_engine = StrategyEngine()
                self.strategy_engine.register(TrendFollowingStrategy(
                    client=None,
                    min_signal_strength=self.config.strategy_min_signal_strength,
                    confirmation_timeframe=self.config.strategy_confirmation_timeframe,
                ))
                self.strategy_engine.register(MeanReversionStrategy(
                    client=None,
                    rsi_oversold=self.config.meanrev_rsi_oversold,
                    rsi_overbought=self.config.meanrev_rsi_overbought,
                    bb_squeeze_threshold=self.config.meanrev_bb_squeeze_threshold,
                ))
                self.strategy_engine.register(BreakoutStrategy(
                    client=None,
                    donchian_period=self.config.breakout_donchian_period,
                    atr_expansion_threshold=self.config.breakout_atr_expansion,
                ))
                self.strategy_engine.register(GridDCAStrategy(
                    client=None,
                    grid_levels=self.config.grid_levels,
                    level_spacing_pct=self.config.grid_level_spacing_pct,
                ))
                self.strategy_engine.register(self._ml_primary_strategy)
                logger.info(
                    "[StrategyEngine] Multi-strategy mode — %d strategies: %s",
                    len(self.strategy_engine.strategy_names),
                    ", ".join(self.strategy_engine.strategy_names),
                )
            except Exception as e:
                logger.warning("[StrategyEngine] Init failed, fallback to legacy: %s", e)
                self.strategy_engine = None

        self.selector = None
        self.strategy = None
        self.check_interval = self.config.loop_interval_seconds
        self._loop_task: asyncio.Task | None = None
        self._balance_cache = {"value": 0.0, "timestamp": 0.0}
        self.balance_cache_ttl = self.config.balance_cache_ttl
        self.observation_alert_interval = self.config.observation_alert_interval
        self._last_observation_notice = 0.0
        self._positions_cache_limit = 500
        self.last_error: str | None = None
        self.last_risk_snapshot: dict[str, Any] | None = None

        # Risco e proteções adicionais
        self.use_position_cap = getattr(self.config, "risk_use_position_cap", True)
        self.daily_drawdown_limit_pct = getattr(self.config, "daily_drawdown_limit_pct", 0.0)
        self.weekly_drawdown_limit_pct = getattr(self.config, "weekly_drawdown_limit_pct", 0.0)
        self.api_latency_threshold = float(os.getenv("API_LATENCY_THRESHOLD", "2.0"))
        self._current_drawdown_pct: float = 0.0  # Atualizado em _check_drawdown_limits
        # Cache para _check_drawdown_limits — evita 2 queries MongoDB a cada ciclo de 15s
        self._drawdown_cache: dict[str, Any] = {"result": True, "ts": 0.0, "ttl": 60.0}
        # Contador de sinais na última hora (para regime adaptation)
        # deque sem maxlen: entradas antigas são removidas via popleft
        # (limpeza lazy por tempo, não por quantidade — sinais por hora variam)
        self._signals_last_hour: deque = deque()  # timestamps float (monotonic)

        # Métricas simples
        self.metrics = {
            "orders_submitted": 0,
            "binance_errors": 0,
            "last_loop_ms": None,
            "last_order_symbol": None,
            "last_order_timestamp": None,
        }

        # Circuit breaker: pausa bot após falhas consecutivas
        self._consecutive_failures = 0
        self._max_consecutive_failures = DEFAULT_MAX_CONSECUTIVE_FAILURES
        self._circuit_breaker_cooldown = DEFAULT_CIRCUIT_BREAKER_COOLDOWN
        self._circuit_open_until: float = 0.0

        # Cooldown por símbolo após stop loss (evita recomprar o que caiu)
        self._sl_cooldown_minutes = int(os.getenv("SYMBOL_SL_COOLDOWN_MINUTES", "0"))
        self._sl_cooldown: dict[str, float] = {}  # symbol → timestamp do SL

        # Asyncio locks para proteger estado compartilhado
        self._positions_lock = asyncio.Lock()
        self._balance_lock = asyncio.Lock()

    async def _run_blocking(self, func, *args, **kwargs):
        """Run blocking code in a background thread to keep the event loop responsive"""
        start = time.perf_counter()
        result = await asyncio.to_thread(func, *args, **kwargs)
        duration = time.perf_counter() - start
        if duration > self.api_latency_threshold:
            logger.warning(
                "Latencia alta em chamada de API: %.2fs (limite %.2fs) func=%s",
                duration,
                self.api_latency_threshold,
                getattr(func, "__name__", str(func)),
            )
            # Latencia alta = aviso, NAO falha — nao aciona circuit breaker
        # Reset do circuit breaker é feito explicitamente em _get_balance e
        # _get_price_map — operações que medem saúde real da exchange.
        # Não resetar aqui para evitar que chamadas auxiliares (get_symbol_precision,
        # get_orderbook_ticker, etc.) apaguem falhas legítimas.
        return result

    async def _notify_observing(self, note: str | None = None, force: bool = False):
        """Send observation update to Telegram when bot is idle"""
        if self.positions:
            return

        try:
            loop = asyncio.get_running_loop()
            current_time = loop.time()
        except RuntimeError:
            current_time = None

        if not force and current_time is not None:
            if (current_time - self._last_observation_notice) < self.observation_alert_interval:
                return

        await telegram_notifier.notify_monitoring_async(note)

        if current_time is not None:
            self._last_observation_notice = current_time

    async def _get_account_balance(self, force_refresh: bool = False) -> float | None:
        """Return cached account balance to avoid hitting the API on every iteration.
        
        In paper trading mode, returns the configured paper balance (default 8000 USDT).
        In live mode, fetches real balance from Binance API with caching.
        """
        # Paper mode: use configured paper balance, no API call needed
        if getattr(binance_manager, "_paper_trade", False):
            paper_balance = float(os.getenv("PAPER_TRADE_BALANCE", 8000.0))
            return paper_balance
        
        async with self._balance_lock:
            loop = asyncio.get_running_loop()
            elapsed = loop.time() - self._balance_cache["timestamp"]

            if not force_refresh and elapsed < self.balance_cache_ttl:
                return self._balance_cache["value"]

            try:
                balance = await self._run_blocking(binance_manager.get_account_balance)
                self._reset_circuit_breaker()  # Sucesso: resetar contador
            except BinanceTransientError as exc:
                logger.warning("Problema temporario ao buscar saldo: %s", exc)
                self._record_failure()
                self.metrics["binance_errors"] += 1
                return None
            except BinanceCriticalError as exc:
                logger.error("Erro critico ao buscar saldo: %s", exc)
                self._record_failure()
                self.metrics["binance_errors"] += 1
                await telegram_notifier.send_message_async(
                    f"Erro critico ao consultar saldo na {self.config.exchange.upper()}. Verifique credenciais ou limite de API."
                )
                return None

            if balance is not None:
                self._balance_cache["value"] = balance
                self._balance_cache["timestamp"] = loop.time()

            return balance

    async def _get_price_map(self, symbols):
        """Fetch price map for symbols using a single API request when possible"""
        if not symbols:
            return {}
        try:
            result = await self._run_blocking(binance_manager.get_price_map, symbols)
            self._reset_circuit_breaker()  # Sucesso: resetar contador
            return result
        except BinanceTransientError as exc:
            logger.warning("Falha temporaria ao buscar precos: %s", exc)
            self._record_failure()
            self.metrics["binance_errors"] += 1
            return {}
        except BinanceCriticalError as exc:
            logger.error("Erro critico ao buscar precos: %s", exc)
            self._record_failure()
            self.metrics["binance_errors"] += 1
            await telegram_notifier.send_message_async(
                f"Erro critico ao buscar precos na {self.config.exchange.upper()}. Cheque as credenciais ou status da API."
            )
            return {}

    async def _check_drawdown_limits(self, balance: float) -> bool:
        """Check daily/weekly drawdown limits; pause if exceeded.

        Resultado cacheado por 60s para evitar queries MongoDB a cada ciclo de 15s.
        Cache é invalidado imediatamente quando o bot é pausado.
        """
        if balance is None or balance <= 0:
            return True

        day_limit = getattr(self, "daily_drawdown_limit_pct", 0.0) or 0.0
        week_limit = getattr(self, "weekly_drawdown_limit_pct", 0.0) or 0.0
        if day_limit <= 0 and week_limit <= 0:
            return True

        # Verificar cache (TTL 60s)
        import time as _time

        now_ts = _time.monotonic()
        cache = self._drawdown_cache
        if (now_ts - cache["ts"]) < cache["ttl"]:
            return cache["result"]

        now = datetime.now(UTC)
        day_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
        week_start = day_start - timedelta(days=day_start.weekday())

        async def _pnl_since(start_dt):
            trades = await self.db.trades.find(
                {"closed_at": {"$gte": start_dt.isoformat()}}, {"pnl": 1, "_id": 0}
            ).to_list(1000)
            return sum(t.get("pnl", 0) for t in trades)

        if day_limit > 0:
            day_pnl = await _pnl_since(day_start)
            # Salvar drawdown percentual para uso em outros módulos (ex: LLM risk advisor)
            if balance > 0 and day_pnl < 0:
                self._current_drawdown_pct = abs(day_pnl) / balance * 100
            day_limit_value = -(day_limit / 100) * balance
            if day_pnl <= day_limit_value:
                logger.error(
                    "Limite de perda diaria atingido: pnl=%.2f limite=%.2f (%.2f%%)",
                    day_pnl,
                    day_limit_value,
                    -day_limit,
                )
                await telegram_notifier.send_message_async(
                    f"⏸️ Bot pausado: perda diaria {day_pnl:.2f} <= limite {day_limit_value:.2f} ({day_limit:.1f}%)."
                )
                self.is_running = False
                self.last_error = "Limite de perda diaria atingido"
                self._drawdown_cache = {"result": False, "ts": now_ts, "ttl": 60.0}
                return False

        if week_limit > 0:
            week_pnl = await _pnl_since(week_start)
            week_limit_value = -(week_limit / 100) * balance
            if week_pnl <= week_limit_value:
                logger.error(
                    "Limite de perda semanal atingido: pnl=%.2f limite=%.2f (%.2f%%)",
                    week_pnl,
                    week_limit_value,
                    -week_limit,
                )
                await telegram_notifier.send_message_async(
                    f"⏸️ Bot pausado: perda semanal {week_pnl:.2f} <= limite {week_limit_value:.2f} ({week_limit:.1f}%)."
                )
                self.is_running = False
                self.last_error = "Limite de perda semanal atingido"
                self._drawdown_cache = {"result": False, "ts": now_ts, "ttl": 60.0}
                return False

        self._drawdown_cache = {"result": True, "ts": now_ts, "ttl": 60.0}
        return True

    async def initialize(self, config: BotConfig | None = None):
        """Initialize bot components"""
        try:
            config_obj = config or await load_bot_config(self.db)
            self._apply_config(config_obj)

            logger.info(
                "Loading config (source=%s, testnet=%s)",
                "provided" if config is not None else "db/env",
                self.config.binance_testnet,
            )

            # Determine API credentials based on selected exchange
            exchange_id = self.config.exchange
            if exchange_id == "kraken":
                api_key = self.config.kraken_api_key
                api_secret = self.config.kraken_api_secret
            else:
                api_key = self.config.binance_api_key
                api_secret = self.config.binance_api_secret

            success = binance_manager.initialize(
                exchange=exchange_id,
                api_key=api_key,
                api_secret=api_secret,
                testnet=self.config.binance_testnet,
                paper_trade=self.config.paper_trade,
            )
            logger.info("%s initialization: %s", exchange_id.upper(), "Success" if success else "Failed")

            telegram_notifier.initialize(
                bot_token=self.config.telegram_bot_token,
                chat_id=self.config.telegram_chat_id,
                verify_ssl=self.config.telegram_verify_ssl,
            )

            if binance_manager.client:
                self.strategy = TradingStrategy(
                    binance_manager,
                    min_signal_strength=self.config.strategy_min_signal_strength,
                    activation_threshold=self.config.strategy_activation_threshold,
                    timeframe=self.config.strategy_timeframe,
                    confirmation_timeframe=self.config.strategy_confirmation_timeframe,
                    limit=self.config.strategy_klines_limit,
                )
                self.selector = CryptoSelector(
                    binance_manager,
                    self.strategy,
                    base_symbols=self.config.selector_base_symbols,
                    trending_refresh_interval=self.config.selector_trending_refresh_interval,
                    min_change_percent=self.config.selector_min_change_percent,
                    trending_pool_size=self.config.selector_trending_pool_size,
                    min_quote_volume=self.config.selector_min_quote_volume,
                    max_spread_percent=self.config.selector_max_spread_percent,
                )

                # Inject strategy_engine into selector for multi-strategy candidate filtering
                if self.strategy_engine is not None:
                    self.selector.strategy_engine = self.strategy_engine

                # Inject client into strategy engine strategies
                if self.strategy_engine is not None:
                    for name in self.strategy_engine.strategy_names:
                        s = self.strategy_engine._strategies.get(name)
                        if s is not None and s.client is None:
                            s.client = binance_manager.client
                    logger.info("[StrategyEngine] Client injected into %d strategies",
                                len(self.strategy_engine.strategy_names))

            # Initialize Learning System
            await self.learning_system.initialize()
            self._sync_strategy_learning_params()

            # Verify LLM Analyzer availability (já foi instanciado no __init__)
            if self.llm_analyzer is not None:
                try:
                    if await self.llm_analyzer.is_available():
                        logger.info("[LLM] Ollama Analyzer disponível e pronto!")
                        logger.info(
                            "[LLM] Model: %s | Host: %s",
                            self.llm_analyzer.model_name,
                            self.llm_analyzer.ollama_host,
                        )
                    else:
                        logger.warning(
                            "[LLM] Ollama não está disponível - AI analysis desabilitada"
                        )
                        logger.warning("[LLM] Execute: ollama serve && ollama pull mistral")
                except Exception as e:
                    logger.warning("[LLM] Erro ao verificar Ollama: %s", e)
            elif LLM_ANALYZER_AVAILABLE:
                logger.warning("[LLM] Analyzer não foi instanciado corretamente")
            else:
                logger.info("[LLM] Módulo LLM Analyzer não disponível")

            # Load open positions from database
            await self._load_positions()

            logger.info("Trading bot initialized successfully")
            return True

        except Exception as e:
            logger.error("Error initializing bot: %s", e)
            return False

    async def start(self):
        """Start the trading bot"""
        try:
            if self.is_running:
                logger.warning("Bot is already running")
                self.last_error = "Bot is already running"
                return False

            if not binance_manager.client:
                logger.error(f"Exchange client ({self.config.exchange}) not initialized")
                self.last_error = f"Exchange client ({self.config.exchange}) not initialized"
                return False

            # VERIFICACAO E LIMPEZA INICIAL
            logger.info(f"Verificando posicoes existentes na {self.config.exchange.upper()} antes de iniciar...")
            await telegram_notifier.send_message_async("Verificando posicoes abertas na conta...")

            cleanup_result = await self._cleanup_existing_positions()
            if cleanup_result and cleanup_result.get("status") not in {"clean", "cleaned"}:
                self.last_error = (
                    cleanup_result.get("error")
                    or cleanup_result.get("status")
                    or "Falha na limpeza inicial"
                )
                logger.error("Erro na limpeza inicial antes do start: %s", self.last_error)
                return False

            self.is_running = True
            await telegram_notifier.notify_bot_started_async()
            watch_note = None
            if self.selector and getattr(self.selector, "symbols", None):
                preview = ", ".join(self.selector.symbols[:5])
                suffix = "..." if len(self.selector.symbols) > 5 else ""
                watch_note = f"Pares monitorados: {preview}{suffix}"
            self._last_observation_notice = 0.0
            await self._notify_observing(
                watch_note or "Monitorando pares com gerenciamento de risco ativo.", force=True
            )

            logger.info("Trading bot started")
            self.last_error = None

            # Start main loop
            self._loop_task = _ = asyncio.create_task(self._trading_loop(), name="trading_loop")

            return True

        except Exception as e:
            logger.error("Error starting bot: %s", e)
            self.is_running = False
            self.last_error = str(e)
            return False

    async def stop(self):
        """Stop the trading bot safely with retry queue for failed closes"""
        try:
            logger.info("Stopping bot - closing all positions safely...")
            await telegram_notifier.send_message_async(
                "Bot parando - Fechando posicoes abertas com seguranca..."
            )

            self.is_running = False
            await self._refresh_positions_cache()

            # Close all open positions before stopping with retry queue
            if self.positions:
                logger.info("Closing %d open positions...", len(self.positions))
                failed_positions = []
                max_retries = 3

                for position in self.positions[
                    :
                ]:  # Copy list to avoid modification during iteration
                    success = await self._try_close_position_with_retry(
                        position, "Bot stopped by user", max_attempts=1
                    )
                    if not success:
                        failed_positions.append(position)

                # Retry failed positions
                retry_count = 0
                while failed_positions and retry_count < max_retries:
                    retry_count += 1
                    logger.warning(
                        "Retentativa %d/%d para %d posicoes que falharam",
                        retry_count,
                        max_retries,
                        len(failed_positions),
                    )
                    await asyncio.sleep(2)  # Wait before retry

                    still_failed = []
                    for position in failed_positions:
                        success = await self._try_close_position_with_retry(
                            position, "Bot stopped by user (retry)", max_attempts=1
                        )
                        if not success:
                            still_failed.append(position)
                    failed_positions = still_failed

                if failed_positions:
                    symbols = [p.get("symbol", "UNKNOWN") for p in failed_positions]
                    logger.error(
                        "ATENCAO: %d posicoes NAO foram fechadas: %s",
                        len(failed_positions),
                        ", ".join(symbols),
                    )
                    await telegram_notifier.send_message_async(
                        f"⚠️ ATENÇÃO: {len(failed_positions)} posições não foram fechadas!\n"
                        f"Símbolos: {', '.join(symbols)}\n"
                        f"Verifique manualmente na {self.config.exchange.upper()}."
                    )
                else:
                    logger.info("All positions closed safely")
                    await telegram_notifier.send_message_async(
                        "Todas as posicoes fechadas com seguranca. Bot parado."
                    )
            else:
                logger.info("No open positions to close")
                await telegram_notifier.send_message_async("Bot parado (sem posicoes abertas)")

            await self._refresh_positions_cache()
            await telegram_notifier.notify_bot_stopped_async()
            await telegram_notifier.close()
            if self._loop_task:
                await self._loop_task
                self._loop_task = None
            logger.info("Trading bot stopped safely")
            return True
        except Exception as e:
            logger.error("Error stopping bot: %s", e)
            return False

    async def set_paper_mode(self, enabled: bool) -> bool:
        """Toggle paper trading mode on/off at runtime.
        
        PAPER MODE (enabled=True):  Simulated orders, real market data.
        REAL MODE  (enabled=False): Real orders on Binance mainnet.
        
        Safety: only switches the internal flag. The binance_client
        checks this flag before every order — no restart required.
        """
        import os

        from bot.binance_client import binance_manager

        try:
            mode_name = "Paper Trading" if enabled else "REAL TRADING"
            if not enabled:
                # Switching to real money — safety checks
                balance = await self._get_account_balance()
                logger.warning(
                    "⚠️ SWITCHING TO REAL TRADING MODE — orders will execute on Binance Mainnet!"
                )
                logger.warning(
                    "Account balance: %.2f USDT — ensure this is intentional", balance
                )

            binance_manager._paper_trade = enabled
            self.config.paper_trade = enabled

            # Update env var so it survives restart
            os.environ["PAPER_TRADE"] = str(enabled).lower()

            logger.info("Trading mode changed: %s (paper_trade=%s)", mode_name, enabled)

            if not enabled:
                await telegram_notifier.send_message_async(
                    f"⚠️ <b>REAL TRADING MODE ACTIVATED</b>\n\n"
                    f"Orders will execute on <b>Binance Mainnet</b> with real funds.\n"
                    f"Account: {balance:.2f} USDT\n"
                    f"Risk per trade: {self.config.risk_percentage}%"
                )
            else:
                await telegram_notifier.send_message_async(
                    "📝 <b>Paper Trading Mode</b>\n\n"
                    "Orders are SIMULATED. Real market data, zero financial risk."
                )

            return True
        except Exception as e:
            logger.error("Error setting paper mode: %s", e)
            return False

    async def _trading_loop(self):
        """Main trading loop"""
        while self.is_running:
            loop_start = time.perf_counter()
            try:
                # Circuit breaker: verificar se deve pausar
                if self._is_circuit_open():
                    remaining = self._circuit_open_until - asyncio.get_running_loop().time()
                    logger.warning(
                        "Circuit breaker ABERTO - pausando operacoes por %.0f segundos",
                        max(0, remaining),
                    )
                    await asyncio.sleep(min(self.check_interval, remaining))
                    continue

                # Check existing positions (cache é populado uma única vez por ciclo)
                await self._refresh_positions_cache()
                await self._check_positions()

                # Look for new opportunities if not at max positions
                async with self._positions_lock:
                    current_count = len(self.positions)
                if current_count < self.risk_manager.max_positions:
                    await self._find_and_open_position()

                # Descontar tempo já gasto no ciclo para manter intervalos precisos
                self.metrics["last_loop_ms"] = (time.perf_counter() - loop_start) * 1000
                elapsed = time.perf_counter() - loop_start
                await asyncio.sleep(max(0.0, self.check_interval - elapsed))

            except Exception as e:
                logger.error("Error in trading loop: %s", e)
                self._record_failure()
                elapsed = time.perf_counter() - loop_start
                await asyncio.sleep(max(0.0, self.check_interval - elapsed))

    def _is_near_candle_close(self, timeframe: str = "15m", threshold_seconds: int = 45) -> bool:
        """
        Verifica se estamos próximos do fechamento da vela.
        Retorna True se faltam menos de threshold_seconds para fechar.
        Isso evita entrar em sinais que podem mudar antes da vela fechar.
        """
        now = datetime.now(UTC)

        # Mapear timeframe para minutos
        tf_minutes = {"1m": 1, "3m": 3, "5m": 5, "15m": 15, "30m": 30, "1h": 60, "4h": 240}
        candle_minutes = tf_minutes.get(timeframe, 15)
        candle_seconds = candle_minutes * 60

        # Segundos decorridos desde início do período
        if candle_minutes >= 60:
            # Para timeframes de hora ou mais
            total_minutes = now.hour * 60 + now.minute
            elapsed = (total_minutes % candle_minutes) * 60 + now.second
        else:
            elapsed = (now.minute % candle_minutes) * 60 + now.second

        remaining = candle_seconds - elapsed
        return remaining <= threshold_seconds

    def _get_progressive_trail_factor(self, profit_pct: float) -> float:
        """
        Retorna o fator multiplicador do trail baseado no lucro acumulado.
        Quanto maior o lucro, mais apertado o trailing (protege ganhos).

        Lógica:
        - Lucro < 0.5%: fator 1.0 (trail normal)
        - Lucro 0.5-1%: fator 0.9 (trail 10% mais apertado)
        - Lucro 1-2%: fator 0.7 (trail 30% mais apertado)
        - Lucro 2-3%: fator 0.5 (trail 50% mais apertado)
        - Lucro > 3%: fator 0.3 (trail 70% mais apertado - lock máximo)

        Args:
            profit_pct: Lucro percentual atual da posição

        Returns:
            Fator multiplicador (0.3 a 1.0)
        """
        if profit_pct < 0.5:
            return 1.0  # Trail normal
        elif profit_pct < 1.0:
            return 0.9  # 10% mais apertado
        elif profit_pct < 2.0:
            return 0.7  # 30% mais apertado
        elif profit_pct < 3.0:
            return 0.5  # 50% mais apertado
        else:
            return 0.3  # Máximo lock - 70% mais apertado

    async def _check_btc_health(self) -> bool:
        """
        Verifica se BTC está em condição favorável para longs.
        Retorna False se BTC está em queda (evita entradas em BTC e alts).
        MELHORIA: Verifica queda recente de preço (>2% em 15min) e bloqueia TUDO.
        """
        try:
            if not self.strategy:
                return True

            # Buscar preço atual e preço de 15 minutos atrás
            btc_ticker = await self._run_blocking(
                self.strategy.get_historical_data, "BTCUSDT", timeframe="1m", limit=20
            )
            
            if btc_ticker is not None and len(btc_ticker) >= 15:
                current_price = float(btc_ticker.iloc[-1]["close"])
                price_15min_ago = float(btc_ticker.iloc[-15]["close"])
                btc_change_pct = ((current_price - price_15min_ago) / price_15min_ago) * 100
                
                if btc_change_pct < -2.0:
                    logger.warning(
                        "⛔ BTC caiu %.1f%% nos últimos 15min (%.2f → %.2f) — BLOQUEANDO TODAS AS ENTRADAS",
                        btc_change_pct, price_15min_ago, current_price,
                    )
                    return False
                elif btc_change_pct < -1.0:
                    logger.warning(
                        "⚠️ BTC em queda de %.1f%% — cautela, mas permitindo trades",
                        btc_change_pct,
                    )
            else:
                current_price = None
                price_15min_ago = None

            btc_analysis = await self._run_blocking(self.strategy.analyze_symbol, "BTCUSDT")

            if not btc_analysis:
                logger.debug("Não foi possível analisar BTC - continuando")
                return True

            btc_trend = btc_analysis.get("trend", "neutral")
            btc_rsi = btc_analysis.get("rsi", 50)
            btc_trend_bias = btc_analysis.get("trend_bias", "neutral")

            # BTC em queda forte = não entrar em NADA (nem BTC, nem alts)
            if btc_trend == "bearish" and btc_rsi < 35:
                logger.warning(
                    "⛔ BTC em queda forte (trend=%s, RSI=%.1f) - bloqueando BTC e alts",
                    btc_trend, btc_rsi,
                )
                return False

            # BTC em tendência de baixa = não entrar em NADA
            if btc_trend_bias == "bearish" and btc_rsi < 40:
                logger.warning(
                    "⛔ BTC com viés bearish (bias=%s, RSI=%.1f) - bloqueando BTC e alts",
                    btc_trend_bias, btc_rsi,
                )
                return False

            logger.debug("BTC saudável (trend=%s, RSI=%.1f) - OK para trades", btc_trend, btc_rsi)
            return True

        except Exception as e:
            logger.warning("Erro ao verificar saúde do BTC: %s - continuando", e)
            return True

    def _is_optimal_trading_time(self) -> tuple:
        """
        Verifica se estamos em horário de boa liquidez para trading.

        Sessões de mercado (UTC):
        - Ásia: 00:00 - 08:00 UTC (Tokyo, Singapore, Hong Kong)
        - Europa: 07:00 - 16:00 UTC (London, Frankfurt)
        - América: 13:00 - 22:00 UTC (New York, Chicago)

        Melhores horários (overlap):
        - 07:00-08:00 UTC: Ásia + Europa
        - 13:00-16:00 UTC: Europa + América (MELHOR!)

        Piores horários:
        - 22:00-00:00 UTC: Gap entre sessões (baixa liquidez)
        - 04:00-07:00 UTC: Apenas sessão asiática tardia

        Returns:
            tuple: (is_optimal: bool, session_info: str)
        """
        import os

        # Verificar se o filtro está habilitado (default: True)
        filter_enabled = os.getenv("TRADING_TIME_FILTER", "true").lower() == "true"
        if not filter_enabled:
            return True, "Filtro de horário desabilitado"

        now = datetime.now(UTC)
        hour = now.hour

        # Definir qualidade dos horários
        if 13 <= hour < 16:
            # Overlap Europa + América - MELHOR horário
            return True, "Sessão Europa+América (optimal)"

        elif 7 <= hour < 13:
            # Sessão Europa ativa
            return True, "Sessão Europa"

        elif 16 <= hour < 22:
            # Sessão América
            return True, "Sessão América"

        elif 0 <= hour < 4:
            # Sessão Ásia ativa
            return True, "Sessão Ásia"

        elif 4 <= hour < 7:
            # Final da sessão Ásia - liquidez reduzida
            return False, "Fim sessão Ásia (liquidez reduzida)"

        else:  # 22:00-00:00
            # Gap entre sessões - baixa liquidez
            return False, "Gap entre sessões (baixa liquidez)"

    async def _find_and_open_position(self):
        """Find and open a new trading position using strategy"""
        try:
            self._sync_strategy_learning_params()
            logger.info("Scanning market for opportunities...")

            if not self.selector or not self.strategy:
                logger.error("Selector or strategy not initialized")
                return

            # MELHORIA 1: Verificar se BTC está saudável antes de qualquer entrada
            if not await self._check_btc_health():
                await self._notify_observing(
                    "BTC em queda - aguardando estabilização para entrar em alts."
                )
                return

            # MELHORIA 2: Bloquear entrada nos últimos 60s antes do fechamento da vela
            # Nesse período o sinal ainda pode mudar antes da confirmação da vela
            timeframe = getattr(self.strategy, "timeframe", "15m")
            if self._is_near_candle_close(timeframe, threshold_seconds=60):
                logger.debug(
                    "[Candle Close] Faltam <60s para fechar a vela %s — aguardando confirmação.",
                    timeframe,
                )
                return

            # MELHORIA 3: Verificar se estamos em horário de boa liquidez
            is_optimal_time, session_info = self._is_optimal_trading_time()
            if not is_optimal_time:
                logger.info("Horário não ideal para trading: %s", session_info)
                await self._notify_observing(f"Aguardando horário melhor: {session_info}")
                return
            else:
                logger.debug("Sessão de trading: %s", session_info)

            # Refresh positions from DB to avoid race conditions
            await self._refresh_positions_cache()

            # Get list of symbols already in positions (from fresh cache)
            async with self._positions_lock:
                excluded_symbols = [pos["symbol"] for pos in self.positions]

            #  Use CryptoSelector to find best opportunity
            opportunity = await self._run_blocking(
                self.selector.select_best_crypto, excluded_symbols
            )

            if not opportunity:
                logger.info("No trading opportunities found")
                await self._notify_observing("Sem sinais convincentes no momento.")
                return

            logger.info(
                "Opportunity found: %s | Signal: %s | Score: %.2f | Unified: %d",
                opportunity["symbol"],
                opportunity["signal"],
                opportunity.get("score", 0),
                opportunity.get("unified_score", 0),
            )

            # MELHORIA: Cooldown pós stop-loss — não recomprar símbolo que acabou de cair
            if self._sl_cooldown_minutes > 0 and opportunity["symbol"] in self._sl_cooldown:
                elapsed = time.time() - self._sl_cooldown[opportunity["symbol"]]
                if elapsed < self._sl_cooldown_minutes * 60:
                    remaining = int(self._sl_cooldown_minutes * 60 - elapsed)
                    logger.info(
                        "⏳ %s em cooldown pós-STOP_LOSS — faltam %ds",
                        opportunity["symbol"], remaining,
                    )
                    return
                else:
                    del self._sl_cooldown[opportunity["symbol"]]

            # ── Multi-Strategy Engine (new path) ──
            if self.strategy_engine is not None:
                symbol = opportunity["symbol"]
                df = self.strategy.get_historical_data(symbol)
                if df is not None and len(df) >= 50:
                    df = self.strategy.calculate_indicators(df)
                    signals = self.strategy_engine.analyze_symbol(symbol, df)

                    if signals:
                        best = signals[0]
                        logger.info(
                            "[StrategyEngine] %s: %s/%s score=%d conf=%.2f (regime=%s)",
                            symbol, best.signal, best.strategy_name,
                            best.score, best.confidence,
                            best.regime.regime if best.regime else "?",
                        )

                        # Merge strategy signal into opportunity
                        opportunity["signal"] = best.signal
                        opportunity["unified_score"] = best.score
                        opportunity["signal_quality"] = "excellent" if best.score >= 70 else (
                            "good" if best.score >= 55 else "fair"
                        )
                        opportunity["strategy_name"] = best.strategy_name
                        opportunity["entry_price"] = best.entry_price

                        # Override SL/TP with strategy-specific levels
                        if best.stop_loss:
                            opportunity["stop_loss"] = best.stop_loss
                        if best.take_profit:
                            opportunity["take_profit"] = best.take_profit
                    else:
                        logger.info("[StrategyEngine] No signals from any strategy for %s", symbol)
                        return
                else:
                    logger.debug("[StrategyEngine] Insufficient data for %s, using legacy scoring", symbol)

            # ═══════════════════════════════════════════════════════════════
            # MELHORIA: Unified score as primary gate — must meet min_signal_strength
            unified_score = opportunity.get("unified_score", 0)
            min_required = self.strategy.min_signal_strength
            if unified_score < min_required:
                logger.info(
                    "Unified score %d < minimum %d — skipping %s (quality: %s)",
                    unified_score,
                    min_required,
                    opportunity["symbol"],
                    opportunity.get("signal_quality", "unknown"),
                )
                await self._notify_observing(
                    f"Sinal fraco para {opportunity['symbol']} "
                    f"(score {unified_score} < {min_required})"
                )
                return

            # 🧠 FUNCIONALIDADE #5: REGIME ADAPTATIVO COM FEEDBACK
            if self.risk_advisor:
                try:
                    # Rastrear sinal atual e limpar entradas com mais de 1 hora
                    import time as _time_signals

                    _now_signals = _time_signals.monotonic()
                    self._signals_last_hour.append(_now_signals)
                    # Remover pela esquerda (mais antigo) até estar dentro da janela de 1h
                    while (
                        self._signals_last_hour and _now_signals - self._signals_last_hour[0] > 3600
                    ):
                        self._signals_last_hour.popleft()
                    recent_signals_count = len(self._signals_last_hour)

                    # 🧠 Detectar regime de mercado se não definido na opportunity
                    current_regime = opportunity.get("market_regime")
                    if not current_regime or current_regime == "unknown":
                        try:
                            if self.strategy and hasattr(self.strategy, 'detect_market_regime'):
                                regime_data = self.strategy.detect_market_regime(symbol="BTCUSDT")
                                current_regime = regime_data.get("regime", "unknown") if isinstance(regime_data, dict) else "unknown"
                            else:
                                current_regime = "unknown"
                        except Exception:
                            current_regime = "unknown"

                    regime_adaptation = await self.risk_advisor.get_regime_adaptation(
                        current_regime=current_regime,
                        recent_signals_count=recent_signals_count,
                    )

                    if not regime_adaptation.should_trade:
                        logger.warning(
                            f"[AI Regime] ⚠️ TRADING PAUSADO neste regime: {regime_adaptation.reasoning}"
                        )
                        await self._notify_observing(
                            f"Regime {regime_adaptation.current_regime} com performance ruim - aguardando"
                        )
                        return

                    # Aplicar ajustes adaptativos
                    if regime_adaptation.score_threshold_adjustment != 0:
                        min_score = opportunity.get("score", 0)
                        adjusted_min = 75 + regime_adaptation.score_threshold_adjustment

                        if min_score < adjusted_min:
                            logger.info(
                                f"[AI Regime] Score {min_score} abaixo do threshold adaptado {adjusted_min}. "
                                f"Pulando. Motivo: {regime_adaptation.reasoning}"
                            )
                            await self._notify_observing(
                                f"Score insuficiente após ajuste adaptativo ({adjusted_min} requerido)"
                            )
                            return

                    # Salvar ajustes para aplicar posteriormente
                    opportunity["ai_stop_multiplier_adj"] = (
                        regime_adaptation.stop_multiplier_adjustment
                    )
                    opportunity["ai_size_adjustment"] = regime_adaptation.size_adjustment

                    logger.info(
                        f"[AI Regime] Win Rate: {regime_adaptation.win_rate_last_10:.0f}% | "
                        f"Ajustes: Stop {regime_adaptation.stop_multiplier_adjustment:.1f}x, "
                        f"Size {regime_adaptation.size_adjustment:.0%}"
                    )

                except Exception as e:
                    logger.warning(f"[AI Regime] Erro: {e} - continuando sem adaptação")

            if opportunity.get("signal") != "BUY":
                logger.info(
                    "Sinal %s ignorado para operacao Spot: %s",
                    opportunity.get("signal"),
                    opportunity["symbol"],
                )
                await self._notify_observing(
                    "Sinal de venda ignorado - aguardando setup de compra."
                )
                return

            #  Get additional market data for ML analysis
            opportunity["volume"] = (
                opportunity.get("volume_ratio", 1.0) * 1000000
            )  # Estimate volume
            opportunity["avg_volume"] = 1000000

            # Open position with ML filtering
            await self._open_position(opportunity)

        except Exception as e:
            logger.error("Error finding and opening position: %s", e)

    async def _open_position(self, opportunity: dict):
        """Open a trading position with ML-based filtering"""
        try:
            # 📰 FUNCIONALIDADE #3: ANÁLISE DE SENTIMENTO PRÉ-TRADE
            if self.risk_advisor:
                try:
                    from datetime import datetime

                    pre_trade_analysis = await self.risk_advisor.pre_trade_sentiment_analysis(
                        symbol=opportunity["symbol"],
                        current_time=datetime.utcnow(),
                    )

                    if not pre_trade_analysis.should_enter:
                        logger.warning(
                            f"[AI Pre-Trade] ❌ NÃO ENTRAR: {pre_trade_analysis.reasoning}"
                        )
                        if pre_trade_analysis.risk_events:
                            for event in pre_trade_analysis.risk_events:
                                logger.warning(f"[AI Risk Event] {event}")

                        await self._notify_observing(
                            f"IA detectou risco: {pre_trade_analysis.urgency} - {pre_trade_analysis.sentiment}"
                        )
                        return
                    else:
                        logger.info(f"[AI Pre-Trade] ✅ Via livre: {pre_trade_analysis.reasoning}")
                except Exception as e:
                    logger.warning(f"[AI Pre-Trade] Erro: {e} - continuando sem análise")

            #  MACHINE LEARNING: Calcular score de confianca
            market_conditions = {
                "volume": opportunity.get("volume", 0),
                "avg_volume": opportunity.get("avg_volume", 1),
                "trend": opportunity.get("trend", "neutral"),
                "rsi": opportunity.get("rsi", 50),
            }

            opportunity_score = self.learning_system.calculate_opportunity_score(
                opportunity, market_conditions
            )

            #  MACHINE LEARNING: Decidir se deve entrar no trade
            should_trade_result = self.learning_system.should_take_trade(opportunity_score)
            # Compatibilidade: pode retornar bool ou tupla (bool, str)
            if isinstance(should_trade_result, tuple):
                should_trade, reason = should_trade_result
            else:
                should_trade = should_trade_result
                reason = f"Score: {opportunity_score:.2f}"

            if not should_trade:
                # 🔍 FUNCIONALIDADE #4: FALLBACK REASONING - POR QUE NÃO ENTROU?
                if self.risk_advisor:
                    try:
                        skip_reasoning = await self.risk_advisor.generate_skip_reasoning(
                            symbol=opportunity["symbol"],
                            technical_score=opportunity.get("score", 0),
                            filters_failed=["ML_CONFIDENCE_LOW"],
                            market_regime=opportunity.get("market_regime", "unknown"),
                            current_drawdown=self._current_drawdown_pct,
                        )

                        logger.info(
                            f"[AI Skip Reasoning] {opportunity['symbol']}: {skip_reasoning.primary_reason}"
                        )
                        logger.info(f"[AI Suggestion] {skip_reasoning.suggestion}")

                        await self._notify_observing(
                            f"❌ Pulado: {skip_reasoning.primary_reason[:100]}..."
                        )
                    except Exception as e:
                        logger.warning(f"[AI Skip Reasoning] Erro: {e}")
                        await self._notify_observing("Filtro de confianca descartou o sinal.")
                else:
                    logger.info(f"Trade rejeitado por ML antigo - {reason}")
                    await self._notify_observing("Filtro de confianca descartou o sinal.")
                return

            # NOVO: Filtro ML treinado com dados historicos
            if self.ml_filter and self.ml_filter.loaded:
                # Preparar indicadores para o filtro ML
                ml_indicators = {
                    "rsi": opportunity.get("rsi", 50),
                    "macd": opportunity.get("macd", 0),
                    "macd_signal": opportunity.get("macd_signal", 0),
                    "macd_hist": opportunity.get("macd_hist", 0),
                    "close": opportunity.get("price", opportunity.get("close", 0)),
                    "ema_fast": opportunity.get("ema_fast", 0),
                    "ema_slow": opportunity.get("ema_slow", 0),
                    "ema_50": opportunity.get("ema_50", 0),
                    "ema_200": opportunity.get("ema_200", 0),
                    "bb_upper": opportunity.get("bb_upper", 0),
                    "bb_lower": opportunity.get("bb_lower", 0),
                    "atr": opportunity.get("atr", 0),
                    "vwap": opportunity.get("vwap", 0),
                    "volume_ratio": opportunity.get("volume_ratio", 1),
                }

                ml_should_trade, ml_confidence, ml_reason = self.ml_filter.should_take_trade(
                    opportunity, ml_indicators
                )

                logger.info(f"[ML Filter] {opportunity['symbol']}: {ml_reason}")

                if not ml_should_trade:
                    # 🔍 FUNCIONALIDADE #4: Explicação quando ML Filter rejeita
                    if self.risk_advisor:
                        try:
                            skip_reasoning = await self.risk_advisor.generate_skip_reasoning(
                                symbol=opportunity["symbol"],
                                technical_score=opportunity.get("score", 0),
                                filters_failed=["ML_FILTER"],
                                market_regime=opportunity.get("market_regime", "unknown"),
                                current_drawdown=self._current_drawdown_pct,
                            )
                            logger.info(f"[AI Skip] {skip_reasoning.primary_reason}")
                            await self._notify_observing(f"❌ {skip_reasoning.primary_reason[:80]}")
                        except Exception:
                            logger.info(f"Trade rejeitado por ML Filter - {ml_reason}")
                            await self._notify_observing(f"Filtro ML rejeitou: {ml_reason}")
                    else:
                        logger.info(f"Trade rejeitado por ML Filter - {ml_reason}")
                        await self._notify_observing(f"Filtro ML rejeitou: {ml_reason}")
                    return

                # Adicionar confianca ML ao opportunity para logging
                opportunity["ml_confidence"] = ml_confidence
                logger.info(f"[ML Filter] Trade aprovado com confianca {ml_confidence:.2%}")

            # NOVO: LLM Market Analyzer - Análise avançada de regime e adaptação
            if self.market_analyzer and await self.market_analyzer.is_available():
                try:
                    logger.info("[LLM Market] Analisando regime de mercado...")

                    # Buscar dados BTC e altcoin em paralelo
                    btc_data, alt_data = await asyncio.gather(
                        self._run_blocking(
                            self.strategy.get_historical_data,
                            "BTCUSDT",
                            timeframe=self.strategy.timeframe,
                            limit=20,
                        ),
                        self._run_blocking(
                            self.strategy.get_historical_data,
                            opportunity["symbol"],
                            timeframe=self.strategy.timeframe,
                            limit=20,
                        ),
                    )

                    # Calcular volatilidade recente
                    recent_volatility = opportunity.get("atr", 0)

                    # Buscar trades recentes para aprendizado
                    recent_trades = []
                    if hasattr(self, "positions") and self.positions:
                        recent_trades = [
                            {
                                "symbol": p.get("symbol"),
                                "pnl_pct": p.get("pnl_pct", 0),
                                "duration_minutes": p.get("duration_minutes", 0),
                                "regime": p.get("market_regime", "unknown"),
                            }
                            for p in self.positions[-50:]
                            if p.get("status") == "closed"
                        ]

                    # Analisar regime de mercado
                    market_context = await self.market_analyzer.analyze_market_regime(
                        btc_data=btc_data,
                        alt_data=alt_data,
                        recent_volatility=recent_volatility,
                        recent_trades=recent_trades,
                    )

                    logger.info(
                        f"[LLM Market] Regime: {market_context.regime.value}, "
                        f"Vol: {market_context.volatility_percentile}º, "
                        f"Trend: {market_context.trend_strength}/100"
                    )

                    # Obter recomendação adaptativa
                    recommendation = await self.market_analyzer.recommend_trade(
                        symbol=opportunity["symbol"],
                        technical_score=opportunity.get("score", 0),
                        indicators=ml_indicators if "ml_indicators" in locals() else {},
                        market_context=market_context,
                    )

                    # Verificar se deve pular o trade
                    if recommendation.action == "SKIP":
                        logger.info(f"[LLM Market] Trade rejeitado: {recommendation.reasoning}")
                        await self._notify_observing(
                            f"IA recomenda aguardar: {recommendation.reasoning}"
                        )
                        return

                    # Armazenar ajustes para aplicar posteriormente
                    opportunity["llm_stop_multiplier"] = recommendation.suggested_stop_multiplier
                    opportunity["llm_target_multiplier"] = (
                        recommendation.suggested_target_multiplier
                    )
                    opportunity["llm_size_adjustment"] = recommendation.position_size_adjustment
                    opportunity["llm_confidence"] = recommendation.confidence
                    opportunity["llm_reasoning"] = recommendation.reasoning
                    opportunity["market_regime"] = market_context.regime.value

                    logger.info(
                        f"[LLM Market] {recommendation.action} com {recommendation.confidence:.0%} confiança - "
                        f"Stop: {recommendation.suggested_stop_multiplier:.2f}x, "
                        f"Target: {recommendation.suggested_target_multiplier:.2f}x, "
                        f"Size: {recommendation.position_size_adjustment:.0%}"
                    )

                except Exception as e:
                    logger.error(f"[LLM Market] Erro na análise: {e}")
                    # Continua sem a análise LLM em caso de erro

            # Get account balance
            balance = await self._get_account_balance()
            if balance is None or balance <= 0:
                logger.error("Failed to get account balance")
                await telegram_notifier.send_message_async(
                    "Falha ao consultar saldo da conta. Verifique credenciais ou limite de API."
                )
                await self._notify_observing("Aguardando atualizacao de saldo para operar.")
                return

            # Checar limites de perda antes de abrir nova posicao
            if not await self._check_drawdown_limits(balance):
                return

            # FASE 6: Calcular ATR e regime de volatilidade para stops dinâmicos
            atr = None
            volatility_regime = "normal"
            try:
                # Buscar dados históricos para calcular ATR
                df = await self._run_blocking(
                    self.strategy.get_historical_data,
                    opportunity["symbol"],
                    timeframe=self.strategy.timeframe,
                    limit=30,
                )

                if df is not None and not df.empty and "atr" in df.columns:
                    atr = df["atr"].iloc[-1]
                    if not pd.isna(atr):
                        # Determinar regime de volatilidade
                        volatility_regime = await self._run_blocking(
                            self.strategy.get_market_volatility_regime, df
                        )
                        logger.info(
                            "[ATR] %s - ATR: %.4f, Regime: %s",
                            opportunity["symbol"],
                            atr,
                            volatility_regime,
                        )
                    else:
                        logger.warning(
                            "[ATR] ATR is NaN for %s - using percentage stops",
                            opportunity["symbol"],
                        )
                        atr = None
                else:
                    logger.warning(
                        "[ATR] No ATR data available for %s - using percentage stops",
                        opportunity["symbol"],
                    )
            except Exception as e:
                logger.warning(
                    "[ATR] Error calculating ATR for %s: %s - using percentage stops",
                    opportunity["symbol"],
                    e,
                )
                atr = None

            # Calculate position size (com ATR se disponível)
            position_params = self.risk_manager.calculate_position_size(
                balance, opportunity["price"], atr=atr, volatility_regime=volatility_regime
            )

            if not position_params:
                logger.error("Failed to calculate position size")
                await telegram_notifier.send_message_async(
                    "Nao foi possivel calcular o tamanho da posicao. Revise parametros de risco."
                )
                await self._notify_observing(
                    "Aguardando ajustes de risco para proxima oportunidade."
                )
                return

            # 🎯 FUNCIONALIDADE #1: ADAPTIVE STOP-LOSS AJUSTADO POR IA
            if self.risk_advisor and atr:
                try:
                    # Calcula volatilidade percentile (simplificado)
                    volatility_percentile = 50.0  # TODO: Calcular baseado em histórico
                    if volatility_regime == "high":
                        volatility_percentile = 75.0
                    elif volatility_regime == "low":
                        volatility_percentile = 25.0

                    # Calcular trend de volatilidade: ATR atual vs média dos últimos 20 candles
                    recent_volatility_trend = "stable"
                    if df is not None and "atr" in df.columns and len(df) >= 5:
                        atr_series = df["atr"].dropna()
                        if len(atr_series) >= 5:
                            atr_mean = atr_series.tail(20).mean()
                            atr_current = atr_series.iloc[-1]
                            if atr_mean > 0:
                                atr_change_pct = (atr_current - atr_mean) / atr_mean * 100
                                if atr_change_pct > 20:
                                    recent_volatility_trend = "increasing"
                                elif atr_change_pct < -20:
                                    recent_volatility_trend = "decreasing"

                    adaptive_sl = await self.risk_advisor.calculate_adaptive_stop_loss(
                        symbol=opportunity["symbol"],
                        entry_price=opportunity["price"],
                        atr=atr,
                        base_sl_multiplier=2.0,  # Multiplier base do risk_manager
                        volatility_percentile=volatility_percentile,
                        recent_volatility_trend=recent_volatility_trend,
                    )

                    if adaptive_sl.confidence > 0.7:  # Alta confiança na recomendação IA
                        position_params["stop_loss"] = adaptive_sl.stop_loss_price
                        logger.info(
                            f"[AI Stop-Loss] {opportunity['symbol']}: {adaptive_sl.reasoning} "
                            f"(${adaptive_sl.stop_loss_price:.4f}, {adaptive_sl.stop_multiplier:.1f}x ATR)"
                        )
                except Exception as e:
                    logger.warning(f"[AI Stop-Loss] Erro: {e} - usando stop base")

            #  MACHINE LEARNING: Ajustar Stop Loss (passa entry_price para cálculo correto)
            position_params["stop_loss"] = self.learning_system.adjust_stop_loss(
                position_params["stop_loss"], entry_price=opportunity["price"]
            )

            # Salvaguarda: garantir SL do lado correto para BUY (spot)
            if position_params["stop_loss"] >= opportunity["price"]:
                logger.warning(
                    "Stop loss ajustado ficou acima do entry (BUY). Revertendo para base calculada."
                )
                stop_loss_pct_decimal = self.risk_manager.stop_loss_percentage / 100
                position_params["stop_loss"] = round(
                    opportunity["price"] * (1 - stop_loss_pct_decimal), 4
                )

            #  MACHINE LEARNING: Ajustar Take Profit (passa entry_price para cálculo correto)
            position_params["take_profit"] = self.learning_system.adjust_take_profit(
                position_params["take_profit"], entry_price=opportunity["price"]
            )

            # Salvaguarda TP: para BUY TP deve ficar acima do entry; para SELL, abaixo
            if position_params["take_profit"] <= opportunity["price"]:
                logger.warning("Take profit ajustado ficou no lado errado. Reancorando para BUY.")
                tp_pct_decimal = self.risk_manager.take_profit_percentage / 100
                position_params["take_profit"] = round(
                    opportunity["price"] * (1 + tp_pct_decimal), 4
                )

            #  MACHINE LEARNING: Ajustar tamanho da posicao
            position_params["position_size_usdt"] = self.learning_system.adjust_position_size(
                position_params["position_size_usdt"]
            )

            # 📊 FUNCIONALIDADE #2: POSITION SIZING INTELIGENTE
            if self.risk_advisor:
                try:
                    intelligent_size = await self.risk_advisor.calculate_intelligent_position_size(
                        symbol=opportunity["symbol"],
                        technical_score=opportunity.get("score", 0),
                        has_divergence=opportunity.get("has_divergence", False),
                        volume_confirmed=opportunity.get("volume_confirmed", True),
                        trend_strength=opportunity.get("trend_strength", 50),
                        btc_correlation=self.strategy.calculate_btc_correlation(
                            opportunity["symbol"]
                        ),
                    )

                    if intelligent_size.confidence_score >= 6:  # Confiança razoável
                        original_size = position_params["position_size_usdt"]
                        position_params["position_size_usdt"] = round(
                            original_size * intelligent_size.size_multiplier, 2
                        )
                        logger.info(
                            f"[AI Position Size] {opportunity['symbol']}: Confidence {intelligent_size.confidence_score}/10 "
                            f"→ Size ${original_size} → ${position_params['position_size_usdt']} "
                            f"({intelligent_size.size_multiplier:.1f}x) | {intelligent_size.reasoning}"
                        )

                        if intelligent_size.risk_flags:
                            logger.warning(
                                f"[AI Risk Flags] {', '.join(intelligent_size.risk_flags)}"
                            )
                except Exception as e:
                    logger.warning(f"[AI Position Size] Erro: {e} - usando size base")

            # 🧠 FUNCIONALIDADE #5: APLICAR AJUSTES ADAPTATIVOS DO REGIME
            if "ai_stop_multiplier_adj" in opportunity:
                original_stop = position_params["stop_loss"]
                stop_distance = abs(opportunity["price"] - original_stop)
                adjusted_stop_distance = stop_distance * opportunity["ai_stop_multiplier_adj"]
                position_params["stop_loss"] = round(
                    opportunity["price"] - adjusted_stop_distance, 4
                )
                logger.info(
                    f"[AI Regime Adjust] Stop: ${original_stop:.4f} → ${position_params['stop_loss']:.4f} "
                    f"({opportunity['ai_stop_multiplier_adj']:.1f}x)"
                )

            if "ai_size_adjustment" in opportunity:
                original_size = position_params["position_size_usdt"]
                position_params["position_size_usdt"] = round(
                    original_size * opportunity["ai_size_adjustment"], 2
                )
                logger.info(
                    f"[AI Regime Adjust] Size: ${original_size:.2f} → ${position_params['position_size_usdt']:.2f} "
                    f"({opportunity['ai_size_adjustment']:.0%})"
                )

            # NOVO: Aplicar ajustes adaptativos do LLM Market Analyzer
            if "llm_stop_multiplier" in opportunity:
                original_stop = position_params["stop_loss"]
                stop_distance = abs(opportunity["price"] - original_stop)
                adjusted_stop_distance = stop_distance * opportunity["llm_stop_multiplier"]
                position_params["stop_loss"] = round(
                    opportunity["price"] - adjusted_stop_distance, 4
                )
                logger.info(
                    f"[LLM Adjust] Stop Loss: {original_stop} → {position_params['stop_loss']} "
                    f"(multiplier: {opportunity['llm_stop_multiplier']:.2f}x)"
                )

            if "llm_target_multiplier" in opportunity:
                original_target = position_params["take_profit"]
                target_distance = abs(original_target - opportunity["price"])
                adjusted_target_distance = target_distance * opportunity["llm_target_multiplier"]
                position_params["take_profit"] = round(
                    opportunity["price"] + adjusted_target_distance, 4
                )
                logger.info(
                    f"[LLM Adjust] Take Profit: {original_target} → {position_params['take_profit']} "
                    f"(multiplier: {opportunity['llm_target_multiplier']:.2f}x)"
                )

            if "llm_size_adjustment" in opportunity:
                original_size = position_params["position_size_usdt"]
                position_params["position_size_usdt"] = round(
                    original_size * opportunity["llm_size_adjustment"], 2
                )
                logger.info(
                    f"[LLM Adjust] Position Size: ${original_size} → ${position_params['position_size_usdt']} "
                    f"(adjustment: {opportunity['llm_size_adjustment']:.0%})"
                )

            # Recalcular quantity com novo position size
            position_params["quantity"] = (
                position_params["position_size_usdt"] / opportunity["price"]
            )

            # Logar risco efetivo vs alvo para auditoria
            try:
                logger.info(
                    json.dumps(
                        {
                            "event": "position_sizing",
                            "symbol": opportunity["symbol"],
                            "side": "BUY",
                            "entry": round(opportunity["price"], 6),
                            "quantity": round(position_params.get("quantity", 0), 6),
                            "position_size_usdt": position_params.get("position_size_usdt"),
                            "stop_loss": position_params.get("stop_loss"),
                            "take_profit": position_params.get("take_profit"),
                            "risk_target": position_params.get("risk_amount_target"),
                            "risk_effective": position_params.get("risk_amount"),
                            "risk_pct_effective": position_params.get(
                                "risk_percent_effective", 0.0
                            ),
                            "max_positions": self.config.max_positions,
                        }
                    )
                )
                self.last_risk_snapshot = {
                    "symbol": opportunity["symbol"],
                    "entry": round(opportunity["price"], 6),
                    "stop_loss": position_params.get("stop_loss"),
                    "take_profit": position_params.get("take_profit"),
                    "risk_target": position_params.get("risk_amount_target"),
                    "risk_effective": position_params.get("risk_amount"),
                    "risk_pct_effective": position_params.get("risk_percent_effective", 0.0),
                    "position_size_usdt": position_params.get("position_size_usdt"),
                    "timestamp": datetime.now(UTC).isoformat(),
                }
            except Exception:
                pass

            # Note: No leverage setting in Spot trading

            side = "BUY" if opportunity.get("signal") == "BUY" else "SELL"
            if side == "SELL":
                logger.warning(
                    "Tentativa de venda ignorada no modo Spot: %s", opportunity["symbol"]
                )
                await self._notify_observing("Venda ignorada - aguardando oportunidade de compra.")
                return

            # Place order (apenas operacoes de compra para Spot)
            try:
                order = await self._run_blocking(
                    binance_manager.place_order,
                    opportunity["symbol"],
                    side,
                    position_params["quantity"],
                )
            except BinanceTransientError as exc:
                logger.warning(
                    "Falha temporaria ao enviar ordem %s %s qty=%s: %s",
                    opportunity["symbol"],
                    side,
                    position_params["quantity"],
                    exc,
                )
                self.metrics["binance_errors"] += 1
                await telegram_notifier.send_message_async(
                    f"Falha temporaria ao executar ordem para {opportunity['symbol']}. Tentaremos novamente no proximo ciclo."
                )
                await self._notify_observing(f"Erro temporario na {self.config.exchange.upper()} - aguardando novo ciclo.")
                return
            except BinanceCriticalError as exc:
                logger.error(
                    "Erro critico ao enviar ordem %s %s qty=%s: %s",
                    opportunity["symbol"],
                    side,
                    position_params["quantity"],
                    exc,
                )
                self.metrics["binance_errors"] += 1
                await telegram_notifier.send_message_async(
                    f"{self.config.exchange.upper()} rejeitou ordem para {opportunity['symbol']}: {exc}"
                )
                await self._notify_observing(
                    f"Ordem rejeitada pela {self.config.exchange.upper()} - aguardando nova configuracao."
                )
                return
            except Exception as exc:
                logger.error(
                    "Unexpected error placing order %s %s qty=%s: %s",
                    opportunity["symbol"],
                    side,
                    position_params["quantity"],
                    exc,
                )
                await telegram_notifier.send_message_async(
                    f"Erro inesperado ao executar ordem para {opportunity['symbol']}: {exc!s}"
                )
                await self._notify_observing("Erro ao enviar ordem - verifique os logs.")
                return

            # Create position record
            position = {
                "symbol": opportunity["symbol"],
                "side": side,
                "entry_price": opportunity["price"],
                "quantity": position_params["quantity"],
                "position_size": position_params["position_size_usdt"],
                "leverage": 1,  # Spot trading = no leverage
                "stop_loss": position_params["stop_loss"],
                "take_profit": position_params["take_profit"],
                "opened_at": datetime.now(UTC).isoformat(),
                "status": "open",
                "ml_score": opportunity_score,  # Salvar score de ML
                "risk_amount": position_params.get("risk_amount"),
                "trailing": {
                    "activation_price": round(
                        opportunity["price"]
                        * (
                            1 + position_params.get("trailing_activation", 0) / 100
                            if side == "BUY"
                            else 1 - position_params.get("trailing_activation", 0) / 100
                        ),
                        4,
                    ),
                    "step_pct": position_params.get("trailing_step", 0),
                    "active": False,
                },
            }

            # Double-check for duplicates directly in DB before insert (race condition guard)
            existing = await self.db.positions.find_one(
                {"symbol": opportunity["symbol"], "status": "open"}
            )
            if existing:
                logger.warning(
                    "Position already exists for %s (race condition avoided)", opportunity["symbol"]
                )
                await self._notify_observing(f"Posicao ja existe para {opportunity['symbol']}.")
                return

            # Save to database
            result = await self.db.positions.insert_one(position)
            position["_id"] = result.inserted_id
            self.positions.append(position)

            # 🛡️ PROTEÇÃO: Enviar ordem OCO ao Binance (SL + TP protegidos no servidor)
            # Se o bot cair, as ordens OCO continuam ativas na exchange.
            if side == "BUY":
                try:
                    sl_price = position_params["stop_loss"]
                    tp_price = position_params["take_profit"]
                    entry = opportunity["price"]
                    # stop_limit_price ligeiramente abaixo do stop_price (0.1%) para garantir execução
                    sl_limit_price = round(sl_price * 0.999, 4)

                    # Só enviar OCO se preços fazem sentido (TP > entry > SL)
                    if tp_price > entry > sl_price > 0:
                        oco_result = await self._run_blocking(
                            binance_manager.place_oco_order,
                            opportunity["symbol"],
                            position_params["quantity"],
                            tp_price,
                            sl_price,
                            sl_limit_price,
                        )
                        if oco_result:
                            # Salvar IDs das ordens OCO na posição para cancelar se necessário
                            oco_order_ids = [
                                r.get("orderId")
                                for r in oco_result.get("orderReports", [])
                                if r.get("orderId")
                            ]
                            await self.db.positions.update_one(
                                {"_id": position["_id"]},
                                {"$set": {"oco_order_ids": oco_order_ids}},
                            )
                            position["oco_order_ids"] = oco_order_ids
                            logger.info(
                                "[OCO] %s: ordens de proteção criadas %s",
                                opportunity["symbol"],
                                oco_order_ids,
                            )
                        else:
                            logger.warning(
                                "[OCO] %s: OCO não criado — SL/TP apenas em memória",
                                opportunity["symbol"],
                            )
                    else:
                        logger.warning(
                            "[OCO] %s: preços inválidos tp=%.4f entry=%.4f sl=%.4f — OCO ignorado",
                            opportunity["symbol"],
                            tp_price,
                            entry,
                            sl_price,
                        )
                except Exception as oco_exc:
                    # Falha no OCO não cancela o trade — posição já foi aberta
                    logger.warning(
                        "[OCO] Erro ao criar OCO para %s: %s — usando monitoramento em memória",
                        opportunity["symbol"],
                        oco_exc,
                    )

            # Atualizar métricas de ordem
            self.metrics["orders_submitted"] += 1
            self.metrics["last_order_symbol"] = opportunity["symbol"]
            self.metrics["last_order_timestamp"] = datetime.now(UTC).isoformat()
            await self._get_account_balance(force_refresh=True)

            try:
                loop = asyncio.get_running_loop()
                self._last_observation_notice = loop.time()
            except RuntimeError:
                pass

            # Notify
            await telegram_notifier.notify_position_opened_async(
                opportunity["symbol"],
                side,
                opportunity["price"],
                position_params["position_size_usdt"],
                leverage=1,
                stop_loss=position_params["stop_loss"],
                take_profit=position_params["take_profit"],
                ml_score=opportunity_score,
            )

            logger.info(
                "Opened %s position on %s with ML score %.2f",
                side,
                opportunity["symbol"],
                opportunity_score,
            )

        except Exception as e:
            logger.error("Error opening position: %s", e)

    async def _try_close_position_with_retry(
        self, position: dict, reason: str, max_attempts: int = 1
    ) -> bool:
        """Tenta fechar uma posição, retornando True se sucesso, False se falhar."""
        for attempt in range(max_attempts):
            try:
                # Get current price for proper closing
                try:
                    current_price = await self._run_blocking(
                        binance_manager.get_symbol_price, position["symbol"]
                    )
                except BinanceTransientError as exc:
                    logger.warning(
                        "Falha temporaria ao obter preco para %s: %s", position["symbol"], exc
                    )
                    current_price = position["entry_price"]
                except BinanceCriticalError as exc:
                    logger.error("Erro critico ao obter preco para %s: %s", position["symbol"], exc)
                    current_price = position["entry_price"]

                if not current_price:
                    logger.warning(
                        "Could not get price for %s, using entry price", position["symbol"]
                    )
                    current_price = position["entry_price"]

                await self._close_position(position, current_price, reason)
                await asyncio.sleep(1)  # Small delay between closes
                return True

            except Exception as e:
                logger.error(
                    "Error closing position %s (attempt %d/%d): %s",
                    position.get("symbol"),
                    attempt + 1,
                    max_attempts,
                    e,
                )
                if attempt < max_attempts - 1:
                    await asyncio.sleep(1)

        return False

    async def _check_positions(self):
        """Check and manage open positions.

        NOTA: O trailing stop é verificado a cada ciclo (default 15s).
        Para mercados muito voláteis, considerar implementar websocket
        para atualizações de preço em tempo real (melhoria futura).

        MELHORIA: Trailing progressivo - quanto maior o lucro, mais apertado o trail.
        """
        try:
            async with self._positions_lock:
                if not self.positions:
                    return
                positions_snapshot = list(self.positions)

            symbols = {pos["symbol"] for pos in positions_snapshot}
            price_map = await self._get_price_map(list(symbols))

            for position in positions_snapshot:
                current_price = price_map.get(position["symbol"])
                if current_price is None:
                    continue

                # Calcular lucro atual para trailing progressivo
                entry_price = position["entry_price"]
                if position["side"] == "BUY":
                    profit_pct = ((current_price - entry_price) / entry_price) * 100
                else:
                    profit_pct = ((entry_price - current_price) / entry_price) * 100

                trailing_cfg = position.get("trailing") or {}
                stop_updated = False
                step_pct = trailing_cfg.get("step_pct", 0)
                if step_pct:
                    # MELHORIA: Aplicar fator progressivo ao step
                    trail_factor = self._get_progressive_trail_factor(profit_pct)
                    adjusted_step_pct = step_pct * trail_factor
                    step_pct_dec = adjusted_step_pct / 100

                    activation_price = trailing_cfg.get("activation_price")

                    if activation_price:
                        if position["side"] == "BUY" and current_price >= activation_price:
                            trailing_cfg["active"] = True
                            new_stop = round(current_price * (1 - step_pct_dec), 4)
                            if new_stop > position["stop_loss"]:
                                position["stop_loss"] = new_stop
                                trailing_cfg["activation_price"] = round(
                                    current_price * (1 + step_pct_dec), 4
                                )
                                trailing_cfg["trail_factor"] = trail_factor  # Registrar fator usado
                                stop_updated = True
                        elif position["side"] == "SELL" and current_price <= activation_price:
                            trailing_cfg["active"] = True
                            new_stop = round(current_price * (1 + step_pct_dec), 4)
                            if new_stop < position["stop_loss"]:
                                position["stop_loss"] = new_stop
                                trailing_cfg["activation_price"] = round(
                                    current_price * (1 - step_pct_dec), 4
                                )
                                trailing_cfg["trail_factor"] = trail_factor  # Registrar fator usado
                                stop_updated = True

                if stop_updated:
                    trailing_cfg["last_update"] = datetime.now(UTC).isoformat()
                    try:
                        await self.db.positions.update_one(
                            {"_id": position["_id"]},
                            {
                                "$set": {
                                    "stop_loss": position["stop_loss"],
                                    "trailing": trailing_cfg,
                                }
                            },
                        )
                        logger.info(
                            "Trailing stop ajustado %s -> %.4f (profit: %.2f%%, factor: %.1f)",
                            position["symbol"],
                            position["stop_loss"],
                            profit_pct,
                            trailing_cfg.get("trail_factor", 1.0),
                        )
                    except Exception as e:
                        logger.error(f"Erro ao atualizar trailing stop no banco: {e}")
                    position["trailing"] = trailing_cfg

                # FASE 6: Verificar time stop (4h)
                max_hold_hours = int(os.getenv("RISK_MAX_HOLD_HOURS", "4"))
                if self.risk_manager.should_close_by_time(
                    position["opened_at"], max_hold_hours=max_hold_hours
                ):
                    logger.info(
                        "[Time Stop] Fechando %s - posição aberta há > %dh",
                        position["symbol"],
                        max_hold_hours,
                    )
                    await self._close_position(position, current_price, "TIME_STOP")
                    continue  # Pular para próxima posição

                # Check if should close
                should_close, reason = self.risk_manager.should_close_position(
                    current_price,
                    position["entry_price"],
                    position["stop_loss"],
                    position["take_profit"],
                    position["side"],
                )

                if should_close:
                    await self._close_position(position, current_price, reason)

        except Exception as e:
            logger.error("Error checking positions: %s", e)

    async def _close_position(self, position: dict, exit_price: float, reason: str):
        """Close a position"""
        try:
            # Place closing order
            close_side = "SELL" if position["side"] == "BUY" else "BUY"

            logger.info(f"Fechando posicao {position['symbol']} - Motivo: {reason}")

            # 🛡️ Cancelar ordens OCO pendentes antes de enviar ordem de fechamento
            # Evita double-fill: OCO executando ao mesmo tempo que o fechamento do bot
            oco_ids = position.get("oco_order_ids", [])
            if oco_ids:
                for oco_id in oco_ids:
                    try:
                        await self._run_blocking(
                            binance_manager.cancel_order, position["symbol"], oco_id
                        )
                        logger.info("[OCO] Cancelada ordem %s para %s", oco_id, position["symbol"])
                    except Exception as cancel_exc:
                        # Se já foi executada, o cancelamento falha — é ok, continua
                        logger.debug(
                            "[OCO] Não foi possível cancelar ordem %s: %s", oco_id, cancel_exc
                        )

            try:
                order = await self._run_blocking(
                    binance_manager.place_order,
                    position["symbol"],
                    close_side,
                    position["quantity"],
                )
            except BinanceTransientError as exc:
                logger.warning("Falha temporaria ao fechar %s: %s", position["symbol"], exc)
                await telegram_notifier.send_message_async(
                    f"Falha temporaria ao fechar {position['symbol']}. Tentaremos novamente."
                )
                return
            except BinanceCriticalError as exc:
                logger.error("Erro critico ao fechar %s: %s", position["symbol"], exc)
                await telegram_notifier.send_message_async(
                    f"Erro critico ao fechar {position['symbol']}: {exc}"
                )
                return
            if not order:
                logger.error(f"Falha ao fechar posicao {position['symbol']}")
                return

            # Calculate PnL
            try:
                pnl_data = self.risk_manager.calculate_pnl(
                    position["entry_price"],
                    exit_price,
                    position["quantity"],
                    position["side"],
                    1,  # Spot trading = no leverage
                )
            except Exception as e:
                logger.error(f"Erro ao calcular PnL: {e}")
                pnl_data = {"pnl": 0.0, "roe": 0.0}

            # Update position
            position["exit_price"] = exit_price
            position["pnl"] = pnl_data["pnl"]
            position["roe"] = pnl_data["roe"]
            position["closed_at"] = datetime.now(UTC).isoformat()
            position["close_reason"] = reason
            position["status"] = "closed"

            # Update in database
            try:
                await self.db.positions.update_one({"_id": position["_id"]}, {"$set": position})
                logger.info("Posicao atualizada no banco de dados")
            except Exception as e:
                logger.error(f"Erro ao atualizar posicao no banco: {e}")

            # Save to trades history
            try:
                await self.db.trades.insert_one(position)
                logger.info("Trade salvo no historico")
            except Exception as e:
                logger.error(f"Erro ao salvar trade no historico: {e}")

            #  MACHINE LEARNING: Learn from this trade
            try:
                await self.learning_system.learn_from_trade(position)
                logger.info("Sistema de aprendizado atualizado")
            except Exception as e:
                logger.error(f"Erro no sistema de aprendizado: {e}")

            # NOVO: LLM Market Analyzer - Adicionar ao histórico para aprendizado
            if self.market_analyzer and "market_regime" in position:
                try:
                    # Calcular duração em minutos
                    from dateutil import parser as date_parser

                    opened_at = date_parser.isoparse(position["opened_at"])
                    closed_at = date_parser.isoparse(position["closed_at"])
                    duration_minutes = int((closed_at - opened_at).total_seconds() / 60)

                    self.market_analyzer.add_trade_to_history(
                        symbol=position["symbol"],
                        pnl_pct=pnl_data["roe"],
                        duration_minutes=duration_minutes,
                        regime=position["market_regime"],
                    )
                    logger.info(
                        f"[LLM Market] Trade adicionado ao histórico: "
                        f"{position['symbol']} {pnl_data['roe']:+.2f}% em {duration_minutes}min"
                    )
                except Exception as e:
                    logger.error(f"[LLM Market] Erro ao adicionar ao histórico: {e}")

            # 🧠 FUNCIONALIDADE #5: FEEDBACK DE TRADES PARA REGIME ADAPTATIVO
            if self.risk_advisor:
                try:
                    from dateutil import parser as date_parser

                    opened_at = date_parser.isoparse(position["opened_at"])
                    closed_at = date_parser.isoparse(position["closed_at"])
                    duration_minutes = int((closed_at - opened_at).total_seconds() / 60)

                    self.risk_advisor.add_trade_feedback(
                        symbol=position["symbol"],
                        entry_time=opened_at,
                        regime=position.get("market_regime", "unknown"),
                        score=position.get("score", 0),
                        pnl_percent=pnl_data["roe"],
                        duration_minutes=duration_minutes,
                        hit_stop=(reason == "STOP_LOSS"),
                    )

                    logger.info(
                        f"[AI Feedback] Trade registrado: {position['symbol']} "
                        f"{'+' if pnl_data['roe'] > 0 else ''}{pnl_data['roe']:.2f}% "
                        f"em {duration_minutes}min ({reason})"
                    )
                except Exception as e:
                    logger.error(f"[AI Feedback] Erro ao registrar feedback: {e}")

            # Remove from active positions (protegido por lock)
            try:
                async with self._positions_lock:
                    if position in self.positions:
                        self.positions.remove(position)
                logger.info("Posicao removida da lista ativa")
            except Exception as e:
                logger.error("Erro ao remover posicao da lista: %s", e)

            # Notify
            try:
                reason_label = {
                    "STOP_LOSS": "Stop Loss atingido",
                    "TAKE_PROFIT": "Take Profit atingido",
                    "TIME_STOP": "Tempo limite atingido (8h)",
                }.get(reason, reason)

                await telegram_notifier.notify_position_closed_async(
                    position["symbol"],
                    position["side"],
                    position["entry_price"],
                    exit_price,
                    pnl_data["pnl"],
                    pnl_data["roe"],
                    reason_label,
                )
                logger.info("Notificacao Telegram enviada")
            except Exception as e:
                logger.error(f"Erro ao enviar notificacao Telegram: {e}")

            # Cooldown pós stop loss: registrar símbolo para não recomprar imediatamente
            if reason == "STOP_LOSS" and self._sl_cooldown_minutes > 0:
                self._sl_cooldown[position["symbol"]] = time.time()
                logger.info(
                    "⏳ Cooldown %dmin ativado para %s após STOP_LOSS",
                    self._sl_cooldown_minutes, position["symbol"],
                )

            if not self.positions:
                await self._notify_observing(
                    "Sem posicoes abertas. Em observacao aguardando novo setup.", force=True
                )

            await self._get_account_balance(force_refresh=True)
            logger.info(
                "Posicao fechada: %s %s | PnL: %.2f USDT",
                position["side"],
                position["symbol"],
                pnl_data["pnl"],
            )

        except Exception as e:
            logger.error("ERRO CRITICO ao fechar posicao: %s", e)
            import traceback

            logger.error(traceback.format_exc())

    async def _refresh_positions_cache(self) -> list[dict]:
        """Reload open positions from MongoDB so the DB stays the source of truth."""
        try:
            cursor = self.db.positions.find({"status": "open"}).sort("opened_at", 1)
            positions = await cursor.to_list(self._positions_cache_limit)
            async with self._positions_lock:
                self.positions = positions
            return positions
        except Exception as e:
            logger.error("Error refreshing open positions cache: %s", e)
            async with self._positions_lock:
                return list(self.positions)

    async def _load_positions(self):
        """Load open positions from database"""
        try:
            positions = await self._refresh_positions_cache()
            logger.info("Loaded %d open positions", len(positions))
        except Exception as e:
            logger.error("Error loading positions: %s", e)

    async def _cleanup_existing_positions(self):
        """Cleanup existing positions before starting bot"""
        try:
            logger.info("Iniciando limpeza de posicoes existentes...")

            # 1. Buscar ordens abertas na Binance Spot
            # In Spot, we check for open orders instead of positions
            try:
                open_orders = await self._run_blocking(binance_manager.get_open_orders)
            except BinanceTransientError as exc:
                logger.warning("Falha temporaria ao listar ordens abertas: %s", exc)
                await telegram_notifier.send_message_async(
                    "Nao foi possivel listar ordens abertas. Tente novamente."
                )
                return {
                    "status": "retry",
                    "found_orders": 0,
                    "canceled_orders": 0,
                    "error": str(exc),
                }
            except BinanceCriticalError as exc:
                logger.error("Erro critico ao listar ordens abertas: %s", exc)
                await telegram_notifier.send_message_async(
                    f"Erro ao consultar ordens abertas: {exc}"
                )
                return {
                    "status": "error",
                    "found_orders": 0,
                    "canceled_orders": 0,
                    "error": str(exc),
                }

            if not open_orders:
                logger.info("Nenhuma ordem aberta na exchange. Conta limpa!")
                await telegram_notifier.send_message_async("Conta limpa - Nenhuma ordem aberta")

                # Limpar MongoDB tambem (caso tenha lixo)
                await self.db.positions.delete_many({"status": "open"})
                await self._refresh_positions_cache()
                return {"status": "clean", "found_orders": 0, "canceled_orders": 0}

            # 2. Tem ordens abertas - CANCELAR TODAS
            logger.warning("Encontradas %d ordens abertas! Cancelando...", len(open_orders))
            await telegram_notifier.send_message_async(
                f"Encontradas {len(open_orders)} ordens abertas na conta!\n"
                f"Cancelando todas antes de iniciar o bot..."
            )

            canceled_count = 0
            for order in open_orders:
                try:
                    symbol = order["symbol"]
                    order_id = order["orderId"]
                    side = order["side"]
                    quantity = float(order["origQty"])
                    price = float(order.get("price", 0))
                    order_type = order["type"]

                    logger.info(
                        "Cancelando %s %s %s | Qty: %s | Price: $%.2f",
                        symbol,
                        side,
                        order_type,
                        quantity,
                        price,
                    )

                    # Cancelar ordem
                    try:
                        await self._run_blocking(binance_manager.cancel_order, symbol, order_id)
                        canceled_count += 1
                        logger.info("Ordem %s cancelada", symbol)
                        await telegram_notifier.send_message_async(
                            f"Ordem cancelada:\n"
                            f"   {symbol} {side} {order_type}\n"
                            f"   Qty: {quantity}\n"
                            f"   Price: ${price:.2f}"
                        )
                        await asyncio.sleep(0.5)  # Delay entre cancelamentos
                    except BinanceTransientError as exc:
                        logger.warning("Falha temporaria ao cancelar ordem %s: %s", symbol, exc)
                        await telegram_notifier.send_message_async(
                            f"Falha temporaria ao cancelar ordem {symbol}: {exc}"
                        )
                    except BinanceCriticalError as exc:
                        logger.error("Erro critico ao cancelar ordem %s: %s", symbol, exc)
                        await telegram_notifier.send_message_async(
                            f"Erro ao cancelar ordem {symbol}: {exc}"
                        )
                    except Exception as e:
                        logger.error(
                            "Erro cancelando ordem %s: %s", order.get("symbol", "UNKNOWN"), e
                        )
                        await telegram_notifier.send_message_async(
                            f"Erro inesperado ao cancelar ordem {symbol}: {e}"
                        )

                except Exception as e:
                    logger.error("Erro cancelando ordem %s: %s", order.get("symbol", "UNKNOWN"), e)

            # 3. Limpar MongoDB
            await self.db.positions.delete_many({"status": "open"})
            await self._refresh_positions_cache()

            logger.info(
                "Limpeza concluida! %d/%d ordens canceladas", canceled_count, len(open_orders)
            )
            await telegram_notifier.send_message_async(
                f"Limpeza concluida!\n"
                f"   {canceled_count} ordens canceladas\n"
                f"   Conta pronta para operar!"
            )

            # Pequeno delay para garantir que ordens foram processadas
            await asyncio.sleep(2)
            return {
                "status": "cleaned",
                "found_orders": len(open_orders),
                "canceled_orders": canceled_count,
            }

        except Exception as e:
            logger.error("Erro na limpeza de posicoes: %s", e)
            await telegram_notifier.send_message_async(f"Erro na limpeza: {e!s}")
            return {"status": "error", "found_orders": 0, "canceled_orders": 0, "error": str(e)}

    async def sync_account(self) -> dict:
        """Public method to trigger account synchronization/cleanup"""
        result = await self._cleanup_existing_positions()
        return result or {"status": "unknown", "found_orders": 0, "canceled_orders": 0}

    def _sanitize_positions(self, positions: list[dict]) -> list[dict]:
        """Convert MongoDB ObjectId to string for JSON serialization."""
        sanitized = []
        for pos in positions:
            clean_pos = {}
            for key, value in pos.items():
                if hasattr(value, "__str__") and type(value).__name__ == "ObjectId":
                    clean_pos[key] = str(value)
                elif isinstance(value, dict):
                    clean_pos[key] = {
                        k: str(v) if type(v).__name__ == "ObjectId" else v for k, v in value.items()
                    }
                else:
                    clean_pos[key] = value
            sanitized.append(clean_pos)
        return sanitized

    async def get_status(self) -> dict:
        """Get bot status"""
        try:
            await self._refresh_positions_cache()
            
            paper_trade = getattr(binance_manager, "_paper_trade", False)
            balance = 0
            
            if paper_trade:
                # Paper mode: compute real equity from trades
                paper_initial = float(os.getenv("PAPER_TRADE_BALANCE", 1000.0))
                invested = sum(p.get("position_size", 0) for p in self.positions)
                try:
                    pipeline = [{"$group": {"_id": None, "total": {"$sum": "$pnl"}}}]
                    result = await self.db.trades.aggregate(pipeline).to_list(length=1)
                    total_pnl = result[0]["total"] if result else 0.0
                except Exception:
                    total_pnl = 0.0
                equity = paper_initial + total_pnl
                available = equity - invested
                balance = available
            elif binance_manager.client:
                # Live mode: fetch real balance from Binance
                cached_balance = await self._get_account_balance()
                balance = cached_balance if cached_balance is not None else 0
                equity = balance
                available = balance
                invested = sum(p.get("position_size", 0) for p in self.positions)
                total_pnl = 0.0
                paper_initial = 0.0

            # Sanitize positions to convert ObjectId to string
            sanitized_positions = self._sanitize_positions(self.positions)

            return {
                "is_running": self.is_running,
                "balance": round(balance, 2),
                "equity": round(equity, 2),
                "available": round(available, 2),
                "invested": round(invested, 2),
                "total_pnl": round(total_pnl, 2),
                "paper_initial": paper_initial,
                "open_positions": len(self.positions),
                "max_positions": self.risk_manager.max_positions,
                "positions": sanitized_positions,
                "testnet_mode": binance_manager.use_testnet,
                "paper_trade": paper_trade,
            }
        except Exception as e:
            logger.error("Error getting status: %s", e)
            return {
                "is_running": False,
                "balance": 0,
                "testnet_mode": binance_manager.use_testnet,
                "paper_trade": getattr(binance_manager, "_paper_trade", False),
                "error": str(e),
            }

    # ========== CIRCUIT BREAKER ==========
    def _record_failure(self) -> None:
        """Registra uma falha consecutiva. Abre o circuit breaker se exceder limite."""
        self._consecutive_failures += 1
        logger.warning(
            "Falha consecutiva #%d/%d registrada",
            self._consecutive_failures,
            self._max_consecutive_failures,
        )
        if self._consecutive_failures >= self._max_consecutive_failures:
            self._open_circuit_breaker()

    def _reset_circuit_breaker(self) -> None:
        """Reseta o contador de falhas após operação bem-sucedida."""
        if self._consecutive_failures > 0:
            logger.info("Circuit breaker resetado - operacao bem-sucedida")
        self._consecutive_failures = 0

    def _open_circuit_breaker(self) -> None:
        """Abre o circuit breaker, pausando operações por um período."""
        try:
            loop = asyncio.get_running_loop()
            self._circuit_open_until = loop.time() + self._circuit_breaker_cooldown
        except RuntimeError:
            import time

            self._circuit_open_until = time.time() + self._circuit_breaker_cooldown

        logger.error(
            "CIRCUIT BREAKER ABERTO - %d falhas consecutivas. "
            "Pausando operacoes por %d segundos.",
            self._consecutive_failures,
            self._circuit_breaker_cooldown,
        )
        # Notificar via Telegram (fire-and-forget)
        _ = asyncio.create_task(
            telegram_notifier.send_message_async(
                f"⚠️ CIRCUIT BREAKER ATIVADO\n"
                f"Falhas consecutivas: {self._consecutive_failures}\n"
                f"Pausando operações por {self._circuit_breaker_cooldown // 60} minutos.\n"
                f"Verifique conexao com {self.config.exchange.upper()}."
            )
        )

    def _is_circuit_open(self) -> bool:
        """Verifica se o circuit breaker está aberto."""
        if self._circuit_open_until <= 0:
            return False
        try:
            loop = asyncio.get_running_loop()
            current_time = loop.time()
        except RuntimeError:
            import time

            current_time = time.time()

        if current_time >= self._circuit_open_until:
            # Cooldown expirou - fechar circuit breaker
            self._circuit_open_until = 0.0
            self._consecutive_failures = 0
            logger.info("Circuit breaker FECHADO - retomando operacoes")
            _ = asyncio.create_task(
                telegram_notifier.send_message_async(
                    "✅ Circuit breaker desativado. Retomando operações."
                )
            )
            return False
        return True

    def _apply_config(self, config: BotConfig) -> None:
        """Refresh runtime dependencies according to config values."""
        sanitized = config.sanitized()
        self.config = sanitized
        self.risk_manager = RiskManager(
            risk_percentage=sanitized.risk_percentage,
            max_positions=sanitized.max_positions,
            leverage=1,
            stop_loss_percentage=sanitized.risk_stop_loss_percentage,
            reward_ratio=sanitized.risk_reward_ratio,
            trailing_activation=sanitized.risk_trailing_activation,
            trailing_step=sanitized.risk_trailing_step,
            use_position_cap=getattr(sanitized, "risk_use_position_cap", True),
        )
        self.balance_cache_ttl = sanitized.balance_cache_ttl
        self.observation_alert_interval = sanitized.observation_alert_interval
        self.check_interval = sanitized.loop_interval_seconds
        self.use_position_cap = getattr(sanitized, "risk_use_position_cap", True)
        self.daily_drawdown_limit_pct = getattr(sanitized, "daily_drawdown_limit_pct", 0.0)
        self.weekly_drawdown_limit_pct = getattr(sanitized, "weekly_drawdown_limit_pct", 0.0)
        if self.strategy:
            self.strategy.timeframe = sanitized.strategy_timeframe
            self.strategy.confirmation_timeframe = sanitized.strategy_confirmation_timeframe
            self.strategy.limit = sanitized.strategy_klines_limit
            self.strategy.set_min_signal_strength(sanitized.strategy_min_signal_strength)
            self.strategy.activation_threshold = sanitized.strategy_activation_threshold
        if self.selector:
            self.selector.update_settings(
                base_symbols=sanitized.selector_base_symbols,
                trending_refresh_interval=sanitized.selector_trending_refresh_interval,
                min_change_percent=sanitized.selector_min_change_percent,
                trending_pool_size=sanitized.selector_trending_pool_size,
            )

    def _calculate_min_strength_from_learning(self) -> int:
        """Convert learned confidence (0-1) to strength threshold (0-100)."""
        base_strength = max(0, min(100, int(self.config.strategy_min_signal_strength or 0)))
        try:
            # Usar novo sistema de aprendizado avançado
            score = float(
                self.learning_system.params.get("min_confidence_score", base_strength / 100)
            )
            return max(0, min(100, int(score * 100)))
        except Exception:
            return base_strength

    def _sync_strategy_learning_params(self) -> None:
        """Apply learning-based thresholds to the trading strategy."""
        if self.strategy:
            self.strategy.set_min_signal_strength(self._calculate_min_strength_from_learning())

    async def get_learning_report(self) -> dict:
        """Retorna relatório do sistema de aprendizado avançado."""
        return await self.learning_system.get_learning_report()


# Global bot instance
bot_instance = None


async def get_bot(db) -> TradingBot:
    """Get or create bot instance"""
    global bot_instance
    if bot_instance is None:
        bot_instance = TradingBot(db)
        await bot_instance.initialize()
    return bot_instance
