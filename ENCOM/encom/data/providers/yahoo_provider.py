"""
Yahoo Finance Data Provider
"""

import pandas as pd
from encom.data.data_pipeline import DataProvider

try:
    import yfinance as yf
    YFINANCE_AVAILABLE = True
except ImportError:
    YFINANCE_AVAILABLE = False


class YahooFinanceProvider(DataProvider):
    """
    Yahoo Finance data provider (FREE, unlimited)

    Supports:
    - All US stocks, ETFs
    - 10+ years of historical data
    - Timeframes: 1m, 2m, 5m, 15m, 30m, 60m, 90m, 1h, 1d, 5d, 1wk, 1mo, 3mo
    """

    def __init__(self):
        super().__init__("Yahoo Finance")

        if not YFINANCE_AVAILABLE:
            raise ImportError("yfinance not installed. Run: pip install yfinance")

    def fetch_historical(self, symbol: str, start_date: str, end_date: str,
                        timeframe: str = "1d") -> pd.DataFrame:
        """
        Fetch historical data from Yahoo Finance

        Args:
            symbol: Ticker symbol (e.g., "AAPL")
            start_date: Start date (YYYY-MM-DD)
            end_date: End date (YYYY-MM-DD)
            timeframe: Interval (1d, 1h, 15m, etc.)

        Returns:
            DataFrame with OHLCV data
        """
        ticker = yf.Ticker(symbol)

        # Map timeframe to yfinance interval
        interval = self._map_timeframe(timeframe)

        df = ticker.history(start=start_date, end=end_date, interval=interval)

        if df.empty:
            raise ValueError(f"No data found for {symbol}")

        # Standardize column names
        df.columns = df.columns.str.lower()

        # Keep only OHLCV
        df = df[['open', 'high', 'low', 'close', 'volume']]

        return df

    def validate_symbol(self, symbol: str) -> bool:
        """Check if symbol is valid"""
        try:
            ticker = yf.Ticker(symbol)
            info = ticker.info
            return 'symbol' in info or 'shortName' in info
        except:
            return False

    def _map_timeframe(self, timeframe: str) -> str:
        """Map standard timeframe to yfinance interval"""
        mapping = {
            "1m": "1m",
            "5m": "5m",
            "15m": "15m",
            "30m": "30m",
            "1h": "1h",
            "1d": "1d",
            "1w": "1wk",
            "1mo": "1mo"
        }
        return mapping.get(timeframe, timeframe)
