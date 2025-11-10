# Adaptive Learning FinTech Forecasting System

A complete, continuously learning FinTech system that forecasts stock/crypto/ForEx prices, monitors accuracy over time, and manages simulated portfolios with interactive visualizations.

## System Architecture

### Overview
The system extends the original forecasting application with:
- **Adaptive Learning**: Incremental updates and periodic retraining
- **Continuous Evaluation**: Automatic metric tracking (MAE, RMSE, MAPE)
- **Monitoring Dashboard**: Real-time performance visualization and alerts
- **Portfolio Management**: Simulated trading based on predictions
- **Error Visualization**: Candlestick charts with prediction error overlays

### Architecture Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                      Frontend (React)                        │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐                  │
│  │ Forecast │  │Monitor   │  │Portfolio │                  │
│  │  Page    │  │Dashboard │  │  Page    │                  │
│  └────┬─────┘  └────┬─────┘  └────┬─────┘                  │
└───────┼─────────────┼─────────────┼────────────────────────┘
        │             │             │
        └─────────────┴─────────────┘
                    │
        ┌───────────▼────────────┐
        │   FastAPI Backend      │
        │  ┌──────────────────┐ │
        │  │  API Endpoints    │ │
        │  └────────┬──────────┘ │
        │           │            │
        │  ┌────────▼──────────┐ │
        │  │ Forecast Engine   │ │
        │  │ - Model Training   │ │
        │  │ - Incremental     │ │
        │  │ - Retraining      │ │
        │  └────────┬──────────┘ │
        │           │            │
        │  ┌────────▼──────────┐ │
        │  │ Evaluation Service │ │
        │  │ - Metrics Calc    │ │
        │  │ - Ground Truth     │ │
        │  └────────┬──────────┘ │
        │           │            │
        │  ┌────────▼──────────┐ │
        │  │ Portfolio Manager │ │
        │  │ - Trading Logic   │ │
        │  │ - Performance     │ │
        │  └────────┬──────────┘ │
        └───────────┼────────────┘
                    │
        ┌───────────▼────────────┐
        │      MongoDB           │
        │  - Model Versions      │
        │  - Evaluations         │
        │  - Portfolios          │
        │  - Alerts              │
        └────────────────────────┘
```

## Key Features

### 1. Adaptive & Continuous Learning
- **Incremental Updates**: Models update with new data using online learning
- **Periodic Retraining**: Scheduled full retraining on extended historical data
- **Model Versioning**: Track model versions and performance over time
- **Automatic Promotion**: Promote better-performing models to production

### 2. Continuous Evaluation & Monitoring
- **Manual Evaluation**: Trigger evaluation via API to compare predictions vs actuals
- **Metrics Tracking**: MAE, RMSE, MAPE computed and stored over time
- **Performance Trends**: Track improving/degrading performance
- **Alert System**: Automatic alerts when thresholds exceeded

### 3. Portfolio Management
- **Simulated Trading**: Buy/sell/hold based on prediction signals
- **Decimal Quantity Support**: Supports fractional holdings (e.g., 0.5 Bitcoin)
- **Portfolio Persistence**: Portfolios are saved to MongoDB and can be loaded after backend restarts
- **Performance Metrics**: Returns, volatility, Sharpe ratio calculation
- **Transaction History**: Complete audit trail of all trades
- **Portfolio Visualization**: Growth charts and holdings tables
- **Load Existing Portfolios**: Browse and load previously created portfolios

### 4. Enhanced Visualizations
- **Error Overlays**: Prediction vs actual differences on candlestick charts
- **Interactive Charts**: Zoom, pan, hover tooltips with error details
- **Error Bands**: Colored regions showing prediction deviation
- **Real-time Updates**: Auto-refresh monitoring dashboards

## Installation

### Prerequisites
- Python 3.9+
- MongoDB (local or cloud)
- Node.js 18+ (for frontend)

### Backend Setup
```bash
cd backend
pip install -r requirements.txt

# Set MongoDB URI
# Windows PowerShell:
$env:MONGODB_URI="mongodb+srv://user:pass@cluster.mongodb.net/?retryWrites=true&w=majority"

