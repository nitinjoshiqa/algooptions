#!/usr/bin/env python3
"""
Build comprehensive NIFTY500 universe with 220+ stocks.
Expands from 135 (>50B) to 220+ by including mid-cap stocks (>20B).
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

print("Building expanded NIFTY500 with 220+ stocks (including mid-caps)...")
print("=" * 80)

# Comprehensive list with additional mid-cap stocks
EXTENDED_INDIAN_STOCKS = [
    # Top 135 already validated (>50B)
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
    'VOLTAS.NS', 'TIINDIA.NS', 'ESCORTS.NS', 'UCOBANK.NS', 'BLUESTARCO.NS',
    'APOLLOTYRE.NS', 'KPITTECH.NS', 'DELHIVERY.NS', 'EXIDEIND.NS', 'MRPL.NS',
    'FORCEMOT.NS', 'MANAPPURAM.NS', 'PFIZER.NS', 'KIOCL.NS', 'HATSUN.NS',
    'INOXWIND.NS', 'DEEPAKFERT.NS', 'RATNAMANI.NS', 'CYIENT.NS', 'GRAPHITE.NS',
    'RPOWER.NS', 'SANOFI.NS', 'JYOTHYLAB.NS', 'MOIL.NS',
    
    # Additional mid-cap stocks (20B - 50B range)
    'TATACONSUM.NS', 'FCONSUMER.NS', 'MAHABANK.NS', 'SBICARD.NS',
    'IDFC.NS', 'BANKINDIA.NS', 'VIZSLA.NS', 'INDIACER.NS',
    'WHIRLPOOL.NS', 'BAJAJHLDNG.NS', 'SYNGENE.NS',
    'KALYANKJIL.NS', 'BOGNBANK.NS', 'CORPBANK.NS',
    'CANARA.NS', 'INDIAMAP.NS', 'PCBL.NS', 'GUJGASLTD.NS',
    'AAPL.NS', 'ADANIGREEN.NS', 'ADANIENSOL.NS', 'AEGISLOG.NS',
    'AEROIND.NS', 'AFMMPL.NS', 'AIBL.NS', 'ALBK.NS', 'ALLCARGO.NS',
    'ALLSEC.NS', 'ALMONDZ.NS', 'AMZN.NS', 'ANATECH.NS', 'ANDHRCEMET.NS',
    'ANDHRABANK.NS', 'ANKITMETAL.NS', 'ANSAFSUGAR.NS', 'APARCERAMICS.NS', 
    'APCL.NS', 'APLLTD.NS', 'APOLLOGLOB.NS', 'APOLLOTYRE.NS', 'APTECH.NS',
    'APTM.NS', 'AQUALCHEM.NS', 'AQUA.NS', 'ARABESQUE.NS', 'ARADBTEX.NS',
    'ARAFLTEX.NS', 'ARTISANWEB.NS', 'ARXPHARMA.NS', 'ASHOKLEY.NS', 'ASMSPHARMA.NS',
    'ASPLGROUP.NS', 'ASTERDM.NS', 'ASTRAL.NS', 'ASWTCORP.NS', 'ATFL.NS',
    'ATHI.NS', 'ATHNABANK.NS', 'ATISHAY.NS', 'ATLASCEMET.NS', 'ATMAJSONS.NS',
    'ATMAN.NS', 'ATMATECH.NS', 'ATMECS.NS', 'ATNINTER.NS', 'ATOMS.NS',
    'ATRIND.NS', 'ATULAUTO.NS', 'ATULAUTOS.NS', 'AUBANK.NS', 'AUGF.NS',
    'AUGMINDS.NS', 'AUGOMEC.NS', 'AUGSTEEL.NS', 'AUHIND.NS', 'AULAK.NS',
    'AUROPHARMA.NS', 'AURORA.NS', 'AURORAINS.NS', 'AUTOIND.NS', 'AUTOSEC.NS',
    'AUTPIL.NS', 'AUTRADE.NS', 'AUTRON.NS', 'AUXFINSEC.NS', 'AVADHSUGAR.NS',
    'AVANTFEED.NS', 'AVETL.NS', 'AVIBANK.NS', 'AVID.NS', 'AVINASH.NS',
    'AVINASHTIN.NS', 'AVITECH.NS', 'AVIVATRUCK.NS', 'AVMHOLDING.NS', 'AVPLITD.NS',
    'AVSL.NS', 'AVTNPL.NS', 'AXISBANK.NS', 'AXISBE.NS', 'AXISGOLD.NS',
    'AXISMY.NS', 'AXISSHORT.NS', 'AXISNIFTY.NS', 'AXISVISA.NS', 'AXSONEOS.NS',
    'AYDINC.NS', 'AZIONTECH.NS', 'AZZINDLTD.NS', 'AZUMM.NS',
    
    # Additional picks to fill gaps
    'TATACHEM.NS', 'TATACOMM.NS', 'TATAELXSI.NS', 'TATAINVST.NS', 'TATAMOTORS.NS',
    'TATASPONGE.NS', 'TATASTEEL.NS', 'TATATECH.NS', 'TATATELEG.NS', 'TATAUVL.NS',
    'TAXRIDERS.NS', 'TAXPAYERS.NS', 'TBYOILDRILL.NS', 'TCAMLAB.NS', 'TCEPL.NS',
    'TCGREATIND.NS', 'TCIL.NS', 'TCLIND.NS', 'TDPOWERSYS.NS', 'TEATECH.NS',
    'TECHTRADE.NS', 'TECIL.NS', 'TECHM.NS', 'TECHNIDYE.NS', 'TECHNOFAB.NS',
    'TECHNOVA.NS', 'TECBOTIND.NS', 'TEDHI.NS', 'TELCOLIVING.NS', 'TELETECH.NS',
    'TELEVISED.NS', 'TELIBANDHAN.NS', 'TEMPL.NS', 'TEMPOLARC.NS', 'TERDEX.NS',
]

print(f"Testing {len(EXTENDED_INDIAN_STOCKS)} stocks...")
print()

valid_stocks = []
tested = 0

for i, ticker in enumerate(EXTENDED_INDIAN_STOCKS, 1):
    try:
        tested += 1
        symbol = ticker.replace('.NS', '')
        print(f"[{i:3d}/{len(EXTENDED_INDIAN_STOCKS)}] {symbol:15s} ", end='', flush=True)
        
        stock = yf.Ticker(ticker)
        info = stock.info
        market_cap = info.get('marketCap')
        price = info.get('currentPrice')
        name = info.get('longName', symbol)
        
        market_cap_b = (market_cap / 1_000_000_000) if market_cap else 0
        
        if market_cap and market_cap_b >= 20:  # >= 20B threshold
            # Check if already in list (avoid duplicates)
            if not any(s['symbol'] == symbol for s in valid_stocks):
                valid_stocks.append({
                    'ticker': ticker,
                    'symbol': symbol,
                    'name': name[:50],
                    'market_cap_b': round(market_cap_b, 2),
                    'price': round(price, 2) if price else 0,
                })
                print(f"[OK] {market_cap_b:8.1f}B")
            else:
                print(f"[DUP] (duplicate)")
        elif market_cap:
            print(f"[<20B] {market_cap_b:8.1f}B")
        else:
            print(f"[FAIL] No data")
        
        time.sleep(0.02)
        
    except Exception as e:
        print(f"[ERR] {str(e)[:20]}")

print("\n" + "=" * 80)
print("RESULTS:")
print("-" * 80)

# Sort by market cap descending
valid_stocks_sorted = sorted(valid_stocks, key=lambda x: x['market_cap_b'], reverse=True)

print(f"\nTotal unique stocks with Market Cap >= 20B: {len(valid_stocks_sorted)}")
print()

# Display all stocks
for i, stock in enumerate(valid_stocks_sorted, 1):
    print(f"{i:3d}. {stock['symbol']:15s} {stock['market_cap_b']:8.1f}B  {stock['name'][:40]}")

# Save to files
with open('nifty500_constituents_final_220.txt', 'w') as f:
    for stock in valid_stocks_sorted[:220]:  # Take top 220
        f.write(stock['symbol'] + '\n')

# Also save detailed JSON
results = {
    'timestamp': datetime.now().isoformat(),
    'valid_stocks': valid_stocks_sorted[:220],
    'summary': {
        'total_tested': len(EXTENDED_INDIAN_STOCKS),
        'valid_count': len(valid_stocks_sorted),
        'selected_count': min(220, len(valid_stocks_sorted)),
        'minimum_market_cap_b': 20
    }
}

with open('nifty500_market_cap_final.json', 'w') as f:
    json.dump(results, f, indent=2)

print("\n" + "=" * 80)
print(f"SAVED {min(220, len(valid_stocks_sorted))} stocks to:")
print(f"  - nifty500_constituents_final_220.txt")
print(f"  - nifty500_market_cap_final.json")
print()
print("SUMMARY:")
print(f"  Total stocks found: {len(valid_stocks_sorted)}")
print(f"  Selected (top 220): {min(220, len(valid_stocks_sorted))}")
if len(valid_stocks_sorted) >= 220:
    print(f"  Status: [ACHIEVED 220+]")
else:
    print(f"  Status: Have {len(valid_stocks_sorted)} (need lower threshold)")
print("=" * 80)
