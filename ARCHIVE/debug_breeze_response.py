#!/usr/bin/env python3
"""Debug Breeze API response structure."""

import sys
sys.path.insert(0, 'd:/DreamProject/algooptions')

from utils.breeze_api import get_breeze_instance
from datetime import datetime, timedelta
import json

print('BREEZE API RESPONSE DEBUG')
print('=' * 70)
print()

breeze = get_breeze_instance()

test_symbols = ['INFY', 'HDFCBANK', 'TCS']

for symbol in test_symbols:
    print(f'{symbol}:')
    print('-' * 70)
    
    end_time = datetime.now()
    start_time = end_time - timedelta(days=3)
    
    res = breeze.get_historical_data(
        interval='5minute',
        from_date=start_time.strftime('%Y-%m-%d'),
        to_date=end_time.strftime('%Y-%m-%d'),
        stock_code=symbol,
        exchange_code='NSE',
        product_type='MIS'
    )
    
    print(f'Response type: {type(res)}')
    print(f'Response keys: {res.keys() if res else "None"}')
    
    if res:
        print(f'Status: {res.get("Status")}')
        print(f'Success type: {type(res.get("Success"))}')
        print(f'Success value: {res.get("Success")[:50] if res.get("Success") else "None"}...')
        print(f'Error: {res.get("Error")}')
    
    print()

print('=' * 70)
print()
print('OBSERVATIONS:')
print('- TCS returns 309 candles (Success is a list)')
print('- INFY/HDFCBANK return Status 200 but Success is None')
print('- Possible issues:')
print('  1. Symbol not available in Breeze (coverage gap)')
print('  2. Symbol naming convention different')
print('  3. Market data subscription missing')
print('  4. Account permissions issue')
