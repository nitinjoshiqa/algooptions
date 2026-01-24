# ARCHIVE - Historical Files & Deprecated Code

This directory contains files that were either:
- **Deprecated:** Superseded by newer implementations
- **Experimental:** Test versions or prototypes
- **Historical:** Documentation from earlier project phases

---

## 📂 Directory Structure

```
ARCHIVE/
├── scripts/           # 18 deprecated Python scripts
├── constituents/      # 10 old stock list versions
├── docs/              # 39 archived documentation files
└── README.md          # This file
```

---

## 📜 Archived Python Scripts (18 files)

These were build/test scripts from development phases. **Do not use in production.**

### Market Cap Research Scripts
- `build_nifty500_220plus.py` - Expanded list to 220+ (superseded)
- `build_nifty500_220_final.py` - Final 220 list attempt
- `build_nifty500_expanded_220.py` - Another 220 variant
- `comprehensive_15b_test.py` - Market cap threshold testing
- `test_15b_threshold.py` - Another 15B threshold test
- `fetch_top_200_stocks.py` - Top 200 by market cap
- `fetch_top_stocks_by_market_cap.py` - Stock fetcher by cap

### Diagnostic & Debug Scripts
- `analyze_missing_stocks.py` - Debug missing symbols
- `debug_breeze_response.py` - Breeze API debugging
- `diagnose_missing_stocks.py` - Another missing stock analyzer
- `test_breeze_api.py` - Breeze Connect API test
- `test_cache_system.py` - Cache system validation

### Data/Validation Scripts
- `clean_constituents.py` - Old cleanup script
- `create_final_nifty200_list.py` - NIFTY200 list creator
- `expand_to_220.py` - Expansion to 220 stocks
- `find_stable_stocks.py` - Stock stability analyzer
- `validate_nifty500.py` - NIFTY500 validator

### Final Report Generators
- `final_screener_report_220.py` - Old report generator

---

## 📋 Archived Constituent Files (10 files)

Old versions of stock lists. Use only **active versions**:

### Active (Use These)
- `../nifty500_constituents.txt` - **179 validated stocks** ✅
- `../nifty200_constituents.txt` - Top 200 stocks ✅

### Archived (Historical Only)
- `nifty500_constituents_220plus.txt` - Old 220+ attempt (had duplicates)
- `nifty500_constituents_final_220.txt` - Another 220 variant
- `nifty500_validated_stocks.txt` - Older validation list
- `nifty200_constituents_old.txt` - Old NIFTY200 version
- `nifty200_updated_constituents.txt` - Intermediate version
- `nifty_200_updated_constituents.txt` - Typo variant
- `top_stocks_symbols.txt` - Experiment file
- `test_mini_universe.txt` - Small test universe
- `test_ns_symbols.txt` - NS suffix test file
- `skipped_symbols.txt` - Symbols that failed validation

**Why archived?**
- Contained duplicates (228 symbols → 179 unique)
- Symbols lacked `.NS` suffix (now fixed in active version)
- Superseded by cleaned, validated constituent file

---

## 📚 Archived Documentation (39 files)

Consolidated into **[WIKI.md](../WIKI.md)** and **[ARCHITECTURE.md](../ARCHITECTURE.md)**

### Strategy Documentation (7 files)
- `OPTION_SELLING_BASICS.md` through `OPTION_SELLING_THETA_DECAY_RISKS.md` (5 files)
- `STRATEGY_OPTION_SELLING_BASICS.md` (2 files)
- `THETA_DECAY_*.md` (5 files total)