# Linux/Mac:
export MONGODB_URI="mongodb+srv://user:pass@cluster.mongodb.net/?retryWrites=true&w=majority"
```

### Frontend Setup
```bash
cd frontend
npm install
```

## Running the System

### Development Mode

**Backend:**
```bash
cd backend/source_code
python run_api.py
# Or: uvicorn api.app:app --host 127.0.0.1 --port 8001 --reload
```

**Frontend:**
```bash
cd frontend
npm run dev
```

### Docker Deployment

```bash
cd backend
docker-compose up -d
```

## API Documentation

### Core Endpoints

#### Data Curation
- `POST /api/curate` - Fetch and store price/news data
  ```json
  { "ticker": "AAPL", "days": 60 }
  ```

#### Forecasting
- `POST /api/forecast` - Generate predictions
  ```json
  { "ticker": "AAPL", "days": 120, "horizon": 24 }
  ```

- `POST /api/visualize` - Get visualization data with errors
  ```json
  { "ticker": "AAPL", "days": 60, "horizon": 24 }
  ```

### Adaptive Learning Endpoints

#### Model Retraining
- `POST /api/retrain` - Manually trigger retraining
  ```json
  { "ticker": "AAPL", "model_type": "lstm", "days": 120 }
  ```

- `GET /api/models/versions` - List all model versions
  ```
  ?model_type=lstm&ticker=AAPL&production_only=true
  ```

- `POST /api/models/promote` - Promote model to production
  ```json
  { "ticker": "AAPL", "model_type": "lstm", "version": "v20250916_120000" }
  ```

### Evaluation Endpoints

- `POST /api/evaluate` - Evaluate past predictions
  ```json
  { "ticker": "AAPL", "prediction_id": "uuid", "days_back": 7 }
  ```

- `GET /api/evaluations/history` - Get evaluation history
  ```
  ?ticker=AAPL&model_type=lstm&limit=100
  ```

### Monitoring Endpoints

- `GET /api/monitoring/metrics` - Get aggregated metrics
  ```
  ?ticker=AAPL&window=daily&days_back=30
  ```

- `GET /api/monitoring/alerts` - Get recent alerts
  ```
  ?ticker=AAPL&severity=error&limit=50
  ```

- `GET /api/monitoring/performance-trends` - Get performance trends
  ```
  ?ticker=AAPL&days_back=30
  ```

- `POST /api/monitoring/alerts/configure` - Configure alert thresholds
  ```json
  { "thresholds": { "MAPE": 10.0, "RMSE_spike": 20.0 } }
  ```

### Portfolio Endpoints

- `GET /api/portfolio/list` - List all existing portfolios
  ```
  Returns: { "success": true, "portfolios": [...], "count": N }
  ```

- `POST /api/portfolio/create` - Create new portfolio
  ```json
  { "initial_cash": 100000.0 }
  ```

- `POST /api/portfolio/trade` - Execute a trade (buy/sell)
  ```json
  { 
    "portfolio_id": "uuid", 
    "ticker": "AAPL", 
    "action": "buy",
    "quantity": 0.5,  // Supports decimal quantities (e.g., 0.5 Bitcoin)
    "price": 150.0  // Optional: auto-fetched if not provided
  }
  ```

- `POST /api/portfolio/trade-from-prediction` - Trade based on prediction
  ```json
  { "portfolio_id": "uuid", "ticker": "AAPL", "predicted_price": 150.0 }
  ```

- `GET /api/portfolio/{portfolio_id}` - Get portfolio status
  ```
  Query params: ?skip_price_fetch=false (default: true for faster response)
  ```

- `GET /api/portfolio/{portfolio_id}/performance` - Get performance metrics

- `GET /api/portfolio/{portfolio_id}/history` - Get transaction history

## Testing

### Run Unit Tests
```bash
cd backend/source_code
python -m pytest tests/ -v
```

### Run Specific Test Suite
```bash
# Test incremental learning
python -m pytest tests/test_incremental_learning.py -v

# Test evaluation
python -m pytest tests/test_evaluation.py -v

# Test portfolio
python -m pytest tests/test_portfolio.py -v

# Test API
python -m pytest tests/test_api.py -v
```

## MongoDB Collections

The system uses the following MongoDB collections:

- `model_versions` - Model version metadata
- `model_performance` - Performance metrics per version
- `evaluations` - Evaluation results over time
- `alerts` - System alerts and notifications
- `portfolios` - Portfolio data and holdings
- `transactions` - Trading transaction history
- `forecasts` - Forecast predictions
- `curated_data` - Curated price/news data
- `visualize_snapshots` - Visualization snapshots

## Project Structure

```
backend/
├── source_code/
│   ├── api/
│   │   └── app.py              # FastAPI application
│   ├── forecasting/
│   │   ├── forecast_engine.py  # Main forecast engine
│   │   ├── model_neural.py      # Neural network models
│   │   ├── model_traditional.py # Traditional models
│   │   ├── evaluation.py       # Evaluation metrics
│   │   ├── evaluation_service.py # Evaluation service
│   │   ├── incremental_learning.py # Incremental updates
│   │   ├── retraining_service.py   # Retraining service
│   │   ├── model_registry.py       # Model versioning
│   │   ├── model_storage.py        # Model storage
│   │   └── model_comparison.py     # Model comparison
│   ├── monitoring/
│   │   ├── metrics_aggregator.py   # Metrics aggregation
│   │   └── alert_service.py         # Alert generation
│   ├── portfolio/
│   │   ├── portfolio_manager.py    # Portfolio operations
│   │   ├── trading_strategy.py      # Trading logic
│   │   └── performance_metrics.py   # Performance calc
│   ├── database/
│   │   └── mongo_connector.py       # MongoDB operations
│   ├── tests/                        # Test suite
│   └── ...
├── Dockerfile
├── docker-compose.yml
└── requirements.txt

