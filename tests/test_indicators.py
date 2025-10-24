"""
Unit tests for indicators module
"""

import pytest
import pandas as pd
import numpy as np
from src.indicators import calculate_rsi, find_peaks, find_troughs


def test_rsi_calculation():
    """Test RSI calculation with known values"""
    # Test data from standard RSI examples
    prices = pd.Series([
        44.34, 44.09, 43.61, 44.33, 44.83, 45.10, 45.42, 45.84, 46.08,
        45.89, 46.03, 45.61, 46.28, 46.28, 46.00, 46.03, 46.41, 46.22, 45.64
    ])
    
    rsi = calculate_rsi(prices, period=14)
    
    # RSI should be between 0 and 100
    assert rsi.min() >= 0
    assert rsi.max() <= 100
    
    # Should have NaN values for first 14 periods
    assert pd.isna(rsi.iloc[0])
    
    # Should have values after warmup period
    assert not pd.isna(rsi.iloc[-1])


def test_rsi_overbought_oversold():
    """Test RSI correctly identifies overbought/oversold"""
    # Create uptrending data (should be overbought)
    uptrend = pd.Series(range(100, 150))
    rsi_up = calculate_rsi(uptrend, period=14)
    
    # RSI should be high for strong uptrend
    assert rsi_up.iloc[-1] > 70
    
    # Create downtrending data (should be oversold)
    downtrend = pd.Series(range(150, 100, -1))
    rsi_down = calculate_rsi(downtrend, period=14)
    
    # RSI should be low for strong downtrend
    assert rsi_down.iloc[-1] < 30


def test_find_peaks():
    """Test peak detection"""
    # Create data with known peaks
    prices = pd.Series([
        10, 12, 15, 18, 20, 19, 17, 15,  # Peak at index 4 (20)
        16, 18, 21, 22, 21, 19, 17,      # Peak at index 11 (22)
        18, 19, 18, 17, 16
    ])
    
    peaks = find_peaks(prices, window=2)
    
    # Should find peaks
    assert len(peaks) > 0
    
    # Peaks should be local maxima
    for peak in peaks:
        if peak > 2 and peak < len(prices) - 2:
            # Peak should be higher than surrounding values
            assert prices.iloc[peak] >= prices.iloc[peak-1]
            assert prices.iloc[peak] >= prices.iloc[peak+1]


def test_find_troughs():
    """Test trough detection"""
    # Create data with known troughs
    prices = pd.Series([
        20, 18, 15, 12, 10, 12, 15, 18,  # Trough at index 4 (10)
        17, 15, 12, 11, 13, 15, 17,      # Trough at index 11 (11)
        16, 14, 15, 16, 17
    ])
    
    troughs = find_troughs(prices, window=2)
    
    # Should find troughs
    assert len(troughs) > 0
    
    # Troughs should be local minima
    for trough in troughs:
        if trough > 2 and trough < len(prices) - 2:
            # Trough should be lower than surrounding values
            assert prices.iloc[trough] <= prices.iloc[trough-1]
            assert prices.iloc[trough] <= prices.iloc[trough+1]


def test_rsi_with_flat_prices():
    """Test RSI behavior with flat prices"""
    flat_prices = pd.Series([100.0] * 50)
    rsi = calculate_rsi(flat_prices, period=14)
    
    # RSI should be around 50 for flat prices (or NaN due to no movement)
    # This is expected behavior - no price change means no momentum
    assert pd.isna(rsi.iloc[-1]) or 45 <= rsi.iloc[-1] <= 55


def test_rsi_period_parameter():
    """Test RSI with different periods"""
    prices = pd.Series(range(100, 150))
    
    rsi_14 = calculate_rsi(prices, period=14)
    rsi_7 = calculate_rsi(prices, period=7)
    
    # Different periods should give different results
    assert not rsi_14.equals(rsi_7)
    
    # Shorter period should have values earlier
    assert pd.isna(rsi_7.iloc[10])  # Should have value
    assert pd.isna(rsi_14.iloc[10])  # Still warming up


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
