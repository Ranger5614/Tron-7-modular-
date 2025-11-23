"""
Test Report Generation System

Generates sample reports to verify functionality.

Author: ENCOM Development Team
"""

import sys
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

print("=" * 70)
print("TESTING ENCOM REPORT GENERATION")
print("=" * 70)
print()

# Check dependencies
try:
    import plotly
    print("✅ Plotly installed")
except ImportError:
    print("⚠️  Plotly not installed. Run: pip install plotly")

try:
    import openpyxl
    print("✅ openpyxl installed")
except ImportError:
    print("⚠️  openpyxl not installed. Run: pip install openpyxl")

print()

# Import report generator
try:
    from encom.analytics.report_generator import ReportGenerator
    print("✅ Report generator imported successfully")
    print()
except Exception as e:
    print(f"❌ Import failed: {e}")
    sys.exit(1)

# Create mock backtest result
print("Creating mock backtest result...")

# Generate sample equity curve
np.random.seed(42)
n_days = 252  # 1 year of trading days
start_date = datetime(2023, 1, 1)
dates = pd.date_range(start=start_date, periods=n_days, freq='D')

# Simulate equity curve (starting at $10,000)
initial_capital = 10000
returns = np.random.randn(n_days) * 0.015 + 0.001  # Daily returns with slight upward drift
equity_values = initial_capital * np.cumprod(1 + returns)

# Create equity series with date index
equity_series = pd.Series(equity_values, index=dates)

# Generate sample trades
trades = []
for i in range(30):
    entry_date = dates[np.random.randint(0, n_days - 10)]
    exit_date = entry_date + timedelta(days=np.random.randint(1, 10))
    entry_price = 100 + np.random.randn() * 10
    exit_price = entry_price + np.random.randn() * 5
    shares = 10
    pnl = (exit_price - entry_price) * shares

    trades.append({
        'entry_date': entry_date,
        'exit_date': exit_date,
        'direction': 'long',
        'entry_price': entry_price,
        'exit_price': exit_price,
        'shares': shares,
        'pnl': pnl,
        'return_pct': ((exit_price - entry_price) / entry_price) * 100
    })

# Calculate metrics
total_return = ((equity_values[-1] - initial_capital) / initial_capital) * 100
winning_trades = sum(1 for t in trades if t['pnl'] > 0)
losing_trades = sum(1 for t in trades if t['pnl'] <= 0)
win_rate = (winning_trades / len(trades)) * 100 if trades else 0

gross_profit = sum(t['pnl'] for t in trades if t['pnl'] > 0)
gross_loss = abs(sum(t['pnl'] for t in trades if t['pnl'] < 0))
profit_factor = gross_profit / gross_loss if gross_loss > 0 else 0

# Calculate max drawdown
peak = equity_series.expanding().max()
drawdown = (equity_series - peak) / peak
max_drawdown = drawdown.min() * 100

# Calculate Sharpe ratio
daily_returns = equity_series.pct_change().dropna()
sharpe = (daily_returns.mean() / daily_returns.std()) * np.sqrt(252) if len(daily_returns) > 0 else 0

metrics = {
    'total_return': total_return,
    'annual_return': total_return,  # Assuming 1 year
    'sharpe_ratio': sharpe,
    'sortino_ratio': sharpe * 1.2,  # Mock value
    'max_drawdown': max_drawdown,
    'win_rate': win_rate,
    'profit_factor': profit_factor,
    'total_trades': len(trades),
    'winning_trades': winning_trades,
    'losing_trades': losing_trades,
    'avg_win': gross_profit / winning_trades if winning_trades > 0 else 0,
    'avg_loss': gross_loss / losing_trades if losing_trades > 0 else 0,
    'largest_win': max([t['pnl'] for t in trades], default=0),
    'largest_loss': min([t['pnl'] for t in trades], default=0),
}

# Mock portfolio object
class MockPortfolio:
    def __init__(self, equity_series, initial_capital):
        self._equity = equity_series
        self._initial_capital = initial_capital

    def equity_curve(self):
        return self._equity

    def get_equity(self):
        return self._equity.iloc[-1]

portfolio = MockPortfolio(equity_series, initial_capital)

# Create backtest result dict
backtest_result = {
    'portfolio': portfolio,
    'metrics': metrics,
    'trades': trades,
    'initial_capital': initial_capital,
    'start_date': dates[0],
    'end_date': dates[-1],
}

print(f"Generated mock result:")
print(f"  - Initial Capital: ${initial_capital:,.2f}")
print(f"  - Final Equity: ${equity_values[-1]:,.2f}")
print(f"  - Total Return: {total_return:.2f}%")
print(f"  - Total Trades: {len(trades)}")
print(f"  - Win Rate: {win_rate:.2f}%")
print()

# Generate reports
print("=" * 70)
print("GENERATING REPORTS")
print("=" * 70)
print()

try:
    generator = ReportGenerator(backtest_result, strategy_name="Test Strategy")

    # Generate HTML report
    print("Generating HTML report...")
    html_path = generator.generate_html_report("test_backtest_report.html")

    # Generate Excel report
    print("Generating Excel report...")
    excel_path = generator.generate_excel_report("test_backtest_report.xlsx")

    print()
    print("=" * 70)
    print("SUCCESS")
    print("=" * 70)
    print()
    print("✅ Report generation system is working!")
    print()
    print("Generated reports:")
    if html_path:
        print(f"  - HTML: {html_path}")
    if excel_path:
        print(f"  - Excel: {excel_path}")
    print()
    print("Open the HTML file in your browser to view interactive charts.")
    print()

except Exception as e:
    print(f"❌ Report generation failed: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

print("End of Line. 🎮")
