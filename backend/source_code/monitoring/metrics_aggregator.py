"""
Metrics Aggregator
Aggregates evaluation metrics over time windows and computes trends
"""

from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from pymongo import MongoClient
import os


class MetricsAggregator:
    """Aggregates and analyzes evaluation metrics"""
    
    def __init__(self, mongo_uri: Optional[str] = None):
        """Initialize metrics aggregator"""
        self.uri = mongo_uri or os.getenv('MONGODB_URI')
        self.client = None
        self.db = None
        self._init_connection()
    
    def _init_connection(self):
        """Initialize MongoDB connection"""
        if self.uri:
            try:
                self.client = MongoClient(self.uri, serverSelectionTimeoutMS=2000)
                self.db = self.client.get_database('fintech_forecasting')
            except Exception:
                self.client = None
                self.db = None
    
    def aggregate_metrics(
        self,
        ticker: Optional[str] = None,
        model_type: Optional[str] = None,
        window: str = 'daily',  # 'daily', 'weekly', 'monthly'
        days_back: int = 30
    ) -> Dict[str, Any]:
        """
        Aggregate metrics over time windows
        
        Args:
            ticker: Optional ticker filter
            model_type: Optional model type filter
            window: Aggregation window ('daily', 'weekly', 'monthly')
            days_back: Number of days to look back
            
        Returns:
            Dictionary with aggregated metrics
        """
        if self.db is None:
            return {'success': False, 'message': 'MongoDB not configured'}
        
        col = self.db.get_collection('evaluations')
        
        # Build query
        query = {}
        if ticker:
            query['ticker'] = ticker
        
        start_date = datetime.utcnow() - timedelta(days=days_back)
        # Query by either evaluation_date or prediction_date to catch all relevant evaluations
        # Use $or to match evaluations where either date is within range
        date_query = {
            '$or': [
                {'evaluation_date': {'$gte': start_date.isoformat()}},
                {'prediction_date': {'$gte': start_date.isoformat()}}
            ]
        }
        query.update(date_query)
        
        # Get evaluations, sorted by prediction_date if available, otherwise evaluation_date
        evaluations = list(col.find(query).sort([
            ('prediction_date', 1),
            ('evaluation_date', 1)
        ]))
        
        if not evaluations:
            return {
                'success': True,
                'window': window,
                'aggregated_metrics': {},
                'count': 0,
                'message': 'No evaluation data available. Run evaluation first or create forecasts.'
            }
        
        # Aggregate by window - but keep individual evaluations visible
        aggregated = {}
        
        for eval_doc in evaluations:
            # Use prediction_date if available (when forecast was made), otherwise use evaluation_date
            pred_date_str = eval_doc.get('prediction_date', '')
            eval_date_str = eval_doc.get('evaluation_date', '')
            
            # Prefer prediction_date for grouping, as it represents when the forecast was made
            date_str = pred_date_str if pred_date_str else eval_date_str
            if not date_str:
                continue
            
            try:
                date_obj = datetime.fromisoformat(date_str.replace('Z', '+00:00'))
            except:
                # Try evaluation_date as fallback
                try:
                    date_obj = datetime.fromisoformat(eval_date_str.replace('Z', '+00:00'))
                except:
                    continue
            
            # Determine window key based on aggregation window
            if window == 'daily':
                # For daily, use the date itself (not grouped)
                window_key = date_obj.strftime('%Y-%m-%d')
            elif window == 'weekly':
                # Get week start
                week_start = date_obj - timedelta(days=date_obj.weekday())
                window_key = week_start.strftime('%Y-%m-%d')  # Use date for better sorting
            elif window == 'monthly':
                # Use first day of month
                window_key = date_obj.strftime('%Y-%m-01')
            else:
                window_key = date_obj.strftime('%Y-%m-%d')
            
            # For daily window, show each evaluation as a separate point
            # For weekly/monthly, group them by window
            if window == 'daily':
                # Use evaluation_date for display to spread points across time
                # This shows when evaluations were actually run, creating a time series
                eval_date_str = eval_doc.get('evaluation_date', '')
                pred_id = eval_doc.get('prediction_id', '')
                
                # Try to use evaluation_date for display (when evaluation was run)
                if eval_date_str:
                    try:
                        eval_date_obj = datetime.fromisoformat(eval_date_str.replace('Z', '+00:00'))
                        # Use evaluation date for display to show time series
                        display_key = eval_date_obj.strftime('%Y-%m-%d %H:%M')
                        # Use full timestamp as unique key
                        unique_key = eval_date_obj.strftime('%Y-%m-%dT%H:%M:%S')
                        # Use evaluation datetime for sorting
                        date_obj = eval_date_obj
                    except:
                        # Fallback to prediction date
                        display_key = date_obj.strftime('%Y-%m-%d')
                        unique_key = f"{date_obj.isoformat()}_{pred_id if pred_id else len(aggregated)}"
                else:
                    # Fallback: use prediction date
                    display_key = date_obj.strftime('%Y-%m-%d')
                    unique_key = f"{date_obj.isoformat()}_{pred_id if pred_id else len(aggregated)}"
            else:
                unique_key = window_key
                display_key = window_key
            
            if unique_key not in aggregated:
                # Store the datetime used for sorting (evaluation_date if available, otherwise prediction_date)
                aggregated[unique_key] = {
                    'date': display_key,
                    'datetime': date_obj.isoformat(),  # Use the datetime we determined (evaluation_date or prediction_date)
                    'metrics': [],
                    'count': 0
                }
            
            # Extract metrics
            ensemble_metrics = eval_doc.get('ensemble_metrics', {})
            component_metrics = eval_doc.get('component_metrics', {})
            
            if ensemble_metrics:
                aggregated[unique_key]['metrics'].append(ensemble_metrics)
                aggregated[unique_key]['count'] += 1
            
            # Also aggregate component metrics if model_type specified
            if model_type and component_metrics:
                model_key = model_type.replace('_forecast', '').replace('_', '')
                if model_key in component_metrics:
                    aggregated[unique_key]['metrics'].append(component_metrics[model_key])
        
        # Compute averages for each window (or use individual values for daily)
        result = {}
        for unique_key, data in aggregated.items():
            metrics_list = data['metrics']
            if not metrics_list:
                continue
            
            # For daily window with multiple evaluations on same day, average them
            # For weekly/monthly, always average
            if len(metrics_list) == 1:
                # Single evaluation - use it directly
                avg_metrics = metrics_list[0]
            else:
                # Multiple evaluations - average them
                avg_metrics = {}
                for metric_name in ['MAE', 'RMSE', 'MAPE']:
                    values = [m.get(metric_name, 0) for m in metrics_list if metric_name in m and m.get(metric_name) is not None]
                    if values:
                        avg_metrics[metric_name] = sum(values) / len(values)
            
            result[unique_key] = {
                'date': data['date'],
                'datetime': data.get('datetime', data['date']),
                'average_metrics': avg_metrics,
                'count': data['count']
            }
        
        return {
            'success': True,
            'window': window,
            'ticker': ticker,
            'model_type': model_type,
            'aggregated_metrics': result,
            'total_windows': len(result)
        }
    
    def compute_trends(
        self,
        ticker: str,
        model_type: Optional[str] = None,
        days_back: int = 30
    ) -> Dict[str, Any]:
        """
        Compute performance trends (improving/degrading)
        
        Args:
            ticker: Ticker symbol
            model_type: Optional model type
            days_back: Days to analyze
            
        Returns:
            Dictionary with trend analysis
        """
        if self.db is None:
            return {'success': False, 'message': 'MongoDB not configured'}
        
        # Get daily aggregations
        daily_agg = self.aggregate_metrics(ticker, model_type, 'daily', days_back)
        
        if not daily_agg.get('success') or not daily_agg.get('aggregated_metrics'):
            return {
                'success': False,
                'message': 'No data available for trend analysis'
            }
        
        aggregated = daily_agg['aggregated_metrics']
        dates = sorted(aggregated.keys())
        
        if len(dates) < 2:
            return {
                'success': False,
                'message': 'Insufficient data for trend analysis (need at least 2 data points)'
            }
        
        # Get first and last metrics
        first_metrics = aggregated[dates[0]].get('average_metrics', {})
        last_metrics = aggregated[dates[-1]].get('average_metrics', {})
        
        trends = {}
        for metric in ['MAE', 'RMSE', 'MAPE']:
            first_val = first_metrics.get(metric, 0)
            last_val = last_metrics.get(metric, 0)
            
            if first_val > 0:
                change_pct = ((last_val - first_val) / first_val) * 100
            else:
                change_pct = 0.0
            
            # Lower is better, so negative change is improvement
            trends[metric] = {
                'first_value': first_val,
                'last_value': last_val,
                'change_percentage': change_pct,
                'trend': 'improving' if change_pct < 0 else 'degrading' if change_pct > 0 else 'stable'
            }
        
        return {
            'success': True,
            'ticker': ticker,
            'model_type': model_type,
            'period': f'{days_back} days',
            'trends': trends,
            'overall_trend': 'improving' if all(t['trend'] == 'improving' for t in trends.values()) else \
                          'degrading' if all(t['trend'] == 'degrading' for t in trends.values()) else 'mixed'
        }
    
    def rank_models(
        self,
        ticker: str,
        metric: str = 'MAPE',
        days_back: int = 30
    ) -> Dict[str, Any]:
        """
        Rank models by performance
        
        Args:
            ticker: Ticker symbol
            metric: Metric to rank by ('MAE', 'RMSE', 'MAPE')
            days_back: Days to analyze
            
        Returns:
            Dictionary with model rankings
        """
        # Ensure MongoDB connection
        if self.db is None and self.uri:
            try:
                from pymongo import MongoClient
                self.client = MongoClient(self.uri, serverSelectionTimeoutMS=2000)
                self.db = self.client.get_database('fintech_forecasting')
            except Exception:
                return {'success': False, 'message': 'MongoDB not configured or connection failed'}
        
        if self.db is None:
            return {'success': False, 'message': 'MongoDB not configured'}
        
        col = self.db.get_collection('evaluations')
        
        start_date = datetime.utcnow() - timedelta(days=days_back)
        evaluations = list(col.find({
            'ticker': ticker,
            'evaluation_date': {'$gte': start_date.isoformat()}
        }))
        
        if not evaluations:
            return {
                'success': False,
                'message': 'No evaluations found'
            }
        
        # Aggregate metrics by model (collect all metrics, not just one)
        model_metrics = {}
        
        for eval_doc in evaluations:
            component_metrics = eval_doc.get('component_metrics', {})
            
            for model_name, metrics in component_metrics.items():
                if model_name not in model_metrics:
                    model_metrics[model_name] = {
                        'MAE': [],
                        'RMSE': [],
                        'MAPE': []
                    }
                
                # Collect all metrics
                if 'MAE' in metrics:
                    model_metrics[model_name]['MAE'].append(metrics['MAE'])
                if 'RMSE' in metrics:
                    model_metrics[model_name]['RMSE'].append(metrics['RMSE'])
                if 'MAPE' in metrics:
                    model_metrics[model_name]['MAPE'].append(metrics['MAPE'])
        
        # Compute averages for all metrics and rank
        rankings = []
        for model_name, metric_lists in model_metrics.items():
            if any(metric_lists.values()):  # If any metric has data
                avg_mae = sum(metric_lists['MAE']) / len(metric_lists['MAE']) if metric_lists['MAE'] else 0
                avg_rmse = sum(metric_lists['RMSE']) / len(metric_lists['RMSE']) if metric_lists['RMSE'] else 0
                avg_mape = sum(metric_lists['MAPE']) / len(metric_lists['MAPE']) if metric_lists['MAPE'] else 0
                eval_count = max(len(metric_lists['MAE']), len(metric_lists['RMSE']), len(metric_lists['MAPE']))
                
                rankings.append({
                    'model': model_name,
                    'average_mae': avg_mae,
                    'average_rmse': avg_rmse,
                    'average_mape': avg_mape,
                    'evaluations': eval_count
                })
        
        # Sort by the specified metric (lower is better)
        rankings.sort(key=lambda x: x.get('average_' + metric.lower(), float('inf')))
        
        return {
            'success': True,
            'ticker': ticker,
            'metric': metric,
            'rankings': rankings,
            'best_model': rankings[0]['model'] if rankings else None
        }

