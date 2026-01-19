"""
Refactored NIFTY Bearnness Screener - Clean Modular Architecture

Usage:
    python nifty_bearnness_v2.py --mode swing --universe nifty --quick
    python nifty_bearnness_v2.py --force-yf --parallel 8 --universe banknifty
"""

import argparse
import csv
import signal
import warnings
import shutil
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from datetime import datetime

# Suppress curl_cffi KeyboardInterrupt warnings (library issue, not critical)
warnings.filterwarnings('ignore', message='.*KeyboardInterrupt.*')
warnings.filterwarnings('ignore', category=DeprecationWarning)

# Handle KeyboardInterrupt gracefully
def signal_handler(sig, frame):
    print("\n[INFO] Interrupted by user. Cleaning up...")
    exit(0)

signal.signal(signal.SIGINT, signal_handler)

# Core modules
from core.config import OUT_CSV
from core.universe import UniverseManager
from core.scoring_engine import BearnessScoringEngine
from core.option_strategies import suggest_option_strategy, STRATEGY_TOOLTIPS
from core.sector_mapper import get_sector
from core.database_operations import save_daily_score
from core.database import init_db
from core.database import get_session, close_session
from core.performance import get_tracker
from nifty_screener.enhanced_reporter import EnhancedReportGenerator
import pandas as pd

# Note: save_csv and save_html are defined below (too large to modularize yet)
# Future: Extract to exporters/ module


def print_results(results):
    """Print ranked results to console."""
    scored = [r for r in results if r.get("final_score") is not None]
    # Sort defensively - handle None values
    scored.sort(key=lambda r: (r["final_score"] if r.get("final_score") is not None else float('inf')))
    
    print("\nRanked by bearness (most bearish first):")
    print(f"{'Rank':<6}{'Symbol':<12}{'Score':<10}{'Conf%':<8}{'Price':<12}{'%BelowHigh':<14}{'%AboveLow':<12}")
    print("-" * 90)
    
    for i, r in enumerate(scored, 1):
        price = r.get('price', 0)
        conf_str = f"{r.get('confidence', 0):.0f}" if r.get('confidence') is not None else "N/A"
        
        # Calculate % Below High and % Above Low
        week52_high = r.get('52w_high', price)
        week52_low = r.get('52w_low', price)
        
        pct_below_high_str = "N/A"
        if week52_high and week52_high > 0:
            pct_below_high = ((week52_high - price) / week52_high) * 100
            pct_below_high_str = f"{pct_below_high:.2f}%"
        
        pct_above_low_str = "N/A"
        if week52_low and week52_low > 0:
            pct_above_low = ((price - week52_low) / week52_low) * 100
            pct_above_low_str = f"{pct_above_low:.2f}%"
        
        print(f"{i:<6}{r['symbol']:<12}{r['final_score']:+.3f}    {conf_str:<8}{price:>10.2f}   {pct_below_high_str:>12}   {pct_above_low_str:>10}")
    
    nodata = [r for r in results if r.get("final_score") is None]
    if nodata:
        print("\nSymbols with no data:")
        print(", ".join(r['symbol'] for r in nodata))

def _compute_index_bias(engine, results=None):
    """Compute NIFTY index directional bias.
    1) Try direct engine scoring on 'NIFTY'.
    2) Fallback: compute breadth-weighted bias from results if available.
    Returns (bias_score: float, source: str).
    """
    try:
        idx = engine.compute_score('NIFTY')
        if idx and idx.get('status') == 'OK' and idx.get('final_score') is not None:
            return float(idx['final_score']), f"engine/{idx.get('source','')}"
    except Exception:
        pass

    # Breadth-based fallback: confidence-weighted average of scores
    if results:
        vals = []
        for r in results:
            s = r.get('final_score')
            c = r.get('confidence')
            if s is not None and c is not None:
                # Weight by confidence (0-1)
                vals.append(s * max(0.0, min(1.0, c / 100.0)))
        if vals:
            return (sum(vals) / len(vals)), 'breadth/conf-weighted'

    return 0.0, 'breadth'

def print_actionables(results, index_bias=0.0, conf_threshold=35.0, score_threshold=0.15):
    """Print shortlist of actionable picks based on score, confidence, and index alignment."""
    ok = [r for r in results if r.get('final_score') is not None and r.get('confidence') is not None]
    if not ok:
        print("\nNo actionable picks: no scored results available.")
        return

    # Determine preferred direction based on index bias
    prefer_bear = index_bias < -0.05
    prefer_bull = index_bias > 0.05

    def aligned(r):
        s = r.get('final_score', 0.0)
        if prefer_bear:
            return s <= -score_threshold
        if prefer_bull:
            return s >= score_threshold
        # Neutral index: allow both directions
        return abs(s) >= score_threshold

    # Filter by confidence and alignment
    picks = [r for r in ok if r['confidence'] >= conf_threshold and aligned(r)]
    # Rank by score magnitude (higher absolute score = stronger signal)
    picks.sort(key=lambda r: abs(r.get('final_score', 0.0)), reverse=True)

    # Header
    direction = 'Bearish' if prefer_bear else 'Bullish' if prefer_bull else 'Neutral'
    print(f"\nActionable picks (index: {direction}, bias={index_bias:+.3f}, conf>={conf_threshold}, |score|>={score_threshold}):")
    print(f"{'Rank':<6}{'Symbol':<12}{'Score':<10}{'Conf%':<8}{'Price':<10}{'ATR':<8}{'SL%':<8}{'Target%':<10}{'Sector':<14}")
    print('-'*90)
    for rank, r in enumerate(picks[:25], 1):
        price = r.get('price') or 0.0
        conf = r.get('confidence') or 0.0
        score = r.get('final_score') or 0.0
        atr = r.get('atr') or 0.0
        
        # Calculate SL and Target percentages (2.5x ATR SL, 3:1 RR)
        sl_pct = (2.5 * atr / price * 100) if price > 0 and atr > 0 else 0.0
        target_pct = sl_pct * 3.0
        
        direction_icon = '▼' if score < 0 else '▲'
        
        print(f"{rank:<6}{r['symbol']:<12}{score:+.3f}    {conf:>6.0f}   {price:>8.2f}  {atr:>6.2f}  {sl_pct:>6.1f}%  {target_pct:>8.1f}%  {r.get('sector','Unknown'):<14}")


# Note: get_sector() removed - now imported from core.sector_mapper
# Note: save_csv() defined below  
# Note: save_html() defined below

# Auto-load to database
def _load_results_to_database(csv_path):
    """Load screener results from CSV into database."""
    try:
        from datetime import datetime, date
        
        # Initialize database with schema
        init_db()
        
        df = pd.read_csv(csv_path)
        session = get_session()
        
        loaded = 0
        skipped = 0
        today = date.today()
        
        for _, row in df.iterrows():
            try:
                # Extract values with defaults
                symbol = str(row.get('symbol', '')).strip()
                base_score = row.get('final_score', None)
                confidence = row.get('confidence', 50)
                option_score = row.get('option_score', 0.0)
                strategy = str(row.get('strategy', 'NEUTRAL')).strip()
                
                # Skip if no valid score
                if pd.isna(base_score):
                    skipped += 1
                    continue
                
                # Handle NaN confidence
                if pd.isna(confidence):
                    confidence = 50
                else:
                    confidence = int(confidence)
                
                # Determine bucket
                if base_score >= 0.5:
                    bucket = 'HIGH'
                elif base_score >= 0.25:
                    bucket = 'MEDIUM'
                else:
                    bucket = 'LOW'
                
                # Determine option quality
                if option_score >= 0.15:
                    option_quality = 'GOOD'
                elif option_score >= -0.10:
                    option_quality = 'MARGINAL'
                else:
                    option_quality = 'POOR'
                
                # Save to database
                save_daily_score(
                    session=session,
                    symbol=symbol,
                    trade_date=today,
                    base_score=float(base_score),
                    score_bucket=bucket,
                    option_score=float(option_score) if not pd.isna(option_score) else 0.0,
                    option_quality=option_quality,
                    suggested_strategy=strategy,
                    confidence_level=confidence
                )
                loaded += 1
            except Exception as e:
                # Handle emoji in error messages (Windows console issue)
                try:
                    print(f"[DEBUG] Error saving {symbol}: {str(e)}")
                except UnicodeEncodeError:
                    error_msg = str(e).encode('ascii', errors='replace').decode('ascii')
                    print(f"[DEBUG] Error saving {symbol}: {error_msg}")
                skipped += 1
                continue
        
        session.commit()
        close_session(session)
        
        print(f"\nDatabase Load:")
        print(f"   [LOADED] {loaded} scores")
        if skipped > 0:
            print(f"   [SKIPPED] {skipped} (missing/invalid data)")
        print(f"   Total: {loaded + skipped} records processed")
    except Exception as e:
        print(f"\n[ERROR] Database load failed: {e}")

