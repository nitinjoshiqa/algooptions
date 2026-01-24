"""Data providers: Breeze API and yFinance.

CACHING STRATEGY (Intraday signals decay):
    - Intraday (5m, 15m): NEVER cached - always fetch fresh
    - Daily (1d): Cached 24h - doesn't change intraday
    - Prices: Cached 60s - refreshed frequently
    
This ensures intraday signals are always current while keeping 
daily data fast. Fresh intraday every run = accurate signals.
"""
# -*- coding: utf-8 -*-
from datetime import datetime, timedelta
import os
import sys
import time
import random
import json
import logging
import threading
import io

# Ensure stdout handles Unicode properly on Windows
if sys.platform == 'win32':
    # For Windows, use UTF-8 encoding for console
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

# Suppress yfinance verbose logging
logging.getLogger('yfinance').setLevel(logging.ERROR)
logging.getLogger('urllib3').setLevel(logging.ERROR)

# Try to import yfinance
try:
    import yfinance as yf
    HAVE_YFINANCE = True
    # yfinance requires curl_cffi session, or None (let it handle)
    _yf_session = None
    def get_yf_session():
        # Return None to let yfinance handle session creation
        return None
except Exception:
    HAVE_YFINANCE = False
    def get_yf_session():
        return None

# Try to import nsepython for direct NSE data
try:
    import nsepython
    HAVE_NSEPYTHON = True
except Exception:
    HAVE_NSEPYTHON = False

from utils.breeze_api import get_breeze_instance
from core.config import EXCHANGE, PRODUCT

# Rate limiting configuration
_last_yf_request_time = 0
_request_delay = 1.0  # 1 second between requests to avoid rate limiting
_rate_limit_backoff = 10  # Start with 10 second backoff
_rate_limit_max_backoff = 300  # Max 5 minutes between attempts

# Disk cache for candles (persistent across runs)
_candle_cache_dir = os.path.join(os.path.dirname(__file__), '.candle_cache')
os.makedirs(_candle_cache_dir, exist_ok=True)
_candle_cache_ttl = 86400  # 24 hours for disk cache (1 day = intraday data changes daily)

def _get_candle_cache_path(symbol, interval):
    """Get disk cache file path for candles."""
    return os.path.join(_candle_cache_dir, f"{symbol}_{interval}.json")

def _load_candles_from_disk(symbol, interval, ttl_hours=2):
    """Load candles from disk cache if valid.
    
    Args:
        symbol: Stock symbol
        interval: Candle interval ('5minute', '15minute', '1day', etc.)
        ttl_hours: Cache is valid if modified within this many hours
    
    Returns:
        List of candles if cache valid, None otherwise
        
    NOTE: Intraday data (5m, 15m) is NOT cached - always fetched fresh
          Daily data (1d) uses 24h cache since it doesn't change intraday
    """
    # IMPORTANT: Don't cache intraday data - signals decay, need fresh data every run
    if '5minute' in interval or '15minute' in interval or 'minute' in interval:
        return None  # Always fetch fresh intraday
    
    # Cache only daily and longer intervals
    cache_path = _get_candle_cache_path(symbol, interval)
    if os.path.exists(cache_path):
        try:
            stat = os.stat(cache_path)
            ttl_seconds = ttl_hours * 3600
            if time.time() - stat.st_mtime < ttl_seconds:
                with open(cache_path, 'r') as f:
                    return json.load(f)
        except Exception:
            pass
    return None

def _save_candles_to_disk(symbol, interval, candles):
    """Save candles to disk cache (intraday excluded)."""
    # Don't cache intraday - always fresh
    if '5minute' in interval or '15minute' in interval or 'minute' in interval:
        return  # Skip caching for intraday
    
    cache_path = _get_candle_cache_path(symbol, interval)
    try:
        with open(cache_path, 'w') as f:
            json.dump(candles, f)
    except Exception:
        pass

_rate_limit_max_backoff = 300  # Max 5 minutes between attempts

# Cache for prices and candles to avoid repeated requests
_price_cache = {}  # symbol -> (price, timestamp)
_cache_ttl = 60  # Cache valid for 60 seconds

def _get_cache_key(symbol, data_type='price'):
    """Generate cache key."""
    return f"{data_type}:{symbol}"

