#!/usr/bin/env python3
# scripts/load_csv_to_db.py
"""
Load existing CSV data into database.
Uses nifty_bearnness.csv as source for today's scores.
"""

import os
import sys
import pandas as pd
from datetime import date

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.database import get_session, close_session
from core.database_operations import save_daily_score


def determine_score_bucket(score: float) -> str:
    """Determine bucket from score."""
    if score >= 0.50:
        return "Ultra-Strong"
    elif score >= 0.30:
        return "Strong Bullish"
    elif score >= 0.15:
        return "Strong Bullish"
    elif score >= 0.05:
        return "Moderate Bullish"
    elif score > -0.05:
        return "Neutral"
    elif score > -0.15:
        return "Moderate Bearish"
    elif score > -0.30:
        return "Strong Bearish"
    else:
        return "Ultra-Strong Bearish"


def determine_option_quality(option_score: float) -> str:
    """Determine option quality from option score."""
    if option_score > 0.0:
        return "good"
    elif option_score > -0.3:
        return "marginal"
    else:
        return "poor"


def load_csv_to_db():
    """Load today's data from CSV into database."""
    
    csv_file = 'nifty_bearnness.csv'
    
    if not os.path.exists(csv_file):
        print(f"❌ {csv_file} not found!")
        print("   Run: python nifty_bearnness_v2.py --universe nifty --mode swing --force-yf --screener-format html")
        return False
    
    print(f"\n📥 Loading data from {csv_file}...")
    
    try:
        df = pd.read_csv(csv_file)
        print(f"✅ Loaded {len(df)} rows from CSV")
        
        session = get_session()
        today = date.today()
        saved_count = 0
        
        for idx, row in df.iterrows():
            try:
                base_score = float(row['final_score'])
                option_score = float(row['option_score'])
                confidence = int(row['confidence']) if pd.notna(row['confidence']) else 50
                
                # Determine bucket
                score_bucket = determine_score_bucket(base_score)
                option_quality = determine_option_quality(option_score)
                
                # Determine confidence level
                if confidence >= 60:
                    confidence_bucket = "High"
                elif confidence >= 40:
                    confidence_bucket = "Medium"
                else:
                    confidence_bucket = "Low"
                
                # Check NO-TRADE gate
                is_no_trade_gate = option_score < -0.3
                
                save_daily_score(
                    session,
                    symbol=row['symbol'],
                    trade_date=today,
                    base_score=base_score,
                    score_bucket=score_bucket,
                    option_score=option_score,
                    option_quality=option_quality,
                    is_no_trade_gate=is_no_trade_gate,
                    suggested_strategy=row.get('strategy', None),
                    confidence_level=confidence,
                    confidence_bucket=confidence_bucket
                )
                saved_count += 1
            except Exception as e:
                print(f"   ❌ Error saving {row.get('symbol', 'Unknown')}: {str(e)[:50]}")
        
        print(f"\n✅ Saved {saved_count}/{len(df)} daily scores to database")
        close_session(session)
        
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = load_csv_to_db()
    sys.exit(0 if success else 1)
