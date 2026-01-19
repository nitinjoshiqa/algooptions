"""
Volume Direction Logic: Accumulation vs Distribution Analysis

Analyzes volume patterns to determine if the market is in:
- ACCUMULATION: Smart money buying (rising price + rising volume)
- DISTRIBUTION: Smart money selling (rising price + falling volume or falling price + rising volume)
- NEUTRAL: Ambiguous volume signals

This helps validate trend strength:
- Uptrend + Accumulation = Strong bullish signal
- Uptrend + Distribution = Weakening bullish signal (be cautious)
- Downtrend + Distribution = Strong bearish signal
- Downtrend + Accumulation = Weakening bearish signal (may reverse)

Technical Foundation:
- On-Balance Volume (OBV) trend
- Volume Rate of Change (VROC)
- Chaikin Money Flow (CMF)
- Volume by price zones
"""

from dataclasses import dataclass
from typing import Optional, Dict, List
from enum import Enum
import math


class VolumeDirection(Enum):
    """Volume direction classification"""
    ACCUMULATION = "accumulation"    # Smart money buying
    DISTRIBUTION = "distribution"    # Smart money selling
    NEUTRAL = "neutral"              # Unclear volume signal
    DIVERGENCE = "divergence"        # Volume contradicts price (warning)


@dataclass
class VolumeMetrics:
    """Volume analysis metrics"""
    obv: float = 0.0                 # On-Balance Volume trend
    obv_trend: str = "neutral"       # "rising", "falling", "neutral"
    vroc: float = 0.0                # Volume Rate of Change %
    avg_volume: float = 0.0
    current_volume: float = 0.0
    volume_change_pct: float = 0.0   # Current vs average
    price_momentum: str = "neutral"   # "bullish", "bearish", "neutral"
    direction: VolumeDirection = VolumeDirection.NEUTRAL
    confidence: float = 0.0           # 0-100, how confident in the direction
    
    def __str__(self) -> str:
        return (
            f"Volume Direction: {self.direction.value:15} | "
            f"Confidence: {self.confidence:6.1f}% | "
            f"Volume Change: {self.volume_change_pct:+7.2f}%"
        )


