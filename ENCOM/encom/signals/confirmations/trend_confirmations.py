"""
Trend Confirmation Signals for ENCOM Backtesting Engine

These confirmations verify that the broader trend supports the core signal.
Use in Layer 1 (required) or Layer 2 (optional) of the confirmation engine.

Author: ENCOM Development Team
License: MIT
"""

import numpy as np
from encom.indicators import adx, supertrend, ema, sma, psar, aroon


class ADXStrengthConfirmation:
    """
    Confirms strong trend using ADX (Average Directional Index)

    Theory:
    - ADX > 25: Strong trend (bullish or bearish)
    - ADX > 40: Very strong trend
    - ADX < 20: Weak/ranging market

    Use Case: Confirm trend-following signals in trending markets
    """

    def __init__(self, period=14, threshold=25):
        """
        Args:
            period: ADX calculation period
            threshold: Minimum ADX for confirmation (default: 25)
        """
        self.period = period
        self.threshold = threshold
        self.name = f"ADX_Strength_{threshold}"

    def evaluate(self, data, direction, bar_idx):
        """
        Evaluate confirmation at specific bar

        Args:
            data: OHLCV DataFrame
            direction: 1 for long, -1 for short
            bar_idx: Current bar index

        Returns:
            bool: True if ADX confirms trend strength
        """
        adx_values = adx(data['high'].values, data['low'].values,
                        data['close'].values, self.period)

        # ADX confirms if above threshold (direction-agnostic)
        return adx_values[bar_idx] > self.threshold

    def vectorized_evaluate(self, data, direction):
        """
        Vectorized evaluation for all bars

        Returns:
            np.ndarray: Boolean array of confirmations
        """
        adx_values = adx(data['high'].values, data['low'].values,
                        data['close'].values, self.period)

        return adx_values > self.threshold


class SupertrendAlignmentConfirmation:
    """
    Confirms trend using Supertrend indicator

    Theory:
    - Price > Supertrend: Uptrend
    - Price < Supertrend: Downtrend
    - Supertrend changes color at trend reversals

    Use Case: Confirm trend direction with adaptive indicator
    """

    def __init__(self, period=10, multiplier=3.0):
        """
        Args:
            period: ATR period for Supertrend
            multiplier: ATR multiplier
        """
        self.period = period
        self.multiplier = multiplier
        self.name = f"Supertrend_Align_{period}"

    def evaluate(self, data, direction, bar_idx):
        """Evaluate at specific bar"""
        st_values, st_direction = supertrend(
            data['high'].values, data['low'].values,
            data['close'].values, self.period, self.multiplier
        )

        # Supertrend direction: 1 = up, -1 = down
        # Confirm if Supertrend direction matches signal direction
        return st_direction[bar_idx] == direction

    def vectorized_evaluate(self, data, direction):
        """Vectorized evaluation"""
        st_values, st_direction = supertrend(
            data['high'].values, data['low'].values,
            data['close'].values, self.period, self.multiplier
        )

        # Return array where Supertrend matches direction
        if direction == 1:  # Long
            return st_direction == 1
        else:  # Short
            return st_direction == -1


class MovingAverageAlignmentConfirmation:
    """
    Confirms trend using Moving Average alignment

    Theory:
    - Fast MA > Slow MA: Uptrend
    - Fast MA < Slow MA: Downtrend
    - Golden Cross/Death Cross patterns

    Use Case: Classic trend confirmation
    """

    def __init__(self, fast_period=50, slow_period=200, ma_type='sma'):
        """
        Args:
            fast_period: Fast MA period
            slow_period: Slow MA period
            ma_type: 'sma' or 'ema'
        """
        self.fast_period = fast_period
        self.slow_period = slow_period
        self.ma_type = ma_type
        self.name = f"MA_Align_{fast_period}_{slow_period}"

    def evaluate(self, data, direction, bar_idx):
        """Evaluate at specific bar"""
        close = data['close'].values

        if self.ma_type == 'ema':
            fast_ma = ema(close, self.fast_period)
            slow_ma = ema(close, self.slow_period)
        else:
            fast_ma = sma(close, self.fast_period)
            slow_ma = sma(close, self.slow_period)

        if direction == 1:  # Long
            return fast_ma[bar_idx] > slow_ma[bar_idx]
        else:  # Short
            return fast_ma[bar_idx] < slow_ma[bar_idx]

    def vectorized_evaluate(self, data, direction):
        """Vectorized evaluation"""
        close = data['close'].values

        if self.ma_type == 'ema':
            fast_ma = ema(close, self.fast_period)
            slow_ma = ema(close, self.slow_period)
        else:
            fast_ma = sma(close, self.fast_period)
            slow_ma = sma(close, self.slow_period)

        if direction == 1:  # Long
            return fast_ma > slow_ma
        else:  # Short
            return fast_ma < slow_ma


class ParabolicSARConfirmation:
    """
    Confirms trend using Parabolic SAR

    Theory:
    - Price > PSAR: Uptrend
    - Price < PSAR: Downtrend
    - PSAR flips provide stop-loss levels

    Use Case: Trend confirmation with built-in stops
    """

    def __init__(self, acceleration=0.02, maximum=0.2):
        """
        Args:
            acceleration: SAR acceleration factor
            maximum: Maximum acceleration
        """
        self.acceleration = acceleration
        self.maximum = maximum
        self.name = "PSAR_Confirm"

    def evaluate(self, data, direction, bar_idx):
        """Evaluate at specific bar"""
        psar_values = psar(data['high'].values, data['low'].values,
                          data['close'].values, self.acceleration, self.maximum)

        close = data['close'].values[bar_idx]

        if direction == 1:  # Long
            return close > psar_values[bar_idx]
        else:  # Short
            return close < psar_values[bar_idx]

    def vectorized_evaluate(self, data, direction):
        """Vectorized evaluation"""
        psar_values = psar(data['high'].values, data['low'].values,
                          data['close'].values, self.acceleration, self.maximum)

        close = data['close'].values

        if direction == 1:  # Long
            return close > psar_values
        else:  # Short
            return close < psar_values


class AroonConfirmation:
    """
    Confirms trend using Aroon indicator

    Theory:
    - Aroon Up > 70 & Aroon Down < 30: Strong uptrend
    - Aroon Down > 70 & Aroon Up < 30: Strong downtrend
    - Measures time since highest high / lowest low

    Use Case: Confirm trend strength and direction
    """

    def __init__(self, period=25, threshold=70):
        """
        Args:
            period: Aroon period
            threshold: Threshold for strong trend (default: 70)
        """
        self.period = period
        self.threshold = threshold
        self.name = f"Aroon_Confirm_{period}"

    def evaluate(self, data, direction, bar_idx):
        """Evaluate at specific bar"""
        aroon_up, aroon_down = aroon(data['high'].values, data['low'].values, self.period)

        if direction == 1:  # Long
            # Strong uptrend: Aroon Up high, Aroon Down low
            return (aroon_up[bar_idx] > self.threshold and
                   aroon_down[bar_idx] < (100 - self.threshold))
        else:  # Short
            # Strong downtrend: Aroon Down high, Aroon Up low
            return (aroon_down[bar_idx] > self.threshold and
                   aroon_up[bar_idx] < (100 - self.threshold))

    def vectorized_evaluate(self, data, direction):
        """Vectorized evaluation"""
        aroon_up, aroon_down = aroon(data['high'].values, data['low'].values, self.period)

        if direction == 1:  # Long
            return (aroon_up > self.threshold) & (aroon_down < (100 - self.threshold))
        else:  # Short
            return (aroon_down > self.threshold) & (aroon_up < (100 - self.threshold))
