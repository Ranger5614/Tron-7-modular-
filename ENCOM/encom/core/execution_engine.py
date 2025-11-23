"""
Execution Engine - Signal processing pipeline
"""

from typing import Dict, Any, Optional
import pandas as pd
import numpy as np
from encom.core.signal_registry import BaseSignal
from encom.core.confirmation_engine import ConfirmationEngine
from encom.core.filter_engine import FilterEngine


class SignalExecutionEngine:
    """
    Processes signals through the complete pipeline:
    Core Signal → Confirmation Layers → Quality Filters → Entry Decision

    PERFORMANCE: Supports vectorized signal pre-calculation for 10-100x speedup
    """

    def __init__(self):
        self.core_signal: Optional[BaseSignal] = None
        self.confirmation_engine = ConfirmationEngine()
        self.filter_engine = FilterEngine()

        # Vectorized signal cache
        self._vectorized_signals: Optional[np.ndarray] = None
        self._data_hash: Optional[int] = None

    def set_core_signal(self, signal: BaseSignal):
        """Set the core signal (wake-up trigger)"""
        self.core_signal = signal
        self._vectorized_signals = None  # Reset cache

    def precompute_signals(self, df: pd.DataFrame):
        """
        Pre-compute vectorized signals for entire dataset (PERFORMANCE BOOST)

        Call this before running backtest to get 10-100x speedup by calculating
        indicators once instead of on every bar.
        """
        if not self.core_signal:
            return

        # Check if we already computed for this data
        data_hash = hash(str(df.index[0]) + str(df.index[-1]) + str(len(df)))
        if self._data_hash == data_hash and self._vectorized_signals is not None:
            return  # Already computed

        # Compute vectorized signals
        if hasattr(self.core_signal, 'evaluate_vectorized'):
            self._vectorized_signals = self.core_signal.evaluate_vectorized(df)
            self._data_hash = data_hash

    def process_bar(self, df: pd.DataFrame, current_idx: int,
                   symbol_data: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Process a single bar through the complete signal pipeline

        PERFORMANCE: If precompute_signals() was called, uses cached vectorized results

        Returns:
            Dict with signal results and entry decision
        """
        result = {
            "core_triggered": False,
            "confirmations": {},
            "filters": {},
            "entry_signal": False,
            "signal_strength": 0.0
        }

        # Step 1: Check core signal
        if not self.core_signal:
            return result

        # Use vectorized signal if available (FAST PATH)
        if self._vectorized_signals is not None:
            core_triggered = bool(self._vectorized_signals[current_idx])
        else:
            # Fallback to bar-by-bar evaluation (SLOW PATH)
            core_triggered = self.core_signal.evaluate(df, current_idx)

        core_strength = self.core_signal.get_strength(df, current_idx)

        result["core_triggered"] = core_triggered
        result["core_strength"] = core_strength

        if not core_triggered:
            return result

        # Step 2: Check confirmation layers
        confirmations = self.confirmation_engine.evaluate_all(df, current_idx)
        result["confirmations"] = confirmations

        if not confirmations["confirmed"]:
            return result

        # Step 3: Apply quality filters
        filters = self.filter_engine.apply_filters(df, current_idx, symbol_data)
        result["filters"] = filters

        if not filters["passed"]:
            return result

        # All checks passed - generate entry signal
        result["entry_signal"] = True
        result["signal_strength"] = (
            core_strength * 0.5 +
            confirmations["total_strength"] * 0.5
        )

        return result
