"""
Filter Engine - Quality filters for signal validation
"""

from typing import List, Dict, Any
import pandas as pd
from encom.core.signal_registry import BaseSignal


class QualityFilter(BaseSignal):
    """
    Base class for quality filters
    """

    def __init__(self, name: str, params: Dict[str, Any] = None):
        super().__init__(name, params)
        self.signal_type = "filter"


class FilterEngine:
    """
    Manages and applies quality filters
    """

    def __init__(self):
        self.filters: List[QualityFilter] = []

    def add_filter(self, filter_obj: QualityFilter):
        """Add a quality filter"""
        self.filters.append(filter_obj)

    def apply_filters(self, df: pd.DataFrame, current_idx: int,
                     symbol_data: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Apply all quality filters

        Args:
            df: OHLCV dataframe
            current_idx: Current bar index
            symbol_data: Additional symbol metadata (volume, spread, etc.)

        Returns:
            Dict with filter results and pass/fail status
        """
        if not self.filters:
            return {"passed": True, "failed_filters": []}

        results = []
        failed_filters = []

        for f in self.filters:
            passed = f.evaluate(df, current_idx)
            results.append(passed)

            if not passed:
                failed_filters.append(f.name)

        return {
            "passed": all(results),
            "failed_filters": failed_filters,
            "total_filters": len(self.filters),
            "passed_filters": sum(results)
        }
