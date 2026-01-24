# Contributing to NIFTY Bearnness Screener

Thank you for interest in contributing! This document outlines guidelines and process.

## Code of Conduct

- Be respectful and constructive
- Focus on code quality and user experience
- No harassment or discriminatory language

## How to Contribute

### 1. Report Issues
```
Describe what went wrong with:
- Python version (python --version)
- Command you ran
- Full error message
- Steps to reproduce
```

### 2. Suggest Features
```
Explain:
- What feature you want
- Why it's useful
- Example use case
```

### 3. Submit Code

```bash
# Clone your fork
git clone https://github.com/YOUR_USERNAME/algooptions.git
cd algooptions

# Create feature branch
git checkout -b feature/your-feature-name

# Make changes
# Test thoroughly
python nifty_bearnness_v2.py --universe banknifty --quick

# Commit with clear messages
git commit -m "Add feature: description of what you did"

# Push to your fork
git push origin feature/your-feature-name

# Create Pull Request on GitHub
```

## Code Standards

### Python Style
- Follow PEP 8
- Use type hints where possible
- Write docstrings for functions

```python
def score_stock(symbol: str, mode: str = 'swing') -> dict:
    """
    Calculate bearness score for a stock.
    
    Args:
        symbol: Stock ticker (e.g., 'HDFC')
        mode: Analysis mode ('intraday', 'swing', 'position')
    
    Returns:
        Dictionary with 'score' and 'confidence' keys
    """
    pass
```

### Testing
```bash
# Run existing tests
python -m pytest tests/ -v

# Test your specific feature
python -c "from core.your_module import your_function; print(your_function())"
```

### Documentation
- Update docs/ if adding features
- Add examples in docstrings
- Keep README.md accurate

## Areas We Need Help With

### High Priority
- [ ] More data sources (NSEPython, Blinkx, etc.)
- [ ] Backtesting engine enhancements
- [ ] More option strategies
- [ ] Better error messages

### Medium Priority
- [ ] Docker containerization
- [ ] Cloud deployment guide (AWS, GCP, Azure)
- [ ] Trading bot integration
- [ ] Real-time alerts

### Documentation
- [ ] Video tutorials
- [ ] Interactive examples
- [ ] Strategy guides
- [ ] API documentation

## Questions?

- Check [PRODUCTION_GUIDE.md](../PRODUCTION_GUIDE.md)
- Review [ARCHITECTURE.md](../ARCHITECTURE.md)
- Open an issue with the question label

---

## Thank You!

Your contributions make this project better. We appreciate your time and effort! 🙏
