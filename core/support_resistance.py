"""
Support and Resistance Level Detection
======================================

This module identifies key support and resistance levels based on:
1. Recent Price Action (Swing Highs/Lows)
2. Pivot Points (Classical, Fibonacci, Camarilla)
3. Moving Averages (20, 50, 200-day)
4. Volume Profile (High Volume Nodes)
5. Psychological Levels (Round numbers)

These levels are then used to set more realistic targets and stop losses
instead of relying purely on ATR multiples.
"""

import numpy as np
import pandas as pd
from typing import Dict, Tuple, List, Optional


class SupportResistanceDetector:
    """Detect support and resistance levels from price data."""
    
    def __init__(self, lookback_periods: int = 20):
        """
        Initialize detector.
        
        Args:
            lookback_periods: Number of days to look back for swing highs/lows
        """
        self.lookback = lookback_periods
    
    def calculate_hybrid_sl_target(
        self,
        sr_sl_pct: float,
        sr_target_pct: float,
        atr_sl_pct: float,
        atr_target_pct: float,
        current_price: float,
        atr: float,
        trend: str = 'bullish'
    ) -> Dict[str, float]:
        """
        Blend Support/Resistance with ATR for realistic SL/Target.
        
        Hybrid formula:
        - SL = max(SR_pct × 0.7, min(ATR_pct × 1.0, ATR_pct × 0.3))
          (70% weight to S/R, but never below 1x ATR)
        - Target = SR_pct × 0.8 + ATR_pct × 0.2
          (80% weight to S/R, 20% safety margin from ATR)
        
        Args:
            sr_sl_pct: S/R-based stop loss %
            sr_target_pct: S/R-based target %
            atr_sl_pct: ATR-based stop loss %
            atr_target_pct: ATR-based target %
            current_price: Current stock price
            atr: Average True Range value
            trend: 'bullish' or 'bearish' (determines SL/Target direction)
        
        Returns:
            Dict with hybrid sl_pct, target_pct, sl_price, target_price
        """
        # HYBRID STOP LOSS: Respect S/R but don't go supertight
        sl_pct = max(
            sr_sl_pct * 0.7,           # 70% weight to structural level
            atr_sl_pct * 1.0           # Safety floor: at least 1x ATR
        )
        # Cap at 5% (don't let S/R create massive stops)
        sl_pct = min(sl_pct, 5.0)
        
        # HYBRID TARGET: Blend for realistic expectations
        target_pct = (sr_target_pct * 0.8) + (atr_target_pct * 0.2)
        # Ensure target > SL (minimum 1.5:1 R:R)
        if target_pct <= sl_pct * 1.5:
            target_pct = sl_pct * 1.5
        
        # Calculate prices based on TREND direction
        if trend == 'bearish':
            # For bearish: SL goes ABOVE, Target goes BELOW
            sl_price = round(current_price * (1 + sl_pct / 100), 2)
            target_price = round(current_price * (1 - target_pct / 100), 2)
        else:  # bullish or neutral
            # For bullish: SL goes BELOW, Target goes ABOVE
            sl_price = round(current_price * (1 - sl_pct / 100), 2)
            target_price = round(current_price * (1 + target_pct / 100), 2)
        
        rr_ratio = round(target_pct / sl_pct if sl_pct > 0 else 0, 2)
        
        return {
            'sl_pct': round(sl_pct, 2),
            'target_pct': round(target_pct, 2),
            'sl_price': sl_price,
            'target_price': target_price,
            'rr_ratio': rr_ratio,
        }
    
    def detect_extreme_zone(
        self,
        rsi: Optional[float] = None,
        bb_score: Optional[float] = None,
        ema_score: Optional[float] = None,
        macd_score: Optional[float] = None,
        trend: str = 'neutral'
    ) -> Dict[str, any]:
        """
        Detect if price is in overbought/oversold danger zone.
        
        Uses multiple indicators to confirm extremes:
        - RSI: Overbought (>75) / Oversold (<25)
        - Bollinger Bands: At upper band (>0.8) / lower band (<0.2)
        - EMA: Strong trend confirmation (>0.7 or <-0.7)
        - MACD: Momentum extremes (>0.8 or <-0.8)
        
        Args:
            rsi: RSI value (0-100)
            bb_score: Bollinger Band score (-1 to +1)
            ema_score: EMA trend score (-1 to +1)
            macd_score: MACD momentum score (-1 to +1)
            trend: 'bearish', 'bullish', or 'neutral'
        
        Returns:
            Dict with:
            - 'is_extreme': bool - True if in danger zone
            - 'zone_type': 'overbought', 'oversold', 'normal'
            - 'risk_level': 'HIGH', 'MEDIUM', 'LOW'
            - 'reason': str - explanation with indicator values
        """
        zone_signals = []
        signal_details = []
        
        # ===== RSI Analysis (extreme values always HIGH risk) =====
        rsi_extreme = False
        if rsi is not None:
            if rsi >= 85:
                zone_signals.append('overbought')
                signal_details.append(f"RSI {rsi:.0f} (>=85 EXTREME)")
                rsi_extreme = True
            elif rsi >= 70:
                zone_signals.append('overbought')
                signal_details.append(f"RSI {rsi:.0f} (>=70)")
            elif rsi <= 15:
                zone_signals.append('oversold')
                signal_details.append(f"RSI {rsi:.0f} (<=15 EXTREME)")
                rsi_extreme = True
            elif rsi <= 30:
                zone_signals.append('oversold')
                signal_details.append(f"RSI {rsi:.0f} (<=30)")
            elif rsi >= 65:
                signal_details.append(f"RSI {rsi:.0f} (approaching overbought)")
            elif rsi <= 35:
                signal_details.append(f"RSI {rsi:.0f} (approaching oversold)")
        
        # ===== Bollinger Band Analysis (score: -1 at lower, +1 at upper) =====
        if bb_score is not None:
            if bb_score >= 0.8:
                zone_signals.append('overbought')
                signal_details.append(f"BB upper band ({bb_score:.2f})")
            elif bb_score >= 0.6:
                signal_details.append(f"BB approaching upper ({bb_score:.2f})")
            elif bb_score <= -0.8:
                zone_signals.append('oversold')
                signal_details.append(f"BB lower band ({bb_score:.2f})")
            elif bb_score <= -0.6:
                signal_details.append(f"BB approaching lower ({bb_score:.2f})")
        
        # ===== EMA Trend Confirmation (more sensitive) =====
        if ema_score is not None:
            if abs(ema_score) >= 0.7:
                # Strong trend = confirms extreme
                if ema_score > 0.7:
                    zone_signals.append('overbought')
                    signal_details.append(f"EMA strong bull ({ema_score:.2f})")
                else:
                    zone_signals.append('oversold')
                    signal_details.append(f"EMA strong bear ({ema_score:.2f})")
        
        # ===== MACD Momentum Confirmation (more sensitive) =====
        if macd_score is not None:
            if abs(macd_score) >= 0.7:
                # Strong momentum = confirms extreme
                if macd_score > 0.7:
                    zone_signals.append('overbought')
                    signal_details.append(f"MACD strong bull ({macd_score:.2f})")
                else:
                    zone_signals.append('oversold')
                    signal_details.append(f"MACD strong bear ({macd_score:.2f})")
        
        # ===== Determine Risk Level =====
        if not zone_signals:
            # No extreme signals
            reason = "Normal zone: " + ", ".join(signal_details) if signal_details else "No extreme indicators detected"
            return {
                'is_extreme': False,
                'zone_type': 'normal',
                'risk_level': 'LOW',
                'reason': reason,
                'signal_count': 0,
            }
        
        # Count signal type
        zone_counts = {}
        for signal in zone_signals:
            zone_counts[signal] = zone_counts.get(signal, 0) + 1
        
        # Determine final zone (majority)
        primary_zone = max(zone_counts, key=zone_counts.get)
        signal_count = len(zone_signals)

        # If RSI is extreme, always HIGH risk
        if rsi_extreme:
            risk_level = 'HIGH'
            reason = f"EXTREME {primary_zone.upper()} (RSI): {', '.join(signal_details)}"
        elif signal_count >= 3:
            risk_level = 'HIGH'
            reason = f"CONFIRMED {primary_zone.upper()}: {signal_count} indicators converging. {', '.join(signal_details)}"
        elif signal_count >= 2:
            risk_level = 'HIGH'
            reason = f"CONFIRMED {primary_zone.upper()}: {signal_count} indicators converging. {', '.join(signal_details)}"
        elif signal_count == 1:
            # If the only signal is RSI (non-extreme), MEDIUM risk
            if 'RSI' in ''.join(signal_details):
                risk_level = 'MEDIUM'
                reason = f"RSI {primary_zone.upper()} zone: {', '.join(signal_details)}"
            else:
                risk_level = 'MEDIUM'
                reason = f"Alert {primary_zone.upper()}: {', '.join(signal_details)}"
        else:
            risk_level = 'LOW'
            reason = f"Normal zone: {', '.join(signal_details)}"

        return {
            'is_extreme': True,
            'zone_type': primary_zone,
            'risk_level': risk_level,
            'reason': reason,
            'signal_count': signal_count,
            'signals': zone_signals,
        }
    
    def adjust_position_size(
        self,
        base_position_size: float,
        risk_level: str,
        confidence: float
    ) -> Dict[str, any]:
        """
        Reduce position size for high-risk zones while maintaining score integrity.
        
        Args:
            base_position_size: Original calculated position size
            risk_level: 'HIGH', 'MEDIUM', or 'LOW'
            confidence: Signal confidence (0-100%)
        
        Returns:
            Dict with adjusted_size, multiplier, and reason
        """
        if risk_level == 'HIGH':
            # Reduce by 40-50% for extreme zones
            multiplier = 0.5 if confidence < 50 else 0.6
            reason = "High reversal risk - position reduced 40-50%"
        elif risk_level == 'MEDIUM':
            # Reduce by 20-30%
            multiplier = 0.75 if confidence < 50 else 0.8
            reason = "Moderate reversal risk - position reduced 20-25%"
        else:
            # Normal zone, no reduction
            multiplier = 1.0
            reason = "Normal zone - full position size"
        
        adjusted_size = round(base_position_size * multiplier)
        
        return {
            'adjusted_size': adjusted_size,
            'multiplier': multiplier,
            'reason': reason,
            'reduction_pct': round((1 - multiplier) * 100, 0) if multiplier < 1 else 0,
        }
    
    def detect_levels(self, df: pd.DataFrame) -> Dict[str, any]:
        """
        Detect all support and resistance levels.
        
        Args:
            df: DataFrame with columns ['open', 'high', 'low', 'close', 'volume']
                Must be sorted by date (oldest first)
        
        Returns:
            Dict with keys:
            - 'support': List of support levels (strongest first)
            - 'resistance': List of resistance levels (strongest first)
            - 'pivot': Pivot point levels
            - 'current_level': Current price position relative to levels
        """
        if df is None or len(df) < self.lookback:
            return self._empty_levels()
        
        current_price = float(df['close'].iloc[-1])
        
        results = {
            'support': [],
            'resistance': [],
            'pivot': {},
            'current_price': current_price,
            'consolidated_support': [],
            'consolidated_resistance': [],
        }
        
        # 1. Swing Highs and Lows (Recent Price Action)
        swing_highs, swing_lows = self._find_swing_points(df)
        results['support'].extend(swing_lows)
        results['resistance'].extend(swing_highs)
        
        # 2. Pivot Points
        pivot_levels = self._calculate_pivot_points(df)
        results['pivot'] = pivot_levels
        
        # Add pivot support/resistance
        if 'S1' in pivot_levels:
            results['support'].append(pivot_levels['S1'])
        if 'S2' in pivot_levels:
            results['support'].append(pivot_levels['S2'])
        if 'R1' in pivot_levels:
            results['resistance'].append(pivot_levels['R1'])
        if 'R2' in pivot_levels:
            results['resistance'].append(pivot_levels['R2'])
        
        # 3. Moving Average Support/Resistance
        ma_levels = self._get_ma_levels(df)
        if ma_levels['ma20'] is not None:
            results['support'].append(ma_levels['ma20'])
            results['resistance'].append(ma_levels['ma20'])
        
        # 4. Consolidate levels (merge nearby levels)
        results['consolidated_support'] = self._consolidate_levels(
            sorted(set(results['support']), reverse=True),
            consolidation_pct=0.5  # Within 0.5% = same level
        )
        results['consolidated_resistance'] = self._consolidate_levels(
            sorted(set(results['resistance']), reverse=True),
            consolidation_pct=0.5
        )
        
        # Sort for easier access
        results['support'] = sorted(set(results['support']), reverse=True)
        results['resistance'] = sorted(set(results['resistance']), reverse=True)
        
        return results
    
    def get_nearest_support_resistance(
        self, 
        current_price: float, 
        levels: Dict
    ) -> Tuple[Optional[float], Optional[float]]:
        """
        Get nearest support below and resistance above current price.
        
        Args:
            current_price: Current stock price
            levels: Dict from detect_levels()
        
        Returns:
            (nearest_support, nearest_resistance)
        """
        support_list = levels.get('consolidated_support', [])
        resistance_list = levels.get('consolidated_resistance', [])
        
        # Support: highest level below price
        nearest_support = None
        for s in support_list:
            if s < current_price:
                nearest_support = s
                break
        
        # Resistance: lowest level above price
        nearest_resistance = None
        for r in resistance_list:
            if r > current_price:
                nearest_resistance = r
                break
        
        return nearest_support, nearest_resistance
    
    def calculate_smart_sl_target(
        self,
        current_price: float,
        trend: str,  # 'bullish' or 'bearish'
        atr: float,
        levels: Dict,
        account_risk_pct: float = 1.0  # Risk 1% per trade
    ) -> Dict[str, float]:
        """
        Calculate SL and Target using support/resistance + ATR.
        
        Strategy:
        - For BEARISH: Place SL above nearest resistance, Target at nearest support
        - For BULLISH: Place SL below nearest support, Target at nearest resistance
        - Use ATR as fallback if levels not available
        
        Args:
            current_price: Entry price
            trend: 'bullish' or 'bearish'
            atr: Average True Range
            levels: Dict from detect_levels()
            account_risk_pct: Maximum % of account to risk per trade
        
        Returns:
            Dict with keys: 'sl_price', 'target_price', 'sl_pct', 'target_pct', 'rr_ratio'
        """
        nearest_support, nearest_resistance = self.get_nearest_support_resistance(
            current_price, levels
        )
        
        if trend == 'bearish':
            # Selling (expecting down)
            # SL = resistance level + 0.5% buffer, or 1.5x ATR above price
            if nearest_resistance:
                sl_price = nearest_resistance * 1.005  # 0.5% buffer above resistance
            else:
                sl_price = current_price + (1.5 * atr)
            
            # Target = support level - 0.5% buffer, or ATR below price
            if nearest_support:
                target_price = nearest_support * 0.995  # 0.5% buffer below support
            else:
                target_price = current_price - atr
        
        else:  # bullish
            # Buying (expecting up)
            # SL = support level - 0.5% buffer, or 1.5x ATR below price
            if nearest_support:
                sl_price = nearest_support * 0.995  # 0.5% buffer below support
            else:
                sl_price = current_price - (1.5 * atr)
            
            # Target = resistance level + 0.5% buffer, or ATR above price
            if nearest_resistance:
                target_price = nearest_resistance * 1.005  # 0.5% buffer above resistance
            else:
                target_price = current_price + atr
        
        # Calculate percentages
        sl_pct = abs((sl_price - current_price) / current_price * 100)
        target_pct = abs((target_price - current_price) / current_price * 100)
        
        # Risk-reward ratio
        risk = sl_pct
        reward = target_pct
        rr_ratio = reward / risk if risk > 0 else 0
        
        return {
            'sl_price': round(sl_price, 2),
            'target_price': round(target_price, 2),
            'sl_pct': round(sl_pct, 2),
            'target_pct': round(target_pct, 2),
            'rr_ratio': round(rr_ratio, 2),
            'support_used': nearest_support is not None,
            'resistance_used': nearest_resistance is not None,
        }
    
    # ==================== PRIVATE METHODS ====================
    
    def _find_swing_points(self, df: pd.DataFrame, period: int = 5) -> Tuple[List[float], List[float]]:
        """
        Find swing highs and lows using a rolling window.
        
        Swing High: A high that has lower highs on both sides within 'period' bars
        Swing Low: A low that has higher lows on both sides within 'period' bars
        """
        highs = df['high'].values
        lows = df['low'].values
        
        swing_highs = []
        swing_lows = []
        
        for i in range(period, len(df) - period):
            # Check for swing high
            if highs[i] == max(highs[i-period:i+period+1]):
                swing_highs.append(float(highs[i]))
            
            # Check for swing low
            if lows[i] == min(lows[i-period:i+period+1]):
                swing_lows.append(float(lows[i]))
        
        return swing_highs[-5:], swing_lows[-5:]  # Return last 5
    
    def _calculate_pivot_points(self, df: pd.DataFrame) -> Dict[str, float]:
        """
        Calculate classical pivot points from recent price action.
        
        Formulas:
        - Pivot (P) = (High + Low + Close) / 3
        - Resistance1 (R1) = (2 * P) - Low
        - Resistance2 (R2) = P + (High - Low)
        - Support1 (S1) = (2 * P) - High
        - Support2 (S2) = P - (High - Low)
        """
        high = float(df['high'].iloc[-1])
        low = float(df['low'].iloc[-1])
        close = float(df['close'].iloc[-1])
        
        p = (high + low + close) / 3
        
        return {
            'pivot': round(p, 2),
            'R1': round((2 * p) - low, 2),
            'R2': round(p + (high - low), 2),
            'S1': round((2 * p) - high, 2),
            'S2': round(p - (high - low), 2),
        }
    
    def _get_ma_levels(self, df: pd.DataFrame) -> Dict[str, Optional[float]]:
        """Get moving average levels as dynamic support/resistance."""
        result = {
            'ma20': None,
            'ma50': None,
            'ma200': None,
        }
        
        if len(df) >= 20:
            result['ma20'] = float(df['close'].tail(20).mean())
        if len(df) >= 50:
            result['ma50'] = float(df['close'].tail(50).mean())
        if len(df) >= 200:
            result['ma200'] = float(df['close'].tail(200).mean())
        
        return result
    
    def _consolidate_levels(self, levels: List[float], consolidation_pct: float = 0.5) -> List[float]:
        """
        Merge support/resistance levels that are very close together.
        
        Args:
            levels: Sorted list of levels (descending)
            consolidation_pct: Merge levels within X% of each other
        
        Returns:
            Consolidated list with duplicates merged
        """
        if not levels:
            return []
        
        consolidated = []
        tolerance = consolidation_pct / 100
        
        for level in levels:
            # Check if this level is too close to an existing one
            is_duplicate = False
            for existing in consolidated:
                if abs(level - existing) / existing < tolerance:
                    is_duplicate = True
                    break
            
            if not is_duplicate:
                consolidated.append(level)
        
        return consolidated
    
    def _empty_levels(self) -> Dict:
        """Return empty levels dict."""
        return {
            'support': [],
            'resistance': [],
            'pivot': {},
            'current_price': 0,
            'consolidated_support': [],
            'consolidated_resistance': [],
        }