**Consolidated into:** [WIKI.md > Scoring Modes & Configuration](../WIKI.md#scoring-modes-and-configuration)

### Setup & Automation Docs (5 files)
- `AUTOMATION_GUIDE.md` - Scheduler setup
- `AUTOMATION_QUICKSTART.md` - Quick automation
- `BREEZE_CONNECT_API_GUIDE.md` - Breeze API
- `BREEZE_CONNECT_SETUP.md` - Breeze setup
- `CACHING_STRATEGY.md` - Caching explanation

**Consolidated into:** [WIKI.md > API Integration](../WIKI.md#api-integration)

### Troubleshooting & Data Docs (8 files)
- `DATA_STALENESS_IN_INDICATORS.md` - Data freshness
- `DATA_STALENESS_RISKS.md` - Staleness risks
- `HOW_CACHE_WORKS.md` - Cache mechanism
- `HOW_FETCHER_WORKS.md` - Data fetching
- `HOW_INDICATORS_WORK.md` - Indicator calculation
- `HOW_SCORING_WORKS.md` - Scoring algorithm
- `SIGNAL_GENERATION_BRIEF.md` - Signal logic
- `STALENESS_vs_PERFORMANCE_TRADEOFF.md` - Tradeoff analysis

**Consolidated into:** [WIKI.md > Troubleshooting Guide](../WIKI.md#troubleshooting-guide) & [ARCHITECTURE.md](../ARCHITECTURE.md)

### Implementation & Status (7 files)
- `IMPLEMENTATION_COMPLETE.md`
- `IMPLEMENTATION_STATUS_FINAL.md`
- `IMPLEMENTATION_SUMMARY.md`
- `IMPROVEMENTS_QUICK_REF.md`
- `IMPROVEMENTS_SUMMARY.md`
- `FINAL_SUMMARY.md`
- `00_READ_ME_FIRST_IMPLEMENTATION_COMPLETE.md`

**Consolidated into:** [README.md](../README.md) status section

### Process & Reporting Docs (7 files)
- `CRITICAL_BACKTEST_ISSUE.md`
- `REMAINING_BUGS_ANALYSIS.md`
- `SCORING_BUGS_FOUND.md`
- `SCORING_ENGINE_ANALYSIS.md`
- `BACKTEST_ACTUAL_LOGIC_ANALYSIS.md`
- `BACKTEST_ANALYSIS_3MONTH.md`
- `HTML_REPORT_STRUCTURE.md`

**Consolidated into:** [ARCHITECTURE.md](../ARCHITECTURE.md) & [WIKI.md](../WIKI.md)

### Quick Reference Docs (5 files)
- `OPTION_INTELLIGENCE_GUIDE.md`
- `QUICKSTART_ALL_TIERS.md`
- `SCORING_DOCUMENTATION_MAP.md`
- `DEPLOYMENT_CHECKLIST.md`
- `README_*.md` (multiple variants)

**Consolidated into:** [README.md](../README.md) & [WIKI.md](../WIKI.md)

---

## 🔄 Why Files Were Archived

### Problem: Duplicate Documentation
- **Before:** 39 scattered markdown files with overlapping content
- **Solution:** Consolidated into 2 authoritative documents:
  - **[WIKI.md](../WIKI.md)** - Feature reference (16 sections)
  - **[ARCHITECTURE.md](../ARCHITECTURE.md)** - System design

### Problem: Experimental Scripts
- **Before:** 18 build/test scripts from development phases
- **Solution:** Archived experimental code, kept only production files:
  - `nifty_bearnness_v2.py` - Main screener ✅
  - `wait_strategy.py` - Rate limiting ✅
  - `config_manager.py` - Settings ✅

### Problem: Outdated Constituent Lists
- **Before:** 10 versions with duplicates and format issues (228 symbols)
- **Solution:** Single validated list (179 symbols, all with `.NS` suffix)

---

## 📖 How to Use ARCHIVE

### Finding Historical Info
```
Q: "What was the old symbol format issue?"
A: See ARCHIVE/docs/BACKTEST_ACTUAL_LOGIC_ANALYSIS.md

Q: "How did the 220+ expansion work?"
A: See ARCHIVE/scripts/build_nifty500_220_final.py
```

### Learning from Experiments
```
Q: "What was tried for Breeze integration?"
A: See ARCHIVE/scripts/test_breeze_api.py
   and ARCHIVE/docs/BREEZE_CONNECT_SETUP.md
```

### Understanding Project Evolution
1. **Phase 1:** Initial screener development
2. **Phase 2:** Expansion to 220+ stocks (ARCHIVE/scripts/)
3. **Phase 3:** Symbol format fixes (ARCHIVE/docs/)
4. **Phase 4:** Rate limiting implementation
5. **Phase 5:** Documentation consolidation (→ WIKI.md, ARCHITECTURE.md)

---

## ⚠️ Important Notes

- **Do NOT use archived scripts in production**
- **Do NOT edit archived files** (they're historical snapshots)
- **Use README.md → WIKI.md → ARCHITECTURE.md for current info**
- **If you need old code:** Check here first, then ask about restoration

---

## 📊 Cleanup Summary

| Category | Before | After | Status |
|----------|--------|-------|--------|
| Python Scripts | 30+ | 3 core files | ✅ Archived 18 |
| Constituent Files | 10 versions | 2 active | ✅ Archived 10 |
| Documentation | 39 scattered docs | 2 consolidated | ✅ Archived 39 |
| **Total** | **80+ files** | **Clean & organized** | ✅ **Complete** |

---

**Archive Created:** January 23, 2026  
**Total Archived Files:** 67  
**Cleanup Status:** ✅ Complete  
**Next Action:** Review [README.md](../README.md) → [WIKI.md](../WIKI.md) → [ARCHITECTURE.md](../ARCHITECTURE.md)
