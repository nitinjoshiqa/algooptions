# Algo Options Screener - Complete Wiki

**Last Updated:** January 23, 2026  
**Status:** Production Ready ✓  
**Universe:** 179+ validated stocks  
**Main Script:** `nifty_bearnness_v2.py`

---

## 📋 Quick Start (60 seconds)

### Run Full Screener
```bash
# Activate environment
& .venv/Scripts/Activate.ps1

# Run with swing trading scores (recommended)
python nifty_bearnness_v2.py --universe nifty500 --mode swing --screener-format html --force-yf

# Run with intraday scores
python nifty_bearnness_v2.py --universe nifty500 --mode intraday --screener-format html --force-yf
```

### Output Files
- **CSV:** `nifty_bearnness.csv` - All 179+ stocks with scores
- **HTML:** `nifty_bearnness.html` - Interactive report with sorting
- **Timestamp Reports:** `reports/` folder with dated outputs

---

## 🏗️ System Architecture

### High-Level Flow

```
User Command
    ↓
CLI Argument Parser (argparse)
    ↓
Load Universe (nifty_constituents.txt)
    ↓
ThreadPoolExecutor (8 workers)
├─ Worker 1: Fetch RELIANCE → Score → Queue
├─ Worker 2: Fetch HDFCBANK → Score → Queue
├─ ...
└─ Worker 8: Fetch CIPLA → Score → Queue
    ↓
[Smart Wait Strategy: 1.5s between batches]
    ↓
Collect & Sort Results
    ↓
Generate CSV + HTML Reports
```

### Project Structure

```
algooptions/                       # Root directory
├── nifty_bearnness_v2.py         # MAIN SCREENER (2,647 lines)
│   └── Orchestrates entire workflow
│
├── wait_strategy.py              # API rate limiting & retry logic
│   └── Prevents timeouts, exponential backoff
│
├── config_manager.py             # Configuration management
│   └── CLI args & defaults
│
├── scheduler.py                  # Daily job scheduler
│   └── Run at market close (15:30)
│
├── core/                         # Core business logic
│   ├── scoring_engine.py         # Bearness calculation
│   │   └── Swing/Intraday/Position scoring modes
│   │
│   ├── universe.py               # Stock universe management
│   │   └── Load constituents lists
│   │
│   ├── option_strategies.py      # Option recommendations
│   │   └── Put/Call spread suggestions
│   │
│   ├── sector_mapper.py          # Sector classification
│   │   └── Banking, IT, Energy, etc.
│   │
│   ├── support_resistance.py     # S/R level calculation
│   │   └── Breakout detection
│   │
│   ├── performance.py            # Analytics tracker
│   │   └── Win rate, metrics
│   │
│   └── [13 more supporting modules]
│
├── data_providers/               # Data fetching
│   ├── yfinance_provider.py      # Yahoo Finance (primary)
│   └── breeze_provider.py        # Breeze API (fallback)
│
├── exporters/                    # Report generation
│   ├── csv_exporter.py           # CSV output
│   └── html_exporter.py          # HTML dashboard
│
├── indicators/                   # Technical indicators
│   └── candle_aggregator.py      # 15-min from 5-min
│
├── Universe Files
│   ├── banknifty_constituents.txt (14 stocks)
│   ├── nifty50_constituents.txt (50 stocks)
│   ├── nifty_constituents.txt (100 stocks)
│   └── niftylarge_constituents.txt (257 stocks)
│
└── Configuration
    ├── fallback_strategy_config.json
    └── Various JSON metadata files
```

---

## 🔄 Data Processing Pipeline

### Scoring Algorithm

For each stock:

```
1. FETCH DATA (from yFinance)
   ├─ 1-hour candles (intraday)
   ├─ Daily candles (short-term)
   └─ Weekly candles (long-term)

2. CALCULATE INDICATORS
   ├─ EMA (Exponential Moving Average)
   ├─ MACD (Momentum)
   ├─ RSI (Overbought/Oversold)
   ├─ ATR (Volatility)
   └─ Bollinger Bands

3. SCORE EACH TIMEFRAME (-1 to +1)
   ├─ Momentum Score
   ├─ Trend Score
   └─ Volatility Score

4. COMPOSITE SCORE (Weighted by mode)
   ├─ Swing: 50% 1H + 30% 1D + 20% 1W
   ├─ Intraday: 70% 1H + 20% 1D + 10% 1W
   └─ Position: 20% 1H + 30% 1D + 50% 1W

5. OUTPUT
   ├─ CSV row
   └─ HTML entry
```

### Rate Limiting Strategy

