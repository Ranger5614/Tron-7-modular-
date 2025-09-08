# market.py - MODULAR VERSION
"""
🌌 MARKET INTERFACE - UNIVERSAL EXCHANGE GATEWAY 🌌
Strategy-agnostic exchange interface for modular trading
Enhanced with OCO orders, retry logic, and robust position verification
Per Aspera Ad Astra
"""

import time
import json
import hmac
import hashlib
import threading
import requests
from urllib.parse import urlencode
from datetime import datetime
import config


class Market:
    def __init__(self):
        """🛸 Initialize Universal Market Gateway"""
        # API Configuration
        if config.ENABLE_FUTURES:
            self.api_prefix = "/fapi/v1"
            self.api_url = "https://fapi.binance.com" if not config.FUTURES_TESTNET else "https://testnet.binancefuture.com"
            print(f"🚀 Futures trading: Using {'TESTNET' if config.FUTURES_TESTNET else 'MAINNET'}")
        else:
            self.api_prefix = "/api/v3"
            self.api_url = "https://api.binance.com" if not config.USE_TESTNET else "https://testnet.binance.vision"
            print(f"📈 Spot trading: Using {'TESTNET' if config.USE_TESTNET else 'MAINNET'}")
        
        self.api_key = config.BINANCE_API_KEY
        self.api_secret = config.BINANCE_API_SECRET
        self.last_request_time = 0
        self.min_request_interval = config.RATE_LIMIT_DELAY
        
        # Session management
        self.session = requests.Session()
        self.session.headers.update({'X-MBX-APIKEY': self.api_key})
        
        # MOVE THESE BEFORE _load_symbol_info() !!!!
        # Circuit breaker settings
        self.circuit_breaker_active = False
        self.circuit_breaker_reset_time = 0
        self.circuit_breaker_cooldown = 60  # 60 second cooldown
        self.api_failure_count = 0
        self.api_failure_threshold = 5  # Trip after 5 consecutive failures
        
        # Order status cache for efficiency
        self._order_status_cache = {}
        self._order_cache_lock = threading.RLock()
        self._last_cache_cleanup = time.time()
        self._max_cache_age = 300  # 5 minutes
        
        # Request nonce for replay protection
        self._request_nonce = 0
        self._nonce_lock = threading.Lock()
        
        # OCO tracking with thread safety
        self.oco_pairs = {}
        self.oco_lock = threading.RLock()
        
        # ENHANCED: Order lifecycle tracking
        self.order_lifecycle = {}
        self.lifecycle_lock = threading.RLock()
        self.order_states = {}  # Track order states: PENDING, FILLED, CANCELLED, FAILED
        
        # NOW load symbol info (after circuit breaker is initialized)
        self.symbol_info = {}
        self._load_symbol_info()  # This can now safely use circuit breaker
        print(f"🌌 Market Interface initialized with {len(self.symbol_info)} symbols")
        
        print(f"🌌 Market Interface initialized")

    def __del__(self):
        """Cleanup resources on deletion"""
        try:
            self.close()
        except:
            pass
    def _check_circuit_breaker(self):
        """🔌 Check if circuit breaker is active"""
        if self.circuit_breaker_active:
            if time.time() > self.circuit_breaker_reset_time:
                print("🔌 Circuit breaker reset - resuming normal operations")
                self.circuit_breaker_active = False
                self.api_failure_count = 0
                return False
            else:
                remaining = int(self.circuit_breaker_reset_time - time.time())
                print(f"🔌 Circuit breaker ACTIVE - {remaining}s remaining")
                return True
        return False

    def _get_default_symbol_info(self, symbol):
        """Get default symbol info for missing symbols"""
        return {
            "base_asset": symbol[:-4] if symbol.endswith('USDT') else symbol[:-3],
            "quote_asset": "USDT",
            "min_qty": 0.001,
            "max_qty": 999999,
            "step_size": 0.001,
            "tick_size": 0.01,
            "min_price": 0,
            "max_price": 999999,
            "min_notional": config.MIN_ORDER_VALUE_USD,
            "quantity_precision": 3,
            "price_precision": 2,
            "status": "TRADING"
        }

    def _handle_api_success(self):
        """✅ Reset failure count on successful API call"""
        if self.api_failure_count > 0:
            self.api_failure_count = 0
            if self.circuit_breaker_active:
                print("🔌 Circuit breaker cleared - API responding normally")
                self.circuit_breaker_active = False
                self.circuit_breaker_reset_time = 0  # Add this line

    def _handle_api_failure(self):
        """❌ Handle API failure and trigger circuit breaker if needed"""
        self.api_failure_count += 1
        
        if self.api_failure_count >= self.api_failure_threshold:
            if not self.circuit_breaker_active:
                self.circuit_breaker_active = True
                self.circuit_breaker_reset_time = time.time() + self.circuit_breaker_cooldown
                print(f"🔌 CIRCUIT BREAKER TRIGGERED - Pausing operations for {self.circuit_breaker_cooldown}s")
                print(f"🔌 Consecutive API failures: {self.api_failure_count}")

    def close(self):
        """Close the session properly"""
        try:
            if hasattr(self, 'session') and self.session:
                self.session.close()
                print("✅ Market session closed")
        except Exception as e:
            print(f"⚠️ Error closing session: {str(e)}")

    def get_cache_stats(self):
        """Get cache statistics for monitoring"""
        with self._order_cache_lock:
            return {
                'order_cache_size': len(self._order_status_cache),
                'oco_pairs_tracked': len(self.oco_pairs),
                'symbol_info_cached': len(self.symbol_info),
                'circuit_breaker_active': self.circuit_breaker_active,
                'api_failure_count': self.api_failure_count
            }
    
    def test_connection(self):
        """🔍 Test connection to exchange"""
        try:
            response = self._make_request("GET", f"{self.api_prefix}/ping")
            if response is not None:
                account = self.get_account_info()
                if account:
                    print("✅ Connection established - Systems nominal")
                    return True
            return False
        except Exception as e:
            print(f"🚨 Connection test failed: {str(e)}")
            return False

    def get_candles(self, symbol, interval, limit=500):
        """📊 Fetch candlestick data"""
        try:
            params = {
                "symbol": symbol,
                "interval": interval,
                "limit": min(limit, 1000)
            }
            response = self._make_request("GET", f"{self.api_prefix}/klines", params)
            return response if response else []
        except Exception as e:
            print(f"🚨 Error fetching candles for {symbol}: {str(e)}")
            return []
    
    def get_open_orders(self, symbol=None):
        """📋 Get all open orders or for specific symbol"""
        try:
            params = {}
            if symbol:
                params["symbol"] = symbol
                
            response = self._make_request("GET", f"{self.api_prefix}/openOrders", params, signed=True)
            
            if response:
                return response
            return []
            
        except Exception as e:
            print(f"🚨 Error getting open orders: {str(e)}")
            return []

    def get_order_book(self, symbol, limit=10):
        """📖 Get order book with VALIDATION"""
        try:
            params = {"symbol": symbol, "limit": limit}
            response = self._make_request("GET", f"{self.api_prefix}/depth", params)
            if response:
                order_book = {
                    'bids': response.get('bids', []),
                    'asks': response.get('asks', []),
                    'lastUpdateId': response.get('lastUpdateId', 0)
                }
                
                # ADDED: Validate before returning
                if self.validate_order_book(order_book):
                    return order_book
                else:
                    print(f"⚠️ Invalid order book data for {symbol}")
                    return None
            return None
        except Exception as e:
            print(f"🚨 Error fetching order book for {symbol}: {str(e)}")
            return None

    def cleanup_oco_for_symbol(self, symbol):
        """Clean up OCO tracking for a closed position"""
        with self.oco_lock:
            if symbol in self.oco_pairs:
                del self.oco_pairs[symbol]
                print(f"🧹 Cleaned up OCO tracking for {symbol}")

    def validate_order_book(self, order_book):
        """🔍 Validate order book data integrity with ENHANCED SAFETY"""
        try:
            if not order_book:
                return False, "Order book is None or empty"
            
            # Check for required fields
            if 'bids' not in order_book or 'asks' not in order_book:
                return False, "Missing bids or asks in order book"
            
            bids = order_book['bids']
            asks = order_book['asks']
            
            if not bids or not asks:
                return False, "Empty bids or asks arrays"
            
            # Check bid/ask structure
            if len(bids) == 0 or len(asks) == 0:
                return False, "No bid or ask data available"
            
            # Validate data format
            try:
                first_bid = bids[0]
                first_ask = asks[0]
                
                if len(first_bid) < 2 or len(first_ask) < 2:
                    return False, "Invalid bid/ask format"
                
                best_bid = float(first_bid[0])
                best_ask = float(first_ask[0])
            except (ValueError, IndexError, TypeError) as e:
                return False, f"Invalid price format: {str(e)}"
            
            # Validate price structure
            if best_bid >= best_ask:
                return False, f"Invalid price structure: bid {best_bid} >= ask {best_ask}"
            
            # ENHANCED: More lenient spread check for volatile markets
            spread = (best_ask - best_bid) / best_bid
            if spread > 0.2:  # Allow up to 20% spread (was 10%)
                return False, f"Spread too wide: {spread:.2%}"
            
            # ENHANCED: Check for reasonable price values
            if best_bid <= 0 or best_ask <= 0:
                return False, "Invalid price values (zero or negative)"
            
            return True, "Order book validation passed"
            
        except Exception as e:
            print(f"🚨 Error validating order book: {str(e)}")
            return False, f"Validation error: {str(e)}"

    def validate_order_book_safe(self, order_book, symbol):
        """🎯 Safer order book validation with detailed error reporting"""
        valid, reason = self.validate_order_book(order_book)
        
        if not valid:
            print(f"⚠️ Order book validation failed for {symbol}: {reason}")
            # ENHANCED: Log the failure but don't reject immediately
            # This allows the system to continue with potentially valid data
            
        return valid, reason
        
    def get_position(self, symbol):
        """📊 Get position for symbol - ALWAYS queries exchange (no caching)
        
        This method ALWAYS fetches fresh data from exchange to ensure accuracy.
        For cached data, use portfolio.positions_cache instead.
        
        Args:
            symbol: Trading symbol to check
            
        Returns:
            Position dict or None if no position exists
        """
        if not config.ENABLE_FUTURES:
            return None
            
        try:
            params = {"symbol": symbol}
            # Use v2 endpoint for most accurate data
            response = self._make_request("GET", "/fapi/v2/positionRisk", params, signed=True)
            
            if response and isinstance(response, list):
                for pos in response:
                    if pos['symbol'] == symbol:
                        amt = float(pos.get('positionAmt', 0))
                        # Return position data even if amt is 0 but entry price exists (recently closed)
                        if amt != 0 or float(pos.get('entryPrice', 0)) > 0:
                            return {
                                'symbol': symbol,
                                'positionAmt': amt,
                                'entryPrice': float(pos.get('entryPrice', 0)),
                                'markPrice': float(pos.get('markPrice', 0)),
                                'unRealizedProfit': float(pos.get('unRealizedProfit', 0)),
                                'positionSide': pos.get('positionSide', 'BOTH'),
                                'liquidationPrice': float(pos.get('liquidationPrice', 0))
                            }
            return None
            
        except Exception as e:
            print(f"🚨 Error getting position: {str(e)}")
            return None

    def set_leverage_with_retry(self, symbol, leverage, max_retries=3):
        """Set leverage with retry logic for reliability"""
        for attempt in range(max_retries):
            try:
                if self.set_leverage(symbol, leverage):
                    return True
                time.sleep(1)
            except Exception as e:
                print(f"⚠️ Leverage setting attempt {attempt + 1} failed: {str(e)}")
                if attempt < max_retries - 1:
                    time.sleep(2 ** attempt)  # Exponential backoff
        
        print(f"🚨 Failed to set leverage for {symbol} after {max_retries} attempts")
        return False

    def get_position_direct(self, symbol):
        """📊 Direct position query with no caching - for critical operations"""
        return self.get_position(symbol)  # Already queries exchange directly

    def get_position_risk(self, symbol=None):
        """📊 Get all position risk data"""
        if not config.ENABLE_FUTURES:
            return []
            
        try:
            params = {}
            if symbol:
                params["symbol"] = symbol
                
            # Use v2 endpoint for futures positions
            response = self._make_request("GET", "/fapi/v2/positionRisk", params, signed=True)
            
            if response:
                # Filter active positions only
                return [pos for pos in response if float(pos.get("positionAmt", 0)) != 0]
            return []
            
        except Exception as e:
            print(f"🚨 Error getting position risk: {str(e)}")
            return []

    def get_all_active_positions(self):
        """📊 Get all positions with non-zero amounts"""
        if not config.ENABLE_FUTURES:
            return {}
        
        try:
            positions = {}
            response = self._make_request("GET", "/fapi/v2/positionRisk", signed=True)
            
            if response:
                for pos in response:
                    amt = float(pos.get('positionAmt', 0))
                    if amt != 0:
                        symbol = pos['symbol']
                        positions[symbol] = {
                            'symbol': symbol,
                            'positionAmt': amt,
                            'entryPrice': float(pos.get('entryPrice', 0)),
                            'markPrice': float(pos.get('markPrice', 0)),
                            'unRealizedProfit': float(pos.get('unRealizedProfit', 0)),
                            'side': 'LONG' if amt > 0 else 'SHORT'
                        }
            
            return positions
            
        except Exception as e:
            print(f"🚨 Error getting all positions: {str(e)}")
            return {}

    def get_trade_history(self, symbol, limit=50):
        """📜 Get recent trades for a symbol"""
        try:
            params = {
                "symbol": symbol,
                "limit": limit
            }
            
            # Use myTrades endpoint
            response = self._make_request("GET", f"{self.api_prefix}/userTrades", params, signed=True)
            
            if response:
                return response
            return []
            
        except Exception as e:
            print(f"🚨 Error getting trade history: {str(e)}")
            return []

    def _rate_limit(self):
        """⚡ Rate limiting to avoid hitting API limits"""
        current_time = time.time()
        elapsed = current_time - self.last_request_time
        
        if elapsed < self.min_request_interval:
            time.sleep(self.min_request_interval - elapsed)
        
        self.last_request_time = time.time()


    def _get_timestamp(self):
        """⏰ Get current timestamp in milliseconds"""
        return int(time.time() * 1000)


    def _generate_signature(self, params):
        """🔐 Generate signature with REPLAY PROTECTION"""
        # Add nonce for replay protection
        with self._nonce_lock:
            self._request_nonce += 1
            params['recvWindow'] = 5000  # 5 second window
            params['timestamp'] = self._get_timestamp()
            
        query_string = urlencode(params)
        return hmac.new(
            self.api_secret.encode('utf-8'),
            query_string.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()


    def get_position_with_retry(self, symbol, max_retries=3):
        """🔄 Get position with retry logic"""
        last_error = None
        
        for attempt in range(max_retries):
            try:
                position = self.get_position(symbol)
                if position is not None:
                    return position
                    
                # If None, might be a temporary issue, retry
                time.sleep(0.5)
                
            except Exception as e:
                last_error = str(e)
                print(f"⚠️ Attempt {attempt + 1} failed to get position: {last_error}")
                if attempt < max_retries - 1:
                    time.sleep(1)
        
        print(f"❌ Failed to get position after {max_retries} attempts")
        return None

    def get_price(self, symbol):
        """💰 Get current price for symbol"""
        try:
            params = {"symbol": symbol}
            response = self._make_request("GET", f"{self.api_prefix}/ticker/price", params)
            return float(response["price"]) if response else None
        except Exception as e:
            print(f"🚨 Error fetching price for {symbol}: {str(e)}")
            return None

    def get_24hr_stats(self, symbol):
        """📈 Get 24hr trading statistics"""
        try:
            params = {"symbol": symbol}
            response = self._make_request("GET", f"{self.api_prefix}/ticker/24hr", params)
            if response:
                return {
                    "volume": float(response.get("volume", 0)),
                    "quoteVolume": float(response.get("quoteVolume", 0)),
                    "priceChangePercent": float(response.get("priceChangePercent", 0)),
                    "high": float(response.get("highPrice", 0)),
                    "low": float(response.get("lowPrice", 0))
                }
            return None
        except Exception as e:
            print(f"🚨 Error fetching 24hr stats for {symbol}: {str(e)}")
            return None

    # In market (modular).py

    def place_order(self, symbol, side, quantity, price=None, reduce_only=False):
        """🚀 Place order using LIVE exchange rules"""
        try:
            import math
            
            # Validate inputs
            if quantity is None or quantity <= 0:
                print(f"❌ Invalid quantity: {quantity}")
                return None
            
            # Ensure we have latest symbol info
            if symbol not in self.symbol_info:
                self.refresh_symbol_info(symbol)
            
            # Format quantity using live rules
            quantity_float = self._format_quantity(symbol, quantity)
            if quantity_float <= 0:
                print(f"❌ Formatted quantity is zero or negative")
                return None
            
            # Get symbol rules
            info = self.symbol_info.get(symbol, {})
            step_size = info.get("step_size", 1.0)
            tick_size = info.get("tick_size", 0.01)
            
            # Calculate precision
            if step_size >= 1:
                qty_precision = 0
            else:
                qty_precision = int(round(-math.log10(step_size), 0))
            
            if tick_size >= 1:
                price_precision = 0
            else:
                price_precision = int(round(-math.log10(tick_size), 0))
            
            # Format quantity string
            quantity_str = f"{quantity_float:.{qty_precision}f}"
            
            # Build parameters
            params = {
                "symbol": symbol,
                "side": side,
                "quantity": quantity_str
            }
            
            # Handle price for limit orders
            if price and config.USE_LIMIT_ORDERS:
                # Format price with tick size
                price_factor = 1 / tick_size
                price_steps = round(price * price_factor)
                formatted_price = price_steps * tick_size
                
                price_str = f"{formatted_price:.{price_precision}f}"
                
                params["type"] = "LIMIT"
                params["price"] = price_str
                params["timeInForce"] = "GTC"
            else:
                params["type"] = "MARKET"
            
            # Add futures parameters
            if config.ENABLE_FUTURES and reduce_only:
                params["reduceOnly"] = "true"
            
            print(f"📊 Placing order for {symbol}:")
            print(f"   Quantity: {quantity_str} (step: {step_size})")
            if price:
                print(f"   Price: {params.get('price', 'N/A')} (tick: {tick_size})")
            
            # Place the order
            response = self._make_request("POST", f"{self.api_prefix}/order", params, signed=True)
            
            if response and response.get("orderId"):
                # Track order lifecycle
                client_order_id = response.get("clientOrderId", f"order_{response['orderId']}")
                self.track_order_lifecycle(symbol, client_order_id)
                
                fallback_price = price if price else self.get_price(symbol)
                return self._parse_order_response(response, fallback_price)
            
            return None
            
        except Exception as e:
            print(f"🚨 Order placement error: {str(e)}")
            import traceback
            traceback.print_exc()
            return None

    def place_order_with_retry(self, symbol, side, quantity, price=None, reduce_only=False):
        """🔄 Place order with retry logic and EXPONENTIAL BACKOFF"""
        last_error = None
        base_delay = config.ORDER_RETRY_DELAY
        max_delay = 30  # Maximum delay between retries
        
        for attempt in range(config.ORDER_RETRY_ATTEMPTS):
            try:
                print(f"🔄 Order attempt {attempt + 1}/{config.ORDER_RETRY_ATTEMPTS} for {symbol}")
                
                # Attempt to place order
                result = self.place_order(symbol, side, quantity, price, reduce_only)
                
                if result:
                    if attempt > 0:
                        print(f"✅ Order succeeded on attempt {attempt + 1}")
                    return result
                
                # If we get here, order returned None (not an exception)
                last_error = "Order returned None"
                
            except Exception as e:
                last_error = str(e)
                print(f"❌ Order attempt {attempt + 1} failed: {last_error}")
            
            # Don't sleep after last attempt
            if attempt < config.ORDER_RETRY_ATTEMPTS - 1:
                # Exponential backoff: delay = base * (2 ^ attempt)
                delay = min(base_delay * (2 ** attempt), max_delay)
                print(f"⏳ Waiting {delay:.1f}s before retry (exponential backoff)...")
                time.sleep(delay)
        
        print(f"🚨 All order attempts failed. Last error: {last_error}")
        return None

    def place_oco_order(self, symbol, side, quantity, price, stop_price, stop_limit_price=None):
        """🎯 Place OCO-style exit orders with INSTITUTIONAL VERIFICATION"""
        if not config.ENABLE_FUTURES:
            print("❌ OCO orders are only available for futures trading")
            return None
        
        try:
            # ENHANCED position verification with immediate retry
            position = None
            max_verify_attempts = 5
            
            for attempt in range(max_verify_attempts):
                position = self.get_position_direct(symbol)
                if position and abs(position.get('positionAmt', 0)) > 0:
                    break
                if attempt < max_verify_attempts - 1:
                    print(f"⏳ Position verification attempt {attempt + 1}/{max_verify_attempts}")
                    time.sleep(0.5)
            
            if not position or abs(position.get('positionAmt', 0)) == 0:
                print(f"❌ Cannot place OCO for {symbol} - no position after {max_verify_attempts} attempts")
                return None
            
            # Use EXACT position quantity
            actual_quantity = abs(float(position['positionAmt']))
            if actual_quantity == 0:
                print(f"❌ Cannot place OCO for {symbol} - position quantity is 0")
                return None
            
            # Format values with proper precision
            formatted_quantity = self._format_quantity(symbol, actual_quantity)
            formatted_price = self._format_price_with_tick_size(symbol, price)
            formatted_stop_price = self._format_price_with_tick_size(symbol, stop_price)
            
            print(f"🎯 Placing exit orders for {symbol}: Qty={formatted_quantity}, TP=${formatted_price}, SL=${formatted_stop_price}")
            
            # Track order IDs
            tp_order_id = None
            sl_order_id = None
            orders_placed = []
            
            try:
                # Place TP order first (LIMIT)
                tp_params = {
                    "symbol": symbol,
                    "side": side,
                    "type": "LIMIT",
                    "quantity": formatted_quantity,
                    "price": formatted_price,
                    "reduceOnly": "true",
                    "timeInForce": "GTC",
                    "newClientOrderId": f"TP_{symbol}_{int(time.time()*1000)}"
                }
                
                tp_response = self._make_request("POST", f"{self.api_prefix}/order", tp_params, signed=True)
                
                if not tp_response or not tp_response.get("orderId"):
                    print(f"❌ Failed to place TP order for {symbol}")
                    return None
                
                tp_order_id = tp_response["orderId"]
                orders_placed.append(('TP', tp_order_id))
                print(f"✅ TP order placed: {tp_order_id} @ ${formatted_price}")
                
                # Minimal delay between orders
                time.sleep(0.2)
                
                # Place SL order (STOP_MARKET)
                sl_params = {
                    "symbol": symbol,
                    "side": side,
                    "type": "STOP_MARKET",
                    "quantity": formatted_quantity,
                    "stopPrice": formatted_stop_price,
                    "reduceOnly": "true",
                    "workingType": "MARK_PRICE",
                    "priceProtect": "true",
                    "newClientOrderId": f"SL_{symbol}_{int(time.time()*1000)}"
                }
                
                sl_response = self._make_request("POST", f"{self.api_prefix}/order", sl_params, signed=True)
                
                if not sl_response or not sl_response.get("orderId"):
                    print(f"❌ Failed to place SL order, cancelling TP order")
                    self.cancel_order(symbol, tp_order_id)
                    return None
                
                sl_order_id = sl_response["orderId"]
                orders_placed.append(('SL', sl_order_id))
                print(f"✅ SL order placed: {sl_order_id} @ ${formatted_stop_price}")
                
                # FAST verification (0.5 second)
                time.sleep(0.5)
                
                verification = self.verify_exit_orders(symbol, tp_order_id, sl_order_id)
                if not verification['tp_found'] or not verification['sl_found']:
                    print(f"⚠️ Exit order verification failed - attempting cleanup")
                    # Don't cancel - they might still be processing
                    # Just log the warning
                
                # Create OCO result
                oco_result = {
                    "tp_order_id": tp_order_id,
                    "sl_order_id": sl_order_id,
                    "tp_price": formatted_price,
                    "sl_price": formatted_stop_price,
                    "quantity": formatted_quantity,
                    "symbol": symbol,
                    "is_oco": True,
                    "created_at": time.time(),
                    "status": "active"
                }
                
                # ENHANCED: Store for monitoring with lifecycle tracking
                with self.oco_lock:
                    self.oco_pairs[symbol] = oco_result
                
                # ENHANCED: Add to order lifecycle tracking
                with self.lifecycle_lock:
                    self.order_lifecycle[symbol] = {
                        'entry_time': time.time(),
                        'oco_created': True,
                        'tp_order_id': tp_order_id,
                        'sl_order_id': sl_order_id,
                        'current_state': 'oco_active',
                        'last_update': time.time(),
                        'tp_price': formatted_price,
                        'sl_price': formatted_stop_price,
                        'quantity': formatted_quantity
                    }
                
                print(f"✅ Exit orders placed for {symbol}: TP={tp_order_id}, SL={sl_order_id}")
                return oco_result
                
            except Exception as e:
                # Clean up on error
                print(f"🚨 Exit order placement error: {str(e)}")
                for order_type, order_id in orders_placed:
                    if order_id:
                        try:
                            self.cancel_order(symbol, order_id)
                            print(f"🧹 Cleaned up {order_type} order: {order_id}")
                        except:
                            pass
                raise e
                
        except Exception as e:
            print(f"🚨 OCO order error for {symbol}: {str(e)}")
            return None 

    def monitor_and_execute_oco_logic(self):
        """🔍 Monitor OCO pairs with ENHANCED RACE CONDITION PROTECTION"""
        if not self.oco_pairs:
            return
        
        orders_to_remove = []
        
        with self.oco_lock:  # Protect against race conditions
            for symbol, oco_data in list(self.oco_pairs.items()):
                try:
                    # Skip if already completed
                    if oco_data.get('status') == 'completed':
                        orders_to_remove.append(symbol)
                        continue
                    
                    # ENHANCED: Atomic check-and-set for processing flag with timeout
                    already_processing = oco_data.setdefault('processing', False)
                    if already_processing:
                        # Check if processing has been stuck for too long (30s timeout)
                        processing_start = oco_data.get('processing_start', 0)
                        if time.time() - processing_start > 30:
                            print(f"⚠️ {symbol} OCO processing stuck for 30s - resetting flag")
                            oco_data['processing'] = False
                        else:
                            continue
                        
                    # Mark as processing atomically with timestamp
                    oco_data['processing'] = True
                    oco_data['processing_start'] = time.time()
                    
                    try:
                        # ENHANCED: Use fresh order status with reduced cache age for critical operations
                        tp_status = self.get_order_status_cached(symbol, oco_data['tp_order_id'], cache_time=0.5)
                        sl_status = self.get_order_status_cached(symbol, oco_data['sl_order_id'], cache_time=0.5)
                        
                        # Case 1: TP filled - cancel SL IMMEDIATELY
                        if tp_status == "FILLED" and sl_status not in ["FILLED", "CANCELED"]:
                            print(f"🎯 {symbol} TP FILLED - cancelling SL order NOW")
                            cancel_success = self._cancel_order_with_retry(symbol, oco_data['sl_order_id'], max_attempts=5)
                            
                            if cancel_success:
                                print(f"✅ SL cancelled successfully")
                            else:
                                print(f"⚠️ Failed to cancel SL after 5 attempts")
                            
                            oco_data['status'] = 'completed'
                            oco_data['exit_type'] = 'TAKE_PROFIT'
                            oco_data['completed_at'] = time.time()
                            orders_to_remove.append(symbol)
                            
                        # Case 2: SL filled - cancel TP IMMEDIATELY
                        elif sl_status == "FILLED" and tp_status not in ["FILLED", "CANCELED"]:
                            print(f"🛡️ {symbol} SL FILLED - cancelling TP order NOW")
                            cancel_success = self._cancel_order_with_retry(symbol, oco_data['tp_order_id'], max_attempts=5)
                            
                            if cancel_success:
                                print(f"✅ TP cancelled successfully")
                            else:
                                print(f"⚠️ Failed to cancel TP after 5 attempts")
                            
                            oco_data['status'] = 'completed'
                            oco_data['exit_type'] = 'STOP_LOSS'
                            oco_data['completed_at'] = time.time()
                            orders_to_remove.append(symbol)
                            
                        # Case 3: Both inactive - check if position closed manually
                        elif tp_status in ["CANCELED", "EXPIRED", None] and sl_status in ["CANCELED", "EXPIRED", None]:
                            position = self.get_position(symbol)
                            if not position or abs(position.get('positionAmt', 0)) == 0:
                                print(f"✅ {symbol} position closed - removing exit order tracking")
                                oco_data['status'] = 'completed'
                                oco_data['exit_type'] = 'MANUAL'
                                oco_data['completed_at'] = time.time()
                                orders_to_remove.append(symbol)
                                
                        # Case 4: Clean up old OCOs (over 12 hours)
                        elif time.time() - oco_data.get('created_at', 0) > 43200:  # 12 hours
                            print(f"🧹 Cleaning up stale OCO for {symbol}")
                            orders_to_remove.append(symbol)
                            
                    except Exception as e:
                        print(f"⚠️ Error monitoring OCO for {symbol}: {str(e)}")
                        # Log the error for debugging
                        import traceback
                        traceback.print_exc()
                    finally:
                        # CRITICAL FIX: Always clear processing flag, even on error
                        oco_data['processing'] = False
                        oco_data.pop('processing_start', None)  # Clean up timestamp
                            
                except Exception as e:
                    print(f"🚨 Critical error in OCO monitoring for {symbol}: {str(e)}")
                    # CRITICAL FIX: Ensure processing flag is cleared on error
                    if symbol in self.oco_pairs:
                        self.oco_pairs[symbol]['processing'] = False
                        self.oco_pairs[symbol].pop('processing_start', None)
            
            # Clean up completed OCOs
            for symbol in orders_to_remove:
                if symbol in self.oco_pairs:
                    del self.oco_pairs[symbol]


    def place_oco_order_with_retry(self, symbol, side, quantity, price, stop_price):
        """🔄 Place OCO order with retry logic and EXPONENTIAL BACKOFF"""
        last_error = None
        base_delay = config.ORDER_RETRY_DELAY
        max_delay = 30  # Maximum delay between retries
        
        for attempt in range(config.OCO_PLACEMENT_RETRIES):
            try:
                print(f"🔄 OCO attempt {attempt + 1}/{config.OCO_PLACEMENT_RETRIES} for {symbol}")
                
                result = self.place_oco_order(symbol, side, quantity, price, stop_price)
                
                if result:
                    if attempt > 0:
                        print(f"✅ OCO succeeded on attempt {attempt + 1}")
                    return result
                
                last_error = "OCO returned None"
                
            except Exception as e:
                last_error = str(e)
                print(f"❌ OCO attempt {attempt + 1} failed: {last_error}")
            
            if attempt < config.OCO_PLACEMENT_RETRIES - 1:
                # Exponential backoff: delay = base * (2 ^ attempt)
                delay = min(base_delay * (2 ** attempt), max_delay)
                print(f"⏳ Waiting {delay:.1f}s before retry (exponential backoff)...")
                time.sleep(delay)
        
        print(f"🚨 All OCO attempts failed. Last error: {last_error}")
        return None

    def check_and_cancel_oco_pairs(self):
        """🔍 Check OCO pairs and cancel the other order when one fills"""
        if not self.oco_pairs:
            return
        
        for symbol, oco_data in list(self.oco_pairs.items()):
            try:
                # Check both orders
                tp_status = self.cache_order_status_fresh(symbol, oco_data['tp_order_id'], max_age=0.5)
                sl_status = self.cache_order_status_fresh(symbol, oco_data['sl_order_id'], max_age=0.5)
                
                # If TP filled, cancel SL
                if tp_status == "FILLED":
                    print(f"🎯 {symbol} TP filled - cancelling SL order {oco_data['sl_order_id']}")
                    self.cancel_order(symbol, oco_data['sl_order_id'])
                    del self.oco_pairs[symbol]
                    
                # If SL filled, cancel TP
                elif sl_status == "FILLED":
                    print(f"🛡️ {symbol} SL filled - cancelling TP order {oco_data['tp_order_id']}")
                    self.cancel_order(symbol, oco_data['tp_order_id'])
                    del self.oco_pairs[symbol]
                    
                # If both are cancelled or expired, remove from tracking
                elif tp_status in ["CANCELED", "EXPIRED", None] and sl_status in ["CANCELED", "EXPIRED", None]:
                    print(f"⚠️ {symbol} OCO orders no longer active - removing from tracking")
                    del self.oco_pairs[symbol]
                    
            except Exception as e:
                print(f"🚨 Error checking OCO pair for {symbol}: {str(e)}")

    def cancel_order(self, symbol, order_id):
        """❌ Cancel an order"""
        try:
            params = {
                "symbol": symbol,
                "orderId": order_id
            }
            
            response = self._make_request("DELETE", f"{self.api_prefix}/order", params, signed=True)
            return response is not None
            
        except Exception as e:
            # Order already filled/canceled is success
            if any(phrase in str(e).lower() for phrase in ['unknown order', 'order does not exist']):
                return True
            print(f"❌ Cancel order error: {str(e)}")
            return False

    def _cancel_order_with_retry(self, symbol, order_id, max_attempts=3):
        """❌ Cancel order with enhanced retry logic for critical operations"""
        for attempt in range(max_attempts):
            try:
                if self.cancel_order(symbol, order_id):
                    return True
                
                # Exponential backoff between attempts
                if attempt < max_attempts - 1:
                    delay = 0.1 * (2 ** attempt)  # 0.1s, 0.2s, 0.4s, etc.
                    time.sleep(delay)
                    
            except Exception as e:
                print(f"🚨 Cancel attempt {attempt + 1} failed: {str(e)}")
                if attempt < max_attempts - 1:
                    time.sleep(0.1)
        
        return False

    def cancel_all_orders_for_symbol(self, symbol):
        """❌ Cancel all open orders for a symbol"""
        try:
            params = {"symbol": symbol}
            
            response = self._make_request("DELETE", f"{self.api_prefix}/allOpenOrders", params, signed=True)
            
            if response:
                print(f"✅ Cancelled all orders for {symbol}")
                return True
            return False
            
        except Exception as e:
            print(f"❌ Error cancelling all orders for {symbol}: {str(e)}")
            return False

    def cancel_all_exit_orders(self, symbol):
        """❌ Cancel only TP/SL orders for a symbol"""
        try:
            open_orders = self.get_open_orders(symbol)
            cancelled_count = 0
            
            for order in open_orders:
                # Identify exit orders
                if order.get('reduceOnly'):
                    if self.cancel_order(symbol, order['orderId']):
                        cancelled_count += 1
            
            if cancelled_count > 0:
                print(f"✅ Cancelled {cancelled_count} exit orders for {symbol}")
            
            return True
            
        except Exception as e:
            print(f"❌ Error cancelling exit orders: {str(e)}")
            return False

    def check_order_status(self, symbol, order_id):
        """🔍 Check order status"""
        try:
            params = {
                "symbol": symbol,
                "orderId": order_id
            }
            
            response = self._make_request("GET", f"{self.api_prefix}/order", params, signed=True)
            if response:
                return response.get("status")
                
            # Check order history if not found
            history_params = {
                "symbol": symbol,
                "orderId": order_id,
                "limit": 1
            }
            
            history = self._make_request("GET", f"{self.api_prefix}/allOrders", history_params, signed=True)
            if history and len(history) > 0:
                return history[0].get("status")
                
            return None
            
        except Exception as e:
            print(f"❌ Error checking order status: {str(e)}")
            return None

    def get_order_status_cached(self, symbol, order_id, cache_time=0.5):
        """🚀 Get order status with ENHANCED THREAD-SAFE caching and auto-cleanup"""
        cache_key = f"{symbol}_{order_id}"
        current_time = time.time()
        
        with self._order_cache_lock:  # Thread safety
            # ENHANCED: More frequent cache cleanup for critical operations
            if current_time - self._last_cache_cleanup > 30:  # Every 30 seconds
                self._cleanup_order_cache()
                self._last_cache_cleanup = current_time
            
            # Check if we have cached status
            if cache_key in self._order_status_cache:
                cached_data = self._order_status_cache[cache_key]
                if current_time - cached_data['timestamp'] < cache_time:
                    return cached_data['status']
        
        # Get fresh status
        status = self.check_order_status(symbol, order_id)
        
        # Cache it thread-safely
        with self._order_cache_lock:
            self._order_status_cache[cache_key] = {
                'status': status,
                'timestamp': current_time
            }
        
        return status

    def cache_order_status_fresh(self, symbol, order_id, max_age=0.5):
        """🎯 Fresh order status with configurable cache age for all operations"""
        return self.get_order_status_cached(symbol, order_id, cache_time=max_age)

    def _cleanup_order_cache(self):
        """Clean up old cache entries - must be called with lock held"""
        current_time = time.time()
        cutoff_time = current_time - self._max_cache_age
        
        # Remove old entries
        old_size = len(self._order_status_cache)
        self._order_status_cache = {
            k: v for k, v in self._order_status_cache.items()
            if v['timestamp'] > cutoff_time
        }
        
        # Also limit total size
        if len(self._order_status_cache) > 200:  # Max 200 entries
            # Keep only 100 most recent
            sorted_items = sorted(
                self._order_status_cache.items(),
                key=lambda x: x[1]['timestamp'],
                reverse=True
            )
            self._order_status_cache = dict(sorted_items[:100])
        
        new_size = len(self._order_status_cache)
        if old_size - new_size > 0:
            print(f"🧹 Cleaned {old_size - new_size} cache entries")

    def wait_for_order_fill(self, symbol, order_id, timeout=None):
        """⏳ Wait for order to fill - REDUCED LOGGING"""
        timeout = timeout or config.PARTIAL_FILL_TIMEOUT
        start_time = time.time()
        
        print(f"⏳ Waiting for order {order_id} to fill (timeout: {timeout}s)...")
        
        last_log_time = 0
        log_interval = 5  # Only log every 5 seconds
        
        while time.time() - start_time < timeout:
            try:
                # Check order status
                status = self.cache_order_status_fresh(symbol, order_id, max_age=0.5)
                elapsed = int(time.time() - start_time)
                
                # Only log periodically, not every check
                if elapsed - last_log_time >= log_interval:
                    print(f"   Order status: {status} ({elapsed}s elapsed)")
                    last_log_time = elapsed
                
                # Check if filled
                if status == "FILLED":
                    print(f"✅ Order {order_id} FILLED!")
                    return True
                elif status in ["CANCELED", "REJECTED", "EXPIRED"]:
                    print(f"❌ Order {order_id} terminated: {status}")
                    return False
                
                time.sleep(0.5)  # Check every 500ms
                    
            except Exception as e:
                if "Order does not exist" in str(e):
                    # Check if position exists (order might have filled)
                    position = self.get_position(symbol)
                    if position and abs(position.get('positionAmt', 0)) > 0:
                        print(f"✅ Position exists - treating as filled")
                        return True
                
                # Only log errors once
                if elapsed == 0:
                    print(f"⚠️ Error checking order: {str(e)}")
                time.sleep(1)
        
        print(f"⏰ Order {order_id} timed out after {timeout}s")
        return False

    def get_order_fills(self, symbol, order_id):
        """📊 Get detailed fill information for an order"""
        try:
            # Get recent trades
            trades = self.get_trade_history(symbol, limit=50)
            
            # Filter for this order
            order_fills = [t for t in trades if str(t.get('orderId')) == str(order_id)]
            
            if order_fills:
                total_qty = sum(float(f['qty']) for f in order_fills)
                total_value = sum(float(f['qty']) * float(f['price']) for f in order_fills)
                avg_price = total_value / total_qty if total_qty > 0 else 0
                
                return {
                    "total_qty": total_qty,
                    "avg_price": avg_price,
                    "fills": order_fills,
                    "fill_count": len(order_fills)
                }
            
            return None
            
        except Exception as e:
            print(f"🚨 Error getting order fills: {str(e)}")
            return None

    def verify_no_pending_orders(self, symbol):
        """✅ Verify no pending orders exist for symbol"""
        try:
            open_orders = self.get_open_orders(symbol)
            
            # Check for non-reduce-only orders (entry orders)
            entry_orders = [o for o in open_orders if not o.get('reduceOnly', False)]
            
            return len(entry_orders) == 0
            
        except Exception as e:
            print(f"🚨 Error verifying pending orders: {str(e)}")
            return False

    def verify_position_exists(self, symbol):
        """✅ Verify a position actually exists on exchange - CRITICAL METHOD"""
        if not config.ENABLE_FUTURES:
            return False
            
        try:
            # Method 1: Direct position query
            position = self.get_position_direct(symbol)
            if position and abs(position.get('positionAmt', 0)) > 0:
                return True
            
            # Method 2: Check all positions
            all_positions = self.get_position_risk()
            if all_positions:
                for pos in all_positions:
                    if pos.get('symbol') == symbol and abs(float(pos.get('positionAmt', 0))) > 0:
                        return True
            
            # Method 3: Double-check with individual query
            time.sleep(0.5)  # Brief delay
            position = self.get_position_direct(symbol)
            if position and abs(position.get('positionAmt', 0)) > 0:
                return True
            
            return False
            
        except Exception as e:
            print(f"🚨 Error verifying position: {str(e)}")
            # On error, assume position exists for safety
            return True

    def verify_no_position_exists(self, symbol):
        """✅ ENHANCED: Triple-check that NO position exists for a symbol"""
        # SKIP IF DEBUG MODE
        if hasattr(config, 'SKIP_POSITION_VERIFICATION') and config.SKIP_POSITION_VERIFICATION:
            print(f"⚠️ SKIPPING POSITION VERIFICATION FOR {symbol} (DEBUG MODE)")
            return True
            
        if not config.ENABLE_FUTURES:
            return True
        
        try:
            print(f"\n🔍 POSITION VERIFICATION FOR {symbol}:")
            
            # Check 1: Direct position query with v2 endpoint (most accurate)
            print(f"  Check 1: Direct position query...")
            position = self.get_position_direct(symbol)
            if position and abs(position.get('positionAmt', 0)) > 0:
                print(f"  ❌ FOUND POSITION: Amount = {position.get('positionAmt')}")
                return False
            print(f"  ✅ No position found in direct query")
            
            # Check 2: Get ALL positions and search
            print(f"  Check 2: Checking all positions...")
            all_positions = self.get_position_risk()
            if all_positions:
                for pos in all_positions:
                    if pos.get('symbol') == symbol:
                        amt = float(pos.get('positionAmt', 0))
                        if amt != 0:
                            print(f"  ❌ FOUND POSITION in all positions: Amount = {amt}")
                            return False
            print(f"  ✅ No position found in all positions")
            
            # Check 3: Check open orders (entry orders could indicate pending position)
            print(f"  Check 3: Checking open orders...")
            open_orders = self.get_open_orders(symbol)
            for order in open_orders:
                # Look for non-reduce-only orders (entry orders)
                if not order.get('reduceOnly', False):
                    print(f"  ❌ FOUND ENTRY ORDER: {order.get('orderId')} - {order.get('side')} {order.get('origQty')}")
                    return False
            print(f"  ✅ No entry orders found")
            
            # Check 4: Brief wait and re-check (catches race conditions)
            print(f"  Check 4: Final verification after delay...")
            time.sleep(0.5)
            position = self.get_position_direct(symbol)
            if position and abs(position.get('positionAmt', 0)) > 0:
                print(f"  ❌ FOUND POSITION AFTER DELAY: Amount = {position.get('positionAmt')}")
                return False
            
            print(f"  ✅ ALL CHECKS PASSED - No position exists for {symbol}")
            return True
            
        except Exception as e:
            print(f"🚨 Error verifying no position for {symbol}: {str(e)}")
            # On error, assume position exists for safety
            return False

    def get_account_info(self):
        """🏦 Get account information"""
        try:
            if config.ENABLE_FUTURES:
                # Use v2 for futures
                endpoint = "/fapi/v2/account"
            else:
                endpoint = f"{self.api_prefix}/account"
            return self._make_request("GET", endpoint, signed=True)
        except Exception as e:
            print(f"🚨 Error fetching account info: {str(e)}")
            return None

    def get_total_balance_usd(self):
        """💰 Get total account balance in USD"""
        try:
            print("🔍 Fetching account balance...")
            all_balances = self.get_all_balances()
            
            if not all_balances:
                print("⚠️ No balances returned")
                return 0
                
            total_usd = 0
            
            for asset, balance_info in all_balances.items():
                if asset == "USDT":
                    total_usd += balance_info["total"]
                    print(f"💵 Found USDT balance: {balance_info['total']:.2f}")
                else:
                    # Skip other assets for now
                    if balance_info["total"] > 0.0001:
                        print(f"⚠️ Skipping {asset} conversion (balance: {balance_info['total']})")
                        
            print(f"💰 Total balance: ${total_usd:.2f}")
            return total_usd
        except Exception as e:
            print(f"🚨 Error calculating USD balance: {str(e)}")
            return 0

    def get_all_balances(self):
        """💎 Get all non-zero balances"""
        try:
            account = self.get_account_info()
            if not account:
                return {}
                
            balances = {}
            
            if config.ENABLE_FUTURES:
                for balance in account.get("assets", []):
                    total = float(balance.get("walletBalance", 0))
                    if total > 0:
                        balances[balance["asset"]] = {
                            "free": float(balance.get("availableBalance", 0)),
                            "locked": total - float(balance.get("availableBalance", 0)),
                            "total": total
                        }
            else:
                for balance in account.get("balances", []):
                    free = float(balance["free"])
                    locked = float(balance["locked"])
                    total = free + locked
                    if total > 0:
                        balances[balance["asset"]] = {
                            "free": free,
                            "locked": locked,
                            "total": total
                        }
            
            return balances
        except Exception as e:
            print(f"🚨 Error fetching balances: {str(e)}")
            return {}

    def calculate_quantity(self, symbol, usd_amount, price):
        """🧮 Calculate order quantity from USD amount - ENHANCED"""
        try:
            if price is None or price <= 0:
                print(f"❌ Invalid price for {symbol}: {price}")
                return 0
                
            if usd_amount is None or usd_amount <= 0:
                print(f"❌ Invalid USD amount: {usd_amount}")
                return 0
            
            # Ensure we have symbol info
            if symbol not in self.symbol_info:
                self.refresh_symbol_info(symbol)
            
            # Get symbol info
            info = self.symbol_info.get(symbol, {})
            min_notional = info.get("min_notional", config.MIN_ORDER_VALUE_USD)
            step_size = info.get("step_size", 0.01)
            min_qty = info.get("min_qty", step_size)
            
            # CRITICAL: Ensure we meet minimum notional
            if usd_amount < min_notional:
                print(f"📈 Adjusting order size from ${usd_amount:.2f} to minimum ${min_notional:.2f}")
                usd_amount = min_notional * 1.1  # Add 10% buffer
            
            # Calculate raw quantity
            raw_quantity = usd_amount / price
            
            # Format quantity according to step size
            formatted_quantity = self._format_quantity(symbol, raw_quantity)
            
            # Verify the formatted quantity meets minimum
            if formatted_quantity < min_qty:
                formatted_quantity = min_qty
                print(f"📈 Adjusted to minimum quantity: {formatted_quantity}")
            
            # Final notional check
            notional_value = formatted_quantity * price
            
            print(f"🔍 {symbol}: Raw qty: {raw_quantity:.6f}, Formatted: {formatted_quantity:.6f}, "
                f"Notional: ${notional_value:.2f}, Min: ${min_notional:.2f}")
            
            # If still below minimum, increase quantity
            if notional_value < min_notional:
                # Calculate exact quantity needed
                min_quantity = (min_notional * 1.1) / price
                formatted_quantity = self._format_quantity(symbol, min_quantity)
                new_notional = formatted_quantity * price
                
                print(f"📈 Final adjustment for {symbol}: Qty: {formatted_quantity:.6f}, Notional: ${new_notional:.2f}")
                
                # Final check
                if new_notional < min_notional:
                    print(f"❌ Cannot meet minimum notional for {symbol}: ${min_notional:.2f}")
                    return 0
            
            return formatted_quantity
            
        except Exception as e:
            print(f"🚨 Error calculating quantity: {str(e)}")
            import traceback
            traceback.print_exc()
            return 0

    def set_leverage(self, symbol, leverage):
        """⚡ Set leverage for futures symbol"""
        if not config.ENABLE_FUTURES:
            return True
            
        try:
            params = {
                "symbol": symbol,
                "leverage": int(leverage)
            }
            
            response = self._make_request("POST", f"{self.api_prefix}/leverage", params, signed=True)
            
            if response:
                actual = response.get("leverage", 0)
                if actual == leverage:
                    print(f"⚡ Leverage set to {leverage}x for {symbol}")
                    return True
                    
            return False
            
        except Exception as e:
            print(f"🚨 Error setting leverage: {str(e)}")
            return False

    def set_margin_type(self, symbol, margin_type="ISOLATED"):
        """💰 Set margin type for futures"""
        if not config.ENABLE_FUTURES:
            return True
            
        try:
            params = {
                "symbol": symbol,
                "marginType": margin_type
            }
            
            response = self._make_request("POST", f"{self.api_prefix}/marginType", params, signed=True)
            
            # Error -4046 means already set correctly
            if response or (isinstance(response, dict) and response.get('code') == -4046):
                print(f"💰 Margin type set to {margin_type} for {symbol}")
                return True
                
            return False
            
        except Exception as e:
            if "-4046" in str(e):
                return True
            print(f"🚨 Error setting margin type: {str(e)}")
            return False

    def set_position_mode(self, hedge_mode=False):
        """⚡ Set position mode for futures"""
        if not config.ENABLE_FUTURES:
            return True
            
        try:
            params = {
                "dualSidePosition": "true" if hedge_mode else "false"
            }
            
            response = self._make_request("POST", f"{self.api_prefix}/positionSide/dual", params, signed=True)
            
            # Error -4059 means already in correct mode
            if response or (isinstance(response, dict) and response.get('code') == -4059):
                mode_name = "Hedge" if hedge_mode else "One-way"
                print(f"⚡ Position mode set to {mode_name}")
                return True
                
            return False
            
        except Exception as e:
            if "-4059" in str(e):
                return True
            print(f"🚨 Error setting position mode: {str(e)}")
            return False

    def verify_exit_orders(self, symbol, tp_order_id=None, sl_order_id=None):
        """✅ Verify exit orders exist and are active"""
        try:
            open_orders = self.get_open_orders(symbol)
            
            tp_found = False
            sl_found = False
            
            for order in open_orders:
                order_id = str(order.get("orderId"))
                
                if tp_order_id and str(tp_order_id) == order_id:
                    tp_found = True
                    print(f"✅ TP order verified: {symbol} - ID: {order_id}")
                    
                if sl_order_id and str(sl_order_id) == order_id:
                    sl_found = True
                    print(f"✅ SL order verified: {symbol} - ID: {order_id}")
            
            if tp_order_id and not tp_found:
                print(f"⚠️ TP order not found for {symbol} - ID: {tp_order_id}")
                
            if sl_order_id and not sl_found:
                print(f"⚠️ SL order not found for {symbol} - ID: {sl_order_id}")
                
            return {"tp_found": tp_found, "sl_found": sl_found}
            
        except Exception as e:
            print(f"🚨 Error verifying exit orders: {str(e)}")
            return {"tp_found": False, "sl_found": False}

    def verify_exit_orders_fast(self, symbol):
        """✅ FAST verification of exit orders - single API call"""
        try:
            open_orders = self.get_open_orders(symbol)
            
            has_tp = False
            has_sl = False
            tp_id = None
            sl_id = None
            
            for order in open_orders:
                if not order.get('reduceOnly'):
                    continue
                    
                order_type = order.get('type')
                if order_type == 'LIMIT':
                    has_tp = True
                    tp_id = order.get('orderId')
                elif order_type in ['STOP_MARKET', 'STOP', 'STOP_LOSS_LIMIT']:
                    has_sl = True
                    sl_id = order.get('orderId')
            
            return {
                'has_tp': has_tp,
                'has_sl': has_sl,
                'tp_id': tp_id,
                'sl_id': sl_id,
                'both_present': has_tp and has_sl
            }
            
        except Exception as e:
            print(f"🚨 Error verifying exit orders: {str(e)}")
            return {
                'has_tp': False,
                'has_sl': False,
                'tp_id': None,
                'sl_id': None,
                'both_present': False
            }

    def ensure_exit_orders(self, symbol, position_data):
        """🔍 Ensure a position has both TP and SL orders"""
        if not config.ENABLE_FUTURES:
            return {"tp_exists": False, "sl_exists": False}
            
        try:
            open_orders = self.get_open_orders(symbol)
            
            tp_exists = False
            sl_exists = False
            tp_order_id = None
            sl_order_id = None
            
            # Check existing orders
            for order in open_orders:
                if order.get('type') == 'LIMIT' and order.get('reduceOnly'):
                    tp_exists = True
                    tp_order_id = order.get('orderId')
                elif order.get('type') in ['STOP_MARKET', 'STOP'] and order.get('reduceOnly'):
                    sl_exists = True
                    sl_order_id = order.get('orderId')
            
            result = {
                "tp_exists": tp_exists,
                "sl_exists": sl_exists,
                "tp_order_id": tp_order_id,
                "sl_order_id": sl_order_id
            }
            
            # Report status
            if not tp_exists:
                print(f"⚠️ {symbol} missing TP order")
            if not sl_exists:
                print(f"⚠️ {symbol} missing SL order")
            if tp_exists and sl_exists:
                print(f"✅ {symbol} has both exit orders")
                
            return result
            
        except Exception as e:
            print(f"🚨 Error checking exit orders for {symbol}: {str(e)}")
            return {"tp_exists": False, "sl_exists": False}

    def get_all_positions_for_symbols(self, symbols):
        """🔍 Check multiple symbols for positions in one call"""
        if not config.ENABLE_FUTURES:
            return {}
            
        try:
            positions = self.get_position_risk()
            if not positions:
                return {}
                
            result = {}
            for symbol in symbols:
                result[symbol] = False  # Default to no position
                
            for pos in positions:
                symbol = pos.get('symbol')
                if symbol in symbols:
                    amt = float(pos.get('positionAmt', 0))
                    if amt != 0:
                        result[symbol] = True
                        
            return result
            
        except Exception as e:
            print(f"🚨 Error checking positions for symbols: {str(e)}")
            return {}

    def get_exit_order_status(self, symbol, tp_order_id, sl_order_id):
        """🎯 Get status of exit orders"""
        try:
            status = {
                "tp_status": None,
                "tp_filled": False,
                "tp_fill_price": 0,
                "sl_status": None,
                "sl_filled": False,
                "sl_fill_price": 0
            }
            
            # Check TP order
            if tp_order_id:
                tp_order = self.get_order_by_id(symbol, tp_order_id)
                if tp_order:
                    status["tp_status"] = tp_order["status"]
                    status["tp_filled"] = tp_order["status"] == "FILLED"
                    if status["tp_filled"]:
                        status["tp_fill_price"] = tp_order["avgPrice"] or tp_order["price"]
            
            # Check SL order
            if sl_order_id:
                sl_order = self.get_order_by_id(symbol, sl_order_id)
                if sl_order:
                    status["sl_status"] = sl_order["status"]
                    status["sl_filled"] = sl_order["status"] == "FILLED"
                    if status["sl_filled"]:
                        status["sl_fill_price"] = sl_order["avgPrice"] or sl_order["price"]
            
            return status
            
        except Exception as e:
            print(f"🚨 Error checking exit orders: {str(e)}")
            return None

    def get_order_by_id(self, symbol, order_id):
        """🔍 Get detailed order information by ID"""
        try:
            params = {
                "symbol": symbol,
                "orderId": order_id
            }
            
            # First try to get from open orders
            response = self._make_request("GET", f"{self.api_prefix}/order", params, signed=True)
            
            if response:
                return {
                    "orderId": response.get("orderId"),
                    "symbol": response.get("symbol"),
                    "status": response.get("status"),
                    "type": response.get("type"),
                    "side": response.get("side"),
                    "price": float(response.get("price", 0)),
                    "avgPrice": float(response.get("avgPrice", 0)),
                    "executedQty": float(response.get("executedQty", 0)),
                    "time": response.get("time"),
                    "reduceOnly": response.get("reduceOnly", False)
                }
            
            # If not found in open orders, check history
            return self.get_historical_order(symbol, order_id)
            
        except Exception as e:
            print(f"🚨 Error getting order {order_id}: {str(e)}")
            return None

    def get_historical_order(self, symbol, order_id):
        """📜 Get historical order information"""
        try:
            params = {
                "symbol": symbol,
                "orderId": order_id,
                "limit": 1
            }
            
            response = self._make_request("GET", f"{self.api_prefix}/allOrders", params, signed=True)
            
            if response and len(response) > 0:
                order = response[0]
                return {
                    "orderId": order.get("orderId"),
                    "symbol": order.get("symbol"),
                    "status": order.get("status"),
                    "type": order.get("type"),
                    "side": order.get("side"),
                    "price": float(order.get("price", 0)),
                    "avgPrice": float(order.get("avgPrice", 0)),
                    "executedQty": float(order.get("executedQty", 0)),
                    "time": order.get("time"),
                    "reduceOnly": order.get("reduceOnly", False)
                }
            
            return None
            
        except Exception as e:
            print(f"🚨 Error getting historical order: {str(e)}")
            return None

    def get_recent_orders(self, symbol, limit=50):
        """📋 Get recent orders for a symbol (including filled)"""
        try:
            params = {
                "symbol": symbol,
                "limit": limit
            }
            
            response = self._make_request("GET", f"{self.api_prefix}/allOrders", params, signed=True)
            
            if response:
                # Format and return order data
                orders = []
                for order in response:
                    orders.append({
                        "orderId": order.get("orderId"),
                        "symbol": order.get("symbol"),
                        "status": order.get("status"),
                        "type": order.get("type"),
                        "side": order.get("side"),
                        "price": float(order.get("price", 0)),
                        "avgPrice": float(order.get("avgPrice", 0)),
                        "executedQty": float(order.get("executedQty", 0)),
                        "time": order.get("time"),
                        "updateTime": order.get("updateTime", order.get("time")),  # ADD THIS LINE!
                        "reduceOnly": order.get("reduceOnly", False)
                    })
                
                return orders
            
            return []
            
        except Exception as e:
            print(f"🚨 Error getting recent orders: {str(e)}")
            return []

    def cancel_order_safe(self, symbol, order_id):
        """🛡️ Safely cancel an order (handles already filled/cancelled)"""
        try:
            # First check if order exists and is cancellable
            order = self.get_order_by_id(symbol, order_id)
            
            if not order:
                return True  # Order doesn't exist, consider it cancelled
                
            if order["status"] in ["FILLED", "CANCELED", "REJECTED", "EXPIRED"]:
                return True  # Already in terminal state
                
            # Try to cancel
            return self.cancel_order(symbol, order_id)
            
        except Exception as e:
            # If error contains "Unknown order", it's already gone
            if "unknown order" in str(e).lower():
                return True
            print(f"🚨 Error in safe cancel: {str(e)}")
            return False

    def cleanup_orphaned_orders(self):
        """🧹 Clean up any exit orders without positions"""
        if not config.ENABLE_FUTURES:
            return
            
        try:
            print("🧹 Checking for orphaned exit orders...")
            
            # Get all open orders
            open_orders = self._make_request("GET", f"{self.api_prefix}/openOrders", signed=True)
            if not open_orders:
                print("✅ No open orders found")
                return
                
            # Get all active positions
            active_positions = self.get_position_risk()
            position_symbols = {pos['symbol'] for pos in active_positions}
            
            orphaned_count = 0
            
            for order in open_orders:
                order_type = order.get('type', '')
                symbol = order.get('symbol', '')
                
                # Check if this is an exit order (stop or take profit)
                if order_type in ['STOP_MARKET', 'TAKE_PROFIT_MARKET', 'LIMIT'] and order.get('reduceOnly'):
                    # Check if we have a position for this symbol
                    if symbol not in position_symbols:
                        print(f"🧹 Found orphaned {order_type} order for {symbol} - cancelling...")
                        if self.cancel_order(symbol, order['orderId']):
                            orphaned_count += 1
            
            if orphaned_count > 0:
                print(f"✅ Cleaned up {orphaned_count} orphaned orders")
            else:
                print("✅ No orphaned orders found")
                
        except Exception as e:
            print(f"🚨 Error during orphaned order cleanup: {str(e)}")

    # === PRIVATE HELPER METHODS ===

    def _parse_order_response(self, response, fallback_price):
        """📊 Parse order response into standardized format"""
        try:
            executed_qty = float(response.get("executedQty", 0))
            if executed_qty == 0:
                executed_qty = float(response.get("origQty", 0))
            
            # Calculate fill price
            fill_price = fallback_price if fallback_price else 0
            
            if config.ENABLE_FUTURES:
                avg_price = float(response.get("avgPrice", 0))
                if avg_price > 0:
                    fill_price = avg_price
                elif response.get("type") == "LIMIT":
                    # For LIMIT orders, use the limit price
                    fill_price = float(response.get("price", fallback_price))
            elif "fills" in response and len(response["fills"]) > 0:
                total_value = sum(float(fill["qty"]) * float(fill["price"]) for fill in response["fills"])
                total_qty = sum(float(fill["qty"]) for fill in response["fills"])
                if total_qty > 0:
                    fill_price = total_value / total_qty
            
            return {
                "symbol": response["symbol"],
                "orderId": response["orderId"],
                "side": response["side"],
                "price": fill_price,
                "quantity": self._format_quantity(response["symbol"], executed_qty),
                "status": response["status"],
                "type": response["type"]
            }
        except Exception as e:
            print(f"🚨 Error parsing order response: {str(e)}")
            return None

    def _load_symbol_info(self):
        """🔡 Load trading rules DIRECTLY from exchange - NO HARDCODING"""
        try:
            print("🔡 Fetching LIVE symbol information from Binance...")
            
            # Get configured symbols
            configured_symbols = set(config.PAIR_CONFIGS.keys())
            if not configured_symbols:
                print("⚠️ No symbols configured in PAIR_CONFIGS")
                return
            
            print(f"📊 Fetching rules for: {', '.join(sorted(configured_symbols))}")
            
            # Fetch from exchange
            response = self._make_request("GET", f"{self.api_prefix}/exchangeInfo")
            if not response:
                print("❌ Failed to fetch exchange info")
                return
            
            # Parse the response
            loaded_count = 0
            not_found = []
            
            for symbol_data in response.get("symbols", []):
                symbol = symbol_data["symbol"]
                
                # Skip if not in our configured list
                if symbol not in configured_symbols:
                    continue
                
                # Get filters
                filters = {f["filterType"]: f for f in symbol_data.get("filters", [])}
                
                # LOT_SIZE filter (for quantity rules)
                lot_size = filters.get("LOT_SIZE", {})
                step_size = float(lot_size.get("stepSize", 1.0))
                min_qty = float(lot_size.get("minQty", 1.0))
                max_qty = float(lot_size.get("maxQty", 10000000.0))
                
                # PRICE_FILTER (for price rules)
                price_filter = filters.get("PRICE_FILTER", {})
                tick_size = float(price_filter.get("tickSize", 0.01))
                min_price = float(price_filter.get("minPrice", 0.0))
                max_price = float(price_filter.get("maxPrice", 10000.0))
                
                # MIN_NOTIONAL filter
                if config.ENABLE_FUTURES:
                    notional_filter = filters.get("NOTIONAL", {})
                    min_notional = float(notional_filter.get("minNotional", 20.0))
                else:
                    min_notional_filter = filters.get("MIN_NOTIONAL", {})
                    min_notional = float(min_notional_filter.get("minNotional", 20.0))
                
                # Calculate precision from step/tick sizes
                import math
                
                # For quantity precision
                if step_size >= 1:
                    quantity_precision = 0
                else:
                    quantity_precision = int(round(-math.log10(step_size), 0))
                
                # For price precision
                if tick_size >= 1:
                    price_precision = 0
                else:
                    price_precision = int(round(-math.log10(tick_size), 0))
                
                # Store the info
                self.symbol_info[symbol] = {
                    "base_asset": symbol_data.get("baseAsset", ""),
                    "quote_asset": symbol_data.get("quoteAsset", ""),
                    "min_qty": min_qty,
                    "max_qty": max_qty,
                    "step_size": step_size,
                    "tick_size": tick_size,
                    "min_price": min_price,
                    "max_price": max_price,
                    "min_notional": min_notional,
                    "quantity_precision": quantity_precision,
                    "price_precision": price_precision,
                    "status": symbol_data.get("status", "TRADING"),
                    "contract_type": symbol_data.get("contractType", "PERPETUAL"),
                    "filters": filters,
                    "last_updated": time.time()
                }
                
                loaded_count += 1
                
                # Log the actual values
                print(f"   ✅ {symbol}:")
                print(f"      Quantity: step={step_size}, precision={quantity_precision}, min={min_qty}")
                print(f"      Price: tick={tick_size}, precision={price_precision}")
                print(f"      Min notional: ${min_notional}")
            
            # Check for missing symbols
            loaded_symbols = set(self.symbol_info.keys())
            missing = configured_symbols - loaded_symbols
            
            if missing:
                print(f"⚠️ Not found on exchange: {', '.join(missing)}")
                # Try to load them individually
                for symbol in missing:
                    self._fetch_single_symbol_info(symbol)
            
            print(f"\n✅ Successfully loaded {len(self.symbol_info)} symbols from exchange")
            
            # Show summary
            print("\n📊 TRADING RULES SUMMARY:")
            for symbol in sorted(self.symbol_info.keys()):
                info = self.symbol_info[symbol]
                if info['step_size'] >= 1:
                    print(f"   {symbol}: Quantity must be multiples of {info['step_size']:.0f} (whole numbers)")
                else:
                    print(f"   {symbol}: Quantity precision = {info['quantity_precision']} decimals (step: {info['step_size']})")
            
        except Exception as e:
            print(f"🚨 Error loading symbol info: {str(e)}")
            import traceback
            traceback.print_exc()

    def _fetch_single_symbol_info(self, symbol):
        """Fetch info for a single symbol"""
        try:
            params = {"symbol": symbol}
            response = self._make_request("GET", f"{self.api_prefix}/exchangeInfo", params)
            
            if response and "symbols" in response:
                for symbol_data in response["symbols"]:
                    if symbol_data["symbol"] == symbol:
                        # Parse it the same way as above
                        # (copy the parsing logic from _load_symbol_info)
                        pass
        except:
            pass

    def refresh_symbol_info(self, symbol):
        """Refresh symbol info - COMPLETELY FIXED VERSION"""
        try:
            # Skip if recently updated
            if symbol in self.symbol_info:
                last_updated = self.symbol_info.get(symbol, {}).get("last_updated", 0)
                if time.time() - last_updated < 300:  # 5 minutes
                    return True
            
            print(f"🔄 Fetching fresh rules for {symbol}...")
            
            # Fetch exchange info
            url = f"{self.api_url}{self.api_prefix}/exchangeInfo"
            
            try:
                response = self.session.get(url, timeout=10)
                if response.status_code != 200:
                    print(f"❌ Failed to fetch exchange info: HTTP {response.status_code}")
                    return False
                
                data = response.json()
            except Exception as e:
                print(f"❌ Failed to fetch exchange info: {str(e)}")
                return False
            
            # Find the symbol
            found = False
            for sym_data in data.get("symbols", []):
                if sym_data.get("symbol") != symbol:
                    continue
                
                found = True
                
                # Parse filters
                filters = {}
                for f in sym_data.get("filters", []):
                    filters[f["filterType"]] = f
                
                # Get LOT_SIZE filter
                lot_size = filters.get("LOT_SIZE", {})
                step_size = float(lot_size.get("stepSize", 0.001))
                min_qty = float(lot_size.get("minQty", 0.001))
                
                # Get PRICE_FILTER
                price_filter = filters.get("PRICE_FILTER", {})
                tick_size = float(price_filter.get("tickSize", 0.001))
                
                # Get MIN_NOTIONAL
                notional_filter = filters.get("NOTIONAL", {})
                min_notional = float(notional_filter.get("minNotional", 20.0))
                
                # Calculate precision
                import math
                if step_size >= 1:
                    qty_precision = 0
                else:
                    qty_precision = int(round(-math.log10(step_size), 0))
                
                if tick_size >= 1:
                    price_precision = 0  
                else:
                    price_precision = int(round(-math.log10(tick_size), 0))
                
                # Store the info
                if symbol not in self.symbol_info:
                    self.symbol_info[symbol] = {}
                
                self.symbol_info[symbol].update({
                    "step_size": step_size,
                    "min_qty": min_qty,
                    "tick_size": tick_size,
                    "min_notional": min_notional,
                    "quantity_precision": qty_precision,
                    "price_precision": price_precision,
                    "last_updated": time.time()
                })
                
                print(f"   ✅ {symbol}: step={step_size}, qty_prec={qty_precision}, tick={tick_size}, price_prec={price_precision}")
                break
            
            if not found:
                print(f"   ⚠️ {symbol} not found - using defaults")
                # CORRECT defaults for common symbols
                defaults = {
                    "NEARUSDT": {"step": 0.1, "tick": 0.001},
                    "UNIUSDT": {"step": 0.01, "tick": 0.001},
                    "ADAUSDT": {"step": 1.0, "tick": 0.0001},
                    "HBARUSDT": {"step": 10.0, "tick": 0.00001},
                }
                
                if symbol in defaults:
                    step_size = defaults[symbol]["step"]
                    tick_size = defaults[symbol]["tick"]
                else:
                    step_size = 0.01
                    tick_size = 0.001
                
                import math
                qty_precision = 0 if step_size >= 1 else int(round(-math.log10(step_size), 0))
                price_precision = 0 if tick_size >= 1 else int(round(-math.log10(tick_size), 0))
                
                if symbol not in self.symbol_info:
                    self.symbol_info[symbol] = {}
                    
                self.symbol_info[symbol].update({
                    "step_size": step_size,
                    "min_qty": step_size,
                    "tick_size": tick_size,
                    "min_notional": 20.0,
                    "quantity_precision": qty_precision,
                    "price_precision": price_precision,
                    "last_updated": time.time()
                })
                
                print(f"   📌 Using defaults for {symbol}: step={step_size}, precision={qty_precision}")
            
            return True
            
        except Exception as e:
            print(f"🚨 Critical error in refresh_symbol_info: {str(e)}")
            import traceback
            traceback.print_exc()
            
            # Emergency defaults
            if symbol not in self.symbol_info:
                self.symbol_info[symbol] = {
                    "step_size": 0.01,
                    "min_qty": 0.01,
                    "tick_size": 0.001,
                    "min_notional": 20.0,
                    "quantity_precision": 2,
                    "price_precision": 3,
                    "last_updated": 0
                }
            return False
    
    def _format_quantity(self, symbol, quantity):
        """🔧 Format quantity using LIVE step size from exchange"""
        try:
            import math
            
            if quantity is None or quantity <= 0:
                return 0
            
            # Refresh symbol info if needed
            if symbol not in self.symbol_info:
                self.refresh_symbol_info(symbol)
            
            info = self.symbol_info.get(symbol, {})
            step_size = info.get("step_size", 1.0)
            
            if step_size <= 0:
                return 0
            
            # Calculate how many steps
            factor = 1 / step_size
            steps = math.floor(quantity * factor)
            formatted_quantity = steps * step_size
            
            # Calculate precision
            if step_size >= 1:
                precision = 0
            else:
                precision = int(round(-math.log10(step_size), 0))
            
            # Round to exact precision
            if precision == 0:
                formatted_quantity = float(int(formatted_quantity))
            else:
                formatted_quantity = round(formatted_quantity, precision)
            
            print(f"🔧 {symbol}: {quantity:.6f} -> {formatted_quantity} (step={step_size}, precision={precision})")
            
            return formatted_quantity
            
        except Exception as e:
            print(f"🚨 Error formatting quantity: {str(e)}")
            return 0

    def ensure_precision(self, symbol, price, qty):
        """🎯 Centralized precision validation for order placement"""
        try:
            symbol_info = self.symbol_info.get(symbol, {})
            if not symbol_info:
                # Refresh symbol info if missing
                self.refresh_symbol_info(symbol)
                symbol_info = self.symbol_info.get(symbol, {})
            
            # Get precision constraints
            step_size = float(symbol_info.get('step_size', 0.001))
            tick_size = float(symbol_info.get('tick_size', 0.01))
            min_qty = float(symbol_info.get('min_qty', 0.001))
            min_notional = float(symbol_info.get('min_notional', 10.0))
            
            # Format price and quantity
            formatted_price = self._format_price_with_tick_size(symbol, price)
            formatted_qty = self._format_quantity(symbol, qty)
            
            # Validate minimum quantity
            if formatted_qty < min_qty:
                formatted_qty = min_qty
                print(f"📈 Adjusted quantity to minimum: {formatted_qty}")
            
            # Validate minimum notional
            notional_value = formatted_price * formatted_qty
            if notional_value < min_notional:
                # Calculate required quantity
                required_qty = (min_notional * 1.1) / formatted_price
                formatted_qty = self._format_quantity(symbol, required_qty)
                notional_value = formatted_price * formatted_qty
                print(f"📈 Adjusted for minimum notional: {formatted_qty} = ${notional_value:.2f}")
            
            # Prepare notes
            notes = []
            if price != formatted_price:
                notes.append(f"Price adjusted: {price} → {formatted_price}")
            if qty != formatted_qty:
                notes.append(f"Quantity adjusted: {qty} → {formatted_qty}")
            
            return formatted_price, formatted_qty, notes
            
        except Exception as e:
            print(f"🚨 Error in precision validation: {str(e)}")
            return price, qty, [f"Validation error: {str(e)}"]
        
    def _format_price(self, symbol, price):
        """🔧 Format price according to exchange rules"""
        try:
            if price is None or price <= 0:
                return 0
                
            info = self.symbol_info.get(symbol, {})
            decimals = info.get("price_precision", 4)
            return round(price, decimals)
        except Exception as e:
            print(f"🚨 Error formatting price: {str(e)}")
            return price

    def _format_price_with_tick_size(self, symbol, price):
        """🔧 Format price to tick size requirements"""
        try:
            if price is None or price <= 0:
                return 0
                
            info = self.symbol_info.get(symbol, {})
            tick_size = info.get("tick_size", 0.0001)
            
            if tick_size == 0:
                # If no tick size info, use price precision
                decimals = info.get("price_precision", 4)
                return round(price, decimals)
            
            # Round to nearest tick size
            ticks = round(price / tick_size)
            formatted_price = ticks * tick_size
            
            # Ensure we don't have floating point precision issues
            if tick_size >= 1:
                return int(formatted_price)
            else:
                # Calculate decimal places from tick size
                decimal_str = f"{tick_size:.10f}".rstrip('0')
                if '.' in decimal_str:
                    decimals = len(decimal_str.split('.')[1])
                else:
                    decimals = 0
                
                return float(f"{formatted_price:.{decimals}f}")
                
        except Exception as e:
            print(f"🚨 Error formatting price with tick size: {str(e)}")
            return self._format_price(symbol, price)

    def _make_request(self, method, endpoint, params=None, signed=False):
        """📡 Make HTTP request to exchange with CIRCUIT BREAKER protection"""
        # Check circuit breaker first
        if self._check_circuit_breaker():
            return None
        
        # Rate limiting
        self._rate_limit()
        
        # Sign request if needed
        if signed:
            params = params or {}
            params['timestamp'] = self._get_timestamp()
            params['signature'] = self._generate_signature(params)
        
        url = self.api_url + endpoint
        
        try:
            # Make the request with better timeout handling
            timeout_seconds = 10
            
            if method == "GET":
                response = self.session.get(url, params=params, timeout=timeout_seconds)
            elif method == "POST":
                response = self.session.post(url, data=params, timeout=timeout_seconds)
            elif method == "DELETE":
                response = self.session.delete(url, params=params, timeout=timeout_seconds)
            else:
                raise ValueError(f"Unsupported method: {method}")
            
            # Handle response
            if response.status_code == 200:
                self._handle_api_success()  # Reset failure counter
                return response.json()
            else:
                # Handle errors
                self._handle_api_failure()  # Increment failure counter
                try:
                    error = response.json()
                    error_msg = error.get('msg', 'Unknown error')
                    error_code = error.get('code', 'N/A')
                    
                    # Log specific error codes
                    if error_code == -2022:
                        print(f"🚨 ReduceOnly order rejected - no position exists")
                    elif error_code == -2021:
                        print(f"🚨 Order would immediately trigger")
                    elif error_code == -2019:
                        print(f"🚨 Margin is insufficient")
                    elif error_code == -1111:
                        print(f"🚨 Precision error")
                        # Additional debug for precision error
                        if params:
                            print(f"   🔴 PRECISION ERROR DEBUG:")
                            print(f"      Symbol: {params.get('symbol', 'UNKNOWN')}")
                            if 'quantity' in params:
                                print(f"      Quantity sent: {params['quantity']}")
                                print(f"      Quantity type: {type(params['quantity'])}")
                                print(f"      Quantity repr: {repr(params['quantity'])}")
                            if 'price' in params:
                                print(f"      Price sent: {params['price']}")
                                print(f"      Price type: {type(params['price'])}")
                                print(f"      Price repr: {repr(params['price'])}")
                            # Try to get symbol info for comparison
                            symbol = params.get('symbol')
                            if symbol and hasattr(self, 'symbol_info'):
                                info = self.symbol_info.get(symbol, {})
                                if info:
                                    print(f"      Expected step_size: {info.get('step_size', 'N/A')}")
                                    print(f"      Expected tick_size: {info.get('tick_size', 'N/A')}")
                                    print(f"      Expected price_precision: {info.get('price_precision', 'N/A')}")
                                    print(f"      Expected quantity_precision: {info.get('quantity_precision', 'N/A')}")
                    else:
                        print(f"🚨 API Error [{error_code}]: {error_msg}")
                        
                except json.JSONDecodeError:
                    print(f"🚨 HTTP Error {response.status_code}")
                    print(f"   Response text: {response.text[:500]}")  # First 500 chars of response
                    
                return None
                
        except requests.exceptions.Timeout:
            self._handle_api_failure()
            print(f"🚨 Request timeout for {endpoint} after {timeout_seconds}s")
            return None
        except requests.exceptions.ConnectionError:
            self._handle_api_failure()
            print(f"🚨 Connection error for {endpoint}")
            return None
        except Exception as e:
            self._handle_api_failure()
            print(f"🚨 Request exception: {str(e)}")
            import traceback
            traceback.print_exc()
            return None
                
        except requests.exceptions.Timeout:
            self._handle_api_failure()
            print(f"🚨 Request timeout for {endpoint} after {timeout_seconds}s")
            return None
        except requests.exceptions.ConnectionError:
            self._handle_api_failure()
            print(f"🚨 Connection error for {endpoint}")
            return None
        except Exception as e:
            self._handle_api_failure()
            print(f"🚨 Request exception: {str(e)}")
            return None

    def _generate_signature(self, params):
        """🔐 Generate signature for authenticated requests"""
        query_string = urlencode(params)
        return hmac.new(
            self.api_secret.encode('utf-8'),
            query_string.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()

    def _get_timestamp(self):
        """⏰ Get current timestamp in milliseconds"""
        return int(time.time() * 1000)

    def _rate_limit(self):
        """⚡ Rate limiting"""
        current_time = time.time()
        elapsed = current_time - self.last_request_time
        if elapsed < self.min_request_interval:
            time.sleep(self.min_request_interval - elapsed)
        self.last_request_time = time.time()

    def track_order_lifecycle(self, symbol, client_order_id, oco_ids=None):
        """🎯 Explicit lifecycle guard to prevent order drift"""
        with self.lifecycle_lock:
            order_key = f"{symbol}_{client_order_id}"
            
            # Initialize order lifecycle
            if order_key not in self.order_lifecycle:
                self.order_lifecycle[order_key] = {
                    'symbol': symbol,
                    'client_order_id': client_order_id,
                    'oco_ids': oco_ids or {},
                    'state': 'PENDING',
                    'created_at': time.time(),
                    'last_update': time.time(),
                    'fill_price': None,
                    'fill_quantity': None,
                    'cancel_reason': None
                }
                print(f"🎯 Order lifecycle started: {symbol} {client_order_id}")
            
            return self.order_lifecycle[order_key]

    def update_order_lifecycle(self, symbol, client_order_id, new_state, **kwargs):
        """🔄 Update order lifecycle state"""
        with self.lifecycle_lock:
            order_key = f"{symbol}_{client_order_id}"
            
            if order_key in self.order_lifecycle:
                order = self.order_lifecycle[order_key]
                order['state'] = new_state
                order['last_update'] = time.time()
                
                # Update additional fields
                for key, value in kwargs.items():
                    order[key] = value
                
                print(f"🔄 Order lifecycle update: {symbol} {client_order_id} -> {new_state}")
                
                # Clean up completed orders after 1 hour
                if new_state in ['FILLED', 'CANCELLED', 'FAILED']:
                    if time.time() - order['created_at'] > 3600:  # 1 hour
                        del self.order_lifecycle[order_key]
                        print(f"🧹 Cleaned up completed order: {symbol} {client_order_id}")
                
                return order
            else:
                print(f"⚠️ Order lifecycle not found: {symbol} {client_order_id}")
                return None

    def get_order_lifecycle_state(self, symbol, client_order_id):
        """📊 Get current order lifecycle state"""
        with self.lifecycle_lock:
            order_key = f"{symbol}_{client_order_id}"
            return self.order_lifecycle.get(order_key, {}).get('state', 'UNKNOWN')

    def cleanup_orphaned_orders(self):
        """🧹 Clean up orphaned orders older than 24 hours"""
        with self.lifecycle_lock:
            current_time = time.time()
            orphaned = []
            
            for order_key, order in self.order_lifecycle.items():
                if current_time - order['created_at'] > 86400:  # 24 hours
                    orphaned.append(order_key)
            
            for order_key in orphaned:
                del self.order_lifecycle[order_key]
                print(f"🧹 Cleaned up orphaned order: {order_key}")
            
            if orphaned:
                print(f"🧹 Cleaned up {len(orphaned)} orphaned orders")


print("🌌 MODULAR MARKET INTERFACE READY! 🚀")
print(f"📈 Market: {'FUTURES' if config.ENABLE_FUTURES else 'SPOT'}")
print("🎯 Per Aspera Ad Astra!")