def save_csv(results, output_path, args):
    """Save results to CSV."""
    with open(output_path, "w", newline='', encoding='utf-8') as csvf:
        writer = csv.writer(csvf)
        writer.writerow([
            "rank", "symbol", "sector", "index", "market_regime", "final_score",
            "confidence", "price", "pct_below_high", "pct_above_low", "mode", "strategy", "strategy_reason",
            "or_score", "vwap_score", "structure_score", "rsi", "rsi_score", "ema_score",
            "volume_score", "macd_score", "bb_score", "atr",
            "intraday_weight", "swing_weight", "longterm_weight",
            "option_score", "option_iv", "option_spread_pct", "option_type", "option_strike", "option_expiry",
            "option_volume", "option_oi", "option_delta", "option_gamma", "option_theta", "option_vega"
        ])
        
        for i, r in enumerate(results, 1):
            price = r.get('price', 0)
            week52_high = r.get('52w_high', price)
            week52_low = r.get('52w_low', price)
            
            # Calculate % Below High and % Above Low
            pct_below_high = ""
            if week52_high and week52_high > 0:
                pct_below_high = f"{((week52_high - price) / week52_high) * 100:.2f}"
            
            pct_above_low = ""
            if week52_low and week52_low > 0:
                pct_above_low = f"{((price - week52_low) / week52_low) * 100:.2f}"
            
            weights = r.get('weights', {})
            
            sector_val = r.get('sector', 'Unknown')
            # Derive option strategy recommendation for CSV
            score = r.get('final_score')
            conf_val = r.get('confidence') or 0
            atr_val = r.get('atr') or 0
            px = price or 0
            volatility_pct = ((atr_val / px) * 100) if (px > 0 and atr_val > 0) else 2.0
            is_bullish = (score is not None) and (score > 0.05)
            is_bearish = (score is not None) and (score < -0.05)
            abs_score = abs(score) if score is not None else 0
            option_score = r.get('option_score')
            strategy_val, strategy_class = suggest_option_strategy(is_bullish, is_bearish, volatility_pct, conf_val, abs_score, option_score)
            strategy_reason = STRATEGY_TOOLTIPS.get(strategy_class, '')
            
            writer.writerow([
                i,
                r['symbol'],
                sector_val,
                r.get('index', ''),
                r.get('market_regime', ''),
                f"{r['final_score']:.4f}" if r.get('final_score') is not None else '',
                f"{r['confidence']:.1f}" if r.get('confidence') is not None else '',
                f"{r['price']:.2f}" if r.get('price') is not None else '',
                pct_below_high,
                pct_above_low,
                r.get('mode', ''),
                strategy_val,
                strategy_reason,
                f"{r['or_score']:.4f}" if r.get('or_score') is not None else '',
                f"{r['vwap_score']:.4f}" if r.get('vwap_score') is not None else '',
                f"{r['structure_score']:.4f}" if r.get('structure_score') is not None else '',
                f"{r['rsi']:.2f}" if r.get('rsi') is not None else '',
                f"{r['rsi_score']:.4f}" if r.get('rsi_score') is not None else '',
                f"{r['ema_score']:.4f}" if r.get('ema_score') is not None else '',
                f"{r['volume_score']:.4f}" if r.get('volume_score') is not None else '',
                f"{r['macd_score']:.4f}" if r.get('macd_score') is not None else '',
                f"{r['bb_score']:.4f}" if r.get('bb_score') is not None else '',
                f"{r['atr']:.2f}" if r.get('atr') is not None else '',
                f"{weights.get('intraday', 0):.2f}" if weights else '',
                f"{weights.get('swing', 0):.2f}" if weights else '',
                f"{weights.get('longterm', 0):.2f}" if weights else '',
                f"{r['option_score']:.4f}" if r.get('option_score') is not None else '',
                f"{r['option_iv']:.4f}" if r.get('option_iv') is not None else '',
                f"{r['option_spread_pct']:.4f}" if r.get('option_spread_pct') is not None else '',
                r.get('option_type', ''),
                f"{r['option_strike']:.2f}" if r.get('option_strike') is not None else '',
                r.get('option_expiry', ''),
                f"{r['option_volume']:.0f}" if r.get('option_volume') is not None else '',
                f"{r['option_oi']:.0f}" if r.get('option_oi') is not None else '',
                f"{r['option_delta']:.4f}" if r.get('option_delta') is not None else '',
                f"{r['option_gamma']:.6f}" if r.get('option_gamma') is not None else '',
                f"{r['option_theta']:.4f}" if r.get('option_theta') is not None else '',
                f"{r['option_vega']:.4f}" if r.get('option_vega') is not None else '',
            ])
    
    print(f"\nSaved results to {output_path}")


