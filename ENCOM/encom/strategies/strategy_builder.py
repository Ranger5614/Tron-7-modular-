"""
Modular Strategy Builder for ENCOM

Drag-and-drop style strategy composition (via code).
Build complex strategies by combining signals, confirmations, and filters.

Author: ENCOM Development Team
License: MIT
"""

from typing import List, Dict, Optional, Callable
from dataclasses import dataclass
import numpy as np


@dataclass
class StrategyComponent:
    """Base class for strategy components"""
    name: str
    description: str
    enabled: bool = True


class StrategyBuilder:
    """
    Modular strategy builder
    
    Build strategies by composing:
    - Entry signals
    - Entry confirmations
    - Entry filters
    - Exit signals
    - Exit confirmations
    - Position sizing rules
    - Risk management rules
    
    Example:
        builder = StrategyBuilder("My Custom Strategy")
        builder.add_entry_signal('RSI', rsi_oversold)
        builder.add_confirmation('Volume', volume_above_average)
        builder.add_exit_signal('RSI', rsi_overbought)
        builder.set_position_size('risk_percent', 0.02)
        
        strategy = builder.build()
    """
    
    def __init__(self, name: str, description: str = ""):
        """
        Args:
            name: Strategy name
            description: Strategy description
        """
        self.name = name
        self.description = description
        
        # Strategy components
        self.entry_signals = []
        self.entry_confirmations = []
        self.entry_filters = []
        self.exit_signals = []
        self.exit_confirmations = []
        self.exit_filters = []
        
        # Rules
        self.position_sizing_rule = None
        self.risk_management_rules = []
        
        # Settings
        self.require_all_confirmations = True
        self.require_any_signal = False  # True = OR logic, False = AND logic
        
    def add_entry_signal(self, name: str, signal_func: Callable, 
                        direction: str = 'long', weight: float = 1.0):
        """
        Add entry signal
        
        Args:
            name: Signal name
            signal_func: Function that returns True/False or strength (0-1)
            direction: 'long' or 'short'
            weight: Signal weight (default 1.0)
        """
        self.entry_signals.append({
            'name': name,
            'func': signal_func,
            'direction': direction,
            'weight': weight,
            'enabled': True
        })
        return self
    
    def add_entry_confirmation(self, name: str, confirmation_func: Callable,
                              required: bool = True):
        """
        Add entry confirmation
        
        Args:
            name: Confirmation name
            confirmation_func: Function that returns True/False
            required: Must be True for entry (default True)
        """
        self.entry_confirmations.append({
            'name': name,
            'func': confirmation_func,
            'required': required,
            'enabled': True
        })
        return self
    
    def add_entry_filter(self, name: str, filter_func: Callable):
        """
        Add entry filter (blocks entry if False)
        
        Args:
            name: Filter name
            filter_func: Function that returns True/False
        """
        self.entry_filters.append({
            'name': name,
            'func': filter_func,
            'enabled': True
        })
        return self
    
    def add_exit_signal(self, name: str, signal_func: Callable,
                       priority: int = 1):
        """
        Add exit signal
        
        Args:
            name: Signal name
            signal_func: Function that returns True/False
            priority: Exit priority (higher = more important)
        """
        self.exit_signals.append({
            'name': name,
            'func': signal_func,
            'priority': priority,
            'enabled': True
        })
        return self
    
    def set_position_sizing(self, method: str, **kwargs):
        """
        Set position sizing method
        
        Args:
            method: 'fixed', 'risk_percent', 'kelly', 'volatility'
            **kwargs: Method-specific parameters
        """
        self.position_sizing_rule = {
            'method': method,
            'params': kwargs
        }
        return self
    
    def add_risk_rule(self, name: str, rule_func: Callable):
        """
        Add risk management rule
        
        Args:
            name: Rule name
            rule_func: Function that modifies position or blocks trade
        """
        self.risk_management_rules.append({
            'name': name,
            'func': rule_func,
            'enabled': True
        })
        return self
    
    def set_confirmation_logic(self, require_all: bool = True):
        """
        Set confirmation logic
        
        Args:
            require_all: True = AND logic (all must pass), False = OR logic (any can pass)
        """
        self.require_all_confirmations = require_all
        return self
    
    def set_signal_logic(self, require_any: bool = False):
        """
        Set signal logic
        
        Args:
            require_any: True = OR logic (any signal), False = AND logic (all signals)
        """
        self.require_any_signal = require_any
        return self
    
    def build(self):
        """
        Build the strategy
        
        Returns:
            Configured Strategy object
        """
        strategy = ComposableStrategy(
            name=self.name,
            description=self.description,
            entry_signals=self.entry_signals,
            entry_confirmations=self.entry_confirmations,
            entry_filters=self.entry_filters,
            exit_signals=self.exit_signals,
            exit_confirmations=self.exit_confirmations,
            exit_filters=self.exit_filters,
            position_sizing_rule=self.position_sizing_rule,
            risk_management_rules=self.risk_management_rules,
            require_all_confirmations=self.require_all_confirmations,
            require_any_signal=self.require_any_signal
        )
        
        return strategy
    
    def save_config(self, filepath: str):
        """Save strategy configuration to file"""
        import json
        
        config = {
            'name': self.name,
            'description': self.description,
            'entry_signals': [{'name': s['name'], 'direction': s['direction'], 'weight': s['weight']} 
                            for s in self.entry_signals],
            'entry_confirmations': [{'name': c['name'], 'required': c['required']} 
                                  for c in self.entry_confirmations],
            'entry_filters': [{'name': f['name']} for f in self.entry_filters],
            'exit_signals': [{'name': s['name'], 'priority': s['priority']} 
                           for s in self.exit_signals],
            'position_sizing': self.position_sizing_rule,
            'risk_rules': [{'name': r['name']} for r in self.risk_management_rules],
            'settings': {
                'require_all_confirmations': self.require_all_confirmations,
                'require_any_signal': self.require_any_signal
            }
        }
        
        with open(filepath, 'w') as f:
            json.dump(config, f, indent=2)
        
        print(f"✅ Strategy configuration saved to: {filepath}")
        return self


