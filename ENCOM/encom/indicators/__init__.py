"""
High-performance technical indicators with Numba JIT compilation

All indicators are vectorized and Numba-compiled for maximum speed.
Typical speedup: 20-50x faster than pandas-based implementations.

Usage:
    from encom.indicators import rsi, macd, atr, bollinger_bands

    # Calculate RSI for entire series at once
    rsi_values = rsi(df['close'].values, period=14)

    # Calculate MACD
    macd_line, signal_line, histogram = macd(df['close'].values)

    # Calculate Bollinger Bands
    middle, upper, lower = bollinger_bands(df['close'].values)
"""

from encom.indicators.momentum import (
    rsi, macd, ema, sma, stochastic,
    rsi_nb, macd_nb, ema_nb, sma_nb, stochastic_nb
)

from encom.indicators.volatility import (
    atr, bollinger_bands, std_dev, keltner_channels,
    atr_nb, bollinger_bands_nb, std_dev_nb, keltner_channels_nb
)

__all__ = [
    # Momentum indicators
    "rsi", "macd", "ema", "sma", "stochastic",
    "rsi_nb", "macd_nb", "ema_nb", "sma_nb", "stochastic_nb",

    # Volatility indicators
    "atr", "bollinger_bands", "std_dev", "keltner_channels",
    "atr_nb", "bollinger_bands_nb", "std_dev_nb", "keltner_channels_nb",
]
