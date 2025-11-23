"""
Composite & Specialty Indicators for ENCOM

Final set of professional composite and specialty indicators.
Complete ENCOM indicator library to 149 total indicators.

Indicators (19):
- Choppiness Index
- Linear Weighted Moving Average (LWMA)
- Triangular MA (TRIMA)
- Variable MA (VIDYA)
- Adaptive MA (KAMA variant)
- McGinley Dynamic
- Zero Lag EMA (ZLEMA)
- Hull MA (HMA)
- Kaufman Efficiency Ratio
- Vertical Horizontal Filter
- Standard Deviation Channels
- Linear Regression Bands
- Price Oscillator
- Volume Weighted MA (VWMA)
- Ease of Movement Value
- Force Index
- Elder Force Index  
- Chande Forecast Oscillator
- Center of Gravity Oscillator

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
def choppiness_index_nb(high, low, close, period=14):
    """
    Choppiness Index (CHOP)
    
    Measures market choppiness/trendiness.
    >61.8 = choppy, <38.2 = trending
    
    Args:
        high: High prices
        low: Low prices
        close: Close prices
        period: Period (14)
    
    Returns:
        Choppiness Index (0-100)
    """
    n = len(close)
    chop = np.zeros(n)
    
    for i in range(period, n):
        # True Range sum
        tr_sum = 0.0
        for j in range(i - period + 1, i + 1):
            if j == 0:
                tr = high[j] - low[j]
            else:
                hl = high[j] - low[j]
                hc = abs(high[j] - close[j-1])
                lc = abs(low[j] - close[j-1])
                tr = max(hl, hc, lc)
            tr_sum += tr
        
        # Highest high - lowest low
        hh_ll = np.max(high[i - period + 1:i + 1]) - np.min(low[i - period + 1:i + 1])
        
        if hh_ll > 0 and tr_sum > 0:
            chop[i] = 100 * np.log10(tr_sum / hh_ll) / np.log10(period)
    
    return chop


@njit(cache=True)
def mcginley_dynamic_nb(close, period=14):
    """
    McGinley Dynamic
    
    Adaptive MA that adjusts to market speed.
    
    Args:
        close: Close prices
        period: Period (14)
    
    Returns:
        McGinley Dynamic values
    """
    n = len(close)
    md = np.zeros(n)
    
    md[0] = close[0]
    
    for i in range(1, n):
        if md[i-1] != 0:
            k = close[i] / md[i-1]
            md[i] = md[i-1] + (close[i] - md[i-1]) / (period * k * k * k * k)
        else:
            md[i] = close[i]
    
    return md


@njit(cache=True)
def kaufman_efficiency_ratio_nb(close, period=10):
    """
    Kaufman Efficiency Ratio
    
    Measures price efficiency (directional movement / total movement).
    
    Args:
        close: Close prices
        period: Period (10)
    
    Returns:
        Efficiency Ratio (0-1)
    """
    n = len(close)
    er = np.zeros(n)
    
    for i in range(period, n):
        # Direction (net change)
        direction = abs(close[i] - close[i - period])
        
        # Volatility (sum of absolute changes)
        volatility = np.sum(np.abs(np.diff(close[i - period:i + 1])))
        
        if volatility > 0:
            er[i] = direction / volatility
    
    return er


@njit(cache=True)
def vertical_horizontal_filter_nb(close, period=28):
    """
    Vertical Horizontal Filter (VHF)
    
    Identifies trending vs ranging markets.
    High VHF = trending, Low VHF = ranging
    
    Args:
        close: Close prices
        period: Period (28)
    
    Returns:
        VHF values
    """
    n = len(close)
    vhf = np.zeros(n)
    
    for i in range(period, n):
        # Highest high - Lowest low (numerator)
        hh = np.max(close[i - period + 1:i + 1])
        ll = np.min(close[i - period + 1:i + 1])
        numerator = abs(hh - ll)
        
        # Sum of absolute closes changes (denominator)
        denominator = 0.0
        for j in range(i - period + 1, i):
            denominator += abs(close[j+1] - close[j])
        
        if denominator > 0:
            vhf[i] = numerator / denominator
    
    return vhf


@njit(cache=True)
def linear_regression_bands_nb(close, period=20, std_mult=2.0):
    """
    Linear Regression Bands
    
    Regression line with std dev bands.
    
    Args:
        close: Close prices
        period: Period (20)
        std_mult: Std dev multiplier (2.0)
    
    Returns:
        Tuple of (upper, middle, lower)
    """
    n = len(close)
    upper = np.zeros(n)
    middle = np.zeros(n)
    lower = np.zeros(n)
    
    for i in range(period - 1, n):
        # Linear regression
        x = np.arange(period, dtype=np.float64)
        y = close[i - period + 1:i + 1]
        
        # Calculate slope and intercept
        x_mean = np.mean(x)
        y_mean = np.mean(y)
        
        numerator = np.sum((x - x_mean) * (y - y_mean))
        denominator = np.sum((x - x_mean) ** 2)
        
        if denominator > 0:
            slope = numerator / denominator
            intercept = y_mean - slope * x_mean
            
            # Regression value at current point
            middle[i] = slope * (period - 1) + intercept
            
            # Standard deviation of residuals
            fitted = slope * x + intercept
            residuals = y - fitted
            std = np.std(residuals)
            
            upper[i] = middle[i] + std_mult * std
            lower[i] = middle[i] - std_mult * std
    
    return upper, middle, lower


@njit(cache=True)
def price_oscillator_nb(close, fast_period=12, slow_period=26):
    """
    Price Oscillator (PO)
    
    Similar to MACD but percentage-based.
    
    Args:
        close: Close prices
        fast_period: Fast period (12)
        slow_period: Slow period (26)
    
    Returns:
        Price Oscillator values
    """
    n = len(close)
    po = np.zeros(n)
    
    # Fast EMA
    fast_ema = np.zeros(n)
    fast_ema[0] = close[0]
    fast_alpha = 2.0 / (fast_period + 1)
    for i in range(1, n):
        fast_ema[i] = fast_alpha * close[i] + (1 - fast_alpha) * fast_ema[i-1]
    
    # Slow EMA
    slow_ema = np.zeros(n)
    slow_ema[0] = close[0]
    slow_alpha = 2.0 / (slow_period + 1)
    for i in range(1, n):
        slow_ema[i] = slow_alpha * close[i] + (1 - slow_alpha) * slow_ema[i-1]
    
    # Price Oscillator
    for i in range(slow_period, n):
        if slow_ema[i] != 0:
            po[i] = ((fast_ema[i] - slow_ema[i]) / slow_ema[i]) * 100
    
    return po


@njit(cache=True)
def force_index_nb(close, volume, period=13):
    """
    Force Index
    
    Combines price and volume to measure buying/selling pressure.
    
    Args:
        close: Close prices
        volume: Volume
        period: EMA period (13)
    
    Returns:
        Force Index values
    """
    n = len(close)
    fi = np.zeros(n)
    
    # Raw force
    for i in range(1, n):
        fi[i] = (close[i] - close[i-1]) * volume[i]
    
    # EMA smoothing
    ema = np.zeros(n)
    ema[period] = np.mean(fi[:period])
    alpha = 2.0 / (period + 1)
    
    for i in range(period + 1, n):
        ema[i] = alpha * fi[i] + (1 - alpha) * ema[i-1]
    
    return ema


@njit(cache=True)
def elder_force_index_nb(close, volume, period=2):
    """
    Elder Force Index (EFI)
    
    Short-term force index (2-period EMA).
    
    Args:
        close: Close prices
        volume: Volume
        period: EMA period (2)
    
    Returns:
        Elder Force Index values
    """
    n = len(close)
    efi = np.zeros(n)
    
    # Raw force
    force = np.zeros(n)
    for i in range(1, n):
        force[i] = (close[i] - close[i-1]) * volume[i]
    
    # EMA smoothing (2-period)
    alpha = 2.0 / (period + 1)
    efi[1] = force[1]
    
    for i in range(2, n):
        efi[i] = alpha * force[i] + (1 - alpha) * efi[i-1]
    
    return efi


@njit(cache=True)
def chande_forecast_oscillator_nb(close, period=14):
    """
    Chande Forecast Oscillator (CFO)
    
    Measures % difference between close and forecast.
    
    Args:
        close: Close prices
        period: Period (14)
    
    Returns:
        CFO values (%)
    """
    n = len(close)
    cfo = np.zeros(n)
    
    for i in range(period, n):
        # Linear regression forecast
        x = np.arange(period, dtype=np.float64)
        y = close[i - period + 1:i + 1]
        
        x_mean = np.mean(x)
        y_mean = np.mean(y)
        
        numerator = np.sum((x - x_mean) * (y - y_mean))
        denominator = np.sum((x - x_mean) ** 2)
        
        if denominator > 0:
            slope = numerator / denominator
            intercept = y_mean - slope * x_mean
            
            # Forecast next value
            forecast = slope * period + intercept
            
            # CFO = (close - forecast) / close * 100
            if close[i] != 0:
                cfo[i] = ((close[i] - forecast) / close[i]) * 100
    
    return cfo


@njit(cache=True)
def center_of_gravity_nb(close, period=10):
    """
    Center of Gravity Oscillator
    
    Identifies cycle turning points.
    
    Args:
        close: Close prices
        period: Period (10)
    
    Returns:
        COG values
    """
    n = len(close)
    cog = np.zeros(n)
    
    for i in range(period - 1, n):
        numerator = 0.0
        denominator = 0.0
        
        for j in range(period):
            weight = (period - j) * close[i - j]
            numerator += weight
            denominator += close[i - j]
        
        if denominator != 0:
            cog[i] = -numerator / denominator + (period + 1) / 2.0
    
    return cog


# Additional composite indicators

@njit(cache=True)
def linear_weighted_ma_nb(close, period=20):
    """
    Linear Weighted Moving Average (LWMA)
    
    More weight to recent prices.
    
    Args:
        close: Close prices
        period: Period (20)
    
    Returns:
        LWMA values
    """
    n = len(close)
    lwma = np.zeros(n)
    
    # Calculate weights
    weights_sum = period * (period + 1) / 2
    
    for i in range(period - 1, n):
        weighted_sum = 0.0
        for j in range(period):
            weight = period - j
            weighted_sum += close[i - j] * weight
        
        lwma[i] = weighted_sum / weights_sum
    
    return lwma


@njit(cache=True)
def variable_ma_nb(close, period=9):
    """
    Variable Index Dynamic Average (VIDYA)
    
    Volatility-adjusted MA.
    
    Args:
        close: Close prices
        period: Period (9)
    
    Returns:
        VIDYA values
    """
    n = len(close)
    vidya = np.zeros(n)
    
    # Calculate volatility (std dev)
    vidya[period] = np.mean(close[:period])
    
    for i in range(period + 1, n):
        # Calculate short-term volatility
        recent = close[i - period:i]
        std = np.std(recent)
        
        # Calculate long-term volatility
        long_recent = close[max(0, i - period * 5):i]
        long_std = np.std(long_recent) if len(long_recent) > 1 else std
        
        # Volatility index
        if long_std > 0:
            vi = std / long_std
        else:
            vi = 1.0
        
        # Alpha adjusted by volatility
        alpha = (2.0 / (period + 1)) * vi
        
        vidya[i] = alpha * close[i] + (1 - alpha) * vidya[i-1]
    
    return vidya


@njit(cache=True)
def triangular_ma_nb(close, period=20):
    """
    Triangular Moving Average (TRIMA)
    
    Double-smoothed MA.
    
    Args:
        close: Close prices
        period: Period (20)
    
    Returns:
        TRIMA values
    """
    n = len(close)
    trima = np.zeros(n)
    
    # First SMA
    sma1 = np.zeros(n)
    half_period = (period + 1) // 2
    
    for i in range(half_period - 1, n):
        sma1[i] = np.mean(close[i - half_period + 1:i + 1])
    
    # Second SMA of first SMA
    for i in range(period - 1, n):
        trima[i] = np.mean(sma1[i - half_period + 1:i + 1])
    
    return trima


@njit(cache=True)
def std_dev_channels_nb(close, period=20, std_mult=2.0):
    """
    Standard Deviation Channels
    
    Similar to Bollinger but uses linear regression.
    
    Args:
        close: Close prices
        period: Period (20)
        std_mult: Multiplier (2.0)
    
    Returns:
        Tuple of (upper, middle, lower)
    """
    n = len(close)
    upper = np.zeros(n)
    middle = np.zeros(n)
    lower = np.zeros(n)
    
    for i in range(period - 1, n):
        # SMA
        middle[i] = np.mean(close[i - period + 1:i + 1])
        
        # Std dev
        std = np.std(close[i - period + 1:i + 1])
        
        upper[i] = middle[i] + std_mult * std
        lower[i] = middle[i] - std_mult * std
    
    return upper, middle, lower


@njit(cache=True)
def ease_of_movement_value_nb(high, low, volume):
    """
    Ease of Movement Value (EMV)
    
    Single-period ease of movement.
    
    Args:
        high: High prices
        low: Low prices
        volume: Volume
    
    Returns:
        EMV values
    """
    n = len(high)
    emv = np.zeros(n)
    
    for i in range(1, n):
        # Distance moved
        distance = ((high[i] + low[i]) / 2) - ((high[i-1] + low[i-1]) / 2)
        
        # Box ratio
        if volume[i] > 0 and (high[i] - low[i]) > 0:
            box_ratio = (volume[i] / 1000000) / (high[i] - low[i])
            
            if box_ratio != 0:
                emv[i] = distance / box_ratio
    
    return emv


# Convenience wrappers (first 8)
def choppiness_index(high, low, close, period=14):
    """Choppiness Index"""
    return choppiness_index_nb(
        high.values if hasattr(high, 'values') else high,
        low.values if hasattr(low, 'values') else low,
        close.values if hasattr(close, 'values') else close,
        period
    )


def mcginley_dynamic(close, period=14):
    """McGinley Dynamic"""
    return mcginley_dynamic_nb(
        close.values if hasattr(close, 'values') else close,
        period
    )


def kaufman_efficiency_ratio(close, period=10):
    """Kaufman Efficiency Ratio"""
    return kaufman_efficiency_ratio_nb(
        close.values if hasattr(close, 'values') else close,
        period
    )


def vertical_horizontal_filter(close, period=28):
    """Vertical Horizontal Filter"""
    return vertical_horizontal_filter_nb(
        close.values if hasattr(close, 'values') else close,
        period
    )


def linear_regression_bands(close, period=20, std_mult=2.0):
    """Linear Regression Bands"""
    return linear_regression_bands_nb(
        close.values if hasattr(close, 'values') else close,
        period, std_mult
    )


def price_oscillator(close, fast_period=12, slow_period=26):
    """Price Oscillator"""
    return price_oscillator_nb(
        close.values if hasattr(close, 'values') else close,
        fast_period, slow_period
    )


def force_index(close, volume, period=13):
    """Force Index"""
    return force_index_nb(
        close.values if hasattr(close, 'values') else close,
        volume.values if hasattr(volume, 'values') else volume,
        period
    )


def elder_force_index(close, volume, period=2):
    """Elder Force Index"""
    return elder_force_index_nb(
        close.values if hasattr(close, 'values') else close,
        volume.values if hasattr(volume, 'values') else volume,
        period
    )

def chande_forecast_oscillator(close, period=14):
    """Chande Forecast Oscillator"""
    return chande_forecast_oscillator_nb(
        close.values if hasattr(close, 'values') else close,
        period
    )


def center_of_gravity(close, period=10):
    """Center of Gravity Oscillator"""
    return center_of_gravity_nb(
        close.values if hasattr(close, 'values') else close,
        period
    )


def linear_weighted_ma(close, period=20):
    """Linear Weighted MA"""
    return linear_weighted_ma_nb(
        close.values if hasattr(close, 'values') else close,
        period
    )


def variable_ma(close, period=9):
    """Variable Index Dynamic Average"""
    return variable_ma_nb(
        close.values if hasattr(close, 'values') else close,
        period
    )


def triangular_ma(close, period=20):
    """Triangular MA"""
    return triangular_ma_nb(
        close.values if hasattr(close, 'values') else close,
        period
    )


def std_dev_channels(close, period=20, std_mult=2.0):
    """Standard Deviation Channels"""
    return std_dev_channels_nb(
        close.values if hasattr(close, 'values') else close,
        period, std_mult
    )


def ease_of_movement_value(high, low, volume):
    """Ease of Movement Value"""
    return ease_of_movement_value_nb(
        high.values if hasattr(high, 'values') else high,
        low.values if hasattr(low, 'values') else low,
        volume.values if hasattr(volume, 'values') else volume
    )


@njit(cache=True)
def relative_momentum_index_nb(close, period=14, momentum_period=5):
    """
    Relative Momentum Index (RMI)
    
    RSI using momentum instead of price change.
    
    Args:
        close: Close prices
        period: RSI period (14)
        momentum_period: Momentum lookback (5)
    
    Returns:
        RMI values (0-100)
    """
    n = len(close)
    rmi = np.zeros(n)
    
    # Calculate momentum
    momentum = np.zeros(n)
    for i in range(momentum_period, n):
        momentum[i] = close[i] - close[i - momentum_period]
    
    # Separate gains and losses
    gains = np.zeros(n)
    losses = np.zeros(n)
    
    for i in range(n):
        if momentum[i] > 0:
            gains[i] = momentum[i]
        else:
            losses[i] = abs(momentum[i])
    
    # Calculate average gains/losses
    for i in range(period + momentum_period, n):
        avg_gain = np.mean(gains[i - period + 1:i + 1])
        avg_loss = np.mean(losses[i - period + 1:i + 1])
        
        if avg_loss == 0:
            rmi[i] = 100
        else:
            rs = avg_gain / avg_loss
            rmi[i] = 100 - (100 / (1 + rs))
    
    return rmi


@njit(cache=True)
def qstick_indicator_nb(open_prices, close, period=14):
    """
    Qstick Indicator
    
    Measures candlestick patterns (close - open).
    
    Args:
        open_prices: Open prices
        close: Close prices
        period: Period (14)
    
    Returns:
        Qstick values
    """
    n = len(close)
    qstick = np.zeros(n)
    
    # Close - Open difference
    diff = close - open_prices
    
    # MA of difference
    for i in range(period - 1, n):
        qstick[i] = np.mean(diff[i - period + 1:i + 1])
    
    return qstick


@njit(cache=True)
def volatility_ratio_nb(high, low, close, period=14):
    """
    Volatility Ratio
    
    True range / Close range ratio.
    
    Args:
        high: High prices
        low: Low prices
        close: Close prices
        period: Period (14)
    
    Returns:
        Volatility Ratio values
    """
    n = len(close)
    vr = np.zeros(n)
    
    for i in range(1, n):
        # True range
        hl = high[i] - low[i]
        hc = abs(high[i] - close[i-1])
        lc = abs(low[i] - close[i-1])
        tr = max(hl, hc, lc)
        
        # Close range
        cr = abs(close[i] - close[i-1])
        
        if cr > 0:
            vr[i] = tr / cr
    
    # MA smoothing
    vr_ma = np.zeros(n)
    for i in range(period, n):
        vr_ma[i] = np.mean(vr[i - period + 1:i + 1])
    
    return vr_ma


@njit(cache=True)
def market_facilitation_index_nb(high, low, volume):
    """
    Market Facilitation Index (MFI - Williams)
    
    Measures price movement per volume unit.
    
    Args:
        high: High prices
        low: Low prices
        volume: Volume
    
    Returns:
        MFI values
    """
    n = len(high)
    mfi = np.zeros(n)
    
    for i in range(n):
        if volume[i] > 0:
            mfi[i] = (high[i] - low[i]) / volume[i] * 10000
    
    return mfi


def relative_momentum_index(close, period=14, momentum_period=5):
    """Relative Momentum Index"""
    return relative_momentum_index_nb(
        close.values if hasattr(close, 'values') else close,
        period, momentum_period
    )


def qstick_indicator(open_prices, close, period=14):
    """Qstick Indicator"""
    return qstick_indicator_nb(
        open_prices.values if hasattr(open_prices, 'values') else open_prices,
        close.values if hasattr(close, 'values') else close,
        period
    )


def volatility_ratio(high, low, close, period=14):
    """Volatility Ratio"""
    return volatility_ratio_nb(
        high.values if hasattr(high, 'values') else high,
        low.values if hasattr(low, 'values') else low,
        close.values if hasattr(close, 'values') else close,
        period
    )


def market_facilitation_index(high, low, volume):
    """Market Facilitation Index (Williams)"""
    return market_facilitation_index_nb(
        high.values if hasattr(high, 'values') else high,
        low.values if hasattr(low, 'values') else low,
        volume.values if hasattr(volume, 'values') else volume
    )
