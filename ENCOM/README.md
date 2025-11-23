# 🎮 ENCOM - Enhanced Network Command

**Professional-grade backtesting engine for Tron 7 trading strategies**

[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

---

## 🎯 Mission

ENCOM is a modular backtesting companion for [Tron 7](https://github.com/Ranger5614/Tron-7-modular-) designed to validate trading strategies, analyze risk metrics, and optimize performance before live deployment.

**Key Philosophy**: *Where strategies are forged, tested, and proven before battle.*

---

## ✨ Features

### 🏗️ Core Engine
- **Historical Data Management** - Fetch and cache Binance OHLCV data
- **Event-Driven Simulation** - Bar-by-bar playback with lookahead bias prevention
- **Realistic Order Execution** - Market/limit orders with slippage and commission modeling
- **OCO Order Simulation** - Full take-profit / stop-loss mechanics

### 🔌 Tron 7 Integration
- **Strategy Bridge** - Import and test Tron 7 strategies directly
- **Configuration Sync** - Seamless parameter and config compatibility
- **Position Sizing** - Identical risk management rules
- **Multi-Symbol Support** - Test on any number of trading pairs

### 📊 Analytics & Metrics
- **Performance Metrics** - Returns, Sharpe Ratio, Max Drawdown, Win Rate
- **Risk Analytics** - Sortino Ratio, VaR, MAE/MFE, Tail Risk
- **Visualization** - Equity curves, drawdown charts, trade distributions
- **Detailed Reports** - Excel exports, PDF summaries, trade logs

### 🚀 Optimization Suite
- **Grid Search** - Multi-parameter optimization with parallel processing
- **Walk-Forward Analysis** - Out-of-sample validation
- **Monte Carlo Simulation** - Confidence intervals and worst-case scenarios
- **Overfitting Detection** - Train/test splits, stability scoring

### 🛡️ Validation & Quality
- **Bias Detection** - Lookahead, survivorship, data snooping checks
- **Sanity Checks** - Realistic fills, proper slippage, accurate commissions
- **Benchmarking** - Compare against buy-and-hold and market indices

---

## 🚀 Quick Start

### Installation

```bash
# Clone the repository
git clone https://github.com/Ranger5614/ENCOM.git
cd ENCOM

# Install dependencies
pip install -r requirements.txt

# Configure settings
cp encom_config_template.py encom_config.py
# Edit encom_config.py with your settings
```

### Basic Usage

```bash
# Run a backtest
python -m encom.interface.encom_cli run MyStrategy --start 2024-01-01 --end 2024-12-31

# Optimize strategy parameters
python -m encom.interface.encom_cli optimize MyStrategy --params params.json

# Compare multiple strategies
python -m encom.interface.encom_cli compare Strategy1 Strategy2

# Generate report
python -m encom.interface.encom_cli report backtest_20241123_123456
```

---

## 📦 Project Structure

```
ENCOM/
├── encom/
│   ├── core/
│   │   ├── data_engine.py          # Historical data fetching & caching
│   │   ├── sim_engine.py           # Order/position simulation
│   │   └── event_engine.py         # Event-driven backtest loop
│   ├── integration/
│   │   ├── strategy_bridge.py      # Tron 7 strategy adapter
│   │   └── portfolio_sim.py        # Virtual portfolio management
│   ├── analytics/
│   │   ├── metrics.py              # Performance calculations
│   │   ├── reports.py              # Visualization & exports
│   │   └── validators.py           # Bias detection
│   ├── optimization/
│   │   ├── optimizer.py            # Parameter optimization
│   │   ├── monte_carlo.py          # Monte Carlo simulation
│   │   └── benchmark.py            # Strategy comparison
│   ├── interface/
│   │   ├── encom_cli.py            # Command-line interface
│   │   └── encom_config.py         # Configuration management
│   └── utils/
│       ├── logging.py              # Logging utilities
│       └── helpers.py              # Helper functions
├── tests/                          # Unit tests
├── data/                           # Cached historical data
├── logs/                           # Backtest logs
├── reports/                        # Generated reports
├── ROADMAP.md                      # Development roadmap
├── requirements.txt                # Python dependencies
└── README.md                       # This file
```

---

## 🎓 Example: Testing a Tron 7 Strategy

```python
from encom.interface.encom_cli import BacktestRunner
from tron7.strategy import MyCustomStrategy

# Initialize backtest
runner = BacktestRunner(
    strategy=MyCustomStrategy(),
    symbols=['BTCUSDT', 'ETHUSDT'],
    start_date='2024-01-01',
    end_date='2024-12-31',
    initial_capital=10000,
    timeframe='15m'
)

# Run backtest
results = runner.run()

# Print metrics
print(f"Total Return: {results.total_return:.2%}")
print(f"Sharpe Ratio: {results.sharpe_ratio:.2f}")
print(f"Max Drawdown: {results.max_drawdown:.2%}")
print(f"Win Rate: {results.win_rate:.2%}")

# Generate report
results.export_excel('backtest_report.xlsx')
results.plot_equity_curve()
```

---

## 🔧 Configuration

Edit `encom_config.py` to customize:

```python
# Backtest settings
INITIAL_CAPITAL = 10000
COMMISSION_RATE = 0.0004  # 0.04% for futures
SLIPPAGE_PCT = 0.0005     # 0.05% slippage

# Data settings
DATA_CACHE_DIR = './data'
TIMEFRAME = '15m'
SYMBOLS = ['BTCUSDT', 'ETHUSDT', 'BNBUSDT']

# Optimization settings
OPTIMIZATION_CORES = 4
WALK_FORWARD_PERIODS = 6
MONTE_CARLO_RUNS = 1000
```

---

## 📈 Performance Metrics

ENCOM calculates comprehensive metrics:

| Category | Metrics |
|----------|---------|
| **Returns** | Total Return, CAGR, Monthly/Yearly Returns |
| **Risk** | Sharpe Ratio, Sortino Ratio, Calmar Ratio, VaR |
| **Drawdown** | Max Drawdown, Avg Drawdown, Recovery Time |
| **Trade Stats** | Win Rate, Profit Factor, Avg Win/Loss, R-Multiple |
| **Advanced** | MAE/MFE, Tail Risk, Trade Duration, Symbol Performance |

---

## 🛣️ Development Roadmap

See [ROADMAP.md](ROADMAP.md) for detailed development phases.

**Current Status**: 🏗️ Phase 1 - Core Engine Foundation

**Next Milestone**: MVP Release (Data Engine + Simulation + Basic Metrics)

---

## 🤝 Integration with Tron 7

ENCOM is designed as a companion to [Tron 7](https://github.com/Ranger5614/Tron-7-modular-):

1. **Strategy Compatibility** - Import any Tron 7 `BaseStrategy` implementation
2. **Config Sync** - Use Tron 7 config files directly
3. **Validation Workflow** - Test → Optimize → Validate → Deploy
4. **Paper Trading** - Bridge to live simulation before real trading

---

## 📚 Documentation

- [Roadmap](ROADMAP.md) - Development phases and milestones
- [Architecture](docs/architecture.md) - System design overview *(coming soon)*
- [API Reference](docs/api.md) - Module documentation *(coming soon)*
- [Examples](examples/) - Sample backtests and strategies *(coming soon)*

---

## 🧪 Testing

```bash
# Run all tests
pytest tests/

# Run specific test suite
pytest tests/test_sim_engine.py

# Run with coverage
pytest --cov=encom tests/
```

---

## 🚦 Requirements

- Python 3.8+
- pandas, numpy, scipy
- matplotlib / plotly
- ccxt or binance-python
- openpyxl (for Excel exports)
- joblib (for parallel processing)

See `requirements.txt` for full dependencies.

---

## 📝 License

MIT License - See [LICENSE](LICENSE) for details.

---

## 🌟 Credits

Built as a companion to **Tron 7** - Modular Trading Bot by Ranger5614

*Per Aspera Ad Astra* 🚀

**End of Line.** 🎮
