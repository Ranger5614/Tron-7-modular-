# config.py - MODULAR VERSION
"""
🚀 MODULAR TRADING BOT CONFIGURATION 🚀
Universal configuration file for strategy-agnostic trading
Change STRATEGY_CLASS to switch strategies!
Per Aspera Ad Astra
"""

import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# 🎯 STRATEGY SELECTION - CHANGE THIS TO SWITCH STRATEGIES!
STRATEGY_CLASS = "YourStrategyNameHere"  # Name of the strategy class to use

# 🛰️ API Configuration - SECURE VERSION
BINANCE_API_KEY = os.getenv('BINANCE_API_KEY', '')
BINANCE_API_SECRET = os.getenv('BINANCE_API_SECRET', '')
DISCORD_WEBHOOK = os.getenv('DISCORD_WEBHOOK', '')

# Validate that credentials are set
if not BINANCE_API_KEY or not BINANCE_API_SECRET:
    raise ValueError("❌ CRITICAL: Binance API credentials not found in environment variables!")
    
if not DISCORD_WEBHOOK:
    print("⚠️ WARNING: Discord webhook not found - notifications will be disabled")

# 🧪 OPERATIONAL MODES
DRY_RUN_MODE = False                      # Set to True for testing without real trades
VERBOSE_LOGGING = True                    # Set to True for detailed logging
USE_TESTNET = False                       # Set to True for testnet mode (spot trading)

# 🚀 FUTURES TRADING CONFIGURATION
ENABLE_FUTURES = True                     # Master switch for futures trading
FUTURES_TESTNET = False                   # False = real futures trading
LEVERAGE = 1                              # Leverage multiplier
MARGIN_TYPE = "USDT"                      # USDT-margined futures
POSITION_MODE = "ONE_WAY"                 # Simple one-way mode
ISOLATED_MARGIN = False                   # Use cross margin for better flexibility

# 💰 POSITION SIZING
FIXED_POSITION_SIZE_USD = 20.0            # Fixed position size in USD
MAX_TOTAL_POSITIONS = 3                   # Maximum concurrent positions
MIN_ORDER_VALUE_USD = 20.0                # Minimum order value

# 🎯 RISK MANAGEMENT - UNIVERSAL PARAMETERS
MAX_LEVERAGE = 1                          # Maximum allowed leverage
MIN_MARGIN_RATIO = 0.20                   # Maintain 20% margin minimum
MARGIN_CALL_THRESHOLD = 0.25              # Margin call warning at 25%
DAILY_LOSS_LIMIT_PERCENT = 10.0           # Stop at 10% daily loss
MAX_HOLD_BARS = 100                       # Exit after N bars (strategy can override)

# 🎯 EXIT CONFIGURATION - UNIVERSAL DEFAULTS
USE_DYNAMIC_EXITS = False                 # Use fixed TP/SL by default
FIXED_TP_PCT = 0.015                      # 1.5% take profit (strategy can override)
FIXED_SL_PCT = 0.006                      # 0.6% stop loss (strategy can override)
RISK_REWARD_RATIO = 2.5                   # Target risk/reward ratio

# 📊 ORDER EXECUTION SETTINGS
USE_LIMIT_ORDERS = True                   # Use limit orders for entries
USE_REDUCE_ONLY = True                    # Always reduce-only for exits
POST_ONLY_ENTRIES = False                 # Market orders for fast fills
AUTO_PLACE_EXIT_ORDERS = True             # Auto place TP/SL orders
ORDER_FILL_TIMEOUT = 300                  # Cancel unfilled orders after 5 minutes

# 🔄 ENHANCED ORDER MANAGEMENT
USE_OCO_ORDERS = True                     # Use OCO (One-Cancels-Other) for TP/SL
ORDER_RETRY_ATTEMPTS = 3                  # Number of retry attempts for failed orders
ORDER_RETRY_DELAY = 2                     # Initial delay between retries (seconds)
ORDER_RETRY_BACKOFF = 1.5                 # Exponential backoff multiplier
PARTIAL_FILL_TIMEOUT = 30                 # Wait time for partial fills (seconds)
EXIT_ORDER_VERIFY_DELAY = 1               # Delay after placing exit orders (seconds)
MAX_ORDER_AGE_SECONDS = 10                # Consider orders stale after this time

# OCO Timing Improvements - ENHANCED FOR PERFORMANCE
OCO_VERIFICATION_DELAY = 2        # Reduced from 3s to 2s for faster execution
OCO_PLACEMENT_RETRIES = 5         # Increased from 3 to 5 for better reliability
OCO_MONITOR_INTERVAL = 2          # Reduced from 3s to 2s for faster monitoring
EXIT_ORDER_VERIFY_DELAY = 1       # Reduced from 2s to 1s for faster verification

