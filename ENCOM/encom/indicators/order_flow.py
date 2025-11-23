"""
Order Flow Indicators for ENCOM

Professional tape reading indicators for institutional trading.
Analyzes buying/selling pressure and aggressive order flow.

Indicators:
- Delta Volume (Buy/Sell Imbalance)
- Cumulative Volume Delta (CVD)
- Aggressive Buy/Sell Ratio

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
def delta_volume_nb(high, low, close, volume):
    """
    Delta Volume

    Estimates buy volume minus sell volume per bar.
    Positive = buying pressure, Negative = selling pressure.

    Approximation based on price movement within bar:
    - If close > open: bullish bar, more buying
    - If close < open: bearish bar, more selling

    Args:
        high: High prices
        low: Low prices
        close: Close prices
        volume: Volume

    Returns:
        Delta volume (buy - sell)
    """
    n = len(close)
    delta = np.zeros(n)

    # Use close-to-close change as proxy
    for i in range(1, n):
        price_change = close[i] - close[i-1]
        range_val = high[i] - low[i]

        if range_val > 0:
            # Estimate buy/sell based on where close is in range
            close_position = (close[i] - low[i]) / range_val  # 0 to 1

            # If close near high: more buying
            # If close near low: more selling
            buy_volume = volume[i] * close_position
            sell_volume = volume[i] * (1 - close_position)

            delta[i] = buy_volume - sell_volume
        else:
            # No range, use price change direction
            if price_change > 0:
                delta[i] = volume[i]
            elif price_change < 0:
                delta[i] = -volume[i]
            else:
                delta[i] = 0

    return delta


@njit(cache=True)
def cumulative_volume_delta_nb(high, low, close, volume):
    """
    Cumulative Volume Delta (CVD)

    Running sum of delta volume.
    Shows persistent buying or selling pressure.

    Args:
        high: High prices
        low: Low prices
        close: Close prices
        volume: Volume

    Returns:
        Cumulative delta volume
    """
    # Calculate delta
    delta = delta_volume_nb(high, low, close, volume)

    # Cumulative sum
    cvd = np.cumsum(delta)

    return cvd


@njit(cache=True)
def aggressive_ratio_nb(high, low, close, volume, period=20):
    """
    Aggressive Buy/Sell Ratio

    Ratio of aggressive buying to aggressive selling.
    > 1.0 = more aggressive buying
    < 1.0 = more aggressive selling

    Aggressive trades estimated by:
    - Upticks on high volume = aggressive buying
    - Downticks on high volume = aggressive selling

    Args:
        high: High prices
        low: Low prices
        close: Close prices
        volume: Volume
        period: Lookback period (20)

    Returns:
        Aggressive buy/sell ratio
    """
    n = len(close)
    ratio = np.ones(n)  # Default to 1.0 (neutral)

    for i in range(period, n):
        aggressive_buy = 0.0
        aggressive_sell = 0.0

        # Calculate average volume for threshold
        avg_volume = np.mean(volume[i - period:i])

        for j in range(i - period + 1, i + 1):
            if j < 1:
                continue

            price_change = close[j] - close[j-1]
            vol = volume[j]

            # Only count if volume above average (aggressive)
            if vol > avg_volume:
                if price_change > 0:
                    aggressive_buy += vol
                elif price_change < 0:
                    aggressive_sell += vol

        # Calculate ratio
        if aggressive_sell > 0:
            ratio[i] = aggressive_buy / aggressive_sell
        elif aggressive_buy > 0:
            ratio[i] = 2.0  # Strong buying, no selling
        else:
            ratio[i] = 1.0  # Neutral

    # Fill early values
    for i in range(period):
        ratio[i] = 1.0

    return ratio


@njit(cache=True)
def volume_pace_nb(volume, period=20):
    """
    Volume Pace

    Rate of volume accumulation relative to time.
    High pace = rapid volume = institutional activity.

    Args:
        volume: Volume
        period: Lookback period (20)

    Returns:
        Volume pace (volume per bar)
    """
    n = len(volume)
    pace = np.zeros(n)

    for i in range(period - 1, n):
        # Total volume in period
        total_vol = np.sum(volume[i - period + 1:i + 1])

        # Pace = volume per bar
        pace[i] = total_vol / period

    # Fill early values with current volume
    for i in range(period - 1):
        pace[i] = volume[i]

    return pace


# ===================================
# Convenience Wrappers
# ===================================

def delta_volume(high, low, close, volume):
    """Delta Volume (Buy - Sell)"""
    return delta_volume_nb(
        high.values if hasattr(high, 'values') else high,
        low.values if hasattr(low, 'values') else low,
        close.values if hasattr(close, 'values') else close,
        volume.values if hasattr(volume, 'values') else volume
    )


def cumulative_volume_delta(high, low, close, volume):
    """Cumulative Volume Delta (CVD)"""
    return cumulative_volume_delta_nb(
        high.values if hasattr(high, 'values') else high,
        low.values if hasattr(low, 'values') else low,
        close.values if hasattr(close, 'values') else close,
        volume.values if hasattr(volume, 'values') else volume
    )


def aggressive_ratio(high, low, close, volume, period=20):
    """Aggressive Buy/Sell Ratio"""
    return aggressive_ratio_nb(
        high.values if hasattr(high, 'values') else high,
        low.values if hasattr(low, 'values') else low,
        close.values if hasattr(close, 'values') else close,
        volume.values if hasattr(volume, 'values') else volume,
        period
    )


def volume_pace(volume, period=20):
    """Volume Pace"""
    return volume_pace_nb(
        volume.values if hasattr(volume, 'values') else volume,
        period
    )
