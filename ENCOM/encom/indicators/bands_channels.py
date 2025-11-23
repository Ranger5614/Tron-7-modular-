"""
Bands and Channels for ENCOM

Additional bands, envelopes, and channel indicators.
Professional volatility bands for support/resistance.

Indicators (8):
- Envelope (Moving Average Envelope)
- Starc Bands
- Price Channel Bands
- High/Low Bands
- Median Price Bands
- Typical Price Bands
- Weighted Close Bands
- Acceleration Bands

Author: ENCOM Development Team
License: MIT
"""

import numpy as np
from numba import njit

try:
    from numba import njit
    NUMBA_AVAILABLE = True
except ImportError:
    def njit(*args, **kwargs):
        def decorator(func):
            return func
        return decorator if args and callable(args[0]) else decorator
    NUMBA_AVAILABLE = False


@njit(cache=True)
def envelope_nb(close, period=20, percent=2.5):
    """
    Moving Average Envelope
    
    Upper and lower bands around MA.
    
    Args:
        close: Close prices
        period: MA period (20)
        percent: Envelope percentage (2.5%)
    
    Returns:
        Tuple of (upper, middle, lower)
    """
    n = len(close)
    upper = np.zeros(n)
    middle = np.zeros(n)
    lower = np.zeros(n)
    
    # Calculate SMA
    for i in range(period - 1, n):
        middle[i] = np.mean(close[i - period + 1:i + 1])
        upper[i] = middle[i] * (1 + percent / 100)
        lower[i] = middle[i] * (1 - percent / 100)
    
    return upper, middle, lower


@njit(cache=True)
def starc_bands_nb(close, high, low, atr_period=15, ma_period=5, atr_multiplier=2.0):
    """
    Stoller Average Range Channels (STARC Bands)
    
    MA with ATR-based bands.
    
    Args:
        close: Close prices
        high: High prices
        low: Low prices
        atr_period: ATR period (15)
        ma_period: MA period (5)
        atr_multiplier: ATR multiplier (2.0)
    
    Returns:
        Tuple of (upper, middle, lower)
    """
    n = len(close)
    upper = np.zeros(n)
    middle = np.zeros(n)
    lower = np.zeros(n)
    
    # Calculate ATR
    tr = np.zeros(n)
    tr[0] = high[0] - low[0]
    for i in range(1, n):
        hl = high[i] - low[i]
        hc = abs(high[i] - close[i-1])
        lc = abs(low[i] - close[i-1])
        tr[i] = max(hl, hc, lc)
    
    atr = np.zeros(n)
    if n >= atr_period:
        atr[atr_period - 1] = np.mean(tr[:atr_period])
        for i in range(atr_period, n):
            atr[i] = (atr[i-1] * (atr_period - 1) + tr[i]) / atr_period
    
    # Calculate SMA
    for i in range(ma_period - 1, n):
        middle[i] = np.mean(close[i - ma_period + 1:i + 1])
        upper[i] = middle[i] + (atr[i] * atr_multiplier)
        lower[i] = middle[i] - (atr[i] * atr_multiplier)
    
    return upper, middle, lower


@njit(cache=True)
def price_channel_bands_nb(high, low, period=20):
    """
    Price Channel Bands
    
    Upper = highest high
    Lower = lowest low
    Middle = average
    
    Args:
        high: High prices
        low: Low prices
        period: Lookback period (20)
    
    Returns:
        Tuple of (upper, middle, lower)
    """
    n = len(high)
    upper = np.zeros(n)
    middle = np.zeros(n)
    lower = np.zeros(n)
    
    for i in range(period - 1, n):
        upper[i] = np.max(high[i - period + 1:i + 1])
        lower[i] = np.min(low[i - period + 1:i + 1])
        middle[i] = (upper[i] + lower[i]) / 2
    
    return upper, middle, lower


@njit(cache=True)
def median_price_bands_nb(high, low, period=20, std_mult=2.0):
    """
    Median Price Bands
    
    Bands around median price (high + low) / 2.
    
    Args:
        high: High prices
        low: Low prices
        period: Period (20)
        std_mult: Std dev multiplier (2.0)
    
    Returns:
        Tuple of (upper, middle, lower)
    """
    n = len(high)
    upper = np.zeros(n)
    middle = np.zeros(n)
    lower = np.zeros(n)
    
    # Median price
    median = (high + low) / 2
    
    for i in range(period - 1, n):
        # SMA of median
        middle[i] = np.mean(median[i - period + 1:i + 1])
        
        # Std dev
        std = np.std(median[i - period + 1:i + 1])
        
        upper[i] = middle[i] + (std * std_mult)
        lower[i] = middle[i] - (std * std_mult)
    
    return upper, middle, lower


@njit(cache=True)
def typical_price_bands_nb(high, low, close, period=20, std_mult=2.0):
    """
    Typical Price Bands
    
    Bands around typical price (high + low + close) / 3.
    
    Args:
        high: High prices
        low: Low prices
        close: Close prices
        period: Period (20)
        std_mult: Std dev multiplier (2.0)
    
    Returns:
        Tuple of (upper, middle, lower)
    """
    n = len(high)
    upper = np.zeros(n)
    middle = np.zeros(n)
    lower = np.zeros(n)
    
    # Typical price
    typical = (high + low + close) / 3
    
    for i in range(period - 1, n):
        # SMA of typical
        middle[i] = np.mean(typical[i - period + 1:i + 1])
        
        # Std dev
        std = np.std(typical[i - period + 1:i + 1])
        
        upper[i] = middle[i] + (std * std_mult)
        lower[i] = middle[i] - (std * std_mult)
    
    return upper, middle, lower


