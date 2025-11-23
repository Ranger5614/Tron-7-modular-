"""
Base Strategy - Template for building complete strategies
"""

from encom.core import SignalExecutionEngine


class BaseStrategy:
    """
    Base class for strategy templates

    Strategies combine:
    - 1 Core Signal (entry trigger)
    - 0-2 Confirmation Layers
    - 0+ Quality Filters
    """

    def __init__(self, name: str = "Base Strategy"):
        self.name = name
        self.engine = SignalExecutionEngine()

    def build(self) -> SignalExecutionEngine:
        """
        Build and return configured signal execution engine

        Override this method in subclasses to configure signals
        """
        raise NotImplementedError("Subclasses must implement build()")

    def get_config(self) -> dict:
        """Get strategy configuration"""
        return {
            "name": self.name,
            "core_signal": self.engine.core_signal.name if self.engine.core_signal else None,
            "confirmations": {
                "layer1": len(self.engine.confirmation_engine.layer1.signals),
                "layer2": len(self.engine.confirmation_engine.layer2.signals),
            },
            "filters": len(self.engine.filter_engine.filters)
        }
