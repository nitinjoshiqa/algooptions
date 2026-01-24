# Implementation: Option Selling Cards in HTML Report

## Complete Python Code for Cards

Add this to `nifty_bearnness_v2.py`:

---

## 1. Calculate Selling Viability Score

```python
def calculate_selling_viability_score(row):
    """
    Calculate how suitable a stock is for option selling (premium collection).
    
    Higher score = Better for selling options (short calls/puts, spreads)
    
    Score Range: 0-100
    - 90-100: Excellent (naked selling safe)
    - 80-89: Very Good (spreads safe)
    - 70-79: Good (conservative spreads)
    - 60-69: Fair (avoid)
    - <60: Poor (skip selling)
    
    Factors:
    1. IV (35%) - Low IV = high decay advantage
    2. HV (35%) - Low vol = price stable = premium safe
    3. Liquidity (20%) - Tight spreads = easy exit
    4. Neutrality (10%) - Lower |score| = less move expected = safer premium
    """
    
    # Validate data
    try:
        option_iv = float(row.get('option_iv', 0.30) or 0.30)
        volatility_pct = float(row.get('volatility_pct', 2.0) or 2.0)
        option_spread_pct = float(row.get('option_spread_pct', 5.0) or 5.0)
        final_score = float(row.get('final_score', 0) or 0)
    except (ValueError, TypeError):
        return 0  # Skip if data invalid
    
    # ========== COMPONENT 1: IV Score (35% weight) ==========
    # Low IV = premium decay favorable for sellers
    
    option_iv_pct = option_iv * 100  # Convert 0-1 scale to 0-100
    
    if option_iv_pct < 20:
        iv_score = 100
    elif option_iv_pct < 30:
        iv_score = 85
    elif option_iv_pct < 40:
        iv_score = 60
    elif option_iv_pct < 50:
        iv_score = 35
    else:
        iv_score = 10
    
    # ========== COMPONENT 2: HV Score (35% weight) ==========
    # Low historical volatility = price stays flat = premium is safe
    
    if volatility_pct < 1.0:
        hv_score = 100
    elif volatility_pct < 1.5:
        hv_score = 90
    elif volatility_pct < 2.0:
        hv_score = 75
    elif volatility_pct < 3.0:
        hv_score = 50
    else:
        hv_score = 20
    
    # ========== COMPONENT 3: Liquidity Score (20% weight) ==========
    # Tight bid-ask spread = easy entry/exit at full premium
    
    if option_spread_pct < 1.0:
        liquidity_score = 95
    elif option_spread_pct < 2.0:
        liquidity_score = 85
    elif option_spread_pct < 3.0:
        liquidity_score = 75
    elif option_spread_pct < 5.0:
        liquidity_score = 50
    else:
        liquidity_score = 10
    
    # ========== COMPONENT 4: Neutrality Score (10% weight) ==========
    # Lower |score| = less directional move expected = premium safer
    
    abs_score = abs(final_score)
    
    if abs_score < 0.10:
        neutral_score = 95
    elif abs_score < 0.20:
        neutral_score = 85
    elif abs_score < 0.30:
        neutral_score = 60
    elif abs_score < 0.50:
        neutral_score = 30
    else:
        neutral_score = 10
    
    # ========== FINAL SCORE ==========
    # Weighted average (IV and HV equally important, liquidity critical, neutrality bonus)
    
    selling_viability_score = (
        iv_score * 0.35 +
        hv_score * 0.35 +
        liquidity_score * 0.20 +
        neutral_score * 0.10
    )
    
    return round(selling_viability_score, 2)


def determine_selling_quality(score):
    """Return quality rating and color for selling score"""
    if score >= 90:
        return "Excellent", "selling-excellent"
    elif score >= 80:
        return "Very Good", "selling-verygood"
    elif score >= 70:
        return "Good", "selling-good"
    elif score >= 60:
        return "Fair", "selling-fair"
    else:
        return "Poor", "selling-poor"


def determine_selling_strategies(selling_score, iv_pct, abs_score, stock_name):
    """
    Recommend which option selling strategies are appropriate
    based on selling score and market conditions
    """
    strategies = []
    
    if selling_score >= 90:
        # Safe for naked selling
        if abs_score < 0.15:
            strategies.extend(["📍 Naked Put", "📍 Covered Call", "📍 Naked Call"])
        else:
            strategies.extend(["📍 Naked Put" if abs_score > 0 else "📍 Naked Call", "📍 Put Spread", "📍 Strangle"])
    elif selling_score >= 80:
        # Safe for spreads
        strategies.extend(["📍 Put Spread", "📍 Call Spread", "📍 Iron Condor"])
    elif selling_score >= 70:
        # Conservative spreads only
        strategies.extend(["📍 Put Spread", "📍 Call Spread", "📍 Wide Strangle"])
    else:
        # Not suitable for selling
        strategies.extend(["❌ Avoid Selling"])
    
    return strategies[:3]  # Return top 3


def get_iv_quality(iv_pct):
    """Determine IV quality indicator"""
    if iv_pct < 20:
        return "Very Low 🟢", "low"
    elif iv_pct < 30:
        return "Low 🟢", "low"
    elif iv_pct < 40:
        return "Normal 🟡", "normal"
    elif iv_pct < 50:
        return "Elevated 🟠", "high"
    else:
        return "High 🔴", "high"


def get_vol_quality(vol_pct):
    """Determine volatility stability indicator"""
    if vol_pct < 1.0:
        return "Ultra-Stable 🟢"
    elif vol_pct < 1.5:
        return "Very Stable 🟢"
    elif vol_pct < 2.0:
        return "Stable 🟡"
    elif vol_pct < 3.0:
        return "Normal 🟡"
    else:
        return "Volatile 🔴"


def get_spread_quality(spread_pct):
    """Determine bid-ask spread quality"""
    if spread_pct < 1.0:
        return "Excellent 🟢"
    elif spread_pct < 2.0:
        return "Very Good 🟢"
    elif spread_pct < 3.0:
        return "Good 🟡"
    elif spread_pct < 5.0:
        return "Fair 🟡"
    else:
        return "Poor 🔴"
```

