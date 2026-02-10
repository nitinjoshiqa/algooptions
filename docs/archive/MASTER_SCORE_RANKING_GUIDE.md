# Master Score Ranking Strategy

## Quick Decision Tree

```
You have multiple signals. How do you rank/prioritize?

                    ┌─────────────────────────────┐
                    │  Get all signals with       │
                    │  Master Score calculated    │
                    └──────────┬──────────────────┘
                               │
                               ▼
                    ┌─────────────────────────────┐
                    │  Sort by Master Score       │
                    │  (descending: highest first) │
                    │  Range: 0-100               │
                    └──────────┬──────────────────┘
                               │
                ┌──────────────┼──────────────────┐
                ▼              ▼                  ▼
         ┌──────────┐   ┌──────────┐        ┌──────────┐
         │  80-100  │   │  70-79   │        │  < 70    │
         │ EXCELLENT│   │   GOOD   │        │   FAIR   │
         │ (Take)   │   │ (Take)   │        │ (Skip)   │
         └──────────┘   └──────────┘        └──────────┘
              │               │
              │               │
         100% Position    80% Position     Look for better
         Size (3% risk)   Size (2% risk)   signal
```

---

## Practical Examples

### Scenario 1: Multiple Bullish Signals Same Day

**Signals Received:**
1. INFY: Master Score 85, Robustness 85, Confidence 90
2. HDFC: Master Score 72, Robustness 57, Confidence 78
3. TCS: Master Score 78, Robustness 78, Confidence 85
4. RELIANCE: Master Score 62, Robustness 43, Confidence 65

**Ranking Decision:**
```
RANK 1: INFY (Master 85) → TAKE | Full position (3% risk)
RANK 2: TCS (Master 78) → TAKE | Standard position (2% risk)
RANK 3: HDFC (Master 72) → CONSIDER | Smaller position (1% risk)
RANK 4: RELIANCE (Master 62) → SKIP | Wait for higher quality
```

**Logic:**
- INFY: Master score 85 = Excellent, all filters passing, strong pattern
- TCS: Master score 78 = Good quality, take but slightly reduced conviction
- HDFC: Master score 72 = Good but only 5/7 filters = Caution
- RELIANCE: Master score 62 = Only passing 3 filters = Too risky

---

### Scenario 2: High Master Score vs High Confidence

**Which should you take?**

**Signal A:**
- Master Score: 88
- Confidence: 75
- Robustness: 90 (7/7 filters)
- Context: 85

**Signal B:**
- Master Score: 65
- Confidence: 95
- Robustness: 30 (2/7 filters)
- Context: 45

**Decision: TAKE SIGNAL A**

**Why:**
- High master score (88) means all dimensions validated
- High robustness (7/7 filters) = All safety checks passed
- Even though confidence is "only" 75, it's balanced by excellent robustness
- Signal B has pattern match (95 confidence) but fails 5 key safety filters = High risk

**Lesson:** Master score > confidence alone because it accounts for safety.

---

### Scenario 3: Today's Daily Limit (5 Signals Max)

**Signals Available:**
1. ABC: Master 83
2. DEF: Master 81
3. GHI: Master 79
4. JKL: Master 76
5. MNO: Master 74
6. PQR: Master 68
7. STU: Master 61

**Allocation (5 signal limit):**
```
Signal 1 (ABC, 83):  100% position (3% risk)
Signal 2 (DEF, 81):  100% position (3% risk)
Signal 3 (GHI, 79):  80% position (2% risk)
Signal 4 (JKL, 76):  80% position (2% risk)
Signal 5 (MNO, 74):  60% position (1.5% risk)

SKIP (PQR, 68):      Below fair threshold
SKIP (STU, 61):      Below safe threshold
```

**Total Daily Risk:** 3 + 3 + 2 + 2 + 1.5 = 11.5% (within limit)

**Why MNO and skip PQR/STU:**
- MNO (74) is still "good" quality, worth 1.5% risk
- PQR (68) is borderline fair, questionable
- STU (61) is poor quality, skip

---

## Threshold Guidelines

### Master Score Interpretation

```
Range      | Quality  | Position Size | Risk % | Action
─────────────────────────────────────────────────────────
90-100     | EXCELLENT| 100% (Full)   | 3.0% | TAKE - Highest confidence
80-89      | EXCELLENT| 100% (Full)   | 3.0% | TAKE - Very strong signal
75-79      | GOOD     | 80-100%       | 2.0% | TAKE - Standard entry
70-74      | GOOD     | 60-80%        | 1.5% | CONSIDER - Reduce size
65-69      | FAIR     | 30-60%        | 1.0% | CAUTION - Small only
60-64      | FAIR     | Skip          | 0.0% | SKIP unless high conviction
<60        | POOR     | SKIP          | 0.0% | SKIP - Wait for better
```

### When to Override

**Take signal below 70 if:**
- News catalyst aligns with signal direction
- Pattern is historically rare (>80% accuracy)
- Large market move imminent (earnings, Fed, etc.)

**Take signal below 60 if:**
- You have external alpha (private news, insider info)
- It's a rare setup you've been waiting for
- Risk/reward is 1:5 or better

**Skip signal above 80 if:**
- Position already filled today
- Daily loss limit hit
- Different signal same day with higher score

---

## Daily Execution Checklist

### Morning Routine
```
□ Scan all signals from overnight
□ Calculate master_score for each (or auto-calculated)
□ Sort descending by master_score
□ Filter out below 70 (unless special case)
│
├─ Master ≥ 80? → TAKE (full position)
├─ Master 75-79? → TAKE (80% position)
├─ Master 70-74? → CONSIDER (60% position)
├─ Master 65-69? → SKIP unless conviction
└─ Master < 65? → SKIP (wait for better)
│
□ Check daily loss: -2% limit
□ Check daily trades: 5 max
□ Execute positions (smallest to largest)
□ Set initial stops (ATR-based)
□ Log reason for each entry
```

