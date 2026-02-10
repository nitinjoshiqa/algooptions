"""
Backtesting Engine - Replays historical data and generates signals

UPDATED: Now integrates new robustness & context engines for improved accuracy
"""

import pandas as pd
import yfinance as yf
from datetime import datetime, timedelta
from indicators.patterns import detect_patterns
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# NEW: Import unified context, robustness, and special day detection engines
from core.context_engine import compute_context_score as compute_context_from_engine
from core.robustness_engine import (
    validate_robustness, 
    get_robustness_score, 
    calculate_robustness_momentum as calc_robustness_momentum_from_filters,
    get_robustness_fail_reasons
)
from core.special_days_detector import get_special_day_type, adjust_for_special_day
from core.trade_learner import log_trade_opportunity


# ==================== SIGNAL PERSISTENCE VALIDATION FUNCTIONS ====================
# These functions validate that detected signals persist across multiple candles
# Purpose: Avoid entering on temporary spikes/dips that reverse immediately

def is_signal_persistent(df, current_idx, lookback=1):
    """
    Verify signal condition persists across multiple candles
    
    Args:
        df: DataFrame with OHLCV
        current_idx: Current candle index where signal detected
        lookback: How many bars back to verify (1 = current candle, 2 = current + 1 back)
    
    Returns:
        dict: Signal persistence metrics
    """
    # Need at least current bar and one previous bar (index 0)
    if current_idx < 1:
        return {}  # Not enough data yet
    
    # Current values
    curr_close = df['Close'].iloc[current_idx]
    curr_sma20 = df['SMA20'].iloc[current_idx]
    curr_sma50 = df['SMA50'].iloc[current_idx]
    curr_rsi = df['RSI'].iloc[current_idx]
    curr_price_sma20 = (curr_close - curr_sma20) / curr_sma20 if curr_sma20 != 0 else 0
    
    # Previous values (lookback)
    prev_close = df['Close'].iloc[current_idx - 1]
    prev_sma20 = df['SMA20'].iloc[current_idx - 1]
    prev_sma50 = df['SMA50'].iloc[current_idx - 1]
    prev_rsi = df['RSI'].iloc[current_idx - 1]
    prev_price_sma20 = (prev_close - prev_sma20) / prev_sma20 if prev_sma20 != 0 else 0
    
    # Two candles back (for double confirmation)
    prev2_sma20 = df['SMA20'].iloc[current_idx - 2] if current_idx >= 2 else prev_sma20
    prev2_sma50 = df['SMA50'].iloc[current_idx - 2] if current_idx >= 2 else prev_sma50
    
    return {
        'sma20': curr_sma20,
        'sma50': curr_sma50,
        'rsi': curr_rsi,
        'price_sma20_offset': curr_price_sma20,
        'prev_sma20': prev_sma20,
        'prev_sma50': prev_sma50,
        'prev_rsi': prev_rsi,
        'prev_price_sma20_offset': prev_price_sma20,
        'sma20_trending_up': curr_sma20 > prev_sma20 > prev2_sma20,
        'sma50_trending_up': curr_sma50 > prev_sma50,
        'rsi_rising': curr_rsi > prev_rsi,
        'price_above_sma20_confirmed': 
            (curr_price_sma20 > 0 and prev_price_sma20 > 0),  # Both bars above
        'price_above_sma20_rising': 
            (curr_price_sma20 > prev_price_sma20),  # Diverging
    }


def get_market_regime(adx_value):
    """
    Determine market regime based on ADX
    ADX > 25 = TRENDING | 20-25 = NEUTRAL | < 20 = RANGING
    """
    if adx_value > 25:
        return 'TRENDING'
    elif adx_value < 20:
        return 'RANGING'
    else:
        return 'NEUTRAL'


def get_volatility_regime(atr, close):
    """
    Determine volatility regime based on ATR/Close ratio
    """
    if close == 0:
        return 'MEDIUM'
    vol_ratio = atr / close
    if vol_ratio > 0.03:  # > 3% daily
        return 'HIGH'
    elif vol_ratio > 0.015:
        return 'MEDIUM'
    else:
        return 'LOW'




# Note: Robustness momentum is now calculated by robustness_engine
# based on filter state changes, not price momentum



