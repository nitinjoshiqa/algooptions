#!/usr/bin/env python3
"""
Comprehensive Breeze Connect Diagnostic Tool

This script tests every aspect of BreezeConnect to identify exactly what's working
and what's failing. Run this to troubleshoot data fetching issues.

Usage:
    python breeze_diagnostic.py
"""

import os
import sys
import json
from datetime import datetime, timedelta
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Colors for output
class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    RESET = '\033[0m'
    BOLD = '\033[1m'

def print_test(title):
    """Print a test section header"""
    print(f"\n{Colors.BOLD}{Colors.BLUE}{'='*60}")
    print(f"TEST: {title}")
    print(f"{'='*60}{Colors.RESET}")

def print_success(msg):
    """Print success message"""
    print(f"{Colors.GREEN}✓ {msg}{Colors.RESET}")

def print_error(msg):
    """Print error message"""
    print(f"{Colors.RED}✗ {msg}{Colors.RESET}")

def print_warning(msg):
    """Print warning message"""
    print(f"{Colors.YELLOW}⚠ {msg}{Colors.RESET}")

def print_info(msg):
    """Print info message"""
    print(f"{Colors.BLUE}ℹ {msg}{Colors.RESET}")

def test_credentials():
    """Test 1: Check if credentials are present"""
    print_test("Credentials Presence")
    
    api_key = os.getenv('BREEZE_API_KEY')
    api_secret = os.getenv('BREEZE_API_SECRET')
    session_token = os.getenv('BREEZE_SESSION_TOKEN')
    
    if api_key:
        print_success(f"API Key found: {api_key[:10]}...{api_key[-5:]}")
    else:
        print_error("API Key missing from .env")
        return False
    
    if api_secret:
        print_success(f"API Secret found: {api_secret[:10]}...{api_secret[-5:]}")
    else:
        print_error("API Secret missing from .env")
        return False
    
    if session_token:
        print_success(f"Session Token found: {session_token}")
    else:
        print_error("Session Token missing from .env")
        return False
    
    return True

def test_module_import():
    """Test 2: Check if BreezeConnect module can be imported"""
    print_test("Module Import")
    
    try:
        from breeze_connect import BreezeConnect
        print_success("BreezeConnect module imported successfully")
        return True
    except ImportError as e:
        print_error(f"Failed to import BreezeConnect: {e}")
        print_info("Install with: pip install breeze-connect")
        return False

def test_instance_creation():
    """Test 3: Test creating Breeze instance"""
    print_test("Instance Creation")
    
    try:
        from breeze_connect import BreezeConnect
        
        api_key = os.getenv('BREEZE_API_KEY')
        if not api_key:
            print_error("API Key not found")
            return False
        
        breeze = BreezeConnect(api_key=api_key)
        print_success("BreezeConnect instance created successfully")
        return breeze
    except Exception as e:
        print_error(f"Failed to create instance: {e}")
        return None

