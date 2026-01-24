"""Configuration constants."""
import os

# Exchange and product settings
EXCHANGE = "NSE"
PRODUCT = "cash"

# Indicator settings
OPENING_RANGE_MINUTES = 30
VWAP_LOOKBACK_MIN = 60
TREND_CONFIRM_BARS = 3

# File paths
BASE_DIR = os.path.dirname(os.path.dirname(__file__))
CONST_FILE = os.path.join(BASE_DIR, "nifty_constituents.txt")
OUT_CSV = os.path.join(BASE_DIR, "nifty_bearnness.csv")

# Default weights for different modes
MODE_WEIGHTS = {
    'intraday': {'intraday': 0.25, 'swing': 0.50, 'longterm': 0.25},
    'swing': {'intraday': 0.35, 'swing': 0.35, 'longterm': 0.30},
    'longterm': {'intraday': 0.15, 'swing': 0.25, 'longterm': 0.60}
}

# Market regime weight adjustments
REGIME_WEIGHTS = {
    'strong_trend': {'intraday': 0.60, 'swing': 0.25, 'longterm': 0.15},
    'weak_trend': {'intraday': 0.40, 'swing': 0.35, 'longterm': 0.25},
    'high_volatility': {'intraday': 0.40, 'swing': 0.30, 'longterm': 0.30},
    'consolidation': {'intraday': 0.35, 'swing': 0.35, 'longterm': 0.30}
}
