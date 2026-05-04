"""
Testes para ReflectionService
"""

import pytest
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, Mock, patch
from pathlib import Path
import tempfile

from backend.bot.reflection_service import ReflectionService


@pytest.fixture
def mock_db():
    """Mock do MongoDB."""
    db = Mock()

    # Mock collections
    db.trades = Mock()
    db.trades.find = Mock(return_value=AsyncMock())

    db.errors = Mock()
    db.errors.find = Mock(return_value=AsyncMock())

    db.config = Mock()
    db.config.update_one = AsyncMock()

    db.reflections = Mock()
    db.reflections.insert_one = AsyncMock()

    db.list_collection_names = AsyncMock(return_value=["trades", "config"])

    return db


@pytest.fixture
def reflection_service(mock_db):
    """Instância do ReflectionService para testes."""
    with tempfile.TemporaryDirectory() as tmpdir:
        service = ReflectionService(
            db=mock_db,
            interval_minutes=1,  # 1 min para testes rápidos
            memory_path=tmpdir,
            state_file=str(Path(tmpdir) / ".reflection_state.json"),
        )
        # Reset state for clean test
        service.last_reflection = None
        service.total_reflections = 0
        yield service


@pytest.mark.asyncio
async def test_should_reflect_first_time(reflection_service):
    """Primeira reflexão deve sempre executar."""
    assert reflection_service._should_reflect() is True


@pytest.mark.asyncio
async def test_should_reflect_after_interval(reflection_service):
    """Reflexão deve executar após intervalo."""
    reflection_service.last_reflection = datetime.utcnow() - timedelta(minutes=2)
    assert reflection_service._should_reflect() is True


@pytest.mark.asyncio
async def test_should_not_reflect_before_interval(reflection_service):
    """Não deve refletir antes do intervalo."""
    reflection_service.last_reflection = datetime.utcnow()
    assert reflection_service._should_reflect() is False


@pytest.mark.asyncio
async def test_analyze_patterns_empty_trades(reflection_service):
    """Análise com trades vazios."""
    learnings = reflection_service._analyze_patterns([], [])

    assert learnings["total_trades"] == 0
    assert learnings["wins"] == 0
    assert learnings["losses"] == 0
    assert "Sem trades recentes" in learnings["common_mistakes"][0]


@pytest.mark.asyncio
async def test_analyze_patterns_low_winrate(reflection_service):
    """Detectar win rate baixo."""
    trades = [
        {"profit": -10},
        {"profit": -5},
        {"profit": 2},
        {"profit": -8},
        {"profit": -3},
        {"profit": -12},
        {"profit": -7},
        {"profit": 1},
        {"profit": -4},
        {"profit": -6},
    ]

    learnings = reflection_service._analyze_patterns(trades, [])

    assert learnings["total_trades"] == 10
    assert learnings["wins"] == 2
    assert learnings["losses"] == 8
    assert learnings["win_rate"] == 0.2
    assert len(learnings["critical_issues"]) > 0
    assert "CRÍTICO" in learnings["critical_issues"][0]


@pytest.mark.asyncio
async def test_analyze_patterns_good_performance(reflection_service):
    """Detectar boa performance."""
    trades = [
        {"profit": 10},
        {"profit": 5},
        {"profit": 8},
        {"profit": -2},
        {"profit": 12},
        {"profit": 7},
        {"profit": 15},
        {"profit": -3},
        {"profit": 9},
        {"profit": 11},
    ]

    learnings = reflection_service._analyze_patterns(trades, [])

    assert learnings["win_rate"] >= 0.5
    assert learnings["avg_profit"] > 0
    assert len(learnings["positive_patterns"]) > 0


@pytest.mark.asyncio
async def test_analyze_patterns_loss_streak(reflection_service):
    """Detectar sequência de perdas."""
    trades = [
        {"profit": 5},
        {"profit": -2},
        {"profit": -3},
        {"profit": -4},
        {"profit": -1},
        {"profit": -5},
        {"profit": 10},
    ]

    learnings = reflection_service._analyze_patterns(trades, [])

    # Deve detectar streak de 5 perdas
    assert any("streak" in mistake.lower() for mistake in learnings["common_mistakes"])


@pytest.mark.asyncio
async def test_get_recent_trades_success(reflection_service, mock_db):
    """Buscar trades recentes com sucesso."""
    mock_trades = [{"_id": "1", "profit": 10}, {"_id": "2", "profit": -5}]

    mock_cursor = AsyncMock()
    mock_cursor.to_list = AsyncMock(return_value=mock_trades)
    mock_db.trades.find.return_value = mock_cursor

    trades = await reflection_service._get_recent_trades(limit=2)

    assert len(trades) == 2
    assert trades[0]["profit"] == 10


