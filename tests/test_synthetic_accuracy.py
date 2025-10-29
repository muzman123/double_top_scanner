"""
Synthetic Data Accuracy Testing
Tests the double top detector against known valid and invalid patterns
Measures: Accuracy, Precision, Recall, F1 Score
"""

import pytest
import pandas as pd
import numpy as np
from src.pattern_detector import DoubleTopDetector
import logging

# Set up logging
logging.basicConfig(level=logging.WARNING)


def create_double_top_pattern(
    peak_price=100,
    trough_depth_pct=5,
    candles_between=15,
    peak2_variation_pct=0,  # How much Peak2 differs from Peak1 (+ or -)
    add_noise=True
):
    """
    Create synthetic double top pattern
    
    Args:
        peak_price: Price level for Peak1
        trough_depth_pct: Depth of trough as % of peak
        candles_between: Candles between peaks
        peak2_variation_pct: How much Peak2 varies from Peak1 (0 = identical, -1 = 1% lower)
        add_noise: Add random noise to make realistic
    
    Returns:
        pd.DataFrame: OHLCV data
    """
    dates = pd.date_range('2024-01-01', periods=100, freq='D')
    
    # Build price array
    prices = []
    for i in range(100):
        if i < 30:
            # Uptrend to Peak 1
            price = 80 + i * 0.67
        elif i == 30:
            # Peak 1
            price = peak_price
        elif i < 40:
            # Decline to trough
            progress = (i - 30) / 10
            price = peak_price - (peak_price * trough_depth_pct / 100) * progress
        elif i < 30 + candles_between:
            # Trough level
            price = peak_price * (1 - trough_depth_pct / 100)
        elif i < 50:
            # Rally to Peak 2
            progress = (i - 40) / 10
            trough_price = peak_price * (1 - trough_depth_pct / 100)
            peak2_target = peak_price * (1 + peak2_variation_pct / 100)
            price = trough_price + (peak2_target - trough_price) * progress
        elif i == 50:
            # Peak 2
            price = peak_price * (1 + peak2_variation_pct / 100)
        else:
            # Decline after pattern
            price = peak_price * (1 + peak2_variation_pct / 100) - (i - 50) * 0.5
        
        prices.append(max(price, 10))  # Prevent negative prices
    
    # Add noise if requested
    if add_noise:
        noise = np.random.normal(0, 0.3, len(prices))
        prices = [max(p + n, 10) for p, n in zip(prices, noise)]
    
    # Create OHLCV data
    df = pd.DataFrame({
        'Open': prices,
        'High': [p + abs(np.random.uniform(0, 0.5)) for p in prices],
        'Low': [p - abs(np.random.uniform(0, 0.5)) for p in prices],
        'Close': prices,
        'Volume': [1000000 + np.random.uniform(-100000, 100000) for _ in prices]
    }, index=dates)
    
    # Ensure High >= Close >= Low
    df['High'] = df[['High', 'Close']].max(axis=1)
    df['Low'] = df[['Low', 'Close']].min(axis=1)
    
    return df


def create_uptrend(length=100, start_price=80, end_price=120):
    """Create uptrending data (not a double top)"""
    dates = pd.date_range('2024-01-01', periods=length, freq='D')
    prices = np.linspace(start_price, end_price, length)
    
    # Add some volatility
    noise = np.random.normal(0, 1, length)
    prices = prices + noise
    
    df = pd.DataFrame({
        'Open': prices,
        'High': [p + abs(np.random.uniform(0, 0.5)) for p in prices],
        'Low': [p - abs(np.random.uniform(0, 0.5)) for p in prices],
        'Close': prices,
        'Volume': [1000000 + np.random.uniform(-100000, 100000) for _ in prices]
    }, index=dates)
    
    df['High'] = df[['High', 'Close']].max(axis=1)
    df['Low'] = df[['Low', 'Close']].min(axis=1)
    
    return df


def create_downtrend(length=100, start_price=120, end_price=80):
    """Create downtrending data (not a double top)"""
    return create_uptrend(length, start_price, end_price)


