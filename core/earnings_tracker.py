"""Earnings surprise tracking - EPS beat/miss, dates, consistency."""
import sys
import os
from datetime import datetime, timedelta

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from data_providers import get_fundamentals


def get_earnings_dates(symbol):
    """
    Get upcoming and past earnings dates for a symbol.
    
    Returns:
        {
            'next_earnings': datetime or None,
            'days_until_earnings': int or None,
            'last_earnings_date': datetime or None,
            'earnings_frequency': 'quarterly' | 'annual' | None
        }
    """
    try:
        # This would integrate with earnings calendar API
        # For now, using event_calendar from utilities if available
        try:
            from scripts.utilities.event_calendar import get_earnings_dates as get_earnings_from_cal
            dates = get_earnings_from_cal(symbol)
            if dates:
                return dates
        except:
            pass
        
        # Fallback: Return None if calendar not available
        return {
            'next_earnings': None,
            'days_until_earnings': None,
            'last_earnings_date': None,
            'earnings_frequency': None
        }
    
    except Exception as e:
        return None


def calculate_earnings_beat_miss(symbol, fundamentals_data=None):
    """
    Calculate EPS beat/miss history and consistency.
    
    Returns:
        {
            'last_4q_beats': [1, -2, 0.5, -1],  # % surprise (positive = beat)
            'beat_miss_ratio': 0.75,  # beats / total (0-1)
            'consistency_score': 0.4,  # How consistent (1 = always beats, 0 = random)
            'surprise_volatility': 2.5,  # Std dev of surprises (higher = unpredictable)
            'average_surprise': 0.8,  # Average beat/miss magnitude (%)
        }
    """
    try:
        if not fundamentals_data:
            fundamentals_data = get_fundamentals(symbol)
        
        if not fundamentals_data:
            return None
        
        # Extract analyst data (if available in fundamentals)
        # This depends on your fundamentals data structure
        eps_current = fundamentals_data.get('eps', 0)
        pe_current = fundamentals_data.get('pe_ratio', 0)
        
        # Placeholder: would need historical earnings data
        # For now, return conservative estimates
        return {
            'last_4q_beats': [],  # Would come from earnings calendar
            'beat_miss_ratio': 0.5,  # 50/50 by default
            'consistency_score': 0.3,  # Low consistency = unpredictable
            'surprise_volatility': 3.0,  # High volatility in surprises
            'average_surprise': 0.0,  # Neutral on average
            'eps_current': eps_current,
            'pe_current': pe_current
        }
    
    except Exception as e:
        return None


def get_earnings_confidence_modifier(symbol, days_until_earnings=None):
    """
    Get confidence modifier based on earnings proximity and history.
    
    Returns:
        {
            'modifier': 0.7,  # Multiply confidence by this (0.4 = -60% confidence, 1.0 = no change)
            'reason': 'Pre-earnings window (2 days)',
            'position_size_factor': 0.7  # Reduce position size by multiplying
        }
    """
    try:
        earnings_data = get_earnings_dates(symbol)
        beat_miss_data = calculate_earnings_beat_miss(symbol)
        
        if not earnings_data or not isinstance(earnings_data, dict) or earnings_data.get('days_until_earnings') is None:
            return {
                'modifier': 1.0,
                'reason': 'No upcoming earnings',
                'position_size_factor': 1.0
            }
        
        days_to_earnings = earnings_data.get('days_until_earnings')
        
        # HIGH RISK ZONES
        # 2-3 days before earnings: high volatility expected
        if 0 <= days_to_earnings <= 3:
            consistency = beat_miss_data.get('beat_miss_ratio', 0.5) if beat_miss_data else 0.5
            
            # Even beaters have noise around earnings
            if consistency > 0.7:
                # Consistent beater: less risk
                modifier = 0.7
                reason = f'Pre-earnings ({days_to_earnings}d) - consistent beater'
            else:
                # Unpredictable: higher risk
                modifier = 0.4
                reason = f'Pre-earnings ({days_to_earnings}d) - unpredictable'
            
            return {
                'modifier': modifier,
                'reason': reason,
                'position_size_factor': modifier  # Same reduction for position
            }
        
        # POST-EARNINGS VALIDATION (1-3 days after)
        elif -3 <= days_to_earnings < 0:
            return {
                'modifier': 0.5,
                'reason': 'Post-earnings (signal needs validation)',
                'position_size_factor': 0.6
            }
        
        # MODERATE WINDOW: 1-2 weeks out
        elif 4 <= days_to_earnings <= 14:
            return {
                'modifier': 0.85,
                'reason': f'Earnings in {days_to_earnings} days',
                'position_size_factor': 0.85
            }
        
        # SAFE: > 2 weeks from earnings
        else:
            return {
                'modifier': 1.0,
                'reason': f'Safe window ({days_to_earnings}d from earnings)',
                'position_size_factor': 1.0
            }
    
    except Exception as e:
        return {
            'modifier': 1.0,
            'reason': f'Error calculating earnings impact: {str(e)}',
            'position_size_factor': 1.0
        }


def get_earnings_summary(symbol):
    """
    Get complete earnings summary for display in HTML.
    
    Returns:
        {
            'next_earnings_date': '2026-02-15',
            'days_until': 7,
            'last_surprise': 2.5,  # % (positive = beat)
            'beat_miss_history': 'B M B B M' (last 5 quarters),
            'consistency': '60% beater',
            'risk_level': 'MEDIUM'
        }
    """
    try:
        earnings_data = get_earnings_dates(symbol)
        beat_miss_data = calculate_earnings_beat_miss(symbol)
        
        if not earnings_data or not earnings_data['next_earnings']:
            return {
                'next_earnings_date': None,
                'days_until': None,
                'last_surprise': None,
                'beat_miss_history': None,
                'consistency': 'Unknown',
                'risk_level': 'UNKNOWN'
            }
        
        next_date = earnings_data['next_earnings']
        days_until = earnings_data['days_until_earnings']
        
        # Build history string
        last_4q = beat_miss_data.get('last_4q_beats', []) if beat_miss_data else []
        history = ' '.join([f"{'B' if x > 0 else 'M' if x < 0 else '='}" for x in last_4q[-5:]])
        
        # Risk assessment
        if 0 <= days_until <= 3:
            risk = 'HIGH'
        elif 4 <= days_until <= 14:
            risk = 'MEDIUM'
        else:
            risk = 'LOW'
        
        consistency = beat_miss_data.get('beat_miss_ratio', 0.5) if beat_miss_data else 0.5
        last_surprise = beat_miss_data.get('last_4q_beats', [None])[0] if beat_miss_data and beat_miss_data.get('last_4q_beats') else None
        
        return {
            'next_earnings_date': next_date.strftime('%Y-%m-%d') if next_date else None,
            'days_until': days_until,
            'last_surprise': round(last_surprise, 2) if last_surprise else None,
            'beat_miss_history': history if history else 'N/A',
            'consistency': f"{int(consistency * 100)}% beater",
            'risk_level': risk
        }
    
    except Exception as e:
        return {
            'next_earnings_date': None,
            'days_until': None,
            'last_surprise': None,
            'beat_miss_history': None,
            'consistency': 'Error',
            'risk_level': 'UNKNOWN'
        }
