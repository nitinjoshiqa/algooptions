#!/usr/bin/env python3
"""
Candle cache database module for storing intraday/daily historical candles.

This module provides fast local storage of candle data to minimize API calls.
Supports multiple timeframes: 5minute, 15minute, 1hour, 1day

Database: SQLite (candle_cache.db)
TTL: 4-8 hours depending on candle age
"""

import os
import json
from datetime import datetime, timedelta
from sqlalchemy import create_engine, Column, Integer, String, DateTime, Text, Index, UniqueConstraint
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool


def normalize_symbol(symbol):
    """
    Normalize symbol for cache key - remove .NS suffix to ensure consistent caching.
    CRITICAL: All cache keys must use the base symbol (e.g., 'HDFCBANK') not variants
    to prevent data integrity issues where HDFCBANK and HDFCBANK.NS return different cached data.
    
    Args:
        symbol: Stock symbol (may or may not have .NS suffix)
    
    Returns:
        Normalized symbol without .NS suffix
    """
    if symbol and symbol.endswith('.NS'):
        return symbol[:-3]  # Remove .NS suffix
    return symbol

# Database setup
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CANDLE_CACHE_PATH = os.path.join(BASE_DIR, "candle_cache.db")
CANDLE_CACHE_URL = f"sqlite:///{CANDLE_CACHE_PATH}"