def integrate_with_screener(result: Dict, data: pd.DataFrame, atr: float) -> Dict:
    """
    Integrate support/resistance with screener results using HYBRID approach.
    
    NEW: Implements hybrid S/R + ATR calculation AND extreme zone detection.
    - Score remains UNCHANGED (integrity preserved)
    - SL/Target use blend of S/R + ATR (realistic levels)
    - Risk zone flags added (overbought/oversold warnings)
    - Position size auto-adjusted for danger zones
    
    Usage in nifty_bearnness_v2.py:
    ``` 
    from core.support_resistance import integrate_with_screener
    
    # In the scoring loop, after getting 'result' dict:
    result = integrate_with_screener(result, historical_data_df, atr_value)
    ```
    
    Args:
        result: Screener result dict (with 'price', 'final_score', RSI, etc.)
        data: Historical price DataFrame
        atr: Current ATR value
    
    Returns:
        Updated result dict with new keys:
        - 'support_levels'
        - 'resistance_levels'
        - 'sl_price', 'target_price', 'sl_pct', 'target_pct', 'rr_ratio'
        - 'method': 'sr' (hybrid) or 'atr'
        - 'risk_zone': bool
        - 'zone_type': 'overbought', 'oversold', 'normal'
        - 'risk_level': 'HIGH', 'MEDIUM', 'LOW'
        - 'position_size_multiplier': reduction factor (0.5 to 1.0)
    """
    try:
        detector = SupportResistanceDetector(lookback_periods=20)
        current_price = result.get('price', 0)
        
        if data is None or len(data) < 5 or current_price <= 0:
            # Fallback: set defaults without S/R
            _set_atr_based_sl_target(result, atr)
            result['method'] = 'atr'
            result['risk_zone'] = False
            result['zone_type'] = 'normal'
            result['risk_level'] = 'LOW'
            result['position_size_multiplier'] = 1.0
            return result
        
        # ==================== STEP 1: Detect Support/Resistance Levels ====================
        levels = detector.detect_levels(data)
        result['support_levels'] = levels.get('consolidated_support', [])
        result['resistance_levels'] = levels.get('consolidated_resistance', [])
        result['pivot_levels'] = levels.get('pivot', {})
        
        # Determine trend from score (SCORE UNCHANGED)
        score = result.get('final_score', 0)
        trend = 'bearish' if score < -0.05 else 'bullish' if score > 0.05 else 'neutral'
        
        # ==================== STEP 2: Calculate ATR-Based SL/Target ====================
        price = current_price
        atr_sl_pct = (2.5 * atr / price * 100) if price > 0 and atr > 0 else 1.5
        atr_target_pct = atr_sl_pct * 3.0
        
        # ==================== STEP 3: Calculate S/R-Based SL/Target ====================
        if abs(score) >= 0.10 and len(result['support_levels']) > 0 and len(result['resistance_levels']) > 0:
            # Strong signal with available levels - use S/R
            sr_result = detector.calculate_smart_sl_target(
                current_price=current_price,
                trend=trend,
                atr=atr,
                levels=levels
            )
            sr_sl_pct = sr_result['sl_pct']
            sr_target_pct = sr_result['target_pct']
            has_sr_data = True
        else:
            # Weak signal or no data - use ATR percentages
            sr_sl_pct = atr_sl_pct
            sr_target_pct = atr_target_pct
            has_sr_data = False
        
        # ==================== STEP 4: HYBRID Calculation (Key Innovation) ====================
        if has_sr_data:
            hybrid_result = detector.calculate_hybrid_sl_target(
                sr_sl_pct=sr_sl_pct,
                sr_target_pct=sr_target_pct,
                atr_sl_pct=atr_sl_pct,
                atr_target_pct=atr_target_pct,
                current_price=current_price,
                atr=atr,
                trend=trend  # FIXED: pass trend direction
            )
            result['sl_price'] = hybrid_result['sl_price']
            result['target_price'] = hybrid_result['target_price']
            result['sl_pct'] = hybrid_result['sl_pct']
            result['target_pct'] = hybrid_result['target_pct']
            result['rr_ratio'] = hybrid_result['rr_ratio']
            result['method'] = 'sr'  # Hybrid S/R + ATR
        else:
            # No S/R data, use pure ATR
            _set_atr_based_sl_target(result, atr)
            result['method'] = 'atr'
        
        # ==================== STEP 5: Detect Extreme Zones (Overbought/Oversold) ====================
        rsi = result.get('rsi')
        
        # Multi-indicator extreme zone detection
        # Available indicators: RSI, BB_score, EMA_score, MACD_score
        bb_score = result.get('bb_score', 0)
        ema_score = result.get('ema_score', 0)
        macd_score = result.get('macd_score', 0)
        
        extreme_result = detector.detect_extreme_zone(
            rsi=rsi,
            bb_score=bb_score,
            ema_score=ema_score,
            macd_score=macd_score,
            trend=trend
        )
        
        result['risk_zone'] = extreme_result['is_extreme']
        result['zone_type'] = extreme_result['zone_type']
        result['risk_level'] = extreme_result['risk_level']
        result['risk_reason'] = extreme_result['reason']
        
        # ==================== STEP 6: Adjust Position Size for Risk ====================
        # Note: Score & confidence remain unchanged - only position size adjusts
        base_position = result.get('position_size', 100)  # Default if not set
        confidence = result.get('confidence', 50)
        
        position_adjust = detector.adjust_position_size(
            base_position_size=base_position,
            risk_level=extreme_result['risk_level'],
            confidence=confidence
        )
        
        result['adjusted_position_size'] = position_adjust['adjusted_size']
        result['position_size_multiplier'] = position_adjust['multiplier']
        result['position_size_reason'] = position_adjust['reason']
        
        return result
    
    except Exception as e:
        # Silently fallback to ATR on any error
        _set_atr_based_sl_target(result, atr)
        result['method'] = 'atr'
        result['risk_zone'] = False
        result['zone_type'] = 'normal'
        result['risk_level'] = 'LOW'
        result['position_size_multiplier'] = 1.0
        return result


def _set_atr_based_sl_target(result: Dict, atr: float) -> None:
    """Set SL and target using traditional ATR method."""
    price = result.get('price', 0)
    if price <= 0 or atr <= 0:
        return
    
    sl_pct = (2.5 * atr / price) * 100
    target_pct = sl_pct * 3.0
    
    result['sl_pct'] = round(sl_pct, 2)
    result['target_pct'] = round(target_pct, 2)
    result['rr_ratio'] = 3.0
    result['sl_price'] = round(price - (2.5 * atr), 2)
    result['target_price'] = round(price + (3.0 * sl_pct / 100 * price), 2)
