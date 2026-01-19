#!/usr/bin/env python3
# scripts/init_database.py
"""
Initialize SQLite database for trading framework.

One-time setup script that:
  1. Creates all tables (stocks, prices, daily_scores, trade_executions, bucket_analytics)
  2. Loads NIFTY 50 stock master data
  3. Imports 12 months of historical price data from Yahoo Finance
  4. Ready for daily score updates

Usage:
  python scripts/init_database.py
"""

import os
import sys
from datetime import datetime, timedelta, date
import yfinance as yf
import pandas as pd

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.database import init_db, get_session, close_session, get_or_create_stock
from core.database_operations import save_price


# NIFTY 50 Stocks
NIFTY_50_STOCKS = [
    ("ADANIGREEN", "Adani Green Energy"),
    ("ADANIENT", "Adani Enterprises"),
    ("ADANIPORTS", "Adani Ports"),
    ("APOLLOHOSP", "Apollo Hospitals"),
    ("ASIANPAINT", "Asian Paints"),
    ("AXISBANK", "Axis Bank"),
    ("BAJAJ-AUTO", "Bajaj Auto"),
    ("BAJAJFINSV", "Bajaj Finserv"),
    ("BAJAZJMOTOR", "Bajaj Motors"),
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


def load_nifty_stocks(session):
    """Load NIFTY 50 stocks into database."""
    print("\n📚 Loading NIFTY 50 stocks...")
    
    for symbol, name in NIFTY_50_STOCKS:
        stock = get_or_create_stock(
            session,
            symbol=symbol,
            name=name,
            sector="Mixed",
            nifty_constituent=True
        )
        print(f"  ✅ {symbol}: {name}")
    
    print(f"\n✅ Loaded {len(NIFTY_50_STOCKS)} NIFTY stocks")


def load_historical_prices(session, days: int = 365):
    """Load historical price data from Yahoo Finance."""
    print(f"\n📈 Loading {days} days of historical price data...")
    
    start_date = (date.today() - timedelta(days=days)).strftime('%Y-%m-%d')
    end_date = date.today().strftime('%Y-%m-%d')
    
    symbols_to_load = [symbol for symbol, _ in NIFTY_50_STOCKS]
    
    loaded_count = 0
    failed_symbols = []
    
    for symbol in symbols_to_load:
        try:
            print(f"  Loading {symbol}...", end=" ")
            
            # Add .NS for NSE stocks
            ticker = f"{symbol}.NS"
            df = yf.download(ticker, start=start_date, end=end_date, progress=False, show_errors=False)
            
            if df.empty:
                print("❌ No data")
                failed_symbols.append(symbol)
                continue
            
            # Save each day's OHLCV
            for idx, row in df.iterrows():
                trade_date = idx.date()
                save_price(
                    session,
                    symbol=symbol,
                    trade_date=trade_date,
                    open_price=float(row['Open']),
                    high=float(row['High']),
                    low=float(row['Low']),
                    close=float(row['Close']),
                    volume=int(row['Volume'])
                )
            
            loaded_count += 1
            print(f"✅ {len(df)} days")
            
        except Exception as e:
            print(f"❌ Error: {str(e)[:50]}")
            failed_symbols.append(symbol)
    
    print(f"\n✅ Loaded {loaded_count}/{len(symbols_to_load)} symbols")
    
    if failed_symbols:
        print(f"⚠️  Failed to load: {', '.join(failed_symbols)}")
    
    return loaded_count


def print_database_stats(session):
    """Print database statistics."""
    from core.database import Stock, Price, DailyScore, TradeExecution, BucketAnalytic
    
    stock_count = session.query(Stock).count()
    price_count = session.query(Price).count()
    score_count = session.query(DailyScore).count()
    trade_count = session.query(TradeExecution).count()
    bucket_count = session.query(BucketAnalytic).count()
    
    print("\n" + "="*50)
    print("📊 DATABASE STATISTICS")
    print("="*50)
    print(f"  Stocks:          {stock_count:,}")
    print(f"  Price Records:   {price_count:,}")
    print(f"  Daily Scores:    {score_count:,}")
    print(f"  Trade Executions:{trade_count:,}")
    print(f"  Bucket Analytics:{bucket_count:,}")
    print("="*50)
    
    # Calculate storage size
    import os
    db_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "trading_data.db")
    if os.path.exists(db_path):
        size_mb = os.path.getsize(db_path) / (1024 * 1024)
        print(f"\n💾 Database Size: {size_mb:.2f} MB")
        print(f"📍 Location: {db_path}")


def main():
    """Main initialization routine."""
    print("\n" + "="*60)
    print("🚀 TRADING DATABASE INITIALIZATION")
    print("="*60)
    print(f"   Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Step 1: Create database
    print("\n[1/3] Creating database schema...")
    try:
        init_db()
        print("✅ Database schema created")
    except Exception as e:
        print(f"❌ Error creating database: {e}")
        return False
    
    session = get_session()
    
    try:
        # Step 2: Load stocks
        print("\n[2/3] Loading NIFTY 50 master data...")
        load_nifty_stocks(session)
        
        # Step 3: Load historical data
        print("\n[3/3] Loading 12 months of historical price data...")
        print("    (This may take 2-3 minutes. Please wait...)")
        loaded = load_historical_prices(session, days=365)
        
        if loaded == 0:
            print("\n❌ WARNING: No historical data loaded!")
            print("   Check internet connection and Yahoo Finance availability")
            return False
        
        # Print statistics
        print_database_stats(session)
        
        print("\n" + "="*60)
        print("✅ DATABASE INITIALIZATION COMPLETE")
        print("="*60)
        print("\n📌 Next Steps:")
        print("   1. Daily screener automatically saves scores to database")
        print("   2. Track trades with: python scripts/track_trade.py")
        print("   3. Analyze performance with: python analysis/validate_framework.py")
        print("   4. Run backtest with: python backtesting/run_backtest.py")
        print("\n💡 Commands to try:")
        print("   python nifty_bearnness_v2.py --universe nifty --mode swing --force-yf --screener-format html")
        print("   python -c \"from core.database_operations import *; s=get_session(); print(len(get_today_scores(s)))\"")
        
        return True
        
    except Exception as e:
        print(f"\n❌ Error during initialization: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        close_session(session)


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
