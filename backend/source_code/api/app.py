from fastapi import FastAPI, HTTPException, Body
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from datetime import date
from typing import List, Optional
from dotenv import load_dotenv, find_dotenv
from pathlib import Path

import sys, os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from price_fetcher import PriceFetcher
from news_fetcher import NewsFetcher
from helper_utils import DataProcessor

from forecasting.forecast_engine import ForecastEngine, ForecastRequest
from database.mongo_connector import MongoConnector

# Load env files reliably regardless of current working directory
# Support .env.local (preferred) and .env as fallback
env_candidates = [
    # Prefer the app directory first
    str(Path(__file__).resolve().parent / ".env.local"),
    str(Path(__file__).resolve().parent / ".env"),
    # Then parent (Backend)
    str(Path(__file__).resolve().parents[1] / ".env.local"),
    str(Path(__file__).resolve().parents[1] / ".env"),
]
for p in env_candidates:
    if p and os.path.exists(p):
        # Allow later files to overwrite earlier values
        load_dotenv(p, override=True)

app = FastAPI(title="FinTech Forecasting API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

price_fetcher = PriceFetcher()
news_fetcher = NewsFetcher()
processor = DataProcessor()
forecast_engine = ForecastEngine()
mongo = MongoConnector()

class CurateRequest(BaseModel):
    ticker: str
    days: int = 60

def _extract_payload(model_cls, req_obj, **kwargs):
    if req_obj is not None:
        return req_obj
    return model_cls(**{k: v for k, v in kwargs.items() if v is not None})


@app.post("/api/curate")
def curate(req: CurateRequest | None = Body(default=None), ticker: str | None = None, days: int | None = None):
    try:
        req = _extract_payload(CurateRequest, req, ticker=ticker, days=days)
        # Normalize and validate ticker
        req.ticker = (req.ticker or '').strip().upper()
        if not req.ticker or req.ticker in {"STRING", "NULL", "NONE"}:
            raise HTTPException(status_code=422, detail="Invalid ticker symbol")
        if req.days is None or req.days <= 0:
            raise HTTPException(status_code=422, detail="'days' must be a positive integer")

        try:
            price_df = price_fetcher.fetch_historical_prices(req.ticker, req.days)
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"No data available for ticker {req.ticker}: {e}")
        end = date.today()
        start = end
        news_df = news_fetcher.fetch_daily_news(req.ticker, start, end)
        merged = processor.merge_datasets(price_df, news_df)
        # store curated data in Mongo instead of writing CSV/JSON
        inserted_id = mongo.save_curated_data(req.ticker, merged.to_dict('records'))
        if not inserted_id:
            raise HTTPException(status_code=500, detail="Failed to save curated data to MongoDB")
        return {"success": True, "rows": len(merged), "curated_id": inserted_id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/health")
def health():
    # Minimal env visibility to confirm backend sees the URI
    import os
    has_uri = bool(os.getenv("MONGODB_URI"))
    return {"ok": True, "has_mongodb_uri": has_uri}

@app.post("/api/forecast")
def forecast(req: ForecastRequest):
    try:
        result = forecast_engine.run_forecast(req)
        # Try to persist, but do not fail the request if DB is not configured
        try:
            saved_id = mongo.save_forecast_result(result)
            result['saved_id'] = saved_id
        except Exception:
            result['saved_id'] = None
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

class VisualizeRequest(BaseModel):
    ticker: str
    days: int = 60
    horizon: int = 24

@app.post("/api/visualize")
def visualize(req: VisualizeRequest | None = Body(default=None), ticker: str | None = None, days: int | None = None, horizon: int | None = None):
    try:
        req = _extract_payload(VisualizeRequest, req, ticker=ticker, days=days, horizon=horizon)
        # Normalize and validate
        req.ticker = (req.ticker or '').strip().upper()
        if not req.ticker or req.ticker in {"STRING", "NULL", "NONE"}:
            raise HTTPException(status_code=422, detail="Invalid ticker symbol")
        if req.days is None or req.days <= 0:
            raise HTTPException(status_code=422, detail="'days' must be a positive integer")
        if req.horizon is None or req.horizon <= 0:
            raise HTTPException(status_code=422, detail="'horizon' must be a positive integer")

        try:
            hist = price_fetcher.fetch_historical_prices(req.ticker, req.days)
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"No data available for ticker {req.ticker}: {e}")
        vis = forecast_engine.get_visualization_data(hist, req.ticker, req.horizon)
        # add summary stats and sentiment series
        stats = processor.generate_summary_stats(hist, req.ticker)
        # fetch news and align to derive sentiment time series
        start = hist['Date'].min() if 'Date' in hist.columns else None
        end = hist['Date'].max() if 'Date' in hist.columns else None
        sentiment_series = []
        news_items = []
        if start and end:
            news_df = news_fetcher.fetch_daily_news(req.ticker, start, end)
            merged = processor.merge_datasets(hist, news_df)
            if 'Mean_Sentiment_Score' in merged.columns:
                for d, row in merged[['Date','Mean_Sentiment_Score']].dropna().iterrows():
                    sentiment_series.append({'date': str(row['Date']), 'score': float(row['Mean_Sentiment_Score'])})
            # include latest headlines if available
            if 'Daily_Headlines' in merged.columns:
                for _, row in merged[['Date','Daily_Headlines']].tail(10).iterrows():
                    try:
                        # headlines stored as joined string; split if needed
                        heads = str(row['Daily_Headlines']).split('\n')
                        for h in heads:
                            h = h.strip()
                            if h:
                                news_items.append({ 'date': str(row['Date']), 'headline': h })
                    except Exception:
                        continue
        vis['summary'] = stats
        vis['sentiment'] = sentiment_series
        vis['news'] = news_items
        # persist snapshot (historical, forecast, components, news)
        saved = mongo.save_visualize_snapshot({
            'ticker': req.ticker,
            'horizon': req.horizon,
            'historical': vis.get('historical', []),
            'forecast': vis.get('forecast', []),
            'components': vis.get('components', {}),
            'news': news_items,
            'summary': stats,
        })
        if not saved:
            raise HTTPException(status_code=500, detail="Failed to save visualize snapshot to MongoDB")
        return vis
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