```
Batch Processing:
├─ Process 8 stocks in parallel
├─ 0.2s delay between individual requests
├─ 1.5s delay between batches
└─ Exponential backoff on failures (0.5s → 10s max)

Result: No throttling, no timeouts
Prevents "thundering herd" API problem
```

### Caching Layer

```
Request for RELIANCE data
    ↓
Check SQLite cache (candle_cache.db)
    ├─ If fresh (< 24h): Return from DB
    └─ If expired: Fetch from API & cache
    
Benefits:
├─ 20-30% faster on repeat runs
├─ Less API calls = safer rate limiting
└─ Historical data always available
```

---

## 🎯 Core Components Explained

### 1. Main Entry Point: `nifty_bearnness_v2.py`

**What it does:**
- Parses CLI arguments
- Loads stock universe
- Spawns 8 worker threads
- Coordinates scoring
- Generates reports

**Key functions:**
```python
main()                  # CLI & initialization
fetch_stock_data()      # Parallel fetching
process_stock()         # Individual stock scoring
save_csv()              # CSV export
save_html()             # HTML report generation
print_results()         # Console output
```

### 2. Scoring Engine: `core/scoring_engine.py`

**Calculates bearness/bullishness**

Three modes:
- **Swing** (default): Balanced 2-5 day analysis
- **Intraday**: Favors 1H data for same-day trades
- **Position**: Long-term multi-week focus

Score range: `-1.0` (most bullish) to `+1.0` (most bearish)

### 3. Data Providers

**yFinance (Primary)**
- ✓ Free, no auth required
- ✓ All 257+ stocks covered
- ✓ ~0.2-0.3s per stock

**Breeze API (Optional)**
- ✓ Faster (~0.1s per stock)
- ✓ Requires API credentials
- ✓ Only 57 largecap stocks

**Fallback Strategy**
```
Try Breeze → Fail → Use yFinance → Fail → Daily cache
```

### 4. Rate Limiter: `wait_strategy.py`

**Prevents API throttling**

```python
class BatchRequestHandler:
    batch_size = 8              # Process 8 in parallel
    inter_batch_delay = 1.5     # Wait 1.5s between batches
    request_delay = 0.2         # 200ms between individual requests

@retry_with_backoff(max_attempts=3)
def fetch_with_retry(symbol):
    """Auto-retry with exponential backoff"""
```

### 5. Configuration: `config_manager.py`

**Centralized settings**

```python
UNIVERSES = {
    'banknifty': 14,      # Banking sector
    'nifty50': 50,        # Top 50 stocks
    'nifty': 100,         # NIFTY100
    'niftylarge': 257     # NIFTY500 validated
}

SCORING_MODES = {
    'swing': {'1h': 50%, '1d': 30%, '1w': 20%},
    'intraday': {'1h': 70%, '1d': 20%, '1w': 10%},
    'position': {'1h': 20%, '1d': 30%, '1w': 50%}
}

PERFORMANCE = {
    'max_workers': 6,           # Thread count
    'cache_enabled': True,
    'cache_ttl_hours': 24
}
```

### 6. Output Formatters

**HTML Report** (`exporters/html_exporter.py`)
- Interactive dashboard
- Sortable/filterable table
- Color-coded scores
- Charts & visualizations
- Auto-refresh every 15 min

**CSV Export** (`exporters/csv_exporter.py`)
- Excel-ready format
- All columns with metadata
- Import to trading apps
- Lightweight & portable

---

## 📊 Technical Indicators Reference

| Indicator | Purpose | Range | Interpretation |
|-----------|---------|-------|-----------------|
| **EMA** | Momentum | Trend following | >Price=Bullish, <Price=Bearish |
| **MACD** | Trend strength | Crossover | Positive=Bullish, Negative=Bearish |
| **RSI** | Overbought/Oversold | 0-100 | >70=Overbought, <30=Oversold |
| **ATR** | Volatility | Varies | High=High risk, Low=Consolidation |
| **Bollinger** | Support/Resistance | Price bands | Outside=Breakout, Inside=Coiling |

---

## 🔧 Threading & Performance

### Thread Allocation (6-thread default)

```
Total: 6 worker threads

Distribution (2:1 ratio yF:Breeze):
├─ 4 yFinance workers
│   └─ Each handles 1-2 stocks (~0.3s/stock)
│
└─ 2 Breeze workers
    └─ Each handles 1 stock (~0.1s/stock)

Total for 257 stocks: ~52.5 seconds
```

### Optimization Options

**Use 8 threads (for powerful machines):**
```bash
python nifty_bearnness_v2.py --num-threads 8
```
Distribution: 5 yFinance + 2 Breeze + 1 overflow

