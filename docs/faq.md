# Frequently Asked Questions

## General Questions

### Q: Is AlgoOptions free?
**A:** Yes! It's completely free and open-source. Only data is from Yahoo Finance (free) or Breeze API (paid if you use it).

### Q: What's the minimum account size to trade?
**A:** ₹25,000 (can do 5-10 shares per trade). Better with ₹50,000+.

### Q: Which broker should I use?
**A:** Any broker works (Zerodha, Angel, 5paisa, etc.). Use one with low brokerage and good API support.

### Q: Can I trade crypto/forex with this?
**A:** Currently designed for Indian stock market (NSE). Can be adapted for other assets.

---

## Scoring & Signals

### Q: What does a score of -0.08 mean?
**A:** Weak bearish signal. It's visible but not strong. Consider only if confidence > 70%.

### Q: Why do scores change every day?
**A:** Because new price data, volume, and indicators update daily. Scores reflect current market state.

### Q: Can I get conflicting signals?
**A:** Yes, especially during market turning points. If 5m is bullish but 1h is bearish, prefer the 1h (longer-term context).

### Q: Which signal is most reliable?
**A:** **All 3 timeframes aligned** (✓✓✓) = 75%+ success rate. Mixed signals = 50-60% success rate.

---

## Risk & Position Sizing

### Q: Why the 2% risk rule?
**A:** 
- Allows you to lose 50 trades in a row and still have 97% capital
- Mathematically optimal (Kelly Criterion approximation)
- Protects psychology during drawdowns

### Q: What if I risk more, like 5%?
**A:** You'll win/lose faster. You'll blow up faster too. After 20 consecutive losses: you've lost 64% of capital. Most people panic-trade and lose more.

### Q: How do I calculate position size?
**A:** 
1. Capital × 2% = Risk amount
2. Entry - SL = Risk per share
3. Risk amount / Risk per share = Position size

See [Position Sizing](core/position-sizing.md) for details.

### Q: What if position size is 0.3 shares?
**A:** Round down to 0, skip the trade. Minimum position should be 1 share.

---

## Options Trading

### Q: Can I trade options with this screener?
**A:** Yes! Check the recommended "Strategy" column in the report.

### Q: Which options strategy is safest?
**A:** 
1. **Long Call/Put** (Defined loss, most beginner-friendly)
2. **Call/Put Spreads** (Limited risk, limited profit)
3. **Iron Butterfly** (Complex, but excellent risk/reward)

Avoid naked short selling as a beginner.

### Q: How many option contracts should I buy?
**A:** Same 2% rule applies:
```
Max Loss = 2% of capital
Contract Cost = Premium × 100 (per contract in India)

If 2% = ₹2,000 and Premium = ₹50
Contracts = 2,000 / (50 × 100) ≈ 0.4 contracts ≈ 0 (skip)

Better: ₹100 premium
Contracts = 2,000 / (100 × 100) = 0.2 contracts ≈ 0 (still skip)

Use 1% risk for options until experienced.
```

---

## Execution & Brokers

### Q: Should I use MARKET or LIMIT orders?
**A:** 
- **MARKET:** Immediate fill, might slip price (use for entry)
- **LIMIT:** Exact price, might not fill (use for exits)

Best practice: Market for entry, limit for exit targets.

### Q: How do I set stop-loss?
**A:** 
- **Type:** SL-M or STOP-LOSS in your broker
- **Trigger:** ₹price from report
- **Quantity:** Same as entry quantity

### Q: Can I trade on multiple timeframes?
**A:** 
- **YES:** But manage separately
- If you trade intraday (5m) AND swing (15m), track separately
- Risk/position size applies to each trade independently
- Don't accumulate positions (e.g., long intraday + long swing at same time)

---

## Common Mistakes

### ❌ Mistake 1: Ignoring Stop-Loss
**Why it's wrong:** One gap-down can wipe out your account.  
**Fix:** Always set SL immediately after entry. No exceptions.

### ❌ Mistake 2: Moving Stop-Loss Against You
**Why it's wrong:** Converts winners to losers.  
**Fix:** Set it and forget it. SL is your exit trigger, not a "price target."

### ❌ Mistake 3: Risking More Than 2%
**Why it's wrong:** Quick way to account depletion.  
**Fix:** Strictly follow position sizing rules. If trade is too big, it's too risky.

### ❌ Mistake 4: Trading Low-Confidence Signals
**Why it's wrong:** 50% win rate on weak signals = net loser.  
**Fix:** Only trade Conf% > 70%.

### ❌ Mistake 5: Averaging Down
**Why it's wrong:** Pyramid losses instead of profits.  
**Fix:** Take size calculated at entry. If you want more shares, wait for new signal.

### ❌ Mistake 6: Skipping Boring Trades
**Why it's wrong:** NIFTY Bank might not be exciting but has great R:R.  
**Fix:** Focus on R:R and probability, not "sexiness" of stock.

### ❌ Mistake 7: Over-Trading
**Why it's wrong:** More trades = more commissions and mistakes.  
**Fix:** Maximum 3-5 trades per day. Quality > Quantity.

---

## Improving Your Results

### Q: How can I improve my win rate?
**A:**
1. Only trade Conf% > 75%
2. Only trade R:R > 2.0
3. Trade at support/resistance levels (higher probability)
4. Wait for all 3 timeframes to align
5. Trade the last 1-2 hours of market (cleaner signals)

### Q: Should I use different settings?
**A:** 
- Default settings are production-tested
- For beginners: don't change anything
- For advanced: experiment with --mode or --parallel only

### Q: How often should I backtest?
**A:** 
- Monthly: Review your trades (wins/losses/patterns)
- Quarterly: Run backtests on new ideas
- Never: Trade before backtesting idea

---

## Technical Issues

### Q: Report doesn't open in browser
**A:** 
```
Right-click nifty_bearnness.html → Open With → Chrome/Edge
Or drag file into browser
```

### Q: Python error "Module not found"
**A:** 
```bash
# Activate virtual environment first
.venv\Scripts\activate

# Then run
python nifty_bearnness_v2.py ...
```

### Q: Script runs but no output
**A:** 
```bash
# Run with logging
python nifty_bearnness_v2.py --universe banknifty --force-yf 2>&1 | tee output.log

# Check output.log for errors
```

---

## Support

- **Documentation:** See [Getting Started](getting-started/overview.md)
- **API Reference:** See [Advanced](advanced/api-reference.md)
- **Backtesting:** See [Backtesting Guide](advanced/backtesting.md)

**Last Updated:** January 21, 2026
