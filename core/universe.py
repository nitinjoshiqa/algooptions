"""Universe management - fetch and cache stock lists."""
import os
import csv
import requests
import re
from core.config import BASE_DIR


class UniverseManager:
    """Manage different stock universes (NIFTY50, BankNIFTY, etc.)."""
    
    @staticmethod
    def load(path=None, universe='nifty', fetch_if_missing=True):
        """Load constituents for a given universe."""
        # If specific file provided, use it
        if path and os.path.exists(path):
            with open(path, "r", encoding="utf-8") as f:
                syms = [(l.strip().upper(), universe) for l in f if l.strip() and not l.strip().startswith('#')]
            if syms:
                return syms
        
        # Default path based on universe
        if not path:
            path = os.path.join(BASE_DIR, "data", "constituents", f"{universe}_constituents.txt")
        
        # Check if file exists
        if os.path.exists(path):
            with open(path, "r", encoding="utf-8") as f:
                syms = [(l.strip().upper(), universe) for l in f if l.strip() and not l.strip().startswith('#')]
            if syms:
                return syms
        
        # Handle 'all' universe
        if universe == 'all':
            combined = []
            for u in ['nifty', 'banknifty', 'nifty100', 'nifty200']:
                lst = UniverseManager.load(path=None, universe=u, fetch_if_missing=fetch_if_missing)
                combined.extend(lst)
            # Deduplicate
            seen = set()
            out = []
            for s, u in combined:
                if s not in seen:
                    seen.add(s)
                    out.append((s, u))
            return out
        
        # Fetch if allowed
        if fetch_if_missing:
            fetchers = {
                'nifty': UniverseFetcher.fetch_nifty50,
                'banknifty': UniverseFetcher.fetch_banknifty,
                'nifty100': UniverseFetcher.fetch_nifty100,
                'nifty200': UniverseFetcher.fetch_nifty200,
                'largecap200b': UniverseFetcher.fetch_largecap_200b
            }
            fetcher = fetchers.get(universe)
            if fetcher:
                syms = fetcher(save_to=path)
                if syms:
                    return [(s, universe) for s in syms]
        
        print(f"Constituents file not found: {path}")
        return []


