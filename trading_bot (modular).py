# trading_bot.py - MODULAR ORCHESTRATOR VERSION
"""
🚀 HYPERION MODULAR TRADING BOT - ORCHESTRATOR 🚀
Strategy-agnostic orchestration layer with enhanced safety
OCO orders, retry logic, and exchange-first design
Per Aspera Ad Astra
"""

import time
import sys
import signal
import os
import traceback
from datetime import datetime, date, timedelta, timezone
import threading
import json
import importlib

# Import core modules (strategy-agnostic)
import config
from portfolio import Portfolio, PositionState
from market import Market
from notifier import QuantumDimensionalPortal


class HyperionAdvancedLogger:
    """Placeholder for advanced logger if not available"""
    def __init__(self):
        pass
    
    def log_error(self, category, message, context=None):
        print(f"🚨 [{category}] {message}")
    
    def log_signal_detected(self, signal_data):
        pass
    
    def log_scan_performance(self, scan_number, duration_seconds, pairs_scanned, signals_found):
        pass
    
    def log_account_snapshot(self, account_data, positions_data):
        pass
    
    def log_order_attempt(self, symbol, side, quantity, price, order_type="MARKET"):
        return time.time()
    
    def log_order_result(self, symbol, order_response, start_time, success=True):
        pass
    
    def log_position_entry(self, position_data):
        pass
    
    def log_position_exit(self, exit_data):
        pass
    
    def log_position_update(self, symbol, position_data, current_price):
        pass
    
    def get_session_metrics(self):
        return {}
    
    def export_session_report(self):
        print("📊 Session report exported")