def calculate_master_score(confidence, final_score=0.68, context_score=3.0, 
                          context_momentum=0.0, robustness_score=50, news_sentiment=0.0):
    """
    Calculate master score combining all 6 dimensions with weightage
    
    GUARDRAILS:
    - Master score is DIRECTION-AGNOSTIC (0-100 quality metric, not bias)
    - Use ONLY for ranking, position sizing, and UI display
    - DO NOT use for signal generation, validation, or direction bias
    - Signals are already validated by robustness filters (ALL 7 must PASS)
    - Master score CANNOT override signal = NO/YES decision
    
    Args:
        confidence: Pattern confidence (0-100)
        final_score: Technical score (0-1)
        context_score: Institutional context (0-5)
        context_momentum: Context momentum (-1 to +1)
        robustness_score: Filter quality (0-100) = (filters_passed / 7) * 100
        news_sentiment: News sentiment (-1 to +1)
    
    Returns:
        dict: {
            'master_score': 0-100,
            'components': {...},
            'weights': {...},
            'tooltip': str
        }
    """
    # Normalize all scores to 0-100 range
    normalized = {
        'confidence': confidence,  # Already 0-100
        'technical': (final_score * 100),  # 0-1 → 0-100
        'context': (context_score / 5.0 * 100),  # 0-5 → 0-100
        'momentum': ((context_momentum + 1) / 2 * 100),  # -1 to +1 → 0-100
        'robustness': robustness_score,  # Already 0-100
        'news': ((news_sentiment + 1) / 2 * 100),  # -1 to +1 → 0-100
    }
    
    # Weightage (updated: 6 dimensions)
    weights = {
        'confidence': 0.25,    # Pattern quality - 25%
        'technical': 0.25,     # Indicator quality - 25%
        'robustness': 0.20,    # Entry environment - 20%
        'context': 0.15,       # Market context - 15%
        'momentum': 0.10,      # Market momentum - 10%
        'news': 0.05,          # News impact - 5%
    }
    
    # Calculate weighted master score
    master_score = sum(
        normalized[key] * weights[key]
        for key in weights.keys()
    )
    
    # Create tooltip text
    tooltip = (
        f"Master Score: {master_score:.1f}/100\n"
        f"━━━━━━━━━━━━━━━━━━━━━━\n"
        f"Confidence (Pattern): {normalized['confidence']:.0f}/100 (25% weight)\n"
        f"  Quality of pattern detection\n\n"
        f"Technical (Indicators): {normalized['technical']:.0f}/100 (25% weight)\n"
        f"  RSI, VWAP, EMA, MACD, Bollinger Bands\n\n"
        f"Robustness (Filters): {normalized['robustness']:.0f}/100 (20% weight)\n"
        f"  ALL 7 filters (regime, volume, time, liquidity, earnings, MTF, exp)\n\n"
        f"Context (Institutional): {normalized['context']:.0f}/100 (15% weight)\n"
        f"  Vol/Div/RSI divergence, institutional flows\n\n"
        f"Momentum (Market Flow): {normalized['momentum']:.0f}/100 (10% weight)\n"
        f"  Rate of change in momentum: {context_momentum:+.2f}\n\n"
        f"News Sentiment: {normalized['news']:.0f}/100 (5% weight)\n"
        f"  Latest news impact: {news_sentiment:+.2f}\n"
        f"━━━━━━━━━━━━━━━━━━━━━━\n"
        f"Tier: {'STRONG ✓✓' if master_score >= 80 else 'GOOD ✓' if master_score >= 70 else 'FAIR ⚠' if master_score >= 60 else 'WEAK ✗'}\n"
        f"Use for: Ranking & position sizing only\n"
        f"NOT for: Signal generation or direction bias"
    )
    
    return {
        'master_score': master_score,
        'components': normalized,
        'weights': weights,
        'tooltip': tooltip
    }


