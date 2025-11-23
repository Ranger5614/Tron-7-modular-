"""
Advanced Position Sizing Algorithms for ENCOM

Professional risk management and capital allocation strategies.

Author: ENCOM Development Team
License: MIT
"""

import numpy as np
from typing import Dict, List, Optional
from dataclasses import dataclass


@dataclass
class PositionSize:
    """Container for position size calculation"""
    shares: int
    capital_allocation: float
    risk_amount: float
    risk_percent: float
    stop_loss_distance: Optional[float] = None


class PositionSizer:
    """
    Advanced position sizing algorithms

    Algorithms:
    - Fixed Dollar: Fixed $ amount per trade
    - Fixed Percent: Fixed % of capital per trade
    - Volatility-Based: Size based on ATR/volatility
    - Kelly Criterion: Optimal bet size based on edge
    - Risk Percent: Size based on stop loss distance
    - Equal Weight: Equal allocation across positions
    """

    def __init__(self, total_capital: float, max_position_size: float = 0.20):
        """
        Args:
            total_capital: Total portfolio capital
            max_position_size: Maximum position size as fraction of capital (0.20 = 20%)
        """
        self.total_capital = total_capital
        self.max_position_size = max_position_size

    def fixed_dollar(self, dollar_amount: float, price: float) -> PositionSize:
        """
        Fixed Dollar Amount per trade

        Args:
            dollar_amount: Dollar amount to allocate
            price: Current price per share

        Returns:
            PositionSize
        """
        # Apply max position size constraint
        max_capital = self.total_capital * self.max_position_size
        capital = min(dollar_amount, max_capital)

        shares = int(capital / price) if price > 0 else 0
        actual_capital = shares * price

        return PositionSize(
            shares=shares,
            capital_allocation=actual_capital,
            risk_amount=0,  # No explicit risk
            risk_percent=0
        )

    def fixed_percent(self, percent: float, price: float) -> PositionSize:
        """
        Fixed Percent of capital per trade

        Args:
            percent: Percent of capital (0.05 = 5%)
            price: Current price per share

        Returns:
            PositionSize
        """
        # Apply max position size constraint
        allocation_pct = min(percent, self.max_position_size)
        capital = self.total_capital * allocation_pct

        shares = int(capital / price) if price > 0 else 0
        actual_capital = shares * price

        return PositionSize(
            shares=shares,
            capital_allocation=actual_capital,
            risk_amount=0,
            risk_percent=0
        )

    def volatility_based(self, price: float, atr: float,
                        target_volatility: float = 0.01) -> PositionSize:
        """
        Volatility-Based sizing using ATR

        Adjusts position size inversely to volatility.

        Args:
            price: Current price
            atr: Average True Range (volatility measure)
            target_volatility: Target portfolio volatility (0.01 = 1%)

        Returns:
            PositionSize
        """
        if atr == 0 or price == 0:
            return PositionSize(0, 0, 0, 0)

        # Calculate position value based on target volatility
        # Position size inversely proportional to volatility
        volatility_pct = atr / price
        capital = (self.total_capital * target_volatility) / volatility_pct

        # Apply max position constraint
        max_capital = self.total_capital * self.max_position_size
        capital = min(capital, max_capital)

        shares = int(capital / price)
        actual_capital = shares * price

        return PositionSize(
            shares=shares,
            capital_allocation=actual_capital,
            risk_amount=shares * atr,
            risk_percent=(shares * atr / self.total_capital) * 100
        )

    def kelly_criterion(self, win_rate: float, avg_win: float, avg_loss: float,
                       price: float, conservative: bool = True) -> PositionSize:
        """
        Kelly Criterion - Optimal bet size

        Kelly % = W - [(1-W) / R]
        Where:
        - W = Win rate
        - R = Avg Win / Avg Loss

        Args:
            win_rate: Historical win rate (0.55 = 55%)
            avg_win: Average winning trade ($)
            avg_loss: Average losing trade ($, positive)
            price: Current price
            conservative: Use half-Kelly for safety

        Returns:
            PositionSize
        """
        if avg_loss == 0:
            return PositionSize(0, 0, 0, 0)

        # Calculate Kelly percentage
        win_loss_ratio = avg_win / avg_loss
        kelly_pct = win_rate - ((1 - win_rate) / win_loss_ratio)

        # Ensure positive
        kelly_pct = max(kelly_pct, 0)

        # Half-Kelly for safety (more conservative)
        if conservative:
            kelly_pct *= 0.5

        # Apply max position constraint
        kelly_pct = min(kelly_pct, self.max_position_size)

        # Calculate shares
        capital = self.total_capital * kelly_pct
        shares = int(capital / price) if price > 0 else 0
        actual_capital = shares * price

        return PositionSize(
            shares=shares,
            capital_allocation=actual_capital,
            risk_amount=0,
            risk_percent=kelly_pct * 100
        )

    def risk_percent(self, price: float, stop_loss_price: float,
                    risk_percent: float = 0.01) -> PositionSize:
        """
        Risk Percent - Size based on stop loss distance

        Position size calculated so that if stop is hit, you lose exactly risk_percent of capital.

        Args:
            price: Entry price
            stop_loss_price: Stop loss price
            risk_percent: Percent of capital to risk (0.01 = 1%)

        Returns:
            PositionSize
        """
        if price == 0 or price == stop_loss_price:
            return PositionSize(0, 0, 0, 0)

        # Calculate risk per share
        risk_per_share = abs(price - stop_loss_price)

        # Calculate shares to risk exactly risk_percent of capital
        risk_amount = self.total_capital * risk_percent
        shares = int(risk_amount / risk_per_share) if risk_per_share > 0 else 0

        # Apply max position constraint
        max_shares = int((self.total_capital * self.max_position_size) / price)
        shares = min(shares, max_shares)

        actual_capital = shares * price
        actual_risk = shares * risk_per_share

        return PositionSize(
            shares=shares,
            capital_allocation=actual_capital,
            risk_amount=actual_risk,
            risk_percent=(actual_risk / self.total_capital) * 100,
            stop_loss_distance=risk_per_share
        )

    def equal_weight(self, price: float, num_positions: int) -> PositionSize:
        """
        Equal Weight - Divide capital equally across N positions

        Args:
            price: Current price
            num_positions: Number of total positions

        Returns:
            PositionSize
        """
        if num_positions == 0 or price == 0:
            return PositionSize(0, 0, 0, 0)

        # Equal allocation
        capital_per_position = self.total_capital / num_positions

        # Apply max position constraint
        max_capital = self.total_capital * self.max_position_size
        capital = min(capital_per_position, max_capital)

        shares = int(capital / price)
        actual_capital = shares * price

        return PositionSize(
            shares=shares,
            capital_allocation=actual_capital,
            risk_amount=0,
            risk_percent=0
        )

    def optimal_f(self, trade_pnl_history: List[float], price: float) -> PositionSize:
        """
        Optimal F - Ralph Vince's optimal leverage

        Finds the fraction that maximizes geometric growth.

        Args:
            trade_pnl_history: List of historical trade P&Ls
            price: Current price

        Returns:
            PositionSize
        """
        if not trade_pnl_history or price == 0:
            return PositionSize(0, 0, 0, 0)

        # Find largest loss
        largest_loss = abs(min(trade_pnl_history))

        if largest_loss == 0:
            return PositionSize(0, 0, 0, 0)

        # Test different f values
        best_f = 0
        best_twrreturn = -np.inf

        for f in np.arange(0.01, 1.0, 0.01):
            twr = 1.0

            for pnl in trade_pnl_history:
                hpr = 1 + (f * pnl / largest_loss)
                if hpr <= 0:
                    twr = 0
                    break
                twr *= hpr

            if twr > best_twr:
                best_twr = twr
                best_f = f

        # Use conservative (half optimal f)
        optimal_fraction = best_f * 0.5

        # Apply max position constraint
        optimal_fraction = min(optimal_fraction, self.max_position_size)

        capital = self.total_capital * optimal_fraction
        shares = int(capital / price)
        actual_capital = shares * price

        return PositionSize(
            shares=shares,
            capital_allocation=actual_capital,
            risk_amount=0,
            risk_percent=optimal_fraction * 100
        )


