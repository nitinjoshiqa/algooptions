"""
Event Calendar - Fetch and manage earnings/result dates for stocks.

This module provides functions to:
1. Get earnings dates from Breeze API (if available)
2. Load earnings dates from CSV calendar file (user-maintained)
3. Try yfinance API as fallback
4. Calculate days until next earnings
5. Use as input for theta decay scoring

CSV Format (event_calendar.csv):
    symbol,earnings_date,event_type
    SBIN,2026-02-15,Q3-Results
    RELIANCE,2026-02-20,Q3-Results
    HDFCBANK,2026-01-25,Q3-Results
"""

from datetime import datetime, timedelta
import yfinance as yf
import logging
from pathlib import Path
import csv
import warnings

# Suppress yfinance warnings about missing earnings dates
warnings.filterwarnings('ignore', message='.*No earnings dates found.*')
warnings.filterwarnings('ignore', message='.*symbol may be delisted.*')

logger = logging.getLogger(__name__)

# Cache for earnings dates (avoid repeated API calls)
EARNINGS_CACHE = {}
CACHE_VALIDITY_DAYS = 7
EARNINGS_CACHE_FILE = Path(__file__).parent / ".earnings_cache.json"

# Path to manually maintained earnings calendar
# Look for event_calendar.csv in the root project directory
EARNINGS_CALENDAR_PATH = Path(__file__).parent.parent.parent / "event_calendar.csv"

# Try to import Breeze for earnings data
try:
    from utils.breeze_api import get_breeze_instance
    BREEZE_AVAILABLE = True
except:
    BREEZE_AVAILABLE = False

def _load_persistent_cache():
    """Load earnings cache from disk if it exists."""
    global EARNINGS_CACHE
    if EARNINGS_CACHE_FILE.exists():
        try:
            import json
            with open(EARNINGS_CACHE_FILE, 'r') as f:
                cached_data = json.load(f)
                # Restore cache with datetime objects
                for symbol, data in cached_data.items():
                    if data.get('fetch_time'):
                        data['fetch_time'] = datetime.fromisoformat(data['fetch_time'])
                    if data.get('next_earnings'):
                        data['next_earnings'] = datetime.fromisoformat(data['next_earnings'])
                EARNINGS_CACHE = cached_data
                logger.debug(f"Loaded {len(EARNINGS_CACHE)} cached earnings dates from disk")
        except Exception as e:
            logger.debug(f"Could not load persistent cache: {e}")

def _save_persistent_cache():
    """Save earnings cache to disk."""
    try:
        import json
        cache_to_save = {}
        for symbol, data in EARNINGS_CACHE.items():
            cache_to_save[symbol] = {
                'next_earnings': data['next_earnings'].isoformat() if data.get('next_earnings') else None,
                'days_until': data.get('days_until'),
                'fetch_time': data['fetch_time'].isoformat() if data.get('fetch_time') else None
            }
        
        with open(EARNINGS_CACHE_FILE, 'w') as f:
            json.dump(cache_to_save, f, indent=2)
    except Exception as e:
        logger.debug(f"Could not save persistent cache: {e}")

def _is_cache_stale(last_fetch_date):
    """Check if cache entry is older than CACHE_VALIDITY_DAYS."""
    if last_fetch_date is None:
        return True
    return (datetime.now() - last_fetch_date).days >= CACHE_VALIDITY_DAYS

# Load persistent cache on module import
_load_persistent_cache()

