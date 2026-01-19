"""Scoring strategies for technical indicators."""
from indicators import rsi, ema, atr, vwap_proxy, opening_range_from_candles, bollinger_bands, macd_line
from core.config import OPENING_RANGE_MINUTES, VWAP_LOOKBACK_MIN, TREND_CONFIRM_BARS


def rsi_score(rsi_val):
    """Map RSI to [-1, 1]: 30-70 positive, extremes negative."""
    if rsi_val is None:
        return 0
    try:
        r = float(rsi_val)
    except Exception:
        return 0
    if 30 <= r <= 70:
        return max(0.0, 1.0 - (abs(r - 50.0) / 20.0))
    elif r < 30:
        return -min(1.0, (30.0 - r) / 30.0)
    else:  # r > 70
        return -min(1.0, (r - 70.0) / 30.0)


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
    """Volume score with accumulation/distribution bias and weak-volume pattern support.

    Captures:
    - Accumulation: high volume + up move
    - Distribution: high volume + down move
    - Directional validation vs recent trend
    - Small boost for strong candle bodies even if volume slightly below average
    """
    if len(candles) < periods:
        return 0
    try:
        volumes = [int(c.get("volume", 0)) for c in candles]
        current_vol = volumes[-1]
        avg_vol = sum(volumes[-periods:]) / periods
        if avg_vol == 0:
            return 0
        
        vol_ratio = current_vol / avg_vol
        # Price direction on current bar
        current_close = float(candles[-1].get('close', 0))
        current_open = float(candles[-1].get('open', current_close))
        price_direction = 1 if current_close > current_open else -1
        body_size = abs(current_close - current_open)
        high = float(candles[-1].get('high', current_close))
        low = float(candles[-1].get('low', current_close))
        range_size = max(high - low, 1e-6)
        body_ratio = body_size / range_size  # >0.6 = strong body
        
        # Recent trend direction (last 5 bars)
        trend_direction = 0
        recent_closes = [float(c.get('close', 0)) for c in candles[-6:-1]]
        if len(recent_closes) >= 2:
            trend_direction = 1 if recent_closes[-1] > recent_closes[0] else -1
        
        # Base score from relative volume
        score = (vol_ratio - 1) / 0.5  # vol_ratio 1.5 -> +1, 0.5 -> -1
        
        # Accumulation / Distribution bias on high volume
        if vol_ratio >= 1.2:
            if price_direction > 0:
                score += 0.2  # Accumulation tilt
            else:
                score -= 0.2  # Distribution tilt
        
        # Counter-trend high volume penalty
        if trend_direction != 0 and price_direction != trend_direction and vol_ratio > 1.3:
            score *= 0.7
        
        # Weak volume but strong candle body: give small credit for decisive move
        if 0.7 <= vol_ratio < 1.0 and body_ratio >= 0.6:
            score += 0.1 * price_direction
        
        return max(-1, min(1, score))
    except Exception:
        return 0


def macd_score(candles):
    """MACD score: bearish if negative, bullish if positive."""
    macd_val = macd_line(candles)
    if macd_val is None:
        return 0
    if macd_val < 0:
        return max(-1, macd_val / 100)
    else:
        return min(1, macd_val / 100)


def bollinger_bands_score(candles, period=20, std_dev=2):
    """Bollinger Bands score: price near lower band = bearish, near upper = bullish."""
    if len(candles) < period:
        return 0
    try:
        upper, middle, lower = bollinger_bands(candles, period, std_dev)
        if upper is None or lower is None or upper == lower:
            return 0
        current = float(candles[-1].get("close", 0))
        normalized = (current - lower) / (upper - lower)
        return max(-1, min(1, (normalized - 0.5) * 2))
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
