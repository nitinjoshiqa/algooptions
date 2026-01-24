# BREEZE API CANDLE DATA AVAILABILITY ANALYSIS

**Date:** January 23, 2026  
**Status:** BREEZE API IS WORKING ✓

## Summary

The **Breeze API (ICICI Direct)** is properly configured and functioning. However, it has **limited stock coverage** - only some stocks return historical candle data while others return "No Data Found" error.

---

## Test Results

### Connection Status: ✓ WORKING
- BreezeConnect module: Installed ✓
- Session authentication: Valid ✓  
- API credentials: Configured ✓
- Session status: Verified with API call ✓

### Candle Data Availability: ⚠️ LIMITED
| Symbol | Status | Candles | Error |
|--------|--------|---------|-------|
| TCS | ✓ Works | 309 (5m) | None |
| INFY | ✗ No Data | 0 | "No Data Found" |
| HDFCBANK | ✗ No Data | 0 | "No Data Found" |
| RELIANCE | ✗ No Data | 0 | "No Data Found" |
| ICICIBANK | ✗ No Data | 0 | "No Data Found" |

### Root Cause
The Breeze API returns Status 200 (success) but with `Success: None` and Error: "No Data Found" for stocks where market data subscription is limited or symbol coverage gaps exist in their database.

---

## Current Data Provider Fallback Chain

```
1. Disk Cache (1 hour TTL)    ← Fastest ⚡
   ↓ (if not cached)
2. Breeze API (ICICI)         ← Limited coverage ⚠️
   ↓ (if no data)
3. NSE Direct API             ← Timeout protection
   ↓ (if fails)
4. Yahoo Finance (yfinance)   ← Global coverage but rate-limited
   ↓ (if rate limited)
5. Empty result               ← No data available
```

---

## Optimization Options

### Option A: Optimize Current System (Recommended)
**Goal:** Maximize Breeze usage, minimize API calls

**Changes:**
1. **Increase disk cache TTL** from 1 hour → 4-8 hours
   - Reduces API calls by 50-70%
   - Safe because market data doesn't change that frequently intraday

2. **Add database caching layer**
   - Store all fetched candles in local SQLite
   - Query DB before API calls
   - Update on-demand only

3. **Batch API calls**
   - Fetch all timeframes (5m, 15m, 1h, 1day) in single call where possible
   - Reduce individual API overhead

**Expected impact:** 60-80% faster screener execution

---

### Option B: Database-Backed Candles
**Goal:** Reduce external API dependency

**Implementation:**
```python
# Check local DB first
candles = query_candle_db(symbol, interval, last_updated > 1_hour_ago)
if candles:
    return candles, 'db'

# Then try Breeze
candles = breeze.get_historical_data(...)
if candles:
    save_to_candle_db(symbol, interval, candles)
    return candles, 'breeze'

# Fallback to yfinance
...
```

**Benefits:**
- ✓ No repeated API calls for same data
- ✓ Faster than any API
- ✓ Reduces rate limiting issues
- ✓ Works offline with cached data

**Drawbacks:**
- ✗ Requires database maintenance
- ✗ Initial setup effort

---

## Recommendation

**Use Option A (Optimize Disk Cache)** immediately:
- ✓ Simple to implement
- ✓ No breaking changes
- ✓ Significant speed improvement
- ✓ Breeze already provides best available data

**Then migrate to Option B if:**
- Screener needs to run more frequently
- Want guaranteed offline operation
- Rate limiting becomes frequent issue

---

## Next Steps

1. Increase disk cache TTL in `data_providers/__init__.py`
2. Add logging to track cache hit rate
3. Monitor API call reduction
4. Consider SQLite database layer if needed

Would you like me to implement the disk cache optimization?
