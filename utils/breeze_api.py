import os
import sys
import time
from dotenv import load_dotenv

# BreezeConnect may be unavailable; handle gracefully
try:
    from breeze_connect import BreezeConnect
except Exception as e:
    BreezeConnect = None
    print(f"BreezeConnect import failed [WARN]: {e}", file=sys.stderr)

# Load environment variables
load_dotenv()

API_KEY = os.getenv("BREEZE_API_KEY")
API_SECRET = os.getenv("BREEZE_API_SECRET")
SESSION_TOKEN = os.getenv("BREEZE_SESSION_TOKEN")

# Retry configuration
BREEZE_RETRY_ATTEMPTS = 3
BREEZE_RETRY_DELAY = 2  # seconds

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

def _attempt_breeze_connection(attempt=1):
    """Attempt to connect to Breeze with error details."""
    try:
        print(f"[Attempt {attempt}/{BREEZE_RETRY_ATTEMPTS}] Initializing BreezeConnect...", file=sys.stderr)
        breeze_obj = BreezeConnect(api_key=API_KEY)
        
        print(f"[Attempt {attempt}/{BREEZE_RETRY_ATTEMPTS}] Generating session...", file=sys.stderr)
        result = breeze_obj.generate_session(
            api_secret=API_SECRET,
            session_token=SESSION_TOKEN
        )
        
        # Check if session generation was successful
        if result and isinstance(result, dict):
            status = result.get('Status')
            if status == 200 or status == 201:
                print("[OK] Breeze session established successfully", file=sys.stderr)
                return breeze_obj, True
            else:
                error = result.get('Error', 'Unknown error')
                print(f"[FAIL] Breeze session failed with status {status}: {error}", file=sys.stderr)
                return None, False
        else:
            # generate_session() returned None - test with actual API call
            print(f"[?] Session result was None - verifying with API test...", file=sys.stderr)
            try:
                test_result = breeze_obj.get_portfolio_positions()
                if test_result is not None:
                    print("[OK] Breeze API verified working", file=sys.stderr)
                    return breeze_obj, True
                else:
                    print("[FAIL] Breeze API test returned None - session invalid", file=sys.stderr)
                    return None, False
            except Exception as test_error:
                print(f"[FAIL] Breeze API test failed: {type(test_error).__name__}: {str(test_error)[:80]}", file=sys.stderr)
                return None, False
            
    except ConnectionError as e:
        print(f"[FAIL] Connection error (attempt {attempt}): {str(e)[:100]}", file=sys.stderr)
        return None, False
    except TimeoutError as e:
        print(f"[FAIL] Timeout error (attempt {attempt}): {str(e)[:100]}", file=sys.stderr)
        return None, False
    except Exception as e:
        print(f"[FAIL] Error (attempt {attempt}): {type(e).__name__}: {str(e)[:80]}", file=sys.stderr)
        return None, False


def get_breeze_instance():
    """Lazy-initialize Breeze connection with retry logic."""
    global _breeze_instance, _breeze_initialized
    
    if _breeze_initialized:
        return _breeze_instance
    
    _breeze_initialized = True
    
    if not BreezeConnect:
        _breeze_instance = _DummyBreeze()
        print("BreezeConnect module not available [INFO]", file=sys.stderr)
        return _breeze_instance
    
    if not API_KEY or not API_SECRET:
        print("Breeze credentials missing [WARN]: API_KEY or API_SECRET not in .env", file=sys.stderr)
        _breeze_instance = _DummyBreeze()
        return _breeze_instance
    
    # Retry connection attempts
    for attempt in range(1, BREEZE_RETRY_ATTEMPTS + 1):
        breeze_obj, success = _attempt_breeze_connection(attempt)
        if success:
            _breeze_instance = breeze_obj
            return _breeze_instance
        
        # Wait before retry (except after last attempt)
        if attempt < BREEZE_RETRY_ATTEMPTS:
            print(f"[RETRY] Waiting {BREEZE_RETRY_DELAY}s before retry...", file=sys.stderr)
            time.sleep(BREEZE_RETRY_DELAY)
    
    # All retries exhausted
    print(f"[WARN] Failed to connect to Breeze after {BREEZE_RETRY_ATTEMPTS} attempts - falling back to alternative providers", file=sys.stderr)
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
