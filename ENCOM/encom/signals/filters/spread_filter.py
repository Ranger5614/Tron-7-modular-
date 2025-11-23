"""
Spread Filter - Bid-ask spread threshold
"""

import pandas as pd
from encom.core.filter_engine import QualityFilter
from encom.core.signal_registry import signal_registry


class SpreadFilter(QualityFilter):
    """
    Bid-Ask Spread Filter

    Only allows trades when spread is below threshold

    Parameters:
    - max_spread_pct: Maximum spread percentage (default: 0.1%)
    """

    def __init__(self, params=None):
        super().__init__("Spread Filter", params)
        self.max_spread_pct = self.params.get("max_spread_pct", 0.001)  # 0.1%

    def evaluate(self, df: pd.DataFrame, current_idx: int) -> bool:
        """Check if spread is below threshold"""
        # Note: Real implementation would need bid/ask data
        # For now, estimate spread from high-low range
        if current_idx < 0 or current_idx >= len(df):
            return False

        high = df['high'].iloc[current_idx]
        low = df['low'].iloc[current_idx]
        mid = (high + low) / 2

        if mid == 0:
            return False

        estimated_spread = ((high - low) / mid)

        return estimated_spread <= self.max_spread_pct

    def get_strength(self, df: pd.DataFrame, current_idx: int) -> float:
        """Spread filter is binary - pass/fail"""
        return 100.0 if self.evaluate(df, current_idx) else 0.0


# Register filter
signal_registry.register(SpreadFilter, "filter")
