#!/usr/bin/env python3
"""
Double Top Scanner - Main Entry Point
Run this script to execute the scanner
"""

import os
import sys
import yaml
import logging
from datetime import datetime
from src.scanner import DoubleTopScanner
from src.notifier import Notifier


def setup_logging(config):
    """Set up logging configuration"""
    log_level = config['output']['log_level']
    log_path = config['output']['log_path']
    
    # Create log directory if it doesn't exist
    os.makedirs(os.path.dirname(log_path), exist_ok=True)
    
    # Configure logging
    logging.basicConfig(
        level=getattr(logging, log_level),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_path),
            logging.StreamHandler(sys.stdout)
        ]
    )
    
    return logging.getLogger(__name__)


def load_config():
    """Load configuration from YAML file"""
    config_path = 'config/settings.yaml'
    
    if not os.path.exists(config_path):
        print(f"Error: Configuration file not found: {config_path}")
        sys.exit(1)
    
    with open(config_path, 'r') as f:
        config = yaml.safe_load(f)
    
    return config


def run_scan():
    """Main scan execution function"""
    # Load configuration
    print("Loading configuration...")
    config = load_config()
    
    # Setup logging
    logger = setup_logging(config)
    logger.info("="*80)
    logger.info("DOUBLE TOP SCANNER STARTED")
    logger.info(f"Time: {datetime.now()}")
    logger.info("="*80)
    
    try:
        # Initialize scanner
        logger.info("Initializing scanner...")
        scanner = DoubleTopScanner(config)
        
        # Run scan
        logger.info("Starting scan...")
        start_time = datetime.now()
        results = scanner.scan_all()
        end_time = datetime.now()
        
        scan_duration = (end_time - start_time).total_seconds()
        logger.info(f"Scan completed in {scan_duration:.1f} seconds")
        logger.info(f"Found {len(results)} candidates with score >= {config['scoring']['min_score_to_report']}")
        
        # Send notifications
        logger.info("Sending notifications...")
        notifier = Notifier(config)
        notifier.notify(results)
        
        logger.info("="*80)
        logger.info("SCAN COMPLETED SUCCESSFULLY")
        logger.info("="*80)
        
        return 0
        
    except KeyboardInterrupt:
        logger.warning("Scan interrupted by user")
        return 1
        
    except Exception as e:
        logger.error(f"Error during scan: {e}", exc_info=True)
        return 1


def main():
    """Main entry point with argument parsing"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Double Top Scanner - Automated Pattern Detection')
    parser.add_argument('--config', '-c', help='Path to config file', default='config/settings.yaml')
    parser.add_argument('--test', '-t', action='store_true', help='Run in test mode (scan 100 symbols)')
    parser.add_argument('--symbol', '-s', help='Scan single symbol')
    
    args = parser.parse_args()
    
    # Override config path if provided
    if args.config != 'config/settings.yaml':
        global config_path
        config_path = args.config
    
    # Test mode - handle separately with direct initialization
    if args.test:
        print("Running in TEST mode (scanning 100 stocks from S&P 500)...")
        print("Fetching S&P 500 stock list from Wikipedia...")
        
        config = load_config()
        
        # Fetch S&P 500 list directly
        try:
            from src.data_fetcher import DataFetcher
            temp_fetcher = DataFetcher(config)
            sp500_stocks = temp_fetcher.get_sp500_list()
            
            if sp500_stocks and len(sp500_stocks) > 0:
                print(f" Fetched {len(sp500_stocks)} S&P 500 stocks")
                
                # Load current asset universe
                import json
                with open('config/asset_universe.json', 'r') as f:
                    assets = json.load(f)
                
                # Replace stocks with S&P 500 list
                assets['stocks'] = sp500_stocks
                
                # Save temporarily
                with open('config/asset_universe.json', 'w') as f:
                    json.dump(assets, f, indent=2)
                
                print(" Updated asset universe with S&P 500 stocks")
                print(f"Scanning first 100 stocks...")
            else:
                print("Could not fetch S&P 500 list, using default asset list")
        except Exception as e:
            print(f"Error fetching S&P 500: {e}")
            print("Installing required package...")
            import subprocess
            subprocess.run([sys.executable, "-m", "pip", "install", "lxml"], check=False)
            print("Please run the test again")
            return 1
        
        # Modify config for test mode
        config['assets']['max_assets_to_scan'] = 100
        config['output']['log_level'] = 'INFO'
        
        # Setup logging
        logger = setup_logging(config)
        logger.info("="*80)
        logger.info("DOUBLE TOP SCANNER - TEST MODE (100 stocks)")
        logger.info(f"Time: {datetime.now()}")
        logger.info("="*80)
        
        try:
            # Initialize scanner with modified config
            logger.info("Initializing scanner...")
            scanner = DoubleTopScanner(config)
            
            # Run scan
            logger.info("Starting scan of 100 stocks...")
            start_time = datetime.now()
            results = scanner.scan_all()
            end_time = datetime.now()
            
            scan_duration = (end_time - start_time).total_seconds()
            logger.info(f"Scan completed in {scan_duration:.1f} seconds")
            logger.info(f"Found {len(results)} candidates with score >= {config['scoring']['min_score_to_report']}")
            
            # Send notifications
            logger.info("Sending notifications...")
            notifier = Notifier(config)
            notifier.notify(results)
            
            logger.info("="*80)
            logger.info("TEST SCAN COMPLETED")
            logger.info("="*80)
            
            return 0
            
        except KeyboardInterrupt:
            logger.warning("Scan interrupted by user")
            return 1
        except Exception as e:
            logger.error(f"Error during scan: {e}", exc_info=True)
            return 1
    
    # Single symbol mode
    if args.symbol:
        print(f"Scanning single symbol: {args.symbol}")
        config = load_config()
        logger = setup_logging(config)
        
        scanner = DoubleTopScanner(config)
        result = scanner.scan_symbol(args.symbol, 'manual')
        
        if result:
            status = result.get('pattern_status', 'confirmed')
            mode = result.get('detection_mode', 'detection')
            status_emoji = "" if status == 'forming' else ""
            
            print(f"\n{status_emoji} Pattern found! Score: {result['score']}/6")
            print(f"  Mode: {mode.upper()}")
            print(f"  Status: {status.upper()} {'(neckline NOT broken yet - early warning)' if status == 'forming' else '(neckline broken - confirmed reversal)'}")
            print(f"  Peak 1: ${result['peak1_price']:.2f} on {result.get('peak1_time', 'N/A')}")
            print(f"  Peak 2: ${result['peak2_price']:.2f} on {result.get('peak2_time', 'N/A')}")
            print(f"  Trough: ${result['trough_price']:.2f} ({result['trough_depth_pct']:.1f}% depth)")
            print(f"  Neckline: ${result.get('neckline', 'N/A'):.2f}")
            print(f"  Candles Between Peaks: {result.get('candles_between_peaks', 'N/A')}")
            print(f"  RSI Daily: {result['rsi_daily'] if result['rsi_daily'] else 'N/A'}")
            print(f"  RSI Weekly: {result['rsi_weekly'] if result['rsi_weekly'] else 'N/A'}")
            print(f"  RSI Monthly: {result['rsi_monthly'] if result['rsi_monthly'] else 'N/A'}")
            print(f"  RSI Divergence: {'Yes' if result['rsi_divergence'] else 'No'}")
        else:
            print("✗ No pattern detected")
        
        return 0
    
    # Normal scan
    return run_scan()


if __name__ == "__main__":
    sys.exit(main())
