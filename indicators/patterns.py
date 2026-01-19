"""Chart pattern detection module with multi-timeframe analysis."""


def detect_double_top(candles, lookback=20):
    """Detect double top pattern (bearish reversal)."""
    if len(candles) < lookback:
        return None, 0
    
    recent = candles[-lookback:]
    highs = [c['high'] for c in recent]
    
    # Find two significant peaks
    max_idx = highs.index(max(highs))
    if max_idx < 5 or max_idx >= len(highs) - 5:
        return None, 0
    
    # Look for second peak
    second_peak = max(highs[max_idx+1:])
    if abs(second_peak - highs[max_idx]) / highs[max_idx] < 0.01:  # Within 1%
        valley = min(highs[:max_idx+1])
        confidence = min(0.8, 0.5 + (0.3 * (1 - abs(second_peak - highs[max_idx]) / highs[max_idx] * 100)))
        return 'Double Top', confidence
    
    return None, 0


def detect_double_bottom(candles, lookback=20):
    """Detect double bottom pattern (bullish reversal)."""
    if len(candles) < lookback:
        return None, 0
    
    recent = candles[-lookback:]
    lows = [c['low'] for c in recent]
    
    # Find two significant troughs
    min_idx = lows.index(min(lows))
    if min_idx < 5 or min_idx >= len(lows) - 5:
        return None, 0
    
    # Look for second trough
    second_trough = min(lows[min_idx+1:])
    if abs(second_trough - lows[min_idx]) / lows[min_idx] < 0.01:  # Within 1%
        confidence = min(0.8, 0.5 + (0.3 * (1 - abs(second_trough - lows[min_idx]) / lows[min_idx] * 100)))
        return 'Double Bottom', confidence
    
    return None, 0


def detect_head_shoulders(candles, lookback=20):
    """Detect head and shoulders pattern (bearish reversal)."""
    if len(candles) < lookback:
        return None, 0
    
    recent = candles[-lookback:]
    highs = [c['high'] for c in recent]
    
    if len(highs) < 5:
        return None, 0
    
    # Look for 3 peaks: left shoulder < head > right shoulder
    for i in range(1, len(highs) - 2):
        left = highs[i]
        head = highs[i+1] if i+1 < len(highs) else 0
        right = highs[i+2] if i+2 < len(highs) else 0
        
        if head > left and head > right and left > 0 and right > 0:
            shoulder_sim = abs(left - right) / left
            if shoulder_sim < 0.05 and head > left * 1.03:  # Similar shoulders, higher head
                confidence = min(0.85, 0.55 + (0.3 * (1 - shoulder_sim * 100)))
                return 'Head & Shoulders', confidence
    
    return None, 0


def detect_inverted_head_shoulders(candles, lookback=20):
    """Detect inverted head and shoulders (bullish reversal)."""
    if len(candles) < lookback:
        return None, 0
    
    recent = candles[-lookback:]
    lows = [c['low'] for c in recent]
    
    if len(lows) < 5:
        return None, 0
    
    # Look for 3 troughs: left shoulder > head < right shoulder
    for i in range(1, len(lows) - 2):
        left = lows[i]
        head = lows[i+1] if i+1 < len(lows) else 999999
        right = lows[i+2] if i+2 < len(lows) else 999999
        
        if head < left and head < right and left > 0 and right > 0:
            shoulder_sim = abs(left - right) / left
            if shoulder_sim < 0.05 and head < left * 0.97:  # Similar shoulders, lower head
                confidence = min(0.85, 0.55 + (0.3 * (1 - shoulder_sim * 100)))
                return 'Inverted H&S', confidence
    
    return None, 0


