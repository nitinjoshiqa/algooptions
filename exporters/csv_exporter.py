"""CSV export functionality for screener results."""

import csv


def save_csv(results, output_path, args, suggest_option_strategy, strategy_tooltips):
    """Save results to CSV with all metrics."""
    with open(output_path, "w", newline='', encoding='utf-8') as csvf:
        writer = csv.writer(csvf)
        writer.writerow([
            "rank", "symbol", "sector", "index", "market_regime", "score",
            "swing_score", "longterm_score",
            "confidence", "context_score", "context_momentum", "robustness_score", "robustness_momentum", "master_score", 
            "price", "pct_below_high", "pct_above_low", "mode", "strategy", "strategy_reason",
            "or_score", "vwap_score", "structure_score", "rsi", "rsi_score", "ema_score",
            "volume_score", "macd_score", "bb_score", "atr",
            "intraday_weight", "swing_weight", "longterm_weight",
            "option_score", "option_iv", "option_spread_pct", "option_type", "option_strike", "option_expiry",
            "option_volume", "option_oi", "option_delta", "option_gamma", "option_theta", "option_vega"
        ])
        
        for i, r in enumerate(results, 1):
            price = r.get('price', 0)
            week52_high = r.get('52w_high', price)
            week52_low = r.get('52w_low', price)
            
            # Calculate % Below High and % Above Low
            pct_below_high = ""
            if week52_high and week52_high > 0:
                pct_below_high = f"{((week52_high - price) / week52_high) * 100:.2f}"
            
            pct_above_low = ""
            if week52_low and week52_low > 0:
                pct_above_low = f"{((price - week52_low) / week52_low) * 100:.2f}"
            
            weights = r.get('weights', {})
            
            sector_val = r.get('sector', 'Unknown')
            # Derive option strategy recommendation for CSV
            score = r.get('final_score')
            conf_val = r.get('confidence') or 0
            atr_val = r.get('atr') or 0
            px = price or 0
            volatility_pct = ((atr_val / px) * 100) if (px > 0 and atr_val > 0) else 2.0
            is_bullish = (score is not None) and (score > 0.05)
            is_bearish = (score is not None) and (score < -0.05)
            abs_score = abs(score) if score is not None else 0
            option_score = r.get('option_score')
            strategy_val, strategy_class = suggest_option_strategy(is_bullish, is_bearish, volatility_pct, conf_val, abs_score, option_score)
            strategy_reason = strategy_tooltips.get(strategy_class, '')
            
            writer.writerow([
                i,
                r['symbol'],
                sector_val,
                r.get('index', ''),
                r.get('market_regime', ''),
                f"{r['final_score']:.4f}" if r.get('final_score') is not None else '',
                f"{r.get('swing_score', 0):.4f}" if r.get('swing_score') is not None else '',
                f"{r.get('longterm_score', 0):.4f}" if r.get('longterm_score') is not None else '',
                f"{r['confidence']:.1f}" if r.get('confidence') is not None else '',
                f"{r.get('context_score', 0):.2f}" if r.get('context_score') is not None else '',
                f"{r.get('context_momentum', 0):+.2f}" if r.get('context_momentum') is not None else '',
                f"{r.get('robustness_score', 0):.0f}" if r.get('robustness_score') is not None else '',
                f"{r.get('robustness_momentum', 0):+.2f}" if r.get('robustness_momentum') is not None else '',
                f"{r.get('master_score', 0):.0f}" if r.get('master_score') is not None else '',
                f"{r['price']:.2f}" if r.get('price') is not None else '',
                pct_below_high,
                pct_above_low,
                r.get('mode', ''),
                strategy_val,
                strategy_reason,
                f"{r['or_score']:.4f}" if r.get('or_score') is not None else '',
                f"{r['vwap_score']:.4f}" if r.get('vwap_score') is not None else '',
                f"{r['structure_score']:.4f}" if r.get('structure_score') is not None else '',
                f"{r['rsi']:.2f}" if r.get('rsi') is not None else '',
                f"{r['rsi_score']:.4f}" if r.get('rsi_score') is not None else '',
                f"{r['ema_score']:.4f}" if r.get('ema_score') is not None else '',
                f"{r['volume_score']:.4f}" if r.get('volume_score') is not None else '',
                f"{r['macd_score']:.4f}" if r.get('macd_score') is not None else '',
                f"{r['bb_score']:.4f}" if r.get('bb_score') is not None else '',
                f"{r['atr']:.2f}" if r.get('atr') is not None else '',
                f"{weights.get('intraday', 0):.2f}" if weights else '',
                f"{weights.get('swing', 0):.2f}" if weights else '',
                f"{weights.get('longterm', 0):.2f}" if weights else '',
                f"{r['option_score']:.4f}" if r.get('option_score') is not None else '',
                f"{r['option_iv']:.4f}" if r.get('option_iv') is not None else '',
                f"{r['option_spread_pct']:.4f}" if r.get('option_spread_pct') is not None else '',
                r.get('option_type', ''),
                f"{r['option_strike']:.2f}" if r.get('option_strike') is not None else '',
                r.get('option_expiry', ''),
                f"{r['option_volume']:.0f}" if r.get('option_volume') is not None else '',
                f"{r['option_oi']:.0f}" if r.get('option_oi') is not None else '',
                f"{r['option_delta']:.4f}" if r.get('option_delta') is not None else '',
                f"{r['option_gamma']:.6f}" if r.get('option_gamma') is not None else '',
                f"{r['option_theta']:.4f}" if r.get('option_theta') is not None else '',
                f"{r['option_vega']:.4f}" if r.get('option_vega') is not None else '',
            ])
    
    print(f"\nSaved results to {output_path}")
