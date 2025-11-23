"""
Volume Filter - Quality Filter Example
"""

import pandas as pd
from encom.core.filter_engine import QualityFilter
from encom.core.signal_registry import signal_registry


class VolumeFilter(QualityFilter):
    """
    Minimum Volume Filter

    Only allows trades when volume exceeds threshold

    Parameters:
    - min_volume_usd: Minimum daily volume in USD (default: 1M)
    """

    def __init__(self, params=None):
        super().__init__("Volume Filter", params)
        self.min_volume_usd = self.params.get("min_volume_usd", 1_000_000)

    def evaluate(self, df: pd.DataFrame, current_idx: int) -> bool:
        """Check if volume meets minimum threshold"""
        if current_idx < 0 or current_idx >= len(df):
            return False

        current_price = df['close'].iloc[current_idx]
        current_volume = df['volume'].iloc[current_idx]

        volume_usd = current_price * current_volume

        return volume_usd >= self.min_volume_usd

    def get_strength(self, df: pd.DataFrame, current_idx: int) -> float:
        """Volume filter doesn't have strength - binary pass/fail"""
        return 100.0 if self.evaluate(df, current_idx) else 0.0


# Register filter
signal_registry.register(VolumeFilter, "filter")
