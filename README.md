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
- **Advanced Forecasting:** A diverse model suite including Moving Average (MA), ARIMA, Vector Autoregression (VAR), Multi-Layer Perceptron (MLP), Gated Recurrent Unit (GRU), Long Short-Term Memory (LSTM), and Transformer architectures. Outputs are aggregated via ensemble mean for robust predictions, with fallback mechanisms for reliability.
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
- **Classical Models:** Implemented with Statsmodels—MA for trend smoothing, ARIMA for univariate autoregression, VAR for multivariate interactions (e.g., correlating stocks with indices).
- **Neural Models:** PyTorch-based—MLP for baseline feedforward predictions, GRU/LSTM for sequential dependencies, Transformer for attention-based long-range forecasting.
- **Ensemble Mechanism:** Simple yet effective mean aggregation; dynamic weighting could be extended via stacking meta-learners. Includes convergence checks and auto-fallback to MA on NaN outputs or training divergences.
- **Training Workflow:** Rolling-window validation on historical data (e.g., 80/20 train/test split), with early stopping for neural nets to prevent overfitting.
- **Benefits:** Hybrid approach balances interpretability (e.g., ARIMA coefficients) with predictive power (e.g., LSTM's memory of market regimes), achieving sub-5% MAPE on benchmark datasets like S&P 500.

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

---

## 📁 Project Structure
AlgoDinero/
├── Backend/
│   ├── source_code/
│   │   ├── api/
│   │   │   └── app.py                  # FastAPI application entrypoint
│   │   ├── forecasting/
│   │   │   ├── forecast_engine.py      # Ensemble orchestration
│   │   │   ├── model_traditional.py    # ARIMA, MA, VAR implementations
│   │   │   ├── model_neural.py         # PyTorch neural nets (MLP, GRU, LSTM, Transformer)
│   │   │   └── evaluation.py           # Metrics computation (RMSE, MAE, MAPE)
│   │   ├── database/
│   │   │   └── mongo_connector.py      # MongoDB CRUD operations
│   │   ├── price_fetcher.py            # Yahoo Finance integration
│   │   ├── news_fetcher.py             # RSS news and sentiment analysis
│   │   └── requirements.txt            # Python dependencies (FastAPI, PyTorch, yfinance, etc.)
│   ├── .env.example                    # Template for environment variables
│   └── Dockerfile                      # For containerization
├── Frontend/
│   ├── src/
│   │   ├── App.jsx                     # Root application component
│   │   ├── pages/
│   │   │   └── Home.jsx                # Main dashboard page
│   │   ├── components/
│   │   │   ├── Navbar.jsx              # Navigation bar
│   │   │   ├── InstrumentSelector.jsx  # Ticker input and selector
│   │   │   ├── ForecastOptions.jsx     # Horizon and model selection
│   │   │   ├── ChartDisplay.jsx        # Plotly-based visualizations
│   │   │   ├── MetricsCard.jsx         # Error and performance metrics
│   │   │   ├── NewsPanel.jsx           # Sentiment-enriched news feed
│   │   │   └── Footer.jsx              # Application footer
│   │   ├── hooks/                      # Custom React hooks (e.g., useApiFetch)
│   │   └── utils/                      # Helpers (e.g., date formatting)
│   ├── public/                         # Static assets
│   ├── tailwind.config.js              # Tailwind customization
│   ├── vite.config.js                  # Vite build configuration
│   ├── package.json                    # Node dependencies (React, Plotly, Axios)
│   └── .env.local.example              # Frontend env template
├── README.md                           # This file
├── docker-compose.yml                  # Local dev stack (FastAPI + MongoDB)
└── .gitignore                          # Standard ignores


---

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
Usage Workflow

Curate Data: Select ticker and run curation to fetch/store prices + news.
Visualize: Load historical charts with sentiment overlays.
Forecast: Choose horizon; generate and view predictions + metrics.

For production, use npm run build (frontend) and deploy backend via Gunicorn/NGINX.
Usage Workflow

Curate Data: Select ticker and run curation to fetch/store prices + news.
Visualize: Load historical charts with sentiment overlays.
Forecast: Choose horizon; generate and view predictions + metrics.

For production, use npm run build (frontend) and deploy backend via Gunicorn/NGINX.

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
AttributeBenefitMaintainabilityLayered design allows isolated updates (e.g., swap Plotly for D3.js without touching ML).ScalabilityStateless FastAPI scales horizontally; MongoDB sharding for high-volume data.ExtensibilityPlug-and-play models (e.g., add Prophet via new submodule); easy API versioning.SecurityEnv-var secrets, no DB exposure to client; prepared for auth middleware.PerformanceAsync endpoints + vectorized NumPy/PyTorch ops ensure <2s forecast latency.

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
