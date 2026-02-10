#!/usr/bin/env python3
"""
Analyze Robustness Filter Effectiveness
Shows which filters are helping and which patterns benefit most
"""

import sys
sys.path.insert(0, '.')
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from backtesting.backtest_engine import BacktestEngine
from backtesting.trade_simulator import TradeSimulator

print("=" * 100)
print("  FILTER EFFECTIVENESS ANALYSIS")
print("=" * 100)
print()

# Configuration
symbol = 'INFY.NS'
end_date = datetime.now()
start_date = end_date - timedelta(days=180)  # 6 months

print(f"Analyzing: {symbol}")
print(f"Period: {start_date.date()} to {end_date.date()}")
print()

try:
    # Run backtest
    print("Running backtest with all filters..."); print()
    engine = BacktestEngine(start_date=start_date, end_date=end_date, symbols=[symbol])
    result = engine.run_backtest(symbol)
    
    if result is None or 'signals' not in result:
        print("❌ No backtest results available")
        sys.exit(1)
    
    signals = result['signals']
    print(f"✓ Generated {len(signals)} signals\n")
    
    # Analyze signals
    if len(signals) > 0:
        signals_df = pd.DataFrame(signals)
        
        print("1️⃣  SIGNALS BY PATTERN")
        print("-" * 100)
        for pattern in signals_df['pattern'].unique():
            count = len(signals_df[signals_df['pattern'] == pattern])
            print(f"   {pattern:20s}: {count:3d} signals")
        print()
        
        print("2️⃣  SIGNALS BY MARKET REGIME")
        print("-" * 100)
        for regime in signals_df['regime'].unique():
            count = len(signals_df[signals_df['regime'] == regime])
            pct = (count / len(signals_df)) * 100
            print(f"   {regime:20s}: {count:3d} signals ({pct:5.1f}%)")
        print()
        
        print("3️⃣  SIGNALS BY VOLATILITY")
        print("-" * 100)
        for vol in ['HIGH', 'MEDIUM', 'LOW']:
            count = len(signals_df[signals_df['volatility'] == vol])
            if count > 0:
                pct = (count / len(signals_df)) * 100
                avg_conf = signals_df[signals_df['volatility'] == vol]['confidence'].mean()
                print(f"   {vol:20s}: {count:3d} signals ({pct:5.1f}%) | Avg Confidence: {avg_conf:.0f}")
        print()
        
        print("4️⃣  CONFIDENCE LEVELS")
        print("-" * 100)
        for conf_level in [80, 85, 90]:
            count = len(signals_df[signals_df['confidence'] >= conf_level])
            pct = (count / len(signals_df)) * 100 if len(signals_df) > 0 else 0
            print(f"   Confidence >= {conf_level}: {count:3d} signals ({pct:5.1f}%)")
        print()
        
        print("5️⃣  SIGNAL STATISTICS")
        print("-" * 100)
        print(f"   Total Signals:        {len(signals_df)}")
        print(f"   Date Range:           {signals_df['date'].min()} to {signals_df['date'].max()}")
        print(f"   Avg Price Entry:      ₹{signals_df['price'].mean():.2f}")
        print(f"   Avg Stop Loss:        ₹{signals_df['stop_loss'].mean():.2f}")
        print(f"   Avg Target:           ₹{signals_df['target'].mean():.2f}")
        print(f"   Avg Confidence:       {signals_df['confidence'].mean():.1f}%")
        print()
        
        # Execute trades to see actual results
        print("6️⃣  EXECUTING TRADES WITH VOLATILITY SIZING...")
        print("-" * 100)
        sim = TradeSimulator(
            initial_capital=100000,
            daily_loss_limit=-0.02,
            max_daily_trades=5
        )
        sym_trades = sim.execute_trades(result)
        summary = sim.get_summary()
        
        print(f"   Total Trades:         {summary['total_trades']}")
        print(f"   Winning Trades:       {summary['winning_trades']}")
        print(f"   Losing Trades:        {summary['losing_trades']}")
        print(f"   Win Rate:             {summary['win_rate']:.1f}%")
        print(f"   Total P&L:            ₹{summary['total_pnl']:.2f}")
        print(f"   Final Capital:        ₹{summary['final_capital']:.2f}")
        print(f"   Return:               {summary['return_pct']:.2f}%")
        print(f"   Avg R-Multiple:       {summary['avg_r_multiple']:.2f}R")
        print(f"   Profit Factor:        {summary['profit_factor']:.2f}")
        print(f"   Avg Hold Days:        {summary['avg_hold_days']:.1f}")
        print()
        
    else:
        print("❌ No signals generated - all filtered out")
        print("   This means filters are very strict")
        print("   Consider relaxing: volume requirement, time filter, or ADX threshold")

except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

print("=" * 100)
print("  ANALYSIS COMPLETE ✓")
print("=" * 100)
print()
print("📊 NEXT STEPS:")
print("   1. Check if signals are being generated (should be 30-50 per 6 months)")
print("   2. Validate win rate is >50% (target: 60%+)")
print("   3. Check which regime has best win rate (trending should win most)")
print("   4. Verify volatility adjustment works (LOW vol = bigger positions)")
print()
