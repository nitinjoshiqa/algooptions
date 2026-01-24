# 🎯 Option Selling Algorithm - Quick Reference Card

## One-Page Summary

### THE PROBLEM
How do you pick stocks suitable for **selling options** (collecting premiums)?
- Need **low volatility** (stock stays flat = premium safe)
- Need **good liquidity** (can exit easily)
- Need **low IV** (premium decay helps you)

### THE SOLUTION
**Selling Viability Score** (0-100 scale)

---

## SCORING FORMULA

```
SCORE = (IV_Score × 0.35) + (HV_Score × 0.35) + (Liquidity × 0.20) + (Neutral × 0.10)
```

**Simple Interpretation:**
- Higher score = Better for selling options
- Score ≥ 80 = Safe to sell
- Score < 70 = Avoid selling

---

## FOUR KEY METRICS

| Metric | What | Weight | Good Value | Bad Value |
|--------|------|--------|-----------|-----------|
| **IV** | Option pricing volatility | 35% | < 30% | > 40% |
| **HV** | Actual price movement | 35% | < 1.5% | > 3% |
| **Spread** | Bid-ask gap | 20% | < 2% | > 5% |
| **Signal** | Direction bias (\|score\|) | 10% | < 0.2 | > 0.5 |

---

## QUALITY RATINGS

```
Score Range    | Rating         | Strategy          | Risk
≥ 90           | ⭐⭐⭐⭐⭐ EXC | Naked/Call/Put    | Very Low ✅
80-89          | ⭐⭐⭐⭐ VG   | Put/Call Spreads  | Low ✅
70-79          | ⭐⭐⭐ G      | Conservative      | Moderate ⚠️
60-69          | ⭐⭐ F        | Not suitable      | High ❌
< 60           | ⭐ P          | AVOID             | Very High ❌
```

---

## TYPICAL TOP 5 CANDIDATES

| Rank | Stock | IV | HV | Spread | Score | Action |
|------|-------|----|----|--------|-------|--------|
| 1 | SBIN | 18% | 0.8% | 0.8% | 96 | Naked |
| 2 | TCS | 20% | 0.9% | 0.7% | 94 | Naked |
| 3 | INFY | 22% | 1.1% | 1.2% | 91 | Spreads |
| 4 | HDFCBANK | 25% | 1.3% | 1.1% | 88 | Spreads |
| 5 | RELIANCE | 28% | 1.5% | 1.4% | 83 | Conservative |

---

## DECISION TREE

```
START: Check Selling Score
│
├─ Score ≥ 90? ✅
│  ├─ IV < 25%? ✅ → SELL NAKED (highest profit)
│  └─ IV 25-35%? ✅ → SELL NAKED or SPREAD (good)
│
├─ Score 80-89? ✅
│  ├─ IV < 30%? ✅ → SELL SPREADS (safe)
│  └─ IV > 30%? ⚠️  → SELL CONSERVATIVE SPREAD
│
├─ Score 70-79? ⚠️
│  └─ Only use WIDE SPREADS (larger cushion needed)
│
└─ Score < 70? ❌
   └─ SKIP (too risky for selling)
```

---

## ENTRY CHECKLIST

Before selling options, verify ALL:

- [ ] Selling Score ≥ 80
- [ ] IV ≤ 30% (not elevated)
- [ ] Bid-Ask Spread < 3% (liquid)
- [ ] Stock not near earnings
- [ ] Not entering earnings week
- [ ] Technical support/resistance clear
- [ ] No breaking news expected
- [ ] Days to expiry > 5

If ANY fails → SKIP TRADE

---

## STRATEGY SELECTION

### Score ≥ 90 (Excellent)
✅ **Naked Put or Naked Call**
- Sell 1 ATM (At The Money) option
- Collect full premium
- Maximum profit but naked risk
- Best for: Very stable mega-caps (SBIN, TCS)

✅ **Covered Call**
- Sell call against 100 shares owned
- Collect premium + potential capital gains
- Unlimited downside risk (but own shares)

### Score 80-89 (Very Good)
✅ **Put Spread**
- Sell 1 higher strike put
- Buy 1 lower strike put
- Limited risk = more sleep at night
- Example: Sell 1800 put, Buy 1750 put (₹50 width)

✅ **Call Spread**
- Sell 1 OTM call
- Buy 1 higher strike call
- Cap profit but also cap risk

✅ **Iron Condor**
- Sell call spread + sell put spread
- Profit from stock staying in middle
- Requires score ≥ 85

### Score < 80 (Poor)
❌ **Don't sell** - Use directional long strategies instead

---

## POSITION SIZING

```
Risk per trade = Account × 2%

Example:
Account: ₹100,000
Risk: ₹2,000
Stock: SBIN, Option: Sell 1 Call
Premium: ₹50
Loss limit: ₹100 (2x premium for buffer)

Each option = 100 shares
Contracts to sell = Risk / Loss per point
                 = ₹2,000 / ₹100 = 20 shares worth
                 = 0.2 contracts ≈ Skip this (too small)

Better: Sell 1 contract = ₹5,000 risk (5% account)
       Then adjust account size up or use spreads
```

---

## EXIT RULES

### Close Winning Trade At:
```
✅ 50% of max profit reached
   Example: Sold call for ₹50, close at ₹25 profit

✅ 100% of max profit (assignment/expiry)
   Example: Stock stays below strike, keep ₹50

✅ 5 days before expiry (reduce gamma risk)
   Example: Weekly option, close on Wed if profitable
```

