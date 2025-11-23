#!/usr/bin/env python3
"""
Backtest Performance Benchmark
Compare vectorized vs bar-by-bar signal evaluation
"""

import time
import numpy as np
import pandas as pd
from encom.data import DataPipeline, YahooFinanceProvider
from encom.engine import BacktestRunner
from encom.strategies import RSIMeanReversionStrategy, MACDTrendStrategy

def benchmark_strategy(strategy_name, strategy_class, symbol, start_date, end_date):
    """Benchmark a strategy with vectorized signals"""
    print(f"\n{'='*60}")
    print(f"BENCHMARK: {strategy_name}")
    print(f"{'='*60}")

    # Initialize data pipeline
    data_pipeline = DataPipeline(cache_dir="./data")
    data_pipeline.set_provider(YahooFinanceProvider())

    # Create strategy
    strategy = strategy_class()
    signal_engine = strategy.build()

    # Run backtest with timing
    runner = BacktestRunner(data_pipeline)

    print(f"Symbol: {symbol}")
    print(f"Period: {start_date} to {end_date}")
    print(f"\nRunning backtest with VECTORIZED signals...")

    start = time.time()
    results = runner.run_backtest(
        symbol=symbol,
        start_date=start_date,
        end_date=end_date,
        signal_engine=signal_engine,
        initial_capital=10000,
        verbose=False
    )
    elapsed = time.time() - start

    # Results
    print(f"\n⚡ PERFORMANCE METRICS:")
    print(f"   Execution Time:  {elapsed:.4f}s")
    print(f"   Bars Processed:  {results.get('total_bars', 'N/A')}")
    if results.get('total_bars'):
        bars_per_sec = results['total_bars'] / elapsed
        print(f"   Throughput:      {bars_per_sec:.0f} bars/sec")

    print(f"\n📊 BACKTEST RESULTS:")
    print(f"   Total Return:    {results['total_return']:.2f}%")
    print(f"   Total Trades:    {results['total_trades']}")
    print(f"   Win Rate:        {results['win_rate']:.1f}%")
    print(f"   Sharpe Ratio:    {results['sharpe_ratio']:.2f}")
    print(f"   Max Drawdown:    {results['max_drawdown']:.2f}%")

    return elapsed, results

def main():
    print("""
╔══════════════════════════════════════════════════════════╗
║  ENCOM BACKTEST PERFORMANCE BENCHMARK                   ║
║  Testing Numba-optimized vectorized signals             ║
╚══════════════════════════════════════════════════════════╝
    """)

    # Test parameters
    symbol = "AAPL"
    start_date = "2022-01-01"
    end_date = "2023-12-31"

    print(f"Test Configuration:")
    print(f"  Symbol:      {symbol}")
    print(f"  Date Range:  {start_date} to {end_date}")
    print(f"  Data Points: ~2 years (500+ bars)")

    # Benchmark RSI strategy
    rsi_time, rsi_results = benchmark_strategy(
        "RSI Mean Reversion",
        RSIMeanReversionStrategy,
        symbol,
        start_date,
        end_date
    )

    # Benchmark MACD strategy
    macd_time, macd_results = benchmark_strategy(
        "MACD Trend Following",
        MACDTrendStrategy,
        symbol,
        start_date,
        end_date
    )

    # Summary
    print(f"\n{'='*60}")
    print(f"BENCHMARK SUMMARY")
    print(f"{'='*60}")
    print(f"\nRSI Strategy:   {rsi_time:.4f}s")
    print(f"MACD Strategy:  {macd_time:.4f}s")
    print(f"\nExpected Performance:")
    print(f"  - With Numba JIT:  10-100x faster than pandas")
    print(f"  - 2 year backtest: <1 second")
    print(f"  - 10 year backtest: <5 seconds")
    print(f"\n🚀 Optimization Status: {'ACTIVE' if rsi_time < 2 else 'CHECK NUMBA'}")
    print(f"\nEnd of Line. 🎮")

if __name__ == "__main__":
    main()