class VolumeDirectionAnalyzer:
    """Analyzes volume patterns to identify accumulation/distribution"""
    
    def __init__(self, lookback_period: int = 20):
        """
        Initialize analyzer
        
        Args:
            lookback_period: Number of periods for moving averages (default: 20 days)
        """
        self.lookback_period = lookback_period
        self.price_history: List[float] = []
        self.volume_history: List[float] = []
        self.obv_history: List[float] = []
    
    def analyze(
        self,
        current_price: float,
        previous_price: float,
        current_volume: float,
        avg_volume: float,
        price_score: float = 0.0,
        confidence: float = 50.0,
    ) -> VolumeMetrics:
        """
        Analyze current volume against price movement
        
        Args:
            current_price: Current stock price
            previous_price: Previous close price
            current_volume: Current trading volume
            avg_volume: Average volume (typically 20-day SMA)
            price_score: Price momentum score (-1 to +1)
            confidence: Confidence in price direction (0-100)
        
        Returns:
            VolumeMetrics with direction and confidence
        """
        metrics = VolumeMetrics()
        
        # Store data for history
        self.price_history.append(current_price)
        self.volume_history.append(current_volume)
        
        # Calculate basic metrics
        metrics.current_volume = current_volume
        metrics.avg_volume = avg_volume
        metrics.volume_change_pct = ((current_volume - avg_volume) / avg_volume * 100) if avg_volume > 0 else 0
        
        # Determine price momentum
        price_change = current_price - previous_price
        if price_change > 0.01:  # Small buffer for noise
            metrics.price_momentum = "bullish"
        elif price_change < -0.01:
            metrics.price_momentum = "bearish"
        else:
            metrics.price_momentum = "neutral"
        
        # Calculate OBV trend
        self._update_obv(current_price, previous_price, current_volume)
        metrics.obv_trend = self._get_obv_trend()
        
        # Determine direction based on price and volume relationship
        metrics.direction, metrics.confidence = self._determine_direction(
            price_momentum=metrics.price_momentum,
            volume_change_pct=metrics.volume_change_pct,
            price_score=price_score,
            confidence=confidence,
            obv_trend=metrics.obv_trend
        )
        
        return metrics
    
    def _update_obv(self, current_price: float, previous_price: float, volume: float):
        """Update On-Balance Volume"""
        if not self.obv_history:
            self.obv_history.append(volume if current_price > previous_price else -volume)
        else:
            obv = self.obv_history[-1]
            if current_price > previous_price:
                obv += volume
            elif current_price < previous_price:
                obv -= volume
            # If unchanged, OBV stays the same
            self.obv_history.append(obv)
    
    def _get_obv_trend(self) -> str:
        """Determine OBV trend direction"""
        if len(self.obv_history) < 5:
            return "neutral"
        
        recent_obv = self.obv_history[-5:]
        avg_recent = sum(recent_obv) / len(recent_obv)
        
        if recent_obv[-1] > avg_recent:
            return "rising"
        elif recent_obv[-1] < avg_recent:
            return "falling"
        else:
            return "neutral"
    
    def _determine_direction(
        self,
        price_momentum: str,
        volume_change_pct: float,
        price_score: float,
        confidence: float,
        obv_trend: str
    ) -> tuple:
        """
        Determine if market is in accumulation or distribution
        
        Returns:
            (VolumeDirection, confidence_level)
        """
        # Thresholds
        HIGH_VOLUME_THRESHOLD = 20    # 20% above average
        LOW_VOLUME_THRESHOLD = -20    # 20% below average
        
        direction = VolumeDirection.NEUTRAL
        direction_confidence = 0.0
        
        # ==================== ACCUMULATION SIGNALS ====================
        # Bullish price + Rising volume = Strong accumulation
        if price_momentum == "bullish" and volume_change_pct > HIGH_VOLUME_THRESHOLD:
            direction = VolumeDirection.ACCUMULATION
            direction_confidence = min(95, 60 + abs(volume_change_pct) * 0.5 + confidence * 0.2)
        
        # Bullish price + Normal volume (not falling) = Weak accumulation
        elif price_momentum == "bullish" and volume_change_pct > LOW_VOLUME_THRESHOLD:
            direction = VolumeDirection.ACCUMULATION
            direction_confidence = min(70, 40 + confidence * 0.3)
        
        # ==================== DISTRIBUTION SIGNALS ====================
        # Bullish price + FALLING volume = Distribution warning (smart money selling into rally)
        elif price_momentum == "bullish" and volume_change_pct < LOW_VOLUME_THRESHOLD:
            direction = VolumeDirection.DISTRIBUTION
            direction_confidence = min(85, 50 + abs(volume_change_pct) * 0.4 + confidence * 0.2)
        
        # Bearish price + Rising volume = Strong distribution
        elif price_momentum == "bearish" and volume_change_pct > HIGH_VOLUME_THRESHOLD:
            direction = VolumeDirection.DISTRIBUTION
            direction_confidence = min(95, 60 + abs(volume_change_pct) * 0.5 + confidence * 0.2)
        
        # Bearish price + Normal volume = Weak distribution
        elif price_momentum == "bearish" and volume_change_pct > LOW_VOLUME_THRESHOLD:
            direction = VolumeDirection.DISTRIBUTION
            direction_confidence = min(70, 40 + confidence * 0.3)
        
        # ==================== DIVERGENCE SIGNALS ====================
        # Bearish price + FALLING volume = Divergence (may bounce)
        elif price_momentum == "bearish" and volume_change_pct < LOW_VOLUME_THRESHOLD:
            direction = VolumeDirection.DIVERGENCE
            direction_confidence = 60.0
        
        # Neutral or unclear
        else:
            direction = VolumeDirection.NEUTRAL
            direction_confidence = 30.0
        
        # Boost confidence based on OBV alignment
        if obv_trend == "rising" and direction in [VolumeDirection.ACCUMULATION, VolumeDirection.DIVERGENCE]:
            direction_confidence = min(98, direction_confidence + 10)
        elif obv_trend == "falling" and direction in [VolumeDirection.DISTRIBUTION]:
            direction_confidence = min(98, direction_confidence + 10)
        
        return direction, direction_confidence
    
    def get_signal_strength(self, metrics: VolumeMetrics, price_score: float = 0.0) -> float:
        """
        Get overall signal strength combining price and volume (-1 to +1)
        
        Positive values = Bullish (accumulation on uptrend)
        Negative values = Bearish (distribution on downtrend)
        """
        base_price_score = price_score  # -1 to +1
        
        # Adjust based on volume direction
        if metrics.direction == VolumeDirection.ACCUMULATION:
            # Boost bullish scores
            volume_boost = 0.2
        elif metrics.direction == VolumeDirection.DISTRIBUTION:
            # Reduce or reverse scores
            volume_boost = -0.2
        elif metrics.direction == VolumeDirection.DIVERGENCE:
            # Reduce confidence significantly
            volume_boost = -0.3
        else:
            volume_boost = 0.0
        
        # Confidence-weighted adjustment
        confidence_weight = metrics.confidence / 100.0
        adjusted_score = base_price_score + (volume_boost * confidence_weight)
        
        # Clamp to -1 to +1 range
        return max(-1.0, min(1.0, adjusted_score))
    
    def generate_signal_message(self, metrics: VolumeMetrics, symbol: str = "") -> str:
        """Generate human-readable signal message"""
        prefix = f"{symbol}: " if symbol else ""
        
        message_map = {
            VolumeDirection.ACCUMULATION: (
                f"{prefix}ACCUMULATION - Smart money buying. "
                f"Volume {metrics.volume_change_pct:+.1f}% vs avg. "
                f"Strong {metrics.price_momentum} trend. "
                f"Confidence: {metrics.confidence:.0f}%"
            ),
            VolumeDirection.DISTRIBUTION: (
                f"{prefix}DISTRIBUTION - Smart money selling. "
                f"Volume {metrics.volume_change_pct:+.1f}% vs avg. "
                f"Weak/uncertain trend. "
                f"Confidence: {metrics.confidence:.0f}%"
            ),
            VolumeDirection.DIVERGENCE: (
                f"{prefix}DIVERGENCE - Price/volume mismatch. "
                f"Price {metrics.price_momentum}, Volume {metrics.volume_change_pct:+.1f}%. "
                f"Potential reversal warning. "
                f"Confidence: {metrics.confidence:.0f}%"
            ),
            VolumeDirection.NEUTRAL: (
                f"{prefix}NEUTRAL - Unclear volume signal. "
                f"Volume {metrics.volume_change_pct:+.1f}% vs avg. "
                f"Wait for confirmation."
            ),
        }
        
        return message_map.get(metrics.direction, "Unknown direction")


