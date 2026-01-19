# core/database_operations.py
"""
Database CRUD operations for trading framework.

Provides high-level functions to:
  - Save daily prices and scores
  - Query historical data
  - Track trades
  - Calculate bucket performance
  - Export for analysis
"""

from datetime import datetime, timedelta, date
from typing import List, Optional, Tuple
from sqlalchemy import func, and_, or_, desc
from sqlalchemy.orm import Session
from core.database import (
    get_session, close_session,
    Stock, Price, DailyScore, TradeExecution, BucketAnalytic
)


# ============================================================================
# PRICE DATA Operations
# ============================================================================

def save_price(session: Session, symbol: str, trade_date: date, 
               open_price: float, high: float, low: float, close: float, volume: int):
    """Save or update daily price data."""
    try:
        # Check if record already exists
        existing = session.query(Price).filter(
            and_(Price.symbol == symbol, Price.date == trade_date)
        ).first()
        
        if existing:
            # Update existing
            existing.open = open_price
            existing.high = high
            existing.low = low
            existing.close = close
            existing.volume = volume
        else:
            # Create new
            price = Price(
                symbol=symbol,
                date=trade_date,
                open=open_price,
                high=high,
                low=low,
                close=close,
                volume=volume
            )
            session.add(price)
        
        session.commit()
        return True
    except Exception as e:
        session.rollback()
        print(f"❌ Error saving price for {symbol}: {e}")
        return False


def save_multiple_prices(session: Session, prices_data: List[dict]):
    """Bulk save multiple price records.
    
    Args:
        prices_data: List of dicts with keys: symbol, date, open, high, low, close, volume
    """
    try:
        for data in prices_data:
            save_price(session, data['symbol'], data['date'], 
                      data['open'], data['high'], data['low'], 
                      data['close'], data['volume'])
        return True
    except Exception as e:
        print(f"❌ Error bulk saving prices: {e}")
        return False


def get_price_history(session: Session, symbol: str, days: int = 365) -> List[Price]:
    """Get price history for a stock."""
    start_date = date.today() - timedelta(days=days)
    return session.query(Price).filter(
        and_(Price.symbol == symbol, Price.date >= start_date)
    ).order_by(desc(Price.date)).all()


def get_latest_price(session: Session, symbol: str) -> Optional[Price]:
    """Get latest price data for a stock."""
    return session.query(Price).filter(
        Price.symbol == symbol
    ).order_by(desc(Price.date)).first()


def get_prices_by_date_range(session: Session, symbol: str, 
                            start_date: date, end_date: date) -> List[Price]:
    """Get prices for specific date range."""
    return session.query(Price).filter(
        and_(Price.symbol == symbol, 
             Price.date >= start_date, 
             Price.date <= end_date)
    ).order_by(Price.date).all()


# ============================================================================
# DAILY SCORES Operations
# ============================================================================

def save_daily_score(session: Session, symbol: str, trade_date: date,
                    base_score: float, score_bucket: str,
                    option_score: Optional[float] = None,
                    option_quality: Optional[str] = None,
                    is_no_trade_gate: bool = False,
                    volume_direction: Optional[str] = None,
                    volume_confidence: Optional[int] = None,
                    obv_current: Optional[float] = None,
                    obv_average_30: Optional[float] = None,
                    volume_change_pct: Optional[float] = None,
                    suggested_strategy: Optional[str] = None,
                    confidence_level: Optional[int] = None,
                    confidence_bucket: Optional[str] = None):
    """Save daily score for a stock."""
    try:
        # Check if exists
        existing = session.query(DailyScore).filter(
            and_(DailyScore.symbol == symbol, DailyScore.date == trade_date)
        ).first()
        
        if existing:
            # Update
            existing.base_score = base_score
            existing.score_bucket = score_bucket
            existing.option_score = option_score
            existing.option_quality = option_quality
            existing.is_no_trade_gate = is_no_trade_gate
            existing.volume_direction = volume_direction
            existing.volume_confidence = volume_confidence
            existing.obv_current = obv_current
            existing.obv_average_30 = obv_average_30
            existing.volume_change_pct = volume_change_pct
            existing.suggested_strategy = suggested_strategy
            existing.confidence_level = confidence_level
            existing.confidence_bucket = confidence_bucket
        else:
            # Create new
            daily_score = DailyScore(
                symbol=symbol,
                date=trade_date,
                base_score=base_score,
                score_bucket=score_bucket,
                option_score=option_score,
                option_quality=option_quality,
                is_no_trade_gate=is_no_trade_gate,
                volume_direction=volume_direction,
                volume_confidence=volume_confidence,
                obv_current=obv_current,
                obv_average_30=obv_average_30,
                volume_change_pct=volume_change_pct,
                suggested_strategy=suggested_strategy,
                confidence_level=confidence_level,
                confidence_bucket=confidence_bucket
            )
            session.add(daily_score)
        
        session.commit()
        return True
    except Exception as e:
        session.rollback()
        try:
            print(f"Error saving daily score for {symbol}: {e}")
        except UnicodeEncodeError:
            print(f"Error saving daily score for {symbol}: {str(e).encode('ascii', errors='replace').decode('ascii')}")
        return False


