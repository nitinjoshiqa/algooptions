# Implementation Quick Reference

**Last Updated:** February 10, 2026  
**Version:** 2.0 (Complete)

---

## 🔑 Key Functions Reference

### 1. Signal Persistence Validation
**File:** `backtesting/backtest_engine.py:20-72`

```python
def is_signal_persistent(df, current_idx, lookback=1):
    """
    Validates signal persists across candles.
    
    Args:
        df: DataFrame with OHLCV + indicators
        current_idx: Current candle index
        lookback: How many bars to verify (default 1)
    
    Returns:
        dict: Signal persistence metrics
    
    Checks:
        ✓ Price vs SMA20 persistence
        ✓ Price vs SMA50 persistence
        ✓ RSI momentum confirmation
        ✓ Multi-timeframe alignment
    
    Example:
        >>> persistence = is_signal_persistent(df, 50)
        >>> if persistence.get('is_persistent'):
        >>>     signal_valid = True
    """
```

---

### 2. Market Regime (From ADX)
**File:** `backtesting/backtest_engine.py:73-85`

```python
def get_market_regime(adx_value):
    """
    Classifies market regime using ADX.
    
    Args:
        adx_value: ADX indicator value (0-100)
    
    Returns:
        str: "TRENDING", "NEUTRAL", or "RANGING"
    
    Map:
        ADX ≥ 25  → TRENDING (strong direction)
        20-25     → NEUTRAL (transitioning)
        < 20      → RANGING (consolidating)
    
    Usage:
        >>> regime = get_market_regime(df['ADX'].iloc[-1])
        >>> if regime == 'TRENDING':
        >>>     sl_multiplier = 1.2 * base_atr
    """
```

---

### 3. Volatility Regime (From ATR)
**File:** `backtesting/backtest_engine.py:86-100`

```python
def get_volatility_regime(atr, close):
    """
    Classifies volatility using ATR.
    
    Args:
        atr: Average True Range value
        close: Current close price
    
    Returns:
        str: "HIGH", "MEDIUM", or "LOW"
    
    Logic:
        attratio = (atr / close) * 100
        
        > 4%   → HIGH    (loose stops, expect big moves)
        2-4%   → MEDIUM  (normal stops)
        < 2%   → LOW     (tight stops, small moves)
    
    Usage:
        >>> vol = get_volatility_regime(atr, price)
        >>> if vol == 'HIGH':
        >>>     position_size = 0.01 * capital  # 1% risk
        >>> elif vol == 'MEDIUM':
        >>>     position_size = 0.02 * capital  # 2% risk
        >>> else:
        >>>     position_size = 0.03 * capital  # 3% risk
    """
```

---

### 4. Robustness Momentum
**File:** `backtesting/backtest_engine.py:101-130`

```python
def calculate_robustness_momentum(df, current_idx, filters_passed_current):
    """
    Tracks if filter quality improving or degrading.
    
    Args:
        df: DataFrame with robustness history
        current_idx: Current bar index
        filters_passed_current: # of filters passing now (0-7)
    
    Returns:
        float: Momentum value (-1.0 to +1.0)
        
    Interpretation:
        +1.0 → All 7 filters adding (strengthening) 
        +0.5 → Some filters improving
         0.0 → No change (stable)
        -0.5 → Some filters breaking
        -1.0 → All 7 filters breaking (weakening)
    
    Usage:
        >>> momentum = calculate_robustness_momentum(df, idx, filters_passed)
        >>> if momentum > 0.3:
        >>>     confidence_boost = 0.15  # Add confidence
        >>> elif momentum < -0.3:
        >>>     signal_warning = True    # Skip or reduce size
    """
```

---

### 5. Master Score (6-Dimensional)
**File:** `backtesting/backtest_engine.py:132-200`

```python
def calculate_master_score(
    confidence,           # 0-100
    final_score=0.68,    # -1 to +1
    context_score=3.0,   # 0-5
    context_momentum=0.0, # -1 to +1
    robustness_score=50,  # 0-100
    news_sentiment=0.0    # -1 to +1
):
    """
    Calculate 6-dimensional composite quality score.
    
    Weights:
        Confidence (25%)    → Pattern quality
        Technical (25%)     → Indicator strength
        Robustness (20%)    → Filter quality
        Context (15%)       → Market structure
        Momentum (10%)      → Rate of change
        News (5%)           → Sentiment
    
    Returns:
        dict: {
            'master_score': 0-100,
            'components': {normalized scores},
            'tooltip': breakdown text
        }
    
    Tiers:
        ≥ 80 → STRONG CONVICTION (full position)
        70-79 → GOOD (standard position)
        60-69 → FAIR (reduced position)
        < 60 → WEAK (skip)
    
    Usage:
        >>> result = calculate_master_score(
        ...     confidence=85,
        ...     final_score=0.75,
        ...     context_score=3.5,
        ...     robustness_score=82
        ... )
        >>> master_score = result['master_score']  # 81.3/100
        >>> if master_score >= 80:
        >>>     position_size = normal_size
        >>> elif master_score < 60:
        >>>     position_size = 0  # Skip
    """
```

