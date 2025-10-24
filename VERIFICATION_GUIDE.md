# Pattern Detection Verification Guide

This guide provides multiple strategies to verify that the Double Top Scanner is accurately detecting patterns.

## 🎯 Quick Verification Methods

### Method 1: Visual Chart Verification (RECOMMENDED)

**Step 1: Run the verification tool**
```bash
python verify_results.py META --plot
```

This will:
- ✅ Show detailed pattern metrics
- ✅ Generate a visual chart with peaks/trough marked
- ✅ Display RSI divergence visually
- ✅ Verify all scoring criteria

**Step 2: Manual Chart Comparison**
1. Open the generated chart image in `output/`
2. Go to https://finance.yahoo.com/chart/{SYMBOL}
3. Set to Daily timeframe
4. Compare:
   - Peak locations and prices
   - Trough location and depth
   - RSI values at peaks (add RSI indicator on Yahoo Finance)

**What to Look For:**
- ✅ Peaks should be at similar price levels (within 3%)
- ✅ Trough should be significantly lower (at least 3% from peak)
- ✅ RSI at Peak 2 should be lower than Peak 1 (for divergence)
- ✅ At least 8 candles between peaks

---

### Method 2: Compare with Known Patterns

**Test with Gold (XAUUSD) - The Reference Case**

According to the spec, Gold around $2,790 should show:
- Peak 1 & 2: Both around $2,790 level
- Trough: ~$2,670 (4.3% decline)
- All RSI timeframes overbought
- Score: 6/6

**Verification Steps:**
```bash
# Test with Gold
python verify_results.py GC=F --plot

# Or use the historical data if available
python verify_results.py XAUUSD --plot
```

Compare results to specification:
- Peak difference should be ~0.2%
- Trough depth should be ~4.3%
- All RSI values should be >70

---

### Method 3: Unit Test Validation

**Run the unit tests:**
```bash
pytest tests/test_indicators.py -v
```

This verifies:
- ✅ RSI calculation accuracy
- ✅ Peak/trough detection logic
- ✅ Pattern matching criteria

**Create your own test:**
```python
# Add to tests/test_patterns.py
def test_known_double_top():
    """Test with synthetic double top data"""
    # Create perfect double top pattern
    prices = create_double_top_data(
        peak1_price=100,
        peak2_price=100,
        trough_price=94,  # 6% depth
        candles_between=10
    )
    
    pattern = detector.detect(prices)
    
    assert pattern is not None
    assert pattern['price_diff_pct'] < 3.0
    assert pattern['trough_depth_pct'] >= 3.0
    assert pattern['candles_between'] >= 8
```

---

### Method 4: Cross-Validation with Trading View

**TradingView Comparison:**

1. Go to https://www.tradingview.com/chart/
2. Load your symbol (e.g., META, NVDA)
3. Add indicators:
   - RSI(14) for Daily, Weekly, Monthly
4. Use the drawing tools to mark:
   - Horizontal lines at peak levels
   - Measure trough depth
   - Count candles between peaks

**Compare:**
- Scanner peak prices vs. TradingView peak prices
- Scanner RSI values vs. TradingView RSI values
- Trough depth percentage

---

### Method 5: CSV Results Validation

**Check the CSV output:**
```bash
# View results
cat output/alerts_2025-10-22.csv

# Or open in Excel/Google Sheets for easier viewing
```

**Manual Verification Checklist:**

For each detected pattern, verify:

| Criterion | Expected | How to Verify |
|-----------|----------|---------------|
| Peak Price Difference | ≤ 3% | `abs(peak2_price - peak1_price) / peak1_price * 100` |
| Candles Between Peaks | ≥ 8 | Check `candles_between_peaks` column |
| Trough Depth | ≥ 3% | Check `trough_depth_pct` column |
| RSI Divergence | Peak1 > Peak2 by ≥2 | `rsi_divergence_value` ≥ 2.0 |
| Daily RSI | > 70 for score | Check `rsi_daily` column |
| Volume Decline | ≥ 20% for score | Check `volume_decline_pct` column |

---

## 🔬 Advanced Verification Strategies

### Strategy 1: Backtest Historical Accuracy

**Test on known market tops:**
```bash
# Test major tops from 2021-2024
python verify_results.py SPY --plot  # S&P 500
python verify_results.py QQQ --plot  # NASDAQ
python verify_results.py AAPL --plot # Apple's known tops
```

Research historical double tops and verify the scanner detects them.

---

### Strategy 2: False Positive Rate Testing

**Scan assets that should NOT have patterns:**

```bash
# Test with stocks in strong uptrends (should find few/no patterns)
python run_scanner.py --symbol TSLA
python run_scanner.py --symbol NVDA
```

**Expected:** 
- Uptrending stocks should have low scores (0-2)
- Only overbought stocks with actual double tops should score 3+

---

### Strategy 3: Multi-Timeframe Consistency Check

**Verify RSI across timeframes:**

```python
# Create this test script
from src.data_fetcher import DataFetcher
from src.indicators import calculate_rsi
import yaml

with open('config/settings.yaml') as f:
    config = yaml.safe_load(f)

fetcher = DataFetcher(config)
data = fetcher.fetch_multiple_timeframes('AAPL', ['1d', '1wk', '1mo'])

for tf, df in data.items():
    rsi = calculate_rsi(df['Close'], period=14)
    print(f"{tf}: Current RSI = {rsi.iloc[-1]:.2f}")
```

**Compare with:**
- TradingView RSI values
- Other trading platforms
- Manual RSI calculation in Excel

