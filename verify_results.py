#!/usr/bin/env python3
"""
Pattern Verification Tool
Visually verify that detected patterns are accurate
"""

import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import yaml
from datetime import datetime
from src.scanner import DoubleTopScanner
from src.data_fetcher import DataFetcher
from src.indicators import calculate_rsi

def plot_pattern(symbol, data, pattern_result, config):
    """
    Plot price chart with detected pattern highlighted
    
    Args:
        symbol (str): Ticker symbol
        data (dict): Multi-timeframe data
        pattern_result (dict): Pattern detection result
        config (dict): Configuration dictionary
    """
    # Use primary timeframe (4h by default) for chart
    # This ensures the pattern timestamps match the data
    primary_tf = config['data']['primary_timeframe']
    
    if primary_tf not in data:
        print(f"Warning: Primary timeframe {primary_tf} not in data, using 1d")
        primary_tf = '1d'
    
    df = data[primary_tf].copy()
    
    # Calculate RSI for daily
    df['RSI'] = calculate_rsi(df['Close'], period=14)
    
    # Create figure with 2 subplots
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(14, 10), 
                                     gridspec_kw={'height_ratios': [2, 1]})
    
    # Plot 1: Price with pattern
    ax1.plot(df.index, df['Close'], label='Close Price', linewidth=1.5, color='black')
    ax1.fill_between(df.index, df['Low'], df['High'], alpha=0.3, color='lightblue')
    
    # Mark peaks and trough
    try:
        # Parse timestamps from pattern result
        peak1_time = pd.to_datetime(pattern_result['peak1_time'])
        peak2_time = pd.to_datetime(pattern_result['peak2_time'])
        trough_time = pd.to_datetime(pattern_result.get('trough_time', pattern_result['peak1_time']))
        
        # Get prices from pattern result
        peak1_price = pattern_result['peak1_price']
        peak2_price = pattern_result['peak2_price']
        trough_price = pattern_result['trough_price']
        
        # Plot markers with larger size and better visibility
        ax1.scatter([peak1_time], [peak1_price],
                   color='red', s=400, marker='v', label='Peak 1', zorder=10,
                   edgecolors='darkred', linewidths=3)
        ax1.scatter([peak2_time], [peak2_price],
                   color='red', s=400, marker='v', label='Peak 2', zorder=10,
                   edgecolors='darkred', linewidths=3)
        ax1.scatter([trough_time], [trough_price],
                   color='lime', s=400, marker='^', label='Trough', zorder=10,
                   edgecolors='darkgreen', linewidths=3)
        
        # Draw neckline (horizontal line at trough price) - make it very visible
        neckline = pattern_result.get('neckline', trough_price)
        ax1.axhline(y=neckline, color='purple',
                   linestyle='--', linewidth=3, label=f'Neckline = ${neckline:.2f}', alpha=0.9)
        
        # Draw horizontal lines connecting peaks (resistance level)
        ax1.hlines(y=peak1_price, xmin=peak1_time, xmax=peak2_time,
                  colors='orange', linestyles='dotted', linewidth=2, alpha=0.6, label='Resistance')
        
        # Add text annotations with better visibility
        ax1.annotate(f"PEAK 1\n${peak1_price:.2f}",
                    xy=(peak1_time, peak1_price),
                    xytext=(0, 35), textcoords='offset points',
                    bbox=dict(boxstyle='round,pad=0.7', facecolor='red', alpha=0.85, edgecolor='black', linewidth=2),
                    fontsize=11, ha='center', color='white', fontweight='bold',
                    arrowprops=dict(arrowstyle='->', color='red', lw=2))
        
        ax1.annotate(f"PEAK 2\n${peak2_price:.2f}",
                    xy=(peak2_time, peak2_price),
                    xytext=(0, 35), textcoords='offset points',
                    bbox=dict(boxstyle='round,pad=0.7', facecolor='red', alpha=0.85, edgecolor='black', linewidth=2),
                    fontsize=11, ha='center', color='white', fontweight='bold',
                    arrowprops=dict(arrowstyle='->', color='red', lw=2))
        
        ax1.annotate(f"TROUGH\n${trough_price:.2f}\n({pattern_result['trough_depth_pct']:.1f}% drop)",
                    xy=(trough_time, trough_price),
                    xytext=(0, -50), textcoords='offset points',
                    bbox=dict(boxstyle='round,pad=0.7', facecolor='lime', alpha=0.85, edgecolor='black', linewidth=2),
                    fontsize=11, ha='center', color='black', fontweight='bold',
                    arrowprops=dict(arrowstyle='->', color='green', lw=2))
        
        print(f" Pattern markers plotted successfully")
        print(f"  Peak 1: ${peak1_price:.2f} at {peak1_time}")
        print(f"  Peak 2: ${peak2_price:.2f} at {peak2_time}")
        print(f"  Trough: ${trough_price:.2f} at {trough_time}")
        print(f"  Neckline: ${neckline:.2f}")
        
    except Exception as e:
        print(f"Warning: Could not plot pattern markers: {e}")
        import traceback
        traceback.print_exc()
    
    ax1.set_title(f'{symbol} - Double Top Pattern Detection\nScore: {pattern_result["score"]}/6', 
                  fontsize=14, fontweight='bold')
    ax1.set_ylabel('Price ($)', fontsize=12)
    ax1.legend(loc='upper left', fontsize=10)
    ax1.grid(True, alpha=0.3)
    
    # Plot 2: RSI
    ax2.plot(df.index, df['RSI'], label='RSI(14)', linewidth=1.5, color='blue')
    ax2.axhline(y=70, color='red', linestyle='--', linewidth=1, label='Overbought (70)', alpha=0.7)
    ax2.axhline(y=30, color='green', linestyle='--', linewidth=1, label='Oversold (30)', alpha=0.7)
    
    # Mark RSI at peaks
    try:
        # Get RSI values - try different field names
        rsi_peak1 = pattern_result.get('rsi_peak1') or pattern_result.get('rsi_4h_peak1')
        rsi_peak2 = pattern_result.get('rsi_peak2') or pattern_result.get('rsi_4h_peak2')
        
        if rsi_peak1 and peak1_time in df.index:
            ax2.scatter([peak1_time], [rsi_peak1],
                       color='red', s=150, marker='o', zorder=5, edgecolors='darkred', linewidths=2)
            ax2.annotate(f"Peak1 RSI: {rsi_peak1:.1f}",
                        xy=(peak1_time, rsi_peak1),
                        xytext=(0, 15), textcoords='offset points',
                        bbox=dict(boxstyle='round', facecolor='white', alpha=0.8),
                        fontsize=9, ha='center')
        
        if rsi_peak2 and peak2_time in df.index:
            ax2.scatter([peak2_time], [rsi_peak2],
                       color='red', s=150, marker='o', zorder=5, edgecolors='darkred', linewidths=2)
            ax2.annotate(f"Peak2 RSI: {rsi_peak2:.1f}",
                        xy=(peak2_time, rsi_peak2),
                        xytext=(0, 15), textcoords='offset points',
                        bbox=dict(boxstyle='round', facecolor='white', alpha=0.8),
                        fontsize=9, ha='center')
    except Exception as e:
        print(f"Warning: Could not plot RSI markers: {e}")
    
    # Add divergence indicator
    if pattern_result['rsi_divergence']:
        ax2.text(0.02, 0.95, f'RSI DIVERGENCE: {pattern_result["rsi_divergence_value"]:.1f} points', 
                transform=ax2.transAxes, fontsize=10, verticalalignment='top',
                bbox=dict(boxstyle='round', facecolor='yellow', alpha=0.8))
    
    ax2.set_ylabel('RSI', fontsize=12)
    ax2.set_xlabel('Date', fontsize=12)
    ax2.legend(loc='upper left', fontsize=9)
    ax2.grid(True, alpha=0.3)
    ax2.set_ylim([0, 100])
    
    plt.tight_layout()
    
    # Save plot
    filename = f'output/pattern_verification_{symbol}_{datetime.now().strftime("%Y%m%d_%H%M%S")}.png'
    plt.savefig(filename, dpi=150, bbox_inches='tight')
    print(f"Chart saved: {filename}")
    plt.show()