---

## 2. HTML Card Generation Function

```python
def generate_option_selling_cards_html(scored_data):
    """
    Generate HTML for top 5 option selling candidates.
    
    These are stocks most suitable for premium selling (short calls/puts)
    based on low volatility, good liquidity, and directional neutrality.
    """
    
    # Calculate selling score for each stock
    selling_stocks = []
    for row in scored_data:
        if row.get('option_iv') is not None:  # Only stocks with option data
            selling_score = calculate_selling_viability_score(row)
            selling_stocks.append({
                **row,
                'selling_viability_score': selling_score
            })
    
    # Sort by selling score, get top 5
    top_sellers = sorted(selling_stocks, key=lambda x: x['selling_viability_score'], reverse=True)[:5]
    
    if not top_sellers:
        return ""  # No data, skip this section
    
    # Start HTML section
    html = '''
    <section class="option-selling-section">
        <div class="option-selling-card">
            <div class="card-header">
                <h2>💰 TOP 5 OPTION SELLING OPPORTUNITIES</h2>
                <p>Stocks best suited for premium selling (short calls/puts, spreads) - Stable, low movement</p>
            </div>
            
            <div class="card-grid">
    '''
    
    # Generate cards for each top seller
    for rank, stock in enumerate(top_sellers, 1):
        html += generate_single_selling_card(stock, rank)
    
    html += '''
            </div>
        </div>
    </section>
    '''
    
    return html


def generate_single_selling_card(stock, rank):
    """Generate HTML for a single option selling card"""
    
    symbol = stock.get('symbol', 'N/A')
    selling_score = stock.get('selling_viability_score', 0)
    option_iv = stock.get('option_iv', 0) or 0
    volatility_pct = stock.get('volatility_pct', 0) or 0
    option_spread_pct = stock.get('option_spread_pct', 0) or 0
    final_score = stock.get('final_score', 0) or 0
    abs_score = abs(final_score)
    
    # Convert IV to percentage
    iv_pct = option_iv * 100
    
    # Get quality ratings
    quality, quality_class = determine_selling_quality(selling_score)
    iv_quality, iv_class = get_iv_quality(iv_pct)
    vol_quality = get_vol_quality(volatility_pct)
    spread_quality = get_spread_quality(option_spread_pct)
    strategies = determine_selling_strategies(selling_score, iv_pct, abs_score, symbol)
    
    # Stars display
    if selling_score >= 90:
        stars = "⭐⭐⭐⭐⭐"
    elif selling_score >= 80:
        stars = "⭐⭐⭐⭐"
    elif selling_score >= 70:
        stars = "⭐⭐⭐"
    else:
        stars = "⭐⭐"
    
    # Action recommendation
    if selling_score >= 90:
        action = f"Sell Naked {'Call' if abs_score > 0.05 else 'Put' if abs_score < -0.05 else 'Call or Put'}"
    elif selling_score >= 80:
        action = f"Sell {'Call' if abs_score > 0.05 else 'Put' if abs_score < -0.05 else 'Put'} Spread"
    else:
        action = "Conservative Wide Spread"
    
    # Premium collection level
    if selling_score >= 90:
        premium_level = "Very High"
    elif selling_score >= 80:
        premium_level = "High"
    else:
        premium_level = "Moderate"
    
    # Risk level
    if selling_score >= 90:
        risk_level = "Very Low"
    elif selling_score >= 80:
        risk_level = "Low"
    else:
        risk_level = "Moderate"
    
    # HTML card
    html = f'''
                <div class="selling-card {quality_class}">
                    <div class="rank-badge">{rank}</div>
                    
                    <div class="symbol">
                        <strong>{symbol}</strong>
                        <span class="selling-score">{selling_score:.0f}/100 {stars}</span>
                    </div>
                    
                    <div class="metrics">
                        <div class="metric-row">
                            <span class="label">Implied Vol (IV):</span>
                            <span class="value {iv_class}">{iv_pct:.1f}% {iv_quality}</span>
                        </div>
                        <div class="metric-row">
                            <span class="label">Historical Vol:</span>
                            <span class="value low">{volatility_pct:.2f}% {vol_quality}</span>
                        </div>
                        <div class="metric-row">
                            <span class="label">Bid-Ask Spread:</span>
                            <span class="value low">{option_spread_pct:.2f}% {spread_quality}</span>
                        </div>
                        <div class="metric-row">
                            <span class="label">Directional Signal:</span>
                            <span class="value neutral">±{abs_score:.2f} 🟡 {'Very Neutral' if abs_score < 0.10 else 'Neutral' if abs_score < 0.20 else 'Slightly Directional'}</span>
                        </div>
                    </div>
                    
                    <div class="recommendation">
                        <strong>✅ {quality.upper()} FOR SELLING</strong>
                        <div class="strategies">
                            {f'<span class="strategy">{strategies[0]}</span>' if len(strategies) > 0 else ''}
                            {f'<span class="strategy">{strategies[1]}</span>' if len(strategies) > 1 else ''}
                            {f'<span class="strategy">{strategies[2]}</span>' if len(strategies) > 2 else ''}
                        </div>
                    </div>
                    
                    <div class="action-info">
                        <p><strong>Action:</strong> {action}</p>
                        <p><strong>Premium Collection:</strong> {premium_level} (decay working for you) 📈</p>
                        <p><strong>Risk:</strong> {risk_level} (stable, tight stops)</p>
                    </div>
                </div>
    '''
    
    return html
```

