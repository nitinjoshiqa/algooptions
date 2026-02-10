#!/usr/bin/env python
"""Test robustness scoring integration with HTML generation."""

import sys
sys.path.insert(0, '.')

from backtesting.backtest_engine import BacktestEngine
from exporters.csv_exporter import save_csv
from nifty_bearnness_v2 import save_html, suggest_option_strategy, STRATEGY_TOOLTIPS
import pandas as pd
from datetime import datetime

def test_robustness_backtest():
    """Run a quick backtest to test robustness scoring integration."""
    
    # Initialize backtest engine
    engine = BacktestEngine(
        start_date='2025-08-01',  # Use 6+ months history for sufficient bars
        end_date='2026-02-10',
        symbols=['RELIANCE', 'TCS', 'INFY', 'ICICIBANK', 'LT']
    )
    
    print("=" * 80)
    print("ROBUSTNESS SCORING INTEGRATION TEST")
    print("=" * 80)
    
    # Run backtest for each symbol
    all_signals = []
    for symbol in engine.symbols:
        print(f"\nTesting signal generation for {symbol}...")
        
        # Load data for symbol
        df = engine.load_historical_data(symbol)
        if df is None or len(df) < 100:
            print(f"  ✗ Not enough data for {symbol}")
            continue
        
        signals = engine.generate_signals(symbol, df)
        
        if signals:
            print(f"✓ Generated {len(signals)} signals")
            
            # Check for new fields
            first_signal = signals[0]
            fields_to_check = [
                'robustness_score', 'robustness_momentum', 'master_score',
                'final_score', 'context_score', 'context_momentum',
                'news_sentiment_score', 'master_score_tooltip'
            ]
            
            print("  New fields present:")
            for field in fields_to_check:
                if field in first_signal:
                    value = first_signal[field]
                    if isinstance(value, float):
                        print(f"    ✓ {field}: {value:.2f}")
                    else:
                        print(f"    ✓ {field}: {str(value)[:50]}")
                else:
                    print(f"    ✗ {field}: MISSING")
            
            # Print sample signal
            print(f"\n  Sample signal from {symbol}:")
            print(f"    Pattern: {first_signal.get('pattern', 'N/A')}")
            print(f"    Confidence: {first_signal.get('confidence', 'N/A')}")
            print(f"    Robustness: {first_signal.get('robustness_score', 'N/A'):.0f}/100")
            print(f"    Master Score: {first_signal.get('master_score', 'N/A'):.0f}/100")
            print(f"    Filters Passed: {first_signal.get('filters_passed', 0)}/7")
            
            all_signals.extend(signals)
        else:
            print(f"  No signals generated for {symbol}")
    
    # Convert signals to dataframe for HTML export
    if all_signals:
        print("\n" + "=" * 80)
        print(f"TOTAL SIGNALS GENERATED: {len(all_signals)}")
        print("=" * 80)
        
        # Prepare data for HTML export
        results = []
        for sig in all_signals:
            results.append({
                'symbol': sig['symbol'],
                'date': sig['date'],
                'signal': sig['signal'],
                'price': sig['price'],
                'pattern': sig['pattern'],
                'confidence': sig['confidence'],
                'final_score': sig.get('final_score', 0.70),
                'context_score': sig.get('context_score', 3.0),
                'context_momentum': sig.get('context_momentum', 0.0),
                'robustness_score': sig.get('robustness_score', 0),
                'robustness_momentum': sig.get('robustness_momentum', 0),
                'master_score': sig.get('master_score', 0),
                'master_score_tooltip': sig.get('master_score_tooltip', ''),
                'stop_loss': sig.get('stop_loss', 0),
                'target': sig.get('target', 0),
                'atr': sig.get('atr', 0),
                'volatility': sig.get('volatility', 'MEDIUM'),
                'market_regime': sig.get('regime', 'NEUTRAL'),
                'reason': sig.get('reason', ''),
            })
        
        # Export to CSV
        csv_path = f'robustness_test_signals_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv'
        print(f"\nExporting to CSV: {csv_path}")
        try:
            save_csv(results, csv_path, None, suggest_option_strategy, STRATEGY_TOOLTIPS)
            print(f"✓ CSV exported successfully")
        except Exception as e:
            print(f"✗ CSV export failed: {e}")
        
        # Export to HTML
        html_path = f'robustness_test_signals_{datetime.now().strftime("%Y%m%d_%H%M%S")}.html'
        print(f"\nExporting to HTML: {html_path}")
        try:
            save_html(results, html_path, None)
            print(f"✓ HTML exported successfully")
            print(f"  Open {html_path} in browser to view")
        except Exception as e:
            print(f"✗ HTML export failed: {e}")
        
        # Print summary statistics by master_score band
        print("\n" + "=" * 80)
        print("SIGNAL DISTRIBUTION BY MASTER SCORE")
        print("=" * 80)
        
        bands = {
            '80+': len([s for s in results if s['master_score'] >= 80]),
            '70-79': len([s for s in results if 70 <= s['master_score'] < 80]),
            '60-69': len([s for s in results if 60 <= s['master_score'] < 70]),
            '<60': len([s for s in results if s['master_score'] < 60]),
        }
        
        for band, count in bands.items():
            pct = (count / len(results) * 100) if len(results) > 0 else 0
            print(f"  Master {band}: {count} signals ({pct:.1f}%)")
        
        # Print top 5 signals by master_score
        print("\n" + "=" * 80)
        print("TOP 5 SIGNALS BY MASTER SCORE")
        print("=" * 80)
        
        top_signals = sorted(results, key=lambda x: x['master_score'], reverse=True)[:5]
        for i, sig in enumerate(top_signals, 1):
            print(f"\n  #{i}: {sig['symbol']} ({sig['signal'].upper()})")
            print(f"      Pattern: {sig['pattern']}")
            print(f"      Master Score: {sig['master_score']:.0f}/100")
            print(f"      Confidence: {sig['confidence']:.0f}%")
            print(f"      Robustness: {sig['robustness_score']:.0f}% ({int(sig.get('filters_passed', 0) or 0)}/7 filters)")
            print(f"      Price: {sig['price']:.2f}")
        
    else:
        print("\n✗ No signals generated - backtest may have failed")
    
    print("\n" + "=" * 80)
    print("TEST COMPLETE")
    print("=" * 80)

if __name__ == '__main__':
    test_robustness_backtest()
