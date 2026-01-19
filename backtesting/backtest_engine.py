"""
Backtesting Engine - Replays historical data and generates signals
"""

import pandas as pd
import yfinance as yf
from datetime import datetime, timedelta
from indicators.patterns import detect_patterns
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


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
        Generate entry/exit signals with improved filters
        
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
            
            # Calculate trend strength and recent price action
            price_above_sma50 = (current_price - sma50) / sma50
            price_above_sma20 = (current_price - sma20) / sma20
            
            # Pattern 1: Golden Cross (original)
            golden_cross = (prev_sma20 <= prev_sma50 and sma20 > sma50 and
                           current_price > sma50 and volume > vol_avg * 1.1 and adx > 20)
            
            # Pattern 2: Pullback to SMA20 in uptrend (new)
            pullback_buy = (sma20 > sma50 and  # Established uptrend
                           abs(price_above_sma20) < 0.02 and  # Price near SMA20 (within 2%)
                           rsi > 35 and rsi < 65 and  # Not extreme
                           volume > vol_avg * 0.9 and  # Reasonable volume
                           adx > 18)  # Some trend strength
            
            # Pattern 3: Consolidation breakout (new)
            range_bars = df['High'].iloc[i-5:i].max() - df['Low'].iloc[i-5:i].min()
            range_pct = (range_bars / df['Close'].iloc[i-5]) if df['Close'].iloc[i-5] > 0 else 0
            consolidation_breakout = (range_pct < 0.05 and  # Tight 5-bar range (<5%)
                                     current_price > df['High'].iloc[i-5:i-1].max() and  # Break above
                                     volume > vol_avg * 1.3 and  # Strong volume
                                     rsi > 45 and rsi < 75)
            
            # BULLISH ENTRY: Any of 3 patterns
            if (golden_cross or pullback_buy or consolidation_breakout) and rsi < 75:
                
                signal_type = 'buy'
                pattern_name = 'Golden Cross' if golden_cross else 'Pullback' if pullback_buy else 'Breakout'
                stop_loss = min(current_price - (current_atr * 2.5), sma50 * 0.97)
                risk = current_price - stop_loss
                target = current_price + (risk * 3)
                confidence = 75 if golden_cross else 65
                
                signals.append({
                    'date': current_date,
                    'symbol': symbol,
                    'signal': signal_type,
                    'price': current_price,
                    'pattern': pattern_name,
                    'confidence': confidence,
                    'stop_loss': stop_loss,
                    'target': target,
                    'atr': current_atr,
                    'reason': f"{pattern_name} with RSI {rsi:.1f}"
                })
            
            # Pattern 1: Death Cross (original)
            death_cross = (prev_sma20 >= prev_sma50 and sma20 < sma50 and
                          current_price < sma50 and volume > vol_avg * 1.1 and adx > 20)
            
            # Pattern 2: Pullback to SMA20 in downtrend (new)
            pullback_sell = (sma20 < sma50 and  # Established downtrend
                            abs(price_above_sma20) < 0.02 and  # Price near SMA20
                            rsi > 35 and rsi < 65 and
                            volume > vol_avg * 0.9 and
                            adx > 18)
            
            # Pattern 3: Breakdown from consolidation (new)
            breakdown = (range_pct < 0.05 and  # Tight range
                        current_price < df['Low'].iloc[i-5:i-1].min() and  # Break below
                        volume > vol_avg * 1.3 and
                        rsi > 25 and rsi < 55)
            
            # BEARISH ENTRY: Any of 3 patterns
            if (death_cross or pullback_sell or breakdown) and rsi > 25:
                
                signal_type = 'sell'
                pattern_name = 'Death Cross' if death_cross else 'Pullback' if pullback_sell else 'Breakdown'
                stop_loss = max(current_price + (current_atr * 2.5), sma50 * 1.03)
                risk = stop_loss - current_price
                target = current_price - (risk * 3)
                confidence = 75 if death_cross else 65
                
                signals.append({
                    'date': current_date,
                    'symbol': symbol,
                    'signal': signal_type,
                    'price': current_price,
                    'pattern': pattern_name,
                    'confidence': confidence,
                    'stop_loss': stop_loss,
                    'target': target,
                    'atr': current_atr,
                    'reason': f"{pattern_name} with RSI {rsi:.1f}"
                })
        
        print(f"  Generated {len(signals)} signals for {symbol}")
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
