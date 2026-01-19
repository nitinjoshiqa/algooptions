"""
Intraday Backtest Engine - Tests screener logic on historical intraday data

This engine:
1. Downloads 5-minute historical data (yfinance or Breeze)
2. Replays screener logic bar-by-bar
3. Enters when screener triggers actionable signal
4. Exits same-day or at target/stop
5. Measures realistic intraday performance

Usage:
    python run_intraday_backtest.py --universe nifty --days 60 --output intraday_results.html
"""

import pandas as pd
import yfinance as yf
from datetime import datetime, timedelta
from dataclasses import dataclass
from typing import List, Dict
from core.scoring_engine import BearnessScoringEngine

# Breeze API imports
try:
    from breeze_connect import BreezeConnect
    from breeze_details import API_KEY, API_SECRET, SESSION_TOKEN
    BREEZE_AVAILABLE = True
except ImportError:
    BREEZE_AVAILABLE = False
    print("[INFO] Breeze API not available, using yfinance only")


@dataclass
class IntradayTrade:
    """Single intraday trade record"""
    entry_datetime: pd.Timestamp
    exit_datetime: pd.Timestamp
    symbol: str
    direction: str  # 'long' or 'short'
    entry_price: float
    exit_price: float
    stop_loss: float
    target: float
    shares: int
    pnl: float
    pnl_pct: float
    r_multiple: float
    exit_reason: str  # 'TARGET', 'STOP', 'EOD'
    signal_score: float
    confidence: float
    pattern: str
    hold_minutes: int


