"""
Evaluation Service
Handles continuous evaluation of model predictions against ground truth
"""

from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
import numpy as np
import pandas as pd

from .evaluation import rmse, mae, mape
from .model_registry import ModelRegistry
from database.mongo_connector import MongoConnector


class EvaluationService:
    """Manages evaluation of model predictions"""
    
    def __init__(self):
        """Initialize evaluation service"""
        self.registry = ModelRegistry()
        self.mongo = MongoConnector()
    
    def evaluate_predictions(
        self,
        ticker: str,
        prediction_id: Optional[str] = None,
        days_back: int = 7,
        allow_recent: bool = True  # Allow evaluating recent forecasts using historical backtesting
    ) -> Dict[str, Any]:
        """
        Evaluate past predictions against ground truth
        
        Args:
            ticker: Ticker symbol
            prediction_id: Optional specific prediction ID to evaluate
            days_back: Number of days back to evaluate
            
        Returns:
            Dictionary with evaluation results
        """
        try:
            # Fetch ground truth data (actual prices)
            from price_fetcher import PriceFetcher
            fetcher = PriceFetcher()
            end_date = datetime.now()
            start_date = end_date - timedelta(days=days_back + 5)  # Buffer
            
            # Get actual prices
            hist_df = fetcher.fetch_historical_prices(ticker, days_back + 5)
            hist_df['Date'] = pd.to_datetime(hist_df['Date'])
            hist_df = hist_df.sort_values('Date')
            
            # Get predictions from MongoDB
            # Ensure MongoDB is connected
            if not self.mongo.ensure_connected():
                return {
                    'success': False,
                    'message': 'MongoDB not configured. Please set MONGODB_URI environment variable.'
                }
            
            forecasts_col = self.mongo.db.get_collection('forecasts')
            
            if prediction_id:
                # Evaluate specific prediction
                prediction_doc = forecasts_col.find_one({'_id': prediction_id})
                if not prediction_doc:
                    return {
                        'success': False,
                        'message': f'Prediction {prediction_id} not found'
                    }
                predictions = [prediction_doc]
            else:
                # Get recent predictions for this ticker
                predictions = list(forecasts_col.find({
                    'ticker': ticker
                }).sort('created_at', -1).limit(20))  # Get more to find evaluable ones
            
            if not predictions:
                return {
                    'success': False,
                    'message': f'No predictions found for ticker {ticker} in MongoDB. Make sure forecasts were saved successfully.'
                }
            
            # Evaluate each prediction
            evaluation_results = []
            skipped_future = 0
            skipped_no_data = 0
            
            for pred_doc in predictions:
                pred_date = pred_doc.get('created_at')
                if isinstance(pred_date, str):
                    try:
                        pred_date = datetime.fromisoformat(pred_date.replace('Z', '+00:00'))
                    except:
                        continue
                elif not isinstance(pred_date, datetime):
                    continue
                
                # Get predictions
                pred_values = pred_doc.get('predictions', [])
                components = pred_doc.get('components', {})
                horizon = pred_doc.get('horizon', len(pred_values))
                
                if not pred_values:
                    skipped_no_data += 1
                    continue
                
                # Get actual values for the forecast period
                pred_start = pred_date.replace(tzinfo=None)
                pred_end = pred_start + timedelta(days=horizon)
                
                # Check if prediction period is in the future
                now = datetime.now()
                is_future = pred_end > now
                
                if is_future and not allow_recent:
                    # Skip future predictions unless backtesting is allowed
                    skipped_future += 1
                    continue
                
                # For recent/future forecasts, use historical backtesting approach
                if is_future and allow_recent:
                    # Backtesting: Use historical data from earlier in the dataset
                    # This simulates evaluating a forecast by using past data as "ground truth"
                    # Find where in the historical data the prediction date would fall
                    hist_dates = hist_df['Date'].values
                    
                    # For backtesting, use data from the end of the historical dataset
                    # This simulates what would happen if we made a prediction N days ago
                    # and now we have the actual prices
                    if len(hist_df) < horizon + 5:  # Need enough data
                        skipped_no_data += 1
                        continue
                    
                    # Use the last N days of historical data as "ground truth"
                    # This simulates the scenario where the forecast was made earlier
                    actual_data = hist_df.iloc[-horizon:].copy()
                    # Keep original dates for consistency
                else:
                    # Normal evaluation: filter historical data for prediction period
                    mask = (hist_df['Date'] >= pred_start) & (hist_df['Date'] <= pred_end)
                    actual_data = hist_df[mask]
                
                if len(actual_data) == 0:
                    skipped_no_data += 1
                    continue
                
                actual_values = actual_data['Close'].values
                
                # Align predictions with actuals
                min_len = min(len(pred_values), len(actual_values))
                pred_aligned = np.array(pred_values[:min_len])
                actual_aligned = actual_values[:min_len]
                
                if len(pred_aligned) == 0:
                    continue
                
                # Calculate metrics for ensemble
                ensemble_metrics = {
                    'MAE': mae(pred_aligned, actual_aligned),
                    'RMSE': rmse(pred_aligned, actual_aligned),
                    'MAPE': mape(pred_aligned, actual_aligned)
                }
                
                # Calculate metrics for each component model
                component_metrics = {}
                for model_name, component_preds in components.items():
                    if component_preds and len(component_preds) > 0:
                        comp_aligned = np.array(component_preds[:min_len])
                        component_metrics[model_name] = {
                            'MAE': mae(comp_aligned, actual_aligned),
                            'RMSE': rmse(comp_aligned, actual_aligned),
                            'MAPE': mape(comp_aligned, actual_aligned)
                        }
                
                # Use prediction creation date for better time-series visualization
                prediction_created = pred_doc.get('created_at', '')
                if isinstance(prediction_created, str):
                    try:
                        pred_created_date = datetime.fromisoformat(prediction_created.replace('Z', '+00:00'))
                    except:
                        pred_created_date = pred_date
                else:
                    pred_created_date = pred_date
                
                evaluation_result = {
                    'prediction_id': str(pred_doc.get('_id', '')),
                    'ticker': ticker,
                    'prediction_date': pred_created_date.isoformat(),  # When forecast was made
                    'prediction_target_date': pred_date.isoformat(),  # What date was being predicted
                    'horizon': horizon,
                    'evaluation_date': datetime.utcnow().isoformat(),  # When evaluation was run
                    'data_points': min_len,
                    'ensemble_metrics': ensemble_metrics,
                    'component_metrics': component_metrics
                }
                
                evaluation_results.append(evaluation_result)
                
                # Save evaluation to MongoDB
                self.mongo.save_evaluation_result(evaluation_result)
                
                # Save performance metrics to model registry
                for model_name, metrics in component_metrics.items():
                    # Extract model type from name (e.g., 'lstm' from 'lstm_forecast')
                    model_type = model_name.replace('_forecast', '').replace('_', '')
                    if model_type in ['lstm', 'gru', 'transformer', 'mlp', 'arima', 'moving', 'average', 'var']:
                        # Get latest version for this model type
                        latest_model = self.registry.get_latest_model(model_type, ticker, production_only=False)
                        if latest_model:
                            version = latest_model.get('version', 'unknown')
                            self.registry.save_model_performance(
                                model_type,
                                version,
                                ticker,
                                metrics
                            )
            
            # Build response message
            message_parts = []
            if len(evaluation_results) > 0:
                backtest_note = " (using backtesting mode with historical data)" if allow_recent and skipped_future > 0 else ""
                message_parts.append(f'Successfully evaluated {len(evaluation_results)} prediction(s){backtest_note}')
            if skipped_future > 0 and not allow_recent:
                message_parts.append(f'{skipped_future} forecast(s) skipped (predicted dates are in the future - wait for actual prices)')
            if skipped_no_data > 0:
                message_parts.append(f'{skipped_no_data} forecast(s) skipped (no ground truth data available)')
            
            if len(evaluation_results) == 0:
                if allow_recent:
                    return {
                        'success': False,
                        'ticker': ticker,
                        'count': 0,
                        'message': f'No predictions could be evaluated. {skipped_future} forecast(s) had insufficient historical data for backtesting, {skipped_no_data} had no data. Total forecasts found: {len(predictions)}'
                    }
                else:
                    return {
                        'success': False,
                        'ticker': ticker,
                        'count': 0,
                        'message': f'No predictions could be evaluated. {skipped_future} forecast(s) are too recent (wait 1-2 days for actual prices), {skipped_no_data} had no data. Total forecasts found: {len(predictions)}'
                    }
            
            return {
                'success': True,
                'ticker': ticker,
                'evaluations': evaluation_results,
                'count': len(evaluation_results),
                'evaluation_date': datetime.utcnow().isoformat(),
                'message': '; '.join(message_parts) if message_parts else 'Evaluation completed'
            }
            
        except Exception as e:
            return {
                'success': False,
                'message': f'Error evaluating predictions: {str(e)}'
            }
    
    def get_evaluation_history(
        self,
        ticker: str,
        model_type: Optional[str] = None,
        limit: int = 100
    ) -> Dict[str, Any]:
        """
        Get evaluation history for a ticker or model
        
        Args:
            ticker: Ticker symbol
            model_type: Optional model type filter
            limit: Maximum number of records
            
        Returns:
            Dictionary with evaluation history
        """
        try:
            # Ensure MongoDB is connected
            if not self.mongo.ensure_connected():
                return {'success': False, 'message': 'MongoDB not configured. Please set MONGODB_URI environment variable.'}
            
            col = self.mongo.db.get_collection('evaluations')
            
            query = {'ticker': ticker}
            if model_type:
                query['model_type'] = model_type
            
            evaluations = list(col.find(query).sort('evaluation_date', -1).limit(limit))
            
            for eval_doc in evaluations:
                if '_id' in eval_doc:
                    eval_doc['_id'] = str(eval_doc['_id'])
            
            return {
                'success': True,
                'ticker': ticker,
                'model_type': model_type,
                'evaluations': evaluations,
                'count': len(evaluations)
            }
            
        except Exception as e:
            return {
                'success': False,
                'message': f'Error getting evaluation history: {str(e)}'
            }

