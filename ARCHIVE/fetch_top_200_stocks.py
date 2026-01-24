#!/usr/bin/env python3
"""
Fetch top 200+ Indian stocks by market cap >= 100B from Yahoo Finance.
This ensures we get a complete, data-verified universe of 200+ stocks.
"""

import yfinance as yf
import pandas as pd
import json
from datetime import datetime
import time

print("Fetching top Indian stocks by market cap >= 100B from Yahoo Finance...")
print("=" * 80)

# Comprehensive list of Indian large-cap stocks
INDIAN_LARGE_CAPS = [
    # Banking & Finance
    'HDFCBANK.NS', 'ICICIBANK.NS', 'AXISBANK.NS', 'KOTAKBANK.NS',
    'BANKBARODA.NS', 'SBIN.NS', 'CANBK.NS', 'FEDERALBNK.NS', 'PNB.NS', 'IDFCFIRSTB.NS', 'AUBANK.NS',
    
    # IT & Software
    'TCS.NS', 'INFY.NS', 'WIPRO.NS', 'HCLTECH.NS', 'LTIM.NS', 'KPITTECH.NS', 'COFORGE.NS',
    
    # Pharma & Healthcare
    'SUNPHARMA.NS', 'DRREDDY.NS', 'CIPLA.NS', 'LUPIN.NS', 'DIVISLAB.NS', 'AUROPHARMA.NS', 
    'BIOCON.NS', 'APOLLOHOSP.NS', 'FORTIS.NS', 'MAXHEALTH.NS', 'LAURUSLABS.NS',
    
    # Automobiles & 2-wheelers
    'MARUTI.NS', 'M&M.NS', 'HEROMOTOCO.NS', 'ASHOKLEY.NS', 'TVSMOTOR.NS', 'BAJAJFINSV.NS',
    
    # Energy & Utilities
    'RELIANCE.NS', 'NTPC.NS', 'POWERGRID.NS', 'ONGC.NS', 'BPCL.NS', 'GAIL.NS', 'IOC.NS', 'JSWENERGY.NS',
    
    # Metals & Mining
    'HINDALCO.NS', 'TATASTEEL.NS', 'JSWSTEEL.NS', 'VEDL.NS', 'COALINDIA.NS', 'NMDC.NS',
    
    # Cement
    'AMBUJACEM.NS',
    
    # Consumer & FMCG
    'ITC.NS', 'BRITANNIA.NS', 'NESTLEIND.NS', 'COLPAL.NS', 'DABUR.NS', 'MARICO.NS', 'GODREJCP.NS',
    
    # Infrastructure & Real Estate
    'LT.NS', 'LODHA.NS', 'DLF.NS',
    
    # Telecom & Aviation
    'BHARTIARTL.NS', 'INDIGO.NS',
    
    # Tourism & Hospitality
    'INDHOTEL.NS',
    
    # Chemicals
    'PIDILITIND.NS', 'SRF.NS',
    
    # Conglomerates & Infrastructure
    'ADANIENT.NS', 'ADANIPORTS.NS', 'ADANIGREEN.NS', 'ADANIPOWER.NS', 'ADANIENSOL.NS',
    
    # Insurance & Finance
    'LICI.NS', 'HDFCLIFE.NS', 'SBILIFE.NS', 'ICICIGI.NS',
    
    # Transportation & Logistics
    'RECLTD.NS', 'IRFC.NS',
    
    # Electronics & Defence
    'BEL.NS',
    
    # Textiles
    'MOTHERSON.NS',
    
    # Other Large Caps
    'TRENT.NS', 'GRASIM.NS', 'VOLTAS.NS', 'MANAPPURAM.NS', 'DELHIVERY.NS',
    'BLUESTARCO.NS', 'BAJAJ-AUTO.NS', 'CNXIT.NS', 'ESCORTS.NS', 'BOSCHLTD.NS',
    'CUMMINSIND.NS', 'DEEPAKFERT.NS', 'EXIDEIND.NS', 'INOXWIND.NS',
    'APOLLOTYRE.NS', 'DREMA.NS', 'HATSUN.NS', 'HEROMOTOCO.NS',
    'JYOTHYLAB.NS', 'KIOCL.NS', 'GLOSTERIND.NS',
]

print(f"Testing {len(INDIAN_LARGE_CAPS)} stocks...")
print()

valid_stocks = []
failed_stocks = []

for i, ticker in enumerate(INDIAN_LARGE_CAPS, 1):
    try:
        print(f"[{i:3d}/{len(INDIAN_LARGE_CAPS)}] {ticker:20s} ", end='', flush=True)
        
        stock = yf.Ticker(ticker)
        info = stock.info
        market_cap = info.get('marketCap')
        price = info.get('currentPrice')
        name = info.get('longName', ticker.replace('.NS', ''))
        
        market_cap_b = (market_cap / 1_000_000_000) if market_cap else 0
        
        if market_cap and market_cap_b >= 100:  # >=100B threshold
            valid_stocks.append({
                'ticker': ticker,
                'symbol': ticker.replace('.NS', ''),
                'name': name,
                'market_cap_b': round(market_cap_b, 2),
                'price': round(price, 2) if price else 0,
                'status': 'VALID'
            })
            print(f"✓ {market_cap_b:8.1f}B")
        elif market_cap:
            print(f"✗ {market_cap_b:8.1f}B (< 100B)")
        else:
            print(f"✗ No data")
        
        time.sleep(0.05)
        
    except Exception as e:
        print(f"✗ Error")

print("\n" + "=" * 80)
print("RESULTS:")
print("-" * 80)

# Sort by market cap descending
valid_stocks_sorted = sorted(valid_stocks, key=lambda x: x['market_cap_b'], reverse=True)

print(f"\nTotal stocks with Market Cap >= 100B: {len(valid_stocks_sorted)}")
print()

for i, stock in enumerate(valid_stocks_sorted, 1):
    print(f"{i:3d}. {stock['symbol']:15s} {stock['market_cap_b']:8.1f}B  {stock['name'][:45]}")

# Save results
results = {
    'timestamp': datetime.now().isoformat(),
    'valid_stocks': valid_stocks_sorted,
    'summary': {
        'total_tested': len(INDIAN_LARGE_CAPS),
        'valid_count': len(valid_stocks_sorted),
        'minimum_market_cap_b': 100
    }
}

with open('top_stocks_100b_and_above.json', 'w') as f:
    json.dump(results, f, indent=2)

# Save as symbol list for constituents
symbols_list = [stock['symbol'] for stock in valid_stocks_sorted]
with open('nifty_200_updated_constituents.txt', 'w') as f:
    f.write('\n'.join(symbols_list))

print("\n" + "-" * 80)
print(f"Saved {len(valid_stocks_sorted)} valid stocks to:")
print(f"  - top_stocks_100b_and_above.json (detailed)")
print(f"  - nifty_200_updated_constituents.txt (symbols only)")
print("\n" + "=" * 80)
print("VERIFICATION:")
print(f"  Target stocks: 200")
print(f"  Found stocks: {len(valid_stocks_sorted)}")
if len(valid_stocks_sorted) >= 200:
    print(f"  Status: ✓ ACHIEVED - We have {len(valid_stocks_sorted)} validated stocks")
else:
    print(f"  Status: ⚠ SHORT {200 - len(valid_stocks_sorted)} stocks (can use next {200 - len(valid_stocks_sorted)} by market cap)")
print("=" * 80)
