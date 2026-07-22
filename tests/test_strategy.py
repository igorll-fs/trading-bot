"""
Testes unitários para TradingStrategy.
Valida cálculo de indicadores e geração de sinais.
"""

import pytest
import sys
import os
import pandas as pd
import numpy as np
from unittest.mock import Mock, patch, MagicMock

# Adicionar backend ao path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))


class TestTradingStrategyInit:
    """Testes de inicialização da estratégia."""
    
    def test_default_values(self):
        """Valores padrão devem ser aplicados."""
        from bot.strategy import TradingStrategy
        
        mock_client = Mock()
        strategy = TradingStrategy(client=mock_client)
        
        assert strategy.timeframe == '15m'
        assert strategy.confirmation_timeframe == '1h'
        assert strategy.limit == 200
        assert strategy.min_signal_strength == 60
        
    def test_custom_values(self):
        """Valores customizados devem sobrescrever padrões."""
        from bot.strategy import TradingStrategy
        
        mock_client = Mock()
        strategy = TradingStrategy(
            client=mock_client,
            min_signal_strength=70,
            timeframe='1h',
            confirmation_timeframe='4h',
            limit=100,
        )
        
        assert strategy.timeframe == '1h'
        assert strategy.confirmation_timeframe == '4h'
        assert strategy.limit == 100
        assert strategy.min_signal_strength == 70
        
    def test_min_signal_strength_clamped(self):
        """Signal strength deve ser clamped entre 0 e 100."""
        from bot.strategy import TradingStrategy
        
        mock_client = Mock()
        
        # Valor acima de 100
        strategy = TradingStrategy(client=mock_client, min_signal_strength=150)
        assert strategy.min_signal_strength == 100
        
        # Valor abaixo de 0
        strategy2 = TradingStrategy(client=mock_client, min_signal_strength=-10)
        assert strategy2.min_signal_strength == 0


class TestCalculateIndicators:
    """Testes para cálculo de indicadores técnicos."""
    
    def _create_sample_df(self, rows=100):
        """Cria DataFrame de exemplo com OHLCV."""
        np.random.seed(42)
        close = 100 + np.cumsum(np.random.randn(rows) * 0.5)
        high = close + np.abs(np.random.randn(rows) * 0.3)
        low = close - np.abs(np.random.randn(rows) * 0.3)
        
        return pd.DataFrame({
            'open': close - np.random.randn(rows) * 0.1,
            'high': high,
            'low': low,
            'close': close,
            'volume': np.random.randint(1000, 10000, rows).astype(float),
        })
    
    def test_calculate_indicators_adds_columns(self):
        """Indicadores devem ser adicionados ao DataFrame."""
        from bot.strategy import TradingStrategy
        
        mock_client = Mock()
        strategy = TradingStrategy(client=mock_client)
        
        df = self._create_sample_df(100)
        result = strategy.calculate_indicators(df)
        
        # Verificar indicadores principais
        assert 'ema_fast' in result.columns
        assert 'ema_slow' in result.columns
        assert 'rsi' in result.columns
        assert 'macd' in result.columns
        assert 'atr' in result.columns
        assert 'vwap' in result.columns
        
    def test_calculate_indicators_insufficient_data(self):
        """Com dados insuficientes, deve retornar DF sem erro."""
        from bot.strategy import TradingStrategy
        
        mock_client = Mock()
        strategy = TradingStrategy(client=mock_client)
        
        df = self._create_sample_df(10)  # Muito pouco
        result = strategy.calculate_indicators(df)
        
        # Não deve crashar, deve retornar o DF (talvez sem alguns indicadores)
        assert result is not None
        assert len(result) == 10
        
    def test_calculate_indicators_idempotent(self):
        """Chamar múltiplas vezes não deve duplicar colunas."""
        from bot.strategy import TradingStrategy
        
        mock_client = Mock()
        strategy = TradingStrategy(client=mock_client)
        
        df = self._create_sample_df(100)
        result1 = strategy.calculate_indicators(df)
        result2 = strategy.calculate_indicators(result1)
        
        # Colunas devem ser as mesmas
        assert list(result1.columns) == list(result2.columns)


