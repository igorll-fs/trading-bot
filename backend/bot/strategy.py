import pandas as pd
import numpy as np
from binance.client import Client
import talib
import logging
from typing import Dict, Optional
from bot.market_cache import get_cache

logger = logging.getLogger(__name__)

class TradingStrategy:
    """Multi-timeframe trading strategy combining trend, momentum, and volume intelligence"""
    
    def __init__(
        self,
        client: Client,
        min_signal_strength: int = 60,
        timeframe: str = '15m',
        confirmation_timeframe: str = '1h',
        limit: int = 200,
    ):
        self.client = client
        self.timeframe = timeframe or '15m'
        self.confirmation_timeframe = confirmation_timeframe or '1h'
        self.limit = max(10, int(limit or 200))
        self.cache = get_cache()  # Cache com TTL de 5 segundos
        self.min_signal_strength = max(0, min(100, int(min_signal_strength)))

    def set_min_signal_strength(self, strength: float) -> None:
        """Atualiza o threshold mínimo (0-100) para aceitar um sinal."""
        self.min_signal_strength = max(0, min(100, int(strength)))
        
    def get_historical_data(self, symbol: str, timeframe: Optional[str] = None,
                            limit: Optional[int] = None) -> Optional[pd.DataFrame]:
        """Get historical klines data with cache support for multiple timeframes"""
        try:
            timeframe = timeframe or self.timeframe
            limit = limit or self.limit
            cache_key = f"klines_{symbol}_{timeframe}_{limit}"
            cached_data = self.cache.get(cache_key)
            
            if cached_data is not None:
                logger.debug("Cache HIT para %s", symbol)
                return cached_data
            
            # Cache miss - buscar da API
            logger.debug("Cache MISS para %s - buscando da API", symbol)
            klines = self.client.get_klines(
                symbol=symbol,
                interval=timeframe,
                limit=limit
            )
            
            df = pd.DataFrame(klines, columns=[
                'timestamp', 'open', 'high', 'low', 'close', 'volume',
                'close_time', 'quote_volume', 'trades', 'taker_buy_base',
                'taker_buy_quote', 'ignore'
            ])
            
            df['close'] = pd.to_numeric(df['close'])
            df['high'] = pd.to_numeric(df['high'])
            df['low'] = pd.to_numeric(df['low'])
            df['volume'] = pd.to_numeric(df['volume'])
            
            # Armazenar no cache (TTL: 5 segundos)
            self.cache.set(cache_key, df)
            
            return df
            
        except Exception as e:
            logger.error("Error getting historical data for %s: %s", symbol, e)
            return None
    
    def calculate_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        """Calculate technical indicators (idempotente).
        
        Retorna o DataFrame com indicadores calculados.
        Em caso de dados insuficientes para algum indicador,
        loga warning específico e continua com os demais.
        """
        try:
            required_cols = [
                'ema_fast', 'ema_slow', 'ema_50', 'ema_200',
                'rsi', 'macd', 'macd_signal', 'macd_hist',
                'bb_upper', 'bb_middle', 'bb_lower',
                'atr', 'obv', 'momentum', 'vwap'
            ]
            if all(col in df.columns for col in required_cols):
                return df
            
            # Verificar dados mínimos
            data_len = len(df)
            if data_len < 26:  # Mínimo para EMA slow
                logger.warning(
                    "Dados insuficientes para calcular indicadores: %d linhas (minimo 26)",
                    data_len
                )
                return df

            close = df['close'].values
            high = df['high'].values
            low = df['low'].values
            
            # EMAs
            try:
                df['ema_fast'] = talib.EMA(close, timeperiod=12)
                df['ema_slow'] = talib.EMA(close, timeperiod=26)
                df['ema_50'] = talib.EMA(close, timeperiod=50) if data_len >= 50 else np.nan
                df['ema_200'] = talib.EMA(close, timeperiod=200) if data_len >= 200 else np.nan
            except Exception as e:
                logger.warning("Erro ao calcular EMAs: %s", e)
            
            # RSI
            try:
                df['rsi'] = talib.RSI(close, timeperiod=14)
            except Exception as e:
                logger.warning("Erro ao calcular RSI: %s", e)
                df['rsi'] = np.nan
            
            # MACD
            try:
                macd, signal, hist = talib.MACD(close, fastperiod=12, slowperiod=26, signalperiod=9)
                df['macd'] = macd
                df['macd_signal'] = signal
                df['macd_hist'] = hist
            except Exception as e:
                logger.warning("Erro ao calcular MACD: %s", e)
                df['macd'] = df['macd_signal'] = df['macd_hist'] = np.nan
            
            # Bollinger Bands
            try:
                upper, middle, lower = talib.BBANDS(close, timeperiod=20)
                df['bb_upper'] = upper
                df['bb_middle'] = middle
                df['bb_lower'] = lower
            except Exception as e:
                logger.warning("Erro ao calcular Bollinger Bands: %s", e)
                df['bb_upper'] = df['bb_middle'] = df['bb_lower'] = np.nan
            
            # Volatility and volume-derived metrics
            try:
                df['atr'] = talib.ATR(high, low, close, timeperiod=14)
            except Exception as e:
                logger.warning("Erro ao calcular ATR: %s", e)
                df['atr'] = np.nan

            # ADX for trend strength
            try:
                df['adx'] = talib.ADX(high, low, close, timeperiod=14)
            except Exception as e:
                logger.warning("Erro ao calcular ADX: %s", e)
                df['adx'] = np.nan

            try:
                df['obv'] = talib.OBV(close, df['volume'].values)
            except Exception as e:
                logger.warning("Erro ao calcular OBV: %s", e)
                df['obv'] = np.nan
                
            try:
                df['momentum'] = talib.MOM(close, timeperiod=10)
            except Exception as e:
                logger.warning("Erro ao calcular Momentum: %s", e)
                df['momentum'] = np.nan
            
            # MELHORIA: Calcular % de volume de compradores (taker buy)
            try:
                if 'taker_buy_quote' in df.columns and 'quote_volume' in df.columns:
                    taker_buy = pd.to_numeric(df['taker_buy_quote'], errors='coerce')
                    quote_vol = pd.to_numeric(df['quote_volume'], errors='coerce').replace(0, np.nan)
                    df['buy_volume_pct'] = (taker_buy / quote_vol).fillna(0.5)
                    df['buy_volume_ma'] = df['buy_volume_pct'].rolling(10).mean()
                else:
                    df['buy_volume_pct'] = 0.5
                    df['buy_volume_ma'] = 0.5
            except Exception as e:
                logger.warning("Erro ao calcular buy volume pct: %s", e)
                df['buy_volume_pct'] = 0.5
                df['buy_volume_ma'] = 0.5
            
            # VWAP (não usa TA-Lib)
            typical_price = (df['high'] + df['low'] + df['close']) / 3
            cumulative_volume = df['volume'].cumsum()
            cumulative_price_volume = (typical_price * df['volume']).cumsum()
            df['vwap'] = (cumulative_price_volume / cumulative_volume.replace(0, np.nan)).ffill()
            
            return df
            
        except Exception as e:
            logger.error("Error calculating indicators: %s", e)
            return df
    
    def calculate_btc_correlation(self, symbol: str, lookback: int = 30) -> float:
        """
        Calcula correlação do ativo com BTC.
        Alta correlação + BTC bearish = evitar longs em alts.
        
        Returns:
            Correlação de -1 a 1 (>0.7 é alta correlação)
        """
        try:
            if 'BTC' in symbol:
                return 1.0
            
            symbol_df = self.get_historical_data(symbol, limit=lookback)
            btc_df = self.get_historical_data('BTCUSDT', limit=lookback)
            
            if symbol_df is None or btc_df is None or len(symbol_df) < 10 or len(btc_df) < 10:
                return 0.5  # Default neutro
            
            # Calcular returns
            symbol_returns = symbol_df['close'].pct_change().dropna()
            btc_returns = btc_df['close'].pct_change().dropna()
            
            # Alinhar tamanhos
            min_len = min(len(symbol_returns), len(btc_returns))
            symbol_returns = symbol_returns.tail(min_len)
            btc_returns = btc_returns.tail(min_len)
            
            correlation = symbol_returns.corr(btc_returns)
            
            return float(correlation) if not pd.isna(correlation) else 0.5

        except Exception as e:
            logger.warning("Erro ao calcular correlação BTC para %s: %s", symbol, e)
            return 0.5

    def detect_market_regime(self, df: pd.DataFrame = None, symbol: str = 'BTCUSDT') -> Dict:
        """
        Detecta regime atual do mercado.
        
        Returns:
            Dict com regime e recomendação:
            - 'trending': ADX > 25, bom para entries
            - 'ranging': ADX < 20 e baixa volatilidade, evitar entries
            - 'volatile': Alta volatilidade, aumentar SL
        """
        try:
            if df is None:
                df = self.get_historical_data(symbol, limit=50)
            
            if df is None or len(df) < 30:
                return {'regime': 'unknown', 'can_trade': True}
            
            df = self.calculate_indicators(df)
            
            # ADX para força da tendência
            adx = talib.ADX(df['high'].values, df['low'].values, df['close'].values, timeperiod=14)
            current_adx = float(adx[-1]) if not np.isnan(adx[-1]) else 20
            
            # ATR ratio para volatilidade
            atr = df['atr'].iloc[-1] if 'atr' in df.columns else 0
            atr_ma = df['atr'].rolling(20).mean().iloc[-1] if 'atr' in df.columns else atr
            volatility_ratio = atr / atr_ma if atr_ma > 0 else 1.0
            
            # Determinar regime
            if current_adx > 25:
                regime = 'trending'
                can_trade = True
                recommendation = 'Bom momento para seguir tendência'
            elif volatility_ratio > 1.5:
                regime = 'volatile'
                can_trade = True
                recommendation = 'Usar stops mais largos'
            elif current_adx < 20 and volatility_ratio < 0.8:
                regime = 'ranging'
                can_trade = False
                recommendation = 'Evitar novas entradas - consolidação'
            else:
                regime = 'neutral'
                can_trade = True
                recommendation = 'Aguardar confirmação mais forte'
            
            return {
                'regime': regime,
                'adx': round(current_adx, 1),
                'volatility_ratio': round(volatility_ratio, 2),
                'can_trade': can_trade,
                'recommendation': recommendation
            }
            
        except Exception as e:
            logger.warning("Erro ao detectar regime: %s", e)
            return {'regime': 'unknown', 'can_trade': True}
    
    def detect_rsi_divergence(self, df: pd.DataFrame, lookback: int = 14) -> str:
        """
        Detecta divergência entre RSI e preço.
        
        Divergência Bullish: Preço faz lower low, RSI faz higher low
        Divergência Bearish: Preço faz higher high, RSI faz lower high
        
        Args:
            df: DataFrame com colunas 'close', 'low', 'high', 'rsi'
            lookback: Número de períodos para analisar
            
        Returns:
            'bullish', 'bearish' ou 'none'
        """
        try:
            if len(df) < lookback or 'rsi' not in df.columns:
                return 'none'
            
            recent = df.tail(lookback).copy()
            
            # Encontrar mínimos e máximos locais (últimos 2 pivots)
            lows = recent['low'].values
            highs = recent['high'].values
            rsi = recent['rsi'].values
            
            # Divergência Bullish: preço em queda (lower lows), RSI subindo (higher lows)
            # Comparar primeira metade com segunda metade
            mid = lookback // 2
            first_half_low = lows[:mid].min()
            second_half_low = lows[mid:].min()
            first_half_rsi_at_low = rsi[np.argmin(lows[:mid])]
            second_half_rsi_at_low = rsi[mid + np.argmin(lows[mid:])]
            
            # Preço faz lower low, mas RSI faz higher low = BULLISH
            if second_half_low < first_half_low * 0.998:  # Tolerância 0.2%
                if second_half_rsi_at_low > first_half_rsi_at_low * 1.02:  # RSI 2% maior
                    logger.debug(
                        "Divergência BULLISH detectada: preço %.4f->%.4f, RSI %.1f->%.1f",
                        first_half_low, second_half_low,
                        first_half_rsi_at_low, second_half_rsi_at_low
                    )
                    return 'bullish'
            
            # Divergência Bearish: preço em alta (higher highs), RSI caindo (lower highs)
            first_half_high = highs[:mid].max()
            second_half_high = highs[mid:].max()
            first_half_rsi_at_high = rsi[np.argmax(highs[:mid])]
            second_half_rsi_at_high = rsi[mid + np.argmax(highs[mid:])]
            
            # Preço faz higher high, mas RSI faz lower high = BEARISH
            if second_half_high > first_half_high * 1.002:  # Tolerância 0.2%
                if second_half_rsi_at_high < first_half_rsi_at_high * 0.98:  # RSI 2% menor
                    logger.debug(
                        "Divergência BEARISH detectada: preço %.4f->%.4f, RSI %.1f->%.1f",
                        first_half_high, second_half_high,
                        first_half_rsi_at_high, second_half_rsi_at_high
                    )
                    return 'bearish'
            
            return 'none'
            
        except Exception as e:
            logger.warning("Erro ao detectar divergência RSI: %s", e)
            return 'none'
    
    def calculate_unified_score(self, df: pd.DataFrame, higher_df: pd.DataFrame = None,
                                volume_ratio: float = 1.0, signal: str = 'HOLD') -> Dict:
        """
        Calcula score unificado de 0-100 com pesos configuráveis.
        
        Este método centraliza toda a lógica de pontuação que antes estava
        fragmentada em strategy.py, selector.py e learning_system.py.
        
        Componentes do score (total = 100):
        - EMA Cross/Trend: 20 pontos
        - Higher TF Confirmation: 15 pontos
        - MACD Momentum: 10 pontos
        - RSI Position + Divergence: 15 pontos
        - Volume (ratio + direction): 20 pontos
        - VWAP Position: 10 pontos
        - Bollinger Position: 10 pontos
        
        Returns:
            Dict com 'score' (0-100), 'components' (breakdown), 'signal_quality'
        """
        try:
            if len(df) < 2:
                return {'score': 0, 'components': {}, 'signal_quality': 'poor'}
            
            latest = df.iloc[-1]
            prev = df.iloc[-2]
            components = {}
            total_score = 0
            
            # 1. EMA Cross/Trend (20 pontos)
            ema_score = 0
            if 'ema_fast' in latest and 'ema_slow' in latest:
                # Cross recente
                if not pd.isna(latest['ema_fast']) and not pd.isna(prev.get('ema_fast')):
                    if latest['ema_fast'] > latest['ema_slow']:
                        if prev['ema_fast'] <= prev['ema_slow']:  # Cross recente
                            ema_score += 12 if signal == 'BUY' else 0
                        else:
                            ema_score += 8 if signal == 'BUY' else 0
                    elif latest['ema_fast'] < latest['ema_slow']:
                        if prev['ema_fast'] >= prev['ema_slow']:  # Cross recente
                            ema_score += 12 if signal == 'SELL' else 0
                        else:
                            ema_score += 8 if signal == 'SELL' else 0
                
                # EMA 50 > 200 trend
                if 'ema_50' in latest and 'ema_200' in latest:
                    if not pd.isna(latest['ema_50']) and not pd.isna(latest['ema_200']):
                        if latest['ema_50'] > latest['ema_200'] and signal == 'BUY':
                            ema_score += 8
                        elif latest['ema_50'] < latest['ema_200'] and signal == 'SELL':
                            ema_score += 8
            
            components['ema'] = min(ema_score, 20)
            total_score += components['ema']
            
            # 2. Higher TF Confirmation (15 pontos)
            htf_score = 0
            if higher_df is not None and len(higher_df) >= 2:
                h_latest = higher_df.iloc[-1]
                if 'ema_50' in h_latest and 'ema_200' in h_latest:
                    if not pd.isna(h_latest['ema_50']) and not pd.isna(h_latest['ema_200']):
                        if h_latest['ema_50'] > h_latest['ema_200'] and signal == 'BUY':
                            htf_score = 15
                        elif h_latest['ema_50'] < h_latest['ema_200'] and signal == 'SELL':
                            htf_score = 15
                        elif h_latest['ema_50'] > h_latest['ema_200'] and signal == 'SELL':
                            htf_score = -5  # Penalidade: contra tendência maior
                        elif h_latest['ema_50'] < h_latest['ema_200'] and signal == 'BUY':
                            htf_score = -5
            components['higher_tf'] = max(0, htf_score)
            total_score += components['higher_tf']
            
            # 3. MACD Momentum (10 pontos)
            macd_score = 0
            if 'macd_hist' in latest and not pd.isna(latest['macd_hist']):
                hist = latest['macd_hist']
                prev_hist = prev.get('macd_hist', 0)
                if signal == 'BUY':
                    if hist > 0 and hist > prev_hist:
                        macd_score = 10
                    elif hist > 0:
                        macd_score = 6
                    elif hist < 0 and hist > prev_hist:  # Virando
                        macd_score = 4
                elif signal == 'SELL':
                    if hist < 0 and hist < prev_hist:
                        macd_score = 10
                    elif hist < 0:
                        macd_score = 6
                    elif hist > 0 and hist < prev_hist:  # Virando
                        macd_score = 4
            components['macd'] = macd_score
            total_score += macd_score
            
            # 4. RSI + Divergência (15 pontos)
            rsi_score = 0
            rsi = latest.get('rsi', 50)
            if not pd.isna(rsi):
                if signal == 'BUY':
                    if 30 <= rsi <= 45:  # Zona ideal para compra
                        rsi_score = 10
                    elif 45 < rsi <= 55:  # Neutro
                        rsi_score = 6
                    elif rsi < 30:  # Sobrevendido (pode reverter)
                        rsi_score = 8
                elif signal == 'SELL':
                    if 55 <= rsi <= 70:  # Zona ideal para venda
                        rsi_score = 10
                    elif 45 <= rsi < 55:  # Neutro
                        rsi_score = 6
                    elif rsi > 70:  # Sobrecomprado
                        rsi_score = 8
            
            # Bonus por divergência
            divergence = self.detect_rsi_divergence(df)
            if divergence == 'bullish' and signal == 'BUY':
                rsi_score += 5
            elif divergence == 'bearish' and signal == 'SELL':
                rsi_score += 5
            elif divergence == 'bullish' and signal == 'SELL':
                rsi_score -= 3  # Contra divergência
            elif divergence == 'bearish' and signal == 'BUY':
                rsi_score -= 3
            
            components['rsi'] = max(0, min(rsi_score, 15))
            total_score += components['rsi']
            
            # 5. Volume (ratio + direção) (20 pontos)
            volume_score = 0
            # Volume ratio
            if volume_ratio >= 1.5:
                volume_score += 10
            elif volume_ratio >= 1.2:
                volume_score += 7
            elif volume_ratio >= 1.0:
                volume_score += 4
            elif volume_ratio < 0.8:
                volume_score -= 2  # Volume baixo = penalidade
            
            # Direção do volume (taker buy %)
            buy_pct = latest.get('buy_volume_pct', 0.5)
            if not pd.isna(buy_pct):
                if signal == 'BUY':
                    if buy_pct > 0.55:
                        volume_score += 10
                    elif buy_pct > 0.50:
                        volume_score += 5
                    elif buy_pct < 0.45:
                        volume_score -= 5  # Vendedores dominando
                elif signal == 'SELL':
                    if buy_pct < 0.45:
                        volume_score += 10
                    elif buy_pct < 0.50:
                        volume_score += 5
                    elif buy_pct > 0.55:
                        volume_score -= 5  # Compradores dominando
            
            components['volume'] = max(0, min(volume_score, 20))
            total_score += components['volume']
            
            # 6. VWAP Position (10 pontos)
            vwap_score = 0
            if 'vwap' in latest and not pd.isna(latest['vwap']):
                price = latest['close']
                vwap = latest['vwap']
                if signal == 'BUY' and price > vwap:
                    vwap_score = 10
                elif signal == 'BUY' and price > vwap * 0.995:
                    vwap_score = 5
                elif signal == 'SELL' and price < vwap:
                    vwap_score = 10
                elif signal == 'SELL' and price < vwap * 1.005:
                    vwap_score = 5
            components['vwap'] = vwap_score
            total_score += vwap_score
            
            # 7. Bollinger Position (10 pontos)
            bb_score = 0
            if 'bb_lower' in latest and 'bb_upper' in latest:
                if not pd.isna(latest['bb_lower']) and not pd.isna(latest['bb_upper']):
                    price = latest['close']
                    bb_lower = latest['bb_lower']
                    bb_upper = latest['bb_upper']
                    bb_middle = latest.get('bb_middle', (bb_lower + bb_upper) / 2)
                    
                    if signal == 'BUY':
                        if price <= bb_lower * 1.005:  # Perto do lower
                            bb_score = 10
                        elif price < bb_middle:
                            bb_score = 6
                    elif signal == 'SELL':
                        if price >= bb_upper * 0.995:  # Perto do upper
                            bb_score = 10
                        elif price > bb_middle:
                            bb_score = 6
            components['bollinger'] = bb_score
            total_score += bb_score
            
            # Determinar qualidade do sinal
            if total_score >= 70:
                quality = 'excellent'
            elif total_score >= 55:
                quality = 'good'
            elif total_score >= 40:
                quality = 'fair'
            else:
                quality = 'poor'
            
            return {
                'score': min(max(total_score, 0), 100),
                'components': components,
                'signal_quality': quality,
                'divergence': divergence if 'divergence' in dir() else 'none'
            }
            
        except Exception as e:
            logger.error("Erro ao calcular score unificado: %s", e)
            return {'score': 0, 'components': {}, 'signal_quality': 'poor'}
    
    def _get_adaptive_atr_multipliers(self, df: pd.DataFrame, current_atr: float) -> tuple:
        """
        Retorna multiplicadores ATR adaptativos baseado no regime de volatilidade.
        
        - Alta volatilidade: SL/TP mais distantes (evita stops prematuros)
        - Baixa volatilidade: SL/TP mais próximos (captura movimentos menores)
        
        Returns:
            tuple: (sl_multiplier, tp_multiplier)
        """
        try:
            if 'atr' not in df.columns or len(df) < 20:
                return 1.8, 2.2  # Default
            
            atr_ma = df['atr'].rolling(20).mean().iloc[-1]
            
            if pd.isna(atr_ma) or atr_ma == 0:
                return 1.8, 2.2  # Default
            
            volatility_ratio = current_atr / atr_ma
            
            if volatility_ratio > 1.5:
                # Alta volatilidade - dar mais espaço
                logger.debug("Volatilidade ALTA (ratio=%.2f) - usando ATR mult 2.5/3.0", volatility_ratio)
                return 2.5, 3.0
            elif volatility_ratio > 1.2:
                # Volatilidade acima da média
                logger.debug("Volatilidade MÉDIA-ALTA (ratio=%.2f) - usando ATR mult 2.0/2.5", volatility_ratio)
                return 2.0, 2.5
            elif volatility_ratio < 0.7:
                # Baixa volatilidade - apertar stops
                logger.debug("Volatilidade BAIXA (ratio=%.2f) - usando ATR mult 1.2/1.5", volatility_ratio)
                return 1.2, 1.5
            elif volatility_ratio < 0.9:
                # Volatilidade abaixo da média
                logger.debug("Volatilidade MÉDIA-BAIXA (ratio=%.2f) - usando ATR mult 1.5/1.8", volatility_ratio)
                return 1.5, 1.8
            else:
                # Volatilidade normal
                return 1.8, 2.2
                
        except Exception as e:
            logger.warning("Erro ao calcular ATR adaptativo: %s - usando default", e)
            return 1.8, 2.2

    def check_ema_stacking(self, df: pd.DataFrame, lookback: int = 3) -> bool:
        """
        Check if EMAs are properly stacked for trend continuation.
        For BUY: EMA 8 > EMA 21 > EMA 55

        Args:
            df: DataFrame with ema columns
            lookback: Number of candles to check (default 3)

        Returns:
            True if EMAs stacked correctly for last N candles
        """
        try:
            if len(df) < lookback:
                return False

            # Check if we have the required EMAs
            if not all(col in df.columns for col in ['ema_fast', 'ema_slow', 'ema_50']):
                return False

            # Check last N candles
            for i in range(-lookback, 0):
                row = df.iloc[i]
                if pd.isna(row['ema_fast']) or pd.isna(row['ema_slow']) or pd.isna(row['ema_50']):
                    return False

                # For bullish: fast > slow > 50
                if not (row['ema_fast'] > row['ema_slow'] > row['ema_50']):
                    return False

            return True

        except Exception as e:
            logger.warning(f"Error checking EMA stacking: {e}")
            return False

    def is_breaking_high(self, df: pd.DataFrame, lookback: int = 5) -> bool:
        """
        Check if current price is breaking above recent highs.
        Confirms momentum continuation.

        Args:
            df: DataFrame with 'high' column
            lookback: Number of periods to look back

        Returns:
            True if current close > highest high of last N periods
        """
        try:
            if len(df) < lookback + 1:
                return False

            current_close = df['close'].iloc[-1]
            recent_highs = df['high'].iloc[-lookback-1:-1]
            highest = recent_highs.max()

            return current_close > highest

        except Exception as e:
            logger.warning(f"Error checking breakout: {e}")
            return False

    def get_market_volatility_regime(self, df: pd.DataFrame) -> str:
        """
        Determine current volatility regime based on ATR.

        Returns:
            'low', 'normal', 'high', or 'extreme'
        """
        try:
            if 'atr' not in df.columns or len(df) < 20:
                return 'normal'

            current_atr = df['atr'].iloc[-1]
            atr_ma = df['atr'].rolling(20).mean().iloc[-1]

            if pd.isna(current_atr) or pd.isna(atr_ma) or atr_ma == 0:
                return 'normal'

            ratio = current_atr / atr_ma

            if ratio > 2.0:
                return 'extreme'
            elif ratio > 1.5:
                return 'high'
            elif ratio < 0.7:
                return 'low'
            else:
                return 'normal'

        except Exception as e:
            logger.warning(f"Error determining volatility regime: {e}")
            return 'normal'

    def generate_signal(self, df: pd.DataFrame, higher_df: Optional[pd.DataFrame] = None,
                        volume_ratio: float = 1.0) -> Dict:
        """Generate trading signal blending momentum, trend, and volume context"""
        try:
            if len(df) < 2:
                return {'signal': 'HOLD', 'strength': 0}
            
            latest = df.iloc[-1]
            prev = df.iloc[-2]

            def has_indicator(*cols, require_prev=False):
                """Check if latest (and optionally previous) rows have valid values for the given indicators."""
                for col in cols:
                    if col not in latest or pd.isna(latest[col]):
                        return False
                    if require_prev and (col not in prev or pd.isna(prev[col])):
                        return False
                return True
            atr_value = latest.get('atr', np.nan)
            if np.isnan(atr_value) or atr_value == 0:
                atr_value = latest['close'] * 0.01
            
            higher_trend = 'neutral'
            if higher_df is not None and len(higher_df) >= 2:
                higher_latest = higher_df.iloc[-1]
                ema_50 = higher_latest.get('ema_50')
                ema_200 = higher_latest.get('ema_200')
                higher_adx = higher_latest.get('adx', 0)

                if pd.notna(ema_50) and pd.notna(ema_200) and pd.notna(higher_adx):
                    # CORREÇÃO: Require ADX > 30 (era 25) for trending confirmation
                    if higher_adx > 30:
                        if ema_50 > ema_200:
                            higher_trend = 'bullish'
                        elif ema_50 < ema_200:
                            higher_trend = 'bearish'
                        logger.debug(f"Higher TF trend: {higher_trend} with ADX {higher_adx:.1f}")
                    else:
                        higher_trend = 'neutral'  # Not trending strongly enough
                        logger.debug(f"Higher TF ADX {higher_adx:.1f} < 25, market ranging")
            
            signal = 'HOLD'
            strength = 0
            buy_score = 0.0
            sell_score = 0.0
            
            if has_indicator('ema_fast', 'ema_slow', require_prev=True):
                if latest['ema_fast'] > latest['ema_slow'] and prev['ema_fast'] <= prev['ema_slow']:
                    buy_score += 2.0
                if latest['ema_fast'] < latest['ema_slow'] and prev['ema_fast'] >= prev['ema_slow']:
                    sell_score += 2.0
            
            if has_indicator('ema_50', 'ema_200'):
                if latest['ema_50'] > latest['ema_200']:
                    buy_score += 2.0
                if latest['ema_50'] < latest['ema_200']:
                    sell_score += 2.0
            
            if higher_trend == 'bullish':
                buy_score += 1.5
            elif higher_trend == 'bearish':
                sell_score += 1.5
            
            if has_indicator('macd_hist', require_prev=True):
                if latest['macd_hist'] > 0 and latest['macd_hist'] > prev['macd_hist']:
                    buy_score += 1.5
                if latest['macd_hist'] < 0 and latest['macd_hist'] < prev['macd_hist']:
                    sell_score += 1.5
            
            if has_indicator('rsi', require_prev=True):
                if latest['rsi'] > 50 and latest['rsi'] < 70 and (latest['rsi'] - prev['rsi']) > 2:
                    buy_score += 1.0
                if latest['rsi'] < 50 and latest['rsi'] > 30 and (latest['rsi'] - prev['rsi']) < -2:
                    sell_score += 1.0
            
            if has_indicator('vwap'):
                if latest['close'] > latest['vwap']:
                    buy_score += 1.0
                elif latest['close'] < latest['vwap']:
                    sell_score += 1.0
            
            volume_delta = volume_ratio - 1.0
            if volume_delta >= 0.20:  # CORREÇÃO: Volume mínimo 1.2x (era 1.05x)
                buy_score += min(volume_delta / 0.05, 1.0)
            elif volume_delta < 0.10:  # NOVO: Penalizar volume muito baixo
                buy_score -= 1.0
                logger.debug(f"Volume baixo ({volume_ratio:.2f}x) - penalidade aplicada")
            elif volume_delta <= -0.05:
                sell_score += min(abs(volume_delta) / 0.05, 1.0)
            
            # MELHORIA: Ajustar score baseado na direção do volume (quem está comprando/vendendo)
            buy_vol_pct = latest.get('buy_volume_pct', 0.5)
            if not pd.isna(buy_vol_pct):
                if buy_vol_pct > 0.58:  # CORREÇÃO: Aumentado de 55% para 58%
                    buy_score += 1.5
                    logger.debug("Volume de compra dominante (%.1f%%) - bonus para BUY", buy_vol_pct * 100)
                elif buy_vol_pct < 0.52:  # CORREÇÃO: Penalizar se não houver pressão compradora (era <0.45)
                    buy_score -= 2.0  # CORREÇÃO: Aumentado de -1.5 para -2.0
                    logger.debug("Pressão compradora fraca (%.1f%%) - penalidade aplicada", buy_vol_pct * 100)
                elif buy_vol_pct < 0.45:  # Vendedores dominando muito (<45%)
                    sell_score += 1.0
                    logger.debug("Volume de venda dominante (%.1f%%) - bonus para SELL", buy_vol_pct * 100)
            
            # MELHORIA: Divergência RSI - sinais fortes de reversão
            divergence = self.detect_rsi_divergence(df)
            if divergence == 'bullish':
                buy_score += 2.5  # Forte sinal de reversão para cima
                logger.debug("Divergência BULLISH detectada - bonus para BUY")
            elif divergence == 'bearish':
                sell_score += 2.5  # Forte sinal de reversão para baixo
                logger.debug("Divergência BEARISH detectada - bonus para SELL")

            # NOVO: Bônus para sinais de momentum forte
            # EMA stacking bonus
            if self.check_ema_stacking(df):
                buy_score += 1.5
                logger.debug("EMA stacking confirmed - bonus for BUY")

            # Breakout confirmation
            if self.is_breaking_high(df):
                buy_score += 1.0
                logger.debug("Price breaking recent highs - bonus for BUY")

            # ADX strength on current timeframe
            current_adx = latest.get('adx', 0)
            if not pd.isna(current_adx) and current_adx > 30:
                buy_score += 1.0
                logger.debug(f"Strong ADX {current_adx:.1f} - bonus for BUY")

            activation_threshold = 9.0  # CORREÇÃO: Aumentado de 7.0 para 9.0 para filtrar sinais fracos
            
            # NOVO: Bloquear trading em mercados ranging (ADX < 25)
            if not pd.isna(current_adx) and current_adx < 25:
                logger.debug(f"Mercado ranging (ADX={current_adx:.1f} < 25) - BLOQUEANDO trades")
                signal = 'HOLD'
                strength = 0
            elif buy_score >= activation_threshold and higher_trend == 'bullish':  # Must be bullish
                signal = 'BUY'
                strength = min(int(buy_score / 12 * 100), 100)  # Adjusted scale
            elif sell_score >= activation_threshold and higher_trend == 'bearish':  # Must be bearish
                signal = 'SELL'
                strength = min(int(sell_score / 10 * 100), 100)
            
            # MELHORIA: ATR adaptativo baseado no regime de volatilidade
            sl_mult, tp_mult = self._get_adaptive_atr_multipliers(df, atr_value)
            
            stop_loss = None
            take_profit = None
            risk_reward = None
            if signal == 'BUY':
                stop_loss = round(latest['close'] - sl_mult * atr_value, 6)
                take_profit = round(latest['close'] + tp_mult * atr_value, 6)
            elif signal == 'SELL':
                stop_loss = round(latest['close'] + sl_mult * atr_value, 6)
                take_profit = round(latest['close'] - tp_mult * atr_value, 6)
            
            if stop_loss is not None and take_profit is not None:
                risk = latest['close'] - stop_loss if signal == 'BUY' else stop_loss - latest['close']
                reward = take_profit - latest['close'] if signal == 'BUY' else latest['close'] - take_profit
                if risk > 0:
                    risk_reward = round(reward / risk, 2)
            
            ema_trend = 'neutral'
            if has_indicator('ema_50', 'ema_200'):
                ema_trend = 'bullish' if latest['ema_50'] > latest['ema_200'] else 'bearish'

            rsi_value = latest.get('rsi')
            if pd.isna(rsi_value):
                rsi_value = 50.0
            macd_value = latest.get('macd')
            if pd.isna(macd_value):
                macd_value = 0.0

            result = {
                'signal': signal,
                'strength': strength,
                'rsi': float(rsi_value),
                'macd': float(macd_value),
                'ema_trend': ema_trend,
                'trend_bias': higher_trend,
                'stop_loss': stop_loss,
                'take_profit': take_profit,
                'risk_reward': risk_reward,
                'atr': round(float(atr_value), 6)
            }
            min_strength_required = max(self.min_signal_strength, 80)  # CORREÇÃO: Aumentado de 75 para 80
            if result['signal'] in ('BUY', 'SELL') and result['strength'] < min_strength_required:
                logger.debug(f"Signal strength {result['strength']} < required {min_strength_required}, converting to HOLD")
                result['signal'] = 'HOLD'
                result['strength'] = 0

            return result
            
        except Exception as e:
            logger.error("Error generating signal: %s", e)
            return {'signal': 'HOLD', 'strength': 0}
    
    def analyze_symbol(self, symbol: str) -> Optional[Dict]:
        """Complete analysis of a symbol"""
        try:
            df = self.get_historical_data(symbol)
            if df is None or len(df) == 0:
                return None
            
            df = self.calculate_indicators(df)
            volume_ma = df['volume'].rolling(window=20).mean().iloc[-1]
            current_volume = df['volume'].iloc[-1]
            volume_ma_value = float(volume_ma) if not np.isnan(volume_ma) else 0.0
            volume_ratio = current_volume / volume_ma_value if volume_ma_value > 0 else 1.0
            
            higher_df = self.get_historical_data(symbol, timeframe=self.confirmation_timeframe, limit=300)
            if higher_df is not None and len(higher_df) > 0:
                higher_df = self.calculate_indicators(higher_df)
            else:
                higher_df = None
            
            signal_data = self.generate_signal(df, higher_df, volume_ratio)
            
            # MELHORIA: Calcular score unificado
            unified = self.calculate_unified_score(
                df, higher_df, volume_ratio, 
                signal_data.get('signal', 'HOLD')
            )
            
            # Calculate volatility
            returns = df['close'].pct_change()
            volatility = returns.std() * 100
            volatility = float(volatility) if not np.isnan(volatility) else 0.0
            volume_ratio = float(volume_ratio)
            
            momentum_value = df['momentum'].iloc[-1] if 'momentum' in df.columns else 0
            momentum_value = float(momentum_value) if not np.isnan(momentum_value) else 0
            
            # Detectar divergência RSI
            divergence = self.detect_rsi_divergence(df)
            
            return {
                'symbol': symbol,
                'signal': signal_data['signal'],
                'strength': signal_data['strength'],
                'unified_score': unified['score'],  # NOVO: Score unificado 0-100
                'signal_quality': unified['signal_quality'],  # NOVO: excellent/good/fair/poor
                'score_components': unified['components'],  # NOVO: Breakdown do score
                'divergence': divergence,  # NOVO: bullish/bearish/none
                'price': float(df['close'].iloc[-1]),
                'volatility': volatility,
                'volume_ratio': volume_ratio,
                'rsi': signal_data.get('rsi', 50),
                'trend': signal_data.get('ema_trend', 'neutral'),
                'trend_bias': signal_data.get('trend_bias', 'neutral'),
                'stop_loss': signal_data.get('stop_loss'),
                'take_profit': signal_data.get('take_profit'),
                'risk_reward': signal_data.get('risk_reward'),
                'atr': signal_data.get('atr'),
                'momentum': momentum_value,
                'timeframe': self.timeframe,
                'confirmation_timeframe': self.confirmation_timeframe
            }
            
        except Exception as e:
            logger.error("Error analyzing %s: %s", symbol, e)
            return None