def get_today_scores(session: Session) -> List[DailyScore]:
    """Get all scores for today."""
    today = date.today()
    return session.query(DailyScore).filter(
        DailyScore.date == today
    ).order_by(desc(DailyScore.base_score)).all()


def get_high_confidence_stocks(session: Session, confidence_min: int = 60,
                              trade_date: Optional[date] = None) -> List[DailyScore]:
    """Get high confidence stocks for a date."""
    if trade_date is None:
        trade_date = date.today()
    
    return session.query(DailyScore).filter(
        and_(DailyScore.date == trade_date,
             DailyScore.confidence_level >= confidence_min,
             DailyScore.is_no_trade_gate == False)
    ).order_by(desc(DailyScore.base_score)).all()


def get_stock_history(session: Session, symbol: str, days: int = 30) -> List[DailyScore]:
    """Get score history for a stock."""
    start_date = date.today() - timedelta(days=days)
    return session.query(DailyScore).filter(
        and_(DailyScore.symbol == symbol, DailyScore.date >= start_date)
    ).order_by(desc(DailyScore.date)).all()


def get_no_trade_gate_blocks(session: Session, trade_date: Optional[date] = None) -> List[DailyScore]:
    """Get all stocks blocked by NO-TRADE gate."""
    if trade_date is None:
        trade_date = date.today()
    
    return session.query(DailyScore).filter(
        and_(DailyScore.date == trade_date,
             DailyScore.is_no_trade_gate == True)
    ).all()


def get_scores_by_bucket(session: Session, bucket: str, 
                        days: int = 365) -> List[DailyScore]:
    """Get all stocks in a specific score bucket."""
    start_date = date.today() - timedelta(days=days)
    return session.query(DailyScore).filter(
        and_(DailyScore.score_bucket == bucket,
             DailyScore.date >= start_date)
    ).order_by(desc(DailyScore.date)).all()


def get_volume_direction_stats(session: Session, direction: str,
                              days: int = 365) -> List[DailyScore]:
    """Get stocks with specific volume direction."""
    start_date = date.today() - timedelta(days=days)
    return session.query(DailyScore).filter(
        and_(DailyScore.volume_direction == direction,
             DailyScore.date >= start_date)
    ).order_by(desc(DailyScore.date)).all()


# ============================================================================
# TRADE EXECUTION Operations
# ============================================================================

def open_trade(session: Session, symbol: str, entry_date: date,
               entry_price: float, entry_score: float, entry_score_bucket: str,
               strategy_taken: str, quantity: int = 1,
               confidence_level: Optional[int] = None,
               volume_direction: Optional[str] = None,
               position_size_pct: Optional[float] = None,
               risk_per_trade: Optional[float] = None,
               target_price: Optional[float] = None) -> Optional[int]:
    """Open a new trade. Returns trade ID."""
    try:
        trade = TradeExecution(
            symbol=symbol,
            entry_date=entry_date,
            entry_price=entry_price,
            entry_score=entry_score,
            entry_score_bucket=entry_score_bucket,
            entry_confidence=confidence_level,
            entry_volume_direction=volume_direction,
            strategy_taken=strategy_taken,
            quantity=quantity,
            position_size_pct=position_size_pct,
            risk_per_trade=risk_per_trade,
            target_price=target_price
        )
        session.add(trade)
        session.commit()
        return trade.id
    except Exception as e:
        session.rollback()
        print(f"❌ Error opening trade for {symbol}: {e}")
        return None


def close_trade(session: Session, trade_id: int, exit_date: date,
                exit_price: float, exit_reason: str = "Manual Close") -> bool:
    """Close an open trade and calculate P&L."""
    try:
        trade = session.query(TradeExecution).filter(
            TradeExecution.id == trade_id
        ).first()
        
        if not trade:
            print(f"❌ Trade {trade_id} not found")
            return False
        
        # Calculate P&L
        pnl_points = exit_price - trade.entry_price
        pnl_percent = (pnl_points / trade.entry_price) * 100
        hold_days = (exit_date - trade.entry_date).days
        win = 1 if pnl_percent > 0 else 0
        
        # Update trade
        trade.exit_date = exit_date
        trade.exit_price = exit_price
        trade.exit_reason = exit_reason
        trade.pnl_points = pnl_points
        trade.pnl_percent = pnl_percent
        trade.hold_days = hold_days
        trade.win = win
        
        session.commit()
        return True
    except Exception as e:
        session.rollback()
        print(f"❌ Error closing trade {trade_id}: {e}")
        return False


