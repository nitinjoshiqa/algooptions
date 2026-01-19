#!/usr/bin/env python3
"""Test nsepython API to understand how to use it"""

import nsepython

print("=" * 70)
print("TESTING NSEPYTHON LIBRARY")
print("=" * 70)

# Check available classes/functions
print("\nAvailable functions in nsepython:")
funcs = [f for f in dir(nsepython) if not f.startswith('_')]
for func in funcs[:20]:
    print(f"  - {func}")

print("\n" + "=" * 70)
print("TEST 1: Using nseFetcher")
print("=" * 70)

try:
    fetcher = nsepython.nseFetcher()
    print(f"nseFetcher created: {type(fetcher)}")
    
    # Check available methods
    methods = [m for m in dir(fetcher) if not m.startswith('_')]
    print(f"Available methods: {methods[:10]}")
    
except Exception as e:
    print(f"Error with nseFetcher: {e}")

print("\n" + "=" * 70)
print("TEST 2: Try direct function calls")
print("=" * 70)

# Try different approaches
test_functions = [
    'fetchQuote',
    'fetchPrice', 
    'getQuote',
    'getPrice',
    'get_quote',
    'get_price',
]

for func_name in test_functions:
    if hasattr(nsepython, func_name):
        print(f"Found function: {func_name}")

print("\n" + "=" * 70)
print("TEST 3: Try fetching data")
print("=" * 70)

# Most common approach - try a simple call
try:
    # Try the most likely API
    quote = nsepython.getQuote('SBIN')
    print(f"getQuote('SBIN') returned: {type(quote)}")
    print(f"Data: {quote}")
except Exception as e:
    print(f"getQuote failed: {e}")

try:
    # Alternative approach
    from nsepython import nseFetcher
    fetcher = nseFetcher()
    quote = fetcher.getQuote('SBIN')
    print(f"fetcher.getQuote('SBIN') returned: {type(quote)}")
    print(f"Data: {quote}")
except Exception as e:
    print(f"fetcher.getQuote failed: {e}")

print("\n" + "=" * 70)
print("TEST 4: Check nsepython version and help")
print("=" * 70)

try:
    print(f"nsepython version: {nsepython.__version__}")
except:
    print("No __version__ attribute")

# Try help
try:
    help_text = nsepython.__doc__
    print(f"Module docstring: {help_text[:200] if help_text else 'None'}")
except:
    pass