def _is_cache_valid(cache_key):
    """Check if cache entry is still valid."""
    if cache_key not in _price_cache:
        return False
    price, timestamp = _price_cache[cache_key]
    return (time.time() - timestamp) < _cache_ttl

def _rate_limit_sleep():
    """Sleep to respect rate limits."""
    global _last_yf_request_time
    elapsed = time.time() - _last_yf_request_time
    if elapsed < _request_delay:
        time.sleep(_request_delay - elapsed)
    _last_yf_request_time = time.time()


class DataProvider:
    """Abstract base class for data providers."""
    
    def get_spot_price(self, symbol):
        raise NotImplementedError
    
    def get_candles(self, symbol, interval, max_bars):
        raise NotImplementedError


class BreezeProvider(DataProvider):
    """Breeze API data provider with connection resilience and retry logic."""
    
    def __init__(self):
        self.breeze = get_breeze_instance()
        # Check if we got a real connection or dummy
        self.is_dummy = self.breeze.__class__.__name__ == '_DummyBreeze'
        self._max_retries = 2
        self._retry_backoff = 2  # Exponential backoff multiplier
    
    def _is_breeze_available(self):
        """Quick health check to see if Breeze is responding."""
        try:
            if self.is_dummy:
                return False
            # Try a simple call to verify connection
            # This will fail fast if Breeze is down
            result = self.breeze.get_portfolio_positions()
            return result is not None or isinstance(result, dict)
        except Exception:
            return False
    
    def get_spot_price(self, symbol):
        try:
            if self.is_dummy:
                return None
            
            # Quick availability check
            if not self._is_breeze_available():
                return None
            
            res = self.breeze.get_quotes(
                stock_code=symbol,
                exchange_code=EXCHANGE,
                product_type=PRODUCT
            )
            
            if res and res.get('Status') == 200 and res.get("Success") and len(res["Success"]) > 0:
                try:
                    price = float(res["Success"][0]["ltp"])
                    return price
                except (KeyError, ValueError, TypeError):
                    return None
            
            # Log failures for debugging
            if res and res.get('Status') != 200:
                error = res.get('Error', 'Unknown error')
                # Silently fall through - this is expected when Breeze is not available
                pass
                
        except AttributeError:
            # Breeze not available
            return None
        except Exception:
            # Silently fail - fallback will handle it
            pass
        
        return None
    
    def get_candles(self, symbol, interval="5minute", max_bars=200):
        """Fetch historical candles from Breeze using aggregation for unsupported intervals.
        
        Strategy for 15-minute data (not supported by Breeze):
        - Request 5-minute candles from Breeze (supported)
        - Aggregate 3x 5-minute candles into 15-minute candles
        - This gives same data quality as native 15-min without API limitation
        """
        try:
            breeze = get_breeze_instance()
            
            # Check if Breeze is actually available (not dummy)
            if self.is_dummy:
                return [], None
            
            # Breeze API actual support (tested 2026-01-24):
            breeze_supported = ['1minute', '5minute', '30minute']
            
            # Validate interval before API call
            valid_intervals = ['1minute', '5minute', '15minute', '30minute', '1hour', '1day', '1week']
            if interval not in valid_intervals:
                print(f"[WARN] {symbol}: Invalid interval '{interval}'")
                return [], None
            
            # Handle 15-minute specially: fetch 5-min and aggregate
            request_interval = interval
            needs_aggregation = False
            
            if interval == '15minute' and interval not in breeze_supported:
                # Strategy: Get 5-min candles and aggregate them (3x5min = 15min)
                # But if 5min also unavailable from Breeze, just fall back to yFinance for native 15min
                request_interval = '5minute'
                needs_aggregation = True
                # Need 3x more bars to aggregate
                max_bars = max_bars * 3
            
            # Check if Breeze supports the actual request interval
            if request_interval not in breeze_supported:
                # Breeze doesn't support this interval - silently fall back to NSE/yFinance
                return [], None  # Fall back to NSE/yFinance (no debug message)
            
            # Dynamic lookback based on interval (more data = better indicators)
            if 'minute' in request_interval:
                days_back = 10  # Intraday: 10 days = ~240-480 candles
            elif 'hour' in request_interval:
                days_back = 30  # Hourly: 30 days = ~720 candles
            else:
                days_back = 100  # Daily+: 100 days = full history
            
            end_time = datetime.now()
            start_time = end_time - timedelta(days=days_back)
            
            # Use Breeze v1 API (proven to work with 1min, 5min, 30min)
            # v1 API uses simple date format (YYYY-MM-DD)
            try:
                res = _call_with_timeout(
                    breeze.get_historical_data,
                    kwargs={
                        'interval': request_interval,
                        'from_date': start_time.strftime("%Y-%m-%d"),
                        'to_date': end_time.strftime("%Y-%m-%d"),
                        'stock_code': symbol,
                        'exchange_code': EXCHANGE,
                        'product_type': PRODUCT
                    },
                    timeout=5
                )
                api_version = "v1"
            except Exception as e:
                print(f"[WARN] {symbol}: Breeze API v1 error: {str(e)[:100]}")
                return [], None
            
            # Validate response
            if not res:
                print(f"[WARN] {symbol}: No response from Breeze API {api_version} (timeout or connection issue)")
                return [], None
            
            # Check API status
            if res.get('Status') != 200:
                error_msg = res.get('Error', 'Unknown error')
                print(f"[WARN] {symbol}: Breeze API {api_version} error {res.get('Status')}: {error_msg}")
                return [], None
            
            # Extract candles
            raw = res.get("Success", [])
            if raw is None:
                # Breeze returns None when "No Data Found" instead of empty list
                raw = []
            
            if not raw:
                # If we were trying to aggregate 15min from 5min and it failed, let fallback handle it
                if needs_aggregation:
                    print(f"[DEBUG] {symbol}: No 5-min candles from Breeze, will fall back to yFinance for 15min")
                else:
                    print(f"[DEBUG] {symbol}: No candles returned for interval {interval}")
                return [], None
            
            # Parse candles with error handling
            candles = []
            for c in raw:
                try:
                    dt = c.get('datetime') or c.get('date') or ''
                    o = float(c.get('open', 0))
                    h = float(c.get('high', 0))
                    l = float(c.get('low', 0))
                    cc = float(c.get('close', 0))
                    v_raw = c.get('volume', c.get('Volume', 0))
                    try:
                        v = int(v_raw) if v_raw is not None else 0
                    except (ValueError, TypeError):
                        v = 0
                    
                    candles.append({
                        'datetime': dt,
                        'open': o,
                        'high': h,
                        'low': l,
                        'close': cc,
                        'volume': v
                    })
                except (KeyError, ValueError, TypeError) as e:
                    # Skip malformed candles
                    continue
            
            if not candles:
                print(f"[WARN] {symbol}: No valid candles after parsing")
                return [], None
            
            # Sort by datetime and return
            try:
                candles_sorted = sorted(candles, key=lambda c: c.get('datetime', ''))
            except Exception:
                candles_sorted = candles
            
            # Apply aggregation if needed (15-min from 5-min)
            if needs_aggregation and candles_sorted:
                from indicators.candle_aggregator import create_15min_from_5min
                candles_sorted = create_15min_from_5min(candles_sorted)
                try:
                    print(f"[OK] {symbol}: Aggregated {len(candles)} 5-min -> {len(candles_sorted)} 15-min")
                except (UnicodeEncodeError, UnicodeDecodeError):
                    print(f"[OK] {symbol}: Aggregated 5m to 15m: {len(candles_sorted)} bars")
            
            # Success!
            result = candles_sorted[-max_bars:]
            try:
                print(f"[OK] {symbol}: Got {len(result)} candles from Breeze {api_version} ({interval})")
            except (UnicodeEncodeError, UnicodeDecodeError):
                print(f"[OK] {symbol}: Got {len(result)} candles from Breeze")
            return result, 'breeze'
            
        except TimeoutError:
            try:
                print(f"[TIMEOUT] {symbol}: Breeze API timeout after 5 seconds")
            except (UnicodeEncodeError, UnicodeDecodeError):
                print(f"[TIMEOUT] {symbol}: API timeout")
            return [], None
        except Exception as e:
            try:
                err_msg = str(e)[:80]
                # Replace unicode chars that cause encoding issues
                err_msg = err_msg.replace('\u2192', '->').replace('\u2190', '<-').replace('\u2191', '^').replace('\u2193', 'v')
                print(f"[ERROR] {symbol}: Breeze exception: {type(e).__name__}: {err_msg}")
            except (UnicodeEncodeError, UnicodeDecodeError):
                print(f"[ERROR] {symbol}: Breeze API failed")
            return [], None


