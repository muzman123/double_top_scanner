"""
Scanner Module - IMPROVED VERSION
Main orchestration logic for scanning assets and detecting patterns
Changes: Added safety checks, pattern confidence tracking, better error handling
"""

import pandas as pd
import json
import logging
from datetime import datetime
from src.data_fetcher import DataFetcher
from src.pattern_detector import DoubleTopDetector
from src.indicators import calculate_rsi

logger = logging.getLogger(__name__)


class DoubleTopScanner:
    """Main scanner class that orchestrates the scanning process"""
    
    def __init__(self, config):
        """
        Initialize scanner
        
        Args:
            config (dict): Configuration dictionary
        """
        self.config = config
        self.data_fetcher = DataFetcher(config)
        self.pattern_detector = DoubleTopDetector(config)
        self.min_score = config['scoring']['min_score_to_report']
        self.volume_decline_threshold = config['scoring']['volume_decline_threshold']
        
        # Load asset universe
        self.assets = self._load_assets()
    
    def _load_assets(self):
        """
        Load asset universe from config file
        
        Returns:
            dict: Dictionary with asset types and symbols
        """
        config_file = self.config['assets']['config_file']
        
        try:
            with open(config_file, 'r') as f:
                assets = json.load(f)
            
            # Optionally auto-update S&P 500 list
            if self.config['assets'].get('sp500_auto_update', False):
                logger.info("Auto-updating S&P 500 list...")
                sp500_list = self.data_fetcher.get_sp500_list()
                if sp500_list:
                    assets['stocks'] = sp500_list
            
            total = len(assets.get('stocks', [])) + len(assets.get('indices', [])) + len(assets.get('commodities', []))
            logger.info(f"Loaded {total} assets from {config_file}")
            
            return assets
            
        except Exception as e:
            logger.error(f"Error loading assets: {e}")
            return {'stocks': [], 'indices': [], 'commodities': []}
    
    def scan_all(self):
        """
        Scan all assets for double top patterns
        
        Returns:
            list: List of candidates with scores >= min_score
        """
        results = []
        stats = {
            'total_scanned': 0,
            'patterns_found': 0,
            'patterns_passed_confidence': 0,
            'patterns_passed_score': 0,
            'errors': 0
        }
        
        # Flatten asset list
        all_symbols = []
        for asset_type, symbols in self.assets.items():
            if asset_type.startswith('_'):  # Skip comments
                continue
            for symbol in symbols:
                all_symbols.append((symbol, asset_type))
        
        # Apply max assets limit if set (for testing)
        max_assets = self.config['assets'].get('max_assets_to_scan')
        if max_assets:
            all_symbols = all_symbols[:max_assets]
            logger.info(f"Limiting scan to {max_assets} assets for testing")
        
        logger.info(f"Scanning {len(all_symbols)} assets...")
        
        # Scan each symbol
        for idx, (symbol, asset_type) in enumerate(all_symbols):
            if (idx + 1) % 10 == 0:
                logger.info(f"Progress: {idx + 1}/{len(all_symbols)} - Found {len(results)} candidates so far")
            
            try:
                stats['total_scanned'] += 1
                result = self.scan_symbol(symbol, asset_type)
                
                if result:
                    stats['patterns_found'] += 1
                    
                    # Check confidence (should already be filtered, but double check)
                    if result.get('pattern_confidence', 0) >= self.config['pattern'].get('min_confidence', 40):
                        stats['patterns_passed_confidence'] += 1
                        
                        # Check score
                        if result['score'] >= self.min_score:
                            stats['patterns_passed_score'] += 1
                            results.append(result)
                            status_emoji = "⚠️" if result['pattern_status'] == 'forming' else ""
                            status_text = result['pattern_status'].upper()
                            logger.info(f"{status_emoji} {symbol}: Score {result['score']}/6, Status: {status_text}, Confidence {result['pattern_confidence']:.0f}%")
            
            except Exception as e:
                stats['errors'] += 1
                logger.error(f"Error scanning {symbol}: {e}")
                continue
        
        logger.info(f"Scan complete!")
        logger.info(f"  Total scanned: {stats['total_scanned']}")
        logger.info(f"  Patterns detected: {stats['patterns_found']} ({stats['patterns_found']/stats['total_scanned']*100:.1f}%)")
        logger.info(f"  Passed confidence filter: {stats['patterns_passed_confidence']}")
        logger.info(f"  Passed score filter: {stats['patterns_passed_score']}")
        logger.info(f"  Final candidates: {len(results)}")
        logger.info(f"  Errors: {stats['errors']}")
        
        # Sort by score (descending) then by symbol
        results.sort(key=lambda x: (-x['score'], x['symbol']))
        
        return results
    
    def scan_symbol(self, symbol, asset_type):
        """
        Scan a single symbol for double top pattern
        
        Args:
            symbol (str): Ticker symbol
            asset_type (str): Asset type (stocks, indices, commodities)
        
        Returns:
            dict or None: Candidate details if pattern found with sufficient score
        """
        # Fetch multi-timeframe data
        timeframes = self.config['rsi']['timeframes']
        data = self.data_fetcher.fetch_multiple_timeframes(symbol, timeframes)
        
        if not data:
            logger.debug(f"{symbol}: No data available")
            return None
        
        # Primary timeframe for pattern detection
        primary_tf = self.config['data']['primary_timeframe']
        if primary_tf not in data:
            logger.warning(f"{symbol}: Primary timeframe {primary_tf} not available")
            return None
        
        primary_df = data[primary_tf]
        
        # Check sufficient data
        if len(primary_df) < self.config['pattern']['lookback_candles']:
            logger.debug(f"{symbol}: Insufficient data ({len(primary_df)} bars)")
            return None
        
        # Detect double top pattern
        pattern = self.pattern_detector.detect(primary_df)
        
        if not pattern:
            return None
        
        # IMPROVEMENT: Safety check for pattern confidence
        # (Detector should already filter this, but double-check)
        pattern_confidence = pattern.get('confidence', 0)
        min_confidence = self.config['pattern'].get('min_confidence', 40)
        
        if pattern_confidence < min_confidence:
            logger.debug(f"{symbol}: Pattern confidence {pattern_confidence:.0f}% < {min_confidence}%")
            return None
        
        # Calculate RSI for all timeframes
        rsi_values = {}
        for tf in timeframes:
            if tf in data:
                try:
                    rsi = calculate_rsi(data[tf]['Close'], period=self.config['rsi']['period'])
                    if not rsi.empty and not pd.isna(rsi.iloc[-1]):
                        rsi_values[tf] = float(rsi.iloc[-1])
                    else:
                        rsi_values[tf] = None
                except Exception as e:
                    logger.debug(f"{symbol}: Error calculating {tf} RSI: {e}")
                    rsi_values[tf] = None
            else:
                rsi_values[tf] = None
        
        # Calculate score
        score = self._calculate_score(pattern, rsi_values)
        
        # Get current price and change
        current_price = float(primary_df['Close'].iloc[-1])
        prev_price = float(primary_df['Close'].iloc[-2]) if len(primary_df) > 1 else current_price
        price_change_pct = ((current_price - prev_price) / prev_price) * 100
        
        # Build result
        result = {
            'date': datetime.now().strftime('%Y-%m-%d'),
            'symbol': symbol,
            'asset_type': asset_type,
            'score': score,
            'pattern_confidence': pattern_confidence,
            'pattern_status': pattern.get('status', 'confirmed'),  # 'forming' or 'confirmed'
            'detection_mode': pattern.get('mode', 'detection'),  # 'prediction' or 'detection'
            'current_price': current_price,
            'price_change_pct': price_change_pct,
            
            # Pattern details
            'peak1_price': pattern['peak1_price'],
            'peak1_time': str(pattern['peak1_time']),
            'peak2_price': pattern['peak2_price'],
            'peak2_time': str(pattern['peak2_time']),
            'price_diff_pct': pattern['price_diff_pct'],
            'trough_price': pattern['trough_price'],
            'trough_depth_pct': pattern['trough_depth_pct'],
            'neckline': pattern['neckline'],
            'candles_between_peaks': pattern['candles_between'],
            
            # RSI details
            'rsi_4h_current': rsi_values.get('4h'),
            'rsi_4h_peak1': pattern.get('rsi_peak1'),  # IMPROVEMENT: Use .get() for safety
            'rsi_4h_peak2': pattern.get('rsi_peak2'),
            'rsi_divergence': pattern.get('rsi_divergence', False),
            'rsi_divergence_value': pattern.get('rsi_divergence_value', 0),
            'rsi_daily': rsi_values.get('1d'),
            'rsi_weekly': rsi_values.get('1wk'),
            'rsi_monthly': rsi_values.get('1mo'),
            
            # Volume details
            'volume_peak1': pattern.get('volume_peak1'),
            'volume_peak2': pattern.get('volume_peak2'),
            'volume_decline_pct': pattern.get('volume_decline_pct', 0),
            
            # Chart link
            'chart_link': f"https://finance.yahoo.com/chart/{symbol}"
        }
        
        return result
    
    def _calculate_score(self, pattern, rsi_values):
        """
        Calculate 0-6 score based on pattern and RSI conditions
        
        Args:
            pattern (dict): Pattern details
            rsi_values (dict): RSI values for different timeframes
        
        Returns:
            int: Score (0-6)
        """
        score = 0
        
        # 1. Double top pattern detected (+1)
        # IMPROVEMENT: Use .get() for safety
        if pattern.get('found', False):
            score += 1
        
        # 2. RSI divergence (+1)
        if pattern.get('rsi_divergence', False):
            score += 1
        
        # 3. Daily RSI > 70 (+1)
        daily_rsi = rsi_values.get('1d')
        if daily_rsi and daily_rsi > self.config['rsi']['overbought_threshold']:
            score += 1
        
        # 4. Weekly RSI > 70 (+1)
        weekly_rsi = rsi_values.get('1wk')
        if weekly_rsi and weekly_rsi > self.config['rsi']['overbought_threshold']:
            score += 1
        
        # 5. Monthly RSI > 70 (+1)
        monthly_rsi = rsi_values.get('1mo')
        if monthly_rsi and monthly_rsi > self.config['rsi']['overbought_threshold']:
            score += 1
        
        # 6. Volume decline 20%+ (+1)
        volume_decline = pattern.get('volume_decline_pct', 0)
        if volume_decline >= self.volume_decline_threshold:
            score += 1
        
        return score