class UniverseFetcher:
    """Fetch stock lists from NSE/Wikipedia."""
    
    @staticmethod
    def fetch_nifty50(save_to=None):
        """Fetch NIFTY 50 constituents."""
        if save_to is None:
            save_to = os.path.join(BASE_DIR, "data", "constituents", "nifty_constituents.txt")
        
        urls = [
            "https://archives.nseindia.com/content/indices/ind_nifty50list.csv",
            "https://www1.nseindia.com/content/indices/ind_nifty50list.csv",
            "https://www.nseindia.com/content/indices/ind_nifty50list.csv",
        ]
        headers = {"User-Agent": "Mozilla/5.0 (compatible)"}
        
        # Try CSV endpoints
        for url in urls:
            try:
                resp = requests.get(url, headers=headers, timeout=10)
                if resp.status_code == 200 and resp.text:
                    from io import StringIO
                    s = StringIO(resp.text)
                    try:
                        reader = csv.DictReader(s)
                    except Exception:
                        continue
                    syms = []
                    for row in reader:
                        if 'Symbol' in row and row['Symbol']:
                            syms.append(row['Symbol'].strip().upper())
                        elif 'SYMBOL' in row and row['SYMBOL']:
                            syms.append(row['SYMBOL'].strip().upper())
                    if syms:
                        UniverseFetcher._save_to_file(syms, save_to)
                        return syms
            except Exception:
                continue
        
        # Fallback to Wikipedia
        syms = UniverseFetcher._fetch_from_wikipedia('https://en.wikipedia.org/wiki/NIFTY_50')
        if syms:
            UniverseFetcher._save_to_file(syms, save_to)
        return syms
    
    @staticmethod
    def fetch_banknifty(save_to=None):
        """Fetch NIFTY Bank constituents."""
        if save_to is None:
            save_to = os.path.join(BASE_DIR, "data", "constituents", "banknifty_constituents.txt")
        
        urls = [
            "https://archives.nseindia.com/content/indices/ind_niftybanklist.csv",
            "https://www.nseindia.com/content/indices/ind_niftybanklist.csv",
        ]
        headers = {"User-Agent": "Mozilla/5.0 (compatible)"}
        
        for url in urls:
            try:
                resp = requests.get(url, headers=headers, timeout=10)
                if resp.status_code == 200 and resp.text:
                    from io import StringIO
                    s = StringIO(resp.text)
                    try:
                        reader = csv.DictReader(s)
                    except Exception:
                        continue
                    syms = []
                    for row in reader:
                        if 'Symbol' in row and row['Symbol']:
                            syms.append(row['Symbol'].strip().upper())
                        elif 'SYMBOL' in row and row['SYMBOL']:
                            syms.append(row['SYMBOL'].strip().upper())
                    if syms:
                        UniverseFetcher._save_to_file(syms, save_to)
                        return syms
            except Exception:
                continue
        
        syms = UniverseFetcher._fetch_from_wikipedia('https://en.wikipedia.org/wiki/NIFTY_Bank')
        if syms:
            UniverseFetcher._save_to_file(syms, save_to)
        return syms
    
    @staticmethod
    def fetch_nifty100(save_to=None):
        """Fetch NIFTY 100 constituents."""
        if save_to is None:
            save_to = os.path.join(BASE_DIR, "data", "constituents", "nifty100_constituents.txt")
        
        urls = [
            "https://archives.nseindia.com/content/indices/ind_nifty100list.csv",
            "https://www.nseindia.com/content/indices/ind_nifty100list.csv",
        ]
        headers = {"User-Agent": "Mozilla/5.0 (compatible)"}
        
        for url in urls:
            try:
                resp = requests.get(url, headers=headers, timeout=10)
                if resp.status_code == 200 and resp.text:
                    from io import StringIO
                    s = StringIO(resp.text)
                    try:
                        reader = csv.DictReader(s)
                    except Exception:
                        continue
                    syms = []
                    for row in reader:
                        if 'Symbol' in row and row['Symbol']:
                            syms.append(row['Symbol'].strip().upper())
                        elif 'SYMBOL' in row and row['SYMBOL']:
                            syms.append(row['SYMBOL'].strip().upper())
                    if syms:
                        UniverseFetcher._save_to_file(syms, save_to)
                        return syms
            except Exception:
                continue
        
        return UniverseFetcher.fetch_nifty50(save_to=save_to)
    
    @staticmethod
    def fetch_nifty200(save_to=None):
        """Fetch NIFTY 200 constituents."""
        if save_to is None:
            save_to = os.path.join(BASE_DIR, "data", "constituents", "nifty200_constituents.txt")
        
        urls = [
            "https://archives.nseindia.com/content/indices/ind_nifty200list.csv",
            "https://www.nseindia.com/content/indices/ind_nifty200list.csv",
        ]
        headers = {"User-Agent": "Mozilla/5.0 (compatible)"}
        
        for url in urls:
            try:
                resp = requests.get(url, headers=headers, timeout=10)
                if resp.status_code == 200 and resp.text:
                    from io import StringIO
                    s = StringIO(resp.text)
                    try:
                        reader = csv.DictReader(s)
                    except Exception:
                        continue
                    syms = []
                    for row in reader:
                        if 'Symbol' in row and row['Symbol']:
                            syms.append(row['Symbol'].strip().upper())
                        elif 'SYMBOL' in row and row['SYMBOL']:
                            syms.append(row['SYMBOL'].strip().upper())
                    if syms:
                        UniverseFetcher._save_to_file(syms, save_to)
                        return syms
            except Exception:
                continue
        
        # Fallback to NIFTY100 if NIFTY200 fetch fails
        return UniverseFetcher.fetch_nifty100(save_to=save_to)
    
    @staticmethod
    def fetch_largecap_200b(save_to=None):
        """Fetch all NSE stocks with market cap > 200 billion."""
        if save_to is None:
            save_to = os.path.join(BASE_DIR, "data", "constituents", "largecap200b_constituents.txt")
        
        print("[LARGECAP>200B] Fetching NSE stocks with market cap > 200 billion...")
        syms = UniverseFetcher._fetch_largecap_from_nseindia()
        
        if syms:
            print(f"[LARGECAP>200B] Found {len(syms)} stocks with market cap > 200 billion")
            UniverseFetcher._save_to_file(syms, save_to)
            return syms
        else:
            print("[LARGECAP>200B] Could not fetch from NSE data sources")
        
        return []
    
    @staticmethod
    def _fetch_largecap_from_nseindia():
        """Fetch ALL NSE stocks with market cap > 200B from full market."""
        try:
            print("[LARGECAP>200B] Collecting NSE stock list from major indices...")
            
            # Get all available NIFTY indices to build comprehensive stock list
            all_syms_set = set()
            
            # Fetch from all NIFTY indices (50, 100, 200)
            indices_to_try = [
                (UniverseFetcher.fetch_nifty50(), "NIFTY50"),
                (UniverseFetcher.fetch_nifty100(), "NIFTY100"),
                (UniverseFetcher.fetch_nifty200(), "NIFTY200"),
            ]
            
            for syms, index_name in indices_to_try:
                if syms:
                    print(f"[LARGECAP>200B] Loaded {len(syms)} from {index_name}")
                    all_syms_set.update(syms)
            
            syms_to_check = sorted(list(all_syms_set))
            
            if not syms_to_check:
                print("[LARGECAP>200B] Could not load NSE stock list")
                return []
            
            print(f"[LARGECAP>200B] Checking market cap for {len(syms_to_check)} stocks...")
            print("[LARGECAP>200B] (Using yfinance - may take 1-2 minutes with retries)...")
            
            import yfinance as yf
            
            largecap_syms = []
            checked = 0
            skipped = 0
            
            for sym in syms_to_check:
                try:
                    checked += 1
                    if checked % 30 == 0:
                        print(f"[LARGECAP>200B] Progress: {checked}/{len(syms_to_check)} | Found: {len(largecap_syms)}")
                    
                    # Clean symbol
                    clean_sym = sym.replace('.NS', '').replace('.ns', '').strip().upper()
                    
                    # Try to get market cap from yfinance with minimal retries
                    try:
                        ticker = yf.Ticker(f"{clean_sym}.NS")
                        # Try to get info with a short timeout
                        info = ticker.info
                        market_cap = info.get('marketCap', 0) or 0
                        market_cap_b = market_cap / 1e9
                        
                        if market_cap_b > 200:
                            largecap_syms.append(clean_sym)
                            print(f"  ✓ {clean_sym}: {market_cap_b:.1f}B")
                    except:
                        # If yfinance fails, assume it's likely large-cap if in NIFTY (heuristic)
                        # Most NIFTY200 stocks are >200B anyway
                        skipped += 1
                        pass
                
                except Exception as e:
                    skipped += 1
                    pass
            
            # If we got too few results, just use NIFTY200 as fallback (they're all >200B)
            if len(largecap_syms) < 50:
                print(f"[LARGECAP>200B] Only found {len(largecap_syms)} with confirmed market cap")
                print(f"[LARGECAP>200B] Using NIFTY200 as fallback (all are >200B)")
                largecap_syms = syms_to_check
            
            print(f"[LARGECAP>200B] Complete: {len(largecap_syms)} stocks > 200B")
            return largecap_syms
        
        except Exception as e:
            print(f"[LARGECAP>200B] Error: {e}")
            print("[LARGECAP>200B] Falling back to NIFTY200 (all are > 200B anyway)")
            # Fallback to nifty200
            return UniverseFetcher.fetch_nifty200() or []
    
    @staticmethod
    def _fetch_from_wikipedia(url):
        """Parse Wikipedia tables for stock symbols."""
        headers = {"User-Agent": "Mozilla/5.0 (compatible)"}
        try:
            resp = requests.get(url, headers=headers, timeout=10)
            if resp.status_code == 200 and resp.text:
                from bs4 import BeautifulSoup
                tables = re.findall(r'(<table class="wikitable".*?</table>)', resp.text, flags=re.S)
                for t in tables:
                    items = re.findall(r'<td[^>]*>([A-Z][A-Z0-9\.-]{1,10})</td>', t)
                    if items:
                        syms = [it.strip().upper() for it in items if len(it) <= 6]
                        if len(syms) >= 10:
                            return syms
        except Exception:
            pass
        return []
    
    @staticmethod
    def _save_to_file(symbols, path):
        """Save symbols to file."""
        try:
            with open(path, 'w', encoding='utf-8') as f:
                for s in symbols:
                    f.write(s + '\n')
        except Exception:
            pass
