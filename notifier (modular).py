# notifier.py - MODULAR VERSION
"""
🚀 NOTIFICATION SYSTEM - UNIVERSAL MESSENGER 🚀
Strategy-agnostic notification interface for modular trading
Enhanced with OCO, retry, and reconciliation notifications
Per Aspera Ad Astra
"""

import json
import requests
from datetime import datetime, date, timedelta, timezone
from collections import deque
import os
import time
import queue
import hashlib
import threading
from collections import deque
import config


class QuantumDimensionalPortal:
    def __init__(self):
        """Initialize the Universal Notification System 🛸"""
        self.webhook_url = config.DISCORD_WEBHOOK
        self.enable_discord = config.ENABLE_DISCORD and self.webhook_url
        self.enable_console = config.ENABLE_CONSOLE
        self.enable_file_logging = config.ENABLE_FILE_LOGGING
        self.last_discord_time = 0
        self.discord_rate_limit = 2  # seconds between messages
        self.alerts_lock = threading.RLock() 

        # Non-blocking logger setup with OVERFLOW STRATEGY
        if self.enable_file_logging:
            os.makedirs(config.LOG_DIR, exist_ok=True)
            self.log_queue = queue.Queue(maxsize=5000)  # ADDED: Max size with limit
            self.log_overflow_strategy = "drop_oldest"  # drop_oldest or block
            self.dropped_log_count = 0
            self.logger_thread = threading.Thread(target=self._log_writer, daemon=True)
            self.logger_thread.start()
            
            # Logger health monitoring
            self.log_failures = 0
            self.last_log_health_check = time.time()
            
        # Duplicate prevention with automatic cleanup
        self.recent_alerts = {}  # Store recent alert hashes
        self.duplicate_window = 60  # Don't repeat identical alerts within 60 seconds
        self.last_alert_cleanup = time.time()  # ADDED: Track cleanup time
        
        # Failed Discord message persistence
        self.failed_discord_messages = deque(maxlen=100)  # ADDED: Store failed messages
        self.discord_retry_thread = threading.Thread(target=self._retry_failed_discord, daemon=True)
        self.discord_retry_thread.start()
        
        # Validate Discord webhook URL
        if self.webhook_url:
            self._validate_webhook_url()  # ADDED: Security validation
        
        # Universal color codes
        self.colors = {
            "success": 0x00FF00,
            "error": 0xFF0000,
            "warning": 0xFFA500,
            "info": 0x0000FF,
            "profit": 0x00FF00,
            "loss": 0xFF0000,
            "neutral": 0x808080,
            "signal": 0x9932CC,
            "critical": 0x8B0000,
            "oco": 0x4B0082
        }
        
        # Market emojis
        self.market_emojis = {
            "FUTURES": "⚡",
            "SPOT": "💰"
        }
        
        print("🔔 Notification system initialized")

    def _log_writer(self):
        """Worker thread with OVERFLOW HANDLING and spurious wakeup protection"""
        consecutive_failures = 0
        max_failures = 5
        messages_written = 0
        
        while True:
            try:
                # Use timeout to handle spurious wakeups properly
                try:
                    log_entry = self.log_queue.get(timeout=1)
                except queue.Empty:
                    # Timeout is normal, continue loop
                    continue
                    
                if log_entry is None:  # Sentinel value to stop thread
                    break
                
                # Write the log entry
                with open(config.HYPERION_LOG_FILE, 'a', encoding='utf-8') as f:
                    f.write(log_entry + "\n")
                    f.flush()
                    os.fsync(f.fileno())
                
                messages_written += 1
                consecutive_failures = 0  # Reset on success
                
                # Update health metrics every 100 messages
                if messages_written % 100 == 0:
                    self.log_failures = 0  # Reset failure counter on successful writes
                    
            except Exception as e:
                consecutive_failures += 1
                self.log_failures += 1
                
                if consecutive_failures >= max_failures:
                    print(f"🚨 CRITICAL: Logger thread failing repeatedly ({consecutive_failures} failures)")
                    # Try to recover
                    time.sleep(1)
                    consecutive_failures = 0  # Reset and try again
                
                print(f"🚨 Logger thread error #{consecutive_failures}: {str(e)}")

    def _is_duplicate_alert(self, alert_type, message):
        """Check if duplicate with ENHANCED DYNAMIC WINDOWS - THREAD SAFE"""
        alert_hash = hashlib.md5(f"{alert_type}:{message}".encode()).hexdigest()
        current_time = time.time()
        
        with self.alerts_lock:  # Thread-safe access
            # Automatic cleanup every 5 minutes
            if current_time - self.last_alert_cleanup > 300:
                self.cleanup_old_alerts()
                self.last_alert_cleanup = current_time
            
            # ENHANCED: Dynamic duplicate window based on alert type
            dynamic_window = self._get_duplicate_window_for_type(alert_type)
            
            # Check if duplicate
            if alert_hash in self.recent_alerts:
                time_since = current_time - self.recent_alerts[alert_hash]
                if time_since < dynamic_window:
                    return True  # Is duplicate
            
            # Store this alert
            self.recent_alerts[alert_hash] = current_time
            return False

    def _get_duplicate_window_for_type(self, alert_type):
        """Get dynamic duplicate window based on alert criticality"""
        # CRITICAL FIX: Reduce window for exit notifications to prevent missed alerts
        if alert_type in ['EXIT', 'EXIT_TP', 'EXIT_SL', 'EXIT_MANUAL', 'POSITION_CLOSED']:
            return 10  # 10 seconds for exit notifications (was 60s)
        elif alert_type in ['ENTRY', 'SIGNAL_DETECTED']:
            return 30  # 30 seconds for entry notifications
        elif alert_type in ['HEARTBEAT', 'STATUS_UPDATE']:
            return 60  # 60 seconds for status updates
        else:
            return 20  # 20 seconds default

    def _validate_webhook_url(self):
        """Validate Discord webhook URL for security"""
        if not self.webhook_url:
            return
        
        # Basic validation - accept webhooks with additional paths
        if not self.webhook_url.startswith('https://discord.com/api/webhooks/'):
            if not self.webhook_url.startswith('https://discordapp.com/api/webhooks/'):  # Also accept old format
                print("⚠️ Invalid Discord webhook URL format")
                self.enable_discord = False
                return
        
        # Sanitize URL (remove any query parameters that might be added)
        if '?' in self.webhook_url:
            self.webhook_url = self.webhook_url.split('?')[0]
            print("⚠️ Removed query parameters from webhook URL")

    def cleanup_old_alerts(self):
        """🧹 Clean up old alert history to prevent memory leak - THREAD SAFE"""
        current_time = time.time()
        
        with self.alerts_lock:  # FIX: Thread-safe cleanup
            before_count = len(self.recent_alerts)
            
            # Remove alerts older than duplicate window
            self.recent_alerts = {
                h: t for h, t in self.recent_alerts.items() 
                if current_time - t < self.duplicate_window * 2
            }
            
            after_count = len(self.recent_alerts)
            if before_count - after_count > 0:
                self.quantum_log(f"🧹 Cleaned {before_count - after_count} old alert records", "INFO")

    def get_notification_stats(self):
        """Get notification system statistics"""
        stats = {
            'dropped_logs': self.dropped_log_count,
            'failed_discord_pending': len(self.failed_discord_messages),
            'duplicate_alerts_blocked': self.get_alerts_count(),  # FIX: Use thread-safe method
            'log_queue_size': self.log_queue.qsize() if hasattr(self, 'log_queue') else 0,
            'log_failures': self.log_failures
        }
        return stats

    def get_alerts_count(self):
        """Get count of recent alerts - THREAD SAFE"""
        with self.alerts_lock:
            return len(self.recent_alerts)
        
    def quantum_log(self, message, level="INFO"):
        """📝 Universal log entry with OVERFLOW HANDLING"""
        timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")  # Use UTC
        log_entry = f"[{timestamp}] [{level}] {message}"
        
        # Console output remains synchronous
        if self.enable_console:
            level_emoji = {
                "SUCCESS": "✅",
                "INFO": "📡", 
                "TRADE": "⚡",
                "ERROR": "🚨",
                "WARNING": "⚠️",
                "CRITICAL": "💀"
            }
            emoji = level_emoji.get(level, "📡")
            print(f"{emoji} {log_entry}")
        
        # File logging with overflow handling
        if self.enable_file_logging:
            try:
                if self.log_overflow_strategy == "drop_oldest" and self.log_queue.full():
                    # Drop oldest message
                    try:
                        self.log_queue.get_nowait()
                        self.dropped_log_count += 1
                        if self.dropped_log_count % 100 == 0:  # Warn every 100 drops
                            print(f"⚠️ Dropped {self.dropped_log_count} log messages due to overflow")
                    except queue.Empty:
                        pass
                
                # Try to add new message
                if self.log_overflow_strategy == "block":
                    self.log_queue.put(log_entry, timeout=1)  # Block up to 1 second
                else:
                    self.log_queue.put_nowait(log_entry)
                    
            except queue.Full:
                self.dropped_log_count += 1
                if self.dropped_log_count % 100 == 0:
                    print(f"⚠️ Log queue full - dropped {self.dropped_log_count} messages")

    def shutdown(self):
        """Shut down with PROPER CLEANUP"""
        print("🛑 Shutting down notification system...")
        
        # Final stats
        stats = self.get_notification_stats()
        print(f"📊 Final notification stats: {stats}")
        
        with self.alerts_lock:
            self.recent_alerts.clear()

        # Try to flush any remaining Discord messages
        if self.failed_discord_messages:
            print(f"⚠️ {len(self.failed_discord_messages)} Discord messages pending at shutdown")
            for msg in list(self.failed_discord_messages)[:5]:  # Try to send up to 5
                try:
                    self._send_discord_embed(msg['content'], msg['embed'])
                except:
                    pass
        
        # Shutdown file logger
        if self.enable_file_logging:
            # Wait for queue to empty (max 5 seconds)
            timeout = time.time() + 5
            while self.log_queue.qsize() > 0 and time.time() < timeout:
                time.sleep(0.1)
            
            if self.log_queue.qsize() > 0:
                print(f"⚠️ {self.log_queue.qsize()} log messages lost at shutdown")
            
            # Send sentinel to stop thread
            try:
                self.log_queue.put(None, timeout=1)
            except:
                pass
            
            # Wait for thread to finish
            try:
                self.logger_thread.join(timeout=2)
                print("✅ Logger thread shutdown complete")
            except Exception as e:
                print(f"⚠️ Error joining logger thread: {e}")
        
        print("✅ Notification system shutdown complete")

    def send_strike_entry_alert(self, signal, position_sizing):
        """🎯 ENTRY ALERT - CLEAN AND RELIABLE"""
        try:
            # Validate inputs with safe defaults
            symbol = signal.get("symbol", "UNKNOWN")
            action = signal.get("action", "UNKNOWN")
            entry_price = signal.get("entry_price", 0)
            stop_price = signal.get("stop_price", 0)
            target_price = signal.get("target_price", 0)
            quality_score = signal.get("quality_score", 0)
            
            # Market info
            market_type = "FUTURES" if config.ENABLE_FUTURES else "SPOT"
            leverage_info = f" @{config.LEVERAGE}x" if config.ENABLE_FUTURES else ""
            
            # Risk calculations
            position_size_usd = position_sizing.get("position_size_usd", 0)
            
            # Calculate percentages
            if entry_price > 0:
                sl_pct = abs((stop_price - entry_price) / entry_price) * 100
                tp_pct = abs((target_price - entry_price) / entry_price) * 100
                risk_reward = tp_pct / sl_pct if sl_pct > 0 else 0
            else:
                sl_pct = 0
                tp_pct = 0
                risk_reward = 0
            
            # Choose color based on direction
            color = self.colors["success"] if action == "LONG" else self.colors["signal"]
            action_emoji = "📈" if action == "LONG" else "📉"
            
            # Exit order status
            protection_status = "✅ Protected" if config.AUTO_PLACE_EXIT_ORDERS else "⚠️ Manual Exit"
            
            embed = {
                "title": f"{action_emoji} {action} ENTRY • {symbol}",
                "description": f"{market_type}{leverage_info} • {protection_status}",
                "color": color,
                "fields": [
                    {
                        "name": "💰 Entry", 
                        "value": f"`${entry_price:.4f}`", 
                        "inline": True
                    },
                    {
                        "name": "🎯 Target", 
                        "value": f"`${target_price:.4f}` (+{tp_pct:.1f}%)", 
                        "inline": True
                    },
                    {
                        "name": "🛡️ Stop", 
                        "value": f"`${stop_price:.4f}` (-{sl_pct:.1f}%)", 
                        "inline": True
                    },
                    {
                        "name": "📊 Stats", 
                        "value": f"Size: `${position_size_usd:.0f}` • R:R: `1:{risk_reward:.1f}` • Quality: `{quality_score:.2f}`", 
                        "inline": False
                    }
                ],
                "footer": {"text": f"Hyperion Bot • {datetime.now(timezone.utc).strftime('%I:%M %p UTC')}"},
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
            
            self._send_discord_embed("", embed)
            
            # Log
            self.quantum_log(
                f"ENTRY: {action} {symbol} @ ${entry_price:.4f}{leverage_info} | "
                f"TP: ${target_price:.4f} (+{tp_pct:.1f}%) | "
                f"SL: ${stop_price:.4f} (-{sl_pct:.1f}%)", 
                "TRADE"
            )
            
        except Exception as e:
            self.quantum_log(f"Entry alert error: {str(e)}", "ERROR")

    def send_entry_attempt_alert(self, symbol, signal, position_sizing):
        """🚀 ENTRY ATTEMPT ALERT - When order is being placed"""
        try:
            action = signal.get("action", "UNKNOWN")
            entry_price = signal.get("entry_price", 0)
            position_size_usd = position_sizing.get("position_size_usd", 0)
            
            market_type = "FUTURES" if config.ENABLE_FUTURES else "SPOT"
            leverage_info = f" @{config.LEVERAGE}x" if config.ENABLE_FUTURES else ""
            
            embed = {
                "title": f"🚀 ENTRY ATTEMPT • {symbol}",
                "description": f"{action} • {market_type}{leverage_info}",
                "color": self.colors["info"],
                "fields": [
                    {
                        "name": "💰 Target Entry", 
                        "value": f"`${entry_price:.4f}`", 
                        "inline": True
                    },
                    {
                        "name": "📊 Position Size", 
                        "value": f"`${position_size_usd:.0f}`", 
                        "inline": True
                    },
                    {
                        "name": "⏰ Status", 
                        "value": "`Placing LIMIT order...`", 
                        "inline": True
                    }
                ],
                "footer": {"text": f"Hyperion Bot • {datetime.now(timezone.utc).strftime('%I:%M %p UTC')}"},
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
            
            self._send_discord_embed("", embed)
            
        except Exception as e:
            self.quantum_log(f"Entry attempt alert error: {str(e)}", "ERROR")

    def send_entry_failed_alert(self, symbol, signal, failure_reason):
        """❌ ENTRY FAILED ALERT - When entry attempt fails"""
        try:
            action = signal.get("action", "UNKNOWN")
            entry_price = signal.get("entry_price", 0)
            
            embed = {
                "title": f"❌ ENTRY FAILED • {symbol}",
                "description": f"{action} • {failure_reason}",
                "color": self.colors["error"],
                "fields": [
                    {
                        "name": "💰 Target Entry", 
                        "value": f"`${entry_price:.4f}`", 
                        "inline": True
                    },
                    {
                        "name": "🚫 Reason", 
                        "value": f"`{failure_reason}`", 
                        "inline": True
                    }
                ],
                "footer": {"text": f"Hyperion Bot • {datetime.now(timezone.utc).strftime('%I:%M %p UTC')}"},
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
            
            self._send_discord_embed("", embed)
            
        except Exception as e:
            self.quantum_log(f"Entry failed alert error: {str(e)}", "ERROR")

    def send_entry_converted_alert(self, symbol, signal, conversion_type):
        """🔄 ENTRY CONVERTED ALERT - When LIMIT converts to MARKET"""
        try:
            action = signal.get("action", "UNKNOWN")
            entry_price = signal.get("entry_price", 0)
            
            embed = {
                "title": f"🔄 ENTRY CONVERTED • {symbol}",
                "description": f"{action} • {conversion_type}",
                "color": self.colors["warning"],
                "fields": [
                    {
                        "name": "💰 Target Entry", 
                        "value": f"`${entry_price:.4f}`", 
                        "inline": True
                    },
                    {
                        "name": "🔄 Conversion", 
                        "value": f"`{conversion_type}`", 
                        "inline": True
                    }
                ],
                "footer": {"text": f"Hyperion Bot • {datetime.now(timezone.utc).strftime('%I:%M %p UTC')}"},
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
            
            self._send_discord_embed("", embed)
            
        except Exception as e:
            self.quantum_log(f"Entry converted alert error: {str(e)}", "ERROR")

    def send_strike_exit_alert(self, exit_data):
        """🚪 EXIT ALERT - WITH DUPLICATE PREVENTION"""
        try:
            # Extract data with safe defaults
            symbol = exit_data.get("symbol", "UNKNOWN")
            pnl_usd = exit_data.get("pnl_usd", 0)
            exit_type = exit_data.get("exit_type", "UNKNOWN")
            
            # Check for duplicate (use symbol and exit type as key)
            duplicate_key = f"{symbol}_{exit_type}_{pnl_usd:.2f}"
            if self._is_duplicate_alert("EXIT", duplicate_key):
                self.quantum_log(f"Skipping duplicate exit alert for {symbol}", "INFO")
                return
            
            # Rest of the existing method continues...
            direction = exit_data.get("direction", "UNKNOWN")
            entry_price = exit_data.get("entry_price", 0)
            exit_price = exit_data.get("exit_price", 0)
            pnl_pct = exit_data.get("pnl_pct", 0)
            reason = exit_data.get("reason", "Unknown")
            hold_time = exit_data.get("hold_time", 0)
            
            # Market info
            market_type = "FUTURES" if config.ENABLE_FUTURES else "SPOT"
            direction_emoji = "📈" if direction == "LONG" else "📉"
            
            # Result styling
            if pnl_usd > 0:
                color = self.colors["profit"]
                emoji = "✨"
                result = "PROFIT"
            else:
                color = self.colors["loss"] 
                emoji = "💔"
                result = "LOSS"
            
            # Clean exit type display
            exit_display = {
                "TAKE_PROFIT": "Take Profit Hit 🎯",
                "STOP_LOSS": "Stop Loss Hit 🛡️",
                "TIME_EXIT": "Time Exit ⏰",
                "MANUAL": "Manual Close 👤",
                "EMERGENCY": "Emergency Exit 🚨",
                "UNKNOWN": "Position Closed 📊"
            }.get(exit_type, exit_type)
            
            embed = {
                "title": f"{emoji} {result} • {symbol}",
                "description": f"{direction_emoji} {direction} closed • {exit_display}",
                "color": color,
                "fields": [
                    {
                        "name": "💰 P&L", 
                        "value": f"`${pnl_usd:+.2f}` ({pnl_pct:+.1f}%)", 
                        "inline": True
                    },
                    {
                        "name": "📊 Prices", 
                        "value": f"In: `${entry_price:.4f}`\nOut: `${exit_price:.4f}`", 
                        "inline": True
                    },
                    {
                        "name": "⏱️ Duration", 
                        "value": f"`{hold_time} bars`", 
                        "inline": True
                    }
                ],
                "footer": {"text": f"Hyperion Bot • {market_type} • {datetime.now(timezone.utc).strftime('%I:%M %p UTC')}"},
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
            
            self._send_discord_embed("", embed)
            
            self.quantum_log(
                f"EXIT: {symbol} {direction} | P&L: ${pnl_usd:+.2f} ({pnl_pct:+.1f}%) | {exit_display}", 
                "TRADE"
            )
            
        except Exception as e:
            self.quantum_log(f"Exit alert error: {str(e)}", "ERROR")

    def send_oco_placed_alert(self, symbol, oco_result):
        """🎯 QUANTUM ENTANGLEMENT SHIELD ACTIVATED"""
        try:
            embed = {
                "title": f"🌌 QUANTUM ENTANGLEMENT INITIALIZED",
                "description": f"**{symbol}** • Dimensional exit portals synchronized",
                "color": self.colors["oco"],
                "fields": [
                    {
                        "name": "🔮 Portal Coordinates",
                        "value": f"Victory Portal: `{oco_result['tp_order_id']}`\nEscape Portal: `{oco_result['sl_order_id']}`",
                        "inline": True
                    },
                    {
                        "name": "⚡ Dimensional Anchors",
                        "value": f"Profit Dimension: `${oco_result['tp_price']:.4f}`\nSafety Dimension: `${oco_result['sl_price']:.4f}`",
                        "inline": True
                    },
                    {
                        "name": "🛸 Quantum Mass",
                        "value": f"`{oco_result['quantity']}` units",
                        "inline": True
                    }
                ],
                "footer": {"text": "🚀 Hyperion Systems • Quantum Shield ACTIVE"},
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
            
            self._send_discord_embed("", embed)
            self.quantum_log(f"QUANTUM SHIELD DEPLOYED: {symbol} | Victory: {oco_result['tp_order_id']} | Escape: {oco_result['sl_order_id']}", "SUCCESS")
            
        except Exception as e:
            self.quantum_log(f"Quantum shield error: {str(e)}", "ERROR")

    def send_quantum_heartbeat(self, heartbeat_data):
        """💓 SYSTEM HEARTBEAT - SHOWING REAL TODAY'S DATA"""
        try:
            # Extract data with validation
            balance = heartbeat_data.get("balance", 0)
            active_positions = heartbeat_data.get("active_positions", 0)
            pending_orders = heartbeat_data.get("pending_orders", 0)
            
            # TODAY's metrics (fixed)
            today_pnl = heartbeat_data.get("today_pnl", 0)
            today_trades = heartbeat_data.get("today_trades", 0)
            today_win_rate = heartbeat_data.get("today_win_rate", 0)
            
            # Session metrics
            uptime_hours = heartbeat_data.get("uptime_hours", 0)
            scan_count = heartbeat_data.get("scan_count", 0)
            strategy = heartbeat_data.get("strategy", "Unknown")
            
            # Account metrics
            account_value = heartbeat_data.get("account_value_usd", balance)
            total_unrealized = heartbeat_data.get("total_unrealized_pnl", 0)
            
            # Format uptime
            hours = int(uptime_hours)
            minutes = int((uptime_hours - hours) * 60)
            uptime_str = f"{hours}h {minutes}m"
            
            # Determine status
            if active_positions > 0:
                status = "TRADING ACTIVE"
                color = self.colors["info"]
                emoji = "⚡"
            elif pending_orders > 0:
                status = "ORDERS PENDING"
                color = self.colors["warning"]
                emoji = "⏳"
            elif today_trades > 0:
                status = "TRADES TODAY"
                color = self.colors["success"]
                emoji = "✅"
            else:
                status = "SCANNING"
                color = self.colors["neutral"]
                emoji = "🔍"
            
            # Market info
            market_type = "FUTURES" if config.ENABLE_FUTURES else "SPOT"
            
            # Create embed
            embed = {
                "title": f"{emoji} HYPERION STATUS • {status}",
                "description": f"**{strategy}** • **{market_type}** • Uptime: `{uptime_str}`",
                "color": color,
                "fields": [
                    {
                        "name": "💰 Account",
                        "value": f"Balance: `${balance:.0f}`\nEquity: `${account_value:.0f}`\nUnrealized: `${total_unrealized:+.0f}`",
                        "inline": True
                    },
                    {
                        "name": "📊 Today",
                        "value": f"Trades: `{today_trades}`\nP&L: `${today_pnl:+.2f}`\nWin Rate: `{today_win_rate:.0f}%`",
                        "inline": True
                    },
                    {
                        "name": "⚡ Activity",
                        "value": f"Positions: `{active_positions}/{config.MAX_TOTAL_POSITIONS}`\nPending: `{pending_orders}`\nScans: `{scan_count}`",
                        "inline": True
                    }
                ]
            }
            
            # Add expected vs actual open orders if available
            expected_open_orders = heartbeat_data.get("expected_open_orders", 0)
            actual_open_orders = heartbeat_data.get("actual_open_orders", 0)
            orphans_cleaned = heartbeat_data.get("orphans_cleaned_last_5m", 0)
            
            if expected_open_orders is not None and actual_open_orders is not None:
                delta = actual_open_orders - expected_open_orders
                delta_emoji = "✅" if delta == 0 else "⚠️" if delta > 0 else "❌"
                delta_color = "`0`" if delta == 0 else f"`+{delta}`" if delta > 0 else f"`{delta}`"
                
                embed["fields"].append({
                    "name": f"{delta_emoji} Order Parity",
                    "value": f"Expected: `{expected_open_orders}` • Actual: `{actual_open_orders}` • Delta: {delta_color}\nOrphans cleaned: `{orphans_cleaned}`",
                    "inline": False
                })
            
            embed["footer"] = {"text": f"🚀 Hyperion Trading • {datetime.now(timezone.utc).strftime('%I:%M %p UTC')}"}
            embed["timestamp"] = datetime.now(timezone.utc).isoformat()
            
            # Add position details if any
            positions = heartbeat_data.get("positions", [])
            if positions:
                position_lines = []
                for pos in positions[:3]:  # Top 3 positions
                    symbol = pos.get("symbol", "?")
                    direction = pos.get("direction", "?")
                    unrealized = pos.get("unrealized_pnl", 0)
                    unrealized_pct = pos.get("unrealized_pnl_pct", 0)
                    
                    dir_emoji = "🟢" if direction == "LONG" else "🔴"
                    pnl_emoji = "💎" if unrealized > 0 else "⚡"
                    
                    position_lines.append(
                        f"{dir_emoji} {symbol}: {pnl_emoji} `${unrealized:+.0f}` ({unrealized_pct:+.1f}%)"
                    )
                
                if position_lines:
                    embed["fields"].append({
                        "name": "📈 Open Positions",
                        "value": "\n".join(position_lines),
                        "inline": False
                    })
            
            # Add fill performance if available
            fill_perf = heartbeat_data.get("fill_performance", {})
            if fill_perf and fill_perf.get("fill_rate", 0) > 0:
                embed["fields"].append({
                    "name": "⚡ Fill Performance",
                    "value": f"Rate: `{fill_perf.get('fill_rate', 0):.0f}%` • Avg: `{fill_perf.get('avg_fill_time', 0):.1f}s`",
                    "inline": False
                })
            
            self._send_discord_embed("", embed)
            
            # Console log
            self.quantum_log(
                f"💓 HEARTBEAT: ${balance:.0f} | Positions: {active_positions} | "
                f"Today: {today_trades} trades (${today_pnl:+.2f}) | {uptime_str}",
                "INFO"
            )
            
        except Exception as e:
            self.quantum_log(f"Heartbeat error: {str(e)}", "ERROR")

    def send_startup_message(self, account_balance_usd):
        """🚀 SYSTEM INITIALIZATION"""
        market_type = "FUTURES" if config.ENABLE_FUTURES else "SPOT"
        market_emoji = self.market_emojis.get(market_type, "📊")
        
        active_pairs = []
        for symbol, config_data in config.PAIR_CONFIGS.items():
            if config_data.get("active", False):
                active_pairs.append(symbol)
        
        embed = {
            "title": f"🚀 HYPERION SYSTEMS • ONLINE • {market_type} {market_emoji}",
            "description": f"**Quantum Drive Initialized Successfully**\n*The stars await our command*",
            "color": self.colors["success"],
            "fields": [
                {
                    "name": "💰 Hyperion Credits", 
                    "value": f"`${account_balance_usd:.0f}`", 
                    "inline": True
                },
                {
                    "name": "🎯 Strike Force", 
                    "value": f"`${config.FIXED_POSITION_SIZE_USD}`", 
                    "inline": True
                },
                {
                    "name": "⚡ Fleet Capacity", 
                    "value": f"`{config.MAX_TOTAL_POSITIONS} vessels`", 
                    "inline": True
                }
            ],
            "footer": {"text": f"🚀 Hyperion Command • Per Aspera Ad Astra"},
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        
        # Configuration details
        embed["fields"].append({
            "name": "⚙️ Quantum Configuration",
            "value": f"**AI Core:** `{config.STRATEGY_CLASS}`\n"
                     f"**Quantum Shields:** `{'🌌 ENGAGED' if config.USE_OCO_ORDERS else '📡 STANDARD'}`\n"
                     f"**Dimensional Sync:** `Every {config.RECONCILIATION_INTERVAL}s`\n"
                     f"**Temporal Redundancy:** `{config.ORDER_RETRY_ATTEMPTS} timelines`",
            "inline": False
        })
        
        if config.ENABLE_FUTURES:
            embed["fields"].append({
                "name": "⚡ Warp Drive Status",
                "value": f"**Amplification:** `{config.LEVERAGE}x`\n"
                        f"**Energy Source:** `{config.MARGIN_TYPE}`\n"
                        f"**Reverse Thrusters:** `{'ONLINE' if not config.LONG_ONLY_MODE else 'OFFLINE'}`",
                "inline": False
            })
        
        # Add active pairs
        embed["fields"].append({
            "name": f"🌟 Star Systems Under Surveillance ({len(active_pairs)})", 
            "value": f"`{', '.join(active_pairs[:8])}{'...' if len(active_pairs) > 8 else ''}`", 
            "inline": False
        })
        
        self._send_discord_embed("", embed)
        self.quantum_log(f"🚀 HYPERION SYSTEMS ONLINE - {market_type} DRIVES ENGAGED! TO THE STARS!", "SUCCESS")

    # Replaced send_shutdown_message
    def send_shutdown_message(self, session_summary):
        """🛑 SYSTEM SHUTDOWN - SHOWING CORRECT SESSION DATA"""
        try:
            # Extract session data properly
            balance = session_summary.get("balance_usd", 0)
            
            # TODAY's performance (not all-time)
            today_trades = session_summary.get("today_trades", 0)
            today_pnl = session_summary.get("today_pnl_usd", 0)
            today_win_rate = session_summary.get("today_win_rate", 0)
            today_wins = session_summary.get("today_wins", 0)
            
            # All-time stats
            total_trades = session_summary.get("total_trades", 0)
            total_pnl = session_summary.get("total_pnl_usd", 0)
            profit_factor = session_summary.get("profit_factor", 0)
            
            market_type = session_summary.get("market_type", "SPOT")
            market_emoji = self.market_emojis.get(market_type, "📊")
            
            # Result based on TODAY's performance
            if today_pnl > 0:
                session_result = "PROFITABLE SESSION"
                result_emoji = "✨"
                color = self.colors["profit"]
            elif today_pnl < 0:
                session_result = "LOSING SESSION"
                result_emoji = "💔"
                color = self.colors["loss"]
            else:
                session_result = "BREAK EVEN"
                result_emoji = "➖"
                color = self.colors["neutral"]
            
            embed = {
                "title": f"🛑 HYPERION SHUTDOWN • {market_emoji}",
                "description": f"**{session_result}** {result_emoji}",
                "color": color,
                "fields": [
                    {
                        "name": "📅 Today's Results",
                        "value": f"Trades: `{today_trades}`\nWins: `{today_wins}`\nWin Rate: `{today_win_rate:.0f}%`\nP&L: `${today_pnl:+.2f}`",
                        "inline": True
                    },
                    {
                        "name": "💰 Final Balance",
                        "value": f"`${balance:.0f}`",
                        "inline": True
                    },
                    {
                        "name": "📊 All-Time Stats",
                        "value": f"Total Trades: `{total_trades}`\nTotal P&L: `${total_pnl:+.2f}`\nProfit Factor: `{profit_factor:.2f}`",
                        "inline": True
                    }
                ],
                "footer": {"text": f"🚀 Hyperion Systems • Session Complete"},
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
            
            self._send_discord_embed("", embed)
            self.quantum_log("🛑 Hyperion Systems shutting down. Session complete!", "INFO")
            
        except Exception as e:
            self.quantum_log(f"Shutdown message error: {str(e)}", "ERROR")

    def send_critical_alert(self, message, priority="WARNING"):
        """🚨 CRITICAL SYSTEM ALERT - WITH DUPLICATE PREVENTION"""
        # Check for duplicate
        if self._is_duplicate_alert(f"CRITICAL_{priority}", message):
            return  # Skip duplicate alert
        
        alert_type = priority.upper() if priority else "WARNING"
        
        if alert_type == "CRITICAL":
            emoji = "🚨"
            color = self.colors["critical"]
            content = "@everyone"
        elif alert_type == "ERROR":
            emoji = "❌"
            color = self.colors["error"]
            content = ""
        else:
            emoji = "⚠️"
            color = self.colors["warning"]
            content = ""
        
        embed = {
            "title": f"{emoji} HYPERION ALERT: {alert_type}",
            "description": f"⚡ {message}",
            "color": color,
            "fields": [
                {
                    "name": "🕐 Stardate",
                    "value": f"`{datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')}`",
                    "inline": True
                },
                {
                    "name": "📈 Dimension",
                    "value": f"`{'FUTURES' if config.ENABLE_FUTURES else 'SPOT'}`",
                    "inline": True
                },
                {
                    "name": "🌌 Shield Status",
                    "value": f"`{'QUANTUM' if config.USE_OCO_ORDERS else 'STANDARD'}`",
                    "inline": True
                }
            ],
            "footer": {"text": f"🚀 Hyperion Command • RED ALERT!"},
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        
        self._send_discord_embed(content, embed)
        log_level = alert_type if alert_type in ["CRITICAL", "ERROR", "WARNING"] else "WARNING"
        self.quantum_log(f"{alert_type}: {message}", log_level)

    def send_exit_order_repair_alert(self, symbol, missing_orders):
        """Send alert when exit orders need repair"""
        missing_str = ", ".join(missing_orders)
        
        embed = {
            "title": f"🔧 EXIT ORDER REPAIR - {symbol}",
            "description": f"Missing orders detected: {missing_str}",
            "color": self.colors["warning"],
            "fields": [
                {
                    "name": "🔍 Status",
                    "value": "Attempting automatic repair",
                    "inline": True
                },
                {
                    "name": "⚠️ Risk Level",
                    "value": "UNPROTECTED POSITION",
                    "inline": True
                }
            ],
            "footer": {"text": f"Hyperion Safety System • {datetime.now(timezone.utc).strftime('%I:%M %p UTC')}"},
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        
        self._send_discord_embed("", embed)
        self.quantum_log(f"🔧 Repairing exit orders for {symbol}: {missing_str}", "WARNING")

    def send_margin_warning(self, margin_ratio, at_risk_symbols):
        """Send margin warning alert"""
        symbols_str = ", ".join(at_risk_symbols[:5])  # Show max 5 symbols
        
        embed = {
            "title": "⚠️ MARGIN WARNING",
            "description": f"Margin ratio: {margin_ratio:.2%}",
            "color": self.colors["warning"],
            "fields": [
                {
                    "name": "🔥 At Risk Positions",
                    "value": symbols_str if symbols_str else "None identified",
                    "inline": False
                },
                {
                    "name": "📊 Recommended Action",
                    "value": "Consider reducing position size or adding margin",
                    "inline": False
                }
            ],
            "footer": {"text": "Hyperion Risk Management"},
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        
        self._send_discord_embed("", embed)
        self.quantum_log(f"⚠️ MARGIN WARNING: Ratio {margin_ratio:.2%}", "WARNING")

    def _send_discord_embed(self, content, embed):
        """📡 Send to Discord with PERSISTENCE for failed messages"""
        if not self.enable_discord:
            return
        
        # Rate limiting
        current_time = time.time()
        time_since_last = current_time - self.last_discord_time
        
        if time_since_last < self.discord_rate_limit:
            time.sleep(self.discord_rate_limit - time_since_last)
        
        max_retries = 3
        retry_count = 0
        
        while retry_count < max_retries:
            try:
                payload = {"content": content, "embeds": [embed]}
                response = requests.post(
                    self.webhook_url, 
                    json=payload, 
                    timeout=5,
                    headers={"Content-Type": "application/json"}  # Explicit header
                )
                
                if response.status_code == 204:
                    # Success
                    self.last_discord_time = time.time()
                    return True
                
                elif response.status_code == 429:
                    # Rate limited - get retry after
                    retry_after = response.json().get('retry_after', 5)
                    print(f"⚠️ Discord rate limit - waiting {retry_after}s")
                    
                    if retry_after < 60:  # Only wait if reasonable
                        time.sleep(retry_after)
                        retry_count += 1
                        continue
                    else:
                        # Too long - save for later
                        self._save_failed_discord(content, embed)
                        return False
                        
                else:
                    print(f"⚠️ Discord error: {response.status_code}")
                    retry_count += 1
                    
            except requests.exceptions.Timeout:
                print("⚠️ Discord timeout")
                retry_count += 1
                
            except requests.exceptions.ConnectionError:
                retry_count += 1
                if retry_count < max_retries:
                    time.sleep(2)  # Wait before retry
                    continue
                
            except Exception as e:
                print(f"🚨 Discord send error: {str(e)}")
                retry_count += 1
            
            if retry_count < max_retries:
                time.sleep(2 ** retry_count)  # Exponential backoff
        
        # All retries failed - save for later
        self._save_failed_discord(content, embed)
        print(f"🚨 Discord send failed after {max_retries} retries - saved for retry")
        return False

    def _save_failed_discord(self, content, embed):
        """Save failed Discord messages for retry"""
        try:
            self.failed_discord_messages.append({
                'content': content,
                'embed': embed,
                'timestamp': time.time(),
                'retry_count': 0
            })
        except Exception as e:
            print(f"⚠️ Could not save failed message: {str(e)}")

    def _retry_failed_discord(self):
        """Background thread to retry failed Discord messages"""
        max_consecutive_failures = 10
        consecutive_failures = 0
        
        while True:
            try:
                time.sleep(30)  # Check every 30 seconds
                
                if not self.failed_discord_messages:
                    consecutive_failures = 0  # Reset on success
                    continue
                
                # Try to send oldest failed message
                current_time = time.time()
                messages_to_retry = []
                
                # Collect messages older than 10 seconds
                for msg in list(self.failed_discord_messages):
                    if current_time - msg['timestamp'] > 10:
                        messages_to_retry.append(msg)
                
                for msg in messages_to_retry:
                    try:
                        # Remove from queue first
                        self.failed_discord_messages.remove(msg)
                        
                        # Try to send
                        if self._send_discord_embed(msg['content'], msg['embed']):
                            print(f"✅ Successfully sent previously failed Discord message")
                        else:
                            # Failed again - increment retry count
                            msg['retry_count'] += 1
                            if msg['retry_count'] < 10:  # Max 10 retries
                                msg['timestamp'] = current_time  # Reset timestamp
                                self.failed_discord_messages.append(msg)
                            else:
                                print(f"❌ Dropping Discord message after 10 failed retries")
                                # FIX: Log dropped message for debugging
                                try:
                                    self.quantum_log(f"Dropped Discord message: {msg['embed'].get('title', 'Unknown')}", "WARNING")
                                except:
                                    pass
                        
                        time.sleep(2)  # Don't spam retries
                        
                    except Exception as e:
                        print(f"⚠️ Error retrying Discord message: {str(e)}")
                        
            except Exception as e:
                consecutive_failures += 1
                print(f"⚠️ Discord retry thread error: {str(e)}")
                
                if consecutive_failures >= max_consecutive_failures:
                    print(f"🚨 Discord retry thread failing repeatedly - pausing for 5 minutes")
                    time.sleep(300)  # Wait 5 minutes
                    consecutive_failures = 0
                else:
                    time.sleep(60)  # Wait 1 minute on error

print("🚀 MODULAR NOTIFICATION SYSTEM READY!")
print(f"📈 Market type: {'FUTURES' if config.ENABLE_FUTURES else 'SPOT'}")
print(f"🎯 OCO Orders: {'ENABLED' if config.USE_OCO_ORDERS else 'DISABLED'}")
print("🎯 Per Aspera Ad Astra!")