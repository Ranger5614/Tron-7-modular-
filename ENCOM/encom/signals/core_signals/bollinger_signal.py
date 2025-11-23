"""
Bollinger Bands Signal - Volatility breakout
"""

import pandas as pd
import numpy as np
from encom.core.signal_registry import BaseSignal, signal_registry
from encom.indicators import bollinger_bands_nb


class BollingerSignal(BaseSignal):
    """
    Bollinger Bands Breakout Signal

    Triggers when price bounces off lower band (bullish reversal)

    Parameters:
    - period: BB period (default: 20)
    - std_dev: Standard deviations (default: 2.0)
    """

    def __init__(self, params=None):
        super().__init__("Bollinger Bands", params)
        self.signal_type = "core"
        self.period = self.params.get("period", 20)
        self.std_dev = self.params.get("std_dev", 2.0)

    def evaluate(self, df: pd.DataFrame, current_idx: int) -> bool:
        """Check if price bounces off lower band"""
        if current_idx < self.period + 1:
            return False

        middle, upper, lower = self._calculate_bands(df, current_idx)
        price_current = df['close'].iloc[current_idx]
        price_prev = df['close'].iloc[current_idx - 1]

        # Bullish: price was below/at lower band, now moving up
        touched_lower = price_prev <= lower
        bouncing_up = price_current > price_prev

        return touched_lower and bouncing_up

    def get_strength(self, df: pd.DataFrame, current_idx: int) -> float:
        """Calculate signal strength based on position in bands"""
        if current_idx < self.period:
            return 0.0

        middle, upper, lower = self._calculate_bands(df, current_idx)
        price = df['close'].iloc[current_idx]

        # Position in bands: 0 = lower band, 50 = middle, 100 = upper
        band_range = upper - lower

        if band_range == 0:
            return 50.0

        position = ((price - lower) / band_range) * 100

        # Inverse for signal strength (lower = stronger signal)
        strength = 100 - position

        return max(0, min(strength, 100))

    def _calculate_bands(self, df: pd.DataFrame, idx: int) -> tuple:
        """Calculate Bollinger Bands at given index"""
        prices = df['close'].iloc[max(0, idx - self.period):idx + 1]

        if len(prices) < self.period:
            return 0, 0, 0

        middle = prices.rolling(window=self.period).mean().iloc[-1]
        std = prices.rolling(window=self.period).std().iloc[-1]

        upper = middle + (self.std_dev * std)
        lower = middle - (self.std_dev * std)

        return middle, upper, lower

    def evaluate_vectorized(self, df: pd.DataFrame) -> np.ndarray:
        """
        Vectorized Bollinger Bands signal evaluation (30-200x faster)

        Returns boolean array where True = price bouncing off lower band
        """
        # Calculate Bollinger Bands for entire dataset once (Numba-optimized)
        close_array = df['close'].values.astype(np.float64)
        middle, upper, lower = bollinger_bands_nb(close_array, self.period, self.std_dev)

        # Detect bounce: price was at/below lower band, now moving up
        price_prev = np.roll(close_array, 1)
        price_prev[0] = close_array[0]  # No signal on first bar

        touched_lower = price_prev <= lower
        bouncing_up = close_array > price_prev

        signal = touched_lower & bouncing_up

        # No signals before period is satisfied
        signal[:self.period + 1] = False

        return signal


# Register signal
signal_registry.register(BollingerSignal, "core")
