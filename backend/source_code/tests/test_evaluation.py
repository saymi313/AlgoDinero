"""
Tests for evaluation functionality
"""

import unittest
import numpy as np
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from forecasting.evaluation import rmse, mae, mape, directional_accuracy, evaluate_time_series


class TestEvaluation(unittest.TestCase):
    """Test evaluation metrics"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.actual = np.array([100, 102, 101, 103, 105])
        self.predicted = np.array([101, 103, 100, 104, 106])
    
    def test_rmse(self):
        """Test RMSE calculation"""
        result = rmse(self.predicted, self.actual)
        self.assertIsInstance(result, float)
        self.assertGreaterEqual(result, 0)
    
    def test_mae(self):
        """Test MAE calculation"""
        result = mae(self.predicted, self.actual)
        self.assertIsInstance(result, float)
        self.assertGreaterEqual(result, 0)
    
    def test_mape(self):
        """Test MAPE calculation"""
        result = mape(self.predicted, self.actual)
        self.assertIsInstance(result, float)
        self.assertGreaterEqual(result, 0)
    
    def test_directional_accuracy(self):
        """Test directional accuracy"""
        result = directional_accuracy(self.predicted, self.actual)
        self.assertIsInstance(result, float)
        self.assertGreaterEqual(result, 0)
        self.assertLessEqual(result, 100)
    
    def test_evaluate_time_series(self):
        """Test time series evaluation"""
        predictions = {
            'model1': self.predicted,
            'model2': self.actual  # Perfect prediction
        }
        
        result = evaluate_time_series(predictions, self.actual)
        
        self.assertIn('model1', result)
        self.assertIn('model2', result)
        self.assertIn('RMSE', result['model1'])
        self.assertIn('MAE', result['model1'])
        self.assertIn('MAPE', result['model1'])
    
    def test_rmse_edge_cases(self):
        """Test RMSE with edge cases"""
        # Empty arrays
        result = rmse(np.array([]), np.array([]))
        self.assertEqual(result, 0.0)
        
        # Single value
        result = rmse(np.array([100]), np.array([100]))
        self.assertEqual(result, 0.0)
        
        # Perfect prediction
        actual = np.array([100, 200, 300])
        predicted = np.array([100, 200, 300])
        result = rmse(predicted, actual)
        self.assertEqual(result, 0.0)
    
    def test_mae_edge_cases(self):
        """Test MAE with edge cases"""
        # Empty arrays
        result = mae(np.array([]), np.array([]))
        self.assertEqual(result, 0.0)
        
        # Single value
        result = mae(np.array([100]), np.array([100]))
        self.assertEqual(result, 0.0)
    
    def test_mape_edge_cases(self):
        """Test MAPE with edge cases"""
        # Zero actual values (should handle gracefully)
        actual = np.array([0, 100, 200])
        predicted = np.array([10, 110, 210])
        result = mape(predicted, actual)
        self.assertIsInstance(result, float)
        self.assertGreaterEqual(result, 0)
    
    def test_directional_accuracy_edge_cases(self):
        """Test directional accuracy with edge cases"""
        # All correct
        actual = np.array([100, 102, 104, 106])
        predicted = np.array([101, 103, 105, 107])  # All upward
        result = directional_accuracy(predicted, actual)
        self.assertEqual(result, 100.0)
        
        # All wrong
        actual = np.array([100, 102, 104, 106])
        predicted = np.array([99, 101, 103, 105])  # All downward (wrong)
        result = directional_accuracy(predicted, actual)
        self.assertEqual(result, 0.0)
        
        # Empty arrays
        result = directional_accuracy(np.array([]), np.array([]))
        self.assertEqual(result, 0.0)


if __name__ == '__main__':
    unittest.main()

