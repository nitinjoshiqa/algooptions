#!/usr/bin/env python3
"""
Build comprehensive NIFTY500 universe with 220+ stocks by market cap.
Ensures all common large-cap stocks are included (TATASTEEL, etc.)
Validates each stock has real-time data on Yahoo Finance.
"""

import yfinance as yf
import json
from datetime import datetime
import time

print("Building NIFTY500 universe with 220+ stocks by market cap...")
print("=" * 80)

# Comprehensive list of ALL major Indian stocks across all sectors
# Includes commonly traded stocks that may have been missed
ALL_INDIAN_STOCKS = [
    # Banking & Finance (30+)
    'HDFCBANK.NS', 'ICICIBANK.NS', 'AXISBANK.NS', 'KOTAKBANK.NS', 'SBIN.NS',
    'BANKBARODA.NS', 'CANBK.NS', 'FEDERALBNK.NS', 'PNB.NS', 'IDFCFIRSTB.NS', 'AUBANK.NS',
    'INDUSIND.NS', 'UCOBANK.NS', 'UNIONBANK.NS', 'IDBI.NS', 'BANKNIFTY.NS',
    'BAJFINANCE.NS', 'BAJAJFINSV.NS', 'HDFC.NS', 'ICICIPRULI.NS', 'SBICARD.NS',
    'HDFCLIFE.NS', 'SBILIFE.NS', 'ICICIGI.NS', 'LICI.NS', 'ABCAPITAL.NS',
    
    # IT & Software (15+)
    'TCS.NS', 'INFY.NS', 'WIPRO.NS', 'HCLTECH.NS', 'LTIM.NS', 'TECHM.NS',
    'KPITTECH.NS', 'COFORGE.NS', 'PERSISTENT.NS', 'MPHASIS.NS', 'MINDTREE.NS',
    'CYIENT.NS', 'HEXAWARE.NS',
    
    # Pharma & Healthcare (20+)
    'SUNPHARMA.NS', 'DRREDDY.NS', 'CIPLA.NS', 'LUPIN.NS', 'DIVISLAB.NS', 'AUROPHARMA.NS',
    'BIOCON.NS', 'APOLLOHOSP.NS', 'FORTIS.NS', 'MAXHEALTH.NS', 'LAURUSLABS.NS',
    'GLENMARK.NS', 'ALKEM.NS', 'TORRENTPHARM.NS', 'SANOFI.NS', 'PFIZER.NS',
    
    # Automobiles & 2-wheelers (15+)
    'MARUTI.NS', 'M&M.NS', 'HEROMOTOCO.NS', 'ASHOKLEY.NS', 'TVSMOTOR.NS',
    'BAJAJ-AUTO.NS', 'CUMMINSIND.NS', 'APOLLOTYRE.NS', 'BOSCHLTD.NS', 'ESCORTS.NS',
    'FORCEMOT.NS', 'EXIDEIND.NS', 'SENSORSDRIVE.NS',
    
    # Energy & Utilities (15+)
    'RELIANCE.NS', 'NTPC.NS', 'POWERGRID.NS', 'ONGC.NS', 'BPCL.NS', 'GAIL.NS', 'IOC.NS',
    'JSWENERGY.NS', 'ADANIPOWER.NS', 'ADANIENSOL.NS', 'TATAPOWER.NS',
    
    # Metals & Mining (10+)
    'HINDALCO.NS', 'TATASTEEL.NS', 'JSWSTEEL.NS', 'VEDL.NS', 'NMDC.NS', 'COALINDIA.NS',
    'JINDALSTEL.NS', 'RATNAMANI.NS',
    
    # Cement (5+)
    'AMBUJACEM.NS', 'SHREECEM.NS', 'ULTRACEM.NS', 'DALBHUMI.NS',
    
    # Consumer & FMCG (15+)
    'ITC.NS', 'BRITANNIA.NS', 'NESTLEIND.NS', 'COLPAL.NS', 'DABUR.NS', 'MARICO.NS',
    'GODREJCP.NS', 'UNILEVER.NS', 'HATSUN.NS', 'JYOTHYLAB.NS',
    
    # Infrastructure & Real Estate (10+)
    'LT.NS', 'LODHA.NS', 'DLF.NS', 'GENSOL.NS', 'MERCK.NS',
    
    # Telecom & Aviation (8+)
    'BHARTIARTL.NS', 'INDIGO.NS', 'SPICEJET.NS', 'AIRWORKS.NS',
    
    # Tourism & Hospitality (3+)
    'INDHOTEL.NS',
    
    # Chemicals & Fertilizers (10+)
    'PIDILITIND.NS', 'SRF.NS', 'DEEPAKFERT.NS', 'GUJALKALI.NS', 'UPL.NS',
    'INSECTICIDES.NS', 'HERITAGEFD.NS',
    
    # Conglomerates & Infrastructure (10+)
    'ADANIENT.NS', 'ADANIPORTS.NS', 'ADANIGREEN.NS', 'ADANIPOWER.NS',
    
    # Textiles & Apparel (5+)
    'MOTHERSON.NS', 'FINOLEX.NS', 'ARVINDFARM.NS',
    
    # Electronics & Defence (5+)
    'BEL.NS', 'HAVELLS.NS', 'BLUESTARCO.NS',
    
    # Logistics & Transportation (5+)
    'RECLTD.NS', 'IRFC.NS', 'DELHIVERY.NS', 'TIINDIA.NS',
    
    # Miscellaneous Large Caps (20+)
    'GRASIM.NS', 'VOLTAS.NS', 'TRENT.NS', 'KPITTECH.NS', 'MANAPPURAM.NS',
    'GRAPHITE.NS', 'HYUNDAI.NS', 'MRPL.NS', 'KIOCL.NS', 'INOXWIND.NS',
    'HAL.NS', 'SAIL.NS', 'HINDPETRO.NS', 'CGPOWER.NS', 'BHEL.NS',
    'BDL.NS', 'GLENMARK.NS', 'BIOCON.NS', 'JINDALSTEL.NS', 'NITINSOFTW.NS',
    'RATNAMANI.NS', 'MOIL.NS', 'RPOWER.NS', 'CNXIT.NS', 'GLOSTERIND.NS',
]

