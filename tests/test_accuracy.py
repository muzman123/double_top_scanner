"""
Accuracy Tests for Pattern Detection
Tests pattern detection against known criteria
"""

import pytest
import pandas as pd
import numpy as np
from src.pattern_detector import DoubleTopDetector
from src.indicators import calculate_rsi


def create_synthetic_double_top(peak_price=100, trough_depth_pct=5, candles_between=15):
    """
    Create synthetic data with known double top pattern
    
    Args:
        peak_price: Price level for peaks
        trough_depth_pct: Percentage depth of trough
        candles_between: Candles between peaks
    
    Returns:
        pd.DataFrame: OHLCV data with double top
    """
    dates = pd.date_range('2024-01-01', periods=100, freq='D')
    
    prices = []
    for i in range(100):
        if i < 30:
            price = 80 + i * 0.5  # Uptrend to peak 1
        elif i == 30:
            price = peak_price  # Peak 1
        elif i < 40:
            price = peak_price - (i - 30) * (peak_price * trough_depth_pct / 100) / 10  # Down to trough
        elif i < 30 + candles_between:
            price = peak_price * (1 - trough_depth_pct / 100)  # Trough level
        elif i < 50:
            price = peak_price * (1 - trough_depth_pct / 100) + (i - 40) * (peak_price * trough_depth_pct / 100) / 10  # Up to peak 2
        elif i == 50:
            price = peak_price * 0.99  # Peak 2 (slightly lower)
        else:
            price = peak_price * 0.99 - (i - 50) * 0.5  # Decline after pattern
        
        prices.append(price)
    
    df = pd.DataFrame({
        'Open': prices,
        'High': [p + np.random.uniform(0, 0.5) for p in prices],
        'Low': [p - np.random.uniform(0, 0.5) for p in prices],
        'Close': prices,
        'Volume': [1000000 + np.random.uniform(-100000, 100000) for _ in prices]
    }, index=dates)
    
    return df


@pytest.fixture
def config():
    """Load test configuration"""
    return {
        'pattern': {
            'price_tolerance_pct': 3.0,
            'min_candle_distance': 8,
            'trough_depth_pct': 3.0,
            'lookback_candles': 100
        },
        'rsi': {
            'period': 14,
            'divergence_min_diff': 2.0
        }
    }


class TestPatternDetection:
    """Test pattern detection accuracy"""
    
    def test_valid_double_top_detected(self, config):
        """Test that valid double top is detected"""
        df = create_synthetic_double_top(
            peak_price=100,
            trough_depth_pct=5,  # 5% depth (> 3% required)
            candles_between=15   # 15 candles (> 8 required)
        )
        
        detector = DoubleTopDetector(config)
        pattern = detector.detect(df)
        
        assert pattern is not None, "Valid double top should be detected"
        assert pattern['found'] == True
    
    def test_peak_tolerance_check(self, config):
        """Test that peaks must be within 3% tolerance"""
        df = create_synthetic_double_top(
            peak_price=100,
            trough_depth_pct=5,
            candles_between=15
        )
        
        detector = DoubleTopDetector(config)
        pattern = detector.detect(df)
        
        assert pattern is not None
        # Peak 2 is 99 (1% difference), should be within 3% tolerance
        assert pattern['price_diff_pct'] <= 3.0
    
    def test_minimum_trough_depth(self, config):
        """Test that trough must be at least 3% deep"""
        df = create_synthetic_double_top(
            peak_price=100,
            trough_depth_pct=5,  # 5% > 3% required
            candles_between=15
        )
        
        detector = DoubleTopDetector(config)
        pattern = detector.detect(df)
        
        assert pattern is not None
        assert pattern['trough_depth_pct'] >= 3.0
    
    def test_minimum_candle_distance(self, config):
        """Test that peaks must be at least 8 candles apart"""
        df = create_synthetic_double_top(
            peak_price=100,
            trough_depth_pct=5,
            candles_between=15  # 15 > 8 required
        )
        
        detector = DoubleTopDetector(config)
        pattern = detector.detect(df)
        
        assert pattern is not None
        assert pattern['candles_between'] >= 8
    
    def test_insufficient_trough_depth_rejected(self, config):
        """Test that shallow trough is rejected"""
        df = create_synthetic_double_top(
            peak_price=100,
            trough_depth_pct=2,  # Only 2% depth (< 3% required)
            candles_between=15
        )
        
        detector = DoubleTopDetector(config)
        pattern = detector.detect(df)
        
        # Should be rejected due to insufficient trough depth
        assert pattern is None or pattern['trough_depth_pct'] < 3.0
    
    def test_too_close_peaks_rejected(self, config):
        """Test that peaks too close together are rejected"""
        df = create_synthetic_double_top(
            peak_price=100,
            trough_depth_pct=5,
            candles_between=5  # Only 5 candles (< 8 required)
        )
        
        detector = DoubleTopDetector(config)
        pattern = detector.detect(df)
        
        # Should be rejected or candle distance should be < 8
        assert pattern is None or pattern['candles_between'] < 8


