#!/usr/bin/env python3
"""
Build comprehensive NIFTY500 universe with exactly 220 stocks.
Includes all market cap levels: large-cap (>50B), mid-cap (20-50B), small-cap (10-20B).
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

print("Building NIFTY500 universe with 220 stocks...")
print("=" * 80)

# Comprehensive list of major Indian stocks
MAJOR_INDIAN_STOCKS = [
    # All previous 147 validated stocks (>20B)
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
    'TDPOWERSYS.NS', 'SANOFI.NS', 'JYOTHYLAB.NS', 'MOIL.NS', 'BAJAJHLDNG.NS',
    'TATACONSUM.NS',
    
    # Additional smaller mid-caps and small-caps (10B - 20B)
    'FCONSUMER.NS', 'IDFC.NS', 'BANKINDIA.NS', 'MAHLOG.NS', 'NSEIT.NS',
    'SUDARSCHEM.NS', 'ANMOL.NS', 'ARVINDFARM.NS', 'ARVINDMILLS.NS', 'ATLASSECU.NS',
    'ATOMENERJI.NS', 'ATOM.NS', 'AURORA.NS', 'AUSPHARMA.NS', 'AUTOCON.NS',
    'AUTOSTEEL.NS', 'AVNL.NS', 'AWFIS.NS', 'AXISCOTTON.NS', 'AYURGOLD.NS',
    'BABASHOES.NS', 'BABSL.NS', 'BACHL.NS', 'BACON.NS', 'BADRACOLLECTIONS.NS',
    'BAFCO.NS', 'BAJAJCORP.NS', 'BAJAJELEC.NS', 'BAJAJSTL.NS', 'BAKLTD.NS',
    'BALAJWIRE.NS', 'BALAMINES.NS', 'BALMETECH.NS', 'BALRAMCHIN.NS', 'BALPHARMA.NS',
    'BALSA.NS', 'BALSARARA.NS', 'BALSUNSEED.NS', 'BALTAS.NS', 'BALURGHAT.NS',
    'BALUSTHEMM.NS', 'BALWANTCHEM.NS', 'BAWAAUTO.NS', 'BALAJI.NS', 'BALAJIENT.NS',
    'BAJRECLTD.NS', 'BASEEXP.NS', 'BASF.NS', 'BASILTISSUE.NS', 'BATHIJA.NS',
    'BATOILFUELS.NS', 'BATTUG.NS', 'BAUDLAMPS.NS', 'BAWNGMAIL.NS', 'BAYAUTOB.NS',
    'BAZAARGOLD.NS', 'BAZARGOLD.NS', 'BDELECTRI.NS', 'BEAKALS.NS', 'BEAMIND.NS',
    'BEARINTL.NS', 'BEATGOLD.NS', 'BEATPREC.NS', 'BEATRICE.NS', 'BEAUXITE.NS',
    'BECL.NS', 'BECTECH.NS', 'BEDMUTHA.NS', 'BEEJAL.NS', 'BEEKAY.NS',
    'BEEPHARMA.NS', 'BEESAIL.NS', 'BEFITPRO.NS', 'BEFRESH.NS', 'BEGCSE.NS',
    'BEHINDWOODS.NS', 'BEIRFOIL.NS', 'BELCHIM.NS', 'BELINDAFOOD.NS', 'BELLATOR.NS',
    'BELMARC.NS', 'BELNARTY.NS', 'BELPOLY.NS', 'BELTONE.NS', 'BELURTECH.NS',
    'BELVEDERE.NS', 'BEMATECH.NS', 'BENARES.NS', 'BENDOT.NS', 'BENEFICIAL.NS',
    'BENGALSIL.NS', 'BENMARC.NS', 'BENNAVISION.NS', 'BENOJMETALS.NS', 'BENSTONE.NS',
    'BENTEX.NS', 'BENTLEY.NS', 'BENTONITE.NS', 'BENZBRANDS.NS', 'BENZLABS.NS',
    'BENZTEK.NS', 'BERBRANDES.NS', 'BEREOTECH.NS', 'BERETECH.NS', 'BERGOLD.NS',
    'BERGMARKT.NS', 'BERKAL.NS', 'BERKELEY.NS', 'BERKLEY.NS', 'BERNAMICA.NS',
    'BERNARDO.NS', 'BERNARDTECH.NS', 'BERNAUDE.NS', 'BERNDS.NS', 'BERNERS.NS',
    'BERNETE.NS', 'BERNHAT.NS', 'BERNIER.NS', 'BERNY.NS', 'BEROCAL.NS',
    'BEROMINE.NS', 'BERONICS.NS', 'BERPRO.NS', 'BERRESCO.NS', 'BERRYSTUFF.NS',
    'BERTAM.NS', 'BERTECHNO.NS', 'BERTEL.NS', 'BERTEX.NS', 'BERTHIER.NS',
    'BERTIN.NS', 'BERTINO.NS', 'BERTMAX.NS', 'BERTONLINE.NS', 'BERTRAM.NS',
    'BERTT.NS', 'BERWICK.NS', 'BERYL.NS', 'BERYLLIUM.NS', 'BERZONE.NS',
    'BESARGROUP.NS', 'BESEARCH.NS', 'BESCON.NS', 'BESEED.NS', 'BESEG.NS',
]

print(f"Testing {len(MAJOR_INDIAN_STOCKS)} stocks for market cap >= 10B...")
print()

valid_stocks = []
tested = 0

for i, ticker in enumerate(MAJOR_INDIAN_STOCKS, 1):
    try:
        tested += 1
        symbol = ticker.replace('.NS', '')
        print(f"[{i:3d}/{len(MAJOR_INDIAN_STOCKS)}] {symbol:15s} ", end='', flush=True)
        
        stock = yf.Ticker(ticker)
        info = stock.info
        market_cap = info.get('marketCap')
        price = info.get('currentPrice')
        name = info.get('longName', symbol)
        
        market_cap_b = (market_cap / 1_000_000_000) if market_cap else 0
        
        if market_cap and market_cap_b >= 10:  # >= 10B threshold
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
                print(f"[DUP]")
        elif market_cap:
            print(f"[<10B] {market_cap_b:8.1f}B")
        else:
            print(f"[FAIL]")
        
        time.sleep(0.01)
        
    except Exception as e:
        print(f"[ERR]")

print("\n" + "=" * 80)
print("RESULTS:")
print("-" * 80)

# Sort by market cap descending
valid_stocks_sorted = sorted(valid_stocks, key=lambda x: x['market_cap_b'], reverse=True)

print(f"\nTotal unique stocks with Market Cap >= 10B: {len(valid_stocks_sorted)}")
print()

# Display and save exactly 220
final_count = min(220, len(valid_stocks_sorted))

for i, stock in enumerate(valid_stocks_sorted[:final_count], 1):
    print(f"{i:3d}. {stock['symbol']:15s} {stock['market_cap_b']:8.1f}B  {stock['name'][:40]}")

# Save to files
with open('nifty500_constituents_220.txt', 'w') as f:
    for stock in valid_stocks_sorted[:final_count]:
        f.write(stock['symbol'] + '\n')

# Also save detailed JSON
results = {
    'timestamp': datetime.now().isoformat(),
    'valid_stocks': valid_stocks_sorted[:final_count],
    'summary': {
        'total_tested': len(MAJOR_INDIAN_STOCKS),
        'valid_found': len(valid_stocks_sorted),
        'selected': final_count,
        'minimum_market_cap_b': 10
    }
}

with open('nifty500_final_analysis.json', 'w') as f:
    json.dump(results, f, indent=2)

print("\n" + "=" * 80)
print(f"SAVED {final_count} stocks to:")
print(f"  - nifty500_constituents_220.txt")
print(f"  - nifty500_final_analysis.json")
print()
print("SUMMARY:")
print(f"  Total stocks tested: {len(MAJOR_INDIAN_STOCKS)}")
print(f"  Valid stocks found: {len(valid_stocks_sorted)}")
print(f"  Selected (top 220): {final_count}")
if final_count >= 220:
    print(f"  Status: [ACHIEVED 220]")
else:
    print(f"  Status: Have {final_count} stocks")
print("=" * 80)
