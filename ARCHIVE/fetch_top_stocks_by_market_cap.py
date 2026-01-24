#!/usr/bin/env python3
"""
Identify top 200 Indian stocks by market cap > 200B from Yahoo Finance.
Use as reference to build a clean, data-verified universe.
"""

import yfinance as yf
import pandas as pd
import json
from datetime import datetime
import time

print("Fetching top Indian stocks by market cap from Yahoo Finance...")
print("=" * 80)

# Known large-cap Indian stocks on Yahoo (with valid ticker formats)
# These are NSE-listed companies that Yahoo tracks
KNOWN_LARGE_CAPS = [
    # Banking & Finance
    'HDFCBANK.NS', 'ICICIBANK.NS', 'AXISBANK.NS', 'KOTAKBANK.NS', 'INDUSIND.NS',
    'BANKBARODA.NS', 'SBIN.NS', 'CANBK.NS', 'FEDERALBNK.NS', 'PNB.NS', 'IDFCFIRSTB.NS',
    
    # IT & Software
    'TCS.NS', 'INFY.NS', 'WIPRO.NS', 'TECHM.NS', 'LTIM.NS', 'HCLTECH.NS',
    
    # Pharma
    'SUNPHARMA.NS', 'DRREDDY.NS', 'CIPLA.NS', 'LUPIN.NS', 'DIVISLAB.NS', 'AUROPHARMA.NS', 'BIOCON.NS',
    
    # Automobiles
    'MARUTI.NS', 'M&M.NS', 'TATAMOTORS.NS', 'HEROMOTOCO.NS', 'ASHOKLEY.NS', 'BAJAJFINSV.NS',
    
    # Energy & Utilities
    'RELIANCE.NS', 'NTPC.NS', 'POWERGRID.NS', 'ONGC.NS', 'BPCL.NS', 'GAIL.NS', 'IOC.NS',
    
    # Metals
    'HINDALCO.NS', 'TATASTEEL.NS', 'JSWSTEEL.NS', 'VEDL.NS', 'NALCO.NS', 'JINDALSTEEL.NS',
    
    # Cement
    'ULTRACEM.NS', 'AMBUJACEM.NS', 'DALBHUMI.NS',
    
    # Consumer
    'ITC.NS', 'BRITANNIA.NS', 'NESTLEIND.NS', 'COLPAL.NS', 'DABUR.NS', 'MARICO.NS',
    'UNILEVER.NS', 'GODREJCP.NS', 'BAJFINANCE.NS',
    
    # Infrastructure & Construction
    'LT.NS', 'LODHA.NS', 'DLF.NS',
    
    # Telecommunications
    'BHARTIARTL.NS', 'JIOTOWER.NS', 'INDIGO.NS',
    
    # Real Estate & Tourism
    'INDHOTEL.NS',
    
    # Chemicals
    'PIDILITIND.NS', 'SRF.NS',
    
    # Conglomerates
    'ADANIENT.NS', 'ADANIPORTS.NS', 'ADANIGREEN.NS', 'ADANIPOWER.NS', 'ADANIENSOL.NS',
    
    # Insurance
    'LICI.NS', 'HDFCLIFE.NS', 'SBILIFE.NS', 'ICICIGI.NS', 'BAJAJFINSV.NS',
    
    # Others (Large cap)
    'JSWENERGY.NS', 'COALINDIA.NS', 'GRAPHITE.NS', 'APOLLOHOSP.NS', 'FORTIS.NS',
    'MAXHEALTH.NS', 'LAURUSLABS.NS', 'MRPL.NS', 'MOTHERSON.NS', 'RECLTD.NS',
    'IRFC.NS', 'NTPC.NS', 'BEL.NS', 'KPITTECH.NS', 'GRASIM.NS', 'VOLTAS.NS', 'TRENT.NS',
]

print(f"Testing {len(KNOWN_LARGE_CAPS)} known large-cap stocks...")
print()