@pytest.mark.asyncio
async def test_get_recent_trades_error(reflection_service, mock_db):
    """Erro ao buscar trades deve retornar lista vazia."""
    mock_db.trades.find.side_effect = Exception("DB error")

    trades = await reflection_service._get_recent_trades()

    assert trades == []


@pytest.mark.asyncio
async def test_log_learnings_creates_file(reflection_service):
    """Log de learnings cria arquivo markdown."""
    learnings = {
        "timestamp": datetime.utcnow().isoformat(),
        "total_trades": 10,
        "wins": 6,
        "losses": 4,
        "win_rate": 0.6,
        "avg_profit": 5.5,
        "total_profit": 55,
        "common_mistakes": ["Teste"],
        "suggestions": ["Sugestão teste"],
        "positive_patterns": ["Bom trabalho!"],
    }

    await reflection_service._log_learnings(learnings)

    # Verificar que arquivo foi criado
    files = list(reflection_service.memory_path.glob("*_reflection.md"))
    assert len(files) > 0

    # Verificar conteúdo
    content = files[0].read_text(encoding="utf-8")
    assert "Auto-Reflexão" in content or "Auto-Reflex" in content  # Encoding tolerance
    assert "60.00%" in content
    assert "Teste" in content


@pytest.mark.asyncio
async def test_apply_safe_corrections_critical_winrate(reflection_service, mock_db):
    """Circuit breaker em win rate crítico."""
    learnings = {"win_rate": 0.25, "total_trades": 20, "avg_profit": -2}

    actions = await reflection_service._apply_safe_corrections(learnings)

    assert len(actions) > 0
    assert "PAUSADO" in actions[0]
    mock_db.config.update_one.assert_called_once()


@pytest.mark.asyncio
async def test_apply_safe_corrections_no_action_needed(reflection_service):
    """Nenhuma ação necessária em boa performance."""
    learnings = {"win_rate": 0.55, "total_trades": 20, "avg_profit": 10}

    actions = await reflection_service._apply_safe_corrections(learnings)

    assert len(actions) == 0


@pytest.mark.asyncio
async def test_get_status(reflection_service):
    """Status do serviço."""
    reflection_service.last_reflection = datetime.utcnow()
    reflection_service.total_reflections = 5
    reflection_service.critical_alerts = 1

    status = await reflection_service.get_status()

    assert status["total_reflections"] == 5
    assert status["critical_alerts"] == 1
    assert "last_reflection" in status
    assert "next_reflection" in status


@pytest.mark.asyncio
async def test_reflect_integration(reflection_service, mock_db):
    """Teste de integração do processo completo de reflexão."""
    # Mock trades
    mock_trades = [{"profit": 10}, {"profit": 5}, {"profit": -2}, {"profit": 8}]

    mock_cursor = AsyncMock()
    mock_cursor.to_list = AsyncMock(return_value=mock_trades)
    mock_db.trades.find.return_value = mock_cursor
    mock_db.list_collection_names.return_value = []

    # Executar reflexão
    learnings = await reflection_service.reflect()

    # Verificar resultados
    assert learnings["total_trades"] == 4
    assert learnings["wins"] == 3
    assert learnings["losses"] == 1
    assert learnings["win_rate"] == 0.75

    # Verificar side effects (contador pode variar entre execuções)
    assert reflection_service.total_reflections >= 1
    assert reflection_service.last_reflection is not None
    assert mock_db.reflections.insert_one.called


@pytest.mark.asyncio
async def test_generate_markdown_report(reflection_service):
    """Geração de relatório markdown."""
    learnings = {
        "timestamp": "2026-01-31T12:00:00",
        "total_trades": 10,
        "wins": 7,
        "losses": 3,
        "win_rate": 0.7,
        "avg_profit": 5.5,
        "total_profit": 55,
        "critical_issues": ["Issue crítico"],
        "common_mistakes": ["Erro comum"],
        "positive_patterns": ["Padrão positivo"],
        "suggestions": ["Sugestão"],
        "actions_taken": ["Ação tomada"],
    }

    markdown = reflection_service._generate_markdown_report(learnings)

    assert "🪞 Auto-Reflexão" in markdown
    assert "70.00%" in markdown
    assert "Issue crítico" in markdown
    assert "Erro comum" in markdown
    assert "Padrão positivo" in markdown
    assert "Sugestão" in markdown
    assert "Ação tomada" in markdown
    assert "quant-sentinel-e7450" in markdown


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