class ComposableStrategy:
    """
    Composable strategy built from modular components
    
    Used by BacktestRunner like any other strategy.
    """
    
    def __init__(self, name: str, description: str,
                 entry_signals: List[Dict],
                 entry_confirmations: List[Dict],
                 entry_filters: List[Dict],
                 exit_signals: List[Dict],
                 exit_confirmations: List[Dict],
                 exit_filters: List[Dict],
                 position_sizing_rule: Optional[Dict],
                 risk_management_rules: List[Dict],
                 require_all_confirmations: bool,
                 require_any_signal: bool):
        """Initialize composable strategy"""
        self.name = name
        self.description = description
        
        self.entry_signals = entry_signals
        self.entry_confirmations = entry_confirmations
        self.entry_filters = entry_filters
        self.exit_signals = exit_signals
        self.exit_confirmations = exit_confirmations
        self.exit_filters = exit_filters
        
        self.position_sizing_rule = position_sizing_rule
        self.risk_management_rules = risk_management_rules
        
        self.require_all_confirmations = require_all_confirmations
        self.require_any_signal = require_any_signal
        
        # State
        self.position = None
        self.data = None
        self.bar_index = 0
    
    def on_data(self, data, bar_index):
        """Called for each bar"""
        self.data = data
        self.bar_index = bar_index
        
        # Check for exit first (if in position)
        if self.position is not None:
            if self._should_exit(bar_index):
                return 'EXIT'
        
        # Check for entry (if not in position)
        if self.position is None:
            if self._should_enter(bar_index):
                return 'ENTER'
        
        return 'HOLD'
    
    def _should_enter(self, bar_index: int) -> bool:
        """Check if should enter position"""
        # 1. Check filters (any False blocks entry)
        for filter_item in self.entry_filters:
            if not filter_item['enabled']:
                continue
            
            try:
                if not filter_item['func'](self.data, bar_index):
                    return False
            except Exception as e:
                print(f"Filter '{filter_item['name']}' error: {e}")
                return False
        
        # 2. Check signals
        signal_results = []
        for signal in self.entry_signals:
            if not signal['enabled']:
                continue
            
            try:
                result = signal['func'](self.data, bar_index)
                signal_results.append(result)
            except Exception as e:
                print(f"Signal '{signal['name']}' error: {e}")
                signal_results.append(False)
        
        # Apply signal logic
        if self.require_any_signal:
            if not any(signal_results):
                return False
        else:
            if not all(signal_results):
                return False
        
        # 3. Check confirmations
        confirmation_results = []
        for confirmation in self.entry_confirmations:
            if not confirmation['enabled']:
                continue
            
            try:
                result = confirmation['func'](self.data, bar_index)
                confirmation_results.append(result)
            except Exception as e:
                print(f"Confirmation '{confirmation['name']}' error: {e}")
                if confirmation['required']:
                    return False
        
        # Apply confirmation logic
        if self.require_all_confirmations:
            if not all(confirmation_results):
                return False
        else:
            if not any(confirmation_results):
                return False
        
        return True
    
    def _should_exit(self, bar_index: int) -> bool:
        """Check if should exit position"""
        # Check exit signals (sorted by priority)
        sorted_exits = sorted(self.exit_signals, 
                            key=lambda x: x['priority'], 
                            reverse=True)
        
        for signal in sorted_exits:
            if not signal['enabled']:
                continue
            
            try:
                if signal['func'](self.data, bar_index):
                    return True
            except Exception as e:
                print(f"Exit signal '{signal['name']}' error: {e}")
        
        return False
    
    def get_position_size(self, price: float, account_value: float) -> int:
        """Calculate position size"""
        if self.position_sizing_rule is None:
            # Default: 10% of account
            return int((account_value * 0.1) / price)
        
        method = self.position_sizing_rule['method']
        params = self.position_sizing_rule['params']
        
        if method == 'fixed':
            return params.get('shares', 100)
        
        elif method == 'risk_percent':
            risk_pct = params.get('risk_percent', 0.02)
            risk_amount = account_value * risk_pct
            
            stop_loss_pct = params.get('stop_loss_pct', 0.05)
            risk_per_share = price * stop_loss_pct
            
            if risk_per_share > 0:
                return int(risk_amount / risk_per_share)
            else:
                return 0
        
        elif method == 'percent':
            pct = params.get('percent', 0.1)
            return int((account_value * pct) / price)
        
        else:
            return 0
    
    def __str__(self):
        """String representation"""
        return f"ComposableStrategy('{self.name}', {len(self.entry_signals)} signals, {len(self.entry_confirmations)} confirmations)"
