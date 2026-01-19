#!/usr/bin/env python3
"""
Quick test to verify data loading from various providers.
Tests get_spot_price() for a few stocks to see which provider works.
"""

import os
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from dotenv import load_dotenv
load_dotenv()

# Test imports
from data_providers import BreezeProvider, YFinanceProvider, get_spot_price

def test_spot_price_loading():
    """Test loading spot prices from various providers"""
    
    test_stocks = ['SBIN', 'ICICIBANK', 'RELIANCE', 'INFY', 'HDFC']
    
    print("\n" + "="*70)
    print("TESTING SPOT PRICE LOADING".center(70))
    print("="*70 + "\n")
    
    breeze_provider = BreezeProvider()
    yfinance_provider = YFinanceProvider()
    
    print(f"{'Symbol':<12} {'Breeze':<20} {'YFinance':<20} {'Fallback Result':<20}")
    print("-"*72)
    
    for stock in test_stocks:
        # Test Breeze
        breeze_price = breeze_provider.get_spot_price(stock)
        breeze_status = f"✓ {breeze_price:.2f}" if breeze_price else "✗ No data"
        
        # Test YFinance
        yf_price = yfinance_provider.get_spot_price(stock)
        yf_status = f"✓ {yf_price:.2f}" if yf_price else "✗ No data"
        
        # Test fallback function (tries both)
        fallback_price = get_spot_price(stock)
        fallback_status = f"✓ {fallback_price:.2f}" if fallback_price else "✗ No data"
        
        print(f"{stock:<12} {breeze_status:<20} {yf_status:<20} {fallback_status:<20}")
    
    print("\n" + "="*70)
    print("Legend: ✓ = Price fetched successfully, ✗ = Failed to get price")
    print("="*70 + "\n")

def test_intraday_candles():
    """Test loading intraday candles"""
    
    print("\n" + "="*70)
    print("TESTING INTRADAY CANDLES (15-min)".center(70))
    print("="*70 + "\n")
    
    breeze_provider = BreezeProvider()
    yfinance_provider = YFinanceProvider()
    
    test_stocks = ['SBIN', 'RELIANCE']
    
    print(f"{'Symbol':<12} {'Breeze':<20} {'YFinance':<20} {'Status':<20}")
    print("-"*72)
    
    for stock in test_stocks:
        # Test Breeze
        breeze_candles = breeze_provider.get_candles(stock, '15min')
        breeze_status = f"✓ {len(breeze_candles)} bars" if breeze_candles else "✗ No data"
        
        # Test YFinance
        yf_candles = yfinance_provider.get_candles(stock, '15min')
        yf_status = f"✓ {len(yf_candles)} bars" if yf_candles else "✗ No data"
        
        # Summary
        has_data = "✓ Has data" if (breeze_candles or yf_candles) else "✗ No data"
        
        print(f"{stock:<12} {breeze_status:<20} {yf_status:<20} {has_data:<20}")
    
    print("\n" + "="*70)
    print("="*70 + "\n")

if __name__ == '__main__':
    print("\nTesting Data Provider Integration...\n")
    
    try:
        test_spot_price_loading()
        test_intraday_candles()
        
        print("✓ All tests completed successfully!")
        print("\nNote: If YFinance shows 'No data', this might be due to rate limiting.")
        print("Check the screener output for 'Rate limited' messages.")
        
    except Exception as e:
        print(f"\n✗ Error during testing: {e}")
        import traceback
        traceback.print_exc()
