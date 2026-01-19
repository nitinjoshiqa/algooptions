"""Main scoring engine - Strategy pattern implementation."""
from indicators import rsi, ema, atr, vwap_proxy, opening_range_from_candles
from indicators.patterns import detect_patterns
from scoring import (rsi_score, ema_score, opening_range_score, vwap_score, 
                     structure_score, volume_score, macd_score, bollinger_bands_score,
                     calculate_sl_target)
from options.option_scorer import OptionScorer
from data_providers import get_spot_price, get_intraday_candles_for
from core.market_regime import MarketRegimeDetector
from core.config import MODE_WEIGHTS, OPENING_RANGE_MINUTES, VWAP_LOOKBACK_MIN

# Global cache for index (NIFTY) score to avoid repeated calls
_INDEX_SCORE_CACHE = {}


class BearnessScoringEngine:
    """Main scoring engine using Strategy pattern."""
    
    def __init__(self, mode='intraday', use_yf=False, force_yf=False, quick_mode=False,
                 intraday_weight=None, swing_weight=None, longterm_weight=None,
                 index_bias=None):
        self.mode = mode
        self.use_yf = use_yf
        self.force_yf = force_yf
        self.quick_mode = quick_mode
        
        # Set weights based on mode or custom values
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
        
        # Index bias (market alignment multiplier)
        self.index_bias = index_bias
        self.index_bias_source = 'external' if index_bias is not None else 'auto'
        
        self.regime_detector = MarketRegimeDetector()
        self.option_scorer = OptionScorer(use_yf=use_yf)
    
    def compute_score(self, symbol):
        """Compute bearness score for a symbol."""
        # Try symbol variants
        variants = self._get_symbol_variants(symbol)
        
        for sym in variants:
            result = self._try_symbol(sym, symbol)
            if result and result.get('status') == 'OK':
                return result
        
        # No data found
        return self._no_data_result(symbol)
    
    def _get_symbol_variants(self, symbol):
        """Get symbol variants to try."""
        if self.quick_mode:
            return [symbol, symbol + '.NS']
        else:
            return [symbol, symbol.replace('-', ''), symbol.replace('.', ''), 
                   symbol + '.NS', symbol + ' NSE']
    
    def _try_symbol(self, sym, original_symbol):
        """Try to fetch and score a symbol variant."""
        # Get current price with timeout handling
        price = get_spot_price(sym, self.use_yf, self.force_yf)
        if price is None:
            return None

        # Fetch candles for all required timeframes (needed for option scorer too)
        try:
            candles_data = self._fetch_all_timeframes(sym)
        except Exception as e:
            # Log and continue with empty candles (will use default scores)
            print(f"[WARN] Failed to fetch candles for {sym}: {type(e).__name__}")
            candles_data = {'intraday': [], 'swing': [], 'longterm': []}
        
        if not candles_data['intraday']:
            # Return minimal result with just price, skip detailed scoring
            return self._minimal_score_result(sym, original_symbol, price)
        
        # Compute scores for each timeframe (to get ATR and RSI for option scoring)
        scores_by_tf = self._compute_timeframe_scores(candles_data, price, sym)
        if 'intraday' not in scores_by_tf:
            # Fall back to minimal scoring
            return self._minimal_score_result(sym, original_symbol, price)

        # Option score (nearest ATM) - with ATR and RSI for synthetic scoring fallback
        option_score = None
        try:
            atr = scores_by_tf['intraday'].get('atr', 1.0) if scores_by_tf.get('intraday') else 1.0
            rsi = scores_by_tf['intraday'].get('rsi', 50.0) if scores_by_tf.get('intraday') else 50.0
            option_score = self.option_scorer.score_atm_option(sym, price, atr, rsi)
        except Exception:
            pass
        
        # If option scoring failed, use sensible defaults based on current metrics
        if option_score is None:
            from dataclasses import dataclass
            @dataclass
            class StubOptionScore:
                option_score: float = 0.0
                option_iv: float = 0.20  # Assumed 20% IV for NSE stocks
                option_spread_pct: float = 0.02  # Assumed 2% bid-ask spread
                option_type: str = "ATM"
                strike: float = price
                expiry: str = "N/A"
                source: str = "stub"
                option_volume: float = 0
                option_oi: float = 0
                option_delta: float = 0.5  # ATM delta
                option_gamma: float = 0.05
                option_theta: float = -0.01
                option_vega: float = 0.20
            option_score = StubOptionScore()
        
        # Detect market regime and adjust weights if needed
        detected_regime = None
        w_intra = self.w_intraday
        w_swing = self.w_swing
        w_long = self.w_longterm
        
        if not self.custom_weights:
            regime_info = self.regime_detector.detect(
                candles_data['intraday'],
                candles_data.get('swing'),
                candles_data.get('longterm')
            )
            detected_regime = regime_info['regime']
            w_intra = regime_info['weights']['intraday']
            w_swing = regime_info['weights']['swing']
            w_long = regime_info['weights']['longterm']
        
        # Blend scores
        blended = self._blend_scores(scores_by_tf, w_intra, w_swing, w_long)
        
        # Detect chart patterns on all timeframes
        pattern_name, pattern_conf, pattern_impact, pattern_detail = detect_patterns(
            candles_data.get('intraday', []),
            candles_data.get('swing'),
            candles_data.get('longterm')
        )

        # Event risk awareness: detect large overnight gaps (proxy for earnings/news)
        event_risk = self._detect_event_risk(candles_data.get('intraday'))

        
        # Apply pattern influence to final score with confidence boost
        # Pattern impact is now weighted: stronger patterns (higher confidence) have bigger impact
        # Base impact: -0.35 to +0.35 (was -0.25 to +0.25)
        # Confidence multiplier: 50% confidence = 0.6x, 80% confidence = 1.0x, 95% confidence = 1.2x
        if pattern_name:
            confidence_multiplier = 0.5 + (pattern_conf - 0.5) * 1.4  # Maps 50% -> 0.6x, 80% -> 1.0x, 95% -> 1.2x
            adjusted_final_score = blended['final'] + (pattern_impact * 1.4 * confidence_multiplier)
        else:
            adjusted_final_score = blended['final']

        # Boost pattern-following setups even if volume_score is muted
        try:
            vol_score_now = scores_by_tf['intraday'].get('volume_score', 0)
            if pattern_name and abs(vol_score_now) < 0.2:
                adjusted_final_score += pattern_impact * 0.1  # modest bump
        except Exception:
            pass

        # Index-bias multipliers: prioritize market-aligned entries
        # Skip applying bias when scoring the index itself
        try:
            if original_symbol.upper() not in ('NIFTY', 'NSEI'):
                ib = self.index_bias if self.index_bias is not None else None
                if ib is None:
                    # Try to get from global cache first (avoid repeated NIFTY calls)
                    global _INDEX_SCORE_CACHE
                    if 'nsei' not in _INDEX_SCORE_CACHE:
                        # Lazy compute once and cache globally
                        try:
                            idx = self._get_index_score()
                            if idx and idx.get('final_score') is not None:
                                _INDEX_SCORE_CACHE['nsei'] = float(idx['final_score'])
                            else:
                                _INDEX_SCORE_CACHE['nsei'] = 0.0
                        except Exception as e:
                            # Silently fail - treat as neutral market
                            _INDEX_SCORE_CACHE['nsei'] = 0.0
                    
                    ib = _INDEX_SCORE_CACHE.get('nsei', 0.0)
                    self.index_bias = ib
                    self.index_bias_source = 'global_cache'
                ib = self.index_bias or 0.0
                # Apply directional multipliers
                if ib < -0.05:  # Bearish index
                    if adjusted_final_score < 0:
                        adjusted_final_score *= 1.15
                        blended['confidence'] *= 1.08
                    elif adjusted_final_score > 0:
                        adjusted_final_score *= 0.90
                        blended['confidence'] *= 0.95
                elif ib > 0.05:  # Bullish index
                    if adjusted_final_score > 0:
                        adjusted_final_score *= 1.15
                        blended['confidence'] *= 1.08
                    elif adjusted_final_score < 0:
                        adjusted_final_score *= 0.90
                        blended['confidence'] *= 0.95
        except Exception:
            pass

        # Event risk penalty: reduce aggression on gap/earnings-like days
        if event_risk and event_risk.get('flag'):
            adjusted_final_score *= 0.9
            blended['confidence'] *= 0.9

        # Clamp confidence
        blended['confidence'] = min(100.0, max(0.0, blended['confidence']))
        # Optional clamp final score
        adjusted_final_score = max(-1.0, min(1.0, adjusted_final_score))
        
        # Calculate price change metrics
        daily_pct, weekly_pct, week52_high, week52_low = self._calculate_price_changes(candles_data, price)
        
        # Build result
        intraday_data = scores_by_tf['intraday']
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
            "final_score": adjusted_final_score,
            "confidence": blended['confidence'],
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
            "opening_range": intraday_data['opening_range'],
            "vwap": intraday_data['vwap'],
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
            # Add timeframe-specific scores for alignment calculation
            "score_5m": scores_by_tf['intraday']['final_score'],
            "score_15m": scores_by_tf.get('swing', {}).get('final_score', 0),
            "score_1h": scores_by_tf.get('longterm', {}).get('final_score', 0),
            # Add price change metrics
            "daily_change_pct": daily_pct,
            "weekly_change_pct": weekly_pct,
            "52w_high": week52_high,
            "52w_low": week52_low,
            # Event risk annotation
            "event_risk": event_risk,
            # Add candles data for Pivot calculation
            "candles_data": candles_data
        }
        return result

    def _detect_event_risk(self, intraday_candles):
        """Detect overnight gaps as proxy for earnings/news event risk.

        Returns dict: {flag: bool, gap_pct: float, reason: str}
        """
        try:
            if not intraday_candles or len(intraday_candles) < 2:
                return {"flag": False, "gap_pct": 0.0, "reason": "insufficient"}

            # Extract dates if available
            def _get_date(c):
                return c.get('date') or c.get('timestamp', '')[:10]

            by_date = {}
            for c in intraday_candles:
                d = _get_date(c)
                by_date.setdefault(d, []).append(c)
            dates = [d for d in by_date.keys() if d]
            if len(dates) < 2:
                return {"flag": False, "gap_pct": 0.0, "reason": "oneday"}
            dates.sort()
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
    
    def _get_index_score(self):
        """Get NIFTY/NSEI index score with minimal data requirements.
        
        Returns a simple scoring result based on index price movement only.
        Uses exponential moving average to determine trend (bullish/bearish).
        Falls back to neutral (0.0) if data unavailable.
        
        Uses ^NSEI ticker which is the standard Yahoo Finance ticker for NIFTY 50 index.
        """
        try:
            # Try to get NIFTY index data using ^NSEI ticker
            for sym_variant in ['^NSEI', 'NIFTYBEES.NS']:
                try:
                    # Get just the price
                    price = get_spot_price(sym_variant, use_yf=True, force_yf=True)
                    if price is None:
                        continue
                    
                    # Try to get some candles for trend detection
                    try:
                        candles, src = get_intraday_candles_for(sym_variant, '1day', 20, use_yf=True, force_yf=True)
                        if candles and len(candles) >= 3:
                            # Simple trend: compare recent price to 10-day average
                            closes = [float(c.get('close', 0)) for c in candles[-10:]]
                            avg_price = sum(closes) / len(closes)
                            trend_score = (price - avg_price) / avg_price if avg_price > 0 else 0.0
                            # Clamp to [-1, +1]
                            trend_score = max(-1.0, min(1.0, trend_score))
                        else:
                            trend_score = 0.0  # Neutral if no candles
                    except Exception:
                        trend_score = 0.0
                    
                    # Return a minimal result with the trend score
                    return {
                        "symbol": "NIFTY",
                        "final_score": trend_score,
                        "price": price,
                        "source": src or "yfinance",
                        "status": "INDEX"
                    }
                except Exception:
                    continue  # Try next variant
            
            # If all variants fail, return neutral
            return {"final_score": 0.0, "status": "INDEX_NEUTRAL"}
        
        except Exception:
            return {"final_score": 0.0, "status": "INDEX_ERROR"}
    
    def _minimal_score_result(self, sym, original_symbol, price):
        """Return a minimal scoring result when detailed candle data is unavailable.
        
        Uses default values for missing technical indicators to allow stock
        to be included in results instead of being skipped entirely.
        """
        result = {
            "symbol": original_symbol,
            "variant": sym,
            "source": "fallback",
            "market_regime": "unknown",
            "pattern": "None",
            "pattern_confidence": 0.0,
            "pattern_detail": "No candle data",
            "status": "MINIMAL",  # Mark as minimal scoring fallback
            "mode": self.mode,
            # Use neutral/default scores when data unavailable
            "final_score": 0.0,  # Neutral score
            "confidence": 20.0,  # Low confidence due to missing data
            "price": price,
            # Default technical indicator values
            "or_score": 0.0,
            "vwap_score": 0.0,
            "structure_score": 0.0,
            "rsi": 50.0,  # Neutral RSI
            "rsi_score": 0.0,
            "ema_score": 0.0,
            "volume_score": 0.0,
            "macd_score": 0.0,
            "bb_score": 0.0,
            "atr": 1.0,  # Default ATR
            "opening_range": 0.0,
            "vwap": price,  # Use current price as proxy
            # Option scoring with defaults
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
            # Default timeframe scores
            "score_5m": 0.0,
            "score_15m": 0.0,
            "score_1h": 0.0,
            # Price change metrics (unavailable)
            "daily_change_pct": 0.0,
            "weekly_change_pct": 0.0,
            "52w_high": price,
            "52w_low": price,
            # Event risk annotation
            "event_risk": {"flag": False, "gap_pct": 0.0, "reason": "no_data"},
            "candles_data": {'intraday': [], 'swing': [], 'longterm': [], 'source': 'fallback'}
        }
        return result
    
    def _fetch_all_timeframes(self, symbol):
        """Fetch candles for all required timeframes."""
        result = {'intraday': None, 'swing': None, 'longterm': None, 'source': []}
        
        if self.w_intraday > 0:
            bars = 40 if self.quick_mode else 78
            candles, src = get_intraday_candles_for(symbol, '5minute', bars, self.use_yf, self.force_yf)
            if candles:
                result['intraday'] = candles
                result['source'].append(src or 'breeze')
        
        if self.w_swing > 0:
            bars = 15 if self.quick_mode else 26
            candles, src = get_intraday_candles_for(symbol, '15minute', bars, self.use_yf, self.force_yf)
            if candles:
                result['swing'] = candles
                if src and src not in result['source']:
                    result['source'].append(src)
        
        if self.w_longterm > 0:
            bars = 10 if self.quick_mode else 20
            candles, src = get_intraday_candles_for(symbol, '1day', bars, self.use_yf, self.force_yf)
            if candles:
                result['longterm'] = candles
                if src and src not in result['source']:
                    result['source'].append(src)
        
        result['source'] = ', '.join(result['source']) if result['source'] else 'breeze'
        return result
    
    def _compute_timeframe_scores(self, candles_data, price, symbol):
        """Compute scores for all available timeframes."""
        scores = {}
        
        for tf_name, candles in [('intraday', candles_data['intraday']),
                                  ('swing', candles_data['swing']),
                                  ('longterm', candles_data['longterm'])]:
            if candles and len(candles) >= 3:
                # Intraday session timing filter: exclude first/last 30 minutes
                if tf_name == 'intraday' and len(candles) > 20:
                    try:
                        trimmed = candles[6:-6]  # 6 bars = 30 minutes on 5m
                        candles = trimmed if len(trimmed) >= 3 else candles
                    except Exception:
                        pass
                scores[tf_name] = self._compute_single_timeframe(candles, price, symbol)
        
        return scores
    
    def _compute_single_timeframe(self, candles, price, symbol):
        """Compute score for a single timeframe with regime-adaptive weighting."""
        # Normalize all indicators to [-1, +1] range
        or_bars = max(1, OPENING_RANGE_MINUTES // 5)
        or_high, or_low = opening_range_from_candles(candles, or_bars)
        lookback_bars = max(1, VWAP_LOOKBACK_MIN // 5)
        vwap = vwap_proxy(candles, lookback_bars)
        
        # Get raw indicator scores
        or_s = opening_range_score(price, or_high, or_low)
        vwap_s = vwap_score(price, vwap)
        struct_s = structure_score(candles)
        
        # Technical indicators
        rsi_val = rsi(candles, period=14)
        rsi_s = rsi_score(rsi_val)
        ema_s = ema_score(candles)
        vol_s = volume_score(candles, periods=20)
        macd_s = macd_score(candles)
        bb_s = bollinger_bands_score(candles, period=20)
        atr_val = atr(candles, period=14)
        
        # NORMALIZATION: Clamp all scores to [-1, +1] range
        def normalize_score(score):
            """Normalize any score to [-1, +1] range."""
            return max(-1.0, min(1.0, score))
        
        or_s_norm = normalize_score(or_s)
        vwap_s_norm = normalize_score(vwap_s)
        struct_s_norm = normalize_score(struct_s)
        rsi_s_norm = normalize_score(rsi_s)
        ema_s_norm = normalize_score(ema_s)
        vol_s_norm = normalize_score(vol_s)
        macd_s_norm = normalize_score(macd_s)
        bb_s_norm = normalize_score(bb_s)
        atr_norm = normalize_score(atr_val / 100.0) if atr_val else 0  # Volatility factor
        
        # REGIME-ADAPTIVE WEIGHTING
        # Default equal weights
        weights = {
            'or': 1.0, 'vwap': 1.0, 'struct': 1.0, 'rsi': 1.0,
            'ema': 1.0, 'vol': 1.0, 'macd': 1.0, 'bb': 1.0
        }
        
        # Detect regime from candles data
        recent_candles = candles[-10:] if len(candles) >= 10 else candles
        highs = [c.get('high', 0) for c in recent_candles]
        lows = [c.get('low', 0) for c in recent_candles]
        closes = [c.get('close', 0) for c in recent_candles]
        
        if highs and lows and closes:
            # Calculate volatility and trend
            atr_recent = sum(h - l for h, l in zip(highs, lows)) / len(highs) if highs else 1
            price_range = max(closes) - min(closes)
            volatility_pct = (atr_recent / (sum(closes) / len(closes))) * 100 if closes else 5
            
            # Trend detection: compare recent closes to EMA
            ema_vals = [c.get('ema', close) for c, close in zip(recent_candles, closes)]
            trend_direction = 1 if closes[-1] > ema_vals[-1] else -1
            
            if volatility_pct > 4.0:
                # VOLATILE market: Penalize confidence, trust ATR & Volume
                regime = 'volatile'
                weights = {'or': 0.7, 'vwap': 0.7, 'struct': 0.8, 'rsi': 0.6,
                          'ema': 0.6, 'vol': 1.5, 'macd': 0.6, 'bb': 1.3}
            elif trend_direction * closes[-1] > trend_direction * (sum(ema_vals) / len(ema_vals)):
                # TRENDING market: Boost trend indicators & Volume
                regime = 'trending'
                weights = {'or': 1.1, 'vwap': 0.9, 'struct': 1.3, 'rsi': 0.9,
                          'ema': 1.4, 'vol': 1.3, 'macd': 1.2, 'bb': 0.8}
            else:
                # RANGING market: Boost oscillators & Volume
                regime = 'ranging'
                weights = {'or': 0.9, 'vwap': 1.3, 'struct': 0.9, 'rsi': 1.2,
                          'ema': 0.8, 'vol': 1.2, 'macd': 1.0, 'bb': 1.4}
        else:
            regime = 'unknown'
        
        # Apply weighted normalization
        weighted_scores = [
            or_s_norm * weights['or'],
            vwap_s_norm * weights['vwap'],
            struct_s_norm * weights['struct'],
            rsi_s_norm * weights['rsi'],
            ema_s_norm * weights['ema'],
            vol_s_norm * weights['vol'],
            macd_s_norm * weights['macd'],
            bb_s_norm * weights['bb']
        ]
        
        # Normalize weights sum
        weight_sum = sum(weights.values())
        final = sum(weighted_scores) / weight_sum if weight_sum > 0 else 0
        
        # ENHANCEMENT 3: Volatile market confidence penalty
        volatility_penalty = 1.0
        if regime == 'volatile':
            volatility_penalty = 0.85  # Reduce confidence in volatile conditions
        
        # Multi-Indicator Consensus + Volume + Regime
        all_scores = [or_s_norm, vwap_s_norm, struct_s_norm, rsi_s_norm, 
                      ema_s_norm, vol_s_norm, macd_s_norm, bb_s_norm]
        bearish_count = sum(1 for sc in all_scores if sc < -0.2)
        bullish_count = sum(1 for sc in all_scores if sc > 0.2)
        
        max_agreement = max(bearish_count, bullish_count)
        if max_agreement >= 5:
            consensus_factor = 1.0
        elif max_agreement == 4:
            consensus_factor = 0.85
        else:
            consensus_factor = 0.6
        
        # Volume confirmation (increased impact - volume is key conviction factor)
        # Stricter penalties for low volume to filter fake breakouts
        if vol_s_norm > 0.5:
            volume_factor = 1.30  # High volume = strong conviction (boosted)
        elif vol_s_norm > 0.3:
            volume_factor = 1.15
        elif vol_s_norm > 0.0:
            volume_factor = 1.0
        elif vol_s_norm > -0.2:
            volume_factor = 0.75  # Low volume = reduced conviction
        elif vol_s_norm > -0.4:
            volume_factor = 0.50  # Very low volume = major penalty
        else:
            volume_factor = 0.35  # Extremely low volume = near-disqualification
        
        # Base confidence
        signal_agreement = max(bearish_count, bullish_count) / len(all_scores)
        base_confidence = signal_agreement * 100

        # RSI band factor: boost confidence when RSI aligns with final direction
        rsi_factor = 1.0
        try:
            if final > 0:
                if rsi_val >= 70:
                    rsi_factor = 1.20
                elif rsi_val >= 60:
                    rsi_factor = 1.10
            elif final < 0:
                if rsi_val <= 30:
                    rsi_factor = 1.20
                elif rsi_val <= 40:
                    rsi_factor = 1.10
        except Exception:
            pass

        # Alignment boost: OR/VWAP/EMA agreement with final direction
        align_count = 0
        for s in (or_s_norm, vwap_s_norm, ema_s_norm):
            try:
                if final > 0 and s > 0.1:
                    align_count += 1
                elif final < 0 and s < -0.1:
                    align_count += 1
            except Exception:
                continue
        align_factor = 1.0 + (0.08 * max(0, align_count - 1))  # up to ~16%

        # Apply all factors
        confidence = base_confidence * consensus_factor * volume_factor * volatility_penalty * rsi_factor * align_factor
        # Confidence floor for strong signals
        if abs(final) >= 0.35 and confidence < 35:
            confidence = 35.0
        confidence = min(100, max(0, confidence))
        
        return {
            "final_score": final,
            "confidence": confidence,
            "regime": regime,  # Market regime (trending/ranging/volatile)
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
            "vwap": vwap
        }
    
    def _calculate_price_changes(self, candles_data, current_price):
        """Calculate daily, weekly, and 52-week price changes."""
        daily_pct = 0
        weekly_pct = 0
        week52_high = current_price
        week52_low = current_price
        
        # Daily change from intraday candles (first to last)
        if candles_data['intraday'] and len(candles_data['intraday']) > 0:
            first_close = candles_data['intraday'][0].get('close', current_price)
            daily_pct = ((current_price - first_close) / first_close) * 100 if first_close > 0 else 0
        
        # Weekly and 52-week from daily candles
        if candles_data['longterm'] and len(candles_data['longterm']) > 0:
            # Weekly: first candle to last candle
            first_close = candles_data['longterm'][0].get('close', current_price)
            weekly_pct = ((current_price - first_close) / first_close) * 100 if first_close > 0 else 0
            
            # 52-week high/low from available daily candles
            highs = [c.get('high', current_price) for c in candles_data['longterm']]
            lows = [c.get('low', current_price) for c in candles_data['longterm']]
            week52_high = max(highs) if highs else current_price
            week52_low = min(lows) if lows else current_price
        
        return daily_pct, weekly_pct, week52_high, week52_low
    
    def _blend_scores(self, scores_by_tf, w_intra, w_swing, w_long):
        """Blend scores from multiple timeframes."""
        blended_final = 0
        blended_confidence = 0
        blended_atr = 0
        weight_sum = 0
        
        # Collect timeframe scores for alignment check
        tf_scores = []
        
        if w_intra > 0 and 'intraday' in scores_by_tf:
            blended_final += scores_by_tf['intraday']['final_score'] * w_intra
            blended_confidence += scores_by_tf['intraday']['confidence'] * w_intra
            blended_atr += (scores_by_tf['intraday']['atr'] or 0) * w_intra
            weight_sum += w_intra
            tf_scores.append(scores_by_tf['intraday']['final_score'])
        
        if w_swing > 0 and 'swing' in scores_by_tf:
            blended_final += scores_by_tf['swing']['final_score'] * w_swing
            blended_confidence += scores_by_tf['swing']['confidence'] * w_swing
            blended_atr += (scores_by_tf['swing']['atr'] or 0) * w_swing
            weight_sum += w_swing
            tf_scores.append(scores_by_tf['swing']['final_score'])
        
        if w_long > 0 and 'longterm' in scores_by_tf:
            blended_final += scores_by_tf['longterm']['final_score'] * w_long
            blended_confidence += scores_by_tf['longterm']['confidence'] * w_long
            blended_atr += (scores_by_tf['longterm']['atr'] or 0) * w_long
            weight_sum += w_long
            tf_scores.append(scores_by_tf['longterm']['final_score'])
        
        if weight_sum > 0:
            blended_final /= weight_sum
            blended_confidence /= weight_sum
            blended_atr /= weight_sum
        
        # ENHANCEMENT 3: Timeframe Alignment Boost
        # Check if multiple timeframes agree on direction
        if len(tf_scores) >= 2:
            bearish_tfs = sum(1 for s in tf_scores if s < -0.05)
            bullish_tfs = sum(1 for s in tf_scores if s > 0.05)
            
            if len(tf_scores) == 3:
                # All 3 timeframes available
                if max(bearish_tfs, bullish_tfs) == 3:
                    blended_confidence *= 1.15  # All 3 align: +15% confidence boost
                elif max(bearish_tfs, bullish_tfs) == 2:
                    blended_confidence *= 1.0  # 2 out of 3: no change
                else:
                    blended_confidence *= 0.90  # Conflicting signals: -10% penalty
            elif len(tf_scores) == 2:
                # Only 2 timeframes available
                if max(bearish_tfs, bullish_tfs) == 2:
                    blended_confidence *= 1.10  # Both align: +10% boost
                else:
                    blended_confidence *= 0.92  # Conflicting: -8% penalty
        
        # Clamp confidence to 0-100 range
        blended_confidence = min(100, max(0, blended_confidence))
        
        return {
            'final': blended_final,
            'confidence': blended_confidence,
            'atr': blended_atr
        }
    
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
