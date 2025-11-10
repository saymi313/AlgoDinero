from fastapi import FastAPI, HTTPException, Body
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from datetime import date
from typing import List, Optional, Dict
from dotenv import load_dotenv, find_dotenv
from pathlib import Path

import sys, os
import pandas as pd
from datetime import datetime as dt
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from price_fetcher import PriceFetcher
from news_fetcher import NewsFetcher
from helper_utils import DataProcessor

from forecasting.forecast_engine import ForecastEngine, ForecastRequest
from forecasting.retraining_service import RetrainingService
from forecasting.model_registry import ModelRegistry
from forecasting.evaluation_service import EvaluationService
from forecasting.scheduler import RetrainingScheduler
from monitoring.metrics_aggregator import MetricsAggregator
from monitoring.alert_service import AlertService
from portfolio.portfolio_manager import PortfolioManager
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
retraining_service = RetrainingService()
model_registry = ModelRegistry()
evaluation_service = EvaluationService()
metrics_aggregator = MetricsAggregator()
alert_service = AlertService()
portfolio_manager = PortfolioManager()

# Initialize retraining scheduler (will be started on startup)
retraining_scheduler = None

# Start scheduler on app startup
@app.on_event("startup")
async def startup_event():
    """Start the retraining scheduler on application startup"""
    global retraining_scheduler
    try:
        # Initialize scheduler here to avoid issues during module import
        retraining_scheduler = RetrainingScheduler(retraining_service)
        retraining_scheduler.start(check_interval_hours=24, check_time="00:00")
        print("Retraining scheduler started successfully")
    except Exception as e:
        print(f"Warning: Could not start retraining scheduler: {str(e)}")
        import traceback
        traceback.print_exc()
        # Don't fail startup if scheduler can't start
        retraining_scheduler = None

@app.on_event("shutdown")
async def shutdown_event():
    """Stop the retraining scheduler on application shutdown"""
    global retraining_scheduler
    try:
        if retraining_scheduler is not None:
            retraining_scheduler.shutdown()
            print("Retraining scheduler stopped")
    except Exception as e:
        print(f"Warning: Error stopping retraining scheduler: {str(e)}")

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
            
            # Trigger evaluation asynchronously (non-blocking)
            # This allows the forecast to return immediately while evaluation runs in background
            if saved_id:
                try:
                    # Use threading to make evaluation truly async
                    import threading
                    def run_evaluation():
                        try:
                            evaluation_service.evaluate_predictions(
                                ticker=req.ticker,
                                days_back=7,
                                allow_recent=True
                            )
                        except Exception:
                            pass  # Silently fail in background thread
                    
                    thread = threading.Thread(target=run_evaluation, daemon=True)
                    thread.start()
                except Exception:
                    # Don't fail forecast if evaluation fails
                    pass
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
        
        # Calculate errors for past predictions where ground-truth is available
        errors = []
        if mongo.db is not None:
            try:
                # Get past forecasts for this ticker
                forecasts_col = mongo.db.get_collection('forecasts')
                past_forecasts = list(forecasts_col.find({
                    'ticker': req.ticker
                }).sort('created_at', -1).limit(5))
                
                for forecast_doc in past_forecasts:
                    forecast_date = forecast_doc.get('created_at')
                    if isinstance(forecast_date, str):
                        try:
                            forecast_date = dt.fromisoformat(forecast_date.replace('Z', '+00:00'))
                        except:
                            continue
                    
                    if not isinstance(forecast_date, dt):
                        continue
                    
                    # Get actual prices for the forecast period
                    forecast_horizon = forecast_doc.get('horizon', 24)
                    end_date = forecast_date.replace(tzinfo=None)
                    start_date = end_date
                    
                    # Fetch actual data for the period
                    try:
                        actual_df = price_fetcher.fetch_historical_prices(req.ticker, forecast_horizon + 5)
                        actual_df['Date'] = pd.to_datetime(actual_df['Date'])
                        
                        # Filter for the forecast period
                        mask = (actual_df['Date'] >= start_date) & (actual_df['Date'] <= end_date + pd.Timedelta(days=forecast_horizon))
                        actual_period = actual_df[mask]
                        
                        if len(actual_period) > 0:
                            predictions = forecast_doc.get('predictions', [])
                            actuals = actual_period['Close'].values.tolist()
                            
                            # Align and calculate errors
                            min_len = min(len(predictions), len(actuals))
                            for i in range(min_len):
                                if i < len(actual_period):
                                    error = {
                                        'date': str(actual_period.iloc[i]['Date'].date()),
                                        'predicted': float(predictions[i]),
                                        'actual': float(actuals[i]),
                                        'error': float(actuals[i] - predictions[i]),
                                        'error_pct': float(((actuals[i] - predictions[i]) / actuals[i]) * 100) if actuals[i] > 0 else 0.0
                                    }
                                    errors.append(error)
                    except Exception as e:
                        # Skip if error calculating
                        continue
            except Exception:
                # If error fetching, continue without errors
                pass
        
        vis['errors'] = errors
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

