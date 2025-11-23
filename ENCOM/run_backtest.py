#!/usr/bin/env python3
"""
ENCOM - CLI Backtest Runner
Simple command-line interface to run backtests
"""

import argparse
import sys

# Add parent directory to path for imports
from encom.data import DataPipeline, YahooFinanceProvider
from encom.engine import BacktestRunner
from encom.core import SignalExecutionEngine
from encom.signals.core_signals.ma_crossover import MACrossover
from encom.signals.filters.volume_filter import VolumeFilter


def create_ma_crossover_strategy(fast_period: int = 20, slow_period: int = 50):
    """
    Create MA Crossover strategy with volume filter

    Strategy:
    - Core Signal: MA Crossover (fast crosses above slow)
    - Filter: Minimum volume (1M USD)
    """
    engine = SignalExecutionEngine()

    # Core signal
    ma_signal = MACrossover(params={
        "fast_period": fast_period,
        "slow_period": slow_period
    })
    engine.set_core_signal(ma_signal)

    # Quality filter
    volume_filter = VolumeFilter(params={
        "min_volume_usd": 1_000_000
    })
    engine.filter_engine.add_filter(volume_filter)

    return engine


def main():
    parser = argparse.ArgumentParser(
        description="ENCOM - Backtest a trading strategy",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python run_backtest.py AAPL 2024-01-01 2024-12-31
  python run_backtest.py TSLA 2023-01-01 2023-12-31 --fast 10 --slow 30
  python run_backtest.py MSFT 2024-01-01 2024-12-31 --capital 20000

End of Line. 🎮
        """
    )

    parser.add_argument("symbol", help="Stock symbol (e.g., AAPL)")
    parser.add_argument("start_date", help="Start date (YYYY-MM-DD)")
    parser.add_argument("end_date", help="End date (YYYY-MM-DD)")
    parser.add_argument("--fast", type=int, default=20, help="Fast MA period (default: 20)")
    parser.add_argument("--slow", type=int, default=50, help="Slow MA period (default: 50)")
    parser.add_argument("--capital", type=float, default=10000, help="Initial capital (default: 10000)")
    parser.add_argument("--quiet", action="store_true", help="Suppress output")

    args = parser.parse_args()

    # Validate dates
    if args.start_date >= args.end_date:
        print("❌ Error: start_date must be before end_date")
        sys.exit(1)

    try:
        # Initialize data pipeline
        data_pipeline = DataPipeline(cache_dir="./data")
        data_pipeline.set_provider(YahooFinanceProvider())

        # Create strategy
        strategy = create_ma_crossover_strategy(
            fast_period=args.fast,
            slow_period=args.slow
        )

        # Run backtest
        runner = BacktestRunner(data_pipeline)

        results = runner.run_backtest(
            symbol=args.symbol,
            start_date=args.start_date,
            end_date=args.end_date,
            signal_engine=strategy,
            initial_capital=args.capital,
            verbose=not args.quiet
        )

        # Exit code based on profitability
        sys.exit(0 if results['profitable'] else 1)

    except Exception as e:
        print(f"\n❌ Error: {e}\n")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
