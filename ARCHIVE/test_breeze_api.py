#!/usr/bin/env python3
"""Diagnostic test for Breeze API candle fetching."""

import sys
sys.path.insert(0, 'd:/DreamProject/algooptions')

from utils.breeze_api import get_breeze_instance
from datetime import datetime, timedelta

print('BREEZE API DIAGNOSTIC TEST')
print('=' * 70)
print()

# Check Breeze instance
breeze = get_breeze_instance()
print(f'Breeze instance type: {breeze.__class__.__name__}')
print(f'Is dummy: {breeze.__class__.__name__ == "_DummyBreeze"}')
print()

if breeze.__class__.__name__ == "_DummyBreeze":
    print('[RESULT] Breeze API is NOT available (using dummy)')
    print()
    print('Possible reasons:')
    print('  1. BreezeConnect module not installed')
    print('  2. Breeze credentials missing (.env file)')
    print('  3. Session token invalid or expired')
    sys.exit(1)

# Try to fetch candles directly
print('Testing Breeze candle fetch...')
print('-' * 70)

test_symbols = ['TCS', 'INFY', 'HDFCBANK', 'RELIANCE', 'ICICIBANK']

total_candles = 0
successful = 0

for symbol in test_symbols:
    print(f'{symbol}:')
    
    try:
        # Try 5-minute candles
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
        
        if res:
            status = res.get('Status')
            success = res.get('Success', [])
            error = res.get('Error', 'None')
            
            print(f'  Status: {status}')
            print(f'  Candles: {len(success) if success else 0}')
            
            if len(success) > 0:
                successful += 1
                total_candles += len(success)
                print(f'  Sample: {success[0]}')
            
            if error and error != 'None':
                print(f'  Error: {error}')
        else:
            print(f'  Result: None (API returned None)')
    except Exception as e:
        print(f'  Exception: {type(e).__name__}: {str(e)[:100]}')
    
    print()

print('=' * 70)
print(f'Summary:')
print(f'  Successfully fetched: {successful}/{len(test_symbols)} symbols')
print(f'  Total candles retrieved: {total_candles}')

if successful > 0:
    print()
    print('[RESULT] ✓ Breeze API is WORKING - can fetch candles')
else:
    print()
    print('[RESULT] ✗ Breeze API returned no candles - check credentials/permissions')