print(f"Testing {len(ALL_INDIAN_STOCKS)} stocks for market cap >= 50B...")
print()

valid_stocks = []
tested = 0

for i, ticker in enumerate(ALL_INDIAN_STOCKS, 1):
    try:
        tested += 1
        symbol = ticker.replace('.NS', '')
        print(f"[{i:3d}/{len(ALL_INDIAN_STOCKS)}] {symbol:15s} ", end='', flush=True)
        
        stock = yf.Ticker(ticker)
        info = stock.info
        market_cap = info.get('marketCap')
        price = info.get('currentPrice')
        name = info.get('longName', symbol)
        
        market_cap_b = (market_cap / 1_000_000_000) if market_cap else 0
        
        if market_cap and market_cap_b >= 50:  # >= 50B threshold
            valid_stocks.append({
                'ticker': ticker,
                'symbol': symbol,
                'name': name[:50],
                'market_cap_b': round(market_cap_b, 2),
                'price': round(price, 2) if price else 0,
            })
            print(f"✓ {market_cap_b:8.1f}B")
        elif market_cap:
            print(f"✗ {market_cap_b:8.1f}B (< 50B)")
        else:
            print(f"✗ No data")
        
        time.sleep(0.03)
        
    except Exception as e:
        print(f"✗ Error")

print("\n" + "=" * 80)
print("RESULTS:")
print("-" * 80)

# Sort by market cap descending
valid_stocks_sorted = sorted(valid_stocks, key=lambda x: x['market_cap_b'], reverse=True)

print(f"\nTotal stocks with Market Cap >= 50B: {len(valid_stocks_sorted)}")
print()

# Display all stocks
for i, stock in enumerate(valid_stocks_sorted, 1):
    print(f"{i:3d}. {stock['symbol']:15s} {stock['market_cap_b']:8.1f}B  {stock['name'][:40]}")

# Save to files
with open('nifty500_constituents_220plus.txt', 'w') as f:
    for stock in valid_stocks_sorted:
        f.write(stock['symbol'] + '\n')

# Also save detailed JSON
results = {
    'timestamp': datetime.now().isoformat(),
    'valid_stocks': valid_stocks_sorted,
    'summary': {
        'total_tested': len(ALL_INDIAN_STOCKS),
        'valid_count': len(valid_stocks_sorted),
        'minimum_market_cap_b': 50
    }
}

with open('nifty500_market_cap_analysis.json', 'w') as f:
    json.dump(results, f, indent=2)

print("\n" + "=" * 80)
print(f"SAVED {len(valid_stocks_sorted)} stocks to:")
print(f"  - nifty500_constituents_220plus.txt")
print(f"  - nifty500_market_cap_analysis.json")
print()
print("SUMMARY:")
print(f"  Total stocks found: {len(valid_stocks_sorted)}")
print(f"  Target: 220+")
if len(valid_stocks_sorted) >= 220:
    print(f"  Status: ✓ ACHIEVED")
else:
    print(f"  Status: NEED {220 - len(valid_stocks_sorted)} more (expand threshold)")
print("=" * 80)
