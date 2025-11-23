"""
Advanced Momentum Indicators for ENCOM

Elite quant-level momentum indicators with Numba optimization.

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
def trix_nb(close, period=15):
    """
    TRIX - Triple Exponential Average

    Momentum oscillator showing rate of change of triple EMA.

    Args:
        close: Close prices
        period: TRIX period (15)

    Returns:
        TRIX values (%)
    """
    n = len(close)
    trix = np.zeros(n)

    # Calculate first EMA
    ema1 = np.zeros(n)
    ema1[0] = close[0]
    alpha = 2.0 / (period + 1)

    for i in range(1, n):
        ema1[i] = alpha * close[i] + (1 - alpha) * ema1[i-1]

    # Calculate second EMA
    ema2 = np.zeros(n)
    ema2[0] = ema1[0]

    for i in range(1, n):
        ema2[i] = alpha * ema1[i] + (1 - alpha) * ema2[i-1]

    # Calculate third EMA
    ema3 = np.zeros(n)
    ema3[0] = ema2[0]

    for i in range(1, n):
        ema3[i] = alpha * ema2[i] + (1 - alpha) * ema3[i-1]

    # Calculate ROC of triple EMA
    for i in range(1, n):
        if ema3[i-1] != 0:
            trix[i] = ((ema3[i] - ema3[i-1]) / ema3[i-1]) * 100.0

    return trix


@njit(cache=True)
def bop_nb(open_price, high, low, close):
    """
    Balance of Power (BOP)

    Measures buying vs selling pressure.

    Args:
        open_price: Open prices
        high: High prices
        low: Low prices
        close: Close prices

    Returns:
        BOP values (-1 to +1)
    """
    n = len(close)
    bop = np.zeros(n)

    for i in range(n):
        hl_diff = high[i] - low[i]

        if hl_diff != 0:
            bop[i] = (close[i] - open_price[i]) / hl_diff
        else:
            bop[i] = 0.0

    return bop


@njit(cache=True)
def apo_nb(close, fast_period=12, slow_period=26):
    """
    Absolute Price Oscillator (APO)

    Difference between fast and slow EMA (unlike PPO which is percentage).

    Args:
        close: Close prices
        fast_period: Fast EMA period (12)
        slow_period: Slow EMA period (26)

    Returns:
        APO values
    """
    n = len(close)

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

    # APO = Fast EMA - Slow EMA
    apo = fast_ema - slow_ema

    return apo


@njit(cache=True)
def kst_nb(close, roc1=10, roc2=15, roc3=20, roc4=30,
           sma1=10, sma2=10, sma3=10, sma4=15):
    """
    Know Sure Thing (KST)

    Multi-period momentum oscillator using smoothed ROC.

    Args:
        close: Close prices
        roc1, roc2, roc3, roc4: ROC periods (10,15,20,30)
        sma1, sma2, sma3, sma4: SMA smoothing periods (10,10,10,15)

    Returns:
        KST values
    """
    n = len(close)
    kst = np.zeros(n)

    # Calculate 4 ROC series
    roc_1 = np.zeros(n)
    roc_2 = np.zeros(n)
    roc_3 = np.zeros(n)
    roc_4 = np.zeros(n)

    for i in range(roc1, n):
        roc_1[i] = ((close[i] - close[i - roc1]) / close[i - roc1]) * 100.0

    for i in range(roc2, n):
        roc_2[i] = ((close[i] - close[i - roc2]) / close[i - roc2]) * 100.0

    for i in range(roc3, n):
        roc_3[i] = ((close[i] - close[i - roc3]) / close[i - roc3]) * 100.0

    for i in range(roc4, n):
        roc_4[i] = ((close[i] - close[i - roc4]) / close[i - roc4]) * 100.0

    # Smooth each ROC with SMA
    sma_roc1 = np.zeros(n)
    sma_roc2 = np.zeros(n)
    sma_roc3 = np.zeros(n)
    sma_roc4 = np.zeros(n)

    for i in range(sma1 - 1, n):
        sma_roc1[i] = np.mean(roc_1[i - sma1 + 1:i + 1])

    for i in range(sma2 - 1, n):
        sma_roc2[i] = np.mean(roc_2[i - sma2 + 1:i + 1])

    for i in range(sma3 - 1, n):
        sma_roc3[i] = np.mean(roc_3[i - sma3 + 1:i + 1])

    for i in range(sma4 - 1, n):
        sma_roc4[i] = np.mean(roc_4[i - sma4 + 1:i + 1])

    # KST = weighted sum of smoothed ROCs
    kst = (1 * sma_roc1) + (2 * sma_roc2) + (3 * sma_roc3) + (4 * sma_roc4)

    return kst


@njit(cache=True)
def dpo_nb(close, period=20):
    """
    Detrended Price Oscillator (DPO)

    Removes trend to identify cycles.

    Args:
        close: Close prices
        period: DPO period (20)

    Returns:
        DPO values
    """
    n = len(close)
    dpo = np.zeros(n)

    displacement = int(period / 2) + 1

    # Calculate SMA
    for i in range(period - 1, n):
        sma = np.mean(close[i - period + 1:i + 1])

        # DPO[i] = Close[i - displacement] - SMA[i]
        if i >= displacement:
            dpo[i - displacement] = close[i - displacement] - sma

    return dpo


@njit(cache=True)
def fisher_transform_nb(high, low, period=9):
    """
    Fisher Transform

    Converts prices to Gaussian normal distribution.

    Args:
        high: High prices
        low: Low prices
        period: Period (9)

    Returns:
        Tuple of (fisher, trigger)
    """
    n = len(high)
    fisher = np.zeros(n)
    trigger = np.zeros(n)
    value = np.zeros(n)

    for i in range(period - 1, n):
        # Normalize price to -1 to +1
        max_high = np.max(high[i - period + 1:i + 1])
        min_low = np.min(low[i - period + 1:i + 1])

        if max_high - min_low != 0:
            value[i] = 0.33 * 2 * ((high[i] + low[i]) / 2 - min_low) / (max_high - min_low - 1) + 0.67 * value[i-1]
        else:
            value[i] = value[i-1]

        # Limit to -0.999 to 0.999
        value[i] = max(min(value[i], 0.999), -0.999)

        # Fisher Transform
        fisher[i] = 0.5 * np.log((1 + value[i]) / (1 - value[i])) + 0.5 * fisher[i-1]

        # Trigger is previous Fisher value
        if i > 0:
            trigger[i] = fisher[i-1]

    return fisher, trigger


@njit(cache=True)
def ao_nb(high, low, fast_period=5, slow_period=34):
    """
    Awesome Oscillator (AO)

    Bill Williams' momentum indicator.

    Args:
        high: High prices
        low: Low prices
        fast_period: Fast SMA period (5)
        slow_period: Slow SMA period (34)

    Returns:
        AO values
    """
    n = len(high)
    ao = np.zeros(n)

    # Median price
    median = (high + low) / 2.0

    # Fast SMA of median
    fast_sma = np.zeros(n)
    for i in range(fast_period - 1, n):
        fast_sma[i] = np.mean(median[i - fast_period + 1:i + 1])

    # Slow SMA of median
    slow_sma = np.zeros(n)
    for i in range(slow_period - 1, n):
        slow_sma[i] = np.mean(median[i - slow_period + 1:i + 1])

    # AO = Fast SMA - Slow SMA
    ao = fast_sma - slow_sma

    return ao


@njit(cache=True)
def ac_nb(high, low, fast_period=5, slow_period=34, signal_period=5):
    """
    Acceleration/Deceleration Oscillator (AC)

    Measures acceleration of Awesome Oscillator.

    Args:
        high: High prices
        low: Low prices
        fast_period: Fast period (5)
        slow_period: Slow period (34)
        signal_period: Signal SMA period (5)

    Returns:
        AC values
    """
    # Calculate AO first
    ao = ao_nb(high, low, fast_period, slow_period)

    n = len(ao)
    ac = np.zeros(n)

    # Signal line (SMA of AO)
    signal = np.zeros(n)
    for i in range(signal_period - 1, n):
        signal[i] = np.mean(ao[i - signal_period + 1:i + 1])

    # AC = AO - Signal
    ac = ao - signal

    return ac


# Convenience wrappers
def trix(close, period=15):
    """TRIX - Triple Exponential Average"""
    return trix_nb(close.values if hasattr(close, 'values') else close, period)


def bop(open_price, high, low, close):
    """Balance of Power"""
    return bop_nb(open_price.values if hasattr(open_price, 'values') else open_price,
                  high.values if hasattr(high, 'values') else high,
                  low.values if hasattr(low, 'values') else low,
                  close.values if hasattr(close, 'values') else close)


def apo(close, fast_period=12, slow_period=26):
    """Absolute Price Oscillator"""
    return apo_nb(close.values if hasattr(close, 'values') else close,
                  fast_period, slow_period)


def kst(close, roc1=10, roc2=15, roc3=20, roc4=30,
        sma1=10, sma2=10, sma3=10, sma4=15):
    """Know Sure Thing"""
    return kst_nb(close.values if hasattr(close, 'values') else close,
                  roc1, roc2, roc3, roc4, sma1, sma2, sma3, sma4)


def dpo(close, period=20):
    """Detrended Price Oscillator"""
    return dpo_nb(close.values if hasattr(close, 'values') else close, period)


def fisher_transform(high, low, period=9):
    """Fisher Transform"""
    return fisher_transform_nb(high.values if hasattr(high, 'values') else high,
                               low.values if hasattr(low, 'values') else low,
                               period)


def ao(high, low, fast_period=5, slow_period=34):
    """Awesome Oscillator"""
    return ao_nb(high.values if hasattr(high, 'values') else high,
                 low.values if hasattr(low, 'values') else low,
                 fast_period, slow_period)


def ac(high, low, fast_period=5, slow_period=34, signal_period=5):
    """Acceleration/Deceleration Oscillator"""
    return ac_nb(high.values if hasattr(high, 'values') else high,
                 low.values if hasattr(low, 'values') else low,
                 fast_period, slow_period, signal_period)
