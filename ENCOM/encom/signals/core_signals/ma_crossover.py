"""
Moving Average Crossover - Core Signal Example
"""

import pandas as pd
from encom.core.signal_registry import BaseSignal, signal_registry


class MACrossover(BaseSignal):
    """
    Moving Average Crossover Signal

    Triggers when fast MA crosses above slow MA (bullish)

    Parameters:
    - fast_period: Fast MA period (default: 20)
    - slow_period: Slow MA period (default: 50)
    """

    def __init__(self, params=None):
        super().__init__("MA Crossover", params)
        self.signal_type = "core"
        self.fast_period = self.params.get("fast_period", 20)
        self.slow_period = self.params.get("slow_period", 50)

    def evaluate(self, df: pd.DataFrame, current_idx: int) -> bool:
        """Check if MA crossover occurred"""
        if current_idx < self.slow_period + 1:
            return False

        # Calculate MAs
        fast_ma_current = df['close'].iloc[current_idx - self.fast_period:current_idx].mean()
        slow_ma_current = df['close'].iloc[current_idx - self.slow_period:current_idx].mean()

        fast_ma_prev = df['close'].iloc[current_idx - self.fast_period - 1:current_idx - 1].mean()
        slow_ma_prev = df['close'].iloc[current_idx - self.slow_period - 1:current_idx - 1].mean()

        # Crossover: fast was below, now above
        crossover = (fast_ma_prev <= slow_ma_prev) and (fast_ma_current > slow_ma_current)

        return crossover

    def get_strength(self, df: pd.DataFrame, current_idx: int) -> float:
        """Calculate signal strength based on MA separation"""
        if current_idx < self.slow_period:
            return 0.0

        fast_ma = df['close'].iloc[current_idx - self.fast_period:current_idx].mean()
        slow_ma = df['close'].iloc[current_idx - self.slow_period:current_idx].mean()

        # Strength based on percentage separation
        separation_pct = ((fast_ma - slow_ma) / slow_ma) * 100

        # Normalize to 0-100
        strength = min(abs(separation_pct) * 20, 100)

        return strength


# Register signal
signal_registry.register(MACrossover, "core")
