# Configuration

## Environment Setup

Edit `.env` file in project root:

```env
# Breeze Connect (Optional - for live data)
BREEZE_API_KEY=your_breeze_key

# Data Source (yfinance or breeze)
DATA_SOURCE=yfinance

# Timezone
TIMEZONE=Asia/Kolkata
```

## System Settings

Edit `core/config.py`:

```python
# Trading Risk
RISK_PER_TRADE = 0.02  # 2% per trade (NEVER change this lightly)
BASE_RR_RATIO = 2.0    # Target 2:1 risk/reward minimum

# Signal Thresholds
MIN_CONFIDENCE = 60    # Only trade signals with 60%+ confidence
MIN_SCORE = 0.15       # Only actionable if |score| >= 0.15

# Scoring Weights (by mode)
INTRADAY_WEIGHTS = {'5m': 0.50, '15m': 0.30, '1h': 0.20}
SWING_WEIGHTS = {'5m': 0.20, '15m': 0.30, '1h': 0.50}
LONGTERM_WEIGHTS = {'5m': 0.10, '15m': 0.20, '1h': 0.70}
```

## Advanced Configuration

### ATR Multipliers
```python
# How wide to make stops based on volatility
ATR_MULTIPLIERS = {
    'low': 1.0,      # < 2% volatility
    'normal': 1.5,   # 2-4% volatility
    'high': 2.5,     # 4-6% volatility
    'extreme': 3.5   # > 6% volatility
}
```

### Market Regime Adjustments
```python
REGIME_ADJUSTMENTS = {
    'trending': {'atr_mult': 1.2, 'rr_target': 2.0},
    'ranging': {'atr_mult': 0.8, 'rr_target': 1.5},
    'volatile': {'atr_mult': 1.4, 'rr_target': 1.8}
}
```

---

See also: [API Reference](api-reference.md)
