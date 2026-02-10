"""
Trade Learner - Post-Trade Learning & Calibration Logging

Purpose:
    Log trade execution data for future calibration and analysis
    Track {symbol, date, master_score, robustness_score, entry_price, exit_price, R_multiple}
    Enable performance analysis by score band
    
Architecture:
    - log_trade_opportunity(signal, triggered=False) → None (appends to CSV)
    - log_trade_result(trade_id, entry_price, exit_price, exit_date) → None
    - analyze_performance_by_score_band() → DataFrame
"""

import csv
import os
from datetime import datetime
from pathlib import Path


class TradeLogger:
    """Logs trade opportunities and results for learning"""
    
    def __init__(self, log_dir='logs', opportunities_file='trade_opportunities.csv', results_file='trade_results.csv'):
        """
        Initialize trade logger
        
        Args:
            log_dir: Directory for log files
            opportunities_file: File to log opportunities
            results_file: File to log executed trades
        """
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(exist_ok=True)
        
        self.opportunities_file = self.log_dir / opportunities_file
        self.results_file = self.log_dir / results_file
        
        # Initialize files if not exist
        self._init_opportunities_file()
        self._init_results_file()
    
    def _init_opportunities_file(self):
        """Create opportunities log file with headers"""
        if not self.opportunities_file.exists():
            with open(self.opportunities_file, 'w', newline='') as f:
                writer = csv.DictWriter(f, fieldnames=[
                    'date', 'symbol', 'signal_type', 'entry_price', 'pattern',
                    'confidence', 'robustness_score', 'robustness_tier',
                    'context_score', 'master_score', 'master_score_tier',
                    'triggered', 'triggered_date',
                    'stop_loss', 'target', 'risk_reward_ratio',
                    'volatility', 'market_regime', 'special_day_flag'
                ])
                writer.writeheader()
    
    def _init_results_file(self):
        """Create results log file with headers"""
        if not self.results_file.exists():
            with open(self.results_file, 'w', newline='') as f:
                writer = csv.DictWriter(f, fieldnames=[
                    'date', 'symbol', 'entry_date', 'entry_price', 'entry_confidence',
                    'entry_robustness_score', 'entry_master_score',
                    'exit_date', 'exit_price', 'pnl', 'pnl_pct', 'r_multiple',
                    'holding_days', 'stop_trigger', 'target_trigger', 'exit_reason'
                ])
                writer.writeheader()
    
    def log_opportunity(self, signal):
        """
        Log a signal opportunity (potential trade)
        
        Args:
            signal: Signal dict with fields:
                - date, symbol, signal, price, pattern, confidence
                - robustness_score, master_score, context_score
                - stop_loss, target, volatility, regime
                - special_day_flag (optional)
        """
        try:
            row = {
                'date': signal.get('date'),
                'symbol': signal.get('symbol'),
                'signal_type': signal.get('signal'),
                'entry_price': round(signal.get('price', 0), 2),
                'pattern': signal.get('pattern'),
                'confidence': signal.get('confidence', 0),
                'robustness_score': round(signal.get('robustness_score', 0), 1),
                'robustness_tier': self._get_tier(signal.get('robustness_score', 0), 'robustness'),
                'context_score': round(signal.get('context_score', 2.5), 2),
                'master_score': round(signal.get('master_score', 50), 1),
                'master_score_tier': self._get_tier(signal.get('master_score', 50), 'master'),
                'triggered': 0,  # Will update when trade executes
                'triggered_date': '',
                'stop_loss': round(signal.get('stop_loss', 0), 2),
                'target': round(signal.get('target', 0), 2),
                'risk_reward_ratio': self._calc_rrr(signal),
                'volatility': signal.get('volatility'),
                'market_regime': signal.get('regime'),
                'special_day_flag': signal.get('special_day_flag', 0)
            }
            
            with open(self.opportunities_file, 'a', newline='') as f:
                writer = csv.DictWriter(f, fieldnames=row.keys())
                writer.writerow(row)
        
        except Exception as e:
            print(f"[ERROR] Failed to log opportunity: {e}")
    
    def log_result(self, symbol, entry_date, entry_price, entry_confidence, entry_robustness, entry_master,
                   exit_date, exit_price, exit_reason='time_exit'):
        """
        Log a trade result (after exit)
        
        Args:
            symbol: Stock symbol
            entry_date: Trade entry date
            entry_price: Entry price
            entry_confidence: Original confidence
            entry_robustness: Original robustness score
            entry_master: Original master score
            exit_date: Trade exit date
            exit_price: Exit price
            exit_reason: How it exited ('stop_triggered', 'target_triggered', 'time_exit', etc)
        """
        try:
            pnl = exit_price - entry_price
            pnl_pct = (pnl / entry_price * 100) if entry_price != 0 else 0
            
            # Estimate R multiple
            # Assumption: position risk = entry_price * 2% (typical)
            estimated_risk = entry_price * 0.02
            r_multiple = pnl / estimated_risk if estimated_risk != 0 else 0
            
            # Holding duration
            entry_dt = datetime.fromisoformat(str(entry_date))
            exit_dt = datetime.fromisoformat(str(exit_date))
            holding_days = (exit_dt - entry_dt).days
            
            row = {
                'date': exit_date,
                'symbol': symbol,
                'entry_date': entry_date,
                'entry_price': round(entry_price, 2),
                'entry_confidence': entry_confidence,
                'entry_robustness_score': round(entry_robustness, 1),
                'entry_master_score': round(entry_master, 1),
                'exit_date': exit_date,
                'exit_price': round(exit_price, 2),
                'pnl': round(pnl, 2),
                'pnl_pct': round(pnl_pct, 2),
                'r_multiple': round(r_multiple, 2),
                'holding_days': holding_days,
                'stop_trigger': 1 if 'stop' in exit_reason.lower() else 0,
                'target_trigger': 1 if 'target' in exit_reason.lower() else 0,
                'exit_reason': exit_reason
            }
            
            with open(self.results_file, 'a', newline='') as f:
                writer = csv.DictWriter(f, fieldnames=row.keys())
                writer.writerow(row)
        
        except Exception as e:
            print(f"[ERROR] Failed to log result: {e}")
    
    @staticmethod
    def _get_tier(score, score_type):
        """Get tier name for score"""
        if score_type == 'robustness':
            if score >= 85:
                return 'STRONG'
            elif score >= 70:
                return 'GOOD'
            elif score >= 57:
                return 'FAIR'
            elif score >= 43:
                return 'WEAK'
            else:
                return 'POOR'
        elif score_type == 'master':
            if score >= 80:
                return 'STRONG'
            elif score >= 70:
                return 'GOOD'
            elif score >= 60:
                return 'FAIR'
            else:
                return 'WEAK'
        return 'UNKNOWN'
    
    @staticmethod
    def _calc_rrr(signal):
        """Calculate Risk/Reward Ratio"""
        entry = signal.get('price', 0)
        stop = signal.get('stop_loss', 0)
        target = signal.get('target', 0)
        
        if entry == 0 or stop == 0 or target == 0:
            return 0.0
        
        risk = entry - stop
        reward = target - entry
        
        if risk <= 0:
            return 0.0
        
        return round(reward / risk, 2)


# Global logger instance
_trade_logger = None


def get_trade_logger():
    """Get or create global trade logger instance"""
    global _trade_logger
    if _trade_logger is None:
        _trade_logger = TradeLogger()
    return _trade_logger


def log_trade_opportunity(signal):
    """Log a trade opportunity"""
    logger = get_trade_logger()
    logger.log_opportunity(signal)


def log_trade_result(symbol, entry_date, entry_price, entry_confidence, entry_robustness, entry_master,
                    exit_date, exit_price, exit_reason='time_exit'):
    """Log a trade result"""
    logger = get_trade_logger()
    logger.log_result(symbol, entry_date, entry_price, entry_confidence, entry_robustness, entry_master,
                     exit_date, exit_price, exit_reason)
