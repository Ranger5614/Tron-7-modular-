"""
Monte Carlo Simulation - Risk modeling and confidence intervals
"""

import numpy as np
import pandas as pd
from typing import List, Dict, Any


class MonteCarloSimulator:
    """
    Monte Carlo simulation for strategy validation

    Methods:
    1. Trade sequence shuffling
    2. Geometric Brownian Motion (GBM)
    3. Random walk simulation
    4. Bootstrap resampling
    """

    def __init__(self, num_simulations: int = 1000, confidence_level: float = 0.95):
        """
        Args:
            num_simulations: Number of Monte Carlo runs
            confidence_level: Confidence level (0.95 = 95%)
        """
        self.num_simulations = num_simulations
        self.confidence_level = confidence_level

    def shuffle_trades(self, trades: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Shuffle trade sequence and calculate confidence intervals

        Args:
            trades: List of trade results (pnl, return_pct)

        Returns:
            Monte Carlo results with confidence intervals
        """
        equity_curves = []

        for _ in range(self.num_simulations):
            # Shuffle trades
            shuffled = np.random.permutation(trades)

            # Calculate equity curve
            equity = [1.0]  # Start with 1.0 (100%)
            for trade in shuffled:
                equity.append(equity[-1] * (1 + trade["return_pct"]))

            equity_curves.append(equity)

        # Calculate statistics
        equity_array = np.array(equity_curves)

        lower_bound = np.percentile(equity_array, (1 - self.confidence_level) * 100 / 2, axis=0)
        upper_bound = np.percentile(equity_array, 100 - (1 - self.confidence_level) * 100 / 2, axis=0)
        median = np.percentile(equity_array, 50, axis=0)

        return {
            "equity_curves": equity_curves,
            "lower_bound": lower_bound.tolist(),
            "upper_bound": upper_bound.tolist(),
            "median": median.tolist(),
            "confidence_level": self.confidence_level
        }

    def geometric_brownian_motion(self, initial_price: float, mu: float, sigma: float,
                                  days: int) -> Dict[str, Any]:
        """
        Simulate price paths using Geometric Brownian Motion

        Args:
            initial_price: Starting price
            mu: Expected return (drift)
            sigma: Volatility (standard deviation)
            days: Number of days to simulate

        Returns:
            Simulated price paths and statistics
        """
        dt = 1  # Daily time step
        price_paths = []

        for _ in range(self.num_simulations):
            prices = [initial_price]

            for _ in range(days):
                # GBM formula: dS = μS dt + σS dW
                drift = mu * prices[-1] * dt
                shock = sigma * prices[-1] * np.random.normal() * np.sqrt(dt)
                prices.append(prices[-1] + drift + shock)

            price_paths.append(prices)

        # Calculate statistics
        paths_array = np.array(price_paths)

        return {
            "price_paths": price_paths,
            "mean_path": np.mean(paths_array, axis=0).tolist(),
            "lower_bound": np.percentile(paths_array, (1 - self.confidence_level) * 100 / 2, axis=0).tolist(),
            "upper_bound": np.percentile(paths_array, 100 - (1 - self.confidence_level) * 100 / 2, axis=0).tolist()
        }

    def calculate_risk_metrics(self, equity_curves: List[List[float]]) -> Dict[str, Any]:
        """
        Calculate risk metrics from Monte Carlo simulations

        Returns:
            Risk metrics including probability of ruin, worst-case DD, etc.
        """
        final_values = [curve[-1] for curve in equity_curves]
        max_drawdowns = []

        for curve in equity_curves:
            peak = curve[0]
            max_dd = 0
            for val in curve:
                if val > peak:
                    peak = val
                dd = (peak - val) / peak
                if dd > max_dd:
                    max_dd = dd
            max_drawdowns.append(max_dd)

        # Probability of ruin (ending below starting capital)
        prob_of_ruin = sum(1 for val in final_values if val < 1.0) / len(final_values)

        return {
            "probability_of_ruin": prob_of_ruin,
            "worst_case_final_value": min(final_values),
            "best_case_final_value": max(final_values),
            "median_final_value": np.median(final_values),
            "worst_case_drawdown": max(max_drawdowns),
            "median_drawdown": np.median(max_drawdowns),
            "expected_drawdown_95pct": np.percentile(max_drawdowns, 95)
        }
