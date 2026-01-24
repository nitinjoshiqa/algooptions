# Technical Indicators

## Indicators Used in AlgoOptions

The screener uses 8 primary technical indicators to generate signals:

### 1. RSI (Relative Strength Index)
**Purpose:** Identify overbought/oversold conditions  
**Formula:** RSI = 100 - (100 / (1 + RS)) where RS = AvgGain/AvgLoss

```
RSI > 70: Overbought (potential pullback)
RSI < 30: Oversold (potential bounce)
RSI 40-60: Neutral
```

**In AlgoOptions:** Boosts bearish score if RSI > 70, bullish if RSI < 30

---

### 2. MACD (Moving Average Convergence Divergence)
**Purpose:** Identify momentum changes  
**Components:**
- MACD Line = 12 EMA - 26 EMA
- Signal Line = 9 EMA of MACD
- Histogram = MACD - Signal

```
MACD > Signal: Bullish momentum
MACD < Signal: Bearish momentum
MACD crossing Signal: Momentum shift
```

---

### 3. EMA (Exponential Moving Average)
**Purpose:** Identify trend direction  
**Commonly used periods:**
- EMA 9: Ultra-short term
- EMA 20: Short term (swing)
- EMA 50: Medium term (monthly)
- EMA 200: Long term (yearly)

```
Price > EMA_50 > EMA_200: Bullish
Price < EMA_50 < EMA_200: Bearish
```

---

### 4. Bollinger Bands
**Purpose:** Identify volatility extremes  
**Formula:**
- Upper Band = SMA_20 + (2 × StdDev)
- Lower Band = SMA_20 - (2 × StdDev)

```
Price touches Upper Band: Overbought
Price touches Lower Band: Oversold
Band squeeze: Low volatility (breakout imminent)
Band expansion: High volatility
```

---

### 5. Volume Analysis
**Purpose:** Confirm price moves  
**Logic:**
- Volume up + Price up = Strong bullish
- Volume up + Price down = Strong bearish
- Volume down + Any price = Weak signal

```
Volume Confirmation:
- High volume breakout: Likely to hold
- Low volume breakout: Likely to fail
```

---

### 6. ATR (Average True Range)
**Purpose:** Measure volatility  
**Use in AlgoOptions:**
- Calculate position size
- Set stop-loss width
- Identify low/high volatility environments

```
Low ATR (₹5 on ₹100): Stable stock
High ATR (₹20 on ₹100): Volatile stock
```

---

### 7. VWAP (Volume-Weighted Average Price)
**Purpose:** Fair value level for intraday trades  
**Formula:** VWAP = Σ(Price × Volume) / Σ(Volume)

```
Price > VWAP: Bullish (institutional buying)
Price < VWAP: Bearish (institutional selling)
Price near VWAP: Fair value
```

---

### 8. Opening Range (OR)
**Purpose:** Identify intraday breakouts  
**Definition:** High and Low of first 30 minutes

```
Price breaks above OR High: Bullish breakout
Price breaks below OR Low: Bearish breakdown
Price within OR: Consolidation
```

---

## Indicator Dashboard

The HTML report shows a technical indicator summary for each stock:

```
RSI: 62.5       (Between 30-70, slightly bullish)
MACD: Bullish   (MACD above signal line)
EMA Trend: ↑    (Price above 50/200 EMAs)
Volume: ↑       (Increasing compared to MA)
Bollinger: Mid  (Price at middle band)
VWAP: Above     (Price above fair value)
ATR: ₹15        (Medium volatility)
OR: Neutral     (Within yesterday's range)
```

---

## Custom Indicators (Advanced)

### Cumulative Volume Indicator
```python
cumulative_vol = sum(volume[-20:])
if cumulative_vol > cumulative_vol_baseline:
    score_adjustment += 0.1 (Bullish)
```

### Support/Resistance Strength
```python
touches = count(price_reversal_at_level)
if touches >= 4:
    level_strength = "STRONG"  # High probability
elif touches >= 2:
    level_strength = "MEDIUM"  # Moderate probability
else:
    level_strength = "WEAK"    # Low probability
```

---

See also: [Scoring Engine](../core/scoring-engine.md), [Timeframe Analysis](timeframe-analysis.md)
