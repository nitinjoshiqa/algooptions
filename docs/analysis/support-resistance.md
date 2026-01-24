# Support & Resistance

## What Are S/R Levels?

**Support:** Price level where buying interest emerges (floor)  
**Resistance:** Price level where selling pressure emerges (ceiling)

When price bounces from these levels repeatedly, they become **high-probability trade locations**.

## Types of S/R Levels

### 1. Swing Levels (Most Important)
```
Swing Low: Recent local minimum
Swing High: Recent local maximum

RELIANCE daily chart:
         Peak (₹2,600) ← Resistance
        /    \
       /      \
    Low (₹2,450) ← Support
      /        \
     /          \
   Current: ₹2,500 ← Between S/R
```

**How to find:**
- Look at last 20-50 candles
- Mark obvious peaks and troughs
- Strongest if price bounced 2+ times

---

### 2. Pivot Levels (Algorithmic)

```
Pivot = (High + Low + Close) / 3
R1 = (2 × Pivot) - Low    ← Resistance 1
R2 = Pivot + (High - Low)  ← Resistance 2
S1 = (2 × Pivot) - High   ← Support 1
S2 = Pivot - (High - Low)  ← Support 2

Example (Daily):
High: ₹2,550
Low: ₹2,450
Close: ₹2,500

Pivot = (2,550 + 2,450 + 2,500) / 3 = ₹2,500
R1 = (2 × 2,500) - 2,450 = ₹2,550
R2 = 2,500 + (2,550 - 2,450) = ₹2,600
S1 = (2 × 2,500) - 2,550 = ₹2,450
S2 = 2,500 - (2,550 - 2,450) = ₹2,400
```

**Use:** Daily traders, intraday levels, mechanical entries

---

### 3. Moving Average Support

```
Price > EMA_50 > EMA_200 = BULLISH
↑        ↑        ↑

Price < EMA_50 < EMA_200 = BEARISH
↓        ↓        ↓

Key MAs:
- EMA_9: Ultra-short term (intraday scalping)
- EMA_20: Short term (swing trading, weekly alignment)
- EMA_50: Medium term (monthly trend)
- EMA_200: Long term (annual trend, major support/resistance)
```

**Use:** Trend confirmation, dynamic support/resistance

---

### 4. Round Numbers (Psychological)

```
₹100, ₹500, ₹1,000, ₹2,000, ₹5,000, ₹10,000

Why? Traders use limit orders at round numbers.
     Many algorithms use round numbers.
     Psychology: "I'll buy if it hits ₹100"

Reality: Often holds as S/R, but breakouts can be sharp
```

---

### 5. 52-Week High/Low (Institutional Levels)

```
52W High: ₹2,800 ← Major Resistance
Current: ₹2,500
52W Low: ₹2,200 ← Major Support
```

**Why strong?**
- Institutions track these
- Stop-losses cluster here
- Psychology: "If it breaks 52W high, must go higher"

---

## Using S/R in Trading

### Entry: Buy at Support
```
Price: ₹100
Support: ₹98
Entry: ₹98.50 (just below support to catch bounce)
SL: ₹97 (if support breaks)
Target: Next resistance at ₹105

Risk: 100 - 97 = ₹3
Reward: 105 - 100 = ₹5
R:R: 5/3 = 1.67
```

### Entry: Sell at Resistance (Short)
```
Price: ₹100
Resistance: ₹102
Entry: ₹101.50 (just below resistance)
SL: ₹103 (if resistance breaks)
Target: Next support at ₹95

Risk: 103 - 100 = ₹3
Reward: 100 - 95 = ₹5
R:R: 5/3 = 1.67
```

### Breakout Entry: Break Above Resistance
```
Price: ₹100
Resistance: ₹105

Strong Breakout Signal:
- Price > ₹105 with high volume
- Entry: ₹105.50 (confirmed break)
- SL: ₹104.50 (failed breakout)
- Target: Previous R2 or 52W high

Probability: 65-70% success rate
```

---

## Support/Resistance Strength

### Weak S/R (Avoid)
```
- Touched only 1-2 times in recent history
- Price swept through it multiple times
- At random levels (not at swings or pivots)

Action: Skip these, they don't hold
```

### Medium S/R (Trade Carefully)
```
- Touched 2-3 times
- Price respects it ~60% of the time
- At medium-term swings or moving averages

Action: OK for swing trades, use tight stops
```

### Strong S/R (High Probability)
```
- Touched 4+ times (proven support/resistance)
- Price respects it 75%+ of the time
- At major swings, pivots, or 52W highs/lows
- Multiple timeframes align (daily + weekly)

Action: Ideal entry zone, larger positions OK
```

---

## Example: INFY Trading Plan

```
Setup (Daily Chart):
- 52W High: ₹2,100
- R2 (Pivot): ₹2,080
- R1 (Pivot): ₹2,050
- Current Price: ₹2,020
- S1 (Pivot): ₹1,990
- S2 (Pivot): ₹1,960
- 52W Low: ₹1,800

EMA_50: ₹2,010
EMA_200: ₹1,950

Scenario 1 - Support Hold:
IF price dips to S1 (₹1,990):
  Entry: ₹1,990
  SL: ₹1,980 (risk ₹10)
  Target: ₹2,050 (R1, reward ₹60)
  R:R: 6.0:1 ✓ Excellent

Scenario 2 - Breakout Up:
IF price breaks R1 (₹2,050) on volume:
  Entry: ₹2,055 (confirmed break)
  SL: ₹2,040 (failed breakout)
  Target: ₹2,100 (52W High, reward ₹45)
  Risk: ₹15, Reward: ₹45
  R:R: 3.0:1 ✓ Good

Scenario 3 - Major Breakdown:
IF price breaks S2 (₹1,960):
  Signal: Change in trend, skip longs
  Shorts: Enter ₹1,950
  Target: ₹1,900 (support cluster)
```

---

## How AlgoOptions Uses S/R

Our system automatically:

1. **Identifies** swing highs/lows from 50-candle history
2. **Calculates** daily pivot levels
3. **Flags** nearby support/resistance for each stock
4. **Adjusts** stop-loss placement to just outside levels
5. **Boosts** confidence if signal aligns with S/R

---

See also: [Scoring Engine](../core/scoring-engine.md), [Risk Management](../core/risk-management.md)
