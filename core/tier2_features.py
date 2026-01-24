"""Tier 2 Features: Pattern Validation, SL Scaling, Position Sizing."""

import numpy as np


class PatternValidator:
    """Validate and track pattern performance."""
    
    def __init__(self, min_instances=100, min_win_rate=0.55):
        """
        Initialize pattern validator.
        
        Args:
            min_instances: Minimum number of instances needed to validate
            min_win_rate: Minimum win rate required to use pattern
        """
        self.min_instances = min_instances
        self.min_win_rate = min_win_rate
        self.pattern_stats = {}  # {pattern_name: {wins, losses, last_100_wr}}
    
    def record_result(self, pattern_name, win):
        """Record trade result for a pattern."""
        if pattern_name not in self.pattern_stats:
            self.pattern_stats[pattern_name] = {
                'wins': 0,
                'losses': 0,
                'trades': [],  # Last 100 trades (True/False)
            }
        
        stats = self.pattern_stats[pattern_name]
        if win:
            stats['wins'] += 1
        else:
            stats['losses'] += 1
        
        # Keep only last 100 trades
        stats['trades'].append(win)
        if len(stats['trades']) > 100:
            stats['trades'].pop(0)
    
    def get_pattern_quality(self, pattern_name):
        """
        Get pattern quality score (0-1).
        
        Returns:
            Quality score or 0 if not enough instances
        """
        if pattern_name not in self.pattern_stats:
            return 0.0
        
        stats = self.pattern_stats[pattern_name]
        total = stats['wins'] + stats['losses']
        
        if total < self.min_instances:
            return 0.0  # Not validated yet
        
        wr = stats['wins'] / total if total > 0 else 0
        if wr < self.min_win_rate:
            return 0.0  # Doesn't meet minimum
        
        # Quality = (Win Rate - Min) / (1 - Min)
        quality = (wr - self.min_win_rate) / (1 - self.min_win_rate)
        return min(1.0, max(0.0, quality))
    
    def should_use_pattern(self, pattern_name):
        """Check if pattern should be used in trading."""
        return self.get_pattern_quality(pattern_name) > 0


class ConfidenceSLScaler:
    """Scale stop-loss distance based on signal quality."""
    
    @staticmethod
    def calculate_sl_distance(atr, confidence, direction, regime):
        """
        Calculate stop-loss distance based on confidence and regime.
        
        Args:
            atr: Average True Range value
            confidence: Signal confidence (10-100)
            direction: 'SHORT' or 'LONG'
            regime: Market regime ('trending', 'ranging', 'choppy', 'volatile')
        
        Returns:
            SL distance in price units
        """
        base_multiplier = 2.0
        
        # Confidence-based adjustment (higher confidence = tighter stops)
        if confidence > 65:
            confidence_mult = base_multiplier * 0.85  # 15% tighter
        elif confidence > 45:
            confidence_mult = base_multiplier * 1.0   # Normal
        else:
            confidence_mult = base_multiplier * 1.3   # 30% wider
        
        # Regime-based adjustment
        if regime == 'trending':
            regime_mult = 0.95  # Tightest in trending (go with the trend)
        elif regime == 'ranging':
            regime_mult = 1.05  # Slightly wider in ranging
        elif regime == 'choppy':
            regime_mult = 1.2   # Widest in choppy (more whipsaws)
        else:  # volatile
            regime_mult = 1.15  # Wide in volatile
        
        final_multiplier = confidence_mult * regime_mult
        return atr * final_multiplier
    
    @staticmethod
    def calculate_target_distance(atr, risk_reward_ratio=1.25):
        """
        Calculate target distance based on ATR and desired R:R ratio.
        
        Args:
            atr: Average True Range
            risk_reward_ratio: Target risk:reward ratio (default 1:1.25)
        
        Returns:
            Target distance in price units
        """
        sl_distance = atr * 2.0
        target_distance = sl_distance * risk_reward_ratio
        return target_distance


