# Project Documentation - Financial Data Curation System

**Course**: CS4063 - Natural Language Processing  
**Assignment**: Financial Data Curation for Next-Day Price Prediction  
**Date**: September 18, 2025  

## 📁 Project Structure

```
fintech_curation/
├── source_code/
│   ├── main_scraper.py      # Main orchestration script
│   ├── price_fetcher.py     # Price data collection module
│   ├── news_fetcher.py      # News data collection module
│   └── helper_utils.py      # Data processing utilities
├── output_data/             # Generated CSV/JSON files
├── sample_evidence/         # Sample data and summaries
├── documentation/
│   └── feature_justification.md
├── requirements.txt         # Dependencies
├── README.md               # Setup and usage guide
└── project.md              # This file
```

## 🐍 Python Files Explanation - Function by Function

### 1. `main_scraper.py` - Main Orchestration Script

**Purpose**: The central controller that orchestrates the entire data curation process.

#### **Class: FinTechDataCuration**

**`__init__(self, output_dir, evidence_dir)`**
- **Purpose**: Initialize the data curation system
- **Parameters**: 
  - `output_dir`: Directory for output files
  - `evidence_dir`: Directory for sample evidence
- **What it does**: Sets up logging, initializes all modules (PriceFetcher, NewsFetcher, DataProcessor)

**`run_curation(self, exchange, ticker_symbol, num_days)`**
- **Purpose**: Main orchestration function for single ticker processing
- **Parameters**:
  - `exchange`: Stock exchange (NYSE, NASDAQ, PSX)
  - `ticker_symbol`: Stock or crypto symbol
  - `num_days`: Number of days to fetch
- **Process**:
  1. Validates ticker symbol
  2. Gets ticker information
  3. Fetches price data via PriceFetcher
  4. Fetches news data via NewsFetcher
  5. Merges datasets via DataProcessor
  6. Validates data quality
  7. Saves data in multiple formats
  8. Generates summaries and samples
- **Returns**: Dictionary with success status, file paths, and quality metrics

**`run_batch_curation(self, tickers, num_days)`**
- **Purpose**: Process multiple tickers in batch
- **Parameters**:
  - `tickers`: List of ticker symbols
  - `num_days`: Number of days for each ticker
- **Process**: Loops through each ticker, calls `run_curation()`, tracks success/failure
- **Returns**: Batch results with success/failure counts

#### **Functions**

**`parse_arguments()`**
- **Purpose**: Parse command line arguments using argparse
- **Arguments handled**:
  - `--exchange`: Stock exchange
  - `--ticker`: Single ticker symbol
  - `--days`: Number of days
  - `--batch`: Comma-separated tickers
  - `--output-dir`: Output directory
  - `--evidence-dir`: Evidence directory
  - `--log-level`: Logging level
  - `--quiet`: Suppress console output
- **Returns**: Parsed arguments namespace

**`main()`**
- **Purpose**: Main entry point of the program
- **Process**:
  1. Parse command line arguments
  2. Setup logging
  3. Initialize FinTechDataCuration
  4. Run single ticker or batch processing
  5. Print results and handle errors
- **Error Handling**: KeyboardInterrupt, general exceptions

---

### 2. `price_fetcher.py` - Price Data Collection Module

**Purpose**: Fetches and processes structured financial data (OHLCV, technical indicators).

#### **Class: PriceFetcher**

**`__init__(self)`**
- **Purpose**: Initialize the price fetcher
- **What it does**: Sets up logging and yfinance configuration

**`validate_ticker(self, ticker_symbol)`**
- **Purpose**: Validate if ticker symbol exists
- **Parameters**: `ticker_symbol`: Stock or crypto symbol
- **Process**: Attempts to create yfinance Ticker object
- **Returns**: Boolean (True if valid, False if invalid)

**`get_ticker_info(self, ticker_symbol)`**
- **Purpose**: Get ticker information (name, sector, market cap, etc.)
- **Parameters**: `ticker_symbol`: Stock or crypto symbol
- **Process**: Fetches ticker info from yfinance
- **Returns**: Dictionary with ticker metadata

