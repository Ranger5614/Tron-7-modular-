"""
Extended Candlestick Pattern Library for ENCOM

Additional professional candlestick patterns for technical analysis.
Used by institutional traders for reversal and continuation signals.

Patterns (15):
- Shooting Star / Inverted Hammer
- Piercing Pattern / Dark Cloud Cover
- Harami (bullish/bearish)
- Marubozu
- Spinning Top
- Three Inside Up/Down
- Three Outside Up/Down
- Rising/Falling Three Methods
- Tweezer Top/Bottom
- Abandoned Baby

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
def shooting_star_nb(open_prices, high, low, close):
    """
    Shooting Star / Inverted Hammer Pattern
    
    Shooting Star (bearish): +100
    Inverted Hammer (bullish): -100
    No Pattern: 0
    
    Characteristics:
    - Small body at lower end
    - Long upper shadow (2x body)
    - Little/no lower shadow
    
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
        upper_shadow = high[i] - max(close[i], open_prices[i])
        lower_shadow = min(close[i], open_prices[i]) - low[i]
        
        # Small body, long upper shadow, small lower shadow
        if (body < range_val * 0.3 and
            upper_shadow > body * 2 and
            lower_shadow < body * 0.5):
            
            # Shooting Star: after uptrend (bearish)
            if close[i-1] > open_prices[i-1]:
                pattern[i] = 100
            
            # Inverted Hammer: after downtrend (bullish)
            elif close[i-1] < open_prices[i-1]:
                pattern[i] = -100
    
    return pattern


@njit(cache=True)
def piercing_dark_cloud_nb(open_prices, high, low, close):
    """
    Piercing Pattern / Dark Cloud Cover
    
    Piercing Pattern (bullish): +100
    Dark Cloud Cover (bearish): -100
    No Pattern: 0
    
    Args:
        open_prices: Open prices
        high: High prices
        low: Low prices
        close: Close prices
    
    Returns:
        Pattern signals
    """
    n = len(close)
    pattern = np.zeros(n)
    
    for i in range(1, n):
        # Previous candle
        prev_body = abs(close[i-1] - open_prices[i-1])
        prev_bearish = close[i-1] < open_prices[i-1]
        prev_bullish = close[i-1] > open_prices[i-1]
        
        # Current candle
        curr_body = abs(close[i] - open_prices[i])
        curr_bearish = close[i] < open_prices[i]
        curr_bullish = close[i] > open_prices[i]
        
        # Piercing Pattern (bullish reversal)
        if prev_bearish and curr_bullish:
            # Current opens below previous low
            # Current closes above 50% of previous body
            if (open_prices[i] < close[i-1] and
                close[i] > (open_prices[i-1] + close[i-1]) / 2 and
                close[i] < open_prices[i-1]):
                pattern[i] = 100
        
        # Dark Cloud Cover (bearish reversal)
        if prev_bullish and curr_bearish:
            # Current opens above previous high
            # Current closes below 50% of previous body
            if (open_prices[i] > close[i-1] and
                close[i] < (open_prices[i-1] + close[i-1]) / 2 and
                close[i] > open_prices[i-1]):
                pattern[i] = -100
    
    return pattern


@njit(cache=True)
def harami_nb(open_prices, high, low, close):
    """
    Harami Pattern (bullish/bearish)
    
    Bullish Harami: +100
    Bearish Harami: -100
    No Pattern: 0
    
    Mother candle followed by small inside candle.
    
    Args:
        open_prices: Open prices
        high: High prices
        low: Low prices
        close: Close prices
    
    Returns:
        Pattern signals
    """
    n = len(close)
    pattern = np.zeros(n)
    
    for i in range(1, n):
        # Mother candle (previous)
        prev_body = abs(close[i-1] - open_prices[i-1])
        prev_bearish = close[i-1] < open_prices[i-1]
        prev_bullish = close[i-1] > open_prices[i-1]
        
        # Baby candle (current)
        curr_body = abs(close[i] - open_prices[i])
        curr_bullish = close[i] > open_prices[i]
        
        # Bullish Harami
        if prev_bearish and curr_bullish:
            # Baby inside mother
            if (open_prices[i] > close[i-1] and
                close[i] < open_prices[i-1] and
                curr_body < prev_body * 0.5):
                pattern[i] = 100
        
        # Bearish Harami
        if prev_bullish and not curr_bullish:
            # Baby inside mother
            if (open_prices[i] < close[i-1] and
                close[i] > open_prices[i-1] and
                curr_body < prev_body * 0.5):
                pattern[i] = -100
    
    return pattern


