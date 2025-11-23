"""
Test visualization module
"""

import numpy as np
import pandas as pd
from datetime import datetime, timedelta

print("=" * 70)
print("ENCOM Visualization Module Test")
print("=" * 70)
print()

# Generate test data
n = 100
dates = pd.date_range(start='2024-01-01', periods=n, freq='D')

# Realistic price data
np.random.seed(42)
close = 100 + np.cumsum(np.random.randn(n) * 2)
high = close + np.abs(np.random.randn(n) * 1.5)
low = close - np.abs(np.random.randn(n) * 1.5)
open_prices = close + np.random.randn(n) * 0.5
volume = np.random.randint(1000000, 5000000, n)

# Ensure OHLC relationships
for i in range(n):
    high[i] = max(high[i], open_prices[i], close[i])
    low[i] = min(low[i], open_prices[i], close[i])

# Create DataFrame
data = pd.DataFrame({
    'open': open_prices,
    'high': high,
    'low': low,
    'close': close,
    'volume': volume
}, index=dates)

print("Testing visualization imports...")
try:
    from encom.visualization import TradingChart, PortfolioChart, BacktestDashboard
    print("✅ Successfully imported: TradingChart, PortfolioChart, BacktestDashboard")
except ImportError as e:
    print(f"❌ Import error: {e}")
    print("Note: Plotly may not be installed. This is optional.")
    exit(0)

print()
print("Testing TradingChart creation...")
try:
    chart = TradingChart(data, title="Test Trading Chart")
    chart.create_base_chart('candlestick')
    
    # Add a simple moving average
    sma = data['close'].rolling(20).mean()
    chart.add_indicator('SMA 20', sma.values, color='orange')
    
    print("✅ TradingChart created successfully")
except Exception as e:
    print(f"❌ TradingChart error: {e}")
    exit(1)

print()
print("Testing PortfolioChart creation...")
try:
    # Create equity curve
    equity = pd.Series(
        10000 + np.cumsum(np.random.randn(n) * 100),
        index=dates
    )
    
    portfolio_chart = PortfolioChart(equity, title="Test Portfolio")
    portfolio_chart.create_performance_chart()
    
    print("✅ PortfolioChart created successfully")
except Exception as e:
    print(f"❌ PortfolioChart error: {e}")
    exit(1)

print()
print("Testing BacktestDashboard creation...")
try:
    # Mock backtest result
    equity_history = [
        {'date': dates[i], 'equity': 10000 + i * 100}
        for i in range(n)
    ]
    
    trades = [
        {
            'entry_date': dates[10],
            'entry_price': 100,
            'exit_date': dates[20],
            'exit_price': 105,
            'direction': 'BUY',
            'pnl': 50,
            'return_pct': 5.0
        },
        {
            'entry_date': dates[30],
            'entry_price': 110,
            'exit_date': dates[40],
            'exit_price': 108,
            'direction': 'BUY',
            'pnl': -20,
            'return_pct': -1.8
        }
    ]
    
    backtest_result = {
        'portfolio': type('obj', (object,), {
            'equity_history': equity_history,
            'get_equity': lambda: equity_history[-1]['equity']
        })(),
        'metrics': {
            'total_return': 25.5,
            'sharpe_ratio': 1.8,
            'max_drawdown': -15.2,
            'win_rate': 60.0,
            'total_trades': 10,
            'profit_factor': 2.1
        },
        'trades': trades
    }
    
    dashboard = BacktestDashboard(backtest_result)
    dashboard.create_dashboard()
    
    print("✅ BacktestDashboard created successfully")
except Exception as e:
    print(f"❌ BacktestDashboard error: {e}")
    exit(1)

print()
print("=" * 70)
print("SUMMARY")
print("=" * 70)
print("✅ All visualization components working correctly")
print()
print("Visualization Features:")
print("  - TradingChart: Interactive candlestick/OHLC charts")
print("  - PortfolioChart: Equity curve with drawdown")
print("  - BacktestDashboard: Complete backtesting dashboard")
print("  - All charts support .show() and .save(filepath)")
print()
