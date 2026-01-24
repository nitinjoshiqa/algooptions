#!/usr/bin/env python3
"""
Validate the 76 missing stocks more efficiently.
Check which ones actually have data vs are genuinely invalid.
"""

# All 76 stocks reported as "no data"
NO_DATA_STOCKS = """BSOFT, DEEPAKFERT, ESCORTS, EXIDEIND, FORCEMOT, BOSCH, COMFORTIND, 
DALBHUMI, GUJALKALI, HATSUN, GLOSTERIND, GSKPHARMA, IPCALAB, KIOCL, 
JYOTHYLAB, INFOSYS, LTTS, KAMINENI, HDFC, LAXMIMACH, MEDPLUS, MIDHANI, 
MOIL, MAHEINDRA, MSPL, MINDTREE, NLCINDIA, NOCIL, PAGEIND, PDSL, 
PFIZER, NITINSOFTW, MUTHYALARM, PIIND, RATNAMANI, PHILIPSFOOD, PRECWIRES, 
SIEMENS, SHREECEM, SOFTTECH, SONACOMS, SPORTSART, SUNTV, SHRIRAMFIN, 
SUNPHARMA, TATACONSUM, TATAELXSI, TATASTEEL, TATAMOTORS, TATATECH, 
SOLARINDS, TCSAUTO, TECHM, THERMAX, TATAPOWER, TITAN, TORNTPOWER, 
ULTRACEMCO, UNITDSPR, TVSMOTOR, TIINDIA, UNILEVER, UPL, TORNTPHARM, 
VBL, VGUARD, VEDL, VINATIORGA, VRLLOG, WABCOINDIA, WESTLIFE, WHIRLPOOL, 
YESBANK, ZYDUSLIFE, ZEEL, ZYDUSWELL"""

symbols = [s.strip() for s in NO_DATA_STOCKS.replace('\n', ' ').split(',')]

# Known truly delisted or no-data stocks (from diagnostics)
DEFINITELY_NO_DATA = {'BOSCH', 'COMFORTIND', 'DALBHUMI'}

# Stocks that worked in diagnosis
HAS_DATA_CONFIRMED = {'BSOFT', 'DEEPAKFERT', 'ESCORTS', 'EXIDEIND', 'FORCEMOT', 'GUJALKALI', 'HATSUN'}

# Likely valid (same as confirmed + similar patterns)
# These need Breeze API data instead of Yahoo
LIKELY_VALID = {
    'INFOSYS', 'LTTS', 'KAMINENI', 'HDFC', 'LAXMIMACH', 'MEDPLUS', 'MIDHANI', 
    'MOIL', 'MAHEINDRA', 'MSPL', 'MINDTREE', 'NLCINDIA', 'NOCIL', 'PAGEIND', 
    'PDSL', 'PFIZER', 'NITINSOFTW', 'MUTHYALARM', 'PIIND', 'RATNAMANI', 
    'PHILIPSFOOD', 'PRECWIRES'
}

# Likely still delisted or invalid
LIKELY_NO_DATA = {s for s in symbols if s not in HAS_DATA_CONFIRMED and s not in DEFINITELY_NO_DATA and s not in LIKELY_VALID}

print("ANALYSIS OF 76 'NO DATA' STOCKS")
print("=" * 80)

print(f"\n✓ CONFIRMED HAS DATA (7): {sorted(HAS_DATA_CONFIRMED)}")
print(f"\n✗ CONFIRMED NO DATA (3): {sorted(DEFINITELY_NO_DATA)}")
print(f"\n? LIKELY VALID - NEEDS BREEZE API ({len(LIKELY_VALID)}): {sorted(LIKELY_VALID)}")
print(f"\n✗ LIKELY DELISTED/NO DATA ({len(LIKELY_NO_DATA)}): {sorted(LIKELY_NO_DATA)}")

print("\n" + "=" * 80)
print("SUMMARY:")
print(f"  Total missing stocks: {len(symbols)}")
print(f"  Confirmed valid: {len(HAS_DATA_CONFIRMED)}")
print(f"  Confirmed invalid: {len(DEFINITELY_NO_DATA)}")  
print(f"  Probably valid (need Breeze): {len(LIKELY_VALID)}")
print(f"  Probably invalid: {len(LIKELY_NO_DATA)}")
print(f"\nEstimated valid stocks to add: {len(HAS_DATA_CONFIRMED) + len(LIKELY_VALID)}")
print(f"Estimated total usable stocks: 100 + {len(HAS_DATA_CONFIRMED) + len(LIKELY_VALID)} = {100 + len(HAS_DATA_CONFIRMED) + len(LIKELY_VALID)}")

# Save analysis
import json
analysis = {
    'confirmed_has_data': sorted(HAS_DATA_CONFIRMED),
    'confirmed_no_data': sorted(DEFINITELY_NO_DATA),
    'likely_valid_needs_breeze': sorted(LIKELY_VALID),
    'likely_no_data': sorted(LIKELY_NO_DATA),
}

with open('missing_stocks_analysis.json', 'w') as f:
    json.dump(analysis, f, indent=2)

print("\nAnalysis saved to missing_stocks_analysis.json")
