"""
Advanced Performance Analytics for ENCOM

Professional trade analysis including:
- MAE (Maximum Adverse Excursion)
- MFE (Maximum Favorable Excursion)
- Performance Attribution
- Trade Efficiency Analysis
- Risk-Adjusted Returns

Author: ENCOM Development Team
License: MIT
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass


@dataclass
class TradeAnalysis:
    """Container for individual trade analysis"""
    entry_date: str
    exit_date: str
    direction: str  # 'long' or 'short'
    entry_price: float
    exit_price: float
    shares: int
    pnl: float
    return_pct: float
    mae: float  # Maximum Adverse Excursion
    mfe: float  # Maximum Favorable Excursion
    mae_pct: float  # MAE as % of entry
    mfe_pct: float  # MFE as % of entry
    efficiency: float  # MFE / MAE ratio
    hold_days: int


class AdvancedAnalytics:
    """
    Advanced performance analytics for professional traders

    Analyzes trades to identify:
    - Optimal exit points (MFE analysis)
    - Stop-loss levels (MAE analysis)
    - Trade efficiency (capturing favorable moves)
    - Performance attribution (by signal, time, market condition)
    """

    def __init__(self, trades: List[Dict], equity_curve: pd.Series, market_data: pd.DataFrame):
        """
        Args:
            trades: List of trade dicts from backtest
            equity_curve: Equity curve series
            market_data: OHLCV market data
        """
        self.trades = trades
        self.equity_curve = equity_curve
        self.market_data = market_data

    def calculate_mae_mfe(self) -> List[TradeAnalysis]:
        """
        Calculate MAE/MFE for all trades

        MAE = Maximum loss during trade (how deep did it go against you)
        MFE = Maximum profit during trade (best possible exit)

        Returns:
            List of TradeAnalysis objects with MAE/MFE data
        """
        trade_analyses = []

        for trade in self.trades:
            # Extract trade info
            entry_date = trade.get('entry_date')
            exit_date = trade.get('exit_date')
            direction = trade.get('direction', 'long')
            entry_price = trade.get('entry_price')
            exit_price = trade.get('exit_price')
            shares = trade.get('shares', 0)

            if not all([entry_date, exit_date, entry_price, exit_price]):
                continue

            # Get price data during trade
            mask = (self.market_data.index >= entry_date) & (self.market_data.index <= exit_date)
            trade_data = self.market_data[mask]

            if len(trade_data) == 0:
                continue

            # Calculate MAE and MFE
            if direction == 'long':
                # Long trade
                # MAE = worst drawdown from entry
                # MFE = best profit from entry
                mae = entry_price - trade_data['low'].min()
                mfe = trade_data['high'].max() - entry_price

            else:
                # Short trade
                # MAE = worst drawdown (price going up)
                # MFE = best profit (price going down)
                mae = trade_data['high'].max() - entry_price
                mfe = entry_price - trade_data['low'].min()

            # Calculate percentages
            mae_pct = (mae / entry_price) * 100 if entry_price > 0 else 0
            mfe_pct = (mfe / entry_price) * 100 if entry_price > 0 else 0

            # Trade efficiency (how much of MFE was captured)
            pnl = trade.get('pnl', 0)
            actual_gain = abs(exit_price - entry_price)

            if mfe > 0:
                efficiency = (actual_gain / mfe) * 100
            else:
                efficiency = 0

            # Hold days
            if isinstance(entry_date, str):
                entry_date = pd.to_datetime(entry_date)
            if isinstance(exit_date, str):
                exit_date = pd.to_datetime(exit_date)

            hold_days = (exit_date - entry_date).days

            trade_analyses.append(TradeAnalysis(
                entry_date=str(entry_date),
                exit_date=str(exit_date),
                direction=direction,
                entry_price=entry_price,
                exit_price=exit_price,
                shares=shares,
                pnl=pnl,
                return_pct=trade.get('return_pct', 0),
                mae=mae,
                mfe=mfe,
                mae_pct=mae_pct,
                mfe_pct=mfe_pct,
                efficiency=efficiency,
                hold_days=hold_days
            ))

        return trade_analyses

    def get_mae_mfe_summary(self) -> Dict:
        """
        Get summary statistics for MAE/MFE

        Returns:
            Dict with summary metrics
        """
        analyses = self.calculate_mae_mfe()

        if not analyses:
            return {}

        maes = [a.mae for a in analyses]
        mfes = [a.mfe for a in analyses]
        mae_pcts = [a.mae_pct for a in analyses]
        mfe_pcts = [a.mfe_pct for a in analyses]
        efficiencies = [a.efficiency for a in analyses]

        # Winning vs losing trades
        winning_trades = [a for a in analyses if a.pnl > 0]
        losing_trades = [a for a in analyses if a.pnl <= 0]

        summary = {
            'total_trades': len(analyses),
            'winning_trades': len(winning_trades),
            'losing_trades': len(losing_trades),

            # MAE statistics
            'avg_mae': np.mean(maes),
            'max_mae': np.max(maes),
            'avg_mae_pct': np.mean(mae_pcts),
            'max_mae_pct': np.max(mae_pcts),

            # MFE statistics
            'avg_mfe': np.mean(mfes),
            'max_mfe': np.max(mfes),
            'avg_mfe_pct': np.mean(mfe_pcts),
            'max_mfe_pct': np.max(mfe_pcts),

            # Efficiency
            'avg_efficiency': np.mean(efficiencies),
            'avg_efficiency_winners': np.mean([a.efficiency for a in winning_trades]) if winning_trades else 0,
            'avg_efficiency_losers': np.mean([a.efficiency for a in losing_trades]) if losing_trades else 0,

            # Winners vs Losers
            'avg_mae_winners': np.mean([a.mae for a in winning_trades]) if winning_trades else 0,
            'avg_mfe_winners': np.mean([a.mfe for a in winning_trades]) if winning_trades else 0,
            'avg_mae_losers': np.mean([a.mae for a in losing_trades]) if losing_trades else 0,
            'avg_mfe_losers': np.mean([a.mfe for a in losing_trades]) if losing_trades else 0,
        }

        return summary

    def get_optimal_stop_loss(self, percentile: float = 75) -> float:
        """
        Calculate optimal stop-loss based on MAE

        Args:
            percentile: Percentile of MAE to use (75 = 75th percentile)

        Returns:
            Optimal stop-loss as % of entry price
        """
        analyses = self.calculate_mae_mfe()

        if not analyses:
            return 0

        # Get MAE for winning trades only (we want to avoid stops that would have stopped us out of winners)
        winning_trades = [a for a in analyses if a.pnl > 0]

        if not winning_trades:
            return 0

        mae_pcts = [a.mae_pct for a in winning_trades]

        # Use percentile (e.g., 75th percentile means 75% of winning trades had MAE below this)
        optimal_stop = np.percentile(mae_pcts, percentile)

        return optimal_stop

    def get_optimal_take_profit(self, percentile: float = 50) -> float:
        """
        Calculate optimal take-profit based on MFE

        Args:
            percentile: Percentile of MFE to use (50 = median)

        Returns:
            Optimal take-profit as % of entry price
        """
        analyses = self.calculate_mae_mfe()

        if not analyses:
            return 0

        # Get MFE for all trades
        mfe_pcts = [a.mfe_pct for a in analyses]

        # Use percentile
        optimal_tp = np.percentile(mfe_pcts, percentile)

        return optimal_tp

    def get_performance_attribution(self) -> Dict:
        """
        Attribute performance to different factors

        Returns:
            Dict with performance attribution
        """
        if not self.trades:
            return {}

        total_pnl = sum(t.get('pnl', 0) for t in self.trades)

        # By direction
        long_trades = [t for t in self.trades if t.get('direction') == 'long']
        short_trades = [t for t in self.trades if t.get('direction') == 'short']

        long_pnl = sum(t.get('pnl', 0) for t in long_trades)
        short_pnl = sum(t.get('pnl', 0) for t in short_trades)

        # By month (if dates available)
        monthly_pnl = {}
        for trade in self.trades:
            exit_date = trade.get('exit_date')
            if exit_date:
                if isinstance(exit_date, str):
                    exit_date = pd.to_datetime(exit_date)
                month = exit_date.strftime('%Y-%m')
                monthly_pnl[month] = monthly_pnl.get(month, 0) + trade.get('pnl', 0)

        # By trade size
        small_trades = [t for t in self.trades if t.get('shares', 0) < 50]
        medium_trades = [t for t in self.trades if 50 <= t.get('shares', 0) < 200]
        large_trades = [t for t in self.trades if t.get('shares', 0) >= 200]

        attribution = {
            'total_pnl': total_pnl,

            'by_direction': {
                'long': {
                    'trades': len(long_trades),
                    'pnl': long_pnl,
                    'contribution_pct': (long_pnl / total_pnl * 100) if total_pnl != 0 else 0
                },
                'short': {
                    'trades': len(short_trades),
                    'pnl': short_pnl,
                    'contribution_pct': (short_pnl / total_pnl * 100) if total_pnl != 0 else 0
                }
            },

            'by_month': monthly_pnl,

            'by_size': {
                'small': {'trades': len(small_trades), 'pnl': sum(t.get('pnl', 0) for t in small_trades)},
                'medium': {'trades': len(medium_trades), 'pnl': sum(t.get('pnl', 0) for t in medium_trades)},
                'large': {'trades': len(large_trades), 'pnl': sum(t.get('pnl', 0) for t in large_trades)}
            }
        }

        return attribution

    def get_trade_efficiency_report(self) -> Dict:
        """
        Analyze trade efficiency (how well did we capture favorable moves)

        Returns:
            Dict with efficiency metrics
        """
        analyses = self.calculate_mae_mfe()

        if not analyses:
            return {}

        # Categorize by efficiency
        highly_efficient = [a for a in analyses if a.efficiency >= 70]
        moderately_efficient = [a for a in analyses if 30 <= a.efficiency < 70]
        poorly_efficient = [a for a in analyses if a.efficiency < 30]

        # Winners vs Losers efficiency
        winners = [a for a in analyses if a.pnl > 0]
        losers = [a for a in analyses if a.pnl <= 0]

        report = {
            'overall_efficiency': np.mean([a.efficiency for a in analyses]),

            'by_category': {
                'highly_efficient': {
                    'count': len(highly_efficient),
                    'pct': (len(highly_efficient) / len(analyses)) * 100,
                    'avg_pnl': np.mean([a.pnl for a in highly_efficient]) if highly_efficient else 0
                },
                'moderately_efficient': {
                    'count': len(moderately_efficient),
                    'pct': (len(moderately_efficient) / len(analyses)) * 100,
                    'avg_pnl': np.mean([a.pnl for a in moderately_efficient]) if moderately_efficient else 0
                },
                'poorly_efficient': {
                    'count': len(poorly_efficient),
                    'pct': (len(poorly_efficient) / len(analyses)) * 100,
                    'avg_pnl': np.mean([a.pnl for a in poorly_efficient]) if poorly_efficient else 0
                }
            },

            'winners_vs_losers': {
                'winners_efficiency': np.mean([a.efficiency for a in winners]) if winners else 0,
                'losers_efficiency': np.mean([a.efficiency for a in losers]) if losers else 0
            },

            'insights': self._generate_efficiency_insights(analyses)
        }

        return report

    def _generate_efficiency_insights(self, analyses: List[TradeAnalysis]) -> List[str]:
        """Generate actionable insights from efficiency analysis"""
        insights = []

        if not analyses:
            return insights

        avg_efficiency = np.mean([a.efficiency for a in analyses])

        if avg_efficiency < 40:
            insights.append("⚠️  Low trade efficiency (<40%) - Consider tightening take-profit targets")

        winners = [a for a in analyses if a.pnl > 0]
        if winners:
            avg_winner_efficiency = np.mean([a.efficiency for a in winners])
            if avg_winner_efficiency < 50:
                insights.append("⚠️  Winning trades not capturing enough of favorable moves - Exit strategy may be too conservative")

        # Check if we're exiting winners too early
        early_exits = [a for a in winners if a.efficiency < 30]
        if len(early_exits) / len(analyses) > 0.3:
            insights.append("⚠️  >30% of trades exited too early - Consider trailing stops or wider targets")

        # Check MAE vs MFE ratio
        avg_mae = np.mean([a.mae_pct for a in analyses])
        avg_mfe = np.mean([a.mfe_pct for a in analyses])

        if avg_mae > avg_mfe * 0.8:
            insights.append("⚠️  MAE approaching MFE - Risk management may need improvement")

        return insights

    def get_risk_adjusted_metrics(self) -> Dict:
        """
        Calculate advanced risk-adjusted performance metrics

        Returns:
            Dict with risk-adjusted metrics
        """
        if not isinstance(self.equity_curve, pd.Series) or len(self.equity_curve) == 0:
            return {}

        # Calculate returns
        returns = self.equity_curve.pct_change().dropna()

        # Downside returns (only negative)
        downside_returns = returns[returns < 0]

        # Metrics
        metrics = {
            # Basic
            'total_return_pct': ((self.equity_curve.iloc[-1] / self.equity_curve.iloc[0]) - 1) * 100,
            'volatility': returns.std() * np.sqrt(252) * 100,  # Annualized

            # Sharpe Ratio (assume 2% risk-free rate)
            'sharpe_ratio': ((returns.mean() * 252) - 0.02) / (returns.std() * np.sqrt(252)) if returns.std() > 0 else 0,

            # Sortino Ratio (downside deviation)
            'sortino_ratio': ((returns.mean() * 252) - 0.02) / (downside_returns.std() * np.sqrt(252)) if len(downside_returns) > 0 and downside_returns.std() > 0 else 0,

            # Calmar Ratio (return / max drawdown)
            'calmar_ratio': self._calculate_calmar_ratio(returns),

            # Omega Ratio
            'omega_ratio': self._calculate_omega_ratio(returns),

            # Information Ratio (if benchmark available)
            'information_ratio': 0,  # Would need benchmark

            # Kurtosis & Skewness
            'skewness': returns.skew(),
            'kurtosis': returns.kurtosis(),
        }

        return metrics

    def _calculate_calmar_ratio(self, returns: pd.Series) -> float:
        """Calculate Calmar Ratio"""
        if len(returns) == 0:
            return 0

        # Annualized return
        annual_return = returns.mean() * 252

        # Max drawdown
        cumulative = (1 + returns).cumprod()
        running_max = cumulative.expanding().max()
        drawdown = (cumulative - running_max) / running_max
        max_dd = abs(drawdown.min())

        if max_dd == 0:
            return 0

        return annual_return / max_dd

    def _calculate_omega_ratio(self, returns: pd.Series, threshold: float = 0.0) -> float:
        """Calculate Omega Ratio"""
        if len(returns) == 0:
            return 0

        # Gains vs losses above/below threshold
        gains = returns[returns > threshold].sum()
        losses = abs(returns[returns <= threshold].sum())

        if losses == 0:
            return np.inf if gains > 0 else 0

        return gains / losses


# Convenience function
def analyze_trades(backtest_result: Dict) -> Dict:
    """
    Comprehensive trade analysis

    Args:
        backtest_result: Result dict from BacktestRunner

    Returns:
        Dict with all analytics
    """
    trades = backtest_result.get('trades', [])
    portfolio = backtest_result.get('portfolio')

    if not trades or not portfolio:
        return {}

    equity_curve = portfolio.equity_curve()
    market_data = backtest_result.get('data')  # Would need to pass this

    if market_data is None:
        return {}

    analytics = AdvancedAnalytics(trades, equity_curve, market_data)

    return {
        'mae_mfe_summary': analytics.get_mae_mfe_summary(),
        'optimal_stop_loss': analytics.get_optimal_stop_loss(),
        'optimal_take_profit': analytics.get_optimal_take_profit(),
        'performance_attribution': analytics.get_performance_attribution(),
        'trade_efficiency': analytics.get_trade_efficiency_report(),
        'risk_adjusted_metrics': analytics.get_risk_adjusted_metrics()
    }
