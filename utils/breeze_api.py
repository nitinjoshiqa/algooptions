import os
from dotenv import load_dotenv

# BreezeConnect may be unavailable; handle gracefully
try:
    from breeze_connect import BreezeConnect
except Exception as e:
    BreezeConnect = None
    print(f"BreezeConnect import failed [WARN]: {e}")

# Load environment variables
load_dotenv()

API_KEY = os.getenv("BREEZE_API_KEY")
API_SECRET = os.getenv("BREEZE_API_SECRET")
SESSION_TOKEN = os.getenv("BREEZE_SESSION_TOKEN")

class _DummyBreeze:
    def get_quotes(self, *args, **kwargs):
        return None
    def get_historical_data(self, *args, **kwargs):
        return None
    def get_portfolio_positions(self, *args, **kwargs):
        return []
    def place_order(self, *args, **kwargs):
        return None

# Lazy initialization - only connect to Breeze when actually needed
_breeze_instance = None
_breeze_initialized = False

def get_breeze_instance():
    """Lazy-initialize Breeze connection."""
    global _breeze_instance, _breeze_initialized
    
    if _breeze_initialized:
        return _breeze_instance
    
    _breeze_initialized = True
    
    if not BreezeConnect:
        _breeze_instance = _DummyBreeze()
        print("BreezeConnect module not available [INFO]")
        return _breeze_instance
    
    try:
        if not API_KEY or not API_SECRET:
            print("Breeze credentials missing [WARN]: API_KEY or API_SECRET not in .env")
            _breeze_instance = _DummyBreeze()
            return _breeze_instance
        
        print(f"Initializing BreezeConnect with API Key: {API_KEY[:10]}...")
        _breeze_instance = BreezeConnect(api_key=API_KEY)
        
        print(f"Generating session with token: {SESSION_TOKEN}...")
        result = _breeze_instance.generate_session(
            api_secret=API_SECRET,
            session_token=SESSION_TOKEN
        )
        
        # Check if session generation was successful
        if result and isinstance(result, dict):
            status = result.get('Status')
            if status == 200 or status == 201:
                print("Breeze session established successfully [OK]")
                return _breeze_instance
            else:
                error = result.get('Error', 'Unknown error')
                print(f"Breeze session failed with status {status} [ERROR]: {error}")
                _breeze_instance = _DummyBreeze()
                return _breeze_instance
        else:
            # generate_session() returned None - but that doesn't mean it failed!
            # Test with actual API call to verify session is valid
            print(f"Breeze session result was None - testing with API call [INFO]...")
            try:
                # Test with a simple read-only call
                test_result = _breeze_instance.get_portfolio_positions()
                if test_result is not None:
                    print("Breeze session is valid (verified with API call) [OK]")
                    return _breeze_instance
                else:
                    # API call returned None too - session is not working
                    print("Breeze session test failed - API returned None [ERROR]")
                    _breeze_instance = _DummyBreeze()
                    return _breeze_instance
            except Exception as test_error:
                print(f"Breeze session test failed - API error: {type(test_error).__name__}: {test_error} [ERROR]")
                _breeze_instance = _DummyBreeze()
                return _breeze_instance
            
    except Exception as e:
        print(f"Breeze session exception [ERROR]: {type(e).__name__}: {e}")
        _breeze_instance = _DummyBreeze()
    
    return _breeze_instance

# Initialize breeze lazily - call get_breeze_instance() to get the real instance
breeze = get_breeze_instance()

def get_positions():
    # Correct Breeze method
    global breeze
    breeze = get_breeze_instance()
    return breeze.get_portfolio_positions()

def exit_position(pos):
    global breeze
    breeze = get_breeze_instance()
    breeze.place_order(
        stock_code=pos["stock_code"],
        exchange_code=pos["exchange_code"],
        product=pos["product"],
        action="buy" if pos["action"] == "sell" else "sell",
        quantity=pos["quantity"],
        order_type="market"
    )
