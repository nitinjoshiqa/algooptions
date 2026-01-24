#!/usr/bin/env python3
"""
Test broader market cap threshold: 15B instead of 20B
See how many additional stocks we can get
"""

import yfinance as yf
import json
from datetime import datetime
import time
import sys
import io

# Fix Unicode output on Windows
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

print("Testing broader threshold: Market Cap >= 15B")
print("=" * 80)

# Comprehensive list of major Indian stocks (same as before)
TEST_STOCKS = [
    'RELIANCE.NS', 'HDFCBANK.NS', 'BHARTIARTL.NS', 'TCS.NS', 'ICICIBANK.NS',
    'SBIN.NS', 'INFY.NS', 'BAJFINANCE.NS', 'LT.NS', 'LICI.NS',
    'MARUTI.NS', 'HCLTECH.NS', 'M&M.NS', 'KOTAKBANK.NS', 'ITC.NS',
    'SUNPHARMA.NS', 'AXISBANK.NS', 'NTPC.NS', 'BAJAJFINSV.NS', 'ONGC.NS',
    'ADANIPORTS.NS', 'BEL.NS', 'HAL.NS', 'JSWSTEEL.NS', 'VEDL.NS',
    'BAJAJ-AUTO.NS', 'COALINDIA.NS', 'ADANIPOWER.NS', 'NESTLEIND.NS', 'WIPRO.NS',
    'ADANIENT.NS', 'POWERGRID.NS', 'TATASTEEL.NS', 'IOC.NS', 'HINDALCO.NS',
    'SBILIFE.NS', 'GRASIM.NS', 'HYUNDAI.NS', 'INDIGO.NS', 'LTIM.NS',
    'TVSMOTOR.NS', 'DIVISLAB.NS', 'HDFCLIFE.NS', 'BANKBARODA.NS', 'BPCL.NS',
    'TECHM.NS', 'IRFC.NS', 'PIDILITIND.NS', 'DLF.NS', 'BRITANNIA.NS',
    'PNB.NS', 'CANBK.NS', 'TRENT.NS', 'UNIONBANK.NS', 'AMBUJACEM.NS',
    'ADANIGREEN.NS', 'GODREJCP.NS', 'MOTHERSON.NS', 'ASHOKLEY.NS', 'TATAPOWER.NS',
    'CUMMINSIND.NS', 'JINDALSTEL.NS', 'HEROMOTOCO.NS', 'CIPLA.NS', 'GAIL.NS',
    'IDBI.NS', 'BOSCHLTD.NS', 'DRREDDY.NS', 'APOLLOHOSP.NS', 'LUPIN.NS',
    'SHREECEM.NS', 'ADANIENSOL.NS', 'MAXHEALTH.NS', 'PERSISTENT.NS', 'MARICO.NS',
    'RECLTD.NS', 'ICICIPRULI.NS', 'DABUR.NS', 'INDHOTEL.NS', 'ABCAPITAL.NS',
    'LODHA.NS', 'ICICIGI.NS', 'HINDPETRO.NS', 'CGPOWER.NS', 'BHEL.NS',
    'JSWENERGY.NS', 'HAVELLS.NS', 'SRF.NS', 'SBICARD.NS', 'AUBANK.NS',
    'IDFCFIRSTB.NS', 'ALKEM.NS', 'FEDERALBNK.NS', 'NMDC.NS', 'AUROPHARMA.NS',
    'FORTIS.NS', 'SAIL.NS', 'BIOCON.NS', 'UPL.NS', 'COLPAL.NS',
    'GLENMARK.NS', 'COFORGE.NS', 'LAURUSLABS.NS', 'MPHASIS.NS', 'BDL.NS',
    'MAHABANK.NS', 'TATACOMM.NS', 'VOLTAS.NS', 'TIINDIA.NS', 'ESCORTS.NS',
    'KALYANKJIL.NS', 'ASTRAL.NS', 'UCOBANK.NS', 'BLUESTARCO.NS', 'TATAELXSI.NS',
    'APOLLOTYRE.NS', 'KPITTECH.NS', 'DELHIVERY.NS', 'ASTERDM.NS', 'GUJGASLTD.NS',
    'EXIDEIND.NS', 'MRPL.NS', 'TATATECH.NS', 'FORCEMOT.NS', 'MANAPPURAM.NS',
    'AEGISLOG.NS', 'SYNGENE.NS', 'PFIZER.NS', 'KIOCL.NS', 'HATSUN.NS',
    'TATACHEM.NS', 'INOXWIND.NS', 'APLLTD.NS', 'DEEPAKFERT.NS', 'RATNAMANI.NS',
    'CYIENT.NS', 'GRAPHITE.NS', 'RPOWER.NS', 'PCBL.NS', 'WHIRLPOOL.NS',
    'TDPOWERSYS.NS', 'SANOFI.NS', 'JYOTHYLAB.NS', 'MOIL.NS',
]

print(f"Testing {len(TEST_STOCKS)} stocks for Market Cap >= 15B...")
print()

cap_15b = []
cap_20b = []
failed = 0

for i, ticker in enumerate(TEST_STOCKS, 1):
    try:
        symbol = ticker.replace('.NS', '')
        print(f"[{i:3d}/{len(TEST_STOCKS)}] {symbol:15s} ", end='', flush=True)
        
        stock = yf.Ticker(ticker)
        info = stock.info
        market_cap = info.get('marketCap')
        price = info.get('currentPrice')
        name = info.get('longName', symbol)
        
        market_cap_b = (market_cap / 1_000_000_000) if market_cap else 0
        
        if market_cap:
            if market_cap_b >= 15:
                cap_15b.append((symbol, market_cap_b))
                if market_cap_b >= 20:
                    cap_20b.append((symbol, market_cap_b))
                print(f"[OK] {market_cap_b:8.1f}B")
            else:
                print(f"[LOW] {market_cap_b:8.1f}B")
        else:
            print(f"[FAIL]")
            failed += 1
        
        time.sleep(0.02)
        
    except Exception as e:
        print(f"[ERR] {str(e)[:15]}")
        failed += 1

print("\n" + "=" * 80)
print("RESULTS:")
print("-" * 80)
print()
print(f"Stocks with Market Cap >= 20B: {len(cap_20b)}")
print(f"Stocks with Market Cap >= 15B: {len(cap_15b)}")
print(f"Additional by lowering to 15B: {len(cap_15b) - len(cap_20b)}")
print(f"Failed/No data: {failed}")
print()

# Show stocks in 15B-20B range
in_15_20_range = [(s, m) for s, m in cap_15b if m < 20]
if in_15_20_range:
    print(f"Stocks in 15B-20B range ({len(in_15_20_range)}):")
    in_15_20_range_sorted = sorted(in_15_20_range, key=lambda x: x[1], reverse=True)
    for symbol, market_cap_b in in_15_20_range_sorted[:20]:
        print(f"  {symbol:15s} {market_cap_b:8.1f}B")

# Save results
results = {
    'timestamp': datetime.now().isoformat(),
    'market_cap_15b': len(cap_15b),
    'market_cap_20b': len(cap_20b),
    'additional_from_15b': len(cap_15b) - len(cap_20b),
    'summary': {
        'threshold_15b_count': len(cap_15b),
        'threshold_20b_count': len(cap_20b),
        'improvement': f"{((len(cap_15b) / len(cap_20b) - 1) * 100):.1f}%" if cap_20b else "N/A"
    }
}

with open('market_cap_threshold_analysis.json', 'w') as f:
    json.dump(results, f, indent=2)

print()
print("=" * 80)
print("Analysis saved to: market_cap_threshold_analysis.json")
print("=" * 80)
