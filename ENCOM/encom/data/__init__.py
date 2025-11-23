"""
Data acquisition and management
"""

from encom.data.data_pipeline import DataPipeline, DataProvider
from encom.data.providers import YahooFinanceProvider

__all__ = [
    "DataPipeline",
    "DataProvider",
    "YahooFinanceProvider",
]
