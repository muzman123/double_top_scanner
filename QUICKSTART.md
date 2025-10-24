# Quick Start Guide

Get the Double Top Scanner running in 5 minutes!

## Step 1: Install (2 minutes)

### Linux/Mac:
```bash
cd double_top_scanner
./setup.sh
```

### Windows:
```cmd
cd double_top_scanner
setup.bat
```

This will:
- Create virtual environment
- Install all dependencies
- Create .env file template
- Create output directories

## Step 2: Configure Email (1 minute)

Edit `.env` file:

```bash
# For Gmail
SMTP_USERNAME=your_email@gmail.com
SMTP_PASSWORD=your_gmail_app_password
```

**Getting Gmail App Password:**
1. Go to: https://myaccount.google.com/apppasswords
2. Select "Mail" and your device
3. Copy the 16-character password
4. Paste into `.env` file

**Note:** If you don't want email, set `email_enabled: false` in `config/settings.yaml`

## Step 3: Test Run (1 minute)

```bash
# Activate environment
source venv/bin/activate  # Linux/Mac
venv\Scripts\activate     # Windows

# Test with 5 symbols
python run_scanner.py --test
```

You should see output like:
```
Loading configuration...
Initializing scanner...
Scanning 5 assets...
Progress: 5/5
Found 1 candidates with score >= 3
```

## Step 4: Test Single Symbol (1 minute)

```bash
# Test with a specific stock
python run_scanner.py --symbol AAPL
```

This will show if a double top pattern exists for that symbol.

## Step 5: Full Scan (Optional)

```bash
# Scan all 38 symbols in test config (takes ~5 minutes)
python run_scanner.py
```

Results will be in:
- Console output
- `output/alerts_2025-10-22.csv`
- `output/logs/scanner.log`

## Understanding Output

### Score Meanings:
- **6/6**: PREMIUM - All criteria met (very rare)
- **5/6**: HIGH - Almost perfect setup
- **4/6**: GOOD - Solid opportunity
- **3/6**: WATCHLIST - Monitor for development

### Pattern Example:
```
AAPL     | $175.23  | Peak1: $178.45 | Peak2: $177.89 | Trough:  3.6% | RSI: 73.5 | Div: 
```

This means:
- Current price: $175.23
- Two peaks around $178
- Trough dropped 3.6% below peaks
- Daily RSI is overbought at 73.5
- RSI divergence detected ()

## Common Issues

### "No data returned for symbol"
- Check internet connection
- Try different symbol
- Some symbols don't have data for all timeframes

### "SMTP authentication failed"
- Use App Password, not regular Gmail password
- Enable 2FA on Gmail first
- Check username/password are correct

### Scanner is slow
- Normal: ~10-30 seconds per symbol with yfinance
- To speed up: reduce symbols or use Polygon.io

## Next Steps

1. **Review config**: Edit `config/settings.yaml` to adjust parameters
2. **Add symbols**: Edit `config/asset_universe.json` to add more stocks
3. **Schedule daily**: Set up cron job (see README.md)
4. **Get S&P 500**: Set `sp500_auto_update: true` in config

## Full Documentation

See `README.md` for:
- Complete configuration options
- Data source alternatives (Polygon.io, IBKR)
- Automated scheduling setup
- Pattern detection details
- Troubleshooting guide

## Tips for Success

1. **Start small**: Test with 5-10 symbols before scaling to 500
2. **Understand patterns**: Review detected patterns on charts manually
3. **Adjust parameters**: Tune `config/settings.yaml` to your trading style
4. **Check daily**: Review alerts each morning before market open
5. **Paper trade first**: Test signals before real money

## Getting Help

- Check `README.md` for detailed documentation
- Review log files in `output/logs/`
- Test individual modules (see README.md "Manual Testing")
- Verify data is being fetched correctly

---

**You're ready to scan!** 🚀

Try: `python run_scanner.py --test`