def _call_with_timeout(func, args=(), kwargs=None, timeout=10):
    """Call function with timeout (for NSE API which can hang)."""
    if kwargs is None:
        kwargs = {}
    
    result = [None]
    exception = [None]
    
    def wrapper():
        try:
            result[0] = func(*args, **kwargs)
        except Exception as e:
            exception[0] = e
    
    thread = threading.Thread(target=wrapper, daemon=True)
    thread.start()
    thread.join(timeout=timeout)
    
    if exception[0]:
        raise exception[0]
    return result[0]


class NSEProvider(DataProvider):
    """Direct NSE API provider using nsepython library with timeout protection."""
    
    def __init__(self):
        if not HAVE_NSEPYTHON:
            raise ImportError("nsepython not available")
    
    def get_spot_price(self, symbol):
        """Get spot price directly from NSE with timeout."""
        try:
            # Call with 5 second timeout to fail fast if NSE is slow
            quote = _call_with_timeout(nsepython.nse_quote, args=('EQ', symbol), timeout=5)
            
            if quote and isinstance(quote, dict):
                # Extract price from various possible keys
                for key in ['lastPrice', 'last_price', 'close', 'pricebandupper', 'price', 'ltp']:
                    if key in quote:
                        try:
                            price = float(quote[key])
                            if price > 0:
                                return price
                        except (ValueError, TypeError):
                            pass
            
            return None
        
        except Exception:
            # Timeout, connection error, or NSE unavailable
            return None
    
    def get_candles(self, symbol, interval="5minute", max_bars=200):
        """Get historical data directly from NSE with timeout protection."""
        try:
            # Wrap NSE call with timeout to prevent hanging (5 second limit - fail fast)
            history = _call_with_timeout(
                nsepython.equity_history,
                args=(symbol, 30),
                timeout=5
            )
            
            if history is not None and not history.empty:
                candles = []
                
                # equity_history returns DataFrame with columns: Date, CH_OPENING_PRICE, CH_TRADE_HIGH_PRICE, 
                # CH_TRADE_LOW_PRICE, CH_CLOSING_PRICE, CH_TOT_TRADED_VOL, CH_TOT_TRADED_VAL
                
                for idx, row in history.iterrows():
                    try:
                        candle = {
                            'datetime': str(row.get('Date', idx)) if 'Date' in row else str(idx),
                            'open': float(row.get('CH_OPENING_PRICE', row.get('open', 0))),
                            'high': float(row.get('CH_TRADE_HIGH_PRICE', row.get('high', 0))),
                            'low': float(row.get('CH_TRADE_LOW_PRICE', row.get('low', 0))),
                            'close': float(row.get('CH_CLOSING_PRICE', row.get('close', 0))),
                            'volume': int(row.get('CH_TOT_TRADED_VOL', row.get('volume', 0))),
                        }
                        candles.append(candle)
                    except Exception:
                        continue
                
                if candles:
                    # Return last max_bars candles
                    return candles[-max_bars:], 'nse'
            
            return [], None
        
        except Exception:
            # Timeout, connection error, or NSE unavailable
            return [], None


