# Risk Management

## Philosophy

**Risk Management > Profit Optimization**

We follow the principle: *Protect capital first, profits second.*

Every trade is sized and stopped out to limit losses to **exactly 2% of your trading capital**.

## ATR-Based Stop-Loss

### What is ATR?

ATR (Average True Range) measures volatility - how much a stock typically moves per day:

```
If ATR = ₹10, the stock typically moves ₹10 in a day.
If ATR = ₹50, the stock is highly volatile.
```

### Dynamic Stop-Loss Multipliers

Our system adjusts stop-loss width based on **volatility**:

```
Volatility % = (ATR / Current Price) × 100

< 2% volatility:   SL = 1.0× ATR  (Very tight)
2-4% volatility:   SL = 1.5× ATR  (Tight to normal)
4-6% volatility:   SL = 2.5× ATR  (Wide)
> 6% volatility:   SL = 3.5× ATR  (Very wide)
```

**Why?** High-volatility stocks need wider stops, or we get whipsawed out of good trades.

### Example: Volatile Stock (ADANIGREEN)

```
Current Price: ₹1,200
ATR (14 days): ₹60
Volatility: 60/1200 = 5%  → HIGH VOLATILITY

Stop-Loss = Price - (60 × 2.5) = 1,200 - 150 = ₹1,050
```

## Market Regime Adjustment

The system also adjusts for **market conditions**:

| Regime | SL Multiplier | Rationale | R:R Target |
|--------|---------------|-----------|------------|
| **Trending** | +20% wider | Trends have bigger moves | 2.0 |
| **Ranging** | -20% tighter | Limited room in ranges | 1.5 |
| **Volatile** | +40% wider | Unpredictable swings | 1.8 |
| **Quiet** | Normal | Baseline volatility | 2.0 |

## Risk-to-Reward (R:R) Ratio

**Core Rule:** Never risk ₹1 unless potential gain is ₹1.50+ (minimum 1.5:1)

```
R:R = (Target Price - Entry) / (Entry - Stop Loss)

Example:
Entry: ₹100
SL: ₹95    (Risk = ₹5)
Target: ₹110  (Reward = ₹10)

R:R = 10/5 = 2.0  ✓ ACCEPTABLE (minimum 1.5)
```

### Dynamic R:R Boosting

The system boosts expected R:R based on signal quality:

```
Base R:R = 2.0 (Standard expectation)

Confidence Boost:
- 60-79% confidence: +0.3 → 2.3
- 80-100% confidence: +0.5 → 2.5

Alignment Bonus:
- All 3 timeframes aligned: +0.2
- 2 timeframes aligned: +0.0
- 1 or fewer aligned: -0.2

Market Structure Bonus:
- Entry at support: +0.15
- Entry at resistance (for shorts): +0.15
```

## Position Sizing (2% Risk Rule)

### The Formula

```
Position Size = (Capital × Risk% ) / Risk per Share

Example:
- Trading Capital: ₹1,00,000
- Risk per Trade: 2% = ₹2,000
- Current Price: ₹100
- Stop-Loss: ₹95 (Risk = ₹5 per share)

Position = 2,000 / 5 = 400 shares
```

### Dynamic Adjustment by Risk Level

```
Risk Level    Adjustment    Position Size
─────────────────────────────────────────
LOW (<1.5%)       100%      Use calculated size
NORMAL (1.5-3%)    100%      Use calculated size
MEDIUM (3-5%)       75%      25% reduction
HIGH (>5%)          50%      50% reduction
```

This ensures we don't blow up on volatile stocks.

## Kelly Criterion (Advanced)

For those familiar with betting mathematics, we also offer Kelly-based sizing:

```
Kelly % = (Win% × AvgWin - Loss% × AvgLoss) / AvgWin

Then apply: Position = Kelly% × Trading Capital / Risk per Share

⚠️ Conservative Kelly = Kelly% / 4 (Recommended)
```

## Risk Zones

The system identifies three risk zones:

### 🟢 NORMAL (Safe Entry)
- Stock within normal range
- Volatility < 3%
- Not near extreme support/resistance
- **Action:** Normal position size, standard R:R

### 🟡 MEDIUM (Caution)
- Volatility 3-5%
- Near significant support/resistance
- Extreme RSI (>70 or <30)
- **Action:** 25% smaller position, wider stops

### 🔴 HIGH (Extreme)
- Volatility > 5%
- At 52-week highs/lows
- Deep oversold/overbought
- **Action:** 50% smaller position, very wide stops, or skip trade

## Example Risk Management Flow

```
Signal Generated: RELIANCE, Score = -0.42 (Strong Bearish)
Entry Price: ₹2,500
ATR (14): ₹50
Volatility: 50/2500 = 2% → NORMAL range

SL Multiplier: 1.5 (for 2% volatility)
Stop Loss: 2,500 - (50 × 1.5) = ₹2,425  (Risk = ₹75/share)

Base R:R: 2.0
Confidence: 85% → +0.5 bonus
Final R:R Target: 2.5

Reward per share: 75 × 2.5 = ₹187.50
Target Price: 2,500 + 187.50 = ₹2,687.50

Position Size:
Capital: ₹1,00,000
Risk per trade: 2% = ₹2,000
Position: 2,000 / 75 = 26.67 ≈ 26 shares

✓ Trade Setup:
- Entry: ₹2,500 (26 shares)
- SL: ₹2,425 (max loss ₹1,950 ≈ 1.95%)
- Target: ₹2,688 (potential gain ₹4,875 ≈ 4.87%)
- R:R: 2.5 ✓
```

---

See also: [Position Sizing](position-sizing.md), [Scoring Engine](scoring-engine.md)
