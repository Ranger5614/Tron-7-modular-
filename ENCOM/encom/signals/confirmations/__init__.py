"""
Confirmation Signals - Layer 1 and Layer 2

Complete library of 15+ confirmation signals organized by category:
- Trend Confirmations (5): ADX, Supertrend, MA Alignment, PSAR, Aroon
- Volume Confirmations (4): Volume Increasing, OBV Trend, CMF, Volume Ratio
- Volatility Confirmations (4): ATR Expanding/Contracting, BB Width, KC Position
- Momentum Confirmations (5): RSI Direction, MACD Histogram, Stochastic, ROC, CCI

Author: ENCOM Development Team
License: MIT
"""

# Trend Confirmations
from encom.signals.confirmations.trend_confirmations import (
    ADXStrengthConfirmation,
    SupertrendAlignmentConfirmation,
    MovingAverageAlignmentConfirmation,
    ParabolicSARConfirmation,
    AroonConfirmation,
)

# Volume Confirmations
from encom.signals.confirmations.volume_confirmations import (
    VolumeIncreasingConfirmation,
    OBVTrendConfirmation,
    CMFConfirmation,
    VolumeRatioConfirmation,
)

# Volatility Confirmations
from encom.signals.confirmations.volatility_confirmations import (
    ATRExpandingConfirmation,
    ATRContractingConfirmation,
    BollingerBandWidthConfirmation,
    KeltnerChannelPositionConfirmation,
)

# Momentum Confirmations
from encom.signals.confirmations.momentum_confirmations import (
    RSIDirectionConfirmation,
    MACDHistogramSlopeConfirmation,
    StochasticAlignmentConfirmation,
    ROCPositiveConfirmation,
    CCIConfirmation,
)

__all__ = [
    # Trend (5)
    'ADXStrengthConfirmation',
    'SupertrendAlignmentConfirmation',
    'MovingAverageAlignmentConfirmation',
    'ParabolicSARConfirmation',
    'AroonConfirmation',
    # Volume (4)
    'VolumeIncreasingConfirmation',
    'OBVTrendConfirmation',
    'CMFConfirmation',
    'VolumeRatioConfirmation',
    # Volatility (4)
    'ATRExpandingConfirmation',
    'ATRContractingConfirmation',
    'BollingerBandWidthConfirmation',
    'KeltnerChannelPositionConfirmation',
    # Momentum (5)
    'RSIDirectionConfirmation',
    'MACDHistogramSlopeConfirmation',
    'StochasticAlignmentConfirmation',
    'ROCPositiveConfirmation',
    'CCIConfirmation',
]