class YFinanceProvider(DataProvider):
    """yFinance data provider with rate limiting, caching, and retry logic."""
    
    def __init__(self):
        if not HAVE_YFINANCE:
            raise ImportError("yfinance not available")
    
    def _get_with_retry(self, symbol, max_retries=1):
        """Fetch from yfinance with retry ONLY on rate limiting.
        
        For non-rate-limit errors (stock not found), fail fast without retrying.
        Only retry on 429/rate limit errors to avoid wasting API calls on non-existent stocks.
        """
        backoff = _rate_limit_backoff
        last_error = None
        is_rate_limit_error = False
        
        for attempt in range(max_retries + 1):
            try:
                _rate_limit_sleep()
                t = yf.Ticker(symbol)
                return t
            except Exception as e:
                last_error = e
                # Check if this is a rate limit error (ONLY error type we retry on)
                error_str = str(e).lower()
                if 'rate' in error_str or 'too many' in error_str or '429' in error_str:
                    is_rate_limit_error = True
                    if attempt < max_retries:
                        wait_time = min(backoff + random.uniform(0, 2), _rate_limit_max_backoff)
                        print(f"    Rate limited on {symbol}. Waiting {wait_time:.1f}s before retry (attempt {attempt+1}/{max_retries})...")
                        time.sleep(wait_time)
                        backoff = min(backoff * 2.0, _rate_limit_max_backoff)
                        continue
                # For non-rate-limit errors (stock doesn't exist, bad symbol, etc): fail immediately
                # Don't waste retries on stocks that will never work
                break
        
        raise last_error
    
    def get_spot_price(self, symbol):
        # Check cache first
        cache_key = _get_cache_key(symbol, 'price')
        if _is_cache_valid(cache_key):
            price, _ = _price_cache[cache_key]
            return price
        
        # Build variants - don't add .NS to index tickers (starting with ^)
        if symbol.startswith('^'):
            # Index ticker - use as-is
            variants = [symbol]
        else:
            # Regular stock - try with .NS suffix first (but avoid double .NS)
            base_symbol = symbol.rstrip('.NS') if symbol.endswith('.NS') else symbol
            variants = [base_symbol + '.NS', base_symbol, base_symbol.replace('-', ''), base_symbol.replace('.', '') + '.NS']
        
        for sym in variants:
            try:
                t = self._get_with_retry(sym, max_retries=1)
                try:
                    info = t.fast_info if hasattr(t, 'fast_info') else {}
                    if info:
                        p = info.get('lastPrice') or info.get('last_price') or info.get('previousClose')
                        if p:
                            price = float(p)
                            _price_cache[cache_key] = (price, time.time())
                            return price
                except Exception:
                    pass
                
                df = t.history(period='5d', interval='1d', auto_adjust=False)
                if df is not None and not df.empty:
                    try:
                        price = float(df.iloc[-1]['Close'])
                        _price_cache[cache_key] = (price, time.time())
                        return price
                    except Exception:
                        continue
            except Exception as e:
                # Try next variant
                continue
        return None
    
    def get_candles(self, symbol, interval='5m', max_bars=200):
        # Map interval names
        yf_interval = interval
        if interval in ('5minute', '5min'):
            yf_interval = '5m'
        elif interval in ('15minute', '15min'):
            yf_interval = '15m'
        elif interval in ('1hour', '60min', '1h'):
            yf_interval = '60m'
        elif interval in ('1day', 'daily'):
            yf_interval = '1d'
        
        # Build variants - don't add .NS to index tickers (starting with ^)
        if symbol.startswith('^'):
            # Index ticker - use as-is
            variants = [symbol]
        else:
            # Regular stock - try with .NS suffix first (but avoid double .NS)
            base_symbol = symbol.rstrip('.NS') if symbol.endswith('.NS') else symbol
            variants = [base_symbol + '.NS', base_symbol, base_symbol.replace('-', ''), base_symbol.replace('.', '') + '.NS']
        
        for sym in variants:
            try:
                t = self._get_with_retry(sym, max_retries=1)
                period = '5d' if yf_interval.endswith('m') else '30d'
                df = t.history(period=period, interval=yf_interval, auto_adjust=False)
                if df is None or df.empty:
                    continue
                
                candles = []
                for idx, row in df.iterrows():
                    try:
                        dt = idx.to_pydatetime().strftime('%Y-%m-%d %H:%M:%S')
                        o = float(row.get('Open', row.get('open', 0)))
                        h = float(row.get('High', row.get('high', 0)))
                        l = float(row.get('Low', row.get('low', 0)))
                        c = float(row.get('Close', row.get('close', 0)))
                        v = int(row.get('Volume', 0)) if row.get('Volume') is not None else 0
                    except Exception:
                        continue
                    candles.append({'datetime': dt, 'open': o, 'high': h, 'low': l, 'close': c, 'volume': v})
                
                if not candles:
                    continue
                return candles[-max_bars:], 'yfinance'
            except Exception as e:
                # Try next variant
                continue
        return [], None


