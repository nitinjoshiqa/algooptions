"""Main scoring engine - Strategy pattern implementation."""
from indicators import rsi, ema, atr, vwap_proxy, opening_range_from_candles
from indicators.patterns import detect_patterns
from scoring import (rsi_score, ema_score, opening_range_score, vwap_score, 
                     structure_score, volume_score, macd_score, bollinger_bands_score,
                     calculate_sl_target, volume_acceleration_score, vwap_crossover_score,
                     opening_range_breakout_score, fundamentals_score, news_sentiment_score)
from options.option_scorer import OptionScorer
from data_providers import get_spot_price, get_intraday_candles_for, get_fundamentals, get_news_sentiment
from core.market_regime import MarketRegimeDetector
from core.config import MODE_WEIGHTS, OPENING_RANGE_MINUTES, VWAP_LOOKBACK_MIN
from core.relative_strength import calculate_relative_strength
from core.divergence_detection import calculate_price_volume_divergence, calculate_price_rsi_divergence
from core.earnings_tracker import get_earnings_dates, get_earnings_confidence_modifier, get_earnings_summary
# TIER 2: Pattern validation, SL scaling, position sizing
from core.tier2_features import (MarketFilter, ConfidenceSLScaler, PositionSizer, 
                                 PatternValidator, should_trade_symbol, get_sl_and_target,
                                 calculate_position)
# TIER 3: ML weighting, calibration, continuous optimization
from core.tier3_features import (IndicatorValidator, ConfidenceCalibrator, 
                                 MLWeightOptimizer, ContinuousCalibrationEngine,
                                 create_calibration_engine)

_INDEX_SCORE_CACHE = {}


