# Shared institutional context score logic
import math

def tanh(x):
    return math.tanh(x)


def generate_mini_chart_svg(candles_data, price, symbol, width=280, height=60):
    """
    Generate a minimal SVG sparkline chart for quick price trend visualization.
    
    Shows last ~30 candles with support/resistance levels marked.
    Color: Green (up) | Red (down) | Gray (neutral)
    
    Returns: SVG HTML string suitable for inline embedding
    """
    try:
        if not candles_data or not isinstance(candles_data, list) or len(candles_data) < 3:
            return ""  # Not enough data for chart
        
        # Take last 30 candles for performance
        candles = candles_data[-30:] if len(candles_data) > 30 else candles_data
        
        # Extract close prices
        closes = []
        for c in candles:
            close = c.get('close') or c.get('c')
            if close:
                try:
                    closes.append(float(close))
                except:
                    pass
        
        if len(closes) < 3:
            return ""  # Not enough valid prices
        
        # Calculate chart metrics
        min_price = min(closes)
        max_price = max(closes)
        price_range = max_price - min_price
        
        if price_range == 0:
            price_range = min_price * 0.01  # Avoid division by zero
        
        # Determine trend (first vs last)
        trend_up = closes[-1] > closes[0]
        line_color = "#27ae60" if trend_up else "#e74c3c"
        
        # SVG parameters
        margin = 8
        chart_width = width - (2 * margin)
        chart_height = height - (2 * margin)
        
        # Convert prices to SVG Y coordinates
        def price_to_y(p):
            normalized = (p - min_price) / price_range
            return margin + chart_height * (1 - normalized)
        
        # Generate path points
        points = []
        for i, price_val in enumerate(closes):
            x = margin + (i / (len(closes) - 1)) * chart_width if len(closes) > 1 else margin + chart_width / 2
            y = price_to_y(price_val)
            points.append(f"{x},{y}")
        
        path_d = " ".join([f"L {p}" for p in points])
        path_d = f"M {points[0]} {path_d}"  # Move to first point
        
        # Generate SVG with gradient
        svg = f'''<svg width="{width}" height="{height}" viewBox="0 0 {width} {height}" style="display: inline-block; vertical-align: middle; margin: 0 4px;">
            <defs>
                <linearGradient id="chart-grad-{symbol}" x1="0%" y1="0%" x2="0%" y2="100%">
                    <stop offset="0%" style="stop-color:{line_color};stop-opacity:0.3" />
                    <stop offset="100%" style="stop-color:{line_color};stop-opacity:0.05" />
                </linearGradient>
            </defs>
            <path d="{path_d}" stroke="{line_color}" stroke-width="2" fill="none" stroke-linecap="round" stroke-linejoin="round"/>
            <path d="{path_d} L {margin + chart_width},{margin + chart_height} L {margin},{ margin + chart_height}" fill="url(#chart-grad-{symbol})"/>
            <text x="{width - margin}" y="{height - 2}" font-size="10" text-anchor="end" fill="{line_color}" font-weight="bold">{price:.0f}</text>
        </svg>'''
        
        return svg
    
    except Exception as e:
        return ""  # Silently fail if chart generation has issues


def compute_context_score(row):
    """
    Context score on a 0–5 scale (fuzzy, early-signal aware, with divergence factors)

    0.0–1.0 : hostile
    1.0–2.0 : weak
    2.0–3.0 : neutral
    3.0–4.0 : early supportive
    4.0–5.0 : strong institutional
    
    Returns: (score, momentum)
    - score: 0-5 context score
    - momentum: -1 to +1 (accelerating negative to accelerating positive)
    """

    # --------------------------------------------------
    # Base (neutral = 2.5)
    # --------------------------------------------------
    score = 2.5
    momentum = 0.0

    # --- Inputs ---
    vwap_score   = row.get('vwap_score', 0.0) or 0.0
    volume_score = row.get('volume_score', 0.0) or 0.0
    regime       = row.get('market_regime', 'neutral')
    risk_level   = row.get('risk_level', 'LOW')
    
    # --- NEW: Divergence signals ---
    pv_div_score = row.get('pv_divergence_score', 0.0) or 0.0
    pr_div_score = row.get('pr_divergence_score', 0.0) or 0.0
    pv_confidence = row.get('pv_confidence', 0.0) or 0.0

    # --------------------------------------------------
    # 1️⃣ VWAP pressure (most important early signal)
    # Range contribution: approx ±1.0
    # --------------------------------------------------
    vwap_contrib = 1.0 * tanh(vwap_score * 1.8)
    score += vwap_contrib
    
    # VWAP momentum: derivative of tanh (how fast it's changing)
    vwap_momentum = 1.0 * (1 - tanh(vwap_score * 1.8)**2) * 1.8 * vwap_score
    momentum += 0.6 * vwap_momentum  # Weight VWAP momentum heavily

    # --------------------------------------------------
    # 2️⃣ Volume participation (accumulation / distribution)
    # Range contribution: approx ±0.7
    # --------------------------------------------------
    volume_contrib = 0.7 * tanh(volume_score * 1.5)
    score += volume_contrib
    
    # Volume momentum
    volume_momentum = 0.7 * (1 - tanh(volume_score * 1.5)**2) * 1.5 * volume_score
    momentum += 0.4 * volume_momentum

    # --------------------------------------------------
    # 3️⃣ Divergence detection (NEW: climax & reversal warnings)
    # CAPPED: Divergence can ONLY reduce or cap context, NEVER increase it
    # Range contribution: ±0.6 (but only negative or neutral, not positive)
    # --------------------------------------------------
    # Price/Volume divergence: climax conditions are BEARISH signals (lower context)
    if pv_div_score < -0.5:  # Climax: price up but volume down (exhaustion)
        divergence_contrib = -0.6 * pv_confidence  # Strong signal reduces context
        score += divergence_contrib
        momentum -= 0.3 * pv_confidence  # Accelerate downward momentum
    # REMOVED: elif branch that allowed positive divergence contribution
    # Divergence alignment is NOT allowed to boost context_score
    # If healthy alignment exists, it drives volume_score/vwap_score instead
    
    # Price/RSI divergence: bearish divergence means weakness (lower context)
    if pr_div_score < -0.5:  # Bearish divergence = reversal risk
        score -= 0.3  # Reduce institutional confidence
        momentum -= 0.15
    # REMOVED: elif branch for bullish divergence bonus
    # Bullish reversal bounce potential does not inflate context (stays with indicators)

    # --------------------------------------------------
    # 4️⃣ Market regime modulation
    # --------------------------------------------------
    regime_str = regime or 'neutral'
    if 'trending' in regime_str:
        score += 0.4
        momentum += 0.1  # Trending = positive momentum
    elif 'volatile' in regime_str:
        score -= 0.6
        momentum -= 0.2  # Volatile = negative momentum
    elif 'ranging' in regime_str:
        score += 0.0  # true neutral
        momentum += 0.0

    # --------------------------------------------------
    # 5️⃣ Risk compression (reduce conviction, keep bias)
    # --------------------------------------------------
    if risk_level == 'HIGH':
        score = 2.5 + (score - 2.5) * 0.55
        momentum *= 0.7  # Dampen momentum in high risk
    elif risk_level == 'MEDIUM':
        score = 2.5 + (score - 2.5) * 0.75
        momentum *= 0.85

    # --------------------------------------------------
    # 6️⃣ Safety clamp
    # --------------------------------------------------
    score = max(0.0, min(5.0, score))
    momentum = max(-1.0, min(1.0, momentum))

    return round(score, 2), round(momentum, 2)
"""
Refactored NIFTY Bearnness Screener - Clean Modular Architecture

Usage:
    python nifty_bearnness_v2.py --mode swing --universe nifty --quick
    python nifty_bearnness_v2.py --force-yf --parallel 8 --universe banknifty
    python nifty_bearnness_v2.py --universe niftylarge --mode intraday --use-6thread
"""

import argparse
import csv
import signal
import warnings
import shutil
import threading
import queue
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from datetime import datetime

# Suppress curl_cffi KeyboardInterrupt warnings (library issue, not critical)
warnings.filterwarnings('ignore', message='.*KeyboardInterrupt.*')
warnings.filterwarnings('ignore', category=DeprecationWarning)

# Import wait strategy for intelligent rate limiting
from scripts.utilities.wait_strategy import BatchRequestHandler

# Import event calendar for earnings dates
from scripts.utilities.event_calendar import get_earnings_dates, get_event_risk_score

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
from core.performance import get_tracker
from core.support_resistance import integrate_with_screener
import pandas as pd

# Optional database imports (gracefully handle if not installed)
try:
    from core.database_operations import save_daily_score
    from core.database import init_db, get_session, close_session
    HAS_DATABASE = True
except (ImportError, ModuleNotFoundError):
    HAS_DATABASE = False
    save_daily_score = None
    
try:
    from nifty_screener.enhanced_reporter import EnhancedReportGenerator
    HAS_REPORTER = True
except (ImportError, ModuleNotFoundError):
    HAS_REPORTER = False
    EnhancedReportGenerator = None

# Note: save_csv and save_html are defined below (too large to modularize yet)
# Future: Extract to exporters/ module


def load_failed_symbols_from_csv(csv_path):
    """Load symbols from CSV that had no data or errors (for retry)."""
    if not csv_path or not Path(csv_path).exists():
        return []
    
    try:
        df = pd.read_csv(csv_path)
        # Failed symbols are those with no 'price' (no data retrieved)
        failed = df[df['price'].isna() | (df['price'] == '')]['symbol'].unique().tolist()
        return failed
    except Exception as e:
        print(f"[WARN] Could not load failed symbols from {csv_path}: {e}")
        return []


def merge_csv_results(existing_csv, new_results, output_csv):
    """Merge new results with existing results, preferring successful stocks."""
    try:
        # Load existing results
        existing_df = pd.read_csv(existing_csv) if Path(existing_csv).exists() else pd.DataFrame()
        
        # Load new results
        new_df = pd.read_csv(new_results)
        
        if existing_df.empty:
            merged_df = new_df.copy()
        else:
            # Merge: take new results for symbols in new_df, keep existing for others
            # Remove symbols that appear in new_df from existing_df
            merged_df = existing_df[~existing_df['symbol'].isin(new_df['symbol'])]
            
            # Add all new results
            merged_df = pd.concat([merged_df, new_df], ignore_index=True)
            
            # Sort by symbol for consistency
            merged_df = merged_df.sort_values('symbol').reset_index(drop=True)
        
        # Reindex with rank
        merged_df.insert(0, 'rank', range(1, len(merged_df) + 1))
        merged_df.to_csv(output_csv, index=False)
        
        print(f"[OK] Merged {len(new_df)} new results with existing. Total: {len(merged_df)}")
        return merged_df
    except Exception as e:
        print(f"[WARN] Merge failed: {e}")
        return None


def calculate_option_premium_quality(row):
    """
    Calculate comprehensive Option Premium Quality Score (0-1).
    
    Combines: Stock quality + Theta quality + Event risk + Execution quality + Greeks safety
    
    Components (weighted):
    1. Stock Fundamentals (20%) - option_selling_score
       - IV/HV spread, liquidity, neutral position
    
    2. Theta Opportunity (45%) - theta_decay_score  
       - Theta magnitude, IV level, OI, theta efficiency, event risk
    
    3. Greeks Quality (35%) - spreads, delta, gamma
       - Bid-ask spread (40%)
       - Delta appropriateness for ATM (35%)
       - Gamma safety (25%)
    
    Range: 0.0 (worst) to 1.0 (best premium selling opportunity)
    """
    try:
        # ==================== COMPONENT 1: STOCK QUALITY ====================
        stock_quality = float(row.get('option_selling_score') or 0.5)
        
        # ==================== COMPONENT 2: THETA OPPORTUNITY ====================
        theta_quality = float(row.get('theta_decay_score') or 0.5)
        
        # ==================== COMPONENT 3: GREEKS QUALITY ====================
        # Sub-component A: Spread Penalty (40% weight)
        spread_pct = float(row.get('option_spread_pct') or 2.0)
        
        if spread_pct < 1.0:
            spread_score = 1.0
        elif spread_pct < 2.0:
            spread_score = 0.8
        elif spread_pct < 5.0:
            spread_score = 0.5
        else:
            spread_score = 0.1  # Avoid if spread too wide
        
        # Sub-component B: Delta Appropriateness (35% weight)
        # ATM calls should be ~0.4-0.5 delta for best theta decay + safety
        delta = float(row.get('option_delta') or 0.5)
        
        if 0.35 <= delta <= 0.55:
            delta_score = 1.0  # Perfect ATM
        elif (0.25 <= delta < 0.35) or (0.55 < delta <= 0.65):
            delta_score = 0.85
        elif (0.15 <= delta < 0.25) or (0.65 < delta <= 0.75):
            delta_score = 0.6
        elif (0.05 <= delta < 0.15) or (0.75 < delta <= 0.95):
            delta_score = 0.3
        else:
            delta_score = 0.1  # Very far from ATM
        
        # Sub-component C: Gamma Safety (25% weight)
        # Lower gamma = less delta swing = more predictable losses/gains
        gamma = float(row.get('option_gamma') or 0.02)
        
        if gamma < 0.01:
            gamma_score = 1.0  # Very stable
        elif gamma < 0.02:
            gamma_score = 0.85
        elif gamma < 0.03:
            gamma_score = 0.6
        elif gamma < 0.05:
            gamma_score = 0.3
        else:
            gamma_score = 0.1  # Very unstable, avoid
        
        # Combine Greeks into single quality score
        greeks_quality = (
            spread_score * 0.40 +
            delta_score * 0.35 +
            gamma_score * 0.25
        )
        
        # ==================== FINAL COMBINATION ====================
        # Weights: Stock(20%) + Theta(45%) + Greeks(35%)
        option_premium_quality = (
            stock_quality * 0.20 +
            theta_quality * 0.45 +
            greeks_quality * 0.35
        )
        
        # Ensure within bounds
        return max(0.0, min(1.0, option_premium_quality))
        
    except (ValueError, TypeError, ZeroDivisionError):
        return 0.0  # Return lowest score if data invalid


