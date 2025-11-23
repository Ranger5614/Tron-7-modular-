"""
ENCOM - Enhanced Network Command
Signal-based visual backtesting platform for systematic strategy development
"""

__version__ = "0.2.0"
__author__ = "Ranger5614"
__description__ = "Modular signal-based backtesting platform"

# Core framework
from encom.core.signal_registry import BaseSignal, SignalRegistry, signal_registry
from encom.core.confirmation_engine import ConfirmationEngine, ConfirmationLayer
from encom.core.filter_engine import FilterEngine, QualityFilter
from encom.core.execution_engine import SignalExecutionEngine

# Data
from encom.data import DataPipeline, DataProvider, YahooFinanceProvider

# Validation
from encom.validation import WalkForwardAnalysis, MonteCarloSimulator, RobustnessTest

# Signals
from encom.signals import MACrossover, VolumeFilter

__all__ = [
    # Core
    "BaseSignal",
    "SignalRegistry",
    "signal_registry",
    "ConfirmationEngine",
    "ConfirmationLayer",
    "FilterEngine",
    "QualityFilter",
    "SignalExecutionEngine",
    # Data
    "DataPipeline",
    "DataProvider",
    "YahooFinanceProvider",
    # Validation
    "WalkForwardAnalysis",
    "MonteCarloSimulator",
    "RobustnessTest",
    # Signals
    "MACrossover",
    "VolumeFilter",
]
