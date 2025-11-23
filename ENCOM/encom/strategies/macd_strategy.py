"""
MACD Trend Following Strategy
"""

from encom.strategies.base_strategy import BaseStrategy
from encom.signals.core_signals import MACDSignal
from encom.signals.filters import VolumeFilter, TimeFilter


class MACDTrendStrategy(BaseStrategy):
    """
    MACD Trend Following Strategy

    Entry: MACD histogram crosses above zero
    Filters: Volume, Time of day

    Parameters:
    - fast_period: Fast EMA (default: 12)
    - slow_period: Slow EMA (default: 26)
    - signal_period: Signal line (default: 9)
    - min_volume: Minimum volume (default: 1M)
    """

    def __init__(self, **params):
        super().__init__("MACD Trend")
        self.params = params

    def build(self):
        """Build MACD trend strategy"""
        # Core signal: MACD histogram cross
        macd_signal = MACDSignal(params={
            "fast_period": self.params.get("fast_period", 12),
            "slow_period": self.params.get("slow_period", 26),
            "signal_period": self.params.get("signal_period", 9),
        })
        self.engine.set_core_signal(macd_signal)

        # Filter 1: Volume
        volume_filter = VolumeFilter(params={
            "min_volume_usd": self.params.get("min_volume", 1_000_000)
        })
        self.engine.filter_engine.add_filter(volume_filter)

        # Filter 2: Time of day (for intraday)
        time_filter = TimeFilter(params={
            "avoid_first_hour": True,
            "avoid_last_hour": True
        })
        self.engine.filter_engine.add_filter(time_filter)

        return self.engine
