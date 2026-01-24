# 📋 Strategy Recommendation Logic: Main Table vs Option Intelligence

## Quick Answer

**NO** - The strategies in the **main screener table** and **Option Intelligence section** use **DIFFERENT selection logic**:

| Aspect | Main Table Strategy | Option Intelligence |
|--------|-------------------|---------------------|
| **Selection Criteria** | ALL 154 stocks | Top 6 by \|score\| |
| **Sort Order** | Shows for every stock | Only highest signal strength |
| **Logic** | Individual strategy recommendation | Ranked by conviction level |
| **Filter** | All stocks (no filter) | Highest technical conviction |

---

## Main Table Strategy: Individual Recommendation Logic

### For EVERY stock in the table, the system recommends a strategy based on:

```python
suggest_option_strategy(
    is_bullish,      # Score > +0.05?
    is_bearish,      # Score < -0.05?
    volatility_pct,  # ATR/Price (1-4% typical)
    conf_val,        # Confidence 0-100%
    abs_score,       # |Score| magnitude
    option_score     # Liquidity score
)
```

### Decision Tree Example:

```
For COCHINSHIP (Score: +0.413, Conf: 100%, Vol: 0.5%, Abs Score: 0.413)

Step 1: Check liquidity gate
├─ option_score > -0.3? → YES ✅ (Good liquidity)

Step 2: Is it bullish? (score > 0.05)
├─ YES ✅ (score = +0.413)

Step 3: Check volatility level
├─ volatility_pct (0.5%) < 1.5%? → YES (LOW volatility)

Step 4: Check confidence
├─ conf_val (100%) >= 60%? → YES ✅ (High confidence)

Step 5: Apply bullish rules
├─ low_vol AND high_conf?
├─ → Return "Call Diagonal"
```

---

## Strategy Selection Rules

### Bullish Signals (Score > +0.05)

```
HIGH Vol (>3.5%) + HIGH Conf (≥60%) + STRONG Signal (|score|≥0.15)
├─ → Long Call Spread 🎯
│   (Wide profitable zone, defined risk)
│
HIGH Vol + MED Conf
├─ → Bull Call 🎯
│   (Narrow strikes, limited loss)
│
MED Vol (1.5-3.5%) + HIGH Conf
├─ → ATM Call 🎯
│   (Balanced delta 0.50, best timing)
│
LOW Vol (<1.5%) + HIGH Conf
├─ → Call Diagonal ✅
│   (Long-dated call, sell short call)
│
LOW Vol + MED Conf
├─ → Call Calendar ✅
│   (Theta positive, benefits from time decay)
│
Default
└─ → Long Call
    (Simple directional play)
```

**Example**: COCHINSHIP
- Vol: 0.5% (LOW) ✓
- Conf: 100% (HIGH) ✓
- → **Call Diagonal** (best for this profile)

---

### Bearish Signals (Score < -0.05)

```
HIGH Vol + HIGH Conf + STRONG Signal
├─ → Put Spread 📉
│   (Best risk/reward on big moves down)
│
HIGH Vol + MED Conf
├─ → Bear Put 📉
│   (Collect premium on downside)
│
MED Vol + HIGH Conf
├─ → ATM Put 📉
│   (Balanced protective put)
│
LOW Vol + HIGH Conf
├─ → Put Diagonal
│   (Long-dated put, sell short put)
│
LOW Vol + MED Conf
└─ → Put Calendar
    (Time decay benefits seller)
```

**Example**: DIVISLAB
- Vol: ~0.4% (LOW) ✓
- Conf: 64% (HIGH) ✓
- Score: -0.239 (BEARISH) ✓
- → **Put Diagonal** (best for low volatility bearish setup)

---

### Neutral Signals (No Clear Direction)

```
HIGH Vol + HIGH Conf
├─ → Iron Condor 🔄
│   (Sell strangle, collect premium on range)
│
HIGH Vol only
├─ → Straddle 🔄
│   (Buy call + put, profit from big move)
│
MED Vol + HIGH Conf
├─ → Strangle 🔄
│   (Cheaper version of straddle)
│
LOW Vol only
└─ → Covered Call
    (Own stock, sell upside)
```

---

## Option Intelligence Section: Selection-Based Logic

### Different Approach: **Rank by Conviction, Not Individual Recommendation**

```python
# OPTION INTELLIGENCE: Top 6 by signal strength
top_options = sorted(
    [stocks with valid option data],
    key=lambda x: abs(x['final_score']),  # ← Ranked by |score|
    reverse=True
)[:6]
```

**Why different?**
1. **Option Intelligence** = "Which stocks have the STRONGEST signals?" → Sort by |score|
2. **Main Table Strategy** = "For THIS stock, what strategy works best?" → Individual logic

---

## Detailed Strategy Parameters

### Signal Strength Requirements

