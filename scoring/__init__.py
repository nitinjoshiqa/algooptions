"""Scoring strategies for technical indicators."""
from indicators import rsi, ema, atr, vwap_proxy, opening_range_from_candles, bollinger_bands, macd_line
from core.config import OPENING_RANGE_MINUTES, VWAP_LOOKBACK_MIN, TREND_CONFIRM_BARS


def rsi_score(rsi_val, rsi_prev=None):
    """
    IMPROVED: Direction-based RSI scoring with fuzzy logic.
    
    Business logic:
    - RSI RISING (momentum increasing) = BULLISH, regardless of level
    - RSI FALLING (momentum decreasing) = BEARISH, regardless of level
    - Extreme levels (30/70) amplify the signal, not reverse it
    - Fuzzy logic: smooth transitions instead of hard thresholds
    
    Fuzzy zones:
    - RSI 0-30: Rising = strong bullish, Falling = neutral
    - RSI 30-45: Rising = bullish, Falling = slight bearish  
    - RSI 45-55: Neutral zone (slight bias based on direction)
    - RSI 55-70: Rising = strong bullish, Falling = bearish
    - RSI 70-100: Rising = extreme bullish, Falling = strong bearish
    """
    if rsi_val is None:
        return 0
    try:
        r = float(rsi_val)
    except Exception:
        return 0
    
    # Handle case when previous RSI not available - use magnitude-only scoring
    if rsi_prev is None:
        # Fallback: use momentum indicator (distance from 50)
        # But don't penalize strength - high RSI in uptrend is GOOD
        momentum = (r - 50.0) / 50.0  # Ranges from -1 to +1
        # Apply fuzzy membership to dampen extreme claims
        if 30 < r < 70:
            # Normal zone: full signal
            return momentum
        else:
            # Extreme zone: amplify signal (not reverse it!)
            return momentum * 1.2 if abs(momentum) > 0.4 else momentum
    
    # Direction-based scoring (when previous RSI available)
    try:
        rsi_p = float(rsi_prev)
    except:
        rsi_p = 50  # Default to neutral if parse fails
    
    # Calculate RSI direction (momentum)
    rsi_change = r - rsi_p
    
    # Fuzzy membership functions for smooth transitions
    def triangle_fuzzy(x, peak, width):
        """Triangle fuzzy membership (smooth peak)"""
        if x < peak - width or x > peak + width:
            return 0
        if x <= peak:
            return (x - (peak - width)) / width
        return ((peak + width) - x) / width
    
    # Score components
    level_score = (r - 50.0) / 50.0  # -1 to +1 based on absolute level
    direction_score = min(1.0, max(-1.0, rsi_change / 5.0))  # Normalize change to -1 to +1
    
    # Fuzzy weighting based on RSI zone
    if r < 30:
        # Oversold zone: direction matters more
        # Rising from oversold = strong bullish
        # Falling further = extreme bearish (but this rarely happens)
        weight_direction = 0.7
        weight_level = 0.3
    elif 30 <= r < 45:
        # Weak zone: direction is important
        weight_direction = 0.6
        weight_level = 0.4
    elif 45 <= r <= 55:
        # Neutral zone: both matter equally
        weight_direction = 0.5
        weight_level = 0.5
    elif 55 < r <= 70:
        # Strong zone: direction is important
        weight_direction = 0.6
        weight_level = 0.4
    else:  # r > 70
        # Overbought zone: direction matters most
        # Rising above 70 = extremely bullish (continuation)
        # Falling from 70 = potential reversal (but less extreme)
        weight_direction = 0.7
        weight_level = 0.3
    
    # Combine with fuzzy logic
    final_score = (direction_score * weight_direction) + (level_score * weight_level)
    
    # Apply sigmoid-like dampening to avoid extreme scores
    # This creates smooth transitions instead of hard cliffs
    return max(-1.0, min(1.0, final_score * 0.95))


