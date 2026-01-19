"""
Enhanced HTML report generator with colors, confidence levels, and risk/reward.
"""

from datetime import datetime
from typing import List, Dict, Any, Optional
from pathlib import Path
import json

REPORT_TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title}</title>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}
        
        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #1e3c72 0%, #2a5298 100%);
            color: #333;
            padding: 20px;
            min-height: 100vh;
        }}
        
        .container {{
            max-width: 1400px;
            margin: 0 auto;
        }}
        
        header {{
            background: white;
            border-radius: 8px;
            padding: 25px;
            margin-bottom: 30px;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
            border-left: 5px solid #2a5298;
        }}
        
        header h1 {{
            font-size: 28px;
            margin-bottom: 10px;
            color: #1e3c72;
        }}
        
        header p {{
            color: #666;
            font-size: 14px;
        }}
        
        .stats-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 15px;
            margin-bottom: 30px;
        }}
        
        .stat-card {{
            background: white;
            border-radius: 8px;
            padding: 20px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            border-top: 4px solid #2a5298;
        }}
        
        .stat-card.bullish {{
            border-top-color: #27ae60;
        }}
        
        .stat-card.bearish {{
            border-top-color: #e74c3c;
        }}
        
        .stat-card.index {{
            border-top-color: #f39c12;
        }}
        
        .stat-card h3 {{
            font-size: 12px;
            color: #999;
            text-transform: uppercase;
            margin-bottom: 10px;
            letter-spacing: 1px;
        }}
        
        .stat-card .value {{
            font-size: 24px;
            font-weight: bold;
            color: #1e3c72;
        }}
        
        .stat-card .subtext {{
            font-size: 12px;
            color: #999;
            margin-top: 8px;
        }}
        
        .picks-section {{
            margin-bottom: 30px;
        }}
        
        .section-header {{
            background: white;
            padding: 15px 25px;
            border-radius: 8px 8px 0 0;
            border-bottom: 2px solid #ecf0f1;
            border-left: 5px solid #2a5298;
        }}
        
        .section-header h2 {{
            font-size: 20px;
            color: #1e3c72;
        }}
        
        .picks-table {{
            background: white;
            border-radius: 0 0 8px 8px;
            overflow: hidden;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            margin-bottom: 30px;
        }}
        
        table {{
            width: 100%;
            border-collapse: collapse;
        }}
        
        thead {{
            background: #f8f9fa;
            border-bottom: 2px solid #ecf0f1;
        }}
        
        th {{
            padding: 15px;
            text-align: left;
            font-size: 12px;
            font-weight: 600;
            color: #666;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }}
        
        td {{
            padding: 15px;
            border-bottom: 1px solid #ecf0f1;
            font-size: 14px;
        }}
        
        tr:hover {{
            background: #f8f9fa;
        }}
        
        tr:last-child td {{
            border-bottom: none;
        }}
        
        .symbol {{
            font-weight: 600;
            color: #1e3c72;
        }}
        
        .badge {{
            display: inline-block;
            padding: 4px 12px;
            border-radius: 20px;
            font-size: 12px;
            font-weight: 600;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }}
        
        .badge.bullish {{
            background: #d4edda;
            color: #155724;
        }}
        
        .badge.bearish {{
            background: #f8d7da;
            color: #721c24;
        }}
        
        .badge.high {{
            background: #cfe2ff;
            color: #084298;
        }}
        
        .badge.medium {{
            background: #fff3cd;
            color: #664d03;
        }}
        
        .badge.low {{
            background: #e2e3e5;
            color: #383d41;
        }}
        
        .score {{
            font-weight: 600;
            text-align: center;
        }}
        
        .score.strong {{
            color: #27ae60;
        }}
        
        .score.moderate {{
            color: #f39c12;
        }}
        
        .score.weak {{
            color: #e74c3c;
        }}
        
        .metrics {{
            display: flex;
            gap: 10px;
            font-size: 12px;
            color: #666;
        }}
        
        .metric {{
            display: flex;
            align-items: center;
            gap: 4px;
        }}
        
        .metric-label {{
            font-weight: 600;
        }}
        
        .risk-reward {{
            text-align: center;
            font-size: 12px;
        }}
        
        .risk-reward .ratio {{
            font-weight: 600;
            color: #1e3c72;
            font-size: 16px;
        }}
        
        .no-picks {{
            background: white;
            border-radius: 8px;
            padding: 40px 25px;
            text-align: center;
            color: #999;
        }}
        
        .no-picks p {{
            font-size: 16px;
        }}
        
        footer {{
            background: white;
            border-radius: 8px;
            padding: 20px 25px;
            text-align: center;
            color: #999;
            font-size: 12px;
            margin-top: 30px;
            border-top: 1px solid #ecf0f1;
        }}
        
        .confidence-bar {{
            display: inline-block;
            height: 20px;
            border-radius: 3px;
            margin: 2px;
            padding: 0 8px;
            display: flex;
            align-items: center;
            font-size: 11px;
            font-weight: 600;
        }}
        
        .conf-high {{
            background: #d4edda;
            color: #155724;
            width: 80%;
        }}
        
        .conf-medium {{
            background: #fff3cd;
            color: #664d03;
            width: 60%;
        }}
        
        .conf-low {{
            background: #f8d7da;
            color: #721c24;
            width: 40%;
        }}
        
        @media (max-width: 768px) {{
            .stats-grid {{
                grid-template-columns: 1fr;
            }}
            
            table {{
                font-size: 12px;
            }}
            
            th, td {{
                padding: 10px;
            }}
            
            .metrics {{
                flex-direction: column;
                gap: 4px;
            }}
        }}
    </style>
</head>
<body>
    <div class="container">
        <header>
            <h1>{title}</h1>
            <p>Generated on {timestamp}</p>
        </header>
        
        <div class="stats-grid">
            {stats_cards}
        </div>
        
        {picks_sections}
        
        <footer>
            <p>Report generated by AlgoOptions Screener | {timestamp}</p>
        </footer>
    </div>
</body>
</html>"""


def get_confidence_badge_html(confidence: str) -> str:
    """Generate HTML for confidence badge."""
    conf_map = {
        "high": ("HIGH", "high"),
        "medium": ("MEDIUM", "medium"),
        "low": ("LOW", "low"),
    }
    label, css_class = conf_map.get(confidence.lower(), ("UNKNOWN", "low"))
    return f'<span class="badge {css_class}">{label}</span>'


def get_direction_badge_html(direction: str) -> str:
    """Generate HTML for direction badge."""
    direction_str = str(direction).lower() if direction else ""
    if "bull" in direction_str:
        return '<span class="badge bullish">BULLISH</span>'
    elif "bear" in direction_str:
        return '<span class="badge bearish">BEARISH</span>'
    else:
        return '<span class="badge">NEUTRAL</span>'


def get_score_class(score: float) -> str:
    """Get CSS class for score based on value."""
    if abs(score) > 0.5:
        return "strong"
    elif abs(score) > 0.3:
        return "moderate"
    else:
        return "weak"


def format_metric(label: str, value: Any, decimals: int = 2) -> str:
    """Format a metric for display."""
    if isinstance(value, float):
        formatted = f"{value:.{decimals}f}"
    else:
        formatted = str(value)
    return f'<span class="metric"><span class="metric-label">{label}:</span>{formatted}</span>'


class EnhancedReportGenerator:
    """Generates enhanced HTML reports with styling and visualizations."""
    
    def __init__(self):
        self.report_dir = Path(__file__).parent.parent / "reports"
        self.report_dir.mkdir(exist_ok=True)
    
    def generate_report(self, title: str, picks_data: Dict[str, List[Dict[str, Any]]], 
                       index_bias: Optional[float] = None, 
                       index_price: Optional[float] = None) -> str:
        """Generate enhanced HTML report."""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        # Build stats cards
        stats_html = self._build_stats_cards(picks_data, index_bias, index_price)
        
        # Build picks sections
        picks_html = self._build_picks_sections(picks_data)
        
        # Render template
        report_html = REPORT_TEMPLATE.format(
            title=title,
            timestamp=timestamp,
            stats_cards=stats_html,
            picks_sections=picks_html,
        )
        
        return report_html
    
    def _build_stats_cards(self, picks_data: Dict[str, List[Dict[str, Any]]], 
                          index_bias: Optional[float], index_price: Optional[float]) -> str:
        """Build statistics cards HTML."""
        cards = []
        
        # Total picks
        total_picks = sum(len(picks) for picks in picks_data.values())
        cards.append(f"""
        <div class="stat-card">
            <h3>Total Picks</h3>
            <div class="value">{total_picks}</div>
        </div>""")
        
        # Bullish picks
        bullish_picks = len(picks_data.get("bullish", []))
        cards.append(f"""
        <div class="stat-card bullish">
            <h3>Bullish</h3>
            <div class="value" style="color: #27ae60;">{bullish_picks}</div>
            <div class="subtext">{bullish_picks/max(total_picks, 1)*100:.0f}% of picks</div>
        </div>""")
        
        # Bearish picks
        bearish_picks = len(picks_data.get("bearish", []))
        cards.append(f"""
        <div class="stat-card bearish">
            <h3>Bearish</h3>
            <div class="value" style="color: #e74c3c;">{bearish_picks}</div>
            <div class="subtext">{bearish_picks/max(total_picks, 1)*100:.0f}% of picks</div>
        </div>""")
        
        # Index bias
        if index_bias is not None:
            bias_direction = "BULLISH" if index_bias > 0 else "BEARISH"
            bias_color = "#27ae60" if index_bias > 0 else "#e74c3c"
            cards.append(f"""
        <div class="stat-card index">
            <h3>Market Bias</h3>
            <div class="value" style="color: {bias_color};">{bias_direction}</div>
            <div class="subtext">Strength: {abs(index_bias):.3f}</div>
        </div>""")
        
        # Index price
        if index_price is not None:
            cards.append(f"""
        <div class="stat-card index">
            <h3>NIFTY 50</h3>
            <div class="value">{index_price:,.0f}</div>
            <div class="subtext">Current level</div>
        </div>""")
        
        return "".join(cards)
    
    def _build_picks_sections(self, picks_data: Dict[str, List[Dict[str, Any]]]) -> str:
        """Build picks sections (bullish and bearish)."""
        sections = []
        
        # Bullish section
        bullish_picks = picks_data.get("bullish", [])
        sections.append(self._build_picks_table(
            "Bullish Picks",
            bullish_picks,
            "bullish"
        ))
        
        # Bearish section
        bearish_picks = picks_data.get("bearish", [])
        sections.append(self._build_picks_table(
            "Bearish Picks",
            bearish_picks,
            "bearish"
        ))
        
        return "".join(sections)
    
    def _build_picks_table(self, title: str, picks: List[Dict[str, Any]], 
                          direction: str) -> str:
        """Build a picks table section."""
        if not picks:
            return f"""
        <div class="picks-section">
            <div class="section-header">
                <h2>{title}</h2>
            </div>
            <div class="no-picks">
                <p>No {direction} picks generated</p>
            </div>
        </div>"""
        
        # Build table rows
        rows = []
        for pick in picks:
            symbol = pick.get("symbol", "N/A")
            score = float(pick.get("final_score", pick.get("score", 0)))
            # Determine direction from score if not in pick
            if score > 0.05:
                direction_text = "BULLISH"
            elif score < -0.05:
                direction_text = "BEARISH"
            else:
                direction_text = "NEUTRAL"
            
            confidence = pick.get("confidence", 50)  # Default to 50 if missing
            # Convert confidence to string for badge
            if isinstance(confidence, (int, float)):
                conf_level = "high" if confidence > 70 else ("medium" if confidence > 40 else "low")
            else:
                conf_level = str(confidence).lower()
            
            price = float(pick.get("price", 0))
            rsi = float(pick.get("rsi", 50)) if pick.get("rsi") is not None else 50
            ema_trend = float(pick.get("ema_score", 0)) if pick.get("ema_score") is not None else 0
            atr = float(pick.get("atr", 0)) if pick.get("atr") is not None else 0
            
            # Calculate risk/reward
            atr_val = abs(atr) if atr else 0.01
            if atr_val > 0:
                reward = atr_val * 2  # 2x ATR for reward
                risk_reward_ratio = reward / atr_val
            else:
                risk_reward_ratio = 2.0
            
            score_class = get_score_class(score)
            
            metrics_html = f"""
                <div class="metrics">
                    {format_metric("RSI", rsi, 0)}
                    {format_metric("EMA", ema_trend, 2)}
                    {format_metric("ATR", atr, 2)}
                </div>
            """
            
            rows.append(f"""
            <tr>
                <td><span class="symbol">{symbol}</span></td>
                <td>{get_direction_badge_html(direction_text)}</td>
                <td><span class="score {score_class}">{score:.3f}</span></td>
                <td><strong>₹{price:,.2f}</strong></td>
                <td>{get_confidence_badge_html(conf_level)}</td>
                <td>{metrics_html}</td>
                <td><div class="risk-reward"><div class="ratio">{risk_reward_ratio:.1f}:1</div><small>R/R</small></div></td>
            </tr>
            """)
        
        table_html = f"""
        <div class="picks-section">
            <div class="section-header">
                <h2>{title}</h2>
            </div>
            <div class="picks-table">
                <table>
                    <thead>
                        <tr>
                            <th>Symbol</th>
                            <th>Direction</th>
                            <th>Score</th>
                            <th>Entry Price</th>
                            <th>Confidence</th>
                            <th>Technical</th>
                            <th>Risk/Reward</th>
                        </tr>
                    </thead>
                    <tbody>
                        {''.join(rows)}
                    </tbody>
                </table>
            </div>
        </div>"""
        
        return table_html
    
    def save_report(self, html_content: str, filename: str = None) -> Path:
        """Save HTML report to file."""
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"screener_report_{timestamp}.html"
        
        filepath = self.report_dir / filename
        filepath.write_text(html_content, encoding='utf-8')
        return filepath