# Engine configuration
engine = create_engine(
    CANDLE_CACHE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
    echo=False
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


class CandleCache(Base):
    """Cache for intraday and daily candle data."""
    __tablename__ = "candle_cache"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    symbol = Column(String(20), nullable=False)
    interval = Column(String(20), nullable=False)  # '5minute', '15minute', '1hour', '1day'
    candles_json = Column(Text, nullable=False)  # JSON array of candles
    source = Column(String(50), default='breeze')  # breeze, yfinance, nse
    last_fetched = Column(DateTime, default=datetime.utcnow)
    
    # Unique constraint: one cache entry per symbol per interval
    __table_args__ = (
        UniqueConstraint('symbol', 'interval', name='uix_symbol_interval'),
        Index('idx_symbol', 'symbol'),
        Index('idx_interval', 'interval'),
        Index('idx_last_fetched', 'last_fetched'),
    )
    
    def __repr__(self):
        return f"<CandleCache(symbol='{self.symbol}', interval='{self.interval}')>"


# Create tables
Base.metadata.create_all(bind=engine)


def get_session():
    """Get database session."""
    return SessionLocal()


def save_candles_to_db(symbol, interval, candles, source='breeze'):
    """
    Save candles to database cache.
    
    Args:
        symbol: Stock symbol (e.g., 'TCS' or 'TCS.NS')
        interval: Candle interval ('5minute', '15minute', '1hour', '1day')
        candles: List of candle dicts with OHLCV data
        source: Data source ('breeze', 'yfinance', 'nse')
    
    Returns:
        True if saved, False if error
    """
    if not candles:
        return False
    
    # Normalize symbol to prevent data integrity issues
    symbol = normalize_symbol(symbol)
    
    session = None
    try:
        session = get_session()
        
        # Convert candles to JSON
        candles_json = json.dumps(candles)
        
        # Check if entry exists
        existing = session.query(CandleCache).filter(
            CandleCache.symbol == symbol,
            CandleCache.interval == interval
        ).first()
        
        if existing:
            # Update existing entry
            existing.candles_json = candles_json
            existing.source = source
            existing.last_fetched = datetime.utcnow()
        else:
            # Create new entry
            cache_entry = CandleCache(
                symbol=symbol,
                interval=interval,
                candles_json=candles_json,
                source=source
            )
            session.add(cache_entry)
        
        session.commit()
        return True
    except Exception as e:
        try:
            if session:
                session.rollback()
        except:
            pass  # Ignore rollback errors (no transaction active)
        return False
    finally:
        if session:
            try:
                session.close()
            except:
                pass  # Ignore close errors


def load_candles_from_db(symbol, interval, max_age_hours=4):
    """
    Load candles from database cache.
    
    Args:
        symbol: Stock symbol (e.g., 'TCS' or 'TCS.NS')
        interval: Candle interval ('5minute', '15minute', '1hour', '1day')
        max_age_hours: Cache is valid if fetched within this many hours (default 4)
    
    Returns:
        Tuple (candles list, source) if cache hit, (None, None) if expired/not found
    """
    # Normalize symbol to prevent data integrity issues
    symbol = normalize_symbol(symbol)
    
    session = None
    try:
        session = get_session()
        
        # Query cache entry
        cache_entry = session.query(CandleCache).filter(
            CandleCache.symbol == symbol,
            CandleCache.interval == interval
        ).first()
        
        if not cache_entry:
            return None, None
        
        # Check if cache is still valid
        age = datetime.utcnow() - cache_entry.last_fetched
        max_age = timedelta(hours=max_age_hours)
        
        if age > max_age:
            # Cache expired
            return None, None
        
        # Parse and return candles
        candles = json.loads(cache_entry.candles_json)
        source = cache_entry.source
        
        return candles, source
    except Exception as e:
        return None, None
    finally:
        if session:
            session.close()


def clear_old_cache(max_age_hours=24):
    """
    Clear cache entries older than specified hours.
    
    Args:
        max_age_hours: Delete entries older than this (default 24 hours)
    
    Returns:
        Number of entries deleted
    """
    session = None
    try:
        session = get_session()
        
        cutoff_time = datetime.utcnow() - timedelta(hours=max_age_hours)
        
        deleted = session.query(CandleCache).filter(
            CandleCache.last_fetched < cutoff_time
        ).delete()
        
        session.commit()
        
        return deleted
    except Exception as e:
        try:
            if session:
                session.rollback()
        except:
            pass  # Ignore rollback errors (no transaction active)
        return 0
    finally:
        if session:
            try:
                session.close()
            except:
                pass  # Ignore close errors


def migrate_cache_to_normalized_symbols():
    """
    CRITICAL FIX: Consolidate cache entries from symbol variants to single normalized form.
    
    Problem: Cache stored both HDFCBANK and HDFCBANK.NS as separate entries, causing
    data integrity issues where different symbol variants returned different cached data.
    
    Solution: Delete duplicate variant entries (.NS suffix) and keep base symbol entries.
    This ensures all queries normalize to the base symbol before cache lookup.
    
    Returns:
        Dict with migration stats: {'removed_variant_entries': count, 'consolidated_symbols': list}
    """
    session = None
    try:
        session = get_session()
        
        # Find all symbols with .NS suffix
        variant_entries = session.query(CandleCache).filter(
            CandleCache.symbol.like('%.NS')
        ).all()
        
        removed_count = 0
        consolidated_symbols = set()
        
        for entry in variant_entries:
            # Check if base symbol (without .NS) exists
            base_symbol = entry.symbol[:-3]  # Remove .NS
            base_entry = session.query(CandleCache).filter(
                CandleCache.symbol == base_symbol,
                CandleCache.interval == entry.interval
            ).first()
            
            if base_entry:
                # Base entry exists - delete this variant entry
                session.delete(entry)
                removed_count += 1
                consolidated_symbols.add(entry.symbol)
            else:
                # No base entry exists - rename this variant to base form
                entry.symbol = base_symbol
                consolidated_symbols.add(f"{entry.symbol}.NS -> {base_symbol}")
        
        session.commit()
        
        return {
            'removed_variant_entries': removed_count,
            'consolidated_symbols': list(consolidated_symbols)
        }
    except Exception as e:
        try:
            if session:
                session.rollback()
        except:
            pass
        return {'removed_variant_entries': 0, 'consolidated_symbols': [], 'error': str(e)}
    finally:
        if session:
            try:
                session.close()
            except:
                pass


def get_cache_stats():
    """Get cache statistics."""
    session = None
    try:
        session = get_session()
        
        total_entries = session.query(CandleCache).count()
        symbols_cached = session.query(CandleCache.symbol).distinct().count()
        
        # Find oldest and newest entries
        oldest = session.query(CandleCache).order_by(CandleCache.last_fetched).first()
        newest = session.query(CandleCache).order_by(CandleCache.last_fetched.desc()).first()
        
        return {
            'total_entries': total_entries,
            'symbols_cached': symbols_cached,
            'oldest_entry': oldest.last_fetched if oldest else None,
            'newest_entry': newest.last_fetched if newest else None,
        }
    except Exception as e:
        return {}
    finally:
        if session:
            session.close()
