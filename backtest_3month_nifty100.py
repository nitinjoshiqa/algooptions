#!/usr/bin/env python3
"""
3-Month NIFTY100 Backtest
Validates the scoring framework on historical data
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

from backtesting.trade_simulator import TradeSimulator, Trade


def load_nifty100_scores(screener_module):
    """Extract scoring function from main screener"""
    # Import the scoring logic
    import importlib.util
    spec = importlib.util.spec_from_file_location("nifty_bearnness_v2", 
                                                    "nifty_bearnness_v2.py")
    screener = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(screener)
    return screener


def calculate_signals(df, threshold=0.05):
    """
    Generate buy/sell signals based on historical data
    Returns DataFrame with signals
    """
    if df is None or df.empty or len(df) < 50:
        return None
    
    df = df.copy()
    
    # Calculate technical indicators
    df['SMA20'] = df['Close'].rolling(20).mean()
    df['SMA50'] = df['Close'].rolling(50).mean()
    df['RSI'] = calculate_rsi(df['Close'], 14)
    df['ATR'] = calculate_atr(df, 14)
    
    # Basic scoring logic (simplified from nifty_bearnness_v2.py)
    signals = []
    for i in range(50, len(df)):
        current = df.iloc[i]
        
        # Price above MA50 and MA20 above MA50 = Bullish
        score = 0
        if current['Close'] > current['SMA20'] > current['SMA50']:
            score += 0.3
        
        # RSI oversold/overbought
        if current['RSI'] < 30:
            score += 0.2  # Oversold = potential long
        elif current['RSI'] > 70:
            score -= 0.2  # Overbought = potential short
        
        # Volume trend (simplified)
        if i > 0:
            vol_trend = df.iloc[i]['Volume'] - df.iloc[i-1]['Volume']
            if vol_trend > 0 and score > 0:
                score += 0.1
        
        # Generate signal
        signal = 0
        if score > threshold:
            signal = 1  # BUY
        elif score < -threshold:
            signal = -1  # SELL
        
        signals.append({
            'date': df.index[i],
            'close': current['Close'],
            'signal': signal,
            'score': score,
            'atr': current['ATR'],
            'sma20': current['SMA20'],
            'sma50': current['SMA50'],
            'rsi': current['RSI']
        })
    
    return pd.DataFrame(signals)


def calculate_rsi(prices, period=14):
    """Calculate RSI indicator"""
    deltas = np.diff(prices)
    seed = deltas[:period+1]
    up = seed[seed >= 0].sum() / period
    down = -seed[seed < 0].sum() / period
    rs = up / down if down != 0 else 1
    rsi = np.zeros_like(prices)
    rsi[:period] = 100. - 100. / (1. + rs)
    
    for i in range(period, len(prices)):
        delta = deltas[i-1]
        if delta > 0:
            upval = delta
            downval = 0.
        else:
            upval = 0.
            downval = -delta
        
        up = (up * (period - 1) + upval) / period
        down = (down * (period - 1) + downval) / period
        rs = up / down if down != 0 else 1
        rsi[i] = 100. - 100. / (1. + rs)
    
    return rsi


def calculate_atr(df, period=14):
    """Calculate Average True Range"""
    high_low = df['High'] - df['Low']
    high_close = abs(df['High'] - df['Close'].shift())
    low_close = abs(df['Low'] - df['Close'].shift())
    
    ranges = pd.concat([high_low, high_close, low_close], axis=1)
    true_range = ranges.max(axis=1)
    atr = true_range.rolling(period).mean()
    
    return atr


def simulate_trades(signals_df, initial_capital=100000, risk_per_trade=0.02):
    """
    Simulate trades based on signals
    Returns trade results and statistics
    """
    if signals_df is None or signals_df.empty:
        return None
    
    simulator = TradeSimulator(initial_capital, risk_per_trade)
    trades_list = []
    
    for i in range(len(signals_df)):
        signal = signals_df.iloc[i]
        
        if signal['signal'] == 1:  # BUY signal
            # Calculate stop loss and target
            stop_loss = signal['close'] - (signal['atr'] * 2)
            target = signal['close'] + (signal['atr'] * 3)
            
            position = {
                'entry_date': signal['date'],
                'entry_price': signal['close'],
                'stop_loss': stop_loss,
                'target': target,
                'direction': 'long',
                'atr': signal['atr'],
                'score': signal['score']
            }
            
            # Find exit (next 20 days or SL/target hit)
            for j in range(i+1, min(i+20, len(signals_df))):
                exit_signal = signals_df.iloc[j]
                
                if exit_signal['close'] <= stop_loss:
                    # Stop loss hit
                    exit_price = stop_loss
                    exit_reason = 'stop_loss'
                    break
                elif exit_signal['close'] >= target:
                    # Target hit
                    exit_price = target
                    exit_reason = 'target'
                    break
                elif exit_signal['signal'] == -1:
                    # Opposite signal
                    exit_price = exit_signal['close']
                    exit_reason = 'signal'
                    break
            else:
                # Time exit (20 days elapsed)
                exit_signal = signals_df.iloc[min(i+20, len(signals_df)-1)]
                exit_price = exit_signal['close']
                exit_reason = 'time'
                j = min(i+20, len(signals_df)-1)
            
            # Calculate trade metrics
            pnl = exit_price - position['entry_price']
            pnl_pct = (pnl / position['entry_price']) * 100
            
            trade = {
                'entry_date': position['entry_date'],
                'exit_date': signals_df.iloc[j]['date'],
                'symbol': 'NIFTY100',
                'direction': position['direction'],
                'entry_price': position['entry_price'],
                'exit_price': exit_price,
                'stop_loss': position['stop_loss'],
                'target': position['target'],
                'pnl': pnl,
                'pnl_pct': pnl_pct,
                'exit_reason': exit_reason,
                'score': position['score'],
                'hold_days': j - i
            }
            
            trades_list.append(trade)
    
    return pd.DataFrame(trades_list)


def run_backtest():
    """Execute 3-month backtest"""
    
    print("\n" + "="*70)
    print("🔍 NIFTY100 3-MONTH BACKTEST")
    print("="*70 + "\n")
    
    # Date range: 3 months ago to today
    end_date = datetime.now()
    start_date = end_date - timedelta(days=90)
    
    print(f"Period: {start_date.date()} to {end_date.date()}")
    print(f"Duration: 3 months (~90 days)")
    
    # Load NIFTY100 constituents
    print("\n📂 Loading NIFTY100 constituents...")
    constituents_file = Path("data/constituents/nifty100_constituents.txt")
    
    if not constituents_file.exists():
        print(f"❌ File not found: {constituents_file}")
        return
    
    with open(constituents_file) as f:
        symbols = [line.strip() for line in f if line.strip()]
    
    print(f"✅ Loaded {len(symbols)} symbols")
    
    # Download historical data
    print(f"\n📊 Downloading {len(symbols)} stocks for 3 months...")
    all_trades = []
    successful = 0
    failed = 0
    
    for idx, symbol in enumerate(symbols, 1):
        try:
            print(f"  [{idx}/{len(symbols)}] {symbol}...", end=" ", flush=True)
            
            # Download data
            ticker = yf.Ticker(f"{symbol}.NS")
            df = ticker.history(start=start_date, end=end_date)
            
            if df.empty or len(df) < 30:
                print("⚠️ Insufficient data")
                failed += 1
                continue
            
            # Generate signals
            signals_df = calculate_signals(df)
            
            if signals_df is None or signals_df.empty:
                print("⚠️ No signals")
                failed += 1
                continue
            
            # Simulate trades
            trades_df = simulate_trades(signals_df)
            
            if trades_df is not None and not trades_df.empty:
                trades_df['symbol'] = symbol
                all_trades.append(trades_df)
                print(f"✅ {len(trades_df)} trades")
                successful += 1
            else:
                print("⚠️ No trades")
                failed += 1
                
        except Exception as e:
            print(f"❌ Error: {str(e)[:50]}")
            failed += 1
    
    print(f"\n✅ Successfully processed: {successful} stocks")
    print(f"⚠️ Failed/Skipped: {failed} stocks")
    
    if not all_trades:
        print("\n❌ No trades generated. Backtest inconclusive.")
        return
    
    # Combine all trades
    all_trades_df = pd.concat(all_trades, ignore_index=True)
    
    # Calculate statistics
    print("\n" + "="*70)
    print("📈 BACKTEST RESULTS")
    print("="*70 + "\n")
    
    total_trades = len(all_trades_df)
    winning_trades = len(all_trades_df[all_trades_df['pnl'] > 0])
    losing_trades = len(all_trades_df[all_trades_df['pnl'] <= 0])
    
    win_rate = (winning_trades / total_trades * 100) if total_trades > 0 else 0
    avg_win = all_trades_df[all_trades_df['pnl'] > 0]['pnl_pct'].mean() if winning_trades > 0 else 0
    avg_loss = all_trades_df[all_trades_df['pnl'] <= 0]['pnl_pct'].mean() if losing_trades > 0 else 0
    
    total_pnl = all_trades_df['pnl'].sum()
    total_pnl_pct = all_trades_df['pnl_pct'].sum()
    
    # Risk/Reward
    profit_factor = abs(all_trades_df[all_trades_df['pnl'] > 0]['pnl'].sum() / 
                       all_trades_df[all_trades_df['pnl'] <= 0]['pnl'].sum()) if losing_trades > 0 else 0
    
    # Sharpe ratio (simplified)
    returns = all_trades_df['pnl_pct'].values
    sharpe = (np.mean(returns) / np.std(returns) * np.sqrt(252)) if np.std(returns) > 0 else 0
    
    print(f"Total Trades:        {total_trades}")
    print(f"Winning Trades:      {winning_trades} ({win_rate:.1f}%)")
    print(f"Losing Trades:       {losing_trades}")
    print(f"\nAverage Win:         {avg_win:.2f}%")
    print(f"Average Loss:        {avg_loss:.2f}%")
    print(f"Win/Loss Ratio:      {abs(avg_win/avg_loss) if avg_loss != 0 else 0:.2f}x")
    
    print(f"\nTotal P&L:           ₹{total_pnl:,.0f}")
    print(f"Total Return %:      {total_pnl_pct:.2f}%")
    print(f"Profit Factor:       {profit_factor:.2f}x")
    print(f"Sharpe Ratio:        {sharpe:.2f}")
    
    # Drawdown
    cumulative_pnl = all_trades_df['pnl'].cumsum()
    running_max = cumulative_pnl.cummax()
    drawdown = (cumulative_pnl - running_max) / running_max
    max_drawdown = drawdown.min() * 100
    print(f"Max Drawdown:        {max_drawdown:.2f}%")
    
    # Save detailed results
    output_file = Path("reports/backtest_results_3month.csv")
    output_file.parent.mkdir(exist_ok=True)
    all_trades_df.to_csv(output_file, index=False)
    print(f"\n💾 Detailed trades saved to: {output_file}")
    
    # Summary file
    summary = {
        'backtest_period': f"{start_date.date()} to {end_date.date()}",
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
        'max_drawdown_pct': float(max_drawdown)
    }
    
    summary_file = Path("reports/backtest_summary_3month.json")
    with open(summary_file, 'w') as f:
        json.dump(summary, f, indent=2)
    
    print(f"📊 Summary saved to: {summary_file}")
    
    # Verdict
    print("\n" + "="*70)
    print("🎯 VERDICT")
    print("="*70)
    
    if win_rate >= 55 and profit_factor >= 1.5 and max_drawdown >= -20:
        print("\n✅ FRAMEWORK IS PROMISING")
        print("   • Win rate > 55%: Good signal quality")
        print("   • Profit factor > 1.5x: More gains than losses")
        print("   • Drawdown acceptable: Risk-controlled")
        print("\n→ Worth automating and live trading")
    elif win_rate >= 50 and profit_factor >= 1.0:
        print("\n⚠️ FRAMEWORK SHOWS POTENTIAL")
        print("   • Win rate borderline (50%+)")
        print("   • Needs optimization")
        print("\n→ Tweak scoring weights and retry")
    else:
        print("\n❌ FRAMEWORK NEEDS MAJOR REVISION")
        print("   • Win rate < 50%: More losers than winners")
        print("   • Profit factor < 1.0: Losses exceed gains")
        print("\n→ Review scoring logic and indicators")
    
    print("\n" + "="*70 + "\n")
    
    return summary


if __name__ == "__main__":
    try:
        results = run_backtest()
    except KeyboardInterrupt:
        print("\n\n⏹️ Backtest interrupted by user")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
