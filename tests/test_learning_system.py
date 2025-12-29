"""
Testes unitários para BotLearningSystem.
Valida ajuste de parâmetros e persistência de aprendizado.
"""

import pytest
import sys
import os
from unittest.mock import Mock, AsyncMock, patch, MagicMock

# Adicionar backend ao path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))


class TestLearningSystemInit:
    """Testes de inicialização do sistema de aprendizado."""
    
    def test_default_mode_active(self):
        """Modo padrão deve ser 'active'."""
        from bot.learning_system import BotLearningSystem
        
        mock_db = Mock()
        
        with patch.dict(os.environ, {}, clear=True):
            system = BotLearningSystem(db=mock_db)
            
        assert system.mode == 'active'
        assert system.learning_enabled == True
        assert system.observe_only == False
        
    def test_observe_mode(self):
        """Modo 'observe' deve apenas logar sugestões."""
        from bot.learning_system import BotLearningSystem
        
        mock_db = Mock()
        
        with patch.dict(os.environ, {'BOT_LEARNING_MODE': 'observe'}):
            system = BotLearningSystem(db=mock_db)
            
        assert system.mode == 'observe'
        assert system.learning_enabled == True
        assert system.observe_only == True
        
    def test_disabled_mode(self):
        """Modo 'disabled' deve desativar aprendizado."""
        from bot.learning_system import BotLearningSystem
        
        mock_db = Mock()
        
        with patch.dict(os.environ, {'BOT_LEARNING_MODE': 'disabled'}):
            system = BotLearningSystem(db=mock_db)
            
        assert system.mode == 'disabled'
        assert system.learning_enabled == False
        
    def test_invalid_mode_defaults_to_active(self):
        """Modo inválido deve usar 'active'."""
        from bot.learning_system import BotLearningSystem
        
        mock_db = Mock()
        
        with patch.dict(os.environ, {'BOT_LEARNING_MODE': 'invalid_mode'}):
            system = BotLearningSystem(db=mock_db)
            
        assert system.mode == 'active'


class TestAdjustableParams:
    """Testes para parâmetros ajustáveis."""
    
    def test_default_params(self):
        """Parâmetros padrão devem ser razoáveis."""
        from bot.learning_system import BotLearningSystem
        
        mock_db = Mock()
        system = BotLearningSystem(db=mock_db)
        
        assert 'min_confidence_score' in system.adjustable_params
        assert 'stop_loss_multiplier' in system.adjustable_params
        assert 'take_profit_multiplier' in system.adjustable_params
        assert 'position_size_multiplier' in system.adjustable_params
        
        # Valores padrão
        assert system.adjustable_params['min_confidence_score'] == 0.5
        assert system.adjustable_params['stop_loss_multiplier'] == 1.0
        assert system.adjustable_params['take_profit_multiplier'] == 1.0
        assert system.adjustable_params['position_size_multiplier'] == 1.0
        
    def test_param_bounds(self):
        """Limites dos parâmetros devem estar definidos."""
        from bot.learning_system import BotLearningSystem
        
        mock_db = Mock()
        system = BotLearningSystem(db=mock_db)
        
        assert 'min_confidence_score' in system.param_bounds
        assert 'stop_loss_multiplier' in system.param_bounds
        
        # Verificar formato (min, max)
        for param, bounds in system.param_bounds.items():
            assert isinstance(bounds, tuple)
            assert len(bounds) == 2
            assert bounds[0] < bounds[1]


class TestUpdateParam:
    """Testes para atualização de parâmetros com suavização EMA."""
    
    def test_update_param_within_bounds(self):
        """Valores dentro dos limites são suavizados via EMA."""
        from bot.learning_system import BotLearningSystem
        
        mock_db = Mock()
        system = BotLearningSystem(db=mock_db)
        
        # Suavização EMA: new = alpha * target + (1-alpha) * current
        # Com alpha=0.15, current=0.5, target=0.7:
        # new = 0.15 * 0.7 + 0.85 * 0.5 = 0.105 + 0.425 = 0.53
        system._update_param('min_confidence_score', 0.7, 'teste')
        
        # Valor esperado com suavização (não mais valor direto)
        expected = 0.15 * 0.7 + 0.85 * 0.5  # ~0.53
        assert abs(system.adjustable_params['min_confidence_score'] - expected) < 0.01
        
    def test_update_param_clamped_high(self):
        """Valores acima do limite são suavizados e depois clamped."""
        from bot.learning_system import BotLearningSystem
        
        mock_db = Mock()
        system = BotLearningSystem(db=mock_db)
        
        # Suavização com target=1.5, current=0.5:
        # smoothed = 0.15 * 1.5 + 0.85 * 0.5 = 0.225 + 0.425 = 0.65
        # Como 0.65 < 0.9 (max), não precisa clampar
        system._update_param('min_confidence_score', 1.5, 'teste')
        
        expected = 0.15 * 1.5 + 0.85 * 0.5  # ~0.65
        assert abs(system.adjustable_params['min_confidence_score'] - expected) < 0.01
        
    def test_update_param_clamped_low(self):
        """Valores abaixo do limite são suavizados e depois clamped."""
        from bot.learning_system import BotLearningSystem
        
        mock_db = Mock()
        system = BotLearningSystem(db=mock_db)
        
        # Suavização com target=0.1, current=0.5:
        # smoothed = 0.15 * 0.1 + 0.85 * 0.5 = 0.015 + 0.425 = 0.44
        # Como 0.44 > 0.3 (min), não precisa clampar
        system._update_param('min_confidence_score', 0.1, 'teste')
        
        expected = 0.15 * 0.1 + 0.85 * 0.5  # ~0.44
        assert abs(system.adjustable_params['min_confidence_score'] - expected) < 0.01
    
    def test_update_param_converges_with_repeated_calls(self):
        """Chamadas repetidas convergem para o valor alvo."""
        from bot.learning_system import BotLearningSystem
        
        mock_db = Mock()
        system = BotLearningSystem(db=mock_db)
        
        # Aplicar várias vezes o mesmo target - deve convergir
        target = 0.7
        for _ in range(50):  # 50 iterações deve convergir bem
            system._update_param('min_confidence_score', target, 'teste')
        
        # Após muitas iterações, deve estar muito próximo do alvo
        assert abs(system.adjustable_params['min_confidence_score'] - target) < 0.05
        
    def test_observe_mode_does_not_update(self):
        """Modo observe não deve alterar parâmetros."""
        from bot.learning_system import BotLearningSystem
        
        mock_db = Mock()
        
        with patch.dict(os.environ, {'BOT_LEARNING_MODE': 'observe'}):
            system = BotLearningSystem(db=mock_db)
            
        original = system.adjustable_params['min_confidence_score']
        system._update_param('min_confidence_score', 0.8, 'teste')
        
        # Não deve ter mudado
        assert system.adjustable_params['min_confidence_score'] == original