def save_html(results, output_path, args):
    """Save results to HTML with interactive table."""
    scored = [r for r in results if r.get("final_score") is not None]
    # Sort defensively - handle None values  
    scored.sort(key=lambda r: (r.get("final_score") if r.get("final_score") is not None else float('inf')))
    
    nodata_count = len([r for r in results if r.get("final_score") is None])
    
    # Calculate sector performance metrics
    sector_scores = {}
    for r in scored:
        sector = r.get('sector', 'Unknown')
        final_score = r.get('final_score', 0) or 0
        if sector not in sector_scores:
            sector_scores[sector] = {'total': 0, 'count': 0, 'avg': 0}
        sector_scores[sector]['total'] += final_score
        sector_scores[sector]['count'] += 1
    
    # Calculate averages
    for sector in sector_scores:
        if sector_scores[sector]['count'] > 0:
            sector_scores[sector]['avg'] = sector_scores[sector]['total'] / sector_scores[sector]['count']
    
    # Find min/max for color gradient
    sector_avgs = [data['avg'] for data in sector_scores.values() if data['count'] > 0]
    min_avg = min(sector_avgs) if sector_avgs else -1
    max_avg = max(sector_avgs) if sector_avgs else 1
    avg_range = max_avg - min_avg if max_avg != min_avg else 1
    num_sectors = len(sector_scores)
    
    def get_sector_color(sector):
        """Get color for sector based on average score with vibrant gradient."""
        if sector not in sector_scores or sector_scores[sector]['count'] == 0:
            return '#f0f0f0'  # light gray for unknown
        
        # If only 1 sector in data, use neutral light gray (no comparison possible)
        if num_sectors == 1:
            return '#f0f0f0'  # neutral light gray
        
        avg = sector_scores[sector]['avg']
        # Normalize to 0-1 range where 0=worst (red), 1=best (green)
        normalized = (avg - min_avg) / avg_range if avg_range > 0 else 0.5
        # Create vibrant gradient: bright red (0) -> pale yellow (0.5) -> bright green (1)
        if normalized < 0.5:
            # Bright Red to Pale Yellow (bearish to neutral)
            r = 255                                  # Full red
            g = int(107 + (200 * (normalized * 2))) # 107 -> 207 at center
            b = 107                                 # Constant blue
        else:
            # Pale Yellow to Bright Green (neutral to bullish)
            r = int(255 - (204 * (2 - normalized * 2)))    # 255 -> 51
            g = int(207 + (48 * (2 - normalized * 2)))     # 207 -> 255
            b = int(107 - (107 * (2 - normalized * 2)))    # 107 -> 0
        return f'#{r:02x}{g:02x}{b:02x}'
    
    def get_sector_text_color(bg_hex):
        """Determine text color (white or black) based on background brightness."""
        # Parse hex color
        bg_hex = bg_hex.lstrip('#')
        r = int(bg_hex[0:2], 16)
        g = int(bg_hex[2:4], 16)
        b = int(bg_hex[4:6], 16)
        
        # Calculate luminance using relative luminance formula
        luminance = (0.299 * r + 0.587 * g + 0.114 * b) / 255
        
        # Use white text for dark backgrounds, black for light backgrounds
        return 'white' if luminance < 0.5 else '#222'
    
    # Use global suggest_option_strategy and STRATEGY_TOOLTIPS defined at module level
    
    # TF Alignment Tooltips
    TF_ALIGNMENT_TOOLTIPS = {
        '✓✓✓': 'All 3 timeframes (5m, 15m, 1h) aligned - Strongest signal. High probability. +30% R:R boost.',
        '✓✓✗': '2 of 3 timeframes aligned - Good signal. Moderate probability. +10% R:R boost.',
        '✓✗✗': 'Only 1 timeframe aligned - Weak signal. Lower probability. -15% R:R penalty.',
        'N/A': 'Timeframe data not available.',
    }
    
    html_content = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta http-equiv="refresh" content="900">  <!-- Auto-refresh every 15 min -->
    <title>Nifty Stock Analyser - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</title>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&family=JetBrains+Mono:wght@400;600&display=swap" rel="stylesheet">
    <style>
        * {{ box-sizing: border-box; }}
        body {{ font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif; margin: 0; padding: 20px; background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%); min-height: 100vh; }}
        .container {{ max-width: 1400px; margin: 0 auto; }}
        h2 {{ color: #1a202c; margin: 0 0 8px 0; font-size: 32px; font-weight: 700; letter-spacing: -0.5px; }}
        h3 {{ color: #2d3748; margin: 24px 0 16px 0; font-size: 18px; font-weight: 600; border-bottom: 2px solid #e2e8f0; padding-bottom: 8px; text-transform: uppercase; letter-spacing: 0.5px; }}
        h4 {{ color: #2d3748; margin: 0 0 12px 0; font-size: 15px; font-weight: 600; }}
        p.info {{ color: #718096; margin: 8px 0; font-size: 14px; display: flex; gap: 24px; flex-wrap: wrap; }}
        p.info strong {{ color: #2d3748; font-weight: 600; }}
        p.info strong {{ color: #2d3748; font-weight: 600; }}
        
        /* DASHBOARD SECTIONS */
        .dashboard {{ background: white; border-radius: 12px; padding: 24px; margin-bottom: 24px; box-shadow: 0 4px 6px rgba(0,0,0,0.07); }}
        .metrics-grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 16px; margin: 16px 0; }}
        .metric-card {{ background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 16px; border-radius: 8px; text-align: center; }}
        .metric-card.bullish {{ background: linear-gradient(135deg, #11998e 0%, #38ef7d 100%); }}
        .metric-card.bearish {{ background: linear-gradient(135deg, #ee0979 0%, #ff6a00 100%); }}
        .metric-card.neutral {{ background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); }}
        .metric-value {{ font-size: 28px; font-weight: 700; margin: 8px 0; font-family: 'JetBrains Mono', monospace; }}
        .metric-label {{ font-size: 12px; opacity: 0.9; text-transform: uppercase; letter-spacing: 0.5px; font-weight: 500; }}
        .metric-subtext {{ font-size: 11px; opacity: 0.8; margin-top: 6px; }}
        
        .insights-row {{ display: grid; grid-template-columns: 1fr 1fr; gap: 16px; margin: 16px 0; }}
        .insight-box {{ background: #f7fafc; border-left: 4px solid #667eea; padding: 14px; border-radius: 6px; }}
        .insight-box.bull {{ border-left-color: #38ef7d; }}
        .insight-box.bear {{ border-left-color: #ff6a00; }}
        .insight-title {{ font-weight: 600; color: #2d3748; font-size: 13px; text-transform: uppercase; margin-bottom: 8px; }}
        .insight-content {{ font-size: 13px; color: #4a5568; line-height: 1.6; }}
        .insight-item {{ display: flex; justify-content: space-between; align-items: center; padding: 8px 0; border-bottom: 1px solid #e2e8f0; }}
        .insight-item:last-child {{ border-bottom: none; }}
        .insight-name {{ font-weight: 500; color: #2d3748; }}
        .insight-value {{ font-weight: 600; color: #667eea; font-family: 'JetBrains Mono', monospace; }}
        
        .risk-matrix {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(160px, 1fr)); gap: 12px; margin: 16px 0; }}
        .risk-card {{ background: white; border: 2px solid #e2e8f0; border-radius: 8px; padding: 12px; text-align: center; transition: all 0.3s; }}
        .risk-card:hover {{ border-color: #667eea; box-shadow: 0 4px 12px rgba(102, 126, 234, 0.1); transform: translateY(-2px); }}
        .risk-symbol {{ font-weight: 700; font-size: 16px; font-family: 'JetBrains Mono', monospace; color: #2d3748; }}
        .risk-metric {{ font-size: 11px; color: #718096; margin-top: 4px; }}
        .risk-rr {{ font-weight: 600; color: #11998e; font-family: 'JetBrains Mono', monospace; }}
        
        /* TOP PICKS SECTION */
        .top-picks-container {{
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 16px;
            margin: 16px 0;
        }}
        
        .picks-card {{
            background: white;
            border-radius: 8px;
            padding: 16px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.08);
            border-left: 5px solid;
        }}
        
        .picks-card.bullish {{
            border-left-color: #38ef7d;
            background: linear-gradient(to right, rgba(56, 239, 125, 0.03), transparent);
        }}
        
        .picks-card.bearish {{
            border-left-color: #ff6a00;
            background: linear-gradient(to right, rgba(255, 106, 0, 0.03), transparent);
        }}
        
        .picks-card h4 {{
            margin: 0 0 12px 0;
            color: #2d3748;
            font-size: 14px;
            font-weight: 600;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }}
        
        .pick-item {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 10px 0;
            border-bottom: 1px solid #edf2f7;
            font-size: 13px;
        }}
        
        .pick-item:last-child {{
            border-bottom: none;
        }}
        
        .pick-symbol {{
            font-weight: 600;
            color: #2d3748;
            font-family: 'JetBrains Mono', monospace;
            min-width: 70px;
        }}
        
        .pick-score {{
            font-weight: 700;
            padding: 4px 8px;
            border-radius: 4px;
            font-size: 12px;
            font-family: 'JetBrains Mono', monospace;
        }}
        
        .pick-score.bull {{
            background: #c6f6d5;
            color: #22543d;
        }}
        
        .pick-score.bear {{
            background: #fed7d7;
            color: #742a2a;
        }}
        
        .pick-details {{
            color: #718096;
            font-size: 12px;
            text-align: right;
        }}
        
        /* SECTOR HEATMAP */
        .sector-heatmap {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
            gap: 12px;
            margin: 16px 0;
        }}
        
        .sector-card {{
            padding: 14px;
            border-radius: 8px;
            text-align: center;
            transition: all 0.3s ease;
            cursor: default;
            box-shadow: 0 2px 8px rgba(0,0,0,0.08);
        }}
        
        .sector-card:hover {{
            transform: translateY(-4px);
            box-shadow: 0 8px 16px rgba(0,0,0,0.12);
        }}
        
        .sector-name {{
            font-weight: 600;
            font-size: 13px;
            margin-bottom: 8px;
            color: #2d3748;
        }}
        
        .sector-score {{
            font-size: 20px;
            font-weight: 700;
            margin-bottom: 4px;
            font-family: 'JetBrains Mono', monospace;
        }}
        
        .sector-count {{
            font-size: 12px;
            opacity: 0.85;
            line-height: 1.4;
        }}
        
        /* MAIN TABLE STYLES */
        table {{ border-collapse: collapse; width: 100%; font-size: 13px; background-color: white; box-shadow: 0 4px 6px rgba(0,0,0,0.07); border-radius: 8px; overflow: hidden; }}
        th, td {{ border: 1px solid #e2e8f0; padding: 10px 8px; text-align: left; }}
        th {{ background: #f7fafc; cursor: pointer; position: relative; font-weight: 600; color: #2d3748; font-family: 'Inter', sans-serif; }}
        th.sort-asc::after {{ content: " ▲"; font-size: 11px; color: #667eea; }}
        th.sort-desc::after {{ content: " ▼"; font-size: 11px; color: #667eea; }}
        tr:hover {{ background-color: #f7fafc; }}
        td {{ font-family: 'Inter', sans-serif; color: #4a5568; }}
        td.mono {{ font-family: 'JetBrains Mono', monospace; font-size: 12px; }}
        
        .badge {{ display: inline-block; padding: 4px 8px; border-radius: 4px; font-size: 11px; font-weight: 600; text-transform: uppercase; letter-spacing: 0.5px; }}
        .tag-bear {{ background: #fed7d7; color: #742a2a; }}
        .tag-bull {{ background: #c6f6d5; color: #22543d; }}
        .tag-neutral {{ background: #e2e8f0; color: #2d3748; }}
        
        .controls {{ margin-bottom: 16px; padding: 16px; background: white; border-radius: 8px; box-shadow: 0 2px 8px rgba(0,0,0,0.08); }}
        .search {{ padding: 10px 12px; border: 2px solid #e2e8f0; border-radius: 6px; width: 300px; font-family: 'Inter', sans-serif; font-size: 14px; transition: border-color 0.3s; }}
        .search:focus {{ outline: none; border-color: #667eea; background: #f7fafc; }}
        .control-group {{ margin: 10px 0; display: inline-block; margin-right: 20px; }}
        input[type="range"] {{ vertical-align: middle; margin: 0 8px; }}
        label {{ margin-right: 10px; font-size: 13px; font-weight: 500; color: #2d3748; }}
        select {{ padding: 8px 10px; border: 2px solid #e2e8f0; border-radius: 6px; font-family: 'Inter', sans-serif; font-size: 13px; cursor: pointer; transition: border-color 0.3s; }}
        select:focus {{ outline: none; border-color: #667eea; background: #f7fafc; }}
        
        .no-data {{ color: #a0aec0; font-style: italic; margin-top: 15px; padding: 10px; }}
        .score {{ font-weight: 700; border-radius: 4px; font-family: 'JetBrains Mono', monospace; }}
        .grade-a {{ background-color: #11998e; color: white; }}
        .grade-b {{ background-color: #38ef7d; color: #22543d; }}
        .grade-c {{ background-color: #f6ad55; color: white; }}
        .grade-d {{ background-color: #fc8181; color: white; }}
        .grade-f {{ background-color: #f56565; color: white; }}
        
        .trend-strong-bull {{ background-color: #11998e; color: white; }}
        .trend-bull {{ background-color: #38ef7d; color: #22543d; }}
        .trend-neutral {{ background-color: #cbd5e0; color: #2d3748; }}
        .trend-bear {{ background-color: #fc8181; color: white; }}
        .trend-strong-bear {{ background-color: #f56565; color: white; }}
        
        .regime-trending {{ background-color: #4299e1; color: white; }}
        .regime-ranging {{ background-color: #a0aec0; color: white; }}
        .regime-volatile {{ background-color: #f56565; color: white; }}
        .regime-quiet {{ background-color: #cbd5e0; color: #2d3748; }}
        
        /* Strategy Badge Styles */
        .long-call {{ background-color: #11998e; color: white; font-weight: 600; }}
        .bull-call {{ background-color: #38ef7d; color: #22543d; font-weight: 600; }}
        .lcall-spread {{ background-color: #81e6d9; color: #234e52; font-weight: 600; }}
        .atm-call {{ background-color: #4299e1; color: white; font-weight: 600; }}
        .call-diagonal {{ background-color: #63b3ed; color: white; font-weight: 600; }}
        .call-calendar {{ background-color: #90cdf4; color: #2c5282; font-weight: 600; }}
        
        .long-put {{ background-color: #f56565; color: white; font-weight: 600; }}
        .bear-put {{ background-color: #fc8181; color: white; font-weight: 600; }}
        .put-spread {{ background-color: #ed8936; color: white; font-weight: 600; }}
        .atm-put {{ background-color: #f6ad55; color: white; font-weight: 600; }}
        .put-diagonal {{ background-color: #fbd38d; color: #7c2d12; font-weight: 600; }}
        .put-calendar {{ background-color: #feebc8; color: #7c2d12; font-weight: 600; }}
        
        .iron-condor {{ background-color: #9f7aea; color: white; font-weight: 600; }}
        .straddle {{ background-color: #b794f6; color: white; font-weight: 600; }}
        .strangle {{ background-color: #d6bcfa; color: #44337a; font-weight: 600; }}
        .covered-call {{ background-color: #ecc94b; color: #7c2d12; font-weight: 600; }}
        .neutral-strategy {{ background-color: #e2e8f0; color: #2d3748; font-weight: 600; }}
        
        .strategy-trending-short {{ background-color: #f56565; color: white; font-weight: 600; }}
        .strategy-trending-long {{ background-color: #11998e; color: white; font-weight: 600; }}
        .strategy-pullback-short {{ background-color: #f6ad55; color: white; }}
        .strategy-pullback-long {{ background-color: #4299e1; color: white; }}
        .strategy-fade {{ background-color: #9f7aea; color: white; }}
        .strategy-range {{ background-color: #38b6a8; color: white; }}
        .strategy-breakout {{ background-color: #ed8936; color: white; }}
        .strategy-swing-short {{ background-color: #c53030; color: white; }}
        .strategy-swing-long {{ background-color: #0f7938; color: white; }}
        .strategy-avoid {{ background-color: #4a5568; color: white; font-weight: 600; }}
        .strategy-wait {{ background-color: #a0aec0; color: white; }}
        .strategy-watch {{ background-color: #718096; color: white; }}
        .strategy-neutral {{ background-color: #cbd5e0; color: #2d3748; }}
        
        /* Tooltip styling */
        .tooltip-trigger {{
            position: relative;
            cursor: help;
            border-bottom: 2px dotted #667eea;
            transition: all 0.2s ease;
        }}
        
        .tooltip-trigger:hover {{
            background-color: rgba(102, 126, 234, 0.08);
        }}
        
        .tooltip-trigger .tooltiptext {{
            visibility: hidden;
            background-color: #2d3748;
            color: white;
            text-align: left;
            border-radius: 6px;
            padding: 12px 14px;
            position: absolute;
            z-index: 1000;
            font-size: 12px;
            font-weight: 400;
            white-space: normal;
            text-decoration: none;
            box-shadow: 0 8px 24px rgba(0, 0, 0, 0.3);
            border: 1px solid #4a5568;
            bottom: 125%;
            transition: visibility 0.2s ease;
            pointer-events: none;
            line-height: 1.5;
            font-family: 'Inter', sans-serif;
        }}
        
        .tooltip-trigger:hover .tooltiptext {{
            visibility: visible;
        }}
        
        .tooltip-trigger .tooltiptext::after {{
            content: "";
            position: absolute;
            top: 100%;
            left: 12px;
            margin-left: -6px;
            border-width: 6px;
            border-style: solid;
            border-color: #2d3748 transparent transparent transparent;
        }}
        
        .align-strong {{ color: #11998e; font-weight: 700; }}
        .align-medium {{ color: #f6ad55; font-weight: 700; }}
        .align-weak {{ color: #f56565; font-weight: 700; }}
        
        .tooltip {{ position: relative; cursor: help; }}
        .tooltip .tooltiptext {{ visibility: hidden; background-color: #2d3748; color: #fff; text-align: left; padding: 10px 12px; border-radius: 6px; position: absolute; z-index: 1000; bottom: 125%; left: 50%; margin-left: -80px; width: 160px; opacity: 0; transition: opacity 0.3s; font-size: 11px; line-height: 1.4; font-family: 'Inter', sans-serif; }}
        .tooltip .tooltiptext::after {{ content: ""; position: absolute; top: 100%; left: 50%; margin-left: -5px; border-width: 5px; border-style: solid; border-color: #2d3748 transparent transparent transparent; }}
        .tooltip:hover .tooltiptext {{ visibility: visible; opacity: 1; }}
        
        .quick-actions {{ background: white; border-radius: 8px; padding: 16px; box-shadow: 0 2px 8px rgba(0,0,0,0.08); margin-top: 20px; }}
        .action-legend {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(180px, 1fr)); gap: 12px; margin: 12px 0; }}
        .legend-item {{ display: flex; align-items: center; gap: 8px; font-size: 12px; }}
        .legend-dot {{ width: 12px; height: 12px; border-radius: 2px; }}
        .legend-dot.bull {{ background: #38ef7d; }}
        .legend-dot.bear {{ background: #ff6a00; }}
        .legend-dot.neutral {{ background: #cbd5e0; }}
    </style>
</head>
<body>
    <div class="container">
        <h2>Nifty Stock Analyser</h2>
        <p class="info"><strong>Universe:</strong> {args.universe} | <strong>Mode:</strong> {args.mode} | <strong>Stocks Analyzed:</strong> {len(scored)} | <strong>No Data:</strong> {nodata_count} | <strong>Generated:</strong> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>

    
    <!-- DASHBOARD SECTIONS -->
    <div class="dashboard">
        <!-- KEY METRICS -->
        <h3>Key Metrics</h3>
        <div class="metrics-grid">
"""
    
    # Calculate metrics (negative = bearish, positive = bullish)
    bearish_count = len([r for r in scored if r.get('final_score', 0) < -0.05])
    bullish_count = len([r for r in scored if r.get('final_score', 0) > 0.05])
    neutral_count = len(scored) - bullish_count - bearish_count
    avg_confidence = sum([r.get('confidence', 0) or 0 for r in scored]) / len(scored) if scored else 0
    avg_score = sum([r.get('final_score', 0) or 0 for r in scored]) / len(scored) if scored else 0
    
    html_content += f'''
            <div class="metric-card bearish">
                <div class="metric-label">Bearish Picks</div>
                <div class="metric-value">{bearish_count}</div>
                <div class="metric-subtext">{(bearish_count/len(scored)*100 if scored else 0):.1f}% of total</div>
            </div>
            <div class="metric-card bullish">
                <div class="metric-label">Bullish Picks</div>
                <div class="metric-value">{bullish_count}</div>
                <div class="metric-subtext">{(bullish_count/len(scored)*100 if scored else 0):.1f}% of total</div>
            </div>
            <div class="metric-card neutral">
                <div class="metric-label">Neutral</div>
                <div class="metric-value">{neutral_count}</div>
                <div class="metric-subtext">{(neutral_count/len(scored)*100 if scored else 0):.1f}% of total</div>
            </div>
            <div class="metric-card neutral">
                <div class="metric-label">Avg Confidence</div>
                <div class="metric-value">{avg_confidence:.1f}%</div>
                <div class="metric-subtext">Signal reliability</div>
            </div>
'''
    
    # SECTOR INSIGHTS
    html_content += '<h3>Sector Intelligence</h3><div class="insights-row">'
    
    # Top bullish sectors
    bullish_sectors = sorted(
        [(s, d['avg']) for s, d in sector_scores.items() if d['avg'] < -0.05],
        key=lambda x: x[1]
    )[:3]
    
    bearish_sectors = sorted(
        [(s, d['avg']) for s, d in sector_scores.items() if d['avg'] > 0.05],
        key=lambda x: x[1],
        reverse=True
    )[:3]
    
    html_content += '<div class="insight-box bull"><div class="insight-title">🚀 Top Bullish Sectors</div><div class="insight-content">'
    if bullish_sectors:
        for sector, score in bullish_sectors:
            html_content += f'<div class="insight-item"><span class="insight-name">{sector}</span><span class="insight-value">{score:+.3f}</span></div>'
    else:
        html_content += '<div style="color: #a0aec0; font-size: 12px;">No bullish sectors found</div>'
    html_content += '</div></div>'
    
    html_content += '<div class="insight-box bear"><div class="insight-title">📉 Top Bearish Sectors</div><div class="insight-content">'
    if bearish_sectors:
        for sector, score in bearish_sectors:
            html_content += f'<div class="insight-item"><span class="insight-name">{sector}</span><span class="insight-value">{score:+.3f}</span></div>'
    else:
        html_content += '<div style="color: #a0aec0; font-size: 12px;">No bearish sectors found</div>'
    html_content += '</div></div></div>'
    
    # RISK/OPPORTUNITY MATRIX
    html_content += '<h3>Best Risk-Reward Opportunities</h3><div class="risk-matrix">'
    
    # Find best R:R picks
    best_rr = sorted(
        [(r.get('symbol', 'N/A'), 
          r.get('final_score', 0),
          r.get('rr_ratio', 0) or 1) 
         for r in scored if r.get('rr_ratio')],
        key=lambda x: x[2],
        reverse=True
    )[:6]
    
    if best_rr:
        for symbol, score, rr in best_rr:
            sentiment = "🟢" if score < 0 else "🔴"
            html_content += f'''<div class="risk-card">
                <div style="font-size: 20px; margin-bottom: 4px;">{sentiment}</div>
                <div class="risk-symbol">{symbol}</div>
                <div class="risk-metric">Score: {score:+.3f}</div>
                <div class="risk-metric">R:R: <span class="risk-rr">{rr:.2f}</span></div>
            </div>'''
    else:
        html_content += '<div style="grid-column: 1/-1; color: #a0aec0; text-align: center; padding: 20px;">No opportunities available</div>'
    
    html_content += '</div></div>'  # Close dashboard and risk-matrix
    
    html_content += """
    
    <!-- TOP PICKS SECTION -->
    <h3>Top Picks at a Glance</h3>
    <div class="top-picks-container">
"""
    
    # Add picks (negative = bearish, positive = bullish)
    bearish_picks = [r for r in scored if r.get('final_score', 0) < -0.05][:3]
    bullish_picks = [r for r in scored if r.get('final_score', 0) > 0.05][:3]
    
    html_content += '<div class="picks-card bearish"><h4>📉 Top Bearish</h4>'
    if bearish_picks:
        for pick in bearish_picks:
            symbol = pick.get('symbol', 'N/A')
            score = pick.get('final_score', 0)
            conf = pick.get('confidence', 0) or 0
            price = pick.get('price', 0) or 0
            html_content += f'''<div class="pick-item">
                <span class="pick-symbol">{symbol}</span>
                <span class="pick-score bear">{score:+.3f}</span>
                <span class="pick-details">{conf:.0f}% | ₹{price:,.0f}</span>
            </div>'''
    else:
        html_content += '<div class="pick-item" style="color: #a0aec0;">No bearish picks</div>'
    html_content += '</div>'
    
    html_content += '<div class="picks-card bullish"><h4>📈 Top Bullish</h4>'
    if bullish_picks:
        for pick in bullish_picks:
            symbol = pick.get('symbol', 'N/A')
            score = pick.get('final_score', 0)
            conf = pick.get('confidence', 0) or 0
            price = pick.get('price', 0) or 0
            html_content += f'''<div class="pick-item">
                <span class="pick-symbol">{symbol}</span>
                <span class="pick-score bull">{score:+.3f}</span>
                <span class="pick-details">{conf:.0f}% | ₹{price:,.0f}</span>
            </div>'''
    else:
        html_content += '<div class="pick-item" style="color: #a0aec0;">No bullish picks</div>'
    html_content += '</div></div>'
    
    # Add sectoral heatmap
    html_content += '<h3>Sectoral Heat Map</h3><div class="sector-heatmap">'
    
    for sector in sorted(sector_scores.keys()):
        data = sector_scores[sector]
        avg_score = data['avg']
        count = data['count']
        bg_color = get_sector_color(sector)
        text_color = get_sector_text_color(bg_color)
        
        # Determine sentiment badge
        if avg_score > 0.05:
            sentiment = "Bullish"
        elif avg_score < -0.05:
            sentiment = "Bearish"
        else:
            sentiment = "Neutral"
        
        # Use gradient for neutral sectors (red to green)
        if -0.05 <= avg_score <= 0.05:
            bg_color = "linear-gradient(135deg, #f56565 0%, #38ef7d 100%)"
            text_color = "#ffffff"
        
        html_content += f'''<div class="sector-card" style="background: {bg_color}; color: {text_color};">
            <div class="sector-name">{sector}</div>
            <div class="sector-score">{avg_score:+.3f}</div>
            <div class="sector-count">{count} stocks | {sentiment}</div>
        </div>'''
    
    html_content += '</div>'
    
    html_content += """
    <h3>Full Screener Results</h3>
    <div class="controls">
        <div class="control-group">
            <input class="search" id="search" placeholder="Filter symbols or text..." onkeyup="filterTable()" />
        </div>
        <div class="control-group">
            <label for="sectorFilter">Sector:</label>
            <select id="sectorFilter" onchange="filterTable()">
                <option value="all">All</option>
            </select>
        </div>
        <div class="control-group">
            <label><input type="checkbox" id="enableMinConf" onchange="filterTable()" /> Min Confidence %</label>
            <input type="range" id="minConf" min="0" max="100" step="1" value="0" oninput="document.getElementById('minConfVal').innerText=this.value;filterTable()" />
            <span id="minConfVal">0</span>
        </div>
    </div>
    
    <table id="screener">
        <thead>
            <tr>
                <th data-type="num" onclick="sortTable(this, 'num')" title="Position rank by bearness score"><span class="tooltip">Rank<span class="tooltiptext">Position rank ordered by bearness score (most bearish first)</span></span></th>
                <th data-type="str" onclick="sortTable(this, 'str')" title="Stock symbol"><span class="tooltip">Symbol<span class="tooltiptext">NSE stock symbol/ticker</span></span></th>
                <th data-type="str" onclick="sortTable(this, 'str')" title="Industry sector"><span class="tooltip">Sector<span class="tooltiptext">Industry classification (Banking, IT, Auto, etc.)</span></span></th>
                <th data-type="str" onclick="sortTable(this, 'str')" title="Price pattern"><span class="tooltip">Pattern<span class="tooltiptext">Technical pattern: golden cross, death cross, consolidation, etc.</span></span></th>
                <th data-type="str" onclick="sortTable(this, 'str')" title="Trend direction"><span class="tooltip">Trend<span class="tooltiptext">Overall trend: uptrend, downtrend, or sideways</span></span></th>
                <th data-type="str" onclick="sortTable(this, 'str')" title="Timeframe alignment"><span class="tooltip">TF Align<span class="tooltiptext">Alignment across timeframes (intraday/swing/longterm)</span></span></th>
                <th data-type="str" onclick="sortTable(this, 'str')" title="Trading strategy"><span class="tooltip">Strategy<span class="tooltiptext">Recommended strategy (swing, breakout, mean reversion)</span></span></th>
                <th data-type="num" onclick="sortTable(this, 'num')" title="Bearness score -1 to +1"><span class="tooltip">Score<span class="tooltiptext">Bearness score: -1 (bullish) to +1 (bearish), 0 (neutral)</span></span></th>
                <th data-type="num" onclick="sortTable(this, 'num')" title="Signal confidence 0-100%"><span class="tooltip">Conf%<span class="tooltiptext">Confidence in signal (0-100%): higher = more reliable</span></span></th>
                <th data-type="num" onclick="sortTable(this, 'num')" title="Current price"><span class="tooltip">Price<span class="tooltiptext">Current closing price in rupees</span></span></th>
                <th data-type="num" onclick="sortTable(this, 'num')" title="Suggested stop loss"><span class="tooltip">Stop Loss<span class="tooltiptext">Suggested stop loss price (2.5× ATR from entry)</span></span></th>
                <th data-type="num" onclick="sortTable(this, 'num')" title="Suggested target"><span class="tooltip">Target<span class="tooltiptext">Suggested profit target (4.5× ATR from entry)</span></span></th>
                <th data-type="num" onclick="sortTable(this, 'num')" title="Risk to reward ratio"><span class="tooltip">R:R<span class="tooltiptext">Risk-to-reward ratio (target gain vs stop loss risk)</span></span></th>
                <th data-type="num" onclick="sortTable(this, 'num')" title="Position size"><span class="tooltip">Pos Size<span class="tooltiptext">Suggested position size (shares) at 2% risk</span></span></th>
                <th data-type="num" onclick="sortTable(this, 'num')" title="52-week high"><span class="tooltip">52W High<span class="tooltiptext">52-week high price</span></span></th>
                <th data-type="num" onclick="sortTable(this, 'num')" title="52-week low"><span class="tooltip">52W Low<span class="tooltiptext">52-week low price</span></span></th>
                <th data-type="num" onclick="sortTable(this, 'num')" title="Daily % change"><span class="tooltip">Daily%<span class="tooltiptext">Percentage change from yesterday's close</span></span></th>
                <th data-type="num" onclick="sortTable(this, 'num')" title="Weekly % change"><span class="tooltip">Weekly%<span class="tooltiptext">Percentage change from last week's close</span></span></th>
                <th data-type="num" onclick="sortTable(this, 'num')" title="% below 52-week high"><span class="tooltip">52W High %<span class="tooltiptext">Percentage below 52-week high (pullback magnitude)</span></span></th>
                <th data-type="num" onclick="sortTable(this, 'num')" title="% above 52-week low"><span class="tooltip">52W Low %<span class="tooltiptext">Percentage above 52-week low (recovery distance)</span></span></th>
                <th data-type="num" onclick="sortTable(this, 'num')" title="Opening range score -1 to +1"><span class="tooltip">OR<span class="tooltiptext">Opening range score: price vs first 30min high/low (-1 to +1)</span></span></th>
                <th data-type="num" onclick="sortTable(this, 'num')" title="VWAP score -1 to +1"><span class="tooltip">VWAP<span class="tooltiptext">Volume-weighted average price score (-1: below, +1: above)</span></span></th>
                <th data-type="num" onclick="sortTable(this, 'num')" title="Price structure score -1 to +1"><span class="tooltip">Structure<span class="tooltiptext">Price structure quality (-1: weak, +1: strong reversal pattern)</span></span></th>
                <th data-type="num" onclick="sortTable(this, 'num')" title="RSI momentum score"><span class="tooltip">RSI<span class="tooltiptext">Relative Strength Index score (-1 oversold to +1 overbought)</span></span></th>
                <th data-type="num" onclick="sortTable(this, 'num')" title="EMA trend score -1 to +1"><span class="tooltip">EMA<span class="tooltiptext">Exponential moving average trend score (-1: bearish, +1: bullish)</span></span></th>
                <th data-type="num" onclick="sortTable(this, 'num')" title="Volume score -1 to +1"><span class="tooltip">Vol<span class="tooltiptext">Volume analysis score (-1: low/decreasing, +1: high/increasing)</span></span></th>
                <th data-type="num" onclick="sortTable(this, 'num')" title="MACD momentum -1 to +1"><span class="tooltip">MACD<span class="tooltiptext">MACD momentum score (-1: bearish divergence, +1: bullish)</span></span></th>
                <th data-type="num" onclick="sortTable(this, 'num')" title="Bollinger Band score -1 to +1"><span class="tooltip">BB<span class="tooltiptext">Bollinger Band score (-1: at lower band, +1: at upper band)</span></span></th>
                <th data-type="num" onclick="sortTable(this, 'num')" title="Average true range"><span class="tooltip">ATR<span class="tooltiptext">Average True Range: volatility measure (stop/target distance)</span></span></th>
                <th data-type="num" onclick="sortTable(this, 'num')" title="Option pricing score -1 to +1"><span class="tooltip">Opt Score<span class="tooltiptext">Option attractiveness (-1: expensive/high IV, +1: cheap/low IV)</span></span></th>
                <th data-type="num" onclick="sortTable(this, 'num')" title="Option implied volatility"><span class="tooltip">Opt IV<span class="tooltiptext">Implied volatility (0-1 scale, lower = more stable)</span></span></th>
                <th data-type="num" onclick="sortTable(this, 'num')" title="Option bid-ask spread %"><span class="tooltip">Opt Spread%<span class="tooltiptext">Bid-ask spread % (lower = more liquid)</span></span></th>
                <th data-type="num" onclick="sortTable(this, 'num')" title="Option delta"><span class="tooltip">Opt Delta<span class="tooltiptext">Delta: directional sensitivity (0.5 = ATM, >0.5 = ITM)</span></span></th>
                <th data-type="num" onclick="sortTable(this, 'num')" title="Option gamma"><span class="tooltip">Opt Gamma<span class="tooltiptext">Gamma: rate of delta change (higher = more sensitive)</span></span></th>
                <th data-type="num" onclick="sortTable(this, 'num')" title="Option theta daily decay"><span class="tooltip">Opt Theta<span class="tooltiptext">Theta: daily time decay (negative = cost to buyer)</span></span></th>
                <th data-type="num" onclick="sortTable(this, 'num')" title="Option vega volatility sensitivity"><span class="tooltip">Opt Vega<span class="tooltiptext">Vega: volatility sensitivity (per 1% IV change)</span></span></th>
            </tr>
        </thead>
        <tbody>
"""
    
    for i, r in enumerate(scored, 1):
        # COMPREHENSIVE TYPE CONVERSIONS - ensure no None/string comparisons
        price = r.get('price', 0) or 0
        atr_val = r.get('atr') or 0
        conf_val = r.get('confidence', 0) or 0
        
        # Ensure all numeric types are float, never None or str
        try:
            price = float(price) if price else 0
        except (TypeError, ValueError):
            price = 0
        
        try:
            conf_val = float(conf_val) if conf_val else 0
        except (TypeError, ValueError):
            conf_val = 0
        
        try:
            atr_val = float(atr_val) if atr_val else 0
        except (TypeError, ValueError):
            atr_val = 0
        
        conf_str = f"{conf_val:.0f}" if conf_val is not None else "N/A"
        
        score = r.get('final_score')
        score = score if score is not None else 0
        try:
            score = float(score) if score is not None else 0
        except (TypeError, ValueError):
            score = 0
        
        # Calculate Trend Strength (Accelerating/Stable/Weakening)
        score_5m = r.get('score_5m', 0) or 0
        score_15m = r.get('score_15m', 0) or 0
        score_1h = r.get('score_1h', 0) or 0
        
        # Detect trend: compare direction and magnitude changes
        # If scores are moving toward more negative (more bearish), it's accelerating
        # If scores are moving toward less negative (less bearish), it's weakening
        trend_5_15 = score_15m - score_5m  # If negative, 15m is more bearish than 5m
        trend_15_1h = score_1h - score_15m  # If negative, 1h is more bearish than 15m
        
        if abs(trend_5_15) < 0.05 and abs(trend_15_1h) < 0.05:
            trend_strength = "Stable"
            trend_badge = "→"
            trend_color = "#95a5a6"  # gray
        elif trend_5_15 < -0.02 and trend_15_1h < -0.02:
            # Both moving toward more negative = accelerating bearishness
            trend_strength = "Accelerating"
            trend_badge = "↑"
            trend_color = "#c0392b"  # red for accelerating bearishness
        elif trend_5_15 > 0.02 and trend_15_1h > 0.02:
            # Both moving toward less negative = weakening bearishness
            trend_strength = "Weakening"
            trend_badge = "↓"
            trend_color = "#27ae60"  # green for weakening bearishness
        else:
            trend_strength = "Mixed"
            trend_badge = "↔"
            trend_color = "#f39c12"  # orange for mixed signals
        
        trend_str = f"{trend_badge} {trend_strength}"
        
        # Calculate % Below High and % Above Low
        # Price Context Metrics - get 52W High/Low first
        week52_high = r.get('52w_high', price) or price
        week52_low = r.get('52w_low', price) or price
        
        # ENSURE THESE ARE ALWAYS NUMBERS, NEVER None OR str
        try:
            week52_high = float(week52_high) if week52_high else price
        except (TypeError, ValueError):
            week52_high = price
        
        try:
            week52_low = float(week52_low) if week52_low else price
        except (TypeError, ValueError):
            week52_low = price
        
        # % Below High = ((High - Price) / High) * 100
        pct_below_high = 0.0
        pct_below_high_str = "N/A"
        if week52_high and week52_high > 0:
            pct_below_high = ((week52_high - price) / week52_high) * 100
            pct_below_high_str = f"{pct_below_high:.2f}%"
        
        # % Above Low = ((Price - Low) / Low) * 100
        pct_above_low = 0.0
        pct_above_low_str = "N/A"
        if week52_low and week52_low > 0:
            pct_above_low = ((price - week52_low) / week52_low) * 100
            pct_above_low_str = f"{pct_above_low:.2f}%"
        
        # Determine Quality Grade (A-F) based on score and confidence
        abs_score_val = abs(score)
        if abs_score_val >= 0.15 and conf_val >= 45:
            grade = "A"
            grade_class = "grade-a"
        elif abs_score_val >= 0.10 and conf_val >= 40:
            grade = "B"
            grade_class = "grade-b"
        elif abs_score_val >= 0.06 and conf_val >= 35:
            grade = "C"
            grade_class = "grade-c"
        elif abs_score_val >= 0.03 and conf_val >= 25:
            grade = "D"
            grade_class = "grade-d"
        else:
            grade = "F"
            grade_class = "grade-f"
    
        sector = r.get('sector', 'Unknown')

        # Determine Trend Direction
        ema_score = r.get('ema_score', 0) or 0
        structure_score = r.get('structure_score', 0) or 0
        vwap_score = r.get('vwap_score', 0) or 0
        trend_strength = (ema_score + structure_score + vwap_score) / 3
        
        if score < -0.15:
            trend = "Strong Bear"
            trend_class = "trend-strong-bear"
        elif score < -0.05:
            trend = "Bear"
            trend_class = "trend-bear"
        elif score > 0.15:
            trend = "Strong Bull"
            trend_class = "trend-strong-bull"
        elif score > 0.05:
            trend = "Bull"
            trend_class = "trend-bull"
        else:
            trend = "Neutral"
            trend_class = "trend-neutral"
        
        # Market Regime
        regime = r.get('market_regime', 'Unknown')
        regime = regime if regime is not None else 'Unknown'
        regime_lower = regime.lower() if regime else 'unknown'
        
        if regime_lower in ['trending', 'trend']:
            regime_class = "regime-trending"
            regime_display = "Trending"
        elif regime_lower in ['ranging', 'range']:
            regime_class = "regime-ranging"
            regime_display = "Ranging"
        elif regime_lower in ['volatile', 'vol']:
            regime_class = "regime-volatile"
            regime_display = "Volatile"
        else:
            regime_class = "regime-quiet"
            regime_display = regime if regime != 'Unknown' else "N/A"
        
        # Timeframe Alignment (check if 5m, 15m, 1h scores agree)
        tf_5m = (r.get('score_5m') or 0) if r.get('score_5m') is not None else 0
        tf_15m = (r.get('score_15m') or 0) if r.get('score_15m') is not None else 0
        tf_1h = (r.get('score_1h') or 0) if r.get('score_1h') is not None else 0
        
        # Count how many timeframes agree on direction (positive/negative)
        tf_directions = [1 if s > 0 else -1 if s < 0 else 0 for s in [tf_5m, tf_15m, tf_1h]]
        tf_bullish = sum(1 for d in tf_directions if d > 0)
        tf_bearish = sum(1 for d in tf_directions if d < 0)
        tf_neutral = sum(1 for d in tf_directions if d == 0)
        
        if max(tf_bullish, tf_bearish) == 3:
            align = "✓✓✓"
            align_class = "align-strong"
        elif max(tf_bullish, tf_bearish) == 2:
            align = "✓✓✗"
            align_class = "align-medium"
        else:
            align = "✓✗✗"
            align_class = "align-weak"
        
        # Ensure align is not None before using it
        if align is None:
            align = "N/A"
            align_class = "align-weak"
        
        # Get TF alignment tooltip
        align_tooltip = TF_ALIGNMENT_TOOLTIPS.get(align, 'Multi-timeframe alignment status')
        
        # Score breakdown for tooltip
        score_tooltip = f"5m: {tf_5m:+.3f}\n15m: {tf_15m:+.3f}\n1h: {tf_1h:+.3f}"
        
        # Strategy Tagging based on option strategies (volatility-dependent)
        abs_score = abs(score) if score is not None else 0
        is_bearish = (score is not None) and (score < -0.05)
        is_bullish = (score is not None) and (score > 0.05)
        high_conf = conf_val >= 40
        med_conf = 25 <= conf_val < 40
        
        # Calculate volatility percentage (ATR / price * 100)
        atr_val = (r.get('atr') or 0) if r.get('atr') is not None else 0
        price = price if price is not None else 1
        if price > 0 and atr_val > 0:
            volatility_pct = (atr_val / price) * 100
        else:
            volatility_pct = 2.0  # Default middle-ground volatility
        
        # Get option strategy suggestion (with option_score NO-TRADE gate)
        option_score = r.get('option_score')
        strategy, strategy_class = suggest_option_strategy(is_bullish, is_bearish, volatility_pct, conf_val, abs_score, option_score)
        
        # POSITION SIZING & RISK MANAGEMENT
        # Configuration (can be made user-configurable)
        CAPITAL = 100000  # Trading capital in INR
        RISK_PER_TRADE = 0.02  # 2% risk per trade
        
        # Ensure all comparison variables are not None
        price = price if price is not None else 0
        conf_val = conf_val if conf_val is not None else 0
        
        # Dynamic stop-loss multiplier based on regime
        if regime_display == "Trending":
            sl_multiplier = 2.5  # Wider stops for trends
            base_rr = 2.0  # Base R:R for trends
        elif regime_display == "Ranging":
            sl_multiplier = 1.5  # Tighter stops for ranges
            base_rr = 1.5  # Base R:R for ranges (harder to get big moves)
        elif regime_display == "Volatile":
            sl_multiplier = 3.0  # Very wide stops for volatility
            base_rr = 1.8  # Base R:R for volatile (unpredictable)
        else:
            sl_multiplier = 2.0  # Default
            base_rr = 2.0  # Default base
        
        # DYNAMIC R:R CALCULATION based on signal quality
        rr_multiplier = 1.0
        
        # 1. Confidence boost (higher confidence = better R:R expectation)
        if conf_val >= 60:
            rr_multiplier += 0.5  # Very high confidence
        elif conf_val >= 50:
            rr_multiplier += 0.3
        elif conf_val >= 40:
            rr_multiplier += 0.15
        elif conf_val < 30:
            rr_multiplier -= 0.2  # Low confidence = lower target
        
        # 2. Signal strength boost (stronger signals can capture bigger moves)
        if abs_score >= 0.25:
            rr_multiplier += 0.4  # Very strong signal
        elif abs_score >= 0.15:
            rr_multiplier += 0.25
        elif abs_score >= 0.10:
            rr_multiplier += 0.1
        
        # 3. Timeframe alignment boost (better alignment = higher probability of continuation)
        if align == "✓✓✓":
            rr_multiplier += 0.3  # All timeframes aligned
        elif align == "✓✓✗":
            rr_multiplier += 0.1  # Partial alignment
        else:
            rr_multiplier -= 0.15  # Weak alignment = lower target
        
        # 4. Strategy-specific adjustment
        if strategy in ["Trending Short", "Trending Long"]:
            rr_multiplier += 0.3  # Trend trades can capture larger moves
        elif strategy in ["Fade Extreme", "Range Trade"]:
            rr_multiplier -= 0.2  # Mean reversion = limited upside
        elif strategy == "Avoid":
            rr_multiplier = 0.5  # Very conservative if trading at all
        
        # 5. Market structure adjustment (price position in 52W range)
        if pct_below_high < 5 and is_bullish:
            rr_multiplier -= 0.2  # Near highs, limited upside for longs
        elif pct_above_low < 5 and is_bearish:
            rr_multiplier -= 0.2  # Near lows, limited downside for shorts
        elif 40 < pct_below_high < 60:
            rr_multiplier += 0.1  # Mid-range, good setup
        
        # Calculate final R:R (minimum 1.0, maximum 5.0)
        rr_ratio = max(1.0, min(5.0, base_rr * rr_multiplier))
        
        # Calculate stop-loss and target
        if atr_val > 0 and price > 0:
            if is_bearish:  # Short trade
                stop_loss = price + (atr_val * sl_multiplier)
                risk_per_share = stop_loss - price
                target = price - (risk_per_share * rr_ratio)
            elif is_bullish:  # Long trade
                stop_loss = price - (atr_val * sl_multiplier)
                risk_per_share = price - stop_loss
                target = price + (risk_per_share * rr_ratio)
            else:  # Neutral
                stop_loss = 0
                target = 0
                risk_per_share = 0
            
            # Position sizing: shares = (capital * risk%) / risk_per_share
            if risk_per_share > 0:
                max_shares = int((CAPITAL * RISK_PER_TRADE) / risk_per_share)
                position_value = max_shares * price
                position_size = min(max_shares, int(CAPITAL * 0.2 / price))  # Max 20% of capital per position
            else:
                position_size = 0
                position_value = 0
        else:
            stop_loss = 0
            target = 0
            position_size = 0
            risk_per_share = 0
            rr_ratio = 0
        
        # Format display strings
        sl_str = f"{stop_loss:.2f}" if stop_loss > 0 else "N/A"
        target_str = f"{target:.2f}" if target > 0 else "N/A"
        rr_str = f"1:{rr_ratio:.1f}" if rr_ratio > 0 else "N/A"
        pos_size_str = f"{position_size}" if position_size > 0 else "N/A"
        
        # Color coding for R:R
        if rr_ratio >= 3.0:
            rr_color = "#27ae60"  # Green - excellent
        elif rr_ratio >= 2.0:
            rr_color = "#3498db"  # Blue - good
        elif rr_ratio >= 1.5:
            rr_color = "#f39c12"  # Orange - acceptable
        else:
            rr_color = "#e74c3c"  # Red - poor
        
        # Daily and Weekly Change %
        daily_change = r.get('daily_change_pct', 0) or 0
        weekly_change = r.get('weekly_change_pct', 0) or 0
        try:
            daily_change = float(daily_change) if daily_change else 0
        except (TypeError, ValueError):
            daily_change = 0
        try:
            weekly_change = float(weekly_change) if weekly_change else 0
        except (TypeError, ValueError):
            weekly_change = 0
        
        daily_str = f"{daily_change:+.2f}%" if daily_change != 0 else "N/A"
        weekly_str = f"{weekly_change:+.2f}%" if weekly_change != 0 else "N/A"
        daily_color = "#27ae60" if daily_change > 0 else "#e74c3c" if daily_change < 0 else "#95a5a6"
        weekly_color = "#27ae60" if weekly_change > 0 else "#e74c3c" if weekly_change < 0 else "#95a5a6"
        
        # Pivot Points (Classic) - calculated from swing candles
        candles = r.get('candles_data', {})
        if candles and candles.get('swing') and len(candles['swing']) > 0:
            recent_candle = candles['swing'][-1]  # Most recent 15m candle
            high = recent_candle.get('high', price)
            low = recent_candle.get('low', price)
            close = recent_candle.get('close', price)
        else:
            high = price
            low = price
            close = price
        pivot = (high + low + close) / 3
        r1 = (2 * pivot) - low
        s1 = (2 * pivot) - high
        r2 = pivot + (high - low)
        s2 = pivot - (high - low)
        pivot_str = f"S2:{s2:.0f} S1:{s1:.0f} P:{pivot:.0f} R1:{r1:.0f} R2:{r2:.0f}"
        
        # Color scoring: hue from 0 (red/bearish) to 120 (green/bullish)
        score_normalized = max(-1, min(1, score))
        hue = 60 + (score_normalized * 60)  # 0-120 range
        score_style = f"background-color: hsl({hue}, 80%, 92%);"
        
        atr_str = "N/A" if atr_val is None else f"{atr_val:.2f}"
        
        # Get pattern information and color
        pattern = r.get('pattern', 'None')
        pattern_conf = r.get('pattern_confidence', 0) or 0
        pattern_detail = r.get('pattern_detail', {})
        
        # Pattern coloring: bearish=red, bullish=green
        bearish_patterns = ['Double Top', 'Head & Shoulders', 'Descending Triangle', 'Rising Wedge']
        bullish_patterns = ['Double Bottom', 'Inverted H&S', 'Ascending Triangle', 'Falling Wedge']
        
        if pattern in bearish_patterns:
            pattern_color = '#c0392b'  # Red for bearish
            pattern_badge = '📉'
        elif pattern in bullish_patterns:
            pattern_color = '#27ae60'  # Green for bullish
            pattern_badge = '📈'
        else:
            pattern_color = '#95a5a6'  # Gray for no pattern
            pattern_badge = '—'
        
        # Build pattern tooltip
        if pattern != 'None' and pattern_detail:
            timeframe = pattern_detail.get('timeframe', '5m')
            aligned_tfs = pattern_detail.get('aligned_timeframes', [])
            description = pattern_detail.get('description', '')
            image = pattern_detail.get('image', '')
            reliability = pattern_detail.get('reliability', 'Unknown')
            bias = pattern_detail.get('bias', 'unknown')
            
            # Format aligned timeframes
            aligned_str = ', '.join(aligned_tfs) if aligned_tfs else timeframe
            
            # Create rich tooltip with colored diagram
            tooltip_text = f"""<div style="background: #f8f9fa; padding: 12px; border-radius: 4px; border-left: 4px solid {pattern_color}; max-width: 400px;">
                <div style="font-weight: bold; color: {pattern_color}; margin-bottom: 8px; font-size: 13px;">
                    {pattern_badge} {pattern} ({timeframe})
                </div>
                <div style="font-size: 11px; color: #2c3e50; margin-bottom: 6px;">
                    <strong>Confidence:</strong> {pattern_conf:.0%} | <strong>Reliability:</strong> {reliability}
                </div>
                <div style="font-size: 11px; color: #34495e; margin-bottom: 6px;">
                    <strong>Aligned TFs:</strong> {aligned_str}
                </div>
                <div style="font-size: 11px; color: #34495e; margin-bottom: 8px;">
                    {description}
                </div>
                <div style="background: white; padding: 10px; border-radius: 3px; font-family: monospace; font-size: 11px; line-height: 1.5; color: #2c3e50; border: 1px solid #ecf0f1; white-space: pre-wrap; word-break: break-word;">
                    {image}
                </div>
            </div>"""
            
            pattern_str = f"<span class='tooltip' style='color: {pattern_color}; font-weight: bold; cursor: help; border-bottom: 2px dashed {pattern_color};'>{pattern_badge} {pattern}<span class='tooltiptext' style='width: 420px; left: -210px;'>{tooltip_text}</span></span><br/><small style='color: {pattern_color};'>Conf: {pattern_conf:.0%}</small>"
        else:
            pattern_str = f"<span style='color: {pattern_color};'>—</span>"
        
        # Get sector color based on sector performance
        sector_color = get_sector_color(sector)
        sector_text_color = get_sector_text_color(sector_color)
        
        html_content += f"""            <tr>
                <td>{i}</td>
                <td><strong>{r['symbol']}</strong></td>
                <td style="background-color: {sector_color}; color: {sector_text_color}; font-weight: bold;">{sector}</td>
                <td>{pattern_str}</td>
                <td><span class="badge {trend_class}">{trend}</span></td>
                <td><span class="{align_class} tooltip-trigger" title="{align_tooltip}">{align}<span class="tooltiptext" style="width: 300px; bottom: 125%;">{align_tooltip}</span></span></td>
                <td><span class="badge {strategy_class} tooltip-trigger" style="font-size: 0.85em; padding: 4px 8px; position: relative;" title="{STRATEGY_TOOLTIPS.get(strategy_class, 'Option strategy recommendation')}">{strategy}<span class="tooltiptext" style="width: 320px; bottom: 125%; left: 50%; transform: translateX(-50%);">{STRATEGY_TOOLTIPS.get(strategy_class, 'Option strategy recommendation')}</span></span></td>
                <td class="score tooltip" style="{score_style}" data-score="{score:+.4f}"><span style="color: {trend_color}; font-weight: bold;">{trend_badge}</span> {score:+.4f}<span class="tooltiptext">{score_tooltip}</span></td>
                <td data-conf="{conf_val}">{conf_str}</td>
                <td data-price="{price:.2f}">{price:.2f}</td>
                <td data-sl="{stop_loss:.2f}" style="font-weight: bold; color: #e74c3c;">{sl_str}</td>
                <td data-target="{target:.2f}" style="font-weight: bold; color: #27ae60;">{target_str}</td>
                <td data-rr="{rr_ratio:.2f}" style="font-weight: bold; color: {rr_color};">{rr_str}</td>
                <td data-pos="{position_size}" style="font-weight: bold; color: #3498db;">{pos_size_str}</td>
                <td data-score="{week52_high:.2f}" style="font-weight: bold; color: #27ae60;">{week52_high:.2f}</td>
                <td data-score="{week52_low:.2f}" style="font-weight: bold; color: #c0392b;">{week52_low:.2f}</td>
                <td data-score="{daily_change:.2f}" style="color: {daily_color}; font-weight: bold;">{daily_str}</td>
                <td data-score="{weekly_change:.2f}" style="color: {weekly_color}; font-weight: bold;">{weekly_str}</td>
                <td data-score="{pct_below_high:.2f}" style="font-weight: bold; color: #e67e22;">{pct_below_high_str}</td>
                <td data-score="{pct_above_low:.2f}" style="font-weight: bold; color: #3498db;">{pct_above_low_str}</td>
                <td>{r.get('or_score', 0):+.4f}</td>
                <td>{r.get('vwap_score', 0):+.4f}</td>
                <td>{r.get('structure_score', 0):+.4f}</td>
                <td>{r.get('rsi') or 0:.2f}</td>
                <td>{r.get('ema_score', 0):+.4f}</td>
                <td>{r.get('volume_score', 0):+.4f}</td>
                <td>{r.get('macd_score', 0):+.4f}</td>
                <td>{r.get('bb_score', 0):+.4f}</td>
                <td>{atr_str}</td>
                <td>{r.get('option_score') or 0:+.4f}</td>
                <td>{r.get('option_iv') or 0:.4f}</td>
                <td>{r.get('option_spread_pct') or 0:.4f}</td>
                <td>{r.get('option_delta') or 0:+.4f}</td>
                <td>{r.get('option_gamma') or 0:.6f}</td>
                <td>{r.get('option_theta') or 0:+.4f}</td>
                <td>{r.get('option_vega') or 0:+.4f}</td>
            </tr>
"""
    
    html_content += """        </tbody>
    </table>
"""
    
    nodata = [r for r in results if r.get("final_score") is None]
    if nodata:
        nodata_symbols = ", ".join(r['symbol'] for r in nodata)
        html_content += f"""    <div class="no-data">
        <p><strong>Symbols with no data ({len(nodata)}):</strong> {nodata_symbols}</p>
    </div>
"""
    
    html_content += """    <script>
let lastSort = {col: null, asc: true};

function sortTable(th, type) {
    const table = document.getElementById("screener");
    const tbody = table.tBodies[0];
    const rows = Array.from(tbody.rows);
    const idx = Array.from(th.parentNode.children).indexOf(th);
    const asc = !(lastSort.col === idx && lastSort.asc);
    
    rows.sort((a, b) => {
        let cellA = a.cells[idx];
        let cellB = b.cells[idx];
        
        let va = cellA.getAttribute("data-score") || cellA.getAttribute("data-conf") || cellA.getAttribute("data-price") || cellA.innerText.trim();
        let vb = cellB.getAttribute("data-score") || cellB.getAttribute("data-conf") || cellB.getAttribute("data-price") || cellB.innerText.trim();
        
        if (type === "num") {
            va = parseFloat(va) || 0;
            vb = parseFloat(vb) || 0;
        } else {
            va = va.toLowerCase();
            vb = vb.toLowerCase();
        }
        
        if (va < vb) return asc ? -1 : 1;
        if (va > vb) return asc ? 1 : -1;
        return 0;
    });
    
    rows.forEach(r => tbody.appendChild(r));
    
    document.querySelectorAll('th').forEach(h => h.classList.remove('sort-asc', 'sort-desc'));
    if (asc) th.classList.add('sort-asc');
    else th.classList.add('sort-desc');
    
    lastSort = {col: idx, asc: asc};
}

function filterTable() {
    const v = document.getElementById("search").value.toLowerCase();
    const rows = document.getElementById("screener").tBodies[0].rows;
    const enableConf = document.getElementById("enableMinConf").checked;
    const minConf = parseFloat(document.getElementById("minConf").value) || 0;
    const sectorSel = document.getElementById("sectorFilter").value.toLowerCase();
    
    for (let i = 0; i < rows.length; i++) {
        const r = rows[i];
        const textMatch = r.innerText.toLowerCase().includes(v);
        
        let confVal = 0;
        // Column positions: 0 Rank, 1 Symbol, 2 Sector, 3 Pattern, 4 Trend, 5 TF Align, 6 Strategy, 7 Score, 8 Conf%, 9 Price, 10 SL, 11 Target, 12 R:R, 13 Pos Size
        if (r.cells[8]) {
            const confText = r.cells[8].getAttribute("data-conf") || r.cells[8].innerText.trim();
            confVal = parseFloat(confText) || 0;
        }
        
        const sectorCell = r.cells[2] ? (r.cells[2].innerText || "").toLowerCase() : "";
        const sectorMatch = (sectorSel === "all") || (sectorCell === sectorSel);
        const confMatch = (!enableConf) || (confVal >= minConf);
        r.style.display = (textMatch && sectorMatch && confMatch) ? "" : "none";
    }
}

// Populate sector dropdown from table rows
function populateSectors() {
    const rows = document.getElementById("screener").tBodies[0].rows;
    const sectors = new Set();
    for (let i = 0; i < rows.length; i++) {
        const cell = rows[i].cells[2];
        if (cell) {
            const sec = (cell.innerText || "").trim();
            if (sec) sectors.add(sec);
        }
    }
    const select = document.getElementById("sectorFilter");
    const existing = new Set();
    // Keep "All" default
    for (let i = select.options.length - 1; i >= 0; i--) {
        existing.add(select.options[i].value);
    }
    Array.from(sectors).sort().forEach(sec => {
        const val = sec;
        if (!existing.has(val)) {
            const opt = document.createElement("option");
            opt.value = val;
            opt.text = sec;
            select.appendChild(opt);
        }
    });
}

document.addEventListener("DOMContentLoaded", () => {
    populateSectors();
    filterTable();
});
    </script>
</body>
</html>
"""
    
    with open(output_path, "w", encoding='utf-8') as f:
        f.write(html_content)
    
    print(f"\nSaved results to {output_path}")


def main():
    parser = argparse.ArgumentParser(description='Rank stocks by bearness - Refactored V2')
    parser.add_argument('--universe', choices=['nifty', 'banknifty', 'nifty100', 'nifty200', 'all'], default='nifty')
    parser.add_argument('--mode', default='swing', choices=['intraday', 'swing', 'longterm', 'custom'])
    parser.add_argument('--intraday-w', type=float, default=None)
    parser.add_argument('--swing-w', type=float, default=None)
    parser.add_argument('--longterm-w', type=float, default=None)
    parser.add_argument('--use-yf', action='store_true')
    parser.add_argument('--force-yf', action='store_true')
    parser.add_argument('--quick', action='store_true')
    parser.add_argument('--parallel', type=int, default=8)
    parser.add_argument('--export', help='Output CSV path')
    parser.add_argument('--screener-format', choices=['csv', 'html'], default='csv', help='Export format')
    parser.add_argument('--fetch', action='store_true')
    parser.add_argument('--save-db', action='store_true', help='Automatically load results to database')
    args = parser.parse_args()
    
    # Load universe
    syms = UniverseManager.load(universe=args.universe, fetch_if_missing=True)
    print(f"Loaded {len(syms)} symbols")
    if args.quick:
        print("[QUICK MODE] ~40% faster: fewer candles + reduced retries")
    if syms:
        print(', '.join(s for s, u in syms))
    
    if not syms:
        return
    
    # Show mode
    mode_info = {
        'intraday': 'Intraday (5m only) - Sharp & reactive',
        'swing': 'Swing (50/30/20) - Balanced multi-timeframe',
        'longterm': 'Long-term (20/30/50) - Trend-focused',
        'custom': f'Custom weights'
    }
    print(f"\n[MODE] {mode_info.get(args.mode, 'Unknown')}")
    
    # Create scoring engine
    engine = BearnessScoringEngine(
        mode=args.mode,
        use_yf=args.use_yf,
        force_yf=args.force_yf,
        quick_mode=args.quick,
        intraday_weight=args.intraday_w,
        swing_weight=args.swing_w,
        longterm_weight=args.longterm_w
    )
    
    # Compute scores in parallel
    results = []
    with ThreadPoolExecutor(max_workers=max(1, args.parallel)) as exe:
        futures = {}
        for sym, u in syms:
            futures[exe.submit(engine.compute_score, sym)] = (sym, u)
        
        for fut in as_completed(futures):
            sym, u = futures[fut]
            try:
                data = fut.result()
                if data:
                    data['index'] = u
                    results.append(data)
                    if data.get('status') == 'OK':
                        print(f"Processing {sym}... done (score={data['final_score']:.2f})")
                    else:
                        print(f"Processing {sym}... skipped (no data)")
            except Exception as e:
                print(f"{sym}: error -> {e}")
                results.append({"symbol": sym, "status": "ERROR", "index": u})
    
    # Enrich with sector info (using modular sector_mapper)
    for r in results:
        r['sector'] = get_sector(r.get('symbol', ''))

    # Compute index bias and print actionable picks first
    idx_bias, idx_src = _compute_index_bias(engine, results=results)
    print_actionables(results, index_bias=idx_bias, conf_threshold=35.0, score_threshold=0.15)

    # Print and save full results
    print_results(results)
    
    # Always save CSV for downstream parsing
    csv_path = args.export if (args.export and str(args.export).lower().endswith('.csv')) else OUT_CSV
    save_csv(results, csv_path, args)

    # Save HTML - ORIGINAL HTML is PRIMARY (saved to root + reports folder)
    if args.screener_format == 'html':
        html_path = args.export if (args.export and str(args.export).lower().endswith('.html')) else str(Path(csv_path).with_suffix('.html'))
        
        # Save ORIGINAL HTML to root (PRIMARY)
        save_html(results, html_path, args)
        print(f"[OK] Original HTML saved to {html_path}")
        
        # Also copy to reports folder with timestamp
        try:
            reports_dir = Path(csv_path).parent / "reports"
            reports_dir.mkdir(exist_ok=True)
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            
            # Copy original HTML to reports with timestamp
            original_html_copy = reports_dir / f"nifty_bearnness_{timestamp}.html"
            shutil.copy(html_path, original_html_copy)
            print(f"[OK] Copied to reports folder: {original_html_copy}")
        except Exception as e:
            print(f"[WARN] Could not copy to reports folder: {e}")
        
        # Also generate ENHANCED version if user wants extra visuals (SECONDARY)
        try:
            reporter = EnhancedReportGenerator()
            
            # Organize picks by direction
            bullish_picks = [r for r in results if r.get('final_score') and r['final_score'] > 0.05]
            bearish_picks = [r for r in results if r.get('final_score') and r['final_score'] < -0.05]
            
            picks_data = {
                'bullish': bullish_picks,
                'bearish': bearish_picks
            }
            
            report_title = f"NIFTY {args.universe.upper()} Screener - {args.mode.upper()} Mode"
            
            html_content = reporter.generate_report(
                title=report_title,
                picks_data=picks_data,
                index_bias=idx_bias,
                index_price=None  # Can add NIFTY price here if available
            )
            
            # Save enhanced version to reports directory with timestamp
            reports_dir = Path(csv_path).parent / "reports"
            reports_dir.mkdir(exist_ok=True)
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            enhanced_html = reports_dir / f"screener_report_enhanced_{args.universe}_{args.mode}_{timestamp}.html"
            enhanced_html.write_text(html_content, encoding='utf-8')
            print(f"[OK] Enhanced HTML also generated: {enhanced_html}")
        except Exception as e:
            print(f"[INFO] Enhanced reporter skipped: {e}")
    
    # Record picks to performance database
    try:
        tracker = get_tracker()
        bullish_picks = [r for r in results if r.get('final_score') and r['final_score'] > 0.05]
        bearish_picks = [r for r in results if r.get('final_score') and r['final_score'] < -0.05]
        
        for pick in bullish_picks + bearish_picks:
            direction = "bullish" if pick['final_score'] > 0 else "bearish"
            tracker.record_pick(
                symbol=pick['symbol'],
                direction=direction,
                score=float(pick['final_score']),
                price=float(pick['price'] or 0),
                rsi=float(pick.get('rsi', 50)),
                ema_trend=float(pick.get('ema_score', 0)),
                atr=float(pick.get('atr', 0)),
                confidence="high" if pick.get('confidence', 0) > 70 else ("medium" if pick.get('confidence', 0) > 40 else "low"),
                notes=f"From {args.universe} {args.mode} screener"
            )
        
        stats = tracker.get_performance_stats(days=30)
        print(f"\n[PERF] 30-day stats: {stats['total_picks']} picks, {stats['win_rate']:.1f}% win rate")
    except Exception as e:
        print(f"[WARN] Performance tracking failed: {e}")
    
    # Auto-load to database if requested
    if args.save_db:
        _load_results_to_database(csv_path)
        print(f"\n[SUCCESS] Results automatically saved to database")


if __name__ == '__main__':
    main()