def get_open_trades(session: Session) -> List[TradeExecution]:
    """Get all open trades."""
    return session.query(TradeExecution).filter(
        TradeExecution.exit_date.is_(None)
    ).all()


def get_closed_trades(session: Session, days: int = 365) -> List[TradeExecution]:
    """Get closed trades from last N days."""
    start_date = date.today() - timedelta(days=days)
    return session.query(TradeExecution).filter(
        and_(TradeExecution.exit_date.isnot(None),
             TradeExecution.exit_date >= start_date)
    ).order_by(desc(TradeExecution.exit_date)).all()


def get_trades_by_bucket(session: Session, bucket: str) -> List[TradeExecution]:
    """Get all trades for a specific bucket."""
    return session.query(TradeExecution).filter(
        and_(TradeExecution.entry_score_bucket == bucket,
             TradeExecution.exit_date.isnot(None))
    ).all()


def get_trades_by_symbol(session: Session, symbol: str) -> List[TradeExecution]:
    """Get all trades for a symbol."""
    return session.query(TradeExecution).filter(
        TradeExecution.symbol == symbol
    ).all()


def get_bucket_win_rate(session: Session, bucket: str) -> Optional[float]:
    """Get win rate for a bucket."""
    trades = get_trades_by_bucket(session, bucket)
    if not trades:
        return None
    
    wins = sum(1 for t in trades if t.win == 1)
    return (wins / len(trades)) * 100


def get_bucket_stats(session: Session, bucket: str) -> dict:
    """Get comprehensive stats for a bucket."""
    trades = get_trades_by_bucket(session, bucket)
    
    if not trades:
        return {"error": "No trades found"}
    
    wins = [t for t in trades if t.win == 1]
    losses = [t for t in trades if t.win == 0]
    
    avg_win = sum(t.pnl_percent for t in wins) / len(wins) if wins else 0
    avg_loss = sum(t.pnl_percent for t in losses) / len(losses) if losses else 0
    
    win_rate = (len(wins) / len(trades)) * 100
    expectancy = (win_rate/100 * avg_win) - ((1 - win_rate/100) * abs(avg_loss))
    
    return {
        "bucket": bucket,
        "total_trades": len(trades),
        "wins": len(wins),
        "losses": len(losses),
        "win_rate": round(win_rate, 2),
        "avg_win": round(avg_win, 2),
        "avg_loss": round(avg_loss, 2),
        "largest_win": round(max([t.pnl_percent for t in wins], default=0), 2),
        "largest_loss": round(min([t.pnl_percent for t in losses], default=0), 2),
        "expectancy": round(expectancy, 2)
    }


# ============================================================================
# BUCKET ANALYTICS Operations
# ============================================================================

def save_bucket_analytics(session: Session, score_bucket: str,
                         period_start: date, period_end: date,
                         total_trades: int, winning_trades: int,
                         win_rate: float, avg_win_pnl: float,
                         avg_loss_pnl: float, largest_win: float,
                         largest_loss: float, expectancy: float,
                         risk_reward_ratio: float, profit_factor: float) -> bool:
    """Save or update bucket analytics."""
    try:
        existing = session.query(BucketAnalytic).filter(
            and_(BucketAnalytic.score_bucket == score_bucket,
                 BucketAnalytic.period_start == period_start,
                 BucketAnalytic.period_end == period_end)
        ).first()
        
        if existing:
            # Update
            existing.total_trades = total_trades
            existing.winning_trades = winning_trades
            existing.losing_trades = total_trades - winning_trades
            existing.win_rate = win_rate
            existing.avg_win_pnl = avg_win_pnl
            existing.avg_loss_pnl = avg_loss_pnl
            existing.largest_win = largest_win
            existing.largest_loss = largest_loss
            existing.expectancy = expectancy
            existing.risk_reward_ratio = risk_reward_ratio
            existing.profit_factor = profit_factor
        else:
            # Create new
            analytics = BucketAnalytic(
                score_bucket=score_bucket,
                period_start=period_start,
                period_end=period_end,
                total_trades=total_trades,
                winning_trades=winning_trades,
                losing_trades=total_trades - winning_trades,
                win_rate=win_rate,
                avg_win_pnl=avg_win_pnl,
                avg_loss_pnl=avg_loss_pnl,
                largest_win=largest_win,
                largest_loss=largest_loss,
                expectancy=expectancy,
                risk_reward_ratio=risk_reward_ratio,
                profit_factor=profit_factor
            )
            session.add(analytics)
        
        session.commit()
        return True
    except Exception as e:
        session.rollback()
        print(f"❌ Error saving bucket analytics: {e}")
        return False


