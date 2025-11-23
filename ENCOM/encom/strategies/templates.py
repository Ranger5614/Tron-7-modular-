"""
Pre-built Strategy Templates for ENCOM

Ready-to-use strategy templates that can be easily customized.

Author: ENCOM Development Team
License: MIT
"""

from encom.strategies.strategy_builder import StrategyBuilder
from encom.indicators import rsi, sma, ema, macd, adx, atr, volume_roc, obv


def create_rsi_strategy(rsi_oversold=30, rsi_overbought=70, rsi_period=14):
    """
    RSI Mean Reversion Strategy
    
    Entry: RSI < oversold
    Exit: RSI > overbought
    
    Args:
        rsi_oversold: RSI oversold level (30)
        rsi_overbought: RSI overbought level (70)
        rsi_period: RSI period (14)
    
    Returns:
        ComposableStrategy
    """
    builder = StrategyBuilder(
        "RSI Mean Reversion",
        f"Buy when RSI < {rsi_oversold}, sell when RSI > {rsi_overbought}"
    )
    
    # Entry: RSI oversold
    def rsi_oversold_signal(data, bar_index):
        rsi_values = rsi(data['close'].values, rsi_period)
        return rsi_values[bar_index] < rsi_oversold
    
    # Exit: RSI overbought
    def rsi_overbought_signal(data, bar_index):
        rsi_values = rsi(data['close'].values, rsi_period)
        return rsi_values[bar_index] > rsi_overbought
    
    builder.add_entry_signal('RSI Oversold', rsi_oversold_signal)
    builder.add_exit_signal('RSI Overbought', rsi_overbought_signal)
    builder.set_position_sizing('percent', percent=0.1)
    
    return builder.build()


def create_ma_crossover_strategy(fast_period=50, slow_period=200):
    """
    Moving Average Crossover Strategy
    
    Entry: Fast MA crosses above Slow MA
    Exit: Fast MA crosses below Slow MA
    
    Args:
        fast_period: Fast MA period (50)
        slow_period: Slow MA period (200)
    
    Returns:
        ComposableStrategy
    """
    builder = StrategyBuilder(
        f"MA Crossover {fast_period}/{slow_period}",
        f"Golden cross ({fast_period} > {slow_period}) entry, death cross exit"
    )
    
    # Track previous cross state
    prev_cross = {'bullish': False}
    
    # Entry: Fast MA crosses above Slow MA
    def ma_cross_up(data, bar_index):
        if bar_index < 1:
            return False
        
        fast_ma = sma(data['close'].values, fast_period)
        slow_ma = sma(data['close'].values, slow_period)
        
        # Current: fast > slow
        # Previous: fast <= slow
        cross_up = (fast_ma[bar_index] > slow_ma[bar_index] and
                   fast_ma[bar_index - 1] <= slow_ma[bar_index - 1])
        
        if cross_up:
            prev_cross['bullish'] = True
        
        return cross_up
    
    # Exit: Fast MA crosses below Slow MA
    def ma_cross_down(data, bar_index):
        if bar_index < 1:
            return False
        
        fast_ma = sma(data['close'].values, fast_period)
        slow_ma = sma(data['close'].values, slow_period)
        
        # Current: fast < slow
        # Previous: fast >= slow
        cross_down = (fast_ma[bar_index] < slow_ma[bar_index] and
                     fast_ma[bar_index - 1] >= slow_ma[bar_index - 1])
        
        if cross_down:
            prev_cross['bullish'] = False
        
        return cross_down
    
    builder.add_entry_signal('MA Cross Up', ma_cross_up)
    builder.add_exit_signal('MA Cross Down', ma_cross_down)
    builder.set_position_sizing('percent', percent=0.15)
    
    return builder.build()


def create_macd_strategy(fast=12, slow=26, signal=9):
    """
    MACD Trend Following Strategy
    
    Entry: MACD crosses above signal line
    Exit: MACD crosses below signal line
    Confirmation: ADX > 25 (strong trend)
    
    Args:
        fast: MACD fast period (12)
        slow: MACD slow period (26)
        signal: MACD signal period (9)
    
    Returns:
        ComposableStrategy
    """
    builder = StrategyBuilder(
        "MACD Trend Following",
        "MACD crossover with ADX trend confirmation"
    )
    
    # Entry: MACD crosses above signal
    def macd_cross_up(data, bar_index):
        if bar_index < 1:
            return False
        
        macd_line, signal_line, _ = macd(data['close'].values, fast, slow, signal)
        
        return (macd_line[bar_index] > signal_line[bar_index] and
                macd_line[bar_index - 1] <= signal_line[bar_index - 1])
    
    # Exit: MACD crosses below signal
    def macd_cross_down(data, bar_index):
        if bar_index < 1:
            return False
        
        macd_line, signal_line, _ = macd(data['close'].values, fast, slow, signal)
        
        return (macd_line[bar_index] < signal_line[bar_index] and
                macd_line[bar_index - 1] >= signal_line[bar_index - 1])
    
    # Confirmation: Strong trend (ADX > 25)
    def strong_trend(data, bar_index):
        from encom.indicators import adx
        adx_values = adx(data['high'].values, data['low'].values, 
                        data['close'].values, 14)
        return adx_values[bar_index] > 25
    
    builder.add_entry_signal('MACD Cross Up', macd_cross_up)
    builder.add_entry_confirmation('Strong Trend', strong_trend)
    builder.add_exit_signal('MACD Cross Down', macd_cross_down)
    builder.set_position_sizing('percent', percent=0.15)
    
    return builder.build()


