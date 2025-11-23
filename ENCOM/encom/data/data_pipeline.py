"""
Data Pipeline - Main data acquisition and management
"""

from abc import ABC, abstractmethod
from typing import Optional, Dict, Any
import pandas as pd
from datetime import datetime
from pathlib import Path


class DataProvider(ABC):
    """
    Base class for all data providers
    """

    def __init__(self, name: str):
        self.name = name

    @abstractmethod
    def fetch_historical(self, symbol: str, start_date: str, end_date: str,
                        timeframe: str = "1d") -> pd.DataFrame:
        """
        Fetch historical OHLCV data

        Args:
            symbol: Ticker symbol (e.g., "AAPL")
            start_date: Start date (YYYY-MM-DD)
            end_date: End date (YYYY-MM-DD)
            timeframe: Timeframe (1d, 1h, 15m, etc.)

        Returns:
            DataFrame with columns: [open, high, low, close, volume]
        """
        pass

    @abstractmethod
    def validate_symbol(self, symbol: str) -> bool:
        """Check if symbol is valid"""
        pass


class DataPipeline:
    """
    Manages data fetching, caching, and preprocessing
    """

    def __init__(self, cache_dir: str = "./data", provider: Optional[DataProvider] = None):
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(exist_ok=True, parents=True)
        self.provider = provider

    def set_provider(self, provider: DataProvider):
        """Set the data provider"""
        self.provider = provider

    def get_data(self, symbol: str, start_date: str, end_date: str,
                timeframe: str = "1d", use_cache: bool = True) -> pd.DataFrame:
        """
        Get historical data (from cache or fetch)

        Args:
            symbol: Ticker symbol
            start_date: Start date (YYYY-MM-DD)
            end_date: End date (YYYY-MM-DD)
            timeframe: Timeframe
            use_cache: Use cached data if available

        Returns:
            DataFrame with OHLCV data
        """
        if not self.provider:
            raise ValueError("No data provider set")

        # Check cache first
        if use_cache:
            cached_data = self._load_from_cache(symbol, start_date, end_date, timeframe)
            if cached_data is not None:
                return cached_data

        # Fetch from provider
        df = self.provider.fetch_historical(symbol, start_date, end_date, timeframe)

        # Validate and clean
        df = self._validate_data(df)

        # Save to cache
        self._save_to_cache(df, symbol, start_date, end_date, timeframe)

        return df

    def _load_from_cache(self, symbol: str, start_date: str, end_date: str,
                        timeframe: str) -> Optional[pd.DataFrame]:
        """Load data from cache"""
        cache_file = self._get_cache_path(symbol, timeframe)

        if not cache_file.exists():
            return None

        try:
            df = pd.read_parquet(cache_file)

            # Filter to requested date range
            df = df[(df.index >= start_date) & (df.index <= end_date)]

            # Check if we have complete data
            if len(df) == 0:
                return None

            return df

        except Exception as e:
            print(f"Error loading cache: {e}")
            return None

    def _save_to_cache(self, df: pd.DataFrame, symbol: str, start_date: str,
                      end_date: str, timeframe: str):
        """Save data to cache"""
        cache_file = self._get_cache_path(symbol, timeframe)

        try:
            # Load existing cache if exists
            if cache_file.exists():
                existing_df = pd.read_parquet(cache_file)
                # Merge and remove duplicates
                df = pd.concat([existing_df, df]).drop_duplicates()
                df = df.sort_index()

            df.to_parquet(cache_file)

        except Exception as e:
            print(f"Error saving cache: {e}")

    def _get_cache_path(self, symbol: str, timeframe: str) -> Path:
        """Get cache file path"""
        return self.cache_dir / f"{symbol}_{timeframe}.parquet"

    def _validate_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """Validate and clean data"""
        # Ensure required columns
        required_cols = ['open', 'high', 'low', 'close', 'volume']
        for col in required_cols:
            if col not in df.columns:
                raise ValueError(f"Missing required column: {col}")

        # Remove NaN values
        df = df.dropna()

        # Ensure index is datetime
        if not isinstance(df.index, pd.DatetimeIndex):
            df.index = pd.to_datetime(df.index)

        # Sort by date
        df = df.sort_index()

        return df

    def clear_cache(self, symbol: Optional[str] = None):
        """Clear cache for symbol or all"""
        if symbol:
            for file in self.cache_dir.glob(f"{symbol}_*.parquet"):
                file.unlink()
        else:
            for file in self.cache_dir.glob("*.parquet"):
                file.unlink()
