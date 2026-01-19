#!/usr/bin/env python3
"""Test BreezeConnect with valid credentials."""

from breeze_connect import BreezeConnect
import os
from dotenv import load_dotenv

load_dotenv()

api_key = os.getenv('BREEZE_API_KEY')
api_secret = os.getenv('BREEZE_API_SECRET')
session_token = os.getenv('BREEZE_SESSION_TOKEN')

print("Testing BreezeConnect with valid credentials...")
print(f"API Key: {api_key[:15]}...")
print(f"API Secret: {api_secret[:15]}...")
print(f"Session Token: {session_token}")

try:
    print("\n1. Initializing BreezeConnect...")
    bc = BreezeConnect(api_key=api_key)
    print("   ✓ Instance created")
    
    print("\n2. Generating session...")
    bc.generate_session(api_secret=api_secret, session_token=session_token)
    print("   ✓ Session established")
    
    # Test different symbols
    test_symbols = ['SBIN', 'ICICIBANK', 'HDFCBANK']
    
    print("\n3. Testing get_quotes for different symbols...")
    for sym in test_symbols:
        try:
            res = bc.get_quotes(stock_code=sym, exchange_code='NSE', product_type='cash')
            
            if res['Status'] == 200 and res['Success']:
                ltp = res['Success'][0]['ltp']
                print(f"   ✓ {sym}: LTP = {ltp}")
            else:
                print(f"   ✗ {sym}: Status {res['Status']} - {res.get('Error', 'Unknown error')}")
        except Exception as e:
            print(f"   ✗ {sym}: {type(e).__name__}: {e}")
    
    print("\n4. Testing get_historical_data...")
    from datetime import datetime, timedelta
    end_date = datetime.now()
    start_date = end_date - timedelta(days=5)
    
    res = bc.get_historical_data(
        stock_code='SBIN',
        exchange_code='NSE',
        product_type='cash',
        from_date=start_date.strftime('%Y-%m-%d'),
        to_date=end_date.strftime('%Y-%m-%d'),
        interval='1day'
    )
    
    if res['Status'] == 200 and res['Success']:
        print(f"   ✓ Retrieved {len(res['Success'])} candles")
        if res['Success']:
            first = res['Success'][0]
            print(f"   First candle: {first.get('datetime')} - Open: {first.get('open')}, Close: {first.get('close')}")
    else:
        print(f"   ✗ Status {res['Status']}: {res.get('Error')}")
    
    print("\n✓ BreezeProvider is working correctly!")
    
except Exception as e:
    print(f"\n✗ Critical Error: {type(e).__name__}: {e}")
    import traceback
    traceback.print_exc()
