# Backtesting Guide

## Why Backtest?

Before trading real money, prove that your strategy works on **historical data**.

```
Trading in real markets = Expensive learning
Backtesting = Free learning
```

## Run the Backtest

```bash
# Available backtest scripts:
python backtest_nifty200_comprehensive.py   # All stocks, all timeframes
python backtest_nifty200_conservative.py    # Conservative filters only
python backtest_enhanced_kelly.py           # Kelly Criterion sizing
```

## Interpreting Results

### Key Metrics

| Metric | Target | Meaning |
|--------|--------|---------|
| **Win Rate** | > 50% | % of trades that profit |
| **Avg Win** | > 0 | Average profit per winning trade |
| **Avg Loss** | > 0 | Average loss per losing trade |
| **Profit Factor** | > 1.5 | (Total Wins) / (Total Losses) |
| **Sharpe Ratio** | > 1.0 | Risk-adjusted returns |
| **Max Drawdown** | < 20% | Biggest peak-to-trough loss |

### Example Report

```
Backtest Results: NIFTY 200 (Last 3 Months)
════════════════════════════════════════════
Total Trades:         145
Winning Trades:        82  (56.6% win rate) ✓
Losing Trades:         63
Average Win:        ₹850
Average Loss:       ₹420
Profit Factor:       2.02  (82×850) / (63×420) ✓✓
Total Profit:     ₹46,150
Max Drawdown:        12.3% ✓

Conclusion: PROFITABLE STRATEGY ✓
```

## Customizing Backtests

Edit `backtest_nifty200_conservative.py`:

```python
# Change date range
START_DATE = "2025-10-01"
END_DATE = "2026-01-21"

# Change universe
UNIVERSE = "nifty50"  # or "banknifty"

# Change confidence threshold
MIN_CONFIDENCE = 75  # (default 60)

# Change scoring weights
weights = {'5m': 0.1, '15m': 0.2, '1h': 0.7}
```

## Backtesting vs Live Trading

| Factor | Backtest | Live |
|--------|----------|------|
| **Slippage** | None | 1-2 paise per trade |
| **Commissions** | Usually ignored | ₹20-50 per trade |
| **Market Impact** | Ignored | Real impact on big positions |
| **Liquidity** | Assumed perfect | Real liquidity limits |

**Reality:** Live results 10-20% worse than backtest (account for slippage).

## Forward Testing (Paper Trading)

Before live trading, paper trade for 2-4 weeks:

```
1. Generate signals daily
2. Simulate entries/exits
3. Track in Excel
4. Don't risk real money
5. Prove system works first

If paper trading:
- Shows >55% win rate for 50+ trades
- Shows consistent profits over 4 weeks
- Then you can go live with small sizes
```

---

See also: [Risk Management](../core/risk-management.md)