class IntradayBacktestEngine:
    """Backtest intraday screener signals on historical 5-minute data"""
    
    def __init__(self, initial_capital=100000, risk_per_trade=0.01, commission=0.0005, use_breeze=True):
        """
        Args:
            initial_capital: Starting capital
            risk_per_trade: Risk % per trade (default 1% for intraday)
            commission: Commission % (default 0.05%)
            use_breeze: Use Breeze API for data (fallback to yfinance)
        """
        self.initial_capital = initial_capital
        self.capital = initial_capital
        self.risk_per_trade = risk_per_trade
        self.commission = commission
        self.trades = []
        self.closed_trades = []  # Track closed trades for results
        self.entry_rsi_values = []  # Track RSI at entry for analysis
        self.use_breeze = use_breeze and BREEZE_AVAILABLE
        
        # Slippage modeling: realistic for liquid stocks
        self.entry_slippage_pct = 0.0005  # 0.05% entry slippage
        self.exit_slippage_pct = 0.001    # 0.10% exit slippage
        
        # Entry confirmation tracking (wait for signal to persist)
        self.pending_signal = None  # Track pending signal for confirmation
        
        # Initialize Breeze connection
        self.breeze = None
        if self.use_breeze:
            try:
                self.breeze = BreezeConnect(api_key=API_KEY)
                self.breeze.generate_session(api_secret=API_SECRET, session_token=SESSION_TOKEN)
                print("[INFO] Breeze API connected successfully")
            except Exception as e:
                print(f"[WARN] Breeze connection failed: {e}. Using yfinance.")
                self.use_breeze = False
        
        # Initialize screener engine - ACTUAL SCREENER LOGIC
        self.screener = BearnessScoringEngine(
            mode='intraday',
            use_yf=not self.use_breeze,
            force_yf=not self.use_breeze,
            quick_mode=False
        )
    
    def download_intraday_data(self, symbol, days=60):
        """
        Download 5-minute historical data
        
        Tries Breeze API first, falls back to yfinance
        """
        print(f"  Downloading {days} days of 5-minute data for {symbol}...")
        
        # Try Breeze first
        if self.use_breeze and self.breeze:
            try:
                df = self._download_breeze_data(symbol, days)
                if df is not None and not df.empty:
                    print(f"  Loaded {len(df)} bars from Breeze")
                    return df
            except Exception as e:
                print(f"  [!] Breeze failed: {e}, trying yfinance...")
        
        # Fallback to yfinance
        try:
            ticker = yf.Ticker(f"{symbol}.NS")
            
            # yfinance supports max 60 days for 5-minute interval
            days = min(days, 60)
            start_date = datetime.now() - timedelta(days=days)
            
            df = ticker.history(start=start_date, interval='5m')
            
            if df.empty:
                print(f"  [!] No data for {symbol}")
                return None
            
            print(f"  Loaded {len(df)} bars from yfinance")
            return df
        
        except Exception as e:
            print(f"  [X] Error: {e}")
            return None
    
    def _download_breeze_data(self, symbol, days=60):
        """Download data from Breeze API"""
        if not self.breeze:
            return None
        
        # Calculate date range
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)
        
        # Breeze API call
        response = self.breeze.get_historical_data_v2(
            interval="5minute",
            from_date=start_date.strftime("%Y-%m-%d"),
            to_date=end_date.strftime("%Y-%m-%d"),
            stock_code=symbol,
            exchange_code="NSE",
            product_type="cash"
        )
        
        if not response or response.get('Status') != 200:
            return None
        
        # Convert to DataFrame
        data = response.get('Success', [])
        if not data:
            return None
        
        df = pd.DataFrame(data)
        df['datetime'] = pd.to_datetime(df['datetime'])
        df.set_index('datetime', inplace=True)
        
        # Rename columns to match yfinance format
        df.rename(columns={
            'open': 'Open',
            'high': 'High',
            'low': 'Low',
            'close': 'Close',
            'volume': 'Volume'
        }, inplace=True)
        
        return df
    
    def calculate_position_size(self, price, stop_loss):
        """Calculate shares based on risk"""
        risk_amount = self.capital * self.risk_per_trade
        risk_per_share = abs(price - stop_loss)
        
        if risk_per_share == 0:
            return 0
        
        shares = int(risk_amount / risk_per_share)
        
        # Don't use more than 20% capital
        max_shares = int((self.capital * 0.2) / price)
        shares = min(shares, max_shares)
        
        return shares
    
    def should_enter_trade(self, score, confidence, pattern, rsi=50):
        """
        Determine if screener signal is actionable
        
        Entry Rules - TOP 10% HIGH-CONVICTION SIGNALS:
        - Bearish: score >= 0.45 and confidence >= 35 (top 10% bearish)
        - Bullish: score <= -0.45 and confidence >= 35 (top 10% bullish)
        
        Score ±0.45 already captures RSI extremes indirectly - no additional RSI filter needed.
        This allows entries closer to momentum turning points.
        """
        # Score-based filtering only - score ±0.45 already incorporates RSI signals
        # TOP 10% SIGNALS: Score >= 0.45 or <= -0.45, confidence >= 35 (strict quality)
        # This filters to highest conviction signals with better accuracy
        if score >= 0.45 and confidence >= 35:
            return 'short'  # Top bearish signals
        elif score <= -0.45 and confidence >= 35:
            return 'long'   # Top bullish signals
        return None
    
    def run_backtest(self, symbol, days=60):
        """
        Backtest intraday strategy on historical data
        
        Process:
        1. Download 5-minute bars
        2. Group by day
        3. For each day, scan bars for screener signals
        4. Enter when signal triggers
        5. Exit at target/stop/EOD
        """
        print(f"\n[Backtesting {symbol}]")
        
        # Download data
        df = self.download_intraday_data(symbol, days)
        if df is None or len(df) < 100:
            return
        
        # Prepare data
        df['date'] = df.index.date
        df['time'] = df.index.time
        
        # Group by trading day
        trading_days = df['date'].unique()
        
        print(f"  Testing {len(trading_days)} trading days...")
        
        active_trade = None
        signals_generated = 0
        trades_entered = 0
        
        for day in trading_days:
            day_data = df[df['date'] == day].copy()
            
            if len(day_data) < 10:  # Need minimum bars
                continue

            # Compute Opening Range (first 30 minutes = 6 bars)
            or_bars_count = min(6, len(day_data))
            or_high = day_data.iloc[:or_bars_count]['High'].max()
            or_low = day_data.iloc[:or_bars_count]['Low'].min()
            
            # Scan each bar for entry signal (if no active trade)
            for i in range(10, len(day_data)):  # Skip first 10 bars (market opening)
                current_bar = day_data.iloc[i]
                current_time = day_data.index[i]
                current_price = current_bar['Close']
                
                # --- EXIT LOGIC (if in trade) ---
                if active_trade:
                    high = current_bar['High']
                    low = current_bar['Low']
                    
                    exit_price = None
                    exit_reason = None
                    
                    # Calculate current P&L and risk for trailing stop
                    entry_price = active_trade['entry_price']
                    risk_per_share = abs(entry_price - active_trade['stop_loss'])
                    
                    if active_trade['direction'] == 'long':
                        profit = current_price - entry_price
                        
                        # PARTIAL PROFIT-TAKING (improvement #4): Exit 50% at 1R
                        if not active_trade.get('partial_exit_done') and profit >= risk_per_share:
                            half_shares = active_trade['shares'] // 2
                            if half_shares > 0:
                                # Exit 50% of position at 1R profit
                                partial_exit_price = entry_price + risk_per_share
                                # Apply exit slippage
                                partial_exit_price_with_slippage = partial_exit_price * (1 - self.exit_slippage_pct)
                                partial_pnl = half_shares * (partial_exit_price_with_slippage - entry_price)
                                self.capital += partial_pnl
                                active_trade['shares'] -= half_shares
                                active_trade['partial_exit_done'] = True
                                # Move stop to breakeven after partial exit
                                active_trade['stop_loss'] = entry_price
                        
                        # Trail stop after +2R (for remaining 50%)
                        elif profit >= risk_per_share * 2.0 and active_trade.get('partial_exit_done'):
                            trail_stop = entry_price + (risk_per_share * 1.0)  # Lock 1R
                            active_trade['stop_loss'] = max(active_trade['stop_loss'], trail_stop)
                        
                        if high >= active_trade['target']:
                            exit_price = active_trade['target']
                            exit_reason = 'TARGET'
                        elif low <= active_trade['stop_loss']:
                            exit_price = active_trade['stop_loss']
                            exit_reason = 'STOP'
                    else:  # short
                        profit = entry_price - current_price
                        
                        # PARTIAL PROFIT-TAKING: Exit 50% at 1R
                        if not active_trade.get('partial_exit_done') and profit >= risk_per_share:
                            half_shares = active_trade['shares'] // 2
                            if half_shares > 0:
                                # Exit 50% of position at 1R profit
                                partial_exit_price = entry_price - risk_per_share
                                # Apply exit slippage
                                partial_exit_price_with_slippage = partial_exit_price * (1 + self.exit_slippage_pct)
                                partial_pnl = half_shares * (entry_price - partial_exit_price_with_slippage)
                                self.capital += partial_pnl
                                active_trade['shares'] -= half_shares
                                active_trade['partial_exit_done'] = True
                                # Move stop to breakeven after partial exit
                                active_trade['stop_loss'] = entry_price
                        
                        # Trail stop after +2R (for remaining 50%)
                        elif profit >= risk_per_share * 2.0 and active_trade.get('partial_exit_done'):
                            trail_stop = entry_price - (risk_per_share * 1.0)  # Lock 1R
                            active_trade['stop_loss'] = min(active_trade['stop_loss'], trail_stop)
                        
                        if low <= active_trade['target']:
                            exit_price = active_trade['target']
                            exit_reason = 'TARGET'
                        elif high >= active_trade['stop_loss']:
                            exit_price = active_trade['stop_loss']
                            exit_reason = 'STOP'
                    
                    # VWAP recross exit: DISABLED for swing trading
                    # Let stops and targets manage risk - VWAP is intraday metric
                    # if exit_price is None:
                    #     entry_price = active_trade['entry_price']
                    #     current_pnl = (current_price - entry_price) if active_trade['direction'] == 'long' else (entry_price - current_price)
                    #     if current_pnl < 0:
                    #         session_bars = day_data.iloc[:i+1]
                    #         vwap_now = self._calculate_vwap(session_bars)
                    #         if active_trade['direction'] == 'long' and current_price < vwap_now:
                    #             exit_price = current_price
                    #             exit_reason = 'VWAP_RECROSS'
                    #         elif active_trade['direction'] == 'short' and current_price > vwap_now:
                    #             exit_price = current_price
                    #             exit_reason = 'VWAP_RECROSS'

                    # Time exit: Max 5 trading days (swing trade holding limit)
                    bars_held = i - active_trade.get('entry_bar_idx', 0)
                    max_bars = 375  # ~5 days of 5-min bars (75 bars/day * 5 days)
                    if bars_held >= max_bars:
                        if exit_price is None:
                            exit_price = current_price
                            exit_reason = 'TIME_EXIT'
                    
                    # Close trade if exit conditions are met, or if no shares left after partial exit
                    if exit_price or active_trade['shares'] <= 0:
                        if exit_price:
                            self._close_trade(active_trade, exit_price, exit_reason, current_time)
                        else:
                            # Shares were fully exited via partial exits, close with current price
                            self._close_trade(active_trade, current_price, 'PARTIAL_EXIT_COMPLETE', current_time)
                        active_trade = None
                        continue
                
                # --- ENTRY LOGIC (if no active trade) ---
                if not active_trade:
                    # Skip if too close to EOD (less than 2 hours left)
                    if current_time.hour >= 13:
                        continue
                    
                    # Run screener on recent bars
                    # Convert recent bars to screener format
                    recent_bars = day_data.iloc[max(0, i-78):i+1]  # Last 78 bars (6.5 hours)
                    
                    if len(recent_bars) < 20:
                        continue
                    
                    # Build candles dict for screener
                    candles = []
                    for idx, row in recent_bars.iterrows():
                        candles.append({
                            'open': row['Open'],
                            'high': row['High'],
                            'low': row['Low'],
                            'close': row['Close'],
                            'volume': row['Volume']
                        })
                    
                    # USE ACTUAL SCREENER LOGIC
                    # Call the real BearnessScoringEngine for exact same logic as nifty_bearnness_v2.py
                    try:
                        # Prepare candles data for screener
                        candles_data = {
                            'intraday': candles,
                            'swing': None,
                            'longterm': None,
                        }
                        
                        # Get current price
                        price = current_price
                        
                        # Compute scores using actual screener engine
                        scores_by_tf = self.screener._compute_timeframe_scores(candles_data, price, symbol)
                        
                        if 'intraday' in scores_by_tf:
                            score_result = scores_by_tf['intraday']
                            score = score_result.get('final_score', 0)
                            confidence = score_result.get('confidence', 40)
                            rsi_val = score_result.get('rsi', 50)
                        else:
                            # Fallback if screener fails
                            raise Exception("No intraday score computed")
                        
                    except Exception as e:
                        # Fallback to simple scoring if screener fails
                        closes = [c['close'] for c in candles]
                        volumes = [c['volume'] for c in candles]
                        
                        sma20 = sum(closes[-20:]) / 20 if len(closes) >= 20 else closes[-1]
                        rsi_val = self._calculate_rsi(closes)
                        vol_avg = sum(volumes[-20:]) / 20 if len(volumes) >= 20 else volumes[-1]
                        
                        # RSI-based scoring (higher weight)
                        if rsi_val < 30:
                            rsi_component = -0.5  # Oversold - strong bullish
                        elif rsi_val < 40:
                            rsi_component = -0.3  # Bullish
                        elif rsi_val < 50:
                            rsi_component = -0.1  # Mild bullish
                        elif rsi_val < 60:
                            rsi_component = 0.1   # Mild bearish
                        elif rsi_val < 70:
                            rsi_component = 0.3   # Bearish
                        else:
                            rsi_component = 0.5   # Overbought - strong bearish
                        
                        # Price/SMA component
                        price_component = 0
                        if current_price > sma20 * 1.01:
                            price_component = -0.2  # Bullish
                        elif current_price < sma20 * 0.99:
                            price_component = 0.2   # Bearish
                        
                        # Volume component
                        vol_component = 0
                        if volumes[-1] > vol_avg * 1.3:
                            vol_component = -0.1 if current_price > sma20 else 0.1
                        
                        # Weighted blend: RSI 50%, Price 30%, Volume 20%
                        score = (rsi_component * 0.5 + price_component * 0.3 + vol_component * 0.2)
                        
                        # Confidence based on RSI range and signal strength
                        if 40 <= rsi_val <= 60 and abs(score) > 0.3:
                            confidence = 75
                        elif 35 <= rsi_val <= 65 and abs(score) > 0.2:
                            confidence = 65
                        elif 30 <= rsi_val <= 70:
                            confidence = 55
                        else:
                            confidence = 40
                    
                    # Calculate RSI for filter
                    closes_for_rsi = [c['close'] for c in candles]
                    rsi_val = self._calculate_rsi(closes_for_rsi, period=14)
                    
                    # Check if actionable (score-based with RSI filter)
                    direction = self.should_enter_trade(score, confidence, 'Momentum', rsi=rsi_val)
                    
                    if direction:
                        signals_generated += 1
                        
                        # For TOP 10% signals, skip additional filters - signal quality is already high
                        # Just apply basic sanity checks
                        if i < or_bars_count:
                            continue

                        # Session VWAP using all bars up to current bar
                        session_bars = day_data.iloc[:i+1]
                        vwap = self._calculate_vwap(session_bars)

                        # For high-conviction signals (score >= 0.45), VWAP/EMA filters are optional
                        # Just require minimum volume to avoid illiquid bars
                        recent_vols = [c['volume'] for c in candles[-20:] if c.get('volume', 0) > 0]
                        avg_vol = sum(recent_vols) / len(recent_vols) if recent_vols else 1
                        current_vol = current_bar.get('Volume', 0)
                        min_volume_ok = current_vol >= (avg_vol * 0.5)  # Relaxed: 50% of average volume
                        
                        if not min_volume_ok:
                            continue  # Skip if volume too low

                        # TREND ALIGNMENT CHECK (improvement #3)
                        # Only trade if daily trend aligns with signal direction
                        # Use EMA slope as trend proxy: positive = uptrend, negative = downtrend
                        closes_recent = [c['close'] for c in candles]
                        ema_slope = self._ema_slope(closes_recent, period=20, lookback=5)
                        
                        if direction == 'long' and ema_slope < 0:
                            continue  # Don't go long in downtrend
                        if direction == 'short' and ema_slope > 0:
                            continue  # Don't go short in uptrend

                        # Calculate SL/Target with regime-aware risk/reward
                        atr = self._calculate_atr(candles[-14:]) if len(candles) >= 14 else current_price * 0.01
                        volatility_pct = (atr / current_price) * 100 if current_price > 0 else 0.0

                        # Regime classification - 4x ATR stop, 4x ATR target (1:1 R:R)
                        # Reverted: 4x ATR for both stop and target for higher accuracy
                        regime = 'swing'
                        sl_mult, tgt_mult = 4.0, 4.0   # 1:1 risk-to-reward ratio

                        if direction == 'long':
                            stop_loss = current_price - (atr * sl_mult)
                            target = current_price + (atr * tgt_mult)
                        else:
                            stop_loss = current_price + (atr * sl_mult)
                            target = current_price - (atr * tgt_mult)

                        # Position size
                        shares = self.calculate_position_size(current_price, stop_loss)
                        
                        if shares > 0:
                            position_cost = shares * current_price
                            
                            if position_cost <= self.capital * 0.2:  # Max 20% per trade
                                trades_entered += 1
                                
                                # Apply slippage to entry price
                                if direction == 'long':
                                    entry_price_with_slippage = current_price * (1 + self.entry_slippage_pct)
                                else:  # short
                                    entry_price_with_slippage = current_price * (1 - self.entry_slippage_pct)
                                
                                active_trade = {
                                    'entry_time': current_time,
                                    'entry_price': entry_price_with_slippage,
                                    'entry_bar_idx': i,
                                    'stop_loss': stop_loss,
                                    'target': target,
                                    'shares': shares,
                                    'direction': direction,
                                    'score': score,
                                    'confidence': confidence,
                                    'pattern': 'Momentum',
                                    'symbol': symbol,  # Track symbol
                                    'entry_rsi': rsi_val  # Track RSI at entry
                                }
        
        # Close any open trade at last bar
        if active_trade:
            last_bar = day_data.iloc[-1]
            last_time = day_data.index[-1]
            self._close_trade(active_trade, last_bar['Close'], 'TIME_EXIT', last_time)
        
        print(f"  Signals: {signals_generated} | Trades: {trades_entered}")
        
        # Return results for aggregation
        return {
            'symbol': symbol,
            'trades': self.closed_trades,
            'signals': signals_generated,
            'trades_entered': trades_entered,
            'capital': self.capital
        }
    
    def _calculate_rsi(self, closes, period=14):
        """Calculate RSI"""
        if len(closes) < period + 1:
            return 50
        
        deltas = [closes[i] - closes[i-1] for i in range(1, len(closes))]
        gains = [d if d > 0 else 0 for d in deltas]
        losses = [-d if d < 0 else 0 for d in deltas]
        
        avg_gain = sum(gains[-period:]) / period
        avg_loss = sum(losses[-period:]) / period
        
        if avg_loss == 0:
            return 100
        
        rs = avg_gain / avg_loss
        rsi = 100 - (100 / (1 + rs))
        return rsi

    def _calculate_vwap(self, bars_df):
        """Calculate session VWAP up to current bar"""
        typical = (bars_df['High'] + bars_df['Low'] + bars_df['Close']) / 3.0
        cum_tp_vol = (typical * bars_df['Volume']).cumsum()
        cum_vol = bars_df['Volume'].cumsum()
        vwap_series = cum_tp_vol / cum_vol.replace(0, pd.NA)
        return float(vwap_series.iloc[-1]) if len(vwap_series) else float(typical.iloc[-1])

    def _ema_slope(self, closes, period=20, lookback=5):
        """Calculate EMA slope over lookback bars (positive = uptrend)"""
        if len(closes) < period + lookback + 1:
            return 0.0
        s = pd.Series(closes)
        ema = s.ewm(span=period, adjust=False).mean()
        return float(ema.iloc[-1] - ema.iloc[-(lookback+1)])
    
    def _calculate_atr(self, candles, period=14):
        """Calculate ATR"""
        if len(candles) < 2:
            return candles[-1]['close'] * 0.01
        
        trs = []
        for i in range(1, len(candles)):
            high_low = candles[i]['high'] - candles[i]['low']
            high_close = abs(candles[i]['high'] - candles[i-1]['close'])
            low_close = abs(candles[i]['low'] - candles[i-1]['close'])
            trs.append(max(high_low, high_close, low_close))
        
        return sum(trs[-period:]) / min(period, len(trs)) if trs else candles[-1]['close'] * 0.01
    
    def _close_trade(self, trade, exit_price, exit_reason, exit_time):
        """Close active trade and record"""
        # Apply slippage to exit price
        if trade['direction'] == 'long':
            exit_price_with_slippage = exit_price * (1 - self.exit_slippage_pct)
        else:  # short
            exit_price_with_slippage = exit_price * (1 + self.exit_slippage_pct)
        
        # Calculate P&L
        entry_commission = trade['shares'] * trade['entry_price'] * self.commission
        exit_commission = trade['shares'] * exit_price_with_slippage * self.commission
        
        if trade['direction'] == 'long':
            gross_pnl = trade['shares'] * (exit_price_with_slippage - trade['entry_price'])
        else:
            gross_pnl = trade['shares'] * (trade['entry_price'] - exit_price_with_slippage)
        
        net_pnl = gross_pnl - entry_commission - exit_commission
        
        # R-multiple
        risk_per_share = abs(trade['entry_price'] - trade['stop_loss'])
        total_risk = risk_per_share * trade['shares']
        r_multiple = net_pnl / total_risk if total_risk > 0 else 0
        
        # Update capital
        self.capital += net_pnl
        
        # Record trade
        hold_minutes = int((exit_time - trade['entry_time']).total_seconds() / 60)
        hold_bars = 0  # Default to 0 if we don't have entry_bar_idx
        
        trade_obj = IntradayTrade(
            entry_datetime=trade['entry_time'],
            exit_datetime=exit_time,
            symbol=trade.get('symbol', 'UNKNOWN'),
            direction=trade['direction'],
            entry_price=trade['entry_price'],
            exit_price=exit_price_with_slippage,
            stop_loss=trade['stop_loss'],
            target=trade['target'],
            shares=trade['shares'],
            pnl=net_pnl,
            pnl_pct=(net_pnl / (trade['shares'] * trade['entry_price'])) * 100,
            r_multiple=r_multiple,
            exit_reason=exit_reason,
            signal_score=trade.get('score', 0),
            confidence=trade.get('confidence', 0),
            pattern=trade.get('pattern', 'Unknown'),
            hold_minutes=hold_minutes
        )
        
        self.trades.append(trade_obj)
        self.closed_trades.append({
            'symbol': trade.get('symbol', 'UNKNOWN'),
            'entry_price': trade['entry_price'],
            'exit_price': exit_price_with_slippage,
            'pnl': net_pnl,
            'exit_reason': exit_reason,
            'duration_bars': hold_bars,
            'entry_rsi': trade.get('entry_rsi', None)  # Track RSI at entry
        })
    
    def get_summary(self):
        """Get summary statistics"""
        if not self.trades:
            return {
                'total_trades': 0,
                'winning_trades': 0,
                'losing_trades': 0,
                'win_rate': 0.0,
                'total_pnl': 0.0,
                'avg_win': 0.0,
                'avg_loss': 0.0,
                'profit_factor': 0.0,
                'avg_r_multiple': 0.0,
                'final_capital': self.initial_capital,
                'return_pct': 0.0,
                'avg_hold_minutes': 0.0,
                'target_exits': 0,
                'stop_exits': 0,
                'time_exits': 0,
                'vwap_exits': 0
            }
        
        winners = [t for t in self.trades if t.pnl > 0]
        losers = [t for t in self.trades if t.pnl <= 0]
        
        total_pnl = sum(t.pnl for t in self.trades)
        sum_wins = sum(t.pnl for t in winners)
        sum_losses = sum(t.pnl for t in losers)
        
        return {
            'total_trades': len(self.trades),
            'winning_trades': len(winners),
            'losing_trades': len(losers),
            'win_rate': (len(winners) / len(self.trades)) * 100,
            'total_pnl': total_pnl,
            'avg_win': sum_wins / len(winners) if winners else 0,
            'avg_loss': sum_losses / len(losers) if losers else 0,
            'profit_factor': (sum_wins / abs(sum_losses)) if sum_losses != 0 else 0,
            'avg_r_multiple': sum(t.r_multiple for t in self.trades) / len(self.trades),
            'final_capital': self.initial_capital + total_pnl,
            'return_pct': (total_pnl / self.initial_capital) * 100,
            'avg_hold_minutes': sum(t.hold_minutes for t in self.trades) / len(self.trades),
            'target_exits': len([t for t in self.trades if t.exit_reason == 'TARGET']),
            'stop_exits': len([t for t in self.trades if t.exit_reason == 'STOP']),
            'time_exits': len([t for t in self.trades if t.exit_reason == 'TIME_EXIT']),
            'vwap_exits': len([t for t in self.trades if t.exit_reason == 'VWAP_RECROSS'])
        }
