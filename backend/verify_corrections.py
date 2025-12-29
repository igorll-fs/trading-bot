"""
Script para verificar se as correções foram aplicadas corretamente.
"""
import sys
from bot.config import BotConfig

def verify_corrections():
    """Verifica se os parâmetros foram ajustados conforme esperado."""
    print("\n🔍 VERIFICAÇÃO DAS CORREÇÕES APLICADAS\n")
    
    config = BotConfig()
    
    checks = []
    
    # CONFIG.PY - Verificar parâmetros padrão
    print("📋 CONFIG.PY:")
    checks.append(("max_positions", config.max_positions, 2, "✅" if config.max_positions == 2 else "❌"))
    checks.append(("risk_percentage", config.risk_percentage, 1.5, "✅" if config.risk_percentage == 1.5 else "❌"))
    checks.append(("strategy_min_signal_strength", config.strategy_min_signal_strength, 80, "✅" if config.strategy_min_signal_strength == 80 else "❌"))
    checks.append(("selector_min_change_percent", config.selector_min_change_percent, 1.0, "✅" if config.selector_min_change_percent == 1.0 else "❌"))
    checks.append(("selector_min_quote_volume", config.selector_min_quote_volume, 100_000.0, "✅" if config.selector_min_quote_volume == 100_000.0 else "❌"))
    checks.append(("risk_stop_loss_percentage", config.risk_stop_loss_percentage, 1.2, "✅" if config.risk_stop_loss_percentage == 1.2 else "❌"))
    checks.append(("risk_reward_ratio", config.risk_reward_ratio, 2.5, "✅" if config.risk_reward_ratio == 2.5 else "❌"))
    
    for param, atual, esperado, status in checks:
        print(f"  {status} {param}: {atual} (esperado: {esperado})")
    
    # Verificar código-fonte dos outros arquivos
    print("\n📋 STRATEGY.PY:")
    with open('bot/strategy.py', 'r', encoding='utf-8') as f:
        strategy_content = f.read()
    
    strategy_checks = [
        ("activation_threshold = 9.0", "activation_threshold = 9.0" in strategy_content),
        ("min_strength 80", "max(self.min_signal_strength, 80)" in strategy_content),
        ("higher_adx > 30", "higher_adx > 30" in strategy_content),
        ("volume_delta >= 0.20", "volume_delta >= 0.20" in strategy_content),
        ("buy_vol_pct > 0.58", "buy_vol_pct > 0.58" in strategy_content),
        ("ADX < 25 block", "current_adx < 25" in strategy_content and "BLOQUEANDO trades" in strategy_content),
    ]
    
    for check_name, result in strategy_checks:
        status = "✅" if result else "❌"
        print(f"  {status} {check_name}")
    
    print("\n📋 RISK_MANAGER.PY:")
    with open('bot/risk_manager.py', 'r', encoding='utf-8') as f:
        risk_content = f.read()
    
    risk_checks = [
        ("sl_mult = 2.5 (high)", "sl_mult = 2.5" in risk_content),
        ("sl_mult = 2.0 (normal)", "sl_mult = 2.0" in risk_content),
        ("sl_mult = 1.8 (low)", "sl_mult = 1.8" in risk_content),
        ("risk_reward < 2.5", "risk_reward < 2.5" in risk_content),
    ]
    
    for check_name, result in risk_checks:
        status = "✅" if result else "❌"
        print(f"  {status} {check_name}")
    
    # Resumo
    total_checks = len(checks) + len(strategy_checks) + len(risk_checks)
    passed_checks = sum(1 for _, _, _, s in checks if s == "✅")
    passed_checks += sum(1 for _, r in strategy_checks if r)
    passed_checks += sum(1 for _, r in risk_checks if r)
    
    print(f"\n{'='*60}")
    print(f"RESULTADO: {passed_checks}/{total_checks} verificações passaram")
    
    if passed_checks == total_checks:
        print("\n🎉 TODAS AS CORREÇÕES APLICADAS COM SUCESSO!")
        print("\n⚠️  PRÓXIMOS PASSOS:")
        print("1. Editar backend/.env:")
        print("   BINANCE_TESTNET=true")
        print("2. Reiniciar o bot: .\\scripts\\stop.bat && .\\scripts\\start.bat")
        print("3. Monitorar por 5-7 dias no testnet")
        print("4. Verificar métricas:")
        print("   - Profit Factor > 1.5")
        print("   - Win Rate > 50%")
        print("   - Máx 5 trades/dia")
        print("   - Perda máx por trade < 50 USDT")
        return 0
    else:
        print("\n❌ ALGUMAS VERIFICAÇÕES FALHARAM - Revisar correções!")
        return 1

if __name__ == "__main__":
    sys.exit(verify_corrections())
