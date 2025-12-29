import logging
import time
from typing import List, Dict, Optional, Tuple

import pandas as pd

from bot.market_cache import get_stats_cache, get_price_cache
from bot.config import DEFAULT_SELECTOR_BASE_SYMBOLS

logger = logging.getLogger(__name__)

class CryptoSelector:
    """Intelligent cryptocurrency selector"""
    
    def __init__(
        self,
        client,
        strategy,
        *,
        base_symbols: Optional[List[str]] = None,
        trending_refresh_interval: int = 120,
        min_change_percent: float = 1.0,  # Increased for momentum focus
        trending_pool_size: int = 10,
        min_quote_volume: float = 50_000.0,
        max_spread_percent: float = 0.25,
    ):
        """
        Initialize CryptoSelector
        
        Args:
            client: Binance client
            strategy: TradingStrategy instance (OBRIGATÓRIO para evitar cache duplicado)
        
        Raises:
            ValueError: Se strategy não for fornecido
        """
        if strategy is None:
            raise ValueError(
                "CryptoSelector requer uma instância de TradingStrategy. "
                "Injete a strategy existente para evitar cache duplicado."
            )
        self.client = client
        self._stats_cache = get_stats_cache()
        self._price_cache = get_price_cache()
        self.strategy = strategy

        # Base universe (alta liquidez)
        self.base_symbols = list(base_symbols or DEFAULT_SELECTOR_BASE_SYMBOLS)

        # Runtime state for trending filtering
        self.symbols = list(self.base_symbols)
        self._trending_cache: Dict[str, Tuple[float, float]] = {}
        self.trending_refresh_interval = trending_refresh_interval  # seconds
        self.min_change_percent = min_change_percent  # focus em ativos em alta
        self.trending_pool_size = trending_pool_size
        self._last_trending_refresh = 0.0
        self.min_quote_volume = float(min_quote_volume)
        self.max_spread_percent = float(max_spread_percent)

    def _refresh_trending_symbols(self):
        """Atualiza lista de simbolos priorizando quem esta em alta."""
        now = time.time()
        if (now - self._last_trending_refresh) < self.trending_refresh_interval:
            return

        try:
            tickers = self._stats_cache.get_or_set('ticker_24h_snapshot', self.client.get_ticker)
            if not tickers:
                raise ValueError("ticker snapshot vazio")
            snapshot: Dict[str, Tuple[float, float]] = {}

            for ticker in tickers:
                symbol = ticker.get('symbol')
                if symbol not in self.base_symbols:
                    continue
                try:
                    change = float(ticker.get('priceChangePercent', 0.0))
                    quote_volume = float(ticker.get('quoteVolume', 0.0))
                except (TypeError, ValueError):
                    continue

                if change < self.min_change_percent:
                    continue

                snapshot[symbol] = (change, quote_volume)

            if snapshot:
                # Ordena por variacao positiva, depois volume
                ordered = sorted(
                    snapshot.items(),
                    key=lambda item: (item[1][0], item[1][1]),
                    reverse=True
                )
                selected = [symbol for symbol, _ in ordered[: self.trending_pool_size]]
                self.symbols = selected or list(self.base_symbols)
                self._trending_cache = snapshot
                logger.info(
                    "Atualizando lista de pares em alta: %s",
                    ", ".join(self.symbols)
                )
            else:
                # fallback para base case
                self.symbols = list(self.base_symbols)
                self._trending_cache = {}
                logger.info(
                    "Nenhum ativo acima de %.2f%%, usando lista base",
                    self.min_change_percent
                )

        except Exception as e:
            logger.error(f"Erro ao atualizar ativos em alta: {e}")
            self.symbols = list(self.base_symbols)
            self._trending_cache = {}

        self._last_trending_refresh = now
    
    def update_settings(
        self,
        *,
        base_symbols: Optional[List[str]] = None,
        trending_refresh_interval: Optional[int] = None,
        min_change_percent: Optional[float] = None,
        trending_pool_size: Optional[int] = None,
        min_quote_volume: Optional[float] = None,
        max_spread_percent: Optional[float] = None,
    ):
        """Atualiza parâmetros do seletor em tempo de execução."""
        if base_symbols:
            self.base_symbols = list(base_symbols)
            self.symbols = list(self.base_symbols)
        if trending_refresh_interval is not None:
            self.trending_refresh_interval = max(10, int(trending_refresh_interval))
        if min_change_percent is not None:
            self.min_change_percent = float(min_change_percent)
        if trending_pool_size is not None:
            self.trending_pool_size = max(1, int(trending_pool_size))
        if min_quote_volume is not None:
            self.min_quote_volume = max(0.0, float(min_quote_volume))
        if max_spread_percent is not None:
            self.max_spread_percent = max(0.0, float(max_spread_percent))
    
    def select_best_crypto(self, excluded_symbols: List[str] = None) -> Optional[Dict]:
        """Select the best cryptocurrency to trade"""
        try:
            if excluded_symbols is None:
                excluded_symbols = []
            
            self._refresh_trending_symbols()
            candidates = []
            
            for symbol in self.symbols:
                if symbol in excluded_symbols:
                    continue

                if not self._passes_liquidity_filters(symbol):
                    logger.info("%s filtrado por spread/volume insuficiente", symbol)
                    continue
                
                analysis = self.strategy.analyze_symbol(symbol)
                if analysis and analysis['signal'] != 'HOLD':
                    # MELHORIA: Usar unified_score se disponível, senão calcular legado
                    if 'unified_score' in analysis:
                        score = analysis['unified_score']
                        logger.info(
                            "%s: Signal=%s, UnifiedScore=%d (%s), Divergence=%s",
                            symbol, analysis['signal'], score,
                            analysis.get('signal_quality', 'unknown'),
                            analysis.get('divergence', 'none')
                        )
                    else:
                        # Fallback para cálculo legado
                        score = self._calculate_score(analysis)
                        logger.info(f"{symbol}: Signal={analysis['signal']}, Score={score:.2f}")
                    
                    analysis['score'] = score
                    trending_info = self._trending_cache.get(symbol)
                    if trending_info:
                        analysis['price_change_percent'] = trending_info[0]
                        analysis['quote_volume'] = trending_info[1]
                        # Bonus adicional para ativos em forte alta
                        analysis['score'] += min(trending_info[0], 5)  # cap bonus
                    candidates.append(analysis)
            
            if not candidates:
                logger.info("No trading opportunities found")
                return None
            
            # Sort by score and return best
            candidates.sort(key=lambda x: x['score'], reverse=True)
            best = candidates[0]
            
            logger.info(f"Best opportunity: {best['symbol']} with score {best['score']:.2f}")
            return best
            
        except Exception as e:
            logger.error("Error selecting crypto: %s", e)
            return None
    
    def _calculate_score(self, analysis: Dict) -> float:
        """Calculate opportunity score"""
        score = 0.0
        
        # Signal strength (max 40 points)
        score += analysis['strength'] * 0.4
        
        # Volume ratio (max 30 points)
        volume_score = min(analysis['volume_ratio'] * 15, 30)
        score += volume_score
        
        # Volatility (optimal range: 0.5-2.0) (max 30 points)
        volatility = analysis['volatility']
        if 0.5 <= volatility <= 2.0:
            volatility_score = 30
        elif volatility < 0.5:
            volatility_score = volatility * 60
        else:
            volatility_score = max(30 - (volatility - 2) * 10, 0)
        score += volatility_score
        
        return score

    def _passes_liquidity_filters(self, symbol: str) -> bool:
        """Filtra pares com spread alto ou volume baixo no timeframe configurado.
        
        MELHORIA: Filtro dinâmico que ajusta limites baseado na volatilidade do mercado.
        Em alta volatilidade, permite spreads maiores (mercado mais volátil = spreads maiores).
        """
        try:
            # MELHORIA: Detectar regime de mercado para ajustar filtros
            regime = self.strategy.detect_market_regime()
            volatility_multiplier = 1.0
            
            if regime.get('regime') == 'volatile':
                volatility_multiplier = 1.5  # Permite spreads 50% maiores em mercado volátil
            elif regime.get('regime') == 'trending':
                volatility_multiplier = 1.2  # Permite spreads 20% maiores em tendência
            
            adjusted_max_spread = self.max_spread_percent * volatility_multiplier
            adjusted_min_volume = self.min_quote_volume * (1 / volatility_multiplier)  # Volume menor aceito
            
            # Spread via book ticker
            ticker = self._price_cache.get_or_set(
                f"book_ticker_{symbol}",
                lambda: self.client.get_orderbook_ticker(symbol=symbol),
            )
            if ticker:
                bid = float(ticker.get('bidPrice', 0))
                ask = float(ticker.get('askPrice', 0))
                if bid > 0 and ask > 0:
                    mid = (bid + ask) / 2
                    spread_pct = ((ask - bid) / mid) * 100
                    if spread_pct > adjusted_max_spread:
                        logger.info(
                            "%s rejeitado: spread %.3f%% acima do limite %.3f%% (ajustado de %.3f%%)",
                            symbol,
                            spread_pct,
                            adjusted_max_spread,
                            self.max_spread_percent,
                        )
                        return False

            # Volume no timeframe configurado (quote volume)
            df = self.strategy.get_historical_data(symbol, timeframe=self.strategy.timeframe, limit=30)
            if df is None or df.empty:
                return False

            # quote_volume já vem como string; garantir numérico
            try:
                quote_volume = pd.to_numeric(df['quote_volume']).tail(8).sum()
            except Exception:
                quote_volume = 0

            if quote_volume < adjusted_min_volume:
                logger.info(
                    "%s rejeitado: volume %.0f < minimo %.0f (timeframe %s)",
                    symbol,
                    quote_volume,
                    adjusted_min_volume,
                    self.strategy.timeframe,
                )
                return False
            
            # MELHORIA: Verificar correlação com BTC se for alt
            if 'BTC' not in symbol:
                btc_correlation = self.strategy.calculate_btc_correlation(symbol)
                regime_data = self.strategy.detect_market_regime(symbol='BTCUSDT')
                
                # Se BTC está bearish e alta correlação, penalizar (mas não rejeitar)
                if btc_correlation > 0.7 and regime_data.get('regime') == 'trending':
                    # Analisar direção do BTC
                    btc_df = self.strategy.get_historical_data('BTCUSDT', limit=20)
                    if btc_df is not None:
                        btc_trend = btc_df['close'].iloc[-1] < btc_df['close'].iloc[-5]  # Caindo
                        if btc_trend:
                            logger.info(
                                "%s: Alta correlação BTC (%.2f) e BTC caindo - cuidado",
                                symbol, btc_correlation
                            )
                            # Não rejeita, mas o score será penalizado

            return True
        except Exception as exc:
            logger.warning("Falha ao aplicar filtro de liquidez em %s: %s", symbol, exc)
            return False