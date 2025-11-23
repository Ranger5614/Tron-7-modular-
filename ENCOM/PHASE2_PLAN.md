# 🎯 ENCOM Phase 2 - Build Plan

## Goal
Expand signal library, add advanced metrics, create strategy templates - all lean & mean.

---

## File Structure (Complete)

```
encom/
├── core/                           # ✅ Signal framework (DONE)
│   ├── signal_registry.py
│   ├── confirmation_engine.py
│   ├── filter_engine.py
│   └── execution_engine.py
│
├── signals/                        # 🔨 BUILD THIS
│   ├── core_signals/              # Entry signals (wake-up)
│   │   ├── ma_crossover.py        ✅ DONE
│   │   ├── rsi_signal.py          🆕 RSI overbought/oversold
│   │   ├── macd_signal.py         🆕 MACD histogram
│   │   ├── bollinger_signal.py    🆕 Bollinger breakout
│   │   ├── breakout_signal.py     🆕 Price breakout
│   │   └── volume_spike.py        🆕 Volume spike
│   │
│   ├── confirmations/             # Confirmation signals
│   │   ├── trend_confirmation.py  🆕 ADX, MA slope
│   │   ├── volume_confirmation.py 🆕 OBV, volume trend
│   │   └── volatility_confirmation.py 🆕 ATR expansion
│   │
│   └── filters/                   # Quality filters
│       ├── volume_filter.py       ✅ DONE
│       ├── spread_filter.py       🆕 Bid-ask spread
│       ├── time_filter.py         🆕 Time of day
│       └── volatility_filter.py   🆕 ATR threshold
│
├── engine/                         # ✅ Core engine (DONE)
│   ├── portfolio.py
│   ├── metrics.py                 🔨 ENHANCE (Sharpe, Sortino)
│   ├── backtest_engine.py
│   └── __init__.py
│
├── strategies/                     # 🆕 NEW - Strategy templates
│   ├── base_strategy.py           🆕 Strategy base class
│   ├── ma_crossover_strategy.py   🆕 Complete MA strategy
│   ├── rsi_strategy.py            🆕 RSI mean reversion
│   ├── breakout_strategy.py       🆕 Breakout strategy
│   └── __init__.py
│
├── analytics/                      # 🔨 BUILD THIS
│   ├── advanced_metrics.py        🆕 Sharpe, Sortino, Calmar
│   ├── trade_analytics.py         🆕 MAE/MFE analysis
│   └── __init__.py
│
├── data/                           # ✅ Data pipeline (DONE)
│   ├── data_pipeline.py
│   └── providers/
│
└── validation/                     # ✅ Validation (DONE)
    ├── walk_forward.py
    ├── monte_carlo.py
    └── robustness.py
```

---

## Implementation Priority

### **Phase 2A: Core Signals** (30 min)
1. RSI signal (overbought/oversold)
2. MACD signal (histogram cross)
3. Bollinger Bands (breakout)

### **Phase 2B: Filters** (15 min)
4. Spread filter (bid-ask spread)
5. Time filter (avoid first/last hour)
6. Volatility filter (ATR threshold)

### **Phase 2C: Advanced Metrics** (20 min)
7. Sharpe Ratio
8. Sortino Ratio
9. Calmar Ratio

### **Phase 2D: Strategy Templates** (15 min)
10. Base strategy class
11. Complete strategy examples
12. Easy configuration

---

## Code Quality Standards

1. **Lean**: Each file <150 lines
2. **Clean**: One purpose per file
3. **Consistent**: Same interface pattern
4. **Documented**: Docstrings on all classes
5. **Testable**: Can run independently

---

**Let's build.** 🎮