def calculate_option_selling_score_0_1(row):
    """
    Calculate option selling viability score on 0-1 scale.
    Independent from existing scoring logic.
    
    Higher score = Better for selling options (low volatility, good liquidity, neutral direction)
    
    Components:
    - IV (35%): Lower IV = better (premium decay advantage)
    - HV (35%): Lower volatility = better (stock stability)
    - Liquidity (20%): Tighter spread = better (easy exits)
    - Neutrality (10%): Neutral direction = better (less gap risk)
    
    Returns: Float 0-1 with variance across full range
    """
    try:
        # Get metrics with safe defaults
        option_iv = float(row.get('option_iv') or 0.30)
        volatility_pct = float(row.get('volatility_pct') or 2.0)
        option_spread_pct = float(row.get('option_spread_pct') or 5.0)
        final_score = float(row.get('final_score') or 0)
        abs_score = abs(final_score)
        
        # Convert IV to percentage scale (0-1 becomes 0-100)
        iv_pct = option_iv * 100
        
        # ========== COMPONENT SCORES (0-1 scale) ==========
        
        # IV Score: Lower IV = higher score
        # Range: 0% (100 points) to 50%+ (10 points)
        if iv_pct < 20:
            iv_component = 1.0
        elif iv_pct < 30:
            iv_component = 0.85
        elif iv_pct < 40:
            iv_component = 0.60
        elif iv_pct < 50:
            iv_component = 0.35
        else:
            iv_component = 0.10
        
        # HV Score: Lower volatility = higher score
        # Range: <1.0% (100) to >3.0% (20)
        if volatility_pct < 1.0:
            hv_component = 1.0
        elif volatility_pct < 1.5:
            hv_component = 0.90
        elif volatility_pct < 2.0:
            hv_component = 0.75
        elif volatility_pct < 3.0:
            hv_component = 0.50
        else:
            hv_component = 0.20
        
        # Liquidity Score: Tighter spread = higher score
        # Range: <1.0% (95) to >5.0% (10)
        if option_spread_pct < 1.0:
            liquidity_component = 0.95
        elif option_spread_pct < 2.0:
            liquidity_component = 0.85
        elif option_spread_pct < 3.0:
            liquidity_component = 0.75
        elif option_spread_pct < 5.0:
            liquidity_component = 0.50
        else:
            liquidity_component = 0.10
        
        # Neutrality Score: Lower |score| = higher score
        # Range: <0.10 (95) to >0.50 (10)
        if abs_score < 0.10:
            neutral_component = 0.95
        elif abs_score < 0.20:
            neutral_component = 0.85
        elif abs_score < 0.30:
            neutral_component = 0.60
        elif abs_score < 0.50:
            neutral_component = 0.30
        else:
            neutral_component = 0.10
        
        # ========== WEIGHTED AVERAGE (0-1) ==========
        selling_score = (
            iv_component * 0.35 +
            hv_component * 0.35 +
            liquidity_component * 0.20 +
            neutral_component * 0.10
        )
        
        # Ensure within bounds
        return max(0.0, min(1.0, selling_score))
        
    except (ValueError, TypeError):
        return 0.0  # Return lowest score if data invalid


def calculate_theta_decay_score(row):
    """
    Calculate theta decay score (0-1) for premium selling opportunities.
    
    Uses REAL OPTION CHAIN DATA + EVENT DATES from the selected strike.
    Based on 5 continuous sub-scores (each 0-1):
    
    1. Theta Magnitude (0-1): Absolute theta value normalized
       - Measures: How much daily decay in the option premium
       - Higher theta = better for sellers
    
    2. Implied Volatility (0-1): IV level relative to volatility context
       - Measures: Option IV as % (0.15 = 15%)
       - Higher IV = higher premium = better for sellers
    
    3. Open Interest / Liquidity (0-1): OI level for trading viability
       - Measures: Option chain liquidity
       - Higher OI = easier to trade
    
    4. Theta Efficiency (0-1): Theta relative to strike price
       - Measures: Daily decay as % of strike
       - Higher efficiency = more attractive for selling
    
    5. Event Risk (0-1): Days until next earnings/result date
       - Measures: Time until major corporate event
       - Higher = safer (further from event)
       - Low score if within 7 days of earnings
    
    Hard Veto: If |final_score| > 0.50 (trending) → return 0.0
    
    Weights: Theta(30%) + IV(20%) + Liquidity(15%) + Efficiency(10%) + EventRisk(25%)
    Range: 0.0 (worst) to 1.0 (best for theta selling)
    """
    try:
        # ==================== HARD VETO: TRENDING REGIME ====================
        final_score = float(row.get('final_score') or 0)
        if abs(final_score) > 0.50:
            return 0.0  # Strong trend = bad for selling premium
        
        # ==================== SUB-SCORE 1: THETA MAGNITUDE ====================
        # Higher absolute theta = better for premium sellers
        option_theta = float(row.get('option_theta') or 0)
        abs_theta = abs(option_theta)
        
        # Scoring: |theta| >= 1.0 = 1.0, 0.5-1.0 = 0.8, 0.2-0.5 = 0.6, <0.2 = 0.2
        if abs_theta >= 1.0:
            theta_mag_score = 1.0
        elif abs_theta >= 0.5:
            theta_mag_score = 0.8
        elif abs_theta >= 0.2:
            theta_mag_score = 0.6
        elif abs_theta > 0:
            theta_mag_score = 0.3
        else:
            theta_mag_score = 0.0  # No theta
        
        # ==================== SUB-SCORE 2: IMPLIED VOLATILITY ====================
        # Higher IV = higher premium = better for premium sellers
        option_iv = float(row.get('option_iv') or 0.20)  # On 0-1 scale
        iv_pct = option_iv * 100  # Convert to percentage
        
        # Scoring: IV% >= 40% = 1.0, 30-40% = 0.8, 20-30% = 0.6, 10-20% = 0.3, <10% = 0.1
        if iv_pct >= 40:
            iv_score = 1.0
        elif iv_pct >= 30:
            iv_score = 0.8
        elif iv_pct >= 20:
            iv_score = 0.6
        elif iv_pct >= 10:
            iv_score = 0.3
        else:
            iv_score = 0.1
        
        # ==================== SUB-SCORE 3: OPEN INTEREST / LIQUIDITY ====================
        # Higher OI = more liquid = easier to sell
        option_oi = float(row.get('option_oi') or 0)
        
        # Scoring: OI >= 2000 = 1.0, 1000-2000 = 0.85, 500-1000 = 0.7, 100-500 = 0.4, <100 = 0.1
        if option_oi >= 2000:
            liquidity_score = 1.0
        elif option_oi >= 1000:
            liquidity_score = 0.85
        elif option_oi >= 500:
            liquidity_score = 0.7
        elif option_oi >= 100:
            liquidity_score = 0.4
        elif option_oi > 0:
            liquidity_score = 0.15
        else:
            liquidity_score = 0.0  # No OI
        
        # ==================== SUB-SCORE 4: THETA EFFICIENCY ====================
        # Theta as % of strike price - how much decay relative to contract value
        option_strike = float(row.get('option_strike') or 100)
        
        # Theta efficiency = |theta| / strike
        theta_efficiency_raw = abs_theta / max(1, option_strike)
        
        # Convert to percentage (for easier interpretation)
        theta_efficiency_pct = theta_efficiency_raw * 100
        
        # Scoring: efficiency% >= 1.0% = 1.0, 0.5-1.0% = 0.8, 0.2-0.5% = 0.6, 0.1-0.2% = 0.3, <0.1% = 0.1
        if theta_efficiency_pct >= 1.0:
            efficiency_score = 1.0
        elif theta_efficiency_pct >= 0.5:
            efficiency_score = 0.8
        elif theta_efficiency_pct >= 0.2:
            efficiency_score = 0.6
        elif theta_efficiency_pct >= 0.1:
            efficiency_score = 0.3
        else:
            efficiency_score = 0.1
        
        # ==================== SUB-SCORE 5: EVENT RISK (EARNINGS DATES) ====================
        # Get earnings date and calculate days until event
        symbol = row.get('symbol', '')
        event_data = get_earnings_dates(symbol, use_cache=True)
        days_until_event = event_data.get('days_until')
        
        # Convert days to risk score (higher = safer for theta)
        event_risk_score = get_event_risk_score(days_until_event)
        
        # Store event info in row for reference
        row['event_days_until'] = days_until_event
        row['event_date'] = event_data.get('next_earnings')
        row['event_source'] = event_data.get('source')
        
        # ==================== COMBINE WITH WEIGHTS ====================
        # Weights: Theta(30%) + IV(20%) + Liquidity(15%) + Efficiency(10%) + EventRisk(25%)
        # EventRisk gets high weight because it's a critical veto factor
        theta_decay_score = (
            theta_mag_score * 0.30 +
            iv_score * 0.20 +
            liquidity_score * 0.15 +
            efficiency_score * 0.10 +
            event_risk_score * 0.25
        )
        
        # Ensure within bounds
        return max(0.0, min(1.0, theta_decay_score))
        
    except (ValueError, TypeError, ZeroDivisionError):
        return 0.0  # Return lowest score if data invalid


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

def print_actionables(results, index_bias=0.0, conf_threshold=40.0, score_threshold=0.35, mode='swing'):
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
        daily_atr = r.get('daily_atr') or 0.0
        
        # Calculate SL and Target percentages for DAY FRAME TRADING
        # Use daily ATR (14-period daily volatility) instead of 5-minute ATR
        atr_for_sl = daily_atr if daily_atr > 0 else atr
        
        if mode in ('swing', 'longterm'):
            # DAY/SWING TRADING: 1.5x ATR SL with 2:1 RR (realistic for day frame)
            sl_multiplier = 1.5  # Less aggressive than 2.5x (was for 5-min scalping)
            rr_ratio = 2.0  # 2:1 reward-to-risk (achievable for day trading)
        else:
            # INTRADAY SCALPING: Keep tighter stops (5-min volatility basis)
            sl_multiplier = 2.0
            rr_ratio = 2.5
        
        sl_pct = (sl_multiplier * atr_for_sl / price * 100) if price > 0 and atr_for_sl > 0 else 0.0
        target_pct = sl_pct * rr_ratio
        
        direction_icon = '▼' if score < 0 else '▲'
        
        print(f"{rank:<6}{r['symbol']:<12}{score:+.3f}    {conf:>6.0f}   {price:>8.2f}  {atr:>6.2f}  {sl_pct:>6.1f}%  {target_pct:>8.1f}%  {r.get('sector','Unknown'):<14}")


# Note: get_sector() removed - now imported from core.sector_mapper
# Note: save_csv() defined below  
# Note: save_html() defined below