**`fetch_historical_prices(self, ticker_symbol, num_days)`**
- **Purpose**: Main function to fetch price data and calculate indicators
- **Parameters**:
  - `ticker_symbol`: Stock or crypto symbol
  - `num_days`: Number of days to fetch
- **Process**:
  1. Download historical data from Yahoo Finance
  2. Calculate Previous Close (shift Close by 1 day)
  3. Calculate Daily Return: `(Close - Prev_Close) / Prev_Close`
  4. Calculate 5-day Simple Moving Average (SMA_5)
  5. Calculate 5-day Rolling Volatility (std of returns)
  6. Handle missing values and data gaps
- **Returns**: pandas DataFrame with OHLCV + technical indicators

**`_calculate_technical_indicators(self, price_data)`**
- **Purpose**: Calculate technical indicators from price data
- **Parameters**: `price_data`: DataFrame with OHLCV data
- **Process**:
  1. Calculate Previous Close (shift Close by 1 day)
  2. Calculate Daily Return percentage
  3. Calculate 5-day Simple Moving Average
  4. Calculate 5-day Rolling Volatility
- **Returns**: DataFrame with added technical indicators

**`_handle_missing_data(self, price_data)`**
- **Purpose**: Handle missing values and data gaps
- **Parameters**: `price_data`: DataFrame with potential missing values
- **Process**:
  1. Forward fill missing Previous Close values
  2. Fill missing Daily Return with 0
  3. Handle edge cases for first day data
- **Returns**: Cleaned DataFrame with no missing values

---

### 3. `news_fetcher.py` - News Data Collection Module

**Purpose**: Fetches and processes unstructured financial news data with sentiment analysis.

#### **Class: NewsFetcher**

**`__init__(self)`**
- **Purpose**: Initialize the news fetcher
- **What it does**: Sets up logging, user-agent headers, and TextBlob configuration

**`fetch_daily_news(self, ticker_symbol, start_date, end_date)`**
- **Purpose**: Main function to fetch news and perform sentiment analysis
- **Parameters**:
  - `ticker_symbol`: Stock or crypto symbol
  - `start_date`: Start date for news fetching
  - `end_date`: End date for news fetching
- **Process**:
  1. Determine if ticker is cryptocurrency
  2. Fetch news from appropriate source (Yahoo Finance or CoinDesk)
  3. Extract headlines and dates
  4. Perform sentiment analysis
  5. Aggregate by trading day
- **Returns**: pandas DataFrame with daily headlines, counts, and sentiment scores

**`_fetch_stock_news(self, ticker_symbol, start_date, end_date)`**
- **Purpose**: Fetch news for stock tickers from Yahoo Finance
- **Parameters**: Same as `fetch_daily_news`
- **Process**:
  1. Construct Yahoo Finance news URL
  2. Send HTTP request with proper headers
  3. Parse HTML response with BeautifulSoup
  4. Extract headline text and publication dates
  5. Handle errors and retries
- **Returns**: List of news articles with headlines and dates

**`_fetch_crypto_news(self, ticker_symbol, start_date, end_date)`**
- **Purpose**: Fetch news for cryptocurrency tickers from CoinDesk
- **Parameters**: Same as `fetch_daily_news`
- **Process**:
  1. Construct CoinDesk news URL
  2. Send HTTP request with proper headers
  3. Parse HTML response with BeautifulSoup
  4. Extract headline text and publication dates
  5. Handle errors and retries
- **Returns**: List of news articles with headlines and dates

**`_extract_news_from_html(self, html_content)`**
- **Purpose**: Extract news headlines and dates from HTML content
- **Parameters**: `html_content`: HTML content from web scraping
- **Process**:
  1. Parse HTML with BeautifulSoup
  2. Find news article elements
  3. Extract headline text and links
  4. Extract publication dates
  5. Clean and format data
- **Returns**: List of dictionaries with headline and date information

**`_perform_sentiment_analysis(self, headlines)`**
- **Purpose**: Perform sentiment analysis on news headlines
- **Parameters**: `headlines`: List of headline strings
- **Process**:
  1. Use TextBlob to analyze each headline
  2. Calculate polarity score (-1 to 1)
  3. Handle empty or invalid headlines
  4. Calculate mean sentiment score
- **Returns**: List of sentiment scores