def detect_descending_triangle(candles, lookback=20):
    """Detect descending triangle (bearish continuation)."""
    if len(candles) < lookback:
        return None, 0
    
    recent = candles[-lookback:]
    highs = [c['high'] for c in recent]
    lows = [c['low'] for c in recent]
    
    if len(highs) < 6:
        return None, 0
    
    # Check last 6-8 candles for pattern
    h_check = highs[-8:]
    l_check = lows[-8:]
    
    # Highs should be declining (at least 2-3 lower)
    declining = sum(1 for i in range(len(h_check)-1) if h_check[i+1] < h_check[i])
    if declining < 2:
        return None, 0
    
    # Lows should be relatively stable (support level)
    lows_range = max(l_check) - min(l_check)
    lows_stable = lows_range < (min(l_check) * 0.025)  # Within 2.5%
    
    if lows_stable:
        # Check that current low is near support
        if lows[-1] <= (min(l_check) * 1.02):
            confidence = 0.65
            return 'Descending Triangle', confidence
    
    return None, 0


def detect_ascending_triangle(candles, lookback=20):
    """Detect ascending triangle (bullish continuation)."""
    if len(candles) < lookback:
        return None, 0
    
    recent = candles[-lookback:]
    highs = [c['high'] for c in recent]
    lows = [c['low'] for c in recent]
    
    if len(lows) < 6:
        return None, 0
    
    # Check last 6-8 candles for pattern
    h_check = highs[-8:]
    l_check = lows[-8:]
    
    # Lows should be rising (at least 2-3 higher)
    rising = sum(1 for i in range(len(l_check)-1) if l_check[i+1] > l_check[i])
    if rising < 2:
        return None, 0
    
    # Highs should be relatively stable (resistance level)
    highs_range = max(h_check) - min(h_check)
    highs_stable = highs_range < (max(h_check) * 0.025)  # Within 2.5%
    
    if highs_stable:
        # Check that current high is near resistance
        if highs[-1] >= (max(h_check) * 0.98):
            confidence = 0.65
            return 'Ascending Triangle', confidence
    
    return None, 0


def detect_rising_wedge(candles, lookback=20):
    """Detect rising wedge (bearish reversal)."""
    if len(candles) < lookback:
        return None, 0
    
    recent = candles[-lookback:]
    highs = [c['high'] for c in recent]
    lows = [c['low'] for c in recent]
    
    # Both highs and lows rising, but highs rising faster (wedge shape)
    if len(highs) < 5 or len(lows) < 5:
        return None, 0
    
    # Check recent trend
    high_trend = (highs[-1] - highs[-5]) / highs[-5] if highs[-5] > 0 else 0
    low_trend = (lows[-1] - lows[-5]) / lows[-5] if lows[-5] > 0 else 0
    
    # Rising wedge: both up, but high_trend > low_trend (widening range)
    if high_trend > low_trend and high_trend > 0.02:  # At least 2% up
        # Check if range is expanding
        range_5 = highs[-5] - lows[-5]
        range_1 = highs[-1] - lows[-1]
        if range_1 > range_5:
            confidence = 0.70
            return 'Rising Wedge', confidence
    
    return None, 0


def detect_falling_wedge(candles, lookback=20):
    """Detect falling wedge (bullish reversal)."""
    if len(candles) < lookback:
        return None, 0
    
    recent = candles[-lookback:]
    highs = [c['high'] for c in recent]
    lows = [c['low'] for c in recent]
    
    if len(highs) < 5 or len(lows) < 5:
        return None, 0
    
    # Check recent trend
    high_trend = (highs[-1] - highs[-5]) / highs[-5] if highs[-5] > 0 else 0
    low_trend = (lows[-1] - lows[-5]) / lows[-5] if lows[-5] > 0 else 0
    
    # Falling wedge: both down, but low_trend < high_trend (narrowing range)
    if high_trend < low_trend and high_trend < -0.02:  # At least 2% down
        # Check if range is contracting
        range_5 = highs[-5] - lows[-5]
        range_1 = highs[-1] - lows[-1]
        if range_1 < range_5:
            confidence = 0.70
            return 'Falling Wedge', confidence
    
    return None, 0


