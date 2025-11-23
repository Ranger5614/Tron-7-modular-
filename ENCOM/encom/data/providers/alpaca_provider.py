"""
Alpaca Markets Data Provider (Free tier available)
"""

import pandas as pd
from encom.data.data_pipeline import DataProvider


class AlpacaProvider(DataProvider):
    """
    Alpaca Markets data provider (FREE tier available)

    Supports:
    - Paper trading account (free)
    - Historical stock data
    - Real-time data feed
    """

    def __init__(self, api_key: str, secret_key: str, paper: bool = True):
        super().__init__("Alpaca Markets")
        self.api_key = api_key
        self.secret_key = secret_key
        self.paper = paper

        # TODO: Implement alpaca client
        # from alpaca.data import StockHistoricalDataClient
        # self.client = StockHistoricalDataClient(api_key, secret_key)

    def fetch_historical(self, symbol: str, start_date: str, end_date: str,
                        timeframe: str = "1d") -> pd.DataFrame:
        """
        Fetch historical data from Alpaca

        Implementation pending - requires alpaca-py package
        """
        raise NotImplementedError("Alpaca provider - Phase 2")

    def validate_symbol(self, symbol: str) -> bool:
        """Check if symbol is valid"""
        raise NotImplementedError("Alpaca provider - Phase 2")