# ENHANCED: Order Status Cache Settings
ORDER_STATUS_CACHE_TIME = 0.5     # Reduced from 2s to 0.5s for fresh data
CACHE_CLEANUP_INTERVAL = 30       # Cleanup every 30s instead of 60s

# ENHANCED: Duplicate Alert Windows
DUPLICATE_WINDOW_EXIT = 10        # 10s for exit notifications (was 60s)
DUPLICATE_WINDOW_ENTRY = 30       # 30s for entry notifications
DUPLICATE_WINDOW_STATUS = 60      # 60s for status updates

# ENHANCED: Position Sync Intervals (single source of truth)
POSITION_SYNC_INTERVAL = 15       # Reduced from 30s to 15s
RECONCILIATION_INTERVAL = 30      # Reduced from 60s to 30s
VERIFY_POSITION_BEFORE_ENTRY = True       # Always verify no position exists before entry
FORCE_POSITION_SYNC_ON_ERROR = True       # Force sync when errors occur
POSITION_VERIFICATION_RETRIES = 3         # Retries for position verification

# 🛡️ EXIT ORDER MANAGEMENT (align with enhanced values above)
OCO_PLACEMENT_RETRIES = max(OCO_PLACEMENT_RETRIES, 5)
OCO_VERIFICATION_DELAY = max(OCO_VERIFICATION_DELAY, 2)
EXIT_ORDER_CHECK_INTERVAL = 30
AUTO_REPAIR_EXIT_ORDERS = True
EXIT_ORDER_REPAIR_DELAY = 5

# 🌌 PAIR CONFIGURATIONS - UNIVERSAL FORMAT
# Configure your trading pairs below
# Each pair can override the default TP/SL percentages if needed
PAIR_CONFIGS = {
    # Add your trading pairs here
    # Example format:
    # "BTCUSDT": {
    #     "active": True,                    # Enable/disable this pair
    #     "priority": 1,                     # Priority for signal processing
    #     "min_volume_usd": 100000000,       # Minimum 24h volume in USD
    #     "cooldown_minutes": 0,             # Cooldown between trades (minutes)
    #     "tp_pct": 0.015,                   # Override FIXED_TP_PCT for this pair
    #     "sl_pct": 0.006,                   # Override FIXED_SL_PCT for this pair
    #     "use_dynamic_tp": False,           # Use dynamic TP (strategy-specific)
    #     "max_positions": 1                 # Max concurrent positions for this pair
    # },
    # "ETHUSDT": {
    #     "active": True,
    #     "priority": 2,
    #     "min_volume_usd": 50000000,
    #     "cooldown_minutes": 0,
    #     "tp_pct": 0.015,
    #     "sl_pct": 0.006,
    #     "use_dynamic_tp": False,
    #     "max_positions": 1
    # },
    # Add more pairs as needed...
}

# 🚀 OPERATIONAL PARAMETERS
TIMEFRAME = "15m"                         # Timeframe for candles
LOOKBACK_CANDLES = 100                    # Candles for indicators (strategy can override)
MAIN_LOOP_INTERVAL = 20                   # Main loop interval (seconds)
POSITION_MONITOR_INTERVAL = 15            # Position monitoring interval
HEARTBEAT_INTERVAL = 600                  # Discord heartbeat (10 min)

# 📡 LIVE PRICE MONITORING (Optional - strategies can use this)
LIVE_PRICE_CHECK_INTERVAL = 5             # Seconds between live price checks
LIVE_PRICE_API_LIMIT = 10                 # Max symbols to check per cycle
ENABLE_FAST_ENTRY = False                 # Use live price monitoring (strategy-specific)

# 🛡️ EMERGENCY PROTOCOLS
CONSECUTIVE_LOSS_LIMIT = 3                # Stop after N consecutive losses
MIN_BALANCE_USD = 100.0                   # Minimum balance to trade
LONG_ONLY_MODE = False                    # Allow both LONG and SHORT
EMERGENCY_LOSS_PERCENT = 2.0              # Force close at -X% loss
ZOMBIE_CHECK_BARS = 1                     # Consider position zombie after N bars
SUSTAINED_LOSS_BARS = 2                   # Bars in loss before emergency close
SUSTAINED_LOSS_THRESHOLD = 0.3            # -X% sustained loss threshold

# 📁 FILE PATHS
DATA_DIR = "trading_data"
LOG_DIR = "trading_logs"
POSITIONS_FILE = f"{DATA_DIR}/positions.json"
TRADES_LOG_FILE = f"{LOG_DIR}/trades.log"
HYPERION_LOG_FILE = f"{LOG_DIR}/trading_bot.log"