**Disable threading:**
```bash
python nifty_bearnness_v2.py --no-6thread
```
Uses sequential ThreadPoolExecutor (slower but safer)

**Quick mode (40% faster):**
```bash
python nifty_bearnness_v2.py --quick
```
Fewer candles, reduced timeframes, faster calculation

### Expected Performance

| Universe | Stocks | Mode | Threads | Time |
|----------|--------|------|---------|------|
| banknifty | 14 | intraday | 6 | 30s |
| nifty50 | 50 | swing | 6 | 1m 45s |
| niftylarge | 257 | swing | 6 | 5m 20s |
| niftylarge | 257 | swing | 8 | 5m 10s |
| niftylarge | 257 | position | 6 | 8m 30s |

---

## 🎯 Design Patterns Used

### 1. Factory Pattern (Data Providers)
```python
# Choose provider based on flag
provider = YFinanceAdapter() if use_yfinance else BreezeAdapter()
```

### 2. Strategy Pattern (Scoring Modes)
```python
# Different weights, same interface
engine = ScoringEngine(mode='swing')  # vs 'intraday' or 'position'
```

### 3. Decorator Pattern (Retry Logic)
```python
@retry_with_backoff(max_attempts=3)
def fetch_data(symbol):
    # Auto-retries with exponential backoff
    return yfinance.download(symbol)
```

### 4. Thread Pool Pattern (Parallelization)
```python
with ThreadPoolExecutor(max_workers=8) as executor:
    futures = [executor.submit(score_stock, sym) for sym in symbols]
    for future in as_completed(futures):
        result = future.result()
```

---

## 🛠️ Error Handling

```
Network timeout
    ├─ Retry with 0.5s delay
    ├─ Retry with 1.0s delay
    ├─ Retry with 2.0s delay
    └─ Skip stock, log error

API rate limit (429)
    ├─ Increase batch delay
    └─ Retry next batch

Invalid symbol
    ├─ Skip gracefully
    └─ Log warning

Success
    ├─ Cache result
    └─ Score & queue
```

---

## 📈 Testing Strategy

### Quick Validation
```bash
# Test single stock
python nifty_bearnness_v2.py --universe nifty50 --quick

# Check cache
python -c "import sqlite3; conn = sqlite3.connect('candle_cache.db'); print(conn.execute('SELECT COUNT(*) FROM cache').fetchone())"
```

### Full Test
```bash
# Complete run with 100 stocks
python nifty_bearnness_v2.py --universe nifty --force-yf
```

### Deployment Test
```bash
# Verify scheduler works
python scheduler.py --test
```
└── reports/                    ← Generated HTML/CSV reports
```

---

## 📊 What The Screener Does

### 1. **Stock Selection**
- Loads 179 validated Indian stocks (NSE: NIFTY500 universe)
- Market cap validated: ≥15B INR
- All symbols verified with Yahoo Finance

### 2. **Score Calculation** (3 Timeframes)
Each stock gets a **composite score from -1 (bullish) to +1 (bearish)**

| Timeframe | Weight | Indicators | Use Case |
|-----------|--------|-----------|----------|
| **1H** | 50% | EMA, MACD, RSI | Short-term momentum (options selling) |
| **1D** | 30% | EMA, ATR, BBANDS | Mid-term trend | 
| **1W** | 20% | EMA, Volume, RSI | Long-term bias |

### 3. **Output Formats**
- **Ranked Table:** 179 stocks sorted by score
- **Option Selling Candidates:** Stocks with high theta decay potential
- **Interactive Filtering:** HTML report with sortable columns

---

## 🎯 Scoring Modes

### Swing Mode (Recommended) ✓
```bash
python nifty_bearnness_v2.py --mode swing
```
- **Weights:** 1H:50%, 1D:30%, 1W:20%
- **Use:** Multi-day swing trading & options selling
- **Bias:** Balanced across timeframes

### Intraday Mode
```bash
python nifty_bearnness_v2.py --mode intraday
```
- **Weights:** 1H:70%, 1D:20%, 1W:10%
- **Use:** Same-day trading
- **Bias:** Short-term momentum

### Longterm Mode
```bash
python nifty_bearnness_v2.py --mode longterm
```
- **Weights:** 1H:20%, 1D:30%, 1W:50%
- **Use:** Position trading
- **Bias:** Long-term trend

### Custom Mode
```bash
python nifty_bearnness_v2.py --swing-w 40 --intraday-w 40 --longterm-w 20
```

---

## 🔄 Wait Strategy (Rate Limiting)

**Purpose:** Prevent API timeouts when fetching 179+ stocks

### How It Works
```
Request 1  → 0.2s delay → Request 2
Batch 1-8  → 1.5s delay → Batch 9-16
(exponential backoff: 0.5s → 10s max)
```

### Enable/Disable
```bash
# Enable (default)
python nifty_bearnness_v2.py --universe nifty500

