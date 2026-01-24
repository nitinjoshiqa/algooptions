"""
Historical Data Manager
Manages 6-month historical OHLC data storage in SQLite for fast backtesting
"""

import sqlite3
import pandas as pd
import yfinance as yf
from datetime import datetime, timedelta
from pathlib import Path
import json

class HistoricalDataManager:
    """Manages historical data storage and retrieval."""
    
    def __init__(self, db_path='databases/historical_data.db'):
        """Initialize database connection."""
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.conn = None
        self._init_db()
    
    def _init_db(self):
        """Initialize database and create tables."""
        self.conn = sqlite3.connect(str(self.db_path))
        cursor = self.conn.cursor()
        
        # Create OHLC table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS ohlc_data (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                symbol TEXT NOT NULL,
                date TEXT NOT NULL,
                open REAL,
                high REAL,
                low REAL,
                close REAL,
                volume INTEGER,
                UNIQUE(symbol, date)
            )
        ''')
        
        # Create metadata table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS fetch_metadata (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                symbol TEXT UNIQUE NOT NULL,
                last_fetch_date TEXT,
                data_start_date TEXT,
                data_end_date TEXT,
                record_count INTEGER
            )
        ''')
        
        self.conn.commit()
        print("[OK] Database initialized: " + str(self.db_path))
    
    def fetch_and_store_6months(self, symbols, force_refresh=False):
        """
        Fetch last 6 months of data for symbols and store in database.
        
        Args:
            symbols: List of stock symbols (e.g., ['TECHM.NS', 'WIPRO.NS'])
            force_refresh: If True, refetch all data
        """
        end_date = datetime.now()
        start_date = end_date - timedelta(days=180)
        
        print("\n" + "=" * 100)
        print("FETCHING 6-MONTH HISTORICAL DATA")
        print("=" * 100)
        print("\nPeriod: " + start_date.strftime('%Y-%m-%d') + " to " + end_date.strftime('%Y-%m-%d'))
        print("Symbols: " + str(len(symbols)))
        print("Force refresh: " + str(force_refresh))
        
        cursor = self.conn.cursor()
        
        success_count = 0
        error_count = 0
        
        for i, symbol in enumerate(symbols, 1):
            print("[" + str(i) + "/" + str(len(symbols)) + "] " + symbol + "...", end=" ", flush=True)
            
            try:
                # Check if we should skip this symbol
                if not force_refresh:
                    cursor.execute('SELECT record_count FROM fetch_metadata WHERE symbol = ?', (symbol,))
                    result = cursor.fetchone()
                    if result and result[0] > 0:
                        print("[CACHED] " + str(result[0]) + " records")
                        continue
                
                # Fetch data from yfinance
                data = yf.download(
                    symbol,
                    start=start_date,
                    end=end_date,
                    progress=False
                )
                
                if data.empty:
                    print("[WARN] No data")
                    error_count += 1
                    continue
                
                # Store data
                data_reset = data.reset_index()
                data_reset['Date'] = pd.to_datetime(data_reset['Date'])
                
                # Insert records
                for _, row in data_reset.iterrows():
                    cursor.execute('''
                        INSERT OR REPLACE INTO ohlc_data 
                        (symbol, date, open, high, low, close, volume)
                        VALUES (?, ?, ?, ?, ?, ?, ?)
                    ''', (
                        symbol,
                        str(row['Date'].date()),
                        float(row['Open']),
                        float(row['High']),
                        float(row['Low']),
                        float(row['Close']),
                        int(row['Volume'])
                    ))
                
                # Update metadata
                min_date = str(data_reset['Date'].min().date())
                max_date = str(data_reset['Date'].max().date())
                cursor.execute('''
                    INSERT OR REPLACE INTO fetch_metadata
                    (symbol, last_fetch_date, data_start_date, data_end_date, record_count)
                    VALUES (?, ?, ?, ?, ?)
                ''', (
                    symbol,
                    datetime.now().strftime('%Y-%m-%d'),
                    min_date,
                    max_date,
                    len(data_reset)
                ))
                
                self.conn.commit()
                print("[OK] " + str(len(data_reset)) + " records")
                success_count += 1
                
            except Exception as e:
                print("[ERROR] " + str(e)[:50])
                error_count += 1
        
        print("\n" + "-" * 100)
        print("Summary: " + str(success_count) + " succeeded, " + str(error_count) + " failed")
        return success_count, error_count
    
    def get_price_at_date(self, symbol, date_str):
        """Get closing price on a specific date."""
        cursor = self.conn.cursor()
        cursor.execute('''
            SELECT close FROM ohlc_data 
            WHERE symbol = ? AND date = ?
        ''', (symbol, date_str))
        
        result = cursor.fetchone()
        return result[0] if result else None
    
    def get_price_after_days(self, symbol, date_str, days=2):
        """Get closing price N trading days after a date."""
        cursor = self.conn.cursor()
        cursor.execute('''
            SELECT close FROM ohlc_data 
            WHERE symbol = ? AND date > ?
            ORDER BY date ASC
            LIMIT 1 OFFSET ?
        ''', (symbol, date_str, days))
        
        result = cursor.fetchone()
        return result[0] if result else None
    
    def get_data_range(self, symbol, start_date, end_date):
        """Get OHLC data for date range."""
        cursor = self.conn.cursor()
        cursor.execute('''
            SELECT date, open, high, low, close, volume 
            FROM ohlc_data 
            WHERE symbol = ? AND date BETWEEN ? AND ?
            ORDER BY date ASC
        ''', (symbol, start_date, end_date))
        
        rows = cursor.fetchall()
        if not rows:
            return pd.DataFrame()
        
        df = pd.DataFrame(rows, columns=['date', 'open', 'high', 'low', 'close', 'volume'])
        df['date'] = pd.to_datetime(df['date'])
        return df
    
    def get_cached_symbols(self):
        """Get list of cached symbols."""
        cursor = self.conn.cursor()
        cursor.execute('SELECT symbol, record_count, data_start_date, data_end_date FROM fetch_metadata ORDER BY symbol')
        return cursor.fetchall()
    
    def get_db_status(self):
        """Get database statistics."""
        cursor = self.conn.cursor()
        
        cursor.execute('SELECT COUNT(DISTINCT symbol) FROM ohlc_data')
        symbol_count = cursor.fetchone()[0]
        
        cursor.execute('SELECT COUNT(*) FROM ohlc_data')
        record_count = cursor.fetchone()[0]
        
        cursor.execute('SELECT MIN(date), MAX(date) FROM ohlc_data')
        date_range = cursor.fetchone()
        
        return {
            'symbols': symbol_count,
            'records': record_count,
            'start_date': date_range[0],
            'end_date': date_range[1],
            'db_size_mb': self.db_path.stat().st_size / (1024 * 1024) if self.db_path.exists() else 0
        }
    
    def close(self):
        """Close database connection."""
        if self.conn:
            self.conn.close()