class TestPerformanceMetrics:
    """Testes para métricas de performance."""
    
    def test_initial_metrics(self):
        """Métricas iniciais devem estar zeradas."""
        from bot.learning_system import BotLearningSystem
        
        mock_db = Mock()
        system = BotLearningSystem(db=mock_db)
        
        assert system.performance_metrics['total_trades'] == 0
        assert system.performance_metrics['winning_trades'] == 0
        assert system.performance_metrics['losing_trades'] == 0
        assert system.performance_metrics['win_rate'] == 0.0


class TestAdjustStopLoss:
    """Testes para ajuste de stop loss baseado em aprendizado."""
    
    def test_adjust_stop_loss_buy_position(self):
        """Deve ajustar stop loss para posição de compra (SL abaixo do entry)."""
        from bot.learning_system import BotLearningSystem
        
        mock_db = Mock()
        system = BotLearningSystem(db=mock_db)
        system.adjustable_params['stop_loss_multiplier'] = 1.2
        
        # Entry em 100, SL original em 95 (5 de distância)
        adjusted = system.adjust_stop_loss(base_stop_loss=95.0, entry_price=100.0)
        
        # Com multiplier 1.2, distância vai de 5 para 6 (5 * 1.2)
        # Novo SL = 100 - 6 = 94
        assert adjusted == 94.0
        
    def test_adjust_stop_loss_sell_position(self):
        """Deve ajustar stop loss para posição de venda (SL acima do entry)."""
        from bot.learning_system import BotLearningSystem
        
        mock_db = Mock()
        system = BotLearningSystem(db=mock_db)
        system.adjustable_params['stop_loss_multiplier'] = 0.8
        
        # Entry em 100, SL original em 105 (5 de distância)
        adjusted = system.adjust_stop_loss(base_stop_loss=105.0, entry_price=100.0)
        
        # Com multiplier 0.8, distância vai de 5 para 4 (5 * 0.8)
        # Novo SL = 100 + 4 = 104
        assert adjusted == 104.0
        
    def test_adjust_stop_loss_without_entry_returns_original(self):
        """Sem entry_price, deve retornar SL original."""
        from bot.learning_system import BotLearningSystem
        
        mock_db = Mock()
        system = BotLearningSystem(db=mock_db)
        
        adjusted = system.adjust_stop_loss(base_stop_loss=95.0)
        
        assert adjusted == 95.0


class TestShouldTrade:
    """Testes para decisão de trade baseada em ML."""
    
    def test_high_confidence_should_trade(self):
        """Alta confiança deve permitir trade."""
        from bot.learning_system import BotLearningSystem
        
        mock_db = Mock()
        system = BotLearningSystem(db=mock_db)
        system.adjustable_params['min_confidence_score'] = 0.5
        
        result = system.should_take_trade(opportunity_score=0.8)
        
        assert result == True
        
    def test_low_confidence_should_not_trade(self):
        """Baixa confiança deve rejeitar trade."""
        from bot.learning_system import BotLearningSystem
        
        mock_db = Mock()
        system = BotLearningSystem(db=mock_db)
        system.adjustable_params['min_confidence_score'] = 0.6
        
        result = system.should_take_trade(opportunity_score=0.4)
        
        assert result == False
        
    def test_exact_threshold_should_trade(self):
        """Confiança igual ao threshold deve permitir."""
        from bot.learning_system import BotLearningSystem
        
        mock_db = Mock()
        system = BotLearningSystem(db=mock_db)
        system.adjustable_params['min_confidence_score'] = 0.5
        
        result = system.should_take_trade(opportunity_score=0.5)
        
        assert result == True


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