---

### Strategy 4: Divergence Validation

**For patterns with RSI divergence, verify:**

1. Price makes similar/higher high at Peak 2
2. RSI makes lower high at Peak 2
3. Difference is at least 2 points

**Visual check:**
```bash
python verify_results.py META --plot
```

Look at the RSI chart:
- RSI at Peak 1 should be HIGHER than RSI at Peak 2
- For META example: RSI divergence of 20.9 points is clearly visible

---

## 📊 Statistical Validation

### Expected Detection Rates

Based on the spec and market conditions:

| Score | Expected Frequency | What It Means |
|-------|-------------------|---------------|
| 6/6 | RARE (1-2%) | Perfect setup like Gold example |
| 5/6 | LOW (3-5%) | High quality signals |
| 4/6 | MODERATE (10-15%) | Good tradable setups |
| 3/6 | COMMON (20-30%) | Watchlist items |
| <3 | FILTERED OUT | Not reported |

**If you're seeing:**
- Too many 6/6 scores → Criteria may be too loose
- No patterns at all → Criteria may be too strict
- All scores are 3 → Check RSI overbought conditions

---

## 🧪 Quick Accuracy Tests

### Test 1: Known Good Pattern (META Example)

From the CSV output, META shows:
- Peak 1: $747.40, Peak 2: $758.37 (1.47% difference ✅)
- Trough: $690.73 (7.58% depth ✅)
- 39 candles between peaks ✅
- RSI Divergence: 20.9 points ✅
- Score: 3/6 ✅

**Verify this manually:**
```bash
python verify_results.py META --plot
```

Then check https://finance.yahoo.com/chart/META

---

### Test 2: RSI Calculation Accuracy

**Compare with known RSI formula:**

```python
# Test RSI calculation
from src.indicators import calculate_rsi
import pandas as pd

# Known test data from Wilder's RSI
test_prices = pd.Series([
    44, 44.34, 44.09, 43.61, 44.33, 44.83, 45.10, 45.42, 45.84, 46.08,
    45.89, 46.03, 45.61, 46.28, 46.28, 46.00, 46.03, 46.41, 46.22, 45.64
])

rsi = calculate_rsi(test_prices, period=14)
print(f"Latest RSI: {rsi.iloc[-1]:.2f}")

# Expected: ~70.5 (based on Wilder's original RSI)
# If within 1-2 points, calculation is correct
```

---

### Test 3: Scoring System Verification

**Manual score calculation:**

For any detected pattern, calculate score manually:
1. Pattern detected? +1
2. RSI divergence (≥2 points)? +1
3. Daily RSI > 70? +1
4. Weekly RSI > 70? +1
5. Monthly RSI > 70? +1
6. Volume decline ≥20%? +1

**Compare with scanner output.**

---

## 🚨 Red Flags (Potential Issues)

Watch for these signs of inaccurate detection:

| Red Flag | Possible Issue | Solution |
|----------|---------------|----------|
| All patterns score 6/6 | Criteria too loose | Check RSI threshold config |
| Peaks at random locations | Peak detection bug | Verify `find_peaks()` window size |
| Trough outside peak range | Trough detection bug | Check trough search logic |
| RSI values don't match charts | RSI calculation error | Test with known RSI values |
| Negative volume decline | Volume calculation bug | Check volume data availability |

---

## ✅ Validation Checklist

Before trusting results, complete this checklist:

- [ ] Run verification tool on 3-5 symbols
- [ ] Compare at least 2 patterns with Yahoo Finance charts
- [ ] Verify RSI values match TradingView/Yahoo Finance
- [ ] Check that peak tolerance is ≤3%
- [ ] Verify trough depth is ≥3%
- [ ] Confirm candle distance is ≥8
- [ ] Test known market tops (if available)
- [ ] Review false positive rate (should be <25%)

---

## 🎓 Learning from Results

**Good Pattern Example (High Confidence):**
- Clear visual double top formation
- Strong RSI divergence (>5 points)
- Multiple timeframes overbought
- Volume declining at Peak 2
- Score: 4-6/6

**Questionable Pattern (Low Confidence):**
- Barely meets 3% tolerance
- Minimal RSI divergence (<3 points)
- Mixed RSI timeframes
- Score: 3/6

**Always verify high-score patterns manually before trading!**

---

## 📚 Resources for Verification

1. **Yahoo Finance Charts**: https://finance.yahoo.com/chart/
2. **TradingView**: https://www.tradingview.com/chart/
3. **Investopedia RSI Guide**: https://www.investopedia.com/terms/r/rsi.asp
4. **Double Top Pattern**: https://www.investopedia.com/terms/d/doubletop.asp

---

## 🔧 Quick Commands Reference

```bash
# Verify single symbol with visual chart
python verify_results.py AAPL --plot

# Scan single symbol (text output only)
python run_scanner.py --symbol AAPL

# Run full scan with test set
python run_scanner.py --test

# View latest results
cat output/alerts_2025-10-22.csv
```

---

## 💡 Pro Tips

1. **Start Small**: Verify 5-10 symbols manually before trusting full scans
2. **Use Visual Verification**: Charts don't lie - always check visually
3. **Compare Multiple Sources**: Yahoo Finance + TradingView for confirmation
4. **Document Discrepancies**: If you find errors, note them for debugging
5. **Test Edge Cases**: Very small/large stocks, volatile vs stable
6. **Check Market Conditions**: More patterns in overbought markets

---

**Remember:** This is a screening tool, not a trading signal. Always perform manual analysis before trading!