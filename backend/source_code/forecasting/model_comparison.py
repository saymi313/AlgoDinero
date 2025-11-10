"""
Model Comparison Module
Compares model versions and determines which performs better
"""

from typing import Dict, Any, List, Optional
import numpy as np
from datetime import datetime


class ModelComparator:
    """Compares model performance and determines best model"""
    
    def __init__(self):
        """Initialize model comparator"""
        pass
    
    def compare_models(
        self,
        old_metrics: Dict[str, float],
        new_metrics: Dict[str, float],
        primary_metric: str = 'MAPE'
    ) -> Dict[str, Any]:
        """
        Compare two model versions based on metrics
        
        Args:
            old_metrics: Metrics from old model version
            new_metrics: Metrics from new model version
            primary_metric: Primary metric to use for comparison (MAPE, RMSE, MAE)
            
        Returns:
            Dictionary with comparison results
        """
        comparison = {
            'old_metrics': old_metrics,
            'new_metrics': new_metrics,
            'primary_metric': primary_metric,
            'improvement': {},
            'better_model': None,
            'improvement_percentage': 0.0
        }
        
        # Compare all metrics
        for metric in ['MAE', 'RMSE', 'MAPE']:
            if metric in old_metrics and metric in new_metrics:
                old_val = old_metrics[metric]
                new_val = new_metrics[metric]
                
                # Lower is better for all these metrics
                if old_val > 0:
                    improvement = ((old_val - new_val) / old_val) * 100
                else:
                    improvement = 0.0
                
                comparison['improvement'][metric] = improvement
        
        # Determine better model based on primary metric
        if primary_metric in old_metrics and primary_metric in new_metrics:
            old_primary = old_metrics[primary_metric]
            new_primary = new_metrics[primary_metric]
            
            if new_primary < old_primary:
                comparison['better_model'] = 'new'
                if old_primary > 0:
                    comparison['improvement_percentage'] = ((old_primary - new_primary) / old_primary) * 100
            else:
                comparison['better_model'] = 'old'
                if new_primary > 0:
                    comparison['improvement_percentage'] = ((new_primary - old_primary) / new_primary) * 100
        
        return comparison
    
    def should_promote(
        self,
        comparison: Dict[str, Any],
        improvement_threshold: float = 5.0
    ) -> bool:
        """
        Determine if new model should be promoted to production
        
        Args:
            comparison: Comparison result from compare_models
            improvement_threshold: Minimum improvement percentage required
            
        Returns:
            True if new model should be promoted
        """
        if comparison['better_model'] != 'new':
            return False
        
        return comparison['improvement_percentage'] >= improvement_threshold
    
    def aggregate_metrics(
        self,
        metrics_list: List[Dict[str, float]]
    ) -> Dict[str, float]:
        """
        Aggregate multiple metric evaluations
        
        Args:
            metrics_list: List of metric dictionaries
            
        Returns:
            Aggregated metrics (mean values)
        """
        if not metrics_list:
            return {}
        
        aggregated = {}
        metric_names = set()
        
        for metrics in metrics_list:
            metric_names.update(metrics.keys())
        
        for metric in metric_names:
            values = [m.get(metric, 0) for m in metrics_list if metric in m]
            if values:
                aggregated[metric] = float(np.mean(values))
        
        return aggregated