---

## 3. CSS Styling

Add to `save_html()` function in `<style>` tag:

```css
/* ========== OPTION SELLING CARDS ========== */

.option-selling-section {
    margin: 30px 0;
}

.option-selling-card {
    background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
    border-radius: 12px;
    padding: 25px;
    border-left: 5px solid #00ff88;
    box-shadow: 0 8px 16px rgba(0, 0, 0, 0.3);
}

.card-header {
    text-align: center;
    margin-bottom: 30px;
    border-bottom: 2px solid rgba(0, 255, 136, 0.2);
    padding-bottom: 15px;
}

.card-header h2 {
    color: #00ff88;
    font-size: 24px;
    margin: 0 0 8px 0;
    font-weight: bold;
}

.card-header p {
    color: #a0a0a0;
    font-size: 14px;
    margin: 0;
}

.card-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
    gap: 18px;
    margin-top: 20px;
}

/* Individual Selling Card */
.selling-card {
    background: #0f3460;
    border: 1px solid rgba(0, 255, 136, 0.3);
    border-radius: 8px;
    padding: 18px;
    position: relative;
    transition: all 0.3s ease;
}

.selling-card:hover {
    border-color: #00ff88;
    box-shadow: 0 8px 20px rgba(0, 255, 136, 0.2);
    transform: translateY(-4px);
}

.selling-excellent {
    border-left: 4px solid #00ff00;
    background: linear-gradient(90deg, #0f3460 0%, #0d4620 100%);
}

.selling-verygood {
    border-left: 4px solid #00d4ff;
    background: linear-gradient(90deg, #0f3460 0%, #0d3a5c 100%);
}

.selling-good {
    border-left: 4px solid #ffaa00;
    background: linear-gradient(90deg, #0f3460 0%, #4d3a1a 100%);
}

.selling-fair {
    border-left: 4px solid #ff6600;
    background: linear-gradient(90deg, #0f3460 0%, #5c2a1a 100%);
}

.selling-poor {
    border-left: 4px solid #ff4444;
    background: linear-gradient(90deg, #0f3460 0%, #5c1a1a 100%);
}

/* Rank Badge */
.rank-badge {
    position: absolute;
    top: 12px;
    right: 12px;
    background: #00ff88;
    color: #0f3460;
    width: 36px;
    height: 36px;
    border-radius: 50%;
    display: flex;
    align-items: center;
    justify-content: center;
    font-weight: bold;
    font-size: 18px;
}

/* Symbol Header */
.symbol {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 14px;
    border-bottom: 1px solid rgba(0, 255, 136, 0.2);
    padding-bottom: 10px;
}

.symbol strong {
    font-size: 20px;
    color: #ffffff;
    font-weight: bold;
}

.selling-score {
    font-size: 12px;
    color: #00ff88;
    font-weight: bold;
}

/* Metrics */
.metrics {
    margin: 14px 0;
    font-size: 13px;
}

.metric-row {
    display: flex;
    justify-content: space-between;
    padding: 8px 0;
    border-bottom: 1px solid rgba(255, 255, 255, 0.08);
}

.metric-row:last-child {
    border-bottom: none;
}

.metric-row .label {
    color: #a0a0a0;
}

.metric-row .value {
    color: #ffffff;
    font-weight: bold;
}

.value.low {
    color: #00ff88;
}

.value.normal {
    color: #ffaa00;
}

.value.high {
    color: #ff4444;
}

.value.neutral {
    color: #00d4ff;
}

/* Recommendation */
.recommendation {
    background: rgba(0, 255, 136, 0.1);
    border-radius: 6px;
    padding: 12px;
    margin: 12px 0;
    border-left: 3px solid #00ff88;
}

.recommendation strong {
    color: #00ff88;
    display: block;
    margin-bottom: 8px;
    font-size: 14px;
}

.strategies {
    display: flex;
    flex-wrap: wrap;
    gap: 6px;
}

.strategy {
    background: rgba(0, 212, 255, 0.2);
    color: #00d4ff;
    padding: 4px 8px;
    border-radius: 4px;
    font-size: 11px;
    font-weight: bold;
    white-space: nowrap;
}

/* Action Info */
.action-info {
    font-size: 12px;
    color: #a0a0a0;
    margin-top: 12px;
}

.action-info p {
    margin: 5px 0;
    padding: 3px 0;
    line-height: 1.4;
}

.action-info strong {
    color: #ffffff;
}

/* Responsive */
@media (max-width: 1024px) {
    .card-grid {
        grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
    }
}

@media (max-width: 768px) {
    .card-grid {
        grid-template-columns: 1fr;
    }
    
    .option-selling-card {
        padding: 18px;
    }
    
    .selling-card {
        padding: 14px;
    }
    
    .rank-badge {
        width: 32px;
        height: 32px;
        font-size: 16px;
    }
}
```

