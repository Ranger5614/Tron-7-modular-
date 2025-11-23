"""
MACD Signal - Moving Average Convergence Divergence
"""

import pandas as pd
import numpy as np
from encom.core.signal_registry import BaseSignal, signal_registry
from encom.indicators import macd_nb


class MACDSignal(BaseSignal):
    """
    MACD Histogram Cross Signal

    Triggers when MACD histogram crosses above zero (bullish)

    Parameters:
    - fast_period: Fast EMA period (default: 12)
    - slow_period: Slow EMA period (default: 26)
    - signal_period: Signal line period (default: 9)
    """

    def __init__(self, params=None):
        super().__init__("MACD Signal", params)
        self.signal_type = "core"
        self.fast_period = self.params.get("fast_period", 12)
        self.slow_period = self.params.get("slow_period", 26)
        self.signal_period = self.params.get("signal_period", 9)

    def evaluate(self, df: pd.DataFrame, current_idx: int) -> bool:
        """Check if MACD histogram crosses above zero"""
        min_period = self.slow_period + self.signal_period

        if current_idx < min_period + 1:
            return False

        hist_current = self._calculate_histogram(df, current_idx)
        hist_prev = self._calculate_histogram(df, current_idx - 1)

        # Bullish: histogram crosses above zero
        bullish_cross = (hist_prev <= 0) and (hist_current > 0)

        return bullish_cross

    def get_strength(self, df: pd.DataFrame, current_idx: int) -> float:
        """Calculate signal strength based on histogram value"""
        min_period = self.slow_period + self.signal_period

        if current_idx < min_period:
            return 0.0

        hist = self._calculate_histogram(df, current_idx)

        # Normalize histogram to 0-100 (arbitrary scaling)
        strength = abs(hist) * 1000  # Scale to reasonable range

        return min(strength, 100)

    def _calculate_histogram(self, df: pd.DataFrame, idx: int) -> float:
        """Calculate MACD histogram at given index"""
        # Get price data
        prices = df['close'].iloc[:idx + 1]

        # Calculate EMAs
        fast_ema = prices.ewm(span=self.fast_period, adjust=False).mean().iloc[-1]
        slow_ema = prices.ewm(span=self.slow_period, adjust=False).mean().iloc[-1]

        # MACD line
        macd_line = fast_ema - slow_ema

        # Calculate signal line (EMA of MACD)
        macd_series = prices.ewm(span=self.fast_period, adjust=False).mean() - \
                      prices.ewm(span=self.slow_period, adjust=False).mean()

        signal_line = macd_series.ewm(span=self.signal_period, adjust=False).mean().iloc[-1]

        # Histogram = MACD - Signal
        histogram = macd_line - signal_line

        return histogram

    def evaluate_vectorized(self, df: pd.DataFrame) -> np.ndarray:
        """
        Vectorized MACD signal evaluation (40-70x faster)

        Returns boolean array where True = MACD histogram crossing above zero
        """
        # Calculate MACD for entire dataset once (Numba-optimized)
        close_array = df['close'].values.astype(np.float64)
        macd_line, signal_line, histogram = macd_nb(
            close_array,
            self.fast_period,
            self.slow_period,
            self.signal_period
        )

        # Detect bullish crosses: histogram crosses above zero
        hist_prev = np.roll(histogram, 1)
        hist_prev[0] = 0.0  # No signal on first bar

        bullish_cross = (hist_prev <= 0) & (histogram > 0)

        # No signals before period is satisfied
        min_period = self.slow_period + self.signal_period
        bullish_cross[:min_period + 1] = False

        return bullish_cross


# Register signal
signal_registry.register(MACDSignal, "core")