---

## 🚀 Quick Integration Example

### Adding Robustness to Your Signal

```python
from backtesting.backtest_engine import (
    calculate_master_score,
    get_market_regime,
    get_volatility_regime,
    calculate_robustness_momentum
)

# After signal detection...
if signal_detected:
    
    # Calculate robustness metrics
    regime = get_market_regime(df['ADX'].iloc[-1])
    vol = get_volatility_regime(df['ATR'].iloc[-1], df['Close'].iloc[-1])
    
    # Simulate 7-filter robustness (0-7)
    filters_passed = 6  # Example: 6 of 7 filters pass
    robustness_pct = (filters_passed / 7) * 100  # 86%
    
    # Calculate momentum
    momentum = calculate_robustness_momentum(df, idx, filters_passed)
    
    # Calculate master score
    master_result = calculate_master_score(
        confidence=confidence_val,
        final_score=final_score_val,
        context_score=context_val,
        context_momentum=momentum_val,
        robustness_score=robustness_pct,
        news_sentiment=news_val
    )
    
    # Add to signal
    signal = {
        'symbol': 'RELIANCE',
        'price': 2800,
        'signal_type': 'BULLISH',
        
        # New fields
        'robustness_score': robustness_pct,
        'robustness_momentum': momentum,
        'master_score': master_result['master_score'],
        'master_score_tooltip': master_result['tooltip'],
        'filters_passed': filters_passed
    }
    
    # Decision logic
    if master_result['master_score'] >= 80:
        position_size = normal_risk
    elif master_result['master_score'] >= 70:
        position_size = normal_risk * 0.8
    elif 60 <= master_result['master_score']:
        position_size = normal_risk * 0.5
    else:
        position_size = 0  # Skip
```

---

## 📊 CSV Export Format

```python
# New columns added to CSV export
from exporters.csv_exporter import save_csv

results = [
    {
        'symbol': 'RELIANCE',
        'price': 2800,
        'confidence': 85,
        'final_score': 0.82,
        
        # NEW COLUMNS (3)
        'robustness_score': 82.0,
        'robustness_momentum': 0.5,
        'master_score': 81.3
    }
]

# Save with robustness columns
save_csv(results, 'output.csv')

# CSV will have:
# symbol,price,confidence,final_score,...,robustness_score,robustness_momentum,master_score
# RELIANCE,2800,85,0.82,...,82.0,0.5,81.3
```

---

## 🎨 HTML Table Columns

### New Columns in HTML Report

| Column | Type | Range | Color | Tooltip |
|--------|------|-------|-------|---------|
| Robustness% | Number | 0-100 | Green≥80, Orange 60-80, Red<60 | "7 safety filters..." |
| Robust Momentum | Number | -1 to +1 | Heatmap | "Filter trend..." |
| Master Score | Number | 0-100 | Green≥80, Orange 60-79, etc | Full breakdown |

### HTML Rendering Code

```python
# From nifty_bearnness_v2.py (lines 1948-1973)

robustness_score = r.get('robustness_score', 0) or 0
robustness_momentum = r.get('robustness_momentum', 0) or 0
master_score = r.get('master_score', 0) or 0
master_score_tooltip = r.get('master_score_tooltip', '')

# Color coding
if robustness_score >= 80:
    robust_color = '#27ae60'  # Green
elif robustness_score >= 60:
    robust_color = '#f39c12'  # Orange
else:
    robust_color = '#e74c3c'  # Red

# Render columns
html += f"<td style='color: {robust_color};'>{robustness_score:.0f}</td>"
html += f"<td style='background-color: hsl(...)'>{robustness_momentum:+.2f}</td>"
html += f"<td style='color: {master_color}; font-weight: bold;'>"
html += f"<span class='tooltip'>{master_score:.0f}<span class='tooltiptext'>{master_score_tooltip}</span></span>"
html += "</td>"
```

---

## 🧪 Testing Examples

### Unit Test: Master Score

