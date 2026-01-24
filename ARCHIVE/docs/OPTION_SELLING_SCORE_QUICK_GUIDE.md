# Option Selling Score - Quick Reference

## What Is It?
A new **0-1 scale score** added to AlgoOptions screener that measures how suitable a stock is for **selling options premium** (calls/puts).

## Where To Find It

### CSV Report
- New column: `option_selling_score`
- Values: 0.0000 to 0.9999
- Example: SBIN = 0.9850, VOLATILE_STOCK = 0.1350

### HTML Report  
- Column: "Sell Score" (next to "Opt Vega")
- Sortable: Click header to sort high-to-low
- Color-coded: Green (high scores) = better for selling

## Score Meaning

| Score | Quality | Action |
|-------|---------|--------|
| > 0.90 | ⭐⭐⭐⭐⭐ Excellent | Sell naked calls/puts |
| 0.80-0.90 | ⭐⭐⭐⭐ Very Good | Sell naked or wide spreads |
| 0.70-0.80 | ⭐⭐⭐ Good | Sell call/put spreads |
| 0.50-0.70 | ⭐⭐ Moderate | Use wide spreads, manage closely |
| 0.30-0.50 | ⭐ Poor | Use very tight spreads or skip |
| < 0.30 | ❌ Very Poor | Skip - too risky |

## What The Score Considers

✓ **IV (35%)** - How much option premium is available
✓ **Volatility (35%)** - How stable the stock price is
✓ **Liquidity (20%)** - How easy to enter/exit
✓ **Neutrality (10%)** - How directional the signal is

**Higher Score = Lower Risk for Selling Premium**

## Best Stocks for Option Selling
- Score > 0.85 = Tier 1 (SBIN, TCS type)
- Score > 0.75 = Tier 2 (Good quality)
- Score > 0.65 = Tier 3 (Acceptable)

## Examples

**SBIN-like (Blue chip, stable)**
- IV: 18%, Vol: 0.8%, Spread: 0.8%, Neutral
- **Score: 0.9850** ← Excellent for selling

**Mid-cap (Medium quality)**
- IV: 35%, Vol: 1.5%, Spread: 2.5%, Weak signal
- **Score: 0.7075** ← Good for spreads

**Volatile micro-cap**
- IV: 55%, Vol: 3.5%, Spread: 5.5%, Strong signal
- **Score: 0.1350** ← Skip/high risk

## How To Use

### In CSV
1. Open CSV in Excel
2. Sort by option_selling_score (descending)
3. Top stocks = best for selling premium
4. Bottom stocks = avoid for selling

### In HTML Report
1. Open HTML in browser
2. Click "Sell Score" column header
3. Sorts high-to-low automatically
4. Read the scores

### In Your Trading
1. Identify stocks with score > 0.80
2. These stocks have stable options
3. Sell calls/puts for consistent premium
4. Better risk/reward than volatile stocks

## Technical Details

**Calculation:**
```
Score = (IV×0.35) + (HV×0.35) + (Liq×0.20) + (Neutral×0.10)
Range: 0.0 to 1.0
```

**Data Used:**
- option_iv (option implied volatility)
- volatility_pct (historical volatility)
- option_spread_pct (bid-ask spread)
- final_score (price momentum/direction)

**No Existing Fields Modified** - Completely independent new field

## Why This Matters

Traditional selling: Pick any stock, sell options, hope it doesn't move
With this score: Pick stocks with high scores, much safer premium selling

The difference:
- Score > 0.85 stocks: Stable prices, low IV swings = safer selling
- Score < 0.40 stocks: Volatile, wide spreads = risky selling

## Quick Tips

✓ Look for scores > 0.85 first
✓ 0.75-0.85 = Still good, use spreads
✓ < 0.50 = Too risky for beginners
✓ High IV not always bad (if stable & liquid)
✓ Combine with other filters for best results

---

**Questions?** See OPTION_SELLING_SCORE_IMPLEMENTATION.md for detailed guide.
