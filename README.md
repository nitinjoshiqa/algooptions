# NIFTY Bearnness Screener

Advanced technical stock screener for identifying bearish & bullish trading opportunities across NIFTY indices using multi-timeframe analysis, option strategies, and intelligent data sourcing.

**Status:** ✅ Production Ready  
**Python:** 3.12+  
**Coverage:** 257 NIFTY500 stocks | 14 BANKNIFTY | 50 NIFTY50  
**Performance:** 52.5s (6-thread) | Full reports in <6 minutes

---

## 🚀 Quick Start (5 minutes)

### 1. Clone & Setup
```bash
git clone https://github.com/yourusername/algooptions.git
cd algooptions
python -m venv .venv
.venv\Scripts\activate  # Windows
source .venv/bin/activate  # Linux/Mac
pip install -r requirements.txt
```

### 2. Run Analysis
```bash
# Analyze 14 BANKNIFTY stocks in 30 seconds
python nifty_bearnness_v2.py --universe banknifty --quick

# Analyze 50 NIFTY50 stocks in 2 minutes
python nifty_bearnness_v2.py --universe nifty50

# Full analysis: 257 NIFTY500 stocks in 5-6 minutes
python nifty_bearnness_v2.py --universe niftylarge --mode swing
```

### 3. View Results
- **HTML Dashboard:** `nifty_bearnness.html` (open in browser)
- **CSV Export:** `nifty_bearnness.csv` (open in Excel)
- **Console Output:** Top bearish/bullish stocks with scores

---

## 📖 First Time? Read This

