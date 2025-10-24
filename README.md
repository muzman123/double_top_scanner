# Double Top Scanner

Automated daily morning alert system that identifies potential double/triple top reversal patterns combined with multi-timeframe RSI overbought conditions across stocks, indices, and commodities.

## 🎯 Features

- Scans ~520 assets daily (S&P 500 stocks, 10 indices, 3 commodities)
- Detects double top patterns with configurable parameters
- Multi-timeframe RSI analysis (4h, Daily, Weekly, Monthly)
- RSI divergence detection
- Scoring system (0-6 points) to prioritize opportunities
- Daily email alerts with CSV export
- Automated scheduling support

## 📋 Requirements

- Python 3.9+
- Internet connection for data fetching
- Email account for notifications (optional)

## 🚀 Quick Start

### 1. Installation

```bash
# Clone or download the project
cd double_top_scanner

# Create virtual environment (recommended)
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Configuration

Edit `config/settings.yaml` to customize:
- Pattern detection parameters
- RSI thresholds
- Email settings
- Data source

Create `.env` file for sensitive data:
```bash
SMTP_USERNAME=your_email@gmail.com
SMTP_PASSWORD=your_app_password
POLYGON_API_KEY=your_polygon_key  # If using Polygon.io
```

### 3. Test Run

```bash
# Test with just 5 symbols
python run_scanner.py --test

# Scan single symbol
python run_scanner.py --symbol AAPL

# Full scan
python run_scanner.py
```

## 📊 How It Works

### Pattern Detection

The scanner looks for **double top patterns** with these criteria:

1. **Two peaks** at similar price levels (within 3% tolerance)
2. **Minimum 8 candles** between peaks
3. **Trough drops 3%+** below peaks
4. **RSI divergence**: Price makes similar high, but RSI goes lower

### Scoring System (0-6 Points)

| Points | Criteria |
|--------|----------|
| +1 | Double top pattern detected |
| +1 | RSI bearish divergence (Peak1 RSI > Peak2 RSI by ≥2 points) |
| +1 | Daily RSI > 70 |
| +1 | Weekly RSI > 70 |
| +1 | Monthly RSI > 70 |
| +1 | Volume decline (Peak2 < Peak1 by 20%+) |

**Score Interpretation:**
- 6 points = PREMIUM (highest priority)
- 5 points = HIGH Quality
- 4 points = GOOD Quality
- 3 points = WATCHLIST
- <3 points = Not reported

### Example: Gold Pattern (6/6 Score)

```
Peak 1 & 2: ~$2,790 level (0.2% difference) 
Distance: 10 candles apart 
Trough: $2,670 (4.3% decline) 
RSI Divergence: Peak1 RSI > Peak2 RSI 
Daily RSI > 70 
Weekly RSI > 70 
Monthly RSI > 70 
```

## 📁 Project Structure

```
double_top_scanner/
├── config/
│   ├── settings.yaml              # Main configuration
│   └── asset_universe.json        # List of symbols to scan
├── src/
│   ├── data_fetcher.py           # Data retrieval (yfinance/Polygon/IBKR)
│   ├── indicators.py             # RSI and technical indicators
│   ├── pattern_detector.py       # Double top detection logic
│   ├── scanner.py                # Main scanning orchestration
│   └── notifier.py               # Email and CSV output
├── output/
│   ├── alerts_YYYY-MM-DD.csv     # Daily results (auto-generated)
│   └── logs/                     # Log files
├── tests/                        # Unit tests
├── requirements.txt              # Python dependencies
├── run_scanner.py                # Main entry point
└── README.md                     # This file
```

## ⚙️ Configuration Guide

### Pattern Parameters

```yaml
pattern:
  price_tolerance_pct: 3.0          # Max price diff between peaks (%)
  min_candle_distance: 8            # Min candles between peaks
  trough_depth_pct: 3.0             # Min trough depth (%)
  lookback_candles: 100             # How far back to look
```

### Data Source Options

**Option 1: yfinance (Free)**
```yaml
data:
  source: 'yfinance'
  primary_timeframe: '1d'  # Note: 4h not available for stocks
```

**Option 2: Polygon.io ($199/month)**
```yaml
data:
  source: 'polygon'
  primary_timeframe: '4h'  # 4h available
  polygon_api_key: ''      # Set in .env file
```

**Option 3: Interactive Brokers (Free with account)**
```yaml
data:
  source: 'ibkr'
  ibkr_host: '127.0.0.1'
  ibkr_port: 7497
```

### Email Configuration

For Gmail:
1. Enable 2-factor authentication
2. Generate App Password: https://myaccount.google.com/apppasswords
3. Set environment variables:

```bash
export SMTP_USERNAME=your_email@gmail.com
export SMTP_PASSWORD=your_app_password
```

## 🕐 Automated Scheduling

### Linux/Mac (cron)

```bash
# Edit crontab
crontab -e

# Add this line (runs at 8:00 AM CET, Monday-Friday)
0 8 * * 1-5 cd /path/to/double_top_scanner && /path/to/venv/bin/python run_scanner.py
```

### Windows (Task Scheduler)

1. Open Task Scheduler
2. Create Basic Task
3. Trigger: Daily at 08:00
4. Action: Start Program
   - Program: `C:\path\to\venv\Scripts\python.exe`
   - Arguments: `run_scanner.py`
   - Start in: `C:\path\to\double_top_scanner`

### Python APScheduler (Alternative)

Enable in `config/settings.yaml`:
```yaml
schedule:
  enabled: true
  run_time: "08:00"
  timezone: "Europe/Berlin"
