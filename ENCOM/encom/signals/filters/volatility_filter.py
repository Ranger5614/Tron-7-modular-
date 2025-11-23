"""
Volatility Filter - ATR threshold
"""

import pandas as pd
from encom.core.filter_engine import QualityFilter
from encom.core.signal_registry import signal_registry


class VolatilityFilter(QualityFilter):
    """
    Volatility Filter (ATR-based)

    Only allows trades when volatility is within acceptable range

    Parameters:
    - atr_period: ATR calculation period (default: 14)
    - min_atr: Minimum ATR threshold (default: 0.0)
    - max_atr: Maximum ATR threshold (default: 999999.0)
    - atr_multiplier: ATR as % of price (default: None)
    """

    def __init__(self, params=None):
        super().__init__("Volatility Filter", params)
        self.atr_period = self.params.get("atr_period", 14)
        self.min_atr = self.params.get("min_atr", 0.0)
        self.max_atr = self.params.get("max_atr", 999999.0)
        self.atr_multiplier = self.params.get("atr_multiplier", None)

    def evaluate(self, df: pd.DataFrame, current_idx: int) -> bool:
        """Check if ATR is within acceptable range"""
        if current_idx < self.atr_period:
            return False

        atr = self._calculate_atr(df, current_idx)

        # If using percentage-based threshold
        if self.atr_multiplier is not None:
            price = df['close'].iloc[current_idx]
            max_atr_allowed = price * self.atr_multiplier
            return atr <= max_atr_allowed

        # Absolute threshold
        return self.min_atr <= atr <= self.max_atr

    def get_strength(self, df: pd.DataFrame, current_idx: int) -> float:
        """Volatility filter is binary - pass/fail"""
        return 100.0 if self.evaluate(df, current_idx) else 0.0

    def _calculate_atr(self, df: pd.DataFrame, idx: int) -> float:
        """Calculate Average True Range"""
        # Get data window
        high = df['high'].iloc[max(0, idx - self.atr_period):idx + 1]
        low = df['low'].iloc[max(0, idx - self.atr_period):idx + 1]
        close = df['close'].iloc[max(0, idx - self.atr_period):idx + 1]

        if len(high) < 2:
            return 0.0

        # Calculate True Range
        tr1 = high - low
        tr2 = abs(high - close.shift(1))
        tr3 = abs(low - close.shift(1))

        tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)

        # Average True Range
        atr = tr.rolling(window=self.atr_period).mean().iloc[-1]

        return atr if pd.notna(atr) else 0.0


# Register filter
signal_registry.register(VolatilityFilter, "filter")
