"""
Volume Confirmation Signals for ENCOM Backtesting Engine

These confirmations verify that volume supports the core signal.
Institutional participation often shows up in volume.

Author: ENCOM Development Team
License: MIT
"""

import numpy as np
from encom.indicators import obv, cmf, sma


class VolumeIncreasingConfirmation:
    """
    Confirms volume is above average

    Theory:
    - High volume = institutional participation
    - Low volume = weak signal, retail only
    - Volume surge confirms breakouts

    Use Case: Filter out low-conviction signals
    """

    def __init__(self, period=20, multiplier=1.0):
        """
        Args:
            period: Lookback period for average volume
            multiplier: Minimum multiplier of average (1.0 = equal, 1.5 = 50% above)
        """
        self.period = period
        self.multiplier = multiplier
        self.name = f"Volume_Above_Avg_{period}"

    def evaluate(self, data, direction, bar_idx):
        """Evaluate at specific bar"""
        volume = data['volume'].values
        avg_volume = sma(volume, self.period)

        # Confirm if current volume > average * multiplier
        return volume[bar_idx] > (avg_volume[bar_idx] * self.multiplier)

    def vectorized_evaluate(self, data, direction):
        """Vectorized evaluation"""
        volume = data['volume'].values
        avg_volume = sma(volume, self.period)

        return volume > (avg_volume * self.multiplier)


class OBVTrendConfirmation:
    """
    Confirms On-Balance Volume (OBV) trend matches signal

    Theory:
    - OBV rising: Accumulation (bullish)
    - OBV falling: Distribution (bearish)
    - OBV divergence warns of reversals

    Use Case: Confirm institutional buying/selling
    """

    def __init__(self, ma_period=20):
        """
        Args:
            ma_period: Period for OBV moving average
        """
        self.ma_period = ma_period
        self.name = f"OBV_Trend_{ma_period}"

    def evaluate(self, data, direction, bar_idx):
        """Evaluate at specific bar"""
        obv_values = obv(data['close'].values, data['volume'].values)
        obv_ma = sma(obv_values, self.ma_period)

        if direction == 1:  # Long
            # OBV trending up (above its MA)
            return obv_values[bar_idx] > obv_ma[bar_idx]
        else:  # Short
            # OBV trending down (below its MA)
            return obv_values[bar_idx] < obv_ma[bar_idx]

    def vectorized_evaluate(self, data, direction):
        """Vectorized evaluation"""
        obv_values = obv(data['close'].values, data['volume'].values)
        obv_ma = sma(obv_values, self.ma_period)

        if direction == 1:  # Long
            return obv_values > obv_ma
        else:  # Short
            return obv_values < obv_ma


class CMFConfirmation:
    """
    Confirms Chaikin Money Flow (CMF) matches direction

    Theory:
    - CMF > 0: Buying pressure (accumulation)
    - CMF < 0: Selling pressure (distribution)
    - CMF measures volume-weighted accumulation/distribution

    Use Case: Confirm money flow direction
    """

    def __init__(self, period=20, threshold=0.0):
        """
        Args:
            period: CMF period
            threshold: Minimum CMF value (default: 0.0)
        """
        self.period = period
        self.threshold = threshold
        self.name = f"CMF_Confirm_{period}"

    def evaluate(self, data, direction, bar_idx):
        """Evaluate at specific bar"""
        cmf_values = cmf(data['high'].values, data['low'].values,
                        data['close'].values, data['volume'].values, self.period)

        if direction == 1:  # Long
            # CMF positive = buying pressure
            return cmf_values[bar_idx] > self.threshold
        else:  # Short
            # CMF negative = selling pressure
            return cmf_values[bar_idx] < -self.threshold

    def vectorized_evaluate(self, data, direction):
        """Vectorized evaluation"""
        cmf_values = cmf(data['high'].values, data['low'].values,
                        data['close'].values, data['volume'].values, self.period)

        if direction == 1:  # Long
            return cmf_values > self.threshold
        else:  # Short
            return cmf_values < -self.threshold


class VolumeRatioConfirmation:
    """
    Confirms volume ratio (current / average) exceeds threshold

    Theory:
    - Volume spike = conviction
    - 2x average volume = strong signal
    - 3x+ average volume = institutional activity

    Use Case: Detect volume surges on breakouts
    """

    def __init__(self, period=20, min_ratio=1.5):
        """
        Args:
            period: Lookback period for average
            min_ratio: Minimum volume ratio (2.0 = 200% of average)
        """
        self.period = period
        self.min_ratio = min_ratio
        self.name = f"Volume_Ratio_{min_ratio}x"

    def evaluate(self, data, direction, bar_idx):
        """Evaluate at specific bar"""
        volume = data['volume'].values
        avg_volume = sma(volume, self.period)

        # Avoid division by zero
        if avg_volume[bar_idx] == 0:
            return False

        ratio = volume[bar_idx] / avg_volume[bar_idx]
        return ratio >= self.min_ratio

    def vectorized_evaluate(self, data, direction):
        """Vectorized evaluation"""
        volume = data['volume'].values
        avg_volume = sma(volume, self.period)

        # Handle division by zero
        ratio = np.zeros_like(volume)
        mask = avg_volume > 0
        ratio[mask] = volume[mask] / avg_volume[mask]

        return ratio >= self.min_ratio
