"""
Professional Report Generation for ENCOM Backtesting Engine

Generates:
- Interactive HTML reports with Plotly charts
- Excel exports with formatted tables and trade logs
- PDF reports (optional)
- Performance summary dashboards

Author: ENCOM Development Team
License: MIT
"""

import pandas as pd
import numpy as np
from datetime import datetime
from pathlib import Path
import json

try:
    import plotly.graph_objects as go
    from plotly.subplots import make_subplots
    PLOTLY_AVAILABLE = True
except ImportError:
    PLOTLY_AVAILABLE = False
    print("⚠️  Plotly not available. Install with: pip install plotly")

try:
    import openpyxl
    from openpyxl.styles import Font, Alignment, PatternFill, Border, Side
    EXCEL_AVAILABLE = True
except ImportError:
    EXCEL_AVAILABLE = False
    print("⚠️  openpyxl not available. Install with: pip install openpyxl")


class ReportGenerator:
    """
    Generate professional backtest reports

    Features:
    - Interactive equity curve with Plotly
    - Drawdown underwater chart
    - Monthly/yearly return heatmaps
    - Excel export with trade log
    - Performance summary tables
    """

    def __init__(self, backtest_result, strategy_name="Strategy"):
        """
        Args:
            backtest_result: Result dict from BacktestRunner
            strategy_name: Name of strategy for reports
        """
        self.result = backtest_result
        self.strategy_name = strategy_name
        self.portfolio = backtest_result.get('portfolio')
        self.metrics = backtest_result.get('metrics', {})
        self.trades = backtest_result.get('trades', [])

    def generate_html_report(self, output_path="backtest_report.html"):
        """
        Generate interactive HTML report with Plotly charts

        Args:
            output_path: Path to save HTML file

        Returns:
            Path to generated report
        """
        if not PLOTLY_AVAILABLE:
            print("❌ Plotly not installed. Cannot generate HTML report.")
            return None

        # Create subplots
        fig = make_subplots(
            rows=3, cols=2,
            subplot_titles=(
                'Equity Curve',
                'Drawdown Underwater Chart',
                'Monthly Returns Heatmap',
                'Trade Distribution',
                'Win/Loss Analysis',
                'Performance Metrics'
            ),
            specs=[
                [{"secondary_y": False}, {"secondary_y": False}],
                [{"type": "heatmap"}, {"type": "bar"}],
                [{"type": "pie"}, {"type": "table"}]
            ],
            row_heights=[0.4, 0.3, 0.3],
            vertical_spacing=0.08,
            horizontal_spacing=0.12
        )

        # 1. Equity Curve
        equity = self.portfolio.equity_curve()
        dates = equity.index if isinstance(equity, pd.Series) else range(len(equity))

        fig.add_trace(
            go.Scatter(
                x=dates,
                y=equity,
                mode='lines',
                name='Equity',
                line=dict(color='#00FF41', width=2),
                hovertemplate='<b>%{x}</b><br>Equity: $%{y:,.2f}<extra></extra>'
            ),
            row=1, col=1
        )

        # 2. Drawdown Chart
        drawdown = self._calculate_drawdown(equity)
        fig.add_trace(
            go.Scatter(
                x=dates,
                y=drawdown * 100,
                mode='lines',
                name='Drawdown',
                fill='tozeroy',
                line=dict(color='#FF0000', width=1),
                hovertemplate='<b>%{x}</b><br>Drawdown: %{y:.2f}%<extra></extra>'
            ),
            row=1, col=2
        )

        # 3. Monthly Returns Heatmap (if we have date index)
        if isinstance(equity, pd.Series) and isinstance(equity.index, pd.DatetimeIndex):
            monthly_returns = self._calculate_monthly_returns(equity)
            if monthly_returns is not None:
                fig.add_trace(
                    go.Heatmap(
                        z=monthly_returns.values,
                        x=monthly_returns.columns,
                        y=monthly_returns.index,
                        colorscale='RdYlGn',
                        text=monthly_returns.values,
                        texttemplate='%{text:.1f}%',
                        hovertemplate='%{y} %{x}<br>Return: %{z:.2f}%<extra></extra>'
                    ),
                    row=2, col=1
                )

        # 4. Trade Distribution
        if self.trades:
            pnl_values = [t.get('pnl', 0) for t in self.trades]
            fig.add_trace(
                go.Histogram(
                    x=pnl_values,
                    nbinsx=30,
                    name='Trade P&L',
                    marker_color='#00FF41',
                    hovertemplate='P&L: $%{x:,.2f}<br>Count: %{y}<extra></extra>'
                ),
                row=2, col=2
            )

        # 5. Win/Loss Pie Chart
        if self.trades:
            wins = sum(1 for t in self.trades if t.get('pnl', 0) > 0)
            losses = sum(1 for t in self.trades if t.get('pnl', 0) < 0)

            fig.add_trace(
                go.Pie(
                    labels=['Wins', 'Losses'],
                    values=[wins, losses],
                    marker_colors=['#00FF41', '#FF0000'],
                    hovertemplate='<b>%{label}</b><br>Count: %{value}<br>%{percent}<extra></extra>'
                ),
                row=3, col=1
            )

        # 6. Performance Metrics Table
        metrics_data = [
            ['Total Return', f"{self.metrics.get('total_return', 0):.2f}%"],
            ['Sharpe Ratio', f"{self.metrics.get('sharpe_ratio', 0):.2f}"],
            ['Max Drawdown', f"{self.metrics.get('max_drawdown', 0):.2f}%"],
            ['Win Rate', f"{self.metrics.get('win_rate', 0):.2f}%"],
            ['Profit Factor', f"{self.metrics.get('profit_factor', 0):.2f}"],
            ['Total Trades', f"{self.metrics.get('total_trades', 0)}"],
        ]

        fig.add_trace(
            go.Table(
                header=dict(
                    values=['<b>Metric</b>', '<b>Value</b>'],
                    fill_color='#1a1a1a',
                    align='left',
                    font=dict(color='#00FF41', size=12)
                ),
                cells=dict(
                    values=list(zip(*metrics_data)),
                    fill_color='#0a0a0a',
                    align='left',
                    font=dict(color='white', size=11),
                    height=25
                )
            ),
            row=3, col=2
        )

        # Update layout
        fig.update_layout(
            title=dict(
                text=f"<b>{self.strategy_name} - Backtest Report</b>",
                x=0.5,
                xanchor='center',
                font=dict(size=24, color='#00FF41')
            ),
            showlegend=False,
            height=1400,
            plot_bgcolor='#0a0a0a',
            paper_bgcolor='#000000',
            font=dict(color='white', family='monospace'),
            hovermode='x unified'
        )

        # Update axes
        fig.update_xaxes(showgrid=True, gridwidth=1, gridcolor='#1a1a1a')
        fig.update_yaxes(showgrid=True, gridwidth=1, gridcolor='#1a1a1a')

        # Save report
        output_path = Path(output_path)
        fig.write_html(str(output_path))

        print(f"✅ HTML report saved: {output_path}")
        return output_path

    def generate_excel_report(self, output_path="backtest_report.xlsx"):
        """
        Generate Excel report with formatted tables

        Args:
            output_path: Path to save Excel file

        Returns:
            Path to generated report
        """
        if not EXCEL_AVAILABLE:
            print("❌ openpyxl not installed. Cannot generate Excel report.")
            return None

        output_path = Path(output_path)

        # Create Excel writer
        with pd.ExcelWriter(output_path, engine='openpyxl') as writer:
            # Sheet 1: Summary
            summary_df = self._create_summary_dataframe()
            summary_df.to_excel(writer, sheet_name='Summary', index=False)

            # Sheet 2: Trade Log
            if self.trades:
                trades_df = pd.DataFrame(self.trades)
                trades_df.to_excel(writer, sheet_name='Trade Log', index=False)

            # Sheet 3: Equity Curve
            equity = self.portfolio.equity_curve()
            equity_df = pd.DataFrame({'Equity': equity})
            equity_df.to_excel(writer, sheet_name='Equity Curve')

            # Sheet 4: Monthly Returns (if applicable)
            if isinstance(equity, pd.Series) and isinstance(equity.index, pd.DatetimeIndex):
                monthly_returns = self._calculate_monthly_returns(equity)
                if monthly_returns is not None:
                    monthly_returns.to_excel(writer, sheet_name='Monthly Returns')

            # Format workbook
            workbook = writer.book
            self._format_excel_workbook(workbook)

        print(f"✅ Excel report saved: {output_path}")
        return output_path

    def _create_summary_dataframe(self):
        """Create summary DataFrame for Excel"""
        data = {
            'Metric': [
                'Strategy Name',
                'Start Date',
                'End Date',
                'Initial Capital',
                'Final Equity',
                'Total Return (%)',
                'Annual Return (%)',
                'Sharpe Ratio',
                'Sortino Ratio',
                'Max Drawdown (%)',
                'Win Rate (%)',
                'Profit Factor',
                'Total Trades',
                'Winning Trades',
                'Losing Trades',
                'Avg Win ($)',
                'Avg Loss ($)',
                'Largest Win ($)',
                'Largest Loss ($)',
            ],
            'Value': [
                self.strategy_name,
                str(self.result.get('start_date', 'N/A')),
                str(self.result.get('end_date', 'N/A')),
                f"${self.result.get('initial_capital', 0):,.2f}",
                f"${self.portfolio.get_equity():,.2f}",
                f"{self.metrics.get('total_return', 0):.2f}",
                f"{self.metrics.get('annual_return', 0):.2f}",
                f"{self.metrics.get('sharpe_ratio', 0):.3f}",
                f"{self.metrics.get('sortino_ratio', 0):.3f}",
                f"{self.metrics.get('max_drawdown', 0):.2f}",
                f"{self.metrics.get('win_rate', 0):.2f}",
                f"{self.metrics.get('profit_factor', 0):.2f}",
                self.metrics.get('total_trades', 0),
                self.metrics.get('winning_trades', 0),
                self.metrics.get('losing_trades', 0),
                f"${self.metrics.get('avg_win', 0):,.2f}",
                f"${self.metrics.get('avg_loss', 0):,.2f}",
                f"${self.metrics.get('largest_win', 0):,.2f}",
                f"${self.metrics.get('largest_loss', 0):,.2f}",
            ]
        }
        return pd.DataFrame(data)

    def _format_excel_workbook(self, workbook):
        """Apply formatting to Excel workbook"""
        # Header style
        header_fill = PatternFill(start_color="00FF41", end_color="00FF41", fill_type="solid")
        header_font = Font(bold=True, color="000000")

        for sheet_name in workbook.sheetnames:
            sheet = workbook[sheet_name]

            # Format headers (first row)
            for cell in sheet[1]:
                cell.fill = header_fill
                cell.font = header_font
                cell.alignment = Alignment(horizontal='center', vertical='center')

            # Auto-adjust column widths
            for column in sheet.columns:
                max_length = 0
                column_letter = column[0].column_letter
                for cell in column:
                    try:
                        if len(str(cell.value)) > max_length:
                            max_length = len(str(cell.value))
                    except:
                        pass
                adjusted_width = min(max_length + 2, 50)
                sheet.column_dimensions[column_letter].width = adjusted_width

    def _calculate_drawdown(self, equity):
        """Calculate drawdown series"""
        if isinstance(equity, pd.Series):
            peak = equity.expanding().max()
            drawdown = (equity - peak) / peak
        else:
            equity_arr = np.array(equity)
            peak = np.maximum.accumulate(equity_arr)
            drawdown = np.divide(equity_arr - peak, peak, where=peak != 0, out=np.zeros_like(peak))

        return drawdown

    def _calculate_monthly_returns(self, equity):
        """Calculate monthly returns matrix for heatmap"""
        if not isinstance(equity, pd.Series) or not isinstance(equity.index, pd.DatetimeIndex):
            return None

        try:
            # Resample to monthly
            monthly_equity = equity.resample('ME').last()
            monthly_returns = monthly_equity.pct_change() * 100

            # Pivot to matrix format (years x months)
            monthly_returns_df = monthly_returns.to_frame('returns')
            monthly_returns_df['year'] = monthly_returns.index.year
            monthly_returns_df['month'] = monthly_returns.index.strftime('%b')

            pivot = monthly_returns_df.pivot_table(
                values='returns',
                index='year',
                columns='month',
                aggfunc='sum'
            )

            # Reorder months
            month_order = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun',
                          'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
            pivot = pivot.reindex(columns=month_order, fill_value=0)

            return pivot
        except Exception as e:
            print(f"⚠️  Could not calculate monthly returns: {e}")
            return None

    def generate_all_reports(self, output_dir="reports"):
        """
        Generate all report types

        Args:
            output_dir: Directory to save reports

        Returns:
            Dict of generated file paths
        """
        output_dir = Path(output_dir)
        output_dir.mkdir(exist_ok=True)

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        base_name = f"{self.strategy_name}_{timestamp}"

        results = {}

        # HTML report
        html_path = output_dir / f"{base_name}.html"
        results['html'] = self.generate_html_report(html_path)

        # Excel report
        excel_path = output_dir / f"{base_name}.xlsx"
        results['excel'] = self.generate_excel_report(excel_path)

        return results


def generate_report(backtest_result, strategy_name="Strategy", output_dir="reports"):
    """
    Convenience function to generate all reports

    Args:
        backtest_result: Result dict from BacktestRunner
        strategy_name: Name of strategy
        output_dir: Output directory

    Returns:
        Dict of generated file paths
    """
    generator = ReportGenerator(backtest_result, strategy_name)
    return generator.generate_all_reports(output_dir)