valid_stocks = []
failed_stocks = []

for i, ticker in enumerate(KNOWN_LARGE_CAPS, 1):
    try:
        print(f"[{i:3d}/{len(KNOWN_LARGE_CAPS)}] {ticker:20s} ", end='', flush=True)
        
        stock = yf.Ticker(ticker)
        
        # Get market cap
        info = stock.info
        market_cap = info.get('marketCap')
        price = info.get('currentPrice')
        name = info.get('longName', ticker.replace('.NS', ''))
        
        # Market cap in billions
        market_cap_b = (market_cap / 1_000_000_000) if market_cap else 0
        
        if market_cap and market_cap_b >= 200:
            valid_stocks.append({
                'ticker': ticker,
                'symbol': ticker.replace('.NS', ''),
                'name': name,
                'market_cap_b': round(market_cap_b, 2),
                'price': price,
                'status': 'VALID'
            })
            print(f"✓ {market_cap_b:8.1f}B - {name[:30]}")
        elif market_cap:
            print(f"✗ {market_cap_b:8.1f}B - Below 200B threshold")
            failed_stocks.append({
                'ticker': ticker,
                'reason': f'Market cap {market_cap_b:.1f}B < 200B',
                'market_cap_b': market_cap_b
            })
        else:
            print(f"✗ No market cap data")
            failed_stocks.append({
                'ticker': ticker,
                'reason': 'No market cap data',
                'market_cap_b': 0
            })
        
        time.sleep(0.1)  # Rate limit
        
    except Exception as e:
        print(f"✗ Error: {str(e)[:40]}")
        failed_stocks.append({
            'ticker': ticker,
            'reason': str(e)[:50],
            'market_cap_b': 0
        })

print("\n" + "=" * 80)
print("RESULTS:")
print("-" * 80)

# Sort by market cap descending
valid_stocks_sorted = sorted(valid_stocks, key=lambda x: x['market_cap_b'], reverse=True)

print(f"\nStocks with Market Cap > 200B: {len(valid_stocks_sorted)}")
print()

for i, stock in enumerate(valid_stocks_sorted[:50], 1):  # Show top 50
    print(f"{i:3d}. {stock['symbol']:15s} {stock['market_cap_b']:8.1f}B  {stock['name'][:40]}")

if len(valid_stocks_sorted) > 50:
    print(f"\n... and {len(valid_stocks_sorted) - 50} more stocks")

print("\n" + "-" * 80)
print(f"Total valid (>200B): {len(valid_stocks_sorted)}")
print(f"Failed/Below threshold: {len(failed_stocks)}")

# If we have less than 200, extend the search
if len(valid_stocks_sorted) < 200:
    print(f"\nNote: Only found {len(valid_stocks_sorted)} stocks > 200B. Consider lowering threshold to 100B.")

# Save results
results = {
    'timestamp': datetime.now().isoformat(),
    'valid_stocks': valid_stocks_sorted,
    'failed_stocks': failed_stocks,
    'summary': {
        'total_tested': len(KNOWN_LARGE_CAPS),
        'valid_count': len(valid_stocks_sorted),
        'failed_count': len(failed_stocks),
        'minimum_market_cap_b': 200
    }
}

with open('top_stocks_by_market_cap.json', 'w') as f:
    json.dump(results, f, indent=2)

# Also save as a simple symbol list for nifty200_constituents.txt
symbols_list = [stock['symbol'] for stock in valid_stocks_sorted]
with open('top_stocks_symbols.txt', 'w') as f:
    f.write('\n'.join(symbols_list))

print(f"\nResults saved to:")
print(f"  - top_stocks_by_market_cap.json (detailed)")
print(f"  - top_stocks_symbols.txt (symbols only)")

print("\n" + "=" * 80)
print("To use as new constituent list:")
print(f"  cp top_stocks_symbols.txt data/constituents/nifty200_constituents.txt")
print("=" * 80)
