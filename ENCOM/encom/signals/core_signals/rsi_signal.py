"""
RSI Signal - Relative Strength Index overbought/oversold
"""

import pandas as pd
import numpy as np
from encom.core.signal_registry import BaseSignal, signal_registry
from encom.indicators import rsi_nb


class RSISignal(BaseSignal):
    """
    RSI Overbought/Oversold Signal

    Triggers when RSI crosses oversold threshold (bullish)

    Parameters:
    - period: RSI period (default: 14)
    - oversold: Oversold threshold (default: 30)
    - overbought: Overbought threshold (default: 70)
    """

    def __init__(self, params=None):
        super().__init__("RSI Signal", params)
        self.signal_type = "core"
        self.period = self.params.get("period", 14)
        self.oversold = self.params.get("oversold", 30)
        self.overbought = self.params.get("overbought", 70)

    def evaluate(self, df: pd.DataFrame, current_idx: int) -> bool:
        """Check if RSI crosses from oversold to neutral"""
        if current_idx < self.period + 1:
            return False

        rsi_current = self._calculate_rsi(df, current_idx)
        rsi_prev = self._calculate_rsi(df, current_idx - 1)

        # Bullish: RSI was oversold, now crossing above oversold threshold
        bullish_cross = (rsi_prev <= self.oversold) and (rsi_current > self.oversold)

        return bullish_cross

    def get_strength(self, df: pd.DataFrame, current_idx: int) -> float:
        """Calculate signal strength based on RSI distance from 50"""
        if current_idx < self.period:
            return 0.0

        rsi = self._calculate_rsi(df, current_idx)

        # Strength: distance from neutral (50)
        # RSI near 30 = strong (oversold), near 50 = weak
        if rsi < 50:
            strength = (50 - rsi) * 2  # Scale 0-40 to 0-80
        else:
            strength = (rsi - 50) * 2  # Scale 50-100 to 0-100

        return min(strength, 100)

    def _calculate_rsi(self, df: pd.DataFrame, idx: int) -> float:
        """Calculate RSI at given index"""
        # Get price changes
        prices = df['close'].iloc[max(0, idx - self.period):idx + 1]

        if len(prices) < self.period:
            return 50.0

        deltas = prices.diff()

        # Separate gains and losses
        gains = deltas.where(deltas > 0, 0.0)
        losses = -deltas.where(deltas < 0, 0.0)

        # Calculate average gains/losses
        avg_gain = gains.rolling(window=self.period, min_periods=self.period).mean().iloc[-1]
        avg_loss = losses.rolling(window=self.period, min_periods=self.period).mean().iloc[-1]

        if avg_loss == 0:
            return 100.0

        rs = avg_gain / avg_loss
        rsi = 100 - (100 / (1 + rs))

        return rsi

    def evaluate_vectorized(self, df: pd.DataFrame) -> np.ndarray:
        """
        Vectorized RSI signal evaluation (50-100x faster)

        Returns boolean array where True = RSI crossing above oversold threshold
        """
        # Calculate RSI for entire dataset once (Numba-optimized)
        close_array = df['close'].values.astype(np.float64)
        rsi_values = rsi_nb(close_array, self.period)

        # Detect bullish crosses: RSI was oversold, now crossing above threshold
        rsi_prev = np.roll(rsi_values, 1)
        rsi_prev[0] = 50.0  # No signal on first bar

        bullish_cross = (rsi_prev <= self.oversold) & (rsi_values > self.oversold)

        # No signals before period is satisfied
        bullish_cross[:self.period + 1] = False

        return bullish_cross


# Register signal
signal_registry.register(RSISignal, "core")