### During Day Monitoring
```
□ Watch master_score on active positions (robustness_momentum)
□ If robustness_momentum turns negative:
   - Could indicate deteriorating filters
   - Consider partial profit or tightened stop
   
□ If robustness_momentum stays positive:
   - Reinforce thesis, hold for target
   
□ Track cumulative daily P&L
□ If hitting -2% limit, close all remain trades
□ If hitting 5 trades for day, pause (wait for EOD review)
```

---

## Integration with Existing Scores

### How Master Score Relates

```
Your Existing System         New Master Score
─────────────────────────────────────────────────────
Confidence (pattern)     ──┐
Final Score (indicators) ──┼─→ Master Score
Context Score            ──┤   (6-dimension
Context Momentum         ──│    weighted)
News Sentiment           ──┤
(NEW) Robustness         ──┘

Master Score = Unified decision point
Individual scores = Detail/diagnosis
```

**Example:**
- Old approach: "Confidence 85 looks good, take it"
- New approach: "Confidence 85 BUT robustness only 40, skip"
- Master score 72 = Shows balanced view ("good but not excellent")

---

## Customization by Strategy

### Conservative (Low Risk Tolerance)
```
Only take Master Score ≥ 80
Position size: 50% (1.5% risk only)
Daily limit: 3 signals max
Daily loss limit: -1% (tighter than 2%)
```

### Moderate (Balanced)
```
Take Master Score ≥ 75
Position size: 100% (3% risk)
Daily limit: 5 signals max
Daily loss limit: -2%
```

### Aggressive (Growth Focus)
```
Take Master Score ≥ 70
Position size: 120% (3.6% risk - using leverage)
Daily limit: Unlimited
Daily loss limit: -3%
Allow 1-2 > 70 < 75 overrides per day
```

---

## Automation Example

### Pseudo-Code for Ranking

```python
def rank_signals_for_entry(signals_list):
    """
    Rank all signals by master_score, return entry priority
    """
    # Sort descending by master_score
    ranked = sorted(signals_list, 
                   key=lambda x: x['master_score'], 
                   reverse=True)
    
    entries = []
    daily_risk = 0
    max_daily_risk = 2.0  # %
    max_trades = 5
    
    for signal in ranked:
        # Check limits
        if len(entries) >= max_trades:
            break
        if daily_risk >= max_daily_risk:
            break
        
        # Determine position size based on master_score
        master = signal['master_score']
        robustness = signal['robustness_score']
        
        if master >= 80:
            position_size = 3.0  # 3% risk
            action = 'TAKE'
        elif master >= 75:
            position_size = 2.0  # 2% risk
            action = 'TAKE'
        elif master >= 70:
            position_size = 1.5  # 1.5% risk
            action = 'CONSIDER'
        elif master >= 65 and robustness >= 50:
            position_size = 1.0  # 1% risk only
            action = 'SMALL_ONLY'
        else:
            position_size = 0    # Skip
            action = 'SKIP'
        
        if position_size > 0:
            daily_risk += position_size
            entries.append({
                'symbol': signal['symbol'],
                'action': action,
                'risk_pct': position_size,
                'master_score': master,
                'reason': signal.get('reason', '')
            })
    
    return entries
```

---

## Performance Tracking

### Metrics to Track by Master Score Band

```
Master 80+ │ Win Rate: 65% | Avg Win: 2.4% | Avg Loss: -1.1% | Profit Factor: 2.8
Master 75-79 │ Win Rate: 62% | Avg Win: 2.1% | Avg Loss: -1.2% | Profit Factor: 2.1
Master 70-74 │ Win Rate: 58% | Avg Win: 1.8% | Avg Loss: -1.3% | Profit Factor: 1.6
Master 65-69 │ Win Rate: 52% | Avg Win: 1.4% | Avg Loss: -1.4% | Profit Factor: 1.1
Master <65   │ Win Rate: 48% | Avg Win: 1.0% | Avg Loss: -1.5% | Profit Factor: 0.8
```

**Optimal Range:** Master 75-89 (best risk/reward balance)

---

## Decision Matrix (Quick Reference)

| Master Score | Robustness | Confidence | Decision | Position | Risk |
|---|---|---|---|---|---|
| 90+ | 90+ | 90+ | TAKE | 100% | 3.0% |
| 85-89 | 80+ | 80+ | TAKE | 100% | 3.0% |
| 80-84 | 70+ | 75+ | TAKE | 100% | 3.0% |
| 75-79 | 60+ | 70+ | TAKE | 80% | 2.0% |
| 70-74 | 50+ | 65+ | CONSIDER | 60% | 1.5% |
| 65-69 | 40+ | 60+ | CAUTION | 30% | 1.0% |
| 60-64 | 30+ | 55+ | SKIP* | 0% | 0% |
| <60 | <30 | <50 | SKIP | 0% | 0% |

*Skip unless special circumstances (10:1 risk/reward, etc.)

---

## Summary

**Golden Rules for Ranking:**

1. **Primary Sort**: Master Score (descending)
2. **Position Size**: Directly correlates to master score
3. **Risk%**: Higher master score = Higher risk% allowed
4. **Daily Limits**: Hit 5 trades or -2% loss, stop all entries
5. **Override Only**: For high conviction setups with external alpha

**The Master Score is your unified quality metric. Use it.**