def verify_pattern_details(symbol, pattern_result):
    """Print detailed pattern verification information"""
    print("\n" + "="*80)
    print(f"PATTERN VERIFICATION: {symbol}")
    print("="*80)
    
    print(f"\n📊 PATTERN METRICS:")
    print(f"  Peak 1: ${pattern_result['peak1_price']:.2f} on {pattern_result['peak1_time']}")
    print(f"  Peak 2: ${pattern_result['peak2_price']:.2f} on {pattern_result['peak2_time']}")
    print(f"  Price Difference: {pattern_result['price_diff_pct']:.2f}% (must be ≤ 3%)")
    print(f"   PASS" if pattern_result['price_diff_pct'] <= 3.0 else "  ✗ FAIL")
    
    trough_time = pattern_result.get('trough_time', 'N/A')
    print(f"\n  Trough: ${pattern_result['trough_price']:.2f} on {trough_time}")
    print(f"  Trough Depth: {pattern_result['trough_depth_pct']:.2f}% (must be ≥ 3%)")
    print(f"   PASS" if pattern_result['trough_depth_pct'] >= 3.0 else "  ✗ FAIL")
    
    candles_between = pattern_result.get('candles_between_peaks', pattern_result.get('candles_between', 'N/A'))
    print(f"\n  Candles Between Peaks: {candles_between} (must be ≥ 8)")
    if isinstance(candles_between, (int, float)):
        print(f"   PASS" if candles_between >= 8 else "  ✗ FAIL")
    
    print(f"\n📈 RSI ANALYSIS:")
    rsi_peak1 = pattern_result.get('rsi_peak1') or pattern_result.get('rsi_4h_peak1')
    rsi_peak2 = pattern_result.get('rsi_peak2') or pattern_result.get('rsi_4h_peak2')
    
    if rsi_peak1 and rsi_peak2:
        print(f"  RSI at Peak 1: {rsi_peak1:.2f}")
        print(f"  RSI at Peak 2: {rsi_peak2:.2f}")
        rsi_div_value = pattern_result.get('rsi_divergence_value', rsi_peak1 - rsi_peak2)
        print(f"  RSI Divergence: {rsi_div_value:.2f} points")
        print(f"  Divergence Detected: {'YES ' if pattern_result.get('rsi_divergence', False) else 'NO ✗'}")
        if pattern_result.get('rsi_divergence'):
            print(f"  (Peak1 RSI > Peak2 RSI by ≥ 2 points)")
    
    rsi_daily = pattern_result.get('rsi_daily')
    rsi_weekly = pattern_result.get('rsi_weekly')
    rsi_monthly = pattern_result.get('rsi_monthly')
    
    print(f"\n  RSI Daily: {rsi_daily if rsi_daily else 'N/A'}")
    print(f"  RSI Weekly: {rsi_weekly if rsi_weekly else 'N/A'}")
    print(f"  RSI Monthly: {rsi_monthly if rsi_monthly else 'N/A'}")
    
    print(f"\n📊 VOLUME ANALYSIS:")
    vol_peak1 = pattern_result.get('volume_peak1')
    vol_peak2 = pattern_result.get('volume_peak2')
    
    if vol_peak1 and vol_peak2:
        print(f"  Volume at Peak 1: {vol_peak1:,.0f}")
        print(f"  Volume at Peak 2: {vol_peak2:,.0f}")
        vol_decline = pattern_result.get('volume_decline_pct', 0)
        print(f"  Volume Decline: {vol_decline:.2f}%")
        print(f"  Volume Declining: {'YES ' if vol_decline >= 20 else 'NO ✗'}")
    else:
        print(f"  Volume data not available")
    
    print(f"\n🎯 SCORE BREAKDOWN:")
    print(f"  Pattern Detected: +1 point")
    
    rsi_div_score = 1 if pattern_result.get('rsi_divergence', False) else 0
    print(f"  RSI Divergence: +{rsi_div_score} point")
    
    daily_rsi = pattern_result.get('rsi_daily', 0)
    daily_score = 1 if daily_rsi and daily_rsi > 70 else 0
    print(f"  Daily RSI > 70: +{daily_score} point")
    
    weekly_rsi = pattern_result.get('rsi_weekly', 0)
    weekly_score = 1 if weekly_rsi and weekly_rsi > 70 else 0
    print(f"  Weekly RSI > 70: +{weekly_score} point")
    
    monthly_rsi = pattern_result.get('rsi_monthly', 0)
    monthly_score = 1 if monthly_rsi and monthly_rsi > 70 else 0
    print(f"  Monthly RSI > 70: +{monthly_score} point")
    
    vol_decline = pattern_result.get('volume_decline_pct', 0)
    vol_score = 1 if vol_decline >= 20 else 0
    print(f"  Volume Decline ≥20%: +{vol_score} point")
    
    total_score = pattern_result.get('score', 1 + rsi_div_score + daily_score + weekly_score + monthly_score + vol_score)
    print(f"\n  TOTAL SCORE: {total_score}/6")
    
    print("\n" + "="*80)


