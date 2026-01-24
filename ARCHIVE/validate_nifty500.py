#!/usr/bin/env python3
"""
Validate NIFTY500 stocks for data availability.
Identifies stocks with reliable candle data from yfinance/Breeze.
"""

import time
import requests
from pathlib import Path
from data_providers import get_intraday_candles_for

# NIFTY500 comprehensive list - test 150+ stocks
NIFTY500_CANDIDATES = [
    # Pharma & Healthcare
    "ABCAPITAL", "BIOCON", "DRREDDY", "FORTIS", "GLENMARK", "GSKPHARMA",
    "IPCALAB", "JBCHEMO", "LAURUSLABS", "PHOENIX", "TORNTPHARM",
    
    # Auto & Auto Components
    "ASHOKLEY", "ESCORTS", "FORCEMOT", "MOTHERSON", "TVSMOTOR", "BEL",
    "AUTOIND", "EXIDEIND",
    
    # Finance & NBFC
    "CHOLAFIN", "MANAPPURAM", "MCLELECTRIC", "SHRIRAMFIN", "CREDITACC",
    
    # IT & Software
    "COFORGE", "KPITTECH", "LTTS", "PERSISTENT", "SOFTTECH", "KSOLVE",
    "BSOFT", "HCLTECL",
    
    # Chemicals & Materials
    "BASF", "BAYER", "DEEPAKFERT", "GRAPHITE", "GUJALKALI", "NOCIL",
    "PIDILITIND", "SRF", "TRONOX", "UPL",
    
    # Metals & Mining
    "COALINDIA", "HINDZINC", "JSPL", "KIOCL", "MOIL", "NMDC", "RATNAMANI",
    "SAIL", "TATASTEEL", "ICICIBANK",
    
    # Consumer & FMCG
    "BRITANNIA", "HATSUN", "JYOTHYLAB", "MARICO", "NESTLEIND", "VBL",
    "PHILIPSFOOD",
    
    # Infrastructure & Telecom
    "BHARTIARTL", "GTLINFRA", "INDTRADING", "IOLCP", "RPOWER",
    
    # Energy & Utilities
    "GAIL", "IBREALEST", "INDIGO", "IOC", "IRFC", "NTPC", "OIL", "ONGC",
    "RECLTD",
    
    # Real Estate
    "DLF", "LODHA", "RADIOCITY",
    
    # Media & Entertainment
    "REDTAPE", "SUNTV", "ZEE",
    
    # Others from NIFTY500
    "ASAHISPONGE", "ASTRAL", "AUTOIND", "BERGEPAINT", "BHEL",
    "BKMINDST", "BLUEDART", "BLUESTARCO", "BPCL", "CIL", "DHANI",
    "EXIDEIND", "GILLETTE", "GSKCONS", "HCLTECH", "HERITGFOOD",
    "IBULHSGFIN", "INFRATEL", "INOXWIND", "ISEC", "ITDC", "JBMA",
    "JKCEMENT", "JKTYRE", "JMFINANCIAL", "KALUPUR", "KALYANIFORGE",
    "KAMBMT", "KARUPADHYAY", "KAVVERIND", "KESHKAIND", "KINDHOTEL",
    "KNRCON", "KOTAKBANK", "KPRESSIONS", "KPTL", "KRESOIL", "KUNISEC",
    "KWITKOOL", "LALA", "LALPATHLABS", "LAURUS", "LAXMIMACH", "LTI",
    "LUPIN", "MAHINDRA", "MANAPPURAM", "MANUGRAPH", "MARALOVER",
    "MRPL", "MSPL", "MTARTECH", "MUTHYALARM", "NATCOPHARM",
    "NAVNETEDU", "NETWORK18", "NEWTECH", "NFLINFRA", "NIACIN",
    "NILAINFRA", "NINSYS", "NIRMHCLDY", "NLCINDIA", "NOLKINDUS",
    "NOVELTI", "NULLINFOSEC",
]

def check_stock_data(symbol, max_retries=2):
    """Check if stock has valid data from yfinance/Breeze."""
    for attempt in range(max_retries):
        try:
            print(f"  Testing {symbol}...", end="", flush=True)
            candles, src = get_intraday_candles_for(
                symbol, 
                interval='5minute',
                max_bars=200,
                use_yf=False,
                force_yf=True  # Force yfinance for broader coverage
            )
            
            if candles and len(candles) >= 100:
                price = float(candles[-1].get('close', 0))
                print(f" [OK] {src} ({len(candles)} bars, Price: Rs{price:,.0f})")
                return {
                    'symbol': symbol,
                    'status': 'OK',
                    'candles': len(candles),
                    'price': price,
                    'source': src
                }
            else:
                print(f" [FAIL] Insufficient data ({len(candles) if candles else 0} bars)")
                return {
                    'symbol': symbol,
                    'status': 'INSUFFICIENT_DATA',
                    'candles': len(candles) if candles else 0
                }
        except Exception as e:
            print(f" [ERROR] {str(e)[:40]}")
            if attempt < max_retries - 1:
                time.sleep(0.5)
                continue
            return {
                'symbol': symbol,
                'status': 'ERROR',
                'error': str(e)[:50]
            }
    
    return {'symbol': symbol, 'status': 'ERROR'}

def main():
    print("=" * 70)
    print("NIFTY500 Stock Validation - Finding 100+ Reliable Stocks")
    print("=" * 70)
    print(f"\nTesting {len(NIFTY500_CANDIDATES)} NIFTY500 candidates...\n")
    
    results = []
    ok_count = 0
    
    for symbol in NIFTY500_CANDIDATES:
        data = check_stock_data(symbol)
        results.append(data)
        
        if data['status'] == 'OK':
            ok_count += 1
        
        time.sleep(0.2)  # Rate limiting
        
        if ok_count >= 100:
            print(f"\n✓ Found 100 stocks with valid data. Stopping.")
            break
    
    # Filter to working stocks only
    working_stocks = [r for r in results if r['status'] == 'OK']
    working_stocks.sort(key=lambda x: x['symbol'])
    
    print(f"\n" + "=" * 70)
    print(f"Results: {len(working_stocks)} stocks with reliable data")
    print("=" * 70 + "\n")
    
    # Save list
    output_file = Path(__file__).parent / "nifty500_validated_stocks.txt"
    stock_list = ",".join([s['symbol'] for s in working_stocks])
    
    with open(output_file, 'w') as f:
        f.write(stock_list)
    
    print(f"Saved {len(working_stocks)} stocks to: {output_file.name}\n")
    print("Validated Stocks:")
    for i, s in enumerate(working_stocks, 1):
        print(f"{i:2d}. {s['symbol']:15s} ({s['candles']:3d} bars, Rs{s['price']:>8,.0f})")
    
    return working_stocks

if __name__ == '__main__':
    stocks = main()
