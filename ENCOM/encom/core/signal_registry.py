"""
Signal Registry - Base classes and signal library management
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
import pandas as pd
import numpy as np


class BaseSignal(ABC):
    """
    Base class for all signals (core, confirmation, filters)

    All signals must inherit from this class and implement:
    - evaluate(): Signal detection logic (bar-by-bar)
    - get_strength(): Signal strength scoring (0-100)
    - evaluate_vectorized(): Optional vectorized evaluation for performance
    """

    def __init__(self, name: str, params: Optional[Dict[str, Any]] = None):
        self.name = name
        self.params = params or {}
        self.signal_type = "base"  # core, confirmation, filter
        self._cached_signals = None  # Cache for vectorized results

    @abstractmethod
    def evaluate(self, df: pd.DataFrame, current_idx: int) -> bool:
        """
        Evaluate if signal is triggered (bar-by-bar mode)

        Args:
            df: OHLCV dataframe
            current_idx: Current bar index

        Returns:
            True if signal triggered, False otherwise
        """
        pass

    @abstractmethod
    def get_strength(self, df: pd.DataFrame, current_idx: int) -> float:
        """
        Calculate signal strength (0-100)

        Args:
            df: OHLCV dataframe
            current_idx: Current bar index

        Returns:
            Signal strength score (0-100)
        """
        pass

    def evaluate_vectorized(self, df: pd.DataFrame) -> np.ndarray:
        """
        Vectorized signal evaluation for entire dataset (PERFORMANCE)

        Override this method for 10-100x speedup. Default implementation
        falls back to bar-by-bar evaluation.

        Args:
            df: OHLCV dataframe

        Returns:
            Boolean numpy array where True indicates signal triggered
        """
        # Fallback: bar-by-bar evaluation
        signals = np.zeros(len(df), dtype=bool)
        for i in range(len(df)):
            signals[i] = self.evaluate(df, i)
        return signals

    def get_config(self) -> Dict[str, Any]:
        """Get signal configuration"""
        return {
            "name": self.name,
            "type": self.signal_type,
            "params": self.params
        }


class SignalRegistry:
    """
    Central registry for all available signals
    """

    def __init__(self):
        self._signals = {
            "core": {},
            "confirmation": {},
            "filter": {}
        }

    def register(self, signal_class, signal_type: str):
        """Register a signal class"""
        self._signals[signal_type][signal_class.__name__] = signal_class

    def get_signal(self, signal_name: str, signal_type: str, params: Dict[str, Any] = None):
        """Instantiate a signal by name"""
        signal_class = self._signals[signal_type].get(signal_name)
        if not signal_class:
            raise ValueError(f"Signal {signal_name} not found in {signal_type}")
        return signal_class(params=params)

    def list_signals(self, signal_type: Optional[str] = None):
        """List all available signals"""
        if signal_type:
            return list(self._signals[signal_type].keys())
        return {k: list(v.keys()) for k, v in self._signals.items()}


# Global signal registry
signal_registry = SignalRegistry()