class MarketFilter:
    """Filter trades based on market conditions."""
    
    @staticmethod
    def should_trade(regime, atr_pct, confidence):
        """
        Determine if current market conditions are suitable for trading.
        
        Args:
            regime: Market regime ('trending', 'ranging', 'choppy', 'volatile')
            atr_pct: ATR as percentage of price
            confidence: Signal confidence (10-100)
        
        Returns:
            True if should trade, False otherwise
        """
        # Skip choppy markets with low confidence
        if regime == 'choppy' and confidence < 60:
            return False
        
        # Skip very volatile markets
        if atr_pct > 8.0:
            return False
        
        # Skip illiquid markets (very low volatility)
        if atr_pct < 1.5:
            return False
        
        # Skip if confidence too low in volatile markets
        if regime == 'volatile' and confidence < 50:
            return False
        
        return True
    
    @staticmethod
    def get_filter_reason(regime, atr_pct, confidence):
        """Get reason if trade should be skipped."""
        if regime == 'choppy' and confidence < 60:
            return "SKIP: Choppy market with low confidence"
        if atr_pct > 8.0:
            return f"SKIP: Volatility too high ({atr_pct:.2f}%)"
        if atr_pct < 1.5:
            return f"SKIP: Volatility too low ({atr_pct:.2f}%)"
        if regime == 'volatile' and confidence < 50:
            return "SKIP: Volatile market with insufficient confidence"
        return None


class PositionSizer:
    """Calculate position sizes based on signal quality."""
    
    @staticmethod
    def calculate_position_size(confidence, atr, regime, capital=100000, risk_per_trade=0.02):
        """
        Calculate position size based on confidence and risk parameters.
        
        Args:
            confidence: Signal confidence (10-100)
            atr: Average True Range
            regime: Market regime
            capital: Total trading capital
            risk_per_trade: Risk as fraction of capital per trade
        
        Returns:
            {
                'shares': Number of shares to trade,
                'confidence_mult': Confidence multiplier applied,
                'regime_mult': Regime multiplier applied,
                'risk_amount': Actual risk amount in currency
            }
        """
        base_risk = capital * risk_per_trade
        
        # Confidence multiplier (higher confidence = larger position)
        if confidence > 65:
            confidence_mult = 1.3  # 30% larger position
        elif confidence > 50:
            confidence_mult = 1.0  # Normal position
        elif confidence > 35:
            confidence_mult = 0.7  # 30% smaller
        else:
            confidence_mult = 0.4  # Very small
        
        # Regime multiplier
        if regime == 'trending':
            regime_mult = 1.2  # 20% larger in trending (higher probability)
        elif regime == 'choppy':
            regime_mult = 0.5  # Half size in choppy (lower probability)
        elif regime == 'volatile':
            regime_mult = 0.7  # Reduce in volatile
        else:  # ranging
            regime_mult = 1.0
        
        # Calculate effective risk and position size
        effective_risk = base_risk * confidence_mult * regime_mult
        shares = effective_risk / atr if atr > 0 else 0
        
        return {
            'shares': int(shares),
            'confidence_mult': confidence_mult,
            'regime_mult': regime_mult,
            'risk_amount': effective_risk,
            'confidence': confidence,
            'regime': regime,
            'atr': atr
        }
    
    @staticmethod
    def should_skip_trade(position_info):
        """Check if position size is too small to trade."""
        return position_info['shares'] < 1


# Integration functions for scoring_engine.py

def should_trade_symbol(regime, atr_pct, confidence):
    """
    Main entry point for Tier 2 market filtering.
    
    Returns: (should_trade, reason)
    """
    should_trade = MarketFilter.should_trade(regime, atr_pct, confidence)
    reason = MarketFilter.get_filter_reason(regime, atr_pct, confidence) if not should_trade else None
    return should_trade, reason


def get_sl_and_target(atr, confidence, direction, regime, risk_reward_ratio=1.25):
    """
    Get SL and target distances.
    
    Returns: {sl_distance, target_distance, recommendation}
    """
    scaler = ConfidenceSLScaler()
    sl_dist = scaler.calculate_sl_distance(atr, confidence, direction, regime)
    target_dist = scaler.calculate_target_distance(atr, risk_reward_ratio)
    
    return {
        'sl_distance': sl_dist,
        'target_distance': target_dist,
        'rr_ratio': target_dist / sl_dist if sl_dist > 0 else 0,
        'sl_tightness': confidence  # For reporting
    }


def calculate_position(confidence, atr, regime, capital=100000, risk_per_trade=0.02):
    """
    Calculate optimal position size.
    
    Returns: position info dict
    """
    sizer = PositionSizer()
    return sizer.calculate_position_size(confidence, atr, regime, capital, risk_per_trade)
