#!/usr/bin/env python3
# scripts/populate_database.py
"""
Populate existing database with NIFTY 50 stocks and historical price data.
"""

import os
import sys
from datetime import datetime, timedelta, date

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.database import get_session, close_session, get_or_create_stock, Stock, Price
from core.database_operations import save_price

try:
    import yfinance as yf
except ImportError:
    print("❌ yfinance not installed. Installing...")
    os.system(f"{sys.executable} -m pip install yfinance --quiet")
    import yfinance as yf


NIFTY_50_STOCKS = [
    ("ADANIGREEN", "Adani Green Energy"),
    ("ADANIENT", "Adani Enterprises"),
    ("ADANIPORTS", "Adani Ports"),
    ("APOLLOHOSP", "Apollo Hospitals"),
    ("ASIANPAINT", "Asian Paints"),
    ("AXISBANK", "Axis Bank"),
    ("BAJAJ-AUTO", "Bajaj Auto"),
    ("BAJAJFINSV", "Bajaj Finserv"),
    ("BAJAJMOTOR", "Bajaj Motors"),
    ("BHARTIARTL", "Bharti Airtel"),
    ("BPCL", "BPCL"),
    ("BRITANNIA", "Britannia"),
    ("BSOFT", "Brookfield Software"),
    ("CGPOWER", "CG Power"),
    ("CIPLA", "Cipla"),
    ("COALINDIA", "Coal India"),
    ("COLPAL", "Colgate Palmolive"),
    ("DIVISLAB", "Divi's Labs"),
    ("EICHERMOT", "Eicher Motors"),
    ("GAIL", "GAIL"),
    ("GRASIM", "Grasim Industries"),
    ("HCLTECH", "HCL Technologies"),
    ("HDFCBANK", "HDFC Bank"),
    ("HDFCLIFE", "HDFC Life"),
    ("HEROMOTOCO", "Hero MotoCorp"),
    ("HINDALCO", "Hindalco"),
    ("HINDPETRO", "Hindustan Petroleum"),
    ("HINDUNILVR", "Hindustan Unilever"),
    ("ICICIBANK", "ICICI Bank"),
    ("ICICIPRULI", "ICICI Prudential"),
    ("INFY", "Infosys"),
    ("INDUSINDBK", "IndusInd Bank"),
    ("IOC", "Indian Oil"),
    ("ITC", "ITC"),
    ("JSWSTEEL", "JSW Steel"),
    ("KOTAKBANK", "Kotak Mahindra Bank"),
    ("LT", "Larsen & Toubro"),
    ("LTIM", "LT Infotech"),
    ("MARUTI", "Maruti Suzuki"),
    ("MAXHEALTH", "Max Healthcare"),
    ("NESTLEIND", "Nestle India"),
    ("NTPC", "NTPC"),
    ("ONGC", "ONGC"),
    ("POWERGRID", "Power Grid"),
    ("RELIANCE", "Reliance Industries"),
    ("SBIN", "State Bank of India"),
    ("SBILIFE", "SBI Life"),
    ("SUNPHARMA", "Sun Pharma"),
    ("TATAMOTORS", "Tata Motors"),
    ("TATAPOWER", "Tata Power"),
    ("TATASTEEL", "Tata Steel"),
    ("TCS", "TCS"),
    ("TECHM", "Tech Mahindra"),
    ("TITAN", "Titan"),
    ("TORNTPHARM", "Torrent Pharma"),
    ("ULTRACEMCO", "UltraTech Cement"),
    ("UNITDSPR", "United Spirits"),
    ("VEDL", "Vedanta"),
    ("WIPRO", "Wipro"),
]


def main():
    print("\n" + "="*60)
    print("📊 DATABASE POPULATION")
    print("="*60)
    
    session = get_session()
    
    try:
        # Step 1: Load stocks
        print("\n[1/2] Loading NIFTY 50 stocks...")
        for symbol, name in NIFTY_50_STOCKS:
            get_or_create_stock(session, symbol, name, nifty_constituent=True)
            print(f"  ✅ {symbol}")
        
        stock_count = session.query(Stock).count()
        print(f"\n✅ Loaded {stock_count} stocks")
        
        # Step 2: Load historical data
        print("\n[2/2] Loading 365 days of historical price data...")
        print("    (This takes 2-3 minutes, please wait...)\n")
        
        start_date = (date.today() - timedelta(days=365)).strftime('%Y-%m-%d')
        end_date = date.today().strftime('%Y-%m-%d')
        
        loaded_count = 0
        failed_symbols = []
        
        for symbol, name in NIFTY_50_STOCKS:
            try:
                print(f"  Loading {symbol:12} ...", end=" ", flush=True)
                
                ticker = f"{symbol}.NS"
                df = yf.download(ticker, start=start_date, end=end_date, progress=False, show_errors=False)
                
                if df.empty:
                    print("❌ No data")
                    failed_symbols.append(symbol)
                    continue
                
                # Save prices
                for idx, row in df.iterrows():
                    save_price(
                        session,
                        symbol=symbol,
                        trade_date=idx.date(),
                        open_price=float(row['Open']),
                        high=float(row['High']),
                        low=float(row['Low']),
                        close=float(row['Close']),
                        volume=int(row['Volume'])
                    )
                
                loaded_count += 1
                print(f"✅ {len(df):3d} days")
                
            except Exception as e:
                print(f"❌ Error")
                failed_symbols.append(symbol)
        
        # Statistics
        price_count = session.query(Price).count()
        
        print("\n" + "="*60)
        print("✅ DATABASE POPULATION COMPLETE")
        print("="*60)
        print(f"\n📊 Summary:")
        print(f"   Stocks loaded:     {stock_count}")
        print(f"   Price records:     {price_count:,}")
        print(f"   Symbols succeeded: {loaded_count}/{len(NIFTY_50_STOCKS)}")
        
        if failed_symbols:
            print(f"\n⚠️  Failed to load ({len(failed_symbols)}): {', '.join(failed_symbols)}")
        
        # Database size
        db_path = 'trading_data.db'
        if os.path.exists(db_path):
            size_mb = os.path.getsize(db_path) / (1024 * 1024)
            print(f"\n💾 Database size: {size_mb:.2f} MB")
        
        print("\n📌 Next Steps:")
        print("   1. Run daily screener: python nifty_bearnness_v2.py --universe nifty --mode swing --force-yf --screener-format html")
        print("   2. View database: python -c \"from core.database_operations import get_today_scores; s=get_session(); print(len(get_today_scores(s)))\"")
        print("   3. Backtest: python backtesting/run_backtest.py")
        
        return True
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        close_session(session)


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
