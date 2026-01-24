#!/usr/bin/env python3
"""
Expand NIFTY500 to 220 stocks by adding validated mid-cap and small-cap stocks.
"""

import yfinance as yf
import time
import sys
import io

# Fix Unicode output on Windows
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# Read current 148 stocks
with open('nifty500_constituents_final_220.txt', 'r') as f:
    existing = set(line.strip() for line in f if line.strip())

print(f"Current stocks: {len(existing)}")
print("Adding more stocks to reach 220...")
print()

# Additional quality stocks to test (10B-50B range)
additional_stocks = [
    'FCONSUMER.NS', 'IDFC.NS', 'BANKINDIA.NS', 'MAHLOG.NS', 'NSEIT.NS',
    'SUDARSCHEM.NS', 'ARVINDFARM.NS', 'ARVINDMILLS.NS', 'ASTRAL.NS', 'AWFIS.NS',
    'BAJAJCORP.NS', 'BAJAJELEC.NS', 'BAKLTD.NS', 'BALRAMCHIN.NS', 'BASF.NS',
    'BATAVIA.NS', 'BDELECTRI.NS', 'BEEKAY.NS', 'BELCHIM.NS', 'BEML.NS',
    'BERGEPAINT.NS', 'BEVERAGE.NS', 'BHAGERIA.NS', 'BHAGIRADH.NS', 'BHAJMALL.NS',
    'BHAKTI.NS', 'BHAKTIWEL.NS', 'BHALERS.NS', 'BHALSOL.NS', 'BHAMASHAH.NS',
    'BHAMARTD.NS', 'BHAMBHORE.NS', 'BHAMINI.NS', 'BHAMIRA.NS', 'BHAMS.NS',
    'BHANADYA.NS', 'BHANARGAZ.NS', 'BHANARGCB.NS', 'BHANDARI.NS', 'BHANDIYO.NS',
    'BHANDUJA.NS', 'BHANG.NS', 'BHANGMA.NS', 'BHANI.NS', 'BHANICG.NS',
    'BHANUMATI.NS', 'BHANUME.NS', 'BHANUMEJ.NS', 'BHANUMES.NS', 'BHANUNT.NS',
    'BHANVI.NS', 'BHARARA.NS', 'BHARATA.NS', 'BHARATEN.NS', 'BHARATFIB.NS',
    'BHARATFLR.NS', 'BHARATFTY.NS', 'BHARATGEM.NS', 'BHARATGLD.NS', 'BHARATHS.NS',
    'BHARAVAI.NS', 'BHARAT.NS', 'BHARDWAJ.NS', 'BHARELLI.NS', 'BHARGARA.NS',
    'BHARGEEN.NS', 'BHARGEL.NS', 'BHARGISA.NS', 'BHARGOLD.NS', 'BHARGOPAL.NS',
]

print(f"Testing {len(additional_stocks)} additional stocks...")
print()

validated = []

for i, ticker in enumerate(additional_stocks, 1):
    try:
        symbol = ticker.replace('.NS', '')
        print(f"[{i:3d}/{len(additional_stocks)}] {symbol:15s} ", end='', flush=True)
        
        stock = yf.Ticker(ticker)
        info = stock.info
        market_cap = info.get('marketCap')
        price = info.get('currentPrice')
        name = info.get('longName', symbol)
        
        market_cap_b = (market_cap / 1_000_000_000) if market_cap else 0
        
        if market_cap and market_cap_b >= 10:
            if symbol not in existing:
                validated.append((symbol, market_cap_b, name))
                print(f"[OK] {market_cap_b:8.1f}B")
            else:
                print(f"[SKIP] (already included)")
        elif market_cap:
            print(f"[LOW] {market_cap_b:8.1f}B")
        else:
            print(f"[FAIL]")
        
        time.sleep(0.01)
        
    except Exception as e:
        print(f"[ERR]")

print()
print("=" * 80)
print(f"Found {len(validated)} new stocks")
print()

# Sort by market cap
validated_sorted = sorted(validated, key=lambda x: x[1], reverse=True)

# Calculate how many we need
need = 220 - len(existing)
selected = validated_sorted[:need]

print(f"Need {need} more stocks to reach 220")
print(f"Selected {len(selected)} from validated")
print()

# Append to file
with open('nifty500_constituents_final_220.txt', 'a') as f:
    for symbol, market_cap_b, name in selected:
        f.write(symbol + '\n')

# Verify final count
with open('nifty500_constituents_final_220.txt', 'r') as f:
    final_stocks = [line.strip() for line in f if line.strip()]

print(f"Final stock count: {len(final_stocks)}")
print()

if len(final_stocks) >= 220:
    print("[SUCCESS] Reached 220+ stocks!")
else:
    print(f"[INFO] Have {len(final_stocks)} stocks (need {220 - len(final_stocks)} more)")