# Disable 
python nifty_bearnness_v2.py --universe nifty500 --no-wait-strategy
```

### Configuration
Edit `wait_strategy.py` lines 120-125:
```python
batch_size = 8                    # Stocks per batch
inter_batch_delay = 1.5           # Seconds between batches
request_delay = 0.2               # Seconds between individual requests
max_retries = 3                   # Retry attempts
exponential_base = 2              # Backoff multiplier
```

---

## 📁 Universe Configuration

### Active Lists

**nifty500_constituents.txt** (179 stocks)
- Validated ≥15B market cap
- Yahoo Finance verified symbols
- Updated January 23, 2026
- Includes `.NS` suffix for NSE listings

**nifty200_constituents.txt** (200 stocks)
- NIFTY200 official index
- High liquidity, large cap
- Legacy support only

### Adding Stocks
1. Edit `nifty500_constituents.txt`
2. Add one symbol per line (e.g., `RELIANCE.NS`)
3. Verify on Yahoo Finance before adding
4. Re-run screener

---

## 🛠️ Command Reference

### Basic Commands
```bash
# Full NIFTY500 screener
python nifty_bearnness_v2.py --universe nifty500 --mode swing --screener-format html --force-yf

# Faster NIFTY200 screener  
python nifty_bearnness_v2.py --universe nifty200 --mode swing

# CSV output only (faster)
python nifty_bearnness_v2.py --universe nifty500 --screener-format csv
```

### Advanced Options
```bash
# Parallel workers (default: 8)
python nifty_bearnness_v2.py --parallel 16

# Intraday + CSV export
python nifty_bearnness_v2.py --mode intraday --export my_results.csv

# Force Yahoo Finance (skip Breeze API)
python nifty_bearnness_v2.py --force-yf

# All stocks (includes all index universes)
python nifty_bearnness_v2.py --universe all
```

### Output Modes
```bash
# HTML Report (interactive, sortable)
--screener-format html

# CSV (fastest, Excel compatible)
--screener-format csv

# Both (HTML + CSV)
--screener-format both   # Not yet implemented
```

---

## 📈 Understanding the Scores

### Score Ranges
```
-1.0  ────────────────────────────  +1.0
 ↑                                   ↑
BULLISH                          BEARISH
(Sell Puts)                   (Sell Calls)
```

### Example Top Picks

**Most Bullish** (Best for Sell Put strategies):
```
MRPL       +0.224   "Strong momentum up, write puts"
PIDILITIND +0.204   "Clear uptrend, low IV premiums"
GAIL       +0.195   "Sustained buying pressure"
```

**Most Bearish** (Best for Sell Call strategies):
```
ADANIGREEN -0.345   "Downtrend confirmed, high theta"
ICICIGI    -0.259   "Weakness across all timeframes"
AMBUJACEM  -0.230   "Consolidation with sellers"
```

### Confidence Scores
- **100%:** All 3 timeframes agree
- **≥80%:** 2+ timeframes agree  
- **<60%:** Conflicting signals (skip these)

---

## 🔧 Configuration Files

### config_manager.py
Central settings for all screener parameters:
```python
DEFAULT_UNIVERSE = "nifty500"
DEFAULT_MODE = "swing"
MAX_WORKERS = 8
CACHE_ENABLED = True
```

### wait_strategy.py
API rate limiting and retry mechanisms:
```python
class APIRateLimiter:
    """Exponential backoff: 0.5s → 10s max"""
    
class BatchRequestHandler:
    """Groups 8 stocks per batch with 1.5s delays"""
```

---

## 📋 Universes Explained

| Universe | Stocks | Volatility | Liquidity | Use Case |
|----------|--------|-----------|----------|----------|
| **nifty50** | 50 | Low | Highest | Large cap ETFs, mutual funds |
| **nifty100** | 100 | Low-Mid | Very High | Blue chip options trading |
| **nifty200** | 200 | Mid | High | Balanced screener (fast) |
| **nifty500** ✓ | 179 | Mid-High | High | Full analysis (comprehensive) |
| **all** | 500+ | High | Medium | Research/backtesting |

**Recommended:** `nifty500` - Best balance of breadth and speed

---

## ⚙️ API Integration

### Yahoo Finance (Primary - `--force-yf`)
- **Pro:** Free, reliable, no auth needed
- **Data:** OHLCV candles, volumes
- **Speed:** 1-2 min for 179 stocks
- **Used by:** `nifty_bearnness_v2.py`

### Breeze Connect (Fallback)
- **Pro:** Real-time data, margin info
- **Con:** Requires API credentials
- **Config:** `.env` file with API key
- **Used by:** `core/data_providers/breeze_api.py`

### Default Priority
```
1. Yahoo Finance (if --force-yf)
2. Breeze API (if .env configured)
3. Error + Skip stock
```

---

## 🐛 Troubleshooting

### No Data Downloaded
```bash
# Check if symbols are in Yahoo Finance
python test_failed_symbols.py

