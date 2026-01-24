"""Tier 3 Features: ML-based Weighting, Indicator Validation, Continuous Calibration."""

import numpy as np
from datetime import datetime, timedelta
import pickle
import os


class IndicatorValidator:
    """Validate individual indicator performance and quality."""
    
    def __init__(self, min_samples=100):
        """
        Initialize indicator validator.
        
        Args:
            min_samples: Minimum samples needed to validate indicator
        """
        self.min_samples = min_samples
        self.indicator_stats = {}  # {indicator_name: {wins, losses, samples}}
    
    def record_result(self, indicator_name, signal_direction, result_win):
        """Record a trade result for a specific indicator."""
        if indicator_name not in self.indicator_stats:
            self.indicator_stats[indicator_name] = {
                'wins': 0,
                'losses': 0,
                'samples': [],
                'correlations': {}
            }
        
        stats = self.indicator_stats[indicator_name]
        if result_win:
            stats['wins'] += 1
        else:
            stats['losses'] += 1
        
        stats['samples'].append({
            'direction': signal_direction,
            'win': result_win,
            'timestamp': datetime.now()
        })
    
    def get_indicator_quality(self, indicator_name):
        """
        Get quality score for an indicator (0-1).
        
        Returns quality or 0 if not validated.
        """
        if indicator_name not in self.indicator_stats:
            return 0.0
        
        stats = self.indicator_stats[indicator_name]
        total = stats['wins'] + stats['losses']
        
        if total < self.min_samples:
            return 0.0  # Not validated
        
        wr = stats['wins'] / total if total > 0 else 0
        
        # Quality = (WR - 50%) / 50%
        # So 55% WR = quality 0.1, 60% WR = quality 0.2, etc.
        quality = (wr - 0.50) / 0.50
        return min(1.0, max(0.0, quality))
    
    def get_recommended_weight(self, indicator_name, default_weight=1.0):
        """Get recommended weight based on validation."""
        quality = self.get_indicator_quality(indicator_name)
        if quality == 0.0:
            return 0.0  # Don't use unvalidated indicators
        return default_weight * (0.5 + quality)  # 0.5 to 1.5x multiplier


class ConfidenceCalibrator:
    """Calibrate confidence scores to actual win rates."""
    
    def __init__(self, bucket_size=5):
        """
        Initialize calibrator.
        
        Args:
            bucket_size: Confidence bucket size (5 = 0-5, 5-10, etc.)
        """
        self.bucket_size = bucket_size
        self.confidence_buckets = {}  # {bucket: {wins, losses}}
        self.calibration_curve = {}  # {bucket: actual_wr}
        self.recalibration_count = 0
    
    def record_trade(self, confidence, win):
        """Record trade with its confidence and result."""
        bucket = int(confidence / self.bucket_size) * self.bucket_size
        
        if bucket not in self.confidence_buckets:
            self.confidence_buckets[bucket] = {'wins': 0, 'losses': 0}
        
        if win:
            self.confidence_buckets[bucket]['wins'] += 1
        else:
            self.confidence_buckets[bucket]['losses'] += 1
    
    def get_calibrated_confidence(self, raw_confidence):
        """
        Adjust confidence based on historical accuracy.
        
        Returns: Calibrated confidence (0-100)
        """
        if not self.confidence_buckets:
            return raw_confidence  # No data yet
        
        bucket = int(raw_confidence / self.bucket_size) * self.bucket_size
        
        if bucket not in self.confidence_buckets:
            # No data for this bucket, return raw
            return raw_confidence
        
        stats = self.confidence_buckets[bucket]
        total = stats['wins'] + stats['losses']
        if total < 10:  # Need at least 10 trades to trust
            return raw_confidence
        
        # Actual win rate for this confidence bucket
        actual_wr = stats['wins'] / total
        
        # Adjust raw confidence to match actual performance
        # If raw confidence says 70% but actual is 60%, reduce it
        calibrated = raw_confidence * actual_wr / (bucket + self.bucket_size/2)
        return min(100, max(0, calibrated))
    
    def recalibrate(self):
        """Recalculate calibration curve."""
        self.calibration_curve = {}
        
        for bucket, stats in self.confidence_buckets.items():
            total = stats['wins'] + stats['losses']
            if total >= 20:  # Only trust with 20+ samples
                wr = stats['wins'] / total
                self.calibration_curve[bucket] = wr
        
        self.recalibration_count += 1
        return len(self.calibration_curve)  # Calibrated buckets


