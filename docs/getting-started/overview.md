# Overview

## System Architecture

The AlgoOptions screener follows a **modular, production-grade architecture**:

```
┌─────────────────────────────────────────────────┐
│  Data Input Layer                               │
│  (Yahoo Finance / Breeze API)                   │
└────────────────┬────────────────────────────────┘
                 │
        ┌────────▼─────────┐
        │  Universe Manager │ ◄── nifty200, banknifty, nifty50
        └────────┬─────────┘
                 │
        ┌────────▼──────────────┐
        │ Scoring Engine        │
        │ ├─ 5-min analysis     │
        │ ├─ 15-min analysis    │
        │ └─ 1-hour analysis    │
        └────────┬──────────────┘
                 │
    ┌────────────┼────────────────┐
    │            │                │
┌───▼────┐  ┌───▼────┐  ┌───────▼────┐
│ Risk   │  │Options │  │Position    │
│Mgmt    │  │Strat   │  │Sizing      │
└────────┘  └────────┘  └────────────┘
    │            │                │
    └────────────┼────────────────┘
                 │
        ┌────────▼──────────┐
        │ Report Generator  │
        │ ├─ CSV Export     │
        │ └─ HTML Dashboard │
        └───────────────────┘
```

## Data Flow

1. **Data Collection** → Fetch OHLCV data from Yahoo Finance
2. **Multi-Timeframe Analysis** → Calculate scores for 5m, 15m, 1h
3. **Aggregation** → Weighted average (50% daily, 30% swing, 20% longterm)
4. **Risk Assessment** → Determine volatility, ATR, confidence
5. **Position Sizing** → Calculate shares based on 2% risk
6. **Report Generation** → Create HTML/CSV output

## Scoring System

The system uses a **-1 to +1 scoring scale**:

| Score Range | Interpretation | Signal Strength |
|-------------|-----------------|-----------------|
| **< -0.35** | Strong Bearish | ⭐⭐⭐ Strong |
| **-0.15 to -0.35** | Bearish | ⭐⭐ Moderate |
| **-0.05 to -0.15** | Weak Bearish | ⭐ Weak |
| **-0.05 to +0.05** | Neutral | ➖ No Signal |
| **+0.05 to +0.15** | Weak Bullish | ⭐ Weak |
| **+0.15 to +0.35** | Bullish | ⭐⭐ Moderate |
| **> +0.35** | Strong Bullish | ⭐⭐⭐ Strong |

## Confidence Metric

Confidence (0-100%) represents signal reliability:

- **90-100%** - All indicators aligned, very reliable
- **70-89%** - Most indicators aligned, good reliability
- **50-69%** - Mixed signals, moderate reliability
- **25-49%** - Weak alignment, low reliability
- **< 25%** - Very weak signal, avoid trading

## Sectors Covered

The screener analyzes stocks across these sectors:

- 🏦 Banking & Financial Services
- ⚙️ Auto & Engineering
- 🔧 Manufacturing
- ⚡ Energy & Utilities
- 🏢 Pharma & Healthcare
- 🏗️ Infrastructure
- 🛒 Consumer & Retail
- 📱 Technology & IT
- 🚀 Innovation & Startups

---

For detailed explanations, see:
- [Scoring Engine](../core/scoring-engine.md) - How scores are calculated
- [Risk Management](../core/risk-management.md) - Risk calculations
- [Position Sizing](../core/position-sizing.md) - Position size logic
