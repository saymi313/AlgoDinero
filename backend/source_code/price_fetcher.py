"""
Price Fetcher Module for Financial Data Curation
Handles structured financial data retrieval and processing
"""

import pandas as pd
import yfinance as yf
import logging
from datetime import datetime, timedelta
from typing import Optional, Tuple
from tenacity import retry, stop_after_attempt, wait_exponential


class PriceFetcher:
    """
    A class to fetch and process historical price data for stocks and cryptocurrencies
    """
    
    def __init__(self):
        """Initialize the PriceFetcher with logging configuration"""
        self.logger = logging.getLogger(__name__)
        
    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
    def fetch_historical_prices(self, ticker_symbol: str, num_days: int = 10) -> pd.DataFrame:
        """
        Fetch historical price data for a given ticker symbol
        
        Args:
            ticker_symbol (str): Stock or crypto ticker symbol (e.g., 'AAPL', 'BTC-USD')
            num_days (int): Number of days of historical data to fetch
            
        Returns:
            pd.DataFrame: DataFrame with OHLCV data and calculated indicators
            
        Raises:
            Exception: If data fetching fails after retries
        """
        try:
            self.logger.info(f"Fetching {num_days} days of price data for {ticker_symbol}")
            
            # Calculate start date (add buffer for weekends/holidays)
            end_date = datetime.now()
            start_date = end_date - timedelta(days=num_days + 10)  # Buffer for weekends
            
            # Fetch data using yfinance
            ticker = yf.Ticker(ticker_symbol)
            price_data = ticker.history(start=start_date, end=end_date)
            
            if price_data.empty:
                raise ValueError(f"No data found for ticker {ticker_symbol}")
            
            # Keep only the most recent num_days of data
            price_data = price_data.tail(num_days)
            
            # Reset index to make Date a column
            price_data = price_data.reset_index()
            price_data['Date'] = pd.to_datetime(price_data['Date']).dt.date
            
            # Calculate additional indicators
            price_data = self._calculate_indicators(price_data)
            
            self.logger.info(f"Successfully fetched {len(price_data)} days of data for {ticker_symbol}")
            return price_data
            
        except Exception as e:
            self.logger.error(f"Failed to fetch price data for {ticker_symbol}: {str(e)}")
            raise
    
    def _calculate_indicators(self, price_data: pd.DataFrame) -> pd.DataFrame:
        """
        Calculate technical indicators for the price data
        
        Args:
            price_data (pd.DataFrame): Raw price data with OHLCV columns
            
        Returns:
            pd.DataFrame: Price data with additional calculated indicators
        """
        try:
            # Ensure we have the required columns
            required_columns = ['Open', 'High', 'Low', 'Close', 'Volume']
            for col in required_columns:
                if col not in price_data.columns:
                    raise ValueError(f"Missing required column: {col}")
            
            # Calculate previous close (shifted by 1 day)
            price_data['Prev_Close'] = price_data['Close'].shift(1)
            
            # Calculate daily return
            price_data['Daily_Return'] = (price_data['Close'] - price_data['Prev_Close']) / price_data['Prev_Close']
            
            # Calculate 5-day Simple Moving Average
            price_data['SMA_5'] = price_data['Close'].rolling(window=5, min_periods=1).mean()
            
            # Calculate 5-day rolling volatility (standard deviation of returns)
            price_data['Volatility_5'] = price_data['Daily_Return'].rolling(window=5, min_periods=1).std()
            
            # Handle NaN values in the first row (avoid chained assignment warnings)
            price_data['Prev_Close'] = price_data['Prev_Close'].fillna(price_data['Close'])
            price_data['Daily_Return'] = price_data['Daily_Return'].fillna(0)
            
            # Round numerical columns to 4 decimal places for consistency
            numerical_columns = ['Open', 'High', 'Low', 'Close', 'Volume', 'Prev_Close', 
                               'Daily_Return', 'SMA_5', 'Volatility_5']
            for col in numerical_columns:
                if col in price_data.columns:
                    price_data[col] = price_data[col].round(4)
            
            self.logger.info("Successfully calculated technical indicators")
            return price_data
            
        except Exception as e:
            self.logger.error(f"Error calculating indicators: {str(e)}")
            raise
    
    def get_ticker_info(self, ticker_symbol: str) -> dict:
        """
        Get basic information about a ticker symbol
        
        Args:
            ticker_symbol (str): Stock or crypto ticker symbol
            
        Returns:
            dict: Dictionary containing ticker information
        """
        try:
            ticker = yf.Ticker(ticker_symbol)
            info = ticker.info
            
            return {
                'symbol': ticker_symbol,
                'name': info.get('longName', 'Unknown'),
                'sector': info.get('sector', 'Unknown'),
                'industry': info.get('industry', 'Unknown'),
                'market_cap': info.get('marketCap', 'Unknown'),
                'currency': info.get('currency', 'USD')
            }
            
        except Exception as e:
            self.logger.warning(f"Could not fetch ticker info for {ticker_symbol}: {str(e)}")
            return {
                'symbol': ticker_symbol,
                'name': 'Unknown',
                'sector': 'Unknown',
                'industry': 'Unknown',
                'market_cap': 'Unknown',
                'currency': 'USD'
            }
    
    def validate_ticker(self, ticker_symbol: str) -> bool:
        """
        Validate if a ticker symbol exists and has data
        
        Args:
            ticker_symbol (str): Stock or crypto ticker symbol
            
        Returns:
            bool: True if ticker is valid, False otherwise
        """
        try:
            ticker = yf.Ticker(ticker_symbol)
            # Try to get recent data
            data = ticker.history(period="5d")
            return not data.empty
        except:
            return False


def main():
    """
    Test function for the PriceFetcher module
    """
    # Configure logging
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    
    # Test the PriceFetcher
    fetcher = PriceFetcher()
    
    # Test with AAPL
    try:
        print("Testing PriceFetcher with AAPL...")
        aapl_data = fetcher.fetch_historical_prices('AAPL', 10)
        print(f"AAPL data shape: {aapl_data.shape}")
        print(f"AAPL columns: {list(aapl_data.columns)}")
        print("\nFirst 3 rows:")
        print(aapl_data.head(3))
        
        # Test ticker info
        info = fetcher.get_ticker_info('AAPL')
        print(f"\nAAPL Info: {info}")
        
    except Exception as e:
        print(f"Error testing AAPL: {e}")


if __name__ == "__main__":
    main()
