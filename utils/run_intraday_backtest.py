"""
Run Intraday Backtest - Test screener on historical intraday data

Usage:
    python run_intraday_backtest.py --universe nifty --days 30 --output intraday_nifty.html
    python run_intraday_backtest.py --symbols RELIANCE,INFY --days 60
"""

import argparse
from datetime import datetime
from backtesting.intraday_backtest_engine import IntradayBacktestEngine
from core.universe import UniverseManager


def load_universe(universe_name):
    """Load stock symbols from universe file"""
    universe_files = {
        'nifty': 'nifty_constituents.txt',
        'banknifty': 'banknifty_constituents.txt',
        'nifty100': 'nifty100_constituents.txt',
    }
    
    filename = universe_files.get(universe_name.lower())
    if not filename:
        return []
    
    try:
        with open(filename, 'r') as f:
            symbols = [line.strip() for line in f if line.strip()]
        return symbols
    except FileNotFoundError:
        print(f"[!] Universe file not found: {filename}")
        return []


def main():
    parser = argparse.ArgumentParser(description='Intraday backtest for screener')
    parser.add_argument('--symbols', type=str, help='Comma-separated symbols')
    parser.add_argument('--universe', type=str, help='Universe name (nifty, banknifty)')
    parser.add_argument('--days', type=int, default=30, help='Days of history (max 60 for 5m data)')
    parser.add_argument('--capital', type=float, default=100000, help='Initial capital')
    parser.add_argument('--risk', type=float, default=0.01, help='Risk per trade (default: 1%)')
    parser.add_argument('--output', type=str, default='intraday_backtest.html', help='Output file')
    parser.add_argument('--use-breeze', action='store_true', help='Use Breeze API for data (faster, more reliable)')
    parser.add_argument('--limit', type=int, default=10, help='Max symbols to process (<=0 for all)')
    
    args = parser.parse_args()
    
    # Get symbols
    if args.symbols:
        symbols = [s.strip() for s in args.symbols.split(',')]
    elif args.universe:
        symbols = load_universe(args.universe)
    else:
        print("[X] Error: Provide either --symbols or --universe")
        return
    
    if not symbols:
        print("[X] No symbols to backtest")
        return
    
    # Limit days to 60 (yfinance 5m data limit)
    days = min(args.days, 60)
    
    print(f"\n{'='*80}")
    print(f"  SWING TRADING BACKTEST (1-2 Days)")
    print(f"{'='*80}")
    print(f"  Symbols:        {len(symbols)} stocks")
    print(f"  History:        Last {days} days (5-minute bars)")
    print(f"  Initial Capital: Rs {args.capital:,.0f}")
    print(f"  Risk per Trade: {args.risk*100:.1f}%")
    print(f"{'='*80}\n")
    
    if days < args.days:
        print(f"[!] Note: Reduced to {days} days (yfinance 5m limit)\n")
    
    # Initialize engine
    engine = IntradayBacktestEngine(
        initial_capital=args.capital,
        risk_per_trade=args.risk,
        use_breeze=args.use_breeze
    )
    
    # Run backtest for each symbol
    limit = args.limit
    process_count = len(symbols) if (limit is None or limit <= 0) else min(len(symbols), limit)
    for i, symbol in enumerate(symbols[:process_count], 1):
        print(f"[{i}/{process_count}] {symbol}")
        try:
            engine.run_backtest(symbol, days=days)
        except Exception as e:
            print(f"  [X] Error: {e}")
    
    # Get summary
    summary = engine.get_summary()
    
    print(f"\n{'='*80}")
    print(f"  BACKTEST RESULTS")
    print(f"{'='*80}")
    print(f"  Total Trades:    {summary.get('total_trades', 0)}")
    print(f"  Winning Trades:  {summary.get('winning_trades', 0)}")
    print(f"  Losing Trades:   {summary.get('losing_trades', 0)}")
    print(f"  Win Rate:        {summary.get('win_rate', 0):.1f}%")
    print(f"  Total P&L:       Rs {summary.get('total_pnl', 0):,.0f}")
    print(f"  Final Capital:   Rs {summary.get('final_capital', 0):,.0f}")
    print(f"  Return:          {summary.get('return_pct', 0):.2f}%")
    print(f"  Profit Factor:   {summary.get('profit_factor', 0):.2f}")
    print(f"  Avg R-Multiple:  {summary.get('avg_r_multiple', 0):.2f}")
    print(f"  Avg Hold:        {summary.get('avg_hold_minutes', 0):.0f} minutes")
    print(f"\n  Exit Breakdown:")
    total_trades = summary.get('total_trades', 0)
    def pct(count):
        return (count / total_trades * 100) if total_trades > 0 else 0.0
    targets = summary.get('target_exits', 0)
    stops = summary.get('stop_exits', 0)
    time_exit = summary.get('time_exits', 0)
    vwap = summary.get('vwap_exits', 0)
    print(f"    Targets:       {targets} ({pct(targets):.1f}%)")
    print(f"    Stops:         {stops} ({pct(stops):.1f}%)")
    print(f"    VWAP Recross:  {vwap} ({pct(vwap):.1f}%)")
    print(f"    Time (2-day):  {time_exit} ({pct(time_exit):.1f}%)")
    print(f"{'='*80}\n")
    
    # Interpretation
    if summary.get('total_trades', 0) == 0:
        print("[!] No trades generated. Possible reasons:")
        print("  - Signal thresholds too strict")
        print("  - Market was ranging")
        print("  - Data quality issues")
    elif summary.get('win_rate', 0) > 50 and summary.get('return_pct', 0) > 0:
        print("[+] POSITIVE RESULTS:")
        print("  - Win rate above 50%")
        print("  - Positive returns")
        print("  - Strategy shows promise!")
    elif summary.get('return_pct', 0) > 0:
        print("[!] MARGINAL RESULTS:")
        print("  - Positive but low win rate")
        print("  - Needs optimization")
    else:
        print("[X] NEGATIVE RESULTS:")
        print("  - Strategy needs work")
        print("  - Review entry/exit logic")
    
    print(f"\nNote: This is a simplified backtest.")
    print(f"   For production:")
    print(f"   - Use actual screener scoring logic")
    print(f"   - Get more historical data (Breeze API)")
    print(f"   - Add slippage modeling")
    print(f"   - Test different parameters")


if __name__ == '__main__':
    main()
