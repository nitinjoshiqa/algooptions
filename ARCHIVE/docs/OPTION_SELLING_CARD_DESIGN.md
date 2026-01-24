# 🎴 Option Selling Card Design

## Card Layout for Option Selling Candidates

### HTML Card Structure

```html
<div class="option-selling-card">
    <div class="card-header">
        <h3>💰 OPTION SELLING OPPORTUNITIES</h3>
        <p>Top 5 stocks suitable for premium selling (short calls/puts)</p>
    </div>
    
    <div class="card-grid">
        <!-- CARD 1 -->
        <div class="selling-card selling-excellent">
            <div class="rank-badge">1</div>
            
            <div class="symbol">
                <strong>SBIN</strong>
                <span class="selling-score">96/100 ⭐⭐⭐⭐⭐</span>
            </div>
            
            <div class="metrics">
                <div class="metric-row">
                    <span class="label">Implied Vol (IV):</span>
                    <span class="value low">18% 🟢 Very Low</span>
                </div>
                <div class="metric-row">
                    <span class="label">Historical Vol:</span>
                    <span class="value low">0.8% 🟢 Ultra-Stable</span>
                </div>
                <div class="metric-row">
                    <span class="label">Bid-Ask Spread:</span>
                    <span class="value low">0.8% 🟢 Excellent</span>
                </div>
                <div class="metric-row">
                    <span class="label">Directional Signal:</span>
                    <span class="value neutral">±0.05 🟡 Neutral</span>
                </div>
            </div>
            
            <div class="recommendation">
                <strong>✅ PERFECT FOR SELLING</strong>
                <div class="strategies">
                    <span class="strategy">📍 Naked Put</span>
                    <span class="strategy">📍 Covered Call</span>
                    <span class="strategy">📍 Put Spread</span>
                </div>
            </div>
            
            <div class="action-info">
                <p><strong>Action:</strong> Sell 1 ATM Call / 1 ATM Put</p>
                <p><strong>Premium Collection:</strong> High (decay working for you)</p>
                <p><strong>Risk:</strong> Very Low (stable stock, tight stops)</p>
            </div>
        </div>
        
        <!-- CARD 2 -->
        <div class="selling-card selling-verygood">
            <div class="rank-badge">2</div>
            
            <div class="symbol">
                <strong>INFY</strong>
                <span class="selling-score">91/100 ⭐⭐⭐⭐</span>
            </div>
            
            <div class="metrics">
                <div class="metric-row">
                    <span class="label">Implied Vol (IV):</span>
                    <span class="value low">22% 🟢 Low</span>
                </div>
                <div class="metric-row">
                    <span class="label">Historical Vol:</span>
                    <span class="value low">1.1% 🟢 Very Stable</span>
                </div>
                <div class="metric-row">
                    <span class="label">Bid-Ask Spread:</span>
                    <span class="value low">1.2% 🟢 Excellent</span>
                </div>
                <div class="metric-row">
                    <span class="label">Directional Signal:</span>
                    <span class="value neutral">±0.12 🟡 Neutral</span>
                </div>
            </div>
            
            <div class="recommendation">
                <strong>✅ HIGHLY SUITABLE</strong>
                <div class="strategies">
                    <span class="strategy">📍 Put Spread</span>
                    <span class="strategy">📍 Call Spread</span>
                    <span class="strategy">📍 Iron Condor</span>
                </div>
            </div>
            
            <div class="action-info">
                <p><strong>Action:</strong> Sell Put Spread (wider margin of safety)</p>
                <p><strong>Premium Collection:</strong> High</p>
                <p><strong>Risk:</strong> Low (defensive spreads)</p>
            </div>
        </div>
        
        <!-- CARD 3 -->
        <div class="selling-card selling-verygood">
            <div class="rank-badge">3</div>
            
            <div class="symbol">
                <strong>TCS</strong>
                <span class="selling-score">94/100 ⭐⭐⭐⭐⭐</span>
            </div>
            
            <div class="metrics">
                <div class="metric-row">
                    <span class="label">Implied Vol (IV):</span>
                    <span class="value low">20% 🟢 Very Low</span>
                </div>
                <div class="metric-row">
                    <span class="label">Historical Vol:</span>
                    <span class="value low">0.9% 🟢 Ultra-Stable</span>
                </div>
                <div class="metric-row">
                    <span class="label">Bid-Ask Spread:</span>
                    <span class="value low">0.7% 🟢 Excellent</span>
                </div>
                <div class="metric-row">
                    <span class="label">Directional Signal:</span>
                    <span class="value neutral">±0.08 🟡 Neutral</span>
                </div>
            </div>
            
            <div class="recommendation">
                <strong>✅ PERFECT FOR SELLING</strong>
                <div class="strategies">
                    <span class="strategy">📍 Naked Put</span>
                    <span class="strategy">📍 Covered Call</span>
                    <span class="strategy">📍 Strangle</span>
                </div>
            </div>
            
            <div class="action-info">
                <p><strong>Action:</strong> Sell OTM Put or Call for wider cushion</p>
                <p><strong>Premium Collection:</strong> Very High (tightest bid-ask)</p>
                <p><strong>Risk:</strong> Very Low (most liquid)</p>
            </div>
        </div>
    </div>
</div>
```