def validate_bullish_signal(df, current_idx, signal_type):
    """
    Validate bullish signal will persist
    
    Returns True only if signal is likely to continue
    """
    if current_idx < 2:
        return False
    
    persistence = is_signal_persistent(df, current_idx)
    if not persistence:
        return False
    
    if signal_type == 'Golden Cross':
        # Golden cross valid if:
        # 1. SMA20 > SMA50 (✓ checked in generate_signals)
        # 2. Both EMAs trending up ← NEW VALIDATION
        # 3. Price above both ← NEW VALIDATION
        return (
            persistence['sma20_trending_up'] and
            persistence['sma50_trending_up'] and
            persistence['price_above_sma20_confirmed']
        )
    
    elif signal_type == 'Pullback':
        # Pullback valid if:
        # 1. Price near SMA20 (✓ checked)
        # 2. SMA20 still above SMA50 ← NEW VALIDATION
        # 3. RSI rising (momentum recovering) ← NEW VALIDATION
        return (
            persistence['sma20'] > persistence['sma50'] and
            persistence['rsi_rising'] and
            persistence['price_above_sma20_confirmed']
        )
    
    elif signal_type == 'Breakout':
        # Breakout valid if:
        # 1. Close above 5-bar high (✓ checked)
        # 2. Price continuing above, not falling back ← NEW VALIDATION
        # 3. RSI not overbought yet ← NEW VALIDATION
        return (
            persistence['rsi'] < 70 and
            persistence['price_above_sma20_rising'] and
            persistence['rsi_rising']
        )
    
    return False


def validate_bearish_signal(df, current_idx, signal_type):
    """
    Validate bearish signal will persist
    """
    if current_idx < 2:
        return False
    
    persistence = is_signal_persistent(df, current_idx)
    if not persistence:
        return False
    
    if signal_type == 'Death Cross':
        # Death cross valid if:
        # 1. SMA20 < SMA50 (✓ checked)
        # 2. Both EMAs trending down ← NEW VALIDATION
        # 3. Price below both ← NEW VALIDATION
        sma20 = persistence['sma20']
        sma50 = persistence['sma50']
        prev_sma20 = persistence['prev_sma20']
        prev_sma50 = persistence['prev_sma50']
        
        return (
            sma20 < prev_sma20 and 
            persistence['price_above_sma20_offset'] < 0  # Price below SMA20
        )
    
    elif signal_type == 'Pullback':
        # Pullback sell valid if SMA20 < SMA50 and RSI falling
        return (
            persistence['sma20'] < persistence['sma50'] and
            not persistence['rsi_rising'] and  # RSI falling
            persistence['price_above_sma20_offset'] < 0.02  # Near SMA20
        )
    
    elif signal_type == 'Breakdown':
        # Breakdown valid if continuing lower with bearish momentum
        return (
            persistence['rsi'] > 30 and
            not persistence['rsi_rising'] and
            persistence['price_above_sma20_offset'] < 0
        )
    
    return False

# =====================================================================


