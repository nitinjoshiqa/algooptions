# API Reference

## Python Module: `nifty_bearnness_v2.py`

### Main Entry Point

```bash
python nifty_bearnness_v2.py [OPTIONS]
```

### Command-Line Arguments

```
--universe              Universe to screen (default: nifty)
                        Options: nifty, banknifty, nifty200, nifty50
                        
--mode                  Analysis mode (default: swing)
                        Options: intraday, swing, longterm
                        
--screener-format       Output format (default: html)
                        Options: csv, html, both
                        
--parallel              Number of parallel threads (default: 1)
                        Range: 1-8 (higher = faster but more CPU)
                        
--force-yf              Force Yahoo Finance (skip Breeze API)
                        Flag: --force-yf
                        
--quick                 Quick mode (fewer indicators, faster)
                        Flag: --quick
                        
--help                  Show help message
```

### Example Usage

```bash
# Basic
python nifty_bearnness_v2.py

# NIFTY 200 with parallel processing
python nifty_bearnness_v2.py --universe nifty200 --parallel 4

# BankNifty, swing mode, output both formats
python nifty_bearnness_v2.py --universe banknifty --mode swing --screener-format both

# Quick mode (for testing)
python nifty_bearnness_v2.py --universe nifty50 --quick

# Force Yahoo Finance (no Breeze)
python nifty_bearnness_v2.py --force-yf
```

---

## Core Modules

### `core/scoring_engine.py`
Calculates bearness/bullish scores

```python
from core.scoring_engine import BearnessScoringEngine

engine = BearnessScoringEngine()
score = engine.score_symbol('RELIANCE', data)
# Returns: {'score_5m': float, 'score_15m': float, 'score_1h': float, ...}
```

### `core/risk_management.py`
Calculates stop-loss, target, and position size

```python
from core.risk_management import calculate_risk

risk = calculate_risk(
    entry=100,
    atr=5,
    volatility=2.5,
    capital=100000
)
# Returns: {'sl': 97.5, 'target': 110, 'pos_size': 400}
```

### `core/option_strategies.py`
Recommends option strategies

```python
from core.option_strategies import suggest_option_strategy

strategy = suggest_option_strategy(
    is_bullish=True,
    is_bearish=False,
    volatility=2.5,
    confidence=75,
    score=0.42,
    option_score=0.5
)
# Returns: ('Long Call Spread', 'bullish')
```

---

## Output Files

### CSV Format
```
symbol,final_score,confidence,price,sl_price,target_price,rr_ratio,pos_size,
risk_level,market_regime,sector,trend,tf_align,strategy,...
```

Fields:
- `symbol` - Stock ticker
- `final_score` - Composite score (-1 to +1)
- `confidence` - Signal confidence (0-100)
- `price` - Current price
- `sl_price` - Suggested stop-loss
- `target_price` - Suggested target
- `rr_ratio` - Risk-to-reward ratio
- `pos_size` - Position size for 2% risk
- `risk_level` - NORMAL / MEDIUM / HIGH
- `market_regime` - Trending / Ranging / Volatile
- `sector` - Sector classification
- `trend` - Bull / Bear / Neutral
- `tf_align` - ✓✓✓ / ✓✓✗ / ✓✗✗
- `strategy` - Recommended options strategy

### HTML Format
Interactive report with:
- Dashboard summary
- Sortable data table
- Color-coded stocks
- Embedded strategy tooltips
- Responsive design

---

## Configuration

### Environment Variables (`.env`)
```
BREEZE_API_KEY=your_key_here
DATA_SOURCE=yfinance  # or 'breeze'
TIMEZONE=Asia/Kolkata
```

### Config Options (`core/config.py`)
```python
# Risk management
RISK_PER_TRADE = 0.02  # 2%
BASE_CONFIDENCE_THRESHOLD = 60

# Scoring weights
SWING_MODE_WEIGHTS = {'5m': 0.2, '15m': 0.3, '1h': 0.5}

# Output
OUT_CSV = 'nifty_bearnness.csv'
OUT_HTML = 'nifty_bearnness.html'
```

---

## Integration Examples

### Use with TA-Lib
```python
import talib

# Calculate RSI
rsi = talib.RSI(close, timeperiod=14)
```

### Database Integration
```python
from core.database import save_daily_score

save_daily_score(
    symbol='RELIANCE',
    score=0.42,
    timestamp=datetime.now()
)
```

---

## Troubleshooting API Issues

### ModuleNotFoundError
```
Error: No module named 'core'
Solution: Run from project root directory
```

### Connection Error
```
Error: Failed to connect to Breeze API
Solution: Use --force-yf flag to use Yahoo Finance
```

### Memory Error
```
Error: Memory full with --parallel 8
Solution: Reduce --parallel value (use 2-4)
```

---

See also: [Configuration](configuration.md), [Backtesting](backtesting.md)
