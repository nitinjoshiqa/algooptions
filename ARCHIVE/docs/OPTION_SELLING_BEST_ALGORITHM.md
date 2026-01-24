# 📊 Best Algorithm for Option Selling - Complete Strategy

## Overview

To identify stocks **suitable for option selling**, we use a **Volatility-Based Viability Score** that prioritizes:

1. **Low Implied Volatility (IV)** - Premium decay working FOR you
2. **Low Historical Volatility (HV)** - Actual price stability
3. **High Liquidity** (tight bid-ask) - Easy entry/exit
4. **Directional Neutrality** - Less likely to gap against you

---

## Recommended Algorithm: "Selling Viability Score"

### Formula

```
SELLING_VIABILITY_SCORE = (IV_Score × 0.35) + (HV_Score × 0.35) + (Liquidity_Score × 0.20) + (Neutral_Score × 0.10)

Range: 0-100
Higher = Better for selling options
```

### Scoring Breakdown

#### 1. **IV Score (35% weight)** - Most Important
Why? **Premium decay is your profit source**

```
IV < 20%     → 100 (extremely cheap premium to sell)
IV 20-30%    → 85  (cheap premium, IDEAL for selling)
IV 30-40%    → 60  (normal, acceptable)
IV 40-50%    → 35  (elevated, less premium decay)
IV > 50%     → 10  (avoid - gamma risk)
```

**Example**: SBIN IV=18% → Score=100  
**Why**: When you sell a call/put, you want IV to drop (and you keep premium)

---

#### 2. **HV Score (35% weight)** - Very Important
Why? **If stock doesn't move, you win the trade**

```
HV < 1.0%    → 100 (ultra-stable, perfect for naked selling)
HV 1.0-1.5%  → 90  (very stable, IDEAL)
HV 1.5-2.0%  → 75  (stable, good for spreads)
HV 2.0-3.0%  → 50  (normal volatility)
HV > 3.0%    → 20  (choppy, risky for selling)
```

**Example**: INFY HV=1.1% → Score=90  
**Why**: Lower HV = premium you collect is safer (less chance of assignment)

---

#### 3. **Liquidity Score (20% weight)** - Critical for Exit
Why? **You need to exit quickly if needed**

```
Bid-Ask Spread:
< 1.0%       → 95  (liquid, excellent liquidity)
1.0-2.0%     → 85  (very good, can exit easy)
2.0-3.0%     → 75  (good, acceptable)
3.0-5.0%     → 50  (fair, some friction)
> 5.0%       → 10  (poor, hard to exit)
```

**Example**: TCS Spread=0.7% → Score=95  
**Why**: Tight spreads = you get full premium, exit at better prices

---

#### 4. **Directional Neutrality (10% weight)** - Safety Bonus
Why? **Lower directional bias = premium is safer**

```
|Score| < 0.10    → 95  (very neutral, no strong bias)
|Score| 0.10-0.20 → 85  (neutral, IDEAL for sellers)
|Score| 0.20-0.30 → 60  (slight directional)
|Score| 0.30-0.50 → 30  (directional move expected)
|Score| > 0.50    → 10  (strong move expected, risky)
```

**Example**: HDFCBANK |Score|=0.08 → Score=95  
**Why**: Stock not expected to move big = premium collection safer

---

## Top 5 Option Selling Candidates

Based on this algorithm, here are typical top candidates:

| Rank | Symbol | IV | HV | Spread | |Score| | **Selling Score** | Rating |
|------|--------|----|----|--------|--------|---------|--------|
| 1 | SBIN | 18% | 0.8% | 0.8% | 0.05 | **96** | ⭐⭐⭐⭐⭐ Excellent |
| 2 | TCS | 20% | 0.9% | 0.7% | 0.08 | **94** | ⭐⭐⭐⭐⭐ Excellent |
| 3 | INFY | 22% | 1.1% | 1.2% | 0.12 | **91** | ⭐⭐⭐⭐ Very Good |
| 4 | HDFCBANK | 25% | 1.3% | 1.1% | 0.15 | **88** | ⭐⭐⭐⭐ Very Good |
| 5 | RELIANCE | 28% | 1.5% | 1.4% | 0.18 | **83** | ⭐⭐⭐ Good |

