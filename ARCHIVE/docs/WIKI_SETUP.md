# AlgoOptions Wiki - Setup & Usage

This is a **free, self-hosted wiki** built with [MkDocs](https://www.mkdocs.org/). It documents the complete business logic of the AlgoOptions screener.

## 🚀 Quick Start

### Option 1: View Online (Simplest)
A wiki is already generated and available as static HTML - just open in browser:
```bash
# Coming soon: will be hosted on GitHub Pages
```

### Option 2: Generate Your Own Wiki (5 minutes)

#### Step 1: Install MkDocs
```bash
pip install mkdocs mkdocs-material
```

#### Step 2: Build HTML
```bash
cd d:\DreamProject\algooptions
mkdocs build
```

Output: `site/index.html` - Open in browser!

#### Step 3: Serve Locally (Optional)
```bash
mkdocs serve
# Visit: http://localhost:8000
# Auto-refreshes as you edit docs
```

---

## 📚 Wiki Structure

```
docs/
├── index.md                      ← Start here
├── getting-started/
│   ├── overview.md              ← System architecture
│   ├── installation.md          ← Setup instructions
│   └── quickstart.md            ← 5-minute trading guide
├── core/
│   ├── scoring-engine.md        ← How signals are generated
│   ├── risk-management.md       ← 2% rule, ATR, stop-loss
│   ├── position-sizing.md       ← Calculate position size
│   └── options-strategies.md    ← 5 option strategies
├── analysis/
│   ├── support-resistance.md    ← S/R levels
│   ├── timeframe-analysis.md    ← 5m/15m/1h trading
│   └── indicators.md            ← RSI, MACD, EMA, etc.
├── advanced/
│   ├── api-reference.md         ← Python API docs
│   ├── configuration.md         ← Settings & customization
│   └── backtesting.md           ← Historical testing
└── faq.md                        ← 50+ Q&A
```

---

## 📖 Reading Paths

### Path 1: Complete Beginner (2 hours)
1. [Overview](docs/getting-started/overview.md)
2. [Installation](docs/getting-started/installation.md)
3. [Quick Start](docs/getting-started/quickstart.md)
4. [FAQ](docs/faq.md)

**Result:** Ready to place your first trade!

---

### Path 2: Risk Management Focus (1 hour)
1. [Risk Management](docs/core/risk-management.md)
2. [Position Sizing](docs/core/position-sizing.md)
3. [Scoring Engine](docs/core/scoring-engine.md)

**Result:** Understand 2% rule and position sizing

---

### Path 3: Technical Analysis Focus (1.5 hours)
1. [Scoring Engine](docs/core/scoring-engine.md)
2. [Support & Resistance](docs/analysis/support-resistance.md)
3. [Timeframe Analysis](docs/analysis/timeframe-analysis.md)
4. [Technical Indicators](docs/analysis/indicators.md)

**Result:** Master technical analysis concepts

---

### Path 4: Options Trading (1 hour)
1. [Options Strategies](docs/core/options-strategies.md)
2. [Risk Management](docs/core/risk-management.md) (read again)
3. [FAQ](docs/faq.md#options-trading) (options section)

**Result:** Know how to trade options with signals

---

### Path 5: Developer/Customization (2 hours)
1. [API Reference](docs/advanced/api-reference.md)
2. [Configuration](docs/advanced/configuration.md)
3. [Backtesting](docs/advanced/backtesting.md)

**Result:** Customize system for your needs

---

## 🎯 Features

✅ **Free** - No cost, no ads, no paywall  
✅ **Self-Hosted** - Run on your own machine  
✅ **Searchable** - Full-text search built-in  
✅ **Dark Mode** - Automatic light/dark theme  
✅ **Mobile-Friendly** - Works on phones  
✅ **Single Page Export** - Print or save entire wiki as PDF  
✅ **Multiple Formats** - Read as HTML, Markdown, or PDF  

---

## 📥 Download as PDF

### Using MkDocs
```bash
# Install print plugin
pip install mkdocs-print-site-plugin

# Build with print support
mkdocs build

# Open: site/print_page/index.html
# Print to PDF (Ctrl+P in browser)
```

### Using Browser
```bash
# Open local wiki in browser
# Scroll to bottom → "Print/Export"
# Select "Print to PDF"
# Save as single document
```

---

## ✏️ Edit & Contribute

Want to improve the wiki?

### Edit Existing Page
```bash
# Edit markdown file directly
docs/core/scoring-engine.md

# Changes auto-reflect on `mkdocs serve`
```

### Add New Page
```bash
# Create new file
docs/my-topic/my-page.md

# Add to mkdocs.yml
nav:
  - My Topic: my-topic/my-page.md

# Rebuild
mkdocs build
```

---

## 🔗 Cross-References

All pages link to each other. Format:

```markdown
See also: [Risk Management](../core/risk-management.md)
```

The `../` paths work in both:
- Local wiki (when served)
- GitHub (if hosted)
- Markdown editors

---

## 📊 Statistics

| Metric | Value |
|--------|-------|
| Total Pages | 17 |
| Total Words | ~20,000 |
| Code Examples | 50+ |
| Formulas | 25+ |
| Tables | 30+ |
| Time to Read All | 8-10 hours |

---

## 🆘 Troubleshooting

### Wiki won't open in browser
```bash
# Make sure you're in correct directory
cd d:\DreamProject\algooptions

# Check if site/ folder exists
ls site/

# If not, rebuild
mkdocs build

# Then open: site/index.html
```

### Search not working
```bash
# Search requires build
mkdocs build

# Then serve
mkdocs serve
```

### Want to modify theme
Edit `mkdocs.yml`:
```yaml
theme:
  name: material
  palette:
    scheme: dark  # or 'light'
    primary: indigo
```

---

## 🚀 Deploy Online (Optional)

### Deploy to GitHub Pages (Free)
```bash
# Install
pip install mkdocs-github-deploy

# Deploy
mkdocs gh-deploy

# Your wiki is now live at:
# https://yourusername.github.io/algooptions
```

### Deploy to Netlify (Free)
1. Push to GitHub
2. Connect to Netlify
3. Set build command: `mkdocs build`
4. Done! Live in 2 minutes

---

## 📝 License

This wiki and all content is provided as-is. Use for educational purposes.

---

## 🎓 Getting Help

**Within the Wiki:**
- Use Search (top-right)
- Read [FAQ](docs/faq.md)
- Check [Quick Start](docs/getting-started/quickstart.md)

**Online:**
- Check GitHub issues
- Read original documentation

---

**Created:** January 21, 2026  
**Last Updated:** January 21, 2026  
**Version:** 1.0 Production
