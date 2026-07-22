"""
Testes unitários para RiskManager.
Valida cálculos críticos de position sizing, PnL e stop loss.
"""

import pytest
import sys
import os

# Adicionar backend ao path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))

from bot.risk_manager import RiskManager


class TestRiskManagerInit:
    """Testes de inicialização do RiskManager."""
    
    def test_default_values(self):
        """Valores padrão devem ser aplicados corretamente."""
        rm = RiskManager()
        assert rm.risk_percentage == 2.0
        assert rm.max_positions == 3
        assert rm.default_leverage == 1
        assert rm.stop_loss_percentage == 1.5
        assert rm.reward_ratio == 2.0
        assert rm.take_profit_percentage == 3.0  # 1.5 * 2.0
        assert rm.trailing_activation == 0.75
        assert rm.trailing_step == 0.5
    
    def test_custom_values(self):
        """Valores customizados devem sobrescrever os padrões."""
        rm = RiskManager(
            risk_percentage=3.0,
            max_positions=5,
            stop_loss_percentage=2.0,
            reward_ratio=3.0,
            trailing_activation=1.0,
            trailing_step=0.25,
        )
        assert rm.risk_percentage == 3.0
        assert rm.max_positions == 5
        assert rm.stop_loss_percentage == 2.0
        assert rm.take_profit_percentage == 6.0  # 2.0 * 3.0
        assert rm.trailing_activation == 1.0
        assert rm.trailing_step == 0.25


class TestCalculatePositionSize:
    """Testes para cálculo de tamanho de posição."""
    
    def test_basic_position_size(self):
        """Cálculo básico de position size."""
        rm = RiskManager(
            risk_percentage=2.0,
            max_positions=3,
            stop_loss_percentage=1.5,
            reward_ratio=2.0,
        )
        
        balance = 1000.0
        entry_price = 50000.0  # BTC price
        
        result = rm.calculate_position_size(balance, entry_price)
        
        assert result is not None
        assert 'quantity' in result
        assert 'position_size_usdt' in result
        assert 'stop_loss' in result
        assert 'take_profit' in result
        assert 'risk_amount' in result
        assert result['leverage'] == 1
    
    def test_position_size_respects_max_positions(self):
        """Position size não deve exceder balance / max_positions."""
        rm = RiskManager(
            risk_percentage=50.0,  # Alto risco
            max_positions=2,
            stop_loss_percentage=1.5,
        )
        
        balance = 1000.0
        entry_price = 100.0
        
        result = rm.calculate_position_size(balance, entry_price)
        
        # Deve ser limitado a 500 (1000 / 2)
        assert result['position_size_usdt'] <= 500.0
    
    def test_stop_loss_calculation(self):
        """Stop loss deve estar no preço correto."""
        rm = RiskManager(stop_loss_percentage=2.0)
        
        balance = 1000.0
        entry_price = 100.0
        
        result = rm.calculate_position_size(balance, entry_price)
        
        # Stop loss = 100 * (1 - 0.02) = 98
        assert result['stop_loss'] == 98.0
    
    def test_take_profit_calculation(self):
        """Take profit deve estar no preço correto."""
        rm = RiskManager(
            stop_loss_percentage=2.0,
            reward_ratio=2.0,  # TP = 4%
        )
        
        balance = 1000.0
        entry_price = 100.0
        
        result = rm.calculate_position_size(balance, entry_price)
        
        # Take profit = 100 * (1 + 0.04) = 104
        assert result['take_profit'] == 104.0
    
    def test_quantity_calculation(self):
        """Quantity deve ser position_size / entry_price."""
        rm = RiskManager(
            risk_percentage=10.0,
            max_positions=1,
            stop_loss_percentage=10.0,  # Para simplificar
        )
        
        balance = 1000.0
        entry_price = 100.0
        
        result = rm.calculate_position_size(balance, entry_price)
        
        expected_quantity = result['position_size_usdt'] / entry_price
        assert abs(result['quantity'] - expected_quantity) < 0.000001
    
    def test_trailing_params_included(self):
        """Parâmetros de trailing devem estar no resultado."""
        rm = RiskManager(
            trailing_activation=1.5,
            trailing_step=0.3,
        )
        
        result = rm.calculate_position_size(1000.0, 100.0)
        
        assert result['trailing_activation'] == 1.5
        assert result['trailing_step'] == 0.3
    
    def test_zero_balance_handling(self):
        """Balance zero deve retornar position size zero."""
        rm = RiskManager()
        
        result = rm.calculate_position_size(0.0, 100.0)
        
        assert result is not None
        assert result['position_size_usdt'] == 0.0
        assert result['quantity'] == 0.0

    def test_risk_effective_matches_target_when_possible(self):
        """Risco efetivo deve ficar próximo do alvo quando sem limite de posição."""
        rm = RiskManager(
            risk_percentage=2.0,
            max_positions=1,
            stop_loss_percentage=5.0,
            use_position_cap=False,
        )

        balance = 5000.0
        entry_price = 100.0

        result = rm.calculate_position_size(balance, entry_price)

        assert result is not None
        assert pytest.approx(result['risk_amount_target'], rel=1e-3) == 100.0
        assert pytest.approx(result['risk_amount'], rel=1e-3) == 100.0
        assert pytest.approx(result['risk_percent_effective'], rel=1e-3) == rm.risk_percentage

    def test_stop_loss_take_profit_on_correct_side(self):
        """SL deve ficar abaixo do entry e TP acima (lado BUY)."""
        rm = RiskManager(stop_loss_percentage=2.5, reward_ratio=2.0)

        entry_price = 50.0
        result = rm.calculate_position_size(2000.0, entry_price)

        assert result['stop_loss'] < entry_price
        assert result['take_profit'] > entry_price