def get_earnings_from_breeze(symbol):
    """
    Fetch earnings dates from Breeze API.
    
    Breeze has detailed corporate action data including earnings announcements.
    """
    if not BREEZE_AVAILABLE:
        return None
    
    try:
        breeze = get_breeze_instance()
        
        # Check if it's a dummy instance
        if breeze.__class__.__name__ == '_DummyBreeze':
            return None
        
        # Breeze API call for corporate actions / earnings
        # The exact method depends on Breeze documentation
        # Try to get corporate actions which includes earnings announcements
        
        # Note: This is a tentative API call - may need adjustment based on actual Breeze API
        try:
            # Try different possible method names
            if hasattr(breeze, 'get_corporate_actions'):
                result = breeze.get_corporate_actions(symbol=symbol)
                if result and isinstance(result, list):
                    # Look for earnings/result announcements
                    for action in result:
                        if 'earnings' in str(action).lower() or 'result' in str(action).lower():
                            # Parse the date
                            if isinstance(action, dict) and 'date' in action:
                                try:
                                    earnings_date = datetime.strptime(action['date'], '%Y-%m-%d')
                                    return earnings_date
                                except:
                                    pass
            
            # Try alternative method name
            elif hasattr(breeze, 'get_events'):
                result = breeze.get_events(symbol=symbol)
                if result and isinstance(result, dict):
                    events = result.get('events', [])
                    for event in events:
                        if 'earnings' in str(event).lower() or 'result' in str(event).lower():
                            if isinstance(event, dict) and 'date' in event:
                                try:
                                    earnings_date = datetime.strptime(event['date'], '%Y-%m-%d')
                                    return earnings_date
                                except:
                                    pass
        
        except Exception as e:
            logger.debug(f"Breeze API call failed for {symbol}: {e}")
        
        return None
    
    except Exception as e:
        logger.debug(f"Error fetching from Breeze for {symbol}: {e}")
        return None


def load_earnings_calendar():
    """Load earnings dates from CSV file if it exists."""
    calendar = {}
    
    if EARNINGS_CALENDAR_PATH.exists():
        try:
            with open(EARNINGS_CALENDAR_PATH, 'r') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    symbol = row.get('symbol', '').strip()
                    date_str = row.get('earnings_date', '').strip()
                    
                    if symbol and date_str:
                        try:
                            earnings_date = datetime.strptime(date_str, '%Y-%m-%d')
                            calendar[symbol] = {
                                'date': earnings_date,
                                'type': row.get('event_type', 'Results')
                            }
                        except ValueError:
                            logger.debug(f"Invalid date format for {symbol}: {date_str}")
            
            logger.info(f"Loaded {len(calendar)} events from {EARNINGS_CALENDAR_PATH}")
        except Exception as e:
            logger.error(f"Error loading earnings calendar: {e}")
    
    return calendar


def save_earnings_to_csv(symbol, earnings_date, event_type='Results'):
    """
    Save a fetched earnings date to the CSV file.
    
    Args:
        symbol: Stock symbol (e.g., 'SBIN')
        earnings_date: datetime object of the earnings date
        event_type: Type of event (default: 'Results')
    """
    try:
        # Read existing data
        existing_data = {}
        if EARNINGS_CALENDAR_PATH.exists():
            try:
                with open(EARNINGS_CALENDAR_PATH, 'r') as f:
                    reader = csv.DictReader(f)
                    for row in reader:
                        sym = row.get('symbol', '').strip()
                        if sym:
                            existing_data[sym] = row
            except Exception as e:
                logger.debug(f"Could not read existing CSV: {e}")
        
        # Update or add entry
        if earnings_date:
            existing_data[symbol] = {
                'symbol': symbol,
                'earnings_date': earnings_date.strftime('%Y-%m-%d'),
                'event_type': event_type
            }
        
        # Write back to CSV
        if existing_data:
            with open(EARNINGS_CALENDAR_PATH, 'w', newline='') as f:
                writer = csv.DictWriter(f, fieldnames=['symbol', 'earnings_date', 'event_type'])
                writer.writeheader()
                
                # Sort by symbol for readability
                for symbol in sorted(existing_data.keys()):
                    writer.writerow(existing_data[symbol])
            
            logger.debug(f"Saved earnings date for {symbol} to {EARNINGS_CALENDAR_PATH}")
    
    except Exception as e:
        logger.debug(f"Could not save earnings to CSV: {e}")


