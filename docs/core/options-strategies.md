# Options Strategies

## System Overview

The screener recommends **5 core option strategies** based on:
1. **Direction**: Bullish, Bearish, or Neutral
2. **Volatility**: Low, Normal, or High (IV)
3. **Confidence**: How sure we are about direction
4. **Score**: Signal strength (-1 to +1 scale)

## Strategy Selection Matrix

```
Direction    Volatility    Confidence    Recommended Strategy
─────────────────────────────────────────────────────────────
Bearish      Low           High (>70%)    Short Put Spread
Bearish      Low           Med (50-70%)   Long Put or Straddle
Bearish      Medium        High           Long Put Spread
Bearish      High          High           Iron Butterfly or Short Strangle
Bearish      High          Low            Wide Strangle or Skip

Neutral      Low           Any            Short Straddle
Neutral      Medium        Any            Short Strangle or Call Ratio Spread
Neutral      High          Any            Iron Butterfly or Iron Condor

Bullish      Low           High           Short Call Spread
Bullish      Low           Med            Long Call or Straddle
Bullish      Medium        High           Long Call Spread
Bullish      High          High           Iron Butterfly or Long Strangle
Bullish      High          Low            Wide Strangle or Skip
```

## 5 Core Strategies Explained

### 1. 📉 Long Put (Bearish, Buy Protection)

**Setup:**
```
Buy 1 ATM Put
Sell 1 OTM Put (to reduce cost)

Example: RELIANCE @ ₹2,500
Buy ₹2,500 Put
Sell ₹2,450 Put
Net Cost: ₹20 (spread cost)
Width: ₹50
```

**When to Use:**
- Very bearish bias
- High confidence (>75%)
- Want to limit downside
- Earnings play (buy volatility)

**Profit/Loss:**
```
Max Profit: Width - Cost = 50 - 20 = ₹30 per share
Max Loss: Cost = ₹20 per share
Break Even: Strike - Cost = 2,500 - 20 = ₹2,480
```

**Pros:** Limited risk, defined profit, directional
**Cons:** Time decay works against you, need sharp move

---

### 2. 📈 Long Call (Bullish, Buy Upside)

**Setup:**
```
Buy 1 ATM Call
Sell 1 OTM Call (to reduce cost)

Example: INFY @ ₹2,000
Buy ₹2,000 Call
Sell ₹2,050 Call
Net Cost: ₹25
Width: ₹50
```

**When to Use:**
- Very bullish bias
- High confidence (>75%)
- Want unlimited upside
- Earnings play (buy volatility)

**Profit/Loss:**
```
Max Profit: Width - Cost = 50 - 25 = ₹25 per share
Max Loss: Cost = ₹25 per share
Break Even: Strike + Cost = 2,000 + 25 = ₹2,025
```

**Pros:** Directional, clear profit target
**Cons:** Loses money if stock doesn't move enough

---

### 3. 🎢 Short Straddle (Neutral, Sell Time Decay)

**Setup:**
```
Sell 1 ATM Call
Sell 1 ATM Put (at same strike)

Example: TCS @ ₹3,500
Sell ₹3,500 Call @ ₹80
Sell ₹3,500 Put @ ₹80
Net Credit: ₹160
```

**When to Use:**
- Neutral signal (no clear direction)
- Low IV environment
- Stock consolidating
- Want to collect time decay

**Profit/Loss:**
```
Max Profit: Credit = ₹160 per share
Max Loss: Unlimited above + Unlimited below
Break Even Upper: 3,500 + 160 = ₹3,660
Break Even Lower: 3,500 - 160 = ₹3,340
```

**Pros:** High credit, money if stock stays still, time decay helps
**Cons:** Unlimited risk both ways, need very good entry

---

### 4. 🦋 Iron Butterfly (Neutral, Limited Risk)

**Setup:**
```
Sell 1 ATM Call      (e.g., ₹100 strike)
Buy 1 OTM Call       (e.g., ₹110 strike)
Sell 1 ATM Put       (e.g., ₹100 strike)
Buy 1 OTM Put        (e.g., ₹90 strike)

Net: Credit if structured well
```

