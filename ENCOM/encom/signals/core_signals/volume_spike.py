"""
Volume Spike Signal - Unusual volume activity
"""

import pandas as pd
from encom.core.signal_registry import BaseSignal, signal_registry


class VolumeSpikeSignal(BaseSignal):
    """
    Volume Spike Signal

    Triggers when volume spikes above average

    Parameters:
    - period: Lookback period for average volume (default: 20)
    - threshold: Spike threshold multiplier (default: 2.0x average)
    """

    def __init__(self, params=None):
        super().__init__("Volume Spike", params)
        self.signal_type = "core"
        self.period = self.params.get("period", 20)
        self.threshold = self.params.get("threshold", 2.0)

    def evaluate(self, df: pd.DataFrame, current_idx: int) -> bool:
        """Check if volume spike occurs"""
        if current_idx < self.period:
            return False

        # Calculate average volume
        avg_volume = df['volume'].iloc[current_idx - self.period:current_idx].mean()

        # Current volume
        current_volume = df['volume'].iloc[current_idx]

        # Spike: volume > threshold * average
        spike = current_volume > (avg_volume * self.threshold)

        # Also require price to be rising (bullish spike)
        price_rising = df['close'].iloc[current_idx] > df['close'].iloc[current_idx - 1]

        return spike and price_rising

    def get_strength(self, df: pd.DataFrame, current_idx: int) -> float:
        """Calculate signal strength based on spike magnitude"""
        if current_idx < self.period:
            return 0.0

        avg_volume = df['volume'].iloc[current_idx - self.period:current_idx].mean()
        current_volume = df['volume'].iloc[current_idx]

        if avg_volume == 0:
            return 0.0

        # Spike ratio
        spike_ratio = current_volume / avg_volume

        # Normalize to 0-100 (2x = 50, 4x = 100)
        strength = ((spike_ratio - 1) / 3) * 100

        return max(0, min(strength, 100))


# Register signal
signal_registry.register(VolumeSpikeSignal, "core")
