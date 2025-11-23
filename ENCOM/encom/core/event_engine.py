"""
Event Engine - Event-driven backtest loop
"""


class EventEngine:
    """
    Manages bar-by-bar event-driven simulation

    Features:
    - Bar-by-bar playback
    - Timestamp synchronization
    - Lookahead bias prevention
    - State persistence
    """

    def __init__(self):
        self.current_timestamp = None

    def run_backtest(self, data, strategy, portfolio):
        """Execute bar-by-bar backtest"""
        raise NotImplementedError("EventEngine.run_backtest - Phase 1")

    def process_bar(self, bar_data):
        """Process single bar of data"""
        raise NotImplementedError("EventEngine.process_bar - Phase 1")