@njit(cache=True)
def weighted_close_bands_nb(high, low, close, period=20, std_mult=2.0):
    """
    Weighted Close Bands
    
    Bands around weighted close (high + low + 2*close) / 4.
    
    Args:
        high: High prices
        low: Low prices
        close: Close prices
        period: Period (20)
        std_mult: Std dev multiplier (2.0)
    
    Returns:
        Tuple of (upper, middle, lower)
    """
    n = len(high)
    upper = np.zeros(n)
    middle = np.zeros(n)
    lower = np.zeros(n)
    
    # Weighted close
    weighted = (high + low + 2 * close) / 4
    
    for i in range(period - 1, n):
        # SMA of weighted
        middle[i] = np.mean(weighted[i - period + 1:i + 1])
        
        # Std dev
        std = np.std(weighted[i - period + 1:i + 1])
        
        upper[i] = middle[i] + (std * std_mult)
        lower[i] = middle[i] - (std * std_mult)
    
    return upper, middle, lower


@njit(cache=True)
def acceleration_bands_nb(high, low, close, period=20, factor=4.0):
    """
    Acceleration Bands
    
    Uses price acceleration to create dynamic bands.
    
    Args:
        high: High prices
        low: Low prices
        close: Close prices
        period: Period (20)
        factor: Acceleration factor (4.0)
    
    Returns:
        Tuple of (upper, middle, lower)
    """
    n = len(close)
    upper = np.zeros(n)
    middle = np.zeros(n)
    lower = np.zeros(n)
    
    # Calculate SMA
    for i in range(period - 1, n):
        middle[i] = np.mean(close[i - period + 1:i + 1])
    
    # Calculate bands with acceleration
    for i in range(period, n):
        hl_avg = (high[i] + low[i]) / 2
        
        # Acceleration factor based on (high-low)/close
        if close[i] > 0:
            accel = (high[i] - low[i]) / close[i]
        else:
            accel = 0
        
        band_width = middle[i] * accel * factor
        
        upper[i] = middle[i] + band_width
        lower[i] = middle[i] - band_width
    
    return upper, middle, lower


@njit(cache=True)
def high_low_bands_nb(high, low, period=20):
    """
    High/Low Bands
    
    Simple bands based on high/low averages.
    
    Args:
        high: High prices
        low: Low prices
        period: Period (20)
    
    Returns:
        Tuple of (upper, middle, lower)
    """
    n = len(high)
    upper = np.zeros(n)
    middle = np.zeros(n)
    lower = np.zeros(n)
    
    for i in range(period - 1, n):
        upper[i] = np.mean(high[i - period + 1:i + 1])
        lower[i] = np.mean(low[i - period + 1:i + 1])
        middle[i] = (upper[i] + lower[i]) / 2
    
    return upper, middle, lower


# Convenience wrappers
def envelope(close, period=20, percent=2.5):
    """Moving Average Envelope"""
    return envelope_nb(
        close.values if hasattr(close, 'values') else close,
        period, percent
    )


def starc_bands(close, high, low, atr_period=15, ma_period=5, atr_multiplier=2.0):
    """STARC Bands"""
    return starc_bands_nb(
        close.values if hasattr(close, 'values') else close,
        high.values if hasattr(high, 'values') else high,
        low.values if hasattr(low, 'values') else low,
        atr_period, ma_period, atr_multiplier
    )


def price_channel_bands(high, low, period=20):
    """Price Channel Bands"""
    return price_channel_bands_nb(
        high.values if hasattr(high, 'values') else high,
        low.values if hasattr(low, 'values') else low,
        period
    )


def median_price_bands(high, low, period=20, std_mult=2.0):
    """Median Price Bands"""
    return median_price_bands_nb(
        high.values if hasattr(high, 'values') else high,
        low.values if hasattr(low, 'values') else low,
        period, std_mult
    )


def typical_price_bands(high, low, close, period=20, std_mult=2.0):
    """Typical Price Bands"""
    return typical_price_bands_nb(
        high.values if hasattr(high, 'values') else high,
        low.values if hasattr(low, 'values') else low,
        close.values if hasattr(close, 'values') else close,
        period, std_mult
    )


def weighted_close_bands(high, low, close, period=20, std_mult=2.0):
    """Weighted Close Bands"""
    return weighted_close_bands_nb(
        high.values if hasattr(high, 'values') else high,
        low.values if hasattr(low, 'values') else low,
        close.values if hasattr(close, 'values') else close,
        period, std_mult
    )


def acceleration_bands(high, low, close, period=20, factor=4.0):
    """Acceleration Bands"""
    return acceleration_bands_nb(
        high.values if hasattr(high, 'values') else high,
        low.values if hasattr(low, 'values') else low,
        close.values if hasattr(close, 'values') else close,
        period, factor
    )


def high_low_bands(high, low, period=20):
    """High/Low Bands"""
    return high_low_bands_nb(
        high.values if hasattr(high, 'values') else high,
        low.values if hasattr(low, 'values') else low,
        period
    )