### Close Losing Trade At:
```
❌ Stop loss triggered (predefined)
   Example: Sold call for ₹50, max loss = ₹100

❌ Directional signal reverses (stock breaking setup)
   Example: Sold call but stock breaks support = exit

❌ IV spikes > 40% (gamma risk too high)
   Example: Earnings coming, close position
```

---

## COMMON MISTAKES TO AVOID

| ❌ Mistake | Why Wrong | ✅ Fix |
|-----------|-----------|-------|
| Sell without score check | Risky stocks | Check score ≥ 80 first |
| Ignore bid-ask spread | Can't exit | Only trade spread < 3% |
| Sell all premium | No buffer | Close at 50% profit |
| Moving stop loss up | Converts winner to loser | Set SL and forget it |
| Sell near earnings | Gap risk | Check calendar first |
| Selling too many contracts | Account blowup risk | Stick to 2% per trade |
| Ignoring IV spikes | Gamma risk explosion | Exit if IV > 40% |
| Trading illiquid options | Can't exit at will | Only liquid stocks |

---

## CHECKLIST: IS THIS STOCK GOOD TO SELL?

```
Stock: ________  Date: ________  Price: ________

METRIC CHECKLIST:
□ Selling Score ____/100 (≥80? YES/NO)
□ IV ___% (≤30%? YES/NO)
□ HV ___% (<1.5%? YES/NO)
□ Bid-Ask Spread __% (<3%? YES/NO)
□ Signal ±____ (<0.2? YES/NO)

CALENDAR CHECKLIST:
□ No earnings this month? YES/NO
□ Days to expiry _____ (>5? YES/NO)
□ No major events? YES/NO

TECHNICAL CHECKLIST:
□ Not at resistance? YES/NO
□ Not at support? YES/NO
□ Chart looks healthy? YES/NO

DECISION:
If all YES → ✅ SAFE TO SELL
If any NO  → ❌ SKIP THIS TRADE
```

---

## QUICK MENTAL MATH

**Question**: Sold 1 call for ₹50, want to know max profit/loss

**Answer**:
- Max Profit = ₹50 (premium collected)
- Max Loss = Unlimited (naked) or Width - Credit (spreads)
- Breakeven = Strike + Premium (for put seller)

**Example**:
```
Sell 1 call at 500 strike for ₹50
Max Profit: ₹50 (if stock ≤ 500 at expiry)
Max Loss: Unlimited (if stock goes to 1000)
Breakeven: Not applicable (seller wins if ≤ 500)
```

---

## VOCABULARY

| Term | Meaning |
|------|---------|
| **IV** | Implied Volatility - option market expects this much movement |
| **HV** | Historical Volatility - stock actually moved this much |
| **ATM** | At The Money - strike = current stock price |
| **OTM** | Out of The Money - strike further from money (less risky) |
| **ITM** | In The Money - strike closer to assignment |
| **Spread** | Gap between bid (buy) and ask (sell) prices |
| **Assignment** | You're forced to buy (put) or sell (call) shares |
| **Decay** | Theta decay - premium value decreases (good for sellers) |
| **Gap** | Stock opens at price far from close (risky for sellers) |

---

## SIMPLE RULE

```
FOR OPTION SELLING:

IF Score ≥ 80 AND IV ≤ 30% AND Spread < 3%
   THEN → Safe to sell options ✅
   
ELSE
   THEN → Skip this stock ❌

That's it!
```

---

## COLOR QUICK REFERENCE

```
🟢 GREEN    = Good (IV low, Vol stable, Spread tight)
🟡 YELLOW   = Caution (Mix of good and okay metrics)
🟠 ORANGE   = Warning (Some metrics not ideal)
🔴 RED      = Avoid (IV high, Vol high, or poor spread)
```

---

## CARD MEANINGS AT A GLANCE

```
WHEN YOU SEE:

🟢 SBIN, Score 96, ⭐⭐⭐⭐⭐
→ Perfect for naked selling

🟢 INFY, Score 91, ⭐⭐⭐⭐
→ Great for spreads

🟡 Stock below 80, ⭐⭐⭐
→ Only if you want conservative wide spreads

🔴 Stock below 70, ⭐⭐
→ Don't sell (better to buy options instead)
```

---

## QUICK LINKS TO FULL DOCS

| Need | File |
|------|------|
| Complete algorithm | `OPTION_SELLING_BEST_ALGORITHM.md` |
| Card visual guide | `OPTION_SELLING_VISUAL_GUIDE.md` |
| Python code | `OPTION_SELLING_IMPLEMENTATION.md` |
| Trading examples | `OPTION_SELLING_COMPLETE_SUMMARY.md` |
| Design details | `OPTION_SELLING_CARD_DESIGN.md` |
| This card | `OPTION_SELLING_QUICK_REFERENCE.md` |

---

## 30-SECOND SUMMARY

> **Problem**: Hard to pick stocks for option selling  
> **Solution**: Selling Viability Score (0-100)  
> **Formula**: IV (35%) + HV (35%) + Liquidity (20%) + Neutral (10%)  
> **Threshold**: Score ≥ 80 = Safe to sell  
> **Display**: Color-coded cards in HTML report  
> **Benefit**: Identifies low-volatility, liquid stocks for income trading  

---

## PRINT THIS CARD

📎 Save as PDF or print for your desk!

Use this when:
- Evaluating a stock for option selling
- Checking if report score is safe
- Remembering which metrics matter
- Training a trader on the system

---

*Quick Reference Card - Option Selling Algorithm*  
*Created: January 21, 2026*  
*Print, Save, Share* ✅  

