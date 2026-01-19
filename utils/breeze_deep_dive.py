#!/usr/bin/env python3
"""Deep dive into BreezeConnect API."""

from breeze_connect import BreezeConnect
import os
from dotenv import load_dotenv
import json
import sys

# Fix encoding for Windows
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

load_dotenv()

api_key = os.getenv('BREEZE_API_KEY')
api_secret = os.getenv('BREEZE_API_SECRET')
session_token = os.getenv('BREEZE_SESSION_TOKEN')

print("=" * 80)
print("BREEZE CONNECT DEEP DIVE")
print("=" * 80)

try:
    print("\n1. Initializing BreezeConnect...")
    bc = BreezeConnect(api_key=api_key)
    print("   [OK] Instance created")
    
    print("\n2. Generating session...")
    bc.generate_session(api_secret=api_secret, session_token=session_token)
    print("   [OK] Session established")
    
    print("\n3. Getting customer details...")
    try:
        cust = bc.get_customer_details()
        print(f"   Response: {cust}")
        if isinstance(cust, dict):
            for k, v in cust.items():
                if k != 'Success':
                    print(f"     {k}: {v}")
                elif isinstance(v, list) and len(v) > 0:
                    print(f"     Customer: {v[0]}")
    except Exception as e:
        print(f"   Error: {e}")
    
    print("\n4. Getting stock script list (first 20)...")
    try:
        scripts = bc.get_stock_script_list()
        if isinstance(scripts, dict):
            success = scripts.get('Success', [])
            if isinstance(success, list) and len(success) > 0:
                print(f"   Total scripts: {len(success)}")
                print("   First 20:")
                for i, script in enumerate(success[:20]):
                    print(f"     {i+1}. {script.get('Stock_name', 'N/A')} - {script.get('Stock_code', 'N/A')} ({script.get('Exch_seg', 'N/A')})")
            else:
                print(f"   Scripts response: {scripts}")
        else:
            print(f"   Response: {scripts}")
    except Exception as e:
        print(f"   Error: {e}")
    
    print("\n5. Testing get_quotes with different product types...")
    test_configs = [
        ('SBIN', 'NSE', 'cash'),
        ('SBIN', 'NSE', 'mtf'),
        ('SBIN', 'BSE', 'cash'),
        ('ICICIBANK', 'NSE', 'cash'),
        ('ICICIBANK', 'NSE', 'mtf'),
        ('HDFCBANK', 'NSE', 'cash'),
    ]
    
    for stock_code, exchange, product in test_configs:
        try:
            res = bc.get_quotes(
                stock_code=stock_code,
                exchange_code=exchange,
                product_type=product
            )
            
            if res and res.get('Status') == 200 and res.get('Success'):
                ltp = res['Success'][0].get('ltp', 'N/A')
                print(f"   [OK] {stock_code:12} {exchange:5} {product:8} = {ltp}")
            else:
                error = res.get('Error', 'Unknown') if res else 'No response'
                print(f"   [ER] {stock_code:12} {exchange:5} {product:8} = {error[:40]}")
        except Exception as e:
            print(f"   [ER] {stock_code:12} {exchange:5} {product:8} = {str(e)[:40]}")
    
    print("\n6. Testing get_stock_token_value...")
    try:
        token_res = bc.get_stock_token_value(
            exchange_code='NSE',
            stock_code='SBIN',
            product_type='cash'
        )
        print(f"   Response: {json.dumps(token_res, indent=2, default=str)[:500]}")
    except Exception as e:
        print(f"   Error: {e}")
    
    print("\n7. Testing with explicit stock token...")
    try:
        # First get the token
        token_res = bc.get_stock_token_value(
            exchange_code='NSE',
            stock_code='SBIN',
            product_type='cash'
        )
        
        if token_res and token_res.get('Success'):
            token = token_res['Success'][0].get('stat_fetch_token')
            print(f"   Got token: {token}")
            
            # Now try to get quotes using token
            quotes = bc.get_quotes(
                stock_code='SBIN',
                exchange_code='NSE',
                product_type='cash'
            )
            print(f"   Quotes: {quotes.get('Success', [{}])[0] if quotes.get('Success') else 'No data'}")
    except Exception as e:
        print(f"   Error: {e}")
    
    print("\n8. Testing get_historical_data...")
    from datetime import datetime, timedelta
    end_date = datetime.now()
    start_date = end_date - timedelta(days=5)
    
    try:
        hist = bc.get_historical_data(
            stock_code='SBIN',
            exchange_code='NSE',
            product_type='cash',
            from_date=start_date.strftime('%Y-%m-%d'),
            to_date=end_date.strftime('%Y-%m-%d'),
            interval='1day'
        )
        
        if hist and hist.get('Status') == 200:
            data = hist.get('Success', [])
            print(f"   [OK] Got {len(data)} candles")
            if len(data) > 0:
                first = data[0]
                print(f"   First: {first}")
        else:
            print(f"   Error: {hist.get('Error') if hist else 'No response'}")
    except Exception as e:
        print(f"   Error: {e}")

except Exception as e:
    print(f"\n[ERROR] {type(e).__name__}: {e}")
    import traceback
    traceback.print_exc()
