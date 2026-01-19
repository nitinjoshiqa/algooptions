"""Market regime detection."""
from core.config import REGIME_WEIGHTS


class MarketRegimeDetector:
    """Detect market regime based on volatility and trend strength."""
    
    @staticmethod
    def detect(candles_intraday, candles_swing=None, candles_longterm=None):
        """Detect market regime and return adjusted weights.
        
        Returns: dict with regime info and adjusted weights.
        """
        regime = 'weak_trend'
        weights = REGIME_WEIGHTS['weak_trend'].copy()
        
        try:
            if candles_intraday and len(candles_intraday) >= 10:
                closes = [float(c.get('close', 0)) for c in candles_intraday[-20:]]
                highs = [float(c.get('high', 0)) for c in candles_intraday[-20:]]
                lows = [float(c.get('low', 0)) for c in candles_intraday[-20:]]
                
                # Calculate volatility (ATR-like)
                trs = []
                for i in range(1, len(closes)):
                    tr = max(
                        highs[i] - lows[i],
                        abs(highs[i] - closes[i-1]),
                        abs(lows[i] - closes[i-1])
                    )
                    trs.append(tr)
                avg_tr = sum(trs) / len(trs) if trs else 0
                
                # Calculate trend strength
                sma20 = sum(closes) / len(closes)
                recent_close = closes[-1]
                trend_strength = abs(recent_close - sma20) / sma20 if sma20 > 0 else 0
                
                # Calculate volatility ratio
                volatility_ratio = avg_tr / sma20 if sma20 > 0 else 0
                
                # Determine momentum direction
                closes_last5 = closes[-5:]
                uptrend_count = sum(1 for i in range(1, len(closes_last5)) if closes_last5[i] > closes_last5[i-1])
                trend_direction = 'up' if uptrend_count >= 3 else 'down' if uptrend_count <= 2 else 'mixed'
                
                # Apply regime logic
                if volatility_ratio > 0.06:
                    regime = 'high_volatility'
                    weights = REGIME_WEIGHTS['high_volatility'].copy()
                elif trend_strength > 0.02 and trend_direction in ('up', 'down'):
                    regime = 'strong_trend'
                    weights = REGIME_WEIGHTS['strong_trend'].copy()
                elif trend_strength < 0.005 or volatility_ratio < 0.02:
                    regime = 'consolidation'
                    weights = REGIME_WEIGHTS['consolidation'].copy()
                else:
                    regime = 'weak_trend'
                    weights = REGIME_WEIGHTS['weak_trend'].copy()
        except Exception:
            pass
        
        return {
            'regime': regime,
            'weights': weights
        }