```
strong_signal = abs_score >= 0.15

Examples:
├─ COCHINSHIP: |+0.413| = 0.413 → STRONG ✅
├─ POLICYBZR: |+0.364| = 0.364 → STRONG ✅
├─ DIVISLAB:  |-0.239| = 0.239 → STRONG ✅
├─ NYKAA:     |+0.170| = 0.170 → STRONG ✅
├─ INFY:      |+0.171| = 0.171 → STRONG ✅
└─ ASHOKLEY:  |+0.180| = 0.180 → STRONG ✅
```

### Volatility Classifications

```
HIGH Vol (>3.5%)
├─ Example: COCHINSHIP (ATR/Price = 0.5%) = 0.5%
├─ Recommendation: Sell premium or spreads
├─ Reason: Low vol → Time decay benefits seller

MED Vol (1.5%-3.5%)
├─ Example: Most stocks fall here
├─ Recommendation: Balanced spreads
├─ Reason: Medium time decay + directional

LOW Vol (<1.5%)
├─ Example: Most blue chips
├─ Recommendation: Diagonals or calendars
├─ Reason: Very low time decay, need timing
```

### Confidence Thresholds

```
HIGH Conf ≥60%
├─ All top-5 Signal Intelligence stocks
├─ Use aggressive strategies
├─ Examples: Long Call, Put Spread

MED Conf 40-60%
├─ Use balanced strategies
├─ Examples: Bull Call, Bear Put

LOW Conf <40%
├─ Avoid options or use very wide spreads
├─ Stick with simple directional plays
```

### Liquidity Gate (Option Score)

```
option_score < -0.3  → NO-TRADE ❌
├─ Options too expensive/illiquid
├─ Recommendation: Skip or use equity instead

option_score -0.3 to +0.3 → CAUTION ⚠️
├─ Marginal liquidity
├─ Use wide spreads only

option_score > +0.3 → GO ✅
├─ Good liquidity
├─ Any strategy allowed
```

---

## Example: How Strategies Differ

### COCHINSHIP (Strong Bullish, Low Vol, High Conf)

#### Main Table Strategy (Individual Recommendation)
```
Input:
├─ is_bullish: YES (score +0.413)
├─ volatility_pct: 0.5% (LOW)
├─ conf_val: 100% (HIGH)
├─ abs_score: 0.413 (STRONG)

Decision Tree:
├─ Not (HIGH Vol AND HIGH Conf AND STRONG Signal) → No
├─ Not (HIGH Vol AND MED Conf) → No
├─ Not (MED Vol AND HIGH Conf) → No
├─ YES: (LOW Vol AND HIGH Conf) → MATCH ✓

Output: "Call Diagonal" ✅
Reason: Low volatility + high confidence = need timing, not premium collection
```

#### Option Intelligence (Ranked Selection)
```
Ranking by |score|:
1. COCHINSHIP: |+0.413| = 0.413 ← SELECTED for Option Intelligence ⭐
2. POLICYBZR: |+0.364| = 0.364 ← SELECTED ⭐
3. DIVISLAB: |-0.239| = 0.239 ← SELECTED ⭐
...
6. [6th highest |score|] ← SELECTED ⭐
7. NYKAA: |+0.170| = 0.170 ← NOT selected (7th)

Reason: Option Intelligence shows ONLY top 6 by signal strength
```

---

## Why Two Different Approaches?

### Main Table Strategy (All 154 Stocks)
**Purpose**: Help decide what to do with ANY stock
- Covers every possible scenario
- Adapts to each stock's characteristics
- Shows strategy for weak signals too
- Comprehensive coverage

### Option Intelligence (Top 6 Only)
**Purpose**: Highlight best opportunities
- Focus on strong signals only
- Shows detailed Greeks analysis
- Easier decision-making (fewer options)
- Quality over quantity

---

## Summary: Key Differences

| Aspect | Main Table | Option Intelligence |
|--------|-----------|---------------------|
| **Stocks Included** | ALL 154 | Top 6 by \|score\| |
| **Logic Type** | Decision tree (which strategy?) | Ranking (which stocks?) |
| **Input Variables** | Direction, vol, confidence, liquidity | Score magnitude only |
| **Output** | 1 strategy per stock | Ranked list with details |
| **Filters Applied** | Liquidity gate only | Liquidity gate + strength gate |
| **Use Case** | "How do I trade THIS stock?" | "Which stocks should I focus on?" |

---

## When to Use Which?

### Use Main Table Strategy When:
- ✅ You've picked a specific stock
- ✅ You want to know the best option strategy for it
- ✅ You need to adapt to volatility/confidence
- ✅ You want all 154 stocks covered

### Use Option Intelligence When:
- ✅ You want top quality setups only
- ✅ You need detailed Greeks analysis
- ✅ You want to see IV/spread opportunities
- ✅ You're short on time (focus on 6 best)

---

**Generated**: Jan 21, 2026  
**Mode**: SWING (50/30/20 weights)  
**Total Stocks**: 154  
**Option Intelligence Stocks**: 6 (top by |score|)
