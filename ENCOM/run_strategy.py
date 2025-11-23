#!/usr/bin/env python3
"""
ENCOM - Strategy Backtest Runner
Run pre-built strategy templates
"""

import argparse
import sys

from encom.data import DataPipeline, YahooFinanceProvider
from encom.engine import BacktestRunner
from encom.strategies import (
    RSIMeanReversionStrategy,
    BreakoutStrategy,
    MACDTrendStrategy
)


STRATEGIES = {
    "rsi": RSIMeanReversionStrategy,
    "breakout": BreakoutStrategy,
    "macd": MACDTrendStrategy,
}


def main():
    parser = argparse.ArgumentParser(
        description="ENCOM - Run strategy templates",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Available Strategies:
  rsi       - RSI Mean Reversion (oversold bounce)
  breakout  - Price Breakout with Volume Confirmation
  macd      - MACD Trend Following

Examples:
  python run_strategy.py rsi AAPL 2023-01-01 2023-12-31
  python run_strategy.py breakout TSLA 2024-01-01 2024-12-31
  python run_strategy.py macd MSFT 2023-01-01 2023-12-31 --capital 20000

End of Line. 🎮
        """
    )

    parser.add_argument("strategy", choices=STRATEGIES.keys(), help="Strategy to run")
    parser.add_argument("symbol", help="Stock symbol (e.g., AAPL)")
    parser.add_argument("start_date", help="Start date (YYYY-MM-DD)")
    parser.add_argument("end_date", help="End date (YYYY-MM-DD)")
    parser.add_argument("--capital", type=float, default=10000, help="Initial capital")
    parser.add_argument("--quiet", action="store_true", help="Suppress output")

    args = parser.parse_args()

    try:
        # Initialize data pipeline
        data_pipeline = DataPipeline(cache_dir="./data")
        data_pipeline.set_provider(YahooFinanceProvider())

        # Create strategy
        strategy_class = STRATEGIES[args.strategy]
        strategy = strategy_class()
        signal_engine = strategy.build()

        print(f"\n📋 Strategy: {strategy.name}")
        config = strategy.get_config()
        print(f"   Core Signal: {config['core_signal']}")
        print(f"   Confirmations: Layer 1={config['confirmations']['layer1']}, Layer 2={config['confirmations']['layer2']}")
        print(f"   Filters: {config['filters']}")
        print()

        # Run backtest
        runner = BacktestRunner(data_pipeline)

        results = runner.run_backtest(
            symbol=args.symbol,
            start_date=args.start_date,
            end_date=args.end_date,
            signal_engine=signal_engine,
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
