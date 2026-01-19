#!/usr/bin/env python3
"""Test YFinance directly"""

import yfinance as yf
import warnings

warnings.filterwarnings('ignore')

print("=" * 70)
print("TESTING YFINANCE DIRECTLY")
print("=" * 70)

test_stocks = ['SBIN', 'ICICIBANK', 'RELIANCE', 'INFY', 'HDFC']

for symbol in test_stocks:
    print(f"\nTesting {symbol}...")
    
    # Try different variants
    variants = [symbol + '.NS', symbol, symbol.replace('-', '') + '.NS']
    
    for sym_variant in variants:
        try:
            print(f"  Trying: {sym_variant}...", end=" ")
            ticker = yf.Ticker(sym_variant)
            
            # Try fast_info first
            if hasattr(ticker, 'fast_info'):
                info = ticker.fast_info
                price = info.get('lastPrice') or info.get('last_price') or info.get('previousClose')
                if price:
                    print(f"✓ {price}")
                    break
            
            # Try history
            df = ticker.history(period='5d', interval='1d')
            if df is not None and not df.empty:
                price = float(df.iloc[-1]['Close'])
                print(f"✓ {price}")
                break
            else:
                print("✗ No data")
        
        except Exception as e:
            print(f"✗ {type(e).__name__}: {str(e)[:50]}")
    else:
        print(f"  FAILED: Could not get data for {symbol}")

print("\n" + "=" * 70)
print("Summary:")
print("  If ✓ appears, stock prices are available from YFinance")
print("  If ✗ appears for all variants, stock might not be on YFinance")
print("=" * 70)