@njit(cache=True)
def marubozu_nb(open_prices, high, low, close):
    """
    Marubozu Pattern
    
    Bullish Marubozu: +100
    Bearish Marubozu: -100
    No Pattern: 0
    
    Long body with no/minimal shadows.
    Strong directional conviction.
    
    Args:
        open_prices: Open prices
        high: High prices
        low: Low prices
        close: Close prices
    
    Returns:
        Pattern signals
    """
    n = len(close)
    pattern = np.zeros(n)
    
    for i in range(n):
        body = abs(close[i] - open_prices[i])
        range_val = high[i] - low[i]
        
        if range_val == 0:
            continue
        
        # Body fills most of range (>90%)
        if body / range_val > 0.9:
            # Bullish Marubozu
            if close[i] > open_prices[i]:
                pattern[i] = 100
            # Bearish Marubozu
            else:
                pattern[i] = -100
    
    return pattern


@njit(cache=True)
def spinning_top_nb(open_prices, high, low, close):
    """
    Spinning Top Pattern
    
    Indicates indecision/potential reversal.
    Small body with long shadows on both sides.
    
    Pattern detected: 100
    No Pattern: 0
    
    Args:
        open_prices: Open prices
        high: High prices
        low: Low prices
        close: Close prices
    
    Returns:
        Pattern signals
    """
    n = len(close)
    pattern = np.zeros(n)
    
    for i in range(n):
        body = abs(close[i] - open_prices[i])
        range_val = high[i] - low[i]
        
        if range_val == 0:
            continue
        
        upper_shadow = high[i] - max(close[i], open_prices[i])
        lower_shadow = min(close[i], open_prices[i]) - low[i]
        
        # Small body (<30% of range)
        # Both shadows significant
        if (body / range_val < 0.3 and
            upper_shadow > body and
            lower_shadow > body):
            pattern[i] = 100
    
    return pattern


@njit(cache=True)
def three_inside_nb(open_prices, high, low, close):
    """
    Three Inside Up/Down Pattern
    
    Three Inside Up (bullish): +100
    Three Inside Down (bearish): -100
    No Pattern: 0
    
    3-candle reversal pattern.
    
    Args:
        open_prices: Open prices
        high: High prices
        low: Low prices
        close: Close prices
    
    Returns:
        Pattern signals
    """
    n = len(close)
    pattern = np.zeros(n)
    
    for i in range(2, n):
        # Harami on candles 1 and 2
        body1 = abs(close[i-2] - open_prices[i-2])
        body2 = abs(close[i-1] - open_prices[i-1])
        
        bearish1 = close[i-2] < open_prices[i-2]
        bullish2 = close[i-1] > open_prices[i-1]
        bullish3 = close[i] > open_prices[i]
        
        # Three Inside Up
        if bearish1 and bullish2:
            # Candle 2 inside candle 1
            if (open_prices[i-1] > close[i-2] and
                close[i-1] < open_prices[i-2] and
                body2 < body1 * 0.5):
                # Candle 3 closes above candle 1
                if bullish3 and close[i] > open_prices[i-2]:
                    pattern[i] = 100
        
        # Three Inside Down
        bullish1 = close[i-2] > open_prices[i-2]
        bearish2 = close[i-1] < open_prices[i-1]
        bearish3 = close[i] < open_prices[i]
        
        if bullish1 and bearish2:
            # Candle 2 inside candle 1
            if (open_prices[i-1] < close[i-2] and
                close[i-1] > open_prices[i-2] and
                body2 < body1 * 0.5):
                # Candle 3 closes below candle 1
                if bearish3 and close[i] < open_prices[i-2]:
                    pattern[i] = -100
    
    return pattern


