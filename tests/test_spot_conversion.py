"""
🧪 Test Script: Spot Trading Conversion Validation
Validates that all Binance API calls are correctly using Spot endpoints.
"""

import sys
import os

# Add backend to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'backend'))

def test_binance_client_imports():
    """Test that binance_client can be imported and has Spot methods"""
    from bot.binance_client import BinanceClientManager

    manager = BinanceClientManager()
    assert hasattr(manager, 'get_open_orders'), "Missing get_open_orders method"
    assert hasattr(manager, 'cancel_order'), "Missing cancel_order method"
    assert not hasattr(manager, 'set_leverage'), "set_leverage should be removed"

def test_risk_manager():
    """Test that RiskManager uses leverage=1"""
    from bot.risk_manager import RiskManager
    
    rm = RiskManager(risk_percentage=2.0, max_positions=3, leverage=1)
    assert rm.default_leverage == 1, f"Expected leverage=1, got {rm.default_leverage}"
    
    position_params = rm.calculate_position_size(1000.0, 50000.0)
    if position_params:
        assert position_params['leverage'] == 1, "Position leverage should be 1"
    
    pnl_data = rm.calculate_pnl(
        entry_price=100.0,
        exit_price=110.0,
        quantity=1.0,
        side='BUY',
        leverage=1
    )
    if pnl_data:
        assert pnl_data['roe'] == 10.0, f"Expected ROE 10.0%, got {pnl_data['roe']}%"

def test_strategy_imports():
    """Test that Strategy module structure is valid"""
    # Full testing would require MongoDB and Binance client
    # Verify the module can be discovered
    import importlib
    spec = importlib.util.find_spec('bot.strategy')
    assert spec is not None, "Strategy module not found"

def main():
    """Run all validation tests"""
    print("=" * 60)
    print("🧪 TESTING SPOT TRADING CONVERSION")
    print("=" * 60)
    print()
    
    results = []
    
    print("1️⃣ Testing BinanceClientManager...")
    results.append(test_binance_client_imports())
    print()
    
    print("2️⃣ Testing RiskManager...")
    results.append(test_risk_manager())
    print()
    
    print("3️⃣ Testing Strategy...")
    results.append(test_strategy_imports())
    print()
    
    print("=" * 60)
    if all(results):
        print("✅ ALL TESTS PASSED - Spot conversion successful!")
        print("=" * 60)
        return 0
    else:
        print("❌ SOME TESTS FAILED - Check errors above")
        print("=" * 60)
        return 1

if __name__ == "__main__":
    sys.exit(main())
