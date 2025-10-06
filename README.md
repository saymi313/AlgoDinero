# AlgoDinero – FinTech Forecasting Dashboard

Modern React + FastAPI project for financial data curation, forecasting, and visualization.

## Features
- Frontend: Vite + React (JSX), Tailwind, Plotly charts, model overlays, sentiment and news panel
- Backend: FastAPI, data curation (prices + news), forecasting (MA/ARIMA/VAR/MLP/GRU/LSTM/Transformer) with ensemble and metrics
- Persistence: MongoDB Atlas (curated, visualize_snapshots, forecasts)

## Quick Start

### Backend
```bash
cd Backend/source_code
python -m venv .venv && . .venv/Scripts/activate
pip install -r ../requirements.txt

# Create .env (or .env.local) here with your MongoDB SRV URI
# MONGODB_URI=mongodb+srv://USER:PASSWORD@CLUSTER.mongodb.net/?retryWrites=true&w=majority&appName=AlgoDinero

uvicorn api.app:app --host 127.0.0.1 --port 8001 --reload
```

### Frontend
```bash
cd frontend
npm install
npm run dev
```

Open the app, set ticker/horizon, then:
- Curate → write curated rows to MongoDB
- Visualize → snapshot historical/forecast/news
- Forecast → write predictions, components, metrics

## API
- POST `/api/curate` { ticker, days }
- POST `/api/visualize` { ticker, days, horizon }
- POST `/api/forecast` { ticker, days, horizon }
- GET `/api/health`

## Repos & Structure
```
Backend/
  source_code/
    api/app.py
    forecasting/
      forecast_engine.py
      model_traditional.py
      model_neural.py
      evaluation.py
    database/mongo_connector.py
    price_fetcher.py
    news_fetcher.py

frontend/
  src/
    App.jsx
    pages/Home.jsx
    components/
      Navbar.jsx InstrumentSelector.jsx ForecastOptions.jsx ChartDisplay.jsx MetricsCard.jsx NewsPanel.jsx Footer.jsx
```

## Notes
- Do not commit secrets. `.env`/`.env.local` are loaded at runtime and should not be pushed.
- If Atlas auth fails: fix password, allow your IP, restart backend, check `/api/health`.