class HyperionModularTradingBot:
    def __init__(self):
        """🛸 Initialize the Modular Trading Command Center"""
        self.running = False
        self.bot_start_time = datetime.now(timezone.utc)  # CHANGED from datetime.now(timezone.utc)
        self.last_error = None
        self.consecutive_errors = 0
        self.max_consecutive_errors = 5
        
        # Timing trackers - OPTIMIZED FOR SPEED
        self.last_signal_scan = 0
        self.last_position_monitor = 0
        self.last_heartbeat = 0
        self.last_reconciliation = 0
        self.last_order_check = 0
        self.last_emergency_check = 0
        self.last_exit_order_check = 0
        self.last_position_sync = 0
        self.last_oco_check = 0
        
        # Stats tracking
        self.signals_detected_today = 0
        self.trades_executed_today = 0
        self.scan_count = 0
        
        # Thread safety for critical operations
        self.order_lock = threading.Lock()
        self.position_operation_lock = threading.Lock()
        
        # Circuit breaker safe polling
        self.poll_intervals = {
            'exit_orders': 2,      # 2 seconds for exit order monitoring
            'positions': 10,       # 10 seconds for position monitoring
            'reconciliation': 30,  # 30 seconds for reconciliation
            'heartbeat': config.HEARTBEAT_INTERVAL  # Use config value (10 minutes)
        }
        self.last_poll_times = {}
        self.poll_lock = threading.Lock()
        
        
         # Stats tracking
        self.signals_detected_today = 0
        self.trades_executed_today = 0
        self.scan_count = 0
        
        # Emergency tracking to prevent multiple triggers
        self.emergency_triggered_positions = set()
        
        # Performance tracking for fills
        self.fill_performance = {
            'attempted': 0,
            'filled': 0,
            'cancelled': 0,
            'avg_fill_time': 0
        }

        # Atomic position counter for race condition prevention
        self.position_counter_lock = threading.Lock()
        self.committed_positions = set()  # Track symbols with positions or pending orders
        
        # Performance tracking for fills
        self.fill_performance = {
            'attempted': 0,
            'filled': 0,
            'cancelled': 0,
            'avg_fill_time': 0
        }
        
        self.entry_performance = {}  # Track performance by entry type
        # FIX: Add retry tracking for emergency closes
        self.emergency_close_retries = {}  # Track retries per symbol
        self.max_emergency_retries = 3

        # Initialize components
        try:
            self.notifier = QuantumDimensionalPortal()
            self.market = Market()
            self.portfolio = Portfolio()
            
            # MODULAR: Dynamic strategy loading
            self._load_strategy()
            
            # Clean up any orphaned orders from previous sessions
            self.notifier.quantum_log("🧹 Cleaning up orphaned orders...", "INFO")
            self.market.cleanup_orphaned_orders()
            
            # Try to import advanced logger
            try:
                from advanced_logger import HyperionAdvancedLogger
                self.logger = HyperionAdvancedLogger()
                self.notifier.quantum_log("✅ Advanced logger initialized", "INFO")
            except ImportError:
                self.logger = HyperionAdvancedLogger()  # Use placeholder
                self.notifier.quantum_log("⚠️ Advanced logger not found, using basic logging", "WARNING")
            
            self._log_startup()
            
            # Verify connection
            self.notifier.quantum_log("🔌 Testing connection to exchange...", "INFO")
            if not self.market.test_connection():
                raise Exception("Failed to connect to exchange")
            self.notifier.quantum_log("✅ Connection established", "SUCCESS")
            
            # Initialize market settings
            if config.ENABLE_FUTURES:
                self.notifier.quantum_log("⚡ Initializing futures settings...", "INFO")
                self._initialize_futures_settings()
            
            # Load portfolio state and sync with exchange
            self.notifier.quantum_log("📂 Loading portfolio state...", "INFO")
            self.portfolio.load_positions()
            
            # Update account info
            self._update_account_balance()
            
            # Force initial sync with exchange
            self.notifier.quantum_log("🔄 Initial sync with exchange...", "INFO")
            self.portfolio.sync_with_exchange(self.market)
            exchange_positions = self.portfolio.get_positions_from_exchange(self.market)
            self.notifier.quantum_log(f"✅ Found {len(exchange_positions)} active positions on exchange", "SUCCESS")
            
            # Initial reconciliation
            self.portfolio.reconcile_with_exchange(self.market, self.notifier)
            
            self.notifier.quantum_log("✅ Bot initialization complete!", "SUCCESS")
            self.notifier.quantum_log(f"🚀 Ready to trade with ${self.portfolio.balance_usd:.2f}", "INFO")
            
        except Exception as e:
            error_msg = f"❌ Initialization failed: {str(e)}"
            print(error_msg)
            if hasattr(self, 'notifier'):
                self.notifier.quantum_log(error_msg, "ERROR")
            raise

    def _load_strategy(self):
        """MODULAR: Dynamically load strategy class from config"""
        try:
            # Get strategy class name from config
            strategy_class_name = getattr(config, 'STRATEGY_CLASS', 'QuantumLegacyV73Strategy')
            
            self.notifier.quantum_log(f"📦 Loading strategy: {strategy_class_name}", "INFO")
            
            # Import strategy module
            strategy_module = importlib.import_module('strategy')
            
            # Get strategy class
            strategy_class = getattr(strategy_module, strategy_class_name)
            
            # Instantiate strategy
            self.strategy = strategy_class()
            
            self.notifier.quantum_log(f"✅ Strategy loaded: {strategy_class_name}", "SUCCESS")
            
            # Log strategy configuration
            if hasattr(self.strategy, 'get_market_overview'):
                overview = self.strategy.get_market_overview()
                self.notifier.quantum_log(f"📊 Strategy: {overview.get('strategy_name', 'Unknown')}", "INFO")
                if config.ENABLE_REGIME_SWITCHING:
                    self.notifier.quantum_log(f"🔄 Regime: {overview.get('current_regime', 'UNKNOWN')}", "INFO")
            
        except AttributeError as e:
            # Strategy class not found in module
            self.notifier.quantum_log(f"⚠️ Strategy class '{strategy_class_name}' not found in strategy.py", "ERROR")
            self.notifier.quantum_log(f"Error details: {str(e)}", "ERROR")
            
            # Try to use QuantumLegacyV73Strategy as fallback
            try:
                self.notifier.quantum_log("📦 Attempting to load QuantumLegacyV73Strategy as fallback", "INFO")
                from strategy import QuantumLegacyV73Strategy
                self.strategy = QuantumLegacyV73Strategy()
                self.notifier.quantum_log("✅ Fallback strategy loaded: QuantumLegacyV73Strategy", "SUCCESS")
            except ImportError as ie:
                self.notifier.quantum_log(f"❌ CRITICAL: Cannot load any strategy!", "ERROR")
                self.notifier.quantum_log(f"Import error: {str(ie)}", "ERROR")
                
                # Last resort - try to use BaseStrategy (will fail on detect_entry_signal)
                from strategy import BaseStrategy
                self.strategy = BaseStrategy()
                self.notifier.quantum_log("⚠️ WARNING: Using BaseStrategy - THIS WILL NOT WORK FOR TRADING!", "WARNING")
                
        except ImportError as e:
            # Strategy module cannot be imported
            self.notifier.quantum_log(f"❌ Cannot import strategy module: {str(e)}", "ERROR")
            
            # Check if strategy.py exists
            import os
            if not os.path.exists('strategy.py'):
                self.notifier.quantum_log("❌ strategy.py file not found!", "ERROR")
                raise FileNotFoundError("strategy.py not found - cannot run bot without strategy file")
            else:
                self.notifier.quantum_log("📁 strategy.py exists but has import errors", "ERROR")
                
                # Try to provide more diagnostic info
                import traceback
                self.notifier.quantum_log("📋 Full error trace:", "ERROR")
                traceback.print_exc()
                raise
                
        except Exception as e:
            # Any other error
            self.notifier.quantum_log(f"❌ Unexpected error loading strategy: {str(e)}", "ERROR")
            import traceback
            traceback.print_exc()
            
            # Try fallback
            try:
                self.notifier.quantum_log("📦 Attempting emergency fallback to QuantumLegacyV73Strategy", "WARNING")
                from strategy import QuantumLegacyV73Strategy
                self.strategy = QuantumLegacyV73Strategy()
                self.notifier.quantum_log("✅ Emergency fallback successful", "SUCCESS")
            except:
                self.notifier.quantum_log("❌ FATAL: No strategy could be loaded", "ERROR")
                raise RuntimeError("Cannot load any trading strategy - aborting")

    def circuit_breaker_safe_poll(self, poll_type, poll_function, *args, **kwargs):
        """🔌 Poll wrapper that guarantees minimum cadence even during breaker cooldowns"""
        with self.poll_lock:
            current_time = time.time()
            last_poll = self.last_poll_times.get(poll_type, 0)
            min_interval = self.poll_intervals.get(poll_type, 30)  # Default 30s
            
            # Check if enough time has passed
            if current_time - last_poll < min_interval:
                return False  # Not time to poll yet
            
            # Update last poll time
            self.last_poll_times[poll_type] = current_time
            
            try:
                # Execute the poll function
                result = poll_function(*args, **kwargs)
                return result
            except Exception as e:
                self.notifier.quantum_log(f"🚨 Poll error in {poll_type}: {str(e)}", "ERROR")
                # Don't reset last_poll_time on error - maintain minimum cadence
                return False

    def _log_startup(self):
        """Log startup information"""
        strategy_name = self.strategy.__class__.__name__
        self.notifier.quantum_log(f"🚀 Initializing Hyperion Modular Trading Bot...", "INFO")
        self.notifier.quantum_log(f"🎯 Strategy: {strategy_name}", "INFO")
        self.notifier.quantum_log(f"📈 Market: {'FUTURES' if config.ENABLE_FUTURES else 'SPOT'}", "INFO")
        self.notifier.quantum_log(f"💰 Position Size: ${config.FIXED_POSITION_SIZE_USD}", "INFO")
        self.notifier.quantum_log(f"⚡ Max Positions: {config.MAX_TOTAL_POSITIONS}", "INFO")
        self.notifier.quantum_log(f"🔄 OCO Orders: {'ENABLED' if config.USE_OCO_ORDERS else 'DISABLED'}", "INFO")
        
        active_pairs = [s for s, c in config.PAIR_CONFIGS.items() if c.get("active", False)]
        self.notifier.quantum_log(f"🌌 Active pairs: {', '.join(active_pairs)}", "INFO")
        
    def _setup_dead_mans_switch(self):
        """Setup dead man's switch for position protection"""
        try:
            # Create dead man's switch file
            switch_file = f"{config.DATA_DIR}/dead_mans_switch.json"
            switch_data = {
                "bot_id": self.session_id,
                "start_time": self.bot_start_time.isoformat(),
                "emergency_close_after_seconds": 300,  # 5 minutes
                "positions_to_close": [],
                "enabled": True
            }
            
            with open(switch_file, 'w') as f:
                json.dump(switch_data, f, indent=2)
            
            print("🔒 Dead man's switch activated - positions protected")
            
        except Exception as e:
            print(f"⚠️ Could not setup dead man's switch: {str(e)}")

    def _initialize_futures_settings(self):
        """Initialize futures-specific settings"""
        try:
            self.market.set_position_mode(hedge_mode=False)
            
            active_pairs = [s for s, c in config.PAIR_CONFIGS.items() if c.get("active", False)]
            for symbol in active_pairs:
                self.market.set_leverage(symbol, config.LEVERAGE)
                if config.ISOLATED_MARGIN:
                    self.market.set_margin_type(symbol, "ISOLATED")
                    
            self.notifier.quantum_log(f"✅ Futures initialized - Leverage: {config.LEVERAGE}x", "SUCCESS")
        except Exception as e:
            self.notifier.quantum_log(f"⚠️ Futures init warning: {str(e)}", "WARNING")

    def _update_account_balance(self):
        """Update account balance"""
        self.notifier.quantum_log("💰 Updating account balance...", "INFO")
        try:
            balance = self.market.get_total_balance_usd()
            if balance is not None and balance > 0:
                self.portfolio.update_balance_usd(balance)
                self.notifier.quantum_log(f"✅ Balance updated: ${self.portfolio.balance_usd:.2f}", "SUCCESS")
            else:
                self.notifier.quantum_log("⚠️ Balance update failed or is zero. Using cached value.", "WARNING")
        except Exception as e:
            self.notifier.quantum_log(f"⚠️ Balance update exception: {str(e)}", "WARNING")

    def run(self):
        """🌌 Main Trading Loop - INSTITUTIONAL SPEED WITH MEMORY MANAGEMENT"""
        self.running = True
        
        # Set up signal handlers
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
        
        # Send startup notification
        self.notifier.send_startup_message(self.portfolio.balance_usd)
        
        # Initialize timing for new features
        self.last_memory_cleanup = 0
        self.last_heartbeat_file = 0
        self.last_stale_cleanup = 0
        
        self.notifier.quantum_log("🚀 Starting initial scan...", "INFO")
        try:
            self._scan_for_signals()
        except Exception as e:
            self.notifier.quantum_log(f"❌ Initial scan failed: {str(e)}", "ERROR")
        
        self._send_heartbeat()
        self._update_heartbeat_file()  # Initial heartbeat file
        
        self.notifier.quantum_log(f"⏰ Starting main loop - Scan interval: {config.MAIN_LOOP_INTERVAL}s", "INFO")
        
        while self.running:
            try:
                cycle_start = time.time()
                
                # Update heartbeat file (every 10 seconds)
                if self._should_run(self.last_heartbeat_file, 10):
                    self._update_heartbeat_file()
                    self.last_heartbeat_file = time.time()
                
                # CRITICAL: Fast exit order monitoring (every 2 seconds) - with circuit breaker safe polling
                if self.circuit_breaker_safe_poll('exit_orders', self._monitor_exit_orders_fast):
                    pass  # Function executed successfully
                
                # Order monitoring (every 2 seconds for fast fills)
                if self._should_run(self.last_order_check, 2):
                    self._monitor_and_process_orders()
                    self.last_order_check = time.time()
                
                # Position sync with exchange (every 30s - ALIGNED WITH RECONCILIATION)
                if self._should_run(self.last_position_sync, 30):
                    # Sync first
                    if self.portfolio.sync_with_exchange(self.market):
                        self.last_position_sync = time.time()
                        
                        # Then reconcile immediately after sync
                        if self._should_run(self.last_reconciliation, 30):
                            self.portfolio.reconcile_with_exchange(self.market, self.notifier)
                            self.last_reconciliation = time.time()
                    else:
                        self.notifier.quantum_log("⚠️ Position sync failed - skipping reconciliation", "WARNING")
                
                # Signal scanning
                if self._should_run(self.last_signal_scan, config.MAIN_LOOP_INTERVAL):
                    self._scan_for_signals()
                    self.last_signal_scan = time.time()
                
                # Position monitoring - with circuit breaker safe polling
                if self.circuit_breaker_safe_poll('positions', self._monitor_positions):
                    pass  # Function executed successfully
                
                # Reconciliation (every 30s - ALIGNED WITH POSITION SYNC) - with circuit breaker safe polling
                if self.circuit_breaker_safe_poll('reconciliation', self.portfolio.reconcile_with_exchange, self.market, self.notifier):
                    pass  # Function executed successfully
                
                # Memory cleanup (every hour)
                if self._should_run(self.last_memory_cleanup, 3600):
                    self._cleanup_old_data()
                    self.last_memory_cleanup = time.time()
                
                # Stale entry cleanup (every 5 minutes)
                if self._should_run(self.last_stale_cleanup, 300):
                    self._cleanup_stale_entries()
                    self.last_stale_cleanup = time.time()
                
                # Emergency checks (every 15s)
                if self._should_run(self.last_emergency_check, 15):
                    if not self._emergency_checks():
                        self.notifier.send_critical_alert(
                            "🚨 Emergency stop triggered - shutting down",
                            "CRITICAL"
                        )
                        break
                    self._emergency_position_check()
                    
                    # FIX: Retry failed emergency closes
                    if self.emergency_close_retries:
                        self._retry_failed_emergency_closes()
                    
                    self.last_emergency_check = time.time()
                
                # Heartbeat - with circuit breaker safe polling
                if self.circuit_breaker_safe_poll('heartbeat', self._send_heartbeat):
                    pass  # Function executed successfully
                
                # Sleep for remainder
                self._cycle_sleep(cycle_start)
                self.consecutive_errors = 0
                
            except KeyboardInterrupt:
                self.notifier.quantum_log("⌨️ Keyboard interrupt received", "INFO")
                self.shutdown()
                break
            except Exception as e:
                self._handle_error(e)
                
                if self.consecutive_errors >= self.max_consecutive_errors:
                    self.notifier.send_critical_alert(
                        f"🚨 Too many consecutive errors ({self.consecutive_errors}). Shutting down.",
                        "CRITICAL"
                    )
                    self._emergency_close_all_positions()
                    self.shutdown()
                    break

    def _scan_for_signals(self):
        """🎯 MODULAR: Scan for trading signals using strategy."""
        try:
            self.scan_count += 1
            
            # Get strategy info for display
            strategy_name = self.strategy.__class__.__name__
            self.notifier.quantum_log(f"🔍 Scan #{self.scan_count} [{strategy_name}]", "INFO")
            
            # Check position limits against exchange
            if not self.portfolio.check_position_limits_before_order(self.market):
                self.notifier.quantum_log("📊 Position limit reached - skipping signal scan", "INFO")
                return
            
            # Check emergency conditions
            if self._check_emergency_conditions():
                return
            
            # Scan each symbol
            detected_signals = []
            
            active_pairs = [s for s, c in config.PAIR_CONFIGS.items() if c.get("active", False)]
            for symbol in active_pairs:
                if not self._can_trade_symbol(symbol, config.PAIR_CONFIGS[symbol]):
                    continue
                
                # Get market data
                candles = self.market.get_candles(symbol, config.TIMEFRAME, config.LOOKBACK_CANDLES)
                if not candles or len(candles) < 50:  # Minimum candles needed
                    continue
                
                # MODULAR: Let strategy detect signals
                signal = self._safe_strategy_call("detect_entry_signal", symbol, candles, verbose=config.VERBOSE_LOGGING)
                
                if signal:
                    detected_signals.append(signal)
                    self.signals_detected_today += 1
                    
                    # Log signal detection
                    if hasattr(self.logger, 'log_signal_detected'):
                        self.logger.log_signal_detected(signal)
            
            # Log scan performance
            if hasattr(self.logger, 'log_scan_performance'):
                self.logger.log_scan_performance(
                    self.scan_count,
                    time.time() - self.last_signal_scan,
                    len(active_pairs),
                    len(detected_signals)
                )
            
            # Execute filtered signals
            if detected_signals:
                # MODULAR: Let strategy filter signals
                filtered_signals = self._safe_strategy_call("filter_correlated_signals", detected_signals)
                
                self.notifier.quantum_log(
                    f"⚡ Executing {len(filtered_signals)} filtered signals "
                    f"(from {len(detected_signals)} detected)",
                    "INFO"
                )
                
                self._execute_signals(filtered_signals)
            else:
                self.notifier.quantum_log("💤 No signals detected in this scan", "INFO")
                
        except Exception as e:
            self.logger.log_error("SignalScan", str(e))
            self.notifier.quantum_log(f"🚨 Signal scan error: {str(e)}", "ERROR")
            import traceback
            traceback.print_exc()

    def _execute_signals(self, signals):
        """Execute filtered signals with PROPER ATOMIC POSITION ENFORCEMENT"""
        print(f"\n{'='*60}")
        print(f"🚀 EXECUTING {len(signals)} SIGNALS")
        print(f"{'='*60}")

        executed = 0
        
        # CRITICAL FIX: Pre-reserve all slots atomically
        reserved_slots = []
        
        with self.position_counter_lock:
            # Get current state from exchange
            all_positions = self.market.get_all_active_positions()
            position_symbols = set(all_positions.keys())
            current_position_count = len(position_symbols)
            
            # Get pending orders
            pending_symbols = set(self.portfolio.pending_orders.keys())
            
            # Update committed positions tracker
            self.committed_positions = position_symbols.union(pending_symbols)
            
            # CRITICAL: Track total committed positions
            total_committed = len(self.committed_positions)
            
            print(f"\n📊 PRE-EXECUTION POSITION CHECK:")
            print(f"  Active positions: {current_position_count}")
            print(f"  Pending orders: {len(pending_symbols)}")
            print(f"  Total committed: {total_committed}/{config.MAX_TOTAL_POSITIONS}")
            
            if all_positions:
                print(f"  Active: {', '.join(position_symbols)}")
            if pending_symbols:
                print(f"  Pending: {', '.join(pending_symbols)}")

            # Check if already at limit
            if total_committed >= config.MAX_TOTAL_POSITIONS:
                print(f"  ❌ POSITION LIMIT ALREADY REACHED - ABORTING ALL SIGNALS")
                self.notifier.quantum_log(
                    f"🚫 Position limit reached ({total_committed}/{config.MAX_TOTAL_POSITIONS}) - no signals executed",
                    "WARNING"
                )
                return

            # ATOMIC RESERVATION: Reserve slots for all signals we'll execute
            signals_to_execute = []
            for signal in signals:
                symbol = signal["symbol"]
                
                # Check if already committed
                if symbol in self.committed_positions:
                    print(f"  ⚠️ {symbol} already committed - skipping")
                    continue
                
                # Check if would exceed limit
                if len(self.committed_positions) + len(signals_to_execute) >= config.MAX_TOTAL_POSITIONS:
                    print(f"  ⚠️ Would exceed limit - stopping signal processing")
                    break
                
                # Reserve this slot
                reservation_id = self.portfolio.check_position_limits_before_order(self.market)
                if reservation_id:
                    reserved_slots.append((symbol, reservation_id))
                    signals_to_execute.append(signal)
                    self.committed_positions.add(symbol)
                else:
                    print(f"  ❌ Could not reserve slot for {symbol}")
                    break

        # Now execute with reserved slots
        for signal, (symbol, reservation_id) in zip(signals_to_execute, reserved_slots):
            print(f"\n{'='*50}")
            print(f"📊 Processing signal: {symbol} {signal['action']} (Reserved: {reservation_id})")
            
            # Execute the entry with reservation
            success = False
            try:
                # Update reservation with actual symbol
                self.portfolio.update_reservation(reservation_id, symbol)
                
                success = self._execute_entry(signal)
                if success:
                    executed += 1
                    self.trades_executed_today += 1
                    print(f"   ✅ Entry executed successfully!")
                    
                    # Track entry performance
                    entry_type = signal.get('entry_type', 'STANDARD')
                    if not hasattr(self, 'entry_performance'):
                        self.entry_performance = {}
                    if entry_type not in self.entry_performance:
                        self.entry_performance[entry_type] = {'count': 0, 'success': 0}
                    self.entry_performance[entry_type]['count'] += 1
                    self.entry_performance[entry_type]['success'] += 1
                    
                    # Rate limit between executions
                    if executed < len(signals_to_execute):
                        time.sleep(2.0)
                else:
                    # Remove from committed if failed
                    self.committed_positions.discard(symbol)
                    print(f"   ❌ Entry execution failed!")
            except Exception as e:
                # Remove from committed on error
                self.committed_positions.discard(symbol)
                print(f"   ❌ Entry execution error: {str(e)}")
                self.notifier.quantum_log(f"❌ Failed to execute {symbol}: {str(e)}", "ERROR")

        print(f"\n{'='*60}")
        print(f"📊 EXECUTION COMPLETE: {executed}/{len(signals)} signals executed")
        
        # Final verification
        time.sleep(2)
        final_positions = self.market.get_all_active_positions()
        final_pending = len(self.portfolio.pending_orders)
        print(f"📊 POST-EXECUTION VERIFICATION:")
        print(f"  Active positions: {len(final_positions)}")
        print(f"  Pending orders: {final_pending}")
        print(f"  Total: {len(final_positions) + final_pending}/{config.MAX_TOTAL_POSITIONS}")
        print(f"{'='*60}\n")

    def _monitor_and_process_orders(self):
        """Monitor and process pending orders - NO OCO PLACEMENT TO PREVENT RACE CONDITION"""
        try:
            # Monitor unfilled orders
            filled_orders = self.portfolio.monitor_unfilled_orders(self.market, self.notifier)
            
            if not filled_orders:
                return
            
            self.notifier.quantum_log(f"📊 Processing {len(filled_orders)} filled orders", "INFO")
            
            for order_data in filled_orders:
                symbol = order_data['symbol']
                pending_data = order_data['pending_data']
                fill_price = order_data['fill_price']
                actual_quantity = order_data['actual_quantity']
                slippage = order_data['slippage']
                
                # Log fill
                self.notifier.quantum_log(
                    f"✅ Processing fill for {symbol} @ ${fill_price:.4f} "
                    f"(slippage: {slippage*100:.2f}%)",
                    "SUCCESS"
                )
                
                # CRITICAL FIX: DO NOT PLACE EXIT ORDERS HERE!
                # The _execute_entry function is responsible for placing exit orders
                # This prevents the race condition where incorrect stops are placed
                
                # Just log that the fill was processed
                self.notifier.quantum_log(
                    f"📝 Fill processed for {symbol} - exit orders will be handled by entry executor",
                    "INFO"
                )
                
                # Note: The portfolio.order_filled was already called by monitor_unfilled_orders
                # so the position is recorded, but without exit orders being placed here
                        
        except Exception as e:
            self.logger.log_error("MonitorOrders", str(e))
            self.notifier.quantum_log(f"⚠️ Order monitoring error: {str(e)}", "WARNING")

    def _monitor_oco_orders(self):
        """🎯 IMPROVED: Monitor OCO orders more efficiently"""
        try:
            # Use the improved market method
            self.market.monitor_and_execute_oco_logic()
            
            # Also check portfolio positions for exit order status
            for symbol, position in self.portfolio.positions_cache.items():
                tp_order_id = position.get('tp_order_id')
                sl_order_id = position.get('sl_order_id')
                
                # Skip if no exit orders
                if not tp_order_id or not sl_order_id:
                    continue
                
                # Skip if already being tracked by market OCO logic
                if symbol in self.market.oco_pairs:
                    continue
                
                # Manual check for orphaned exit orders
                tp_status = self.market.cache_order_status_fresh(symbol, tp_order_id, max_age=0.5)
                sl_status = self.market.cache_order_status_fresh(symbol, sl_order_id, max_age=0.5)
                
                # If one is filled but not tracked, handle it
                if tp_status == "FILLED" and sl_status not in ["FILLED", "CANCELED"]:
                    self.notifier.quantum_log(
                        f"🎯 Found untracked TP fill for {symbol} - cancelling SL",
                        "INFO"
                    )
                    self.market.cancel_order(symbol, sl_order_id)
                    position['sl_order_id'] = None
                    # Track lifecycle
                    try:
                        self.portfolio.track_order_event(symbol, 'TP_FILLED', {"tp_order_id": tp_order_id})
                    except Exception:
                        pass
                    
                elif sl_status == "FILLED" and tp_status not in ["FILLED", "CANCELED"]:
                    self.notifier.quantum_log(
                        f"🛡️ Found untracked SL fill for {symbol} - cancelling TP",
                        "INFO"
                    )
                    self.market.cancel_order(symbol, tp_order_id)
                    position['tp_order_id'] = None
                    # Track lifecycle
                    try:
                        self.portfolio.track_order_event(symbol, 'SL_FILLED', {"sl_order_id": sl_order_id})
                    except Exception:
                        pass
                    
        except Exception as e:
            self.logger.log_error("OCOMonitor", str(e))
            self.notifier.quantum_log(f"⚠️ OCO monitoring error: {str(e)}", "WARNING")

    def _monitor_exit_orders_fast(self):
        """Monitor exit orders at INSTITUTIONAL SPEED - 2 second checks with circuit breaker safety"""
        try:
            # ENHANCED: Circuit breaker safe polling
            if self.market._check_circuit_breaker():
                print("🔌 Circuit breaker active - skipping exit order monitoring")
                return
            
            # Get all active positions
            exchange_positions = self.portfolio.get_positions_from_exchange(self.market)
            
            for symbol, position in self.portfolio.positions_cache.items():
                tp_order_id = position.get('tp_order_id')
                sl_order_id = position.get('sl_order_id')
                
                # Skip if no exit orders
                if not tp_order_id or not sl_order_id:
                    continue
                
                # Check if position still exists on exchange
                if symbol not in exchange_positions:
                    # Position closed - cancel any remaining orders
                    self.market.cancel_order(symbol, tp_order_id)
                    self.market.cancel_order(symbol, sl_order_id)
                    continue
                
                # Check order statuses
                tp_status = self.market.cache_order_status_fresh(symbol, tp_order_id, max_age=0.5)
                sl_status = self.market.cache_order_status_fresh(symbol, sl_order_id, max_age=0.5)
                
                # If TP filled, cancel SL immediately
                if tp_status == "FILLED" and sl_status not in ["FILLED", "CANCELED"]:
                    if self.market.cancel_order(symbol, sl_order_id):
                        self.notifier.quantum_log(f"✅ {symbol} TP filled - SL cancelled", "SUCCESS")
                    position['sl_order_id'] = None
                    try:
                        self.portfolio.track_order_event(symbol, 'TP_FILLED', {"tp_order_id": tp_order_id})
                    except Exception:
                        pass
                    
                # If SL filled, cancel TP immediately
                elif sl_status == "FILLED" and tp_status not in ["FILLED", "CANCELED"]:
                    if self.market.cancel_order(symbol, tp_order_id):
                        self.notifier.quantum_log(f"✅ {symbol} SL filled - TP cancelled", "SUCCESS")
                    position['tp_order_id'] = None
                    try:
                        self.portfolio.track_order_event(symbol, 'SL_FILLED', {"sl_order_id": sl_order_id})
                    except Exception:
                        pass
                    
                # If both cancelled/expired, position might be manually closed
                elif tp_status in ["CANCELED", "EXPIRED", None] and sl_status in ["CANCELED", "EXPIRED", None]:
                    # Verify position still exists
                    if symbol not in exchange_positions:
                        self.notifier.quantum_log(f"📊 {symbol} exit orders cleared - position closed", "INFO")
                        
        except Exception as e:
            self.logger.log_error("FastExitMonitor", str(e))

    def _place_oco_exit_orders(self, symbol, position_data):
        """🎯 Place OCO exit orders for a position - FIXED to use pre-calculated stops"""
        try:
            direction = position_data["direction"]
            quantity = position_data["quantity"]
            entry_price = position_data.get("entry_price", 0)
            
            # ✅ CRITICAL FIX: Use the pre-calculated stop and target prices
            # These were already calculated correctly in _execute_entry based on actual fill price
            stop_price = position_data.get("stop_price")
            target_price = position_data.get("target_price")
            
            # CRITICAL: Validate that the prices were passed correctly
            if not stop_price or not target_price or stop_price <= 0 or target_price <= 0:
                self.notifier.quantum_log(
                    f"❌ Invalid or missing stop/target prices in position_data for {symbol}! "
                    f"Stop: {stop_price}, Target: {target_price}",
                    "ERROR"
                )
                self.logger.log_error("PlaceOCO", f"Missing/invalid stops for {symbol}", 
                                    {"position_data": position_data})
                return None
            
            # Log what we're using (for verification)
            self.notifier.quantum_log(
                f"🎯 Using pre-calculated exits for {symbol}: "
                f"Entry=${entry_price:.4f}, Stop=${stop_price:.4f}, Target=${target_price:.4f}",
                "INFO"
            )
            
            # Verify the percentages (for logging only, not recalculating)
            if direction == "LONG":
                actual_sl_pct = (entry_price - stop_price) / entry_price * 100
                actual_tp_pct = (target_price - entry_price) / entry_price * 100
            else:
                actual_sl_pct = (stop_price - entry_price) / entry_price * 100
                actual_tp_pct = (entry_price - target_price) / entry_price * 100
            
            self.notifier.quantum_log(
                f"📊 Exit percentages: SL={actual_sl_pct:.2f}%, TP={actual_tp_pct:.2f}%",
                "INFO"
            )
            
            # Determine exit side
            exit_side = "SELL" if direction == "LONG" else "BUY"
            
            # Wait for position to be visible on exchange
            self.notifier.quantum_log(f"⏳ Waiting for {symbol} position to settle...", "INFO")
            time.sleep(config.OCO_VERIFICATION_DELAY)
            
            # Verify position exists with retry
            position_verified = False
            for attempt in range(3):
                if self.market.verify_position_exists(symbol):
                    position_verified = True
                    break
                self.notifier.quantum_log(
                    f"⏳ Position not yet visible, waiting... (attempt {attempt + 1}/3)",
                    "INFO"
                )
                time.sleep(2)
            
            if not position_verified:
                self.notifier.quantum_log(
                    f"❌ Cannot place OCO - {symbol} position not verified after 3 attempts",
                    "ERROR"
                )
                return None
            
            # Check for existing exit orders to prevent duplicates
            existing_exit_orders = self.market.get_open_orders()
            if existing_exit_orders:
                symbol_exit_orders = [order for order in existing_exit_orders 
                                    if order.get('symbol') == symbol and order.get('reduceOnly', False)]
                if symbol_exit_orders:
                    self.notifier.quantum_log(
                        f"⚠️ Found {len(symbol_exit_orders)} existing exit orders for {symbol} - skipping OCO placement",
                        "WARNING"
                    )
                    return None
            
            # Place OCO with retry logic
            self.notifier.quantum_log(
                f"🎯 Placing OCO orders for {symbol}... TP=${target_price:.4f}, SL=${stop_price:.4f}",
                "INFO"
            )
            
            oco_result = None
            last_error = None
            
            for attempt in range(config.OCO_PLACEMENT_RETRIES):
                try:
                    oco_result = self.market.place_oco_order(
                        symbol, exit_side, quantity, target_price, stop_price
                    )
                    
                    if oco_result:
                        break
                        
                    last_error = "OCO returned None"
                    
                except Exception as e:
                    last_error = str(e)
                    self.notifier.quantum_log(
                        f"⚠️ OCO attempt {attempt + 1} failed: {last_error}",
                        "WARNING"
                    )
                
                if attempt < config.OCO_PLACEMENT_RETRIES - 1:
                    time.sleep(2 * (attempt + 1))  # Progressive delay
            
            if not oco_result:
                self.notifier.quantum_log(
                    f"🚨 Failed to place OCO after {config.OCO_PLACEMENT_RETRIES} attempts: {last_error}",
                    "ERROR"
                )
                return None
            
            # Update portfolio with order IDs
            self.portfolio.update_exit_order_ids(
                symbol,
                tp_order_id=oco_result["tp_order_id"],
                sl_order_id=oco_result["sl_order_id"]
            )
            
            # Send OCO placed alert immediately after creation
            self.notifier.send_oco_placed_alert(symbol, oco_result)
            
            try:
                self.portfolio.track_order_event(symbol, 'OCO_PLACED', {
                    "tp_order_id": oco_result["tp_order_id"],
                    "sl_order_id": oco_result["sl_order_id"]
                })
            except Exception:
                pass
            
            # Mark exit orders as placed
            self.portfolio.mark_exit_orders_placed(symbol)
            
            # Final verification
            time.sleep(1)
            final_check = self.market.verify_exit_orders(
                symbol,
                oco_result["tp_order_id"],
                oco_result["sl_order_id"]
            )
            
            if final_check["tp_found"] and final_check["sl_found"]:
                self.notifier.quantum_log(
                    f"✅ OCO PLACED & VERIFIED for {symbol} | "
                    f"TP: ${target_price:.4f} (ID: {oco_result['tp_order_id']}) | "
                    f"SL: ${stop_price:.4f} (ID: {oco_result['sl_order_id']})",
                    "SUCCESS"
                )
                
                return oco_result
            else:
                self.notifier.quantum_log(
                    f"⚠️ OCO placed but verification failed for {symbol}",
                    "WARNING"
                )
                return oco_result
                
        except Exception as e:
            self.logger.log_error("PlaceOCO", str(e), {"symbol": symbol})
            self.notifier.quantum_log(f"🚨 OCO placement error: {str(e)}", "ERROR")
            return None

    def _place_separate_exit_orders(self, symbol, position_data):
        """🛡️ Place separate TP and SL orders (fallback if OCO not available)"""
        try:
            # This is the legacy method - kept as fallback
            # Implementation would place TP and SL separately
            self.notifier.quantum_log(f"⚠️ Using separate exit orders for {symbol} (OCO disabled)", "WARNING")
            # ... implementation ...
            return None
            
        except Exception as e:
            self.logger.log_error("PlaceSeparateExits", str(e))
            return None

    def _monitor_positions(self):
        """🔍 Monitor active positions with exchange data - FIXED TP/SL CALCULATIONS"""
        try:
            self.notifier.quantum_log("🔍 Position monitoring cycle starting...", "INFO")
            
            # Get latest positions directly from the exchange
            exchange_positions = self.portfolio.get_positions_from_exchange(self.market)
            
            self.notifier.quantum_log(
                f"📊 Monitoring {len(exchange_positions)} active positions",
                "INFO"
            )
            
            # Check each position with individual error handling
            for symbol, exchange_pos in exchange_positions.items():
                try:
                    # Get cached position data for exit levels
                    cached_pos = self.portfolio.positions_cache.get(symbol, {})
                    
                    # Ensure we have valid data before processing
                    current_price = exchange_pos.get('current_price')
                    if current_price is None:
                        self.notifier.quantum_log(
                            f"⚠️ No current price for {symbol}, fetching...",
                            "WARNING"
                        )
                        current_price = self.market.get_price(symbol)
                        if current_price is None:
                            self.notifier.quantum_log(
                                f"❌ Cannot get price for {symbol}, skipping",
                                "ERROR"
                            )
                            continue
                        exchange_pos['current_price'] = current_price
                    
                    # CRITICAL FIX: Use STRATEGY parameters, not config!
                    if 'stop_price' not in cached_pos or cached_pos['stop_price'] is None:
                        # Get STRATEGY's actual parameters
                        strategy_params = self.strategy.get_exit_params()
                        sl_pct = strategy_params['sl_pct']  # Will be 0.004 for your strategy
                        tp_pct = strategy_params['tp_pct']  # Will be 0.005 for your strategy
                        
                        entry_price = exchange_pos.get('entry_price', current_price)
                        direction = exchange_pos.get('direction', 'LONG')
                        
                        if direction == "LONG":
                            cached_pos['stop_price'] = entry_price * (1 - sl_pct)  # FIXED!
                            cached_pos['target_price'] = entry_price * (1 + tp_pct)  # FIXED!
                        else:
                            cached_pos['stop_price'] = entry_price * (1 + sl_pct)  # FIXED!
                            cached_pos['target_price'] = entry_price * (1 - tp_pct)  # FIXED!
                        
                        # Verify the calculations
                        if direction == "LONG":
                            actual_sl_pct = (entry_price - cached_pos['stop_price']) / entry_price * 100
                            actual_tp_pct = (cached_pos['target_price'] - entry_price) / entry_price * 100
                        else:
                            actual_sl_pct = (cached_pos['stop_price'] - entry_price) / entry_price * 100
                            actual_tp_pct = (entry_price - cached_pos['target_price']) / entry_price * 100
                        
                        self.notifier.quantum_log(
                            f"⚠️ {symbol} missing stops - using STRATEGY defaults: "
                            f"SL=${cached_pos['stop_price']:.4f} ({actual_sl_pct:.1f}%), "
                            f"TP=${cached_pos['target_price']:.4f} ({actual_tp_pct:.1f}%)",
                            "WARNING"
                        )
                        
                        # Save the corrected position data
                        self.portfolio.positions_cache[symbol] = cached_pos
                        self.portfolio.save_positions()
                    
                    # Combine exchange and cached data
                    position_data = {
                        **cached_pos,
                        **exchange_pos,
                        "symbol": symbol
                    }
                    
                    # Update portfolio cache
                    self.portfolio.update_position(
                        symbol,
                        current_price,
                        exchange_pos.get('unrealized_pnl', 0)
                    )
                    
                    # Log position update
                    if hasattr(self.logger, 'log_position_update'):
                        self.logger.log_position_update(symbol, position_data, current_price)
                    
                    # MODULAR: Let strategy check exit conditions
                    bars_held = self._calculate_bars_held(position_data.get("entry_time"))

                    exit_signal = self._safe_strategy_call("check_exit_conditions",
                        position_data,
                        current_price,
                        bars_held
                    )
                    
                    if exit_signal:
                        self.notifier.quantum_log(
                            f"🚪 Exit signal for {symbol}: {exit_signal['reason']}", 
                            "INFO"
                        )
                        self._execute_exit(symbol, position_data, exit_signal)
                        
                except Exception as e:
                    # Individual position error - log but continue with others
                    self.logger.log_error("MonitorPosition", str(e), {"symbol": symbol})
                    self.notifier.quantum_log(
                        f"⚠️ Error monitoring {symbol}: {str(e)} - continuing with other positions", 
                        "WARNING"
                    )
                    continue  # Continue monitoring other positions
            
            # Check for closed positions (outside the loop for safety)
            try:
                for symbol in list(self.portfolio.positions_cache.keys()):
                    if symbol not in exchange_positions:
                        self.notifier.quantum_log(f"💀 {symbol} closed on exchange", "INFO")
                        self._handle_exchange_closed_position(symbol)
            except Exception as e:
                self.notifier.quantum_log(
                    f"⚠️ Error checking closed positions: {str(e)}", 
                    "WARNING"
                )
                        
        except Exception as e:
            # Top-level error - this should rarely happen now
            self.logger.log_error("PositionMonitor", str(e))
            self.notifier.quantum_log(f"🚨 Position monitor critical error: {str(e)}", "ERROR")

    def _validate_position_data(self, symbol, position_data):
        """
        Validate and fix position data before using it
        """
        # Ensure required fields exist and are not None
        required_fields = {
            'symbol': symbol,
            'direction': 'LONG',  # default
            'entry_price': 0,
            'current_price': 0,
            'stop_price': 0,
            'target_price': 0,
            'quantity': 0,
            'unrealized_pnl': 0
        }
        
        for field, default_value in required_fields.items():
            if field not in position_data or position_data[field] is None:
                position_data[field] = default_value
                
        # Calculate missing stops if needed
        if position_data['stop_price'] == 0 and position_data['entry_price'] > 0:
            if position_data['direction'] == 'LONG':
                position_data['stop_price'] = position_data['entry_price'] * (1 - config.FIXED_SL_PCT)
                position_data['target_price'] = position_data['entry_price'] * (1 + config.FIXED_TP_PCT)
            else:
                position_data['stop_price'] = position_data['entry_price'] * (1 + config.FIXED_SL_PCT)
                position_data['target_price'] = position_data['entry_price'] * (1 - config.FIXED_TP_PCT)
        
        return position_data

    def _handle_exchange_closed_position(self, symbol):
        """Handle a position that was closed on exchange - ENHANCED"""
        try:
            cached_pos = self.portfolio.positions_cache.get(symbol)
            if not cached_pos:
                # Try to get data from recent trades
                self.notifier.quantum_log(f"⚠️ No cached data for {symbol}, checking trade history...", "WARNING")
                
                trades = self.market.get_trade_history(symbol, limit=50)
                if trades:
                    # Find entry and exit trades
                    entry_trade = None
                    exit_trade = None
                    
                    for trade in trades:
                        if float(trade.get('realizedPnl', 0)) == 0 and not entry_trade:
                            entry_trade = trade
                        elif float(trade.get('realizedPnl', 0)) != 0:
                            exit_trade = trade
                            
                    if entry_trade:
                        # Reconstruct basic position data
                        cached_pos = {
                            "symbol": symbol,
                            "direction": "LONG" if entry_trade['side'] == "BUY" else "SHORT",
                            "entry_price": float(entry_trade['price']),
                            "quantity": float(entry_trade['qty']),
                            "position_size_usd": float(entry_trade['qty']) * float(entry_trade['price']),
                            "entry_time": datetime.fromtimestamp(entry_trade['time']/1000).isoformat()
                        }
                        self.notifier.quantum_log(f"✅ Reconstructed position from trades", "INFO")
            
            if not cached_pos:
                self.notifier.quantum_log(f"❌ Cannot process closed position {symbol} - no data", "ERROR")
                return
            
            # Determine exit details
            exit_price = cached_pos.get('current_price', cached_pos['entry_price'])
            exit_type = "UNKNOWN"
            reason = "Position Closed on Exchange"
            
            # Check recent orders to determine exit type
            try:
                recent_orders = self.market.get_recent_orders(symbol, limit=20)
                
                for order in recent_orders:
                    if order['status'] == 'FILLED' and order.get('reduceOnly'):
                        order_time = order.get('updateTime', order.get('time', 0))
                        
                        # Check if order is recent (within 10 minutes)
                        if (time.time() * 1000 - order_time) < 600000:
                            if order['type'] == 'LIMIT':
                                # Likely TP
                                exit_type = "TAKE_PROFIT"
                                reason = "Take Profit Hit"
                                exit_price = float(order.get('avgPrice', order['price']))
                                break
                            elif order['type'] in ['STOP_MARKET', 'STOP', 'STOP_LOSS_LIMIT']:
                                # Likely SL
                                exit_type = "STOP_LOSS"
                                reason = "Stop Loss Hit"
                                exit_price = float(order.get('avgPrice', order['price']))
                                break
                            elif order['type'] == 'MARKET':
                                # Manual or bot exit
                                exit_type = "MANUAL"
                                reason = "Manual Exit"
                                exit_price = float(order.get('avgPrice', order['price']))
                                
            except Exception as e:
                self.notifier.quantum_log(f"⚠️ Error checking orders: {str(e)}", "WARNING")
            
            # Calculate P&L
            quantity = cached_pos.get("quantity", 0)
            entry_price = cached_pos.get("entry_price", exit_price)
            
            if cached_pos.get("direction") == "LONG":
                pnl_usd = (exit_price - entry_price) * quantity
            else:
                pnl_usd = (entry_price - exit_price) * quantity
            
            # Log position exit
            if hasattr(self.logger, 'log_position_exit'):
                exit_data = {
                    "symbol": symbol,
                    "direction": cached_pos.get("direction", "UNKNOWN"),
                    "entry_price": entry_price,
                    "exit_price": exit_price,
                    "pnl_usd": pnl_usd,
                    "pnl_pct": (pnl_usd / cached_pos.get("position_size_usd", 1)) * 100 if cached_pos.get("position_size_usd", 0) > 0 else 0,
                    "reason": reason,
                    "exit_type": exit_type,
                    "hold_time_hours": self._calculate_hold_time_hours(cached_pos.get("entry_time"))
                }
                self.logger.log_position_exit(exit_data)
            
            # Close position in portfolio and get trade data
            trade_data = self.portfolio.close_position(
                symbol, exit_price, pnl_usd, reason,
                additional_info={"exit_type": exit_type}
            )
            
            # Clean up orders
            self.market.cancel_all_orders_for_symbol(symbol)
            
            # Send notification with complete data
            if trade_data:
                exit_alert_data = {
                    "symbol": symbol,
                    "direction": trade_data.get("direction", "UNKNOWN"),
                    "entry_price": trade_data.get("entry_price", 0),
                    "exit_price": exit_price,
                    "pnl_usd": pnl_usd,
                    "pnl_pct": trade_data.get("pnl_pct", 0),
                    "reason": reason,
                    "exit_type": exit_type,
                    "hold_time": trade_data.get("hold_time_bars", 0)
                }
                
                self.notifier.send_strike_exit_alert(exit_alert_data)
                self.notifier.quantum_log(
                    f"✅ Exit notification sent: {symbol} | {exit_type} | P&L: ${pnl_usd:+.2f}",
                    "SUCCESS"
                )
            
        except Exception as e:
            self.logger.log_error("HandleClosedPosition", str(e), {"symbol": symbol})
            self.notifier.quantum_log(f"🚨 Error handling closed position {symbol}: {str(e)}", "ERROR")
            import traceback
            traceback.print_exc()

    
    def _execute_entry(self, signal):
        """Execute a single entry signal - FIXED STOP/TARGET CALCULATION"""
        symbol = signal["symbol"]
        action = signal["action"]
        side = "BUY" if action == "LONG" else "SELL"
        entry_price_target = signal["entry_price"]
        
        try:
            with self.order_lock:
                # Final safety check
                if not self.market.verify_no_position_exists(symbol):
                    self.notifier.quantum_log(f"⚠️ {symbol} already has position - aborting entry", "WARNING")
                    return False
                
                if symbol in self.portfolio.pending_orders:
                    self.notifier.quantum_log(f"⚠️ {symbol} already has pending order", "WARNING")
                    return False
                
                # Calculate position size
                position_sizing = self._safe_strategy_call("calculate_position_size", symbol, self.portfolio.balance_usd)
                if not position_sizing:
                    self.notifier.quantum_log(f"❌ Sizing calculation failed for {symbol}", "ERROR")
                    return False
                
                quantity = self.market.calculate_quantity(symbol, position_sizing["position_size_usd"], entry_price_target)
                if quantity <= 0:
                    self.notifier.quantum_log(f"❌ Invalid quantity ({quantity}) for {symbol}", "ERROR")
                    return False
                
                # Prepare order data
                order_data = {
                    "symbol": symbol,
                    "direction": action,
                    "entry_price": entry_price_target,
                    "quantity": quantity,
                    "stop_price": signal["stop_price"],
                    "target_price": signal["target_price"],
                    "position_size_usd": position_sizing["position_size_usd"],
                    "risk_usd": position_sizing["risk_usd"],
                    "pair_config": config.PAIR_CONFIGS.get(symbol, {}),
                    "signal_data": signal
                }
                
                # Add to pending orders
                self.portfolio.add_pending_order(symbol, order_data)
                try:
                    self.portfolio.track_order_event(symbol, 'PENDING_ENTRY', {"order": order_data})
                except Exception:
                    pass
                
                # IMPROVED: Progressive fill strategy
                self.notifier.quantum_log(f"🚀 Placing limit order for {symbol}...", "INFO")
                
                # Send entry attempt alert
                self.notifier.send_entry_attempt_alert(symbol, signal, position_sizing)
                
                fill_start = time.time()
                
                # Place limit order
                order = self.market.place_order(symbol, side, quantity, price=entry_price_target)
                
                if not order:
                    self.notifier.send_entry_failed_alert(symbol, signal, "PLACEMENT_FAILED")
                    self.portfolio.cancel_unfilled_order(symbol, "PLACEMENT_FAILED")
                    return False
                
                order_id = order.get("orderId")
                self.portfolio.pending_orders[symbol]["order_id"] = order_id
                
                # IMPROVED FILL STRATEGY: 15 seconds for limit, then convert to market
                filled = False
                limit_wait_time = 15  # Give limit order more time
                market_fallback = True  # Enable market order fallback
                
                # Phase 1: Wait for limit fill (15 seconds)
                filled = self.market.wait_for_order_fill(symbol, order_id, timeout=limit_wait_time)
                
                if not filled and market_fallback:
                    # Phase 2: Cancel limit and try market order
                    self.notifier.quantum_log(f"⏰ Limit order not filled in {limit_wait_time}s - converting to MARKET", "WARNING")
                    
                    # Send market conversion alert
                    self.notifier.send_entry_converted_alert(symbol, signal, "LIMIT_TO_MARKET")
                    
                    # Cancel the limit order
                    if self.market.cancel_order(symbol, order_id):
                        # Place market order immediately
                        self.notifier.quantum_log(f"🚀 Placing MARKET order for immediate fill...", "INFO")
                        
                        market_order = self.market.place_order(symbol, side, quantity, price=None)  # Market order
                        
                        if market_order:
                            market_order_id = market_order.get("orderId")
                            self.portfolio.pending_orders[symbol]["order_id"] = market_order_id
                            
                            # Wait for market fill (should be instant)
                            filled = self.market.wait_for_order_fill(symbol, market_order_id, timeout=5)
                            
                            if filled:
                                self.notifier.quantum_log(f"✅ Market order filled!", "SUCCESS")
                                order_id = market_order_id  # Update order ID for fill info
                
                if not filled:
                    # Final cancellation
                    self.market.cancel_order(symbol, order_id)
                    self.notifier.send_entry_failed_alert(symbol, signal, "TIMEOUT")
                    self.portfolio.cancel_unfilled_order(symbol, "TIMEOUT")
                    
                    # Track performance
                    self.fill_performance['attempted'] += 1
                    self.fill_performance['cancelled'] += 1
                    
                    return False
                
                # ORDER FILLED - Process it
                fill_info = self.market.get_order_fills(symbol, order_id)
                if fill_info:
                    fill_price = fill_info["avg_price"]
                    actual_quantity = fill_info["total_qty"]
                else:
                    fill_price = entry_price_target
                    actual_quantity = quantity
                
                # Track fill performance
                fill_time = time.time() - fill_start
                self.fill_performance['attempted'] += 1
                self.fill_performance['filled'] += 1
                self.fill_performance['avg_fill_time'] = (
                    (self.fill_performance['avg_fill_time'] * (self.fill_performance['filled'] - 1) + fill_time) /
                    self.fill_performance['filled']
                )
                
                self.notifier.quantum_log(
                    f"✅ FILLED in {fill_time:.1f}s: {symbol} @ ${fill_price:.4f} "
                    f"(slippage: {abs(fill_price - entry_price_target)/entry_price_target*100:.2f}%)",
                    "SUCCESS"
                )
                try:
                    self.portfolio.track_order_event(symbol, 'ENTRY_FILLED', {
                        "price": fill_price,
                        "quantity": actual_quantity,
                        "order_id": order_id
                    })
                except Exception:
                    pass
                
                # RECALCULATE STOPS BASED ON ACTUAL FILL PRICE - FIXED!
                strategy_params = self.strategy.get_exit_params()
                sl_pct = strategy_params['sl_pct']
                tp_pct = strategy_params['tp_pct']
                
                if action == "LONG":
                    recalc_stop = fill_price * (1 - sl_pct)    # Use strategy's actual percentages
                    recalc_target = fill_price * (1 + tp_pct)
                else:  # SHORT
                    recalc_stop = fill_price * (1 + sl_pct)
                    recalc_target = fill_price * (1 - tp_pct)
                
                # Verify the calculations are correct
                if action == "LONG":
                    actual_sl_pct = (fill_price - recalc_stop) / fill_price * 100
                    actual_tp_pct = (recalc_target - fill_price) / fill_price * 100
                else:
                    actual_sl_pct = (recalc_stop - fill_price) / fill_price * 100  
                    actual_tp_pct = (fill_price - recalc_target) / fill_price * 100
                
                self.notifier.quantum_log(
                    f"🎯 RECALCULATED EXITS: SL=${recalc_stop:.4f} ({actual_sl_pct:.1f}%), "
                    f"TP=${recalc_target:.4f} ({actual_tp_pct:.1f}%)",
                    "INFO"
                )
                
                # Process the fill in portfolio
                order_result = {
                    "status": "FILLED",
                    "symbol": symbol,
                    "price": fill_price,
                    "quantity": actual_quantity
                }
                
                if not self.portfolio.order_filled(symbol, order_result):
                    self.notifier.quantum_log(f"❌ Failed to process fill for {symbol}", "ERROR")
                    return False
                
                # Update position with recalculated stops
                position_data = self.portfolio.positions_cache.get(symbol)
                if position_data:
                    position_data["stop_price"] = recalc_stop
                    position_data["target_price"] = recalc_target
                    position_data["actual_entry_price"] = fill_price
                    position_data["entry_slippage"] = abs(fill_price - entry_price_target) / entry_price_target
                    self.portfolio.save_positions()
                
                # SEND ENTRY NOTIFICATION
                self.notifier.send_strike_entry_alert(signal, position_sizing)
                
                # Log to advanced logger
                if hasattr(self.logger, 'log_position_entry'):
                    self.logger.log_position_entry({
                        "symbol": symbol,
                        "direction": action,
                        "entry_price": fill_price,
                        "quantity": actual_quantity,
                        "position_size_usd": position_sizing["position_size_usd"],
                        "stop_price": recalc_stop,
                        "target_price": recalc_target,
                        "market_type": "FUTURES" if config.ENABLE_FUTURES else "SPOT"
                    })
                
                # =============================================================
                # ✅ ADD THIS LINE TO START THE SYMBOL-SPECIFIC COOLDOWN
                # =============================================================
                self.strategy.notify_trade_executed(symbol)
                
                # Place exit orders
                if config.ENABLE_FUTURES and config.AUTO_PLACE_EXIT_ORDERS:
                    time.sleep(2)  # Let position register
                    
                    if config.USE_OCO_ORDERS:
                        oco_result = self._place_oco_exit_orders(symbol, position_data)
                        if not oco_result:
                            self.notifier.quantum_log(
                                f"⚠️ Exit orders failed for {symbol} - POSITION UNPROTECTED!",
                                "WARNING"
                            )
                            
                self.trades_executed_today += 1
                return True
                
        except Exception as e:
            self.notifier.quantum_log(f"❌ Entry execution error for {symbol}: {str(e)}", "ERROR")
            try:
                self.portfolio.cancel_unfilled_order(symbol, f"ERROR: {str(e)}")
            except:
                pass
            return False


    def _generate_client_order_id(self, symbol, side, order_type="entry"):
        """Generate unique client order ID for deduplication"""
        timestamp = int(time.time() * 1000)
        return f"HYP_{order_type}_{symbol}_{side}_{timestamp}"

    def _execute_exit(self, symbol, position, exit_signal):
        """Execute a bot-decided exit safely - ENHANCED"""
        with self.position_operation_lock:
            try:
                self.notifier.quantum_log(f"🚪 Executing exit for {symbol}: {exit_signal['reason']}", "INFO")

                # Cancel existing exit orders
                self.notifier.quantum_log(f"⏳ Cancelling exit orders for {symbol}...", "INFO")
                self.market.cancel_all_exit_orders(symbol)
                time.sleep(0.5)

                # Verify position still exists
                exchange_position = self.market.get_position(symbol)
                if not exchange_position or abs(exchange_position.get('positionAmt', 0)) == 0:
                    self.notifier.quantum_log(f"✅ Position {symbol} already closed", "INFO")
                    self._handle_exchange_closed_position(symbol)
                    return

                # Place closing order with retry
                exit_side = "SELL" if position["direction"] == "LONG" else "BUY"
                quantity = abs(float(exchange_position['positionAmt']))

                self.notifier.quantum_log(f"🚀 Placing close order for {symbol}...", "INFO")
                
                # Log order attempt
                start_time = self.logger.log_order_attempt(symbol, exit_side, quantity, None, "MARKET")
                
                close_order = self.market.place_order_with_retry(
                    symbol, exit_side, quantity, reduce_only=True
                )
                
                if not close_order:
                    self.logger.log_order_result(symbol, None, start_time, success=False)
                    self.notifier.send_critical_alert(
                        f"🚨 CRITICAL: FAILED TO CLOSE {symbol}! MANUAL INTERVENTION REQUIRED!", 
                        "CRITICAL"
                    )
                    return

                self.logger.log_order_result(symbol, close_order, start_time, success=True)
                self.notifier.quantum_log(f"✅ Closing order placed for {symbol}", "SUCCESS")
                
                # Wait for fill
                order_id = close_order.get("orderId")
                filled = self.market.wait_for_order_fill(symbol, order_id, timeout=30)
                
                if filled:
                    self.notifier.quantum_log(f"✅ Position {symbol} closed successfully", "SUCCESS")
                    
                    # Get fill price
                    fill_info = self.market.get_order_fills(symbol, order_id)
                    exit_price = fill_info["avg_price"] if fill_info else exchange_position.get('markPrice', position.get('entry_price'))
                    
                    # Calculate P&L
                    quantity = abs(float(exchange_position['positionAmt']))
                    entry_price = position.get('entry_price', exchange_position.get('entryPrice'))
                    
                    if position["direction"] == "LONG":
                        pnl_usd = (exit_price - entry_price) * quantity
                    else:
                        pnl_usd = (entry_price - exit_price) * quantity
                    
                    # Log position exit
                    hold_time_hours = self._calculate_hold_time_hours(position.get("entry_time"))
                    exit_data = {
                        "symbol": symbol,
                        "direction": position["direction"],
                        "entry_price": entry_price,
                        "exit_price": exit_price,
                        "pnl_usd": pnl_usd,
                        "pnl_pct": (pnl_usd / position.get("position_size_usd", 1)) * 100,
                        "reason": exit_signal["reason"],
                        "exit_type": exit_signal["exit_type"],
                        "hold_time_hours": hold_time_hours,
                        "market_type": "FUTURES" if config.ENABLE_FUTURES else "SPOT"
                    }
                    
                    if hasattr(self.logger, 'log_position_exit'):
                        self.logger.log_position_exit(exit_data)
                    
                    # Close position in portfolio and get trade data
                    trade_data = self.portfolio.close_position(
                        symbol, exit_price, pnl_usd, exit_signal["reason"],
                        additional_info={"exit_type": exit_signal["exit_type"]}
                    )
                    
                    # Send exit notification with complete data
                    if trade_data:
                        exit_alert_data = {
                            "symbol": symbol,
                            "direction": trade_data.get("direction", position["direction"]),
                            "entry_price": trade_data.get("entry_price", entry_price),
                            "exit_price": exit_price,
                            "pnl_usd": pnl_usd,
                            "pnl_pct": trade_data.get("pnl_pct", (pnl_usd / position.get("position_size_usd", 1)) * 100),
                            "reason": exit_signal["reason"],
                            "exit_type": exit_signal["exit_type"],
                            "hold_time": trade_data.get("hold_time_bars", self._calculate_bars_held(position.get("entry_time")))
                        }
                        
                        self.notifier.send_strike_exit_alert(exit_alert_data)
                        self.notifier.quantum_log(
                            f"✅ Exit complete and notification sent: {symbol} | P&L: ${pnl_usd:+.2f}",
                            "SUCCESS"
                        )
                else:
                    self.notifier.quantum_log(f"⚠️ Close order not filled yet for {symbol}", "WARNING")
                            
            except Exception as e:
                self.logger.log_error("ExecuteExit", str(e), {"symbol": symbol})
                self.notifier.quantum_log(f"🚨 Exit execution error: {str(e)}", "ERROR")
                import traceback
                traceback.print_exc()

    def _check_and_repair_exit_orders(self):
        """🔧 Check and repair missing exit orders - FIXED CALCULATION"""
        if not config.ENABLE_FUTURES or not config.AUTO_PLACE_EXIT_ORDERS:
            return
        
        try:
            # Get positions from exchange
            exchange_positions = self.portfolio.get_positions_from_exchange(self.market)
            
            for symbol in exchange_positions:
                cached_pos = self.portfolio.positions_cache.get(symbol, {})
                
                # Skip if position is too new (might still be placing orders)
                position_age = time.time() - cached_pos.get('entry_timestamp', time.time())
                if position_age < 30:  # Wait 30 seconds before attempting repair
                    continue
                
                # CRITICAL FIX: If stop_price or target_price is missing or 0, calculate them!
                if not cached_pos:
                    # Create minimal cached position from exchange data
                    exchange_data = exchange_positions[symbol]
                    cached_pos = {
                        'symbol': symbol,
                        'direction': exchange_data.get('direction', 'LONG'),
                        'entry_price': exchange_data.get('entry_price', 0),
                        'quantity': exchange_data.get('quantity', 0),
                        'stop_price': 0,
                        'target_price': 0,
                        'entry_timestamp': time.time() - 31  # Mark as old enough
                    }
                    self.portfolio.positions_cache[symbol] = cached_pos
                
                # FIX: Calculate missing stop/target prices using STRATEGY percentages
                entry_price = cached_pos.get('entry_price', 0)
                if entry_price == 0:
                    # Try to get from exchange
                    entry_price = exchange_positions[symbol].get('entry_price', 0)
                    cached_pos['entry_price'] = entry_price
                
                # If stop_price is 0 or missing, calculate it using STRATEGY percentages
                if not cached_pos.get('stop_price') or cached_pos.get('stop_price') == 0:
                    if entry_price > 0:
                        # CRITICAL FIX: Use strategy's actual percentages, not config defaults
                        strategy_params = self.strategy.get_exit_params()
                        sl_pct = strategy_params['sl_pct']  # Will be 0.004 (0.4%)
                        tp_pct = strategy_params['tp_pct']  # Will be 0.005 (0.5%)
                        
                        direction = cached_pos.get('direction', 'LONG')
                        if direction == 'LONG':
                            cached_pos['stop_price'] = entry_price * (1 - sl_pct)
                            cached_pos['target_price'] = entry_price * (1 + tp_pct)
                        else:  # SHORT
                            cached_pos['stop_price'] = entry_price * (1 + sl_pct)
                            cached_pos['target_price'] = entry_price * (1 - tp_pct)
                        
                        # Verify the calculations
                        if direction == 'LONG':
                            actual_sl_pct = (entry_price - cached_pos['stop_price']) / entry_price * 100
                            actual_tp_pct = (cached_pos['target_price'] - entry_price) / entry_price * 100
                        else:
                            actual_sl_pct = (cached_pos['stop_price'] - entry_price) / entry_price * 100
                            actual_tp_pct = (entry_price - cached_pos['target_price']) / entry_price * 100
                        
                        self.notifier.quantum_log(
                            f"📊 Calculated stops for {symbol} using STRATEGY params: "
                            f"Entry=${entry_price:.4f}, SL=${cached_pos['stop_price']:.4f} ({actual_sl_pct:.1f}%), "
                            f"TP=${cached_pos['target_price']:.4f} ({actual_tp_pct:.1f}%)",
                            "INFO"
                        )
                        
                        # Save the updated position data
                        self.portfolio.save_positions()
                    else:
                        self.notifier.quantum_log(
                            f"❌ Cannot calculate stops for {symbol} - no entry price!",
                            "ERROR"
                        )
                        continue
                
                # Check if exit orders exist
                status = self.market.verify_exit_orders_fast(symbol)
                
                # Only repair if BOTH are missing (avoid duplicate orders)
                if not status['has_tp'] and not status['has_sl']:
                    self.notifier.quantum_log(
                        f"⚠️ {symbol} missing BOTH exit orders - attempting repair...",
                        "WARNING"
                    )
                    
                    # Send repair notification
                    self.notifier.send_exit_order_repair_alert(symbol, ["TP", "SL"])
                    
                    # Verify we have valid prices before attempting OCO
                    if cached_pos['stop_price'] > 0 and cached_pos['target_price'] > 0:
                        # Repair by placing new OCO
                        if config.USE_OCO_ORDERS:
                            self._place_oco_exit_orders(symbol, cached_pos)
                        else:
                            self._place_separate_exit_orders(symbol, cached_pos)
                    else:
                        self.notifier.quantum_log(
                            f"❌ Cannot place exit orders for {symbol} - invalid prices!",
                            "ERROR"
                        )
                elif not status['has_tp'] or not status['has_sl']:
                    # Only one is missing - be careful
                    missing = []
                    if not status['has_tp']:
                        missing.append("TP")
                    if not status['has_sl']:
                        missing.append("SL")
                    
                    self.notifier.quantum_log(
                        f"⚠️ {symbol} missing {', '.join(missing)} order(s) - manual intervention may be needed",
                        "WARNING"
                    )
                        
        except Exception as e:
            self.logger.log_error("RepairExitOrders", str(e))
            self.notifier.quantum_log(f"🚨 Exit order repair error: {str(e)}", "ERROR")

    def _emergency_checks(self):
        """Run emergency protocol checks"""
        try:
            # Get actual positions from exchange
            exchange_positions = self.portfolio.get_positions_from_exchange(self.market)
            total_positions = len(exchange_positions)
            pending_orders = len(self.portfolio.pending_orders)
            
            # Position limit check
            if total_positions > config.MAX_TOTAL_POSITIONS:
                self.notifier.send_critical_alert(
                    f"🚨 POSITION LIMIT BREACHED: {total_positions}/{config.MAX_TOTAL_POSITIONS}",
                    "CRITICAL"
                )
                return False
            
            # Daily loss check
            daily_pnl = self.portfolio.get_daily_pnl_usd()
            daily_loss_limit = self.portfolio.balance_usd * (config.DAILY_LOSS_LIMIT_PERCENT / 100)
            
            if daily_pnl <= -daily_loss_limit:
                self.notifier.send_critical_alert(
                    f"🚨 DAILY LOSS LIMIT HIT: ${daily_pnl:.2f} (limit: ${-daily_loss_limit:.2f})",
                    "CRITICAL"
                )
                return False
            
            # Minimum balance check
            if self.portfolio.balance_usd < config.MIN_BALANCE_USD:
                self.notifier.send_critical_alert(
                    f"🚨 BALANCE TOO LOW: ${self.portfolio.balance_usd:.2f} < ${config.MIN_BALANCE_USD}",
                    "CRITICAL"
                )
                return False
            
            # Consecutive loss check
            if self.portfolio.consecutive_losses >= config.CONSECUTIVE_LOSS_LIMIT:
                self.notifier.send_critical_alert(
                    f"🚨 CONSECUTIVE LOSS LIMIT: {self.portfolio.consecutive_losses} losses in a row",
                    "CRITICAL"
                )
                return False
            
            # Margin warning for futures
            if config.ENABLE_FUTURES:
                account_info = self.market.get_account_info()
                if account_info:
                    total_margin_balance = float(account_info.get('totalMarginBalance', 0))
                    total_position_margin = float(account_info.get('totalPositionInitialMargin', 0))
                    
                    # FIX: Only calculate margin ratio if we have positions
                    if total_position_margin > 0:
                        margin_ratio = total_margin_balance / total_position_margin
                        
                        if margin_ratio < config.MARGIN_CALL_THRESHOLD:
                            liquidation_risk_symbols = []
                            for symbol in exchange_positions:
                                pos = exchange_positions[symbol]
                                if pos.get('unrealized_pnl', 0) < 0:
                                    liquidation_risk_symbols.append(symbol)
                            
                            self.notifier.send_margin_warning(margin_ratio, liquidation_risk_symbols)
                            return False
                    else:
                        # No positions = no margin risk
                        # This is the normal state when not trading
                        pass
                else:
                    # Add warning when account info cannot be retrieved
                    self.notifier.quantum_log("⚠️ Could not retrieve account info for margin check.", "WARNING")
            
            return True
            
        except Exception as e:
            self.logger.log_error("EmergencyCheck", str(e))
            # Don't stop on check error - log it but continue trading
            return True

    def _check_emergency_conditions(self):
        """Check for emergency stop conditions"""
        # Daily loss limit
        daily_pnl = self.portfolio.get_daily_pnl_usd()
        daily_loss_limit = self.portfolio.balance_usd * (config.DAILY_LOSS_LIMIT_PERCENT / 100)
        
        if daily_pnl <= -daily_loss_limit:
            self.notifier.quantum_log(f"🚨 Daily loss limit hit: ${daily_pnl:.2f}", "WARNING")
            return True
        
        # Minimum balance
        if self.portfolio.balance_usd < config.MIN_BALANCE_USD:
            self.notifier.quantum_log(f"🚨 Balance below minimum: ${self.portfolio.balance_usd:.2f}", "WARNING")
            return True
        
        return False

    def _emergency_position_check(self):
        """Emergency check for positions needing immediate closure - WITH DUPLICATE PREVENTION"""
        try:
            # Get positions from exchange
            exchange_positions = self.portfolio.get_positions_from_exchange(self.market)
            
            for symbol, exchange_pos in exchange_positions.items():
                # Skip if already triggered emergency for this position
                if symbol in self.emergency_triggered_positions:
                    continue
                    
                current_price = exchange_pos['current_price']
                entry_price = exchange_pos['entry_price']
                direction = exchange_pos['direction']
                
                # Calculate P&L
                if direction == "LONG":
                    pnl_pct = ((current_price - entry_price) / entry_price) * 100
                else:
                    pnl_pct = ((entry_price - current_price) / entry_price) * 100
                
                # Check emergency conditions
                emergency_close = False
                reason = ""
                
                # Max loss exceeded
                if pnl_pct <= -config.EMERGENCY_LOSS_PERCENT:
                    emergency_close = True
                    reason = f"EMERGENCY: Max loss exceeded ({pnl_pct:.1f}%)"
                
                if emergency_close:
                    # Mark as triggered to prevent duplicates
                    self.emergency_triggered_positions.add(symbol)
                    
                    self.notifier.send_critical_alert(
                        f"🚨 EMERGENCY CLOSE: {symbol}\n{reason}",
                        "CRITICAL"
                    )
                    
                    exit_signal = {
                        "exit_type": "EMERGENCY",
                        "reason": reason
                    }
                    
                    # Combine data for exit
                    position_data = {**cached_pos, **exchange_pos}
                    self._execute_exit(symbol, position_data, exit_signal)
            
            # Clean up closed positions from emergency tracker
            for symbol in list(self.emergency_triggered_positions):
                if symbol not in exchange_positions:
                    self.emergency_triggered_positions.discard(symbol)
                    
        except Exception as e:
            self.logger.log_error("EmergencyPositionCheck", str(e))
            self.notifier.quantum_log(f"⚠️ Emergency position check error: {str(e)}", "WARNING")

    def _cleanup_old_data(self):
        """🧹 Clean up old data to prevent memory leaks - MORE AGGRESSIVE"""
        try:
            current_time = time.time()
            
            # Clean old order status cache in market (more aggressive)
            if hasattr(self.market, '_order_status_cache'):
                cutoff_time = current_time - 1800  # Keep last 30 minutes only (was 1 hour)
                old_size = len(self.market._order_status_cache)
                self.market._order_status_cache = {
                    k: v for k, v in self.market._order_status_cache.items()
                    if v['timestamp'] > cutoff_time
                }
                new_size = len(self.market._order_status_cache)
                if old_size - new_size > 0:
                    self.notifier.quantum_log(f"🧹 Cleaned {old_size - new_size} order cache entries", "INFO")
            
            # Clean old OCO pairs (more aggressive)
            if hasattr(self.market, 'oco_pairs'):
                old_count = len(self.market.oco_pairs)
                for symbol in list(self.market.oco_pairs.keys()):
                    oco_data = self.market.oco_pairs[symbol]
                    if current_time - oco_data.get('created_at', 0) > 43200:  # 12 hours
                        del self.market.oco_pairs[symbol]
                if len(self.market.oco_pairs) < old_count:
                    self.notifier.quantum_log(f"🧹 Cleaned {old_count - len(self.market.oco_pairs)} stale OCO pairs", "INFO")
            
            # Trim fill performance history
            if hasattr(self, 'fill_performance'):
                if self.fill_performance.get('attempted', 0) > 500:  # Reduced from 1000
                    fill_rate = (self.fill_performance['filled'] / self.fill_performance['attempted'] * 100) if self.fill_performance['attempted'] > 0 else 0
                    self.fill_performance = {
                        'attempted': 0,
                        'filled': 0,
                        'cancelled': 0,
                        'avg_fill_time': self.fill_performance.get('avg_fill_time', 0),
                        'historical_fill_rate': fill_rate
                    }
                    self.notifier.quantum_log(f"📊 Reset fill stats. Historical rate: {fill_rate:.1f}%", "INFO")
            
            # Clear emergency triggered positions that are no longer active
            if hasattr(self, 'emergency_triggered_positions'):
                active_positions = set(self.portfolio.positions_cache.keys())
                old_size = len(self.emergency_triggered_positions)
                self.emergency_triggered_positions = self.emergency_triggered_positions.intersection(active_positions)
                if len(self.emergency_triggered_positions) < old_size:
                    self.notifier.quantum_log(f"🧹 Cleaned {old_size - len(self.emergency_triggered_positions)} emergency flags", "INFO")
            
            # FIX: Clean emergency retry tracking
            if hasattr(self, 'emergency_close_retries'):
                for symbol in list(self.emergency_close_retries.keys()):
                    if symbol not in self.portfolio.positions_cache:
                        del self.emergency_close_retries[symbol]
            
            # FIX: Call logger cleanup
            if hasattr(self.logger, 'cleanup_performance_tracking'):
                self.logger.cleanup_performance_tracking()
            
            self.notifier.quantum_log("🧹 Memory cleanup completed", "INFO")
            
        except Exception as e:
            self.notifier.quantum_log(f"⚠️ Memory cleanup error: {str(e)}", "WARNING")

    def _safe_strategy_call(self, method_name, *args, **kwargs):
        """Safely call strategy methods with error handling"""
        try:
            method = getattr(self.strategy, method_name)
            return method(*args, **kwargs)
        except Exception as e:
            self.logger.log_error(f"Strategy.{method_name}", str(e))
            self.notifier.quantum_log(f"⚠️ Strategy error in {method_name}: {str(e)}", "WARNING")
            
            # Return safe defaults based on method
            if method_name == "detect_entry_signal":
                return None
            elif method_name == "check_exit_conditions":
                return None
            elif method_name == "filter_correlated_signals":
                return args[0] if args else []  # Return unfiltered signals
            elif method_name == "calculate_position_size":
                # Return default sizing
                return {
                    "position_size_usd": config.FIXED_POSITION_SIZE_USD,
                    "risk_usd": config.FIXED_POSITION_SIZE_USD * config.FIXED_SL_PCT,
                    "risk_pct": (config.FIXED_POSITION_SIZE_USD * config.FIXED_SL_PCT / self.portfolio.balance_usd) * 100,
                    "leverage": config.LEVERAGE if config.ENABLE_FUTURES else 1,
                    "margin_required": config.FIXED_POSITION_SIZE_USD / config.LEVERAGE if config.ENABLE_FUTURES else config.FIXED_POSITION_SIZE_USD
                }
            else:
                return None
        
    def _update_heartbeat_file(self):
        """💓 Update heartbeat file ATOMICALLY for external monitoring"""
        try:
            heartbeat_file = f"{config.DATA_DIR}/bot_heartbeat.json"
            heartbeat_data = {
                "timestamp": time.time(),
                "datetime": datetime.now(timezone.utc).isoformat(),  # CHANGED
                "status": "RUNNING",
                "positions": len(self.portfolio.positions_cache),
                "pending_orders": len(self.portfolio.pending_orders),
                "balance": self.portfolio.balance_usd,
                "errors": self.consecutive_errors,
                "uptime_hours": (datetime.now(timezone.utc) - self.bot_start_time).total_seconds() / 3600,  # CHANGED
                "last_scan": self.last_signal_scan,
                "strategy": self.strategy.__class__.__name__,
                "fill_performance": self.fill_performance
            }
            
            # Atomic write with temp file
            temp_file = f"{heartbeat_file}.tmp"
            with open(temp_file, 'w') as f:
                json.dump(heartbeat_data, f, indent=2)
            
            # Atomic rename (on POSIX systems)
            os.replace(temp_file, heartbeat_file)
            
        except Exception as e:
            # Don't crash on heartbeat errors
            if self.consecutive_errors == 0:  # Only log if not already in error state
                self.notifier.quantum_log(f"⚠️ Heartbeat file update failed: {str(e)}", "WARNING")

    def _emergency_close_all_positions(self):
        """🚨 Emergency close all positions - WITH RETRY MECHANISM"""
        self.notifier.quantum_log("🚨 EMERGENCY: Closing all positions!", "CRITICAL")
        
        failed_closures = []
        
        try:
            # Get all positions from exchange
            exchange_positions = self.portfolio.get_positions_from_exchange(self.market)
            
            if not exchange_positions:
                self.notifier.quantum_log("✅ No positions to close", "INFO")
                return
            
            for symbol, exchange_pos in exchange_positions.items():
                close_success = False
                
                # FIX: Try up to 3 times per symbol
                for attempt in range(self.max_emergency_retries):
                    try:
                        self.notifier.quantum_log(f"🚨 Emergency close attempt {attempt + 1}/{self.max_emergency_retries} for {symbol}", "INFO")
                        
                        # Cancel all orders first
                        self.market.cancel_all_orders_for_symbol(symbol)
                        time.sleep(0.5)
                        
                        # Get position details
                        direction = exchange_pos.get('direction', 'LONG')
                        exit_side = "SELL" if direction == "LONG" else "BUY"
                        quantity = abs(float(exchange_pos.get('quantity', exchange_pos.get('positionAmt', 0))))
                        
                        if quantity == 0:
                            self.notifier.quantum_log(f"⚠️ {symbol} has zero quantity, skipping", "WARNING")
                            close_success = True
                            break
                        
                        # Place market order
                        close_order = self.market.place_order(symbol, exit_side, quantity, reduce_only=True)
                        
                        if close_order:
                            # Wait for fill
                            order_id = close_order.get("orderId")
                            filled = self.market.wait_for_order_fill(symbol, order_id, timeout=10)
                            
                            if filled:
                                self.notifier.quantum_log(f"✅ Emergency closed {symbol} on attempt {attempt + 1}", "SUCCESS")
                                close_success = True
                                break
                            else:
                                self.notifier.quantum_log(f"⚠️ Order placed but not filled for {symbol}", "WARNING")
                        
                        # Wait before retry
                        if attempt < self.max_emergency_retries - 1:
                            time.sleep(2 * (attempt + 1))  # Progressive delay
                            
                    except Exception as e:
                        self.notifier.quantum_log(f"🚨 Emergency close attempt {attempt + 1} failed for {symbol}: {str(e)}", "ERROR")
                        if attempt < self.max_emergency_retries - 1:
                            time.sleep(2)
                
                if not close_success:
                    failed_closures.append(symbol)
                    self.emergency_close_retries[symbol] = self.max_emergency_retries
                    self.notifier.quantum_log(f"❌ FAILED to emergency close {symbol} after {self.max_emergency_retries} attempts", "CRITICAL")
                
                # Brief pause between symbols
                time.sleep(1)
            
            # Report results
            if failed_closures:
                self.notifier.send_critical_alert(
                    f"🚨 EMERGENCY CLOSE INCOMPLETE!\n"
                    f"Failed to close {len(failed_closures)} positions: {', '.join(failed_closures)}\n"
                    f"MANUAL INTERVENTION REQUIRED IMMEDIATELY!",
                    "CRITICAL"
                )
                
                # FIX: Log failed positions to file
                try:
                    emergency_file = f"{config.LOG_DIR}/emergency_failed_closes_{int(time.time())}.txt"
                    with open(emergency_file, 'w') as f:
                        f.write(f"Emergency close failed at {datetime.now(timezone.utc).isoformat()}\n")
                        f.write(f"Failed symbols:\n")
                        for symbol in failed_closures:
                            pos = exchange_positions.get(symbol, {})
                            f.write(f"  {symbol}: {pos}\n")
                    self.notifier.quantum_log(f"📝 Failed positions logged to {emergency_file}", "INFO")
                except:
                    pass
            else:
                self.notifier.quantum_log("✅ All positions closed successfully", "SUCCESS")
                        
        except Exception as e:
            self.logger.log_error("EmergencyCloseAll", str(e))
            self.notifier.quantum_log(f"🚨 Emergency close all error: {str(e)}", "ERROR")
            self.notifier.send_critical_alert(
                f"🚨 EMERGENCY CLOSE FAILED!\n{str(e)}\nMANUAL INTERVENTION REQUIRED!",
                "CRITICAL"
            )

    def _retry_failed_emergency_closes(self):
        """Retry failed emergency closes periodically"""
        if not self.emergency_close_retries:
            return
        
        for symbol in list(self.emergency_close_retries.keys()):
            try:
                # Check if position still exists
                position = self.market.get_position(symbol)
                if not position or abs(position.get('positionAmt', 0)) == 0:
                    del self.emergency_close_retries[symbol]
                    self.notifier.quantum_log(f"✅ {symbol} no longer has position", "INFO")
                    continue
                
                # Try to close again
                self.notifier.quantum_log(f"🔄 Retrying emergency close for {symbol}", "WARNING")
                
                direction = "LONG" if position['positionAmt'] > 0 else "SHORT"
                exit_side = "SELL" if direction == "LONG" else "BUY"
                quantity = abs(position['positionAmt'])
                
                close_order = self.market.place_order(symbol, exit_side, quantity, reduce_only=True)
                
                if close_order:
                    order_id = close_order.get("orderId")
                    filled = self.market.wait_for_order_fill(symbol, order_id, timeout=10)
                    
                    if filled:
                        self.notifier.quantum_log(f"✅ Successfully closed {symbol} on retry", "SUCCESS")
                        del self.emergency_close_retries[symbol]
                        
            except Exception as e:
                self.notifier.quantum_log(f"⚠️ Retry failed for {symbol}: {str(e)}", "WARNING")

    def _cleanup_stale_entries(self):
        """🧹 Clean up stale entry LIMIT orders"""
        try:
            current_time = time.time()
            cleaned_count = 0
            
            for symbol, pending_data in list(self.portfolio.pending_orders.items()):
                order_time = pending_data.get('timestamp', 0)
                order_id = pending_data.get('order_id')
                
                # Check if order is older than 5 minutes (300 seconds)
                if current_time - order_time > 300 and order_id:
                    self.notifier.quantum_log(
                        f"🧹 Cleaning stale entry order for {symbol} (age: {int(current_time - order_time)}s)",
                        "WARNING"
                    )
                    
                    # Cancel the order with retry
                    if self.market.cancel_order(symbol, order_id):
                        self.notifier.send_entry_failed_alert(symbol, pending_data.get('signal', {}), "STALE_TIMEOUT")
                        self.portfolio.cancel_unfilled_order(symbol, "STALE_TIMEOUT")
                        cleaned_count += 1
                    else:
                        self.notifier.quantum_log(
                            f"⚠️ Failed to cancel stale order {order_id} for {symbol}",
                            "WARNING"
                        )
            
            if cleaned_count > 0:
                self.notifier.quantum_log(
                    f"🧹 Cleaned {cleaned_count} stale entry orders",
                    "INFO"
                )
                
            # Update orphan cleanup counter
            if hasattr(self, 'orphans_cleaned_last_5m'):
                self.orphans_cleaned_last_5m += cleaned_count
            else:
                self.orphans_cleaned_last_5m = cleaned_count
                
        except Exception as e:
            self.notifier.quantum_log(f"⚠️ Stale entry cleanup error: {str(e)}", "WARNING")

    def _send_heartbeat(self):
        """💓 Send heartbeat with ACCURATE REAL-TIME DATA"""
        try:
            # Update balance
            self._update_account_balance()
            
            # Get REAL current data
            portfolio_summary = self.portfolio.get_summary()
            exchange_positions = self.portfolio.get_positions_from_exchange(self.market)
            
            # Get position details for heartbeat
            positions_data = []
            total_unrealized_pnl = 0
            
            for symbol, pos in exchange_positions.items():
                unrealized = pos.get('unrealized_pnl', 0)
                total_unrealized_pnl += unrealized
                
                positions_data.append({
                    "symbol": symbol,
                    "direction": pos.get('direction', 'UNKNOWN'),
                    "unrealized_pnl": unrealized,
                    "unrealized_pnl_pct": (unrealized / pos.get('position_size_usd', 1)) * 100 if pos.get('position_size_usd', 0) > 0 else 0
                })
            
            # Calculate expected vs actual open orders
            expected_open_orders = len(exchange_positions) * 2  # 2 exit orders per position (TP + SL)
            actual_open_orders = 0
            orphans_cleaned_last_5m = 0
            
            try:
                # Get actual open orders from exchange
                open_orders = self.market.get_open_orders()
                if open_orders:
                    # Count only reduceOnly orders (exit orders)
                    actual_open_orders = sum(1 for order in open_orders if order.get('reduceOnly', False))
                
                # Track orphans cleaned (this will be updated by cleanup functions)
                if hasattr(self, 'orphans_cleaned_last_5m'):
                    orphans_cleaned_last_5m = self.orphans_cleaned_last_5m
                    
            except Exception as e:
                self.notifier.quantum_log(f"⚠️ Error calculating order parity: {str(e)}", "WARNING")
            
            # Build ACCURATE heartbeat data
            heartbeat_data = {
                "balance": self.portfolio.balance_usd,
                "active_positions": len(exchange_positions),
                "pending_orders": len(self.portfolio.pending_orders),
                "today_pnl": portfolio_summary["today_pnl_usd"],
                "today_trades": portfolio_summary["today_trades"],
                "today_win_rate": portfolio_summary["today_win_rate"],
                "uptime_hours": (datetime.now(timezone.utc) - self.bot_start_time).total_seconds() / 3600,  # CHANGED
                "scan_count": self.scan_count,
                "strategy": self.strategy.__class__.__name__,
                "positions": positions_data[:5],  # Top 5 positions
                "account_value_usd": self.portfolio.balance_usd + total_unrealized_pnl,
                "total_unrealized_pnl": total_unrealized_pnl,
                "expected_open_orders": expected_open_orders,
                "actual_open_orders": actual_open_orders,
                "orphans_cleaned_last_5m": orphans_cleaned_last_5m,
                "fill_performance": {
                    "fill_rate": (self.fill_performance['filled'] / self.fill_performance['attempted'] * 100) if self.fill_performance['attempted'] > 0 else 0,
                    "avg_fill_time": self.fill_performance['avg_fill_time']
                }
            }
            
            # Send heartbeat
            self.notifier.send_quantum_heartbeat(heartbeat_data)
            
        except Exception as e:
            self.logger.log_error("Heartbeat", str(e))
            self.notifier.quantum_log(f"⚠️ Heartbeat error: {str(e)}", "WARNING")

    def _track_execution_metrics(self):
        """Track execution quality metrics"""
        if not hasattr(self, 'execution_metrics'):
            self.execution_metrics = {
                'total_slippage_bps': 0,
                'orders_placed': 0,
                'avg_fill_time': 0,
                'limit_fills': 0,
                'market_fills': 0,
                'failed_orders': 0
            }
        
        # Calculate average slippage
        if self.execution_metrics['orders_placed'] > 0:
            avg_slippage = self.execution_metrics['total_slippage_bps'] / self.execution_metrics['orders_placed']
            
            # Alert if slippage is high
            if avg_slippage > 10:  # More than 10 bps average
                self.notifier.quantum_log(
                    f"⚠️ High average slippage: {avg_slippage:.1f} bps",
                    "WARNING"
                )

    def _can_trade_symbol(self, symbol, pair_config):
        """Check if symbol can be traded"""
        # Check if active
        if not pair_config.get("active", False):
            return False
        
        # Check if already have position
        if symbol in self.portfolio.positions_cache:
            return False
        
        # Check if have pending order
        if symbol in self.portfolio.pending_orders:
            return False
        
        # Check 24hr stats if configured
        if config.MIN_24H_VOLUME_USD > 0:
            stats = self.market.get_24hr_stats(symbol)
            if stats and stats["quoteVolume"] < config.MIN_24H_VOLUME_USD:
                return False
        
        return True

    def _calculate_bars_held(self, entry_time):
        """Calculate number of bars held"""
        if not entry_time:
            return 0
        
        try:
            # Handle both string and datetime
            if isinstance(entry_time, str):
                # Remove timezone info and parse
                entry_dt = datetime.fromisoformat(entry_time.replace('Z', '+00:00').split('+')[0])
                # Make it timezone-aware if it isn't
                if entry_dt.tzinfo is None:
                    entry_dt = entry_dt.replace(tzinfo=timezone.utc)
            else:
                entry_dt = entry_time
                if entry_dt.tzinfo is None:
                    entry_dt = entry_dt.replace(tzinfo=timezone.utc)
            
            # Use UTC for current time
            current_time = datetime.now(timezone.utc)
            time_held = current_time - entry_dt
            minutes_held = time_held.total_seconds() / 60
            
            # Map timeframe to minutes
            timeframe_minutes = {
                "1m": 1, "3m": 3, "5m": 5, "15m": 15,
                "30m": 30, "1h": 60, "4h": 240, "1d": 1440
            }
            
            bar_minutes = timeframe_minutes.get(config.TIMEFRAME, 15)
            bars = int(minutes_held / bar_minutes)
            
            return bars
            
        except Exception as e:
            print(f"⚠️ Error calculating bars held: {str(e)}")
            import traceback
            traceback.print_exc()
            return 0
    
    def _calculate_hold_time_hours(self, entry_time):
        """Calculate hold time in hours"""
        try:
            if isinstance(entry_time, str):
                entry_dt = datetime.fromisoformat(entry_time.replace('Z', '+00:00').split('+')[0])
            else:
                entry_dt = entry_time
            return round((datetime.now() - entry_dt).total_seconds() / 3600, 1)
        except:
            return 0.0

    def _should_run(self, last_run_time, interval):
        """Check if enough time has passed to run a task"""
        return time.time() - last_run_time >= interval

    def _cycle_sleep(self, cycle_start):
        """Sleep for remainder of cycle"""
        cycle_duration = time.time() - cycle_start
        sleep_time = max(0, config.MAIN_LOOP_INTERVAL - cycle_duration)
        if sleep_time > 0:
            time.sleep(sleep_time)

    def verify_trade_logging(self):
        """Check if trades.log is being written - ENHANCED VERSION"""
        log_file = config.TRADES_LOG_FILE
        print(f"\n{'='*60}")
        print(f"🔍 TRADE LOG VERIFICATION:")
        print(f"   Log file path: {log_file}")
        print(f"   Directory exists: {os.path.exists(os.path.dirname(log_file))}")
        print(f"   File exists: {os.path.exists(log_file)}")
        
        # Check write permissions
        if os.path.exists(os.path.dirname(log_file)):
            print(f"   Directory writable: {os.access(os.path.dirname(log_file), os.W_OK)}")
        
        if os.path.exists(log_file):
            # File stats
            stat = os.stat(log_file)
            print(f"   File writable: {os.access(log_file, os.W_OK)}")
            print(f"   File size: {stat.st_size} bytes")
            print(f"   Last modified: {datetime.fromtimestamp(stat.st_mtime).strftime('%Y-%m-%d %H:%M:%S')}")
            
            with open(log_file, 'r') as f:
                lines = f.readlines()
            
            print(f"   Total lines: {len(lines)}")
            
            if lines:
                # Show first and last entries
                print(f"\n   📝 First entry:")
                print(f"      {lines[0].strip()}")
                print(f"\n   📝 Last entry:")
                print(f"      {lines[-1].strip()}")
                
                # Parse last entry to check format
                try:
                    parts = lines[-1].strip().split('|')
                    if len(parts) >= 5:
                        timestamp_str = parts[0]
                        action = parts[1]
                        symbol = parts[2]
                        
                        # Check how recent the last entry is
                        try:
                            last_timestamp = datetime.fromisoformat(timestamp_str)
                            age = (datetime.now() - last_timestamp).total_seconds()
                            print(f"\n   ⏰ Last entry age: {age:.0f} seconds ago")
                            
                            if age > 3600:  # More than 1 hour
                                print(f"   ⚠️ WARNING: Last entry is {age/3600:.1f} hours old!")
                        except:
                            print(f"   ⚠️ Could not parse timestamp from last entry")
                            
                        print(f"   📊 Last action: {action} on {symbol}")
                    else:
                        print(f"   ⚠️ Last entry has unexpected format ({len(parts)} parts)")
                except Exception as e:
                    print(f"   ❌ Error parsing last entry: {str(e)}")
        else:
            print(f"\n   ❌ Log file does not exist!")
            
            # Try to create it
            try:
                os.makedirs(os.path.dirname(log_file), exist_ok=True)
                with open(log_file, 'w') as f:
                    f.write(f"# Trading log created at {datetime.now().isoformat()}\n")
                    f.write(f"# Format: timestamp|action|symbol|price|quantity|details...\n")
                print(f"   ✅ Created new log file with headers")
            except Exception as e:
                print(f"   ❌ ERROR creating log file: {str(e)}")
        
        print(f"{'='*60}\n")

    def _handle_error(self, error):
        """Handle errors in main loop"""
        self.consecutive_errors += 1
        self.last_error = str(error)
        
        self.logger.log_error("MainLoop", str(error))
        self.notifier.quantum_log(f"🚨 Main loop error #{self.consecutive_errors}: {str(error)}", "ERROR")
        
        if config.VERBOSE_LOGGING:
            import traceback
            traceback.print_exc()
        
        # Progressive backoff
        sleep_time = min(60, 5 * self.consecutive_errors)
        self.notifier.quantum_log(f"⏳ Sleeping {sleep_time}s before retry...", "INFO")
        time.sleep(sleep_time)

    def _signal_handler(self, signum, frame):
        """Handle shutdown signals"""
        self.notifier.quantum_log(f"🛑 Received signal {signum} - initiating graceful shutdown", "INFO")
        self.shutdown()

    def shutdown(self):
        """🛑 Graceful shutdown"""
        self.notifier.quantum_log("🛑 Initiating shutdown sequence...", "INFO")
        self.running = False
        
        try:
            # Save portfolio state
            self.notifier.quantum_log("💾 Saving portfolio state...", "INFO")
            self.portfolio.save_positions()
            
            # Send shutdown notification
            summary = self.portfolio.get_summary()
            self.notifier.send_shutdown_message(summary)
            
            # Export session report
            if hasattr(self.logger, 'export_session_report'):
                self.logger.export_session_report()
            
            # Close market connection
            if hasattr(self.market, 'close'):
                self.market.close()
            
            self.notifier.quantum_log("✅ Shutdown complete", "SUCCESS")
            
        except Exception as e:
            self.notifier.quantum_log(f"⚠️ Shutdown error: {str(e)}", "WARNING")
        
        # Final debug state
        if config.VERBOSE_LOGGING:
            self.portfolio.debug_log_state()


def main():
    """🚀 Entry point"""
    print("\n" + "="*60)
    print("🚀 HYPERION MODULAR TRADING BOT 🚀")
    print("="*60 + "\n")
    
    try:
        # Create and run bot
        bot = HyperionModularTradingBot()
        bot.run()
        
    except KeyboardInterrupt:
        print("\n⌨️ Keyboard interrupt - shutting down...")
        if 'bot' in locals():
            bot.shutdown()
            
    except Exception as e:
        print(f"\n🚨 FATAL ERROR: {str(e)}")
        import traceback
        traceback.print_exc()
        
        # Try to send critical alert
        try:
            notifier = QuantumDimensionalPortal()
            notifier.send_critical_alert(
                f"🚨 BOT CRASH: {str(e)}",
                "CRITICAL"
            )
        except:
            pass
    
    print("\n👋 Bot terminated")
    sys.exit(0)


if __name__ == "__main__":
    main()