# Integration with scoring engine
def augment_score_with_volume(
    base_score: float,
    volume_metrics: VolumeMetrics,
    weight: float = 0.15  # 15% weight for volume
) -> float:
    """
    Augment a stock score with volume direction signal
    
    Args:
        base_score: Original score (-1 to +1)
        volume_metrics: Calculated volume metrics
        weight: How much to weight volume signal (0-1)
    
    Returns:
        Adjusted score incorporating volume (-1 to +1)
    """
    # Calculate volume signal contribution
    if volume_metrics.direction == VolumeDirection.ACCUMULATION:
        volume_signal = 0.3  # Bullish boost
    elif volume_metrics.direction == VolumeDirection.DISTRIBUTION:
        volume_signal = -0.2  # Bearish penalty
    elif volume_metrics.direction == VolumeDirection.DIVERGENCE:
        volume_signal = -0.4  # Strong warning
    else:
        volume_signal = 0.0
    
    # Apply confidence-weighted adjustment
    confidence_weight = volume_metrics.confidence / 100.0
    adjustment = volume_signal * confidence_weight * weight
    
    # Blend with base score
    adjusted_score = base_score + adjustment
    
    # Clamp to -1 to +1
    return max(-1.0, min(1.0, adjusted_score))


if __name__ == "__main__":
    # Example usage
    analyzer = VolumeDirectionAnalyzer()
    
    # Test case 1: Bullish with high volume (Accumulation)
    metrics1 = analyzer.analyze(
        current_price=1000,
        previous_price=990,
        current_volume=10000000,
        avg_volume=5000000,
        price_score=0.3,
        confidence=70
    )
    print("Test 1 (Bullish + High Volume):")
    print(f"  {metrics1}")
    print(f"  Message: {analyzer.generate_signal_message(metrics1, 'INFY')}")
    print()
    
    # Test case 2: Bullish but low volume (Distribution warning)
    metrics2 = analyzer.analyze(
        current_price=1010,
        previous_price=1000,
        current_volume=2000000,
        avg_volume=5000000,
        price_score=0.3,
        confidence=70
    )
    print("Test 2 (Bullish + Low Volume - Distribution Warning):")
    print(f"  {metrics2}")
    print(f"  Message: {analyzer.generate_signal_message(metrics2, 'INFY')}")
    print()
    
    # Test case 3: Bearish with high volume (Distribution)
    metrics3 = analyzer.analyze(
        current_price=990,
        previous_price=1000,
        current_volume=12000000,
        avg_volume=5000000,
        price_score=-0.4,
        confidence=75
    )
    print("Test 3 (Bearish + High Volume - Distribution):")
    print(f"  {metrics3}")
    print(f"  Message: {analyzer.generate_signal_message(metrics3, 'INFY')}")