class MLWeightOptimizer:
    """Learn optimal indicator weights from historical data."""
    
    def __init__(self, learning_rate=0.01, window_size=100):
        """
        Initialize ML weight optimizer.
        
        Args:
            learning_rate: How fast to update weights (0.01-0.1)
            window_size: Number of recent trades to use for learning
        """
        self.learning_rate = learning_rate
        self.window_size = window_size
        
        # Initial weights (equal)
        self.weights = {
            'rsi': 1.0,
            'ema': 1.0,
            'macd': 1.0,
            'bb': 1.0,
            'or': 1.0,
            'vwap': 1.0,
            'volume': 1.0,
            'structure': 1.0,
            'patterns': 1.0
        }
        
        self.trade_history = []  # [{indicator_signals}, win/loss]
    
    def record_trade(self, indicator_signals, win):
        """
        Record trade with indicator signals and result.
        
        Args:
            indicator_signals: {indicator_name: score}
            win: Boolean, whether trade won
        """
        self.trade_history.append({
            'signals': indicator_signals,
            'win': win,
            'timestamp': datetime.now()
        })
        
        # Keep only recent trades
        if len(self.trade_history) > self.window_size:
            self.trade_history.pop(0)
    
    def optimize_weights(self):
        """
        Use recent trades to optimize weights.
        
        Returns: Updated weights
        """
        if len(self.trade_history) < 20:
            return self.weights  # Need at least 20 trades
        
        # Calculate correlation of each indicator with wins
        correlations = {}
        
        for indicator in self.weights.keys():
            wins_with_signal = 0
            losses_with_signal = 0
            wins_without_signal = 0
            losses_without_signal = 0
            
            for trade in self.trade_history:
                signal = trade['signals'].get(indicator, 0)
                
                if abs(signal) > 0.1:  # Has signal
                    if trade['win']:
                        wins_with_signal += 1
                    else:
                        losses_with_signal += 1
                else:  # No signal
                    if trade['win']:
                        wins_without_signal += 1
                    else:
                        losses_without_signal += 1
            
            # Calculate correlation (win rate with signal vs without)
            with_signal_wr = wins_with_signal / max(1, wins_with_signal + losses_with_signal)
            without_signal_wr = wins_without_signal / max(1, wins_without_signal + losses_without_signal)
            
            correlation = with_signal_wr - 0.50  # Centered at 50%
            correlations[indicator] = correlation
        
        # Update weights based on correlation
        max_correlation = max(abs(c) for c in correlations.values()) if correlations else 1.0
        
        for indicator in self.weights.keys():
            corr = correlations.get(indicator, 0)
            
            if max_correlation > 0:
                # Positive correlation = increase weight
                adjustment = (corr / max_correlation) * self.learning_rate
                self.weights[indicator] *= (1 + adjustment)
            
            # Keep weights in reasonable range (0.1 to 3.0)
            self.weights[indicator] = min(3.0, max(0.1, self.weights[indicator]))
        
        # Normalize weights to sum to 9.0
        weight_sum = sum(self.weights.values())
        for indicator in self.weights:
            self.weights[indicator] = self.weights[indicator] * 9.0 / weight_sum
        
        return self.weights
    
    def get_weights(self):
        """Get current weights."""
        return self.weights.copy()
    
    def save_weights(self, filepath):
        """Save weights to file."""
        try:
            with open(filepath, 'wb') as f:
                pickle.dump({
                    'weights': self.weights,
                    'timestamp': datetime.now()
                }, f)
            return True
        except Exception as e:
            print(f"Failed to save weights: {e}")
            return False
    
    def load_weights(self, filepath):
        """Load weights from file."""
        try:
            with open(filepath, 'rb') as f:
                data = pickle.load(f)
                self.weights = data['weights']
            return True
        except Exception as e:
            print(f"Failed to load weights: {e}")
            return False


class ContinuousCalibrationEngine:
    """Continuously monitor and adapt to market changes."""
    
    def __init__(self, data_dir='tier3_data'):
        """Initialize calibration engine."""
        self.data_dir = data_dir
        self.indicator_validator = IndicatorValidator(min_samples=100)
        self.confidence_calibrator = ConfidenceCalibrator(bucket_size=5)
        self.ml_optimizer = MLWeightOptimizer(learning_rate=0.02, window_size=200)
        
        self.last_optimization = datetime.now()
        self.optimization_frequency = timedelta(days=7)  # Optimize weekly
        
        # Create data directory
        os.makedirs(data_dir, exist_ok=True)
    
    def record_trade_result(self, indicator_signals, confidence, win):
        """Record a trade result for all calibration systems."""
        # Record for confidence calibration
        self.confidence_calibrator.record_trade(confidence, win)
        
        # Record for ML optimization
        self.ml_optimizer.record_trade(indicator_signals, win)
    
    def get_adaptive_weights(self):
        """Get current adaptive weights from ML optimizer."""
        return self.ml_optimizer.get_weights()
    
    def should_optimize(self):
        """Check if it's time to optimize weights."""
        if not self.last_optimization:
            return True
        
        return datetime.now() - self.last_optimization >= self.optimization_frequency
    
    def run_optimization(self):
        """Run full optimization cycle."""
        # Recalibrate confidence
        buckets_calibrated = self.confidence_calibrator.recalibrate()
        
        # Optimize ML weights
        new_weights = self.ml_optimizer.optimize_weights()
        
        # Save weights
        self.ml_optimizer.save_weights(
            os.path.join(self.data_dir, f"weights_{datetime.now().strftime('%Y%m%d')}.pkl")
        )
        
        self.last_optimization = datetime.now()
        
        return {
            'confidence_buckets_calibrated': buckets_calibrated,
            'weights_updated': len(new_weights),
            'new_weights': new_weights
        }
    
    def get_calibrated_confidence(self, raw_confidence):
        """Get confidence adjusted for historical accuracy."""
        return self.confidence_calibrator.get_calibrated_confidence(raw_confidence)
    
    def get_summary(self):
        """Get summary of calibration state."""
        return {
            'confidence_buckets': len(self.confidence_calibrator.confidence_buckets),
            'ml_trades_recorded': len(self.ml_optimizer.trade_history),
            'calibration_updates': self.confidence_calibrator.recalibration_count,
            'current_weights': self.ml_optimizer.get_weights()
        }


# Integration functions

def create_calibration_engine(data_dir='tier3_data'):
    """Create a new calibration engine."""
    return ContinuousCalibrationEngine(data_dir=data_dir)


def get_ml_weights(engine):
    """Get ML-optimized weights from engine."""
    if not engine.should_optimize():
        return engine.get_adaptive_weights()
    
    result = engine.run_optimization()
    return result['new_weights']
