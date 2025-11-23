# ENCOM Repository Structure

## 📂 Complete Directory Layout

```
ENCOM/
├── README.md                           # Project overview & quick start
├── ROADMAP.md                          # Development roadmap (7 phases)
├── STRUCTURE.md                        # This file - repository structure
├── LICENSE                             # MIT License
├── requirements.txt                    # Python dependencies
├── encom_config_template.py            # Configuration template
├── .gitignore                          # Git ignore rules
│
├── encom/                              # Main package
│   ├── __init__.py                     # Package initialization
│   │
│   ├── core/                           # Core signal framework engine
│   │   ├── __init__.py
│   │   ├── signal_registry.py          # Signal base classes & registry
│   │   ├── confirmation_engine.py      # Confirmation layer logic
│   │   ├── filter_engine.py            # Quality filter system
│   │   ├── execution_engine.py         # Signal processing pipeline
│   │   ├── data_engine.py              # [Legacy - moved to data/]
│   │   ├── sim_engine.py               # [Legacy - to be refactored]
│   │   ├── event_engine.py             # [Legacy - to be refactored]
│   │   ├── order_sim.py                # Order execution simulation
│   │   └── portfolio_engine.py         # Portfolio management
│   │
│   ├── signals/                        # Signal implementations
│   │   ├── core_signals/               # Core wake-up signals
│   │   │   ├── __init__.py
│   │   │   ├── ma_crossover.py         # MA crossover signal (example)
│   │   │   ├── price_action.py         # [TODO] Breakouts, reversals
│   │   │   ├── technical.py            # [TODO] RSI, MACD, Bollinger
│   │   │   ├── volume.py               # [TODO] Volume spike signals
│   │   │   └── momentum.py             # [TODO] Momentum signals
│   │   ├── confirmations/              # Confirmation signals
│   │   │   ├── __init__.py
│   │   │   └── [TODO] Trend, volume, volatility confirmations
│   │   └── filters/                    # Quality filters
│   │       ├── __init__.py
│   │       ├── volume_filter.py        # Min volume filter (example)
│   │       └── [TODO] Spread, time, volatility filters
│   │
│   ├── data/                           # Data acquisition & management
│   │   ├── __init__.py
│   │   ├── data_pipeline.py            # Main data pipeline manager
│   │   ├── cache_manager.py            # [TODO] Advanced caching
│   │   └── providers/                  # Data provider implementations
│   │       ├── __init__.py
│   │       ├── yahoo_provider.py       # Yahoo Finance (FREE)
│   │       ├── polygon_provider.py     # Polygon.io (PAID)
│   │       └── alpaca_provider.py      # Alpaca Markets (FREE tier)
│   │
│   ├── analytics/                      # Performance analytics
│   │   ├── __init__.py
│   │   ├── metrics.py                  # [TODO] Performance calculations
│   │   ├── reports.py                  # [TODO] Visual reports
│   │   └── validators.py               # [TODO] Bias detection
│   │
│   ├── validation/                     # Validation & testing suite
│   │   ├── __init__.py
│   │   ├── walk_forward.py             # Walk-forward analysis
│   │   ├── monte_carlo.py              # Monte Carlo simulation (GBM)
│   │   └── robustness.py               # Robustness & sensitivity testing
│   │
│   ├── interface/                      # User interfaces
│   │   ├── __init__.py
│   │   ├── encom_cli.py                # CLI interface
│   │   ├── encom_config.py             # Configuration management
│   │   ├── asset_selector.py           # [TODO] Asset selection UI
│   │   ├── timeline_panel.py           # [TODO] Timeline configuration
│   │   ├── signal_builder_ui.py        # [TODO] Drag-drop signal builder
│   │   ├── filter_builder_ui.py        # [TODO] Drag-drop filter builder
│   │   ├── dashboard.py                # [TODO] Strategy dashboard
│   │   └── web_app/                    # Web-based interface
│   │       ├── frontend/               # [TODO] React frontend
│   │       └── backend/                # [TODO] FastAPI backend
│   │
│   ├── optimizer/                      # Parameter optimization
│   │   ├── __init__.py
│   │   ├── grid_search.py              # [TODO] Grid search optimizer
│   │   ├── genetic.py                  # [TODO] Genetic algorithm
│   │   └── bayesian.py                 # [TODO] Bayesian optimization
│   │
│   └── utils/                          # Utility functions
│       ├── __init__.py
│       ├── logging.py                  # [TODO] Logging utilities
│       └── helpers.py                  # [TODO] Helper functions
│
├── tests/                              # Unit tests
│   └── [TODO] Test files
│
├── data/                               # Cached historical data (gitignored)
│   └── *.parquet                       # Parquet cache files
│
├── logs/                               # Application logs (gitignored)
│   └── *.log
│
└── reports/                            # Generated reports (gitignored)
    └── *.xlsx, *.pdf, *.html
```