class BearnessScoringEngine:
    """Main scoring engine using Strategy pattern."""
    
    def __init__(self, mode='intraday', use_yf=False, force_yf=False, force_breeze=False, quick_mode=False,
                 intraday_weight=None, swing_weight=None, longterm_weight=None,
                 index_bias=None):
        self.mode = mode
        self.use_yf = use_yf
        self.force_yf = force_yf
        self.force_breeze = force_breeze
        self.quick_mode = quick_mode
        
        if intraday_weight is not None or swing_weight is not None or longterm_weight is not None:
            self.w_intraday = intraday_weight if intraday_weight is not None else 0.5
            self.w_swing = swing_weight if swing_weight is not None else 0.3
            self.w_longterm = longterm_weight if longterm_weight is not None else 0.2
            self.custom_weights = True
        else:
            weights = MODE_WEIGHTS.get(mode, MODE_WEIGHTS['intraday'])
            self.w_intraday = weights['intraday']
            self.w_swing = weights['swing']
            self.w_longterm = weights['longterm']
            self.custom_weights = False
        
        self.index_bias = index_bias
        self.index_bias_source = 'external' if index_bias is not None else 'auto'
        
        self.regime_detector = MarketRegimeDetector()
        self.option_scorer = OptionScorer(use_yf=use_yf)
        
        # TIER 2: Initialize pattern validator and SL scaler
        self.pattern_validator = PatternValidator(min_instances=100, min_win_rate=0.55)
        self.sl_scaler = ConfidenceSLScaler()
        self.position_sizer = PositionSizer()
        self.market_filter = MarketFilter()
        
        # TIER 3: Initialize continuous calibration engine
        self.calibration_engine = create_calibration_engine('tier3_data')
        
        # NEW: Sector volume cache for dynamic liquidity filtering
        self._sector_volume_cache = {}
    
    def compute_score(self, symbol):
        """Compute bearness score for a symbol."""
        if symbol.upper() in ('NIFTY', 'NSEI', '^NSEI'):
            idx_result = self._get_index_score()
            if idx_result and idx_result.get('final_score') is not None:
                return idx_result
            else:
                return self._no_data_result(symbol)
        
        variants = self._get_symbol_variants(symbol)
        
        for sym in variants:
            result = self._try_symbol(sym, symbol)
            if result and result.get('status') == 'OK':
                return result
        
        return self._no_data_result(symbol)
    
    def _get_symbol_variants(self, symbol):
        """Get symbol variants to try.
        
        Note: Don't add .NS suffix here - data providers handle that.
        Adding .NS here causes yFinance to create .NS.NS (double suffix).
        """
        if self.quick_mode:
            return [symbol]  # Only the base symbol, let data providers add .NS
        else:
            return [symbol, symbol.replace('-', ''), symbol.replace('.', '')]
    
    def _try_symbol(self, sym, original_symbol):
        """Try to fetch and score a symbol variant."""
        price = get_spot_price(sym, self.use_yf, self.force_yf, self.force_breeze)
        if price is None:
            return None

        # Fetch fundamentals and news data (cached, so doesn't slow down much)
        fundamentals_data = get_fundamentals(sym, self.use_yf, self.force_yf, self.force_breeze)
        news_data = get_news_sentiment(sym)
        
        # Fetch relative strength data (sector and index comparison)
        rs_data = calculate_relative_strength(sym, use_yf=self.use_yf, force_yf=self.force_yf, force_breeze=self.force_breeze)
        
        # Fetch divergence data (price/volume, price/RSI)
        pv_divergence = calculate_price_volume_divergence(sym, use_yf=self.use_yf, force_yf=self.force_yf, force_breeze=self.force_breeze)

        # PHASE 1: Liquidity & Volatility Filters (single pass)
        filter_result = self._apply_filters(sym, price)
        if filter_result:
            return filter_result

        # PHASE 2: Fetch all timeframe data
        try:
            candles_data = self._fetch_all_timeframes(sym)
        except Exception as e:
            print(f"[WARN] Failed to fetch candles for {sym}: {type(e).__name__}")
            candles_data = {'intraday': [], 'swing': [], 'longterm': []}
        
        if not candles_data['intraday']:
            return self._minimal_score_result(sym, original_symbol, price)

        # PHASE 3: Compute scores (single regime detection, no compound multipliers)
        scores_by_tf = self._compute_timeframe_scores(candles_data, price, sym, fundamentals_data, news_data)
        if 'intraday' not in scores_by_tf:
            return self._minimal_score_result(sym, original_symbol, price)

        # PHASE 4: Option scoring
        option_score = self._get_option_score(scores_by_tf, sym, price)
        
        # PHASE 5: Blend timeframes (single pass, no regime re-detection)
        intraday_data = scores_by_tf['intraday']
        detected_regime = scores_by_tf['intraday'].get('regime', 'unknown')
        atr_val = intraday_data.get('atr', 0)
        price_val = price if price > 0 else 0.01
        atr_pct = (atr_val / price_val) * 100 if price_val > 0 else 0
        
        # Calculate price/RSI divergence (reversal warnings)
        rsi_val = intraday_data.get('rsi', 50.0)
        pr_divergence = calculate_price_rsi_divergence(sym, rsi_val, use_yf=self.use_yf, force_yf=self.force_yf, force_breeze=self.force_breeze)
        
        blended = self._blend_scores(scores_by_tf, self.w_intraday, self.w_swing, self.w_longterm, 
                                     regime=detected_regime, atr_pct=atr_pct)
        # Calculate price changes now that we have candles data
        daily_pct, weekly_pct, week52_high, week52_low = self._calculate_price_changes(candles_data, price)
        
        # PHASE 6: Detect patterns & event risk (once each)
        pattern_name, pattern_conf, pattern_impact, pattern_detail = detect_patterns(
            candles_data.get('intraday', []),
            candles_data.get('swing'),
            candles_data.get('longterm')
        )
        event_risk = self._detect_event_risk(candles_data.get('intraday'))

        # PHASE 7: Apply single final adjustment (pattern + index bias + events)
        # NOTE: final_score is PURE TECHNICAL - NO option data mixed in
        # Option data is used ONLY for strategy selection and filtering, never for scoring
        final_score = self._apply_final_adjustments(
            blended['final'],
            pattern_name, pattern_conf, pattern_impact,
            event_risk,
            original_symbol
        )
        
        # PHASE 8: Recalculate final confidence with alignment and pattern quality
        # Get alignment_count from blended result
        alignment_count = blended.get('alignment_count', 1)
        
        # Calculate signal strength from all indicator scores
        all_scores = [
            intraday_data['or_score'],
            intraday_data['vwap_score'],
            intraday_data['structure_score'],
            intraday_data['rsi_score'],
            intraday_data['ema_score'],
            intraday_data['volume_score'],
            intraday_data['macd_score'],
            intraday_data['bb_score']
        ]
        signal_strength = sum(abs(s) for s in all_scores) / len(all_scores) if all_scores else 0
        
        # Pattern quality for confidence calculation
        pattern_quality = pattern_conf if pattern_name else 0.0
        
        # Recalculate confidence with all parameters
        final_confidence = self._compute_confidence(
            all_scores,
            intraday_data['volume_score'],
            detected_regime,
            intraday_data['rsi'],
            alignment_count=alignment_count,
            signal_strength=signal_strength,
            pattern_quality=pattern_quality
        )
        
        # Apply earnings impact: reduce confidence near earnings (noise filter)
        earnings_data = get_earnings_dates(sym)
        earnings_modifier_data = get_earnings_confidence_modifier(sym, 
            earnings_data.get('days_until_earnings') if earnings_data else None)
        earnings_modifier = earnings_modifier_data.get('modifier', 1.0)
        final_confidence = final_confidence * earnings_modifier  # Apply 0.4-1.0 multiplier
        
        # CONFIDENCE FLOOR TRACKING - Detect and record reason for flooring
        confidence_floor_reason = None
        pre_floor_confidence = final_confidence
        final_confidence = max(20, min(100, final_confidence))  # Keep in 20-100 range
        
        # Determine floor reason if confidence was capped at 20%
        if pre_floor_confidence < 20 and final_confidence == 20:
            # Identify which factor caused the floor
            if all_scores and sum(1 for s in all_scores if abs(s) > 0.5) < 2:
                confidence_floor_reason = "low_signal_strength"
            elif detected_regime and 'volatile' in detected_regime:
                confidence_floor_reason = "regime_volatile"
            elif earnings_modifier < 0.8:
                confidence_floor_reason = "high_event_risk"
            else:
                confidence_floor_reason = "multiple_weak_factors"
        
        # ============================================================================
        # CONTEXT CALCULATION (ENGINE-SIDE) - Institutional context + momentum
        # This feeds into system_state for authoritative execution decisions
        # ============================================================================
        # Compute risk_level locally based on RSI (same logic as HTML generation)
        rsi_val = intraday_data.get('rsi', 50) or 50
        if rsi_val >= 70:
            local_risk_level = 'HIGH'  # Overbought
        elif rsi_val <= 30:
            local_risk_level = 'MEDIUM'  # Oversold
        else:
            local_risk_level = 'LOW'  # Neutral
        
        # Extract context inputs from available data
        vwap_score = intraday_data.get('vwap_score', 0.0) or 0.0
        volume_score = intraday_data.get('volume_score', 0.0) or 0.0
        pv_div_score = pv_divergence.get('divergence_score', 0) if pv_divergence else 0
        pr_div_score = pr_divergence.get('divergence_score', 0) if pr_divergence else 0
        pv_confidence = pv_divergence.get('confidence', 0) if pv_divergence else 0
        
        # Calculate context metrics (simplified version of main script's compute_context_score)
        context_score = self._compute_context_metrics(
            vwap_score=vwap_score,
            volume_score=volume_score,
            regime=detected_regime,
            risk_level=local_risk_level,
            pv_div_score=pv_div_score,
            pr_div_score=pr_div_score,
            pv_confidence=pv_confidence
        )
        context_momentum = self._compute_context_momentum(
            vwap_score=vwap_score,
            volume_score=volume_score,
            regime=detected_regime,
            pv_div_score=pv_div_score,
            pr_div_score=pr_div_score
        )
        
        # ============================================================================
        # SYSTEM STATE CALCULATION (AUTHORITATIVE) - Hard execution blocker
        # ============================================================================
        news_score = (news_data.get('news_sentiment_score', 0) or 0) if news_data else 0
        
        # Compute system state based on engine data
        system_state = self._compute_system_state_authoritative(
            context_score=context_score,
            context_momentum=context_momentum,
            risk_level=local_risk_level,
            news_score=news_score,
            confidence=final_confidence
        )
        
        # HARD-BLOCK execution if system_state is STAND_DOWN
        if system_state == 'STAND_DOWN':
            should_trade = False
            filter_reason = f"STAND_DOWN: {self._get_standdown_reason(context_score, context_momentum, local_risk_level, news_score)}"
        else:
            # PHASE 9: TIER 2 - Market filtering, SL/Target, Position sizing
            should_trade, filter_reason = should_trade_symbol(detected_regime, atr_pct, final_confidence)
        sl_target_info = get_sl_and_target(atr_val, final_confidence, final_score, detected_regime, risk_reward_ratio=1.25)
        position_info = calculate_position(final_confidence, atr_val, detected_regime, capital=100000, risk_per_trade=0.02)
        
        # Pattern quality from validator
        pattern_quality_score = self.pattern_validator.get_pattern_quality(pattern_name) if pattern_name else 0.0
        
        # PHASE 9b: Calculate multi-mode scores (intraday, swing, longterm)
        intraday_score = self._calculate_mode_score(
            scores_by_tf, 0.25, 0.50, 0.25,
            pattern_name, pattern_conf, pattern_impact, event_risk, original_symbol
        )
        swing_score = self._calculate_mode_score(
            scores_by_tf, 0.35, 0.35, 0.30,
            pattern_name, pattern_conf, pattern_impact, event_risk, original_symbol
        )
        longterm_score = self._calculate_mode_score(
            scores_by_tf, 0.15, 0.25, 0.60,
            pattern_name, pattern_conf, pattern_impact, event_risk, original_symbol
        )
        
        # final_score is linked to intraday_score (primary decision maker)
        final_score = intraday_score
        
        # ============================================================================
        # ---- SCORING FREEZE POINT ----
        # After this point, final_score is IMMUTABLE
        # Only confidence, state, and execution filters may be calculated below
        # Do NOT modify final_score after this marker
        # ============================================================================
        
        # PHASE 10: Build result
        w_intra, w_swing, w_long = self.w_intraday, self.w_swing, self.w_longterm
        
        result = {
            "symbol": original_symbol,
            "variant": sym,
            "source": candles_data['source'],
            "market_regime": detected_regime,
            "pattern": pattern_name or "None",
            "pattern_confidence": pattern_conf,
            "pattern_detail": pattern_detail,
            "status": "OK",
            "mode": self.mode,
            "final_score": final_score,
            "intraday_score": intraday_score,
            "swing_score": swing_score,
            "longterm_score": longterm_score,
            "confidence": final_confidence,
            "confidence_floor_reason": confidence_floor_reason,  # Why was conf floored?
            "system_state": system_state,  # AUTHORITATIVE execution state (engine-computed)
            "context_score": context_score,  # Institutional context (0-5)
            "context_momentum": context_momentum,  # Context rate of change (-1 to +1)
            "risk_level": local_risk_level,  # Risk zone (LOW/MEDIUM/HIGH based on RSI)
            "price": price,
            "or_score": intraday_data['or_score'],
            "vwap_score": intraday_data['vwap_score'],
            "structure_score": intraday_data['structure_score'],
            "rsi": intraday_data['rsi'],
            "rsi_score": intraday_data['rsi_score'],
            "ema_score": intraday_data['ema_score'],
            "volume_score": intraday_data['volume_score'],
            "macd_score": intraday_data['macd_score'],
            "bb_score": intraday_data['bb_score'],
            "atr": blended['atr'],
            "daily_atr": candles_data.get('daily_atr', 0),  # Daily ATR for day frame SL/Target
            "opening_range": intraday_data['opening_range'],
            "vwap": intraday_data['vwap'],
            # NEW: Early Signal Detectors
            "volume_acceleration": intraday_data.get('volume_acceleration', 0),
            "vwap_crossover": intraday_data.get('vwap_crossover', 0),
            "opening_range_breakout": intraday_data.get('opening_range_breakout', 0),
            # FUNDAMENTALS & NEWS (for intraday analysis)
            "fundamentals_score": intraday_data.get('fundamentals_score', 0),
            "news_sentiment_score": intraday_data.get('news_sentiment_score', 0),
            "news_headlines": news_data.get('recent_news', []) if news_data else [],
            "news_count": news_data.get('news_count', 0) if news_data else 0,
            # RELATIVE STRENGTH (weighted: 60% sector, 40% index) - informational only
            "rs_weighted": rs_data.get('rs_weighted', 0) if rs_data else 0,
            "sector": rs_data.get('sector', 'Unknown') if rs_data else 'Unknown',
            "peer_data": rs_data.get('peer_data', []) if rs_data else [],
            # EARNINGS IMPACT (confidence modifier + summary)
            "earnings_next_date": earnings_data.get('next_earnings').strftime('%Y-%m-%d') if earnings_data and earnings_data.get('next_earnings') else None,
            "earnings_days_until": earnings_data.get('days_until_earnings') if earnings_data else None,
            "earnings_confidence_modifier": earnings_modifier,
            "earnings_modifier_reason": earnings_modifier_data.get('reason', ''),
            "earnings_position_size_factor": earnings_modifier_data.get('position_size_factor', 1.0),
            # DIVERGENCE DETECTION (climax conditions & reversal warnings)
            "pv_divergence_type": pv_divergence.get('divergence_type') if pv_divergence else None,
            "pv_divergence_score": pv_divergence.get('divergence_score', 0) if pv_divergence else 0,
            "pv_price_trend": pv_divergence.get('price_trend', 0) if pv_divergence else 0,
            "pv_volume_trend": pv_divergence.get('volume_trend', 0) if pv_divergence else 0,
            "pv_confidence": pv_divergence.get('confidence', 0) if pv_divergence else 0,
            "pr_divergence_type": pr_divergence.get('divergence_type') if pr_divergence else None,
            "pr_divergence_score": pr_divergence.get('divergence_score', 0) if pr_divergence else 0,
            "pr_price_momentum": pr_divergence.get('price_momentum', 0) if pr_divergence else 0,
            "pr_rsi_level": pr_divergence.get('rsi_level', 50) if pr_divergence else 50,
            "pr_confidence": pr_divergence.get('confidence', 0) if pr_divergence else 0,
            # TIER 2: Market filtering and position sizing
            "should_trade": should_trade,
            "filter_reason": filter_reason,
            "sl_distance": sl_target_info['sl_distance'],
            "target_distance": sl_target_info['target_distance'],
            "rr_ratio": sl_target_info['rr_ratio'],
            "position_shares": position_info['shares'],
            "position_risk_amount": position_info['risk_amount'],
            "position_confidence_mult": position_info['confidence_mult'],
            "position_regime_mult": position_info['regime_mult'],
            "pattern_quality_validated": pattern_quality_score,
            "atr_pct": atr_pct,
            "option_score": option_score.option_score if option_score else None,
            "option_iv": option_score.option_iv if option_score else None,
            "option_spread_pct": option_score.option_spread_pct if option_score else None,
            "option_type": option_score.option_type if option_score else None,
            "option_strike": option_score.strike if option_score else None,
            "option_expiry": option_score.expiry if option_score else None,
            "option_source": option_score.source if option_score else None,
            "option_volume": option_score.option_volume if option_score else None,
            "option_oi": option_score.option_oi if option_score else None,
            "option_delta": option_score.option_delta if option_score else None,
            "option_gamma": option_score.option_gamma if option_score else None,
            "option_theta": option_score.option_theta if option_score else None,
            "option_vega": option_score.option_vega if option_score else None,
            "weights": {"intraday": w_intra, "swing": w_swing, "longterm": w_long},
            "score_5m": scores_by_tf['intraday']['final_score'],
            "score_15m": scores_by_tf.get('swing', {}).get('final_score', 0),
            "score_1h": scores_by_tf.get('longterm', {}).get('final_score', 0),
            "daily_change_pct": daily_pct,
            "weekly_change_pct": weekly_pct,
            "52w_high": week52_high,
            "52w_low": week52_low,
            # TIER 3: ML weights and calibration
            "ml_weights": self.calibration_engine.get_adaptive_weights(),
            "calibration_status": self.calibration_engine.get_summary(),
            "event_risk": event_risk,
            "candles_data": candles_data
        }
        return result

    def _apply_filters(self, sym, price):
        """
        IMPROVED: Dynamic Liquidity Filter (vs static volume)
        
        Instead of filtering out all stocks < 500K volume:
        - Calculate sector median volume dynamically
        - Filter only if volume < 0.5x sector median
        - Boost confidence if volume > 1.5x sector median
        - Allows mid-cap movers with 3x their volume to trade
        """
        try:
            test_candles, _ = get_intraday_candles_for(sym, '1day', 5, self.use_yf, self.force_yf, self.force_breeze)
            if test_candles:
                volumes = [float(c.get('volume', 0)) for c in test_candles]
                avg_volume = sum(volumes) / len(volumes) if volumes else 0
                avg_value = avg_volume * price if price > 0 else 0
                
                # DYNAMIC THRESHOLD: Use sector median if available
                # For now, use adjusted absolute minimum (less strict than before)
                min_volume = 300000  # Reduced from 500K (allows mid-caps)
                min_value = 500000000  # Reduced from 1B
                
                if avg_volume < min_volume or (avg_value < min_value and avg_value > 0):
                    return {"symbol": sym, "status": "LOW_LIQUIDITY", "price": price, 
                           "final_score": None, "confidence": None}
        except Exception:
            pass

        try:
            swing_candles, _ = get_intraday_candles_for(sym, '1day', 20, self.use_yf, self.force_yf, self.force_breeze)
            if swing_candles and len(swing_candles) >= 14:
                highs = [float(c.get('high', 0)) for c in swing_candles]
                lows = [float(c.get('low', 0)) for c in swing_candles]
                closes = [float(c.get('close', 0)) for c in swing_candles]
                
                tr_values = []
                for i in range(1, len(highs)):
                    tr = max(highs[i] - lows[i], abs(highs[i] - closes[i-1]), abs(lows[i] - closes[i-1]))
                    tr_values.append(tr)
                
                if tr_values:
                    atr_val = sum(tr_values[-14:]) / 14
                    volatility_pct = (atr_val / price) * 100 if price > 0 else 0
                    
                    # Filter only for extremely high volatility (> 8%)
                    # Don't filter on low volatility since BANKNIFTY and dividend stocks have lower volatility
                    if volatility_pct > 8.0:
                        return {"symbol": sym, "status": "VOLATILITY_FILTER", "price": price,
                               "final_score": None, "confidence": None}
        except Exception:
            pass

        return None



    def _get_option_score(self, scores_by_tf, sym, price):
        """Get option score with synthetic fallback."""
        try:
            atr = scores_by_tf['intraday'].get('atr', 1.0) if scores_by_tf.get('intraday') else 1.0
            rsi = scores_by_tf['intraday'].get('rsi', 50.0) if scores_by_tf.get('intraday') else 50.0
            option_score = self.option_scorer.score_atm_option(sym, price, atr, rsi)
        except Exception:
            option_score = None
        
        if option_score is None:
            from dataclasses import dataclass
            @dataclass
            class StubOptionScore:
                option_score: float = 0.0
                option_iv: float = 0.20
                option_spread_pct: float = 0.02
                option_type: str = "ATM"
                strike: float = price
                expiry: str = "N/A"
                source: str = "stub"
                option_volume: float = 0
                option_oi: float = 0
                option_delta: float = 0.5
                option_gamma: float = 0.05
                option_theta: float = -0.01
                option_vega: float = 0.20
            option_score = StubOptionScore()
        
        return option_score

    def _apply_final_adjustments(self, base_score, pattern_name, pattern_conf, pattern_impact,
                                  event_risk, original_symbol):
        """Apply pattern, index bias, and event risk adjustments (SINGLE PASS)."""
        final_score = base_score
        
        # Pattern adjustment only (no compound chains)
        if pattern_name:
            confidence_multiplier = 0.5 + (pattern_conf - 0.5) * 1.0
            final_score += pattern_impact * 0.6 * confidence_multiplier
        
        # Index bias adjustment only (simple directional boost/penalty)
        ib = self._get_index_bias(original_symbol)
        if ib is not None and abs(ib) > 0.05:
            if (ib < 0 and final_score < 0) or (ib > 0 and final_score > 0):
                final_score *= 1.05  # Aligned with market: +5%
            elif (ib < 0 and final_score > 0) or (ib > 0 and final_score < 0):
                final_score *= 0.95  # Against market: -5%
        
        # Event risk penalty (simple, no cascading effects)
        if event_risk and event_risk.get('flag'):
            final_score *= 0.9
        
        # IMPROVED: Allow wider range for better discrimination (-2.0 to +2.0)
        return max(-2.0, min(2.0, final_score))

    def _get_index_bias(self, original_symbol):
        """Get index bias once, cache globally."""
        if original_symbol.upper() in ('NIFTY', 'NSEI'):
            return None
        
        if self.index_bias is not None:
            return self.index_bias
        
        global _INDEX_SCORE_CACHE
        if 'nsei' not in _INDEX_SCORE_CACHE:
            try:
                idx = self._get_index_score()
                if idx and idx.get('final_score') is not None:
                    _INDEX_SCORE_CACHE['nsei'] = float(idx['final_score'])
                else:
                    _INDEX_SCORE_CACHE['nsei'] = 0.0
            except Exception:
                _INDEX_SCORE_CACHE['nsei'] = 0.0
        
        return _INDEX_SCORE_CACHE.get('nsei', 0.0)
    
    def _get_index_score(self):
        """Get NIFTY/NSEI index score with minimal data requirements."""
        try:
            for sym_variant in ['^NSEI', 'NIFTYBEES.NS']:
                try:
                    price = get_spot_price(sym_variant, use_yf=True, force_yf=True, force_breeze=False)
                    if price is None:
                        continue
                    
                    try:
                        candles, src = get_intraday_candles_for(sym_variant, '1day', 20, use_yf=True, force_yf=True, force_breeze=False)
                        if candles and len(candles) >= 3:
                            closes = [float(c.get('close', 0)) for c in candles[-10:]]
                            avg_price = sum(closes) / len(closes)
                            trend_score = (price - avg_price) / avg_price if avg_price > 0 else 0.0
                            trend_score = max(-1.0, min(1.0, trend_score))
                        else:
                            trend_score = 0.0
                    except Exception:
                        trend_score = 0.0
                    
                    return {
                        "symbol": "NIFTY",
                        "final_score": trend_score,
                        "price": price,
                        "source": src or "yfinance",
                        "status": "INDEX"
                    }
                except Exception:
                    continue
            
            return {"final_score": 0.0, "status": "INDEX_NEUTRAL"}
        except Exception:
            return {"final_score": 0.0, "status": "INDEX_ERROR"}
    
    def _minimal_score_result(self, sym, original_symbol, price):
        """Return minimal result when candle data unavailable."""
        result = {
            "symbol": original_symbol,
            "variant": sym,
            "source": "fallback",
            "market_regime": "unknown",
            "pattern": "None",
            "pattern_confidence": 0.0,
            "pattern_detail": "No candle data",
            "status": "MINIMAL",
            "mode": self.mode,
            "final_score": 0.0,
            "confidence": 20.0,
            "price": price,
            "or_score": 0.0,
            "vwap_score": 0.0,
            "structure_score": 0.0,
            "rsi": 50.0,
            "rsi_score": 0.0,
            "ema_score": 0.0,
            "volume_score": 0.0,
            "macd_score": 0.0,
            "bb_score": 0.0,
            "atr": 1.0,
            "opening_range": 0.0,
            "vwap": price,
            "option_score": 0.0,
            "option_iv": 0.20,
            "option_spread_pct": 0.02,
            "option_type": "ATM",
            "option_strike": price,
            "option_expiry": "N/A",
            "option_source": "default",
            "option_volume": 0,
            "option_oi": 0,
            "option_delta": 0.5,
            "option_gamma": 0.05,
            "option_theta": -0.01,
            "option_vega": 0.20,
            "weights": {"intraday": self.w_intraday, "swing": self.w_swing, "longterm": self.w_longterm},
            "score_5m": 0.0,
            "score_15m": 0.0,
            "score_1h": 0.0,
            "daily_change_pct": 0.0,
            "weekly_change_pct": 0.0,
            "52w_high": price,
            "52w_low": price,
            "event_risk": {"flag": False, "gap_pct": 0.0, "reason": "no_data"},
            "candles_data": {'intraday': [], 'swing': [], 'longterm': [], 'source': 'fallback'}
        }
        return result
    
    def _fetch_all_timeframes(self, symbol):
        """Fetch candles for all required timeframes."""
        result = {'intraday': None, 'swing': None, 'longterm': None, 'source': [], 'daily_atr': None}
        
        if self.w_intraday > 0:
            bars = 40 if self.quick_mode else 78
            candles, src = get_intraday_candles_for(symbol, '5minute', bars, self.use_yf, self.force_yf, self.force_breeze)
            if candles:
                result['intraday'] = candles
                result['source'].append(src or 'breeze')
        
        if self.w_swing > 0:
            bars = 15 if self.quick_mode else 26
            candles, src = get_intraday_candles_for(symbol, '15minute', bars, self.use_yf, self.force_yf, self.force_breeze)
            if candles:
                result['swing'] = candles
                if src and src not in result['source']:
                    result['source'].append(src)
        
        if self.w_longterm > 0:
            bars = 10 if self.quick_mode else 20
            candles, src = get_intraday_candles_for(symbol, '1day', bars, self.use_yf, self.force_yf, self.force_breeze)
            if candles:
                result['longterm'] = candles
                if src and src not in result['source']:
                    result['source'].append(src)
                
                # OPTIMIZATION: Use longterm daily candles to calculate daily ATR
                # No need for separate fetch - reuse existing daily data
                if len(candles) >= 14:
                    from indicators import atr
                    result['daily_atr'] = atr(candles, period=14)
        
        result['source'] = ', '.join(result['source']) if result['source'] else 'breeze'
        return result
    
    def _compute_timeframe_scores(self, candles_data, price, symbol, fundamentals_data=None, news_data=None):
        """Compute scores for all available timeframes (SINGLE REGIME DETECTION)."""
        scores = {}
        
        for tf_name, candles in [('intraday', candles_data['intraday']),
                                  ('swing', candles_data['swing']),
                                  ('longterm', candles_data['longterm'])]:
            if candles and len(candles) >= 3:
                if tf_name == 'intraday' and len(candles) > 20:
                    try:
                        trimmed = candles[6:-6]
                        candles = trimmed if len(trimmed) >= 3 else candles
                    except Exception:
                        pass
                scores[tf_name] = self._compute_single_timeframe(candles, price, symbol, fundamentals_data, news_data, tf_name == 'intraday')
        
        return scores
    
    def _compute_single_timeframe(self, candles, price, symbol, fundamentals_data=None, news_data=None, is_intraday=False):
        """Compute score for a single timeframe with regime-adaptive weighting."""
        # Get all indicator values (normalize only once at the end)
        or_bars = max(1, OPENING_RANGE_MINUTES // 5)
        or_high, or_low = opening_range_from_candles(candles, or_bars)
        lookback_bars = max(1, VWAP_LOOKBACK_MIN // 5)
        vwap = vwap_proxy(candles, lookback_bars)
        
        or_s = opening_range_score(price, or_high, or_low)
        vwap_s = vwap_score(price, vwap)
        struct_s = structure_score(candles)
        rsi_val = rsi(candles, period=14)
        # Get previous RSI for direction-based scoring
        rsi_prev = rsi(candles[:-1], period=14) if len(candles) > 15 else None
        rsi_s = rsi_score(rsi_val, rsi_prev)
        ema_s = ema_score(candles)
        vol_s = volume_score(candles, periods=20)
        macd_s = macd_score(candles)
        bb_s = bollinger_bands_score(candles, period=20)
        atr_val = atr(candles, period=14)
        
        # NEW: Early Signal Detectors (Volume Acceleration, VWAP Crossover, OR Breakout)
        vol_accel_s = volume_acceleration_score(candles, lookback=20)
        vwap_cross_s = vwap_crossover_score(candles, price)
        or_breakout_s = opening_range_breakout_score(candles, price)
        
        # ========================================================================
        # IMPROVEMENT 3: ELIMINATE DOUBLE-COUNTING
        # ========================================================================
        # Instead of using RSI + MACD + EMA + Bollinger (all measure momentum),
        # use ONE signal per category:
        # - TREND: EMA only (clean trend following)
        # - MOMENTUM/EXTREMES: RSI only (but ONLY if extreme >30/<70)
        # - REVERSALS: Bollinger Bands only (price at extremes)
        # - VOLUME: Keep as-is
        # - EARLY SIGNALS: New detectors (volume accel, VWAP cross, OR breakout)
        
        # Gate: Use RSI signal only if in extreme zone (outside 40-60)
        # Handle None case
        if rsi_val is None:
            rsi_s_gated = 0
        else:
            rsi_s_gated = rsi_s if (rsi_val < 40 or rsi_val > 60) else 0
        
        # MACD & Structure are redundant with EMA trend - reduce their weight significantly
        macd_s_reduced = macd_s * 0.3  # Was 1.2 weight, now minimal
        struct_s_reduced = struct_s * 0.2  # Was also trend-based, minimal
        
        # Bollinger Bands captures reversals; don't double-count with RSI extremes
        bb_s_reduced = bb_s if rsi_s_gated == 0 else bb_s * 0.5  # Use BB if RSI not extreme
        
        # NORMALIZE ONCE: All scores to [-1, +1]
        def normalize_score(score):
            return max(-1.0, min(1.0, score))
        
        or_s_norm = normalize_score(or_s)
        vwap_s_norm = normalize_score(vwap_s)
        struct_s_norm = normalize_score(struct_s_reduced)  # Reduced
        rsi_s_norm = normalize_score(rsi_s_gated)  # Gated to extremes only
        ema_s_norm = normalize_score(ema_s)  # Primary trend indicator
        vol_s_norm = normalize_score(vol_s)  # Keep full weight
        macd_s_norm = normalize_score(macd_s_reduced)  # Reduced to avoid redundancy
        bb_s_norm = normalize_score(bb_s_reduced)  # Reduced when RSI is extreme
        vol_accel_norm = normalize_score(vol_accel_s)
        vwap_cross_norm = normalize_score(vwap_cross_s)
        or_breakout_norm = normalize_score(or_breakout_s)
        
        # NEWS SENTIMENT: Only for intraday timeframe (fundamentals too slow-moving for intraday)
        fundamentals_norm = 0
        news_norm = 0
        if is_intraday:
            # Skip fundamentals for intraday - they change too slowly
            # fundamentals_norm = normalize_score(fundamentals_score(fundamentals_data))
            news_norm = normalize_score(news_sentiment_score(news_data))
        else:
            # For swing/longterm timeframes, include fundamentals but keep separate from technical score
            fundamentals_norm = normalize_score(fundamentals_score(fundamentals_data))
        
        # DETECT REGIME ONCE (at the start, not scattered throughout)
        regime = self._detect_regime(candles)
        weights = self._get_weights_for_regime(regime)
        
        # Apply weights - reduced redundancy (TECHNICAL ONLY - fundamentals separate)
        weighted_scores = [
            or_s_norm * weights['or'],
            vwap_s_norm * weights['vwap'],
            struct_s_norm * weights['struct'],
            rsi_s_norm * weights['rsi'],  # Only if extreme, gated
            ema_s_norm * weights['ema'],  # Primary trend
            vol_s_norm * weights['vol'],  # Full weight
            macd_s_norm * weights['macd'],  # Reduced (redundant with EMA)
            bb_s_norm * weights['bb'],  # Conditional on RSI
            vol_accel_norm * 0.15,  # Volume acceleration: 15% weight (early signal)
            vwap_cross_norm * 0.10,  # VWAP crossover: 10% weight (confirmation)
            or_breakout_norm * 0.08   # Opening range breakout: 8% weight (intraday)
        ]
        total_weight = sum(weights.values()) + 0.15 + 0.10 + 0.08
        final = sum(weighted_scores) / total_weight if total_weight > 0 else 0
        
        # IMPROVED: Amplify strong consensus signals and expand range
        # Calculate consensus strength (how many indicators agree)
        consensus_count = sum(1 for s in [or_s_norm, vwap_s_norm, ema_s_norm, vol_s_norm] 
                             if (s > 0.15 or s < -0.15))  # Count strong signals
        
        # Apply amplification based on consensus
        if consensus_count >= 3:
            # Strong multi-indicator consensus: amplify by 1.4x
            amplification = 1.4 if abs(final) > 0.1 else 1.0
        elif consensus_count == 2:
            # Moderate consensus: amplify by 1.2x
            amplification = 1.2 if abs(final) > 0.1 else 1.0
        else:
            # Weak signal: normal (1.0x)
            amplification = 1.0
        
        final = final * amplification
        
        # Non-linear scaling to expand range while preserving direction
        # Use sign-preserving cubic scaling for stronger differentiation
        if final > 0:
            final = final ** 0.85  # Bullish amplification
        elif final < 0:
            final = -((-final) ** 0.85)  # Bearish amplification
        
        # Use regime variable (already detected)
        # Calculate signal strength as the average magnitude of all indicators
        all_scores = [or_s_norm, vwap_s_norm, struct_s_norm, rsi_s_norm, ema_s_norm, vol_s_norm, 
                     macd_s_norm, bb_s_norm, vol_accel_norm, vwap_cross_norm, or_breakout_norm]
        signal_strength = sum(abs(s) for s in all_scores) / len(all_scores) if all_scores else 0
        
        # No pattern quality at single timeframe level - will be added in blend
        confidence = self._compute_confidence(
            all_scores,
            vol_s_norm,
            regime,
            rsi_val,
            alignment_count=1,  # Single timeframe, no alignment yet
            signal_strength=signal_strength,
            pattern_quality=0.0  # Pattern detection happens at blend level
        )
        
        return {
            "final_score": final,
            "confidence": confidence,
            "regime": regime,  # Pass it forward
            "or_score": or_s,
            "vwap_score": vwap_s,
            "structure_score": struct_s,
            "rsi": rsi_val,
            "rsi_score": rsi_s,
            "ema_score": ema_s,
            "volume_score": vol_s,
            "macd_score": macd_s,
            "bb_score": bb_s,
            "atr": atr_val,
            "opening_range": (or_low, or_high),
            "vwap": vwap,
            # NEW: Early signal detectors
            "volume_acceleration": vol_accel_s,
            "vwap_crossover": vwap_cross_s,
            "opening_range_breakout": or_breakout_s,
            # FUNDAMENTALS & NEWS
            "fundamentals_score": fundamentals_norm,
            "news_sentiment_score": news_norm if is_intraday else 0
        }

    def _get_adaptive_weights(self, regime, atr_pct, signal_strength):
        """
        Calculate adaptive timeframe weights based on market conditions.
        
        Args:
            regime: 'trending', 'ranging', 'choppy', 'volatile'
            atr_pct: Current ATR as % of price
            signal_strength: Magnitude of strongest signal
        
        Returns:
            Dict with 'intraday', 'swing', 'longterm' weights
        """
        import numpy as np
        
        # Base weights by regime
        if regime == 'trending':
            if atr_pct < 4:  # Smooth trend
                # Trust intraday trend-following heavily
                weights = {'intraday': 0.60, 'swing': 0.30, 'longterm': 0.10}
            else:  # Volatile trend
                # Reduce intraday whipsaw risk
                weights = {'intraday': 0.40, 'swing': 0.45, 'longterm': 0.15}
        
        elif regime == 'ranging':
            # Reduce intraday noise, use swing/daily
            weights = {'intraday': 0.20, 'swing': 0.45, 'longterm': 0.35}
        
        elif regime == 'choppy':
            # Avoid intraday, rely on daily structure
            weights = {'intraday': 0.10, 'swing': 0.40, 'longterm': 0.50}
        
        elif regime == 'volatile':
            # Balanced approach, reduce reliance on any single TF
            weights = {'intraday': 0.30, 'swing': 0.35, 'longterm': 0.35}
        
        else:  # Default (shouldn't reach here)
            weights = {'intraday': 0.50, 'swing': 0.30, 'longterm': 0.20}
        
        # Adjust weights by signal strength
        # Strong signals (|score| > 0.4) get MORE weight
        # Weak signals (|score| < 0.1) get LESS weight
        if abs(signal_strength) > 0.40:
            # Boost stronger timeframe weights proportionally
            max_key = max(weights.keys(), key=lambda k: weights[k])
            weights[max_key] *= 1.15
            # Normalize
            total = sum(weights.values())
            weights = {k: v / total for k, v in weights.items()}
        
        elif abs(signal_strength) < 0.10:
            # Reduce weight to weak signals (give to strongest)
            min_key = min(weights.keys(), key=lambda k: weights[k])
            weights[min_key] *= 0.85
            # Normalize
            total = sum(weights.values())
            weights = {k: v / total for k, v in weights.items()}
        
        return weights

    def _detect_regime(self, candles):
        """Single source of truth for regime detection."""
        recent_candles = candles[-10:] if len(candles) >= 10 else candles
        highs = [float(c.get('high', 0)) for c in recent_candles]
        lows = [float(c.get('low', 0)) for c in recent_candles]
        closes = [float(c.get('close', 0)) for c in recent_candles]
        
        if not (highs and lows and closes):
            return 'unknown'
        
        atr_recent = sum(h - l for h, l in zip(highs, lows)) / len(highs)
        avg_close = sum(closes) / len(closes)
        volatility_pct = (atr_recent / avg_close) * 100 if avg_close > 0 else 0
        
        ema_vals = [float(c.get('ema', close)) for c, close in zip(recent_candles, closes)]
        trend_up = closes[-1] > (sum(ema_vals) / len(ema_vals))
        
        if volatility_pct > 4.0:
            return 'volatile'
        elif trend_up:
            return 'trending'
        else:
            return 'ranging'
    
    def _get_weights_for_regime(self, regime):
        """
        Get indicator weights based on regime - BALANCED for neutral-leaning.
        
        Goal: Reduce bias, allow both bullish and bearish signals
        - Equal weight to trend indicators (EMA) and momentum (RSI)
        - Volume validates but doesn't dominate (soft fuzzy scoring)
        - No single indicator > 1.3x weight
        """
        or_weight = 0.0 if self.mode in ('swing', 'longterm') else 1.0
        
        if regime == 'volatile':
            # Volatile: structure, RSI, volume all matter equally
            return {'or': or_weight * 0.6, 'vwap': 0.8, 'struct': 0.95, 'rsi': 0.9,
                   'ema': 0.9, 'vol': 0.8, 'macd': 0.7, 'bb': 1.0}
        elif regime == 'trending':
            # Trending: EMA leads; RSI confirms trend direction
            return {'or': or_weight * 1.0, 'vwap': 0.85, 'struct': 1.1, 'rsi': 1.0,
                   'ema': 1.3, 'vol': 0.8, 'macd': 1.0, 'bb': 0.7}
        else:  # ranging
            # Ranging: mean reversion; RSI and Bollinger lead  
            return {'or': or_weight * 0.8, 'vwap': 1.2, 'struct': 0.8, 'rsi': 1.1,
                   'ema': 0.85, 'vol': 0.8, 'macd': 0.9, 'bb': 1.2}

    def _compute_confidence(self, all_scores, vol_score, regime, rsi_val,
                            alignment_count=1, signal_strength=0.0, pattern_quality=0.0):
        """
        CALIBRATED 3-PILLAR CONFIDENCE FORMULA (v3) - STRICT MODE
        
        More selective confidence that reflects actual signal quality:
        
        1. SIGNAL AGREEMENT (50 points max) - Strong indicator alignment?
           - Require >0.5 threshold for "strong" signals (was >0.3)
           - Penalize conflicting signals heavily
        
        2. MOMENTUM CONFIRMATION (30 points max) - Real momentum?
           - Require avg momentum > 0.65 for full credit (was 0.70)
           - Penalize weak momentum signals
        
        3. VOLUME VALIDATION (20 points max) - Does volume confirm?
           - Stricter penalties for volume divergence
           - Bonus only for strong volume support
        
        Returns: 20-100 confidence score (lower baseline, harder to earn points)
        """
        confidence = 25  # REDUCED from 40: must earn confidence, not assume it
        
        # ============================================================================
        # PILLAR 1: SIGNAL AGREEMENT (50 points max) - STRICTER
        # ============================================================================
        # Count STRONG signals (>0.5 abuse value) - was 0.3, now 0.5 (stricter)
        strong_signals = [s for s in all_scores if abs(s) > 0.50]
        weak_signals = [s for s in all_scores if 0.25 < abs(s) <= 0.50]
        conflicting_signals = []
        
        # Check for conflicting signals (opposite direction of majority)
        if len(all_scores) >= 3:
            positive = sum(1 for s in all_scores if s > 0.1)
            negative = sum(1 for s in all_scores if s < -0.1)
            if positive > 0 and negative > 0 and abs(positive - negative) >= 3:
                conflicting_signals = [s for s in weak_signals if (sum(1 for x in all_scores if x > 0) > sum(1 for x in all_scores if x < 0)) != (s > 0)]
        
        # Score strong signals (stricter thresholds)
        if len(strong_signals) >= 5:
            confidence += 50  # Excellent: 5+ strong indicators aligned
        elif len(strong_signals) == 4:
            confidence += 38  # Very strong: 4 strong indicators
        elif len(strong_signals) == 3:
            confidence += 25  # Good: 3 strong indicators
        elif len(strong_signals) == 2:
            confidence += 12  # Moderate: 2 strong indicators
        elif len(strong_signals) == 1:
            confidence += 5   # Weak: only 1 strong indicator
        # else: 0 (no strong signals at all)
        
        # PENALTY: Conflicting signals reduce confidence heavily
        if len(conflicting_signals) >= 2:
            confidence -= 20  # Major conflict: multiple opposing signals
        elif len(conflicting_signals) == 1:
            confidence -= 10  # Minor conflict: one opposing signal
        
        # BONUS: 100% alignment among strong signals (all point same direction)
        if len(strong_signals) >= 3:
            directions = [1 if s > 0.5 else -1 for s in strong_signals]
            if len(set(directions)) == 1:  # All same direction
                confidence += 8  # Clean consensus bonus (reduced from 10)
        
        # WEAK SIGNALS CONTRIBUTION (moderate boost if some weak alignment)
        if len(weak_signals) >= 3 and len(strong_signals) == 0:
            confidence += 8  # Some alignment even without strong signals
        
        # ============================================================================
        # PILLAR 2: MOMENTUM CONFIRMATION (30 points max) - STRICTER
        # ============================================================================
        # Extract momentum indicators: RSI, MACD, EMA (capture direction + conviction)
        try:
            ema_score = next((s for i, s in enumerate(all_scores) if i == 4), 0)  # EMA usually at index 4
            macd_score = next((s for i, s in enumerate(all_scores) if i == 6), 0)  # MACD usually at index 6
        except:
            ema_score = 0
            macd_score = 0
        
        # Average momentum across RSI-derived signal + EMA + MACD
        rsi_normalized = max(-1.0, min(1.0, (rsi_val - 50.0) / 30.0)) if rsi_val else 0
        momentum_signals = [rsi_normalized, ema_score, macd_score]
        avg_momentum = sum(abs(m) for m in momentum_signals) / len(momentum_signals) if momentum_signals else 0
        
        # STRICTER thresholds - require higher momentum for credit
        if avg_momentum > 0.75:
            confidence += 30  # Excellent momentum
        elif avg_momentum > 0.60:
            confidence += 20  # Strong momentum (raised from 0.50 threshold)
        elif avg_momentum > 0.40:
            confidence += 10  # Moderate momentum
        elif avg_momentum > 0.20:
            confidence += 4   # Weak momentum (reduced credit)
        else:
            confidence -= 5   # Penalize zero/negative momentum (NEW)
        
        # ============================================================================
        # PILLAR 3: VOLUME VALIDATION (20 points max) - STRICTER
        # ============================================================================
        # Does volume align with price direction?
        if vol_score > 0.60:
            confidence += 20  # Excellent supporting volume
        elif vol_score > 0.30:
            confidence += 12  # Good supporting volume (raised threshold from 0.20)
        elif vol_score > 0.05:
            confidence += 5   # Mild supporting volume
        elif vol_score < -0.50:
            confidence -= 20  # STRONG conflicting volume (penalty increased from -15)
        elif vol_score < -0.25:
            confidence -= 12  # MODERATE conflicting volume (penalty increased from -8)
        else:
            confidence -= 3   # Slight penalty for neutral/mixed volume (NEW)
        
        # ============================================================================
        # REGIME CONTEXT (stricter modulation)
        # ============================================================================
        if regime == 'trending':
            confidence = min(100, confidence + 8)  # Boost in trending (increased from +5)
        elif regime == 'choppy':
            confidence = max(20, confidence - 30)  # HARDER cap in choppy (increased from -20)
        elif regime == 'volatile':
            confidence = max(25, confidence - 25)  # HARDER penalty for volatile (increased from -15)
        elif regime == 'sideways':
            confidence = max(20, confidence - 25)  # Penalize sideways markets
        
        # ============================================================================
        # MULTI-TIMEFRAME ALIGNMENT BONUS (stricter)
        # ============================================================================
        if alignment_count >= 3:
            confidence += 15  # 3+ timeframes aligned (strong bonus)
        elif alignment_count == 2:
            confidence += 8   # 2 timeframes aligned (reduced from flat 10)
        # else: 0 (single timeframe = no bonus)
        
        # ============================================================================
        # FINAL CLAMP & RETURN
        # ============================================================================
        # Range: 20-100 (much harder to achieve high confidence)
        confidence = min(100, max(20, confidence))
        
        return confidence
    

    
    def _detect_event_risk(self, intraday_candles):
        """Detect overnight gaps as proxy for earnings/news event risk."""
        try:
            if not intraday_candles or len(intraday_candles) < 2:
                return {"flag": False, "gap_pct": 0.0, "reason": "insufficient"}

            def _get_date(c):
                return c.get('date') or c.get('timestamp', '')[:10]

            by_date = {}
            for c in intraday_candles:
                d = _get_date(c)
                by_date.setdefault(d, []).append(c)
            
            dates = sorted([d for d in by_date.keys() if d])
            if len(dates) < 2:
                return {"flag": False, "gap_pct": 0.0, "reason": "oneday"}
            
            last_day, prev_day = dates[-1], dates[-2]
            today_first = by_date[last_day][0]
            prev_last = by_date[prev_day][-1]

            prev_close = float(prev_last.get('close', 0))
            today_open = float(today_first.get('open', 0))
            if prev_close <= 0 or today_open <= 0:
                return {"flag": False, "gap_pct": 0.0, "reason": "nodata"}

            gap_pct = (today_open - prev_close) / prev_close * 100.0
            if abs(gap_pct) >= 3.0:
                return {"flag": True, "gap_pct": gap_pct, "reason": "gap>=3%"}
            return {"flag": False, "gap_pct": gap_pct, "reason": "normal"}
        except Exception:
            return {"flag": False, "gap_pct": 0.0, "reason": "error"}
    
    def _calculate_price_changes(self, candles_data, current_price):
        """Calculate daily, weekly, and 52-week price changes."""
        daily_pct = 0
        weekly_pct = 0
        week52_high = current_price
        week52_low = current_price
        
        if candles_data['intraday'] and len(candles_data['intraday']) > 0:
            first_close = candles_data['intraday'][0].get('close', current_price)
            daily_pct = ((current_price - first_close) / first_close) * 100 if first_close > 0 else 0
        
        if candles_data['longterm'] and len(candles_data['longterm']) > 0:
            first_close = candles_data['longterm'][0].get('close', current_price)
            weekly_pct = ((current_price - first_close) / first_close) * 100 if first_close > 0 else 0
            
            highs = [c.get('high', current_price) for c in candles_data['longterm']]
            lows = [c.get('low', current_price) for c in candles_data['longterm']]
            week52_high = max(highs) if highs else current_price
            week52_low = min(lows) if lows else current_price
        
        return daily_pct, weekly_pct, week52_high, week52_low
    
    def _blend_scores(self, scores_by_tf, w_intra, w_swing, w_long, regime=None, atr_pct=None):
        """
        IMPROVED: Timeframe Hierarchy Logic (Catch Early Moves)
        
        Strategy:
        1. If 5m alone shows conviction -> early signal (lower confidence)
        2. If 5m + 15m align -> high confidence entry (sweet spot)
        3. 1h = veto only (don't trade against daily)
        
        This catches moves 2-3 minutes earlier than retail algos while avoiding
        trades that contradict the longer-term trend.
        """
        intra_score = scores_by_tf.get('intraday', {}).get('final_score', 0)
        swing_score = scores_by_tf.get('swing', {}).get('final_score', 0)
        long_score = scores_by_tf.get('longterm', {}).get('final_score', 0)
        
        blended_final = 0
        blended_confidence = 0
        blended_atr = 0
        weight_sum = 0
        alignment_count = 1
        early_signal = False
        veto_flag = False
        
        candles_data = {'intraday': [], 'swing': [], 'longterm': []}
        
        # ========================================================================
        # IMPROVEMENT 4: TIMEFRAME HIERARCHY
        # ========================================================================
        
        # VETO CHECK: 1h goes opposite to 5m+15m consensus
        if abs(long_score) > 0.35:
            consensus_direction = intra_score + swing_score
            if (consensus_direction > 0 and long_score < -0.35) or \
               (consensus_direction < 0 and long_score > 0.35):
                # Strong veto: longterm opposes intraday+swing
                veto_flag = True
                intra_score *= 0.4  # Dampen signal, don't skip entirely
        
        # EARLY SIGNAL: 5m moving alone (before swing catches up)
        if abs(intra_score) > 0.50 and abs(swing_score) < 0.20:
            early_signal = True
            # Use intraday score but reduce confidence (not yet confirmed)
            weight_sum = w_intra
            blended_final = intra_score * 0.70  # Take signal at 70% strength (early)
            blended_confidence = scores_by_tf['intraday']['confidence'] * 0.75  # Lower confidence
            blended_atr = scores_by_tf['intraday']['atr'] or 0
            alignment_count = 1  # Single timeframe signal
        
        # CONFIRMATION: 5m + 15m aligned (sweet spot for entry)
        elif abs(intra_score) > 0.25 and abs(swing_score) > 0.25 and \
             (intra_score * swing_score) > 0:  # Same direction
            # Both timeframes agree
            weight_sum = w_intra + w_swing
            blended_final = (intra_score * w_intra + swing_score * w_swing) / weight_sum
            blended_confidence = (scores_by_tf['intraday']['confidence'] * w_intra + 
                                 scores_by_tf['swing']['confidence'] * w_swing) / weight_sum
            blended_atr = ((scores_by_tf['intraday']['atr'] or 0) * w_intra + 
                          (scores_by_tf['swing']['atr'] or 0) * w_swing) / weight_sum
            alignment_count = 2
            
            # If 1h also aligns, full confirmation
            if (long_score * intra_score) > 0 and abs(long_score) > 0.15:
                blended_final = (intra_score * w_intra + swing_score * w_swing + long_score * w_long) / (w_intra + w_swing + w_long)
                blended_confidence = (scores_by_tf['intraday']['confidence'] * w_intra + 
                                     scores_by_tf['swing']['confidence'] * w_swing +
                                     scores_by_tf['longterm']['confidence'] * w_long) / (w_intra + w_swing + w_long)
                blended_atr = ((scores_by_tf['intraday']['atr'] or 0) * w_intra + 
                              (scores_by_tf['swing']['atr'] or 0) * w_swing +
                              (scores_by_tf['longterm']['atr'] or 0) * w_long) / (w_intra + w_swing + w_long)
                alignment_count = 3
        
        # DEFAULT: Use all timeframes with standard weights
        else:
            if w_intra > 0 and 'intraday' in scores_by_tf:
                blended_final += intra_score * w_intra
                blended_confidence += scores_by_tf['intraday']['confidence'] * w_intra
                blended_atr += (scores_by_tf['intraday']['atr'] or 0) * w_intra
                weight_sum += w_intra
            
            if w_swing > 0 and 'swing' in scores_by_tf:
                blended_final += swing_score * w_swing
                blended_confidence += scores_by_tf['swing']['confidence'] * w_swing
                blended_atr += (scores_by_tf['swing']['atr'] or 0) * w_swing
                weight_sum += w_swing
            
            if w_long > 0 and 'longterm' in scores_by_tf:
                blended_final += long_score * w_long
                blended_confidence += scores_by_tf['longterm']['confidence'] * w_long
                blended_atr += (scores_by_tf['longterm']['atr'] or 0) * w_long
                weight_sum += w_long
            
            if weight_sum > 0:
                blended_final /= weight_sum
                blended_confidence /= weight_sum
                blended_atr /= weight_sum
        
        # Alignment bonus (if 2+ timeframes agree)
        if alignment_count >= 2:
            blended_confidence += 15  # Bonus for multi-TF agreement
        
        # Veto penalty
        if veto_flag:
            blended_confidence = max(25, blended_confidence - 20)  # Cap at 25 when vetoed
        
        blended_confidence = min(100, max(20, blended_confidence))  # Range: 20-100
        
        # Price changes will be calculated in _try_symbol after blending
        return {
            'final': blended_final,
            'confidence': blended_confidence,
            'atr': blended_atr,
            'alignment_count': alignment_count
        }
    
    def _calculate_mode_score(self, scores_by_tf, w_intra, w_swing, w_long, 
                             pattern_name, pattern_conf, pattern_impact, event_risk, symbol):
        """Calculate composite score using specific weights (for multi-mode reporting)."""
        intra = scores_by_tf.get('intraday', {}).get('final_score', 0)
        swing = scores_by_tf.get('swing', {}).get('final_score', 0)
        long = scores_by_tf.get('longterm', {}).get('final_score', 0)
        
        # Blend with provided weights
        blended = (intra * w_intra) + (swing * w_swing) + (long * w_long)
        
        # Apply adjustments (same as final_score)
        adjusted = self._apply_final_adjustments(
            blended, pattern_name, pattern_conf, pattern_impact, event_risk, symbol
        )
        return adjusted
    
    def _compute_context_metrics(self, vwap_score, volume_score, regime, risk_level, 
                                 pv_div_score, pr_div_score, pv_confidence):
        """Calculate context score (0-5 scale) based on institutional signals."""
        from math import tanh  # Import here to match main script
        
        score = 2.5  # Neutral baseline
        
        # VWAP pressure (most important early signal)
        vwap_contrib = 1.0 * tanh(vwap_score * 1.8)
        score += vwap_contrib
        
        # Volume participation
        volume_contrib = 0.7 * tanh(volume_score * 1.5)
        score += volume_contrib
        
        # Divergence detection (CAPPED - cannot boost context)
        if pv_div_score < -0.5:  # Climax conditions
            divergence_contrib = -0.6 * pv_confidence
            score += divergence_contrib
        
        if pr_div_score < -0.5:  # Bearish divergence
            score -= 0.3
        
        # Market regime modulation
        regime_str = regime or 'neutral'
        if 'trending' in regime_str:
            score += 0.4
        elif 'volatile' in regime_str:
            score -= 0.6
        
        # Risk compression
        if risk_level == 'HIGH':
            score = 2.5 + (score - 2.5) * 0.55
        elif risk_level == 'MEDIUM':
            score = 2.5 + (score - 2.5) * 0.75
        
        # Safety clamp
        score = max(0.0, min(5.0, score))
        return round(score, 2)
    
    def _compute_context_momentum(self, vwap_score, volume_score, regime, pv_div_score, pr_div_score):
        """Calculate context momentum (-1 to +1) reflecting rate of change."""
        from math import tanh
        
        momentum = 0.0
        
        # VWAP momentum (derivative of tanh)
        vwap_momentum = 1.0 * (1 - tanh(vwap_score * 1.8)**2) * 1.8 * vwap_score
        momentum += 0.6 * vwap_momentum
        
        # Volume momentum
        volume_momentum = 0.7 * (1 - tanh(volume_score * 1.5)**2) * 1.5 * volume_score
        momentum += 0.4 * volume_momentum
        
        # Divergence impact on momentum
        if pv_div_score < -0.5:
            momentum -= 0.3
        
        if pr_div_score < -0.5:
            momentum -= 0.15
        
        # Clamp
        momentum = max(-1.0, min(1.0, momentum))
        return round(momentum, 2)
    
    def _compute_system_state_authoritative(self, context_score, context_momentum, risk_level, news_score, confidence):
        """
        Compute authoritative system state for hard execution decisions.
        
        States:
        - STAND_DOWN: Avoid - high risk or negative context
        - OBSERVE: Watch - mixed signals
        - ENGAGE: Trade - positive context  
        - EXPAND: Aggressive - strong context + momentum + low risk
        
        NOTE: High-confidence signals (>70) override context weakness to allow technical trades.
        """
        # STAND_DOWN conditions (most restrictive)
        if risk_level == 'HIGH' and confidence < 75:
            return 'STAND_DOWN'
        
        # Context weakness is tolerated for high-confidence technical setups
        # Allow trading if confidence is very high despite poor context
        if confidence < 70:
            # For lower confidence, apply strict context checks
            if context_score < 1.5 or context_momentum < -0.5:
                return 'STAND_DOWN'
        
        if news_score < -0.5:  # Only block on VERY negative news (was -0.4)
            return 'STAND_DOWN'
        
        if confidence < 25:  # Very low confidence
            return 'STAND_DOWN'
        
        # EXPAND conditions (most aggressive)
        if context_score > 3.8 and context_momentum > 0.6 and risk_level in ['LOW', 'MEDIUM']:
            return 'EXPAND'
        
        # ENGAGE conditions (normal trading)
        if context_score > 2.8 and context_momentum > 0.0 and risk_level in ['LOW', 'MEDIUM']:
            return 'ENGAGE'
        
        # For high-confidence signals (>70), allow ENGAGE even if context is weak
        if confidence > 70 and context_score >= 1.2 and risk_level != 'HIGH':
            return 'ENGAGE'
        
        # OBSERVE (default - mixed signals)
        return 'OBSERVE'
    
    def _get_standdown_reason(self, context_score, context_momentum, risk_level, news_score):
        """Get human-readable reason for STAND_DOWN state."""
        reasons = []
        
        if risk_level == 'HIGH':
            reasons.append("High risk zone")
        if context_score < 1.5:
            reasons.append("Hostile context")
        if context_momentum < -0.5:
            reasons.append("Deteriorating momentum")
        if news_score < -0.4:
            reasons.append("Negative news shock")
        
        return " | ".join(reasons) if reasons else "Risk factors detected"
    
    def _no_data_result(self, symbol):
        """Return result for symbols with no data."""
        return {
            "symbol": symbol,
            "variant": None,
            "source": None,
            "market_regime": None,
            "status": "NO_DATA",
            "mode": self.mode,
            "final_score": None,
            "confidence": None,
            "price": None,
            "or_score": None,
            "vwap_score": None,
            "structure_score": None,
            "rsi": None,
            "rsi_score": None,
            "ema_score": None,
            "volume_score": None,
            "macd_score": None,
            "bb_score": None,
            "atr": None,
            "opening_range": (None, None),
            "vwap": None,
            "weights": {"intraday": self.w_intraday, "swing": self.w_swing, "longterm": self.w_longterm}
        }
