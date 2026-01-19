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
            path = os.path.join(BASE_DIR, f"{universe}_constituents.txt")
        
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
                'nifty200': UniverseFetcher.fetch_nifty200
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
            save_to = os.path.join(BASE_DIR, "nifty_constituents.txt")
        
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
            save_to = os.path.join(BASE_DIR, "banknifty_constituents.txt")
        
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
            save_to = os.path.join(BASE_DIR, "nifty100_constituents.txt")
        
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
        """Fetch NIFTY 200 constituents (fallback to NIFTY100)."""
        if save_to is None:
            save_to = os.path.join(BASE_DIR, "nifty200_constituents.txt")
        return UniverseFetcher.fetch_nifty100(save_to=save_to)
    
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
