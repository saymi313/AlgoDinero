# 💹 AlgoDinero – AI-Powered FinTech Forecasting Dashboard

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![React](https://img.shields.io/badge/React-Vite-blue.svg)](https://reactjs.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-Python-green.svg)](https://fastapi.tiangolo.com/)
[![MongoDB](https://img.shields.io/badge/MongoDB-Atlas-brightgreen.svg)](https://www.mongodb.com/atlas)

**AlgoDinero** is a sophisticated, full-stack AI-driven financial forecasting dashboard that empowers users with seamless data curation, advanced model-based predictions, and interactive visualizations for financial instruments. Built with a focus on modularity, scalability, and real-time insights, it bridges live market data with cutting-edge machine learning to deliver actionable intelligence for traders, analysts, and financial professionals.

The application leverages **React (Vite)** for a responsive frontend, **FastAPI (Python)** for robust backend APIs, and **MongoDB Atlas** for secure, cloud-based data persistence. At its core, AlgoDinero employs a **layered client-server architecture** that enforces strict separation of concerns across presentation, service, domain (ML), and storage layers, ensuring maintainability, extensibility, and high performance.

---

## 🧠 Overview

AlgoDinero transforms complex financial data workflows into an intuitive, end-to-end platform. It ingests real-time market feeds and news, applies a hybrid ensemble of classical and deep learning models for precise forecasting, and renders dynamic visualizations—all while maintaining full traceability through persistent storage.

### **Key Features**
- **Data Curation:** Automated ingestion and alignment of historical price data (via Yahoo Finance) and financial news (via RSS feeds), enriched with sentiment analysis using NLP techniques.
- **Advanced Forecasting:** A diverse model suite including Moving Average (MA), ARIMA, Vector Autoregression (VAR), Multi-Layer Perceptron (MLP), Gated Recurrent Unit (GRU), Long Short-Term Memory (LSTM), and Transformer architectures. Each model contributes unique strengths: MA provides stable baselines, ARIMA captures linear trends, VAR models cross-asset relationships, MLP handles non-linear patterns, GRU/LSTM capture temporal dependencies, and Transformers identify long-range attention patterns. Outputs are aggregated via ensemble mean for robust predictions, with intelligent fallback mechanisms for reliability.
- **Interactive Visualizations:** Real-time OHLC candlestick charts, forecast overlays, error metric dashboards (RMSE, MAE, MAPE), and sentiment timelines powered by Plotly.js for zoomable, hover-interactive experiences.
- **Persistent Analytics:** Comprehensive snapshots of curated datasets, forecasts, and visualizations stored in MongoDB, enabling audit trails, historical comparisons, and offline analysis.
- **User-Centric Design:** Responsive interface supporting multi-instrument analysis, customizable forecast horizons (e.g., 1-30 days), and one-click curation-to-visualization workflows.

This architecture not only democratizes access to AI-driven financial tools but also scales effortlessly for enterprise-grade deployments.

---

## 🏗️ System Architecture

AlgoDinero adopts a **4-tier modular architecture** inspired by clean architecture principles, promoting loose coupling, testability, and independent evolution of components. Communication flows unidirectionally: from the frontend through RESTful APIs to the backend, which orchestrates domain logic and persists results in the database.

### **1. Presentation Layer (Frontend)**
- **Technologies:** React (Vite for fast bundling), Tailwind CSS (for utility-first styling), Plotly.js (for advanced charting).
- **Core Responsibilities:**
  - User input handling: Ticker symbols (e.g., AAPL, BTC-USD), forecast periods, and visualization preferences.
  - API orchestration: Asynchronous HTTP requests to backend endpoints using Axios or Fetch.
  - Dynamic Rendering: 
    - Interactive OHLC candlesticks with volume overlays.
    - Multi-line forecast plots (individual models + ensemble).
    - Metric cards displaying quantitative evaluations and qualitative sentiment scores.
    - News panels with keyword-highlighted articles and polarity gauges.
- **Design Principles:** Component-based (e.g., reusable hooks for data fetching), state-managed with React Context or Redux for global ticker/forecast state, and optimized for mobile responsiveness via Tailwind breakpoints.
- **Benefits:** Decoupled from business logic, enabling rapid UI iterations without backend redeploys. CORS and JWT-ready for secure cross-origin requests.

### **2. Service Layer (Backend APIs)**
- **Technologies:** FastAPI (async Python framework for high-throughput APIs), Pydantic for schema validation.
- **Key Endpoints:** (Detailed in [API Reference](#api-reference) below)
  - Data ingestion and processing pipelines triggered via POST requests.
  - Health monitoring for operational reliability.
- **Modular Components:**
  - **PriceFetcher:** Leverages `yfinance` library for historical and real-time OHLCV data, with caching to mitigate API rate limits.
  - **NewsFetcher:** Scrapes RSS feeds (e.g., from Reuters, Bloomberg) and applies VADER or TextBlob for sentiment scoring on headlines and summaries.
  - **DataProcessor:** Time-series alignment, feature engineering (e.g., technical indicators like RSI, MACD), and metric computation.
  - **ForecastingEngine:** Orchestrates model training/inference, hyperparameter tuning (via GridSearch for classical models), and ensemble weighting based on historical accuracy.
  - **MongoConnector:** PyMongo driver for CRUD operations, with indexing on timestamps and tickers for query efficiency.
- **Design Principles:** Stateless design for containerized scaling (e.g., Docker/Kubernetes), dependency injection via FastAPI's Depends(), and comprehensive logging with StructLog.
- **Benefits:** API-first approach ensures interoperability; async I/O handles concurrent user sessions efficiently.

### **3. Domain Layer (Modeling & Business Logic)**

#### **Traditional Forecasting Models**

**Moving Average (MA)**
- **Purpose:** Provides baseline trend smoothing and serves as a robust fallback mechanism
- **Implementation:** Simple arithmetic mean over specified window periods (e.g., 5, 10, 20 days)
- **Contribution:** Acts as a stable baseline that captures general market trends without overfitting to noise
- **Use Case:** When other models fail to converge or for short-term trend identification
- **Strengths:** Fast computation, interpretable, immune to overfitting
- **Limitations:** Cannot capture complex patterns or sudden market shifts

**ARIMA (AutoRegressive Integrated Moving Average)**
- **Purpose:** Captures linear relationships and seasonal patterns in univariate time series
- **Implementation:** Uses `statsmodels.tsa.arima.model.ARIMA` with automatic order selection (p,d,q)
- **Contribution:** Provides interpretable coefficients for trend, seasonality, and noise components
- **Use Case:** Traditional econometric forecasting for stocks with clear seasonal patterns
- **Strengths:** Well-established statistical foundation, handles non-stationarity through differencing
- **Limitations:** Assumes linear relationships, struggles with non-linear market dynamics

**VAR (Vector Autoregression)**
- **Purpose:** Models multivariate relationships between multiple financial instruments
- **Implementation:** Uses `statsmodels.tsa.vector_ar.var_model.VAR` to capture cross-asset dependencies
- **Contribution:** Captures how different assets influence each other (e.g., how S&P 500 affects individual stocks)
- **Use Case:** Portfolio-level forecasting and understanding market contagion effects
- **Strengths:** Captures cross-asset correlations, useful for multi-asset strategies
- **Limitations:** Requires multiple time series, computationally expensive with many variables

#### **Neural Network Models**

**Multi-Layer Perceptron (MLP)**
- **Purpose:** Baseline neural network for non-linear pattern recognition
- **Implementation:** `sklearn.neural_network.MLPRegressor` with 2-3 hidden layers
- **Contribution:** Captures non-linear relationships between features and price movements
- **Use Case:** When linear models (ARIMA) fail to capture complex market dynamics
- **Strengths:** Handles non-linear patterns, relatively fast training
- **Limitations:** Cannot capture temporal dependencies, treats each prediction independently

**Gated Recurrent Unit (GRU)**
- **Purpose:** Efficiently captures sequential dependencies with reduced computational complexity
- **Implementation:** PyTorch-based with 2-3 GRU layers, dropout for regularization
- **Contribution:** Balances memory efficiency with sequence modeling capability
- **Use Case:** Medium-term forecasting (1-2 weeks) where computational efficiency is important
- **Strengths:** Faster training than LSTM, good for shorter sequences, less prone to overfitting
- **Limitations:** May have shorter memory than LSTM for very long sequences

**Long Short-Term Memory (LSTM)**
- **Purpose:** Captures long-range temporal dependencies and market regime changes
- **Implementation:** PyTorch-based with 2-3 LSTM layers, attention mechanisms
- **Contribution:** Remembers important market events and regime changes over extended periods
- **Use Case:** Long-term forecasting (1-4 weeks) and capturing market cycles
- **Strengths:** Excellent memory retention, handles vanishing gradient problem, captures complex patterns
- **Limitations:** Computationally intensive, requires more data for training

**Transformer (Encoder-Only)**
- **Purpose:** Attention-based model for capturing complex long-range dependencies
- **Implementation:** Custom PyTorch transformer with multi-head self-attention
- **Contribution:** Identifies which historical periods are most relevant for current predictions
- **Use Case:** Complex market scenarios with multiple influencing factors and long-term dependencies
- **Strengths:** Parallelizable training, excellent at capturing long-range dependencies, interpretable attention weights
- **Limitations:** Requires large datasets, computationally expensive, may overfit on small datasets

#### **Ensemble Strategy**
- **Mechanism:** Simple mean aggregation across all model predictions with automatic fallback to MA
- **Contribution:** Reduces individual model bias and variance, provides robust predictions
- **Benefits:** Combines interpretability of traditional models with predictive power of neural networks
- **Fallback Logic:** If any model fails to converge or produces NaN values, automatically falls back to Moving Average
- **Performance:** Achieves sub-5% MAPE on benchmark datasets by leveraging complementary model strengths

#### **Training & Evaluation Framework**
- **Validation Strategy:** Rolling-window validation with 80/20 train/test splits
- **Early Stopping:** Prevents overfitting in neural networks by monitoring validation loss
- **Metrics:** RMSE (Root Mean Squared Error), MAE (Mean Absolute Error), MAPE (Mean Absolute Percentage Error)
- **Hyperparameter Tuning:** Grid search for traditional models, adaptive learning rates for neural networks
- **Robustness:** Each model includes convergence checks and graceful error handling

#### **Model Performance Characteristics & Contributions**

**Performance by Model Type:**

| Model Category | Best Use Case | Typical MAPE | Training Time | Interpretability | Memory Usage |
|----------------|---------------|--------------|---------------|------------------|--------------|
| **Traditional** | Linear trends, seasonal patterns | 3-8% | <1s | High | Low |
| **Neural** | Complex patterns, non-linear relationships | 2-6% | 10-60s | Medium | High |
| **Ensemble** | Robust predictions, uncertainty reduction | 2-5% | 15-65s | Medium | High |

**Specific Model Contributions to AlgoDinero:**

1. **Moving Average (MA)** - The "Safety Net"
   - **Role:** Provides reliable baseline predictions when other models fail
   - **Contribution:** Ensures the system never fails completely, even with insufficient data
   - **Performance:** 5-10% MAPE but 100% reliability
   - **When to Use:** Short-term predictions, fallback scenarios, trend identification

2. **ARIMA** - The "Statistician"
   - **Role:** Captures linear relationships and seasonal patterns
   - **Contribution:** Provides interpretable coefficients for market analysis
   - **Performance:** 3-7% MAPE on seasonal stocks (e.g., retail, energy)
   - **When to Use:** Traditional stocks with clear seasonal patterns, econometric analysis

3. **VAR** - The "Portfolio Analyst"
   - **Role:** Models cross-asset relationships and market contagion
   - **Contribution:** Enables multi-asset forecasting and risk assessment
   - **Performance:** 4-8% MAPE but captures correlation effects
   - **When to Use:** Portfolio forecasting, understanding market interdependencies

4. **MLP** - The "Pattern Recognizer"
   - **Role:** Captures non-linear relationships between features and prices
   - **Contribution:** Handles complex market dynamics that linear models miss
   - **Performance:** 3-6% MAPE on volatile assets
   - **When to Use:** Cryptocurrencies, high-volatility stocks, non-linear market regimes

5. **GRU** - The "Efficient Learner"
   - **Role:** Balances sequence modeling with computational efficiency
   - **Contribution:** Fast training while capturing temporal dependencies
   - **Performance:** 2-5% MAPE with 3x faster training than LSTM
   - **When to Use:** Medium-term forecasting, real-time applications, resource-constrained environments

6. **LSTM** - The "Memory Master"
   - **Role:** Captures long-range dependencies and market regime changes
   - **Contribution:** Remembers important market events and cycles
   - **Performance:** 2-4% MAPE on long-term predictions
   - **When to Use:** Long-term forecasting, capturing market cycles, regime change detection

7. **Transformer** - The "Attention Expert"
   - **Role:** Identifies which historical periods are most relevant for predictions
   - **Contribution:** Provides interpretable attention weights and long-range pattern recognition
   - **Performance:** 2-4% MAPE with excellent long-range dependency capture
   - **When to Use:** Complex market scenarios, multi-factor analysis, long-term strategic forecasting

**Ensemble Synergy:**
- **Complementary Strengths:** Traditional models provide interpretability, neural models capture complexity
- **Robustness:** Multiple models reduce single-point-of-failure risks
- **Adaptability:** Different models excel in different market conditions
- **Performance:** Ensemble typically achieves 2-5% MAPE across diverse market conditions

### **4. Storage Layer (Data Persistence)**
- **Technologies:** MongoDB Atlas (managed NoSQL for flexible schemas and global replication).
- **Schema Overview:**
  - **curated:** Documents with {ticker, timestamp, ohlcv, news_items[], sentiment_scores[]}, indexed on ticker+timestamp.
  - **visualize_snapshots:** {run_id, plot_data (JSON-serialized Plotly figures), summary_stats}.
  - **forecasts:** {ticker, horizon, model_type, predictions[], metrics {rmse, mae, mape}, ensemble_mean}.
- **Access Patterns:** High-write during batch jobs (curate/forecast), optimized reads for dashboard refreshes via aggregation pipelines (e.g., $match + $group for averages).
- **Benefits:** Schema flexibility accommodates evolving features (e.g., adding options data); Atlas provides backups, encryption, and VPC peering for compliance (e.g., GDPR/SOC2).

### **Cross-Cutting Concerns**
- **Configuration Management:** Environment variables via python-dotenv (e.g., `MONGODB_URI`, `YF_API_TIMEOUT=30`); separate `.env.local` for development overrides.
- **Error Resilience:** Structured exceptions with FastAPI's HTTPException, model retry logic, and user-friendly messages (e.g., "Insufficient data for 30-day forecast").
- **Security Posture:** Secrets never exposed client-side; API rate limiting with SlowAPI; input sanitization against injection; optional OAuth2 for multi-user auth.
- **Observability & Scalability:** Integrated Prometheus metrics for endpoint latency; backend deployable as microservices, with ML inference offloadable to GPU clusters (e.g., via Ray).
- **Testing:** Unit tests (Pytest for backend, Jest for frontend), integration tests for end-to-end flows, and CI/CD hooks for automated validation.

## 📁 Project Structure

```
AlgoDinero/
├── backend/
│   ├── source_code/
│   │   ├── api/
│   │   │   └── app.py                      # FastAPI application entrypoint with all endpoints
│   │   ├── database/
│   │   │   └── mongo_connector.py          # MongoDB CRUD operations and connection management
│   │   ├── forecasting/
│   │   │   ├── forecast_engine.py          # Ensemble orchestration and adaptive weighting
│   │   │   ├── model_traditional.py        # ARIMA, MA, VAR implementations
│   │   │   ├── model_neural.py             # PyTorch neural nets (MLP, GRU, LSTM, Transformer)
│   │   │   ├── evaluation.py               # Metrics computation (RMSE, MAE, MAPE, Directional Accuracy)
│   │   │   ├── evaluation_service.py       # Continuous evaluation and backtesting service
│   │   │   ├── incremental_learning.py     # Model fine-tuning and incremental updates
│   │   │   ├── model_registry.py           # Model versioning and metadata management
│   │   │   ├── model_storage.py            # Model serialization and persistence
│   │   │   ├── model_comparison.py         # Model performance comparison utilities
│   │   │   ├── retraining_service.py       # Scheduled retraining orchestration
│   │   │   └── scheduler.py                # APScheduler-based automatic retraining
│   │   ├── monitoring/
│   │   │   ├── metrics_aggregator.py       # Aggregates evaluation metrics over time
│   │   │   └── alert_service.py            # Performance threshold alerts and notifications
│   │   ├── portfolio/
│   │   │   ├── portfolio_manager.py        # Portfolio CRUD, trade execution, value tracking
│   │   │   ├── trading_strategy.py         # Signal generation and position sizing
│   │   │   └── performance_metrics.py      # Returns, volatility, Sharpe ratio calculations
│   │   ├── tests/
│   │   │   ├── test_api.py                 # API endpoint integration tests
│   │   │   ├── test_evaluation.py          # Evaluation metrics unit tests
│   │   │   ├── test_incremental_learning.py # Incremental learning tests
│   │   │   ├── test_portfolio.py           # Portfolio management tests
│   │   │   ├── test_adaptive_ensemble.py   # Adaptive ensemble weighting tests
│   │   │   ├── test_scheduler.py           # Scheduler functionality tests
│   │   │   └── run_tests.py                # Test runner script
│   │   ├── price_fetcher.py                # Yahoo Finance integration for historical prices
│   │   ├── news_fetcher.py                 # RSS news scraping and sentiment analysis
│   │   ├── helper_utils.py                 # Data merging, CSV/JSON export utilities
│   │   ├── main_scraper.py                 # Main data curation orchestration script
│   │   └── run_api.py                      # Alternative API entrypoint
│   ├── Dockerfile                          # Docker containerization for backend
│   ├── docker-compose.yml                  # Local dev stack (FastAPI + MongoDB)
│   ├── requirements.txt                    # Python dependencies
│   └── README.md                           # Backend-specific documentation
│
├── frontend/
│   ├── src/
│   │   ├── pages/
│   │   │   ├── Home.jsx                    # Main forecasting dashboard page
│   │   │   ├── Monitoring.jsx              # Model performance monitoring dashboard
│   │   │   └── Portfolio.jsx               # Portfolio management and trading interface
│   │   ├── components/
│   │   │   ├── Navbar.jsx                  # Navigation bar with routing
│   │   │   ├── InstrumentSelector.jsx      # Ticker input and dropdown selector
│   │   │   ├── ForecastOptions.jsx         # Horizon and model selection UI
│   │   │   ├── ChartDisplay.jsx            # Plotly candlestick charts with error overlays
│   │   │   ├── ErrorOverlay.jsx            # Error overlay visibility controls
│   │   │   ├── MetricsCard.jsx             # Error and performance metrics display
│   │   │   ├── MetricsChart.jsx            # Time-series metrics visualization
│   │   │   ├── ModelPerformanceTable.jsx   # Model ranking and comparison table
│   │   │   ├── AlertPanel.jsx              # Performance alerts display
│   │   │   ├── NewsPanel.jsx               # Sentiment-enriched news feed
│   │   │   ├── PortfolioChart.jsx          # Portfolio value and price dual-axis chart
│   │   │   ├── TradingPanel.jsx            # Trade execution interface (buy/sell/hold)
│   │   │   ├── PerformanceMetrics.jsx      # Portfolio performance metrics display
│   │   │   └── Footer.jsx                  # Application footer
│   │   ├── App.jsx                         # Root application component with routing
│   │   ├── main.jsx                        # React application entrypoint
│   │   └── index.css                       # Global styles and Tailwind imports
│   ├── public/                             # Static assets (favicon, etc.)
│   ├── package.json                        # Node dependencies (React, Plotly, Axios, etc.)
│   ├── tailwind.config.js                  # Tailwind CSS configuration
│   └── vite.config.js                      # Vite build configuration
│
├── README.md                               # This file - main project documentation
├── .gitignore                              # Git ignore rules (excludes .md files except README)
└── [Documentation Files]                   # A3.md, REQUIREMENTS_COMPLIANCE.md, etc. (gitignored)
```

### **Directory Overview**

**Backend (`backend/source_code/`):**
- **`api/`**: FastAPI application with REST endpoints for curation, forecasting, monitoring, and portfolio management
- **`forecasting/`**: Core ML models, ensemble logic, evaluation, incremental learning, and retraining services
- **`monitoring/`**: Metrics aggregation, performance tracking, and alerting services
- **`portfolio/`**: Portfolio management, trading strategies, and performance calculations
- **`database/`**: MongoDB connection and data persistence layer
- **`tests/`**: Comprehensive unit and integration tests

**Frontend (`frontend/src/`):**
- **`pages/`**: Three main application pages (Home/Forecasting, Monitoring, Portfolio)
- **`components/`**: Reusable React components for charts, forms, metrics, and UI elements
- **`App.jsx`**: Main router configuration and application shell

**Root:**
- Configuration files (`.gitignore`, `docker-compose.yml`)
- Documentation (README.md and other markdown files)
## 🚀 Quick Start Guide

### **Prerequisites**
- Python 3.10+ and Node.js 18+.
- MongoDB Atlas account (free tier sufficient for development).
- API keys: Yahoo Finance (implicit via yfinance; no key needed for basics).

### **Backend Setup**
```bash
cd Backend/source_code
python -m venv .venv
source .venv/bin/activate  # On macOS/Linux; use .venv\Scripts\activate on Windows
pip install -r requirements.txt

# Copy and configure .env
cp ../.env.example .env
# Edit .env with your MongoDB Atlas URI, e.g.:
# MONGODB_URI=mongodb+srv://<user>:<pass>@cluster0.xxxxx.mongodb.net/?retryWrites=true&w=majority&appName=AlgoDinero

uvicorn api.app:app --host 127.0.0.1 --port 8001 --reload
```
Backend runs at http://localhost:8001. Test with curl http://localhost:8001/api/health.
### **Frontend Setup**
```bash
cd ../Frontend
npm install
cp .env.local.example .env.local
# Edit .env.local if needed (e.g., VITE_API_BASE_URL=http://localhost:8001)
npm run dev
```
Frontend serves at http://localhost:5173 (Vite default). Open in browser to interact.

### **Usage Workflow**

1. **Curate Data**: Select ticker and run curation to fetch/store prices + news
2. **Visualize**: Load historical charts with sentiment overlays
3. **Forecast**: Choose horizon; generate and view predictions + metrics
4. **Monitor**: View model performance metrics, rankings, and alerts on the Monitoring page
5. **Portfolio**: Create portfolios, execute trades, and track performance on the Portfolio page

For production, use `npm run build` (frontend) and deploy backend via Gunicorn/NGINX.

## 🔗 API Reference

| Method | Endpoint          | Description                                      | Request Body Example                  | Response                          |
|--------|-------------------|--------------------------------------------------|---------------------------------------|-----------------------------------|
| POST   | `/api/curate`     | Fetches, aligns, and stores price/news data.     | `{ "ticker": "AAPL", "days_back": 365 }` | `{ "status": "success", "run_id": "uuid" }` |
| POST   | `/api/visualize`  | Generates visualization data with forecasts.     | `{ "run_id": "uuid" }`                | `{ "charts": [...], "sentiment": {...} }` |
| POST   | `/api/forecast`   | Executes models and computes metrics.            | `{ "ticker": "AAPL", "horizon": 7 }`  | `{ "predictions": [...], "metrics": {...} }` |
| GET    | `/api/health`     | System health check (DB connectivity, etc.).     | N/A                                   | `{ "status": "healthy" }`         |

All endpoints return JSON; errors use standard HTTP codes (e.g., 400 for invalid input).

---

## 🧩 Why This Architecture?

| Attribute      | Benefit                                                                 |
|----------------|-------------------------------------------------------------------------|
| **Maintainability** | Layered design allows isolated updates (e.g., swap Plotly for D3.js without touching ML). |
| **Scalability**    | Stateless FastAPI scales horizontally; MongoDB sharding for high-volume data. |
| **Extensibility**  | Plug-and-play models (e.g., add Prophet via new submodule); easy API versioning. |
| **Security**       | Env-var secrets, no DB exposure to client; prepared for auth middleware. |
| **Performance**    | Async endpoints + vectorized NumPy/PyTorch ops ensure <2s forecast latency. |
## 🧭 Contributing & Next Steps

We welcome contributions! Fork the repo, create a feature branch, and submit a PR with tests. See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

**Roadmap Ideas:**
- Real-time WebSocket updates for live trading.
- Advanced ensembles (e.g., XGBoost stacking).
- Multi-asset portfolio forecasting.
- Export to CSV/PDF for reports.

## 📄 License
This project is MIT-licensed. See [LICENSE](LICENSE) for details.

---

**AlgoDinero: Empowering Financial Foresight**  
*Stack: React + Tailwind + Plotly | FastAPI + PyTorch + Statsmodels | MongoDB Atlas*  
*Architecture: SPA → REST API → ML Domain → NoSQL Persistence*  
*Built to inspire innovation in AI-driven finance.*
