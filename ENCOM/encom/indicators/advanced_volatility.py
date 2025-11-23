"""
Advanced Volatility Indicators for ENCOM

Professional volatility analysis with Numba optimization.

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
def historical_volatility_nb(close, period=20, annualize=True):
    """
    Historical Volatility (HV)

    Standard deviation of log returns.

    Args:
        close: Close prices
        period: Lookback period (20)
        annualize: Multiply by sqrt(252) for annual volatility

    Returns:
        Historical volatility (%)
    """
    n = len(close)
    hv = np.zeros(n)

    # Calculate log returns
    log_returns = np.zeros(n)
    for i in range(1, n):
        if close[i-1] > 0:
            log_returns[i] = np.log(close[i] / close[i-1])

    # Calculate rolling std dev
    for i in range(period, n):
        window = log_returns[i - period + 1:i + 1]
        hv[i] = np.std(window)

        if annualize:
            hv[i] *= np.sqrt(252)

    # Convert to percentage
    hv = hv * 100.0

    return hv


@njit(cache=True)
def ulcer_index_nb(close, period=14):
    """
    Ulcer Index

    Measures downside volatility (drawdown).

    Args:
        close: Close prices
        period: Lookback period (14)

    Returns:
        Ulcer Index values
    """
    n = len(close)
    ui = np.zeros(n)

    for i in range(period - 1, n):
        # Find highest close in period
        highest = np.max(close[i - period + 1:i + 1])

        # Calculate percentage drawdowns
        drawdowns_sq = 0.0

        for j in range(i - period + 1, i + 1):
            if highest > 0:
                dd = ((close[j] - highest) / highest) * 100.0
                drawdowns_sq += dd ** 2

        # Ulcer Index = sqrt(mean of squared drawdowns)
        ui[i] = np.sqrt(drawdowns_sq / period)

    return ui


@njit(cache=True)
def chaikin_volatility_nb(high, low, ema_period=10, roc_period=10):
    """
    Chaikin Volatility

    Volatility based on High-Low range.

    Args:
        high: High prices
        low: Low prices
        ema_period: EMA period for H-L range (10)
        roc_period: ROC period for volatility (10)

    Returns:
        Chaikin Volatility (%)
    """
    n = len(high)
    cv = np.zeros(n)

    # Calculate H-L range
    hl_range = high - low

    # EMA of H-L range
    ema = np.zeros(n)
    ema[0] = hl_range[0]
    alpha = 2.0 / (ema_period + 1)

    for i in range(1, n):
        ema[i] = alpha * hl_range[i] + (1 - alpha) * ema[i-1]

    # ROC of EMA
    for i in range(roc_period, n):
        if ema[i - roc_period] != 0:
            cv[i] = ((ema[i] - ema[i - roc_period]) / ema[i - roc_period]) * 100.0

    return cv


@njit(cache=True)
def natr_nb(high, low, close, period=14):
    """
    Normalized Average True Range (NATR)

    ATR as percentage of close price.

    Args:
        high: High prices
        low: Low prices
        close: Close prices
        period: ATR period (14)

    Returns:
        NATR values (%)
    """
    n = len(close)
    natr = np.zeros(n)

    # Calculate True Range
    tr = np.zeros(n)
    tr[0] = high[0] - low[0]

    for i in range(1, n):
        hl = high[i] - low[i]
        hc = abs(high[i] - close[i - 1])
        lc = abs(low[i] - close[i - 1])
        tr[i] = max(hl, hc, lc)

    # Calculate ATR
    atr = np.zeros(n)
    if n >= period:
        atr[period - 1] = np.mean(tr[:period])

        multiplier = 1.0 / period
        for i in range(period, n):
            atr[i] = atr[i - 1] + multiplier * (tr[i] - atr[i - 1])

        for i in range(period - 1):
            atr[i] = atr[period - 1]

    # Normalize by close price
    for i in range(n):
        if close[i] != 0:
            natr[i] = (atr[i] / close[i]) * 100.0

    return natr


@njit(cache=True)
def true_range_nb(high, low, close):
    """
    True Range (TR)

    Standalone True Range calculation.

    Args:
        high: High prices
        low: Low prices
        close: Close prices

    Returns:
        True Range values
    """
    n = len(close)
    tr = np.zeros(n)

    tr[0] = high[0] - low[0]

    for i in range(1, n):
        hl = high[i] - low[i]
        hc = abs(high[i] - close[i - 1])
        lc = abs(low[i] - close[i - 1])
        tr[i] = max(hl, hc, lc)

    return tr


@njit(cache=True)
def mass_index_nb(high, low, fast_period=9, slow_period=25):
    """
    Mass Index

    Identifies trend reversals using range expansion.

    Args:
        high: High prices
        low: Low prices
        fast_period: Fast EMA period (9)
        slow_period: Slow EMA period (25)

    Returns:
        Mass Index values
    """
    n = len(high)
    mass_index = np.zeros(n)

    # H-L range
    hl = high - low

    # Single EMA of H-L
    ema1 = np.zeros(n)
    ema1[0] = hl[0]
    alpha = 2.0 / (fast_period + 1)

    for i in range(1, n):
        ema1[i] = alpha * hl[i] + (1 - alpha) * ema1[i-1]

    # Double EMA
    ema2 = np.zeros(n)
    ema2[0] = ema1[0]

    for i in range(1, n):
        ema2[i] = alpha * ema1[i] + (1 - alpha) * ema2[i-1]

    # EMA ratio
    ema_ratio = np.zeros(n)
    for i in range(n):
        if ema2[i] != 0:
            ema_ratio[i] = ema1[i] / ema2[i]
        else:
            ema_ratio[i] = 1.0

    # Sum of ratio over slow_period
    for i in range(slow_period - 1, n):
        mass_index[i] = np.sum(ema_ratio[i - slow_period + 1:i + 1])

    return mass_index


@njit(cache=True)
def price_channels_nb(high, low, period=20):
    """
    Price Channels

    Similar to Donchian Channels.

    Args:
        high: High prices
        low: Low prices
        period: Lookback period (20)

    Returns:
        Tuple of (upper_channel, lower_channel)
    """
    n = len(high)
    upper = np.zeros(n)
    lower = np.zeros(n)

    for i in range(period - 1, n):
        upper[i] = np.max(high[i - period + 1:i + 1])
        lower[i] = np.min(low[i - period + 1:i + 1])

    # Fill early values
    for i in range(period - 1):
        if i > 0:
            upper[i] = np.max(high[:i + 1])
            lower[i] = np.min(low[:i + 1])

    return upper, lower


# Convenience wrappers
def historical_volatility(close, period=20, annualize=True):
    """Historical Volatility"""
    return historical_volatility_nb(close.values if hasattr(close, 'values') else close,
                                    period, annualize)


def ulcer_index(close, period=14):
    """Ulcer Index"""
    return ulcer_index_nb(close.values if hasattr(close, 'values') else close, period)


def chaikin_volatility(high, low, ema_period=10, roc_period=10):
    """Chaikin Volatility"""
    return chaikin_volatility_nb(high.values if hasattr(high, 'values') else high,
                                 low.values if hasattr(low, 'values') else low,
                                 ema_period, roc_period)


def natr(high, low, close, period=14):
    """Normalized ATR"""
    return natr_nb(high.values if hasattr(high, 'values') else high,
                   low.values if hasattr(low, 'values') else low,
                   close.values if hasattr(close, 'values') else close,
                   period)


def true_range(high, low, close):
    """True Range"""
    return true_range_nb(high.values if hasattr(high, 'values') else high,
                        low.values if hasattr(low, 'values') else low,
                        close.values if hasattr(close, 'values') else close)


def mass_index(high, low, fast_period=9, slow_period=25):
    """Mass Index"""
    return mass_index_nb(high.values if hasattr(high, 'values') else high,
                        low.values if hasattr(low, 'values') else low,
                        fast_period, slow_period)


def price_channels(high, low, period=20):
    """Price Channels"""
    return price_channels_nb(high.values if hasattr(high, 'values') else high,
                            low.values if hasattr(low, 'values') else low,
                            period)