**`_aggregate_news_by_date(self, news_data)`**
- **Purpose**: Group news headlines by trading day
- **Parameters**: `news_data`: List of news articles with dates
- **Process**:
  1. Group headlines by date
  2. Calculate headline count per day
  3. Calculate mean sentiment score per day
  4. Handle date alignment with trading days
- **Returns**: pandas DataFrame with daily aggregated news data

**`_align_news_with_trading_days(self, news_df)`**
- **Purpose**: Align news data with trading days (exclude weekends)
- **Parameters**: `news_df`: DataFrame with news data
- **Process**:
  1. Convert dates to datetime
  2. Filter out weekends
  3. Forward fill missing days
  4. Ensure proper date alignment
- **Returns**: DataFrame aligned with trading days

---

### 4. `helper_utils.py` - Data Processing Utilities

**Purpose**: Handles data merging, validation, saving, and quality control.

#### **Class: DataProcessor**

**`__init__(self, output_dir, evidence_dir)`**
- **Purpose**: Initialize the data processor
- **Parameters**:
  - `output_dir`: Directory for output files
  - `evidence_dir`: Directory for sample evidence
- **What it does**: Sets up logging, creates directories, initializes file paths

**`merge_datasets(self, price_df, news_df)`**
- **Purpose**: Merge price and news datasets with proper validation
- **Parameters**:
  - `price_df`: DataFrame with price data
  - `news_df`: DataFrame with news data
- **Process**:
  1. Convert dates to datetime format
  2. Validate and clean price data
  3. Validate and clean news data
  4. Merge on Date column
  5. Sort by date
  6. Forward fill missing values
  7. Fill remaining NaN values
- **Returns**: Merged DataFrame with aligned data