---

## 🎯 Module Responsibilities

### **Core Framework** (`encom/core/`)
- **signal_registry.py**: Base classes for signals, central signal registry
- **confirmation_engine.py**: Multi-layer confirmation logic (Layer 1 + Layer 2)
- **filter_engine.py**: Quality filter system (volume, spread, time, volatility)
- **execution_engine.py**: Signal processing pipeline (Core → Confirm → Filter → Entry)
- **order_sim.py**: Order execution simulation (slippage, commissions)
- **portfolio_engine.py**: Multi-position portfolio management

### **Signals** (`encom/signals/`)
- **core_signals/**: Wake-up triggers (MA cross, breakouts, RSI, MACD)
- **confirmations/**: Validation signals (trend, volume, volatility)
- **filters/**: Quality filters (min volume, bid-ask spread, time-of-day)

### **Data** (`encom/data/`)
- **data_pipeline.py**: Main data manager (fetch, cache, validate)
- **providers/**: Integration with Yahoo Finance, Polygon.io, Alpaca
- **Cache Flow**: API → Local Parquet → Backtest Engine

### **Validation** (`encom/validation/`)
- **walk_forward.py**: Rolling window optimization, in/out-of-sample testing
- **monte_carlo.py**: Trade shuffling, GBM simulation, confidence intervals
- **robustness.py**: Parameter sensitivity, bias detection, stress testing

### **Interface** (`encom/interface/`)
- **encom_cli.py**: Command-line interface
- **web_app/**: React frontend + FastAPI backend (drag-drop UI)
- **Panels**: Asset selector, timeline, signal builder, filter builder

### **Optimizer** (`encom/optimizer/`)
- Grid search, genetic algorithms, Bayesian optimization
- Multi-objective optimization (return vs risk)

---

## 🚀 Implementation Status

### ✅ **Completed (Phase 1 - Foundation)**
- Signal framework architecture (registry, base classes)
- Confirmation engine (multi-layer logic)
- Filter engine (quality filter system)
- Execution engine (signal processing pipeline)
- Data pipeline (fetch, cache, validate)
- Yahoo Finance provider (FREE, unlimited)
- Walk-forward analysis
- Monte Carlo simulation (GBM, trade shuffling)
- Robustness testing (sensitivity, bias detection)

### 🏗️ **In Progress**
- Example signals (MA crossover, volume filter)
- Order simulation (slippage, commissions)
- Portfolio manager

### 📋 **TODO (Phases 2-7)**
- Complete signal library (10+ core, 15+ confirmations, 20+ filters)
- Analytics & metrics (Sharpe, Sortino, drawdown)
- Visual reports (equity curves, heatmaps, Excel/PDF)
- Web-based drag-drop interface (React + FastAPI)
- Parameter optimization (grid search, genetic)
- Multi-asset backtesting (50+ stocks simultaneously)

---

## 📊 Data Flow Architecture

```
User Input (Asset + Timeline + Signals + Filters)
    ↓
Data Pipeline → Check Cache → Fetch if Missing → Save to Parquet
    ↓
Signal Execution Engine (Bar-by-Bar)
    ↓
Core Signal Evaluation → Confirmation Layers → Quality Filters
    ↓
Entry Decision → Order Simulation → Portfolio Update
    ↓
Performance Analytics → Walk-Forward → Monte Carlo
    ↓
Reports & Visualization (Equity Curve, Metrics, Excel)
```

---

## 🔧 Key Design Patterns

1. **Signal Framework**: Core → Confirm 1 → Confirm 2 → Filters
2. **Modular Signals**: Drag-drop, plug-and-play signal library
3. **Data Caching**: First run fetches, subsequent runs use cache
4. **Validation-First**: Walk-forward + Monte Carlo mandatory
5. **Asset Agnostic**: Same engine for stocks, crypto, futures, forex

---

## 📝 Quick Reference

| Task | Module | Status |
|------|--------|--------|
| Add new core signal | `encom/signals/core_signals/` | ✅ Ready |
| Add confirmation | `encom/signals/confirmations/` | ✅ Ready |
| Add quality filter | `encom/signals/filters/` | ✅ Ready |
| Fetch historical data | `encom/data/data_pipeline.py` | ✅ Ready |
| Add data provider | `encom/data/providers/` | 🏗️ Yahoo done |
| Run walk-forward | `encom/validation/walk_forward.py` | ✅ Ready |
| Run Monte Carlo | `encom/validation/monte_carlo.py` | ✅ Ready |
| Optimize parameters | `encom/optimizer/` | 📋 TODO |
| Generate reports | `encom/analytics/reports.py` | 📋 TODO |

---

**ENCOM**: *Signal-based strategy development, visually designed, mathematically validated.*

**End of Line.** 🎮
