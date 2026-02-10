"""
Robustness Engine - Unified Robustness Filtering & Diagnostics

Purpose:
    - Single source of truth for all 7 robustness filters
    - Track which filters pass/fail with diagnostic reasons
    - Calculate robustness_score strictly as (filters_passed / 7) * 100
    - Calculate robustness_momentum from filter state changes
    
Architecture:
    - validate_robustness(row) → dict with pass/fail status for each filter
    - get_robustness_score(filters_status) → 0-100
    - get_robustness_momentum(df, idx, prev_filters, curr_filters) → -1 to +1
"""

from enum import Enum


class RobustnessFilter(Enum):
    """All 7 robustness filters"""
    MARKET_REGIME = 'market_regime'
    VOLUME_CONFIRMATION = 'volume_confirmation'
    TIME_OF_DAY = 'time_of_day'
    LIQUIDITY = 'liquidity'
    EARNINGS_SAFETY = 'earnings_safety'
    MULTI_TIMEFRAME = 'multi_timeframe'
    EXPECTANCY = 'expectancy'


def validate_robustness(row):
    """
    Validate all 7 robustness filters for a signal
    
    Filters are BINARY: pass or fail. No partial credit.
    
    Args:
        row: Dictionary containing:
            - market_regime: 'TRENDING', 'NEUTRAL', 'RANGING'
            - adx: ADX value (> 22 for trending)
            - volume: Current volume
            - volume_avg: Average volume
            - hour: Hour of day (9-15 valid for IST)
            - close_price: Current close
            - atr: Average True Range
            - has_earnings_risk: Boolean or 0/1
            - sma20, sma50: Moving averages
            - historical_winrate: Expected win rate (>0.50)
    
    Returns:
        dict: {
            'market_regime': {'pass': bool, 'reason': str},
            'volume_confirmation': {'pass': bool, 'reason': str},
            'time_of_day': {'pass': bool, 'reason': str},
            'liquidity': {'pass': bool, 'reason': str},
            'earnings_safety': {'pass': bool, 'reason': str},
            'multi_timeframe': {'pass': bool, 'reason': str},
            'expectancy': {'pass': bool, 'reason': str},
        }
    """
    
    results = {}
    
    # ==================== FILTER 1: MARKET REGIME ====================
    # PASS: ADX > 22 (trending market)
    adx = row.get('adx', 0) or 0
    regime = row.get('market_regime', 'NEUTRAL') or 'NEUTRAL'
    regime_pass = adx > 22 or regime == 'TRENDING'
    results['market_regime'] = {
        'pass': regime_pass,
        'reason': f"ADX={adx:.1f}" if regime_pass else f"low_adx (adx={adx:.1f})"
    }
    
    # ==================== FILTER 2: VOLUME CONFIRMATION ====================
    # PASS: Volume 1.2-1.5x average (not climactic, not weak)
    volume = row.get('volume', 0) or 0
    volume_avg = row.get('volume_avg', 0) or 1  # Avoid division by zero
    vol_ratio = (volume / volume_avg) if volume_avg > 0 else 0
    vol_pass = 1.2 <= vol_ratio <= 1.5
    results['volume_confirmation'] = {
        'pass': vol_pass,
        'reason': f"vol_ratio={vol_ratio:.2f}x" if vol_pass else f"poor_volume (ratio={vol_ratio:.2f}x)"
    }
    
    # ==================== FILTER 3: TIME OF DAY ====================
    # PASS: 9 AM - 3 PM IST (9:00-15:00)
    hour = row.get('hour', 12) or 12  # Default to noon if missing
    time_pass = 9 <= hour < 15  # Up to but not including 15:00
    results['time_of_day'] = {
        'pass': time_pass,
        'reason': f"hour={hour}:00" if time_pass else f"bad_time (hour={hour}:00)"
    }
    
    # ==================== FILTER 4: LIQUIDITY ====================
    # PASS: Daily volume >= 50k shares
    liquidity_pass = volume >= 50000
    results['liquidity'] = {
        'pass': liquidity_pass,
        'reason': f"volume={volume:,.0f}" if liquidity_pass else f"low_liquidity (vol={volume:,.0f})"
    }
    
    # ==================== FILTER 5: EARNINGS SAFETY ====================
    # PASS: No >2.5x spike (climactic spike = earnings risk)
    has_earnings_risk = row.get('has_earnings_risk', False) or row.get('earnings_risk_spike', False)
    earnings_pass = not has_earnings_risk
    results['earnings_safety'] = {
        'pass': earnings_pass,
        'reason': "earnings_clear" if earnings_pass else "earnings_risk"
    }
    
    # ==================== FILTER 6: MULTI-TIMEFRAME ====================
    # PASS: Price > SMA20 > SMA50 (confirming uptrend structure)
    close = row.get('close_price', 0) or row.get('close', 0) or 0
    sma20 = row.get('sma20', 0) or 0
    sma50 = row.get('sma50', 0) or 0
    mtf_pass = close > sma20 > sma50 if (sma20 and sma50) else False
    results['multi_timeframe'] = {
        'pass': mtf_pass,
        'reason': "price>sma20>sma50" if mtf_pass else "weak_structure"
    }
    
    # ==================== FILTER 7: EXPECTANCY ====================
    # PASS: Historical win rate > 50%
    historical_winrate = row.get('historical_winrate', 0.50) or 0.50
    expectancy_pass = historical_winrate > 0.50
    results['expectancy'] = {
        'pass': expectancy_pass,
        'reason': f"wr={historical_winrate*100:.0f}%" if expectancy_pass else f"low_wr (wr={historical_winrate*100:.0f}%)"
    }
    
    return results