class PortfolioHeatManager:
    """
    Portfolio Heat Management

    Limits total risk exposure across all positions.
    """

    def __init__(self, max_portfolio_heat: float = 0.06):
        """
        Args:
            max_portfolio_heat: Maximum total portfolio risk (0.06 = 6%)
        """
        self.max_portfolio_heat = max_portfolio_heat
        self.current_positions = {}

    def add_position(self, symbol: str, risk_amount: float):
        """Add a position and its risk"""
        self.current_positions[symbol] = risk_amount

    def remove_position(self, symbol: str):
        """Remove a position"""
        if symbol in self.current_positions:
            del self.current_positions[symbol]

    def get_current_heat(self, total_capital: float) -> float:
        """
        Get current portfolio heat (% of capital at risk)

        Args:
            total_capital: Total portfolio capital

        Returns:
            Current heat percentage (0.05 = 5%)
        """
        total_risk = sum(self.current_positions.values())
        return (total_risk / total_capital) if total_capital > 0 else 0

    def can_add_position(self, risk_amount: float, total_capital: float) -> bool:
        """
        Check if new position can be added without exceeding max heat

        Args:
            risk_amount: Risk amount of new position
            total_capital: Total portfolio capital

        Returns:
            True if position can be added
        """
        current_heat = self.get_current_heat(total_capital)
        new_heat = current_heat + (risk_amount / total_capital)

        return new_heat <= self.max_portfolio_heat


