"""
Backtest Engine - Main backtesting orchestrator
"""

import pandas as pd
from typing import Dict, Optional
from datetime import datetime

from encom.engine.portfolio import Portfolio
from encom.engine.metrics import MetricsCalculator
from encom.core.execution_engine import SignalExecutionEngine
from encom.data.data_pipeline import DataPipeline


class BacktestEngine:
    """
    Main backtesting engine - orchestrates the entire backtest
    Clean, bar-by-bar execution with signal framework integration
    """

    def __init__(
        self,
        initial_capital: float = 10000.0,
        position_size_pct: float = 1.0,  # 100% of capital per trade
        stop_loss_pct: float = 0.02,     # 2% stop loss
        take_profit_pct: float = 0.05    # 5% take profit
    ):
        self.initial_capital = initial_capital
        self.position_size_pct = position_size_pct
        self.stop_loss_pct = stop_loss_pct
        self.take_profit_pct = take_profit_pct

        # Core components
        self.portfolio = Portfolio(initial_capital)
        self.signal_engine = SignalExecutionEngine()
        self.metrics = MetricsCalculator(self.portfolio)

    def run(
        self,
        data: pd.DataFrame,
        symbol: str,
        verbose: bool = False
    ) -> Dict:
        """
        Run backtest on historical data

        Args:
            data: OHLCV DataFrame with datetime index
            symbol: Stock symbol
            verbose: Print progress

        Returns:
            Dict with backtest results
        """
        if verbose:
            print(f"\n🚀 Running backtest on {symbol}...")
            print(f"   Data points: {len(data)}")
            print(f"   Period: {data.index[0]} to {data.index[-1]}")
            print()

        # PERFORMANCE OPTIMIZATION: Pre-compute vectorized signals once
        # This provides 10-100x speedup by calculating indicators once
        # instead of recalculating on every bar
        if verbose:
            print("⚡ Pre-computing vectorized signals...")

        self.signal_engine.precompute_signals(data)

        if verbose:
            print("✅ Signal pre-computation complete\n")

        # Bar-by-bar loop (now uses cached vectorized signals - FAST)
        for idx in range(len(data)):
            current_bar = data.iloc[idx]
            current_price = current_bar['close']
            current_time = data.index[idx]

            # Check exit conditions for open positions
            if self.portfolio.has_position(symbol):
                self._check_exits(symbol, current_price, current_time, data, idx)

            # Check entry signals if no position
            if not self.portfolio.has_position(symbol):
                self._check_entry(symbol, current_price, current_time, data, idx)

            # Update equity curve
            self.portfolio.update_equity_curve(current_time, {symbol: current_price})

        # Close any remaining positions at end
        if self.portfolio.has_position(symbol):
            final_price = data.iloc[-1]['close']
            final_time = data.index[-1]
            self.portfolio.close_position(symbol, final_price, final_time)

        if verbose:
            print(f"✅ Backtest complete!")
            print(f"   Total trades: {len(self.portfolio.get_closed_trades())}")
            print()

        # Calculate metrics
        results = self.metrics.calculate_all()
        results['symbol'] = symbol
        results['start_date'] = str(data.index[0].date())
        results['end_date'] = str(data.index[-1].date())

        return results

    def _check_entry(self, symbol: str, price: float, timestamp: datetime,
                    data: pd.DataFrame, current_idx: int):
        """Check for entry signals"""
        # Evaluate signal pipeline
        signal_result = self.signal_engine.process_bar(data, current_idx)

        if signal_result['entry_signal']:
            # Calculate position size
            available_cash = self.portfolio.get_available_cash()
            position_value = available_cash * self.position_size_pct
            quantity = int(position_value / price)

            if quantity > 0:
                success = self.portfolio.open_position(symbol, price, quantity, timestamp)

                if success and hasattr(self, '_verbose') and self._verbose:
                    print(f"  📈 BUY {quantity} shares @ ${price:.2f} on {timestamp.date()}")

    def _check_exits(self, symbol: str, price: float, timestamp: datetime,
                    data: pd.DataFrame, current_idx: int):
        """Check exit conditions (stop-loss, take-profit)"""
        pos = self.portfolio.positions.get(symbol)
        if not pos:
            return

        # Calculate P&L percentage
        pnl_pct = pos.get_pnl_pct(price) / 100  # Convert to decimal

        # Stop-loss
        if pnl_pct <= -self.stop_loss_pct:
            trade = self.portfolio.close_position(symbol, price, timestamp)
            if trade and hasattr(self, '_verbose') and self._verbose:
                print(f"  🛑 STOP LOSS: Sell @ ${price:.2f}, P&L: {trade.pnl_pct:.2f}%")
            return

        # Take-profit
        if pnl_pct >= self.take_profit_pct:
            trade = self.portfolio.close_position(symbol, price, timestamp)
            if trade and hasattr(self, '_verbose') and self._verbose:
                print(f"  ✅ TAKE PROFIT: Sell @ ${price:.2f}, P&L: {trade.pnl_pct:.2f}%")
            return


class BacktestRunner:
    """
    High-level runner for easy backtesting
    """

    def __init__(self, data_pipeline: Optional[DataPipeline] = None):
        self.data_pipeline = data_pipeline

    def run_backtest(
        self,
        symbol: str,
        start_date: str,
        end_date: str,
        signal_engine: SignalExecutionEngine,
        initial_capital: float = 10000.0,
        verbose: bool = True
    ) -> Dict:
        """
        Run complete backtest from symbol and dates

        Args:
            symbol: Stock symbol (e.g., "AAPL")
            start_date: Start date (YYYY-MM-DD)
            end_date: End date (YYYY-MM-DD)
            signal_engine: Configured signal execution engine
            initial_capital: Starting capital
            verbose: Print progress

        Returns:
            Backtest results dict
        """
        # Fetch data
        if verbose:
            print(f"📊 Fetching data for {symbol}...")

        data = self.data_pipeline.get_data(symbol, start_date, end_date, timeframe="1d")

        if verbose:
            print(f"✅ Data loaded: {len(data)} bars")

        # Create and run backtest
        engine = BacktestEngine(initial_capital=initial_capital)
        engine.signal_engine = signal_engine
        engine._verbose = verbose

        results = engine.run(data, symbol, verbose=verbose)

        # Print report
        if verbose:
            engine.metrics.print_report(symbol, start_date, end_date)

        return results
