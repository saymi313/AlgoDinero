"""
Tests for adaptive ensemble weighting functionality
"""

import unittest
import numpy as np
import sys
import os
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, timedelta

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from forecasting.forecast_engine import ForecastEngine, ForecastRequest


class TestAdaptiveEnsemble(unittest.TestCase):
    """Test adaptive ensemble weighting"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.engine = ForecastEngine()
        self.model_types = ['moving_average', 'arima', 'mlp', 'var', 'gru', 'lstm', 'transformer']
    
    def test_calculate_adaptive_weights_equal_fallback(self):
        """Test that weights fallback to equal when no performance data"""
        # Mock MongoDB to return None (not configured)
        self.engine.mongo_db = None
        
        weights = self.engine._calculate_adaptive_weights('AAPL', self.model_types)
        
        # Should return equal weights
        self.assertEqual(len(weights), len(self.model_types))
        expected_weight = 1.0 / len(self.model_types)
        for model_type in self.model_types:
            self.assertAlmostEqual(weights[model_type], expected_weight, places=5)
        
        # Weights should sum to 1.0
        total_weight = sum(weights.values())
        self.assertAlmostEqual(total_weight, 1.0, places=5)
    
    def test_calculate_adaptive_weights_with_performance_data(self):
        """Test adaptive weights calculation with performance data"""
        # Mock MongoDB collection with evaluation data
        mock_collection = MagicMock()
        
        # Create mock evaluation documents with different MAPE values
        mock_evaluations = [
            {
                'ticker': 'AAPL',
                'evaluation_date': (datetime.utcnow() - timedelta(days=i)).isoformat(),
                'component_metrics': {
                    'moving_average': {'MAPE': 5.0},  # Best performance
                    'arima': {'MAPE': 10.0},
                    'mlp': {'MAPE': 15.0},
                    'var': {'MAPE': 12.0},
                    'gru': {'MAPE': 8.0},
                    'lstm': {'MAPE': 7.0},
                    'transformer': {'MAPE': 9.0}
                }
            }
            for i in range(5)
        ]
        
        mock_collection.find.return_value.sort.return_value.limit.return_value = mock_evaluations
        self.engine.mongo_db = MagicMock()
        self.engine.mongo_db.get_collection.return_value = mock_collection
        
        weights = self.engine._calculate_adaptive_weights('AAPL', self.model_types)
        
        # Weights should be normalized
        total_weight = sum(weights.values())
        self.assertAlmostEqual(total_weight, 1.0, places=5)
        
        # Better performing models should have higher weights
        # moving_average has lowest MAPE (5.0), so should have highest weight
        self.assertGreater(weights['moving_average'], weights['mlp'])
        self.assertGreater(weights['moving_average'], weights['arima'])
    
    def test_calculate_adaptive_weights_error_handling(self):
        """Test that errors in weight calculation fallback to equal weights"""
        # Mock MongoDB to raise an exception
        self.engine.mongo_db = MagicMock()
        self.engine.mongo_db.get_collection.side_effect = Exception("Database error")
        
        weights = self.engine._calculate_adaptive_weights('AAPL', self.model_types)
        
        # Should fallback to equal weights on error
        expected_weight = 1.0 / len(self.model_types)
        for model_type in self.model_types:
            self.assertAlmostEqual(weights[model_type], expected_weight, places=5)
    
    def test_adaptive_weights_in_forecast(self):
        """Test that forecast includes ensemble weights"""
        # Mock the _load_history method to return sample data
        mock_df = MagicMock()
        mock_df.__getitem__.return_value.values.astype.return_value = np.array([100, 102, 101, 103, 105] * 24)
        mock_df.__getitem__.return_value.iloc.__getitem__.return_value = datetime.now()
        
        with patch.object(self.engine, '_load_history', return_value=mock_df):
            with patch.object(self.engine, '_arima', return_value=np.array([106, 107, 108, 109, 110])):
                with patch.object(self.engine, '_mlp', return_value=np.array([106, 107, 108, 109, 110])):
                    # Mock MongoDB to avoid connection issues
                    self.engine.mongo_db = None
                    
                    request = ForecastRequest(ticker='AAPL', horizon=5, days=120)
                    result = self.engine.run_forecast(request)
                    
                    # Check that ensemble_weights are included
                    self.assertIn('ensemble_weights', result)
                    self.assertIsInstance(result['ensemble_weights'], dict)
                    self.assertEqual(len(result['ensemble_weights']), len(self.model_types))
    
    def test_weights_normalization(self):
        """Test that weights are properly normalized"""
        # Test with various scenarios
        test_cases = [
            ['model1', 'model2', 'model3'],
            ['model1'],
            ['model1', 'model2', 'model3', 'model4', 'model5']
        ]
        
        for model_types in test_cases:
            self.engine.mongo_db = None  # Use fallback
            weights = self.engine._calculate_adaptive_weights('AAPL', model_types)
            
            # Weights should sum to 1.0
            total = sum(weights.values())
            self.assertAlmostEqual(total, 1.0, places=5, msg=f"Failed for {model_types}")
            
            # All weights should be positive
            for weight in weights.values():
                self.assertGreater(weight, 0)
    
    def test_weights_with_missing_metrics(self):
        """Test weights calculation when some models have no metrics"""
        # Mock MongoDB collection with partial evaluation data
        mock_collection = MagicMock()
        
        mock_evaluations = [
            {
                'ticker': 'AAPL',
                'evaluation_date': datetime.utcnow().isoformat(),
                'component_metrics': {
                    'moving_average': {'MAPE': 5.0},
                    'arima': {'MAPE': 10.0},
                    # Other models missing
                }
            }
        ]
        
        mock_collection.find.return_value.sort.return_value.limit.return_value = mock_evaluations
        self.engine.mongo_db = MagicMock()
        self.engine.mongo_db.get_collection.return_value = mock_collection
        
        weights = self.engine._calculate_adaptive_weights('AAPL', self.model_types)
        
        # Weights should still be normalized
        total_weight = sum(weights.values())
        self.assertAlmostEqual(total_weight, 1.0, places=5)
        
        # Models with metrics should have higher weights than those without
        self.assertGreater(weights['moving_average'], weights['mlp'])


if __name__ == '__main__':
    unittest.main()