# Example usage
if __name__ == "__main__":
    # Initialize position sizer
    sizer = PositionSizer(total_capital=100000, max_position_size=0.20)

    price = 150.00
    stop_loss = 145.00
    atr = 3.50

    print("Position Sizing Examples")
    print("=" * 60)
    print(f"Capital: $100,000")
    print(f"Price: ${price}")
    print(f"Stop Loss: ${stop_loss}")
    print(f"ATR: ${atr}")
    print()

    # Fixed Dollar
    pos = sizer.fixed_dollar(dollar_amount=10000, price=price)
    print(f"Fixed Dollar ($10K):")
    print(f"  Shares: {pos.shares}")
    print(f"  Capital: ${pos.capital_allocation:,.2f}")
    print()

    # Risk Percent
    pos = sizer.risk_percent(price=price, stop_loss_price=stop_loss, risk_percent=0.01)
    print(f"Risk 1% of Capital:")
    print(f"  Shares: {pos.shares}")
    print(f"  Capital: ${pos.capital_allocation:,.2f}")
    print(f"  Risk: ${pos.risk_amount:,.2f} ({pos.risk_percent:.2f}%)")
    print()

    # Kelly Criterion
    pos = sizer.kelly_criterion(win_rate=0.55, avg_win=500, avg_loss=300, price=price)
    print(f"Kelly Criterion (55% win rate, 500/300 avg):")
    print(f"  Shares: {pos.shares}")
    print(f"  Capital: ${pos.capital_allocation:,.2f}")
    print(f"  Kelly %: {pos.risk_percent:.2f}%")
    print()

    # Volatility-Based
    pos = sizer.volatility_based(price=price, atr=atr, target_volatility=0.01)
    print(f"Volatility-Based (1% target vol):")
    print(f"  Shares: {pos.shares}")
    print(f"  Capital: ${pos.capital_allocation:,.2f}")
    print()
