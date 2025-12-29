"""Testes simples para notificação de fechamento e cálculo de PnL."""

from bot.telegram_client import telegram_notifier
from bot.risk_manager import RiskManager


def test_notify_position_closed() -> None:
    """Valida chamadas de notificação com diferentes cenários."""

    print('=== Teste: notify_position_closed ===')

    samples = [
        dict(symbol='BTCUSDT', side='BUY', entry_price=50_000.0, exit_price=51_000.0, pnl=100.5, roe=5.25),
        dict(symbol='ETHUSDT', side='SELL', entry_price=None, exit_price=None, pnl=None, roe=None),
        dict(symbol='ADAUSDT', side='BUY', entry_price=0.45678912, exit_price=0.45678913, pnl=-1500.75, roe=-15.85),
    ]

    for idx, payload in enumerate(samples, start=1):
        try:
            ok = telegram_notifier.notify_position_closed(**payload)
            status = 'enviado' if ok else 'Telegram não configurado'
            print(f"  Caso {idx}: {status}")
        except Exception as exc:
            print(f"  Caso {idx}: erro inesperado -> {exc}")


def test_pnl_calculation() -> None:
    """Executa cálculos básicos de PnL para LONG/SHORT."""

    print('\n=== Teste: RiskManager.calculate_pnl ===')
    risk_manager = RiskManager()

    try:
        long_result = risk_manager.calculate_pnl(
            entry_price=50_000.0,
            exit_price=51_000.0,
            quantity=0.1,
            side='BUY',
            leverage=10,
        )
        print(f"  LONG lucro: {long_result}")
    except Exception as exc:
        print(f"  LONG erro: {exc}")

    try:
        short_result = risk_manager.calculate_pnl(
            entry_price=50_000.0,
            exit_price=51_000.0,
            quantity=0.1,
            side='SELL',
            leverage=10,
        )
        print(f"  SHORT prejuizo: {short_result}")
    except Exception as exc:
        print(f"  SHORT erro: {exc}")


if __name__ == '__main__':
    test_notify_position_closed()
    test_pnl_calculation()

