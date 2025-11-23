"""
Market Profile Indicators for ENCOM

Professional auction market theory indicators.
Used by institutional traders for value area and POC analysis.

Indicators:
- Point of Control (POC)
- Value Area High/Low (VAH/VAL)
- Volume Profile

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
def point_of_control_nb(high, low, close, volume, period=20, price_bins=50):
    """
    Point of Control (POC)

    Price level with highest volume in the period.
    Professional traders use this as major support/resistance.

    Args:
        high: High prices
        low: Low prices
        close: Close prices
        volume: Volume
        period: Lookback period (20)
        price_bins: Number of price bins for histogram (50)

    Returns:
        POC price levels
    """
    n = len(close)
    poc = np.zeros(n)

    for i in range(period - 1, n):
        # Get price range for period
        period_high = np.max(high[i - period + 1:i + 1])
        period_low = np.min(low[i - period + 1:i + 1])

        if period_high == period_low:
            poc[i] = close[i]
            continue

        # Create price bins
        bin_size = (period_high - period_low) / price_bins
        volume_at_price = np.zeros(price_bins)

        # Distribute volume across price bins
        for j in range(i - period + 1, i + 1):
            # Determine which bin this bar's price falls into
            price = (high[j] + low[j] + close[j]) / 3.0  # Typical price

            bin_idx = int((price - period_low) / bin_size)
            if bin_idx >= price_bins:
                bin_idx = price_bins - 1
            if bin_idx < 0:
                bin_idx = 0

            # Add volume to this price level
            volume_at_price[bin_idx] += volume[j]

        # Find bin with highest volume
        max_volume_idx = 0
        max_volume = volume_at_price[0]

        for k in range(1, price_bins):
            if volume_at_price[k] > max_volume:
                max_volume = volume_at_price[k]
                max_volume_idx = k

        # POC is the center price of the max volume bin
        poc[i] = period_low + (max_volume_idx + 0.5) * bin_size

    # Fill early values
    for i in range(period - 1):
        poc[i] = close[i]

    return poc


@njit(cache=True)
def value_area_nb(high, low, close, volume, period=20, price_bins=50, value_percent=0.70):
    """
    Value Area High/Low (VAH/VAL)

    Price range containing specified % of volume (typically 70%).
    Represents the "fair value" zone.

    Args:
        high: High prices
        low: Low prices
        close: Close prices
        volume: Volume
        period: Lookback period (20)
        price_bins: Number of price bins (50)
        value_percent: Percentage of volume (0.70 = 70%)

    Returns:
        Tuple of (VAH, VAL, POC)
    """
    n = len(close)
    vah = np.zeros(n)
    val = np.zeros(n)
    poc = np.zeros(n)

    for i in range(period - 1, n):
        # Get price range
        period_high = np.max(high[i - period + 1:i + 1])
        period_low = np.min(low[i - period + 1:i + 1])

        if period_high == period_low:
            vah[i] = close[i]
            val[i] = close[i]
            poc[i] = close[i]
            continue

        # Create volume profile
        bin_size = (period_high - period_low) / price_bins
        volume_at_price = np.zeros(price_bins)

        for j in range(i - period + 1, i + 1):
            price = (high[j] + low[j] + close[j]) / 3.0
            bin_idx = int((price - period_low) / bin_size)
            if bin_idx >= price_bins:
                bin_idx = price_bins - 1
            if bin_idx < 0:
                bin_idx = 0

            volume_at_price[bin_idx] += volume[j]

        # Find POC
        max_volume_idx = np.argmax(volume_at_price)
        poc[i] = period_low + (max_volume_idx + 0.5) * bin_size

        # Calculate Value Area
        total_volume = np.sum(volume_at_price)
        target_volume = total_volume * value_percent

        # Start from POC and expand outward
        va_volume = volume_at_price[max_volume_idx]
        va_low_idx = max_volume_idx
        va_high_idx = max_volume_idx

        while va_volume < target_volume:
            # Check which side has more volume
            volume_above = 0.0
            volume_below = 0.0

            if va_high_idx < price_bins - 1:
                volume_above = volume_at_price[va_high_idx + 1]

            if va_low_idx > 0:
                volume_below = volume_at_price[va_low_idx - 1]

            # Expand to side with more volume
            if volume_above >= volume_below and va_high_idx < price_bins - 1:
                va_high_idx += 1
                va_volume += volume_at_price[va_high_idx]
            elif va_low_idx > 0:
                va_low_idx -= 1
                va_volume += volume_at_price[va_low_idx]
            else:
                break

        # Convert indices to prices
        vah[i] = period_low + (va_high_idx + 1) * bin_size
        val[i] = period_low + va_low_idx * bin_size

    # Fill early values
    for i in range(period - 1):
        vah[i] = high[i]
        val[i] = low[i]
        poc[i] = close[i]

    return vah, val, poc


@njit(cache=True)
def volume_profile_nb(high, low, close, volume, period=20, price_bins=50):
    """
    Volume Profile

    Distribution of volume across price levels.
    Returns volume at each price level.

    Args:
        high: High prices
        low: Low prices
        close: Close prices
        volume: Volume
        period: Lookback period (20)
        price_bins: Number of price bins (50)

    Returns:
        2D array of volume distribution (n_bars x price_bins)
    """
    n = len(close)
    profile = np.zeros((n, price_bins))

    for i in range(period - 1, n):
        # Get price range
        period_high = np.max(high[i - period + 1:i + 1])
        period_low = np.min(low[i - period + 1:i + 1])

        if period_high == period_low:
            continue

        # Create histogram
        bin_size = (period_high - period_low) / price_bins

        for j in range(i - period + 1, i + 1):
            price = (high[j] + low[j] + close[j]) / 3.0
            bin_idx = int((price - period_low) / bin_size)

            if bin_idx >= price_bins:
                bin_idx = price_bins - 1
            if bin_idx < 0:
                bin_idx = 0

            profile[i, bin_idx] += volume[j]

    return profile


# ===================================
# Convenience Wrappers
# ===================================

def point_of_control(high, low, close, volume, period=20, price_bins=50):
    """Point of Control (POC)"""
    return point_of_control_nb(
        high.values if hasattr(high, 'values') else high,
        low.values if hasattr(low, 'values') else low,
        close.values if hasattr(close, 'values') else close,
        volume.values if hasattr(volume, 'values') else volume,
        period, price_bins
    )


def value_area(high, low, close, volume, period=20, price_bins=50, value_percent=0.70):
    """Value Area High/Low (VAH/VAL)"""
    return value_area_nb(
        high.values if hasattr(high, 'values') else high,
        low.values if hasattr(low, 'values') else low,
        close.values if hasattr(close, 'values') else close,
        volume.values if hasattr(volume, 'values') else volume,
        period, price_bins, value_percent
    )


def volume_profile(high, low, close, volume, period=20, price_bins=50):
    """Volume Profile"""
    return volume_profile_nb(
        high.values if hasattr(high, 'values') else high,
        low.values if hasattr(low, 'values') else low,
        close.values if hasattr(close, 'values') else close,
        volume.values if hasattr(volume, 'values') else volume,
        period, price_bins
    )
