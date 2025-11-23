"""
Portfolio Tracker - Position and cash management
"""

from typing import Dict, List, Optional
from dataclasses import dataclass
from datetime import datetime


@dataclass
class Trade:
    """Single trade record"""
    timestamp: datetime
    symbol: str
    side: str  # 'BUY' or 'SELL'
    quantity: int
    price: float
    pnl: float = 0.0
    pnl_pct: float = 0.0


@dataclass
class Position:
    """Open position"""
    symbol: str
    entry_time: datetime
    entry_price: float
    quantity: int
    side: str = 'LONG'

    def get_pnl(self, current_price: float) -> float:
        """Calculate unrealized P&L"""
        return (current_price - self.entry_price) * self.quantity

    def get_pnl_pct(self, current_price: float) -> float:
        """Calculate unrealized P&L percentage"""
        return ((current_price - self.entry_price) / self.entry_price) * 100


class Portfolio:
    """
    Tracks cash, positions, and trades
    Clean, simple portfolio manager for backtesting
    """

    def __init__(self, initial_cash: float = 10000.0):
        self.initial_cash = initial_cash
        self.cash = initial_cash
        self.positions: Dict[str, Position] = {}
        self.trades: List[Trade] = []
        self.equity_curve: List[Dict] = []

    def get_equity(self, current_prices: Dict[str, float]) -> float:
        """Calculate total equity (cash + positions)"""
        positions_value = sum(
            pos.quantity * current_prices.get(pos.symbol, pos.entry_price)
            for pos in self.positions.values()
        )
        return self.cash + positions_value

    def get_available_cash(self) -> float:
        """Get available cash for trading"""
        return self.cash

    def has_position(self, symbol: str) -> bool:
        """Check if position exists"""
        return symbol in self.positions

    def open_position(self, symbol: str, price: float, quantity: int, timestamp: datetime):
        """Open a new position"""
        if self.has_position(symbol):
            return False

        cost = price * quantity
        if cost > self.cash:
            return False  # Insufficient funds

        # Deduct cash
        self.cash -= cost

        # Create position
        self.positions[symbol] = Position(
            symbol=symbol,
            entry_time=timestamp,
            entry_price=price,
            quantity=quantity
        )

        # Record trade
        self.trades.append(Trade(
            timestamp=timestamp,
            symbol=symbol,
            side='BUY',
            quantity=quantity,
            price=price
        ))

        return True

    def close_position(self, symbol: str, price: float, timestamp: datetime) -> Optional[Trade]:
        """Close an existing position"""
        if not self.has_position(symbol):
            return None

        pos = self.positions[symbol]

        # Calculate P&L
        proceeds = price * pos.quantity
        self.cash += proceeds

        pnl = pos.get_pnl(price)
        pnl_pct = pos.get_pnl_pct(price)

        # Record trade
        trade = Trade(
            timestamp=timestamp,
            symbol=symbol,
            side='SELL',
            quantity=pos.quantity,
            price=price,
            pnl=pnl,
            pnl_pct=pnl_pct
        )
        self.trades.append(trade)

        # Remove position
        del self.positions[symbol]

        return trade

    def update_equity_curve(self, timestamp: datetime, current_prices: Dict[str, float]):
        """Record equity at this point in time"""
        equity = self.get_equity(current_prices)
        self.equity_curve.append({
            'timestamp': timestamp,
            'equity': equity,
            'cash': self.cash,
            'positions_value': equity - self.cash
        })

    def get_closed_trades(self) -> List[Trade]:
        """Get all closed trades (SELL orders)"""
        return [t for t in self.trades if t.side == 'SELL']

    def get_summary(self) -> Dict:
        """Get portfolio summary"""
        closed_trades = self.get_closed_trades()

        if not closed_trades:
            return {
                'total_trades': 0,
                'winning_trades': 0,
                'losing_trades': 0,
                'total_pnl': 0.0,
                'win_rate': 0.0,
                'avg_win': 0.0,
                'avg_loss': 0.0
            }

        winning = [t for t in closed_trades if t.pnl > 0]
        losing = [t for t in closed_trades if t.pnl <= 0]

        return {
            'total_trades': len(closed_trades),
            'winning_trades': len(winning),
            'losing_trades': len(losing),
            'total_pnl': sum(t.pnl for t in closed_trades),
            'win_rate': len(winning) / len(closed_trades) * 100 if closed_trades else 0,
            'avg_win': sum(t.pnl_pct for t in winning) / len(winning) if winning else 0,
            'avg_loss': sum(t.pnl_pct for t in losing) / len(losing) if losing else 0,
        }
