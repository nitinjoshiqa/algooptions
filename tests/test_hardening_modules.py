import sys
sys.path.insert(0, '.')

# Test all new hardening modules
from core.context_engine import compute_context_score, get_context_tier
from core.robustness_engine import validate_robustness, get_robustness_score
from core.special_days_detector import get_special_day_type
from core.trade_learner import get_trade_logger

tests_passed = 0

try:
    ctx_score, ctx_mom = compute_context_score({'vwap_score': 0.5})
    print(f'✓ Context module: score={ctx_score:.2f}, momentum={ctx_mom:+.2f}')
    tests_passed += 1
except Exception as e:
    print(f'✗ Context module: {e}')

try:
    rob_filters = validate_robustness({'adx': 28, 'market_regime': 'TRENDING'})
    rob_score = get_robustness_score(rob_filters)
    filters_passed = sum(1 for f in rob_filters.values() if f.get('pass'))
    print(f'✓ Robustness module: {filters_passed} filters passed, score={rob_score:.1f}')
    tests_passed += 1
except Exception as e:
    print(f'✗ Robustness module: {e}')

try:
    from datetime import datetime
    day_type = get_special_day_type(datetime.now().date())
    print(f'✓ Special days module: today is {day_type}')
    tests_passed += 1
except Exception as e:
    print(f'✗ Special days module: {e}')

try:
    logger = get_trade_logger()
    print(f'✓ Trade logger module: ready')
    tests_passed += 1
except Exception as e:
    print(f'✗ Trade logger module: {e}')

print(f'\n✅ {tests_passed}/4 modules verified successfully!')