frontend/
├── src/
│   ├── pages/
│   │   ├── Home.jsx              # Forecast page
│   │   ├── Monitoring.jsx        # Monitoring dashboard
│   │   └── Portfolio.jsx         # Portfolio management
│   ├── components/
│   │   ├── ChartDisplay.jsx       # Enhanced with errors
│   │   ├── ErrorOverlay.jsx       # Error visualization
│   │   ├── MetricsChart.jsx      # Metrics charts
│   │   ├── AlertPanel.jsx        # Alert display
│   │   ├── ModelPerformanceTable.jsx # Performance table
│   │   ├── PortfolioChart.jsx    # Portfolio charts
│   │   ├── TradingPanel.jsx      # Trading interface
│   │   └── PerformanceMetrics.jsx # Performance display
│   └── ...
└── package.json
```

## Deployment

### Docker Deployment
```bash
cd backend
docker-compose up -d
```

### Production Deployment
```bash
# Backend with Gunicorn
gunicorn source_code.api.app:app -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8001

# Frontend build
cd frontend
npm run build
# Serve with nginx or similar
```

## Usage Examples

### 1. Create Portfolio and Trade
```bash
# List existing portfolios
curl -X GET http://localhost:8001/api/portfolio/list

# Create portfolio
curl -X POST http://localhost:8001/api/portfolio/create \
  -H "Content-Type: application/json" \
  -d '{"initial_cash": 100000}'

# Get forecast
curl -X POST http://localhost:8001/api/forecast \
  -H "Content-Type: application/json" \
  -d '{"ticker": "AAPL", "days": 120, "horizon": 1}'

# Execute trade with decimal quantity (e.g., 0.5 Bitcoin)
curl -X POST http://localhost:8001/api/portfolio/trade \
  -H "Content-Type: application/json" \
  -d '{"portfolio_id": "uuid", "ticker": "BTC-USD", "action": "buy", "quantity": 0.5}'

# Trade based on prediction
curl -X POST http://localhost:8001/api/portfolio/trade-from-prediction \
  -H "Content-Type: application/json" \
  -d '{"portfolio_id": "uuid", "ticker": "AAPL", "predicted_price": 150.0}'
```

### 2. Retrain Models
```bash
curl -X POST http://localhost:8001/api/retrain \
  -H "Content-Type: application/json" \
  -d '{"ticker": "AAPL", "model_type": "lstm", "days": 120}'
```

### 3. Evaluate Predictions
```bash
curl -X POST http://localhost:8001/api/evaluate \
  -H "Content-Type: application/json" \
  -d '{"ticker": "AAPL", "days_back": 7}'
```

## Architecture Decisions

### Adaptive Learning
- **Incremental Updates**: Use gradient-based updates for neural models, partial_fit for sklearn models
- **Retraining Schedule**: Weekly retraining with 60-day rolling window
- **Model Promotion**: Automatic promotion if new model improves by >5% on MAPE

### Evaluation Strategy
- **Manual Triggers**: Evaluation triggered via API when ground-truth available
- **Metrics Storage**: All metrics stored in MongoDB for historical analysis
- **Time Alignment**: Precise date-based alignment of predictions and actuals

### Portfolio Management
- **Trading Signals**: Buy if predicted increase >2%, Sell if predicted decrease <-2%
- **Position Sizing**: 10% of portfolio per trade (configurable)
- **Decimal Quantities**: Supports fractional holdings (e.g., 0.5 Bitcoin, 0.25 shares)
- **Portfolio Persistence**: All portfolios saved to MongoDB, persist across backend restarts
- **Performance Tracking**: Real-time calculation of returns, volatility, Sharpe ratio
- **Auto/Manual Trading**: Toggle between automatic signal-based trading and manual trade execution

## Troubleshooting

### MongoDB Connection Issues
- Verify MONGODB_URI environment variable is set
- Check network connectivity to MongoDB cluster
- Verify credentials are correct

### Model Loading Errors
- Ensure model files exist in `models/` directory
- Check model version exists in MongoDB
- Verify model type matches expected format

### Frontend Connection Issues
- Verify backend is running on port 8001
- Check CORS settings in FastAPI
- Verify API_BASE URL in frontend components

## License

Educational use for CS4063 - Natural Language Processing course.
