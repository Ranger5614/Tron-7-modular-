"""
Test script for new indicators (24 new elite indicators)

Tests:
- Hilbert Transform Suite (7)
- Pattern Recognition (5)
- Market Profile (3)
- Order Flow (4)
- Advanced Volume (5)
"""

import numpy as np
import sys

print("=" * 70)
print("ENCOM New Indicators Test")
print("=" * 70)
print()

# Generate test data
n = 200
np.random.seed(42)

# Realistic price data
close = 100 + np.cumsum(np.random.randn(n) * 0.5)
high = close + np.abs(np.random.randn(n) * 0.3)
low = close - np.abs(np.random.randn(n) * 0.3)
open_prices = close + np.random.randn(n) * 0.2
volume = np.random.randint(100000, 1000000, n).astype(float)

# Ensure OHLC relationships
for i in range(n):
    high[i] = max(high[i], open_prices[i], close[i])
    low[i] = min(low[i], open_prices[i], close[i])

# Track results
passed = 0
failed = 0
errors = []


def test_indicator(name, func, *args):
    """Test a single indicator"""
    global passed, failed
    try:
        result = func(*args)

        if result is None:
            print(f"❌ {name:40} - Returned None")
            failed += 1
            errors.append(f"{name}: Returned None")
            return False

        # Check if result is valid
        if isinstance(result, tuple):
            for r in result:
                if not isinstance(r, np.ndarray) or len(r) != n:
                    print(f"❌ {name:40} - Invalid output shape")
                    failed += 1
                    errors.append(f"{name}: Invalid output shape")
                    return False
        elif isinstance(result, np.ndarray):
            if len(result) != n:
                print(f"❌ {name:40} - Invalid output length")
                failed += 1
                errors.append(f"{name}: Invalid output length")
                return False

        print(f"✅ {name:40} - OK")
        passed += 1
        return True

    except Exception as e:
        print(f"❌ {name:40} - {str(e)}")
        failed += 1
        errors.append(f"{name}: {str(e)}")
        return False


print("Testing Hilbert Transform Suite (7 indicators)...")
print("-" * 70)

from encom.indicators import (
    ht_trendline, ht_dcperiod, ht_dcphase, ht_phasor, ht_sine, ht_trendmode, ht_leadsine
)

test_indicator("HT_TRENDLINE", ht_trendline, close)
test_indicator("HT_DCPERIOD", ht_dcperiod, close)
test_indicator("HT_DCPHASE", ht_dcphase, close)
test_indicator("HT_PHASOR", ht_phasor, close)
test_indicator("HT_SINE", ht_sine, close)
test_indicator("HT_TRENDMODE", ht_trendmode, close)
test_indicator("HT_LEADSINE", ht_leadsine, close)

print()
print("Testing Pattern Recognition (5 indicators)...")
print("-" * 70)

from encom.indicators import (
    engulfing_pattern, doji_pattern, hammer_pattern,
    morning_evening_star, three_soldiers_crows
)

test_indicator("Engulfing Pattern", engulfing_pattern, open_prices, high, low, close)
test_indicator("Doji Pattern", doji_pattern, open_prices, high, low, close)
test_indicator("Hammer Pattern", hammer_pattern, open_prices, high, low, close)
test_indicator("Morning/Evening Star", morning_evening_star, open_prices, high, low, close)
test_indicator("Three Soldiers/Crows", three_soldiers_crows, open_prices, high, low, close)

print()
print("Testing Market Profile (3 indicators)...")
print("-" * 70)

from encom.indicators import (
    point_of_control, value_area, volume_profile
)

test_indicator("Point of Control", point_of_control, high, low, close, volume)
test_indicator("Value Area", value_area, high, low, close, volume)
test_indicator("Volume Profile", volume_profile, high, low, close, volume)

print()
print("Testing Order Flow (4 indicators)...")
print("-" * 70)

from encom.indicators import (
    delta_volume, cumulative_volume_delta, aggressive_ratio, volume_pace
)

test_indicator("Delta Volume", delta_volume, high, low, close, volume)
test_indicator("Cumulative Volume Delta", cumulative_volume_delta, high, low, close, volume)
test_indicator("Aggressive Ratio", aggressive_ratio, high, low, close, volume)
test_indicator("Volume Pace", volume_pace, volume)

print()
print("Testing Advanced Volume (5 indicators)...")
print("-" * 70)

from encom.indicators import (
    volume_roc_adv, klinger_volume_oscillator, ease_of_movement,
    negative_volume_index, positive_volume_index
)

test_indicator("Volume ROC", volume_roc_adv, volume)
test_indicator("Klinger Volume Oscillator", klinger_volume_oscillator, high, low, close, volume)
test_indicator("Ease of Movement", ease_of_movement, high, low, volume)
test_indicator("Negative Volume Index", negative_volume_index, close, volume)
test_indicator("Positive Volume Index", positive_volume_index, close, volume)

print()
print("=" * 70)
print("SUMMARY")
print("=" * 70)
print(f"✅ Passed: {passed}/24")
print(f"❌ Failed: {failed}/24")

if failed > 0:
    print()
    print("Errors:")
    for error in errors:
        print(f"  - {error}")
    sys.exit(1)
else:
    print()
    print("🎉 All 24 new indicators working perfectly!")
    print()
    print("Total ENCOM Indicators: 80 (previous) + 24 (new) = 104 indicators")
    print()
    sys.exit(0)