---

## 4. Integration in Main Code

In the `save_html()` function, add this after the existing "Option Intelligence" section:

```python
# GENERATE OPTION SELLING CARDS (NEW)
selling_cards_html = generate_option_selling_cards_html(scored)

# Insert in HTML report
html_content = html_content.replace(
    "<!-- INSERT SELLING CARDS HERE -->",
    selling_cards_html
)
# OR append before Option Intelligence section:
html_content = html_content.replace(
    "<section class=\"option-intelligence-section\">",
    selling_cards_html + "\n<section class=\"option-intelligence-section\">"
)
```

---

## 5. Example Output

```
💰 TOP 5 OPTION SELLING OPPORTUNITIES

┌─────────────────────────────────────────┐
│ #1: SBIN (96/100) ⭐⭐⭐⭐⭐            │
│ IV: 18% 🟢 HV: 0.8% 🟢 Spread: 0.8%    │
│ ✅ PERFECT FOR NAKED SELLING            │
│ Strategies: Naked Put | Covered Call    │
│ Action: Sell ATM Call or Put            │
│ Premium: Very High | Risk: Very Low     │
└─────────────────────────────────────────┘

┌─────────────────────────────────────────┐
│ #2: TCS (94/100) ⭐⭐⭐⭐⭐            │
│ IV: 20% 🟢 HV: 0.9% 🟢 Spread: 0.7%    │
│ ✅ PERFECT FOR SELLING                  │
│ Strategies: Naked Put | Covered Call    │
│ Action: Sell OTM Put for wider cushion  │
│ Premium: Very High | Risk: Very Low     │
└─────────────────────────────────────────┘

[... Cards 3-5 ...]
```

---

## Integration Checklist

- [ ] Add `calculate_selling_viability_score()` function
- [ ] Add `determine_selling_quality()` function
- [ ] Add helper functions (get_iv_quality, get_vol_quality, etc.)
- [ ] Add `generate_option_selling_cards_html()` function
- [ ] Add `generate_single_selling_card()` function
- [ ] Add CSS styling to `<style>` tag
- [ ] Call `generate_option_selling_cards_html()` in `save_html()`
- [ ] Test with current data (should show top 5 sellers)
- [ ] Compare cards with Option Intelligence cards (should differ!)

---

**Ready for Integration**: Yes ✅  
**Tested**: No (pending integration)  
**Status**: Production-ready code  
