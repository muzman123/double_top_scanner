# 🎯 Double Top Scanner

> **Professional stock market scanner that detects bearish reversal patterns (double tops) across 250+ stocks with email alerts**

[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![Tests](https://img.shields.io/badge/tests-39%20passing-brightgreen.svg)](tests/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

## 📋 Table of Contents
- [What is a Double Top?](#what-is-a-double-top)
- [Features](#features)
- [Quick Start](#quick-start)
- [Installation](#installation)
- [Configuration](#configuration)
- [Usage](#usage)
- [Test Results](#test-results)
- [How It Works](#how-it-works)
- [Contributing](#contributing)

---

## 🎓 What is a Double Top?

A **double top** is a bearish chart pattern that signals a potential price reversal:

```
Price Chart:
    Peak1      Peak2
      ▲          ▲         <- Resistance Level
      │          │
      │    ╱─────╯
      │   ╱
      │  ╱  Trough
      │ ╱     ▼           <- Neckline
      │╱
      └─────────────────
         Time →
```

**Pattern Characteristics:**
1. **Peak 1**: Price rallies to resistance and gets rejected
2. **Trough**: Price declines 3%+ from peak  
3. **Peak 2**: Price rallies again to same resistance level and fails
4. **Confirmation**: Price breaks below the neckline (trough)

**Trading Signal:** Potential price decline ahead (bearish reversal)

---

## ✨ Features

### 🔮 Dual Detection Modes
- **Prediction Mode**: Early warning alerts BEFORE neckline breaks (catch patterns forming)
- **Detection Mode**: Conservative alerts AFTER neckline breaks (confirmed reversals)

### 🧠 Advanced Pattern Recognition
- **Asymmetric Prominence**: Validates M-shape characteristics
  - Peak 1: Must show 1.5%+ reversal drop on right
  - Peak 2: Must show 1.5%+ rally rise on left
- **RSI Divergence**: Required for confirmation (bearish divergence)
- **Multi-Timeframe Analysis**: Daily, Weekly, Monthly RSI scoring
- **Reversal Confirmation**: Rejects patterns where price rallied back (continuation, not reversal)

### 📧 Smart Notifications
- **Email Alerts**: HTML formatted with pattern details
- **CSV Export**: Full data export for analysis
- **Score-Based Filtering**: Only alerts on high-probability setups (Score ≥3/6)

### 🎛️ Fully Configurable
- All thresholds adjustable via YAML config
- No hardcoded values
- Easy to tune for different strategies

### ✅ Production Ready
- **39 Unit Tests** (100% passing)
- Tested on 250+ stocks
- 7% detection rate on live data
- Error handling and logging

---

## 🚀 Quick Start

### 1. Clone & Setup
```bash
# Clone repository
git clone https://github.com/yourusername/double_top_scanner.git
cd double_top_scanner

# Windows
setup.bat

# Linux/Mac
chmod +x setup.sh
./setup.sh
```

### 2. Configure
```bash
# Copy template
cp config/settings.yaml.template config/settings.yaml

# Edit with your settings
nano config/settings.yaml
```

### 3. Run Scanner
```bash
# Full scan (200 stocks)
python run_scanner.py

# Test mode (100 stocks)
python run_scanner.py --test

# Single symbol
python run_scanner.py --symbol AAPL
```

---

## 📥 Installation

### Prerequisites
- Python 3.8 or higher
- pip package manager
- Internet connection (for market data)

### Automated Setup

**Windows:**
```cmd
setup.bat
```

**Linux/Mac:**
```bash
chmod +x setup.sh
./setup.sh
```

### Manual Installation
```bash
# Create virtual environment
python -m venv venv

# Activate (Windows)
venv\Scripts\activate

# Activate (Linux/Mac)
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Copy config template
cp config/settings.yaml.template config/settings.yaml
```

---

## ⚙️ Configuration

### 1. Copy Template
```bash
cp config/settings.yaml.template config/settings.yaml
```

### 2. Edit Settings

**Pattern Detection:**
```yaml
pattern:
  mode: prediction              # 'prediction' or 'detection'
  min_confidence: 30            # Min pattern quality (0-100)
  min_reversal_drop_pct: 1.5   # Peak 1 reversal signal
  min_rally_rise_pct: 1.5      # Peak 2 rally signal
```

**RSI Requirements:**
```yaml
rsi:
  divergence_min_diff: 0.5      # Min RSI divergence points
  divergence_required: true     # Require RSI divergence
```

**Email Notifications:**
```yaml
notification:
  email_enabled: true
  smtp_host: smtp.gmail.com
  smtp_port: 587
  smtp_username: your-email@gmail.com
  smtp_password: your-app-password  # Use Gmail App Password
  email_to: your-email@gmail.com
```

**Asset Selection:**
```yaml
assets:
  max_assets_to_scan: 200       # Limit scan size
```

### 3. Gmail App Password Setup

1. Go to Google Account Settings
2. Security → 2-Step Verification (enable if not enabled)
3. Security → App Passwords
4. Generate new app password for "Mail"
5. Copy 16-character password to `smtp_password` in config

---

## 🎮 Usage

### Basic Commands

```bash
# Full scan with email alerts
python run_scanner.py

# Test mode (100 stocks, faster)
python run_scanner.py --test

# Scan specific symbol
python run_scanner.py --symbol TSLA

# Generate chart for pattern
python verify_results.py INTC --plot
```

### Output Examples

**Console Output:**
```
⚠️ INTC: Score 4/6, Status: FORMING, Confidence 66%
  Peak 1: $39.65 on 2025-10-10
  Peak 2: $38.52 on 2025-10-20
  Neckline: $34.69 ← WATCH FOR BREAK!
```

**Email Alert:**
- HTML table with all patterns
- Scores, RSI values, divergence indicators
- Links to Yahoo Finance charts
- CSV attachment with full details

**CSV Export:**
- `output/alerts_YYYY-MM-DD.csv`
- All pattern metrics and timestamps
- Ready for spreadsheet analysis

---

## 📊 Test Results

### Unit Tests (39 tests, 100% passing)

Run tests:
```bash
python -m pytest tests/test_pattern_detector.py -v
```

**Test Coverage:**
```
✅ RSI Calculation       (4 tests) - Formula accuracy, overbought/oversold
✅ Peak Detection        (4 tests) - Single/multiple peaks, recent peaks
✅ Asymmetric Prominence (3 tests) - M-shape validation
✅ Price Tolerance       (3 tests) - 3% similarity, uptrend rejection
✅ Trough Depth          (2 tests) - Minimum depth validation
✅ Distance Requirements (3 tests) - Min 8 bars between peaks
✅ RSI Divergence        (2 tests) - Divergence detection
✅ Scoring System        (2 tests) - Quality scoring
✅ Pattern Detection     (4 tests) - Complete patterns, edge cases
✅ Mode Behavior         (2 tests) - Prediction vs detection
✅ Edge Cases            (4 tests) - Volatility, missing data
✅ Neckline Break        (2 tests) - Confirmation validation
✅ Integration           (4 tests) - End-to-end flows
```

### Production Scan Results

**Test Scan:** 100 S&P 500 stocks in 80 seconds
**Patterns Found:** 5 (7% detection rate)

| Symbol | Score | Confidence | Status | Notes |
|--------|-------|------------|--------|-------|
| GS | 4/6 | 63% | FORMING | Best candidate |
| ETN | 3/6 | 63% | FORMING | Strong pattern |
| ADI | 3/6 | 55% | FORMING | Watch closely |
| CMG | 3/6 | 50% | FORMING | Marginal |
| INTC | 3/6 | 30% | FORMING | Low confidence |

---

## 🔬 How It Works

### Detection Algorithm

1. **Fetch Data**: OHLCV data for 4h, daily, weekly, monthly timeframes
2. **Find Peaks**: Asymmetric prominence detection
3. **Validate Pattern**:
   - Time spacing (8-67 bars)
   - Price similarity (within 3%)
   - Trough depth (≥3%)
   - M-shape structure
   - Asymmetric prominence
4. **Mode Check**:
   - Prediction: Recent peak (≤50 bars), price declining
   - Detection: Neckline break confirmed
5. **RSI Analysis**:
   - Calculate RSI for all timeframes
   - Check for bearish divergence (≥0.5 points)
6. **Scoring** (0-6 points):
   - +1: Pattern detected
   - +1: RSI divergence present
   - +1: Daily RSI >70 (overbought)
   - +1: Weekly RSI >70
   - +1: Monthly RSI >70
   - +1: Volume decline ≥20%
7. **Alert**: If score ≥3, send notification

### Prediction vs Detection Modes

| Feature | Prediction Mode | Detection Mode |
|---------|----------------|----------------|
| **Alert Timing** | At Peak 2 formation | After neckline break |
| **Neckline Break** | NOT required ⚠️ | Required ✓ |
| **Peak Recency** | ≤50 bars (configurable) | No limit |
| **Price Check** | Must be 2%+ below Peak 2 | Must break neckline |
| **Risk/Reward** | Earlier entry, higher risk | Confirmed signal, lower risk |

---

## 🛠️ Development

### Project Structure
```
src/
├── pattern_detector.py    # Core pattern detection logic
├── scanner.py             # Orchestrates scanning workflow
├── indicators.py          # RSI and technical indicators
├── data_fetcher.py        # Fetch market data (yfinance)
└── notifier.py            # Email/CSV notifications

config/
├── settings.yaml.template # Configuration template (COPY THIS)
└── asset_universe.json    # 250+ stocks to scan

tests/
├── test_pattern_detector.py  # 39 comprehensive tests
└── test_indicators.py         # RSI tests
```

### Running Tests
```bash
# All tests
python -m pytest tests/ -v

# Specific test file
python -m pytest tests/test_pattern_detector.py -v

# With coverage
python -m pytest tests/ --cov=src --cov-report=html
```

### Adding New Stocks
Edit `config/asset_universe.json`:
```json
{
  "stocks": [
    "AAPL", "MSFT", "GOOGL",  // Add your symbols here
    ...
  ]
}
```

---

## 📖 Documentation

- [**PREDICTION_MODE.md**](PREDICTION_MODE.md) - Mode comparison & guide
- [**PATTERN_DETECTION_EXPLAINED.md**](PATTERN_DETECTION_EXPLAINED.md) - Algorithm deep dive
- [**BUGFIX_SUMMARY.md**](BUGFIX_SUMMARY.md) - All bugs fixed
- [**VERIFICATION_GUIDE.md**](VERIFICATION_GUIDE.md) - Chart visualization

---

## 🤝 Contributing

Contributions welcome! Please:
1. Fork the repository
2. Create a feature branch
3. Add tests for new features
4. Ensure all tests pass
5. Submit a pull request

---

## 📝 License

MIT License - see LICENSE file for details

---

## ⚠️ Disclaimer

This software is for **educational and informational purposes only**. 

- NOT financial advice
- NOT a recommendation to buy/sell securities
- Trading involves risk of loss
- Always do your own research
- Test thoroughly before live trading

**Use at your own risk. Past performance does not guarantee future results.**

---

## 💬 Support

- **Issues**: [GitHub Issues](https://github.com/yourusername/double_top_scanner/issues)
- **Discussions**: [GitHub Discussions](https://github.com/yourusername/double_top_scanner/discussions)

---

## 🙏 Acknowledgments

- **yfinance** - Market data provider
- **pandas** - Data manipulation
- **scipy** - Signal processing for peak detection

---

**Happy Pattern Hunting! 📈📉**