# Force Yahoo Finance API
python nifty_bearnness_v2.py --force-yf

# Verify constituent file
cat nifty500_constituents.txt | head -20
```

### API Timeouts
```bash
# Increase wait strategy delays (edit wait_strategy.py)
inter_batch_delay = 2.0    # Increase from 1.5
request_delay = 0.5         # Increase from 0.2

# Or disable wait strategy
python nifty_bearnness_v2.py --no-wait-strategy
```

### Symbol Not Found
**Error:** `"Quote not found for symbol: SYMBOL"`

**Fix:**
1. Check if symbol has `.NS` suffix
2. Verify on [NSE Website](https://www.nseindia.com/)
3. Test with: `python test_failed_symbols.py SYMBOL`
4. Update `nifty500_constituents.txt` with correct ticker

---

## 📊 Performance Expectations

| Config | Time | Stocks | Notes |
|--------|------|--------|-------|
| nifty200 | 3-4 min | 200 | Baseline, fast |
| nifty500 | 8-12 min | 179+ | Comprehensive |
| all | 15-20 min | 500+ | Full universe |

**Optimization Tips:**
- Use `--screener-format csv` (faster than HTML)
- Reduce `--parallel` workers on slow internet
- Cache enabled by default (`candle_cache.db`)

---

## 🔐 Security & Config

### Environment Variables (.env)
```
BREEZE_API_KEY=your_api_key_here
CACHE_TTL_HOURS=24
LOG_LEVEL=INFO
```

### Data Cache
- **Location:** `candle_cache.db` (SQLite)
- **TTL:** 24 hours (configurable)
- **Size:** ~50MB for 179 stocks
- **Refresh:** Automatic on new run

---

## 📝 Output Examples

### HTML Report
```
Interactive dashboard with:
✓ Sortable table (click headers)
✓ Charts & visualizations
✓ Option selling candidates highlighted
✓ Risk/reward metrics
✓ Real-time scores
```

### CSV Output
```
Symbol,Score,Confidence,Price,ATR,SL%,Target%,Sector
MRPL,0.224,100,155.40,3.78%,12.61%,Metals
PIDILITIND,0.204,53,1447.90,2.20%,2.51%,Materials
...
```

---

## 🎓 Common Use Cases

### Option Selling Candidates
Look for scores between **-0.3 to +0.3** with **conf > 80%**:
- Stable premiums
- Predictable direction
- Good theta decay

### Swing Trade Entry Points
Look for **extreme scores** (< -0.2 or > 0.2) with **confidence 100%**:
- Strong directional bias
- Multi-timeframe agreement
- High probability setups

### Risk Management
Always check:
- **Confidence ≥ 80%** (avoid <60%)
- **Price position** (%BelowHigh, %AboveLow)
- **Volatility (ATR)** for position sizing

---

## 📞 Support & Resources

### Key Files Reference
- **Main Script:** `nifty_bearnness_v2.py`
- **Rate Limiting:** `wait_strategy.py`
- **Config:** `config_manager.py`
- **Daily Job:** `scheduler.py`
- **Stocks List:** `nifty500_constituents.txt`

### Documentation
- **THIS FILE:** `WIKI.md` - Complete reference
- **Architecture:** `ARCHITECTURE.md` - Code structure
- **README:** Quick start guide
- **Archived Docs:** `ARCHIVE/docs/` - Historical documentation

### Testing
- **Symbol Validator:** `test_failed_symbols.py`
- **Database:** `candle_cache.db` (auto-managed)
- **Logs:** `logs/` directory

---

## 🚀 Next Steps

1. **First Run:** `python nifty_bearnness_v2.py --universe nifty200 --mode swing --screener-format html`
2. **Review Output:** Open `nifty_bearnness.html` in browser
3. **Schedule Daily:** Edit `scheduler.py` for morning runs
4. **Customize:** Adjust weights in `config_manager.py`
5. **Monitor:** Check `logs/` for errors/warnings

---

**Version:** 2.0 | **Updated:** Jan 23, 2026 | **Maintained by:** Development Team
