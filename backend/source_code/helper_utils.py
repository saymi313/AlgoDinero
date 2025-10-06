"""
Helper Utilities Module for Financial Data Curation
Handles data alignment, saving, logging, and visualization
"""

import pandas as pd
import numpy as np
import json
import logging
import os
from datetime import datetime, date
from typing import Tuple, Optional


class DataProcessor:
    """
    A class to handle data processing, alignment, and visualization
    """
    
    def __init__(self, output_dir: str = "output_data", evidence_dir: str = "sample_evidence"):
        """
        Initialize the DataProcessor
        
        Args:
            output_dir (str): Directory for output data files
            evidence_dir (str): Directory for sample evidence files
        """
        self.logger = logging.getLogger(__name__)
        self.output_dir = output_dir
        self.evidence_dir = evidence_dir
        
        # Create directories if they don't exist
        os.makedirs(output_dir, exist_ok=True)
        os.makedirs(evidence_dir, exist_ok=True)
    
    def merge_datasets(self, price_df: pd.DataFrame, news_df: pd.DataFrame) -> pd.DataFrame:
        """
        Merge price and news datasets on Date column with proper validation
        
        Args:
            price_df (pd.DataFrame): Price data DataFrame
            news_df (pd.DataFrame): News data DataFrame
            
        Returns:
            pd.DataFrame: Merged dataset with aligned data
        """
        try:
            self.logger.info("Merging price and news datasets")
            
            # Ensure Date columns are datetime
            price_df['Date'] = pd.to_datetime(price_df['Date']).dt.date
            news_df['Date'] = pd.to_datetime(news_df['Date']).dt.date
            
            # Filter out invalid price data (rows with all zeros or NaN)
            price_df = self._validate_price_data(price_df)
            news_df = self._validate_news_data(news_df)
            
            # Merge on Date column
            merged_df = pd.merge(price_df, news_df, on='Date', how='outer')
            
            # Sort by date
            merged_df = merged_df.sort_values('Date').reset_index(drop=True)
            
            # Forward fill missing values for news data (weekends/holidays)
            news_columns = ['Daily_Headlines', 'Headline_Count', 'Mean_Sentiment_Score']
            for col in news_columns:
                if col in merged_df.columns:
                    merged_df[col] = merged_df[col].ffill()
            
            # Fill remaining NaN values appropriately
            merged_df = self._fill_missing_values(merged_df)
            
            self.logger.info(f"Successfully merged datasets. Final shape: {merged_df.shape}")
            return merged_df
            
        except Exception as e:
            self.logger.error(f"Error merging datasets: {str(e)}")
            raise
    
    def _validate_price_data(self, price_df: pd.DataFrame) -> pd.DataFrame:
        """
        Validate and clean price data
        
        Args:
            price_df (pd.DataFrame): Raw price data
            
        Returns:
            pd.DataFrame: Cleaned price data
        """
        # Remove rows where all price columns are zero or NaN
        price_columns = ['Open', 'High', 'Low', 'Close', 'Volume']
        valid_rows = []
        
        for idx, row in price_df.iterrows():
            # Check if at least one price column has valid data
            has_valid_price = any(
                pd.notna(row[col]) and row[col] != 0 and row[col] != '#####' 
                for col in price_columns if col in row
            )
            
            if has_valid_price:
                valid_rows.append(idx)
        
        cleaned_df = price_df.iloc[valid_rows].copy()
        self.logger.info(f"Filtered price data: {len(price_df)} -> {len(cleaned_df)} valid rows")
        return cleaned_df
    
    def _validate_news_data(self, news_df: pd.DataFrame) -> pd.DataFrame:
        """
        Validate and clean news data
        
        Args:
            news_df (pd.DataFrame): Raw news data
            
        Returns:
            pd.DataFrame: Cleaned news data
        """
        # Remove rows with empty or invalid news data
        news_columns = ['Daily_Headlines', 'Headline_Count', 'Mean_Sentiment_Score']
        valid_rows = []
        
        for idx, row in news_df.iterrows():
            # Check if news data is valid
            has_valid_news = (
                pd.notna(row.get('Daily_Headlines', '')) and 
                str(row.get('Daily_Headlines', '')).strip() != '' and
                str(row.get('Daily_Headlines', '')).strip() != '#####'
            )
            
            if has_valid_news:
                valid_rows.append(idx)
        
        cleaned_df = news_df.iloc[valid_rows].copy()
        self.logger.info(f"Filtered news data: {len(news_df)} -> {len(cleaned_df)} valid rows")
        return cleaned_df
    
    def _fill_missing_values(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Fill missing values appropriately based on data type
        
        Args:
            df (pd.DataFrame): DataFrame with missing values
            
        Returns:
            pd.DataFrame: DataFrame with filled values
        """
        # Fill numerical columns with 0
        numerical_columns = ['Open', 'High', 'Low', 'Close', 'Volume', 'Dividends', 'Stock Splits',
                           'Prev_Close', 'Daily_Return', 'SMA_5', 'Volatility_5', 'Headline_Count', 'Mean_Sentiment_Score']
        
        for col in numerical_columns:
            if col in df.columns:
                df[col] = df[col].fillna(0)
        
        # Fill text columns with empty string
        text_columns = ['Daily_Headlines']
        for col in text_columns:
            if col in df.columns:
                df[col] = df[col].fillna('')
        
        return df
    
    def save_data(self, data: pd.DataFrame, ticker_symbol: str, format_type: str = 'both') -> Tuple[str, str]:
        """
        Save data to CSV and/or JSON files with separate structured and unstructured data
        
        Args:
            data (pd.DataFrame): Data to save
            ticker_symbol (str): Ticker symbol for filename
            format_type (str): 'csv', 'json', or 'both'
            
        Returns:
            Tuple[str, str]: Paths to saved files
        """
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            
            # Save complete dataset
            csv_path, json_path = self._save_complete_dataset(data, ticker_symbol, timestamp, format_type)
            
            # Save structured data separately
            self._save_structured_data(data, ticker_symbol, timestamp)
            
            # Save unstructured data separately
            self._save_unstructured_data(data, ticker_symbol, timestamp)
            
            return csv_path, json_path
            
        except Exception as e:
            self.logger.error(f"Error saving data: {str(e)}")
            raise
    
    def _save_complete_dataset(self, data: pd.DataFrame, ticker_symbol: str, timestamp: str, format_type: str) -> Tuple[str, str]:
        """Save the complete merged dataset"""
        base_filename = f"{ticker_symbol}_curated_data_{timestamp}"
        
        csv_path = None
        json_path = None
        
        if format_type in ['csv', 'both']:
            csv_path = os.path.join(self.output_dir, f"{base_filename}.csv")
            data.to_csv(csv_path, index=False)
            self.logger.info(f"Complete dataset saved to CSV: {csv_path}")
        
        if format_type in ['json', 'both']:
            json_path = os.path.join(self.output_dir, f"{base_filename}.json")
            json_data = data.to_dict('records')
            with open(json_path, 'w') as f:
                json.dump(json_data, f, indent=2, default=str)
            self.logger.info(f"Complete dataset saved to JSON: {json_path}")
        
        return csv_path, json_path
    
    def _save_structured_data(self, data: pd.DataFrame, ticker_symbol: str, timestamp: str):
        """Save structured data separately"""
        structured_columns = [
            'Date', 'Open', 'High', 'Low', 'Close', 'Volume', 'Dividends', 'Stock Splits',
            'Prev_Close', 'Daily_Return', 'SMA_5', 'Volatility_5'
        ]
        
        # Filter to only include columns that exist in the data
        available_columns = [col for col in structured_columns if col in data.columns]
        structured_data = data[available_columns].copy()
        
        # Remove rows with invalid data
        structured_data = self._validate_price_data(structured_data)
        
        if len(structured_data) > 0:
            # Save CSV
            csv_path = os.path.join(self.output_dir, f"{ticker_symbol}_structured_data_{timestamp}.csv")
            structured_data.to_csv(csv_path, index=False)
            self.logger.info(f"Structured data saved to CSV: {csv_path}")
            
            # Save JSON
            json_path = os.path.join(self.output_dir, f"{ticker_symbol}_structured_data_{timestamp}.json")
            json_data = structured_data.to_dict('records')
            with open(json_path, 'w') as f:
                json.dump(json_data, f, indent=2, default=str)
            self.logger.info(f"Structured data saved to JSON: {json_path}")
        else:
            self.logger.warning("No valid structured data to save")
    
    def _save_unstructured_data(self, data: pd.DataFrame, ticker_symbol: str, timestamp: str):
        """Save unstructured data separately"""
        unstructured_columns = ['Date', 'Daily_Headlines', 'Headline_Count', 'Mean_Sentiment_Score']
        
        # Filter to only include columns that exist in the data
        available_columns = [col for col in unstructured_columns if col in data.columns]
        unstructured_data = data[available_columns].copy()
        
        # Remove rows with invalid data
        unstructured_data = self._validate_news_data(unstructured_data)
        
        if len(unstructured_data) > 0:
            # Save CSV
            csv_path = os.path.join(self.output_dir, f"{ticker_symbol}_unstructured_data_{timestamp}.csv")
            unstructured_data.to_csv(csv_path, index=False)
            self.logger.info(f"Unstructured data saved to CSV: {csv_path}")
            
            # Save JSON
            json_path = os.path.join(self.output_dir, f"{ticker_symbol}_unstructured_data_{timestamp}.json")
            json_data = unstructured_data.to_dict('records')
            with open(json_path, 'w') as f:
                json.dump(json_data, f, indent=2, default=str)
            self.logger.info(f"Unstructured data saved to JSON: {json_path}")
        else:
            self.logger.warning("No valid unstructured data to save")
    
    def create_data_summary(self, data: pd.DataFrame, ticker_symbol: str) -> str:
        """
        Create a data summary report (no visualization)
        
        Args:
            data (pd.DataFrame): Data to summarize
            ticker_symbol (str): Ticker symbol
            
        Returns:
            str: Path to saved summary file
        """
        try:
            self.logger.info(f"Creating data summary for {ticker_symbol}")
            
            # Create summary report
            summary = {
                'ticker': ticker_symbol,
                'data_points': len(data),
                'date_range': {
                    'start': str(data['Date'].min()) if 'Date' in data.columns else 'N/A',
                    'end': str(data['Date'].max()) if 'Date' in data.columns else 'N/A'
                },
                'features': list(data.columns),
                'data_quality': '100%' if not data.isnull().any().any() else 'Partial'
            }
            
            # Save summary
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            summary_filename = f"{ticker_symbol}_summary_{timestamp}.txt"
            summary_path = os.path.join(self.evidence_dir, summary_filename)
            
            with open(summary_path, 'w') as f:
                f.write(f"Data Summary for {ticker_symbol}\n")
                f.write("=" * 40 + "\n")
                f.write(f"Data Points: {summary['data_points']}\n")
                f.write(f"Date Range: {summary['date_range']['start']} to {summary['date_range']['end']}\n")
                f.write(f"Features: {len(summary['features'])}\n")
                f.write(f"Data Quality: {summary['data_quality']}\n")
                f.write("\nFeatures List:\n")
                for feature in summary['features']:
                    f.write(f"  - {feature}\n")
            
            self.logger.info(f"Data summary saved: {summary_path}")
            return summary_path
            
        except Exception as e:
            self.logger.error(f"Error creating data summary: {str(e)}")
            return ""
    
    def generate_summary_stats(self, data: pd.DataFrame, ticker_symbol: str) -> dict:
        """
        Generate summary statistics for the data
        
        Args:
            data (pd.DataFrame): Data to analyze
            ticker_symbol (str): Ticker symbol
            
        Returns:
            dict: Summary statistics
        """
        try:
            stats = {
                'ticker': ticker_symbol,
                'data_points': len(data),
                'date_range': {
                    'start': str(data['Date'].min()) if 'Date' in data.columns else 'N/A',
                    'end': str(data['Date'].max()) if 'Date' in data.columns else 'N/A'
                }
            }
            
            # Price statistics
            if 'Close' in data.columns:
                stats['price_stats'] = {
                    'mean_close': float(data['Close'].mean()),
                    'min_close': float(data['Close'].min()),
                    'max_close': float(data['Close'].max()),
                    'std_close': float(data['Close'].std())
                }
            
            # Return statistics
            if 'Daily_Return' in data.columns:
                stats['return_stats'] = {
                    'mean_return': float(data['Daily_Return'].mean()),
                    'volatility': float(data['Daily_Return'].std()),
                    'positive_days': int((data['Daily_Return'] > 0).sum()),
                    'negative_days': int((data['Daily_Return'] < 0).sum())
                }
            
            # Volume statistics
            if 'Volume' in data.columns:
                stats['volume_stats'] = {
                    'mean_volume': float(data['Volume'].mean()),
                    'max_volume': float(data['Volume'].max()),
                    'min_volume': float(data['Volume'].min())
                }
            
            # Sentiment statistics
            if 'Mean_Sentiment_Score' in data.columns:
                stats['sentiment_stats'] = {
                    'mean_sentiment': float(data['Mean_Sentiment_Score'].mean()),
                    'positive_sentiment_days': int((data['Mean_Sentiment_Score'] > 0).sum()),
                    'negative_sentiment_days': int((data['Mean_Sentiment_Score'] < 0).sum())
                }
            
            return stats
            
        except Exception as e:
            self.logger.error(f"Error generating summary stats: {str(e)}")
            return {'ticker': ticker_symbol, 'error': str(e)}
    
    def save_sample_evidence(self, data: pd.DataFrame, ticker_symbol: str, num_rows: int = 5) -> str:
        """
        Save sample data for evidence
        
        Args:
            data (pd.DataFrame): Data to sample
            ticker_symbol (str): Ticker symbol
            num_rows (int): Number of rows to include in sample
            
        Returns:
            str: Path to saved sample file
        """
        try:
            # Take first num_rows of data
            sample_data = data.head(num_rows)
            
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            sample_filename = f"{ticker_symbol}_sample_{timestamp}.csv"
            sample_path = os.path.join(self.evidence_dir, sample_filename)
            
            sample_data.to_csv(sample_path, index=False)
            self.logger.info(f"Sample evidence saved: {sample_path}")
            
            return sample_path
            
        except Exception as e:
            self.logger.error(f"Error saving sample evidence: {str(e)}")
            return ""


def setup_logging(log_level: str = 'INFO') -> None:
    """
    Setup logging configuration
    
    Args:
        log_level (str): Logging level (DEBUG, INFO, WARNING, ERROR)
    """
    logging.basicConfig(
        level=getattr(logging, log_level.upper()),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler('fintech_curation.log'),
            logging.StreamHandler()
        ]
    )


def validate_data_quality(data: pd.DataFrame) -> dict:
    """
    Validate data quality and return quality metrics
    
    Args:
        data (pd.DataFrame): Data to validate
        
    Returns:
        dict: Quality metrics
    """
    quality_metrics = {
        'total_rows': len(data),
        'missing_values': {},
        'data_types': {},
        'quality_score': 0.0
    }
    
    try:
        # Check for missing values
        for column in data.columns:
            missing_count = data[column].isnull().sum()
            quality_metrics['missing_values'][column] = int(missing_count)
        
        # Check data types
        for column in data.columns:
            quality_metrics['data_types'][column] = str(data[column].dtype)
        
        # Calculate quality score (0-100)
        total_cells = len(data) * len(data.columns)
        missing_cells = sum(quality_metrics['missing_values'].values())
        quality_score = ((total_cells - missing_cells) / total_cells) * 100
        quality_metrics['quality_score'] = round(quality_score, 2)
        
        return quality_metrics
        
    except Exception as e:
        quality_metrics['error'] = str(e)
        return quality_metrics


def main():
    """
    Test function for the helper utilities
    """
    # Setup logging
    setup_logging()
    
    # Create sample data for testing
    sample_data = pd.DataFrame({
        'Date': pd.date_range('2024-01-01', periods=10, freq='D').date,
        'Close': [100, 102, 101, 103, 105, 104, 106, 108, 107, 109],
        'Volume': [1000000, 1200000, 900000, 1100000, 1300000, 1000000, 1400000, 1200000, 1100000, 1500000],
        'Daily_Return': [0, 0.02, -0.0098, 0.0198, 0.0194, -0.0095, 0.0192, 0.0189, -0.0093, 0.0187],
        'Mean_Sentiment_Score': [0.1, 0.2, -0.1, 0.3, 0.4, 0.1, 0.5, 0.2, -0.2, 0.3]
    })
    
    # Test DataProcessor
    processor = DataProcessor()
    
    # Test visualization
    plot_path = processor.create_visualization(sample_data, 'TEST')
    print(f"Plot saved: {plot_path}")
    
    # Test summary stats
    stats = processor.generate_summary_stats(sample_data, 'TEST')
    print(f"Summary stats: {stats}")
    
    # Test data quality
    quality = validate_data_quality(sample_data)
    print(f"Data quality: {quality}")


if __name__ == "__main__":
    main()
