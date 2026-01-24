# Position Sizing

## Core Principle

**Every trade must risk exactly 2% of capital** - no more, no less.

This ensures that 50 consecutive losses won't deplete your account (statistically impossible to have 50 losses in a row with a >50% win rate).

## The 2% Rule Explained

```
Account Size: ₹1,00,000
Max Risk per Trade: 2% = ₹2,000

If you lose 20 trades in a row:
- Loss = 20 × 2% = 40%
- Remaining = ₹60,000

You can still trade and recover.
```

## Position Sizing Formula

### Step 1: Calculate Your Risk Amount
```
Risk Amount = Total Capital × Risk %
            = ₹1,00,000 × 0.02
            = ₹2,000
```

### Step 2: Calculate Risk per Share
```
Risk per Share = Entry Price - Stop Loss
               = ₹100 - ₹95
               = ₹5
```

### Step 3: Calculate Position Size
```
Position Size = Risk Amount / Risk per Share
              = ₹2,000 / ₹5
              = 400 shares
```

### Step 4: Verify Maximum Loss
```
Max Loss = Position Size × Risk per Share
         = 400 × ₹5
         = ₹2,000 ✓ (Equals 2% of capital)
```

## Practical Examples

### Example 1: High-Confidence, Low-Risk Trade

```
Capital: ₹50,000
Entry: HDFC @ ₹1,500
Stop Loss: ₹1,475 (ATR-based)
Risk per share: ₹25

Position = (50,000 × 0.02) / 25
         = 1,000 / 25
         = 40 shares

Max loss: 40 × 25 = ₹1,000 ✓
```

### Example 2: Volatile Stock, Must Adjust

```
Capital: ₹50,000
Entry: ADANIGREEN @ ₹1,500
Volatility: 6% (HIGH RISK)
ATR-based SL: ₹1,350 (₹150 risk per share)

Standard calc = 1,000 / 150 = 6.67 shares
⚠️ Risk adjustment = 50% for HIGH volatility
Adjusted: 6.67 × 0.5 = 3.3 ≈ 3 shares

Max loss: 3 × 150 = ₹450 (0.9% risk) ✓
```

## Position Size Brackets

Based on your account size:

| Account Size | Max Risk per Trade | Typical Position |
|--------------|-------------------|-----------------|
| ₹25,000      | ₹500              | 5-20 shares (depending on price) |
| ₹50,000      | ₹1,000            | 10-50 shares |
| ₹1,00,000    | ₹2,000            | 20-100 shares |
| ₹5,00,000    | ₹10,000           | 100-500 shares |
| ₹10,00,000   | ₹20,000           | 200-1000 shares |

## Special Adjustments

### 1. Earnings Announcement Risk
If earnings are announced within next 3 days:
```
Position = Standard Position × 0.5  (50% reduction)

Why? IV increases dramatically, wider stops required.
```

### 2. Support/Resistance Entries

#### Entry at Support (for Long)
```
Position = Standard Position × 1.1  (10% increase)

Why? Support = high probability, tighter stop possible
```

#### Entry at Resistance (for Short)
```
Position = Standard Position × 1.1  (10% increase)

Why? Resistance = high probability, tighter stop possible
```

### 3. Trending vs Ranging Market

#### Strong Uptrend
```
Position = Standard Position × 1.15  (15% increase)

Why? Trend has momentum, higher probability
```

#### Sideways/Ranging Market
```
Position = Standard Position × 0.85  (15% reduction)

Why? Limited move potential, chop kills profits
```

## Options Position Sizing

For **option strategies**, we calculate differently:

### Single Options (Long Call/Put)
```
Premium Cost = ₹5 per share
Capital at Risk = Premium × 100 shares
Contracts = 2% Risk / Premium Cost

Example:
- 2% of ₹1,00,000 = ₹2,000
- INFY Call Premium = ₹50
- Contracts = 2,000 / 5,000 = 0.4 contracts ≈ Skip or use 1 with reduced capital

Recommended: Use ≤ 1% for options until skilled
```

### Spread Strategies (Credit/Debit Spreads)
```
Max Loss per Spread = Width × 100 (for 1 contract)

Example: SPX Put Spread
- Short ₹100 strike, Long ₹95 strike
- Max Loss = (100-95) × 100 = ₹500

Contracts = (2% of capital) / Max Loss
          = 2,000 / 500
          = 4 contracts
```

## Kelly Criterion (Advanced)

For traders with enough historical data:

```
Kelly % = (Win% × AvgWin - Loss% × AvgLoss) / AvgWin

Example:
- Historical Win Rate: 55%
- Avg Win: ₹5,000
- Avg Loss: ₹3,000

Kelly % = (0.55 × 5,000 - 0.45 × 3,000) / 5,000
        = (2,750 - 1,350) / 5,000
        = 1,400 / 5,000
        = 0.28 = 28%

⚠️ Use 1/4 Kelly = 7% for safety
Position = 0.07 × Capital / Risk per Share
```

## Compounding & Scaling

As you grow your capital, position size grows:

```
Month 1: Start with ₹1,00,000
         Position = 2% of capital = ₹2,000 risk per trade

After winning streak: ₹1,25,000
                      New position = 2% × 1,25,000 = ₹2,500

After lucky month: ₹1,50,000
                   New position = 2% × 1,50,000 = ₹3,000
```

This is **compound growth** - your positions grow with your account.

---

See also: [Risk Management](risk-management.md), [Options Strategies](options-strategies.md)
