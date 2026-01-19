"""
Trade Simulator - Executes trades and tracks P&L
"""

import pandas as pd
from dataclasses import dataclass
from typing import List, Dict


@dataclass
class Trade:
    """Individual trade record"""
    entry_date: pd.Timestamp
    exit_date: pd.Timestamp
    symbol: str
    direction: str  # 'long' or 'short'
    entry_price: float
    exit_price: float
    stop_loss: float
    target: float
    shares: int
    pnl: float
    pnl_pct: float
    r_multiple: float  # Risk/Reward ratio (P&L / Total Risk)
    exit_reason: str  # 'target', 'stop', 'time', 'manual'
    pattern: str
    confidence: int
    hold_days: int
    

class TradeSimulator:
    """Simulate trade execution with position sizing and exits"""
    
    def __init__(self, initial_capital=100000, risk_per_trade=0.02, commission=0.0005):
        """
        Args:
            initial_capital: Starting capital (default 1L)
            risk_per_trade: Risk % per trade (default 2%)
            commission: Commission % (default 0.05%)
        """
        self.initial_capital = initial_capital
        self.capital = initial_capital
        self.risk_per_trade = risk_per_trade
        self.commission = commission
        self.trades = []
        self.open_positions = {}
        
    def calculate_position_size(self, price, stop_loss):
        """Calculate shares to buy based on risk"""
        risk_amount = self.capital * self.risk_per_trade
        risk_per_share = abs(price - stop_loss)
        
        if risk_per_share == 0:
            return 0
            
        shares = int(risk_amount / risk_per_share)
        
        # Don't use more than 20% of capital per position
        max_shares = int((self.capital * 0.2) / price)
        shares = min(shares, max_shares)
        
        return shares
    
    def execute_trades(self, backtest_result):
        """
        Single-pass replay of trades through historical data
        
        - Opens ONE trade at a time per symbol
        - Replays candles forward chronologically  
        - Exits trades using SL or Target
        - Tracks R-multiple and realistic metrics
        - Properly tracks capital: Capital = Initial + Sum(Trade P&Ls)
        
        Args:
            backtest_result: Output from BacktestEngine.run_backtest()
        
        Returns:
            List of Trade objects (closed trades only)
        """
        symbol = backtest_result['symbol']
        df = backtest_result['data']
        signals = backtest_result['signals']
        
        # Sort signals chronologically
        signals = sorted(signals, key=lambda x: x['date'])
        symbol_trades = []  # Trades for this symbol only
        active_trade = None
        signal_idx = 0
        
        # Walk through each candle chronologically
        for i in range(len(df)):
            candle = df.iloc[i]
            date = df.index[i]
            high = candle['High']
            low = candle['Low']
            close = candle['Close']
            
            # ===== STEP 1: Check if active trade exits =====
            if active_trade:
                exit_price = None
                exit_reason = None
                
                if active_trade['direction'] == 'long':
                    # Long exit: SL first, then Target
                    if low <= active_trade['stop_loss']:
                        exit_price = active_trade['stop_loss']
                        exit_reason = 'SL'
                    elif high >= active_trade['target']:
                        exit_price = active_trade['target']
                        exit_reason = 'TARGET'
                else:  # short
                    # Short exit: SL first, then Target
                    if high >= active_trade['stop_loss']:
                        exit_price = active_trade['stop_loss']
                        exit_reason = 'SL'
                    elif low <= active_trade['target']:
                        exit_price = active_trade['target']
                        exit_reason = 'TARGET'
                
                # Partial profit at +1.5R, then move stop to breakeven
                if not active_trade.get('partial_taken', False) and active_trade.get('shares', 0) > 1:
                    entry_px = active_trade['entry_price']
                    r = active_trade['entry_risk']
                    if active_trade['direction'] == 'long':
                        threshold = entry_px + 1.5 * r
                        if high >= threshold:
                            part_shares = max(1, active_trade['shares'] // 2)
                            part_exit = threshold
                            # Realize partial P&L minus exit commission for partial
                            exit_comm_part = part_shares * part_exit * self.commission
                            gross_part = part_shares * (part_exit - entry_px)
                            active_trade['realized_pnl'] = active_trade.get('realized_pnl', 0.0) + (gross_part - exit_comm_part)
                            active_trade['shares'] -= part_shares
                            active_trade['partial_taken'] = True
                            # Move stop to breakeven (never worse than current stop)
                            active_trade['stop_loss'] = max(active_trade['stop_loss'], entry_px)
                    else:
                        threshold = entry_px - 1.5 * r
                        if low <= threshold:
                            part_shares = max(1, active_trade['shares'] // 2)
                            part_exit = threshold
                            exit_comm_part = part_shares * part_exit * self.commission
                            gross_part = part_shares * (entry_px - part_exit)
                            active_trade['realized_pnl'] = active_trade.get('realized_pnl', 0.0) + (gross_part - exit_comm_part)
                            active_trade['shares'] -= part_shares
                            active_trade['partial_taken'] = True
                            active_trade['stop_loss'] = min(active_trade['stop_loss'], entry_px)

                # Time-based exit (max hold 20 trading days)
                if active_trade and (date - active_trade['entry_date']).days >= 20:
                    exit_price = close
                    exit_reason = 'TIME'

                if exit_price is not None:
                    # Calculate remaining leg P&L and commissions
                    remaining_shares = active_trade['shares']
                    exit_commission = remaining_shares * exit_price * self.commission

                    if active_trade['direction'] == 'long':
                        gross_remaining = remaining_shares * (exit_price - active_trade['entry_price'])
                    else:  # short
                        gross_remaining = remaining_shares * (active_trade['entry_price'] - exit_price)

                    # Net across both legs: realized partial + remaining - total entry commission
                    net_pnl = (
                        active_trade.get('realized_pnl', 0.0)
                        + gross_remaining
                        - exit_commission
                        - active_trade.get('entry_commission_total', 0.0)
                    )

                    # R-multiple based on initial risk and shares
                    risk_per_share = abs(active_trade['entry_price'] - active_trade['stop_loss'])
                    total_risk = risk_per_share * active_trade.get('initial_shares', remaining_shares)
                    r_multiple = net_pnl / total_risk if total_risk > 0 else 0

                    # Update capital with P&L
                    self.capital += net_pnl

                    # Record trade (use initial_shares for reporting)
                    trade = Trade(
                        entry_date=active_trade['entry_date'],
                        exit_date=date,
                        symbol=symbol,
                        direction=active_trade['direction'],
                        entry_price=active_trade['entry_price'],
                        exit_price=exit_price,
                        stop_loss=active_trade['stop_loss'],
                        target=active_trade['target'],
                        shares=active_trade.get('initial_shares', remaining_shares),
                        pnl=net_pnl,
                        pnl_pct=(net_pnl / (active_trade.get('initial_shares', remaining_shares) * active_trade['entry_price'])) * 100,
                        r_multiple=r_multiple,
                        exit_reason=exit_reason,
                        pattern=active_trade['pattern'],
                        confidence=active_trade['confidence'],
                        hold_days=(date - active_trade['entry_date']).days
                    )

                    symbol_trades.append(trade)
                    self.trades.append(trade)  # Add to global list
                    active_trade = None
                    # Don't check entry on same candle as exit
                    continue
            
            # ===== STEP 2: Check if new trade enters =====
            if not active_trade and signal_idx < len(signals):
                signal = signals[signal_idx]

                # Only process signals that reach this candle
                if signal['date'] == date:
                    entry_price = signal['price']
                    stop_loss = signal['stop_loss']
                    target = signal['target']
                    signal_type = signal['signal']

                    # Calculate position size
                    shares = self.calculate_position_size(entry_price, stop_loss)

                    if shares > 0:
                        # Check capital availability
                        position_cost = shares * entry_price

                        if position_cost <= self.capital:
                            # Open position
                            active_trade = {
                                'entry_date': date,
                                'entry_price': entry_price,
                                'stop_loss': stop_loss,
                                'target': target,
                                'shares': shares,
                                'direction': 'long' if signal_type == 'buy' else 'short',
                                'pattern': signal.get('pattern', ''),
                                'confidence': signal.get('confidence', 0),
                                # Tracking for trailing logic
                                'best_price': entry_price,
                                'entry_risk': abs(entry_price - stop_loss),
                                # Partial profit tracking
                                'initial_shares': shares,
                                'partial_taken': False,
                                'realized_pnl': 0.0,
                                'entry_commission_total': shares * entry_price * self.commission
                            }

                    signal_idx += 1

            # ===== STEP 3: Manage trailing stop post-entry =====
            if active_trade:
                # Update best price
                if active_trade['direction'] == 'long':
                    active_trade['best_price'] = max(active_trade['best_price'], high)
                    # Activate trailing after +1R
                    if active_trade['best_price'] - active_trade['entry_price'] >= active_trade['entry_risk']:
                        trailing_stop = active_trade['best_price'] - (0.5 * active_trade['entry_risk'])
                        # Never worse than original stop
                        active_trade['stop_loss'] = max(active_trade['stop_loss'], trailing_stop)
                else:
                    active_trade['best_price'] = min(active_trade['best_price'], low)
                    if active_trade['entry_price'] - active_trade['best_price'] >= active_trade['entry_risk']:
                        trailing_stop = active_trade['best_price'] + (0.5 * active_trade['entry_risk'])
                        active_trade['stop_loss'] = min(active_trade['stop_loss'], trailing_stop)
        
        # Close any open position at end of backtest
        if active_trade:
            exit_price = close
            remaining_shares = active_trade['shares']
            exit_commission = remaining_shares * exit_price * self.commission

            if active_trade['direction'] == 'long':
                gross_remaining = remaining_shares * (exit_price - active_trade['entry_price'])
            else:
                gross_remaining = remaining_shares * (active_trade['entry_price'] - exit_price)

            net_pnl = (
                active_trade.get('realized_pnl', 0.0)
                + gross_remaining
                - exit_commission
                - active_trade.get('entry_commission_total', 0.0)
            )

            # R-multiple based on initial risk and shares
            risk_per_share = abs(active_trade['entry_price'] - active_trade['stop_loss'])
            total_risk = risk_per_share * active_trade.get('initial_shares', remaining_shares)
            r_multiple = net_pnl / total_risk if total_risk > 0 else 0

            self.capital += net_pnl

            trade = Trade(
                entry_date=active_trade['entry_date'],
                exit_date=date,
                symbol=symbol,
                direction=active_trade['direction'],
                entry_price=active_trade['entry_price'],
                exit_price=exit_price,
                stop_loss=active_trade['stop_loss'],
                target=active_trade['target'],
                shares=active_trade.get('initial_shares', remaining_shares),
                pnl=net_pnl,
                pnl_pct=(net_pnl / (active_trade.get('initial_shares', remaining_shares) * active_trade['entry_price'])) * 100,
                r_multiple=r_multiple,
                exit_reason='EOD',
                pattern=active_trade['pattern'],
                confidence=active_trade['confidence'],
                hold_days=(date - active_trade['entry_date']).days
            )

            symbol_trades.append(trade)
            self.trades.append(trade)  # Add to global list
        
        return symbol_trades
    
    def old_execute_trades(self, backtest_result):
        """OLD METHOD - Kept for reference. Do not use."""
        symbol = backtest_result['symbol']
        df = backtest_result['data']
        signals = backtest_result['signals']
        
        for signal in signals:
            signal_date = signal['date']
            signal_type = signal['signal']
            entry_price = signal['price']
            stop_loss = signal['stop_loss']
            target = signal['target']
            pattern = signal['pattern']
            confidence = signal['confidence']
            
            # Skip if already in position
            if symbol in self.open_positions:
                continue
            
            # Calculate position size
            shares = self.calculate_position_size(entry_price, stop_loss)
            if shares == 0:
                continue
            
            # Entry commission
            entry_cost = shares * entry_price * (1 + self.commission)
            
            # Check if we have enough capital
            if entry_cost > self.capital:
                continue
            
            # Open position
            self.open_positions[symbol] = {
                'entry_date': signal_date,
                'entry_price': entry_price,
                'stop_loss': stop_loss,
                'target': target,
                'shares': shares,
                'direction': 'long' if signal_type == 'buy' else 'short',
                'pattern': pattern,
                'confidence': confidence
            }
            
            # Deduct capital
            self.capital -= entry_cost
            
            # Now check subsequent bars for exit
            entry_idx = df.index.get_loc(signal_date)
            max_hold_days = 20  # Reduced from 30 (exit faster if not working)
            
            # Track highest/lowest for trailing stop
            best_price = entry_price
            
            for j in range(entry_idx + 1, min(entry_idx + max_hold_days, len(df))):
                bar_date = df.index[j]
                bar_high = df['High'].iloc[j]
                bar_low = df['Low'].iloc[j]
                bar_close = df['Close'].iloc[j]
                
                # Update best price for trailing stop
                if signal_type == 'buy':
                    best_price = max(best_price, bar_high)
                    # Trailing stop: lock in 50% of gains
                    trailing_stop = best_price - (best_price - entry_price) * 0.5
                    trailing_stop = max(trailing_stop, stop_loss)  # Never worse than original stop
                else:  # sell
                    best_price = min(best_price, bar_low)
                    trailing_stop = best_price + (entry_price - best_price) * 0.5
                    trailing_stop = min(trailing_stop, stop_loss)
                
                exit_price = None
                exit_reason = None
                
                # Check for target hit
                if signal_type == 'buy' and bar_high >= target:
                    exit_price = target
                    exit_reason = 'target'
                elif signal_type == 'sell' and bar_low <= target:
                    exit_price = target
                    exit_reason = 'target'
                
                # Check for trailing stop hit
                elif signal_type == 'buy' and bar_low <= trailing_stop:
                    exit_price = trailing_stop
                    exit_reason = 'trailing_stop' if trailing_stop > stop_loss else 'stop'
                elif signal_type == 'sell' and bar_high >= trailing_stop:
                    exit_price = trailing_stop
                    exit_reason = 'trailing_stop' if trailing_stop < stop_loss else 'stop'
                
                # Time-based exit
                elif j == entry_idx + max_hold_days - 1:
                    exit_price = bar_close
                    exit_reason = 'time'
                
                # If exit triggered
                if exit_price is not None:
                    # Close position
                    pos = self.open_positions.pop(symbol)
                    
                    # Calculate P&L (after commissions)
                    entry_commission = shares * entry_price * self.commission
                    exit_commission = shares * exit_price * self.commission
                    
                    if pos['direction'] == 'long':
                        gross_pnl = shares * (exit_price - entry_price)
                    else:  # short
                        gross_pnl = shares * (entry_price - exit_price)
                    
                    # Net P&L after commissions
                    total_pnl = gross_pnl - entry_commission - exit_commission
                    pnl_pct = (total_pnl / (shares * pos['entry_price'])) * 100
                    
                    # Return capital (exit value after commission)
                    exit_value = shares * exit_price - exit_commission
                    self.capital += exit_value
                    
                    # Record trade
                    trade = Trade(
                        entry_date=pos['entry_date'],
                        exit_date=bar_date,
                        symbol=symbol,
                        direction=pos['direction'],
                        entry_price=pos['entry_price'],
                        exit_price=exit_price,
                        stop_loss=pos['stop_loss'],
                        target=pos['target'],
                        shares=shares,
                        pnl=total_pnl,
                        pnl_pct=pnl_pct,
                        exit_reason=exit_reason,
                        pattern=pos['pattern'],
                        confidence=pos['confidence'],
                        hold_days=(bar_date - pos['entry_date']).days
                    )
                    
                    self.trades.append(trade)
                    break
        
        return self.trades
    
    def get_summary(self):
        """Get trading summary statistics"""
        if not self.trades:
            return {
                'total_trades': 0,
                'win_rate': 0,
                'total_pnl': 0,
                'final_capital': self.capital,
                'return_pct': 0
            }
        
        winning_trades = [t for t in self.trades if t.pnl > 0]
        losing_trades = [t for t in self.trades if t.pnl <= 0]
        
        total_pnl = sum(t.pnl for t in self.trades)
        sum_wins = sum(t.pnl for t in winning_trades)
        sum_losses = sum(t.pnl for t in losing_trades)
        avg_win = sum_wins / len(winning_trades) if winning_trades else 0
        avg_loss = sum_losses / len(losing_trades) if losing_trades else 0
        
        # R-multiple statistics
        avg_r_multiple = sum(t.r_multiple for t in self.trades) / len(self.trades) if self.trades else 0
        win_r_multiples = [t.r_multiple for t in winning_trades]
        loss_r_multiples = [t.r_multiple for t in losing_trades]
        avg_win_r = sum(win_r_multiples) / len(win_r_multiples) if win_r_multiples else 0
        avg_loss_r = sum(loss_r_multiples) / len(loss_r_multiples) if loss_r_multiples else 0
        
        return {
            'total_trades': len(self.trades),
            'winning_trades': len(winning_trades),
            'losing_trades': len(losing_trades),
            'win_rate': (len(winning_trades) / len(self.trades)) * 100,
            'total_pnl': total_pnl,
            'avg_win': avg_win,
            'avg_loss': avg_loss,
            'profit_factor': (sum_wins / abs(sum_losses)) if sum_losses != 0 else 0,
            'avg_r_multiple': avg_r_multiple,  # Average R-multiple across all trades
            'win_avg_r': avg_win_r,  # Average R-multiple for winning trades
            'loss_avg_r': avg_loss_r,  # Average R-multiple for losing trades
            'final_capital': self.initial_capital + total_pnl,
            'return_pct': (total_pnl / self.initial_capital) * 100,
            'avg_hold_days': sum(t.hold_days for t in self.trades) / len(self.trades)
        }
