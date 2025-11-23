"""
Time Filter - Time-of-day filtering
"""

import pandas as pd
from datetime import time
from encom.core.filter_engine import QualityFilter
from encom.core.signal_registry import signal_registry


class TimeFilter(QualityFilter):
    """
    Time of Day Filter

    Avoids trading during first/last hour (high volatility, low liquidity)

    Parameters:
    - avoid_first_hour: Avoid first hour after market open (default: True)
    - avoid_last_hour: Avoid last hour before close (default: True)
    - market_open: Market open time (default: 09:30)
    - market_close: Market close time (default: 16:00)
    """

    def __init__(self, params=None):
        super().__init__("Time Filter", params)
        self.avoid_first_hour = self.params.get("avoid_first_hour", True)
        self.avoid_last_hour = self.params.get("avoid_last_hour", True)
        self.market_open = self.params.get("market_open", time(9, 30))
        self.market_close = self.params.get("market_close", time(16, 0))

    def evaluate(self, df: pd.DataFrame, current_idx: int) -> bool:
        """Check if current time is acceptable for trading"""
        if current_idx < 0 or current_idx >= len(df):
            return False

        timestamp = df.index[current_idx]

        # For daily data, always pass
        if not hasattr(timestamp, 'hour'):
            return True

        current_time = timestamp.time()

        # Check first hour
        if self.avoid_first_hour:
            first_hour_end = time(self.market_open.hour + 1, self.market_open.minute)
            if current_time < first_hour_end:
                return False

        # Check last hour
        if self.avoid_last_hour:
            last_hour_start = time(self.market_close.hour - 1, self.market_close.minute)
            if current_time >= last_hour_start:
                return False

        return True

    def get_strength(self, df: pd.DataFrame, current_idx: int) -> float:
        """Time filter is binary - pass/fail"""
        return 100.0 if self.evaluate(df, current_idx) else 0.0


# Register filter
signal_registry.register(TimeFilter, "filter")
