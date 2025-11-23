"""
Advanced Performance Metrics - Sharpe, Sortino, Calmar, etc.
"""

import numpy as np
from typing import List, Dict


class AdvancedMetrics:
    """
    Calculate advanced risk-adjusted performance metrics
    """

    @staticmethod
    def sharpe_ratio(returns: List[float], risk_free_rate: float = 0.02) -> float:
        """
        Calculate Sharpe Ratio

        Args:
            returns: List of period returns (daily/monthly)
            risk_free_rate: Annual risk-free rate (default: 2%)

        Returns:
            Sharpe ratio (annualized)
        """
        if not returns or len(returns) < 2:
            return 0.0

        returns_array = np.array(returns)

        # Assume daily returns, convert risk-free rate to daily
        daily_rf = (1 + risk_free_rate) ** (1 / 252) - 1

        excess_returns = returns_array - daily_rf
        avg_excess = np.mean(excess_returns)
        std_returns = np.std(excess_returns, ddof=1)

        if std_returns == 0:
            return 0.0

        # Annualize
        sharpe = (avg_excess / std_returns) * np.sqrt(252)

        return sharpe

    @staticmethod
    def sortino_ratio(returns: List[float], risk_free_rate: float = 0.02,
                     target_return: float = 0.0) -> float:
        """
        Calculate Sortino Ratio (downside deviation)

        Args:
            returns: List of period returns
            risk_free_rate: Annual risk-free rate
            target_return: Target return threshold

        Returns:
            Sortino ratio (annualized)
        """
        if not returns or len(returns) < 2:
            return 0.0

        returns_array = np.array(returns)

        daily_rf = (1 + risk_free_rate) ** (1 / 252) - 1
        excess_returns = returns_array - daily_rf

        # Downside deviation (only negative returns)
        downside_returns = excess_returns[excess_returns < target_return]

        if len(downside_returns) == 0:
            return np.inf if np.mean(excess_returns) > 0 else 0.0

        downside_std = np.std(downside_returns, ddof=1)

        if downside_std == 0:
            return 0.0

        avg_excess = np.mean(excess_returns)

        # Annualize
        sortino = (avg_excess / downside_std) * np.sqrt(252)

        return sortino

    @staticmethod
    def calmar_ratio(total_return: float, max_drawdown: float, years: float = 1.0) -> float:
        """
        Calculate Calmar Ratio (return / max drawdown)

        Args:
            total_return: Total return percentage
            max_drawdown: Maximum drawdown percentage
            years: Number of years in period

        Returns:
            Calmar ratio
        """
        if max_drawdown == 0:
            return np.inf if total_return > 0 else 0.0

        # Annualize return
        annualized_return = ((1 + total_return / 100) ** (1 / years) - 1) * 100

        calmar = annualized_return / max_drawdown

        return calmar

    @staticmethod
    def calculate_returns_series(equity_curve: List[Dict]) -> List[float]:
        """
        Calculate period returns from equity curve

        Args:
            equity_curve: List of equity points with 'equity' key

        Returns:
            List of period returns (decimal)
        """
        if len(equity_curve) < 2:
            return []

        returns = []
        for i in range(1, len(equity_curve)):
            prev_equity = equity_curve[i - 1]['equity']
            curr_equity = equity_curve[i]['equity']

            if prev_equity == 0:
                continue

            period_return = (curr_equity - prev_equity) / prev_equity
            returns.append(period_return)

        return returns

    @staticmethod
    def max_consecutive_losses(trades: List) -> int:
        """Calculate maximum consecutive losing trades"""
        if not trades:
            return 0

        max_streak = 0
        current_streak = 0

        for trade in trades:
            if trade.pnl < 0:
                current_streak += 1
                max_streak = max(max_streak, current_streak)
            else:
                current_streak = 0

        return max_streak

    @staticmethod
    def profit_factor(winning_trades: List, losing_trades: List) -> float:
        """
        Calculate profit factor (gross profit / gross loss)

        Args:
            winning_trades: List of winning trades
            losing_trades: List of losing trades

        Returns:
            Profit factor
        """
        if not winning_trades and not losing_trades:
            return 0.0

        gross_profit = sum(abs(t.pnl) for t in winning_trades) if winning_trades else 0
        gross_loss = sum(abs(t.pnl) for t in losing_trades) if losing_trades else 0

        if gross_loss == 0:
            return np.inf if gross_profit > 0 else 0.0

        return gross_profit / gross_loss
