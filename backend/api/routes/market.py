"""
API Routes para dados de mercado em tempo real
"""

from fastapi import APIRouter, HTTPException
from typing import Dict, Any
import logging

logger = logging.getLogger(__name__)


def create_market_router(db, get_bot):
    """Cria router para endpoints de mercado."""
    
    router = APIRouter(prefix="/market", tags=["market"])
    
    @router.get("/prices")
    async def get_market_prices() -> Dict[str, Any]:
        """
        Retorna preços em tempo real das moedas monitoradas.
        Usado pelo dashboard para mostrar variações.
        """
        try:
            from bot.binance_client import binance_manager
            
            # Moedas monitoradas pelo bot
            monitored_symbols = [
                'BTCUSDT', 'ETHUSDT', 'BNBUSDT', 'SOLUSDT', 'XRPUSDT',
                'DOGEUSDT', 'ADAUSDT', 'AVAXUSDT', 'LINKUSDT', 'DOTUSDT', 'LTCUSDT'
            ]
            
            prices = {}
            
            # Buscar ticker 24h para preço e variação
            tickers = binance_manager.client.get_ticker()
            
            for ticker in tickers:
                symbol = ticker.get('symbol')
                if symbol in monitored_symbols:
                    prices[symbol] = {
                        'price': float(ticker.get('lastPrice', 0)),
                        'change_24h': float(ticker.get('priceChangePercent', 0)),
                        'high_24h': float(ticker.get('highPrice', 0)),
                        'low_24h': float(ticker.get('lowPrice', 0)),
                        'volume_24h': float(ticker.get('quoteVolume', 0)),
                    }
            
            return {
                'prices': prices,
                'count': len(prices)
            }
            
        except Exception as e:
            logger.error(f"Erro ao buscar preços: {e}")
            raise HTTPException(status_code=500, detail=str(e))
    
    @router.get("/signals")
    async def get_active_signals() -> Dict[str, Any]:
        """
        Retorna sinais ativos detectados pelo bot.
        Mostra oportunidades sem entrar automaticamente.
        """
        try:
            bot = await get_bot(db)
            
            if not bot.selector or not bot.strategy:
                return {'signals': [], 'count': 0}
            
            # Símbolos já em posição
            excluded = [pos['symbol'] for pos in bot.positions]
            
            signals = []
            
            # Analisar todos os símbolos monitorados
            for symbol in bot.selector.symbols[:15]:  # Limitar a 15 para performance
                if symbol in excluded:
                    continue
                
                try:
                    analysis = bot.strategy.analyze_symbol(symbol)
                    if analysis and analysis.get('signal') != 'HOLD':
                        signals.append({
                            'symbol': symbol,
                            'signal': analysis.get('signal'),
                            'score': analysis.get('unified_score', 0),
                            'quality': analysis.get('signal_quality', 'unknown'),
                            'strength': analysis.get('strength', 0),
                            'rsi': round(analysis.get('rsi', 50), 1),
                            'trend': analysis.get('trend', 'neutral'),
                            'divergence': analysis.get('divergence', 'none'),
                            'price': analysis.get('price', 0),
                            'stop_loss': analysis.get('stop_loss'),
                            'take_profit': analysis.get('take_profit'),
                        })
                except Exception as e:
                    logger.debug(f"Erro ao analisar {symbol}: {e}")
                    continue
            
            # Ordenar por score
            signals.sort(key=lambda x: x['score'], reverse=True)
            
            return {
                'signals': signals[:10],  # Top 10 sinais
                'count': len(signals)
            }
            
        except Exception as e:
            logger.error(f"Erro ao buscar sinais: {e}")
            raise HTTPException(status_code=500, detail=str(e))
    
    @router.get("/btc-health")
    async def get_btc_health() -> Dict[str, Any]:
        """
        Retorna saúde do BTC (tendência macro).
        Usado para decidir se deve operar alts.
        """
        try:
            bot = await get_bot(db)
            
            if not bot.strategy:
                return {'healthy': True, 'trend': 'unknown', 'correlation_warning': False}
            
            # Analisar BTC
            btc_analysis = bot.strategy.analyze_symbol('BTCUSDT')
            
            if not btc_analysis:
                return {'healthy': True, 'trend': 'unknown', 'correlation_warning': False}
            
            trend = btc_analysis.get('trend', 'neutral')
            rsi = btc_analysis.get('rsi', 50)
            
            # BTC saudável se não estiver em queda forte
            healthy = not (trend == 'bearish' and rsi < 40)
            
            return {
                'healthy': healthy,
                'trend': trend,
                'rsi': round(rsi, 1),
                'price': btc_analysis.get('price', 0),
                'signal': btc_analysis.get('signal', 'HOLD'),
                'correlation_warning': not healthy
            }
            
        except Exception as e:
            logger.error(f"Erro ao verificar BTC health: {e}")
            return {'healthy': True, 'trend': 'unknown', 'correlation_warning': False}
    
    @router.get("/regime")
    async def get_market_regime() -> Dict[str, Any]:
        """
        Retorna regime atual do mercado.
        - trending: Bom para entries
        - ranging: Evitar entries
        - volatile: Cuidado com stops
        """
        try:
            bot = await get_bot(db)
            
            if not bot.strategy:
                return {'regime': 'unknown', 'description': 'Bot não inicializado'}
            
            # Analisar BTC como proxy do mercado
            df = bot.strategy.get_historical_data('BTCUSDT', limit=50)
            
            if df is None or len(df) < 30:
                return {'regime': 'unknown', 'description': 'Dados insuficientes'}
            
            df = bot.strategy.calculate_indicators(df)
            
            # Calcular ADX para força da tendência
            import talib
            adx = talib.ADX(df['high'].values, df['low'].values, df['close'].values, timeperiod=14)
            current_adx = float(adx[-1]) if not pd.isna(adx[-1]) else 20
            
            # ATR ratio para volatilidade
            atr = df['atr'].iloc[-1]
            atr_ma = df['atr'].rolling(20).mean().iloc[-1]
            volatility_ratio = atr / atr_ma if atr_ma > 0 else 1.0
            
            # Determinar regime
            if current_adx > 25:
                regime = 'trending'
                description = 'Mercado em tendência - bom para seguir momentum'
            elif volatility_ratio > 1.5:
                regime = 'volatile'
                description = 'Alta volatilidade - cuidado com stops apertados'
            elif current_adx < 20 and volatility_ratio < 0.8:
                regime = 'ranging'
                description = 'Consolidação - evitar novas entradas'
            else:
                regime = 'neutral'
                description = 'Mercado neutro - aguardar confirmação'
            
            return {
                'regime': regime,
                'description': description,
                'adx': round(current_adx, 1),
                'volatility_ratio': round(volatility_ratio, 2),
                'recommendation': 'enter' if regime == 'trending' else 'wait'
            }
            
        except Exception as e:
            logger.error(f"Erro ao detectar regime: {e}")
            return {'regime': 'unknown', 'description': str(e)}
    
    @router.get("/monitored-coins")
    async def get_monitored_coins() -> Dict[str, Any]:
        """
        Retorna lista de moedas REALMENTE monitoradas pelo bot.
        Baseado em bot.selector.symbols (dados reais).
        """
        try:
            bot = await get_bot(db)
            
            if not bot.selector:
                # Fallback: retornar símbolos padrão se bot não iniciado
                default_symbols = [
                    'BTCUSDT', 'ETHUSDT', 'BNBUSDT', 'SOLUSDT', 'XRPUSDT',
                    'DOGEUSDT', 'ADAUSDT', 'AVAXUSDT', 'LINKUSDT', 'DOTUSDT', 'LTCUSDT'
                ]
                return {
                    'coins': [
                        {
                            'symbol': symbol.replace('USDT', ''),
                            'full_symbol': symbol,
                            'name': symbol.replace('USDT', ''),
                            'enabled': True,
                            'source': 'default'
                        }
                        for symbol in default_symbols
                    ],
                    'count': len(default_symbols),
                    'source': 'default_config'
                }
            
            # Dados REAIS do selector
            coins_data = []
            for symbol in bot.selector.symbols[:20]:  # Limitar a 20 para performance
                base_symbol = symbol.replace('USDT', '')
                
                # Metadados conhecidos (opcional, mas não afeta funcionalidade)
                coin_metadata = {
                    'ETH': {'name': 'Ethereum', 'color': '#627EEA'},
                    'BNB': {'name': 'Binance Coin', 'color': '#F3BA2F'},
                    'SOL': {'name': 'Solana', 'color': '#00FFA3'},
                    'XRP': {'name': 'Ripple', 'color': '#23292F'},
                    'DOGE': {'name': 'Dogecoin', 'color': '#C2A633'},
                    'ADA': {'name': 'Cardano', 'color': '#0033AD'},
                    'AVAX': {'name': 'Avalanche', 'color': '#E84142'},
                    'LINK': {'name': 'Chainlink', 'color': '#2A5ADA'},
                    'DOT': {'name': 'Polkadot', 'color': '#E6007A'},
                    'LTC': {'name': 'Litecoin', 'color': '#BFBBBB'},
                    'BTC': {'name': 'Bitcoin', 'color': '#F7931A'},
                }.get(base_symbol, {'name': base_symbol, 'color': '#6B7280'})
                
                coins_data.append({
                    'symbol': base_symbol,
                    'full_symbol': symbol,
                    'name': coin_metadata['name'],
                    'color': coin_metadata['color'],
                    'enabled': True,
                    'source': 'selector'
                })
            
            return {
                'coins': coins_data,
                'count': len(coins_data),
                'source': 'bot_selector'
            }
            
        except Exception as e:
            logger.error(f"Erro ao buscar moedas monitoradas: {e}")
            raise HTTPException(status_code=500, detail=str(e))
    
    return router


# Import pandas for regime detection
import pandas as pd
