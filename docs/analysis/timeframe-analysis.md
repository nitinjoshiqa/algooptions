# Timeframe Analysis

## Multi-Timeframe Trading Principle

**Higher timeframes always win over lower timeframes.**

```
Weekly Trend > Daily Trend > 4H Trend > 1H Trend > 15m Trend > 5m Trend

Example:
Weekly: STRONG BULLISH
Daily: BEARISH
Signal: Don't short, wait for daily to align with weekly
```

## AlgoOptions Timeframes

The system analyzes 3 key timeframes:

### 1. Five-Minute Chart (Intraday Scalping)
```
Candle = 5 minutes
Session = 78 candles (6.5 hours market)
Best for: Scalpers, quick entries/exits (minutes to hours)
```

**When to use 5m signals:**
- Day trading during market hours
- Quick 1-2% moves
- High-frequency entries

**Risk:** Fast moves can whipsaw you out

---

### 2. Fifteen-Minute Chart (Swing Trading)
```
Candle = 15 minutes
Session = 26 candles (6.5 hours market)
Best for: Swing traders (hours to days)
```

**When to use 15m signals:**
- Swing trades (4-24 hours)
- Good balance of speed vs noise
- Most reliable for beginners

**Advantage:** Filters out 5m noise, captures 15m-1h trends

---

### 3. One-Hour Chart (Position Trading)
```
Candle = 1 hour
Session = 6 candles (6.5 hours market)
Best for: Position traders (days to weeks)
```

**When to use 1h signals:**
- Multi-day trades
- Strong trends
- Institutional-grade moves

**Advantage:** Long-term trend clarity, fewer false breakouts

---

## Timeframe Alignment (TF Align)

### ✓✓✓ All Aligned (Strongest Signal)
```
5m: BULLISH
15m: BULLISH
1h: BULLISH

Probability: 75-80% success ⭐⭐⭐

Example Trade:
- All timeframes show clear uptrend
- Volume increasing
- Support holding

Action: MAX POSITION, tight stops
```

### ✓✓✗ Two Aligned (Good Signal)
```
5m: BULLISH
15m: BULLISH
1h: NEUTRAL

Probability: 60-65% success ⭐⭐

Example Trade:
- Short-term momentum strong
- Longer-term trend forming
- Could reverse if 1h turns bearish

Action: NORMAL POSITION, watch 1h closely
```

### ✓✗✗ One Aligned (Weak Signal)
```
5m: BULLISH
15m: NEUTRAL
1h: BEARISH

Probability: 45-50% success ⭐

Example Trade:
- Quick bounce only
- Longer-term trend is down
- High risk of failure

Action: SKIP or SMALL POSITION only
```

---

## Strategy by Timeframe Alignment

```
5m Score  │ 15m Score │ 1h Score  │ Action
──────────┼───────────┼───────────┼─────────────────────────
Strong +  │ Strong +  │ Strong +  │ BUY BIG - All aligned
+         │ +         │ +         │ BUY - Aligned
+         │ +         │ Neutral   │ BUY SMALL - Short term bullish
+         │ Neutral   │ Neutral   │ BUY TINY - Intraday only
Neutral   │ Neutral   │ Neutral   │ SKIP - No signal
-         │ -         │ -         │ SHORT BIG - All aligned
-         │ Neutral   │ -         │ SHORT SMALL - Longer trend down
-         │ Neutral   │ +         │ SKIP - Lower TF doesn't matter
```

---

## Example: RELIANCE Trade

```
Weekly Trend: STRONG UPTREND ↑
Daily Trend: Consolidating (range ₹2,450-₹2,550)
4H Trend: BEARISH (lower highs)

5m Score: -0.25 (Bearish, drop from ₹2,500)
15m Score: -0.10 (Weak bearish)
1h Score: -0.05 (Neutral turning down)

Final Score: -0.10 (Weak bearish)
Alignment: ✓✗✗ (Only 5m aligned)

Action: SKIP THIS SHORT
- Lower timeframe bearish doesn't override weekly bullish
- Risk: Wave down within larger uptrend
- Better: Wait for 4h/1h to turn bullish, then buy

What if 4h turned bullish?
Then: 5m still shows bounce entry opportunity
Position: Normal size (5m + 4h aligned)
```

---

## Using Multi-Timeframe Confirmation

### Best Practice: 3-Step Confirmation

```
Step 1: Check Weekly/Daily Bias
- If weekly uptrend, prefer LONGS
- If weekly downtrend, prefer SHORTS
- If weekly neutral, trade both ways (smaller size)

Step 2: Identify 4H/1H Trend
- Entering in direction of 4H/1H trend (higher probability)
- Pullbacks offer better entries than breakouts against trend

Step 3: Use 15m/5m for Entry Timing
- Wait for 15m dip to enter long (in uptrend)
- Wait for 15m spike to enter short (in downtrend)
- Tightest stops on 5m entries
```

### Example Trade Setup

```
Weekly: Uptrend ↑ (HDFC in multi-month uptrend)
Daily: Consolidation (pullback/pause)
4H: Turning back up (bullish signal)

Entry Plan:
1. Wait for 15m dip (natural pullback)
2. Buy when 15m reverses up from support
3. Stop below local 15m low
4. Target = Daily resistance or 4H highs

Why this works?
- Larger trend (weekly/daily) supports up
- Medium trend (4h) confirms up
- Short-term (15m) gives optimal entry
```

---

See also: [Scoring Engine](../core/scoring-engine.md), [Support & Resistance](support-resistance.md)
