"""Divergence Detection - Identify climax conditions and reversal warnings."""
from datetime import datetime, timedelta
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from data_providers import get_intraday_candles_for


def calculate_price_volume_divergence(symbol, use_yf=False, force_yf=False, force_breeze=False):
    """
    Detect Price vs Volume Divergence (climax conditions).
    
    Works with limited data (even 5-10 candles) by analyzing trend vs volume.
    """
    try:
        # Try intraday first, fall back to daily if needed
        candles, _ = get_intraday_candles_for(
            symbol, interval='15minute', max_bars=50,
            use_yf=use_yf, force_yf=force_yf, force_breeze=force_breeze
        )
        
        # Fall back to daily if not enough intraday data
        if not candles or len(candles) < 5:
            candles, _ = get_intraday_candles_for(
                symbol, interval='1day', max_bars=20,
                use_yf=use_yf, force_yf=force_yf, force_breeze=force_breeze
            )
        
        if not candles or len(candles) < 3:
            return None
        
        # Use all available candles (not just recent 10)
        prices = [c.get('close', 0) for c in candles[-min(10, len(candles)):]]
        volumes = [c.get('volume', 0) for c in candles[-min(10, len(candles)):]]
        
        if not prices or sum(volumes) == 0 or len(prices) < 3:
            return None
        
        # Split into recent (last 50%) and older (first 50%)
        split = len(prices) // 2
        avg_price_recent = sum(prices[-split:]) / split if split > 0 else prices[-1]
        avg_price_older = sum(prices[:split]) / split if split > 0 else prices[0]
        price_trend = ((avg_price_recent - avg_price_older) / avg_price_older) * 100 if avg_price_older > 0 else 0
        
        avg_vol_recent = sum(volumes[-split:]) / split if split > 0 else volumes[-1]
        avg_vol_older = sum(volumes[:split]) / split if split > 0 else volumes[0]
        volume_trend = ((avg_vol_recent - avg_vol_older) / avg_vol_older) * 100 if avg_vol_older > 0 else 0
        
        # Detect divergence with relaxed thresholds for small datasets
        divergence_type = None
        divergence_score = 0
        confidence = 0
        
        # Climax Top: Price up, Volume DOWN (exhaustion)
        if price_trend > 1 and volume_trend < -5:
            divergence_type = 'climax_top'
            divergence_score = -0.5
            confidence = min(0.7, abs(volume_trend) / 30)
        
        # Climax Bottom: Price down, Volume DOWN (failed capitulation)
        elif price_trend < -1 and volume_trend < -5:
            divergence_type = 'climax_bottom'
            divergence_score = -0.3
            confidence = min(0.6, abs(volume_trend) / 30)
        
        # Healthy: Price and volume move together
        elif (price_trend > 1 and volume_trend > 3) or (price_trend < -1 and volume_trend > 3):
            divergence_type = 'healthy'
            divergence_score = 0.2
            confidence = 0.6
        
        else:
            return None  # No clear signal
        
        return {
            'divergence_type': divergence_type,
            'divergence_score': divergence_score,
            'price_trend': round(price_trend, 2),
            'volume_trend': round(volume_trend, 2),
            'confidence': round(confidence, 2)
        }
    
    except Exception as e:
        return None


def calculate_price_rsi_divergence(symbol, rsi_value, use_yf=False, force_yf=False, force_breeze=False):
    """
    Detect Price vs RSI Divergence (reversal warnings).
    
    - Bearish divergence: Price makes new high, RSI doesn't = weakness, reversal risk
    - Bullish divergence: Price makes new low, RSI doesn't = strength, reversal potential
    
    Args:
        symbol: Stock symbol
        rsi_value: Current RSI value (0-100) from scoring engine
        
    Returns:
        {
            'divergence_type': 'bearish' | 'bullish' | 'none',
            'divergence_score': -1 to +1,
            'price_momentum': recent price trend,
            'rsi_level': current RSI level,
            'confidence': 0-1
        }
    """
    try:
        # Fetch daily candles for trend analysis
        candles, _ = get_intraday_candles_for(
            symbol, interval='1day', max_bars=20,
            use_yf=use_yf, force_yf=force_yf, force_breeze=force_breeze
        )
        
        if not candles or len(candles) < 10:
            return None
        
        # Get recent prices
        recent_closes = [c.get('close', 0) for c in candles[-10:]]
        
        if not recent_closes:
            return None
        
        # Calculate price trend
        price_5d = recent_closes[-5]
        price_1d = recent_closes[-1]
        price_10d = recent_closes[0]
        
        price_momentum = ((price_1d - price_10d) / price_10d) * 100 if price_10d > 0 else 0
        
        # Check for price extremes
        price_high = max(recent_closes)
        price_low = min(recent_closes)
        
        # RSI level interpretation
        rsi_overbought = rsi_value > 70
        rsi_oversold = rsi_value < 30
        
        divergence_type = None
        divergence_score = 0
        confidence = 0
        
        # Bearish Divergence: New High but RSI NOT overbought (or declining)
        if price_1d == price_high and price_momentum > 5:
            if not rsi_overbought or rsi_value < 60:
                divergence_type = 'bearish'
                divergence_score = -0.7  # Strong bearish
                confidence = 0.8 if rsi_value < 50 else 0.6
        
        # Bullish Divergence: New Low but RSI NOT oversold (or recovering)
        elif price_1d == price_low and price_momentum < -5:
            if not rsi_oversold or rsi_value > 40:
                divergence_type = 'bullish'
                divergence_score = 0.6  # Bullish
                confidence = 0.75 if rsi_value > 50 else 0.5
        
        else:
            divergence_type = 'none'
            divergence_score = 0
            confidence = 0.3
        
        return {
            'divergence_type': divergence_type,
            'divergence_score': divergence_score,
            'price_momentum': round(price_momentum, 2),
            'rsi_level': round(rsi_value, 1),
            'confidence': round(confidence, 2)
        }
    
    except Exception as e:
        return None


def get_divergence_indicator(divergence_data):
    """
    Get visual indicator HTML for divergence.
    
    Returns: HTML badge with color and emoji
    """
    if not divergence_data:
        return "○"
    
    div_type = divergence_data.get('divergence_type')
    
    if div_type == 'climax_top':
        return "⚠️ <strong>Climax Top</strong>"
    elif div_type == 'climax_bottom':
        return "⚠️ <strong>Climax Bot</strong>"
    elif div_type == 'healthy':
        return "✓ <strong>Healthy</strong>"
    elif div_type == 'bearish':
        return "↙ <strong>Bearish Div</strong>"
    elif div_type == 'bullish':
        return "↗ <strong>Bullish Div</strong>"
    else:
        return "○ Normal"
