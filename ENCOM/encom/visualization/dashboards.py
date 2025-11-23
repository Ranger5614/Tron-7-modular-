"""
Professional Dashboards for ENCOM

Complete portfolio and backtesting dashboards.
Real-time monitoring and analysis interfaces.

Author: ENCOM Development Team
License: MIT
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional
from datetime import datetime

try:
    import plotly.graph_objects as go
    from plotly.subplots import make_subplots
    PLOTLY_AVAILABLE = True
except ImportError:
    PLOTLY_AVAILABLE = False


class BacktestDashboard:
    """
    Comprehensive backtesting dashboard
    
    Displays:
    - Equity curve with trades
    - Drawdown
    - Returns distribution
    - Win/loss analysis
    - Monthly performance heatmap
    - Key metrics table
    """
    
    def __init__(self, backtest_result: Dict):
        """
        Args:
            backtest_result: Backtest result dictionary from BacktestRunner
        """
        if not PLOTLY_AVAILABLE:
            raise ImportError("Plotly required for dashboards")
        
        self.result = backtest_result
        self.portfolio = backtest_result.get('portfolio')
        self.metrics = backtest_result.get('metrics', {})
        self.trades = backtest_result.get('trades', [])
        self.fig = None
    
    def create_dashboard(self):
        """Create complete backtesting dashboard"""
        # Create 3x2 grid layout
        self.fig = make_subplots(
            rows=3, cols=2,
            subplot_titles=(
                'Equity Curve', 'Drawdown',
                'Returns Distribution', 'Win/Loss Analysis',
                'Monthly Returns Heatmap', 'Key Metrics'
            ),
            specs=[
                [{"type": "scatter"}, {"type": "scatter"}],
                [{"type": "histogram"}, {"type": "bar"}],
                [{"type": "heatmap", "colspan": 2}, None]
            ],
            vertical_spacing=0.12,
            horizontal_spacing=0.10,
            row_heights=[0.35, 0.3, 0.35]
        )
        
        # 1. Equity Curve
        equity_history = self.portfolio.equity_history
        dates = [e['date'] for e in equity_history]
        equity = [e['equity'] for e in equity_history]
        
        self.fig.add_trace(
            go.Scatter(
                x=dates,
                y=equity,
                mode='lines',
                name='Equity',
                line=dict(color='#2196F3', width=2),
                fill='tozeroy',
                fillcolor='rgba(33, 150, 243, 0.1)'
            ),
            row=1, col=1
        )
        
        # Add trade markers
        for trade in self.trades:
            if trade['direction'] == 'BUY':
                self.fig.add_trace(
                    go.Scatter(
                        x=[trade['entry_date']],
                        y=[trade['entry_price']],
                        mode='markers',
                        marker=dict(symbol='triangle-up', size=10, color='#26a69a'),
                        showlegend=False,
                        hovertext=f"BUY @ ${trade['entry_price']:.2f}"
                    ),
                    row=1, col=1
                )
            else:
                self.fig.add_trace(
                    go.Scatter(
                        x=[trade['exit_date']],
                        y=[trade['exit_price']],
                        mode='markers',
                        marker=dict(symbol='triangle-down', size=10, color='#ef5350'),
                        showlegend=False,
                        hovertext=f"SELL @ ${trade['exit_price']:.2f} | P&L: ${trade['pnl']:+.2f}"
                    ),
                    row=1, col=1
                )
        
        # 2. Drawdown
        equity_series = pd.Series(equity, index=dates)
        cummax = equity_series.cummax()
        drawdown = (equity_series - cummax) / cummax * 100
        
        self.fig.add_trace(
            go.Scatter(
                x=dates,
                y=drawdown.values,
                mode='lines',
                name='Drawdown',
                line=dict(color='#ef5350', width=1),
                fill='tozeroy',
                fillcolor='rgba(239, 83, 80, 0.3)'
            ),
            row=1, col=2
        )
        
        # 3. Returns Distribution
        if len(self.trades) > 0:
            returns_pct = [t.get('return_pct', 0) for t in self.trades]
            
            self.fig.add_trace(
                go.Histogram(
                    x=returns_pct,
                    name='Returns',
                    marker=dict(color='#9C27B0'),
                    opacity=0.7,
                    nbinsx=30
                ),
                row=2, col=1
            )
        
        # 4. Win/Loss Analysis
        if len(self.trades) > 0:
            winning_trades = len([t for t in self.trades if t.get('pnl', 0) > 0])
            losing_trades = len([t for t in self.trades if t.get('pnl', 0) <= 0])
            
            self.fig.add_trace(
                go.Bar(
                    x=['Wins', 'Losses'],
                    y=[winning_trades, losing_trades],
                    marker=dict(color=['#26a69a', '#ef5350']),
                    name='Trades'
                ),
                row=2, col=2
            )
        
        # 5. Monthly Returns Heatmap
        if len(equity_history) > 30:
            monthly_returns = self._calculate_monthly_returns(pd.Series(equity, index=dates))

            if not monthly_returns.empty:
                # Convert Series to DataFrame for pivot
                monthly_df = pd.DataFrame({
                    'year': monthly_returns.index.year,
                    'month': monthly_returns.index.month,
                    'returns': monthly_returns.values
                })

                # Pivot to year x month matrix
                pivot = monthly_df.pivot_table(
                    index='year',
                    columns='month',
                    values='returns'
                )
                
                month_names = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun',
                             'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
                
                self.fig.add_trace(
                    go.Heatmap(
                        z=pivot.values,
                        x=month_names[:len(pivot.columns)],
                        y=pivot.index,
                        colorscale='RdYlGn',
                        zmid=0,
                        text=np.round(pivot.values, 1),
                        texttemplate='%{text}%',
                        textfont={"size": 10},
                        name='Monthly Returns'
                    ),
                    row=3, col=1
                )
        
        # Update layout
        self.fig.update_layout(
            height=1200,
            showlegend=False,
            title_text="Backtesting Dashboard",
            title_font_size=24,
            template='plotly_dark'
        )
        
        # Update axes labels
        self.fig.update_xaxes(title_text="Date", row=1, col=1)
        self.fig.update_yaxes(title_text="Equity ($)", row=1, col=1)
        
        self.fig.update_xaxes(title_text="Date", row=1, col=2)
        self.fig.update_yaxes(title_text="Drawdown (%)", row=1, col=2)
        
        self.fig.update_xaxes(title_text="Return (%)", row=2, col=1)
        self.fig.update_yaxes(title_text="Frequency", row=2, col=1)
        
        self.fig.update_xaxes(title_text="", row=2, col=2)
        self.fig.update_yaxes(title_text="Count", row=2, col=2)
        
        self.fig.update_xaxes(title_text="Month", row=3, col=1)
        self.fig.update_yaxes(title_text="Year", row=3, col=1)
        
        return self
    
    def _calculate_monthly_returns(self, equity: pd.Series) -> pd.Series:
        """Calculate monthly returns from equity curve"""
        # Resample to month-end (ME = month end)
        monthly_equity = equity.resample('ME').last()
        
        # Calculate returns
        monthly_returns = monthly_equity.pct_change() * 100
        
        return monthly_returns.dropna()
    
    def add_metrics_table(self):
        """Add key metrics table"""
        # Format metrics for display
        metrics_data = {
            'Metric': [],
            'Value': []
        }
        
        # Select key metrics
        display_metrics = {
            'Total Return': f"{self.metrics.get('total_return', 0):.2f}%",
            'Sharpe Ratio': f"{self.metrics.get('sharpe_ratio', 0):.2f}",
            'Max Drawdown': f"{self.metrics.get('max_drawdown', 0):.2f}%",
            'Win Rate': f"{self.metrics.get('win_rate', 0):.2f}%",
            'Total Trades': f"{self.metrics.get('total_trades', 0)}",
            'Profit Factor': f"{self.metrics.get('profit_factor', 0):.2f}",
        }
        
        for metric, value in display_metrics.items():
            metrics_data['Metric'].append(metric)
            metrics_data['Value'].append(value)
        
        # Add as annotation (simplified)
        metrics_text = "<br>".join([f"<b>{k}:</b> {v}" for k, v in display_metrics.items()])
        
        self.fig.add_annotation(
            xref="paper",
            yref="paper",
            x=0.98,
            y=0.98,
            text=metrics_text,
            showarrow=False,
            bgcolor="rgba(0,0,0,0.5)",
            bordercolor="white",
            borderwidth=1,
            font=dict(size=12, color="white"),
            align="left"
        )
        
        return self
    
    def show(self):
        """Display dashboard"""
        if self.fig is None:
            raise ValueError("Create dashboard first")
        self.fig.show()
    
    def save(self, filepath: str):
        """Save to HTML"""
        if self.fig is None:
            raise ValueError("Create dashboard first")
        self.fig.write_html(filepath)
        print(f"✅ Dashboard saved to: {filepath}")


class LiveTradingDashboard:
    """
    Real-time trading dashboard
    
    Features:
    - Live position monitoring
    - Real-time P&L
    - Open orders
    - Account status
    - Recent trades
    """
    
    def __init__(self):
        """Initialize live dashboard"""
        if not PLOTLY_AVAILABLE:
            raise ImportError("Plotly required")
        
        self.fig = None
        self.positions = []
        self.orders = []
        self.account_info = {}
    
    def create_dashboard(self, positions: List[Dict], 
                        orders: List[Dict],
                        account_info: Dict):
        """
        Create live trading dashboard
        
        Args:
            positions: List of open positions
            orders: List of open orders
            account_info: Account information dict
        """
        self.positions = positions
        self.orders = orders
        self.account_info = account_info
        
        # Create 2x2 grid
        self.fig = make_subplots(
            rows=2, cols=2,
            subplot_titles=(
                'Open Positions', 'Account Summary',
                'Position P&L', 'Open Orders'
            ),
            specs=[
                [{"type": "table"}, {"type": "table"}],
                [{"type": "bar"}, {"type": "table"}]
            ],
            vertical_spacing=0.15,
            horizontal_spacing=0.12
        )
        
        # 1. Open Positions Table
        if positions:
            pos_data = {
                'Symbol': [p['symbol'] for p in positions],
                'Quantity': [p['quantity'] for p in positions],
                'Avg Cost': [f"${p['avg_cost']:.2f}" for p in positions],
                'Current': [f"${p['current_price']:.2f}" for p in positions],
                'P&L': [f"${p['unrealized_pnl']:+.2f}" for p in positions],
                'P&L %': [f"{p['unrealized_pnl_pct']:+.2f}%" for p in positions]
            }
            
            # Color P&L based on gain/loss
            colors = ['palegreen' if p['unrealized_pnl'] > 0 else 'lightcoral' 
                     for p in positions]
            
            self.fig.add_trace(
                go.Table(
                    header=dict(
                        values=list(pos_data.keys()),
                        fill_color='#1976D2',
                        font=dict(color='white', size=12),
                        align='left'
                    ),
                    cells=dict(
                        values=list(pos_data.values()),
                        fill_color=['white'] * 4 + [colors] * 2,
                        font=dict(color='black', size=11),
                        align='left'
                    )
                ),
                row=1, col=1
            )
        
        # 2. Account Summary
        acc_data = {
            'Metric': ['Total Value', 'Cash', 'Buying Power', 'Day P&L', 'Total P&L'],
            'Value': [
                f"${account_info.get('total_value', 0):,.2f}",
                f"${account_info.get('cash', 0):,.2f}",
                f"${account_info.get('buying_power', 0):,.2f}",
                f"${account_info.get('day_pnl', 0):+,.2f}",
                f"${account_info.get('total_pnl', 0):+,.2f}"
            ]
        }
        
        self.fig.add_trace(
            go.Table(
                header=dict(
                    values=['Metric', 'Value'],
                    fill_color='#1976D2',
                    font=dict(color='white', size=12),
                    align='left'
                ),
                cells=dict(
                    values=[acc_data['Metric'], acc_data['Value']],
                    fill_color='white',
                    font=dict(color='black', size=11),
                    align='left'
                )
            ),
            row=1, col=2
        )
        
        # 3. Position P&L Bar Chart
        if positions:
            symbols = [p['symbol'] for p in positions]
            pnls = [p['unrealized_pnl'] for p in positions]
            colors_bar = ['#26a69a' if pnl > 0 else '#ef5350' for pnl in pnls]
            
            self.fig.add_trace(
                go.Bar(
                    x=symbols,
                    y=pnls,
                    marker=dict(color=colors_bar),
                    name='P&L'
                ),
                row=2, col=1
            )
        
        # 4. Open Orders Table
        if orders:
            order_data = {
                'Symbol': [o['symbol'] for o in orders],
                'Action': [o['action'] for o in orders],
                'Quantity': [o['quantity'] for o in orders],
                'Type': [o['order_type'] for o in orders],
                'Limit Price': [f"${o.get('limit_price', 0):.2f}" if o.get('limit_price') else 'Market' for o in orders],
                'Status': [o['status'] for o in orders]
            }
            
            self.fig.add_trace(
                go.Table(
                    header=dict(
                        values=list(order_data.keys()),
                        fill_color='#1976D2',
                        font=dict(color='white', size=12),
                        align='left'
                    ),
                    cells=dict(
                        values=list(order_data.values()),
                        fill_color='white',
                        font=dict(color='black', size=11),
                        align='left'
                    )
                ),
                row=2, col=2
            )
        
        # Update layout
        self.fig.update_layout(
            height=900,
            title_text="Live Trading Dashboard",
            title_font_size=24,
            showlegend=False,
            template='plotly_dark'
        )
        
        self.fig.update_yaxes(title_text="P&L ($)", row=2, col=1)
        
        return self
    
    def show(self):
        """Display dashboard"""
        if self.fig is None:
            raise ValueError("Create dashboard first")
        self.fig.show()
    
    def save(self, filepath: str):
        """Save to HTML"""
        if self.fig is None:
            raise ValueError("Create dashboard first")
        self.fig.write_html(filepath)
        print(f"✅ Dashboard saved to: {filepath}")
