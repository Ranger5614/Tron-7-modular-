# advanced_logger.py - PROFESSIONAL TRADING LOGGER
"""
🚀 HYPERION ADVANCED LOGGER - INSTITUTIONAL GRADE
- Professional Excel reports suitable for asset management presentation
- Clear P&L tracking with advanced metrics
- Clean folder structure
- Comprehensive trade analysis
"""

import json
import os
import threading
import time
import uuid
from datetime import datetime, date, timedelta, timezone
from collections import defaultdict
import pandas as pd
import numpy as np
from openpyxl import Workbook
from openpyxl.styles import PatternFill, Font, Alignment, Border, Side, NamedStyle
from openpyxl.chart import LineChart, BarChart, PieChart, Reference, DoughnutChart
from openpyxl.utils.dataframe import dataframe_to_rows
from openpyxl.utils import get_column_letter
from openpyxl.formatting.rule import CellIsRule, ColorScaleRule
from datetime import datetime, date, timedelta, timezone
import config


class HyperionAdvancedLogger:
    def __init__(self):
        """Initialize the professional logger"""
        print(f"\n{'='*60}")
        print(f"🚀 INITIALIZING HYPERION PROFESSIONAL LOGGER")
        print(f"{'='*60}\n")
        
        # Session info
        self.session_id = f"HYPERION_{int(time.time())}"
        self.session_start = datetime.now(timezone.utc)  # FIXED: Use UTC consistently
        
        # Create ONLY necessary directories
        self.base_dir = config.LOG_DIR
        if not os.path.exists(self.base_dir):  # FIXED: Validate before operations
            os.makedirs(self.base_dir, exist_ok=True)
        os.makedirs(f"{self.base_dir}/daily_reports", exist_ok=True)
        
        # File paths
        self.events_file = f"{self.base_dir}/trading_events.jsonl"
        self.excel_file = f"{self.base_dir}/daily_reports/trading_report_{date.today()}.xlsx"
        
        # Trade tracking with unique IDs - THREAD SAFE
        self.active_trades = {}
        self.trades_lock = threading.RLock()  # ADDED: Thread safety for trades
        
        # In-memory counters
        self.signal_count = 0
        self.trade_count = 0
        self.error_count = 0
        self.order_count = 0
        
        # Report generation settings
        self.auto_report_interval = 1800  # 30 minutes
        self.auto_report_enabled = True
        self.report_on_trade_close = True
        self.trades_since_report = 0
        self.last_report_time = time.time()
        
        # Start background report generator
        self.report_thread = threading.Thread(target=self._background_report_generator, daemon=True)
        self.report_thread.start()
        self.last_cleanup_time = time.time()

        # Performance tracking with size limit
        self.performance_tracking = {}
        self.max_performance_entries = 1000  # ADDED: Prevent memory leak
        
        # Define professional styles
        self._define_excel_styles()
        
        print(f"✅ Logger initialized successfully")
        print(f"📁 Events log: {self.events_file}")
        print(f"📊 Excel reports: {self.base_dir}/daily_reports/")
        print(f"🔄 Auto-reports every {self.auto_report_interval/60:.0f} minutes")
        
        # Log session start
        self._log_event("SESSION_START", {
            "session_id": self.session_id,
            "config": {
                "strategy": config.STRATEGY_CLASS,
                "market": "FUTURES" if config.ENABLE_FUTURES else "SPOT",
                "position_size": config.FIXED_POSITION_SIZE_USD,
                "max_positions": config.MAX_TOTAL_POSITIONS,
                "tp_pct": getattr(config, 'FIXED_TP_PCT', 0.008) * 100,
                "sl_pct": getattr(config, 'FIXED_SL_PCT', 0.007) * 100
            }
        })

    def _define_excel_styles(self):
        """Define professional Excel styles"""
        self.styles = {
            'header': {
                'font': Font(name='Arial', size=11, bold=True, color="FFFFFF"),
                'fill': PatternFill(start_color="2C3E50", end_color="2C3E50", fill_type="solid"),
                'alignment': Alignment(horizontal="center", vertical="center"),
                'border': Border(
                    left=Side(style='thin', color='FFFFFF'),
                    right=Side(style='thin', color='FFFFFF'),
                    top=Side(style='thin', color='FFFFFF'),
                    bottom=Side(style='thin', color='FFFFFF')
                )
            },
            'title': {
                'font': Font(name='Arial Black', size=24, bold=True, color="2C3E50"),
                'alignment': Alignment(horizontal="center", vertical="center")
            },
            'subtitle': {
                'font': Font(name='Arial', size=14, bold=True, color="34495E"),
                'alignment': Alignment(horizontal="left", vertical="center")
            },
            'profit': {
                'font': Font(name='Arial', size=11, bold=True, color="27AE60"),
                'fill': PatternFill(start_color="E8F8F5", end_color="E8F8F5", fill_type="solid")
            },
            'loss': {
                'font': Font(name='Arial', size=11, bold=True, color="E74C3C"),
                'fill': PatternFill(start_color="FADBD8", end_color="FADBD8", fill_type="solid")
            },
            'neutral': {
                'font': Font(name='Arial', size=10),
                'alignment': Alignment(horizontal="center", vertical="center")
            }
        }
    
    def cleanup_performance_tracking(self):
        """Prevent memory leak in performance tracking"""
        if len(self.performance_tracking) > self.max_performance_entries:
            # Keep only recent entries
            sorted_keys = sorted(self.performance_tracking.keys())
            for key in sorted_keys[:-self.max_performance_entries]:
                del self.performance_tracking[key]

    def get_performance_summary(self):
        """Get summary of performance tracking - THREAD SAFE"""
        try:
            if not self.performance_tracking:
                return {}
            
            # Calculate averages
            total_scans = len(self.performance_tracking)
            avg_duration = sum(p['duration'] for p in self.performance_tracking.values()) / total_scans
            avg_efficiency = sum(p['efficiency'] for p in self.performance_tracking.values()) / total_scans
            
            return {
                'total_scans': total_scans,
                'avg_duration': avg_duration,
                'avg_efficiency': avg_efficiency,
                'memory_usage': len(self.performance_tracking)
            }
        except Exception as e:
            print(f"⚠️ Error getting performance summary: {e}")
            return {}
    
    def _log_event(self, event_type: str, data: dict):
        """Core logging - bulletproof JSONL append"""
        try:
            log_entry = {
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "session_id": self.session_id,
                "event": event_type,
                "data": data
            }
            
            with open(self.events_file, 'a') as f:
                f.write(json.dumps(log_entry) + '\n')
                f.flush()
                os.fsync(f.fileno())
                
        except Exception as e:
            print(f"🚨 CRITICAL: Failed to log {event_type}: {e}")

    # === PUBLIC LOGGING METHODS ===
    
    def log_signal_detected(self, signal_data):
        """Log signal detection with quality info"""
        self.signal_count += 1
        signal_data['signal_number'] = self.signal_count
        self._log_event("SIGNAL_DETECTED", signal_data)
        
        quality = signal_data.get('quality_score', 0)
        print(f"🎯 Signal #{self.signal_count}: {signal_data.get('symbol')} "
              f"{signal_data.get('action')} (Q: {quality:.3f})")

    def log_order_attempt(self, symbol, side, quantity, price, order_type="MARKET"):
        """Log order attempt"""
        self.order_count += 1
        self._log_event("ORDER_ATTEMPT", {
            "order_number": self.order_count,
            "symbol": symbol,
            "side": side,
            "quantity": quantity,
            "price": price,
            "order_type": order_type
        })
        return time.time()

    def log_order_result(self, symbol, order_response, start_time, success=True):
        """Log order result"""
        duration_ms = (time.time() - start_time) * 1000
        self._log_event("ORDER_RESULT", {
            "symbol": symbol,
            "success": success,
            "duration_ms": duration_ms,
            "order_id": order_response.get("orderId") if order_response else None,
            "status": order_response.get("status") if order_response else "FAILED"
        })

    def log_position_entry(self, position_data):
        """Log position entry with unique trade ID"""
        with self.trades_lock:  # ADDED: Thread safety
            trade_id = str(uuid.uuid4())
            symbol = position_data.get('symbol')
            
            self.active_trades[symbol] = trade_id
            position_data['trade_id'] = trade_id
            position_data['trade_number'] = len(self.active_trades)
            
            self._log_event("TRADE_OPENED", position_data)
            
            print(f"✅ ENTRY #{len(self.active_trades)}: {symbol} {position_data.get('direction')} "
                f"@ ${position_data.get('entry_price', 0):.4f} [ID: {trade_id[:8]}...]")

    def log_position_exit(self, exit_data):
        """Log position exit with matching trade ID"""
        with self.trades_lock:  # ADDED: Thread safety
            symbol = exit_data.get('symbol')
            
            trade_id = self.active_trades.get(symbol)
            if trade_id:
                exit_data['trade_id'] = trade_id
                del self.active_trades[symbol]
            else:
                exit_data['trade_id'] = str(uuid.uuid4())
                print(f"⚠️ No active trade ID found for {symbol}, using new ID")
            
            self.trade_count += 1
            self.trades_since_report += 1
            exit_data['cumulative_trades'] = self.trade_count
            
            self._log_event("TRADE_CLOSED", exit_data)
            
            pnl = exit_data.get('pnl_usd', 0)
            print(f"{'💰' if pnl > 0 else '💸'} EXIT #{self.trade_count}: {symbol} | "
                f"P&L: ${pnl:.2f} ({exit_data.get('pnl_pct', 0):.1f}%) | "
                f"{exit_data.get('exit_type', 'UNKNOWN')}")
            
            # Auto-generate report after X trades
            if self.report_on_trade_close and self.trades_since_report >= 5:
                self._generate_report_safe()

    def log_position_update(self, symbol, position_data, current_price):
        """Log position update"""
        trade_id = self.active_trades.get(symbol)
        
        self._log_event("POSITION_UPDATE", {
            "symbol": symbol,
            "trade_id": trade_id,
            "current_price": current_price,
            "unrealized_pnl": position_data.get("unrealized_pnl", 0),
            "unrealized_pnl_pct": position_data.get("unrealized_pnl_pct", 0)
        })

    def log_error(self, component, message, context=None):
        """Log error with severity classification"""
        self.error_count += 1
        
        severity = "HIGH"
        if any(word in message.lower() for word in ['failed', 'error', 'critical']):
            severity = "CRITICAL"
        elif any(word in message.lower() for word in ['warning', 'retry']):
            severity = "MEDIUM"
        
        self._log_event("ERROR", {
            "error_number": self.error_count,
            "component": component,
            "message": message,
            "severity": severity,
            "context": context or {}
        })
        
        emoji = "🚨" if severity == "CRITICAL" else "⚠️"
        print(f"{emoji} Error #{self.error_count} [{component}]: {message}")

    def log_account_snapshot(self, account_data, positions_data):
        """Log account snapshot"""
        self._log_event("ACCOUNT_SNAPSHOT", {
            "balance": account_data.get("balance", 0),
            "equity": account_data.get("equity", account_data.get("balance", 0)),
            "positions": len(positions_data),
            "total_unrealized_pnl": sum(p.get("unrealized_pnl", 0) for p in positions_data.values()),
            "margin_ratio": account_data.get("margin_ratio", 0)
        })

    def log_scan_performance(self, scan_number, duration_seconds, pairs_scanned, signals_found):
        """Log scan performance with memory cleanup"""
        self._log_event("SCAN_COMPLETE", {
            "scan_number": scan_number,
            "duration_seconds": duration_seconds,
            "pairs_scanned": pairs_scanned,
            "signals_found": signals_found,
            "signals_per_pair": signals_found / pairs_scanned if pairs_scanned > 0 else 0
        })
        
        # Store in performance tracking
        timestamp = datetime.now(timezone.utc).isoformat()  # FIX: Use UTC
        self.performance_tracking[timestamp] = {
            "scan_number": scan_number,
            "duration": duration_seconds,
            "efficiency": signals_found / pairs_scanned if pairs_scanned > 0 else 0
        }

    def get_session_metrics(self):
        """Get current session metrics"""
        uptime_hours = (datetime.now(timezone.utc) - self.session_start).total_seconds() / 3600
        
        return {
            "session_id": self.session_id,
            "uptime_hours": uptime_hours,
            "signals_detected": self.signal_count,
            "trades_completed": self.trade_count,
            "errors_logged": self.error_count,
            "orders_placed": self.order_count,
            "active_trades": len(self.active_trades)
        }

    def export_session_report(self):
        """Export final session report"""
        self._log_event("SESSION_END", {
            "duration_hours": (datetime.now(timezone.utc) - self.session_start).total_seconds() / 3600,
            "total_signals": self.signal_count,
            "total_trades": self.trade_count,
            "total_errors": self.error_count,
            "total_orders": self.order_count
        })
        
        print(f"📊 Generating final session report...")
        self._generate_report_safe()

    def rotate_event_log(self):
        """Rotate event log if it gets too large"""
        try:
            if os.path.exists(self.events_file):
                file_size = os.path.getsize(self.events_file)
                # FIX: Rotate at 50MB instead of 100MB for better performance
                if file_size > 50 * 1024 * 1024:  # 50MB
                    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
                    archive_file = f"{self.events_file}.{timestamp}"
                    
                    # FIX: Use temp file for safer rotation
                    temp_file = f"{archive_file}.tmp"
                    
                    try:
                        # Copy to temp file first
                        import shutil
                        shutil.copy2(self.events_file, temp_file)
                        
                        # Clear original file
                        with open(self.events_file, 'w') as f:
                            f.write(f"# Log rotated at {datetime.now(timezone.utc).isoformat()}\n")
                        
                        # Rename temp to archive
                        os.rename(temp_file, archive_file)
                        print(f"📄 Rotated event log to {archive_file}")
                        
                        # Try compression in background
                        try:
                            import gzip
                            import threading
                            
                            def compress_async():
                                with open(archive_file, 'rb') as f_in:
                                    with gzip.open(f"{archive_file}.gz", 'wb') as f_out:
                                        f_out.writelines(f_in)
                                os.remove(archive_file)
                                print(f"📦 Compressed archive to {archive_file}.gz")
                            
                            threading.Thread(target=compress_async, daemon=True).start()
                        except:
                            pass
                            
                    except Exception as e:
                        print(f"⚠️ Rotation failed: {e}")
                        if os.path.exists(temp_file):
                            os.remove(temp_file)
                            
        except Exception as e:
            print(f"⚠️ Log rotation error: {e}")

    # === AUTOMATIC REPORT GENERATION ===

    def _background_report_generator(self):
        """Background thread for periodic report generation"""
        while True:
            try:
                time.sleep(60)  # Check every minute
                
                if not self.auto_report_enabled:
                    continue
                
                time_since_report = time.time() - self.last_report_time
                
                # FIX: Clean up performance tracking every hour
                if time.time() - self.last_cleanup_time > 3600:
                    self.cleanup_performance_tracking()
                    self.last_cleanup_time = time.time()
                
                if time_since_report >= self.auto_report_interval:
                    print(f"🔄 Auto-generating scheduled report...")
                    self._generate_report_safe()
                    self.cleanup_performance_tracking()

            except Exception as e:
                print(f"⚠️ Report generator thread error: {e}")
                time.sleep(60)

    def _generate_report_safe(self):
        """Safely generate comprehensive report - NON-BLOCKING"""
        def _generate_async():
            try:
                print(f"📊 Starting report generation...")
                start_time = time.time()
                
                # Load all events
                events_df = self._load_events()
                if events_df.empty:
                    print("📊 No events to report yet")
                    return
                
                # Generate comprehensive report
                self._generate_comprehensive_report(events_df)
                
                duration = time.time() - start_time
                print(f"✅ Report generated successfully in {duration:.1f}s")
                
                self.last_report_time = time.time()
                self.trades_since_report = 0
                
            except Exception as e:
                print(f"⚠️ Report generation error (trading continues): {e}")
                import traceback
                traceback.print_exc()
        
        # Run in separate thread to avoid blocking
        report_thread = threading.Thread(target=_generate_async, daemon=True)
        report_thread.start()

    def _load_events(self):
        """Load all events into DataFrame"""
        events = []
        try:
            with open(self.events_file, 'r') as f:
                for line in f:
                    if line.strip():
                        events.append(json.loads(line))
        except FileNotFoundError:
            return pd.DataFrame()
        
        return pd.DataFrame(events)

    def _generate_comprehensive_report(self, events_df):
        """Generate professional Excel report - UTC STANDARDIZED"""
        trades_opened = events_df[events_df['event'] == 'TRADE_OPENED'].copy()
        trades_closed = events_df[events_df['event'] == 'TRADE_CLOSED'].copy()
        signals = events_df[events_df['event'] == 'SIGNAL_DETECTED'].copy()
        errors = events_df[events_df['event'] == 'ERROR'].copy()
        orders = events_df[events_df['event'].isin(['ORDER_ATTEMPT', 'ORDER_RESULT'])].copy()
        
        trades_df = self._build_trades_with_ids(trades_opened, trades_closed)
        
        metrics = self._calculate_comprehensive_metrics(trades_df, signals, orders)
        
        self._generate_professional_excel(trades_df, signals, errors, orders, metrics)

    
    def _build_trades_with_ids(self, trades_opened, trades_closed):
        """Build trades dataframe with matching trade IDs"""
        # FIX: Proper DataFrame empty check
        if (isinstance(trades_opened, pd.DataFrame) and trades_opened.empty) or \
        (isinstance(trades_closed, pd.DataFrame) and trades_closed.empty) or \
        (isinstance(trades_opened, list) and not trades_opened) or \
        (isinstance(trades_closed, list) and not trades_closed) or \
        trades_opened is None or trades_closed is None:
            return pd.DataFrame()
        
        opens_df = pd.DataFrame(trades_opened)
        closes_df = pd.DataFrame(trades_closed)
        
        # Debug: Check what columns we actually have
        print(f"DEBUG: opens_df columns: {opens_df.columns.tolist() if not opens_df.empty else 'EMPTY'}")
        print(f"DEBUG: closes_df columns: {closes_df.columns.tolist() if not closes_df.empty else 'EMPTY'}")
        
        # Check if required columns exist
        required_opens = ['symbol', 'direction', 'entry_price', 'quantity', 'timestamp']
        required_closes = ['symbol', 'exit_price', 'pnl_usd', 'pnl_pct', 'exit_type', 'timestamp']
        
        for col in required_opens:
            if col not in opens_df.columns:
                print(f"WARNING: Missing column '{col}' in opens_df")
                return pd.DataFrame()
        
        for col in required_closes:
            if col not in closes_df.columns:
                print(f"WARNING: Missing column '{col}' in closes_df")
                return pd.DataFrame()
        
        # Extract data with proper timezone handling
        opens_data = pd.DataFrame({
            'symbol': opens_df['symbol'].values,
            'direction': opens_df['direction'].values,
            'entry_price': opens_df['entry_price'].values,
            'quantity': opens_df['quantity'].values,
        })
        
        closes_data = pd.DataFrame({
            'symbol': closes_df['symbol'].values,
            'exit_price': closes_df['exit_price'].values,
            'pnl_usd': closes_df['pnl_usd'].values,
            'pnl_pct': closes_df['pnl_pct'].values,
            'exit_type': closes_df['exit_type'].values,
        })
        
        # FIXED: Handle both timezone-aware and naive timestamps
        opens_data['open_timestamp'] = pd.to_datetime(opens_df['timestamp'].values, utc=True)
        closes_data['close_timestamp'] = pd.to_datetime(closes_df['timestamp'].values, utc=True)
        
        # Match trades by symbol and time proximity
        matched_trades = []
        
        for idx, close_trade in closes_data.iterrows():
            symbol = close_trade['symbol']
            close_time = close_trade['close_timestamp']
            
            # Find the most recent open for this symbol before the close
            symbol_opens = opens_data[opens_data['symbol'] == symbol]
            valid_opens = symbol_opens[symbol_opens['open_timestamp'] < close_time]
            
            if not valid_opens.empty:
                # Get the most recent valid open
                best_open_idx = valid_opens['open_timestamp'].idxmax()
                open_trade = opens_data.loc[best_open_idx]
                
                # Create matched trade
                matched_trade = {
                    'trade_id': f"{symbol}_{open_trade['open_timestamp'].strftime('%Y%m%d_%H%M%S')}",
                    'symbol': symbol,
                    'direction': open_trade['direction'],
                    'entry_price': open_trade['entry_price'],
                    'exit_price': close_trade['exit_price'],
                    'quantity': open_trade['quantity'],
                    'pnl_usd': close_trade['pnl_usd'],
                    'pnl_pct': close_trade['pnl_pct'],
                    'exit_type': close_trade['exit_type'],
                    'open_timestamp': open_trade['open_timestamp'],
                    'close_timestamp': close_trade['close_timestamp'],
                    'duration_hours': (close_trade['close_timestamp'] - open_trade['open_timestamp']).total_seconds() / 3600
                }
                matched_trades.append(matched_trade)
                
                # Remove the matched open to avoid double-matching
                opens_data = opens_data.drop(best_open_idx)
        
        return pd.DataFrame(matched_trades)

    def _calculate_comprehensive_metrics(self, trades_df, signals_df, orders_df):
        """Calculate all metrics including advanced statistics - WITH SAFE DIVISION"""
        metrics = {}
        
        if not trades_df.empty:
            total_trades = len(trades_df)
            winning_trades = trades_df[trades_df['pnl_usd'] > 0]
            losing_trades = trades_df[trades_df['pnl_usd'] <= 0]
            
            # Basic metrics
            metrics['total_trades'] = total_trades
            metrics['winning_trades'] = len(winning_trades)
            metrics['losing_trades'] = len(losing_trades)
            metrics['win_rate'] = (len(winning_trades) / total_trades * 100) if total_trades > 0 else 0
            
            # P&L metrics
            metrics['total_pnl'] = trades_df['pnl_usd'].sum()
            metrics['avg_pnl'] = trades_df['pnl_usd'].mean() if total_trades > 0 else 0
            metrics['avg_win'] = winning_trades['pnl_usd'].mean() if len(winning_trades) > 0 else 0
            metrics['avg_loss'] = losing_trades['pnl_usd'].mean() if len(losing_trades) > 0 else 0
            
            # Profit factor - SAFE DIVISION
            gross_profit = winning_trades['pnl_usd'].sum() if len(winning_trades) > 0 else 0
            gross_loss = abs(losing_trades['pnl_usd'].sum()) if len(losing_trades) > 0 else 0
            metrics['profit_factor'] = (gross_profit / gross_loss) if gross_loss > 0 else (999.99 if gross_profit > 0 else 0)
            
            # Risk metrics
            metrics['sharpe_ratio'] = self._calculate_sharpe_ratio(trades_df)
            metrics['max_drawdown'] = self._calculate_max_drawdown(trades_df)
            metrics['recovery_factor'] = abs(metrics['total_pnl'] / metrics['max_drawdown']) if metrics['max_drawdown'] < 0 else 0
            
            # Best/worst
            metrics['best_trade'] = trades_df['pnl_usd'].max() if total_trades > 0 else 0
            metrics['worst_trade'] = trades_df['pnl_usd'].min() if total_trades > 0 else 0
            metrics['largest_win'] = trades_df['pnl_pct'].max() if total_trades > 0 else 0
            metrics['largest_loss'] = trades_df['pnl_pct'].min() if total_trades > 0 else 0
            
            # Time analysis - SAFE DIVISION
            metrics['avg_hold_time_bars'] = trades_df['hold_time_bars'].mean() if total_trades > 0 else 0
            metrics['avg_winning_time'] = winning_trades['hold_time_bars'].mean() if len(winning_trades) > 0 else 0
            metrics['avg_losing_time'] = losing_trades['hold_time_bars'].mean() if len(losing_trades) > 0 else 0
            
            # Exit type breakdown
            metrics['exit_types'] = trades_df['exit_type'].value_counts().to_dict() if 'exit_type' in trades_df.columns else {}
            
            # Perfect exits
            if 'perfect_exit' in trades_df.columns:
                metrics['perfect_exits'] = len(trades_df[trades_df['perfect_exit'] == 'YES'])
                metrics['perfect_exit_rate'] = (metrics['perfect_exits'] / total_trades * 100) if total_trades > 0 else 0
            else:
                metrics['perfect_exits'] = 0
                metrics['perfect_exit_rate'] = 0
                
        else:
            # Default values with safe initialization
            metrics = {
                'total_trades': 0, 'winning_trades': 0, 'losing_trades': 0, 'win_rate': 0, 
                'total_pnl': 0, 'avg_pnl': 0, 'avg_win': 0, 'avg_loss': 0, 'profit_factor': 0,
                'sharpe_ratio': 0, 'max_drawdown': 0, 'recovery_factor': 0, 'best_trade': 0,
                'worst_trade': 0, 'largest_win': 0, 'largest_loss': 0, 'avg_hold_time_bars': 0,
                'avg_winning_time': 0, 'avg_losing_time': 0, 'perfect_exits': 0, 'perfect_exit_rate': 0,
                'exit_types': {}
            }
        
        # Signal metrics - SAFE DIVISION
        if not signals_df.empty:
            signals_data = pd.json_normalize(signals_df['data'].tolist())
            metrics['total_signals'] = len(signals_data)
            metrics['avg_signal_quality'] = signals_data['quality_score'].mean() if 'quality_score' in signals_data and len(signals_data) > 0 else 0
            metrics['signal_execution_rate'] = (metrics['total_trades'] / metrics['total_signals'] * 100) if metrics['total_signals'] > 0 else 0
        else:
            metrics['total_signals'] = 0
            metrics['avg_signal_quality'] = 0
            metrics['signal_execution_rate'] = 0
        
        return metrics

    def _calculate_sharpe_ratio(self, trades_df):
        """Calculate Sharpe ratio (annualized)"""
        if trades_df.empty:
            return 0
        
        # Group by day and calculate daily returns
        trades_df['date'] = pd.to_datetime(trades_df['close_timestamp']).dt.date
        daily_returns = trades_df.groupby('date')['pnl_usd'].sum()
        
        if len(daily_returns) < 2:
            return 0
        
        # Calculate Sharpe (assuming 252 trading days)
        avg_return = daily_returns.mean()
        std_return = daily_returns.std()
        
        if std_return == 0:
            return 0
        
        sharpe = (avg_return / std_return) * np.sqrt(252)
        return round(sharpe, 2)

    def _calculate_max_drawdown(self, trades_df):
        """Calculate maximum drawdown"""
        if trades_df.empty:
            return 0
        
        # Sort by time and calculate cumulative P&L
        trades_df = trades_df.sort_values('close_timestamp')
        cumulative_pnl = trades_df['pnl_usd'].cumsum()
        
        # Calculate running maximum
        running_max = cumulative_pnl.expanding().max()
        
        # Calculate drawdown
        drawdown = cumulative_pnl - running_max
        
        return drawdown.min()

    def _generate_professional_excel(self, trades_df, signals_df, errors_df, orders_df, metrics):
        """Generate institutional-grade Excel report - WITH SAFE FILE HANDLING"""
        wb = None
        try:
            wb = Workbook()
            
            self._create_executive_summary(wb.active, metrics, trades_df)
            wb.active.title = "Executive Summary"
            
            if not trades_df.empty:
                trades_sheet = wb.create_sheet("Trade Analysis")
                self._create_trade_analysis_sheet(trades_sheet, trades_df)
            
            perf_sheet = wb.create_sheet("Performance Metrics")
            self._create_performance_metrics_sheet(perf_sheet, trades_df, metrics)
            
            risk_sheet = wb.create_sheet("Risk Analysis")
            self._create_risk_analysis_sheet(risk_sheet, trades_df, metrics)
            
            if not trades_df.empty:
                symbol_sheet = wb.create_sheet("Symbol Analysis")
                self._create_enhanced_symbol_sheet(symbol_sheet, trades_df)
            
            if not trades_df.empty:
                time_sheet = wb.create_sheet("Time Analysis")
                self._create_time_analysis_sheet(time_sheet, trades_df)
            
            if not signals_df.empty:
                signal_sheet = wb.create_sheet("Signal Analysis")
                self._create_signal_analysis_sheet(signal_sheet, signals_df)
            
            if not errors_df.empty:
                error_sheet = wb.create_sheet("System Errors")
                self._create_error_sheet(error_sheet, errors_df)
            
            timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
            filename = f"{self.base_dir}/daily_reports/trading_report_{date.today()}_{timestamp}.xlsx"
            
            if self._safe_excel_generation(wb, filename):
                print(f"📊 Professional report saved: {filename}")
            else:
                print(f"⚠️ Failed to save report: {filename}")
                
        except Exception as e:
            print(f"⚠️ Excel generation error: {str(e)}")
            import traceback
            traceback.print_exc()
        finally:
            if wb:
                try:
                    wb.close()
                except:
                    pass

    def _safe_excel_generation(self, wb, filename):
        """Safely save Excel with proper exception handling"""
        temp_file = None
        try:
            # Use temp file for atomic write
            temp_file = f"{filename}.tmp"
            wb.save(temp_file)
            
            # Atomic rename
            if os.path.exists(filename):
                backup_file = f"{filename}.bak"
                if os.path.exists(backup_file):
                    os.remove(backup_file)
                os.rename(filename, backup_file)
            
            os.rename(temp_file, filename)
            return True
            
        except Exception as e:
            print(f"⚠️ Excel save error: {str(e)}")
            if temp_file and os.path.exists(temp_file):
                try:
                    os.remove(temp_file)
                except:
                    pass
            return False

    def _create_executive_summary(self, ws, metrics, trades_df):
        """Create professional executive summary"""
        ws['A1'] = "TRADING PERFORMANCE REPORT"
        ws['A1'].font = Font(name='Arial Black', size=28, bold=True, color="1A1A1A")
        ws['A1'].alignment = Alignment(horizontal="center", vertical="center")
        ws.merge_cells('A1:H2')
        
        ws['A3'] = f"Report Date: {datetime.now(timezone.utc).strftime('%B %d, %Y')}"
        ws['A3'].font = Font(name='Arial', size=12, color="666666")
        ws.merge_cells('A3:D3')
        
        ws['E3'] = f"Trading Session: {datetime.now(timezone.utc).strftime('%I:%M %p UTC')}"
        ws['E3'].font = Font(name='Arial', size=12, color="666666")
        ws['E3'].alignment = Alignment(horizontal="right")
        ws.merge_cells('E3:H3')
        
        # Add separator line
        for col in range(1, 9):
            ws.cell(row=4, column=col).border = Border(bottom=Side(style='thick', color='E0E0E0'))
        
        # KEY METRICS SECTION - Large P&L Display
        ws['A6'] = "NET PROFIT/LOSS"
        ws['A6'].font = Font(name='Arial', size=14, bold=True, color="666666")
        ws.merge_cells('A6:C6')
        
        # Big P&L number
        pnl_value = metrics.get('total_pnl', 0)
        ws['A7'] = f"${pnl_value:,.2f}"
        if pnl_value >= 0:
            ws['A7'].font = Font(name='Arial Black', size=36, bold=True, color="27AE60")
        else:
            ws['A7'].font = Font(name='Arial Black', size=36, bold=True, color="E74C3C")
        ws['A7'].alignment = Alignment(horizontal="center", vertical="center")
        ws.merge_cells('A7:C9')
        
        # Win rate box
        ws['D6'] = "WIN RATE"
        ws['D6'].font = Font(name='Arial', size=14, bold=True, color="666666")
        ws.merge_cells('D6:E6')
        
        ws['D7'] = f"{metrics.get('win_rate', 0):.1f}%"
        ws['D7'].font = Font(name='Arial Black', size=28, bold=True, color="3498DB")
        ws['D7'].alignment = Alignment(horizontal="center", vertical="center")
        ws.merge_cells('D7:E9')
        
        # Profit factor box
        ws['F6'] = "PROFIT FACTOR"
        ws['F6'].font = Font(name='Arial', size=14, bold=True, color="666666")
        ws.merge_cells('F6:H6')
        
        pf_value = metrics.get('profit_factor', 0)
        ws['F7'] = f"{pf_value:.2f}"
        if pf_value >= 1.5:
            ws['F7'].font = Font(name='Arial Black', size=28, bold=True, color="27AE60")
        elif pf_value >= 1.0:
            ws['F7'].font = Font(name='Arial Black', size=28, bold=True, color="F39C12")
        else:
            ws['F7'].font = Font(name='Arial Black', size=28, bold=True, color="E74C3C")
        ws['F7'].alignment = Alignment(horizontal="center", vertical="center")
        ws.merge_cells('F7:H9')
        
        # Performance Overview Table
        ws['A11'] = "PERFORMANCE OVERVIEW"
        ws['A11'].font = Font(name='Arial', size=16, bold=True, color="2C3E50")
        ws.merge_cells('A11:H11')
        
        # Create performance table
        perf_data = [
            ["Metric", "Value", "Metric", "Value"],
            ["Total Trades", metrics.get('total_trades', 0), "Sharpe Ratio", f"{metrics.get('sharpe_ratio', 0):.2f}"],
            ["Winning Trades", metrics.get('winning_trades', 0), "Max Drawdown", f"${metrics.get('max_drawdown', 0):.2f}"],
            ["Losing Trades", metrics.get('losing_trades', 0), "Recovery Factor", f"{metrics.get('recovery_factor', 0):.2f}"],
            ["Average Win", f"${metrics.get('avg_win', 0):.2f}", "Best Trade", f"${metrics.get('best_trade', 0):.2f}"],
            ["Average Loss", f"${metrics.get('avg_loss', 0):.2f}", "Worst Trade", f"${metrics.get('worst_trade', 0):.2f}"],
            ["Win Rate", f"{metrics.get('win_rate', 0):.1f}%", "Avg Hold Time", f"{metrics.get('avg_hold_time_bars', 0):.1f} bars"],
            ["Signals Found", metrics.get('total_signals', 0), "Signal Quality", f"{metrics.get('avg_signal_quality', 0):.2f}"]
        ]
        
        # Write performance table
        start_row = 13
        for i, row_data in enumerate(perf_data):
            for j, value in enumerate(row_data):
                cell = ws.cell(row=start_row + i, column=j + 1, value=value)
                
                if i == 0:  # Header
                    cell.font = Font(name='Arial', size=11, bold=True, color="FFFFFF")
                    cell.fill = PatternFill(start_color="34495E", end_color="34495E", fill_type="solid")
                    cell.alignment = Alignment(horizontal="center")
                else:
                    if j % 2 == 0:  # Metric names
                        cell.font = Font(name='Arial', size=10, bold=True)
                        cell.fill = PatternFill(start_color="ECF0F1", end_color="ECF0F1", fill_type="solid")
                    else:  # Values
                        cell.font = Font(name='Arial', size=10)
                        cell.alignment = Alignment(horizontal="center")
                        
                        # Color code certain values
                        if isinstance(value, str) and '$' in value:
                            try:
                                num_value = float(value.replace('$', '').replace(',', ''))
                                if num_value > 0:
                                    cell.font = Font(name='Arial', size=10, color="27AE60")
                                elif num_value < 0:
                                    cell.font = Font(name='Arial', size=10, color="E74C3C")
                            except:
                                pass
        
        # Exit Type Distribution
        ws['A23'] = "EXIT TYPE DISTRIBUTION"
        ws['A23'].font = Font(name='Arial', size=16, bold=True, color="2C3E50")
        ws.merge_cells('A23:D23')
        
        exit_types = metrics.get('exit_types', {})
        exit_data = [["Exit Type", "Count", "Percentage"]]
        total_exits = sum(exit_types.values()) if exit_types else 1
        
        for exit_type, count in exit_types.items():
            percentage = (count / total_exits * 100) if total_exits > 0 else 0
            exit_data.append([exit_type, count, f"{percentage:.1f}%"])
        
        # Write exit type table
        for i, row_data in enumerate(exit_data):
            for j, value in enumerate(row_data):
                cell = ws.cell(row=25 + i, column=j + 1, value=value)
                
                if i == 0:  # Header
                    cell.font = Font(name='Arial', size=11, bold=True, color="FFFFFF")
                    cell.fill = PatternFill(start_color="34495E", end_color="34495E", fill_type="solid")
                else:
                    cell.font = Font(name='Arial', size=10)
                    
                    # Color code exit types
                    if j == 0 and i > 0:  # Exit type column
                        if value == "TAKE_PROFIT":
                            cell.fill = PatternFill(start_color="D5F4E6", end_color="D5F4E6", fill_type="solid")
                        elif value == "STOP_LOSS":
                            cell.fill = PatternFill(start_color="FADBD8", end_color="FADBD8", fill_type="solid")
                        elif value == "TIME_EXIT":
                            cell.fill = PatternFill(start_color="FCF3CF", end_color="FCF3CF", fill_type="solid")
        
        # Recent Performance Chart Data
        if not trades_df.empty:
            ws['E23'] = "CUMULATIVE P&L PROGRESSION"
            ws['E23'].font = Font(name='Arial', size=16, bold=True, color="2C3E50")
            ws.merge_cells('E23:H23')
            
            # Calculate cumulative P&L
            trades_sorted = trades_df.sort_values('close_timestamp')
            trades_sorted['cumulative_pnl'] = trades_sorted['pnl_usd'].cumsum()
            
            # Create mini table for chart
            chart_data = [["Trade #", "P&L", "Cumulative"]]
            for idx, (_, trade) in enumerate(trades_sorted.tail(10).iterrows()):
                chart_data.append([
                    idx + 1,
                    f"${trade['pnl_usd']:.2f}",
                    f"${trade['cumulative_pnl']:.2f}"
                ])
            
            for i, row_data in enumerate(chart_data):
                for j, value in enumerate(row_data):
                    cell = ws.cell(row=25 + i, column=j + 5, value=value)
                    if i == 0:
                        cell.font = Font(name='Arial', size=11, bold=True, color="FFFFFF")
                        cell.fill = PatternFill(start_color="34495E", end_color="34495E", fill_type="solid")
                    else:
                        cell.font = Font(name='Arial', size=10)
                        if j == 1 and isinstance(value, str) and '$' in value:
                            try:
                                num_value = float(value.replace('$', ''))
                                if num_value > 0:
                                    cell.font = Font(name='Arial', size=10, color="27AE60", bold=True)
                                else:
                                    cell.font = Font(name='Arial', size=10, color="E74C3C", bold=True)
                            except:
                                pass
        
        # Footer
        ws['A38'] = "Generated by Hyperion Trading Systems"
        ws['A38'].font = Font(name='Arial', size=10, italic=True, color="95A5A6")
        ws.merge_cells('A38:H38')
        ws['A38'].alignment = Alignment(horizontal="center")
        
        # Adjust column widths
        ws.column_dimensions['A'].width = 20
        ws.column_dimensions['B'].width = 15
        ws.column_dimensions['C'].width = 15
        ws.column_dimensions['D'].width = 15
        ws.column_dimensions['E'].width = 15
        ws.column_dimensions['F'].width = 15
        ws.column_dimensions['G'].width = 15
        ws.column_dimensions['H'].width = 15
        
        # Add borders to all tables
        self._add_table_borders(ws, 13, 1, 8, 8)  # Performance table
        self._add_table_borders(ws, 25, 1, len(exit_data), 3)  # Exit type table
        if not trades_df.empty:
            self._add_table_borders(ws, 25, 5, len(chart_data), 3)  # Chart data table

    def _create_trade_analysis_sheet(self, ws, trades_df):
        """Create detailed trade analysis sheet"""
        # Title
        ws['A1'] = "DETAILED TRADE ANALYSIS"
        ws['A1'].font = Font(name='Arial', size=18, bold=True, color="2C3E50")
        ws.merge_cells('A1:N1')
        
        # Prepare trade data with all columns
        trade_columns = [
            'Trade #', 'Symbol', 'Direction', 'Entry Time', 'Exit Time',
            'Entry Price', 'Exit Price', 'Quantity', 'P&L ($)', 'P&L (%)',
            'Exit Type', 'Hold Time', 'R:R Achieved', 'Perfect Exit'
        ]
        
        # Write headers
        for col, header in enumerate(trade_columns, 1):
            cell = ws.cell(row=3, column=col, value=header)
            cell.font = Font(name='Arial', size=11, bold=True, color="FFFFFF")
            cell.fill = PatternFill(start_color="2C3E50", end_color="2C3E50", fill_type="solid")
            cell.alignment = Alignment(horizontal="center", vertical="center")
        
        # Write trade data
        trades_sorted = trades_df.sort_values('close_timestamp', ascending=False)
        
        for idx, (_, trade) in enumerate(trades_sorted.iterrows(), 1):
            row = idx + 3
            
            # Trade number
            ws.cell(row=row, column=1, value=idx)
            
            # Symbol
            ws.cell(row=row, column=2, value=trade['symbol'])
            
            # Direction
            dir_cell = ws.cell(row=row, column=3, value=trade['direction'])
            if trade['direction'] == 'LONG':
                dir_cell.fill = PatternFill(start_color="E8F8F5", end_color="E8F8F5", fill_type="solid")
            else:
                dir_cell.fill = PatternFill(start_color="EBF5FB", end_color="EBF5FB", fill_type="solid")
            
            # Times
            ws.cell(row=row, column=4, value=pd.to_datetime(trade['open_timestamp']).tz_localize('UTC').strftime('%m/%d %H:%M UTC'))
            ws.cell(row=row, column=5, value=pd.to_datetime(trade['close_timestamp']).tz_localize('UTC').strftime('%m/%d %H:%M UTC'))
            
            # Prices
            ws.cell(row=row, column=6, value=f"${trade['entry_price']:.4f}")
            ws.cell(row=row, column=7, value=f"${trade['exit_price']:.4f}")
            
            # Quantity
            ws.cell(row=row, column=8, value=f"{trade['quantity']:.4f}")
            
            # P&L USD
            pnl_cell = ws.cell(row=row, column=9, value=trade['pnl_usd'])
            pnl_cell.number_format = '$#,##0.00'
            if trade['pnl_usd'] > 0:
                pnl_cell.font = Font(name='Arial', size=11, bold=True, color="27AE60")
                pnl_cell.fill = PatternFill(start_color="E8F8F5", end_color="E8F8F5", fill_type="solid")
            else:
                pnl_cell.font = Font(name='Arial', size=11, bold=True, color="E74C3C")
                pnl_cell.fill = PatternFill(start_color="FADBD8", end_color="FADBD8", fill_type="solid")
            
            # P&L %
            pct_cell = ws.cell(row=row, column=10, value=f"{trade['pnl_pct']:.2f}%")
            if trade['pnl_pct'] > 0:
                pct_cell.font = Font(color="27AE60", bold=True)
            else:
                pct_cell.font = Font(color="E74C3C", bold=True)
            
            # Exit Type
            exit_cell = ws.cell(row=row, column=11, value=trade['exit_type'])
            exit_colors = {
                'TAKE_PROFIT': PatternFill(start_color="D5F4E6", end_color="D5F4E6", fill_type="solid"),
                'STOP_LOSS': PatternFill(start_color="FADBD8", end_color="FADBD8", fill_type="solid"),
                'TIME_EXIT': PatternFill(start_color="FCF3CF", end_color="FCF3CF", fill_type="solid"),
                'MANUAL': PatternFill(start_color="EBDEF0", end_color="EBDEF0", fill_type="solid")
            }
            if trade['exit_type'] in exit_colors:
                exit_cell.fill = exit_colors[trade['exit_type']]
            
            # Hold time
            ws.cell(row=row, column=12, value=f"{trade['hold_time_bars']:.1f} bars")
            
            # R:R Achieved
            rr_cell = ws.cell(row=row, column=13, value=f"{trade['risk_reward_achieved']:.2f}")
            if trade['risk_reward_achieved'] > 1:
                rr_cell.font = Font(color="27AE60", bold=True)
            
            # Perfect Exit
            perfect_cell = ws.cell(row=row, column=14, value=trade['perfect_exit'])
            if trade['perfect_exit'] == 'YES':
                perfect_cell.fill = PatternFill(start_color="D5F4E6", end_color="D5F4E6", fill_type="solid")
                perfect_cell.font = Font(bold=True, color="27AE60")
        
        # Auto-fit columns
        for column in ws.columns:
            max_length = 0
            column_letter = get_column_letter(column[0].column)
            for cell in column:
                try:
                    if len(str(cell.value)) > max_length:
                        max_length = len(str(cell.value))
                except:
                    pass
            adjusted_width = min(max_length + 2, 30)
            ws.column_dimensions[column_letter].width = adjusted_width
        
        # Add filters
        ws.auto_filter.ref = f"A3:N{len(trades_sorted) + 3}"
        
        # Freeze top rows
        ws.freeze_panes = 'A4'

    def _create_performance_metrics_sheet(self, ws, trades_df, metrics):
        """Create performance metrics sheet with charts"""
        # Title
        ws['A1'] = "PERFORMANCE METRICS & ANALYSIS"
        ws['A1'].font = Font(name='Arial', size=18, bold=True, color="2C3E50")
        ws.merge_cells('A1:H1')
        
        # Key Performance Indicators
        ws['A3'] = "KEY PERFORMANCE INDICATORS"
        ws['A3'].font = Font(name='Arial', size=14, bold=True, color="34495E")
        ws.merge_cells('A3:D3')
        
        # KPI Grid
        kpi_data = [
            ["Total Return", f"${metrics['total_pnl']:.2f}", "Sharpe Ratio", f"{metrics['sharpe_ratio']:.2f}"],
            ["Win Rate", f"{metrics['win_rate']:.1f}%", "Profit Factor", f"{metrics['profit_factor']:.2f}"],
            ["Max Drawdown", f"${metrics['max_drawdown']:.2f}", "Recovery Factor", f"{metrics['recovery_factor']:.2f}"],
            ["Avg Win/Loss Ratio", f"{abs(metrics['avg_win']/metrics['avg_loss']) if metrics['avg_loss'] != 0 else 0:.2f}", "Perfect Exit Rate", f"{metrics['perfect_exit_rate']:.1f}%"]
        ]
        
        start_row = 5
        for i, row_data in enumerate(kpi_data):
            for j, value in enumerate(row_data):
                cell = ws.cell(row=start_row + i, column=j + 1, value=value)
                
                if j % 2 == 0:  # Labels
                    cell.font = Font(name='Arial', size=11, bold=True)
                    cell.fill = PatternFill(start_color="ECF0F1", end_color="ECF0F1", fill_type="solid")
                else:  # Values
                    cell.font = Font(name='Arial', size=12, bold=True)
                    cell.alignment = Alignment(horizontal="center")
                    
                    # Color code values
                    if isinstance(value, str):
                        if '$' in value and '-' in value:
                            cell.font = Font(name='Arial', size=12, bold=True, color="E74C3C")
                        elif any(good in value for good in ['%', '.']):
                            try:
                                num_val = float(value.replace('%', '').replace('$', ''))
                                if 'Rate' in str(ws.cell(row=start_row + i, column=j).value):
                                    if num_val >= 50:
                                        cell.font = Font(name='Arial', size=12, bold=True, color="27AE60")
                                elif 'Factor' in str(ws.cell(row=start_row + i, column=j).value):
                                    if num_val >= 1.5:
                                        cell.font = Font(name='Arial', size=12, bold=True, color="27AE60")
                            except:
                                pass
        
        # Time-based Performance Analysis
        if not trades_df.empty:
            ws['A11'] = "PERFORMANCE BY TIME PERIOD"
            ws['A11'].font = Font(name='Arial', size=14, bold=True, color="34495E")
            ws.merge_cells('A11:H11')
            
            # Daily performance
            trades_df['date'] = pd.to_datetime(trades_df['close_timestamp']).dt.date
            daily_perf = trades_df.groupby('date').agg({
                'pnl_usd': ['sum', 'count'],
                'pnl_pct': 'mean'
            }).round(2)
            
            # Write daily performance table
            daily_headers = ['Date', 'Trades', 'P&L ($)', 'Avg P&L (%)', 'Cumulative']
            for col, header in enumerate(daily_headers, 1):
                cell = ws.cell(row=13, column=col, value=header)
                cell.font = Font(name='Arial', size=11, bold=True, color="FFFFFF")
                cell.fill = PatternFill(start_color="34495E", end_color="34495E", fill_type="solid")
            
            cumulative = 0
            for idx, (date, data) in enumerate(daily_perf.iterrows()):
                row = 14 + idx
                ws.cell(row=row, column=1, value=date.strftime('%Y-%m-%d'))
                ws.cell(row=row, column=2, value=int(data[('pnl_usd', 'count')]))
                
                daily_pnl = data[('pnl_usd', 'sum')]
                pnl_cell = ws.cell(row=row, column=3, value=daily_pnl)
                pnl_cell.number_format = '$#,##0.00'
                if daily_pnl > 0:
                    pnl_cell.font = Font(color="27AE60", bold=True)
                else:
                    pnl_cell.font = Font(color="E74C3C", bold=True)
                
                ws.cell(row=row, column=4, value=f"{data[('pnl_pct', 'mean')]:.2f}%")
                
                cumulative += daily_pnl
                cum_cell = ws.cell(row=row, column=5, value=cumulative)
                cum_cell.number_format = '$#,##0.00'
                if cumulative > 0:
                    cum_cell.font = Font(color="27AE60", bold=True)
                else:
                    cum_cell.font = Font(color="E74C3C", bold=True)
        
        # Session Performance
        ws['F3'] = "PERFORMANCE BY SESSION"
        ws['F3'].font = Font(name='Arial', size=14, bold=True, color="34495E")
        ws.merge_cells('F3:H3')
        
        if not trades_df.empty:
            session_perf = trades_df.groupby('session').agg({
                'pnl_usd': ['sum', 'count', 'mean'],
                'pnl_pct': 'mean'
            }).round(2)
            
            session_headers = ['Session', 'Trades', 'Total P&L']
            for col, header in enumerate(session_headers, 6):
                cell = ws.cell(row=5, column=col, value=header)
                cell.font = Font(name='Arial', size=11, bold=True, color="FFFFFF")
                cell.fill = PatternFill(start_color="34495E", end_color="34495E", fill_type="solid")
            
            for idx, (session, data) in enumerate(session_perf.iterrows()):
                row = 6 + idx
                ws.cell(row=row, column=6, value=session)
                ws.cell(row=row, column=7, value=int(data[('pnl_usd', 'count')]))
                
                session_pnl = data[('pnl_usd', 'sum')]
                pnl_cell = ws.cell(row=row, column=8, value=session_pnl)
                pnl_cell.number_format = '$#,##0.00'
                if session_pnl > 0:
                    pnl_cell.font = Font(color="27AE60", bold=True)
                else:
                    pnl_cell.font = Font(color="E74C3C", bold=True)
        
        # Auto-fit columns
        for column in ws.columns:
            max_length = 0
            column_letter = get_column_letter(column[0].column)
            for cell in column:
                try:
                    if len(str(cell.value)) > max_length:
                        max_length = len(str(cell.value))
                except:
                    pass
            adjusted_width = min(max_length + 2, 30)
            ws.column_dimensions[column_letter].width = adjusted_width

    def _create_risk_analysis_sheet(self, ws, trades_df, metrics):
        """Create risk analysis sheet"""
        # Title
        ws['A1'] = "RISK ANALYSIS & STATISTICS"
        ws['A1'].font = Font(name='Arial', size=18, bold=True, color="2C3E50")
        ws.merge_cells('A1:F1')
        
        # Risk Metrics Summary
        ws['A3'] = "RISK METRICS SUMMARY"
        ws['A3'].font = Font(name='Arial', size=14, bold=True, color="34495E")
        ws.merge_cells('A3:C3')
        
        risk_data = [
            ["Metric", "Value", "Status"],
            ["Maximum Drawdown", f"${metrics['max_drawdown']:.2f}", self._get_risk_status(metrics['max_drawdown'], -50, -100)],
            ["Sharpe Ratio", f"{metrics['sharpe_ratio']:.2f}", self._get_risk_status(metrics['sharpe_ratio'], 1.0, 0.5, higher_better=True)],
            ["Recovery Factor", f"{metrics['recovery_factor']:.2f}", self._get_risk_status(metrics['recovery_factor'], 2.0, 1.0, higher_better=True)],
            ["Largest Loss", f"${metrics['worst_trade']:.2f}", self._get_risk_status(metrics['worst_trade'], -20, -50)],
            ["Consecutive Losses", "N/A", "Monitor"],
            ["Risk per Trade", f"{0.7:.1f}%", "Fixed"]
        ]
        
        for i, row_data in enumerate(risk_data):
            for j, value in enumerate(row_data):
                cell = ws.cell(row=5 + i, column=j + 1, value=value)
                
                if i == 0:  # Header
                    cell.font = Font(name='Arial', size=11, bold=True, color="FFFFFF")
                    cell.fill = PatternFill(start_color="34495E", end_color="34495E", fill_type="solid")
                else:
                    if j == 0:  # Metric name
                        cell.font = Font(name='Arial', size=10, bold=True)
                        cell.fill = PatternFill(start_color="ECF0F1", end_color="ECF0F1", fill_type="solid")
                    elif j == 2:  # Status
                        if value == "Good":
                            cell.fill = PatternFill(start_color="D5F4E6", end_color="D5F4E6", fill_type="solid")
                            cell.font = Font(color="27AE60", bold=True)
                        elif value == "Warning":
                            cell.fill = PatternFill(start_color="FCF3CF", end_color="FCF3CF", fill_type="solid")
                            cell.font = Font(color="F39C12", bold=True)
                        elif value == "Critical":
                            cell.fill = PatternFill(start_color="FADBD8", end_color="FADBD8", fill_type="solid")
                            cell.font = Font(color="E74C3C", bold=True)
        
        # Distribution Analysis
        if not trades_df.empty:
            ws['E3'] = "P&L DISTRIBUTION"
            ws['E3'].font = Font(name='Arial', size=14, bold=True, color="34495E")
            ws.merge_cells('E3:F3')
            
            # Calculate P&L distribution
            pnl_ranges = [
                ('< -$50', len(trades_df[trades_df['pnl_usd'] < -50])),
                ('-$50 to -$20', len(trades_df[(trades_df['pnl_usd'] >= -50) & (trades_df['pnl_usd'] < -20)])),
                ('-$20 to $0', len(trades_df[(trades_df['pnl_usd'] >= -20) & (trades_df['pnl_usd'] < 0)])),
                ('$0 to $20', len(trades_df[(trades_df['pnl_usd'] >= 0) & (trades_df['pnl_usd'] < 20)])),
                ('$20 to $50', len(trades_df[(trades_df['pnl_usd'] >= 20) & (trades_df['pnl_usd'] < 50)])),
                ('> $50', len(trades_df[trades_df['pnl_usd'] >= 50]))
            ]
            
            dist_headers = ['Range', 'Count']
            for col, header in enumerate(dist_headers):
                cell = ws.cell(row=5, column=col + 5, value=header)
                cell.font = Font(name='Arial', size=11, bold=True, color="FFFFFF")
                cell.fill = PatternFill(start_color="34495E", end_color="34495E", fill_type="solid")
            
            for i, (range_name, count) in enumerate(pnl_ranges):
                ws.cell(row=6 + i, column=5, value=range_name)
                ws.cell(row=6 + i, column=6, value=count)
        
        # Risk Assessment
        ws['A13'] = "RISK ASSESSMENT"
        ws['A13'].font = Font(name='Arial', size=14, bold=True, color="34495E")
        ws.merge_cells('A13:F13')
        
        # Calculate risk score
        risk_score = self._calculate_risk_score(metrics)
        
        ws['A15'] = "Overall Risk Score"
        ws['A15'].font = Font(name='Arial', size=12, bold=True)
        
        ws['B15'] = f"{risk_score}/100"
        ws['B15'].font = Font(name='Arial', size=16, bold=True)
        if risk_score >= 80:
            ws['B15'].font = Font(name='Arial', size=16, bold=True, color="27AE60")
            ws['C15'] = "Low Risk"
            ws['C15'].fill = PatternFill(start_color="D5F4E6", end_color="D5F4E6", fill_type="solid")
        elif risk_score >= 60:
            ws['C15'] = "Moderate Risk"
            ws['C15'].fill = PatternFill(start_color="FCF3CF", end_color="FCF3CF", fill_type="solid")
        else:
            ws['B15'].font = Font(name='Arial', size=16, bold=True, color="E74C3C")
            ws['C15'] = "High Risk"
            ws['C15'].fill = PatternFill(start_color="FADBD8", end_color="FADBD8", fill_type="solid")
        
        # Recommendations
        ws['A17'] = "RISK MANAGEMENT RECOMMENDATIONS"
        ws['A17'].font = Font(name='Arial', size=12, bold=True)
        ws.merge_cells('A17:F17')
        
        recommendations = self._get_risk_recommendations(metrics, trades_df)
        for i, rec in enumerate(recommendations):
            ws.cell(row=19 + i, column=1, value=f"• {rec}")
            ws.cell(row=19 + i, column=1).font = Font(name='Arial', size=10)
        
        # Auto-fit columns
        for column in ws.columns:
            max_length = 0
            column_letter = get_column_letter(column[0].column)
            for cell in column:
                try:
                    if len(str(cell.value)) > max_length:
                        max_length = len(str(cell.value))
                except:
                    pass
            adjusted_width = min(max_length + 2, 40)
            ws.column_dimensions[column_letter].width = adjusted_width

    def _create_enhanced_symbol_sheet(self, ws, trades_df):
        """Create enhanced symbol performance analysis"""
        # Title
        ws['A1'] = "SYMBOL PERFORMANCE ANALYSIS"
        ws['A1'].font = Font(name='Arial', size=18, bold=True, color="2C3E50")
        ws.merge_cells('A1:J1')
        
        # Calculate symbol statistics
        symbol_stats = trades_df.groupby('symbol').agg({
            'pnl_usd': ['count', 'sum', 'mean', 'std'],
            'pnl_pct': 'mean',
            'hold_time_bars': 'mean'
        }).round(2)
        
        # Calculate additional metrics per symbol
        symbol_metrics = []
        
        for symbol in symbol_stats.index:
            symbol_trades = trades_df[trades_df['symbol'] == symbol]
            wins = symbol_trades[symbol_trades['pnl_usd'] > 0]
            losses = symbol_trades[symbol_trades['pnl_usd'] < 0]
            
            # Calculate profit factor
            gross_profit = wins['pnl_usd'].sum() if len(wins) > 0 else 0
            gross_loss = abs(losses['pnl_usd'].sum()) if len(losses) > 0 else 0
            profit_factor = gross_profit / gross_loss if gross_loss > 0 else gross_profit
            
            # Calculate Sharpe ratio for symbol
            returns = symbol_trades['pnl_pct'].values
            sharpe = (returns.mean() / returns.std() * np.sqrt(252)) if returns.std() > 0 else 0
            
            symbol_metrics.append({
                'symbol': symbol,
                'trades': int(symbol_stats.loc[symbol, ('pnl_usd', 'count')]),
                'wins': len(wins),
                'losses': len(losses),
                'win_rate': (len(wins) / len(symbol_trades) * 100),
                'total_pnl': symbol_stats.loc[symbol, ('pnl_usd', 'sum')],
                'avg_pnl': symbol_stats.loc[symbol, ('pnl_usd', 'mean')],
                'profit_factor': profit_factor,
                'sharpe': sharpe,
                'avg_hold': symbol_stats.loc[symbol, ('hold_time_bars', 'mean')],
                'best_trade': symbol_trades['pnl_usd'].max(),
                'worst_trade': symbol_trades['pnl_usd'].min()
            })
        
        # Sort by total P&L
        symbol_metrics = sorted(symbol_metrics, key=lambda x: x['total_pnl'], reverse=True)
        
        # Write headers
        headers = [
            'Symbol', 'Trades', 'Wins', 'Losses', 'Win Rate', 
            'Total P&L', 'Avg P&L', 'Profit Factor', 'Sharpe', 
            'Avg Hold', 'Best Trade', 'Worst Trade'
        ]
        
        for col, header in enumerate(headers, 1):
            cell = ws.cell(row=3, column=col, value=header)
            cell.font = Font(name='Arial', size=11, bold=True, color="FFFFFF")
            cell.fill = PatternFill(start_color="2C3E50", end_color="2C3E50", fill_type="solid")
            cell.alignment = Alignment(horizontal="center")
        
        # Write data
        for row_idx, symbol_data in enumerate(symbol_metrics, 4):
            # Symbol
            ws.cell(row=row_idx, column=1, value=symbol_data['symbol'])
            ws.cell(row=row_idx, column=1).font = Font(bold=True)
            
            # Trade counts
            ws.cell(row=row_idx, column=2, value=symbol_data['trades'])
            ws.cell(row=row_idx, column=3, value=symbol_data['wins'])
            ws.cell(row=row_idx, column=4, value=symbol_data['losses'])
            
            # Win rate
            wr_cell = ws.cell(row=row_idx, column=5, value=f"{symbol_data['win_rate']:.1f}%")
            if symbol_data['win_rate'] >= 60:
                wr_cell.font = Font(color="27AE60", bold=True)
            elif symbol_data['win_rate'] < 40:
                wr_cell.font = Font(color="E74C3C", bold=True)
            
            # Total P&L
            total_pnl_cell = ws.cell(row=row_idx, column=6, value=symbol_data['total_pnl'])
            total_pnl_cell.number_format = '$#,##0.00'
            if symbol_data['total_pnl'] > 0:
                total_pnl_cell.font = Font(color="27AE60", bold=True, size=12)
                total_pnl_cell.fill = PatternFill(start_color="E8F8F5", end_color="E8F8F5", fill_type="solid")
            else:
                total_pnl_cell.font = Font(color="E74C3C", bold=True, size=12)
                total_pnl_cell.fill = PatternFill(start_color="FADBD8", end_color="FADBD8", fill_type="solid")
            
            # Avg P&L
            avg_pnl_cell = ws.cell(row=row_idx, column=7, value=symbol_data['avg_pnl'])
            avg_pnl_cell.number_format = '$#,##0.00'
            
            # Profit Factor
            pf_cell = ws.cell(row=row_idx, column=8, value=f"{symbol_data['profit_factor']:.2f}")
            if symbol_data['profit_factor'] >= 1.5:
                pf_cell.font = Font(color="27AE60", bold=True)
                pf_cell.fill = PatternFill(start_color="E8F8F5", end_color="E8F8F5", fill_type="solid")
            elif symbol_data['profit_factor'] < 1:
                pf_cell.font = Font(color="E74C3C", bold=True)
                pf_cell.fill = PatternFill(start_color="FADBD8", end_color="FADBD8", fill_type="solid")
            
            # Sharpe
            ws.cell(row=row_idx, column=9, value=f"{symbol_data['sharpe']:.2f}")
            
            # Avg Hold
            ws.cell(row=row_idx, column=10, value=f"{symbol_data['avg_hold']:.1f}")
            
            # Best/Worst trades
            best_cell = ws.cell(row=row_idx, column=11, value=symbol_data['best_trade'])
            best_cell.number_format = '$#,##0.00'
            best_cell.font = Font(color="27AE60")
            
            worst_cell = ws.cell(row=row_idx, column=12, value=symbol_data['worst_trade'])
            worst_cell.number_format = '$#,##0.00'
            worst_cell.font = Font(color="E74C3C")
        
        # Add summary statistics
        ws['A' + str(len(symbol_metrics) + 6)] = "SYMBOL PERFORMANCE SUMMARY"
        ws['A' + str(len(symbol_metrics) + 6)].font = Font(name='Arial', size=14, bold=True, color="34495E")
        
        # Best and worst performers
        if symbol_metrics:
            best_symbol = max(symbol_metrics, key=lambda x: x['total_pnl'])
            worst_symbol = min(symbol_metrics, key=lambda x: x['total_pnl'])
            
            summary_row = len(symbol_metrics) + 8
            ws[f'A{summary_row}'] = "Best Performer:"
            ws[f'B{summary_row}'] = f"{best_symbol['symbol']} (${best_symbol['total_pnl']:.2f})"
            ws[f'B{summary_row}'].font = Font(color="27AE60", bold=True)
            
            ws[f'A{summary_row + 1}'] = "Worst Performer:"
            ws[f'B{summary_row + 1}'] = f"{worst_symbol['symbol']} (${worst_symbol['total_pnl']:.2f})"
            ws[f'B{summary_row + 1}'].font = Font(color="E74C3C", bold=True)
            
            # Most consistent
            most_consistent = max(symbol_metrics, key=lambda x: x['win_rate'])
            ws[f'A{summary_row + 2}'] = "Most Consistent:"
            ws[f'B{summary_row + 2}'] = f"{most_consistent['symbol']} ({most_consistent['win_rate']:.1f}% win rate)"
            
            # Highest profit factor
            highest_pf = max(symbol_metrics, key=lambda x: x['profit_factor'])
            ws[f'A{summary_row + 3}'] = "Highest Profit Factor:"
            ws[f'B{summary_row + 3}'] = f"{highest_pf['symbol']} ({highest_pf['profit_factor']:.2f})"
        
        # Auto-fit columns
        for column in ws.columns:
            max_length = 0
            column_letter = get_column_letter(column[0].column)
            for cell in column:
                try:
                    if len(str(cell.value)) > max_length:
                        max_length = len(str(cell.value))
                except:
                    pass
            adjusted_width = min(max_length + 2, 25)
            ws.column_dimensions[column_letter].width = adjusted_width
        
        # Add conditional formatting for the data rows
        data_range = f"A4:L{len(symbol_metrics) + 3}"
        
        # Add borders
        self._add_table_borders(ws, 3, 1, len(symbol_metrics) + 1, 12)

    def _create_time_analysis_sheet(self, ws, trades_df):
        """Create time-based analysis sheet"""
        # Title
        ws['A1'] = "TIME-BASED ANALYSIS"
        ws['A1'].font = Font(name='Arial', size=18, bold=True, color="2C3E50")
        ws.merge_cells('A1:H1')
        
        # Performance by Day of Week
        ws['A3'] = "PERFORMANCE BY DAY OF WEEK"
        ws['A3'].font = Font(name='Arial', size=14, bold=True, color="34495E")
        ws.merge_cells('A3:D3')
        
        # Day of week analysis
        trades_df['day_name'] = pd.to_datetime(trades_df['close_timestamp']).dt.day_name()
        day_order = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
        
        day_stats = []
        for day in day_order:
            day_trades = trades_df[trades_df['day_name'] == day]
            if len(day_trades) > 0:
                wins = len(day_trades[day_trades['pnl_usd'] > 0])
                total = len(day_trades)
                day_stats.append({
                    'day': day,
                    'trades': total,
                    'wins': wins,
                    'win_rate': (wins / total * 100),
                    'total_pnl': day_trades['pnl_usd'].sum(),
                    'avg_pnl': day_trades['pnl_usd'].mean()
                })
        
        # Write day of week table
        day_headers = ['Day', 'Trades', 'Win Rate', 'Total P&L', 'Avg P&L']
        for col, header in enumerate(day_headers, 1):
            cell = ws.cell(row=5, column=col, value=header)
            cell.font = Font(name='Arial', size=11, bold=True, color="FFFFFF")
            cell.fill = PatternFill(start_color="34495E", end_color="34495E", fill_type="solid")
        
        for idx, day_data in enumerate(day_stats):
            row = 6 + idx
            ws.cell(row=row, column=1, value=day_data['day'])
            ws.cell(row=row, column=2, value=day_data['trades'])
            
            wr_cell = ws.cell(row=row, column=3, value=f"{day_data['win_rate']:.1f}%")
            if day_data['win_rate'] >= 60:
                wr_cell.font = Font(color="27AE60", bold=True)
            
            total_pnl_cell = ws.cell(row=row, column=4, value=day_data['total_pnl'])
            total_pnl_cell.number_format = '$#,##0.00'
            if day_data['total_pnl'] > 0:
                total_pnl_cell.font = Font(color="27AE60", bold=True)
            else:
                total_pnl_cell.font = Font(color="E74C3C", bold=True)
            
            avg_pnl_cell = ws.cell(row=row, column=5, value=day_data['avg_pnl'])
            avg_pnl_cell.number_format = '$#,##0.00'
        
        # Performance by Hour
        ws['F3'] = "PERFORMANCE BY HOUR"
        ws['F3'].font = Font(name='Arial', size=14, bold=True, color="34495E")
        ws.merge_cells('F3:H3')
        
        # Hour analysis
        trades_df['hour'] = pd.to_datetime(trades_df['close_timestamp']).dt.hour
        hour_stats = trades_df.groupby('hour').agg({
            'pnl_usd': ['count', 'sum', 'mean'],
            'pnl_pct': 'mean'
        }).round(2)
        
        # Write hour headers
        hour_headers = ['Hour', 'Trades', 'Total P&L']
        for col, header in enumerate(hour_headers, 6):
            cell = ws.cell(row=5, column=col, value=header)
            cell.font = Font(name='Arial', size=11, bold=True, color="FFFFFF")
            cell.fill = PatternFill(start_color="34495E", end_color="34495E", fill_type="solid")
        
        # Write top performing hours
        hour_perf = []
        for hour, data in hour_stats.iterrows():
            hour_perf.append({
                'hour': f"{hour:02d}:00",
                'trades': int(data[('pnl_usd', 'count')]),
                'total_pnl': data[('pnl_usd', 'sum')]
            })
        
        # Sort by total P&L
        hour_perf = sorted(hour_perf, key=lambda x: x['total_pnl'], reverse=True)[:10]
        
        for idx, hour_data in enumerate(hour_perf):
            row = 6 + idx
            ws.cell(row=row, column=6, value=hour_data['hour'])
            ws.cell(row=row, column=7, value=hour_data['trades'])
            
            pnl_cell = ws.cell(row=row, column=8, value=hour_data['total_pnl'])
            pnl_cell.number_format = '$#,##0.00'
            if hour_data['total_pnl'] > 0:
                pnl_cell.font = Font(color="27AE60", bold=True)
            else:
                pnl_cell.font = Font(color="E74C3C", bold=True)
        
        # Hold Time Analysis
        ws['A15'] = "HOLD TIME ANALYSIS"
        ws['A15'].font = Font(name='Arial', size=14, bold=True, color="34495E")
        ws.merge_cells('A15:H15')
        
        # Hold time buckets
        trades_df['hold_bucket'] = pd.cut(trades_df['hold_time_bars'], 
                                            bins=[0, 2, 4, 8, 16, 100], 
                                            labels=['0-2 bars', '2-4 bars', '4-8 bars', '8-16 bars', '16+ bars'])
        
        hold_stats = trades_df.groupby('hold_bucket').agg({
            'pnl_usd': ['count', 'sum', 'mean'],
            'pnl_pct': 'mean'
        }).round(2)
        
        # Write hold time table
        hold_headers = ['Hold Time', 'Trades', 'Win Rate', 'Total P&L', 'Avg P&L']
        for col, header in enumerate(hold_headers, 1):
            cell = ws.cell(row=17, column=col, value=header)
            cell.font = Font(name='Arial', size=11, bold=True, color="FFFFFF")
            cell.fill = PatternFill(start_color="34495E", end_color="34495E", fill_type="solid")
        
        for idx, (bucket, data) in enumerate(hold_stats.iterrows()):
            row = 18 + idx
            bucket_trades = trades_df[trades_df['hold_bucket'] == bucket]
            wins = len(bucket_trades[bucket_trades['pnl_usd'] > 0])
            total = len(bucket_trades)
            
            ws.cell(row=row, column=1, value=str(bucket))
            ws.cell(row=row, column=2, value=int(data[('pnl_usd', 'count')]))
            
            if total > 0:
                wr_cell = ws.cell(row=row, column=3, value=f"{(wins/total*100):.1f}%")
                if (wins/total*100) >= 60:
                    wr_cell.font = Font(color="27AE60", bold=True)
            
            total_pnl_cell = ws.cell(row=row, column=4, value=data[('pnl_usd', 'sum')])
            total_pnl_cell.number_format = '$#,##0.00'
            if data[('pnl_usd', 'sum')] > 0:
                total_pnl_cell.font = Font(color="27AE60", bold=True)
            else:
                total_pnl_cell.font = Font(color="E74C3C", bold=True)
            
            avg_pnl_cell = ws.cell(row=row, column=5, value=data[('pnl_usd', 'mean')])
            avg_pnl_cell.number_format = '$#,##0.00'
        
        # Auto-fit columns
        for column in ws.columns:
            max_length = 0
            column_letter = get_column_letter(column[0].column)
            for cell in column:
                try:
                    if len(str(cell.value)) > max_length:
                        max_length = len(str(cell.value))
                except:
                    pass
            adjusted_width = min(max_length + 2, 30)
            ws.column_dimensions[column_letter].width = adjusted_width

    def _create_signal_analysis_sheet(self, ws, signals_df):
        """Create signal analysis sheet"""
        # Title
        ws['A1'] = "SIGNAL ANALYSIS"
        ws['A1'].font = Font(name='Arial', size=18, bold=True, color="2C3E50")
        ws.merge_cells('A1:F1')
        
        # Extract signal data
        signals_data = pd.json_normalize(signals_df['data'].tolist())
        signals_data['timestamp'] = signals_df['timestamp'].values
        
        # Signal Quality Distribution
        ws['A3'] = "SIGNAL QUALITY DISTRIBUTION"
        ws['A3'].font = Font(name='Arial', size=14, bold=True, color="34495E")
        ws.merge_cells('A3:C3')
        
        if 'quality_score' in signals_data.columns:
            quality_bins = [0, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0]
            quality_labels = ['0.0-0.5', '0.5-0.6', '0.6-0.7', '0.7-0.8', '0.8-0.9', '0.9-1.0']
            signals_data['quality_bucket'] = pd.cut(signals_data['quality_score'], 
                                                    bins=quality_bins, 
                                                    labels=quality_labels)
            
            quality_dist = signals_data['quality_bucket'].value_counts().sort_index()
            
            # Write quality distribution
            quality_headers = ['Quality Range', 'Count', 'Percentage']
            for col, header in enumerate(quality_headers, 1):
                cell = ws.cell(row=5, column=col, value=header)
                cell.font = Font(name='Arial', size=11, bold=True, color="FFFFFF")
                cell.fill = PatternFill(start_color="34495E", end_color="34495E", fill_type="solid")
            
            total_signals = len(signals_data)
            for idx, (bucket, count) in enumerate(quality_dist.items()):
                row = 6 + idx
                ws.cell(row=row, column=1, value=str(bucket))
                ws.cell(row=row, column=2, value=int(count))
                
                pct_cell = ws.cell(row=row, column=3, value=f"{(count/total_signals*100):.1f}%")
                
                # Color code based on quality
                if '0.8' in str(bucket) or '0.9' in str(bucket):
                    pct_cell.font = Font(color="27AE60", bold=True)
                elif '0.0' in str(bucket) or '0.5' in str(bucket):
                    pct_cell.font = Font(color="E74C3C", bold=True)
        
        # Signal by Symbol
        ws['E3'] = "SIGNALS BY SYMBOL"
        ws['E3'].font = Font(name='Arial', size=14, bold=True, color="34495E")
        ws.merge_cells('E3:F3')
        
        if 'symbol' in signals_data.columns:
            symbol_signals = signals_data['symbol'].value_counts().head(10)
            
            symbol_headers = ['Symbol', 'Signals']
            for col, header in enumerate(symbol_headers, 5):
                cell = ws.cell(row=5, column=col, value=header)
                cell.font = Font(name='Arial', size=11, bold=True, color="FFFFFF")
                cell.fill = PatternFill(start_color="34495E", end_color="34495E", fill_type="solid")
            
            for idx, (symbol, count) in enumerate(symbol_signals.items()):
                row = 6 + idx
                ws.cell(row=row, column=5, value=symbol)
                ws.cell(row=row, column=6, value=int(count))
        
        # Signal Execution Analysis
        ws['A14'] = "SIGNAL EXECUTION ANALYSIS"
        ws['A14'].font = Font(name='Arial', size=14, bold=True, color="34495E")
        ws.merge_cells('A14:F14')
        
        exec_data = [
            ["Metric", "Value"],
            ["Total Signals Generated", len(signals_data)],
            ["Average Signal Quality", f"{signals_data['quality_score'].mean():.3f}" if 'quality_score' in signals_data else "N/A"],
            ["Signals Above Threshold (0.6)", len(signals_data[signals_data['quality_score'] >= 0.6]) if 'quality_score' in signals_data else "N/A"],
            ["Signal Execution Rate", f"{(len(signals_data) / len(signals_data) * 100):.1f}%" if len(signals_data) > 0 else "0%"]
        ]
        
        for i, row_data in enumerate(exec_data):
            for j, value in enumerate(row_data):
                cell = ws.cell(row=16 + i, column=j + 1, value=value)
                
                if i == 0:  # Header
                    cell.font = Font(name='Arial', size=11, bold=True, color="FFFFFF")
                    cell.fill = PatternFill(start_color="34495E", end_color="34495E", fill_type="solid")
                else:
                    if j == 0:  # Metric name
                        cell.font = Font(name='Arial', size=10, bold=True)
                        cell.fill = PatternFill(start_color="ECF0F1", end_color="ECF0F1", fill_type="solid")
        
        # Auto-fit columns
        for column in ws.columns:
            max_length = 0
            column_letter = get_column_letter(column[0].column)
            for cell in column:
                try:
                    if len(str(cell.value)) > max_length:
                        max_length = len(str(cell.value))
                except:
                    pass
            adjusted_width = min(max_length + 2, 30)
            ws.column_dimensions[column_letter].width = adjusted_width

    def _create_error_sheet(self, ws, errors_df):
        """Create error analysis sheet"""
        # Title
        ws['A1'] = "SYSTEM ERROR LOG"
        ws['A1'].font = Font(name='Arial', size=18, bold=True, color="C0392B")
        ws.merge_cells('A1:F1')
        
        # Extract error data
        errors_data = pd.json_normalize(errors_df['data'].tolist())
        errors_data['timestamp'] = errors_df['timestamp'].values
        
        # Error Summary
        ws['A3'] = "ERROR SUMMARY"
        ws['A3'].font = Font(name='Arial', size=14, bold=True, color="34495E")
        ws.merge_cells('A3:C3')
        
        # Count by severity
        severity_counts = errors_data['severity'].value_counts() if 'severity' in errors_data else pd.Series()
        
        summary_data = [
            ["Severity", "Count", "Action Required"],
            ["CRITICAL", severity_counts.get('CRITICAL', 0), "Immediate"],
            ["HIGH", severity_counts.get('HIGH', 0), "Within 24h"],
            ["MEDIUM", severity_counts.get('MEDIUM', 0), "Monitor"],
            ["LOW", severity_counts.get('LOW', 0), "Log Only"]
        ]
        
        for i, row_data in enumerate(summary_data):
            for j, value in enumerate(row_data):
                cell = ws.cell(row=5 + i, column=j + 1, value=value)
                
                if i == 0:  # Header
                    cell.font = Font(name='Arial', size=11, bold=True, color="FFFFFF")
                    cell.fill = PatternFill(start_color="34495E", end_color="34495E", fill_type="solid")
                else:
                    if j == 0:  # Severity
                        if value == "CRITICAL":
                            cell.font = Font(color="E74C3C", bold=True)
                            cell.fill = PatternFill(start_color="FADBD8", end_color="FADBD8", fill_type="solid")
                        elif value == "HIGH":
                            cell.font = Font(color="E67E22", bold=True)
                            cell.fill = PatternFill(start_color="FCE4D4", end_color="FCE4D4", fill_type="solid")
        
        # Recent Errors
        ws['A12'] = "RECENT ERRORS (Last 20)"
        ws['A12'].font = Font(name='Arial', size=14, bold=True, color="34495E")
        ws.merge_cells('A12:F12')
        
        # Error details
        error_headers = ['Time', 'Component', 'Severity', 'Message']
        for col, header in enumerate(error_headers, 1):
            cell = ws.cell(row=14, column=col, value=header)
            cell.font = Font(name='Arial', size=11, bold=True, color="FFFFFF")
            cell.fill = PatternFill(start_color="34495E", end_color="34495E", fill_type="solid")
        
        # Write recent errors
        recent_errors = errors_data.tail(20).sort_values('timestamp', ascending=False)
        
        for idx, (_, error) in enumerate(recent_errors.iterrows()):
            row = 15 + idx
            
            # Time
            ws.cell(row=row, column=1, value=pd.to_datetime(error['timestamp']).strftime('%m/%d %H:%M'))
            
            # Component
            ws.cell(row=row, column=2, value=error.get('component', 'Unknown'))
            
            # Severity
            sev_cell = ws.cell(row=row, column=3, value=error.get('severity', 'UNKNOWN'))
            if error.get('severity') == 'CRITICAL':
                sev_cell.font = Font(color="E74C3C", bold=True)
                sev_cell.fill = PatternFill(start_color="FADBD8", end_color="FADBD8", fill_type="solid")
            elif error.get('severity') == 'HIGH':
                sev_cell.font = Font(color="E67E22", bold=True)
            
            # Message (truncated)
            message = str(error.get('message', ''))[:100]
            ws.cell(row=row, column=4, value=message)
        
        # Auto-fit columns
        for column in ws.columns:
            max_length = 0
            column_letter = get_column_letter(column[0].column)
            for cell in column:
                try:
                    if len(str(cell.value)) > max_length:
                        max_length = len(str(cell.value))
                except:
                    pass
            adjusted_width = min(max_length + 2, 50)
            ws.column_dimensions[column_letter].width = adjusted_width

    def _add_table_borders(self, ws, start_row, start_col, num_rows, num_cols):
        """Add professional borders to a table"""
        thin_border = Border(
            left=Side(style='thin', color='D3D3D3'),
            right=Side(style='thin', color='D3D3D3'),
            top=Side(style='thin', color='D3D3D3'),
            bottom=Side(style='thin', color='D3D3D3')
        )
        
        for row in range(start_row, start_row + num_rows):
            for col in range(start_col, start_col + num_cols):
                ws.cell(row=row, column=col).border = thin_border

    def _get_risk_status(self, value, warning_threshold, critical_threshold, higher_better=False):
        """Get risk status based on thresholds"""
        if higher_better:
            if value >= warning_threshold:
                return "Good"
            elif value >= critical_threshold:
                return "Warning"
            else:
                return "Critical"
        else:
            if value >= critical_threshold:
                return "Good"
            elif value >= warning_threshold:
                return "Warning"
            else:
                return "Critical"

    def _calculate_risk_score(self, metrics):
        """Calculate overall risk score (0-100, higher is better)"""
        score = 100
        
        # Drawdown impact
        if metrics['max_drawdown'] < -100:
            score -= 30
        elif metrics['max_drawdown'] < -50:
            score -= 20
        elif metrics['max_drawdown'] < -25:
            score -= 10
        
        # Sharpe ratio impact
        if metrics['sharpe_ratio'] < 0:
            score -= 20
        elif metrics['sharpe_ratio'] < 0.5:
            score -= 10
        elif metrics['sharpe_ratio'] > 1.5:
            score += 10
        
        # Win rate impact
        if metrics['win_rate'] < 40:
            score -= 15
        elif metrics['win_rate'] > 60:
            score += 10
        
        # Profit factor impact
        if metrics['profit_factor'] < 1:
            score -= 20
        elif metrics['profit_factor'] > 1.5:
            score += 10
        
        return max(0, min(100, score))

    def _get_risk_recommendations(self, metrics, trades_df):
        """Generate risk management recommendations"""
        recommendations = []
        
        if metrics['max_drawdown'] < -50:
            recommendations.append("Consider reducing position size - maximum drawdown exceeds 50%")
        
        if metrics['win_rate'] < 40:
            recommendations.append("Review entry criteria - win rate is below 40%")
        
        if metrics['profit_factor'] < 1.2:
            recommendations.append("Optimize exit strategy - profit factor needs improvement")
        
        if metrics['avg_losing_time'] > metrics['avg_winning_time']:
            recommendations.append("Consider tighter stop losses - losses are held longer than wins")
        
        if not trades_df.empty:
            # Check for overtrading specific symbols
            symbol_losses = trades_df[trades_df['pnl_usd'] < 0].groupby('symbol').size()
            for symbol, loss_count in symbol_losses.items():
                if loss_count > 5:
                    recommendations.append(f"Review trading criteria for {symbol} - high loss frequency")
        
        if len(recommendations) == 0:
            recommendations.append("Risk metrics are within acceptable parameters")
            recommendations.append("Continue monitoring performance consistency")
        
        return recommendations[:5]  # Return top 5 recommendations


print("🚀 HYPERION ADVANCED LOGGER - PROFESSIONAL VERSION READY!")
print("📊 Features: Institutional-grade Excel reports with comprehensive analysis")
print("✅ Clean folder structure - no more empty directories!")
print("💎 Professional formatting suitable for asset management presentation")