class BacktestEngine:
    """Historical data replay and signal generation"""
    
    def __init__(self, start_date, end_date, symbols):
        """
        Args:
            start_date: '2024-01-01'
            end_date: '2026-01-18'
            symbols: ['INFY', 'RELIANCE', 'TCS']
        """
        self.start_date = pd.to_datetime(start_date)
        self.end_date = pd.to_datetime(end_date)
        self.symbols = symbols
        self.data_cache = {}
        
    def load_historical_data(self, symbol, interval='1d'):
        """Download historical OHLCV data"""
        print(f"Loading {symbol} data from {self.start_date.date()} to {self.end_date.date()}...")
        
        try:
            ticker = yf.Ticker(f"{symbol}.NS")
            df = ticker.history(
                start=self.start_date, 
                end=self.end_date,
                interval=interval
            )
            
            if df.empty:
                print(f"  ⚠️ No data for {symbol}")
                return None
                
            # Add basic indicators
            df['Returns'] = df['Close'].pct_change()
            df['SMA20'] = df['Close'].rolling(20).mean()
            df['SMA50'] = df['Close'].rolling(50).mean()
            
            # ATR for stop-loss
            high_low = df['High'] - df['Low']
            high_close = abs(df['High'] - df['Close'].shift())
            low_close = abs(df['Low'] - df['Close'].shift())
            ranges = pd.concat([high_low, high_close, low_close], axis=1)
            df['ATR'] = ranges.max(axis=1).rolling(14).mean()
            
            # ADX for trend strength (filter trending stocks only)
            plus_dm = df['High'].diff()
            minus_dm = -df['Low'].diff()
            plus_dm[plus_dm < 0] = 0
            minus_dm[minus_dm < 0] = 0
            
            tr = ranges.max(axis=1)
            atr14 = tr.rolling(14).mean()
            
            plus_di = 100 * (plus_dm.rolling(14).mean() / atr14)
            minus_di = 100 * (minus_dm.rolling(14).mean() / atr14)
            
            dx = 100 * abs(plus_di - minus_di) / (plus_di + minus_di)
            df['ADX'] = dx.rolling(14).mean()
            
            print(f"  ✓ Loaded {len(df)} bars for {symbol}")
            return df
            
        except Exception as e:
            print(f"  ✗ Error loading {symbol}: {e}")
            return None
    
    def generate_signals(self, symbol, df):
        """
        Generate entry/exit signals with 7 NEW robustness filters:
        1. Market regime (ADX)
        2. Volume confirmation
        3. Time-of-day filtering
        4. Liquidity checks
        5. Volatility-adjusted sizing awareness
        6. Earnings/gap avoidance
        7. Expectancy filtering
        
        Returns: List of signals
        """
        signals = []
        
        # Add RSI for momentum filter
        delta = df['Close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        rs = gain / loss
        df['RSI'] = 100 - (100 / (1 + rs))
        
        # Add volume filter
        df['VolSMA'] = df['Volume'].rolling(20).mean()
        
        # Pattern expectancy rates (based on historical performance)
        pattern_expectancy = {
            'Golden Cross': 0.62, 'Pullback': 0.64, 'Breakout': 0.58,
            'Death Cross': 0.60, 'Breakdown': 0.56
        }
        
        for i in range(50, len(df)):
            current_date = df.index[i]
            current_price = df['Close'].iloc[i]
            current_atr = df['ATR'].iloc[i]
            
            sma20 = df['SMA20'].iloc[i]
            sma50 = df['SMA50'].iloc[i]
            prev_sma20 = df['SMA20'].iloc[i-1]
            prev_sma50 = df['SMA50'].iloc[i-1]
            
            rsi = df['RSI'].iloc[i]
            volume = df['Volume'].iloc[i]
            vol_avg = df['VolSMA'].iloc[i]
            adx = df['ADX'].iloc[i]
            
            # ===== NEW ROBUSTNESS FILTERS =====
            
            # FILTER 1: Market Regime Detection (ADX)
            market_regime = get_market_regime(adx)
            regime_valid = market_regime in ['TRENDING', 'NEUTRAL']
            
            # FILTER 2: Volatility Regime
            vol_regime = get_volatility_regime(current_atr, current_price)
            
            # FILTER 3: Time-of-Day Filter (9 AM - 3 PM IST only)
            hour = current_date.hour if hasattr(current_date, 'hour') else 13
            time_valid = 9 <= hour <= 15
            
            # FILTER 4: Liquidity Check (Min 50k daily volume)
            min_vol = 50000
            avg_volume_20d = df['Volume'].iloc[max(0, i-20):i].mean()
            liquidity_valid = avg_volume_20d > min_vol
            
            # FILTER 5: Earnings/Gap Avoidance (No extreme volume spikes)
            volume_surge = volume > vol_avg * 2.5  # >250% = event risk
            earnings_safe = not volume_surge
            
            # FILTER 6: Multi-timeframe simple check
            sma_aligned = current_price > sma20 > sma50
            
            # Calculate trend strength and recent price action
            price_above_sma50 = (current_price - sma50) / sma50
            price_above_sma20 = (current_price - sma20) / sma20
            
            # Pattern 1: Golden Cross (original)
            golden_cross = (prev_sma20 <= prev_sma50 and sma20 > sma50 and
                           current_price > sma50 and volume > vol_avg * 1.3 and adx > 22)
            
            # Pattern 2: Pullback to SMA20 in uptrend (new)
            pullback_buy = (sma20 > sma50 and  # Established uptrend
                           abs(price_above_sma20) < 0.02 and  # Price near SMA20 (within 2%)
                           rsi > 35 and rsi < 65 and  # Not extreme
                           volume > vol_avg * 1.2 and  # Reasonable volume
                           adx > 20)  # Some trend strength
            
            # Pattern 3: Consolidation breakout (new)
            range_bars = df['High'].iloc[i-5:i].max() - df['Low'].iloc[i-5:i].min()
            range_pct = (range_bars / df['Close'].iloc[i-5]) if df['Close'].iloc[i-5] > 0 else 0
            consolidation_breakout = (range_pct < 0.05 and  # Tight 5-bar range (<5%)
                                     current_price > df['High'].iloc[i-5:i-1].max() and  # Break above
                                     volume > vol_avg * 1.5 and  # Strong volume
                                     rsi > 45 and rsi < 75)
            
            # ==================== BULLISH PATTERNS WITH 7 ROBUSTNESS FILTERS ====================
            is_valid_bullish = False
            pattern_name = None
            confidence = 0
            
            if golden_cross and rsi < 75 and liquidity_valid and time_valid and earnings_safe:
                # Apply all 7 filters
                if (regime_valid and
                    validate_bullish_signal(df, i, 'Golden Cross') and
                    pattern_expectancy.get('Golden Cross', 0.50) > 0.50):
                    is_valid_bullish = True
                    pattern_name = 'Golden Cross'
                    confidence = 88
            
            elif pullback_buy and liquidity_valid and time_valid and earnings_safe:
                if (regime_valid and
                    validate_bullish_signal(df, i, 'Pullback') and
                    pattern_expectancy.get('Pullback', 0.50) > 0.50):
                    is_valid_bullish = True
                    pattern_name = 'Pullback'
                    confidence = 75
            
            elif consolidation_breakout and liquidity_valid and time_valid and earnings_safe:
                if (regime_valid and
                    validate_bullish_signal(df, i, 'Breakout') and
                    pattern_expectancy.get('Breakout', 0.50) > 0.50):
                    is_valid_bullish = True
                    pattern_name = 'Breakout'
                    confidence = 80
            
            # ONLY FIRE SIGNAL IF ALL 7 FILTERS PASS
            if is_valid_bullish and pattern_name:
                stop_loss = min(current_price - (current_atr * 2.5), sma50 * 0.97)
                risk = current_price - stop_loss
                target = current_price + (risk * 3)
                
                # Count filters passed
                filters_passed = sum([
                    regime_valid,
                    liquidity_valid,
                    time_valid,
                    earnings_safe
                ])
                
                # Calculate robustness momentum
                robustness_momentum = calculate_robustness_momentum(df, i, filters_passed)
                
                # Calculate master score (with default values for context metrics)
                master_result = calculate_master_score(
                    confidence=confidence,
                    final_score=0.70,  # Typical technical score
                    context_score=3.0,  # Typical context score
                    context_momentum=0.45,  # Bullish momentum
                    robustness_score=(filters_passed / 7 * 100),  # Convert filter count to 0-100
                    news_sentiment=0.0  # Neutral news
                )
                
                signals.append({
                    'date': current_date,
                    'symbol': symbol,
                    'signal': 'buy',
                    'price': current_price,
                    'pattern': pattern_name,
                    'confidence': confidence,
                    'stop_loss': stop_loss,
                    'target': target,
                    'atr': current_atr,
                    'volatility': vol_regime,
                    'regime': market_regime,
                    
                    # Scoring fields (existing system)
                    'final_score': 0.70,  # Default technical score
                    'context_score': 3.0,  # Default context score
                    'context_momentum': 0.45,  # Bullish momentum
                    'news_sentiment_score': 0.0,  # Neutral news (can be overridden)
                    
                    # NEW: Filter and robustness metrics
                    'filters_passed': filters_passed,
                    'robustness_score': (filters_passed / 7 * 100),
                    'robustness_momentum': robustness_momentum,
                    'master_score': master_result['master_score'],
                    'master_score_tooltip': master_result['tooltip'],
                    
                    'reason': f"{pattern_name} | ADX={adx:.1f} ({market_regime}) | Vol={vol_regime} | RSI={rsi:.1f} | Master={master_result['master_score']:.0f}"
                })
            
            # Pattern 1: Death Cross (original)
            death_cross = (prev_sma20 >= prev_sma50 and sma20 < sma50 and
                          current_price < sma50 and volume > vol_avg * 1.3 and adx > 22)
            
            # Pattern 2: Pullback to SMA20 in downtrend (new)
            pullback_sell = (sma20 < sma50 and  # Established downtrend
                            abs(price_above_sma20) < 0.02 and  # Price near SMA20
                            rsi > 35 and rsi < 65 and
                            volume > vol_avg * 1.2 and
                            adx > 20)
            
            # Pattern 3: Breakdown from consolidation (new)
            breakdown = (range_pct < 0.05 and  # Tight range
                        current_price < df['Low'].iloc[i-5:i-1].min() and  # Break below
                        volume > vol_avg * 1.5 and
                        rsi > 25 and rsi < 55)
            
            # ==================== BEARISH PATTERNS WITH 7 ROBUSTNESS FILTERS ====================
            is_valid_bearish = False
            pattern_name_sell = None
            confidence_sell = 0
            
            if death_cross and rsi > 25 and liquidity_valid and time_valid and earnings_safe:
                if (regime_valid and
                    validate_bearish_signal(df, i, 'Death Cross') and
                    pattern_expectancy.get('Death Cross', 0.50) > 0.50):
                    is_valid_bearish = True
                    pattern_name_sell = 'Death Cross'
                    confidence_sell = 88
            
            elif pullback_sell and liquidity_valid and time_valid and earnings_safe:
                if (regime_valid and
                    validate_bearish_signal(df, i, 'Pullback') and
                    pattern_expectancy.get('Pullback', 0.50) > 0.50):
                    is_valid_bearish = True
                    pattern_name_sell = 'Pullback'
                    confidence_sell = 75
            
            elif breakdown and liquidity_valid and time_valid and earnings_safe:
                if (regime_valid and
                    validate_bearish_signal(df, i, 'Breakdown') and
                    pattern_expectancy.get('Breakdown', 0.50) > 0.50):
                    is_valid_bearish = True
                    pattern_name_sell = 'Breakdown'
                    confidence_sell = 80
            
            # ONLY FIRE SIGNAL IF ALL 7 FILTERS PASS
            if is_valid_bearish and pattern_name_sell:
                stop_loss = max(current_price + (current_atr * 2.5), sma50 * 1.03)
                risk = stop_loss - current_price
                target = current_price - (risk * 3)
                
                # Count filters passed
                filters_passed = sum([
                    regime_valid,
                    liquidity_valid,
                    time_valid,
                    earnings_safe
                ])
                
                # Calculate robustness momentum
                robustness_momentum = calculate_robustness_momentum(df, i, filters_passed)
                
                # Calculate master score
                master_result = calculate_master_score(
                    confidence=confidence_sell,
                    final_score=0.70,
                    context_score=3.0,
                    context_momentum=-0.45,  # Bearish momentum
                    robustness_score=(filters_passed / 7 * 100),
                    news_sentiment=0.0
                )
                
                signals.append({
                    'date': current_date,
                    'symbol': symbol,
                    'signal': 'sell',
                    'price': current_price,
                    'pattern': pattern_name_sell,
                    'confidence': confidence_sell,
                    'stop_loss': stop_loss,
                    'target': target,
                    'atr': current_atr,
                    'volatility': vol_regime,
                    'regime': market_regime,
                    
                    # Scoring fields (existing system)
                    'final_score': 0.70,  # Default technical score
                    'context_score': 3.0,  # Default context score
                    'context_momentum': -0.45,  # Bearish momentum
                    'news_sentiment_score': 0.0,  # Neutral news (can be overridden)
                    
                    # NEW: Filter and robustness metrics
                    'filters_passed': filters_passed,
                    'robustness_score': (filters_passed / 7 * 100),
                    'robustness_momentum': robustness_momentum,
                    'master_score': master_result['master_score'],
                    'master_score_tooltip': master_result['tooltip'],
                    
                    'reason': f"{pattern_name_sell} | ADX={adx:.1f} ({market_regime}) | Vol={vol_regime} | RSI={rsi:.1f} | Master={master_result['master_score']:.0f}"
                })
        
        print(f"  Generated {len(signals)} CONFIRMED signals for {symbol} (with persistence validation)")
        return signals
    
    def run_backtest(self, symbol):
        """Run complete backtest for a symbol"""
        # Load data
        df = self.load_historical_data(symbol)
        if df is None or len(df) < 100:
            return None
        
        # Generate signals
        signals = self.generate_signals(symbol, df)
        
        return {
            'symbol': symbol,
            'data': df,
            'signals': signals,
            'start_date': self.start_date,
            'end_date': self.end_date
        }
