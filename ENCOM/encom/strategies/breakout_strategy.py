"""
Breakout Strategy with Volume Confirmation
"""

from encom.strategies.base_strategy import BaseStrategy
from encom.signals.core_signals import BreakoutSignal, VolumeSpikeSignal
from encom.signals.filters import VolumeFilter


class BreakoutStrategy(BaseStrategy):
    """
    Price Breakout Strategy with Volume Spike Confirmation

    Entry: Price breaks above recent high
    Confirmation: Volume spike (2x average)
    Filters: Minimum volume

    Parameters:
    - lookback: Breakout lookback period (default: 20)
    - volume_threshold: Volume spike multiplier (default: 2.0)
    - min_volume: Minimum daily volume (default: 1M)
    """

    def __init__(self, **params):
        super().__init__("Breakout Strategy")
        self.params = params

    def build(self):
        """Build breakout strategy"""
        # Core signal: Price breakout
        breakout_signal = BreakoutSignal(params={
            "lookback": self.params.get("lookback", 20)
        })
        self.engine.set_core_signal(breakout_signal)

        # Confirmation Layer 1: Volume spike
        volume_spike = VolumeSpikeSignal(params={
            "period": 20,
            "threshold": self.params.get("volume_threshold", 2.0)
        })
        self.engine.confirmation_engine.layer1.add_signal(volume_spike)

        # Filter: Minimum volume
        volume_filter = VolumeFilter(params={
            "min_volume_usd": self.params.get("min_volume", 1_000_000)
        })
        self.engine.filter_engine.add_filter(volume_filter)

        return self.engine
