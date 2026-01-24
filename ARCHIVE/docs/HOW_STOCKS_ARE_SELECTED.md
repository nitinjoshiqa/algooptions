# 📊 How Stocks Are Selected - The Complete Process

## Quick Overview
The system picks **154 Nifty200 stocks** through a **7-Phase Technical Analysis Pipeline** that combines:
- Multi-timeframe technical scoring (5m, 15m, 1h)
- Institutional entry signals (volume, VWAP, opening range)
- Risk management filters
- Pattern validation
- Option Greeks optimization

---

## Phase 1️⃣: Universe Selection & Filters

### Input: 154 Nifty200 stocks
```
360ONE, AUBANK, ADANIENSOL, ADANIENT... YESBANK
```

### Applied Filters (Disqualify stocks):

#### **Liquidity Filter** ❌ Removes illiquid stocks
- **Minimum daily volume**: 300,000 shares
- **Minimum daily value**: ₹500M (~$6M)
- Why? Ensures we can exit positions without slippage

#### **Volatility Filter** ❌ Removes too stable/volatile stocks
- **ATR range**: 1.5% - 8.0% of price (14-day)
- Too stable (<1.5%): No profit opportunities
- Too volatile (>8%): High whipsaw risk

**Result**: ~140-150 stocks pass filters (some fail)

---

## Phase 2️⃣: Multi-Timeframe Data Collection

For each stock, fetch 3 timeframes:
```
5-minute  (1 day = 78 candles)     → Intraday entry/exit timing
15-minute (5 days = 20 candles)    → Swing trade signals  
1-hour    (20 days = 20 candles)   → Trend confirmation
```

---

## Phase 3️⃣: Compute Timeframe Scores

### For each timeframe, calculate 8 Technical Indicators:

| Indicator | What it Measures | Range |
|-----------|-----------------|-------|
| **RSI** | Momentum (overbought/oversold) | -1 to +1 |
| **EMA** | Trend direction (fast vs slow) | -1 to +1 |
| **MACD** | Momentum divergence | -1 to +1 |
| **Volume** | Volume surge vs avg | -1 to +1 |
| **Structure** | Pattern quality (HLC alignment) | -1 to +1 |
| **Bollinger Bands** | Price extreme position | -1 to +1 |
| **Opening Range** | First 30min high/low breakout | -1 to +1 |
| **VWAP** | Price vs volume-weighted avg | -1 to +1 |

### Example: COCHINSHIP on Jan 21, 2026

**5m score**: +0.45 (bullish)
- RSI: 65 (strong, not overbought)
- EMA: Bullish cross detected
- Volume: Spiking above 20-day avg
- Structure: Clean higher lows

**15m score**: +0.42 (bullish)
**1h score**: +0.38 (bullish)

✅ **All 3 timeframes agree = HIGH CONFIDENCE**

---

## Phase 4️⃣: Blend Scores by Mode

### Mode = "SWING" (Your current mode)
```
Final Score = (5m × 50%) + (15m × 30%) + (1h × 20%)
              ↑ Short-term entry  ↑ Swing signal  ↑ Trend filter
```

**COCHINSHIP Blended**: (0.45 × 0.50) + (0.42 × 0.30) + (0.38 × 0.20) = **+0.425**

### Why these weights?
- **50% intraday**: Best entry/exit timing
- **30% swing**: Avoid chop, catch moves
- **20% longterm**: Confirm trend, avoid reversals

---

## Phase 5️⃣: Pattern Detection & Validation

Detects technical patterns and validates them:

### Bullish Patterns ✅
- Double Bottom (buy signal)
- Inverted H&S (reversal up)
- Ascending Triangle (breakout)
- Falling Wedge (recovery)

### Bearish Patterns ❌
- Double Top (sell signal)
- Head & Shoulders (reversal down)
- Descending Triangle (breakdown)
- Rising Wedge (pullback)

**Validation**: Historical win rate > 55%

---

## Phase 6️⃣: Calculate Confidence Score

Combines multiple factors into **0-100% confidence**:

### **3-Pillar System**:

#### 🎯 Pillar 1: Signal Agreement (40% weight)
```
Count of strong indicators (>0.3):
COCHINSHIP: 6/6 indicators agree = 100% agreement
Score: +0.425 (from blend) + boost = +0.45
```

#### ⚡ Pillar 2: Momentum Conviction (35% weight)
```
Average of: RSI + EMA + MACD
Example: (0.65 + 0.60 + 0.55) / 3 = 0.60 momentum
```

#### 📊 Pillar 3: Volume Support (25% weight)
```
Volume > 1.2x average? YES
Volume acceleration? YES
VWAP crossover? YES
= Institutional participation confirmed
```