def ema_score(candles):
    """EMA crossover score: short EMA (9) vs long EMA (21)."""
    short_ema = ema(candles, period=9)
    long_ema = ema(candles, period=21)
    if short_ema is None or long_ema is None:
        return 0
    if short_ema < long_ema:
        diff = long_ema - short_ema
        pct = diff / long_ema if long_ema != 0 else 0
        return max(-1, -pct / 0.05)
    else:
        diff = short_ema - long_ema
        pct = diff / long_ema if long_ema != 0 else 0
        return min(1, pct / 0.05)


def opening_range_score(price, or_high, or_low):
    """Score based on price position within opening range."""
    if or_high is None or or_low is None or or_high == or_low:
        return 0
    range_size = or_high - or_low
    midpoint = (or_high + or_low) / 2
    distance = price - midpoint
    normalized = distance / (range_size / 2)
    return max(-1, min(1, normalized))


def vwap_score(price, vwap):
    """Score based on price distance from VWAP."""
    if vwap is None or vwap == 0:
        return 0
    percent_diff = (price - vwap) / vwap
    score = percent_diff / 0.05
    return max(-1, min(1, score))


def structure_score(candles):
    """Score based on recent price structure/trend."""
    if len(candles) < TREND_CONFIRM_BARS:
        return 0
    recent = candles[-TREND_CONFIRM_BARS:]
    try:
        closes = [float(c["close"]) for c in recent]
    except Exception:
        return 0
    close_change = closes[-1] - closes[0]
    close_avg = sum(closes) / len(closes)
    if close_avg == 0:
        return 0
    score = (close_change / close_avg) / 0.02
    return max(-1, min(1, score))


def volume_score(candles, periods=20):
    """
    IMPROVED: Volume score with softer penalties.
    
    Goal: Validate trend but don't penalize strongly for low volume
    - High volume + direction = strong confirmation (+0.5 to +1.0)
    - Low volume + direction = weak but not invalid (-0.1 to +0.3)
    - Counter-trend volume = moderate penalty (-0.3 to 0)
    
    Don't let volume alone kill a good technical setup!
    """
    if len(candles) < periods:
        return 0.0  # Unknown volume, assume neutral
    try:
        volumes = [float(c.get("volume", 0)) for c in candles]
        current_vol = volumes[-1]
        avg_vol = sum(volumes[-periods:]) / periods
        if avg_vol == 0:
            return 0.0
        
        vol_ratio = current_vol / avg_vol
        
        # Price direction on current bar
        current_close = float(candles[-1].get('close', 0))
        current_open = float(candles[-1].get('open', current_close))
        price_direction = 1 if current_close > current_open else -1
        
        # Recent trend direction (last 3-5 bars)
        trend_direction = 0
        recent_closes = [float(c.get('close', 0)) for c in candles[-6:-1]]
        if len(recent_closes) >= 2:
            trend_direction = 1 if recent_closes[-1] > recent_closes[0] else -1
        
        # FUZZY LOGIC: Smooth volume scoring
        # Base: volume compared to average
        if vol_ratio > 1.5:
            # High volume (50% above average)
            if price_direction == trend_direction or trend_direction == 0:
                score = 0.6 + (min(vol_ratio - 1.5, 1.0) / 2.0) * 0.4  # +0.6 to +1.0
            else:
                # Counter-trend with high volume = distribution/liquidation
                score = 0.1  # Mild concern but not fatal
        elif vol_ratio > 1.2:
            # Above-average volume
            score = 0.3 + (0.2 * (vol_ratio - 1.2) / 0.3)  # +0.3 to +0.5
            if price_direction != trend_direction and trend_direction != 0:
                score -= 0.15  # Slight penalty for divergence
        elif vol_ratio > 0.8:
            # Normal/slightly below average - still valid
            if price_direction == trend_direction:
                score = 0.1  # Slightly bullish (continues existing trend)
            elif trend_direction == 0:
                score = 0.0  # Neutral, no prior trend
            else:
                score = -0.05  # Weak divergence penalty
        else:
            # Low volume (<80% of average)
            # But don't penalize too hard - maybe just low liquidity day
            if price_direction == trend_direction:
                score = -0.2  # Weak confirmation
            else:
                score = -0.25  # Weak divergence
        
        return max(-1.0, min(1.0, score))
    except Exception:
        return 0.0