class TestCalculatePnL:
    """Testes para cálculo de PnL."""
    
    def test_buy_profit(self):
        """PnL positivo em operação BUY com preço subindo."""
        rm = RiskManager()
        
        result = rm.calculate_pnl(
            entry_price=100.0,
            exit_price=110.0,
            quantity=1.0,
            side='BUY',
        )
        
        assert result is not None
        assert result['pnl'] == 10.0
        assert result['roe'] == 10.0  # 10% de retorno
        assert result['price_diff'] == 10.0
        assert result['price_diff_percentage'] == 10.0
    
    def test_buy_loss(self):
        """PnL negativo em operação BUY com preço caindo."""
        rm = RiskManager()
        
        result = rm.calculate_pnl(
            entry_price=100.0,
            exit_price=95.0,
            quantity=1.0,
            side='BUY',
        )
        
        assert result['pnl'] == -5.0
        assert result['roe'] == -5.0
        assert result['price_diff'] == -5.0
    
    def test_sell_profit(self):
        """PnL positivo em operação SELL com preço caindo."""
        rm = RiskManager()
        
        result = rm.calculate_pnl(
            entry_price=100.0,
            exit_price=90.0,
            quantity=1.0,
            side='SELL',
        )
        
        assert result['pnl'] == 10.0
        assert result['roe'] == 10.0
    
    def test_sell_loss(self):
        """PnL negativo em operação SELL com preço subindo."""
        rm = RiskManager()
        
        result = rm.calculate_pnl(
            entry_price=100.0,
            exit_price=105.0,
            quantity=1.0,
            side='SELL',
        )
        
        assert result['pnl'] == -5.0
        assert result['roe'] == -5.0
    
    def test_pnl_with_quantity(self):
        """PnL deve escalar com quantity."""
        rm = RiskManager()
        
        result = rm.calculate_pnl(
            entry_price=100.0,
            exit_price=110.0,
            quantity=5.0,
            side='BUY',
        )
        
        # PnL = (110 - 100) * 5 = 50
        assert result['pnl'] == 50.0
        # ROE ainda é 10% (baseado no preço, não na quantity)
        assert result['roe'] == 10.0
    
    def test_pnl_breakeven(self):
        """PnL zero quando entry == exit."""
        rm = RiskManager()
        
        result = rm.calculate_pnl(
            entry_price=100.0,
            exit_price=100.0,
            quantity=1.0,
            side='BUY',
        )
        
        assert result['pnl'] == 0.0
        assert result['roe'] == 0.0