```

Then run continuously:
```bash
python -c "from src.scheduler import start_scheduler; start_scheduler()"
```

## 📧 Output Examples

### Console Output

```
================================================================================
DOUBLE TOP SCANNER RESULTS - 2025-10-22 08:00
================================================================================

PREMIUM CANDIDATES (Score 6/6): 2
--------------------------------------------------------------------------------
AAPL     | $175.23  | Peak1: $178.45 | Peak2: $177.89 | Trough:  3.6% | RSI: 73.5 | Div: 
GC=F     | $2785.50 | Peak1: $2790.00| Peak2: $2785.00| Trough:  4.3% | RSI: 76.2 | Div: 

HIGH-QUALITY CANDIDATES (Score 5/6): 5
...
```

### CSV Output

File: `output/alerts_2025-10-22.csv`

Columns include:
- Date, Symbol, Asset_Type, Score
- Current_Price, Price_Change_Pct
- Peak1_Price, Peak1_Time, Peak2_Price, Peak2_Time
- Trough_Price, Trough_Depth_Pct
- RSI values (4h, Daily, Weekly, Monthly)
- Volume data
- Chart_Link

## 🧪 Testing

### Run Tests

```bash
# Run all tests
pytest tests/

# Run specific test
pytest tests/test_indicators.py

# With coverage
pytest --cov=src tests/
```

### Manual Testing

Test individual components:

```bash
# Test RSI calculation
python src/indicators.py

# Test pattern detector
python src/pattern_detector.py

# Test data fetcher
python src/data_fetcher.py

# Test scanner
python src/scanner.py
```

## 🐛 Troubleshooting

### "No data returned for symbol"
- Check internet connection
- Verify symbol is correct (use Yahoo Finance format)
- Some symbols may not have data for all timeframes

### "SMTP authentication failed"
- Verify email/password are correct
- For Gmail, use App Password, not regular password
- Check 2FA is enabled

### "Rate limit exceeded"
- yfinance has rate limits; add delays in config
- Consider upgrading to Polygon.io for higher limits
- For IBKR, implement request pacing

### Slow scanning
- Reduce `max_assets_to_scan` for testing
- Use faster data source (Polygon/IBKR)
- Implement caching for historical data

## 📈 Data Source Comparison

| Feature | yfinance | Polygon.io | IBKR |
|---------|----------|------------|------|
| Cost | Free | $199/month | Free* |
| 4h data for stocks | ❌ | ✅ | ✅ |
| S&P 500 coverage | ✅ | ✅ | ✅ |
| Rate limits | Yes (moderate) | None | Pacing required |
| Reliability | Medium | High | High |
| Setup complexity | Easy | Easy | Moderate |

*Requires brokerage account

## 🎓 Understanding the Algorithm

### Why Double Tops?

A double top is a bearish reversal pattern where:
1. Price makes a high (peak 1)
2. Price pulls back (trough)
3. Price rallies back to similar high (peak 2)
4. Price fails to break higher and reverses

This suggests **buyers are exhausted** and sellers may take control.

### Why RSI?

RSI (Relative Strength Index) measures momentum:
- Above 70 = Overbought (potential reversal)
- Divergence = Momentum weakening despite similar prices

### Why Multi-Timeframe?

Checking multiple timeframes confirms the pattern:
- 4h: Short-term exhaustion
- Daily: Medium-term overbought
- Weekly: Long-term overbought
- Monthly: Extreme overbought (rare!)

More timeframes aligned = stronger signal

## 🔧 Customization

### Add More Assets

Edit `config/asset_universe.json`:
```json
{
  "stocks": ["AAPL", "MSFT", "GOOGL", ...],
  "crypto": ["BTC-USD", "ETH-USD"],
  "forex": ["EURUSD=X", "GBPUSD=X"]
}
```

### Change Detection Parameters

Stricter patterns (fewer results):
```yaml
pattern:
  price_tolerance_pct: 1.0    # Peaks must be closer
  min_candle_distance: 12     # More time required
  trough_depth_pct: 5.0       # Deeper trough required
```

Looser patterns (more results):
```yaml
pattern:
  price_tolerance_pct: 5.0
  min_candle_distance: 5
  trough_depth_pct: 2.0
```

## 📝 TODO / Future Enhancements

- [ ] Add triple top detection
- [ ] Implement Polygon.io data fetcher
- [ ] Implement IBKR data fetcher
- [ ] Add backtesting module
- [ ] Create web dashboard
- [ ] Add more pattern types (head & shoulders, etc.)
- [ ] Machine learning for pattern validation
- [ ] Real-time alerts (not just daily)

## 📄 License

This project is for educational purposes. Use at your own risk. Not financial advice.

## 🤝 Contributing

Feel free to submit issues or pull requests.

## Disclaimer

This is a screening tool only. It does NOT:
- Provide financial advice
- Guarantee profitable trades
- Execute trades automatically

Always:
- Review patterns manually
- Perform your own analysis
- Manage risk appropriately
- Consult a financial advisor

---

**Happy Scanning! 📊🎯**
#   d o u b l e _ t o p _ s c a n n e r  
 