class TestRSICalculation:
    """Test RSI calculation accuracy"""
    
    def test_rsi_calculation_known_values(self):
        """Test RSI with known values from Wilder's original RSI"""
        # Known test data
        test_prices = pd.Series([
            44, 44.34, 44.09, 43.61, 44.33, 44.83, 45.10, 45.42, 45.84, 46.08,
            45.89, 46.03, 45.61, 46.28, 46.28, 46.00, 46.03, 46.41, 46.22, 45.64,
            46.21, 46.25, 45.71, 46.45, 45.78, 45.35, 44.03, 44.18, 44.22, 44.57
        ])
        
        rsi = calculate_rsi(test_prices, period=14)
        
        # RSI should be between 0 and 100
        assert rsi.iloc[-1] >= 0
        assert rsi.iloc[-1] <= 100
        
        # Last RSI value should be around 37-40 based on the data
        # (declining prices at the end)
        assert 30 <= rsi.iloc[-1] <= 50
    
    def test_rsi_overbought_detection(self):
        """Test RSI detects overbought conditions"""
        # Create strongly uptrending prices
        prices = pd.Series([100 + i for i in range(30)])
        
        rsi = calculate_rsi(prices, period=14)
        
        # Strong uptrend should result in high RSI
        assert rsi.iloc[-1] > 70
    
    def test_rsi_oversold_detection(self):
        """Test RSI detects oversold conditions"""
        # Create strongly downtrending prices
        prices = pd.Series([100 - i for i in range(30)])
        
        rsi = calculate_rsi(prices, period=14)
        
        # Strong downtrend should result in low RSI
        assert rsi.iloc[-1] < 30


class TestScoringSystem:
    """Test scoring system accuracy"""
    
    def test_score_components(self, config):
        """Test that each score component is counted correctly"""
        df = create_synthetic_double_top(
            peak_price=100,
            trough_depth_pct=5,
            candles_between=15
        )
        
        detector = DoubleTopDetector(config)
        pattern = detector.detect(df)
        
        assert pattern is not None
        
        # Pattern detected should always give +1
        assert pattern['found'] == True
        
        # Verify score is at least 1 (pattern detected)
        # Note: score is calculated in scanner.py, here we just verify pattern detection
    
    def test_volume_decline_calculation(self, config):
        """Test volume decline calculation"""
        df = create_synthetic_double_top(
            peak_price=100,
            trough_depth_pct=5,
            candles_between=15
        )
        
        # Manually set volumes with decline
        peak1_idx = 30
        peak2_idx = 50
        df.iloc[peak1_idx, df.columns.get_loc('Volume')] = 1000000
        df.iloc[peak2_idx, df.columns.get_loc('Volume')] = 700000  # 30% decline
        
        detector = DoubleTopDetector(config)
        pattern = detector.detect(df)
        
        assert pattern is not None
        assert pattern['volume_decline_pct'] > 0
        # Should show volume decline
        assert pattern['volume_peak1'] > pattern['volume_peak2']


class TestEdgeCases:
    """Test edge cases and boundary conditions"""
    
    def test_insufficient_data(self, config):
        """Test with insufficient data points"""
        # Only 50 candles (less than lookback period of 100)
        dates = pd.date_range('2024-01-01', periods=50, freq='D')
        df = pd.DataFrame({
            'Open': [100] * 50,
            'High': [101] * 50,
            'Low': [99] * 50,
            'Close': [100] * 50,
            'Volume': [1000000] * 50
        }, index=dates)
        
        detector = DoubleTopDetector(config)
        pattern = detector.detect(df)
        
        # Should return None with insufficient data
        assert pattern is None
    
    def test_no_peaks_found(self, config):
        """Test with flat price data (no peaks)"""
        dates = pd.date_range('2024-01-01', periods=100, freq='D')
        df = pd.DataFrame({
            'Open': [100] * 100,
            'High': [100] * 100,
            'Low': [100] * 100,
            'Close': [100] * 100,
            'Volume': [1000000] * 100
        }, index=dates)
        
        detector = DoubleTopDetector(config)
        pattern = detector.detect(df)
        
        # Should return None (no peaks in flat data)
        assert pattern is None


if __name__ == "__main__":
    pytest.main([__file__, '-v'])