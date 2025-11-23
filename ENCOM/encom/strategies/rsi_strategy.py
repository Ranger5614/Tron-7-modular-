"""
RSI Mean Reversion Strategy
"""

from encom.strategies.base_strategy import BaseStrategy
from encom.signals.core_signals import RSISignal
from encom.signals.filters import VolumeFilter, VolatilityFilter


class RSIMeanReversionStrategy(BaseStrategy):
    """
    RSI Mean Reversion Strategy

    Entry: RSI crosses above oversold (30)
    Filters: Minimum volume, moderate volatility

    Parameters:
    - rsi_period: RSI calculation period (default: 14)
    - oversold: Oversold threshold (default: 30)
    - min_volume: Minimum daily volume (default: 1M)
    - max_atr_mult: Max ATR as % of price (default: 5%)
    """

    def __init__(self, **params):
        super().__init__("RSI Mean Reversion")
        self.params = params

    def build(self):
        """Build RSI mean reversion strategy"""
        # Core signal: RSI oversold
        rsi_signal = RSISignal(params={
            "period": self.params.get("rsi_period", 14),
            "oversold": self.params.get("oversold", 30),
            "overbought": self.params.get("overbought", 70),
        })
        self.engine.set_core_signal(rsi_signal)

        # Filter 1: Minimum volume
        volume_filter = VolumeFilter(params={
            "min_volume_usd": self.params.get("min_volume", 1_000_000)
        })
        self.engine.filter_engine.add_filter(volume_filter)

        # Filter 2: Volatility (avoid extreme volatility)
        volatility_filter = VolatilityFilter(params={
            "atr_period": 14,
            "atr_multiplier": self.params.get("max_atr_mult", 0.05)
        })
        self.engine.filter_engine.add_filter(volatility_filter)

        return self.engine
