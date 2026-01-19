"""
Performance tracking and result recording system.
Stores pick history, daily results, and win rate statistics.
"""

import sqlite3
import json
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional, List, Dict, Any
import logging

logger = logging.getLogger(__name__)

# Database location
DB_PATH = Path(__file__).parent.parent / "performance.db"


class PerformanceTracker:
    """Manages performance database and result tracking."""
    
    def __init__(self, db_path: Path = DB_PATH):
        self.db_path = db_path
        self._ensure_database()
    
    def _ensure_database(self):
        """Create database and tables if they don't exist."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Picks table: Store each screener recommendation
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS picks (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    date TEXT NOT NULL,
                    symbol TEXT NOT NULL,
                    direction TEXT NOT NULL,
                    score REAL NOT NULL,
                    price REAL NOT NULL,
                    rsi REAL,
                    ema_trend REAL,
                    atr REAL,
                    confidence TEXT DEFAULT 'medium',
                    notes TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Results table: Track daily outcomes
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS results (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    pick_id INTEGER NOT NULL,
                    date TEXT NOT NULL,
                    price REAL NOT NULL,
                    pnl REAL,
                    pnl_percent REAL,
                    status TEXT DEFAULT 'open',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (pick_id) REFERENCES picks(id)
                )
            """)
            
            # Index for faster queries
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_picks_symbol_date 
                ON picks(symbol, date)
            """)
            
            conn.commit()
    
    def record_pick(self, symbol: str, direction: str, score: float, 
                    price: float, rsi: Optional[float] = None, 
                    ema_trend: Optional[float] = None, atr: Optional[float] = None,
                    confidence: str = "medium", notes: Optional[str] = None) -> int:
        """Record a new pick from screener run."""
        date = datetime.now().strftime("%Y-%m-%d")
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO picks 
                (date, symbol, direction, score, price, rsi, ema_trend, atr, confidence, notes)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (date, symbol, direction, score, price, rsi, ema_trend, atr, confidence, notes))
            
            conn.commit()
            pick_id = cursor.lastrowid
            logger.info(f"Recorded pick: {symbol} {direction} @ {price} (score: {score:.2f})")
            return pick_id
    
    def record_result(self, pick_id: int, current_price: float, status: str = "open") -> Optional[float]:
        """Record daily result for a pick. Returns PnL percent or None."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Get pick details
            cursor.execute("SELECT price FROM picks WHERE id = ?", (pick_id,))
            row = cursor.fetchone()
            if not row:
                logger.warning(f"Pick {pick_id} not found")
                return None
            
            entry_price = row[0]
            pnl = current_price - entry_price
            pnl_percent = (pnl / entry_price * 100) if entry_price > 0 else 0
            
            date = datetime.now().strftime("%Y-%m-%d")
            
            # Check if result already exists for this pick and date
            cursor.execute(
                "SELECT id FROM results WHERE pick_id = ? AND date = ?",
                (pick_id, date)
            )
            existing = cursor.fetchone()
            
            if existing:
                # Update existing result
                cursor.execute("""
                    UPDATE results 
                    SET price = ?, pnl = ?, pnl_percent = ?, status = ?
                    WHERE id = ?
                """, (current_price, pnl, pnl_percent, status, existing[0]))
            else:
                # Insert new result
                cursor.execute("""
                    INSERT INTO results 
                    (pick_id, date, price, pnl, pnl_percent, status)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (pick_id, date, current_price, pnl, pnl_percent, status))
            
            conn.commit()
            return pnl_percent
    
    def get_picks_by_date(self, date: str) -> List[Dict[str, Any]]:
        """Get all picks from a specific date."""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute("""
                SELECT * FROM picks WHERE date = ? ORDER BY score DESC
            """, (date,))
            return [dict(row) for row in cursor.fetchall()]
    
    def get_open_picks(self) -> List[Dict[str, Any]]:
        """Get picks with open status (no final result yet)."""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute("""
                SELECT p.*, 
                       MAX(r.pnl_percent) as latest_pnl_percent,
                       MAX(r.date) as latest_result_date
                FROM picks p
                LEFT JOIN results r ON p.id = r.pick_id
                WHERE NOT EXISTS (
                    SELECT 1 FROM results WHERE pick_id = p.id AND status = 'closed'
                )
                GROUP BY p.id
                ORDER BY p.date DESC, p.score DESC
            """)
            return [dict(row) for row in cursor.fetchall()]
    
    def get_performance_stats(self, days: int = 30) -> Dict[str, Any]:
        """Get performance statistics for last N days."""
        cutoff_date = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Total picks
            cursor.execute(
                "SELECT COUNT(*) FROM picks WHERE date >= ?", (cutoff_date,)
            )
            total_picks = cursor.fetchone()[0]
            
            # Bullish vs bearish
            cursor.execute(
                "SELECT direction, COUNT(*) FROM picks WHERE date >= ? GROUP BY direction",
                (cutoff_date,)
            )
            directions = dict(cursor.fetchall())
            
            # Win rate (positive PnL)
            cursor.execute("""
                SELECT COUNT(*) FROM results 
                WHERE pnl_percent > 0 AND date >= ?
            """, (cutoff_date,))
            winners = cursor.fetchone()[0]
            
            # Losers
            cursor.execute("""
                SELECT COUNT(*) FROM results 
                WHERE pnl_percent <= 0 AND date >= ?
            """, (cutoff_date,))
            losers = cursor.fetchone()[0]
            
            # Average PnL
            cursor.execute("""
                SELECT AVG(pnl_percent), MAX(pnl_percent), MIN(pnl_percent)
                FROM results WHERE date >= ?
            """, (cutoff_date,))
            avg_pnl, max_pnl, min_pnl = cursor.fetchone()
            
            total_results = winners + losers
            win_rate = (winners / total_results * 100) if total_results > 0 else 0
            
            return {
                "period_days": days,
                "total_picks": total_picks,
                "bullish_picks": directions.get("bullish", 0),
                "bearish_picks": directions.get("bearish", 0),
                "total_results": total_results,
                "winners": winners,
                "losers": losers,
                "win_rate": round(win_rate, 2),
                "avg_pnl_percent": round(avg_pnl or 0, 2),
                "max_pnl_percent": round(max_pnl or 0, 2),
                "min_pnl_percent": round(min_pnl or 0, 2),
            }
    
    def get_symbol_performance(self, symbol: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Get recent performance for a specific symbol."""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute("""
                SELECT p.*, 
                       GROUP_CONCAT(r.pnl_percent, ',') as results
                FROM picks p
                LEFT JOIN results r ON p.id = r.pick_id
                WHERE p.symbol = ?
                GROUP BY p.id
                ORDER BY p.date DESC
                LIMIT ?
            """, (symbol, limit))
            return [dict(row) for row in cursor.fetchall()]


# Singleton instance
_tracker = None


def get_tracker() -> PerformanceTracker:
    """Get or create the global tracker instance."""
    global _tracker
    if _tracker is None:
        _tracker = PerformanceTracker()
    return _tracker