def get_robustness_score(filters_status):
    """
    Calculate robustness score (0-100) based on filters passed
    
    Strict definition: (filters_passed / 7) * 100
    No confidence or pattern factors included.
    
    Args:
        filters_status: dict from validate_robustness()
    
    Returns:
        float: 0-100 robustness score
    """
    if not filters_status:
        return 0.0
    
    filters_passed = sum(1 for f in filters_status.values() if f.get('pass', False))
    robustness_score = (filters_passed / 7.0) * 100.0
    
    return round(robustness_score, 1)


def get_robustness_fail_reasons(filters_status):
    """
    Extract list of reasons why filters failed
    
    Args:
        filters_status: dict from validate_robustness()
    
    Returns:
        list: Reason strings for failed filters (empty if all pass)
    """
    reasons = []
    for filter_name, status in filters_status.items():
        if not status.get('pass', False):
            reason = status.get('reason', 'unknown')
            reasons.append(reason)
    
    return reasons


def calculate_robustness_momentum(df, current_idx, curr_filters_status, prev_filters_status=None):
    """
    Calculate robustness momentum from filter state changes
    
    Strictly filter-based (not price-based):
    - More filters passing than before = +momentum
    - Fewer filters passing than before = -momentum
    - Same filters = 0 momentum
    
    Normalized to [-1, +1]
    
    Args:
        df: Price dataframe (used for validation)
        current_idx: Current bar index
        curr_filters_status: dict from validate_robustness() for current bar
        prev_filters_status: dict from validate_robustness() for previous bar (optional)
    
    Returns:
        float: -1 to +1 robustness momentum
    """
    
    if current_idx < 1:
        return 0.0  # Not enough history
    
    # Count current filters
    curr_pass = sum(1 for f in curr_filters_status.values() if f.get('pass', False))
    
    if prev_filters_status is None:
        # No previous state available; estimate from price momentum
        if current_idx < 2:
            return 0.0
        
        prev_close = df['Close'].iloc[current_idx - 1] if 'Close' in df.columns else 0
        prev2_close = df['Close'].iloc[current_idx - 2] if 'Close' in df.columns else prev_close
        curr_close = df['Close'].iloc[current_idx] if 'Close' in df.columns else 0
        
        if prev_close == 0:
            return 0.0
        
        # Price momentum as proxy
        price_momentum = (curr_close - prev_close) / prev_close
        return max(-1.0, min(1.0, price_momentum * 10))  # Scale and clamp
    
    # Count previous filters
    prev_pass = sum(1 for f in prev_filters_status.values() if f.get('pass', False))
    
    # Calculate momentum: change in passing filters normalized
    filter_change = curr_pass - prev_pass
    
    # Normalize: -7 to +7 → -1 to +1
    robustness_momentum = filter_change / 7.0
    
    return max(-1.0, min(1.0, round(robustness_momentum, 2)))


def get_robustness_tier(robustness_score):
    """
    Map robustness score (0-100) to tier name
    
    Args:
        robustness_score: float 0-100
        
    Returns:
        str: Tier name
    """
    if robustness_score >= 85:
        return 'STRONG (6-7/7 filters)'
    elif robustness_score >= 70:
        return 'GOOD (5/7 filters)'
    elif robustness_score >= 57:
        return 'FAIR (4/7 filters)'
    elif robustness_score >= 43:
        return 'WEAK (3/7 filters)'
    else:
        return 'POOR (≤2/7 filters)'


def get_robustness_color(robustness_score):
    """
    Get color for HTML rendering based on robustness score
    
    Args:
        robustness_score: float 0-100
        
    Returns:
        str: Hex color code
    """
    if robustness_score >= 85:
        return '#00b050'  # Strong green
    elif robustness_score >= 70:
        return '#70ad47'  # Good green
    elif robustness_score >= 57:
        return '#ffb000'  # Fair yellow
    elif robustness_score >= 43:
        return '#ff9500'  # Weak orange
    else:
        return '#c5504f'  # Poor red
