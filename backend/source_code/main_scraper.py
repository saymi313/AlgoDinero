"""
Financial Data Curation Tool for CS4063 Assignment
Scrapes structured and unstructured financial data for next-day price prediction
"""

import argparse
import sys
import os
from datetime import datetime, date, timedelta
import logging

# Add the source_code directory to the path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from price_fetcher import PriceFetcher
from news_fetcher import NewsFetcher
from helper_utils import DataProcessor, setup_logging, validate_data_quality


class FinTechDataCuration:
    """
    Main class for orchestrating financial data curation
    """
    
    def __init__(self, output_dir: str = "output_data", evidence_dir: str = "sample_evidence"):
        """
        Initialize the FinTech Data Curation system
        
        Args:
            output_dir (str): Directory for output data files
            evidence_dir (str): Directory for sample evidence files
        """
        self.logger = logging.getLogger(__name__)
        self.price_fetcher = PriceFetcher()
        self.news_fetcher = NewsFetcher()
        self.data_processor = DataProcessor(output_dir, evidence_dir)
        
    def run_curation(self, exchange: str, ticker_symbol: str, num_days: int = 10) -> dict:
        """
        Run the complete data curation process
        
        Args:
            exchange (str): Stock exchange (e.g., NYSE, NASDAQ, PSX)
            ticker_symbol (str): Stock or crypto ticker symbol
            num_days (int): Number of days of data to fetch
            
        Returns:
            dict: Results of the curation process
        """
        try:
            self.logger.info(f"Starting data curation for {ticker_symbol} on {exchange}")
            
            # Validate ticker symbol
            if not self.price_fetcher.validate_ticker(ticker_symbol):
                self.logger.warning(f"Ticker {ticker_symbol} validation failed, proceeding anyway...")
            
            # Get ticker information
            ticker_info = self.price_fetcher.get_ticker_info(ticker_symbol)
            self.logger.info(f"Ticker info: {ticker_info}")
            
            # Fetch price data
            self.logger.info("Fetching price data...")
            price_data = self.price_fetcher.fetch_historical_prices(ticker_symbol, num_days)
            
            # Calculate date range for news
            end_date = date.today()
            start_date = end_date - timedelta(days=num_days + 5)  # Buffer for news
            
            # Fetch news data
            self.logger.info("Fetching news data...")
            news_data = self.news_fetcher.fetch_daily_news(ticker_symbol, start_date, end_date)
            
            # Merge datasets
            self.logger.info("Merging datasets...")
            merged_data = self.data_processor.merge_datasets(price_data, news_data)
            
            # Validate data quality
            quality_metrics = validate_data_quality(merged_data)
            self.logger.info(f"Data quality score: {quality_metrics['quality_score']}%")
            
            # Save data
            self.logger.info("Saving data...")
            csv_path, json_path = self.data_processor.save_data(merged_data, ticker_symbol)
            
            # Create data summary
            self.logger.info("Creating data summary...")
            summary_path = self.data_processor.create_data_summary(merged_data, ticker_symbol)
            
            # Save sample evidence
            sample_path = self.data_processor.save_sample_evidence(merged_data, ticker_symbol)
            
            # Generate summary statistics
            summary_stats = self.data_processor.generate_summary_stats(merged_data, ticker_symbol)
            
            # Prepare results
            results = {
                'success': True,
                'ticker_symbol': ticker_symbol,
                'exchange': exchange,
                'data_points': len(merged_data),
                'date_range': {
                    'start': str(merged_data['Date'].min()) if 'Date' in merged_data.columns else 'N/A',
                    'end': str(merged_data['Date'].max()) if 'Date' in merged_data.columns else 'N/A'
                },
                'files_created': {
                    'complete_csv': csv_path,
                    'complete_json': json_path,
                    'structured_csv': f"{ticker_symbol}_structured_data_*.csv",
                    'structured_json': f"{ticker_symbol}_structured_data_*.json",
                    'unstructured_csv': f"{ticker_symbol}_unstructured_data_*.csv",
                    'unstructured_json': f"{ticker_symbol}_unstructured_data_*.json",
                    'summary': summary_path,
                    'sample': sample_path
                },
                'quality_metrics': quality_metrics,
                'summary_stats': summary_stats,
                'ticker_info': ticker_info
            }
            
            self.logger.info(f"Data curation completed successfully for {ticker_symbol}")
            return results
            
        except Exception as e:
            self.logger.error(f"Data curation failed for {ticker_symbol}: {str(e)}")
            return {
                'success': False,
                'ticker_symbol': ticker_symbol,
                'exchange': exchange,
                'error': str(e)
            }
    
    def run_batch_curation(self, tickers: list, num_days: int = 10) -> dict:
        """
        Run curation for multiple tickers
        
        Args:
            tickers (list): List of ticker symbols
            num_days (int): Number of days of data to fetch
            
        Returns:
            dict: Batch results
        """
        batch_results = {
            'total_tickers': len(tickers),
            'successful': 0,
            'failed': 0,
            'results': []
        }
        
        for ticker in tickers:
            self.logger.info(f"Processing ticker: {ticker}")
            result = self.run_curation("AUTO", ticker, num_days)
            batch_results['results'].append(result)
            
            if result['success']:
                batch_results['successful'] += 1
            else:
                batch_results['failed'] += 1
        
        return batch_results


