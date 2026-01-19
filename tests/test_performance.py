#!/usr/bin/env python3
"""Test the performance tracking system"""

from core.performance import get_tracker

tracker = get_tracker()

# Get performance stats
stats = tracker.get_performance_stats(days=30)
print('Performance Stats (Last 30 Days):')
for key, value in stats.items():
    print(f'  {key}: {value}')

print()
print('Recent Open Picks (Last 10):')
open_picks = tracker.get_open_picks()
for i, pick in enumerate(open_picks[:10], 1):
    symbol = pick.get("symbol", "")
    direction = pick.get("direction", "")
    score = float(pick.get("score", 0))
    confidence = pick.get("confidence", "unknown")  # Now a string (high/medium/low)
    print(f'{i:2d}. {symbol:12} {direction:8} score={score:+.3f} confidence={confidence}')

print()
print(f'\nTotal picks tracked: {stats["total_picks"]}')
print(f'Win rate: {stats["win_rate"]:.1f}%')
print(f'Bullish: {stats["bullish_picks"]}, Bearish: {stats["bearish_picks"]}')
