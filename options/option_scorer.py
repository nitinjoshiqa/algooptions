"""Option scoring helper for nearest ATM options using Breeze API.

This module uses Breeze option chains. It is defensive: any failure returns None
so the rest of the screener can proceed without options data.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta
from math import log, sqrt, exp, erf, pi
from typing import Optional

try:
    from breeze_api import get_breeze_instance
except ImportError:
    get_breeze_instance = None


@dataclass
class OptionScore:
    option_score: float
    option_iv: float
    option_spread_pct: float
    option_type: str
    strike: float
    expiry: str
    source: str
    option_volume: float
    option_oi: float
    option_delta: float
    option_gamma: float
    option_theta: float
    option_vega: float


class OptionScorer:
    def __init__(self, use_yf: bool = True):
        """Initialize with Breeze support. Falls back to synthetic scoring if Breeze unavailable."""
        self.use_breeze = get_breeze_instance is not None
        self.breeze = None
        if self.use_breeze:
            try:
                self.breeze = get_breeze_instance()
            except Exception:
                self.breeze = None

    def _norm_cdf(self, x: float) -> float:
        return 0.5 * (1.0 + erf(x / sqrt(2.0)))

    def _norm_pdf(self, x: float) -> float:
        return (1.0 / sqrt(2.0 * pi)) * exp(-0.5 * x * x)

    def _bs_greeks(self, spot: float, strike: float, t: float, r: float, iv: float, option_type: str):
        """Compute Black-Scholes greeks. Returns tuple (delta, gamma, theta, vega)."""
        try:
            if spot <= 0 or strike <= 0 or t <= 0 or iv <= 0:
                return None, None, None, None
            d1 = (log(spot / strike) + (r + 0.5 * iv * iv) * t) / (iv * sqrt(t))
            d2 = d1 - iv * sqrt(t)
            pdf = self._norm_pdf(d1)
            cdf_d1 = self._norm_cdf(d1)
            cdf_d2 = self._norm_cdf(d2)

            if option_type == "CALL":
                delta = cdf_d1
                theta = -(spot * pdf * iv) / (2 * sqrt(t)) - r * strike * exp(-r * t) * cdf_d2
            else:
                delta = cdf_d1 - 1
                theta = -(spot * pdf * iv) / (2 * sqrt(t)) + r * strike * exp(-r * t) * (1 - cdf_d2)

            gamma = pdf / (spot * iv * sqrt(t))
            vega = spot * pdf * sqrt(t)
            return delta, gamma, theta, vega
        except Exception:
            return None, None, None, None

    def _get_next_expiry(self):
        """Get next Thursday (NSE weekly expiry)."""
        today = datetime.now()
        days_ahead = 3 - today.weekday()  # 3 = Thursday
        if days_ahead <= 0:  # Target day already happened this week
            days_ahead += 7
        expiry = today + timedelta(days=days_ahead)
        return expiry.strftime("%d-%b-%y").upper()

    def _synthetic_option_score(self, symbol: str, spot: float, atr: float, rsi: float) -> OptionScore:
        """Generate synthetic option score when Breeze data unavailable. 
        
        Based on stock volatility (ATR) and momentum (RSI) to simulate realistic option metrics.
        """
        try:
            # Get next expiry
            expiry = self._get_next_expiry()
            
            # Find nearest ATM strike
            strike_step = 50 if symbol in ['NIFTY', 'BANKNIFTY', 'FINNIFTY'] else 5
            atm_strike = round(spot / strike_step) * strike_step
            
            # Synthetic IV based on ATR/spot ratio (normalized volatility)
            vol_pct = (atr / spot) * 100 if spot > 0 else 20
            # Scale to IV: typical stock is 15-25% IV, scale vol_pct accordingly
            option_iv = max(0.10, min(0.35, 0.15 + (vol_pct / 5.0) * 0.1))
            
            # Synthetic bid-ask spread (tighter for higher liquidity)
            # Assume major stocks have ~2% spreads, illiquid have ~5%
            option_spread_pct = max(0.5, min(5.0, 2.0 + (20 - vol_pct) * 0.1))
            
            # Synthetic volume and OI (larger stocks have higher vol/oi)
            # Normalize: liquid stock ~5000 volume, illiquid ~500
            base_vol = 5000 if symbol in ['NIFTY', 'BANKNIFTY', 'SBIN', 'HDFC', 'INFY'] else 1000
            option_volume = int(base_vol * (0.5 + 0.5 * max(0, (50 - option_spread_pct) / 50)))
            option_oi = int(option_volume * 2)  # OI typically 2x volume
            
            # Synthetic greeks
            t = 7 / 365.0  # ~1 week to expiry
            r = 0.06  # Risk-free rate
            delta, gamma, theta, vega = self._bs_greeks(spot, atm_strike, t, r, option_iv, "CALL")
            
            if delta is None:
                # Fallback if BS calculation fails
                delta = 0.5
                gamma = 0.01
                theta = -0.001  # Daily theta decay (negative for long calls)
                vega = 0.2
            else:
                # Annualize theta: convert daily decay to annual (theta is typically per day in option markets)
                theta = theta / 365.0  # Convert to daily theta, then scale for display
            
            # Option score components: 40% spread, 30% IV, 20% volume, 10% OI
            spread_score = max(0, 1.0 - (option_spread_pct / 5.0))  # Tight spread preferred
            iv_score = max(0, 1.0 - abs(option_iv - 0.18) / 0.15)  # Target IV ~18%
            vol_score = min(1.0, option_volume / 5000.0)  # Normalize
            oi_score = min(1.0, option_oi / 10000.0)  # Normalize
            
            # Liquidity score (0-1) - how easy to trade
            liquidity_score = (0.4 * spread_score + 0.3 * iv_score + 0.2 * vol_score + 0.1 * oi_score)
            
            # Option score: scale -1 to +1, negative = unattractive/high cost, positive = attractive/low cost
            # High spread/IV makes options expensive (negative), low spread/IV makes them cheap (positive)
            option_score = (2.0 * liquidity_score - 1.0)  # Range: -1 to +1
            
            return OptionScore(
                option_score=option_score,
                option_iv=option_iv,
                option_spread_pct=option_spread_pct,
                option_type="CALL",
                strike=atm_strike,
                expiry=expiry,
                source="Synthetic",
                option_volume=option_volume,
                option_oi=option_oi,
                option_delta=delta,
                option_gamma=gamma,
                option_theta=theta,
                option_vega=vega,
            )
        except Exception:
            return None

    def score_atm_option(self, symbol: str, spot: float, atr: float = 1.0, rsi: float = 50.0) -> Optional[OptionScore]:
        """Score nearest ATM option using Breeze (or synthetic fallback).
        
        Args:
            symbol: Stock symbol
            spot: Current spot price
            atr: Average True Range (for volatility estimate)
            rsi: RSI value (for momentum context)
        
        Returns:
            OptionScore or None on complete failure
        """
        if spot is None or spot <= 0:
            return None
        
        # Try real Breeze data first
        if self.use_breeze and self.breeze is not None:
            try:
                expiry = self._get_next_expiry()
                strike_step = 50 if symbol in ['NIFTY', 'BANKNIFTY', 'FINNIFTY'] else 5
                atm_strike = round(spot / strike_step) * strike_step
                
                call_res = self.breeze.get_option_chain_quotes(
                    stock_code=symbol,
                    exchange_code="NFO",
                    expiry_date=expiry,
                    right="call",
                    strike_price=str(atm_strike)
                )
                
                if call_res and "Success" in call_res and call_res["Success"]:
                    call_data = call_res["Success"][0]
                    
                    # Get IV from Breeze, or fall back to volatility-based calculation if missing
                    breeze_iv = call_data.get("iv")
                    if breeze_iv and breeze_iv > 0:
                        option_iv = float(breeze_iv)
                    else:
                        # Breeze didn't return IV (common near expiry) - use stock volatility instead
                        vol_pct = (atr / spot) * 100 if spot > 0 and atr > 0 else 20
                        option_iv = max(0.10, min(0.35, 0.15 + (vol_pct / 5.0) * 0.1))
                    
                    option_volume = int(call_data.get("volume", 0))
                    option_oi = int(call_data.get("open_interest", 0))
                    ltp = float(call_data.get("ltp", 0))
                    bid = float(call_data.get("bid1", ltp))
                    ask = float(call_data.get("ask1", ltp))
                    spread_pct = ((ask - bid) / ltp * 100) if ltp > 0 else 0
                    
                    t = 7 / 365.0
                    r = 0.06
                    delta, gamma, theta, vega = self._bs_greeks(spot, atm_strike, t, r, option_iv, "CALL")
                    
                    if delta is None:
                        delta, gamma, theta, vega = 0.5, 0.01, -0.01, 0.2
                    
                    spread_score = max(0, 1.0 - (spread_pct / 2.0))
                    iv_score = max(0, 1.0 - abs(option_iv - 0.18) / 0.2)
                    vol_score = min(1.0, option_volume / 100.0)
                    oi_score = min(1.0, option_oi / 10000.0)
                    option_score = (0.4 * spread_score + 0.3 * iv_score + 0.2 * vol_score + 0.1 * oi_score)
                    
                    return OptionScore(
                        option_score=option_score,
                        option_iv=option_iv,
                        option_spread_pct=spread_pct,
                        option_type="CALL",
                        strike=atm_strike,
                        expiry=expiry,
                        source="Breeze+Volatility",
                        option_volume=option_volume,
                        option_oi=option_oi,
                        option_delta=delta,
                        option_gamma=gamma,
                        option_theta=theta,
                        option_vega=vega,
                    )
            except Exception:
                pass  # Fall through to synthetic
        
        # Fallback to synthetic scoring when Breeze unavailable
        return self._synthetic_option_score(symbol, spot, atr, rsi)


__all__ = ["OptionScorer", "OptionScore"]
