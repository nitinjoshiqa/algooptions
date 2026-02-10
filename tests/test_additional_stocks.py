import os
import sys
sys.path.append(os.path.dirname(__file__))

from data_providers import YFinanceProvider

def test_additional_stocks():
    # Read the additional stocks file
    with open('ARCHIVE/additional_100_stocks.txt', 'r') as f:
        content = f.read().strip()

    # Split by \n to get individual stocks
    stocks = content.split('\\n')

    print(f"Found {len(stocks)} stocks to test:")
    for stock in stocks:
        print(f"  {stock}")

    # Initialize provider
    provider = YFinanceProvider()

    available_stocks = []
    unavailable_stocks = []

    for stock in stocks:
        if not stock.strip():
            continue

        symbol = stock.strip() + '.NS'
        try:
            price = provider.get_spot_price(symbol)
            if price is not None and price > 0:
                available_stocks.append(stock.strip())
                print(f"✓ {stock.strip()}: ₹{price:.2f}")
            else:
                unavailable_stocks.append(stock.strip())
                print(f"✗ {stock.strip()}: No data")
        except Exception as e:
            unavailable_stocks.append(stock.strip())
            print(f"✗ {stock.strip()}: Error - {str(e)}")

    print(f"\nSummary:")
    print(f"Available: {len(available_stocks)} stocks")
    print(f"Unavailable: {len(unavailable_stocks)} stocks")

    if available_stocks:
        print(f"\nAvailable stocks: {', '.join(available_stocks)}")

        # Read current niftylarge
        with open('data/constituents/niftylarge_constituents.txt', 'r') as f:
            current_stocks = [line.strip() for line in f.readlines() if line.strip()]

        print(f"Current niftylarge size: {len(current_stocks)}")

        # Add new stocks
        new_stocks = [stock for stock in available_stocks if stock not in current_stocks]
        if new_stocks:
            print(f"Adding {len(new_stocks)} new stocks: {', '.join(new_stocks)}")

            updated_stocks = current_stocks + new_stocks
            with open('data/constituents/niftylarge_constituents.txt', 'w') as f:
                for stock in sorted(updated_stocks):
                    f.write(f"{stock}\n")

            print(f"Updated niftylarge to {len(updated_stocks)} stocks")
        else:
            print("No new stocks to add")

if __name__ == "__main__":
    test_additional_stocks()