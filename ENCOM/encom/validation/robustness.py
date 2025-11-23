"""
Robustness Testing - Sensitivity analysis and bias detection
"""

from typing import Dict, List, Any
import pandas as pd
import numpy as np


class RobustnessTest:
    """
    Tests strategy robustness and detects biases
    """

    def __init__(self):
        pass

    def parameter_sensitivity(self, backtest_func, df: pd.DataFrame,
                             base_params: Dict[str, Any],
                             param_ranges: Dict[str, List[Any]]) -> Dict[str, Any]:
        """
        Test parameter sensitivity

        Args:
            backtest_func: Backtest function
            df: Historical data
            base_params: Base parameter set
            param_ranges: Parameter variations to test

        Returns:
            Sensitivity analysis results
        """
        results = []

        for param_name, param_values in param_ranges.items():
            param_results = []

            for value in param_values:
                # Create modified params
                test_params = base_params.copy()
                test_params[param_name] = value

                # Run backtest
                result = backtest_func(df, test_params)

                param_results.append({
                    "value": value,
                    "return": result.get("total_return", 0),
                    "sharpe": result.get("sharpe_ratio", 0),
                    "max_dd": result.get("max_drawdown", 0)
                })

            # Calculate sensitivity score (variance of returns)
            returns = [r["return"] for r in param_results]
            sensitivity_score = np.std(returns)

            results.append({
                "parameter": param_name,
                "sensitivity_score": sensitivity_score,
                "results": param_results
            })

        return {"sensitivity_analysis": results}

    def detect_lookahead_bias(self, signal_func, df: pd.DataFrame) -> Dict[str, Any]:
        """
        Detect potential lookahead bias in signal generation

        Checks if signal logic uses future data
        """
        warnings = []

        # Test: Signal should not change when future data changes
        for i in range(len(df) - 10, len(df)):
            # Get signal with full data
            signal_full = signal_func(df, i)

            # Get signal with truncated data
            df_truncated = df.iloc[:i+1]
            signal_truncated = signal_func(df_truncated, i)

            if signal_full != signal_truncated:
                warnings.append(f"Lookahead bias detected at index {i}")

        return {
            "lookahead_bias_detected": len(warnings) > 0,
            "warnings": warnings
        }

    def detect_overfitting(self, train_results: Dict[str, Any],
                          test_results: Dict[str, Any],
                          threshold: float = 0.15) -> Dict[str, Any]:
        """
        Detect overfitting by comparing train/test performance

        Args:
            train_results: In-sample results
            test_results: Out-of-sample results
            threshold: Acceptable degradation threshold (default 15%)

        Returns:
            Overfitting detection results
        """
        train_return = train_results.get("total_return", 0)
        test_return = test_results.get("total_return", 0)

        degradation = (train_return - test_return) / train_return if train_return else 0

        overfitting_detected = degradation > threshold

        return {
            "overfitting_detected": overfitting_detected,
            "train_return": train_return,
            "test_return": test_return,
            "degradation_pct": degradation * 100,
            "threshold_pct": threshold * 100,
            "warning": "Strategy may be overfitted" if overfitting_detected else "No overfitting detected"
        }

    def stress_test(self, backtest_func, df: pd.DataFrame, params: Dict[str, Any],
                   commission_multipliers: List[float] = [1.0, 2.0, 3.0, 5.0],
                   slippage_multipliers: List[float] = [1.0, 2.0, 3.0, 5.0]) -> Dict[str, Any]:
        """
        Stress test with higher commissions and slippage

        Tests if strategy remains profitable under adverse conditions
        """
        results = []

        for comm_mult in commission_multipliers:
            for slip_mult in slippage_multipliers:
                # Modify execution costs
                stress_params = params.copy()
                stress_params["commission_multiplier"] = comm_mult
                stress_params["slippage_multiplier"] = slip_mult

                result = backtest_func(df, stress_params)

                results.append({
                    "commission_mult": comm_mult,
                    "slippage_mult": slip_mult,
                    "return": result.get("total_return", 0),
                    "profitable": result.get("total_return", 0) > 0
                })

        # Calculate robustness score
        profitable_scenarios = sum(1 for r in results if r["profitable"])
        robustness_score = profitable_scenarios / len(results)

        return {
            "stress_test_results": results,
            "robustness_score": robustness_score,
            "passed": robustness_score > 0.7  # 70% of scenarios profitable
        }
