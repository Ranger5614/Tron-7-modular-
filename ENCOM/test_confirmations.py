"""
Test all 18 confirmation signals

Verifies:
- All confirmations import correctly
- evaluate() method works
- vectorized_evaluate() method works
- No runtime errors

Author: ENCOM Development Team
"""

import sys
import pandas as pd
import numpy as np

# Test imports
print("=" * 70)
print("TESTING ENCOM CONFIRMATION SIGNALS")
print("=" * 70)
print()

try:
    from encom.signals.confirmations import *
    print("✅ All confirmations imported successfully")
    print()
except Exception as e:
    print(f"❌ Import failed: {e}")
    sys.exit(1)

# Generate test data
np.random.seed(42)
n = 500

# Realistic price data
price = 100 + np.cumsum(np.random.randn(n) * 2)
price = np.maximum(price, 50)  # Floor at 50

high = price + np.random.rand(n) * 2
low = price - np.random.rand(n) * 2
close = price
volume = np.random.randint(1000000, 5000000, n).astype(float)

data = pd.DataFrame({
    'open': price,
    'high': high,
    'low': low,
    'close': close,
    'volume': volume
})

print("Generated test data: 500 bars")
print()

# Test all confirmations
confirmations = [
    # Trend (5)
    ("ADX Strength", ADXStrengthConfirmation()),
    ("Supertrend Alignment", SupertrendAlignmentConfirmation()),
    ("MA Alignment", MovingAverageAlignmentConfirmation()),
    ("Parabolic SAR", ParabolicSARConfirmation()),
    ("Aroon", AroonConfirmation()),
    # Volume (4)
    ("Volume Increasing", VolumeIncreasingConfirmation()),
    ("OBV Trend", OBVTrendConfirmation()),
    ("CMF", CMFConfirmation()),
    ("Volume Ratio", VolumeRatioConfirmation()),
    # Volatility (4)
    ("ATR Expanding", ATRExpandingConfirmation()),
    ("ATR Contracting", ATRContractingConfirmation()),
    ("BB Width Expanding", BollingerBandWidthConfirmation(mode='expanding')),
    ("KC Position", KeltnerChannelPositionConfirmation()),
    # Momentum (5)
    ("RSI Direction", RSIDirectionConfirmation()),
    ("MACD Histogram Slope", MACDHistogramSlopeConfirmation()),
    ("Stochastic Alignment", StochasticAlignmentConfirmation()),
    ("ROC Positive", ROCPositiveConfirmation()),
    ("CCI", CCIConfirmation()),
]

print("=" * 70)
print("TESTING evaluate() METHOD")
print("=" * 70)
print()

passed = 0
failed = 0

for name, confirmation in confirmations:
    try:
        # Test at bar 100 for long direction
        result = confirmation.evaluate(data, direction=1, bar_idx=100)

        if isinstance(result, (bool, np.bool_)):
            print(f"✅ {name:30} - OK (result: {result})")
            passed += 1
        else:
            print(f"❌ {name:30} - Invalid return type: {type(result)}")
            failed += 1
    except Exception as e:
        print(f"❌ {name:30} - Error: {str(e)[:40]}")
        failed += 1

print()
print(f"Results: {passed} passed, {failed} failed")
print()

# Test vectorized evaluation
print("=" * 70)
print("TESTING vectorized_evaluate() METHOD")
print("=" * 70)
print()

passed_vec = 0
failed_vec = 0

for name, confirmation in confirmations:
    try:
        # Test vectorized evaluation
        result = confirmation.vectorized_evaluate(data, direction=1)

        if isinstance(result, np.ndarray) and result.dtype == bool and len(result) == len(data):
            true_count = np.sum(result)
            pct = (true_count / len(result)) * 100
            print(f"✅ {name:30} - OK ({true_count} confirmations, {pct:.1f}%)")
            passed_vec += 1
        else:
            print(f"❌ {name:30} - Invalid return: {type(result)}")
            failed_vec += 1
    except Exception as e:
        print(f"❌ {name:30} - Error: {str(e)[:40]}")
        failed_vec += 1

print()
print(f"Results: {passed_vec} passed, {failed_vec} failed")
print()

# Final summary
print("=" * 70)
print("SUMMARY")
print("=" * 70)
print()

total_tests = len(confirmations) * 2  # evaluate + vectorized
total_passed = passed + passed_vec
total_failed = failed + failed_vec

print(f"Total confirmations: {len(confirmations)}")
print(f"Total tests run: {total_tests}")
print(f"✅ Passed: {total_passed}")
print(f"❌ Failed: {total_failed}")
print()

if total_failed == 0:
    print("🎉 ALL TESTS PASSED - Confirmations are production-ready!")
    print()
    print("Available confirmation signals:")
    print("  • Trend (5): ADX, Supertrend, MA Alignment, PSAR, Aroon")
    print("  • Volume (4): Volume Increasing, OBV, CMF, Volume Ratio")
    print("  • Volatility (4): ATR Expanding/Contracting, BB Width, KC Position")
    print("  • Momentum (5): RSI, MACD Histogram, Stochastic, ROC, CCI")
    print()
    print("Total: 18 confirmation signals ready to use!")
else:
    print("⚠️  Some tests failed - review errors above")
    sys.exit(1)

print()
print("End of Line. 🎮")
