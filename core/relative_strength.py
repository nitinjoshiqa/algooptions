"""Relative Strength Analysis - Compare stock momentum vs sector and index."""
from datetime import datetime, timedelta
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.sector_mapper import SECTOR_MAP
from data_providers import get_intraday_candles_for


def calculate_momentum(symbol, periods=[1, 5, 10], use_yf=False, force_yf=False, force_breeze=False):
    """
    Calculate momentum (% change) for a symbol over multiple periods.
    
    Args:
        symbol: Stock symbol (e.g., 'RELIANCE')
        periods: List of periods to calculate momentum (e.g., [1, 5, 10] for 1/5/10 day)
        
    Returns:
        Dict with momentum % for each period
        Example: {'1d': 2.5, '5d': -1.2, '10d': 5.8}
    """
    try:
        # Fetch daily candles (get more bars to ensure sufficient history for momentum calc)
        # Requesting 90 days to handle 10d momentum + buffer for holidays/weekends
        candles, _ = get_intraday_candles_for(
            symbol, interval='1day', max_bars=90,
            use_yf=use_yf, force_yf=force_yf, force_breeze=force_breeze
        )
        
        if not candles or len(candles) < 2:
            return None
        
        # Get current price (latest candle close)
        current_price = candles[-1].get('close', 0)
        
        momentum = {}
        for period in periods:
            if period > len(candles) - 1:
                # Not enough data for this period - use maximum available period
                # This ensures we calculate momentum on best available data instead of returning 0
                available_period = len(candles) - 1
                if available_period >= 1:
                    past_price = candles[0].get('close', 0)  # Oldest candle available
                    if past_price > 0:
                        pct_change = ((current_price - past_price) / past_price) * 100
                        momentum[f'{period}d'] = round(pct_change, 2)
                    else:
                        momentum[f'{period}d'] = 0.0
                else:
                    momentum[f'{period}d'] = 0.0
            else:
                past_price = candles[-(period + 1)].get('close', 0)
                if past_price > 0:
                    pct_change = ((current_price - past_price) / past_price) * 100
                    momentum[f'{period}d'] = round(pct_change, 2)
                else:
                    momentum[f'{period}d'] = 0.0
        
        return momentum
    
    except Exception as e:
        return None


def get_sector_stocks(symbol):
    """Get all stocks in the same sector as the given symbol."""
    if symbol not in SECTOR_MAP:
        return []
    
    sector = SECTOR_MAP[symbol]
    sector_stocks = [s for s, sec in SECTOR_MAP.items() if sec == sector]
    return sector_stocks


def calculate_relative_strength(symbol, use_yf=False, force_yf=False, force_breeze=False):
    """
    Calculate Relative Strength scores comparing stock to sector and index.
    
    Returns dict with:
    - stock_momentum: Stock's own momentum (5d, 10d)
    - sector_momentum: Sector average momentum
    - index_momentum: Nifty50 momentum
    - rs_vs_sector: RS score vs sector (-1 to +1)
    - rs_vs_index: RS score vs Nifty50 (-1 to +1)
    - outperformer: Boolean, True if beating sector
    - sector_rank: Rank within sector (1 = best)
    - sector_stocks: List of sector stocks for peer comparison
    - peer_data: List of dicts with symbol, momentum, rank for tooltips
    """
    try:
        # Get stock momentum
        stock_mom = calculate_momentum(symbol, periods=[5, 10], use_yf=use_yf, force_yf=force_yf, force_breeze=force_breeze)
        if not stock_mom:
            return None
        
        # Get sector momentum
        sector_stocks = get_sector_stocks(symbol)
        if not sector_stocks or len(sector_stocks) == 0:
            return None
        
        sector_momentums = []
        peer_data = []
        
        for stock in sector_stocks:
            if stock == symbol:
                continue  # Skip self
            
            s_mom = calculate_momentum(stock, periods=[5, 10], use_yf=use_yf, force_yf=force_yf, force_breeze=force_breeze)
            if s_mom:
                # Use 5-day momentum as primary metric
                sector_momentums.append(s_mom['5d'])
                peer_data.append({
                    'symbol': stock,
                    'momentum_5d': s_mom['5d'],
                    'momentum_10d': s_mom['10d']
                })
        
        if not sector_momentums:
            return None
        
        # Calculate sector average momentum
        sector_avg_5d = sum(sector_momentums) / len(sector_momentums)
        
        # Get Nifty50 momentum (use alternate symbols if NIFTY fails)
        nifty_mom = calculate_momentum('NIFTY', periods=[5, 10], use_yf=use_yf, force_yf=force_yf, force_breeze=force_breeze)
        if not nifty_mom:
            # Try alternate NIFTY symbols for yFinance compatibility
            for nifty_symbol in ['^NSEI', 'NIFTYBEES', 'RELIANCE']:
                nifty_mom = calculate_momentum(nifty_symbol, periods=[5, 10], use_yf=True, force_yf=True, force_breeze=False)
                if nifty_mom and (nifty_mom['5d'] != 0.0 or nifty_mom['10d'] != 0.0):
                    break
        
        if not nifty_mom:
            nifty_mom = {'5d': 0.0, '10d': 0.0}
        
        # Calculate Relative Strength scores
        # RS vs Sector: How much better/worse than sector
        stock_5d_mom = stock_mom['5d']
        rs_vs_sector = (stock_5d_mom - sector_avg_5d) / (abs(sector_avg_5d) + 0.01)  # Avoid division by zero
        rs_vs_sector = max(-1.0, min(1.0, rs_vs_sector))  # Clamp to [-1, +1]
        
        # RS vs Index
        index_5d_mom = nifty_mom['5d']
        rs_vs_index = (stock_5d_mom - index_5d_mom) / (abs(index_5d_mom) + 0.01)
        rs_vs_index = max(-1.0, min(1.0, rs_vs_index))
        
        # Rank within sector
        peer_data.append({
            'symbol': symbol,
            'momentum_5d': stock_5d_mom,
            'momentum_10d': stock_mom['10d']
        })
        
        # Sort by 5-day momentum (descending)
        peer_data.sort(key=lambda x: x['momentum_5d'], reverse=True)
        sector_rank = next((i + 1 for i, p in enumerate(peer_data) if p['symbol'] == symbol), 1)
        
        # Calculate weighted RS: 60% sector, 40% index (combined single metric)
        weighted_rs = (rs_vs_sector * 0.6) + (rs_vs_index * 0.4)
        weighted_rs = max(-1.0, min(1.0, weighted_rs))  # Clamp to [-1, +1]
        
        return {
            'stock_momentum_5d': stock_5d_mom,
            'stock_momentum_10d': stock_mom['10d'],
            'sector_momentum_5d': sector_avg_5d,
            'sector_momentum_10d': 0.0,  # Would need to calculate
            'index_momentum_5d': index_5d_mom,
            'index_momentum_10d': nifty_mom['10d'],
            'rs_vs_sector': rs_vs_sector,
            'rs_vs_index': rs_vs_index,
            'rs_weighted': weighted_rs,  # SINGLE metric: 60% sector + 40% index
            'outperformer': stock_5d_mom > sector_avg_5d,
            'sector': SECTOR_MAP.get(symbol, 'Unknown'),
            'sector_rank': sector_rank,
            'sector_size': len(peer_data),
            'peer_data': peer_data[:10]  # Top 10 peers for tooltip
        }
    
    except Exception as e:
        import traceback
        traceback.print_exc()
        return None
