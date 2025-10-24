"""
Data Fetcher Module
Handles data retrieval from various sources (yfinance, Polygon, IBKR)
"""

import pandas as pd
import yfinance as yf
from datetime import datetime, timedelta
import time
import logging
import os

logger = logging.getLogger(__name__)


class DataFetcher:
    """Fetches market data from configured source"""
    
    def __init__(self, config):
        """
        Initialize data fetcher
        
        Args:
            config (dict): Configuration dictionary
        """
        self.config = config
        self.source = config['data']['source']
        self.primary_timeframe = config['data']['primary_timeframe']
        
        if self.source == 'polygon':
            self._init_polygon()
        elif self.source == 'ibkr':
            self._init_ibkr()
    
    def _init_polygon(self):
        """Initialize Polygon.io client"""
        try:
            from polygon import RESTClient
            api_key = self.config['data'].get('polygon_api_key') or os.environ.get('POLYGON_API_KEY')
            if not api_key:
                raise ValueError("Polygon API key not found in config or environment")
            self.polygon_client = RESTClient(api_key)
            logger.info("Polygon.io client initialized")
        except ImportError:
            logger.error("polygon-api-client not installed. Run: pip install polygon-api-client")
            raise
    
    def _init_ibkr(self):
        """Initialize Interactive Brokers client"""
        try:
            from ib_insync import IB
            self.ib = IB()
            host = self.config['data'].get('ibkr_host', '127.0.0.1')
            port = self.config['data'].get('ibkr_port', 7497)
            client_id = self.config['data'].get('ibkr_client_id', 1)
            self.ib.connect(host, port, clientId=client_id)
            logger.info(f"Connected to IBKR at {host}:{port}")
        except ImportError:
            logger.error("ib-insync not installed. Run: pip install ib-insync")
            raise
        except Exception as e:
            logger.error(f"Failed to connect to IBKR: {e}")
            raise
    
    def fetch_ohlcv(self, symbol, timeframe, periods=100):
        if self.source == 'yfinance':
            return self._fetch_yfinance(symbol, timeframe, periods)
        elif self.source == 'polygon':
            return self._fetch_polygon(symbol, timeframe, periods)
        elif self.source == 'ibkr':
            return self._fetch_ibkr(symbol, timeframe, periods)
        else:
            raise ValueError(f"Unknown data source: {self.source}")

    def _fetch_yfinance(self, symbol, timeframe, periods=100):
        try:
            interval_map = {
                '1d': '1d',
                '1wk': '1wk',
                '1mo': '1mo',
                '1h': '1h',
                '4h': '1h',
            }
            
            interval = interval_map.get(timeframe, '1d')
            
            primary_tf = self.config['data']['primary_timeframe']
            is_primary = (timeframe == primary_tf)
            
            if is_primary:
                if timeframe == '1mo':
                    period_str = f"{periods}mo"
                elif timeframe == '1wk':
                    period_str = f"{periods * 7}d"
                elif timeframe in ['1h', '4h']:
                    period_str = "60d"
                else:
                    period_str = f"{periods}d"
            else:
                # BUG FIX: Fetch more data for non-primary timeframes to ensure enough for RSI calculation
                # RSI needs at least 15 periods, so fetch extra to be safe
                if timeframe == '1mo':
                    period_str = "24mo"  # Was 14mo - not enough for RSI
                elif timeframe == '1wk':
                    period_str = "150d"  # Was 98d - fetch ~21 weeks
                elif timeframe == '1d':
                    period_str = "30d"  # Was 14d - not enough for RSI (needs 15+)
                elif timeframe in ['1h', '4h']:
                    period_str = "60d"
                else:
                    period_str = "60d"
            
            ticker = yf.Ticker(symbol)
            df = ticker.history(period=period_str, interval=interval)
            
            if df.empty:
                logger.warning(f"No data returned for {symbol}")
                return None
            
            if timeframe == '4h':
                df = df.resample('4h').agg({
                    'Open': 'first',
                    'High': 'max',
                    'Low': 'min',
                    'Close': 'last',
                    'Volume': 'sum'
                }).dropna()
            
            required_cols = ['Open', 'High', 'Low', 'Close', 'Volume']
            if not all(col in df.columns for col in required_cols):
                logger.warning(f"Missing required columns for {symbol}")
                return None
            
            df = df[required_cols].tail(periods)
            
            time.sleep(0.1)
            
            return df
            
        except Exception as e:
            logger.error(f"Error fetching {symbol} from yfinance: {e}")
            return None

    def _fetch_polygon(self, symbol, timeframe, periods=100):
        """
        Fetch data using Polygon.io
        
        Note: Implement this when you have Polygon API access
        """
        logger.warning("Polygon.io fetcher not yet implemented")
        return None
    
    def _fetch_ibkr(self, symbol, timeframe, periods=100):
        """
        Fetch data using Interactive Brokers
        
        Note: Implement this when you have IBKR access
        """
        logger.warning("IBKR fetcher not yet implemented")
        return None
    
    def fetch_multiple_timeframes(self, symbol, timeframes=None):
        """
        Fetch data for multiple timeframes at once
        
        Args:
            symbol (str): Ticker symbol
            timeframes (list): List of timeframes (default from config)
        
        Returns:
            dict: Dictionary with timeframe as key and DataFrame as value
        """
        if timeframes is None:
            timeframes = self.config['rsi']['timeframes']
        
        data = {}
        for tf in timeframes:
            df = self.fetch_ohlcv(symbol, tf)
            if df is not None:
                data[tf] = df
        
        return data
    
    def get_sp500_list(self):
        """
        Get current S&P 500 constituents
        
        Returns:
            list: List of ticker symbols
        """
        try:
            # Fetch from Wikipedia
            url = 'https://en.wikipedia.org/wiki/List_of_S%26P_500_companies'
            tables = pd.read_html(url)
            sp500_table = tables[0]
            tickers = sp500_table['Symbol'].tolist()
            
            # Clean tickers (replace . with -)
            tickers = [t.replace('.', '-') for t in tickers]
            
            logger.info(f"Fetched {len(tickers)} S&P 500 symbols")
            return tickers
            
        except Exception as e:
            logger.error(f"Error fetching S&P 500 list: {e}")
            return []


if __name__ == "__main__":
    # Test data fetcher
    import yaml
    import sys
    
    logging.basicConfig(level=logging.INFO)
    
    # Load config
    with open('../config/settings.yaml', 'r') as f:
        config = yaml.safe_load(f)
    
    fetcher = DataFetcher(config)
    
    # Test single symbol
    print("Testing AAPL daily data...")
    df = fetcher.fetch_ohlcv('AAPL', '1d', periods=50)
    if df is not None:
        print(f"Fetched {len(df)} rows")
        print(df.tail())
    
    # Test multiple timeframes
    print("\nTesting multiple timeframes for AAPL...")
    data = fetcher.fetch_multiple_timeframes('AAPL', ['1d', '1wk'])
    for tf, df in data.items():
        print(f"{tf}: {len(df)} rows")
    
    # Test S&P 500 list
    print("\nTesting S&P 500 list fetch...")
    sp500 = fetcher.get_sp500_list()
    print(f"Fetched {len(sp500)} symbols")
    print(f"First 10: {sp500[:10]}")
