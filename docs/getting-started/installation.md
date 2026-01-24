# Installation & Setup

## Prerequisites

- **Python 3.8+**
- **pip** (Python package manager)
- **Virtual Environment** (recommended)

## Step 1: Clone or Download

```bash
cd d:\DreamProject\algooptions
```

## Step 2: Create Virtual Environment

```bash
python -m venv .venv
.venv\Scripts\activate  # On Windows
# source .venv/bin/activate  # On Mac/Linux
```

## Step 3: Install Dependencies

```bash
pip install -r requirements.txt
```

## Step 4: Configure API Keys

Edit `.env` file with your credentials:

```env
# Breeze Connect API (Optional for live data)
BREEZE_API_KEY=your_api_key_here

# Data source
DATA_SOURCE=yfinance  # or 'breeze'
```

## Step 5: Run Screener

```bash
# For NIFTY 200
python nifty_bearnness_v2.py --universe nifty200 --mode swing --screener-format html

# For BankNifty
python nifty_bearnness_v2.py --universe banknifty --mode swing --screener-format html

# With parallel processing (faster)
python nifty_bearnness_v2.py --universe nifty200 --parallel 4
```

## Step 6: View Results

Results are saved to:
- `nifty_bearnness.html` - Interactive HTML report
- `nifty_bearnness.csv` - Data spreadsheet
- `reports/` - Timestamped backups

## Configuration Options

| Option | Default | Description |
|--------|---------|-------------|
| `--universe` | nifty | nifty, banknifty, nifty200, nifty50 |
| `--mode` | swing | intraday, swing, longterm |
| `--screener-format` | html | csv, html, both |
| `--parallel` | 1 | Number of parallel threads (2-8) |
| `--force-yf` | False | Force Yahoo Finance (skip Breeze) |
| `--quick` | False | Quick mode (fewer indicators) |

## Troubleshooting

### Issue: "ModuleNotFoundError: No module named 'core'"
**Solution:** Ensure you're running from the project root directory

### Issue: "API connection failed"
**Solution:** Use `--force-yf` flag to use Yahoo Finance instead of Breeze API

### Issue: "Slow processing"
**Solution:** Increase `--parallel` value (e.g., `--parallel 8`)

---

Next: [Quick Start Guide](quickstart.md)