if __name__ == "__main__":
    # Test scanner
    import yaml
    
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Load config
    with open('../config/settings.yaml', 'r') as f:
        config = yaml.safe_load(f)
    
    # Override for testing
    config['assets']['max_assets_to_scan'] = 10  # Test with just 10 symbols
    
    # Create scanner and run
    scanner = DoubleTopScanner(config)
    
    # Test single symbol first
    print("\n" + "="*80)
    print("TESTING SINGLE SYMBOL: NVDA")
    print("="*80)
    result = scanner.scan_symbol('NVDA', 'stocks')
    if result:
        print(f"✅ Found pattern!")
        print(f"  Score: {result['score']}/6")
        print(f"  Confidence: {result['pattern_confidence']:.0f}%")
        print(f"  Peak 1: ${result['peak1_price']:.2f}")
        print(f"  Peak 2: ${result['peak2_price']:.2f}")
        print(f"  Trough: ${result['trough_price']:.2f} ({result['trough_depth_pct']:.1f}% decline)")
    else:
        print("❌ No pattern found in NVDA")
    
    # Run full scan
    print("\n" + "="*80)
    print("RUNNING FULL SCAN")
    print("="*80)
    results = scanner.scan_all()
    
    print("\n" + "="*80)
    print(f"SCAN RESULTS: {len(results)} candidates found")
    print("="*80)
    
    if results:
        for result in results:
            print(f"\n{result['symbol']} ({result['asset_type']}) - Score: {result['score']}/6, Confidence: {result['pattern_confidence']:.0f}%")
            print(f"  Current Price: ${result['current_price']:.2f}")
            print(f"  Peak 1: ${result['peak1_price']:.2f}, Peak 2: ${result['peak2_price']:.2f}")
            print(f"  Trough: ${result['trough_price']:.2f} ({result['trough_depth_pct']:.1f}% decline)")
            print(f"  RSI Daily: {result['rsi_daily']:.1f if result['rsi_daily'] else 'N/A'}")
            print(f"  Chart: {result['chart_link']}")
    else:
        print("\nNo patterns found!")
        print("Troubleshooting tips:")
        print("  1. Check config: trough_depth_pct should be 5.0 (not 3.0)")
        print("  2. Check config: min_confidence should be 40 (not 60)")
        print("  3. Try even more lenient: trough_depth_pct = 3.0")
        print("  4. Set log_level to DEBUG to see rejection reasons")