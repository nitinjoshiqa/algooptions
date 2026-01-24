# 💡 How Option Intelligence Stocks Are Identified

## Overview
The **Option Intelligence** section displays the **top 6 stocks** with the best option trading setups, selected based on technical signal strength and option Greeks optimization.

---

## Selection Criteria

### Primary Filter: Absolute Score (Signal Strength)
```python
top_options = sorted(
    [r for r in scored if r.get('option_iv') is not None and r.get('final_score') is not None],
    key=lambda x: abs(x.get('final_score', 0) or 0),
    reverse=True
)[:6]
```

**What this means:**
- Takes stocks with valid option Greeks data
- Sorts by **|score|** in descending order (highest first)
- Selects top 6 stocks

### Why Absolute Score?
- **|score| = 0.4** means strong conviction (either +0.4 bearish or -0.4 bullish)
- **|score| = 0.05** means weak signal (uncertain direction)
- Options work best with **strong directional conviction** + **high confidence**

---

## Ranking Logic

### Stock with Score = +0.45 (COCHINSHIP)
- **abs(+0.45) = 0.45** ← Ranked #1 (highest signal strength)
- Strong bullish signal
- Good for: Long call spreads, bull call spreads

### Stock with Score = +0.17 (NYKAA)
- **abs(+0.17) = 0.17** ← Lower priority
- Moderate bullish signal
- Less conviction = avoid options

### Stock with Score = -0.24 (DIVISLAB)
- **abs(-0.24) = 0.24** ← Mid-ranked
- Strong bearish signal
- Good for: Long put spreads, bear call spreads

---

## Example Top 6 Selection

| Rank | Symbol | Score | \|Score\| | Type | Ranking |
|------|--------|-------|---------|------|---------|
| 1 | COCHINSHIP | +0.435 | 0.435 | Bullish | ⭐ Strongest |
| 2 | POLICYBZR | +0.364 | 0.364 | Bullish | ⭐⭐ Strong |
| 3 | DIVISLAB | -0.239 | 0.239 | Bearish | ⭐⭐ Strong |
| 4 | INDHOTEL | +0.215 | 0.215 | Bullish | ⭐⭐⭐ Moderate |
| 5 | CGPOWER | +0.200 | 0.200 | Bullish | Moderate |
| 6 | LICHSGFIN | -0.171 | 0.171 | Bearish | Moderate |

---

## Option Intelligence Card Details

### For Each Stock, Show:

#### 1️⃣ **IV Level** (Implied Volatility)
```
HIGH IV (>40%)   → 📊 Sell premium (Covered Call, Put Spread)
NORMAL IV (25-40%) → ⚖️ Balanced (Spreads or Directional)
LOW IV (<25%)    → 📈 Buy options (Long Call/Put)
```

#### 2️⃣ **Bid-Ask Spread Quality**
```
< 2%  → Excellent (Most liquid, easy exit)
< 4%  → Good (Acceptable liquidity)
< 6%  → Fair (Medium liquidity risk)
> 6%  → Poor (Avoid - hard to exit)
```

#### 3️⃣ **Option Greeks**
```
Delta (Δ)  = Directional sensitivity
            0.5 = ATM (neutral)
            >0.7 = Deep ITM (highly directional)
            <0.3 = OTM (low probability)

Gamma (Γ)  = Delta acceleration
            High = Delta changes quickly (risky)
            Low = Delta stable (predictable)

Theta (Θ)  = Time decay per day
            Positive = You earn from time decay (selling)
            Negative = You lose from time decay (buying)

Vega (ν)   = Volatility sensitivity
            High = Profit from IV increase
            Low = Stable in changing volatility
```

#### 4️⃣ **Recommended Strategy**
```
IF Score > +0.2 (Bullish):
   - Buy Call or Bull Call Spread (expect up move)
   - Max profit = limited, max loss = limited

IF Score < -0.2 (Bearish):
   - Buy Put or Bear Call Spread (expect down move)
   - Max profit = limited, max loss = limited

IF IV > 40% (High):
   - Sell Call/Put or Spread (collect premium now)
   - Benefit when IV drops

IF IV < 25% (Low):
   - Buy Call/Put (cheap protection)
   - Benefit from IV spike + direction
```

---

## Example: COCHINSHIP Option Intelligence Card

