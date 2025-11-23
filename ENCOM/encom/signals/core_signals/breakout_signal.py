"""
Breakout Signal - Price breakout of range
"""

import pandas as pd
from encom.core.signal_registry import BaseSignal, signal_registry


class BreakoutSignal(BaseSignal):
    """
    Price Breakout Signal

    Triggers when price breaks above recent high

    Parameters:
    - lookback: Lookback period for high/low (default: 20)
    """

    def __init__(self, params=None):
        super().__init__("Breakout Signal", params)
        self.signal_type = "core"
        self.lookback = self.params.get("lookback", 20)

    def evaluate(self, df: pd.DataFrame, current_idx: int) -> bool:
        """Check if price breaks above recent high"""
        if current_idx < self.lookback + 1:
            return False

        # Get recent high (excluding current bar)
        recent_high = df['high'].iloc[current_idx - self.lookback:current_idx].max()

        # Current price
        current_price = df['close'].iloc[current_idx]
        prev_price = df['close'].iloc[current_idx - 1]

        # Breakout: current price breaks above recent high
        breakout = (prev_price <= recent_high) and (current_price > recent_high)

        return breakout

    def get_strength(self, df: pd.DataFrame, current_idx: int) -> float:
        """Calculate signal strength based on breakout magnitude"""
        if current_idx < self.lookback:
            return 0.0

        recent_high = df['high'].iloc[current_idx - self.lookback:current_idx].max()
        current_price = df['close'].iloc[current_idx]

        # Strength = how far above the breakout level
        if recent_high == 0:
            return 0.0

        breakout_pct = ((current_price - recent_high) / recent_high) * 100

        # Scale to 0-100 (0.5% breakout = 50 strength)
        strength = breakout_pct * 100

        return max(0, min(strength, 100))


# Register signal
signal_registry.register(BreakoutSignal, "core")
