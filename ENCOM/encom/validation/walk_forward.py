"""
Walk-Forward Analysis - Out-of-sample validation
"""

from typing import Dict, List, Any
import pandas as pd


class WalkForwardAnalysis:
    """
    Performs walk-forward analysis with rolling windows

    Methodology:
    1. Split data into train/test windows
    2. Optimize on train window
    3. Test on out-of-sample test window
    4. Roll forward and repeat
    5. Analyze in-sample vs out-of-sample degradation
    """

    def __init__(self, train_size: int, test_size: int, step_size: int):
        """
        Args:
            train_size: Training window size (days)
            test_size: Testing window size (days)
            step_size: Step size for rolling window (days)
        """
        self.train_size = train_size
        self.test_size = test_size
        self.step_size = step_size

    def generate_windows(self, df: pd.DataFrame) -> List[Dict[str, Any]]:
        """
        Generate train/test windows

        Returns:
            List of window dicts with train/test date ranges
        """
        windows = []
        total_days = len(df)

        start_idx = 0
        while start_idx + self.train_size + self.test_size <= total_days:
            train_end_idx = start_idx + self.train_size
            test_end_idx = train_end_idx + self.test_size

            windows.append({
                "window_id": len(windows) + 1,
                "train_start": df.index[start_idx],
                "train_end": df.index[train_end_idx - 1],
                "test_start": df.index[train_end_idx],
                "test_end": df.index[test_end_idx - 1],
                "train_data": df.iloc[start_idx:train_end_idx],
                "test_data": df.iloc[train_end_idx:test_end_idx]
            })

            start_idx += self.step_size

        return windows

    def run_analysis(self, backtest_func, optimize_func, df: pd.DataFrame,
                    strategy_params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Run walk-forward analysis

        Args:
            backtest_func: Function to run backtest
            optimize_func: Function to optimize parameters
            df: Historical data
            strategy_params: Initial strategy parameters

        Returns:
            Walk-forward results with degradation metrics
        """
        windows = self.generate_windows(df)
        results = []

        for window in windows:
            # Optimize on train data
            optimized_params = optimize_func(
                window["train_data"],
                strategy_params
            )

            # Test on train data (in-sample)
            train_result = backtest_func(
                window["train_data"],
                optimized_params
            )

            # Test on test data (out-of-sample)
            test_result = backtest_func(
                window["test_data"],
                optimized_params
            )

            results.append({
                "window_id": window["window_id"],
                "train_return": train_result["total_return"],
                "test_return": test_result["total_return"],
                "train_sharpe": train_result.get("sharpe_ratio", 0),
                "test_sharpe": test_result.get("sharpe_ratio", 0),
                "degradation": train_result["total_return"] - test_result["total_return"]
            })

        # Calculate summary statistics
        avg_train_return = sum(r["train_return"] for r in results) / len(results)
        avg_test_return = sum(r["test_return"] for r in results) / len(results)
        avg_degradation = sum(r["degradation"] for r in results) / len(results)

        return {
            "windows": results,
            "summary": {
                "avg_in_sample_return": avg_train_return,
                "avg_out_of_sample_return": avg_test_return,
                "avg_degradation": avg_degradation,
                "degradation_pct": (avg_degradation / avg_train_return * 100) if avg_train_return else 0
            }
        }