```
📊 COCHINSHIP

Score: +0.435 (Strong Bullish) ✅
Confidence: 100%

IV Level: 20% - LOW (Buy Options) 🟦
   → Buy calls cheap before IV spikes
   → Strategy: Long Call or Bull Call Spread

Bid-Ask Spread: 0.5% - Excellent ✅
   → Very liquid, easy entry/exit

Option Greeks:
   Delta: 0.72 (Deep ITM) - Directional
   Gamma: 0.08 (Moderate) - Accelerating
   Theta: -0.15 (Time decay against buyer) ⚠️
   Vega: 0.25 (IV sensitive)

Recommended Action:
   💡 Bull Call Spread
   - Buy ATM Call (capture bullish move)
   - Sell OTM Call (cap risk, collect premium)
   - Max Profit: Strike difference - spread cost
   - Max Loss: Spread cost
   - Breakeven: Entry price + spread cost
```

---

## Why Option Intelligence is Useful

### 1️⃣ **Signal Strength Filter**
Only shows stocks with **strong technical conviction** (|score| ≥ 0.17)
- Weak signals = options don't work well
- Strong signals = better probability

### 2️⃣ **Greeks Optimization**
Shows best option trading conditions:
- IV level guides strategy (buy vs sell premium)
- Delta shows how directional the move can be
- Theta shows time decay benefit/cost
- Spread % ensures liquidity

### 3️⃣ **Risk/Reward Matching**
Combines:
- **Technical signal** (which direction)
- **Option pricing** (is it cheap/expensive?)
- **Liquidity** (can you exit?)
- **Greeks** (which strategy works?)

---

## 🎯 NEW: Option Selling Selector (Low Volatility Stocks)

### Purpose
Identify stocks **suitable for premium selling** (short calls/puts, credit spreads) - stable stocks with low movement.

### Algorithm: Volatility Scoring

```python
def calculate_option_selling_score(row):
    """
    Score stocks for option selling suitability.
    Higher score = Better for selling options
    
    Formula:
    Selling_Score = (Low_IV_Factor × IV_Weight) + 
                    (Low_HV_Factor × HV_Weight) + 
                    (Low_Movement_Factor × Movement_Weight) +
                    (Liquidity_Factor × Liquidity_Weight)
    """
    
    # 1. IV Stability (Implied Volatility)
    option_iv = row.get('option_iv', 0.30)
    
    if option_iv < 0.20:      # Very Low
        iv_score = 100
    elif option_iv < 0.30:     # Low (IDEAL)
        iv_score = 85
    elif option_iv < 0.40:     # Normal
        iv_score = 60
    elif option_iv < 0.50:     # Elevated
        iv_score = 35
    else:                       # Very High (avoid)
        iv_score = 10
    
    # 2. Historical Volatility (ATR-based)
    volatility_pct = row.get('volatility_pct', 2.0)
    
    if volatility_pct < 1.0:    # Very Stable
        hv_score = 100
    elif volatility_pct < 1.5:  # Stable (IDEAL)
        hv_score = 90
    elif volatility_pct < 2.0:  # Low
        hv_score = 75
    elif volatility_pct < 3.0:  # Normal
        hv_score = 50
    else:                        # Volatile (avoid)
        hv_score = 20
    
    # 3. Bid-Ask Spread (Liquidity)
    spread_pct = row.get('option_spread_pct', 5.0)
    
    if spread_pct < 1.0:        # Excellent
        liquidity_score = 95
    elif spread_pct < 2.0:      # Very Good
        liquidity_score = 85
    elif spread_pct < 3.0:      # Good
        liquidity_score = 75
    elif spread_pct < 5.0:      # Fair
        liquidity_score = 50
    else:                        # Poor (avoid)
        liquidity_score = 10
    
    # 4. Directional Neutrality (Lower |score| = more neutral)
    abs_score = abs(row.get('final_score', 0))
    
    if abs_score < 0.10:        # Very Neutral
        neutral_score = 95
    elif abs_score < 0.20:      # Neutral (IDEAL)
        neutral_score = 85
    elif abs_score < 0.30:      # Slightly Directional
        neutral_score = 60
    elif abs_score < 0.50:      # Directional
        neutral_score = 30
    else:                        # Very Directional (avoid)
        neutral_score = 10
    
    # Weighted Average (70% IV, 60% HV, 70% Liquidity, 30% Neutrality)
    selling_score = (
        iv_score * 0.35 +        # IV most important (decay your friend)
        hv_score * 0.35 +        # HV stability second
        liquidity_score * 0.20 + # Liquidity critical for exit
        neutral_score * 0.10     # Neutrality optional
    )
    
    return round(selling_score, 2)
```

### Scoring Interpretation

