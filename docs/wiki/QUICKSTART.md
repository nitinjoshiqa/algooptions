# Getting Started - NIFTY Bearnness Screener

## What is This?

A **production-grade stock screener** that analyzes NIFTY (Indian stock market) securities to identify bearish and bullish trading opportunities using:
- Technical analysis (momentum, trend, volatility)
- Multi-timeframe analysis (intraday, swing, position)
- Automatic option strategy suggestions (puts, calls, spreads)
- Intelligent data sourcing (Breeze API + yFinance with smart fallback)

**Perfect for:** Day traders, swing traders, options traders, and automated trading systems.

---

## Installation (5 minutes)

### Step 1: Clone Repository
```bash
git clone https://github.com/yourusername/algooptions.git
cd algooptions
```

### Step 2: Create Virtual Environment
```bash
# Windows
python -m venv .venv
.\.venv\Scripts\activate

# Linux/Mac
python3 -m venv .venv
source .venv/bin/activate
```

### Step 3: Install Dependencies
```bash
pip install -r requirements.txt
```

### Step 4: (Optional) Add Breeze API Credentials
Create `.env` file in project root:
```
BREEZE_API_KEY=your_key
BREEZE_USER_ID=your_user_id
BREEZE_PASSWORD=your_password
```
⚠️ If no `.env` file: System uses yFinance (fully functional, all stocks covered)

---

## Run Your First Analysis (2 minutes)

### Analyze 14 BANKNIFTY Stocks
```bash
python nifty_bearnness_v2.py --universe banknifty --mode intraday --quick
```

**Expected output:**
- Console shows top bearish stocks with scores
- `nifty_bearnness.csv` - Data export
- `nifty_bearnness.html` - Interactive dashboard
- Time: ~30 seconds

### Analyze 257 NIFTY500 Stocks (Full Suite)
```bash
python nifty_bearnness_v2.py --universe niftylarge --mode swing --quick
```

**Expected output:**
- Full analysis with sector mapping, option strategies, S/R levels
- Timestamped backup in `reports/` folder
- Time: ~5-6 minutes with 6 threads (default)

---

## Understanding Results

### The CSV Output
Open `nifty_bearnness.csv` in Excel:

| Column | Meaning |
|--------|---------|
| **Symbol** | Stock ticker (e.g., HDFC, INFY) |
| **Bearness Score** | -1.0 (bullish) to +1.0 (bearish) |
| **Confidence %** | How certain we are (higher = more reliable) |
| **Price** | Last traded price |
| **SL%** | Suggested stop loss percentage |
| **Target%** | Profit target percentage |
| **Puts Strat** | Recommended put spread strategy |

### The HTML Dashboard
Open `nifty_bearnness.html` in browser:
- Visual charts for top bearish stocks
- Sortable/filterable data table
- One-click view of each stock's analysis

### Interpreting Bearness Score
```
Score = -0.35 to -0.50  →  Good bearish setup (shorts, puts)
Score = -0.10 to 0.10   →  Neutral (avoid)
Score = 0.35 to 0.50    →  Good bullish setup (longs, calls)
Score < -0.35 & Conf>80% → Actionable for entry
```

---

## Common Scenarios

### "I want to analyze only NIFTY 50 stocks"
```bash
python nifty_bearnness_v2.py --universe nifty50
```

### "I want faster results (40% quicker)"
```bash
python nifty_bearnness_v2.py --universe banknifty --quick
```

### "I want to see only CSV, not HTML"
```bash
python nifty_bearnness_v2.py --universe nifty --screener-format csv
```

### "I want to use 8 threads instead of 6"
```bash
python nifty_bearnness_v2.py --universe niftylarge --num-threads 8
```

### "I want position-level analysis (daily timeframe)"
```bash
python nifty_bearnness_v2.py --mode position
```

---

## Available Stock Universes

| Universe | Stocks | Use Case | Time |
|----------|--------|----------|------|
| `banknifty` | 14 | Banking sector only | 30s |
| `nifty50` | 50 | Top 50 largest | 2m |
| `nifty` | ~100 | NIFTY100 index | 3m |
| `niftylarge` | 257 | NIFTY500 validated stocks | 5-6m |

---

## Troubleshooting

### "I'm getting errors about Breeze API"
✅ **Normal!** This just means Breeze isn't available for that stock.  
Solution: System automatically uses yFinance (you'll see the fallback message).  
**No action needed** - analysis continues normally.

### "The analysis is taking too long"
**Check which mode you're using:**
- `--quick` is fastest (30-40% quicker)
- `--mode intraday` is faster than `--mode swing`
- Add `--num-threads 8` for more parallel processing

**Typical times:**
- banknifty: 30s
- nifty50: 2m
- niftylarge: 5-6m

### "I don't have the Breeze API credentials"
✅ **No problem!** System works 100% with yFinance alone.  
Just leave `.env` file blank or delete it.

### "The HTML report won't open"
Try opening with a different browser (Chrome, Firefox).  
If still broken, use CSV output instead: `--screener-format csv`

---

## Next Steps

1. **Try different universes:** Explore `nifty50`, `nifty`, `niftylarge`
2. **Try different modes:** Experiment with `intraday`, `swing`, `position`
3. **Check the scores:** Look for stocks with |score| >= 0.35 and confidence >= 80%
4. **Use the option strategies:** Each stock gets recommended puts/calls
5. **Review the full guide:** See [PRODUCTION_GUIDE.md](PRODUCTION_GUIDE.md) for advanced usage

---

## More Documentation

- **[PRODUCTION_GUIDE.md](PRODUCTION_GUIDE.md)** ← Complete reference with all features
- **[ARCHITECTURE.md](ARCHITECTURE.md)** ← System design & component details  
- **[WIKI.md](WIKI.md)** ← Full command reference & FAQ
- **Issues?** Check [PRODUCTION_GUIDE.md#troubleshooting](PRODUCTION_GUIDE.md#troubleshooting)

---

## Quick Reference Card

```bash
# Core command structure
python nifty_bearnness_v2.py [OPTIONS]

# Most common:
--universe {banknifty,nifty50,nifty,niftylarge}  # Which stocks to analyze
--mode {intraday,swing,position}                  # Timeframe (default: swing)
--num-threads {6,8}                               # Parallel threads (default: 6)
--quick                                           # 40% faster mode
--screener-format {html,csv,both}                 # Output type (default: both)
--no-6thread                                      # Disable multi-threading

# One-liners:
python nifty_bearnness_v2.py --universe banknifty --mode intraday --quick
python nifty_bearnness_v2.py --universe niftylarge --mode swing --num-threads 8
python nifty_bearnness_v2.py --universe nifty50 --screener-format html
```

---

**Ready? Run:** `python nifty_bearnness_v2.py --universe banknifty --quick`  
**Questions? Check:** [PRODUCTION_GUIDE.md](PRODUCTION_GUIDE.md)
