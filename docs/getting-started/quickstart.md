# Quick Start Guide

Get started with AlgoOptions in **5 minutes**.

## 1. Run Your First Screener (2 min)

```bash
# Activate virtual environment
.venv\Scripts\activate

# Run NIFTY 200 analysis
python nifty_bearnness_v2.py --universe nifty200 --mode swing --screener-format html
```

**Output:**
- `nifty_bearnness.html` - Interactive report (open in browser)
- `nifty_bearnness.csv` - Raw data for spreadsheets

---

## 2. Understand the Report (2 min)

### What You'll See:

| Column | Meaning |
|--------|---------|
| **Symbol** | Stock ticker (RELIANCE, INFY, etc.) |
| **Score** | -1 (bearish) to +1 (bullish) |
| **Conf%** | How confident is the signal (0-100%) |
| **Price** | Current price in INR |
| **Stop Loss** | Where to exit if wrong |
| **Target** | Where profit target is |
| **R:R** | Risk-to-reward ratio (want 1.5+) |
| **Pos Size** | Suggested shares for 2% risk |
| **Risk Zone** | NORMAL/MEDIUM/HIGH volatility |

### Green vs Red Colors:
- 🟢 **Green background** = Bullish stocks
- 🔴 **Red background** = Bearish stocks
- ⚪ **White background** = Neutral

---

## 3. Identify Your First Trade (1 min)

### Look for:

```
✓ Score < -0.35 (Strong bearish) OR > +0.35 (Strong bullish)
✓ Conf% > 70% (High confidence)
✓ R:R > 1.5 (Good risk/reward)
✓ Risk Zone = NORMAL (Safe volatility)
```

**Example Good Trade:**
```
ADANIGREEN
Score: -0.42 (Strong Bearish) ✓
Conf%: 82 (Very High) ✓
Price: ₹1,200
SL: ₹1,150 (Risk: ₹50)
Target: ₹1,050 (Reward: ₹150)
R:R: 3.0 ✓✓
Pos Size: 26 shares (for ₹1,00,000 capital)
Risk Zone: NORMAL ✓
```

---

## 4. Place the Trade

### Step-by-Step:

1. **Open your broker app** (Zerodha, Angel, etc.)

2. **Create BUY order** (for bullish) OR **CREATE SHORT** (for bearish)
   ```
   Quantity: 26 shares (from Pos Size column)
   Price: ₹1,200 (current market price)
   Order Type: MARKET (immediate) or LIMIT (at price)
   ```

3. **Immediately set STOP LOSS**
   ```
   Quantity: 26 shares
   Price: ₹1,150 (from Stop Loss column)
   Order Type: STOP LOSS or SL-M
   Trigger: ₹1,150
   ```

4. **Set TARGET (Optional but recommended)**
   ```
   Quantity: 26 shares
   Price: ₹1,050 (from Target column)
   Order Type: LIMIT
   ```

### Example Zerodha Setup:
```
1. Go to Stocks → Search "ADANIGREEN"
2. Click BUY
3. Quantity: 26
4. Price: Market
5. Click BUY → Fills immediately

6. Right-click position → SET STOPLOSS
7. Price: ₹1,150
8. Click SET STOPLOSS

Done! Your trade is hedged.
```

---

## 5. Manage the Trade

### Rules:

```
✓ KEEP the stop-loss
  - Never move it up (for shorts) or down (for longs)
  - If SL hits, accept the loss (it's protecting you)

✓ EXIT at Target
  - Don't hold for "bigger moves"
  - Secure your profits

✓ TRACK wins/losses
  - Keep Excel sheet of every trade
  - Win rate, avg win, avg loss
  - For future trading plan improvements

✓ NEVER catch falling knives
  - If stock gaps below SL, don't panic
  - Your SL will protect you (at a gap cost)
```

---

## Advanced: Generate All 3 Indexes

### Run All in Parallel (Faster):

```bash
# NIFTY 200 + BANKNIFTY + NIFTY 50
python nifty_bearnness_v2.py --universe nifty200 --parallel 4
python nifty_bearnness_v2.py --universe banknifty --parallel 4
python nifty_bearnness_v2.py --universe nifty50 --parallel 4
```

---

## FAQ

### Q: How often should I run the screener?
**A:** Daily before market open (9:00 AM IST) for fresh signals

### Q: Which timeframe signals are best?
**A:** 
- **Intraday:** 5-min scores (fast, stop-losses tight)
- **Swing:** 15-min scores (2-4 hour holds)
- **Position:** 1-hour scores (1-3 day holds)

### Q: Can I trade the day after signal?
**A:** Yes, but signal strength may fade. Intraday signals are best acted on immediately. Swing signals good for 2-3 days.

### Q: What if score is +0.05?
**A:** Too weak, skip it. Need ±0.15+ for reliable trades.

### Q: How many trades should I take?
**A:** 
- Maximum 5-10 per day
- Never more than 30% of capital in single trade
- Never have >5 open positions

---

## Next Steps

- **Understand the math:** Read [Scoring Engine](../core/scoring-engine.md)
- **Learn risk management:** Read [Risk Management](../core/risk-management.md)
- **Options strategies:** Read [Options Strategies](../core/options-strategies.md)
- **Deep technical analysis:** Read [Support & Resistance](../analysis/support-resistance.md)

---

**Happy Trading! 🚀**

---

See also: [Installation](installation.md), [Overview](overview.md)