👉 **New to the screener?** Start with **[QUICKSTART.md](docs/wiki/QUICKSTART.md)** (5-min guide)  
👉 **Ready for details?** Read **[PRODUCTION_GUIDE.md](docs/wiki/PRODUCTION_GUIDE.md)** (complete reference)  
👉 **Troubleshooting?** Check **[PRODUCTION_GUIDE.md#troubleshooting](docs/wiki/PRODUCTION_GUIDE.md#troubleshooting)**

---

## 📚 Documentation

Start with one of these based on your needs:

| Document | For... | Read Time |
|----------|--------|-----------|
| **[docs/wiki/QUICKSTART.md](docs/wiki/QUICKSTART.md)** | 🟢 **New users** - Install & run in 5 min | 5 min |
| **[docs/wiki/PRODUCTION_GUIDE.md](docs/wiki/PRODUCTION_GUIDE.md)** | 🟡 **All users** - Complete reference & troubleshooting | 20 min |
| **[docs/wiki/WIKI.md](docs/wiki/WIKI.md)** | 🔵 **Developers** - System design, architecture & advanced | 30 min |
| **[docs/wiki/CONTRIBUTING.md](docs/wiki/CONTRIBUTING.md)** | 🟠 **Contributors** - How to contribute code | 10 min |

### Navigation Quick Tips
- **Just getting started?** → Read **[docs/wiki/QUICKSTART.md](docs/wiki/QUICKSTART.md)** first (5 minutes)
- **Running into issues?** → Check **[docs/wiki/PRODUCTION_GUIDE.md#troubleshooting](docs/wiki/PRODUCTION_GUIDE.md#troubleshooting)**
- **Want system architecture?** → See **[docs/wiki/WIKI.md#-system-architecture](docs/wiki/WIKI.md#-system-architecture)**
- **Understanding the score?** → See **[docs/wiki/PRODUCTION_GUIDE.md#output-interpretation](docs/wiki/PRODUCTION_GUIDE.md#output-interpretation)**
- **Want to contribute?** → Read **[docs/wiki/CONTRIBUTING.md](docs/wiki/CONTRIBUTING.md)**

---

## ⚡ Core Commands

```bash
# Basic usage
python nifty_bearnness_v2.py

# With all options
python nifty_bearnness_v2.py \
    --universe nifty500 \
    --mode swing \
    --screener-format html \
    --force-yf

# Disable rate limiting (not recommended)
python nifty_bearnness_v2.py --no-wait-strategy
```

**Complete command reference:** See [WIKI.md > Command Reference](WIKI.md#command-reference)

---

## 📊 What It Does

1. **Fetches** real-time OHLCV data (1H, 1D, 1W timeframes)
2. **Calculates** technical scores using EMA, MACD, RSI, ATR, Bollinger Bands
3. **Scores** across 3 timeframes with configurable weights
4. **Ranks** 179 stocks by composite bearness score
5. **Outputs** interactive HTML report + CSV export

**Sample Output:**
```
Rank  Symbol      Score   Conf%  Price
────────────────────────────────────────
1     ESCORTS     -0.642   94%   1286.50
2     BOSCHLTD    -0.598   92%   17450.00
3     ALKEM       -0.571   88%   3205.25
...
```

---

## 🔧 Configuration

### Scoring Modes

| Mode | 1H Weight | 1D Weight | 1W Weight | Use Case |
|------|-----------|-----------|-----------|----------|
| **swing** (default) | 50% | 30% | 20% | 2-5 day trades |
| **intraday** | 70% | 20% | 10% | Same-day trades |
| **longterm** | 20% | 30% | 50% | Multi-week trades |

```bash
python nifty_bearnness_v2.py --mode longterm
```

### Universe Selection

| Universe | Size | Symbols | Use |
|----------|------|---------|-----|
| nifty50 | 50 | Top 50 stocks | Quick test (2 min) |
| nifty200 | 200 | Top 200 stocks | Balanced (5 min) |
| nifty500 | 179 | Validated >=15B mcap | Full scan (10 min) |

```bash
python nifty_bearnness_v2.py --universe nifty200
```

**Full configuration guide:** [WIKI.md > Configuration](WIKI.md#configuration-files)

---

## 🏗️ Architecture

```
Data Fetch (API) → Score Calculation → Output Generation
     ↓                    ↓                      ↓
   yfinance          Technical Indicators    HTML/CSV
  + Cache            (EMA,MACD,RSI,ATR)     Reports
```

**Key Components:**
- `nifty_bearnness_v2.py` - Main screener (2,647 lines)
- `wait_strategy.py` - API rate limiting & retry logic
- `config_manager.py` - Centralized settings
- `nifty500_constituents.txt` - Stock universe (179 validated)

**For detailed architecture diagrams and component relationships:**  
See [ARCHITECTURE.md](ARCHITECTURE.md)

---

## ⚠️ Common Issues

| Problem | Solution |
|---------|----------|
| **Timeout/API errors** | Wait strategy enabled by default, but if issues: `--force-yf` flag forces Yahoo Finance |
| **No data for symbol** | Symbol format incorrect; check [WIKI.md > Troubleshooting](WIKI.md#troubleshooting) |
| **Old results showing** | Data is cached for 24h; delete `candle_cache.db` for fresh fetch |
| **Wrong scores** | Verify scoring mode with `--mode swing` (or intraday/longterm) |

**Full troubleshooting:** [WIKI.md > Troubleshooting Guide](WIKI.md#troubleshooting-guide)

---

## 🚀 Production Deployment

### Schedule Daily Runs
```bash
# Add to crontab (runs 3:30 PM every weekday)
30 15 * * 1-5 /usr/bin/python3 /path/to/nifty_bearnness_v2.py --universe nifty500 > /tmp/screener.log 2>&1
```

### Integrate with Trading System
```python
from nifty_bearnness_v2 import load_results

results = load_results('nifty_bearnness.csv')
for stock in results[results['Score'] < -0.5]:  # Bearish threshold
    print(f"Sell signal: {stock['Symbol']} @ {stock['Price']}")
```

**Full deployment guide:** [WIKI.md > Deployment](WIKI.md#production-deployment)

---

## 📈 Performance Expectations

| Universe | Stocks | Time | Cache Hit |
|----------|--------|------|-----------|
| nifty50 | 50 | 2-3 min | 30 sec |
| nifty200 | 200 | 5-6 min | 1 min |
| nifty500 | 179 | 10-12 min | 2 min |

*Times vary based on network speed and API response time*

---

## 🔗 Key Files

| File | Purpose | Size |
|------|---------|------|
| `nifty_bearnness_v2.py` | Main screener logic | 2,647 lines |
| `wait_strategy.py` | API rate limiting | ~200 lines |
| `config_manager.py` | Settings management | ~100 lines |
| `nifty500_constituents.txt` | Stock universe | 179 symbols |
| `candle_cache.db` | Data cache (SQLite) | Auto-managed |
| `nifty_bearnness.html` | Output report | Generated |
| `nifty_bearnness.csv` | CSV export | Generated |

---

## 📖 Additional Resources

- **[WIKI.md](WIKI.md)** - Complete reference documentation (16 sections)
- **[ARCHITECTURE.md](ARCHITECTURE.md)** - System design & data flow
- **[ARCHIVE/](ARCHIVE/)** - Historical documentation & deprecated files
- **Code Comments** - Each Python file has inline documentation

---

## 🤝 Contributing

To add new features:

1. **Check** [ARCHITECTURE.md](ARCHITECTURE.md) for system design
2. **Read** relevant code sections with `# Comments explaining logic`
3. **Test** with `--universe nifty50` first (2-min runs)
4. **Validate** output in `nifty_bearnness.csv`

---

## 📝 License & Attribution

Built for Indian stock market analysis using NSE/NIFTY indices.

**Data Source:** Yahoo Finance  
**Markets:** NSE (Bombay Stock Exchange)  
**Time Zone:** IST (UTC+5:30)

---

## ✅ Quality Checklist

- ✅ 179 validated stocks (market cap >= 15B INR)
- ✅ API rate limiting with exponential backoff
- ✅ 24-hour data cache with auto-expire
- ✅ 3-timeframe composite scoring
- ✅ HTML + CSV report generation
- ✅ Comprehensive documentation (WIKI + ARCHITECTURE)
- ✅ Production-ready error handling
- ✅ Configurable scoring weights & modes

---

**Version:** 2.0 | **Status:** ✅ Production Ready  
**Questions?** → See [WIKI.md](WIKI.md) | **Architecture?** → See [ARCHITECTURE.md](ARCHITECTURE.md)
run_daily_screener.bat
```

---

## 📊 Output Files
- **nifty_bearnness.html** - Visual report with charts
- **nifty_bearnness.csv** - Data in spreadsheet format
- **nifty_bearnness_filtered.csv** - Filtered/curated picks

---

## 🧹 Cleanup Summary
All old backtest files, debug scripts, and intermediate results have been removed. The workspace now contains:
- **15 files total** (vs 150+ before)
- **~1.2 MB** (vs several hundred MB before)
- Only essential production code and docs

---

## 📝 Notes
- All backtesting and validation is complete
- Production system is ready for deployment
- Check [START_HERE.md](START_HERE.md) for detailed instructions
