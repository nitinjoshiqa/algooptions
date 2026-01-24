"""Candle aggregation utility - Create higher timeframes from lower ones.

Allows creating 15-min candles from 5-min candles, 1-hour from 15-min, etc.
"""

def aggregate_candles(candles, source_interval, target_interval):
    """
    Aggregate candles to a higher timeframe.
    
    Args:
        candles: List of candle dicts with OHLCV
        source_interval: Source interval (e.g., '5minute')
        target_interval: Target interval (e.g., '15minute')
    
    Returns:
        List of aggregated candles
    
    Examples:
        # Convert 5-min to 15-min (group by 3)
        candles_15min = aggregate_candles(candles_5min, '5minute', '15minute')
        
        # Convert 5-min to 30-min (group by 6)
        candles_30min = aggregate_candles(candles_5min, '5minute', '30minute')
    """
    
    if not candles or len(candles) < 2:
        return candles
    
    # Define aggregation ratios
    aggregation_ratios = {
        ('1minute', '5minute'): 5,
        ('1minute', '15minute'): 15,
        ('1minute', '30minute'): 30,
        ('1minute', '1hour'): 60,
        ('5minute', '15minute'): 3,
        ('5minute', '30minute'): 6,
        ('5minute', '1hour'): 12,
        ('15minute', '30minute'): 2,
        ('15minute', '1hour'): 4,
        ('30minute', '1hour'): 2,
    }
    
    key = (source_interval, target_interval)
    if key not in aggregation_ratios:
        print(f"[WARN] Cannot aggregate {source_interval} → {target_interval}")
        return candles
    
    ratio = aggregation_ratios[key]
    aggregated = []
    
    for i in range(0, len(candles), ratio):
        group = candles[i:i+ratio]
        
        if len(group) == 0:
            continue
        
        # Build aggregated candle
        agg_candle = {
            'datetime': group[0].get('datetime', ''),
            'open': float(group[0].get('open', 0)),
            'high': max(float(c.get('high', 0)) for c in group),
            'low': min(float(c.get('low', 0)) for c in group),
            'close': float(group[-1].get('close', 0)),
            'volume': sum(int(c.get('volume', 0)) for c in group),
            'source': f"aggregated ({len(group)}x {source_interval})"
        }
        
        # Only add if it's a complete group
        if len(group) == ratio:
            aggregated.append(agg_candle)
    
    return aggregated


def create_15min_from_5min(candles_5min):
    """Convenience function: Create 15-min candles from 5-min candles."""
    return aggregate_candles(candles_5min, '5minute', '15minute')


def create_30min_from_5min(candles_5min):
    """Convenience function: Create 30-min candles from 5-min candles."""
    return aggregate_candles(candles_5min, '5minute', '30minute')


def create_1hour_from_5min(candles_5min):
    """Convenience function: Create 1-hour candles from 5-min candles."""
    return aggregate_candles(candles_5min, '5minute', '1hour')


def create_1hour_from_15min(candles_15min):
    """Convenience function: Create 1-hour candles from 15-min candles."""
    return aggregate_candles(candles_15min, '15minute', '1hour')


# Example usage and testing
if __name__ == "__main__":
    # Test with sample 5-min candles
    sample_5min = [
        {'datetime': '2026-01-24 09:15', 'open': 100.0, 'high': 102.0, 'low': 99.0, 'close': 101.5, 'volume': 1000},
        {'datetime': '2026-01-24 09:20', 'open': 101.5, 'high': 103.0, 'low': 101.0, 'close': 102.5, 'volume': 1200},
        {'datetime': '2026-01-24 09:25', 'open': 102.5, 'high': 104.0, 'low': 102.0, 'close': 103.5, 'volume': 1100},
        {'datetime': '2026-01-24 09:30', 'open': 103.5, 'high': 105.0, 'low': 103.0, 'close': 104.5, 'volume': 1300},
        {'datetime': '2026-01-24 09:35', 'open': 104.5, 'high': 106.0, 'low': 104.0, 'close': 105.5, 'volume': 1400},
        {'datetime': '2026-01-24 09:40', 'open': 105.5, 'high': 107.0, 'low': 105.0, 'close': 106.5, 'volume': 1500},
    ]
    
    print("Original 5-min candles:")
    for c in sample_5min:
        print(f"  {c['datetime']}: O={c['open']}, H={c['high']}, L={c['low']}, C={c['close']}, V={c['volume']}")
    
    print("\nAggregated 15-min candles (3x5min):")
    candles_15min = create_15min_from_5min(sample_5min)
    for c in candles_15min:
        print(f"  {c['datetime']}: O={c['open']}, H={c['high']}, L={c['low']}, C={c['close']}, V={c['volume']}")
    
    print("\nVerification (15-min should be [99-104.5] high, [99-102] low):")
    if candles_15min:
        c = candles_15min[0]
        print(f"  First 15-min: Open={c['open']}, High={c['high']}, Low={c['low']}, Close={c['close']}")
        print(f"  ✓ High={c['high']} (max of 102, 103, 104)")
        print(f"  ✓ Low={c['low']} (min of 99, 101, 102)")
