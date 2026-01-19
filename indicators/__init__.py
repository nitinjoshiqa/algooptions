"""Technical indicators module."""

def rsi(candles, period=14):
    """Calculate RSI (Relative Strength Index). Returns value 0-100."""
    if len(candles) < period + 1:
        return None
    closes = [float(c.get("close", 0)) for c in candles]
    gains = []
    losses = []
    for i in range(1, len(closes)):
        change = closes[i] - closes[i-1]
        if change > 0:
            gains.append(change)
            losses.append(0)
        else:
            gains.append(0)
            losses.append(abs(change))
    avg_gain = sum(gains[-period:]) / period
    avg_loss = sum(losses[-period:]) / period
    if avg_loss == 0:
        return 100 if avg_gain > 0 else 50
    rs = avg_gain / avg_loss
    return 100 - (100 / (1 + rs))


def ema(candles, period=9):
    """Calculate EMA (Exponential Moving Average)."""
    if len(candles) < period:
        return None
    closes = [float(c.get("close", 0)) for c in candles]
    multiplier = 2 / (period + 1)
    ema_val = sum(closes[:period]) / period
    for close in closes[period:]:
        ema_val = close * multiplier + ema_val * (1 - multiplier)
    return ema_val


def atr(candles, period=14):
    """Calculate ATR (Average True Range) for volatility normalization."""
    if len(candles) < period:
        return None
    tr_list = []
    for i, c in enumerate(candles):
        h = float(c.get("high", 0))
        l = float(c.get("low", 0))
        close_prev = float(candles[i-1].get("close", l)) if i > 0 else l
        tr = max(h - l, abs(h - close_prev), abs(l - close_prev))
        tr_list.append(tr)
    return sum(tr_list[-period:]) / period if tr_list else None


def vwap_proxy(candles, lookback_bars):
    """Calculate VWAP proxy using typical price."""
    total = 0
    count = 0
    for c in candles[-lookback_bars:]:
        try:
            typical = (float(c["high"]) + float(c["low"]) + float(c["close"])) / 3
            total += typical
            count += 1
        except Exception:
            continue
    return total / count if count else None


def opening_range_from_candles(candles, or_bars):
    """Extract opening range high/low from first N bars."""
    or_candles = candles[:or_bars]
    # Skip flat pre-market bars
    or_mov = [c for c in or_candles if float(c.get("high", 0)) != float(c.get("low", 0))]
    if or_mov:
        high = max(float(c["high"]) for c in or_mov)
        low = min(float(c["low"]) for c in or_mov)
    elif candles:
        high = max(float(c["high"]) for c in candles)
        low = min(float(c["low"]) for c in candles)
    else:
        high = low = None
    return high, low


def bollinger_bands(candles, period=20, std_dev=2):
    """Calculate Bollinger Bands. Returns (upper, middle, lower)."""
    if len(candles) < period:
        return None, None, None
    try:
        closes = [float(c.get("close", 0)) for c in candles[-period:]]
        sma = sum(closes) / period
        variance = sum((c - sma) ** 2 for c in closes) / period
        std = variance ** 0.5
        upper_band = sma + std_dev * std
        lower_band = sma - std_dev * std
        return upper_band, sma, lower_band
    except Exception:
        return None, None, None


def macd_line(candles):
    """Calculate MACD line (12-EMA - 26-EMA)."""
    ema12 = ema(candles, period=12)
    ema26 = ema(candles, period=26)
    if ema12 is None or ema26 is None:
        return None
    return ema12 - ema26
