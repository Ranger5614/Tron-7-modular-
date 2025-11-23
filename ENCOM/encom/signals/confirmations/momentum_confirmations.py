"""
Momentum Confirmation Signals for ENCOM Backtesting Engine

These confirmations verify that momentum supports the core signal.
Momentum measures the speed and strength of price movements.

Author: ENCOM Development Team
License: MIT
"""

import numpy as np
from encom.indicators import rsi, macd, stochastic, roc, cci


class RSIDirectionConfirmation:
    """
    Confirms RSI is trending in signal direction

    Theory:
    - RSI rising = bullish momentum
    - RSI falling = bearish momentum
    - RSI divergence warns of reversals

    Use Case: Momentum confirmation, avoid counter-trend trades
    """

    def __init__(self, period=14, lookback=3):
        """
        Args:
            period: RSI period
            lookback: Bars to compare for direction
        """
        self.period = period
        self.lookback = lookback
        self.name = f"RSI_Direction_{period}"

    def evaluate(self, data, direction, bar_idx):
        """Evaluate at specific bar"""
        if bar_idx < self.lookback:
            return False

        rsi_values = rsi(data['close'].values, self.period)

        current_rsi = rsi_values[bar_idx]
        past_rsi = rsi_values[bar_idx - self.lookback]

        if direction == 1:  # Long
            # RSI rising
            return current_rsi > past_rsi
        else:  # Short
            # RSI falling
            return current_rsi < past_rsi

    def vectorized_evaluate(self, data, direction):
        """Vectorized evaluation"""
        rsi_values = rsi(data['close'].values, self.period)

        # Create shifted array for comparison
        result = np.zeros(len(rsi_values), dtype=bool)

        if direction == 1:  # Long
            result[self.lookback:] = rsi_values[self.lookback:] > rsi_values[:-self.lookback]
        else:  # Short
            result[self.lookback:] = rsi_values[self.lookback:] < rsi_values[:-self.lookback]

        return result


class MACDHistogramSlopeConfirmation:
    """
    Confirms MACD histogram is increasing (momentum accelerating)

    Theory:
    - Histogram rising = momentum accelerating
    - Histogram falling = momentum decelerating
    - Histogram crossing zero = trend change

    Use Case: Momentum acceleration confirmation
    """

    def __init__(self, fast_period=12, slow_period=26, signal_period=9, lookback=2):
        """
        Args:
            fast_period: MACD fast EMA
            slow_period: MACD slow EMA
            signal_period: Signal line period
            lookback: Bars to compare for slope
        """
        self.fast_period = fast_period
        self.slow_period = slow_period
        self.signal_period = signal_period
        self.lookback = lookback
        self.name = "MACD_Histogram_Slope"

    def evaluate(self, data, direction, bar_idx):
        """Evaluate at specific bar"""
        if bar_idx < self.lookback:
            return False

        macd_line, signal_line, histogram = macd(
            data['close'].values,
            self.fast_period, self.slow_period, self.signal_period
        )

        current_hist = histogram[bar_idx]
        past_hist = histogram[bar_idx - self.lookback]

        if direction == 1:  # Long
            # Histogram rising (momentum accelerating up)
            return current_hist > past_hist
        else:  # Short
            # Histogram falling (momentum accelerating down)
            return current_hist < past_hist

    def vectorized_evaluate(self, data, direction):
        """Vectorized evaluation"""
        macd_line, signal_line, histogram = macd(
            data['close'].values,
            self.fast_period, self.slow_period, self.signal_period
        )

        result = np.zeros(len(histogram), dtype=bool)

        if direction == 1:  # Long
            result[self.lookback:] = histogram[self.lookback:] > histogram[:-self.lookback]
        else:  # Short
            result[self.lookback:] = histogram[self.lookback:] < histogram[:-self.lookback]

        return result


class StochasticAlignmentConfirmation:
    """
    Confirms Stochastic oscillator matches direction

    Theory:
    - %K > %D and rising = bullish
    - %K < %D and falling = bearish
    - Overbought/oversold extremes

    Use Case: Short-term momentum confirmation
    """

    def __init__(self, k_period=14, d_period=3):
        """
        Args:
            k_period: %K period
            d_period: %D period
        """
        self.k_period = k_period
        self.d_period = d_period
        self.name = f"Stochastic_{k_period}"

    def evaluate(self, data, direction, bar_idx):
        """Evaluate at specific bar"""
        k_values, d_values = stochastic(
            data['high'].values, data['low'].values,
            data['close'].values, self.k_period, self.d_period
        )

        if direction == 1:  # Long
            # %K above %D (bullish)
            return k_values[bar_idx] > d_values[bar_idx]
        else:  # Short
            # %K below %D (bearish)
            return k_values[bar_idx] < d_values[bar_idx]

    def vectorized_evaluate(self, data, direction):
        """Vectorized evaluation"""
        k_values, d_values = stochastic(
            data['high'].values, data['low'].values,
            data['close'].values, self.k_period, self.d_period
        )

        if direction == 1:  # Long
            return k_values > d_values
        else:  # Short
            return k_values < d_values


class ROCPositiveConfirmation:
    """
    Confirms Rate of Change (ROC) matches direction

    Theory:
    - ROC > 0: Price rising
    - ROC < 0: Price falling
    - ROC magnitude = strength of move

    Use Case: Simple momentum confirmation
    """

    def __init__(self, period=12):
        """
        Args:
            period: ROC period
        """
        self.period = period
        self.name = f"ROC_Positive_{period}"

    def evaluate(self, data, direction, bar_idx):
        """Evaluate at specific bar"""
        roc_values = roc(data['close'].values, self.period)

        if direction == 1:  # Long
            # ROC positive (price rising)
            return roc_values[bar_idx] > 0
        else:  # Short
            # ROC negative (price falling)
            return roc_values[bar_idx] < 0

    def vectorized_evaluate(self, data, direction):
        """Vectorized evaluation"""
        roc_values = roc(data['close'].values, self.period)

        if direction == 1:  # Long
            return roc_values > 0
        else:  # Short
            return roc_values < 0


class CCIConfirmation:
    """
    Confirms Commodity Channel Index (CCI) matches direction

    Theory:
    - CCI > 100: Overbought (strong uptrend)
    - CCI < -100: Oversold (strong downtrend)
    - CCI > 0: Bullish, CCI < 0: Bearish

    Use Case: Trend strength and momentum confirmation
    """

    def __init__(self, period=20, threshold=0):
        """
        Args:
            period: CCI period
            threshold: CCI threshold (0 = neutral, 100 = strong)
        """
        self.period = period
        self.threshold = threshold
        self.name = f"CCI_Confirm_{period}"

    def evaluate(self, data, direction, bar_idx):
        """Evaluate at specific bar"""
        cci_values = cci(data['high'].values, data['low'].values,
                        data['close'].values, self.period)

        if direction == 1:  # Long
            # CCI positive (bullish)
            return cci_values[bar_idx] > self.threshold
        else:  # Short
            # CCI negative (bearish)
            return cci_values[bar_idx] < -self.threshold

    def vectorized_evaluate(self, data, direction):
        """Vectorized evaluation"""
        cci_values = cci(data['high'].values, data['low'].values,
                        data['close'].values, self.period)

        if direction == 1:  # Long
            return cci_values > self.threshold
        else:  # Short
            return cci_values < -self.threshold
