"""
Alert Service
Generates alerts when performance thresholds are exceeded
"""

from typing import Dict, Any, List, Optional
from datetime import datetime
from pymongo import MongoClient
import os


class AlertService:
    """Manages system alerts and notifications"""
    
    def __init__(self, mongo_uri: Optional[str] = None):
        """Initialize alert service"""
        self.uri = mongo_uri or os.getenv('MONGODB_URI')
        self.client = None
        self.db = None
        self.default_thresholds = {
            'MAPE': 10.0,  # 10% MAPE threshold
            'RMSE_spike': 20.0,  # 20% increase in RMSE
            'MAE_spike': 20.0,  # 20% increase in MAE
            'degrading_trend': 15.0  # 15% degradation over period
        }
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
    
    def check_thresholds(
        self,
        ticker: str,
        model_type: Optional[str] = None,
        thresholds: Optional[Dict[str, float]] = None
    ) -> List[Dict[str, Any]]:
        """
        Check if any metrics exceed thresholds and generate alerts
        
        Args:
            ticker: Ticker symbol
            model_type: Optional model type filter
            thresholds: Custom thresholds (uses defaults if None)
            
        Returns:
            List of generated alerts
        """
        if self.db is None:
            return []
        
        if thresholds is None:
            thresholds = self.default_thresholds
        
        alerts = []
        
        # Get recent evaluations
        col = self.db.get_collection('evaluations')
        recent_evals = list(col.find({
            'ticker': ticker
        }).sort('evaluation_date', -1).limit(10))
        
        if not recent_evals:
            return alerts
        
        # Check each evaluation
        for eval_doc in recent_evals:
            ensemble_metrics = eval_doc.get('ensemble_metrics', {})
            component_metrics = eval_doc.get('component_metrics', {})
            
            # Check ensemble metrics
            if ensemble_metrics:
                mape_val = ensemble_metrics.get('MAPE', 0)
                if mape_val > thresholds.get('MAPE', 10.0):
                    alert = {
                        'type': 'high_mape',
                        'severity': 'warning',
                        'ticker': ticker,
                        'model_type': 'ensemble',
                        'metric': 'MAPE',
                        'value': mape_val,
                        'threshold': thresholds.get('MAPE', 10.0),
                        'message': f'MAPE ({mape_val:.2f}%) exceeds threshold ({thresholds.get("MAPE", 10.0)}%)',
                        'evaluation_id': str(eval_doc.get('_id', '')),
                        'evaluation_date': eval_doc.get('evaluation_date', '')
                    }
                    alerts.append(alert)
            
            # Check component metrics if model_type specified
            if model_type and component_metrics:
                model_key = model_type.replace('_forecast', '').replace('_', '')
                if model_key in component_metrics:
                    metrics = component_metrics[model_key]
                    mape_val = metrics.get('MAPE', 0)
                    if mape_val > thresholds.get('MAPE', 10.0):
                        alert = {
                            'type': 'high_mape',
                            'severity': 'warning',
                            'ticker': ticker,
                            'model_type': model_type,
                            'metric': 'MAPE',
                            'value': mape_val,
                            'threshold': thresholds.get('MAPE', 10.0),
                            'message': f'{model_type} MAPE ({mape_val:.2f}%) exceeds threshold',
                            'evaluation_id': str(eval_doc.get('_id', '')),
                            'evaluation_date': eval_doc.get('evaluation_date', '')
                        }
                        alerts.append(alert)
        
        # Check for spikes (compare with previous evaluation)
        if len(recent_evals) >= 2:
            current = recent_evals[0]
            previous = recent_evals[1]
            
            current_metrics = current.get('ensemble_metrics', {})
            previous_metrics = previous.get('ensemble_metrics', {})
            
            for metric in ['RMSE', 'MAE']:
                current_val = current_metrics.get(metric, 0)
                previous_val = previous_metrics.get(metric, 0)
                
                if previous_val > 0:
                    spike_pct = ((current_val - previous_val) / previous_val) * 100
                    threshold_key = f'{metric}_spike'
                    
                    if spike_pct > thresholds.get(threshold_key, 20.0):
                        alert = {
                            'type': 'metric_spike',
                            'severity': 'error',
                            'ticker': ticker,
                            'model_type': 'ensemble',
                            'metric': metric,
                            'current_value': current_val,
                            'previous_value': previous_val,
                            'spike_percentage': spike_pct,
                            'threshold': thresholds.get(threshold_key, 20.0),
                            'message': f'{metric} spiked by {spike_pct:.2f}% (threshold: {thresholds.get(threshold_key, 20.0)}%)',
                            'evaluation_id': str(current.get('_id', '')),
                            'evaluation_date': current.get('evaluation_date', '')
                        }
                        alerts.append(alert)
        
        # Save alerts to MongoDB
        for alert in alerts:
            alert['created_at'] = datetime.utcnow()
            self.save_alert(alert)
        
        return alerts
    
    def save_alert(self, alert_data: Dict[str, Any]) -> str:
        """Save alert to MongoDB"""
        if self.db is None:
            return ""
        
        col = self.db.get_collection('alerts')
        doc = dict(alert_data)
        if 'created_at' not in doc:
            doc['created_at'] = datetime.utcnow()
        result = col.insert_one(doc)
        return str(result.inserted_id)
    
    def get_recent_alerts(
        self,
        ticker: Optional[str] = None,
        severity: Optional[str] = None,
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        """
        Get recent alerts
        
        Args:
            ticker: Optional ticker filter
            severity: Optional severity filter ('warning', 'error')
            limit: Maximum number of alerts
            
        Returns:
            List of alerts
        """
        if self.db is None:
            return []
        
        col = self.db.get_collection('alerts')
        
        query = {}
        if ticker:
            query['ticker'] = ticker
        if severity:
            query['severity'] = severity
        
        alerts = list(col.find(query).sort('created_at', -1).limit(limit))
        
        for alert in alerts:
            if '_id' in alert:
                alert['_id'] = str(alert['_id'])
        
        return alerts
    
    def configure_thresholds(
        self,
        thresholds: Dict[str, float]
    ) -> Dict[str, Any]:
        """
        Configure alert thresholds
        
        Args:
            thresholds: Dictionary of threshold values
            
        Returns:
            Configuration result
        """
        # Update default thresholds
        self.default_thresholds.update(thresholds)
        
        return {
            'success': True,
            'message': 'Thresholds updated',
            'thresholds': self.default_thresholds
        }

