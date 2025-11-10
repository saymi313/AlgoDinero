"""
Retraining Service
Handles periodic and scheduled model retraining
"""

from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
import numpy as np
import pandas as pd

from .model_registry import ModelRegistry
from .model_storage import ModelStorage
from .model_comparison import ModelComparator
from .evaluation import summarize_metrics


class RetrainingService:
    """Manages periodic retraining of forecasting models"""
    
    def __init__(self):
        """Initialize retraining service"""
        self.registry = ModelRegistry()
        self.storage = ModelStorage()
        self.comparator = ModelComparator()
        self._engine = None  # Lazy initialization to avoid circular import
    
    @property
    def engine(self):
        """Lazy load ForecastEngine to avoid circular imports"""
        if self._engine is None:
            from .forecast_engine import ForecastEngine
            self._engine = ForecastEngine()
        return self._engine
    
    def retrain_model(
        self,
        ticker: str,
        model_type: str,
        days: int = 120,
        horizon: int = 24,
        window_days: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Retrain a model on extended historical data
        
        Args:
            ticker: Ticker symbol
            model_type: Type of model to retrain
            days: Number of days of historical data to use
            horizon: Forecast horizon for validation
            window_days: Optional rolling window size (uses all data if None)
            
        Returns:
            Dictionary with retraining results
        """
        try:
            # Load historical data
            hist_df = self.engine._load_history(ticker, days)
            y = hist_df['Close'].values.astype(float)
            
            # Use rolling window if specified
            if window_days and len(y) > window_days:
                training_data = y[-window_days:]
            else:
                training_data = y
            
            # Get current production model for comparison
            current_model = self.registry.get_latest_model(model_type, ticker, production_only=True)
            
            # Retrain model (this is a simplified version - actual retraining would call model-specific training)
            # For now, we'll create a new version and evaluate it
            new_version = f"v{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}"
            
            # In a real implementation, you would:
            # 1. Train the model on training_data
            # 2. Save the trained model
            # 3. Evaluate on validation set
            # 4. Compare with current model
            # 5. Promote if better
            
            # For now, return retraining info
            result = {
                'success': True,
                'ticker': ticker,
                'model_type': model_type,
                'new_version': new_version,
                'training_data_points': len(training_data),
                'training_days': days,
                'window_days': window_days,
                'retrain_date': datetime.utcnow().isoformat(),
                'current_version': current_model.get('version') if current_model else None
            }
            
            return result
            
        except Exception as e:
            return {
                'success': False,
                'message': f'Error retraining model: {str(e)}'
            }
    
    def retrain_all_models(
        self,
        ticker: str,
        days: int = 120,
        model_types: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Retrain all models for a ticker
        
        Args:
            ticker: Ticker symbol
            days: Number of days of historical data
            model_types: List of model types to retrain (defaults to all)
            
        Returns:
            Dictionary with retraining results for all models
        """
        if model_types is None:
            model_types = ['lstm', 'gru', 'transformer', 'mlp', 'arima']
        
        results = {}
        
        for model_type in model_types:
            result = self.retrain_model(ticker, model_type, days)
            results[model_type] = result
        
        return {
            'ticker': ticker,
            'retrain_date': datetime.utcnow().isoformat(),
            'results': results
        }
    
    def compare_and_promote(
        self,
        ticker: str,
        model_type: str,
        old_version: str,
        new_version: str,
        validation_metrics: Dict[str, float],
        improvement_threshold: float = 5.0
    ) -> Dict[str, Any]:
        """
        Compare two model versions and promote if new one is better
        
        Args:
            ticker: Ticker symbol
            model_type: Type of model
            old_version: Old model version
            new_version: New model version
            validation_metrics: Metrics from new model validation
            improvement_threshold: Minimum improvement to promote
            
        Returns:
            Dictionary with comparison and promotion results
        """
        try:
            # Get old model metrics
            old_performance = self.registry.get_model_performance_history(
                model_type, old_version, ticker, limit=1
            )
            
            if old_performance:
                old_metrics = old_performance[0].get('metrics', {})
            else:
                # If no old metrics, assume new model is better
                old_metrics = {'MAE': float('inf'), 'RMSE': float('inf'), 'MAPE': float('inf')}
            
            # Compare models
            comparison = self.comparator.compare_models(
                old_metrics,
                validation_metrics,
                primary_metric='MAPE'
            )
            
            # Determine if should promote
            should_promote = self.comparator.should_promote(comparison, improvement_threshold)
            
            if should_promote:
                # Promote new model
                promoted = self.registry.promote_model_version(
                    model_type,
                    new_version,
                    ticker
                )
                
                # Save performance metrics
                self.registry.save_model_performance(
                    model_type,
                    new_version,
                    ticker,
                    validation_metrics
                )
                
                return {
                    'success': True,
                    'promoted': True,
                    'comparison': comparison,
                    'message': f'New model {new_version} promoted to production'
                }
            else:
                return {
                    'success': True,
                    'promoted': False,
                    'comparison': comparison,
                    'message': f'New model {new_version} not promoted (improvement: {comparison["improvement_percentage"]:.2f}% < {improvement_threshold}%)'
                }
                
        except Exception as e:
            return {
                'success': False,
                'promoted': False,
                'message': f'Error in comparison: {str(e)}'
            }
    
    def check_retrain_schedule(
        self,
        ticker: str,
        model_type: str,
        retrain_interval_days: int = 7
    ) -> Dict[str, Any]:
        """
        Check if model should be retrained based on schedule
        
        Args:
            ticker: Ticker symbol
            model_type: Type of model
            retrain_interval_days: Days between retraining
            
        Returns:
            Dictionary with schedule check results
        """
        current_model = self.registry.get_latest_model(model_type, ticker, production_only=True)
        
        if not current_model:
            return {
                'should_retrain': True,
                'reason': 'No production model found'
            }
        
        created_at = current_model.get('created_at')
        if isinstance(created_at, str):
            created_at = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
        elif not isinstance(created_at, datetime):
            created_at = datetime.utcnow()
        
        days_since_retrain = (datetime.utcnow() - created_at.replace(tzinfo=None)).days
        
        should_retrain = days_since_retrain >= retrain_interval_days
        
        return {
            'should_retrain': should_retrain,
            'days_since_retrain': days_since_retrain,
            'retrain_interval_days': retrain_interval_days,
            'current_version': current_model.get('version'),
            'last_retrain_date': created_at.isoformat() if isinstance(created_at, datetime) else str(created_at)
        }

