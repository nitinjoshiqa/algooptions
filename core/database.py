# core/database.py
"""
SQLAlchemy database configuration and ORM models for trading framework.

Tables:
  - stocks: Master reference of NIFTY constituents
  - prices: Daily OHLCV data (updated daily)
  - daily_scores: Calculated metrics per stock per day
  - trade_executions: Trade entry/exit with P&L
  - bucket_analytics: Pre-calculated bucket performance

Database: SQLite (trading_data.db)
"""

import os
from datetime import datetime
from sqlalchemy import create_engine, Column, Integer, String, Float, Date, DateTime, Boolean, ForeignKey, UniqueConstraint, Index
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from sqlalchemy.pool import StaticPool

# Database setup
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATABASE_PATH = os.path.join(BASE_DIR, "trading_data.db")
DATABASE_URL = f"sqlite:///{DATABASE_PATH}"

# Engine configuration
engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
    echo=False  # Set to True for SQL debugging
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


# ============================================================================
# ORM Models
# ============================================================================

class Stock(Base):
    """Master reference table for all stocks."""
    __tablename__ = "stocks"
    
    symbol = Column(String(20), primary_key=True)
    name = Column(String(100), nullable=False)
    sector = Column(String(50))
    market_cap_crores = Column(Integer)
    nifty_constituent = Column(Boolean, default=True)
    nifty_100_constituent = Column(Boolean, default=False)
    banknifty_constituent = Column(Boolean, default=False)
    
    # Tracking
    data_start_date = Column(Date)
    last_update = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    prices = relationship("Price", back_populates="stock", cascade="all, delete-orphan")
    daily_scores = relationship("DailyScore", back_populates="stock", cascade="all, delete-orphan")
    trade_executions = relationship("TradeExecution", back_populates="stock", cascade="all, delete-orphan")
    
    # Index
    __table_args__ = (
        Index('idx_sector', 'sector'),
    )
    
    def __repr__(self):
        return f"<Stock(symbol='{self.symbol}', name='{self.name}')>"