def macd_score(candles):
    """MACD score: bearish if negative, bullish if positive.
    
    FIXED: Changed divisor from 100 to 5 to make MACD contribution meaningful.
    Typical MACD values are ±5, so dividing by 5 gives ±1.0 score range.
    """
    macd_val = macd_line(candles)
    if macd_val is None:
        return 0
    # FIXED: Divide by 5 instead of 100 (MACD ±5 -> score ±1.0)
    if macd_val < 0:
        return max(-1, macd_val / 5)
    else:
        return min(1, macd_val / 5)


def bollinger_bands_score(candles, period=20, std_dev=2):
    """Bollinger Bands score: price near lower band = bullish (oversold), near upper = bearish (overbought).
    
    FIXED: Inverted logic - lower band now returns positive (buy signal), upper band negative (sell signal)
    """
    if len(candles) < period:
        return 0
    try:
        upper, middle, lower = bollinger_bands(candles, period, std_dev)
        if upper is None or lower is None or upper == lower:
            return 0
        current = float(candles[-1].get("close", 0))
        normalized = (current - lower) / (upper - lower)
        # FIXED: Flip the sign - lower band (normalized=0) = +1 (bullish), upper band (normalized=1) = -1 (bearish)
        return max(-1, min(1, (0.5 - normalized) * 2))
    except Exception:
        return 0


def calculate_sl_target(price, atr_val, direction='bearish', atr_multiplier=2):
    """Calculate SL and target based on ATR."""
    if atr_val is None or atr_val <= 0:
        return None, None
    
    if direction == 'bearish':
        target = price - (atr_multiplier * atr_val)
        sl = price + atr_val
    else:  # bullish
        target = price + (atr_multiplier * atr_val)
        sl = price - atr_val
    
    return sl, target


def volume_acceleration_score(candles, lookback=20):
    """
    Detect volume building BEFORE price confirmation.
    
    Score range: [-1, 1]
    - Positive: Volume accelerating above average (institutional entry signal)
    - Negative: Volume declining (weak commitment)
    
    This catches institutional entry 1-2 candles BEFORE retail algos notice the price move.
    """
    if len(candles) < lookback + 2:
        return 0
    
    try:
        current_vol = float(candles[-1].get('volume', 0))
        previous_vol = float(candles[-2].get('volume', 0)) if len(candles) >= 2 else 0
        
        # Average volume over lookback period (excluding current)
        recent_vols = [float(c.get('volume', 0)) for c in candles[-lookback:-1]]
        avg_vol = sum(recent_vols) / len(recent_vols) if recent_vols else 1
        
        if avg_vol == 0:
            return 0
        
        # Score: how much above average is current volume?
        vol_acceleration = (current_vol - avg_vol) / avg_vol
        score = min(1.0, vol_acceleration / 0.5)  # 50% above avg = +1
        
        # Bonus: if volume was also above avg previous candle (building trend)
        vol_trend_bonus = 0
        if previous_vol > avg_vol:
            vol_trend_bonus = 0.2  # Consistent building
        
        final_score = max(0, min(1.0, score + vol_trend_bonus))
        
        # Penalty: if volume declining despite price move
        if len(candles) >= 3:
            closes = [float(c.get('close', 0)) for c in candles[-3:]]
            has_price_move = abs(closes[-1] - closes[0]) > 0
            vol_declining = current_vol < previous_vol < avg_vol
            
            if has_price_move and vol_declining:
                final_score *= 0.7  # Weak volume on price move
        
        return final_score
    except Exception:
        return 0


