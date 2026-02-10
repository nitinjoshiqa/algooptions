"""
Context Engine - Single Source of Truth for Institutional Context Scoring

Purpose:
    Extract all context score and context momentum calculations into one module.
    All components (scoring engine, HTML generation, CSV export) import and use this.
    
Architecture:
    - compute_context_score(row) → (context_score, context_momentum)
    - Pure function with no side effects
    - Input: dict with VWAP, volume, divergence, regime, risk metrics
    - Output: (score: 0-5, momentum: -1 to +1)
"""

import math


def tanh(x):
    """Hyperbolic tangent function for smooth scoring transitions"""
    return math.tanh(x)


def compute_context_score(row):
    """
    Calculate institutional context score (0–5 scale) and momentum (-1 to +1)
    
    Context represents the market structure quality and institutional participation:
    - 0.0–1.0 : HOSTILE (potential reversal, weak structure)
    - 1.0–2.0 : WEAK (uncertain, low conviction)
    - 2.0–3.0 : NEUTRAL (balanced, no clear bias)
    - 3.0–4.0 : EARLY SUPPORTIVE (building conviction)
    - 4.0–5.0 : STRONG INSTITUTIONAL (high quality entry)
    
    Args:
        row: Dictionary containing:
            - vwap_score: VWAP divergence (-2 to +2)
            - volume_score: Volume trend (-2 to +2)
            - pv_divergence_score: Price/Volume alignment (-1 to +1)
            - pr_divergence_score: Price/RSI alignment (-1 to +1)
            - market_regime: 'trending', 'neutral', 'ranging', 'volatile'
            - risk_level: 'LOW', 'MEDIUM', 'HIGH'
            - pv_confidence: Divergence confidence (0-1)
    
    Returns:
        tuple: (context_score: float 0-5, context_momentum: float -1 to +1)
    """
    
    # Base initialization (neutral)
    score = 2.5
    momentum = 0.0
    
    # Extract inputs with safe defaults
    vwap_score = row.get('vwap_score', 0.0) or 0.0
    volume_score = row.get('volume_score', 0.0) or 0.0
    regime = row.get('market_regime', 'neutral') or 'neutral'
    risk_level = row.get('risk_level', 'LOW') or 'LOW'
    
    pv_div_score = row.get('pv_divergence_score', 0.0) or 0.0
    pr_div_score = row.get('pr_divergence_score', 0.0) or 0.0
    pv_confidence = row.get('pv_confidence', 0.0) or 0.0
    
    # ==================== COMPONENT 1: VWAP PRESSURE ====================
    # Most important early institutional signal
    # Range contribution: approximately ±1.0
    vwap_contrib = 1.0 * tanh(vwap_score * 1.8)
    score += vwap_contrib
    
    # VWAP momentum: derivative of tanh (rate of change)
    vwap_momentum = 1.0 * (1 - tanh(vwap_score * 1.8)**2) * 1.8 * vwap_score
    momentum += 0.6 * vwap_momentum  # Heavily weight VWAP momentum
    
    # ==================== COMPONENT 2: VOLUME PARTICIPATION ====================
    # Accumulation/distribution signal
    # Range contribution: approximately ±0.7
    volume_contrib = 0.7 * tanh(volume_score * 1.5)
    score += volume_contrib
    
    # Volume momentum
    volume_momentum = 0.7 * (1 - tanh(volume_score * 1.5)**2) * 1.5 * volume_score
    momentum += 0.4 * volume_momentum
    
    # ==================== COMPONENT 3: DIVERGENCE DETECTION ====================
    # Climax and reversal warnings (NEW: asymmetric - only negative impact allowed)
    # Price/Volume divergence: climax conditions are BEARISH (lower context)
    if pv_div_score < -0.5:  # Climax: price up but volume failing
        divergence_contrib = -0.6 * pv_confidence
        score += divergence_contrib
        momentum -= 0.3 * pv_confidence
    
    # Price/RSI divergence: bearish divergence = weakness
    if pr_div_score < -0.5:  # Bearish divergence = reversal risk
        score -= 0.3
        momentum -= 0.15
    
    # ==================== COMPONENT 4: MARKET REGIME MODULATION ====================
    regime_str = (regime or 'neutral').lower()
    if 'trending' in regime_str:
        score += 0.4
        momentum += 0.1
    elif 'volatile' in regime_str or 'high' in regime_str:
        score -= 0.6
        momentum -= 0.2
    elif 'ranging' in regime_str:
        score += 0.0  # True neutral
        momentum += 0.0
    
    # ==================== COMPONENT 5: RISK COMPRESSION ====================
    # High risk reduces conviction but preserves bias
    if risk_level == 'HIGH':
        pivot = 2.5
        score = pivot + (score - pivot) * 0.55
        momentum *= 0.7  # Dampen momentum in high risk
    elif risk_level == 'MEDIUM':
        pivot = 2.5
        score = pivot + (score - pivot) * 0.75
        momentum *= 0.85
    
    # ==================== FINALIZATION ====================
    # Clamp to valid ranges
    score = max(0.0, min(5.0, score))
    momentum = max(-1.0, min(1.0, momentum))
    
    return round(score, 2), round(momentum, 2)


def get_context_tier(context_score):
    """
    Map context score (0-5) to tier name
    
    Args:
        context_score: float 0-5
        
    Returns:
        str: Tier name
    """
    if context_score >= 4.0:
        return 'STRONG'
    elif context_score >= 3.0:
        return 'SUPPORTIVE'
    elif context_score >= 2.0:
        return 'NEUTRAL'
    elif context_score >= 1.0:
        return 'WEAK'
    else:
        return 'HOSTILE'


def get_context_color(context_score):
    """
    Get color for HTML rendering based on context score
    
    Args:
        context_score: float 0-5
        
    Returns:
        str: Hex color code
    """
    if context_score >= 4.5:
        return '#00b050'  # Strong green
    elif context_score >= 3.5:
        return '#70ad47'  # Good green
    elif context_score >= 2.5:
        return '#ffb000'  # Neutral yellow
    elif context_score >= 1.5:
        return '#ff9500'  # Weak orange
    else:
        return '#c5504f'  # Hostile red