def _get_earnings_from_calendar():
    """Load the earnings calendar once and cache it."""
    if not hasattr(_get_earnings_from_calendar, 'calendar'):
        _get_earnings_from_calendar.calendar = load_earnings_calendar()
    return _get_earnings_from_calendar.calendar


def get_earnings_dates(symbol, use_cache=True):
    """
    Fetch upcoming earnings/result dates for a stock.
    
    Tries multiple sources in order:
    1. Check in-memory cache
    2. Try Breeze API (if available) - PREFERRED FOR NSE STOCKS
    3. Check local CSV calendar file (event_calendar.csv) - recommended
    4. Try yfinance API as fallback
    
    Args:
        symbol: Stock symbol (e.g., 'SBIN', 'RELIANCE')
        use_cache: Use cached data if available
    
    Returns:
        {
            'next_earnings': datetime or None,
            'days_until': int or None,
            'source': 'cache', 'breeze', 'csv', 'yfinance', 'not_found', or 'error'
        }
    """
    # Check in-memory cache first
    if use_cache and symbol in EARNINGS_CACHE:
        cached_data = EARNINGS_CACHE[symbol]
        if not _is_cache_stale(cached_data['fetch_time']):
            return {
                'next_earnings': cached_data['next_earnings'],
                'days_until': cached_data['days_until'],
                'source': 'cache'
            }
    
    # 1. Try Breeze API first (best for NSE stocks)
    breeze_earnings = get_earnings_from_breeze(symbol)
    if breeze_earnings:
        today = datetime.now()
        days_until = (breeze_earnings - today).days
        
        result = {
            'next_earnings': breeze_earnings,
            'days_until': days_until,
            'source': 'breeze'
        }
        
        # Cache the result
        EARNINGS_CACHE[symbol] = {
            'next_earnings': breeze_earnings,
            'days_until': days_until,
            'fetch_time': datetime.now()
        }
        
        # Save to CSV for future use (avoid repeated API calls)
        save_earnings_to_csv(symbol, breeze_earnings, 'Results')
        
        return result
    
    # 2. Try local CSV calendar (preferred - user-maintained)
    calendar = _get_earnings_from_calendar()
    if symbol in calendar:
        earnings_date = calendar[symbol]['date']
        today = datetime.now()
        days_until = (earnings_date - today).days
        
        result = {
            'next_earnings': earnings_date,
            'days_until': days_until,
            'source': 'csv'
        }
        
        # Cache the result
        EARNINGS_CACHE[symbol] = {
            'next_earnings': earnings_date,
            'days_until': days_until,
            'fetch_time': datetime.now()
        }
        
        return result
    
    # 3. Try yfinance API as fallback
    try:
        # Try multiple symbol formats for NSE stocks
        ticker_symbols = [symbol]
        
        # Add .NS variant if not already present
        if '.NS' not in symbol and symbol not in ['NIFTY', 'BANKNIFTY']:
            ticker_symbols.append(f"{symbol}.NS")
        
        # Try each variant
        for ticker_symbol in ticker_symbols:
            try:
                # Fetch ticker with timeout and suppress warnings
                with warnings.catch_warnings():
                    warnings.simplefilter("ignore")
                    ticker = yf.Ticker(ticker_symbol)
                
                # Try to get earnings dates with warning suppression
                with warnings.catch_warnings():
                    warnings.simplefilter("ignore")
                    earnings_df = None
                    if hasattr(ticker, 'earnings_dates') and ticker.earnings_dates is not None:
                        earnings_df = ticker.earnings_dates
                    
                    if earnings_df is not None and not earnings_df.empty:
                        # Get the first (earliest) upcoming earnings date
                        first_earnings_date = earnings_df.index[0]
                        
                        # Convert to datetime if needed
                        if hasattr(first_earnings_date, 'to_pydatetime'):
                            first_earnings_date = first_earnings_date.to_pydatetime()
                        
                        today = datetime.now()
                        days_until = (first_earnings_date - today).days
                        
                        # Only consider if within next 6 months (180 days)
                        if days_until > -30 and days_until <= 180:  # Allow past 30 days (recent events)
                            result = {
                                'next_earnings': first_earnings_date,
                                'days_until': days_until,
                                'source': 'yfinance'
                            }
                            
                            # Cache the result
                            EARNINGS_CACHE[symbol] = {
                                'next_earnings': first_earnings_date,
                                'days_until': days_until,
                                'fetch_time': datetime.now()
                            }
                            _save_persistent_cache()
                            
                            # Save to CSV for future use (avoid repeated API calls)
                            save_earnings_to_csv(symbol, first_earnings_date, 'Earnings')
                            
                            return result
            except Exception as e:
                logger.debug(f"Could not fetch earnings for {ticker_symbol}: {str(e)}")
                continue
        
        # No earnings data found - cache this result to avoid repeated API calls
        EARNINGS_CACHE[symbol] = {
            'next_earnings': None,
            'days_until': None,
            'fetch_time': datetime.now()
        }
        _save_persistent_cache()
        
        return {
            'next_earnings': None,
            'days_until': None,
            'source': 'not_found'
        }
    
    except Exception as e:
        logger.debug(f"Could not fetch earnings for {symbol}: {str(e)}")
        # Also cache error results to avoid repeated failed API calls
        EARNINGS_CACHE[symbol] = {
            'next_earnings': None,
            'days_until': None,
            'fetch_time': datetime.now()
        }
        _save_persistent_cache()
        
        return {
            'next_earnings': None,
            'days_until': None,
            'source': 'error'
        }


