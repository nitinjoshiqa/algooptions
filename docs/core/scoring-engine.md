# Scoring Engine

## How Signals Are Generated

The scoring engine is the **heart of the system**. It analyzes multiple technical indicators across three timeframes and produces a single composite "bearness score" (-1 to +1).

## Multi-Timeframe Scoring

### 1. Five-Minute Analysis (Intraday)
Captures **short-term momentum** and quick reversals:

```
5m Score = (OR + VWAP + RSI + Volume) / 4
OR = Opening Range score (-1 to +1)
VWAP = Volume-Weighted Average Price score
RSI = Relative Strength Index momentum
Volume = Volume trend strength
```

**Use Case:** Intraday scalpers, entry timing

### 2. Fifteen-Minute Analysis (Swing)
Captures **swing trading opportunities** (4-8 hour moves):

```
15m Score = (Structure + EMA + MACD + BB) / 4
Structure = Price structure quality (reversal patterns)
EMA = Exponential Moving Average trend
MACD = Momentum Divergence
BB = Bollinger Band extremes
```

**Use Case:** Swing traders, day traders

### 3. One-Hour Analysis (Long-term)
Captures **longer-term trend direction** (1-3 day moves):

```
1h Score = (Trend + Support/Resistance + Volume Profile) / 3
Trend = Overall directional bias
S/R = Proximity to support/resistance levels
Volume Profile = Volume at different price levels
```

**Use Case:** Position traders, swing traders

## Composite Score Calculation

```
Final Score = (5m_score × 20%) + (15m_score × 30%) + (1h_score × 50%)

Weights (by default mode):
- Intraday Mode:    5m: 50%,  15m: 30%, 1h: 20%
- Swing Mode:       5m: 20%,  15m: 30%, 1h: 50%  ← Current Default
- Long-term Mode:   5m: 10%,  15m: 20%, 1h: 70%
```

## Component Indicators

### 1. Opening Range (OR)
**What:** Price position relative to first 30-minute high/low

```
OR_High = Max(price[0:30 minutes])
OR_Low = Min(price[0:30 minutes])

If price > OR_High: +1 (bullish breakout)
If price < OR_Low:  -1 (bearish breakdown)
Otherwise: Interpolate (-1 to +1)
```

**Signal:** Strong intraday moves start with OR breakouts

### 2. VWAP (Volume-Weighted Average Price)
**What:** Average price weighted by volume - the "true fair value"

```
VWAP = Sum(Price × Volume) / Sum(Volume)

If price > VWAP: +1 (bullish, price above fair value)
If price < VWAP: -1 (bearish, price below fair value)
```

**Signal:** Price above VWAP = institutional buying, bullish

### 3. RSI (Relative Strength Index)
**What:** Momentum indicator measuring overbought/oversold conditions

```
RSI = 100 - (100 / (1 + RS))
RS = Average Gain / Average Loss (14 periods)

RSI > 70: +1 (Overbought, potential reversal down)
RSI < 30: -1 (Oversold, potential reversal up)
RSI = 50: 0 (Neutral)
```

**Signal:** Extreme RSI often precedes reversals

### 4. Volume Analysis
**What:** Trend confirmation by volume

```
Volume Trend = (Current Vol - MA_Vol) / MA_Vol × 100

High Volume + Up = +1 (Strong buying)
High Volume + Down = -1 (Strong selling)
Low Volume + Any = ±0.3 (Weak signal)
```

**Signal:** Price moves with volume are more reliable

### 5. Price Structure
**What:** Quality of price action patterns

```
Strong Reversal Pattern: +/- 0.8
Double Top/Bottom: +/- 0.6
Support/Resistance Touch: +/- 0.4
Random Walk: ±0.2
```

**Signal:** High-quality patterns = higher probability moves

### 6. EMA (Exponential Moving Average)
**What:** Trend direction using weighted moving averages

```
If price > EMA_50: +0.5 (Bullish trend)
If price > EMA_200: +0.5 (Long-term bullish)

Score = Combines short + long EMA alignment
```

**Signal:** Prices above EMAs = bullish, below = bearish

### 7. MACD (Moving Average Convergence Divergence)
**What:** Momentum trend changes

```
MACD = 12 EMA - 26 EMA
Signal Line = 9 EMA of MACD

MACD > Signal: +0.5 (Bullish momentum)
MACD < Signal: -0.5 (Bearish momentum)
```

**Signal:** Crossovers often precede big moves

### 8. Bollinger Bands
**What:** Volatility and extremes

```
BB_Upper = SMA_20 + (2 × StdDev_20)
BB_Lower = SMA_20 - (2 × StdDev_20)

If price > BB_Upper: +1 (Overbought/breakout)
If price < BB_Lower: -1 (Oversold/breakdown)
If price near Mid: 0 (Fair value)
```

**Signal:** Touching bands shows volatility extremes

## Confidence Calculation

Confidence measures how "sure" we are about the signal:

```
Base Confidence = Average of:
  - Indicator agreement (how many indicators align?)
  - Pattern quality (strong vs weak patterns)
  - Volume confirmation (is volume backing the move?)
  - Timeframe alignment (are multiple timeframes aligned?)

Confidence Adjustment:
  - If all indicators agree: +20%
  - If RSI is in extreme zone: +15%
  - If volume > 150% of average: +10%
  - If at support/resistance: +15%
  - If price just broke key level: +20%
```

## Risk Scoring

Risk assessment determines position size and stop-loss width:

```
Volatility Risk = ATR / Price × 100%

Risk Level Classification:
- < 1.5%: LOW RISK (tight stops, larger positions)
- 1.5-3%: NORMAL RISK (standard stops, standard positions)
- 3-5%: MEDIUM RISK (wider stops, smaller positions)
- > 5%: HIGH RISK (very wide stops, tiny positions)
```

---

## Example: Analyzing INFY

```
5m Score:  +0.12  (Price above VWAP, RSI=52, normal volume)
15m Score: +0.08  (Small uptrend, MACD positive)
1h Score:  +0.02  (Price near 50 EMA, weak structure)

Final Score = (0.12×20%) + (0.08×30%) + (0.02×50%)
            = 0.024 + 0.024 + 0.010
            = +0.058 ✓ Weak Bullish Signal
            
Confidence: 62% (Most indicators slightly bullish, but not strongly aligned)
```

See also: [Risk Management](risk-management.md), [Technical Indicators](../analysis/indicators.md)
