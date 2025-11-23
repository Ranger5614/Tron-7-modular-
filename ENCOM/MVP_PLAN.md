# 🎯 ENCOM MVP - Development Plan

## Goal
Build a working backtesting engine that can test a simple strategy on real stock data in <200 lines of core code.

---

## MVP Scope (Phase 0)

### **What's IN**
- ✅ Yahoo Finance data fetching + caching
- ✅ Signal framework (1 core signal, 1 filter)
- ✅ Bar-by-bar backtesting engine
- ✅ Simple portfolio tracker (cash + positions)
- ✅ Basic metrics (total return, win rate, max drawdown, # trades)
- ✅ CLI to run backtest

### **What's OUT** (Future phases)
- ❌ Walk-forward analysis
- ❌ Monte Carlo simulation
- ❌ Multiple confirmations
- ❌ Visual charts
- ❌ Excel reports
- ❌ Web interface
- ❌ Parameter optimization

---

## Architecture (Inspired by Tron 7)

```
encom/
├── engine/                  # Core backtesting engine
│   ├── backtest_engine.py   # Main orchestrator (bar-by-bar loop)
│   ├── portfolio.py         # Position & cash tracking
│   └── metrics.py           # Performance calculations
├── core/                    # Signal framework (already done)
├── data/                    # Data pipeline (already done)
├── signals/                 # Signal library (already done)
└── run_backtest.py          # CLI entry point
```

---

## Implementation Steps

### **Step 1: Portfolio Tracker** (50 lines)
- Track cash balance
- Track open positions
- Calculate P&L
- Record trades

### **Step 2: Backtesting Engine** (100 lines)
- Load data
- Bar-by-bar loop
- Signal evaluation (core → filter → entry)
- Order execution (market orders only)
- Exit management (simple stop-loss/take-profit)
- Call portfolio tracker

### **Step 3: Metrics Calculator** (50 lines)
- Total return
- Win rate
- Max drawdown
- Number of trades
- Average win/loss

### **Step 4: CLI Runner** (30 lines)
- Parse arguments (symbol, dates, strategy)
- Initialize components
- Run backtest
- Print results

### **Step 5: Example Strategy** (20 lines)
- MA Crossover signal (already done)
- Volume filter (already done)
- Combine into complete strategy

### **Step 6: Test** (10 minutes)
- Run backtest on AAPL 2024
- Verify results make sense
- Check all metrics calculate correctly

---

## Success Criteria

```bash
$ python run_backtest.py AAPL 2024-01-01 2024-12-31

Fetching data for AAPL...
Running backtest...
==================================
BACKTEST RESULTS
==================================
Symbol: AAPL
Period: 2024-01-01 to 2024-12-31
Strategy: MA Crossover (20/50)

Performance:
  Total Return: +15.3%
  Win Rate: 62.5%
  Max Drawdown: -8.2%
  Total Trades: 8
  Avg Win: +5.2%
  Avg Loss: -2.1%

End of Line.
```

---

## Timeline

- **Step 1-2**: Portfolio + Engine (~1 hour)
- **Step 3-4**: Metrics + CLI (~30 min)
- **Step 5-6**: Strategy + Test (~20 min)

**Total**: ~2 hours for complete MVP

---

## Code Quality Standards

1. **Clean**: No bloat, no unnecessary abstractions
2. **Modular**: Each file has ONE clear purpose
3. **Testable**: Can run end-to-end in one command
4. **Documented**: Docstrings on all classes/methods
5. **Extensible**: Easy to add signals, metrics, features later

---

**Let's build.** 🎮
