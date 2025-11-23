"""
Metrics Calculator - Performance analysis
"""

from typing import List, Dict
from encom.engine.portfolio import Portfolio
from encom.analytics.advanced_metrics import AdvancedMetrics


class MetricsCalculator:
    """
    Calculate backtest performance metrics
    Clean, focused on essential metrics only
    """

    def __init__(self, portfolio: Portfolio):
        self.portfolio = portfolio

    def calculate_all(self) -> Dict:
        """Calculate all metrics"""
        equity_curve = self.portfolio.equity_curve
        summary = self.portfolio.get_summary()

        if not equity_curve:
            return self._empty_metrics()

        initial_equity = self.portfolio.initial_cash
        final_equity = equity_curve[-1]['equity']

        total_return = ((final_equity - initial_equity) / initial_equity) * 100

        max_dd = self._calculate_max_drawdown(equity_curve)

        # Calculate advanced metrics
        returns_series = AdvancedMetrics.calculate_returns_series(equity_curve)
        sharpe = AdvancedMetrics.sharpe_ratio(returns_series) if returns_series else 0.0
        sortino = AdvancedMetrics.sortino_ratio(returns_series) if returns_series else 0.0

        # Estimate backtest duration in years
        if len(equity_curve) > 1:
            days = len(equity_curve)
            years = days / 252  # Trading days per year
        else:
            years = 1.0

        calmar = AdvancedMetrics.calmar_ratio(total_return, max_dd, years)

        # Profit factor
        closed_trades = self.portfolio.get_closed_trades()
        winning = [t for t in closed_trades if t.pnl > 0]
        losing = [t for t in closed_trades if t.pnl <= 0]
        profit_factor = AdvancedMetrics.profit_factor(winning, losing)

        return {
            # Returns
            'initial_capital': initial_equity,
            'final_equity': final_equity,
            'total_return': total_return,
            'total_pnl': final_equity - initial_equity,

            # Trade Stats
            'total_trades': summary['total_trades'],
            'winning_trades': summary['winning_trades'],
            'losing_trades': summary['losing_trades'],
            'win_rate': summary['win_rate'],
            'avg_win': summary['avg_win'],
            'avg_loss': summary['avg_loss'],

            # Risk Metrics
            'max_drawdown': max_dd,
            'sharpe_ratio': sharpe,
            'sortino_ratio': sortino,
            'calmar_ratio': calmar,
            'profit_factor': profit_factor,

            # Summary
            'profitable': total_return > 0
        }

    def _calculate_max_drawdown(self, equity_curve: List[Dict]) -> float:
        """Calculate maximum drawdown percentage"""
        if not equity_curve:
            return 0.0

        peak = equity_curve[0]['equity']
        max_dd = 0.0

        for point in equity_curve:
            equity = point['equity']

            if equity > peak:
                peak = equity

            dd = ((peak - equity) / peak) * 100
            if dd > max_dd:
                max_dd = dd

        return max_dd

    def _empty_metrics(self) -> Dict:
        """Return empty metrics"""
        return {
            'initial_capital': self.portfolio.initial_cash,
            'final_equity': self.portfolio.initial_cash,
            'total_return': 0.0,
            'total_pnl': 0.0,
            'total_trades': 0,
            'winning_trades': 0,
            'losing_trades': 0,
            'win_rate': 0.0,
            'avg_win': 0.0,
            'avg_loss': 0.0,
            'max_drawdown': 0.0,
            'sharpe_ratio': 0.0,
            'sortino_ratio': 0.0,
            'calmar_ratio': 0.0,
            'profit_factor': 0.0,
            'profitable': False
        }

    def print_report(self, symbol: str, start_date: str, end_date: str):
        """Print formatted backtest report"""
        metrics = self.calculate_all()

        print("\n" + "="*50)
        print("ENCOM BACKTEST RESULTS")
        print("="*50)
        print(f"Symbol: {symbol}")
        print(f"Period: {start_date} to {end_date}")
        print()

        print("PERFORMANCE:")
        print(f"  Initial Capital: ${metrics['initial_capital']:,.2f}")
        print(f"  Final Equity:    ${metrics['final_equity']:,.2f}")
        print(f"  Total Return:    {metrics['total_return']:+.2f}%")
        print(f"  Total P&L:       ${metrics['total_pnl']:+,.2f}")
        print()

        print("TRADE STATISTICS:")
        print(f"  Total Trades:    {metrics['total_trades']}")
        print(f"  Winning Trades:  {metrics['winning_trades']}")
        print(f"  Losing Trades:   {metrics['losing_trades']}")
        print(f"  Win Rate:        {metrics['win_rate']:.1f}%")
        if metrics['total_trades'] > 0:
            print(f"  Avg Win:         {metrics['avg_win']:+.2f}%")
            print(f"  Avg Loss:        {metrics['avg_loss']:+.2f}%")
        print()

        print("RISK METRICS:")
        print(f"  Max Drawdown:    {metrics['max_drawdown']:.2f}%")
        if metrics.get('sharpe_ratio'):
            print(f"  Sharpe Ratio:    {metrics['sharpe_ratio']:.2f}")
        if metrics.get('sortino_ratio'):
            print(f"  Sortino Ratio:   {metrics['sortino_ratio']:.2f}")
        if metrics.get('calmar_ratio') and abs(metrics['calmar_ratio']) < 999:
            print(f"  Calmar Ratio:    {metrics['calmar_ratio']:.2f}")
        if metrics.get('profit_factor') and metrics['profit_factor'] < 999:
            print(f"  Profit Factor:   {metrics['profit_factor']:.2f}")
        print()

        print("="*50)
        if metrics['profitable']:
            print("✅ PROFITABLE STRATEGY")
        else:
            print("❌ UNPROFITABLE STRATEGY")
        print("="*50)
        print("\nEnd of Line. 🎮\n")
