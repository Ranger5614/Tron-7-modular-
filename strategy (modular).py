# strategy.py - MODULAR STRATEGY INTERFACE
"""
🚀 MODULAR STRATEGY INTERFACE 🚀
This is the chassis - implement these methods in your strategy!
Drop in any strategy engine that follows this interface.
Per Aspera Ad Astra
"""

import numpy as np
import config


class BaseStrategy:
    """
    Base strategy interface that all strategies must implement.
    This is the chassis - your strategies are the engines!
    """
    
    def __init__(self):
        """Initialize your strategy parameters here"""
        # These should be overridden in your strategy
        self.tp_pct = 0.01      # Default 1% TP
        self.sl_pct = 0.007     # Default 0.7% SL
        self.name = "BaseStrategy"
        
    def detect_entry_signal(self, symbol, candles, verbose=False):
        """
        Main entry point for signal detection
        
        Args:
            symbol: Trading pair symbol (e.g., 'BTCUSDT')
            candles: List of OHLCV candles from exchange
                     [[timestamp, open, high, low, close, volume], ...]
            verbose: Enable detailed logging
            
        Returns:
            signal dict with keys:
                - action: "LONG" or "SHORT"
                - symbol: The trading symbol
                - entry_price: Recommended entry price
                - stop_price: Stop loss price
                - target_price: Take profit price
                - quality_score: Signal quality (0-1)
                - entry_type: "STANDARD", "FAST_ENTRY", etc.
                - any other strategy-specific data
            
            OR None if no signal
        """
        raise NotImplementedError("Your strategy must implement detect_entry_signal()")
    
    def check_exit_conditions(self, position, current_price, bars_held):
        """
        Check if position should be exited
        
        Args:
            position: Dict with position data including:
                - symbol, direction, entry_price, stop_price, target_price, etc.
            current_price: Current market price
            bars_held: Number of bars/candles held
            
        Returns:
            exit_signal dict with keys:
                - exit_type: "TAKE_PROFIT", "STOP_LOSS", "TIME_EXIT", etc.
                - reason: Human readable reason
            
            OR None if no exit
        """
        raise NotImplementedError("Your strategy must implement check_exit_conditions()")
    
    def filter_correlated_signals(self, signals):
        """
        Filter multiple signals to avoid correlation
        
        Args:
            signals: List of signal dicts
            
        Returns:
            Filtered list of signals
        """
        # Default implementation - sort by quality
        if len(signals) <= config.MAX_TOTAL_POSITIONS:
            return signals
            
        return sorted(signals, 
                     key=lambda x: x.get("quality_score", 0), 
                     reverse=True)[:config.MAX_TOTAL_POSITIONS]
    
    def calculate_position_size(self, symbol, account_balance):
        """
        Calculate position size for a symbol
        
        Args:
            symbol: Trading pair
            account_balance: Current account balance
            
        Returns:
            Dict with position sizing info:
                - position_size_usd: Position size in USD
                - risk_usd: Risk amount in USD  
                - risk_pct: Risk as percentage of account
                - leverage: Leverage to use
                - margin_required: Margin needed
                
            OR None if position cannot be taken
        """
        # Default implementation
        position_size_usd = config.FIXED_POSITION_SIZE_USD
        risk_usd = position_size_usd * self.sl_pct
        risk_pct = (risk_usd / account_balance) * 100
        
        # Check if we have enough balance
        if config.ENABLE_FUTURES:
            margin_required = position_size_usd / config.LEVERAGE
            if margin_required > account_balance * 0.95:
                return None
        else:
            if position_size_usd > account_balance * 0.95:
                return None
        
        return {
            "position_size_usd": position_size_usd,
            "risk_usd": risk_usd,
            "risk_pct": risk_pct,
            "leverage": config.LEVERAGE if config.ENABLE_FUTURES else 1,
            "margin_required": position_size_usd / config.LEVERAGE if config.ENABLE_FUTURES else position_size_usd
        }
    
    def check_live_price_entry(self, symbol, live_bid, live_ask):
        """
        OPTIONAL: Check for live price entries (advanced feature)
        
        Args:
            symbol: Trading pair
            live_bid: Current bid price
            live_ask: Current ask price
            
        Returns:
            signal dict or None
        """
        # Default: No live price checking
        return None
    
    def get_market_overview(self):
        """
        Get strategy overview and current market view
        
        Returns:
            Dict with strategy info and market overview
        """
        return {
            "strategy_name": self.name,
            "strategy_type": self.__class__.__name__,
            "tp_pct": self.tp_pct * 100,
            "sl_pct": self.sl_pct * 100,
            "active_pairs": sum(1 for p in config.PAIR_CONFIGS.values() if p.get("active")),
            "market_mode": "FUTURES" if config.ENABLE_FUTURES else "SPOT"
        }


