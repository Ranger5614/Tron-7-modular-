"""
Advanced Visualization Module for ENCOM

Professional-grade interactive charts and dashboards for quantitative analysis.

Features:
- Interactive Plotly charts
- Real-time streaming plots
- Portfolio dashboards
- Multi-asset comparisons
- Custom indicators overlay

Usage:
    from encom.visualization import TradingChart, PortfolioChart, BacktestDashboard

    # Create interactive trading chart
    chart = TradingChart(data, title="AAPL Trading Chart")
    chart.create_base_chart('candlestick')
    chart.add_indicator('SMA 50', sma_values, color='orange')
    chart.add_trades(trades_list)
    chart.show()

    # Create backtesting dashboard
    dashboard = BacktestDashboard(backtest_result)
    dashboard.create_dashboard()
    dashboard.show()

Author: ENCOM Development Team
License: MIT
"""

from encom.visualization.charts import TradingChart, PortfolioChart, MultiAssetChart
from encom.visualization.dashboards import BacktestDashboard, LiveTradingDashboard

__all__ = [
    'TradingChart',
    'PortfolioChart',
    'MultiAssetChart',
    'BacktestDashboard',
    'LiveTradingDashboard'
]
