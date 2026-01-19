"""Option strategy recommendation engine."""


STRATEGY_TOOLTIPS = {
    'long-call': 'Buy ATM/ITM Call - Bullish directional play. Max loss: premium paid. Best for rising IV.',
    'bull-call': 'Buy lower strike call, sell higher strike call. Limited profit, defined risk. High vol ideal.',
    'lcall-spread': 'Call spread with wide strikes. Best for high volatility + strong bullish bias.',
    'atm-call': 'ATM call only - Balanced delta (0.50-0.65). Good timing play with fair premium.',
    'call-diagonal': 'Long longer-dated call, sell shorter call. Low risk, good for trending markets.',
    'call-calendar': 'Sell near-term call, buy longer-term call. Theta positive, benefits from IV drop.',
    'long-put': 'Buy ATM/ITM Put - Bearish directional play. Max loss: premium paid. Best for falling IV.',
    'bear-put': 'Sell higher strike put, buy lower strike put. Premium collection. High vol favorable.',
    'put-spread': 'Put spread with wide strikes. Best for high volatility + strong bearish bias.',
    'atm-put': 'ATM put only - Balanced delta. Good for downside protection/timing.',
    'put-diagonal': 'Long longer-dated put, sell shorter put. Low risk, good for declining markets.',
    'put-calendar': 'Sell near-term put, buy longer-term put. Theta positive, benefits from IV drop.',
    'iron-condor': 'Sell strangle, buy wider strangle. Range-bound trade. Max profit when stock stays flat.',
    'straddle': 'Buy ATM call + ATM put. Profits from big move. High volatility expected.',
    'strangle': 'Buy OTM call + OTM put. Lower cost than straddle. Requires larger move to profit.',
    'covered-call': 'Own stock, sell call. Generate income. Capped upside. Neutral/slightly bullish.',
    'neutral-strategy': 'Neutral/watching - Unclear direction. Wait for clearer setup.',
    'no-trade': '❌ NO-TRADE - Option liquidity too poor. Wait for better conditions or use equity only.',
}


def suggest_option_strategy(is_bullish, is_bearish, volatility_pct, conf_val, abs_score, option_score=None):
    """
    Suggest option strategy based on bullish/bearish bias, volatility, and confidence.
    
    **Option Geek NO-TRADE Gate:** Blocks all trade suggestions if option liquidity is too poor.
    
    Args:
        is_bullish (bool): Bullish directional bias
        is_bearish (bool): Bearish directional bias
        volatility_pct (float): ATR/price * 100 (percentage volatility)
        conf_val (float): Confidence level 0-100
        abs_score (float): Absolute score magnitude
        option_score (float, optional): Option liquidity score (-1 to +1, from option_scorer)
                                       -1 = expensive/illiquid, +1 = cheap/liquid
        
    Returns:
        tuple: (strategy_name: str, strategy_class_key: str)
        
    Note:
        - option_score < -0.3: NO-TRADE (poor liquidity, high cost)
        - option_score -0.3 to +0.3: CAUTION (marginal liquidity)
        - option_score > +0.3: GO (good liquidity, reasonable cost)
    """
    # ==================== OPTION GEEK NO-TRADE GATE ====================
    # If options are too expensive/illiquid, block ALL trade suggestions
    if option_score is not None and option_score < -0.3:
        return "NO-TRADE", "no-trade"
    # ====================================================================
    
    if volatility_pct is None or volatility_pct == 0:
        volatility_pct = 2.0

    # Volatility classification
    high_vol = volatility_pct > 3.5
    med_vol = 1.5 <= volatility_pct <= 3.5
    low_vol = volatility_pct < 1.5

    # Confidence classification
    high_conf = (conf_val or 0) >= 60
    med_conf = 40 <= (conf_val or 0) < 60
    strong_signal = (abs_score or 0) >= 0.15

    # Bullish strategies
    if is_bullish:
        if high_vol and high_conf and strong_signal:
            return "Long Call Spread", "lcall-spread"
        elif high_vol and med_conf:
            return "Bull Call", "bull-call"
        elif med_vol and high_conf:
            return "ATM Call", "atm-call"
        elif low_vol and high_conf:
            return "Call Diagonal", "call-diagonal"
        elif low_vol and med_conf:
            return "Call Calendar", "call-calendar"
        else:
            return "Long Call", "long-call"
    
    # Bearish strategies
    elif is_bearish:
        if high_vol and high_conf and strong_signal:
            return "Put Spread", "put-spread"
        elif high_vol and med_conf:
            return "Bear Put", "bear-put"
        elif med_vol and high_conf:
            return "ATM Put", "atm-put"
        elif low_vol and high_conf:
            return "Put Diagonal", "put-diagonal"
        elif low_vol and med_conf:
            return "Put Calendar", "put-calendar"
        else:
            return "Long Put", "long-put"
    
    # Neutral/directional unclear
    else:
        if high_vol and high_conf:
            return "Iron Condor", "iron-condor"
        elif high_vol:
            return "Straddle", "straddle"
        elif med_vol and high_conf:
            return "Strangle", "strangle"
        elif low_vol:
            return "Covered Call", "covered-call"
        else:
            return "Neutral", "neutral-strategy"