```python
# Expected: Perfect score
result = calculate_master_score(
    confidence=100,
    final_score=1.0,
    context_score=5.0,
    context_momentum=1.0,
    robustness_score=100,
    news_sentiment=1.0
)
assert result['master_score'] == 100.0  ✅

# Expected: Good score
result = calculate_master_score(
    confidence=85,
    final_score=0.75,
    context_score=3.5,
    context_momentum=0.3,
    robustness_score=82,
    news_sentiment=0.1
)
assert 80 <= result['master_score'] < 85  ✅

# Expected: Fair score
result = calculate_master_score(
    confidence=65,
    final_score=0.5,
    context_score=3.0,
    context_momentum=0.0,
    robustness_score=71,
    news_sentiment=-0.2
)
assert 65 <= result['master_score'] < 75  ✅
```

### Integration Test: Full Signal Pipeline

```python
# Simulate signal generation with robustness
signal = generate_full_signal_with_robustness(
    df=historical_data,
    symbol='RELIANCE',
    pattern='Golden Cross',
    idx=100
)

# Verify all 15 fields present
required_fields = [
    'symbol', 'timestamp', 'price', 'signal_type', 'pattern',
    'confidence', 'final_score', 'context_score', 'context_momentum',
    'news_sentiment_score', 'filters_passed', 'robustness_score',
    'robustness_momentum', 'master_score', 'master_score_tooltip'
]

for field in required_fields:
    assert field in signal, f"Missing: {field}"  ✅

# Verify types
assert isinstance(signal['master_score'], (int, float))  ✅
assert 0 <= signal['master_score'] <= 100  ✅
assert isinstance(signal['robustness_momentum'], (int, float))  ✅
assert -1 <= signal['robustness_momentum'] <= 1  ✅
```

---

## ⚡ Performance Tips

### Optimization Tips

1. **Cache Market Regime**
   ```python
   # DON'T: Calculate every candle
   regime = get_market_regime(df['ADX'].iloc[i])
   
   # DO: Cache if not changing much
   cached_regime = get_market_regime(df['ADX'].iloc[-1])
   ```

2. **Batch Master Score Calculation**
   ```python
   # DON'T: Calculate individually
   for r in results:
       r['master_score'] = calculate_master_score(...)
   
   # DO: Process in batches
   scores = vectorized_master_score_calc(results)
   ```

3. **Pre-populate Robustness**
   ```python
   # During signal generation, include robustness
   # Not post-hoc calculation
   ```

---

## 🐛 Debugging Checklist

**Master Score not showing?**
- [ ] Check signal has 'robustness_score' ✓
- [ ] Check signal has 'context_score' ✓
- [ ] Check signal has 'confidence' ✓
- [ ] Run: `python test_scoring_functions.py`
- [ ] Verify in HTML: `<table id="screener">` has data

**Tooltip overlapping?**
- [ ] Check CSS: `.tooltip .tooltiptext { top: 100% }` ✓
- [ ] Check margin: `margin-top: 8px` ✓
- [ ] Regenerate HTML: `python nifty_bearnness_v2.py --quick`

**CSV not exporting robustness?**
- [ ] Check signal has 'robustness_score' ✓
- [ ] Check CSV exporter includes 3 new columns ✓
- [ ] Run: `python -c "from exporters.csv_exporter import *; print('OK')"`

**Tests failing?**
- [ ] Run: `python test_scoring_functions.py`
- [ ] Check all 7 tests pass
- [ ] If failing, check backtest_engine.py hasn't changed

---

## 📞 Common Issues & Solutions

### Issue: Master Score = 0
**Solution:** Check all input parameters are non-null
```python
# Problem
result = calculate_master_score(None, None, None)

# Solution
result = calculate_master_score(
    confidence=85,
    final_score=0.75,
    context_score=3.0
)
```

### Issue: Robustness Score = 50
**Solution:** Filters are failing - check signal generation
```python
# Problem: Only 3 of 7 filters pass → robustness = 43%
# Solution: Review which filters are failing
for i, filter in enumerate(ROBUSTNESS_FILTERS):
    if not filter(signal):
        print(f"Filter {i} failed: {filter.__name__}")
```

### Issue: HTML tooltip blank
**Solution:** Check master_score_tooltip is populated
```python
# Problem
r['master_score_tooltip'] = None

# Solution
r['master_score_tooltip'] = generate_tooltip(master_score, components)
```

---

## 📚 Documentation References

| Document | Purpose |
|----------|---------|
| ROBUSTNESS_SYSTEM_WIKI.md | Complete system design |
| CODE_REFACTORING_SUMMARY.md | Architecture changes |
| IMPLEMENTATION_QUICK_REFERENCE.md | This file |
| test_scoring_functions.py | Unit tests (7/7 passing) |
| generate_demo_html.py | Demo generation |

---

**Version:** 2.0 Complete  
**Status:** ✅ Production Ready  
**Last Updated:** February 10, 2026