### **Final Confidence Formula**:
```
Confidence = (40% × signal_agreement) 
           + (35% × momentum_strength)
           + (25% × volume_support)
           + (event_risk_adjustment)
           
COCHINSHIP: 40 + 38 + 22 = 100% confidence ✅
```

---

## Phase 7️⃣: Risk Management & Position Sizing

### Calculate Stop Loss & Target:

```
For COCHINSHIP (Price = 1467):
ATR (volatility) = 10

Stop Loss = Price - (2.5 × ATR)
          = 1467 - 25
          = 1442 (-1.7%)

Target = Price + (4.5 × ATR)
       = 1467 + 45
       = 1512 (+3.1%)

Risk:Reward = 45/25 = 1.8:1 ✅ (Good R:R)
```

### Position Sizing:
```
If you risk 2% of account on SL:
Position shares = (Account × 2%) / (SL distance in Rs)
                = (₹100,000 × 2%) / (₹25)
                = 80 shares
```

---

## Final Output: The Ranking

Stocks are sorted by **bearness score** (-1 to +1):

```
Rank  Symbol      Score   Conf%   Price    R:R    Status
--------------------------------------------------------------
1     DIVISLAB    -0.24    64%    6010     1.5:1  BEARISH
2     ADANIENT    -0.22    57%    2032     2.0:1  BEARISH
...
152   NYKAA       +0.17    69%    242      1.8:1  BULLISH
153   POLICYBZR   +0.35   100%    1661     2.5:1  ACTIONABLE ⭐
154   COCHINSHIP  +0.44   100%    1467     1.8:1  ACTIONABLE ⭐
```

---

## 🎯 Actionable Picks Criteria

A stock becomes **"ACTIONABLE"** if:

✅ **Min Confidence**: ≥ 60%  
✅ **Min |Score|**: ≥ 0.35 (strong conviction either direction)  
✅ **Timeframe Alignment**: At least 2/3 timeframes agree  
✅ **R:R Ratio**: ≥ 1.5:1 (profit > risk)  

**From 154 stocks → ~2-10 actionable picks per scan**

---

## 📈 Example: Why COCHINSHIP Made the Cut

| Factor | Value | Status |
|--------|-------|--------|
| 5m Score | +0.45 | ✅ Strong bullish |
| 15m Score | +0.42 | ✅ Strong bullish |
| 1h Score | +0.38 | ✅ Bullish trend |
| Blended | +0.435 | ✅ Actionable threshold |
| Confidence | 100% | ✅ Perfect signal |
| Pattern | None | ✓ Clean move |
| Volume | Spiking | ✅ Institutional entry |
| R:R Ratio | 1.8:1 | ✅ Good risk/reward |

**Decision**: ✅ **TRADE IT** - Swing long from 1467, target 1512, stop 1442

---

## HTML Filters to Control Selection

In your report, you can adjust who gets selected:

```
🔍 Search: Find specific stocks
📊 Sector: Filter by industry
✓ Min Conf%: Require confidence threshold (default: 0%)
✓ Min |Score|: Require signal strength (default: 0.35 = actionable level)
```

**Default Settings**:
- Min |Score| = **0.35** → Shows only actionable picks
- Min Conf% = **0%** → Shows all confidence levels

Uncheck **Min |Score|** to see all 154 stocks including marginal ones.

---

## Key Takeaways

1. **Universe**: 154 Nifty200 stocks analyzed
2. **Filters**: Removes ~5-10% for liquidity/volatility
3. **Scoring**: Blends 3 timeframes (50/30/20 for swing)
4. **Validation**: 8 technical indicators per timeframe
5. **Confidence**: 3-pillar system (signals, momentum, volume)
6. **Actionable**: Score ≥ 0.35 + Confidence ≥ 60%
7. **Output**: Ranked by signal strength + R:R ratio

---

## Data Pipeline Flow

```
154 Stocks
    ↓
[Liquidity & Volatility Filters]
    ↓
~145 Stocks (pass filters)
    ↓
[Fetch 5m/15m/1h candles]
    ↓
[Calculate 8 indicators per TF]
    ↓
[Blend 3 timeframes]
    ↓
[Confidence calculation]
    ↓
[Pattern detection]
    ↓
[Calculate SL/Target/R:R]
    ↓
[Final ranking]
    ↓
~2-10 Actionable picks (|score| ≥ 0.35, conf ≥ 60%)
```

---

**Generated**: Jan 21, 2026  
**Mode**: SWING (50/30/20 weights)  
**Stocks Analyzed**: 154  
**Data Quality**: Real-time (force-yf enabled)
