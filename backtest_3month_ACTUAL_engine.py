#!/usr/bin/env python3
"""
3-Month NIFTY100 Backtest - USING ACTUAL SCORING ENGINE
This backtest uses the real BearnessScoringEngine from nifty_bearnness_v2.py
"""

import pandas as pd
import numpy as np
import yfinance as yf
from datetime import datetime, timedelta
import json
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from core.scoring_engine import BearnessScoringEngine


def simulate_trades_from_signals(symbol, start_date, end_date, engine, conf_threshold=40, score_threshold=0.05):
    """
    Simulate trades using ACTUAL scoring engine signals
    
    Args:
        symbol: Stock symbol
        start_date: Start date
        end_date: End date
        engine: BearnessScoringEngine instance
        conf_threshold: Minimum confidence (default 40%)
        score_threshold: Minimum absolute score (default 0.05)
    
    Returns:
        List of trades
    """
    
    # Download daily data
    try:
        ticker = yf.Ticker(f"{symbol}.NS")
        df = ticker.history(start=start_date, end=end_date)
        
        if df.empty or len(df) < 50:
            return None
    except:
        return None
    
    trades = []
    
    # For each date, compute score using the actual engine
    for i in range(50, len(df)):
        current_date = df.index[i]
        
        try:
            # Get score from actual engine (this is the REAL strategy)
            score_result = engine.compute_score(symbol)
            
            if not score_result or score_result.get('status') != 'OK':
                continue
            
            final_score = score_result.get('final_score')
            confidence = score_result.get('confidence', 0) or 0
            
            # FILTER: Only trade if confidence >= threshold AND |score| >= threshold
            if confidence < conf_threshold or abs(final_score) < score_threshold:
                continue
            
            # Price at this date
            entry_price = df.iloc[i]['Close']
            atr = score_result.get('atr', entry_price * 0.02)  # Default 2% if missing
            
            # Entry signal
            if final_score < -score_threshold:
                direction = 'short'
                stop_loss = entry_price + (atr * 2)
                target = entry_price - (atr * 3)
            elif final_score > score_threshold:
                direction = 'long'
                stop_loss = entry_price - (atr * 2)
                target = entry_price + (atr * 3)
            else:
                continue
            
            # Find exit in next 20 days
            exit_price = None
            exit_reason = None
            
            for j in range(i+1, min(i+21, len(df))):
                exit_date = df.index[j]
                price = df.iloc[j]['Close']
                
                if direction == 'long':
                    if price <= stop_loss:
                        exit_price = stop_loss
                        exit_reason = 'stop_loss'
                        break
                    elif price >= target:
                        exit_price = target
                        exit_reason = 'target'
                        break
                else:  # short
                    if price >= stop_loss:
                        exit_price = stop_loss
                        exit_reason = 'stop_loss'
                        break
                    elif price <= target:
                        exit_price = target
                        exit_reason = 'target'
                        break
            else:
                # Time exit (20 days elapsed)
                exit_price = df.iloc[min(i+20, len(df)-1)]['Close']
                exit_date = df.index[min(i+20, len(df)-1)]
                exit_reason = 'time'
                j = min(i+20, len(df)-1)
            
            if exit_price is None:
                continue
            
            # Calculate P&L
            if direction == 'long':
                pnl = exit_price - entry_price
            else:
                pnl = entry_price - exit_price
            
            pnl_pct = (pnl / entry_price) * 100
            
            trade = {
                'entry_date': current_date.strftime('%Y-%m-%d'),
                'exit_date': exit_date.strftime('%Y-%m-%d'),
                'symbol': symbol,
                'direction': direction,
                'entry_price': entry_price,
                'exit_price': exit_price,
                'stop_loss': stop_loss,
                'target': target,
                'pnl': pnl,
                'pnl_pct': pnl_pct,
                'exit_reason': exit_reason,
                'confidence': confidence,
                'score': final_score,
                'atr': atr
            }
            
            trades.append(trade)
        
        except Exception as e:
            # Skip errors for individual stocks
            continue
    
    return trades if trades else None


