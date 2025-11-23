#!/usr/bin/env python3
"""
Performance Benchmark - Test indicator speed
"""

import numpy as np
import time

# Generate test data
np.random.seed(42)
n_bars = 10000
close = np.cumsum(np.random.randn(n_bars)) + 100

print(f"Performance Benchmark")
print(f"Data size: {n_bars:,} bars")
print("=" * 50)

# Test RSI
try:
    from encom.indicators import rsi

    # Warmup (JIT compilation)
    _ = rsi(close[:100], 14)

    # Benchmark
    start = time.time()
    for _ in range(100):
        result = rsi(close, 14)
    elapsed = time.time() - start

    print(f"✅ RSI (Numba):        {elapsed:.3f}s for 100 runs")
    print(f"   Per run:            {elapsed/100*1000:.2f}ms")
    print(f"   Throughput:         {n_bars * 100 / elapsed / 1000:.0f}K bars/sec")
except Exception as e:
    print(f"❌ RSI failed: {e}")

print()

# Test MACD
try:
    from encom.indicators import macd

    # Warmup
    _ = macd(close[:100])

    # Benchmark
    start = time.time()
    for _ in range(100):
        macd_line, signal, hist = macd(close)
    elapsed = time.time() - start

    print(f"✅ MACD (Numba):       {elapsed:.3f}s for 100 runs")
    print(f"   Per run:            {elapsed/100*1000:.2f}ms")
    print(f"   Throughput:         {n_bars * 100 / elapsed / 1000:.0f}K bars/sec")
except Exception as e:
    print(f"❌ MACD failed: {e}")

print()

# Test Bollinger Bands
try:
    from encom.indicators import bollinger_bands

    # Warmup
    _ = bollinger_bands(close[:100])

    # Benchmark
    start = time.time()
    for _ in range(100):
        middle, upper, lower = bollinger_bands(close, 20, 2.0)
    elapsed = time.time() - start

    print(f"✅ Bollinger (Numba):  {elapsed:.3f}s for 100 runs")
    print(f"   Per run:            {elapsed/100*1000:.2f}ms")
    print(f"   Throughput:         {n_bars * 100 / elapsed / 1000:.0f}K bars/sec")
except Exception as e:
    print(f"❌ Bollinger failed: {e}")

print()
print("=" * 50)
print("🚀 Optimization Status:")

try:
    import numba
    print(f"✅ Numba installed: v{numba.__version__}")
    print("   JIT compilation active - FAST MODE")
except ImportError:
    print("⚠️  Numba not installed")
    print("   Install: pip install numba")
    print("   Running in fallback mode (slower)")

print()
print("Expected performance with Numba:")
print("  - 10,000 bars: <10ms per indicator")
print("  - 100,000 bars: <100ms per indicator")
print("  - 20-50x faster than pandas")
print()
print("End of Line. 🎮")