class Price(Base):
    """Daily OHLCV data for all stocks."""
    __tablename__ = "prices"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    symbol = Column(String(20), ForeignKey("stocks.symbol"), nullable=False)
    date = Column(Date, nullable=False)
    open = Column(Float, nullable=False)
    high = Column(Float, nullable=False)
    low = Column(Float, nullable=False)
    close = Column(Float, nullable=False)
    volume = Column(Integer, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationship
    stock = relationship("Stock", back_populates="prices")
    
    # Unique constraint: one entry per symbol per day
    # Indexes for common queries
    __table_args__ = (
        UniqueConstraint('symbol', 'date', name='uix_symbol_date'),
        Index('idx_symbol', 'symbol'),
        Index('idx_date', 'date'),
        Index('idx_symbol_date', 'symbol', 'date'),
    )
    
    def __repr__(self):
        return f"<Price(symbol='{self.symbol}', date={self.date}, close={self.close})>"


class DailyScore(Base):
    """Daily calculated metrics for each stock."""
    __tablename__ = "daily_scores"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    symbol = Column(String(20), ForeignKey("stocks.symbol"), nullable=False)
    date = Column(Date, nullable=False)
    
    # Base Scoring System
    base_score = Column(Float, nullable=False)  # Range: -1.0 to +1.0
    score_bucket = Column(String(30), nullable=False)  # "Ultra-Strong", "Strong Bullish", etc.
    
    # Option Geek Scoring
    option_score = Column(Float)  # Range: -0.5 to +0.5
    option_quality = Column(String(20))  # "excellent", "good", "marginal", "poor"
    is_no_trade_gate = Column(Boolean, default=False)  # 1 if blocked (option_score < -0.3)
    
    # Volume Direction Analysis
    volume_direction = Column(String(20))  # "ACCUMULATION", "DISTRIBUTION", "DIVERGENCE", "NEUTRAL"
    volume_confidence = Column(Integer)  # Range: 0-100%
    obv_current = Column(Float)
    obv_average_30 = Column(Float)
    volume_change_pct = Column(Float)
    
    # Strategy Output
    suggested_strategy = Column(String(50))  # "Long Call", "Long Put", etc.
    confidence_level = Column(Integer)  # Range: 0-100%
    confidence_bucket = Column(String(20))  # "High", "Medium", "Low"
    
    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationship
    stock = relationship("Stock", back_populates="daily_scores")
    
    # Indexes
    __table_args__ = (
        UniqueConstraint('symbol', 'date', name='uix_score_symbol_date'),
        Index('idx_symbol', 'symbol'),
        Index('idx_date', 'date'),
        Index('idx_symbol_date', 'symbol', 'date'),
        Index('idx_score_bucket', 'score_bucket'),
        Index('idx_confidence', 'confidence_bucket'),
        Index('idx_no_trade_gate', 'is_no_trade_gate'),
    )
    
    def __repr__(self):
        return f"<DailyScore(symbol='{self.symbol}', date={self.date}, score={self.base_score}, strategy='{self.suggested_strategy}')>"


class TradeExecution(Base):
    """Track all executed trades from entry to exit."""
    __tablename__ = "trade_executions"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    symbol = Column(String(20), ForeignKey("stocks.symbol"), nullable=False)
    
    # Entry Details
    entry_date = Column(Date, nullable=False)
    entry_price = Column(Float, nullable=False)
    entry_score = Column(Float, nullable=False)
    entry_score_bucket = Column(String(30), nullable=False)
    entry_volume_direction = Column(String(20))
    entry_confidence = Column(Integer)
    strategy_taken = Column(String(50), nullable=False)
    
    # Position Parameters
    quantity = Column(Integer, nullable=False)
    position_size_pct = Column(Float)  # % of portfolio
    risk_per_trade = Column(Float)  # Stop loss level
    target_price = Column(Float)  # Take profit level
    
    # Exit Details
    exit_date = Column(Date)  # NULL = open trade
    exit_price = Column(Float)
    exit_reason = Column(String(50))  # "Target Hit", "Stop Loss", "Manual Close", etc.
    
    # P&L Calculation
    pnl_points = Column(Float)  # exit_price - entry_price
    pnl_percent = Column(Float)  # (pnl_points / entry_price) * 100
    win = Column(Integer)  # 1 if profitable, 0 if loss, NULL if open
    hold_days = Column(Integer)  # Days held
    
    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationship
    stock = relationship("Stock", back_populates="trade_executions")
    
    # Indexes
    __table_args__ = (
        Index('idx_symbol', 'symbol'),
        Index('idx_entry_date', 'entry_date'),
        Index('idx_exit_date', 'exit_date'),
        Index('idx_status', 'exit_date'),  # NULL = open trades
        Index('idx_entry_bucket', 'entry_score_bucket'),
        Index('idx_win', 'win'),
    )
    
    def __repr__(self):
        status = "OPEN" if self.exit_date is None else "CLOSED"
        return f"<TradeExecution(symbol='{self.symbol}', entry={self.entry_date}, pnl={self.pnl_percent}, status={status})>"


class BucketAnalytic(Base):
    """Pre-calculated bucket performance metrics."""
    __tablename__ = "bucket_analytics"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    score_bucket = Column(String(30), nullable=False)
    
    # Time Period
    period_start = Column(Date, nullable=False)
    period_end = Column(Date, nullable=False)
    
    # Trade Statistics
    total_trades = Column(Integer, default=0)
    winning_trades = Column(Integer, default=0)
    losing_trades = Column(Integer, default=0)
    
    # Metrics
    win_rate = Column(Float)  # %
    avg_win_pnl = Column(Float)
    avg_loss_pnl = Column(Float)
    largest_win = Column(Float)
    largest_loss = Column(Float)
    
    # Expectancy Calculation
    expectancy = Column(Float)  # (win% × avg_win) - (loss% × abs(avg_loss))
    risk_reward_ratio = Column(Float)  # avg_win / abs(avg_loss)
    profit_factor = Column(Float)  # total_wins / total_losses
    
    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Indexes
    __table_args__ = (
        UniqueConstraint('score_bucket', 'period_start', 'period_end', name='uix_bucket_period'),
        Index('idx_bucket', 'score_bucket'),
        Index('idx_period', 'period_start', 'period_end'),
    )
    
    def __repr__(self):
        return f"<BucketAnalytic(bucket='{self.score_bucket}', trades={self.total_trades}, wr={self.win_rate}%)>"


# ============================================================================
# Database Initialization
# ============================================================================

def init_db():
    """Create all tables if they don't exist."""
    try:
        Base.metadata.create_all(bind=engine)
        print(f"Database initialized at: {DATABASE_PATH}")
    except Exception as e:
        # Index may already exist - this is OK
        if "already exists" not in str(e):
            raise
        print(f"Database already initialized (indexes exist)")


def get_session():
    """Get a database session."""
    return SessionLocal()


def close_session(session):
    """Close a database session."""
    if session:
        session.close()


# ============================================================================
# Utility Functions
# ============================================================================

def get_or_create_stock(session, symbol, name, sector=None, nifty_constituent=True):
    """Get or create a stock record."""
    stock = session.query(Stock).filter(Stock.symbol == symbol).first()
    if not stock:
        stock = Stock(
            symbol=symbol,
            name=name,
            sector=sector,
            nifty_constituent=nifty_constituent,
            data_start_date=datetime.now().date()
        )
        session.add(stock)
        session.commit()
    return stock


def stock_exists(session, symbol):
    """Check if stock exists."""
    return session.query(Stock).filter(Stock.symbol == symbol).first() is not None


def delete_all_data(session):
    """⚠️ Delete ALL data from database. Use with caution!"""
    try:
        session.query(TradeExecution).delete()
        session.query(BucketAnalytic).delete()
        session.query(DailyScore).delete()
        session.query(Price).delete()
        session.query(Stock).delete()
        session.commit()
        print("⚠️ All data deleted from database")
    except Exception as e:
        session.rollback()
        print(f"❌ Error deleting data: {e}")


if __name__ == "__main__":
    # Initialize database on direct run
    init_db()
    session = get_session()
    
    # Print database info
    stock_count = session.query(Stock).count()
    price_count = session.query(Price).count()
    score_count = session.query(DailyScore).count()
    trade_count = session.query(TradeExecution).count()
    
    print(f"\n📊 Database Statistics:")
    print(f"  Stocks: {stock_count}")
    print(f"  Prices: {price_count}")
    print(f"  Daily Scores: {score_count}")
    print(f"  Trade Executions: {trade_count}")
    
    close_session(session)
