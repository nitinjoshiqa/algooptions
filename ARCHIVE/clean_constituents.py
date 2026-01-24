#!/usr/bin/env python3
"""
Clean and validate the NIFTY500 constituents file
Remove duplicates and invalid symbols
Keep only verified stocks from comprehensive test
"""

import yfinance as yf
import time

# Read current file
with open('nifty500_constituents_final_220.txt', 'r') as f:
    all_stocks = [line.strip() for line in f if line.strip()]

print(f"Total entries in file: {len(all_stocks)}")
print(f"Unique entries: {len(set(all_stocks))}")
print()

# Get unique stocks
unique_stocks = list(set(all_stocks))
print(f"Validating {len(unique_stocks)} unique stocks against Yahoo Finance...")
print()

validated = []
invalid = []

for i, symbol in enumerate(unique_stocks, 1):
    try:
        print(f"[{i:3d}/{len(unique_stocks)}] {symbol:15s} ", end='', flush=True)
        
        ticker = yf.Ticker(f"{symbol}.NS")
        info = ticker.info
        market_cap = info.get('marketCap')
        
        if market_cap:
            market_cap_b = market_cap / 1_000_000_000
            if market_cap_b >= 10:  # Must be >= 10B
                validated.append((symbol, market_cap_b))
                print(f"[OK] {market_cap_b:.1f}B")
            else:
                print(f"[LOW] {market_cap_b:.1f}B")
                invalid.append(symbol)
        else:
            print(f"[FAIL] No data")
            invalid.append(symbol)
        
        time.sleep(0.02)
        
    except Exception as e:
        print(f"[ERR] Invalid symbol")
        invalid.append(symbol)

print()
print("=" * 80)
print("VALIDATION RESULTS")
print("=" * 80)
print(f"Valid stocks (>=10B):  {len(validated)}")
print(f"Invalid stocks:        {len(invalid)}")
print()

if invalid:
    print("Removed invalid stocks:")
    for s in invalid[:20]:
        print(f"  - {s}")
    if len(invalid) > 20:
        print(f"  ... and {len(invalid) - 20} more")
    print()

# Sort by market cap
validated_sorted = sorted(validated, key=lambda x: x[1], reverse=True)

print(f"Top 10 by Market Cap:")
for symbol, mcap in validated_sorted[:10]:
    print(f"  {symbol:15s} {mcap:8.1f}B")

print()
print("=" * 80)

# Save cleaned file
with open('nifty500_constituents_final_220.txt', 'w') as f:
    for symbol, _ in validated_sorted:
        f.write(symbol + '\n')

print(f"CLEANED FILE SAVED: nifty500_constituents_final_220.txt")
print(f"Final count: {len(validated_sorted)} unique, validated stocks")
print("=" * 80)
