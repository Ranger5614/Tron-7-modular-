"""
Strategy Bridge - Tron 7 strategy adapter
"""


class StrategyBridge:
    """
    Adapts Tron 7 strategies for backtesting

    Features:
    - Import Tron 7 BaseStrategy implementations
    - Mock market data provider
    - Signal extraction
    - Parameter override
    """

    def __init__(self, strategy_class):
        self.strategy_class = strategy_class

    def import_strategy(self, strategy_path):
        """Import strategy from Tron 7"""
        raise NotImplementedError("StrategyBridge.import_strategy - Phase 2")

    def extract_signals(self, symbol, candles):
        """Extract entry/exit signals from strategy"""
        raise NotImplementedError("StrategyBridge.extract_signals - Phase 2")
