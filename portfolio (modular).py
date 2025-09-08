# portfolio.py - MODULAR VERSION
"""
🌌 PORTFOLIO MANAGEMENT SYSTEM 🌌
Strategy-agnostic position and P&L tracking
Exchange-first design - Binance is the source of truth
Per Aspera Ad Astra
"""

import json
import os
import csv
import queue
import time
from datetime import datetime, date, timedelta, timezone
from collections import defaultdict, deque
from enum import Enum
import threading
import tempfile
import shutil
import config


class PositionState(Enum):
    """Position lifecycle states"""
    NONE = "NONE"
    PENDING_ENTRY = "PENDING_ENTRY"
    ENTERING = "ENTERING"
    ACTIVE = "ACTIVE"
    PENDING_EXIT = "PENDING_EXIT"
    EXITING = "EXITING"
    CLOSED = "CLOSED"
    ERROR = "ERROR"


class Portfolio:
    def __init__(self):
        """🛸 Initialize Portfolio Tracking System"""
        # Position tracking - local cache only, not source of truth
        self.positions_cache = {}  # Renamed to make it clear it's just a cache
        self.pending_orders = {}
        self.position_states = {}  # Track state machine
        
        # Use a Re-entrant Lock to prevent deadlocks
        self.position_lock = threading.RLock()
        
        # Balance tracking
        self.balance_usd = 0.0
        self.initial_balance_usd = 0.0
        
        # Trade history with archival mechanism
        self.all_trades = []
        self.trades_today = []
        self.max_trades_in_memory = 1000  # ADDED: Prevent memory leak
        self.archived_trades_count = 0  # ADDED: Track archived trades
        
        # Performance metrics
        self.consecutive_losses = 0
        self.consecutive_wins = 0
        self.max_consecutive_wins = 0
        self.max_consecutive_losses = 0
        
        # Initialize the async logging system with CRITICAL FIX
        self.log_queue = queue.Queue(maxsize=1000)  # ADDED: Limit queue size
        self.logging_active = True
        self.log_thread = threading.Thread(target=self._log_writer, daemon=True)
        self.log_thread.start()
        self.failed_log_queue = deque(maxlen=100)  # Store failed logs for retry
        self.log_retry_thread = threading.Thread(target=self._retry_failed_logs, daemon=True)
        self.log_retry_thread.start()

        # Add logging verification flag
        self.verify_logging = getattr(config, 'VERIFY_LOGGING', False)
        # Track failed log attempts
        self.failed_log_attempts = []
        
        # Basic statistics with memory management
        self.daily_stats = defaultdict(lambda: {
            "trades": 0, "wins": 0, "losses": 0, "pnl_usd": 0.0, "volume_usd": 0.0,
            "win_rate": 0.0, "long_trades": 0, "short_trades": 0,
            "futures_trades": 0, "spot_trades": 0,
            "canceled_orders": 0, "filled_orders": 0
        })
        
        # Symbol performance with cleanup mechanism
        self.symbol_performance = {}  # CHANGED: Regular dict, will clean manually
        self.max_symbols_tracked = 100  # ADDED: Limit tracked symbols
        
        # Last sync time
        self.last_exchange_sync = 0
        
        # ADDED: Archive directory for old trades
        self.archive_dir = f"{config.DATA_DIR}/archives"
        os.makedirs(self.archive_dir, exist_ok=True)
        
        # Create directories
        os.makedirs(config.DATA_DIR, exist_ok=True)
        os.makedirs(config.LOG_DIR, exist_ok=True)
        
        print(f"🌌 Portfolio System initialized - Exchange-first design")
        print(f"📈 Market type: {'FUTURES' if config.ENABLE_FUTURES else 'SPOT'}")

        # Order lifecycle tracking - centralized and thread-safe
        self._lifecycle_lock = threading.RLock()
        self._order_lifecycle = {}
        # state machine snapshots for quick checks
        # states: INIT, PENDING_ENTRY, ENTRY_FILLED, OCO_PLACED, TP_FILLED, SL_FILLED, CLOSED

    def sync_with_exchange(self, market):
        """🔄 Sync positions with exchange - ENHANCED WITH REDUCED INTERVALS"""
        with self.position_lock:
            try:
                # SKIP IF DEBUG MODE
                if hasattr(config, 'SKIP_POSITION_VERIFICATION') and config.SKIP_POSITION_VERIFICATION:
                    print("⚠️ SKIPPING EXCHANGE SYNC (DEBUG MODE)")
                    return True
                    
                if not config.ENABLE_FUTURES:
                    # For spot trading, we don't have positions
                    self.positions_cache.clear()
                    return True
                
                # ENHANCED: Check if sync is needed (avoid excessive API calls)
                current_time = time.time()
                if hasattr(self, 'last_sync_attempt') and current_time - self.last_sync_attempt < 15:
                    # Skip if last sync was less than 15 seconds ago
                    return True
                
                self.last_sync_attempt = current_time
                
                # Get all positions from exchange
                exchange_positions = market.get_position_risk()
                if exchange_positions is None:
                    print("⚠️ Could not fetch positions from exchange")
                    return False
                
                # Build current position map from exchange
                current_positions = {}
                sync_timestamp = time.time()
                
                for pos in exchange_positions:
                    symbol = pos['symbol']
                    amt = float(pos.get('positionAmt', 0))
                    if amt != 0:
                        # Get cached data if available, otherwise create new
                        cached_data = self.positions_cache.get(symbol, {})
                        
                        # Check if cache is stale (older than 5 minutes)
                        cache_age = sync_timestamp - cached_data.get('last_sync', 0)
                        if cache_age > 300:  # 5 minutes
                            print(f"⚠️ Stale cache for {symbol} ({cache_age:.0f}s old) - refreshing")
                            cached_data = {}  # Clear stale cache
                        
                        current_positions[symbol] = {
                            'symbol': symbol,
                            'direction': 'LONG' if amt > 0 else 'SHORT',
                            'quantity': abs(amt),
                            'entry_price': float(pos.get('entryPrice', 0)),
                            'current_price': float(pos.get('markPrice', 0)),
                            'unrealized_pnl': float(pos.get('unRealizedProfit', 0)),
                            'position_size_usd': abs(amt) * float(pos.get('entryPrice', 0)),
                            'leverage': config.LEVERAGE,
                            'market_type': 'FUTURES',
                            # Preserve cached data with versioning
                            'entry_time': cached_data.get('entry_time', datetime.now(timezone.utc).isoformat()),
                            'stop_price': cached_data.get('stop_price', 0),
                            'target_price': cached_data.get('target_price', 0),
                            'tp_order_id': cached_data.get('tp_order_id'),
                            'sl_order_id': cached_data.get('sl_order_id'),
                            'signal_data': cached_data.get('signal_data', {}),
                            'last_sync': sync_timestamp,
                            'cache_version': cached_data.get('cache_version', 0) + 1  # Increment version
                        }
                        
                        # Update state
                        if symbol not in self.position_states:
                            self.position_states[symbol] = PositionState.ACTIVE
                
                # Update cache
                self.positions_cache = current_positions
                self.last_exchange_sync = sync_timestamp
                
                # Clean up states for closed positions
                for symbol in list(self.position_states.keys()):
                    if symbol not in current_positions and self.position_states[symbol] == PositionState.ACTIVE:
                        self.position_states[symbol] = PositionState.CLOSED
                
                return True
                
            except Exception as e:
                print(f"🚨 Error syncing with exchange: {str(e)}")
                return False

    def get_positions_from_exchange(self, market):
        """📊 Get current positions directly from exchange"""
        if not config.ENABLE_FUTURES:
            return {}
        
        try:
            positions = {}
            exchange_positions = market.get_position_risk()
            
            if exchange_positions:
                for pos in exchange_positions:
                    amt = float(pos.get('positionAmt', 0))
                    if amt != 0:
                        symbol = pos['symbol']
                        positions[symbol] = {
                            'symbol': symbol,
                            'direction': 'LONG' if amt > 0 else 'SHORT',
                            'quantity': abs(amt),
                            'entry_price': float(pos.get('entryPrice', 0)),
                            'current_price': float(pos.get('markPrice', 0)),
                            'unrealized_pnl': float(pos.get('unRealizedProfit', 0))
                        }
            
            return positions
            
        except Exception as e:
            print(f"🚨 Error getting positions from exchange: {str(e)}")
            return {}

    def is_state_transition_valid(self, symbol, new_state):
        """
        Validate if a state transition is allowed
        
        Valid transitions:
        NONE -> PENDING_ENTRY -> ENTERING -> ACTIVE -> PENDING_EXIT -> EXITING -> CLOSED
        """
        with self.position_lock:
            current_state = self.position_states.get(symbol, PositionState.NONE)
            
            # Define valid transitions
            valid_transitions = {
                PositionState.NONE: [PositionState.PENDING_ENTRY],
                PositionState.PENDING_ENTRY: [PositionState.ENTERING, PositionState.NONE],
                PositionState.ENTERING: [PositionState.ACTIVE, PositionState.ERROR, PositionState.NONE],
                PositionState.ACTIVE: [PositionState.PENDING_EXIT, PositionState.EXITING, PositionState.CLOSED],
                PositionState.PENDING_EXIT: [PositionState.EXITING, PositionState.ACTIVE],
                PositionState.EXITING: [PositionState.CLOSED, PositionState.ACTIVE],
                PositionState.CLOSED: [PositionState.NONE],
                PositionState.ERROR: [PositionState.NONE]
            }
            
            # Check if transition is valid
            allowed_states = valid_transitions.get(current_state, [])
            is_valid = new_state in allowed_states
            
            if not is_valid and current_state != new_state:  # Allow same state
                print(f"⚠️ Invalid state transition for {symbol}: {current_state.value} -> {new_state.value}")
            
            return is_valid or current_state == new_state

    def add_pending_order(self, symbol, order_data):
        """
        Add a pending order for tracking
        
        Args:
            symbol: Trading pair symbol
            order_data: Dictionary with order details
        """
        with self.position_lock:
            # Validate state transition
            if not self.is_state_transition_valid(symbol, PositionState.PENDING_ENTRY):
                print(f"⚠️ Cannot add pending order for {symbol} - invalid state")
                return False
            
            # Add timestamp
            order_data["order_time"] = time.time()
            order_data["order_id"] = None  # Will be set when order is placed
            
            # Store pending order
            self.pending_orders[symbol] = order_data
            self.position_states[symbol] = PositionState.PENDING_ENTRY
            
            # Save state
            self.save_positions()
            
            print(f"📝 Added pending order for {symbol}")
            # Track lifecycle event
            try:
                self.track_order_event(symbol, 'PENDING_ENTRY', {"order": order_data})
            except Exception:
                pass
            return True
    
    def load_positions(self):
        """📡 Load saved state and sync with exchange - FULLY UTC"""
        with self.position_lock:
            try:
                # Load saved data for trade history and stats
                if os.path.exists(config.POSITIONS_FILE):
                    with open(config.POSITIONS_FILE, 'r') as f:
                        data = json.load(f)
                    
                    # Load only non-position data
                    self.balance_usd = data.get("balance_usd", 0.0)
                    self.initial_balance_usd = data.get("initial_balance_usd", self.balance_usd)
                    self.all_trades = data.get("all_trades", [])
                    self.consecutive_losses = data.get("consecutive_losses", 0)
                    self.consecutive_wins = data.get("consecutive_wins", 0)
                    self.max_consecutive_wins = data.get("max_consecutive_wins", 0)
                    self.max_consecutive_losses = data.get("max_consecutive_losses", 0)
                    self.archived_trades_count = data.get("archived_trades_count", 0)
                    
                    # Load cached position data (for TP/SL info)
                    cached_positions = data.get("positions", {})
                    for symbol, pos_data in cached_positions.items():
                        self.positions_cache[symbol] = pos_data
                    
                    # Apply archival if too many trades
                    self._archive_old_trades()
                    
                    # FIX: Use UTC for today's date calculation
                    today_utc = datetime.now(timezone.utc).date().isoformat()
                    self.trades_today = []
                    
                    for trade in self.all_trades:
                        # Check if trade was closed today (using UTC)
                        if 'exit_time' in trade:
                            # Parse ISO format and ensure UTC
                            exit_time_str = trade['exit_time']
                            try:
                                # Handle both timezone-aware and naive timestamps
                                if 'T' in exit_time_str:
                                    # ISO format - extract date part
                                    exit_date_utc = exit_time_str.split('T')[0]
                                else:
                                    # Parse and convert to UTC
                                    exit_dt = datetime.fromisoformat(exit_time_str.replace('Z', '+00:00').split('+')[0])
                                    exit_date_utc = exit_dt.date().isoformat()
                                
                                if exit_date_utc == today_utc:
                                    self.trades_today.append(trade)
                            except Exception as e:
                                print(f"⚠️ Error parsing trade date: {str(e)}")
                    
                    # Initialize today's stats properly
                    self.daily_stats[today_utc] = {
                        "trades": 0, "wins": 0, "losses": 0, "pnl_usd": 0.0, "volume_usd": 0.0,
                        "win_rate": 0.0, "long_trades": 0, "short_trades": 0,
                        "futures_trades": 0, "spot_trades": 0,
                        "canceled_orders": 0, "filled_orders": 0
                    }
                    
                    # Rebuild ONLY from today's trades
                    for trade in self.trades_today:
                        self._update_daily_stats(trade)
                    
                    # Clean up old daily stats (keep last 30 days)
                    self._cleanup_old_daily_stats()
                    
                    # Rebuild all other stats
                    self._rebuild_performance_stats()
                    
                    print(f"📡 Loaded trading history - {len(self.all_trades)} trades in memory")
                    print(f"📁 Total trades (including archived): {len(self.all_trades) + self.archived_trades_count}")
                    print(f"📅 Today's trades (UTC): {len(self.trades_today)}")
                    print(f"⚠️ Position data will be synced from exchange")
                    
            except Exception as e:
                print(f"🚨 Error loading saved data: {str(e)}")

    def _archive_old_trades(self):
        """Archive old trades to prevent memory leak"""
        if len(self.all_trades) <= self.max_trades_in_memory:
            return
        
        # Calculate how many to archive
        trades_to_archive = len(self.all_trades) - self.max_trades_in_memory + 100  # Keep 100 buffer
        
        if trades_to_archive > 0:
            # Get oldest trades
            trades_to_save = self.all_trades[:trades_to_archive]
            
            # Create archive file
            archive_date = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
            archive_file = f"{self.archive_dir}/trades_archive_{archive_date}.json"
            
            try:
                # Save to archive
                with open(archive_file, 'w') as f:
                    json.dump({
                        'archived_at': datetime.now(timezone.utc).isoformat(),
                        'trades': trades_to_save,
                        'count': len(trades_to_save)
                    }, f, indent=2)
                
                # Remove from memory
                self.all_trades = self.all_trades[trades_to_archive:]
                self.archived_trades_count += trades_to_archive
                
                print(f"📁 Archived {trades_to_archive} old trades to {archive_file}")
                
                # Compress if possible
                try:
                    import gzip
                    with open(archive_file, 'rb') as f_in:
                        with gzip.open(f"{archive_file}.gz", 'wb') as f_out:
                            f_out.writelines(f_in)
                    os.remove(archive_file)
                    print(f"📦 Compressed archive to {archive_file}.gz")
                except:
                    pass
                    
            except Exception as e:
                print(f"⚠️ Failed to archive trades: {str(e)}")

    def _cleanup_old_daily_stats(self):
        """Clean up old daily stats to prevent memory leak"""
        try:
            # Keep only last 30 days
            cutoff_date = (datetime.now(timezone.utc).date() - timedelta(days=30)).isoformat()
            
            # Get keys to delete
            keys_to_delete = [k for k in self.daily_stats.keys() if k < cutoff_date]
            
            for key in keys_to_delete:
                del self.daily_stats[key]
            
            if keys_to_delete:
                print(f"🧹 Cleaned up {len(keys_to_delete)} old daily stat entries")
                
        except Exception as e:
            print(f"⚠️ Error cleaning daily stats: {str(e)}")

    def _cleanup_symbol_performance(self):
        """Clean up symbol performance to prevent memory leak"""
        if len(self.symbol_performance) <= self.max_symbols_tracked:
            return
        
        try:
            # Sort by last trade time (most recent first)
            # Keep only symbols with recent activity
            sorted_symbols = sorted(
                self.symbol_performance.items(),
                key=lambda x: x[1].get('last_trade_time', 0),
                reverse=True
            )
            
            # Keep top N symbols
            self.symbol_performance = dict(sorted_symbols[:self.max_symbols_tracked])
            
            print(f"🧹 Cleaned symbol performance - kept top {self.max_symbols_tracked} symbols")
            
        except Exception as e:
            print(f"⚠️ Error cleaning symbol performance: {str(e)}")

    def save_positions(self):
        """💾 Save current state (backup only, not source of truth)"""
        with self.position_lock:
            temp_path = None
            try:
                data = {
                    "positions": self.positions_cache,  # Save cache for TP/SL data
                    "pending_orders": self.pending_orders,
                    "balance_usd": self.balance_usd,
                    "initial_balance_usd": self.initial_balance_usd,
                    "all_trades": self.all_trades,
                    "consecutive_losses": self.consecutive_losses,
                    "consecutive_wins": self.consecutive_wins,
                    "max_consecutive_wins": self.max_consecutive_wins,
                    "max_consecutive_losses": self.max_consecutive_losses,
                    "last_saved": datetime.now().isoformat(),
                    "note": "Positions are cached data only - exchange is source of truth"
                }
                
                # Atomic write
                temp_fd, temp_path = tempfile.mkstemp(dir=f"./{config.DATA_DIR}")
                
                with os.fdopen(temp_fd, 'w') as f:
                    json.dump(data, f, indent=2)
                
                shutil.move(temp_path, config.POSITIONS_FILE)
                temp_path = None
                    
            except Exception as e:
                print(f"🚨 Error saving data: {str(e)}")
            finally:
                if temp_path and os.path.exists(temp_path):
                    try:
                        os.unlink(temp_path)
                    except:
                        pass
    
    def update_balance_usd(self, new_balance_usd):
        """💰 Update account balance"""
        with self.position_lock:
            self.balance_usd = new_balance_usd
            if self.initial_balance_usd == 0:
                self.initial_balance_usd = new_balance_usd
            self.save_positions()

    def reconcile_with_exchange(self, market, notifier):
        """🔄 FAST reconciliation with exchange"""
        with self.position_lock:
            try:
                # Quick sync
                if not self.sync_with_exchange(market):
                    notifier.quantum_log("⚠️ Failed to sync with exchange", "WARNING")
                    return False
                
                # ENHANCED: Post-sync OCO verification
                self._verify_oco_after_sync(market)
                
                # Get current exchange positions
                exchange_positions = self.get_positions_from_exchange(market)
                
                # Track changes
                positions_removed = 0
                exit_notifications_sent = 0
                
                # FAST CHECK: Find closed positions
                closed_positions = []
                for symbol in list(self.positions_cache.keys()):
                    if symbol not in exchange_positions:
                        closed_positions.append(symbol)
                        positions_removed += 1
                
                # Process closed positions quickly
                for symbol in closed_positions:
                    notifier.quantum_log(f"💀 Position closed: {symbol}", "INFO")
                    
                    cached_pos = self.positions_cache.get(symbol, {})
                    
                    # Quick exit detection from recent orders (last 5 only for speed)
                    exit_price = cached_pos.get('current_price', cached_pos.get('entry_price', 0))
                    exit_type = "UNKNOWN"
                    reason = "Position Closed (Exchange)"
                    
                    try:
                        # FAST: Only check last 5 orders
                        recent_orders = market.get_recent_orders(symbol, limit=5)
                        
                        for order in recent_orders:
                            if order['status'] == 'FILLED' and order.get('reduceOnly'):
                                # Quick type detection
                                if order['type'] == 'LIMIT':
                                    exit_type = "TAKE_PROFIT"
                                    reason = "Take Profit Hit"
                                elif order['type'] in ['STOP_MARKET', 'STOP']:
                                    exit_type = "STOP_LOSS"
                                    reason = "Stop Loss Hit"
                                else:
                                    exit_type = "MANUAL"
                                    reason = "Manual Exit"
                                
                                exit_price = float(order.get('avgPrice', order.get('price', exit_price)))
                                break
                                
                    except Exception as e:
                        pass  # Don't slow down for order checks
                    
                    # Quick P&L calculation
                    if cached_pos and 'entry_price' in cached_pos and 'quantity' in cached_pos:
                        quantity = cached_pos['quantity']
                        entry_price = cached_pos['entry_price']
                        
                        if cached_pos.get('direction') == 'LONG':
                            pnl_usd = (exit_price - entry_price) * quantity
                        else:
                            pnl_usd = (entry_price - exit_price) * quantity
                    else:
                        pnl_usd = 0
                    
                    # Close position
                    trade_data = self.close_position(
                        symbol, exit_price, pnl_usd, reason,
                        additional_info={"exit_type": exit_type}
                    )
                    
                    # Send notification
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
                        
                        notifier.send_strike_exit_alert(exit_alert_data)
                        exit_notifications_sent += 1
                
                # Quick check for new positions (orphans)
                positions_added = 0
                for symbol, exchange_pos in exchange_positions.items():
                    if symbol not in self.positions_cache:
                        notifier.quantum_log(f"🆕 Found orphan position: {symbol}", "WARNING")
                        self._adopt_orphan_position(symbol, exchange_pos, market)
                        positions_added += 1
                
                self.save_positions()
                
                # Only log if changes occurred
                if positions_added > 0 or positions_removed > 0:
                    notifier.quantum_log(
                        f"✅ Reconciliation: +{positions_added} -{positions_removed} positions",
                        "INFO"
                    )
                
                return True
                
            except Exception as e:
                notifier.quantum_log(f"🚨 Reconciliation error: {str(e)}", "ERROR")
                return False
            
    def _log_writer(self):
        """Worker thread with IMPROVED LOG PERSISTENCE"""
        consecutive_failures = 0
        max_failures = 5
        
        while self.logging_active:
            try:
                # Use timeout to handle spurious wakeups
                try:
                    log_entry = self.log_queue.get(timeout=1)
                except queue.Empty:
                    continue
                    
                if log_entry is None:  # Sentinel value to stop thread
                    break
                
                # Ensure directory exists
                os.makedirs(os.path.dirname(config.TRADES_LOG_FILE), exist_ok=True)
                
                # Write with maximum persistence
                try:
                    with open(config.TRADES_LOG_FILE, 'a', encoding='utf-8') as f:
                        f.write(log_entry + "\n")
                        f.flush()
                        os.fsync(f.fileno())  # Force write to disk
                    
                    # Reset failure counter on success
                    consecutive_failures = 0
                    
                except Exception as write_error:
                    consecutive_failures += 1
                    print(f"🚨 Log write error #{consecutive_failures}: {str(write_error)}")
                    
                    # FIX: Add to failed queue for retry
                    self.failed_log_queue.append({
                        'entry': log_entry,
                        'timestamp': time.time(),
                        'attempts': 1
                    })
                    
                    if consecutive_failures >= max_failures:
                        print(f"🚨 Log writer failing repeatedly - switching to emergency mode")
                        # Try emergency log
                        self._emergency_log_trade("LOG_FAILURE", "", {"entry": log_entry})
                        consecutive_failures = 0
                        time.sleep(1)
                        
            except Exception as e:
                print(f"🚨 Log writer thread error: {str(e)}")
                time.sleep(1)

    def _write_log_entry_sync(self, log_entry):
        """Write log entry synchronously with retry and verification"""
        max_attempts = 3
        for attempt in range(max_attempts):
            try:
                # Ensure directory exists
                os.makedirs(os.path.dirname(config.TRADES_LOG_FILE), exist_ok=True)
                
                # Write the entry
                with open(config.TRADES_LOG_FILE, 'a', buffering=1) as f:
                    f.write(log_entry + '\n')
                    f.flush()
                    os.fsync(f.fileno())  # Force write to disk
                
                # Verify it was written
                if self._verify_log_entry(log_entry):
                    print(f"✅ Log entry written and verified")
                    return True
                else:
                    print(f"⚠️ Log entry written but verification failed")
                    
            except Exception as e:
                print(f"🚨 Write attempt {attempt + 1}/{max_attempts} failed: {str(e)}")
                if attempt < max_attempts - 1:
                    time.sleep(0.5)
        
        raise Exception(f"Failed to write log entry after {max_attempts} attempts!")

    def check_position_limits_before_order(self, market=None):
        """🚨 Check if we can place another order - ATOMIC WITH RESERVATION"""
        with self.position_lock:
            try:
                # Get exchange positions
                if market and config.ENABLE_FUTURES:
                    exchange_positions = self.get_positions_from_exchange(market)
                    exchange_count = len(exchange_positions)
                else:
                    exchange_count = 0
                
                # Count pending orders (exclude expired ones)
                current_time = time.time()
                pending_count = 0
                for symbol, order_data in self.pending_orders.items():
                    order_age = current_time - order_data.get('order_time', current_time)
                    if order_age < 300:  # Only count orders less than 5 minutes old
                        pending_count += 1
                
                # Count reserved slots (for orders being placed right now)
                reserved_count = len([s for s in self.position_states.values() 
                                    if s == PositionState.PENDING_ENTRY])
                
                # CRITICAL: Total committed includes all three
                total_committed = exchange_count + pending_count
                
                # Check limit
                can_trade = total_committed < config.MAX_TOTAL_POSITIONS
                
                print(f"📊 POSITION LIMIT CHECK:")
                print(f"   Exchange positions: {exchange_count}")
                print(f"   Pending orders: {pending_count}")
                print(f"   Reserved slots: {reserved_count}")
                print(f"   Total committed: {total_committed}/{config.MAX_TOTAL_POSITIONS}")
                print(f"   Can trade: {'YES' if can_trade else 'NO'}")
                
                if not can_trade:
                    print(f"⌛ POSITION LIMIT REACHED: Cannot open new positions")
                
                # If we can trade, immediately reserve a slot
                if can_trade:
                    # Generate temporary reservation ID
                    temp_id = f"RESERVE_{int(time.time()*1000)}"
                    self.position_states[temp_id] = PositionState.PENDING_ENTRY
                    # Return the reservation ID so it can be updated later
                    return temp_id
                
                return None
                
            except Exception as e:
                print(f"⚠️ Error checking position limits: {str(e)}")
                # Conservative - assume we can't trade on error
                return None

    def update_reservation(self, reservation_id, symbol):
        """Update a position reservation with actual symbol"""
        with self.position_lock:
            if reservation_id and reservation_id in self.position_states:
                # Remove old reservation
                del self.position_states[reservation_id]
                # Add actual symbol state
                self.position_states[symbol] = PositionState.PENDING_ENTRY
                return True
            return False

    def order_filled(self, symbol, order_result):
        """✅ Handle order fill - FIXED: No stale stop/target prices"""
        with self.position_lock:
            if symbol not in self.pending_orders:
                return False
            
            if order_result.get('status') != 'FILLED':
                print(f"⚠️ Order not filled: {symbol} Status: {order_result.get('status')}")
                return False
            
            # Get pending data
            pending_data = self.pending_orders[symbol]
            
            # Create position entry in cache
            position_data = {
                "symbol": symbol,
                "direction": pending_data["direction"],
                "entry_time": datetime.now(timezone.utc).isoformat(),
                "entry_timestamp": time.time(),
                "entry_price": order_result["price"],  # Use actual fill price
                "quantity": order_result["quantity"],
                # CRITICAL FIX: Don't use stale stop/target prices!
                # These will be set by _execute_entry after recalculation
                "stop_price": None,  # Will be set by _execute_entry
                "target_price": None,  # Will be set by _execute_entry
                "position_size_usd": order_result["quantity"] * order_result["price"],
                "risk_usd": pending_data.get("risk_usd", 0),
                "pair_config": pending_data.get("pair_config", {}),
                "leverage": config.LEVERAGE if config.ENABLE_FUTURES else 1,
                "market_type": "FUTURES" if config.ENABLE_FUTURES else "SPOT",
                "tp_order_id": None,
                "sl_order_id": None,
                # The _execute_entry function will handle placing exit orders
                "needs_exit_orders": False,  # IMPORTANT: Set to False
                "signal_data": pending_data.get("signal_data", {}),
                "last_sync": time.time(),
                "cache_version": 1
            }
            
            # Update state and cache
            del self.pending_orders[symbol]
            self.positions_cache[symbol] = position_data
            self.position_states[symbol] = PositionState.ACTIVE
            
            # Update stats
            today = datetime.now(timezone.utc).date().isoformat()
            self.daily_stats[today]["filled_orders"] += 1
            
            # Log trade entry
            self._log_trade("ENTRY", symbol, position_data)
            
            self.save_positions()
            
            print(f"✅ Position opened: {symbol} {pending_data['direction']} @ ${order_result['price']:.4f}")
            print(f"📝 Note: Stop/target prices will be set by executor after recalculation")
            # Track lifecycle event
            try:
                self.track_order_event(symbol, 'ENTRY_FILLED', {"order_result": order_result})
            except Exception:
                pass
            return True

    def open_position(self, symbol, action, entry_price, quantity, stop_price, target_price, position_sizing):
        """📈 Record a new position (after confirming with exchange)"""
        with self.position_lock:
            position_data = {
                "symbol": symbol,
                "direction": action,
                "entry_time": datetime.now(timezone.utc).isoformat(),
                "entry_timestamp": time.time(),
                "entry_price": entry_price,
                "quantity": quantity,
                "stop_price": stop_price,
                "target_price": target_price,
                "position_size_usd": position_sizing.get("position_size_usd", 0),
                "risk_usd": position_sizing.get("risk_usd", 0),
                "leverage": config.LEVERAGE if config.ENABLE_FUTURES else 1,
                "market_type": "FUTURES" if config.ENABLE_FUTURES else "SPOT",
                "tp_order_id": None,
                "sl_order_id": None,
                "needs_exit_orders": config.AUTO_PLACE_EXIT_ORDERS and config.ENABLE_FUTURES,
                "status": "ACTIVE",
                "unrealized_pnl": 0.0,
                "current_price": entry_price,
                "last_sync": time.time()
            }
            
            self.positions_cache[symbol] = position_data
            self.position_states[symbol] = PositionState.ACTIVE
            self._log_trade("ENTRY", symbol, position_data)
            self.save_positions()
            
            print(f"✅ PORTFOLIO: Position recorded for {symbol} {action} @ ${entry_price:.4f}")
            return position_data

    def get_positions_needing_exit_orders(self):
        """🔍 Get list of positions that need exit orders placed"""
        with self.position_lock:
            positions_needing_orders = []
            
            for symbol, position in self.positions_cache.items():
                if position.get("needs_exit_orders", False):
                    if not position.get("tp_order_id") or not position.get("sl_order_id"):
                        positions_needing_orders.append((symbol, position))
            
            return positions_needing_orders
    
    def mark_exit_orders_placed(self, symbol):
        """✅ Mark that exit orders have been successfully placed"""
        with self.position_lock:
            if symbol in self.positions_cache:
                self.positions_cache[symbol]["needs_exit_orders"] = False
                self.save_positions()
                print(f"✅ Exit orders marked as placed for {symbol}")

    def update_exit_order_ids(self, symbol, tp_order_id=None, sl_order_id=None):
        """📝 Update exit order IDs"""
        with self.position_lock:
            if symbol not in self.positions_cache:
                print(f"⚠️ Cannot update exit orders - no position cached for {symbol}")
                return False
            
            position = self.positions_cache[symbol]
            updated = False
            
            if tp_order_id is not None:
                position["tp_order_id"] = tp_order_id
                updated = True
                print(f"📝 Updated TP order ID for {symbol}: {tp_order_id}")
                
            if sl_order_id is not None:
                position["sl_order_id"] = sl_order_id
                updated = True
                print(f"📝 Updated SL order ID for {symbol}: {sl_order_id}")
            
            if updated:
                position["last_verified"] = time.time()
                self.save_positions()
                # If both TP and SL IDs are now present, mark OCO placed
                try:
                    if position.get("tp_order_id") and position.get("sl_order_id"):
                        self.track_order_event(symbol, 'OCO_PLACED', {
                            "tp_order_id": position.get("tp_order_id"),
                            "sl_order_id": position.get("sl_order_id")
                        })
                except Exception:
                    pass
                
            return True

    def cancel_unfilled_order(self, symbol, reason="TIMEOUT"):
        """❌ Cancel unfilled order"""
        with self.position_lock:
            if symbol not in self.pending_orders:
                return False
            
            # Update stats
            today = date.today().isoformat()
            self.daily_stats[today]["canceled_orders"] += 1
            self.symbol_performance[symbol]["canceled_orders"] += 1
            
            # Update state
            self.position_states[symbol] = PositionState.NONE
            
            # Remove from pending
            del self.pending_orders[symbol]
            self.save_positions()
            
            print(f"❌ Order canceled: {symbol} | Reason: {reason}")
            return True

    def monitor_unfilled_orders(self, market, notifier):
        """⏰ Monitor and handle unfilled orders - WITH PROPER NOTIFICATIONS"""
        filled_orders_data = []
        
        with self.position_lock:
            pending_copy = list(self.pending_orders.items())
        
        if not pending_copy:
            return filled_orders_data
        
        current_time = time.time()
        timeout_seconds = config.ORDER_FILL_TIMEOUT
        
        for symbol, order_data in pending_copy:
            order_age = current_time - order_data.get("order_time", current_time)
            order_id = order_data.get("order_id")
            
            if not order_id:
                continue
            
            # Update state
            with self.position_lock:
                if self.position_states.get(symbol) == PositionState.PENDING_ENTRY:
                    self.position_states[symbol] = PositionState.ENTERING
            
            order_status = market.cache_order_status_fresh(symbol, order_id, max_age=0.5)
            
            if order_status == 'FILLED':
                # CRITICAL: Build complete fill data for notification
                notifier.quantum_log(f"✅ Fill detected for {symbol} (Order ID: {order_id})", "SUCCESS")
                
                # Get fill details from exchange
                fill_info = market.get_order_fills(symbol, order_id)
                if fill_info:
                    fill_price = fill_info["avg_price"]
                    actual_quantity = fill_info["total_qty"]
                else:
                    fill_price = order_data.get("entry_price")
                    actual_quantity = order_data.get("quantity")
                
                # Calculate slippage
                target_price = order_data.get("entry_price", fill_price)
                slippage = abs(fill_price - target_price) / target_price if target_price > 0 else 0
                
                notifier.quantum_log(
                    f"✅ ORDER FILLED: {symbol} @ ${fill_price:.4f} "
                    f"(target: ${target_price:.4f}, slippage: {slippage*100:.2f}%)",
                    "SUCCESS"
                )
                
                # Package all data for the bot to process
                filled_orders_data.append({
                    "symbol": symbol,
                    "pending_data": order_data,
                    "fill_price": fill_price,
                    "actual_quantity": actual_quantity,
                    "slippage": slippage,
                    "order_age": order_age
                })
                
                # Process the fill in portfolio
                order_result = {
                    "status": "FILLED",
                    "symbol": symbol,
                    "price": fill_price,
                    "quantity": actual_quantity
                }
                
                if self.order_filled(symbol, order_result):
                    notifier.quantum_log(
                        f"✅ Position opened: {symbol} {order_data['direction']} @ ${fill_price:.4f}",
                        "SUCCESS"
                    )
                else:
                    notifier.quantum_log(
                        f"❌ Failed to process fill for {symbol}",
                        "ERROR"
                    )
                    
            elif order_status == 'CANCELED':
                self.cancel_unfilled_order(symbol, "CANCELED_BY_EXCHANGE")
                notifier.quantum_log(f"❌ Order cancelled by exchange: {symbol}", "WARNING")
                
            elif order_status in ['REJECTED', 'EXPIRED']:
                self.cancel_unfilled_order(symbol, f"ORDER_{order_status}")
                notifier.quantum_log(f"❌ Order {order_status.lower()}: {symbol}", "WARNING")
                
            elif order_age > timeout_seconds:
                notifier.quantum_log(f"⏰ Order timeout: {symbol} (Age: {order_age:.0f}s)", "WARNING")
                
                # Try to cancel the order
                if market.cancel_order(symbol, order_id):
                    self.cancel_unfilled_order(symbol, "TIMEOUT")
                    notifier.quantum_log(f"✅ Cancelled timed out order: {symbol}", "INFO")
                else:
                    notifier.quantum_log(f"⚠️ Failed to cancel timed out order: {symbol}", "WARNING")
        
        # Return filled orders for processing
        return filled_orders_data

    def update_position(self, symbol, current_price, unrealized_pnl):
        """📊 Update cached position data"""
        with self.position_lock:
            if symbol in self.positions_cache:
                self.positions_cache[symbol]["current_price"] = current_price
                self.positions_cache[symbol]["unrealized_pnl"] = unrealized_pnl

    def emit_close_event_once(self, symbol, exit_type, source, trade_data=None):
        """🎯 Idempotent close event emitter to guarantee notifier/logger parity"""
        event_key = f"{symbol}_{exit_type}_{int(time.time() / 10)}"  # 10-second window
        
        with self.position_lock:
            # Check if this close event was already emitted
            if hasattr(self, '_emitted_close_events'):
                if event_key in self._emitted_close_events:
                    print(f"⚠️ Close event already emitted for {symbol} - skipping duplicate")
                    return None
            else:
                self._emitted_close_events = set()
            
            # Mark this event as emitted
            self._emitted_close_events.add(event_key)
            
            # Clean up old events (older than 1 hour)
            current_time = int(time.time() / 10)
            self._emitted_close_events = {
                key for key in self._emitted_close_events 
                if int(key.split('_')[-1]) > current_time - 360  # 1 hour = 360 * 10 seconds
            }
            
            print(f"🎯 Emitting close event: {symbol} {exit_type} from {source}")
            return trade_data

    def close_position(self, symbol, exit_price, pnl_usd, reason, additional_info=None):
        """🚪 Close a position with PROPER STATE MANAGEMENT and IDEMPOTENT EVENTS"""
        with self.position_lock:
            # ENHANCED: Check if position was already closed to prevent duplicate events
            if symbol in self.position_states and self.position_states[symbol] == PositionState.CLOSED:
                print(f"⚠️ Position {symbol} already closed - skipping duplicate close event")
                return None
            
            print(f"\n{'='*60}")
            print(f"📊 CLOSING POSITION: {symbol}")
            print(f"   Exit Price: ${exit_price:.4f}")
            print(f"   P&L: ${pnl_usd:.2f}")
            print(f"   Reason: {reason}")
            print(f"{'='*60}")
            
            # Validate state transition
            current_state = self.position_states.get(symbol, PositionState.NONE)
            if not self.is_state_transition_valid(symbol, PositionState.CLOSED):
                print(f"⚠️ Invalid state transition for {symbol}: {current_state} -> CLOSED")
            
            # Get position from cache
            position = self.positions_cache.get(symbol)
            
            # If no cached data, try to reconstruct
            if not position:
                print(f"⚠️ No cached data for {symbol}, using minimal data")
                position = {
                    "entry_time": datetime.now(timezone.utc).isoformat(),
                    "direction": "UNKNOWN",
                    "entry_price": exit_price,
                    "quantity": 0,
                    "position_size_usd": abs(pnl_usd) * 10,  # Rough estimate
                    "leverage": config.LEVERAGE if config.ENABLE_FUTURES else 1,
                    "market_type": "FUTURES" if config.ENABLE_FUTURES else "SPOT"
                }
            
            # Extract exit type
            exit_type = "UNKNOWN"
            if additional_info:
                if isinstance(additional_info, dict):
                    exit_type = additional_info.get("exit_type", "UNKNOWN")
                elif isinstance(additional_info, str):
                    exit_type = additional_info
            
            # Calculate hold time
            try:
                hold_time_hours = self._calculate_hold_time_hours(position.get("entry_time", datetime.now(timezone.utc).isoformat()))
            except:
                hold_time_hours = 0.0
            
            # COMMISSION CALCULATION
            entry_commission_rate = 0.0004  # 0.04% taker
            exit_commission_rate = 0.0004   # 0.04% taker
            
            # Calculate commission in USD
            position_size_usd = float(position.get("position_size_usd", 0))
            entry_commission = position_size_usd * entry_commission_rate
            exit_commission = position_size_usd * exit_commission_rate
            total_commission = entry_commission + exit_commission
            
            # Adjust P&L for commission
            net_pnl_usd = pnl_usd - total_commission
            
            print(f"💰 Commission: Entry ${entry_commission:.2f} + Exit ${exit_commission:.2f} = ${total_commission:.2f}")
            print(f"📊 Net P&L after commission: ${net_pnl_usd:.2f}")
            
            # Create complete trade record
            trade = {
                "symbol": symbol,
                "direction": position.get("direction", "UNKNOWN"),
                "entry_time": position.get("entry_time", datetime.now(timezone.utc).isoformat()),
                "exit_time": datetime.now(timezone.utc).isoformat(),
                "entry_price": float(position.get("entry_price", exit_price)),
                "exit_price": float(exit_price),
                "quantity": float(position.get("quantity", 0)),
                "position_size_usd": position_size_usd,
                "pnl_usd": float(pnl_usd),
                "commission_usd": total_commission,
                "net_pnl_usd": net_pnl_usd,
                "pnl_pct": (pnl_usd / position_size_usd) * 100 if position_size_usd > 0 else 0,
                "net_pnl_pct": (net_pnl_usd / position_size_usd) * 100 if position_size_usd > 0 else 0,
                "exit_reason": str(reason),
                "exit_type": str(exit_type),
                "hold_time_hours": float(hold_time_hours),
                "hold_time_bars": int(hold_time_hours * 4),  # 15-min bars
                "market_type": position.get("market_type", "FUTURES" if config.ENABLE_FUTURES else "SPOT"),
                "leverage": position.get("leverage", config.LEVERAGE if config.ENABLE_FUTURES else 1)
            }
            
            # Update trade history
            self.all_trades.append(trade)
            self.trades_today.append(trade)
            
            # Archive old trades if needed
            self._archive_old_trades()
            
            # Update consecutive tracking (use net P&L)
            if net_pnl_usd > 0:
                self.consecutive_wins += 1
                self.consecutive_losses = 0
                self.max_consecutive_wins = max(self.max_consecutive_wins, self.consecutive_wins)
            else:
                self.consecutive_losses += 1
                self.consecutive_wins = 0
                self.max_consecutive_losses = max(self.max_consecutive_losses, self.consecutive_losses)
            
            # Update stats with net values
            self._update_daily_stats(trade)
            self._update_performance_stats(trade)
            
            # LOG THE EXIT - CRITICAL
            print(f"📝 Logging exit to trades.log...")
            try:
                self._log_trade("EXIT", symbol, trade)
                print(f"✅ Exit logged successfully")
            except Exception as e:
                print(f"🚨 Primary log failed: {str(e)}")
                # Emergency logging as fallback
                self._emergency_log_trade("EXIT", symbol, trade)
            
            # Remove from cache and update state
            if symbol in self.positions_cache:
                del self.positions_cache[symbol]
            
            # Clean up any reservation states
            temp_reservations = [k for k, v in self.position_states.items() 
                            if k.startswith("RESERVE_") and v == PositionState.PENDING_ENTRY]
            for reservation in temp_reservations:
                del self.position_states[reservation]
            
            # Update state
            self.position_states[symbol] = PositionState.CLOSED
            
            # Clean up symbol performance if too many
            self._cleanup_symbol_performance()
            
            # Save positions
            try:
                self.save_positions()
            except Exception as e:
                print(f"⚠️ Failed to save positions: {str(e)}")
            
            print(f"✅ Position closed successfully")
            print(f"{'='*60}\n")
            
            # Use idempotent close event emitter
            trade = self.emit_close_event_once(symbol, exit_type, "portfolio.close_position", trade)
            
            # Track lifecycle event
            try:
                self.track_order_event(symbol, 'CLOSED', {"trade": trade, "exit_type": exit_type, "reason": reason})
            except Exception:
                pass

            # Return trade data for notification
            return trade

    # === ORDER LIFECYCLE TRACKING ===
    def track_order_event(self, symbol, event, data=None):
        """Record an order lifecycle event for a symbol in a thread-safe manner"""
        timestamp = time.time()
        with self._lifecycle_lock:
            lifecycle = self._order_lifecycle.get(symbol)
            if not lifecycle:
                lifecycle = {"events": [], "state": "INIT", "timestamps": {}}
                self._order_lifecycle[symbol] = lifecycle
            lifecycle["events"].append({"event": event, "time": timestamp, "data": data or {}})
            lifecycle["timestamps"][event] = timestamp
            # Map events to states
            event_to_state = {
                'PENDING_ENTRY': 'PENDING_ENTRY',
                'ENTRY_FILLED': 'ENTRY_FILLED',
                'OCO_PLACED': 'OCO_PLACED',
                'TP_FILLED': 'TP_FILLED',
                'SL_FILLED': 'SL_FILLED',
                'CLOSED': 'CLOSED'
            }
            lifecycle["state"] = event_to_state.get(event, lifecycle["state"])  # keep previous if unknown

    def get_order_lifecycle(self, symbol):
        """Get the lifecycle record for a symbol"""
        with self._lifecycle_lock:
            return dict(self._order_lifecycle.get(symbol, {"events": [], "state": "INIT", "timestamps": {}}))
    
    def get_daily_pnl_usd(self):
        """💰 Get today's P&L - UTC BASED"""
        with self.position_lock:
            today_utc = datetime.now(timezone.utc).date().isoformat()
            
            # Calculate from actual today's trades only (UTC)
            today_pnl = 0.0
            for trade in self.trades_today:
                # Make sure this trade is actually from today
                if 'exit_time' in trade:
                    try:
                        exit_time_str = trade['exit_time']
                        if 'T' in exit_time_str:
                            trade_date = exit_time_str.split('T')[0]
                        else:
                            exit_dt = datetime.fromisoformat(exit_time_str.replace('Z', '+00:00').split('+')[0])
                            trade_date = exit_dt.date().isoformat()
                        
                        if trade_date == today_utc:
                            # Use net P&L if available
                            today_pnl += trade.get('net_pnl_usd', trade.get('pnl_usd', 0))
                    except:
                        pass
            
            return today_pnl

    def get_order_fill_rate(self):
        """📊 Get order fill rate"""
        with self.position_lock:
            today_stats = self.daily_stats[date.today().isoformat()]
            filled = today_stats.get("filled_orders", 0)
            canceled = today_stats.get("canceled_orders", 0)
            total = filled + canceled
            return (filled / total * 100) if total > 0 else 100.0

    def get_summary(self):
        """🌌 Get ACCURATE portfolio summary with COMMISSIONS"""
        with self.position_lock:
            total_trades = len(self.all_trades)
            if total_trades == 0:
                return self._get_empty_summary()
            
            # Use net P&L for calculations
            winning_trades = [t for t in self.all_trades if t.get("net_pnl_usd", t.get("pnl_usd", 0)) > 0]
            losing_trades = [t for t in self.all_trades if t.get("net_pnl_usd", t.get("pnl_usd", 0)) <= 0]
            
            win_rate = (len(winning_trades) / total_trades) * 100
            
            # Calculate with net P&L
            total_profit = sum(t.get("net_pnl_usd", t.get("pnl_usd", 0)) for t in winning_trades)
            total_loss = abs(sum(t.get("net_pnl_usd", t.get("pnl_usd", 0)) for t in losing_trades))
            profit_factor = total_profit / total_loss if total_loss > 0 else 999.99
            
            avg_win = total_profit / len(winning_trades) if winning_trades else 0
            avg_loss = total_loss / len(losing_trades) if losing_trades else 0
            
            total_pnl = total_profit - total_loss
            total_commissions = sum(t.get("commission_usd", 0) for t in self.all_trades)
            total_return_pct = ((self.balance_usd / self.initial_balance_usd) - 1) * 100 if self.initial_balance_usd > 0 else 0
            
            # TODAY's metrics (UTC based)
            today_utc = datetime.now(timezone.utc).date().isoformat()
            
            # Filter for ACTUAL today's trades
            today_trades = []
            today_pnl = 0.0
            today_wins = 0
            today_commissions = 0.0
            
            for trade in self.all_trades:
                if 'exit_time' in trade:
                    try:
                        exit_time_str = trade['exit_time']
                        if 'T' in exit_time_str:
                            trade_date = exit_time_str.split('T')[0]
                        else:
                            exit_dt = datetime.fromisoformat(exit_time_str.replace('Z', '+00:00').split('+')[0])
                            trade_date = exit_dt.date().isoformat()
                        
                        if trade_date == today_utc:
                            today_trades.append(trade)
                            today_pnl += trade.get('net_pnl_usd', trade.get('pnl_usd', 0))
                            today_commissions += trade.get('commission_usd', 0)
                            if trade.get('net_pnl_usd', trade.get('pnl_usd', 0)) > 0:
                                today_wins += 1
                    except:
                        pass
            
            today_trade_count = len(today_trades)
            today_win_rate = (today_wins / today_trade_count * 100) if today_trade_count > 0 else 0
            
            # Get today's order stats
            today_stats = self.daily_stats.get(today_utc, {})
            today_filled_orders = today_stats.get("filled_orders", 0)
            today_canceled_orders = today_stats.get("canceled_orders", 0)
            total_orders = today_filled_orders + today_canceled_orders
            order_fill_rate = (today_filled_orders / total_orders * 100) if total_orders > 0 else 100.0
            
            # Count active positions
            active_positions = len(self.positions_cache)
            positions_with_exit_orders = sum(
                1 for p in self.positions_cache.values()
                if p.get("tp_order_id") and p.get("sl_order_id")
            )
            
            return {
                "total_trades": total_trades,
                "active_positions": active_positions,
                "pending_orders": len(self.pending_orders),
                "total_committed": active_positions + len(self.pending_orders),
                "position_utilization": ((active_positions + len(self.pending_orders)) / config.MAX_TOTAL_POSITIONS) * 100,
                "positions_with_exit_orders": positions_with_exit_orders,
                "exit_order_coverage": (positions_with_exit_orders / active_positions * 100) if active_positions else 100.0,
                "win_rate": win_rate,
                "profit_factor": profit_factor,
                "total_pnl_usd": total_pnl,
                "total_commissions_usd": total_commissions,
                "total_return_pct": total_return_pct,
                "average_win_usd": avg_win,
                "average_loss_usd": avg_loss,
                "best_trade_usd": max(self.all_trades, key=lambda x: x.get("net_pnl_usd", x.get("pnl_usd", 0))).get("net_pnl_usd", 0) if self.all_trades else 0,
                "worst_trade_usd": min(self.all_trades, key=lambda x: x.get("net_pnl_usd", x.get("pnl_usd", 0))).get("net_pnl_usd", 0) if self.all_trades else 0,
                "avg_hold_time_hours": sum(t.get("hold_time_hours", 0) for t in self.all_trades) / total_trades,
                "consecutive_wins": self.consecutive_wins,
                "consecutive_losses": self.consecutive_losses,
                "max_consecutive_wins": self.max_consecutive_wins,
                "max_consecutive_losses": self.max_consecutive_losses,
                "today_trades": today_trade_count,
                "today_pnl_usd": today_pnl,
                "today_commissions_usd": today_commissions,
                "today_win_rate": today_win_rate,
                "today_wins": today_wins,
                "today_filled_orders": today_filled_orders,
                "today_canceled_orders": today_canceled_orders,
                "order_fill_rate": order_fill_rate,
                "balance_usd": self.balance_usd,
                "initial_balance_usd": self.initial_balance_usd,
                "market_type": "FUTURES" if config.ENABLE_FUTURES else "SPOT",
                "symbol_performance": dict(self.symbol_performance),
                "last_sync_age": time.time() - self.last_exchange_sync if self.last_exchange_sync else 999
            }

    def get_position_state(self, symbol):
        """Get current state of a position"""
        with self.position_lock:
            return self.position_states.get(symbol, PositionState.NONE)

    def validate_and_fix_states(self):
        """Validate and fix any invalid position states - IMPROVED"""
        with self.position_lock:
            # Clean up old reservations (older than 5 minutes)
            current_time = time.time()
            reservations_to_clean = []
            
            for key, state in list(self.position_states.items()):  # FIX: Use list() to avoid runtime error
                if key.startswith("RESERVE_"):
                    # Extract timestamp from reservation ID
                    try:
                        reserve_time = int(key.split("_")[1]) / 1000
                        if current_time - reserve_time > 300:  # 5 minutes
                            reservations_to_clean.append(key)
                    except:
                        reservations_to_clean.append(key)  # Clean invalid reservations
            
            for key in reservations_to_clean:
                del self.position_states[key]
                print(f"🧹 Cleaned stale reservation: {key}")
            
            # Validate states match actual positions
            for symbol in list(self.position_states.keys()):
                if not symbol.startswith("RESERVE_"):
                    # Check if state makes sense
                    state = self.position_states[symbol]
                    has_position = symbol in self.positions_cache
                    has_pending = symbol in self.pending_orders
                    
                    # Fix inconsistencies
                    if state == PositionState.ACTIVE and not has_position:
                        print(f"⚠️ Fixing state for {symbol}: ACTIVE but no position")
                        self.position_states[symbol] = PositionState.CLOSED
                    elif state == PositionState.PENDING_ENTRY and not has_pending:
                        print(f"⚠️ Fixing state for {symbol}: PENDING but no order")
                        self.position_states[symbol] = PositionState.NONE
                    elif state == PositionState.ERROR:
                        # FIX: Auto-recover from ERROR state after 10 minutes
                        # This requires tracking when error occurred - for now just reset
                        print(f"⚠️ Resetting ERROR state for {symbol}")
                        self.position_states[symbol] = PositionState.NONE

    # === PRIVATE HELPER METHODS ===

    def _adopt_orphan_position(self, symbol, exchange_data, market):
        """🆕 Adopt an orphan position with BETTER RECONSTRUCTION"""
        try:
            # Try to get more info from recent trades
            trade_info = {}
            try:
                trades = market.get_trade_history(symbol, limit=100)
                if trades:
                    # Find the opening trade (first trade without realizedPnl)
                    for trade in reversed(trades):  # Start from oldest
                        if float(trade.get('realizedPnl', 0)) == 0:
                            trade_info = {
                                'actual_entry_price': float(trade['price']),
                                'actual_entry_time': datetime.fromtimestamp(trade['time']/1000).isoformat(),
                                'entry_order_type': trade.get('maker', False),  # True if maker
                            }
                            break
            except Exception as e:
                print(f"⚠️ Could not fetch trade history for {symbol}: {str(e)}")
            
            # Create position data from exchange info
            entry_price = trade_info.get('actual_entry_price', exchange_data.get('entry_price', 0))
            entry_time = trade_info.get('actual_entry_time', datetime.now(timezone.utc).isoformat())
            
            position_data = {
                "symbol": symbol,
                "direction": exchange_data['direction'],
                "entry_time": entry_time,
                "entry_timestamp": time.time(),
                "entry_price": entry_price,
                "quantity": exchange_data['quantity'],
                "current_price": exchange_data['current_price'],
                "unrealized_pnl": exchange_data['unrealized_pnl'],
                "position_size_usd": exchange_data['quantity'] * entry_price,
                "stop_price": entry_price * (0.994 if exchange_data['direction'] == 'LONG' else 1.006),
                "target_price": entry_price * (1.015 if exchange_data['direction'] == 'LONG' else 0.985),
                "pair_config": config.PAIR_CONFIGS.get(symbol, {}),
                "leverage": config.LEVERAGE,
                "market_type": "FUTURES",
                "note": "Orphan position adopted during reconciliation",
                "reconstruction_data": trade_info,  # Store reconstruction info
                "tp_order_id": None,
                "sl_order_id": None,
                "needs_exit_orders": True,
                "signal_data": {"orphan": True},
                "last_sync": time.time(),
                "cache_version": 1
            }
            
            # Add to cache
            self.positions_cache[symbol] = position_data
            self.position_states[symbol] = PositionState.ACTIVE
            self.save_positions()
            
            print(f"✅ Adopted orphan: {symbol} {exchange_data['direction']} | "
                f"Qty: {exchange_data['quantity']:.4f} @ ${entry_price:.4f}")
            
            if trade_info:
                print(f"   📊 Reconstructed from trades: Entry @ {entry_time}")
                
        except Exception as e:
            print(f"🚨 Error adopting orphan {symbol}: {str(e)}")

    def _verify_oco_after_sync(self, market):
        """🔍 Post-sync crosscheck to reconcile OCO vs cache"""
        try:
            # Check each cached position for OCO drift
            for symbol, position in self.positions_cache.items():
                tp_order_id = position.get('tp_order_id')
                sl_order_id = position.get('sl_order_id')
                
                # Skip if no exit orders
                if not tp_order_id or not sl_order_id:
                    continue
                
                # Check if OCO is being tracked by market module
                if symbol in market.oco_pairs:
                    market_oco = market.oco_pairs[symbol]
                    
                    # Verify order IDs match
                    if (market_oco.get('tp_order_id') != tp_order_id or 
                        market_oco.get('sl_order_id') != sl_order_id):
                        print(f"⚠️ OCO drift detected for {symbol} - updating market tracking")
                        
                        # Update market OCO tracking
                        with market.oco_lock:
                            market.oco_pairs[symbol] = {
                                'tp_order_id': tp_order_id,
                                'sl_order_id': sl_order_id,
                                'created_at': time.time(),
                                'status': 'active'
                            }
                else:
                    # OCO not tracked by market - add it
                    print(f"⚠️ OCO not tracked by market for {symbol} - adding to tracking")
                    with market.oco_lock:
                        market.oco_pairs[symbol] = {
                            'tp_order_id': tp_order_id,
                            'sl_order_id': sl_order_id,
                            'created_at': time.time(),
                            'status': 'active'
                        }
                
                # Verify exit orders still exist on exchange
                try:
                    verification = market.verify_exit_orders_fast(symbol)
                    if not verification['both_present']:
                        print(f"⚠️ Missing exit orders for {symbol} - OCO drift detected")
                        # Mark for repair in next cycle
                        position['needs_repair'] = True
                except Exception as e:
                    print(f"⚠️ Error verifying exit orders for {symbol}: {str(e)}")
                    
        except Exception as e:
            print(f"🚨 Error in OCO verification: {str(e)}")

    def _update_position_from_exchange(self, symbol, exchange_data):
        """📊 Update cached position from exchange data"""
        if symbol in self.positions_cache:
            self.positions_cache[symbol]["quantity"] = exchange_data['quantity']
            self.positions_cache[symbol]["current_price"] = exchange_data['current_price']
            self.positions_cache[symbol]["unrealized_pnl"] = exchange_data['unrealized_pnl']
            self.positions_cache[symbol]["last_sync"] = time.time()

    def _verify_all_exit_orders(self, market, notifier):
        """🔍 Verify all positions have exit orders"""
        for symbol, position in self.positions_cache.items():
            if not position.get("tp_order_id") or not position.get("sl_order_id"):
                notifier.quantum_log(f"⚠️ {symbol} missing exit orders", "WARNING")
                position["needs_exit_orders"] = True

    def _verify_log_entry(self, log_entry):
        """Verify a log entry was written to file"""
        try:
            with open(config.TRADES_LOG_FILE, 'r') as f:
                # Read last few lines to check
                lines = f.readlines()[-10:]  # Last 10 lines
                for line in lines:
                    if log_entry in line:
                        return True
            return False
        except:
            return False
    
    def _update_daily_stats(self, trade):
        """📊 Update daily statistics - ONLY COUNT ON CLOSE"""
        # Use UTC date
        today_utc = datetime.now(timezone.utc).date().isoformat()
        
        # Only update stats when trade closes (has exit_time)
        if 'exit_time' not in trade:
            return
        
        # Parse trade close date
        try:
            exit_time_str = trade['exit_time']
            if 'T' in exit_time_str:
                trade_date = exit_time_str.split('T')[0]
            else:
                # Parse and convert to UTC
                exit_dt = datetime.fromisoformat(exit_time_str.replace('Z', '+00:00').split('+')[0])
                trade_date = exit_dt.date().isoformat()
        except:
            trade_date = today_utc
        
        # Initialize stats if needed
        if trade_date not in self.daily_stats:
            self.daily_stats[trade_date] = {
                "trades": 0, "wins": 0, "losses": 0, "pnl_usd": 0.0, "volume_usd": 0.0,
                "win_rate": 0.0, "long_trades": 0, "short_trades": 0,
                "futures_trades": 0, "spot_trades": 0,
                "canceled_orders": 0, "filled_orders": 0
            }
        
        # Update stats for the day the trade closed
        stats = self.daily_stats[trade_date]
        stats["trades"] += 1
        
        # Use net P&L if available, otherwise gross
        pnl_to_use = trade.get("net_pnl_usd", trade.get("pnl_usd", 0))
        
        if pnl_to_use > 0:
            stats["wins"] += 1
        else:
            stats["losses"] += 1
        
        stats["pnl_usd"] += pnl_to_use
        stats["volume_usd"] += trade.get("position_size_usd", 0)
        
        if trade.get("direction") == "LONG":
            stats["long_trades"] += 1
        else:
            stats["short_trades"] += 1
        
        if trade.get("market_type") == "FUTURES":
            stats["futures_trades"] += 1
        else:
            stats["spot_trades"] += 1
        
        stats["win_rate"] = (stats["wins"] / stats["trades"]) * 100 if stats["trades"] > 0 else 0

    def _update_performance_stats(self, trade):
        """📈 Update performance statistics with TIMESTAMP TRACKING"""
        symbol = trade["symbol"]
        
        # Initialize if needed
        if symbol not in self.symbol_performance:
            self.symbol_performance[symbol] = {
                "trades": 0,
                "wins": 0,
                "total_pnl_usd": 0.0,
                "best_trade": 0.0,
                "worst_trade": 0.0,
                "avg_hold_time": 0.0,
                "canceled_orders": 0,
                "last_trade_time": 0  # ADDED: Track last activity
            }
        
        perf = self.symbol_performance[symbol]
        perf["trades"] += 1
        perf["last_trade_time"] = time.time()  # ADDED: Update timestamp
        
        if trade["pnl_usd"] > 0:
            perf["wins"] += 1
        perf["total_pnl_usd"] += trade["pnl_usd"]
        perf["avg_hold_time"] = ((perf["avg_hold_time"] * (perf["trades"] - 1) + trade["hold_time_hours"]) / perf["trades"])
        if trade["pnl_usd"] > perf["best_trade"]:
            perf["best_trade"] = trade["pnl_usd"]
        if trade["pnl_usd"] < perf["worst_trade"]:
            perf["worst_trade"] = trade["pnl_usd"]

    def _rebuild_performance_stats(self):
        """🔄 Rebuild performance statistics from trade history"""
        self.daily_stats.clear()
        self.symbol_performance.clear()
        for trade in self.all_trades:
            try:
                self._update_daily_stats(trade)
                self._update_performance_stats(trade)
            except Exception as e:
                print(f"⚠️ Error rebuilding stats for trade: {str(e)}")


    def _retry_failed_logs(self):
        """Background thread to retry failed log writes"""
        max_consecutive_failures = 10
        consecutive_failures = 0
        
        while self.logging_active:
            try:
                time.sleep(30)  # Check every 30 seconds
                
                if not self.failed_log_queue:
                    consecutive_failures = 0  # Reset on success
                    continue
                
                # Try to write failed logs
                current_time = time.time()
                logs_to_retry = []
                
                # Collect logs older than 10 seconds
                for log_entry in list(self.failed_log_queue):
                    if current_time - log_entry['timestamp'] > 10:
                        logs_to_retry.append(log_entry)
                
                for log_entry in logs_to_retry:
                    try:
                        # Remove from queue first
                        self.failed_log_queue.remove(log_entry)
                        
                        # Try to write
                        os.makedirs(os.path.dirname(config.TRADES_LOG_FILE), exist_ok=True)
                        
                        with open(config.TRADES_LOG_FILE, 'a', encoding='utf-8') as f:
                            f.write(log_entry['entry'] + "\n")
                            f.flush()
                            os.fsync(f.fileno())
                        
                        print(f"✅ Successfully wrote previously failed log entry")
                        
                    except Exception as e:
                        # Re-add to queue if still failing
                        log_entry['attempts'] += 1
                        if log_entry['attempts'] < 10:  # Max 10 retries
                            log_entry['timestamp'] = current_time  # Reset timestamp
                            self.failed_log_queue.append(log_entry)
                        else:
                            print(f"❌ Dropping log entry after 10 failed retries")
                        
                        time.sleep(2)  # Don't spam retries
                        
            except Exception as e:
                consecutive_failures += 1
                print(f"⚠️ Log retry thread error: {str(e)}")
                
                if consecutive_failures >= max_consecutive_failures:
                    print(f"🚨 Log retry thread failing repeatedly - pausing for 5 minutes")
                    time.sleep(300)  # Wait 5 minutes
                    consecutive_failures = 0
                else:
                    time.sleep(60)  # Wait 1 minute on error
                    
    def _calculate_hold_time_hours(self, entry_time_str):
        """⏰ Calculate hold time in hours"""
        try:
            # Handle timezone-aware strings
            if isinstance(entry_time_str, str):
                # Remove timezone info if present
                entry_time_str = entry_time_str.replace('Z', '+00:00')
                entry_time = datetime.fromisoformat(entry_time_str.split('+')[0])
            else:
                entry_time = entry_time_str
            return round((datetime.now() - entry_time).total_seconds() / 3600, 1)
        except:
            return 0.0

    def _log_trade(self, action, symbol, data):
        """📄 Log trade to file - NON-BLOCKING WITH RETRY"""
        try:
            timestamp = datetime.now().isoformat()
            
            if action == "ENTRY":
                # Validate entry data with safe defaults
                entry_price = float(data.get('entry_price', 0))
                quantity = float(data.get('quantity', 0))
                direction = str(data.get('direction', 'UNKNOWN'))
                market_type = str(data.get('market_type', 'SPOT'))
                
                log_entry = (
                    f"{timestamp}|ENTRY|{symbol}|"
                    f"{entry_price:.4f}|{quantity:.4f}|"
                    f"Direction:{direction}|"
                    f"Market:{market_type}"
                )
            else:  # EXIT
                # Validate exit data with safe defaults
                exit_price = float(data.get('exit_price', 0))
                quantity = float(data.get('quantity', 0))
                pnl_usd = float(data.get('pnl_usd', 0))
                pnl_pct = float(data.get('pnl_pct', 0))
                exit_reason = str(data.get('exit_reason', 'UNKNOWN'))
                exit_type = str(data.get('exit_type', 'UNKNOWN'))
                hold_time_bars = int(data.get('hold_time_bars', 0))
                direction = str(data.get('direction', 'UNKNOWN'))
                
                log_entry = (
                    f"{timestamp}|EXIT|{symbol}|"
                    f"{exit_price:.4f}|{quantity:.4f}|"
                    f"PNL:${pnl_usd:.2f} ({pnl_pct:.2f}%)|"
                    f"Reason:{exit_reason}|"
                    f"Type:{exit_type}|"
                    f"HoldBars:{hold_time_bars}|"
                    f"Direction:{direction}"
                )
            
            # FIX: Non-blocking queue put with overflow handling
            try:
                self.log_queue.put_nowait(log_entry)
                print(f"✅ Queued {action} log for {symbol}")
            except queue.Full:
                print(f"⚠️ Log queue full - adding to retry queue")
                self.failed_log_queue.append({
                    'entry': log_entry,
                    'timestamp': time.time(),
                    'attempts': 1
                })
                # Still try emergency log for critical trades
                if action == "EXIT":
                    self._emergency_log_trade(action, symbol, data)
                    
        except Exception as e:
            print(f"🚨 ERROR in _log_trade: {str(e)}")
            # Always try emergency log on error
            self._emergency_log_trade(action, symbol, data)

    def _emergency_log_trade(self, action, symbol, data):
        """🚨 Emergency backup logging with SIZE LIMIT and ROTATION"""
        try:
            emergency_file = f"{config.LOG_DIR}/emergency_trades.log"
            os.makedirs(os.path.dirname(emergency_file), exist_ok=True)
            
            # Check file size (rotate if > 10MB)
            if os.path.exists(emergency_file):
                file_size = os.path.getsize(emergency_file)
                if file_size > 10 * 1024 * 1024:  # 10MB
                    # Rotate the file
                    backup_file = f"{emergency_file}.{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}"
                    try:
                        os.rename(emergency_file, backup_file)
                        print(f"📂 Rotated emergency log to {backup_file}")
                        
                        # Try to compress old file
                        try:
                            import gzip
                            with open(backup_file, 'rb') as f_in:
                                with gzip.open(f"{backup_file}.gz", 'wb') as f_out:
                                    f_out.writelines(f_in)
                            os.remove(backup_file)
                            print(f"📦 Compressed to {backup_file}.gz")
                        except Exception as gz_error:
                            print(f"⚠️ Could not compress backup: {str(gz_error)}")
                            # Keep uncompressed backup file
                            pass
                            
                    except Exception as rotate_error:
                        print(f"⚠️ Could not rotate emergency log: {str(rotate_error)}")
                        # If rotation fails, truncate the file instead
                        try:
                            # Keep last 1000 lines
                            with open(emergency_file, 'r') as f:
                                lines = f.readlines()
                            
                            if len(lines) > 1000:
                                with open(emergency_file, 'w') as f:
                                    f.writelines(lines[-1000:])
                                    f.write(f"# Log truncated at {datetime.now(timezone.utc).isoformat()}\n")
                                print(f"📂 Truncated emergency log to last 1000 lines")
                        except:
                            # If even truncation fails, clear the file
                            with open(emergency_file, 'w') as f:
                                f.write(f"# Log cleared at {datetime.now(timezone.utc).isoformat()}\n")
                            print(f"🧹 Cleared emergency log due to errors")
            
            # Format the log entry
            timestamp = datetime.now(timezone.utc).isoformat()
            
            # Create a safe JSON representation of data
            try:
                # Try to serialize the data
                data_json = json.dumps(data, default=str)  # Use default=str for non-serializable objects
            except Exception as json_error:
                # If JSON serialization fails, create a string representation
                try:
                    data_json = str(data)
                except:
                    data_json = "ERROR: Could not serialize data"
                print(f"⚠️ Could not JSON serialize emergency log data: {str(json_error)}")
            
            # Create the log entry
            log_entry = f"{timestamp}|EMERGENCY|{action}|{symbol}|{data_json}\n"
            
            # Write to file with error handling
            write_success = False
            max_attempts = 3
            
            for attempt in range(max_attempts):
                try:
                    with open(emergency_file, 'a', encoding='utf-8') as f:
                        f.write(log_entry)
                        f.flush()
                        os.fsync(f.fileno())  # Force write to disk
                    
                    write_success = True
                    if attempt > 0:
                        print(f"✅ EMERGENCY LOG written on attempt {attempt + 1}")
                    else:
                        print(f"🚨 EMERGENCY LOG written to {emergency_file}")
                    break
                    
                except Exception as write_error:
                    print(f"⚠️ Emergency log write attempt {attempt + 1} failed: {str(write_error)}")
                    if attempt < max_attempts - 1:
                        time.sleep(0.5)  # Brief pause before retry
                    else:
                        # Last resort - try to write to alternate location
                        try:
                            alternate_file = f"{config.DATA_DIR}/emergency_trades_backup.log"
                            os.makedirs(os.path.dirname(alternate_file), exist_ok=True)
                            with open(alternate_file, 'a', encoding='utf-8') as f:
                                f.write(log_entry)
                                f.flush()
                            print(f"🚨 EMERGENCY LOG written to alternate location: {alternate_file}")
                            write_success = True
                        except Exception as alt_error:
                            print(f"🚨 CRITICAL: Could not write emergency log anywhere: {str(alt_error)}")
            
            # If this is a critical trade (EXIT), also try to save to a daily file
            if action == "EXIT" and write_success:
                try:
                    daily_file = f"{config.LOG_DIR}/emergency_exits_{datetime.now(timezone.utc).strftime('%Y%m%d')}.log"
                    with open(daily_file, 'a', encoding='utf-8') as f:
                        f.write(log_entry)
                        f.flush()
                    print(f"📝 EXIT also logged to daily file: {daily_file}")
                except:
                    pass  # This is optional, don't fail if it doesn't work
            
            # Add to failed attempts tracker if write failed
            if not write_success:
                if not hasattr(self, 'failed_log_attempts'):
                    self.failed_log_attempts = []
                self.failed_log_attempts.append(log_entry)
                
                # Keep only last 100 failed attempts to prevent memory leak
                if len(self.failed_log_attempts) > 100:
                    self.failed_log_attempts = self.failed_log_attempts[-100:]
                
                print(f"🚨 Added to failed log attempts buffer ({len(self.failed_log_attempts)} pending)")
            
            return write_success
            
        except Exception as e:
            print(f"🚨 EMERGENCY LOG CATASTROPHIC FAILURE: {str(e)}")
            # Absolute last resort - print to console
            try:
                print(f"🚨 EMERGENCY LOG DATA: {action}|{symbol}|{str(data)[:500]}")  # Limit data size
            except:
                print(f"🚨 EMERGENCY LOG: Failed to log {action} for {symbol}")
            
            return False
    
    def debug_log_state(self):
        """Debug method to check logging state"""
        print(f"\n🔍 DEBUG LOG STATE:")
        print(f"   Trades log file: {config.TRADES_LOG_FILE}")
        print(f"   File exists: {os.path.exists(config.TRADES_LOG_FILE)}")
        print(f"   Directory exists: {os.path.exists(os.path.dirname(config.TRADES_LOG_FILE))}")
        print(f"   File writable: {os.access(config.TRADES_LOG_FILE, os.W_OK) if os.path.exists(config.TRADES_LOG_FILE) else 'N/A'}")
        print(f"   Total trades recorded: {len(self.all_trades)}")
        print(f"   Trades today: {len(self.trades_today)}")

        if self.all_trades:
            print(f"\n   Last 3 trades:")
            for trade in self.all_trades[-3:]:
                print(f"      {trade.get('symbol')} {trade.get('direction')} - "
                    f"Entry: {trade.get('entry_time', 'N/A')}, "
                    f"Exit: {trade.get('exit_time', 'N/A')}")

    def verify_all_trades_logged(self):
        """Verify all trades in memory are in the log file"""
        print("\n🔍 VERIFYING TRADE LOG INTEGRITY...")
        
        if not os.path.exists(config.TRADES_LOG_FILE):
            print(f"❌ Trade log file does not exist: {config.TRADES_LOG_FILE}")
            return False
        
        # Read log file
        logged_trades = set()
        with open(config.TRADES_LOG_FILE, 'r') as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith('#'):
                    continue
                parts = line.split('|')
                if len(parts) >= 3:
                    # Create a simple key for matching
                    key = f"{parts[1]}_{parts[2]}"  # ACTION_SYMBOL
                    logged_trades.add(key)
        
        # Check all trades
        missing_trades = []
        for trade in self.all_trades:
            # Each trade should have an ENTRY and EXIT
            entry_key = f"ENTRY_{trade['symbol']}"
            exit_key = f"EXIT_{trade['symbol']}"
            
            if entry_key not in logged_trades:
                missing_trades.append(f"ENTRY for {trade['symbol']} at {trade.get('entry_time', 'unknown')}")
            if exit_key not in logged_trades:
                missing_trades.append(f"EXIT for {trade['symbol']} at {trade.get('exit_time', 'unknown')}")
        
        if missing_trades:
            print(f"❌ MISSING {len(missing_trades)} trade logs:")
            for missing in missing_trades[:10]:  # Show first 10
                print(f"   - {missing}")
            if len(missing_trades) > 10:
                print(f"   ... and {len(missing_trades) - 10} more")
            return False
        else:
            print(f"✅ All {len(self.all_trades)} trades are properly logged")
            return True
        
    def _get_empty_summary(self):
        """📊 Get empty summary structure"""
        return {
            "total_trades": 0,
            "active_positions": 0,
            "pending_orders": 0,
            "total_committed": 0,
            "position_utilization": 0,
            "positions_with_exit_orders": 0,
            "exit_order_coverage": 100.0,
            "win_rate": 0,
            "profit_factor": 0,
            "total_pnl_usd": 0,
            "total_return_pct": 0,
            "average_win_usd": 0,
            "average_loss_usd": 0,
            "best_trade_usd": 0,
            "worst_trade_usd": 0,
            "avg_hold_time_hours": 0,
            "consecutive_wins": 0,
            "consecutive_losses": 0,
            "max_consecutive_wins": 0,
            "max_consecutive_losses": 0,
            "today_trades": 0,
            "today_pnl_usd": 0,
            "today_win_rate": 0,
            "today_filled_orders": 0,
            "today_canceled_orders": 0,
            "order_fill_rate": 100.0,
            "balance_usd": self.balance_usd,
            "initial_balance_usd": self.initial_balance_usd,
            "market_type": "FUTURES" if config.ENABLE_FUTURES else "SPOT",
            "symbol_performance": {},
            "last_sync_age": 999
        }

    def shutdown(self):
        """Shutdown the logger threads gracefully"""
        print("🛑 Shutting down trade logger...")
        
        # FIX: Process any remaining failed logs
        if self.failed_log_queue:
            print(f"⚠️ Processing {len(self.failed_log_queue)} failed log entries...")
            for failed_log in list(self.failed_log_queue):
                try:
                    with open(config.TRADES_LOG_FILE, 'a', encoding='utf-8') as f:
                        f.write(failed_log['entry'] + "\n")
                        f.flush()
                        os.fsync(f.fileno())
                except:
                    pass
        
        # Check for any failed logs in memory
        if self.failed_log_attempts:
            print(f"⚠️ WARNING: {len(self.failed_log_attempts)} permanently failed log attempts!")
            # Try to write them one more time
            for entry in self.failed_log_attempts[:10]:  # First 10 only
                try:
                    self._write_log_entry_sync(entry)
                except:
                    pass
        
        # Shutdown the async logger
        if hasattr(self, 'log_queue'):
            self.logging_active = False
            
            # FIX: Flush queue before stopping
            while not self.log_queue.empty():
                try:
                    entry = self.log_queue.get_nowait()
                    self._write_log_entry_sync(entry)
                except queue.Empty:
                    break
                except:
                    pass
            
            self.log_queue.put(None)  # Send sentinel to stop thread
            if hasattr(self, 'log_thread'):
                self.log_thread.join(timeout=5)
            if hasattr(self, 'log_retry_thread'):
                self.log_retry_thread.join(timeout=2)
        
        # Final verification
        self.verify_all_trades_logged()

print("🌌 MODULAR PORTFOLIO SYSTEM READY! 🚀")
print(f"📈 Exchange-first design - Binance is source of truth")
print(f"⚡ Max Positions: {config.MAX_TOTAL_POSITIONS}")
print("🎯 Per Aspera Ad Astra!")