def run_backtest_with_actual_engine():
    """Execute backtest using ACTUAL scoring engine"""
    
    print("\n" + "="*80)
    print("🔍 NIFTY100 3-MONTH BACKTEST (USING ACTUAL SCORING ENGINE)")
    print("="*80 + "\n")
    
    # Date range: 3 months ago to today
    end_date = datetime.now()
    start_date = end_date - timedelta(days=90)
    
    print(f"Period: {start_date.date()} to {end_date.date()}")
    print(f"Duration: 3 months (~90 days)")
    
    # Initialize the ACTUAL scoring engine
    print("\n🔧 Initializing BearnessScoringEngine (swing mode, yfinance)...")
    engine = BearnessScoringEngine(mode='swing', use_yf=True, force_yf=True, quick_mode=False)
    
    # Load NIFTY100 constituents
    print("\n📂 Loading NIFTY100 constituents...")
    constituents_file = Path("data/constituents/nifty100_constituents.txt")
    
    if not constituents_file.exists():
        print(f"❌ File not found: {constituents_file}")
        return
    
    with open(constituents_file) as f:
        symbols = [line.strip() for line in f if line.strip()]
    
    print(f"✅ Loaded {len(symbols)} symbols")
    
    # Run backtest
    print(f"\n📊 Running backtest on {len(symbols)} stocks...")
    print("⚠️ This may take 10-15 minutes (computing real scores for 90 days)...\n")
    
    all_trades = []
    successful = 0
    failed = 0
    
    for idx, symbol in enumerate(symbols, 1):
        try:
            print(f"  [{idx}/{len(symbols)}] {symbol}...", end=" ", flush=True)
            
            # Simulate trades using ACTUAL engine
            symbol_trades = simulate_trades_from_signals(
                symbol, 
                start_date, 
                end_date, 
                engine,
                conf_threshold=40,  # Only trades with confidence > 40%
                score_threshold=0.05  # Only |score| > 0.05
            )
            
            if symbol_trades:
                all_trades.extend(symbol_trades)
                print(f"✅ {len(symbol_trades)} trades")
                successful += 1
            else:
                print("⚠️ No trades")
                failed += 1
                
        except Exception as e:
            print(f"❌ Error")
            failed += 1
    
    print(f"\n✅ Successfully processed: {successful} stocks")
    print(f"⚠️ Failed/Skipped: {failed} stocks")
    
    if not all_trades:
        print("\n❌ No trades generated. Backtest inconclusive.")
        return
    
    # Combine all trades
    all_trades_df = pd.DataFrame(all_trades)
    
    # Calculate statistics
    print("\n" + "="*80)
    print("📈 BACKTEST RESULTS (WITH ACTUAL SCORING ENGINE)")
    print("="*80 + "\n")
    
    total_trades = len(all_trades_df)
    winning_trades = len(all_trades_df[all_trades_df['pnl'] > 0])
    losing_trades = len(all_trades_df[all_trades_df['pnl'] <= 0])
    
    win_rate = (winning_trades / total_trades * 100) if total_trades > 0 else 0
    avg_win = all_trades_df[all_trades_df['pnl'] > 0]['pnl_pct'].mean() if winning_trades > 0 else 0
    avg_loss = all_trades_df[all_trades_df['pnl'] <= 0]['pnl_pct'].mean() if losing_trades > 0 else 0
    
    total_pnl = all_trades_df['pnl'].sum()
    total_pnl_pct = all_trades_df['pnl_pct'].sum()
    
    # Profit factor
    profit_factor = abs(all_trades_df[all_trades_df['pnl'] > 0]['pnl'].sum() / 
                       all_trades_df[all_trades_df['pnl'] <= 0]['pnl'].sum()) if losing_trades > 0 else 0
    
    # Sharpe ratio
    returns = all_trades_df['pnl_pct'].values
    sharpe = (np.mean(returns) / np.std(returns) * np.sqrt(252)) if np.std(returns) > 0 else 0
    
    # Avg confidence of winning vs losing trades
    avg_conf_winners = all_trades_df[all_trades_df['pnl'] > 0]['confidence'].mean() if winning_trades > 0 else 0
    avg_conf_losers = all_trades_df[all_trades_df['pnl'] <= 0]['confidence'].mean() if losing_trades > 0 else 0
    
    print(f"Backtest Settings:")
    print(f"  Min Confidence:      40%")
    print(f"  Min |Score|:         0.05")
    print(f"  Hold Period:         Up to 20 days (or SL/target hit)")
    
    print(f"\nTrade Statistics:")
    print(f"Total Trades:        {total_trades}")
    print(f"Winning Trades:      {winning_trades} ({win_rate:.1f}%)")
    print(f"Losing Trades:       {losing_trades}")
    print(f"\nAverage Win:         {avg_win:.2f}%")
    print(f"Average Loss:        {avg_loss:.2f}%")
    print(f"Win/Loss Ratio:      {abs(avg_win/avg_loss) if avg_loss != 0 else 0:.2f}x")
    
    print(f"\nP&L Metrics:")
    print(f"Total P&L:           ₹{total_pnl:,.0f}")
    print(f"Total Return %:      {total_pnl_pct:.2f}%")
    print(f"Profit Factor:       {profit_factor:.2f}x")
    print(f"Sharpe Ratio:        {sharpe:.2f}")
    
    # Drawdown
    cumulative_pnl = all_trades_df['pnl'].cumsum()
    running_max = cumulative_pnl.cummax()
    drawdown = (cumulative_pnl - running_max) / running_max
    max_drawdown = drawdown.min() * 100
    print(f"Max Drawdown:        {max_drawdown:.2f}%")
    
    print(f"\nConfidence Analysis:")
    print(f"Avg Conf (Winners):  {avg_conf_winners:.1f}%")
    print(f"Avg Conf (Losers):   {avg_conf_losers:.1f}%")
    print(f"Confidence Edge:     {avg_conf_winners - avg_conf_losers:.1f}%")
    
    # Save results
    output_file = Path("reports/backtest_results_ACTUAL_3month.csv")
    output_file.parent.mkdir(exist_ok=True)
    all_trades_df.to_csv(output_file, index=False)
    print(f"\n💾 Detailed trades saved to: {output_file}")
    
    # Summary file
    summary = {
        'backtest_period': f"{start_date.date()} to {end_date.date()}",
        'engine_type': 'ACTUAL BearnessScoringEngine',
        'conf_threshold': 40,
        'score_threshold': 0.05,
        'total_stocks': len(symbols),
        'stocks_processed': successful,
        'total_trades': int(total_trades),
        'winning_trades': int(winning_trades),
        'losing_trades': int(losing_trades),
        'win_rate_pct': float(win_rate),
        'avg_win_pct': float(avg_win),
        'avg_loss_pct': float(avg_loss),
        'total_pnl': float(total_pnl),
        'total_pnl_pct': float(total_pnl_pct),
        'profit_factor': float(profit_factor),
        'sharpe_ratio': float(sharpe),
        'max_drawdown_pct': float(max_drawdown),
        'avg_confidence_winners': float(avg_conf_winners),
        'avg_confidence_losers': float(avg_conf_losers)
    }
    
    summary_file = Path("reports/backtest_summary_ACTUAL_3month.json")
    with open(summary_file, 'w') as f:
        json.dump(summary, f, indent=2)
    
    print(f"📊 Summary saved to: {summary_file}")
    
    # Verdict
    print("\n" + "="*80)
    print("🎯 VERDICT")
    print("="*80)
    
    if win_rate >= 55 and profit_factor >= 1.5 and max_drawdown >= -20:
        print("\n✅ FRAMEWORK IS PROMISING")
        print("   • Win rate > 55%: Good signal quality from real engine")
        print("   • Profit factor > 1.5x: Strong positive edge")
        print("   • Drawdown acceptable: Risk-controlled")
        print("\n→ Worth automating and live trading")
    elif win_rate >= 50 and profit_factor >= 1.0:
        print("\n⚠️ FRAMEWORK SHOWS POTENTIAL")
        print("   • Win rate borderline (50%+)")
        print("   • Needs optimization")
        print("\n→ Tweak confidence threshold or score filters")
    else:
        print("\n❌ FRAMEWORK NEEDS MAJOR REVISION")
        print("   • Win rate < 50%: More losers than winners")
        print("   • Profit factor < 1.0: Losses exceed gains")
        print("\n→ Review scoring engine or apply Tier 1 fixes")
    
    print("\n" + "="*80 + "\n")
    
    return summary


if __name__ == "__main__":
    try:
        results = run_backtest_with_actual_engine()
    except KeyboardInterrupt:
        print("\n\n⏹️ Backtest interrupted by user")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
