import asyncio
import logging
import os
import time
import json
import pandas as pd
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Optional, Any
from motor.motor_asyncio import AsyncIOMotorClient

from binance.exceptions import BinanceAPIException, BinanceOrderException

# Circuit breaker defaults - mais tolerante para evitar pausas desnecessárias
DEFAULT_MAX_CONSECUTIVE_FAILURES = 10  # Aumentado de 5 para 10
DEFAULT_CIRCUIT_BREAKER_COOLDOWN = 120  # Reduzido de 5 min para 2 min

from bot.binance_client import (
    binance_manager,
    BinanceTransientError,
    BinanceCriticalError,
)
from bot.config import BotConfig, load_bot_config
from bot.telegram_client import telegram_notifier
from bot.strategy import TradingStrategy
from bot.selector import CryptoSelector
from bot.risk_manager import RiskManager
from bot.advanced_learning import AdvancedLearningSystem

# ML Signal Filter - modelo treinado com dados historicos
try:
    from ml.ml_signal_filter import get_ml_filter, MLSignalFilter
    ML_FILTER_AVAILABLE = True
except ImportError:
    ML_FILTER_AVAILABLE = False

logger = logging.getLogger(__name__)

class TradingBot:
    def __init__(self, db):
        self.db = db
        self.is_running = False
        self.positions: List[Dict] = []
        self.config = BotConfig.from_env()
        self.risk_manager = RiskManager(
            risk_percentage=self.config.risk_percentage,
            max_positions=self.config.max_positions,
            leverage=1,  # Spot trading = no leverage
            stop_loss_percentage=self.config.risk_stop_loss_percentage,
            reward_ratio=self.config.risk_reward_ratio,
            trailing_activation=self.config.risk_trailing_activation,
            trailing_step=self.config.risk_trailing_step,
            use_position_cap=getattr(self.config, 'risk_use_position_cap', True),
        )
        self.learning_system = AdvancedLearningSystem(db)

        # ML Signal Filter - modelo treinado com dados historicos
        self.ml_filter = None
        if ML_FILTER_AVAILABLE:
            try:
                self.ml_filter = get_ml_filter()
                if self.ml_filter.loaded:
                    logger.info("[ML] Filtro de sinais ML carregado com sucesso!")
                    logger.info("[ML] Accuracy: %.2f%% | Min confidence: %.2f",
                               self.ml_filter.metrics.get('accuracy', 0) * 100,
                               self.ml_filter.min_confidence)
                else:
                    logger.warning("[ML] Modelo nao encontrado - filtro ML desabilitado")
            except Exception as e:
                logger.warning("[ML] Erro ao carregar filtro ML: %s", e)
        else:
            logger.info("[ML] Modulo ML nao disponivel - usando apenas regras base")

        self.selector = None
        self.strategy = None
        self.check_interval = self.config.loop_interval_seconds
        self._loop_task: Optional[asyncio.Task] = None
        self._balance_cache = {'value': 0.0, 'timestamp': 0.0}
        self.balance_cache_ttl = self.config.balance_cache_ttl
        self.observation_alert_interval = self.config.observation_alert_interval
        self._last_observation_notice = 0.0
        self._positions_cache_limit = 500
        self.last_error: Optional[str] = None
        self.last_risk_snapshot: Optional[Dict[str, Any]] = None

        # Risco e proteções adicionais
        self.use_position_cap = getattr(self.config, 'risk_use_position_cap', True)
        self.daily_drawdown_limit_pct = getattr(self.config, 'daily_drawdown_limit_pct', 0.0)
        self.weekly_drawdown_limit_pct = getattr(self.config, 'weekly_drawdown_limit_pct', 0.0)
        self.api_latency_threshold = float(os.getenv("API_LATENCY_THRESHOLD", "2.0"))

        # Métricas simples
        self.metrics = {
            'orders_submitted': 0,
            'binance_errors': 0,
            'last_loop_ms': None,
            'last_order_symbol': None,
            'last_order_timestamp': None,
        }

        # Circuit breaker: pausa bot após falhas consecutivas
        self._consecutive_failures = 0
        self._max_consecutive_failures = DEFAULT_MAX_CONSECUTIVE_FAILURES
        self._circuit_breaker_cooldown = DEFAULT_CIRCUIT_BREAKER_COOLDOWN
        self._circuit_open_until: float = 0.0
        
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
                getattr(func, '__name__', str(func)),
            )
            self._record_failure()
        else:
            self._reset_circuit_breaker()
        return result

    async def _notify_observing(self, note: Optional[str] = None, force: bool = False):
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

    async def _get_account_balance(self, force_refresh: bool = False) -> Optional[float]:
        """Return cached account balance to avoid hitting the API on every iteration"""
        async with self._balance_lock:
            loop = asyncio.get_running_loop()
            elapsed = loop.time() - self._balance_cache['timestamp']

            if not force_refresh and elapsed < self.balance_cache_ttl:
                return self._balance_cache['value']

            try:
                balance = await self._run_blocking(binance_manager.get_account_balance)
                self._reset_circuit_breaker()  # Sucesso: resetar contador
            except BinanceTransientError as exc:
                logger.warning("Problema temporario ao buscar saldo: %s", exc)
                self._record_failure()
                self.metrics['binance_errors'] += 1
                return None
            except BinanceCriticalError as exc:
                logger.error("Erro critico ao buscar saldo: %s", exc)
                self._record_failure()
                self.metrics['binance_errors'] += 1
                await telegram_notifier.send_message_async(
                    "Erro critico ao consultar saldo na Binance. Verifique credenciais ou limite de API."
                )
                return None

            if balance is not None:
                self._balance_cache['value'] = balance
                self._balance_cache['timestamp'] = loop.time()

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
            self.metrics['binance_errors'] += 1
            return {}
        except BinanceCriticalError as exc:
            logger.error("Erro critico ao buscar precos: %s", exc)
            self._record_failure()
            self.metrics['binance_errors'] += 1
            await telegram_notifier.send_message_async(
                "Erro critico ao buscar precos na Binance. Cheque as credenciais ou status da API."
            )
            return {}

    async def _check_drawdown_limits(self, balance: float) -> bool:
        """Check daily/weekly drawdown limits; pause if exceeded."""
        if balance is None or balance <= 0:
            return True

        day_limit = getattr(self, 'daily_drawdown_limit_pct', 0.0) or 0.0
        week_limit = getattr(self, 'weekly_drawdown_limit_pct', 0.0) or 0.0
        if day_limit <= 0 and week_limit <= 0:
            return True

        now = datetime.now(timezone.utc)
        day_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
        week_start = day_start - timedelta(days=day_start.weekday())

        async def _pnl_since(start_dt):
            trades = await self.db.trades.find(
                {'closed_at': {'$gte': start_dt.isoformat()}},
                {'pnl': 1, '_id': 0}
            ).to_list(1000)
            return sum(t.get('pnl', 0) for t in trades)

        if day_limit > 0:
            day_pnl = await _pnl_since(day_start)
            day_limit_value = - (day_limit / 100) * balance
            if day_pnl <= day_limit_value:
                logger.error(
                    "Limite de perda diaria atingido: pnl=%.2f limite=%.2f (%.2f%%)",
                    day_pnl, day_limit_value, -day_limit
                )
                await telegram_notifier.send_message_async(
                    f"⏸️ Bot pausado: perda diaria {day_pnl:.2f} <= limite {day_limit_value:.2f} ({day_limit:.1f}%)."
                )
                self.is_running = False
                self.last_error = "Limite de perda diaria atingido"
                return False

        if week_limit > 0:
            week_pnl = await _pnl_since(week_start)
            week_limit_value = - (week_limit / 100) * balance
            if week_pnl <= week_limit_value:
                logger.error(
                    "Limite de perda semanal atingido: pnl=%.2f limite=%.2f (%.2f%%)",
                    week_pnl, week_limit_value, -week_limit
                )
                await telegram_notifier.send_message_async(
                    f"⏸️ Bot pausado: perda semanal {week_pnl:.2f} <= limite {week_limit_value:.2f} ({week_limit:.1f}%)."
                )
                self.is_running = False
                self.last_error = "Limite de perda semanal atingido"
                return False

        return True

    async def initialize(self, config: Optional[BotConfig] = None):
        """Initialize bot components"""
        try:
            config_obj = config or await load_bot_config(self.db)
            self._apply_config(config_obj)

            logger.info(
                "Loading config (source=%s, testnet=%s)",
                "provided" if config is not None else "db/env",
                self.config.binance_testnet,
            )

            success = binance_manager.initialize(
                api_key=self.config.binance_api_key,
                api_secret=self.config.binance_api_secret,
                testnet=self.config.binance_testnet,
            )
            logger.info("Binance initialization: %s", "Success" if success else "Failed")

            telegram_notifier.initialize(
                bot_token=self.config.telegram_bot_token,
                chat_id=self.config.telegram_chat_id,
                verify_ssl=self.config.telegram_verify_ssl,
            )

            if binance_manager.client:
                self.strategy = TradingStrategy(
                    binance_manager.client,
                    min_signal_strength=self.config.strategy_min_signal_strength,
                    timeframe=self.config.strategy_timeframe,
                    confirmation_timeframe=self.config.strategy_confirmation_timeframe,
                    limit=self.config.strategy_klines_limit,
                )
                self.selector = CryptoSelector(
                    binance_manager.client,
                    self.strategy,
                    base_symbols=self.config.selector_base_symbols,
                    trending_refresh_interval=self.config.selector_trending_refresh_interval,
                    min_change_percent=self.config.selector_min_change_percent,
                    trending_pool_size=self.config.selector_trending_pool_size,
                    min_quote_volume=self.config.selector_min_quote_volume,
                    max_spread_percent=self.config.selector_max_spread_percent,
                )
            
            # Initialize Learning System
            await self.learning_system.initialize()
            self._sync_strategy_learning_params()
            
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
                logger.error("Binance client not initialized")
                self.last_error = "Binance client not initialized"
                return False
            
            # VERIFICACAO E LIMPEZA INICIAL
            logger.info("Verificando posicoes existentes na Binance antes de iniciar...")
            await telegram_notifier.send_message_async("Verificando posicoes abertas na conta...")
            
            cleanup_result = await self._cleanup_existing_positions()
            if cleanup_result and cleanup_result.get('status') not in {'clean', 'cleaned'}:
                self.last_error = cleanup_result.get('error') or cleanup_result.get('status') or "Falha na limpeza inicial"
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
                watch_note or "Monitorando pares com gerenciamento de risco ativo.",
                force=True
            )
            
            logger.info("Trading bot started")
            self.last_error = None
            
            # Start main loop
            self._loop_task = asyncio.create_task(self._trading_loop(), name="trading_loop")
            
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
            await telegram_notifier.send_message_async("Bot parando - Fechando posicoes abertas com seguranca...")
            
            self.is_running = False
            await self._refresh_positions_cache()
            
            # Close all open positions before stopping with retry queue
            if self.positions:
                logger.info("Closing %d open positions...", len(self.positions))
                failed_positions = []
                max_retries = 3
                
                for position in self.positions[:]:  # Copy list to avoid modification during iteration
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
                        retry_count, max_retries, len(failed_positions)
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
                    symbols = [p.get('symbol', 'UNKNOWN') for p in failed_positions]
                    logger.error(
                        "ATENCAO: %d posicoes NAO foram fechadas: %s",
                        len(failed_positions), ", ".join(symbols)
                    )
                    await telegram_notifier.send_message_async(
                        f"⚠️ ATENÇÃO: {len(failed_positions)} posições não foram fechadas!\n"
                        f"Símbolos: {', '.join(symbols)}\n"
                        f"Verifique manualmente na Binance."
                    )
                else:
                    logger.info("All positions closed safely")
                    await telegram_notifier.send_message_async("Todas as posicoes fechadas com seguranca. Bot parado.")
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
                        max(0, remaining)
                    )
                    await asyncio.sleep(min(self.check_interval, remaining))
                    continue
                
                await self._refresh_positions_cache()
                # Check existing positions
                await self._check_positions()
                
                # Look for new opportunities if not at max positions
                async with self._positions_lock:
                    current_count = len(self.positions)
                if current_count < self.risk_manager.max_positions:
                    # Re-sync before opening to ensure DB is the source of truth
                    await self._refresh_positions_cache()
                    async with self._positions_lock:
                        current_count = len(self.positions)
                    if current_count < self.risk_manager.max_positions:
                        await self._find_and_open_position()
                
                # Wait before next iteration
                self.metrics['last_loop_ms'] = (time.perf_counter() - loop_start) * 1000
                await asyncio.sleep(self.check_interval)
                
            except Exception as e:
                logger.error("Error in trading loop: %s", e)
                self._record_failure()
                await asyncio.sleep(self.check_interval)
    
    def _is_near_candle_close(self, timeframe: str = '15m', threshold_seconds: int = 45) -> bool:
        """
        Verifica se estamos próximos do fechamento da vela.
        Retorna True se faltam menos de threshold_seconds para fechar.
        Isso evita entrar em sinais que podem mudar antes da vela fechar.
        """
        now = datetime.now(timezone.utc)
        
        # Mapear timeframe para minutos
        tf_minutes = {'1m': 1, '3m': 3, '5m': 5, '15m': 15, '30m': 30, '1h': 60, '4h': 240}
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
        Verifica se BTC está em condição favorável para longs em altcoins.
        Retorna False se BTC está em queda forte (evita entradas).
        """
        try:
            if not self.strategy:
                return True
            
            btc_analysis = await self._run_blocking(
                self.strategy.analyze_symbol, 'BTCUSDT'
            )
            
            if not btc_analysis:
                logger.debug("Não foi possível analisar BTC - continuando")
                return True
            
            btc_trend = btc_analysis.get('trend', 'neutral')
            btc_rsi = btc_analysis.get('rsi', 50)
            btc_trend_bias = btc_analysis.get('trend_bias', 'neutral')
            
            # BTC em queda forte = não entrar em alts
            if btc_trend == 'bearish' and btc_rsi < 35:
                logger.warning(
                    "BTC em queda forte (trend=%s, RSI=%.1f) - evitando entradas em alts",
                    btc_trend, btc_rsi
                )
                return False
            
            # BTC em tendência de baixa no timeframe maior = cautela
            if btc_trend_bias == 'bearish' and btc_rsi < 40:
                logger.warning(
                    "BTC com viés bearish (bias=%s, RSI=%.1f) - evitando entradas em alts",
                    btc_trend_bias, btc_rsi
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
        
        now = datetime.now(timezone.utc)
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
                await self._notify_observing("BTC em queda - aguardando estabilização para entrar em alts.")
                return
            
            # MELHORIA 2: Verificar se estamos perto do fechamento da vela
            timeframe = getattr(self.strategy, 'timeframe', '15m')
            if not self._is_near_candle_close(timeframe, threshold_seconds=60):
                logger.debug("Aguardando fechamento de vela para confirmar sinal")
                # Não retornar - apenas logar. Pode ser configurável.
            
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
                excluded_symbols = [pos['symbol'] for pos in self.positions]
            
            #  Use CryptoSelector to find best opportunity
            opportunity = await self._run_blocking(
                self.selector.select_best_crypto,
                excluded_symbols
            )
            
            if not opportunity:
                logger.info("No trading opportunities found")
                await self._notify_observing("Sem sinais convincentes no momento.")
                return
            
            logger.info(
                "Opportunity found: %s | Signal: %s | Score: %.2f",
                opportunity['symbol'],
                opportunity['signal'],
                opportunity.get('score', 0)
            )

            if opportunity.get('signal') != 'BUY':
                logger.info(
                    "Sinal %s ignorado para operacao Spot: %s",
                    opportunity.get('signal'),
                    opportunity['symbol']
                )
                await self._notify_observing("Sinal de venda ignorado - aguardando setup de compra.")
                return
            
            #  Get additional market data for ML analysis
            opportunity['volume'] = opportunity.get('volume_ratio', 1.0) * 1000000  # Estimate volume
            opportunity['avg_volume'] = 1000000
            
            # Open position with ML filtering
            await self._open_position(opportunity)
            
        except Exception as e:
            logger.error("Error finding and opening position: %s", e)
    
    async def _open_position(self, opportunity: Dict):
        """Open a trading position with ML-based filtering"""
        try:
            #  MACHINE LEARNING: Calcular score de confianca
            market_conditions = {
                'volume': opportunity.get('volume', 0),
                'avg_volume': opportunity.get('avg_volume', 1),
                'trend': opportunity.get('trend', 'neutral'),
                'rsi': opportunity.get('rsi', 50)
            }
            
            opportunity_score = self.learning_system.calculate_opportunity_score(
                opportunity, 
                market_conditions
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
                logger.info(f"Trade rejeitado por ML antigo - {reason}")
                await self._notify_observing("Filtro de confianca descartou o sinal.")
                return

            # NOVO: Filtro ML treinado com dados historicos
            if self.ml_filter and self.ml_filter.loaded:
                # Preparar indicadores para o filtro ML
                ml_indicators = {
                    'rsi': opportunity.get('rsi', 50),
                    'macd': opportunity.get('macd', 0),
                    'macd_signal': opportunity.get('macd_signal', 0),
                    'macd_hist': opportunity.get('macd_hist', 0),
                    'close': opportunity.get('price', opportunity.get('close', 0)),
                    'ema_fast': opportunity.get('ema_fast', 0),
                    'ema_slow': opportunity.get('ema_slow', 0),
                    'ema_50': opportunity.get('ema_50', 0),
                    'ema_200': opportunity.get('ema_200', 0),
                    'bb_upper': opportunity.get('bb_upper', 0),
                    'bb_lower': opportunity.get('bb_lower', 0),
                    'atr': opportunity.get('atr', 0),
                    'vwap': opportunity.get('vwap', 0),
                    'volume_ratio': opportunity.get('volume_ratio', 1),
                }

                ml_should_trade, ml_confidence, ml_reason = self.ml_filter.should_take_trade(
                    opportunity, ml_indicators
                )

                logger.info(f"[ML Filter] {opportunity['symbol']}: {ml_reason}")

                if not ml_should_trade:
                    logger.info(f"Trade rejeitado por ML Filter - {ml_reason}")
                    await self._notify_observing(f"Filtro ML rejeitou: {ml_reason}")
                    return

                # Adicionar confianca ML ao opportunity para logging
                opportunity['ml_confidence'] = ml_confidence
                logger.info(f"[ML Filter] Trade aprovado com confianca {ml_confidence:.2%}")

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
            volatility_regime = 'normal'
            try:
                # Buscar dados históricos para calcular ATR
                df = await self._run_blocking(
                    self.strategy.get_historical_data,
                    opportunity['symbol'],
                    timeframe=self.strategy.timeframe,
                    limit=30
                )

                if df is not None and not df.empty and 'atr' in df.columns:
                    atr = df['atr'].iloc[-1]
                    if not pd.isna(atr):
                        # Determinar regime de volatilidade
                        volatility_regime = await self._run_blocking(
                            self.strategy.get_market_volatility_regime,
                            df
                        )
                        logger.info(
                            "[ATR] %s - ATR: %.4f, Regime: %s",
                            opportunity['symbol'], atr, volatility_regime
                        )
                    else:
                        logger.warning("[ATR] ATR is NaN for %s - using percentage stops", opportunity['symbol'])
                        atr = None
                else:
                    logger.warning("[ATR] No ATR data available for %s - using percentage stops", opportunity['symbol'])
            except Exception as e:
                logger.warning("[ATR] Error calculating ATR for %s: %s - using percentage stops", opportunity['symbol'], e)
                atr = None

            # Calculate position size (com ATR se disponível)
            position_params = self.risk_manager.calculate_position_size(
                balance,
                opportunity['price'],
                atr=atr,
                volatility_regime=volatility_regime
            )
            
            if not position_params:
                logger.error("Failed to calculate position size")
                await telegram_notifier.send_message_async(
                    "Nao foi possivel calcular o tamanho da posicao. Revise parametros de risco."
                )
                await self._notify_observing("Aguardando ajustes de risco para proxima oportunidade.")
                return
            
            #  MACHINE LEARNING: Ajustar Stop Loss (passa entry_price para cálculo correto)
            position_params['stop_loss'] = self.learning_system.adjust_stop_loss(
                position_params['stop_loss'],
                entry_price=opportunity['price']
            )

            # Salvaguarda: garantir SL do lado correto para BUY (spot)
            if position_params['stop_loss'] >= opportunity['price']:
                logger.warning(
                    "Stop loss ajustado ficou acima do entry (BUY). Revertendo para base calculada.")
                stop_loss_pct_decimal = self.risk_manager.stop_loss_percentage / 100
                position_params['stop_loss'] = round(
                    opportunity['price'] * (1 - stop_loss_pct_decimal), 4
                )
            
            #  MACHINE LEARNING: Ajustar Take Profit (passa entry_price para cálculo correto)
            position_params['take_profit'] = self.learning_system.adjust_take_profit(
                position_params['take_profit'],
                entry_price=opportunity['price']
            )

            # Salvaguarda TP: para BUY TP deve ficar acima do entry; para SELL, abaixo
            if position_params['take_profit'] <= opportunity['price']:
                logger.warning("Take profit ajustado ficou no lado errado. Reancorando para BUY.")
                tp_pct_decimal = self.risk_manager.take_profit_percentage / 100
                position_params['take_profit'] = round(
                    opportunity['price'] * (1 + tp_pct_decimal), 4
                )
            
            #  MACHINE LEARNING: Ajustar tamanho da posicao
            position_params['position_size_usdt'] = self.learning_system.adjust_position_size(
                position_params['position_size_usdt']
            )
            
            # Recalcular quantity com novo position size
            position_params['quantity'] = position_params['position_size_usdt'] / opportunity['price']

            # Logar risco efetivo vs alvo para auditoria
            try:
                logger.info(json.dumps({
                    "event": "position_sizing",
                    "symbol": opportunity['symbol'],
                    "side": "BUY",
                    "entry": round(opportunity['price'], 6),
                    "quantity": round(position_params.get('quantity', 0), 6),
                    "position_size_usdt": position_params.get('position_size_usdt'),
                    "stop_loss": position_params.get('stop_loss'),
                    "take_profit": position_params.get('take_profit'),
                    "risk_target": position_params.get('risk_amount_target'),
                    "risk_effective": position_params.get('risk_amount'),
                    "risk_pct_effective": position_params.get('risk_percent_effective', 0.0),
                    "max_positions": self.config.max_positions,
                }))
                self.last_risk_snapshot = {
                    "symbol": opportunity['symbol'],
                    "entry": round(opportunity['price'], 6),
                    "stop_loss": position_params.get('stop_loss'),
                    "take_profit": position_params.get('take_profit'),
                    "risk_target": position_params.get('risk_amount_target'),
                    "risk_effective": position_params.get('risk_amount'),
                    "risk_pct_effective": position_params.get('risk_percent_effective', 0.0),
                    "position_size_usdt": position_params.get('position_size_usdt'),
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                }
            except Exception:
                pass
            
            # Note: No leverage setting in Spot trading
            
            side = 'BUY' if opportunity.get('signal') == 'BUY' else 'SELL'
            if side == 'SELL':
                logger.warning("Tentativa de venda ignorada no modo Spot: %s", opportunity['symbol'])
                await self._notify_observing("Venda ignorada - aguardando oportunidade de compra.")
                return

            # Place order (apenas operacoes de compra para Spot)
            try:
                order = await self._run_blocking(
                    binance_manager.place_order,
                    opportunity['symbol'],
                    side,
                    position_params['quantity']
                )
            except BinanceTransientError as exc:
                logger.warning(
                    "Falha temporaria ao enviar ordem %s %s qty=%s: %s",
                    opportunity['symbol'],
                    side,
                    position_params['quantity'],
                    exc,
                )
                self.metrics['binance_errors'] += 1
                await telegram_notifier.send_message_async(
                    f"Falha temporaria ao executar ordem para {opportunity['symbol']}. Tentaremos novamente no proximo ciclo."
                )
                await self._notify_observing("Erro temporario na Binance - aguardando novo ciclo.")
                return
            except BinanceCriticalError as exc:
                logger.error(
                    "Erro critico ao enviar ordem %s %s qty=%s: %s",
                    opportunity['symbol'],
                    side,
                    position_params['quantity'],
                    exc,
                )
                self.metrics['binance_errors'] += 1
                await telegram_notifier.send_message_async(
                    f"Binance rejeitou ordem para {opportunity['symbol']}: {exc}"
                )
                await self._notify_observing("Ordem rejeitada pela Binance - aguardando nova configuracao.")
                return
            except Exception as exc:
                logger.error(
                    "Unexpected error placing order %s %s qty=%s: %s",
                    opportunity['symbol'],
                    side,
                    position_params['quantity'],
                    exc,
                )
                await telegram_notifier.send_message_async(
                    f"Erro inesperado ao executar ordem para {opportunity['symbol']}: {str(exc)}"
                )
                await self._notify_observing("Erro ao enviar ordem - verifique os logs.")
                return
            
            # Create position record
            position = {
                'symbol': opportunity['symbol'],
                'side': side,
                'entry_price': opportunity['price'],
                'quantity': position_params['quantity'],
                'position_size': position_params['position_size_usdt'],
                'leverage': 1,  # Spot trading = no leverage
                'stop_loss': position_params['stop_loss'],
                'take_profit': position_params['take_profit'],
                'opened_at': datetime.now(timezone.utc).isoformat(),
                'status': 'open',
                'ml_score': opportunity_score,  # Salvar score de ML
                'risk_amount': position_params.get('risk_amount'),
                'trailing': {
                    'activation_price': round(
                        opportunity['price'] * (
                            1 + position_params.get('trailing_activation', 0) / 100
                            if side == 'BUY'
                            else 1 - position_params.get('trailing_activation', 0) / 100
                        ),
                        4
                    ),
                    'step_pct': position_params.get('trailing_step', 0),
                    'active': False
                }
            }
            
            # Double-check for duplicates directly in DB before insert (race condition guard)
            existing = await self.db.positions.find_one({
                'symbol': opportunity['symbol'],
                'status': 'open'
            })
            if existing:
                logger.warning(
                    "Position already exists for %s (race condition avoided)",
                    opportunity['symbol']
                )
                await self._notify_observing(f"Posicao ja existe para {opportunity['symbol']}.")
                return
            
            # Save to database
            result = await self.db.positions.insert_one(position)
            position['_id'] = result.inserted_id
            self.positions.append(position)

            # Atualizar métricas de ordem
            self.metrics['orders_submitted'] += 1
            self.metrics['last_order_symbol'] = opportunity['symbol']
            self.metrics['last_order_timestamp'] = datetime.now(timezone.utc).isoformat()
            await self._get_account_balance(force_refresh=True)

            try:
                loop = asyncio.get_running_loop()
                self._last_observation_notice = loop.time()
            except RuntimeError:
                pass
            
            # Notify
            await telegram_notifier.notify_position_opened_async(
                opportunity['symbol'],
                side,
                opportunity['price'],
                position_params['position_size_usdt'],
                leverage=1,
                stop_loss=position_params['stop_loss'],
                take_profit=position_params['take_profit'],
                ml_score=opportunity_score
            )
            
            logger.info(
                "Opened %s position on %s with ML score %.2f",
                side, opportunity['symbol'], opportunity_score
            )
            
        except Exception as e:
            logger.error("Error opening position: %s", e)
    
    async def _try_close_position_with_retry(
        self, position: Dict, reason: str, max_attempts: int = 1
    ) -> bool:
        """Tenta fechar uma posição, retornando True se sucesso, False se falhar."""
        for attempt in range(max_attempts):
            try:
                # Get current price for proper closing
                try:
                    current_price = await self._run_blocking(
                        binance_manager.get_symbol_price,
                        position['symbol']
                    )
                except BinanceTransientError as exc:
                    logger.warning(
                        "Falha temporaria ao obter preco para %s: %s",
                        position['symbol'],
                        exc
                    )
                    current_price = position['entry_price']
                except BinanceCriticalError as exc:
                    logger.error(
                        "Erro critico ao obter preco para %s: %s",
                        position['symbol'],
                        exc
                    )
                    current_price = position['entry_price']
                
                if not current_price:
                    logger.warning(
                        "Could not get price for %s, using entry price",
                        position['symbol']
                    )
                    current_price = position['entry_price']
                
                await self._close_position(position, current_price, reason)
                await asyncio.sleep(1)  # Small delay between closes
                return True
                
            except Exception as e:
                logger.error(
                    "Error closing position %s (attempt %d/%d): %s",
                    position.get('symbol'), attempt + 1, max_attempts, e
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

            symbols = {pos['symbol'] for pos in positions_snapshot}
            price_map = await self._get_price_map(list(symbols))

            for position in positions_snapshot:
                current_price = price_map.get(position['symbol'])
                if current_price is None:
                    continue

                # Calcular lucro atual para trailing progressivo
                entry_price = position['entry_price']
                if position['side'] == 'BUY':
                    profit_pct = ((current_price - entry_price) / entry_price) * 100
                else:
                    profit_pct = ((entry_price - current_price) / entry_price) * 100

                trailing_cfg = position.get('trailing') or {}
                stop_updated = False
                step_pct = trailing_cfg.get('step_pct', 0)
                if step_pct:
                    # MELHORIA: Aplicar fator progressivo ao step
                    trail_factor = self._get_progressive_trail_factor(profit_pct)
                    adjusted_step_pct = step_pct * trail_factor
                    step_pct_dec = adjusted_step_pct / 100
                    
                    activation_price = trailing_cfg.get('activation_price')

                    if activation_price:
                        if position['side'] == 'BUY' and current_price >= activation_price:
                            trailing_cfg['active'] = True
                            new_stop = round(current_price * (1 - step_pct_dec), 4)
                            if new_stop > position['stop_loss']:
                                position['stop_loss'] = new_stop
                                trailing_cfg['activation_price'] = round(current_price * (1 + step_pct_dec), 4)
                                trailing_cfg['trail_factor'] = trail_factor  # Registrar fator usado
                                stop_updated = True
                        elif position['side'] == 'SELL' and current_price <= activation_price:
                            trailing_cfg['active'] = True
                            new_stop = round(current_price * (1 + step_pct_dec), 4)
                            if new_stop < position['stop_loss']:
                                position['stop_loss'] = new_stop
                                trailing_cfg['activation_price'] = round(current_price * (1 - step_pct_dec), 4)
                                trailing_cfg['trail_factor'] = trail_factor  # Registrar fator usado
                                stop_updated = True

                if stop_updated:
                    trailing_cfg['last_update'] = datetime.now(timezone.utc).isoformat()
                    try:
                        await self.db.positions.update_one(
                            {'_id': position['_id']},
                            {'$set': {'stop_loss': position['stop_loss'], 'trailing': trailing_cfg}}
                        )
                        logger.info(
                            "Trailing stop ajustado %s -> %.4f (profit: %.2f%%, factor: %.1f)",
                            position['symbol'],
                            position['stop_loss'],
                            profit_pct,
                            trailing_cfg.get('trail_factor', 1.0)
                        )
                    except Exception as e:
                        logger.error(f"Erro ao atualizar trailing stop no banco: {e}")
                    position['trailing'] = trailing_cfg

                # FASE 6: Verificar time stop (4h)
                max_hold_hours = int(os.getenv("RISK_MAX_HOLD_HOURS", "4"))
                if self.risk_manager.should_close_by_time(position['opened_at'], max_hold_hours=max_hold_hours):
                    logger.info(
                        "[Time Stop] Fechando %s - posição aberta há > %dh",
                        position['symbol'], max_hold_hours
                    )
                    await self._close_position(position, current_price, 'TIME_STOP')
                    continue  # Pular para próxima posição

                # Check if should close
                should_close, reason = self.risk_manager.should_close_position(
                    current_price,
                    position['entry_price'],
                    position['stop_loss'],
                    position['take_profit'],
                    position['side']
                )

                if should_close:
                    await self._close_position(position, current_price, reason)
                    
        except Exception as e:
            logger.error("Error checking positions: %s", e)
    
    async def _close_position(self, position: Dict, exit_price: float, reason: str):
        """Close a position"""
        try:
            # Place closing order
            close_side = 'SELL' if position['side'] == 'BUY' else 'BUY'
            
            logger.info(f"Fechando posicao {position['symbol']} - Motivo: {reason}")
            try:
                order = await self._run_blocking(
                    binance_manager.place_order,
                    position['symbol'],
                    close_side,
                    position['quantity']
                )
            except BinanceTransientError as exc:
                logger.warning(
                    "Falha temporaria ao fechar %s: %s",
                    position['symbol'],
                    exc
                )
                await telegram_notifier.send_message_async(
                    f"Falha temporaria ao fechar {position['symbol']}. Tentaremos novamente."
                )
                return
            except BinanceCriticalError as exc:
                logger.error(
                    "Erro critico ao fechar %s: %s",
                    position['symbol'],
                    exc
                )
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
                    position['entry_price'],
                    exit_price,
                    position['quantity'],
                    position['side'],
                    1  # Spot trading = no leverage
                )
            except Exception as e:
                logger.error(f"Erro ao calcular PnL: {e}")
                pnl_data = {'pnl': 0.0, 'roe': 0.0}
            
            # Update position
            position['exit_price'] = exit_price
            position['pnl'] = pnl_data['pnl']
            position['roe'] = pnl_data['roe']
            position['closed_at'] = datetime.now(timezone.utc).isoformat()
            position['close_reason'] = reason
            position['status'] = 'closed'
            
            # Update in database
            try:
                await self.db.positions.update_one(
                    {'_id': position['_id']},
                    {'$set': position}
                )
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
                    'STOP_LOSS': 'Stop Loss atingido',
                    'TAKE_PROFIT': 'Take Profit atingido',
                    'TIME_STOP': 'Tempo limite atingido (4h)'
                }.get(reason, reason)

                await telegram_notifier.notify_position_closed_async(
                    position['symbol'],
                    position['side'],
                    position['entry_price'],
                    exit_price,
                    pnl_data['pnl'],
                    pnl_data['roe'],
                    reason_label
                )
                logger.info("Notificacao Telegram enviada")
            except Exception as e:
                logger.error(f"Erro ao enviar notificacao Telegram: {e}")
            
            if not self.positions:
                await self._notify_observing(
                    "Sem posicoes abertas. Em observacao aguardando novo setup.",
                    force=True
                )
            
            await self._get_account_balance(force_refresh=True)
            logger.info(
                "Posicao fechada: %s %s | PnL: %.2f USDT",
                position['side'], position['symbol'], pnl_data['pnl']
            )
        
        except Exception as e:
            logger.error("ERRO CRITICO ao fechar posicao: %s", e)
            import traceback
            logger.error(traceback.format_exc())
    
    async def _refresh_positions_cache(self) -> List[Dict]:
        """Reload open positions from MongoDB so the DB stays the source of truth."""
        try:
            cursor = self.db.positions.find({'status': 'open'}).sort('opened_at', 1)
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
                await telegram_notifier.send_message_async("Nao foi possivel listar ordens abertas. Tente novamente.")
                return {
                    'status': 'retry',
                    'found_orders': 0,
                    'canceled_orders': 0,
                    'error': str(exc)
                }
            except BinanceCriticalError as exc:
                logger.error("Erro critico ao listar ordens abertas: %s", exc)
                await telegram_notifier.send_message_async(f"Erro ao consultar ordens abertas: {exc}")
                return {
                    'status': 'error',
                    'found_orders': 0,
                    'canceled_orders': 0,
                    'error': str(exc)
                }
            
            if not open_orders:
                logger.info("Nenhuma ordem aberta na Binance. Conta limpa!")
                await telegram_notifier.send_message_async("Conta limpa - Nenhuma ordem aberta")
                
                # Limpar MongoDB tambem (caso tenha lixo)
                await self.db.positions.delete_many({'status': 'open'})
                await self._refresh_positions_cache()
                return {
                    'status': 'clean',
                    'found_orders': 0,
                    'canceled_orders': 0
                }
            
            # 2. Tem ordens abertas - CANCELAR TODAS
            logger.warning("Encontradas %d ordens abertas! Cancelando...", len(open_orders))
            await telegram_notifier.send_message_async(
                f"Encontradas {len(open_orders)} ordens abertas na conta!\n"
                f"Cancelando todas antes de iniciar o bot..."
            )
            
            canceled_count = 0
            for order in open_orders:
                try:
                    symbol = order['symbol']
                    order_id = order['orderId']
                    side = order['side']
                    quantity = float(order['origQty'])
                    price = float(order.get('price', 0))
                    order_type = order['type']
                    
                    logger.info(
                        "Cancelando %s %s %s | Qty: %s | Price: $%.2f",
                        symbol, side, order_type, quantity, price
                    )
                    
                    # Cancelar ordem
                    try:
                        await self._run_blocking(
                            binance_manager.cancel_order,
                            symbol,
                            order_id
                        )
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
                        logger.error("Erro cancelando ordem %s: %s", order.get('symbol', 'UNKNOWN'), e)
                        await telegram_notifier.send_message_async(
                            f"Erro inesperado ao cancelar ordem {symbol}: {e}"
                        )
                        
                except Exception as e:
                    logger.error("Erro cancelando ordem %s: %s", order.get('symbol', 'UNKNOWN'), e)
            
            # 3. Limpar MongoDB
            await self.db.positions.delete_many({'status': 'open'})
            await self._refresh_positions_cache()
            
            logger.info("Limpeza concluida! %d/%d ordens canceladas", canceled_count, len(open_orders))
            await telegram_notifier.send_message_async(
                f"Limpeza concluida!\n"
                f"   {canceled_count} ordens canceladas\n"
                f"   Conta pronta para operar!"
            )
            
            # Pequeno delay para garantir que ordens foram processadas
            await asyncio.sleep(2)
            return {
                'status': 'cleaned',
                'found_orders': len(open_orders),
                'canceled_orders': canceled_count
            }
            
        except Exception as e:
            logger.error("Erro na limpeza de posicoes: %s", e)
            await telegram_notifier.send_message_async(f"Erro na limpeza: {str(e)}")
            return {
                'status': 'error',
                'found_orders': 0,
                'canceled_orders': 0,
                'error': str(e)
            }

    async def sync_account(self) -> Dict:
        """Public method to trigger account synchronization/cleanup"""
        result = await self._cleanup_existing_positions()
        return result or {
            'status': 'unknown',
            'found_orders': 0,
            'canceled_orders': 0
        }
    
    def _sanitize_positions(self, positions: List[Dict]) -> List[Dict]:
        """Convert MongoDB ObjectId to string for JSON serialization."""
        sanitized = []
        for pos in positions:
            clean_pos = {}
            for key, value in pos.items():
                if hasattr(value, '__str__') and type(value).__name__ == 'ObjectId':
                    clean_pos[key] = str(value)
                elif isinstance(value, dict):
                    clean_pos[key] = {k: str(v) if type(v).__name__ == 'ObjectId' else v for k, v in value.items()}
                else:
                    clean_pos[key] = value
            sanitized.append(clean_pos)
        return sanitized

    async def get_status(self) -> Dict:
        """Get bot status"""
        try:
            await self._refresh_positions_cache()
            balance = 0
            if binance_manager.client:
                cached_balance = await self._get_account_balance()
                balance = cached_balance if cached_balance is not None else 0
            
            # Sanitize positions to convert ObjectId to string
            sanitized_positions = self._sanitize_positions(self.positions)
            
            return {
                'is_running': self.is_running,
                'balance': balance,
                'open_positions': len(self.positions),
                'max_positions': self.risk_manager.max_positions,
                'positions': sanitized_positions,
                'testnet_mode': binance_manager.use_testnet
            }
        except Exception as e:
            logger.error("Error getting status: %s", e)
            return {
                'is_running': False, 
                'balance': 0,
                'testnet_mode': binance_manager.use_testnet,
                'error': str(e)
            }

    # ========== CIRCUIT BREAKER ==========
    def _record_failure(self) -> None:
        """Registra uma falha consecutiva. Abre o circuit breaker se exceder limite."""
        self._consecutive_failures += 1
        logger.warning(
            "Falha consecutiva #%d/%d registrada",
            self._consecutive_failures,
            self._max_consecutive_failures
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
            self._circuit_breaker_cooldown
        )
        # Notificar via Telegram (fire-and-forget)
        asyncio.create_task(
            telegram_notifier.send_message_async(
                f"⚠️ CIRCUIT BREAKER ATIVADO\n"
                f"Falhas consecutivas: {self._consecutive_failures}\n"
                f"Pausando operações por {self._circuit_breaker_cooldown // 60} minutos.\n"
                f"Verifique conexão com Binance."
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
            asyncio.create_task(
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
            use_position_cap=getattr(sanitized, 'risk_use_position_cap', True),
        )
        self.balance_cache_ttl = sanitized.balance_cache_ttl
        self.observation_alert_interval = sanitized.observation_alert_interval
        self.check_interval = sanitized.loop_interval_seconds
        self.use_position_cap = getattr(sanitized, 'risk_use_position_cap', True)
        self.daily_drawdown_limit_pct = getattr(sanitized, 'daily_drawdown_limit_pct', 0.0)
        self.weekly_drawdown_limit_pct = getattr(sanitized, 'weekly_drawdown_limit_pct', 0.0)
        if self.strategy:
            self.strategy.timeframe = sanitized.strategy_timeframe
            self.strategy.confirmation_timeframe = sanitized.strategy_confirmation_timeframe
            self.strategy.limit = sanitized.strategy_klines_limit
            self.strategy.set_min_signal_strength(sanitized.strategy_min_signal_strength)
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
            score = float(self.learning_system.params.get('min_confidence_score', base_strength / 100))
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
