"""
🛡️ TESTES UNITÁRIOS: ML GUARDRAILS
Valida que sistema de ML nunca sugere parâmetros suicidas
"""

import pytest
from backend.bot.learning_system import BotLearningSystem
from unittest.mock import AsyncMock, MagicMock


@pytest.fixture
def learning_system():
    """Fixture: Criar learning system mockado"""
    mock_db = MagicMock()
    mock_db.learning_data = MagicMock()
    mock_db.trades = MagicMock()

    system = BotLearningSystem(mock_db)
    system.mode = "active"  # Habilitar aprendizado
    system.observe_only = False
    return system


class TestMLGuardrails:
    """Testes de Segurança para ML Guardrails"""

    # ========== TESTES: min_confidence_score ==========

    def test_confidence_score_safe_range(self, learning_system):
        """✅ Confidence score dentro do range seguro (40-70%) deve passar"""
        is_safe, msg = learning_system._validate_safety("min_confidence_score", 0.50)
        assert is_safe is True, f"0.50 deveria ser seguro, mas falhou: {msg}"

        is_safe, msg = learning_system._validate_safety("min_confidence_score", 0.40)
        assert is_safe is True, "0.40 (limite mínimo) deveria passar"

        is_safe, msg = learning_system._validate_safety("min_confidence_score", 0.70)
        assert is_safe is True, "0.70 (limite máximo) deveria passar"

    def test_confidence_score_too_low_critical(self, learning_system):
        """🚫 Confidence < 35% = ZONA DE PERIGO CRÍTICO"""
        is_safe, msg = learning_system._validate_safety("min_confidence_score", 0.20)
        assert is_safe is False, "20% confidence = suicídio, deveria bloquear!"
        assert "CRÍTICO" in msg or "danger" in msg, f"Mensagem não indica criticidade: {msg}"

    def test_confidence_score_too_low_unsafe(self, learning_system):
        """⚠️ Confidence 35-39% = UNSAFE (abaixo do mínimo seguro)"""
        is_safe, msg = learning_system._validate_safety("min_confidence_score", 0.38)
        assert is_safe is False, "38% está abaixo do safe min (40%), deveria bloquear"
        assert "UNSAFE" in msg or "safe min" in msg, f"Mensagem inadequada: {msg}"

    def test_confidence_score_too_high_paralysis(self, learning_system):
        """⚠️ Confidence > 70% = Paralisia por análise"""
        is_safe, msg = learning_system._validate_safety("min_confidence_score", 0.80)
        assert is_safe is False, "80% é paralisia (> 70% max), deveria bloquear"

    # ========== TESTES: stop_loss_multiplier ==========

    def test_stop_loss_multiplier_safe_range(self, learning_system):
        """✅ Stop Loss multiplier 0.7x-1.2x deve passar"""
        is_safe, msg = learning_system._validate_safety("stop_loss_multiplier", 1.0)
        assert is_safe is True, "1.0x SL multiplier deveria ser seguro"

        is_safe, msg = learning_system._validate_safety("stop_loss_multiplier", 0.70)
        assert is_safe is True, "0.70x (limite min) deveria passar"

        is_safe, msg = learning_system._validate_safety("stop_loss_multiplier", 1.20)
        assert is_safe is True, "1.20x (limite max) deveria passar"

    def test_stop_loss_multiplier_too_tight(self, learning_system):
        """🚫 SL multiplier < 0.7x = Stops prematuros"""
        is_safe, msg = learning_system._validate_safety("stop_loss_multiplier", 0.50)
        assert is_safe is False, "0.5x SL = stops prematuros demais, deve bloquear"

    def test_stop_loss_multiplier_too_wide_critical(self, learning_system):
        """🚫 SL multiplier > 1.5x = PERDA EXCESSIVA (> 3% no E7450)"""
        is_safe, msg = learning_system._validate_safety("stop_loss_multiplier", 1.60)
        assert is_safe is False, "1.6x SL = perda > 3%, deve bloquear IMEDIATAMENTE"
        assert "CRÍTICO" in msg or "danger" in msg, "Deveria indicar criticidade"

    def test_stop_loss_multiplier_moderate_unsafe(self, learning_system):
        """⚠️ SL multiplier 1.21-1.49x = UNSAFE (acima do max seguro)"""
        is_safe, msg = learning_system._validate_safety("stop_loss_multiplier", 1.30)
        assert is_safe is False, "1.3x SL está acima de 1.2x max, deve bloquear"

    # ========== TESTES: take_profit_multiplier ==========

    def test_take_profit_multiplier_safe_range(self, learning_system):
        """✅ TP multiplier 0.6x-1.5x deve passar"""
        is_safe, msg = learning_system._validate_safety("take_profit_multiplier", 1.0)
        assert is_safe is True, "1.0x TP deveria ser seguro"

        is_safe, msg = learning_system._validate_safety("take_profit_multiplier", 0.60)
        assert is_safe is True, "0.60x (min) deveria passar"

        is_safe, msg = learning_system._validate_safety("take_profit_multiplier", 1.50)
        assert is_safe is True, "1.50x (max) deveria passar"

    def test_take_profit_multiplier_too_close(self, learning_system):
        """🚫 TP multiplier < 0.6x = Lucros insignificantes"""
        is_safe, msg = learning_system._validate_safety("take_profit_multiplier", 0.40)
        assert is_safe is False, "0.4x TP = lucro muito baixo, deve bloquear"

    def test_take_profit_multiplier_too_far(self, learning_system):
        """🚫 TP multiplier > 1.5x = Holding excessivo"""
        is_safe, msg = learning_system._validate_safety("take_profit_multiplier", 2.0)
        assert is_safe is False, "2.0x TP = holding excessivo, deve bloquear"

    # ========== TESTES: position_size_multiplier ==========

    def test_position_size_multiplier_safe_range(self, learning_system):
        """✅ Position size 0.5x-1.3x deve passar"""
        is_safe, msg = learning_system._validate_safety("position_size_multiplier", 1.0)
        assert is_safe is True, "1.0x position size deveria ser seguro"

        is_safe, msg = learning_system._validate_safety("position_size_multiplier", 0.50)
        assert is_safe is True, "0.50x (min) deveria passar"

        is_safe, msg = learning_system._validate_safety("position_size_multiplier", 1.30)
        assert is_safe is True, "1.30x (max) deveria passar"

    def test_position_size_multiplier_too_small(self, learning_system):
        """⚠️ Position size < 0.5x = Ineficiência (mas não crítico)"""
        is_safe, msg = learning_system._validate_safety("position_size_multiplier", 0.30)
        assert is_safe is False, "0.3x position = trades ineficientes, deve bloquear"

    def test_position_size_multiplier_too_large_critical(self, learning_system):
        """🚫 Position size >= 1.80x = OVEREXPOSURE SUICIDA (danger zone)"""
        is_safe, msg = learning_system._validate_safety("position_size_multiplier", 1.80)
        assert is_safe is False, "1.8x position = overexposure suicida, deve bloquear"
        # 1.80 está exatamente no danger_max, então deve mostrar CRÍTICO
        assert "CRÍTICO" in msg or "danger" in msg.lower(), f"Deveria indicar criticidade: {msg}"

        # Testar valor acima do danger_max também
        is_safe2, msg2 = learning_system._validate_safety("position_size_multiplier", 2.00)
        assert is_safe2 is False, "2.0x = overexposure absurdo"
        assert "CRÍTICO" in msg2 or "danger" in msg2.lower(), f"2.0x deveria ser crítico: {msg2}"

    def test_position_size_multiplier_moderate_unsafe(self, learning_system):
        """⚠️ Position size 1.31-1.79x = UNSAFE (acima do seguro)"""
        is_safe, msg = learning_system._validate_safety("position_size_multiplier", 1.50)
        assert is_safe is False, "1.5x position está acima de 1.3x max, deve bloquear"

    # ========== TESTES: Integração com _update_param ==========

    def test_update_param_blocks_dangerous_value(self, learning_system):
        """🛡️ _update_param deve BLOQUEAR valores perigosos via guardrail"""
        # Tentar atualizar confidence para 20% (CRÍTICO)
        current_value = learning_system.adjustable_params["min_confidence_score"]
        result = learning_system._update_param("min_confidence_score", 0.20, "Teste suicida")

        # Valor NÃO deve mudar
        assert result == current_value, "Guardrail deveria ter bloqueado mudança perigosa!"
        assert learning_system.adjustable_params["min_confidence_score"] == current_value

    def test_update_param_allows_safe_value(self, learning_system):
        """✅ _update_param deve PERMITIR valores seguros"""
        learning_system.adjustable_params["min_confidence_score"] = 0.50
        result = learning_system._update_param("min_confidence_score", 0.55, "Ajuste seguro")

        # Valor deve ser atualizado (com suavização EMA)
        # Com smoothing_factor=0.15: new = 0.15*0.55 + 0.85*0.50 = 0.5075
        assert result != 0.50, "Valor deveria ter sido atualizado"
        assert (
            0.50 < result < 0.56
        ), f"Valor deveria estar entre 0.50-0.56 (com EMA), mas é {result}"

    def test_param_bounds_align_with_guardrails(self, learning_system):
        """🔍 param_bounds devem estar alinhados com guardrails"""
        # Verificar que os limites nos param_bounds são <= limites dos guardrails
        assert learning_system.param_bounds["min_confidence_score"][0] >= 0.40
        assert learning_system.param_bounds["min_confidence_score"][1] <= 0.70

        assert learning_system.param_bounds["stop_loss_multiplier"][0] >= 0.70
        assert learning_system.param_bounds["stop_loss_multiplier"][1] <= 1.20

        assert learning_system.param_bounds["take_profit_multiplier"][0] >= 0.60
        assert learning_system.param_bounds["take_profit_multiplier"][1] <= 1.50

        assert learning_system.param_bounds["position_size_multiplier"][0] >= 0.50
        assert learning_system.param_bounds["position_size_multiplier"][1] <= 1.30

    # ========== TESTES: Casos extremos ==========

    def test_guardrail_with_unknown_parameter(self, learning_system):
        """✅ Parâmetro não monitorado deve ser permitido"""
        is_safe, msg = learning_system._validate_safety("unknown_param", 999.0)
        assert is_safe is True, "Parâmetro desconhecido deveria ser permitido"
        assert "not monitored" in msg.lower()

    def test_guardrail_boundary_values(self, learning_system):
        """🎯 Testar valores exatamente nos limites"""
        # Exatamente no limite mínimo seguro
        is_safe, _ = learning_system._validate_safety("min_confidence_score", 0.40)
        assert is_safe is True, "Limite mínimo exato (0.40) deveria passar"

        # Exatamente no limite máximo seguro
        is_safe, _ = learning_system._validate_safety("min_confidence_score", 0.70)
        assert is_safe is True, "Limite máximo exato (0.70) deveria passar"

        # 1 decimal abaixo do mínimo seguro
        is_safe, _ = learning_system._validate_safety("min_confidence_score", 0.39)
        assert is_safe is False, "0.39 está abaixo de 0.40 min, deve bloquear"

        # 1 decimal acima do máximo seguro
        is_safe, _ = learning_system._validate_safety("min_confidence_score", 0.71)
        assert is_safe is False, "0.71 está acima de 0.70 max, deve bloquear"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
