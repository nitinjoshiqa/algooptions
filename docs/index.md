# AlgoOptions Wiki - Business Logic Documentation

Welcome to the complete business logic documentation for the **NIFTY Bearnness Screener**. This wiki explains how the system analyzes stocks and generates trading signals.

## 📊 What is AlgoOptions?

AlgoOptions is an **intelligent multi-timeframe stock screener** that:
- Analyzes bearness/bullish sentiment across intraday, swing, and longterm timeframes
- Generates risk-adjusted trading signals with suggested stop-loss and targets
- Calculates position sizing based on 2% risk management
- Recommends options strategies (spreads, straddles, etc.) based on volatility
- Integrates support/resistance levels for optimal entry/exit points

## 🎯 Key Features

| Feature | Description |
|---------|-------------|
| **Multi-Timeframe Analysis** | Combines 5-min, 15-min, and 1-hour data for robust signals |
| **Risk Management** | Dynamic stop-loss sizing based on market volatility (ATR) |
| **Position Sizing** | Kelly Criterion-based position sizing at 2% risk per trade |
| **Options Intelligence** | Suggests option strategies based on IV, volatility, and directional bias |
| **Support/Resistance** | Identifies swing highs/lows and pivot levels for technical analysis |
| **Sector Analysis** | Groups stocks by sector to identify sector-wide trends |
| **Confidence Scoring** | 0-100% confidence metric for each signal |

## 📚 Documentation Structure

- **Getting Started** - Installation and quick tutorials
- **Core Systems** - Deep dives into scoring, risk management, position sizing
- **Technical Analysis** - Support/resistance, timeframe analysis, indicators
- **Advanced** - API reference, configuration, backtesting

## 🚀 Quick Navigation

- New to the system? Start with [Installation](getting-started/installation.md)
- Want to understand how signals are generated? Read [Scoring Engine](core/scoring-engine.md)
- Need help with risk management? See [Risk Management](core/risk-management.md)
- Questions? Check [FAQ](faq.md)

---

**Last Updated:** January 21, 2026  
**Version:** 1.0 Production Ready
