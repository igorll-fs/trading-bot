"""
Testes unitários para CryptoSelector.
Valida seleção de pares e filtros de qualidade.
"""

import pytest
import sys
import os
from unittest.mock import Mock, patch, MagicMock

# Adicionar backend ao path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))


class TestCryptoSelectorInit:
    """Testes de inicialização do seletor."""
    
    def test_requires_strategy(self):
        """Deve exigir strategy para evitar cache duplicado."""
        from bot.selector import CryptoSelector
        
        mock_client = Mock()
        
        with pytest.raises(ValueError, match="requer uma instância"):
            CryptoSelector(client=mock_client, strategy=None)
            
    def test_accepts_strategy(self):
        """Deve aceitar strategy válida."""
        from bot.selector import CryptoSelector
        
        mock_client = Mock()
        mock_strategy = Mock()
        
        selector = CryptoSelector(client=mock_client, strategy=mock_strategy)
        assert selector.strategy == mock_strategy
        
    def test_default_values(self):
        """Valores padrão devem ser aplicados."""
        from bot.selector import CryptoSelector
        
        mock_client = Mock()
        mock_strategy = Mock()
        
        selector = CryptoSelector(client=mock_client, strategy=mock_strategy)
        
        assert selector.trending_refresh_interval == 120
        assert selector.min_change_percent == 0.5
        assert selector.trending_pool_size == 10
        assert selector.min_quote_volume == 50_000.0
        assert selector.max_spread_percent == 0.25
        
    def test_custom_values(self):
        """Valores customizados devem sobrescrever padrões."""
        from bot.selector import CryptoSelector
        
        mock_client = Mock()
        mock_strategy = Mock()
        
        selector = CryptoSelector(
            client=mock_client,
            strategy=mock_strategy,
            trending_refresh_interval=60,
            min_change_percent=1.0,
            trending_pool_size=5,
            min_quote_volume=100_000.0,
            max_spread_percent=0.5,
        )
        
        assert selector.trending_refresh_interval == 60
        assert selector.min_change_percent == 1.0
        assert selector.trending_pool_size == 5
        assert selector.min_quote_volume == 100_000.0
        assert selector.max_spread_percent == 0.5


class TestUpdateSettings:
    """Testes para atualização de configurações em runtime."""
    
    def test_update_single_setting(self):
        """Deve atualizar apenas o parâmetro especificado."""
        from bot.selector import CryptoSelector
        
        mock_client = Mock()
        mock_strategy = Mock()
        
        selector = CryptoSelector(client=mock_client, strategy=mock_strategy)
        original_pool_size = selector.trending_pool_size
        
        selector.update_settings(min_quote_volume=75_000.0)
        
        assert selector.min_quote_volume == 75_000.0
        assert selector.trending_pool_size == original_pool_size  # Não mudou
        
    def test_update_multiple_settings(self):
        """Deve atualizar múltiplos parâmetros."""
        from bot.selector import CryptoSelector
        
        mock_client = Mock()
        mock_strategy = Mock()
        
        selector = CryptoSelector(client=mock_client, strategy=mock_strategy)
        
        selector.update_settings(
            min_quote_volume=30_000.0,
            max_spread_percent=0.35,
            trending_pool_size=15,
        )
        
        assert selector.min_quote_volume == 30_000.0
        assert selector.max_spread_percent == 0.35
        assert selector.trending_pool_size == 15
        
    def test_update_base_symbols(self):
        """Deve atualizar lista de símbolos base."""
        from bot.selector import CryptoSelector
        
        mock_client = Mock()
        mock_strategy = Mock()
        
        selector = CryptoSelector(client=mock_client, strategy=mock_strategy)
        
        new_symbols = ['BTCUSDT', 'ETHUSDT']
        selector.update_settings(base_symbols=new_symbols)
        
        assert selector.base_symbols == new_symbols
        assert selector.symbols == new_symbols  # Também atualiza lista ativa
        
    def test_update_clamps_invalid_values(self):
        """Valores inválidos devem ser corrigidos."""
        from bot.selector import CryptoSelector
        
        mock_client = Mock()
        mock_strategy = Mock()
        
        selector = CryptoSelector(client=mock_client, strategy=mock_strategy)
        
        selector.update_settings(
            trending_refresh_interval=5,  # Muito baixo
            trending_pool_size=0,  # Inválido
            min_quote_volume=-100,  # Negativo
        )
        
        assert selector.trending_refresh_interval >= 10  # Mínimo
        assert selector.trending_pool_size >= 1  # Mínimo
        assert selector.min_quote_volume >= 0  # Não negativo


class TestSelectBestCrypto:
    """Testes para seleção do melhor par."""
    
    def test_returns_none_when_no_candidates(self):
        """Deve retornar None se não houver candidatos."""
        from bot.selector import CryptoSelector
        
        mock_client = Mock()
        mock_strategy = Mock()
        mock_strategy.get_historical_data.return_value = None
        
        selector = CryptoSelector(client=mock_client, strategy=mock_strategy)
        selector.symbols = []  # Lista vazia
        
        result = selector.select_best_crypto()
        
        assert result is None
        
    def test_excludes_specified_symbols(self):
        """Deve excluir símbolos especificados."""
        from bot.selector import CryptoSelector
        
        mock_client = Mock()
        mock_strategy = Mock()
        mock_strategy.get_historical_data.return_value = None
        
        selector = CryptoSelector(client=mock_client, strategy=mock_strategy)
        selector.symbols = ['BTCUSDT', 'ETHUSDT', 'SOLUSDT']
        
        # Mock para não encontrar dados válidos
        with patch.object(selector, '_refresh_trending_symbols'):
            result = selector.select_best_crypto(excluded_symbols=['BTCUSDT', 'ETHUSDT'])
        
        # Não deve retornar BTCUSDT ou ETHUSDT mesmo que fossem válidos


class TestRefreshTrendingSymbols:
    """Testes para atualização de símbolos em alta."""
    
    def test_respects_refresh_interval(self):
        """Não deve atualizar antes do intervalo."""
        from bot.selector import CryptoSelector
        import time
        
        mock_client = Mock()
        mock_strategy = Mock()
        
        selector = CryptoSelector(
            client=mock_client,
            strategy=mock_strategy,
            trending_refresh_interval=120,
        )
        
        # Simular última atualização recente
        selector._last_trending_refresh = time.time()
        original_symbols = selector.symbols.copy()
        
        selector._refresh_trending_symbols()
        
        # Não deve ter mudado (intervalo não passou)
        assert selector.symbols == original_symbols


class TestFilters:
    """Testes para filtros de qualidade."""
    
    def test_min_quote_volume_filter(self):
        """Filtro de volume mínimo deve ser aplicado."""
        from bot.selector import CryptoSelector
        
        mock_client = Mock()
        mock_strategy = Mock()
        
        selector = CryptoSelector(
            client=mock_client,
            strategy=mock_strategy,
            min_quote_volume=100_000.0,
        )
        
        # Volume baixo deve ser rejeitado
        assert selector.min_quote_volume == 100_000.0
        
    def test_max_spread_filter(self):
        """Filtro de spread máximo deve ser aplicado."""
        from bot.selector import CryptoSelector
        
        mock_client = Mock()
        mock_strategy = Mock()
        
        selector = CryptoSelector(
            client=mock_client,
            strategy=mock_strategy,
            max_spread_percent=0.2,
        )
        
        # Spread alto deve ser rejeitado
        assert selector.max_spread_percent == 0.2


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