# ⚡ EXCHANGE SETTINGS
EXCHANGE = "binance"
MARKET_TYPE = "futures" if ENABLE_FUTURES else "spot"
CONNECTION_TIMEOUT = 30
MAX_RETRY_ATTEMPTS = 3
RETRY_DELAY = 2
RATE_LIMIT_DELAY = 0.1

# Order Management - NON-BLOCKING
MONITOR_ORDERS_INTERVAL = 10              # Check unfilled orders every 10 seconds
NON_BLOCKING_ORDERS = True                # Enable non-blocking order management

# ===== LIVE PRICE MONITORING PARAMETERS =====
LIVE_PRICE_CHECK_INTERVAL = 5             # Check live prices every 5 seconds
LIVE_PRICE_API_LIMIT = 10                 # Max symbols per live check
ENTRY_TYPE_LOGGING = True                 # Log entry type performance
LIVE_PRICE_SYMBOLS_LIMIT = 5              # Max symbols to check live

# ===== PERFORMANCE OPTIMIZATIONS =====
ENABLE_POSITION_CACHE = True              # Cache position checks
POSITION_CACHE_TTL = 30                   # Cache time-to-live in seconds
ENABLE_PERFORMANCE_MODE = True            # Master switch for all optimizations
MAX_API_CALLS_PER_SECOND = 10            # Rate limiting
MAX_SLIPPAGE_PERCENT = 0.2                # Max acceptable slippage (0.2%)

# 📡 NOTIFICATION SETTINGS
ENABLE_DISCORD = True                     # Enable Discord notifications
ENABLE_CONSOLE = True                     # Enable console output
ENABLE_FILE_LOGGING = True                # Enable file logging

# 📊 PERFORMANCE TRACKING
TARGET_WIN_RATE = 60.0                    # Target win rate percentage
TARGET_PROFIT_FACTOR = 1.5                # Target profit factor
DEBUG_MODE = False                        # Set to True for debug output

# Create directories if they don't exist
os.makedirs(DATA_DIR, exist_ok=True)
os.makedirs(LOG_DIR, exist_ok=True)

print("🚀 MODULAR TRADING BOT CONFIG LOADED!")
print(f"🎯 Strategy: {STRATEGY_CLASS}")
print(f"📈 Mode: {'FUTURES' if ENABLE_FUTURES else 'SPOT'} | Leverage: {LEVERAGE}x")
print(f"💰 Position Size: ${FIXED_POSITION_SIZE_USD} | Max Positions: {MAX_TOTAL_POSITIONS}")
print(f"🎯 Active Pairs: {sum(1 for p in PAIR_CONFIGS.values() if p.get('active', False))}")
print("=" * 60)

# Strategy-specific configuration notice
print("📦 STRATEGY CONFIGURATION:")
print(f"   Using strategy class: {STRATEGY_CLASS}")
print("   Add strategy-specific parameters below this section")
print("=" * 60)

# ===== STRATEGY-SPECIFIC PARAMETERS =====
# Add your strategy-specific parameters here
# These will be used by your custom strategy implementation
# 
# NAMING CONVENTION: Use UPPERCASE for all parameters
# Your strategy can access these via: config.PARAMETER_NAME
# 
# Examples for different strategy types:
#
# === Moving Average Strategy ===
# MA_FAST_PERIOD = 10                      # Fast MA period
# MA_SLOW_PERIOD = 20                      # Slow MA period
# MA_TYPE = "EMA"                          # MA type: "SMA" or "EMA"
#
# === RSI Strategy ===
# RSI_PERIOD = 14                          # RSI calculation period
# RSI_OVERSOLD = 30                        # Oversold threshold
# RSI_OVERBOUGHT = 70                      # Overbought threshold
#
# === Bollinger Band Strategy ===
# BB_PERIOD = 20                           # Bollinger band period
# BB_STD_DEV = 2.0                         # Standard deviations
# BB_SQUEEZE_THRESHOLD = 0.01              # Squeeze detection threshold
#
# === Custom ML Strategy ===
# MODEL_PATH = "models/my_model.pkl"       # Path to trained model
# FEATURE_LOOKBACK = 50                    # Lookback for features
# PREDICTION_THRESHOLD = 0.7               # Minimum confidence
#
# === Your Strategy Parameters Go Here ===


# ===== END STRATEGY-SPECIFIC PARAMETERS =====

print("✅ Configuration loaded successfully!")
print("📝 Remember to:")
print("   1. Set STRATEGY_CLASS to your strategy class name")
print("   2. Add your strategy parameters in the section above")
print("   3. Configure PAIR_CONFIGS with your trading pairs")
print("🚀 Per Aspera Ad Astra!")