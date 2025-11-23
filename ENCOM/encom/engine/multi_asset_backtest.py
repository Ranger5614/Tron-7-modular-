"""
Multi-Asset Backtesting Engine for ENCOM

Test strategies across 50+ stocks simultaneously with parallel processing.
Portfolio-level metrics, correlation analysis, and sector allocation.

Author: ENCOM Development Team
License: MIT
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Optional
from concurrent.futures import ProcessPoolExecutor, as_completed
from dataclasses import dataclass
import time

from encom.engine.backtest_engine import BacktestRunner
from encom.data.data_pipeline import DataPipeline


@dataclass
class MultiAssetResult:
    """Container for multi-asset backtest results"""
    symbol_results: Dict[str, Dict]  # Results per symbol
    portfolio_metrics: Dict  # Portfolio-level metrics
    correlation_matrix: pd.DataFrame  # Return correlations
    sector_allocation: Dict  # Allocation by sector
    top_performers: List[str]  # Best performing symbols
    worst_performers: List[str]  # Worst performing symbols
    total_runtime: float


class MultiAssetBacktester:
    """
    Run backtests across multiple assets simultaneously

    Features:
    - Parallel execution (multiprocessing)
    - Portfolio-level metrics
    - Correlation analysis
    - Sector/industry analysis
    - Position sizing across portfolio
    """

    def __init__(self, strategy_class, symbols: List[str],
                 start_date: str, end_date: str,
                 initial_capital: float = 10000,
                 capital_per_symbol: Optional[float] = None,
                 n_jobs: int = -1):
        """
        Args:
            strategy_class: Strategy class to backtest
            symbols: List of symbols to test
            start_date: Start date (YYYY-MM-DD)
            end_date: End date (YYYY-MM-DD)
            initial_capital: Total portfolio capital
            capital_per_symbol: Capital allocated per symbol (None = equal weight)
            n_jobs: Number of parallel jobs (-1 = all CPUs)
        """
        self.strategy_class = strategy_class
        self.symbols = symbols
        self.start_date = start_date
        self.end_date = end_date
        self.initial_capital = initial_capital

        # Calculate capital per symbol
        if capital_per_symbol is None:
            self.capital_per_symbol = initial_capital / len(symbols)
        else:
            self.capital_per_symbol = capital_per_symbol

        # Parallel processing
        import multiprocessing
        if n_jobs == -1:
            self.n_jobs = multiprocessing.cpu_count()
        else:
            self.n_jobs = n_jobs

        self.data_pipeline = DataPipeline()

    def run(self, verbose: bool = True) -> MultiAssetResult:
        """
        Run multi-asset backtest

        Args:
            verbose: Show progress

        Returns:
            MultiAssetResult with all results
        """
        start_time = time.time()

        if verbose:
            print("=" * 70)
            print("MULTI-ASSET BACKTEST")
            print("=" * 70)
            print(f"Symbols: {len(self.symbols)}")
            print(f"Period: {self.start_date} to {self.end_date}")
            print(f"Initial Capital: ${self.initial_capital:,.2f}")
            print(f"Capital per Symbol: ${self.capital_per_symbol:,.2f}")
            print(f"Parallel Jobs: {self.n_jobs}")
            print()

        # Fetch all data first
        if verbose:
            print("Fetching market data...")

        symbol_data = {}
        failed_symbols = []

        for symbol in self.symbols:
            try:
                data = self.data_pipeline.get_data(
                    symbol,
                    start_date=self.start_date,
                    end_date=self.end_date
                )

                if data is not None and len(data) > 0:
                    symbol_data[symbol] = data
                else:
                    failed_symbols.append(symbol)

            except Exception as e:
                if verbose:
                    print(f"  ⚠️  Failed to fetch {symbol}: {e}")
                failed_symbols.append(symbol)

        if verbose:
            print(f"  ✅ Loaded {len(symbol_data)} symbols")
            if failed_symbols:
                print(f"  ⚠️  Failed: {len(failed_symbols)} symbols")
            print()

        # Run backtests in parallel
        if verbose:
            print("Running backtests...")

        symbol_results = {}

        if self.n_jobs == 1:
            # Sequential execution
            for symbol, data in symbol_data.items():
                result = self._run_single_backtest(symbol, data, verbose)
                symbol_results[symbol] = result

        else:
            # Parallel execution
            with ProcessPoolExecutor(max_workers=self.n_jobs) as executor:
                futures = {}

                for symbol, data in symbol_data.items():
                    future = executor.submit(
                        self._run_single_backtest,
                        symbol, data, False
                    )
                    futures[future] = symbol

                # Collect results
                completed = 0
                total = len(futures)

                for future in as_completed(futures):
                    symbol = futures[future]

                    try:
                        result = future.result()
                        symbol_results[symbol] = result

                        completed += 1
                        if verbose:
                            pct = (completed / total) * 100
                            print(f"  Progress: {completed}/{total} ({pct:.1f}%)")

                    except Exception as e:
                        if verbose:
                            print(f"  ❌ {symbol} failed: {e}")

        if verbose:
            print(f"  ✅ Completed {len(symbol_results)} backtests")
            print()

        # Calculate portfolio-level metrics
        if verbose:
            print("Calculating portfolio metrics...")

        portfolio_metrics = self._calculate_portfolio_metrics(symbol_results)

        # Calculate correlations
        correlation_matrix = self._calculate_correlations(symbol_data)

        # Identify top/worst performers
        top_performers = self._get_top_performers(symbol_results, n=10)
        worst_performers = self._get_worst_performers(symbol_results, n=10)

        # Sector allocation (placeholder - would need sector data)
        sector_allocation = {}

        total_runtime = time.time() - start_time

        if verbose:
            print()
            self._print_summary(portfolio_metrics, top_performers, worst_performers)

        return MultiAssetResult(
            symbol_results=symbol_results,
            portfolio_metrics=portfolio_metrics,
            correlation_matrix=correlation_matrix,
            sector_allocation=sector_allocation,
            top_performers=top_performers,
            worst_performers=worst_performers,
            total_runtime=total_runtime
        )

    def _run_single_backtest(self, symbol: str, data: pd.DataFrame, verbose: bool = False):
        """Run backtest for single symbol"""
        try:
            # Create strategy instance
            strategy = self.strategy_class()

            # Run backtest
            runner = BacktestRunner(
                strategy=strategy,
                data=data,
                initial_capital=self.capital_per_symbol
            )

            result = runner.run(verbose=False)
            result['symbol'] = symbol

            return result

        except Exception as e:
            return {
                'symbol': symbol,
                'error': str(e),
                'metrics': {}
            }

    def _calculate_portfolio_metrics(self, symbol_results: Dict) -> Dict:
        """Calculate portfolio-level metrics"""
        metrics = {}

        # Aggregate metrics
        total_return = 0
        total_trades = 0
        winning_trades = 0
        losing_trades = 0
        total_pnl = 0

        valid_results = [r for r in symbol_results.values() if 'error' not in r]

        if not valid_results:
            return metrics

        for result in valid_results:
            result_metrics = result.get('metrics', {})

            total_return += result_metrics.get('total_return', 0)
            total_trades += result_metrics.get('total_trades', 0)
            winning_trades += result_metrics.get('winning_trades', 0)
            losing_trades += result_metrics.get('losing_trades', 0)

            # Calculate P&L from equity
            portfolio = result.get('portfolio')
            if portfolio:
                final_equity = portfolio.get_equity()
                pnl = final_equity - self.capital_per_symbol
                total_pnl += pnl

        # Portfolio metrics
        n_symbols = len(valid_results)

        metrics['total_symbols'] = n_symbols
        metrics['avg_return_per_symbol'] = total_return / n_symbols if n_symbols > 0 else 0
        metrics['total_portfolio_pnl'] = total_pnl
        metrics['portfolio_return_pct'] = (total_pnl / self.initial_capital) * 100 if self.initial_capital > 0 else 0
        metrics['total_trades'] = total_trades
        metrics['avg_trades_per_symbol'] = total_trades / n_symbols if n_symbols > 0 else 0
        metrics['winning_trades'] = winning_trades
        metrics['losing_trades'] = losing_trades
        metrics['portfolio_win_rate'] = (winning_trades / total_trades * 100) if total_trades > 0 else 0

        # Best/worst performing symbols
        returns = [(r['symbol'], r['metrics'].get('total_return', 0))
                  for r in valid_results]
        returns.sort(key=lambda x: x[1], reverse=True)

        if returns:
            metrics['best_symbol'] = returns[0][0]
            metrics['best_return'] = returns[0][1]
            metrics['worst_symbol'] = returns[-1][0]
            metrics['worst_return'] = returns[-1][1]

        return metrics

    def _calculate_correlations(self, symbol_data: Dict[str, pd.DataFrame]) -> pd.DataFrame:
        """Calculate return correlations between symbols"""
        if len(symbol_data) < 2:
            return pd.DataFrame()

        # Calculate returns for each symbol
        returns_dict = {}

        for symbol, data in symbol_data.items():
            if 'close' in data.columns:
                returns = data['close'].pct_change().dropna()
                returns_dict[symbol] = returns

        if not returns_dict:
            return pd.DataFrame()

        # Create returns DataFrame
        returns_df = pd.DataFrame(returns_dict)

        # Calculate correlation matrix
        correlation_matrix = returns_df.corr()

        return correlation_matrix

    def _get_top_performers(self, symbol_results: Dict, n: int = 10) -> List[str]:
        """Get top N performing symbols"""
        valid_results = [r for r in symbol_results.values() if 'error' not in r]

        returns = [(r['symbol'], r['metrics'].get('total_return', 0))
                  for r in valid_results]
        returns.sort(key=lambda x: x[1], reverse=True)

        return [symbol for symbol, _ in returns[:n]]

    def _get_worst_performers(self, symbol_results: Dict, n: int = 10) -> List[str]:
        """Get worst N performing symbols"""
        valid_results = [r for r in symbol_results.values() if 'error' not in r]

        returns = [(r['symbol'], r['metrics'].get('total_return', 0))
                  for r in valid_results]
        returns.sort(key=lambda x: x[1])

        return [symbol for symbol, _ in returns[:n]]

    def _print_summary(self, portfolio_metrics: Dict,
                      top_performers: List[str],
                      worst_performers: List[str]):
        """Print summary results"""
        print("=" * 70)
        print("PORTFOLIO SUMMARY")
        print("=" * 70)
        print()

        print(f"Total Symbols Tested: {portfolio_metrics.get('total_symbols', 0)}")
        print(f"Portfolio Return: {portfolio_metrics.get('portfolio_return_pct', 0):.2f}%")
        print(f"Total P&L: ${portfolio_metrics.get('total_portfolio_pnl', 0):,.2f}")
        print(f"Total Trades: {portfolio_metrics.get('total_trades', 0)}")
        print(f"Portfolio Win Rate: {portfolio_metrics.get('portfolio_win_rate', 0):.2f}%")
        print()

        print(f"Best Performer: {portfolio_metrics.get('best_symbol', 'N/A')} "
              f"({portfolio_metrics.get('best_return', 0):.2f}%)")
        print(f"Worst Performer: {portfolio_metrics.get('worst_symbol', 'N/A')} "
              f"({portfolio_metrics.get('worst_return', 0):.2f}%)")
        print()

        if top_performers:
            print(f"Top 10 Performers: {', '.join(top_performers[:10])}")
            print()

        print("=" * 70)


def run_multi_asset_backtest(strategy_class, symbols: List[str],
                             start_date: str, end_date: str,
                             initial_capital: float = 100000,
                             n_jobs: int = -1,
                             verbose: bool = True) -> MultiAssetResult:
    """
    Convenience function to run multi-asset backtest

    Args:
        strategy_class: Strategy to test
        symbols: List of symbols
        start_date: Start date
        end_date: End date
        initial_capital: Total portfolio capital
        n_jobs: Parallel jobs
        verbose: Show progress

    Returns:
        MultiAssetResult
    """
    backtester = MultiAssetBacktester(
        strategy_class=strategy_class,
        symbols=symbols,
        start_date=start_date,
        end_date=end_date,
        initial_capital=initial_capital,
        n_jobs=n_jobs
    )

    return backtester.run(verbose=verbose)
