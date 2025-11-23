"""
Hilbert Transform Suite for ENCOM

Advanced cycle analysis using Hilbert Transform mathematics.
Used by professional quant firms for market cycle identification.

Indicators:
- Instantaneous Trendline (HT_TRENDLINE)
- Dominant Cycle Period (HT_DCPERIOD)
- Dominant Cycle Phase (HT_DCPHASE)
- Phasor Components (HT_PHASOR)
- Sine Wave (HT_SINE)
- Trend vs Cycle Mode (HT_TRENDMODE)
- Leading Sine Wave (HT_LEADSINE)

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
def hilbert_transform_nb(data):
    """
    Calculate Hilbert Transform

    Core computation for all HT indicators.

    Args:
        data: Price series

    Returns:
        Tuple of (detrender, I1, Q1, jI, jQ, I2, Q2, Re, Im)
    """
    n = len(data)

    # Initialize arrays
    smooth = np.zeros(n)
    detrender = np.zeros(n)
    I1 = np.zeros(n)
    Q1 = np.zeros(n)
    jI = np.zeros(n)
    jQ = np.zeros(n)
    I2 = np.zeros(n)
    Q2 = np.zeros(n)
    Re = np.zeros(n)
    Im = np.zeros(n)

    # Smooth price with weighted moving average
    for i in range(4, n):
        smooth[i] = (4*data[i] + 3*data[i-1] + 2*data[i-2] + data[i-3]) / 10.0

    # Detrender (centered)
    for i in range(6, n):
        detrender[i] = (0.0962*smooth[i] + 0.5769*smooth[i-2] -
                       0.5769*smooth[i-4] - 0.0962*smooth[i-6])

    # Compute InPhase and Quadrature components
    for i in range(6, n):
        # InPhase: Detrended Price delayed by 3 bars
        Q1[i] = (0.0962*detrender[i] + 0.5769*detrender[i-2] -
                0.5769*detrender[i-4] - 0.0962*detrender[i-6])
        I1[i] = detrender[i-3]

    # Advance the phase by 90 degrees
    for i in range(6, n):
        jI[i] = (0.0962*I1[i] + 0.5769*I1[i-2] -
                0.5769*I1[i-4] - 0.0962*I1[i-6])
        jQ[i] = (0.0962*Q1[i] + 0.5769*Q1[i-2] -
                0.5769*Q1[i-4] - 0.0962*Q1[i-6])

    # Phasor addition for averaging
    for i in range(6, n):
        I2[i] = I1[i] - jQ[i]
        Q2[i] = Q1[i] + jI[i]

    # Smooth I2 and Q2
    for i in range(6, n):
        I2[i] = 0.2*I2[i] + 0.8*I2[i-1]
        Q2[i] = 0.2*Q2[i] + 0.8*Q2[i-1]

    # Homodyne Discriminator
    for i in range(6, n):
        Re[i] = I2[i]*I2[i-1] + Q2[i]*Q2[i-1]
        Im[i] = I2[i]*Q2[i-1] - Q2[i]*I2[i-1]

    # Smooth Re and Im
    for i in range(6, n):
        Re[i] = 0.2*Re[i] + 0.8*Re[i-1]
        Im[i] = 0.2*Im[i] + 0.8*Im[i-1]

    return detrender, I1, Q1, jI, jQ, I2, Q2, Re, Im


@njit(cache=True)
def ht_trendline_nb(data):
    """
    Hilbert Transform - Instantaneous Trendline

    Determines the current trendline using Hilbert Transform.

    Args:
        data: Price series

    Returns:
        Trendline values
    """
    n = len(data)
    trendline = np.zeros(n)

    # Smooth with WMA
    smooth = np.zeros(n)
    for i in range(4, n):
        smooth[i] = (4*data[i] + 3*data[i-1] + 2*data[i-2] + data[i-3]) / 10.0

    # Calculate trendline
    for i in range(7, n):
        trendline[i] = (4*smooth[i] + 3*smooth[i-1] + 2*smooth[i-2] +
                       smooth[i-3] + smooth[i-4] + smooth[i-5] + smooth[i-6]) / 13.0

    return trendline


@njit(cache=True)
def ht_dcperiod_nb(data):
    """
    Hilbert Transform - Dominant Cycle Period

    Identifies the dominant market cycle period.

    Args:
        data: Price series

    Returns:
        Dominant cycle period (in bars)
    """
    n = len(data)
    period = np.zeros(n)

    detrender, I1, Q1, jI, jQ, I2, Q2, Re, Im = hilbert_transform_nb(data)

    # Calculate period
    for i in range(7, n):
        if Re[i] != 0 and Im[i] != 0:
            # Period = 2*PI / Phase
            phase = np.arctan(Im[i] / Re[i])

            # Convert phase to period
            if phase < 0.1:
                phase = 0.1

            delta_phase = phase - (np.arctan(Im[i-1] / Re[i-1]) if Re[i-1] != 0 else 0)

            if delta_phase < 1:
                delta_phase = 1

            period[i] = 2 * np.pi / delta_phase

            # Limit period to reasonable range (6-50 bars)
            if period[i] > 50:
                period[i] = 50
            if period[i] < 6:
                period[i] = 6
        else:
            period[i] = period[i-1] if i > 0 else 15

    # Smooth period
    for i in range(7, n):
        period[i] = 0.2*period[i] + 0.8*period[i-1]

    return period


@njit(cache=True)
def ht_dcphase_nb(data):
    """
    Hilbert Transform - Dominant Cycle Phase

    Phase of the dominant cycle (0 to 360 degrees).

    Args:
        data: Price series

    Returns:
        Phase in degrees (0-360)
    """
    n = len(data)
    phase = np.zeros(n)

    detrender, I1, Q1, jI, jQ, I2, Q2, Re, Im = hilbert_transform_nb(data)

    # Calculate phase
    for i in range(7, n):
        if I2[i] != 0:
            # Phase = arctan(Q2 / I2)
            phase_rad = np.arctan(Q2[i] / I2[i])
            phase_deg = phase_rad * 180.0 / np.pi

            # Adjust to 0-360 range
            if I2[i] < 0:
                phase_deg += 180
            if phase_deg < 0:
                phase_deg += 360

            phase[i] = phase_deg
        else:
            phase[i] = phase[i-1] if i > 0 else 0

    return phase


@njit(cache=True)
def ht_phasor_nb(data):
    """
    Hilbert Transform - Phasor Components

    Returns InPhase (I) and Quadrature (Q) components.

    Args:
        data: Price series

    Returns:
        Tuple of (inphase, quadrature)
    """
    detrender, I1, Q1, jI, jQ, I2, Q2, Re, Im = hilbert_transform_nb(data)

    return I2, Q2


@njit(cache=True)
def ht_sine_nb(data):
    """
    Hilbert Transform - Sine Wave

    Sine wave indicator for cycle timing.

    Args:
        data: Price series

    Returns:
        Tuple of (sine, lead_sine)
    """
    n = len(data)
    sine = np.zeros(n)
    lead_sine = np.zeros(n)

    # Get phase
    phase = ht_dcphase_nb(data)

    # Calculate sine and lead sine
    for i in range(7, n):
        # Convert phase to radians
        phase_rad = phase[i] * np.pi / 180.0

        sine[i] = np.sin(phase_rad)
        lead_sine[i] = np.sin(phase_rad + 45.0 * np.pi / 180.0)  # Lead by 45 degrees

    return sine, lead_sine


@njit(cache=True)
def ht_trendmode_nb(data):
    """
    Hilbert Transform - Trend vs Cycle Mode

    Identifies whether market is in trend or cycle mode.

    Args:
        data: Price series

    Returns:
        Trend mode (1 = trend, 0 = cycle)
    """
    n = len(data)
    trend_mode = np.zeros(n)

    detrender, I1, Q1, jI, jQ, I2, Q2, Re, Im = hilbert_transform_nb(data)

    # Get dominant cycle period
    period = ht_dcperiod_nb(data)

    # Calculate trend mode
    for i in range(25, n):  # Need 25 bars for calculation
        # Compute smoothed price over dominant cycle period
        dcperiod = int(period[i])
        if dcperiod < 6:
            dcperiod = 6
        if dcperiod > 50:
            dcperiod = 50

        # Check if price movement exceeds cycle variation
        price_range = np.max(data[i-dcperiod:i+1]) - np.min(data[i-dcperiod:i+1])

        # Trend if range is large relative to cycle
        if i >= dcperiod:
            avg_range = np.mean(np.abs(data[i-dcperiod:i] - data[i-dcperiod-1:i-1]))

            if price_range > 1.5 * avg_range * dcperiod:
                trend_mode[i] = 1
            else:
                trend_mode[i] = 0
        else:
            trend_mode[i] = 0

    return trend_mode


# ===================================
# Convenience Wrappers
# ===================================

def ht_trendline(data):
    """Hilbert Transform - Instantaneous Trendline"""
    return ht_trendline_nb(data.values if hasattr(data, 'values') else data)


def ht_dcperiod(data):
    """Hilbert Transform - Dominant Cycle Period"""
    return ht_dcperiod_nb(data.values if hasattr(data, 'values') else data)


def ht_dcphase(data):
    """Hilbert Transform - Dominant Cycle Phase"""
    return ht_dcphase_nb(data.values if hasattr(data, 'values') else data)


def ht_phasor(data):
    """Hilbert Transform - Phasor Components"""
    return ht_phasor_nb(data.values if hasattr(data, 'values') else data)


def ht_sine(data):
    """Hilbert Transform - Sine Wave"""
    return ht_sine_nb(data.values if hasattr(data, 'values') else data)


def ht_trendmode(data):
    """Hilbert Transform - Trend vs Cycle Mode"""
    return ht_trendmode_nb(data.values if hasattr(data, 'values') else data)


def ht_leadsine(data):
    """Hilbert Transform - Leading Sine Wave (convenience)"""
    sine, lead_sine = ht_sine(data)
    return lead_sine