def get_bucket_analytics(session: Session, score_bucket: str,
                        period_end: date = None) -> Optional[BucketAnalytic]:
    """Get bucket analytics for latest period."""
    if period_end is None:
        period_end = date.today()
    
    return session.query(BucketAnalytic).filter(
        and_(BucketAnalytic.score_bucket == score_bucket,
             BucketAnalytic.period_end == period_end)
    ).first()


def get_all_bucket_analytics(session: Session, period_end: date = None) -> List[BucketAnalytic]:
    """Get all bucket analytics for a period."""
    if period_end is None:
        period_end = date.today()
    
    return session.query(BucketAnalytic).filter(
        BucketAnalytic.period_end == period_end
    ).order_by(desc(BucketAnalytic.expectancy)).all()


# ============================================================================
# Reporting Functions
# ============================================================================

def get_portfolio_summary(session: Session) -> dict:
    """Get summary of current portfolio."""
    open_trades = get_open_trades(session)
    closed_trades = get_closed_trades(session)
    
    if not closed_trades:
        return {"error": "No closed trades"}
    
    total_pnl = sum(t.pnl_percent for t in closed_trades)
    avg_pnl = total_pnl / len(closed_trades)
    win_count = sum(1 for t in closed_trades if t.win == 1)
    
    return {
        "open_trades": len(open_trades),
        "closed_trades": len(closed_trades),
        "total_pnl_percent": round(total_pnl, 2),
        "avg_pnl_percent": round(avg_pnl, 2),
        "win_rate": round((win_count / len(closed_trades)) * 100, 2),
        "best_trade": round(max(t.pnl_percent for t in closed_trades), 2),
        "worst_trade": round(min(t.pnl_percent for t in closed_trades), 2)
    }


def get_last_update(session: Session) -> Optional[datetime]:
    """Get timestamp of last database update."""
    latest = session.query(DailyScore).order_by(
        desc(DailyScore.created_at)
    ).first()
    return latest.created_at if latest else None


def export_trades_to_dict(session: Session) -> List[dict]:
    """Export all trades as dictionaries for CSV export."""
    trades = session.query(TradeExecution).filter(
        TradeExecution.exit_date.isnot(None)
    ).all()
    
    return [
        {
            "symbol": t.symbol,
            "entry_date": t.entry_date,
            "entry_price": round(t.entry_price, 2),
            "entry_score": round(t.entry_score, 3),
            "exit_date": t.exit_date,
            "exit_price": round(t.exit_price, 2),
            "pnl_percent": round(t.pnl_percent, 2),
            "win": "YES" if t.win == 1 else "NO",
            "hold_days": t.hold_days,
            "strategy": t.strategy_taken
        }
        for t in trades
    ]


if __name__ == "__main__":
    # Test database operations
    session = get_session()
    
    # Get sample data
    today_scores = get_today_scores(session)
    print(f"\n📊 Today's Scores: {len(today_scores)} stocks")
    for score in today_scores[:5]:
        print(f"  {score.symbol}: {score.base_score:.3f} ({score.suggested_strategy})")
    
    # Get portfolio summary
    try:
        summary = get_portfolio_summary(session)
        print(f"\n💼 Portfolio Summary:")
        for key, value in summary.items():
            print(f"  {key}: {value}")
    except:
        print("\n💼 Portfolio Summary: No data yet")
    
    close_session(session)


# ============================================================================
# SECTOR MAPPING Operations
# ============================================================================

def verify_and_update_sectors(session: Session) -> dict:
    """Verify sector mappings and update Stock table with latest mappings.
    
    Returns:
        dict with statistics about updates
    """
    from core.sector_mapper import get_sector
    
    try:
        stats = {'checked': 0, 'updated': 0, 'stale': 0}
        
        # Get all stocks in database
        stocks = session.query(Stock).all()
        
        for stock in stocks:
            stats['checked'] += 1
            correct_sector = get_sector(stock.symbol)
            
            if stock.sector != correct_sector:
                stats['stale'] += 1
                stock.sector = correct_sector
                stats['updated'] += 1
        
        if stats['updated'] > 0:
            session.commit()
        
        return stats
    except Exception as e:
        print(f"Error updating sectors: {e}")
        return {'error': str(e)}


def check_sector_staleness(session: Session) -> List[dict]:
    """Check which stocks have stale sector mappings.
    
    Returns:
        list of dicts with symbol, current_sector, correct_sector
    """
    from core.sector_mapper import get_sector
    
    stale = []
    stocks = session.query(Stock).all()
    
    for stock in stocks:
        correct_sector = get_sector(stock.symbol)
        if stock.sector != correct_sector:
            stale.append({
                'symbol': stock.symbol,
                'current': stock.sector,
                'correct': correct_sector
            })
    
    return stale