# Auto-load to database
def _load_results_to_database(csv_path):
    """Load screener results from CSV into database."""
    if not HAS_DATABASE:
        print("[WARN] Database module not available - skipping database load")
        return
        
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
                if save_daily_score:
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
            "rank", "symbol", "sector", "index", "market_regime", "score",
            "swing_score", "longterm_score",
            "confidence", "confidence_floor_reason", "system_state", "context_score", "context_momentum", "price", "pct_below_high", "pct_above_low", "mode", "strategy", "strategy_reason",
            "or_score", "vwap_score", "structure_score", "rsi", "rsi_score", "ema_score",
            "volume_score", "macd_score", "bb_score", "atr",
            "sl_price", "target_price", "sl_pct", "target_pct", "rr_ratio", "method",
            "risk_level", "should_trade", "filter_reason", "position_size_multiplier", "support_level", "resistance_level",
            "intraday_weight", "swing_weight", "longterm_weight",
            "option_score", "option_iv", "option_spread_pct", "option_type", "option_strike", "option_expiry",
            "option_volume", "option_oi", "option_delta", "option_gamma", "option_theta", "option_vega",
            "option_premium_quality",
            "event_date", "days_until_event", "event_source"
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
                f"{r.get('final_score', r.get('score', 0)):.4f}" if r.get('final_score') or r.get('score') is not None else '',
                f"{r.get('swing_score', 0):.4f}" if r.get('swing_score') is not None else '',
                f"{r.get('longterm_score', 0):.4f}" if r.get('longterm_score') is not None else '',
                f"{r['confidence']:.1f}" if r.get('confidence') is not None else '',
                r.get('confidence_floor_reason', ''),  # Why was confidence floored?
                r.get('system_state', 'OBSERVE'),  # Derived execution state
                f"{r.get('context_score', 0):.2f}" if r.get('context_score') is not None else '',
                f"{r.get('context_momentum', 0):+.2f}" if r.get('context_momentum') is not None else '',
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
                f"{r.get('sl_price', 0):.2f}" if r.get('sl_price') else '',
                f"{r.get('target_price', 0):.2f}" if r.get('target_price') else '',
                f"{r.get('sl_pct', 0):.2f}" if r.get('sl_pct') else '',
                f"{r.get('target_pct', 0):.2f}" if r.get('target_pct') else '',
                f"{r.get('rr_ratio', 0):.2f}" if r.get('rr_ratio') else '',
                r.get('method', ''),
                r.get('risk_level', 'LOW'),
                str(r.get('should_trade', 'False')),  # Execution block flag
                r.get('filter_reason', ''),  # Why was execution blocked/allowed?
                f"{r.get('position_size_multiplier', 1.0):.2f}" if r.get('position_size_multiplier') else '',
                f"{r.get('support_level', 0):.2f}" if r.get('support_level') else '',
                f"{r.get('resistance_level', 0):.2f}" if r.get('resistance_level') else '',
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
                f"{r['option_premium_quality']:.4f}" if r.get('option_premium_quality') is not None else '',
                str(r['event_date'].date()) if r.get('event_date') else '',
                str(r.get('event_days_until', '')),
                r.get('event_source', ''),
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
            <meta charset=\"UTF-8\">
            <meta http-equiv=\"refresh\" content=\"900\">  <!-- Auto-refresh every 15 min -->
            <title>Nifty Stock Analyser - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</title>
            <link href=\"https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&family=JetBrains+Mono:wght@400;600&display=swap\" rel=\"stylesheet\">
            <style>
                ...existing code...

        # Remove broken multi-line HTML string and use only incremental concatenation for table rows
        .risk-matrix {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(120px, 1fr)); gap: 12px; margin: 16px 0; }}
        .risk-card {{ background: white; border: 2px solid #e2e8f0; border-radius: 10px; padding: 16px; text-align: center; transition: all 0.2s; box-shadow: 0 2px 6px rgba(0,0,0,0.05); }}
        .risk-card:hover {{ border-color: #667eea; box-shadow: 0 6px 16px rgba(102, 126, 234, 0.15); transform: translateY(-3px); }}
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
        
        .sector-heatmap {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(120px, 1fr));
            gap: 12px;
            margin: 16px 0;
        }}
        
        .sector-card {{
            padding: 16px;
            border-radius: 10px;
            text-align: center;
            transition: all 0.2s ease;
            cursor: default;
            box-shadow: 0 2px 8px rgba(0,0,0,0.06);
        }}
        
        .sector-card:hover {{
            transform: translateY(-4px);
            box-shadow: 0 6px 16px rgba(0,0,0,0.15);
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
        #screener-wrapper {{ overflow-x: auto; background: white; border-radius: 10px; box-shadow: 0 2px 8px rgba(0,0,0,0.06); margin-bottom: 24px; }}
        table {{ border-collapse: collapse; width: 100%; font-size: 11px; background-color: white; box-shadow: none; }}
        th, td {{ border: 1px solid #e8eef7; padding: 8px 6px; text-align: left; }}
        th {{ background: #f5f8fc; cursor: pointer; position: relative; font-weight: 600; color: #2d3748; font-family: 'Inter', sans-serif; white-space: nowrap; }}
        th.sort-asc::after {{ content: " ▲"; font-size: 9px; color: #667eea; }}
        th.sort-desc::after {{ content: " ▼"; font-size: 9px; color: #667eea; }}
        tr:hover {{ background-color: #f9fbfd; }}
        td {{ font-family: 'Inter', sans-serif; color: #4a5568; }}
        td.mono {{ font-family: 'JetBrains Mono', monospace; font-size: 10px; }}
        
        .badge {{ display: inline-block; padding: 3px 6px; border-radius: 3px; font-size: 10px; font-weight: 600; text-transform: uppercase; letter-spacing: 0.3px; white-space: nowrap; }}
        .tag-bear {{ background: #fed7d7; color: #742a2a; }}
        .tag-bull {{ background: #c6f6d5; color: #22543d; }}
        .tag-neutral {{ background: #e2e8f0; color: #2d3748; }}
        
        .controls {{ margin-bottom: 12px; padding: 12px; background: white; border-radius: 8px; box-shadow: 0 2px 6px rgba(0,0,0,0.05); }}
        .search {{ padding: 8px 10px; border: 1px solid #e2e8f0; border-radius: 6px; width: 250px; font-family: 'Inter', sans-serif; font-size: 12px; transition: border-color 0.3s; }}
        .search:focus {{ outline: none; border-color: #667eea; background: #f9fbfd; }}
        .control-group {{ margin: 6px 0; display: inline-block; margin-right: 12px; }}
        input[type="range"] {{ vertical-align: middle; margin: 0 6px; height: 4px; }}
        label {{ margin-right: 6px; font-size: 12px; font-weight: 500; color: #2d3748; }}
        select {{ padding: 6px 8px; border: 1px solid #e2e8f0; border-radius: 6px; font-family: 'Inter', sans-serif; font-size: 12px; cursor: pointer; transition: border-color 0.3s; }}
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
        
        /* Support/Resistance Styles */
        .method-sr {{ background-color: #4299e1; color: white; font-weight: 600; padding: 4px 8px; border-radius: 4px; font-size: 11px; }}
        .method-atr {{ background-color: #a0aec0; color: white; font-weight: 600; padding: 4px 8px; border-radius: 4px; font-size: 11px; }}
        .level-support {{ color: #22863a; font-weight: 600; background-color: #f0fff4; padding: 4px 6px; border-radius: 3px; }}
        .level-resistance {{ color: #cb2431; font-weight: 600; background-color: #fff0f0; padding: 4px 6px; border-radius: 3px; }}
        
        /* Risk Zone Styles */
        .risk-normal {{ background-color: #c6f6d5; color: #22543d; font-weight: 600; padding: 4px 8px; border-radius: 4px; font-size: 11px; }}
        .risk-medium {{ background-color: #feebc8; color: #7c2d12; font-weight: 600; padding: 4px 8px; border-radius: 4px; font-size: 11px; }}
        .risk-high {{ background-color: #fed7d7; color: #742a2a; font-weight: 600; padding: 4px 8px; border-radius: 4px; font-size: 11px; }}
        .zone-label {{ font-size: 10px; opacity: 0.8; }}
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
        
        .tooltip {{ position: relative; cursor: help; z-index: 10; display: inline-block; }}
        .tooltip .tooltiptext {{ visibility: hidden; background-color: #2d3748; color: #fff; text-align: left; padding: 12px 14px; border-radius: 6px; position: absolute; z-index: 1001; top: 100%; left: 0; margin-top: 8px; white-space: pre-wrap; opacity: 0; transition: opacity 0.3s; font-size: 12px; line-height: 1.5; font-family: 'Courier New', monospace; max-width: 450px; pointer-events: auto; box-shadow: 0 8px 24px rgba(0, 0, 0, 0.4); border: 1px solid #4a5568; word-wrap: break-word; overflow-wrap: break-word; }}
        .tooltip .tooltiptext::after {{ content: ""; position: absolute; bottom: 100%; left: 12px; border-width: 5px; border-style: solid; border-color: transparent transparent #2d3748 transparent; }}
        .tooltip:hover .tooltiptext {{ visibility: visible; opacity: 1; pointer-events: auto; }}
        
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

    
    <!-- SCREENER TABLE SECTION (FIRST) -->
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
            <label><input type="checkbox" id="enableMinConf" onchange="filterTable()" /> Min Conf%</label>
            <input type="range" id="minConf" min="0" max="100" step="1" value="0" oninput="document.getElementById('minConfVal').innerText=this.value;filterTable()" />
            <span id="minConfVal">0</span>
        </div>
        <div class="control-group">
            <label><input type="checkbox" id="enableMinScore" checked onchange="filterTable()" /> Min |Score|</label>
            <input type="range" id="minScore" min="0" max="1" step="0.01" value="0.35" oninput="document.getElementById('minScoreVal').innerText=this.value;filterTable()" />
            <span id="minScoreVal">0.35</span>
        </div>
        <div class="control-group">
            <label><input type="checkbox" id="enableMinRS" onchange="filterTable()" /> Min Rel Strength</label>
            <input type="range" id="minRS" min="-1" max="1" step="0.05" value="-0.3" oninput="document.getElementById('minRSVal').innerText=this.value;filterTable()" />
            <span id="minRSVal">-0.3</span>
        </div>
    </div>
    
    <div id="screener-wrapper">
    <table id="screener">
        <thead>
            <tr>
                <th data-type="num" onclick="sortTable(this, 'num')" title="Position rank by bearness score"><span class="tooltip">Rank<span class="tooltiptext">Position rank ordered by bearness score (most bearish first)</span></span></th>
                <th data-type="str" onclick="sortTable(this, 'str')" title="Stock symbol"><span class="tooltip">Symbol<span class="tooltiptext">NSE stock symbol/ticker</span></span></th>
                <th data-type="str" onclick="sortTable(this, 'str')" title="Trend direction"><span class="tooltip">Trend<span class="tooltiptext">Overall trend: uptrend, downtrend, or sideways</span></span></th>
                <th data-type="num" onclick="sortTable(this, 'num')" title="Bearness score -1 to +1"><span class="tooltip">Score<span class="tooltiptext">Bearness score: -1 (bullish) to +1 (bearish), 0 (neutral)</span></span></th>
                <th data-type="num" onclick="sortTable(this, 'num')" title="Swing score (1-2 days)"><span class="tooltip">Swing Score<span class="tooltiptext">Swing mode score (35:35:30 weights) for 1-2 day holds</span></span></th>
                <th data-type="num" onclick="sortTable(this, 'num')" title="Longterm score (3-7 days)"><span class="tooltip">LT Score<span class="tooltiptext">Longterm mode score (15:25:60 weights) for multi-day holds</span></span></th>
                <th data-type="num" onclick="sortTable(this, 'num')" title="Signal confidence 0-100%"><span class="tooltip">Conf%<span class="tooltiptext">Confidence in signal (0-100%): higher = more reliable</span></span></th>
                <th data-type="str" onclick="sortTable(this, 'str')" title="Execution state"><span class="tooltip">State<span class="tooltiptext">System state: STAND_DOWN (avoid), OBSERVE (watch), ENGAGE (trade), EXPAND (aggressive)</span></span></th>
                <th data-type="num" onclick="sortTable(this, 'num')" title="Institutional Context Score"><span class="tooltip">Context<span class="tooltiptext">Context score (0-5): 0-1 hostile, 1-2 weak, 2-3 neutral, 3-4 early supportive, 4-5 strong institutional</span></span></th>
                <th data-type="num" onclick="sortTable(this, 'num')" title="Context momentum -1 to +1"><span class="tooltip">Context Momentum<span class="tooltiptext">Context momentum (-1 to +1): rate of change in institutional context</span></span></th>
                <th data-type="num" onclick="sortTable(this, 'num')" title="Robustness score 0-100"><span class="tooltip">Robustness%<span class="tooltiptext">Robustness score (0-100): percentage of 7 safety filters passing</span></span></th>
                <th data-type="num" onclick="sortTable(this, 'num')" title="Robustness momentum -1 to +1"><span class="tooltip">Robust Momentum<span class="tooltiptext">Robustness momentum (-1 to +1): rate of change in filter quality</span></span></th>
                <th data-type="num" onclick="sortTable(this, 'num')" title="Master score 0-100"><span class="tooltip">Master Score<span class="tooltiptext">Master score (0-100): 6-dimension weighted composite (25% conf, 25% tech, 20% robust, 15% context, 10% momentum, 5% news)</span></span></th>
                <th data-type="str" onclick="sortTable(this, 'str')" title="Risk zone status"><span class="tooltip">Risk Zone<span class="tooltiptext">NORMAL: Safe entry | MEDIUM: Caution zone | HIGH: Extreme overbought/oversold</span></span></th>
                <th data-type="num" onclick="sortTable(this, 'num')" title="News sentiment score -1 to +1"><span class="tooltip">News Sentiment<span class="tooltiptext">News sentiment score (-1: very negative, 0: neutral, +1: very positive)</span></span></th>
                <th data-type="num" onclick="sortTable(this, 'num')" title="Relative strength -1 to +1"><span class="tooltip">Rel Strength<span class="tooltiptext">Relative strength vs market (60% sector peers + 40% Nifty50): -1 lagging, 0 neutral, +1 outperforming</span></span></th>
                <th data-type="num" onclick="sortTable(this, 'num')" title="Option premium quality 0-1"><span class="tooltip">Opt Quality<span class="tooltiptext">Combined option quality score (0-1): Stock (20%) + Theta (45%) + Greeks (35%)</span></span></th>
                <th data-type="num" onclick="sortTable(this, 'num')" title="Current price"><span class="tooltip">Price<span class="tooltiptext">Current closing price in rupees</span></span></th>
                <th data-type="num" onclick="sortTable(this, 'num')" title="Suggested stop loss"><span class="tooltip">Stop Loss<span class="tooltiptext">Suggested stop loss price (2.5× ATR from entry)</span></span></th>
                <th data-type="num" onclick="sortTable(this, 'num')" title="Suggested target"><span class="tooltip">Target<span class="tooltiptext">Suggested profit target (4.5× ATR from entry)</span></span></th>
                <th data-type="num" onclick="sortTable(this, 'num')" title="52-week high"><span class="tooltip">52W High<span class="tooltiptext">52-week high price</span></span></th>
                <th data-type="num" onclick="sortTable(this, 'num')" title="52-week low"><span class="tooltip">52W Low<span class="tooltiptext">52-week low price</span></span></th>
                <th data-type="num" onclick="sortTable(this, 'num')" title="Daily % change"><span class="tooltip">Daily%<span class="tooltiptext">Percentage change from yesterday's close</span></span></th>
                <th data-type="num" onclick="sortTable(this, 'num')" title="Weekly % change"><span class="tooltip">Weekly%<span class="tooltiptext">Percentage change from last week's close</span></span></th>
                <th data-type="num" onclick="sortTable(this, 'num')" title="% below 52-week high"><span class="tooltip">52W High %<span class="tooltiptext">Percentage below 52-week high (pullback magnitude)</span></span></th>
                <th data-type="num" onclick="sortTable(this, 'num')" title="% above 52-week low"><span class="tooltip">52W Low %<span class="tooltiptext">Percentage above 52-week low (recovery distance)</span></span></th>
                <th data-type="str" onclick="sortTable(this, 'str')" title="Industry sector"><span class="tooltip">Sector<span class="tooltiptext">Industry classification (Banking, IT, Auto, etc.)</span></span></th>
                <th data-type="str" onclick="sortTable(this, 'str')" title="Price pattern"><span class="tooltip">Pattern<span class="tooltiptext">Technical pattern: golden cross, death cross, consolidation, etc.</span></span></th>
                <th data-type="str" onclick="sortTable(this, 'str')" title="Timeframe alignment"><span class="tooltip">TF Align<span class="tooltiptext">Alignment across timeframes (intraday/swing/longterm)</span></span></th>
                <th data-type="str" onclick="sortTable(this, 'str')" title="Trading strategy"><span class="tooltip">Strategy<span class="tooltiptext">Recommended strategy (swing, breakout, mean reversion)</span></span></th>
                <th data-type="num" onclick="sortTable(this, 'num')" title="Opening range score -1 to +1"><span class="tooltip">OR<span class="tooltiptext">Opening range score: price vs first 30min high/low (-1 to +1)</span></span></th>
                <th data-type="num" onclick="sortTable(this, 'num')" title="VWAP score -1 to +1"><span class="tooltip">VWAP<span class="tooltiptext">Volume-weighted average price score (-1: below, +1: above)</span></span></th>
                <th data-type="num" onclick="sortTable(this, 'num')" title="Price structure score -1 to +1"><span class="tooltip">Structure<span class="tooltiptext">Price structure quality (-1: weak, +1: strong reversal pattern)</span></span></th>
                <th data-type="num" onclick="sortTable(this, 'num')" title="RSI momentum score"><span class="tooltip">RSI<span class="tooltiptext">Relative Strength Index score (-1 oversold to +1 overbought)</span></span></th>
                <th data-type="num" onclick="sortTable(this, 'num')" title="EMA trend score -1 to +1"><span class="tooltip">EMA<span class="tooltiptext">Exponential moving average trend score (-1: bearish, +1: bullish)</span></span></th>
                <th data-type="num" onclick="sortTable(this, 'num')" title="Volume score -1 to +1"><span class="tooltip">Vol<span class="tooltiptext">Volume analysis score (-1: low/decreasing, +1: high/increasing)</span></span></th>
                <th data-type="num" onclick="sortTable(this, 'num')" title="MACD momentum -1 to +1"><span class="tooltip">MACD<span class="tooltiptext">MACD momentum score (-1: bearish divergence, +1: bullish)</span></span></th>
                <th data-type="num" onclick="sortTable(this, 'num')" title="Bollinger Band score -1 to +1"><span class="tooltip">BB<span class="tooltiptext">Bollinger Band score (-1: at lower band, +1: at upper band)</span></span></th>
                <th data-type="num" onclick="sortTable(this, 'num')" title="Average true range"><span class="tooltip">ATR<span class="tooltiptext">Average True Range: volatility measure (stop/target distance)</span></span></th>
                <th data-type="num" onclick="sortTable(this, 'num')" title="Option implied volatility"><span class="tooltip">Opt IV<span class="tooltiptext">Implied volatility (0-1 scale, lower = more stable)</span></span></th>
                <th data-type="num" onclick="sortTable(this, 'num')" title="Option bid-ask spread %"><span class="tooltip">Opt Spread%<span class="tooltiptext">Bid-ask spread % (lower = more liquid)</span></span></th>
                <th data-type="num" onclick="sortTable(this, 'num')" title="Option delta"><span class="tooltip">Opt Delta<span class="tooltiptext">Delta: directional sensitivity (0.5 = ATM, >0.5 = ITM)</span></span></th>
                <th data-type="num" onclick="sortTable(this, 'num')" title="Option gamma"><span class="tooltip">Opt Gamma<span class="tooltiptext">Gamma: rate of delta change (higher = more sensitive)</span></span></th>
                <th data-type="num" onclick="sortTable(this, 'num')" title="Option theta daily decay"><span class="tooltip">Opt Theta<span class="tooltiptext">Theta: daily time decay (negative = cost to buyer)</span></span></th>
                <th data-type="num" onclick="sortTable(this, 'num')" title="Option vega volatility sensitivity"><span class="tooltip">Opt Vega<span class="tooltiptext">Vega: volatility sensitivity (per 1% IV change)</span></span></th>
                <th data-type="str" onclick="sortTable(this, 'str')" title="Next earnings event"><span class="tooltip">Earnings<span class="tooltiptext">Next earnings date and days away. RED=within 3d (high noise). Risk shown: HIGH/MEDIUM/LOW for pre/post earnings impact on signal confidence</span></span></th>
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
        
        # Get sector color based on sector performance
        sector_color = get_sector_color(sector)
        sector_text_color = get_sector_text_color(sector_color)
        
        # Determine Trend Direction
        ema_score = r.get('ema_score', 0) or 0
        structure_score = r.get('structure_score', 0) or 0
        vwap_score = r.get('vwap_score', 0) or 0
        trend_strength = (ema_score + structure_score + vwap_score) / 3
        
        if score < -0.15:
            trend = "Bear Strong"
            trend_class = "trend-strong-bear"
        elif score < -0.05:
            trend = "Bear"
            trend_class = "trend-bear"
        elif score > 0.15:
            trend = "Bull Strong"
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
        
        # PHASE 3: Dynamic ATR-based stop-loss multiplier based on volatility
        # Calculate volatility percentage for dynamic stop-loss sizing
        volatility_pct = (atr_val / price * 100) if price > 0 and atr_val > 0 else 0
        
        # Dynamic stop-loss multiplier based on volatility:
        # - Low volatility (<2%): 1.0x ATR (tight stops)
        # - Normal volatility (2-4%): 1.5-2.0x ATR (standard stops) 
        # - High volatility (4-6%): 2.5-3.0x ATR (wider stops)
        # - Very high volatility (>6%): 3.5x ATR (very wide stops)
        if volatility_pct < 2.0:
            base_sl_multiplier = 1.0  # Very tight for stable stocks
        elif volatility_pct < 4.0:
            base_sl_multiplier = 1.5 + (volatility_pct - 2.0) * 0.25  # 1.5 to 2.0
        elif volatility_pct < 6.0:
            base_sl_multiplier = 2.5 + (volatility_pct - 4.0) * 0.25  # 2.5 to 3.0
        else:
            base_sl_multiplier = 3.5  # Very wide for extremely volatile stocks
        
        # Adjust multiplier based on regime (trending needs wider stops than ranging)
        if regime_display == "Trending":
            sl_multiplier = base_sl_multiplier * 1.2  # 20% wider for trends
            base_rr = 2.0  # Base R:R for trends
        elif regime_display == "Ranging":
            sl_multiplier = base_sl_multiplier * 0.8  # 20% tighter for ranges
            base_rr = 1.5  # Base R:R for ranges (harder to get big moves)
        elif regime_display == "Volatile":
            sl_multiplier = base_sl_multiplier * 1.4  # 40% wider for volatile regime
            base_rr = 1.8  # Base R:R for volatile (unpredictable)
        else:
            sl_multiplier = base_sl_multiplier  # Default
            base_rr = 2.0  # Default base
        
        # Ensure reasonable bounds (0.8x to 5.0x ATR)
        sl_multiplier = max(0.8, min(5.0, sl_multiplier))
        
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
        # PRIORITY: Use hybrid S/R values if available from integrate_with_screener()
        # FALLBACK: Use traditional ATR-based calculation
        if r.get('sl_price') is not None and r.get('target_price') is not None:
            # Hybrid S/R + ATR calculation (preferred)
            stop_loss = r.get('sl_price', 0)
            target = r.get('target_price', 0)
            rr_ratio = r.get('rr_ratio', 1.0) or 1.0
            risk_per_share = abs(price - stop_loss) if stop_loss > 0 else 0
            method_used = "S/R+ATR"
        elif atr_val > 0 and price > 0:
            # Traditional ATR-based calculation (fallback)
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
            method_used = "ATR"
        else:
            stop_loss = 0
            target = 0
            risk_per_share = 0
            rr_ratio = 0
            method_used = "None"
        
        # Position sizing: shares = (capital * risk%) / risk_per_share
        if risk_per_share > 0:
            max_shares = int((CAPITAL * RISK_PER_TRADE) / risk_per_share)
            position_value = max_shares * price
            position_size = min(max_shares, int(CAPITAL * 0.2 / price))  # Max 20% of capital per position
        else:
            position_size = 0
            position_value = 0
        
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
            
            pattern_str = f"<span class='tooltip' style='color: {pattern_color}; font-weight: bold; cursor: help; border-bottom: 2px dashed {pattern_color}; white-space: nowrap;'>{pattern_badge} {pattern}<span class='tooltiptext' style='width: 300px; left: -140px; max-width: 90vw; white-space: normal;'>{tooltip_text}</span></span><br/><small style='color: {pattern_color};'>Conf: {pattern_conf:.0%}</small>"
        else:
            pattern_str = f"<span style='color: {pattern_color};'>—</span>"
        
        # Get risk level with RSI-based fallback when detailed S/R analysis isn't available
        risk_level = r.get('risk_level')
        if not risk_level:
            # Use RSI as basic risk indicator when detailed analysis unavailable
            rsi_val = r.get('rsi', 50) or 50
            if rsi_val > 70:
                risk_level = 'HIGH'  # Overbought - high risk zone
            elif rsi_val < 30:
                risk_level = 'MEDIUM'  # Oversold - medium risk zone
            else:
                risk_level = 'LOW'  # Neutral RSI - low risk zone
        else:
            risk_level = risk_level.upper()
        risk_reason = r.get('risk_reason', None)
        risk_level_display = risk_level.upper() if risk_level else 'N/A'
        risk_class = f"risk-{risk_level.lower()}" if risk_level else 'risk-unknown'
        risk_reason_display = risk_reason if risk_reason else 'No risk reason available'
        context_score, context_momentum = compute_context_score(r)
        html_content += f"            <tr>\n"
        html_content += f"                <td>{i}</td>\n"
        
        # Generate mini chart for symbol cell
        candles_for_chart = r.get('candles_data', {}).get('swing', []) or r.get('candles_data', {}).get('intraday', [])
        mini_chart = generate_mini_chart_svg(candles_for_chart, price, r['symbol'].replace('.', '_'))
        if mini_chart:
            html_content += f"                <td><strong>{r['symbol']}</strong><br/>{mini_chart}</td>\n"
        else:
            html_content += f"                <td><strong>{r['symbol']}</strong></td>\n"
        
        # Trend comes early (after Symbol, before Scores)
        html_content += f"                <td><span class=\"badge {trend_class}\">{trend}</span></td>\n"
        html_content += f"                <td class=\"score\" style=\"{score_style}\" data-score=\"{score:+.4f}\"><span style=\"color: {trend_color}; font-weight: bold;\">{trend_badge}</span> {score:+.4f}</td>\n"
        html_content += f"                <td class=\"score\" style=\"background-color: hsl({max(-1, min(1, r.get('swing_score', 0) or 0))*60+60}, 80%, 92%);\" data-score=\"{r.get('swing_score', 0) or 0:+.4f}\">{r.get('swing_score', 0) or 0:+.4f}</td>\n"
        html_content += f"                <td class=\"score tooltip\" style=\"background-color: hsl({max(-1, min(1, r.get('longterm_score', 0) or 0))*60+60}, 80%, 92%);\" data-score=\"{r.get('longterm_score', 0) or 0:+.4f}\">{r.get('longterm_score', 0) or 0:+.4f}<span class=\"tooltiptext\">Longterm mode (15:25:60) for 3-7 day holds</span></td>\n"
        html_content += f"                <td data-conf=\"{conf_val}\">{conf_str}</td>\n"
        
        # Add system_state badge (NEW: execution clarity)
        system_state = r.get('system_state', 'OBSERVE')
        state_color_map = {
            'STAND_DOWN': '#dc3545',  # Red
            'OBSERVE': '#ffc107',      # Yellow
            'ENGAGE': '#28a745',       # Green
            'EXPAND': '#007bff'        # Blue
        }
        state_color = state_color_map.get(system_state, '#6c757d')  # Default gray
        state_tooltip_map = {
            'STAND_DOWN': 'High risk or negative context - Avoid trading',
            'OBSERVE': 'Mixed signals or neutral context - Watch for clarity',
            'ENGAGE': 'Positive context with moderate confidence - Trade',
            'EXPAND': 'Strong context and momentum with low risk - Aggressive'
        }
        state_tooltip = state_tooltip_map.get(system_state, '')
        html_content += f"                <td style=\"text-align: center;\"><span style=\"background-color: {state_color}; color: white; padding: 4px 8px; border-radius: 4px; font-weight: bold; font-size: 0.9em;\" title=\"{state_tooltip}\" class=\"tooltip-trigger\">{system_state}<span class=\"tooltiptext\">{state_tooltip}</span></span></td>\n"
        
        html_content += f"                <td>{context_score:.2f}</td>\n"
        html_content += f"                <td class=\"score\" style=\"background-color: hsl({max(-1, min(1, context_momentum))*60+60}, 80%, 92%);\" data-score=\"{context_momentum:+.2f}\">{context_momentum:+.2f}</td>\n"
        
        # Add robustness metrics
        robustness_score = r.get('robustness_score', 0) or 0
        robustness_momentum = r.get('robustness_momentum', 0) or 0
        master_score = r.get('master_score', 0) or 0
        master_score_tooltip = r.get('master_score_tooltip', 'No tooltip available')
        
        # Color code robustness score
        if robustness_score >= 80:
            robust_color = '#27ae60'  # Green - excellent
        elif robustness_score >= 60:
            robust_color = '#f39c12'  # Orange - fair
        else:
            robust_color = '#e74c3c'  # Red - poor
        
        # Color code master score
        if master_score >= 80:
            master_color = '#27ae60'  # Green - excellent
        elif master_score >= 70:
            master_color = '#f39c12'  # Orange - good
        elif master_score >= 60:
            master_color = '#e67e22'  # Dark orange - fair
        else:
            master_color = '#e74c3c'  # Red - poor
        
        html_content += f"                <td class=\"score\" style=\"color: {robust_color}; font-weight: bold;\" data-score=\"{robustness_score:.0f}\">{robustness_score:.0f}</td>\n"
        html_content += f"                <td class=\"score\" style=\"background-color: hsl({max(-1, min(1, robustness_momentum))*60+60}, 80%, 92%);\" data-score=\"{robustness_momentum:+.2f}\">{robustness_momentum:+.2f}</td>\n"
        html_content += f"                <td class=\"score tooltip\" style=\"color: {master_color}; font-weight: bold; font-size: 1.1em;\" data-score=\"{master_score:.0f}\"><span style=\"cursor: help;\">{master_score:.0f}</span><span class=\"tooltiptext\" style=\"width: 500px; white-space: pre-wrap;\">{master_score_tooltip}</span></td>\n"
        
        html_content += f"                <td><span class=\"{risk_class}\">{risk_level_display}</span></td>\n"
        
        # Add news sentiment score
        news_sentiment = r.get('news_sentiment_score', 0) or 0
        news_headlines = r.get('news_headlines', []) or []
        news_count = r.get('news_count', 0) or 0
        try:
            news_sentiment = float(news_sentiment) if news_sentiment else 0
        except (TypeError, ValueError):
            news_sentiment = 0
        
        # Color code news sentiment
        if news_sentiment > 0.3:
            news_color = '#27ae60'  # Green - positive
            news_sentiment_label = 'Positive'
        elif news_sentiment < -0.3:
            news_color = '#e74c3c'  # Red - negative
            news_sentiment_label = 'Negative'
        else:
            news_color = '#95a5a6'  # Gray - neutral
            news_sentiment_label = 'Neutral'
        
        # Build news tooltip with headlines
        news_tooltip = f"<strong>News Sentiment Score</strong><br/><strong>Value: {news_sentiment:+.2f}</strong> ({news_sentiment_label})<br/><br/>" \
                       f"<strong>Interpretation:</strong><br/>" \
                       f"Negative news (-1 to 0): Can reduce confidence, trigger stop losses, or indicate selling pressure<br/>" \
                       f"Neutral news (±0.3): Market may ignore or digest news slowly - uncertainty risk<br/>" \
                       f"Positive news (0 to +1): Supports bullish moves, increases conviction, reduces reversals<br/><br/>" \
                       f"<strong>Action:</strong> Recent extreme sentiment (±0.8+) may indicate overbought/oversold - watch for mean reversion."
        
        # Add recent news headlines if available
        if news_headlines and news_count > 0:
            news_tooltip += f"<br/><br/><strong>Recent News ({news_count}):</strong><br/>"
            for i, headline in enumerate(news_headlines[:5], 1):  # Show top 5 headlines
                # Truncate long headlines
                headline_display = headline[:75] + "..." if len(headline) > 75 else headline
                news_tooltip += f"{i}. {headline_display}<br/>"
        
        html_content += f"                <td class=\"score\" style=\"color: {news_color}; font-weight: bold;\" data-score=\"{news_sentiment:+.4f}\"><span class=\"tooltip-trigger\" title=\"News sentiment analysis\"><span style=\"cursor: help;\">{news_sentiment:+.4f}</span><span class=\"tooltiptext\" style=\"width: 450px; white-space: normal;\">{news_tooltip}</span></span></td>\n"
        
        # ==================== EARNINGS INFO WITH TOOLTIP ====================
        earnings_next_date = r.get('earnings_next_date')
        earnings_days_until = r.get('earnings_days_until')
        earnings_confidence_modifier = r.get('earnings_confidence_modifier', 1.0) or 1.0
        earnings_modifier_reason = r.get('earnings_modifier_reason', '')
        
        # Format earnings display
        if earnings_next_date:
            # Determine risk level based on days until earnings
            if earnings_days_until is not None and isinstance(earnings_days_until, (int, float)):
                if -3 <= earnings_days_until <= 3:
                    earnings_risk = 'HIGH'
                    earnings_color = '#e74c3c'  # Red
                else:
                    earnings_risk = 'MEDIUM'
                    earnings_color = '#f39c12'  # Orange
                days_display = f"{int(earnings_days_until)}d"
            else:
                earnings_risk = 'MEDIUM'
                earnings_color = '#f39c12'
                days_display = "TBD"
            
            # Build earnings tooltip
            earnings_tooltip = f"<div style='max-width: 300px;'>"
            earnings_tooltip += f"<strong>Earnings Event</strong><br/>"
            earnings_tooltip += f"Date: {earnings_next_date}<br/>"
            if earnings_days_until is not None:
                earnings_tooltip += f"Days away: {earnings_days_until}<br/>"
            earnings_tooltip += f"Risk level: <strong>{earnings_risk}</strong><br/>"
            earnings_tooltip += f"Signal confidence: {earnings_confidence_modifier:.1%} (modifier)<br/>"
            if earnings_modifier_reason:
                earnings_tooltip += f"Reason: {earnings_modifier_reason}<br/>"
            earnings_tooltip += "</div>"
            
            earnings_cell = f"<span class='tooltip-trigger' style='color: {earnings_color}; font-weight: bold; cursor: help;'>{earnings_next_date} ({days_display})<span class='tooltiptext' style='width: 320px; left: -160px; white-space: normal;'>{earnings_tooltip}</span></span>"
        else:
            earnings_cell = "<span style='color: #95a5a6;'>No earnings</span>"
        
        
        # Add Relative Strength (single weighted column: 60% sector + 40% index)
        rs_weighted = r.get('rs_weighted', 0)
        
        # Color coding for weighted RS
        if rs_weighted > 0.15:
            rs_color = '#27ae60'  # Green - outperformer
            rs_badge = '<strong>+</strong>'
        elif rs_weighted < -0.15:
            rs_color = '#e74c3c'  # Red - underperformer
            rs_badge = '<strong>-</strong>'
        else:
            rs_color = '#95a5a6'  # Gray - neutral
            rs_badge = '<strong>○</strong>'
        
        html_content += f"                <td data-score=\"{rs_weighted:.4f}\" style='color: {rs_color};'><span class='tooltip-trigger' style='cursor: help;'>{rs_badge} {abs(rs_weighted):.3f}<span class='tooltiptext' style='width: 350px; left: -175px; white-space: normal;'>Relative strength (60% vs sector peers + 40% vs Nifty50): Positive = outperforming market, Negative = lagging market.</span></span></td>\n"
        
        html_content += f"                <td>{r.get('option_premium_quality') or 0:.4f}</td>\n"
        html_content += f"                <td data-price=\"{price:.2f}\">{price:.2f}</td>\n"
        html_content += f"                <td data-sl=\"{stop_loss:.2f}\" style=\"font-weight: bold; color: #e74c3c;\">{sl_str}</td>\n"
        html_content += f"                <td data-target=\"{target:.2f}\" style=\"font-weight: bold; color: #27ae60;\">{target_str}</td>\n"
        html_content += f"                <td data-score=\"{week52_high:.2f}\" style=\"font-weight: bold; color: #27ae60;\">{week52_high:.2f}</td>\n"
        html_content += f"                <td data-score=\"{week52_low:.2f}\" style=\"font-weight: bold; color: #c0392b;\">{week52_low:.2f}</td>\n"
        html_content += f"                <td data-score=\"{daily_change:.2f}\" style=\"color: {daily_color}; font-weight: bold;\">{daily_str}</td>\n"
        html_content += f"                <td data-score=\"{weekly_change:.2f}\" style=\"color: {weekly_color}; font-weight: bold;\">{weekly_str}</td>\n"
        html_content += f"                <td data-score=\"{pct_below_high:.2f}\" style=\"font-weight: bold; color: #e67e22;\">{pct_below_high_str}</td>\n"
        html_content += f"                <td data-score=\"{pct_above_low:.2f}\" style=\"font-weight: bold; color: #3498db;\">{pct_above_low_str}</td>\n"
        
        # Add Sector, Pattern, TF Align, Strategy columns (moved after 52W Low%)
        html_content += f"                <td style=\"background-color: {sector_color}; color: {sector_text_color}; font-weight: bold;\">{sector}</td>\n"
        html_content += f"                <td>{pattern_str}</td>\n"
        html_content += f"                <td><span class=\"{{align_class}} tooltip-trigger\" title=\"{align_tooltip}\">{align}<span class=\"tooltiptext\" style=\"width: 300px; bottom: 125%;\">{align_tooltip}</span></span></td>\n"
        html_content += f"                <td><span class=\"badge badge-{strategy_class} tooltip-trigger\" style=\"font-size: 0.85em; padding: 4px 8px; position: relative; display: inline-block;\" title=\"{STRATEGY_TOOLTIPS.get(strategy_class, 'Option strategy recommendation')}\">{strategy}<span class=\"tooltiptext\" style=\"width: 280px; bottom: 125%; left: 50%; transform: translateX(-50%); white-space: normal;\">{STRATEGY_TOOLTIPS.get(strategy_class, 'Option strategy recommendation')}</span></span></td>\n"
        
        html_content += f"                <td>{r.get('or_score', 0):+.4f}</td>\n"
        html_content += f"                <td>{r.get('vwap_score', 0):+.4f}</td>\n"
        html_content += f"                <td>{r.get('structure_score', 0):+.4f}</td>\n"
        html_content += f"                <td>{r.get('rsi') or 0:.2f}</td>\n"
        html_content += f"                <td>{r.get('ema_score', 0):+.4f}</td>\n"
        html_content += f"                <td>{r.get('volume_score', 0):+.4f}</td>\n"
        html_content += f"                <td>{r.get('macd_score', 0):+.4f}</td>\n"
        html_content += f"                <td>{r.get('bb_score', 0):+.4f}</td>\n"
        html_content += f"                <td>{atr_str}</td>\n"
        html_content += f"                <td>{r.get('option_iv') or 0:.4f}</td>\n"
        html_content += f"                <td>{r.get('option_spread_pct') or 0:.4f}</td>\n"
        html_content += f"                <td>{r.get('option_delta') or 0:+.4f}</td>\n"
        html_content += f"                <td>{r.get('option_gamma') or 0:.6f}</td>\n"
        html_content += f"                <td>{r.get('option_theta') or 0:+.4f}</td>\n"
        html_content += f"                <td>{r.get('option_vega') or 0:+.4f}</td>\n"
        html_content += f"                <td>{earnings_cell}</td>\n"
        html_content += f"            </tr>\n"
    
    html_content += """        </tbody>
    </table>
    </div>
    """
    
    # SIGNAL INTELLIGENCE SECTION (RESTORED)
    html_content += """
    <!-- SIGNAL INTELLIGENCE DASHBOARD -->
    <div class="dashboard">
        <h3>Signal Intelligence</h3>
        <p class="info" style="color: #718096; font-size: 13px; margin: 8px 0;">
            <strong>📊 Understanding Your Signals:</strong> 
            The 3-Pillar system breaks confidence into: Signal Agreement (do indicators align?), Momentum (EMA/RSI conviction), Volume (does volume support the move?). 
            Early signals show when institutions enter before retail. Timeframe alignment confirms trending moves.
        </p>
    """
    
    # Find top 4 stocks with best signal quality (limiting to 4 records)
    # Filter: Confidence first, then abs(score) as tiebreaker, exclude HIGH risk
    top_signals = sorted(
        [r for r in scored if r.get('final_score') is not None and r.get('risk_level', '').upper() != 'HIGH'],
        key=lambda x: (x.get('confidence', 0) or 0, abs(x.get('final_score', 0) or 0)),
        reverse=True
    )[:4]
    
    if top_signals:
        html_content += '<div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 14px; margin: 16px 0;">'
        
        cards_shown = 0
        for sig in top_signals:
            symbol = sig.get('symbol', 'N/A')
            score = sig.get('final_score', 0)
            conf = sig.get('confidence', 0) or 0
            
            # Extract 3-pillar data (stored in intermediate calculations during scoring)
            # We'll estimate from available components
            tf_5m = sig.get('score_5m', 0) or 0
            tf_15m = sig.get('score_15m', 0) or 0
            tf_1h = sig.get('score_1h', 0) or 0
            
            # Count signal agreement (how many indicators agree)
            ema_s = sig.get('ema_score', 0) or 0
            rsi_s = sig.get('rsi_score', 0) or 0 if sig.get('rsi', 0) else 0
            macd_s = sig.get('macd_score', 0) or 0
            struct_s = sig.get('structure_score', 0) or 0
            vol_s = sig.get('volume_score', 0) or 0
            bb_s = sig.get('bb_score', 0) or 0
            
            # Timeframe alignment
            tf_dirs = [1 if x > 0 else -1 if x < 0 else 0 for x in [tf_5m, tf_15m, tf_1h]]
            tf_aligned = max(sum(1 for d in tf_dirs if d > 0), sum(1 for d in tf_dirs if d < 0))
            
            # Early signals
            vol_accel = sig.get('volume_acceleration', 0) or 0
            vwap_cross = sig.get('vwap_crossover', 0) or 0
            or_breakout = sig.get('opening_range_breakout', 0) or 0
            early_signals_active = sum(1 for x in [vol_accel, vwap_cross, or_breakout] if abs(x) > 0.5)
            
            # Count strong signals (>0.3) from 6 base indicators
            strong_signals = sum(1 for x in [ema_s, rsi_s, macd_s, struct_s, vol_s, bb_s] if abs(x) > 0.3)
            
            # ADD to signal agreement count: Timeframe alignment + Early signals
            # Timeframe Align (2/3 or 3/3 = strong confirmation)
            if tf_aligned >= 2:
                strong_signals += 1  # +1 for multi-timeframe agreement
            
            # Early Signals (2/3 or 3/3 = strong institutional activity)
            if early_signals_active >= 2:
                strong_signals += 1  # +1 for early signal agreement
            
            # FILTER: Only show cards for stocks with strong consensus (4+ signals total)
            if strong_signals < 4:
                continue
            
            cards_shown += 1
            
            # Momentum conviction (average of momentum indicators)
            momentum_avg = abs((ema_s + rsi_s + macd_s) / 3) if any([ema_s, rsi_s, macd_s]) else 0
            
            # Volume validation
            vol_support = vol_s > 0.5 if vol_s else False
            
            # Current vs avg volume (estimate from volume_score)
            vol_mult = "Strong" if vol_s > 0.6 else "Normal" if vol_s > 0 else "Weak"
            
            # RSI state
            rsi_val = sig.get('rsi', 50) or 50
            if rsi_val > 70:
                rsi_state = "Overbought"
                rsi_color = "#ff6a00"
            elif rsi_val < 30:
                rsi_state = "Oversold"
                rsi_color = "#11998e"
            elif rsi_val > 60:
                rsi_state = "Strong"
                rsi_color = "#f6ad55"
            elif rsi_val < 40:
                rsi_state = "Weak"
                rsi_color = "#4299e1"
            else:
                rsi_state = "Neutral"
                rsi_color = "#95a5a6"
            
            # Sentiment badge
            sentiment_emoji = "📉" if score < -0.05 else "📈" if score > 0.05 else "➡️"
            sentiment_color = "#ff6a00" if score < -0.05 else "#11998e" if score > 0.05 else "#95a5a6"
            
            html_content += f'''<div style="background: white; border-radius: 10px; padding: 14px; border-left: 5px solid {sentiment_color}; box-shadow: 0 2px 8px rgba(0,0,0,0.06);">
                <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px;">
                    <div style="font-weight: 600; font-size: 16px; color: #2d3748;">{sentiment_emoji} {symbol}</div>
                    <div style="font-weight: 700; font-size: 14px; color: {sentiment_color};">{score:+.3f}</div>
                </div>
                
                <div style="background: #f8f9fa; padding: 10px; border-radius: 6px; font-size: 12px; margin-bottom: 10px;">
                    <div style="display: flex; justify-content: space-between; margin-bottom: 6px;">
                        <span style="color: #4a5568;">🎯 <strong>Confidence:</strong></span>
                        <span style="font-weight: 600; color: #667eea;">{conf:.0f}%</span>
                    </div>
                    
                    <div style="display: grid; grid-template-columns: 1fr 1fr 1fr; gap: 8px; font-size: 11px; margin-top: 8px;">
                        <div style="background: white; padding: 6px; border-radius: 4px; text-align: center;">
                            <div style="color: #718096; font-size: 10px;">Signal Agree</div>
                            <div style="font-weight: 700; color: #667eea; font-size: 13px;">{strong_signals}/8</div>
                        </div>
                        <div style="background: white; padding: 6px; border-radius: 4px; text-align: center;">
                            <div style="color: #718096; font-size: 10px;">Momentum</div>
                            <div style="font-weight: 700; color: #f39c12; font-size: 13px;">{momentum_avg:.2f}</div>
                        </div>
                        <div style="background: white; padding: 6px; border-radius: 4px; text-align: center;">
                            <div style="color: #718096; font-size: 10px;">Volume</div>
                            <div style="font-weight: 700; color: #38ef7d; font-size: 13px;">{'✓' if vol_support else '✗'}</div>
                        </div>
                    </div>
                </div>
                
                <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 8px; font-size: 11px; margin-bottom: 10px;">
                    <div style="background: #f0f4ff; padding: 8px; border-radius: 4px;">
                        <div style="color: #667eea; font-weight: 600; margin-bottom: 4px;">⏱️ Timeframe Align</div>
                        <div style="font-weight: 700; color: #2d3748;">{tf_aligned}/3 TF</div>
                        <div style="color: #718096; font-size: 10px; margin-top: 2px;">5m:{tf_5m:+.2f} 15m:{tf_15m:+.2f} 1h:{tf_1h:+.2f}</div>
                    </div>
                    <div style="background: #fff4f0; padding: 8px; border-radius: 4px;">
                        <div style="color: #ff6a00; font-weight: 600; margin-bottom: 4px;">⚡ Early Signals</div>
                        <div style="font-weight: 700; color: #2d3748;">{early_signals_active}/3</div>
                        <div style="color: #718096; font-size: 10px; margin-top: 2px;">Vol:{abs(vol_accel):.2f} VWAP:{abs(vwap_cross):.2f} OR:{abs(or_breakout):.2f}</div>
                    </div>
                </div>
                
                <div style="display: flex; justify-content: space-between; font-size: 11px; padding-top: 8px; border-top: 1px solid #e2e8f0;">
                    <span style="color: #4a5568;">RSI: <span style="font-weight: 600; color: {rsi_color};">{rsi_val:.0f}</span> ({rsi_state})</span>
                    <span style="color: #4a5568;">Vol: <span style="font-weight: 600; color: #38ef7d;">{vol_mult}</span></span>
                </div>
            </div>'''
        
        html_content += '</div>'
        
        # If no cards passed the strong consensus filter, show info message
        if cards_shown == 0:
            html_content = html_content.replace(
                '<div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 14px; margin: 16px 0;"></div>',
                '<div style="background: #f0f4ff; padding: 16px; border-radius: 6px; text-align: center; color: #4a5568; margin: 16px 0;"><strong>💭 Tip:</strong> No stocks currently show 4+ signals agreeing. This is a strict filter showing only highest-consensus setups.</div>'
            )
    
    html_content += '</div>'  # Close signal intelligence dashboard
    
    # PREMIUM SELLING STRATEGY SECTION
    html_content += """
    <!-- PREMIUM SELLING STRATEGIES -->
    <div class="dashboard">
        <h3>Premium Selling Strategies</h3>
        <p class="info" style="color: #718096; font-size: 13px; margin: 8px 0;">
            <strong>💵 Income Generation Playbook:</strong> 
            Strategies ranked by Greeks quality & IV environment. <strong>High IV (>40%)</strong> = Sell premium strategies (spreads, strangles, iron condors). 
            <strong>Theta positive</strong> = time decay in your favor. <strong>Low gamma</strong> = stable positions. <strong>Spread < 3%</strong> = good liquidity.
        </p>
    """
    
    # Show ALL stocks ranked by Greeks quality (gamma safety + spread efficiency)
    # Don't filter by WAIT - show best available in current conditions
    ranked_strategies = []
    for r in scored:
        if r.get('option_premium_quality') is not None and r.get('option_theta') is not None:
            opt_gamma = r.get('option_gamma', 0.05) or 0.05
            opt_spread = r.get('option_spread_pct', 2.5) or 2.5
            opt_quality = r.get('option_premium_quality', 0.5) or 0.5
            
            # Greeks quality score: prefer low gamma (stable) + tight spreads (liquid) + high quality
            # Lower gamma = better (0.005 is better than 0.05)
            # Lower spread = better (1.0 is better than 3.0)
            # Higher quality = better (0.8 is better than 0.5)
            greeks_score = (opt_quality * 100) - (opt_gamma * 500) - (opt_spread * 10)
            
            ranked_strategies.append((r, greeks_score))
    
    # Sort by Greeks quality score and take top 4
    top_premium_strategies = sorted(
        ranked_strategies,
        key=lambda x: x[1],
        reverse=True
    )[:4]
    
    # Extract just the strategy records
    top_premium_strategies = [x[0] for x in top_premium_strategies]
    
    if top_premium_strategies:
        html_content += '<div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(350px, 1fr)); gap: 14px; margin: 16px 0;">'
        
        for strat in top_premium_strategies:
            symbol = strat.get('symbol', 'N/A')
            price = strat.get('price', 0) or 0
            
            # Option metrics for selling
            opt_iv = strat.get('option_iv', 0.30) or 0.30
            opt_spread = strat.get('option_spread_pct', 2.5) or 2.5
            opt_delta = strat.get('option_delta', 0.5) or 0.5
            opt_gamma = strat.get('option_gamma', 0.05) or 0.05
            opt_theta = strat.get('option_theta', -0.01) or -0.01
            opt_quality = strat.get('option_premium_quality', 0.5) or 0.5
            oi = strat.get('option_oi', 0) or 0
            volume = strat.get('option_volume', 0) or 0
            
            # ===== DETERMINE SELLING STRATEGY BASED ON IV & GREEKS =====
            
            # 1. IV Assessment (key for premium selling)
            if opt_iv > 0.65:
                iv_tier = "🔴 VERY HIGH IV"
                iv_color = "#c0392b"
                iv_message = "Premium collectors paradise - sell aggressive spreads"
            elif opt_iv > 0.50:
                iv_tier = "🟠 HIGH IV"
                iv_color = "#ff6a00"
                iv_message = "Excellent for premium selling - use spreads or strangles"
            elif opt_iv > 0.35:
                iv_tier = "🟡 MEDIUM IV"
                iv_color = "#f6ad55"
                iv_message = "Good for income strategies - consider spreads over naked"
            else:
                iv_tier = "🟢 LOW IV"
                iv_color = "#4299e1"
                iv_message = "Avoid naked selling - spreads only or buy side"
            
            # 2. Theta Assessment (daily decay for seller)
            theta_daily = opt_theta * 365  # Annual to daily
            if theta_daily > 0.05:
                theta_tier = "✓✓✓ STRONG"
                theta_color = "#11998e"
                theta_msg = "Excellent daily decay - each day profits"
            elif theta_daily > 0.01:
                theta_tier = "✓✓ GOOD"
                theta_color = "#38ef7d"
                theta_msg = "Decent daily decay - slow profit"
            else:
                theta_tier = "✓ WEAK"
                theta_color = "#f6ad55"
                theta_msg = "Minimal daily decay - longer holding"
            
            # 3. Liquidity/Spread Assessment
            if opt_spread < 1.5:
                liquidity_tier = "💧 EXCELLENT"
                liq_color = "#11998e"
                liq_msg = "Tight spreads - instant execution"
            elif opt_spread < 3.0:
                liquidity_tier = "💧💧 GOOD"
                liq_color = "#38ef7d"
                liq_msg = "Acceptable spreads - normal cost"
            elif opt_spread < 5.0:
                liquidity_tier = "💧💧💧 FAIR"
                liq_color = "#f6ad55"
                liq_msg = "Wider spreads - execution cost matters"
            else:
                liquidity_tier = "⚠️ POOR"
                liq_color = "#e74c3c"
                liq_msg = "Very wide - high slippage risk"
            
            # 4. Gamma Risk Assessment (for short premium)
            if opt_gamma < 0.008:
                gamma_tier = "✓ SAFE"
                gamma_color = "#11998e"
                gamma_msg = "Very stable delta - minimal hedging"
            elif opt_gamma < 0.015:
                gamma_tier = "✓✓ ACCEPTABLE"
                gamma_color = "#38ef7d"
                gamma_msg = "Moderate gamma - some hedging advisable"
            elif opt_gamma < 0.025:
                gamma_tier = "⚠️ RISKY"
                gamma_color = "#f6ad55"
                gamma_msg = "High gamma - needs active management"
            else:
                gamma_tier = "🚫 AVOID"
                gamma_color = "#e74c3c"
                gamma_msg = "Extreme gamma - too much delta risk"
            
            # 5. Position Type Recommendation
            if opt_iv > 0.50 and opt_gamma < 0.015 and opt_spread < 3.0:
                position_type = "🎯 IRON CONDOR / STRANGLE"
                position_color = "#11998e"
                position_detail = "Sell OTM calls & puts, collect premium on both sides"
                strikes = f"Sell {int(price/100)*100+200} Call, Sell {int(price/100)*100-200} Put"
            elif opt_iv > 0.50 and opt_delta > 0.30:
                position_type = "📍 CASH SECURED PUT SPREAD"
                position_color = "#38ef7d"
                position_detail = "Sell ATM put, buy OTM put for defined risk"
                strikes = f"Sell {int(price/100)*100} Put, Buy {int(price/100)*100-100} Put"
            elif opt_iv > 0.50 and opt_delta < 0.70:
                position_type = "📍 CALL SPREAD"
                position_color = "#38ef7d"
                position_detail = "Sell OTM call, buy further OTM call for defined risk"
                strikes = f"Sell {int(price/100)*100+100} Call, Buy {int(price/100)*100+200} Call"
            elif opt_iv > 0.35 and opt_gamma < 0.010:
                position_type = "🔄 RATIO CALL SPREAD"
                position_color = "#f6ad55"
                position_detail = "Higher risk/reward - requires expertise"
                strikes = f"Sell {int(price/100)*100+100} Call, Buy {int(price/100)*100+200} Call"
            else:
                position_type = "⏸️ WAIT"
                position_color = "#95a5a6"
                position_detail = "Conditions not ideal for aggressive selling"
                strikes = "Monitor for better setup"
            
            # 6. Risk metrics
            max_profit_potential = f"Premium collected - max profit if expires OTM"
            max_loss_potential = f"Width of spread or naked exposure"
            
            quality_badge = "Excellent ✓✓✓" if opt_quality > 0.75 else "Good ✓✓" if opt_quality > 0.60 else "Fair ✓" if opt_quality > 0.45 else "Poor"
            
            html_content += f'''<div style="background: white; border-radius: 10px; padding: 14px; border-left: 5px solid {iv_color}; box-shadow: 0 2px 8px rgba(0,0,0,0.06);">
                <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 10px;">
                    <div style="font-weight: 600; font-size: 16px; color: #2d3748;">{symbol} @ ₹{price:.2f}</div>
                    <div style="font-weight: 700; font-size: 11px; background: {iv_color}; color: white; padding: 4px 8px; border-radius: 4px;">{quality_badge}</div>
                </div>
                
                <!-- Market Conditions -->
                <div style="display: grid; grid-template-columns: 1fr 1fr 1fr; gap: 8px; font-size: 11px; margin-bottom: 10px;">
                    <div style="background: linear-gradient(135deg, {iv_color}22 0%, transparent 100%); padding: 8px; border-radius: 4px; border-left: 3px solid {iv_color};">
                        <div style="color: #718096; font-size: 10px; font-weight: 600;">IV Level</div>
                        <div style="font-weight: 700; color: {iv_color}; font-size: 12px;">{opt_iv:.0%}</div>
                        <div style="color: {iv_color}; font-size: 9px; font-weight: 500;">{iv_tier}</div>
                    </div>
                    <div style="background: linear-gradient(135deg, {theta_color}22 0%, transparent 100%); padding: 8px; border-radius: 4px; border-left: 3px solid {theta_color};">
                        <div style="color: #718096; font-size: 10px; font-weight: 600;">Daily Theta</div>
                        <div style="font-weight: 700; color: {theta_color}; font-size: 12px;">{theta_daily:+.4f}</div>
                        <div style="color: {theta_color}; font-size: 9px; font-weight: 500;">{theta_tier}</div>
                    </div>
                    <div style="background: linear-gradient(135deg, {liq_color}22 0%, transparent 100%); padding: 8px; border-radius: 4px; border-left: 3px solid {liq_color};">
                        <div style="color: #718096; font-size: 10px; font-weight: 600;">Spread</div>
                        <div style="font-weight: 700; color: {liq_color}; font-size: 12px;">{opt_spread:.2f}%</div>
                        <div style="color: {liq_color}; font-size: 9px; font-weight: 500;">{liquidity_tier}</div>
                    </div>
                </div>
                
                <!-- Greeks Assessment -->
                <div style="background: #f8f9fa; padding: 10px; border-radius: 6px; margin-bottom: 10px; border-left: 3px solid {gamma_color};">
                    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 6px;">
                        <div style="font-weight: 700; color: #2d3748; font-size: 12px;">Greeks Safety</div>
                        <div style="color: {gamma_color}; font-weight: 600; font-size: 11px;">{gamma_tier}</div>
                    </div>
                    <div style="color: #4a5568; font-size: 11px; margin-bottom: 6px;">Gamma: {opt_gamma:.5f} (delta swings) | Delta: {opt_delta:.2f} (directional) | Vega: {strat.get('option_vega', 0.1):.2f}</div>
                    <div style="color: {gamma_color}; font-size: 10px; font-weight: 500;">{gamma_msg}</div>
                </div>
                
                <!-- Recommended Strategy -->
                <div style="background: linear-gradient(135deg, {position_color}22 0%, transparent 100%); padding: 10px; border-radius: 6px; margin-bottom: 10px; border-left: 3px solid {position_color};">
                    <div style="font-weight: 700; color: {position_color}; font-size: 13px; margin-bottom: 6px;">{position_type}</div>
                    <div style="color: #4a5568; font-size: 11px; line-height: 1.4; margin-bottom: 6px;">{position_detail}</div>
                    <div style="background: white; padding: 6px; border-radius: 4px; color: #2d3748; font-weight: 600; font-size: 10px; font-family: monospace;">{strikes}</div>
                </div>
                
                <!-- Quick Summary -->
                <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 8px; font-size: 10px; padding-top: 8px; border-top: 1px solid #e2e8f0;">
                    <div style="background: #f8f9fa; padding: 6px; border-radius: 4px; text-align: center;">
                        <div style="color: #718096; font-weight: 600;">Max Risk</div>
                        <div style="color: #e74c3c; font-weight: 700;">Spread Width</div>
                    </div>
                    <div style="background: #f8f9fa; padding: 6px; border-radius: 4px; text-align: center;">
                        <div style="color: #718096; font-weight: 600;">Break Even</div>
                        <div style="color: #667eea; font-weight: 700;">Strike ± Premium</div>
                    </div>
                </div>
            </div>'''
        
        html_content += '</div>'
    else:
        html_content += '<div style="background: #fff3cd; padding: 16px; border-radius: 6px; text-align: center; color: #856404; margin: 16px 0; border-left: 4px solid #ffc107;"><strong>⏸️ No Ideal Setups Right Now:</strong> All stocks are in "WAIT" mode. Market conditions not favorable for aggressive premium selling. Monitor for better IV/Gamma conditions.</div>'
    
    html_content += '</div>'  # Close premium selling strategies dashboard
    
    # DASHBOARD SECTIONS (AFTER TABLE)
    html_content += """
    <!-- DASHBOARD SECTIONS (AFTER SCREENER TABLE) -->
    <div class="dashboard">
        <!-- KEY METRICS & MARKET SUMMARY -->
        <h3>Market Intelligence Summary</h3>
    """
    
    # Calculate meaningful metrics
    bearish_count = len([r for r in scored if r.get('final_score', 0) < -0.05])
    bullish_count = len([r for r in scored if r.get('final_score', 0) > 0.05])
    neutral_count = len(scored) - bullish_count - bearish_count
    
    avg_confidence = sum([r.get('confidence', 0) or 0 for r in scored]) / len(scored) if scored else 0
    high_confidence = len([r for r in scored if (r.get('confidence', 0) or 0) >= 70])
    
    avg_score = sum([r.get('final_score', 0) or 0 for r in scored]) / len(scored) if scored else 0
    
    # Volume and liquidity metrics
    avg_volume = sum([r.get('volume', 0) or 0 for r in scored]) / len(scored) if scored else 0
    
    # Option metrics
    avg_iv = sum([r.get('option_iv', 0) or 0 for r in scored if r.get('option_iv')]) / len([r for r in scored if r.get('option_iv')]) if any(r.get('option_iv') for r in scored) else 0
    
    # Determine market regime
    if avg_score > 0.05:
        market_bias = "BULLISH"
        market_color = "#11998e"
        market_emoji = "📈"
    elif avg_score < -0.05:
        market_bias = "BEARISH"
        market_color = "#e74c3c"
        market_emoji = "📉"
    else:
        market_bias = "NEUTRAL"
        market_color = "#95a5a6"
        market_emoji = "⚪"
    
    # Confidence interpretation
    if avg_confidence >= 70:
        conf_level = "HIGH CONFIDENCE"
        conf_color = "#27ae60"
    elif avg_confidence >= 60:
        conf_level = "GOOD CONFIDENCE"
        conf_color = "#38ef7d"
    else:
        conf_level = "MODERATE CAUTION"
        conf_color = "#f39c12"
    
    # IV Regime
    if avg_iv > 0.40:
        iv_regime = "PREMIUM SELLING FAVORABLE"
        iv_color = "#ff6a00"
    elif avg_iv > 0.25:
        iv_regime = "BALANCED (Buy or Sell)"
        iv_color = "#f39c12"
    else:
        iv_regime = "DIRECTIONAL BUYING FAVORABLE"
        iv_color = "#3498db"
    
    html_content += f'''
        <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(220px, 1fr)); gap: 14px; margin: 16px 0;">
            <!-- Market Sentiment -->
            <div style="background: linear-gradient(135deg, {market_color}22 0%, transparent 100%); padding: 16px; border-radius: 8px; border-left: 4px solid {market_color};">
                <div style="font-size: 11px; color: #718096; font-weight: 500; text-transform: uppercase; margin-bottom: 4px;">Overall Bias</div>
                <div style="font-size: 24px; font-weight: 700; color: {market_color}; margin-bottom: 2px;">{market_emoji} {market_bias}</div>
                <div style="font-size: 12px; color: #4a5568;">Avg Score: {avg_score:+.3f}</div>
            </div>
            
            <!-- Confidence Level -->
            <div style="background: linear-gradient(135deg, {conf_color}22 0%, transparent 100%); padding: 16px; border-radius: 8px; border-left: 4px solid {conf_color};">
                <div style="font-size: 11px; color: #718096; font-weight: 500; text-transform: uppercase; margin-bottom: 4px;">Signal Quality</div>
                <div style="font-size: 24px; font-weight: 700; color: {conf_color}; margin-bottom: 2px;">{avg_confidence:.0f}%</div>
                <div style="font-size: 12px; color: #4a5568;">{conf_level}</div>
            </div>
            
            <!-- IV Regime -->
            <div style="background: linear-gradient(135deg, {iv_color}22 0%, transparent 100%); padding: 16px; border-radius: 8px; border-left: 4px solid {iv_color};">
                <div style="font-size: 11px; color: #718096; font-weight: 500; text-transform: uppercase; margin-bottom: 4px;">Option Regime</div>
                <div style="font-size: 14px; font-weight: 700; color: {iv_color}; margin-bottom: 2px;">{avg_iv:.1%} IV</div>
                <div style="font-size: 11px; color: #4a5568;">{iv_regime}</div>
            </div>
            
            <!-- Setup Distribution -->
            <div style="background: linear-gradient(135deg, #667eea22 0%, transparent 100%); padding: 16px; border-radius: 8px; border-left: 4px solid #667eea;">
                <div style="font-size: 11px; color: #718096; font-weight: 500; text-transform: uppercase; margin-bottom: 8px;">Setup Distribution</div>
                <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 8px;">
                    <div style="text-align: center;">
                        <div style="font-size: 16px; font-weight: 700; color: #11998e;">🟢 {bullish_count}</div>
                        <div style="font-size: 10px; color: #718096;">Bullish</div>
                    </div>
                    <div style="text-align: center;">
                        <div style="font-size: 16px; font-weight: 700; color: #e74c3c;">🔴 {bearish_count}</div>
                        <div style="font-size: 10px; color: #718096;">Bearish</div>
                    </div>
                </div>
            </div>
            
            <!-- High Conviction Setups -->
            <div style="background: linear-gradient(135deg, #9f7aea22 0%, transparent 100%); padding: 16px; border-radius: 8px; border-left: 4px solid #9f7aea;">
                <div style="font-size: 11px; color: #718096; font-weight: 500; text-transform: uppercase; margin-bottom: 4px;">High Conviction</div>
                <div style="font-size: 24px; font-weight: 700; color: #9f7aea; margin-bottom: 2px;">{high_confidence}</div>
                <div style="font-size: 12px; color: #4a5568;">Confidence >= 70%</div>
            </div>
            
            <!-- Liquidity Index -->
            <div style="background: linear-gradient(135deg, #4299e122 0%, transparent 100%); padding: 16px; border-radius: 8px; border-left: 4px solid #4299e1;">
                <div style="font-size: 11px; color: #718096; font-weight: 500; text-transform: uppercase; margin-bottom: 4px;">Total Watchlist</div>
                <div style="font-size: 24px; font-weight: 700; color: #4299e1; margin-bottom: 2px;">{len(scored)}</div>
                <div style="font-size: 12px; color: #4a5568;">Stocks analyzed</div>
            </div>
        </div>
        
        <!-- ACTION RECOMMENDATIONS -->
        <div style="background: linear-gradient(135deg, #f6ad5522 0%, transparent 100%); padding: 16px; border-radius: 8px; margin: 16px 0; border-left: 4px solid #f39c12;">
            <div style="font-size: 12px; color: #d35400; font-weight: 600; text-transform: uppercase; margin-bottom: 8px;">⚡ Trading Recommendations</div>
            <ul style="margin: 0; padding-left: 20px; color: #4a5568; font-size: 12px; line-height: 1.6;">
                <li>
                    <strong>Market Bias:</strong> 
                    {('Strong bullish momentum - favor long positions and bull spreads' if avg_score > 0.1 else 'Mild bullish - consider bullish setups with stops' if avg_score > 0.05 else 'Mild bearish - consider bearish setups with stops' if avg_score < -0.05 else 'Neutral - use directional indicators for entry')}
                </li>
                <li>
                    <strong>Signal Quality:</strong>
                    {('Excellent - high conviction setups, follow recommendations closely' if avg_confidence >= 70 else 'Good - solid setups, follow with reasonable stops' if avg_confidence >= 60 else 'Moderate - be selective, use tighter stops')}
                </li>
                <li>
                    <strong>Options Strategy:</strong>
                    {('High IV favors premium selling (spreads, covered calls)' if avg_iv > 0.40 else 'Balanced - can buy or sell premium' if avg_iv > 0.25 else 'Low IV favors buying directional options')}
                </li>
            </ul>
        </div>
    '''
    
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
    
    html_content += '</div></div>'
    
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
    const enableScore = document.getElementById("enableMinScore").checked;
    const minScore = parseFloat(document.getElementById("minScore").value) || 0;
    const enableRS = document.getElementById("enableMinRS").checked;
    const minRS = parseFloat(document.getElementById("minRS").value) || -1;
    const sectorSel = document.getElementById("sectorFilter").value.toLowerCase();
    
    for (let i = 0; i < rows.length; i++) {
        const r = rows[i];
        const textMatch = r.innerText.toLowerCase().includes(v);
        
        let confVal = 0;
        let scoreVal = 0;
        let rsVal = 0;
        // Column positions: 0 Rank, 1 Symbol, 2 Trend, 3 Score, 4 Swing Score, 5 LT Score, 6 Conf%, 7 State, 8 Context, 9 Context Mom, 10 Risk Zone, 11 News Sentiment, 12 Rel Strength, 13 Opt Quality, 14 Price, 15 Stop Loss, 16 Target, 17-22 Price data, 23 Sector, 24 Pattern, 25 TF Align, 26 Strategy, 27+ Technical indicators
        if (r.cells[6]) {
            const confText = r.cells[6].getAttribute("data-conf") || r.cells[6].innerText.trim();
            confVal = parseFloat(confText) || 0;
        }
        if (r.cells[3]) {
            const scoreText = r.cells[3].getAttribute("data-score") || r.cells[3].innerText.trim();
            scoreVal = Math.abs(parseFloat(scoreText)) || 0;
        }
        if (r.cells[12]) {
            const rsText = r.cells[12].getAttribute("data-score") || r.cells[12].innerText.trim();
            rsVal = parseFloat(rsText) || 0;
        }
        
        const sectorCell = r.cells[23] ? (r.cells[23].innerText || "").toLowerCase() : "";
        const sectorMatch = (sectorSel === "all") || (sectorCell === sectorSel);
        const confMatch = (!enableConf) || (confVal >= minConf);
        const scoreMatch = (!enableScore) || (scoreVal >= minScore);
        const rsMatch = (!enableRS) || (rsVal >= minRS);
        r.style.display = (textMatch && sectorMatch && confMatch && scoreMatch && rsMatch) ? "" : "none";
    }
}

// Populate sector dropdown from table rows
function populateSectors() {
    const rows = document.getElementById("screener").tBodies[0].rows;
    const sectors = new Set();
    for (let i = 0; i < rows.length; i++) {
        const cell = rows[i].cells[23];
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


class OptimizedWorker6Thread(threading.Thread):
    """6-thread optimized worker with cap-aware routing"""
    
    def __init__(self, thread_id, cap_type, stock_queue, results, lock, engine):
        super().__init__()
        self.thread_id = thread_id
        self.cap_type = cap_type  # 'largecap' or 'midsmall'
        self.stock_queue = stock_queue
        self.results = results
        self.lock = lock
        self.engine = engine
        self.daemon = False
        self.processed = 0
        
    def run(self):
        """Process stocks from queue - light computation only"""
        while True:
            try:
                stock_item = self.stock_queue.get(timeout=1)
            except queue.Empty:
                break
            
            sym, u = stock_item
            
            try:
                # Just compute score, skip enrichment (will happen later)
                data = self.engine.compute_score(sym)
                if data:
                    data['index'] = u
                    
                    with self.lock:
                        self.results[sym] = data
                        self.processed += 1
                        
                        if self.processed % 10 == 0:
                            print(f"[T{self.thread_id}] {self.processed} processed")
            except Exception as e:
                with self.lock:
                    self.results[sym] = {"symbol": sym, "status": "ERROR", "index": u}
            finally:
                self.stock_queue.task_done()
        
        with self.lock:
            print(f"[T{self.thread_id}] DONE: {self.processed} processed")


def run_with_6thread(syms, engine, num_threads=6):
    """Run with optimized N-thread setup (2:1 yF:Breeze ratio)"""
    
    print("\n" + "=" * 80)
    print(f"{num_threads}-THREAD OPTIMIZED EXECUTION (2:1 yFinance:Breeze ratio)")
    print("=" * 80)
    
    # Load cap distribution if available
    largecap_set = set()
    midsmall_set = set()
    try:
        config_path = Path("fallback_strategy_config.json")
        if config_path.exists():
            import json
            config = json.load(open(config_path))
            largecap_set = set(config['universes']['largecap'])
            midsmall_set = set(config['universes']['midsmall'])
    except:
        pass
    
    # Calculate thread distribution: 2:1 ratio (yF:Breeze)
    yf_threads = max(2, (num_threads * 2) // 3)  # At least 2 yF threads
    breeze_threads = max(1, num_threads - yf_threads)  # Remaining for Breeze
    overflow_threads = 0
    
    # For 8 threads: 5 yF, 2 Breeze, 1 overflow
    if num_threads == 8:
        yf_threads = 5
        breeze_threads = 2
        overflow_threads = 1
    
    # Distribute stocks
    queue_largecap = queue.Queue()
    queue_midsmall = queue.Queue()
    results = {}
    lock = threading.Lock()
    
    for sym, u in syms:
        if sym in largecap_set:
            queue_largecap.put((sym, u))
        else:
            queue_midsmall.put((sym, u))
    
    largecap_count = queue_largecap.qsize()
    midsmall_count = queue_midsmall.qsize()
    
    print(f"\nStock distribution:")
    print(f"  Largecap (Breeze-preferred): {largecap_count}")
    print(f"  Mid/Small (yF-preferred): {midsmall_count}")
    print(f"  Total: {largecap_count + midsmall_count}")
    
    print(f"\nThread allocation ({num_threads} total):")
    print(f"  Threads 1-{yf_threads}: yFinance-first (mid/small)")
    print(f"  Threads {yf_threads+1}-{yf_threads+breeze_threads}: Breeze-first (largecap)")
    if overflow_threads > 0:
        print(f"  Thread {yf_threads+breeze_threads+1}: Adaptive overflow")
    print()
    
    threads = []
    start_time = time.time()
    
    # yFinance-first threads (majority)
    for i in range(1, yf_threads + 1):
        t = OptimizedWorker6Thread(i, 'midsmall', queue_midsmall, results, lock, engine)
        threads.append(t)
        t.start()
    
    # Breeze-first threads
    for i in range(yf_threads + 1, yf_threads + breeze_threads + 1):
        t = OptimizedWorker6Thread(i, 'largecap', queue_largecap, results, lock, engine)
        threads.append(t)
        t.start()
    
    # Overflow thread (if exists)
    if overflow_threads > 0:
        t = OptimizedWorker6Thread(yf_threads + breeze_threads + 1, 'midsmall', queue_midsmall, results, lock, engine)
        threads.append(t)
        t.start()
    
    for t in threads:
        t.join()
    
    elapsed = time.time() - start_time
    
    print("\n" + "=" * 80)
    print(f"{num_threads}-THREAD EXECUTION COMPLETE: {elapsed:.1f}s ({elapsed/60:.2f}min)")
    print("=" * 80)
    
    # Convert results dict to list
    results_list = list(results.values())
    return results_list, elapsed


def main():
    import time as time_module
    t_start = time_module.time()
    print(f"[START] {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} - Starting Nifty screener")
    
    parser = argparse.ArgumentParser(description='Rank stocks by bearness - Refactored V2')
    parser.add_argument('--universe', default='nifty', help='Universe name or custom filename (will look for <universe>_constituents.txt)')
    parser.add_argument('--mode', default='swing', choices=['intraday', 'swing', 'longterm', 'custom'])
    parser.add_argument('--intraday-w', type=float, default=None)
    parser.add_argument('--swing-w', type=float, default=None)
    parser.add_argument('--longterm-w', type=float, default=None)
    parser.add_argument('--use-yf', action='store_true')
    parser.add_argument('--force-yf', action='store_true')
    parser.add_argument('--force-breeze', action='store_true', help='Force Breeze only (no yFinance fallback)')
    parser.add_argument('--quick', action='store_true')
    parser.add_argument('--num-threads', type=int, default=6, choices=[4, 6, 8, 10, 12], help='Number of threads (default 6, use 10-12 for Nifty50+)')
    parser.add_argument('--skip-news', action='store_true', help='Skip news sentiment fetch (faster for large universes)')
    parser.add_argument('--skip-rs', action='store_true', help='Skip relative strength calculations (faster, sort later)')
    parser.add_argument('--no-6thread', action='store_true', help='Disable 6-thread execution (use standard parallel)')
    parser.add_argument('--export', help='Output CSV path')
    parser.add_argument('--screener-format', choices=['csv', 'html'], default='csv', help='Export format')
    parser.add_argument('--fetch', action='store_true')
    parser.add_argument('--save-db', action='store_true', help='Automatically load results to database')
    parser.add_argument('--no-wait-strategy', action='store_true', help='Disable intelligent rate limiting')
    parser.add_argument('--retry-symbols-from', type=str, default=None, help='CSV file to load failed symbols for retry (e.g., nifty_bearnness.csv)')
    parser.add_argument('--retry-attempt', type=int, default=1, help='Which retry attempt (1=first run, 2=retry1, 3=retry2)')
    parser.add_argument('--merge-with', type=str, default=None, help='CSV file to merge results with (cumulative reporting)')
    args = parser.parse_args()
    
    # Load universe first
    syms = UniverseManager.load(universe=args.universe, fetch_if_missing=args.fetch)
    print(f"[INFO] Loaded {len(syms)} symbols from '{args.universe}'")
    
    # Handle retry mode: load only failed symbols from previous run
    if args.retry_symbols_from:
        failed_syms = load_failed_symbols_from_csv(args.retry_symbols_from)
        if failed_syms:
            # Filter universe to only failed symbols
            original_count = len(syms)
            syms = [(s, u) for s, u in syms if s in failed_syms]
            print(f"[RETRY] Attempt {args.retry_attempt}: Retrying {len(syms)} failed symbols from {original_count}")
        else:
            print(f"[INFO] No failed symbols found in {args.retry_symbols_from}")
    
    if args.quick:
        print("[QUICK MODE] ~40% faster: fewer candles + reduced retries")
    if syms:
        print(f"[INFO] First 10: {', '.join(s for s, u in syms[:10])}")
    
    if not syms:
        return
    
    # Adaptive configuration based on universe size
    print(f"\n[UNIVERSE] {args.universe.upper()} with {len(syms)} symbols")
    
    # Auto-adjust thread count if not explicitly set by user
    if len(syms) >= 100 and args.num_threads == 6:
        adaptive_threads = min(12, 6 + (len(syms) - 50) // 15)  # Scale up for large universes
        print(f"[AUTO-TUNED] Large universe ({len(syms)} stocks) - increasing threads: 6 → {adaptive_threads}")
        args.num_threads = adaptive_threads
    
    # Auto-recommend optimizations for large universes
    if len(syms) >= 100:
        print(f"[TIP] For faster Nifty50+ screening: --skip-news --num-threads {min(12, args.num_threads)} --quick")
    
    # Initialize wait strategy for API rate limiting with universe-aware config
    use_wait_strategy = not args.no_wait_strategy
    if use_wait_strategy:
        # Optimized batch sizes by universe (faster for larger sets)
        batch_config = {
            'nifty500': {'batch_size': 60, 'inter_batch_delay': 1.0, 'request_delay': 0.15},
            'nifty200': {'batch_size': 40, 'inter_batch_delay': 1.0, 'request_delay': 0.15},
            'nifty100': {'batch_size': 25, 'inter_batch_delay': 1.0, 'request_delay': 0.15},
            'nifty': {'batch_size': 20, 'inter_batch_delay': 1.0, 'request_delay': 0.15},
            'default': {'batch_size': 8, 'inter_batch_delay': 1.5, 'request_delay': 0.2}
        }
        config = batch_config.get(args.universe, batch_config['default'])
        batch_handler = BatchRequestHandler(
            batch_size=config['batch_size'],
            inter_batch_delay=config['inter_batch_delay'],
            request_delay=config['request_delay']
        )
        num_batches = (len(syms) + config['batch_size'] - 1) // config['batch_size']
        print(f"[BATCHING] Batch size: {config['batch_size']} | Threads: {args.num_threads} | Batches: {num_batches} | Est. time: 10-15 min")
        print(f"[WAIT STRATEGY] Enabled - Intelligent API rate limiting active")
    else:
        batch_handler = None
        print("[WAIT STRATEGY] Disabled")
    
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
        force_breeze=args.force_breeze,
        quick_mode=args.quick,
        intraday_weight=args.intraday_w,
        swing_weight=args.swing_w,
        longterm_weight=args.longterm_w
    )
    
    # Compute scores - choose execution method
    # 6-thread by default (unless disabled with --no-6thread)
    use_6thread = not args.no_6thread and len(syms) > 50
    
    if use_6thread:
        # Use optimized multi-thread execution
        print(f"\n[MODE] {args.num_threads}-THREAD EXECUTION (optimized, 2:1 yF:Breeze ratio)")
        results, execution_time = run_with_6thread(syms, engine, args.num_threads)
    else:
        # Use traditional ThreadPoolExecutor
        if not args.no_6thread:
            print("\n[INFO] Universe too small (<50 stocks), using standard parallel")
        else:
            print("\n[INFO] 6-thread mode disabled, using standard parallel")
        
        results = []
        with ThreadPoolExecutor(max_workers=max(1, args.num_threads)) as exe:
            futures = {}
            for sym, u in syms:
                futures[exe.submit(engine.compute_score, sym)] = (sym, u)
            
            # Optional: Add wait strategy delays between batch submissions
            processed_count = 0
            
            for fut in as_completed(futures):
                sym, u = futures[fut]
                try:
                    # Apply wait strategy batch timing if enabled
                    if batch_handler is not None:
                        processed_count += 1
                        if processed_count % batch_handler.batch_size == 0:
                            import time
                            jitter = __import__('random').uniform(0, batch_handler.inter_batch_delay * 0.2)
                            time.sleep(batch_handler.inter_batch_delay + jitter)
                    
                    data = fut.result()
                    if data:
                        data['index'] = u
                        
                        # ==================== INTEGRATE HYBRID S/R + RISK ZONES ====================
                        # Get historical data for support/resistance detection if score exists
                        if data.get('final_score') is not None and data.get('status') == 'OK':
                            try:
                                from data_providers import get_intraday_candles_for
                                hist_candles, _ = get_intraday_candles_for(
                                    sym, '1day', 200, 
                                    use_yf=args.use_yf, force_yf=args.force_yf, force_breeze=args.force_breeze
                                )
                                if hist_candles is not None and len(hist_candles) > 20:
                                    # Convert list of dicts to DataFrame with proper types
                                    hist_df = pd.DataFrame(hist_candles)
                                    # Ensure numeric columns are float type
                                    for col in ['open', 'high', 'low', 'close', 'volume']:
                                        if col in hist_df.columns:
                                            hist_df[col] = pd.to_numeric(hist_df[col], errors='coerce')
                                    atr_val = data.get('atr', 0) or 0
                                    data = integrate_with_screener(data, hist_df, atr_val)
                                else:
                                    # Set default risk level if S/R integration not possible
                                    data['risk_level'] = 'LOW'
                                    data['risk_reason'] = 'Insufficient historical data for risk analysis'
                            except Exception as e:
                                # Set default risk level if S/R integration fails
                                data['risk_level'] = 'LOW'
                                data['risk_reason'] = f'Risk analysis failed: {str(e)}'
                        else:
                            # Set default risk level for failed scoring
                            data['risk_level'] = 'LOW'
                            data['risk_reason'] = 'Scoring failed or incomplete'
                        # ============================================================================
                        
                        results.append(data)
                        if data.get('status') == 'OK':
                            print(f"Processing {sym}... done (score={data['final_score']:.2f})")
                        else:
                            print(f"Processing {sym}... skipped (no data)")
                except Exception as e:
                    import traceback
                    print(f"{sym}: error -> {e}")
                    traceback.print_exc()
                    results.append({"symbol": sym, "status": "ERROR", "index": u})
    
    # Continue with enrichment regardless of execution method
    # Enrich with sector info (using modular sector_mapper)
    for r in results:
        r['sector'] = get_sector(r.get('symbol', ''))
    
    # Add robustness metrics to all results
    for r in results:
        # Robustness score: derived from confidence and pattern quality
        confidence = r.get('confidence', 0) or 0
        pattern_conf = r.get('pattern_confidence', 0) or 0
        
        # Robustness = 70% confidence + 30% pattern confidence
        r['robustness_score'] = (confidence * 0.7) + (pattern_conf * 0.3)
        
        # Robustness momentum: derived from trend and context momentum
        final_score = r.get('final_score', 0) or 0
        context_momentum = r.get('context_momentum', 0) or 0
        
        # Robustness momentum = average of direction strength and context
        r['robustness_momentum'] = (final_score / 2.0) if final_score != 0 else context_momentum
        
        # Master score: 6-dimensional composite
        # 25% Confidence, 25% Technical, 20% Robustness, 15% Context, 10% Momentum, 5% News
        confidence_norm = confidence  # Already 0-100
        technical_norm = (final_score + 1) * 50  # Convert -1 to +1 → 0-100
        robustness_norm = r['robustness_score']  # Already 0-100
        context_score = r.get('context_score', 0) or 0
        context_norm = (context_score / 5.0) * 100  # Convert 0-5 → 0-100
        momentum_norm = ((context_momentum + 1) / 2) * 100  # Convert -1 to +1 → 0-100
        news_sentiment = r.get('news_sentiment_score', 0) or 0
        news_norm = ((news_sentiment + 1) / 2) * 100  # Convert -1 to +1 → 0-100
        
        # Calculate master score
        master_score = (
            (confidence_norm * 0.25) +
            (technical_norm * 0.25) +
            (robustness_norm * 0.20) +
            (context_norm * 0.15) +
            (momentum_norm * 0.10) +
            (news_norm * 0.05)
        )
        
        r['master_score'] = round(master_score, 1)
        
        # Generate master score tooltip
        tooltip = (
            f"Master Score: {r['master_score']:.1f}/100\n"
            f"━━━━━━━━━━━━━━━━━━━━━━\n"
            f"Confidence (25%): {confidence_norm:.0f}/100\n"
            f"Technical (25%): {technical_norm:.0f}/100\n"
            f"Robustness (20%): {robustness_norm:.0f}/100\n"
            f"Context (15%): {context_norm:.0f}/100\n"
            f"Momentum (10%): {momentum_norm:.0f}/100\n"
            f"News (5%): {news_norm:.0f}/100\n"
            f"━━━━━━━━━━━━━━━━━━━━━━\n"
            f"Rating: {'STRONG ✓✓' if r['master_score'] >= 80 else 'GOOD ✓' if r['master_score'] >= 70 else 'FAIR ⚠' if r['master_score'] >= 60 else 'WEAK ✗'}"
        )
        r['master_score_tooltip'] = tooltip
    
    # Add option selling viability score (0-1 scale, independent field)
    for r in results:
        r['option_selling_score'] = calculate_option_selling_score_0_1(r)
    
    # Add theta decay score (0-1 scale, independent field)
    # Based on 4 continuous sub-scores with hard vetoes for trends and patterns
    for r in results:
        r['theta_decay_score'] = calculate_theta_decay_score(r)
    
    # Add comprehensive option premium quality score (combines stock quality + theta + greeks)
    for r in results:
        r['option_premium_quality'] = calculate_option_premium_quality(r)

    # NOTE: context_score, context_momentum, and system_state are now computed in the engine
    # No need to recalculate them here - they are already in the results with full authority
    # Compute index bias and print actionable picks first
    idx_bias, idx_src = _compute_index_bias(engine, results=results)
    print_actionables(results, index_bias=idx_bias, conf_threshold=60.0, score_threshold=0.35, mode=args.mode)

    # Print and save full results
    print_results(results)
    
    # Print wait strategy statistics if enabled
    if batch_handler is not None:
        stats = batch_handler.stats()
        print(f"\n[WAIT STRATEGY STATS]")
        print(f"  Processed: {stats['processed']}")
        print(f"  Failed: {stats['failed']}")
        print(f"  Success Rate: {stats['success_rate']*100:.1f}%")
    
    # Always save CSV for downstream parsing
    csv_path = args.export if (args.export and str(args.export).lower().endswith('.csv')) else OUT_CSV
    save_csv(results, csv_path, args)
    
    # Merge with previous results if specified (cumulative reporting)
    if args.merge_with:
        final_csv = Path(csv_path).with_stem(f"{Path(csv_path).stem}_merged")
        merge_csv_results(args.merge_with, csv_path, str(final_csv))
        print(f"[OK] Merged results saved to {final_csv}")
        csv_path = str(final_csv)  # Use merged CSV for subsequent operations

    # Always save HTML (no flag needed - screener format)
    html_path = args.export if (args.export and str(args.export).lower().endswith('.html')) else str(Path(csv_path).with_suffix('.html'))
    
    # Save ORIGINAL HTML to root (PRIMARY)
    save_html(results, html_path, args)
    print(f"[OK] Original HTML saved to {html_path}")
    
    # Also save to reports folder for archival
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
    
    # Print final timing summary
    total_elapsed = time_module.time() - t_start
    print(f"\n" + "=" * 80)
    print(f"[COMPLETE] Total Execution Time: {total_elapsed:.1f}s ({total_elapsed/60:.2f}min)")
    print(f"[SUMMARY] {len(results)} stocks analyzed ({len(syms)} loaded)")
    print(f"[END] {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 80 + "\n")


if __name__ == '__main__':
    main()
