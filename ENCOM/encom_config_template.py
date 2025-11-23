"""
ENCOM Configuration Template
Copy this file to encom_config.py and customize your settings
"""

# ============================================================================
# BACKTEST SETTINGS
# ============================================================================

# Initial capital for backtesting
INITIAL_CAPITAL = 10000.0

# Commission rates
COMMISSION_RATE_SPOT = 0.001      # 0.1% for spot trading
COMMISSION_RATE_FUTURES = 0.0004  # 0.04% for futures trading

# Slippage modeling
SLIPPAGE_PCT = 0.0005  # 0.05% average slippage
SLIPPAGE_MODEL = "percentage"  # Options: "percentage", "fixed", "volume_based"

# ============================================================================
# DATA SETTINGS
# ============================================================================

# Data cache directory
DATA_CACHE_DIR = "./data"

# Default timeframe
TIMEFRAME = "15m"  # Options: 1m, 5m, 15m, 1h, 4h, 1d

# Symbols to backtest
SYMBOLS = [
    "BTCUSDT",
    "ETHUSDT",
    "BNBUSDT",
]

# Data source
DATA_SOURCE = "binance"  # Options: "binance", "csv", "database"

# Update cache automatically
AUTO_UPDATE_CACHE = True

# ============================================================================
# SIMULATION SETTINGS
# ============================================================================

# Order execution delays (seconds)
ORDER_LATENCY = 0.1

# Limit order fill logic
LIMIT_ORDER_FILL_STRATEGY = "conservative"  # Options: "conservative", "aggressive", "realistic"

# Market impact modeling
ENABLE_MARKET_IMPACT = False
MARKET_IMPACT_COEFFICIENT = 0.001

# Position limits (same as Tron 7)
MAX_TOTAL_POSITIONS = 3
MAX_POSITIONS_PER_SYMBOL = 1

# ============================================================================
# OPTIMIZATION SETTINGS
# ============================================================================

# Parallel processing
OPTIMIZATION_CORES = 4  # Number of CPU cores to use

# Walk-forward analysis
WALK_FORWARD_PERIODS = 6  # Number of periods for walk-forward
WALK_FORWARD_TRAIN_PCT = 0.7  # 70% train, 30% test

# Monte Carlo simulation
MONTE_CARLO_RUNS = 1000
MONTE_CARLO_CONFIDENCE_LEVEL = 0.95

# Grid search
MAX_COMBINATIONS = 10000  # Limit to prevent excessive computation

# ============================================================================
# REPORTING SETTINGS
# ============================================================================

# Output directory
REPORTS_DIR = "./reports"

# Report formats
GENERATE_EXCEL = True
GENERATE_PDF = False
GENERATE_HTML = True

# Chart settings
CHART_STYLE = "dark"  # Options: "dark", "light", "seaborn"
CHART_DPI = 150

# Metrics to display
CORE_METRICS = [
    "total_return",
    "sharpe_ratio",
    "max_drawdown",
    "win_rate",
    "profit_factor",
]

# ============================================================================
# VALIDATION SETTINGS
# ============================================================================

# Bias detection
ENABLE_LOOKAHEAD_CHECK = True
ENABLE_SURVIVORSHIP_CHECK = True
ENABLE_OVERFITTING_CHECK = True

# Minimum data requirements
MIN_TRADES_REQUIRED = 30
MIN_DATA_DAYS = 90

# ============================================================================
# LOGGING SETTINGS
# ============================================================================

# Log level
LOG_LEVEL = "INFO"  # Options: DEBUG, INFO, WARNING, ERROR

# Log directory
LOG_DIR = "./logs"

# Detailed trade logging
LOG_ALL_ORDERS = True
LOG_BAR_DATA = False  # Warning: generates large logs

# ============================================================================
# TRON 7 INTEGRATION
# ============================================================================

# Path to Tron 7 strategies
TRON7_STRATEGY_PATH = "../Tron-7-modular-/strategy (modular).py"

# Tron 7 config path
TRON7_CONFIG_PATH = "../Tron-7-modular-/config (modular).py"

# Strategy class name
STRATEGY_CLASS = "BaseStrategy"  # Change to your strategy name

# ============================================================================
# ADVANCED SETTINGS
# ============================================================================

# Benchmark symbol
BENCHMARK_SYMBOL = "BTCUSDT"

# Risk-free rate for Sharpe calculation
RISK_FREE_RATE = 0.02  # 2% annual

# Trading session filters
ENABLE_SESSION_FILTER = False
TRADING_SESSIONS = {
    "start_hour": 0,
    "end_hour": 24,
    "days": [0, 1, 2, 3, 4, 5, 6],  # Monday = 0, Sunday = 6
}

# Memory management
MAX_MEMORY_USAGE_MB = 2048
ENABLE_DATA_STREAMING = True  # For large datasets

# ============================================================================
# EXPERIMENTAL FEATURES
# ============================================================================

# Enable multi-strategy portfolio backtesting
ENABLE_PORTFOLIO_MODE = False

# Enable real-time paper trading mode
ENABLE_PAPER_TRADING = False

# Enable strategy correlation analysis
ENABLE_CORRELATION_ANALYSIS = False