def main():
    """Load NIFTY100 symbols and fetch historical data."""
    
    # Load NIFTY100 symbols
    constituents_file = Path('data/constituents/nifty100_constituents.txt')
    
    if not constituents_file.exists():
        print("ERROR: File not found: " + str(constituents_file))
        return
    
    with open(constituents_file, 'r') as f:
        symbols_raw = f.read().strip().split(',')
    
    # Format symbols for yfinance
    symbols = [f"{sym.strip()}.NS" for sym in symbols_raw]
    
    print("\nLoaded " + str(len(symbols)) + " symbols from NIFTY100")
    print("First 5: " + str(symbols[:5]))
    
    # Initialize manager and fetch data
    manager = HistoricalDataManager()
    
    try:
        success, errors = manager.fetch_and_store_6months(symbols, force_refresh=False)
        
        # Show status
        print("\n" + "=" * 100)
        print("DATABASE STATUS")
        print("=" * 100)
        
        status = manager.get_db_status()
        print("\nSymbols cached: " + str(status['symbols']))
        print("Total records: " + "{:,}".format(status['records']))
        print("Date range: " + str(status['start_date']) + " to " + str(status['end_date']))
        print("Database size: " + "{:.2f}".format(status['db_size_mb']) + " MB")
        
        # Show cached symbols
        print("\n" + "=" * 100)
        print("CACHED SYMBOLS (Sample)")
        print("=" * 100)
        
        cached = manager.get_cached_symbols()
        for symbol, count, start, end in cached[:10]:
            print("  {:<15} {:>6} records  {} -> {}".format(symbol, count, start, end))
        
        if len(cached) > 10:
            print("  ... and " + str(len(cached) - 10) + " more")
        
        print("\n[SUCCESS] Data stored: " + str(manager.db_path))
        
    finally:
        manager.close()

if __name__ == '__main__':
    main()