def create_single_peak(peak_price=100, length=100):
    """Create single peak pattern (not a double top)"""
    dates = pd.date_range('2024-01-01', periods=length, freq='D')
    prices = []
    
    for i in range(length):
        if i < 45:
            # Uptrend
            price = 80 + i * 0.44
        elif i == 45:
            # Single peak
            price = peak_price
        else:
            # Decline
            price = peak_price - (i - 45) * 0.36
        
        prices.append(max(price, 10))
    
    # Add noise
    noise = np.random.normal(0, 0.3, length)
    prices = [max(p + n, 10) for p, n in zip(prices, noise)]
    
    df = pd.DataFrame({
        'Open': prices,
        'High': [p + abs(np.random.uniform(0, 0.5)) for p in prices],
        'Low': [p - abs(np.random.uniform(0, 0.5)) for p in prices],
        'Close': prices,
        'Volume': [1000000 + np.random.uniform(-100000, 100000) for _ in prices]
    }, index=dates)
    
    df['High'] = df[['High', 'Close']].max(axis=1)
    df['Low'] = df[['Low', 'Close']].min(axis=1)
    
    return df


def create_triple_top(peak_price=100, length=100):
    """Create triple top pattern (not a simple double top)"""
    dates = pd.date_range('2024-01-01', periods=length, freq='D')
    prices = []
    
    for i in range(length):
        if i < 25:
            price = 80 + i * 0.8
        elif i == 25:
            price = peak_price  # Peak 1
        elif i < 35:
            price = peak_price - (i - 25) * 0.5
        elif i == 40:
            price = peak_price  # Peak 2
        elif i < 50:
            price = peak_price - (i - 40) * 0.5
        elif i == 55:
            price = peak_price  # Peak 3
        else:
            price = peak_price - (i - 55) * 0.5
        
        prices.append(max(price, 10))
    
    noise = np.random.normal(0, 0.3, length)
    prices = [max(p + n, 10) for p, n in zip(prices, noise)]
    
    df = pd.DataFrame({
        'Open': prices,
        'High': [p + abs(np.random.uniform(0, 0.5)) for p in prices],
        'Low': [p - abs(np.random.uniform(0, 0.5)) for p in prices],
        'Close': prices,
        'Volume': [1000000 + np.random.uniform(-100000, 100000) for _ in prices]
    }, index=dates)
    
    df['High'] = df[['High', 'Close']].max(axis=1)
    df['Low'] = df[['Low', 'Close']].min(axis=1)
    
    return df


def create_sideways_range(length=100, price=100, range_pct=3):
    """Create sideways/ranging market (not a double top)"""
    dates = pd.date_range('2024-01-01', periods=length, freq='D')
    
    # Random walk within range
    prices = [price]
    for _ in range(length - 1):
        change = np.random.uniform(-range_pct/2, range_pct/2)
        new_price = prices[-1] * (1 + change/100)
        prices.append(new_price)
    
    df = pd.DataFrame({
        'Open': prices,
        'High': [p + abs(np.random.uniform(0, 0.5)) for p in prices],
        'Low': [p - abs(np.random.uniform(0, 0.5)) for p in prices],
        'Close': prices,
        'Volume': [1000000 + np.random.uniform(-100000, 100000) for _ in prices]
    }, index=dates)
    
    df['High'] = df[['High', 'Close']].max(axis=1)
    df['Low'] = df[['Low', 'Close']].min(axis=1)
    
    return df


@pytest.fixture
def config():
    """Standard test configuration"""
    return {
        'pattern': {
            'mode': 'prediction',
            'price_tolerance_pct': 3.0,
            'min_candle_distance': 8,
            'trough_depth_pct': 3.0,
            'lookback_candles': 100,
            'min_confidence': 30,
            'min_prominence': 1.5,
            'peak_window': 5,
            'max_exceed_pct': 3.0,
            'min_reversal_drop_pct': 1.5,
            'min_rally_rise_pct': 1.5,
            'max_peak_age_pct': 50,
            'reversal_threshold_pct': 2
        },
        'rsi': {
            'period': 14,
            'divergence_min_diff': 0.5,
            'divergence_required': True
        }
    }


