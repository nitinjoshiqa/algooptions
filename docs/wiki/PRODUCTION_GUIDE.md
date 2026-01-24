# Production Guide - NIFTY Bearnness Screener

## System Overview

The NIFTY Bearnness Screener is a production-ready stock analysis tool that combines:
- **Technical Analysis**: Bearness scoring via momentum, trend, volatility
- **Multi-timeframe**: Intraday (5m), Swing (15m/30m/1h), Position (daily)
- **Data Intelligence**: Hybrid Breeze + yFinance with intelligent fallback
- **Option Strategies**: Automated put/call spreads, strangles, straddles
- **Support/Resistance**: Dynamic level calculation with breakout detection
- **Sector Analysis**: Real-time sector classification and mapping

---

## Installation

### Prerequisites
- Python 3.12+ (tested on 3.11+)
- Windows/Linux/Mac compatible
- ~500MB disk space (includes cache database)

### Quick Setup
```bash
# Clone repository
git clone https://github.com/yourusername/algooptions.git
cd algooptions

# Create virtual environment
python -m venv .venv
.venv\Scripts\activate  # Windows
source .venv/bin/activate  # Linux/Mac

# Install dependencies
pip install -r requirements.txt
```

### Configuration
1. **Breeze API** (Optional but recommended):
   - Create `.env` file with:
     ```
     BREEZE_API_KEY=your_key_here
     BREEZE_USER_ID=your_user_id
     BREEZE_PASSWORD=your_password
     ```
   - Leave empty to use yFinance fallback (100% functional)

2. **Database Path** (Optional):
   - Edit `core/config.py` line 18:
     ```python
     DB_PATH = "path/to/your/database.db"
     ```

---

## Running the Screener

### Command Syntax
```bash
python nifty_bearnness_v2.py [OPTIONS]
```

### Essential Options

| Option | Values | Default | Notes |
|--------|--------|---------|-------|
| `--universe` | `banknifty`, `nifty50`, `nifty`, `niftylarge` | nifty | Stock universe |
| `--mode` | `intraday`, `swing`, `position` | swing | Timeframe analysis |
| `--num-threads` | `6`, `8` | `6` | Thread count (6-thread default) |
| `--quick` | flag | disabled | 40% faster (fewer candles) |
| `--screener-format` | `html`, `csv`, `both` | `both` | Output format |

### Quick Examples

```bash
# Analyze banknifty (14 stocks) - Intraday mode, 6 threads, 2 minutes
python nifty_bearnness_v2.py --universe banknifty --mode intraday --quick

# Analyze niftylarge (257 stocks) - Swing mode, 8 threads, full analysis
python nifty_bearnness_v2.py --universe niftylarge --mode swing --num-threads 8

# Generate HTML + CSV reports
python nifty_bearnness_v2.py --universe nifty --screener-format both

# Disable multi-threading (standard execution)
python nifty_bearnness_v2.py --universe nifty50 --no-6thread
```

---

## Output Interpretation

### Bearness Score
- **Range**: -1.0 (most bullish) to +1.0 (most bearish)
- **Actionable**: |score| >= 0.35 AND confidence >= 60%
- **Components**: Momentum (40%) + Trend (30%) + Volatility (30%)

### Confidence %
- **>80%**: High conviction (prefer for entry)
- **60-80%**: Moderate conviction (confirm with other indicators)
- **<60%**: Low conviction (filter out in --quick mode)

### Output Files
```
nifty_bearnness.html          ← Interactive dashboard with charts
nifty_bearnness.csv           ← Excel-importable data
reports/                      ← Timestamped backups (auto-generated)
```

### CSV Columns
```
Symbol      → Stock ticker
Bearness Score → -1 to +1, lower is more bearish
Confidence %   → How certain the score is (60-95%)
Price          → Last traded price
ATR            → Average True Range (volatility)
SL%            → Suggested stop loss %
Target%        → Profit target %
Sector         → Stock sector (Banking, IT, etc.)
Puts Strat      → Recommended put spread
Calls Strat     → Recommended call spread
```

---

## Performance Benchmarks

### Execution Times (Local testing)

| Universe | Stocks | Mode | Threads | Time |
|----------|--------|------|---------|------|
| banknifty | 14 | intraday | 6 | 30s |
| nifty50 | 50 | swing | 6 | 1m 45s |
| niftylarge | 257 | swing | 6 | 5m 20s |
| niftylarge | 257 | swing | 8 | 5m 10s |
| niftylarge | 257 | position | 6 | 8m 30s |

**Notes:**
- Times include data fetching, analysis, enrichment, and report generation
- First run may be slower (database initialization)
- Subsequent runs use cache (20-30% faster)

---

## Data Sources

### Priority Order
1. **Breeze API** (10% of data)
   - Extremely accurate, rate-limited to ~40-50 req/min
   - Only covers 57 largecap NIFTY stocks
   - Reserved for highcap analysis