class RetrainRequest(BaseModel):
    ticker: str
    model_type: str = "all"
    days: int = 120
    window_days: Optional[int] = None

@app.post("/api/retrain")
def retrain(req: RetrainRequest):
    """Manually trigger model retraining"""
    try:
        if req.model_type == "all":
            result = retraining_service.retrain_all_models(req.ticker, req.days)
        else:
            result = retraining_service.retrain_model(
                req.ticker,
                req.model_type,
                req.days,
                window_days=req.window_days
            )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/models/versions")
def list_model_versions(
    model_type: Optional[str] = None,
    ticker: Optional[str] = None,
    production_only: bool = False
):
    """List all model versions"""
    try:
        versions = model_registry.list_model_versions(
            model_type=model_type,
            ticker=ticker,
            production_only=production_only
        )
        return {"versions": versions, "count": len(versions)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

class PromoteRequest(BaseModel):
    ticker: str
    model_type: str
    version: str

@app.post("/api/models/promote")
def promote_model(req: PromoteRequest):
    """Promote a model version to production"""
    try:
        success = model_registry.promote_model_version(
            req.model_type,
            req.version,
            req.ticker
        )
        if success:
            return {
                "success": True,
                "message": f"Model {req.model_type} version {req.version} promoted to production"
            }
        else:
            raise HTTPException(status_code=404, detail="Model version not found")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

class EvaluateRequest(BaseModel):
    ticker: str
    prediction_id: Optional[str] = None
    days_back: int = 7
    allow_recent: bool = True  # Allow evaluating recent forecasts using backtesting

@app.post("/api/evaluate")
def evaluate(req: EvaluateRequest):
    """Manually trigger evaluation of predictions"""
    try:
        result = evaluation_service.evaluate_predictions(
            req.ticker,
            req.prediction_id,
            req.days_back,
            allow_recent=req.allow_recent
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/evaluations/history")
def get_evaluation_history(
    ticker: str,
    model_type: Optional[str] = None,
    limit: int = 100
):
    """Get evaluation history for a ticker"""
    try:
        result = evaluation_service.get_evaluation_history(
            ticker,
            model_type,
            limit
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/monitoring/metrics")
def get_aggregated_metrics(
    ticker: Optional[str] = None,
    model_type: Optional[str] = None,
    window: str = 'daily',
    days_back: int = 30
):
    """Get aggregated metrics over time windows"""
    try:
        result = metrics_aggregator.aggregate_metrics(
            ticker=ticker,
            model_type=model_type,
            window=window,
            days_back=days_back
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/monitoring/alerts")
def get_alerts(
    ticker: Optional[str] = None,
    severity: Optional[str] = None,
    limit: int = 50
):
    """Get recent alerts"""
    try:
        alerts = alert_service.get_recent_alerts(
            ticker=ticker,
            severity=severity,
            limit=limit
        )
        return {
            'alerts': alerts,
            'count': len(alerts)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/monitoring/performance-trends")
def get_performance_trends(
    ticker: str,
    model_type: Optional[str] = None,
    days_back: int = 30
):
    """Get performance trends over time"""
    try:
        result = metrics_aggregator.compute_trends(
            ticker=ticker,
            model_type=model_type,
            days_back=days_back
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/monitoring/rankings")
def get_model_rankings(
    ticker: str,
    metric: str = 'MAPE',
    days_back: int = 30
):
    """Get model performance rankings"""
    try:
        result = metrics_aggregator.rank_models(
            ticker=ticker,
            metric=metric,
            days_back=days_back
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

class AlertConfigRequest(BaseModel):
    thresholds: Dict[str, float]

@app.post("/api/monitoring/alerts/configure")
def configure_alerts(req: AlertConfigRequest):
    """Configure alert thresholds"""
    try:
        result = alert_service.configure_thresholds(req.thresholds)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

class CreatePortfolioRequest(BaseModel):
    portfolio_id: Optional[str] = None
    initial_cash: float = 100000.0

@app.post("/api/portfolio/create")
def create_portfolio(req: CreatePortfolioRequest):
    """Create a new portfolio"""
    try:
        portfolio = portfolio_manager.create_portfolio(
            portfolio_id=req.portfolio_id,
            initial_cash=req.initial_cash
        )
        return portfolio
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

class TradeRequest(BaseModel):
    portfolio_id: str
    ticker: str
    action: str
    quantity: Optional[float] = None  # Changed to float to support decimal quantities (e.g., 0.5 Bitcoin)
    price: Optional[float] = None

@app.post("/api/portfolio/trade")
def execute_trade(req: TradeRequest):
    """Execute a trade"""
    try:
        result = portfolio_manager.execute_trade(
            req.portfolio_id,
            req.ticker,
            req.action,
            req.quantity,
            req.price
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

class TradeFromPredictionRequest(BaseModel):
    portfolio_id: str
    ticker: str
    predicted_price: float
    current_price: Optional[float] = None

@app.post("/api/portfolio/trade-from-prediction")
def trade_from_prediction(req: TradeFromPredictionRequest):
    """Execute trade based on prediction signal"""
    try:
        result = portfolio_manager.trade_based_on_prediction(
            req.portfolio_id,
            req.ticker,
            req.predicted_price,
            req.current_price
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/portfolio/list")
def list_portfolios():
    """List all portfolios"""
    try:
        portfolios = mongo.list_portfolios()
        return {
            'success': True,
            'portfolios': portfolios,
            'count': len(portfolios)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/portfolio/{portfolio_id}")
def get_portfolio(portfolio_id: str, skip_price_fetch: bool = True):
    """Get portfolio status"""
    try:
        # Skip price fetch by default for faster response
        portfolio = portfolio_manager.get_portfolio(portfolio_id, skip_price_fetch=skip_price_fetch)
        if not portfolio:
            raise HTTPException(status_code=404, detail="Portfolio not found")
        return portfolio
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/portfolio/{portfolio_id}/performance")
def get_portfolio_performance(portfolio_id: str):
    """Get portfolio performance metrics with history"""
    try:
        result = portfolio_manager.get_portfolio_performance(portfolio_id)
        # Include history in response for frontend chart
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/portfolio/{portfolio_id}/history")
def get_portfolio_history(portfolio_id: str, limit: int = 100):
    """Get transaction history for a portfolio"""
    try:
        transactions = mongo.get_transactions(portfolio_id, limit=limit)
        return {
            'portfolio_id': portfolio_id,
            'transactions': transactions,
            'count': len(transactions)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/scheduler/status")
def get_scheduler_status():
    """Get retraining scheduler status"""
    global retraining_scheduler
    try:
        if retraining_scheduler is None:
            return {
                'is_running': False,
                'jobs': [],
                'job_count': 0,
                'message': 'Scheduler not initialized'
            }
        status = retraining_scheduler.get_status()
        return status
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/scheduler/start")
def start_scheduler(check_interval_hours: int = 24, check_time: str = "00:00"):
    """Start the retraining scheduler"""
    global retraining_scheduler
    try:
        if retraining_scheduler is None:
            retraining_scheduler = RetrainingScheduler(retraining_service)
        retraining_scheduler.start(check_interval_hours=check_interval_hours, check_time=check_time)
        return {
            'success': True,
            'message': 'Scheduler started successfully',
            'status': retraining_scheduler.get_status()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/scheduler/stop")
def stop_scheduler():
    """Stop the retraining scheduler"""
    global retraining_scheduler
    try:
        if retraining_scheduler is None:
            return {
                'success': False,
                'message': 'Scheduler not initialized',
                'status': {'is_running': False, 'jobs': [], 'job_count': 0}
            }
        retraining_scheduler.stop()
        return {
            'success': True,
            'message': 'Scheduler stopped successfully',
            'status': retraining_scheduler.get_status()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