**When to Use:**
- Neutral bias, low IV
- Want defined, small risk
- Stock very stable
- Earnings just passed (vega decay helps)

**Profit/Loss:**
```
Max Profit: Credit received
Max Loss: Width of wing (limited, defined)
Break Even: Strike ± Credit
```

**Pros:** Defined risk both sides, excellent risk/reward in low IV
**Cons:** Complex, needs experience, multiple Greeks to manage

---

### 5. 🎪 Short Strangle (Neutral, Selling Extremes)

**Setup:**
```
Sell 1 OTM Call  (higher strike, e.g., ₹110)
Sell 1 OTM Put   (lower strike, e.g., ₹90)

Example: Stock @ ₹100
Sell ₹110 Call @ ₹20
Sell ₹90 Put @ ₹20
Net Credit: ₹40
```

**When to Use:**
- Neutral with range
- IV is elevated (good premium)
- Stock consolidating
- Don't expect big moves

**Profit/Loss:**
```
Max Profit: ₹40 (if stock stays ₹90-₹110)
Max Loss: Unlimited outside range
Break Even: 110 + 40 = ₹150 (up)
            90 - 40 = ₹50 (down)
```

**Pros:** Good credit, better than straddle (more room)
**Cons:** Still has undefined risk, needs management

---

## Implied Volatility (IV) and Strategy Selection

### IV Rank (Low = 0-33%, Medium = 33-67%, High = 67-100%)

```
LOW IV (<20 percentile):
- Sell credit spreads
- Short strangles/straddles
- Avoid buying options (premiums cheap)

MEDIUM IV (33-67):
- Neutral → Strangles
- Bullish/Bearish → Defined spreads
- Balanced risk/reward

HIGH IV (>80 percentile):
- Buy options (premiums expensive but move big)
- Sell verticals/butterflies (IV crush helps)
- Avoid naked short
- Close positions if neutral signal
```

## Examples by Stock Type

### Example 1: High-Conviction Bearish (ADANIGREEN)
```
Score: -0.45 (Very Bearish)
Confidence: 88%
IV: 65 (Medium)
Current: ₹1,200
ATR: ₹60

Recommended: Long Put Spread
- Buy ₹1,200 Put
- Sell ₹1,150 Put
- Cost: ₹15
- Max Profit: ₹35
- Risk/Reward: 35/15 = 2.3:1
```

### Example 2: Neutral Signal (TCS)
```
Score: -0.02 (Neutral)
Confidence: 45%
IV: 18 (Low)
Current: ₹3,500
ATR: ₹70

Recommended: Short Strangle
- Sell ₹3,600 Call @ ₹30
- Sell ₹3,400 Put @ ₹30
- Credit: ₹60
- Max Profit: ₹60 (if stays 3,400-3,600)
- Risk: Defined by management
```

### Example 3: High-Conviction Bullish (INFY)
```
Score: +0.42 (Very Bullish)
Confidence: 75%
IV: 42 (Medium)
Current: ₹2,000
ATR: ₹55

Recommended: Long Call Spread
- Buy ₹2,000 Call
- Sell ₹2,050 Call
- Cost: ₹20
- Max Profit: ₹30
- Risk/Reward: 30/20 = 1.5:1
```

## Risk Management for Options

### Rule 1: Position Sizing
```
Max Loss per Trade = 2% of capital

Example:
- Capital: ₹1,00,000
- Max Loss: ₹2,000
- Long Put Spread Max Loss: ₹20 (spread cost)
- Contracts: 2,000 / 2,000 = 1 contract max
```

### Rule 2: Closing Positions
```
- Close at 50% profit (don't be greedy)
- Close at 21 DTE (days to expiration) if breakeven
- Close if thesis changes
- Never hold naked shorts to expiration
```

### Rule 3: Avoid "Infinite" Risk
```
❌ NEVER:
- Sell naked calls or puts (undefined loss)
- Sell straddles/strangles without stop loss
- Hold short premium to expiration

✅ ALWAYS:
- Buy protective options (caps risk)
- Define exit before entry
- Manage size for undefined risk
```

---

See also: [Risk Management](risk-management.md), [Position Sizing](position-sizing.md)
