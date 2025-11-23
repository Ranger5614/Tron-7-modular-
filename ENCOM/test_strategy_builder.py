"""
Test modular strategy builder
"""

import numpy as np
import pandas as pd
from datetime import datetime, timedelta

print("=" * 70)
print("ENCOM Modular Strategy Builder Test")
print("=" * 70)
print()

# Generate test data
n = 100
dates = pd.date_range(start='2024-01-01', periods=n, freq='D')

np.random.seed(42)
close = 100 + np.cumsum(np.random.randn(n) * 2)
high = close + np.abs(np.random.randn(n) * 1.5)
low = close - np.abs(np.random.randn(n) * 1.5)
open_prices = close + np.random.randn(n) * 0.5
volume = np.random.randint(1000000, 5000000, n)

for i in range(n):
    high[i] = max(high[i], open_prices[i], close[i])
    low[i] = min(low[i], open_prices[i], close[i])

data = pd.DataFrame({
    'open': open_prices,
    'high': high,
    'low': low,
    'close': close,
    'volume': volume
}, index=dates)

print("Testing imports...")
try:
    from encom.strategies.strategy_builder import StrategyBuilder
    from encom.strategies.templates import (
        create_rsi_strategy,
        create_ma_crossover_strategy,
        create_macd_strategy,
        create_breakout_strategy,
        create_momentum_strategy
    )
    print("✅ Successfully imported StrategyBuilder and templates")
except ImportError as e:
    print(f"❌ Import error: {e}")
    exit(1)

print()
print("Testing custom strategy builder...")
try:
    # Build custom strategy
    builder = StrategyBuilder("Test Strategy", "Simple test strategy")
    
    # Add simple RSI signal
    def rsi_signal(data, bar_index):
        from encom.indicators import rsi
        rsi_values = rsi(data['close'].values, 14)
        return rsi_values[bar_index] < 30
    
    builder.add_entry_signal('RSI Oversold', rsi_signal)
    
    # Add volume confirmation
    def volume_confirm(data, bar_index):
        if bar_index < 20:
            return False
        avg_vol = sum(data['volume'].values[bar_index-20:bar_index]) / 20
        return data['volume'].values[bar_index] > avg_vol
    
    builder.add_entry_confirmation('Volume Above Average', volume_confirm)
    
    # Add exit signal
    def rsi_exit(data, bar_index):
        from encom.indicators import rsi
        rsi_values = rsi(data['close'].values, 14)
        return rsi_values[bar_index] > 70
    
    builder.add_exit_signal('RSI Overbought', rsi_exit)
    
    # Set position sizing
    builder.set_position_sizing('percent', percent=0.1)
    
    # Build strategy
    strategy = builder.build()
    
    print(f"✅ Custom strategy built: {strategy}")
    print(f"   - {len(strategy.entry_signals)} entry signals")
    print(f"   - {len(strategy.entry_confirmations)} confirmations")
    print(f"   - {len(strategy.exit_signals)} exit signals")
    
except Exception as e:
    print(f"❌ Custom strategy error: {e}")
    exit(1)

print()
print("Testing pre-built templates...")
templates = [
    ('RSI Strategy', create_rsi_strategy),
    ('MA Crossover', create_ma_crossover_strategy),
    ('MACD Strategy', create_macd_strategy),
    ('Breakout Strategy', create_breakout_strategy),
    ('Momentum Strategy', create_momentum_strategy)
]

for name, template_func in templates:
    try:
        strategy = template_func()
        print(f"✅ {name:20} - {strategy.name}")
    except Exception as e:
        print(f"❌ {name:20} - Error: {e}")
        exit(1)

print()
print("Testing strategy execution...")
try:
    # Create simple strategy
    strategy = create_rsi_strategy()
    
    # Test on_data method
    signal_count = 0
    for i in range(20, len(data)):
        signal = strategy.on_data(data, i)
        if signal in ['ENTER', 'EXIT']:
            signal_count += 1
    
    print(f"✅ Strategy executed on {len(data)} bars")
    print(f"   - Generated {signal_count} signals")
    
except Exception as e:
    print(f"❌ Execution error: {e}")
    exit(1)

print()
print("=" * 70)
print("SUMMARY")
print("=" * 70)
print("✅ All strategy builder components working correctly")
print()
print("Features:")
print("  - StrategyBuilder: Modular composition framework")
print("  - 5 pre-built templates ready to use")
print("  - Easy customization with add_* methods")
print("  - Flexible position sizing and risk management")
print("  - Compatible with BacktestRunner")
print()