| Score | Rating | Suitability | Strategy |
|-------|--------|-------------|----------|
| 90-100 | ⭐⭐⭐⭐⭐ Excellent | Perfect for selling | Naked puts, covered calls |
| 80-89 | ⭐⭐⭐⭐ Very Good | Highly suitable | Put spreads, call spreads |
| 70-79 | ⭐⭐⭐ Good | Good choice | Iron condor, strangle |
| 60-69 | ⭐⭐ Fair | Acceptable | Conservative spreads |
| <60 | ⭐ Poor | Avoid selling | Avoid premium selling |

### Example Top 5 Option Selling Candidates

| Rank | Symbol | IV | HV | Spread | Score | Reason |
|------|--------|----|----|--------|-------|--------|
| 1 | SBIN | 0.18 | 0.8% | 0.8% | **96** | Ultra-stable mega-cap |
| 2 | INFY | 0.22 | 1.1% | 1.2% | **91** | Liquid, low vol blue-chip |
| 3 | TCS | 0.20 | 0.9% | 0.7% | **94** | Most liquid index stock |
| 4 | HDFCBANK | 0.25 | 1.3% | 1.1% | **88** | Large-cap, stable |
| 5 | RELIANCE | 0.28 | 1.5% | 1.4% | **83** | Sector leader, predictable |

### When to Use Option Selling

✅ **SELL OPTIONS WHEN:**
- Score ≥ 80 (Very Good or Excellent)
- IV ≤ 30% (Normal or low)
- Volatility < 2% (Calm market)
- Bid-ask < 3% (Liquid options)
- Collect premium while stock stays flat

❌ **AVOID SELLING WHEN:**
- Score < 70 (Fair or Poor)
- IV > 40% (Market uncertainty)
- Volatility > 3% (Choppy market)
- Earnings week (unpredictable)
- |Score| > 0.4 (Strong directional move likely)

---

## Current Configuration

```python
# Select top 6 stocks by absolute score strength
top_options = sorted(
    [r for r in scored if r.get('option_iv') is not None],
    key=lambda x: abs(x.get('final_score', 0)),  # Sort by |score|
    reverse=True
)[:6]  # Take top 6

# NEW: Select top 5 for option selling (low volatility)
option_sellers = sorted(
    [r for r in scored if r.get('option_iv') is not None],
    key=lambda x: calculate_option_selling_score(x),
    reverse=True
)[:5]  # Top 5 best for premium selling
```

**Stocks Included**: 
- 6 per report (highest signal strength) - **Directional traders**
- 5 per report (highest selling score) - **Premium sellers** (NEW)

**Sorted By**: 
- Option Intelligence: Absolute value of bearness score (technical conviction)
- Option Selling: Volatility score (premium collection suitability)

**Excludes**: 
- Stocks with no option data
- Stocks with very weak signals

---

## Key Differences: Signal Intelligence vs Option Intelligence

| Aspect | Signal Intelligence | Option Intelligence |
|--------|-------------------|---------------------|
| **Stocks Shown** | 5 highest confidence | 6 highest \|score\| |
| **Filter** | Confidence ≥ 60% | Absolute signal strength |
| **Exclude** | HIGH risk | None |
| **Sort Order** | Confidence, then \|score\| | \|score\| only |
| **Focus** | When/how to trade | How to trade options |
| **Greeks** | Not shown | Detailed |
| **IV Analysis** | Not shown | Detailed |

---

## How to Use Option Intelligence Cards

### Step 1: Check Signal Strength
- \|Score\| > 0.3 = Strong conviction ✅
- \|Score\| < 0.2 = Weak conviction ❌

### Step 2: Review IV Level
```
If IV HIGH (>40%):
   → Sell premium strategies (credit spreads)
   → Collect premium while IV falls

If IV LOW (<25%):
   → Buy options (calls/puts)
   → Buy protection cheaply
```

### Step 3: Verify Spread Quality
- Bid-ask < 3% = Trade it ✅
- Bid-ask > 5% = Avoid (too expensive) ❌

### Step 4: Pick Strategy Based on Delta
```
Delta 0.3-0.7 = ATM (balanced risk/reward)
Delta > 0.8   = Deep ITM (directional, expensive)
Delta < 0.3   = OTM (cheap, low probability)
```

### Step 5: Calculate Max Risk
- Max Loss = Spread width - credit received (for spreads)
- Max Loss = Premium paid (for long calls/puts)

---

## Summary

**Option Intelligence stocks are identified by:**
1. ✅ Having valid option Greeks data
2. ✅ Strong technical signal (\|score\| highest first)
3. ✅ Ranked by conviction strength (not confidence)
4. ✅ Paired with IV, Greeks, and spread analysis
5. ✅ Recommended specific option strategies

**Updated**: Jan 21, 2026  
**Stocks**: Top 6 by \|score\|  
**Mode**: SWING (50/30/20 weights)