class TestSyntheticAccuracy:
    """Test accuracy using synthetic data"""
    
    def test_valid_double_tops(self, config):
        """Test True Positives: Valid double tops SHOULD be detected"""
        
        detector = DoubleTopDetector(config)
        
        # Create various valid double top patterns
        test_cases = [
            # (name, params)
            ("Perfect double top", {
                'peak_price': 100,
                'trough_depth_pct': 5,
                'candles_between': 15,
                'peak2_variation_pct': 0
            }),
            ("Peak2 slightly lower", {
                'peak_price': 100,
                'trough_depth_pct': 5,
                'candles_between': 15,
                'peak2_variation_pct': -1
            }),
            ("Deep trough", {
                'peak_price': 100,
                'trough_depth_pct': 8,
                'candles_between': 15,
                'peak2_variation_pct': 0
            }),
            ("Wide spacing", {
                'peak_price': 100,
                'trough_depth_pct': 5,
                'candles_between': 30,
                'peak2_variation_pct': 0
            }),
            ("Minimum spacing", {
                'peak_price': 100,
                'trough_depth_pct': 5,
                'candles_between': 10,
                'peak2_variation_pct': 0
            }),
            ("Peak2 marginal higher", {
                'peak_price': 100,
                'trough_depth_pct': 5,
                'candles_between': 15,
                'peak2_variation_pct': 1
            }),
        ]
        
        results = []
        for name, params in test_cases:
            df = create_double_top_pattern(**params)
            pattern = detector.detect(df)
            detected = pattern is not None
            results.append({
                'name': name,
                'detected': detected,
                'expected': True
            })
            if not detected:
                print(f"  ❌ FALSE NEGATIVE: {name}")
            else:
                print(f"  ✅ TRUE POSITIVE: {name}")
        
        # Calculate metrics
        true_positives = sum(1 for r in results if r['detected'] and r['expected'])
        false_negatives = sum(1 for r in results if not r['detected'] and r['expected'])
        
        sensitivity = true_positives / len(results) * 100
        
        print(f"\n📊 Valid Double Tops Detection:")
        print(f"  True Positives: {true_positives}/{len(results)}")
        print(f"  False Negatives: {false_negatives}/{len(results)}")
        print(f"  Sensitivity (Recall): {sensitivity:.1f}%")
        
        # Should detect at least 80% of valid patterns
        assert sensitivity >= 80, f"Sensitivity too low: {sensitivity:.1f}%"
    
    def test_invalid_patterns(self, config):
        """Test True Negatives: Non-double-tops should NOT be detected"""
        
        detector = DoubleTopDetector(config)
        
        # Create various non-double-top patterns
        test_cases = [
            ("Uptrend", create_uptrend()),
            ("Downtrend", create_downtrend()),
            ("Single peak", create_single_peak()),
            ("Triple top", create_triple_top()),
            ("Sideways range", create_sideways_range()),
            ("Shallow trough (2%)", create_double_top_pattern(trough_depth_pct=2)),
            ("Peaks too close (5 candles)", create_double_top_pattern(candles_between=5)),
            ("Peak2 much higher (6%)", create_double_top_pattern(peak2_variation_pct=6)),
        ]
        
        results = []
        for name, df in test_cases:
            pattern = detector.detect(df)
            detected = pattern is not None
            results.append({
                'name': name,
                'detected': detected,
                'expected': False
            })
            if detected:
                print(f"  ❌ FALSE POSITIVE: {name}")
            else:
                print(f"  ✅ TRUE NEGATIVE: {name}")
        
        # Calculate metrics
        true_negatives = sum(1 for r in results if not r['detected'] and not r['expected'])
        false_positives = sum(1 for r in results if r['detected'] and not r['expected'])
        
        specificity = true_negatives / len(results) * 100
        
        print(f"\n📊 Invalid Patterns Rejection:")
        print(f"  True Negatives: {true_negatives}/{len(results)}")
        print(f"  False Positives: {false_positives}/{len(results)}")
        print(f"  Specificity: {specificity:.1f}%")
        
        # Should correctly reject at least 75% of invalid patterns
        assert specificity >= 75, f"Specificity too low: {specificity:.1f}%"
    
    def test_edge_cases(self, config):
        """Test edge cases and boundary conditions"""
        
        detector = DoubleTopDetector(config)
        
        test_cases = [
            ("Exactly 3% trough depth", create_double_top_pattern(trough_depth_pct=3.0), True),
            ("Just under 3% trough (2.9%)", create_double_top_pattern(trough_depth_pct=2.9), False),
            ("Exactly 8 candles apart", create_double_top_pattern(candles_between=8), True),
            ("7 candles apart", create_double_top_pattern(candles_between=7), False),
            ("Exactly 3% price diff", create_double_top_pattern(peak2_variation_pct=3), True),
            ("Just over 3% price diff (3.5%)", create_double_top_pattern(peak2_variation_pct=3.5), False),
        ]
        
        results = []
        for name, df, expected in test_cases:
            pattern = detector.detect(df)
            detected = pattern is not None
            correct = (detected == expected)
            results.append({
                'name': name,
                'detected': detected,
                'expected': expected,
                'correct': correct
            })
            
            status = "✅" if correct else "❌"
            print(f"  {status} {name}: Detected={detected}, Expected={expected}")
        
        accuracy = sum(1 for r in results if r['correct']) / len(results) * 100
        print(f"\n📊 Edge Cases Accuracy: {accuracy:.1f}%")
        
        assert accuracy >= 80, f"Edge case accuracy too low: {accuracy:.1f}%"


