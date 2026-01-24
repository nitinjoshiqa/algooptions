"""
Symbol Format Manager
Handles different symbol formats for different data providers
- Yahoo Finance: requires .NS suffix for NSE stocks
- Breeze API: works with or without suffix
- File: store clean symbols without suffix
"""

class SymbolFormatter:
    """Convert symbols between formats based on provider"""
    
    NIFTY_PROVIDERS = {
        'yfinance': 'add_ns',
        'breeze': 'keep_clean',
        'icedata': 'add_ns',
        'dataframe': 'keep_clean'
    }
    
    @staticmethod
    def format_symbol(symbol: str, provider: str) -> str:
        """
        Format symbol for specific data provider
        
        Args:
            symbol: Clean symbol (e.g., 'RELIANCE')
            provider: Data source ('yfinance', 'breeze', etc.)
            
        Returns:
            Formatted symbol for the provider
            
        Examples:
            format_symbol('RELIANCE', 'yfinance')  → 'RELIANCE.NS'
            format_symbol('RELIANCE', 'breeze')    → 'RELIANCE'
            format_symbol('RELIANCE.NS', 'yfinance') → 'RELIANCE.NS' (idempotent)
        """
        # Clean first - remove any existing suffix
        clean_symbol = symbol.replace('.NS', '').replace('.BO', '').strip()
        
        if provider == 'yfinance':
            # Yahoo Finance needs .NS suffix for NSE
            return f"{clean_symbol}.NS"
        elif provider in ['breeze', 'breeze_connect']:
            # Breeze API works with clean symbol
            return clean_symbol
        elif provider == 'icedata':
            # IceData needs .NS suffix
            return f"{clean_symbol}.NS"
        elif provider in ['dataframe', 'csv', 'cache']:
            # Internal use - keep clean
            return clean_symbol
        else:
            # Default - try with .NS first, then clean
            return f"{clean_symbol}.NS"
    
    @staticmethod
    def get_symbol_variants(symbol: str, quick_mode: bool = False) -> list:
        """
        Get all symbol variants to try for a stock
        Falls back through formats if primary doesn't work
        
        Args:
            symbol: Clean symbol (e.g., 'RELIANCE')
            quick_mode: If True, try only 2 formats. If False, try 5.
            
        Returns:
            List of symbol variants in order of preference
            
        Examples:
            get_symbol_variants('RELIANCE', quick_mode=True)
            → ['RELIANCE.NS', 'RELIANCE']
            
            get_symbol_variants('RELIANCE', quick_mode=False)
            → ['RELIANCE.NS', 'RELIANCE', 'RELIANCENSR', 'RELIANCE NSE', 'REL']
        """
        # Clean the symbol first
        clean = symbol.replace('.NS', '').replace('.BO', '').strip()
        
        if quick_mode:
            return [
                f"{clean}.NS",      # Yahoo Finance standard
                clean               # Breeze or direct
            ]
        else:
            return [
                f"{clean}.NS",      # Yahoo Finance standard
                clean,              # Breeze or clean format
                clean.replace('-', ''),  # Remove hyphens (some stocks use)
                f"{clean} NSE",     # Space-separated NSE
                clean[:3]           # Last resort - first 3 chars (rare)
            ]


class SymbolResolver:
    """Intelligently resolve symbols across providers"""
    
    def __init__(self, provider: str = 'yfinance', use_cache: bool = True):
        """
        Args:
            provider: Primary data source ('yfinance', 'breeze', etc.)
            use_cache: Cache successful symbol formats
        """
        self.provider = provider
        self.use_cache = use_cache
        self.cache = {}  # symbol → confirmed_format
    
    def load_constituents(self, filename: str) -> list:
        """
        Load stock symbols from file (should be clean, no suffixes)
        
        Args:
            filename: Path to constituent file (e.g., 'nifty500_constituents.txt')
            
        Returns:
            List of clean symbols
        """
        symbols = []
        try:
            with open(filename, 'r') as f:
                for line in f:
                    symbol = line.strip()
                    if symbol:
                        # Store clean, without suffix
                        clean = symbol.replace('.NS', '').replace('.BO', '')
                        symbols.append(clean)
        except FileNotFoundError:
            print(f"File not found: {filename}")
            return []
        
        return symbols
    
    def get_formatted_symbol(self, symbol: str) -> str:
        """
        Get properly formatted symbol for current provider
        
        Args:
            symbol: Clean or any format symbol
            
        Returns:
            Formatted symbol ready for data fetching
        """
        # Check cache first
        if self.use_cache and symbol in self.cache:
            return self.cache[symbol]
        
        formatted = SymbolFormatter.format_symbol(symbol, self.provider)
        
        # Cache it
        if self.use_cache:
            self.cache[symbol] = formatted
        
        return formatted
    
    def get_all_variants(self, symbol: str) -> list:
        """Get fallback variants for trying multiple formats"""
        return SymbolFormatter.get_symbol_variants(symbol, quick_mode=False)


# Integration with existing code
def integrate_with_fetcher():
    """
    Example: How to integrate this with data fetching
    """
    example_code = """
    from symbol_formatter import SymbolResolver
    
    # Old way (in data fetcher):
    for symbol in symbols:
        data = fetch_yfinance(symbol + '.NS')  # Hard-coded suffix
    
    # New way (cleaner):
    resolver = SymbolResolver(provider='yfinance')
    symbols = resolver.load_constituents('nifty500_constituents.txt')
    
    for symbol in symbols:
        formatted = resolver.get_formatted_symbol(symbol)
        data = fetch_yfinance(formatted)  # Auto-formatted
    
    # Even better with fallback:
    for symbol in symbols:
        variants = resolver.get_all_variants(symbol)
        for variant in variants:
            try:
                data = fetch_yfinance(variant)
                resolver.cache[symbol] = variant  # Remember what worked
                break
            except:
                continue
    """
    print(example_code)


if __name__ == '__main__':
    # Test the formatter
    print("Symbol Formatter Test")
    print("=" * 50)
    
    test_symbols = ['RELIANCE', 'INFY', 'HDFC', 'TCS']
    
    print("\nYahoo Finance format:")
    for sym in test_symbols:
        print(f"  {sym:12} → {SymbolFormatter.format_symbol(sym, 'yfinance')}")
    
    print("\nBreeze API format:")
    for sym in test_symbols:
        print(f"  {sym:12} → {SymbolFormatter.format_symbol(sym, 'breeze')}")
    
    print("\nSymbol variants for fallback:")
    for sym in test_symbols[:2]:
        variants = SymbolFormatter.get_symbol_variants(sym, quick_mode=False)
        print(f"  {sym}: {variants}")
    
    print("\n\nIntegration example:")
    integrate_with_fetcher()
