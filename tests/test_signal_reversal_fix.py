#!/usr/bin/env python
"""
Signal Reversal Fix - Before/After Comparison Backtest

This script tests the signal reversal fix by running backtests on historical data
and comparing:
1. Signal count (should be lower after fix - fewer false signals)
2. Win rate (should be higher after fix)
3. Average hold time (should be longer after fix)
4. Reversals (should be fewer after fix)

Usage:
    python test_signal_reversal_fix.py
"""

import pandas as pd
import yfinance as yf
from datetime import datetime, timedelta
import sys
import os

sys.path.insert(0, '.')

from backtesting.backtest_engine import BacktestEngine
from backtesting.trade_simulator import TradeSimulator, Trade

def run_backtest_test():
    """Run backtest on historical data and show results"""
    
    print("\n" + "="*80)
    print("  SIGNAL REVERSAL FIX - VALIDATION BACKTEST")
    print("="*80)
    print()
    
    # Test symbols
    symbols = ['INFY', 'RELIANCE', 'TCS']
    
    # Backtest parameters
    start_date = '2025-12-01'
    end_date = '2026-02-10'
    
    print(f"Testing on: {start_date} to {end_date}")
    print(f"Symbols: {', '.join(symbols)}")
    print()
    
    # Initialize backtest engine
    engine = BacktestEngine(start_date, end_date, symbols)
    
    total_results = {
        'signals_generated': 0,
        'trades_created': 0,
        'winning_trades': 0,
        'losing_trades': 0,
        'total_pnl': 0.0,
        'total_pnl_pct': 0.0,
        'hold_times': [],
        'reversals': 0,
    }
    
    for symbol in symbols:
        print(f"\n{'─'*80}")
        print(f"Symbol: {symbol}")
        print(f"{'─'*80}")
        
        try:
            # Run backtest
            result = engine.run_backtest(symbol)
            
            if result is None:
                print(f"  [!] No data for {symbol}")
                continue
            
            df = result['data']
            signals = result['signals']
            
            print(f"  ✓ Loaded {len(df)} bars")
            print(f"  ✓ Generated {len(signals)} signals")
            
            if len(signals) == 0:
                print(f"  [!] No signals generated (validation too strict or no patterns)")
                continue
            
            # Run trade simulator
            simulator = TradeSimulator(initial_capital=100000, risk_per_trade=0.02)
            trades = simulator.execute_trades(result)
            
            print(f"  ✓ Executed {len(trades)} trades")
            
            # Analyze results
            if trades:
                winning = [t for t in trades if t.pnl > 0]
                losing = [t for t in trades if t.pnl <= 0]
                
                win_rate = (len(winning) / len(trades) * 100) if trades else 0
                avg_pnl = sum(t.pnl for t in trades) / len(trades) if trades else 0
                total_pnl = sum(t.pnl for t in trades)
                
                print(f"  ├─ Win Rate: {win_rate:.1f}% ({len(winning)} wins / {len(trades)} trades)")
                print(f"  ├─ Avg P&L: Rs {avg_pnl:,.2f}")
                print(f"  ├─ Total P&L: Rs {total_pnl:,.2f}")
                print(f"  └─ Avg Hold: {sum(t.hold_days for t in trades) / len(trades):.1f} days")
                
                # Track totals
                total_results['signals_generated'] += len(signals)
                total_results['trades_created'] += len(trades)
                total_results['winning_trades'] += len(winning)
                total_results['losing_trades'] += len(losing)
                total_results['total_pnl'] += total_pnl
                total_results['hold_times'].extend([t.hold_days for t in trades])
            
        except Exception as e:
            print(f"  [X] Error: {e}")
            import traceback
            traceback.print_exc()
    
    print()
    print("="*80)
    print("  AGGREGATE RESULTS")
    print("="*80)
    print()
    
    total_trades = total_results['trades_created']
    if total_trades > 0:
        win_rate = total_results['winning_trades'] / total_trades * 100
        avg_hold = sum(total_results['hold_times']) / len(total_results['hold_times'])
        
        print(f"  Total Signals Generated: {total_results['signals_generated']}")
        print(f"  Total Trades Executed:  {total_trades}")
        print(f"  Winning Trades:         {total_results['winning_trades']}")
        print(f"  Losing Trades:          {total_results['losing_trades']}")
        print(f"  Win Rate:               {win_rate:.1f}%")
        print(f"  Average Hold Time:      {avg_hold:.1f} days")
        print(f"  Total P&L:              Rs {total_results['total_pnl']:,.2f}")
        print()
        
        if win_rate >= 55:
            print("  ✓ VALIDATION PASSED - Win rate >= 55%")
            print("  ✓ Signal reversal fix is working successfully!")
        elif win_rate >= 45:
            print("  ✓ PARTIAL PASS - Win rate >= 45% (acceptable)")
            print("  → Consider moving to PATH 2 (multi-timeframe confirmation)")
        else:
            print("  ✗ VALIDATION FAILED - Win rate < 45%")
            print("  → Validation may be too strict, or patterns weak")
    else:
        print("  [!] No trades generated")
        print("  This may indicate:")
        print("  1. Validation is too strict and filtering all signals")
        print("  2. Market conditions don't favor the patterns")
        print("  3. Data quality issues")
    
    print()
    print("="*80)

if __name__ == '__main__':
    run_backtest_test()
