"""
Professional Interactive Charts for ENCOM

Real-time charting with technical indicators overlay.
Interactive Plotly-based visualizations for analysis.

Author: ENCOM Development Team
License: MIT
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Tuple
from datetime import datetime

try:
    import plotly.graph_objects as go
    from plotly.subplots import make_subplots
    PLOTLY_AVAILABLE = True
except ImportError:
    PLOTLY_AVAILABLE = False
    print("⚠️  Plotly not available. Install with: pip install plotly")


class TradingChart:
    """
    Professional interactive trading chart
    
    Features:
    - Candlestick/OHLC charts
    - Volume bars
    - Technical indicators overlay
    - Trade entry/exit markers
    - Custom annotations
    - Responsive zoom/pan
    """
    
    def __init__(self, data: pd.DataFrame, title: str = "Trading Chart"):
        """
        Args:
            data: OHLCV DataFrame with columns: open, high, low, close, volume
            title: Chart title
        """
        if not PLOTLY_AVAILABLE:
            raise ImportError("Plotly is required for charts. Install with: pip install plotly")
        
        self.data = data
        self.title = title
        self.fig = None
        self.indicators = []
        self.trades = []
        
    def create_base_chart(self, chart_type: str = 'candlestick'):
        """
        Create base chart with price and volume
        
        Args:
            chart_type: 'candlestick' or 'ohlc'
        """
        # Create subplots (price + volume)
        self.fig = make_subplots(
            rows=2, cols=1,
            shared_xaxes=True,
            vertical_spacing=0.05,
            row_heights=[0.7, 0.3],
            subplot_titles=(self.title, 'Volume')
        )
        
        # Price chart
        if chart_type == 'candlestick':
            price_trace = go.Candlestick(
                x=self.data.index,
                open=self.data['open'],
                high=self.data['high'],
                low=self.data['low'],
                close=self.data['close'],
                name='Price',
                increasing_line_color='#26a69a',
                decreasing_line_color='#ef5350'
            )
        else:  # OHLC
            price_trace = go.Ohlc(
                x=self.data.index,
                open=self.data['open'],
                high=self.data['high'],
                low=self.data['low'],
                close=self.data['close'],
                name='Price'
            )
        
        self.fig.add_trace(price_trace, row=1, col=1)
        
        # Volume bars
        colors = ['#ef5350' if row['close'] < row['open'] else '#26a69a' 
                 for idx, row in self.data.iterrows()]
        
        self.fig.add_trace(
            go.Bar(
                x=self.data.index,
                y=self.data['volume'],
                name='Volume',
                marker=dict(color=colors),
                opacity=0.6
            ),
            row=2, col=1
        )
        
        # Update layout
        self.fig.update_layout(
            height=800,
            showlegend=True,
            xaxis_rangeslider_visible=False,
            hovermode='x unified',
            template='plotly_dark'
        )
        
        self.fig.update_xaxes(title_text="Date", row=2, col=1)
        self.fig.update_yaxes(title_text="Price", row=1, col=1)
        self.fig.update_yaxes(title_text="Volume", row=2, col=1)
        
        return self
    
    def add_indicator(self, name: str, values: np.ndarray, 
                     color: str = None, dash: str = 'solid',
                     row: int = 1, secondary_y: bool = False):
        """
        Add technical indicator overlay
        
        Args:
            name: Indicator name
            values: Indicator values
            color: Line color
            dash: Line style ('solid', 'dash', 'dot')
            row: Subplot row number
            secondary_y: Use secondary y-axis
        """
        if self.fig is None:
            raise ValueError("Create base chart first with create_base_chart()")
        
        # Ensure values match data length
        if len(values) != len(self.data):
            raise ValueError(f"Indicator length ({len(values)}) must match data length ({len(self.data)})")
        
        # Create indicator trace
        trace = go.Scatter(
            x=self.data.index,
            y=values,
            name=name,
            mode='lines',
            line=dict(color=color, dash=dash),
            opacity=0.8
        )
        
        self.fig.add_trace(trace, row=row, col=1, secondary_y=secondary_y)
        self.indicators.append(name)
        
        return self
    
    def add_horizontal_line(self, y: float, name: str, 
                           color: str = 'gray', dash: str = 'dash',
                           row: int = 1):
        """
        Add horizontal reference line
        
        Args:
            y: Y-coordinate
            name: Line name
            color: Line color
            dash: Line style
            row: Subplot row
        """
        if self.fig is None:
            raise ValueError("Create base chart first")
        
        self.fig.add_hline(
            y=y,
            line_dash=dash,
            line_color=color,
            annotation_text=name,
            row=row,
            col=1
        )
        
        return self
    
    def add_trades(self, trades: List[Dict]):
        """
        Add trade entry/exit markers
        
        Args:
            trades: List of trade dicts with keys: date, price, type ('buy'/'sell'), pnl (optional)
        """
        if self.fig is None:
            raise ValueError("Create base chart first")
        
        for trade in trades:
            date = trade['date']
            price = trade['price']
            trade_type = trade['type']
            pnl = trade.get('pnl', None)
            
            # Marker settings
            if trade_type == 'buy':
                marker = dict(symbol='triangle-up', size=15, color='#26a69a')
                text = f"BUY @ ${price:.2f}"
            else:
                marker = dict(symbol='triangle-down', size=15, color='#ef5350')
                text = f"SELL @ ${price:.2f}"
                if pnl is not None:
                    text += f" | P&L: ${pnl:+.2f}"
            
            # Add marker
            self.fig.add_trace(
                go.Scatter(
                    x=[date],
                    y=[price],
                    mode='markers+text',
                    marker=marker,
                    text=[text],
                    textposition='top center',
                    textfont=dict(size=10),
                    showlegend=False,
                    hoverinfo='text'
                ),
                row=1, col=1
            )
            
            self.trades.append(trade)
        
        return self
    
    def add_annotation(self, date, y, text: str, 
                      arrow: bool = True, color: str = 'white'):
        """
        Add custom annotation
        
        Args:
            date: X-coordinate (date)
            y: Y-coordinate (price)
            text: Annotation text
            arrow: Show arrow
            color: Text color
        """
        if self.fig is None:
            raise ValueError("Create base chart first")
        
        self.fig.add_annotation(
            x=date,
            y=y,
            text=text,
            showarrow=arrow,
            arrowhead=2,
            arrowcolor=color,
            font=dict(color=color, size=12),
            row=1,
            col=1
        )
        
        return self
    
    def show(self):
        """Display the chart"""
        if self.fig is None:
            raise ValueError("Create base chart first")
        
        self.fig.show()
    
    def save(self, filepath: str):
        """
        Save chart to HTML file
        
        Args:
            filepath: Output file path
        """
        if self.fig is None:
            raise ValueError("Create base chart first")
        
        self.fig.write_html(filepath)
        print(f"✅ Chart saved to: {filepath}")


class PortfolioChart:
    """
    Portfolio performance visualization
    
    Features:
    - Equity curve
    - Drawdown chart
    - Rolling metrics
    - Comparison with benchmark
    """
    
    def __init__(self, equity_curve: pd.Series, title: str = "Portfolio Performance"):
        """
        Args:
            equity_curve: Portfolio equity over time
            title: Chart title
        """
        if not PLOTLY_AVAILABLE:
            raise ImportError("Plotly required")
        
        self.equity = equity_curve
        self.title = title
        self.fig = None
        
    def create_performance_chart(self, benchmark: Optional[pd.Series] = None):
        """
        Create equity curve with drawdown
        
        Args:
            benchmark: Optional benchmark series to compare
        """
        # Calculate drawdown
        cummax = self.equity.cummax()
        drawdown = (self.equity - cummax) / cummax * 100
        
        # Create subplots
        self.fig = make_subplots(
            rows=2, cols=1,
            shared_xaxes=True,
            vertical_spacing=0.08,
            row_heights=[0.7, 0.3],
            subplot_titles=(self.title, 'Drawdown (%)')
        )
        
        # Equity curve
        self.fig.add_trace(
            go.Scatter(
                x=self.equity.index,
                y=self.equity.values,
                name='Portfolio',
                mode='lines',
                line=dict(color='#2196F3', width=2),
                fill='tozeroy',
                fillcolor='rgba(33, 150, 243, 0.1)'
            ),
            row=1, col=1
        )
        
        # Benchmark (if provided)
        if benchmark is not None:
            self.fig.add_trace(
                go.Scatter(
                    x=benchmark.index,
                    y=benchmark.values,
                    name='Benchmark',
                    mode='lines',
                    line=dict(color='gray', width=1, dash='dash'),
                    opacity=0.6
                ),
                row=1, col=1
            )
        
        # Drawdown
        self.fig.add_trace(
            go.Scatter(
                x=drawdown.index,
                y=drawdown.values,
                name='Drawdown',
                mode='lines',
                line=dict(color='#ef5350', width=1),
                fill='tozeroy',
                fillcolor='rgba(239, 83, 80, 0.3)'
            ),
            row=2, col=1
        )
        
        # Layout
        self.fig.update_layout(
            height=700,
            showlegend=True,
            hovermode='x unified',
            template='plotly_dark'
        )
        
        self.fig.update_xaxes(title_text="Date", row=2, col=1)
        self.fig.update_yaxes(title_text="Equity ($)", row=1, col=1)
        self.fig.update_yaxes(title_text="Drawdown (%)", row=2, col=1)
        
        return self
    
    def show(self):
        """Display chart"""
        if self.fig is None:
            raise ValueError("Create chart first")
        self.fig.show()
    
    def save(self, filepath: str):
        """Save to HTML"""
        if self.fig is None:
            raise ValueError("Create chart first")
        self.fig.write_html(filepath)
        print(f"✅ Chart saved to: {filepath}")


class MultiAssetChart:
    """
    Multi-asset comparison charts
    
    Features:
    - Normalized returns comparison
    - Correlation heatmap
    - Rolling metrics
    """
    
    def __init__(self, returns_dict: Dict[str, pd.Series], 
                 title: str = "Multi-Asset Comparison"):
        """
        Args:
            returns_dict: Dict of symbol -> returns series
            title: Chart title
        """
        if not PLOTLY_AVAILABLE:
            raise ImportError("Plotly required")
        
        self.returns_dict = returns_dict
        self.title = title
        self.fig = None
    
    def create_comparison_chart(self):
        """Create normalized returns comparison"""
        self.fig = go.Figure()
        
        # Normalize all returns to start at 100
        for symbol, returns in self.returns_dict.items():
            cumulative = (1 + returns).cumprod() * 100
            
            self.fig.add_trace(
                go.Scatter(
                    x=returns.index,
                    y=cumulative.values,
                    name=symbol,
                    mode='lines'
                )
            )
        
        self.fig.update_layout(
            title=self.title,
            xaxis_title="Date",
            yaxis_title="Normalized Returns (Base=100)",
            height=600,
            hovermode='x unified',
            template='plotly_dark'
        )
        
        return self
    
    def show(self):
        """Display chart"""
        if self.fig is None:
            raise ValueError("Create chart first")
        self.fig.show()
    
    def save(self, filepath: str):
        """Save to HTML"""
        if self.fig is None:
            raise ValueError("Create chart first")
        self.fig.write_html(filepath)
        print(f"✅ Chart saved to: {filepath}")
