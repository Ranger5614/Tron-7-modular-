"""
Pattern Recognition Indicators for ENCOM

Algorithmic identification of candlestick and chart patterns.
Professional pattern detection used by institutional traders.

Patterns:
- Engulfing (bullish/bearish)
- Doji
- Hammer & Hanging Man
- Morning Star / Evening Star
- Three White Soldiers / Three Black Crows

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
def engulfing_pattern_nb(open_prices, high, low, close):
    """
    Engulfing Pattern Detection

    Bullish Engulfing: +100
    Bearish Engulfing: -100
    No Pattern: 0

    Args:
        open_prices: Open prices
        high: High prices
        low: Low prices
        close: Close prices

    Returns:
        Pattern signals (+100, -100, or 0)
    """
    n = len(close)
    pattern = np.zeros(n)

    for i in range(1, n):
        # Previous candle
        prev_body = abs(close[i-1] - open_prices[i-1])
        prev_bullish = close[i-1] > open_prices[i-1]

        # Current candle
        curr_body = abs(close[i] - open_prices[i])
        curr_bullish = close[i] > open_prices[i]

        # Bullish Engulfing
        if (not prev_bullish) and curr_bullish:
            # Current body engulfs previous body
            if (close[i] > open_prices[i-1] and
                open_prices[i] < close[i-1] and
                curr_body > prev_body * 1.1):  # 10% larger
                pattern[i] = 100

        # Bearish Engulfing
        if prev_bullish and (not curr_bullish):
            # Current body engulfs previous body
            if (open_prices[i] > close[i-1] and
                close[i] < open_prices[i-1] and
                curr_body > prev_body * 1.1):
                pattern[i] = -100

    return pattern


@njit(cache=True)
def doji_pattern_nb(open_prices, high, low, close, body_threshold=0.1):
    """
    Doji Pattern Detection

    Identifies indecision candles where open ≈ close.

    Args:
        open_prices: Open prices
        high: High prices
        low: Low prices
        close: Close prices
        body_threshold: Max body as % of range (0.1 = 10%)

    Returns:
        Pattern signals (100 for doji, 0 otherwise)
    """
    n = len(close)
    pattern = np.zeros(n)

    for i in range(n):
        body = abs(close[i] - open_prices[i])
        range_val = high[i] - low[i]

        if range_val > 0:
            body_pct = body / range_val

            # Doji: body is very small relative to range
            if body_pct <= body_threshold:
                pattern[i] = 100

    return pattern


@njit(cache=True)
def hammer_pattern_nb(open_prices, high, low, close):
    """
    Hammer & Hanging Man Pattern Detection

    Hammer (bullish reversal): +100
    Hanging Man (bearish reversal): -100
    No Pattern: 0

    Args:
        open_prices: Open prices
        high: High prices
        low: Low prices
        close: Close prices

    Returns:
        Pattern signals (+100, -100, or 0)
    """
    n = len(close)
    pattern = np.zeros(n)

    for i in range(1, n):
        body = abs(close[i] - open_prices[i])
        range_val = high[i] - low[i]

        if range_val == 0:
            continue

        # Upper and lower shadows
        if close[i] > open_prices[i]:
            upper_shadow = high[i] - close[i]
            lower_shadow = open_prices[i] - low[i]
        else:
            upper_shadow = high[i] - open_prices[i]
            lower_shadow = close[i] - low[i]

        # Hammer characteristics:
        # - Small body
        # - Long lower shadow (2x body)
        # - Little/no upper shadow
        if (body < range_val * 0.3 and
            lower_shadow > body * 2 and
            upper_shadow < body * 0.5):

            # Hammer: after downtrend (bullish reversal)
            if close[i-1] < open_prices[i-1]:
                pattern[i] = 100

            # Hanging Man: after uptrend (bearish reversal)
            elif close[i-1] > open_prices[i-1]:
                pattern[i] = -100

    return pattern


@njit(cache=True)
def morning_evening_star_nb(open_prices, high, low, close):
    """
    Morning Star / Evening Star Pattern Detection

    Three-candle reversal patterns.

    Morning Star (bullish reversal): +100
    Evening Star (bearish reversal): -100
    No Pattern: 0

    Args:
        open_prices: Open prices
        high: High prices
        low: Low prices
        close: Close prices

    Returns:
        Pattern signals (+100, -100, or 0)
    """
    n = len(close)
    pattern = np.zeros(n)

    for i in range(2, n):
        # Three candles
        body1 = abs(close[i-2] - open_prices[i-2])
        body2 = abs(close[i-1] - open_prices[i-1])
        body3 = abs(close[i] - open_prices[i])

        # Morning Star (bullish reversal)
        # 1. Long bearish candle
        # 2. Small body (star)
        # 3. Long bullish candle
        bearish1 = close[i-2] < open_prices[i-2]
        small_body2 = body2 < body1 * 0.3
        bullish3 = close[i] > open_prices[i]

        if (bearish1 and small_body2 and bullish3 and
            body3 > body1 * 0.8):
            # Star gaps down, then gaps up
            if (close[i-1] < close[i-2] and
                close[i] > (open_prices[i-2] + close[i-2]) / 2):
                pattern[i] = 100

        # Evening Star (bearish reversal)
        bullish1 = close[i-2] > open_prices[i-2]
        bearish3 = close[i] < open_prices[i]

        if (bullish1 and small_body2 and bearish3 and
            body3 > body1 * 0.8):
            # Star gaps up, then gaps down
            if (close[i-1] > close[i-2] and
                close[i] < (open_prices[i-2] + close[i-2]) / 2):
                pattern[i] = -100

    return pattern


@njit(cache=True)
def three_soldiers_crows_nb(open_prices, high, low, close):
    """
    Three White Soldiers / Three Black Crows Pattern Detection

    Strong trend continuation patterns.

    Three White Soldiers (bullish): +100
    Three Black Crows (bearish): -100
    No Pattern: 0

    Args:
        open_prices: Open prices
        high: High prices
        low: Low prices
        close: Close prices

    Returns:
        Pattern signals (+100, -100, or 0)
    """
    n = len(close)
    pattern = np.zeros(n)

    for i in range(2, n):
        # Three consecutive candles
        bullish1 = close[i-2] > open_prices[i-2]
        bullish2 = close[i-1] > open_prices[i-1]
        bullish3 = close[i] > open_prices[i]

        bearish1 = close[i-2] < open_prices[i-2]
        bearish2 = close[i-1] < open_prices[i-1]
        bearish3 = close[i] < open_prices[i]

        # Three White Soldiers
        if bullish1 and bullish2 and bullish3:
            # Each candle closes higher
            if close[i-1] > close[i-2] and close[i] > close[i-1]:
                # Each candle opens within previous body
                if (open_prices[i-1] > open_prices[i-2] and
                    open_prices[i-1] < close[i-2] and
                    open_prices[i] > open_prices[i-1] and
                    open_prices[i] < close[i-1]):
                    # Similar size candles
                    body1 = close[i-2] - open_prices[i-2]
                    body2 = close[i-1] - open_prices[i-1]
                    body3 = close[i] - open_prices[i]

                    if (body2 > body1 * 0.7 and body2 < body1 * 1.5 and
                        body3 > body2 * 0.7 and body3 < body2 * 1.5):
                        pattern[i] = 100

        # Three Black Crows
        if bearish1 and bearish2 and bearish3:
            # Each candle closes lower
            if close[i-1] < close[i-2] and close[i] < close[i-1]:
                # Each candle opens within previous body
                if (open_prices[i-1] < open_prices[i-2] and
                    open_prices[i-1] > close[i-2] and
                    open_prices[i] < open_prices[i-1] and
                    open_prices[i] > close[i-1]):
                    # Similar size candles
                    body1 = open_prices[i-2] - close[i-2]
                    body2 = open_prices[i-1] - close[i-1]
                    body3 = open_prices[i] - close[i]

                    if (body2 > body1 * 0.7 and body2 < body1 * 1.5 and
                        body3 > body2 * 0.7 and body3 < body2 * 1.5):
                        pattern[i] = -100

    return pattern


# ===================================
# Convenience Wrappers
# ===================================

def engulfing_pattern(open_prices, high, low, close):
    """Engulfing Pattern Detection"""
    return engulfing_pattern_nb(
        open_prices.values if hasattr(open_prices, 'values') else open_prices,
        high.values if hasattr(high, 'values') else high,
        low.values if hasattr(low, 'values') else low,
        close.values if hasattr(close, 'values') else close
    )


def doji_pattern(open_prices, high, low, close, body_threshold=0.1):
    """Doji Pattern Detection"""
    return doji_pattern_nb(
        open_prices.values if hasattr(open_prices, 'values') else open_prices,
        high.values if hasattr(high, 'values') else high,
        low.values if hasattr(low, 'values') else low,
        close.values if hasattr(close, 'values') else close,
        body_threshold
    )


def hammer_pattern(open_prices, high, low, close):
    """Hammer & Hanging Man Pattern Detection"""
    return hammer_pattern_nb(
        open_prices.values if hasattr(open_prices, 'values') else open_prices,
        high.values if hasattr(high, 'values') else high,
        low.values if hasattr(low, 'values') else low,
        close.values if hasattr(close, 'values') else close
    )


def morning_evening_star(open_prices, high, low, close):
    """Morning Star / Evening Star Pattern Detection"""
    return morning_evening_star_nb(
        open_prices.values if hasattr(open_prices, 'values') else open_prices,
        high.values if hasattr(high, 'values') else high,
        low.values if hasattr(low, 'values') else low,
        close.values if hasattr(close, 'values') else close
    )


def three_soldiers_crows(open_prices, high, low, close):
    """Three White Soldiers / Three Black Crows Pattern Detection"""
    return three_soldiers_crows_nb(
        open_prices.values if hasattr(open_prices, 'values') else open_prices,
        high.values if hasattr(high, 'values') else high,
        low.values if hasattr(low, 'values') else low,
        close.values if hasattr(close, 'values') else close
    )