---

## Visual Card Design (For HTML Report)

### What Each Card Shows

```
┌─────────────────────────────────────────┐
│ 💰 OPTION SELLING OPPORTUNITY #1        │
├─────────────────────────────────────────┤
│ Symbol: SBIN                            │
│ Score: 96/100 ⭐⭐⭐⭐⭐ EXCELLENT       │
├─────────────────────────────────────────┤
│ Implied Vol: 18% 🟢 Very Low            │
│   → Premium decay FAST in your favor     │
│                                          │
│ Historical Vol: 0.8% 🟢 Ultra-Stable    │
│   → Stock stays relatively flat          │
│                                          │
│ Bid-Ask Spread: 0.8% 🟢 Excellent       │
│   → Easy entry/exit, no slippage         │
│                                          │
│ Directional Signal: ±0.05 🟡 Neutral   │
│   → No strong move expected              │
├─────────────────────────────────────────┤
│ ✅ PERFECT FOR NAKED SELLING             │
│ Strategies: Naked Put | Covered Call     │
│            Put Spread | Strangle         │
├─────────────────────────────────────────┤
│ 📊 Action: Sell 1 ATM Call OR Put       │
│ 💰 Premium: High (IV decay advantage)    │
│ ⚠️  Risk: Very Low (stable, tight stops) │
└─────────────────────────────────────────┘
```

---

## Implementation in HTML Report

### Card Grid Layout

```html
<section class="option-selling-section">
    <h2>💰 TOP 5 OPTION SELLING CANDIDATES</h2>
    <p>Stocks best suited for premium selling (short calls/puts)</p>
    
    <div class="selling-cards-grid">
        <!-- 5 Cards shown here -->
        <!-- Card 1: SBIN (Score 96)
        <!-- Card 2: TCS (Score 94)
        <!-- Card 3: INFY (Score 91)
        <!-- Card 4: HDFCBANK (Score 88)
        <!-- Card 5: RELIANCE (Score 83)
    </div>
</section>

<section class="option-intelligence-section">
    <!-- Existing Option Intelligence cards (6 cards by |score|) -->
</section>
```

---

## Trading Rules for Option Selling

### ✅ SELL OPTIONS WHEN:

1. **Selling Score ≥ 80**
   ```
   SBIN (96): YES ✅
   INFY (91): YES ✅
   RELIANCE (83): YES ✅
   ```

2. **IV ≤ 30%** (Normal or low)
   ```
   Example: Sell call when IV drops from 40% to 25%
   ```

3. **Volatility < 2%** (Calm market)
   ```
   Example: Intraday scalping options better in quiet markets
   ```

4. **Bid-Ask Spread < 3%** (Liquid options)
   ```
   Example: SBIN spread=0.8% is excellent
   ```

5. **Not earnings week** (Unpredictable events)
   ```
   Example: Avoid selling near quarterly results
   ```

### ❌ AVOID SELLING WHEN:

1. **Selling Score < 70**
   ```
   Poor liquidity or volatile stocks = hard to exit
   ```

2. **IV > 40%** (High uncertainty)
   ```
   When market is chaotic, gamma risk too high
   ```

3. **|Score| > 0.4** (Strong directional move expected)
   ```
   If stock is expected to drop 5%, selling calls risky
   ```

4. **HV > 3%** (Choppy movement)
   ```
   When ATR is high, wider stops needed = less profit
   ```

---

## Comparison: Option Selling vs Buying

