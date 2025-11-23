"""
Advanced Volume Indicators for ENCOM

Professional volume analysis beyond basic volume indicators.
Institutional-grade volume pressure and momentum analysis.

Indicators:
- Volume Rate of Change (VROC)
- Klinger Volume Oscillator (KVO)
- Ease of Movement (EMV)

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
def volume_roc_nb(volume, period=12):
    """
    Volume Rate of Change (VROC)

    Percentage change in volume over period.
    Identifies volume surges and drying up.

    Args:
        volume: Volume
        period: Lookback period (12)

    Returns:
        Volume ROC (%)
    """
    n = len(volume)
    vroc = np.zeros(n)

    for i in range(period, n):
        if volume[i - period] > 0:
            vroc[i] = ((volume[i] - volume[i - period]) / volume[i - period]) * 100.0

    return vroc


@njit(cache=True)
def klinger_volume_oscillator_nb(high, low, close, volume, fast_period=34, slow_period=55, signal_period=13):
    """
    Klinger Volume Oscillator (KVO)

    Measures the difference between two volume-weighted moving averages.
    Identifies long-term money flow trends.

    Args:
        high: High prices
        low: Low prices
        close: Close prices
        volume: Volume
        fast_period: Fast EMA period (34)
        slow_period: Slow EMA period (55)
        signal_period: Signal line period (13)

    Returns:
        Tuple of (KVO, Signal Line)
    """
    n = len(close)
    kvo = np.zeros(n)
    signal = np.zeros(n)

    # Calculate trend (typical price comparison)
    trend = np.zeros(n)
    for i in range(1, n):
        tp_current = (high[i] + low[i] + close[i]) / 3.0
        tp_prev = (high[i-1] + low[i-1] + close[i-1]) / 3.0

        if tp_current > tp_prev:
            trend[i] = 1.0
        else:
            trend[i] = -1.0

    # Calculate volume force
    volume_force = np.zeros(n)
    for i in range(1, n):
        dm = high[i] - low[i]  # Daily movement

        if dm > 0:
            # Volume Force = Volume * Trend * (2 * ((dm / cm) - 1))
            # Simplified: Volume * Trend
            volume_force[i] = volume[i] * trend[i]
        else:
            volume_force[i] = 0

    # Fast EMA of volume force
    fast_ema = np.zeros(n)
    fast_alpha = 2.0 / (fast_period + 1)
    fast_ema[0] = volume_force[0]

    for i in range(1, n):
        fast_ema[i] = fast_alpha * volume_force[i] + (1 - fast_alpha) * fast_ema[i-1]

    # Slow EMA of volume force
    slow_ema = np.zeros(n)
    slow_alpha = 2.0 / (slow_period + 1)
    slow_ema[0] = volume_force[0]

    for i in range(1, n):
        slow_ema[i] = slow_alpha * volume_force[i] + (1 - slow_alpha) * slow_ema[i-1]

    # KVO = Fast EMA - Slow EMA
    kvo = fast_ema - slow_ema

    # Signal line (EMA of KVO)
    signal[0] = kvo[0]
    signal_alpha = 2.0 / (signal_period + 1)

    for i in range(1, n):
        signal[i] = signal_alpha * kvo[i] + (1 - signal_alpha) * signal[i-1]

    return kvo, signal


@njit(cache=True)
def ease_of_movement_nb(high, low, volume, period=14, divisor=10000):
    """
    Ease of Movement (EMV)

    Relates price change to volume.
    High EMV = price moves easily with little volume.
    Low EMV = price requires high volume to move.

    Args:
        high: High prices
        low: Low prices
        volume: Volume
        period: SMA period (14)
        divisor: Scale factor (10000)

    Returns:
        EMV values
    """
    n = len(high)
    emv = np.zeros(n)
    emv_ma = np.zeros(n)

    for i in range(1, n):
        # Distance moved
        midpoint_move = ((high[i] + low[i]) / 2.0) - ((high[i-1] + low[i-1]) / 2.0)

        # Box ratio (volume to range)
        box_height = high[i] - low[i]

        if box_height > 0 and volume[i] > 0:
            box_ratio = (volume[i] / divisor) / box_height

            # EMV = Distance / Box Ratio
            if box_ratio != 0:
                emv[i] = midpoint_move / box_ratio
        else:
            emv[i] = 0

    # SMA of EMV
    for i in range(period - 1, n):
        emv_ma[i] = np.mean(emv[i - period + 1:i + 1])

    return emv_ma


@njit(cache=True)
def negative_volume_index_nb(close, volume):
    """
    Negative Volume Index (NVI)

    Accumulates price changes only on days when volume decreases.
    Tracks "smart money" activity (low volume moves).

    Args:
        close: Close prices
        volume: Volume

    Returns:
        NVI values
    """
    n = len(close)
    nvi = np.zeros(n)
    nvi[0] = 1000  # Start at 1000

    for i in range(1, n):
        # Only update on volume decrease
        if volume[i] < volume[i-1]:
            pct_change = (close[i] - close[i-1]) / close[i-1]
            nvi[i] = nvi[i-1] + (pct_change * nvi[i-1])
        else:
            nvi[i] = nvi[i-1]

    return nvi


@njit(cache=True)
def positive_volume_index_nb(close, volume):
    """
    Positive Volume Index (PVI)

    Accumulates price changes only on days when volume increases.
    Tracks retail activity (high volume moves).

    Args:
        close: Close prices
        volume: Volume

    Returns:
        PVI values
    """
    n = len(close)
    pvi = np.zeros(n)
    pvi[0] = 1000  # Start at 1000

    for i in range(1, n):
        # Only update on volume increase
        if volume[i] > volume[i-1]:
            pct_change = (close[i] - close[i-1]) / close[i-1]
            pvi[i] = pvi[i-1] + (pct_change * pvi[i-1])
        else:
            pvi[i] = pvi[i-1]

    return pvi


# ===================================
# Convenience Wrappers
# ===================================

def volume_roc(volume, period=12):
    """Volume Rate of Change"""
    return volume_roc_nb(
        volume.values if hasattr(volume, 'values') else volume,
        period
    )


def klinger_volume_oscillator(high, low, close, volume, fast_period=34, slow_period=55, signal_period=13):
    """Klinger Volume Oscillator"""
    return klinger_volume_oscillator_nb(
        high.values if hasattr(high, 'values') else high,
        low.values if hasattr(low, 'values') else low,
        close.values if hasattr(close, 'values') else close,
        volume.values if hasattr(volume, 'values') else volume,
        fast_period, slow_period, signal_period
    )


def ease_of_movement(high, low, volume, period=14, divisor=10000):
    """Ease of Movement"""
    return ease_of_movement_nb(
        high.values if hasattr(high, 'values') else high,
        low.values if hasattr(low, 'values') else low,
        volume.values if hasattr(volume, 'values') else volume,
        period, divisor
    )


def negative_volume_index(close, volume):
    """Negative Volume Index"""
    return negative_volume_index_nb(
        close.values if hasattr(close, 'values') else close,
        volume.values if hasattr(volume, 'values') else volume
    )


def positive_volume_index(close, volume):
    """Positive Volume Index"""
    return positive_volume_index_nb(
        close.values if hasattr(close, 'values') else close,
        volume.values if hasattr(volume, 'values') else volume
    )