def main():
    """Main verification function"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Verify Pattern Detection Results')
    parser.add_argument('symbol', help='Symbol to verify (e.g., AAPL, META)')
    parser.add_argument('--plot', action='store_true', help='Generate visual plot')
    
    args = parser.parse_args()
    
    # Load config
    with open('config/settings.yaml', 'r') as f:
        config = yaml.safe_load(f)
    
    print(f"\n🔍 Verifying pattern detection for: {args.symbol}")
    
    # Run scanner
    scanner = DoubleTopScanner(config)
    result = scanner.scan_symbol(args.symbol, 'verification')
    
    if not result:
        print(f"\n❌ No pattern detected for {args.symbol}")
        return
    
    # Print detailed verification
    verify_pattern_details(args.symbol, result)
    
    # Generate visual plot if requested
    if args.plot:
        print("\n📊 Generating visual verification chart...")
        # Fetch data including primary timeframe
        timeframes = config['rsi']['timeframes'].copy()
        primary_tf = config['data']['primary_timeframe']
        if primary_tf not in timeframes:
            timeframes.insert(0, primary_tf)
        
        data = DataFetcher(config).fetch_multiple_timeframes(args.symbol, timeframes)
        plot_pattern(args.symbol, data, result, config)
    
    print("\n✅ Verification complete!")
    print(f"\n💡 TIP: Check the chart at https://finance.yahoo.com/chart/{args.symbol}")
    print(f"   Compare the peaks, trough, and RSI values manually")


if __name__ == "__main__":
    main()