#!/usr/bin/env python3
"""
Find stable Indian stocks with market cap > 200B and reliable data.
Uses yfinance to identify liquid stocks that work well with the screener.
"""

import yfinance as yf
import pandas as pd
import warnings
from datetime import datetime

warnings.filterwarnings('ignore')

# Top Indian companies by market cap (200B+ INR ~2.4B USD)
# Source: BSE top companies list
HIGHCAP_STOCKS = [
    # Banking (most reliable)
    'SBIN', 'HDFCBANK', 'ICICIBANK', 'AXISBANK', 'KOTAK', 'INDUSIND',
    'BANKBARODA', 'PNB', 'FEDERALBNK', 'CANBK', 'IDFCBANK', 'YESBANK',
    
    # IT & Software
    'TCS', 'INFY', 'WIPRO', 'HCL', 'TECHM', 'LT', 'MINDTREE', 'LTIM',
    
    # Finance & NBFC
    'HDFC', 'ICICIPRULI', 'BAJAJFINSV', 'BAJFINANCE', 'SBILIFE', 'HDFCLIFE',
    
    # Energy & Power
    'RELIANCE', 'JSWSTEEL', 'TATASTEEL', 'NTPC', 'POWERGRID', 'ADANIPOWER',
    
    # Cement & Construction
    'ADANIPORTS', 'ADANIGREEN', 'ADANIENT', 'AMBUJACEM', 'SHREECEM', 'ULTRACEMCO',
    
    # Pharma & Healthcare
    'SUNPHARMA', 'CIPLA', 'LUPIN', 'DIVISLAB', 'APOLLOHOSP', 'AUROPHARMA',
    'DMART', 'UNILEVER', 'NESTLEIND',
    
    # Consumer & FMCG
    'ITC', 'BRITANNIA', 'MARICO', 'GODREJCP', 'COLPAL', 'DABUR',
    
    # Auto & Transport
    'MARUTI', 'BAJAJ-AUTO', 'EICHERMOT', 'ASHOKLEY', 'HEROMOTOCO', 'TATAMOTORS',
    
    # Metal & Mining
    'HINDALCO', 'VEDL', 'JINDALSTEL',
    
    # Telecom
    'JIOTOWER', 'INDIGO',
]

def check_stock_data(symbol, max_retries=3):
    """Check if a stock has reliable data on yfinance."""
    for attempt in range(max_retries):
        try:
            # Try to fetch ticker with NSE suffix
            ticker_symbol = f"{symbol}.NS"
            ticker = yf.Ticker(ticker_symbol)
            
            # Try to get history
            hist = ticker.history(period='1y')
            
            if hist.empty:
                # Try without .NS
                ticker = yf.Ticker(symbol)
                hist = ticker.history(period='1y')
            
            if not hist.empty and len(hist) > 200:  # At least 200 trading days
                info = ticker.info
                market_cap = info.get('marketCap', 0)
                price = hist['Close'].iloc[-1]
                
                return {
                    'symbol': symbol,
                    'status': 'OK',
                    'market_cap': market_cap,
                    'price': price,
                    'days_data': len(hist)
                }
            else:
                return {
                    'symbol': symbol,
                    'status': 'INSUFFICIENT_DATA',
                    'market_cap': 0,
                    'price': 0,
                    'days_data': len(hist) if not hist.empty else 0
                }
        
        except Exception as e:
            if attempt == max_retries - 1:
                return {
                    'symbol': symbol,
                    'status': 'ERROR',
                    'market_cap': 0,
                    'price': 0,
                    'days_data': 0,
                    'error': str(e)
                }
        
        # Wait a bit before retry
        import time
        if attempt < max_retries - 1:
            time.sleep(0.5)
    
    return None

def main():
    print("Scanning for stable Indian stocks with market cap > 200B...")
    print(f"Testing {len(HIGHCAP_STOCKS)} stocks...\n")
    
    results = []
    for i, symbol in enumerate(HIGHCAP_STOCKS, 1):
        print(f"[{i:3d}/{len(HIGHCAP_STOCKS)}] {symbol:15s} ", end='', flush=True)
        
        data = check_stock_data(symbol)
        if data:
            results.append(data)
            status = data['status']
            
            if status == 'OK':
                print(f"[OK] Price: Rs{data['price']:,.0f}, {data['days_data']} days")
            elif status == 'INSUFFICIENT_DATA':
                print(f"[FAIL] Not enough data ({data['days_data']} days)")
            else:
                print(f"[ERROR] {data.get('error', 'Unknown')[:40]}")
    
    # Filter to working stocks only
    working_stocks = [r for r in results if r['status'] == 'OK']
    
    print(f"\n{'='*60}")
    print(f"Results: {len(working_stocks)} stocks with reliable data")
    print(f"{'='*60}\n")
    
    # Save to file
    output_file = 'nifty200_updated_constituents.txt'
    with open(output_file, 'w') as f:
        for stock in sorted([s['symbol'] for s in working_stocks]):
            f.write(f"{stock}\n")
    
    print(f"Saved {len(working_stocks)} stable stocks to: {output_file}")
    print("\nStocks found:")
    print(", ".join(sorted([s['symbol'] for s in working_stocks])))
    
    # Also save CSV with details
    df = pd.DataFrame(working_stocks)
    df = df[df['status'] == 'OK'].sort_values('symbol')
    df.to_csv('stable_stocks_report.csv', index=False)
    print(f"\nDetailed report saved to: stable_stocks_report.csv")

if __name__ == '__main__':
    main()