def parse_arguments():
    """
    Parse command line arguments
    
    Returns:
        argparse.Namespace: Parsed arguments
    """
    parser = argparse.ArgumentParser(
        description='Financial Data Curation Tool for AI/ML Tasks',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python main_scraper.py --exchange NASDAQ --ticker AAPL --days 10
  python main_scraper.py --exchange NYSE --ticker TSLA --days 15
  python main_scraper.py --ticker BTC-USD --days 7
  python main_scraper.py --batch AAPL,TSLA,BTC-USD --days 10
        """
    )
    
    # Individual ticker arguments
    parser.add_argument('--exchange', type=str, default='AUTO',
                       help='Stock exchange (NYSE, NASDAQ, PSX, etc.). Use AUTO for automatic detection.')
    parser.add_argument('--ticker', type=str,
                       help='Stock or crypto ticker symbol (e.g., AAPL, BTC-USD)')
    parser.add_argument('--days', type=int, default=10,
                       help='Number of days of historical data to fetch (default: 10)')
    
    # Batch processing
    parser.add_argument('--batch', type=str,
                       help='Comma-separated list of tickers for batch processing (e.g., AAPL,TSLA,BTC-USD)')
    
    # Output options
    parser.add_argument('--output-dir', type=str, default='output_data',
                       help='Directory for output files (default: output_data)')
    parser.add_argument('--evidence-dir', type=str, default='sample_evidence',
                       help='Directory for sample evidence files (default: sample_evidence)')
    
    # Logging options
    parser.add_argument('--log-level', type=str, default='INFO',
                       choices=['DEBUG', 'INFO', 'WARNING', 'ERROR'],
                       help='Logging level (default: INFO)')
    parser.add_argument('--quiet', action='store_true',
                       help='Suppress console output (only log to file)')
    
    return parser.parse_args()


def main():
    """
    Main function to run the financial data curation tool
    """
    # Parse command line arguments
    args = parse_arguments()
    
    # Setup logging
    setup_logging(args.log_level)
    logger = logging.getLogger(__name__)
    
    # Suppress console output if quiet mode
    if args.quiet:
        for handler in logging.getLogger().handlers:
            if isinstance(handler, logging.StreamHandler) and not isinstance(handler, logging.FileHandler):
                handler.setLevel(logging.ERROR)
    
    try:
        # Initialize the curation system
        curator = FinTechDataCuration(args.output_dir, args.evidence_dir)
        
        # Run batch processing if specified
        if args.batch:
            tickers = [ticker.strip() for ticker in args.batch.split(',')]
            logger.info(f"Starting batch processing for {len(tickers)} tickers")
            
            batch_results = curator.run_batch_curation(tickers, args.days)
            
            # Print batch summary
            print(f"\n{'='*60}")
            print(f"BATCH PROCESSING SUMMARY")
            print(f"{'='*60}")
            print(f"Total tickers processed: {batch_results['total_tickers']}")
            print(f"Successful: {batch_results['successful']}")
            print(f"Failed: {batch_results['failed']}")
            print(f"{'='*60}")
            
            # Print individual results
            for result in batch_results['results']:
                status = "✓ SUCCESS" if result['success'] else "✗ FAILED"
                print(f"{result['ticker_symbol']}: {status}")
                if not result['success']:
                    print(f"  Error: {result.get('error', 'Unknown error')}")
            
        # Run single ticker processing
        elif args.ticker:
            logger.info(f"Starting single ticker processing for {args.ticker}")
            
            result = curator.run_curation(args.exchange, args.ticker, args.days)
            
            # Print results
            print(f"\n{'='*60}")
            print(f"DATA CURATION RESULTS")
            print(f"{'='*60}")
            
            if result['success']:
                print(f"✓ SUCCESS: {result['ticker_symbol']}")
                print(f"Exchange: {result['exchange']}")
                print(f"Data points: {result['data_points']}")
                print(f"Date range: {result['date_range']['start']} to {result['date_range']['end']}")
                print(f"Quality score: {result['quality_metrics']['quality_score']}%")
                print(f"\nFiles created:")
                for file_type, path in result['files_created'].items():
                    if path:
                        print(f"  {file_type.upper()}: {path}")
                
                # Print sample data
                print(f"\nSample data (first 3 rows):")
                if 'complete_csv' in result['files_created'] and result['files_created']['complete_csv']:
                    try:
                        import pandas as pd
                        sample_data = pd.read_csv(result['files_created']['complete_csv'])
                        print(sample_data.head(3).to_string(index=False))
                    except Exception as e:
                        print(f"Could not display sample data: {e}")
            else:
                print(f"✗ FAILED: {result['ticker_symbol']}")
                print(f"Error: {result.get('error', 'Unknown error')}")
            
            print(f"{'='*60}")
        
        else:
            print("Error: Please specify either --ticker or --batch argument")
            print("Use --help for usage information")
            sys.exit(1)
    
    except KeyboardInterrupt:
        logger.info("Process interrupted by user")
        print("\nProcess interrupted by user")
        sys.exit(1)
    
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        print(f"Unexpected error: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    main()
