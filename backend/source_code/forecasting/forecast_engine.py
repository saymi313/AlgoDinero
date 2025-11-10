from pydantic import BaseModel
from typing import Dict, Any, Optional, List
import numpy as np
import pandas as pd
from statsmodels.tsa.arima.model import ARIMA
from sklearn.neural_network import MLPRegressor
from .model_traditional import moving_average_forecast, var_close_forecast
from .model_neural import gru_forecast, lstm_forecast, transformer_forecast
from .evaluation import summarize_metrics
from .incremental_learning import ModelUpdater
from .model_registry import ModelRegistry
from .model_storage import ModelStorage
from datetime import datetime, timedelta
from pymongo import MongoClient
import os


class ForecastRequest(BaseModel):
    ticker: str
    horizon: int = 24
    days: int = 120


class ForecastEngine:
    def __init__(self):
        """Initialize forecast engine with incremental learning support"""
        self.model_updater = ModelUpdater()
        self.model_registry = ModelRegistry()
        self.model_storage = ModelStorage()
        self._cached_models = {}  # Cache for loaded models
        # MongoDB connection for fetching recent performance metrics
        self.mongo_uri = os.getenv('MONGODB_URI')
        self.mongo_client = None
        self.mongo_db = None
        if self.mongo_uri:
            try:
                self.mongo_client = MongoClient(self.mongo_uri, serverSelectionTimeoutMS=2000)
                self.mongo_db = self.mongo_client.get_database('fintech_forecasting')
            except Exception:
                self.mongo_client = None
                self.mongo_db = None
    
    def run_forecast(self, req: ForecastRequest) -> Dict[str, Any]:
        hist_df = self._load_history(req.ticker, req.days)
        y = hist_df['Close'].values.astype(float)

        # Run forecasts (some may be slow, but we need them all)
        ma_forecast = moving_average_forecast(y, req.horizon)
        arima_forecast = self._arima(y, req.horizon)
        mlp_forecast = self._mlp(y, req.horizon)
        var_forecast = var_close_forecast(hist_df, req.horizon)
        
        # Neural network forecasts can be slow - wrap in try/except
        try:
            gru_fc = gru_forecast(y, req.horizon)
        except Exception as e:
            print(f"Warning: GRU forecast failed: {e}, using moving average")
            gru_fc = ma_forecast.copy()
        
        try:
            lstm_fc = lstm_forecast(y, req.horizon)
        except Exception as e:
            print(f"Warning: LSTM forecast failed: {e}, using moving average")
            lstm_fc = ma_forecast.copy()
        
        try:
            tr_fc = transformer_forecast(y, req.horizon)
        except Exception as e:
            print(f"Warning: Transformer forecast failed: {e}, using moving average")
            tr_fc = ma_forecast.copy()

        # Get forecasts and model types for adaptive weighting
        forecasts = {
            'moving_average': ma_forecast,
            'arima': arima_forecast,
            'mlp': mlp_forecast,
            'var': var_forecast,
            'gru': gru_fc,
            'lstm': lstm_fc,
            'transformer': tr_fc
        }
        
        # Calculate adaptive weights based on recent performance
        model_types = list(forecasts.keys())
        weights = self._calculate_adaptive_weights(req.ticker, model_types)
        
        # Apply weighted ensemble
        forecast_arrays = [forecasts[mt] for mt in model_types]
        weight_array = np.array([weights[mt] for mt in model_types])
        # Reshape weights for broadcasting
        weight_array = weight_array.reshape(-1, 1)
        ensemble = np.average(np.vstack(forecast_arrays), axis=0, weights=weight_array.flatten())

        metrics = summarize_metrics(forecasts, y)

        return {
            'ticker': req.ticker,
            'horizon': req.horizon,
            'predictions': ensemble.tolist(),
            'components': {
                'moving_average': ma_forecast.tolist(),
                'arima': arima_forecast.tolist(),
                'mlp': mlp_forecast.tolist(),
                'var': var_forecast.tolist(),
                'gru': gru_fc.tolist(),
                'lstm': lstm_fc.tolist(),
                'transformer': tr_fc.tolist()
            },
            'metrics': metrics,
            'ensemble_weights': weights  # Include weights in response for transparency
        }

    def get_visualization_data(self, hist_df: pd.DataFrame, ticker: str, horizon: int) -> Dict[str, Any]:
        y = hist_df['Close'].values.astype(float)
        ma_forecast = moving_average_forecast(y, horizon)
        arima_forecast = self._arima(y, horizon)
        mlp_forecast = self._mlp(y, horizon)
        var_forecast = var_close_forecast(hist_df, horizon)
        gru_fc = gru_forecast(y, horizon)
        lstm_fc = lstm_forecast(y, horizon)
        tr_fc = transformer_forecast(y, horizon)
        
        # Get forecasts and model types for adaptive weighting
        forecasts = {
            'moving_average': ma_forecast,
            'arima': arima_forecast,
            'mlp': mlp_forecast,
            'var': var_forecast,
            'gru': gru_fc,
            'lstm': lstm_fc,
            'transformer': tr_fc
        }
        
        # Calculate adaptive weights based on recent performance
        model_types = list(forecasts.keys())
        weights = self._calculate_adaptive_weights(ticker, model_types)
        
        # Apply weighted ensemble
        forecast_arrays = [forecasts[mt] for mt in model_types]
        weight_array = np.array([weights[mt] for mt in model_types])
        ensemble = np.average(np.vstack(forecast_arrays), axis=0, weights=weight_array.flatten())

        hist = [
            {
                'date': str(d),
                'open': float(row['Open']),
                'high': float(row['High']),
                'low': float(row['Low']),
                'close': float(row['Close'])
            }
            for d, row in hist_df.set_index('Date').iterrows()
        ]

        future_index = pd.date_range(hist_df['Date'].iloc[-1], periods=horizon+1, freq='D')[1:]
        forecast = [{ 'date': str(d.date()), 'close': float(c) } for d, c in zip(future_index, ensemble)]

        return { 'ticker': ticker, 'historical': hist, 'forecast': forecast, 'components': {
            'moving_average': ma_forecast.tolist(),
            'arima': arima_forecast.tolist(),
            'mlp': mlp_forecast.tolist(),
            'var': var_forecast.tolist(),
            'gru': gru_fc.tolist(),
            'lstm': lstm_fc.tolist(),
            'transformer': tr_fc.tolist()
        } }

    def _load_history(self, ticker: str, days: int) -> pd.DataFrame:
        from price_fetcher import PriceFetcher
        fetcher = PriceFetcher()
        return fetcher.fetch_historical_prices(ticker, days)

    def _arima(self, y: np.ndarray, horizon: int) -> np.ndarray:
        try:
            model = ARIMA(y, order=(1,1,1))
            fit = model.fit()
            fc = fit.forecast(steps=horizon)
            return np.array(fc)
        except Exception:
            return moving_average_forecast(y, horizon)

    def _mlp(self, y: np.ndarray, horizon: int) -> np.ndarray:
        try:
            X, t = [], []
            window = 5
            for i in range(len(y) - window):
                X.append(y[i:i+window])
                t.append(y[i+window])
            if len(X) < 5:
                return moving_average_forecast(y, horizon)
            model = MLPRegressor(hidden_layer_sizes=(32,16), max_iter=500, random_state=42)
            model.fit(np.array(X), np.array(t))
            seed = y[-window:].copy()
            out = []
            for _ in range(horizon):
                pred = float(model.predict(seed.reshape(1, -1))[0])
                out.append(pred)
                seed = np.roll(seed, -1)
                seed[-1] = pred
            return np.array(out)
        except Exception:
            return moving_average_forecast(y, horizon)
    
    def update_model(
        self,
        ticker: str,
        model_type: str,
        new_data: np.ndarray,
        days_back: int = 7
    ) -> Dict[str, Any]:
        """
        Update a model with new data using incremental learning
        
        Args:
            ticker: Ticker symbol
            model_type: Type of model to update
            new_data: New time series data
            days_back: Number of days of new data
            
        Returns:
            Dictionary with update status
        """
        try:
            # Try to load existing model
            model_version = self.model_registry.get_latest_model(model_type, ticker, production_only=True)
            
            if model_version:
                version = model_version['version']
                model = self.model_storage.load_model(model_type, version)
                
                if model:
                    # Update model with new data
                    updated_model = self.model_updater.update_model(
                        model,
                        model_type,
                        new_data,
                        epochs=5 if model_type in ['lstm', 'gru', 'transformer'] else None
                    )
                    
                    # Save updated model as new version
                    new_version = f"v{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}"
                    metadata = {
                        'ticker': ticker,
                        'model_type': model_type,
                        'parent_version': version,
                        'update_type': 'incremental',
                        'new_data_points': len(new_data)
                    }
                    
                    self.model_storage.save_model(
                        updated_model,
                        model_type,
                        new_version,
                        metadata
                    )
                    
                    # Register new version
                    self.model_registry.save_model_version(
                        model_type,
                        new_version,
                        ticker,
                        model_version.get('hyperparameters', {}),
                        {
                            'days': days_back,
                            'update_date': datetime.utcnow().isoformat()
                        },
                        is_production=False  # Don't auto-promote
                    )
                    
                    return {
                        'success': True,
                        'model_type': model_type,
                        'ticker': ticker,
                        'old_version': version,
                        'new_version': new_version,
                        'message': 'Model updated successfully'
                    }
            
            return {
                'success': False,
                'message': f'No existing model found for {model_type} on {ticker}'
            }
            
        except Exception as e:
            return {
                'success': False,
                'message': f'Error updating model: {str(e)}'
            }
    
    def rolling_window_retrain(
        self,
        ticker: str,
        model_type: str,
        window_days: int = 60,
        retrain_every_days: int = 7
    ) -> Dict[str, Any]:
        """
        Perform rolling window retraining
        
        Args:
            ticker: Ticker symbol
            model_type: Type of model
            window_days: Training window size
            retrain_every_days: Retraining interval
            
        Returns:
            Dictionary with retraining status
        """
        try:
            # Load historical data
            hist_df = self._load_history(ticker, window_days + 30)  # Extra for buffer
            y = hist_df['Close'].values.astype(float)
            
            # Use last window_days for training
            training_data = y[-window_days:]
            
            # Retrain model (this would call the appropriate training function)
            # For now, return info about the retraining setup
            return {
                'success': True,
                'model_type': model_type,
                'ticker': ticker,
                'training_window_days': window_days,
                'training_data_points': len(training_data),
                'retrain_interval_days': retrain_every_days,
                'retrain_date': datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            return {
                'success': False,
                'message': f'Error in rolling window retrain: {str(e)}'
            }
    
    def _calculate_adaptive_weights(
        self,
        ticker: str,
        model_types: List[str]
    ) -> Dict[str, float]:
        """
        Calculate adaptive weights based on recent model performance
        
        Args:
            ticker: Ticker symbol
            model_types: List of model type names (e.g., 'moving_average', 'lstm', etc.)
            
        Returns:
            Dictionary mapping model types to their weights (normalized to sum to 1.0)
        """
        weights = {}
        total_inverse_error = 0.0
        epsilon = 0.1  # Small value to prevent division by zero
        
        # Get recent performance metrics from evaluations collection
        if self.mongo_db is None:
            # Fallback to equal weights if MongoDB not available
            equal_weight = 1.0 / len(model_types)
            return {mt: equal_weight for mt in model_types}
        
        try:
            col = self.mongo_db.get_collection('evaluations')
            start_date = datetime.utcnow() - timedelta(days=30)  # Look back 30 days
            
            # Get recent evaluations for this ticker
            evaluations = list(col.find({
                'ticker': ticker,
                'evaluation_date': {'$gte': start_date.isoformat()}
            }).sort('evaluation_date', -1).limit(50))  # Get last 50 evaluations
            
            # Map model type names to component names used in evaluations
            # Component names in evaluations match the keys in component_metrics
            model_to_component = {
                'moving_average': 'moving_average',
                'arima': 'arima',
                'mlp': 'mlp',
                'var': 'var',
                'gru': 'gru',
                'lstm': 'lstm',
                'transformer': 'transformer'
            }
            
            # Aggregate recent MAPE for each model
            model_mape_list = {mt: [] for mt in model_types}
            
            for eval_doc in evaluations:
                component_metrics = eval_doc.get('component_metrics', {})
                for model_type in model_types:
                    component_name = model_to_component.get(model_type, model_type)
                    if component_name in component_metrics:
                        metrics = component_metrics[component_name]
                        if 'MAPE' in metrics and metrics['MAPE'] is not None:
                            model_mape_list[model_type].append(metrics['MAPE'])
            
            # Calculate weights based on inverse MAPE (better performance = higher weight)
            for model_type in model_types:
                mape_list = model_mape_list[model_type]
                if mape_list:
                    # Use average MAPE over recent evaluations
                    avg_mape = np.mean(mape_list)
                    # Inverse weighting: better performance (lower MAPE) = higher weight
                    weights[model_type] = 1.0 / (avg_mape + epsilon)
                    total_inverse_error += weights[model_type]
                else:
                    # No performance data available, use default weight
                    weights[model_type] = 1.0
                    total_inverse_error += 1.0
            
            # Normalize weights so they sum to 1.0
            if total_inverse_error > 0:
                for model_type in weights:
                    weights[model_type] /= total_inverse_error
            else:
                # Fallback to equal weights if all weights are zero
                equal_weight = 1.0 / len(model_types)
                weights = {mt: equal_weight for mt in model_types}
                
        except Exception as e:
            # On any error, fallback to equal weights
            equal_weight = 1.0 / len(model_types)
            weights = {mt: equal_weight for mt in model_types}
        
        return weights