---

## CSS Styling for Cards

```css
/* Option Selling Card Container */
.option-selling-card {
    background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
    border-radius: 12px;
    padding: 20px;
    margin: 20px 0;
    border-left: 5px solid #00d4ff;
}

.card-header {
    text-align: center;
    margin-bottom: 25px;
    border-bottom: 2px solid rgba(0, 212, 255, 0.2);
    padding-bottom: 15px;
}

.card-header h3 {
    color: #00d4ff;
    font-size: 22px;
    margin: 0 0 5px 0;
}

.card-header p {
    color: #a0a0a0;
    font-size: 14px;
    margin: 0;
}

/* Grid of Individual Cards */
.card-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(320px, 1fr));
    gap: 15px;
    margin-top: 15px;
}

/* Individual Selling Card */
.selling-card {
    background: #0f3460;
    border: 1px solid rgba(0, 212, 255, 0.3);
    border-radius: 8px;
    padding: 15px;
    position: relative;
    transition: all 0.3s ease;
}

.selling-card:hover {
    border-color: #00d4ff;
    box-shadow: 0 0 15px rgba(0, 212, 255, 0.2);
    transform: translateY(-2px);
}

/* Rank Badge */
.rank-badge {
    position: absolute;
    top: 10px;
    right: 10px;
    background: #00d4ff;
    color: #0f3460;
    width: 32px;
    height: 32px;
    border-radius: 50%;
    display: flex;
    align-items: center;
    justify-content: center;
    font-weight: bold;
    font-size: 16px;
}

/* Symbol Header */
.symbol {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 12px;
    border-bottom: 1px solid rgba(0, 212, 255, 0.2);
    padding-bottom: 8px;
}

.symbol strong {
    font-size: 18px;
    color: #ffffff;
}

.selling-score {
    font-size: 12px;
    color: #00d4ff;
    font-weight: bold;
}

/* Quality Indicators */
.selling-excellent {
    border-left: 3px solid #00ff00;
    background: linear-gradient(90deg, #0f3460 0%, #1a4d2e 100%);
}

.selling-verygood {
    border-left: 3px solid #00d4ff;
    background: linear-gradient(90deg, #0f3460 0%, #1a3d5c 100%);
}

.selling-good {
    border-left: 3px solid #ffaa00;
    background: linear-gradient(90deg, #0f3460 0%, #3d3a1a 100%);
}

.selling-fair {
    border-left: 3px solid #ff6600;
    background: linear-gradient(90deg, #0f3460 0%, #4d2a1a 100%);
}

/* Metrics */
.metrics {
    margin: 12px 0;
    font-size: 13px;
}

.metric-row {
    display: flex;
    justify-content: space-between;
    padding: 6px 0;
    border-bottom: 1px solid rgba(255, 255, 255, 0.1);
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
    color: #00ff00;
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
    background: rgba(0, 212, 255, 0.1);
    border-radius: 6px;
    padding: 10px;
    margin: 10px 0;
    border-left: 3px solid #00d4ff;
}

.recommendation strong {
    color: #00ff00;
    display: block;
    margin-bottom: 6px;
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
}

/* Action Info */
.action-info {
    font-size: 12px;
    color: #a0a0a0;
    margin-top: 10px;
}

.action-info p {
    margin: 4px 0;
    padding: 3px 0;
}

.action-info strong {
    color: #ffffff;
}

/* Responsive */
@media (max-width: 768px) {
    .card-grid {
        grid-template-columns: 1fr;
    }
    
    .selling-card {
        padding: 12px;
    }
}
```

---

## Card Features

### 1. **Color-Coded Quality**
- 🟢 **Green** (Excellent): Score ≥ 90
- 🔵 **Blue** (Very Good): Score 80-89
- 🟡 **Yellow** (Good): Score 70-79
- 🔴 **Red** (Poor): Score < 70

### 2. **Key Metrics Highlighted**
- **IV Level**: Governs premium collection potential
- **Historical Volatility**: Shows actual price stability
- **Bid-Ask Spread**: Critical for entry/exit timing
- **Directional Signal**: Indicates whether stock wants to move

### 3. **Recommended Strategies**
- **Naked Put/Call**: Only for score > 90 (safest)
- **Put/Call Spread**: For score > 85 (defined risk)
- **Iron Condor**: For score > 75 (wider cushion)
- **Strangle**: For score > 80 (OTM protection)

### 4. **Quick Action Summary**
- What to do (sell put spread, naked call, etc.)
- Expected premium collection (High/Very High)
- Risk level (Low/Very Low)

---

## Integration with HTML Report

The card would appear in the HTML report between the current sections:

```
[Summary Stats]
    ↓
[Option Selling Cards] ← NEW
    ↓
[Option Intelligence Cards] (Current high |score| stocks)
    ↓
[Full Data Table]
```

---

## Benefits of This Card Design

