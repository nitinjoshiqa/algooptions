#!/usr/bin/env python3
"""
Expanded test: Check broader set of Indian stocks for 15B-20B range
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

print("Expanded search: Finding stocks in 15B-20B range")
print("=" * 80)

# Expanded list with many smaller players
EXPANDED_STOCKS = [
    # Previously tested 144
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
    
    # Additional smaller cap stocks (potentially 15B-20B)
    'FCONSUMER.NS', 'IDFC.NS', 'BANKINDIA.NS', 'BOSCHLTD.NS', 'TITAN.NS',
    'PAGEIND.NS', 'HEROMOTOCO.NS', 'TORNTPOWER.NS', 'TORNTPHARM.NS', 'SIEMENS.NS',
    'NITINSOFTW.NS', 'HINDZINC.NS', 'IPCALAB.NS', 'LAXMIMACH.NS', 'LTTS.NS',
    'GSKPHARMA.NS', 'SUNTVNEWS.NS', 'SUNTV.NS', 'PHILIPSFOOD.NS', 'MEDPLUS.NS',
    'ASIANPAINT.NS', 'BSOFT.NS', 'COMFORTIND.NS', 'DALBHUMI.NS', 'GLOSTERIND.NS',
    'GUJALKALI.NS', 'KAMINENI.NS', 'MIDHANI.NS', 'MSPL.NS', 'MUTHYALARM.NS',
    'NLCINDIA.NS', 'NOCIL.NS', 'PDSL.NS', 'PHILIPSFOOD.NS', 'PIIND.NS',
    'PRECWIRES.NS', 'SOLARINDS.NS', 'SOFTTECH.NS', 'SONACOMS.NS', 'SPORTSART.NS',
    'UNITDSPR.NS', 'UNILEVER.NS', 'VBL.NS', 'VGUARD.NS', 'VINATIORGA.NS',
    'VRLLOG.NS', 'WABCOINDIA.NS', 'WESTLIFE.NS', 'YESBANK.NS', 'ZEEL.NS',
    'ZYDUSLIFE.NS', 'ZYDUSWELL.NS', 'SHRIRAMFIN.NS',
]

print(f"Testing {len(EXPANDED_STOCKS)} stocks for Market Cap >= 15B...")
print()

results_15b = []
results_20b = []
failed = 0

for i, ticker in enumerate(EXPANDED_STOCKS, 1):
    try:
        symbol = ticker.replace('.NS', '')
        print(f"[{i:3d}/{len(EXPANDED_STOCKS)}] {symbol:15s} ", end='', flush=True)
        
        stock = yf.Ticker(ticker)
        info = stock.info
        market_cap = info.get('marketCap')
        
        market_cap_b = (market_cap / 1_000_000_000) if market_cap else 0
        
        if market_cap:
            if market_cap_b >= 15:
                results_15b.append((symbol, market_cap_b))
                if market_cap_b >= 20:
                    results_20b.append((symbol, market_cap_b))
                print(f"[OK] {market_cap_b:8.1f}B")
            else:
                print(f"[<15B] {market_cap_b:8.1f}B")
        else:
            print(f"[FAIL]")
            failed += 1
        
        time.sleep(0.01)
        
    except Exception as e:
        print(f"[ERR]")
        failed += 1

print("\n" + "=" * 80)
print("COMPREHENSIVE ANALYSIS:")
print("-" * 80)
print()

cap_15_20 = [(s, m) for s, m in results_15b if m < 20]
cap_15_20_sorted = sorted(cap_15_20, key=lambda x: x[1], reverse=True)

print(f"Stocks >= 20B:          {len(results_20b)}")
print(f"Stocks >= 15B:          {len(results_15b)}")
print(f"Stocks in 15B-20B range: {len(cap_15_20)}")
print()

if cap_15_20:
    print("Stocks in 15B-20B range:")
    for symbol, market_cap_b in cap_15_20_sorted:
        print(f"  {symbol:15s} {market_cap_b:8.1f}B")

print()
print("=" * 80)
print("COMPARISON:")
print("-" * 80)
print(f"Current 220-list (>=20B): 148 stocks")
print(f"Potential at >=15B:       {len(results_15b)} stocks")
print(f"Additional stocks:        {len(results_15b) - len(results_20b)}")
print()

improvement_pct = ((len(results_15b) / 148) - 1) * 100 if results_15b else 0
print(f"Improvement: {improvement_pct:+.1f}%")
print("=" * 80)