def create_breakout_strategy(period=20, atr_multiplier=2.0):
    """
    Breakout Strategy with Volume Confirmation
    
    Entry: Price breaks above highest high in period
    Confirmation: Volume > 1.5x average
    Exit: Price drops below SMA or trails by ATR
    
    Args:
        period: Lookback period for high (20)
        atr_multiplier: ATR multiplier for stop loss (2.0)
    
    Returns:
        ComposableStrategy
    """
    builder = StrategyBuilder(
        f"Breakout Strategy ({period} bars)",
        "Breakout above resistance with volume confirmation"
    )
    
    # Track entry price for trailing stop
    entry_state = {'entry_price': None}
    
    # Entry: Breakout above highest high
    def breakout_signal(data, bar_index):
        if bar_index < period:
            return False
        
        # Highest high in period (excluding current bar)
        highest_high = max(data['high'].values[bar_index - period:bar_index])
        
        # Current close breaks above highest high
        return data['close'].values[bar_index] > highest_high
    
    # Confirmation: Volume spike
    def volume_confirmation(data, bar_index):
        if bar_index < 20:
            return False
        
        avg_volume = sum(data['volume'].values[bar_index - 20:bar_index]) / 20
        return data['volume'].values[bar_index] > avg_volume * 1.5
    
    # Exit: Price drops below SMA or ATR trailing stop
    def exit_signal(data, bar_index):
        if entry_state['entry_price'] is None:
            entry_state['entry_price'] = data['close'].values[bar_index]
            return False
        
        # SMA exit
        sma_values = sma(data['close'].values, 20)
        if data['close'].values[bar_index] < sma_values[bar_index]:
            return True
        
        # ATR trailing stop
        atr_values = atr(data['high'].values, data['low'].values, 
                        data['close'].values, 14)
        trailing_stop = entry_state['entry_price'] - (atr_values[bar_index] * atr_multiplier)
        
        if data['close'].values[bar_index] < trailing_stop:
            entry_state['entry_price'] = None
            return True
        
        return False
    
    builder.add_entry_signal('Breakout', breakout_signal)
    builder.add_entry_confirmation('Volume Spike', volume_confirmation)
    builder.add_exit_signal('SMA/ATR Exit', exit_signal)
    builder.set_position_sizing('risk_percent', risk_percent=0.02, stop_loss_pct=0.05)
    
    return builder.build()


def create_momentum_strategy():
    """
    Multi-Indicator Momentum Strategy
    
    Entry conditions (ALL must be true):
    - RSI > 50 (momentum)
    - MACD > 0 (trend)
    - Price > SMA 50 (trend filter)
    - Volume > average (confirmation)
    
    Exit conditions (ANY):
    - RSI < 40
    - MACD < 0
    - Price < SMA 50
    
    Returns:
        ComposableStrategy
    """
    builder = StrategyBuilder(
        "Multi-Indicator Momentum",
        "Combined RSI, MACD, MA, and Volume momentum strategy"
    )
    
    # Entry signals
    def rsi_momentum(data, bar_index):
        rsi_values = rsi(data['close'].values, 14)
        return rsi_values[bar_index] > 50
    
    def macd_positive(data, bar_index):
        macd_line, _, _ = macd(data['close'].values)
        return macd_line[bar_index] > 0
    
    def above_sma(data, bar_index):
        sma_values = sma(data['close'].values, 50)
        return data['close'].values[bar_index] > sma_values[bar_index]
    
    # Volume confirmation
    def volume_above_avg(data, bar_index):
        if bar_index < 20:
            return False
        avg_vol = sum(data['volume'].values[bar_index - 20:bar_index]) / 20
        return data['volume'].values[bar_index] > avg_vol
    
    # Exit signals
    def rsi_weakening(data, bar_index):
        rsi_values = rsi(data['close'].values, 14)
        return rsi_values[bar_index] < 40
    
    def macd_negative(data, bar_index):
        macd_line, _, _ = macd(data['close'].values)
        return macd_line[bar_index] < 0
    
    def below_sma(data, bar_index):
        sma_values = sma(data['close'].values, 50)
        return data['close'].values[bar_index] < sma_values[bar_index]
    
    # Build strategy
    builder.add_entry_signal('RSI Momentum', rsi_momentum)
    builder.add_entry_signal('MACD Positive', macd_positive)
    builder.add_entry_signal('Above SMA 50', above_sma)
    builder.add_entry_confirmation('Volume Above Average', volume_above_avg)
    
    builder.add_exit_signal('RSI Weakening', rsi_weakening, priority=2)
    builder.add_exit_signal('MACD Negative', macd_negative, priority=2)
    builder.add_exit_signal('Below SMA 50', below_sma, priority=3)
    
    builder.set_signal_logic(require_any=False)  # All entry signals must be True
    builder.set_position_sizing('percent', percent=0.15)
    
    return builder.build()