2. **yFinance** (90% of data)
   - Reliable, no rate limits, all universes
   - Slightly delayed data (~15-30 min)
   - Automatic fallback for missing stocks

3. **Daily Fallback** (if above fail)
   - Cached daily OHLC data
   - Used only when live data unavailable

### Intelligent Routing
- The system automatically determines optimal data source per stock
- If Breeze has data → use Breeze (faster, more accurate)
- If Breeze timeout → fallback to yFinance
- If both fail → use cached daily data
- All routing is transparent (logged in console output)

---

## Troubleshooting

### Issue: "No candles returned for interval 5minute"
**Solution:** This is expected! Breeze has limited intraday data.
- System automatically falls back to yFinance for that stock
- You'll see "[DEBUG] Fallback to yFinance for 15min" message
- Score calculation continues normally

### Issue: Execution takes >10 minutes
**Problem:** Likely running on single thread or using --position mode
```bash
# Check threads
python nifty_bearnness_v2.py --universe niftylarge --quick --num-threads 8

# Use faster mode
python nifty_bearnness_v2.py --universe niftylarge --mode intraday --quick
```

### Issue: yFinance rate limiting
**Symptom:** Errors mentioning "Too many requests"
**Solution:** Already handled! System has intelligent wait strategy:
- Automatic delay between requests (100-500ms)
- Exponential backoff on retry
- Per-stock timeout of 10 seconds

### Issue: Missing Breeze API
**Not a problem!** System works 100% with yFinance alone.
- Leave `.env` file empty or remove it
- All 257+ stocks will use yFinance
- Slightly slower but equally accurate

---

## API Reference

### Main Entry Point
```python
# nifty_bearnness_v2.py

# Import core components
from core.scoring_engine import BearnessScoringEngine
from core.universe import UniverseManager
from core.option_strategies import suggest_option_strategy

# Create engine
engine = BearnessScoringEngine()

# Get universe
universes = UniverseManager()
stocks = universes.get('niftylarge')  # Get 257 NIFTY500 stocks

# Score a stock
result = engine.score_stock(symbol='HDFC', mode='swing')
print(f"Score: {result['bearness_score']}, Confidence: {result['confidence']}")

# Get option strategy
strat = suggest_option_strategy(result)
print(f"Strategy: {strat['name']}")
```

---

## Architecture

### Component Organization
```
algooptions/
├── nifty_bearnness_v2.py    ← Main entry point
├── core/                     ← Core modules
│   ├── scoring_engine.py     ← Bearness calculation
│   ├── universe.py           ← Stock universe management
│   ├── option_strategies.py  ← Option recommendation engine
│   ├── sector_mapper.py      ← Sector classification
│   ├── support_resistance.py ← S/R level calculation
│   ├── performance.py        ← Analytics tracker
│   └── config.py             ← Configuration constants
├── data_providers/           ← Data fetching
│   ├── breeze_provider.py    ← Breeze API wrapper
│   └── yfinance_provider.py  ← yFinance wrapper
├── wait_strategy.py          ← API rate limiting
├── event_calendar.py         ← Economic events
└── [universe files]          ← Stock lists (constituents)
```

---

## Code Quality

### Testing
```bash
# Run existing tests (if available)
python -m pytest tests/ -v

# Manual validation
python quick_validate_direct.py
```

### Code Style
- PEP 8 compliant
- Type hints for functions
- Comprehensive docstrings
- Thread-safe operations

---

## Deployment

### Local Scheduling
```bash
# Windows Task Scheduler
# Create task to run:
cd d:\DreamProject\algooptions && .\.venv\Scripts\activate && python nifty_bearnness_v2.py --universe niftylarge --mode swing --quick

# Run daily at 15:30 (market close)
```

### Cloud Deployment
```bash
# Docker containerization (if needed)
# Requirements: python:3.12-slim + dependencies

# Run on schedule:
# AWS Lambda / Google Cloud Functions / Heroku
```

---

## Version History

**v2.0** (Jan 24, 2026)
- ✅ 6-thread default execution
- ✅ Dynamic thread allocation (2:1 ratio)
- ✅ Intelligent API fallback
- ✅ Support/Resistance integration
- ✅ Production-optimized performance

**v1.0** (Jan 2026)
- Initial release with single-threaded analysis
- Breeze + yFinance integration
- Basic bearness scoring

---

## Support & Contributing

### Issues?
1. Check troubleshooting section above
2. Review console output (timestamps + [DEBUG] messages)
3. Check `.env` configuration
4. Verify internet connectivity

### Want to Contribute?
```bash
git checkout -b feature/your-feature
# Make changes
git commit -am "Add your feature"
git push origin feature/your-feature
# Create pull request
```

---

## License

MIT License - See LICENSE file for details

**For questions or issues, create a GitHub Issue with:**
- Command you ran
- Full error message
- Output of `python --version`
- Which universe you used
