import os
import sys
sys.path.append(os.path.dirname(__file__))

from data_providers import YFinanceProvider

def test_next_100_stocks():
    # Read the next 100 stocks file - it's all on one line with \n separators
    with open('ARCHIVE/next_100_stocks.txt', 'r') as f:
        content = f.read().strip()
    
    # Split by \n to get individual stocks
    stocks = content.split('\\n')
    # Filter out empty strings
    stocks = [stock for stock in stocks if stock.strip()]
    
    print(f"Found {len(stocks)} stocks to test:")
    for stock in stocks[:10]:  # Show first 10
        print(f"  {stock}")
    if len(stocks) > 10:
        print(f"  ... and {len(stocks) - 10} more")

    # Initialize provider
    provider = YFinanceProvider()

    available_stocks = []
    unavailable_stocks = []

    for i, stock in enumerate(stocks, 1):
        if not stock.strip():
            continue

        symbol = stock.strip() + '.NS'
        try:
            price = provider.get_spot_price(symbol)
            if price is not None and price > 0:
                available_stocks.append(stock.strip())
                print(f"[{i:3d}] ✓ {stock.strip()}: ₹{price:.2f}")
            else:
                unavailable_stocks.append(stock.strip())
                print(f"[{i:3d}] ✗ {stock.strip()}: No data")
        except Exception as e:
            unavailable_stocks.append(stock.strip())
            print(f"[{i:3d}] ✗ {stock.strip()}: Error - {str(e)[:50]}")

    print(f"\nSummary:")
    print(f"Available: {len(available_stocks)} stocks")
    print(f"Unavailable: {len(unavailable_stocks)} stocks")

    if available_stocks:
        print(f"\nAvailable stocks ({len(available_stocks)}):")
        for stock in available_stocks:
            print(f"  {stock}")

        # Read current niftylarge
        with open('data/constituents/niftylarge_constituents.txt', 'r') as f:
            current_stocks = [line.strip() for line in f.readlines() if line.strip()]

        print(f"Current niftylarge size: {len(current_stocks)}")

        # Add new stocks
        new_stocks = [stock for stock in available_stocks if stock not in current_stocks]
        if new_stocks:
            print(f"Adding {len(new_stocks)} new stocks")

            updated_stocks = current_stocks + new_stocks
            with open('data/constituents/niftylarge_constituents.txt', 'w') as f:
                for stock in sorted(updated_stocks):
                    f.write(f"{stock}\n")

            print(f"Updated niftylarge to {len(updated_stocks)} stocks")
        else:
            print("No new stocks to add")

if __name__ == "__main__":
    test_next_100_stocks()