**`_validate_price_data(self, price_df)`**
- **Purpose**: Filter out invalid price data (zeros, NaN, #####)
- **Parameters**: `price_df`: Raw price data DataFrame
- **Process**:
  1. Check each row for valid price data
  2. Remove rows where all price columns are zero or invalid
  3. Keep only rows with at least one valid price value
- **Returns**: Cleaned DataFrame with valid price data

**`_validate_news_data(self, news_df)`**
- **Purpose**: Filter out invalid news data (empty headlines, #####)
- **Parameters**: `news_df`: Raw news data DataFrame
- **Process**:
  1. Check each row for valid news data
  2. Remove rows with empty or invalid headlines
  3. Keep only rows with meaningful news content
- **Returns**: Cleaned DataFrame with valid news data

**`_fill_missing_values(self, df)`**
- **Purpose**: Fill missing values appropriately based on data type
- **Parameters**: `df`: DataFrame with missing values
- **Process**:
  1. Fill numerical columns with 0
  2. Fill text columns with empty string
  3. Handle different data types appropriately
- **Returns**: DataFrame with filled missing values

**`save_data(self, data, ticker_symbol, format_type='both')`**
- **Purpose**: Save data in multiple formats with separate structured/unstructured files
- **Parameters**:
  - `data`: Merged DataFrame to save
  - `ticker_symbol`: Ticker symbol for filename
  - `format_type`: 'csv', 'json', or 'both'
- **Process**:
  1. Save complete merged dataset
  2. Save structured data separately
  3. Save unstructured data separately
- **Returns**: Tuple of file paths (CSV, JSON)

**`_save_complete_dataset(self, data, ticker_symbol, timestamp, format_type)`**
- **Purpose**: Save the complete merged dataset
- **Parameters**: Same as `save_data` plus timestamp
- **Process**: Save complete dataset in CSV and/or JSON format
- **Returns**: File paths for complete dataset

**`_save_structured_data(self, data, ticker_symbol, timestamp)`**
- **Purpose**: Save structured data separately (OHLCV + indicators)
- **Parameters**: Same as above
- **Process**:
  1. Filter to structured columns only
  2. Validate price data
  3. Save in CSV and JSON formats
- **Returns**: File paths for structured data

**`_save_unstructured_data(self, data, ticker_symbol, timestamp)`**
- **Purpose**: Save unstructured data separately (news + sentiment)
- **Parameters**: Same as above
- **Process**:
  1. Filter to unstructured columns only
  2. Validate news data
  3. Save in CSV and JSON formats
- **Returns**: File paths for unstructured data

**`create_data_summary(self, data, ticker_symbol)`**
- **Purpose**: Create a data summary report (no visualization)
- **Parameters**:
  - `data`: DataFrame to summarize
  - `ticker_symbol`: Ticker symbol for report
- **Process**:
  1. Calculate data statistics
  2. Generate summary report
  3. Save as text file
- **Returns**: Path to summary file

**`save_sample_evidence(self, data, ticker_symbol)`**
- **Purpose**: Save sample evidence (first 5 rows) for quick review
- **Parameters**: Same as above
- **Process**:
  1. Take first 5 rows of data
  2. Save as CSV file
  3. Generate timestamped filename
- **Returns**: Path to sample file

**`generate_summary_stats(self, data, ticker_symbol)`**
- **Purpose**: Generate summary statistics for the data
- **Parameters**: Same as above
- **Process**:
  1. Calculate descriptive statistics
  2. Generate data quality metrics
  3. Create summary dictionary
- **Returns**: Dictionary with summary statistics

#### **Utility Functions**

**`setup_logging(log_level)`**
- **Purpose**: Setup logging configuration
- **Parameters**: `log_level`: Logging level (DEBUG, INFO, WARNING, ERROR)
- **Process**: Configure logging with file and console handlers
- **Returns**: None

**`validate_data_quality(data)`**
- **Purpose**: Validate data quality and completeness
- **Parameters**: `data`: DataFrame to validate
- **Process**:
  1. Check for missing values
  2. Calculate completeness percentage
  3. Generate quality metrics
- **Returns**: Dictionary with quality metrics

---

## 🔄 Data Flow Process

### 1. **Input Processing**
```
User Input → main_scraper.py → Validate Parameters
```

### 2. **Data Collection**
```
main_scraper.py → price_fetcher.py → Yahoo Finance API → Price Data
main_scraper.py → news_fetcher.py → Web Scraping → News Data
```

### 3. **Data Processing**
```
Price Data + News Data → helper_utils.py → Data Validation → Merged Dataset
```

### 4. **Output Generation**
```
Merged Dataset → helper_utils.py → Multiple File Formats → Final Output
```

## 📊 Data Quality Features

### **Validation Pipeline**:
1. **Price Data Validation**: Removes rows with all zeros or invalid values
2. **News Data Validation**: Filters empty headlines and invalid sentiment
3. **Date Alignment**: Ensures proper temporal correspondence
4. **Missing Value Handling**: Forward fill for weekends/holidays
5. **Quality Scoring**: 100% completeness validation

### **Error Handling**:
- **API Failures**: Retry logic with exponential backoff
- **Network Issues**: Graceful degradation and error reporting
- **Data Gaps**: Intelligent filling and validation
- **Invalid Data**: Automatic filtering and quality control

## 🎯 Key Features

### **Modularity**:
- Each module has a single responsibility
- Easy to extend and modify
- Clean separation of concerns

### **Reliability**:
- Comprehensive error handling
- Data validation at every step
- Quality metrics and reporting

### **Flexibility**:
- Configurable date ranges
- Multiple output formats
- Batch processing support

### **Scalability**:
- Handles multiple tickers
- Efficient data processing
- Memory-optimized operations

## 📈 Output Files Generated

For each ticker processed:
- **Complete Dataset**: `{ticker}_curated_data_*.csv/json`
- **Structured Data**: `{ticker}_structured_data_*.csv/json`
- **Unstructured Data**: `{ticker}_unstructured_data_*.csv/json`
- **Summary Report**: `{ticker}_summary_*.txt`
- **Sample Evidence**: `{ticker}_sample_*.csv`

## 🔧 Dependencies

- **`yfinance`**: Yahoo Finance API for price data
- **`requests`**: HTTP requests for web scraping
- **`beautifulsoup4`**: HTML parsing for news extraction
- **`textblob`**: Sentiment analysis
- **`pandas`**: Data manipulation and analysis
- **`tenacity`**: Retry logic for API calls
- **`lxml`**: XML/HTML parsing

This modular design ensures maintainability, reliability, and ease of extension for future enhancements.