✅ **Quick Scanning** - See top 5 sellers at a glance  
✅ **Color-Coded** - Green = Good, Red = Bad (instant assessment)  
✅ **Metric-Heavy** - IV, Vol, Spread all visible  
✅ **Strategy Guidance** - Tells you which strategy to use  
✅ **Action-Oriented** - Suggests specific trades  
✅ **Mobile-Friendly** - Responsive grid layout  
✅ **Professional** - Dark theme matches current design  

---

## Python Implementation

```python
def generate_option_selling_cards(scored_data):
    """
    Generate HTML cards for top 5 option selling candidates
    """
    # Calculate selling score for each stock
    selling_scores = []
    for row in scored_data:
        score = calculate_option_selling_score(row)
        selling_scores.append({
            **row,
            'selling_score': score
        })
    
    # Sort by selling score, get top 5
    top_sellers = sorted(selling_scores, key=lambda x: x['selling_score'], reverse=True)[:5]
    
    # Generate HTML cards
    html = '<div class="option-selling-card">'
    html += '<div class="card-header">💰 OPTION SELLING OPPORTUNITIES</div>'
    html += '<div class="card-grid">'
    
    for rank, stock in enumerate(top_sellers, 1):
        html += generate_single_selling_card(stock, rank)
    
    html += '</div></div>'
    return html


def generate_single_selling_card(stock, rank):
    """Generate HTML for a single selling card"""
    symbol = stock.get('symbol', 'N/A')
    selling_score = stock.get('selling_score', 0)
    iv = stock.get('option_iv', 0) * 100
    hv = stock.get('volatility_pct', 0)
    spread = stock.get('option_spread_pct', 0)
    abs_score = abs(stock.get('final_score', 0))
    
    # Determine quality class
    if selling_score >= 90:
        quality_class = 'selling-excellent'
        stars = '⭐⭐⭐⭐⭐'
    elif selling_score >= 80:
        quality_class = 'selling-verygood'
        stars = '⭐⭐⭐⭐'
    elif selling_score >= 70:
        quality_class = 'selling-good'
        stars = '⭐⭐⭐'
    else:
        quality_class = 'selling-fair'
        stars = '⭐⭐'
    
    # Determine strategy based on score
    if selling_score >= 90:
        primary_strategy = '📍 Naked Put/Call'
        secondary = '📍 Covered Call'
        tertiary = '📍 Put Spread'
    elif selling_score >= 80:
        primary_strategy = '📍 Put Spread'
        secondary = '📍 Call Spread'
        tertiary = '📍 Iron Condor'
    else:
        primary_strategy = '📍 Conservative Spread'
        secondary = '📍 Put Spread'
        tertiary = '📍 Wide Strikes'
    
    # Determine IV color
    if iv < 20:
        iv_color = 'low'
        iv_label = 'Very Low 🟢'
    elif iv < 30:
        iv_color = 'low'
        iv_label = 'Low 🟢'
    elif iv < 40:
        iv_color = 'normal'
        iv_label = 'Normal 🟡'
    else:
        iv_color = 'high'
        iv_label = 'High 🔴'
    
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
                <span class="value {iv_color}">{iv:.1f}% {iv_label}</span>
            </div>
            <div class="metric-row">
                <span class="label">Historical Vol:</span>
                <span class="value low">{hv:.2f}% 🟢 {'Ultra-Stable' if hv < 1.0 else 'Very Stable' if hv < 1.5 else 'Stable'}</span>
            </div>
            <div class="metric-row">
                <span class="label">Bid-Ask Spread:</span>
                <span class="value low">{spread:.2f}% 🟢 {'Excellent' if spread < 1.0 else 'Very Good' if spread < 2.0 else 'Good'}</span>
            </div>
            <div class="metric-row">
                <span class="label">Directional Signal:</span>
                <span class="value neutral">±{abs_score:.2f} 🟡 {'Very Neutral' if abs_score < 0.10 else 'Neutral' if abs_score < 0.20 else 'Slightly Directional'}</span>
            </div>
        </div>
        <div class="recommendation">
            <strong>✅ {'PERFECT FOR SELLING' if selling_score >= 90 else 'HIGHLY SUITABLE' if selling_score >= 80 else 'GOOD CHOICE'}</strong>
            <div class="strategies">
                <span class="strategy">{primary_strategy}</span>
                <span class="strategy">{secondary}</span>
                <span class="strategy">{tertiary}</span>
            </div>
        </div>
        <div class="action-info">
            <p><strong>Action:</strong> Sell {'Naked' if selling_score >= 90 else 'Spread'} {'Call' if abs_score > 0.05 else 'Put' if abs_score < -0.05 else 'Call or Put'}</p>
            <p><strong>Premium Collection:</strong> {'Very High' if selling_score >= 90 else 'High' if selling_score >= 80 else 'Moderate'} (decay working for you)</p>
            <p><strong>Risk:</strong> {'Very Low' if selling_score >= 90 else 'Low'} (stable, tight stops)</p>
        </div>
    </div>
    '''
    
    return html
```

---

**Updated**: Jan 21, 2026  
**Feature**: Option Selling Card Design  
**Status**: Ready for Implementation  
