#!/usr/bin/env python3
"""
Diagnose why 76 NIFTY200 stocks have no data.
Test different symbol formats and data sources.
"""

import sys
sys.path.insert(0, '/root/algooptions')

from data_providers import get_intraday_candles_for, YFinanceProvider
import pandas as pd

# Stocks reported as "no data"
NO_DATA_STOCKS = [
    'BSOFT', 'DEEPAKFERT', 'ESCORTS', 'EXIDEIND', 'FORCEMOT', 'BOSCH', 'COMFORTIND', 
    'DALBHUMI', 'GUJALKALI', 'HATSUN', 'GLOSTERIND', 'GSKPHARMA', 'IPCALAB', 'KIOCL', 
    'JYOTHYLAB', 'INFOSYS', 'LTTS', 'KAMINENI', 'HDFC', 'LAXMIMACH', 'MEDPLUS', 'MIDHANI', 
    'MOIL', 'MAHEINDRA', 'MSPL', 'MINDTREE', 'NLCINDIA', 'NOCIL', 'PAGEIND', 'PDSL', 
    'PFIZER', 'NITINSOFTW', 'MUTHYALARM', 'PIIND', 'RATNAMANI', 'PHILIPSFOOD', 'PRECWIRES', 
    'SIEMENS', 'SHREECEM', 'SOFTTECH', 'SONACOMS', 'SPORTSART', 'SUNTV', 'SHRIRAMFIN', 
    'SUNPHARMA', 'TATACONSUM', 'TATAELXSI', 'TATASTEEL', 'TATAMOTORS', 'TATATECH', 
    'SOLARINDS', 'TCSAUTO', 'TECHM', 'THERMAX', 'TATAPOWER', 'TITAN', 'TORNTPOWER', 
    'ULTRACEMCO', 'UNITDSPR', 'TVSMOTOR', 'TIINDIA', 'UNILEVER', 'UPL', 'TORNTPHARM', 
    'VBL', 'VGUARD', 'VEDL', 'VINATIORGA', 'VRLLOG', 'WABCOINDIA', 'WESTLIFE', 'WHIRLPOOL', 
    'YESBANK', 'ZYDUSLIFE', 'ZEEL', 'ZYDUSWELL'
]

print(f"Diagnosing {len(NO_DATA_STOCKS)} stocks with no data...")
print("=" * 80)

# Test each stock with different formats
results = []

for symbol in NO_DATA_STOCKS[:10]:  # Test first 10 to save time
    print(f"\n[{symbol}] Testing symbol formats...")
    
    variants = [
        symbol,                          # INFOSYS
        symbol + '.NS',                  # INFOSYS.NS
        symbol.upper(),                  # INFOSYS (already upper)
        symbol.lower() + '.NS',          # infosys.ns
    ]
    
    found = False
    for variant in variants:
        try:
            yf_provider = YFinanceProvider()
            # Try to get spot price (faster test than full candles)
            price = yf_provider.get_spot_price(variant)
            if price:
                print(f"  ✓ {variant}: Got price {price}")
                found = True
                results.append({
                    'symbol': symbol,
                    'working_format': variant,
                    'price': price,
                    'status': 'FOUND'
                })
                break
        except Exception as e:
            print(f"  ✗ {variant}: {str(e)[:50]}")
    
    if not found:
        print(f"  ✗ {symbol}: No working format found")
        results.append({
            'symbol': symbol,
            'working_format': None,
            'price': None,
            'status': 'NOT_FOUND'
        })

print("\n" + "=" * 80)
print("\nSUMMARY:")
print("-" * 80)

found_count = sum(1 for r in results if r['status'] == 'FOUND')
not_found_count = len(results) - found_count

print(f"Found with data: {found_count}/{len(results)}")
print(f"Not found: {not_found_count}/{len(results)}")

print("\nDetailed results:")
for r in results:
    print(f"  {r['symbol']:15} -> {r['status']:10} ({r['working_format']})")

# Save results
import json
with open('diagnose_missing_stocks_results.json', 'w') as f:
    json.dump(results, f, indent=2)
print("\nResults saved to diagnose_missing_stocks_results.json")