class TestGenerateSignal:
    """Testes para geração de sinais de trading."""
    
    def _create_bullish_df(self):
        """Cria DataFrame com tendência de alta."""
        rows = 100
        close = np.linspace(100, 120, rows)  # Tendência de alta
        high = close + 0.5
        low = close - 0.5
        
        df = pd.DataFrame({
            'open': close - 0.1,
            'high': high,
            'low': low,
            'close': close,
            'volume': np.full(rows, 5000.0),
        })
        
        # Adicionar indicadores manualmente para teste controlado
        df['ema_fast'] = close
        df['ema_slow'] = close - 1  # Fast > Slow = bullish
        df['ema_50'] = close - 2
        df['ema_200'] = close - 5
        df['rsi'] = np.full(rows, 55.0)  # Não sobrecomprado
        df['macd'] = np.full(rows, 0.5)
        df['macd_signal'] = np.full(rows, 0.3)  # MACD > Signal = bullish
        df['macd_hist'] = np.full(rows, 0.2)
        df['atr'] = np.full(rows, 1.0)
        df['obv'] = np.linspace(1000, 2000, rows)  # OBV crescente
        df['momentum'] = np.full(rows, 1.0)
        df['vwap'] = close - 0.5  # Price > VWAP
        df['bb_upper'] = close + 2
        df['bb_middle'] = close
        df['bb_lower'] = close - 2
        
        return df
        
    def test_generate_signal_returns_dict(self):
        """Sinal deve retornar dicionário com signal e strength."""
        from bot.strategy import TradingStrategy
        
        mock_client = Mock()
        strategy = TradingStrategy(client=mock_client)
        
        df = self._create_bullish_df()
        result = strategy.generate_signal(df)
        
        assert isinstance(result, dict)
        assert 'signal' in result
        assert 'strength' in result
        
    def test_generate_signal_empty_df(self):
        """Com DataFrame vazio, deve retornar HOLD."""
        from bot.strategy import TradingStrategy
        
        mock_client = Mock()
        strategy = TradingStrategy(client=mock_client)
        
        df = pd.DataFrame()
        result = strategy.generate_signal(df)
        
        assert result['signal'] == 'HOLD'
        assert result['strength'] == 0
        
    def test_generate_signal_single_row(self):
        """Com apenas uma linha, deve retornar HOLD."""
        from bot.strategy import TradingStrategy
        
        mock_client = Mock()
        strategy = TradingStrategy(client=mock_client)
        
        df = pd.DataFrame({'close': [100.0], 'high': [101.0], 'low': [99.0], 'volume': [1000.0]})
        result = strategy.generate_signal(df)
        
        assert result['signal'] == 'HOLD'


class TestSetMinSignalStrength:
    """Testes para atualização dinâmica do threshold."""
    
    def test_set_valid_strength(self):
        """Deve aceitar valores válidos."""
        from bot.strategy import TradingStrategy
        
        mock_client = Mock()
        strategy = TradingStrategy(client=mock_client, min_signal_strength=50)
        
        strategy.set_min_signal_strength(75)
        assert strategy.min_signal_strength == 75
        
    def test_set_strength_clamped_high(self):
        """Valores acima de 100 devem ser clamped."""
        from bot.strategy import TradingStrategy
        
        mock_client = Mock()
        strategy = TradingStrategy(client=mock_client)
        
        strategy.set_min_signal_strength(200)
        assert strategy.min_signal_strength == 100
        
    def test_set_strength_clamped_low(self):
        """Valores abaixo de 0 devem ser clamped."""
        from bot.strategy import TradingStrategy
        
        mock_client = Mock()
        strategy = TradingStrategy(client=mock_client)
        
        strategy.set_min_signal_strength(-50)
        assert strategy.min_signal_strength == 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
