"""
Additional Oscillators for ENCOM

Professional oscillators and momentum indicators.
Used for overbought/oversold conditions and divergence analysis.

Indicators (11):
- Stochastic RSI
- True Strength Index (TSI)
- Money Flow Index (MFI) - enhanced
- Ultimate Oscillator
- Percentage Price Oscillator (PPO)
- Balance of Power (BOP)
- Chande Momentum Oscillator (CMO)
- Relative Vigor Index (RVI)
- Psychological Line (PSY)
- Aroon Oscillator
- Commodity Selection Index (CSI)

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
def stochastic_rsi_nb(close, rsi_period=14, stoch_period=14):
    """
    Stochastic RSI
    
    Applies stochastic oscillator to RSI values.
    More sensitive than regular stochastic.
    
    Args:
        close: Close prices
        rsi_period: RSI period (14)
        stoch_period: Stochastic period (14)
    
    Returns:
        Stochastic RSI (0-100)
    """
    n = len(close)
    
    # Calculate RSI first
    rsi = np.zeros(n)
    gains = np.zeros(n)
    losses = np.zeros(n)
    
    for i in range(1, n):
        change = close[i] - close[i-1]
        if change > 0:
            gains[i] = change
        else:
            losses[i] = abs(change)
    
    # Calculate average gains/losses
    avg_gain = np.zeros(n)
    avg_loss = np.zeros(n)
    
    if n >= rsi_period:
        avg_gain[rsi_period - 1] = np.mean(gains[:rsi_period])
        avg_loss[rsi_period - 1] = np.mean(losses[:rsi_period])
        
        for i in range(rsi_period, n):
            avg_gain[i] = (avg_gain[i-1] * (rsi_period - 1) + gains[i]) / rsi_period
            avg_loss[i] = (avg_loss[i-1] * (rsi_period - 1) + losses[i]) / rsi_period
    
    # Calculate RSI
    for i in range(rsi_period - 1, n):
        if avg_loss[i] == 0:
            rsi[i] = 100
        else:
            rs = avg_gain[i] / avg_loss[i]
            rsi[i] = 100 - (100 / (1 + rs))
    
    # Apply stochastic to RSI
    stoch_rsi = np.zeros(n)
    
    for i in range(stoch_period + rsi_period - 1, n):
        rsi_window = rsi[i - stoch_period + 1:i + 1]
        rsi_min = np.min(rsi_window)
        rsi_max = np.max(rsi_window)
        
        if rsi_max - rsi_min > 0:
            stoch_rsi[i] = ((rsi[i] - rsi_min) / (rsi_max - rsi_min)) * 100
    
    return stoch_rsi


@njit(cache=True)
def relative_vigor_index_nb(open_prices, high, low, close, period=10):
    """
    Relative Vigor Index (RVI)
    
    Measures conviction of price movement.
    
    Args:
        open_prices: Open prices
        high: High prices
        low: Low prices
        close: Close prices
        period: RVI period (10)
    
    Returns:
        RVI values
    """
    n = len(close)
    rvi = np.zeros(n)
    
    for i in range(period - 1, n):
        # Numerator: close - open
        num_sum = 0.0
        for j in range(i - period + 1, i + 1):
            num_sum += (close[j] - open_prices[j])
        
        # Denominator: high - low
        den_sum = 0.0
        for j in range(i - period + 1, i + 1):
            den_sum += (high[j] - low[j])
        
        if den_sum != 0:
            rvi[i] = num_sum / den_sum
    
    return rvi


@njit(cache=True)
def psychological_line_nb(close, period=12):
    """
    Psychological Line (PSY)
    
    Percentage of rising days in period.
    
    Args:
        close: Close prices
        period: Lookback period (12)
    
    Returns:
        PSY values (0-100)
    """
    n = len(close)
    psy = np.zeros(n)
    
    for i in range(period, n):
        rising_days = 0
        for j in range(i - period + 1, i + 1):
            if close[j] > close[j-1]:
                rising_days += 1
        
        psy[i] = (rising_days / period) * 100
    
    return psy


@njit(cache=True)
def aroon_oscillator_nb(high, low, period=25):
    """
    Aroon Oscillator
    
    Difference between Aroon Up and Aroon Down.
    Ranges from -100 to +100.
    
    Args:
        high: High prices
        low: Low prices
        period: Aroon period (25)
    
    Returns:
        Aroon Oscillator (-100 to +100)
    """
    n = len(high)
    aroon_osc = np.zeros(n)
    
    for i in range(period, n):
        # Days since highest high
        highest_idx = i - period
        for j in range(i - period, i + 1):
            if high[j] >= high[highest_idx]:
                highest_idx = j
        days_since_high = i - highest_idx
        aroon_up = ((period - days_since_high) / period) * 100
        
        # Days since lowest low
        lowest_idx = i - period
        for j in range(i - period, i + 1):
            if low[j] <= low[lowest_idx]:
                lowest_idx = j
        days_since_low = i - lowest_idx
        aroon_down = ((period - days_since_low) / period) * 100
        
        # Oscillator
        aroon_osc[i] = aroon_up - aroon_down
    
    return aroon_osc


@njit(cache=True)
def commodity_selection_index_nb(close, atr, period=14):
    """
    Commodity Selection Index (CSI)
    
    Identifies trending commodities/stocks.
    Higher CSI = better trending candidate.
    
    Args:
        close: Close prices
        atr: ATR values
        period: Lookback period (14)
    
    Returns:
        CSI values
    """
    n = len(close)
    csi = np.zeros(n)
    
    for i in range(period, n):
        # Directional movement
        dm = close[i] - close[i - period]
        
        # Average ATR over period
        avg_atr = np.mean(atr[i - period:i + 1])
        
        if avg_atr > 0:
            # CSI = (DM / (ATR * sqrt(margin)))
            # Simplified: CSI = DM / ATR (larger = better)
            csi[i] = abs(dm) / avg_atr
    
    return csi


@njit(cache=True)
def detrended_oscillator_nb(close, period=14):
    """
    Detrended Oscillator
    
    Removes trend to identify cycles.
    
    Args:
        close: Close prices
        period: Period (14)
    
    Returns:
        Detrended values
    """
    n = len(close)
    detrend = np.zeros(n)
    
    # Calculate SMA
    sma = np.zeros(n)
    for i in range(period - 1, n):
        sma[i] = np.mean(close[i - period + 1:i + 1])
    
    # Detrend
    for i in range(period - 1, n):
        detrend[i] = close[i] - sma[i]
    
    return detrend


@njit(cache=True)
def trend_intensity_index_nb(close, period=30):
    """
    Trend Intensity Index (TII)
    
    Measures strength of trend.
    >50 = uptrend, <50 = downtrend
    
    Args:
        close: Close prices
        period: Period (30)
    
    Returns:
        TII values (0-100)
    """
    n = len(close)
    tii = np.zeros(n)
    
    for i in range(period, n):
        # SMA
        sma_val = np.mean(close[i - period:i])
        
        # Count bars above SMA
        above_count = 0
        for j in range(i - period, i):
            if close[j] > sma_val:
                above_count += 1
        
        tii[i] = (above_count / period) * 100
    
    return tii


@njit(cache=True)
def momentum_oscillator_nb(close, period=10):
    """
    Momentum Oscillator
    
    Rate of change oscillator.
    
    Args:
        close: Close prices
        period: Period (10)
    
    Returns:
        Momentum values
    """
    n = len(close)
    momentum = np.zeros(n)
    
    for i in range(period, n):
        momentum[i] = close[i] - close[i - period]
    
    return momentum


# Convenience wrappers
def stochastic_rsi(close, rsi_period=14, stoch_period=14):
    """Stochastic RSI"""
    return stochastic_rsi_nb(
        close.values if hasattr(close, 'values') else close,
        rsi_period, stoch_period
    )


def relative_vigor_index(open_prices, high, low, close, period=10):
    """Relative Vigor Index"""
    return relative_vigor_index_nb(
        open_prices.values if hasattr(open_prices, 'values') else open_prices,
        high.values if hasattr(high, 'values') else high,
        low.values if hasattr(low, 'values') else low,
        close.values if hasattr(close, 'values') else close,
        period
    )


def psychological_line(close, period=12):
    """Psychological Line"""
    return psychological_line_nb(
        close.values if hasattr(close, 'values') else close,
        period
    )


def aroon_oscillator(high, low, period=25):
    """Aroon Oscillator"""
    return aroon_oscillator_nb(
        high.values if hasattr(high, 'values') else high,
        low.values if hasattr(low, 'values') else low,
        period
    )


def commodity_selection_index(close, atr, period=14):
    """Commodity Selection Index"""
    return commodity_selection_index_nb(
        close.values if hasattr(close, 'values') else close,
        atr.values if hasattr(atr, 'values') else atr,
        period
    )


def detrended_oscillator(close, period=14):
    """Detrended Oscillator"""
    return detrended_oscillator_nb(
        close.values if hasattr(close, 'values') else close,
        period
    )


def trend_intensity_index(close, period=30):
    """Trend Intensity Index"""
    return trend_intensity_index_nb(
        close.values if hasattr(close, 'values') else close,
        period
    )


def momentum_oscillator(close, period=10):
    """Momentum Oscillator"""
    return momentum_oscillator_nb(
        close.values if hasattr(close, 'values') else close,
        period
    )


@njit(cache=True)
def rate_of_change_ratio_nb(close, period=12):
    """
    Rate of Change Ratio (ROCR)
    
    Price / Price[n periods ago]
    
    Args:
        close: Close prices
        period: Period (12)
    
    Returns:
        ROCR values (typically around 1.0)
    """
    n = len(close)
    rocr = np.ones(n)
    
    for i in range(period, n):
        if close[i - period] != 0:
            rocr[i] = close[i] / close[i - period]
    
    return rocr


@njit(cache=True)
def smoothed_rate_of_change_nb(close, period=13, smooth_period=3):
    """
    Smoothed Rate of Change (S-ROC)
    
    EMA-smoothed ROC for less noise.
    
    Args:
        close: Close prices
        period: ROC period (13)
        smooth_period: Smoothing period (3)
    
    Returns:
        Smoothed ROC values
    """
    n = len(close)
    roc = np.zeros(n)
    
    # Calculate ROC
    for i in range(period, n):
        if close[i - period] != 0:
            roc[i] = ((close[i] - close[i - period]) / close[i - period]) * 100
    
    # Apply EMA smoothing
    sroc = np.zeros(n)
    alpha = 2.0 / (smooth_period + 1)
    
    sroc[period] = roc[period]
    for i in range(period + 1, n):
        sroc[i] = alpha * roc[i] + (1 - alpha) * sroc[i-1]
    
    return sroc


@njit(cache=True)
def intraday_momentum_index_nb(open_prices, close, period=14):
    """
    Intraday Momentum Index (IMI)
    
    RSI applied to intraday gains/losses.
    
    Args:
        open_prices: Open prices
        close: Close prices
        period: Period (14)
    
    Returns:
        IMI values (0-100)
    """
    n = len(close)
    imi = np.zeros(n)
    
    gains = np.zeros(n)
    losses = np.zeros(n)
    
    for i in range(n):
        intraday_change = close[i] - open_prices[i]
        if intraday_change > 0:
            gains[i] = intraday_change
        else:
            losses[i] = abs(intraday_change)
    
    # Calculate averages
    for i in range(period, n):
        avg_gain = np.mean(gains[i - period + 1:i + 1])
        avg_loss = np.mean(losses[i - period + 1:i + 1])
        
        if avg_loss == 0:
            imi[i] = 100
        else:
            rs = avg_gain / avg_loss
            imi[i] = 100 - (100 / (1 + rs))
    
    return imi


def rate_of_change_ratio(close, period=12):
    """Rate of Change Ratio"""
    return rate_of_change_ratio_nb(
        close.values if hasattr(close, 'values') else close,
        period
    )


def smoothed_rate_of_change(close, period=13, smooth_period=3):
    """Smoothed Rate of Change"""
    return smoothed_rate_of_change_nb(
        close.values if hasattr(close, 'values') else close,
        period, smooth_period
    )


def intraday_momentum_index(open_prices, close, period=14):
    """Intraday Momentum Index"""
    return intraday_momentum_index_nb(
        open_prices.values if hasattr(open_prices, 'values') else open_prices,
        close.values if hasattr(close, 'values') else close,
        period
    )
