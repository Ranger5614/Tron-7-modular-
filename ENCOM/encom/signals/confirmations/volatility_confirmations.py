"""
Volatility Confirmation Signals for ENCOM Backtesting Engine

These confirmations verify that volatility conditions support the core signal.
Volatility affects risk, stop-loss placement, and signal reliability.

Author: ENCOM Development Team
License: MIT
"""

import numpy as np
from encom.indicators import atr, bollinger_bands, keltner_channels, sma


class ATRExpandingConfirmation:
    """
    Confirms volatility is expanding (ATR increasing)

    Theory:
    - Expanding volatility = trend beginning
    - Contracting volatility = consolidation/range
    - ATR rising confirms breakout legitimacy

    Use Case: Confirm breakouts, avoid false signals in low volatility
    """

    def __init__(self, period=14, lookback=5):
        """
        Args:
            period: ATR calculation period
            lookback: Periods to compare for expansion
        """
        self.period = period
        self.lookback = lookback
        self.name = f"ATR_Expanding_{period}"

    def evaluate(self, data, direction, bar_idx):
        """Evaluate at specific bar"""
        if bar_idx < self.lookback:
            return False

        atr_values = atr(data['high'].values, data['low'].values,
                        data['close'].values, self.period)

        # ATR expanding if current > previous
        current_atr = atr_values[bar_idx]
        past_atr = atr_values[bar_idx - self.lookback]

        return current_atr > past_atr

    def vectorized_evaluate(self, data, direction):
        """Vectorized evaluation"""
        atr_values = atr(data['high'].values, data['low'].values,
                        data['close'].values, self.period)

        # Create shifted array for comparison
        result = np.zeros(len(atr_values), dtype=bool)
        result[self.lookback:] = atr_values[self.lookback:] > atr_values[:-self.lookback]

        return result


class ATRContractingConfirmation:
    """
    Confirms volatility is contracting (ATR decreasing)

    Theory:
    - Contracting volatility = consolidation before breakout
    - Low volatility = tight stop-losses possible
    - Volatility squeeze setups

    Use Case: Mean reversion strategies, range trading
    """

    def __init__(self, period=14, lookback=5):
        """
        Args:
            period: ATR calculation period
            lookback: Periods to compare for contraction
        """
        self.period = period
        self.lookback = lookback
        self.name = f"ATR_Contracting_{period}"

    def evaluate(self, data, direction, bar_idx):
        """Evaluate at specific bar"""
        if bar_idx < self.lookback:
            return False

        atr_values = atr(data['high'].values, data['low'].values,
                        data['close'].values, self.period)

        # ATR contracting if current < previous
        current_atr = atr_values[bar_idx]
        past_atr = atr_values[bar_idx - self.lookback]

        return current_atr < past_atr

    def vectorized_evaluate(self, data, direction):
        """Vectorized evaluation"""
        atr_values = atr(data['high'].values, data['low'].values,
                        data['close'].values, self.period)

        # Create shifted array for comparison
        result = np.zeros(len(atr_values), dtype=bool)
        result[self.lookback:] = atr_values[self.lookback:] < atr_values[:-self.lookback]

        return result


class BollingerBandWidthConfirmation:
    """
    Confirms Bollinger Band width (volatility state)

    Theory:
    - Wide bands = high volatility
    - Narrow bands = low volatility (squeeze)
    - Band width predicts volatility expansion

    Use Case: Volatility squeeze breakouts, range identification
    """

    def __init__(self, period=20, std_dev=2.0, mode='expanding'):
        """
        Args:
            period: BB period
            std_dev: Standard deviation multiplier
            mode: 'expanding' or 'contracting'
        """
        self.period = period
        self.std_dev = std_dev
        self.mode = mode
        self.name = f"BB_Width_{mode}"

    def evaluate(self, data, direction, bar_idx):
        """Evaluate at specific bar"""
        if bar_idx < 5:  # Need lookback
            return False

        middle, upper, lower = bollinger_bands(data['close'].values, self.period, self.std_dev)

        # Calculate band width
        width = (upper - lower) / middle
        width = np.nan_to_num(width, 0.0)  # Handle division by zero

        # Compare current to average width
        avg_width = sma(width, 20)

        if self.mode == 'expanding':
            return width[bar_idx] > avg_width[bar_idx]
        else:  # contracting
            return width[bar_idx] < avg_width[bar_idx]

    def vectorized_evaluate(self, data, direction):
        """Vectorized evaluation"""
        middle, upper, lower = bollinger_bands(data['close'].values, self.period, self.std_dev)

        # Calculate band width (% of price)
        width = np.zeros_like(middle)
        mask = middle > 0
        width[mask] = (upper[mask] - lower[mask]) / middle[mask]

        # Compare to average width
        avg_width = sma(width, 20)

        if self.mode == 'expanding':
            return width > avg_width
        else:  # contracting
            return width < avg_width


class KeltnerChannelPositionConfirmation:
    """
    Confirms price position within Keltner Channels

    Theory:
    - Price at upper band = strong uptrend
    - Price at lower band = strong downtrend
    - Price at middle = neutral

    Use Case: Trend strength confirmation
    """

    def __init__(self, ema_period=20, atr_period=10, atr_mult=2.0):
        """
        Args:
            ema_period: EMA period for middle line
            atr_period: ATR period
            atr_mult: ATR multiplier
        """
        self.ema_period = ema_period
        self.atr_period = atr_period
        self.atr_mult = atr_mult
        self.name = f"KC_Position_{ema_period}"

    def evaluate(self, data, direction, bar_idx):
        """Evaluate at specific bar"""
        middle, upper, lower = keltner_channels(
            data['high'].values, data['low'].values, data['close'].values,
            self.ema_period, self.atr_period, self.atr_mult
        )

        close = data['close'].values[bar_idx]

        if direction == 1:  # Long
            # Price near/above upper band = strong uptrend
            band_range = upper[bar_idx] - middle[bar_idx]
            if band_range == 0:
                return False
            position = (close - middle[bar_idx]) / band_range
            return position > 0.5  # Upper half of channel
        else:  # Short
            # Price near/below lower band = strong downtrend
            band_range = middle[bar_idx] - lower[bar_idx]
            if band_range == 0:
                return False
            position = (middle[bar_idx] - close) / band_range
            return position > 0.5  # Lower half of channel

    def vectorized_evaluate(self, data, direction):
        """Vectorized evaluation"""
        middle, upper, lower = keltner_channels(
            data['high'].values, data['low'].values, data['close'].values,
            self.ema_period, self.atr_period, self.atr_mult
        )

        close = data['close'].values
        result = np.zeros(len(close), dtype=bool)

        if direction == 1:  # Long
            band_range = upper - middle
            mask = band_range > 0
            position = np.zeros_like(close)
            position[mask] = (close[mask] - middle[mask]) / band_range[mask]
            result = position > 0.5
        else:  # Short
            band_range = middle - lower
            mask = band_range > 0
            position = np.zeros_like(close)
            position[mask] = (middle[mask] - close[mask]) / band_range[mask]
            result = position > 0.5

        return result
