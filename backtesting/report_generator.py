"""
Report Generator - Creates HTML reports with per-stock results
"""

import pandas as pd
from datetime import datetime


class ReportGenerator:
    """Generate backtesting reports"""
    
    def __init__(self, trades, summary_stats):
        self.trades = trades
        self.stats = summary_stats
        
    def generate_html_report(self, output_file='backtest_results.html'):
        """Generate comprehensive HTML report"""
        
        # Group trades by symbol
        trades_by_symbol = {}
        for trade in self.trades:
            if trade.symbol not in trades_by_symbol:
                trades_by_symbol[trade.symbol] = []
            trades_by_symbol[trade.symbol].append(trade)
        
        # Calculate per-symbol stats
        symbol_stats = {}
        for symbol, symbol_trades in trades_by_symbol.items():
            winning = [t for t in symbol_trades if t.pnl > 0]
            losing = [t for t in symbol_trades if t.pnl <= 0]
            
            symbol_stats[symbol] = {
                'total_trades': len(symbol_trades),
                'wins': len(winning),
                'losses': len(losing),
                'win_rate': (len(winning) / len(symbol_trades)) * 100 if symbol_trades else 0,
                'total_pnl': sum(t.pnl for t in symbol_trades),
                'avg_pnl': sum(t.pnl for t in symbol_trades) / len(symbol_trades) if symbol_trades else 0,
                'best_trade': max(t.pnl for t in symbol_trades) if symbol_trades else 0,
                'worst_trade': min(t.pnl for t in symbol_trades) if symbol_trades else 0,
                'avg_hold_days': sum(t.hold_days for t in symbol_trades) / len(symbol_trades) if symbol_trades else 0
            }
        
        html = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>Backtest Results - {datetime.now().strftime('%Y-%m-%d')}</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 20px; background: #f5f5f5; }}
        h1 {{ color: #2c3e50; }}
        h2 {{ color: #34495e; margin-top: 30px; }}
        .summary {{ background: white; padding: 20px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); margin-bottom: 20px; }}
        .stat-grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 15px; }}
        .stat-box {{ background: #ecf0f1; padding: 15px; border-radius: 6px; text-align: center; }}
        .stat-box .label {{ font-size: 12px; color: #7f8c8d; text-transform: uppercase; }}
        .stat-box .value {{ font-size: 24px; font-weight: bold; margin-top: 5px; }}
        .positive {{ color: #27ae60; }}
        .negative {{ color: #e74c3c; }}
        table {{ width: 100%; border-collapse: collapse; background: white; box-shadow: 0 2px 4px rgba(0,0,0,0.1); margin-top: 10px; }}
        th, td {{ padding: 12px; text-align: left; border-bottom: 1px solid #ddd; }}
        th {{ background: #34495e; color: white; font-weight: 600; cursor: pointer; }}
        tr:hover {{ background: #f9f9f9; }}
        .win {{ background-color: #d4edda; color: #155724; }}
        .loss {{ background-color: #f8d7da; color: #721c24; }}
        .badge {{ display: inline-block; padding: 4px 8px; border-radius: 4px; font-size: 11px; font-weight: bold; }}
        .target {{ background: #27ae60; color: white; }}
        .stop {{ background: #e74c3c; color: white; }}
        .time {{ background: #f39c12; color: white; }}
    </style>
</head>
<body>
    <h1>📊 Backtest Results Report</h1>
    <p style="color: #7f8c8d;">Generated on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
    
    <div class="summary">
        <h2>Overall Performance</h2>
        <div class="stat-grid">
            <div class="stat-box">
                <div class="label">Total Trades</div>
                <div class="value">{self.stats['total_trades']}</div>
            </div>
            <div class="stat-box">
                <div class="label">Win Rate</div>
                <div class="value {'positive' if self.stats['win_rate'] > 50 else 'negative'}">{self.stats['win_rate']:.1f}%</div>
            </div>
            <div class="stat-box">
                <div class="label">Total P&L</div>
                <div class="value {'positive' if self.stats['total_pnl'] > 0 else 'negative'}">₹{self.stats['total_pnl']:,.0f}</div>
            </div>
            <div class="stat-box">
                <div class="label">Return %</div>
                <div class="value {'positive' if self.stats['return_pct'] > 0 else 'negative'}">{self.stats['return_pct']:.2f}%</div>
            </div>
            <div class="stat-box">
                <div class="label">Profit Factor</div>
                <div class="value">{self.stats.get('profit_factor', 0):.2f}</div>
            </div>
            <div class="stat-box">
                <div class="label">Avg R-Multiple</div>
                <div class="value">{self.stats.get('avg_r_multiple', 0):.2f}</div>
            </div>
            <div class="stat-box">
                <div class="label">Avg Hold (Days)</div>
                <div class="value">{self.stats.get('avg_hold_days', 0):.1f}</div>
            </div>
        </div>
    </div>
    
    <div class="summary">
        <h2>Per-Stock Performance</h2>
        <table>
            <thead>
                <tr>
                    <th>Symbol</th>
                    <th>Trades</th>
                    <th>Wins</th>
                    <th>Losses</th>
                    <th>Win Rate</th>
                    <th>Total P&L</th>
                    <th>Avg P&L</th>
                    <th>Best</th>
                    <th>Worst</th>
                    <th>Avg Hold</th>
                </tr>
            </thead>
            <tbody>
"""
        
        # Add rows for each symbol
        for symbol in sorted(symbol_stats.keys()):
            stats = symbol_stats[symbol]
            pnl_class = 'positive' if stats['total_pnl'] > 0 else 'negative'
            
            html += f"""
                <tr>
                    <td><strong>{symbol}</strong></td>
                    <td>{stats['total_trades']}</td>
                    <td>{stats['wins']}</td>
                    <td>{stats['losses']}</td>
                    <td>{stats['win_rate']:.1f}%</td>
                    <td class="{pnl_class}">₹{stats['total_pnl']:,.0f}</td>
                    <td class="{pnl_class}">₹{stats['avg_pnl']:,.0f}</td>
                    <td class="positive">₹{stats['best_trade']:,.0f}</td>
                    <td class="negative">₹{stats['worst_trade']:,.0f}</td>
                    <td>{stats['avg_hold_days']:.1f}d</td>
                </tr>
"""
        
        html += """
            </tbody>
        </table>
    </div>
    
    <div class="summary">
        <h2>All Trades</h2>
        <table id="tradesTable">
            <thead>
                <tr>
                    <th>Symbol</th>
                    <th>Entry Date</th>
                    <th>Exit Date</th>
                    <th>Pattern</th>
                    <th>Direction</th>
                    <th>Entry</th>
                    <th>Exit</th>
                    <th>P&L</th>
                    <th>P&L %</th>
                    <th>R-Multiple</th>
                    <th>Exit Reason</th>
                    <th>Hold Days</th>
                </tr>
            </thead>
            <tbody>
"""
        
        # Add all trades
        for trade in sorted(self.trades, key=lambda t: t.entry_date, reverse=True):
            pnl_class = 'win' if trade.pnl > 0 else 'loss'
            
            exit_reason = (trade.exit_reason or '').upper()
            if exit_reason in ['TARGET']:
                reason_badge = '<span class="badge target">TARGET</span>'
            elif exit_reason in ['STOP', 'SL']:
                reason_badge = '<span class="badge stop">STOP</span>'
            else:
                reason_badge = '<span class="badge time">TIME</span>'
            
            html += f"""
                <tr class="{pnl_class}">
                    <td><strong>{trade.symbol}</strong></td>
                    <td>{trade.entry_date.strftime('%Y-%m-%d')}</td>
                    <td>{trade.exit_date.strftime('%Y-%m-%d')}</td>
                    <td>{trade.pattern}</td>
                    <td>{trade.direction.upper()}</td>
                    <td>₹{trade.entry_price:.2f}</td>
                    <td>₹{trade.exit_price:.2f}</td>
                    <td>₹{trade.pnl:,.0f}</td>
                    <td>{trade.pnl_pct:+.2f}%</td>
                    <td>{trade.r_multiple:.2f}</td>
                    <td>{reason_badge}</td>
                    <td>{trade.hold_days}</td>
                </tr>
"""
        
        html += """
            </tbody>
        </table>
    </div>
    
    <script>
        // Add table sorting
        document.querySelectorAll('th').forEach(header => {
            header.addEventListener('click', function() {
                const table = this.closest('table');
                const tbody = table.querySelector('tbody');
                const rows = Array.from(tbody.querySelectorAll('tr'));
                const index = Array.from(this.parentElement.children).indexOf(this);
                
                rows.sort((a, b) => {
                    const aVal = a.children[index].textContent;
                    const bVal = b.children[index].textContent;
                    return aVal.localeCompare(bVal, undefined, {numeric: true});
                });
                
                tbody.innerHTML = '';
                rows.forEach(row => tbody.appendChild(row));
            });
        });
    </script>
</body>
</html>
"""
        
        # Save report
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(html)
        
        print(f"\n✓ Report saved to: {output_file}")
        return output_file
