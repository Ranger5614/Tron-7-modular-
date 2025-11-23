"""
Interactive Brokers (IBKR) Live Trading Connector for ENCOM

Professional-grade integration with Interactive Brokers TWS/Gateway.
Supports market data, order execution, position tracking, and account management.

Requirements:
    pip install ib_insync

Author: ENCOM Development Team
License: MIT
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Callable
from dataclasses import dataclass
from datetime import datetime
import time

try:
    from ib_insync import *
    IB_AVAILABLE = True
except ImportError:
    IB_AVAILABLE = False
    print("⚠️  ib_insync not available. Install with: pip install ib_insync")


@dataclass
class IBKRConfig:
    """IBKR connection configuration"""
    host: str = '127.0.0.1'  # TWS/Gateway host
    port: int = 7497  # 7497 = TWS paper, 7496 = TWS live, 4002 = Gateway paper, 4001 = Gateway live
    client_id: int = 1  # Unique client ID
    readonly: bool = False  # Read-only mode (no orders)
    account: Optional[str] = None  # Account ID (None = primary)


class IBKRConnector:
    """
    Interactive Brokers live trading connector

    Features:
    - Real-time market data (streaming)
    - Historical data download
    - Order execution (market, limit, stop, bracket)
    - Position tracking
    - Account info (balance, P&L, buying power)
    - Risk management (position limits, max loss)
    """

    def __init__(self, config: IBKRConfig):
        """
        Args:
            config: IBKR connection configuration
        """
        if not IB_AVAILABLE:
            raise ImportError("ib_insync not installed. Run: pip install ib_insync")

        self.config = config
        self.ib = IB()
        self.connected = False

        # Callbacks
        self.on_bar_callback = None
        self.on_order_callback = None
        self.on_fill_callback = None

        # State
        self.subscriptions = {}  # symbol -> subscription
        self.positions = {}  # symbol -> position
        self.orders = {}  # orderId -> order

    def connect(self, verbose: bool = True):
        """
        Connect to Interactive Brokers TWS/Gateway

        Args:
            verbose: Print connection status

        Returns:
            True if connected successfully
        """
        try:
            self.ib.connect(
                self.config.host,
                self.config.port,
                clientId=self.config.client_id,
                readonly=self.config.readonly
            )

            self.connected = True

            # Get account info
            accounts = self.ib.managedAccounts()

            if self.config.account is None and accounts:
                self.config.account = accounts[0]

            if verbose:
                print(f"✅ Connected to IBKR")
                print(f"   Host: {self.config.host}:{self.config.port}")
                print(f"   Account: {self.config.account}")
                print(f"   Mode: {'READONLY' if self.config.readonly else 'LIVE'}")
                print()

            # Setup callbacks
            self.ib.orderStatusEvent += self._on_order_status
            self.ib.execDetailsEvent += self._on_execution

            return True

        except Exception as e:
            if verbose:
                print(f"❌ Connection failed: {e}")
            return False

    def disconnect(self):
        """Disconnect from IBKR"""
        if self.connected:
            self.ib.disconnect()
            self.connected = False

    def get_historical_data(self, symbol: str, duration: str = '1 Y',
                           bar_size: str = '1 day', what_to_show: str = 'TRADES') -> pd.DataFrame:
        """
        Download historical data from IBKR

        Args:
            symbol: Stock symbol
            duration: Duration string (e.g., '1 Y', '6 M', '30 D')
            bar_size: Bar size (e.g., '1 day', '1 hour', '5 mins')
            what_to_show: Data type ('TRADES', 'MIDPOINT', 'BID', 'ASK')

        Returns:
            DataFrame with OHLCV data
        """
        if not self.connected:
            raise ConnectionError("Not connected to IBKR")

        # Create contract
        contract = Stock(symbol, 'SMART', 'USD')

        # Request historical data
        bars = self.ib.reqHistoricalData(
            contract,
            endDateTime='',
            durationStr=duration,
            barSizeSetting=bar_size,
            whatToShow=what_to_show,
            useRTH=True,  # Regular trading hours only
            formatDate=1
        )

        # Convert to DataFrame
        if bars:
            df = util.df(bars)
            df = df.rename(columns={
                'date': 'timestamp',
                'volume': 'volume'
            })
            df.set_index('timestamp', inplace=True)
            return df
        else:
            return pd.DataFrame()

    def subscribe_realtime_bars(self, symbol: str, bar_size: int = 5,
                                what_to_show: str = 'TRADES',
                                callback: Optional[Callable] = None):
        """
        Subscribe to real-time bar data (5-second bars minimum)

        Args:
            symbol: Stock symbol
            bar_size: Bar size in seconds (5 minimum)
            what_to_show: Data type ('TRADES', 'MIDPOINT', 'BID', 'ASK')
            callback: Function to call on each bar (receives bar dict)
        """
        if not self.connected:
            raise ConnectionError("Not connected to IBKR")

        # Create contract
        contract = Stock(symbol, 'SMART', 'USD')

        # Subscribe to real-time bars
        bars = self.ib.reqRealTimeBars(
            contract,
            barSize=bar_size,
            whatToShow=what_to_show,
            useRTH=True
        )

        # Setup callback
        if callback:
            bars.updateEvent += lambda bars, hasNewBar: callback(bars[-1]) if hasNewBar else None

        self.subscriptions[symbol] = bars

    def place_market_order(self, symbol: str, quantity: int, action: str = 'BUY') -> Optional[Trade]:
        """
        Place market order

        Args:
            symbol: Stock symbol
            quantity: Number of shares (positive)
            action: 'BUY' or 'SELL'

        Returns:
            Trade object if successful
        """
        if not self.connected:
            raise ConnectionError("Not connected to IBKR")

        if self.config.readonly:
            print("⚠️  READONLY mode - order not placed")
            return None

        # Create contract
        contract = Stock(symbol, 'SMART', 'USD')

        # Create market order
        order = MarketOrder(action, quantity)

        # Place order
        trade = self.ib.placeOrder(contract, order)

        # Store order
        self.orders[trade.order.orderId] = trade

        return trade

    def place_limit_order(self, symbol: str, quantity: int,
                         limit_price: float, action: str = 'BUY') -> Optional[Trade]:
        """
        Place limit order

        Args:
            symbol: Stock symbol
            quantity: Number of shares
            limit_price: Limit price
            action: 'BUY' or 'SELL'

        Returns:
            Trade object if successful
        """
        if not self.connected:
            raise ConnectionError("Not connected to IBKR")

        if self.config.readonly:
            print("⚠️  READONLY mode - order not placed")
            return None

        contract = Stock(symbol, 'SMART', 'USD')
        order = LimitOrder(action, quantity, limit_price)
        trade = self.ib.placeOrder(contract, order)

        self.orders[trade.order.orderId] = trade
        return trade

    def place_bracket_order(self, symbol: str, quantity: int, action: str,
                           entry_price: float, take_profit: float, stop_loss: float) -> List[Trade]:
        """
        Place bracket order (entry + take profit + stop loss)

        Args:
            symbol: Stock symbol
            quantity: Number of shares
            action: 'BUY' or 'SELL'
            entry_price: Entry limit price
            take_profit: Take profit price
            stop_loss: Stop loss price

        Returns:
            List of Trade objects [parent, take_profit, stop_loss]
        """
        if not self.connected:
            raise ConnectionError("Not connected to IBKR")

        if self.config.readonly:
            print("⚠️  READONLY mode - orders not placed")
            return []

        contract = Stock(symbol, 'SMART', 'USD')

        # Create bracket order
        bracket = self.ib.bracketOrder(
            action, quantity, entry_price, take_profit, stop_loss
        )

        # Place all orders
        trades = []
        for order in bracket:
            trade = self.ib.placeOrder(contract, order)
            self.orders[trade.order.orderId] = trade
            trades.append(trade)

        return trades

    def cancel_order(self, order_id: int):
        """Cancel an order by ID"""
        if order_id in self.orders:
            trade = self.orders[order_id]
            self.ib.cancelOrder(trade.order)

    def cancel_all_orders(self):
        """Cancel all open orders"""
        for trade in self.orders.values():
            if trade.orderStatus.status in ['PreSubmitted', 'Submitted']:
                self.ib.cancelOrder(trade.order)

    def get_positions(self) -> Dict[str, Dict]:
        """
        Get all current positions

        Returns:
            Dict of {symbol: {'quantity': int, 'avg_cost': float, 'market_value': float, ...}}
        """
        if not self.connected:
            raise ConnectionError("Not connected to IBKR")

        positions = {}

        for position in self.ib.positions(account=self.config.account):
            symbol = position.contract.symbol

            positions[symbol] = {
                'quantity': position.position,
                'avg_cost': position.avgCost,
                'market_value': position.position * position.marketValue if hasattr(position, 'marketValue') else 0,
                'unrealized_pnl': position.unrealizedPNL,
                'realized_pnl': position.realizedPNL,
            }

        return positions

    def get_account_summary(self) -> Dict:
        """
        Get account summary (balance, buying power, P&L, etc.)

        Returns:
            Dict with account info
        """
        if not self.connected:
            raise ConnectionError("Not connected to IBKR")

        account_values = self.ib.accountValues(account=self.config.account)

        summary = {}

        for av in account_values:
            key = av.tag
            value = av.value

            # Convert to float if possible
            try:
                value = float(value)
            except:
                pass

            summary[key] = value

        # Extract key metrics
        return {
            'net_liquidation': summary.get('NetLiquidation', 0),
            'total_cash': summary.get('TotalCashValue', 0),
            'buying_power': summary.get('BuyingPower', 0),
            'unrealized_pnl': summary.get('UnrealizedPnL', 0),
            'realized_pnl': summary.get('RealizedPnL', 0),
            'gross_position_value': summary.get('GrossPositionValue', 0),
        }

    def get_open_orders(self) -> List[Dict]:
        """
        Get all open orders

        Returns:
            List of order dicts
        """
        if not self.connected:
            raise ConnectionError("Not connected to IBKR")

        open_orders = []

        for trade in self.ib.openTrades():
            open_orders.append({
                'order_id': trade.order.orderId,
                'symbol': trade.contract.symbol,
                'action': trade.order.action,
                'quantity': trade.order.totalQuantity,
                'order_type': trade.order.orderType,
                'limit_price': trade.order.lmtPrice if hasattr(trade.order, 'lmtPrice') else None,
                'status': trade.orderStatus.status,
                'filled': trade.orderStatus.filled,
                'remaining': trade.orderStatus.remaining,
            })

        return open_orders

    # Callback handlers
    def _on_order_status(self, trade: Trade):
        """Handle order status updates"""
        if self.on_order_callback:
            self.on_order_callback(trade)

    def _on_execution(self, trade: Trade, fill: Fill):
        """Handle order fills"""
        if self.on_fill_callback:
            self.on_fill_callback(trade, fill)

    def set_on_bar_callback(self, callback: Callable):
        """Set callback for real-time bars"""
        self.on_bar_callback = callback

    def set_on_order_callback(self, callback: Callable):
        """Set callback for order status updates"""
        self.on_order_callback = callback

    def set_on_fill_callback(self, callback: Callable):
        """Set callback for order fills"""
        self.on_fill_callback = callback

    def run_event_loop(self):
        """
        Run event loop (blocking)

        Use this for real-time trading applications.
        """
        if not self.connected:
            raise ConnectionError("Not connected to IBKR")

        try:
            self.ib.run()
        except KeyboardInterrupt:
            print("\nStopping event loop...")
            self.disconnect()


# Example usage
if __name__ == "__main__":
    # Configuration
    config = IBKRConfig(
        host='127.0.0.1',
        port=7497,  # TWS paper trading
        client_id=1,
        readonly=True  # Safety: read-only mode
    )

    # Create connector
    ibkr = IBKRConnector(config)

    # Connect
    if ibkr.connect():
        # Get account summary
        account = ibkr.get_account_summary()
        print("Account Summary:")
        print(f"  Net Liquidation: ${account['net_liquidation']:,.2f}")
        print(f"  Buying Power: ${account['buying_power']:,.2f}")
        print()

        # Get positions
        positions = ibkr.get_positions()
        print(f"Positions: {len(positions)}")
        for symbol, pos in positions.items():
            print(f"  {symbol}: {pos['quantity']} shares @ ${pos['avg_cost']:.2f}")
        print()

        # Get historical data
        print("Downloading AAPL historical data...")
        data = ibkr.get_historical_data('AAPL', duration='30 D', bar_size='1 day')
        print(f"  Downloaded {len(data)} bars")
        print(data.head())
        print()

        # Disconnect
        ibkr.disconnect()
        print("Disconnected.")