class TestShouldClosePosition:
    """Testes para verificação de fechamento de posição."""
    
    def test_buy_stop_loss_hit(self):
        """BUY deve fechar quando preço <= stop loss."""
        rm = RiskManager()
        
        should_close, reason = rm.should_close_position(
            current_price=95.0,
            entry_price=100.0,
            stop_loss=96.0,
            take_profit=110.0,
            side='BUY',
        )
        
        assert should_close is True
        assert reason == 'STOP_LOSS'
    
    def test_buy_take_profit_hit(self):
        """BUY deve fechar quando preço >= take profit."""
        rm = RiskManager()
        
        should_close, reason = rm.should_close_position(
            current_price=111.0,
            entry_price=100.0,
            stop_loss=96.0,
            take_profit=110.0,
            side='BUY',
        )
        
        assert should_close is True
        assert reason == 'TAKE_PROFIT'
    
    def test_buy_hold(self):
        """BUY deve manter quando preço entre SL e TP."""
        rm = RiskManager()
        
        should_close, reason = rm.should_close_position(
            current_price=105.0,
            entry_price=100.0,
            stop_loss=96.0,
            take_profit=110.0,
            side='BUY',
        )
        
        assert should_close is False
        assert reason is None
    
    def test_sell_stop_loss_hit(self):
        """SELL deve fechar quando preço >= stop loss."""
        rm = RiskManager()
        
        should_close, reason = rm.should_close_position(
            current_price=105.0,
            entry_price=100.0,
            stop_loss=104.0,
            take_profit=90.0,
            side='SELL',
        )
        
        assert should_close is True
        assert reason == 'STOP_LOSS'
    
    def test_sell_take_profit_hit(self):
        """SELL deve fechar quando preço <= take profit."""
        rm = RiskManager()
        
        should_close, reason = rm.should_close_position(
            current_price=89.0,
            entry_price=100.0,
            stop_loss=104.0,
            take_profit=90.0,
            side='SELL',
        )
        
        assert should_close is True
        assert reason == 'TAKE_PROFIT'
    
    def test_sell_hold(self):
        """SELL deve manter quando preço entre TP e SL."""
        rm = RiskManager()
        
        should_close, reason = rm.should_close_position(
            current_price=95.0,
            entry_price=100.0,
            stop_loss=104.0,
            take_profit=90.0,
            side='SELL',
        )
        
        assert should_close is False
        assert reason is None
    
    def test_exact_stop_loss_buy(self):
        """BUY deve fechar quando preço == stop loss."""
        rm = RiskManager()
        
        should_close, reason = rm.should_close_position(
            current_price=96.0,
            entry_price=100.0,
            stop_loss=96.0,
            take_profit=110.0,
            side='BUY',
        )
        
        assert should_close is True
        assert reason == 'STOP_LOSS'
    
    def test_exact_take_profit_buy(self):
        """BUY deve fechar quando preço == take profit."""
        rm = RiskManager()
        
        should_close, reason = rm.should_close_position(
            current_price=110.0,
            entry_price=100.0,
            stop_loss=96.0,
            take_profit=110.0,
            side='BUY',
        )
        
        assert should_close is True
        assert reason == 'TAKE_PROFIT'


class TestEdgeCases:
    """Testes para casos extremos."""
    
    def test_very_small_balance(self):
        """Deve funcionar com balance muito pequeno."""
        rm = RiskManager()
        
        result = rm.calculate_position_size(1.0, 50000.0)
        
        assert result is not None
        assert result['quantity'] >= 0
    
    def test_very_high_price(self):
        """Deve funcionar com preços muito altos."""
        rm = RiskManager()
        
        result = rm.calculate_position_size(10000.0, 1000000.0)
        
        assert result is not None
        assert result['quantity'] > 0
    
    def test_fractional_quantity(self):
        """Quantity deve suportar frações."""
        rm = RiskManager()
        
        result = rm.calculate_position_size(100.0, 50000.0)
        
        assert result is not None
        assert result['quantity'] < 1.0
        assert result['quantity'] > 0


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