def detect_patterns(candles_5m, candles_15m=None, candles_1h=None):
    """Detect patterns across multiple timeframes with alignment bonus."""
    
    pattern_info = {
        'Double Top': {
            'type': 'reversal',
            'bias': 'bearish',
            'description': 'Price rejects resistance twice at similar levels',
            'image': '<span style="color: #e74c3c; font-weight: bold;">╭─────────────╮</span><br/><span style="color: #e74c3c;">│  ◡       ◡  │</span><br/><span style="color: #e74c3c;">│ ╱ ╲     ╱ ╲ │</span><br/><span style="color: #3498db;">│╱───╲───╱───╲│</span><br/><span style="color: #e74c3c; font-weight: bold;">╰─────────────╯</span>',
            'reliability': 'High'
        },
        'Double Bottom': {
            'type': 'reversal',
            'bias': 'bullish',
            'description': 'Price bounces from support twice at similar levels',
            'image': '<span style="color: #27ae60; font-weight: bold;">╭─────────────╮</span><br/><span style="color: #3498db;">│───╱───╱───╱─│</span><br/><span style="color: #27ae60;">│ ╲ ╱     ╲ ╱ │</span><br/><span style="color: #27ae60;">│  ⌒       ⌒  │</span><br/><span style="color: #27ae60; font-weight: bold;">╰─────────────╯</span>',
            'reliability': 'High'
        },
        'Head & Shoulders': {
            'type': 'reversal',
            'bias': 'bearish',
            'description': 'Three peaks: left shoulder < head > right shoulder at neckline',
            'image': '<span style="color: #e74c3c; font-weight: bold;">╭─────────────╮</span><br/><span style="color: #e74c3c;">│     ◆       │</span><br/><span style="color: #e74c3c;">│    ╱ ╲      │</span><br/><span style="color: #e74c3c;">│   ◆   ◆     │</span><br/><span style="color: #e74c3c;">│  ╱ ╲ ╱ ╲    │</span><br/><span style="color: #3498db;">│─────────────│</span><br/><span style="color: #e74c3c; font-weight: bold;">╰─────────────╯</span>',
            'reliability': 'Very High'
        },
        'Inverted H&S': {
            'type': 'reversal',
            'bias': 'bullish',
            'description': 'Three troughs: left shoulder > head < right shoulder at neckline',
            'image': '<span style="color: #27ae60; font-weight: bold;">╭─────────────╮</span><br/><span style="color: #3498db;">│─────────────│</span><br/><span style="color: #27ae60;">│  ╲ ╱ ╲ ╱    │</span><br/><span style="color: #27ae60;">│   ◆   ◆     │</span><br/><span style="color: #27ae60;">│    ╲ ╱      │</span><br/><span style="color: #27ae60;">│     ◆       │</span><br/><span style="color: #27ae60; font-weight: bold;">╰─────────────╯</span>',
            'reliability': 'Very High'
        },
        'Descending Triangle': {
            'type': 'continuation',
            'bias': 'bearish',
            'description': 'Lower highs with flat support - breakout downward expected',
            'image': '<span style="color: #e74c3c; font-weight: bold;">╭─────────────╮</span><br/><span style="color: #e74c3c;">│ ╱           │</span><br/><span style="color: #e74c3c;">│  ╲          │</span><br/><span style="color: #e74c3c;">│   ╲         │</span><br/><span style="color: #3498db;">│────────────▼│</span><br/><span style="color: #e74c3c; font-weight: bold;">╰─────────────╯</span>',
            'reliability': 'High'
        },
        'Ascending Triangle': {
            'type': 'continuation',
            'bias': 'bullish',
            'description': 'Higher lows with flat resistance - breakout upward expected',
            'image': '<span style="color: #27ae60; font-weight: bold;">╭─────────────╮</span><br/><span style="color: #3498db;">│▲────────────│</span><br/><span style="color: #27ae60;">│   ╱         │</span><br/><span style="color: #27ae60;">│  ╱          │</span><br/><span style="color: #27ae60;">│ ╱           │</span><br/><span style="color: #27ae60; font-weight: bold;">╰─────────────╯</span>',
            'reliability': 'High'
        },
        'Rising Wedge': {
            'type': 'reversal',
            'bias': 'bearish',
            'description': 'Both highs and lows rising, but range expanding - typically breaks down',
            'image': '<span style="color: #e74c3c; font-weight: bold;">╭─────────────╮</span><br/><span style="color: #e74c3c;">│         ╱   │</span><br/><span style="color: #e74c3c;">│        ╱ ╲  │</span><br/><span style="color: #e74c3c;">│       ╱   ╲ │</span><br/><span style="color: #3498db;">│──────╱─────╲▼</span><br/><span style="color: #e74c3c; font-weight: bold;">╰─────────────╯</span>',
            'reliability': 'Medium-High'
        },
        'Falling Wedge': {
            'type': 'reversal',
            'bias': 'bullish',
            'description': 'Both highs and lows falling, but range contracting - typically bounces up',
            'image': '<span style="color: #27ae60; font-weight: bold;">╭─────────────╮</span><br/><span style="color: #3498db;">│▲───────────────│</span><br/><span style="color: #27ae60;">│ ╲     ╱    │</span><br/><span style="color: #27ae60;">│  ╲   ╱     │</span><br/><span style="color: #27ae60;">│   ╲ ╱      │</span><br/><span style="color: #27ae60; font-weight: bold;">╰─────────────╯</span>',
            'reliability': 'Medium-High'
        }
    }
    
    if not candles_5m or len(candles_5m) < 10:
        return None, 0, 0, {}
    
    # Detect patterns on each timeframe
    results = {
        '5m': _detect_patterns_on_tf(candles_5m),
        '15m': _detect_patterns_on_tf(candles_15m) if candles_15m else (None, 0),
        '1h': _detect_patterns_on_tf(candles_1h) if candles_1h else (None, 0)
    }
    
    # Find all valid patterns
    valid_patterns = [(tf, name, conf) for tf, (name, conf) in results.items() if name is not None]
    
    if not valid_patterns:
        return None, 0, 0, {}
    
    # Get strongest pattern
    tf, pattern_name, base_conf = max(valid_patterns, key=lambda x: x[2])
    
    # Boost confidence if pattern appears on multiple timeframes
    aligned_tfs = [t for t, n, c in valid_patterns if n == pattern_name]
    alignment_bonus = min(0.15, len(aligned_tfs) * 0.05)  # +5% per aligned TF, max +15%
    confidence = min(0.99, base_conf + alignment_bonus)
    
    # Determine score impact
    pattern_data = pattern_info.get(pattern_name, {})
    bias = pattern_data.get('bias', 'neutral')
    
    if bias == 'bearish':
        score_impact = -confidence * 0.25
    elif bias == 'bullish':
        score_impact = confidence * 0.25
    else:
        score_impact = 0
    
    # Build detailed info dict
    pattern_detail = {
        'name': pattern_name,
        'timeframe': tf,
        'aligned_timeframes': aligned_tfs,
        'confidence': confidence,
        'bias': bias,
        'description': pattern_data.get('description', ''),
        'type': pattern_data.get('type', 'unknown'),
        'image': pattern_data.get('image', ''),
        'reliability': pattern_data.get('reliability', 'Unknown')
    }
    
    return pattern_name, confidence, score_impact, pattern_detail


def _detect_patterns_on_tf(candles):
    """Detect all patterns on a single timeframe."""
    if not candles or len(candles) < 10:
        return None, 0
    
    patterns = [
        detect_descending_triangle(candles),
        detect_ascending_triangle(candles),
        detect_rising_wedge(candles),
        detect_falling_wedge(candles),
        detect_double_top(candles),
        detect_double_bottom(candles),
        detect_head_shoulders(candles),
        detect_inverted_head_shoulders(candles),
    ]
    
    # Filter valid patterns
    valid = [(name, conf) for name, conf in patterns if name is not None]
    
    if not valid:
        return None, 0
    
    # Return strongest pattern on this timeframe
    return max(valid, key=lambda x: x[1])