def run_comprehensive_accuracy_test():
    """
    Run comprehensive accuracy test and generate report
    """
    print("\n" + "="*80)
    print("SYNTHETIC DATA ACCURACY TEST")
    print("="*80)
    
    config = {
        'pattern': {
            'mode': 'prediction',
            'price_tolerance_pct': 3.0,
            'min_candle_distance': 8,
            'trough_depth_pct': 3.0,
            'lookback_candles': 100,
            'min_confidence': 30,
            'min_prominence': 1.5,
            'peak_window': 5,
            'max_exceed_pct': 3.0,
            'min_reversal_drop_pct': 1.5,
            'min_rally_rise_pct': 1.5,
            'max_peak_age_pct': 50,
            'reversal_threshold_pct': 2
        },
        'rsi': {
            'period': 14,
            'divergence_min_diff': 0.5,
            'divergence_required': True
        }
    }
    
    detector = DoubleTopDetector(config)
    
    # Generate test data
    print("\n📊 Generating test datasets...")
    
    # TRUE POSITIVES (should detect)
    valid_patterns = [
        ("Valid DT - Perfect", create_double_top_pattern(100, 5, 15, 0)),
        ("Valid DT - Peak2 lower", create_double_top_pattern(100, 5, 15, -1)),
        ("Valid DT - Deep trough", create_double_top_pattern(100, 8, 15, 0)),
        ("Valid DT - Wide spacing", create_double_top_pattern(100, 5, 30, 0)),
        ("Valid DT - Min spacing", create_double_top_pattern(100, 5, 10, 0)),
        ("Valid DT - Peak2 marginal higher", create_double_top_pattern(100, 5, 15, 1)),
        ("Valid DT - Min trough depth", create_double_top_pattern(100, 3.5, 15, 0)),
        ("Valid DT - Large price", create_double_top_pattern(500, 5, 15, 0)),
    ]
    
    # TRUE NEGATIVES (should NOT detect)
    invalid_patterns = [
        ("Uptrend", create_uptrend()),
        ("Downtrend", create_downtrend()),
        ("Single peak", create_single_peak()),
        ("Triple top", create_triple_top()),
        ("Sideways", create_sideways_range()),
        ("Shallow trough", create_double_top_pattern(trough_depth_pct=2)),
        ("Peaks too close", create_double_top_pattern(candles_between=5)),
        ("Peak2 too high", create_double_top_pattern(peak2_variation_pct=6)),
    ]
    
    # Test valid patterns
    print("\n" + "-"*80)
    print("TESTING VALID DOUBLE TOPS (Should Detect)")
    print("-"*80)
    
    tp = 0  # True positives
    fn = 0  # False negatives
    
    for name, df in valid_patterns:
        pattern = detector.detect(df)
        if pattern is not None:
            tp += 1
            print(f"✅ {name}: DETECTED (confidence: {pattern['confidence']:.0f}%)")
        else:
            fn += 1
            print(f"❌ {name}: NOT DETECTED (False Negative)")
    
    # Test invalid patterns
    print("\n" + "-"*80)
    print("TESTING INVALID PATTERNS (Should NOT Detect)")
    print("-"*80)
    
    tn = 0  # True negatives
    fp = 0  # False positives
    
    for name, df in invalid_patterns:
        pattern = detector.detect(df)
        if pattern is None:
            tn += 1
            print(f"✅ {name}: NOT DETECTED (Correct)")
        else:
            fp += 1
            print(f"❌ {name}: DETECTED (False Positive, confidence: {pattern['confidence']:.0f}%)")
    
    # Calculate metrics
    print("\n" + "="*80)
    print("ACCURACY METRICS")
    print("="*80)
    
    total = tp + tn + fp + fn
    accuracy = (tp + tn) / total * 100 if total > 0 else 0
    precision = tp / (tp + fp) * 100 if (tp + fp) > 0 else 0
    recall = tp / (tp + fn) * 100 if (tp + fn) > 0 else 0
    specificity = tn / (tn + fp) * 100 if (tn + fp) > 0 else 0
    f1_score = 2 * (precision * recall) / (precision + recall) if (precision + recall) > 0 else 0
    
    print(f"\nConfusion Matrix:")
    print(f"                    Predicted Positive    Predicted Negative")
    print(f"Actual Positive     {tp:^18}    {fn:^18}")
    print(f"Actual Negative     {fp:^18}    {tn:^18}")
    
    print(f"\nPerformance Metrics:")
    print(f"  Total Test Cases: {total}")
    print(f"  Accuracy:         {accuracy:.1f}%   (Correct predictions / Total)")
    print(f"  Precision:        {precision:.1f}%   (True Positives / All Positives)")
    print(f"  Recall/Sensitivity: {recall:.1f}%   (True Positives / Actual Positives)")
    print(f"  Specificity:      {specificity:.1f}%   (True Negatives / Actual Negatives)")
    print(f"  F1 Score:         {f1_score:.1f}%   (Harmonic mean of Precision & Recall)")
    
    print(f"\nInterpretation:")
    if accuracy >= 90:
        print("  🎉 EXCELLENT: Algorithm performs exceptionally well!")
    elif accuracy >= 80:
        print("  ✅ GOOD: Algorithm performs well with minor issues")
    elif accuracy >= 70:
        print("  ⚠️  FAIR: Algorithm needs some tuning")
    else:
        print("  ❌ POOR: Algorithm needs significant improvements")
    
    if recall < 70:
        print("  ⚠️  Low Recall: Missing too many valid patterns (false negatives)")
    if specificity < 70:
        print("  ⚠️  Low Specificity: Detecting too many invalid patterns (false positives)")
    
    return {
        'accuracy': accuracy,
        'precision': precision,
        'recall': recall,
        'specificity': specificity,
        'f1_score': f1_score,
        'tp': tp,
        'tn': tn,
        'fp': fp,
        'fn': fn
    }


if __name__ == "__main__":
    # Run comprehensive test
    results = run_comprehensive_accuracy_test()
    
    # Save results
    import json
    import os
    
    os.makedirs('output/accuracy_results', exist_ok=True)
    
    with open('output/accuracy_results/synthetic_accuracy.json', 'w') as f:
        json.dump(results, f, indent=2)
    
    print(f"\n📁 Results saved to: output/accuracy_results/synthetic_accuracy.json")