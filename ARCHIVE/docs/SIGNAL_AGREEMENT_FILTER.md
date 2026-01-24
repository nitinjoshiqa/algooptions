# 🎯 Signal Agreement Filter: Showing Only High-Conviction Setups

## What Changed

**Signal Intelligence section now shows ONLY stocks with strong multi-indicator consensus** (4+ out of 6 signals agreeing).

This reduces clutter and focuses on the highest-quality technical setups.

---

## The 6 Indicators Being Measured

Each stock's "Signal Agree" score counts how many of these 6 indicators show **strong agreement** (>0.3 magnitude):

| Indicator | What It Measures | Example |
|-----------|-----------------|---------|
| **EMA Score** | Trend direction (moving averages) | +0.45 = Strong uptrend |
| **RSI Score** | Momentum & extremes (14-period) | -0.60 = Oversold condition |
| **MACD Score** | Momentum convergence/divergence | +0.38 = Bullish momentum |
| **Structure Score** | Price structure & patterns | +0.42 = Good consolidation |
| **Volume Score** | Volume confirmation (20-period) | +0.65 = Strong volume support |
| **Bollinger Bands Score** | Price extremes vs bands | -0.35 = At band extremes |

---

## Current Filter Threshold

### **4+ out of 6** ← Minimum for cards to display

| Scenario | Result |
|----------|--------|
| **6/6 signals agree** | ⭐⭐⭐⭐⭐ Display card (strongest) |
| **5/6 signals agree** | ⭐⭐⭐⭐ Display card (very strong) |
| **4/6 signals agree** | ⭐⭐⭐ Display card (good) |
| **3/6 signals agree** | ❌ Hidden (moderate consensus) |
| **2/6 signals agree** | ❌ Hidden (weak consensus) |
| **1/6 signals agree** | ❌ Hidden (mixed signals) |

---

## Example: How It Works

### Stock A: COCHINSHIP (Current Status: 0 cards showing today)

```
EMA Score:     +0.48 (>0.3) ✅
RSI Score:     +0.42 (>0.3) ✅  
MACD Score:    -0.15 (<0.3) ❌
Structure:     +0.35 (>0.3) ✅
Volume Score:  +0.68 (>0.3) ✅
BB Score:      +0.22 (<0.3) ❌
                      ─────────────
Signal Agree:  5/6 ⭐⭐⭐⭐
```

**Would Display Card** ✅ (because 5 >= 4)

### Stock B: Example Weak Setup

```
EMA Score:     +0.18 (<0.3) ❌
RSI Score:     +0.25 (<0.3) ❌  
MACD Score:    +0.05 (<0.3) ❌
Structure:     -0.12 (<0.3) ❌
Volume Score:  +0.45 (>0.3) ✅
BB Score:      -0.38 (>0.3) ✅
                      ─────────────
Signal Agree:  2/6 ❌
```

**Would NOT Display Card** (because 2 < 4)

---

## Why This Filter?

| Benefit | Impact |
|---------|--------|
| **Reduces Clutter** | See only highest-conviction setups |
| **Higher Quality Signals** | 4+ indicators agreeing = stronger move |
| **Less False Signals** | Filters out mixed/conflicting setups |
| **Faster Decision Making** | Fewer cards to analyze |
| **Better Risk/Reward** | Strong consensus = more probable moves |

---

## When You'll See Cards

Cards appear in **Signal Intelligence** section **only when:**

✅ Stock selected from top 5 (by confidence × |score|)  
✅ AND NOT flagged as HIGH risk  
✅ AND has 4+ signals agreeing (Signal Agree ≥ 4/6)

---

## What If No Cards Show?

Message displayed:
```
💭 Tip: No stocks currently show 4+ signals agreeing. 
This is a strict filter showing only highest-consensus setups.
```

**This is normal!** It means:
- Market is mixed (few strong multi-indicator setups)
- No clear consensus among major indicators
- Better to wait for stronger setups than trade weak signals

---

## Alternative: Adjusting the Threshold

If you want to see more cards, the threshold can be adjusted:

| Threshold | Result |
|-----------|--------|
| **4/6 (Current)** | Most strict - only best setups |
| **3/6** | More cards shown - good setups |
| **2/6** | Many cards - includes weak setups |

*Current setting: 4/6 (recommended for swing trading)*

---

## Data in CSV

All individual scores are still exported to CSV, so you can:
- ✅ See detailed indicator values
- ✅ Analyze each component
- ✅ Create custom filters
- ✅ Backtest signal combinations

---

## Technical Details

```python
# Signal Agreement Calculation
ema_s, rsi_s, macd_s, struct_s, vol_s, bb_s = [scores from scoring engine]

strong_signals = sum(1 for x in [ema_s, rsi_s, macd_s, struct_s, vol_s, bb_s] 
                     if abs(x) > 0.3)

# Display card only if strong_signals >= 4
if strong_signals >= 4:
    show_card()
```

---

## Quick Reference

**Signal Intelligence Cards Show:**
- Stock with 4+ indicators strongly agreeing
- Top 5 by confidence (primary) × |score| (tiebreaker)  
- Excluding HIGH risk stocks
- With detailed Signal Agree breakdown

**What You See on Card:**
- 🎯 Confidence%
- 📊 Signal Agree (4/6, 5/6, or 6/6)
- 📈 Momentum average
- ✓/✗ Volume support
- ⏱️ Timeframe alignment
- ⚡ Early Signals
- RSI & Volume state

---

**Generated:** Jan 21, 2026  
**Filter Level:** 4/6 signals minimum  
**Universe:** NIFTY200 (154 stocks)  
**Mode:** SWING (50/30/20 weights)
