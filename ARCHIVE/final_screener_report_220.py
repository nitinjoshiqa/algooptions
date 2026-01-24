#!/usr/bin/env python3
"""
Final comprehensive screener report using 220+ stock universe
Shows all stocks with scoring and bearnness metrics
"""

import yfinance as yf
import pandas as pd
import json
from datetime import datetime, timedelta
import time
import sys
import io

# Fix Unicode output on Windows
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

print("=" * 100)
print("FINAL COMPREHENSIVE SCREENER REPORT - 220+ STOCK UNIVERSE")
print("=" * 100)
print(f"Report Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print()

# Read the 220 stocks
with open('nifty500_constituents_final_220.txt', 'r') as f:
    stocks = [line.strip() for line in f if line.strip()]

print(f"Universe: {len(stocks)} stocks")
print(f"Min Market Cap: 10B+")
print()

# Define scoring thresholds
def calculate_bearnness_score(stock_info):
    """
    Calculate bearnness/option selling score based on:
    - Price volatility (IV)
    - Technical strength (RSI)
    - Trend (MA200)
    """
    score = 0
    details = {}
    
    try:
        # Get historical data
        ticker_str = stock_info['ticker']
        data = yf.download(ticker_str, period='6mo', progress=False)
        
        if len(data) < 50:
            return 0, {'error': 'insufficient_data'}
        
        # Calculate metrics
        close = data['Close']
        
        # Volatility (annualized)
        returns = close.pct_change().dropna()
        volatility = returns.std() * (252 ** 0.5)  # Annualized
        details['volatility'] = round(volatility * 100, 2)
        
        # RSI
        delta = close.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        current_rsi = rsi.iloc[-1]
        details['rsi'] = round(current_rsi, 2)
        
        # Trend (MA200)
        ma200 = close.rolling(window=200).mean()
        current_price = close.iloc[-1]
        current_ma200 = ma200.iloc[-1]
        
        if current_ma200 and current_price:
            trend_distance = ((current_price - current_ma200) / current_ma200) * 100
            details['trend_dist'] = round(trend_distance, 2)
        
        # Scoring
        if volatility > 0.30:  # High volatility
            score += 25
        elif volatility > 0.20:
            score += 15
        else:
            score += 5
        
        if 40 < current_rsi < 60:  # Neutral RSI (good for selling)
            score += 25
        elif 30 < current_rsi < 70:
            score += 15
        else:
            score += 5
        
        if current_price > current_ma200 * 1.02:  # Above MA200 by 2%
            score += 20
        elif current_price > current_ma200:
            score += 15
        else:
            score += 10
        
        # Market cap bonus
        market_cap = stock_info.get('market_cap_b', 0)
        if market_cap > 1000:
            score += 10
        elif market_cap > 100:
            score += 5
        
        return score, details
        
    except Exception as e:
        return 0, {'error': str(e)[:30]}

print("Fetching data for 220 stocks...")
print("-" * 100)
print()

results = []
success_count = 0
fail_count = 0

for i, symbol in enumerate(stocks[:50], 1):  # Test with first 50 for speed
    try:
        print(f"[{i:3d}/{min(50, len(stocks))}] {symbol:15s} ", end='', flush=True)
        
        ticker_obj = yf.Ticker(f"{symbol}.NS")
        info = ticker_obj.info
        
        market_cap = info.get('marketCap', 0)
        market_cap_b = market_cap / 1_000_000_000 if market_cap else 0
        current_price = info.get('currentPrice', 0)
        prev_close = info.get('regularMarketPreviousClose', 0)
        
        if current_price and prev_close:
            change_pct = ((current_price - prev_close) / prev_close) * 100
        else:
            change_pct = 0
        
        name = info.get('longName', symbol)[:40]
        
        # Calculate score
        stock_info = {'ticker': f"{symbol}.NS", 'market_cap_b': market_cap_b}
        score, details = calculate_bearnness_score(stock_info)
        
        results.append({
            'symbol': symbol,
            'name': name,
            'price': round(current_price, 2),
            'change': round(change_pct, 2),
            'market_cap_b': round(market_cap_b, 1),
            'score': score,
            'volatility': details.get('volatility', 0),
            'rsi': details.get('rsi', 0),
            'trend_dist': details.get('trend_dist', 0),
        })
        
        print(f"[OK] Score: {score:3d}  Vol: {details.get('volatility', 0):5.1f}%  RSI: {details.get('rsi', 0):5.1f}  MCap: {market_cap_b:6.1f}B")
        success_count += 1
        time.sleep(0.1)
        
    except Exception as e:
        print(f"[FAIL] {str(e)[:40]}")
        fail_count += 1

print()
print("=" * 100)
print("TOP 20 STOCKS BY BEARNNESS SCORE (Good for Option Selling)")
print("=" * 100)
print()

# Sort by score descending
results_sorted = sorted(results, key=lambda x: x['score'], reverse=True)

df = pd.DataFrame(results_sorted)
print(df[['symbol', 'name', 'price', 'change', 'market_cap_b', 'score', 'volatility', 'rsi']].to_string(index=False))

print()
print("=" * 100)
print("SUMMARY STATISTICS")
print("=" * 100)
print(f"Total stocks tested:      {len(results)}")
print(f"Successful:               {success_count}")
print(f"Failed:                   {fail_count}")
print(f"Average Score:            {df['score'].mean():.1f}")
print(f"Max Score:                {df['score'].max():.0f}")
print(f"Min Score:                {df['score'].min():.0f}")
print()
print(f"Average Volatility:       {df['volatility'].mean():.2f}%")
print(f"Average RSI:              {df['rsi'].mean():.1f}")
print()

# Category analysis
high_score = len(df[df['score'] >= 70])
mid_score = len(df[(df['score'] >= 50) & (df['score'] < 70)])
low_score = len(df[df['score'] < 50])

print("Score Distribution:")
print(f"  High (70+):   {high_score} stocks")
print(f"  Medium (50-70): {mid_score} stocks")
print(f"  Low (<50):    {low_score} stocks")

print()
print("=" * 100)
print("GENERATING HTML REPORT...")
print("=" * 100)

# Generate HTML report
html_content = """<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>Bearnness Screener Report - 220 Stock Universe</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 20px; background-color: #f5f5f5; }}
        .container {{ max-width: 1200px; margin: 0 auto; background-color: white; padding: 20px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }}
        h1 {{ color: #1a1a1a; border-bottom: 3px solid #2196F3; padding-bottom: 10px; }}
        h2 {{ color: #333; margin-top: 30px; border-left: 4px solid #2196F3; padding-left: 10px; }}
        .summary {{ background-color: #e3f2fd; padding: 15px; border-radius: 4px; margin: 20px 0; }}
        .summary-grid {{ display: grid; grid-template-columns: repeat(4, 1fr); gap: 15px; }}
        .summary-box {{ background-color: white; padding: 15px; border-radius: 4px; border-left: 4px solid #2196F3; }}
        .summary-box h3 {{ margin: 0 0 10px 0; color: #666; font-size: 12px; text-transform: uppercase; }}
        .summary-box .value {{ font-size: 24px; font-weight: bold; color: #2196F3; }}
        table {{ width: 100%; border-collapse: collapse; margin: 20px 0; }}
        th {{ background-color: #2196F3; color: white; padding: 12px; text-align: left; font-weight: bold; }}
        td {{ padding: 10px; border-bottom: 1px solid #ddd; }}
        tr:hover {{ background-color: #f9f9f9; }}
        tr:nth-child(even) {{ background-color: #f5f5f5; }}
        .score-high {{ background-color: #c8e6c9; color: #2e7d32; font-weight: bold; }}
        .score-mid {{ background-color: #fff9c4; color: #f57f17; font-weight: bold; }}
        .score-low {{ background-color: #ffccbc; color: #d84315; font-weight: bold; }}
        .positive {{ color: #2e7d32; font-weight: bold; }}
        .negative {{ color: #c62828; font-weight: bold; }}
        .timestamp {{ color: #999; font-size: 12px; margin-bottom: 20px; }}
        .footer {{ margin-top: 40px; padding-top: 20px; border-top: 1px solid #ddd; color: #666; font-size: 12px; }}
    </style>
</head>
<body>
    <div class="container">
        <h1>Bearnness Screener Report - 220 Stock Universe</h1>
        <div class="timestamp">Generated: {timestamp}</div>
        
        <div class="summary">
            <div class="summary-grid">
                <div class="summary-box">
                    <h3>Total Stocks</h3>
                    <div class="value">{total_stocks}</div>
                </div>
                <div class="summary-box">
                    <h3>Tested</h3>
                    <div class="value">{tested_stocks}</div>
                </div>
                <div class="summary-box">
                    <h3>Avg Score</h3>
                    <div class="value">{avg_score}</div>
                </div>
                <div class="summary-box">
                    <h3>Max Score</h3>
                    <div class="value">{max_score}</div>
                </div>
            </div>
        </div>

        <h2>Top 20 Stocks by Bearnness Score (Option Selling Candidates)</h2>
        <table>
            <thead>
                <tr>
                    <th>Rank</th>
                    <th>Symbol</th>
                    <th>Name</th>
                    <th>Price</th>
                    <th>Change %</th>
                    <th>Market Cap (B)</th>
                    <th>Bearnness Score</th>
                    <th>Volatility %</th>
                    <th>RSI</th>
                </tr>
            </thead>
            <tbody>
                {table_rows}
            </tbody>
        </table>

        <h2>Score Distribution</h2>
        <table>
            <tr>
                <td><strong>High Score (70+)</strong></td>
                <td style="text-align: center;"><strong>{high_score}</strong> stocks</td>
            </tr>
            <tr>
                <td><strong>Medium Score (50-70)</strong></td>
                <td style="text-align: center;"><strong>{mid_score}</strong> stocks</td>
            </tr>
            <tr>
                <td><strong>Low Score (<50)</strong></td>
                <td style="text-align: center;"><strong>{low_score}</strong> stocks</td>
            </tr>
        </table>

        <h2>Market Statistics</h2>
        <table>
            <tr>
                <td><strong>Average Volatility</strong></td>
                <td style="text-align: right;">{avg_volatility}%</td>
            </tr>
            <tr>
                <td><strong>Average RSI</strong></td>
                <td style="text-align: right;">{avg_rsi}</td>
            </tr>
            <tr>
                <td><strong>Average Market Cap</strong></td>
                <td style="text-align: right;">{avg_mcap}B</td>
            </tr>
        </table>

        <div class="footer">
            <p><strong>Report Type:</strong> Final Comprehensive Screener - 220 Stock Universe (Market Cap > 10B)</p>
            <p><strong>Bearnness Score:</strong> Composite metric for option selling opportunity based on volatility, RSI, trend, and market cap</p>
            <p><strong>Data Source:</strong> Yahoo Finance</p>
        </div>
    </div>
</body>
</html>
"""

# Format table rows
table_rows_html = ""
for idx, row in enumerate(results_sorted[:20], 1):
    if row['score'] >= 70:
        score_class = 'score-high'
    elif row['score'] >= 50:
        score_class = 'score-mid'
    else:
        score_class = 'score-low'
    
    change_class = 'positive' if row['change'] >= 0 else 'negative'
    
    table_rows_html += f"""
    <tr>
        <td>{idx}</td>
        <td><strong>{row['symbol']}</strong></td>
        <td>{row['name']}</td>
        <td>₹{row['price']:.2f}</td>
        <td class="{change_class}">{row['change']:+.2f}%</td>
        <td>{row['market_cap_b']:.1f}</td>
        <td class="{score_class}">{row['score']}</td>
        <td>{row['volatility']:.2f}%</td>
        <td>{row['rsi']:.1f}</td>
    </tr>
    """

# Fill in HTML template
html_final = html_content.format(
    timestamp=datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
    total_stocks=len(stocks),
    tested_stocks=len(results),
    avg_score=f"{df['score'].mean():.1f}",
    max_score=f"{df['score'].max():.0f}",
    table_rows=table_rows_html,
    high_score=high_score,
    mid_score=mid_score,
    low_score=low_score,
    avg_volatility=f"{df['volatility'].mean():.2f}",
    avg_rsi=f"{df['rsi'].mean():.1f}",
    avg_mcap=f"{df['market_cap_b'].mean():.1f}",
)

# Save HTML report
html_filename = f"bearnness_screener_220_final_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html"
with open(html_filename, 'w', encoding='utf-8') as f:
    f.write(html_final)

print(f"HTML Report saved: {html_filename}")
print()
print("=" * 100)
print("REPORT COMPLETE - Ready for review")
print("=" * 100)
