"""Data source abstraction layer - cleaner provider management.

This module manages data provider fallback chain and provides
a unified interface for fetching candles and prices.
"""

import time
from enum import Enum


class DataProvider(Enum):
    """Supported data providers."""
    BREEZE = "breeze"
    NSEPYTHON = "nsepython"
    YFINANCE = "yfinance"
    CACHE = "cache"


class DataSourceManager:
    """Manages data provider fallback chain and caching."""
    
    def __init__(self, prefer_provider=None, force_provider=None):
        """
        Initialize data source manager.
        
        Args:
            prefer_provider: Preferred provider (DataProvider enum)
            force_provider: Force single provider (no fallback)
        """
        self.prefer_provider = prefer_provider
        self.force_provider = force_provider
        self.stats = {
            'breeze': 0,
            'nsepython': 0,
            'yfinance': 0,
            'cache': 0,
            'failed': 0
        }
    
    def get_fallback_chain(self):
        """Get provider fallback order based on configuration."""
        if self.force_provider:
            return [self.force_provider]
        
        if self.prefer_provider:
            # Primary: preferred, Secondary: others
            chain = [self.prefer_provider]
            for provider in [DataProvider.BREEZE, DataProvider.NSEPYTHON, DataProvider.YFINANCE]:
                if provider != self.prefer_provider:
                    chain.append(provider)
            return chain
        
        # Default fallback chain: Breeze → NSE → yFinance
        return [
            DataProvider.BREEZE,
            DataProvider.NSEPYTHON,
            DataProvider.YFINANCE
        ]
    
    def fetch_candles(self, symbol, interval='5minute', max_bars=200):
        """
        Fetch candles with automatic fallback chain.
        
        Returns:
            (candles_list, provider_name) or ([], None) if all sources fail
        """
        from data_providers import get_candles
        
        # Try cache first
        try:
            from core.candle_cache import load_candles_from_db
            cached, source = load_candles_from_db(symbol, interval, max_age_hours=2)
            if cached:
                self.stats['cache'] += 1
                return cached[-max_bars:], f'{source}_cached'
        except Exception:
            pass
        
        # Try each provider in fallback order
        for provider in self.get_fallback_chain():
            try:
                candles, src = get_candles(
                    symbol, 
                    interval, 
                    max_bars,
                    force_yf=(provider == DataProvider.YFINANCE)
                )
                
                if candles:
                    provider_name = provider.value
                    self.stats[provider_name] += 1
                    return candles, provider_name
                    
            except Exception as e:
                # Log but continue to next provider
                continue
        
        # All sources failed
        self.stats['failed'] += 1
        return [], None
    
    def fetch_price(self, symbol, period='1y'):
        """Fetch current/historical price with fallback."""
        from data_providers import get_price
        
        for provider in self.get_fallback_chain():
            try:
                price = get_price(symbol, period=period, force_yf=(provider == DataProvider.YFINANCE))
                if price:
                    return price, provider.value
            except Exception:
                continue
        
        return None, None
    
    def get_stats(self):
        """Get usage statistics for this session."""
        return self.stats
    
    def print_stats(self):
        """Print data source usage statistics."""
        print("\n[DATA SOURCE STATS]")
        for provider, count in self.stats.items():
            if count > 0:
                print(f"  {provider:12} {count:4d}")


class CacheConfig:
    """Cache configuration constants."""
    INTRADAY_INTERVALS = ['1minute', '5minute', '15minute', '30minute', '1hour']
    DAILY_INTERVALS = ['1day', '1d', '1day', '1week']
    
    # TTL in seconds
    INTRADAY_CACHE_TTL = 0  # Never cache intraday (signals decay)
    DAILY_CACHE_TTL = 86400  # 24 hours for daily
    PRICE_CACHE_TTL = 60  # 1 minute for prices
    
    @staticmethod
    def should_cache(interval):
        """Check if interval should be cached."""
        # Never cache intraday
        if interval.lower() in CacheConfig.INTRADAY_INTERVALS:
            return False
        # Cache daily and longer
        return True