def vwap_crossover_score(candles, current_price):
    """
    Detect VWAP crossovers as early reversal/directional signals.
    
    Score range: [-1, 1]
    - +1.0: Bullish crossover (price crosses above VWAP) = smart money buying
    - -1.0: Bearish crossover (price crosses below VWAP) = smart money selling
    - 0.0-0.5: Distance from VWAP (price away from average cost basis)
    
    VWAP represents average cost basis of all buyers. Crossing it = shift in positioning.
    """
    if len(candles) < 21:
        return 0
    
    try:
        # Get VWAP for last 20 candles
        vwap_current = vwap_proxy(candles[-20:])
        vwap_previous = vwap_proxy(candles[-21:-1]) if len(candles) >= 21 else None
        
        if vwap_current is None or vwap_current == 0:
            return 0
        
        current_price = float(current_price) if current_price else float(candles[-1].get('close', 0))
        
        # CROSSOVER DETECTION
        if vwap_previous is not None and vwap_previous != 0:
            prev_close = float(candles[-2].get('close', 0)) if len(candles) >= 2 else current_price
            
            # Bullish crossover: price was below VWAP, now above
            bullish_cross = (prev_close < vwap_previous) and (current_price > vwap_current)
            # Bearish crossover: price was above VWAP, now below
            bearish_cross = (prev_close > vwap_previous) and (current_price < vwap_current)
            
            if bullish_cross:
                return 1.0  # Strong bullish signal
            elif bearish_cross:
                return -1.0  # Strong bearish signal
        
        # NO CROSSOVER: Score distance from VWAP
        pct_from_vwap = (current_price - vwap_current) / vwap_current
        distance_score = min(1.0, max(-1.0, pct_from_vwap / 0.03))  # 3% = ±1.0
        
        return distance_score
    except Exception:
        return 0


def opening_range_breakout_score(intraday_candles, current_price):
    """
    Detect if price breaks out of opening range.
    
    Score range: [-1, 1]
    - +1.0: Breakout above opening range (bullish, day's high likely established)
    - -1.0: Breakout below opening range (bearish, day's low likely set)
    - 0.0: Price in range (consolidating)
    
    Opening range (first 30-60 min) sets daily range. Breakout = institutional participation confirmed.
    Retail algos react AFTER breakout; catching it early means catching before retail piles in.
    """
    if not intraday_candles or len(intraday_candles) < 2:
        return 0
    
    try:
        # Get opening range: first 30-60 min of candles (or 3-4 candles if 5/15min)
        or_period = 4  # Usually 4-6 candles = 20-30 minutes
        opening_range_candles = intraday_candles[:min(or_period, len(intraday_candles))]
        
        if len(opening_range_candles) < 2:
            return 0
        
        or_high = max(float(c.get('high', 0)) for c in opening_range_candles)
        or_low = min(float(c.get('low', 0)) for c in opening_range_candles)
        or_range = or_high - or_low
        
        if or_range == 0:
            return 0
        
        current_price = float(current_price) if current_price else float(intraday_candles[-1].get('close', 0))
        
        # Check breakout status
        above_or_high = current_price > or_high
        below_or_low = current_price < or_low
        
        if above_or_high:
            # Bullish breakout: how far above?
            breakout_pct = (current_price - or_high) / or_range
            return min(1.0, 0.8 + breakout_pct * 0.2)  # Start at 0.8, up to 1.0
        
        elif below_or_low:
            # Bearish breakout: how far below?
            breakout_pct = (or_low - current_price) / or_range
            return max(-1.0, -0.8 - breakout_pct * 0.2)  # Start at -0.8, down to -1.0
        
        else:
            # In-range: score based on position
            position_in_range = (current_price - or_low) / or_range
            # Center = 0, high side = 0.3, low side = -0.3
            return (position_in_range - 0.5) * 0.6
    
    except Exception:
        return 0
