# Theta Decay Score - Quick Reference

## What Is It?
A new **0-1 scale independent score** based on 4 continuous sub-scores for identifying premium selling opportunities using theta decay.

## When to Use
- **Score > 0.75**: Excellent for naked calls/puts
- **Score 0.60-0.75**: Good for spreads
- **Score 0.45-0.60**: Consider with caution
- **Score 0.00**: Vetoed (skip these)

## The 4 Sub-Scores

### 1. Event Recency (25% weight)
- How many days since last major event?
- 30+ days = 1.0, Today = 0.0
- Older = safer for selling

### 2. Price Stability (35% weight) - MOST IMPORTANT
- Based on historical volatility %
- Vol < 1% = 0.95, Vol > 3% = 0.1
- Lower volatility = safer

### 3. IV/HV Mismatch (25% weight)
- Gap between option IV and stock volatility
- 5-15% gap = Best opportunity (0.9)
- <2% or >20% = Poor (0.1-0.2)
- Mispricing = premium opportunity

### 4. Theta Efficiency (15% weight)
- Absolute theta decay relative to price
- Combined with open interest (liquidity)
- Theta/price > 0.05 = 0.95
- Need OI > 1000 for no penalty

## The 2 Hard Vetoes

| Veto | Trigger | Result | Logic |
|------|---------|--------|-------|
| **Trend** | `\|final_score\| > 0.50` | Score = 0.0 | Strong trends = gap risk |
| **Pattern** | death cross, golden cross, breakout, breakdown | Score = 0.0 | Strong patterns = directional risk |

## Combined Formula

```
THETA_DECAY_SCORE = (
    Event_Recency(0.25) + 
    Price_Stability(0.35) + 
    IV_HV_Mismatch(0.25) + 
    Theta_Efficiency(0.15)
)
```

If trending OR pattern detected → 0.0 (veto)

## Examples

### Example 1: Blue Chip (SBIN-like)
- Consolidation pattern, neutral signal
- Stable (0.9% vol), good IV gap (10%)
- 15 days since event, high OI
- **Score: 0.64** ✓ Good for selling

### Example 2: Trending Stock
- Strong bearish trend (score 0.55)
- **VETO TRIGGERED**
- **Score: 0.00** ✗ Skip

### Example 3: Death Cross Pattern
- Neutral signal, stable stock
- But death cross pattern detected
- **VETO TRIGGERED**
- **Score: 0.00** ✗ Skip

### Example 4: High Volatility
- Neutral signal, 3.5% volatility
- Recent event (1 day old)
- Low OI (illiquid)
- **Score: 0.11** ✗ Too risky

## Where It Appears

- **CSV**: New column "theta_decay_score"
- **HTML**: Column "Theta Score" (sortable)
- **Code**: Access via `result['theta_decay_score']`

## How to Use

### Best Candidates
Sort by Theta Score (descending):
- 0.75+: Buy these
- 0.60-0.75: Good alternatives
- 0.00: Skip (vetoed)

### Decision Logic
```python
if score == 0.0:
    Skip (trending or bad pattern)
elif score > 0.75:
    Excellent for selling premium
elif score > 0.60:
    Good - use spreads
elif score > 0.45:
    Consider - narrow margins
else:
    Skip - too risky
```

## Key Insight

**Price Stability (35% weight) is most important**
- Lower volatility = safer for premium sellers
- Even with good IV gap, high volatility kills the score
- This reflects reality: stable stocks = consistent theta decay

## Technical Details

| Aspect | Detail |
|--------|--------|
| **Range** | 0.0 to 1.0 |
| **Type** | Fuzzy (continuous) |
| **Vetoes** | 2 hard vetoes only |
| **Independence** | Separate from final_score |
| **Data Needed** | final_score, pattern, volatility, IV, theta, OI, price |
| **Calculation** | ~1ms per stock |
| **Default Handling** | Returns 0.0 if data missing |

## Differences from Option Selling Score

| Aspect | Theta Score | Selling Score |
|--------|-------------|---------------|
| **Focus** | Theta decay opportunity | Premium selling safety |
| **Sub-scores** | Event, Stability, IV/HV, Theta | IV, HV, Liquidity, Neutral |
| **Vetoes** | 2 (trending, patterns) | None (continuous) |
| **Best Use** | Time decay strategies | Conservative selling |
| **Weight** | Stability 35% | All ~25% each |

## Summary

- **4 continuous sub-scores** + **2 hard vetoes**
- **35% weight on stability** (most important)
- **0.0 if trending or bad pattern**
- **Higher score = better for theta selling**
- **Completely independent** from other scores

**Use it to identify best premium selling opportunities based on decay potential!**
