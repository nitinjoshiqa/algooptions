"""
Backtest Institutional Context Scoring Criteria
Tests the effectiveness of the scoring logic over historical data
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from pathlib import Path
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.scoring_engine import BearnessScoringEngine
from nifty_bearnness_v2 import compute_context_score
from core.universe import UniverseManager

def load_universe(universe_name='nifty200'):
    """Load stock universe"""
    return UniverseManager.load(universe=universe_name, fetch_if_missing=False)

def calculate_scores_for_date(target_date, symbols):
    """Calculate scores for all symbols as of target_date"""
    engine = BearnessScoringEngine(mode='swing', use_yf=True, quick_mode=True)

    results = []
    for symbol, _ in symbols[:20]:  # Limit to 20 for testing
        try:
            # Get current score (simulating historical)
            result = engine.compute_score(symbol)
            if result and result.get('status') == 'OK':
                # Calculate context score and momentum
                context_score, context_momentum = compute_context_score({
                    'vwap_score': result.get('vwap_score', 0),
                    'volume_score': result.get('volume_score', 0),
                    'market_regime': result.get('market_regime', 'neutral'),
                    'risk_level': 'LOW' if result.get('confidence', 0) > 70 else 'MEDIUM'
                })

                result['context_score'] = context_score
                result['context_momentum'] = context_momentum
                result['date'] = target_date
                results.append(result)

        except Exception as e:
            print(f"Error scoring {symbol}: {e}")
            continue

    return results

def filter_by_criteria(results):
    """Filter results based on user criteria - LIGHTENED"""
    filtered = []
    for r in results:
        try:
            confidence = r.get('confidence', 0)
            final_score = abs(r.get('final_score', 0))
            context_momentum = r.get('context_momentum', 0)
            # For now, assume LOW risk if confidence > 70
            risk_zone = 'LOW' if confidence > 70 else 'MEDIUM'
            context_score = r.get('context_score', 0)
            
            print(f"  {r['symbol']}: conf={confidence:.1f}, score={final_score:.3f}, momentum={context_momentum:.3f}, ctx_score={context_score:.3f}, risk={risk_zone}")
            
            # ORIGINAL STRICT criteria (modified)
            if (confidence > 80 and  # was 50
                final_score > 0.35 and  # was 0.1
                context_score > 2.8):  # new condition, was 2-5 range
                filtered.append(r)
                
        except Exception as e:
            print(f"Error filtering {r.get('symbol', 'unknown')}: {e}")
            continue
    
    return filtered

def simulate_trading(filtered_results, hold_days=1, current_date=None):
    """Simulate holding filtered stocks for hold_days and calculate actual returns"""
    if not filtered_results:
        return 0.0, 0

    total_return = 0.0
    successful_trades = 0

    for result in filtered_results:
        symbol = result['symbol']
        entry_price = result['price']

        try:
            # Fetch price after hold_days
            exit_date = current_date + timedelta(days=hold_days)
            import yfinance as yf

            ticker = yf.Ticker(f"{symbol}.NS")
            hist = ticker.history(start=exit_date, end=exit_date + timedelta(days=1))

            if not hist.empty:
                exit_price = hist['Close'].iloc[0]
                trade_return = (exit_price - entry_price) / entry_price
                total_return += trade_return
                successful_trades += 1
            else:
                # If no data, assume 0 return
                successful_trades += 1

        except Exception as e:
            print(f"Error calculating return for {symbol}: {e}")
            continue

    avg_return = total_return / successful_trades if successful_trades > 0 else 0
    return avg_return, successful_trades

def run_backtest(start_date, end_date, universe_name='nifty200'):
    """Run backtest from start_date to end_date"""
    symbols = load_universe(universe_name)
    print(f"Loaded {len(symbols)} symbols from {universe_name}")

    current_date = pd.to_datetime(start_date)
    end = pd.to_datetime(end_date)

    total_return = 0.0
    trade_count = 0

    while current_date <= end:
        if current_date.weekday() < 5:  # Monday to Friday
            print(f"Processing {current_date.date()}...")

            # Calculate scores
            results = calculate_scores_for_date(current_date, symbols)

            # Filter by criteria
            filtered = filter_by_criteria(results)
            print(f"  Found {len(filtered)} qualifying stocks")

            # Simulate trading
            if filtered:
                daily_return, trades = simulate_trading(filtered, hold_days=1, current_date=current_date)
                total_return += daily_return
                trade_count += trades
                print(f"  Daily return: {daily_return:.4f} from {trades} trades")

        current_date += timedelta(days=1)

    # Calculate metrics
    total_days = (end - pd.to_datetime(start_date)).days
    annual_return = (1 + total_return) ** (365 / total_days) - 1 if total_days > 0 else 0

    print("\nBacktest Results:")
    print(f"Total return: {total_return:.4f}")
    print(f"Annual return: {annual_return:.4f}")
    print(f"Total trades: {trade_count}")
    print(f"Avg return per trade: {total_return/trade_count:.4f}" if trade_count > 0 else "No trades")

if __name__ == '__main__':
    # Test for last 7 days (lightened)
    end_date = datetime.now().date()
    start_date = end_date - timedelta(days=7)

    run_backtest(start_date, end_date)