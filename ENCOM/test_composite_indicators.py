#!/usr/bin/env python3
"""
Test all 19 composite indicators from composite.py

Validates:
- All indicators compile with Numba
- All return numpy arrays of correct length
- No runtime errors
"""

import numpy as np
from encom.indicators import (
    choppiness_index, mcginley_dynamic, kaufman_efficiency_ratio, vertical_horizontal_filter,
    linear_regression_bands, price_oscillator, force_index, elder_force_index,
    chande_forecast_oscillator, center_of_gravity, linear_weighted_ma, variable_ma,
    triangular_ma, std_dev_channels, ease_of_movement_value,
    relative_momentum_index, qstick_indicator, volatility_ratio, market_facilitation_index
)

def generate_test_data(n=100):
    """Generate realistic OHLCV test data"""
    np.random.seed(42)

    close = 100 + np.cumsum(np.random.randn(n) * 0.5)
    open_prices = close + np.random.randn(n) * 0.3
    high = np.maximum(close, open_prices) + np.abs(np.random.randn(n) * 0.5)
    low = np.minimum(close, open_prices) - np.abs(np.random.randn(n) * 0.5)
    volume = np.abs(np.random.randn(n) * 1000000 + 5000000)

    return open_prices, high, low, close, volume

def test_indicator(name, func, *args):
    """Test a single indicator"""
    try:
        result = func(*args)

        # Handle tuple returns
        if isinstance(result, tuple):
            for i, r in enumerate(result):
                assert isinstance(r, np.ndarray), f"{name}[{i}] did not return numpy array"
                assert len(r) == 100, f"{name}[{i}] returned wrong length: {len(r)}"
        else:
            assert isinstance(result, np.ndarray), f"{name} did not return numpy array"
            assert len(result) == 100, f"{name} returned wrong length: {len(result)}"

        print(f"✅ {name}")
        return True
    except Exception as e:
        print(f"❌ {name}: {e}")
        return False

def main():
    """Test all 19 composite indicators"""
    print("Testing 19 Composite Indicators...")
    print("=" * 60)

    # Generate test data
    open_p, high, low, close, volume = generate_test_data()

    passed = 0
    total = 19

    # Test each indicator
    passed += test_indicator("choppiness_index", choppiness_index, high, low, close)
    passed += test_indicator("mcginley_dynamic", mcginley_dynamic, close)
    passed += test_indicator("kaufman_efficiency_ratio", kaufman_efficiency_ratio, close)
    passed += test_indicator("vertical_horizontal_filter", vertical_horizontal_filter, close)
    passed += test_indicator("linear_regression_bands", linear_regression_bands, close)
    passed += test_indicator("price_oscillator", price_oscillator, close)
    passed += test_indicator("force_index", force_index, close, volume)
    passed += test_indicator("elder_force_index", elder_force_index, close, volume)
    passed += test_indicator("chande_forecast_oscillator", chande_forecast_oscillator, close)
    passed += test_indicator("center_of_gravity", center_of_gravity, close)
    passed += test_indicator("linear_weighted_ma", linear_weighted_ma, close)
    passed += test_indicator("variable_ma", variable_ma, close)
    passed += test_indicator("triangular_ma", triangular_ma, close)
    passed += test_indicator("std_dev_channels", std_dev_channels, close)
    passed += test_indicator("ease_of_movement_value", ease_of_movement_value, high, low, volume)
    passed += test_indicator("relative_momentum_index", relative_momentum_index, close)
    passed += test_indicator("qstick_indicator", qstick_indicator, open_p, close)
    passed += test_indicator("volatility_ratio", volatility_ratio, high, low, close)
    passed += test_indicator("market_facilitation_index", market_facilitation_index, high, low, volume)

    print("=" * 60)
    print(f"Results: {passed}/{total} passed")

    if passed == total:
        print("\n✅ All 19 composite indicators working!")
        print(f"Total ENCOM indicators: 130 (previous) + 19 (new) = 149 indicators")
        return 0
    else:
        print(f"\n❌ {total - passed} indicators failed")
        return 1

if __name__ == "__main__":
    exit(main())