def get_provider(use_yf=False, force_yf=False):
    """Factory method to get appropriate data provider."""
    if force_yf or (use_yf and HAVE_YFINANCE):
        try:
            return YFinanceProvider()
        except ImportError:
            pass
    return BreezeProvider()


def get_spot_price(symbol, use_yf=False, force_yf=False):
    """Get spot price using appropriate provider fallback chain.
    
    Fallback order:
    1. Breeze (ICICI Direct API) - if not forced to YF
    2. Yahoo Finance (yfinance) - global stock data
    3. Return None if all fail
    
    Note: NSEProvider disabled due to website timeouts. Re-enable when stable.
    """
    
    # If force_yf is set, skip Breeze, go straight to yFinance
    if not force_yf:
        # Try Breeze first
        try:
            provider = BreezeProvider()
            price = provider.get_spot_price(symbol)
            if price is not None:
                return price
        except Exception:
            pass  # Fall through to yFinance
    
    # Try yFinance as fallback or primary (if force_yf)
    if HAVE_YFINANCE:
        try:
            provider = YFinanceProvider()
            price = provider.get_spot_price(symbol)
            if price is not None:
                return price
        except Exception:
            pass
    
    # All providers failed
    return None


def get_intraday_candles_for(symbol, interval="5minute", max_bars=200, use_yf=False, force_yf=False):
    """Fetch candles using enhanced fallback chain with smart caching.
    
    Caching Strategy:
    - Daily intervals (1d, 1day): Cache enabled (2-hour TTL) - stable data
    - Intraday intervals (5m, 15m): ALWAYS FRESH - no caching, real-time from API
    
    Fallback order (for INTRADAY):
    1. Breeze (ICICI Direct API) - limited coverage but primary source
    2. NSE Direct API (nsepython) - with timeout protection
    3. Yahoo Finance (yfinance) - global coverage, rate limited
    4. Return empty list if all fail
    
    Fallback order (for DAILY):
    1. Database cache (2 hours TTL) - persistent, survives restarts
    2. Disk cache (2 hours TTL) - fast, temporary per-process
    3. Breeze/NSE/yFinance (same as intraday)
    
    Note: Intraday intervals require fresh data for accurate entry signals.
    Daily intervals can use cache safely (ATR is stable over hours).
    """
    
    # Determine if this is an intraday or daily interval
    is_intraday = interval.lower() not in ('1day', '1d', '1D', '1DAY', 'daily', 'Daily')
    
    # ONLY use cache for daily/long-term intervals (not 5m, 15m, 1h, etc.)
    if not is_intraday:
        # Check database cache first (persistent, 2 hours TTL - Option B)
        try:
            from core.candle_cache import load_candles_from_db
            cached, source = load_candles_from_db(symbol, interval, max_age_hours=2)
            if cached:
                return cached[-max_bars:], f'{source}_cache'
        except Exception:
            pass  # Fall through if DB not available
        
        # Check disk cache next (2 hours TTL)
        cached = _load_candles_from_disk(symbol, interval, ttl_hours=2)
        if cached:
            return cached[-max_bars:], 'disk_cache'
    
    # If force_yf is set, skip Breeze and NSE, go straight to yFinance
    if not force_yf:
        # Try Breeze first
        try:
            provider = BreezeProvider()
            candles, src = provider.get_candles(symbol, interval, max_bars)
            if candles:
                _save_candles_to_disk(symbol, interval, candles)
                # Also save to database cache (Option B)
                try:
                    from core.candle_cache import save_candles_to_db
                    save_candles_to_db(symbol, interval, candles, source=src)
                except Exception:
                    pass  # Continue even if DB save fails
                return candles, src
        except Exception:
            pass  # Fall through to NSE
        
        # Try NSE Direct API with timeout protection
        if HAVE_NSEPYTHON:
            try:
                provider = NSEProvider()
                candles, src = provider.get_candles(symbol, interval, max_bars)
                if candles:
                    _save_candles_to_disk(symbol, interval, candles)
                    # Also save to database cache
                    try:
                        from core.candle_cache import save_candles_to_db
                        save_candles_to_db(symbol, interval, candles, source=src)
                    except Exception:
                        pass
                    return candles, src
            except Exception:
                pass  # Fall through to yFinance
    
    # Try yFinance as fallback or primary (if force_yf)
    if HAVE_YFINANCE:
        try:
            provider = YFinanceProvider()
            candles, src = provider.get_candles(symbol, interval, max_bars)
            if candles:
                # CACHE yfinance results to disk to avoid repeated API calls
                _save_candles_to_disk(symbol, interval, candles)
                # Also save to database cache
                try:
                    from core.candle_cache import save_candles_to_db
                    save_candles_to_db(symbol, interval, candles, source=src)
                except Exception:
                    pass
                return candles, src
        except Exception:
            pass
    
    # All providers failed
    return [], None