class ExampleMACrossStrategy(BaseStrategy):
    """
    Example implementation - Simple MA Crossover Strategy
    This shows how to implement the interface
    """
    
    def __init__(self):
        super().__init__()
        self.name = "MA Crossover Example"
        self.fast_ma_period = 10
        self.slow_ma_period = 30
        self.tp_pct = 0.01    # 1% TP
        self.sl_pct = 0.007   # 0.7% SL
        
    def detect_entry_signal(self, symbol, candles, verbose=False):
        """Simple MA crossover signal detection"""
        if len(candles) < self.slow_ma_period:
            return None
            
        # Convert to numpy arrays
        closes = np.array([float(c[4]) for c in candles])
        
        # Calculate MAs
        fast_ma = np.mean(closes[-self.fast_ma_period:])
        slow_ma = np.mean(closes[-self.slow_ma_period:])
        
        # Previous MAs for crossover detection
        prev_closes = closes[:-1]
        prev_fast_ma = np.mean(prev_closes[-self.fast_ma_period:])
        prev_slow_ma = np.mean(prev_closes[-self.slow_ma_period:])
        
        current_price = closes[-1]
        
        # Check for crossover
        if prev_fast_ma <= prev_slow_ma and fast_ma > slow_ma:
            # Bullish crossover
            return {
                "action": "LONG",
                "symbol": symbol,
                "entry_price": current_price,
                "stop_price": current_price * (1 - self.sl_pct),
                "target_price": current_price * (1 + self.tp_pct),
                "quality_score": 0.7,  # Fixed quality for example
                "entry_type": "STANDARD"
            }
        elif prev_fast_ma >= prev_slow_ma and fast_ma < slow_ma and not config.LONG_ONLY_MODE:
            # Bearish crossover
            return {
                "action": "SHORT",
                "symbol": symbol,
                "entry_price": current_price,
                "stop_price": current_price * (1 + self.sl_pct),
                "target_price": current_price * (1 - self.tp_pct),
                "quality_score": 0.7,
                "entry_type": "STANDARD"
            }
            
        return None
    
    def check_exit_conditions(self, position, current_price, bars_held):
        """Check for exit - just TP/SL for this example"""
        direction = position.get("direction")
        stop_price = position.get("stop_price")
        target_price = position.get("target_price")
        
        if direction == "LONG":
            if current_price <= stop_price:
                return {"exit_type": "STOP_LOSS", "reason": "Stop loss hit"}
            elif current_price >= target_price:
                return {"exit_type": "TAKE_PROFIT", "reason": "Take profit reached"}
        else:  # SHORT
            if current_price >= stop_price:
                return {"exit_type": "STOP_LOSS", "reason": "Stop loss hit"}
            elif current_price <= target_price:
                return {"exit_type": "TAKE_PROFIT", "reason": "Take profit reached"}
                
        # Time stop after 20 bars
        if bars_held >= 20:
            return {"exit_type": "TIME_EXIT", "reason": "Max hold time reached"}
            
        return None


# This allows importing specific strategies
print("🚀 Modular Strategy Interface Loaded!")
print("📦 Available strategies:")
print("   - BaseStrategy (interface)")
print("   - ExampleMACrossStrategy (example)")
print("🎯 To use your own strategy:")
print("   1. Import this file")
print("   2. Create a class that inherits from BaseStrategy")
print("   3. Implement all required methods")
print("   4. Set STRATEGY_CLASS in config.py")