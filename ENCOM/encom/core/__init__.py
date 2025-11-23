"""
Core signal framework engine
"""

from encom.core.signal_registry import BaseSignal, SignalRegistry, signal_registry
from encom.core.confirmation_engine import ConfirmationEngine, ConfirmationLayer
from encom.core.filter_engine import FilterEngine, QualityFilter
from encom.core.execution_engine import SignalExecutionEngine

__all__ = [
    "BaseSignal",
    "SignalRegistry",
    "signal_registry",
    "ConfirmationEngine",
    "ConfirmationLayer",
    "FilterEngine",
    "QualityFilter",
    "SignalExecutionEngine",
]
