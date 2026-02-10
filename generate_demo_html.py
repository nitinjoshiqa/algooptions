#!/usr/bin/env python
"""Generate demo HTML with robustness scoring columns."""

import sys
sys.path.insert(0, '.')

from datetime import datetime
from nifty_bearnness_v2 import save_html, suggest_option_strategy, STRATEGY_TOOLTIPS

def generate_demo_html():
    """Generate HTML with mock signals showing all scoring dimensions."""
    
    print("=" * 80)
    print("GENERATING DEMO HTML WITH ROBUSTNESS SCORING")
    print("=" * 80)
    
    # Create mock args object
    class Args:
        def __init__(self):
            self.universe = 'NIFTY50'
            self.mode = 'intraday'
            self.lookback = 100
    
    args = Args()
    
    # Create mock signals with all scoring fields
    demo_signals = [
        {
            'symbol': 'RELIANCE',
            'date': '2026-02-10',
            'signal': 'buy',
            'price': 2850.00,
            'pattern': 'Golden Cross',
            'confidence': 90,
            'final_score': 0.82,
            'context_score': 4.2,
            'context_momentum': 0.65,
            'robustness_score': 100.0,  # 7/7 filters
            'robustness_momentum': 0.32,
            'master_score': 88.0,
            'master_score_tooltip': '''Master Score: 88.0/100
━━━━━━━━━━━━━━━━━━━━━━
Confidence (Pattern): 90/100 (25% weight)
  Quality of pattern detection

Technical (Indicators): 82/100 (25% weight)
  Composite of RSI, VWAP, EMA, MACD, BB

Robustness (Filters): 100/100 (20% weight)
  7/7 safety filters passing
  ✓ Market regime, ✓ Volume, ✓ Time-of-day, ✓ Liquidity, ✓ Earnings safety, ✓ Multi-TF, ✓ Expectancy

Context (Institutional): 84/100 (15% weight)
  Institutional flows & Vol-RSI alignment

Momentum (Rate of Change): 82.5/100 (10% weight)
  Context improving, filters stable

News Sentiment: 70/100 (5% weight)
  Neutral to slightly positive
''',
            'news_sentiment_score': 0.4,
            'stop_loss': 2800.00,
            'target': 2950.00,
            'atr': 28.50,
            'volatility': 'MEDIUM',
            'market_regime': 'TRENDING',
            'reason': 'Golden Cross | ADX=28.0 (TRENDING) | Vol=MEDIUM | RSI=65.2 | Master=88.0',
            'swing_score': 0.75,
            'longterm_score': 0.65,
        },
        {
            'symbol': 'TCS',
            'date': '2026-02-10',
            'signal': 'buy',
            'price': 3850.00,
            'pattern': 'Pullback to MA20',
            'confidence': 78,
            'final_score': 0.70,
            'context_score': 3.8,
            'context_momentum': 0.45,
            'robustness_score': 85.7,  # 6/7 filters
            'robustness_momentum': 0.22,
            'master_score': 79.5,
            'master_score_tooltip': '''Master Score: 79.5/100
━━━━━━━━━━━━━━━━━━━━━━
Confidence (Pattern): 78/100 (25% weight)
  Reliable pullback pattern

Technical (Indicators): 70/100 (25% weight)
  Good indicator alignment

Robustness (Filters): 85.7/100 (20% weight)
  6/7 filters passing (1 filter failed)
  ✓ Market regime ✓ Volume ✓ Time ✓ Liquidity ✗ Earnings ✓ Multi-TF ✓ Expectancy

Context (Institutional): 76/100 (15% weight)
  Mixed institutional signals

Momentum (Rate of Change): 68/100 (10% weight)
  Slight filter degradation

News Sentiment: 72/100 (5% weight)
  Neutral news
''',
            'news_sentiment_score': 0.0,
            'stop_loss': 3800.00,
            'target': 3920.00,
            'atr': 35.20,
            'volatility': 'MEDIUM',
            'market_regime': 'NEUTRAL',
            'reason': 'Pullback to MA20 | ADX=23.0 (NEUTRAL) | Vol=MEDIUM | RSI=58.5 | Master=79.5',
            'swing_score': 0.65,
            'longterm_score': 0.58,
        },
        {
            'symbol': 'INFY',
            'date': '2026-02-10',
            'signal': 'buy',
            'price': 1450.00,
            'pattern': 'Consolidation Breakout',
            'confidence': 72,
            'final_score': 0.65,
            'context_score': 3.0,
            'context_momentum': -0.15,
            'robustness_score': 71.4,  # 5/7 filters
            'robustness_momentum': -0.22,
            'master_score': 71.4,
            'master_score_tooltip': '''Master Score: 71.4/100
━━━━━━━━━━━━━━━━━━━━━━
Confidence (Pattern): 72/100 (25% weight)
  Moderate pattern confirmation

Technical (Indicators): 65/100 (25% weight)
  Mixed indicator signals

Robustness (Filters): 71.4/100 (20% weight)
  5/7 filters passing (2 filters failed)
  ✓ Market regime ✓ Volume ✗ Time ✓ Liquidity ✗ Earnings ✓ Multi-TF ✓ Expectancy

Context (Institutional): 60/100 (15% weight)
  Weak institutional bias

Momentum (Rate of Change): 42.5/100 (10% weight)
  Filters degrading, caution

News Sentiment: 65/100 (5% weight)
  Slightly negative news
''',
            'news_sentiment_score': -0.2,
            'stop_loss': 1420.00,
            'target': 1510.00,
            'atr': 18.50,
            'volatility': 'LOW',
            'market_regime': 'RANGING',
            'reason': 'Consolidation Breakout | ADX=18.0 (RANGING) | Vol=LOW | RSI=55.2 | Master=71.4',
            'swing_score': 0.45,
            'longterm_score': 0.52,
        },
        {
            'symbol': 'HDFC',
            'date': '2026-02-10',
            'signal': 'buy',
            'price': 2650.00,
            'pattern': 'Death Cross (REVERSED)',
            'confidence': 55,
            'final_score': 0.45,
            'context_score': 2.0,
            'context_momentum': -0.65,
            'robustness_score': 57.1,  # 4/7 filters
            'robustness_momentum': -0.45,
            'master_score': 62.3,
            'master_score_tooltip': '''Master Score: 62.3/100
━━━━━━━━━━━━━━━━━━━━━━
Confidence (Pattern): 55/100 (25% weight)
  Weak pattern (maybe noise)

Technical (Indicators): 45/100 (25% weight)
  Poor indicator alignment

Robustness (Filters): 57.1/100 (20% weight)
  4/7 filters passing (3 filters failed)
  ✓ Market regime ✗ Volume ✗ Time ✗ Liquidity ✓ Earnings ✓ Multi-TF ✓ Expectancy

Context (Institutional): 40/100 (15% weight)
  Hostile institutional context

Momentum (Rate of Change): 17.5/100 (10% weight)
  Strong filter degradation

News Sentiment: 55/100 (5% weight)
  Mixed news sentiment
''',
            'news_sentiment_score': -0.3,
            'stop_loss': 2600.00,
            'target': 2750.00,
            'atr': 42.10,
            'volatility': 'HIGH',
            'market_regime': 'RANGING',
            'reason': 'Death Cross (questionable) | ADX=16.0 (RANGING) | Vol=HIGH | RSI=42.1 | Master=62.3',
            'swing_score': 0.25,
            'longterm_score': 0.15,
        },
    ]
    
    print(f"\nGenerated {len(demo_signals)} mock signals with full scoring details")
    print("\nSignal Summary:")
    for sig in demo_signals:
        print(f"  • {sig['symbol']:10} | Pattern: {sig['pattern']:25} | Master: {sig['master_score']:.0f}/100 | Filters: {sig['robustness_score']:.0f}%")
    
    # Generate HTML
    html_path = f'robustness_demo_{datetime.now().strftime("%Y%m%d_%H%M%S")}.html'
    print(f"\nGenerating HTML: {html_path}")
    
    try:
        save_html(demo_signals, html_path, args)
        print(f"✓ HTML generated successfully!")
        print(f"\nFile location: {html_path}")
        print(f"\nTo view the HTML:")
        print(f"  1. Open {html_path} in a web browser")
        print(f"  2. Scroll right to see new columns:")
        print(f"     - Robustness% (0-100): Filter quality")
        print(f"     - Robust Momentum (-1 to +1): Filter trend")
        print(f"     - Master Score (0-100): 6-dimension composite")
        print(f"  3. Hover over Master Score for detailed tooltip")
        print(f"  4. Click column headers to sort")
        print(f"  5. All existing columns remain (Score, Swing, Context, etc.)")
        
        return html_path
        
    except Exception as e:
        print(f"✗ HTML generation failed: {e}")
        import traceback
        traceback.print_exc()
        return None

if __name__ == '__main__':
    html_file = generate_demo_html()
    
    if html_file:
        print("\n" + "=" * 80)
        print("DEMO HTML GENERATION COMPLETE")
        print("=" * 80)
        print("\nNew columns in HTML:")
        print("  1. Robustness% → Shows % of 7 safety filters passing (0-100)")
        print("  2. Robust Momentum → Shows if filters improving/degrading (-1 to +1)")
        print("  3. Master Score → 6-dimension weighted composite (0-100) with hover tooltip")
        print("\nColor Coding:")
        print("  • Master Score ≥80: 🟢 Green (Excellent)")
        print("  • Master Score 70-79: 🟡 Orange (Good)")
        print("  • Master Score 60-69: 🟠 Dark Orange (Fair)")
        print("  • Master Score <60: 🔴 Red (Poor)")
