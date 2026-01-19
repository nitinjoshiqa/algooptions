#!/usr/bin/env python3
"""Test Breeze API responses directly"""

from breeze_connect import BreezeConnect
import os
import json
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv("BREEZE_API_KEY")
API_SECRET = os.getenv("BREEZE_API_SECRET")
SESSION_TOKEN = os.getenv("BREEZE_SESSION_TOKEN")

print("=" * 70)
print("BREEZE API TEST - GET_QUOTES")
print("=" * 70)

breeze = BreezeConnect(api_key=API_KEY)
print(f"\n1. Instance created: {type(breeze).__name__}")

result = breeze.generate_session(api_secret=API_SECRET, session_token=SESSION_TOKEN)
print(f"\n2. Session generated result: {result}")

# Test get_quotes
print("\n3. Testing get_quotes(stock_code='SBIN', exchange_code='NSE', product_type='cash')...")
quote = breeze.get_quotes(
    stock_code="SBIN",
    exchange_code="NSE",
    product_type="cash"
)
print(f"\nResponse type: {type(quote)}")
print(f"Response content:\n{json.dumps(quote, indent=2, default=str)}")

print("\n" + "=" * 70)
print("BREEZE API TEST - GET_HISTORICAL_DATA")
print("=" * 70)

print("\n4. Testing get_historical_data()...")
history = breeze.get_historical_data(
    stock_code="SBIN",
    exchange_code="NSE",
    product_type="cash",
    interval="1minute",
    from_date="2026-01-18",
    to_date="2026-01-19"
)
print(f"\nResponse type: {type(history)}")
if isinstance(history, dict):
    keys = list(history.keys())
    print(f"Response keys: {keys}")
    if 'Success' in history:
        success_data = history['Success']
        if isinstance(success_data, list):
            print(f"Success data count: {len(success_data)}")
            if len(success_data) > 0:
                print(f"\nSample records (first 3):")
                for i, record in enumerate(success_data[:3]):
                    print(f"  {i+1}. {json.dumps(record, default=str)}")
        else:
            print(f"Success data: {success_data}")

print(f"\nFull response (first 800 chars):\n{json.dumps(history, indent=2, default=str)[:800]}...")

print("\n" + "=" * 70)
print("ANALYSIS")
print("=" * 70)
print("""
If get_quotes returns error "Stock may not be available for trading":
  → This is API limitation, not a code issue
  → Breeze doesn't support NSE spot quotes for all accounts
  
If get_quotes returns success with 'ltp' field:
  → Extract: response['Success'][0]['ltp']
  
If get_historical_data returns candle data:
  → Extract: response['Success'] as list of OHLCV
  
If either returns empty or None:
  → Session might not be properly initialized
  → Check credentials in .env file
""")