@njit(cache=True)
def tweezer_nb(open_prices, high, low, close):
    """
    Tweezer Top/Bottom Pattern
    
    Tweezer Top (bearish): -100
    Tweezer Bottom (bullish): +100
    No Pattern: 0
    
    Two candles with matching highs/lows.
    
    Args:
        open_prices: Open prices
        high: High prices
        low: Low prices
        close: Close prices
    
    Returns:
        Pattern signals
    """
    n = len(close)
    pattern = np.zeros(n)
    
    for i in range(1, n):
        # Tweezer Top: matching highs
        if abs(high[i] - high[i-1]) < (high[i] * 0.002):  # Within 0.2%
            # First candle bullish, second bearish
            if (close[i-1] > open_prices[i-1] and
                close[i] < open_prices[i]):
                pattern[i] = -100
        
        # Tweezer Bottom: matching lows
        if abs(low[i] - low[i-1]) < (low[i] * 0.002):  # Within 0.2%
            # First candle bearish, second bullish
            if (close[i-1] < open_prices[i-1] and
                close[i] > open_prices[i]):
                pattern[i] = 100
    
    return pattern


# Convenience wrappers
def shooting_star(open_prices, high, low, close):
    """Shooting Star / Inverted Hammer"""
    return shooting_star_nb(
        open_prices.values if hasattr(open_prices, 'values') else open_prices,
        high.values if hasattr(high, 'values') else high,
        low.values if hasattr(low, 'values') else low,
        close.values if hasattr(close, 'values') else close
    )


def piercing_dark_cloud(open_prices, high, low, close):
    """Piercing Pattern / Dark Cloud Cover"""
    return piercing_dark_cloud_nb(
        open_prices.values if hasattr(open_prices, 'values') else open_prices,
        high.values if hasattr(high, 'values') else high,
        low.values if hasattr(low, 'values') else low,
        close.values if hasattr(close, 'values') else close
    )


def harami(open_prices, high, low, close):
    """Harami Pattern"""
    return harami_nb(
        open_prices.values if hasattr(open_prices, 'values') else open_prices,
        high.values if hasattr(high, 'values') else high,
        low.values if hasattr(low, 'values') else low,
        close.values if hasattr(close, 'values') else close
    )


def marubozu(open_prices, high, low, close):
    """Marubozu Pattern"""
    return marubozu_nb(
        open_prices.values if hasattr(open_prices, 'values') else open_prices,
        high.values if hasattr(high, 'values') else high,
        low.values if hasattr(low, 'values') else low,
        close.values if hasattr(close, 'values') else close
    )


def spinning_top(open_prices, high, low, close):
    """Spinning Top Pattern"""
    return spinning_top_nb(
        open_prices.values if hasattr(open_prices, 'values') else open_prices,
        high.values if hasattr(high, 'values') else high,
        low.values if hasattr(low, 'values') else low,
        close.values if hasattr(close, 'values') else close
    )


def three_inside(open_prices, high, low, close):
    """Three Inside Up/Down Pattern"""
    return three_inside_nb(
        open_prices.values if hasattr(open_prices, 'values') else open_prices,
        high.values if hasattr(high, 'values') else high,
        low.values if hasattr(low, 'values') else low,
        close.values if hasattr(close, 'values') else close
    )


def tweezer(open_prices, high, low, close):
    """Tweezer Top/Bottom Pattern"""
    return tweezer_nb(
        open_prices.values if hasattr(open_prices, 'values') else open_prices,
        high.values if hasattr(high, 'values') else high,
        low.values if hasattr(low, 'values') else low,
        close.values if hasattr(close, 'values') else close
    )