def get_days_until_event(symbol, use_cache=True):
    """
    Convenience function: get only days until next event.
    
    Returns:
        int: Days until earnings (negative = past event), or None if not available
    """
    data = get_earnings_dates(symbol, use_cache)
    return data.get('days_until')


def get_event_risk_score(days_until_event):
    """
    Convert days until event into a risk score (0-1).
    
    Rationale:
    - 0-7 days to event: HIGH RISK = 0.1 (avoid selling premium)
    - 7-30 days: MEDIUM RISK = 0.4-0.7
    - 30-60 days: LOW RISK = 0.8-0.9
    - 60+ days: NO RISK = 1.0 (safe to sell)
    - Recent past event (within 15 days): ELEVATED = 0.6
    
    Args:
        days_until_event: Integer days until next earnings
    
    Returns:
        float: Risk score 0-1 (higher = lower risk for theta selling)
    """
    if days_until_event is None:
        return 0.9  # Default to "probably safe"
    
    if days_until_event < 0:
        # Past event
        days_since = abs(days_until_event)
        if days_since <= 15:
            return 0.6  # Recently happened - still elevated risk
        else:
            return 1.0  # Enough time since last event
    
    elif days_until_event < 7:
        return 0.1  # Very close - high risk
    elif days_until_event < 14:
        return 0.3
    elif days_until_event < 30:
        return 0.5
    elif days_until_event < 60:
        return 0.75
    else:
        return 1.0  # Safe to sell


def clear_cache():
    """Clear earnings date cache."""
    EARNINGS_CACHE.clear()
    logger.info("Earnings calendar cache cleared")


# Test the module
if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)
    
    # Test symbols
    test_symbols = ['SBIN', 'RELIANCE', 'HDFCBANK', 'TCS', 'INFY']
    
    print("Testing Event Calendar Module:")
    print("-" * 80)
    
    for symbol in test_symbols:
        print(f"\n{symbol}:")
        data = get_earnings_dates(symbol)
        print(f"  Next Earnings: {data['next_earnings']}")
        print(f"  Days Until: {data['days_until']}")
        print(f"  Source: {data['source']}")
        
        if data['days_until'] is not None:
            risk = get_event_risk_score(data['days_until'])
            print(f"  Event Risk Score: {risk:.2f}")
