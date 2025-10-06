# Financial Data Curation Tool - CS4063 Assignment

A Python program that scrapes structured and unstructured financial data to build datasets for predictive modeling. This tool collects minimal yet optimal features from live financial sources to create datasets that can be used for next-day price prediction.

## Assignment Requirements Met

✅ **Input Parameters**: Takes stock exchange and ticker symbol as input  
✅ **Live Data Scraping**: Scrapes from Yahoo Finance, CoinDesk, and other open sources  
✅ **Structured Data**: Historical prices (OHLCV), returns, volatility, moving averages  
✅ **Unstructured Data**: News headlines and sentiment analysis  
✅ **Data Alignment**: Text fields aligned by date with numerical fields  
✅ **Modular Design**: Easy to add new stocks/cryptocurrencies  
✅ **Output Formats**: Saves data in CSV and JSON formats  
✅ **Sample Evidence**: Tested with 2 stocks (AAPL, TSLA) and 1 crypto (BTC-USD)  
✅ **Dataset Ready**: Generated data can be used for future predictive modeling  

## Quick Start

### Installation
```bash
pip install -r requirements.txt
```

### API Server
```bash
# Set Mongo connection (PowerShell)
setx MONGODB_URI "mongodb+srv://<user>:<1234>@algodinero.qtamhh.mongodb.net/?retryWrites=true&w=majority&appName=AlgoDinero"

# Run FastAPI
cd source_code
uvicorn api.app:app --host 127.0.0.1 --port 8000
```

### API Endpoints
- POST /api/curate { ticker, days }
- POST /api/forecast { ticker, days, horizon }
- POST /api/visualize { ticker, days, horizon }

### Usage
```bash
# Single stock/crypto
python source_code/main_scraper.py --exchange NASDAQ --ticker AAPL --days 10

# Cryptocurrency
python source_code/main_scraper.py --ticker BTC-USD --days 10

# Batch processing
python source_code/main_scraper.py --batch AAPL,TSLA,BTC-USD --days 10
```

## Data Structure

The tool generates datasets with 15 features:

**Structured Data (8 features):**
- Date, Open, High, Low, Close, Volume, Dividends, Stock Splits
- Prev_Close, Daily_Return, SMA_5, Volatility_5

**Unstructured Data (3 features):**
- Daily_Headlines, Headline_Count, Mean_Sentiment_Score

## Sample Output

```
============================================================
DATA CURATION RESULTS
============================================================
✓ SUCCESS: AAPL
Exchange: NASDAQ
Data points: 16
Date range: 2025-09-01 to 2025-09-16
Quality score: 100.0%

Files created:
  CSV: output_data\AAPL_curated_data_20250916_205159.csv
  JSON: output_data\AAPL_curated_data_20250916_205159.json
  SUMMARY: sample_evidence\AAPL_summary_20250916_205200.txt
  SAMPLE: sample_evidence\AAPL_sample_20250916_205202.csv
```

## Project Structure

```
fintech_curation/
├── source_code/
│   ├── main_scraper.py      # Main orchestration script
│   ├── price_fetcher.py     # Price data collection
│   ├── news_fetcher.py      # News data collection
│   └── helper_utils.py      # Data processing utilities
├── output_data/             # Generated CSV/JSON files
├── sample_evidence/         # Sample data and summaries
├── documentation/           # Feature justification
├── requirements.txt         # Dependencies
└── README.md               # This file
```

## Assignment Evidence

The tool has been tested and generates sample data for:
- **AAPL** (NASDAQ) - Apple Inc.
- **TSLA** (NASDAQ) - Tesla Inc.  
- **BTC-USD** (Crypto) - Bitcoin

All sample data includes at least 5 days of history with 100% data quality.

## Technical Implementation

- **Data Sources**: Yahoo Finance (yfinance), CoinDesk RSS
- **Sentiment Analysis**: TextBlob polarity scoring
- **Error Handling**: Retry mechanisms and fallback data
- **Data Quality**: 100% completeness validation
- **Modularity**: Clean separation of concerns

## Files Generated

For each run, the tool creates:
- **CSV File**: Complete dataset ready for ML training
- **JSON File**: Alternative format for data processing
- **Sample CSV**: First 5 rows for quick review
- **Summary Report**: Data quality and feature overview

This implementation provides the minimal yet optimal feature set needed to build datasets for next-day price prediction while maintaining clean, modular, and well-documented code.


python main_scraper.py --exchange NASDAQ --ticker AAPL --days 5
python main_scraper.py --ticker BTC-USD --days 5

Batch processing
python main_scraper.py --batch AAPL,TSLA,BTC-USD --days 5