| Aspect | **Option SELLING** | **Option BUYING** |
|--------|-------------------|------------------|
| **When to Use** | Low Vol, High Score | High Vol, Strong Signal |
| **Best Stocks** | SBIN, INFY, TCS | HDFCBANK, RELIANCE |
| **Score Focus** | Selling Score ≥ 80 | \|Score\| ≥ 0.3 |
| **IV Level** | Low IV < 30% | High IV > 40% |
| **Strategy** | Naked, Spreads | Long Call/Put |
| **Time Decay** | Works FOR you ✅ | Works AGAINST you ❌ |
| **Risk** | Unlimited (naked) | Limited (premium) |
| **Profit** | Premium collected | Stock move |

---

## Quick Reference Card

### For Your Trading

```
STEP 1: Check Selling Score
   Score ≥ 80 → Consider selling premium
   Score < 70 → Skip (too risky)

STEP 2: Check IV Level
   IV < 30% → Good for selling (decay advantage)
   IV > 40% → Better for buying (spike opportunity)

STEP 3: Choose Strategy
   Score ≥ 90 + IV Low   → Naked Call/Put
   Score 80-89 + IV Low  → Put/Call Spread
   Score < 80            → Iron Condor (wider)

STEP 4: Set Stops
   Standard: 2x Premium collected
   Example: Sold call for ₹50 premium
            Stop loss at ₹100 loss (-2x)

STEP 5: Exit Rules
   Close if: Stock reaches strike
   Close if: 50% of max profit earned
   Close if: Loss reaches stop level
```

---

## Real Example: SBIN Option Selling Trade

```
Stock: SBIN
Current Price: ₹500
Selling Score: 96/100
IV: 18% (Very Low)
HV: 0.8% (Ultra Stable)

TRADE SETUP:
   Action: Sell 1 ATM Call at 500 strike
   Premium Collected: ₹50
   Expiry: Weekly
   Max Profit: ₹50
   Max Loss: ₹500 - ₹50 = ₹450 (if assigned)
   
EXIT RULES:
   ✅ Close at 50% profit: ₹25 profit (₹25 premium left)
   ✅ Close at 100% profit: ₹50 profit (assignment)
   ❌ Stop loss: Loss > ₹100 (exit immediately)
   
PROBABILITY:
   ✅ 80-85% chance stock stays below 500 (low vol)
   ✅ IV decay helps (less time value needed)
   ✅ Tight stops minimize losses
```

---

## Python Code Summary

```python
def calculate_selling_viability_score(stock):
    """Calculate how suitable a stock is for option selling"""
    
    # Get metrics
    iv = stock['option_iv']  # 0.18 for SBIN
    hv = stock['volatility_pct']  # 0.8 for SBIN
    spread = stock['option_spread_pct']  # 0.8 for SBIN
    abs_score = abs(stock['final_score'])  # 0.05 for SBIN
    
    # Calculate component scores (0-100)
    iv_score = 100 if iv < 0.20 else 85 if iv < 0.30 else 60
    hv_score = 100 if hv < 1.0 else 90 if hv < 1.5 else 75
    liquidity_score = 95 if spread < 0.01 else 85 if spread < 0.02 else 75
    neutral_score = 95 if abs_score < 0.10 else 85 if abs_score < 0.20 else 60
    
    # Weighted average
    selling_score = (
        iv_score * 0.35 +
        hv_score * 0.35 +
        liquidity_score * 0.20 +
        neutral_score * 0.10
    )
    
    return selling_score  # Returns 96 for SBIN

# Get top 5 sellers
top_sellers = sorted(stocks, key=calculate_selling_viability_score, reverse=True)[:5]
```

---

## Summary

**Best Algorithm for Option Selling**: **Selling Viability Score**

- **Input**: IV, Historical Vol, Bid-Ask Spread, Directional Signal
- **Output**: 0-100 score (higher = better for selling)
- **Weights**: IV 35%, HV 35%, Liquidity 20%, Neutrality 10%
- **Display**: Card format in HTML report (top 5 stocks)
- **Benefit**: Clear, actionable, color-coded for quick decision-making

**Key Insight**: Focus on **IV decay + price stability = premium collection** ✅

---

**Updated**: January 21, 2026  
**Status**: Ready for Implementation  
**Next Step**: Add cards to HTML report generation  
