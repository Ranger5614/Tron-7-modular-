"""
Strategy templates
"""

from encom.strategies.base_strategy import BaseStrategy
from encom.strategies.rsi_strategy import RSIMeanReversionStrategy
from encom.strategies.breakout_strategy import BreakoutStrategy
from encom.strategies.macd_strategy import MACDTrendStrategy

__all__ = [
    "BaseStrategy",
    "RSIMeanReversionStrategy",
    "BreakoutStrategy",
    "MACDTrendStrategy",
]
