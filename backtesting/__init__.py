"""
Backtesting module for NIFTY screener strategies
Evaluates historical performance of pattern-based signals
"""

from .backtest_engine import BacktestEngine
from .trade_simulator import TradeSimulator
from .report_generator import ReportGenerator

__all__ = [
    'BacktestEngine',
    'TradeSimulator',
    'ReportGenerator'
]