def test_session_generation(breeze):
    """Test 4: Test session generation"""
    print_test("Session Generation")
    
    if not breeze:
        print_error("Breeze instance not available")
        return False
    
    try:
        api_secret = os.getenv('BREEZE_API_SECRET')
        session_token = os.getenv('BREEZE_SESSION_TOKEN')
        
        if not api_secret or not session_token:
            print_error("API Secret or Session Token missing")
            return False
        
        print_info(f"Generating session with token: {session_token}")
        
        result = breeze.generate_session(
            api_secret=api_secret,
            session_token=session_token
        )
        
        print_info(f"Response: {result}")
        
        # Check response
        if isinstance(result, dict):
            if result.get('status') == 200 or 'Success' in str(result):
                print_success("Session generated successfully")
                return True
            else:
                print_error(f"Session generation failed: {result}")
                return False
        else:
            print_warning(f"Unexpected response type: {type(result)}")
            print_info(f"Response content: {result}")
            return True  # Might still be successful
    
    except Exception as e:
        print_error(f"Session generation error: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_customer_details(breeze):
    """Test 5: Get customer details"""
    print_test("Customer Details")
    
    if not breeze:
        print_error("Breeze instance not available")
        return False
    
    try:
        print_info("Fetching customer details...")
        result = breeze.get_customer_details()
        
        print_info(f"Response: {result}")
        
        if result and not isinstance(result, str):
            print_success("Customer details retrieved successfully")
            print_info(f"Details: {json.dumps(result, indent=2, default=str)[:200]}...")
            return True
        else:
            print_error(f"Failed to get customer details: {result}")
            return False
    
    except Exception as e:
        print_error(f"Error getting customer details: {e}")
        return False

def test_stock_script_list(breeze):
    """Test 6: Get stock script list"""
    print_test("Stock Script List")
    
    if not breeze:
        print_error("Breeze instance not available")
        return False
    
    try:
        print_info("Fetching stock script list...")
        result = breeze.get_stock_script_list()
        
        if result:
            # Count different exchanges
            nse_count = len([s for s in result if s.get('exchangeCode') == 'NSE'])
            bse_count = len([s for s in result if s.get('exchangeCode') == 'BSE'])
            
            print_success(f"Stock script list retrieved: {len(result)} total scripts")
            print_info(f"  - NSE stocks: {nse_count}")
            print_info(f"  - BSE stocks: {bse_count}")
            
            # Show sample NSE stocks
            nse_stocks = [s for s in result if s.get('exchangeCode') == 'NSE' and s.get('productType') == 'cash'][:5]
            if nse_stocks:
                print_info("Sample NSE cash stocks:")
                for stock in nse_stocks:
                    print_info(f"  - {stock.get('stock_code')} ({stock.get('stock_name')})")
            
            return True
        else:
            print_error("Failed to get stock script list")
            return False
    
    except Exception as e:
        print_error(f"Error getting stock script list: {e}")
        return False

def test_get_quotes(breeze):
    """Test 7: Test getting quotes for various stocks"""
    print_test("Get Quotes Test")
    
    if not breeze:
        print_error("Breeze instance not available")
        return False
    
    # Test different configurations
    test_configs = [
        {'stock_code': 'SBIN', 'exchange': 'NSE', 'product': 'cash', 'name': 'SBIN (NSE Cash)'},
        {'stock_code': 'ICICIBANK', 'exchange': 'NSE', 'product': 'cash', 'name': 'ICICIBANK (NSE Cash)'},
        {'stock_code': 'RELIANCE', 'exchange': 'NSE', 'product': 'cash', 'name': 'RELIANCE (NSE Cash)'},
        {'stock_code': 'SBIN', 'exchange': 'NSE', 'product': 'mtf', 'name': 'SBIN (NSE MTF)'},
        {'stock_code': 'INFY', 'exchange': 'NSE', 'product': 'cash', 'name': 'INFY (NSE Cash)'},
    ]
    
    success_count = 0
    
    for config in test_configs:
        try:
            print_info(f"Testing: {config['name']}")
            
            result = breeze.get_quotes(
                stock_code=config['stock_code'],
                exchange_code=config['exchange'],
                product_type=config['product']
            )
            
            print_info(f"  Response type: {type(result)}")
            
            if isinstance(result, dict):
                # Check for error keys
                if 'error' in result or 'Error' in result:
                    error_msg = result.get('error') or result.get('Error')
                    print_warning(f"  Error: {error_msg}")
                elif 'ltp' in result or 'LTP' in result:
                    ltp = result.get('ltp') or result.get('LTP')
                    print_success(f"  Got LTP: {ltp}")
                    success_count += 1
                else:
                    print_warning(f"  Unexpected response: {list(result.keys())[:5]}")
                    if 'ltp' not in str(result).lower():
                        print_info(f"  Full response: {str(result)[:200]}")
            elif isinstance(result, str):
                print_warning(f"  String response: {result}")
            else:
                print_info(f"  Response: {result}")
        
        except Exception as e:
            print_error(f"  Exception: {str(e)[:100]}")
    
    print_info(f"\nQuote success rate: {success_count}/{len(test_configs)}")
    return success_count > 0

def test_get_historical_data(breeze):
    """Test 8: Test getting historical data"""
    print_test("Get Historical Data Test")
    
    if not breeze:
        print_error("Breeze instance not available")
        return False
    
    try:
        print_info("Fetching historical data for SBIN...")
        
        # Use dates from 30 days ago to today
        to_date = datetime.now().strftime('%d-%m-%Y')
        from_date = (datetime.now() - timedelta(days=30)).strftime('%d-%m-%Y')
        
        result = breeze.get_historical_data(
            stock_code='SBIN',
            exchange_code='NSE',
            product_type='cash',
            from_date=from_date,
            to_date=to_date,
            interval='1day'
        )
        
        print_info(f"Response type: {type(result)}")
        
        if isinstance(result, dict):
            if result.get('error') or result.get('Error'):
                error_msg = result.get('error') or result.get('Error')
                print_error(f"Error: {error_msg}")
                return False
            else:
                # Check for candle data
                if isinstance(result.get('candles'), list):
                    candles = result['candles']
                    print_success(f"Got historical data: {len(candles)} candles")
                    if candles:
                        print_info(f"Sample candle: {candles[0]}")
                    return True
                else:
                    print_warning(f"Unexpected response format: {list(result.keys())}")
                    return False
        elif isinstance(result, list):
            print_success(f"Got historical data: {len(result)} candles")
            return True
        else:
            print_warning(f"Unexpected response: {result}")
            return False
    
    except Exception as e:
        print_error(f"Error getting historical data: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_market_depth(breeze):
    """Test 9: Test market depth data"""
    print_test("Market Depth Test")
    
    if not breeze:
        print_error("Breeze instance not available")
        return False
    
    try:
        print_info("Fetching market depth for SBIN...")
        
        # Get quotes which may include depth
        result = breeze.get_quotes(
            stock_code='SBIN',
            exchange_code='NSE',
            product_type='cash'
        )
        
        if isinstance(result, dict) and 'bids' in result:
            print_success("Market depth data available")
            return True
        else:
            print_warning("Market depth not included in quote response")
            return False
    
    except Exception as e:
        print_error(f"Error getting market depth: {e}")
        return False

def test_portfolio_methods(breeze):
    """Test 10: Test portfolio/account methods"""
    print_test("Portfolio Methods")
    
    if not breeze:
        print_error("Breeze instance not available")
        return False
    
    methods_to_test = [
        ('get_demat_holdings', 'Demat Holdings'),
        ('get_funds', 'Available Funds'),
        ('get_portfolio_positions', 'Portfolio Positions'),
    ]
    
    success_count = 0
    
    for method_name, display_name in methods_to_test:
        try:
            if hasattr(breeze, method_name):
                print_info(f"Testing {display_name}...")
                method = getattr(breeze, method_name)
                result = method()
                
                if result:
                    print_success(f"{display_name}: Available")
                    success_count += 1
                else:
                    print_warning(f"{display_name}: Empty result")
            else:
                print_warning(f"{display_name}: Method not available")
        
        except Exception as e:
            print_warning(f"{display_name}: {str(e)[:100]}")
    
    print_info(f"\nPortfolio methods success: {success_count}/{len(methods_to_test)}")
    return success_count > 0

def main():
    """Run all diagnostic tests"""
    print(f"\n{Colors.BOLD}{Colors.BLUE}")
    print("╔" + "═"*58 + "╗")
    print("║" + " "*58 + "║")
    print("║" + "  BREEZE CONNECT DIAGNOSTIC TOOL".center(58) + "║")
    print("║" + " "*58 + "║")
    print("╚" + "═"*58 + "╝")
    print(Colors.RESET)
    
    print(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
    
    # Test sequence
    tests_passed = 0
    tests_total = 0
    
    # Test 1: Credentials
    tests_total += 1
    if test_credentials():
        tests_passed += 1
    
    # Test 2: Module import
    tests_total += 1
    if test_module_import():
        tests_passed += 1
    
    # Test 3: Instance creation
    tests_total += 1
    breeze = test_instance_creation()
    if breeze:
        tests_passed += 1
    
    # Test 4: Session generation
    tests_total += 1
    if breeze and test_session_generation(breeze):
        tests_passed += 1
    
    # Test 5: Customer details
    if breeze:
        tests_total += 1
        if test_customer_details(breeze):
            tests_passed += 1
    
    # Test 6: Script list
    if breeze:
        tests_total += 1
        if test_stock_script_list(breeze):
            tests_passed += 1
    
    # Test 7: Get quotes
    if breeze:
        tests_total += 1
        if test_get_quotes(breeze):
            tests_passed += 1
    
    # Test 8: Historical data
    if breeze:
        tests_total += 1
        if test_get_historical_data(breeze):
            tests_passed += 1
    
    # Test 9: Market depth
    if breeze:
        tests_total += 1
        if test_market_depth(breeze):
            tests_passed += 1
    
    # Test 10: Portfolio methods
    if breeze:
        tests_total += 1
        if test_portfolio_methods(breeze):
            tests_passed += 1
    
    # Summary
    print(f"\n{Colors.BOLD}{Colors.BLUE}{'='*60}")
    print("DIAGNOSTIC SUMMARY")
    print(f"{'='*60}{Colors.RESET}")
    
    print(f"Tests passed: {tests_passed}/{tests_total}")
    
    if tests_passed == tests_total:
        print_success("All tests passed! BreezeConnect is fully functional.")
    elif tests_passed >= tests_total - 2:
        print_warning(f"Most tests passed. Some features may be unavailable.")
    else:
        print_error(f"Critical issues detected. Only {tests_passed} of {tests_total} tests passed.")
    
    print(f"\nCompleted at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Recommendations
    print(f"\n{Colors.BOLD}{Colors.BLUE}RECOMMENDATIONS:{Colors.RESET}")
    
    if tests_passed == 0:
        print_error("Install breeze-connect: pip install breeze-connect")
    elif tests_passed < 4:
        print_error("Check credentials in .env file")
        print_info("Get fresh credentials from: https://www.icicidirect.com/")
    elif tests_passed < 7:
        print_warning("Quotes not working - this is normal due to API limitations")
        print_info("Framework will automatically fall back to Yahoo Finance")
    else:
        print_success("Your BreezeConnect setup is working well!")
        print_info("You can run: python nifty_bearnness_v2.py --universe banknifty --mode swing")

if __name__ == '__main__':
    main()
